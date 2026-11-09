"""Acciones del panel: validación, confirmación, tope de gasto y resultados estructurados."""

import argparse
import json
import os
import stat
import sys
from datetime import datetime
from pathlib import Path

import pytest

from test_arnes import ORDEN
from test_arnes_comparar import CITA, FRAGMENTO, RECUPERADOS, TRAZA, BrazoComparable, preparar_gold
from test_responder import AJUSTES
from wikillm.panel import acciones
from wikillm.panel.acciones import (
    POR_ID,
    AccionDesconocida,
    ConfirmacionRequerida,
    Ejecutor,
    EscritorDeLineas,
    FabricaDeBrazos,
    GastoDeSesion,
    ParametroInvalido,
    TopeDeSesion,
    comando_de_subproceso,
    comando_equivalente,
    correr_subproceso,
    validar,
)

AHORA = datetime(2026, 11, 9, 23, 15, 0)
REGISTRO = (
    "# Log\n\n## Step 2: 2401.00002 — Otro\n- Created: x\n- Updated: (none)\n"
    "- Citations removed: 0\n- Broken links: 0\n- Uncited numeric lines: 0\n\n"
    "## Step 3: 2401.00003 — Un título largo — con raya\n- Created: pagina-a, pagina-b\n"
    "- Updated: pagina-c\n- Citations removed: 1\n- Broken links: 2\n- Uncited numeric lines: 3\n"
)


class FabricaFalsa:
    """Sustituye a la fábrica real: brazos falsos, sin GPU ni modelo de embeddings."""

    def __init__(self, ingeridos=ORDEN[:2], falla=False):
        self.ingeridos = list(ingeridos)
        self.falla = falla
        self.reinicios = 0
        self.brazos = []
        self.listo = False

    def __call__(self, modelo, ajustes, argumentos):
        self.brazos = [
            BrazoComparable("rag", recuperados=RECUPERADOS, falla=self.falla),
            BrazoComparable("wiki", traza=TRAZA, ingeridos=self.ingeridos),
        ]
        return self.brazos

    def reiniciar(self):
        self.reinicios += 1

    def calentar(self, ajustes):
        self.listo = True
        return type("Indice", (), {"total_fragmentos": 5430})()


@pytest.fixture
def raiz(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    datos = tmp_path / "data"
    datos.mkdir()
    filas = [{"arxiv_id": a, "orden_ingesta": i} for i, a in enumerate(ORDEN, start=1)]
    (datos / "manifest_corpus.jsonl").write_text(
        "\n".join(json.dumps(f) for f in filas) + "\n", encoding="utf-8"
    )
    carpeta, spans = preparar_gold(datos)
    spans.replace(carpeta / "spans.jsonl")
    wiki = datos / "wiki" / "demo"
    wiki.mkdir(parents=True)
    (wiki / "estado.json").write_text(json.dumps({"ingeridos": list(ORDEN[:2])}), "utf-8")
    return tmp_path


def ejecutor(raiz, fabrica=None, tope=1.0, **kw):
    return Ejecutor(
        raiz,
        GastoDeSesion(tope),
        brazos=fabrica or FabricaFalsa(),
        modelo=kw.pop("modelo", lambda ajustes, ruta, emitir: object()),
        ahora=lambda: AHORA,
        **kw,
    )


def correr(ej, accion_id, parametros=None, confirmo=True):
    accion, valores = ej.preparar(accion_id, parametros, confirmo)
    eventos = []
    codigo = ej.funcion(accion, valores)(eventos.append)
    return codigo, eventos


def lineas(eventos, canal=None):
    return [e["texto"] for e in eventos if e["t"] == "linea" and e.get("canal") == canal]


# --- catálogo y validación ----------------------------------------------------------------------
def test_el_catalogo_tiene_ids_unicos_y_las_de_pago_declaran_su_estimacion():
    ids = [a.id for a in acciones.CATALOGO]
    assert len(ids) == len(set(ids))
    for a in acciones.CATALOGO:
        assert a.titulo and a.resumen
        assert (not a.gasta) or (a.estimacion and a.usd_estimado > 0)
        json.dumps(a.a_json())


@pytest.mark.parametrize("pregunta", ["", "   \n\t", None, 5, "x" * 401, "hola\x00mundo"])
def test_una_pregunta_vacia_larga_o_con_caracteres_de_control_se_rechaza(raiz, pregunta):
    with pytest.raises(ParametroInvalido):
        validar(POR_ID["comparar"], {"pregunta": pregunta}, raiz)


def test_la_pregunta_se_normaliza_y_el_wiki_toma_su_valor_por_defecto(raiz):
    v = validar(POR_ID["comparar"], {"pregunta": "  What \n is   this? "}, raiz)
    assert v == {"pregunta": "What is this?", "wiki": "data/wiki/demo"}


@pytest.mark.parametrize(
    "wiki",
    ["../x", "data/otro/x", "data/wiki", "data/wiki/a/b", "/abs", "C:/x", "data/wiki/../../x", 7],
)
def test_el_wiki_debe_ser_una_carpeta_dentro_de_data_wiki(raiz, wiki):
    with pytest.raises(ParametroInvalido):
        validar(POR_ID["comparar"], {"pregunta": "q?", "wiki": wiki}, raiz)


def test_un_wiki_con_barras_invertidas_se_normaliza(raiz):
    v = validar(POR_ID["git_wiki"], {"wiki": "data\\wiki\\dev2"}, raiz)
    assert v["wiki"] == "data/wiki/dev2"


@pytest.mark.parametrize("paso", [0, 51, -1, True, 6.5, "seis", None])
def test_el_paso_debe_ser_un_entero_dentro_del_corpus(raiz, paso):
    with pytest.raises(ParametroInvalido):
        validar(POR_ID["ingerir"], {"paso": paso}, raiz)


def test_el_paso_acepta_enteros_y_cadenas_de_digitos(raiz):
    assert validar(POR_ID["ingerir"], {"paso": 6}, raiz)["paso"] == 6
    assert validar(POR_ID["ingerir"], {"paso": "7"}, raiz)["paso"] == 7
    assert validar(POR_ID["ingerir"], {}, raiz)["paso"] == 6  # por defecto: el sexto paper


def test_parametros_desconocidos_o_opciones_fuera_de_la_lista_se_rechazan(raiz):
    with pytest.raises(ParametroInvalido, match="no admitidos"):
        validar(POR_ID["metricas"], {"orden": "rm -rf /"}, raiz)
    with pytest.raises(ParametroInvalido):
        validar(POR_ID["estimar_corrida"], {"alcance": "todo"}, raiz)
    with pytest.raises(ParametroInvalido):
        validar(POR_ID["comparar"], ["no", "es", "un", "objeto"], raiz)


# --- confirmación y tope --------------------------------------------------------------------------
@pytest.mark.parametrize("accion_id", [None, 123, "rm -rf", "no_existe", ["comparar"]])
def test_una_accion_fuera_del_catalogo_no_se_prepara(raiz, accion_id):
    with pytest.raises(AccionDesconocida):
        ejecutor(raiz).preparar(accion_id, {}, True)


def test_las_acciones_que_gastan_o_borran_exigen_confirmacion(raiz):
    ej = ejecutor(raiz)
    with pytest.raises(ConfirmacionRequerida):
        ej.preparar("comparar", {"pregunta": "q?"}, False)
    with pytest.raises(ConfirmacionRequerida):
        ej.preparar("reiniciar_wiki", {}, False)
    assert ej.preparar("comparar", {"pregunta": "q?"}, True)[0].id == "comparar"
    assert ej.preparar("metricas", {}, False)[0].id == "metricas"  # sin costo: no pide nada


def test_con_el_gasto_en_el_tope_se_bloquean_las_acciones_de_pago_y_siguen_las_gratis(raiz):
    ej = ejecutor(raiz, tope=0.01)
    ej.gasto.sumar(0.01)
    with pytest.raises(TopeDeSesion, match="tope"):
        ej.preparar("comparar", {"pregunta": "q?"}, True)
    with pytest.raises(TopeDeSesion):
        ej.preparar("ingerir", {"paso": 6}, True)
    assert ej.preparar("estimar_ingesta", {}, False)[0].gasta is False
    assert ej.preparar("metricas", {}, False)


def test_el_gasto_de_la_sesion_se_acumula():
    gasto = GastoDeSesion(0.25)
    gasto.sumar(0.001)
    gasto.sumar(0.002)
    assert gasto.total == pytest.approx(0.003) and not gasto.agotado
    gasto.sumar(0.25)
    assert gasto.agotado


def test_la_grabacion_de_una_comparacion_guarda_el_paso_del_wiki_al_lanzarla(raiz):
    ej = ejecutor(raiz)
    accion, valores = ej.preparar("comparar", {"pregunta": "q?"}, True)
    assert ej.parametros_grabados(accion, valores) == {
        "pregunta": "q?",
        "wiki": "data/wiki/demo",
        "paso_wiki": 2,
    }
    otra, v = ej.preparar("ingerir", {"paso": 3}, True)
    assert ej.parametros_grabados(otra, v) == {"paso": 3, "wiki": "data/wiki/demo"}


# --- órdenes equivalentes y subprocesos --------------------------------------------------------
def test_la_orden_equivalente_se_puede_pegar_en_la_consola(raiz):
    v = validar(POR_ID["comparar"], {"pregunta": "What is it?"}, raiz)
    assert comando_equivalente(POR_ID["comparar"], v) == (
        'uv run python -m wikillm.arnes comparar "What is it?" --wiki data/wiki/demo'
    )
    con_comillas = validar(POR_ID["comparar"], {"pregunta": 'The "best" one\'s?'}, raiz)
    assert comando_equivalente(POR_ID["comparar"], con_comillas).count("'") == 4  # ' duplicada
    assert comando_equivalente(POR_ID["ingerir"], {"paso": 6, "wiki": "data/wiki/demo"}) == (
        "uv run python -m wikillm.wiki ingerir --paso 6 --wiki data/wiki/demo"
    )
    assert comando_equivalente(POR_ID["calentar"], {}) is None


def test_la_orden_de_reiniciar_el_wiki_es_la_del_sistema_operativo(monkeypatch):
    monkeypatch.setattr(acciones, "_en_windows", lambda: True)
    assert comando_equivalente(POR_ID["reiniciar_wiki"], {}) == r".\scripts\preparar_demo.ps1"
    monkeypatch.setattr(acciones, "_en_windows", lambda: False)
    assert comando_equivalente(POR_ID["reiniciar_wiki"], {}) == (
        "rm -rf data/wiki/demo && cp -r data/wiki/dev2 data/wiki/demo"
    )


def test_los_subprocesos_salen_de_una_lista_fija_con_el_wiki_validado():
    cmd = comando_de_subproceso("git_wiki", {"wiki": "data/wiki/dev2"}, "py")
    assert cmd[-3:] == ["log", "--oneline", "--decorate"] and "data/wiki/dev2" in cmd
    assert comando_de_subproceso("metricas", {}, "py")[:4] == [
        "py",
        "-m",
        "wikillm.eval",
        "metricas",
    ]
    with pytest.raises(AccionDesconocida):
        comando_de_subproceso("comparar", {}, "py")


def test_un_subproceso_transmite_su_salida_linea_a_linea_y_devuelve_su_codigo(tmp_path):
    eventos = []
    codigo = correr_subproceso(
        [sys.executable, "-c", "print('uno'); print('dos'); raise SystemExit(3)"],
        eventos.append,
        cwd=tmp_path,
    )
    assert codigo == 3
    assert [e["texto"] for e in eventos] == ["uno", "dos"]


def test_un_subproceso_que_se_pasa_del_limite_se_corta(tmp_path):
    codigo = correr_subproceso(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        lambda e: None,
        cwd=tmp_path,
        limite=0.5,
    )
    assert codigo != 0


def test_el_escritor_entrega_lineas_completas_y_descarta_las_barras_de_progreso():
    salida = []
    escritor = EscritorDeLineas(salida.append)
    escritor.write("Error: par")
    escritor.write("te uno\nsegunda\r")
    escritor.write("Batches: 100%|██████| 1/1 [00:00<00:00, 5.0it/s]\r")
    escritor.write("\n\n")
    escritor.write("final sin salto")
    escritor.cerrar()
    assert salida == ["Error: parte uno", "segunda", "final sin salto"]


# --- comparar -----------------------------------------------------------------------------------
def test_comparar_muestra_la_orden_equivalente_la_salida_y_el_resultado_con_los_fragmentos(raiz):
    codigo, eventos = correr(ejecutor(raiz), "comparar", {"pregunta": "Which threshold?"})
    assert codigo == 0
    assert eventos[0] == {
        "t": "linea",
        "canal": "comando",
        "texto": 'uv run python -m wikillm.arnes comparar "Which threshold?" --wiki data/wiki/demo',
    }
    salida = lineas(eventos)
    assert any(x.startswith("PREGUNTA  Which threshold?") for x in salida)
    assert any("▌ WikiLLM" in x for x in salida) and any("Evidencia añadida" in x for x in salida)
    [resultado] = [e for e in eventos if e["t"] == "resultado"]
    assert resultado["tipo"] == "comparacion"
    datos = resultado["datos"]
    assert datos["paso"] == 2 and datos["pregunta"] == "Which threshold?"
    rag, wiki = datos["sistemas"]
    assert (rag["sistema"], rag["nombre"], wiki["sistema"]) == ("rag", "RAG simple", "wiki")
    assert rag["citas"] == [{"span_id": CITA, "texto": FRAGMENTO}]
    assert rag["recuperados"][0] == {
        "span_ids": RECUPERADOS[0]["span_ids"],
        "distancia": 0.2512,
        "citado": True,
        "texto": FRAGMENTO,
    }
    assert rag["recuperados"][1]["citado"] is False and rag["recuperados"][1]["texto"] is None
    assert wiki["recuperados"] is None
    assert wiki["traza"]["detalle"][0]["accion"] == "search"
    assert rag["usd"] == 0.001 and rag["llamadas"] == 3


def test_comparar_pasa_la_pregunta_tras_los_guiones_para_que_nunca_sea_una_opcion(raiz):
    recibido = {}

    def arnes(argv, *, salida, crear_brazos, crear_modelo):
        recibido["argv"] = argv
        return 0

    ej = ejecutor(raiz, arnes=arnes)
    correr(ej, "comparar", {"pregunta": "--wiki /etc --k 99"})
    assert recibido["argv"] == ["comparar", "--wiki", "data/wiki/demo", "--", "--wiki /etc --k 99"]


def test_un_error_de_la_orden_llega_como_linea_de_error_y_no_hay_resultado(raiz):
    codigo, eventos = correr(
        ejecutor(raiz, FabricaFalsa(ingeridos=[ORDEN[2]])), "comparar", {"pregunta": "q?"}
    )
    assert codigo == 1
    errores = lineas(eventos, "error")
    assert errores and "wiki" in errores[0]
    assert not any(e["t"] == "resultado" for e in eventos)


def test_un_fallo_del_modelo_se_informa_sin_dejar_evidencia(raiz):
    codigo, eventos = correr(
        ejecutor(raiz, FabricaFalsa(falla=True)), "comparar", {"pregunta": "q?"}
    )
    assert codigo == 1 and "Tope alcanzado" in " ".join(lineas(eventos, "error"))
    assert not (raiz / "results" / "demo" / "comparaciones.jsonl").exists()


def test_la_salida_de_error_se_captura_en_el_proceso_y_se_restaura(raiz, capsys):
    ej = ejecutor(raiz, FabricaFalsa(falla=True))
    original = sys.stderr
    correr(ej, "comparar", {"pregunta": "q?"})
    assert sys.stderr is original
    assert "Tope alcanzado" not in capsys.readouterr().err  # no se ensució la consola del panel


# --- ingerir y estimaciones -----------------------------------------------------------------
def test_ingerir_emite_el_resultado_leido_del_registro_del_wiki(raiz):
    wiki = raiz / "data" / "wiki" / "demo"
    modelos = []

    def principal_falso(argv, *, salida, crear_modelo):
        assert argv == ["ingerir", "--paso", "3", "--wiki", "data/wiki/demo"]
        salida("1 papers por ingerir de 3")
        modelos.append(crear_modelo(AJUSTES))
        (wiki / "estado.json").write_text(json.dumps({"ingeridos": list(ORDEN[:3])}), "utf-8")
        (wiki / "log.md").write_text(REGISTRO, "utf-8")
        return 0

    ej = ejecutor(raiz, wiki=principal_falso, modelo=lambda a, ruta, emitir: ("modelo", ruta))
    codigo, eventos = correr(ej, "ingerir", {"paso": 3})
    assert codigo == 0
    assert modelos == [("modelo", Path("results/demo/llamadas.jsonl"))]
    assert "1 papers por ingerir de 3" in lineas(eventos)
    [resultado] = [e for e in eventos if e["t"] == "resultado"]
    assert resultado["tipo"] == "ingesta"
    assert resultado["datos"] == {
        "paso": 3,
        "arxiv_id": "2401.00003",
        "titulo": "Un título largo — con raya",
        "creadas": ["pagina-a", "pagina-b"],
        "actualizadas": ["pagina-c"],
        "citas_eliminadas": 1,
        "enlaces_rotos": 2,
        "lineas_sin_cita": 3,
        "papers_nuevos": 1,
        "ingeridos": 3,
    }


def test_ingerir_sin_papers_nuevos_no_emite_resultado(raiz):
    ej = ejecutor(raiz, wiki=lambda argv, *, salida, crear_modelo: 0)
    codigo, eventos = correr(ej, "ingerir", {"paso": 2})
    assert codigo == 0 and not any(e["t"] == "resultado" for e in eventos)


def test_las_estimaciones_usan_las_mismas_ordenes_con_estimar(raiz):
    vistos = []

    def principal(argv, *, salida):
        vistos.append(argv)
        salida("estimado")
        return 0

    ej = ejecutor(raiz, arnes=principal, wiki=principal)
    correr(ej, "estimar_ingesta", {"paso": 6}, confirmo=False)
    correr(ej, "estimar_corrida", {"alcance": "piloto"}, confirmo=False)
    correr(ej, "estimar_corrida", {"alcance": "completa"}, confirmo=False)
    assert vistos[0] == ["ingerir", "--paso", "6", "--wiki", "data/wiki/demo", "--estimar"]
    assert vistos[1] == [
        "correr",
        "--corrida",
        "demo-estimar",
        "--estado-minimo",
        "borrador",
        "--pasos",
        "0,5",
        "--tipos",
        "T1,T4,T5",
        "--estimar",
    ]
    assert "--pasos" not in vistos[2] and vistos[2][-1] == "--estimar"


# --- calentar y reiniciar -----------------------------------------------------------------------
def test_calentar_carga_el_indice_y_dice_cuantos_fragmentos_tiene(raiz):
    fabrica = FabricaFalsa()
    codigo, eventos = correr(ejecutor(raiz, fabrica), "calentar", {}, confirmo=False)
    assert codigo == 0 and fabrica.listo
    assert any("5430 fragmentos" in x for x in lineas(eventos))


def test_calentar_sin_indice_que_cargar_lo_dice(raiz):
    ej = ejecutor(raiz, lambda *a: [])  # una fábrica que no sabe calentar
    _, eventos = correr(ej, "calentar", {}, confirmo=False)
    assert "No hay índice que cargar." in lineas(eventos)


def preparar_reinicio(raiz):
    base = raiz / "data" / "wiki" / "dev2"
    (base / ".git" / "objects").mkdir(parents=True)
    (base / "estado.json").write_text(json.dumps({"ingeridos": list(ORDEN[:2])}), "utf-8")
    (base / ".git" / "objects" / "abc").write_text("objeto", "utf-8")
    demo = raiz / "data" / "wiki" / "demo"
    (demo / ".git" / "objects").mkdir(parents=True)
    (demo / ".git" / "objects" / "viejo").write_text("objeto", "utf-8")
    os.chmod(demo / ".git" / "objects" / "viejo", stat.S_IREAD)  # como los objetos de Git
    (demo / "estado.json").write_text(json.dumps({"ingeridos": list(ORDEN)}), "utf-8")
    evidencia = raiz / "results" / "demo" / "comparaciones.jsonl"
    evidencia.parent.mkdir(parents=True)
    evidencia.write_text('{"a": 1}\n', "utf-8")


def test_reiniciar_copia_el_wiki_base_aparta_la_evidencia_y_reinicia_el_indice(raiz):
    preparar_reinicio(raiz)
    fabrica = FabricaFalsa()
    codigo, eventos = correr(ejecutor(raiz, fabrica), "reiniciar_wiki", {})
    assert codigo == 0
    demo = raiz / "data" / "wiki" / "demo"
    assert json.loads((demo / "estado.json").read_text("utf-8"))["ingeridos"] == list(ORDEN[:2])
    assert (demo / ".git" / "objects" / "abc").exists()
    assert not (demo / ".git" / "objects" / "viejo").exists()
    assert not (raiz / "results" / "demo" / "comparaciones.jsonl").exists()
    apartada = raiz / "results" / "demo" / "ensayos" / "comparaciones-20261109-231500.jsonl"
    assert apartada.read_text("utf-8") == '{"a": 1}\n'
    assert fabrica.reinicios == 1
    assert (
        "Wiki de la demostración listo en data/wiki/demo: 2 papers ingeridos (paso 2)."
        in lineas(eventos)
    )


def test_reiniciar_sin_wiki_base_falla_sin_tocar_el_de_la_demostracion(raiz):
    codigo, eventos = correr(ejecutor(raiz), "reiniciar_wiki", {})
    assert codigo == 1 and "Falta data/wiki/dev2" in " ".join(lineas(eventos, "error"))
    assert (raiz / "data" / "wiki" / "demo" / "estado.json").exists()


# --- fábrica de brazos ------------------------------------------------------------------------
def test_la_fabrica_reutiliza_el_indice_y_lo_pone_en_cero_en_cada_pregunta(monkeypatch):
    class Indice:
        total_fragmentos = 7

        def __init__(self):
            self.reinicios = 0

        def reiniciar(self):
            self.reinicios += 1

    creados, armados = [], []
    monkeypatch.setattr(
        acciones, "crear_indice_rag", lambda ajustes, args: creados.append(args.gold) or Indice()
    )
    monkeypatch.setattr(
        acciones,
        "armar_brazos",
        lambda m, a, args, indice: armados.append(indice) or ["rag", "wiki"],
    )
    fabrica = FabricaDeBrazos()
    args = argparse.Namespace(gold=Path("data/gold"), chroma=Path("data/chroma"), corrida="demo")
    assert fabrica.listo is False
    assert fabrica(object(), AJUSTES, args) == ["rag", "wiki"]
    fabrica(object(), AJUSTES, args)
    assert len(creados) == 1 and armados[0] is armados[1] and armados[0].reinicios == 2
    assert fabrica.listo
    fabrica.reiniciar()
    assert armados[0].reinicios == 3
    otro = argparse.Namespace(gold=Path("otro/gold"), chroma=Path("data/chroma"), corrida="demo")
    fabrica(object(), AJUSTES, otro)
    assert len(creados) == 2
