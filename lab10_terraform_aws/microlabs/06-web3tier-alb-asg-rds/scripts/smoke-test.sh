#!/usr/bin/env bash
# Verifica las 3 capas: ALB y targets sanos, balanceo entre AZ, conexión TLS a RDS y aislamiento de red.
# Opcional: CHAOS=1 termina una instancia y mide la autorecuperación del ASG.
source "$(dirname "$0")/../../../scripts/lib.sh"
require aws curl jq

URL=$(out app_url)
ASG=$(out asg_name)
DB=$(out db_endpoint)
TG=$(out target_group_arn)

section "Capa web: ALB ($URL)"
check "ALB responde 200 en /health (espera hasta 5 min a que el ASG esté sano)" \
  retry 30 10 bash -c "[ \"\$(curl -s -o /dev/null -w '%{http_code}' $URL/health)\" = 200 ]"
HEALTHY=$(aws elbv2 describe-target-health --target-group-arn "$TG" \
  --query "length(TargetHealthDescriptions[?TargetHealth.State=='healthy'])" --output text)
expect "Targets sanos" "$HEALTHY" "2"

section "Capa app: balanceo multi-AZ"
AZS=$(for _ in $(seq 1 12); do curl -s "$URL/db" | jq -r '.az // empty'; done | sort -u | tr '\n' ' ')
expect_match "Respuestas desde 2 AZ distintas ($AZS)" "$(echo $AZS | wc -w)" "^2$"

section "Capa datos: RDS PostgreSQL vía Secrets Manager"
R=$(curl -s "$URL/db")
expect "Estado /db" "$(echo "$R" | jq -r .status)" "ok"
expect "Conexión cifrada TLS (rds.force_ssl)" "$(echo "$R" | jq -r .ssl)" "true"
info "PostgreSQL $(echo "$R" | jq -r .postgres) · visitas registradas: $(echo "$R" | jq -r .visits)"

section "Aislamiento"
DB_PUBLIC=$(aws rds describe-db-instances --query "DBInstances[?Endpoint.Address=='$DB'].PubliclyAccessible" --output text)
expect "RDS publicly_accessible" "$DB_PUBLIC" "False"
MULTI_AZ=$(aws rds describe-db-instances --query "DBInstances[?Endpoint.Address=='$DB'].MultiAZ" --output text)
expect "RDS Multi-AZ" "$MULTI_AZ" "True"
check "Puerto 5432 NO alcanzable desde Internet" bash -c "! timeout 5 bash -c '</dev/tcp/$DB/5432' 2>/dev/null"
IMDS=$(aws ec2 describe-instances --filters "Name=tag:aws:autoscaling:groupName,Values=$ASG" "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].MetadataOptions.HttpTokens' --output text | tr '\t' '\n' | sort -u)
expect "IMDSv2 obligatorio" "$IMDS" "required"

section "WAF"
expect "Ataque SQLi bloqueado" "$(http_code "$URL/?id=1%27%20OR%20%271%27=%271")" "403"

if [ "${CHAOS:-0}" = "1" ]; then
  section "Chaos: terminar una instancia"
  VICTIM=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$ASG" \
    --query 'AutoScalingGroups[0].Instances[0].InstanceId' --output text)
  aws ec2 terminate-instances --instance-ids "$VICTIM" >/dev/null
  START=$(date +%s); ERRORS=0
  for _ in $(seq 1 60); do
    [ "$(http_code "$URL/health")" = "200" ] || ERRORS=$((ERRORS + 1))
    sleep 3
  done
  info "Requests fallidos durante la recuperación: $ERRORS de 60"
  check "ASG volvió a 2 instancias sanas" retry 40 15 bash -c \
    "[ \$(aws elbv2 describe-target-health --target-group-arn $TG --query \"length(TargetHealthDescriptions[?TargetHealth.State=='healthy'])\" --output text) -ge 2 ]"
  info "Tiempo total: $(( $(date +%s) - START )) s"
fi

summary
