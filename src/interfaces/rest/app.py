"""App FastAPI. Punto de entrada REST: `uvicorn interfaces.rest.app:app` (README).

Adaptador delgado sobre el caso de uso `EvaluarSolicitud` (ADR-005). Los DTOs de
request/response son Pydantic-para-HTTP y viven AQUÍ, nunca en el dominio
(TROUBLESHOOTING.md). El reloj se lee en este borde, no en el dominio (ADR-006).
Los errores de dominio tipados se traducen a códigos HTTP (invariante 12).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel, Field

from application.casos_uso.evaluar_solicitud import EvaluarSolicitud
from application.casos_uso.gestionar_reglas import GestionarReglas
from application.casos_uso.simular_cambio_regla import SimularCambioRegla
from domain.entities.decision_motor import DecisionMotor
from domain.entities.reporte_impacto import ReporteImpacto
from domain.entities.solicitud import SituacionLaboral, Solicitante, Solicitud
from domain.errores import ErrorDominio, ErrorValidacion, PoliticaInexistente, PoliticaInvalida
from domain.value_objects.monto import Monto
from domain.value_objects.plazo import Plazo
from domain.value_objects.rut import Rut
from infrastructure.di import crear_injector
from infrastructure.persistence.mapeo_politica import politica_a_dict, politica_desde_dict

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


class ActivarIn(BaseModel):
    producto: str
    politica_id: str
    version: int
    actor: str


@app.get("/politicas/{producto}/vigente")
def politica_vigente(producto: str) -> dict[str, Any]:
    try:
        politica = _injector.get(GestionarReglas).vigente(producto, _ahora())
    except PoliticaInexistente as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return politica_a_dict(politica)


@app.get("/politicas/{producto}/{version}")
def politica_por_version(producto: str, version: int) -> dict[str, Any]:
    try:
        politica = _injector.get(GestionarReglas).obtener(producto, version)
    except PoliticaInexistente as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return politica_a_dict(politica)


@app.post("/politicas", status_code=201)
def crear_politica(payload: Annotated[dict[str, Any], Body()]) -> dict[str, str]:
    try:
        politica = politica_desde_dict(payload)
    except (ErrorValidacion, KeyError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=f"Política mal formada: {exc}") from exc
    try:
        _injector.get(GestionarReglas).crear_version(politica)
    except PoliticaInvalida as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"status": "creada", "id": politica.id, "version": str(politica.version)}


@app.post("/politicas/activar")
def activar_politica(payload: ActivarIn) -> dict[str, str]:
    try:
        evento = _injector.get(GestionarReglas).activar(
            payload.producto, payload.politica_id, payload.version, payload.actor, _ahora()
        )
    except PoliticaInexistente as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "status": "activada",
        "producto": evento.producto,
        "version": str(evento.politica_version),
        "actor": evento.actor,
        "momento": evento.momento,
    }


@app.post("/simulaciones")
def simular(payload: Annotated[dict[str, Any], Body()]) -> dict[str, Any]:
    """What-if: reevalúa la población histórica con una política candidata (draft).
    No valida la candidata como versión real: las reglas que leen datos no
    capturados se reportan como no evaluables (SI-02), no se rechazan."""
    try:
        candidata = politica_desde_dict(payload)
    except (ErrorValidacion, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=422, detail=f"Política candidata mal formada: {exc}"
        ) from exc
    reporte = _injector.get(SimularCambioRegla).ejecutar(candidata)
    return _reporte_a_dict(reporte)


def _reporte_a_dict(reporte: ReporteImpacto) -> dict[str, Any]:
    return {
        "total_evaluados": reporte.total_evaluados,
        "sin_cambio": reporte.sin_cambio,
        "flips": [
            {"desde": f.desde.value, "hacia": f.hacia.value, "cantidad": f.cantidad}
            for f in reporte.flips
        ],
        "distribucion_original": {r.value: n for r, n in reporte.distribucion_original},
        "distribucion_candidata": {r.value: n for r, n in reporte.distribucion_candidata},
        "reglas_no_evaluables": list(reporte.reglas_no_evaluables),
    }


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
