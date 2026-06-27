"""Composition root: cableado de puertos→adaptadores con `injector` (ADR-001).

Único lugar que conoce casos de uso (`application/`) y adaptadores concretos
(`infrastructure/`). La persistencia se elige por entorno:
  - por defecto: repos en memoria (dev/tests rápidos, sin BD);
  - `VEREDICTO_PERSISTENCIA=sql`: repos SQLAlchemy sobre Postgres.

Cambiar de una a otra es sólo cambiar el módulo de binds —sin tocar dominio ni
aplicación—, que es justo el pago de la Clean Architecture (ADR-001).
"""

from __future__ import annotations

import os

from injector import Injector, Module, provider, singleton
from sqlalchemy.orm import Session, sessionmaker

from application.casos_uso.consultar_decision import ConsultarDecision
from application.casos_uso.evaluar_solicitud import EvaluarSolicitud
from application.casos_uso.explicar_decision import ExplicarDecision
from application.casos_uso.gestionar_reglas import GestionarReglas
from application.casos_uso.simular_cambio_regla import SimularCambioRegla
from domain.errores import PoliticaInexistente
from domain.ports.gateway_buro import GatewayBuro
from domain.ports.repositorio_activaciones import RepositorioActivaciones
from domain.ports.repositorio_decisiones import RepositorioDecisiones
from domain.ports.repositorio_politicas import RepositorioPoliticas
from domain.services.motor_evaluacion import MotorEvaluacion
from domain.services.motor_simulacion import MotorSimulacion
from infrastructure.buro.buro_simulado import ESCENARIOS_DEMO, BuroSimulado
from infrastructure.persistence.db import crear_engine, crear_session_factory
from infrastructure.persistence.memoria import (
    RepositorioActivacionesMemoria,
    RepositorioDecisionesMemoria,
    RepositorioPoliticasMemoria,
)
from infrastructure.persistence.repositorio_activaciones_sql import (
    RepositorioActivacionesSQLAlchemy,
)
from infrastructure.persistence.repositorio_decisiones_sql import RepositorioDecisionesSQLAlchemy
from infrastructure.persistence.repositorio_politicas_sql import RepositorioPoliticasSQLAlchemy
from infrastructure.seed.politica_consumo import politica_consumo_v1


def _sembrar(politicas: RepositorioPoliticas) -> None:
    """Asegura la política de consumo v1 vigente (idempotente)."""
    try:
        politicas.obtener("consumo", 1)
    except PoliticaInexistente:
        politicas.guardar_version(politica_consumo_v1())
        politicas.activar("consumo", "consumo", 1)


class ModuloAplicacion(Module):
    """Casos de uso + adaptadores que no dependen de la persistencia."""

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
    def evaluar_solicitud(
        self,
        motor: MotorEvaluacion,
        politicas: RepositorioPoliticas,
        decisiones: RepositorioDecisiones,
        buro: GatewayBuro,
    ) -> EvaluarSolicitud:
        return EvaluarSolicitud(motor, politicas, decisiones, buro)

    @provider
    @singleton
    def gestionar_reglas(
        self,
        politicas: RepositorioPoliticas,
        activaciones: RepositorioActivaciones,
    ) -> GestionarReglas:
        return GestionarReglas(politicas, activaciones)

    @provider
    @singleton
    def consultar_decision(self, decisiones: RepositorioDecisiones) -> ConsultarDecision:
        return ConsultarDecision(decisiones)

    @provider
    @singleton
    def explicar_decision(self, decisiones: RepositorioDecisiones) -> ExplicarDecision:
        return ExplicarDecision(decisiones)

    @provider
    @singleton
    def motor_simulacion(self, motor: MotorEvaluacion) -> MotorSimulacion:
        return MotorSimulacion(motor)

    @provider
    @singleton
    def simular_cambio_regla(
        self,
        motor_simulacion: MotorSimulacion,
        decisiones: RepositorioDecisiones,
    ) -> SimularCambioRegla:
        return SimularCambioRegla(motor_simulacion, decisiones)


class ModuloMemoria(Module):
    """Persistencia en memoria (por defecto)."""

    @provider
    @singleton
    def politicas(self) -> RepositorioPoliticas:
        repo = RepositorioPoliticasMemoria()
        _sembrar(repo)
        return repo

    @provider
    @singleton
    def decisiones(self) -> RepositorioDecisiones:
        return RepositorioDecisionesMemoria()

    @provider
    @singleton
    def activaciones(self) -> RepositorioActivaciones:
        return RepositorioActivacionesMemoria()


class ModuloSQL(Module):
    """Persistencia SQLAlchemy sobre Postgres (`VEREDICTO_PERSISTENCIA=sql`).

    Acepta un `session_factory` explícito (seam de testabilidad); si no, lo
    construye desde `DATABASE_URL`.
    """

    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._sf = session_factory or crear_session_factory(crear_engine())

    @provider
    @singleton
    def politicas(self) -> RepositorioPoliticas:
        repo = RepositorioPoliticasSQLAlchemy(self._sf)
        _sembrar(repo)
        return repo

    @provider
    @singleton
    def decisiones(self) -> RepositorioDecisiones:
        return RepositorioDecisionesSQLAlchemy(self._sf)

    @provider
    @singleton
    def activaciones(self) -> RepositorioActivaciones:
        return RepositorioActivacionesSQLAlchemy(self._sf)


def _modulo_persistencia() -> Module:
    if os.environ.get("VEREDICTO_PERSISTENCIA") == "sql":
        return ModuloSQL()
    return ModuloMemoria()


def crear_injector() -> Injector:
    return Injector([ModuloAplicacion(), _modulo_persistencia()])


_injector_compartido: Injector | None = None


def obtener_injector() -> Injector:
    """Composition root ÚNICO del proceso, compartido por REST y MCP (Fase 5, inc 1).

    REST y MCP son adaptadores hermanos sobre los mismos casos de uso (ADR-005); al
    correr en un solo proceso ASGI comparten este injector → una sola conexión y un
    solo store. Resuelve que antes el MCP tuviera su propio injector (store en memoria
    vacío). `crear_injector` sigue disponible para tests que necesiten una instancia
    aislada.
    """
    global _injector_compartido
    if _injector_compartido is None:
        _injector_compartido = crear_injector()
    return _injector_compartido
