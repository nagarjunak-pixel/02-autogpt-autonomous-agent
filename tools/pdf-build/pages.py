# Read part/chapter start pages from a pass's PDF outline -> tocPages.json
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))   # paths below are relative to this folder
import json, sys
from pypdf import PdfReader
pdf, out = sys.argv[1], sys.argv[2]
rep = json.load(open('out/build-report.json'))
r = PdfReader(pdf)
top = [x for x in r.outline if not isinstance(x, list)]
nested = {}
i = 0
seq = r.outline
for idx, it in enumerate(seq):
    if not isinstance(it, list):
        kids = seq[idx+1] if idx+1 < len(seq) and isinstance(seq[idx+1], list) else []
        nested[len(nested)] = (it, [k for k in kids if not isinstance(k, list)])
parts = [v for v in nested.values() if v[0].title.strip() in {p['title'] for p in rep['parts']}]
assert len(parts) == len(rep['parts']), (len(parts), [v[0].title for v in nested.values()])
pages = {}
chapters = iter(rep['chapters'])
for (part_item, kids), p in zip(parts, rep['parts']):
    pages[p['id']] = r.get_destination_page_number(part_item) + 1
    assert len(kids) == p['files'], (p['id'], len(kids), p['files'])
    for k in kids:
        ch = next(chapters)
        pages[ch['id']] = r.get_destination_page_number(k) + 1
json.dump(pages, open(out, 'w'), indent=1)
print('pages for', len(pages), 'entries; last chapter starts p', max(pages.values()), 'of', len(r.pages))
