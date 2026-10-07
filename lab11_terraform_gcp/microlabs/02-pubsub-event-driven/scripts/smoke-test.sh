#!/usr/bin/env bash
# Publica órdenes y verifica: schema, push a la función, filtro por atributos, DLQ, auditoría en BigQuery y Scheduler.
source "$(dirname "$0")/../../../scripts/lib.sh"
require gcloud bq jq

TOPIC=$(out topic)
HV=$(out high_value_subscription)
DLQ=$(out dead_letter_subscription)
TABLE=$(out audit_table)
FN=$(out processor_function)
JOB=$(out scheduler_job)
RUN="smoke$(date +%s)"

# AVRO en JSON: las uniones van como {"double": 250}
publish() { gcloud pubsub topics publish "$TOPIC" --message="$1" ${2:+--attribute="$2"} --format='value(messageIds)'; }

section "Schema AVRO (validación al publicar)"
if gcloud pubsub topics publish "$TOPIC" --message='{"customer":"sin-orderId"}' >/dev/null 2>&1; then
  ko "Mensaje sin orderId fue aceptado"
else
  ok "Mensaje sin orderId rechazado por el schema"
fi

section "Publicar 3 órdenes (corrida $RUN)"
publish "{\"orderId\":\"$RUN-ok\",\"customer\":\"c1\",\"amount\":{\"double\":250},\"run\":{\"string\":\"$RUN\"}}" "tier=standard" >/dev/null && ok "orden normal"
publish "{\"orderId\":\"$RUN-high\",\"customer\":\"c2\",\"amount\":{\"double\":4800},\"run\":{\"string\":\"$RUN\"}}" "tier=high" >/dev/null && ok "orden de alto valor (tier=high)"
publish "{\"orderId\":\"$RUN-bad\",\"customer\":\"c3\",\"amount\":null,\"run\":{\"string\":\"$RUN\"}}" "tier=standard" >/dev/null && ok "orden sin amount (fallará)"

section "Push autenticado -> función"
check "Logs de la función contienen $RUN-ok" retry 18 10 bash -c \
  "gcloud logging read 'resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$FN\" AND jsonPayload.order_id=\"$RUN-ok\"' --freshness=15m --limit=1 --format='value(jsonPayload.order_id)' | grep -q $RUN"

section "Filtro por atributos"
MSGS=$(gcloud pubsub subscriptions pull "$HV" --limit=20 --auto-ack --format=json)
expect "Suscripción high-value recibió solo la orden tier=high" \
  "$(echo "$MSGS" | jq -r --arg r "$RUN" '[.[] | .message.data | @base64d | fromjson | select(.run.string==$r) | .orderId] | join(",")')" "$RUN-high"

section "Dead letter (5 intentos con backoff, ~2-4 min)"
FOUND=""
for _ in $(seq 1 24); do
  M=$(gcloud pubsub subscriptions pull "$DLQ" --limit=20 --auto-ack --format=json)
  if echo "$M" | jq -e --arg id "$RUN-bad" '.[] | select((.message.data | @base64d) | contains($id))' >/dev/null; then
    FOUND=$(echo "$M" | jq -r --arg id "$RUN-bad" '.[] | select((.message.data | @base64d) | contains($id)) | .message.attributes.CloudPubSubDeadLetterSourceDeliveryCount')
    break
  fi
  sleep 10
done
[ -n "$FOUND" ] && ok "Orden fallida en la DLQ tras $FOUND intentos" || ko "No llegó $RUN-bad a la DLQ"

section "Auditoría en BigQuery (suscripción directa, sin código)"
check "3 eventos de la corrida en $TABLE" retry 12 10 bash -c \
  "bq query --use_legacy_sql=false --format=csv \"SELECT COUNT(*) FROM \\\`$TABLE\\\` WHERE data LIKE '%$RUN%'\" | tail -1 | grep -q '^3$'"

section "Cloud Scheduler"
gcloud scheduler jobs run "$JOB" --location "$REGION" >/dev/null && ok "Ejecución manual del job"
check "El job terminó con código 200" retry 12 5 bash -c \
  "gcloud scheduler jobs describe $JOB --location $REGION --format='value(status.code)' | grep -Eq '^(0|)$'"

summary
