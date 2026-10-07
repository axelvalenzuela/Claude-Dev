#!/usr/bin/env bash
# Carga el grafo de muestra con el bulk loader y ejecuta consultas openCypher de negocio.
source "$(dirname "$0")/../../../scripts/lib.sh"
require aws jq

FN=$(out client_function)
ENDPOINT=$(out neptune_endpoint)
TMP=$(mktemp)

invoke() { # invoke <payload-json> -> imprime la respuesta
  aws lambda invoke --function-name "$FN" --cli-binary-format raw-in-base64-out \
    --payload "$1" "$TMP" >/dev/null && cat "$TMP"
}
cypher() { invoke "$(jq -nc --arg q "$1" '{action:"query", query:$q}')"; }

section "Conectividad (Lambda en VPC -> Neptune :8182 con SigV4)"
R=$(cypher "RETURN 1 AS ok")
expect "RETURN 1" "$(echo "$R" | jq -r '.results[0].ok')" "1"

section "Bulk load desde S3 (data/nodes.csv + data/edges.csv)"
COUNT=$(cypher "MATCH (n) RETURN count(n) AS c" | jq -r '.results[0].c')
if [ "$COUNT" -ge 8 ] 2>/dev/null; then
  info "El grafo ya tiene $COUNT nodos, se omite la carga"
else
  LOAD_ID=$(invoke '{"action":"load"}' | jq -r '.payload.loadId')
  info "loadId: $LOAD_ID"
  check "LOAD_COMPLETED" retry 30 10 bash -c \
    "aws lambda invoke --function-name $FN --cli-binary-format raw-in-base64-out --payload '{\"action\":\"load_status\",\"load_id\":\"$LOAD_ID\"}' $TMP >/dev/null && grep -q LOAD_COMPLETED $TMP"
fi
expect "Nodos" "$(cypher "MATCH (n) RETURN count(n) AS c" | jq -r '.results[0].c')" "8"
expect "Relaciones" "$(cypher "MATCH ()-[r]->() RETURN count(r) AS c" | jq -r '.results[0].c')" "9"

section "Consultas de negocio"
R=$(cypher "MATCH (a:Person {name:'Ana'})-[:FRIEND]->()-[:FRIEND]->(fof) RETURN DISTINCT fof.name AS name")
expect "Recomendación: amigos de amigos de Ana" "$(echo "$R" | jq -r '.results[].name' | tr '\n' ',')" "Carlos,"

R=$(cypher "MATCH (p:Person)-[:USES]->(d:Device)<-[:USES]-(r:Person) WHERE r.risk > 80 AND p <> r RETURN p.name AS sospechoso, d.name AS device")
expect "Fraude: comparte dispositivo con persona de alto riesgo" "$(echo "$R" | jq -r '.results[0].sospechoso')" "Ana"

R=$(cypher "MATCH (s:Account)-[t:TRANSFER]->(d:Account) WHERE t.amount > 9000 RETURN count(t) AS c")
expect "Transferencias cercanas al umbral de reporte" "$(echo "$R" | jq -r '.results[0].c')" "2"

section "Aislamiento"
check "Endpoint NO alcanzable desde Internet" bash -c "! timeout 5 bash -c '</dev/tcp/$ENDPOINT/8182' 2>/dev/null"
expect "IAM auth habilitada" "$(aws neptune describe-db-clusters --query "DBClusters[?Endpoint=='$ENDPOINT'].IAMDatabaseAuthenticationEnabled | [0]" --output text)" "True"

rm -f "$TMP"
summary
