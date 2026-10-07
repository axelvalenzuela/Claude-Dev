"""Paso 3 · Batch prediction: clasificar muchos tickets de forma asíncrona (~50 % más barato que online).

Entrada: JSONL en GCS con una petición por línea {"request": {...GenerateContentRequest...}}
Salida:  JSONL en GCS con la respuesta de cada petición.

    python scripts/batch.py
"""

import json
import time

from google.cloud import storage
from google.genai import types

from common import BASE_MODEL, BUCKET, INSTRUCTION, PROJECT, client

tickets = [
    "Me llegó doble cargo en mi tarjeta este mes",
    "La aplicación se cierra sola al abrir reportes",
    "Quiero contratar 40 licencias más para mi empresa",
    "Cancelen mi suscripción por favor, ya no la uso",
    "No me deja recuperar mi contraseña, error 403",
]

bucket = storage.Client(project=PROJECT).bucket(BUCKET)
lines = [json.dumps({"request": {
    "systemInstruction": {"parts": [{"text": INSTRUCTION}]},
    "contents": [{"role": "user", "parts": [{"text": t}]}],
    "generationConfig": {"temperature": 0, "maxOutputTokens": 10},
}}, ensure_ascii=False) for t in tickets]
bucket.blob("datasets/batch_input.jsonl").upload_from_string("\n".join(lines))

job = client.batches.create(
    model=BASE_MODEL,
    src=f"gs://{BUCKET}/datasets/batch_input.jsonl",
    config=types.CreateBatchJobConfig(dest=f"gs://{BUCKET}/outputs/batch/"),
)
print("Batch job:", job.name)

while job.state.name not in ("JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED"):
    time.sleep(30)
    job = client.batches.get(name=job.name)
    print("Estado:", job.state.name)

prefix = job.dest.gcs_uri.replace(f"gs://{BUCKET}/", "")
for blob in bucket.list_blobs(prefix=prefix):
    if blob.name.endswith(".jsonl"):
        for line in blob.download_as_text().splitlines():
            row = json.loads(line)
            ticket = row["request"]["contents"][0]["parts"][0]["text"]
            label = row["response"]["candidates"][0]["content"]["parts"][0]["text"].strip()
            print(f"{label:16} <- {ticket}")
