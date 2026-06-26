"""Monto en pesos chilenos (CLP), entero, type-safe.

CLAUDE.md invariante 1 · SAD §2.3: el dinero se modela como entero en CLP, sin
decimales, con un value object que impide usar `float`. Sin operaciones que
introduzcan flotantes en el núcleo.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.errores import ErrorValidacion


@dataclass(frozen=True, slots=True, order=True)
class Monto:
    """Cantidad entera de CLP. No negativa."""

    pesos: int

    def __post_init__(self) -> None:
        if not isinstance(self.pesos, int) or isinstance(self.pesos, bool):
            raise ErrorValidacion("El monto debe ser un entero de pesos (CLP), sin float.")
        if self.pesos < 0:
            raise ErrorValidacion("El monto no puede ser negativo.")

    # TODO(Fase 1): aritmética type-safe (suma/resta que devuelvan Monto),
    # comparación contra rangos de producto (CASES.md EV-05).
