#!/usr/bin/env bash
# Add or replace README.md from snippets/ for selected repos.
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)
SNIP="$DIR/snippets"

declare -A MAP=(
  [noah-animal-clinic]=noah-animal-clinic-README.md
  [venkatesh-llm]=venkatesh-llm-README.md
  [operdai-backend]=operdai-backend-README.md
)

for repo in "${!MAP[@]}"; do
  src="$SNIP/${MAP[$repo]}"
  echo "==> $repo (README from ${MAP[$repo]})"
  work=$(mktemp -d)
  gh repo clone "nagarjunak-pixel/$repo" "$work/$repo" -- --depth 1
  cp "$src" "$work/$repo/README.md"
  cd "$work/$repo"
  git add README.md
  if git diff --cached --quiet; then
    echo "    (no change)"
  else
    git commit -m "docs: add clear README"
    git push origin HEAD
  fi
  rm -rf "$work"
done
