"""La "forma" de las respuestas que le pedimos al modelo (salida estructurada).

Pasarle a Gemini un esquema (response_schema) hace que responda JSON con
exactamente estos campos. Luego Pydantic lo valida: si el modelo inventa un
campo o pone un tipo equivocado, truena AQUÍ y no tres pasos después.
Ver micro lab 12.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ReglaNegocio(BaseModel):
    descripcion: str = Field(description="La regla en lenguaje de negocio, en español")
    tipo: Literal["filtro", "calculo", "clasificacion", "agregacion", "ordenamiento", "otro"]
    codigo_sas: str = Field(description="Fragmento SAS de donde sale la regla (trazabilidad)")


class AnalisisSAS(BaseModel):
    resumen: str = Field(description="Qué hace el programa, en 1-2 oraciones")
    tablas_entrada: list[str]
    tablas_salida: list[str]
    construcciones_sas: list[str] = Field(description="Ej: DATA step, PROC SQL, PROC MEANS, macro")
    reglas: list[ReglaNegocio]
    complejidad: Literal["baja", "media", "alta"]


class EvaluacionJuez(BaseModel):
    """Lo que devuelve un 'LLM como juez' al calificar otra salida."""
    puntaje: int = Field(ge=1, le=5, description="1 = inservible, 5 = excelente")
    fortalezas: list[str]
    problemas: list[str]
