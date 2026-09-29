"""Guardrails: reglas de seguridad alrededor del modelo.

  ANTES de llamar al modelo  -> redactar_datos_sensibles(): no mandar correos,
                                tarjetas, RFC/CURP, etc. a un servicio externo.
  DESPUÉS de que responde    -> revisar_codigo_generado(): el código que escribe
                                un LLM NO es de confianza. Antes de ejecutarlo
                                se revisa que no importe cosas peligrosas.

Esto no reemplaza un sandbox real (en producción el código se ejecuta en un
contenedor aislado, sin red ni credenciales, p. ej. un Cloud Run Job), pero
es la primera línea de defensa y es fácil de explicar en una entrevista.
"""
from __future__ import annotations

import ast
import re

_PATRONES_SENSIBLES = {
    "CORREO": r"[\w.+-]+@[\w-]+\.[\w.]+",
    "TARJETA": r"\b(?:\d[ -]?){13,16}\b",
    "CURP": r"\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d\b",
    "RFC": r"\b[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}\b",
}

MODULOS_PERMITIDOS = {"pandas", "numpy", "math", "datetime", "decimal"}
LLAMADAS_PROHIBIDAS = {"eval", "exec", "open", "__import__", "compile", "input", "globals"}


def redactar_datos_sensibles(texto: str) -> tuple[str, dict[str, int]]:
    """Reemplaza datos sensibles por [CORREO], [TARJETA]... y cuenta cuántos hubo."""
    conteo = {}
    for etiqueta, patron in _PATRONES_SENSIBLES.items():
        texto, n = re.subn(patron, f"[{etiqueta}]", texto)
        if n:
            conteo[etiqueta] = n
    return texto, conteo


def revisar_codigo_generado(codigo: str) -> list[str]:
    """Devuelve la lista de problemas encontrados (vacía = pasa la revisión)."""
    try:
        arbol = ast.parse(codigo)
    except SyntaxError as e:
        return [f"El código no es Python válido: {e.msg} (línea {e.lineno})"]

    problemas = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos = [a.name.split(".")[0] for a in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            modulos = [(nodo.module or "").split(".")[0]]
        else:
            modulos = []
        for m in modulos:
            if m not in MODULOS_PERMITIDOS:
                problemas.append(f"Importa un módulo no permitido: {m}")
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
            if nodo.func.id in LLAMADAS_PROHIBIDAS:
                problemas.append(f"Usa una función prohibida: {nodo.func.id}()")
    return problemas


def extraer_bloque_codigo(texto: str, lenguaje: str = "python") -> str:
    """Los modelos suelen envolver el código en ```python ... ```. Lo sacamos."""
    m = re.search(rf"```(?:{lenguaje})?\s*\n(.*?)```", texto, re.DOTALL | re.IGNORECASE)
    return (m.group(1) if m else texto).strip()
