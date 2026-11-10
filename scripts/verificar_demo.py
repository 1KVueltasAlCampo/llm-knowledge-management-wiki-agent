"""Revisión previa de la demostración: comprueba que lo necesario está en su sitio.

No llama al modelo ni gasta saldo, y no imprime ningún secreto. Para probar además la conexión
con el proveedor (cuesta menos de un centavo): uv run python scripts/probar_modelo.py

Uso: uv run python scripts/verificar_demo.py
"""

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

from wikillm.common.config import load_settings

REVISIONES: list[tuple[str, bool, str]] = []


def revisar(nombre: str, correcto: bool, detalle: str = "") -> None:
    REVISIONES.append((nombre, correcto, detalle))


def fragmentos_del_panel() -> int | None:
    """Fragmentos del índice que tiene abierto el panel, o None si no corre o no lo cargó.

    Qdrant local deja abrir su carpeta a un solo proceso: si el panel la tiene abierta, esta
    revisión no puede abrirla y le pregunta al panel.
    """
    url = os.environ.get("WIKILLM_PANEL_URL", "http://127.0.0.1:8765/").rstrip("/")
    try:
        with urllib.request.urlopen(f"{url}/api/estado", timeout=2) as respuesta:
            return json.load(respuesta).get("rag_fragmentos")
    except (OSError, ValueError):
        return None


def leer_jsonl(ruta: Path) -> list[dict]:
    return [json.loads(x) for x in ruta.read_text("utf-8").splitlines() if x.strip()]


def main() -> int:
    ajustes = load_settings()
    revisar("clave de la API en .env", bool(ajustes.api_key), f"modelo {ajustes.model}")
    revisar(
        "tope de gasto por corrida", ajustes.max_usd_per_run > 0, f"{ajustes.max_usd_per_run} USD"
    )

    manifest = Path("data/manifest_corpus.jsonl")
    orden = [f["arxiv_id"] for f in sorted(leer_jsonl(manifest), key=lambda f: f["orden_ingesta"])]
    revisar("manifest con 50 papers", len(orden) == 50, f"{len(orden)} papers")
    # Gold may hold extra papers outside the corpus (e.g. the out-of-corpus papers behind the T5
    # drafts); what matters is that every paper of the manifest has its Gold file.
    faltan = [a for a in orden if not Path(f"data/gold/{a}.md").exists()]
    revisar(
        "Gold local de los papers del manifest",
        bool(orden) and not faltan,
        f"faltan {len(faltan)}: {', '.join(faltan[:3])}" if faltan else f"{len(orden)} papers",
    )
    revisar("fragmentos citables (spans.jsonl)", Path("data/gold/spans.jsonl").exists())

    try:
        import torch

        revisar("GPU para los embeddings", torch.cuda.is_available(), ajustes.embedding_device)
    except ImportError:
        revisar("GPU para los embeddings", False, "torch no está instalado")

    total = fragmentos_del_panel()
    if total is not None:
        detalle = f"{total} fragmentos (abierto en el panel)"
        revisar("índice vectorial del RAG", total > 5000, detalle)
    else:
        try:
            from qdrant_client import QdrantClient

            from wikillm.rag.indice import NOMBRE_COLECCION, RUTA_INDICE_POR_DEFECTO

            cliente = QdrantClient(path=str(RUTA_INDICE_POR_DEFECTO))
            try:
                total = cliente.count(NOMBRE_COLECCION, exact=True).count
            finally:
                cliente.close()
            revisar("índice vectorial del RAG", total > 5000, f"{total} fragmentos")
        except Exception as error:  # noqa: BLE001
            revisar("índice vectorial del RAG", False, str(error)[:80])

    estado = Path("data/wiki/demo/estado.json")
    if estado.exists():
        ingeridos = json.loads(estado.read_text("utf-8"))["ingeridos"]
        revisar(
            "wiki de la demostración",
            ingeridos == orden[:5],
            f"{len(ingeridos)} papers (debe ser 5)",
        )
        etiquetas = subprocess.run(
            ["git", "-C", "data/wiki/demo", "tag", "--list", "paso-*"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.split()
        revisar("copias versionadas del wiki", len(etiquetas) == 5, " ".join(sorted(etiquetas)))
    else:
        revisar(
            "wiki de la demostración",
            False,
            "falta data/wiki/demo: ejecuta scripts/preparar_demo.ps1",
        )

    revisar("resultados del piloto", Path("results/piloto-1/respuestas.jsonl").exists())

    cambios = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, check=False
    ).stdout.splitlines()
    revisar("repositorio sin cambios pendientes", not cambios, f"{len(cambios)} cambios")

    for nombre, correcto, detalle in REVISIONES:
        print(f"[{'OK' if correcto else 'FALLA'}] {nombre}" + (f" - {detalle}" if detalle else ""))
    fallas = sum(1 for _, correcto, _ in REVISIONES if not correcto)
    print(f"\n{len(REVISIONES) - fallas} de {len(REVISIONES)} revisiones en orden.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
