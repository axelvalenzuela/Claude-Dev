# Micro lab 05: Pipeline de IA para documentos (Step Functions + Textract + Comprehend + Bedrock)

> **Objetivo:** orquestar servicios de IA administrados con Step Functions. Se practican las integraciones SDK directas (sin Lambda), los reintentos con jitter, el paralelismo y el manejo centralizado de errores.

## Arquitectura

```
Usuario ──PutObject──► S3 docs/incoming/*  (SSE-KMS, expira 30 días)
                          │ EventBridge notifications
                          ▼
             Regla "Object Created" (prefijo incoming/) ──► Step Functions STANDARD
                                                           │
     ┌─────────────────────────────────────────────────────┘
     ▼
 ExtractText (Lambda + Textract) ──► Parallel ┬─ DetectEntities (integración SDK Comprehend)
     │ Retry x3 jitter                         └─ Summarize (Lambda + Bedrock Converse)
     │ Catch                                              │
     ▼                                                    ▼
 NotifyFailure (SNS cifrado) ──► Fail          SaveResult (integración DynamoDB PutItem)
```

## Template clave

`statemachine.asl.json.tpl` es el **Amazon States Language** parametrizado con `templatefile()`. Puedes editarlo visualmente en *Workflow Studio* y pegar el JSON de vuelta, conservando las variables `${...}`.

## Pruebas

```bash
B=$(terraform output -raw documents_bucket)
echo "Amazon Web Services anunció en Seattle una nueva región en México con inversión de 5 mil millones de dólares." > demo.txt
aws s3 cp demo.txt s3://$B/incoming/demo.txt
aws stepfunctions list-executions --state-machine-arn $(terraform output -raw state_machine_arn)
aws dynamodb get-item --table-name $(terraform output -raw results_table) --key '{"document_id":{"S":"incoming/demo.txt"}}'
aws s3 cp factura.png s3://$B/incoming/factura.png   # prueba con Textract
aws s3 cp x.docx s3://$B/incoming/x.docx              # formato no soportado: Fail + correo
```

## Parámetros

| Variable | Default | Descripción |
|---|---|---|
| `model_id` | `amazon.nova-lite-v1:0` | Modelo para el resumen |
| `language_code` | `es` | Idioma de Comprehend |
| `document_retention_days` | 30 | Minimización de datos |
| `alert_emails` | `[]` | Destinatarios de las fallas |

GitLab: `LAB05_TFVARS` (File).

<!-- detalle-funcional -->
## Ejecución rápida

```bash
cd lab10
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/05-ai-document-pipeline/terraform.tfvars.example microlabs/05-ai-document-pipeline/terraform.tfvars   # edita owner y demás
bash scripts/lab.sh init  05-ai-document-pipeline
bash scripts/lab.sh apply 05-ai-document-pipeline
bash scripts/lab.sh test  05-ai-document-pipeline      # smoke test automatizado (abajo)
bash scripts/lab.sh destroy 05-ai-document-pipeline
```

Con `make`: `make apply LAB=05-ai-document-pipeline` · `make test LAB=05-ai-document-pipeline`. Requisitos del smoke test: AWS CLI v2, `jq`, `curl` y credenciales con permisos de escritura sobre el lab.

## Prueba automatizada (`scripts/smoke-test.sh`)

Sube `samples/comunicado.txt` a `incoming/`, espera la ejecución (`SUCCEEDED`) y valida en DynamoDB el resumen y las entidades de Comprehend (organización UABC, ubicaciones y persona). Después sube un `.docx` (formato no soportado) y comprueba la ruta de error (`FAILED` + correo), y un archivo fuera de `incoming/` que **no** debe disparar el flujo.

### Resultado esperado (extracto)

```
== Documento válido (incoming/smoke-1759....txt)
  OK   Ejecución (SUCCEEDED)
  OK   Resumen generado: - UABC y AWS lanzan un programa de formación en nube para 2,000 estudiantes...
  OK   Comprehend detectó la organización UABC
  OK   Comprehend detectó una ubicación
  OK   Comprehend detectó una persona
== Documento no soportado (incoming/smoke-1759....docx) -> ruta de error
  OK   Ejecución (FAILED)
SMOKE TEST OK  (7 verificaciones)
```

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| No se crean ejecuciones | Verifica que el bucket tenga `EventBridge = On` (Properties → Event notifications) y que la clave empiece con `incoming/`. |
| `States.Runtime` en SaveResult | El texto superó el tamaño de ítem de DynamoDB (400 KB) por las entidades; baja `MAX_CHARS` en la Lambda extract. |
| Textract `UnsupportedDocumentException` | La API síncrona solo procesa PDF de **una página** e imágenes; para PDFs largos usa `StartDocumentTextDetection` (reto). |
<!-- detalle-funcional -->

## Well-Architected

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Flujo visual auditable; historial de ejecuciones; X-Ray de punta a punta |
| Seguridad | KMS en S3/SNS; `include_execution_data=false` (no registra contenido); IAM por prefijo `incoming/` |
| Confiabilidad | Retry con backoff y jitter; Catch → notificación; STANDARD con exactly-once |
| Eficiencia de rendimiento | Paralelismo; integraciones SDK sin Lambda intermedia |
| Optimización de costos | Pago por transición; concurrencia de 5 en el resumen; expiración de documentos |
| Sostenibilidad | Modelos administrados compartidos; datos eliminados al expirar |

## Storage mínimo

| Recurso | Definición |
|---|---|
| S3 | Standard, expiración de 30 días, versiones antiguas de 30 días |
| DynamoDB | On-demand; 1 ítem (< 400 KB) por documento |
| Logs | Step Functions con nivel ERROR, 30 días |

## Limpieza

`terraform destroy` (el bucket usa `force_destroy=true` en el lab).
