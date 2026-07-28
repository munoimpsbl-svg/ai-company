#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 <image-or-directory> [...]" >&2
  exit 2
fi

paths=()
for input in "$@"; do
  if [ -d "$input" ]; then
    while IFS= read -r -d '' file; do
      paths+=("$file")
    done < <(find "$input" -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' \) -print0)
  elif [ -f "$input" ]; then
    paths+=("$input")
  else
    echo "Missing path: $input" >&2
    exit 1
  fi
done

if [ "${#paths[@]}" -eq 0 ]; then
  echo "No images found." >&2
  exit 0
fi

total_size() {
  existing_paths=()
  for path in "${paths[@]}"; do
    if [ -f "$path" ]; then
      existing_paths+=("$path")
    fi
  done

  if [ "${#existing_paths[@]}" -eq 0 ]; then
    echo 0
    return
  fi

  wc -c "${existing_paths[@]}" | awk 'END {print $1}'
}

echo "Sending ${#paths[@]} image(s) to ImageOptim..."
open -a ImageOptim -- "${paths[@]}"

stable_seconds="${IMAGEOPTIM_STABLE_SECONDS:-20}"
poll_seconds="${IMAGEOPTIM_POLL_SECONDS:-5}"
min_wait_seconds="${IMAGEOPTIM_MIN_WAIT_SECONDS:-60}"
max_wait_seconds="${IMAGEOPTIM_MAX_WAIT_SECONDS:-600}"

previous_size="$(total_size)"
stable_for=0
elapsed=0

while [ "$elapsed" -lt "$max_wait_seconds" ]; do
  sleep "$poll_seconds"
  elapsed=$((elapsed + poll_seconds))

  current_size="$(total_size)"
  if [ "$current_size" = "$previous_size" ]; then
    stable_for=$((stable_for + poll_seconds))
  else
    stable_for=0
    previous_size="$current_size"
  fi

  if [ "$elapsed" -ge "$min_wait_seconds" ] && [ "$stable_for" -ge "$stable_seconds" ]; then
    echo "Image sizes stable for ${stable_for}s. Assuming ImageOptim finished."
    osascript -e 'tell application "ImageOptim" to quit' >/dev/null 2>&1 || true
    echo "ImageOptim finished."
    exit 0
  fi
done

echo "Timed out waiting for ImageOptim after ${max_wait_seconds}s." >&2
echo "ImageOptim may still be running; please check it manually." >&2
exit 1
