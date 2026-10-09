"""Orquestador multi-agente: coordina Analista -> Convertidor <-> Validador -> Documentador.

Patrón: flujo secuencial con un CICLO DE AUTOCORRECCIÓN entre el Convertidor
y el Validador (a veces llamado "generator-critic" o "reflection"):

    analista ──> convertidor ──> validador ──ok──> documentador ──> APROBADO
                     ^              │
                     └──problemas───┘   (máximo MAX_INTENTOS; si no, REQUIERE_REVISION)

Decisiones de diseño que conviene poder explicar:
  * El validador NO es un LLM: la reconciliación numérica se mide, no se opina.
  * Hay límite de intentos: cada intento cuesta tokens; sin límite, un caso
    imposible gasta dinero para siempre.
  * Sin datos de prueba no hay aprobación automática: se marca para revisión humana.
  * Todo queda registrado (intentos, costo, problemas) para auditoría.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pandas as pd

from comun import agentes
from comun.config import RAIZ
from comun.esquemas import AnalisisSAS
from comun.guardrails import revisar_codigo_generado
from comun.observabilidad import log
from comun.validacion import ResultadoValidacion, ejecutar_y_comparar

MAX_INTENTOS = 3
DATOS = RAIZ / "comun" / "datos"


@dataclass
class CasoPrueba:
    """Entrada real + la salida que produjo SAS con esa entrada (el 'golden')."""
    entrada_csv: Path
    esperado_csv: Path


# Qué datos de prueba tiene cada programa. En un proyecto real esto sale de
# correr SAS una última vez y guardar entradas/salidas antes de apagarlo.
CASOS = {
    "ventas.sas": CasoPrueba(DATOS / "ventas.csv", DATOS / "esperado_resumen_ventas.csv"),
}


@dataclass
class ResultadoMigracion:
    programa: str
    estado: str                         # APROBADO | REQUIERE_REVISION
    analisis: AnalisisSAS
    codigo_python: str
    intentos: int
    validacion: ResultadoValidacion | None
    documentacion: str
    costo_usd: float
    tokens: int
    bitacora: list[str] = field(default_factory=list)


def migrar(
    codigo_sas: str, programa: str = "programa.sas", avisar: Callable[[str], None] = print
) -> ResultadoMigracion:
    bitacora, costo, tokens = [], 0.0, 0

    def registrar(mensaje: str, respuesta=None):
        nonlocal costo, tokens
        if respuesta is not None:
            costo += respuesta.costo_usd
            tokens += respuesta.tokens_entrada + respuesta.tokens_salida
        bitacora.append(mensaje)
        log("INFO", mensaje, programa=programa)
        avisar(mensaje)

    # 1. Analista
    analisis, r = agentes.analista(codigo_sas)
    registrar(f"[analista] {len(analisis.reglas)} reglas, complejidad {analisis.complejidad}", r)

    caso = CASOS.get(programa)
    columnas = list(pd.read_csv(caso.esperado_csv, nrows=0).columns) if caso else None

    # 2. Convertidor <-> Validador
    codigo, validacion, retro = "", None, None
    intento = 0
    for intento in range(1, MAX_INTENTOS + 1):
        codigo_anterior = codigo
        codigo, r = agentes.convertidor(codigo_sas, analisis, columnas, retro, codigo_anterior or None)
        registrar(f"[convertidor] intento {intento}: {len(codigo.splitlines())} líneas de Python", r)

        if caso:
            validacion = ejecutar_y_comparar(codigo, caso.entrada_csv, caso.esperado_csv)
        else:
            problemas = revisar_codigo_generado(codigo)
            validacion = ResultadoValidacion(not problemas, problemas) if problemas else None
        if validacion is None:
            registrar("[validador] sin datos de prueba: solo revisión de seguridad (pasó)")
            break
        if validacion.ok:
            registrar(f"[validador] intento {intento}: reconciliación OK")
            break
        registrar(f"[validador] intento {intento}: FALLÓ\n{validacion.como_texto()}")
        retro = validacion.como_texto()

    aprobado = validacion is not None and validacion.ok
    estado = "APROBADO" if aprobado else "REQUIERE_REVISION"

    # 3. Documentador
    resumen_validacion = validacion.como_texto() if validacion else "Sin datos de prueba: requiere revisión humana."
    documentacion, r = agentes.documentador(analisis, codigo, resumen_validacion)
    registrar("[documentador] documentación generada", r)
    registrar(f"[orquestador] estado final: {estado} en {intento} intento(s), ${costo:.6f} USD")

    return ResultadoMigracion(programa, estado, analisis, codigo, intento, validacion, documentacion,
                              round(costo, 6), tokens, bitacora)
