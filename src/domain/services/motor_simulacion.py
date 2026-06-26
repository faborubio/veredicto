"""MotorSimulacion: replay de una política candidata contra población histórica.

Contrato (a implementar en Fase 3):

    simular(snapshots: Iterable[Insumos], politica_candidata: Politica)
        -> ReporteImpacto

Reusa los SNAPSHOTS de insumos guardados, NUNCA vuelve a llamar al buró
(reproducibilidad; TROUBLESHOOTING.md). Es puro: lectura + cómputo, sin
persistir (CASES.md SI-04).

Límite honesto (SAD §6.2 · CASES.md SI-02): una regla candidata que lee un
`fuente_dato` ausente en el snapshot se marca "no evaluable sobre histórico" y se
reporta; nunca se inventa un valor.
"""

from __future__ import annotations

from collections.abc import Iterable

from domain.entities.insumos import Insumos
from domain.entities.politica import Politica


class MotorSimulacion:
    """Reevaluación masiva sin efectos. Construido sobre MotorEvaluacion."""

    def simular(
        self,
        snapshots: Iterable[Insumos],
        politica_candidata: Politica,
    ) -> object:  # TODO(Fase 3): -> ReporteImpacto
        raise NotImplementedError("MotorSimulacion.simular se implementa en Fase 3.")
