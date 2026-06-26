"""MotorEvaluacion: intérprete PURO y ESTABLE (ADR-006, ADR-008).

    evaluar(insumos: Insumos, politica: Politica) -> DecisionMotor

Propiedades garantizadas:
  - **Determinismo:** misma (insumos, politica) → mismo DecisionMotor y mismo
    rastro, byte-a-byte (scoring entero, orden estable de reglas). Verificado con
    property-based testing.
  - **Pureza:** sin I/O, sin reloj, sin azar, sin estado mutable, sin float.
  - **Estabilidad:** toda la semántica (pesos, agregación, bandas) se lee de la
    política; el motor sólo la interpreta.
  - **Robustez:** nunca lanza por datos faltantes; aplica `ante_dato_faltante` y
    lo registra en el rastro como NA (ADR-009).

Convención de predicados: el predicado de una regla expresa la condición para que
la regla PASE. Un HARD_STOP que NO pasa → rechazo. Un SCORING que pasa → suma su
peso.

Precedencia de decisión (determinista, documentada — SAD §5.2):
  1. Si algún HARD_STOP falla (confirmado) → RECHAZADO.
  2. Si no, si alguna regla fuerza revisión (dato faltante con FORZAR_REVISION) →
     REVISION_MANUAL.
  3. Si no, score → banda (`>=` sobre umbral_min, EV-07).
Un rechazo confirmado domina sobre la incertidumbre de una revisión forzada.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.entities.decision_motor import DecisionMotor
from domain.entities.insumos import Insumos
from domain.entities.politica import Banda, Politica, ResultadoDecision
from domain.entities.rastro import (
    EvaluacionRegla,
    RastroDecision,
    ResultadoEvaluacionRegla,
)
from domain.entities.regla import AnteDatoFaltante, Regla, TipoRegla
from domain.value_objects.disponibilidad import Disponibilidad


@dataclass(frozen=True, slots=True)
class _ResultadoRegla:
    evaluacion: EvaluacionRegla
    hardstop_falla: bool
    fuerza_revision: bool
    aporte: int


class MotorEvaluacion:
    """Intérprete estable de políticas. Sin dependencias hacia afuera."""

    def evaluar(self, insumos: Insumos, politica: Politica) -> DecisionMotor:
        evaluaciones: list[EvaluacionRegla] = []
        hay_hardstop_falla = False
        hay_forzar_revision = False
        score = 0

        for regla in politica.reglas:
            res = self._evaluar_regla(regla, insumos)
            evaluaciones.append(res.evaluacion)
            hay_hardstop_falla = hay_hardstop_falla or res.hardstop_falla
            hay_forzar_revision = hay_forzar_revision or res.fuerza_revision
            score += res.aporte

        if hay_hardstop_falla:
            resultado = ResultadoDecision.RECHAZADO
        elif hay_forzar_revision:
            resultado = ResultadoDecision.REVISION_MANUAL
        else:
            resultado = _banda_para(score, politica.config_scoring.bandas)

        return DecisionMotor(
            politica_id=politica.id,
            politica_version=politica.version,
            resultado=resultado,
            score=score,
            rastro=RastroDecision(tuple(evaluaciones)),
        )

    def _evaluar_regla(self, regla: Regla, insumos: Insumos) -> _ResultadoRegla:
        disponibilidad, valor = insumos.valor_y_disponibilidad(regla.fuente_dato)

        if disponibilidad is Disponibilidad.NO_DISPONIBLE:
            return self._regla_con_dato_faltante(regla, disponibilidad)

        assert valor is not None  # disponibilidad DISPONIBLE garantiza valor presente
        pasa = regla.predicado.evaluar({regla.fuente_dato: valor})
        resultado = ResultadoEvaluacionRegla.PASA if pasa else ResultadoEvaluacionRegla.FALLA

        hardstop_falla = regla.tipo is TipoRegla.HARD_STOP and not pasa
        aporte = regla.peso if (regla.tipo is TipoRegla.SCORING and pasa) else 0

        return _ResultadoRegla(
            evaluacion=EvaluacionRegla(
                regla_id=regla.id,
                tipo=regla.tipo,
                resultado=resultado,
                fuente_dato=regla.fuente_dato,
                disponibilidad=disponibilidad,
                valor_observado=valor,
                aporte_score=aporte or 0,
                explicacion=_explicar(regla, resultado, valor),
            ),
            hardstop_falla=hardstop_falla,
            fuerza_revision=False,
            aporte=aporte or 0,
        )

    def _regla_con_dato_faltante(
        self, regla: Regla, disponibilidad: Disponibilidad
    ) -> _ResultadoRegla:
        """Aplica el `ante_dato_faltante` declarado por la regla (ADR-009)."""
        ante = regla.ante_dato_faltante
        hardstop_falla = False
        fuerza_revision = False
        aporte = 0

        if ante is AnteDatoFaltante.TRATAR_COMO_FALLA:
            hardstop_falla = regla.tipo is TipoRegla.HARD_STOP
        elif ante is AnteDatoFaltante.TRATAR_COMO_OK:
            aporte = regla.peso if (regla.tipo is TipoRegla.SCORING and regla.peso) else 0
        else:  # FORZAR_REVISION
            fuerza_revision = True

        return _ResultadoRegla(
            evaluacion=EvaluacionRegla(
                regla_id=regla.id,
                tipo=regla.tipo,
                resultado=ResultadoEvaluacionRegla.NA,
                fuente_dato=regla.fuente_dato,
                disponibilidad=disponibilidad,
                valor_observado=None,
                aporte_score=aporte,
                explicacion=_explicar(regla, ResultadoEvaluacionRegla.NA, None),
            ),
            hardstop_falla=hardstop_falla,
            fuerza_revision=fuerza_revision,
            aporte=aporte,
        )


def _banda_para(score: int, bandas: tuple[Banda, ...]) -> ResultadoDecision:
    """Primera banda (de mayor a menor umbral) cuyo `umbral_min <= score` (EV-07).
    El orden se impone aquí para no depender del orden de declaración."""
    for banda in sorted(bandas, key=lambda b: b.umbral_min, reverse=True):
        if score >= banda.umbral_min:
            return banda.resultado
    raise ValueError("Configuración de bandas incompleta: ningún umbral cubre el score.")


def _explicar(
    regla: Regla,
    resultado: ResultadoEvaluacionRegla,
    valor: object,
) -> str:
    if resultado is ResultadoEvaluacionRegla.NA:
        return (
            f"{regla.plantilla_explicacion} — dato '{regla.fuente_dato}' no disponible; "
            f"acción: {regla.ante_dato_faltante.value}."
        )
    try:
        base = regla.plantilla_explicacion.format(valor=valor)
    except (KeyError, IndexError):
        base = regla.plantilla_explicacion
    return f"{base} [{resultado.value}]"
