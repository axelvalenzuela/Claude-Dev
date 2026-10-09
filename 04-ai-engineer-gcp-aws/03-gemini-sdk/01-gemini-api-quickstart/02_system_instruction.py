"""02 · System instruction: darle al modelo un rol y reglas ANTES del prompt del usuario.

La system instruction no es "un mensaje más": el modelo la trata como contexto de mayor
prioridad. Úsala para rol, tono, formato y límites ("si no sabes, dilo").

Correr:  python 02_system_instruction.py
"""
import os

from google import genai
from google.genai import types

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
client = genai.Client()

SYSTEM = (
    "Eres un arquitecto de soluciones de Google Cloud. Respondes en español, en máximo "
    "5 viñetas, y siempre mencionas un riesgo o costo a vigilar."
)
prompt = "¿Cuándo uso Cloud Run y cuándo GKE para servir un modelo?"

# PASO 1: compara la misma pregunta con y sin system instruction.
for etiqueta, config in [
    ("SIN system instruction", None),
    ("CON system instruction", types.GenerateContentConfig(system_instruction=SYSTEM, temperature=0.2)),
]:
    response = client.models.generate_content(model=MODEL, contents=prompt, config=config)
    print(f"\n===== {etiqueta} =====\n{response.text}")
