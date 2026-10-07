#!/usr/bin/env bash
# Importa (o re-importa) los documentos del bucket al data store de Vertex AI Search.
# La indexación tarda ~5-15 min la primera vez. Uso:  bash scripts/import-docs.sh [--wait]
set -euo pipefail
cd "$(dirname "$0")/.."

PROJECT="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
LOC=$(terraform output -raw search_location)
DS=$(terraform output -raw data_store_id)
BUCKET=$(terraform output -raw docs_bucket)
HOST=$([ "$LOC" = "global" ] && echo "discoveryengine.googleapis.com" || echo "$LOC-discoveryengine.googleapis.com")
BASE="https://$HOST/v1/projects/$PROJECT/locations/$LOC/collections/default_collection/dataStores/$DS"
AUTH=(-H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: $PROJECT")

# reconciliationMode INCREMENTAL: agrega/actualiza sin borrar lo existente (FULL reemplaza todo)
OP=$(curl -s -X POST "$BASE/branches/default_branch/documents:import" "${AUTH[@]}" -d @- <<JSON | jq -r .name
{"gcsSource": {"inputUris": ["gs://$BUCKET/docs/*"], "dataSchema": "content"}, "reconciliationMode": "INCREMENTAL"}
JSON
)
echo "Operación de importación: $OP"

if [ "${1:-}" = "--wait" ]; then
  for _ in $(seq 1 60); do
    DONE=$(curl -s "https://$HOST/v1/$OP" "${AUTH[@]}" | jq -r '.done // false')
    [ "$DONE" = "true" ] && { echo "Importación terminada"; curl -s "https://$HOST/v1/$OP" "${AUTH[@]}" | jq '.metadata'; exit 0; }
    sleep 20
  done
  echo "La importación sigue en curso; revisa la consola de AI Applications"
fi
