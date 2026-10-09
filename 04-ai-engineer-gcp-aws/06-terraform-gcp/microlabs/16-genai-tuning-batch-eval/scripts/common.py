"""Configuración compartida de los scripts del micro lab 16 (lee los outputs de Terraform)."""

import os
import subprocess
from pathlib import Path

from google import genai

LAB = Path(__file__).resolve().parent.parent
LABELS = ["facturacion", "soporte_tecnico", "ventas", "cancelacion"]
INSTRUCTION = ("Clasifica el ticket en UNA etiqueta: facturacion, soporte_tecnico, ventas o cancelacion. "
               "Responde solo la etiqueta.")


def tf_output(name):
    return subprocess.run(["terraform", f"-chdir={LAB}", "output", "-raw", name],
                          check=True, capture_output=True, text=True).stdout.strip()


PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
REGION = os.environ.get("GOOGLE_CLOUD_REGION") or tf_output("region")
BUCKET = os.environ.get("ML_BUCKET") or tf_output("ml_bucket")
BASE_MODEL = os.environ.get("BASE_MODEL", "gemini-2.5-flash")

# Tuning y batch son regionales: el cliente debe apuntar a la misma región que el bucket
client = genai.Client(vertexai=True, project=PROJECT, location=REGION)
