"""Insumos: contenedor de todo lo que el motor necesita, con presencia explícita.

Es el ÚNICO canal de datos hacia el motor (ADR-006): solicitud + perfil de buró
as-seen + disponibilidad por dato + tiempo, todo como parámetro. El motor no hace
I/O ni lee el reloj.

Define además el **CONTRATO DE INSUMOS**: el conjunto cerrado de `fuente_dato` que
las reglas pueden referenciar (`CAMPOS_INSUMO`). Toda regla cuyo predicado lea un
campo fuera de este conjunto es inválida (CASES.md CF-03).

El acceso uniforme `valor_y_disponibilidad(campo)` devuelve, por campo, su estado
de disponibilidad y su valor as-seen. Aquí vive la derivación del DTI y el manejo
del ingreso cero (EV-03): nunca hay división por cero; el DTI queda NO_DISPONIBLE.

Este contenedor es exactamente lo que se persiste como SNAPSHOT por decisión
(ADR-004): sin él la simulación what-if no es fiel.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.entities.perfil_crediticio import PerfilCrediticio
from domain.entities.predicado import ValorComparable
from domain.entities.solicitud import Solicitud
from domain.errores import ErrorValidacion
from domain.value_objects.disponibilidad import Disponibilidad

# Contrato cerrado: las reglas SÓLO pueden leer estos campos (CF-03).
CAMPOS_INSUMO: frozenset[str] = frozenset(
    {
        "monto",
        "plazo",
        "ingreso_mensual",
        "situacion_laboral",
        "dti",
        "tiene_morosidad_vigente",
        "tiene_deudas_castigadas",
        "meses_historial",
    }
)

# Base de puntos básicos para el DTI: 10000 bps = 100%.
_BPS = 10_000


@dataclass(frozen=True, slots=True)
class Insumos:
    """Snapshot completo de insumos as-seen para una evaluación."""

    solicitud: Solicitud
    perfil: PerfilCrediticio
    # `momento_evaluacion` entra como dato explícito (sin datetime.now() en el
    # núcleo, ADR-006). ISO-8601 en Fase 1; tipo fecha en una fase futura.
    momento_evaluacion: str

    def valor_y_disponibilidad(self, campo: str) -> tuple[Disponibilidad, ValorComparable | None]:
        """Acceso uniforme por nombre de campo del contrato. Lanza si el campo no
        pertenece al contrato (error de configuración, no de negocio)."""
        if campo == "monto":
            return Disponibilidad.DISPONIBLE, self.solicitud.monto.pesos
        if campo == "plazo":
            return Disponibilidad.DISPONIBLE, self.solicitud.plazo.meses
        if campo == "ingreso_mensual":
            return Disponibilidad.DISPONIBLE, self.solicitud.solicitante.ingreso_mensual.pesos
        if campo == "situacion_laboral":
            return Disponibilidad.DISPONIBLE, self.solicitud.solicitante.situacion_laboral.value
        if campo == "dti":
            return self._dti_bps()
        if campo == "tiene_morosidad_vigente":
            return self._campo_buro(self.perfil.tiene_morosidad_vigente)
        if campo == "tiene_deudas_castigadas":
            return self._campo_buro(self.perfil.tiene_deudas_castigadas)
        if campo == "meses_historial":
            return self._campo_buro(self.perfil.meses_historial)
        raise ErrorValidacion(f"Campo '{campo}' no pertenece al contrato de insumos (CF-03).")

    def _dti_bps(self) -> tuple[Disponibilidad, int | None]:
        """DTI en puntos básicos enteros = deuda_total / ingreso (ADR-006, sin
        float). Indefinido (NO_DISPONIBLE) si falta la deuda del buró o el ingreso
        es 0 — evita división por cero (EV-03).

        Nota de modelado: en un motor real esto sería carga financiera
        (cuota/ingreso); aquí usamos deuda/ingreso. Es refinable vía nueva versión
        de política (ADR-003)."""
        if self.perfil.disponibilidad is Disponibilidad.NO_DISPONIBLE:
            return Disponibilidad.NO_DISPONIBLE, None
        if self.perfil.deuda_total is None:
            return Disponibilidad.NO_DISPONIBLE, None
        ingreso = self.solicitud.solicitante.ingreso_mensual.pesos
        if ingreso <= 0:
            return Disponibilidad.NO_DISPONIBLE, None
        return Disponibilidad.DISPONIBLE, self.perfil.deuda_total.pesos * _BPS // ingreso

    def _campo_buro(
        self, valor: ValorComparable | None
    ) -> tuple[Disponibilidad, ValorComparable | None]:
        """Un campo proveniente del buró está disponible sólo si el perfil lo está
        y el valor concreto no es None (perfil PARCIAL puede traer unos sí y otros
        no)."""
        if self.perfil.disponibilidad is Disponibilidad.NO_DISPONIBLE or valor is None:
            return Disponibilidad.NO_DISPONIBLE, None
        return Disponibilidad.DISPONIBLE, valor
