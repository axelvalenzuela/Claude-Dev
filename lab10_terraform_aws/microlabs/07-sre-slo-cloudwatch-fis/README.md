# Micro lab 07: SRE: SLOs, burn-rate alerts, Synthetics, ChatOps y Chaos Engineering

> **Objetivo:** aplicar prácticas SRE sobre las cargas de los labs 01 y 06: definir SLIs/SLOs, alertar por **consumo del presupuesto de error** (no por umbrales sueltos), monitorear desde fuera con canaries, notificar en Slack y validar la resiliencia con un GameDay en AWS FIS.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~3 min · **Costo si queda encendido:** ~USD 10/mes

**Prerrequisitos**

- Lab 00
- Lab 01 desplegado
- Opcional: lab 06 para FIS

**1. Prepara las variables**

```bash
cd lab10_terraform_aws
cp microlabs/07-sre-slo-cloudwatch-fis/terraform.tfvars.example microlabs/07-sre-slo-cloudwatch-fis/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `owner` | tu correo |
| `lab01_state_bucket` | `$TF_STATE_BUCKET` (lee el API del lab 01) |
| `alert_emails` | on-call |
| `enable_fis` | `true` si el lab 06 está arriba |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>
bash scripts/lab.sh init  07-sre-slo-cloudwatch-fis
bash scripts/lab.sh plan  07-sre-slo-cloudwatch-fis   # revisa qué se crea
bash scripts/lab.sh apply 07-sre-slo-cloudwatch-fis
```

**3. Después del apply**

- Confirma la suscripción SNS
- GameDay: `GENERATE_ERRORS=1 bash scripts/lab.sh test 07-sre-slo-cloudwatch-fis`

**4. Verifica**

```bash
bash scripts/lab.sh test 07-sre-slo-cloudwatch-fis   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 07-sre-slo-cloudwatch-fis
```
<!-- despliegue -->


## Arquitectura

```
                 ┌──────────── CloudWatch ─────────────────────────────────────┐
API GW (lab 01) ─┤ métricas 5XX/Count/Latency                                   │
                 │   ├─ burn_long[fast] (1 h) ─┐                                │
                 │   ├─ burn_short[fast] (5m) ─┴─ Composite "page"   ──┐         │
                 │   ├─ burn_long[slow] (6 h) ─┐                       │         │
                 │   ├─ burn_short[slow](30m) ─┴─ Composite "ticket" ──┤         │
                 │   └─ latency p99                                    │         │
Synthetics canary (5 min) ─► SuccessPercent ─► alarma canary ──────────┤         │
                 │ Dashboard "golden signals" · Logs Insights query    │         │
                 └─────────────────────────────────────────────────────┼─────────┘
                                                                       ▼
                                              SNS (KMS) ─► email / Slack (Amazon Q Developer in chat apps)
AWS FIS ─ stop 1 instancia (tag MicroLab=06) ─ stop condition = alarma canary
```

## Conceptos

| Concepto | Valor en el lab |
|---|---|
| SLI disponibilidad | `1 - 5XXError / Count` del stage |
| SLO | 99.9 % en 30 días, que deja 43 min de presupuesto de error |
| Fast burn (page) | 14.4× en 1 h **y** en 5 min: consume el 2 % del presupuesto en 1 h |
| Slow burn (ticket) | 6× en 6 h **y** en 30 min: consume el 5 % en 6 h |
| SLI latencia | p99 < 1000 ms |

## Pasos

1. Despliega primero el **lab 01** (y el **06** si vas a usar FIS).
2. Configura `health_check_url` con `<api_url>/health`.
3. `terraform apply` y abre el `dashboard_url`.
4. **Genera errores** para ver el burn rate: invoca rutas con un token inválido o fuerza un error en la Lambda.
5. **GameDay**: `aws fis start-experiment --experiment-template-id $(terraform output -raw fis_template_id)`. Durante el experimento observa que el ALB saca la instancia, el ASG compensa y el canary sigue en verde.
6. Redacta un **postmortem sin culpables** en la wiki de GitLab: línea de tiempo, impacto en el presupuesto de error y acciones.

## Parámetros

| Variable | Default | Descripción |
|---|---|---|
| `api_name`, `api_stage`, `api_access_log_group` | lab01 | Objetivo observado |
| `health_check_url` | (requerido) | URL del canary |
| `slo_target` | 0.999 | |
| `latency_p99_ms` | 1000 | |
| `runbook_url` | wiki | Se incluye en la descripción de la alarma |
| `canary_runtime_version` | `syn-nodejs-puppeteer-9.1` | Verifica las versiones vigentes |
| `slack_team_id` / `slack_channel_id` | `""` | ChatOps opcional |
| `enable_fis` | `false` | GameDay |

GitLab: `LAB07_TFVARS` (File). Guarda `SLACK_*` como variables **masked**.

<!-- detalle-funcional -->
## Ejecución rápida

```bash
cd lab10_terraform_aws
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/07-sre-slo-cloudwatch-fis/terraform.tfvars.example microlabs/07-sre-slo-cloudwatch-fis/terraform.tfvars   # edita owner y demás
bash scripts/lab.sh init  07-sre-slo-cloudwatch-fis
bash scripts/lab.sh apply 07-sre-slo-cloudwatch-fis
bash scripts/lab.sh test  07-sre-slo-cloudwatch-fis      # smoke test automatizado (abajo)
bash scripts/lab.sh destroy 07-sre-slo-cloudwatch-fis
```

Con `make`: `make apply LAB=07-sre-slo-cloudwatch-fis` · `make test LAB=07-sre-slo-cloudwatch-fis`. Requisitos del smoke test: AWS CLI v2, `jq`, `curl` y credenciales con permisos de escritura sobre el lab.

## Prueba automatizada (`scripts/smoke-test.sh`)

Comprueba que existen el dashboard y las 2 alarmas compuestas, que el canary está `RUNNING` y que su última corrida fue `PASSED`, y lista el estado de todas las alarmas.

### Práctica completa de burn rate (GameDay)

1. En el lab 01 define `enable_fault_injection = true` y aplica.
2. En este lab define `lab01_state_bucket = "<TF_STATE_BUCKET>"`: los nombres del API, el stage, el log group y la URL del canary se leen solos del estado del lab 01 (`terraform_remote_state`).
3. Ejecuta `GENERATE_ERRORS=1 bash scripts/lab.sh test 07-sre-slo-cloudwatch-fis`. Durante 6 min se envía tráfico con ~90 % de errores 5XX. La prueba espera a que la alarma **fast burn** pase a `ALARM` y llegue la notificación.
4. Observa en el dashboard la tasa de error y cómo la alarma se resetea pocos minutos después de detener el tráfico (ventana corta).
5. Documenta el incidente con la plantilla de postmortem (línea de tiempo, presupuesto consumido, acciones).

### Resultado esperado (extracto)

```
== Componentes
  OK   Dashboard golden-signals
  OK   Estado del canary dev-api-health (RUNNING)
  OK   Alarmas compuestas de burn rate (fast + slow) (2)
== Inyección de errores 5XX en el API del lab 01 (6 min)
  ..   Requests: 3600 · 5XX: 3240
  OK   Se generaron errores 5XX
  OK   Alarma compuesta fast burn en ALARM
SMOKE TEST OK  (7 verificaciones)
```

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| El canary falla con `Runtime version is deprecated` | Actualiza `canary_runtime_version` con `aws synthetics describe-runtime-versions`. |
| Las alarmas burn rate quedan en `INSUFFICIENT_DATA` | Es normal sin tráfico (`treat_missing_data = notBreaching` las mantiene en OK cuando hay datos). Genera tráfico con el smoke test del lab 01. |
| `Error: Unable to find remote state` | El lab 01 debe estar aplicado en el mismo `TF_ENV` y con la key `lab10_terraform_aws/01-serverless-apigw-lambda-dynamodb/<env>.tfstate`. |
| ChatOps: `Slack workspace not authorized` | Autoriza el workspace una vez en la consola de *Amazon Q Developer in chat applications* antes de aplicar. |
<!-- detalle-funcional -->

## Well-Architected

| Pilar | Implementación |
|---|---|
| Excelencia operativa | SLOs, runbooks enlazados, postmortems, dashboards, ChatOps |
| Seguridad | SNS con KMS; el canary oculta headers sensibles; Chatbot con guardrail ReadOnly; FIS limitado por etiqueta |
| Confiabilidad | Alertas multi-window que detectan antes que el cliente; chaos engineering con stop condition |
| Eficiencia de rendimiento | p99 como SLI; métricas de saturación |
| Optimización de costos | Canary cada 5 min (~USD 0.0012 por ejecución); retención de artefactos 7/14 días |
| Sostenibilidad | Alertas accionables (menos ruido y menos reprocesos) |

## Storage mínimo

S3 de artefactos del canary con expiración de 14 días; métricas y dashboards sin storage adicional.
