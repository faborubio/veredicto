"""App FastAPI. Punto de entrada REST: `uvicorn interfaces.rest.app:app` (README).

Adaptador delgado sobre el caso de uso `EvaluarSolicitud` (ADR-005). Los DTOs de
request/response son Pydantic-para-HTTP y viven AQUÍ, nunca en el dominio
(TROUBLESHOOTING.md). El reloj se lee en este borde, no en el dominio (ADR-006).
Los errores de dominio tipados se traducen a códigos HTTP (invariante 12).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from application.casos_uso.evaluar_solicitud import EvaluarSolicitud
from domain.entities.decision_motor import DecisionMotor
from domain.entities.solicitud import SituacionLaboral, Solicitante, Solicitud
from domain.errores import ErrorDominio, ErrorValidacion
from domain.value_objects.monto import Monto
from domain.value_objects.plazo import Plazo
from domain.value_objects.rut import Rut
from infrastructure.di import crear_injector

app = FastAPI(title="Veredicto", version="0.1.0")
_injector = crear_injector()


class SolicitudIn(BaseModel):
    idempotency_key: str = Field(min_length=1)
    rut_numero: int
    rut_dv: str = Field(min_length=1, max_length=1)
    ingreso_mensual: int
    situacion_laboral: Literal["DEPENDIENTE", "INDEPENDIENTE", "PENSIONADO"]
    producto: str = "consumo"
    monto: int
    plazo: int


class EvaluacionOut(BaseModel):
    regla_id: str
    tipo: str
    resultado: str
    fuente_dato: str
    disponibilidad: str
    aporte_score: int
    explicacion: str


class DecisionOut(BaseModel):
    resultado: str
    score: int
    politica_id: str
    politica_version: int
    rastro: list[EvaluacionOut]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "fase": "1-motor"}


@app.post("/evaluaciones", response_model=DecisionOut)
def evaluar(payload: SolicitudIn) -> DecisionOut:
    try:
        solicitud = _a_solicitud(payload)
    except ErrorValidacion as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        decision = _injector.get(EvaluarSolicitud).ejecutar(solicitud, _ahora())
    except ErrorDominio as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return _a_salida(decision)


def _ahora() -> str:
    return datetime.now(UTC).isoformat()


def _a_solicitud(payload: SolicitudIn) -> Solicitud:
    solicitante = Solicitante(
        rut=Rut(payload.rut_numero, payload.rut_dv.upper()),
        ingreso_mensual=Monto(payload.ingreso_mensual),
        situacion_laboral=SituacionLaboral(payload.situacion_laboral),
    )
    return Solicitud(
        idempotency_key=payload.idempotency_key,
        solicitante=solicitante,
        producto=payload.producto,
        monto=Monto(payload.monto),
        plazo=Plazo(payload.plazo),
    )


def _a_salida(decision: DecisionMotor) -> DecisionOut:
    return DecisionOut(
        resultado=decision.resultado.value,
        score=decision.score,
        politica_id=decision.politica_id,
        politica_version=decision.politica_version,
        rastro=[
            EvaluacionOut(
                regla_id=e.regla_id,
                tipo=e.tipo.value,
                resultado=e.resultado.value,
                fuente_dato=e.fuente_dato,
                disponibilidad=e.disponibilidad.value,
                aporte_score=e.aporte_score,
                explicacion=e.explicacion,
            )
            for e in decision.rastro.evaluaciones
        ],
    )
