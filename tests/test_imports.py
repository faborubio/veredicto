"""Smoke test de imports de TODAS las capas (R4, Vista de halcón Fase 0).

El test de frontera de `test_scaffolding.py` sólo recorre `domain.*`. Aquí
verificamos que cada módulo de cada capa IMPORTA sin error: un import roto en
`application`, `infrastructure` o `interfaces` (p.ej. el import diferido del
servidor MCP, o la app FastAPI) se cacha de inmediato, no en runtime.

Importar un módulo NO ejecuta su lógica: los servicios/casos de uso esqueleto
sólo lanzan `NotImplementedError` al invocarlos, no al importarlos.
"""

from __future__ import annotations

import importlib
import pkgutil

import pytest

import application
import domain
import infrastructure
import interfaces

_PAQUETES = (application, domain, infrastructure, interfaces)


def _todos_los_modulos() -> list[str]:
    nombres: list[str] = []
    for paquete in _PAQUETES:
        nombres.append(paquete.__name__)
        nombres.extend(
            m.name
            for m in pkgutil.walk_packages(paquete.__path__, prefix=f"{paquete.__name__}.")
        )
    return nombres


@pytest.mark.parametrize("nombre_modulo", _todos_los_modulos())
def test_modulo_importa_sin_error(nombre_modulo: str) -> None:
    importlib.import_module(nombre_modulo)
