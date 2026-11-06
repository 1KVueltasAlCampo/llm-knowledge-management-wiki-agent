# Instrucciones para Claude Code

Proyecto de maestría: comparación experimental RAG frente a WikiLLM sobre un corpus de arXiv.

- Reglas que no se negocian: @CONSTITUTION.md
- Cómo trabajar en el repo (mapa, contratos, comandos, modelos y gasto): @AGENTS.md

Este archivo es corto a propósito: lo común a todos los agentes vive en `AGENTS.md`, y aquí
solo va lo propio de Claude Code.

## Propio de Claude Code

- Los comandos `/opsx:*` y las skills de `.claude/skills/openspec-*` los genera OpenSpec: no
  se editan a mano, se regeneran con la herramienta.
- Antes de dar algo por terminado, ejecutar
  `uv run ruff check . && uv run ruff format --check . && uv run pytest` y mostrar el resultado.
- No hacer commits, push ni merge sin que se pida.
- No ejecutar llamadas que gasten saldo de la API sin avisar antes y mostrar la estimación.
