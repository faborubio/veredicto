"""Test e2e del composition root SQL (ModuloSQL) contra Postgres.

Verifica que el wiring de producción funciona punta a punta: el seed deja la
política vigente, se evalúa una solicitud y la idempotencia opera A TRAVÉS de
Postgres. Cierra el hueco detectado en la Vista de halcón de Fase 2.
"""

from __future__ import annotations

import pytest
from injector import Injector
from sqlalchemy.orm import Session, sessionmaker

from application.casos_uso.evaluar_solicitud import EvaluarSolicitud
from application.casos_uso.gestionar_reglas import GestionarReglas
from domain.entities.politica import ResultadoDecision
from domain.entities.solicitud import SituacionLaboral, Solicitante, Solicitud
from domain.value_objects.monto import Monto
from domain.value_objects.plazo import Plazo
from domain.value_objects.rut import Rut, calcular_dv
from infrastructure.di import ModuloAplicacion, ModuloSQL

pytestmark = pytest.mark.integration

_MOMENTO = "2026-06-26T00:00:00+00:00"


def _solicitud(key: str) -> Solicitud:
    rut = Rut(11_111_111, calcular_dv(11_111_111))
    solicitante = Solicitante(rut, Monto(1_000_000), SituacionLaboral.DEPENDIENTE)
    return Solicitud(key, solicitante, "consumo", Monto(2_000_000), Plazo(24))


def test_wiring_sql_end_to_end(session_factory: sessionmaker[Session]) -> None:
    inyector = Injector([ModuloAplicacion(), ModuloSQL(session_factory=session_factory)])

    # El seed (idempotente) deja consumo v1 vigente sobre Postgres.
    gestor = inyector.get(GestionarReglas)
    assert gestor.vigente("consumo", _MOMENTO).version == 1

    evaluar = inyector.get(EvaluarSolicitud)
    decision = evaluar.ejecutar(_solicitud("sql-e2e"), _MOMENTO)
    assert decision.resultado is ResultadoDecision.APROBADO

    # Idempotencia a través de Postgres: misma clave → misma decisión persistida.
    repetida = evaluar.ejecutar(_solicitud("sql-e2e"), _MOMENTO)
    assert repetida == decision
