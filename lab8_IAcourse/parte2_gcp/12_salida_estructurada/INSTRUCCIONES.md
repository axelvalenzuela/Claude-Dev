# 12 — Instrucciones

## Paso 1 — Correr

```bash
python 12_salida_estructurada/extraer_reglas.py                          # ventas.sas
python 12_salida_estructurada/extraer_reglas.py comun/sas/clientes.sas   # con macro
python 12_salida_estructurada/extraer_reglas.py comun/sas/inventario.sas # con PROC MEANS
```

El JSON queda en `salida/analisis_<programa>.json`.

## Paso 2 — Leer el código

1. [comun/esquemas.py](../comun/esquemas.py): la forma de la respuesta. Nota las `description`: el modelo las lee.
2. [extraer_reglas.py](extraer_reglas.py): `PASO 2` (pedir con esquema), `PASO 3` (validar), `PASO 4` (qué pasa si no valida).
3. En simulado, las reglas salen de expresiones regulares ([comun/simulado.py](../comun/simulado.py), `_analista`).
   En real, Gemini las "entiende": compara ambos resultados.

## Qué observar

- Cada regla trae su `codigo_sas`: así un auditor puede verificarla.
- El ejemplo del PASO 4: `complejidad="extrema"` se rechaza porque no está en el `Literal`.

## Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| `ValidationError` en real | El modelo devolvió algo fuera del esquema | Revisa qué campo; aclara su `description`; reintenta con el error en el prompt |
| Reglas duplicadas o inventadas | Instrucción débil | Refuerza "no inventes" y exige `codigo_sas` literal |
| Faltan reglas (p. ej. el `ELSE`) | El modelo resume de más | Pide "TODAS las reglas", da un ejemplo, mide recall (lab 16) |
| `400 ... schema` | Tipo que el API no soporta en esquemas | Usa tipos simples (str, int, list, Literal) |

## Retos

1. Agrega el campo `riesgo_migracion: str` a `ReglaNegocio` y vuelve a correr en real.
2. Escribe un programa SAS propio en `comun/sas/` y analízalo.
