#!/usr/bin/env bash
# Configura AWS MGN con los recursos creados por Terraform.
# Requisitos: AWS CLI v2, jq, haber ejecutado `terraform apply` en este directorio.
set -euo pipefail
cd "$(dirname "$0")/.."

REGION="${AWS_REGION:-us-east-1}"
TEMPLATE=".build/replication-template.json"
OVERRIDES=".build/launch-template-overrides.json"

echo "==> 1. Inicializar MGN (crea roles vinculados y plantillas por defecto; idempotente)"
aws mgn initialize-service --region "$REGION" || true

echo "==> 2. Aplicar replication configuration template"
TEMPLATE_ID=$(aws mgn describe-replication-configuration-templates --region "$REGION" \
  --query 'items[0].replicationConfigurationTemplateID' --output text)

INPUT=$(jq -c --arg id "$TEMPLATE_ID" '. + {replicationConfigurationTemplateID: $id}' "$TEMPLATE")
aws mgn update-replication-configuration-template --region "$REGION" --cli-input-json "$INPUT" >/dev/null
echo "    Template $TEMPLATE_ID actualizado"

echo "==> 3. Ajustar launch templates de los source servers ya registrados"
for SERVER in $(aws mgn describe-source-servers --region "$REGION" --query 'items[].sourceServerID' --output text); do
  # Settings de MGN: right-sizing básico, copiar IP privada = no, licencias BYOL = no
  aws mgn update-launch-configuration --region "$REGION" --source-server-id "$SERVER" \
    --target-instance-type-right-sizing-method BASIC \
    --copy-private-ip false --copy-tags true \
    --launch-disposition STARTED >/dev/null

  LT_ID=$(aws mgn get-launch-configuration --region "$REGION" --source-server-id "$SERVER" \
    --query 'ec2LaunchTemplateID' --output text)
  LT_DATA=$(jq -c 'del(._comment, ._ebs_kms_key)' "$OVERRIDES")
  NEW_VERSION=$(aws ec2 create-launch-template-version --region "$REGION" --launch-template-id "$LT_ID" \
    --source-version '$Latest' --launch-template-data "$LT_DATA" \
    --query 'LaunchTemplateVersion.VersionNumber' --output text)
  aws ec2 modify-launch-template --region "$REGION" --launch-template-id "$LT_ID" --default-version "$NEW_VERSION" >/dev/null
  echo "    $SERVER -> launch template $LT_ID v$NEW_VERSION"
done

echo "Listo. Siguiente paso: instalar el agente en los servidores origen (ver README)."
