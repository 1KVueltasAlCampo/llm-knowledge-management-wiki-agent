import pytest

from wikillm.common import config

VARIABLES = [
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "DEEPSEEK_THINKING",
    "DEEPSEEK_REASONING_EFFORT",
    "MODEL_TEMPERATURE",
    "MODEL_MAX_RETRIES",
    "MODEL_TIMEOUT_SECONDS",
    "PRICE_INPUT_CACHE_MISS_USD_PER_M",
    "PRICE_INPUT_CACHE_HIT_USD_PER_M",
    "PRICE_OUTPUT_USD_PER_M",
    "MAX_USD_PER_RUN",
    "EMBEDDING_MODEL",
    "EMBEDDING_DEVICE",
]


@pytest.fixture
def entorno_limpio(monkeypatch):
    """Sin .env real y sin variables: se prueban los valores por defecto del código."""
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    for variable in VARIABLES:
        monkeypatch.delenv(variable, raising=False)


def test_valores_por_defecto(entorno_limpio):
    ajustes = config.load_settings()
    assert ajustes.model == "deepseek-flash"
    assert ajustes.thinking == "disabled"
    assert ajustes.temperature == 0
    assert ajustes.max_retries == 3
    assert ajustes.timeout_seconds == 120
    assert ajustes.embedding_model == "BAAI/bge-small-en-v1.5"
    assert ajustes.embedding_device == "cuda"


def test_las_variables_de_entorno_sobrescriben_los_valores(entorno_limpio, monkeypatch):
    monkeypatch.setenv("MODEL_MAX_RETRIES", "5")
    monkeypatch.setenv("EMBEDDING_DEVICE", "cpu")
    ajustes = config.load_settings()
    assert ajustes.max_retries == 5
    assert ajustes.embedding_device == "cpu"


def test_variables_vacias_usan_el_valor_por_defecto(entorno_limpio, monkeypatch):
    monkeypatch.setenv("EMBEDDING_MODEL", "")
    monkeypatch.setenv("EMBEDDING_DEVICE", "")
    ajustes = config.load_settings()
    assert ajustes.embedding_model == "BAAI/bge-small-en-v1.5"
    assert ajustes.embedding_device == "cuda"
