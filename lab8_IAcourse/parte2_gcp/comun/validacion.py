"""Validación de código generado por IA: ejecutarlo y comparar resultados.

La pregunta clave de una migración SAS -> Python no es "¿el código se ve
bien?" sino "¿da EXACTAMENTE los mismos números que SAS?". Eso se llama
RECONCILIACIÓN y es determinista: no se le pregunta a otro LLM, se mide.

Pasos:
  1. guardrails.revisar_codigo_generado()  -> ¿es seguro ejecutarlo?
  2. ejecutarlo en un PROCESO APARTE con tiempo límite (si se cuelga o
     truena, no tumba al orquestador)
  3. comparar su salida contra la salida "golden" (la que produjo SAS)
     con tolerancia numérica
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from comun.guardrails import revisar_codigo_generado

_EJECUTOR = """
import sys
import pandas as pd
sys.path.insert(0, sys.argv[1])
from modulo_generado import transformar
salida = transformar(pd.read_csv(sys.argv[2]))
if not isinstance(salida, pd.DataFrame):
    raise TypeError(f"transformar() debe devolver un DataFrame, devolvió {type(salida).__name__}")
salida.to_csv(sys.argv[3], index=False)
"""


@dataclass
class ResultadoValidacion:
    ok: bool
    problemas: list[str] = field(default_factory=list)

    def como_texto(self) -> str:
        return "OK: la salida coincide con la esperada" if self.ok else "\n".join(f"- {p}" for p in self.problemas)


def ejecutar_y_comparar(
    codigo: str, entrada_csv: Path, esperado_csv: Path, tolerancia: float = 0.01, timeout_s: int = 30
) -> ResultadoValidacion:
    problemas = revisar_codigo_generado(codigo)
    if problemas:
        return ResultadoValidacion(False, problemas)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "modulo_generado.py").write_text(codigo, encoding="utf-8")
        (tmp / "ejecutor.py").write_text(_EJECUTOR, encoding="utf-8")
        salida_csv = tmp / "salida.csv"
        try:
            proceso = subprocess.run(
                [sys.executable, str(tmp / "ejecutor.py"), str(tmp), str(entrada_csv), str(salida_csv)],
                capture_output=True, text=True, timeout=timeout_s,
            )
        except subprocess.TimeoutExpired:
            return ResultadoValidacion(False, [f"El código tardó más de {timeout_s}s (¿ciclo infinito?)"])
        if proceso.returncode != 0:
            ultima_linea = (proceso.stderr.strip().splitlines() or ["error desconocido"])[-1]
            return ResultadoValidacion(False, [f"El código falló al ejecutarse: {ultima_linea}"])
        obtenido = pd.read_csv(salida_csv)

    return comparar(obtenido, pd.read_csv(esperado_csv), tolerancia)


def comparar(obtenido: pd.DataFrame, esperado: pd.DataFrame, tolerancia: float = 0.01) -> ResultadoValidacion:
    """Compara dos tablas sin importar el orden de filas."""
    if list(obtenido.columns) != list(esperado.columns):
        return ResultadoValidacion(
            False, [f"Columnas distintas: se obtuvo {list(obtenido.columns)}, se esperaba {list(esperado.columns)}"]
        )

    texto = [c for c in esperado.columns if not pd.api.types.is_numeric_dtype(esperado[c])]
    numericas = [c for c in esperado.columns if c not in texto]
    unido = esperado.merge(obtenido, on=texto, how="outer", suffixes=("_esperado", "_obtenido"), indicator=True)

    problemas = []
    for _, fila in unido.iterrows():
        llave = ", ".join(f"{c}={fila[c]}" for c in texto)
        if fila["_merge"] == "left_only":
            problemas.append(f"Falta la fila ({llave})")
        elif fila["_merge"] == "right_only":
            problemas.append(f"Sobra la fila ({llave})")
        else:
            for c in numericas:
                e, o = fila[f"{c}_esperado"], fila[f"{c}_obtenido"]
                if abs(e - o) > tolerancia:
                    problemas.append(f"({llave}) columna '{c}': se esperaba {_num(e)}, se obtuvo {_num(o)}")
    return ResultadoValidacion(not problemas, problemas)


def _num(x) -> str:
    """3.0 -> '3' (el merge convierte enteros a float); 33200.36 se queda igual."""
    return str(int(x)) if float(x).is_integer() else str(x)
