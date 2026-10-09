"""Solución del Ejercicio #5. Intenta resolverlo tú antes de leer esto."""
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _verificador import verificar  # noqa: E402


@dataclass
class Llamada:
    tokens_entrada: int
    tokens_salida: int

    def costo(self, precio_entrada: float, precio_salida: float) -> float:
        return (self.tokens_entrada * precio_entrada + self.tokens_salida * precio_salida) / 1_000_000


def total_costos(llamadas: list[Llamada], precio_entrada: float, precio_salida: float) -> float:
    return sum(llamada.costo(precio_entrada, precio_salida) for llamada in llamadas)


@dataclass
class Memoria:
    mensajes: list[str] = field(default_factory=list)

    def agregar(self, mensaje: str) -> None:
        self.mensajes.append(mensaje)

    def ultimos(self, n: int) -> list[str]:
        return self.mensajes[-n:]


def _probar_memoria():
    m = Memoria()
    for mensaje in ["hola", "analiza ventas.sas", "gracias"]:
        m.agregar(mensaje)
    return m.ultimos(2)


RETOS = [
    (1, "Llamada.costo", lambda: Llamada(1_000_000, 1_000_000).costo(0.25, 1.50), 1.75),
    (2, "total_costos", lambda: total_costos([Llamada(1_000_000, 0), Llamada(0, 1_000_000)], 0.25, 1.50), 1.75),
    (3, "Memoria.agregar y Memoria.ultimos", _probar_memoria, ["analiza ventas.sas", "gracias"]),
]

if __name__ == "__main__":
    verificar(RETOS, estricto=True)
