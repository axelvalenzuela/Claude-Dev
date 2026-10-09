# 13 — RAG con embeddings de Vertex AI

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #18 de 26** · [← #17 Salida estructurada](../12_salida_estructurada/README.md) · [#19 Agente con herramientas →](../14_agente_herramientas/README.md) · [ruta completa](../../EMPIEZA-AQUI.md)
<!-- ruta:fin -->

**Qué aprendes:** la versión real del mini RAG de la parte 1: embeddings de Vertex AI,
índice cacheado, búsqueda por coseno, umbral de "no sé" y respuesta con fuentes.
La base de conocimiento son equivalencias SAS → Python/BigQuery ([conocimiento/](conocimiento/)).

## Conceptos

```
INDEXAR (una vez):  documentos ─> fragmentos ─> embeber(RETRIEVAL_DOCUMENT) ─> índice (.indice_*.json)
PREGUNTAR:          pregunta ─> embeber(RETRIEVAL_QUERY) ─> top-k por coseno ─> ¿supera UMBRAL?
                                                                    ├─ no  ─> "No lo sé"
                                                                    └─ sí  ─> prompt con CONTEXTO ─> Gemini ─> respuesta + fuentes
```

- **`task_type`**: documento vs pregunta. Usar el equivocado no da error, solo peores resultados.
- **Chunking**: aquí cada párrafo + el título del documento (para no perder de qué habla).
- **Umbral**: si nada se parece lo suficiente, no se llama al LLM. Se **calibra** con preguntas reales
  (el valor cambia por modelo de embeddings).
- **Por qué embeddings y no palabras**: "repetidos" encuentra el documento que dice "duplicados".
  El script imprime ambos puntajes para que lo veas.

## Para la entrevista

- *"¿Cómo mejorarías un RAG que responde mal?"* → primero medir *retrieval* (¿trajo el fragmento
  correcto?) separado de *generation*. Luego: chunking, metadatos, búsqueda híbrida
  (palabras + vectores), re-ranking, umbral.
- *"¿Dónde guardas el índice en producción?"* → ejercicio 17 (BigQuery `VECTOR_SEARCH`) y alternativas.

Siguiente: [INSTRUCCIONES.md](INSTRUCCIONES.md)
