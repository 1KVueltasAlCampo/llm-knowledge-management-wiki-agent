"""Trabajos del panel: un hilo, eventos ordenados, grabación y reproducción."""

import json
import threading
import time
from datetime import UTC, datetime

import pytest

from wikillm.panel.trabajos import GestorDeTrabajos, SinGrabacion, TrabajoEnCurso

MOMENTO = datetime(2026, 11, 9, 23, 30, 5, tzinfo=UTC)


class Reloj:
    """Reloj que avanza un segundo por consulta; la acción puede adelantarlo."""

    def __init__(self):
        self.t = 0.0

    def __call__(self):
        self.t += 1.0
        return self.t


def terminar(trabajo, limite=5.0):
    fin = time.monotonic() + limite
    while not trabajo.terminado and time.monotonic() < fin:
        time.sleep(0.005)
    assert trabajo.terminado, "el trabajo no terminó a tiempo"


def tipos(trabajo):
    return [e["t"] for e in trabajo.eventos]


@pytest.fixture
def gestor(tmp_path):
    esperas = []
    g = GestorDeTrabajos(
        tmp_path / "grabaciones", reloj=Reloj(), esperar=esperas.append, ahora=lambda: MOMENTO
    )
    g.esperas = esperas
    return g


def tres_lineas(emitir):
    for texto in ("uno", "dos", "tres"):
        emitir({"t": "linea", "texto": texto})
    return 0


def test_los_eventos_salen_en_orden_con_inicio_lineas_y_fin(gestor):
    trabajo = gestor.lanzar("comparar", "Comparar", tres_lineas)
    terminar(trabajo)
    assert tipos(trabajo) == ["inicio", "linea", "linea", "linea", "fin"]
    assert [e["n"] for e in trabajo.eventos] == [0, 1, 2, 3, 4]
    assert [e["texto"] for e in trabajo.eventos if e["t"] == "linea"] == ["uno", "dos", "tres"]
    assert trabajo.eventos[-1]["codigo"] == 0 and trabajo.estado == "terminado"
    assert all("ts" in e for e in trabajo.eventos)


def test_un_segundo_trabajo_mientras_corre_el_primero_se_rechaza(gestor):
    liberar = threading.Event()
    primero = gestor.lanzar("a", "A", lambda emitir: liberar.wait(5) and 0)
    with pytest.raises(TrabajoEnCurso, match="A"):
        gestor.lanzar("b", "B", tres_lineas)
    assert gestor.activo is primero
    liberar.set()
    terminar(primero)
    segundo = gestor.lanzar("b", "B", tres_lineas)  # ya hay hueco
    terminar(segundo)
    assert segundo.estado == "terminado"


def test_una_excepcion_se_informa_con_codigo_1_y_el_gestor_sigue_vivo(gestor):
    def falla(emitir):
        emitir({"t": "linea", "texto": "antes"})
        raise ValueError("se rompió")

    trabajo = gestor.lanzar("a", "A", falla)
    terminar(trabajo)
    assert tipos(trabajo) == ["inicio", "linea", "error", "fin"]
    assert "ValueError: se rompió" in trabajo.eventos[2]["mensaje"]
    assert trabajo.eventos[-1]["codigo"] == 1 and trabajo.estado == "error"
    siguiente = gestor.lanzar("b", "B", tres_lineas)
    terminar(siguiente)
    assert siguiente.estado == "terminado"


def test_un_sys_exit_de_la_accion_tambien_se_informa(gestor):
    def sale(emitir):
        raise SystemExit(2)

    trabajo = gestor.lanzar("a", "A", sale)
    terminar(trabajo)
    assert "error" in tipos(trabajo) and trabajo.eventos[-1]["codigo"] == 1


def test_un_codigo_de_salida_distinto_de_cero_deja_el_trabajo_en_error(gestor):
    trabajo = gestor.lanzar("a", "A", lambda emitir: 3)
    terminar(trabajo)
    assert trabajo.eventos[-1]["codigo"] == 3 and trabajo.estado == "error"


def test_un_observador_que_falla_no_detiene_el_trabajo(tmp_path):
    def observador(trabajo, evento):
        raise RuntimeError("observador roto")

    g = GestorDeTrabajos(tmp_path / "g", observador=observador)
    trabajo = g.lanzar("a", "A", tres_lineas)
    terminar(trabajo)
    assert trabajo.estado == "terminado" and tipos(trabajo)[-1] == "fin"


def test_al_terminar_se_graba_con_encabezado_y_los_eventos(gestor, tmp_path):
    trabajo = gestor.lanzar("comparar", "Comparar", tres_lineas, parametros={"paso_wiki": 5})
    terminar(trabajo)
    archivos = sorted((tmp_path / "grabaciones").glob("*.jsonl"))
    assert [a.name for a in archivos] == ["20261109-233005-000-comparar.jsonl"]
    lineas = [json.loads(x) for x in archivos[0].read_text("utf-8").splitlines()]
    assert lineas[0] == {
        "t": "meta",
        "accion": "comparar",
        "titulo": "Comparar",
        "parametros": {"paso_wiki": 5},
        "fecha": "2026-11-09T23:30:05Z",
        "codigo": 0,
    }
    assert [x["t"] for x in lineas[1:]] == tipos(trabajo)
    assert gestor.grabaciones()[0]["accion"] == "comparar"
    assert gestor.grabaciones()[0]["parametros"] == {"paso_wiki": 5}


def test_sin_grabar_no_se_escribe_nada(gestor, tmp_path):
    terminar(gestor.lanzar("calentar", "Calentar", tres_lineas, grabar=False))
    assert not (tmp_path / "grabaciones").exists()
    assert gestor.grabaciones() == []


def test_un_trabajo_figura_terminado_solo_cuando_su_grabacion_ya_existe(gestor, tmp_path):
    trabajo = gestor.lanzar("a", "A", tres_lineas)
    terminar(trabajo)
    assert len(list((tmp_path / "grabaciones").glob("*.jsonl"))) == 1


def test_reproducir_reemite_lo_grabado_marcado_sin_ejecutar_la_accion(gestor, tmp_path):
    ejecuciones = []

    def accion(emitir):
        ejecuciones.append(1)
        emitir({"t": "linea", "texto": "uno"})
        emitir({"t": "resultado", "tipo": "x", "datos": {"a": 1}})
        return 0

    terminar(gestor.lanzar("comparar", "Comparar", accion))
    repro = gestor.reproducir("comparar", "Reproducción")
    terminar(repro)
    assert ejecuciones == [1]  # no se volvió a ejecutar
    assert tipos(repro) == ["inicio", "repro", "linea", "resultado", "fin"]
    assert all(e.get("repro") is True for e in repro.eventos)
    assert repro.eventos[3]["datos"] == {"a": 1}
    assert repro.eventos[1]["grabacion"].endswith("-comparar.jsonl")
    assert len(list((tmp_path / "grabaciones").glob("*.jsonl"))) == 1  # no graba la reproducción


def test_la_pausa_entre_eventos_tiene_tope(gestor):
    reloj = gestor._reloj

    def lenta(emitir):
        emitir({"t": "linea", "texto": "a"})
        reloj.t += 60
        emitir({"t": "linea", "texto": "b"})
        return 0

    terminar(gestor.lanzar("a", "A", lenta))
    terminar(gestor.reproducir("a", "R"))
    assert gestor.esperas and max(gestor.esperas) == 3.0
    assert all(e >= 0 for e in gestor.esperas)


def test_sin_grabacion_se_rechaza(gestor):
    with pytest.raises(SinGrabacion):
        gestor.reproducir("comparar", "R")


def test_la_reproduccion_elige_la_grabacion_cuyo_encabezado_coincide(tmp_path):
    momentos = iter(datetime(2026, 11, 9, 23, 0, s, tzinfo=UTC) for s in range(10, 40))
    g = GestorDeTrabajos(tmp_path / "g", esperar=lambda s: None, ahora=lambda: next(momentos))

    def con(texto):
        def accion(emitir):
            emitir({"t": "linea", "texto": texto})
            return 0

        return accion

    terminar(g.lanzar("comparar", "C", con("antes"), parametros={"paso_wiki": 5}))
    terminar(g.lanzar("comparar", "C", con("después"), parametros={"paso_wiki": 6}))

    def paso(n):
        return lambda meta: meta["parametros"]["paso_wiki"] == n

    repro = g.reproducir("comparar", "R", paso(5))
    terminar(repro)
    assert [e["texto"] for e in repro.eventos if e["t"] == "linea"] == ["antes"]
    ultima = g.reproducir("comparar", "R")  # sin criterio: la más reciente
    terminar(ultima)
    assert [e["texto"] for e in ultima.eventos if e["t"] == "linea"] == ["después"]
    with pytest.raises(SinGrabacion):
        g.reproducir("comparar", "R", paso(9))


def test_esperar_eventos_entrega_lo_nuevo_y_avisa_cuando_termino(gestor):
    trabajo = gestor.lanzar("a", "A", tres_lineas)
    terminar(trabajo)
    nuevos, terminado = gestor.esperar_eventos(trabajo, 3, espera=0.1)
    assert [e["n"] for e in nuevos] == [3, 4] and terminado is True
    vacios, terminado = gestor.esperar_eventos(trabajo, 5, espera=0.1)
    assert vacios == [] and terminado is True


def test_esperar_eventos_de_un_trabajo_en_curso_no_dice_que_termino(gestor):
    liberar = threading.Event()
    trabajo = gestor.lanzar("a", "A", lambda emitir: liberar.wait(5) and 0)
    while not trabajo.eventos:
        time.sleep(0.005)
    nuevos, terminado = gestor.esperar_eventos(trabajo, 1, espera=0.05)
    assert nuevos == [] and terminado is False
    liberar.set()
    terminar(trabajo)


def test_dos_grabaciones_de_la_misma_accion_en_el_mismo_instante_no_se_pisan(tmp_path):
    g = GestorDeTrabajos(tmp_path / "g", esperar=lambda s: None, ahora=lambda: MOMENTO)
    terminar(g.lanzar("a", "A", tres_lineas, parametros={"n": 1}))
    terminar(g.lanzar("a", "A", tres_lineas, parametros={"n": 2}))
    nombres = [x["archivo"] for x in g.grabaciones()]
    assert nombres == ["20261109-233005-000-a.jsonl", "20261109-233005-001-a.jsonl"]
    assert g.ultima_grabacion("a").name == nombres[-1]
    assert [x["parametros"]["n"] for x in g.grabaciones()] == [1, 2]
