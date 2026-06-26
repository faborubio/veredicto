"""Solicitud + Solicitante. La petición de crédito que entra al sistema.

Porta una `idempotency_key`: misma clave → misma decisión, sin duplicar
(CLAUDE.md invariante 8 · ADR-010). El RUT y la renta son PII (§8.1).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain.value_objects.monto import Monto
from domain.value_objects.plazo import Plazo
from domain.value_objects.rut import Rut


class SituacionLaboral(Enum):
    DEPENDIENTE = "DEPENDIENTE"
    INDEPENDIENTE = "INDEPENDIENTE"
    PENSIONADO = "PENSIONADO"


@dataclass(frozen=True, slots=True)
class Solicitante:
    """Datos del solicitante usados por la política de consumo v1."""

    rut: Rut
    ingreso_mensual: Monto
    situacion_laboral: SituacionLaboral


@dataclass(frozen=True, slots=True)
class Solicitud:
    """Petición de crédito. Inmutable: es un hecho que ocurrió."""

    idempotency_key: str
    solicitante: Solicitante
    producto: str
    monto: Monto
    plazo: Plazo
