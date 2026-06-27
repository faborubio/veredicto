"""GestionarReglas: crear nuevas versiones de política, activarlas y listarlas.

Configurabilidad (ADR-003): "editar" = crear una NUEVA versión completa, validada
e inmutable; nunca mutar una existente (CASES.md CF-04). La validación de
coherencia (CF-01/02/03) ocurre ANTES de persistir. Activar una versión es un
evento auditado (ADR-008): quién/qué/cuándo queda registrado. El modo lectura se
expone vía MCP; la escritura, no, en el MVP.
"""

from __future__ import annotations

from domain.entities.activacion import EventoActivacionPolitica
from domain.entities.politica import Politica
from domain.ports.repositorio_activaciones import RepositorioActivaciones
from domain.ports.repositorio_politicas import RepositorioPoliticas
from domain.services.validacion_politica import validar_politica


class GestionarReglas:
    def __init__(
        self,
        politicas: RepositorioPoliticas,
        activaciones: RepositorioActivaciones,
    ) -> None:
        self._politicas = politicas
        self._activaciones = activaciones

    def crear_version(self, politica: Politica) -> None:
        """Valida (CF-01/02/03) y persiste una nueva versión inmutable. No la
        activa: la activación es un paso aparte y auditado (ADR-008)."""
        validar_politica(politica)
        self._politicas.guardar_version(politica)

    def activar(
        self,
        producto: str,
        politica_id: str,
        version: int,
        actor: str,
        momento: str,
    ) -> EventoActivacionPolitica:
        """Activa una versión y registra el evento auditado (ADR-008)."""
        self._politicas.activar(producto, politica_id, version)
        evento = EventoActivacionPolitica(
            politica_id=politica_id,
            politica_version=version,
            producto=producto,
            actor=actor,
            momento=momento,
        )
        self._activaciones.registrar(evento)
        return evento

    def obtener(self, politica_id: str, version: int) -> Politica:
        return self._politicas.obtener(politica_id, version)

    def vigente(self, producto: str, momento: str) -> Politica:
        return self._politicas.vigente_para(producto, momento)
