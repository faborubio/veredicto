"""RastroDecision + EvaluacionRegla. El artefacto de explicabilidad (ADR-002).

Registro estructurado y ordenado de cada evaluación de regla que produjo la
decisión: qué regla, con qué insumos, contra qué umbral, con qué resultado, y la
acción tomada ante dato faltante. Es lo que la capa MCP traduce a lenguaje
natural y la base de los golden-file tests (SAD §8.2).

Orden estable obligatorio: el rastro es comparable byte-a-byte entre corridas
(invariante de determinismo). Por eso se usan tuplas, no listas/sets.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ResultadoEvaluacionRegla(Enum):
    PASA = "PASA"
    FALLA = "FALLA"
    NA = "NA"  # dato no disponible; se registra la acción aplicada (ADR-009)


@dataclass(frozen=True, slots=True)
class EvaluacionRegla:
    """Resultado de evaluar UNA regla, con todo lo necesario para explicarla.

    Esqueleto de Fase 0: los campos se completan en Fase 1 cuando exista el AST y
    se rendericen las plantillas de explicación con valores/umbrales reales.
    """

    regla_id: str
    resultado: ResultadoEvaluacionRegla
    explicacion: str
    # TODO(Fase 1): valor_observado, umbral, fuente_dato, disponibilidad,
    # accion_ante_faltante, aporte_al_score.


@dataclass(frozen=True, slots=True)
class RastroDecision:
    """Secuencia ordenada e inmutable de evaluaciones de regla."""

    evaluaciones: tuple[EvaluacionRegla, ...]
