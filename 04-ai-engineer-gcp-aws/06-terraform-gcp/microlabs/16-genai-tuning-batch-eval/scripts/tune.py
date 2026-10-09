"""Paso 2 · Supervised fine-tuning (SFT) de Gemini con el dataset de tickets.

COSTO: se cobra por tokens de entrenamiento (tokens del dataset x épocas). Revisa la página de precios.
Tarda ~20-60 min. El modelo ajustado queda desplegado en un endpoint de tu proyecto.

    python scripts/tune.py            # lanza y espera
    python scripts/tune.py --no-wait  # solo lanza
"""

import sys
import time

from google.genai import types

from common import BASE_MODEL, BUCKET, client

job = client.tunings.tune(
    base_model=BASE_MODEL,
    training_dataset=types.TuningDataset(gcs_uri=f"gs://{BUCKET}/datasets/train.jsonl"),
    config=types.CreateTuningJobConfig(
        tuned_model_display_name="aie-clasificador-tickets",
        validation_dataset=types.TuningValidationDataset(gcs_uri=f"gs://{BUCKET}/datasets/validation.jsonl"),
        epoch_count=3,                 # pocas épocas: dataset pequeño y tarea sencilla
        learning_rate_multiplier=1.0,
        adapter_size="ADAPTER_SIZE_FOUR",  # LoRA: más grande = más capacidad y más costo
    ),
)
print("Tuning job:", job.name)

if "--no-wait" in sys.argv:
    sys.exit(0)

while not job.has_ended:
    time.sleep(60)
    job = client.tunings.get(name=job.name)
    print("Estado:", job.state)

print("Estado final:", job.state)
if job.tuned_model:
    print("Endpoint del modelo ajustado:", job.tuned_model.endpoint)
    print(f"Úsalo así:  export TUNED_MODEL={job.tuned_model.endpoint}")
