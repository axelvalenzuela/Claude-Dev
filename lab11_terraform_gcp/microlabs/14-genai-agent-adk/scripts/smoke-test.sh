#!/usr/bin/env bash
# Valida el comportamiento del agente: elige la herramienta correcta, usa memoria y no inventa datos.
source "$(dirname "$0")/../../../scripts/lib.sh"
require gcloud curl jq

URL=$(out agent_url)
TOKEN=$(id_token)
SESSION="smoke$RANDOM"
say() { curl -s -X POST "$URL" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "$(jq -nc --arg m "$1" --arg s "$SESSION" '{message:$m, session:$s}')"; }

section "Selección de herramientas"
R=$(say "Hola, ¿dónde está mi pedido PED-1003?")
expect_match "Llamó consultar_pedido" "$(echo "$R" | jq -c .tool_calls)" "consultar_pedido"
expect_match "Respuesta con el estado real (retrasado)" "$(echo "$R" | jq -r .answer)" "[Rr]etrasad"

R=$(say "¿Y si quiero devolverlo, qué política aplica?")
expect_match "Usó la memoria (categoría hogar) y llamó politica_devoluciones" "$(echo "$R" | jq -c .tool_calls)" "politica_devoluciones"
expect_match "Política de hogar (15 días)" "$(echo "$R" | jq -r .answer)" "15"

section "No inventa"
R=$(say "¿Cuál es el estado del pedido PED-9999?")
expect_match "Pedido inexistente" "$(echo "$R" | jq -r .answer)" "[Nn]o (existe|encontr)"

R=$(say "Quiero saber el estado de mi pedido")
expect "Pide el número de pedido sin llamar herramientas" "$(echo "$R" | jq '.tool_calls | length')" "0"

summary
