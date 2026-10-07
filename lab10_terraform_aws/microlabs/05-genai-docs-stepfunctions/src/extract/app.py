"""Extrae texto de un documento en S3: Textract para imágenes/PDF de una página, lectura directa para .txt."""

import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel("INFO")

s3 = boto3.client("s3")
textract = boto3.client("textract")
MAX_CHARS = int(os.environ.get("MAX_CHARS", "4500"))  # Comprehend síncrono acepta hasta ~100 KB


def handler(event, context):
    bucket, key = event["bucket"], event["key"]
    ext = key.rsplit(".", 1)[-1].lower()

    if ext == "txt":
        text = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
    elif ext in ("png", "jpg", "jpeg", "pdf"):
        result = textract.detect_document_text(Document={"S3Object": {"Bucket": bucket, "Name": key}})
        text = "\n".join(b["Text"] for b in result["Blocks"] if b["BlockType"] == "LINE")
    else:
        raise ValueError(f"Formato no soportado: {ext}")

    if not text.strip():
        raise ValueError("Documento sin texto")

    logger.info({"bucket": bucket, "key": key, "chars": len(text)})
    return {"bucket": bucket, "key": key, "text": text[:MAX_CHARS]}
