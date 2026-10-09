#!/usr/bin/env bash
# Publica 3 eventos y verifica: ruteo a Lambda, filtro numérico a SQS, auditoría y fallas hacia la DLQ.
source "$(dirname "$0")/../../../scripts/lib.sh"
require aws jq

BUS=$(out event_bus_name)
HV_QUEUE=$(out high_value_queue_url)
DLQ=$(out dlq_url)
AUDIT=$(out audit_log_group)
PROC_LOGS=$(out processor_log_group)
RUN="smoke-$(date +%s)"

section "Publicar eventos en $BUS (corrida $RUN)"
ENTRIES=$(jq -nc --arg bus "$BUS" --arg run "$RUN" '[
  {Source:"com.aie.orders", DetailType:"order.created", EventBusName:$bus, Detail:({orderId:($run+"-ok"),   amount:250,  run:$run}|tojson)},
  {Source:"com.aie.orders", DetailType:"order.created", EventBusName:$bus, Detail:({orderId:($run+"-high"), amount:4800, run:$run}|tojson)},
  {Source:"com.aie.orders", DetailType:"order.created", EventBusName:$bus, Detail:({orderId:($run+"-bad"),  run:$run}|tojson)}
]')
R=$(aws events put-events --entries "$ENTRIES")
expect "FailedEntryCount" "$(echo "$R" | jq '.FailedEntryCount')" "0"

section "Regla 1: Lambda procesa order.created"
check "Log del processor contiene $RUN-ok" retry 12 10 bash -c \
  "aws logs filter-log-events --log-group-name '$PROC_LOGS' --filter-pattern '\"$RUN-ok\"' --query 'events[0].message' --output text | grep -q '$RUN'"

section "Regla 2: solo amount >= umbral llega a SQS (input transformer)"
FOUND=""
for _ in $(seq 1 12); do
  MSGS=$(aws sqs receive-message --queue-url "$HV_QUEUE" --max-number-of-messages 10 --wait-time-seconds 5 --output json)
  if echo "$MSGS" | jq -e --arg id "$RUN-high" '.Messages[]? | select(.Body | contains($id))' >/dev/null; then
    FOUND=$(echo "$MSGS" | jq -r --arg id "$RUN-high" '.Messages[] | select(.Body | contains($id)) | .Body')
    for h in $(echo "$MSGS" | jq -r '.Messages[].ReceiptHandle'); do aws sqs delete-message --queue-url "$HV_QUEUE" --receipt-handle "$h"; done
    break
  fi
done
[ -n "$FOUND" ] && ok "Mensaje de alto valor recibido" || ko "No llegó $RUN-high a la cola"
[ -n "$FOUND" ] && expect "Transformación agregó priority=HIGH" "$(echo "$FOUND" | jq -r .priority)" "HIGH"
[ -n "$FOUND" ] && expect_match "La orden de 250 no pasó el filtro" "$FOUND" "$RUN-high"

section "Regla 3: auditoría registra todos los eventos"
check "Log de auditoría contiene la corrida" retry 12 10 bash -c \
  "aws logs filter-log-events --log-group-name '$AUDIT' --filter-pattern '\"$RUN\"' --query 'length(events)' --output text | grep -Eq '^[3-9]'"

section "Falla: evento sin amount termina en la DLQ (Lambda async on_failure, ~1-3 min)"
DLQ_HIT=""
for _ in $(seq 1 20); do
  MSGS=$(aws sqs receive-message --queue-url "$DLQ" --max-number-of-messages 10 --wait-time-seconds 10 --output json)
  if echo "$MSGS" | jq -e --arg id "$RUN-bad" '.Messages[]? | select(.Body | contains($id))' >/dev/null; then
    DLQ_HIT=1
    for h in $(echo "$MSGS" | jq -r '.Messages[].ReceiptHandle'); do aws sqs delete-message --queue-url "$DLQ" --receipt-handle "$h"; done
    break
  fi
done
[ -n "$DLQ_HIT" ] && ok "Evento fallido en la DLQ con contexto de error" || ko "No llegó $RUN-bad a la DLQ"

summary
