"""Cliente de Neptune: consultas openCypher y bulk loader, firmados con SigV4 (IAM database auth).

Eventos de prueba:
  {"action": "load"}
  {"action": "load_status", "load_id": "<id>"}
  {"action": "query", "query": "MATCH (p:Person)-[:FRIEND]->(f) RETURN p.name, f.name LIMIT 10"}
"""

import json
import os

import boto3
import urllib3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

ENDPOINT = f"https://{os.environ['NEPTUNE_ENDPOINT']}:{os.environ['NEPTUNE_PORT']}"
REGION = os.environ["AWS_REGION"]
http = urllib3.PoolManager()


def _signed(method, path, body=None, params=None):
    url = ENDPOINT + path
    data = json.dumps(body) if body is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    request = AWSRequest(method=method, url=url, data=data, params=params, headers=headers)
    SigV4Auth(boto3.Session().get_credentials(), "neptune-db", REGION).add_auth(request)
    prepared = request.prepare()
    response = http.request(method, prepared.url, body=data, headers=dict(prepared.headers))
    return json.loads(response.data.decode() or "{}")


def handler(event, context):
    action = event.get("action", "query")

    if action == "query":
        return _signed("POST", "/openCypher", body={"query": event["query"]})

    if action == "load":
        return _signed("POST", "/loader", body={
            "source": os.environ["LOAD_SOURCE"],
            "format": "opencypher",
            "iamRoleArn": os.environ["LOADER_ROLE_ARN"],
            "region": REGION,
            "failOnError": "TRUE",
            "parallelism": "MEDIUM",
        })

    if action == "load_status":
        return _signed("GET", f"/loader/{event['load_id']}")

    return {"error": f"acción desconocida: {action}"}
