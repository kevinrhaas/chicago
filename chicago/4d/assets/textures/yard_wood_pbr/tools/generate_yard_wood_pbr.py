#!/usr/bin/env python3
"""Build the yard woodpiles' surface library (T-3474).

    python3 assets/textures/yard_wood_pbr/tools/generate_yard_wood_pbr.py
    python3 tools/ktx2_sheets.py --only yard_wood_pbr/

ONE ATLAS, SIX CELLS. The woodpiles are one mesh for the whole town (renderers/web/js/
yard.js, T-1959: the draw-call budget's choice), so their wood is one material and one
sheet set, and each face samples a window of one cell, as the painted cells it replaces
did. The cells are drawn at 1024 px and shipped at 512 (OUT below); the part a face may
sample is the inner 960 (480 shipped), which is `WOOD_CELL_M` = 0.85 m of wood, and the
gutter round it is the same picture, so the mips of one cell do not bleed into the next
at any level a face is seen at.

    col 0            col 1            col 2
    rick_ends_a      rick_ends_b      rick_sides        row 0
    round_end        log_bark         split_face        row 1

- **rick_ends_a / _b** — the face of a rick of cordwood: split billet ends, quarters,
  halves, slabs and small rounds, racked in courses with the dark of the pile behind them.
  Each end carries its growth rings round its own pith, the rays of oak, a heartwood/
  sapwood break, a bark rind on its outer arc, the heart and surface checks a summer opens,
  the facets of the axe that cut it to length, and its own weathering: most a season
  stacked and greying, a few fresh. Two cells of different seed, so neighbouring ricks
  differ.
- **rick_sides** — the sticks seen along their length (a rick's top and its ends): bark
  and pale split faces in courses, the gap under each, a stick's end here and there.
  Sticks run along image x.
- **round_end** — one sawn round filling the cell: the chopping block's top and a log's
  end. Rings round a pith a little off centre, checks opening from the rim, crosscut
  kerf lines, and the scores of an axe.
- **log_bark** — the rough bark of an oak or hickory log, blocky ridges over deep
  furrows, the fissures along image x.
- **split_face** — a split face along the grain: torn fibres, a check or two, cream to
  grey. The billets on the ground, the slabs and a loose stick.

No photograph is embedded, sampled or traced: every map is procedural, and the look is a
reconstruction (docs/LIBERTIES.md L-t3474-yard-wood-surfaces). Deterministic: the same
seeds write the same bytes.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

CELL = 1024
GUTTER = 32
INNER = CELL - 2 * GUTTER          # 960 px = WOOD_CELL_M
CELL_M = 0.85
PX_M = INNER / CELL_M              # 1129 px to the metre
COLS, ROWS = 3, 2
# The cells are drawn at 1024 px and SHIPPED at half that (OUT = 512 a cell, 565 px to
# the metre): the published tree's budget (tools/validate.py) had 13.7 MB of headroom on
# 2026-11-07 and the full-size atlas's six web files were 15.6 MB. Drawn large and
# filtered down, the rings and checks keep their edges.
OUT = 0.5
LIB = Path(__file__).resolve().parent.parent
SID = "woodpile_atlas"
SEED = 18120808

LAYOUT = [
    ("rick_ends_a", 0, 0), ("rick_ends_b", 1, 0), ("rick_sides", 2, 0),
    ("round_end", 0, 1), ("log_bark", 1, 1), ("split_face", 2, 1),
]

# ------------------------------------------------------------------ helpers


def norm01(a):
    lo, hi = float(a.min()), float(a.max())
    return (a - lo) / max(hi - lo, 1e-9)


def noise(rng, shape, sigma):
    a = rng.standard_normal(shape).astype(np.float32)
    return norm01(ndimage.gaussian_filter(a, sigma=sigma, mode="wrap"))


def fbm(rng, shape, sigmas, weights):
    out = np.zeros(shape, np.float32)
    for s, w in zip(sigmas, weights):
        out += w * noise(rng, shape, s)
    return norm01(out)


def lerp(a, b, t):
    t = t[..., None] if np.ndim(t) == 2 else t
    return np.asarray(a, np.float32) * (1 - t) + np.asarray(b, np.float32) * t


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def normal_from_height(h, strength):
    """OpenGL (+Y up the image) normal from a height in [0, 1]. A cell is not a tile, so
    the edges clamp rather than wrap."""
    hp = np.pad(h, 1, mode="edge")
    dx = (hp[1:-1, 2:] - hp[1:-1, :-2]) * 0.5 * strength
    dy = (hp[2:, 1:-1] - hp[:-2, 1:-1]) * 0.5 * strength
    nx, ny, nz = -dx, dy, np.ones_like(h)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / ln, ny / ln, nz / ln], -1)
    return ((n * 0.5 + 0.5) * 255.0 + 0.5).clip(0, 255).astype(np.uint8)


def occlusion(h, radii=((4, 1.0), (16, 1.0), (40, 0.6))):
    """Cavity occlusion at three reaches: the check, the gap between two sticks, and the
    hollow of the pile behind them."""
    ao = np.ones_like(h)
    for r, w in radii:
        blur = ndimage.gaussian_filter(h, r, mode="nearest")
        ao *= 1.0 - w * np.clip((blur - h) * 5.0, 0.0, 1.0)
    return np.clip(ao, 0.0, 1.0)


def to_u8(a):
    return (np.clip(a, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


# Woods of the 1812 groves (oak, hickory, ash and elm are the trees the
# Chicago-portage accounts name), as end-grain colours: (sapwood, heartwood, latewood k,
# rays). sRGB, before weathering.
WOODS = [
    dict(name="white oak", sap=(0.80, 0.68, 0.50), heart=(0.64, 0.48, 0.31), late=0.82, rays=0.10, w=0.38),
    dict(name="red oak", sap=(0.80, 0.66, 0.49), heart=(0.67, 0.49, 0.35), late=0.78, rays=0.08, w=0.20),
    dict(name="hickory", sap=(0.84, 0.74, 0.57), heart=(0.61, 0.44, 0.30), late=0.84, rays=0.0, w=0.22),
    dict(name="ash", sap=(0.86, 0.78, 0.63), heart=(0.74, 0.63, 0.47), late=0.82, rays=0.0, w=0.12),
    dict(name="elm", sap=(0.78, 0.66, 0.50), heart=(0.60, 0.44, 0.32), late=0.80, rays=0.0, w=0.08),
]
SILVER = np.array([0.58, 0.55, 0.50], np.float32)
BARK_DARK = np.array([0.21, 0.18, 0.15], np.float32)
BARK_MID = np.array([0.40, 0.35, 0.30], np.float32)
BARK_GREY = np.array([0.55, 0.52, 0.47], np.float32)
CAMBIUM = np.array([0.52, 0.36, 0.22], np.float32)


def pick_wood(rng):
    w = np.array([x["w"] for x in WOODS])
    return WOODS[int(rng.choice(len(WOODS), p=w / w.sum()))]


def weathering(rng):
    """How far a piece has silvered: most a season stacked, a few fresh, a few grey."""
    u = rng.random()
    if u < 0.3:
        return rng.uniform(0.0, 0.15)
    if u < 0.85:
        return rng.uniform(0.18, 0.45)
    return rng.uniform(0.5, 0.8)


# ------------------------------------------------------------------ end grain


def end_grain(rng, r, th, R, wood, weather, detail, xx, yy):
    """Colour, height and roughness of an end-grain surface at radius r (px) and angle th
    round its pith. `detail` is a dict of fields (noise) over the same box."""
    hw = rng.uniform(0.5, 0.8)
    sp = rng.uniform(3.5, 7.0)                   # ring spacing, px (3-6 mm)
    warp = detail["warp"] * rng.uniform(2.0, 4.0)
    # good years and bad: the spacing swells and narrows as the tree grew
    ph = rng.uniform(0, 6.28, 2)
    ring_t = (r + warp) / sp + 1.6 * np.sin(r / rng.uniform(25, 45) + ph[0]) \
        + 0.9 * np.sin(r / rng.uniform(9, 15) + ph[1])
    frac = ring_t - np.floor(ring_t)
    late = smooth(0.55, 0.8, frac) * (1 - smooth(0.9, 1.0, frac))
    rel = r / max(R, 1e-6)
    sap = np.asarray(wood["sap"], np.float32)
    heart = np.asarray(wood["heart"], np.float32)
    base = lerp(heart, sap, smooth(hw - 0.06, hw + 0.04, rel))
    # the pith's own small dark core
    base = lerp(base, heart * 0.7, smooth(6.0, 1.5, r))
    col = base * (1 - (1 - wood["late"]) * late[..., None])
    # pores: early wood of ring-porous oak/ash speckled dark
    pores = detail["speck"] < 0.18
    col = col * (1 - 0.18 * (pores & (late < 0.3))[..., None])
    if wood["rays"] > 0:
        n_rays = 90
        ray = np.cos(th * n_rays + detail["rayw"] * 6.0)
        ray = smooth(0.985, 1.0, ray) * smooth(0.15, 0.4, rel)
        col = col * (1 + wood["rays"] * ray[..., None])
    # tone variation over the face
    col = col * (0.9 + 0.2 * detail["tone"][..., None])
    # silvering: the face greys toward the weathered tone, darker in the latewood
    silver = SILVER * (0.92 + 0.12 * detail["tone"][..., None]) * (1 - 0.08 * late[..., None])
    col = lerp(col, silver, weather * (0.85 + 0.15 * detail["tone"]))
    # end grain is rough, more so as it weathers; latewood a touch smoother
    rough = 0.86 + 0.08 * weather - 0.04 * late + 0.03 * detail["speck"]
    h = -0.02 * late + 0.01 * detail["speck"]
    return col, h, rough


def checks(rng, r, th, R, n, from_rim):
    """Radial checks: V-shaped cracks, from the pith out (a heart check) or the rim in
    (a surface check, which is what a summer in the stack opens). Returns a 0..1 mask."""
    m = np.zeros_like(r)
    for _ in range(n):
        a = rng.uniform(-math.pi, math.pi)
        d = np.angle(np.exp(1j * (th - a)))
        across = np.abs(d) * np.maximum(r, 1.0)
        if from_rim:
            reach = rng.uniform(0.35, 0.8) * R
            s = np.clip((r - (R - reach)) / max(reach, 1e-6), 0, 1)
        else:
            reach = rng.uniform(0.3, 0.75) * R
            s = np.clip(1 - r / max(reach, 1e-6), 0, 1)
        width = 0.6 + rng.uniform(1.6, 3.6) * s ** 1.3
        wob = (4.0 * np.sin(r * rng.uniform(0.02, 0.05) + rng.uniform(0, 6.28))
               + 1.0 * np.sin(r * rng.uniform(0.08, 0.15) + rng.uniform(0, 6.28))) / np.maximum(r, 8.0)
        across = np.abs(np.angle(np.exp(1j * (th - a - wob)))) * np.maximum(r, 1.0)
        m = np.maximum(m, smooth(width + 0.8, width * 0.4, across) * (s > 0))
    return m


# ------------------------------------------------------------------ rick ends


def rick_ends(seed):
    rng = np.random.default_rng(seed)
    S = CELL
    col = np.zeros((S, S, 3), np.float32)
    h = np.zeros((S, S), np.float32)
    rough = np.full((S, S), 0.97, np.float32)
    owner = np.zeros((S, S), np.int32)
    # the dark of the pile behind: brown-black with a little of the back sticks showing
    back = fbm(rng, (S, S), (30, 9, 3), (0.5, 0.3, 0.2))
    col[:] = lerp(np.array([0.05, 0.04, 0.032]), np.array([0.16, 0.12, 0.09]), back * 0.7)
    h[:] = 0.04 * back
    yy0, xx0 = np.mgrid[0:S, 0:S].astype(np.float32)
    pid = 0
    for layer in (0, 1):
        # layer 0 is the course behind, seen in the gaps; layer 1 is the face
        y = -rng.uniform(0, 120)
        while y < S + 40:
            rh = rng.uniform(105, 185)
            x = -rng.uniform(0, rh)
            while x < S + 40:
                w = rh * rng.uniform(0.7, 1.45)
                sx0 = x + rng.uniform(-6, 6)
                sy0 = y + rng.uniform(-10, 10)
                pid += 1
                stamp_end(rng, col, h, rough, owner, pid, (sx0, sy0, w, rh), layer, xx0, yy0)
                x += w + (rng.uniform(1, 9) if layer else rng.uniform(-10, 4))
            y += rh + (rng.uniform(2, 10) if layer else rng.uniform(-14, 0))
    # grime: the lowest courses carry the yard, the top the weather
    dirt = fbm(rng, (S, S), (60, 14), (0.7, 0.3))
    col = col * (0.88 + 0.2 * dirt[..., None])
    hgt = ndimage.gaussian_filter(h, 0.6)
    return col, hgt, rough, 16.0, (0.62, 0.38)


def stamp_end(rng, col, h, rough, owner, pid, slot, layer, xx0, yy0):
    x0, y0, w, sh = slot
    S = CELL
    kind = rng.choice(["quarter", "eighth", "half", "round", "slab"], p=[0.36, 0.2, 0.18, 0.1, 0.16])
    cx, cy = x0 + w / 2, y0 + sh / 2
    if kind in ("quarter", "eighth"):
        # the pith at one corner of the slot, the two split faces running from it along
        # the slot's sides (a quarter) or closer in (an eighth), the bark arc across
        corner = rng.integers(4)
        px = x0 + (w if corner in (1, 2) else 0) + rng.uniform(-0.06, 0.06) * w
        py = y0 + (sh if corner in (2, 3) else 0) + rng.uniform(-0.06, 0.06) * sh
        if kind == "quarter":
            R = max(w, sh) * rng.uniform(0.92, 1.12)
            half = math.radians(rng.uniform(38, 50))
        else:
            R = math.hypot(w, sh) * rng.uniform(0.85, 0.98)
            half = math.radians(rng.uniform(17, 27))
    elif kind == "half":
        side = rng.integers(4)
        px, py = [(cx, y0), (x0 + w, cy), (cx, y0 + sh), (x0, cy)][side]
        R = (sh if side in (0, 2) else w) * rng.uniform(0.85, 1.0)
        R = min(R, max(w, sh) * 0.62)
        half = math.radians(rng.uniform(82, 95))
    elif kind == "round":
        px, py = cx + rng.uniform(-0.05, 0.05) * w, cy + rng.uniform(-0.05, 0.05) * sh
        R = min(w, sh) / 2 * rng.uniform(0.8, 0.98)
        half = math.pi
    else:  # a slab off the outside of a big log: the pith well beyond one edge
        side = rng.integers(4)
        d = max(w, sh) * rng.uniform(0.6, 1.4)
        px, py = [(cx, y0 - d), (x0 + w + d, cy), (cx, y0 + sh + d), (x0 - d, cy)][side]
        far = math.hypot(cx - px, cy - py) + 0.42 * (sh if side in (0, 2) else w)
        R = far * rng.uniform(0.95, 1.02)
        half = math.radians(rng.uniform(20, 32))
    thc = math.atan2(cy - py, cx - px) + rng.uniform(-0.12, 0.12)
    pad = 24
    bx0 = int(max(0, math.floor(x0 - pad)))
    by0 = int(max(0, math.floor(y0 - pad)))
    bx1 = int(min(S, math.ceil(x0 + w + pad)))
    by1 = int(min(S, math.ceil(y0 + sh + pad)))
    if bx1 <= bx0 + 2 or by1 <= by0 + 2:
        return
    xx = xx0[by0:by1, bx0:bx1]
    yy = yy0[by0:by1, bx0:bx1]
    dx, dy = xx - px, yy - py
    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    ph = rng.uniform(0, 6.28, 3)
    wob = 1 + 0.035 * np.sin(th * 3 + ph[0]) + 0.025 * np.sin(th * 7 + ph[1]) + 0.015 * np.sin(th * 13 + ph[2])
    Rb = R * wob
    inside = r < Rb
    if half < math.pi:
        ang = np.angle(np.exp(1j * (th - thc)))
        # a split face is not a ruled line: it wanders with the grain it tore along
        split_wob = (0.03 * np.sin(r * 0.04 + ph[0]) + 0.02 * np.sin(r * 0.11 + ph[1])) * (1 + 0.5 * np.sign(ang))
        inside &= np.abs(ang) < half + split_wob
    # the neighbours crowd a piece a little: clip to its slot, loosely and raggedly
    ins = -rng.uniform(4.0, 12.0)
    rag = lambda v, k: 3.0 * np.sin(v * k + rng.uniform(0, 6.28))
    inside &= (xx > x0 + ins + rag(yy, 0.05)) & (xx < x0 + w - ins + rag(yy, 0.04))
    inside &= (yy > y0 + ins + rag(xx, 0.045)) & (yy < y0 + sh - ins + rag(xx, 0.06))
    if layer == 0:
        inside &= True
    if not inside.any():
        return
    edge = ndimage.distance_transform_edt(np.pad(inside, 1))[1:-1, 1:-1]
    wood = pick_wood(rng)
    weather = weathering(rng)
    bh = (by1 - by0, bx1 - bx0)
    detail = {
        "warp": noise(rng, bh, 16.0) - 0.5,
        "speck": noise(rng, bh, 0.7),
        "rayw": noise(rng, bh, 3.0),
        "tone": fbm(rng, bh, (14, 4), (0.6, 0.4)),
    }
    c, hh, rr = end_grain(rng, r, th, R, wood, weather, detail, xx, yy)
    # bark on the outer arc where the piece reaches its log's edge
    bt = rng.uniform(11, 24) * (0.7 if kind == "round" else 1.0)
    has_bark = rng.random() < 0.85
    bark = (r > Rb - bt) & has_bark
    camb = (r > Rb - bt - 2.5) & (r <= Rb - bt) & has_bark
    bn = noise(rng, bh, 1.2)
    bark_col = lerp(BARK_DARK, BARK_MID, bn) * (0.85 + 0.3 * detail["tone"][..., None])
    bark_col = lerp(bark_col, BARK_GREY, weather * 0.35)
    # the rind's own fissures, round the arc
    rind = smooth(0.35, 0.6, np.abs(np.sin(th * rng.uniform(40, 70) + 3 * detail["warp"])))
    bark_col = bark_col * (0.7 + 0.3 * rind[..., None])
    c = np.where(bark[..., None], bark_col, c)
    c = np.where(camb[..., None], lerp(c, CAMBIUM * (1 - 0.5 * weather) + SILVER * 0.5 * weather, 0.7), c)
    rr = np.where(bark, 0.97, rr)
    hh = hh + np.where(bark, -0.05 + 0.08 * bn, 0.0)
    # checks: a season opens them from the rim; a few heart checks from the pith
    ck = checks(rng, r, th, R, int(rng.integers(0, 4)), True)
    if rng.random() < 0.5:
        ck = np.maximum(ck, checks(rng, r, th, R, int(rng.integers(1, 3)), False))
    ck = ck * (0.4 + 0.6 * min(1.0, weather + 0.35))
    c = c * (1 - 0.75 * ck[..., None])
    hh = hh - 0.22 * ck
    rr = np.maximum(rr, ck)
    # the axe that cut it to length: two or three planar facets, and its marks
    tilt = np.zeros_like(r)
    nf = rng.integers(1, 4)
    for _ in range(nf):
        a = rng.uniform(0, 6.28)
        g = (np.cos(a) * (xx - cx) + np.sin(a) * (yy - cy))
        cut = rng.uniform(-0.3, 0.3) * max(w, sh)
        tilt = np.maximum(tilt, np.clip((g - cut) / max(w, sh), 0, 1) * rng.uniform(0.06, 0.16))
    saw = rng.random() < 0.3
    if saw:
        a = rng.uniform(0, 3.14)
        kerf = np.sin((np.cos(a) * xx + np.sin(a) * yy) * rng.uniform(0.8, 1.3)) * 0.006
        hh = hh + kerf
    # the piece's own standing proud of the face, bevelled where its fibres crushed
    proud = (rng.uniform(0.55, 0.95) if layer else rng.uniform(0.12, 0.3))
    bevel = np.clip(edge / rng.uniform(4, 8), 0, 1) ** 0.6
    hh = proud * bevel + hh + tilt
    # a rim of grime and shadow at the edge, as a photograph shows a stick end
    c = c * (0.72 + 0.28 * bevel[..., None])
    if layer == 0:
        c = c * rng.uniform(0.32, 0.48)
    hv = h[by0:by1, bx0:bx1]
    write = inside & (hh > hv - 0.02) if layer else inside & (owner[by0:by1, bx0:bx1] == 0)
    col[by0:by1, bx0:bx1] = np.where(write[..., None], c, col[by0:by1, bx0:bx1])
    h[by0:by1, bx0:bx1] = np.where(write, hh, hv)
    rough[by0:by1, bx0:bx1] = np.where(write, rr, rough[by0:by1, bx0:bx1])
    owner[by0:by1, bx0:bx1] = np.where(write, pid, owner[by0:by1, bx0:bx1])


# ------------------------------------------------------------------ rick sides


def bark_field(rng, shape, scale=1.0):
    """Fissured bark, the fissures along x: (height 0..1, colour, fissure mask)."""
    f = fbm(rng, shape, ((2.2 * scale, 26 * scale), (1.1 * scale, 9 * scale), (0.6, 2.5)), (0.5, 0.32, 0.18))
    fis = smooth(0.44, 0.2, f)               # 1 in a fissure
    plates = fbm(rng, shape, ((6 * scale, 40 * scale), (2, 8)), (0.6, 0.4))
    grit = noise(rng, shape, 0.8)
    hgt = 0.72 * (1 - fis) + 0.2 * plates + 0.06 * grit
    c = lerp(BARK_MID, BARK_GREY, smooth(0.4, 0.85, plates))
    c = lerp(c, BARK_DARK, fis * 0.9)
    c = c * (0.88 + 0.22 * grit[..., None])
    lich = noise(rng, shape, 2.5)
    lm = smooth(0.80, 0.86, lich) * (1 - fis) * smooth(0.5, 0.7, plates)
    c = lerp(c, np.array([0.58, 0.60, 0.50]), lm * 0.7)
    return hgt, c, fis


def split_field(rng, shape):
    """A split face along the grain: torn fibres along x, splinters lifting."""
    fib = fbm(rng, shape, ((0.5, 40), (0.4, 12), (0.35, 4)), (0.45, 0.35, 0.2))
    streak = fbm(rng, shape, ((3, 120), (1.2, 40)), (0.6, 0.4))
    lift = smooth(0.72, 0.88, noise(rng, shape, (1.2, 60)))
    hgt = 0.45 * fib + 0.3 * streak + 0.25 * lift
    tone = fbm(rng, shape, ((12, 160), (4, 40)), (0.6, 0.4))
    return hgt, fib, tone, lift


def stick_colour(rng, shape, bark_side, wood, weather):
    if bark_side:
        bh, bc, fis = bark_field(rng, shape, rng.uniform(0.8, 1.3))
        c = lerp(bc, BARK_GREY, weather * 0.35)
        # a strip of bark knocked off in the handling shows the wood under it
        torn = smooth(0.8, 0.86, noise(rng, shape, (10, 80)))
        sap = np.asarray(wood["sap"], np.float32) * 0.92
        c = lerp(c, lerp(sap, SILVER, weather), torn * 0.9)
        return c, 0.2 * bh - 0.1 * torn, 0.95 + 0.03 * fis
    sh, fib, tone, lift = split_field(rng, shape)
    base = lerp(np.asarray(wood["heart"], np.float32), np.asarray(wood["sap"], np.float32),
                smooth(0.2, 0.8, tone))
    c = base * (0.78 + 0.34 * fib[..., None]) * (1 + 0.12 * lift[..., None])
    c = lerp(c, SILVER * (0.88 + 0.18 * fib[..., None]), weather)
    return c, 0.14 * sh, 0.86 + 0.07 * weather + 0.03 * (1 - fib)


def rick_sides(seed):
    """Sticks along their length, in courses; each stick's edges wander and its section is
    a round (bark) or a split's ridge, with the dark of the pile between."""
    rng = np.random.default_rng(seed)
    S = CELL
    back = fbm(rng, (S, S), (24, 7, 2), (0.5, 0.3, 0.2))
    col = lerp(np.array([0.045, 0.035, 0.028]), np.array([0.15, 0.115, 0.085]), back * 0.8)
    h = (0.05 * back).astype(np.float32)
    rough = np.full((S, S), 0.97, np.float32)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    for layer in (0, 1):
        y = -rng.uniform(0, 110)
        while y < S + 30:
            th_ = rng.uniform(95, 170)
            x = -rng.uniform(0, 700)
            while x < S + 30:
                L = rng.uniform(1100, 1700)
                sy0, sy1 = int(max(0, y - 14)), int(min(S, y + th_ + 14))
                sx0, sx1 = int(max(0, x)), int(min(S, x + L))
                if sy1 > sy0 + 4 and sx1 > sx0 + 4:
                    shape = (sy1 - sy0, sx1 - sx0)
                    X = xx[sy0:sy1, sx0:sx1]
                    Y = yy[sy0:sy1, sx0:sx1]
                    ph = rng.uniform(0, 6.28, 4)
                    top = y + 6 * np.sin(X * rng.uniform(0.004, 0.009) + ph[0]) + 2.5 * np.sin(X * 0.03 + ph[1])
                    bot = y + th_ + 6 * np.sin(X * rng.uniform(0.004, 0.009) + ph[2]) + 2.5 * np.sin(X * 0.027 + ph[3])
                    # the stick tapers and its ends are not square
                    along = (X - x) / L
                    taper = 1 - 0.08 * along
                    mid = (top + bot) / 2
                    half = (bot - top) / 2 * taper
                    t = (Y - mid) / np.maximum(half, 1)          # -1..1 across
                    endcut = (X > x + 6 * np.sin(Y * 0.05 + ph[0]) + 3) & (X < x + L - 6 * np.sin(Y * 0.04 + ph[1]) - 3)
                    m = (np.abs(t) < 1) & endcut
                    if m.any():
                        wood = pick_wood(rng)
                        weather = weathering(rng)
                        bark_side = rng.random() < 0.5
                        c, dh, rr = stick_colour(rng, shape, bark_side, wood, weather)
                        if bark_side:
                            prof = np.sqrt(np.clip(1 - t * t, 0, 1))
                        else:
                            ridge = rng.uniform(-0.4, 0.4)
                            prof = np.clip(1 - np.abs(t - ridge) * rng.uniform(0.8, 1.3), 0, 1) ** 0.8
                            # the split face's edge where it meets the bark of the stick
                            c = np.where((np.abs(t) > 0.86)[..., None], lerp(c, BARK_MID, 0.8), c)
                        shade = 0.55 + 0.45 * prof
                        c = c * shade[..., None]
                        proud = rng.uniform(0.6, 0.95) if layer else rng.uniform(0.15, 0.3)
                        hh = proud * (0.35 + 0.65 * prof) + dh
                        if layer == 0:
                            c = c * rng.uniform(0.3, 0.45)
                        hv = h[sy0:sy1, sx0:sx1]
                        wr = m & (hh > hv)
                        col[sy0:sy1, sx0:sx1] = np.where(wr[..., None], c, col[sy0:sy1, sx0:sx1])
                        h[sy0:sy1, sx0:sx1] = np.where(wr, hh, hv)
                        rr = rr if np.ndim(rr) else np.full(shape, rr)
                        rough[sy0:sy1, sx0:sx1] = np.where(wr, rr, rough[sy0:sy1, sx0:sx1])
                x += L + (rng.uniform(6, 60) if layer else rng.uniform(-80, 0))
            y += th_ + (rng.uniform(-6, 6) if layer else rng.uniform(-30, -5))
    dirt = fbm(rng, (S, S), (50, 12), (0.7, 0.3))
    col = col * (0.88 + 0.2 * dirt[..., None])
    return col, ndimage.gaussian_filter(h, 0.6), rough, 14.0, (0.62, 0.38)


# ------------------------------------------------------------------ round end


def round_end(seed):
    rng = np.random.default_rng(seed)
    S = CELL
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    c0 = S / 2
    R = 0.47 * INNER                              # the cap's polygon sits at 0.45
    px, py = c0 + rng.uniform(-0.1, 0.1) * R, c0 + rng.uniform(-0.1, 0.1) * R
    dx, dy = xx - px, yy - py
    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    rc = np.hypot(xx - c0, yy - c0)
    tha = np.arctan2(yy - c0, xx - c0)
    wob = 1 + 0.02 * np.sin(tha * 3 + 1.1) + 0.015 * np.sin(tha * 8 + 2.3)
    Rb = R * wob
    wood = dict(WOODS[0])
    wood["late"] = 0.72
    detail = {
        "warp": noise(rng, (S, S), 24.0) - 0.5,
        "speck": noise(rng, (S, S), 0.7),
        "rayw": noise(rng, (S, S), 3.0),
        "tone": fbm(rng, (S, S), (60, 14), (0.6, 0.4)),
    }
    col, h, rough = end_grain(rng, r, th, R * 1.25, wood, 0.0, detail, xx, yy)
    # the heartwood's own darker, irregular core, and the sapwood band
    hb = 0.62 + 0.05 * np.sin(th * 2 + 0.7) + 0.03 * np.sin(th * 5 + 1.9)
    heart = smooth(hb * R + 6, hb * R - 6, r)
    col = col * (1 - 0.16 * heart[..., None])
    # weathering of a block that stands out in the yard: grey, blotched, darker stains
    wx = fbm(rng, (S, S), (90, 30, 8), (0.5, 0.3, 0.2))
    wthr = 0.25 + 0.4 * smooth(0.35, 0.75, wx)
    col = lerp(col, SILVER * (0.85 + 0.2 * detail["tone"][..., None]), wthr)
    stain = smooth(0.66, 0.85, fbm(rng, (S, S), (40, 10), (0.6, 0.4)))
    col = col * (1 - 0.12 * stain[..., None])
    # the outside of the disc and its rind: bark
    bh, bc, fis = bark_field(rng, (S, S))
    bark = rc > Rb - 0.05 * INNER
    camb = (rc > Rb - 0.05 * INNER - 5) & ~bark
    col = np.where(bark[..., None], bc, col)
    col = np.where(camb[..., None], lerp(col, CAMBIUM, 0.55), col)
    h = np.where(bark, 0.15 * bh, 0.6 + h)
    rough = np.where(bark, 0.96, rough)
    # surface checks from the rim, wide and dark, and a heart check or two
    ck = checks(rng, r, th, R, 6, True)
    ck = np.maximum(ck, checks(rng, r, th, R, 2, False))
    ck = ck * ~bark
    col = col * (1 - 0.85 * ck[..., None])
    h = h - 0.35 * ck
    rough = np.maximum(rough, ck)
    # crosscut kerf: shallow arcs across the face
    a = rng.uniform(0, 3.14)
    kerf = np.sin((np.cos(a) * xx + np.sin(a) * yy + 0.0008 * (xx - c0) ** 2) * 0.9)
    h = h + 0.005 * kerf * ~bark
    # the scores of an axe: short grooves, dark in the cut, crushed pale either side
    face = ~bark
    for _ in range(int(rng.integers(5, 9))):
        ox, oy = c0 + rng.uniform(-0.5, 0.5) * R, c0 + rng.uniform(-0.5, 0.5) * R
        a = rng.uniform(0, 3.14)
        L = rng.uniform(0.2, 0.45) * R
        along = np.cos(a) * (xx - ox) + np.sin(a) * (yy - oy)
        acr = -np.sin(a) * (xx - ox) + np.cos(a) * (yy - oy)
        inl = np.clip(1 - np.abs(along) / (L / 2), 0, 1) ** 0.4
        cut = smooth(2.6, 0.6, np.abs(acr)) * inl * face
        crush = smooth(9.0, 2.0, np.abs(acr)) * inl * face * (1 - cut)
        col = col * (1 - 0.6 * cut[..., None]) * (1 + 0.1 * crush[..., None])
        h = h - 0.25 * cut + 0.02 * crush
    dirt = fbm(rng, (S, S), (80, 20), (0.7, 0.3))
    col = col * (0.86 + 0.22 * dirt[..., None])
    return col, ndimage.gaussian_filter(h, 0.6), rough, 12.0, (0.55, 0.45)


# ------------------------------------------------------------------ log bark


def log_bark(seed):
    """Oak or hickory bark: long ridges along x, splitting and joining over deep furrows,
    broken across into blocks here and there."""
    rng = np.random.default_rng(seed)
    S = CELL
    # furrows are the contour lines of noise stretched along the log: they interlace,
    # part and join as oak bark's do; a finer set between them
    n1 = fbm(rng, (S, S), ((9, 120), (4, 50)), (0.7, 0.3))
    n2 = fbm(rng, (S, S), ((4, 60), (2, 25)), (0.7, 0.3))
    wv = fbm(rng, (S, S), ((30, 30),), (1.0,))
    f1 = smooth(0.05 + 0.04 * wv, 0.0, np.abs(n1 - 0.5))
    f2 = smooth(0.035, 0.0, np.abs(n2 - 0.5)) * 0.7
    big = n1
    furrow = np.clip(np.maximum(f1, f2), 0, 1)        # 1 deep in a furrow
    plate = fbm(rng, (S, S), ((2, 26), (1, 8), (0.5, 2)), (0.5, 0.3, 0.2))
    # blocks: short cracks across a ridge, where the bark has broken as the log swelled
    cross = smooth(0.72, 0.8, noise(rng, (S, S), (16, 2.2))) * (1 - furrow)
    grit = noise(rng, (S, S), 0.8)
    ridge = 1 - furrow
    h = 0.85 * ridge + 0.14 * plate * ridge - 0.25 * cross + 0.05 * grit
    c = lerp(BARK_MID, BARK_GREY, smooth(0.35, 0.8, plate))
    c = lerp(c, BARK_DARK * 0.85, furrow * 0.9)
    c = c * (1 - 0.35 * cross[..., None]) * (0.86 + 0.24 * grit[..., None])
    tone = fbm(rng, (S, S), (150, 50), (0.6, 0.4))
    c = c * (0.85 + 0.25 * tone[..., None])
    lich = noise(rng, (S, S), 3.0)
    lm = smooth(0.78, 0.84, lich) * ridge * smooth(0.45, 0.65, tone)
    c = lerp(c, np.array([0.58, 0.60, 0.48]), lm * 0.7)
    moss = smooth(0.7, 0.8, fbm(rng, (S, S), (20, 6), (0.6, 0.4))) * furrow
    c = lerp(c, np.array([0.24, 0.27, 0.15]), moss * 0.45)
    rough = np.clip(0.92 + 0.06 * furrow, 0, 1)
    return c, ndimage.gaussian_filter(h, 0.7), rough, 14.0, (0.5, 0.5)


# ------------------------------------------------------------------ split face


def split_face(seed):
    rng = np.random.default_rng(seed)
    S = CELL
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    hgt, fib, tone, lift = split_field(rng, (S, S))
    wood = WOODS[0]
    base = lerp(np.asarray(wood["heart"], np.float32), np.asarray(wood["sap"], np.float32),
                smooth(0.25, 0.75, tone))
    c = base * (0.76 + 0.36 * fib[..., None]) * (1 + 0.14 * lift[..., None])
    weather = smooth(0.3, 0.8, fbm(rng, (S, S), ((40, 200), (12, 60)), (0.6, 0.4)))
    c = lerp(c, SILVER * (0.88 + 0.18 * fib[..., None]), weather * 0.7)
    # long checks along the grain
    for _ in range(int(rng.integers(3, 7))):
        y0 = rng.uniform(0, S)
        x0 = rng.uniform(-200, S)
        L = rng.uniform(200, 700)
        wv = np.sin(xx * rng.uniform(0.004, 0.012) + rng.uniform(0, 6.28)) * rng.uniform(2, 8)
        inl = np.clip(1 - np.abs(xx - (x0 + L / 2)) / (L / 2), 0, 1)
        w = 0.5 + 2.4 * inl
        ck = smooth(w + 0.8, w * 0.3, np.abs(yy - y0 - wv)) * (inl > 0)
        c = c * (1 - 0.75 * ck[..., None])
        hgt = hgt - 0.3 * ck
    dirt = fbm(rng, (S, S), (70, 16), (0.7, 0.3))
    c = c * (0.86 + 0.2 * dirt[..., None])
    rough = 0.86 + 0.08 * weather
    return c, ndimage.gaussian_filter(hgt, 0.5), rough, 9.0, (0.5, 0.5)


BUILDERS = {"rick_ends_a": lambda: rick_ends(SEED + 1), "rick_ends_b": lambda: rick_ends(SEED + 2),
            "rick_sides": lambda: rick_sides(SEED + 3), "round_end": lambda: round_end(SEED + 4),
            "log_bark": lambda: log_bark(SEED + 5), "split_face": lambda: split_face(SEED + 6)}


def build_cell(name):
    col, h, rough, strength, (ao_lo, ao_k) = BUILDERS[name]()
    h = norm01(h)
    ao = occlusion(h)
    # bake the occlusion into the colour as a photograph shows it: deep where a stick
    # end stands in front of the dark of the pile
    col = col * (ao_lo + ao_k * ao[..., None])
    return to_u8(col), normal_from_height(h, strength), np.stack(
        [to_u8(ao), to_u8(np.clip(rough, 0, 1)), np.zeros(h.shape, np.uint8)], -1), h


def main(argv=None) -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.parse_args(argv)
    out = LIB / SID
    out.mkdir(parents=True, exist_ok=True)
    W, H = COLS * CELL, ROWS * CELL
    sheets = {k: np.zeros((H, W, 3), np.uint8) for k in ("basecolor", "normal_gl", "orm")}
    height = np.zeros((H, W), np.uint16)
    cells = {}
    for name, cx, cy in LAYOUT:
        base, nrm, orm, h = build_cell(name)
        ys, xs = slice(cy * CELL, (cy + 1) * CELL), slice(cx * CELL, (cx + 1) * CELL)
        sheets["basecolor"][ys, xs] = base
        sheets["normal_gl"][ys, xs] = nrm
        sheets["orm"][ys, xs] = orm
        height[ys, xs] = (h * 65535.0 + 0.5).astype(np.uint16)
        cells[name] = [int((cx * CELL + GUTTER) * OUT), int((cy * CELL + GUTTER) * OUT),
                       int(INNER * OUT), int(INNER * OUT)]
        print(f"  cell {name}")
    web = {}
    Wo, Ho = int(W * OUT), int(H * OUT)
    for k, arr in sheets.items():
        im = Image.fromarray(arr, "RGB").resize((Wo, Ho), Image.LANCZOS)
        if k == "normal_gl":
            # filtered normals shorten; put them back to unit length
            n = np.asarray(im, np.float32) / 127.5 - 1.0
            n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-6)
            im = Image.fromarray(to_u8(n * 0.5 + 0.5), "RGB")
        im.save(out / f"{SID}_{k}.png", optimize=True)
        name = f"{SID}_{k}_web.jpg"
        opts = dict(quality=90, subsampling=0 if k != "basecolor" else 2)
        try:
            im.save(out / name, optimize=True, **opts)
        except OSError:
            im.save(out / name, **opts)
        web[k] = name
    Image.fromarray(height).resize((Wo, Ho), Image.BILINEAR).save(out / f"{SID}_height16.png")
    rough_mean = float(sheets["orm"][..., 1].mean() / 255.0)
    sheet = {
        "id": SID,
        "group": "yard_wood",
        "span_m": CELL_M,
        "cell_m": CELL_M,
        "mean_roughness": round(rough_mean, 3),
        "resolution_px": [Wo, Ho],
        "web_resolution_px": [Wo, Ho],
        "drawn_px": [W, H],
        "px_per_m": round(PX_M * OUT, 2),
        "cells": cells,
        "cells_note": "[x, y, w, h] in image pixels, origin top left, of the part of each cell a face "
                      "may sample (the inner 480 px; a 16 px gutter of the same picture round it). "
                      "Each is cell_m of wood square.",
        "orientation": "rick_sides, log_bark and split_face: the grain along image x; rick_ends and "
                       "round_end: end grain, no axis",
        "note": "The yard woodpiles' wood: split billet ends racked in a rick (two cells), the sticks "
                "along their length, a sawn round's end, oak/hickory log bark, and a split face along the "
                "grain. Woods of the 1812 groves (oak, hickory, ash, elm), most a season stacked and "
                "greying. Reconstructed appearance.",
        "confidence": "reconstructed appearance (L-t3474-yard-wood-surfaces)",
        "color_space": {"basecolor": "sRGB", "normal_gl": "linear",
                        "orm": "linear; R=AO G=Roughness B=Metallic", "height16": "linear 16-bit"},
        "web": web,
        "seamless": False,
        "generator_seed": SEED,
        "generation_method": "deterministic procedural synthesis (tools/generate_yard_wood_pbr.py); "
                             "no photograph sampled",
    }
    (out / "material.json").write_text(json.dumps(sheet, indent=2) + "\n")
    manifest = {"library": "yard_wood_pbr", "version": "1.0.0", "ticket": "T-3474", "materials": [SID]}
    (LIB / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {SID} ({Wo}x{Ho}, drawn at {W}x{H})")


if __name__ == "__main__":
    main()
