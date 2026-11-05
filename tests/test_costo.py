from datetime import UTC, datetime

import pytest

from wikillm.common.costo import Tarifas, calcular_costo, es_hora_pico

TARIFAS = Tarifas(entrada_sin_cache=0.15, entrada_con_cache=0.003, salida=0.60)


def test_costo_de_entrada_sin_cache_y_salida():
    # 1.000 tokens de entrada y 500 de salida: 0,00015 + 0,00030 dólares
    assert calcular_costo(1000, 0, 500, TARIFAS) == pytest.approx(0.00045)


def test_costo_de_entrada_con_cache():
    assert calcular_costo(0, 1_000_000, 0, TARIFAS) == pytest.approx(0.003)


def test_costo_en_hora_pico_es_el_doble():
    normal = calcular_costo(1000, 0, 500, TARIFAS)
    assert calcular_costo(1000, 0, 500, TARIFAS, hora_pico=True) == pytest.approx(2 * normal)


@pytest.mark.parametrize(
    ("momento", "esperado"),
    [
        (datetime(2026, 11, 9, 2, 0, tzinfo=UTC), True),  # lunes 02:00 UTC
        (datetime(2026, 11, 9, 5, 0, tzinfo=UTC), False),  # lunes 05:00 UTC
        (datetime(2026, 11, 9, 6, 30, tzinfo=UTC), True),  # lunes 06:30 UTC
        (datetime(2026, 11, 9, 10, 0, tzinfo=UTC), False),  # el límite final no cuenta
        (datetime(2026, 11, 9, 1, 0, tzinfo=UTC), True),  # el límite inicial sí cuenta
        (datetime(2026, 11, 8, 2, 0, tzinfo=UTC), False),  # domingo
        (datetime(2026, 11, 14, 7, 0, tzinfo=UTC), False),  # sábado
    ],
)
def test_hora_pico_por_dia_y_hora(momento, esperado):
    assert es_hora_pico(momento) is esperado


def test_fecha_sin_zona_horaria_se_toma_como_utc():
    assert es_hora_pico(datetime(2026, 11, 9, 2, 0)) is True
