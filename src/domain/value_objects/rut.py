"""RUT chileno con validación de dígito verificador.

CASES.md EV-01: un RUT inválido debe rechazarse ANTES de entrar al motor, con
error tipado (`ErrorValidacion`). Es PII: ver §8.1 (pseudonimización al persistir).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Rut:
    """RUT normalizado (sin puntos, con dígito verificador).

    Esqueleto de Fase 0: la validación del dígito verificador (módulo 11) se
    implementa y testea en Fase 1 (CASES.md EV-01).
    """

    numero: int
    digito_verificador: str  # "0"-"9" o "K"

    # TODO(Fase 1):
    #   - constructor `desde_texto("12.345.678-5")` que normalice y valide.
    #   - cálculo módulo 11 del DV; ErrorValidacion si no coincide.
    #   - representación enmascarada para logs (no exponer PII completa, §8.1).
