"""Tests del AST de `Predicado` (Fase 1, ADR-002).

Incluye property-based testing (Hypothesis) de dos invariantes:
  - **Determinismo:** evaluar el mismo predicado con los mismos valores da el
    mismo resultado, siempre (ADR-006).
  - **Round-trip de serialización:** `predicado_desde_dict(p.a_dict()) == p`,
    exacto. Es lo que hace que "reglas como datos" sea persistible sin pérdida.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from domain.entities.predicado import (
    Combinacion,
    Combinador,
    Comparacion,
    Comparador,
    Predicado,
    ValorComparable,
    predicado_desde_dict,
)
from domain.errores import ErrorValidacion

# --- Comparaciones unitarias ----------------------------------------------


@pytest.mark.parametrize(
    ("comparador", "umbral", "actual", "esperado"),
    [
        (Comparador.GT, 4500, 4600, True),
        (Comparador.GT, 4500, 4500, False),
        (Comparador.GTE, 4500, 4500, True),
        (Comparador.LT, 4500, 4499, True),
        (Comparador.LTE, 4500, 4500, True),
        (Comparador.EQ, "DEPENDIENTE", "DEPENDIENTE", True),
        (Comparador.NEQ, "DEPENDIENTE", "INDEPENDIENTE", True),
        (Comparador.EQ, True, True, True),
    ],
)
def test_comparacion_evalua(
    comparador: Comparador, umbral: object, actual: object, esperado: bool
) -> None:
    pred = Comparacion("campo", comparador, umbral)  # type: ignore[arg-type]
    assert pred.evaluar({"campo": actual}) is esperado  # type: ignore[dict-item]


def test_in_membresia() -> None:
    pred = Comparacion("situacion", Comparador.IN, ("DEPENDIENTE", "PENSIONADO"))
    assert pred.evaluar({"situacion": "DEPENDIENTE"}) is True
    assert pred.evaluar({"situacion": "INDEPENDIENTE"}) is False


def test_orden_rechaza_no_entero_en_evaluacion() -> None:
    pred = Comparacion("x", Comparador.GT, 10)
    with pytest.raises(ErrorValidacion):
        pred.evaluar({"x": "no-entero"})


def test_orden_rechaza_bool_como_entero() -> None:
    # bool es subclase de int en Python, pero no es comparable por orden aquí.
    pred = Comparacion("x", Comparador.GT, 0)
    with pytest.raises(ErrorValidacion):
        pred.evaluar({"x": True})


def test_validacion_construccion() -> None:
    with pytest.raises(ErrorValidacion):
        Comparacion("x", Comparador.IN, 5)  # IN necesita tupla
    with pytest.raises(ErrorValidacion):
        Comparacion("x", Comparador.GT, "diez")  # orden necesita entero
    with pytest.raises(ErrorValidacion):
        Comparacion("x", Comparador.IN, ())  # tupla vacía
    with pytest.raises(ErrorValidacion):
        Comparacion("x", Comparador.EQ, (1, 2))  # EQ no acepta tupla


def test_campo_ausente_es_error_de_contrato() -> None:
    pred = Comparacion("dti", Comparador.GT, 4500)
    with pytest.raises(ErrorValidacion):
        pred.evaluar({"otro": 1})


# --- Combinaciones ---------------------------------------------------------


def test_and_or_not() -> None:
    a = Comparacion("dti", Comparador.GT, 4500)
    b = Comparacion("situacion", Comparador.EQ, "DEPENDIENTE")
    valores: dict[str, ValorComparable] = {"dti": 5000, "situacion": "DEPENDIENTE"}

    assert Combinacion(Combinador.AND, (a, b)).evaluar(valores) is True
    assert Combinacion(Combinador.OR, (a, b)).evaluar(valores) is True
    assert Combinacion(Combinador.NOT, (a,)).evaluar(valores) is False

    valores_bajo: dict[str, ValorComparable] = {"dti": 1000, "situacion": "DEPENDIENTE"}
    assert Combinacion(Combinador.AND, (a, b)).evaluar(valores_bajo) is False
    assert Combinacion(Combinador.OR, (a, b)).evaluar(valores_bajo) is True


def test_not_requiere_un_operando() -> None:
    a = Comparacion("x", Comparador.GT, 1)
    with pytest.raises(ErrorValidacion):
        Combinacion(Combinador.NOT, (a, a))
    with pytest.raises(ErrorValidacion):
        Combinacion(Combinador.AND, ())


def test_campos_referenciados_union() -> None:
    pred = Combinacion(
        Combinador.AND,
        (
            Comparacion("dti", Comparador.GT, 4500),
            Combinacion(
                Combinador.OR,
                (
                    Comparacion("situacion", Comparador.EQ, "DEPENDIENTE"),
                    Comparacion("morosidad", Comparador.EQ, True),
                ),
            ),
        ),
    )
    assert pred.campos_referenciados() == frozenset({"dti", "situacion", "morosidad"})


def test_predicado_mal_formado_desde_dict() -> None:
    with pytest.raises(ErrorValidacion):
        predicado_desde_dict({"tipo": "desconocido"})
    with pytest.raises(ErrorValidacion):
        predicado_desde_dict({"tipo": "comparacion", "campo": "x", "comparador": "ZZ", "valor": 1})


# --- Property-based: determinismo + round-trip de serialización ------------

_campos = st.sampled_from(["dti", "monto", "plazo", "ingreso"])
_enteros = st.integers(min_value=-1_000_000, max_value=1_000_000)


def _comparaciones_enteras() -> st.SearchStrategy[Predicado]:
    return st.builds(
        Comparacion,
        _campos,
        st.sampled_from(list(Comparador)[:-1]),  # todos menos IN
        _enteros,
    )


def _predicados_enteros() -> st.SearchStrategy[Predicado]:
    return st.recursive(
        _comparaciones_enteras(),
        lambda hijos: st.one_of(
            st.builds(
                Combinacion,
                st.sampled_from([Combinador.AND, Combinador.OR]),
                st.lists(hijos, min_size=1, max_size=3).map(tuple),
            ),
            st.builds(lambda h: Combinacion(Combinador.NOT, (h,)), hijos),
        ),
        max_leaves=6,
    )


@given(pred=_predicados_enteros(), data=st.data())
def test_evaluacion_determinista(pred: Predicado, data: st.DataObject) -> None:
    valores = {campo: data.draw(_enteros) for campo in pred.campos_referenciados()}
    assert pred.evaluar(valores) == pred.evaluar(valores)


@given(pred=_predicados_enteros())
def test_serializacion_round_trip(pred: Predicado) -> None:
    assert predicado_desde_dict(pred.a_dict()) == pred


def test_round_trip_con_in() -> None:
    pred = Comparacion("situacion", Comparador.IN, ("DEPENDIENTE", "PENSIONADO"))
    assert predicado_desde_dict(pred.a_dict()) == pred
