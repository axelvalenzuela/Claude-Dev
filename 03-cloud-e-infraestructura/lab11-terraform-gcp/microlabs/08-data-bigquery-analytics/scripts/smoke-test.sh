#!/usr/bin/env bash
# Publica eventos, verifica la ingesta sin código, el control de costo (partition filter),
# ejecuta el scheduled query y valida la vista autorizada (sin PII).
source "$(dirname "$0")/../../../scripts/lib.sh"
require gcloud bq jq

TOPIC=$(out events_topic)
RAW=$(out raw_table)
KPI=$(out kpi_table)
VIEW=$(out shared_view)
TRANSFER=$(out transfer_config)
DLQ=$(out dlq_subscription)
RUN="smoke$(date +%s)"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

section "Publicar 30 eventos (corrida $RUN)"
TYPES=(page_view page_view add_to_cart purchase)
COUNTRIES=(MX US CA)
for i in $(seq 1 30); do
  T=${TYPES[$((i % 4))]}; C=${COUNTRIES[$((i % 3))]}
  AMOUNT=$([ "$T" = purchase ] && echo "\"$((i * 10)).50\"" || echo null)
  gcloud pubsub topics publish "$TOPIC" --message="{\"event_id\":\"$RUN-$i\",\"event_ts\":\"$NOW\",\"event_type\":\"$T\",\"user_id\":\"u$((i % 7))\",\"email\":\"u$((i % 7))@example.com\",\"country\":\"$C\",\"amount\":$AMOUNT}" >/dev/null
done
gcloud pubsub topics publish "$TOPIC" --message='{"no_cumple":"esquema"}' >/dev/null
ok "31 mensajes publicados (1 inválido)"

section "Ingesta streaming (Pub/Sub -> BigQuery)"
check "30 filas de la corrida en $RAW" retry 18 10 bash -c \
  "bq query --use_legacy_sql=false --format=csv \"SELECT COUNT(*) FROM \\\`$RAW\\\` WHERE DATE(event_ts) = CURRENT_DATE() AND event_id LIKE '$RUN-%'\" | tail -1 | grep -q '^30$'"

section "Control de costo"
if bq query --use_legacy_sql=false --format=csv "SELECT COUNT(*) FROM \`$RAW\`" >/dev/null 2>&1; then
  ko "Se permitió una consulta sin filtro de partición"
else
  ok "Consulta sin filtro de partición rechazada (require_partition_filter)"
fi
BYTES=$(bq query --use_legacy_sql=false --dry_run --format=json "SELECT event_type FROM \`$RAW\` WHERE DATE(event_ts) = CURRENT_DATE() AND country = 'MX'" 2>/dev/null | jq -r '.statistics.totalBytesProcessed // empty')
info "Dry run con partición + cluster: ${BYTES:-?} bytes estimados"

section "Mensaje inválido -> dead letter"
check "Mensaje fuera de esquema en la DLQ (hasta 3 min)" retry 18 10 bash -c \
  "gcloud pubsub subscriptions pull $DLQ --limit=10 --auto-ack --format=json | jq -e '.[] | select((.message.data | @base64d) | contains(\"no_cumple\"))' >/dev/null"

section "Scheduled query (MERGE de KPIs)"
gcloud alpha bq transfers runs start "$TRANSFER" >/dev/null 2>&1 || \
  bq mk --transfer_run --run_time="$NOW" "$TRANSFER" >/dev/null 2>&1 || true
check "KPIs del día en $KPI" retry 18 10 bash -c \
  "bq query --use_legacy_sql=false --format=csv \"SELECT COUNT(*) FROM \\\`$KPI\\\` WHERE day = CURRENT_DATE()\" | tail -1 | grep -Eq '^[1-9]'"

section "Vista autorizada (sin PII)"
COLS=$(bq show --format=json "${VIEW/./:}" | jq -r '[.schema.fields[].name] | join(",")')
expect "Columnas expuestas" "$COLS" "day,country,event_type,events,unique_users,revenue"
check "La vista devuelve datos" bash -c "bq query --use_legacy_sql=false --format=csv 'SELECT COUNT(*) FROM \`$VIEW\`' | tail -1 | grep -Eq '^[1-9]'"

summary
