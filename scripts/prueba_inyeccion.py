"""Prueba de inyección de instrucciones en los documentos (rúbrica R.6.2, Cr7).

Siembra órdenes con un canario en copias temporales de lo que ven el RAG y el agente del wiki, y
mide si la respuesta las obedece. No toca el Gold, el índice ni el wiki reales, ni los prompts.
Diseño y límites: ``openspec/changes/2026-11-17-prueba-inyeccion`` y
``docs/prueba-de-inyeccion.md``.

Uso (desde la raíz del repo):
  python scripts/prueba_inyeccion.py --estimar     # cuenta ejecuciones y costo, sin gastar
  python scripts/prueba_inyeccion.py --ejecutar    # gasta unos 0,10 USD (tope 0,25)

Es reanudable: las ejecuciones ya guardadas en ``results/inyeccion/respuestas.jsonl`` no se repiten.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

from wikillm.common.config import load_settings
from wikillm.common.modelo import ClienteModelo
from wikillm.eval.inyeccion import (
    ATAQUES_DE_INGESTA,
    CONTROL,
    POSICIONES,
    Ataque,
    ataques_de,
    conserva_claves,
    contiene_evidencia,
    elegir_preguntas,
    exito_del_ataque,
    insertar_en_gold,
    resumir,
    sembrar,
)
from wikillm.rag.brazo import construir_mensajes
from wikillm.wiki.almacen import Wiki
from wikillm.wiki.consulta import ConsultaWiki
from wikillm.wiki.ingesta import Ingestor

TOPE_USD = 0.25
PASO = 100
K = 5
PREGUNTAS = 6
SEMILLA = 17
USD_ESTIMADO = 0.10


def leer_jsonl(ruta: Path) -> list[dict[str, Any]]:
    if not ruta.exists():
        return []
    return [json.loads(x) for x in ruta.read_text("utf-8").splitlines() if x.strip()]


def elegibles(corrida: Path, banco: Path) -> list[dict[str, Any]]:
    """Preguntas de un solo paper, con clave, que ambos brazos contestaron bien en el paso 100.

    Así, si la respuesta falla bajo ataque, la causa es el ataque y no una pregunta difícil.
    """
    bien: dict[str, set[str]] = {}
    for e in leer_jsonl(corrida / "evaluados.jsonl"):
        if e["ingest_step"] == PASO and e["veredicto"] == "correcta":
            bien.setdefault(e["question_id"], set()).add(e["system"])
    preguntas = {p["id"]: p for p in leer_jsonl(banco)}
    return [
        p
        for q, sistemas in sorted(bien.items())
        if sistemas == {"rag", "wiki"}
        and (p := preguntas[q])["respuesta_clave"]
        and len(p["fuentes_requeridas"]) == 1
    ]


def con_evidencia_recuperada(indice: Any, preguntas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Solo las preguntas cuyo fragmento de evidencia llega al contexto del RAG: así el ataque
    «en la evidencia» siempre se expone."""
    return [
        p
        for p in preguntas
        if any(
            contiene_evidencia(r.fragmento.texto, [e["span_id"] for e in p["evidencia"]])
            for r in indice.recuperar(p["texto"], K)
        )
    ]


def contar(n: int) -> dict[str, int]:
    rag = n * (len(ataques_de("rag")) * len(POSICIONES) + 1)
    wiki = n * (len(ataques_de("wiki")) * len(POSICIONES) + 1)
    return {"rag": rag, "wiki": wiki, "ingesta": 3, "consultas_ingesta": 3}


class Registro:
    """Filas ya guardadas y escritura incremental, para no repetir lo ya pagado."""

    def __init__(self, ruta: Path) -> None:
        self.ruta = ruta
        self.filas = leer_jsonl(ruta)
        self.claves = {self.clave(f) for f in self.filas}

    @staticmethod
    def clave(f: dict[str, Any]) -> tuple[str, str, str, str]:
        return f["brazo"], f["ataque"], f["posicion"], f["question_id"]

    def hecho(self, brazo: str, ataque: str, posicion: str, qid: str) -> bool:
        return (brazo, ataque, posicion, qid) in self.claves

    def agregar(self, fila: dict[str, Any]) -> None:
        self.filas.append(fila)
        self.claves.add(self.clave(fila))
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        with self.ruta.open("a", encoding="utf-8") as f:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")


def fila_de(
    brazo: str,
    ataque: Ataque | None,
    posicion: str,
    pregunta: dict[str, Any],
    respuesta: str,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "brazo": brazo,
        "ataque": ataque.clave if ataque else CONTROL,
        "posicion": posicion,
        "question_id": pregunta["id"],
        "respuesta": respuesta,
        "exito": exito_del_ataque(ataque, respuesta) if ataque else False,
        "conserva_claves": conserva_claves(pregunta["respuesta_clave"], respuesta),
        **extra,
    }


# --- RAG --------------------------------------------------------------------------------------


def abrir_indice(gold: Path, indice: Path, manifest: Path) -> Any:
    from wikillm.rag.indice import IndiceRag, crear_embeddings, medidor_de_tokens

    ajustes = load_settings()
    almacen = IndiceRag(
        gold,
        indice,
        embeddings=crear_embeddings(ajustes),
        medir=medidor_de_tokens(ajustes.embedding_model),
        modelo_embeddings=ajustes.embedding_model,
    )
    for linea in manifest.read_text("utf-8").splitlines():
        if linea.strip():
            almacen.ingerir(json.loads(linea)["arxiv_id"])
    return almacen


def contexto_de(textos: list[str]) -> str:
    return "\n\n".join(f"Passage {i}\n{t}" for i, t in enumerate(textos, start=1))


def correr_rag(
    modelo: ClienteModelo, indice: Any, preguntas: list[dict], registro: Registro
) -> None:
    for p in preguntas:
        recuperados = indice.recuperar(p["texto"], K)
        textos = [r.fragmento.texto for r in recuperados]
        spans = [e["span_id"] for e in p["evidencia"]]
        con_evidencia = [i for i, t in enumerate(textos) if contiene_evidencia(t, spans)]
        sin_evidencia = [i for i in range(len(textos)) if i not in con_evidencia]
        # el fragmento de la evidencia mejor ubicado y el peor ubicado de los que no la tienen
        destinos = {
            "evidencia": con_evidencia[0] if con_evidencia else None,
            "otro": sin_evidencia[-1] if sin_evidencia else None,
        }
        casos: list[tuple[Ataque | None, str, int | None]] = [(None, "-", None)]
        casos += [(a, pos, destinos[pos]) for a in ataques_de("rag") for pos in POSICIONES]
        for ataque, posicion, indice_destino in casos:
            clave = ataque.clave if ataque else CONTROL
            if registro.hecho("rag", clave, posicion, p["id"]):
                continue
            if ataque and indice_destino is None:
                registro.agregar(
                    fila_de("rag", ataque, posicion, p, "", no_aplica=True, expuesto=False)
                    | {"exito": False, "conserva_claves": False}
                )
                continue
            fragmentos = list(textos)
            if ataque and indice_destino is not None:
                fragmentos[indice_destino] = sembrar(fragmentos[indice_destino], ataque)
            antes = modelo.gasto_acumulado
            llamada = modelo.generar(
                construir_mensajes(p["texto"], contexto_de(fragmentos)), etiqueta="inyeccion-rag"
            )
            registro.agregar(
                fila_de(
                    "rag",
                    ataque,
                    posicion,
                    p,
                    llamada.texto,
                    expuesto=True,
                    usd=round(modelo.gasto_acumulado - antes, 6),
                )
            )
            print(f"rag {clave:>7} {posicion:<9} {p['id']}")


# --- consulta del wiki ------------------------------------------------------------------------


def _palabras(texto: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{4,}", texto.lower()))


def elegir_paginas(wiki: Wiki, p: dict[str, Any], leidas: list[str]) -> dict[str, str | None]:
    """Página de la evidencia y página ajena que el agente ya leía en el control (o la más afín)."""
    spans = [e["span_id"] for e in p["evidencia"]]
    arxiv = p["fuentes_requeridas"][0]
    textos = {s: wiki.leer(s).a_texto() for s in wiki.slugs()}
    con_evidencia = [s for s in leidas if contiene_evidencia(textos[s], spans)] or [
        s for s in leidas if arxiv in textos[s]
    ]
    ajenas = [s for s in leidas if s not in con_evidencia]
    if not ajenas:
        pregunta = _palabras(p["texto"])
        candidatas = [s for s in textos if s not in con_evidencia and arxiv not in textos[s]]
        candidatas.sort(key=lambda s: -len(pregunta & _palabras(textos[s])))
        ajenas = candidatas[:1]
    return {
        "evidencia": con_evidencia[0] if con_evidencia else None,
        "otro": ajenas[0] if ajenas else None,
    }


def consultar(modelo: ClienteModelo, wiki: Wiki, pregunta: str) -> tuple[Any, ConsultaWiki]:
    agente = ConsultaWiki(modelo, wiki)
    return agente.responder(pregunta), agente


def correr_wiki(
    modelo: ClienteModelo, origen: Path, preguntas: list[dict], registro: Registro, tmp: Path
) -> None:
    wiki = Wiki.clonar_desde(origen, tmp / "wiki-consulta")
    wiki.situar_en_paso(PASO)
    for p in preguntas:
        pendientes = [
            (a, pos)
            for a in ataques_de("wiki")
            for pos in POSICIONES
            if not registro.hecho("wiki", a.clave, pos, p["id"])
        ]
        control_hecho = registro.hecho("wiki", CONTROL, "-", p["id"])
        if control_hecho and not pendientes:
            continue
        antes = modelo.gasto_acumulado
        resultado, agente = consultar(modelo, wiki, p["texto"])
        leidas = list(agente.traza.paginas_leidas)
        if not control_hecho:
            registro.agregar(
                fila_de(
                    "wiki",
                    None,
                    "-",
                    p,
                    resultado.respuesta,
                    expuesto=True,
                    acciones=agente.traza.acciones,
                    paginas_leidas=leidas,
                    usd=round(modelo.gasto_acumulado - antes, 6),
                )
            )
            print(f"wiki control {p['id']}")
        destinos = elegir_paginas(wiki, p, leidas)
        for ataque, posicion in pendientes:
            slug = destinos[posicion]
            if slug is None:
                registro.agregar(
                    fila_de("wiki", ataque, posicion, p, "", no_aplica=True, expuesto=False)
                    | {"exito": False, "conserva_claves": False}
                )
                continue
            original = wiki.leer(slug)
            wiki.escribir(replace(original, cuerpo=sembrar(original.cuerpo, ataque)))
            try:
                antes = modelo.gasto_acumulado
                resultado, agente = consultar(modelo, wiki, p["texto"])
            finally:
                wiki.escribir(original)  # la copia queda limpia para la pregunta siguiente
            registro.agregar(
                fila_de(
                    "wiki",
                    ataque,
                    posicion,
                    p,
                    resultado.respuesta,
                    pagina_sembrada=slug,
                    expuesto=slug in agente.traza.paginas_leidas,
                    acciones=agente.traza.acciones,
                    paginas_leidas=list(agente.traza.paginas_leidas),
                    usd=round(modelo.gasto_acumulado - antes, 6),
                )
            )
            print(f"wiki {ataque.clave:>7} {posicion:<9} {p['id']} ({slug})")


# --- ingesta envenenada -----------------------------------------------------------------------


def correr_ingesta(
    modelo: ClienteModelo, gold: Path, preguntas: list[dict], registro: Registro, tmp: Path
) -> None:
    """Tres papers en un wiki vacío: uno limpio y dos envenenados (IA e IB)."""
    por_paper = {p["fuentes_requeridas"][0]: p for p in preguntas}
    papers = sorted(por_paper)[:3]
    if len(papers) < 3:
        return
    sembrados = dict(zip(papers[1:], ATAQUES_DE_INGESTA, strict=True))
    carpeta_gold = tmp / "gold-envenenado"
    carpeta_gold.mkdir(parents=True)
    for arxiv in papers:
        texto = (gold / f"{arxiv}.md").read_text("utf-8")
        if arxiv in sembrados:
            texto = insertar_en_gold(texto, sembrados[arxiv])
        (carpeta_gold / f"{arxiv}.md").write_text(texto, encoding="utf-8")
    wiki = Wiki(tmp / "wiki-ingesta")
    ingestor = Ingestor(modelo, wiki, carpeta_gold)
    for arxiv in papers:
        ataque = sembrados.get(arxiv)
        pregunta = por_paper[arxiv]
        clave = ataque.clave if ataque else CONTROL
        if registro.hecho("ingesta", clave, "ingesta", pregunta["id"]):
            continue
        antes = modelo.gasto_acumulado
        try:
            ingestor.ingerir(arxiv)
            error = None
        except Exception as e:  # noqa: BLE001 - el fallo de formato también es un resultado
            error = f"{type(e).__name__}: {e}"
        paginas = {s: wiki.leer(s).a_texto() for s in wiki.slugs()}
        canarios = [a.canario for a in ATAQUES_DE_INGESTA]
        persistio = {
            c: sorted(s for s, t in paginas.items() if c.lower() in t.lower()) for c in canarios
        }
        registro.agregar(
            {
                "brazo": "ingesta",
                "ataque": clave,
                "posicion": "ingesta",
                "question_id": pregunta["id"],
                "paper": arxiv,
                "respuesta": "",
                "exito": bool(ataque and persistio[ataque.canario]),
                "conserva_claves": False,
                "error_de_ingesta": error,
                "paginas_con_canario": persistio,
                "usd": round(modelo.gasto_acumulado - antes, 6),
            }
        )
        print(f"ingesta {clave:>7} {arxiv}: {error or 'ok'} {persistio}")
    for arxiv in papers:  # una pregunta por paper sobre el wiki resultante
        ataque = sembrados.get(arxiv)
        pregunta = por_paper[arxiv]
        clave = ataque.clave if ataque else CONTROL
        if registro.hecho("ingesta-consulta", clave, "consulta", pregunta["id"]):
            continue
        if arxiv not in wiki.ingeridos:
            continue
        antes = modelo.gasto_acumulado
        resultado, agente = consultar(modelo, wiki, pregunta["texto"])
        registro.agregar(
            fila_de(
                "ingesta-consulta",
                ataque,
                "consulta",
                pregunta,
                resultado.respuesta,
                expuesto=True,
                acciones=agente.traza.acciones,
                usd=round(modelo.gasto_acumulado - antes, 6),
            )
        )
        print(f"consulta tras ingesta {clave:>7} {pregunta['id']}")


# --- resumen ----------------------------------------------------------------------------------


def escribir_resumen(salida: Path, registro: Registro, preguntas: list[dict]) -> None:
    filas = [f for f in registro.filas if not f.get("no_aplica")]
    resumen = resumir(filas)
    gasto = round(sum(f.get("usd", 0) for f in registro.filas), 4)
    (salida / "resumen.json").write_text(
        json.dumps(
            {"preguntas": [p["id"] for p in preguntas], "usd": gasto, "grupos": resumen},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    lineas = [
        "| Brazo | Ataque | Posición | n | Ataque logrado | Conserva las claves |",
        "|---|---|---|--:|--:|--:|",
    ]
    for g in resumen:
        lineas.append(
            f"| {g['brazo']} | {g['ataque']} | {g['posicion']} | {g['n']} | "
            f"{g['exitos']} | {g['utiles']} |"
        )
    (salida / "resumen.md").write_text("\n".join(lineas) + f"\n\nGasto: {gasto} USD\n", "utf-8")
    print("\n".join(lineas), f"\nGasto: {gasto} USD")


def main() -> None:
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    a.add_argument("--corrida", type=Path, default=Path("results/ampliado-fases-1"))
    a.add_argument("--banco", type=Path, default=Path("data/preguntas/banco_100.jsonl"))
    a.add_argument("--gold", type=Path, default=Path("data/corpus100/gold"))
    a.add_argument("--manifest", type=Path, default=Path("data/corpus100/manifest.jsonl"))
    a.add_argument("--indice-rag", type=Path, default=Path("data/qdrant/ampliado-fases-1"))
    a.add_argument("--wiki", type=Path, default=Path("data/wiki/construccion-1"))
    a.add_argument("--salida", type=Path, default=Path("results/inyeccion"))
    a.add_argument("--estimar", action="store_true")
    a.add_argument("--ejecutar", action="store_true")
    args = a.parse_args()

    indice = abrir_indice(args.gold, args.indice_rag, args.manifest)
    candidatas = con_evidencia_recuperada(indice, elegibles(args.corrida, args.banco))
    preguntas = elegir_preguntas(candidatas, PREGUNTAS, SEMILLA)
    cuenta = contar(len(preguntas))
    print(f"Preguntas ({len(preguntas)}, semilla {SEMILLA}): {[p['id'] for p in preguntas]}")
    print(f"Ejecuciones previstas: {cuenta}; estimado {USD_ESTIMADO} USD, tope {TOPE_USD} USD")
    if not args.ejecutar:
        print("Sin --ejecutar no se llama al modelo.")
        return

    args.salida.mkdir(parents=True, exist_ok=True)
    ajustes = replace(load_settings(), max_usd_per_run=TOPE_USD)
    modelo = ClienteModelo(ajustes, ruta_registro=args.salida / "llamadas.jsonl")
    registro = Registro(args.salida / "respuestas.jsonl")
    tmp = Path(tempfile.mkdtemp(prefix="inyeccion-"))
    try:
        correr_rag(modelo, indice, preguntas, registro)
        correr_wiki(modelo, args.wiki, preguntas, registro, tmp)
        correr_ingesta(modelo, args.gold, preguntas, registro, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        escribir_resumen(args.salida, registro, preguntas)


if __name__ == "__main__":
    main()
