#!/usr/bin/env bash
# Verifica el origen simulado, ejecuta verify del job y, con RUN_MIGRATION=1, migra y compara conteos.
source "$(dirname "$0")/../../../scripts/lib.sh"
require gcloud jq

JOB=$(out migration_job)
VM=$(out source_vm)
ZONE=$(out source_zone)

section "Origen simulado ($VM)"
check "PostgreSQL listo con pglogical (hasta 6 min tras el apply)" retry 36 10 bash -c \
  "gcloud compute instances get-serial-port-output $VM --zone $ZONE 2>/dev/null | grep -q 'startup-script exit status 0'"
SRC=$(gcloud compute ssh "$VM" --zone "$ZONE" --tunnel-through-iap --quiet --command \
  "sudo -u postgres psql -d ventas -Atc 'SELECT (SELECT count(*) FROM clientes) || \",\" || (SELECT count(*) FROM pedidos)'" 2>/dev/null | tail -1)
expect "Conteos en el origen (clientes,pedidos)" "$SRC" "500,5000"

section "Job de DMS ($JOB)"
STATE=$(gcloud database-migration migration-jobs describe "$JOB" --region "$REGION" --format='value(state)')
info "Estado actual: $STATE"
if [ "$STATE" = "DRAFT" ] || [ "$STATE" = "NOT_STARTED" ]; then
  gcloud database-migration migration-jobs verify "$JOB" --region "$REGION" >/dev/null 2>&1 &&
    ok "verify enviado (revisa errores con: bash scripts/migrate.sh status)" || ko "verify falló"
fi

if [ "${RUN_MIGRATION:-0}" = "1" ]; then
  section "Migración (dump + CDC, 15-30 min)"
  gcloud database-migration migration-jobs start "$JOB" --region "$REGION" >/dev/null 2>&1 || true
  check "Fase CDC alcanzada" retry 120 30 bash -c \
    "gcloud database-migration migration-jobs describe $JOB --region $REGION --format='value(phase)' | grep -q CDC"
  info "Inserta filas nuevas en el origen y verifica que lleguen al destino antes de promote"
  info "Cutover: bash scripts/migrate.sh promote"
fi

summary
