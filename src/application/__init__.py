"""Capa de aplicación: casos de uso que orquestan el dominio y los puertos.

Aquí vive el I/O-orquestación (no en el dominio): resolver/fijar la política
vigente, llamar al buró vía puerto, construir los `Insumos`, invocar el motor
puro y persistir. REST y MCP son adaptadores paralelos sobre estos casos de uso
(ADR-005): toda la lógica vive aquí una sola vez.
"""
