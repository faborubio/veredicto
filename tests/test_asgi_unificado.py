"""E2E del entrypoint ASGI unificado (Fase 5, inc 1): REST + MCP en UN proceso.

Prueba que una sola app ASGI (`interfaces.asgi:app`) sirve simultáneamente:
  - REST (`GET /health` → 200) con todas sus rutas, y
  - MCP sobre **Streamable HTTP** en `/mcp` (handshake + tools/list por el wire).
Todo in-process con httpx `ASGITransport` (sin abrir puerto, CI-safe): el
`Client` de FastMCP habla el protocolo HTTP real contra la app montada. Confirma
que REST y MCP coexisten como adaptadores hermanos en el mismo servidor (ADR-005).
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from httpx import ASGITransport

from interfaces.asgi import app, mcp_app

_CINCO_TOOLS = [
    "consultar_decision",
    "explicar_decision",
    "listar_reglas",
    "rastro_auditoria",
    "simular_cambio_regla",
]


def _cliente_mcp_http() -> Client[Any]:
    """Cliente MCP que habla Streamable HTTP contra la app ASGI in-process."""

    def factory(
        headers: dict[str, str] | None = None,
        timeout: httpx.Timeout | None = None,
        auth: httpx.Auth | None = None,
        **kwargs: Any,  # FastMCP pasa extras como follow_redirects
    ) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://t",
            headers=headers,
            timeout=timeout,
            auth=auth,
            **kwargs,
        )

    return Client(StreamableHttpTransport(url="http://t/mcp/", httpx_client_factory=factory))


def test_un_solo_proceso_sirve_rest_y_mcp() -> None:
    async def _run() -> tuple[int, list[str]]:
        async with mcp_app.lifespan(app):  # inicializa el session manager de FastMCP
            async with httpx.AsyncClient(
                transport=ASGITransport(app=app), base_url="http://t"
            ) as http:
                health = await http.get("/health")

            async with _cliente_mcp_http() as mcp_client:
                tools = sorted(t.name for t in await mcp_client.list_tools())
            return health.status_code, tools

    status, tools = asyncio.run(_run())
    assert status == 200  # REST vivo en la app unificada
    assert tools == _CINCO_TOOLS  # MCP sobre HTTP en el MISMO proceso


def test_mcp_http_ejecuta_listar_reglas_sobre_el_wire() -> None:
    async def _run() -> Any:
        async with mcp_app.lifespan(app), _cliente_mcp_http() as mcp_client:
            return (await mcp_client.call_tool("listar_reglas", {"producto": "consumo"})).data

    data = asyncio.run(_run())
    assert data["version"] == 1
    assert len(data["reglas"]) == 14  # camino exitoso por Streamable HTTP
