"""Test e2e del endpoint de simulación (Fase 3): POST /simulaciones.

Puebla decisiones vía /evaluaciones y luego simula una política candidata sobre
ellas. Wiring por defecto (memoria).
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from infrastructure.persistence.mapeo_politica import politica_a_dict
from infrastructure.seed.politica_consumo import politica_consumo_v1
from interfaces.rest.app import app

_CLIENTE = TestClient(app)


def _evaluar(key: str) -> None:
    _CLIENTE.post(
        "/evaluaciones",
        json={
            "idempotency_key": key,
            "rut_numero": 11_111_111,
            "rut_dv": "1",
            "ingreso_mensual": 1_000_000,
            "situacion_laboral": "DEPENDIENTE",
            "producto": "consumo",
            "monto": 2_000_000,
            "plazo": 24,
        },
    )


def test_simular_devuelve_reporte_de_impacto() -> None:
    _evaluar("sim-1")
    _evaluar("sim-2")

    base = politica_a_dict(politica_consumo_v1())
    candidata: dict[str, Any] = {
        **base,
        "version": 99,
        "config_scoring": {
            **base["config_scoring"],
            "bandas": [
                {"umbral_min": 90, "resultado": "APROBADO"},
                {"umbral_min": 40, "resultado": "REVISION_MANUAL"},
                {"umbral_min": 0, "resultado": "RECHAZADO"},
            ],
        },
    }

    resp = _CLIENTE.post("/simulaciones", json=candidata)
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["total_evaluados"] >= 2
    assert "flips" in cuerpo
    assert "distribucion_candidata" in cuerpo
    # Los casos limpios (APROBADO con score 85) caen a revisión con umbral 90.
    assert cuerpo["distribucion_candidata"]["REVISION_MANUAL"] >= 2
