"""API REST del migrador, lista para Cloud Run.

    GET  /salud    -> ¿está vivo? (Cloud Run y los balanceadores lo usan)
    POST /migrar   -> recibe código SAS, corre el flujo multi-agente del ejercicio 15
    GET  /docs     -> documentación interactiva (Swagger) que FastAPI genera sola

Por qué Cloud Run: empaquetas tu app en un contenedor y Google la escala de
0 a N instancias según las peticiones. Sin tráfico = 0 instancias = $0.

Correr local (desde 19_cloud_run_api/):   uvicorn app:app --reload --port 8080
"""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))              # desplegada: comun/ está junto a app.py
sys.path.insert(0, str(AQUI.parent))       # local: comun/ está en 04-vertex-ai-projects/

from fastapi import FastAPI, HTTPException  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from comun.config import config  # noqa: E402
from comun.guardrails import redactar_datos_sensibles  # noqa: E402
from comun.observabilidad import log  # noqa: E402
from comun.orquestador import migrar  # noqa: E402

app = FastAPI(title="Migrador SAS -> Python", version="1.0.0")


class SolicitudMigracion(BaseModel):
    programa: str = Field(default="programa.sas", examples=["ventas.sas"])
    # Límite de tamaño: sin él, alguien podría mandar 50 MB y hacerte gastar miles de tokens.
    codigo_sas: str = Field(min_length=10, max_length=100_000)


class RespuestaMigracion(BaseModel):
    estado: str
    intentos: int
    costo_usd: float
    codigo_python: str
    documentacion: str
    problemas: list[str]
    datos_sensibles_redactados: dict[str, int]
    bitacora: list[str]


@app.get("/salud")
def salud():
    return {"estado": "ok", "modo": config.modo, "modelo": config.modelo}


@app.post("/migrar", response_model=RespuestaMigracion)
def migrar_programa(solicitud: SolicitudMigracion):
    # Guardrail de entrada: el código SAS a veces trae correos o datos reales en comentarios.
    codigo, redactados = redactar_datos_sensibles(solicitud.codigo_sas)
    try:
        resultado = migrar(codigo, solicitud.programa, avisar=lambda _m: None)
    except Exception as e:
        log("ERROR", "falló la migración", programa=solicitud.programa, error=str(e))
        raise HTTPException(status_code=502, detail=f"Falló la migración: {type(e).__name__}") from e
    return RespuestaMigracion(
        estado=resultado.estado,
        intentos=resultado.intentos,
        costo_usd=resultado.costo_usd,
        codigo_python=resultado.codigo_python,
        documentacion=resultado.documentacion,
        problemas=resultado.validacion.problemas if resultado.validacion else [],
        datos_sensibles_redactados=redactados,
        bitacora=resultado.bitacora,
    )
