"""Servidor MCP (stdio): `python -m interfaces.mcp.server` (DEPLOY.md).

Adaptador delgado sobre los casos de uso (ADR-005): SIN lógica de negocio. Por
defecto **read-only + simulación**; `evaluar_solicitud` (escritura) NO se expone
en el MVP (SAD §5.3). Las descripciones de cada herramienta son deliberadas: el
modelo las usa para elegir qué llamar. Los errores de dominio se traducen a
respuestas claras (no stack traces, CASES.md MC-01/MC-04). No se devuelve PII
(MC-02 · §8.1).
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from application.casos_uso.consultar_decision import ConsultarDecision
from application.casos_uso.explicar_decision import ExplicarDecision
from application.casos_uso.gestionar_reglas import GestionarReglas
from application.casos_uso.simular_cambio_regla import SimularCambioRegla
from domain.entities.decision_motor import DecisionMotor
from domain.entities.reporte_impacto import CriterioSimulacion, ReporteImpacto
from domain.errores import DecisionInexistente, ErrorDominio, ErrorValidacion, PoliticaInexistente
from infrastructure.di import crear_injector
from infrastructure.persistence.mapeo_politica import politica_desde_dict

mcp: FastMCP[Any] = FastMCP("veredicto")
_injector = crear_injector()


@mcp.tool
def consultar_decision(solicitud_id: str) -> dict[str, Any]:
    """Devuelve el resultado y el score de la decisión de crédito de una solicitud
    ya evaluada (por su idempotency_key). Sólo lectura."""
    try:
        decision = _injector.get(ConsultarDecision).ejecutar(solicitud_id)
    except DecisionInexistente as exc:
        return {"error": "no_encontrada", "detalle": str(exc)}
    return _decision_resumen(decision)


@mcp.tool
def explicar_decision(solicitud_id: str) -> dict[str, Any]:
    """Explica EN LENGUAJE NATURAL por qué se tomó la decisión de una solicitud:
    resultado, score y los motivos decisivos. No expone datos personales."""
    try:
        explicacion = _injector.get(ExplicarDecision).ejecutar(solicitud_id)
    except DecisionInexistente as exc:
        return {"error": "no_encontrada", "detalle": str(exc)}
    return {
        "resultado": explicacion.resultado.value,
        "score": explicacion.score,
        "motivos": list(explicacion.motivos),
    }


@mcp.tool
def rastro_auditoria(solicitud_id: str) -> dict[str, Any]:
    """Devuelve el rastro de auditoría COMPLETO de una decisión: cada regla
    evaluada, su resultado, aporte al score y explicación. Sólo lectura."""
    try:
        decision = _injector.get(ConsultarDecision).ejecutar(solicitud_id)
    except DecisionInexistente as exc:
        return {"error": "no_encontrada", "detalle": str(exc)}
    return {
        **_decision_resumen(decision),
        "rastro": [
            {
                "regla_id": e.regla_id,
                "tipo": e.tipo.value,
                "resultado": e.resultado.value,
                "fuente_dato": e.fuente_dato,
                "disponibilidad": e.disponibilidad.value,
                "aporte_score": e.aporte_score,
                "explicacion": e.explicacion,
            }
            for e in decision.rastro.evaluaciones
        ],
    }


@mcp.tool
def listar_reglas(producto: str = "consumo", version: int | None = None) -> dict[str, Any]:
    """Lista las reglas de una política: la vigente del producto, o una versión
    específica si se indica `version`. Sólo lectura."""
    gestor = _injector.get(GestionarReglas)
    try:
        politica = (
            gestor.obtener(producto, version)
            if version is not None
            else gestor.vigente(producto, "")
        )
    except PoliticaInexistente as exc:
        return {"error": "no_encontrada", "detalle": str(exc)}
    return {
        "politica_id": politica.id,
        "version": politica.version,
        "producto": politica.producto,
        "reglas": [
            {
                "id": r.id,
                "nombre": r.nombre,
                "categoria": r.categoria.value,
                "tipo": r.tipo.value,
                "fuente_dato": r.fuente_dato,
                "peso": r.peso,
            }
            for r in politica.reglas
        ],
    }


@mcp.tool
def simular_cambio_regla(
    politica_candidata: dict[str, Any],
    producto: str | None = None,
    limite: int | None = None,
) -> dict[str, Any]:
    """Simula el impacto de una política candidata sobre la población histórica de
    decisiones (what-if), SIN afectar producción. Devuelve flips, distribuciones y
    las reglas no evaluables sobre el histórico. `producto`/`limite` acotan."""
    try:
        candidata = politica_desde_dict(politica_candidata)
    except (ErrorValidacion, KeyError, TypeError, ValueError) as exc:
        # ValueError cubre enums inválidos (Categoria/TipoRegla/Resultado…): un
        # valor fuera del enum lanza ValueError al deserializar (MC-04).
        return {"error": "politica_mal_formada", "detalle": str(exc)}
    try:
        reporte = _injector.get(SimularCambioRegla).ejecutar(
            candidata, CriterioSimulacion(producto=producto, limite=limite)
        )
    except ErrorDominio as exc:
        return {"error": "dominio", "detalle": str(exc)}
    return _reporte_resumen(reporte)


def _decision_resumen(decision: DecisionMotor) -> dict[str, Any]:
    return {
        "resultado": decision.resultado.value,
        "score": decision.score,
        "politica_id": decision.politica_id,
        "politica_version": decision.politica_version,
    }


def _reporte_resumen(reporte: ReporteImpacto) -> dict[str, Any]:
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


def main() -> None:
    mcp.run()  # transporte stdio por defecto


if __name__ == "__main__":
    main()
