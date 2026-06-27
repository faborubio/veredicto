"""Test de integración del repositorio de activaciones SQLAlchemy (ADR-008)."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session, sessionmaker

from domain.entities.activacion import EventoActivacionPolitica
from infrastructure.persistence.repositorio_activaciones_sql import (
    RepositorioActivacionesSQLAlchemy,
)

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(session_factory: sessionmaker[Session]) -> RepositorioActivacionesSQLAlchemy:
    return RepositorioActivacionesSQLAlchemy(session_factory)


def test_registrar_y_recuperar_historial_ordenado(
    repo: RepositorioActivacionesSQLAlchemy,
) -> None:
    repo.registrar(EventoActivacionPolitica("consumo", 1, "consumo", "ana", "2026-06-26T01:00:00Z"))
    repo.registrar(EventoActivacionPolitica("consumo", 2, "consumo", "ana", "2026-06-26T02:00:00Z"))

    historial = repo.historial("consumo")
    assert [e.politica_version for e in historial] == [1, 2]
    assert all(e.actor == "ana" for e in historial)
