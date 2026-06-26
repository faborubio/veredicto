"""Servidor MCP (stdio): `python -m interfaces.mcp.server` (DEPLOY.md).

Herramientas previstas (read-only + simulación, SAD §5.3):
  consultar_decision · explicar_decision · rastro_auditoria · listar_reglas ·
  simular_cambio_regla.

Esqueleto de Fase 0. El import de FastMCP se difiere a `main()` para que el módulo
sea importable (y auditable por import-linter) sin requerir el runtime MCP. La
implementación de las herramientas llega en Fase 4.
"""

from __future__ import annotations


def main() -> None:
    # TODO(Fase 4): construir el servidor FastMCP, registrar las herramientas
    # read-only sobre los casos de uso (cableados vía injector) y correr stdio.
    raise NotImplementedError("El servidor MCP se implementa en Fase 4.")


if __name__ == "__main__":
    main()
