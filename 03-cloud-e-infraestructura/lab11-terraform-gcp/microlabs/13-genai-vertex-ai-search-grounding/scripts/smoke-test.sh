#!/usr/bin/env bash
# Importa documentos y valida respuestas fundamentadas en ambos modos (Gemini grounding y Search API).
source "$(dirname "$0")/../../../scripts/lib.sh"
require gcloud curl jq

URL=$(out answer_url)
TOKEN=$(id_token)
ask() { curl -s -X POST "$URL" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "$(jq -nc --arg q "$1" --arg m "$2" '{question:$q, mode:$m}')"; }

section "Indexación"
bash "$LAB_DIR/scripts/import-docs.sh" --wait | tail -3
ok "Importación solicitada"

section "Modo gemini (Retrieval con Vertex AI Search)"
R=""
for _ in $(seq 1 10); do   # la indexación puede tardar unos minutos más en reflejarse
  R=$(ask "¿Cuánto cuesta el plan Pro y qué soporte incluye?" gemini)
  echo "$R" | jq -e '.sources | length > 0' >/dev/null 2>&1 && break
  sleep 30
done
expect_match "Precio correcto (25 dólares)" "$(echo "$R" | jq -r .answer)" "25"
expect_match "Fuente citada" "$(echo "$R" | jq -c .sources)" "planes-y-precios"
info "grounding_supports: $(echo "$R" | jq -r .grounding_supports) · tokens: $(echo "$R" | jq -c .usage)"

section "Modo search (resumen del motor con citas)"
R=$(ask "¿Qué crédito recibo si la disponibilidad baja de 99 por ciento?" search)
expect_match "Resumen correcto (25 por ciento)" "$(echo "$R" | jq -r .answer)" "25"
expect_match "Documento fuente" "$(echo "$R" | jq -c .sources)" "soporte-y-sla"

section "Fuera de dominio"
R=$(ask "¿Quién ganó el mundial de 1986?" gemini)
info "Respuesta: $(echo "$R" | jq -r .answer | head -c 160)"
expect "Sin fuentes recuperadas" "$(echo "$R" | jq '.sources | length')" "0"

summary
