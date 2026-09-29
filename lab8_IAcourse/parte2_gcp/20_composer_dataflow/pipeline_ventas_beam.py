"""Micro lab 20 — ventas.sas convertido a un pipeline de Apache Beam (Dataflow).

¿Cuándo Dataflow y no pandas o BigQuery?
  pandas     -> datos que caben en la memoria de UNA máquina
  BigQuery   -> la transformación se puede expresar en SQL (la mayoría de los casos)
  Dataflow   -> procesamiento distribuido y streaming, lógica que no cabe en SQL,
                o leer/escribir muchas fuentes (archivos, Pub/Sub, BigQuery...)

Un pipeline de Beam es una cadena de transformaciones (PTransforms) sobre
colecciones (PCollections). El MISMO código corre:
    local      -> PrismRunner     (el runner local por defecto desde Beam 2.6x; antes DirectRunner)
    en GCP     -> DataflowRunner  (Google levanta y apaga las máquinas por ti)

    leer CSV -> parsear -> filtrar COMPLETADA -> IVA + categoría -> agrupar (región, categoría) -> escribir

Correr local (desde parte2_gcp/, con requirements-beam.txt instalado):
    python 20_composer_dataflow/pipeline_ventas_beam.py
"""
import argparse
import csv
import sys
from pathlib import Path

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

RAIZ = Path(__file__).resolve().parents[1]
ENCABEZADO = "region,categoria,num_ventas,total"


def parsear(linea: str) -> dict:
    id_, fecha, region, estado, monto = next(csv.reader([linea]))
    return {"id": int(id_), "region": region, "estado": estado, "monto": float(monto)}


def agregar_iva_y_categoria(venta: dict) -> dict:
    total = venta["monto"] * 1.16                                   # total_con_iva = monto * 1.16
    return {**venta, "total_con_iva": total,
            "categoria": "ALTA" if total > 10000 else "NORMAL"}      # IF ... THEN 'ALTA' ELSE 'NORMAL'


class ContarYSumar(beam.CombineFn):
    """COUNT(*) y SUM(total_con_iva) en una sola pasada, en paralelo entre máquinas."""

    def create_accumulator(self):
        return 0, 0.0

    def add_input(self, acumulado, total):
        return acumulado[0] + 1, acumulado[1] + total

    def merge_accumulators(self, acumulados):
        cuentas, sumas = zip(*acumulados)
        return sum(cuentas), sum(sumas)

    def extract_output(self, acumulado):
        return acumulado


def formatear(elemento) -> str:
    (region, categoria), (num, total) = elemento
    return f"{region},{categoria},{num},{round(total, 2)}"


def construir(p, entrada: str, salida: str):
    return (
        p
        | "Leer" >> beam.io.ReadFromText(entrada, skip_header_lines=1)
        | "Parsear" >> beam.Map(parsear)
        | "SoloCompletadas" >> beam.Filter(lambda v: v["estado"] == "COMPLETADA")   # WHERE
        | "IvaYCategoria" >> beam.Map(agregar_iva_y_categoria)
        | "Llave" >> beam.Map(lambda v: ((v["region"], v["categoria"]), v["total_con_iva"]))
        | "Agrupar" >> beam.CombinePerKey(ContarYSumar())                          # GROUP BY
        | "Formatear" >> beam.Map(formatear)
        | "Escribir" >> beam.io.WriteToText(salida, header=ENCABEZADO, num_shards=1, shard_name_template="")
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--entrada", default=str(RAIZ / "comun" / "datos" / "ventas.csv"))
    parser.add_argument("--salida", default=str(RAIZ / "salida" / "beam_resumen_ventas.csv"))
    args, opciones_beam = parser.parse_known_args(argv)   # el resto (--runner, --project...) es para Beam

    with beam.Pipeline(options=PipelineOptions(opciones_beam)) as p:
        construir(p, args.entrada, args.salida)

    # Reconciliar solo si corrió local (en Dataflow la salida está en gs://)
    if not args.salida.startswith("gs://"):
        sys.path.insert(0, str(RAIZ))
        import pandas as pd

        from comun.validacion import comparar

        obtenido = pd.read_csv(args.salida).sort_values(["region", "categoria"])
        esperado = pd.read_csv(RAIZ / "comun" / "datos" / "esperado_resumen_ventas.csv")
        print(f"Salida en {args.salida}")
        print(f"Reconciliación contra SAS: {comparar(obtenido, esperado).como_texto()}")


if __name__ == "__main__":
    main()
