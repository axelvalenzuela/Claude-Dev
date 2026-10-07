#!/usr/bin/env bash
# Utilidades compartidas por los smoke tests de los micro labs.
# Uso dentro de microlabs/<lab>/scripts/smoke-test.sh:
#   source "$(dirname "$0")/../../../scripts/lib.sh"
#
# Lee outputs de Terraform de dos formas:
#   - Local:  terraform output (requiere `terraform init` en el lab)
#   - CI:     OUTPUTS_JSON=outputs.json (artifact del job apply)

set -uo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[1]}")/.." && pwd)"
export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_DEFAULT_REGION="$AWS_REGION"
export AWS_PAGER=""

PASS=0
FAIL=0

out() {
  if [ -n "${OUTPUTS_JSON:-}" ]; then
    jq -r --arg k "$1" '.[$k].value' "$OUTPUTS_JSON"
  else
    terraform -chdir="$LAB_DIR" output -raw "$1"
  fi
}

out_json() {
  if [ -n "${OUTPUTS_JSON:-}" ]; then
    jq -c --arg k "$1" '.[$k].value' "$OUTPUTS_JSON"
  else
    terraform -chdir="$LAB_DIR" output -json "$1"
  fi
}

section() { printf '\n\033[1m== %s\033[0m\n' "$1"; }
ok()      { printf '  \033[32mOK\033[0m   %s\n' "$1"; PASS=$((PASS + 1)); }
ko()      { printf '  \033[31mFAIL\033[0m %s\n' "$1"; FAIL=$((FAIL + 1)); }
info()    { printf '  ..   %s\n' "$1"; }

# check "descripción" comando args...  -> OK si el comando termina en 0
check() {
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then ok "$desc"; else ko "$desc"; fi
}

# expect "descripción" <obtenido> <esperado>
expect() {
  if [ "$2" == "$3" ]; then ok "$1 ($2)"; else ko "$1: esperado '$3', obtenido '$2'"; fi
}

# expect_match "descripción" <texto> <regex>
expect_match() {
  if printf '%s' "$2" | grep -Eq "$3"; then ok "$1"; else ko "$1: '$3' no aparece en: ${2:0:200}"; fi
}

# retry <intentos> <segundos> comando...  (para recursos eventualmente consistentes)
retry() {
  local n="$1" wait="$2"; shift 2
  for _ in $(seq 1 "$n"); do
    if "$@"; then return 0; fi
    sleep "$wait"
  done
  return 1
}

# http_code <url> [args curl...] -> imprime solo el código HTTP
http_code() {
  local url="$1"; shift
  curl -s -o /dev/null -w '%{http_code}' "$@" "$url"
}

require() {
  for bin in "$@"; do
    command -v "$bin" >/dev/null 2>&1 || { echo "Falta '$bin' en el PATH"; exit 2; }
  done
}

summary() {
  echo
  if [ "$FAIL" -eq 0 ]; then
    printf '\033[32mSMOKE TEST OK\033[0m  (%d verificaciones)\n' "$PASS"
  else
    printf '\033[31mSMOKE TEST CON FALLAS\033[0m  (%d OK, %d fallas)\n' "$PASS" "$FAIL"
  fi
  [ "$FAIL" -eq 0 ]
}

# Usuario de prueba de Cognito (labs 01, 02 y 04). Exporta TEST_USER y TOKEN.
cognito_login() {
  local pool="$1" client="$2"
  TEST_USER="smoke-$(date +%s)-$RANDOM@example.com"
  TEST_PASS="Smoke-$(date +%s)-Aa1!"
  aws cognito-idp admin-create-user --user-pool-id "$pool" --username "$TEST_USER" \
    --message-action SUPPRESS >/dev/null
  aws cognito-idp admin-set-user-password --user-pool-id "$pool" --username "$TEST_USER" \
    --password "$TEST_PASS" --permanent >/dev/null
  TOKEN=$(aws cognito-idp initiate-auth --client-id "$client" --auth-flow USER_PASSWORD_AUTH \
    --auth-parameters "USERNAME=$TEST_USER,PASSWORD=$TEST_PASS" \
    --query AuthenticationResult.IdToken --output text)
  export TEST_USER TOKEN
}

cognito_cleanup() {
  aws cognito-idp admin-delete-user --user-pool-id "$1" --username "$TEST_USER" >/dev/null 2>&1 || true
}
