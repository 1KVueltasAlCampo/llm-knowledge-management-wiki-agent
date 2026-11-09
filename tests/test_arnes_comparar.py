"""Comparación puntual de una pregunta con brazos falsos: no usa red, GPU ni saldo."""

import json

import pytest
import yaml

from test_arnes import ORDEN
from test_arnes_cli import Entorno, preguntas
from wikillm.arnes.comparar import (
    a_linea,
    comparar,
    crear_resolutor,
    formatear,
    registrar,
)
from wikillm.arnes.corrida import ErrorDeCorrida
from wikillm.arnes.registro import leer_lineas
from wikillm.common.modelo import TopeDeGastoError
from wikillm.common.responder import FRASE_ABSTENCION, ResultadoBrazo, ResultadoIngesta
from wikillm.corpus.spans import calcular_spans

CITA = "2401.00001#s1.p1"
FRAGMENTO = "Primer parrafo con una cifra de 0.8 que respalda la respuesta."
TRAZA = {
    "acciones": 2,
    "detalle": [
        {"accion": "search", "argumento": "PageRank", "resultado": "hipporag, recuperacion"},
        {"accion": "read", "argumento": ["hipporag"], "resultado": "read: hipporag"},
        {"accion": "answer", "argumento": "", "resultado": "final answer"},
    ],
    "incidencias": [],
}


def resultado(texto="It is 0.8.", citas=(CITA,), abstuvo=False, usd=0.001):
    return ResultadoBrazo(
        respuesta=texto,
        citas=() if abstuvo else tuple(citas),
        abstuvo=abstuvo,
        tokens_contexto=300,
        tokens_entrada=1500,
        tokens_salida=60,
        segundos=2.5,
        usd=usd,
        llamadas=3,
    )


RECUPERADOS = [
    {"span_ids": [CITA, "2401.00001#s1.p2"], "distancia": 0.2512},
    {"span_ids": ["2401.00002#s3.p4"], "distancia": 0.4107},
]


class BrazoComparable:
    def __init__(
        self, nombre, res=None, *, traza=None, ingeridos=(), falla=False, recuperados=None
    ):
        self.nombre = nombre
        if recuperados is not None:
            self.ultimos_recuperados = recuperados
        self.res = res or resultado()
        self.falla = falla
        self._ingeridos = list(ingeridos)
        self.preguntas = []
        if traza is not None:
            self.traza = lambda: traza

    @property
    def ingeridos(self):
        return list(self._ingeridos)

    def ingerir(self, arxiv_id):
        if arxiv_id not in self._ingeridos:
            self._ingeridos.append(arxiv_id)
        return ResultadoIngesta(0, 0, 0.0, 0.0, 0)

    def responder(self, pregunta):
        if self.falla:
            raise TopeDeGastoError("Tope alcanzado")
        self.preguntas.append(pregunta)
        return self.res


def par(**wiki):
    return [BrazoComparable("rag"), BrazoComparable("wiki", traza=TRAZA, **wiki)]


def par_con_recuperados(**wiki):
    return [
        BrazoComparable("rag", recuperados=RECUPERADOS),
        BrazoComparable("wiki", traza=TRAZA, **wiki),
    ]


def correr(brazos, paso=2, pregunta="What is the threshold?"):
    return comparar(brazos, pregunta, ORDEN, paso, modelo="deepseek-flash")


# --- núcleo -----------------------------------------------------------------------------------
def test_los_dos_sistemas_reciben_la_misma_pregunta_y_el_rag_se_pone_en_el_paso_del_wiki():
    rag, wiki = par(ingeridos=ORDEN[:2])
    comparacion = correr([rag, wiki])
    assert rag.preguntas == wiki.preguntas == ["What is the threshold?"]
    assert rag.ingeridos == list(ORDEN[:2]) and comparacion.paso == 2
    assert [r.sistema for r in comparacion.respuestas] == ["rag", "wiki"]
    assert comparacion.respuestas[0].traza is None and comparacion.respuestas[1].traza == TRAZA


def test_un_wiki_fuera_de_orden_aborta_sin_preguntar():
    rag, wiki = par(ingeridos=[ORDEN[1]])
    with pytest.raises(ErrorDeCorrida, match="wiki"):
        correr([rag, wiki], paso=1)
    assert rag.preguntas == [] and wiki.preguntas == []


def test_el_paso_debe_estar_dentro_del_corpus():
    with pytest.raises(ErrorDeCorrida, match="paso"):
        correr(par(), paso=9)


def test_con_el_wiki_vacio_se_compara_en_el_paso_cero():
    rag, wiki = par()
    comparacion = correr([rag, wiki], paso=0)
    assert comparacion.paso == 0 and rag.ingeridos == []


# --- presentación -----------------------------------------------------------------------------
def texto(comparacion, fragmento=FRAGMENTO):
    return "\n".join(formatear(comparacion, lambda sid: fragmento if sid == CITA else None))


def test_la_salida_muestra_la_pregunta_el_corpus_y_un_bloque_por_sistema():
    salida = texto(correr(par(ingeridos=ORDEN[:2])))
    assert "PREGUNTA  What is the threshold?" in salida
    assert "2 papers ingeridos (paso 2)" in salida and "deepseek-flash" in salida
    assert "▌ RAG simple" in salida and "▌ WikiLLM" in salida
    assert "COMPARACIÓN" in salida


def test_cada_cita_se_muestra_con_el_comienzo_de_su_fragmento():
    salida = texto(correr(par(ingeridos=ORDEN[:2])))
    assert f"[{CITA}] «{FRAGMENTO}»" in salida


def test_un_fragmento_largo_se_recorta_y_uno_no_disponible_se_indica():
    largo = "palabra " * 100
    assert "…»" in texto(correr(par(ingeridos=ORDEN[:2])), fragmento=largo)
    sin_fragmento = "\n".join(formatear(correr(par(ingeridos=ORDEN[:2])), lambda _: None))
    assert "(no disponible)" in sin_fragmento


def test_los_pasos_del_agente_aparecen_en_orden_con_su_consulta_y_sus_paginas():
    salida = texto(correr(par(ingeridos=ORDEN[:2])))
    assert "1. buscó «PageRank» → hipporag, recuperacion" in salida
    assert "2. leyó «hipporag» → read: hipporag" in salida
    assert "3. respondió → final answer" in salida
    assert salida.index("1. buscó") < salida.index("3. respondió")


def test_una_abstencion_se_indica_y_no_lista_citas():
    abstencion = resultado(FRASE_ABSTENCION, abstuvo=True)
    rag, wiki = par(ingeridos=ORDEN[:2])
    rag.res = wiki.res = abstencion
    salida = texto(correr([rag, wiki]))
    assert salida.count("Se abstuvo") == 2 and "Citas (" not in salida


def test_la_tabla_final_resume_cada_sistema_con_su_costo():
    rag, wiki = par(ingeridos=ORDEN[:2])
    wiki.res = resultado(usd=0.0042)
    salida = texto(correr([rag, wiki]))
    fila_wiki = next(x for x in salida.splitlines() if x.startswith("  WikiLLM"))
    assert "0.004200" in fila_wiki and " no " in fila_wiki
    assert "1500" in fila_wiki and "300" in fila_wiki


# --- evidencia --------------------------------------------------------------------------------
def test_la_linea_de_evidencia_guarda_ids_y_costos_pero_no_el_texto_del_fragmento():
    comparacion = correr(par(ingeridos=ORDEN[:2]))
    cadena = json.dumps(a_linea(comparacion))
    assert CITA in cadena and "usd" in cadena and "detalle" in cadena
    assert FRAGMENTO not in cadena


def test_las_comparaciones_sucesivas_se_acumulan(tmp_path):
    ruta = tmp_path / "demo" / "comparaciones.jsonl"
    registrar(ruta, correr(par(ingeridos=ORDEN[:2]), pregunta="Primera?"))
    registrar(ruta, correr(par(ingeridos=ORDEN[:2]), pregunta="Segunda?"))
    filas = leer_lineas(ruta)
    assert [f["pregunta"] for f in filas] == ["Primera?", "Segunda?"]
    assert {s["sistema"] for s in filas[0]["sistemas"]} == {"rag", "wiki"}


# --- resolución de citas contra el Gold ---------------------------------------------------------
CUERPO = f"# Título\n\n## 1 Introducción\n\n{FRAGMENTO}\n\nSegundo párrafo.\n"


def preparar_gold(tmp_path):
    carpeta = tmp_path / "gold"
    carpeta.mkdir()
    encabezado = yaml.safe_dump(
        {"arxiv_id": "2401.00001", "titulo": "Un paper", "version": "v1"}, sort_keys=False
    )
    (carpeta / "2401.00001.md").write_text(f"---\n{encabezado}---\n\n{CUERPO}", "utf-8")
    spans = tmp_path / "spans.jsonl"
    spans.write_text(
        "\n".join(json.dumps(s.como_dict()) for s in calcular_spans("2401.00001", "v1", CUERPO))
        + "\n",
        "utf-8",
    )
    return carpeta, spans


def test_el_resolutor_devuelve_el_fragmento_real_y_none_si_no_existe(tmp_path):
    carpeta, spans = preparar_gold(tmp_path)
    resolutor = crear_resolutor(carpeta, spans)
    assert resolutor(CITA) == FRAGMENTO
    assert resolutor("2401.00001#s9.p9") is None
    assert resolutor("2999.00001#s1.p1") is None


def test_el_resolutor_rechaza_un_gold_cuya_huella_ya_no_coincide(tmp_path):
    carpeta, spans = preparar_gold(tmp_path)
    ruta = carpeta / "2401.00001.md"
    ruta.write_text(ruta.read_text("utf-8").replace("0.8", "0.9"), "utf-8")
    assert crear_resolutor(carpeta, spans)(CITA) is None


def test_sin_spans_el_resolutor_no_resuelve_nada(tmp_path):
    assert crear_resolutor(tmp_path, tmp_path / "no-existe.jsonl")(CITA) is None


# --- orden de consola ---------------------------------------------------------------------------
class EntornoComparar(Entorno):
    def __init__(self, tmp_path, ingeridos=(), falla=False):
        super().__init__(tmp_path, preguntas(("A1", "T1", "acordado")))
        self.ingeridos = ingeridos
        self.falla = falla
        self.brazos = []

    def crear_brazos(self, modelo, ajustes, argumentos):
        self.brazos = [
            BrazoComparable("rag", falla=self.falla),
            BrazoComparable("wiki", traza=TRAZA, ingeridos=self.ingeridos),
        ]
        return self.brazos

    def comparar(self, *argv):
        from wikillm.arnes.__main__ import principal

        return principal(
            [
                "comparar",
                "Which threshold?",
                "--manifest",
                str(self.manifest),
                "--resultados",
                str(self.tmp_path / "results"),
                "--spans",
                str(self.tmp_path / "no-existe.jsonl"),
                "--wiki",
                str(self.tmp_path / "wiki"),
                *argv,
            ],
            salida=self.salida.append,
            crear_brazos=self.crear_brazos,
            crear_modelo=lambda ajustes, ruta: object(),
            ahora=lambda: self.ahora,
        )


def test_la_orden_toma_el_paso_del_wiki_imprime_y_deja_la_evidencia(tmp_path):
    e = EntornoComparar(tmp_path, ingeridos=ORDEN[:2])
    assert e.comparar() == 0
    assert "2 papers ingeridos (paso 2)" in e.texto and "▌ WikiLLM" in e.texto
    filas = leer_lineas(tmp_path / "results" / "demo" / "comparaciones.jsonl")
    assert len(filas) == 1 and filas[0]["paso"] == 2 and filas[0]["pregunta"] == "Which threshold?"
    assert e.brazos[0].ingeridos == list(ORDEN[:2])


def test_con_el_wiki_vacio_la_orden_compara_en_el_paso_cero(tmp_path):
    e = EntornoComparar(tmp_path)
    assert e.comparar() == 0 and "0 papers ingeridos (paso 0)" in e.texto


def test_un_wiki_fuera_de_orden_devuelve_1_sin_preguntar_ni_escribir(tmp_path, capsys):
    e = EntornoComparar(tmp_path, ingeridos=[ORDEN[2]])
    assert e.comparar() == 1
    assert "wiki" in capsys.readouterr().err
    assert all(b.preguntas == [] for b in e.brazos)
    assert not (tmp_path / "results" / "demo" / "comparaciones.jsonl").exists()


def test_un_fallo_del_modelo_devuelve_1_y_no_escribe_evidencia(tmp_path, capsys):
    e = EntornoComparar(tmp_path, ingeridos=ORDEN[:2], falla=True)
    assert e.comparar() == 1
    assert "Tope alcanzado" in capsys.readouterr().err
    assert not (tmp_path / "results" / "demo" / "comparaciones.jsonl").exists()


# --- fragmentos recuperados por el RAG ----------------------------------------------------------
def test_la_salida_lista_los_fragmentos_recuperados_y_marca_el_citado():
    salida = texto(correr(par_con_recuperados(ingeridos=ORDEN[:2])))
    assert "Fragmentos que recuperó por similitud" in salida
    assert f"* [{CITA}] (+1)  distancia 0.251" in salida
    assert "  [2401.00002#s3.p4]  distancia 0.411" in salida  # sin marca: no se citó


def test_un_sistema_que_no_recupera_no_tiene_esa_seccion_ni_ese_campo():
    comparacion = correr(par(ingeridos=ORDEN[:2]))
    assert "Fragmentos que recuperó" not in texto(comparacion)
    assert all("recuperados" not in s for s in a_linea(comparacion)["sistemas"])


def test_la_evidencia_guarda_ids_y_distancias_de_lo_recuperado_sin_texto():
    linea = a_linea(correr(par_con_recuperados(ingeridos=ORDEN[:2])))
    rag = next(s for s in linea["sistemas"] if s["sistema"] == "rag")
    assert rag["recuperados"] == RECUPERADOS
    assert FRAGMENTO not in json.dumps(linea)
