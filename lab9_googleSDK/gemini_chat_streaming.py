"""
Lab 9 - Chat multiturno y streaming

    - client.chats.create(...)  guarda el historial: cada mensaje nuevo incluye los anteriores
      (por eso el costo de entrada crece con cada turno).
    - send_message_stream(...)  devuelve la respuesta por pedazos (chunks) conforme se genera:
      el usuario ve texto en menos de un segundo aunque la respuesta completa tarde mas.
"""

from google.genai import types

from comun import MODELO, crear_cliente

client = crear_cliente()

chat = client.chats.create(
    model=MODELO,
    config=types.GenerateContentConfig(
        system_instruction="You are a Marvel expert. Answer in Spanish, max 5 lines.",
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    ),
)

# Turno 1: respuesta completa
respuesta = chat.send_message("¿Quién es Miles Morales?")
print("Usuario: ¿Quién es Miles Morales?\nGemini:", respuesta.text)

# Turno 2: el modelo recuerda de quién hablamos (historial) y respondemos en streaming
print("\nUsuario: ¿En qué película animada aparece?\nGemini: ", end="")
for chunk in chat.send_message_stream("¿En qué película animada aparece?"):
    print(chunk.text or "", end="", flush=True)

print(f"\n\nMensajes en el historial: {len(chat.get_history())}")
