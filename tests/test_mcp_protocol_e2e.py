"""E2E del PROTOCOLO MCP (Fase 5, inc 0): cierra la deuda diferida en Fase 4.

Los tests de `test_mcp_server.py` llaman las funciones de las herramientas
directamente, saltándose FastMCP. Aquí ejercitamos el protocolo real
(initialize → tools/list → tools/call) con el `Client` de FastMCP: registro de
herramientas, serialización de argumentos y de resultados estructurados. Es el
mismo cliente que usaría un host MCP (Claude Desktop / Inspector), en proceso
para ser determinista y CI-safe. El transporte stdio por proceso se valida a mano
con el MCP Inspector (ver DEPLOY.md); aquí cubrimos la capa de protocolo.
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastmcp import Client

from interfaces.mcp import server

_CINCO_TOOLS = {
    "consultar_decision",
    "explicar_decision",
    "rastro_auditoria",
    "listar_reglas",
    "simular_cambio_regla",
}


def _ejecutar(coro: Any) -> Any:
    return asyncio.run(coro)


def test_e2e_handshake_lista_exactamente_las_cinco_tools() -> None:
    async def _run() -> set[str]:
        async with Client(server.mcp) as client:
            return {t.name for t in await client.list_tools()}

    assert _ejecutar(_run()) == _CINCO_TOOLS  # tools/list por el protocolo, no atributos del módulo


def test_e2e_call_tool_listar_reglas_devuelve_la_vigente() -> None:
    async def _run() -> Any:  # .data es Any (contenido estructurado del protocolo)
        async with Client(server.mcp) as client:
            return (await client.call_tool("listar_reglas", {"producto": "consumo"})).data

    data = _ejecutar(_run())
    assert data["version"] == 1
    assert len(data["reglas"]) == 14  # camino exitoso serializado por el protocolo


def test_e2e_call_tool_decision_inexistente_traduce_error_sin_stacktrace() -> None:
    async def _run() -> Any:
        async with Client(server.mcp) as client:
            return (await client.call_tool("consultar_decision", {"solicitud_id": "nope"})).data

    assert _ejecutar(_run())["error"] == "no_encontrada"  # MC-01 sobre el wire


def test_e2e_call_tool_simular_politica_mal_formada_traduce_error() -> None:
    async def _run() -> Any:
        async with Client(server.mcp) as client:
            res = await client.call_tool("simular_cambio_regla", {"politica_candidata": {"x": 1}})
            return res.data

    assert _ejecutar(_run())["error"] == "politica_mal_formada"  # MC-04 sobre el wire
