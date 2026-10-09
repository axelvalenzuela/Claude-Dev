# 09 — Instrucciones

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #14 de 26** · [← #13 Temperatura](../08_temperatura/README.md) · [#15 Preparar el entorno →](../../04-vertex-ai-projects/10_setup_gcp/README.md) · [ruta completa](../../EMPIEZA-AQUI.md)
<!-- ruta:fin -->

## Paso #1 — Ejecuta y observa

```bash
python 02-ai-fundamentals/09_mini_rag/mini_rag.py
python 02-ai-fundamentals/09_mini_rag/mini_rag.py "¿Tienen leche de avena?"
```

## Paso #2 — Recorrido guiado del código ([mini_rag.py](mini_rag.py))

Sigue los pasos numerados del docstring:
1. `partir` (chunking con traslape) → 2. `vectorizar` → 3. `buscar` (coseno contra todos) →
4. `armar_prompt` → 5. se imprime el prompt que iría al LLM.

## Paso #3 — Experimento guiado

1. Cambia `UMBRAL` a `0.0` y pregunta "¿Quién es el dueño?". Ahora SÍ arma un prompt, pero con
   contexto irrelevante: así nacen las respuestas inventadas.
2. Copia un prompt impreso y pégalo en un chat de IA. Esa sería la respuesta final del RAG.

## Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| Siempre "no lo sé" | Las palabras de la pregunta no están en los documentos | Es la limitación del conteo; con embeddings (parte 2, ejercicio 13) mejora |
| Recupera un fragmento que no tiene que ver | Palabras comunes compartidas | Agrega esas palabras a `PALABRAS_VACIAS` |

## Autoevaluación

Nombra los 5 pasos de RAG y en qué archivo de 05-rag-app-cloud-run vive cada uno.
