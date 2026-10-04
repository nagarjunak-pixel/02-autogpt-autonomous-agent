#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <repo-name> [repo-name ...]" >&2
  exit 1
fi
for repo in "$@"; do
  echo "==> $repo"
  work=$(mktemp -d)
  gh repo clone "nagarjunak-pixel/$repo" "$work/$repo" -- --depth 1
  cd "$work/$repo"
  git rm -r --cached -f node_modules 2>/dev/null || true
  if [[ ! -f .gitignore ]]; then
    echo 'node_modules/' > .gitignore
  elif ! grep -q '^node_modules/' .gitignore; then
    echo 'node_modules/' >> .gitignore
  fi
  git add .gitignore
  git commit -m "chore: stop tracking node_modules" || true
  git push origin HEAD
  rm -rf "$work"
done
