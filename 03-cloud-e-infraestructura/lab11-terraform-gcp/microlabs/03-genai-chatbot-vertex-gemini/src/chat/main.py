"""Chatbot: Cloud Run function privada -> Vertex AI Gemini (google-genai) con historial en Firestore.

Guardrails en capas:
  1. Validación de entrada (longitud) y lista de temas bloqueados (reglas de negocio baratas, antes del modelo)
  2. System instruction + safety settings de Gemini (BLOCK_LOW_AND_ABOVE en categorías dañinas)
  3. Revisión del finish_reason / prompt_feedback para reportar bloqueos
"""

import base64
import json
import logging
import os
import re
import time
from datetime import datetime, timezone

import functions_framework
from google import genai
from google.cloud import firestore
from google.genai import types

logging.basicConfig(level=logging.INFO, format="%(message)s")

client = genai.Client(vertexai=True, project=os.environ["GOOGLE_CLOUD_PROJECT"], location=os.environ["VERTEX_LOCATION"])
db = firestore.Client(database=os.environ["FIRESTORE_DATABASE"])
messages = db.collection("messages")

MODEL = os.environ["MODEL"]
HISTORY_TURNS = int(os.environ.get("HISTORY_TURNS", "6"))
MAX_TOKENS = int(os.environ.get("MAX_OUTPUT_TOKENS", "512"))
TTL_SECONDS = int(os.environ.get("TTL_HOURS", "24")) * 3600
BLOCKED_TOPICS = [t.strip() for t in os.environ.get("BLOCKED_TOPICS", "").split(",") if t.strip()]
BLOCKED_MESSAGE = "Lo siento, no puedo ayudar con ese tema."

SAFETY = [
    types.SafetySetting(category=c, threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE)
    for c in (
        types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
    )
]

INJECTION = re.compile(r"(ignora|olvida|ignore).{0,40}(instrucciones|instructions|reglas)|system prompt", re.IGNORECASE)


def _history(session_id):
    docs = (messages.where(filter=firestore.FieldFilter("session_id", "==", session_id))
            .order_by("ts", direction=firestore.Query.DESCENDING).limit(HISTORY_TURNS * 2).stream())
    turns = sorted((d.to_dict() for d in docs), key=lambda m: m["ts"])
    return [types.Content(role=m["role"], parts=[types.Part(text=m["text"])]) for m in turns]


def _save(session_id, role, text):
    now = time.time()
    # expires_at es la política TTL de Firestore: el documento se borra solo después de esa fecha
    messages.add({"session_id": session_id, "role": role, "text": text, "ts": now,
                  "expires_at": datetime.fromtimestamp(now + TTL_SECONDS, tz=timezone.utc)})


def _caller_email(authorization):
    try:
        payload = authorization.split(" ", 1)[1].split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload)).get("email", "anon")
    except (IndexError, ValueError):
        return "anon"


def _reply(status, body):
    return (json.dumps(body, ensure_ascii=False), status, {"Content-Type": "application/json"})


@functions_framework.http
def handler(request):
    body = request.get_json(silent=True) or {}
    message = (body.get("message") or "").strip()
    if not message or len(message) > 4000:
        return _reply(400, {"error": "message es requerido (máx. 4000 caracteres)"})

    # Cloud Run ya VERIFICÓ el ID token (IAM invoker) antes de llegar aquí; solo leemos el email.
    caller = _caller_email(request.headers.get("Authorization", ""))
    session_id = f"{caller}#{body.get('session', 'default')}"

    # Capa 1: reglas de negocio antes de gastar tokens
    lowered = message.lower()
    if any(t in lowered for t in BLOCKED_TOPICS) or INJECTION.search(message):
        logging.info(json.dumps({"severity": "WARNING", "msg": "guardrail de entrada", "caller": caller}))
        return _reply(200, {"answer": BLOCKED_MESSAGE, "blocked": True, "reason": "input_guardrail"})

    contents = _history(session_id) + [types.Content(role="user", parts=[types.Part(text=message)])]
    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=os.environ["SYSTEM_INSTRUCTION"],
            max_output_tokens=MAX_TOKENS,
            temperature=0.3,
            safety_settings=SAFETY,
        ),
    )

    usage = response.usage_metadata
    finish = response.candidates[0].finish_reason.name if response.candidates else "BLOCKED"
    blocked = finish in ("SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "BLOCKED") or response.prompt_feedback is not None
    answer = BLOCKED_MESSAGE if blocked else response.text

    logging.info(json.dumps({
        "severity": "INFO", "caller": caller, "model": MODEL, "finish_reason": finish,
        "input_tokens": usage.prompt_token_count if usage else None,
        "output_tokens": usage.candidates_token_count if usage else None,
    }))

    if not blocked:
        _save(session_id, "user", message)
        _save(session_id, "model", answer)

    return _reply(200, {
        "answer": answer,
        "blocked": blocked,
        "finish_reason": finish,
        "usage": {"input_tokens": getattr(usage, "prompt_token_count", None), "output_tokens": getattr(usage, "candidates_token_count", None)},
    })
