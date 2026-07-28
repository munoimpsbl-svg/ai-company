#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
dist="$root/dist"
package_dir="$dist/AI_COMPANY_Windows"
zip_path="$dist/AI_COMPANY_Windows_Installer.zip"

rm -rf "$package_dir" "$zip_path"
mkdir -p "$package_dir"

rsync -a "$root/" "$package_dir/" \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude '.secrets/' \
  --exclude '.env' \
  --include '.env.example' \
  --exclude '.env.*' \
  --exclude '__pycache__/' \
  --exclude '.pycache/' \
  --exclude '*.pyc' \
  --exclude '.DS_Store' \
  --exclude 'dist/' \
  --exclude 'output/' \
  --exclude '02_Daily_Output/*/images/' \
  --exclude '02_Daily_Output/**/*.png' \
  --exclude '02_Daily_Output/**/*.jpg' \
  --exclude '02_Daily_Output/**/*.jpeg' \
  --exclude '02_Daily_Output/**/*.webp'

(
  cd "$dist"
  zip -qr "$(basename "$zip_path")" "AI_COMPANY_Windows"
)

echo "$zip_path"
