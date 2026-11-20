#!/usr/bin/env python3
"""Portable 1871 context forms and original facade maps, without Blender.

python3 generators/city_context_emit.py          # writes kit.glb + kit.json
python3 generators/city_context_emit.py --check  # reproduce and compare every byte

Inputs are the adjacent explicit recipe and this generator. The shared GLB has
one textured material and two meshes per family: individual facade bays nearby,
four walls carrying the same facade atlas at a distance. Neither tier is an
identified historic building. All vertices carry reconstructed confidence.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import random
import struct
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "data/context/1871"
RECIPE = FOLDER / "kit-recipe.json"
sys.path.insert(0, str(ROOT / "tools"))
from compile_scene import cite  # shared source names, URLs, evidence ladder and limits


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def png(image):
    stream = io.BytesIO()
    image.save(stream, "PNG", optimize=False, compress_level=9)
    return stream.getvalue()


def italianate_window(d, h, p, tile, family, rect):
    """T-3686: a tall two-over-two sash under a segmental stone hood and on a sill.

    The pre-fire views (Carbutt's Lake Street and Clark Street rows) show this
    window on almost every brick and stone front; the hood and sill are the
    K09 hood block's and K06 sill's proportions at the cell's scale.
    """
    a, b, c, e = rect
    stone = (204, 194, 168) if family == "brick" else (190, 181, 156)
    shade = (88, 80, 66)
    rise = max(3, (c - a) // 6)
    # Segmental head of the opening: glass under the arc, wall above it.
    d.rectangle((a - 3, b - 1, c + 3, e + 2), fill=(70, 62, 50))
    d.pieslice((a - 3, b - rise, c + 3, b + rise), 180, 360, fill=(70, 62, 50))
    d.rectangle((a, b, c, e), fill=(38, 44, 44))
    d.pieslice((a, b - rise + 2, c, b + rise + 2), 180, 360, fill=(38, 44, 44))
    sash = (226, 220, 204)
    mid = (b + e) // 2
    for x in (a, (a + c) // 2, c):
        d.line((x, b - rise // 2, x, e), fill=sash, width=2)
    d.line((a, mid, c, mid), fill=sash, width=3)
    d.line((a, e, c, e), fill=sash, width=2)
    d.rectangle((a + 3, b + 2, (a + c) // 2 - 2, mid - 3), fill=(62, 74, 76))
    # The hood: an arched band of dressed stone with a keystone, 0.12 m proud.
    d.arc((a - 9, b - rise - 7, c + 9, b + rise + 3), 180, 360, fill=stone, width=6)
    d.rectangle((a - 9, b - 1, a - 3, b + 3), fill=stone)
    d.rectangle((c + 3, b - 1, c + 9, b + 3), fill=stone)
    k = (a + c) // 2
    d.rectangle((k - 4, b - rise - 8, k + 4, b - rise + 2), fill=stone)
    d.line((a - 8, b + 4, c + 8, b + 4), fill=shade, width=1)
    h.arc((a - 9, b - rise - 7, c + 9, b + rise + 3), 180, 360, fill=168, width=6)
    # The sill, projecting with its shadow beneath.
    d.rectangle((a - 7, e + 2, c + 7, e + 6), fill=stone)
    d.line((a - 6, e + 7, c + 6, e + 7), fill=shade, width=2)
    h.rectangle((a - 7, e + 2, c + 7, e + 6), fill=160)
    h.rectangle((a, b, c, e), fill=72)
    p.rectangle((a, b, c, e), fill=(202, 82, 0))


def italianate_shop(d, h, p, tile, rand):
    """T-3686: one bay of a cast-iron shop front, as the stereographs show it:
    painted iron pilasters, a plate-glass light over a panelled bulkhead, and a
    sign band with lettering above. The lettering here is only a texture of
    strokes at this distance; the detail ring carries the painted signboards."""
    iron = (196, 190, 174)
    d.rectangle((0, 0, tile, tile), fill=iron)
    band = (0, round(tile * .03), tile, round(tile * .19))
    d.rectangle(band, fill=(46, 52, 44))
    x = 10
    while x < tile - 14:
        w = rand.randint(4, 9)
        d.rectangle((x, band[1] + 6, x + w, band[3] - 6), fill=(214, 198, 150))
        x += w + rand.randint(3, 6)
    d.line((0, band[3] + 1, tile, band[3] + 1), fill=(120, 112, 96), width=3)
    g0, g1 = round(tile * .24), round(tile * .82)
    d.rectangle((9, g0, tile - 10, g1), fill=(36, 42, 43))
    d.rectangle((13, g0 + 4, tile // 2 - 6, (g0 + g1) // 2), fill=(58, 70, 72))
    d.line((tile // 2, g0, tile // 2, g1), fill=iron, width=3)
    d.rectangle((9, g1 + 2, tile - 10, tile - 3), fill=(176, 168, 150))
    for q in (16, tile // 2 + 6):
        d.rectangle((q, g1 + 6, q + tile // 2 - 26, tile - 8), outline=(140, 132, 116))
    for q in (0, tile - 9):
        d.rectangle((q, g0 - 4, q + 8, tile), fill=(206, 200, 184))
        d.line((q + 4, g0, q + 4, tile - 4), fill=(150, 144, 130), width=1)
    h.rectangle((9, g0, tile - 10, g1), fill=70)
    h.rectangle((band[0], band[1], band[2], band[3]), fill=140)
    p.rectangle((9, g0, tile - 10, g1), fill=(210, 60, 0))


def make_atlas(recipe):
    """8x8 cells: material rows; wall, window, door, shop, loading and trim cells.

    Maps are original procedural illustrations, not photographs or evidence.
    Margins repeat the cell edge so mip filtering cannot borrow another facade.
    """
    size = recipe["texture_size"]
    tile = size // 8
    color = Image.new("RGB", (size, size), (125, 119, 106))
    height = Image.new("L", (size, size), 128)
    orm = Image.new("RGB", (size, size), (255, 235, 0))
    # T-3683: frame walls are painted weatherboard, pale enough for each
    # house's own paint (city-context.js) to tint; the old buff was a near
    # match for the stone row and read as stone at any distance.
    # T-3686: the masonry rows are tinted per building in city-context.js
    # (red, brown or salmon brick; cream "Athens marble", buff Joliet stone or
    # painted brick), so the stone cell is a pale cream (the Lemont stone, K02,
    # textures/prairie_1904_stone/limestone_lemont, as it read new and washed in
    # the pre-fire views) and brick is laid in pale lime mortar as the 1835
    # library's brick is. The detail ring's walls are those textures; kit.json
    # fronts.materials[].match carries the tint that makes them meet these rows.
    families = {"brick": (160, 108, 84), "timber": (228, 223, 209),
                "stone": (192, 184, 162), "weathered": (123, 113, 94)}
    slots = {}
    rand = random.Random(18711008)
    for row, (family, base) in enumerate(families.items()):
        for col, kind in enumerate(("wall", "window", "door", "shop", "loading", "trim")):
            x0, y0 = col * tile, row * tile
            im = Image.new("RGB", (tile, tile), base)
            relief = Image.new("L", (tile, tile), 128)
            surface = Image.new("RGB", (tile, tile), (250, 237, 0))
            d, h, p = ImageDraw.Draw(im), ImageDraw.Draw(relief), ImageDraw.Draw(surface)
            if family in ("brick", "stone"):
                course = 4 if family == "brick" else 12
                unit = 12 if family == "brick" else 28
                d.rectangle((0, 0, tile, tile), fill=(176, 166, 144) if family == "brick" else (136, 128, 108))
                h.rectangle((0, 0, tile, tile), fill=113)
                for y in range(-course, tile + course, course):
                    offset = (unit // 2) * ((y // course) % 2)
                    for x in range(-unit, tile + unit, unit):
                        light = rand.randint(-12, 10)
                        tone = tuple(max(0, min(255, v + light)) for v in base)
                        rect = (x + offset + 1, y + 1, x + offset + unit - 1, y + course - 1)
                        d.rectangle(rect, fill=tone)
                        h.rectangle(rect, fill=128 + rand.randint(-2, 2))
            else:
                # Lapped weatherboards: about 0.13 m to the course on a
                # 3 m storey tile (painted frame); sheds keep wider boards.
                board = 6 if family == "timber" else 9
                for y in range(0, tile, board):
                    v = rand.randint(-5, 5) if family == "timber" else rand.randint(-8, 8)
                    d.rectangle((0, y, tile, y + board - 1), fill=tuple(max(0, min(255, c + v)) for c in base))
                    d.line((0, y + board - 1, tile, y + board - 1), fill=tuple(int(c * .66) for c in base))
                    h.line((0, y + board - 1, tile, y + board - 1), fill=104)
            if kind in ("window", "door", "shop", "loading"):
                rect = {"window": (.29, .20, .71, .78), "door": (.29, .24, .71, 1.0),
                        "shop": (.12, .20, .88, .91), "loading": (.15, .22, .85, 1.0)}[kind]
                a, b, c, e = [round(v * tile) for v in rect]
                frame = (192, 178, 146) if family in ("brick", "stone") else (241, 238, 228) if family == "timber" else (208, 197, 165)
                d.rectangle((a - 4, b - 4, c + 4, e + 3), fill=(73, 65, 53))
                d.rectangle((a - 2, b - 3, c + 3, e + 1), fill=frame)
                d.rectangle((a, b, c, e), fill=(40, 48, 46))
                h.rectangle((a - 4, b - 4, c + 4, e + 3), fill=151)
                h.rectangle((a, b, c, e), fill=72)
                p.rectangle((a, b, c, e), fill=(202, 82, 0))
                if kind in ("door", "loading"):
                    d.rectangle((a + 2, b + tile // 5, c - 2, e), fill=(78, 66, 50))
                    for q in (a + 6, (a + c) // 2, c - 6):
                        d.line((q, b + tile // 5, q, e), fill=(110, 91, 66), width=2)
                    p.rectangle((a, b + tile // 5, c, e), fill=(232, 223, 0))
                elif kind == "shop" and family in ("brick", "stone"):
                    italianate_shop(d, h, p, tile, rand)
                elif kind == "window" and family in ("brick", "stone"):
                    italianate_window(d, h, p, tile, family, (a, b, c, e))
                else:
                    d.rectangle((a + 2, b + 2, c - 2, (b + e) // 2), fill=(65, 78, 78))
                    d.line(((a + c) // 2, b, (a + c) // 2, e), fill=frame, width=2)
                    d.line((a, (b + e) // 2, c, (b + e) // 2), fill=frame, width=2)
                    if kind == "shop":
                        d.rectangle((a - 3, b - 12, c + 3, b - 5), fill=(66, 60, 48))
                    d.line((a - 5, e + 3, c + 5, e + 3), fill=(206, 190, 155), width=3)
            elif kind == "trim":
                d.rectangle((0, 0, tile, tile), fill=tuple(min(255, int(c * 1.10)) for c in base))
            # Reserve a four-pixel gutter in each UV rectangle, replicated outward.
            for target, source in ((color, im), (height, relief), (orm, surface)):
                target.paste(source, (x0, y0))
            slots[f"{family}_{kind}"] = (col, row)
    # Slate, wood shingles and an opaque dark roof/iron surface use dedicated cells.
    for col, (name, base, step) in enumerate((("slate", (66, 71, 69), 14),
                                            ("shingle", (102, 94, 76), 12),
                                            ("dark", (62, 59, 51), 32))):
        x0, y0 = col * tile, 4 * tile
        d, h = ImageDraw.Draw(color), ImageDraw.Draw(height)
        d.rectangle((x0, y0, x0 + tile - 1, y0 + tile - 1), fill=base)
        for y in range(0, tile, step):
            d.line((x0, y0 + y, x0 + tile - 1, y0 + y), fill=tuple(max(0, c - 15) for c in base))
            h.line((x0, y0 + y, x0 + tile - 1, y0 + y), fill=108)
            for x in range((y // step % 2) * 9, tile, 19):
                d.line((x0 + x, y0 + y, x0 + x, min(y0 + tile - 1, y0 + y + step)), fill=tuple(c + 6 for c in base))
        slots[name] = (col, 4)
    # Far silhouettes retain the actual number of storeys/bays in a single
    # textured face. They never turn a five-storey block into one giant window.
    free = [(x, y) for y in range(8) for x in range(8) if (x, y) not in slots.values()]
    for t in recipe["templates"]:
        for face, bays in (("front", t["front_bays"]), ("side", t["side_bays"])):
            col, row = free.pop(0)
            cell = "window"
            for atlas in (color, height, orm):
                source_col, source_row = slots[f"{t['material']}_{cell}"]
                source = atlas.crop((source_col*tile,source_row*tile,(source_col+1)*tile,(source_row+1)*tile))
                composite = Image.new(atlas.mode, (tile*bays,tile*t["storeys"]))
                for floor in range(t["storeys"]):
                    for bay in range(bays): composite.paste(source,(bay*tile,floor*tile))
                atlas.paste(composite.resize((tile,tile),Image.Resampling.LANCZOS),(col*tile,row*tile))
            slots[f"{t['id']}_far_{face}"]=(col,row)
    for name, base in (("bark",(89,69,46)),("foliage_green",(83,103,55)),("foliage_ochre",(127,116,62))):
        col,row=free.pop(0); x0,y0=col*tile,row*tile
        d=ImageDraw.Draw(color)
        d.rectangle((x0,y0,x0+tile-1,y0+tile-1),fill=base)
        for _ in range(450):
            x,y=rand.randrange(tile),rand.randrange(tile)
            tone=tuple(max(0,min(255,c+rand.randint(-12,12))) for c in base)
            if name=="bark": d.line((x0+x,y0+y,x0+x,min(y0+tile-1,y0+y+12)),fill=tone)
            else: d.ellipse((x0+x,y0+y,min(x0+tile-1,x0+x+3),min(y0+tile-1,y0+y+3)),fill=tone)
        slots[name]=(col,row)
    # Height-derived normal: shallow mortar/clapboard relief and recess/frame edges.
    height = height.filter(ImageFilter.GaussianBlur(.55))
    pix = height.load()
    normal = Image.new("RGB", (size, size))
    out = normal.load()
    for y in range(size):
        for x in range(size):
            dx = (pix[min(x + 1, size - 1), y] - pix[max(x - 1, 0), y]) / 90
            dy = (pix[x, min(y + 1, size - 1)] - pix[x, max(y - 1, 0)]) / 90
            inv = 1 / math.sqrt(dx * dx + dy * dy + 1)
            out[x, y] = (round(127.5 * (1 - dx * inv)), round(127.5 * (1 + dy * inv)), round(127.5 * (1 + inv)))
    return [png(color), png(normal), png(orm)], slots


# ---------------------------------------------------------------------------
# T-3686: the detail ring's materials. Walls wear the project's own libraries:
# the 1835 town's brick and white-lead clapboard (textures/chicago_1835_pbr)
# and the 1904 kit's Lemont limestone (textures/prairie_1904_stone, K02), the
# local "Athens marble" of the pre-fire fronts. Painted brick is the 1835 brick
# under a coat of paint. The parts atlas holds the shop glass, doors, sash,
# cast iron, cornice, trim, signboards and awning canvas the renderer builds
# each front from (renderers/web/js/city-fronts.js).
FRONT_WALLS = {
    "brick": ("assets/textures/chicago_1835_pbr/masonry/chicago_clay_brick_lime_mortar/chicago_clay_brick_lime_mortar", 4.2),
    "stone": ("assets/textures/prairie_1904_stone/limestone_lemont/limestone_lemont", 1.2),
    "clapboard": ("assets/textures/chicago_1835_pbr/walls/clapboard_white_lead_paint/clapboard_white_lead_paint", 4.48),
}
FRONT_TRIM = "assets/textures/prairie_1904_stone/dressed_trim/dressed_trim_basecolor.png"
# Generic trade words, never a firm's name: no individual sign survives to letter.
# The trades come from signs legible in pre-fire views of Lake and Clark
# streets (CAPS & FURS, LITHOGRAPHY, TELEGRAPH, BOOK BINDER, JOB PRINTING)
# and the commonest trades of the business directories.
SIGN_WORDS = ["DRY GOODS", "CAPS & FURS", "BOOTS & SHOES", "HARDWARE", "CLOTHING", "DRUGS",
              "BOOK BINDER", "JEWELRY", "GROCERIES", "CROCKERY", "LITHOGRAPHY", "JOB PRINTING",
              "TELEGRAPH", "MILLINERY", "SADDLERY", "TEAS"]
# A plain stroke alphabet on a 4 x 6 grid (no font file, so the bytes are the
# same on every machine): each glyph is polylines of (x, y) grid points.
GLYPHS = {
    "A": [[(0,6),(0,2),(2,0),(4,2),(4,6)],[(0,3),(4,3)]], "B": [[(0,0),(0,6),(3,6),(4,5),(4,4),(3,3),(0,3)],[(0,0),(3,0),(4,1),(4,2),(3,3)]],
    "C": [[(4,0),(1,0),(0,1),(0,5),(1,6),(4,6)]], "D": [[(0,0),(0,6),(3,6),(4,5),(4,1),(3,0),(0,0)]],
    "E": [[(4,0),(0,0),(0,6),(4,6)],[(0,3),(3,3)]], "F": [[(4,0),(0,0),(0,6)],[(0,3),(3,3)]],
    "G": [[(4,1),(3,0),(1,0),(0,1),(0,5),(1,6),(4,6),(4,3),(2,3)]], "H": [[(0,0),(0,6)],[(4,0),(4,6)],[(0,3),(4,3)]],
    "I": [[(1,0),(3,0)],[(2,0),(2,6)],[(1,6),(3,6)]], "J": [[(4,0),(4,5),(3,6),(1,6),(0,5)]],
    "K": [[(0,0),(0,6)],[(4,0),(0,3),(4,6)]], "L": [[(0,0),(0,6),(4,6)]],
    "M": [[(0,6),(0,0),(2,3),(4,0),(4,6)]], "N": [[(0,6),(0,0),(4,6),(4,0)]],
    "O": [[(1,0),(3,0),(4,1),(4,5),(3,6),(1,6),(0,5),(0,1),(1,0)]], "P": [[(0,6),(0,0),(3,0),(4,1),(4,2),(3,3),(0,3)]],
    "R": [[(0,6),(0,0),(3,0),(4,1),(4,2),(3,3),(0,3)],[(2,3),(4,6)]], "S": [[(4,1),(3,0),(1,0),(0,1),(0,2),(4,4),(4,5),(3,6),(1,6),(0,5)]],
    "T": [[(0,0),(4,0)],[(2,0),(2,6)]], "U": [[(0,0),(0,5),(1,6),(3,6),(4,5),(4,0)]],
    "W": [[(0,0),(1,6),(2,3),(3,6),(4,0)]], "Y": [[(0,0),(2,3),(4,0)],[(2,3),(2,6)]],
    "&": [[(4,6),(1,2),(1,1),(2,0),(3,1),(3,2),(0,4),(0,5),(1,6),(2,6),(4,4)]],
}


def letter(d, text, box, ink, weight):
    """Centre `text` in `box` in the stroke alphabet."""
    x0, y0, x1, y1 = box
    height = (y1 - y0) * .62
    unit = height / 6
    advance = unit * 5.6
    width = sum(advance if ch != " " else unit * 3.2 for ch in text) - unit * 1.6
    scale = min(1., (x1 - x0) * .9 / width)
    unit *= scale; advance *= scale; height *= scale; width *= scale
    x = (x0 + x1) / 2 - width / 2
    y = (y0 + y1) / 2 - height / 2
    for ch in text:
        if ch == " ":
            x += unit * 3.2
            continue
        for line in GLYPHS[ch]:
            d.line([(x + px * unit, y + py * unit) for px, py in line], fill=ink, width=max(2, round(weight * scale)), joint="curve")
        x += advance


def wall_maps(stem, size=512, painted=False):
    base = Image.open(ROOT / f"{stem}_basecolor.png").convert("RGB").resize((size, size), Image.Resampling.LANCZOS)
    normal = Image.open(ROOT / f"{stem}_normal_gl.png").convert("RGB").resize((size, size), Image.Resampling.LANCZOS)
    if painted:
        # Paint over brick: the bond and its joints still show, in one pale coat
        # the building's own colour tints (city-context.js PAINTED tones).
        grey = base.convert("L")
        base = Image.merge("RGB", [grey.point(lambda v: min(255, 150 + v // 2))] * 3)
    return base, normal


def make_fronts():
    """The four wall maps and the 4 x 4 parts atlas (256 px cells), as JPEG."""
    maps = {}
    for name, (stem, span) in FRONT_WALLS.items():
        base, normal = wall_maps(stem)
        maps[name] = (base, normal, span)
    base, normal = wall_maps(FRONT_WALLS["brick"][0], painted=True)
    maps["painted"] = (base, normal, FRONT_WALLS["brick"][1])
    cell = 256
    atlas = Image.new("RGB", (cell * 4, cell * 4), (128, 128, 128))
    d = ImageDraw.Draw(atlas)
    rand = random.Random(18711871)
    cells = {}
    def at(name, col, row):
        cells[name] = [col, row]
        return col * cell, row * cell
    # Plate glass over a panelled bulkhead, between thin iron mullions.
    x, y = at("shop_glass", 0, 0)
    d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(198, 192, 178))
    d.rectangle((x + 6, y + 6, x + cell - 7, y + 196), fill=(30, 36, 38))
    for i in range(14):
        g = 44 + i * 3
        d.line((x + 10 + i * 9, y + 10, x + 10 + i * 9 + 60, y + 190), fill=(g, g + 8, g + 10), width=4)
    d.rectangle((x + 6, y + 6, x + cell - 7, y + 40), fill=(44, 52, 54))
    d.line((x + 6, y + 42, x + cell - 7, y + 42), fill=(198, 192, 178), width=4)
    d.line((x + cell // 2, y + 6, x + cell // 2, y + 196), fill=(198, 192, 178), width=4)
    d.rectangle((x + 6, y + 202, x + cell - 7, y + cell - 7), fill=(176, 168, 150))
    for q in (x + 14, x + cell // 2 + 6):
        d.rectangle((q, y + 210, q + cell // 2 - 26, y + cell - 14), outline=(130, 122, 108), width=3)
    # A recessed shop door: glazed double leaves, a transom light above.
    x, y = at("shop_door", 1, 0)
    d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(60, 48, 36))
    d.rectangle((x + 16, y + 10, x + cell - 17, y + 52), fill=(36, 44, 46))
    d.line((x + 16, y + 56, x + cell - 17, y + 56), fill=(150, 130, 100), width=6)
    for q in (x + 16, x + cell // 2 + 4):
        d.rectangle((q, y + 64, q + cell // 2 - 20, y + cell - 4), fill=(84, 64, 44))
        d.rectangle((q + 10, y + 74, q + cell // 2 - 30, y + 170), fill=(40, 48, 50))
        d.rectangle((q + 12, y + 186, q + cell // 2 - 32, y + cell - 18), outline=(110, 86, 60), width=3)
    # Two-over-two sash in its frame (K06 proportions: stiles 1/12, meeting rail).
    x, y = at("sash", 2, 0)
    d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(226, 220, 204))
    for py in (y + 10, y + cell // 2 + 6):
        for px in (x + 14, x + cell // 2 + 4):
            d.rectangle((px, py, px + cell // 2 - 18, py + cell // 2 - 22), fill=(34, 42, 44))
            d.line((px + 6, py + 6, px + 40, py + 70), fill=(70, 84, 88), width=6)
    # A panelled house door with a transom light (K07 leaf: rails, stiles, panels).
    x, y = at("house_door", 3, 0)
    d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(92, 62, 42))
    d.rectangle((x + 12, y + 8, x + cell - 13, y + 46), fill=(36, 44, 46))
    d.line((x + 12, y + 52, x + cell - 13, y + 52), fill=(214, 206, 186), width=8)
    for py in (y + 64, y + 160):
        for px in (x + 30, x + cell // 2 + 10):
            d.rectangle((px, py, px + cell // 2 - 40, py + 84), outline=(64, 42, 28), width=5)
    # Cast iron painted stone colour: a fluted pilaster face (tinted per building).
    x, y = at("iron", 0, 1)
    d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(214, 208, 194))
    for q in range(x + 16, x + cell - 10, 28):
        d.rectangle((q, y, q + 9, y + cell - 1), fill=(174, 168, 154))
    # Cornice and frieze stock: pressed metal or wood, painted (tinted).
    x, y = at("cornice", 1, 1)
    d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(222, 216, 200))
    for q in range(y + 20, y + cell, 46):
        d.line((x, q, x + cell - 1, q), fill=(170, 164, 150), width=5)
    # Dressed stone trim from the 1904 K02 library.
    x, y = at("trim", 2, 1)
    trim = Image.open(ROOT / FRONT_TRIM).convert("RGB").resize((cell, cell), Image.Resampling.LANCZOS)
    atlas.paste(trim, (x, y))
    # Iron, tar and shadow.
    x, y = at("dark", 3, 1)
    d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(48, 50, 46))
    # Painted signboards: four boards to a cell, the trade lettered on each.
    boards = []
    for i, word in enumerate(SIGN_WORDS):
        x, y = (i // 4) * cell, 2 * cell + (i % 4) * (cell // 4)
        board = [(30, 36, 30), (226, 214, 176)] if i % 3 else [(214, 204, 168), (34, 30, 24)]
        if i % 5 == 4:
            board = [(92, 30, 26), (232, 214, 150)]
        d.rectangle((x, y, x + cell - 1, y + cell // 4 - 1), fill=board[0])
        d.rectangle((x + 4, y + 4, x + cell - 5, y + cell // 4 - 5), outline=board[1], width=2)
        letter(d, word, (x + 10, y + 6, x + cell - 10, y + cell // 4 - 6), board[1], 5)
        boards.append([x / (4 * cell), y / (4 * cell), (x + cell) / (4 * cell), (y + cell // 4) / (4 * cell)])
    # Awning canvas, striped and plain (tinted).
    x, y = at("awning", 0, 3)
    for q in range(0, cell // 2, 16):
        d.rectangle((x, y + q, x + cell - 1, y + q + 7), fill=(232, 224, 200))
        d.rectangle((x, y + q + 8, x + cell - 1, y + q + 15), fill=(150, 72, 52))
    for i in range(cell // 2, cell):
        d.line((x, y + i, x + cell - 1, y + i), fill=(228, 218, 190) if (i // 3) % 7 else (210, 200, 172))
    # Painted boards: porch floors, fences, steps (tinted).
    x, y = at("boards", 1, 3)
    for q in range(0, cell, 16):
        v = rand.randint(-8, 8)
        d.rectangle((x, y + q, x + cell - 1, y + q + 14), fill=(220 + v, 214 + v, 198 + v))
        d.line((x, y + q + 15, x + cell - 1, y + q + 15), fill=(150, 144, 130))
    # Stone flags for a walk or a step, and a shadowed recess.
    x, y = at("flags", 2, 3)
    d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(150, 146, 134))
    for q in range(0, cell, 64):
        for r in range(0, cell, 48):
            v = rand.randint(-12, 12)
            d.rectangle((x + r + 2, y + q + 2, x + r + 46, y + q + 62), fill=(168 + v, 162 + v, 148 + v))
    x, y = at("recess", 3, 3)
    d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(26, 24, 22))
    return maps, atlas, cells, boards


def jpeg(image, quality=86):
    stream = io.BytesIO()
    image.save(stream, "JPEG", quality=quality, optimize=False, progressive=False, subsampling=2)
    return stream.getvalue()


class Mesh:
    def __init__(self, slots):
        self.p, self.n, self.uv, self.idx = [], [], [], []
        self.slots = slots

    def face(self, points, tile, centre=None):
        a, b, c = points[:3]
        u, v = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
        normal = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
        length = math.sqrt(sum(t * t for t in normal))
        if length < 1e-9:
            return
        normal = [t / length for t in normal]
        reversed_face = False
        if centre is not None:
            mid = [sum(p[k] for p in points) / len(points) for k in range(3)]
            if sum(normal[k] * (mid[k] - centre[k]) for k in range(3)) < 0:
                points = list(reversed(points))
                normal = [-t for t in normal]
                reversed_face = True
        col, row = self.slots[tile]
        gutter = .015
        u0, v0, u1, v1 = (col + gutter) / 8, (row + gutter) / 8, (col + 1 - gutter) / 8, (row + 1 - gutter) / 8
        coords = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
        if len(points) == 3:
            coords = [(u0, v1), (u1, v1), ((u0 + u1) / 2, v0)]
        if reversed_face: coords = list(reversed(coords))
        base = len(self.p)
        for p, uv in zip(points, coords):
            self.p.append(p); self.n.append(normal); self.uv.append(uv)
        for i in range(1, len(points) - 1):
            self.idx.extend((base, base + i, base + i + 1))

    def box(self, x0, x1, y0, y1, z0, z1, tile, top=None):
        centre = [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]
        for pts in ([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)],
                    [(x1,y0,z1),(x0,y0,z1),(x0,y1,z1),(x1,y1,z1)],
                    [(x0,y0,z1),(x0,y0,z0),(x0,y1,z0),(x0,y1,z1)],
                    [(x1,y0,z0),(x1,y0,z1),(x1,y1,z1),(x1,y1,z0)]):
            self.face(pts, tile, centre)
        self.face([(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)], top or tile, centre)


def build_mesh(t, slots, far=False):
    m = Mesh(slots)
    w, d, h, rise = (t[k] for k in ("width_m", "depth_m", "eave_m", "rise_m"))
    fam, roof = t["material"], t["roof"]
    # Facade subdivisions carry a standard glazed bay without stretching a
    # whole floor across a wall. Far tier shares the silhouette and a broad bay.
    sides = [((-w/2,-d/2),(w/2,-d/2), t["front_bays"], True),
             ((w/2,d/2),(-w/2,d/2), t["front_bays"], False),
             ((-w/2,d/2),(-w/2,-d/2), t["side_bays"], False),
             ((w/2,-d/2),(w/2,d/2), t["side_bays"], False)]
    for side_index, (a, b, bays, front) in enumerate(sides):
        rows, cols = (1, 1) if far else (t["storeys"], bays)
        for floor in range(rows):
            for bay in range(cols):
                p = [a[k] + (b[k] - a[k]) * bay / cols for k in range(2)]
                q = [a[k] + (b[k] - a[k]) * (bay + 1) / cols for k in range(2)]
                y0, y1 = h * floor / rows, h * (floor + 1) / rows
                kind = "window"
                if front and floor == 0 and not far:
                    if t.get("warehouse") and bay == cols // 2: kind = "loading"
                    elif bay == cols // 2: kind = "door"
                    elif t.get("shop"): kind = "shop"
                texture = f"{t['id']}_far_{'front' if side_index < 2 else 'side'}" if far else f"{fam}_{kind}"
                m.face([(p[0],y0,p[1]),(q[0],y0,q[1]),(q[0],y1,q[1]),(p[0],y1,p[1])], texture, (0,h/2,0))
    over = .23 if far else .34
    x0, x1, z0, z1 = -w/2-over, w/2+over, -d/2-over, d/2+over
    roof_tile = "shingle" if fam in ("timber", "weathered") else "slate"
    if roof == "flat" and t.get("shop"):
        # T-3686: the commercial front's crowning cornice, K10's (T-2316)
        # frieze (0.55 m, 25 mm proud) and pressed-metal crown (0.31 m high,
        # 0.485 m out) on the front, with scrolled brackets (0.48 m high,
        # 0.34 m out); the detail ring spaces them at K10's 0.72 m. The far form keeps the
        # crown's silhouette; the sides and back carry a plain coping.
        crown = .485 if not far else .4
        m.box(-w/2-.025,w/2+.025,h-.55,h,-d/2-.025,-d/2+.3,f"{fam}_trim")
        m.box(-w/2-.12,w/2+.12,h,h+.31,-d/2-crown,-d/2+.4,"brick_trim" if fam == "timber" else f"{fam}_trim", "dark")
        m.box(-w/2,w/2,h-.1,h+.18,-d/2+.4,d/2+.04,f"{fam}_trim", "dark")
        if not far:
            # Brackets are the detail ring's (city-fronts.js); five stand in
            # for the run so the crown still reads as carried.
            for i in range(5):
                x = -w/2+.2+(w-.4)*i/4
                m.box(x-.05,x+.05,h-.48,h,-d/2-.34,-d/2,"brick_trim" if fam == "timber" else f"{fam}_trim")
            m.box(-w/2+.28,w/2-.28,h+.13,h+.16,-d/2+.5,d/2-.28,"dark")
            # A stone step at the shop door, on the walk side of the front.
            m.box(-w/2,w/2,0,.16,-d/2-.42,-d/2,"stone_trim")
    elif roof == "flat":
        m.box(x0,x1,h-.22,h+.13,z0,z1,f"{fam}_trim", "dark")
        if not far:
            m.box(-w/2+.28,w/2-.28,h+.13,h+.16,-d/2+.28,d/2-.28,"dark")
    elif roof == "gable":
        m.face([(x0,h,z0),(x0,h,z1),(0,h+rise,z1),(0,h+rise,z0)], roof_tile, (0,h,0))
        m.face([(x1,h,z1),(x1,h,z0),(0,h+rise,z0),(0,h+rise,z1)], roof_tile, (0,h,0))
        m.face([(-w/2,h,-d/2),(w/2,h,-d/2),(0,h+rise,-d/2)], f"{fam}_wall", (0,h,0))
        m.face([(w/2,h,d/2),(-w/2,h,d/2),(0,h+rise,d/2)], f"{fam}_wall", (0,h,0))
    elif roof == "hip":
        r0, r1 = z0 + min(w/2, d/2), z1 - min(w/2, d/2)
        m.face([(x0,h,z0),(x1,h,z0),(0,h+rise,r0)], roof_tile, (0,h,0))
        m.face([(x1,h,z1),(x0,h,z1),(0,h+rise,r1)], roof_tile, (0,h,0))
        m.face([(x0,h,z1),(x0,h,z0),(0,h+rise,r0),(0,h+rise,r1)], roof_tile, (0,h,0))
        m.face([(x1,h,z0),(x1,h,z1),(0,h+rise,r1),(0,h+rise,r0)], roof_tile, (0,h,0))
    elif roof == "mansard":
        inset = min(1.3,w*.2)
        bottom=[(x0,h,z0),(x1,h,z0),(x1,h,z1),(x0,h,z1)]
        top=[(x0+inset,h+rise,z0+inset),(x1-inset,h+rise,z0+inset),(x1-inset,h+rise,z1-inset),(x0+inset,h+rise,z1-inset)]
        for i in range(4): m.face([bottom[i],bottom[(i+1)%4],top[(i+1)%4],top[i]],roof_tile,(0,h,0))
        m.face(top,"dark",(0,h,0))
        if not far:
            for x in (-w*.25,w*.25):
                m.box(x-.55,x+.55,h+.45,h+1.9,z0+.12,z0+.85,f"{fam}_window", "slate")
    if not far:
        # A stone plinth and cornice are physical silhouette/shadow lines.
        m.box(-w/2-.04,w/2+.04,0,.30,-d/2-.04,d/2+.04,f"{fam}_trim")
        cw=.7 if not t.get("factory") else 1.4
        cx, cz=w*.29,d*.19
        ch=h+rise*.7+(1.2 if not t.get("factory") else 11)
        m.box(cx-cw/2,cx+cw/2,h-.1,ch,cz-cw/2,cz+cw/2,"brick_wall","dark")
        m.box(cx-cw*.62,cx+cw*.62,ch-.17,ch+.02,cz-cw*.62,cz+cw*.62,"brick_trim","dark")
        if t.get("shop"):
            m.box(-w/2-.12,w/2+.12,h/t["storeys"]-.23,h/t["storeys"]-.02,-d/2-.3,-d/2+.03,f"{fam}_trim")
        entrance(m, t, w, d, h, fam)
    elif t.get("factory"):
        # Factory stacks are skyline forms, retained in the distant tier.
        cx,cz=w*.29,d*.19
        m.box(cx-.7,cx+.7,h-.1,h+rise*.7+11,cz-.7,cz+.7,"brick_wall","dark")
    return m


def entrance(m, t, w, d, h, fam):
    """T-3686: every house has its way in: steps to the door, a stoop or a porch.

    Sizes are K07's (T-2303): risers about 0.17 m (n = round(floor / 0.17)),
    treads 0.30 m, a principal floor 0.8-1.8 m up for a raised masonry house,
    and a timber porch of a boarded deck, square posts and a flat roof. The
    1835 frame houses' plain plank steps stand at a frame cottage's door.
    """
    if t.get("shop") or t.get("warehouse") or t.get("factory"):
        return
    floor = {"brick_rowhouse": 1.36, "brick_mansard": 1.19, "villa_hip": 1.02,
             "brick_cottage": .51, "timber_cottage": .34, "timber_house": .51, "timber_hip": .51}.get(t["id"], .34)
    risers = max(2, round(floor/.17)); rise = floor/risers
    stair_w = 1.5 if t["id"] in ("brick_rowhouse", "brick_mansard", "villa_hip") else 1.3
    trim = "stone_trim" if fam in ("brick", "stone") else f"{fam}_trim"
    porch = t["id"] in ("timber_house", "timber_hip", "timber_cottage")
    land = 1.9 if porch else 1.1
    if porch:
        pw = min(w*.62, 5.2)
        m.box(-pw/2,pw/2,0,floor,-d/2-land,-d/2,f"{fam}_trim")
        for x in (-pw/2+.2, pw/2-.2):
            m.box(x-.08,x+.08,floor,floor+2.5,-d/2-land+.12,-d/2-land+.28,f"{fam}_trim")
        m.box(-pw/2-.18,pw/2+.18,floor+2.5,floor+2.66,-d/2-land-.18,-d/2,"dark")
    else:
        m.box(-stair_w/2-.3,stair_w/2+.3,0,floor,-d/2-land,-d/2,trim)
    # Equal risers down to grade, each a tread wider than the one above.
    for i in range(1, risers):
        top = floor - i*rise
        m.box(-stair_w/2,stair_w/2,0,top,-d/2-land-.3*i,-d/2-land-.3*(i-1),trim)


# Integrate after Mesh and before glb(). These generic early-autumn silhouettes
# are reconstructed context, not identified species, measured trees or phenology.
# Atlas tile names needed: bark, foliage_green, foliage_ochre.

def build_tree_mesh(t, slots, far=False):
    """Original portable deciduous tree: 96 near / 28 far triangles.

    t: id, form ('round'|'oval'|'spreading'), height_m, crown_r_m,
    trunk_r_m. All numbers are metres. Base at (0,0,0), +Y up.
    Every face will receive the shared kit's reconstructed _CONFIDENCE=1.
    """
    m = Mesh(slots)
    height = float(t["height_m"])
    radius = float(t["crown_r_m"])
    trunk = float(t.get("trunk_r_m", .22))
    form = t.get("form", "round")

    def cross(a, b):
        return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

    def unit(a):
        d = math.sqrt(sum(v*v for v in a)) or 1
        return tuple(v/d for v in a)

    def branch(a, b, r0, r1, sides):
        axis = unit(tuple(b[k]-a[k] for k in range(3)))
        ref = (1,0,0) if abs(axis[0]) < .9 else (0,0,1)
        u = unit(cross(axis, ref))
        v = cross(axis, u)
        rings = []
        for centre, r in ((a,r0),(b,r1)):
            rings.append([tuple(centre[k]+r*(u[k]*math.cos(i*2*math.pi/sides)+v[k]*math.sin(i*2*math.pi/sides)) for k in range(3)) for i in range(sides)])
        centre = tuple((a[k]+b[k])/2 for k in range(3))
        for i in range(sides):
            j=(i+1)%sides
            m.face([rings[0][i],rings[0][j],rings[1][j],rings[1][i]], "bark", centre)

    # Twenty triangles, no transparency, no hidden interior or leaf-card sorting.
    # Axis-normalising the icosahedron puts extrema exactly at centre +/- radii.
    phi=(1+math.sqrt(5))/2
    vertices=[(-1,phi,0),(1,phi,0),(-1,-phi,0),(1,-phi,0),
              (0,-1,phi),(0,1,phi),(0,-1,-phi),(0,1,-phi),
              (phi,0,-1),(phi,0,1),(-phi,0,-1),(-phi,0,1)]
    faces=[(0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),
           (1,5,9),(5,11,4),(11,10,2),(10,7,6),(7,1,8),
           (3,9,4),(3,4,2),(3,2,6),(3,6,8),(3,8,9),
           (4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1)]

    def crown(centre, radii, index):
        points=[tuple(centre[k]+p[k]*radii[k]/phi for k in range(3)) for p in vertices]
        for face_index, face in enumerate(faces):
            # Sparse ochre is a reconstructed early-autumn variation, not a
            # species identification or an assertion about 8 October's weather.
            tile="foliage_ochre" if (face_index+index*3)%11 == 0 else "foliage_green"
            first=len(m.p)
            m.face([points[k] for k in face], tile, centre)
            # Smooth crown normals retain the low-cost portable silhouette
            # without making every triangular lobe a separate flat plane.
            for i in range(first,len(m.p)):
                n=tuple((m.p[i][k]-centre[k])/(radii[k]*radii[k]) for k in range(3))
                m.n[i]=unit(n)

    if form == "oval":
        centre=(0,.64*height,0); radii=(.82*radius,.36*height,.78*radius)
        lobes=[((-.35*radius,.52*height,.10*radius),(.65*radius,.23*height,.68*radius)),
               ((.35*radius,.57*height,-.10*radius),(.65*radius,.26*height,.68*radius))]
    elif form == "spreading":
        centre=(0,.72*height,0); radii=(radius,.28*height,.82*radius)
        lobes=[((-.39*radius,.60*height,.18*radius),(.61*radius,.23*height,.72*radius)),
               ((.39*radius,.62*height,-.18*radius),(.61*radius,.24*height,.72*radius))]
    else:
        centre=(0,.67*height,0); radii=(radius,.33*height,.88*radius)
        lobes=[((-.35*radius,.55*height,.16*radius),(.65*radius,.25*height,.70*radius)),
               ((.35*radius,.59*height,-.16*radius),(.65*radius,.27*height,.70*radius))]

    branch((0,0,0),(0,.65*height,0),trunk,trunk*.42,4 if far else 6)
    crown(centre,radii,0)
    if not far:
        for index,(position,extent) in enumerate(lobes,1):
            crown(position,extent,index)
        for end in ((-.48*radius,.57*height,.10*radius),
                    (.48*radius,.61*height,-.10*radius),
                    (.08*radius,.68*height,.46*radius)):
            branch((0,.29*height,0),end,trunk*.55,trunk*.12,4)
    return m



def glb(recipe):
    maps, slots = make_atlas(recipe)
    blob = bytearray(); views=[]; accessors=[]; meshes=[]; nodes=[]
    def view(data, target=None):
        while len(blob)%4: blob.append(0)
        off=len(blob); blob.extend(data)
        entry={"buffer":0,"byteOffset":off,"byteLength":len(data)}
        if target: entry["target"]=target
        views.append(entry); return len(views)-1
    def accessor(values, width, kind="f", bounds=False):
        flat=[v for row in values for v in row] if width>1 else values
        packed=struct.pack("<"+kind*len(flat),*flat)
        item={"bufferView":view(packed,34963 if kind=="I" else 34962),"componentType":5125 if kind=="I" else 5126,"count":len(values),"type":{1:"SCALAR",2:"VEC2",3:"VEC3"}[width]}
        if bounds:
            item["min"]=[min(row[k] for row in values) for k in range(width)]
            item["max"]=[max(row[k] for row in values) for k in range(width)]
        accessors.append(item); return len(accessors)-1
    stats=[]; vegetation=[]
    for t in recipe["templates"]+recipe.get("vegetation",[]):
        record=dict(t); record["nodes"]={}; record["triangles"]={}
        is_tree="form" in t
        if is_tree:
            record.update(width_m=2*t["crown_r_m"],depth_m=2*t["crown_r_m"],eave_m=t["height_m"],vegetation=True)
        for tier in ("near","far"):
            m=build_tree_mesh(t,slots,tier=="far") if is_tree else build_mesh(t,slots,tier=="far")
            attrs={"POSITION":accessor(m.p,3,bounds=True),"NORMAL":accessor(m.n,3),"TEXCOORD_0":accessor(m.uv,2),"_CONFIDENCE":accessor([1.0]*len(m.p),1)}
            meshes.append({"name":f"{t['id']}__{tier}","primitives":[{"attributes":attrs,"indices":accessor(m.idx,1,"I"),"material":0}]})
            nodes.append({"name":f"{t['id']}__{tier}","mesh":len(meshes)-1,"extras":{"context_template":t["id"],"tier":tier,"confidence":"reconstructed","scene_year":1871}})
            record["nodes"][tier]=nodes[-1]["name"]; record["triangles"][tier]=len(m.idx)//3
        (vegetation if is_tree else stats).append(record)
    images=[{"bufferView":view(data),"mimeType":"image/png","name":name} for data,name in zip(maps,("original_facade_basecolor","original_facade_normal","original_facade_orm"))]
    textures=[{"sampler":0,"source":i} for i in range(3)]
    materials=[{"name":"city_context_1871_atlas","pbrMetallicRoughness":{"baseColorTexture":{"index":0},"metallicRoughnessTexture":{"index":2},"metallicFactor":0,"roughnessFactor":1},"normalTexture":{"index":1,"scale":.45},"occlusionTexture":{"index":2,"strength":.28}}]
    # T-3686: the detail ring's wall and parts materials ride in the kit as one
    # small node, so they load with it and share its provenance stamp.
    walls,parts,cells,boards=make_fronts()
    def texture(image,name,sampler):
        images.append({"bufferView":view(jpeg(image)),"mimeType":"image/jpeg","name":name})
        textures.append({"sampler":sampler,"source":len(images)-1}); return len(textures)-1
    fronts={"materials":{},"cells":cells,"boards":boards,"atlas_cells":4}
    atlas=Image.open(io.BytesIO(maps[0])).convert("RGB")
    def mean(image):
        return ImageStat.Stat(image.resize((64,64),Image.Resampling.BOX)).mean
    linear=lambda c:((c/255+.055)/1.055)**2.4
    rows={"brick":0,"stone":2,"painted":2,"clapboard":1}
    primitives=[]
    for name,(base,normal,span) in walls.items():
        materials.append({"name":f"fronts_{name}","pbrMetallicRoughness":{"baseColorTexture":{"index":texture(base,f"fronts_{name}_basecolor",1)},"metallicFactor":0,"roughnessFactor":.92},"normalTexture":{"index":texture(normal,f"fronts_{name}_normal",1),"scale":.8}})
        target=mean(atlas.crop((0,rows[name]*128,128,rows[name]*128+128)));own=mean(base)
        fronts["materials"][name]={"material":materials[-1]["name"],"span_m":span,"atlas_row":rows[name],"match":[round(linear(a)/linear(b),3) for a,b in zip(target,own)]}
    materials.append({"name":"fronts_parts","pbrMetallicRoughness":{"baseColorTexture":{"index":texture(parts,"fronts_parts_basecolor",0)},"metallicFactor":0,"roughnessFactor":.8}})
    fronts["materials"]["parts"]={"material":"fronts_parts"}
    for index in range(1,len(materials)):
        tri=[[0,0,0],[.01,0,0],[0,.01,0]]
        primitives.append({"attributes":{"POSITION":accessor(tri,3,bounds=True),"NORMAL":accessor([[0,0,1]]*3,3),"TEXCOORD_0":accessor([[0,0],[1,0],[0,1]],2),"_CONFIDENCE":accessor([1.0]*3,1)},"indices":accessor([0,1,2],1,"I"),"material":index})
    meshes.append({"name":"fronts__materials","primitives":primitives})
    nodes.append({"name":"fronts__materials","mesh":len(meshes)-1,"extras":{"context_template":"fronts","tier":"detail","confidence":"reconstructed","scene_year":1871}})
    fronts["node"]="fronts__materials"
    document={"asset":{"version":"2.0","generator":"city_context_emit.py","extras":{"confidence":"reconstructed","source_limit":recipe["source_limit"],"license":recipe["license"]}},"scene":0,"scenes":[{"nodes":list(range(len(nodes)))}],"nodes":nodes,"meshes":meshes,"materials":materials,"textures":textures,"samplers":[{"magFilter":9729,"minFilter":9987,"wrapS":33071,"wrapT":33071},{"magFilter":9729,"minFilter":9987,"wrapS":10497,"wrapT":10497}],"images":images,"accessors":accessors,"bufferViews":views,"buffers":[{"byteLength":len(blob)}]}
    encoded=json.dumps(document,separators=(",",":"),ensure_ascii=False).encode()
    encoded+=b" "*((-len(encoded))%4); blob.extend(b"\0"*((-len(blob))%4))
    output=struct.pack("<III",0x46546c67,2,12+8+len(encoded)+8+len(blob))+struct.pack("<II",len(encoded),0x4e4f534a)+encoded+struct.pack("<II",len(blob),0x004e4942)+blob
    return output,stats,vegetation,fronts


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--check",action="store_true"); args=ap.parse_args()
    recipe=json.loads(RECIPE.read_text())
    records = {}
    citation_ids = sorted(set(recipe.get("citation_sources", recipe["sources"])) | set(recipe["sources"]))
    for source_id in citation_ids:
        source=ROOT/"data/sources"/f"{source_id}.json"
        if not source.exists():
            raise SystemExit(f"Unregistered source: {source_id}")
        record=json.loads(source.read_text())
        records[source_id] = record
        if record.get("rights_status") in ("restricted","check_required"):
            raise SystemExit(f"Source not cleared for generated geometry: {source_id}")
    input_files = [RECIPE, Path(__file__), ROOT/"tools/compile_scene.py", ROOT/"tools/tiers.py", ROOT/"data/source.schema.json"] + [ROOT/"data/sources"/f"{sid}.json" for sid in citation_ids] + [ROOT/f"{stem}_{map}.png" for stem,_ in FRONT_WALLS.values() for map in ("basecolor","normal_gl")] + [ROOT/FRONT_TRIM]
    input_hash = digest(canonical({p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in input_files}))
    data,templates,vegetation,fronts=glb(recipe)
    definition={"schema":"chicago-city-context-kit-v1","generated_by":"generators/city_context_emit.py","recipe":"context/1871/kit-recipe.json","glb":"context/1871/kit.glb","confidence":"reconstructed","sources":recipe["sources"],"source_limit":recipe["source_limit"],"license":recipe["license"],"coordinates":recipe["coordinates"],"input_sha256":input_hash,"citations":cite(citation_ids,records),"asset_sha256":digest(data),"asset_bytes":len(data),"templates":templates,"vegetation":vegetation,"vegetation_note":recipe.get("vegetation_note"),"fronts":fronts}
    outputs={FOLDER/"kit.glb":data,FOLDER/"kit.json":canonical(definition)}
    for path,contents in outputs.items():
        if args.check:
            if not path.exists() or path.read_bytes()!=contents: raise SystemExit(f"Stale generated context kit: {path.relative_to(ROOT)}")
        else: path.write_bytes(contents)
    print(f"1871 context kit: {len(templates)} forms, {len(data):,} bytes; deterministic {'check passed' if args.check else 'build complete'}")


if __name__ == "__main__":
    main()
