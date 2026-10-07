"""Paso 1 · Genera el dataset de clasificación de tickets en formato SFT de Gemini y lo sube a GCS.

Formato SFT (una línea JSON por ejemplo):
  {"systemInstruction": {...}, "contents": [{"role": "user", ...}, {"role": "model", ...}]}

    python scripts/gen_dataset.py
"""

import json
import random

from google.cloud import storage

from common import BUCKET, INSTRUCTION, PROJECT

random.seed(42)
TEMPLATES = {
    "facturacion": ["Me cobraron dos veces el mes de {mes}", "Necesito la factura de {mes} con mi RFC",
                    "El cargo de {monto} pesos no lo reconozco", "¿Por qué subió mi recibo en {mes}?"],
    "soporte_tecnico": ["La app marca error {codigo} al iniciar sesión", "No puedo subir archivos de más de {mb} MB",
                        "El sitio está muy lento desde {mes}", "Me sale pantalla blanca después del error {codigo}"],
    "ventas": ["Quiero cotizar el plan para {n} usuarios", "¿Tienen descuento si pago {n} meses por adelantado?",
               "Me interesa una demo para mi equipo de {n} personas", "¿Qué incluye el plan empresarial?"],
    "cancelacion": ["Quiero dar de baja mi cuenta este {mes}", "¿Cómo cancelo la renovación automática?",
                    "Ya no voy a usar el servicio, cancélenlo", "Necesito cerrar mi cuenta y borrar mis datos"],
}
FILL = {"mes": ["enero", "marzo", "junio", "septiembre"], "monto": ["499", "1,299", "89"], "codigo": ["500", "403", "E-17"],
        "mb": ["50", "100"], "n": ["5", "20", "150"]}


def example(label):
    text = random.choice(TEMPLATES[label]).format(**{k: random.choice(v) for k, v in FILL.items()})
    return {
        "systemInstruction": {"role": "system", "parts": [{"text": INSTRUCTION}]},
        "contents": [{"role": "user", "parts": [{"text": text}]},
                     {"role": "model", "parts": [{"text": label}]}],
    }


def build(n):
    return [example(random.choice(list(TEMPLATES))) for _ in range(n)]


bucket = storage.Client(project=PROJECT).bucket(BUCKET)
for name, rows in {"train": build(160), "validation": build(40)}.items():
    blob = bucket.blob(f"datasets/{name}.jsonl")
    blob.upload_from_string("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), content_type="application/jsonl")
    print(f"gs://{BUCKET}/{blob.name}  ({len(rows)} ejemplos)")
