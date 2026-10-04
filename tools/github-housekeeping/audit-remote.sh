#!/usr/bin/env bash
# Re-scan public repos for committed junk (read-only).
set -euo pipefail
python3 << 'PY'
import json, subprocess

def tree_paths(name: str) -> list[str]:
    for branch in ("main", "master"):
        try:
            out = subprocess.check_output(
                [
                    "gh", "api",
                    f"repos/nagarjunak-pixel/{name}/git/trees/{branch}?recursive=1",
                    "-q", ".tree[].path",
                ],
                text=True,
            )
            return out.splitlines()
        except subprocess.CalledProcessError:
            continue
    return []

repos = json.loads(
    subprocess.check_output(
        ["gh", "repo", "list", "nagarjunak-pixel", "--limit", "100", "--json", "name"],
        text=True,
    )
)
issues = []
for r in repos:
    name = r["name"]
    if name == "nagarjunak-pixel":
        continue
    paths = tree_paths(name)
    if not paths:
        continue
    flags = []
    if any(p.startswith(".venv/") for p in paths):
        flags.append(".venv")
    if any(p.startswith("node_modules/") for p in paths):
        flags.append("node_modules")
    if ".env" in paths:
        flags.append(".env")
    root = subprocess.check_output(
        ["gh", "api", f"repos/nagarjunak-pixel/{name}/contents/", "-q", ".[].name"],
        text=True,
    ).splitlines()
    if not any(x.lower().startswith("readme") for x in root):
        flags.append("no-readme")
    if flags:
        issues.append((name, ", ".join(flags)))
print("Repos with open hygiene issues:", len(issues))
for name, flags in sorted(issues):
    print(f"  {name}: {flags}")
if not issues:
    print("  (none — account looks clean)")
PY
