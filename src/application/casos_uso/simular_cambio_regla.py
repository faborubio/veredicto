"""SimularCambioRegla: what-if sobre población histórica (SAD §6.2).

Carga los casos históricos (snapshot + resultado original) y reevalúa cada uno con
la política candidata vía `MotorSimulacion`. NO re-llama al buró (usa el snapshot)
y NO persiste nada (CASES.md SI-04): es lectura + cómputo puro. Reporta las reglas
no evaluables sobre el histórico, sin inventar datos (SI-02).

Envuelto por la herramienta MCP `simular_cambio_regla(politica_candidata, poblacion)`.
"""

from __future__ import annotations

from domain.entities.politica import Politica
from domain.entities.reporte_impacto import ReporteImpacto
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

    def ejecutar(self, politica_candidata: Politica, criterio: object = None) -> ReporteImpacto:
        casos = self._decisiones.casos_para_simulacion(criterio)
        return self._motor.simular(casos, politica_candidata)
