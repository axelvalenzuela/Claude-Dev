"""12 · Chat multi-turno: el SDK guarda el historial por ti.

Concepto: los modelos no tienen memoria; cada turno se reenvía el historial completo
(por eso el costo crece con la conversación). client.chats lo administra automáticamente.

    python 12_chat_multiturno.py
"""

from google.genai import types

from common import MODEL, client

chat = client.chats.create(
    model=MODEL,
    config=types.GenerateContentConfig(system_instruction="Eres un mentor de cloud. Respuestas de 1-2 líneas."),
)

for message in ["Me llamo Axel y voy a migrar una API a Cloud Run.",
                "¿Qué servicio uso para guardar secretos?",
                "¿Cómo me llamo y qué voy a migrar?"]:
    response = chat.send_message(message)
    print(f"> {message}\n{response.text}  [entrada: {response.usage_metadata.prompt_token_count} tokens]\n")

print("Turnos en el historial:", len(chat.get_history()))   # el prompt crece en cada turno
