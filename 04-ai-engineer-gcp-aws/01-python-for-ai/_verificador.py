"""Revisa automáticamente tus retos de la parte 0. No necesitas leer este archivo para empezar.

Cada reto se describe como (número, descripción, función_que_lo_prueba, resultado_esperado).
Si tu función todavía devuelve None, el reto aparece como "pendiente".
"""
import math
import sys


def _es_pendiente(resultado) -> bool:
    if resultado is None:
        return True
    return isinstance(resultado, (tuple, list)) and any(r is None for r in resultado)


def _iguales(a, b) -> bool:
    if isinstance(a, float) or isinstance(b, float):
        return isinstance(a, (int, float)) and isinstance(b, (int, float)) and math.isclose(a, b, rel_tol=1e-4)
    if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
        return len(a) == len(b) and all(_iguales(x, y) for x, y in zip(a, b))
    return a == b


def verificar(retos, estricto: bool = False) -> int:
    """Imprime el estado de cada reto y devuelve cuántos están correctos.
    estricto=True (lo usan las soluciones y CI) termina con error si alguno falla."""
    print("\n=== Revisión de tus retos ===")
    correctos = 0
    for numero, descripcion, probar, esperado in retos:
        try:
            resultado = probar()
            if _es_pendiente(resultado):
                estado, detalle = "..", "pendiente: busca 'TU CÓDIGO AQUÍ'"
            elif _iguales(resultado, esperado):
                estado, detalle = "OK", ""
                correctos += 1
            else:
                estado, detalle = "X ", f"devolviste {resultado!r}, se esperaba {esperado!r}"
        except Exception as e:  # noqa: BLE001 - al principiante le mostramos cualquier error
            estado, detalle = "X ", f"error: {type(e).__name__}: {e}"
        print(f"  [{estado}] Reto #{numero}: {descripcion}" + (f"\n         {detalle}" if detalle else ""))

    print(f"\n{correctos} de {len(retos)} retos correctos.")
    if correctos == len(retos):
        print("¡Muy bien! Pasa al siguiente ejercicio de la ruta (EMPIEZA-AQUI.md).")
    else:
        print("Completa los que faltan y vuelve a correr el archivo.")
    if estricto and correctos != len(retos):
        sys.exit(1)
    return correctos
