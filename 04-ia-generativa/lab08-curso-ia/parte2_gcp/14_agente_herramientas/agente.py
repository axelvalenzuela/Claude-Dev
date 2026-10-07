"""Micro lab 14 — Un agente = un LLM en un ciclo que puede usar herramientas.

Diferencia clave:
  * Un CHAT responde con lo que ya sabe.
  * Un AGENTE decide qué herramienta necesita, la pide, recibe el resultado,
    y repite hasta tener lo suficiente para responder.

El ciclo (esto es TODO lo que hay detrás de la palabra "agente"):

    PASO #1: mandar la pregunta + la lista de herramientas
    PASO #2: ¿el modelo pidió herramientas?
              sí -> PASO #3: ejecutarlas NOSOTROS y devolverle los resultados -> volver al PASO #2
              no -> es la respuesta final
    Límite de pasos: sin él, un agente confundido puede ciclarse (y gastar) sin fin.

Correr (desde parte2_gcp/):
    python 14_agente_herramientas/agente.py
    python 14_agente_herramientas/agente.py "¿Qué hace clientes.sas?"
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comun.config import config  # noqa: E402
from comun.llm import SesionAgente  # noqa: E402
from herramientas import HERRAMIENTAS  # noqa: E402

MAX_PASOS = 8
SISTEMA = (
    "Eres un agente que evalúa programas SAS para planear su migración a Python/GCP. "
    "Usa las herramientas para obtener datos reales; nunca adivines el contenido de un programa. "
    "Cuando tengas suficiente información, responde en español de forma breve."
)


def ejecutar_agente(pregunta: str) -> str:
    sesion = SesionAgente(SISTEMA, HERRAMIENTAS)
    por_nombre = {f.__name__: f for f in HERRAMIENTAS}

    paso = sesion.enviar(pregunta)                                    # PASO #1
    for numero in range(1, MAX_PASOS + 1):
        if not paso.llamadas:                                         # PASO #2: respuesta final
            return paso.texto or ""
        resultados = []
        for llamada in paso.llamadas:                                 # PASO #3: ejecutar herramientas
            argumentos = json.dumps(llamada.argumentos, ensure_ascii=False)
            print(f"  [paso {numero}] el modelo pide: {llamada.nombre}({argumentos})")
            funcion = por_nombre.get(llamada.nombre)
            try:
                if funcion is None:
                    resultado = f"ERROR: herramienta desconocida {llamada.nombre}"
                else:
                    resultado = funcion(**llamada.argumentos)
            except Exception as e:  # noqa: BLE001 - el error se le devuelve al modelo para que se corrija
                resultado = f"ERROR: {type(e).__name__}: {e}"
            print(f"             resultado: {str(resultado)[:90]}")
            resultados.append((llamada.nombre, resultado))
        paso = sesion.enviar_resultados(resultados)
    return f"Me detuve: se alcanzó el límite de {MAX_PASOS} pasos sin respuesta final."


def main():
    pregunta = " ".join(sys.argv[1:]) or "¿Cuál de los programas SAS es el más complejo de migrar y por qué?"
    print(f"Modo {config.modo}\nPREGUNTA: {pregunta}\n")
    respuesta = ejecutar_agente(pregunta)
    print(f"\nRESPUESTA FINAL:\n{respuesta}")


if __name__ == "__main__":
    main()
