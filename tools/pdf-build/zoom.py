"""Render part of a page of the final PDF at high resolution, for close inspection.
Usage: python3 zoom.py PAGE [x0 y0 x1 y1] [SCALE]   (fractions of the page, default the whole page; scale default 3)
Writes png/zoom/pPAGE_x0-y0-x1-y1.png and prints the path. PAGE is the 0-based page index of the finished PDF: 0 is the cover, so it equals the printed page number."""
import sys, os, pypdfium2 as pdfium
HERE = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[1:]; page = int(a[0])
box = [float(x) for x in a[1:5]] if len(a) >= 5 else [0, 0, 1, 1]
scale = float(a[5]) if len(a) >= 6 else (float(a[1]) if len(a) == 2 else 3.0)
d = pdfium.PdfDocument(os.environ.get('OUT_PDF', os.path.join(HERE, 'dist', 'LLM-Training-Flow-Vol2-Curriculum-and-FDE-Projects.pdf')))
img = d[page].render(scale=scale).to_pil(); w, h = img.size
crop = img.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
os.makedirs(os.path.join(HERE, 'png', 'zoom'), exist_ok=True)
out = os.path.join(HERE, 'png', 'zoom', f"p{page:03d}_{'-'.join(f'{x:g}' for x in box)}_s{scale:g}.png")
crop.save(out); print(out)
