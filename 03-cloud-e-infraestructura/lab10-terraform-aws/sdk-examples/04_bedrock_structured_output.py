"""04 · Salida estructurada (JSON validado) a partir de texto libre.

Concepto: para integrar un LLM con sistemas necesitas JSON con un esquema fijo, no prosa.
Truco: definir una "herramienta" con el esquema y FORZAR al modelo a usarla (toolChoice).

    python 04_bedrock_structured_output.py
"""

import json

from common import MODEL, bedrock

ticket = "Hola, soy Ana de Mexicali. Desde ayer la app de pagos me da error 500 al pagar con tarjeta. Es urgente."

schema = {"type": "object", "required": ["cliente", "ciudad", "producto", "severidad", "resumen"], "properties": {
    "cliente": {"type": "string"},
    "ciudad": {"type": "string"},
    "producto": {"type": "string"},
    "severidad": {"type": "string", "enum": ["baja", "media", "alta"]},
    "resumen": {"type": "string", "description": "máximo 15 palabras"},
}}

response = bedrock.converse(
    modelId=MODEL,
    messages=[{"role": "user", "content": [{"text": f"Clasifica este ticket de soporte:\n{ticket}"}]}],
    toolConfig={
        "tools": [{"toolSpec": {"name": "registrar_ticket", "description": "Registra el ticket clasificado",
                                "inputSchema": {"json": schema}}}],
        "toolChoice": {"tool": {"name": "registrar_ticket"}},   # obliga a responder con este esquema
    },
)

data = next(b["toolUse"]["input"] for b in response["output"]["message"]["content"] if "toolUse" in b)
print(json.dumps(data, indent=2, ensure_ascii=False))
assert data["severidad"] in ("baja", "media", "alta")
