"""CRUD de items sobre DynamoDB para API Gateway (integración Lambda proxy)."""

import json
import logging
import os
import uuid
from decimal import Decimal

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])


def _response(status, body=None):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": "" if body is None else json.dumps(body, default=lambda o: float(o) if isinstance(o, Decimal) else str(o)),
    }


def handler(event, context):
    method = event["httpMethod"]
    item_id = (event.get("pathParameters") or {}).get("id")
    # El usuario autenticado viene del Cognito authorizer: permite aislar datos por usuario.
    user = event["requestContext"].get("authorizer", {}).get("claims", {}).get("sub", "anonymous")
    logger.info({"method": method, "item_id": item_id, "user": user, "request_id": context.aws_request_id})

    # Inyección de fallas para prácticas SRE (micro lab 07): solo si el lab la habilita explícitamente.
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    if os.environ.get("FAULT_INJECTION") == "enabled" and headers.get("x-fault-injection"):
        raise RuntimeError("Falla inyectada (x-fault-injection)")

    if method == "GET" and item_id:
        result = table.get_item(Key={"pk": f"USER#{user}", "sk": f"ITEM#{item_id}"})
        return _response(200, result["Item"]) if "Item" in result else _response(404, {"message": "not found"})

    if method == "GET":
        result = table.query(
            KeyConditionExpression="pk = :pk AND begins_with(sk, :sk)",
            ExpressionAttributeValues={":pk": f"USER#{user}", ":sk": "ITEM#"},
            Limit=50,
        )
        return _response(200, {"items": result["Items"]})

    if method == "POST":
        payload = json.loads(event["body"], parse_float=Decimal)
        new_id = str(uuid.uuid4())
        item = {"pk": f"USER#{user}", "sk": f"ITEM#{new_id}", "id": new_id, **payload}
        table.put_item(Item=item)
        return _response(201, item)

    if method == "DELETE" and item_id:
        table.delete_item(Key={"pk": f"USER#{user}", "sk": f"ITEM#{item_id}"})
        return _response(204)

    return _response(405, {"message": "method not allowed"})
