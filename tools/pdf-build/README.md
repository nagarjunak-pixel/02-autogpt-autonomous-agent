# PDF build for `curriculum/`

This folder turns every Markdown document under `curriculum/` into one typeset PDF. The book has:
- a cover, an About page and a Contents list with page numbers;
- 7 part dividers and 58 chapters;
- rendered Mermaid diagrams, highlighted code, bookmarks, running headers and page numbers.

It then checks the result.

## Build

You need Node 22 and Python 3.11 or later.

```bash
cd tools/pdf-build
npm ci                                   # JavaScript dependencies (Mermaid, markdown-it, Playwright, web fonts)
npx playwright install chromium          # skip if a Chromium is already installed (see CHROMIUM_PATH below)
pip install -r requirements.txt          # pypdf, pypdfium2, reportlab, pikepdf, Pillow, fonttools
./build.sh                               # about 8 minutes; writes dist/LLM-Training-Flow-Vol2-Curriculum-and-FDE-Projects.pdf
```

The cover shows the commit and date of the build (`git rev-parse --short HEAD` and today's date).

Environment variables:

| Variable | Default | Use |
|---|---|---|
| `OUT_PDF` | `dist/LLM-Training-Flow-Vol2-Curriculum-and-FDE-Projects.pdf` | Where the finished PDF goes |
| `COMMIT` | the current `HEAD` | The commit printed on the cover and used in links to the repository |
| `CHROMIUM_PATH` | Playwright's own Chromium | An existing Chromium or Chrome binary to use instead |

`out/`, `dist/`, `vendor/` and `node_modules/` are build products and are not committed.

## What the build does

1. **`prepare_elk.mjs`** copies the ELK layout engine for Mermaid into `vendor/elk`. It tightens ELK's base spacing from 40 to 24, so that diagrams with many nested boxes fit a page at a readable size.
2. **`build_loop.py`** runs `build.mjs` repeatedly. Each pass renders the whole book in headless Chromium:
   - Markdown to HTML (`build.mjs`) and the stylesheet (`style.css`);
   - Mermaid diagrams, each placed inline, on a portrait figure page or on a landscape page, whichever gives the largest labels;
   - text rules that keep IDs, dates, units and short names together.

   `pages.py` then reads the page number of every chapter. The loop stops when:
   - the page numbers stop changing;
   - no heading or lead-in is left at the foot of a page;
   - no chapter ends on a page holding only a few lines.

   A chapter whose last page would hold only a few lines is set slightly tighter.
3. **`render_cover.mjs`** renders `cover.html`, stamped with the commit and date.
4. **`finalize.py`** merges the cover with the book and repairs the bookmarks. It adds the running headers (part and chapter) and footers (title and page number), and draws the accent bar on part dividers. Then it compresses the file.
5. **`verify.py`** checks:
   - every internal link resolves, and every word of the source appears in the PDF;
   - all diagrams render;
   - no table overflows, and no ordinary word breaks in a table cell;
   - no stranded headings, widows or orphans;
   - no chapter ends on a nearly empty page, and no part divider spills onto a second page.

   A clean build reports 0 for each of these.

`front.html` is the About page. The part titles and blurbs are the `PARTS` list at the top of `build.mjs`.

## Fonts

- **Body text:** Source Serif 4.
- **Headings, tables and labels:** Inter.
- **Code:** JetBrains Mono.
- **Devanagari:** Noto Sans Devanagari.

The web fonts come from npm (`@fontsource/*`). The files in `fonts/` fill the gaps:
- the full Inter release, with the tailed lowercase l as the default glyph so that l and I look different;
- Source Serif 4 and JetBrains Mono for the arrows and maths signs that the web subsets lack.

`fonts/prepare_fonts.py` recreates these files from the upstream releases, byte for byte. All four families are under the SIL Open Font License 1.1; the licence texts are in `fonts/`.

## Checking a build by eye

- `python3 zoom.py PAGE x0 y0 x1 y1 SCALE` renders part of a page of the finished PDF at high resolution into `png/zoom/`. x and y are fractions of the page; use SCALE 3–5.
- `node diagharness.mjs curriculum/projects/P06-injection-resistant-inbox-agent.md …` renders just the diagrams of the given files with the build's own diagram code, into `out/dh-N.png`. It prints the placement and label size of each. It needs `out/book-pass2.html` from a previous build.
