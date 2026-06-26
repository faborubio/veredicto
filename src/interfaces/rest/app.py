"""App FastAPI. Punto de entrada REST: `uvicorn interfaces.rest.app:app` (README).

Esqueleto de Fase 0: sólo un endpoint de salud para verificar el arranque. Los
endpoints de evaluación/consulta/gestión se agregan en Fase 1+ como adaptadores
delgados sobre los casos de uso.
"""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="Veredicto", version="0.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "fase": "0-scaffolding"}
