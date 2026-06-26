"""DecisionFinal: vínculo auditable entre el motor y el override humano (ADR-011).

Cuando el resultado del motor es REVISION_MANUAL, un humano puede decidir el
resultado final. Esta entidad envuelve la `DecisionMotor` y, si hubo override,
quién/por qué/cuándo/qué resultó, para que el rastro de auditoría no se rompa
justo donde más importa. El *flujo* de revisión (UI, colas) es externo (§3.3).
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.entities.decision_motor import DecisionMotor
from domain.entities.politica import ResultadoDecision


@dataclass(frozen=True, slots=True)
class OverrideHumano:
    """El acto humano que anula o confirma al motor."""

    actor: str
    justificacion: str
    momento: str  # ISO-8601; tipo fecha en Fase 1
    resultado_final: ResultadoDecision


@dataclass(frozen=True, slots=True)
class DecisionFinal:
    """DecisionMotor + override humano opcional.

    Si `override is None`, el resultado final es el del motor.
    """

    decision_motor: DecisionMotor
    override: OverrideHumano | None = None
