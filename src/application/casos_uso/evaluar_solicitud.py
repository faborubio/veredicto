"""EvaluarSolicitud: el caso de uso central (SAD §6.1).

Orquesta el flujo manteniendo el motor puro:
  1. ¿Existe decisión para `idempotency_key`? → devolverla sin recomputar (ADR-010).
  2. Resolver y FIJAR la política vigente al inicio del request (anti-TOCTOU, ADR-008).
  3. Obtener perfil de buró vía puerto (as-seen; puede ser parcial/ausente).
  4. Construir `Insumos` (snapshot) con el momento explícito (ADR-006).
  5. motor.evaluar(insumos, politica) → DecisionMotor + rastro (PURO).
  6. Persistir decisión + SNAPSHOT íntegro + idempotency_key (ADR-004).

El tiempo entra como parámetro explícito (`momento`); el adaptador de entrada
(REST/MCP) lee el reloj, no el dominio. NO se expone vía MCP en el MVP (escritura).
"""

from __future__ import annotations

from domain.entities.decision_motor import DecisionMotor
from domain.entities.insumos import Insumos
from domain.entities.solicitud import Solicitud
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

    def ejecutar(self, solicitud: Solicitud, momento: str) -> DecisionMotor:
        previa = self._decisiones.por_idempotency_key(solicitud.idempotency_key)
        if previa is not None:
            return previa  # idempotencia: misma clave → misma decisión (ADR-010)

        politica = self._politicas.vigente_para(solicitud.producto, momento)
        perfil = self._buro.obtener_perfil(solicitud.solicitante.rut)
        insumos = Insumos(solicitud=solicitud, perfil=perfil, momento_evaluacion=momento)

        decision = self._motor.evaluar(insumos, politica)

        self._decisiones.guardar(solicitud.idempotency_key, decision, insumos)
        return decision
