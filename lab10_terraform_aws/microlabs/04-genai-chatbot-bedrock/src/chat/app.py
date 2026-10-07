"""Chatbot: HTTP API (payload v2) -> Bedrock Converse API con guardrail e historial en DynamoDB."""

import json
import logging
import os
import time

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel("INFO")

bedrock = boto3.client("bedrock-runtime")
table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])

MODEL_ID = os.environ["MODEL_ID"]
HISTORY_TURNS = int(os.environ.get("HISTORY_TURNS", "6"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "512"))
TTL_SECONDS = int(os.environ.get("TTL_HOURS", "24")) * 3600


def _load_history(session_id):
    result = table.query(
        KeyConditionExpression=Key("session_id").eq(session_id),
        ScanIndexForward=False,
        Limit=HISTORY_TURNS * 2,
    )
    items = sorted(result["Items"], key=lambda i: i["ts"])
    return [{"role": i["role"], "content": [{"text": i["text"]}]} for i in items]


def _save(session_id, role, text):
    now = time.time()
    table.put_item(Item={
        "session_id": session_id,
        "ts": int(now * 1000),
        "role": role,
        "text": text,
        "expires_at": int(now) + TTL_SECONDS,
    })


def _response(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body, ensure_ascii=False)}


def handler(event, context):
    user = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    body = json.loads(event.get("body") or "{}")
    message = (body.get("message") or "").strip()
    if not message or len(message) > 4000:
        return _response(400, {"error": "message es requerido (máx. 4000 caracteres)"})

    # La sesión se liga al usuario autenticado: nadie puede leer el historial de otro.
    session_id = f"{user}#{body.get('session', 'default')}"
    messages = _load_history(session_id) + [{"role": "user", "content": [{"text": message}]}]

    result = bedrock.converse(
        modelId=MODEL_ID,
        system=[{"text": os.environ["SYSTEM_PROMPT"]}],
        messages=messages,
        inferenceConfig={"maxTokens": MAX_TOKENS, "temperature": 0.3},
        guardrailConfig={
            "guardrailIdentifier": os.environ["GUARDRAIL_ID"],
            "guardrailVersion": os.environ["GUARDRAIL_VERSION"],
        },
    )

    answer = result["output"]["message"]["content"][0]["text"]
    usage = result.get("usage", {})
    logger.info(json.dumps({
        "user": user,
        "stop_reason": result.get("stopReason"),
        "input_tokens": usage.get("inputTokens"),
        "output_tokens": usage.get("outputTokens"),
        "latency_ms": result.get("metrics", {}).get("latencyMs"),
    }))

    if result.get("stopReason") != "guardrail_intervened":
        _save(session_id, "user", message)
        _save(session_id, "assistant", answer)

    return _response(200, {"answer": answer, "stop_reason": result.get("stopReason"), "usage": usage})
