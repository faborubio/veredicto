"""Tests de humo de Fase 0.

No prueban lógica de negocio (no existe aún): prueban que el esqueleto está bien
formado, que los value objects defienden sus invariantes básicos y —el más
importante para el proyecto— que la FRONTERA DURA del dominio se respeta: ningún
módulo de `domain/` importa frameworks/adaptadores (CLAUDE.md invariante 2).
"""

from __future__ import annotations

import importlib
import pkgutil

import pytest

import domain
from domain.errores import ErrorValidacion
from domain.value_objects.dti import Dti
from domain.value_objects.monto import Monto
from domain.value_objects.plazo import Plazo

PROHIBIDOS = (
    "sqlalchemy",
    "fastapi",
    "fastmcp",
    "mcp",
    "injector",
    "psycopg",
    "application",
    "infrastructure",
    "interfaces",
)


def _modulos_de_dominio() -> list[str]:
    return [m.name for m in pkgutil.walk_packages(domain.__path__, prefix="domain.")]


@pytest.mark.parametrize("nombre_modulo", _modulos_de_dominio())
def test_dominio_importa_sin_dependencias_externas(nombre_modulo: str) -> None:
    """Cada módulo de dominio importa usando sólo stdlib + domain (frontera dura)."""
    modulo = importlib.import_module(nombre_modulo)
    importados = {getattr(valor, "__module__", "").split(".")[0] for valor in vars(modulo).values()}
    for prohibido in PROHIBIDOS:
        assert prohibido not in importados, (
            f"{nombre_modulo} referencia '{prohibido}': viola la frontera del dominio."
        )


def test_monto_rechaza_negativo_y_float() -> None:
    assert Monto(0).pesos == 0
    with pytest.raises(ErrorValidacion):
        Monto(-1)
    with pytest.raises(ErrorValidacion):
        Monto(1.5)  # type: ignore[arg-type]


def test_dti_en_puntos_basicos_enteros() -> None:
    assert Dti(4500).puntos_basicos == 4500
    with pytest.raises(ErrorValidacion):
        Dti(-1)


def test_plazo_debe_ser_positivo() -> None:
    assert Plazo(12).meses == 12
    with pytest.raises(ErrorValidacion):
        Plazo(0)


def test_value_objects_son_inmutables() -> None:
    monto = Monto(1000)
    with pytest.raises(AttributeError):
        monto.pesos = 2000  # type: ignore[misc]
