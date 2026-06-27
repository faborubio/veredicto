"""Reporte de impacto de una simulación what-if (Fase 3, SAD §6.2).

`CasoHistorico` es la unidad de entrada: un snapshot de insumos as-seen + el
resultado que el motor produjo en su momento. El `ReporteImpacto` resume cómo
cambiarían las decisiones bajo una política candidata, sin afectar producción.

Honestidad de diseño (SAD §6.2 · CASES.md SI-02): si la política candidata lee un
`fuente_dato` que no está capturado en los snapshots, esas reglas se reportan como
**no evaluables** sobre el histórico, en vez de inventar un valor.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.entities.insumos import Insumos
from domain.entities.politica import ResultadoDecision


@dataclass(frozen=True, slots=True)
class CriterioSimulacion:
    """Filtro de la población histórica a simular (SAD §6.2).

    `producto`: acota a un producto (evita simular una candidata de consumo sobre
    decisiones de otro producto). `limite`: cota superior de casos cargados —
    mitigación parcial de SI-03 mientras no haya streaming server-side.
    """

    producto: str | None = None
    limite: int | None = None


@dataclass(frozen=True, slots=True)
class CasoHistorico:
    """Un caso del histórico: insumos as-seen + el resultado original del motor."""

    snapshot: Insumos
    resultado_original: ResultadoDecision


@dataclass(frozen=True, slots=True)
class Flip:
    """Un cambio de resultado bajo la política candidata, con su recuento."""

    desde: ResultadoDecision
    hacia: ResultadoDecision
    cantidad: int


@dataclass(frozen=True, slots=True)
class ReporteImpacto:
    """Resumen determinista del impacto de una política candidata."""

    total_evaluados: int
    sin_cambio: int
    flips: tuple[Flip, ...]
    distribucion_original: tuple[tuple[ResultadoDecision, int], ...]
    distribucion_candidata: tuple[tuple[ResultadoDecision, int], ...]
    # Ids de reglas candidatas que no se pueden evaluar sobre el histórico (SI-02).
    reglas_no_evaluables: tuple[str, ...]
