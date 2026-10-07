#!/usr/bin/env bash
# Ingresa la base de conocimiento (si está vacía) y valida: recuperación, respuesta con citas y "no sé".
source "$(dirname "$0")/../../../scripts/lib.sh"
require gcloud bq curl jq python

URL=$(out ask_url)
TABLE=$(out chunks_table)
TOKEN=$(id_token)
ask() { curl -s -X POST "$URL" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "$(jq -nc --arg q "$1" '{question:$q}')"; }

section "Base de conocimiento"
N=$(bq query --use_legacy_sql=false --format=csv "SELECT COUNT(*) FROM \`$TABLE\`" | tail -1)
if [ "${N:-0}" -eq 0 ]; then
  info "Tabla vacía: ejecutando scripts/ingest.py"
  python "$LAB_DIR/scripts/ingest.py" || ko "ingest.py falló"
  N=$(bq query --use_legacy_sql=false --format=csv "SELECT COUNT(*) FROM \`$TABLE\`" | tail -1)
fi
[ "${N:-0}" -gt 0 ] && ok "Chunks con embedding: $N" || ko "Sin chunks"
DIM=$(bq query --use_legacy_sql=false --format=csv "SELECT ARRAY_LENGTH(embedding) FROM \`$TABLE\` LIMIT 1" | tail -1)
info "Dimensión del embedding: $DIM"

section "RAG"
expect "Sin ID token" "$(http_code "$URL" -X POST -d '{"question":"hola"}')" "403"
R=$(ask "¿Cuántos días de vacaciones tengo en mi primer año?")
expect_match "Respuesta correcta (12 días)" "$(echo "$R" | jq -r .answer)" "12"
expect_match "Cita la fuente" "$(echo "$R" | jq -r .answer)" "vacaciones\.md"
expect "Primera fuente recuperada" "$(echo "$R" | jq -r '.sources[0].source')" "vacaciones.md"

R=$(ask "¿Cuál es el tope diario para comida en un viaje?")
expect_match "Búsqueda semántica (comida ≈ alimentos)" "$(echo "$R" | jq -r .answer)" "60"

R=$(ask "¿Cuál es la capital de Australia?")
expect_match "Fuera de la base: no inventa" "$(echo "$R" | jq -r .answer)" "No tengo esa información"
info "Fuentes para la pregunta fuera de dominio: $(echo "$R" | jq -c '.sources')"

summary
