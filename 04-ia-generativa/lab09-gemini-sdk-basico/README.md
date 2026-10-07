# Laboratorio 9 — Primeros pasos con el SDK de Gemini (`google-genai`)

Scripts cortos para practicar el SDK oficial **`google-genai`** con la Gemini API: llamada básica, *system instructions*, conteo de tokens y control del razonamiento (*thinking*).

## Archivos

| Script | Concepto | Qué observar |
|---|---|---|
| `gemini_call.py` | Llamada mínima: cliente + `generate_content` | `response.text` |
| `gemini_instruction.py` | `system_instruction` para dar un rol al modelo | Cómo cambia el estilo de la respuesta |
| `gemini_tokens.py` | `count_tokens` antes de llamar y `usage_metadata` después | Tokens de entrada, salida y razonamiento |
| `gemini_thinking.py` | `thinking_budget` (0 = sin razonamiento) | `thoughts_token_count` y el costo extra del razonamiento |

## Cómo correrlo

```bash
cd 04-ia-generativa/lab09-gemini-sdk-basico
python -m venv .venv && source .venv/bin/activate     # Windows (Git Bash): source .venv/Scripts/activate
pip install google-genai
export GEMINI_API_KEY=<tu-api-key>                     # https://aistudio.google.com/apikey
python gemini_tokens.py
```

> Los scripts asignan `os.environ['GEMINI_API_KEY'] = "key_exmaple"` como marcador. Para usarlos, borra esa línea y exporta la variable en tu terminal: **nunca escribas una API key real en el código**.

## Notas de revisión (ejercicios)

Estos scripts son de práctica y tienen errores intencionales o por corregir; arreglarlos es parte del ejercicio:

| Archivo | Problema | Corrección |
|---|---|---|
| `gemini_call.py`, `gemini_instruction.py` | `from google import genia` | `from google import genai` (y `genai.Client()`) |
| `gemini_call.py` | `os.environment[...]` | `os.environ[...]` (o mejor, exportar la variable) |
| `gemini_instruction.py` | `types.generateContentConfig` | `types.GenerateContentConfig` |
| `gemini_thinking.py` | `maxOutputTokens=300` como argumento de `generate_content` | `max_output_tokens=300` dentro de `GenerateContentConfig(...)` |
| `gemini_tokens.py` | `thought_token_count`, `input_token_count` | `thoughts_token_count`, `prompt_token_count` |

## Siguiente paso

- Conceptos explicados paso a paso: [lab08-curso-ia](../lab08-curso-ia/).
- Los mismos temas con Vertex AI y en versión de producción: [sdk-examples de lab11](../../03-cloud-e-infraestructura/lab11-terraform-gcp/sdk-examples/) (01 generación, 08 tokens y *thinking*, 12 chat, 16 reintentos).
