"""09 · Evaluación automática: medir la calidad de un prompt con casos de prueba.

Concepto: en producción no se cambia un prompt "a ojo". Se define un set de casos con la
respuesta esperada y se mide el % de aciertos antes de desplegar (quality gate en CI).

    python 09_llm_evaluacion.py
"""

from common import ask

SYSTEM = "Clasifica el sentimiento del comentario. Responde SOLO una palabra: positivo, negativo o neutral."

casos = [
    ("El despliegue fue rapidísimo, excelente servicio", "positivo"),
    ("Se cayó la API tres veces hoy, terrible", "negativo"),
    ("La factura llegó el día 5", "neutral"),
    ("No funciona el login y nadie responde", "negativo"),
    ("Me encantó la nueva consola", "positivo"),
]

aciertos, tokens = 0, 0
for texto, esperado in casos:
    respuesta, usage = ask(texto, system=SYSTEM, max_tokens=10)
    obtenido = (respuesta or "").strip().lower().rstrip(".")
    ok = obtenido == esperado
    aciertos += ok
    tokens += usage.total_token_count
    print(f"{'OK ' if ok else 'ERR'} esperado={esperado:9} obtenido={obtenido:9} | {texto}")

precision = aciertos / len(casos)
print(f"\nPrecisión: {precision:.0%} · tokens totales: {tokens}")
raise SystemExit(0 if precision >= 0.8 else 1)
