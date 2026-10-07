"""01 · Primera llamada a un LLM con la Converse API de Bedrock.

Concepto: la Converse API usa el MISMO formato para todos los modelos de Bedrock
(Nova, Claude, Llama, Mistral...). Cambiar de modelo = cambiar BEDROCK_MODEL.
Observa: el texto, el motivo de parada (stopReason) y los tokens (lo que pagas).

    python 01_bedrock_converse.py
"""

from common import MODEL, bedrock

response = bedrock.converse(
    modelId=MODEL,
    system=[{"text": "Eres un tutor de cloud. Responde en español en máximo 3 líneas."}],
    messages=[{"role": "user", "content": [{"text": "¿Qué es una función serverless?"}]}],
    inferenceConfig={"maxTokens": 200, "temperature": 0.3},
)

print("Respuesta:", response["output"]["message"]["content"][0]["text"])
print("stopReason:", response["stopReason"])            # end_turn | max_tokens | guardrail_intervened...
print("Tokens:", response["usage"])                      # inputTokens, outputTokens, totalTokens
print("Latencia (ms):", response["metrics"]["latencyMs"])
