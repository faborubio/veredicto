"""Puerto del buró de crédito. El adaptador simulado vive en infrastructure/buro.

El gateway hace la I/O (puede fallar/timeout, CASES.md EV-04); el caso de uso
traduce su salida a un `PerfilCrediticio` as-seen antes de entrar al motor, de
modo que el motor permanezca puro (ADR-006).
"""

from __future__ import annotations

from typing import Protocol

from domain.entities.perfil_crediticio import PerfilCrediticio
from domain.value_objects.rut import Rut


class GatewayBuro(Protocol):
    def obtener_perfil(self, rut: Rut) -> PerfilCrediticio:
        """Devuelve el perfil as-seen. Una indisponibilidad del buró se modela
        como `PerfilCrediticio` con `Disponibilidad.NO_DISPONIBLE`, no como
        excepción que rompa la pureza del motor."""
        ...
