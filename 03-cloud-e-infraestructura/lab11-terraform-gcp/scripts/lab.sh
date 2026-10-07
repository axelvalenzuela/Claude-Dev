#!/usr/bin/env bash
# Operación local de un micro lab de GCP (Linux, macOS y Git Bash en Windows).
#
#   ./scripts/lab.sh <acción> <lab>
#
# Acciones: init | plan | apply | test | output | destroy | validate | validate-all | fmt
# Ejemplo:
#   gcloud auth application-default login && gcloud config set project <id>
#   export TF_STATE_BUCKET=<id>-lab11-tfstate
#   ./scripts/lab.sh init 01-serverless-apigw-functions-firestore && ./scripts/lab.sh apply 01-serverless-apigw-functions-firestore
#   ./scripts/lab.sh test 01-serverless-apigw-functions-firestore
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ACTION="${1:-}"
LAB="${2:-}"
ENVIRONMENT="${TF_ENV:-dev}"

usage() { sed -n '2,12p' "$0"; exit 1; }
[ -z "$ACTION" ] && usage

lab_dir() {
  [ -z "$LAB" ] && { echo "Falta el nombre del lab"; exit 1; }
  local d="$ROOT/microlabs/$LAB"
  [ -d "$d" ] || { echo "No existe $d"; ls "$ROOT/microlabs"; exit 1; }
  echo "$d"
}

tfvars_args() {
  [ -f "$1/terraform.tfvars" ] && echo "-var-file=terraform.tfvars" || true
}

case "$ACTION" in
  init)
    D=$(lab_dir)
    if [ "$LAB" = "00-platform-bootstrap-gcs-wif" ]; then
      terraform -chdir="$D" init
    else
      : "${TF_STATE_BUCKET:?Define TF_STATE_BUCKET (output del lab 00-platform-bootstrap-gcs-wif)}"
      terraform -chdir="$D" init -reconfigure \
        -backend-config="bucket=$TF_STATE_BUCKET" \
        -backend-config="prefix=03-cloud-e-infraestructura/lab11-terraform-gcp/$LAB/$ENVIRONMENT"
    fi
    ;;
  plan)
    D=$(lab_dir); terraform -chdir="$D" plan $(tfvars_args "$D") -out=tfplan ;;
  apply)
    D=$(lab_dir)
    [ -f "$D/tfplan" ] || terraform -chdir="$D" plan $(tfvars_args "$D") -out=tfplan
    terraform -chdir="$D" apply tfplan
    rm -f "$D/tfplan"
    terraform -chdir="$D" output
    ;;
  test)
    D=$(lab_dir); bash "$D/scripts/smoke-test.sh" ;;
  output)
    D=$(lab_dir); terraform -chdir="$D" output ;;
  destroy)
    D=$(lab_dir); terraform -chdir="$D" destroy $(tfvars_args "$D") ;;
  validate)
    D=$(lab_dir)
    terraform -chdir="$D" init -backend=false -input=false >/dev/null
    terraform -chdir="$D" validate
    ;;
  validate-all)
    for d in "$ROOT"/microlabs/*/; do
      printf '%-34s ' "$(basename "$d")"
      terraform -chdir="$d" init -backend=false -input=false >/dev/null && terraform -chdir="$d" validate -no-color | tail -1
    done
    ;;
  fmt)
    terraform fmt -recursive "$ROOT" ;;
  *)
    usage ;;
esac
