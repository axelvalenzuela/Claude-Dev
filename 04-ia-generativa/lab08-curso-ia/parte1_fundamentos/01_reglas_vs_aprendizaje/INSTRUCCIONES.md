# 01 — Instrucciones

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #6 de 26** · [← #5 Clases y tipos](../../parte0_python/05_clases_y_tipos/INSTRUCCIONES.md) · [#7 Aprender = ajustar números →](../02_aprender_es_ajustar_numeros/README.md) · [ruta completa](../../EMPIEZA_AQUI.md)
<!-- ruta:fin -->

## Paso #1 — Ejecuta y observa

```bash
python parte1_fundamentos/01_reglas_vs_aprendizaje/spam.py     # desde 04-ia-generativa/lab08-curso-ia/
```

Anota: ¿cuántos aciertos tuvo la regla y cuántos el método aprendido?

## Paso #2 — Recorrido guiado del código ([spam.py](spam.py))

1. `EJEMPLOS` y `PRUEBAS`: datos de **entrenamiento** vs datos **nuevos**. Nunca se prueba con lo mismo que se entrenó.
2. `clasificar_con_regla`: programación clásica. Tú decides la lógica.
3. `entrenar`: solo `Counter.update`, contar palabras por clase. Ese conteo ES el modelo.
4. `puntaje`: suma logaritmos de probabilidades (el `+1` evita que una palabra nunca vista dé cero).
5. `main`: `PASO #1` entrenar, `PASO #2` ver lo aprendido, `PASO #3` comparar.

## Paso #3 — Experimento guiado

Agrega a `PRUEBAS` el mensaje `("gratis la reunion de mañana", "normal")`. Predice qué dirá cada
método **antes** de correrlo. Después córrelo. ¿Acertaste? ¿Por qué el modelo aprendido lo clasificó así?

## Si algo falla

| Síntoma | Solución |
|---|---|
| `python` no se reconoce | Instala Python 3.10+ o usa `uv run --no-project --python 3.12 python spam.py` |
| Acentos raros en la consola de Windows | PowerShell: `$env:PYTHONIOENCODING="utf-8"` · cmd: `set PYTHONIOENCODING=utf-8` |
| `SyntaxError` tras editar | Revisa comas y paréntesis en la tupla que agregaste |

## Autoevaluación

¿Por qué "más datos" mejora al método aprendido pero no a la regla?
