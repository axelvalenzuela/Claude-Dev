"""CRUD de items sobre Firestore, expuesto detrás de API Gateway (path_translation APPEND_PATH_TO_ADDRESS)."""

import json
import logging
import os
import uuid

import functions_framework
from google.cloud import firestore

logging.basicConfig(level=logging.INFO, format="%(message)s")
db = firestore.Client(database=os.environ["FIRESTORE_DATABASE"])
items = db.collection("items")

ALLOWED = {"name": str, "description": str, "price": (int, float)}


def _json(status, body=None):
    return (json.dumps(body, default=str) if body is not None else "", status, {"Content-Type": "application/json"})


def _validate(payload):
    """ESPv2 no valida cuerpos contra el esquema: se valida aquí (defensa en profundidad)."""
    if not isinstance(payload, dict) or "name" not in payload:
        return "name es requerido"
    for key, value in payload.items():
        if key not in ALLOWED:
            return f"campo no permitido: {key}"
        if not isinstance(value, ALLOWED[key]):
            return f"tipo inválido en {key}"
    if not 0 < len(payload["name"]) <= 100:
        return "name debe tener 1-100 caracteres"
    if payload.get("price", 0) < 0:
        return "price debe ser >= 0"
    return None


@functions_framework.http
def handler(request):
    # API Gateway agrega el path después de la URL de la función: /items, /items/<id>, /health
    parts = [p for p in request.path.split("/") if p]
    trace = request.headers.get("X-Cloud-Trace-Context", "")
    logging.info(json.dumps({"severity": "INFO", "method": request.method, "path": request.path, "trace": trace}))

    if parts == ["health"]:
        return _json(200, {"status": "ok"})

    # Inyección de fallas para prácticas de SLO (lab 07): solo si el lab la habilita explícitamente
    if os.environ.get("FAULT_INJECTION") == "enabled" and request.headers.get("x-fault-injection"):
        logging.error(json.dumps({"severity": "ERROR", "msg": "falla inyectada", "trace": trace}))
        return _json(500, {"message": "falla inyectada"})

    if not parts or parts[0] != "items":
        return _json(404, {"message": "not found"})

    item_id = parts[1] if len(parts) > 1 else None

    if request.method == "GET" and item_id:
        doc = items.document(item_id).get()
        return _json(200, {"id": doc.id, **doc.to_dict()}) if doc.exists else _json(404, {"message": "not found"})

    if request.method == "GET":
        docs = items.order_by("created_at", direction=firestore.Query.DESCENDING).limit(50).stream()
        return _json(200, {"items": [{"id": d.id, **d.to_dict()} for d in docs]})

    if request.method == "POST":
        payload = request.get_json(silent=True)
        error = _validate(payload)
        if error:
            return _json(400, {"message": error})
        new_id = str(uuid.uuid4())
        items.document(new_id).set({**payload, "created_at": firestore.SERVER_TIMESTAMP})
        return _json(201, {"id": new_id, **payload})

    if request.method == "DELETE" and item_id:
        items.document(item_id).delete()
        return _json(204)

    return _json(405, {"message": "method not allowed"})
