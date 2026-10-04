#!/usr/bin/env bash
# Remove committed Python virtualenvs from git history (files stay on disk).
set -euo pipefail
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <repo-name> [repo-name ...]" >&2
  exit 1
fi
PY_GITIGNORE=$'# Python\n__pycache__/\n*.py[cod]\n.venv/\nvenv/\n*.egg-info/\n.pytest_cache/\n.env\n!.env.example\n'
for repo in "$@"; do
  echo "==> $repo"
  work=$(mktemp -d)
  gh repo clone "nagarjunak-pixel/$repo" "$work/$repo" -- --depth 1
  cd "$work/$repo"
  git rm -r --cached -f .venv 2>/dev/null || true
  git rm -r --cached -f operdai.egg-info 2>/dev/null || true
  if [[ ! -f .gitignore ]]; then
    printf '%s' "$PY_GITIGNORE" > .gitignore
  elif ! grep -q '^\.venv/' .gitignore; then
    printf '%s' "$PY_GITIGNORE" >> .gitignore
  fi
  git add .gitignore
  git commit -m "chore: stop tracking virtualenv and Python build artifacts" || true
  git push origin HEAD
  rm -rf "$work"
done
