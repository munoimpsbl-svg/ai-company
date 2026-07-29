#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 scripts/ingest_reference_images.py \
  --source "/Volumes/music/写真集/AI_COMPANY_Reference/_incoming" \
  --recursive \
  --label "daily_reference"
