"""Tests de integración del repositorio de políticas SQLAlchemy (Fase 2).

Postgres efímero (testcontainers, SAD §8.2), schema limpio por test. Verifica:
  - round-trip exacto dominio → JSONB → dominio (incluido el AST de predicados);
  - inmutabilidad: no se puede regrabar una versión existente (CF-04);
  - "cambio un umbral → nueva versión, la vieja queda intacta" (entregable Fase 2).
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from sqlalchemy.orm import Session, sessionmaker

from domain.errores import PoliticaInvalida
from infrastructure.persistence.repositorio_politicas_sql import RepositorioPoliticasSQLAlchemy
from infrastructure.seed.politica_consumo import politica_consumo_v1

pytestmark = pytest.mark.integration

_MOMENTO = "2026-06-26T12:00:00+00:00"


@pytest.fixture
def repo(session_factory: sessionmaker[Session]) -> RepositorioPoliticasSQLAlchemy:
    return RepositorioPoliticasSQLAlchemy(session_factory)


def test_round_trip_exacto(repo: RepositorioPoliticasSQLAlchemy) -> None:
    original = politica_consumo_v1()
    repo.guardar_version(original)
    repo.activar("consumo", "consumo", 1)

    assert repo.obtener("consumo", 1) == original  # igualdad profunda, incl. predicados
    assert repo.vigente_para("consumo", _MOMENTO) == original


def test_version_es_inmutable(repo: RepositorioPoliticasSQLAlchemy) -> None:
    repo.guardar_version(politica_consumo_v1())
    with pytest.raises(PoliticaInvalida):
        repo.guardar_version(politica_consumo_v1())  # regrabar → prohibido (CF-04)


def test_nueva_version_no_altera_la_vieja(repo: RepositorioPoliticasSQLAlchemy) -> None:
    v1_original = politica_consumo_v1()
    repo.guardar_version(v1_original)
    repo.activar("consumo", "consumo", 1)

    # Nueva versión con un "cambio de umbral".
    nueva_config = replace(v1_original.config_scoring, score_maximo=120)
    v2 = replace(v1_original, version=2, config_scoring=nueva_config)
    repo.guardar_version(v2)
    repo.activar("consumo", "consumo", 2)

    assert repo.obtener("consumo", 1) == v1_original  # la vieja, intacta
    assert repo.vigente_para("consumo", _MOMENTO).version == 2  # la nueva, vigente
    assert repo.obtener("consumo", 2).config_scoring.score_maximo == 120
