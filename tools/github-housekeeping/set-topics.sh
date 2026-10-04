#!/usr/bin/env bash
# GitHub allows up to 20 topics per repo; values are comma-separated in topics.tsv
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)
TSV="$DIR/topics.tsv"
while IFS=$'\t' read -r name topics; do
  [[ -z "$name" || "$name" =~ ^# ]] && continue
  echo "==> $name → $topics"
  IFS=',' read -ra TOPIC_ARR <<< "$topics"
  args=()
  for t in "${TOPIC_ARR[@]}"; do
    args+=(--add-topic "$t")
  done
  gh repo edit "nagarjunak-pixel/$name" "${args[@]}"
done < "$TSV"
