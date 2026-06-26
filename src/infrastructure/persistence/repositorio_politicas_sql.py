"""RepositorioPoliticasSQLAlchemy: implementa el puerto sobre Postgres.

Versionado inmutable (ADR-003): `guardar_version` inserta una versión nueva y
NUNCA muta una existente (CASES.md CF-04). La activación (qué versión está vigente
por producto) es explícita vía `activar`, garantizando una sola vigente por
producto (CF-05). En Fase 2 el evento auditado de activación (ADR-008) se añade
junto a `GestionarReglas`.
"""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from domain.entities.politica import Politica
from domain.errores import PoliticaInexistente, PoliticaInvalida
from infrastructure.persistence.mapeo_politica import politica_a_orm, politica_desde_orm
from infrastructure.persistence.modelos import PoliticaORM


class RepositorioPoliticasSQLAlchemy:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    def obtener(self, politica_id: str, version: int) -> Politica:
        with self._sf() as s:
            orm = s.get(PoliticaORM, (politica_id, version))
            if orm is None:
                raise PoliticaInexistente(f"Política {politica_id} v{version} no existe.")
            return politica_desde_orm(orm)

    def vigente_para(self, producto: str, momento: str) -> Politica:
        with self._sf() as s:
            orm = s.scalars(
                select(PoliticaORM).where(
                    PoliticaORM.producto == producto, PoliticaORM.vigente.is_(True)
                )
            ).first()
            if orm is None:
                raise PoliticaInexistente(f"No hay política vigente para '{producto}'.")
            return politica_desde_orm(orm)

    def guardar_version(self, politica: Politica) -> None:
        with self._sf() as s:
            existente = s.get(PoliticaORM, (politica.id, politica.version))
            if existente is not None:
                raise PoliticaInvalida(
                    f"La política {politica.id} v{politica.version} ya existe; "
                    "es inmutable (CF-04)."
                )
            s.add(politica_a_orm(politica))
            s.commit()

    def activar(self, producto: str, politica_id: str, version: int) -> None:
        """Marca (politica_id, version) como la única vigente del producto (CF-05)."""
        with self._sf() as s:
            if s.get(PoliticaORM, (politica_id, version)) is None:
                raise PoliticaInexistente(f"Política {politica_id} v{version} no existe.")
            s.execute(
                update(PoliticaORM).where(PoliticaORM.producto == producto).values(vigente=False)
            )
            s.execute(
                update(PoliticaORM)
                .where(PoliticaORM.politica_id == politica_id, PoliticaORM.version == version)
                .values(vigente=True)
            )
            s.commit()
