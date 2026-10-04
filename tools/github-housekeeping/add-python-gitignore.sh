#!/usr/bin/env bash
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)
TEMPLATE="$DIR/snippets/python-gitignore"
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <repo> [repo ...]" >&2
  exit 1
fi
for repo in "$@"; do
  echo "==> $repo"
  work=$(mktemp -d)
  gh repo clone "nagarjunak-pixel/$repo" "$work/$repo" -- --depth 1
  cd "$work/$repo"
  if [[ -f .gitignore ]] && grep -q '^\.venv/' .gitignore; then
    echo "    (.gitignore already has .venv/)"
  elif [[ -f .gitignore ]]; then
    cat "$TEMPLATE" >> .gitignore
    git add .gitignore
    git commit -m "chore: extend .gitignore for Python artifacts"
    git push origin HEAD
  else
    cp "$TEMPLATE" .gitignore
    git add .gitignore
    git commit -m "chore: add Python .gitignore"
    git push origin HEAD
  fi
  rm -rf "$work"
done
