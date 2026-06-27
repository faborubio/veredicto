"""ExplicarDecision: renderiza el rastro a razones legibles (lectura).

Envuelta por la herramienta MCP `explicar_decision`. Aplica minimización de PII:
devuelve sólo lo necesario para explicar (reglas/valores), nunca PII completa
(CASES.md MC-02 · §8.1). Destila los motivos DECISIVOS según el resultado.
"""

from __future__ import annotations

from domain.entities.decision_motor import DecisionMotor
from domain.entities.explicacion import Explicacion
from domain.entities.politica import ResultadoDecision
from domain.entities.rastro import ResultadoEvaluacionRegla
from domain.entities.regla import TipoRegla
from domain.errores import DecisionInexistente
from domain.ports.repositorio_decisiones import RepositorioDecisiones


class ExplicarDecision:
    def __init__(self, decisiones: RepositorioDecisiones) -> None:
        self._decisiones = decisiones

    def ejecutar(self, solicitud_id: str) -> Explicacion:
        decision = self._decisiones.por_solicitud(solicitud_id)
        if decision is None:
            raise DecisionInexistente(f"No existe decisión para la solicitud '{solicitud_id}'.")
        return Explicacion(
            resultado=decision.resultado,
            score=decision.score,
            motivos=_motivos_decisivos(decision),
        )


def _motivos_decisivos(decision: DecisionMotor) -> tuple[str, ...]:
    """Selecciona las explicaciones de las reglas que determinaron el resultado:
    hard-stops que fallaron (rechazo), datos faltantes que forzaron revisión, o
    los aportes positivos (aprobación). Si nada destaca, devuelve todo el rastro."""
    evaluaciones = decision.rastro.evaluaciones
    if decision.resultado is ResultadoDecision.RECHAZADO:
        relevantes = [
            e
            for e in evaluaciones
            if e.tipo is TipoRegla.HARD_STOP and e.resultado is ResultadoEvaluacionRegla.FALLA
        ]
    elif decision.resultado is ResultadoDecision.REVISION_MANUAL:
        relevantes = [e for e in evaluaciones if e.resultado is ResultadoEvaluacionRegla.NA]
    else:  # APROBADO
        relevantes = [e for e in evaluaciones if e.aporte_score > 0]

    if not relevantes:
        relevantes = list(evaluaciones)
    return tuple(e.explicacion for e in relevantes)
