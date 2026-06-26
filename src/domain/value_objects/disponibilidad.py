"""Disponibilidad de un insumo (ADR-009).

El motor nunca asume que un dato está presente. Cada insumo declara su estado;
cada regla declara cómo comportarse ante ausencia (`ante_dato_faltante`).
"""

from __future__ import annotations

from enum import Enum


class Disponibilidad(Enum):
    """Estado de presencia de un insumo, tal como se vio al decidir."""

    DISPONIBLE = "DISPONIBLE"
    NO_DISPONIBLE = "NO_DISPONIBLE"
    PARCIAL = "PARCIAL"
