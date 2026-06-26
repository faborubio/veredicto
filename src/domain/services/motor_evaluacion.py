"""MotorEvaluacion: intérprete PURO y ESTABLE (ADR-006, ADR-008).

Contrato (a implementar en Fase 1):

    evaluar(insumos: Insumos, politica: Politica) -> DecisionMotor

Propiedades que DEBE cumplir (verificadas con property-based testing en Fase 1):
  - Determinismo: misma (insumos, politica) → mismo DecisionMotor y mismo rastro,
    byte-a-byte, en cualquier entorno (scoring entero, orden estable).
  - Pureza: sin I/O, sin datetime.now(), sin azar, sin estado mutable, sin float.
  - Estabilidad: toda la semántica (pesos, agregación, bandas) se lee de la
    política; el motor sólo la interpreta.
  - Robustez: nunca lanza por datos faltantes; aplica `ante_dato_faltante` y lo
    registra en el rastro como NA (ADR-009).

Lógica de decisión (SAD §5.2):
  1. Hard-stops primero: si alguna HARD_STOP falla → RECHAZADO (con rastro).
  2. Scoring: agregación según `config_scoring.metodo_agregacion` → score entero
     → banda (`>=` sobre umbral_min, EV-07).
  3. Warnings: no cambian el resultado; se marcan en el rastro.
"""

from __future__ import annotations

from domain.entities.decision_motor import DecisionMotor
from domain.entities.insumos import Insumos
from domain.entities.politica import Politica


class MotorEvaluacion:
    """Intérprete estable de políticas. Sin dependencias hacia afuera."""

    def evaluar(self, insumos: Insumos, politica: Politica) -> DecisionMotor:
        # TODO(Fase 1): implementar la lógica de decisión + construcción del rastro.
        raise NotImplementedError("MotorEvaluacion.evaluar se implementa en Fase 1.")
