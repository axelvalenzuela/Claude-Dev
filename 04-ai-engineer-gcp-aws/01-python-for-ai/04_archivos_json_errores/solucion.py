"""Solución del Ejercicio #4. Intenta resolverlo tú antes de leer esto."""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _verificador import verificar  # noqa: E402

VENTAS_CSV = Path(__file__).resolve().parents[2] / "04-vertex-ai-projects" / "comun" / "datos" / "ventas.csv"


def leer_json(texto):
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        return {"error": "json invalido"}


def ventas_completadas(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return sum(1 for fila in csv.DictReader(archivo) if fila["estado"] == "COMPLETADA")


def total_completadas(ruta):
    total = 0.0
    with open(ruta, encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            if fila["estado"] == "COMPLETADA":
                total += float(fila["monto"])
    return total


RETOS = [
    (1, "leer_json con JSON bueno y malo",
     lambda: (leer_json('{"a": 1}'), leer_json("esto no es json")), ({"a": 1}, {"error": "json invalido"})),
    (2, "ventas_completadas cuenta filas del CSV", lambda: ventas_completadas(VENTAS_CSV), 9),
    (3, "total_completadas suma montos", lambda: total_completadas(VENTAS_CSV), 71021.0),
]

if __name__ == "__main__":
    verificar(RETOS, estricto=True)
