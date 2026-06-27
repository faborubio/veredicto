"""Test e2e de la API de gestión de políticas (Fase 2): configurabilidad sin desplegar.

Demuestra el entregable: crear nueva versión → la vigente sigue siendo la vieja →
activar → la vigente cambia. Y que una política inválida se rechaza con 422.
Usa el wiring por defecto (memoria), sin BD.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from infrastructure.persistence.mapeo_politica import politica_a_dict
from infrastructure.seed.politica_consumo import politica_consumo_v1
from interfaces.rest.app import app

_CLIENTE = TestClient(app)


def test_get_politica_vigente() -> None:
    resp = _CLIENTE.get("/politicas/consumo/vigente")
    assert resp.status_code == 200
    assert resp.json()["version"] == 1


def test_crear_y_activar_cambia_la_vigente() -> None:
    base = politica_a_dict(politica_consumo_v1())
    v2: dict[str, Any] = {
        **base,
        "version": 2,
        "config_scoring": {**base["config_scoring"], "score_maximo": 120},
    }

    assert _CLIENTE.post("/politicas", json=v2).status_code == 201
    # La vigente sigue siendo la v1 (crear no activa).
    assert _CLIENTE.get("/politicas/consumo/vigente").json()["version"] == 1

    activar = {"producto": "consumo", "politica_id": "consumo", "version": 2, "actor": "riesgo"}
    assert _CLIENTE.post("/politicas/activar", json=activar).status_code == 200
    # Ahora la vigente es la v2; la v1 sigue recuperable (inmutable).
    assert _CLIENTE.get("/politicas/consumo/vigente").json()["version"] == 2
    assert _CLIENTE.get("/politicas/consumo/1").json()["config_scoring"]["score_maximo"] == 100


def test_crear_politica_invalida_devuelve_422() -> None:
    base = politica_a_dict(politica_consumo_v1())
    reglas = [dict(r) for r in base["reglas"]]
    reglas[0] = {
        **reglas[0],
        "fuente_dato": "campo_inexistente",
        "predicado": {
            "tipo": "comparacion",
            "campo": "campo_inexistente",
            "comparador": "GT",
            "valor": 1,
        },
    }
    mala: dict[str, Any] = {**base, "version": 3, "reglas": reglas}
    assert _CLIENTE.post("/politicas", json=mala).status_code == 422
