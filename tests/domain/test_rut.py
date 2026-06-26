"""Tests del RUT (EV-01): validación de dígito verificador módulo 11."""

from __future__ import annotations

import pytest

from domain.errores import ErrorValidacion
from domain.value_objects.rut import Rut, calcular_dv


@pytest.mark.parametrize(
    ("numero", "dv"),
    [(11_111_111, "1"), (12_345_678, "5"), (22_222_222, "2"), (55_555_555, "5")],
)
def test_rut_valido_se_construye(numero: int, dv: str) -> None:
    assert Rut(numero, dv).digito_verificador == dv


def test_dv_incorrecto_es_rechazado() -> None:
    with pytest.raises(ErrorValidacion):
        Rut(12_345_678, "9")  # el correcto es 5


def test_numero_no_positivo_es_rechazado() -> None:
    with pytest.raises(ErrorValidacion):
        Rut(0, "0")


def test_desde_texto_con_y_sin_puntos() -> None:
    assert Rut.desde_texto("12.345.678-5") == Rut(12_345_678, "5")
    assert Rut.desde_texto("123456785") == Rut(12_345_678, "5")


def test_desde_texto_invalido() -> None:
    with pytest.raises(ErrorValidacion):
        Rut.desde_texto("12.345.678-9")
    with pytest.raises(ErrorValidacion):
        Rut.desde_texto("abc")


def test_dv_k() -> None:
    # Buscar un número cuyo DV sea K (resto 10) y verificar normalización.
    numero = next(n for n in range(1, 1000) if calcular_dv(n) == "K")
    assert Rut(numero, "k").digito_verificador == "K"  # normaliza a mayúscula


def test_enmascarado_no_expone_rut_completo() -> None:
    rut = Rut(12_345_678, "5")
    assert rut.enmascarado == "***678-5"
    assert "12345678" not in rut.enmascarado
