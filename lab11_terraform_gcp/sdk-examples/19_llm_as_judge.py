"""19 · LLM-as-judge: evaluar respuestas abiertas con otro modelo y una rúbrica.

Concepto: para texto libre no existe "exact match". Un modelo juez califica con una rúbrica
explícita y devuelve JSON (puntuación + justificación). Úsalo con un set fijo de preguntas
para comparar prompts o modelos; valida periódicamente al juez contra calificaciones humanas.

    python 19_llm_as_judge.py
"""

from pydantic import BaseModel, Field

from google.genai import types

from common import MODEL, ask, client


class Verdict(BaseModel):
    exactitud: int = Field(ge=1, le=5, description="¿Es técnicamente correcta?")
    completitud: int = Field(ge=1, le=5, description="¿Responde todo lo preguntado?")
    concision: int = Field(ge=1, le=5, description="¿Es breve y clara?")
    justificacion: str


RUBRIC = "Eres un evaluador estricto. Califica de 1 a 5 cada criterio con base en la pregunta y la referencia."
question = "¿Cuál es la diferencia entre Cloud Run y Cloud Run functions?"
reference = "Cloud Run despliega contenedores; Cloud Run functions despliega código fuente y Google construye el contenedor. Ambos escalan a cero."

for system in ["Responde en una línea.", "Responde con mucho detalle técnico."]:
    answer, _ = ask(question, system=system, max_tokens=300)
    judge = client.models.generate_content(
        model=MODEL,
        contents=f"PREGUNTA: {question}\nREFERENCIA: {reference}\nRESPUESTA A EVALUAR: {answer}",
        config=types.GenerateContentConfig(system_instruction=RUBRIC, temperature=0,
                                           response_mime_type="application/json", response_schema=Verdict),
    )
    v: Verdict = judge.parsed
    print(f"Prompt '{system}' -> exactitud {v.exactitud} · completitud {v.completitud} · concisión {v.concision}")
    print(f"   {v.justificacion}\n")
