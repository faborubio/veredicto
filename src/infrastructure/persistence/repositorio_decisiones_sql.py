"""RepositorioDecisionesSQLAlchemy: decisiones + snapshot sobre Postgres.

Idempotencia (ADR-010): la `idempotency_key` es PK; `guardar` no duplica.
Cada decisión persiste el SNAPSHOT íntegro de insumos (ADR-004), base de la
reproducibilidad y de la simulación what-if (Fase 3).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from domain.entities.decision_motor import DecisionMotor
from domain.entities.insumos import Insumos
from infrastructure.persistence.mapeo_decision import (
    decision_a_orm,
    decision_desde_orm,
    snapshot_desde_orm,
)
from infrastructure.persistence.modelos import DecisionORM


class RepositorioDecisionesSQLAlchemy:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    def por_idempotency_key(self, key: str) -> DecisionMotor | None:
        with self._sf() as s:
            orm = s.get(DecisionORM, key)
            return decision_desde_orm(orm) if orm is not None else None

    def por_solicitud(self, solicitud_id: str) -> DecisionMotor | None:
        # En Fase 2 la idempotency_key actúa como id de solicitud.
        return self.por_idempotency_key(solicitud_id)

    def guardar(self, idempotency_key: str, decision: DecisionMotor, snapshot: Insumos) -> None:
        with self._sf() as s:
            if s.get(DecisionORM, idempotency_key) is not None:
                return  # idempotente: ya existe, no duplicar (ADR-010)
            s.add(decision_a_orm(idempotency_key, decision, snapshot))
            s.commit()

    def snapshots_de_poblacion(self, criterio: object) -> list[Insumos]:
        # Población completa en Fase 2; el filtrado real (rango/producto) llega en
        # Fase 3 junto con la simulación.
        with self._sf() as s:
            return [snapshot_desde_orm(o) for o in s.scalars(select(DecisionORM)).all()]
