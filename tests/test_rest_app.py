"""Test end-to-end de la REST mínima (Fase 1): POST /evaluaciones.

Usa el TestClient de FastAPI sobre la app real (con el injector cableado). Cierra
el entregable "evalúo una solicitud y obtengo decisión + por qué".
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from interfaces.rest.app import app

_CLIENTE = TestClient(app)


def _payload(rut_numero: int = 11_111_111, key: str = "rest-1") -> dict[str, object]:
    return {
        "idempotency_key": key,
        "rut_numero": rut_numero,
        "rut_dv": "1",
        "ingreso_mensual": 1_000_000,
        "situacion_laboral": "DEPENDIENTE",
        "producto": "consumo",
        "monto": 2_000_000,
        "plazo": 24,
    }


def test_health() -> None:
    assert _CLIENTE.get("/health").status_code == 200


def test_evaluacion_perfil_limpio_aprueba_con_rastro() -> None:
    resp = _CLIENTE.post("/evaluaciones", json=_payload())
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["resultado"] == "APROBADO"
    assert cuerpo["score"] == 85
    # El rastro explica el porqué: una entrada por regla.
    assert len(cuerpo["rastro"]) == 14
    assert all("explicacion" in e for e in cuerpo["rastro"])


def test_evaluacion_morosidad_rechaza() -> None:
    resp = _CLIENTE.post("/evaluaciones", json=_payload(rut_numero=22_222_222, key="rest-mor"))
    assert resp.status_code == 200
    assert resp.json()["resultado"] == "RECHAZADO"


def test_monto_invalido_devuelve_422() -> None:
    payload = _payload(key="rest-bad")
    payload["monto"] = -1  # Monto negativo → ErrorValidacion → 422
    resp = _CLIENTE.post("/evaluaciones", json=payload)
    assert resp.status_code == 422
