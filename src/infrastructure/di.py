"""Cableado de dependencias con `injector` (ADR-001).

En el arranque se enlazan los puertos del dominio a sus adaptadores concretos de
infraestructura (repos SQLAlchemy, buró simulado) y se construyen los casos de
uso. REST y MCP piden los casos de uso ya cableados; ninguna capa de entrega
conoce las implementaciones concretas.

Esqueleto de Fase 0: el `Module` real se completa cuando existan adaptadores
concretos (Fase 1+).
"""

from __future__ import annotations

from injector import Module


class ModuloVeredicto(Module):
    """Binds de puertos→adaptadores y provisión de casos de uso.

    TODO(Fase 1+): configurar() con bind(RepositorioPoliticas, a=...),
    bind(GatewayBuro, a=BuroSimulado), etc.
    """

    def configure(self, binder: object) -> None:
        # Marcador: sin binds hasta tener adaptadores concretos.
        return None
