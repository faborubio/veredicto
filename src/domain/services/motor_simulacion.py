"""MotorSimulacion: replay de una política candidata contra población histórica.

PURO (ADR-006): reusa los SNAPSHOTS de insumos guardados, NUNCA vuelve a llamar al
buró (reproducibilidad; TROUBLESHOOTING.md). No persiste nada (CASES.md SI-04):
es lectura + cómputo. Construido sobre el `MotorEvaluacion` estable.

Límite honesto (SAD §6.2 · CASES.md SI-02): una regla candidata que lee un
`fuente_dato` ausente del contrato de los snapshots se marca "no evaluable sobre el
histórico" y se reporta; nunca se inventa un valor. El impacto se calcula sobre el
subconjunto evaluable, con el caveat explícito en el reporte.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import replace

from domain.entities.insumos import CAMPOS_INSUMO
from domain.entities.politica import Politica, ResultadoDecision
from domain.entities.reporte_impacto import CasoHistorico, Flip, ReporteImpacto
from domain.services.motor_evaluacion import MotorEvaluacion

# Orden estable de resultados para salidas deterministas (no depende de los datos).
_ORDEN_RESULTADOS: tuple[ResultadoDecision, ...] = tuple(ResultadoDecision)


class MotorSimulacion:
    def __init__(self, motor: MotorEvaluacion | None = None) -> None:
        self._motor = motor if motor is not None else MotorEvaluacion()

    def simular(
        self,
        casos: Iterable[CasoHistorico],
        politica_candidata: Politica,
    ) -> ReporteImpacto:
        no_evaluables = self._reglas_no_evaluables(politica_candidata)
        politica = self._sin_reglas(politica_candidata, no_evaluables)

        conteo_original: Counter[ResultadoDecision] = Counter()
        conteo_candidata: Counter[ResultadoDecision] = Counter()
        flips: Counter[tuple[ResultadoDecision, ResultadoDecision]] = Counter()
        sin_cambio = 0
        total = 0

        for caso in casos:
            total += 1
            candidata = self._motor.evaluar(caso.snapshot, politica).resultado
            conteo_original[caso.resultado_original] += 1
            conteo_candidata[candidata] += 1
            if candidata == caso.resultado_original:
                sin_cambio += 1
            else:
                flips[(caso.resultado_original, candidata)] += 1

        return ReporteImpacto(
            total_evaluados=total,
            sin_cambio=sin_cambio,
            flips=tuple(
                Flip(desde, hacia, flips[(desde, hacia)])
                for desde in _ORDEN_RESULTADOS
                for hacia in _ORDEN_RESULTADOS
                if desde != hacia and flips[(desde, hacia)] > 0
            ),
            distribucion_original=self._distribucion(conteo_original),
            distribucion_candidata=self._distribucion(conteo_candidata),
            reglas_no_evaluables=tuple(sorted(no_evaluables)),
        )

    @staticmethod
    def _reglas_no_evaluables(politica: Politica) -> set[str]:
        """Reglas cuyo predicado lee campos fuera del contrato capturado (SI-02)."""
        return {
            regla.id
            for regla in politica.reglas
            if not (regla.campos_referenciados() <= CAMPOS_INSUMO)
        }

    @staticmethod
    def _sin_reglas(politica: Politica, ids_excluidos: set[str]) -> Politica:
        if not ids_excluidos:
            return politica
        reglas = tuple(r for r in politica.reglas if r.id not in ids_excluidos)
        return replace(politica, reglas=reglas)

    @staticmethod
    def _distribucion(
        conteo: Counter[ResultadoDecision],
    ) -> tuple[tuple[ResultadoDecision, int], ...]:
        return tuple((resultado, conteo[resultado]) for resultado in _ORDEN_RESULTADOS)
