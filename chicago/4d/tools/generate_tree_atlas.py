#!/usr/bin/env python3
"""The species leaf and bark atlases the grown trees draw from (T-2743).

    python3 tools/generate_tree_atlas.py                 write assets/textures/trees/*.webp
    python3 tools/generate_tree_atlas.py --masters       also the lossless PNG masters
    python3 tools/generate_tree_atlas.py --sheet PATH    also a contact sheet, at PATH

WHAT IT MAKES. Two atlases, painted from code. One photograph is sampled: the
elm's blades take their surface from a CC BY 4.0 photograph of an American elm
leaf (T-3247, data/sources/bioimages_ulmus_americana_11688.json; credited in
assets/LICENSES.md). Every outline, twig and placement is still drawn here:

  leaf_atlas.png       2048 x 3072 RGBA, 4 x 6 tiles of 512. Per leaf family two
                       tiles: a SPRAY (one twig and its leaves, for the near
                       cards) and a CLUMP (several sprays massed, for the mid and
                       far cards). Families and their tiles are
                       renderers/web/js/tree-model.js LEAF_TILES. The sixth row
                       holds the bare winter elm's twig, a spray and a tuft
                       (TWIG_TILES, tree-model.js TWIG_TILE; T-1934).
  bark_basecolor.png   2048 x 1024 RGB, 4 x 2 tiles of 512, each tileable in both
  bark_normal.png      axes, with its tangent-space normal map (OpenGL, +Y up).
                       Tiles are tree-model.js BARK_TILES.

WHAT THEY ARE JUDGED AGAINST. The botanical habit of each species' leaf and
bark (the species' ordinary habit; docs/LIBERTIES.md L-tree-architecture-2743);
they are reconstructions of what a species looks like, not
evidence about any tree that stood in 1812 or 1835. The leaf tiles are painted
in a near-neutral green so the zone records' July colours, carried as vertex
colour, stay in charge of the hue (the rule tree-surface.js kept since T-2015).

DETERMINISM. Every random draw comes from a seeded numpy Generator, so the same
code writes the same pixels; the output is committed and the renderer loads the
committed files.
"""
from __future__ import annotations

import argparse
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'textures', 'trees')
TILE = 512
SS = 3  # supersampling for the leaf painting

# --------------------------------------------------------------------------- #
# tileable noise                                                              #
# --------------------------------------------------------------------------- #


def lattice_noise(rng, size_x, size_y, cells_x, cells_y):
    """Value noise that wraps at both edges: a random lattice interpolated
    with a smooth step, the lattice indices taken modulo its size."""
    grid = rng.random((cells_y, cells_x))
    xs = np.arange(size_x) * cells_x / size_x
    ys = np.arange(size_y) * cells_y / size_y
    x0 = np.floor(xs).astype(int)
    y0 = np.floor(ys).astype(int)
    fx = xs - x0
    fy = ys - y0
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    x1 = (x0 + 1) % cells_x
    y1 = (y0 + 1) % cells_y
    x0 %= cells_x
    y0 %= cells_y
    a = grid[np.ix_(y0, x0)]
    b = grid[np.ix_(y0, x1)]
    c = grid[np.ix_(y1, x0)]
    d = grid[np.ix_(y1, x1)]
    top = a + (b - a) * fx[None, :]
    bot = c + (d - c) * fx[None, :]
    return top + (bot - top) * fy[:, None]


def fbm(rng, size, cells, octaves=5, aspect=(1, 1), gain=0.5):
    """Fractal sum of wrapping value noise. `aspect` stretches the lattice
    (more cells across than down gives vertical grain)."""
    out = np.zeros((size, size))
    amp = 1.0
    total = 0.0
    cx, cy = cells * aspect[0], cells * aspect[1]
    for _ in range(octaves):
        out += amp * lattice_noise(rng, size, size, max(1, int(cx)), max(1, int(cy)))
        total += amp
        amp *= gain
        cx *= 2
        cy *= 2
    return out / total


def warp_sample(field, dx, dy):
    """Sample `field` at (x + dx, y + dy) with wrap, bilinear."""
    h, w = field.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    sx = (xx + dx) % w
    sy = (yy + dy) % h
    x0 = np.floor(sx).astype(int)
    y0 = np.floor(sy).astype(int)
    fx = sx - x0
    fy = sy - y0
    x1 = (x0 + 1) % w
    y1 = (y0 + 1) % h
    a = field[y0, x0]
    b = field[y0, x1]
    c = field[y1, x0]
    d = field[y1, x1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def worley(rng, size, n, stretch=(1.0, 1.0)):
    """Wrapping cellular noise: F1, F2 and the cell id, with cells stretched by
    `stretch` (x, y) so plates run long up the trunk."""
    pts = rng.random((n, 2)) * size
    yy, xx = np.mgrid[0:size, 0:size].astype(float)
    f1 = np.full((size, size), 1e9)
    f2 = np.full((size, size), 1e9)
    ids = np.zeros((size, size), dtype=int)
    for i, (px, py) in enumerate(pts):
        dx = np.abs(xx - px)
        dx = np.minimum(dx, size - dx) / stretch[0]
        dy = np.abs(yy - py)
        dy = np.minimum(dy, size - dy) / stretch[1]
        d = np.sqrt(dx * dx + dy * dy)
        closer = d < f1
        f2 = np.where(closer, f1, np.minimum(f2, d))
        ids = np.where(closer, i, ids)
        f1 = np.where(closer, d, f1)
    return f1, f2, ids


def normalise(a):
    lo, hi = np.percentile(a, 0.5), np.percentile(a, 99.5)
    return np.clip((a - lo) / max(1e-9, hi - lo), 0, 1)


def normal_map(height, strength):
    """Tangent-space normal from a wrapping height field (OpenGL: +Y up)."""
    gx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5
    gy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5
    nx = -gx * strength
    ny = gy * strength  # image rows run down; GL normal maps point +Y up
    nz = np.ones_like(height)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / l, ny / l, nz / l], axis=-1)
    return ((n * 0.5 + 0.5) * 255).round().astype(np.uint8)


# --------------------------------------------------------------------------- #
# bark                                                                        #
# --------------------------------------------------------------------------- #


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def blur(a, r):
    return gaussian_filter(a, r, mode='wrap')


def worley_warped(rng, n, stretch, wx, wy):
    """Wrapping cellular noise sampled through a warped domain: F1, F2, the
    cell id and each texel's offset from its cell's site."""
    pts = rng.random((n, 2)) * TILE
    yy, xx = np.mgrid[0:TILE, 0:TILE].astype(float)
    xx = (xx + wx) % TILE
    yy = (yy + wy) % TILE
    f1 = np.full((TILE, TILE), 1e9)
    f2 = f1.copy()
    ids = np.zeros((TILE, TILE), int)
    rel = np.zeros((TILE, TILE, 2))
    for i, (px, py) in enumerate(pts):
        dx = (xx - px + TILE / 2) % TILE - TILE / 2
        dy = (yy - py + TILE / 2) % TILE - TILE / 2
        d = np.hypot(dx / stretch[0], dy / stretch[1])
        c = d < f1
        f2 = np.where(c, f1, np.minimum(f2, d))
        ids = np.where(c, i, ids)
        rel[..., 0] = np.where(c, dx, rel[..., 0])
        rel[..., 1] = np.where(c, dy, rel[..., 1])
        f1 = np.where(c, d, f1)
    return f1, f2, ids, rel


def cracks(rng, count, maxlen):
    """Short wandering cross-cracks that break ridges into segments."""
    im = Image.new('L', (TILE * 3, TILE * 3), 0)
    d = ImageDraw.Draw(im)
    for _ in range(count):
        cx, cy = rng.random() * TILE, rng.random() * TILE
        L = maxlen * (0.4 + rng.random() * 0.6)
        a = (rng.random() - 0.5) * 0.7
        w = 1 + int(rng.random() * 3)
        for ox in (0, TILE, 2 * TILE):
            for oy in (0, TILE, 2 * TILE):
                pts = []
                x, y = cx + ox - math.cos(a) * L / 2, cy + oy - math.sin(a) * L / 2
                for _k in range(7):
                    pts.append((x, y))
                    aa = a + (rng.random() - 0.5) * 0.8
                    x += math.cos(aa) * L / 6
                    y += math.sin(aa) * L / 6
                d.line(pts, fill=255, width=w)
    return np.asarray(im).astype(float)[TILE:2 * TILE, TILE:2 * TILE] / 255


def bark_net(rng, n, stretch, warp, ridge_w, depth_w, mode, pal, lichen=0.2, rough=0.3,
             ncrack=0, cracklen=0, jitter=0.4):
    """Ridge-and-furrow bark from a warped, stretched cellular field.

    mode 'net':    the RIDGES are the cell borders and the furrows the cells'
                   hearts, so ridges interlace round lens-shaped furrows the way
                   a cottonwood's, an elm's or a bur oak's do.
    mode 'plates': the plates are the cells and the seams their borders, each
                   plate tilted so one edge lifts (shaggy strips).
    Colour runs furrow floor -> furrow wall -> ridge face, with a weathering
    mottle, grey-green lichen on the ridges, ambient occlusion from the relief
    and a little of the relief's own light baked in so a trunk still reads at
    forty metres, where the normal map has mipped away."""
    wx = (fbm(rng, TILE, 4, 4) - 0.5) * warp[0]
    wy = (fbm(rng, TILE, 3, 4) - 0.5) * warp[1]
    f1, f2, ids, rel = worley_warped(rng, n, stretch, wx, wy)
    edge = f2 - f1
    wob = fbm(rng, TILE, 12, 3, aspect=(1, 3))
    rag = fbm(rng, TILE, 48, 3, aspect=(1, 2))
    edge = edge * (1 - jitter / 2 + jitter * wob) + (rag - 0.5) * ridge_w * 1.2
    fine = fbm(rng, TILE, 40, 3, aspect=(1, 4))
    fib = fbm(rng, TILE, 32, 2, aspect=(8, 0.6))
    if mode == 'net':
        top = 1 - smooth(ridge_w * 0.6, ridge_w * 1.4, edge)
        floor = 1 - smooth(ridge_w, ridge_w + depth_w, edge)
        fis = fbm(rng, TILE, 20, 3, aspect=(2, 9))
        top = top * (1 - 0.55 * smooth(0.62, 0.74, fis))
        hgt = 0.6 * top + 0.4 * floor
    else:
        plate = smooth(ridge_w * 0.5, ridge_w * 1.5, edge)
        tdir = rng.random((n, 2)) - 0.5
        tilt = (rel[..., 0] * tdir[ids, 0] + rel[..., 1] * tdir[ids, 1] / stretch[1]) / (TILE / math.sqrt(n))
        hgt = plate * (0.8 + 0.2 * rng.random(n)[ids]) + 0.25 * np.clip(tilt, -1, 1) * plate
    hgt = hgt + (fine - 0.5) * rough * hgt + (fib - 0.5) * 0.10
    if ncrack:
        c = blur(cracks(rng, ncrack, cracklen), 0.8)
        hgt = hgt * (1 - 0.7 * np.clip(c / max(1e-6, c.max()) * 2, 0, 1))
    hgt = normalise(blur(hgt, 0.7))
    ao = 0.3 + 0.7 * normalise(blur(hgt, 5))
    fb, fw, rf, rf2 = [np.array(q, float) for q in pal]
    t = hgt[..., None]
    col = np.where(t < 0.45, fb + (fw - fb) * (t / 0.45), fw + (rf - fw) * np.clip((t - 0.45) / 0.35, 0, 1))
    m = fbm(rng, TILE, 5, 5)[..., None]
    col = col + (rf2 - rf) * np.clip((m - 0.45) * 2.2, 0, 1) * t
    col = col * (0.55 + 0.45 * ao[..., None])
    gx = np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)
    gy = np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)
    lam = np.clip(0.8 - (gx * 0.8 + gy * 0.4) * 6, 0.4, 1.25)
    col = col * (0.72 + 0.28 * lam)[..., None]
    if lichen:
        lm = smooth(0.56, 0.72, fbm(rng, TILE, 7, 5))[..., None] * smooth(0.55, 0.85, hgt)[..., None]
        col = col * (1 - lichen * lm) + np.array([158, 166, 142.]) * lichen * lm
    col = col + (fbm(rng, TILE, 96, 2) - 0.5)[..., None] * 18
    return hgt, np.clip(col, 0, 255)


# Per kind: the cell count and stretch set the ridges' length and spacing on a
# tile that covers a circumference and a half of wood; the palettes are
# furrow floor, furrow wall, ridge face and its weathered variant.
NET_KINDS = {
    # cottonwood, black willow, Lombardy poplar: thick grey ridges interlacing
    # round deep dark furrows
    'furrowed': dict(n=60, stretch=(1, 4.5), warp=(20, 40), ridge_w=6.0, depth_w=12, mode='net',
                     pal=[(30, 24, 19), (88, 72, 58), (150, 144, 134), (126, 120, 110)],
                     lichen=0.25, ncrack=30, cracklen=12),
    # elm, ash: a finer diamond net, buff-orange in the furrows
    'interlaced': dict(n=150, stretch=(1, 3.2), warp=(14, 24), ridge_w=4.2, depth_w=7, mode='net',
                       pal=[(92, 70, 50), (132, 106, 78), (146, 138, 126), (120, 112, 102)],
                       lichen=0.18, ncrack=60, cracklen=8),
    # bur oak, black oak, black walnut: dark ridges cut across into blocks
    'blocky': dict(n=100, stretch=(1, 2.3), warp=(12, 18), ridge_w=6.5, depth_w=9, mode='net',
                   pal=[(20, 17, 14), (58, 50, 42), (112, 106, 98), (88, 82, 74)],
                   lichen=0.22, rough=0.45, ncrack=160, cracklen=20),
    # white oak, swamp white oak, basswood, red oak: pale scaly ridges, shallow furrows
    'plated': dict(n=210, stretch=(1, 2.2), warp=(10, 16), ridge_w=4.2, depth_w=4, mode='net',
                   pal=[(104, 99, 92), (138, 132, 124), (186, 182, 174), (160, 156, 146)],
                   lichen=0.32, rough=0.35, ncrack=120, cracklen=12),
    # silver maple, sugar maple, shagbark hickory, ironwood: long strips lifting
    'shaggy': dict(n=50, stretch=(1, 9), warp=(8, 40), ridge_w=2.0, depth_w=0, mode='plates',
                   pal=[(44, 38, 34), (102, 94, 86), (164, 160, 152), (140, 134, 126)],
                   lichen=0.15, rough=0.2),
    # hackberry, black ash: corky warts on a low net
    'corky': dict(n=300, stretch=(1, 1.6), warp=(20, 20), ridge_w=4.0, depth_w=4, mode='net',
                  pal=[(98, 93, 86), (124, 118, 110), (166, 162, 152), (142, 138, 128)],
                  lichen=0.12, rough=0.55),
}


def colourise(h, dark, light, rng, mottle=0.08):
    """Map a height field to colour, with a weathering mottle (smooth bark)."""
    m = fbm(rng, TILE, 6, 4)
    t = np.clip(h + (m - 0.5) * mottle * 2, 0, 1)[..., None]
    dark = np.array(dark, float)[None, None, :]
    light = np.array(light, float)[None, None, :]
    return dark + (light - dark) * t


def bark_smooth(rng):
    """Aspen, balsam poplar, young limbs: smooth bark with horizontal lenticels
    and dark branch scars."""
    h = 0.6 + 0.08 * fbm(rng, TILE, 8, 4)
    col = colourise(h, (120, 122, 112), (196, 198, 186), rng, 0.20)
    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))
    hgt = Image.fromarray((h * 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    dh = ImageDraw.Draw(hgt)
    for _ in range(240):
        cx = rng.random() * TILE
        cy = rng.random() * TILE
        w = 3 + rng.random() * 12
        for ox in (-TILE, 0, TILE):
            for oy in (-TILE, 0, TILE):
                box = [cx + ox - w, cy + oy - 0.8, cx + ox + w, cy + oy + 1.2]
                d.ellipse(box, fill=(70, 66, 58))
                dh.ellipse(box, fill=90)
    for _ in range(8):
        cx = rng.random() * TILE
        cy = rng.random() * TILE
        w = 10 + rng.random() * 16
        for ox in (-TILE, 0, TILE):
            for oy in (-TILE, 0, TILE):
                d.polygon([(cx + ox - w, cy + oy), (cx + ox, cy + oy - w * 0.6),
                           (cx + ox + w, cy + oy), (cx + ox, cy + oy + w * 0.9)], fill=(40, 37, 34))
                dh.polygon([(cx + ox - w, cy + oy), (cx + ox, cy + oy - w * 0.6),
                            (cx + ox + w, cy + oy), (cx + ox, cy + oy + w * 0.9)], fill=40)
    col = np.asarray(img).astype(float)
    h = np.asarray(hgt).astype(float) / 255
    return h, col


def bark_sycamore(rng):
    """Sycamore: thin bark flaking in jigsaw patches — brown, grey-green and the
    cream under-bark — the one tile whose colour is its own."""
    f1, f2, ids = worley(rng, TILE, 60, stretch=(1.3, 1.0))
    which = rng.random(60)[ids]
    palette = np.array([(128, 112, 92), (150, 156, 132), (226, 222, 204), (196, 192, 172)], float)
    k = np.clip((which * 4).astype(int), 0, 3)
    col = palette[k]
    edge = np.clip((f2 - f1) / 4.0, 0, 1)
    h = 0.5 + 0.15 * (k >= 2) + 0.25 * edge
    col = col * (0.88 + 0.12 * fbm(rng, TILE, 18, 3))[..., None]
    col = col * (0.75 + 0.25 * edge)[..., None]
    return normalise(h), col


BARK_ORDER = ['furrowed', 'interlaced', 'blocky', 'plated', 'shaggy', 'smooth', 'sycamore', 'corky']
BARK_STRENGTH = {'furrowed': 6.0, 'interlaced': 5.0, 'blocky': 7.0, 'plated': 4.5, 'shaggy': 5.0,
                 'smooth': 2.0, 'sycamore': 2.5, 'corky': 5.0}


def make_bark(seed):
    rng = np.random.default_rng(seed)
    colour = np.zeros((TILE * 2, TILE * 4, 3), np.uint8)
    normal = np.zeros((TILE * 2, TILE * 4, 3), np.uint8)
    for i, kind in enumerate(BARK_ORDER):
        if kind in NET_KINDS:
            h, col = bark_net(rng, **NET_KINDS[kind])
        else:
            h, col = (bark_smooth if kind == 'smooth' else bark_sycamore)(rng)
        x0 = (i % 4) * TILE
        y0 = (i // 4) * TILE
        colour[y0:y0 + TILE, x0:x0 + TILE] = np.clip(col, 0, 255).astype(np.uint8)
        normal[y0:y0 + TILE, x0:x0 + TILE] = normal_map(h * 255 / 40, BARK_STRENGTH[kind])
    return colour, normal


# --------------------------------------------------------------------------- #
# leaves                                                                      #
# --------------------------------------------------------------------------- #


def toothed(points, teeth, depth):
    """Add teeth along an outline: every other vertex pushed out along its normal."""
    out = []
    n = len(points)
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        for k in range(teeth):
            t = k / teeth
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            if k % 2 == 1:
                nx, ny = (y1 - y0), -(x1 - x0)
                l = math.hypot(nx, ny) or 1
                x += nx / l * depth
                y += ny / l * depth
            out.append((x, y))
    return out


def outline(family, rng):
    """A leaf blade in leaf space: base at (0, 0), tip at (0, 1), as a polygon."""
    pts = []
    if family == 'poplar':  # cottonwood: deltoid, truncate base, coarse teeth
        for i in range(31):
            t = i / 30
            w = 0.48 * (1 - t) ** 0.9 * (0.35 + 0.65 * min(1, t * 5))
            pts.append((-w, t * 1.0 if t > 0.05 else t * 0.4))
        side = [(-x, y) for x, y in reversed(pts)]
        pts = toothed(pts + side, 2, 0.022)
    elif family == 'aspen':
        for i in range(40):
            a = math.pi * 2 * i / 40
            pts.append((0.45 * math.sin(a), 0.48 - 0.46 * math.cos(a)))
        pts = toothed(pts, 2, 0.012)
    elif family == 'willow':
        for i in range(31):
            t = i / 30
            w = 0.085 * math.sin(math.pi * t) ** 0.8 * (1.1 - t * 0.4)
            pts.append((-w, t))
        side = [(-x, y) for x, y in reversed(pts)]
        pts = toothed(pts + side, 2, 0.006)
    elif family == 'elm':
        for i in range(31):
            t = i / 30
            w = 0.27 * math.sin(math.pi * min(1, t * 1.05)) ** 0.75
            pts.append((-w * 1.1, t))
        side = [(w * 0.95, y) for (w, y) in reversed([(abs(x), y) for x, y in pts])]
        pts = toothed(pts + side, 2, 0.02)
    elif family == 'maple':  # silver maple: five deep narrow lobes
        lobes = [(-0.95, 0.55), (-0.55, 0.92), (0.0, 1.0), (0.55, 0.92), (0.95, 0.55)]
        for i, (lx, ly) in enumerate(lobes):
            ang = math.atan2(lx, ly)
            r = 0.52 if i in (0, 4) else 0.62
            tip = (math.sin(ang) * r, 0.30 + math.cos(ang) * r)
            sinus = 0.17
            a0 = ang - 0.30
            a1 = ang + 0.30
            pts += [(math.sin(a0) * sinus, 0.30 + math.cos(a0) * sinus),
                    (math.sin(ang - 0.10) * r * 0.75, 0.30 + math.cos(ang - 0.10) * r * 0.75),
                    tip,
                    (math.sin(ang + 0.10) * r * 0.75, 0.30 + math.cos(ang + 0.10) * r * 0.75),
                    (math.sin(a1) * sinus, 0.30 + math.cos(a1) * sinus)]
        pts = [(0, 0.0)] + pts
        pts = toothed(pts, 2, 0.018)
    elif family in ('oak_round', 'oak_pointed'):
        # Bur and white oak: rounded lobes, the bur oak's upper half broad and
        # its lower lobes cut nearly to the midrib. Red and black oak: fewer,
        # deeper lobes ending in bristle points.
        lobes = 3.5 if family == 'oak_round' else 3.0
        left = []
        for i in range(61):
            t = i / 60
            env = 0.40 * math.sin(math.pi * min(1, 0.06 + t * 0.97)) ** 0.6
            if family == 'oak_round':
                env *= 0.65 + 0.55 * t
                ph = abs(math.sin(math.pi * lobes * t)) ** 0.5
                w = env * (0.30 + 0.70 * ph)
            else:
                ph = 1 - abs(((lobes * t) % 1) * 2 - 1)
                w = env * (0.28 + 0.85 * ph ** 2.2)
            left.append((-w, t))
        side = [(-x, y) for x, y in reversed(left)]
        pts = left + side
    elif family == 'heart':  # basswood
        for i in range(36):
            t = i / 35
            w = 0.50 * math.sin(math.pi * (0.12 + t * 0.88)) ** 0.6
            pts.append((-w * 1.05, t))
        side = [(abs(x) * 0.9, y) for x, y in reversed(pts)]
        pts = toothed(pts + side, 2, 0.016)
    else:  # one leaflet of a compound leaf
        for i in range(25):
            t = i / 24
            w = 0.20 * math.sin(math.pi * t) ** 0.8
            pts.append((-w, t))
        side = [(-x, y) for x, y in reversed(pts)]
        pts = toothed(pts + side, 2, 0.008)
    return pts


def draw_leaf(img, draw, cx, cy, length, angle, family, rng, shade, under=False, foreshort=1.0):
    """One blade, turned, foreshortened across its width (a leaf seen edge-on is
    a sliver), shaded light-to-dark across the midrib, with veins."""
    ca, sa = math.cos(angle), math.sin(angle)

    def tr(x, y):
        x *= foreshort
        return (cx + (x * ca - y * sa) * length, cy - (x * sa + y * ca) * length)

    if family == 'compound':
        # A rachis with paired leaflets and a terminal one.
        rach = [tr(0, 0), tr(0, 1.0)]
        draw.line(rach, fill=(96, 104, 70, 255), width=max(1, int(length * 0.012)))
        for k in range(4):
            y = 0.25 + k * 0.2
            for side in (-1, 1):
                a = angle + side * (1.0 + rng.random() * 0.2)
                x0, y0 = tr(0, y)
                sub = outline('compound', rng)
                lc = shade * (0.9 + rng.random() * 0.2)
                poly = [(x0 + (px * math.cos(a) - py * math.sin(a)) * length * 0.36,
                         y0 - (px * math.sin(a) + py * math.cos(a)) * length * 0.36) for px, py in sub]
                draw.polygon(poly, fill=leaf_rgb(lc, rng, under))
        sub = outline('compound', rng)
        x0, y0 = tr(0, 0.95)
        poly = [(x0 + (px * ca - py * sa) * length * 0.38, y0 - (px * sa + py * ca) * length * 0.38) for px, py in sub]
        draw.polygon(poly, fill=leaf_rgb(shade, rng, under))
        return
    pts = outline(family, rng)
    poly = [tr(x, y) for x, y in pts]
    base = leaf_rgb(shade, rng, under)
    if family == 'elm' and photo_fill(img, poly, tr, base):
        # the photograph carries the veins; the midrib is drawn as the painted blades' is
        if length > 30:
            vein = tuple(min(255, int(c * 1.18 + 10)) for c in base[:3]) + (255,)
            draw.line([tr(0, -0.12), tr(0, 0.96)], fill=vein, width=max(1, int(length * 0.014)))
        return
    draw.polygon(poly, fill=base)
    # The half of the blade turned from the light is darker: a fold along the midrib.
    half = [tr(min(0, x), y) for x, y in pts if x <= 0] + [tr(0, 1), tr(0, 0)]
    if len(half) > 3:
        dk = tuple(int(c * 0.86) for c in base[:3]) + (255,)
        draw.polygon(half, fill=dk)
    # Midrib and a few veins, a touch lighter than the blade.
    vein = tuple(min(255, int(c * 1.18 + 10)) for c in base[:3]) + (255,)
    if length > 30:
        draw.line([tr(0, -0.12), tr(0, 0.96)], fill=vein, width=max(1, int(length * 0.014)))
    if family not in ('willow',) and length > 54:
        for k in range(1, 6):
            y = k / 6.5
            for s in (-1, 1):
                draw.line([tr(0, y), tr(s * 0.30, y + 0.16)], fill=vein, width=max(1, int(length * 0.006)))


# T-3247 — THE ELM'S BLADE IS PHOTOGRAPHED. One American elm leaf, its whole upper
# surface on a dark ground (Steven J. Baskauf, Bioimages, CC BY 4.0), is cut out
# and laid into each painted elm outline along the blade's own axis, so the
# blade carries the leaf's real pinnate veins, its fold and its mottle. Only the
# photograph's LIGHTNESS is taken: each blade keeps the painted near-neutral
# green leaf_rgb gives it (so the zone records' July colour stays in charge), and
# the painted blade's random draws are made unchanged, so every other family's
# tile is byte-identical.
ELM_LEAF_PHOTO = os.path.join(ROOT, 'data', 'sources', 'assets', 'bioimages_ulmus_americana_11688',
                              'ulmus_americana_leaf_11688.jpg')
_photo_blade = {}


def photo_blade():
    """The photograph's lightness as a ratio to its blade's mean, at a pyramid of
    sizes, with the blade's base, axis and length in each. Outside the blade the
    nearest blade texel's ratio is carried out, so an outline a little wider than
    the photographed leaf is still filled with leaf."""
    if _photo_blade:
        return _photo_blade
    from scipy import ndimage as ndi
    a = np.asarray(Image.open(ELM_LEAF_PHOTO).convert('RGB')).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # the blade is the one large region clearly greener than it is red or blue
    m = ndi.binary_opening((g - np.maximum(r, b) * 0.85 > 28) & (g > 85), iterations=2)
    lab, n = ndi.label(m)
    blade = lab == 1 + int(np.argmax(ndi.sum(m, lab, range(1, n + 1))))
    blade = ndi.binary_closing(ndi.binary_fill_holes(blade), iterations=3)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    _, (iy, ix) = ndi.distance_transform_edt(~blade, return_indices=True)
    lum = lum[iy, ix] / lum[blade].mean()
    # The veins and mottle at full strength; the photograph's own light across the
    # blade (one half lit, one in shade) at half, since each card is lit again in
    # the renderer and a blade's painted shade already says how deep it sits.
    broad = gaussian_filter(lum, 18)
    ratio = np.clip(1 + (broad - 1) * 0.5 + (lum - broad) * 1.6, 0.55, 1.5)
    # The blade's axis is its long principal axis; the base is the stalk end, at the
    # top of this frame, and the tip the far end.
    ys, xs = np.nonzero(blade)
    c = np.array([xs.mean(), ys.mean()])
    w, v = np.linalg.eigh(np.cov(np.vstack([xs - c[0], ys - c[1]])))
    ax = v[:, int(np.argmax(w))]
    if ax[1] < 0:
        ax = -ax
    t = (xs - c[0]) * ax[0] + (ys - c[1]) * ax[1]
    base = c + ax * t.min()
    length = float(t.max() - t.min())
    img = Image.fromarray(np.clip(ratio * 128, 0, 255).astype(np.uint8), 'L')
    levels = []
    k = 1.0
    while True:
        levels.append((img, base * k, ax, length * k))
        if length * k < 24:
            break
        k *= 0.5
        img = img.resize((max(1, round(img.width * 0.5)), max(1, round(img.height * 0.5))), Image.LANCZOS)
    _photo_blade['levels'] = levels
    return _photo_blade


def photo_fill(img, poly, tr, colour):
    """Fill `poly` with the photographed blade, laid along the leaf space `tr` maps
    (base (0, 0), tip (0, 1)), in `colour` scaled by the photograph's lightness."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, y0 = int(math.floor(min(xs))), int(math.floor(min(ys)))
    w, h = int(math.ceil(max(xs))) - x0 + 1, int(math.ceil(max(ys))) - y0 + 1
    if w < 2 or h < 2:
        return False
    d0 = np.array(tr(0, 0))
    D = np.column_stack([np.array(tr(1, 0)) - d0, np.array(tr(0, 1)) - d0])
    if abs(np.linalg.det(D)) < 1e-6:
        return False
    length = math.hypot(*D[:, 1])
    levels = photo_blade()['levels']
    src, base, ax, lp = next((lv for lv in reversed(levels) if lv[3] >= length), levels[0])
    # the photograph's leaf space: +x to the blade's left as it hangs, +y base to tip
    S = np.column_stack([np.array([ax[1], -ax[0]]) * lp, ax * lp])
    M = S @ np.linalg.inv(D)
    off = base - M @ d0 + M @ np.array([x0, y0])
    lum = src.transform((w, h), Image.AFFINE, (M[0, 0], M[0, 1], off[0], M[1, 0], M[1, 1], off[1]),
                        resample=Image.BILINEAR)
    ratio = np.asarray(lum).astype(np.float32) / 128
    # The painted blade's fold: the half turned from the light is darker.
    gx, gy = np.meshgrid(np.arange(w) + x0 + 0.5, np.arange(h) + y0 + 0.5)
    Di = np.linalg.inv(D)
    across = Di[0, 0] * (gx - d0[0]) + Di[0, 1] * (gy - d0[1])
    ratio = np.where(across < 0, ratio * 0.86, ratio)
    rgb = np.clip(np.array(colour[:3], np.float32) * ratio[..., None], 0, 255).astype(np.uint8)
    tile = Image.fromarray(np.dstack([rgb, np.full((h, w), 255, np.uint8)]), 'RGBA')
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).polygon([(x - x0, y - y0) for x, y in poly], fill=255)
    img.paste(tile, (x0, y0), mask)
    return True


def leaf_rgb(shade, rng, under=False):
    """Near-neutral green; the vertex colour carries the species' July hue. A
    few blades show their pale underside (silver maple, cottonwood flutter)."""
    v = shade * (0.88 + rng.random() * 0.24)
    if under:
        return (int(min(255, v * 1.05 + 40)), int(min(255, v * 1.08 + 44)), int(min(255, v * 0.98 + 38)), 255)
    hue = rng.random()
    r = v * (0.80 + 0.10 * hue)
    g = v * 1.0
    b = v * (0.70 + 0.06 * (1 - hue))
    return (int(min(255, r)), int(min(255, g)), int(min(255, b)), 255)


# Blade length as a fraction of a SPRAY tile. tree-model.js draws a near card
# about 1.3 m across, so these are the species' real leaf lengths over 1.3 m:
# cottonwood 8-12 cm, elm 8-13, silver maple 10-14, bur oak 15-25, basswood
# 10-15, black willow 8-13 (narrow), walnut/ash a whole compound leaf 30-50 cm.
# The first painting had blades twice this size, which is what made the crowns
# read as cartoon foliage.
LEAF_SIZE = {
    'poplar': 0.075, 'aspen': 0.05, 'willow': 0.085, 'elm': 0.07, 'maple': 0.085,
    'oak_round': 0.13, 'oak_pointed': 0.11, 'compound': 0.24, 'heart': 0.09,
}
UNDERSIDE = {'maple': 0.30, 'poplar': 0.12, 'aspen': 0.15, 'willow': 0.18, 'oak_round': 0.10}
# How far apart leaves sit along a twig, in blade lengths.
SPACING = {'compound': 0.55, 'willow': 0.32}


def twig_path(rng, x0, y0, length, angle, steps=12, bend=0.10):
    pts = []
    a = angle
    x, y = x0, y0
    for _ in range(steps + 1):
        pts.append((x, y, a))
        a += (rng.random() - 0.5) * bend
        x += math.sin(a) * length / steps
        y -= math.cos(a) * length / steps
    return pts


def spray_leaves(rng, family, x0, y0, length, angle, scale, depth):
    """A branch end and the leaves it carries, as draw records (not yet
    drawn): a leader, side shoots alternating off it, short spurs off those,
    and leaves along every shoot, each turned, foreshortened and given a depth
    that shades it. A real 1.3 m branch end carries a few hundred leaves; a
    spray card should be most of the way to opaque in its middle."""
    S = TILE * SS
    size = LEAF_SIZE[family] * S * scale
    gap = size * SPACING.get(family, 0.42)
    wood = []
    leaves = []
    lead = twig_path(rng, x0, y0, length, angle)
    shoots = [(lead, 0)]
    nside = 6 + int(rng.random() * 4) if family != 'compound' else 3
    for k in range(nside):
        t = 0.15 + 0.78 * (k + rng.random() * 0.6) / nside
        base = lead[int(t * 12)]
        side = -1 if k % 2 else 1
        sl = length * (0.30 + rng.random() * 0.22) * (1.1 - 0.5 * t)
        sh = twig_path(rng, base[0], base[1], sl, base[2] + side * (0.55 + rng.random() * 0.45))
        shoots.append((sh, 1))
        for j in range(2 if family != 'compound' else 0):
            b2 = sh[int((0.35 + 0.4 * j + rng.random() * 0.15) * 12)]
            shoots.append((twig_path(rng, b2[0], b2[1], sl * (0.35 + rng.random() * 0.2),
                                     b2[2] - side * (0.5 + rng.random() * 0.4) * (1 if j else -1)), 2))
    for sh, order in shoots:
        # A compound leaf's rachis is its own twig: side shoots carry leaves
        # straight off the leader and are not drawn as wood.
        if family != 'compound' or order == 0:
            wood.append(([(x, y) for x, y, _ in sh], max(1, int(S * (0.005, 0.0032, 0.002)[order] * scale))))
        L = sum(math.hypot(sh[i + 1][0] - sh[i][0], sh[i + 1][1] - sh[i][1]) for i in range(len(sh) - 1))
        n = max(2, int(L / max(1.0, gap)))
        for k in range(n):
            t = 0.12 + 0.88 * (k + rng.random() * 0.4) / n
            px, py, pa = sh[min(12, int(t * 12))]
            side = -1 if k % 2 else 1
            spread = (0.25, 0.55) if family == 'willow' else (0.5, 1.1)
            la = pa + side * (spread[0] + rng.random() * (spread[1] - spread[0]))
            # Leaves droop a little under their own weight.
            la += 0.25 * math.sin(la) * rng.random()
            Ls = size * (0.75 + rng.random() * 0.45) * (0.8 + 0.2 * t)
            leaves.append(dict(px=px, py=py, a=la, L=Ls, z=depth + (rng.random() - 0.5) * 0.35,
                               fs=0.35 + rng.random() * 0.65, under=rng.random() < UNDERSIDE.get(family, 0.05)))
        px, py, pa = sh[-1]
        leaves.append(dict(px=px, py=py, a=pa, L=size * 0.8, z=depth + 0.1, fs=0.8, under=False))
    return wood, leaves


def paint_leaves(img, draw, family, rng, wood, leaves):
    S = TILE * SS
    for pts, w in wood:
        draw.line(pts, fill=(88, 80, 64, 255), width=w)
    for lf in sorted(leaves, key=lambda d: d['z']):
        pet = lf['L'] * (0.20 if family in ('poplar', 'aspen', 'maple', 'heart') else 0.06)
        ex = lf['px'] + math.sin(lf['a']) * pet
        ey = lf['py'] - math.cos(lf['a']) * pet
        if pet > 2:
            draw.line([(lf['px'], lf['py']), (ex, ey)], fill=(104, 98, 70, 255), width=max(1, int(S * 0.0025)))
        # Deeper leaves sit in the shade of the ones in front of them.
        z = min(1.0, max(0.0, lf['z']))
        shade = 64 + 160 * z ** 1.15 + rng.random() * 16
        draw_leaf(img, draw, ex, ey, lf['L'], lf['a'], family, rng, shade, lf['under'], lf['fs'])


def cord_spray(rng, x0, y0, length, angle, scale, depth, out):
    """A red cedar's or a juniper's branch end (`scale`): no blade at all. The
    leaves are scales a millimetre or two long pressed flat along cords of
    branchlet, and the cords branch three and four times into a dense, ragged,
    fern-like plate. At a near card's 1.3 m the last cords are a texel wide, so
    what the tile has to carry is the plate's texture: fine cords, thicker at
    their bases, shaded by how deep in the plate they sit."""
    S = TILE * SS

    def grow(x, y, a, L, order, z):
        steps = 7
        pts = [(x, y)]
        for _ in range(steps):
            a += (rng.random() - 0.5) * 0.35
            x += math.sin(a) * L / steps
            y -= math.cos(a) * L / steps
            pts.append((x, y))
        w = max(3, int(S * (0.0075, 0.0060, 0.0050, 0.0042)[order] * scale))
        out.append(dict(kind='cord', pts=pts, w=w, z=z + (rng.random() - 0.5) * 0.2, order=order))
        if order >= 3:
            return
        n = (9, 8, 7)[order] + int(rng.random() * 3)
        for k in range(n):
            t = 0.12 + 0.82 * (k + rng.random() * 0.5) / n
            i = min(steps - 1, int(t * steps))
            bx, by = pts[i]
            side = -1 if k % 2 else 1
            ba = math.atan2(pts[i + 1][0] - bx, -(pts[i + 1][1] - by))
            sl = L * (0.36 + rng.random() * 0.16) * (1.05 - 0.55 * t)
            grow(bx, by, ba + side * (0.45 + rng.random() * 0.35), sl, order + 1,
                 z + (rng.random() - 0.5) * 0.3)
        # The cord's own tip runs on as a branchlet too.
        if order < 3:
            grow(pts[-1][0], pts[-1][1], a, L * 0.38, order + 1, z)

    grow(x0, y0, angle, length, 0, depth)


def needle_spray(rng, x0, y0, length, angle, scale, depth, out):
    """A pine's branch end (`needle`): a twig whose last two or three years of
    growth carry the needles, in pairs, standing out at thirty to sixty degrees
    and crowded toward the shoot tip into a brush. The jack pine's needles are
    2-4 cm and its shoots short and crooked; this paints that."""
    S = TILE * SS
    lead = twig_path(rng, x0, y0, length, angle, steps=12, bend=0.28)
    shoots = [(lead, 0)]
    for k in range(5 + int(rng.random() * 3)):
        t = 0.25 + 0.6 * (k + rng.random() * 0.5) / 6
        b = lead[int(t * 12)]
        side = -1 if k % 2 else 1
        shoots.append((twig_path(rng, b[0], b[1], length * (0.30 + rng.random() * 0.2),
                                 b[2] + side * (0.6 + rng.random() * 0.4), steps=12, bend=0.3), 1))
    nl = S * 0.062 * scale
    for sh, order in shoots:
        out.append(dict(kind='cord', pts=[(x, y) for x, y, _ in sh],
                        w=max(2, int(S * (0.0055, 0.0035)[order] * scale)), z=depth - 0.15, order=order, wood=True))
        # Needles on the shoot's outer 60 %, densest at the tip.
        n = int(150 * (1.0 if order == 0 else 0.7))
        for k in range(n):
            t = 0.45 + 0.55 * (rng.random() ** 0.45)
            px, py, pa = sh[min(12, int(t * 12))]
            for pair in (-1, 1):
                na = pa + pair * (0.35 + rng.random() * 0.75) * (1.25 - 0.55 * t)
                L = nl * (0.7 + rng.random() * 0.5)
                ex = px + math.sin(na) * L
                ey = py - math.cos(na) * L
                out.append(dict(kind='needle', pts=[(px, py), ((px + ex) / 2 + (rng.random() - 0.5) * L * 0.08, (py + ey) / 2), (ex, ey)], w=max(2, int(S * 0.0026 * scale)),
                                z=depth + (rng.random() - 0.5) * 0.4, order=3))
        # The terminal brush and its bud.
        px, py, pa = sh[-1]
        for k in range(40):
            na = pa + (rng.random() - 0.5) * 1.6
            L = nl * (0.6 + rng.random() * 0.5)
            out.append(dict(kind='needle', pts=[(px, py), (px + math.sin(na) * L, py - math.cos(na) * L)],
                            w=max(2, int(S * 0.0026 * scale)), z=depth + 0.15, order=3))


def paint_conifer(draw, rng, marks):
    """Draw cord and needle marks back to front. Wood is grey-brown; foliage the
    same near-neutral green the broadleaf tiles use, so the zone record's July
    colour (vertex colour) sets the hue, darkened in the deep of the plate."""
    for m in sorted(marks, key=lambda d: d['z']):
        z = min(1.0, max(0.0, m['z']))
        if m.get('wood'):
            draw.line(m['pts'], fill=(84, 74, 60, 255), width=m['w'])
            continue
        shade = 58 + 150 * z ** 1.2 + rng.random() * 18
        c = leaf_rgb(shade, rng)
        draw.line(m['pts'], fill=c, width=m['w'])
        if m['kind'] == 'cord' and m['order'] >= 2:
            # The scales catch light along a cord's upper edge.
            hi = tuple(min(255, int(v * 1.16 + 8)) for v in c[:3]) + (255,)
            draw.line([(x - 1, y - 1) for x, y in m['pts']], fill=hi, width=max(1, m['w'] // 2))


CONIFERS = ('scale', 'needle')


def leaf_tile(family, rng, clump=False):
    """A SPRAY tile is one shoot with its side shoots, filling the card; a CLUMP
    tile is a dozen or more sprays massed into a rounded tuft, the way a crown's
    outer shell reads from thirty metres: front sprays lit, back ones in shade."""
    S = TILE * SS
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if family in CONIFERS:
        spray = cord_spray if family == 'scale' else needle_spray
        marks = []
        if not clump:
            spray(rng, S * 0.5, S * 0.97, S * (0.62 if family == 'scale' else 0.70),
                  (rng.random() - 0.5) * 0.25, 1.0, 0.62, marks)
        else:
            for _k in range(26 if family == 'scale' else 18):
                ang = rng.random() * math.pi * 2
                r = math.sqrt(rng.random())
                cx = S * 0.5 + math.cos(ang) * r * S * 0.27
                cy = S * 0.55 + math.sin(ang) * r * S * 0.24
                z = 0.25 + 0.65 * (1 - r) + rng.random() * 0.1
                spray(rng, cx, cy + S * 0.12, S * 0.24,
                      math.atan2(cx - S * 0.5, S * 0.4) + (rng.random() - 0.5) * 1.2, 0.5, z, marks)
        paint_conifer(draw, rng, marks)
        return _finish_tile(img)
    wood, leaves = [], []
    if not clump:
        w, l = spray_leaves(rng, family, S * 0.5, S * 0.97, S * 0.82, (rng.random() - 0.5) * 0.25, 1.0, 0.62)
        wood += w
        leaves += l
    else:
        n = 22 if family != 'compound' else 12
        for _k in range(n):
            ang = rng.random() * math.pi * 2
            r = math.sqrt(rng.random())
            cx = S * 0.5 + math.cos(ang) * r * S * 0.27
            cy = S * 0.55 + math.sin(ang) * r * S * 0.24
            # Front of the tuft (z near 1) toward the middle; back toward the rim.
            z = 0.25 + 0.65 * (1 - r) + rng.random() * 0.1
            w, l = spray_leaves(rng, family, cx, cy + S * 0.12, S * 0.30,
                                math.atan2(cx - S * 0.5, S * 0.4) + (rng.random() - 0.5) * 1.2, 0.42, z)
            wood += w
            leaves += l
    paint_leaves(img, draw, family, rng, wood, leaves)
    return _finish_tile(img)


def _finish_tile(img):
    img = img.resize((TILE, TILE), Image.LANCZOS)
    a = np.asarray(img).astype(np.float32)
    # Keep the blades' edges crisp under alpha test: harden the antialiased rim.
    a[..., 3] = np.clip((a[..., 3] - 60) * 1.6, 0, 255)
    return a.clip(0, 255).astype(np.uint8)


FAMILIES = ['poplar', 'willow', 'elm', 'maple', 'oak_round', 'oak_pointed', 'compound', 'heart']
# T-2768: the two conifer families take a FIFTH ROW, tiles 16-19, and are painted
# after the sixteen broadleaf tiles from the same random stream, so those tiles
# stay byte-identical to the T-2743 atlas.
FAMILIES_ALL = FAMILIES + list(CONIFERS)
# T-1934: the bare winter elm's twig takes a SIXTH ROW, tiles 20 (one branch end's
# twig, TWIG_TILES[0]) and 21 (a tuft of them massed, TWIG_TILES[1]); 22 and 23 stay
# empty. Painted after the twenty tiles before them from the same random stream, so
# those stay byte-identical to the T-2768 atlas.
TWIG_TILES = (20, 21)
ROWS = 6

# The twig's paint: the elm's own bark tile's mean ('interlaced', tile 1 of the bark
# atlas, about (102, 90, 75)), so tree-model.js tints a twig card with the same upper
# bark colour it tints the wood with and the two read as one tree.
TWIG_RGB = (112, 104, 94)


def twig_marks(rng, x0, y0, length, angle, scale, depth, out, order=0, max_order=5):
    """A bare elm's branch end in winter, as the c. 1890s prints draw a parkway
    elm's crown rim: a shoot that forks again and again into fine ascending twig,
    each fork turned up out of the droop the summer's leaf weight gave it, and
    zig-zagging a little at every bud, as an elm's twig does. A mark per shoot:
    its points, its width (thick at the shoot's foot, a texel or two at the last
    twig) and its depth (deeper twigs sit in the shade of the ones in front)."""
    S = TILE * SS
    steps = 6
    pts = [(x0, y0)]
    a = angle
    x, y = x0, y0
    for k in range(steps):
        # the bud's zig-zag, and the shoot easing back toward the vertical
        a += (0.16 if k % 2 else -0.16) * (rng.random() + 0.3) + (0 - a) * 0.06
        x += math.sin(a) * length / steps
        y -= math.cos(a) * length / steps
        pts.append((x, y))
    # A card of this tile is drawn at the mid and far rings, a metre or two across at 10-70 m,
    # so the GPU samples it three or four mips down: a twig is painted 6-16 texels wide, the
    # width that comes through that mip as a line a pixel or two wide and not as a blot.
    w = max(2, int(S * (0.032, 0.023, 0.017, 0.013, 0.012, 0.012)[order] * scale))
    out.append(dict(pts=pts, w=w, z=depth + (rng.random() - 0.5) * 0.15))
    if order >= max_order:
        return
    n = (2, 2, 2, 2, 1)[order] + (1 if rng.random() < 0.3 else 0)
    for k in range(n):
        t = 0.30 + 0.62 * (k + rng.random() * 0.6) / n
        i = min(steps - 1, int(t * steps))
        bx, by = pts[i]
        side = -1 if (k + order) % 2 else 1
        ba = math.atan2(pts[i + 1][0] - bx, -(pts[i + 1][1] - by))
        twig_marks(rng, bx, by, length * (0.50 + rng.random() * 0.18) * (1.08 - 0.4 * t),
                   ba + side * (0.42 + rng.random() * 0.42), scale, depth + (rng.random() - 0.5) * 0.2,
                   out, order + 1, max_order)
    # the shoot's own leader runs on past its last fork
    twig_marks(rng, pts[-1][0], pts[-1][1], length * 0.55, a + (rng.random() - 0.5) * 0.3,
               scale, depth, out, order + 1, max_order)


def twig_tile(rng, clump=False):
    """TWIG_TILES: a SPRAY is one branch end's twig filling the card from its foot;
    a CLUMP is a dozen and more of them massed into the rounded tuft a crown's
    rim reads as from thirty metres, denser toward its middle so the tuft keeps
    a grey core when a coarse mip thins its last twigs out. Painted near the
    elm's bark colour; the card's vertex colour carries the tree's own."""
    S = TILE * SS
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    marks = []
    if not clump:
        twig_marks(rng, S * 0.5, S * 0.98, S * 0.46, (rng.random() - 0.5) * 0.2, 1.0, 0.6, marks, 0, 3)
    else:
        # the tuft fans out of a point below the tile, as a crown's shoots fan out of
        # their limb: each shoot rises along its own ray, the middle ones in front
        for _k in range(9):
            ray = (rng.random() - 0.5) * 2.1
            r = 0.45 + 0.55 * math.sqrt(rng.random())
            cx = S * 0.5 + math.sin(ray) * r * S * 0.30
            cy = S * 1.02 - math.cos(ray) * r * S * 0.42
            z = 0.25 + 0.65 * (1 - abs(ray) / 1.05) * 0.8 + rng.random() * 0.15
            twig_marks(rng, cx, cy, S * 0.26, ray + (rng.random() - 0.5) * 0.35, 0.75, z, marks, 1, 4)
    for m in sorted(marks, key=lambda d: d['z']):
        z = min(1.0, max(0.0, m['z']))
        k = 0.78 + 0.34 * z + (rng.random() - 0.5) * 0.08
        draw.line(m['pts'], fill=tuple(int(min(255, c * k)) for c in TWIG_RGB) + (255,), width=m['w'])
    return _finish_tile(img)


def make_leaves(seed):
    rng = np.random.default_rng(seed)
    atlas = np.zeros((TILE * ROWS, TILE * 4, 4), np.uint8)
    for f, fam in enumerate(FAMILIES_ALL):
        for k, clump in enumerate((False, True)):
            tile = f * 2 + k
            x0 = (tile % 4) * TILE
            y0 = (tile // 4) * TILE
            t = leaf_tile(fam, rng, clump)
            # A transparent gutter so a neighbour never bleeds in through the mips.
            t[:6, :, 3] = 0
            t[-6:, :, 3] = 0
            t[:, :6, 3] = 0
            t[:, -6:, 3] = 0
            atlas[y0:y0 + TILE, x0:x0 + TILE] = t
    for k, tile in enumerate(TWIG_TILES):
        x0 = (tile % 4) * TILE
        y0 = (tile // 4) * TILE
        t = twig_tile(rng, clump=bool(k))
        t[:6, :, 3] = 0
        t[-6:, :, 3] = 0
        t[:, :6, 3] = 0
        t[:, -6:, 3] = 0
        atlas[y0:y0 + TILE, x0:x0 + TILE] = t
    # Fill the colour of transparent texels from their neighbours, so a mip that
    # averages a blade with the gap beside it does not pull in black.
    rgb = atlas[..., :3].astype(np.float32)
    alpha = atlas[..., 3:4].astype(np.float32) / 255
    img = Image.fromarray((rgb * alpha).astype(np.uint8))
    wsum = Image.fromarray((alpha[..., 0] * 255).astype(np.uint8))
    blur = np.asarray(img.filter(ImageFilter.GaussianBlur(6))).astype(np.float32)
    wb = np.asarray(wsum.filter(ImageFilter.GaussianBlur(6))).astype(np.float32)[..., None] / 255
    fill = blur / np.maximum(wb, 1e-3)
    rgb = np.where(alpha > 0.5, rgb, np.clip(fill, 0, 255))
    atlas[..., :3] = rgb.astype(np.uint8)
    return atlas


def write_ktx2(leaves, colour, normal):
    """THE .ktx2 BESIDE EACH WEBP (the T-2582 rule, for these three). A WebP is
    decoded to RGBA8 on the GPU, four bytes a texel and a third more for mips:
    the three atlases came to 35 MB of a 1904 desktop's GPU, more than every elm's
    geometry. Basis Universal is transcoded to the GPU's own block format and kept
    compressed. The normal is UASTC (a vector is data; ETC1S's shared endpoints
    would smear it); the bark colour is ETC1S; the leaf atlas is ETC1S at its top
    quality, since it is a near-neutral colour and a cut-out edge, and UASTC
    shipped it at 2.2 MB of boot bytes against 0.78. Each is encoded from the lossless master, bottom row first, as
    tools/ktx2_sheets.py writes its sheets (KTX2Loader does not flip). The `ktx`
    tool is ktx2_sheets.py's own pinned, hash-checked KTX-Software."""
    import subprocess
    import tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ktx2_sheets import ktx_binary, ETC1S, ETC1S_DATA, UASTC
    exe, env = ktx_binary()
    jobs = [
        ('leaf_atlas', leaves, 'R8G8B8A8_SRGB', 'srgb', ETC1S_DATA, 'clamp'),
        ('bark_basecolor', colour, 'R8G8B8_SRGB', 'srgb', ETC1S, 'clamp'),
        ('bark_normal', normal, 'R8G8B8_UNORM', 'linear', UASTC, 'clamp'),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        for name, im, fmt, oetf, codec, wrap in jobs:
            src = os.path.join(tmp, f'{name}.png')
            im.transpose(Image.FLIP_TOP_BOTTOM).save(src)
            out = os.path.join(OUT, f'{name}.ktx2')
            subprocess.run([exe, 'create', '--format', fmt, '--assign-oetf', oetf,
                            '--generate-mipmap', '--mipmap-wrap', wrap, *codec, src, out],
                           check=True, env=env)


def print_crops(margin=8, alpha=24):
    """T-3017 — each leaf tile's opaque box, as tree-model.js LEAF_CROP: the
    tile's own u0, u1, v0, v1 in atlasUV's units (v up, the 6 px gutter out),
    grown by `margin` pixels so a coarse mip's blurred edge stays inside it. A
    card is cut to this box, so the GPU does not shade and alpha-test the empty
    corners of every spray. Re-run whenever the leaf atlas is regenerated."""
    a = np.asarray(Image.open(os.path.join(OUT, 'leaf_atlas.webp')).convert('RGBA'))[:, :, 3]
    gx = a.shape[1] // TILE
    gy = a.shape[0] // TILE
    pad = 6
    span = TILE - 2 * pad
    rows = []
    for t in range(gx * gy):
        cx, cy = t % gx, t // gx
        tile = a[cy * TILE:(cy + 1) * TILE, cx * TILE:(cx + 1) * TILE]
        ys, xs = np.where(tile > alpha)
        if not len(xs):
            rows.append('[0.000, 1.000, 0.000, 1.000]')  # an empty tile (22, 23)
            continue
        x0 = max(pad, xs.min() - margin)
        x1 = min(TILE - pad, xs.max() + 1 + margin)
        y0 = max(pad, ys.min() - margin)
        y1 = min(TILE - pad, ys.max() + 1 + margin)
        u0, u1 = (x0 - pad) / span, (x1 - pad) / span
        v0, v1 = 1 - (y1 - pad) / span, 1 - (y0 - pad) / span
        rows.append(f'[{u0:.3f}, {u1:.3f}, {v0:.3f}, {v1:.3f}]')
    print('export const LEAF_CROP = [')
    for i in range(0, len(rows), 4):
        print('  ' + ', '.join(rows[i:i + 4]) + ',')
    print('];')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--masters', action='store_true', help='also write the lossless PNGs')
    ap.add_argument('--sheet', metavar='PATH', help='also write a contact sheet (JPEG) there')
    ap.add_argument('--no-ktx2', action='store_true', help='skip the GPU-compressed copies')
    ap.add_argument('--crops', action='store_true',
                    help='print tree-model.js LEAF_CROP from the committed leaf atlas, and write nothing')
    args = ap.parse_args()
    if args.crops:
        print_crops()
        return 0
    os.makedirs(OUT, exist_ok=True)
    leaves = make_leaves(2743)
    colour, normal = make_bark(27431)
    li = Image.fromarray(leaves, 'RGBA')
    ci = Image.fromarray(colour, 'RGB')
    ni = Image.fromarray(normal, 'RGB')
    if args.masters:
        li.save(os.path.join(OUT, 'leaf_atlas.png'), optimize=True)
        ci.save(os.path.join(OUT, 'bark_basecolor.png'), optimize=True)
        ni.save(os.path.join(OUT, 'bark_normal.png'), optimize=True)
    # THE WEB COPIES, AND WHY THEY ARE LOSSY. These are boot bytes. Lossless they
    # were 2.0 + 0.3 + 3.4 MB, because painted noise does not compress; at q85 they
    # are under a fifth of that. The leaf alpha is kept at full quality, since the
    # cut-out edge is the leaf's outline. The normal map is written at half size:
    # a 256-texel bark tile already holds the furrows at the size a visitor sees
    # them, and the half size is a quarter of the GPU memory.
    li.save(os.path.join(OUT, 'leaf_atlas.webp'), quality=85, alpha_quality=100, method=6)
    ci.save(os.path.join(OUT, 'bark_basecolor.webp'), quality=85, method=6)
    ni.resize((ni.width // 2, ni.height // 2), Image.LANCZOS).save(
        os.path.join(OUT, 'bark_normal.webp'), quality=85, method=6)
    if not args.no_ktx2:
        write_ktx2(li, ci, ni.resize((ni.width // 2, ni.height // 2), Image.LANCZOS))
    if args.sheet:
        sheet = Image.new('RGB', (2048, li.height + 1024), (200, 214, 230))
        sheet.paste(li, (0, 0), li)
        sheet.paste(ci, (0, li.height))
        sheet.save(args.sheet, quality=85)
    for f in sorted(os.listdir(OUT)):
        print(f'{f:28s} {os.path.getsize(os.path.join(OUT, f)) // 1024:6d} KB')


if __name__ == '__main__':
    sys.exit(main())
