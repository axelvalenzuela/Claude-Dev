# 09 — Mini RAG (05-rag-app-cloud-run en miniatura, sin nube)

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #14 de 26** · [← #13 Temperatura](../08_temperatura/README.md) · [#15 Preparar el entorno →](../../04-vertex-ai-projects/10_setup_gcp/README.md) · [ruta completa](../../EMPIEZA-AQUI.md)
<!-- ruta:fin -->

**El problema:** un LLM no conoce *tus* documentos (el menú de tu
cafetería, los manuales de tu empresa). Si le preguntas, inventa (ejercicio 07).

**La solución, RAG** (*Retrieval-Augmented Generation*): antes de
preguntarle, **buscas** los fragmentos relevantes y se los **pegas en el
prompt**.

```
documentos ─1─> fragmentos ─2─> vectores ──┐
                                           ├─3─> top-k más parecidos ─4─> prompt ─5─> LLM ─> respuesta
pregunta ─────────────────────2─> vector ──┘
```

| Paso | Qué hace | Aquí | En 05-rag-app-cloud-run |
|---|---|---|---|
| 1. Chunking | Partir documentos en pedazos | `partir()` | `src/chunking.py` |
| 2. Vectores | Texto → vector | `vectorizar()` (conteo de palabras) | `text-embedding-005` en `src/gemini_client.py` |
| 3. Retrieval | Coseno contra todos, quedarse con los mejores | `buscar()` | `src/vector_store.py` |
| 4. Prompt | Instrucciones + CONTEXTO + PREGUNTA | `armar_prompt()` | `src/rag_engine.py` |
| 5. Generar | Mandar el prompt al LLM | *solo se imprime* | Gemini en `src/gemini_client.py` |

```bash
python mini_rag.py
python mini_rag.py "¿Tienen leche de avena?"
```

## Qué observar

- **"¿A qué horas abren los sábados?"** → recupera el fragmento de `horarios.md` y arma el prompt.
- **"¿Quién es el dueño?"** → nada se parece: el agente diría *"no lo sé"*
  en vez de inventar. Eso es lo que hace la instrucción *"usa ÚNICAMENTE el CONTEXTO"*.
- **"¿Puedo llevar a mi perro?"** → también dice "no sé", aunque
  `politicas.md` habla de **mascotas**. Es el problema del ejercicio 06:
  contar palabras no sabe que perro ≈ mascota. Un modelo de embeddings real sí.

## Retos

1. Agrega un documento `"eventos.md"` a `DOCUMENTOS` y pregunta por él.
2. Cambia `TOP_K` a 1 y a 4. ¿Qué cambia en el CONTEXTO?
3. Agrega `"perro": ...` como sinónimo: normaliza `perro` → `mascotas` dentro de `normalizar()`.
   Estás arreglando a mano lo que un modelo de embeddings hace solo.
4. Copia el prompt impreso y pégalo en Claude o Gemini. Esa es la respuesta final de RAG.

## Y ahora, 05-rag-app-cloud-run

Ya viste cada pieza. Abre [05-rag-app-cloud-run/src/rag_engine.py](../../05-rag-app-cloud-run/src/rag_engine.py)
y reconoce los pasos 3, 4 y 5. Lo nuevo en 05-rag-app-cloud-run es solo **quién** hace los
pasos 2 y 5 (Vertex AI en la nube) y **cómo** se publica (FastAPI, Docker,
Cloud Run).
