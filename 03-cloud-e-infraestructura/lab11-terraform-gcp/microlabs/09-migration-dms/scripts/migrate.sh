#!/usr/bin/env bash
# Opera el job de DMS:  bash scripts/migrate.sh <verify|start|status|promote|delete>
#   verify  -> valida conectividad y requisitos del origen (sin migrar)
#   start   -> dump completo + CDC continuo
#   status  -> fase, estado y errores
#   promote -> CUTOVER: detiene la replicación y convierte el destino en instancia primaria independiente
set -euo pipefail
cd "$(dirname "$0")/.."
JOB=$(terraform output -raw migration_job)
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"

case "${1:-status}" in
  verify)  gcloud database-migration migration-jobs verify "$JOB" --region "$REGION" ;;
  start)   gcloud database-migration migration-jobs start "$JOB" --region "$REGION" ;;
  status)  gcloud database-migration migration-jobs describe "$JOB" --region "$REGION" \
             --format='table(state, phase, error.message, duration)' ;;
  promote) read -r -p "¿Confirmas el CUTOVER (detener escrituras en el origen primero)? [s/N] " a
           [ "$a" = "s" ] && gcloud database-migration migration-jobs promote "$JOB" --region "$REGION" ;;
  delete)  gcloud database-migration migration-jobs delete "$JOB" --region "$REGION" ;;
  *)       sed -n '2,7p' "$0" ;;
esac
