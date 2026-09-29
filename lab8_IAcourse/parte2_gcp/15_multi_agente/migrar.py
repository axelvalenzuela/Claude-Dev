"""Micro lab 15 — Flujo multi-agente para migrar un programa SAS a Python.

Este archivo solo es la "puerta de entrada". El código que hay que estudiar está en:
    comun/agentes.py      los 3 agentes LLM (analista, convertidor, documentador)
    comun/validacion.py   el validador determinista (ejecutar + reconciliar)
    comun/orquestador.py  el flujo que los coordina, con ciclo de autocorrección

Correr (desde parte2_gcp/):
    python 15_multi_agente/migrar.py                  # ventas.sas (tiene datos de prueba)
    python 15_multi_agente/migrar.py clientes.sas     # sin datos de prueba -> REQUIERE_REVISION

En modo simulado el convertidor se equivoca A PROPÓSITO en su primer intento
(aplica el umbral sobre `monto` en vez de `total_con_iva`) para que veas al
validador atrapar el error y al convertidor corregirlo con la retroalimentación.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comun.config import RAIZ, config  # noqa: E402
from comun.orquestador import migrar  # noqa: E402


def guardar(resultado) -> Path:
    carpeta = RAIZ / "salida" / Path(resultado.programa).stem
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "transformar.py").write_text(resultado.codigo_python, encoding="utf-8")
    (carpeta / "DOCUMENTACION.md").write_text(resultado.documentacion, encoding="utf-8")
    (carpeta / "analisis.json").write_text(resultado.analisis.model_dump_json(indent=2), encoding="utf-8")
    (carpeta / "bitacora.txt").write_text("\n".join(resultado.bitacora), encoding="utf-8")
    return carpeta


def main():
    programa = sys.argv[1] if len(sys.argv) > 1 else "ventas.sas"
    codigo_sas = (RAIZ / "comun" / "sas" / programa).read_text(encoding="utf-8")
    print(f"Modo {config.modo} | modelo {config.modelo} | programa {programa}\n")

    resultado = migrar(codigo_sas, programa)

    carpeta = guardar(resultado)
    print(f"\nESTADO: {resultado.estado}")
    print(f"Intentos: {resultado.intentos} | tokens: {resultado.tokens} | costo: ${resultado.costo_usd:.6f} USD")
    print(f"Archivos en: {carpeta.relative_to(RAIZ)}/ (transformar.py, DOCUMENTACION.md, analisis.json, bitacora.txt)")
    print("\n--- Código Python final ---")
    print(resultado.codigo_python)


if __name__ == "__main__":
    main()
