"""Fixtures de integración: un Postgres efímero por sesión, schema LIMPIO por test.

El contenedor se levanta una sola vez (caro); pero cada test recibe un esquema
recién recreado (drop+create) para quedar AISLADO —sin estado acumulado entre
tests, que es frágil y oculta bugs—. Requiere Docker.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

import infrastructure.persistence.modelos  # noqa: F401  (registra todas las tablas)
from infrastructure.persistence.db import Base, crear_session_factory

PostgresContainer = pytest.importorskip("testcontainers.postgres").PostgresContainer


@pytest.fixture(scope="session")
def _engine() -> Iterator[Engine]:
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as postgres:
        yield create_engine(postgres.get_connection_url())


@pytest.fixture
def session_factory(_engine: Engine) -> sessionmaker[Session]:
    Base.metadata.drop_all(_engine)
    Base.metadata.create_all(_engine)
    return crear_session_factory(_engine)
