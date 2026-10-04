#!/usr/bin/env bash
# Run the full account hygiene pass (requires gh auth with push access).
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)

if ! gh auth status >/dev/null 2>&1; then
  echo "Authenticate first: gh auth login" >&2
  exit 1
fi

echo "=== 1/7 Strip committed .venv ==="
"$DIR/strip-tracked-venv.sh" operdai-backend antigravity-sdk localaitv-mcp-server tokens-eat-up

echo "=== 2/7 Strip committed node_modules ==="
"$DIR/strip-tracked-node-modules.sh" spring-boot-mcp

echo "=== 3/7 Add READMEs ==="
"$DIR/add-missing-readmes.sh"

echo "=== 4/7 Add Python .gitignore ==="
"$DIR/add-python-gitignore.sh" ai-calc pytorch-interactive-demo

echo "=== 5/7 Publish profile index ==="
"$DIR/publish-profile-index.sh"

echo "=== 6/7 Set GitHub descriptions ==="
"$DIR/set-descriptions.sh"

echo "=== 7/7 Set GitHub topics ==="
"$DIR/set-topics.sh"

echo "=== Audit ==="
"$DIR/audit-remote.sh"

echo "Done."
