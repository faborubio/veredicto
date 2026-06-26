"""Solicitud + Solicitante. La petición de crédito que entra al sistema.

Porta una `idempotency_key`: misma clave → misma decisión, sin duplicar
(CLAUDE.md invariante 8 · ADR-010). El RUT es PII (§8.1).
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.value_objects.monto import Monto
from domain.value_objects.plazo import Plazo
from domain.value_objects.rut import Rut


@dataclass(frozen=True, slots=True)
class Solicitante:
    """Datos del solicitante. Esqueleto de Fase 0."""

    rut: Rut
    # TODO(Fase 1): situacion_laboral (DEPENDIENTE/INDEPENDIENTE), ingreso
    # declarado (Monto), antigüedad, etc. — alineados con las reglas reales.


@dataclass(frozen=True, slots=True)
class Solicitud:
    """Petición de crédito. Inmutable: es un hecho que ocurrió."""

    idempotency_key: str
    solicitante: Solicitante
    producto: str
    monto: Monto
    plazo: Plazo
