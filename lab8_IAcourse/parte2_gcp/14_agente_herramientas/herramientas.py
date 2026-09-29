"""Herramientas (tools) que el agente puede usar.

Son funciones normales de Python. El SDK convierte su NOMBRE, su DOCSTRING y
sus TYPE HINTS en la descripción que ve el modelo. Por eso:
  * el docstring debe decir CUÁNDO usar la herramienta, no solo qué hace;
  * los parámetros deben tener tipos simples (str, int, list[str]);
  * el resultado debe ser serializable a JSON (dict, list, str, números).
Un docstring vago = el modelo escoge mal la herramienta.
"""
import re
from pathlib import Path

CARPETA_SAS = Path(__file__).resolve().parents[1] / "comun" / "sas"

_EQUIVALENCIAS = {
    "DATA step": "pandas: filtros y columnas sobre el DataFrame | BigQuery: SELECT ... WHERE / CTE",
    "PROC SQL": "BigQuery SQL casi directo (ojo con funciones propias de SAS como CALCULATED)",
    "PROC SORT": "pandas: sort_values + drop_duplicates | BigQuery: QUALIFY ROW_NUMBER() = 1",
    "PROC MEANS": "pandas: groupby().agg() | BigQuery: GROUP BY con SUM/AVG",
    "macro": "función de Python con parámetros; expandir la macro antes de convertir",
    "FORMAT": "solo presentación: pandas .dt.strftime | BigQuery FORMAT_DATE",
}


def listar_programas_sas() -> list[str]:
    """Lista los nombres de todos los programas SAS disponibles para analizar.
    Úsala primero cuando no sepas qué programas existen."""
    return sorted(p.name for p in CARPETA_SAS.glob("*.sas"))


def leer_programa_sas(nombre_programa: str) -> str:
    """Devuelve el código fuente completo de un programa SAS.
    Úsala cuando necesites ver el código exacto de un programa (p. ej. 'ventas.sas')."""
    ruta = (CARPETA_SAS / nombre_programa).resolve()
    if ruta.parent != CARPETA_SAS or not ruta.exists():   # evita leer fuera de la carpeta
        return f"ERROR: no existe el programa {nombre_programa}"
    return ruta.read_text(encoding="utf-8")


def contar_complejidad(nombre_programa: str) -> dict:
    """Mide la complejidad de migración de un programa SAS: qué construcciones usa
    y un puntaje (más alto = más difícil de migrar). Úsala para comparar programas."""
    codigo = leer_programa_sas(nombre_programa)
    if codigo.startswith("ERROR"):
        return {"programa": nombre_programa, "error": codigo}
    pesos = {"DATA step": (r"\bDATA\s+\w", 1), "PROC SQL": (r"PROC\s+SQL", 1), "PROC SORT": (r"PROC\s+SORT", 1),
             "PROC MEANS": (r"PROC\s+MEANS", 2), "macro": (r"%MACRO", 4), "FORMAT": (r"\bFORMAT\b", 1)}
    encontradas = {n: len(re.findall(p, codigo, re.I)) * w for n, (p, w) in pesos.items()}
    encontradas = {n: v for n, v in encontradas.items() if v}
    return {"programa": nombre_programa, "puntaje": sum(encontradas.values()),
            "construcciones": sorted(encontradas, key=encontradas.get, reverse=True),
            "lineas": len(codigo.splitlines())}


def buscar_equivalencia(construccion_sas: str) -> str:
    """Devuelve el equivalente en Python/BigQuery de una construcción SAS
    (por ejemplo 'PROC SORT', 'macro', 'DATA step')."""
    for nombre, equivalencia in _EQUIVALENCIAS.items():
        if nombre.lower() in construccion_sas.lower():
            return f"{nombre} -> {equivalencia}"
    return f"Sin equivalencia registrada para '{construccion_sas}'"


HERRAMIENTAS = [listar_programas_sas, leer_programa_sas, contar_complejidad, buscar_equivalencia]
