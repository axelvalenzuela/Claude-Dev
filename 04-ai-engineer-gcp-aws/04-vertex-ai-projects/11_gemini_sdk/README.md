# 11 — Gemini con el SDK `google-genai`

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #16 de 26** · [← #15 Preparar el entorno](../10_setup_gcp/README.md) · [#17 Salida estructurada →](../12_salida_estructurada/README.md) · [ruta completa](../../EMPIEZA-AQUI.md)
<!-- ruta:fin -->

**Qué aprendes:** hacer llamadas a Gemini en Vertex AI y leer lo que importa en
producción: tokens, costo y latencia.

## Conceptos

- **SDK unificado `google-genai`**: el mismo cliente sirve para la Gemini Developer API (API key)
  y para Vertex AI (`vertexai=True`, facturado a tu proyecto, con IAM). En empresa se usa Vertex.
- **`contents`** = lo que dice el usuario. **`system_instruction`** = quién es el modelo y sus
  reglas fijas; pesa más que el prompt y no se repite en cada mensaje del usuario.
- **`usage_metadata`**: `prompt_token_count` (entrada), `candidates_token_count` (salida) y
  `thoughts_token_count` (razonamiento interno de modelos con *thinking*, **se cobra como salida**).
- **Temperatura**: la guía de Gemini 3 recomienda dejarla en su valor por defecto (1.0); en la
  familia 2.x se bajaba a ~0.2 para tareas precisas (como 05-rag-app-cloud-run). El código deja `None` = por defecto.

El código que habla con Vertex está en [comun/llm.py](../comun/llm.py), función `generar`.

```python
cliente = genai.Client(vertexai=True, project=PROYECTO, location="global")
r = cliente.models.generate_content(
    model="gemini-3.1-flash-lite",
    contents="Explica este programa SAS...",
    config=types.GenerateContentConfig(system_instruction="Eres un ingeniero senior..."),
)
r.text, r.usage_metadata.prompt_token_count
```

## Para la entrevista

- *"¿Cómo estimas el costo de un proceso con LLM?"* → tokens de entrada × precio + tokens de
  salida (incluye thinking) × precio; medir con muestras reales y proyectar (ejercicio 21).
- *"¿Cómo manejas errores del API?"* → reintento con backoff exponencial solo en 429/5xx.

Siguiente: [INSTRUCCIONES.md](INSTRUCCIONES.md)
