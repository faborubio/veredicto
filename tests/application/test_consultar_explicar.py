"""Tests de ConsultarDecision y ExplicarDecision (Fase 4, lectura)."""

from __future__ import annotations

import pytest

from application.casos_uso.consultar_decision import ConsultarDecision
from application.casos_uso.explicar_decision import ExplicarDecision
from domain.entities.insumos import Insumos
from domain.entities.perfil_crediticio import PerfilCrediticio
from domain.entities.politica import ResultadoDecision
from domain.entities.solicitud import SituacionLaboral, Solicitante, Solicitud
from domain.errores import DecisionInexistente
from domain.services.motor_evaluacion import MotorEvaluacion
from domain.value_objects.disponibilidad import Disponibilidad
from domain.value_objects.monto import Monto
from domain.value_objects.plazo import Plazo
from domain.value_objects.rut import Rut, calcular_dv
from infrastructure.persistence.memoria import RepositorioDecisionesMemoria
from infrastructure.seed.politica_consumo import politica_consumo_v1

_MOTOR = MotorEvaluacion()
_POLITICA = politica_consumo_v1()


def _insumos(key: str, morosidad: bool = False) -> Insumos:
    rut = Rut(11_111_111, calcular_dv(11_111_111))
    solicitante = Solicitante(rut, Monto(1_000_000), SituacionLaboral.DEPENDIENTE)
    solicitud = Solicitud(key, solicitante, "consumo", Monto(2_000_000), Plazo(24))
    perfil = PerfilCrediticio(
        disponibilidad=Disponibilidad.DISPONIBLE,
        deuda_total=Monto(300_000),
        tiene_morosidad_vigente=morosidad,
        tiene_deudas_castigadas=False,
        meses_historial=36,
    )
    return Insumos(solicitud, perfil, "2026-06-26T00:00:00+00:00")


def _repo_con_decision(key: str, morosidad: bool = False) -> RepositorioDecisionesMemoria:
    repo = RepositorioDecisionesMemoria()
    insumos = _insumos(key, morosidad)
    repo.guardar(key, _MOTOR.evaluar(insumos, _POLITICA), insumos)
    return repo


def test_consultar_decision_existente() -> None:
    repo = _repo_con_decision("d-1")
    decision = ConsultarDecision(repo).ejecutar("d-1")
    assert decision.resultado is ResultadoDecision.APROBADO


def test_consultar_decision_inexistente_lanza_tipado() -> None:
    repo = RepositorioDecisionesMemoria()
    with pytest.raises(DecisionInexistente):
        ConsultarDecision(repo).ejecutar("no-existe")


def test_explicar_aprobado_lista_aportes() -> None:
    repo = _repo_con_decision("d-2")
    explicacion = ExplicarDecision(repo).ejecutar("d-2")
    assert explicacion.resultado is ResultadoDecision.APROBADO
    assert len(explicacion.motivos) > 0  # reglas que aportaron al score


def test_explicar_rechazado_da_motivo_del_hard_stop() -> None:
    repo = _repo_con_decision("d-3", morosidad=True)  # morosidad → RECHAZADO
    explicacion = ExplicarDecision(repo).ejecutar("d-3")
    assert explicacion.resultado is ResultadoDecision.RECHAZADO
    assert any("morosidad" in m.lower() for m in explicacion.motivos)
