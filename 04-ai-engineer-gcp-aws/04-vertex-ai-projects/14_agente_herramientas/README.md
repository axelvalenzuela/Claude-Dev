# 14 — Un agente con herramientas (function calling)

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #19 de 26** · [← #18 RAG con embeddings](../13_embeddings_rag/README.md) · [#20 Multi-agente SAS → Python →](../15_multi_agente/README.md) · [ruta completa](../../EMPIEZA-AQUI.md)
<!-- ruta:fin -->

**Qué aprendes:** qué es realmente un "agente": un LLM dentro de un ciclo que decide qué
herramienta usar, recibe el resultado y sigue hasta poder responder.

## Conceptos

```
pregunta ─> LLM ─┬─ "llama a listar_programas_sas()" ─> TU código la ejecuta ─> resultado ─> LLM ─┐
                 │                                                                                │
                 └─ respuesta final <────────────────────── (repite hasta MAX_PASOS) ─────────────┘
```

- **El modelo nunca ejecuta nada**: solo *pide* la herramienta con argumentos. Tu código decide
  si la ejecuta. Eso es un punto de control de seguridad.
- **Las herramientas son funciones de Python** ([herramientas.py](herramientas.py)). El SDK convierte
  nombre + docstring + type hints en su descripción → **el docstring es parte del prompt**.
- **Llamadas en paralelo**: el modelo puede pedir varias herramientas a la vez (aquí,
  `contar_complejidad` para los 3 programas).
- **Errores como resultado**: si una herramienta falla, se le devuelve el error al modelo para que se corrija.
- **Límite de pasos**: sin él, un agente confundido se cicla y gasta.
- En [comun/llm.py](../comun/llm.py), `SesionAgente` apaga el *automatic function calling* del SDK
  para que veas cada paso; en real guarda el turno del modelo tal cual (Gemini 3 necesita sus
  *thought signatures* de vuelta).

## Para la entrevista

- *"¿Qué diferencia hay entre un chatbot y un agente?"* → el agente actúa: elige herramientas,
  observa resultados y decide el siguiente paso, con un objetivo.
- *"¿Cómo evitas que un agente haga algo peligroso?"* → herramientas de solo lectura por defecto,
  validación de argumentos (ver `leer_programa_sas`, que impide salir de la carpeta), límite de
  pasos, confirmación humana para acciones irreversibles.

Siguiente: [INSTRUCCIONES.md](INSTRUCCIONES.md)
