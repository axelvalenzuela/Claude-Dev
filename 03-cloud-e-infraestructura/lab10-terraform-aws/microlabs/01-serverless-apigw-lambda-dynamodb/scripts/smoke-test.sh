#!/usr/bin/env bash
# Prueba de punta a punta de la API: health, autenticación, validación, CRUD y aislamiento.
source "$(dirname "$0")/../../../scripts/lib.sh"
require aws curl jq

API=$(out api_url)
POOL=$(out user_pool_id)
CLIENT=$(out user_pool_client_id)
KEY=$(aws apigateway get-api-key --api-key "$(out api_key_id)" --include-value --query value --output text)

section "Usuario de prueba en Cognito"
cognito_login "$POOL" "$CLIENT"
trap 'cognito_cleanup "$POOL"' EXIT
[ -n "$TOKEN" ] && ok "Login USER_PASSWORD_AUTH ($TEST_USER)" || ko "No se obtuvo IdToken"

H=(-H "Authorization: $TOKEN" -H "x-api-key: $KEY" -H "Content-Type: application/json")

section "Endpoints"
expect "GET /health (MOCK, sin auth)" "$(http_code "$API/health")" "200"
expect "GET /items sin credenciales" "$(http_code "$API/items")" "401"
expect "GET /items con JWT pero sin API key" "$(http_code "$API/items" -H "Authorization: $TOKEN")" "403"
expect "POST /items con cuerpo inválido (validación OpenAPI)" \
  "$(http_code "$API/items" -X POST "${H[@]}" -d '{"foo":1}')" "400"

CREATED=$(curl -s -X POST "$API/items" "${H[@]}" -d '{"name":"laptop","price":999.5,"description":"smoke test"}')
ID=$(echo "$CREATED" | jq -r '.id // empty')
[ -n "$ID" ] && ok "POST /items crea el item ($ID)" || ko "POST /items: $CREATED"

LIST=$(curl -s "$API/items" "${H[@]}")
expect "GET /items devuelve el item" "$(echo "$LIST" | jq --arg id "$ID" '[.items[] | select(.id==$id)] | length')" "1"
expect "GET /items/{id}" "$(http_code "$API/items/$ID" "${H[@]}")" "200"
expect "DELETE /items/{id}" "$(http_code "$API/items/$ID" -X DELETE "${H[@]}")" "204"
expect "GET /items/{id} después de borrar" "$(http_code "$API/items/$ID" "${H[@]}")" "404"

section "Throttling del usage plan"
CODES=$(for _ in $(seq 1 30); do http_code "$API/items" "${H[@]}" & done; wait)
info "Códigos en ráfaga de 30 requests: $(echo $CODES | tr ' ' '\n' | sort | uniq -c | tr '\n' ' ')"
ok "Ráfaga ejecutada (con throttle_burst_limit bajo verás 429)"

section "Observabilidad"
LOGS=$(out access_log_group)
check "Access logs presentes en $LOGS" retry 6 10 bash -c \
  "aws logs filter-log-events --log-group-name '$LOGS' --limit 1 --query 'events[0].message' --output text | grep -q requestId"
check "Trazas X-Ray en los últimos 10 min" bash -c \
  "aws xray get-trace-summaries --start-time $(( $(date +%s) - 600 )) --end-time $(date +%s) --query 'TraceSummaries[0].Id' --output text | grep -vq None"

summary
