#!/usr/bin/env bash
set -euo pipefail

python evaluate_skillnet.py validate-package \
  --gold ../02_Gold_Standard_21_V4.json \
  --output ../results/package_validation_report.json

for CONFIG in A B C; do
  python evaluate_skillnet.py evaluate \
    --gold ../02_Gold_Standard_21_V4.json \
    --predictions ../predictions/${CONFIG}/run_01 \
    --configuration ${CONFIG} \
    --run-id 1 \
    --output-dir ../results/${CONFIG}_run_01
done

python evaluate_skillnet.py aggregate \
  --input-root ../results \
  --output-dir ../results/summary
