"""Tests del MotorEvaluacion sobre la política de consumo v1 (Fase 1).

Cubre el invariante estrella (determinismo, property-based) y los casos borde de
`CASES.md`: hard-stops (EV-06), ingreso 0 (EV-03), buró ausente (EV-04 a nivel de
disponibilidad), thin file (EV-02) y empate en banda (EV-07).
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from domain.entities.insumos import CAMPOS_INSUMO, Insumos
from domain.entities.perfil_crediticio import PerfilCrediticio
from domain.entities.politica import ResultadoDecision
from domain.entities.solicitud import SituacionLaboral, Solicitante, Solicitud
from domain.services.motor_evaluacion import MotorEvaluacion
from domain.value_objects.disponibilidad import Disponibilidad
from domain.value_objects.monto import Monto
from domain.value_objects.plazo import Plazo
from domain.value_objects.rut import Rut
from infrastructure.seed.politica_consumo import politica_consumo_v1

_MOTOR = MotorEvaluacion()
_POLITICA = politica_consumo_v1()


def _insumos(
    *,
    monto: int = 2_000_000,
    plazo: int = 24,
    ingreso: int = 1_000_000,
    situacion: SituacionLaboral = SituacionLaboral.DEPENDIENTE,
    perfil_disp: Disponibilidad = Disponibilidad.DISPONIBLE,
    deuda: int | None = 300_000,
    morosidad: bool | None = False,
    castigadas: bool | None = False,
    meses_historial: int | None = 36,
) -> Insumos:
    solicitante = Solicitante(Rut(12_345_678, "5"), Monto(ingreso), situacion)
    solicitud = Solicitud("idem-1", solicitante, "consumo", Monto(monto), Plazo(plazo))
    perfil = PerfilCrediticio(
        disponibilidad=perfil_disp,
        deuda_total=Monto(deuda) if deuda is not None else None,
        tiene_morosidad_vigente=morosidad,
        tiene_deudas_castigadas=castigadas,
        meses_historial=meses_historial,
    )
    return Insumos(solicitud, perfil, "2026-06-26")


# --- Coherencia de la política con el contrato (CF-03) ---------------------


def test_seed_politica_respeta_el_contrato_de_insumos() -> None:
    for regla in _POLITICA.reglas:
        campos = regla.campos_referenciados()
        assert campos <= CAMPOS_INSUMO, f"{regla.id} referencia campo fuera del contrato"
        # Asunción de fuente única de Fase 1: el predicado lee sólo su fuente_dato.
        assert campos == {regla.fuente_dato}, f"{regla.id} no es de fuente única"


# --- Casos de negocio ------------------------------------------------------


def test_perfil_limpio_dependiente_aprueba() -> None:
    # dependiente +30, dti 3000bps→+25, historial 36→+30 = 85 → APROBADO.
    decision = _MOTOR.evaluar(_insumos(), _POLITICA)
    assert decision.resultado is ResultadoDecision.APROBADO
    assert decision.score == 85


def test_morosidad_vigente_es_hard_stop() -> None:
    decision = _MOTOR.evaluar(_insumos(morosidad=True), _POLITICA)
    assert decision.resultado is ResultadoDecision.RECHAZADO


def test_buro_no_disponible_fuerza_revision() -> None:
    # EV-04 (disponibilidad): sin perfil, R3/R4/R6/R9 fuerzan revisión; los
    # hard-stops sobre la solicitud (monto/plazo/ingreso) pasan.
    decision = _MOTOR.evaluar(
        _insumos(
            perfil_disp=Disponibilidad.NO_DISPONIBLE,
            deuda=None,
            morosidad=None,
            castigadas=None,
            meses_historial=None,
        ),
        _POLITICA,
    )
    assert decision.resultado is ResultadoDecision.REVISION_MANUAL


def test_ingreso_cero_rechaza_sin_division_por_cero() -> None:
    # EV-03: ingreso 0 → R5 (ingreso mínimo) falla como hard-stop → RECHAZADO,
    # y el DTI queda NO_DISPONIBLE sin lanzar excepción.
    decision = _MOTOR.evaluar(_insumos(ingreso=0), _POLITICA)
    assert decision.resultado is ResultadoDecision.RECHAZADO


def test_thin_file_fuerza_revision() -> None:
    # EV-02: sin historial (meses_historial NO_DISPONIBLE) → revisión manual.
    decision = _MOTOR.evaluar(_insumos(meses_historial=None), _POLITICA)
    assert decision.resultado is ResultadoDecision.REVISION_MANUAL


def test_empate_exacto_en_banda_aprueba() -> None:
    # EV-07: score exactamente 70 → APROBADO (comparación `>=`).
    # dependiente +30, dti≤2500 +40 (deuda 200k/ingreso 1M=2000bps), historial 3 → 0.
    decision = _MOTOR.evaluar(_insumos(deuda=200_000, meses_historial=3), _POLITICA)
    assert decision.score == 70
    assert decision.resultado is ResultadoDecision.APROBADO


def test_rastro_tiene_una_entrada_por_regla() -> None:
    decision = _MOTOR.evaluar(_insumos(), _POLITICA)
    assert len(decision.rastro.evaluaciones) == len(_POLITICA.reglas)


# --- Invariante estrella: determinismo (property-based) --------------------


@st.composite
def _insumos_aleatorios(draw: st.DrawFn) -> Insumos:
    solicitante = Solicitante(
        Rut(11_111_111, "1"),
        Monto(draw(st.integers(min_value=0, max_value=5_000_000))),
        draw(st.sampled_from(list(SituacionLaboral))),
    )
    solicitud = Solicitud(
        "k",
        solicitante,
        "consumo",
        Monto(draw(st.integers(min_value=0, max_value=30_000_000))),
        Plazo(draw(st.integers(min_value=1, max_value=120))),
    )
    perfil = PerfilCrediticio(
        disponibilidad=draw(st.sampled_from(list(Disponibilidad))),
        deuda_total=Monto(draw(st.integers(min_value=0, max_value=10_000_000))),
        tiene_morosidad_vigente=draw(st.booleans()),
        tiene_deudas_castigadas=draw(st.booleans()),
        meses_historial=draw(st.integers(min_value=0, max_value=240)),
    )
    return Insumos(solicitud, perfil, "2026-06-26")


@given(insumos=_insumos_aleatorios())
def test_evaluacion_es_determinista(insumos: Insumos) -> None:
    """Misma (insumos, política) → misma DecisionMotor y mismo rastro, byte-a-byte.
    Si esto falla, hay no-determinismo escondido (ADR-006)."""
    primera = _MOTOR.evaluar(insumos, _POLITICA)
    segunda = _MOTOR.evaluar(insumos, _POLITICA)
    assert primera == segunda


@given(insumos=_insumos_aleatorios())
def test_score_siempre_entero_y_en_rango(insumos: Insumos) -> None:
    decision = _MOTOR.evaluar(insumos, _POLITICA)
    assert type(decision.score) is int
    assert 0 <= decision.score <= _POLITICA.config_scoring.score_maximo


@pytest.mark.parametrize("_", range(3))
def test_nunca_lanza_por_datos_faltantes(_: int) -> None:
    # Robustez (ADR-009): combinaciones de ausencia no deben lanzar.
    _MOTOR.evaluar(
        _insumos(perfil_disp=Disponibilidad.PARCIAL, deuda=None, meses_historial=None),
        _POLITICA,
    )
