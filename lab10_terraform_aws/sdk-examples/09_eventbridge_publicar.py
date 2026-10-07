"""09 · Publicar eventos (integra el micro lab 03): desacoplar la IA del resto del sistema.

Concepto: un servicio de IA que clasifica un pedido no llama directo a los demás sistemas:
publica un evento y cada consumidor reacciona. Aquí se publica al bus del lab 03.

    export EVENT_BUS=$(terraform -chdir=../microlabs/03-events-eventbridge-sqs output -raw event_bus_name)
    python 09_eventbridge_publicar.py
"""

import json
import os
import uuid

import boto3

events = boto3.client("events", region_name=os.environ.get("AWS_REGION", "us-east-1"))

order = {"orderId": f"SDK-{uuid.uuid4().hex[:6]}", "amount": 1500, "customer": "c-sdk"}

response = events.put_events(Entries=[{
    "Source": "com.lab10.orders",
    "DetailType": "order.created",
    "Detail": json.dumps(order),
    "EventBusName": os.environ["EVENT_BUS"],
}])

print("Publicado:", order, "· fallidos:", response["FailedEntryCount"])
print("Como amount >= 1000, revisa también la cola high-value del lab 03.")
