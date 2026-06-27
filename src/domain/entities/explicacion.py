"""Explicacion: resumen legible del porqué de una decisión (artefacto MCP).

Destila el rastro a los motivos que realmente determinaron el resultado, para que
Riesgo/Operaciones lo entiendan sin leer el rastro completo. Sin PII (§8.1): sólo
reglas, valores y umbrales — nunca RUT/identidad.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.entities.politica import ResultadoDecision


@dataclass(frozen=True, slots=True)
class Explicacion:
    resultado: ResultadoDecision
    score: int
    motivos: tuple[str, ...]
