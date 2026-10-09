"""Ejercicio #4 — Módulos, archivos, JSON, CSV y manejo de errores.

Por qué importa para IA: lees datos de archivos, los modelos responden JSON
(que a veces viene MAL), y tu programa no debe tronar por eso.

  PASO #1: python 01-python-for-ai/04_archivos_json_errores/ejercicio.py
  PASO #2: lee demostracion()
  PASO #3: resuelve los retos
  PASO #4: vuelve a correr hasta ver todo en [OK]
"""
import csv                   # PASO #1 — import: traer herramientas de la biblioteca estándar
import json
import sys
from pathlib import Path     # Path: rutas de archivos que funcionan en Windows, Mac y Linux

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _verificador import verificar  # noqa: E402

AQUI = Path(__file__).resolve().parent
# El mismo archivo de ventas que usa la parte 2 (la "tabla" que migraremos desde SAS)
VENTAS_CSV = AQUI.parents[1] / "04-vertex-ai-projects" / "comun" / "datos" / "ventas.csv"


def demostracion():
    # PASO #2 — leer un archivo de texto completo
    texto = VENTAS_CSV.read_text(encoding="utf-8")
    print("primeras líneas del CSV:\n" + "\n".join(texto.splitlines()[:3]))

    # PASO #3 — leer un CSV fila por fila; DictReader da cada fila como diccionario
    with VENTAS_CSV.open(encoding="utf-8") as archivo:      # with = cierra el archivo solo al terminar
        for fila in csv.DictReader(archivo):
            print(f"  venta {fila['id']}: {fila['region']} {fila['estado']} ${fila['monto']}")
            break                                            # solo la primera, para no llenar la pantalla
    # OJO: del CSV todo llega como TEXTO. "12000" no es 12000: se convierte con float() o int().

    # PASO #4 — JSON: el formato en que responden los modelos y las APIs
    respuesta_texto = '{"resumen": "filtra ventas", "complejidad": "baja", "reglas": 3}'
    datos = json.loads(respuesta_texto)          # texto JSON -> diccionario de Python
    print("complejidad:", datos["complejidad"])
    print("de vuelta a texto:", json.dumps(datos, ensure_ascii=False))

    # PASO #5 — try / except: atrapar un error en vez de que el programa truene
    respuesta_rota = '{"resumen": "filtra ventas", "complejidad": '      # un modelo cortó la respuesta
    try:
        json.loads(respuesta_rota)
    except json.JSONDecodeError as error:
        print("El modelo devolvió JSON inválido:", error.msg)


# ============================================================================
# RETOS
# ============================================================================

def leer_json(texto):
    """Reto #1: convierte texto JSON en diccionario. Si el JSON es inválido, NO truenes:
    devuelve {"error": "json invalido"}.     (pista: PASO #4 y PASO #5)"""
    # TU CÓDIGO AQUÍ
    return None


def ventas_completadas(ruta):
    """Reto #2: cuántas filas del CSV tienen estado == "COMPLETADA".   (pista: PASO #3)"""
    # TU CÓDIGO AQUÍ
    return None


def total_completadas(ruta):
    """Reto #3: suma del monto de las ventas COMPLETADAS. Recuerda convertir con float()."""
    # TU CÓDIGO AQUÍ
    return None


RETOS = [
    (1, "leer_json con JSON bueno y malo",
     lambda: (leer_json('{"a": 1}'), leer_json("esto no es json")), ({"a": 1}, {"error": "json invalido"})),
    (2, "ventas_completadas cuenta filas del CSV", lambda: ventas_completadas(VENTAS_CSV), 9),
    (3, "total_completadas suma montos", lambda: total_completadas(VENTAS_CSV), 71021.0),
]

if __name__ == "__main__":
    demostracion()
    verificar(RETOS)
