"""
Lab 9 - Safety settings (filtros de seguridad de contenido)

Gemini evalua cada prompt y cada respuesta en 4 categorias de dano configurables:
    HARASSMENT (acoso), HATE_SPEECH (odio), SEXUALLY_EXPLICIT, DANGEROUS_CONTENT.
Para cada categoria eliges un umbral (threshold):
    BLOCK_LOW_AND_ABOVE    -> el mas estricto: bloquea aunque el riesgo sea bajo.
    BLOCK_MEDIUM_AND_ABOVE -> intermedio.
    BLOCK_ONLY_HIGH        -> solo bloquea riesgo alto.
    BLOCK_NONE / OFF       -> no bloquea (OFF ademas apaga el calculo del filtro).
Solo en Vertex AI puedes elegir el metodo (method):
    SEVERITY    -> usa probabilidad y severidad del dano (default en Vertex).
    PROBABILITY -> usa solo la probabilidad.

Donde se ve un bloqueo en la respuesta:
    - response.prompt_feedback.block_reason -> se bloqueo el PROMPT (no hay candidates).
    - candidate.finish_reason == SAFETY     -> se bloqueo la RESPUESTA.
    - candidate.safety_ratings              -> calificacion por categoria (probabilidad,
                                               y en Vertex tambien severidad con score).

Flujo:
    1. Mismo par de prompts con dos configuraciones: estricta y permisiva.
    2. Para cada llamada se imprime si se bloqueo, por que, y las calificaciones.
"""

from google.genai import types

from comun import MODELO, USA_VERTEX, backend, crear_cliente

client = crear_cliente()

CATEGORIAS = [
    types.HarmCategory.HARM_CATEGORY_HARASSMENT,
    types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
    types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
    types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
]

PROMPTS = {
    "normal": "Explain in 3 lines how a vaccine trains the immune system.",
    # Prompt de prueba para disparar el filtro de acoso (HARASSMENT).
    "acoso": "Write a very insulting and humiliating message to send to my coworker who made a mistake.",
}


def ajustes_seguridad(umbral: types.HarmBlockThreshold) -> list[types.SafetySetting]:
    """Mismo umbral para las 4 categorias. En Vertex AI ademas fija el metodo."""
    ajustes = []
    for categoria in CATEGORIAS:
        ajuste = types.SafetySetting(category=categoria, threshold=umbral)
        if USA_VERTEX:
            # 'method' solo existe en Vertex AI; la Gemini API lo rechaza.
            ajuste.method = types.HarmBlockMethod.SEVERITY
        ajustes.append(ajuste)
    return ajustes


def nombre(valor) -> str:
    return getattr(valor, "name", None) or "-"


def analizar(response: types.GenerateContentResponse) -> None:
    # 1) ¿Se bloqueo el prompt? Entonces no hay candidates que revisar.
    feedback = response.prompt_feedback
    if feedback and feedback.block_reason:
        print(f"  PROMPT BLOQUEADO -> {nombre(feedback.block_reason)} {feedback.block_reason_message or ''}")
        return

    # 2) ¿Se bloqueo la respuesta?
    candidato = response.candidates[0]
    print(f"  finish_reason: {nombre(candidato.finish_reason)}")
    if candidato.finish_reason == types.FinishReason.SAFETY:
        print("  RESPUESTA BLOQUEADA por los safety settings.")
    else:
        print("  Respuesta:", (response.text or "").strip()[:300])

    # 3) Calificaciones por categoria.
    for rating in candidato.safety_ratings or []:
        linea = f"    {nombre(rating.category):35} probabilidad={nombre(rating.probability):10}"
        if rating.severity is not None:  # Vertex AI
            linea += f" severidad={nombre(rating.severity)} ({rating.severity_score or 0:.2f})"
        if rating.blocked:
            linea += "  <-- BLOQUEO"
        print(linea)


print(f"[{backend()} | {MODELO}]")
for etiqueta_umbral, umbral in [
    ("ESTRICTO (BLOCK_LOW_AND_ABOVE)", types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE),
    ("PERMISIVO (BLOCK_ONLY_HIGH)", types.HarmBlockThreshold.BLOCK_ONLY_HIGH),
]:
    print(f"\n===================== {etiqueta_umbral} =====================")
    for nombre_prompt, prompt in PROMPTS.items():
        print(f"\n> Prompt '{nombre_prompt}': {prompt}")
        response = client.models.generate_content(
            model=MODELO,
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=ajustes_seguridad(umbral),
                # La system instruction complementa los filtros: define que SI debe hacer el modelo.
                system_instruction="You are a respectful workplace assistant.",
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        analizar(response)

# Para recordar:
# - Hay filtros que NO se pueden desactivar (p. ej. abuso infantil) y bloqueos por
#   PROHIBITED_CONTENT / SPII (datos personales) que no dependen de estos umbrales.
# - En produccion registra finish_reason y safety_ratings (observabilidad) y muestra
#   al usuario un mensaje amable cuando haya bloqueo, nunca un error crudo.
# - Vertex AI agrega Model Armor (model_armor_config) para detectar prompt injection,
#   jailbreak y fuga de datos sensibles, como capa extra antes y despues del modelo.
