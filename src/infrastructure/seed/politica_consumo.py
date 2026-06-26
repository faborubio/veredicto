"""Política de crédito de consumo chileno — versión 1 (DATO, no código).

Umbrales acordados como defaults v1 (refinables vía nueva versión, ADR-003). El
scoring por tramos se modela como reglas booleanas con peso fijo y rangos
mutuamente excluyentes (fiel a ADR-002): cada regla suma su peso sii su predicado
pasa, evitando doble conteo.

Score máximo = 100 (DTI máx 40 + situación máx 30 + historial máx 30).
Bandas: ≥70 APROBADO · 40-69 REVISION_MANUAL · <40 RECHAZADO.

Thin file (EV-02): si `meses_historial` viene NO_DISPONIBLE (sin historial), las
reglas de historial fuerzan REVISION_MANUAL vía `ante_dato_faltante`.
"""

from __future__ import annotations

from domain.entities.politica import (
    Banda,
    ConfiguracionScoring,
    MetodoAgregacion,
    Politica,
    ResultadoDecision,
    Vigencia,
)
from domain.entities.predicado import (
    Combinacion,
    Combinador,
    Comparacion,
    Comparador,
    Predicado,
    ValorRegla,
)
from domain.entities.regla import AnteDatoFaltante, Categoria, Regla, TipoRegla

# --- Helpers de predicado --------------------------------------------------


def _cmp(campo: str, comparador: Comparador, valor: ValorRegla) -> Comparacion:
    return Comparacion(campo, comparador, valor)


def _entre(campo: str, minimo: int, maximo: int) -> Combinacion:
    return Combinacion(
        Combinador.AND,
        (_cmp(campo, Comparador.GTE, minimo), _cmp(campo, Comparador.LTE, maximo)),
    )


def _rango_semi(campo: str, mayor_que: int, hasta: int) -> Combinacion:
    """mayor_que < campo <= hasta (tramos de scoring mutuamente excluyentes)."""
    return Combinacion(
        Combinador.AND,
        (_cmp(campo, Comparador.GT, mayor_que), _cmp(campo, Comparador.LTE, hasta)),
    )


def _hard(
    id_: str,
    nombre: str,
    categoria: Categoria,
    fuente: str,
    predicado: Predicado,
    ante: AnteDatoFaltante,
    plantilla: str,
) -> Regla:
    return Regla(
        id=id_,
        nombre=nombre,
        categoria=categoria,
        tipo=TipoRegla.HARD_STOP,
        predicado=predicado,
        fuente_dato=fuente,
        ante_dato_faltante=ante,
        plantilla_explicacion=plantilla,
    )


def _scoring(
    id_: str,
    nombre: str,
    categoria: Categoria,
    fuente: str,
    predicado: Predicado,
    peso: int,
    plantilla: str,
) -> Regla:
    return Regla(
        id=id_,
        nombre=nombre,
        categoria=categoria,
        tipo=TipoRegla.SCORING,
        predicado=predicado,
        fuente_dato=fuente,
        ante_dato_faltante=AnteDatoFaltante.FORZAR_REVISION,
        plantilla_explicacion=plantilla,
        peso=peso,
    )


_REGLAS: tuple[Regla, ...] = (
    # --- Hard-stops de elegibilidad ---
    _hard(
        "R1-monto-rango",
        "Monto dentro del rango del producto",
        Categoria.ELEGIBILIDAD,
        "monto",
        _entre("monto", 500_000, 20_000_000),
        AnteDatoFaltante.TRATAR_COMO_FALLA,
        "Monto solicitado {valor} CLP debe estar entre 500.000 y 20.000.000.",
    ),
    _hard(
        "R2-plazo-rango",
        "Plazo dentro del rango permitido",
        Categoria.ELEGIBILIDAD,
        "plazo",
        _entre("plazo", 6, 48),
        AnteDatoFaltante.TRATAR_COMO_FALLA,
        "Plazo {valor} meses debe estar entre 6 y 48.",
    ),
    # --- Hard-stops de comportamiento (buró) ---
    _hard(
        "R3-sin-morosidad",
        "Sin morosidad vigente",
        Categoria.COMPORTAMIENTO,
        "tiene_morosidad_vigente",
        _cmp("tiene_morosidad_vigente", Comparador.EQ, False),
        AnteDatoFaltante.FORZAR_REVISION,
        "No debe registrar morosidad vigente.",
    ),
    _hard(
        "R4-sin-castigadas",
        "Sin deudas castigadas",
        Categoria.COMPORTAMIENTO,
        "tiene_deudas_castigadas",
        _cmp("tiene_deudas_castigadas", Comparador.EQ, False),
        AnteDatoFaltante.FORZAR_REVISION,
        "No debe registrar deudas castigadas.",
    ),
    # --- Hard-stops de capacidad de pago ---
    _hard(
        "R5-ingreso-minimo",
        "Ingreso mensual mínimo",
        Categoria.CAPACIDAD_PAGO,
        "ingreso_mensual",
        _cmp("ingreso_mensual", Comparador.GTE, 350_000),
        AnteDatoFaltante.TRATAR_COMO_FALLA,
        "Ingreso mensual {valor} CLP debe ser al menos 350.000.",
    ),
    _hard(
        "R6-dti-tope",
        "DTI bajo el tope duro",
        Categoria.CAPACIDAD_PAGO,
        "dti",
        _cmp("dti", Comparador.LTE, 5_000),
        AnteDatoFaltante.FORZAR_REVISION,
        "DTI {valor} bps no debe superar 5000 (50%).",
    ),
    # --- Scoring: DTI (tramos excluyentes, máx 40) ---
    _scoring(
        "R7a-dti-excelente",
        "DTI ≤ 25%",
        Categoria.CAPACIDAD_PAGO,
        "dti",
        _cmp("dti", Comparador.LTE, 2_500),
        40,
        "DTI {valor} bps en tramo excelente (≤2500).",
    ),
    _scoring(
        "R7b-dti-bueno",
        "DTI 25%-35%",
        Categoria.CAPACIDAD_PAGO,
        "dti",
        _rango_semi("dti", 2_500, 3_500),
        25,
        "DTI {valor} bps en tramo bueno (2500-3500).",
    ),
    _scoring(
        "R7c-dti-aceptable",
        "DTI 35%-50%",
        Categoria.CAPACIDAD_PAGO,
        "dti",
        _rango_semi("dti", 3_500, 5_000),
        10,
        "DTI {valor} bps en tramo aceptable (3500-5000).",
    ),
    # --- Scoring: situación laboral (excluyente, máx 30) ---
    _scoring(
        "R8a-dependiente",
        "Situación laboral dependiente",
        Categoria.CAPACIDAD_PAGO,
        "situacion_laboral",
        _cmp("situacion_laboral", Comparador.EQ, "DEPENDIENTE"),
        30,
        "Situación laboral {valor}.",
    ),
    _scoring(
        "R8b-pensionado",
        "Situación laboral pensionado",
        Categoria.CAPACIDAD_PAGO,
        "situacion_laboral",
        _cmp("situacion_laboral", Comparador.EQ, "PENSIONADO"),
        20,
        "Situación laboral {valor}.",
    ),
    _scoring(
        "R8c-independiente",
        "Situación laboral independiente",
        Categoria.CAPACIDAD_PAGO,
        "situacion_laboral",
        _cmp("situacion_laboral", Comparador.EQ, "INDEPENDIENTE"),
        10,
        "Situación laboral {valor}.",
    ),
    # --- Scoring: antigüedad de historial (excluyente, máx 30) ---
    _scoring(
        "R9a-historial-solido",
        "Historial ≥ 24 meses",
        Categoria.COMPORTAMIENTO,
        "meses_historial",
        _cmp("meses_historial", Comparador.GTE, 24),
        30,
        "Historial de {valor} meses (sólido).",
    ),
    _scoring(
        "R9b-historial-medio",
        "Historial 6-23 meses",
        Categoria.COMPORTAMIENTO,
        "meses_historial",
        Combinacion(
            Combinador.AND,
            (
                _cmp("meses_historial", Comparador.GTE, 6),
                _cmp("meses_historial", Comparador.LT, 24),
            ),
        ),
        15,
        "Historial de {valor} meses (medio).",
    ),
)

_CONFIG_SCORING = ConfiguracionScoring(
    metodo_agregacion=MetodoAgregacion.SUMA_PONDERADA,
    score_maximo=100,
    bandas=(
        Banda(70, ResultadoDecision.APROBADO),
        Banda(40, ResultadoDecision.REVISION_MANUAL),
        Banda(0, ResultadoDecision.RECHAZADO),
    ),
)


def politica_consumo_v1() -> Politica:
    """Construye la política de consumo v1 (inmutable)."""
    return Politica(
        id="consumo",
        version=1,
        producto="consumo",
        reglas=_REGLAS,
        config_scoring=_CONFIG_SCORING,
        vigencia=Vigencia(efectiva_desde="2026-01-01"),
    )
