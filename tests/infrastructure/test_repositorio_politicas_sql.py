"""Tests de integración del repositorio de políticas SQLAlchemy (Fase 2).

Levanta un Postgres efímero con testcontainers (SAD §8.2) y verifica:
  - round-trip exacto dominio → JSONB → dominio (incluido el AST de predicados);
  - inmutabilidad: no se puede regrabar una versión existente (CF-04);
  - "cambio un umbral → nueva versión, la vieja queda intacta" (entregable Fase 2).

Marcado `integration`: requiere Docker.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace

import pytest
from sqlalchemy import create_engine

import infrastructure.persistence.modelos  # noqa: F401  (registra tablas)
from domain.errores import PoliticaInvalida
from infrastructure.persistence.db import Base, crear_session_factory
from infrastructure.persistence.repositorio_politicas_sql import RepositorioPoliticasSQLAlchemy
from infrastructure.seed.politica_consumo import politica_consumo_v1

PostgresContainer = pytest.importorskip("testcontainers.postgres").PostgresContainer

pytestmark = pytest.mark.integration

_MOMENTO = "2026-06-26T12:00:00+00:00"


@pytest.fixture(scope="module")
def repo() -> Iterator[RepositorioPoliticasSQLAlchemy]:
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as postgres:
        engine = create_engine(postgres.get_connection_url())
        Base.metadata.create_all(engine)
        yield RepositorioPoliticasSQLAlchemy(crear_session_factory(engine))


def test_round_trip_exacto(repo: RepositorioPoliticasSQLAlchemy) -> None:
    original = politica_consumo_v1()
    repo.guardar_version(original)
    repo.activar("consumo", "consumo", 1)

    recuperada = repo.obtener("consumo", 1)
    assert recuperada == original  # igualdad profunda, incluidos los predicados AST

    vigente = repo.vigente_para("consumo", _MOMENTO)
    assert vigente == original


def test_version_es_inmutable(repo: RepositorioPoliticasSQLAlchemy) -> None:
    # Ya se guardó v1 en el test anterior (mismo módulo/fixture). Regrabar → error.
    with pytest.raises(PoliticaInvalida):
        repo.guardar_version(politica_consumo_v1())


def test_nueva_version_no_altera_la_vieja(repo: RepositorioPoliticasSQLAlchemy) -> None:
    v1_original = politica_consumo_v1()
    # Nueva versión con bandas distintas (un "cambio de umbral").
    nueva_config = replace(v1_original.config_scoring, score_maximo=120)
    v2 = replace(v1_original, version=2, config_scoring=nueva_config)

    repo.guardar_version(v2)
    repo.activar("consumo", "consumo", 2)

    # La versión vieja sigue intacta y recuperable.
    assert repo.obtener("consumo", 1) == v1_original
    # La vigente ahora es la v2.
    assert repo.vigente_para("consumo", _MOMENTO).version == 2
    assert repo.obtener("consumo", 2).config_scoring.score_maximo == 120
