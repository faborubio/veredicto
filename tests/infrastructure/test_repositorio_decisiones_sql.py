"""Tests de integración del repositorio de decisiones SQLAlchemy (Fase 2).

Verifica (contra Postgres efímero):
  - round-trip exacto de `DecisionMotor` (incluido el rastro);
  - reconstrucción fiel del SNAPSHOT de insumos (ADR-004) → habilita simulación;
  - idempotencia: regrabar la misma clave no duplica (ADR-010).
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session, sessionmaker

from domain.entities.insumos import Insumos
from domain.entities.perfil_crediticio import PerfilCrediticio
from domain.entities.solicitud import SituacionLaboral, Solicitante, Solicitud
from domain.services.motor_evaluacion import MotorEvaluacion
from domain.value_objects.disponibilidad import Disponibilidad
from domain.value_objects.monto import Monto
from domain.value_objects.plazo import Plazo
from domain.value_objects.rut import Rut, calcular_dv
from infrastructure.persistence.repositorio_decisiones_sql import RepositorioDecisionesSQLAlchemy
from infrastructure.seed.politica_consumo import politica_consumo_v1

pytestmark = pytest.mark.integration

_MOMENTO = "2026-06-26T12:00:00+00:00"
_POLITICA = politica_consumo_v1()
_MOTOR = MotorEvaluacion()


@pytest.fixture
def repo(session_factory: sessionmaker[Session]) -> RepositorioDecisionesSQLAlchemy:
    return RepositorioDecisionesSQLAlchemy(session_factory)


def _insumos(key: str, rut_numero: int = 11_111_111) -> Insumos:
    solicitante = Solicitante(
        Rut(rut_numero, calcular_dv(rut_numero)), Monto(1_000_000), SituacionLaboral.DEPENDIENTE
    )
    solicitud = Solicitud(key, solicitante, "consumo", Monto(2_000_000), Plazo(24))
    perfil = PerfilCrediticio(
        disponibilidad=Disponibilidad.DISPONIBLE,
        deuda_total=Monto(300_000),
        tiene_morosidad_vigente=False,
        tiene_deudas_castigadas=False,
        meses_historial=36,
    )
    return Insumos(solicitud, perfil, _MOMENTO)


def test_round_trip_decision_y_rastro(repo: RepositorioDecisionesSQLAlchemy) -> None:
    insumos = _insumos("dec-1")
    decision = _MOTOR.evaluar(insumos, _POLITICA)

    repo.guardar("dec-1", decision, insumos)
    recuperada = repo.por_idempotency_key("dec-1")

    assert recuperada == decision  # igualdad profunda, incluido el rastro completo

    # casos_para_simulacion devuelve (snapshot, resultado original) — base del what-if.
    casos = repo.casos_para_simulacion(None)
    assert len(casos) == 1
    assert casos[0].resultado_original is decision.resultado
    assert casos[0].snapshot == insumos


def test_snapshot_se_reconstruye_fiel(repo: RepositorioDecisionesSQLAlchemy) -> None:
    insumos = _insumos("dec-2")
    repo.guardar("dec-2", _MOTOR.evaluar(insumos, _POLITICA), insumos)

    snapshots = repo.snapshots_de_poblacion(None)
    assert insumos in snapshots  # el snapshot vuelve idéntico (ADR-004)


def test_idempotencia_no_duplica(repo: RepositorioDecisionesSQLAlchemy) -> None:
    insumos = _insumos("dec-dup")
    decision = _MOTOR.evaluar(insumos, _POLITICA)
    repo.guardar("dec-dup", decision, insumos)
    repo.guardar("dec-dup", decision, insumos)  # segunda vez: no debe duplicar

    assert repo.por_idempotency_key("dec-dup") == decision
