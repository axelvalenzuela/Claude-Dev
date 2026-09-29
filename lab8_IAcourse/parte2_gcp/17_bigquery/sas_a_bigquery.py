"""Micro lab 17 — SAS -> BigQuery SQL, validado con dry run y reconciliación.

  PASO 1: cargar ventas.csv a la tabla `ventas` (creada por Terraform en infra/)
  PASO 2: pedirle a Gemini que traduzca ventas.sas a BigQuery SQL
  PASO 3: DRY RUN -> ¿el SQL es válido? ¿cuántos bytes leería? ¿cuánto costaría?
  PASO 4: ejecutarlo y RECONCILIAR contra la salida original de SAS
  PASO 5: guardar el SQL aprobado

Mismo principio que el lab 15: el LLM propone, una verificación determinista decide.

Correr (desde parte2_gcp/):   python 17_bigquery/sas_a_bigquery.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bq  # noqa: E402
import pandas as pd  # noqa: E402

from comun import llm  # noqa: E402
from comun.config import RAIZ, config  # noqa: E402
from comun.guardrails import extraer_bloque_codigo  # noqa: E402
from comun.validacion import comparar  # noqa: E402

SISTEMA = (
    "Traduces programas SAS a GoogleSQL de BigQuery. Usa CTEs (WITH) para cada DATA step, "
    "nombres de tabla completos entre backticks, y ORDER BY al final. "
    "Responde solo con un bloque ```sql```."
)


def main():
    print(f"Modo {config.modo} | tabla {bq.tabla('ventas')}\n")

    # PASO 1
    filas = bq.cargar_csv(RAIZ / "comun" / "datos" / "ventas.csv", "ventas")
    print(f"PASO 1: {filas} filas cargadas en {bq.tabla('ventas')}")

    # PASO 2
    sas = (RAIZ / "comun" / "sas" / "ventas.sas").read_text(encoding="utf-8")
    columnas = list(pd.read_csv(RAIZ / "comun" / "datos" / "esperado_resumen_ventas.csv", nrows=0).columns)
    prompt = (
        f"Programa SAS:\n{sas}\n\n"
        f"Tabla de entrada en BigQuery: `{bq.tabla('ventas')}` (columnas: id, fecha, region, estado, monto)\n"
        f"Columnas de salida, en este orden: {', '.join(columnas)}. Redondea montos a 2 decimales."
    )
    r = llm.generar(prompt, rol="convertidor_sql", sistema=SISTEMA)
    sql = extraer_bloque_codigo(r.texto, "sql")
    print(f"PASO 2: SQL generado ({r.tokens_entrada}+{r.tokens_salida} tokens, ${r.costo_usd:.6f})\n")
    print(sql, "\n")

    # PASO 3
    try:
        estimacion = bq.estimar(sql)
    except Exception as e:  # noqa: BLE001 - un SQL inválido se reporta, no se ejecuta
        print(f"PASO 3: el SQL NO es válido -> {e}")
        print("(En un flujo real, este error vuelve al LLM como retroalimentación.)")
        return
    print(f"PASO 3: dry run OK | leería {estimacion['bytes']:,} bytes | costo ~${estimacion['costo_usd']:.6f}")

    # PASO 4
    obtenido = bq.consultar(sql)
    esperado = pd.read_csv(RAIZ / "comun" / "datos" / "esperado_resumen_ventas.csv")
    validacion = comparar(obtenido, esperado)
    print(f"PASO 4: reconciliación -> {validacion.como_texto()}")

    # PASO 5
    if validacion.ok:
        destino = RAIZ / "salida" / "resumen_ventas.sql"
        destino.parent.mkdir(exist_ok=True)
        destino.write_text(sql + "\n", encoding="utf-8")
        print(f"PASO 5: SQL aprobado guardado en {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
