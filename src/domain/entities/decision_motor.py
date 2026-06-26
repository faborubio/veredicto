"""DecisionMotor: salida inmutable del motor de evaluación.

Resultado (APROBADO / RECHAZADO / REVISION_MANUAL) + score entero + rastro +
referencia EXCLUSIVA a la versión de política que decidió (ADR-003, ADR-008).
No contiene PII ni I/O; es un hecho reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.entities.politica import ResultadoDecision
from domain.entities.rastro import RastroDecision


@dataclass(frozen=True, slots=True)
class DecisionMotor:
    """Veredicto del motor para una solicitud, dado una versión de política."""

    politica_id: str
    politica_version: int
    resultado: ResultadoDecision
    score: int  # entero (ADR-006)
    rastro: RastroDecision
