# Parte 0 — Python para IA (ejercicios #1 a #5)

Si nunca has programado en Python, **empieza aquí**. Son 5 ejercicios con justo el Python que
usan los micro labs de IA, con ejemplos de IA (tokens, costos, respuestas JSON, vectores).

| Ejercicio | Carpeta | Aprendes | Lo usarás en |
|---|---|---|---|
| **#1** | [01_primer_script](01_primer_script/) | variables, tipos, f-strings, `if`, funciones básicas | todo |
| **#2** | [02_listas_y_diccionarios](02_listas_y_diccionarios/) | listas, diccionarios, `for`, contar | tokens (#10), bigramas (#12), respuestas JSON |
| **#3** | [03_funciones](03_funciones/) | funciones, `return`, valores por defecto, `zip`, `math` | embeddings (#11), RAG (#14, #18) |
| **#4** | [04_archivos_json_errores](04_archivos_json_errores/) | `import`, archivos, CSV, JSON, `try/except` | salida estructurada (#17), BigQuery (#22) |
| **#5** | [05_clases_y_tipos](05_clases_y_tipos/) | type hints, `@dataclass`, clases, métodos | el SDK de Gemini y los agentes (#16–#20) |

## Cómo funciona cada ejercicio

Cada carpeta tiene 3 archivos:

| Archivo | Para qué |
|---|---|
| `INSTRUCCIONES.md` | Qué hacer, paso #1, #2, #3... y qué hacer si algo falla |
| `ejercicio.py` | Una **demostración** (léela) + **3 retos** que tú completas |
| `solucion.py` | Las respuestas. Míralas solo si te atoras más de 10 minutos |

Al correr `ejercicio.py`, al final aparece una revisión automática:

```
  [OK] Reto #1: costo_usd calcula el costo por tokens
  [..] Reto #2: saludo arma el texto con f-string
         pendiente: busca 'TU CÓDIGO AQUÍ'
  [X ] Reto #3: es_caro compara contra el límite
         devolviste False, se esperaba True
```

`[OK]` correcto · `[..]` todavía no lo haces · `[X ]` lo intentaste pero hay un error (te dice cuál).

## Antes del ejercicio #1: instalar Python y un editor

1. **Python 3.12**: <https://www.python.org/downloads/>. En Windows, en el instalador marca
   **"Add python.exe to PATH"**. Comprueba en una terminal nueva: `python --version`.
   (Alternativa: con `uv` ya instalado, `uv run --python 3.12 python archivo.py` no requiere instalar Python.)
2. **VS Code** con la extensión **Python** (de Microsoft).
3. Abre la carpeta raíz del repo (`ai-engineer-gcp-aws`) en VS Code y usa su terminal (**Terminal > New Terminal**).
   Todos los comandos se escriben desde la raíz del repo.
