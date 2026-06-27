"""Entrypoint ASGI unificado: REST + MCP en un solo proceso (Fase 5, inc 1).

`uvicorn interfaces.asgi:app` sirve ambos adaptadores en un mismo árbol ASGI:
  - `/`        → REST (FastAPI): evaluación, gestión de políticas, simulación.
  - `/mcp`     → MCP (FastMCP) sobre **Streamable HTTP** (transporte remoto).

REST y MCP siguen siendo **adaptadores hermanos** sobre los mismos casos de uso
(ADR-005): comparten proceso y el composition root (`obtener_injector`), pero MCP
NO pasa por REST — cada uno llama directo a `application`. `stateless_http=True`
alinea el MCP con el núcleo *stateless* de la spec (SAD §7.2) → escalable detrás
de un balanceador / Cloud Run. El `lifespan` del session manager de FastMCP se
propaga a la app padre (requisito al montar el http_app).

El servidor stdio (`python -m interfaces.mcp.server`) sigue existiendo para el host
local (Claude Desktop); este entrypoint es el camino HTTP/remoto.
"""

from __future__ import annotations

from fastapi import FastAPI

from interfaces.mcp.server import mcp
from interfaces.rest.app import app as rest_app

mcp_app = mcp.http_app(path="/", stateless_http=True)

app = FastAPI(title="Veredicto", version="0.1.0", lifespan=mcp_app.lifespan)
app.include_router(rest_app.router)  # rutas REST directo en la app unificada (/docs las ve)
app.mount("/mcp", mcp_app)  # MCP (Streamable HTTP) en /mcp
