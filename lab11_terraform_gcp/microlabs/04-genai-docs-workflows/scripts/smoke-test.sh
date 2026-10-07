#!/usr/bin/env bash
# Sube documentos y verifica: ejecución del workflow, entidades + resumen en BigQuery, ruta de error y filtro de prefijo.
source "$(dirname "$0")/../../../scripts/lib.sh"
require gcloud bq jq

BUCKET=$(out documents_bucket)
WF=$(out workflow)
TABLE=$(out results_table)
RUN="smoke-$(date +%s)"

last_state() { # last_state <objeto> -> estado de la ejecución que procesó ese objeto
  local obj="$1"
  for _ in $(seq 1 "${2:-36}"); do
    for ex in $(gcloud workflows executions list "$WF" --location "$REGION" --limit 15 --format='value(name)'); do
      d=$(gcloud workflows executions describe "$ex" --format=json)
      if echo "$d" | jq -r .argument | grep -q "$obj"; then
        s=$(echo "$d" | jq -r .state)
        [ "$s" != "ACTIVE" ] && { echo "$s"; return; }
      fi
    done
    sleep 5
  done
  echo "NOT_FOUND"
}

section "Documento .txt"
gcloud storage cp "$LAB_DIR/samples/comunicado.txt" "gs://$BUCKET/incoming/$RUN.txt" --quiet >/dev/null
expect "Ejecución" "$(last_state "incoming/$RUN.txt")" "SUCCEEDED"
ROW=$(bq query --use_legacy_sql=false --format=json \
  "SELECT summary, TO_JSON_STRING(entities) AS entities FROM \`$TABLE\` WHERE document_id = 'incoming/$RUN.txt'")
SUMMARY=$(echo "$ROW" | jq -r '.[0].summary // empty')
[ -n "$SUMMARY" ] && ok "Resumen de Gemini: ${SUMMARY:0:90}..." || ko "Sin fila en $TABLE"
ENT=$(echo "$ROW" | jq -r '.[0].entities // ""')
expect_match "Entidad ORGANIZATION (UABC)" "$ENT" "UABC"
expect_match "Entidad LOCATION" "$ENT" "LOCATION"
expect_match "Entidad PERSON" "$ENT" "PERSON"

section "Formato no soportado -> FAILED"
echo "x" | gcloud storage cp - "gs://$BUCKET/incoming/$RUN.docx" --quiet >/dev/null
expect "Ejecución" "$(last_state "incoming/$RUN.docx")" "FAILED"

section "Fuera de incoming/ -> el workflow lo ignora"
gcloud storage cp "$LAB_DIR/samples/comunicado.txt" "gs://$BUCKET/otros/$RUN.txt" --quiet >/dev/null
expect "Ejecución" "$(last_state "otros/$RUN.txt")" "SUCCEEDED"
COUNT=$(bq query --use_legacy_sql=false --format=csv "SELECT COUNT(*) FROM \`$TABLE\` WHERE document_id = 'otros/$RUN.txt'" | tail -1)
expect "Sin fila en BigQuery para otros/" "$COUNT" "0"

summary
