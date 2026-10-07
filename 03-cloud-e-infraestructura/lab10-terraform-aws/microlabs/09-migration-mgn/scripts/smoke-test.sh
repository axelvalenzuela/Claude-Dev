#!/usr/bin/env bash
# Verifica la landing zone de migración y, si MGN ya está configurado, el template de replicación
# y el estado de los source servers.
source "$(dirname "$0")/../../../scripts/lib.sh"
require aws jq

STAGING=$(out staging_subnet_id)
REPL_SG=$(out replication_security_group_id)
TARGET_SG=$(out target_security_group_id)
ROLE=$(out agent_installer_role_arn)
KMS=$(out ebs_kms_key_arn)

section "Red y seguridad"
check "Subnet de staging existe" aws ec2 describe-subnets --subnet-ids "$STAGING"
RULES=$(aws ec2 describe-security-group-rules --filters "Name=group-id,Values=$REPL_SG" --output json)
expect "SG replicación: puerto 1500 de entrada" \
  "$(echo "$RULES" | jq '[.SecurityGroupRules[] | select(.IsEgress==false and .FromPort==1500)] | length > 0')" "true"
expect "SG replicación: sin 0.0.0.0/0 de entrada" \
  "$(echo "$RULES" | jq '[.SecurityGroupRules[] | select(.IsEgress==false and .CidrIpv4=="0.0.0.0/0")] | length')" "0"
expect "SG target: sin SSH/RDP abiertos" \
  "$(aws ec2 describe-security-group-rules --filters "Name=group-id,Values=$TARGET_SG" --output json |
     jq '[.SecurityGroupRules[] | select(.IsEgress==false and (.FromPort==22 or .FromPort==3389))] | length')" "0"
expect "Rotación de la CMK" "$(aws kms get-key-rotation-status --key-id "$KMS" --query KeyRotationEnabled --output text)" "True"
expect_match "Rol instalador exige MFA" \
  "$(aws iam get-role --role-name "${ROLE##*/}" --query Role.AssumeRolePolicyDocument --output json)" "MultiFactorAuthPresent"

section "AWS MGN"
TPL=$(aws mgn describe-replication-configuration-templates --output json 2>/dev/null || echo '{}')
if [ "$(echo "$TPL" | jq '.items | length // 0')" -gt 0 ]; then
  expect "Template usa la subnet de staging" "$(echo "$TPL" | jq -r '.items[0].stagingAreaSubnetId')" "$STAGING"
  expect "Cifrado EBS CUSTOM" "$(echo "$TPL" | jq -r '.items[0].ebsEncryption')" "CUSTOM"
  SERVERS=$(aws mgn describe-source-servers --output json)
  N=$(echo "$SERVERS" | jq '.items | length')
  info "Source servers registrados: $N"
  echo "$SERVERS" | jq -r '.items[] | "  ..   \(.sourceProperties.identificationHints.hostname // .sourceServerID): \(.dataReplicationInfo.dataReplicationState // "N/A") · lag \(.dataReplicationInfo.lagDuration // "-") · ciclo \(.lifeCycle.state)"'
  ok "Consulta de MGN"
else
  info "MGN no está inicializado: ejecuta scripts/configure-mgn.sh"
  ok "Landing zone lista para inicializar MGN"
fi

summary
