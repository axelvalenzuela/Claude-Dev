# Ejercicio #1 — Tu primer script

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #1 de 26** · [#2 Listas y diccionarios →](../02_listas_y_diccionarios/INSTRUCCIONES.md) · [ruta completa](../../EMPIEZA_AQUI.md)
<!-- ruta:fin -->

**Aprendes:** qué es una variable, los tipos básicos (`str`, `int`, `float`, `bool`), cómo
mostrar resultados con f-strings, decidir con `if` y escribir tu primera función.

## #1 — Ejecuta

Abre una terminal en `04-ia-generativa/lab08-curso-ia/` y escribe:

```bash
python parte0_python/01_primer_script/ejercicio.py
```

Verás lo que imprime la demostración y, al final, los 3 retos como `[..] pendiente`.

## #2 — Lee la demostración

Abre [ejercicio.py](ejercicio.py) y sigue la función `demostracion()` de `PASO #1` a `PASO #7`.
Por cada paso, busca en la terminal la línea que produjo.

## #3 — Resuelve los retos

Baja a **RETOS**. En cada función:
1. Lee el docstring (el texto entre `"""`): dice qué debe devolver y trae un ejemplo.
2. Borra la línea `return None`.
3. Escribe tu código y termina con `return <tu resultado>`.

| Reto | Qué hace |
|---|---|
| #1 `costo_usd` | tokens × precio ÷ 1,000,000 |
| #2 `saludo` | un texto con f-string |
| #3 `es_caro` | una comparación (`>`) |

## #4 — Revisa

Vuelve a correr el comando del #1 hasta ver `3 de 3 retos correctos`. Si te atoras, compara con [solucion.py](solucion.py).

## Si algo falla

| Mensaje | Qué significa | Solución |
|---|---|---|
| `python: command not found` / "no se encontró Python" | Python no está instalado o no está en el PATH | Instálalo marcando "Add to PATH" y abre una terminal nueva |
| `can't open file ... No such file` | Estás en otra carpeta | `cd` a `04-ia-generativa/lab08-curso-ia/` |
| `IndentationError` | Espacios al inicio de la línea mal puestos | Dentro de una función todo va con 4 espacios |
| `SyntaxError` | Algo mal escrito (falta `:`, comilla o paréntesis) | Mira la línea que indica y la anterior |
| `NameError: name 'x' is not defined` | Usas una variable que no existe (o está mal escrita) | Revisa mayúsculas/minúsculas |
| `[X ] devolviste 'Hola, Ana.Bienvenido...'` | El texto no es idéntico | Compara espacio por espacio con el esperado |

## Palabras nuevas

**variable** nombre que guarda un valor · **tipo** qué clase de dato es · **función** bloque
reutilizable que recibe datos y devuelve un resultado · **return** lo que devuelve · **docstring**
explicación de una función entre `"""`.

Siguiente: **Ejercicio #2** → [02_listas_y_diccionarios](../02_listas_y_diccionarios/INSTRUCCIONES.md)
