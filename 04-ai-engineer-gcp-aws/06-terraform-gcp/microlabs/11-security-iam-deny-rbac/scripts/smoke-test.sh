#!/usr/bin/env bash
# Verifica auditoría, sinks, alertas y RBAC; prueba negativa de la deny policy (crear llave de SA debe fallar)
# y genera un evento auditado para comprobar que llega al log bucket.
source "$(dirname "$0")/../../../scripts/lib.sh"
require gcloud jq

PROBE=$(out probe_service_account)
ARCHIVE=$(out archive_bucket)
NAME_PREFIX="aie-${TF_ENV:-dev}-sec"

section "Auditoría"
AUDIT=$(gcloud projects get-iam-policy "$PROJECT" --format=json | jq -r '[.auditConfigs[]?.service] | join(",")')
expect_match "Data Access logs configurados" "$AUDIT" "storage.googleapis.com"
B=$(gcloud logging buckets describe "$NAME_PREFIX-audit" --location=global --format=json)
expect "Retención del log bucket (días)" "$(echo "$B" | jq -r .retentionDays)" "365"
expect "Log Analytics" "$(echo "$B" | jq -r .analyticsEnabled)" "true"
expect "Sinks de auditoría" "$(gcloud logging sinks list --format='value(name)' | grep -c "$NAME_PREFIX-audit")" "2"
expect_match "Archivo GCS cifrado con CMEK" "$(gcloud storage buckets describe "gs://$ARCHIVE" --format=json | jq -r .default_kms_key)" "cryptoKeys"

section "IAM Deny Policy (prueba negativa)"
if OUT=$(gcloud iam service-accounts keys create /tmp/probe-key.json --iam-account "$PROBE" 2>&1); then
  ko "Se creó una llave de SA (la deny policy no aplica a tu identidad o eres excepción)"
  gcloud iam service-accounts keys delete "$(jq -r .private_key_id /tmp/probe-key.json)" --iam-account "$PROBE" --quiet >/dev/null 2>&1
  rm -f /tmp/probe-key.json
else
  expect_match "Creación de llave denegada" "$OUT" "PERMISSION_DENIED|denied"
fi

section "Evento auditado llega al log bucket"
gcloud storage ls "gs://$ARCHIVE" >/dev/null 2>&1 || true   # genera un DATA_READ auditado
check "Audit logs recientes en el bucket (hasta 3 min)" retry 18 10 bash -c \
  "gcloud logging read 'logName:\"cloudaudit.googleapis.com\"' --bucket=$NAME_PREFIX-audit --location=global --view=_AllLogs --freshness=10m --limit=1 --format='value(timestamp)' | grep -q ."

section "Alertas de seguridad"
POL=$(gcloud alpha monitoring policies list --format='value(displayName)' 2>/dev/null | grep -c "$NAME_PREFIX" || true)
info "Políticas de alerta $NAME_PREFIX: $POL (esperadas 4)"
[ "${POL:-0}" -ge 4 ] && ok "Alertas basadas en logs" || ko "Faltan alertas (gcloud alpha requerido para listar)"

section "RBAC"
ROLE=$(out custom_role)
check "Rol custom $ROLE existe" gcloud iam roles describe "${ROLE##*/}" --project "$PROJECT"
expect "Rol custom NO incluye setIamPolicy" \
  "$(gcloud iam roles describe "${ROLE##*/}" --project "$PROJECT" --format=json | jq '.includedPermissions | any(test("setIamPolicy")) | not')" "true"
info "Bindings RBAC: $(out_json rbac_bindings | jq -r 'length') (equipo|rol|miembro)"

summary
