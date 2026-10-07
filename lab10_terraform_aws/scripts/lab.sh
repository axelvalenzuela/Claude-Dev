#!/usr/bin/env bash
# Operación local de un micro lab (funciona en Linux, macOS y Git Bash en Windows).
#
#   ./scripts/lab.sh <acción> <lab>
#
# Acciones: init | plan | apply | test | output | destroy | validate | validate-all | fmt
# Ejemplos:
#   export TF_STATE_BUCKET=lab10-dev-tfstate-123456789012
#   ./scripts/lab.sh init 01-serverless-api
#   ./scripts/lab.sh apply 01-serverless-api
#   ./scripts/lab.sh test 01-serverless-api
#   ./scripts/lab.sh destroy 01-serverless-api
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ACTION="${1:-}"
LAB="${2:-}"
ENVIRONMENT="${TF_ENV:-dev}"
REGION="${AWS_REGION:-us-east-1}"

usage() { sed -n '2,13p' "$0"; exit 1; }
[ -z "$ACTION" ] && usage

lab_dir() {
  [ -z "$LAB" ] && { echo "Falta el nombre del lab (p. ej. 01-serverless-api)"; exit 1; }
  local d="$ROOT/microlabs/$LAB"
  [ -d "$d" ] || { echo "No existe $d"; ls "$ROOT/microlabs"; exit 1; }
  echo "$d"
}

tfvars_args() {
  local d="$1"
  if [ -f "$d/terraform.tfvars" ]; then echo "-var-file=terraform.tfvars"; fi
}

case "$ACTION" in
  init)
    D=$(lab_dir)
    if [ "$LAB" = "00-bootstrap" ]; then
      terraform -chdir="$D" init
    else
      : "${TF_STATE_BUCKET:?Define TF_STATE_BUCKET (output del lab 00-bootstrap)}"
      terraform -chdir="$D" init -reconfigure \
        -backend-config="bucket=$TF_STATE_BUCKET" \
        -backend-config="key=lab10/$LAB/$ENVIRONMENT.tfstate" \
        -backend-config="region=$REGION" \
        -backend-config="use_lockfile=true" \
        -backend-config="encrypt=true"
    fi
    ;;
  plan)
    D=$(lab_dir)
    terraform -chdir="$D" plan $(tfvars_args "$D") -out=tfplan
    ;;
  apply)
    D=$(lab_dir)
    [ -f "$D/tfplan" ] || terraform -chdir="$D" plan $(tfvars_args "$D") -out=tfplan
    terraform -chdir="$D" apply tfplan
    rm -f "$D/tfplan"
    terraform -chdir="$D" output
    ;;
  test)
    D=$(lab_dir)
    bash "$D/scripts/smoke-test.sh"
    ;;
  output)
    D=$(lab_dir)
    terraform -chdir="$D" output
    ;;
  destroy)
    D=$(lab_dir)
    terraform -chdir="$D" destroy $(tfvars_args "$D")
    ;;
  validate)
    D=$(lab_dir)
    terraform -chdir="$D" init -backend=false -input=false >/dev/null
    terraform -chdir="$D" validate
    ;;
  validate-all)
    for d in "$ROOT"/microlabs/*/; do
      name=$(basename "$d")
      printf '%-32s ' "$name"
      terraform -chdir="$d" init -backend=false -input=false >/dev/null && terraform -chdir="$d" validate -no-color | tail -1
    done
    ;;
  fmt)
    terraform fmt -recursive "$ROOT"
    ;;
  *)
    usage
    ;;
esac
