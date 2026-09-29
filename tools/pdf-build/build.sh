#!/usr/bin/env bash
# Build the PDF edition of curriculum/ and check it. See README.md. Exits non-zero if any check fails.
set -euo pipefail
# a relative OUT_PDF is relative to where the script was called from
OUT_PDF=$(python3 -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "${OUT_PDF:-$(dirname "$0")/dist/LLM-Training-Flow-Vol2-Curriculum-and-FDE-Projects.pdf}")
cd "$(dirname "$0")"
export COMMIT=${COMMIT:-$(git rev-parse --short HEAD)}
# the cover says so when curriculum/ has uncommitted changes
export DIRTY=${DIRTY:-$(git status --porcelain -- ../../curriculum | head -c1)}
[ -d node_modules ] || { echo "node_modules is missing: run 'npm ci' in tools/pdf-build first" >&2; exit 1; }
mkdir -p out "$(dirname "$OUT_PDF")"
node prepare_elk.mjs
python3 build_loop.py                  # render passes until page numbers settle and nothing is stranded
node render_cover.mjs
python3 finalize.py "$OUT_PDF"         # cover, bookmarks, running headers and footers
echo "PDF: $OUT_PDF"
python3 verify.py "$OUT_PDF"           # prints the checks and ends with CHECKS PASSED or CHECKS FAILED
