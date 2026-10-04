#!/usr/bin/env bash
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)
TSV="$DIR/descriptions.tsv"
while IFS=$'\t' read -r name desc; do
  [[ -z "$name" || "$name" =~ ^# ]] && continue
  echo "==> $name"
  gh repo edit "nagarjunak-pixel/$name" --description "$desc"
done < "$TSV"
