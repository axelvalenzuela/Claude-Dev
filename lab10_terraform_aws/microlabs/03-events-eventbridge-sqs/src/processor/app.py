"""Consumidor de eventos order.created. Debe ser idempotente: EventBridge entrega al menos una vez."""

import json
import logging

logger = logging.getLogger()
logger.setLevel("INFO")


def handler(event, context):
    detail = event.get("detail", {})
    logger.info(json.dumps({
        "msg": "order received",
        "event_id": event.get("id"),  # úsalo como llave de idempotencia
        "order_id": detail.get("orderId"),
        "amount": detail.get("amount"),
    }))
    if detail.get("amount") is None:
        # Un error aquí dispara reintentos y, al agotarse, el evento termina en la DLQ.
        raise ValueError("evento sin amount")
    return {"status": "processed", "orderId": detail.get("orderId")}
