"""Micro lab 21 — ¿Cuánto gastó la IA, en qué y qué tan rápido?

Cada llamada que hicieron los labs 11-19 quedó registrada en
.registros/llamadas.jsonl (ver comun/observabilidad.py). Este script lo resume:

  PASO 1: leer el registro
  PASO 2: agrupar por rol del agente y modelo -> llamadas, tokens, costo, latencia
  PASO 3: proyectar: ¿cuánto costaría migrar N programas?
  PASO 4 (MODO=real, opcional): mandar el registro a BigQuery para tableros y auditoría

Correr (desde parte2_gcp/):
    python 21_monitoreo_gobernanza/reporte_costos.py
    python 21_monitoreo_gobernanza/reporte_costos.py --programas 5000
    python 21_monitoreo_gobernanza/reporte_costos.py --bigquery      # solo MODO=real
"""
import argparse
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comun.config import config  # noqa: E402
from comun.observabilidad import ARCHIVO_REGISTRO, leer_registro, ruta_legible  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--programas", type=int, default=1000, help="programas SAS para la proyección")
    parser.add_argument("--bigquery", action="store_true", help="exportar el registro a BigQuery")
    args = parser.parse_args()

    registros = leer_registro()                                                     # PASO 1
    if not registros:
        print(f"No hay registros en {ruta_legible(ARCHIVO_REGISTRO)}. Corre antes los labs 11-19.")
        return

    grupos = defaultdict(list)                                                      # PASO 2
    for r in registros:
        grupos[(r["modo"], r["tipo"], r["rol"], r["modelo"])].append(r)

    print(f"{'modo':<9}{'tipo':<9}{'rol':<20}{'modelo':<24}{'llam.':>6}{'tokens':>9}{'costo USD':>12}{'lat. p50':>10}")
    print("-" * 99)
    for (modo, tipo, rol, modelo), filas in sorted(grupos.items()):
        tokens = sum(f["tokens_entrada"] + f["tokens_salida"] for f in filas)
        costo = sum(f["costo_usd"] for f in filas)
        p50 = statistics.median(f["latencia_s"] for f in filas)
        print(f"{modo:<9}{tipo:<9}{rol[:19]:<20}{modelo[:23]:<24}{len(filas):>6}{tokens:>9}{costo:>12.6f}{p50:>9.2f}s")

    total = sum(r["costo_usd"] for r in registros)
    print(f"\nTotal: {len(registros)} llamadas, ${total:.6f} USD")

    migraciones = [r for r in registros if r["rol"] == "analista"]                  # PASO 3
    if migraciones:
        costo_programa = sum(r["costo_usd"] for r in registros if r["rol"] in
                             ("analista", "convertidor", "documentador")) / len(migraciones)
        print(f"\nProyección: ~${costo_programa:.6f} USD por programa (análisis+conversión+documentación)")
        print(f"            -> {args.programas:,} programas ≈ ${costo_programa * args.programas:,.2f} USD en tokens")
        print("            (los programas reales son más largos: mide con 10-20 reales antes de presupuestar)")

    if args.bigquery:                                                               # PASO 4
        exportar_a_bigquery(registros)


def exportar_a_bigquery(registros):
    if not config.es_real:
        print("\n--bigquery requiere MODO=real.")
        return
    config.exigir_proyecto()
    from google.cloud import bigquery

    tabla = f"{config.proyecto}.{config.dataset}.auditoria_llm"
    campos = ("timestamp", "modo", "tipo", "rol", "modelo",
              "tokens_entrada", "tokens_salida", "costo_usd", "latencia_s")
    filas = [{c: r.get(c) for c in campos} for r in registros]
    # Load job (gratis) en vez de insert_rows_json (streaming, se cobra por GB).
    trabajo = bigquery.Client(project=config.proyecto).load_table_from_json(
        filas, tabla, job_config=bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_APPEND)
    )
    trabajo.result()
    print(f"\n{len(filas)} registros agregados a {tabla}")


if __name__ == "__main__":
    main()
