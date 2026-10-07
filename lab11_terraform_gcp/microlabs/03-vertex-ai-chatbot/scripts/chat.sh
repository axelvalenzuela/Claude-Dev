#!/usr/bin/env bash
# Chat interactivo en la terminal contra el chatbot privado (usa tu identidad de gcloud).
#   bash scripts/chat.sh            -> escribe preguntas; "salir" para terminar
set -euo pipefail
cd "$(dirname "$0")/.."
URL=$(terraform output -raw chat_url)
TOKEN=$(gcloud auth print-identity-token)
SESSION="cli-$RANDOM"
echo "Chatbot lab11 (sesión $SESSION). Escribe 'salir' para terminar."
while read -r -p "> " MSG; do
  [ "$MSG" = "salir" ] && break
  curl -s -X POST "$URL" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
    -d "$(jq -nc --arg m "$MSG" --arg s "$SESSION" '{message:$m, session:$s}')" |
    jq -r '"\(.answer)\n   [\(.finish_reason // "-") · tokens in \(.usage.input_tokens // "-") / out \(.usage.output_tokens // "-")\(if .blocked then " · BLOQUEADO" else "" end)]"'
done
