"""Puerto de persistencia de eventos de activación de política (ADR-008)."""

from __future__ import annotations

from typing import Protocol

from domain.entities.activacion import EventoActivacionPolitica


class RepositorioActivaciones(Protocol):
    def registrar(self, evento: EventoActivacionPolitica) -> None:
        """Persiste el evento auditado de activación (quién/qué/cuándo)."""
        ...

    def historial(self, producto: str) -> list[EventoActivacionPolitica]:
        """Devuelve el historial de activaciones de un producto, ordenado."""
        ...
