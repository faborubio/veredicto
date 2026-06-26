"""Mecanismos de entrega: REST (FastAPI) y MCP (FastMCP).

Adaptadores hermanos sobre los mismos casos de uso (ADR-005). El adaptador MCP
NO pasa por REST: ambos llaman a `application/` en proceso (SAD §7.1).
"""
