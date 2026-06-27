"""Tests de GestionarReglas (Fase 2): crear versión validada + activación auditada."""

from __future__ import annotations

import pytest

from application.casos_uso.gestionar_reglas import GestionarReglas
from domain.entities.politica import (
    Banda,
    ConfiguracionScoring,
    MetodoAgregacion,
    Politica,
    ResultadoDecision,
    Vigencia,
)
from domain.entities.predicado import Comparacion, Comparador
from domain.entities.regla import AnteDatoFaltante, Categoria, Regla, TipoRegla
from domain.errores import PoliticaInexistente, PoliticaInvalida
from infrastructure.persistence.memoria import (
    RepositorioActivacionesMemoria,
    RepositorioPoliticasMemoria,
)
from infrastructure.seed.politica_consumo import politica_consumo_v1


def _gestor() -> tuple[GestionarReglas, RepositorioActivacionesMemoria]:
    activaciones = RepositorioActivacionesMemoria()
    gestor = GestionarReglas(RepositorioPoliticasMemoria(), activaciones)
    return gestor, activaciones


def _politica_con_campo_invalido() -> Politica:
    regla = Regla(
        id="R-mala",
        nombre="campo fuera del contrato",
        categoria=Categoria.ELEGIBILIDAD,
        tipo=TipoRegla.HARD_STOP,
        predicado=Comparacion("campo_inexistente", Comparador.GT, 1),
        fuente_dato="campo_inexistente",
        ante_dato_faltante=AnteDatoFaltante.TRATAR_COMO_FALLA,
        plantilla_explicacion="x",
    )
    return Politica(
        id="consumo",
        version=9,
        producto="consumo",
        reglas=(regla,),
        config_scoring=ConfiguracionScoring(
            MetodoAgregacion.SUMA_PONDERADA, 100, (Banda(0, ResultadoDecision.RECHAZADO),)
        ),
        vigencia=Vigencia("2026-01-01"),
    )


def test_crear_version_valida_persiste() -> None:
    gestor, _ = _gestor()
    gestor.crear_version(politica_consumo_v1())
    assert gestor.obtener("consumo", 1).version == 1


def test_crear_version_invalida_rechaza_cf03() -> None:
    gestor, _ = _gestor()
    with pytest.raises(PoliticaInvalida):
        gestor.crear_version(_politica_con_campo_invalido())


def test_vigente_solo_tras_activar() -> None:
    gestor, _ = _gestor()
    gestor.crear_version(politica_consumo_v1())
    with pytest.raises(PoliticaInexistente):
        gestor.vigente("consumo", "2026-06-26T00:00:00+00:00")
    gestor.activar("consumo", "consumo", 1, "riesgo@x.cl", "2026-06-26T00:00:00+00:00")
    assert gestor.vigente("consumo", "2026-06-26T00:00:00+00:00").version == 1


def test_activar_registra_evento_auditado() -> None:
    gestor, activaciones = _gestor()
    gestor.crear_version(politica_consumo_v1())
    evento = gestor.activar("consumo", "consumo", 1, "riesgo@x.cl", "2026-06-26T00:00:00+00:00")

    assert evento.actor == "riesgo@x.cl"
    historial = activaciones.historial("consumo")
    assert len(historial) == 1
    assert historial[0].politica_version == 1
