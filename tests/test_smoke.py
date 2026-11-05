"""Pruebas de humo: no llaman a la API ni gastan saldo."""

from pathlib import Path

import wikillm
from wikillm.common.config import load_settings

RAIZ = Path(__file__).resolve().parent.parent

VARIABLES_OBLIGATORIAS = [
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "MAX_USD_PER_RUN",
]


def test_paquete_importa():
    assert wikillm is not None


def test_configuracion_usa_valores_por_defecto(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
    monkeypatch.delenv("MAX_USD_PER_RUN", raising=False)
    ajustes = load_settings()
    assert ajustes.model == "deepseek-flash"
    assert ajustes.max_usd_per_run > 0


def test_la_clave_no_aparece_al_imprimir_la_configuracion(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-clave-de-prueba")
    assert "sk-clave-de-prueba" not in repr(load_settings())


def test_env_example_lista_las_variables_obligatorias():
    contenido = (RAIZ / ".env.example").read_text(encoding="utf-8")
    for variable in VARIABLES_OBLIGATORIAS:
        assert f"{variable}=" in contenido


def test_env_esta_ignorado_por_git():
    lineas = (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in lineas
