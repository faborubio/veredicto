"""GestionarReglas: crear nuevas versiones de política y listarlas.

Configurabilidad (ADR-003): "editar" = crear una NUEVA versión de política
completa, validada e inmutable; nunca mutar una existente (CASES.md CF-04).
Activar una versión es un evento auditado (ADR-008). El modo lectura
(`listar_reglas`) se expone vía MCP; la escritura, no, en el MVP.
"""

from __future__ import annotations

from domain.ports.repositorio_activaciones import RepositorioActivaciones
from domain.ports.repositorio_politicas import RepositorioPoliticas


class GestionarReglas:
    def __init__(
        self,
        politicas: RepositorioPoliticas,
        activaciones: RepositorioActivaciones,
    ) -> None:
        self._politicas = politicas
        self._activaciones = activaciones

    # TODO(Fase 2):
    #   - crear_version(politica) con validación de coherencia (CF-01..CF-03).
    #   - activar(politica_id, version, actor) → registra EventoActivacionPolitica.
    #   - listar(version?) para lectura/MCP.
