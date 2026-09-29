"""El mismo flujo multi-agente, pero con Google ADK (Agent Development Kit).

En comun/orquestador.py escribimos el ciclo a mano (para entenderlo). Un
framework como ADK te da esas piezas hechas:

    SequentialAgent  corre sub-agentes en orden        (analista -> ciclo -> documentador)
    LoopAgent        repite sub-agentes hasta que uno "escala" o se llega a max_iterations
    output_key       guarda la respuesta de un agente en el estado compartido de la sesión
    {analisis}       dentro de una instrucción, se reemplaza por ese estado

Solo funciona con Vertex AI real (no hay modo simulado). Correr desde
15_multi_agente/ con:   adk web     (interfaz en el navegador)
                  o:    adk run adk_migracion
Ver 15_multi_agente/INSTRUCCIONES.md, sección "Versión con ADK".
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # parte2_gcp/, para importar comun/
from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent  # noqa: E402
from google.adk.tools import ToolContext  # noqa: E402

from comun.agentes import SISTEMA_ANALISTA, SISTEMA_CONVERTIDOR, SISTEMA_DOCUMENTADOR  # noqa: E402
from comun.guardrails import extraer_bloque_codigo  # noqa: E402
from comun.orquestador import CASOS  # noqa: E402
from comun.validacion import ejecutar_y_comparar  # noqa: E402

MODELO = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")


def validar_codigo(codigo_python: str, tool_context: ToolContext) -> dict:
    """Ejecuta el código Python propuesto contra los datos de prueba de ventas.sas
    y compara con la salida original de SAS. Úsala con el código COMPLETO."""
    caso = CASOS["ventas.sas"]
    resultado = ejecutar_y_comparar(extraer_bloque_codigo(codigo_python), caso.entrada_csv, caso.esperado_csv)
    if resultado.ok:
        tool_context.actions.escalate = True     # <- esto termina el LoopAgent
    return {"ok": resultado.ok, "problemas": resultado.problemas}


analista = LlmAgent(
    name="analista",
    model=MODELO,
    instruction=SISTEMA_ANALISTA + " Responde en JSON con resumen, tablas y lista de reglas.",
    output_key="analisis",
)

convertidor = LlmAgent(
    name="convertidor",
    model=MODELO,
    instruction=SISTEMA_CONVERTIDOR
    + "\nAnálisis de reglas: {analisis}\n"
    "Columnas de salida esperadas: region, categoria, num_ventas, total.\n"
    "Si en la conversación hay problemas reportados por el validador, corrígelos.",
    output_key="codigo_python",
)

validador = LlmAgent(
    name="validador",
    model=MODELO,
    instruction="Llama a validar_codigo con este código exacto: {codigo_python}\n"
    "Después resume en una línea si pasó o qué problemas hubo.",
    tools=[validar_codigo],
)

ciclo_conversion = LoopAgent(name="ciclo_conversion", sub_agents=[convertidor, validador], max_iterations=3)

documentador = LlmAgent(
    name="documentador",
    model=MODELO,
    instruction=SISTEMA_DOCUMENTADOR + "\nAnálisis: {analisis}\nCódigo final: {codigo_python}",
)

# ADK busca una variable llamada root_agent en agent.py
root_agent = SequentialAgent(name="migracion_sas", sub_agents=[analista, ciclo_conversion, documentador])
