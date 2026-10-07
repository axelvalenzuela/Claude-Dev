#!/usr/bin/env bash
# Valida el ciclo sin costo alto: dataset -> batch prediction -> evaluación del modelo base.
# El fine-tuning (con costo) solo corre con RUN_TUNING=1.
source "$(dirname "$0")/../../../scripts/lib.sh"
require gcloud python jq

BUCKET=$(out ml_bucket)
export GOOGLE_CLOUD_PROJECT="$PROJECT" ML_BUCKET="$BUCKET" GOOGLE_CLOUD_REGION="$(out region)"
cd "$LAB_DIR/scripts"

section "Dataset SFT"
python gen_dataset.py && ok "Dataset generado y subido" || ko "gen_dataset.py falló"
check "train.jsonl en gs://$BUCKET" gcloud storage ls "gs://$BUCKET/datasets/train.jsonl"
LINE=$(gcloud storage cat "gs://$BUCKET/datasets/train.jsonl" | head -1)
expect_match "Formato SFT (contents user/model)" "$LINE" '"role": "model"'

section "Batch prediction (5 tickets)"
OUT=$(python batch.py 2>&1); echo "$OUT" | tail -6
expect_match "Job terminado" "$OUT" "JOB_STATE_SUCCEEDED"
expect_match "Clasificó facturación" "$OUT" "facturacion"

section "Evaluación del modelo base (10 casos)"
EVAL=$(EVAL_LIMIT=10 python evaluate.py)
ACC=$(echo "$EVAL" | jq -r '.[0].exactitud')
info "Exactitud base: $ACC · $(echo "$EVAL" | jq -c '.[0].por_etiqueta')"
awk "BEGIN{exit !($ACC >= 0.6)}" && ok "Exactitud base >= 60 %" || ko "Exactitud base $ACC"

if [ "${RUN_TUNING:-0}" = "1" ]; then
  section "Fine-tuning (con costo, 20-60 min)"
  python tune.py && ok "Tuning terminado: exporta TUNED_MODEL y corre evaluate.py para comparar"
fi

summary
