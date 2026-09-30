# 11 — Instrucciones

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #16 de 26** · [← #15 Preparar el entorno](../10_setup_gcp/README.md) · [#17 Salida estructurada →](../12_salida_estructurada/README.md) · [ruta completa](../../EMPIEZA_AQUI.md)
<!-- ruta:fin -->

## Paso #1 — Correr en simulado

```bash
python 11_gemini_sdk/hola_gemini.py
```

Verás los 3 pasos: prompt simple, con instrucción de sistema, y métricas.

## Paso #2 — Leer el código en este orden

1. [hola_gemini.py](hola_gemini.py): `PASO #1`, `PASO #2`, `PASO #3`.
2. [comun/llm.py](../comun/llm.py): `generar()` → la rama `if config.es_real:` es la llamada real al SDK.
3. [comun/precios.py](../comun/precios.py): cómo se convierte tokens en dólares.

## Paso #3 — En real

Con `MODO=real` en `.env`, vuelve a correrlo. Compara:
- ¿La respuesta del PASO #2 respetó "máximo 5 viñetas, sin introducción"?
- ¿Cuántos `tokens de salida` hubo? Si el modelo "piensa", son más que el texto visible.

## Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| Respuesta vacía (`""`) | Filtro de seguridad o límite de tokens | Revisa `r.candidates[0].finish_reason` (SAFETY, MAX_TOKENS) |
| Ignora la instrucción de sistema | Instrucción ambigua o contradictoria con el prompt | Hazla concreta y verificable ("máximo 5 viñetas") |
| Latencia alta | Modelo grande o mucho *thinking* | Modelo Flash-Lite, o `thinking_config` con nivel bajo |
| 404 / 403 / 429 | Configuración | Tabla del [lab 10](../10_setup_gcp/INSTRUCCIONES.md#si-algo-falla) |

## Retos

1. Cambia `GEMINI_MODEL` a otro modelo de la tabla de precios y compara costo y respuesta.
2. Agrega un PASO #4 que use `generate_content_stream` para imprimir la respuesta mientras llega.
3. Pide lo mismo sin instrucción de sistema pero con las reglas dentro del prompt. ¿Cambia algo?
