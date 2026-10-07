#!/usr/bin/env bash
# Utilidades compartidas por los smoke tests de los micro labs de GCP.
#   source "$(dirname "$0")/../../../scripts/lib.sh"
# Outputs: terraform output (local) u OUTPUTS_JSON=outputs.json (CI).
# Proyecto: GOOGLE_CLOUD_PROJECT o el configurado en gcloud.

set -uo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[1]}")/.." && pwd)"
PROJECT="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
export CLOUDSDK_CORE_DISABLE_PROMPTS=1

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

check() {
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then ok "$desc"; else ko "$desc"; fi
}

expect() {
  if [ "$2" == "$3" ]; then ok "$1 ($2)"; else ko "$1: esperado '$3', obtenido '$2'"; fi
}

expect_match() {
  if printf '%s' "$2" | grep -Eq "$3"; then ok "$1"; else ko "$1: '$3' no aparece en: ${2:0:200}"; fi
}

retry() {
  local n="$1" wait="$2"; shift 2
  for _ in $(seq 1 "$n"); do
    if "$@"; then return 0; fi
    sleep "$wait"
  done
  return 1
}

http_code() {
  local url="$1"; shift
  curl -s -o /dev/null -w '%{http_code}' "$@" "$url"
}

# ID token de tu identidad para invocar servicios privados de Cloud Run / functions
id_token() {
  gcloud auth print-identity-token 2>/dev/null
}

access_token() {
  gcloud auth print-access-token 2>/dev/null
}

require() {
  for bin in "$@"; do
    command -v "$bin" >/dev/null 2>&1 || { echo "Falta '$bin' en el PATH"; exit 2; }
  done
  [ -n "$PROJECT" ] || { echo "Define GOOGLE_CLOUD_PROJECT o ejecuta: gcloud config set project <id>"; exit 2; }
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
