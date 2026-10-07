# Micro lab 07 (GCP): SRE con Cloud Monitoring: SLOs, burn rate, uptime y dashboard

> **Objetivo:** Definir SLOs request-based sobre el servicio del lab 01 y alertar por **consumo del presupuesto de error** (multi-window, multi-burn-rate), con uptime checks y dashboard de señales doradas.

## Arquitectura

```
Cloud Run (función items, lab 01) ─► métricas run.googleapis.com/request_count, request_latencies
                │
Custom service lab11-dev-sre-api
  ├─ SLO availability 99.5 % / 28 d  (bad = 5xx, total = todas)
  └─ SLO latency 95 % < 800 ms        (distribution_cut)
Alert policies (AND de 2 condiciones select_slo_burn_rate):
  ├─ fast: 14.4x en 1 h y 5 min  → CRITICAL
  └─ slow: 6x    en 6 h y 30 min → WARNING
Uptime check /health desde 3 regiones ─► alerta si falla en 2+
Dashboard: tráfico por clase, p50/p95/p99, instancias, burn rate, uptime
```

## Recursos de Terraform

| Recurso / archivo | Propósito |
|---|---|
| `data.terraform_remote_state.lab01` | Lee servicio y host del lab 01 si defines `lab01_state_bucket` |
| `google_monitoring_custom_service` + `google_monitoring_slo` x2 | SLIs request-based |
| `google_monitoring_alert_policy.burn` | `select_slo_burn_rate(slo, ventana)` combinadas con AND |
| `google_monitoring_uptime_check_config` | Caja negra con SSL validado |
| `google_monitoring_dashboard` + `dashboard.json.tpl` | Golden signals |

## Parámetros

| Variable | Default | Nota |
|---|---|---|
| `lab01_state_bucket` | `null` | Integra con el lab 01 |
| `availability_goal` | 0.995 | ~201 min de presupuesto/28 d |
| `latency_goal` / `latency_threshold_ms` | 0.95 / 800 |  |
| `alert_emails` | `[]` | Canales de email |

Variables comunes (`common_variables.tf`): `project_id`, `region` (us-central1), `environment` (dev), `owner` (label), `cost_center`, `build_service_account`.

## Ejecución rápida

```bash
cd lab11
gcloud auth login && gcloud auth application-default login
gcloud config set project <PROJECT_ID>
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/07-sre-observability/terraform.tfvars.example microlabs/07-sre-observability/terraform.tfvars   # edita los valores
bash scripts/lab.sh init  07-sre-observability
bash scripts/lab.sh apply 07-sre-observability
bash scripts/lab.sh test  07-sre-observability
bash scripts/lab.sh destroy 07-sre-observability
```

**GameDay:** (1) `enable_fault_injection = true` en el lab 01, (2) `GENERATE_ERRORS=1 bash scripts/lab.sh test 07-sre-observability`. El test envía ~90 % de 5XX durante 6 min y verifica que el burn rate de 5 min supere 14.4 (alerta fast). (3) Documenta el postmortem: línea de tiempo, presupuesto consumido y acciones.

## Prueba automatizada (`scripts/smoke-test.sh`)

2 SLOs definidos; 2 políticas de burn rate y 1 de uptime; uptime check sobre el host del gateway que responde `/health`. Con `GENERATE_ERRORS=1`: errores 5XX generados y burn rate de 5 min > 14.4.

### Resultado esperado (extracto)

```
== Servicio y SLOs
  ..   Disponibilidad 99.5% (28 días)
  ..   95% de requests < 800 ms
  OK   SLOs definidos (2)
== Alertas
  OK   Políticas de burn rate (fast + slow) (2)
== Inyección de errores (6 min) en el lab 01
  OK   Burn rate 5 min = 178.2 (> 14.4: la alerta fast burn se abre)
SMOKE TEST OK  (7 verificaciones)
```

## Parámetros en GitLab

| Variable | Tipo | Valor |
|---|---|---|
| `LAB07_TFVARS` | File | terraform.tfvars |

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| Los SLO muestran `No data` | Se necesita tráfico; corre el smoke test del lab 01. |
| `Error 400: ... select_slo_burn_rate` | El nombre del SLO debe ser el completo `projects/.../services/.../serviceLevelObjectives/...` (lo arma el lab). |
| Uptime check falla con SSL | El host debe ser el gateway sin `https://` (lo toma del remote state). |

## Google Cloud Architecture Framework (Well-Architected)

| Pilar | Implementación |
|---|---|
| Excelencia operativa | SLOs, runbooks, postmortems, dashboard |
| Seguridad | Alertas sin datos sensibles |
| Confiabilidad | Alertas por presupuesto de error; caja negra multi-región |
| Rendimiento | SLO de latencia p95 |
| Costos | Métricas de Cloud Run gratis; uptime checks gratis |
| Sostenibilidad | Menos alertas ruidosas |

## Storage mínimo

| Recurso | Definición |
|---|---|
| Monitoring | Métricas retenidas 6 semanas sin costo adicional |

**Costo aproximado:** Gratis dentro de las cuotas de Cloud Monitoring.
