"""Traducción entidad↔fila para `Politica` (la frontera ORM vive aquí, no en el
dominio ni en los modelos). Round-trip exacto: dominio → JSONB → dominio.
"""

from __future__ import annotations

from typing import Any

from domain.entities.politica import (
    Banda,
    ConfiguracionScoring,
    MetodoAgregacion,
    Politica,
    ResultadoDecision,
    Vigencia,
)
from domain.entities.predicado import predicado_desde_dict
from domain.entities.regla import AnteDatoFaltante, Categoria, Regla, TipoRegla
from infrastructure.persistence.modelos import PoliticaORM


def _regla_a_dict(regla: Regla) -> dict[str, Any]:
    return {
        "id": regla.id,
        "nombre": regla.nombre,
        "categoria": regla.categoria.value,
        "tipo": regla.tipo.value,
        "predicado": regla.predicado.a_dict(),
        "fuente_dato": regla.fuente_dato,
        "ante_dato_faltante": regla.ante_dato_faltante.value,
        "plantilla_explicacion": regla.plantilla_explicacion,
        "peso": regla.peso,
    }


def _regla_desde_dict(d: dict[str, Any]) -> Regla:
    return Regla(
        id=d["id"],
        nombre=d["nombre"],
        categoria=Categoria(d["categoria"]),
        tipo=TipoRegla(d["tipo"]),
        predicado=predicado_desde_dict(d["predicado"]),
        fuente_dato=d["fuente_dato"],
        ante_dato_faltante=AnteDatoFaltante(d["ante_dato_faltante"]),
        plantilla_explicacion=d["plantilla_explicacion"],
        peso=d["peso"],
    )


def _config_a_dict(config: ConfiguracionScoring) -> dict[str, Any]:
    return {
        "metodo_agregacion": config.metodo_agregacion.value,
        "score_maximo": config.score_maximo,
        "bandas": [
            {"umbral_min": b.umbral_min, "resultado": b.resultado.value} for b in config.bandas
        ],
    }


def _config_desde_dict(d: dict[str, Any]) -> ConfiguracionScoring:
    return ConfiguracionScoring(
        metodo_agregacion=MetodoAgregacion(d["metodo_agregacion"]),
        score_maximo=d["score_maximo"],
        bandas=tuple(
            Banda(b["umbral_min"], ResultadoDecision(b["resultado"])) for b in d["bandas"]
        ),
    )


def politica_a_orm(politica: Politica) -> PoliticaORM:
    return PoliticaORM(
        politica_id=politica.id,
        version=politica.version,
        producto=politica.producto,
        reglas=[_regla_a_dict(r) for r in politica.reglas],
        config_scoring=_config_a_dict(politica.config_scoring),
        efectiva_desde=politica.vigencia.efectiva_desde,
        efectiva_hasta=politica.vigencia.efectiva_hasta,
    )


def politica_desde_orm(orm: PoliticaORM) -> Politica:
    return Politica(
        id=orm.politica_id,
        version=orm.version,
        producto=orm.producto,
        reglas=tuple(_regla_desde_dict(d) for d in orm.reglas),
        config_scoring=_config_desde_dict(orm.config_scoring),
        vigencia=Vigencia(efectiva_desde=orm.efectiva_desde, efectiva_hasta=orm.efectiva_hasta),
    )
