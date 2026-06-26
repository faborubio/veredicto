"""Composition root: cableado de puertos→adaptadores con `injector` (ADR-001).

Es el único lugar que conoce a la vez los casos de uso (`application/`) y los
adaptadores concretos (`infrastructure/`). REST y MCP piden los casos de uso ya
cableados; ninguna capa de entrega conoce las implementaciones concretas.

En Fase 1 los adaptadores son en memoria + buró simulado, sembrados con la
política de consumo v1. La sustitución por SQLAlchemy en Fase 2 es un cambio de
binds aquí, sin tocar dominio ni aplicación.
"""

from __future__ import annotations

from injector import Injector, Module, provider, singleton

from application.casos_uso.evaluar_solicitud import EvaluarSolicitud
from domain.ports.gateway_buro import GatewayBuro
from domain.ports.repositorio_decisiones import RepositorioDecisiones
from domain.ports.repositorio_politicas import RepositorioPoliticas
from domain.services.motor_evaluacion import MotorEvaluacion
from infrastructure.buro.buro_simulado import ESCENARIOS_DEMO, BuroSimulado
from infrastructure.persistence.memoria import (
    RepositorioDecisionesMemoria,
    RepositorioPoliticasMemoria,
)
from infrastructure.seed.politica_consumo import politica_consumo_v1


class ModuloVeredicto(Module):
    """Binds de la fase local (en memoria + buró simulado)."""

    @provider
    @singleton
    def motor(self) -> MotorEvaluacion:
        return MotorEvaluacion()

    @provider
    @singleton
    def buro(self) -> GatewayBuro:
        return BuroSimulado(ESCENARIOS_DEMO)

    @provider
    @singleton
    def repositorio_politicas(self) -> RepositorioPoliticas:
        repo = RepositorioPoliticasMemoria()
        repo.guardar_version(politica_consumo_v1())
        return repo

    @provider
    @singleton
    def repositorio_decisiones(self) -> RepositorioDecisiones:
        return RepositorioDecisionesMemoria()

    @provider
    @singleton
    def evaluar_solicitud(
        self,
        motor: MotorEvaluacion,
        politicas: RepositorioPoliticas,
        decisiones: RepositorioDecisiones,
        buro: GatewayBuro,
    ) -> EvaluarSolicitud:
        return EvaluarSolicitud(motor, politicas, decisiones, buro)


def crear_injector() -> Injector:
    return Injector([ModuloVeredicto()])
