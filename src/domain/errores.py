"""Errores de dominio tipados.

Invariante 12 (CLAUDE.md) / §8.4 SAD: nunca tragar excepciones en silencio.
Los errores del dominio son excepciones tipadas que las capas de entrega
(REST/MCP) traducen a códigos HTTP/MCP. El dominio NO conoce HTTP.
"""

from __future__ import annotations


class ErrorDominio(Exception):
    """Raíz de todos los errores de dominio. Permite capturar por categoría."""


class ErrorValidacion(ErrorDominio):
    """Un value object o entidad recibió datos que violan sus invariantes.

    Ej.: RUT con dígito verificador inválido (CASES.md EV-01), monto negativo,
    mezcla de monedas.
    """


class PoliticaInexistente(ErrorDominio):
    """Se solicitó una versión de política que no existe."""


class PoliticaInvalida(ErrorDominio):
    """Una política no pasa sus reglas de coherencia al construirse/versionarse.

    Ej.: regla que referencia un `fuente_dato` inexistente (CASES.md CF-03),
    predicado mal formado (CF-01), bandas de scoring incoherentes (CF-02).
    """


class DecisionInexistente(ErrorDominio):
    """Se consultó una decisión que no existe (CASES.md MC-01)."""
