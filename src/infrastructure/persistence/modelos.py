"""Modelos ORM (SQLAlchemy). La traducción entidad↔fila vive en el mapper, no aquí.

`Politica` es la unidad atómica versionada e inmutable (ADR-003): la PK es
(politica_id, version). Sus reglas y configuración de scoring se guardan como
JSONB —el predicado AST se serializa con `a_dict()`/`predicado_desde_dict()`—,
fiel a "reglas como datos" (ADR-002).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.persistence.db import Base


class PoliticaORM(Base):
    __tablename__ = "politicas"

    politica_id: Mapped[str] = mapped_column(String, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    producto: Mapped[str] = mapped_column(String, index=True)
    # JSONB: estructuras serializadas. Tipadas como Any (frontera JSON).
    reglas: Mapped[Any] = mapped_column(JSONB)
    config_scoring: Mapped[Any] = mapped_column(JSONB)
    efectiva_desde: Mapped[str] = mapped_column(String)
    efectiva_hasta: Mapped[str | None] = mapped_column(String, nullable=True)
    vigente: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
