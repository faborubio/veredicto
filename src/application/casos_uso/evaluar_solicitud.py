"""EvaluarSolicitud: el caso de uso central (SAD §6.1).

Orquesta el flujo, manteniendo el motor puro:
  1. ¿Existe decisión para `idempotency_key`? → devolverla sin recomputar (ADR-010).
  2. Resolver y FIJAR la política vigente al inicio del request (anti-TOCTOU, ADR-008).
  3. Obtener perfil de buró vía puerto (as-seen; puede ser parcial/ausente).
  4. Construir `Insumos` (snapshot) + momento explícito.
  5. motor.evaluar(insumos, politica) → DecisionMotor + rastro (PURO).
  6. Persistir decisión + SNAPSHOT íntegro + versión + idempotency_key (ADR-004).

NO se expone vía MCP en el MVP (es escritura, SAD §5.3).
"""

from __future__ import annotations

from domain.ports.gateway_buro import GatewayBuro
from domain.ports.repositorio_decisiones import RepositorioDecisiones
from domain.ports.repositorio_politicas import RepositorioPoliticas
from domain.services.motor_evaluacion import MotorEvaluacion


class EvaluarSolicitud:
    def __init__(
        self,
        motor: MotorEvaluacion,
        politicas: RepositorioPoliticas,
        decisiones: RepositorioDecisiones,
        buro: GatewayBuro,
    ) -> None:
        self._motor = motor
        self._politicas = politicas
        self._decisiones = decisiones
        self._buro = buro

    # TODO(Fase 1): ejecutar(comando) -> DecisionMotor, según el flujo de §6.1.
