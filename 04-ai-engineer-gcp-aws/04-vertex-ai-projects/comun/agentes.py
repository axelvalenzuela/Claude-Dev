"""Los agentes especializados de la migración SAS -> Python.

Cada agente = UN rol, UNAS instrucciones de sistema, UNA forma de salida.
Separarlos (en vez de un solo prompt gigante que "haga todo") permite:
  * probar y mejorar cada uno por separado,
  * usar un modelo distinto por rol (barato para documentar, potente para convertir),
  * saber EN QUÉ paso falló una migración.

    Analista      SAS -> AnalisisSAS (JSON validado)            [LLM]
    Convertidor   SAS + análisis (+ errores previos) -> Python  [LLM]
    Validador     ejecuta y reconcilia contra la salida de SAS  [NO es LLM: es código determinista]
    Documentador  análisis + código + validación -> Markdown    [LLM]
"""
from __future__ import annotations

from comun import llm
from comun.esquemas import AnalisisSAS
from comun.guardrails import extraer_bloque_codigo

SISTEMA_ANALISTA = (
    "Eres un analista experto en SAS. Extraes TODAS las reglas de negocio de un programa: "
    "filtros, cálculos, clasificaciones, agregaciones y ordenamientos. Para cada regla copias el "
    "fragmento SAS exacto. No inventas nada que no esté en el código."
)

SISTEMA_CONVERTIDOR = """Eres un ingeniero que convierte SAS a Python con pandas.
Reglas obligatorias:
- Define UNA función: def transformar(df: pd.DataFrame) -> pd.DataFrame
  que recibe la tabla de entrada y devuelve la tabla de salida final.
- Solo puedes importar pandas y numpy. No leas ni escribas archivos, no uses red.
- La salida debe tener EXACTAMENTE las columnas indicadas y en ese orden.
- Respeta cada regla de negocio del análisis; comenta de qué línea SAS sale cada paso.
- Responde solo con un bloque ```python```."""

SISTEMA_DOCUMENTADOR = (
    "Eres un redactor técnico. Documentas una migración SAS -> Python para el equipo de negocio "
    "y para auditoría: qué hace el proceso, entradas/salidas, reglas de negocio con su origen SAS, "
    "y cómo se validó. Usa Markdown con encabezados ##."
)


def analista(codigo_sas: str) -> tuple[AnalisisSAS, llm.Respuesta]:
    r = llm.generar(f"Programa SAS:\n\n{codigo_sas}", rol="analista", sistema=SISTEMA_ANALISTA, esquema=AnalisisSAS)
    return r.como(AnalisisSAS), r


def convertidor(
    codigo_sas: str, analisis: AnalisisSAS, columnas_salida: list[str] | None,
    retroalimentacion: str | None = None, codigo_anterior: str | None = None,
) -> tuple[str, llm.Respuesta]:
    prompt = (
        f"Programa SAS:\n{codigo_sas}\n\n"
        f"Análisis de reglas (JSON):\n{analisis.model_dump_json(indent=2)}\n\n"
        f"Columnas de salida esperadas: {', '.join(columnas_salida) if columnas_salida else 'las del programa SAS'}\n"
    )
    if retroalimentacion:
        # El corazón del ciclo de autocorrección: el error CONCRETO vuelve al modelo.
        prompt += (
            f"\nRETROALIMENTACION: tu intento anterior NO pasó la validación.\n"
            f"Problemas detectados:\n{retroalimentacion}\n\n"
            f"Código anterior:\n```python\n{codigo_anterior}\n```\nCorrige el código."
        )
    r = llm.generar(prompt, rol="convertidor", sistema=SISTEMA_CONVERTIDOR)
    return extraer_bloque_codigo(r.texto), r


def documentador(analisis: AnalisisSAS, codigo_python: str, resumen_validacion: str) -> tuple[str, llm.Respuesta]:
    prompt = (
        f"Análisis:\n```json\n{analisis.model_dump_json(indent=2)}\n```\n\n"
        f"Código Python resultante:\n```python\n{codigo_python}\n```\n\n"
        f"Resultado de la validación:\n{resumen_validacion}"
    )
    r = llm.generar(prompt, rol="documentador", sistema=SISTEMA_DOCUMENTADOR)
    return r.texto, r
