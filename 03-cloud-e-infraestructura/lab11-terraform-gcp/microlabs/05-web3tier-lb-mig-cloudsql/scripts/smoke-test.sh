#!/usr/bin/env bash
# Verifica las 3 capas en GCP: LB + backends sanos multi-zona, /db por IP privada con TLS, Cloud Armor y aislamiento.
# CHAOS=1 borra una VM del MIG y mide la autorecuperación (autohealing / tamaño objetivo).
source "$(dirname "$0")/../../../scripts/lib.sh"
require gcloud curl jq

URL=$(out app_url)
MIG=$(out mig_name)
BACKEND=$(out backend_service)
DB=$(out db_instance)

section "Capa web: Load Balancer ($URL)"
check "LB responde 200 en /health (el primer despliegue tarda 5-8 min)" \
  retry 60 10 bash -c "[ \"\$(curl -s -o /dev/null -w '%{http_code}' $URL/health)\" = 200 ]"
HEALTHY=$(gcloud compute backend-services get-health "$BACKEND" --global --format=json |
  jq '[.[].status.healthStatus[] | select(.healthState=="HEALTHY")] | length')
expect "Backends sanos" "$HEALTHY" "2"

section "Capa app: MIG regional"
ZONES=$(for _ in $(seq 1 12); do curl -s "$URL/db" | jq -r '.zone // empty'; done | sort -u | tr '\n' ' ')
expect_match "Respuestas desde 2 zonas ($ZONES)" "$(echo $ZONES | wc -w)" "^2$"
EXT=$(gcloud compute instances list --filter="name~^lab11-.*-3t-app" --format=json | jq '[.[].networkInterfaces[].accessConfigs // [] | length] | add')
expect "VMs con IP pública" "$EXT" "0"

section "Capa datos: Cloud SQL"
R=$(curl -s "$URL/db")
expect "Estado /db" "$(echo "$R" | jq -r .status)" "ok"
expect "Conexión TLS (ssl_mode ENCRYPTED_ONLY)" "$(echo "$R" | jq -r .ssl)" "true"
S=$(gcloud sql instances describe "$DB" --format=json)
expect "Alta disponibilidad" "$(echo "$S" | jq -r .settings.availabilityType)" "REGIONAL"
expect "Sin IP pública" "$(echo "$S" | jq -r .settings.ipConfiguration.ipv4Enabled)" "false"
expect "PITR habilitado" "$(echo "$S" | jq -r .settings.backupConfiguration.pointInTimeRecoveryEnabled)" "true"

section "Cloud Armor"
expect "SQL injection bloqueada" "$(http_code "$URL/?id=1%27%20OR%20%271%27=%271")" "403"
expect "XSS bloqueado" "$(http_code "$URL/?q=%3Cscript%3Ealert(1)%3C/script%3E")" "403"

if [ "${CHAOS:-0}" = "1" ]; then
  section "Chaos: borrar una VM del MIG"
  VICTIM=$(gcloud compute instance-groups managed list-instances "$MIG" --region "$REGION" --format='value(instance.basename())' | head -1)
  gcloud compute instance-groups managed delete-instances "$MIG" --region "$REGION" --instances "$VICTIM" >/dev/null
  ERR=0; for _ in $(seq 1 40); do [ "$(http_code "$URL/health")" = 200 ] || ERR=$((ERR + 1)); sleep 3; done
  info "Requests fallidos durante la recuperación: $ERR de 40"
  check "MIG estable con 2 instancias" retry 40 15 bash -c \
    "gcloud compute instance-groups managed describe $MIG --region $REGION --format='value(status.isStable)' | grep -q True"
fi

summary
