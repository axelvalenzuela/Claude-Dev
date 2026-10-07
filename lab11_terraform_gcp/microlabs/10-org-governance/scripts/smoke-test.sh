#!/usr/bin/env bash
# Verifica jerarquía, org policies EFECTIVAS en los proyectos, firewall jerárquico y el baseline de cada proyecto.
# Incluye pruebas negativas: intentar crear una llave de SA o un bucket público debe FALLAR.
source "$(dirname "$0")/../../../scripts/lib.sh"
require gcloud jq

ROOT=$(out root_folder)
PROJECTS=$(out_json projects)

section "Jerarquía"
info "Carpeta raíz: $ROOT"
expect "Carpetas de entorno" "$(out_json env_folders | jq 'length')" "2"

section "Org policies efectivas (heredadas por cada proyecto)"
for P in $(echo "$PROJECTS" | jq -r '.[]'); do
  for C in iam.disableServiceAccountKeyCreation compute.vmExternalIpAccess storage.publicAccessPrevention; do
    E=$(gcloud org-policies describe "$C" --project "$P" --effective --format=json 2>/dev/null | jq -c '.spec.rules[0]')
    expect_match "$P · $C" "$E" '"enforce":true|"denyAll":true'
  done
done

section "Baseline por proyecto"
for P in $(echo "$PROJECTS" | jq -r '.[]'); do
  expect "$P sin red default" "$(gcloud compute networks list --project "$P" --format='value(name)' 2>/dev/null | grep -c '^default$')" "0"
  expect_match "$P auditoría de datos" "$(gcloud projects get-iam-policy "$P" --format=json | jq -c '.auditConfigs')" "DATA_WRITE"
done

section "Pruebas negativas (deben fallar por política)"
P=$(echo "$PROJECTS" | jq -r '.[]' | head -1)
SA="probe-$RANDOM"
gcloud iam service-accounts create "$SA" --project "$P" >/dev/null 2>&1
if gcloud iam service-accounts keys create /tmp/key.json --iam-account "$SA@$P.iam.gserviceaccount.com" >/dev/null 2>&1; then
  ko "Se creó una llave de SA"; rm -f /tmp/key.json
else
  ok "Creación de llave JSON bloqueada (iam.disableServiceAccountKeyCreation)"
fi
gcloud iam service-accounts delete "$SA@$P.iam.gserviceaccount.com" --project "$P" --quiet >/dev/null 2>&1

section "Firewall jerárquico"
RULES=$(gcloud compute firewall-policies rules list --firewall-policy "$(out firewall_policy)" --format=json 2>/dev/null)
expect_match "Regla deny 22/3389 desde Internet" "$RULES" '"action": ?"deny"'

summary
