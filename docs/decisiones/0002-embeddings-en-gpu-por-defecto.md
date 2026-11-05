# 0002. Embeddings locales, en GPU por defecto

**Fecha:** 4 de noviembre de 2026. **Estado:** vigente; se implementa con el RAG.

## Decisión
Los embeddings se calculan en local, con `BAAI/bge-small-en-v1.5`, y **por defecto en la GPU**
(`EMBEDDING_DEVICE=cuda`). Quien no tenga GPU NVIDIA cambia la variable a `cpu` en su `.env`.
La GPU se usa solo para embeddings, no para modelos de chat.

## Medición (GTX 1650 de 4 GB, i5-10300H, 200 fragmentos de ~500 tokens)

| Dispositivo | Velocidad | ~1.500 fragmentos |
|---|---|---|
| GPU (PyTorch 2.14.1+cu126) | 46,4 fragmentos/s | ~32 s |
| CPU | 6,4 fragmentos/s | ~4 min |

nomic-embed no se pudo medir en GPU por una incompatibilidad de su código remoto con la versión
de `transformers`; no se necesita.

## Por qué
- 4 GB de memoria de vídeo solo permiten modelos de chat de 3–4B, demasiado débiles para el
  agente de la wiki, y además romperían la regla de usar el mismo modelo.
- Para embeddings, la GPU es unas 7 veces más rápida y acelera reindexar al iterar el RAG.
- Ollama no aporta nada que no den las librerías de Python, y exige instalar un servicio.

## Consecuencias
- Instalar PyTorch con CUDA descarga unos 3 GB. Al implementar el RAG se configurará el índice
  de PyTorch en `pyproject.toml` y se documentará el cambio a `cpu`.
- Si `cuda` no está disponible, el código debe avisar con un mensaje claro que indique cambiar
  `EMBEDDING_DEVICE` a `cpu`, en lugar de fallar de forma opaca.
