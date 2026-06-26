"""Insumos: contenedor de todo lo que el motor necesita para evaluar, con
presencia explícita por campo.

Es el ÚNICO canal de datos hacia el motor (ADR-006): la solicitud + el perfil de
buró as-seen + la disponibilidad de cada dato + el tiempo, todo como parámetro.
El motor no hace I/O ni lee el reloj.

Este contenedor es exactamente lo que se persiste como SNAPSHOT por decisión
(ADR-004): sin él, la simulación what-if no es fiel. La simulación reusa el
snapshot, nunca vuelve a llamar al buró (TROUBLESHOOTING.md).
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.entities.perfil_crediticio import PerfilCrediticio
from domain.entities.solicitud import Solicitud


@dataclass(frozen=True, slots=True)
class Insumos:
    """Snapshot completo de insumos as-seen para una evaluación.

    Esqueleto de Fase 0. En Fase 1 se define el "contrato de insumos": el conjunto
    cerrado de `fuente_dato` que las reglas pueden referenciar (valida CF-03), y
    el acceso uniforme `valor_y_disponibilidad(fuente_dato)` que usa el motor.
    """

    solicitud: Solicitud
    perfil: PerfilCrediticio
    # `momento_evaluacion` entra como dato explícito (sin datetime.now() en el
    # núcleo, ADR-006). ISO-8601 en Fase 0; tipo fecha en Fase 1.
    momento_evaluacion: str
