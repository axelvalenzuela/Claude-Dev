# Micro lab 16 (GCP · GenAI): Fine-tuning, batch prediction y evaluación de Gemini

> **Objetivo:** Recorrer el **ciclo de mejora de un modelo**: crear un dataset, medir el modelo base, hacer *supervised fine-tuning* (LoRA) de Gemini, procesar en *batch* a menor costo y **decidir con métricas** si el ajuste vale la pena.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y micro lab 00).

**Tiempo de apply:** ~2 min (infra) · **Costo si queda encendido:** Tuning por tokens de entrenamiento; batch ~50 % del precio online

**Prerrequisitos**

- Micro lab 00
- Python con `pip install -r microlabs/16-genai-tuning-batch-eval/scripts/requirements.txt`

**1. Prepara las variables**

```bash
cd 06-terraform-gcp
cp microlabs/16-genai-tuning-batch-eval/terraform.tfvars.example microlabs/16-genai-tuning-batch-eval/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `project_id` | tu proyecto |
| `owner` | label |
| `region` | región con tuning/batch de Gemini (us-central1) |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del micro lab 00>
bash scripts/lab.sh init  16-genai-tuning-batch-eval
bash scripts/lab.sh plan  16-genai-tuning-batch-eval   # revisa qué se crea
bash scripts/lab.sh apply 16-genai-tuning-batch-eval
```

**3. Después del apply**

- Dataset: `python scripts/gen_dataset.py`
- Batch: `python scripts/batch.py`
- Base: `python scripts/evaluate.py`
- Fine-tuning (con costo): `python scripts/tune.py` y luego `TUNED_MODEL=<endpoint> python scripts/evaluate.py`

**4. Verifica**

```bash
bash scripts/lab.sh test 16-genai-tuning-batch-eval   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 16-genai-tuning-batch-eval
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| scripts/gen_dataset.py | Tu dataset real (formato SFT JSONL) | Siempre |
| scripts/tune.py → `CreateTuningJobConfig` | `epoch_count`, `learning_rate_multiplier`, `adapter_size` | Según calidad y costo |
| scripts/evaluate.py | Métricas de tu tarea | Siempre que cambie la tarea |
| scripts/common.py → `INSTRUCTION`, `LABELS` | Tarea y etiquetas | Otra tarea de clasificación |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
scripts/gen_dataset.py ─► gs://bucket/datasets/train.jsonl, validation.jsonl (formato SFT: systemInstruction + contents user/model)
scripts/evaluate.py    ─► modelo base zero-shot: exactitud por etiqueta, tokens, latencia ─► outputs/eval/*.json
scripts/tune.py        ─► Vertex AI tuning job (SFT, LoRA adapter, 3 épocas) ─► endpoint del modelo ajustado
scripts/evaluate.py    ─► base vs ajustado (misma validación) → decisión con datos
scripts/batch.py       ─► batch prediction: JSONL de peticiones → JSONL de respuestas (asíncrono, más barato)
Terraform: bucket regional + permisos del agente de Vertex AI + alerta de jobs fallidos
```

## Conceptos clave (nivel senior)

| Concepto | Lo que debes saber explicar |
|---|---|
| Prompting → RAG → fine-tuning | Primero prompt engineering; si falta conocimiento, RAG; fine-tuning cuando necesitas formato, estilo o una tarea muy específica de forma consistente y barata. |
| SFT y PEFT/LoRA | El supervised fine-tuning ajusta con pares entrada→salida. LoRA entrena adaptadores pequeños (`adapter_size`) en lugar de todo el modelo: más barato y rápido. |
| Overfitting | Pocas épocas y un set de validación separado; si la pérdida de validación sube mientras la de entrenamiento baja, sobreajusta. |
| Batch prediction | Para cargas que no requieren respuesta inmediata (clasificar millones de registros): ~50 % más barato y sin cuotas de tiempo real. |
| Evaluación | Métricas de tarea (exactitud, F1), métricas por etiqueta, costo y latencia. Para texto libre: Gen AI Evaluation Service con LLM-as-judge (fluidez, groundedness, seguridad). |
| Destilación | Usar un modelo grande para generar datos de entrenamiento de uno pequeño (más barato en producción). |

## Recursos de Terraform y código

| Recurso / archivo | Propósito |
|---|---|
| `module.ml_bucket` | Bucket regional para datasets y resultados con expiración |
| `google_project_service_identity.vertex` + IAM | El agente de Vertex AI lee datasets y escribe resultados |
| `google_monitoring_alert_policy.tuning_job_failed` | Alerta por logs de error de tuning |
| `scripts/*.py` | gen_dataset, evaluate, tune, batch (google-genai) |

## Comandos útiles

```bash
gcloud ai tuning-jobs list --region=us-central1   # (o client.tunings.list())
gcloud ai batch-prediction-jobs list --region=us-central1
gcloud storage cat gs://<bucket>/datasets/train.jsonl | head -2
gcloud ai endpoints list --region=us-central1      # endpoint del modelo ajustado
```

## Prueba automatizada (`scripts/smoke-test.sh`)

Genera y sube el dataset; valida el formato SFT; corre un batch de 5 tickets hasta `JOB_STATE_SUCCEEDED`; evalúa el modelo base (exactitud ≥ 60 %). Con `RUN_TUNING=1` lanza el fine-tuning.

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `Permission denied` del tuning sobre el bucket | El agente `gcp-sa-aiplatform` necesita acceso (incluido); el bucket debe estar en la misma región del job. |
| `Model not supported for tuning` | Verifica qué versiones de Gemini admiten SFT en tu región y ajusta `BASE_MODEL`. |
| Batch tarda mucho | Los batch jobs se encolan; minutos u horas según la carga. |

## Costo

Tuning: tokens del dataset × épocas. Batch: ~50 % del precio online. Evaluación: tokens normales.
