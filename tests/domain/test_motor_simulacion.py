"""Tests del MotorSimulacion (Fase 3). Puro: lectura + cómputo, sin efectos.

Cubre el reporte de impacto (flips/distribución), el límite honesto SI-02 (reglas
no evaluables sobre el histórico) y el determinismo.
"""

from __future__ import annotations

from dataclasses import replace

from domain.entities.insumos import Insumos
from domain.entities.perfil_crediticio import PerfilCrediticio
from domain.entities.politica import Banda, Politica, ResultadoDecision
from domain.entities.predicado import Comparacion, Comparador
from domain.entities.regla import AnteDatoFaltante, Categoria, Regla, TipoRegla
from domain.entities.reporte_impacto import CasoHistorico
from domain.entities.solicitud import SituacionLaboral, Solicitante, Solicitud
from domain.services.motor_evaluacion import MotorEvaluacion
from domain.services.motor_simulacion import MotorSimulacion
from domain.value_objects.disponibilidad import Disponibilidad
from domain.value_objects.monto import Monto
from domain.value_objects.plazo import Plazo
from domain.value_objects.rut import Rut, calcular_dv
from infrastructure.seed.politica_consumo import politica_consumo_v1

_MOTOR = MotorEvaluacion()
_SIM = MotorSimulacion()
_POLITICA = politica_consumo_v1()


def _insumos(deuda: int = 300_000, meses: int = 36) -> Insumos:
    rut = Rut(11_111_111, calcular_dv(11_111_111))
    solicitante = Solicitante(rut, Monto(1_000_000), SituacionLaboral.DEPENDIENTE)
    solicitud = Solicitud("k", solicitante, "consumo", Monto(2_000_000), Plazo(24))
    perfil = PerfilCrediticio(
        disponibilidad=Disponibilidad.DISPONIBLE,
        deuda_total=Monto(deuda),
        tiene_morosidad_vigente=False,
        tiene_deudas_castigadas=False,
        meses_historial=meses,
    )
    return Insumos(solicitud, perfil, "2026-06-26T00:00:00+00:00")


def _caso(deuda: int = 300_000, meses: int = 36) -> CasoHistorico:
    insumos = _insumos(deuda, meses)
    original = _MOTOR.evaluar(insumos, _POLITICA).resultado
    return CasoHistorico(snapshot=insumos, resultado_original=original)


def _politica_mas_estricta() -> Politica:
    # Sube el umbral de aprobación a 90: el caso limpio (score 85) cae a revisión.
    nuevas_bandas = (
        Banda(90, ResultadoDecision.APROBADO),
        Banda(40, ResultadoDecision.REVISION_MANUAL),
        Banda(0, ResultadoDecision.RECHAZADO),
    )
    return replace(
        _POLITICA, version=2, config_scoring=replace(_POLITICA.config_scoring, bandas=nuevas_bandas)
    )


def test_misma_politica_no_genera_flips() -> None:
    casos = [_caso(), _caso(deuda=200_000)]
    reporte = _SIM.simular(casos, _POLITICA)
    assert reporte.total_evaluados == 2
    assert reporte.sin_cambio == 2
    assert reporte.flips == ()


def test_politica_mas_estricta_genera_flip_aprobado_a_revision() -> None:
    casos = [_caso()]  # caso limpio: original APROBADO (score 85)
    reporte = _SIM.simular(casos, _politica_mas_estricta())

    assert reporte.sin_cambio == 0
    assert len(reporte.flips) == 1
    flip = reporte.flips[0]
    assert flip.desde is ResultadoDecision.APROBADO
    assert flip.hacia is ResultadoDecision.REVISION_MANUAL
    assert flip.cantidad == 1


def test_distribucion_cubre_todos_los_resultados() -> None:
    reporte = _SIM.simular([_caso()], _POLITICA)
    etiquetas = [r for r, _ in reporte.distribucion_candidata]
    assert etiquetas == list(ResultadoDecision)  # orden estable


def test_si02_regla_no_evaluable_se_reporta_sin_inventar() -> None:
    # Política candidata con una regla que lee un campo NO capturado en snapshots.
    regla_nueva = Regla(
        id="R-nueva-fuente",
        nombre="lee un dato no capturado",
        categoria=Categoria.COMPORTAMIENTO,
        tipo=TipoRegla.SCORING,
        predicado=Comparacion("score_externo", Comparador.GTE, 700),
        fuente_dato="score_externo",
        ante_dato_faltante=AnteDatoFaltante.FORZAR_REVISION,
        plantilla_explicacion="x",
        peso=10,
    )
    candidata = replace(_POLITICA, version=3, reglas=(*_POLITICA.reglas, regla_nueva))

    reporte = _SIM.simular([_caso()], candidata)
    assert "R-nueva-fuente" in reporte.reglas_no_evaluables
    # El resto sí se evalúa: el caso limpio sigue siendo APROBADO.
    assert reporte.total_evaluados == 1


def test_poblacion_vacia() -> None:
    reporte = _SIM.simular([], _POLITICA)
    assert reporte.total_evaluados == 0
    assert reporte.flips == ()


def test_simulacion_es_determinista() -> None:
    casos = [_caso(), _caso(deuda=200_000), _caso(meses=3)]
    assert _SIM.simular(casos, _POLITICA) == _SIM.simular(casos, _POLITICA)
