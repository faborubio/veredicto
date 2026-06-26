"""ConsultarDecision: recupera una decisión histórica + su rastro (lectura).

Envuelta por las herramientas MCP `consultar_decision` y `rastro_auditoria`
(SAD §5.3). Si no existe → error tipado `DecisionInexistente` (CASES.md MC-01).
"""

from __future__ import annotations

from domain.ports.repositorio_decisiones import RepositorioDecisiones


class ConsultarDecision:
    def __init__(self, decisiones: RepositorioDecisiones) -> None:
        self._decisiones = decisiones

    # TODO(Fase 2): ejecutar(solicitud_id) -> DecisionMotor (o DecisionInexistente).
