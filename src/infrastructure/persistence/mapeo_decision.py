"""Traducción entidad↔fila para `DecisionMotor` y el SNAPSHOT de `Insumos`.

Round-trip exacto dominio → JSONB → dominio. El snapshot captura los insumos tal
como se vieron (ADR-004): solicitud + perfil de buró + disponibilidad implícita en
los valores. Reconstruir desde el snapshot reproduce la decisión sin volver a
llamar al buró (clave para la simulación de Fase 3).
"""

from __future__ import annotations

from typing import Any

from domain.entities.decision_motor import DecisionMotor
from domain.entities.insumos import Insumos
from domain.entities.perfil_crediticio import PerfilCrediticio
from domain.entities.politica import ResultadoDecision
from domain.entities.rastro import EvaluacionRegla, RastroDecision, ResultadoEvaluacionRegla
from domain.entities.regla import TipoRegla
from domain.entities.solicitud import SituacionLaboral, Solicitante, Solicitud
from domain.value_objects.disponibilidad import Disponibilidad
from domain.value_objects.monto import Monto
from domain.value_objects.plazo import Plazo
from domain.value_objects.rut import Rut
from infrastructure.persistence.modelos import DecisionORM

# --- Rastro ----------------------------------------------------------------


def _evaluacion_a_dict(e: EvaluacionRegla) -> dict[str, Any]:
    return {
        "regla_id": e.regla_id,
        "tipo": e.tipo.value,
        "resultado": e.resultado.value,
        "fuente_dato": e.fuente_dato,
        "disponibilidad": e.disponibilidad.value,
        "valor_observado": e.valor_observado,
        "aporte_score": e.aporte_score,
        "explicacion": e.explicacion,
    }


def _evaluacion_desde_dict(d: dict[str, Any]) -> EvaluacionRegla:
    return EvaluacionRegla(
        regla_id=d["regla_id"],
        tipo=TipoRegla(d["tipo"]),
        resultado=ResultadoEvaluacionRegla(d["resultado"]),
        fuente_dato=d["fuente_dato"],
        disponibilidad=Disponibilidad(d["disponibilidad"]),
        valor_observado=d["valor_observado"],
        aporte_score=d["aporte_score"],
        explicacion=d["explicacion"],
    )


def _rastro_a_lista(rastro: RastroDecision) -> list[dict[str, Any]]:
    return [_evaluacion_a_dict(e) for e in rastro.evaluaciones]


def _rastro_desde_lista(lista: list[dict[str, Any]]) -> RastroDecision:
    return RastroDecision(tuple(_evaluacion_desde_dict(d) for d in lista))


# --- Snapshot de insumos ---------------------------------------------------


def _insumos_a_dict(insumos: Insumos) -> dict[str, Any]:
    s = insumos.solicitud
    p = insumos.perfil
    return {
        "solicitud": {
            "idempotency_key": s.idempotency_key,
            "producto": s.producto,
            "monto": s.monto.pesos,
            "plazo": s.plazo.meses,
            "solicitante": {
                "rut_numero": s.solicitante.rut.numero,
                "rut_dv": s.solicitante.rut.digito_verificador,
                "ingreso_mensual": s.solicitante.ingreso_mensual.pesos,
                "situacion_laboral": s.solicitante.situacion_laboral.value,
            },
        },
        "perfil": {
            "disponibilidad": p.disponibilidad.value,
            "deuda_total": p.deuda_total.pesos if p.deuda_total is not None else None,
            "tiene_morosidad_vigente": p.tiene_morosidad_vigente,
            "tiene_deudas_castigadas": p.tiene_deudas_castigadas,
            "meses_historial": p.meses_historial,
        },
        "momento_evaluacion": insumos.momento_evaluacion,
    }


def _insumos_desde_dict(d: dict[str, Any]) -> Insumos:
    sol = d["solicitud"]
    slt = sol["solicitante"]
    perfil = d["perfil"]
    solicitante = Solicitante(
        rut=Rut(slt["rut_numero"], slt["rut_dv"]),
        ingreso_mensual=Monto(slt["ingreso_mensual"]),
        situacion_laboral=SituacionLaboral(slt["situacion_laboral"]),
    )
    solicitud = Solicitud(
        idempotency_key=sol["idempotency_key"],
        solicitante=solicitante,
        producto=sol["producto"],
        monto=Monto(sol["monto"]),
        plazo=Plazo(sol["plazo"]),
    )
    deuda = perfil["deuda_total"]
    perfil_crediticio = PerfilCrediticio(
        disponibilidad=Disponibilidad(perfil["disponibilidad"]),
        deuda_total=Monto(deuda) if deuda is not None else None,
        tiene_morosidad_vigente=perfil["tiene_morosidad_vigente"],
        tiene_deudas_castigadas=perfil["tiene_deudas_castigadas"],
        meses_historial=perfil["meses_historial"],
    )
    return Insumos(
        solicitud=solicitud,
        perfil=perfil_crediticio,
        momento_evaluacion=d["momento_evaluacion"],
    )


# --- DecisionMotor + snapshot ---------------------------------------------


def decision_a_orm(idempotency_key: str, decision: DecisionMotor, snapshot: Insumos) -> DecisionORM:
    return DecisionORM(
        idempotency_key=idempotency_key,
        politica_id=decision.politica_id,
        politica_version=decision.politica_version,
        resultado=decision.resultado.value,
        score=decision.score,
        rastro=_rastro_a_lista(decision.rastro),
        snapshot=_insumos_a_dict(snapshot),
    )


def decision_desde_orm(orm: DecisionORM) -> DecisionMotor:
    return DecisionMotor(
        politica_id=orm.politica_id,
        politica_version=orm.politica_version,
        resultado=ResultadoDecision(orm.resultado),
        score=orm.score,
        rastro=_rastro_desde_lista(orm.rastro),
    )


def snapshot_desde_orm(orm: DecisionORM) -> Insumos:
    return _insumos_desde_dict(orm.snapshot)
