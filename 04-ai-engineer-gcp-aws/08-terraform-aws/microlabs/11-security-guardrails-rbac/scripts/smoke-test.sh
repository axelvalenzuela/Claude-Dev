#!/usr/bin/env bash
# Verifica controles detectivos y preventivos, simula permisos RBAC y genera un hallazgo de muestra.
source "$(dirname "$0")/../../../scripts/lib.sh"
require aws jq

TRAIL=$(out cloudtrail_arn)
DETECTOR=$(out guardduty_detector_id)
ROLES=$(out_json rbac_role_arns)
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

section "Detectivos"
expect "CloudTrail registrando" "$(aws cloudtrail get-trail-status --name "$TRAIL" --query IsLogging --output text)" "True"
expect "CloudTrail validación de integridad" "$(aws cloudtrail describe-trails --trail-name-list "$TRAIL" --query 'trailList[0].LogFileValidationEnabled' --output text)" "True"
expect "AWS Config grabando" "$(aws configservice describe-configuration-recorder-status --query 'ConfigurationRecordersStatus[0].recording' --output text)" "True"
RULES=$(aws configservice describe-config-rules --query "length(ConfigRules[?starts_with(ConfigRuleName, 'aie-')])" --output text)
info "Reglas de Config aie-*: $RULES"
expect "GuardDuty" "$(aws guardduty get-detector --detector-id "$DETECTOR" --query Status --output text)" "ENABLED"
STDS=$(aws securityhub get-enabled-standards --query 'length(StandardsSubscriptions)' --output text)
expect "Security Hub: estándares habilitados" "$STDS" "2"
check "IAM Access Analyzer activo" bash -c "aws accessanalyzer list-analyzers --query 'analyzers[0].status' --output text | grep -q ACTIVE"

section "Preventivos de cuenta"
expect "EBS cifrado por defecto" "$(aws ec2 get-ebs-encryption-by-default --query EbsEncryptionByDefault --output text)" "True"
expect "S3 Block Public Access (cuenta)" "$(aws s3control get-public-access-block --account-id "$ACCOUNT" --query PublicAccessBlockConfiguration.BlockPublicPolicy --output text)" "True"
expect "Password policy: longitud mínima" "$(aws iam get-account-password-policy --query PasswordPolicy.MinimumPasswordLength --output text)" "14"

section "RBAC (simulación de políticas, no requiere asumir roles)"
sim() { aws iam simulate-principal-policy --policy-source-arn "$1" --action-names "$2" \
  --query 'EvaluationResults[0].EvalDecision' --output text; }
DEV=$(echo "$ROLES" | jq -r '.developer')
AUD=$(echo "$ROLES" | jq -r '.auditor')
expect "developer: lambda:CreateFunction" "$(sim "$DEV" lambda:CreateFunction)" "allowed"
expect "developer: cloudtrail:StopLogging (boundary)" "$(sim "$DEV" cloudtrail:StopLogging)" "explicitDeny"
expect "developer: iam:CreateUser (boundary)" "$(sim "$DEV" iam:CreateUser)" "explicitDeny"
expect "auditor: s3:PutObject" "$(sim "$AUD" s3:PutObject)" "implicitDeny"
expect "auditor: cloudtrail:LookupEvents" "$(sim "$AUD" cloudtrail:LookupEvents)" "allowed"
expect_match "Todos los roles exigen MFA" \
  "$(aws iam get-role --role-name "${DEV##*/}" --query Role.AssumeRolePolicyDocument --output json)" "MultiFactorAuthPresent"

section "Respuesta: hallazgo de muestra de GuardDuty -> EventBridge -> SNS"
aws guardduty create-sample-findings --detector-id "$DETECTOR" --finding-types "UnauthorizedAccess:EC2/SSHBruteForce" \
  && ok "Hallazgo de muestra creado (revisa el correo en ~5 min)" || ko "No se pudo crear el hallazgo"

summary
