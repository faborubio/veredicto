"""Test de contrato de las herramientas MCP (Fase 4).

Verifica que cada herramienta delega en el caso de uso correcto y traduce los
errores de dominio a respuestas claras (MC-01 inexistente, MC-04 mal formada),
sin exponer PII (MC-02) ni herramientas de escritura (MC-03: no existe tool de
evaluación). Pobla el estado vía el injector del propio servidor (memoria).
"""

from __future__ import annotations

import asyncio
from typing import Any

from application.casos_uso.evaluar_solicitud import EvaluarSolicitud
from domain.entities.solicitud import SituacionLaboral, Solicitante, Solicitud
from domain.value_objects.monto import Monto
from domain.value_objects.plazo import Plazo
from domain.value_objects.rut import Rut, calcular_dv
from infrastructure.persistence.mapeo_politica import politica_a_dict
from infrastructure.seed.politica_consumo import politica_consumo_v1
from interfaces.mcp import server

_MOMENTO = "2026-06-26T00:00:00+00:00"
_POLITICA_DICT: dict[str, Any] = politica_a_dict(politica_consumo_v1())


def _solicitud(key: str, rut_numero: int = 11_111_111) -> Solicitud:
    rut = Rut(rut_numero, calcular_dv(rut_numero))
    solicitante = Solicitante(rut, Monto(1_000_000), SituacionLaboral.DEPENDIENTE)
    return Solicitud(key, solicitante, "consumo", Monto(2_000_000), Plazo(24))


def _evaluar(key: str, rut_numero: int = 11_111_111) -> None:
    server._injector.get(EvaluarSolicitud).ejecutar(_solicitud(key, rut_numero), _MOMENTO)


def test_consultar_decision_existente() -> None:
    _evaluar("mcp-ok")
    res = server.consultar_decision("mcp-ok")
    assert res["resultado"] == "APROBADO"
    assert "rut" not in res  # sin PII (MC-02)


def test_consultar_inexistente_respuesta_clara() -> None:
    res = server.consultar_decision("no-existe-jamas")
    assert res["error"] == "no_encontrada"  # MC-01: no stack trace


def test_explicar_decision_da_motivos() -> None:
    _evaluar("mcp-exp")
    res = server.explicar_decision("mcp-exp")
    assert res["resultado"] == "APROBADO"
    assert len(res["motivos"]) > 0


def test_rastro_auditoria_completo() -> None:
    _evaluar("mcp-rastro")
    res = server.rastro_auditoria("mcp-rastro")
    assert len(res["rastro"]) == 14  # una entrada por regla


def test_listar_reglas_vigente() -> None:
    res = server.listar_reglas("consumo")
    assert res["version"] == 1
    assert len(res["reglas"]) == 14


def test_simular_cambio_regla_reporta() -> None:
    _evaluar("mcp-sim-1")
    reporte = server.simular_cambio_regla(_POLITICA_DICT)
    assert "total_evaluados" in reporte
    assert "flips" in reporte
    assert "distribucion_candidata" in reporte


def test_simular_politica_mal_formada() -> None:
    res = server.simular_cambio_regla({"basura": 1})
    assert res["error"] == "politica_mal_formada"  # MC-04 (falta estructural → KeyError)


def test_simular_politica_enum_invalido() -> None:
    # MC-04: política estructuralmente completa pero con un enum inválido. El
    # deserializador lanza ValueError; el adaptador debe enmascararlo, no reventar.
    corrupta = {**_POLITICA_DICT, "reglas": list(_POLITICA_DICT["reglas"])}
    corrupta["reglas"][0] = {**corrupta["reglas"][0], "categoria": "BASURA"}
    res = server.simular_cambio_regla(corrupta)
    assert res["error"] == "politica_mal_formada"


def test_solo_se_exponen_las_cinco_tools_read_only() -> None:
    # MC-03 (invariante #11): el set de herramientas REGISTRADAS en FastMCP es
    # exactamente las 5 de lectura/simulación. Nada de escritura por ningún nombre.
    registradas = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert registradas == {
        "consultar_decision",
        "explicar_decision",
        "rastro_auditoria",
        "listar_reglas",
        "simular_cambio_regla",
    }
