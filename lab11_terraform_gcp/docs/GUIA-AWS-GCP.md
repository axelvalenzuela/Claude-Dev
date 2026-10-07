# Guía de estudio: lab10_terraform_aws (AWS) ↔ lab11_terraform_gcp (GCP)

Esta guía conecta los dos laboratorios. lab10_terraform_aws y lab11_terraform_gcp resuelven los **mismos problemas de arquitectura** con Terraform, uno en AWS y otro en Google Cloud. Estudiarlos juntos ayuda a separar el **patrón** (lo que se repite en cualquier nube) del **servicio** (cómo lo implementa cada proveedor).

- AWS: [lab10_terraform_aws/README.md](../../lab10_terraform_aws/README.md) · diagramas en [lab10_terraform_aws/docs/lab10-arquitecturas.pdf](../../lab10_terraform_aws/docs/lab10-arquitecturas.pdf)
- GCP: [lab11_terraform_gcp/README.md](../README.md) · diagramas en [lab11-arquitecturas-gcp.pdf](lab11-arquitecturas-gcp.pdf)

---

## 1. Mapa de micro labs

| Patrón | lab10_terraform_aws (AWS) | lab11_terraform_gcp (GCP) | Lo que se aprende en ambos |
|---|---|---|---|
| Plataforma y CI sin secretos | 00 · S3 + IAM OIDC + boundary | 00 · GCS + Workload Identity Federation | Estado remoto con lock, federación OIDC, separación plan/apply, presupuesto |
| API serverless | 01 · API Gateway REST + Lambda + DynamoDB + Cognito + WAF | 01 · API Gateway + Cloud Run functions + Firestore | Contrato OpenAPI, cuotas por cliente, backend privado, validación, IAM por recurso |
| API GraphQL | 02 · AppSync + resolvers JS | — | Autorización por campo y aislamiento por usuario |
| Orientado a eventos | 03 · EventBridge + SQS + Scheduler | 02 · Pub/Sub + Scheduler + BigQuery | Filtrado en el broker, reintentos, DLQ, replay, consumidores idempotentes |
| IA generativa (chat) | 04 · Bedrock Converse + Guardrails | 03 · Vertex AI Gemini + guardrails en código | Memoria con TTL, guardrails en capas, tope de gasto por tokens e instancias |
| IA orquestada | 05 · Step Functions + Textract + Comprehend | 04 · Workflows + Vision + Natural Language | Integraciones directas con APIs (sin funciones), paralelismo, manejo de errores |
| Web de 3 niveles | 06 · ALB + ASG + RDS Multi-AZ | 05 · LB global + MIG regional + Cloud SQL HA | Cadena de seguridad por capa, multi-zona, secretos en runtime, WAF |
| Kubernetes | — | 06 · GKE Autopilot | Pod Security, Workload Identity, NetworkPolicy, HPA, PDB |
| SRE | 07 · CloudWatch + Synthetics + FIS | 07 · Cloud Monitoring SLOs + uptime | SLI/SLO, presupuesto de error, alertas multi-window multi-burn-rate, GameDay |
| Datos | 08 · Neptune (grafos) | 08 · BigQuery (analítica) | Modelos de datos especializados, acceso privado, control de costos de consulta |
| Migración | 09 · AWS MGN (servidores) | 09 · DMS (bases de datos) | Landing zone, replicación continua, prueba, cutover, rollback |
| Gobernanza multi-cuenta | 10 · StackSets + Organizations | 10 · Carpetas + Org Policies + fábrica de proyectos | Baseline idéntico en N cuentas/proyectos, guardrails heredados |
| Seguridad de cuenta/proyecto | 11 · CloudTrail, Config, GuardDuty, Security Hub, SCP | 11 · Audit logs, sinks, IAM Deny, SCC, VPC-SC | Detección, prevención, RBAC/ABAC, break-glass, respuesta |
| RAG con vectores propios | — (reto del 04) | 12 · BigQuery Vector Search | Chunking, embeddings, umbral de relevancia, citas |
| RAG administrado / grounding | Bedrock Knowledge Bases (reto) | 13 · Vertex AI Search | Build vs buy, grounding metadata |
| Agentes | Bedrock Agents (no incluido) | 14 · ADK | Herramientas, memoria, bucle de agente |
| Seguridad de LLMs | 04 · Bedrock Guardrails | 15 · Model Armor | Injection, jailbreak, PII, filtros de contenido |
| Mejora de modelos | — | 16 · Tuning + batch + evaluación | SFT/LoRA, batch, métricas para decidir |

## 2. Equivalencias de servicios usados

| Necesidad | AWS (lab10_terraform_aws) | Google Cloud (lab11_terraform_gcp) | Diferencia que conviene notar |
|---|---|---|---|
| Estado de Terraform | S3 + `use_lockfile` | GCS (lock nativo) | Ambos ya no necesitan tabla de locks |
| CI sin llaves | IAM OIDC provider + `AssumeRoleWithWebIdentity` | Workload Identity Pool + impersonación de SA | En GCP el filtro va en `attribute_condition` y en el `principalSet` |
| Funciones | Lambda (zip) | Cloud Run functions (build desde source con Cloud Build) | GCP construye un contenedor; Lambda ejecuta el zip directo |
| Identidad de usuarios | Cognito User Pools | Identity Platform / IAM invoker | lab11_terraform_gcp usa identidades de Google (ID token) para simplificar |
| Base documental | DynamoDB | Firestore | Ambas con TTL nativo y recuperación point-in-time |
| Mensajería | EventBridge, SQS | Pub/Sub | Pub/Sub valida esquemas al publicar; EventBridge filtra por contenido JSON |
| Orquestación | Step Functions (ASL JSON) | Workflows (YAML) | Ambos con conectores directos a APIs y `parallel` |
| IA generativa | Bedrock (Converse API) + Guardrails | Vertex AI (Gemini, `google-genai`) | Bedrock tiene guardrails administrados; en lab11_terraform_gcp se implementan en código + safety settings |
| Balanceo y WAF | ALB (regional) + AWS WAF | External Application LB (global) + Cloud Armor | El LB de Google es global con una sola IP anycast |
| Cómputo elástico | Auto Scaling Group | Managed Instance Group regional | Ambos con autohealing y rolling updates |
| Base relacional HA | RDS Multi-AZ | Cloud SQL `REGIONAL` | Ambos con standby síncrono en otra zona |
| Secretos | Secrets Manager (`manage_master_user_password`) | Secret Manager | En AWS RDS administra y rota la contraseña |
| Acceso sin SSH | SSM Session Manager | IAP + OS Login | Ninguno requiere IP pública ni bastion |
| Observabilidad / SLO | CloudWatch metric math + composite alarms | Cloud Monitoring SLO + `select_slo_burn_rate` | GCP tiene objetos SLO nativos |
| Monitoreo sintético | CloudWatch Synthetics | Uptime checks | |
| Gobernanza preventiva | SCPs + permissions boundary | Org Policies + IAM Deny Policies | Las Deny Policies de GCP aplican incluso a Owner |
| Despliegue multi-cuenta | CloudFormation StackSets | Fábrica de proyectos con Terraform `for_each` | |
| Auditoría | CloudTrail + Config | Cloud Audit Logs + Asset Inventory | En GCP los Data Access logs se activan por servicio |
| Detección de amenazas | GuardDuty + Security Hub | Security Command Center | |

## 3. Ruta de estudio sugerida (6 semanas)

| Semana | lab10_terraform_aws (AWS) | lab11_terraform_gcp (GCP) | Entregable |
|---|---|---|---|
| 1 | 00, 11 | 00, 11 | Cuentas preparadas, pipeline OIDC/WIF funcionando, auditoría activa |
| 2 | 01, 02 | 01 | Ambas APIs pasando su smoke test; comparar autorización y cuotas |
| 3 | 03, 05 | 02, 04 | Flujos de eventos con DLQ demostrada; pipeline de documentos |
| 4 | 04 | 03 | Chatbots con memoria y guardrails; tabla de costo por 1,000 conversaciones |
| 5 | 06, 07 | 05, 07 | 3 niveles + GameDay con postmortem (burn rate alcanzado) |
| 6 | 08, 09, 10 | 06, 08, 09, 10 | Datos, migración y gobernanza; presentación final de arquitectura |

Cada semana: `apply` → `test` → romper algo a propósito (revisa la sección de troubleshooting) → `destroy`.

## 4. Modelo de seguridad común

Las dos implementaciones siguen las mismas capas, de afuera hacia adentro:

1. **Guardrails de organización**: SCPs (AWS) / Org Policies (GCP). Nadie puede saltárselos.
2. **Topes por identidad**: permissions boundary (AWS) / IAM Deny Policy (GCP).
3. **RBAC**: roles por función (developer, sre/platform, auditor, finops, break-glass) asignados a grupos.
4. **Condiciones**: ABAC por etiquetas (AWS) / IAM Conditions por recurso o tiempo (GCP).
5. **Políticas de recurso**: quién invoca la función, quién publica en el bus, vistas autorizadas.
6. **Red**: subnets privadas, sin IPs públicas, acceso administrativo por SSM/IAP.

Y el mismo flujo de despliegue: MR → validate/tflint/checkov/plan con identidad de **solo lectura** → merge a `main` protegida → apply **manual** con identidad de despliegue → smoke test → destroy cuando se necesite.

## 5. Costos: qué apagar

| Siempre destruir al terminar | Costo aproximado si queda encendido |
|---|---|
| lab10_terraform_aws/06 three-tier-web | ~USD 95/mes |
| lab10_terraform_aws/08 neptune-graph | ~USD 115/mes |
| lab11_terraform_gcp/05 three-tier-web | ~USD 120/mes |
| lab11_terraform_gcp/06 gke-autopilot | ~USD 95/mes |
| lab11_terraform_gcp/09 dms-migration | ~USD 2/día |

El resto de los labs es serverless y su costo es prácticamente cero sin tráfico. Los labs 00 de ambas nubes crean un presupuesto con alertas.

## 6. Preguntas para repasar

1. ¿Por qué el rol/SA de *plan* puede venir de cualquier rama y el de *apply* solo de `main`? ¿Qué claim del token lo garantiza en cada nube?
2. En el lab de eventos de AWS, ¿por qué la DLQ del target de EventBridge no recibe errores del código de la Lambda?
3. ¿Qué diferencia hay entre alertar por "5XX > 10" y alertar por *burn rate* del presupuesto de error?
4. ¿Qué pasa con un Owner de GCP que intenta crear una llave de service account cuando existe la Deny Policy del lab 11?
5. En las arquitecturas de 3 niveles, ¿qué regla exacta permite que la capa app llegue a la base de datos y por qué se define fuera de los módulos (AWS)?
6. ¿Cómo limita cada chatbot el gasto máximo en el modelo?
