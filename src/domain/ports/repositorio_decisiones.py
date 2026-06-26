"""Puerto de persistencia de decisiones + snapshots de insumos (ADR-004, ADR-010)."""

from __future__ import annotations

from typing import Protocol

from domain.entities.decision_motor import DecisionMotor
from domain.entities.insumos import Insumos


class RepositorioDecisiones(Protocol):
    def por_idempotency_key(self, key: str) -> DecisionMotor | None:
        """Devuelve la decisión previa para una clave, o None (idempotencia,
        ADR-010). Si existe, el caso de uso no recomputa."""
        ...

    def por_solicitud(self, solicitud_id: str) -> DecisionMotor | None:
        """Para ConsultarDecision / ExplicarDecision (None si no existe, MC-01)."""
        ...

    def guardar(
        self,
        idempotency_key: str,
        decision: DecisionMotor,
        snapshot: Insumos,
    ) -> None:
        """Persiste decisión + SNAPSHOT íntegro de insumos (ADR-004). Sin el
        snapshot, la simulación posterior no es fiel."""
        ...

    def snapshots_de_poblacion(self, criterio: object) -> list[Insumos]:
        """Carga snapshots históricos para simulación (ADR-004 · §6.2).
        `criterio` se tipa en Fase 3 (rango de fechas/producto)."""
        ...
