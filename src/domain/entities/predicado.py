"""Predicado: árbol de expresión estructurado y serializable (ADR-002).

El corazón de "reglas como datos, nunca código" (CLAUDE.md invariante 3). Un
predicado es un AST inmutable —jamás una cadena que se `eval()`úa— donde cada nodo
conoce campo/operador/umbral. Eso lo hace:
  - **seguro:** sin ejecución de código arbitrario;
  - **serializable:** `a_dict()` / `predicado_desde_dict()` (round-trip exacto);
  - **explicable:** cada nodo expone el campo, el operador y el umbral que comparó;
  - **validable:** `campos_referenciados()` permite chequear que todo campo exista
    en el contrato de insumos (CASES.md CF-03).

Pureza/determinismo (ADR-006): `evaluar` no hace I/O, no lee reloj, no muta nada,
y opera sobre enteros/strings/bools — sin `float`. La disponibilidad de datos se
maneja a nivel de REGLA (ADR-009), no aquí: el motor sólo invoca `evaluar` con los
valores ya disponibles.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from domain.errores import ErrorValidacion

# Valores que el motor puede comparar. Sin `float` (invariante 1). `bool` se admite
# sólo para igualdad (EQ/NEQ), nunca para orden.
ValorComparable = int | str | bool
# El umbral de una `Comparacion`: un escalar, o una tupla para el operador IN.
ValorRegla = ValorComparable | tuple[ValorComparable, ...]


class Comparador(Enum):
    GT = "GT"  # mayor que            (sólo enteros)
    GTE = "GTE"  # mayor o igual       (sólo enteros)
    LT = "LT"  # menor que            (sólo enteros)
    LTE = "LTE"  # menor o igual       (sólo enteros)
    EQ = "EQ"  # igual               (int/str/bool)
    NEQ = "NEQ"  # distinto            (int/str/bool)
    IN = "IN"  # pertenece a conjunto (umbral = tupla)


class Combinador(Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


_COMPARADORES_DE_ORDEN = frozenset({Comparador.GT, Comparador.GTE, Comparador.LT, Comparador.LTE})


def _es_entero(valor: object) -> bool:
    """True sólo para enteros de verdad. `bool` es subclase de `int` en Python,
    pero NO es un entero comparable por orden en nuestro dominio."""
    return type(valor) is int


class Predicado(ABC):
    """Nodo del árbol de expresión. Inmutable, evaluable, serializable."""

    __slots__ = ()

    @abstractmethod
    def evaluar(self, valores: Mapping[str, ValorComparable]) -> bool:
        """Evalúa el predicado contra los valores DISPONIBLES. Asume presencia de
        los campos referenciados (el motor lo garantiza tras el gate de
        disponibilidad de la regla). Si falta un campo es un error de contrato,
        no un caso de negocio: lanza `ErrorValidacion`."""

    @abstractmethod
    def campos_referenciados(self) -> frozenset[str]:
        """Conjunto de campos (`fuente_dato`) que el predicado lee. Para validar
        contra el contrato de insumos (CF-03) y para trazabilidad."""

    @abstractmethod
    def a_dict(self) -> dict[str, object]:
        """Serialización a estructura JSON-compatible (persistencia, ADR-002)."""


@dataclass(frozen=True, slots=True)
class Comparacion(Predicado):
    """Hoja del árbol: compara un campo contra un umbral con un `Comparador`."""

    campo: str
    comparador: Comparador
    valor: ValorRegla

    def __post_init__(self) -> None:
        if self.comparador is Comparador.IN:
            if not isinstance(self.valor, tuple) or len(self.valor) == 0:
                raise ErrorValidacion("El operador IN requiere una tupla no vacía de valores.")
        else:
            if isinstance(self.valor, tuple):
                raise ErrorValidacion(
                    f"El operador {self.comparador.name} no acepta una tupla como umbral."
                )
            if self.comparador in _COMPARADORES_DE_ORDEN and not _es_entero(self.valor):
                raise ErrorValidacion(
                    f"El operador {self.comparador.name} requiere un umbral entero "
                    "(sin float ni bool)."
                )

    def evaluar(self, valores: Mapping[str, ValorComparable]) -> bool:
        if self.campo not in valores:
            raise ErrorValidacion(
                f"Campo '{self.campo}' ausente del contexto de evaluación (error de contrato)."
            )
        return _aplicar(self.comparador, valores[self.campo], self.valor)

    def campos_referenciados(self) -> frozenset[str]:
        return frozenset({self.campo})

    def a_dict(self) -> dict[str, object]:
        valor: object = list(self.valor) if isinstance(self.valor, tuple) else self.valor
        return {
            "tipo": "comparacion",
            "campo": self.campo,
            "comparador": self.comparador.value,
            "valor": valor,
        }


@dataclass(frozen=True, slots=True)
class Combinacion(Predicado):
    """Nodo interno: combina sub-predicados con AND / OR / NOT."""

    combinador: Combinador
    operandos: tuple[Predicado, ...]

    def __post_init__(self) -> None:
        if self.combinador is Combinador.NOT:
            if len(self.operandos) != 1:
                raise ErrorValidacion("NOT requiere exactamente un operando.")
        elif len(self.operandos) < 1:
            raise ErrorValidacion(f"{self.combinador.name} requiere al menos un operando.")

    def evaluar(self, valores: Mapping[str, ValorComparable]) -> bool:
        if self.combinador is Combinador.NOT:
            return not self.operandos[0].evaluar(valores)
        if self.combinador is Combinador.AND:
            return all(o.evaluar(valores) for o in self.operandos)
        return any(o.evaluar(valores) for o in self.operandos)

    def campos_referenciados(self) -> frozenset[str]:
        return frozenset().union(*(o.campos_referenciados() for o in self.operandos))

    def a_dict(self) -> dict[str, object]:
        return {
            "tipo": "combinacion",
            "combinador": self.combinador.value,
            "operandos": [o.a_dict() for o in self.operandos],
        }


def _aplicar(comparador: Comparador, actual: ValorComparable, esperado: ValorRegla) -> bool:
    if comparador is Comparador.EQ:
        return actual == esperado
    if comparador is Comparador.NEQ:
        return actual != esperado
    if comparador is Comparador.IN:
        if not isinstance(esperado, tuple):
            raise ErrorValidacion("IN requiere una tupla como umbral.")
        return actual in esperado
    # Comparadores de orden: exigen enteros reales en ambos lados.
    if not (_es_entero(actual) and _es_entero(esperado)):
        raise ErrorValidacion(
            f"El operador {comparador.name} sólo compara enteros; "
            f"recibió {type(actual).__name__} vs {type(esperado).__name__}."
        )
    assert isinstance(actual, int) and isinstance(esperado, int)  # narrowing para mypy
    if comparador is Comparador.GT:
        return actual > esperado
    if comparador is Comparador.GTE:
        return actual >= esperado
    if comparador is Comparador.LT:
        return actual < esperado
    return actual <= esperado  # LTE


def predicado_desde_dict(d: Mapping[str, object]) -> Predicado:
    """Reconstruye un `Predicado` desde su forma serializada. Valida la estructura;
    una forma mal formada lanza `ErrorValidacion` (CASES.md CF-01), nunca produce
    un predicado a medio construir."""
    tipo = d.get("tipo")
    if tipo == "comparacion":
        campo = d.get("campo")
        comparador_raw = d.get("comparador")
        valor = d.get("valor")
        if not isinstance(campo, str) or not isinstance(comparador_raw, str):
            raise ErrorValidacion("Comparacion serializada mal formada: 'campo'/'comparador'.")
        try:
            comparador = Comparador(comparador_raw)
        except ValueError as exc:
            raise ErrorValidacion(f"Comparador desconocido: {comparador_raw!r}.") from exc
        if comparador is Comparador.IN:
            if not isinstance(valor, list):
                raise ErrorValidacion("IN serializado requiere una lista de valores.")
            return Comparacion(campo, comparador, tuple(valor))
        if not isinstance(valor, (int, str)):
            raise ErrorValidacion("Umbral serializado inválido para la comparación.")
        return Comparacion(campo, comparador, valor)
    if tipo == "combinacion":
        combinador_raw = d.get("combinador")
        operandos_raw = d.get("operandos")
        if not isinstance(combinador_raw, str) or not isinstance(operandos_raw, list):
            raise ErrorValidacion("Combinacion serializada mal formada.")
        try:
            combinador = Combinador(combinador_raw)
        except ValueError as exc:
            raise ErrorValidacion(f"Combinador desconocido: {combinador_raw!r}.") from exc
        operandos = tuple(
            predicado_desde_dict(o) if isinstance(o, Mapping) else _operando_invalido()
            for o in operandos_raw
        )
        return Combinacion(combinador, operandos)
    raise ErrorValidacion(f"Tipo de predicado desconocido: {tipo!r}.")


def _operando_invalido() -> Predicado:
    raise ErrorValidacion("Operando de combinación serializado inválido.")
