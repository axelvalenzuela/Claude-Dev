#!/usr/bin/env bash
# Verifica SLOs, alertas, uptime check y dashboard. GENERATE_ERRORS=1 inyecta 5XX en el lab 01
# (requiere enable_fault_injection = true allí) y espera a que la alerta fast burn se abra.
source "$(dirname "$0")/../../../scripts/lib.sh"
require gcloud curl jq

SERVICE=$(out service_id)
SLO=$(out availability_slo)
TOKEN=$(access_token)
API="https://monitoring.googleapis.com/v3/projects/$PROJECT"

section "Servicio y SLOs"
SLOS=$(curl -s -H "Authorization: Bearer $TOKEN" "$API/services/$SERVICE/serviceLevelObjectives" | jq -r '.serviceLevelObjectives[].displayName')
echo "$SLOS" | while read -r s; do info "$s"; done
expect "SLOs definidos" "$(echo "$SLOS" | grep -c .)" "2"

section "Alertas"
POL=$(gcloud alpha monitoring policies list --format=json 2>/dev/null || curl -s -H "Authorization: Bearer $TOKEN" "$API/alertPolicies" | jq '.alertPolicies')
expect "Políticas de burn rate (fast + slow)" "$(echo "$POL" | jq '[.[] | select(.displayName | test("SLO burn"))] | length')" "2"
expect "Política de uptime" "$(echo "$POL" | jq '[.[] | select(.displayName | test("uptime"))] | length')" "1"

section "Uptime check"
UP=$(curl -s -H "Authorization: Bearer $TOKEN" "$API/uptimeCheckConfigs" | jq -r '.uptimeCheckConfigs[] | select(.displayName | test("lab11")) | .monitoredResource.labels.host')
[ -n "$UP" ] && ok "Uptime check sobre $UP" || ko "Sin uptime check"
expect "Host responde /health" "$(http_code "https://$UP/health")" "200"

if [ "${GENERATE_ERRORS:-0}" = "1" ]; then
  section "Inyección de errores (6 min) en el lab 01"
  LAB01="$LAB_DIR/../01-api-gateway-functions"
  GW=$(terraform -chdir="$LAB01" output -raw gateway_url)
  KEY=$(terraform -chdir="$LAB01" output -raw api_key)
  END=$(( $(date +%s) + 360 )); N=0; E=0
  while [ "$(date +%s)" -lt "$END" ]; do
    for i in $(seq 1 10); do
      if [ "$i" -eq 1 ]; then F=(); else F=(-H "x-fault-injection: 1"); fi
      c=$(http_code "$GW/items" -H "x-api-key: $KEY" "${F[@]}"); N=$((N + 1)); [ "$c" -ge 500 ] && E=$((E + 1))
    done
    sleep 2
  done
  info "Requests: $N · 5XX: $E"
  [ "$E" -gt 0 ] && ok "Errores 5XX generados" || ko "Sin 5XX: activa enable_fault_injection en el lab 01"
  # Burn rate de la ventana corta (5 min) leído de la API de series de tiempo del SLO
  burn_5m() {
    curl -s -G -H "Authorization: Bearer $(access_token)" "$API/timeSeries" \
      --data-urlencode "filter=select_slo_burn_rate(\"$SLO\", \"300s\")" \
      --data-urlencode "interval.startTime=$(date -u -d '-10 min' +%Y-%m-%dT%H:%M:%SZ)" \
      --data-urlencode "interval.endTime=$(date -u +%Y-%m-%dT%H:%M:%SZ)" |
      jq '[.timeSeries[]?.points[]?.value.doubleValue // 0] | max // 0'
  }
  for _ in $(seq 1 20); do B=$(burn_5m); awk "BEGIN{exit !($B > 14.4)}" && break; sleep 30; done
  awk "BEGIN{exit !($B > 14.4)}" && ok "Burn rate 5 min = $B (> 14.4: la alerta fast burn se abre)" || ko "Burn rate 5 min = $B"
  info "Revisa Monitoring > Alerting > Incidents y el dashboard"
fi

summary
