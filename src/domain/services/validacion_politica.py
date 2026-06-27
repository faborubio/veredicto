"""Validación de coherencia de una política antes de versionarla (CF-01/02/03).

Es lógica de dominio: una política inválida nunca debe persistirse (CASES.md).
Se invoca desde `GestionarReglas.crear_version`. El predicado bien formado (CF-01)
ya está garantizado por construcción del AST; aquí validamos lo que el tipo no
puede: que cada regla lea sólo campos del contrato de insumos y su `fuente_dato`
declarado (CF-03), y la coherencia básica del scoring (CF-02).
"""

from __future__ import annotations

from domain.entities.insumos import CAMPOS_INSUMO
from domain.entities.politica import Politica
from domain.errores import PoliticaInvalida


def validar_politica(politica: Politica) -> None:
    if not politica.reglas:
        raise PoliticaInvalida(f"La política {politica.id} v{politica.version} no tiene reglas.")

    for regla in politica.reglas:
        campos = regla.campos_referenciados()
        fuera = campos - CAMPOS_INSUMO
        if fuera:
            raise PoliticaInvalida(
                f"Regla '{regla.id}' referencia campos fuera del contrato de insumos: "
                f"{sorted(fuera)} (CF-03)."
            )
        if campos != {regla.fuente_dato}:
            raise PoliticaInvalida(
                f"Regla '{regla.id}': el predicado lee {sorted(campos)} pero declara "
                f"fuente_dato='{regla.fuente_dato}' (CF-03, fuente única)."
            )

    config = politica.config_scoring
    if config.score_maximo <= 0:
        raise PoliticaInvalida("score_maximo debe ser positivo (CF-02).")
    if not config.bandas:
        raise PoliticaInvalida("La configuración de scoring no tiene bandas (CF-02).")
    if min(banda.umbral_min for banda in config.bandas) > 0:
        raise PoliticaInvalida("Las bandas deben cubrir desde score 0 (CF-02).")
