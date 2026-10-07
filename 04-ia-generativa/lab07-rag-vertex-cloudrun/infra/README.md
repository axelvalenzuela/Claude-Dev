# Terraform — despliegue del servicio en Cloud Run (opcional)

> **Estado: no ejecutado.** Ni Terraform ni `gcloud` están disponibles en
> el entorno donde se generó este laboratorio, así que esto **no** se
> corrió contra un proyecto real (`init`/`validate`/`plan`/`apply`).
> Revísalo línea por línea antes de aplicarlo — igual que en
> [../../lab6/terraform](../../../03-cloud-e-infraestructura/lab06-sap-s4hana-fiori/terraform/README.md).

Esto es la ruta **opcional** de "infraestructura como código" para
desplegar el lab7. La ruta recomendada para aprender es la manual con
`gcloud` descrita en [../INSTRUCCIONES.md](../INSTRUCCIONES.md) — es
menos código de golpe y se entiende mejor paso a paso la primera vez.
Usa esto cuando ya te quede claro qué hace cada paso manual y quieras la
versión reproducible/versionada.

## Estructura

```
infra/
├── versions.tf             versión de Terraform y provider google (~> 6.0)
├── variables.tf             project_id, region, service_name, container_image, modelos...
├── main.tf                  composición: solo llama a los 3 módulos, sin recursos sueltos
├── outputs.tf                service_url, runtime_service_account
└── modules/
    ├── apis/                habilita aiplatform/run/cloudbuild/artifactregistry
    ├── service_account/      SA dedicada + roles IAM (genérico: recibe var.roles)
    └── cloud_run/            el servicio Cloud Run v2 + IAM público opcional
```

Igual que en [03-cloud-e-infraestructura/lab06-sap-s4hana-fiori/terraform](../../../03-cloud-e-infraestructura/lab06-sap-s4hana-fiori/terraform/README.md), `main.tf`
solo compone módulos — no hay ningún `google_*` suelto fuera de
`modules/*`. A diferencia de lab6 (que usa módulos del registry de
Terraform para AWS), aquí los tres módulos son propios y pequeños: no
existe un módulo de registro tan estándar para "un servicio Cloud Run
con una SA propia" como sí existe `terraform-aws-modules/ec2-instance`.

## Qué crea cada módulo

| Módulo | Recursos | Para qué |
|---|---|---|
| `modules/apis` | `google_project_service` (x4) | Habilita Vertex AI, Cloud Run, Cloud Build y Artifact Registry |
| `modules/service_account` | `google_service_account`, `google_project_iam_member` (uno por rol en `var.roles`) | Identidad dedicada del servicio; `main.tf` le pasa solo `roles/aiplatform.user` — nada de BigQuery, Storage ni IAM. El módulo es genérico a propósito, para poder reusarlo si el lab crece a más de un servicio |
| `modules/cloud_run` | `google_cloud_run_v2_service`, `google_cloud_run_v2_service_iam_member` (opcional) | El servicio en sí: 1 contenedor, `min_instance_count=0` (escala a cero), variables de entorno desde `var.env_vars`, y el acceso público controlado por `var.allow_unauthenticated` |

Esto **no** construye la imagen del contenedor — eso se hace aparte (ver
abajo) porque Terraform no es la herramienta correcta para `docker
build`. Tampoco crea el índice vectorial: lo construye la propia app en
el primer arranque (ver `src/main.py`).

## Requisitos previos

1. Proyecto GCP con facturación habilitada.
2. `gcloud auth login` y `gcloud auth application-default login` ya
   hechos (para que Terraform también tenga credenciales).
3. Un repositorio en Artifact Registry para la imagen:

   ```bash
   gcloud artifacts repositories create lab7 \
     --repository-format=docker \
     --location=us-central1
   ```

4. Construir y publicar la imagen (desde la raíz de `04-ia-generativa/lab07-rag-vertex-cloudrun/`, no desde
   `infra/`):

   ```bash
   gcloud builds submit --tag us-central1-docker.pkg.dev/PROJECT_ID/lab7/rag-gemini:latest
   ```

## Uso

```bash
cd 04-ia-generativa/lab07-rag-vertex-cloudrun/infra
terraform init
terraform plan  -var="project_id=PROJECT_ID" \
                 -var="container_image=us-central1-docker.pkg.dev/PROJECT_ID/lab7/rag-gemini:latest"
terraform apply -var="project_id=PROJECT_ID" \
                 -var="container_image=us-central1-docker.pkg.dev/PROJECT_ID/lab7/rag-gemini:latest"
```

Al terminar, `terraform output service_url` da la URL pública del chat.

Destruir todo (incluye el servicio, no la imagen en Artifact Registry ni
las APIs habilitadas — `disable_on_destroy = false` a propósito, para no
afectar a otros servicios del mismo proyecto):

```bash
terraform destroy -var="project_id=PROJECT_ID" -var="container_image=..."
```

## Diferencia con el camino manual de INSTRUCCIONES.md

`gcloud run deploy --source .` (el camino manual) construye la imagen
**y** despliega en un solo comando, usando Buildpacks o el Dockerfile del
repo automáticamente. Es más rápido para iterar. Esta carpeta separa
"construir la imagen" (`gcloud builds submit`) de "declarar la
infraestructura" (Terraform) a propósito, porque así es como se hace en
un pipeline real de CI/CD — y es el mismo patrón que ya usa
[03-cloud-e-infraestructura/lab06-sap-s4hana-fiori/pipelines](../../../03-cloud-e-infraestructura/lab06-sap-s4hana-fiori/pipelines/README.md) para SAP.
