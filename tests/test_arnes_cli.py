"""Orden de consola del arnés con piezas falsas: no abre modelos ni llama a la API."""

import json
from datetime import UTC, datetime

from test_arnes import ORDEN, BrazoFalso
from wikillm.arnes.__main__ import principal
from wikillm.arnes.registro import leer_corrida, leer_lineas

LUNES_PICO = datetime(2026, 11, 9, 2, 0, tzinfo=UTC)
SABADO = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)


def preguntas(*especificaciones):
    return [
        {"id": id_, "texto": f"Question {id_}?", "tipo": tipo, "estado_verificacion": estado}
        for id_, tipo, estado in especificaciones
    ]


def preparar(tmp_path, banco):
    ruta_banco = tmp_path / "banco.jsonl"
    ruta_banco.write_text("\n".join(json.dumps(p) for p in banco) + "\n", encoding="utf-8")
    filas = [{"arxiv_id": a, "orden_ingesta": i} for i, a in enumerate(ORDEN, start=1)]
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("\n".join(json.dumps(f) for f in filas) + "\n", encoding="utf-8")
    return ruta_banco, manifest


class Entorno:
    def __init__(self, tmp_path, banco, ahora=SABADO, falla_en=None):
        self.tmp_path = tmp_path
        self.banco, self.manifest = preparar(tmp_path, banco)
        self.ahora = ahora
        self.falla_en = falla_en
        self.salida = []
        self.fabricas = 0

    def crear_brazos(self, modelo, ajustes, argumentos):
        self.fabricas += 1
        eventos = []
        return [
            BrazoFalso("rag", eventos),
            BrazoFalso("wiki", eventos, con_traza=True, falla_en=self.falla_en),
        ]

    def correr(self, *argv, corrida="c1"):
        return principal(
            [
                "correr",
                "--corrida",
                corrida,
                "--banco",
                str(self.banco),
                "--manifest",
                str(self.manifest),
                "--resultados",
                str(self.tmp_path / "results"),
                "--spans",
                str(self.tmp_path / "no-existe.jsonl"),
                *argv,
            ],
            salida=self.salida.append,
            crear_brazos=self.crear_brazos,
            crear_modelo=lambda ajustes, ruta: object(),
            ahora=lambda: self.ahora,
        )

    @property
    def texto(self):
        return "\n".join(self.salida)

    @property
    def carpeta(self):
        return self.tmp_path / "results" / "c1"


BANCO_MIXTO = preguntas(
    ("A1", "T1", "acordado"), ("A2", "T5", "acordado"), ("A3", "T1", "borrador")
)


def test_estimar_no_crea_brazos_ni_archivos(tmp_path):
    e = Entorno(tmp_path, BANCO_MIXTO)
    assert e.correr("--pasos", "0,2", "--estimar") == 0
    assert e.fabricas == 0 and not (tmp_path / "results").exists()
    assert "2 preguntas × 2 pasos × 2 brazos = 8 respuestas" in e.texto
    assert "Estimado (cota alta)" in e.texto


def test_por_defecto_solo_las_acordadas_y_la_corrida_vale_para_el_informe(tmp_path):
    e = Entorno(tmp_path, BANCO_MIXTO)
    assert e.correr("--pasos", "0,2") == 0
    datos = leer_corrida(e.carpeta / "corrida.json")
    assert datos["banco"]["preguntas"] == ["A1", "A2"] and datos["valida_para_informe"] is True
    assert len(leer_lineas(e.carpeta / "respuestas.jsonl")) == 2 * 2 * 2
    assert "NO vale para el informe" not in e.texto
    assert "wikillm.eval metricas" in e.texto and "Resumen de c1" in e.texto


def test_un_piloto_con_borradores_lo_avisa_y_queda_marcado_como_no_valido(tmp_path):
    e = Entorno(tmp_path, BANCO_MIXTO)
    assert e.correr("--pasos", "0", "--estado-minimo", "borrador", "--tipos", "T1") == 0
    datos = leer_corrida(e.carpeta / "corrida.json")
    assert datos["valida_para_informe"] is False and datos["banco"]["preguntas"] == ["A1", "A3"]
    assert e.texto.count("NO vale para el informe") == 2  # al empezar y al terminar


def test_los_metadatos_tienen_lo_necesario_para_reproducir(tmp_path):
    e = Entorno(tmp_path, BANCO_MIXTO)
    e.correr("--pasos", "0,3", "--k", "7", "--max-acciones", "4")
    datos = leer_corrida(e.carpeta / "corrida.json")
    assert datos["pasos"] == [0, 3] and datos["brazos"] == {
        "rag": {"k": 7},
        "wiki": {"max_acciones": 4},
    }
    assert datos["modelo"] and len(datos["banco"]["sha256"]) == 64
    assert datos["inicio"] == "2026-11-07T12:00:00Z" and datos["fin"] == "2026-11-07T12:00:00Z"
    assert datos["gasto_usd"] > 0 and "commit" in datos and "precios_usd_por_millon" in datos


def test_ninguna_pregunta_cumple_el_filtro_devuelve_codigo_1_sin_brazos(tmp_path, capsys):
    e = Entorno(tmp_path, preguntas(("X1", "T1", "borrador")))
    assert e.correr("--pasos", "0") == 1
    assert "Ninguna pregunta" in capsys.readouterr().err and e.fabricas == 0


def test_pasos_fuera_del_corpus_devuelven_codigo_1(tmp_path, capsys):
    e = Entorno(tmp_path, BANCO_MIXTO)
    assert e.correr("--pasos", "0,9") == 1
    assert "Pasos no válidos" in capsys.readouterr().err


def test_mas_de_5_usd_sin_confirmar_se_niega(tmp_path, capsys):
    grande = preguntas(*[(f"Q{i:03d}", "T1", "acordado") for i in range(300)])
    e = Entorno(tmp_path, grande)
    assert e.correr("--pasos", "0,1,2,3") == 1
    assert "--confirmo-usd" in capsys.readouterr().err
    assert e.fabricas == 0 and not (tmp_path / "results").exists()


def test_en_hora_pico_se_avisa_pero_no_se_bloquea(tmp_path):
    e = Entorno(tmp_path, BANCO_MIXTO, ahora=LUNES_PICO)
    assert e.correr("--pasos", "0") == 0
    assert "hora pico" in e.texto


def test_un_fallo_del_modelo_devuelve_1_conserva_lo_escrito_e_indica_como_reanudar(
    tmp_path, capsys
):
    e = Entorno(tmp_path, BANCO_MIXTO, falla_en=1)
    assert e.correr("--pasos", "0") == 1
    err = capsys.readouterr().err
    assert "Tope alcanzado" in err and "misma --corrida" in err
    assert "fin" not in leer_corrida(e.carpeta / "corrida.json")
    assert [f["system"] for f in leer_lineas(e.carpeta / "respuestas.jsonl")] == ["rag"]


def test_repetir_la_orden_reanuda_y_registra_la_reanudacion(tmp_path):
    e = Entorno(tmp_path, BANCO_MIXTO, falla_en=1)
    e.correr("--pasos", "0")
    e.falla_en = None
    assert e.correr("--pasos", "0") == 0
    datos = leer_corrida(e.carpeta / "corrida.json")
    assert len(datos["reanudaciones"]) == 1 and "fin" in datos
    claves = [(f["question_id"], f["system"]) for f in leer_lineas(e.carpeta / "respuestas.jsonl")]
    assert len(claves) == len(set(claves)) == 4
    assert "Se reanuda la corrida c1" in e.texto


def test_no_se_reanuda_con_otro_banco_ni_otros_pasos(tmp_path, capsys):
    e = Entorno(tmp_path, BANCO_MIXTO)
    e.correr("--pasos", "0")
    assert e.correr("--pasos", "0,2") == 1
    assert "'pasos'" in capsys.readouterr().err
    e.banco.write_text(json.dumps(preguntas(("A9", "T1", "acordado"))[0]) + "\n", encoding="utf-8")
    assert e.correr("--pasos", "0") == 1
    assert "cambiaron" in capsys.readouterr().err


def test_dos_corridas_con_otro_nombre_no_comparten_resultados(tmp_path):
    e = Entorno(tmp_path, BANCO_MIXTO)
    e.correr("--pasos", "0", corrida="c1")
    e.correr("--pasos", "0", corrida="c2")
    for nombre in ("c1", "c2"):
        assert len(leer_lineas(tmp_path / "results" / nombre / "respuestas.jsonl")) == 4
