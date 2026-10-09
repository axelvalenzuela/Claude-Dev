"""Logs estructurados y registro de cada llamada al modelo.

Dos cosas distintas:
  1. log(...)  -> una línea JSON por evento. En Cloud Run / Cloud Functions,
     todo lo que imprimes en stdout como JSON con campo "severity" aparece en
     Cloud Logging ya separado por campos (filtrable, sin configurar nada).
  2. registrar_llamada(...) -> agrega una línea a .registros/llamadas.jsonl
     con modelo, tokens, costo y latencia. El ejercicio 21 lo resume.

Por defecto los logs solo muestran WARNING o peor, para no ensuciar la salida
de los labs. Pon LOG_NIVEL=INFO en el .env para verlos todos.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from comun.config import RAIZ

ARCHIVO_REGISTRO = RAIZ / ".registros" / "llamadas.jsonl"
_NIVELES = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}
_NIVEL_MINIMO = _NIVELES.get(os.getenv("LOG_NIVEL", "WARNING").upper(), 30)


def log(severidad: str, mensaje: str, **campos) -> None:
    if _NIVELES.get(severidad, 20) < _NIVEL_MINIMO:
        return
    evento = {"severity": severidad, "message": mensaje, **campos}
    print(json.dumps(evento, ensure_ascii=False, default=str), file=sys.stderr)


def registrar_llamada(**datos) -> None:
    datos["timestamp"] = datetime.now(timezone.utc).isoformat()
    log("INFO", "llamada_llm", **datos)
    try:
        ARCHIVO_REGISTRO.parent.mkdir(exist_ok=True)
        with ARCHIVO_REGISTRO.open("a", encoding="utf-8") as f:
            f.write(json.dumps(datos, ensure_ascii=False) + "\n")
    except OSError:
        # En Cloud Functions el disco es de solo lectura (salvo /tmp): no es
        # grave perder el archivo, el log JSON de arriba ya quedó en Cloud Logging.
        pass


def leer_registro() -> list[dict]:
    if not ARCHIVO_REGISTRO.exists():
        return []
    with ARCHIVO_REGISTRO.open(encoding="utf-8") as f:
        return [json.loads(linea) for linea in f if linea.strip()]


def ruta_legible(ruta: Path) -> str:
    try:
        return str(ruta.relative_to(RAIZ))
    except ValueError:
        return str(ruta)
