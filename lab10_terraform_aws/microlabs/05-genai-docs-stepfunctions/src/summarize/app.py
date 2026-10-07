"""Resume texto con Bedrock Converse API (agnóstico al modelo)."""

import os

import boto3

bedrock = boto3.client("bedrock-runtime")


def handler(event, context):
    result = bedrock.converse(
        modelId=os.environ["MODEL_ID"],
        system=[{"text": "Resume documentos en español en máximo 5 viñetas. No inventes datos."}],
        messages=[{"role": "user", "content": [{"text": event["text"]}]}],
        inferenceConfig={"maxTokens": int(os.environ.get("MAX_TOKENS", "300")), "temperature": 0.2},
    )
    return {"summary": result["output"]["message"]["content"][0]["text"]}
