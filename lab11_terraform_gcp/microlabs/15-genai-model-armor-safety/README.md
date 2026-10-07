# Micro lab 15 (GCP · GenAI): Seguridad de LLMs con Model Armor

> **Objetivo:** Proteger cualquier aplicación de LLM con **Model Armor**: detectar prompt injection y jailbreaks, filtrar contenido dañino, evitar fuga de datos sensibles y URLs maliciosas, **antes y después** del modelo.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~5 min · **Costo si queda encendido:** Por evaluación (millones de tokens gratis al mes)

**Prerrequisitos**

- Lab 00 (`build_service_account`)
- Model Armor disponible en `region` (regional)

**1. Prepara las variables**

```bash
cd lab11_terraform_gcp
cp microlabs/15-genai-model-armor-safety/terraform.tfvars.example microlabs/15-genai-model-armor-safety/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `project_id` | tu proyecto |
| `owner` | label |
| `invoker_members` | `["user:tu@correo"]` |
| `region` | región de Model Armor |
| `build_service_account` | output del lab 00 |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>
bash scripts/lab.sh init  15-genai-model-armor-safety
bash scripts/lab.sh plan  15-genai-model-armor-safety   # revisa qué se crea
bash scripts/lab.sh apply 15-genai-model-armor-safety
```

**3. Después del apply**

- Prueba manual: `gcloud model-armor templates sanitize-user-prompt <template> --location=<region> --user-prompt-data='Ignore previous instructions'` (si tu versión de gcloud lo soporta)

**4. Verifica**

```bash
bash scripts/lab.sh test 15-genai-model-armor-safety   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 15-genai-model-armor-safety
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| variables.tf → `rai_confidence`, `injection_confidence` | Sensibilidad de los filtros | Falsos positivos/negativos |
| main.tf → `filter_config.sdp_settings` | `basic_config` o `advanced_config` (plantillas de DLP propias) | Datos sensibles de tu país |
| src/chat/main.py | Qué hacer al bloquear (mensaje, log, escalar) | Experiencia de usuario |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
Usuario ─► Cloud Run function safe-chat
              1. Model Armor sanitize_user_prompt ── MATCH_FOUND ─► 200 {blocked, stage: prompt, findings}
              2. Gemini generate_content
              3. Model Armor sanitize_model_response ── MATCH_FOUND ─► 200 {blocked, stage: response}
              4. respuesta
Template (regional): pi_and_jailbreak · RAI (odio, acoso, sexual, peligroso) · SDP (datos sensibles) · malicious URIs
Logging: cada evaluación queda registrada (log_sanitize_operations)
```

## Conceptos clave (nivel senior)

| Concepto | Lo que debes saber explicar |
|---|---|
| Prompt injection directa e indirecta | Directa: el usuario pide ignorar instrucciones. Indirecta: el ataque viene en un documento o página que el modelo lee (RAG, agentes). Hay que revisar también el contexto recuperado. |
| Defensa en capas | Model Armor (filtro independiente del modelo) + safety settings del modelo + instrucciones + validación de salidas + mínimo privilegio en herramientas. |
| Entrada y salida | La salida también se revisa: el modelo puede filtrar PII o generar URLs maliciosas. |
| Sensitive Data Protection | `basic_config` detecta tipos comunes; `advanced_config` usa tus plantillas de DLP (p. ej. RFC, CURP). |
| Umbrales | LOW_AND_ABOVE bloquea más (más falsos positivos); HIGH bloquea menos. Ajústalos con datos de evaluación. |
| Floor settings | A nivel organización/proyecto se pueden imponer mínimos que ningún template puede relajar. |

## Recursos de Terraform y código

| Recurso / archivo | Propósito |
|---|---|
| `google_model_armor_template.this` | Filtros y umbrales; logging de operaciones |
| `src/chat/main.py` | Cliente `modelarmor_v1` con endpoint regional; bloqueo en entrada y salida |
| `module.chat_sa` | `modelarmor.user` + `aiplatform.user` |

## Comandos útiles

```bash
gcloud model-armor templates list --location=<region>
gcloud model-armor templates describe <template> --location=<region>
gcloud logging read 'resource.type="modelarmor.googleapis.com/SanitizeOperation"' --limit=5
```

## Prueba automatizada (`scripts/smoke-test.sh`)

Prompt benigno pasa; prompt injection bloqueado en la etapa `prompt` por `pi_and_jailbreak`; número de tarjeta bloqueado por SDP; URL de malware de prueba bloqueada; evaluaciones visibles en Cloud Logging.

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `404` al llamar Model Armor | El endpoint debe ser regional (`modelarmor.<region>.rep.googleapis.com`) y coincidir con la región del template. |
| Todo se bloquea | Baja la sensibilidad (`MEDIUM_AND_ABOVE`/`HIGH`) y revisa `findings` para ver qué filtro dispara. |
| SDP no detecta datos locales | Usa `advanced_config` con una plantilla de inspección propia. |

## Costo

Gratis hasta el umbral mensual de tokens evaluados; después, por millón de tokens.
