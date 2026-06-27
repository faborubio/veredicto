"""RepositorioActivacionesSQLAlchemy: historial auditado de activaciones (ADR-008)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from domain.entities.activacion import EventoActivacionPolitica
from infrastructure.persistence.modelos import ActivacionORM


def _a_evento(orm: ActivacionORM) -> EventoActivacionPolitica:
    return EventoActivacionPolitica(
        politica_id=orm.politica_id,
        politica_version=orm.politica_version,
        producto=orm.producto,
        actor=orm.actor,
        momento=orm.momento,
    )


class RepositorioActivacionesSQLAlchemy:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    def registrar(self, evento: EventoActivacionPolitica) -> None:
        with self._sf() as s:
            s.add(
                ActivacionORM(
                    politica_id=evento.politica_id,
                    politica_version=evento.politica_version,
                    producto=evento.producto,
                    actor=evento.actor,
                    momento=evento.momento,
                )
            )
            s.commit()

    def historial(self, producto: str) -> list[EventoActivacionPolitica]:
        with self._sf() as s:
            filas = s.scalars(
                select(ActivacionORM)
                .where(ActivacionORM.producto == producto)
                .order_by(ActivacionORM.id)
            ).all()
            return [_a_evento(f) for f in filas]
