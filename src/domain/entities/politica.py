"""Politica + ConfiguracionScoring. La unidad atómica versionada e inmutable.

CLAUDE.md invariantes 4, 5 · ADR-003, ADR-008: editar = nueva versión completa.
Toda la semántica de decisión (pesos, método de agregación, bandas) vive como
DATO en la política; el motor sólo la interpreta. Fijar la versión de política
basta para reproducir una decisión.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain.entities.regla import Regla


class MetodoAgregacion(Enum):
    """Cómo se agregan los pesos de las reglas SCORING (ADR-008).

    Cambiar la semántica de agregación = un valor nuevo aquí, que queda
    versionado en la política. El intérprete debe soportar cada método que haya
    existido para reproducir decisiones viejas.
    """

    SUMA_PONDERADA = "SUMA_PONDERADA"


class ResultadoDecision(Enum):
    APROBADO = "APROBADO"
    REVISION_MANUAL = "REVISION_MANUAL"
    RECHAZADO = "RECHAZADO"


@dataclass(frozen=True, slots=True, order=True)
class Banda:
    """Umbral de banda de score → resultado. Comparación determinista `>=`
    sobre `umbral_min` (CASES.md EV-07)."""

    umbral_min: int
    resultado: ResultadoDecision


@dataclass(frozen=True, slots=True)
class ConfiguracionScoring:
    """La semántica de decisión como dato (ADR-008). Todo entero (ADR-006)."""

    metodo_agregacion: MetodoAgregacion
    score_maximo: int
    bandas: tuple[Banda, ...]  # tupla = inmutable y orden estable (determinismo)

    # TODO(Fase 1): validar bandas (cobertura sin huecos/solapes, ordenadas),
    # y que score_maximo sea coherente con la suma de pesos posibles (CF-02).


@dataclass(frozen=True, slots=True)
class Vigencia:
    """Ventana de vigencia. Fechas entran como dato explícito, no del reloj del
    motor (ADR-006). Se modelan como ISO-8601 en Fase 0; tipo fecha en Fase 1."""

    efectiva_desde: str
    efectiva_hasta: str | None = None


@dataclass(frozen=True, slots=True)
class Politica:
    """Colección versionada e inmutable de reglas + scoring + vigencia.

    UNIDAD ATÓMICA de versionado (ADR-003). Una decisión referencia exclusivamente
    (id, version) de la política.
    """

    id: str
    version: int
    producto: str
    reglas: tuple[Regla, ...]
    config_scoring: ConfiguracionScoring
    vigencia: Vigencia

    # TODO(Fase 1): validación de coherencia al construir (CF-01..CF-03):
    #   - todo `fuente_dato` referenciado existe en el contrato de Insumos.
    #   - pesos presentes sii SCORING; predicados bien formados.
    # Prohibida la mutación de una política ya usada en decisiones (CF-04):
    # la inmutabilidad (frozen) lo garantiza a nivel de objeto.
