import json, re, sys, pypdfium2 as pdfium
from pypdf import PdfReader
import os as _os
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)))   # paths below are relative to this folder
F = _os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else None
F = F or 'dist/LLM-Training-Flow-Vol2-Curriculum-and-FDE-Projects.pdf'
r = PdfReader(F); named = r.named_destinations
internal = external = broken = 0
for p in r.pages:
    for a in p.get('/Annots') or []:
        a = a.get_object()
        if a.get('/Subtype') != '/Link': continue
        act = a.get('/A'); dest = a.get('/Dest')
        if act is not None:
            act = act.get_object()
            if act.get('/S') == '/URI': external += 1; continue
            dest = act.get('/D')
        internal += 1
        nd = named.get(str(dest)) if dest is not None else None
        try: ok = nd is not None and r.get_destination_page_number(nd) is not None
        except Exception: ok = False
        broken += (not ok)
# text checks read the unstamped main PDF (running headers would pollute them); index 0 stands in for the cover
pdf = pdfium.PdfDocument(F)
_main = pdfium.PdfDocument('out/main-pass2.pdf')
texts = [''] + [_main[i].get_textpage().get_text_range() for i in range(len(_main))]
json.dump(texts, open('out/final-page-texts.json', 'w'))
rep = json.load(open('out/build-report.json')); toc = json.load(open('out/toc2.json'))
starts = sorted((toc[c['id']], c) for c in rep['chapters']); parts = set(toc[p['id']] for p in rep['parts'])
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..')) + '/'; FENCE_LANGS = {'bash', 'python', 'json', 'yaml', 'text', 'typescript', 'http', 'sql', 'markdown', 'jsonl', 'cobol', 'diff', 'mermaid'}
miss_all = []
for k, (start, ch) in enumerate(starts):
    end = starts[k + 1][0] if k + 1 < len(starts) else len(pdf)
    pt = ' '.join(texts[i] for i in range(start, end) if i not in parts)
    src = re.sub(r'```mermaid.*?```', '', open(REPO + ch['file']).read(), flags=re.S)
    src = re.sub(r'\]\([^)]*\)', ']', src)
    langs = set(re.findall(r'^\s*```(\w+)', src, flags=re.M))
    words = {w.lower() for w in re.findall(r'[A-Za-z][A-Za-z0-9]{3,}', src)} - {l.lower() for l in langs}
    flat = re.sub(r'\s+', '', pt).lower()
    pw = {w.lower() for w in re.findall(r'[A-Za-z][A-Za-z0-9]{3,}', pt)}
    miss = sorted(w for w in words if w not in pw and w not in flat)
    if miss: miss_all.append((ch['file'], miss))
print(f"pages {len(pdf)} | internal links {internal} broken {broken} | external {external} | chapters with missing words {len(miss_all)}")
for f, m in miss_all: print('  ', f, m[:10])
print('escaped pipes', rep.get('escapedPipes'), '| mermaid', rep['mermaidRendered'], '/', rep['mermaidInSource'], 'errors', rep['mermaidErrors'], '| problems', rep['problems'])
# stranded headings / label paragraphs: page text (before the footer) ends with a heading or lead
heads = json.load(open('out/headings-pass2.json')); leads = json.load(open('out/leads-pass2.json'))
import unicodedata
nz = lambda s: re.sub(r'\s+', '', unicodedata.normalize('NFKC', s))
targets = sorted({nz(h) for h in heads + leads if len(nz(h)) >= 4}, key=len, reverse=True)
stranded = []
for i, t in enumerate(texts):
    if i in parts or i in (0, 1, 2, 3): continue   # part dividers list chapter titles by design; cover/front matter
    body = t
    tail = nz(body)[-300:]
    for h in targets:
        if tail.endswith(h): stranded.append((i, h[:70])); break
print(f'stranded headings/labels at page bottom: {len(stranded)}')
for s in stranded[:40]: print('  p%d %s' % s)
lay = rep.get('layout', {})
print('diagrams (chapter, orientation, label pt):')
for d in lay.get('diagrams', []): print('  ', d['chapter'], d['orient'], d['labelPt'], f"{d['w']}x{d['h']}")
print('overflowing tables:', lay.get('tableOverflow'))
print('broken ordinary words in cells:', len(lay.get('brokenOrdinary', [])), lay.get('brokenOrdinary', [])[:20])
print('broken long tokens in cells:', lay.get('brokenLong'), lay.get('brokenLongSamples', [])[:8])
print('label breaks inserted:', rep.get('labelBreaks'))

# widows and orphans: a page that starts with only the last line of a block, or ends with only its first line
blocks = json.load(open('out/blocklines-pass2.json'))
nzz = lambda x: re.sub(r'\s+', '', x)
lasts, firsts = {}, {}
for b in blocks:
    if len(nzz(b['last'])) >= 6: lasts.setdefault(nzz(b['last']), []).append(b)
    if len(nzz(b['first'])) >= 6: firsts.setdefault(nzz(b['first']), []).append(b)
widows, orphans = [], []
for i, t in enumerate(texts):
    if i in parts or i < 4: continue
    ls = [nzz(l) for l in t.splitlines() if l.strip()]
    if len(ls) < 2: continue
    if ls[0] in lasts and all(nzz(b['first']) not in ls for b in lasts[ls[0]]): widows.append((i, t.splitlines()[0][:70]))
    if ls[-1] in firsts and all(nzz(b['last']) not in ls for b in firsts[ls[-1]]): orphans.append((i, [l for l in t.splitlines() if l.strip()][-1][:70]))
print(f'widows (one line carried to the next page): {len(widows)}'); [print('  p%d %s' % w) for w in widows[:30]]
print(f'orphans (one line left at the page foot): {len(orphans)}'); [print('  p%d %s' % o) for o in orphans[:30]]
# runover pages: the last page of a chapter holds only a line or two
runover = []
for k, (start, ch) in enumerate(starts):
    end = starts[k + 1][0] if k + 1 < len(starts) else len(texts)
    last = end - 1
    while last in parts: last -= 1
    if last > start:
        n = len([l for l in texts[last].splitlines() if l.strip()])
        if n <= 3: runover.append((last, n, ch['file'].split('/')[-1]))
print(f'chapter-end runover pages (<= 3 lines): {len(runover)}', runover[:20])
chap_starts = {s for s, _ in starts}
spill = sorted(pp for pp in parts if pp + 1 not in chap_starts)
print(f'part dividers that spill onto a second page: {len(spill)}', spill)

print('build loop:', json.load(open('out/loop-report.json')) if __import__('os').path.exists('out/loop-report.json') else 'n/a')

# every check above must be clean; 'broken long tokens' (long hyphenated or code tokens wrapping in a cell) is informational
failures = {
    'broken internal links': broken, 'chapters with missing words': len(miss_all),
    'diagrams not rendered': rep['mermaidInSource'] - rep['mermaidRendered'], 'diagram errors': len(rep['mermaidErrors']),
    'build problems': len(rep['problems']), 'overflowing tables': len(lay.get('tableOverflow') or []),
    'broken ordinary words in cells': len(lay.get('brokenOrdinary', [])), 'stranded headings': len(stranded),
    'widows': len(widows), 'orphans': len(orphans), 'chapter-end runover pages': len(runover), 'part dividers that spill': len(spill),
}
bad = {k: v for k, v in failures.items() if v}
print(f"browser: {rep.get('browser', 'unknown')}")
print('CHECKS PASSED' if not bad else 'CHECKS FAILED: ' + ', '.join(f'{k} {v}' for k, v in bad.items()))
sys.exit(1 if bad else 0)
