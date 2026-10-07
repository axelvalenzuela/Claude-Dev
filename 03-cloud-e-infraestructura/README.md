# 03 · Cloud e infraestructura

Infraestructura como código, contenedores y arquitecturas de referencia en AWS y Google Cloud, con prácticas de seguridad, SRE y GitOps.

| Lab | Qué aprendes | Requiere |
|---|---|---|
| [lab05-kubernetes-local](lab05-kubernetes-local/) | Deployments, ReplicaSets, ConfigMaps, Services e Ingress en un clúster local; self-healing y rolling updates | Docker Desktop, minikube o kind |
| [lab06-sap-s4hana-fiori](lab06-sap-s4hana-fiori/) | Arquitectura de S/4HANA + Fiori capa por capa, assessment y dimensionamiento, Terraform, Ansible y pipelines | Solo lectura y validación (S/4HANA requiere licencia) |
| [lab10-terraform-aws](lab10-terraform-aws/) | 12 micro labs: API Gateway + Lambda, AppSync, EventBridge, Bedrock, Step Functions, 3 niveles, SLO/burn rate, Neptune, MGN, StackSets, RBAC/SCP | Cuenta de AWS ([DESPLIEGUE.md](lab10-terraform-aws/DESPLIEGUE.md)) |
| [lab11-terraform-gcp](lab11-terraform-gcp/) | 17 micro labs: los equivalentes en GCP + 5 de IA generativa (RAG en BigQuery, Vertex AI Search, agente ADK, Model Armor, tuning/batch/evaluación) | Proyecto de GCP ([DESPLIEGUE.md](lab11-terraform-gcp/DESPLIEGUE.md)) |

**Orden sugerido:** lab05 → lab10 → lab11. El lab06 es independiente (arquitectura empresarial SAP).

**Cómo están construidos lab10 y lab11:** módulos compartidos en `modules/`, micro labs en `microlabs/NN-categoria-servicios/`, cada uno con README (despliegue paso a paso, qué modificar en los templates, troubleshooting), smoke test y jobs de GitLab CI. Comparación entre nubes en [lab11-terraform-gcp/docs/GUIA-AWS-GCP.md](lab11-terraform-gcp/docs/GUIA-AWS-GCP.md).

**Relación con otras áreas:** los micro labs GenAI del lab11 (12-16) son la continuación práctica de [04-ia-generativa](../04-ia-generativa/).
