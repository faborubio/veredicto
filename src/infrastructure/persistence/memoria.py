"""Repositorios en memoria (fakes) para Fase 1.

Implementan los puertos del dominio sin base de datos. Permiten el flujo punta a
punta y los tests de casos de uso (SAD §8.2). Los repositorios SQLAlchemy +
Postgres llegan en Fase 2; estos quedan como dobles de prueba.
"""

from __future__ import annotations

from domain.entities.activacion import EventoActivacionPolitica
from domain.entities.decision_motor import DecisionMotor
from domain.entities.insumos import Insumos
from domain.entities.politica import Politica
from domain.entities.reporte_impacto import CasoHistorico
from domain.errores import PoliticaInexistente, PoliticaInvalida


class RepositorioPoliticasMemoria:
    """Guarda versiones de política por (id, version). Activación explícita
    (consistente con el repo SQL): `guardar_version` no marca vigente."""

    def __init__(self) -> None:
        self._por_version: dict[tuple[str, int], Politica] = {}
        self._vigente_por_producto: dict[str, Politica] = {}

    def obtener(self, politica_id: str, version: int) -> Politica:
        try:
            return self._por_version[(politica_id, version)]
        except KeyError as exc:
            raise PoliticaInexistente(f"Política {politica_id} v{version} no existe.") from exc

    def vigente_para(self, producto: str, momento: str) -> Politica:
        try:
            return self._vigente_por_producto[producto]
        except KeyError as exc:
            raise PoliticaInexistente(f"No hay política vigente para '{producto}'.") from exc

    def guardar_version(self, politica: Politica) -> None:
        clave = (politica.id, politica.version)
        if clave in self._por_version:
            raise PoliticaInvalida(
                f"La política {politica.id} v{politica.version} ya existe; es inmutable (CF-04)."
            )
        self._por_version[clave] = politica

    def activar(self, producto: str, politica_id: str, version: int) -> None:
        politica = self.obtener(politica_id, version)
        self._vigente_por_producto[producto] = politica


class RepositorioDecisionesMemoria:
    """Persiste decisiones + snapshot de insumos, indexadas por idempotency_key
    (ADR-010, ADR-004)."""

    def __init__(self) -> None:
        self._por_key: dict[str, tuple[DecisionMotor, Insumos]] = {}

    def por_idempotency_key(self, key: str) -> DecisionMotor | None:
        registro = self._por_key.get(key)
        return registro[0] if registro is not None else None

    def por_solicitud(self, solicitud_id: str) -> DecisionMotor | None:
        # En Fase 1 indexamos por idempotency_key, que actúa como id de solicitud.
        return self.por_idempotency_key(solicitud_id)

    def guardar(self, idempotency_key: str, decision: DecisionMotor, snapshot: Insumos) -> None:
        self._por_key[idempotency_key] = (decision, snapshot)

    def snapshots_de_poblacion(self, criterio: object) -> list[Insumos]:
        # Población completa en Fase 1; el filtrado real llega en Fase 3.
        return [snapshot for _, snapshot in self._por_key.values()]

    def casos_para_simulacion(self, criterio: object) -> list[CasoHistorico]:
        return [
            CasoHistorico(snapshot=snapshot, resultado_original=decision.resultado)
            for decision, snapshot in self._por_key.values()
        ]


class RepositorioActivacionesMemoria:
    """Historial de activaciones de política (ADR-008)."""

    def __init__(self) -> None:
        self._eventos: list[EventoActivacionPolitica] = []

    def registrar(self, evento: EventoActivacionPolitica) -> None:
        self._eventos.append(evento)

    def historial(self, producto: str) -> list[EventoActivacionPolitica]:
        return [e for e in self._eventos if e.producto == producto]
