"""Recreate the font files in this folder from the upstream releases (all SIL Open Font License 1.1).

- Inter 4.1 (full release, not the web subset): the lowercase l is remapped to its tailed alternate (the cv05
  feature), because Chromium ignores font-feature-settings in @font-face and an untailed l looks like a capital I
  ('lm-evaluation-harness' read as 'Im-…').
- Source Serif 4.005 and JetBrains Mono 2.304: used only for the arrows and maths signs the web subsets lack.

DejaVuSans.ttf is copied unchanged from DejaVu Fonts 2.37 (Bitstream Vera licence; see LICENSE-DejaVu.txt).

Usage: python3 fonts/prepare_fonts.py [DIR_WITH_ZIPS]   (downloads the zips when no directory is given)
"""
import hashlib, io, os, sys, urllib.request, zipfile
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
RELEASES = {
    'inter.zip': 'https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip',
    'ss4.zip': 'https://github.com/adobe-fonts/source-serif/releases/download/4.005R/source-serif-4.005_Desktop.zip',
    'jbm.zip': 'https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip',
}
# SHA-256 of the release zips and of the files this script writes (produced with fontTools 4.66)
ZIP_SHA256 = {'inter.zip': '9883fdd4a49d4fb66bd8177ba6625ef9a64aa45899767dde3d36aa425756b11e', 'ss4.zip': '549fdb8f9a682bd06944298621404969f6de77c2e422ff3b8244a1dcd6a0c425', 'jbm.zip': '6f6376c6ed2960ea8a963cd7387ec9d76e3f629125bc33d1fdcd7eb7012f7bbf'}
OUT_SHA256 = {'Inter-400.ttf': '2449c7fe15d4f17428651dbac52bcea91c3ced2071f313c3083707cf8529b7b6', 'Inter-600.ttf': '1d98d7ace6cda5106b07264b122adc17452499be02f025c77b4fdb7526a2a03e', 'Inter-700.ttf': '597e7099bf4adb5a9be587a3d88eda5da8760deee4b61b5e2adc4fc1d6fb5066', 'JetBrainsMono-Regular.ttf': 'a0bf60ef0f83c5ed4d7a75d45838548b1f6873372dfac88f71804491898d138f', 'SourceSerif4-It.ttf': '9d2950a8f1da66e21502c35d646a1d2148e79f9ea43fd2158cf02f5232e7f430', 'SourceSerif4-Regular.ttf': 'e5a4ee6a3d87bb9024796be390c6771e2a0eb1883dae25effaf57ca01668e24b', 'SourceSerif4-Semibold.ttf': '36db62940cb5728b12b1802476dc7fcf4c6c519a7bdd476ba23a4e555fc4655f', 'SourceSerif4-SemiboldIt.ttf': 'd6a0a4317102a255a55850640332ba3acc7c872606a555516b4ecdb66f3c9899'}
FILES = {  # output name: (zip, member)
    'Inter-400.ttf': ('inter.zip', 'extras/ttf/Inter-Regular.ttf'),
    'Inter-600.ttf': ('inter.zip', 'extras/ttf/Inter-SemiBold.ttf'),
    'Inter-700.ttf': ('inter.zip', 'extras/ttf/Inter-Bold.ttf'),
    'SourceSerif4-Regular.ttf': ('ss4.zip', 'source-serif-4.005_Desktop/TTF/SourceSerif4-Regular.ttf'),
    'SourceSerif4-It.ttf': ('ss4.zip', 'source-serif-4.005_Desktop/TTF/SourceSerif4-It.ttf'),
    'SourceSerif4-Semibold.ttf': ('ss4.zip', 'source-serif-4.005_Desktop/TTF/SourceSerif4-Semibold.ttf'),
    'SourceSerif4-SemiboldIt.ttf': ('ss4.zip', 'source-serif-4.005_Desktop/TTF/SourceSerif4-SemiboldIt.ttf'),
    'JetBrainsMono-Regular.ttf': ('jbm.zip', 'fonts/ttf/JetBrainsMono-Regular.ttf'),
}


def zips(src):
    out = {}
    for name, url in RELEASES.items():
        data = open(os.path.join(src, name), 'rb').read() if src else urllib.request.urlopen(url).read()
        if hashlib.sha256(data).hexdigest() != ZIP_SHA256[name]:
            raise SystemExit(f'{name}: checksum mismatch, the release file changed')
        out[name] = zipfile.ZipFile(io.BytesIO(data))
    return out


def tailed_l(font):
    """Point U+006C at the glyph the cv05 feature substitutes for 'l'."""
    gsub = font['GSUB'].table
    lookups = [i for fr in gsub.FeatureList.FeatureRecord if fr.FeatureTag == 'cv05' for i in fr.Feature.LookupListIndex]
    for i in lookups:
        for st in gsub.LookupList.Lookup[i].SubTable:
            m = getattr(st, 'mapping', None) or getattr(getattr(st, 'ExtSubTable', None), 'mapping', None) or {}
            if 'l' in m:
                for t in font['cmap'].tables:
                    if t.isUnicode() and 0x6C in t.cmap:
                        t.cmap[0x6C] = m['l']
                return m['l']
    raise SystemExit('cv05 alternate for l not found')


if __name__ == '__main__':
    zs = zips(sys.argv[1] if len(sys.argv) > 1 else None)
    for out, (z, member) in FILES.items():
        member = next(n for n in zs[z].namelist() if n.endswith(member))
        data = zs[z].read(member)
        if out.startswith('Inter-'):
            f = TTFont(io.BytesIO(data), recalcTimestamp=False); tailed_l(f); f.save(os.path.join(HERE, out))
        else:
            open(os.path.join(HERE, out), 'wb').write(data)
        ok = hashlib.sha256(open(os.path.join(HERE, out), 'rb').read()).hexdigest() == OUT_SHA256[out]
        print('wrote', out, '(matches the committed file)' if ok else '(DIFFERS from the committed file: check the fontTools version)')
