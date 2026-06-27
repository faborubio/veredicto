"""Tests de SimularCambioRegla (Fase 3): what-if sobre decisiones históricas.

Sin efectos (SI-04): la simulación no persiste ni altera nada.
"""

from __future__ import annotations

from dataclasses import replace

from application.casos_uso.simular_cambio_regla import SimularCambioRegla
from domain.entities.insumos import Insumos
from domain.entities.perfil_crediticio import PerfilCrediticio
from domain.entities.politica import Banda, ResultadoDecision
from domain.entities.reporte_impacto import CriterioSimulacion
from domain.entities.solicitud import SituacionLaboral, Solicitante, Solicitud
from domain.services.motor_evaluacion import MotorEvaluacion
from domain.services.motor_simulacion import MotorSimulacion
from domain.value_objects.disponibilidad import Disponibilidad
from domain.value_objects.monto import Monto
from domain.value_objects.plazo import Plazo
from domain.value_objects.rut import Rut, calcular_dv
from infrastructure.persistence.memoria import RepositorioDecisionesMemoria
from infrastructure.seed.politica_consumo import politica_consumo_v1

_POLITICA = politica_consumo_v1()
_MOTOR = MotorEvaluacion()


def _insumos(key: str) -> Insumos:
    rut = Rut(11_111_111, calcular_dv(11_111_111))
    solicitante = Solicitante(rut, Monto(1_000_000), SituacionLaboral.DEPENDIENTE)
    solicitud = Solicitud(key, solicitante, "consumo", Monto(2_000_000), Plazo(24))
    perfil = PerfilCrediticio(
        disponibilidad=Disponibilidad.DISPONIBLE,
        deuda_total=Monto(300_000),
        tiene_morosidad_vigente=False,
        tiene_deudas_castigadas=False,
        meses_historial=36,
    )
    return Insumos(solicitud, perfil, "2026-06-26T00:00:00+00:00")


def _decisiones_con_n_aprobados(n: int) -> RepositorioDecisionesMemoria:
    repo = RepositorioDecisionesMemoria()
    for i in range(n):
        insumos = _insumos(f"k-{i}")
        repo.guardar(f"k-{i}", _MOTOR.evaluar(insumos, _POLITICA), insumos)
    return repo


def test_simular_politica_mas_estricta_reporta_flips() -> None:
    decisiones = _decisiones_con_n_aprobados(3)  # 3 casos limpios → APROBADO original
    caso_uso = SimularCambioRegla(MotorSimulacion(_MOTOR), decisiones)

    estricta = replace(
        _POLITICA,
        version=2,
        config_scoring=replace(
            _POLITICA.config_scoring,
            bandas=(
                Banda(90, ResultadoDecision.APROBADO),
                Banda(40, ResultadoDecision.REVISION_MANUAL),
                Banda(0, ResultadoDecision.RECHAZADO),
            ),
        ),
    )
    reporte = caso_uso.ejecutar(estricta)

    assert reporte.total_evaluados == 3
    assert reporte.sin_cambio == 0
    assert len(reporte.flips) == 1
    assert reporte.flips[0].desde is ResultadoDecision.APROBADO
    assert reporte.flips[0].hacia is ResultadoDecision.REVISION_MANUAL
    assert reporte.flips[0].cantidad == 3


def test_simular_no_persiste_nada_si04() -> None:
    decisiones = _decisiones_con_n_aprobados(2)
    antes = len(decisiones.snapshots_de_poblacion(None))
    SimularCambioRegla(MotorSimulacion(_MOTOR), decisiones).ejecutar(_POLITICA)
    assert len(decisiones.snapshots_de_poblacion(None)) == antes  # sin efectos


def test_criterio_limita_la_poblacion() -> None:
    decisiones = _decisiones_con_n_aprobados(5)
    caso_uso = SimularCambioRegla(MotorSimulacion(_MOTOR), decisiones)
    reporte = caso_uso.ejecutar(_POLITICA, CriterioSimulacion(limite=2))
    assert reporte.total_evaluados == 2
