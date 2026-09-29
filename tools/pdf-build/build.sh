#!/usr/bin/env bash
# Build the PDF edition of curriculum/ and check it. See README.md.
set -euo pipefail
cd "$(dirname "$0")"
OUT_PDF=${OUT_PDF:-dist/LLM-Training-Flow-Vol2-Curriculum-and-FDE-Projects.pdf}
export COMMIT=${COMMIT:-$(git rev-parse --short HEAD)}
[ -d node_modules ] || { echo "node_modules is missing: run 'npm ci' in tools/pdf-build first" >&2; exit 1; }
mkdir -p out "$(dirname "$OUT_PDF")"
node prepare_elk.mjs
python3 build_loop.py                          # render passes until page numbers settle and nothing is stranded
node render_cover.mjs
python3 finalize.py "$OUT_PDF" 2> out/finalize.log   # merge the cover, bookmarks, running headers and footers
python3 verify.py "$OUT_PDF"                   # links, missing words, layout checks
echo "PDF: $OUT_PDF"
