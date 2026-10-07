"""17 · Code execution: el modelo escribe y ejecuta Python en un sandbox para calcular.

Concepto: los LLM son malos haciendo aritmética "de memoria". Con la herramienta code_execution
el modelo genera código, Google lo ejecuta en un entorno aislado y el modelo usa el resultado real.

    python 17_code_execution.py
"""

from google.genai import types

from common import MODEL, client

response = client.models.generate_content(
    model=MODEL,
    contents=("Un servicio cuesta 0.000024 USD por vCPU-segundo. Corre 3 instancias de 2 vCPU "
              "durante 9 horas al día, 22 días al mes. ¿Cuánto cuesta al mes? Calcúlalo con código."),
    config=types.GenerateContentConfig(tools=[types.Tool(code_execution=types.ToolCodeExecution())]),
)

for part in response.candidates[0].content.parts:
    if part.executable_code:
        print("Código generado:\n", part.executable_code.code)
    if part.code_execution_result:
        print("Resultado de la ejecución:", part.code_execution_result.output)
    if part.text:
        print("Respuesta:", part.text)
