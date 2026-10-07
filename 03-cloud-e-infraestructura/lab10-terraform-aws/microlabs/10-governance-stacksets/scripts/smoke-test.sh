#!/usr/bin/env bash
# Verifica el StackSet, sus instancias en las cuentas destino y el bus central.
#   SEND_TEST_EVENT=1 publica un evento de prueba en el bus central (debe llegar el correo).
source "$(dirname "$0")/../../../scripts/lib.sh"
require aws jq

SS=$(out stack_set_name)
BUS_ARN=$(out central_event_bus_arn)
CALL_AS="${CALL_AS:-SELF}"

section "StackSet $SS"
expect "Estado" "$(aws cloudformation describe-stack-set --stack-set-name "$SS" --call-as "$CALL_AS" --query StackSet.Status --output text)" "ACTIVE"
INST=$(aws cloudformation list-stack-instances --stack-set-name "$SS" --call-as "$CALL_AS" --output json)
TOTAL=$(echo "$INST" | jq '.Summaries | length')
CURRENT=$(echo "$INST" | jq '[.Summaries[] | select(.StackInstanceStatus.DetailedStatus=="SUCCEEDED")] | length')
info "Instancias: $TOTAL (cuentas x regiones)"
echo "$INST" | jq -r '.Summaries[] | "  ..   \(.Account) \(.Region): \(.StackInstanceStatus.DetailedStatus) \(.StatusReason // "")"'
[ "$TOTAL" -gt 0 ] && ok "Hay stack instances desplegadas" || ko "No hay instancias: revisa target_ou_ids y trusted access"
expect "Instancias en SUCCEEDED" "$CURRENT" "$TOTAL"

section "Drift"
OP=$(aws cloudformation detect-stack-set-drift --stack-set-name "$SS" --call-as "$CALL_AS" --query OperationId --output text 2>/dev/null || true)
if [ -n "$OP" ]; then
  check "Detección de drift terminó" retry 30 10 bash -c \
    "aws cloudformation describe-stack-set-operation --stack-set-name $SS --operation-id $OP --call-as $CALL_AS --query StackSetOperation.Status --output text | grep -q SUCCEEDED"
  DRIFT=$(aws cloudformation describe-stack-set --stack-set-name "$SS" --call-as "$CALL_AS" --query StackSet.StackSetDriftDetectionDetails.DriftStatus --output text)
  expect "Drift del baseline" "$DRIFT" "IN_SYNC"
fi

section "Bus central"
expect_match "Política restringe a la organización" \
  "$(aws events describe-event-bus --name "${BUS_ARN##*/}" --query Policy --output text)" "aws:PrincipalOrgID"
if [ "${SEND_TEST_EVENT:-0}" = "1" ]; then
  R=$(aws events put-events --entries "[{\"Source\":\"lab10.smoke\",\"DetailType\":\"Smoke test\",\"Detail\":\"{}\",\"EventBusName\":\"$BUS_ARN\"}]")
  expect "Evento de prueba publicado" "$(echo "$R" | jq .FailedEntryCount)" "0"
  info "Debe llegar un correo '[03-cloud-e-infraestructura/lab10-terraform-aws security] Smoke test ...'"
fi

summary
