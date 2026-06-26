"""ExplicarDecision: renderiza el rastro a razones legibles (lectura).

Envuelta por la herramienta MCP `explicar_decision`. Aplica minimización de PII:
devuelve sólo lo necesario para explicar, nunca PII completa (CASES.md MC-02 · §8.1).
"""

from __future__ import annotations

from domain.ports.repositorio_decisiones import RepositorioDecisiones


class ExplicarDecision:
    def __init__(self, decisiones: RepositorioDecisiones) -> None:
        self._decisiones = decisiones

    # TODO(Fase 1/4): ejecutar(solicitud_id) -> explicación estructurada legible.
