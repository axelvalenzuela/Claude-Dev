"""10 · Publicar eventos en Pub/Sub (integra el micro lab 02).

Concepto: un servicio de IA publica su resultado como evento y los consumidores reaccionan.
El topic del lab 02 tiene un schema AVRO: Pub/Sub RECHAZA mensajes que no lo cumplan.

    export ORDERS_TOPIC=$(terraform -chdir=../microlabs/02-events-pubsub-scheduler output -raw topic)
    python 10_pubsub_publicar.py
"""

import json
import os
import uuid

from google.api_core.exceptions import InvalidArgument
from google.cloud import pubsub_v1

publisher = pubsub_v1.PublisherClient()
topic = publisher.topic_path(os.environ["GOOGLE_CLOUD_PROJECT"], os.environ["ORDERS_TOPIC"])

# En JSON de AVRO las uniones se envían como {"tipo": valor}
order = {"orderId": f"SDK-{uuid.uuid4().hex[:6]}", "customer": "c-sdk", "amount": {"double": 1500.0}, "run": None}
future = publisher.publish(topic, json.dumps(order).encode(), tier="high")   # atributo usado por el filtro
print("Publicado:", order["orderId"], "· message id:", future.result())

try:
    publisher.publish(topic, json.dumps({"customer": "sin orderId"}).encode()).result()
except InvalidArgument as error:
    print("Rechazado por el schema (esperado):", str(error)[:100])
