"""PerfilCrediticio: datos del buró, tal como se vieron (as-seen).

Puede venir ausente o parcial (ADR-009): el buró falla, no hay historial
(*thin file*, CASES.md EV-02), o los ingresos no son verificables. Cada campo
porta su `Disponibilidad`. Este perfil entra al motor como dato ya resuelto;
el motor nunca llama al buró (ADR-006).
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.value_objects.disponibilidad import Disponibilidad
from domain.value_objects.monto import Monto


@dataclass(frozen=True, slots=True)
class PerfilCrediticio:
    """Snapshot del perfil del buró usado en una evaluación.

    Esqueleto de Fase 0: campos representativos del dominio chileno. Se afina con
    los fixtures de escenarios de buró en Fase 1 (SAD §8.2: perfil limpio, con
    morosidad vigente, thin file, ingresos no verificables, deudas castigadas).
    """

    disponibilidad: Disponibilidad
    deuda_total: Monto | None = None
    tiene_morosidad_vigente: bool | None = None
    tiene_deudas_castigadas: bool | None = None
    meses_historial: int | None = None  # None / 0 → thin file (EV-02)
