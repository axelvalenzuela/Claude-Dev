"""10 · Disparar el pipeline de IA del lab 05 y esperar el resultado.

Concepto: los procesos de IA largos (OCR + entidades + resumen) se orquestan como flujos
asíncronos. El cliente sube el archivo y consulta el estado, no espera una respuesta HTTP.

    export DOCS_BUCKET=$(terraform -chdir=../microlabs/05-genai-docs-stepfunctions output -raw documents_bucket)
    export RESULTS_TABLE=$(terraform -chdir=../microlabs/05-genai-docs-stepfunctions output -raw results_table)
    python 10_stepfunctions_documento.py
"""

import os
import time

import boto3

region = os.environ.get("AWS_REGION", "us-east-1")
s3 = boto3.client("s3", region_name=region)
table = boto3.resource("dynamodb", region_name=region).Table(os.environ["RESULTS_TABLE"])

key = f"incoming/sdk-{int(time.time())}.txt"
s3.put_object(Bucket=os.environ["DOCS_BUCKET"], Key=key,
              Body="Google y AWS abrieron oficinas en Monterrey en 2026, dijo la directora Laura Pérez.".encode())
print("Subido:", key)

for _ in range(30):
    item = table.get_item(Key={"document_id": key}).get("Item")
    if item:
        print("\nResumen:\n", item["summary"])
        print("\nEntidades:", item["entities"][:300])
        break
    print(".", end="", flush=True)
    time.sleep(5)
else:
    print("\nNo terminó en 150 s: revisa la consola de Step Functions")
