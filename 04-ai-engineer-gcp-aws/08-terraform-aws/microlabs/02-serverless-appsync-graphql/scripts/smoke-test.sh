#!/usr/bin/env bash
# Prueba GraphQL: mutación, consulta, aislamiento por usuario, profundidad y borrado.
source "$(dirname "$0")/../../../scripts/lib.sh"
require aws curl jq

URL=$(out graphql_url)
POOL=$(out user_pool_id)
CLIENT=$(out user_pool_client_id)

gql() { # gql <token> <query-json>
  curl -s "$URL" -H "Authorization: $1" -H 'Content-Type: application/json' -d "$2"
}

section "Usuarios de prueba (A y B) para validar aislamiento"
cognito_login "$POOL" "$CLIENT"; USER_A=$TEST_USER; TOKEN_A=$TOKEN
cognito_login "$POOL" "$CLIENT"; USER_B=$TEST_USER; TOKEN_B=$TOKEN
trap 'TEST_USER=$USER_A cognito_cleanup "$POOL"; TEST_USER=$USER_B cognito_cleanup "$POOL"' EXIT
ok "Usuarios $USER_A y $USER_B"

section "Mutaciones y consultas"
R=$(gql "$TOKEN_A" '{"query":"mutation { createNote(input:{title:\"smoke\", content:\"aie\"}) { id title createdAt } }"}')
ID=$(echo "$R" | jq -r '.data.createNote.id // empty')
[ -n "$ID" ] && ok "createNote ($ID)" || ko "createNote: $R"

R=$(gql "$TOKEN_A" '{"query":"{ listNotes(limit:10) { items { id title } } }"}')
expect "listNotes (usuario A) contiene la nota" "$(echo "$R" | jq --arg id "$ID" '[.data.listNotes.items[] | select(.id==$id)] | length')" "1"

R=$(gql "$TOKEN_B" '{"query":"{ listNotes(limit:10) { items { id } } }"}')
expect "listNotes (usuario B) NO ve notas de A" "$(echo "$R" | jq '.data.listNotes.items | length')" "0"

R=$(gql "$TOKEN_B" "{\"query\":\"{ getNote(id:\\\"$ID\\\") { id } }\"}")
expect "getNote de B sobre nota de A devuelve null" "$(echo "$R" | jq -r '.data.getNote')" "null"

section "Seguridad"
expect "Sin token" "$(http_code "$URL" -H 'Content-Type: application/json' -d '{"query":"{ listNotes { items { id } } }"}')" "401"
R=$(gql "$TOKEN_A" '{"query":"{ __schema { types { name fields { name type { name fields { name type { name fields { name } } } } } } } }"}')
expect_match "Query demasiado profunda rechazada (query_depth_limit)" "$R" "errors"

section "Limpieza"
R=$(gql "$TOKEN_A" "{\"query\":\"mutation { deleteNote(id:\\\"$ID\\\") { id } }\"}")
expect "deleteNote" "$(echo "$R" | jq -r '.data.deleteNote.id')" "$ID"

summary
