"""Configuración compartida por los ejemplos (todo se ajusta con variables de entorno)."""

import json
import math
import os

import boto3

REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL = os.environ.get("BEDROCK_MODEL", "amazon.nova-lite-v1:0")
EMBED_MODEL = os.environ.get("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v2:0")

bedrock = boto3.client("bedrock-runtime", region_name=REGION)


def ask(prompt, system=None, max_tokens=400):
    """Atajo: una pregunta, una respuesta (usado por varios ejemplos)."""
    response = bedrock.converse(
        modelId=MODEL,
        system=[{"text": system}] if system else [],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0.2},
    )
    return response["output"]["message"]["content"][0]["text"], response["usage"]


def embed(text):
    """Vector de 256 dimensiones normalizado (Titan Text Embeddings v2)."""
    body = json.dumps({"inputText": text, "dimensions": 256, "normalize": True})
    response = bedrock.invoke_model(modelId=EMBED_MODEL, body=body)
    return json.loads(response["body"].read())["embedding"]


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))
