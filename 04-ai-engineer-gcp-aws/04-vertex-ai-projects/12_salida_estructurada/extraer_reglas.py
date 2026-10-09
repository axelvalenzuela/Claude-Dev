"""Ejercicio 12 — Salida estructurada: que el modelo responda JSON validable.

Un agente que alimenta a OTRO programa no puede responder prosa: necesita
datos con forma fija. Receta:

  PASO #1: definir la forma con Pydantic        (comun/esquemas.py -> AnalisisSAS)
  PASO #2: pasarla como response_schema          (comun/llm.py, parámetro esquema=)
  PASO #3: validar la respuesta con Pydantic     (respuesta.como(AnalisisSAS))
  PASO #4: si no valida, NO seguir: registrar y reintentar / escalar

Correr (desde 04-vertex-ai-projects/):
    python 12_salida_estructurada/extraer_reglas.py
    python 12_salida_estructurada/extraer_reglas.py comun/sas/clientes.sas
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pydantic import ValidationError  # noqa: E402

from comun import llm  # noqa: E402
from comun.esquemas import AnalisisSAS  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]

SISTEMA = (
    "Eres un analista de código SAS. Extraes TODAS las reglas de negocio del programa. "
    "Para cada regla copia el fragmento SAS exacto de donde sale (trazabilidad). "
    "No inventes tablas ni reglas que no estén en el código."
)


def analizar(ruta_sas: Path) -> AnalisisSAS:
    codigo = ruta_sas.read_text(encoding="utf-8")
    # PASO #2: esquema=AnalisisSAS -> Gemini devuelve JSON con esa forma exacta
    respuesta = llm.generar(f"Programa SAS:\n\n{codigo}", rol="analista", sistema=SISTEMA, esquema=AnalisisSAS)
    # PASO #3: validar. Si falla aquí, lanza ValidationError con el campo culpable.
    return respuesta.como(AnalisisSAS)


def main():
    ruta = RAIZ / (sys.argv[1] if len(sys.argv) > 1 else "comun/sas/ventas.sas")
    analisis = analizar(ruta)

    print(f"Programa: {ruta.name}   complejidad: {analisis.complejidad}")
    print(f"Resumen: {analisis.resumen}")
    print(f"Entradas: {analisis.tablas_entrada}   Salidas: {analisis.tablas_salida}")
    print(f"Construcciones: {analisis.construcciones_sas}\n")
    print(f"{'tipo':<14} regla")
    print("-" * 70)
    for regla in analisis.reglas:
        print(f"{regla.tipo:<14} {regla.descripcion}")

    salida = RAIZ / "salida" / f"analisis_{ruta.stem}.json"
    salida.parent.mkdir(exist_ok=True)
    salida.write_text(analisis.model_dump_json(indent=2), encoding="utf-8")
    print(f"\nJSON guardado en {salida.relative_to(RAIZ)}")

    # PASO #4: ¿qué pasa si el modelo responde algo que no cumple el esquema?
    print("\nDemostración: validar un JSON inválido (complejidad='extrema' no existe):")
    try:
        AnalisisSAS.model_validate_json(
            '{"resumen": "x", "tablas_entrada": [], "tablas_salida": [], '
            '"construcciones_sas": [], "reglas": [], "complejidad": "extrema"}'
        )
    except ValidationError as e:
        print(f"  ValidationError -> {e.errors()[0]['loc']}: {e.errors()[0]['msg']}")
        print("  En producción: se registra, se reintenta con el error en el prompt, o se manda a revisión humana.")


if __name__ == "__main__":
    main()
