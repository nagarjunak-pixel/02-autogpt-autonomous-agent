# PDF build for `curriculum/`

This folder turns the Markdown documents under `curriculum/` into one typeset PDF. The book has:
- a cover, an About page and a Contents list with page numbers;
- 7 part dividers and 58 chapters;
- rendered Mermaid diagrams, highlighted code, bookmarks, running headers and page numbers.

It then checks the result.

## Build

You need Node 22 and Python 3.11 or later.

```bash
cd tools/pdf-build
npm ci                               # JavaScript dependencies (Mermaid, markdown-it, Playwright 1.56.1, web fonts)
npx playwright install chromium      # Playwright's Chromium 141 (revision 1194); skip if it is already in Playwright's browser cache
python3 -m venv .venv && . .venv/bin/activate    # optional; needed where the system Python is externally managed
pip install -r requirements.txt      # pypdf, pypdfium2, reportlab, pikepdf, Pillow, fonttools
./build.sh                           # 8–12 minutes; writes dist/LLM-Training-Flow-Vol2-Curriculum-and-FDE-Projects.pdf
```

`build.sh` ends with the checks in step 5 below. It prints `CHECKS PASSED` and exits 0, or `CHECKS FAILED: …` naming what failed and exits 1.

The cover shows:
- the repository;
- the commit (`git rev-parse --short HEAD`), marked "(with uncommitted changes)" if `curriculum/` has any;
- the build date.

Environment variables:

| Variable | Default | Use |
|---|---|---|
| `OUT_PDF` | `dist/LLM-Training-Flow-Vol2-Curriculum-and-FDE-Projects.pdf` in this folder | Where the finished PDF goes. A relative path is relative to the directory you run `build.sh` from. |
| `COMMIT` | the current `HEAD` | The commit printed on the cover, and used in any links to repository files |
| `REPO_URL` | `https://github.com/nagarjunak-pixel/02-autogpt-autonomous-agent` | The repository named on the cover and used in those links; set it when building from a fork |
| `CHROMIUM_PATH` | Playwright's full Chromium | Another Chromium or Chrome binary. Only Playwright 1.56.1's Chromium (revision 1194) reproduces the published page layout exactly. |

The build launches the full Chromium (`channel: 'chromium'`), not Playwright's default headless shell. The two measure text slightly differently, so using the same browser keeps the page layout reproducible. If the full Chromium cannot start, the build stops rather than fall back. The browser version is recorded in `out/build-report.json` and printed by the checks.

`out/`, `dist/`, `vendor/`, `png/` and `node_modules/` are build products and are not committed.

## What the build does

1. **`prepare_elk.mjs`** copies the ELK layout engine for Mermaid from `node_modules` into `vendor/elk`.
   - It tightens ELK's base spacing from 40 to 24, so that diagrams with many nested boxes fit a page at a readable size.
   - It stops with an error if a new `@mermaid-js/layout-elk` version no longer contains that setting.
2. **`build_loop.py`** runs `build.mjs` repeatedly. Each pass renders the whole book in headless Chromium:
   - Markdown to HTML (`build.mjs`) and the stylesheet (`style.css`);
   - Mermaid diagrams, each placed inline, on a portrait figure page or on a landscape page, whichever gives the largest labels;
   - text rules that keep IDs, dates, units and short names together.

   `pages.py` then reads the page number of every chapter. After each pass, `build_loop.py` does two things:
   - It forces a page break before any heading or lead-in newly stranded at a page foot.
   - It sets a chapter slightly tighter if its last page would hold six lines or fewer. There are up to two levels of tightening.

   The loop stops when the page numbers are stable and nothing new needs a change. Anything left over is reported by the checks in step 5.

   The chapters, and their order and grouping into parts, are the `PARTS` list at the top of `build.mjs`. The build reports a problem, which fails the checks, if a tracked `.md` file under `curriculum/` is missing from that list.
3. **`render_cover.mjs`** renders `cover.html`, stamped with the repository, commit and date.
4. **`finalize.py`** merges the cover with the book and repairs the bookmarks. It adds the running headers (part and chapter) and footers (title and page number), and draws the accent bar on part dividers. Then it compresses the file.
5. **`verify.py`** checks the finished PDF and the build report:
   - **links:** every internal link resolves;
   - **text:** every word of 4 or more letters in each source file appears in that chapter's pages (diagram sources and link targets excluded);
   - **diagrams:** all render, without errors;
   - **build problems:** none, such as a missing link target, an unresolved anchor, the ELK engine not loading, or a file missing from `PARTS`;
   - **tables:** none overflows, and no ordinary word breaks inside a cell;
   - **page layout:**
     - no heading or lead-in is stranded, and there are no widows or orphans;
     - no chapter ends on a page of three lines or fewer;
     - no part divider spills onto a second page.

   It also prints "broken long tokens in cells". That is information, not a failure: long hyphenated or code tokens wrapping inside a narrow cell, as they must.

`front.html` is the About page. The part titles and blurbs are in `PARTS` in `build.mjs`.

## Fonts

- **Body text:** Source Serif 4.
- **Headings, tables and labels:** Inter.
- **Code:** JetBrains Mono.
- **Devanagari:** Noto Sans Devanagari.

The web fonts come from npm (`@fontsource/*`). The files in `fonts/` fill the gaps:
- the full Inter release, with the tailed lowercase l as the default glyph so that l and I look different;
- Source Serif 4 and JetBrains Mono for the arrows and maths signs that the web subsets lack;
- DejaVu Sans for ✓ and ✗ everywhere, and for any character Inter lacks in the running headers.

`fonts/prepare_fonts.py` recreates the Inter, Source Serif 4 and JetBrains Mono files from the upstream releases. It checks the SHA-256 of each download and of each output file.

Licences:
- Inter, Source Serif 4 and JetBrains Mono are under the SIL Open Font License 1.1. DejaVu Sans is under the Bitstream Vera licence.
- Their licence texts are in `fonts/`.
- Noto Sans Devanagari (OFL) ships with its npm package.

A few rare characters that none of these fonts cover fall back to the fonts installed on the system. There are about three in the whole book, such as the Devanagari danda. With `fonts-dejavu-core` and `fonts-freefont-ttf` installed (Debian and Ubuntu package names), the output matches the published PDF exactly. Without them, only those characters' shapes differ.

## Checking a build by eye

Run these from `tools/pdf-build` after a build:

- **`python3 zoom.py PAGE x0 y0 x1 y1 SCALE`** renders part of a page of the finished PDF at high resolution into `png/zoom/`.
  - PAGE is the 0-based page index; 0 is the cover, so it equals the printed page number.
  - x and y are fractions of the page.
  - Use SCALE 3–5.
- **`node diagharness.mjs curriculum/projects/P06-injection-resistant-inbox-agent.md …`** renders just the diagrams of the given files into `out/dh-N.png`.
  - It uses the build's own diagram code, stylesheet and fonts, and prints the placement and label size of each diagram.
  - It needs `out/book-pass2.html` from a previous build.
