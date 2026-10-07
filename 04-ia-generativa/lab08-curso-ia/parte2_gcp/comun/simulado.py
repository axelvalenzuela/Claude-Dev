"""Simulador de Gemini para MODO=simulado: aprender y probar gratis.

IMPORTANTE: esto NO es inteligencia artificial. Son respuestas armadas con
reglas y expresiones regulares para que cada lab corra de punta a punta sin
GCP. Sirve para:
  * entender el FLUJO (qué entra, qué sale, en qué orden),
  * correr tests y CI sin credenciales ni costo,
  * provocar a propósito casos difíciles (p. ej. el convertidor se equivoca
    en su primer intento para que veas el ciclo de corrección del lab 15).

Con MODO=real nada de este archivo se usa.
"""
from __future__ import annotations

import hashlib
import math
import re
import unicodedata

from comun.esquemas import AnalisisSAS, EvaluacionJuez, ReglaNegocio


def contar_tokens(texto: str) -> int:
    """Aproximación clásica: ~4 caracteres por token."""
    return max(1, len(texto) // 4)


def generar(rol: str, prompt: str) -> str:
    manejadores = {
        "analista": _analista,
        "convertidor": _convertidor,
        "convertidor_sql": _convertidor_sql,
        "documentador": _documentador,
        "juez": _juez,
        "rag": _rag,
    }
    return manejadores.get(rol, _general)(prompt)


# ---------------------------------------------------------------------------
# Respuestas por rol
# ---------------------------------------------------------------------------
def _general(prompt: str) -> str:
    if "Explica qué hace este programa SAS" in prompt:
        return (
            "[SIMULADO]\n"
            "- Lee raw.ventas y se queda solo con las ventas COMPLETADAS.\n"
            "- Calcula total_con_iva = monto * 1.16.\n"
            "- Clasifica cada venta como ALTA (> 10,000 con IVA) o NORMAL.\n"
            "- Resume por región y categoría: número de ventas y total."
        )
    return (
        "[SIMULADO] SAS es una plataforma comercial de analítica que usa sus propios "
        "lenguajes (DATA step, PROC SQL, macros). Migrarlo a Python/GCP suele significar: "
        "DATA step -> pandas o BigQuery SQL, PROC SQL -> BigQuery SQL, macros -> funciones "
        "de Python, y la calendarización -> Cloud Composer. "
        "(Pon MODO=real para que responda Gemini de verdad.)"
    )


def _analista(prompt: str) -> str:
    """Extrae reglas de un programa SAS con regex. Gemini lo haría 'entendiendo'."""
    sas = prompt
    construcciones = []
    for patron, nombre in [
        (r"\bDATA\s+\w", "DATA step"), (r"PROC\s+SQL", "PROC SQL"), (r"PROC\s+MEANS", "PROC MEANS"),
        (r"PROC\s+SORT", "PROC SORT"), (r"%MACRO", "macro"), (r"\bFORMAT\b", "FORMAT"),
    ]:
        if re.search(patron, sas, re.IGNORECASE):
            construcciones.append(nombre)

    entradas = re.findall(r"\bSET\s+([\w.&]+)", sas, re.I) + re.findall(r"\bFROM\s+([\w.&]+)", sas, re.I)
    salidas = (
        re.findall(r"\bDATA\s+([\w.&]+)\s*;", sas, re.I)
        + re.findall(r"CREATE\s+TABLE\s+([\w.&]+)", sas, re.I)
        + re.findall(r"OUT=([\w.&]+)", sas, re.I)
    )

    reglas = []
    for cond in re.findall(r"WHERE\s+(.+?);", sas, re.I):
        reglas.append(ReglaNegocio(descripcion=f"Solo se consideran registros donde {cond}", tipo="filtro",
                                   codigo_sas=f"WHERE {cond};"))
    for var, expr in re.findall(r"^\s*(\w+)\s*=\s*([^;]+);", sas, re.M):
        reglas.append(ReglaNegocio(descripcion=f"Se calcula {var} como {expr}", tipo="calculo",
                                   codigo_sas=f"{var} = {expr};"))
    for cond, accion in re.findall(r"IF\s+(.+?)\s+THEN\s+(.+?);", sas, re.I):
        reglas.append(ReglaNegocio(descripcion=f"Si {cond} entonces {accion}", tipo="clasificacion",
                                   codigo_sas=f"IF {cond} THEN {accion};"))
    for grupo in re.findall(r"GROUP\s+BY\s+(.+?);", sas, re.I) + re.findall(r"CLASS\s+(.+?);", sas, re.I):
        reglas.append(ReglaNegocio(descripcion=f"Se agrupa y resume por {grupo}", tipo="agregacion",
                                   codigo_sas=grupo))
    if re.search(r"NODUPKEY", sas, re.I):
        reglas.append(ReglaNegocio(descripcion="Se eliminan registros duplicados por la llave BY",
                                   tipo="ordenamiento", codigo_sas="PROC SORT NODUPKEY"))

    complejidad = "alta" if "macro" in construcciones else ("media" if len(construcciones) >= 2 else "baja")
    analisis = AnalisisSAS(
        resumen=f"[SIMULADO] Programa con {', '.join(construcciones) or 'código SAS'}; "
                f"lee {', '.join(dict.fromkeys(entradas)) or 'sin entradas'} y produce "
                f"{', '.join(dict.fromkeys(salidas)) or 'sin salidas'}.",
        tablas_entrada=list(dict.fromkeys(entradas)),
        tablas_salida=list(dict.fromkeys(salidas)),
        construcciones_sas=construcciones,
        reglas=reglas,
        complejidad=complejidad,
    )
    return analisis.model_dump_json(indent=2)


_VENTAS_CORRECTO = '''import pandas as pd


def transformar(ventas: pd.DataFrame) -> pd.DataFrame:
    # DATA ventas_limpias; WHERE estado = 'COMPLETADA';
    limpias = ventas[ventas["estado"] == "COMPLETADA"].copy()
    # total_con_iva = monto * 1.16;
    limpias["total_con_iva"] = limpias["monto"] * 1.16
    # IF total_con_iva > 10000 THEN categoria = 'ALTA'; ELSE categoria = 'NORMAL';
    limpias["categoria"] = limpias["total_con_iva"].gt(10000).map({True: "ALTA", False: "NORMAL"})
    # PROC SQL ... GROUP BY region, categoria
    resumen = limpias.groupby(["region", "categoria"], as_index=False).agg(
        num_ventas=("id", "count"), total=("total_con_iva", "sum")
    )
    resumen["total"] = resumen["total"].round(2)
    return resumen.sort_values(["region", "categoria"]).reset_index(drop=True)
'''

# Error típico de un LLM: aplicar el umbral sobre `monto` en vez de `total_con_iva`.
_VENTAS_CON_ERROR = _VENTAS_CORRECTO.replace(
    'limpias["total_con_iva"].gt(10000)', 'limpias["monto"].gt(10000)'
)


def _convertidor(prompt: str) -> str:
    if "ventas_limpias" in prompt:
        codigo = _VENTAS_CORRECTO if "RETROALIMENTACION" in prompt else _VENTAS_CON_ERROR
    else:
        codigo = (
            "import pandas as pd\n\n\n"
            "def transformar(df: pd.DataFrame) -> pd.DataFrame:\n"
            "    # [SIMULADO] el simulador solo sabe convertir ventas.sas\n"
            "    return df\n"
        )
    return f"```python\n{codigo}```"


def _convertidor_sql(prompt: str) -> str:
    m = re.search(r"Tabla de entrada en BigQuery: `([^`]+)`", prompt)
    tabla = m.group(1) if m else "proyecto.dataset.ventas"
    return f"""```sql
-- Traducción de ventas.sas (DATA step + PROC SQL) a BigQuery SQL
WITH ventas_limpias AS (
  SELECT
    region,
    monto * 1.16 AS total_con_iva,
    CASE WHEN monto * 1.16 > 10000 THEN 'ALTA' ELSE 'NORMAL' END AS categoria
  FROM `{tabla}`
  WHERE estado = 'COMPLETADA'
)
SELECT region, categoria, COUNT(*) AS num_ventas, ROUND(SUM(total_con_iva), 2) AS total
FROM ventas_limpias
GROUP BY region, categoria
ORDER BY region, categoria
```"""


def _documentador(prompt: str) -> str:
    m = re.search(r"```json\s*(.*?)```", prompt, re.S)
    try:
        analisis = AnalisisSAS.model_validate_json(m.group(1)) if m else None
    except ValueError:
        analisis = None
    if analisis is None:
        return "# Documentación\n\n[SIMULADO] No recibí el análisis en JSON."
    reglas = "\n".join(f"- **{r.tipo}**: {r.descripcion} (`{r.codigo_sas.strip()}`)" for r in analisis.reglas)
    return (
        "# Documentación de migración\n\n"
        f"## Qué hace\n{analisis.resumen}\n\n"
        f"## Entradas y salidas\n- Entradas: {', '.join(analisis.tablas_entrada)}\n"
        f"- Salidas: {', '.join(analisis.tablas_salida)}\n\n"
        f"## Reglas de negocio\n{reglas}\n\n"
        f"## Complejidad\n{analisis.complejidad}\n"
    )


def _juez(prompt: str) -> str:
    tiene_reglas = "## Reglas de negocio" in prompt
    return EvaluacionJuez(
        puntaje=4 if tiene_reglas else 2,
        fortalezas=["Lista las reglas de negocio con su código SAS de origen"] if tiene_reglas else [],
        problemas=["[SIMULADO] No explica cómo se validó la migración"]
        + ([] if tiene_reglas else ["No incluye las reglas de negocio"]),
    ).model_dump_json()


def _rag(prompt: str) -> str:
    bloques = re.findall(r"Fuente: (\S+)\n(.+?)(?=\n\nFuente: |\n\nPREGUNTA:)", prompt, re.S)
    if not bloques:
        return "No lo sé: la información no está en los documentos disponibles."
    fuente, texto = bloques[0]
    oraciones = re.split(r"(?<=[.!?])\s+", texto.strip())
    return f"[SIMULADO] Según {fuente}: {' '.join(oraciones[:2])}"


# ---------------------------------------------------------------------------
# Embeddings falsos
# ---------------------------------------------------------------------------
# Un modelo real APRENDE que "repetidos" y "duplicados" significan lo mismo.
# El simulador lo imita con una lista de sinónimos escrita a mano.
_SINONIMOS = {
    "repetidos": "duplicados", "repetidas": "duplicados", "duplicadas": "duplicados",
    "promedio": "media", "promedios": "media", "mean": "media",
    "juntar": "unir", "combinar": "unir", "merge": "unir", "join": "unir", "cruzar": "unir",
    "fechas": "fecha", "dia": "fecha", "dias": "fecha",
    "orquestar": "calendarizar", "programar": "calendarizar", "horario": "calendarizar",
    "filtrar": "where", "condicion": "where",
    "variables": "macro", "parametros": "macro", "reutilizar": "macro",
}
_VACIAS = set(
    "una uno unos unas los las del con por para que como cual cuanto cuanta cuando donde "
    "sus esta este estos estas hay son ser uso usa usan se sin mas pero sobre entre sas "
    "quito saco hago puedo".split()
)
_DIMENSIONES = 1024


def _normalizar(texto: str) -> list[str]:
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    palabras = re.findall(r"[a-z0-9_]+", texto)
    # [:7] = "stemming" burdo: "duplicados" y "duplicado" quedan iguales
    return [_SINONIMOS.get(p, p)[:7] for p in palabras if len(p) > 2 and p not in _VACIAS]


def embeber(texto: str) -> list[float]:
    vector = [0.0] * _DIMENSIONES
    for palabra in _normalizar(texto):
        # md5 y no hash(): hash() cambia en cada ejecución de Python.
        indice = int(hashlib.md5(palabra.encode()).hexdigest(), 16) % _DIMENSIONES
        vector[indice] += 1.0
    norma = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norma for v in vector]


# ---------------------------------------------------------------------------
# Agente con herramientas (sigue un guion fijo, pensado para el micro lab 14)
# ---------------------------------------------------------------------------
def turno_agente(historial: list[dict]) -> tuple[str | None, list[tuple[str, dict]]]:
    resultados = [h for h in historial if h["rol"] == "herramienta"]
    usadas = {h["nombre"] for h in resultados}

    if "listar_programas_sas" not in usadas:
        return None, [("listar_programas_sas", {})]

    if "contar_complejidad" not in usadas:
        programas = next(h["resultado"] for h in resultados if h["nombre"] == "listar_programas_sas")
        return None, [("contar_complejidad", {"nombre_programa": p}) for p in programas]

    complejidades = [h["resultado"] for h in resultados if h["nombre"] == "contar_complejidad"]
    peor = max(complejidades, key=lambda c: c["puntaje"])
    if "buscar_equivalencia" not in usadas:
        return None, [("buscar_equivalencia", {"construccion_sas": c}) for c in peor["construcciones"][:2]]

    equivalencias = "\n".join(f"  - {h['resultado']}" for h in resultados if h["nombre"] == "buscar_equivalencia")
    return (
        f"[SIMULADO] El programa más complejo es {peor['programa']} (puntaje {peor['puntaje']}), "
        f"porque usa: {', '.join(peor['construcciones'])}.\nEquivalencias sugeridas:\n{equivalencias}",
        [],
    )
