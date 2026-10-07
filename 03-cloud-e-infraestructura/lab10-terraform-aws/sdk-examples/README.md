# Ejemplos SDK para IA Engineer: AWS (boto3 + Amazon Bedrock)

Diez scripts cortos (20-45 líneas), uno por concepto, que cubren lo que se pregunta y se usa en una posición de **AI/ML Engineer** sobre AWS. Cada archivo empieza con un docstring que explica el concepto, cómo correrlo y qué observar.

Los ejemplos 01-08 solo necesitan acceso a Bedrock. Los 09-10 se conectan con los micro labs desplegados.

## Preparación (5 minutos)

```bash
cd 03-cloud-e-infraestructura/lab10-terraform-aws/sdk-examples
python -m venv .venv && source .venv/bin/activate      # Windows (Git Bash): source .venv/Scripts/activate
pip install -r requirements.txt
aws sso login && export AWS_PROFILE=lab10 AWS_REGION=us-east-1
# Bedrock -> Model access: habilita "Amazon Nova Lite" y "Titan Text Embeddings V2"
python 01_bedrock_converse.py
```

Variables opcionales: `BEDROCK_MODEL` (default `amazon.nova-lite-v1:0`), `BEDROCK_EMBED_MODEL` (default `amazon.titan-embed-text-v2:0`). Cambiar de modelo no requiere tocar el código: la Converse API es la misma para todos.

## Índice

| # | Archivo | Concepto | Qué observar | Pregunta típica de entrevista |
|---|---|---|---|---|
| 01 | `01_bedrock_converse.py` | Llamada básica con la Converse API | `stopReason`, tokens, latencia | ¿Cómo cambiarías de modelo sin reescribir la app? |
| 02 | `02_bedrock_streaming.py` | Streaming de respuesta | Time to first token vs. tiempo total | ¿Qué métrica de latencia importa en un chat? |
| 03 | `03_bedrock_tool_use.py` | Tool use / function calling (bucle de agente) | El modelo pide la función; tu código la ejecuta | ¿Quién ejecuta la herramienta: el modelo o la app? |
| 04 | `04_bedrock_structured_output.py` | Salida estructurada forzando una herramienta | JSON con enum validado | ¿Cómo garantizas JSON válido de un LLM? |
| 05 | `05_bedrock_embeddings_search.py` | Embeddings + similitud coseno | Encuentra el documento sin palabras en común | ¿Por qué búsqueda semántica y no por palabras clave? |
| 06 | `06_rag_minimo.py` | RAG: recuperar + generar con citas | Responde solo con el contexto y cita la fuente | ¿Cómo reduces alucinaciones? |
| 07 | `07_bedrock_guardrail.py` | ApplyGuardrail independiente del modelo | PII anonimizada, tema bloqueado, prompt injection | ¿Dónde pondrías los guardrails en la arquitectura? |
| 08 | `08_llm_evaluacion.py` | Evaluación con casos de prueba (quality gate) | Precisión y tokens; exit code para CI | ¿Cómo sabes que un cambio de prompt no empeoró nada? |
| 09 | `09_eventbridge_publicar.py` | Integración por eventos (micro lab 03) | El evento llega a Lambda y, si es de alto valor, a SQS | ¿Por qué desacoplar con eventos? |
| 10 | `10_stepfunctions_documento.py` | Pipeline de IA asíncrono (micro lab 05) | Subir archivo → consultar resultado | ¿Cómo expones un proceso de IA que tarda minutos? |

## Ruta sugerida

1. **Fundamentos del modelo:** 01 → 02 → 08 (aprende a medir antes de optimizar).
2. **Integración con sistemas:** 04 → 03 (de texto libre a datos y acciones).
3. **Conocimiento propio:** 05 → 06 (RAG desde cero, sin frameworks).
4. **Producción:** 07 → 09 → 10 (seguridad, eventos y orquestación con los micro labs).

## Retos para practicar

- 03: agrega una segunda herramienta (p. ej. `convertir_moneda`) y observa cómo el modelo encadena llamadas.
- 06: carga los README de los micro labs como base de conocimiento y pregúntale cómo desplegar uno.
- 08: agrega 10 casos difíciles (sarcasmo, negaciones) y compara dos modelos con `BEDROCK_MODEL`.
- Compara cada ejemplo con su equivalente en GCP: [03-cloud-e-infraestructura/lab11-terraform-gcp/sdk-examples](../../lab11-terraform-gcp/sdk-examples).
