#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 scripts/ingest_reference_images.py \
  --source "/Volumes/music/写真集" \
  --out-root "/Volumes/music/写真集/AI_COMPANY_Reference/_index" \
  --recursive \
  --max-images 0 \
  --label "photobook_refs_non_kikuchi" \
  --purpose mixed \
  --character common \
  --exclude-text "菊地姫奈" \
  --exclude-text "Kikuchi Hina" \
  --exclude-text "Hina Kikuchi" \
  --exclude-text "ヌード" \
  --exclude-text "nude"
