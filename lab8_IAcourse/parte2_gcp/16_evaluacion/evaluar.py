"""Micro lab 16 — Evaluar la calidad de lo que genera la IA (con números).

"Se ve bien" no es una métrica. Para saber si un cambio de prompt o de
modelo MEJORA o EMPEORA la migración, se corre siempre el mismo conjunto de
casos con respuesta conocida (golden set) y se miden cosas objetivas:

  PASO #1: cargar casos_golden.json (programa + lo que DEBERÍA salir)
  PASO #2: correr el flujo multi-agente del lab 15 en cada caso
  PASO #3: métricas deterministas
            - recall de reglas:         ¿encontró los tipos de regla esperados?
            - recall de construcciones: ¿detectó macro, PROC SORT...?
            - estado correcto:          ¿aprobó solo lo que debía aprobar?
  PASO #4: métrica con "LLM como juez" para lo subjetivo (calidad de la documentación)
  PASO #5: QUALITY GATE: si las métricas bajan del umbral, el script sale con
          código 1 -> en CI eso bloquea el merge (ver .github/workflows/lab8-ci.yml)

Correr (desde parte2_gcp/):   python 16_evaluacion/evaluar.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comun import llm  # noqa: E402
from comun.config import RAIZ, config  # noqa: E402
from comun.esquemas import EvaluacionJuez  # noqa: E402
from comun.orquestador import migrar  # noqa: E402

UMBRAL_RECALL = 0.8
UMBRAL_JUEZ = 3.0

SISTEMA_JUEZ = (
    "Eres un revisor exigente de documentación técnica de migraciones. Calificas de 1 a 5 "
    "si la documentación permite a alguien de negocio entender QUÉ hace el proceso y a un auditor "
    "verificar DE DÓNDE sale cada regla. Sé estricto: 5 solo si no le falta nada."
)


def recall(esperados: list[str], obtenidos: list[str]) -> float:
    if not esperados:
        return 1.0
    return len(set(esperados) & set(obtenidos)) / len(set(esperados))


def evaluar_caso(caso: dict) -> dict:
    codigo_sas = (RAIZ / "comun" / "sas" / caso["programa"]).read_text(encoding="utf-8")
    resultado = migrar(codigo_sas, caso["programa"], avisar=lambda _m: None)      # PASO #2

    tipos = [r.tipo for r in resultado.analisis.reglas]                            # PASO #3
    juez = llm.generar(                                                            # PASO #4
        f"Documentación a evaluar:\n\n{resultado.documentacion}",
        rol="juez", sistema=SISTEMA_JUEZ, esquema=EvaluacionJuez,
    ).como(EvaluacionJuez)
    return {
        "programa": caso["programa"],
        "recall_reglas": recall(caso["tipos_regla_esperados"], tipos),
        "recall_construcciones": recall(caso["construcciones_esperadas"], resultado.analisis.construcciones_sas),
        "estado_correcto": (resultado.estado == "APROBADO") == caso["debe_aprobar"],
        "estado": resultado.estado,
        "intentos": resultado.intentos,
        "costo_usd": resultado.costo_usd,
        "juez": juez.puntaje,
        "problemas_juez": juez.problemas,
    }


def main() -> int:
    casos = json.loads((Path(__file__).parent / "casos_golden.json").read_text(encoding="utf-8"))   # PASO #1
    print(f"Modo {config.modo} | modelo {config.modelo} | {len(casos)} casos\n")
    filas = [evaluar_caso(c) for c in casos]

    print(f"{'programa':<16}{'reglas':>8}{'constr.':>9}{'estado':>20}{'ok':>4}{'int.':>6}{'juez':>6}{'costo':>11}")
    print("-" * 80)
    for f in filas:
        print(f"{f['programa']:<16}{f['recall_reglas']:>8.0%}{f['recall_construcciones']:>9.0%}"
              f"{f['estado']:>20}{'sí' if f['estado_correcto'] else 'NO':>4}{f['intentos']:>6}"
              f"{f['juez']:>6}{f['costo_usd']:>11.6f}")

    n = len(filas)
    prom_reglas = sum(f["recall_reglas"] for f in filas) / n
    prom_constr = sum(f["recall_construcciones"] for f in filas) / n
    prom_juez = sum(f["juez"] for f in filas) / n
    estados_ok = all(f["estado_correcto"] for f in filas)
    print(f"\nPromedios: reglas {prom_reglas:.0%} | construcciones {prom_constr:.0%} | juez {prom_juez:.1f}/5"
          f" | costo total ${sum(f['costo_usd'] for f in filas):.6f}")

    # PASO #5 — quality gate
    fallas = []
    if prom_reglas < UMBRAL_RECALL:
        fallas.append(f"recall de reglas {prom_reglas:.0%} < {UMBRAL_RECALL:.0%}")
    if prom_constr < UMBRAL_RECALL:
        fallas.append(f"recall de construcciones {prom_constr:.0%} < {UMBRAL_RECALL:.0%}")
    if prom_juez < UMBRAL_JUEZ:
        fallas.append(f"juez {prom_juez:.1f} < {UMBRAL_JUEZ}")
    if not estados_ok:
        fallas.append("algún programa se aprobó/rechazó cuando no debía")

    if fallas:
        print("\nQUALITY GATE: FALLA\n  - " + "\n  - ".join(fallas))
        return 1
    print("\nQUALITY GATE: PASA")
    return 0


if __name__ == "__main__":
    sys.exit(main())
