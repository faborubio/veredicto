"""Tests del caso de uso EvaluarSolicitud (Fase 1).

Verifica el flujo de §6.1 con adaptadores en memoria + buró simulado: decisión +
rastro, persistencia del snapshot, e idempotencia (ADR-010).
"""

from __future__ import annotations

from application.casos_uso.evaluar_solicitud import EvaluarSolicitud
from domain.entities.politica import ResultadoDecision
from domain.entities.solicitud import SituacionLaboral, Solicitante, Solicitud
from domain.services.motor_evaluacion import MotorEvaluacion
from domain.value_objects.monto import Monto
from domain.value_objects.plazo import Plazo
from domain.value_objects.rut import Rut
from infrastructure.buro.buro_simulado import ESCENARIOS_DEMO, BuroSimulado
from infrastructure.persistence.memoria import (
    RepositorioDecisionesMemoria,
    RepositorioPoliticasMemoria,
)
from infrastructure.seed.politica_consumo import politica_consumo_v1

_MOMENTO = "2026-06-26T12:00:00+00:00"


def _caso_de_uso() -> tuple[EvaluarSolicitud, RepositorioDecisionesMemoria]:
    politicas = RepositorioPoliticasMemoria()
    politicas.guardar_version(politica_consumo_v1())
    decisiones = RepositorioDecisionesMemoria()
    caso = EvaluarSolicitud(
        motor=MotorEvaluacion(),
        politicas=politicas,
        decisiones=decisiones,
        buro=BuroSimulado(ESCENARIOS_DEMO),
    )
    return caso, decisiones


def _solicitud(rut_numero: int = 11_111_111, key: str = "k-1") -> Solicitud:
    solicitante = Solicitante(Rut(rut_numero, "1"), Monto(1_000_000), SituacionLaboral.DEPENDIENTE)
    return Solicitud(key, solicitante, "consumo", Monto(2_000_000), Plazo(24))


def test_flujo_completo_aprueba_perfil_limpio() -> None:
    caso, decisiones = _caso_de_uso()
    decision = caso.ejecutar(_solicitud(rut_numero=11_111_111), _MOMENTO)

    assert decision.resultado is ResultadoDecision.APROBADO
    assert decision.politica_id == "consumo"
    assert decision.politica_version == 1
    # El snapshot quedó persistido para reproducibilidad/simulación (ADR-004).
    assert decisiones.por_idempotency_key("k-1") is not None


def test_buro_con_morosidad_rechaza() -> None:
    caso, _ = _caso_de_uso()
    decision = caso.ejecutar(_solicitud(rut_numero=22_222_222), _MOMENTO)
    assert decision.resultado is ResultadoDecision.RECHAZADO


def test_buro_caido_deriva_a_revision() -> None:
    caso, _ = _caso_de_uso()
    decision = caso.ejecutar(_solicitud(rut_numero=55_555_555), _MOMENTO)
    assert decision.resultado is ResultadoDecision.REVISION_MANUAL


def test_idempotencia_no_recomputa() -> None:
    caso, decisiones = _caso_de_uso()
    primera = caso.ejecutar(_solicitud(key="dup"), _MOMENTO)
    segunda = caso.ejecutar(_solicitud(key="dup"), _MOMENTO)
    # Misma identidad de objeto: se devolvió la decisión persistida, no una nueva.
    assert primera is segunda
    assert len(decisiones.snapshots_de_poblacion(None)) == 1
