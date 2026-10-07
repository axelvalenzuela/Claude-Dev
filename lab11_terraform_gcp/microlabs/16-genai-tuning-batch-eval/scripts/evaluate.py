"""Paso 4 · Evaluación: modelo base (zero-shot) vs modelo ajustado sobre el set de validación.

Métricas: exactitud (exact match), exactitud por etiqueta, tokens y latencia media.
Así se decide con datos si el fine-tuning vale su costo.

    python scripts/evaluate.py                         # solo el modelo base
    TUNED_MODEL=projects/.../endpoints/... python scripts/evaluate.py
"""

import json
import os
import time
from collections import Counter

from google.cloud import storage
from google.genai import types

from common import BASE_MODEL, BUCKET, INSTRUCTION, LABELS, PROJECT, client

LIMIT = int(os.environ.get("EVAL_LIMIT", "40"))
rows = [json.loads(line) for line in
        storage.Client(project=PROJECT).bucket(BUCKET).blob("datasets/validation.jsonl").download_as_text().splitlines()][:LIMIT]
cases = [(r["contents"][0]["parts"][0]["text"], r["contents"][1]["parts"][0]["text"]) for r in rows]


def evaluate(model):
    correct, per_label, total_label, tokens, latency = 0, Counter(), Counter(), 0, 0.0
    for text, expected in cases:
        start = time.perf_counter()
        response = client.models.generate_content(
            model=model, contents=text,
            config=types.GenerateContentConfig(system_instruction=INSTRUCTION, temperature=0, max_output_tokens=10,
                                               thinking_config=types.ThinkingConfig(thinking_budget=0)))
        latency += time.perf_counter() - start
        predicted = (response.text or "").strip().lower()
        total_label[expected] += 1
        if predicted == expected:
            correct += 1
            per_label[expected] += 1
        tokens += response.usage_metadata.total_token_count or 0
    return {
        "modelo": model.split("/")[-1],
        "exactitud": round(correct / len(cases), 3),
        "por_etiqueta": {label: f"{per_label[label]}/{total_label[label]}" for label in LABELS},
        "tokens_promedio": round(tokens / len(cases), 1),
        "latencia_promedio_s": round(latency / len(cases), 3),
    }


results = [evaluate(BASE_MODEL)]
if os.environ.get("TUNED_MODEL"):
    results.append(evaluate(os.environ["TUNED_MODEL"]))

print(json.dumps(results, indent=2, ensure_ascii=False))
storage.Client(project=PROJECT).bucket(BUCKET).blob(f"outputs/eval/{int(time.time())}.json").upload_from_string(
    json.dumps(results, ensure_ascii=False))
