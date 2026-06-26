"""Adaptador MCP (FastMCP). Capa delgada SIN lógica de negocio (ADR-005).

Por defecto read-only + simulación: `evaluar_solicitud` (escritura) NO se expone
en el MVP (SAD §5.3). Cada herramienta envuelve un caso de uso y lleva una
descripción precisa (el modelo la usa para elegir qué llamar).
"""
