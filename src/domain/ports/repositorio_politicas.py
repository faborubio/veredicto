"""Puerto de persistencia de políticas (versionadas e inmutables, ADR-003)."""

from __future__ import annotations

from typing import Protocol

from domain.entities.politica import Politica


class RepositorioPoliticas(Protocol):
    def obtener(self, politica_id: str, version: int) -> Politica:
        """Recupera una versión exacta de política (reproducibilidad)."""
        ...

    def vigente_para(self, producto: str, momento: str) -> Politica:
        """Resuelve la política vigente de un producto en un momento dado.

        El caso de uso la FIJA al inicio del request (anti-TOCTOU, ADR-008)."""
        ...

    def guardar_version(self, politica: Politica) -> None:
        """Persiste una NUEVA versión. Nunca muta una existente (CF-04)."""
        ...

    def activar(self, producto: str, politica_id: str, version: int) -> None:
        """Marca (politica_id, version) como la única vigente del producto (CF-05).
        Guardar y activar son operaciones separadas (ADR-008)."""
        ...
