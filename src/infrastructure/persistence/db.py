"""Setup de SQLAlchemy 2.0: Base declarativa, engine y session factory.

Vive en infraestructura (frontera dura): el dominio no conoce SQLAlchemy. La URL
de conexión entra por entorno (`DATABASE_URL`); en local apunta al Postgres del
docker-compose.
"""

from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

_URL_DEFAULT = "postgresql+psycopg://veredicto:veredicto@localhost:5432/veredicto"


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos ORM."""


def url_de_entorno() -> str:
    return os.environ.get("DATABASE_URL", _URL_DEFAULT)


def crear_engine(url: str | None = None) -> Engine:
    return create_engine(url or url_de_entorno(), future=True)


def crear_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)
