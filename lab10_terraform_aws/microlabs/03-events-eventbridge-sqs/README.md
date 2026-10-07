# Micro lab 03: Arquitectura orientada a eventos con Amazon EventBridge

> **Objetivo:** desacoplar productores y consumidores con un bus de eventos. Se practican el filtrado por contenido, la transformación de entrada, los reintentos, la DLQ, el archive con replay, el bus cross-account y EventBridge Scheduler.

## Arquitectura

```
Productores (apps / otras cuentas) ── PutEvents ──► Bus custom  lab10-dev-evt-orders
                                                     │  Archive (replay 7 días)
         ┌───────────────────────────────────────────┼─────────────────────────────┐
         ▼ regla order.created                       ▼ regla amount >= 1000          ▼ regla audit-all
   Lambda order-processor                     SQS high-value-orders           CloudWatch Logs
   (retry 3, edad máx 1 h)                    (input transformer)             /aws/events/...-audit
         │ fallo                                     │ fallo
         └──────────────► SQS DLQ ◄──────────────────┘   ◄── alarma "dlq-not-empty"

EventBridge Scheduler (rate 1h, ventana flexible 15 min) ──► Lambda reporter
```

## Pasos

```bash
terraform init -backend-config=...   # ver README raíz
terraform apply
aws events put-events --entries file://events/order-created.json
```

Resultados esperados:
- A-1001: lo procesa Lambda y queda en el log de auditoría.
- A-1002: lo procesa Lambda y además llega a la cola de alto valor (`aws sqs receive-message --queue-url $(terraform output -raw high_value_queue_url)`).
- A-1003: Lambda falla (no trae `amount`), se reintenta y termina en la DLQ, lo que dispara la alarma.

**Replay:** consola de EventBridge → Archives → *Start replay* (útil después de corregir un bug del consumidor).

## Parámetros

| Variable | Default | Descripción |
|---|---|---|
| `archive_retention_days` | 7 | Retención para replay |
| `producer_account_ids` | `[]` | Cuentas que pueden publicar (bus policy) |
| `high_value_threshold` | 1000 | Umbral del filtro numérico |
| `report_schedule` | `rate(1 hour)` | Expresión de Scheduler |
| `schedule_timezone` | `America/Tijuana` | Zona horaria del cron |

## Parámetros en GitLab

`LAB03_TFVARS` (File).

<!-- detalle-funcional -->
## Ejecución rápida

```bash
cd lab10
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/03-eventbridge-event-driven/terraform.tfvars.example microlabs/03-eventbridge-event-driven/terraform.tfvars   # edita owner y demás
bash scripts/lab.sh init  03-eventbridge-event-driven
bash scripts/lab.sh apply 03-eventbridge-event-driven
bash scripts/lab.sh test  03-eventbridge-event-driven      # smoke test automatizado (abajo)
bash scripts/lab.sh destroy 03-eventbridge-event-driven
```

Con `make`: `make apply LAB=03-eventbridge-event-driven` · `make test LAB=03-eventbridge-event-driven`. Requisitos del smoke test: AWS CLI v2, `jq`, `curl` y credenciales con permisos de escritura sobre el lab.

## Prueba automatizada (`scripts/smoke-test.sh`)

Publica 3 eventos marcados con un ID de corrida y verifica: (1) el processor los registra en sus logs, (2) solo el de `amount ≥ umbral` llega a SQS ya transformado (`priority = HIGH`), (3) la auditoría registra los 3 y (4) el evento sin `amount` falla en Lambda y llega a la **DLQ** a través del destino `on_failure`.

> **Detalle importante:** EventBridge invoca Lambda de forma **asíncrona**. La `dead_letter_config` del *target* solo recibe eventos que EventBridge no pudo **entregar**. Si el **código** falla, el reintento y el destino de falla los administra Lambda (`aws_lambda_function_event_invoke_config`). Por eso el lab configura ambos.

### Resultado esperado (extracto)

```
== Regla 1: Lambda procesa order.created
  OK   Log del processor contiene smoke-1759...-ok
== Regla 2: solo amount >= umbral llega a SQS (input transformer)
  OK   Mensaje de alto valor recibido
  OK   Transformación agregó priority=HIGH (HIGH)
== Regla 3: auditoría registra todos los eventos
  OK   Log de auditoría contiene la corrida
== Falla: evento sin amount termina en la DLQ (Lambda async on_failure, ~1-3 min)
  OK   Evento fallido en la DLQ con contexto de error
SMOKE TEST OK  (7 verificaciones)
```

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| Los eventos no llegan a ninguna regla | Revisa que `EventBusName` sea el bus custom y no `default`; prueba el patrón con `aws events test-event-pattern`. |
| No llega nada a CloudWatch Logs | La *resource policy* de logs (`aws_cloudwatch_log_resource_policy`) es por cuenta y región, con un límite de 10; si lo superaste, consolida políticas. |
| El evento fallido tarda en llegar a la DLQ | Lambda reintenta con backoff (1 min, luego 2 min). Usa `processor_async_retries = 0` para acelerar la práctica. |
<!-- detalle-funcional -->

## Well-Architected

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Auditoría de todos los eventos; replay para recuperación; alarmas en DLQ y FailedInvocations |
| Seguridad | Políticas de SQS con `aws:SourceArn`; Scheduler con `aws:SourceAccount`; SSE en colas; bus policy explícita |
| Confiabilidad | Reintentos, DLQ, consumidores idempotentes, concurrencia reservada |
| Eficiencia de rendimiento | Filtrado en el bus (no en el código) |
| Optimización de costos | USD 1 por millón de eventos; el filtro evita invocaciones innecesarias; ventana flexible en Scheduler |
| Sostenibilidad | Procesamiento solo cuando hay eventos |

## Storage mínimo

| Recurso | Definición |
|---|---|
| Archive | 7 días |
| SQS | Retención de DLQ de 14 días (máximo) |
| Logs | 14 días |

## Limpieza

`terraform destroy`
