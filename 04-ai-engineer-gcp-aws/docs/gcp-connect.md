# Conectar los ejercicios a Google Cloud (de simulado a real)

Todo en `04-vertex-ai-projects/` corre **gratis en modo simulado**. Esta guía es para cuando
quieras ver a Gemini, BigQuery y Cloud Run de verdad. Costos: ver
[gcp-costs.pdf](gcp-costs.pdf) (resumen: menos de 2 USD para correr todo una vez).

## Lo que te falta (checklist)

| # | Qué | Cómo sabes que ya está |
|---|---|---|
| 1 | Cuenta de Google Cloud con facturación | `gcloud billing accounts list` muestra una cuenta `OPEN: True` |
| 2 | Un proyecto dedicado | `gcloud config get-value project` muestra su ID |
| 3 | gcloud CLI | `gcloud --version` |
| 4 | Credenciales locales (ADC) | `gcloud auth application-default print-access-token` imprime un token |
| 5 | Terraform ≥ 1.6 | `terraform -version` |
| 6 | Recursos creados (APIs, bucket, dataset, cuenta de servicio) | `terraform output` en `infra/` |
| 7 | `04-vertex-ai-projects/.env` con `MODO=real` | `python 10_setup_gcp/verificar_entorno.py` sale sin `[FALLA]` |

## Paso a paso

### 1. Cuenta y proyecto

1. Entra a <https://console.cloud.google.com> y activa la prueba gratuita (pide tarjeta;
   da 300 USD de crédito por 90 días; mientras no "actualices" la cuenta, no te cobran).
2. Instala gcloud: <https://cloud.google.com/sdk/docs/install> (en Windows, el instalador `.exe`).
3. En una terminal nueva:

```bash
gcloud auth login
gcloud projects create aie-TU-NOMBRE-2026        # el ID debe ser único en todo GCP
gcloud config set project aie-TU-NOMBRE-2026
gcloud billing accounts list                       # copia el ACCOUNT_ID
gcloud billing projects link aie-TU-NOMBRE-2026 --billing-account=XXXXXX-XXXXXX-XXXXXX
```

### 2. Credenciales para tu código (ADC)

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project aie-TU-NOMBRE-2026
```

Esto guarda credenciales que el SDK encuentra solo. **No descargues llaves JSON de
cuentas de servicio**: son el secreto que más se filtra en repositorios. En Cloud Run y
Cloud Functions no hace falta nada: usan la cuenta de servicio que crea Terraform.

### 3. Crear la infraestructura con Terraform

Instala Terraform (<https://developer.hashicorp.com/terraform/install>) y sigue
[infra/README.md](../04-vertex-ai-projects/infra/README.md). En resumen:

```bash
cd 04-vertex-ai-projects/infra
cp terraform.tfvars.example terraform.tfvars      # pon tu proyecto
terraform init
terraform plan        # LEE qué va a crear antes de aplicar
terraform apply
```

### 4. Configurar y verificar

```bash
cd ../04-vertex-ai-projects
python -m venv .venv
source .venv/Scripts/activate          # Git Bash en Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt
cp .env.example .env                   # edita: MODO=real y GCP_PROJECT_ID
python 10_setup_gcp/verificar_entorno.py
```

Cuando el verificador salga limpio, corre los ejercicios en orden (ver
[testing-on-gcp.md](testing-on-gcp.md)).

### 5. Al terminar: apagar todo

```bash
cd 04-vertex-ai-projects/infra
terraform destroy
gcloud functions delete analizar-sas --gen2 --region=us-central1   # si la desplegaste
gcloud run services delete migrador-sas --region=us-central1       # si la desplegaste
```

(La Function y Cloud Run se crean con `gcloud`, no con Terraform, por eso se borran aparte.
Sin tráfico cuestan 0, pero es buena costumbre no dejar recursos huérfanos.)

## Si algo falla

Corre primero `python 10_setup_gcp/verificar_entorno.py`: detecta la mayoría de los
problemas y te dice el comando para arreglarlo. La tabla completa de errores está en
[10_setup_gcp/INSTRUCCIONES.md](../04-vertex-ai-projects/10_setup_gcp/INSTRUCCIONES.md#si-algo-falla).
