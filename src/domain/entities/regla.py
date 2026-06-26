"""Regla + Predicado (AST). El corazón configurable del motor (ADR-002).

Una `Regla` es DATO, no código (CLAUDE.md invariante 3). El predicado es un árbol
de expresión estructurado y serializable —jamás `eval()`— donde cada nodo conoce
campo/operador/umbral, lo que lo hace seguro, serializable y auto-explicable.

La unidad versionada es la `Politica`, no la `Regla` (ADR-003): el `id` de la
regla es procedencia, no llave de versión.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain.entities.predicado import Predicado
from domain.errores import ErrorValidacion


class Categoria(Enum):
    ELEGIBILIDAD = "ELEGIBILIDAD"
    CAPACIDAD_PAGO = "CAPACIDAD_PAGO"
    COMPORTAMIENTO = "COMPORTAMIENTO"
    FRAUDE = "FRAUDE"


class TipoRegla(Enum):
    HARD_STOP = "HARD_STOP"  # eliminatoria: si falla → RECHAZADO
    SCORING = "SCORING"  # aporta peso entero al score
    WARNING = "WARNING"  # no cambia el resultado; se marca en el rastro


class AnteDatoFaltante(Enum):
    """Comportamiento declarado de una regla cuando su `fuente_dato` no está
    disponible (ADR-009). El motor aplica esto en vez de asumir presencia."""

    TRATAR_COMO_FALLA = "TRATAR_COMO_FALLA"
    TRATAR_COMO_OK = "TRATAR_COMO_OK"
    FORZAR_REVISION = "FORZAR_REVISION"


@dataclass(frozen=True, slots=True)
class Regla:
    """Unidad declarativa de política. Dato dentro de una versión de `Politica`.

    El `predicado` es un AST (`domain.entities.predicado`): seguro, serializable y
    explicable. La evaluación de disponibilidad y scoring vive en el motor; la
    regla sólo declara su comportamiento (incluido `ante_dato_faltante`, ADR-009).
    """

    id: str  # estable entre versiones (procedencia, ADR-003)
    nombre: str
    categoria: Categoria
    tipo: TipoRegla
    predicado: Predicado
    fuente_dato: str  # qué insumo lee (trazabilidad)
    ante_dato_faltante: AnteDatoFaltante
    plantilla_explicacion: str  # "DTI {valor} supera el umbral {umbral}"
    peso: int | None = None  # ENTERO; sólo para tipo SCORING (sin float)

    def __post_init__(self) -> None:
        # Coherencia peso↔tipo (CASES.md CF-02): el peso existe sii es SCORING.
        if self.tipo is TipoRegla.SCORING:
            if not _es_peso_entero(self.peso):
                raise ErrorValidacion(
                    f"La regla SCORING '{self.id}' requiere un peso entero; recibió {self.peso!r}."
                )
        elif self.peso is not None:
            raise ErrorValidacion(
                f"La regla '{self.id}' de tipo {self.tipo.name} no debe declarar peso."
            )

    def campos_referenciados(self) -> frozenset[str]:
        """Delegado al AST (para validar fuente_dato contra el contrato, CF-03)."""
        return self.predicado.campos_referenciados()


def _es_peso_entero(peso: int | None) -> bool:
    return type(peso) is int
