"""Arnés de comparación con brazos y modelo falsos: no usa red, GPU ni saldo."""

from datetime import UTC, datetime

import pytest

from wikillm.arnes.corrida import (
    Configuracion,
    ErrorDeCorrida,
    ejecutar,
    formatear_resumen,
    resumir,
    validar_pasos,
)
from wikillm.arnes.estimacion import (
    ExcesoDeCosto,
    aviso_de_hora_pico,
    estimar,
    exigir_confirmacion,
)
from wikillm.arnes.registro import (
    actualizar_corrida,
    anexar_linea,
    claves_escritas,
    info_git,
    leer_corrida,
    leer_lineas,
)
from wikillm.arnes.seleccion import (
    ErrorDeSeleccion,
    conteo_por_estado,
    seleccionar,
    valida_para_informe,
)
from wikillm.common.modelo import TopeDeGastoError
from wikillm.common.responder import Brazo, ResultadoBrazo, ResultadoIngesta
from wikillm.eval.metricas import leer_resultados

ORDEN = ("2401.00001", "2401.00002", "2401.00003")


def pregunta(id_, tipo="T1", estado="acordado"):
    return {"id": id_, "texto": f"Question {id_}?", "tipo": tipo, "estado_verificacion": estado}


class BrazoFalso:
    """Brazo que anota lo que le piden; `falla_en` es el número de respuesta que lanza error."""

    def __init__(self, nombre, eventos, *, ingeridos=(), con_traza=False, falla_en=None):
        self.nombre = nombre
        self.eventos = eventos
        self._ingeridos = list(ingeridos)
        self.con_traza = con_traza
        self.falla_en = falla_en
        self.respuestas = 0
        if con_traza:
            self.traza = lambda: {"acciones": 2, "busquedas": 1, "lecturas": 1}

    @property
    def ingeridos(self):
        return list(self._ingeridos)

    def ingerir(self, arxiv_id):
        self.eventos.append((self.nombre, "ingerir", arxiv_id))
        if arxiv_id in self._ingeridos:
            return ResultadoIngesta(0, 0, 0.0, 0.0, 0)
        self._ingeridos.append(arxiv_id)
        wiki = self.nombre == "wiki"
        return ResultadoIngesta(1000 if wiki else 0, 100 if wiki else 0, 1.5, 0.01 * wiki, 2 * wiki)

    def responder(self, texto):
        self.respuestas += 1
        if self.falla_en == self.respuestas:
            raise TopeDeGastoError("Tope alcanzado")
        self.eventos.append((self.nombre, "responder", texto))
        return ResultadoBrazo(
            respuesta=f"{self.nombre} answer",
            citas=(),
            abstuvo=self.nombre == "rag",
            tokens_contexto=100 if self.nombre == "rag" else 300,
            tokens_entrada=500,
            tokens_salida=50,
            segundos=0.5,
            usd=0.001,
            llamadas=1,
        )


def config(tmp_path, preguntas, pasos=(0, 2)):
    return Configuracion(
        corrida="c1",
        carpeta=tmp_path / "c1",
        pasos=tuple(pasos),
        orden=ORDEN,
        preguntas=tuple(preguntas),
        modelo="deepseek-flash",
        temperatura=0.0,
    )


def par(eventos, **kwargs):
    return [
        BrazoFalso("rag", eventos),
        BrazoFalso("wiki", eventos, con_traza=True, **kwargs),
    ]


AHORA = lambda: datetime(2026, 11, 7, 12, 0, tzinfo=UTC)  # noqa: E731


def correr(brazos, cfg):
    ejecutar(brazos, cfg, ahora=AHORA, salida=lambda _: None)


# --- bucle ------------------------------------------------------------------------------------
def test_los_brazos_cumplen_el_contrato_usado_por_el_arnes():
    assert isinstance(BrazoFalso("rag", []), Brazo)


def test_en_cada_paso_se_ingiere_primero_y_los_brazos_se_alternan_pregunta_a_pregunta(tmp_path):
    eventos = []
    correr(par(eventos), config(tmp_path, [pregunta("Q1"), pregunta("Q2")], pasos=(0, 2)))
    esperado = [
        ("rag", "responder", "Question Q1?"),  # paso 0, brazos vacíos
        ("wiki", "responder", "Question Q1?"),
        ("rag", "responder", "Question Q2?"),
        ("wiki", "responder", "Question Q2?"),
        ("rag", "ingerir", ORDEN[0]),
        ("wiki", "ingerir", ORDEN[0]),
        ("rag", "ingerir", ORDEN[1]),
        ("wiki", "ingerir", ORDEN[1]),
        ("rag", "responder", "Question Q1?"),
        ("wiki", "responder", "Question Q1?"),
        ("rag", "responder", "Question Q2?"),
        ("wiki", "responder", "Question Q2?"),
    ]
    assert eventos == esperado


def test_los_tres_archivos_siguen_el_contrato_y_la_traza_es_solo_de_quien_la_ofrece(tmp_path):
    cfg = config(tmp_path, [pregunta("Q1"), pregunta("Q2")], pasos=(0, 2))
    correr(par([]), cfg)
    filas = leer_resultados(cfg.carpeta / "respuestas.jsonl")
    assert len(filas) == 2 * 2 * 2
    assert {f["ingest_step"] for f in filas} == {0, 2}
    assert {f["run_id"] for f in filas} == {"c1"} and {f["model"] for f in filas} == {
        "deepseek-flash"
    }
    ingestas = leer_lineas(cfg.carpeta / "ingestas.jsonl")
    assert len(ingestas) == 2 * 2  # dos papers en dos brazos
    wiki = [f for f in ingestas if f["system"] == "wiki"]
    assert [f["arxiv_id"] for f in wiki] == list(ORDEN[:2]) and wiki[0]["calls"] == 2
    assert [f["ingest_step"] for f in wiki] == [1, 2]
    trazas = leer_lineas(cfg.carpeta / "trazas.jsonl")
    assert len(trazas) == 2 * 2 and {t["system"] for t in trazas} == {"wiki"}
    assert trazas[0]["acciones"] == 2 and trazas[0]["question_id"] == "Q1"


def test_una_pregunta_cuya_fuente_llega_despues_se_hace_igual(tmp_path):
    cfg = config(tmp_path, [pregunta("Q1")], pasos=(0,))
    correr(par([]), cfg)
    assert len(leer_lineas(cfg.carpeta / "respuestas.jsonl")) == 2
    assert not (cfg.carpeta / "ingestas.jsonl").exists()


def test_una_corrida_cortada_se_reanuda_sin_duplicar_ni_repetir(tmp_path):
    cfg = config(tmp_path, [pregunta("Q1"), pregunta("Q2")], pasos=(0, 2))
    eventos = []
    rotos = par(eventos, falla_en=3)  # el wiki falla en su 3.ª respuesta (paso 2, Q1)
    with pytest.raises(TopeDeGastoError):
        correr(rotos, cfg)
    escritas = leer_lineas(cfg.carpeta / "respuestas.jsonl")
    assert len(escritas) == 5  # 4 del paso 0 y rag-Q1 del paso 2; la que falló no se escribe

    eventos_2 = []
    nuevos = [
        BrazoFalso("rag", eventos_2),  # un RAG nuevo empieza sin ingeridos
        BrazoFalso("wiki", eventos_2, con_traza=True, ingeridos=rotos[1].ingeridos),
    ]
    correr(nuevos, cfg)
    claves = [
        (f["question_id"], f["system"], f["ingest_step"])
        for f in leer_lineas(cfg.carpeta / "respuestas.jsonl")
    ]
    assert len(claves) == 8 and len(set(claves)) == 8
    respondidos = [e for e in eventos_2 if e[1] == "responder"]
    assert len(respondidos) == 3  # wiki-Q1, rag-Q2 y wiki-Q2 del paso 2
    assert len(leer_lineas(cfg.carpeta / "ingestas.jsonl")) == 4  # no se repiten


def test_volver_a_lanzar_una_corrida_completa_no_escribe_ni_pregunta_nada(tmp_path):
    cfg = config(tmp_path, [pregunta("Q1")], pasos=(0, 2))
    primero = par([])
    correr(primero, cfg)
    antes = {
        n: (cfg.carpeta / n).read_text("utf-8") for n in ("respuestas.jsonl", "ingestas.jsonl")
    }
    eventos = []
    correr(
        [
            BrazoFalso("rag", eventos),
            BrazoFalso("wiki", eventos, con_traza=True, ingeridos=primero[1].ingeridos),
        ],
        cfg,
    )
    assert not [e for e in eventos if e[1] == "responder"]
    for nombre, texto in antes.items():
        assert (cfg.carpeta / nombre).read_text("utf-8") == texto


def test_un_wiki_mas_adelantado_que_el_paso_aborta_sin_preguntar(tmp_path):
    cfg = config(tmp_path, [pregunta("Q1")], pasos=(0, 2))
    brazos = [BrazoFalso("rag", []), BrazoFalso("wiki", [], con_traza=True, ingeridos=ORDEN)]
    with pytest.raises(ErrorDeCorrida, match="wiki tiene 3 papers"):
        correr(brazos, cfg)
    assert not (cfg.carpeta / "respuestas.jsonl").exists()


def test_un_fallo_del_modelo_conserva_lo_escrito_y_no_inventa_la_respuesta(tmp_path):
    cfg = config(tmp_path, [pregunta("Q1"), pregunta("Q2")], pasos=(0,))
    with pytest.raises(TopeDeGastoError):
        correr(par([], falla_en=2), cfg)  # el wiki falla en Q2
    filas = leer_lineas(cfg.carpeta / "respuestas.jsonl")
    assert [(f["question_id"], f["system"]) for f in filas] == [
        ("Q1", "rag"),
        ("Q1", "wiki"),
        ("Q2", "rag"),
    ]


def test_los_pasos_se_validan():
    assert validar_pasos([5, 0, 5, 3], 10) == (0, 3, 5)
    for malos in ([], [-1], [11]):
        with pytest.raises(ErrorDeCorrida):
            validar_pasos(malos, 10)


def test_el_resumen_por_sistema_usa_lo_escrito(tmp_path):
    cfg = config(tmp_path, [pregunta("Q1"), pregunta("Q2")], pasos=(0, 2))
    correr(par([]), cfg)
    filas = {f["sistema"]: f for f in resumir(cfg.carpeta)}
    assert filas["rag"]["respuestas"] == 4 and filas["rag"]["abstenciones"] == 4
    assert filas["wiki"]["abstenciones"] == 0 and filas["wiki"]["contexto_mediano"] == 300
    assert filas["wiki"]["usd_ingesta"] == pytest.approx(0.02)
    assert filas["wiki"]["usd_preguntas"] == pytest.approx(0.004)
    assert filas["rag"]["seg_ingesta"] == pytest.approx(3.0)
    texto = "\n".join(formatear_resumen(list(filas.values()), "c1"))
    assert "wiki: 4 respuestas (0 abstenciones)" in texto
    assert "wikillm.eval metricas --respuestas results/c1/respuestas.jsonl" in texto


# --- registro ---------------------------------------------------------------------------------
def test_las_lineas_se_leen_apenas_se_escriben_y_las_claves_se_recuperan(tmp_path):
    ruta = tmp_path / "x" / "r.jsonl"
    anexar_linea(ruta, {"a": 1, "b": "ñ"})
    assert leer_lineas(ruta) == [{"a": 1, "b": "ñ"}]
    anexar_linea(ruta, {"a": 2, "b": "z"})
    assert claves_escritas(ruta, ("a", "b")) == {(1, "ñ"), (2, "z")}
    assert leer_lineas(tmp_path / "no.jsonl") == []


def test_los_metadatos_se_actualizan_sin_perder_lo_anterior(tmp_path):
    ruta = tmp_path / "corrida.json"
    assert leer_corrida(ruta) is None
    actualizar_corrida(ruta, corrida="c1", pasos=[0, 5])
    datos = actualizar_corrida(ruta, fin="2026-11-07T12:00:00Z")
    assert datos == {"corrida": "c1", "pasos": [0, 5], "fin": "2026-11-07T12:00:00Z"}
    assert leer_corrida(ruta) == datos


def test_sin_git_la_informacion_queda_en_none(tmp_path):
    assert info_git(tmp_path) == {"commit": None, "arbol_con_cambios": None}


def test_con_git_se_informa_el_commit_y_los_cambios_sin_contar_results(tmp_path):
    import subprocess

    def git(*args):
        subprocess.run(
            ["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t", *args],
            check=True,
            capture_output=True,
        )

    git("init", "-q")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    git("add", "-A")
    git("commit", "-q", "-m", "x")
    limpio = info_git(tmp_path)
    assert len(limpio["commit"]) == 40 and limpio["arbol_con_cambios"] is False
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "r.jsonl").write_text("{}", encoding="utf-8")
    assert info_git(tmp_path)["arbol_con_cambios"] is False
    (tmp_path / "a.txt").write_text("cambio", encoding="utf-8")
    assert info_git(tmp_path)["arbol_con_cambios"] is True


# --- selección --------------------------------------------------------------------------------
BANCO = [
    pregunta("B-T4-1", "T4", "verificado_b"),
    pregunta("A-T1-1", "T1", "acordado"),
    pregunta("A-T5-1", "T5", "acordado"),
    pregunta("A-T1-2", "T1", "borrador"),
]


def test_por_defecto_solo_las_acordadas_y_ordenadas_por_id():
    elegidas = seleccionar(BANCO)
    assert [p["id"] for p in elegidas] == ["A-T1-1", "A-T5-1"]
    assert valida_para_informe(elegidas)


def test_un_piloto_con_borradores_no_vale_para_el_informe():
    elegidas = seleccionar(BANCO, estado_minimo="borrador")
    assert len(elegidas) == 4 and not valida_para_informe(elegidas)
    assert conteo_por_estado(elegidas) == {"verificado_b": 1, "acordado": 2, "borrador": 1}
    assert [p["id"] for p in seleccionar(BANCO, estado_minimo="verificado_b")] == [
        "A-T1-1",
        "A-T5-1",
        "B-T4-1",
    ]


def test_se_acota_por_tipo_y_por_id_y_se_rechaza_lo_desconocido():
    assert [p["id"] for p in seleccionar(BANCO, estado_minimo="borrador", tipos=["T1"])] == [
        "A-T1-1",
        "A-T1-2",
    ]
    assert [p["id"] for p in seleccionar(BANCO, ids=["A-T5-1"])] == ["A-T5-1"]
    for malo in ({"estado_minimo": "listo"}, {"tipos": ["T9"]}, {"ids": ["no-existe"]}):
        with pytest.raises(ErrorDeSeleccion):
            seleccionar(BANCO, **malo)


def test_si_ninguna_pregunta_cumple_el_filtro_hay_un_error():
    with pytest.raises(ErrorDeSeleccion, match="Ninguna pregunta"):
        seleccionar([pregunta("X", estado="borrador")])
    assert not valida_para_informe([])


# --- estimación -------------------------------------------------------------------------------
def test_la_estimacion_suma_ingesta_del_wiki_y_preguntas_de_ambos_brazos():
    e = estimar(["rag", "wiki"], preguntas=60, pasos=11, papers=50)
    assert e.usd_ingesta == pytest.approx(1.5)
    assert e.usd_preguntas == pytest.approx(60 * 11 * 0.0048)
    assert e.total == pytest.approx(e.usd_ingesta + e.usd_preguntas)
    assert e.llamadas_de_pregunta == 660


def test_la_puerta_de_5_usd_pide_confirmacion():
    pequena = estimar(["rag", "wiki"], preguntas=6, pasos=2, papers=5)
    exigir_confirmacion(pequena, 0.0)  # no hace falta
    grande = estimar(["rag", "wiki"], preguntas=300, pasos=4, papers=3)
    with pytest.raises(ExcesoDeCosto, match="--confirmo-usd"):
        exigir_confirmacion(grande, 0.0)
    with pytest.raises(ExcesoDeCosto):
        exigir_confirmacion(grande, grande.total - 1)
    exigir_confirmacion(grande, grande.total)


def test_se_avisa_de_la_hora_pico_entre_semana_y_no_el_fin_de_semana():
    lunes_madrugada = datetime(2026, 11, 9, 2, 0, tzinfo=UTC)
    sabado = datetime(2026, 11, 7, 2, 0, tzinfo=UTC)
    assert "hora pico" in aviso_de_hora_pico(lunes_madrugada)
    assert aviso_de_hora_pico(sabado) is None


def test_un_rag_con_el_indice_vacio_responde_en_el_paso_cero(tmp_path):
    from test_rag_brazo import crear

    brazo, http = crear(tmp_path, "The ingested corpus does not contain this information.", [])
    resultado = brazo.responder("Anything?")
    assert resultado.abstuvo and resultado.citas == () and len(http.solicitudes) == 1
    assert "(no passages)" in http.solicitudes[0]["messages"][1]["content"]
    assert brazo.ingeridos == []
