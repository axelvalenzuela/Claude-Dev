"""Lab 9 - Thinking: cuanto "piensa" el modelo antes de responder y cuanto cuesta."""

from google.genai import types

from comun import MODELO, crear_cliente

client = crear_cliente()
prompt = "A train leaves at 9:40 and arrives at 13:15. If it stopped 3 times for 7 minutes, how long was it moving?"

# thinking_budget = cuántos tokens máximo puede usar el modelo para "pensar" antes de responder.
#   0          -> thinking apagado. Respuesta más rápida y barata, por eso
#                 thoughts_token_count sale None (no hubo razonamiento que contar).
#   -1         -> dinámico (default): el modelo decide cuánto pensar según la dificultad.
#   1 a 24576  -> límite fijo (gemini-2.5-flash). Es un TOPE, no una meta: en prompts
#                 simples puede usar menos. Más budget = mejor razonamiento en tareas
#                 complejas, pero más latencia y costo (los thoughts se cobran como salida).
# Notas:
#   - gemini-2.5-pro no permite apagarlo (mínimo 128).
#   - Los modelos Gemini 3 usan thinking_level ("low" / "high") en lugar de thinking_budget.
#   - include_thoughts=True devuelve un RESUMEN del razonamiento (parte con part.thought=True).
for budget in (0, 1024):
    response = client.models.generate_content(
        model=MODELO,
        contents=prompt,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=budget, include_thoughts=budget > 0),
            # max_output_tokens va DENTRO del config. Ojo: en modelos con thinking,
            # los tokens de razonamiento también cuentan contra este límite.
            max_output_tokens=2048,
        ),
    )

    print(f"\n===== thinking_budget={budget} =====")
    for part in response.candidates[0].content.parts:
        if not part.text:
            continue
        etiqueta = "[resumen del razonamiento]" if part.thought else "[respuesta]"
        print(f"{etiqueta}\n{part.text.strip()}\n")

    # usage_metadata: desglose de tokens cobrados en la llamada.
    #   prompt_token_count     -> entrada (el prompt).
    #   candidates_token_count -> salida visible (response.text).
    #   thoughts_token_count   -> razonamiento interno; None si thinking_budget=0.
    #   total_token_count      -> entrada + salida + razonamiento.
    uso = response.usage_metadata
    print("Total tokens:", uso.total_token_count)
    print("Candidate token count:", uso.candidates_token_count)
    print("Thought tokens count:", uso.thoughts_token_count)
    print("Input tokens count:", uso.prompt_token_count)
