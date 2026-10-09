"""Ejercicio #5 — Clases, dataclasses y type hints.

Por qué importa para IA: el SDK de Gemini, Pydantic (salida estructurada) y los
agentes de la parte 2 están hechos con CLASES. Si entiendes esto, podrás leer
comun/llm.py y comun/esquemas.py sin perderte.

  PASO #1: python 01-python-for-ai/05_clases_y_tipos/ejercicio.py
  PASO #2: lee demostracion()
  PASO #3: resuelve los retos
  PASO #4: vuelve a correr hasta ver todo en [OK]
"""
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _verificador import verificar  # noqa: E402


# PASO #1 — type hints: `texto: str` dice qué TIPO se espera. Python no lo obliga, pero
#           las herramientas (y Pydantic) sí lo usan. -> float dice qué devuelve.
def precio_total(tokens: int, precio: float) -> float:
    return tokens * precio / 1_000_000


# PASO #2 — @dataclass: una clase para GUARDAR datos con nombre, sin escribir __init__ a mano
@dataclass
class Respuesta:
    texto: str
    tokens_entrada: int
    tokens_salida: int

    # PASO #3 — un MÉTODO es una función que vive dentro de la clase; `self` es "este objeto"
    def total_tokens(self) -> int:
        return self.tokens_entrada + self.tokens_salida


# PASO #4 — clase normal con __init__ (se ejecuta al crear el objeto) y estado que cambia
class AgenteEco:
    """Un 'agente' de juguete que recuerda lo que le dicen."""

    def __init__(self, nombre: str):
        self.nombre = nombre
        self.historial: list[str] = []

    def responder(self, mensaje: str) -> str:
        self.historial.append(mensaje)
        return f"[{self.nombre}] recibí: {mensaje} (van {len(self.historial)} mensajes)"


def demostracion():
    print("precio_total:", precio_total(2_000_000, 0.25))

    r = Respuesta(texto="hola", tokens_entrada=10, tokens_salida=5)    # crear un OBJETO
    print(r)                                   # las dataclasses se imprimen bonito solas
    print("total de tokens:", r.total_tokens())
    print("como diccionario:", asdict(r))      # útil para convertir a JSON

    agente = AgenteEco("analista")
    print(agente.responder("analiza ventas.sas"))
    print(agente.responder("¿cuántas reglas encontraste?"))
    print("historial:", agente.historial)

    # PASO #5 — en la parte 2 verás Pydantic: se parece a @dataclass, pero ADEMÁS valida
    #           los tipos (si llega "abc" donde va un int, avisa). Ver comun/esquemas.py.


# ============================================================================
# RETOS
# ============================================================================

@dataclass
class Llamada:
    tokens_entrada: int
    tokens_salida: int

    def costo(self, precio_entrada: float, precio_salida: float) -> float:
        """Reto #1: costo = entrada * precio_entrada / 1M + salida * precio_salida / 1M"""
        # TU CÓDIGO AQUÍ  (usa self.tokens_entrada y self.tokens_salida)
        return None


def total_costos(llamadas: list[Llamada], precio_entrada: float, precio_salida: float) -> float:
    """Reto #2: suma el costo de todas las llamadas de la lista (usa el método del reto #1)."""
    # TU CÓDIGO AQUÍ
    return None


@dataclass
class Memoria:
    """Reto #3: la memoria de un agente. Completa agregar() y ultimos()."""
    mensajes: list[str] = field(default_factory=list)   # una lista vacía nueva para cada Memoria

    def agregar(self, mensaje: str) -> None:
        # TU CÓDIGO AQUÍ  (agrega el mensaje a self.mensajes)
        pass

    def ultimos(self, n: int) -> list[str]:
        """Devuelve los últimos n mensajes.  Pista: lista[-n:] da los últimos n elementos."""
        # TU CÓDIGO AQUÍ
        return None


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
    demostracion()
    verificar(RETOS)
