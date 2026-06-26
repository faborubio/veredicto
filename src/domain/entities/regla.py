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


# --- Predicado (AST) -------------------------------------------------------
#
# Esqueleto de Fase 0. El árbol se modela en Fase 1 como jerarquía de nodos
# inmutables y serializables, p.ej.:
#
#   Predicado (ABC)
#   ├── Comparacion(campo, operador, umbral)   # GT, GTE, LT, LTE, EQ, NEQ, IN
#   └── Combinacion(operador, ramas)           # AND, OR, NOT
#
# Cada nodo expone:
#   - evaluar(insumos) -> ResultadoEvaluacionNodo   (PURO, sin I/O)
#   - campos_referenciados() -> set[str]            (valida fuente_dato, CF-03)
#   - a_dict()/desde_dict()                         (serialización a DB/JSON)
#
# Se deja como marcador para no introducir un AST a medio diseñar en Fase 0.


@dataclass(frozen=True, slots=True)
class Regla:
    """Unidad declarativa de política. Dato dentro de una versión de `Politica`.

    Esqueleto de Fase 0: el campo `predicado` se tipa como `object` hasta que el
    AST exista en Fase 1; la evaluación vive en el motor, no aquí.
    """

    id: str  # estable entre versiones (procedencia, ADR-003)
    nombre: str
    categoria: Categoria
    tipo: TipoRegla
    predicado: object  # TODO(Fase 1): -> Predicado (AST)
    fuente_dato: str  # qué insumo lee (trazabilidad)
    ante_dato_faltante: AnteDatoFaltante
    plantilla_explicacion: str  # "DTI {valor} supera el umbral {umbral}"
    peso: int | None = None  # ENTERO; sólo para tipo SCORING (sin float)

    # TODO(Fase 1): validar que peso esté presente sii tipo == SCORING (CF-02),
    # y que sea entero.
