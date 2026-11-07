"""Brazo RAG con almacén y cliente HTTP falsos: no usa red, GPU ni saldo."""

import json
from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

from test_rag_indice import AJUSTES
from wikillm.common.modelo import ClienteModelo
from wikillm.common.responder import Brazo
from wikillm.rag.brazo import INSTRUCCIONES, BrazoRag, extraer_fuentes
from wikillm.rag.fragmentos import Fragmento
from wikillm.rag.indice import Recuperado


def documento(arxiv_id, seccion, texto):
    metadatos = {"arxiv_id": arxiv_id, "titulo": f"Paper {arxiv_id}", "seccion": seccion}
    return Document(
        page_content=f"Paper {arxiv_id} — {seccion}\n\n{texto}",
        metadata={**metadatos, "posicion": 0},
    )


class AlmacenFalso:
    def __init__(self, documentos):
        self.documentos = documentos
        self.consultas = []

    def similarity_search_with_score(self, pregunta, k):
        self.consultas.append((pregunta, k))
        return [(d, 0.1 * i) for i, d in enumerate(self.documentos[:k])]


class ClienteHttpFalso:
    def __init__(self, texto):
        self.texto = texto
        self.solicitudes = []
        self.chat = SimpleNamespace(completions=self)

    def create(self, **argumentos):
        self.solicitudes.append(argumentos)
        uso = SimpleNamespace(
            prompt_tokens=2000,
            prompt_cache_hit_tokens=0,
            prompt_cache_miss_tokens=2000,
            completion_tokens=80,
            completion_tokens_details=SimpleNamespace(reasoning_tokens=0),
        )
        mensaje = SimpleNamespace(content=self.texto)
        return SimpleNamespace(choices=[SimpleNamespace(message=mensaje)], usage=uso)


DOCUMENTOS = [
    documento("2405.14831", "2 Método", "PageRank personalizado sobre el grafo."),
    documento("2502.14802", "3 Resultados", "Mejora el recobrado en preguntas multisalto."),
]


def crear(tmp_path, texto, **kwargs):
    http = ClienteHttpFalso(texto)
    modelo = ClienteModelo(AJUSTES, ruta_registro=tmp_path / "llamadas.jsonl", cliente=http)
    return BrazoRag(modelo, AlmacenFalso(DOCUMENTOS), **kwargs), http


def recuperado(arxiv_id):
    return Recuperado(Fragmento("x", arxiv_id, "T", "S", 0), 0.1)


def test_cumple_el_contrato_del_brazo(tmp_path):
    brazo, _ = crear(tmp_path, "Responde [2405.14831].")
    assert isinstance(brazo, Brazo)
    assert brazo.nombre == "rag"


def test_el_mensaje_lleva_instrucciones_fragmentos_y_pregunta(tmp_path):
    brazo, http = crear(tmp_path, "Respuesta [2405.14831].")
    brazo.responder("¿Qué algoritmo usa?")
    assert len(http.solicitudes) == 1
    sistema, usuario = http.solicitudes[0]["messages"]
    assert sistema == {"role": "system", "content": INSTRUCCIONES}
    contenido = usuario["content"]
    assert "paper [2405.14831]" in contenido and "paper [2502.14802]" in contenido
    assert "PageRank personalizado" in contenido and "multisalto" in contenido
    assert contenido.endswith("Pregunta: ¿Qué algoritmo usa?")


def test_hace_una_sola_llamada_con_etiqueta_rag_y_suma_las_metricas(tmp_path):
    brazo, _ = crear(tmp_path, "Respuesta [2405.14831].")
    resultado = brazo.responder("¿Hola?")
    assert resultado.llamadas == 1
    assert (resultado.tokens_entrada, resultado.tokens_salida) == (2000, 80)
    assert resultado.usd > 0
    registro = json.loads((tmp_path / "llamadas.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert registro["etiqueta"] == "rag"


def test_usa_k_y_los_segundos_incluyen_recuperar_y_generar(tmp_path):
    tiempos = iter([10.0, 12.5])
    brazo, _ = crear(tmp_path, "Texto [2405.14831].", k=1, reloj=lambda: next(tiempos))
    resultado = brazo.responder("¿Hola?")
    assert brazo._almacen.consultas == [("¿Hola?", 1)]
    assert resultado.segundos == pytest.approx(2.5)


def test_las_fuentes_son_las_citadas_en_orden_de_primera_cita(tmp_path):
    brazo, _ = crear(tmp_path, "Primero [2502.14802] y luego [2405.14831], otra vez [2502.14802].")
    assert brazo.responder("¿Hola?").fuentes == ("2502.14802", "2405.14831")


def test_un_identificador_citado_que_no_se_recupero_se_ignora():
    recuperados = [recuperado("2405.14831")]
    assert extraer_fuentes("Cita [2999.99999] y [2405.14831].", recuperados) == ["2405.14831"]


def test_acepta_varias_citas_en_un_mismo_corchete():
    recuperados = [recuperado("2405.14831"), recuperado("2502.14802")]
    assert extraer_fuentes("Ambos [2405.14831, 2502.14802].", recuperados) == [
        "2405.14831",
        "2502.14802",
    ]


def test_si_el_corpus_no_tiene_la_respuesta_no_hay_fuentes(tmp_path):
    brazo, _ = crear(tmp_path, "El corpus no contiene esta información.")
    resultado = brazo.responder("¿Cuál es la capital de Francia?")
    assert resultado.fuentes == ()
    assert resultado.respuesta == "El corpus no contiene esta información."


def test_los_numeros_sueltos_entre_corchetes_no_son_fuentes():
    assert extraer_fuentes("Ver [1] y [2024.1] y (2405.14831).", [recuperado("2405.14831")]) == []
