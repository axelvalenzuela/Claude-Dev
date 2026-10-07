#!/usr/bin/env bash
# Prueba de punta a punta: API key, cuota, backend privado, validación y CRUD sobre Firestore.
source "$(dirname "$0")/../../../scripts/lib.sh"
require gcloud curl jq

GW=$(out gateway_url)
KEY=$(out api_key)
FN=$(out function_uri)
H=(-H "x-api-key: $KEY" -H "Content-Type: application/json")

section "Gateway ($GW)"
check "Gateway listo (espera hasta 3 min tras el primer apply)" retry 18 10 bash -c "[ \"\$(curl -s -o /dev/null -w '%{http_code}' $GW/health)\" = 200 ]"
expect "GET /health sin API key" "$(http_code "$GW/health")" "200"
expect "GET /items sin API key" "$(http_code "$GW/items")" "401"
expect "GET /items con API key inválida" "$(http_code "$GW/items" -H 'x-api-key: invalida')" "400"

section "Backend privado"
expect "Función directa sin ID token" "$(http_code "$FN/items")" "403"

section "CRUD"
expect "POST cuerpo inválido (validación en código)" "$(http_code "$GW/items" -X POST "${H[@]}" -d '{"foo":1}')" "400"
R=$(curl -s -X POST "$GW/items" "${H[@]}" -d '{"name":"laptop","price":999.5,"description":"smoke"}')
ID=$(echo "$R" | jq -r '.id // empty')
[ -n "$ID" ] && ok "POST /items ($ID)" || ko "POST /items: $R"
expect "GET /items/{id}" "$(curl -s "$GW/items/$ID" "${H[@]}" | jq -r .name)" "laptop"
expect "GET /items incluye el item" "$(curl -s "$GW/items" "${H[@]}" | jq --arg id "$ID" '[.items[] | select(.id==$id)] | length')" "1"
expect "DELETE /items/{id}" "$(http_code "$GW/items/$ID" -X DELETE "${H[@]}")" "204"
expect "GET tras borrar" "$(http_code "$GW/items/$ID" "${H[@]}")" "404"

section "Cuota por API key (${QUOTA:-120}/min)"
CODES=$(for _ in $(seq 1 $(( ${QUOTA:-120} + 20 ))); do http_code "$GW/items" "${H[@]}"; echo; done | sort | uniq -c | tr '\n' ' ')
info "Códigos: $CODES"
expect_match "Aparece 429 al exceder la cuota" "$CODES" "429"

summary
