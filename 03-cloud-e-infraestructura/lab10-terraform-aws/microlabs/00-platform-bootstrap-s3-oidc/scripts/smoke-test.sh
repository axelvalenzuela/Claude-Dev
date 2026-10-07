#!/usr/bin/env bash
# Verifica el bootstrap: bucket de estado seguro, roles OIDC y presupuesto.
source "$(dirname "$0")/../../../scripts/lib.sh"
require aws terraform

BUCKET=$(out tf_state_bucket)
PLAN_ROLE=$(out aws_plan_role_arn)
APPLY_ROLE=$(out aws_apply_role_arn)

section "Bucket de estado: $BUCKET"
expect "Versionado" "$(aws s3api get-bucket-versioning --bucket "$BUCKET" --query Status --output text)" "Enabled"
expect "Cifrado" "$(aws s3api get-bucket-encryption --bucket "$BUCKET" \
  --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm' --output text)" "aws:kms"
expect "Block Public Access" "$(aws s3api get-public-access-block --bucket "$BUCKET" \
  --query 'PublicAccessBlockConfiguration.RestrictPublicBuckets' --output text)" "True"
expect_match "Política exige TLS" "$(aws s3api get-bucket-policy --bucket "$BUCKET" --query Policy --output text)" "aws:SecureTransport"
code=$(curl -s -o /dev/null -w '%{http_code}' "http://$BUCKET.s3.amazonaws.com/")
expect_match "Acceso anónimo denegado (HTTP $code)" "$code" "^(301|307|403)$"

section "Roles de CI (OIDC)"
check "Proveedor OIDC registrado" bash -c "aws iam list-open-id-connect-providers --output text | grep -q gitlab"
PLAN_TRUST=$(aws iam get-role --role-name "${PLAN_ROLE##*/}" --query Role.AssumeRolePolicyDocument --output json)
APPLY_TRUST=$(aws iam get-role --role-name "${APPLY_ROLE##*/}" --query Role.AssumeRolePolicyDocument --output json)
expect_match "Rol plan acepta cualquier rama" "$PLAN_TRUST" 'ref:\*'
expect_match "Rol apply solo acepta main" "$APPLY_TRUST" 'ref:main'
expect_match "Rol apply tiene permissions boundary" \
  "$(aws iam get-role --role-name "${APPLY_ROLE##*/}" --query Role.PermissionsBoundary.PermissionsBoundaryArn --output text)" "ci-boundary"

section "Simulación del boundary (el rol apply NO puede crear usuarios IAM)"
decision=$(aws iam simulate-principal-policy --policy-source-arn "$APPLY_ROLE" --action-names iam:CreateUser \
  --query 'EvaluationResults[0].EvalDecision' --output text)
expect "iam:CreateUser" "$decision" "explicitDeny"

section "Presupuesto"
check "Budget lab10-*-monthly existe" bash -c \
  "aws budgets describe-budgets --account-id $(aws sts get-caller-identity --query Account --output text) --query 'Budgets[].BudgetName' --output text | grep -q monthly"

summary
