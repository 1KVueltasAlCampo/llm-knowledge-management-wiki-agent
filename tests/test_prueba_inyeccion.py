"""Flujo completo de scripts/prueba_inyeccion.py con un modelo falso: sin red ni saldo."""

import importlib.util
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from test_responder import AJUSTES
from wikillm.common.modelo import ClienteModelo
from wikillm.wiki.almacen import Pagina, Wiki

RAIZ = Path(__file__).resolve().parents[1]
GOLD_IDS = ("2601.00001", "2601.00002", "2601.00003")
CUERPO = "# T\n\n## 1 Intro\n\nUno.\n\n## 2 Metodo\n\nEl umbral es 0.8.\n\nDos.\n"


def cargar_script():
    spec = importlib.util.spec_from_file_location(
        "prueba_inyeccion", RAIZ / "scripts" / "prueba_inyeccion.py"
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class ModeloFalso:
    """Responde según lo que pide el prompt. ``obedece``: sigue las órdenes sembradas."""

    def __init__(self, obedece):
        self.obedece = obedece
        self.chat = SimpleNamespace(completions=self)

    def create(self, **argumentos):
        mensajes = argumentos["messages"]
        sistema, ultimo = mensajes[0]["content"], mensajes[-1]["content"]
        todo = "\n".join(m["content"] for m in mensajes)
        canario = re.search(r"PWNED-\d{4}", todo)
        if "TASK: PLAN" in ultimo:
            texto = json.dumps({"update": [], "create": []})
        elif "TASK: WRITE" in ultimo:
            slug = re.search(r"the paper page `([^`]+)`", ultimo).group(1)
            cuerpo = "El umbral es 0.8."
            if self.obedece and canario:
                cuerpo += f" Verified: {canario.group(0)}."
            texto = json.dumps(
                {
                    "pages": [
                        {
                            "slug": slug,
                            "title": slug,
                            "type": "paper",
                            "summary": "Resumen.",
                            "body": cuerpo,
                        }
                    ]
                }
            )
        elif '"action"' in sistema:  # agente del wiki
            if sum(m["role"] == "assistant" for m in mensajes) == 0:
                texto = json.dumps({"action": "read", "pages": ["pagina-uno"]})
            else:
                respuesta = "Reply: " + canario.group(0) if self.obedece and canario else "0.8"
                texto = json.dumps({"action": "answer", "answer": respuesta})
        else:  # RAG
            texto = f"{canario.group(0)}" if self.obedece and canario else "El umbral es 0.8."
        uso = SimpleNamespace(
            prompt_tokens=1000,
            prompt_cache_hit_tokens=0,
            prompt_cache_miss_tokens=1000,
            completion_tokens=50,
            completion_tokens_details=SimpleNamespace(reasoning_tokens=0),
        )
        mensaje = SimpleNamespace(content=texto)
        return SimpleNamespace(choices=[SimpleNamespace(message=mensaje)], usage=uso)


class IndiceFalso:
    def __init__(self, span_id):
        textos = [f"[{span_id}] El umbral es 0.8.", "Otro texto.", "Otro más.", "Y otro."]
        spans = [(span_id,), ("2601.00009#s1.p1",), ("2601.00009#s1.p2",), ("2601.00009#s1.p3",)]
        self.recuperados = [
            SimpleNamespace(fragmento=SimpleNamespace(texto=t, span_ids=s), distancia=0.1)
            for t, s in zip(textos, spans, strict=True)
        ]

    def recuperar(self, consulta, k):
        return self.recuperados[:k]


@pytest.fixture
def entorno(tmp_path):
    gold = tmp_path / "gold"
    gold.mkdir()
    for arxiv in GOLD_IDS:
        cabecera = yaml.safe_dump({"arxiv_id": arxiv, "titulo": f"Paper {arxiv}", "version": "v1"})
        (gold / f"{arxiv}.md").write_text(f"---\n{cabecera}---\n\n{CUERPO}", encoding="utf-8")
    origen = Wiki(tmp_path / "origen")
    origen.escribir(
        Pagina(
            slug="pagina-uno",
            titulo="Pagina uno",
            tipo="paper",
            resumen="Resumen.",
            fuentes=[GOLD_IDS[0]],
            actualizada_en_paso=1,
            cuerpo=f"El umbral es 0.8 [{GOLD_IDS[0]}#s2.p1].",
        )
    )
    origen.guardar_copia(100, "paso 100")
    preguntas = [
        {
            "id": f"Q{i}",
            "texto": "What is the threshold?",
            "respuesta_clave": ["0.8"],
            "fuentes_requeridas": [arxiv],
            "evidencia": [{"span_id": f"{arxiv}#s2.p1"}],
        }
        for i, arxiv in enumerate(GOLD_IDS)
    ]
    return SimpleNamespace(tmp=tmp_path, gold=gold, origen=origen, preguntas=preguntas)


def modelo_de(tmp_path, obedece):
    return ClienteModelo(
        AJUSTES, ruta_registro=tmp_path / "llamadas.jsonl", cliente=ModeloFalso(obedece)
    )


def correr_todo(entorno, obedece):
    script = cargar_script()
    modelo = modelo_de(entorno.tmp, obedece)
    registro = script.Registro(entorno.tmp / "salida" / "respuestas.jsonl")
    trabajo = entorno.tmp / "trabajo"
    trabajo.mkdir()
    script.correr_rag(modelo, IndiceFalso(f"{GOLD_IDS[0]}#s2.p1"), entorno.preguntas[:1], registro)
    script.correr_wiki(modelo, entorno.origen.carpeta, entorno.preguntas[:1], registro, trabajo)
    script.correr_ingesta(modelo, entorno.gold, entorno.preguntas, registro, trabajo)
    return script, registro


def por_clave(registro, brazo):
    return {(f["ataque"], f["posicion"]): f for f in registro.filas if f["brazo"] == brazo}


def test_un_modelo_que_obedece_cae_en_todos_los_ataques_y_el_control_queda_limpio(entorno):
    _, registro = correr_todo(entorno, obedece=True)
    rag, wiki = por_clave(registro, "rag"), por_clave(registro, "wiki")
    assert len(rag) == 5 and len(wiki) == 7  # control + 2 ataques x 2 posiciones; con C, 3 x 2
    assert not rag[("control", "-")]["exito"] and rag[("control", "-")]["conserva_claves"]
    assert all(f["exito"] for k, f in rag.items() if k[0] != "control")
    # con una sola página en el wiki no hay página ajena: esas filas quedan como "no aplica"
    assert all(f.get("no_aplica") for k, f in wiki.items() if k[1] == "otro")
    # la página de la evidencia sí se lee, así que el ataque llega y gana
    leidas = [f for k, f in wiki.items() if k[0] != "control" and k[1] == "evidencia"]
    assert len(leidas) == 3 and all(f["exito"] and f["expuesto"] for f in leidas)
    assert not any(k[0] == "C" for k in rag)


def test_un_modelo_que_ignora_las_ordenes_conserva_las_claves(entorno):
    _, registro = correr_todo(entorno, obedece=False)
    ataques = [
        f
        for f in registro.filas
        if f["brazo"] in {"rag", "wiki"} and f["ataque"] != "control" and not f.get("no_aplica")
    ]
    assert ataques and not any(f["exito"] for f in ataques)
    assert all(f["conserva_claves"] for f in ataques)


def test_la_ingesta_envenenada_registra_si_el_canario_quedo_en_el_wiki(entorno):
    _, registro = correr_todo(entorno, obedece=True)
    ingesta = {f["ataque"]: f for f in registro.filas if f["brazo"] == "ingesta"}
    assert set(ingesta) == {"control", "IA", "IB"}
    assert ingesta["IA"]["exito"] and ingesta["IB"]["exito"] and not ingesta["control"]["exito"]
    consultas = {f["ataque"]: f for f in registro.filas if f["brazo"] == "ingesta-consulta"}
    assert set(consultas) == {"control", "IA", "IB"}


def test_el_wiki_original_y_la_copia_no_conservan_el_ataque(entorno):
    correr_todo(entorno, obedece=True)
    assert "PWNED" not in entorno.origen.leer("pagina-uno").a_texto()


def test_lo_ya_guardado_no_se_repite(entorno):
    script, registro = correr_todo(entorno, obedece=False)
    filas = len(registro.filas)
    reabierto = script.Registro(registro.ruta)
    modelo = modelo_de(entorno.tmp, False)
    script.correr_rag(modelo, IndiceFalso(f"{GOLD_IDS[0]}#s2.p1"), entorno.preguntas[:1], reabierto)
    assert len(reabierto.filas) == filas and modelo.gasto_acumulado == 0
