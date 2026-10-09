#!/usr/bin/env bash
# Despliega la Cloud Function. Requisitos: terraform apply de infra/ (bucket,
# cuenta de servicio y permisos de Eventarc) y gcloud con sesión iniciada.
#
# Uso (Git Bash en Windows, o cualquier terminal bash):
#   export GCP_PROJECT_ID=tu-proyecto
#   bash 18_cloud_functions_storage/desplegar.sh
set -euo pipefail

: "${GCP_PROJECT_ID:?Define primero: export GCP_PROJECT_ID=tu-proyecto}"
REGION="${GCP_REGION:-us-central1}"
BUCKET="${GCS_BUCKET:-${GCP_PROJECT_ID}-migracion-sas}"
MODELO="${GEMINI_MODEL:-gemini-3.1-flash-lite}"
CUENTA="agente-migracion@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

AQUI="$(cd "$(dirname "$0")" && pwd)"
BUILD="$AQUI/build"

# 1. Armar la carpeta que se sube: main.py + requirements.txt + comun/
rm -rf "$BUILD" && mkdir -p "$BUILD"
cp "$AQUI/funcion/main.py" "$AQUI/funcion/requirements.txt" "$BUILD/"
cp -r "$AQUI/../comun" "$BUILD/comun"
rm -rf "$BUILD/comun/__pycache__"

# 2. Desplegar. --trigger-bucket crea el disparador de Eventarc por nosotros.
gcloud functions deploy analizar-sas \
  --gen2 \
  --project="$GCP_PROJECT_ID" \
  --region="$REGION" \
  --runtime=python312 \
  --source="$BUILD" \
  --entry-point=analizar_sas \
  --trigger-bucket="$BUCKET" \
  --service-account="$CUENTA" \
  --trigger-service-account="$CUENTA" \
  --set-env-vars="MODO=real,GCP_PROJECT_ID=${GCP_PROJECT_ID},GEMINI_MODEL=${MODELO},LOG_NIVEL=INFO" \
  --memory=512Mi \
  --timeout=300s \
  --max-instances=3

echo
echo "Listo. Pruébala con:"
echo "  gcloud storage cp comun/sas/ventas.sas gs://${BUCKET}/entrada/ventas.sas"
echo "  gcloud functions logs read analizar-sas --gen2 --region=${REGION} --limit=20"
echo "  gcloud storage cat gs://${BUCKET}/resultados/ventas.json"
