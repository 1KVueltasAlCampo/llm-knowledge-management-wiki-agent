"""Servidor del panel con un servidor real en un puerto libre y acciones de prueba."""

import http.client
import json
import re
import threading
import time
from datetime import UTC, datetime

import pytest

from wikillm.panel import datos
from wikillm.panel.acciones import Ejecutor, GastoDeSesion
from wikillm.panel.servidor import Panel, crear_servidor, servir_en_hilo

PREGUNTA = "What is the total number of sessions?"


class EjecutorDePrueba(Ejecutor):
    """Catálogo y validación reales; cada acción corre una función de prueba."""

    def __init__(self, raiz, gasto, funciones):
        super().__init__(raiz, gasto, brazos=lambda *a: [])
        self.funciones = funciones

    def funcion(self, accion, valores):
        return self.funciones.get(accion.id, lambda emitir: 0)


def tres_lineas(emitir):
    for texto in ("uno", "dos", "tres"):
        emitir({"t": "linea", "texto": texto})
    return 0


def con_llamadas(emitir):
    emitir({"t": "llamada", "etiqueta": "wiki", "usd": 0.001, "texto": "{}"})
    emitir({"t": "llamada", "etiqueta": "wiki", "usd": 0.002, "texto": "{}"})
    return 0


@pytest.fixture
def srv(tmp_path):
    funciones = {"git_wiki": tres_lineas, "comparar": con_llamadas}
    gasto = GastoDeSesion(0.05)
    panel = Panel(
        tmp_path, ejecutor=EjecutorDePrueba(tmp_path, gasto, funciones), espera_del_flujo=0.2
    )
    servidor = crear_servidor(panel, 0)
    servir_en_hilo(servidor)
    servidor.funciones = funciones
    yield servidor
    servidor.shutdown()
    servidor.server_close()


def pedir(srv, metodo, ruta, cuerpo=None, cabeceras=None, bruto=None):
    conexion = http.client.HTTPConnection("127.0.0.1", srv.server_port, timeout=10)
    h = dict(cabeceras or {})
    datos_enviados = bruto
    if cuerpo is not None:
        datos_enviados = json.dumps(cuerpo)
        h.setdefault("Content-Type", "application/json")
    conexion.request(metodo, ruta, body=datos_enviados, headers=h)
    r = conexion.getresponse()
    contenido = r.read()
    cabeceras_respuesta = r.headers
    conexion.close()
    tipo = cabeceras_respuesta.get("Content-Type", "")
    cuerpo_leido = (
        json.loads(contenido) if "json" in tipo and contenido else contenido.decode("utf-8")
    )
    return r.status, cuerpo_leido, cabeceras_respuesta


def lanzar(srv, accion, parametros=None, confirmo=False):
    estado, cuerpo, _ = pedir(
        srv,
        "POST",
        "/api/ejecutar",
        {"accion": accion, "parametros": parametros or {}, "confirmo": confirmo},
    )
    return estado, cuerpo


def eventos(srv, trabajo, cabeceras=None, ruta=None):
    conexion = http.client.HTTPConnection("127.0.0.1", srv.server_port, timeout=10)
    conexion.request("GET", ruta or f"/api/eventos/{trabajo}", headers=cabeceras or {})
    r = conexion.getresponse()
    assert r.status == 200 and r.getheader("Content-Type").startswith("text/event-stream")
    texto = r.read().decode("utf-8")
    conexion.close()
    return [json.loads(x[len("data: ") :]) for x in texto.splitlines() if x.startswith("data: ")]


def esperar_libre(srv, limite=5.0):
    fin = time.monotonic() + limite
    while srv.panel.gestor.activo is not None and time.monotonic() < fin:
        time.sleep(0.005)
    assert srv.panel.gestor.activo is None


# --- página y seguridad ----------------------------------------------------------------------
def test_la_pagina_se_sirve_y_no_hace_referencia_a_direcciones_externas(srv):
    estado, cuerpo, cabeceras = pedir(srv, "GET", "/")
    assert estado == 200 and cabeceras["Content-Type"].startswith("text/html")
    assert "<title>" in cuerpo
    assert not re.search(r"""(?:src|href|action)\s*=\s*["']?(?:https?:)?//""", cuerpo, re.I)
    assert not re.search(r"url\(\s*[\"']?(?:https?:)?//|@import|<link[^>]+rel=.?stylesheet", cuerpo)
    assert "connect-src 'self'" in cabeceras["Content-Security-Policy"]


@pytest.mark.parametrize("metodo", ["GET", "POST"])
def test_un_host_ajeno_recibe_403_y_no_ejecuta_nada(srv, metodo):
    ajeno = {"Host": "ejemplo.com"}
    if metodo == "GET":
        estado, cuerpo, _ = pedir(srv, "GET", "/api/estado", cabeceras=ajeno)
    else:
        estado, cuerpo, _ = pedir(
            srv, "POST", "/api/ejecutar", {"accion": "git_wiki"}, cabeceras=ajeno
        )
    assert estado == 403 and "error" in cuerpo
    assert srv.panel.gestor.trabajo("t1") is None


@pytest.mark.parametrize("host", ["localhost:1", "127.0.0.1", "[::1]:8765"])
def test_los_nombres_locales_se_aceptan(srv, host):
    assert pedir(srv, "GET", "/api/estado", cabeceras={"Host": host})[0] == 200


@pytest.mark.parametrize(
    "host", ["127.0.0.1.ejemplo.com", "localhost@ejemplo.com", "ejemplo.com:80", ""]
)
def test_los_nombres_que_solo_se_parecen_a_los_locales_se_rechazan(srv, host):
    assert pedir(srv, "GET", "/api/estado", cabeceras={"Host": host})[0] == 403


def test_un_origen_ajeno_no_puede_cambiar_el_estado(srv):
    puerto = srv.server_port
    for origen in (
        "http://ejemplo.com",
        "http://127.0.0.1:1",  # otra aplicación local
        f"https://127.0.0.1:{puerto}",
        "null",
    ):
        estado, _, _ = pedir(
            srv, "POST", "/api/ejecutar", {"accion": "git_wiki"}, cabeceras={"Origin": origen}
        )
        assert estado == 403, origen
    assert srv.panel.gestor.trabajo("t1") is None
    propio = {"Origin": f"http://127.0.0.1:{puerto}"}
    assert pedir(srv, "POST", "/api/ejecutar", {"accion": "git_wiki"}, cabeceras=propio)[0] == 202


def test_el_cuerpo_debe_ser_json_de_tamano_razonable(srv):
    assert (
        pedir(srv, "POST", "/api/ejecutar", bruto="x", cabeceras={"Content-Type": "text/plain"})[0]
        == 415
    )
    json_malo = {"Content-Type": "application/json"}
    assert pedir(srv, "POST", "/api/ejecutar", bruto="{no", cabeceras=json_malo)[0] == 400
    assert pedir(srv, "POST", "/api/ejecutar", bruto="[1]", cabeceras=json_malo)[0] == 400
    grande = json.dumps({"accion": "git_wiki", "x": "a" * 30_000})
    assert pedir(srv, "POST", "/api/ejecutar", bruto=grande, cabeceras=json_malo)[0] == 400
    assert pedir(srv, "POST", "/api/otra", {"a": 1})[0] == 404
    assert srv.panel.gestor.trabajo("t1") is None


# --- ejecución y flujo ---------------------------------------------------------------------
def test_el_flujo_trae_las_lineas_en_orden_y_termina_con_el_codigo_cero(srv):
    estado, cuerpo = lanzar(srv, "git_wiki")
    assert estado == 202 and cuerpo == {"trabajo": "t1", "accion": "git_wiki"}
    recibidos = eventos(srv, "t1")
    assert [e["t"] for e in recibidos] == ["inicio", "linea", "linea", "linea", "fin"]
    assert [e["texto"] for e in recibidos if e["t"] == "linea"] == ["uno", "dos", "tres"]
    assert [e["n"] for e in recibidos] == [0, 1, 2, 3, 4] and recibidos[-1]["codigo"] == 0


def test_el_flujo_se_reanuda_despues_del_ultimo_evento_recibido(srv):
    lanzar(srv, "git_wiki")
    completo = eventos(srv, "t1")
    reanudado = eventos(srv, "t1", {"Last-Event-ID": "2"})
    assert [e["n"] for e in reanudado] == [3, 4] and reanudado == completo[3:]
    desde = eventos(srv, "t1", ruta="/api/eventos/t1?desde=4")
    assert [e["n"] for e in desde] == [4]


def test_el_flujo_de_un_trabajo_inexistente_es_404(srv):
    assert pedir(srv, "GET", "/api/eventos/t99")[0] == 404


def test_otro_trabajo_en_curso_se_rechaza_con_409_y_un_mensaje(srv):
    liberar = threading.Event()
    srv.funciones["git_wiki"] = lambda emitir: liberar.wait(5) and 0
    assert lanzar(srv, "git_wiki")[0] == 202
    estado, cuerpo = lanzar(srv, "validar_banco")
    assert estado == 409 and "trabajo en curso" in cuerpo["error"]
    assert pedir(srv, "GET", "/api/estado")[1]["ocupado"]["accion"] == "git_wiki"
    liberar.set()
    esperar_libre(srv)
    assert lanzar(srv, "validar_banco")[0] == 202


@pytest.mark.parametrize("accion", [None, "no_existe", "rm -rf /", 7])
def test_una_accion_desconocida_se_rechaza_con_400_sin_ejecutar(srv, accion):
    estado, cuerpo = lanzar(srv, accion)
    assert estado == 400 and "error" in cuerpo
    assert srv.panel.gestor.trabajo("t1") is None


def test_los_parametros_invalidos_se_rechazan_con_400(srv):
    assert lanzar(srv, "comparar", {"pregunta": ""}, confirmo=True)[0] == 400
    assert lanzar(srv, "comparar", {"pregunta": "x" * 401}, confirmo=True)[0] == 400
    fuera = {"pregunta": PREGUNTA, "wiki": "../fuera"}
    assert lanzar(srv, "comparar", fuera, confirmo=True)[0] == 400
    assert lanzar(srv, "ingerir", {"paso": 99}, confirmo=True)[0] == 400
    assert srv.panel.gestor.trabajo("t1") is None


def test_las_acciones_de_pago_y_las_que_borran_exigen_confirmacion(srv):
    estado, cuerpo = lanzar(srv, "comparar", {"pregunta": PREGUNTA})
    assert estado == 400 and "confirmación" in cuerpo["error"]
    assert lanzar(srv, "reiniciar_wiki")[0] == 400
    assert srv.panel.gestor.trabajo("t1") is None


def test_si_la_accion_falla_el_flujo_trae_el_error_y_el_servidor_sigue(srv):
    def falla(emitir):
        raise RuntimeError("se rompió")

    srv.funciones["git_wiki"] = falla
    lanzar(srv, "git_wiki")
    recibidos = eventos(srv, "t1")
    assert [e["t"] for e in recibidos] == ["inicio", "error", "fin"]
    assert "se rompió" in recibidos[1]["mensaje"] and recibidos[2]["codigo"] == 1
    esperar_libre(srv)
    assert pedir(srv, "GET", "/api/estado")[0] == 200
    srv.funciones["git_wiki"] = tres_lineas
    assert lanzar(srv, "git_wiki")[0] == 202


# --- gasto ------------------------------------------------------------------------------------
def test_el_gasto_se_acumula_y_al_llegar_al_tope_se_bloquean_las_acciones_de_pago(srv):
    lanzar(srv, "comparar", {"pregunta": PREGUNTA}, confirmo=True)
    eventos(srv, "t1")
    esperar_libre(srv)
    gasto = pedir(srv, "GET", "/api/estado")[1]["gasto"]
    assert gasto == {"sesion_usd": 0.003, "tope_usd": 0.05, "agotado": False}

    srv.panel.gasto.sumar(0.05)
    estado, cuerpo = lanzar(srv, "comparar", {"pregunta": PREGUNTA}, confirmo=True)
    assert estado == 403 and "tope" in cuerpo["error"]
    assert lanzar(srv, "git_wiki")[0] == 202  # las acciones sin costo siguen disponibles
    assert pedir(srv, "GET", "/api/estado")[1]["gasto"]["agotado"] is True


# --- visor de archivos -----------------------------------------------------------------------
def test_el_visor_entrega_lo_permitido_y_rechaza_el_resto(srv, tmp_path):
    (tmp_path / "README.md").write_text("# Hola", "utf-8")
    (tmp_path / ".env").write_text("DEEPSEEK_API_KEY=secreta", "utf-8")
    (tmp_path / "secreto.txt").write_text("no", "utf-8")
    estado, cuerpo, _ = pedir(srv, "GET", "/api/archivo?ruta=README.md")
    assert estado == 200 and cuerpo["tipo"] == "markdown" and cuerpo["texto"] == "# Hola"
    for ruta in ("..%2F.env", "docs%2F..%2F.env", ".env", "secreto.txt", "%2Fetc%2Fpasswd", ""):
        estado, cuerpo, _ = pedir(srv, "GET", f"/api/archivo?ruta={ruta}")
        assert estado == 403 and "secreta" not in json.dumps(cuerpo), ruta
    assert pedir(srv, "GET", "/api/archivo")[0] == 403


def test_el_listado_de_archivos_agrupa_lo_que_existe(srv, tmp_path):
    (tmp_path / "README.md").write_text("x", "utf-8")
    (tmp_path / ".env").write_text("x", "utf-8")
    lista = pedir(srv, "GET", "/api/archivos")[1]
    assert {"grupo": "Repositorio", "ruta": "README.md", "nombre": "README.md"} in lista
    assert all(x["ruta"] != ".env" for x in lista)


# --- grabación y reproducción ------------------------------------------------------------------
def test_la_reproduccion_repite_lo_grabado_marcado_y_sin_ejecutar(srv):
    llamadas = []

    def accion(emitir):
        llamadas.append(1)
        emitir({"t": "resultado", "tipo": "x", "datos": {"a": 1}})
        return 0

    srv.funciones["git_wiki"] = accion
    lanzar(srv, "git_wiki")
    eventos(srv, "t1")
    esperar_libre(srv)
    estado, cuerpo, _ = pedir(srv, "POST", "/api/reproducir", {"accion": "git_wiki"})
    assert estado == 202
    recibidos = eventos(srv, cuerpo["trabajo"])
    assert llamadas == [1]
    assert [e["t"] for e in recibidos] == ["inicio", "repro", "resultado", "fin"]
    assert all(e["repro"] is True for e in recibidos)
    assert recibidos[2]["datos"] == {"a": 1}
    esperar_libre(srv)
    assert len(pedir(srv, "GET", "/api/estado")[1]["grabaciones"]) == 1  # no graba la reproducción


def test_reproducir_sin_grabacion_o_con_otra_accion_se_rechaza(srv):
    assert pedir(srv, "POST", "/api/reproducir", {"accion": "git_wiki"})[0] == 404
    assert pedir(srv, "POST", "/api/reproducir", {"accion": "calentar"})[0] == 400
    assert pedir(srv, "POST", "/api/reproducir", {"accion": "no_existe"})[0] == 400
    assert pedir(srv, "POST", "/api/reproducir", {"accion": "git_wiki", "coincide": 3})[0] == 400


def test_la_reproduccion_elige_por_el_estado_del_wiki_al_grabar(srv, tmp_path):
    wiki = tmp_path / "data" / "wiki" / "demo"
    wiki.mkdir(parents=True)
    for n, texto in ((2, "con dos"), (3, "con tres")):
        (wiki / "estado.json").write_text(json.dumps({"ingeridos": list("abc"[:n])}), "utf-8")
        srv.funciones["comparar"] = lambda emitir, t=texto: emitir({"t": "linea", "texto": t}) or 0
        lanzar(srv, "comparar", {"pregunta": PREGUNTA}, confirmo=True)
        eventos(srv, f"t{n - 1}")
        esperar_libre(srv)
    pedido = {"accion": "comparar", "coincide": {"pregunta": PREGUNTA, "paso_wiki": 2}}
    estado, cuerpo, _ = pedir(srv, "POST", "/api/reproducir", pedido)
    assert estado == 202
    textos = [e["texto"] for e in eventos(srv, cuerpo["trabajo"]) if e["t"] == "linea"]
    assert textos == ["con dos"]
    esperar_libre(srv)
    pedido["coincide"]["paso_wiki"] = 9
    assert pedir(srv, "POST", "/api/reproducir", pedido)[0] == 404


# --- ejemplos, estado, métricas ---------------------------------------------------------------
def test_las_preguntas_de_ejemplo_se_publican_con_su_nota(srv):
    ejemplos = pedir(srv, "GET", "/api/ejemplos")[1]
    assert len(ejemplos) >= 2 and all(e["pregunta"] and e["nota"] for e in ejemplos)
    assert all(len(e["pregunta"]) <= 400 for e in ejemplos)


def test_ya_no_hay_guion_ni_notas_de_presentador(srv):
    assert pedir(srv, "GET", "/api/guion")[0] == 404
    assert pedir(srv, "GET", "/notas")[0] == 404


def test_el_estado_indica_el_siguiente_paper_a_ingerir(srv, tmp_path):
    filas = [
        {"arxiv_id": f"2401.0000{i}", "orden_ingesta": i, "titulo": f"Paper {i}"} for i in (1, 2, 3)
    ]
    manifest = tmp_path / "data" / "manifest_corpus.jsonl"
    manifest.parent.mkdir(parents=True)
    lineas = [json.dumps(f) for f in filas]
    manifest.write_text(chr(10).join(lineas) + chr(10), "utf-8")
    wiki = tmp_path / "data" / "wiki" / "demo"
    wiki.mkdir(parents=True)
    (wiki / "estado.json").write_text(json.dumps({"ingeridos": ["2401.00001"]}), "utf-8")
    corpus = pedir(srv, "GET", "/api/estado")[1]["corpus"]
    assert corpus == {
        "total": 3,
        "siguiente": {"paso": 2, "arxiv_id": "2401.00002", "titulo": "Paper 2"},
    }


def test_el_estado_resume_wiki_gasto_y_grabaciones(srv, tmp_path):
    wiki = tmp_path / "data" / "wiki" / "demo"
    (wiki / "pages").mkdir(parents=True)
    (wiki / "estado.json").write_text(json.dumps({"ingeridos": ["a", "b", "c"]}), "utf-8")
    (wiki / "pages" / "p.md").write_text("x", "utf-8")
    e = pedir(srv, "GET", "/api/estado")[1]
    assert e["ocupado"] is None and e["rag_listo"] is False
    assert e["wiki"]["ingeridos"] == 3 and e["wiki"]["paginas"] == 1
    assert e["gasto"] == {"sesion_usd": 0.0, "tope_usd": 0.05, "agotado": False}
    assert e["grabaciones"] == [] and isinstance(e["hora_pico"], bool) and e["modelo"]
    assert datetime.fromisoformat("2026-11-09T00:00:00+00:00").tzinfo == UTC


def test_las_acciones_publicadas_son_las_del_catalogo(srv):
    lista = pedir(srv, "GET", "/api/acciones")[1]
    ids = {a["id"] for a in lista}
    assert {"comparar", "ingerir", "reiniciar_wiki", "calentar"} <= ids
    comparar = next(a for a in lista if a["id"] == "comparar")
    assert comparar["gasta"] and comparar["estimacion"] and comparar["parametros"][0]["nombre"]


def test_las_metricas_del_piloto_vienen_de_los_archivos_guardados(srv, tmp_path):
    base = tmp_path / datos.PILOTO
    base.mkdir(parents=True)
    (base / "metricas_por_paso.json").write_text(json.dumps([{"system": "rag"}]), "utf-8")
    m = pedir(srv, "GET", "/api/metricas")[1]
    assert m["filas"] == [{"system": "rag"}] and m["preguntas"] == []


def test_una_ruta_inexistente_es_404(srv):
    assert pedir(srv, "GET", "/api/nada")[0] == 404
