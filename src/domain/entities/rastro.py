"""RastroDecision + EvaluacionRegla. El artefacto de explicabilidad (ADR-002).

Registro estructurado y ordenado de cada evaluación de regla que produjo la
decisión: qué regla, con qué insumo, su disponibilidad, el valor observado, el
resultado, el aporte al score y la explicación legible. Es lo que la capa MCP
traduce a lenguaje natural y la base de los golden-file tests (SAD §8.2).

Orden estable obligatorio: el rastro es comparable byte-a-byte entre corridas
(invariante de determinismo). Por eso se usan tuplas, no listas/sets.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain.entities.predicado import ValorComparable
from domain.entities.regla import TipoRegla
from domain.value_objects.disponibilidad import Disponibilidad


class ResultadoEvaluacionRegla(Enum):
    PASA = "PASA"
    FALLA = "FALLA"
    NA = "NA"  # dato no disponible; se registra la acción aplicada (ADR-009)


@dataclass(frozen=True, slots=True)
class EvaluacionRegla:
    """Resultado de evaluar UNA regla, con todo lo necesario para explicarla."""

    regla_id: str
    tipo: TipoRegla
    resultado: ResultadoEvaluacionRegla
    fuente_dato: str
    disponibilidad: Disponibilidad
    valor_observado: ValorComparable | None
    aporte_score: int
    explicacion: str


@dataclass(frozen=True, slots=True)
class RastroDecision:
    """Secuencia ordenada e inmutable de evaluaciones de regla."""

    evaluaciones: tuple[EvaluacionRegla, ...]
