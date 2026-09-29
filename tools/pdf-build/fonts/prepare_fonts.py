"""Recreate the font files in this folder from the upstream releases (all SIL Open Font License 1.1).

- Inter 4.1 (full release, not the web subset): the lowercase l is remapped to its tailed alternate (the cv05
  feature), because Chromium ignores font-feature-settings in @font-face and an untailed l looks like a capital I
  ('lm-evaluation-harness' read as 'Im-…').
- Source Serif 4.005 and JetBrains Mono 2.304: used only for the arrows and maths signs the web subsets lack.

Usage: python3 fonts/prepare_fonts.py [DIR_WITH_ZIPS]   (downloads the zips when no directory is given)
"""
import io, os, sys, urllib.request, zipfile
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
RELEASES = {
    'inter.zip': 'https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip',
    'ss4.zip': 'https://github.com/adobe-fonts/source-serif/releases/download/4.005R/source-serif-4.005_Desktop.zip',
    'jbm.zip': 'https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip',
}
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
        print('wrote', out)
