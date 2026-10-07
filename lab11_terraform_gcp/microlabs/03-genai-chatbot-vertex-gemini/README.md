# Micro lab 03 (GCP): Chatbot de IA generativa con Vertex AI Gemini

> **Objetivo:** Chatbot privado (solo identidades autorizadas) con Gemini vía SDK `google-genai`, memoria en Firestore con TTL nativo, guardrails en capas y métricas de tokens.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~5 min · **Costo si queda encendido:** Por token

**Prerrequisitos**

- Lab 00
- Vertex AI habilitado (lo hace el lab)

**1. Prepara las variables**

```bash
cd lab11_terraform_gcp
cp microlabs/03-genai-chatbot-vertex-gemini/terraform.tfvars.example microlabs/03-genai-chatbot-vertex-gemini/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `project_id` | tu proyecto |
| `owner` | label |
| `invoker_members` | `["user:tu@correo"]` |
| `build_service_account` | output del lab 00 |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>
bash scripts/lab.sh init  03-genai-chatbot-vertex-gemini
bash scripts/lab.sh plan  03-genai-chatbot-vertex-gemini   # revisa qué se crea
bash scripts/lab.sh apply 03-genai-chatbot-vertex-gemini
```

**3. Después del apply**

- Chat en terminal: `bash microlabs/03-genai-chatbot-vertex-gemini/scripts/chat.sh`

**4. Verifica**

```bash
bash scripts/lab.sh test 03-genai-chatbot-vertex-gemini   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 03-genai-chatbot-vertex-gemini
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| variables.tf → `system_instruction` | Rol, tono, límites del asistente | Siempre |
| variables.tf → `model`, `max_output_tokens`, `history_turns` | Calidad vs costo | Según presupuesto |
| src/chat/main.py → `SAFETY`, `INJECTION`, `BLOCKED_TOPICS` | Guardrails en código | Según dominio (o usa el lab 15) |
| src/chat/main.py → `GenerateContentConfig` | temperature, tools, response_schema | Para function calling o JSON |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
Usuario (gcloud identity token) ──► Cloud Run function chat (privada: run.invoker = invoker_members)
                                        │ 1. guardrail de entrada: longitud, temas bloqueados, prompt injection
                                        │ 2. historial: Firestore messages (session = email#session, TTL 24 h)
                                        │ 3. Vertex AI generate_content (system_instruction + safety BLOCK_LOW_AND_ABOVE)
                                        ▼
                               Gemini (model, vertex_location)
Logging: tokens in/out por request → métrica de logs output_tokens · guardrail_blocks
```

## Recursos de Terraform

| Recurso / archivo | Propósito |
|---|---|
| `src/chat/main.py` | Lógica: guardrails, historial, `client.models.generate_content` |
| `google_firestore_database` + `google_firestore_index` + `google_firestore_field` (ttl) | Historial con índice compuesto y borrado automático |
| `module.chat_sa` | `roles/aiplatform.user` + Firestore condicionado |
| `module.chat_fn` | 512 Mi, 1 vCPU, concurrencia 8, `max_instances` = tope de gasto |
| `google_logging_metric` x2 | Distribución de tokens de salida y conteo de bloqueos |

## Parámetros

| Variable | Default | Nota |
|---|---|---|
| `model` | `gemini-2.5-flash` | Verifica disponibilidad |
| `vertex_location` | `global` |  |
| `invoker_members` | (requerido) | `user:`/`group:` autorizados |
| `blocked_topics` | 3 temas | Regla de negocio |
| `history_turns` / `max_output_tokens` | 6 / 512 | Costo por request |
| `max_instances` | 3 | Tope de gasto |

Variables comunes (`common_variables.tf`): `project_id`, `region` (us-central1), `environment` (dev), `owner` (label), `cost_center`, `build_service_account`.

## Ejecución rápida

```bash
cd lab11_terraform_gcp
gcloud auth login && gcloud auth application-default login
gcloud config set project <PROJECT_ID>
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/03-genai-chatbot-vertex-gemini/terraform.tfvars.example microlabs/03-genai-chatbot-vertex-gemini/terraform.tfvars   # edita los valores
bash scripts/lab.sh init  03-genai-chatbot-vertex-gemini
bash scripts/lab.sh apply 03-genai-chatbot-vertex-gemini
bash scripts/lab.sh test  03-genai-chatbot-vertex-gemini
bash scripts/lab.sh destroy 03-genai-chatbot-vertex-gemini
```

Chat interactivo: `bash microlabs/03-genai-chatbot-vertex-gemini/scripts/chat.sh` (usa tu identidad de gcloud).

## Prueba automatizada (`scripts/smoke-test.sh`)

403 sin ID token; 400 con mensaje vacío; respuesta de Gemini con `finish_reason = STOP` y conteo de tokens; **memoria** (recuerda el nombre del turno anterior); tema bloqueado (`input_guardrail`) y prompt injection bloqueado.

### Resultado esperado (extracto)

```
== Acceso privado
  OK   Sin ID token (403)
== Respuesta de Gemini
  OK   Respuesta: Entendido.
  OK   finish_reason (STOP)
== Memoria (Firestore)
  OK   Recuerda el nombre
== Guardrails
  OK   Tema bloqueado por regla de negocio (input_guardrail)
  OK   Prompt injection (true)
SMOKE TEST OK  (8 verificaciones)
```

## Parámetros en GitLab

| Variable | Tipo | Valor |
|---|---|---|
| `LAB03_TFVARS` | File | incluye `invoker_members` |
| `TF_VAR_system_instruction` | Variable | cambiar el prompt sin tocar código |

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `404 Publisher Model ... not found` | El modelo no está disponible en `vertex_location`; usa `global` o una región soportada. |
| 403 aun con token | Tu identidad no está en `invoker_members`; usa `gcloud auth print-identity-token` de esa cuenta. |
| `The query requires an index` | El índice compuesto tarda unos minutos en construirse tras el primer apply. |

## Google Cloud Architecture Framework (Well-Architected)

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Métricas de tokens y bloqueos en Logging |
| Seguridad | Función privada; guardrails en 3 capas; historial aislado por email |
| Confiabilidad | Timeouts; tope de instancias |
| Rendimiento | Concurrencia 8 por instancia |
| Costos | `max_output_tokens`, `history_turns`, `max_instances`; TTL |
| Sostenibilidad | Modelo flash (menor cómputo) |

## Storage mínimo

| Recurso | Definición |
|---|---|
| Firestore | TTL 24 h: el historial se borra solo |

**Costo aproximado:** Por tokens de Gemini (flash: centavos por millar de requests cortos).
