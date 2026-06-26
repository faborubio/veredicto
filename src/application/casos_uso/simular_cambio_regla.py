"""SimularCambioRegla: what-if sobre población histórica (SAD §6.2).

Carga snapshots históricos (no re-llama al buró) y reevalúa con la política
candidata vía MotorSimulacion. No persiste nada (CASES.md SI-04). Reporta las
reglas no evaluables sobre el histórico, sin inventar datos (SI-02).

Envuelta por la herramienta MCP `simular_cambio_regla(politica_candidata, poblacion)`.
"""

from __future__ import annotations

from domain.ports.repositorio_decisiones import RepositorioDecisiones
from domain.services.motor_simulacion import MotorSimulacion


class SimularCambioRegla:
    def __init__(
        self,
        motor_simulacion: MotorSimulacion,
        decisiones: RepositorioDecisiones,
    ) -> None:
        self._motor = motor_simulacion
        self._decisiones = decisiones

    # TODO(Fase 3): ejecutar(politica_candidata, poblacion) -> ReporteImpacto.
