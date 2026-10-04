#!/usr/bin/env bash
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)
REPO=nagarjunak-pixel
work=$(mktemp -d)
gh repo clone "nagarjunak-pixel/$REPO" "$work/$REPO" -- --depth 1
cp "$DIR/profile-README.md" "$work/$REPO/README.md"
cd "$work/$REPO"
git add README.md
if git diff --cached --quiet; then
  echo "Profile README already up to date."
else
  git commit -m "docs: refresh grouped index of all public repositories"
  git push origin HEAD
fi
rm -rf "$work"
