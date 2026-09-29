"""Build passes until the page numbers are stable and no heading or lead-in is stranded at a page foot.

Pass 1 renders with placeholder page numbers. Each later pass renders with the previous pass's page numbers and with
forced page breaks before any heading chain that the previous pass left stranded. The final pass's files are copied
to the *-pass2 names that finalize.py and verify.py read.
Usage: COMMIT=<sha> python3 build_loop.py
"""
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))   # paths below are relative to this folder
import json, os, re, shutil, subprocess, sys, unicodedata
import pypdfium2 as pdfium

OUT = 'out'
nz = lambda s: re.sub(r'\s+', '', unicodedata.normalize('NFKC', s))


def run(*cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'{" ".join(cmd)} failed:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}')
    return r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''


def stranded(k):
    """Headings or lead-ins whose text ends a page (part dividers and front matter excluded)."""
    heads = json.load(open(f'{OUT}/headings-pass{k}.json'))
    leads = json.load(open(f'{OUT}/leads-pass{k}.json'))
    toc = json.load(open(f'{OUT}/toc{k}.json'))
    rep = json.load(open(f'{OUT}/build-report.json'))
    parts = {toc[p['id']] for p in rep['parts']}
    first = min(parts)
    targets = sorted({t for t in heads + leads if len(nz(t)) >= 4}, key=lambda t: -len(nz(t)))
    doc = pdfium.PdfDocument(f'{OUT}/main-pass{k}.pdf')
    found = []
    for j in range(len(doc)):
        page = j + 1                                   # final page index (the cover comes first)
        if page < first or page in parts:
            continue
        tail = nz(doc[j].get_textpage().get_text_range())[-400:]
        for t in targets:
            if tail.endswith(nz(t)):
                found.append((page, t))
                break
    return found


def runover(k):
    """Chapters whose last page holds six text lines or fewer."""
    rep = json.load(open(f'{OUT}/build-report.json')); toc = json.load(open(f'{OUT}/toc{k}.json'))
    starts = sorted((toc[c['id']], c['id']) for c in rep['chapters']); parts = {toc[p['id']] for p in rep['parts']}
    doc = pdfium.PdfDocument(f'{OUT}/main-pass{k}.pdf'); out = []
    for i, (start, cid) in enumerate(starts):
        last = (starts[i + 1][0] if i + 1 < len(starts) else len(doc) + 1) - 1
        while last in parts: last -= 1
        if last > start and len([l for l in doc[last - 1].get_textpage().get_text_range().splitlines() if l.strip()]) <= 6:
            out.append(cid)
    return out


tight = {}
for f in ('breaks.json', 'tight.json'):
    if os.path.exists(f'{OUT}/{f}'):
        os.remove(f'{OUT}/{f}')
print(run('node', 'build.mjs', '1'))
print(run('python3', 'pages.py', f'{OUT}/main-pass1.pdf', f'{OUT}/toc1.json'))
breaks, prev, final = [], f'{OUT}/toc1.json', None
for k in range(2, 9):
    json.dump(breaks, open(f'{OUT}/breaks.json', 'w'), ensure_ascii=False)
    print(run('node', 'build.mjs', str(k), prev))
    print(run('python3', 'pages.py', f'{OUT}/main-pass{k}.pdf', f'{OUT}/toc{k}.json'))
    stable = json.load(open(prev)) == json.load(open(f'{OUT}/toc{k}.json'))
    found = stranded(k)
    new = [t for _, t in found if t not in breaks]
    print(f'pass {k}: page numbers {"stable" if stable else "shifted"}; stranded {len(found)} ({len(new)} new)'
          + ''.join(f'\n   p{p}: {t[:80]}' for p, t in found))
    short = [c for c in runover(k) if tight.get(c, 0) < 2] if stable and not new else []
    if short:
        for c in short: tight[c] = tight.get(c, 0) + 1
        json.dump(tight, open(f'{OUT}/tight.json', 'w'))
        print(f'pass {k}: chapters whose last page holds six or fewer lines set tighter: {[(c, tight[c]) for c in short]}')
    elif stable and not new:
        final = k
        break
    breaks += new
    prev = f'{OUT}/toc{k}.json'
if final is None:
    sys.exit('did not converge in 8 passes')
if final != 2:
    for stem in ('main-pass{}.pdf', 'headings-pass{}.json', 'leads-pass{}.json', 'bookmarks-pass{}.json',
                 'blocklines-pass{}.json', 'book-pass{}.html', 'toc{}.json'):
        shutil.copy(f'{OUT}/{stem.format(final)}', f'{OUT}/{stem.format(2)}')
json.dump({'final_pass': final, 'forced_breaks': breaks, 'tight': tight,
           'still_stranded': [{'page': p, 'text': t} for p, t in stranded(2)]},
          open(f'{OUT}/loop-report.json', 'w'), indent=1, ensure_ascii=False)
print(f'converged at pass {final}; forced breaks: {len(breaks)}')
