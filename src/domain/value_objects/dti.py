"""DTI (debt-to-income): ratio deuda/ingreso en puntos básicos (entero).

Se modela en puntos básicos enteros (1% = 100 bps) para evitar `float` en el
núcleo (ADR-006). Ej.: DTI 45% → 4500 bps.

CASES.md EV-03: si el ingreso es 0/nulo, el DTI es indefinido → no se calcula un
ratio (no hay división por cero); la regla correspondiente actúa como hard-stop
con razón clara. El cálculo y ese borde se implementan en Fase 1.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.errores import ErrorValidacion


@dataclass(frozen=True, slots=True, order=True)
class Dti:
    """Ratio deuda/ingreso en puntos básicos enteros. No negativo."""

    puntos_basicos: int

    def __post_init__(self) -> None:
        if not isinstance(self.puntos_basicos, int) or isinstance(self.puntos_basicos, bool):
            raise ErrorValidacion("El DTI debe expresarse en puntos básicos enteros, sin float.")
        if self.puntos_basicos < 0:
            raise ErrorValidacion("El DTI no puede ser negativo.")

    # TODO(Fase 1): constructor `desde_deuda_ingreso(Monto, Monto)` que devuelva
    # None / marque indefinido cuando el ingreso es 0 (EV-03), sin lanzar.
