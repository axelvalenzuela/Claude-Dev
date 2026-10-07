#!/usr/bin/env bash
# Verifica la observabilidad y genera errores controlados para ver el burn rate en acción.
#   GENERATE_ERRORS=1  -> envía tráfico con errores al API del lab 01 durante ~6 min
source "$(dirname "$0")/../../../scripts/lib.sh"
require aws curl jq

NAME_PREFIX="lab10-${TF_ENV:-dev}-sre"
TOPIC=$(out alerts_topic_arn)

section "Componentes"
check "Dashboard golden-signals" aws cloudwatch get-dashboard --dashboard-name "$NAME_PREFIX-golden-signals"
CANARY=$(aws synthetics describe-canaries --query "Canaries[?starts_with(Name, '${TF_ENV:-dev}-api')].Name | [0]" --output text)
expect "Estado del canary $CANARY" "$(aws synthetics get-canary --name "$CANARY" --query Canary.Status.State --output text)" "RUNNING"
COMPOSITES=$(aws cloudwatch describe-alarms --alarm-types CompositeAlarm --alarm-name-prefix "$NAME_PREFIX-slo-" --query 'length(CompositeAlarms)' --output text)
expect "Alarmas compuestas de burn rate (fast + slow)" "$COMPOSITES" "2"
SUBS=$(aws sns list-subscriptions-by-topic --topic-arn "$TOPIC" --query 'length(Subscriptions)' --output text)
info "Suscripciones al tópico de alertas: $SUBS (confirma los correos pendientes)"

section "Última corrida del canary"
LAST=$(aws synthetics get-canary-runs --name "$CANARY" --max-results 1 --query 'CanaryRuns[0].Status.State' --output text)
expect "Resultado" "$LAST" "PASSED"

section "Estado actual de las alarmas"
aws cloudwatch describe-alarms --alarm-name-prefix "$NAME_PREFIX" \
  --query 'concat(MetricAlarms[].[AlarmName,StateValue], CompositeAlarms[].[AlarmName,StateValue])' --output text |
  while read -r n s; do info "$(printf '%-55s %s' "$n" "$s")"; done
ok "Listado de alarmas"

if [ "${GENERATE_ERRORS:-0}" = "1" ]; then
  # Requiere el lab 01 aplicado con enable_fault_injection = true y su estado inicializado localmente.
  section "Inyección de errores 5XX en el API del lab 01 (6 min)"
  LAB01="$LAB_DIR/../01-serverless-api"
  API=$(terraform -chdir="$LAB01" output -raw api_url)
  POOL=$(terraform -chdir="$LAB01" output -raw user_pool_id)
  KEY=$(aws apigateway get-api-key --api-key "$(terraform -chdir="$LAB01" output -raw api_key_id)" --include-value --query value --output text)
  cognito_login "$POOL" "$(terraform -chdir="$LAB01" output -raw user_pool_client_id)"
  trap 'cognito_cleanup "$POOL"' EXIT
  END=$(( $(date +%s) + 360 )); N=0; E=0
  while [ "$(date +%s)" -lt "$END" ]; do
    # 1 de cada 10 requests sano y 9 con falla: tasa de error ~90 %, muy por encima de 14.4 x 0.1 %
    for i in $(seq 1 10); do
      if [ "$i" -eq 1 ]; then F=(); else F=(-H "x-fault-injection: 1"); fi
      c=$(http_code "$API/items" -H "Authorization: $TOKEN" -H "x-api-key: $KEY" "${F[@]}")
      N=$((N + 1)); [ "$c" -ge 500 ] && E=$((E + 1))
    done
    sleep 1
  done
  info "Requests: $N · 5XX: $E"
  [ "$E" -gt 0 ] && ok "Se generaron errores 5XX (¿enable_fault_injection = true en el lab 01?)" || ko "No hubo 5XX: habilita enable_fault_injection en el lab 01"
  check "Alarma compuesta fast burn en ALARM (espera hasta 10 min)" retry 20 30 bash -c \
    "aws cloudwatch describe-alarms --alarm-types CompositeAlarm --alarm-name-prefix '$NAME_PREFIX-slo-fast' --query 'CompositeAlarms[0].StateValue' --output text | grep -q ALARM"
fi

summary
