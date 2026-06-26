"""Plazo del crédito, en meses (entero positivo)."""

from __future__ import annotations

from dataclasses import dataclass

from domain.errores import ErrorValidacion


@dataclass(frozen=True, slots=True, order=True)
class Plazo:
    """Cantidad de meses. Positivo."""

    meses: int

    def __post_init__(self) -> None:
        if not isinstance(self.meses, int) or isinstance(self.meses, bool):
            raise ErrorValidacion("El plazo debe ser un entero de meses.")
        if self.meses <= 0:
            raise ErrorValidacion("El plazo debe ser positivo.")
