# 01 — Reglas vs. aprendizaje

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #6 de 26** · [← #5 Clases y tipos](../../parte0_python/05_clases_y_tipos/INSTRUCCIONES.md) · [#7 Aprender = ajustar números →](../02_aprender_es_ajustar_numeros/README.md) · [ruta completa](../../EMPIEZA_AQUI.md)
<!-- ruta:fin -->

**Idea:** en la programación normal *tú* escribes la regla. En machine
learning le das **ejemplos con la respuesta correcta** y el programa saca
la regla solo.

```bash
python spam.py
```

## Qué observar

- La regla a mano (`"gratis"` o `"dinero"` → spam) falla 2 de 4: no conoce
  `premio` y se equivoca con *"la clase de mañana es gratis"*.
- El método aprendido acierta 4/4. Su "entrenamiento" es solo **contar**
  qué palabras aparecen en spam y cuáles en mensajes normales.
- Nadie le dijo que `premio` es sospechosa: lo dedujo de los ejemplos.

## Retos

1. Agrega a `PRUEBAS` un mensaje que engañe al modelo aprendido. ¿Por qué falló?
2. Quita la mitad de `EJEMPLOS`. ¿Empeora? → **más y mejores datos = mejor modelo**.
3. Pon un ejemplo con la etiqueta equivocada a propósito. Así se ve un dataset "sucio".

**Siguiente:** en [02](../02_aprender_es_ajustar_numeros/) vemos qué significa
"aprender" cuando el modelo tiene números que ajustar.
