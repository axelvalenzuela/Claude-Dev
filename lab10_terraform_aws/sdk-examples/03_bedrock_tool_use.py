"""03 · Tool use (function calling): el modelo decide llamar a TU código.

Concepto clave de los agentes: el modelo no ejecuta nada. Devuelve stopReason="tool_use"
con el nombre y los argumentos; tu código ejecuta la función y le devuelve el resultado.

    python 03_bedrock_tool_use.py
"""

from common import MODEL, bedrock

# 1. Tu función real (aquí simulada)
def precio_instancia(tipo: str) -> dict:
    precios = {"t4g.micro": 0.0084, "t4g.small": 0.0168, "m7g.large": 0.0816}
    return {"tipo": tipo, "usd_por_hora": precios.get(tipo, "desconocido")}


# 2. Su descripción para el modelo (JSON Schema)
tools = {"tools": [{"toolSpec": {
    "name": "precio_instancia",
    "description": "Devuelve el precio por hora de un tipo de instancia EC2 en us-east-1.",
    "inputSchema": {"json": {"type": "object", "properties": {"tipo": {"type": "string"}}, "required": ["tipo"]}},
}}]}

messages = [{"role": "user", "content": [{"text": "¿Cuánto cuesta al mes (730 h) una t4g.small?"}]}]

# 3. Bucle de agente: llamar al modelo hasta que deje de pedir herramientas
while True:
    response = bedrock.converse(modelId=MODEL, messages=messages, toolConfig=tools)
    message = response["output"]["message"]
    messages.append(message)

    if response["stopReason"] != "tool_use":
        print("Respuesta final:", message["content"][0]["text"])
        break

    for block in message["content"]:
        if "toolUse" in block:
            call = block["toolUse"]
            result = precio_instancia(**call["input"])
            print(f"-> El modelo llamó {call['name']}({call['input']}) = {result}")
            messages.append({"role": "user", "content": [
                {"toolResult": {"toolUseId": call["toolUseId"], "content": [{"json": result}]}}]})
