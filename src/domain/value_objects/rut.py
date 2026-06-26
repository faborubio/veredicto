"""RUT chileno con validación de dígito verificador (módulo 11).

CASES.md EV-01: un RUT inválido se rechaza al construirse, con error tipado
(`ErrorValidacion`), antes de que entre al motor. Es PII (§8.1).
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.errores import ErrorValidacion


def calcular_dv(numero: int) -> str:
    """Dígito verificador chileno (módulo 11). Devuelve "0"-"9" o "K"."""
    suma = 0
    multiplicador = 2
    for caracter in reversed(str(numero)):
        suma += int(caracter) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1
    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


@dataclass(frozen=True, slots=True)
class Rut:
    """RUT normalizado (número + dígito verificador). El DV se valida al construir."""

    numero: int
    digito_verificador: str  # "0"-"9" o "K"

    def __post_init__(self) -> None:
        if type(self.numero) is not int or self.numero <= 0:
            raise ErrorValidacion("El RUT debe tener un número entero positivo.")
        dv = self.digito_verificador.upper()
        esperado = calcular_dv(self.numero)
        if dv != esperado:
            raise ErrorValidacion(
                f"Dígito verificador inválido para {self.numero}: "
                f"esperado '{esperado}', recibió '{self.digito_verificador}'."
            )
        object.__setattr__(self, "digito_verificador", dv)  # normaliza a mayúscula

    @classmethod
    def desde_texto(cls, texto: str) -> Rut:
        """Construye desde formatos como "12.345.678-5" o "123456785"."""
        limpio = texto.replace(".", "").replace(" ", "").upper()
        if "-" in limpio:
            cuerpo, dv = limpio.rsplit("-", 1)
        elif len(limpio) >= 2:
            cuerpo, dv = limpio[:-1], limpio[-1]
        else:
            raise ErrorValidacion(f"RUT mal formado: '{texto}'.")
        if not cuerpo.isdigit():
            raise ErrorValidacion(f"RUT mal formado: '{texto}'.")
        return cls(int(cuerpo), dv)

    @property
    def enmascarado(self) -> str:
        """Representación para logs/respuestas sin exponer PII completa (§8.1)."""
        cuerpo = str(self.numero)
        visible = cuerpo[-3:] if len(cuerpo) >= 3 else cuerpo
        return f"***{visible}-{self.digito_verificador}"
