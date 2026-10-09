#!/usr/bin/env bash
# Despliega la API a Cloud Run. Requisitos: terraform apply de infra/ y gcloud con sesión.
#
#   export GCP_PROJECT_ID=tu-proyecto
#   bash 19_cloud_run_api/desplegar.sh
set -euo pipefail

: "${GCP_PROJECT_ID:?Define primero: export GCP_PROJECT_ID=tu-proyecto}"
REGION="${GCP_REGION:-us-central1}"
MODELO="${GEMINI_MODEL:-gemini-3.1-flash-lite}"
CUENTA="agente-migracion@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
AQUI="$(cd "$(dirname "$0")" && pwd)"

bash "$AQUI/preparar_build.sh"

# --source: Cloud Build construye la imagen con el Dockerfile y la guarda en Artifact Registry.
# --no-allow-unauthenticated: solo quien tenga rol run.invoker puede llamarla (nunca expongas
#   una API que gasta tokens sin autenticación).
# --min-instances=0: sin tráfico no pagas. --max-instances: techo de gasto si hay un pico.
gcloud run deploy migrador-sas \
  --project="$GCP_PROJECT_ID" \
  --region="$REGION" \
  --source="$AQUI/build" \
  --service-account="$CUENTA" \
  --no-allow-unauthenticated \
  --set-env-vars="MODO=real,GCP_PROJECT_ID=${GCP_PROJECT_ID},GEMINI_MODEL=${MODELO},LOG_NIVEL=INFO" \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --timeout=300

URL="$(gcloud run services describe migrador-sas --project="$GCP_PROJECT_ID" --region="$REGION" --format='value(status.url)')"
echo
echo "Desplegado en $URL . Pruébalo con:"
echo "  curl -H \"Authorization: Bearer \$(gcloud auth print-identity-token)\" $URL/salud"
