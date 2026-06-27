"""ConsultarDecision: recupera una decisión histórica + su rastro (lectura).

Envuelta por las herramientas MCP `consultar_decision` y `rastro_auditoria`
(SAD §5.3). Si no existe → error tipado `DecisionInexistente` (CASES.md MC-01),
que la capa de entrega traduce a una respuesta clara (no un stack trace).
"""

from __future__ import annotations

from domain.entities.decision_motor import DecisionMotor
from domain.errores import DecisionInexistente
from domain.ports.repositorio_decisiones import RepositorioDecisiones


class ConsultarDecision:
    def __init__(self, decisiones: RepositorioDecisiones) -> None:
        self._decisiones = decisiones

    def ejecutar(self, solicitud_id: str) -> DecisionMotor:
        decision = self._decisiones.por_solicitud(solicitud_id)
        if decision is None:
            raise DecisionInexistente(f"No existe decisión para la solicitud '{solicitud_id}'.")
        return decision
