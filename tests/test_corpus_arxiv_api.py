from dataclasses import dataclass

import pytest

from wikillm.corpus.arxiv_api import ClienteApi, ErrorDeApi, parsear_feed
from wikillm.corpus.candidatos import ids_de_bib, reunir

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2601.00001v3</id>
    <updated>2026-03-02T10:00:00Z</updated>
    <published>2026-01-05T09:00:00Z</published>
    <title>Un   paper
      sintético</title>
    <summary>Resumen sintético.</summary>
    <author><name>Ana Pérez</name></author>
    <author><name>Luis Gómez</name></author>
    <arxiv:doi>10.1000/xyz</arxiv:doi>
    <arxiv:journal_ref>Revista X 2026</arxiv:journal_ref>
    <arxiv:primary_category term="cs.CL"/>
    <category term="cs.CL"/>
    <category term="cs.AI"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2512.00002v1</id>
    <updated>2025-12-01T00:00:00Z</updated>
    <published>2025-12-01T00:00:00Z</published>
    <title>Viejo</title>
    <summary>x</summary>
    <author><name>B</name></author>
    <arxiv:primary_category term="cs.IR"/>
  </entry>
  <entry>
    <id>http://arxiv.org/api/errors#incorrect_id_format_for_bad</id>
    <title>Error</title>
  </entry>
</feed>"""


def test_parsear_feed_extrae_campos_y_descarta_errores():
    registros = parsear_feed(FEED)
    assert [r.arxiv_id for r in registros] == ["2601.00001", "2512.00002"]
    primero = registros[0]
    assert primero.version == "v3"
    assert primero.titulo == "Un paper sintético"
    assert primero.autores == ["Ana Pérez", "Luis Gómez"]
    assert primero.fecha_publicacion == "2026-01-05"
    assert primero.fecha_version == "2026-03-02"
    assert primero.categoria == "cs.CL"
    assert primero.categorias == ["cs.CL", "cs.AI"]
    assert primero.doi == "10.1000/xyz"
    assert primero.journal_ref == "Revista X 2026"
    assert registros[1].journal_ref is None


@dataclass
class _Respuesta:
    text: str
    status_code: int = 200


class _Sesion:
    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []

    def get(self, url, params, headers, timeout):
        self.llamadas.append((params, headers))
        return self.respuestas.pop(0)


class _Reloj:
    def __init__(self):
        self.ahora = 0.0
        self.dormido = []

    def __call__(self):
        return self.ahora

    def dormir(self, segundos):
        self.dormido.append(segundos)
        self.ahora += segundos


def test_cliente_espera_tres_segundos_entre_peticiones_y_sin_correo():
    reloj = _Reloj()
    sesion = _Sesion([_Respuesta(FEED), _Respuesta(FEED)])
    cliente = ClienteApi(sesion, dormir=reloj.dormir, reloj=reloj)
    cliente.buscar('abs:"x"')
    cliente.buscar('abs:"y"')
    assert reloj.dormido == [3.0]
    agente = sesion.llamadas[0][1]["User-Agent"]
    assert "@" not in agente


def test_cliente_falla_con_codigo_distinto_de_200():
    sesion = _Sesion([_Respuesta("", status_code=503)])
    with pytest.raises(ErrorDeApi):
        ClienteApi(sesion).por_ids(["2601.00001"])


def test_ids_de_bib_sin_repetidos_y_sin_version():
    bib = "howpublished = {arXiv:2405.14831v3}\nnote={arXiv 2405.14831} x 2607.04576"
    assert ids_de_bib(bib) == ["2405.14831", "2607.04576"]


def test_reunir_filtra_busquedas_por_fecha_pero_no_semillas():
    reloj = _Reloj()
    sesion = _Sesion([_Respuesta(FEED)])
    cliente = ClienteApi(sesion, dormir=reloj.dormir, reloj=reloj)
    filas = reunir(cliente, [], ['abs:"x"'], desde="2026-01-01")
    assert [f["arxiv_id"] for f in filas] == ["2601.00001"]
    assert filas[0]["origen"] == ['busqueda:abs:"x"']

    sesion = _Sesion([_Respuesta(FEED)])
    cliente = ClienteApi(sesion, dormir=reloj.dormir, reloj=reloj)
    filas = reunir(cliente, ["2512.00002", "2601.00001"], [], desde="2026-01-01")
    assert {f["arxiv_id"] for f in filas} == {"2512.00002", "2601.00001"}
