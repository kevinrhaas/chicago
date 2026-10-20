# T-2926: native HABS sheet 4 (top) over the habs04-court-exterior render (bottom), at the same
# scale and with the same grid of S (red, sheet 4's own frame) and height above north grade (blue),
# so a line can be followed straight down from the drawing to the render. Run from chicago/:
#   python3 4d/docs/RESEARCH/glessner-court-face-T-2926/native_over_render.py \
#       prairie_1904_v1/research/public/glessner-habs-sheet-4.png <render.png> out.jpg S0 S1 Z0 Z1 [scale]
# The render is photo_match.mjs's, whose camera frames native crop [3770,1500,8600,5950] at
# 1600x1518 (data/reference_views/glessner_house/habs04-court-exterior.json); T-2228's section
# controls: north wall x 1165, grade y 5858, 100.6 / 97.7 px per ft.
import math, sys
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None
NX, GY, PX, PY = 1165, 5858, 100.6, 97.7
CX0, CY0, CX1, CY1, RW, RH = 3770, 1500, 8600, 5950, 1600, 1518
src, render, out = sys.argv[1:4]
s0, s1, z0, z1 = map(float, sys.argv[4:8])
scale = float(sys.argv[8]) if len(sys.argv) > 8 else 1.0
x0, x1, y0, y1 = int(NX + s0 * PX), int(NX + s1 * PX), int(GY - z1 * PY), int(GY - z0 * PY)
w, h = int((x1 - x0) * scale), int((y1 - y0) * scale)
top = Image.open(src).crop((x0, y0, x1, y1)).convert('RGB').resize((w, h))
fx, fy = RW / (CX1 - CX0), RH / (CY1 - CY0)
bottom = Image.open(render).convert('RGB').crop(((x0 - CX0) * fx, (y0 - CY0) * fy, (x1 - CX0) * fx, (y1 - CY0) * fy)).resize((w, h), Image.LANCZOS)


def grid(im):
    d = ImageDraw.Draw(im)
    s = math.ceil(s0)
    while s <= s1:
        x = (NX + s * PX - x0) * scale
        d.line([(x, 0), (x, h)], fill=(255, 0, 0), width=1)
        d.text((x + 2, 2), f"{s:.0f}", fill=(255, 0, 0))
        s += 1
    z = math.ceil(z0)
    while z <= z1:
        y = (GY - z * PY - y0) * scale
        d.line([(0, y), (w, y)], fill=(0, 0, 255), width=1)
        d.text((2, y + 2), f"{z:.0f}", fill=(0, 0, 255))
        z += 1


grid(top); grid(bottom)
im = Image.new('RGB', (w, 2 * h + 8), 'white')
im.paste(top, (0, 0)); im.paste(bottom, (0, h + 8))
im.save(out, quality=88)
print(im.size)
