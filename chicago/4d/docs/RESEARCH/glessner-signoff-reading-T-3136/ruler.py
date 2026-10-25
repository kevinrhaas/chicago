"""Stack the photo and render strips of a side-by-side for rows y0-y1, cols x0-x1, zoomed, with a tick ruler (panel px)."""
import sys
from PIL import Image, ImageOps, ImageDraw
f, out, y0, y1, x0, x1, z = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:8])
im = Image.open(f).convert('L'); W = im.width // 2
strips = []
for k in (0, 1):
    s = im.crop((k*W + x0, y0, k*W + x1, y1))
    s = ImageOps.equalize(s) if k == 0 else ImageOps.autocontrast(s)
    strips.append(s.resize(((x1-x0)*z, (y1-y0)*z), Image.NEAREST))
h = (y1-y0)*z; c = Image.new('L', ((x1-x0)*z, 2*h + 60), 255); d = ImageDraw.Draw(c)
c.paste(strips[0], (0, 0)); c.paste(strips[1], (0, h + 60))
for x in range(x0 - x0 % 10, x1, 10):
    X = (x - x0)*z
    if X < 0: continue
    L = 22 if x % 50 == 0 else 10
    d.line([(X, h), (X, h + L)], fill=0); d.line([(X, h+60-L), (X, h+60)], fill=0)
    if x % 50 == 0: d.text((X + 2, h + 24), str(x), fill=0)
c.save(out, quality=90)
