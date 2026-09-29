import os as _os; _CWD = _os.getcwd(); _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))   # paths below are relative to this folder
import json, re, sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject
main, cover, out = 'out/main-pass2.pdf', 'out/cover.pdf', _os.path.join(_CWD, sys.argv[1])
heads = json.load(open('out/headings-pass2.json')); marks = json.load(open('out/bookmarks-pass2.json'))
assert len(heads) == len(marks)
w = PdfWriter()
w.append(PdfReader(cover), import_outline=False)
w.append(PdfReader(main), import_outline=True)
# repair bookmark titles: Chromium drops the space at line wraps; restore from the DOM heading text (same order)
root = w._root_object['/Outlines'].get_object()
items = []
def walk(node):
    cur = node.get('/First')
    while cur is not None:
        o = cur.get_object(); items.append(o)
        walk(o); cur = o.get('/Next')
walk(root)
norm = lambda s: re.sub(r'\s+', '', s)
assert len(items) == len(heads), (len(items), len(heads))
mism = [(o['/Title'], h) for o, h in zip(items, heads) if norm(str(o['/Title'])) != norm(h)]
assert not mism, mism[:5]
# bookmark titles leave out an entry heading's metadata line (priority, status, placement)
fixed = sum(1 for o, h in zip(items, marks) if str(o['/Title']) != h)
for o, h in zip(items, marks): o[NameObject('/Title')] = TextStringObject(h)
n = len(w.pages)

# running headers and footers (stamped, so they can name the current part and chapter)
import io
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as RLFont
from reportlab.lib.units import mm
pdfmetrics.registerFont(RLFont('Inter', 'fonts/Inter-400.ttf'))
pdfmetrics.registerFont(RLFont('Inter-SemiBold', 'fonts/Inter-600.ttf'))
pdfmetrics.registerFont(RLFont('DejaVu', 'fonts/DejaVuSans.ttf'))
# characters Inter lacks are drawn in DejaVu Sans
from fontTools.ttLib import TTFont as _FT
_INTER = set(_FT('fonts/Inter-400.ttf').getBestCmap())
def runs(text, font):
    out = []
    for ch in text:
        f = font if ord(ch) in _INTER or ch == ' ' else 'DejaVu'
        if out and out[-1][0] == f: out[-1][1] += ch
        else: out.append([f, ch])
    return out
def width(text, font, size): return sum(pdfmetrics.stringWidth(t, f, size) for f, t in runs(text, font))
def draw_right(c, x, y, text, font, size):
    x -= width(text, font, size)
    for f, t in runs(text, font):
        c.setFont(f, size); c.drawString(x, y, t); x += pdfmetrics.stringWidth(t, f, size)
rep = json.load(open('out/build-report.json')); toc = json.load(open('out/toc2.json'))
part_of, i = {}, 0
for pi, p in enumerate(rep['parts'], 1):
    for ch in rep['chapters'][i:i + p['files']]:
        part_of[ch['id']] = (pi, p['title'])
    i += p['files']
starts = sorted((toc[c['id']], c) for c in rep['chapters'])
part_pages = {toc[p['id']] for p in rep['parts']}
chapter_first = {s for s, _ in starts}
DOC = 'LLM Training Flow Vol. 2 \u00b7 Curriculum Review, Gap Register, Future Topics and FDE Projects'
# running-head titles for chapters whose full title does not fit beside the part name
SHORT = {'LLM Training Flow Vol. 2: Curriculum Review, Gap Register, Future Topics and FDE Projects': 'Overview of the package'}
MUTED, ACCENT, RULE = (0.36, 0.40, 0.45), (0.07, 0.25, 0.42), (0.80, 0.83, 0.87)

def fit(text, font, size, w):
    if width(text, font, size) <= w: return text
    while text and width(text + '\u2026', font, size) > w: text = text[:-1]
    return text.rstrip(' \u00b7:,') + '\u2026'

# pages whose content reaches into the header band (full-page diagrams on the narrow-margin 'figure' page) get no running header
import pypdfium2 as pdfium
_m = pdfium.PdfDocument(main)
def header_band_used(j):
    pg = _m[j]; H0 = pg.get_height(); tp = pg.get_textpage()
    return any(tp.get_charbox(k)[3] > H0 - 17 * mm for k in range(tp.count_chars()))
# all overlays go into ONE document so the header font is embedded once and shared by every page
buf = io.BytesIO(); c = rl_canvas.Canvas(buf)
plan = []
for idx in range(1, n):                      # index 0 is the cover
    if idx in part_pages:                    # part dividers get only their accent bar, at the top of the text area
        page = w.pages[idx]; W, H = float(page.mediabox.width), float(page.mediabox.height)
        c.setPageSize((W, H)); c.setFillColorRGB(*ACCENT)
        c.rect(17 * mm, H - 21 * mm - 3, 34 * mm, 3, stroke=0, fill=1)
        c.showPage(); plan.append(idx); continue
    if any(pp < idx < min((st for st, _ in starts if st > pp), default=n) for pp in part_pages): continue   # a divider's overflow page
    page = w.pages[idx]
    W, H = float(page.mediabox.width), float(page.mediabox.height)
    ch = next((ch for s, ch in reversed(starts) if s <= idx), None)
    c.setPageSize((W, H))
    x0, x1 = 17 * mm, W - 17 * mm
    if ch and idx not in chapter_first and not header_band_used(idx - 1):
        pn, pt = part_of[ch['id']]
        left = f'PART {pn} \u00b7 {pt.upper()}'
        lw = min(pdfmetrics.stringWidth(left, 'Inter-SemiBold', 6.6), (x1 - x0) * 0.42)
        c.setFont('Inter-SemiBold', 6.6); c.setFillColorRGB(*ACCENT)
        c.drawString(x0, H - 12.2 * mm, fit(left, 'Inter-SemiBold', 6.6, (x1 - x0) * 0.42))
        c.setFont('Inter', 7.2); c.setFillColorRGB(*MUTED)
        draw_right(c, x1, H - 12.2 * mm, fit(SHORT.get(ch['title'], ch['title']), 'Inter', 7.2, (x1 - x0) - lw - 12 * mm), 'Inter', 7.2)
        c.setStrokeColorRGB(*RULE); c.setLineWidth(0.5); c.line(x0, H - 14 * mm, x1, H - 14 * mm)
    c.setFont('Inter', 6.8); c.setFillColorRGB(*MUTED)
    c.drawString(x0, 10.5 * mm, fit(DOC, 'Inter', 6.8, (x1 - x0) * 0.8))
    c.setFont('Inter-SemiBold', 8); c.setFillColorRGB(*ACCENT)
    c.drawRightString(x1, 10.5 * mm, str(idx))
    c.showPage(); plan.append(idx)
c.save(); buf.seek(0)
overlay = PdfReader(buf)
for k, idx in enumerate(plan):
    w.pages[idx].merge_page(overlay.pages[k])
stamped = len([i for i in plan if i not in part_pages])
print('pages stamped with running header/footer:', stamped)
w.set_page_label(0, 0, prefix='Cover')
w.set_page_label(1, n - 1, style='/D', start=1)
w.add_metadata({'/Title': 'LLM Training Flow Vol. 2 — Curriculum Review, Gap Register, Future Topics and Real-World FDE Projects',
                '/Subject': 'Verified gap analysis, 2026–2028 future topics, revised 16-week FDE track, 16 project briefs, templates and starter-kit guides. Facts as of 26 September 2026.',
                '/Keywords': 'LLM, curriculum, forward deployed engineer, FDE, gap register, projects'})
w.page_mode = '/UseOutlines'
w.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
with open(out + '.tmp', 'wb') as f: w.write(f)
import os, pikepdf
with pikepdf.open(out + '.tmp') as pdf:
    pdf.remove_unreferenced_resources()
    pdf.save(out, compress_streams=True, recompress_flate=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
os.remove(out + '.tmp')
print(f'final pages {n}; bookmarks {len(items)}; titles repaired {fixed}')
