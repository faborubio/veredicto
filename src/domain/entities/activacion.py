"""EventoActivacionPolitica: activar una versión de política es un acto auditado.

ADR-008: la activación queda registrada (quién/qué/cuándo). Combinado con fijar
la versión vigente al inicio del request, cierra la ventana TOCTOU de activación
concurrente (CLAUDE.md invariante 9 · SAD §11 riesgo TOCTOU).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EventoActivacionPolitica:
    """Hecho inmutable: una versión de política pasó a vigente."""

    politica_id: str
    politica_version: int
    producto: str
    actor: str
    momento: str  # ISO-8601; tipo fecha en Fase 1
