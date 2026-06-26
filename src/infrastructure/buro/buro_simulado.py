"""Adaptador del buró de crédito SIMULADO (implementa el puerto `GatewayBuro`).

Determinista, sin red, sin costo (SAD §3.3, §8.2). Mapea un RUT a un escenario de
perfil predefinido; el escenario por defecto es LIMPIO. Esto materializa el
requisito de "simulación de servicios de terceros" con fixtures por escenario.

Una indisponibilidad del buró (timeout, caída) se modela como un `PerfilCrediticio`
con `Disponibilidad.NO_DISPONIBLE` —no como excepción— para que el motor siga
siendo puro y nunca lance por datos del mundo real (ADR-006/009, CASES.md EV-04).
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum

from domain.entities.perfil_crediticio import PerfilCrediticio
from domain.value_objects.disponibilidad import Disponibilidad
from domain.value_objects.monto import Monto
from domain.value_objects.rut import Rut


class EscenarioBuro(Enum):
    LIMPIO = "LIMPIO"
    MOROSIDAD_VIGENTE = "MOROSIDAD_VIGENTE"
    DEUDAS_CASTIGADAS = "DEUDAS_CASTIGADAS"
    THIN_FILE = "THIN_FILE"  # sin historial → meses_historial NO_DISPONIBLE (EV-02)
    NO_DISPONIBLE = "NO_DISPONIBLE"  # buró caído/timeout (EV-04)


def perfil_de_escenario(escenario: EscenarioBuro) -> PerfilCrediticio:
    if escenario is EscenarioBuro.LIMPIO:
        return PerfilCrediticio(
            disponibilidad=Disponibilidad.DISPONIBLE,
            deuda_total=Monto(300_000),
            tiene_morosidad_vigente=False,
            tiene_deudas_castigadas=False,
            meses_historial=36,
        )
    if escenario is EscenarioBuro.MOROSIDAD_VIGENTE:
        return PerfilCrediticio(
            disponibilidad=Disponibilidad.DISPONIBLE,
            deuda_total=Monto(2_000_000),
            tiene_morosidad_vigente=True,
            tiene_deudas_castigadas=False,
            meses_historial=24,
        )
    if escenario is EscenarioBuro.DEUDAS_CASTIGADAS:
        return PerfilCrediticio(
            disponibilidad=Disponibilidad.DISPONIBLE,
            deuda_total=Monto(1_200_000),
            tiene_morosidad_vigente=False,
            tiene_deudas_castigadas=True,
            meses_historial=48,
        )
    if escenario is EscenarioBuro.THIN_FILE:
        return PerfilCrediticio(
            disponibilidad=Disponibilidad.DISPONIBLE,
            deuda_total=Monto(0),
            tiene_morosidad_vigente=False,
            tiene_deudas_castigadas=False,
            meses_historial=None,  # sin historial
        )
    # NO_DISPONIBLE: el buró no respondió; nada se sabe.
    return PerfilCrediticio(
        disponibilidad=Disponibilidad.NO_DISPONIBLE,
        deuda_total=None,
        tiene_morosidad_vigente=None,
        tiene_deudas_castigadas=None,
        meses_historial=None,
    )


# RUTs de demostración → escenario (para REST/MCP y tests).
ESCENARIOS_DEMO: dict[int, EscenarioBuro] = {
    11_111_111: EscenarioBuro.LIMPIO,
    22_222_222: EscenarioBuro.MOROSIDAD_VIGENTE,
    33_333_333: EscenarioBuro.DEUDAS_CASTIGADAS,
    44_444_444: EscenarioBuro.THIN_FILE,
    55_555_555: EscenarioBuro.NO_DISPONIBLE,
}


class BuroSimulado:
    """Buró simulado por escenario. Implementa `GatewayBuro` estructuralmente."""

    def __init__(
        self,
        escenarios_por_rut: Mapping[int, EscenarioBuro] | None = None,
        escenario_default: EscenarioBuro = EscenarioBuro.LIMPIO,
    ) -> None:
        self._mapa = dict(escenarios_por_rut or {})
        self._default = escenario_default

    def obtener_perfil(self, rut: Rut) -> PerfilCrediticio:
        return perfil_de_escenario(self._mapa.get(rut.numero, self._default))
