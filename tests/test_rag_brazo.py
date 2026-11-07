"""Brazo RAG con índice y cliente HTTP falsos: no usa red, GPU ni saldo."""

import json
from types import SimpleNamespace

import pytest

from test_responder import AJUSTES
from wikillm.common.modelo import ClienteModelo
from wikillm.common.responder import FRASE_ABSTENCION, Brazo, ResultadoIngesta
from wikillm.rag.brazo import INSTRUCCIONES, BrazoRag, extraer_citas
from wikillm.rag.fragmentos import Fragmento
from wikillm.rag.indice import Recuperado

S1 = "2405.14831#s2.p1"
S2 = "2502.14802#s3.p4"
S3 = "2502.14802#s3.p5"


def recuperado(arxiv_id, span_ids, texto="texto"):
    fragmento = Fragmento(
        f"Paper {arxiv_id} — Sección\n\n" + "\n\n".join(f"[{s}] {texto}" for s in span_ids),
        arxiv_id,
        f"Paper {arxiv_id}",
        "Sección",
        0,
        tuple(span_ids),
    )
    return Recuperado(fragmento, 0.1)


class IndiceFalso:
    def __init__(self, recuperados):
        self.recuperados = recuperados
        self.consultas = []
        self.ingeridos = []

    def recuperar(self, pregunta, k):
        self.consultas.append((pregunta, k))
        return self.recuperados[:k]

    def ingerir(self, arxiv_id):
        self.ingeridos.append(arxiv_id)
        return ResultadoIngesta(0, 0, 0.5, 0.0, 0)


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


RECUPERADOS = [
    recuperado("2405.14831", [S1], "PageRank personalizado sobre el grafo."),
    recuperado("2502.14802", [S2, S3], "Mejora el recobrado en preguntas multisalto."),
]


def crear(tmp_path, texto, recuperados=RECUPERADOS, **kwargs):
    http = ClienteHttpFalso(texto)
    modelo = ClienteModelo(AJUSTES, ruta_registro=tmp_path / "llamadas.jsonl", cliente=http)
    return BrazoRag(modelo, IndiceFalso(recuperados), **kwargs), http


def test_cumple_el_contrato_del_brazo(tmp_path):
    brazo, _ = crear(tmp_path, f"Responde [{S1}].")
    assert isinstance(brazo, Brazo)
    assert brazo.nombre == "rag"


def test_ingerir_delega_en_el_indice_y_devuelve_el_resultado(tmp_path):
    brazo, _ = crear(tmp_path, "x")
    resultado = brazo.ingerir("2405.14831")
    assert brazo._indice.ingeridos == ["2405.14831"]
    assert (resultado.llamadas, resultado.segundos) == (0, 0.5)


def test_el_mensaje_esta_en_ingles_con_span_ids_y_trata_el_contexto_como_datos(tmp_path):
    brazo, http = crear(tmp_path, f"Answer [{S1}].")
    brazo.responder("What algorithm does it use?")
    assert len(http.solicitudes) == 1
    sistema, usuario = http.solicitudes[0]["messages"]
    assert sistema == {"role": "system", "content": INSTRUCCIONES}
    for frase in ("Answer in English", "as data", FRASE_ABSTENCION, "square brackets"):
        assert frase in INSTRUCCIONES
    contenido = usuario["content"]
    assert f"[{S1}] PageRank personalizado" in contenido
    assert f"[{S2}]" in contenido and f"[{S3}]" in contenido
    assert contenido.endswith("Question: What algorithm does it use?")


def test_hace_una_sola_llamada_con_etiqueta_rag_y_suma_las_metricas(tmp_path):
    brazo, _ = crear(tmp_path, f"Answer [{S1}].")
    resultado = brazo.responder("Hello?")
    assert resultado.llamadas == 1
    assert (resultado.tokens_entrada, resultado.tokens_salida) == (2000, 80)
    assert resultado.usd > 0 and resultado.tokens_contexto > 0
    registro = json.loads((tmp_path / "llamadas.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert registro["etiqueta"] == "rag"


def test_usa_k_y_los_segundos_incluyen_recuperar_y_generar(tmp_path):
    tiempos = iter([10.0, 12.5])
    brazo, _ = crear(tmp_path, f"Text [{S1}].", k=1, reloj=lambda: next(tiempos))
    resultado = brazo.responder("Hello?")
    assert brazo._indice.consultas == [("Hello?", 1)]
    assert resultado.segundos == pytest.approx(2.5)


def test_las_citas_son_las_citadas_en_orden_de_primera_cita(tmp_path):
    brazo, _ = crear(tmp_path, f"First [{S2}] then [{S1}], again [{S2}].")
    resultado = brazo.responder("Hello?")
    assert resultado.citas == (S2, S1)
    assert resultado.fuentes == ("2502.14802", "2405.14831")


def test_una_cita_a_un_span_que_no_se_recupero_se_ignora():
    assert extraer_citas(f"Cita [2999.99999#s1.p1] y [{S1}].", RECUPERADOS) == [S1]


def test_una_cita_que_no_existe_en_spans_jsonl_se_ignora():
    assert extraer_citas(f"Dos [{S1}] [{S2}].", RECUPERADOS, spans_validos={S2}) == [S2]


def test_acepta_varias_citas_en_un_mismo_corchete():
    assert extraer_citas(f"Ambos [{S1}, {S2}].", RECUPERADOS) == [S1, S2]


def test_un_paper_o_un_numero_entre_corchetes_no_es_una_cita():
    texto = "Ver [1], [2405.14831] y (2405.14831#s2.p1)."
    assert extraer_citas(texto, RECUPERADOS) == []


def test_la_abstencion_no_lleva_citas_aunque_el_modelo_las_escriba(tmp_path):
    brazo, _ = crear(tmp_path, f"{FRASE_ABSTENCION} [{S1}]")
    resultado = brazo.responder("What is the capital of France?")
    assert resultado.abstuvo and resultado.citas == ()
    assert resultado.respuesta.startswith(FRASE_ABSTENCION)


def test_sin_pasajes_igual_hace_la_llamada_con_un_contexto_vacio(tmp_path):
    brazo, http = crear(tmp_path, FRASE_ABSTENCION, recuperados=[])
    resultado = brazo.responder("Anything?")
    assert len(http.solicitudes) == 1
    assert "(no passages)" in http.solicitudes[0]["messages"][1]["content"]
    assert resultado.abstuvo and resultado.llamadas == 1
