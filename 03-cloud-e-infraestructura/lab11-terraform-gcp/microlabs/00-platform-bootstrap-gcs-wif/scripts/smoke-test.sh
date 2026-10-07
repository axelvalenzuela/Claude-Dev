#!/usr/bin/env bash
# Verifica el bootstrap: bucket de estado, Workload Identity Federation y service accounts.
source "$(dirname "$0")/../../../scripts/lib.sh"
require gcloud jq

BUCKET=$(out tf_state_bucket)
PROVIDER=$(out wif_provider)
PLAN_SA=$(out plan_service_account)
APPLY_SA=$(out apply_service_account)

section "Bucket de estado gs://$BUCKET"
B=$(gcloud storage buckets describe "gs://$BUCKET" --format=json)
expect "Versionado" "$(echo "$B" | jq -r '.versioning_enabled')" "true"
expect "Uniform bucket-level access" "$(echo "$B" | jq -r '.uniform_bucket_level_access')" "true"
expect "Public access prevention" "$(echo "$B" | jq -r '.public_access_prevention')" "enforced"
expect "Acceso anónimo" "$(http_code "https://storage.googleapis.com/$BUCKET/")" "401"

section "Workload Identity Federation"
P=$(gcloud iam workload-identity-pools providers describe "$PROVIDER" --format=json)
expect "Estado del provider" "$(echo "$P" | jq -r .state)" "ACTIVE"
expect_match "Condición restringe al proyecto de GitLab" "$(echo "$P" | jq -r .attributeCondition)" "project_path"

section "Service accounts"
expect "Llaves JSON del SA apply (user-managed)" \
  "$(gcloud iam service-accounts keys list --iam-account "$APPLY_SA" --managed-by=user --format='value(name)' | wc -l | tr -d ' ')" "0"
expect_match "SA apply solo impersonable desde la rama main" \
  "$(gcloud iam service-accounts get-iam-policy "$APPLY_SA" --format=json | jq -r '.bindings[].members[]')" "deploy_ref/.*:branch:main"
expect_match "SA plan impersonable desde el proyecto" \
  "$(gcloud iam service-accounts get-iam-policy "$PLAN_SA" --format=json | jq -r '.bindings[].members[]')" "attribute.project_id"
expect_match "SA plan tiene roles/viewer" \
  "$(gcloud projects get-iam-policy "$PROJECT" --flatten=bindings --filter="bindings.members:$PLAN_SA" --format='value(bindings.role)')" "roles/viewer"

summary
