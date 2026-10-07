"""Consumidor push de Pub/Sub. Responder 2xx = ack; cualquier otro código = reintento (y DLQ al agotarse).
Debe ser idempotente: Pub/Sub entrega al menos una vez (usa message_id como llave de idempotencia)."""

import base64
import json
import logging

import functions_framework

logging.basicConfig(level=logging.INFO, format="%(message)s")


@functions_framework.http
def handler(request):
    envelope = request.get_json(silent=True) or {}
    message = envelope.get("message", {})
    order = json.loads(base64.b64decode(message.get("data", "")) or b"{}")
    attempt = envelope.get("deliveryAttempt")

    # Las uniones AVRO en JSON llegan como {"double": 250.0}
    amount = order.get("amount")
    if isinstance(amount, dict):
        amount = next(iter(amount.values()), None)

    logging.info(json.dumps({
        "severity": "INFO",
        "msg": "order received",
        "message_id": message.get("messageId"),
        "order_id": order.get("orderId"),
        "amount": amount,
        "attributes": message.get("attributes"),
        "delivery_attempt": attempt,
    }))

    if amount is None:
        logging.error(json.dumps({"severity": "ERROR", "msg": "orden sin amount", "order_id": order.get("orderId")}))
        return ("orden sin amount", 500)

    return ("", 204)
