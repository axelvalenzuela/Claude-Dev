#!/usr/bin/env bash
# Sube un documento, espera la ejecución de Step Functions y valida entidades + resumen en DynamoDB.
# También sube un formato no soportado para comprobar la ruta de error (Catch -> SNS -> Fail).
source "$(dirname "$0")/../../../scripts/lib.sh"
require aws jq

BUCKET=$(out documents_bucket)
SM=$(out state_machine_arn)
TABLE=$(out results_table)
RUN="smoke-$(date +%s)"
GOOD_KEY="incoming/$RUN.txt"
BAD_KEY="incoming/$RUN.docx"

wait_execution() { # wait_execution <key> [intentos] -> imprime el status final
  local key="$1" tries="${2:-36}" arn="" status=""
  for _ in $(seq 1 "$tries"); do
    arn=$(aws stepfunctions list-executions --state-machine-arn "$SM" --max-results 20 --output json |
      jq -r '.executions[].executionArn' | while read -r a; do
        aws stepfunctions describe-execution --execution-arn "$a" --query input --output text | grep -q "$key" && echo "$a" && break
      done)
    if [ -n "$arn" ]; then
      status=$(aws stepfunctions describe-execution --execution-arn "$arn" --query status --output text)
      [ "$status" != "RUNNING" ] && { echo "$status"; return; }
    fi
    sleep 5
  done
  echo "${status:-NOT_STARTED}"
}

section "Documento válido ($GOOD_KEY)"
aws s3 cp "$LAB_DIR/samples/comunicado.txt" "s3://$BUCKET/$GOOD_KEY" --only-show-errors
expect "Ejecución" "$(wait_execution "$GOOD_KEY")" "SUCCEEDED"

ITEM=$(aws dynamodb get-item --table-name "$TABLE" --key "{\"document_id\":{\"S\":\"$GOOD_KEY\"}}" --output json)
SUMMARY=$(echo "$ITEM" | jq -r '.Item.summary.S // empty')
ENTITIES=$(echo "$ITEM" | jq -r '.Item.entities.S // "[]"')
[ -n "$SUMMARY" ] && ok "Resumen generado: ${SUMMARY:0:100}..." || ko "Sin resumen en DynamoDB"
expect_match "Comprehend detectó la organización UABC" "$ENTITIES" "UABC"
expect_match "Comprehend detectó una ubicación" "$ENTITIES" "LOCATION"
expect_match "Comprehend detectó una persona" "$ENTITIES" "PERSON"

section "Documento no soportado ($BAD_KEY) -> ruta de error"
echo "no soportado" | aws s3 cp - "s3://$BUCKET/$BAD_KEY" --only-show-errors
expect "Ejecución" "$(wait_execution "$BAD_KEY")" "FAILED"
info "Revisa tu correo: NotifyFailure publica el error en SNS"

section "Fuera del prefijo incoming/ no se dispara nada"
aws s3 cp "$LAB_DIR/samples/comunicado.txt" "s3://$BUCKET/otros/$RUN.txt" --only-show-errors
sleep 20
expect "Ejecuciones para otros/" "$(wait_execution "otros/$RUN.txt" 1)" "NOT_STARTED"

summary
