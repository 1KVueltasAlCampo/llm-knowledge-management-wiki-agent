import json
import re

from wikillm.eval.revision import escribir_html, preparar_items

MANIFEST = [{"arxiv_id": "2601.1", "orden_ingesta": 1, "version": "v2", "titulo": "Uno"}]
PREGUNTA = {
    "id": "A001-T1-01",
    "texto": "¿Qué exactitud reporta?",
    "tipo": "T1",
    "respuesta_oraculo": "0.71",
    "respuesta_clave": ["0.71"],
    "evidencia": [{"span_id": "2601.1#s1.p1", "sha256": "x"}],
    "fuentes_requeridas": ["2601.1"],
    "ingesta_minima": 1,
    "autor": "A",
    "estado_verificacion": "borrador",
}


def test_items_traen_cita_fuente_versionada_y_problemas():
    con_clave_en_pregunta = {**PREGUNTA, "id": "A001-T1-02", "respuesta_clave": ["exactitud"]}
    citas = [{"question_id": "A001-T1-01", "span_id": "2601.1#s1.p1", "cita": "accuracy 0.71"}]
    items = preparar_items([PREGUNTA, con_clave_en_pregunta], citas, MANIFEST)
    assert items[0]["evidencias"] == [{"span_id": "2601.1#s1.p1", "cita": "accuracy 0.71"}]
    assert items[0]["fuentes"][0]["url"] == "https://arxiv.org/html/2601.1v2"
    assert items[0]["problemas"] == []
    assert any("presente en la pregunta" in p for p in items[1]["problemas"])


def test_html_embebe_los_datos_sin_romper_el_script(tmp_path):
    citas = [{"question_id": "A001-T1-01", "span_id": "s", "cita": "x </script><b>y"}]
    ruta = tmp_path / "r.html"
    escribir_html(ruta, preparar_items([PREGUNTA], citas, MANIFEST), "A")
    html = ruta.read_text(encoding="utf-8")
    assert html.count("</script>") == 1  # solo el cierre real
    datos = re.search(r"const ITEMS = (.*);\nconst AUTOR", html).group(1)
    assert json.loads(datos.replace("<\\/", "</"))[0]["evidencias"][0]["cita"] == "x </script><b>y"
    assert 'const AUTOR = "A"' in html
