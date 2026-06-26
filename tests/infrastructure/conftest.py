"""Fixtures compartidas de integración: un único Postgres efímero por sesión.

Levantar el contenedor una sola vez (no por archivo) acelera la suite de
integración. Marca implícita: estos tests requieren Docker.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import infrastructure.persistence.modelos  # noqa: F401  (registra todas las tablas)
from infrastructure.persistence.db import Base, crear_session_factory

PostgresContainer = pytest.importorskip("testcontainers.postgres").PostgresContainer


@pytest.fixture(scope="session")
def session_factory() -> Iterator[sessionmaker[Session]]:
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as postgres:
        engine = create_engine(postgres.get_connection_url())
        Base.metadata.create_all(engine)
        yield crear_session_factory(engine)
