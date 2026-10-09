# 01 · Gemini API quickstart (`google-genai`)

Cuatro scripts cortos para dominar lo básico del SDK oficial **`google-genai`** con una API key de Google AI Studio. Es el punto de entrada antes de pasar a Vertex AI en [02-vertex-ai-examples](../02-vertex-ai-examples/).

| Script | Concepto | Qué observar |
|---|---|---|
| [01_generate.py](01_generate.py) | Cliente + `generate_content` | `response.text` |
| [02_system_instruction.py](02_system_instruction.py) | `system_instruction` y `temperature` | Cómo cambia la respuesta con y sin rol |
| [03_count_tokens.py](03_count_tokens.py) | `count_tokens` antes y `usage_metadata` después | Tokens de entrada, salida y razonamiento |
| [04_thinking_budget.py](04_thinking_budget.py) | `thinking_budget` (0, fijo, dinámico) | Latencia y `thoughts_token_count` |

## Cómo correrlo

1. Crea una API key en <https://aistudio.google.com/apikey> (tiene capa gratuita).
2. Desde la raíz del repo:

```bash
cd 03-gemini-sdk/01-gemini-api-quickstart
python -m venv .venv
source .venv/Scripts/activate            # Git Bash en Windows · Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="<tu-api-key>"     # PowerShell: $env:GEMINI_API_KEY="<tu-api-key>"
python 01_generate.py "¿Qué es un embedding?"
python 02_system_instruction.py
python 03_count_tokens.py
python 04_thinking_budget.py
```

Opcional: `export GEMINI_MODEL=gemini-2.5-flash-lite` para probar otro modelo.

> **Nunca** escribas la API key en el código ni la subas a Git. En Vertex AI no se usan API keys: se usa ADC (`gcloud auth application-default login`) y cuentas de servicio.

## Qué modificar para practicar

| Cambia | En | Para ver |
|---|---|---|
| `SYSTEM` y `temperature` | `02_system_instruction.py` | Cómo el rol y la temperatura cambian formato y variabilidad |
| `prompt` por un texto largo | `03_count_tokens.py` | Que el costo crece con la entrada; compara estimado vs. real |
| Los valores del ciclo `(0, 1024, -1)` | `04_thinking_budget.py` | El trade-off calidad / latencia / costo |
| `GEMINI_MODEL` | variable de entorno | Diferencias entre Flash, Flash-Lite y Pro |

## Errores comunes (y el error típico de entrevista)

| Síntoma | Causa | Arreglo |
|---|---|---|
| `ModuleNotFoundError: google.genia` | Error de dedo en el import | `from google import genai` |
| `AttributeError: ... generateContentConfig` | El SDK usa clases en PascalCase | `types.GenerateContentConfig` |
| `TypeError: unexpected keyword 'maxOutputTokens'` | Parámetros en camelCase o fuera de la config | `config=types.GenerateContentConfig(max_output_tokens=300)` |
| `AttributeError: thought_token_count` | Nombre de campo incorrecto | `thoughts_token_count`, `prompt_token_count` |
| `400 API key not valid` | Falta `GEMINI_API_KEY` o está mal | `echo $GEMINI_API_KEY` y vuelve a exportarla |
| `400 ... thinking budget` | Pediste `0` en un modelo Pro | Pro exige un mínimo de 128 |

## Preguntas para practicar

- ¿Qué diferencia hay entre la Gemini API (AI Studio) y Vertex AI? *(autenticación, cuotas, residencia de datos, IAM, VPC-SC)*
- ¿Por qué `count_tokens` y `usage_metadata.prompt_token_count` pueden diferir ligeramente?
- ¿Cuándo apagarías el razonamiento en producción?

## Siguiente paso

- Lo mismo en Vertex AI y en versión de producción: [02-vertex-ai-examples](../02-vertex-ai-examples/) (01 generación, 08 tokens y *thinking*, 12 chat, 16 reintentos).
- Conceptos desde cero (tokens, embeddings, temperatura): [02-ai-fundamentals](../../02-ai-fundamentals/).
