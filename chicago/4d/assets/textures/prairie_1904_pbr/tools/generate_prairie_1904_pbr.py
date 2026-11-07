#!/usr/bin/env python3
"""Build the Prairie Avenue 1904 street-surface PBR library (T-1728).

    python3 generate_prairie_1904_pbr.py --out ..      # rebuild the library in place

The same contract as the 1835 library it sits beside (chicago_1835_pbr/tools/
generate_1835_pbr_library.py): every tile is deterministic and seamless, and every
material writes aligned base-colour, 16-bit height, OpenGL and DirectX normals,
roughness, AO, metallic and packed ORM maps plus a material.json. Two things differ,
and both are for the web renderer, which binds these directly:

  * 512 px, not 1024. The street is seen from a walker's eye 1.6 m above it; at the
    spans below 512 px is 85-170 px per metre, which is the 1835 mud street's density
    (128 px/m) or better, at a quarter of the bytes.
  * three WEB derivatives per material (`*_basecolor_web.jpg`, `*_normal_gl_web.jpg`,
    `*_orm_web.jpg`), JPEG re-encodes of the same pixels. publish.sh ships those and
    nothing else, so the deployed page pays for three small files per surface and the
    repository keeps the full engine-neutral set.

WHAT THESE ARE EVIDENCE OF: NOTHING. They are procedural pictures of a material a
source names (or a reconstruction names) for a surface; their colour, grain, joint
pattern and wear are ours. Which surface carries which material, and on what evidence,
is data/street_surfaces/1904.json's to say, never this file's. Where a figure below is
a period dimension (a 5 x 6 ft walk block, a 6-ft curbstone, a 4 x 8.5 in paving
brick) it is named with its source or its liberty in the material's note.

No photograph is sampled. Orientation: image x is ALONG the street (the renderer's u),
image y is ACROSS it (v). Walk and curb tiles span their band's full width in v.

THE YARD GROUP (T-3488, v1.1.0) adds five back- and side-yard grounds after the seven
street materials: herringbone brick, stone flagging, pea gravel, trodden earth and dug
loam. They are appended, so the seven keep their seeds and their bytes. Two things are
theirs alone: their relief is built in metres and lit at its true slope (see `relief`),
and each names its own web JPEG qualities (`web_quality`; the seven keep 86/92/90),
because a gravel or a crumb is detail at every pixel and costs bytes at every pixel.
The pea gravel's tile is 1.0 m, not the ~2 m asked for: at 512 px a 5-15 mm stone is
2.5-8 px there and reads as a stone; over 2 m it is 1-4 px and reads as noise.
"""

from __future__ import annotations

import argparse
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

SIZE = 512
FT = 0.3048

# span_m is the tile's length ALONG the street; across is `span_across_m`, or "band"
# for a tile the renderer stretches over the band's own width. `directional` marks a
# tile whose pattern has a direction (joints, courses) and must follow the street's
# own frame; the rest the renderer lays on the world axis nearest the street.
YARD_ORIENTATION = "image x = along the path or court the yard layout lays it on (renderer u); image y = across it (v)"
YARD_CONFIDENCE = "reconstructed appearance; which yard surface carries it is the yard layout's to say, never this map's"

MATERIALS = [
    dict(id="sheet_asphalt", directional=False, group="roadway", span_m=4.0, span_across_m=4.0,
         kind="asphalt", mean_roughness=0.70, colors=((92, 90, 86), (60, 59, 57)),
         note="Sheet asphalt (lake asphalt and sand on a concrete base) about one season old: "
              "a fine sand grain, a faint mottle, wheel-polished streaks along the street and "
              "sparse horse-droppings stains. Colour and wear are reconstructed (L296)."),
    dict(id="macadam_limestone", directional=False, group="roadway", span_m=6.0, span_across_m=6.0,
         kind="macadam", mean_roughness=0.92, colors=((160, 154, 140), (112, 108, 99)),
         note="Water-bound crushed-limestone macadam, worn: pale dusty binder over angular "
              "aggregate, wheel tracks along the street and patched hollows. The city's own "
              "1 Dec 1904 report lists these streets as macadam 'in need of repair'; the look "
              "is reconstructed (L296)."),
    dict(id="vitrified_paving_brick", directional=True, group="roadway", span_m=2.12, span_across_m=2.12,
         kind="brick", mean_roughness=0.80, colors=((122, 64, 50), (84, 52, 46)),
         note="Vitrified paving brick laid on edge across the street in running bond, sand "
              "joints: 20 courses of 0.106 m along and 10 bricks of 0.212 m across per tile (a "
              "4 x 8.5 in brick with its joint). The brick size and colour are reconstructed "
              "(L296)."),
    dict(id="earth_and_cinders", directional=False, group="alley", span_m=4.0, span_across_m=4.0,
         kind="cinder", mean_roughness=0.95, colors=((88, 80, 68), (46, 45, 43)),
         note="An unimproved alley: graded earth dressed with ashes and cinders, rutted along "
              "its length. Reconstructed (L297)."),
    dict(id="portland_cement_walk", directional=True, group="walk", span_m=10 * FT, span_across_m="band",
         kind="walk", mean_roughness=0.82, colors=((182, 179, 171), (150, 147, 140)),
         note="Portland cement concrete walk with a trowelled top worn matte, jointed in "
              "blocks: the tile is two blocks along and one across, the 5 x 6 ft blocks of the "
              "1905 code's sec. 2062. The material is reconstructed (L296)."),
    dict(id="sandstone_curbstone", directional=True, group="curb", span_m=12 * FT, span_across_m="band",
         kind="curb", mean_roughness=0.85, colors=((180, 171, 150), (140, 133, 118)),
         note="Buff sandstone curbstones seen from above, two 6-ft stones per tile with a "
              "tooled top and weathered arrises. Sandstone is what the Board of Local "
              "Improvements' 1902-03 ordinances name when they name a curbstone; the stone "
              "and its length here are reconstructed (L296)."),
    dict(id="grass_plat", directional=False, group="parkway", span_m=3.0, span_across_m=3.0,
         kind="grass", mean_roughness=0.95, colors=((86, 112, 52), (58, 80, 38)),
         note="A mown grass plat in July: mixed greens, clover and a few dry patches. The "
              "1905 code's sec. 2077 names grass plats for this space; the turf is "
              "reconstructed (L296)."),
    # T-3488: the back and side yards. Not street surfaces: x runs along whatever path or
    # court the yard layout lays them on, and that layout, not this library, says where.
    dict(id="yard_brick_herringbone", directional=True, group="yard",
         span_m=1.782, span_across_m=1.782,
         kind="herringbone", mean_roughness=0.80, colors=((138, 86, 68), (90, 60, 50)),
         note="Hard-burned common brick laid flat in a 45-degree herringbone on sand, as in "
              "Chicago yards about 1900: a 4 x 8 in brick with its joint (0.105 x 0.21 m), red-"
              "brown with a few burnt and a few salmon bricks, sand joints sunk and gone to "
              "dirt and a little moss, a walked polish, a chipped corner and a cracked brick "
              "here and there. The brick, the bond and the wear are reconstructed (T-3488).",
         web_quality=(82, 78, 72), ticket="T-3488", orientation=YARD_ORIENTATION, confidence=YARD_CONFIDENCE),
    dict(id="bluestone_flags", directional=True, group="yard", span_m=2.4, span_across_m=2.4,
         kind="flagging", mean_roughness=0.84, colors=((142, 137, 125), (97, 93, 79)),
         note="Random-rectangular stone flagging in three courses: buff-grey Joliet limestone "
              "and blue-grey flag, slabs 0.5-1.0 m with some split smaller, 10-15 mm soil "
              "joints with grass and moss creeping along some, slabs settled unevenly, "
              "weather, lichen and an iron stain or two. Stone, sizes and weathering are "
              "reconstructed (T-3488).",
         ticket="T-3488", orientation=YARD_ORIENTATION, confidence=YARD_CONFIDENCE),
    dict(id="pea_gravel", directional=False, group="yard", span_m=1.0, span_across_m=1.0,
         kind="gravel", mean_roughness=0.78, colors=((184, 174, 156), (99, 89, 77)),
         note="Raked pea gravel for a carriage court or garden path: rounded 5-15 mm stones, "
              "tan, grey, buff and a few white, over a dusty bed, the rake's tines leaving "
              "faint ridges along x. The mix and the raking are reconstructed (T-3488).",
         web_quality=(72, 72, 68), ticket="T-3488", orientation=YARD_ORIENTATION, confidence=YARD_CONFIDENCE),
    dict(id="beaten_earth", directional=False, group="yard", span_m=3.0, span_across_m=3.0,
         kind="earth", mean_roughness=0.89, colors=((126, 115, 98), (111, 101, 84)),
         note="Trodden yard earth for a drying or service yard: compacted brown-grey soil, "
              "the walked ground paler and smoother, the untrodden darker and looser with "
              "thin grass at its margins, a scatter of cinders and pebbles. Reconstructed "
              "(T-3488).",
         web_quality=(86, 85, 80), ticket="T-3488", orientation=YARD_ORIENTATION, confidence=YARD_CONFIDENCE),
    dict(id="garden_loam", directional=True, group="yard", span_m=2.0, span_across_m=2.0,
         kind="loam", mean_roughness=0.91, colors=((86, 72, 58), (64, 53, 43)),
         note="Freshly dug and raked garden loam: a dark crumb, the rake's tines drawn along "
              "x about 30 mm apart, clods and a few small stones on top, the furrow bottoms "
              "damper and darker. Reconstructed (T-3488).",
         web_quality=(82, 78, 72), ticket="T-3488", orientation="image x = along the rows (renderer u); image y = across them (v)",
         confidence=YARD_CONFIDENCE),
]

WEB_SUFFIXES = ("basecolor", "normal_gl", "orm")
MASTER_SUFFIXES = ("basecolor", "normal_gl", "normal_dx", "roughness", "height16", "ao", "metallic", "orm")


# ---------------------------------------------------------------------------- noise

def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def norm01(a):
    lo, hi = float(a.min()), float(a.max())
    return (a - lo) / max(hi - lo, 1e-6)


def blur(a, sigma):
    return ndimage.gaussian_filter(a, sigma=sigma, mode="wrap")


def standard(a):
    """Centre on 0.5 with +-3 standard deviations spanning 0..1, so a blurred field keeps
    its contrast (min-max scaling lets two outliers flatten everything else)."""
    return clamp01(0.5 + (a - a.mean()) / (6.0 * max(float(a.std()), 1e-6)))


def noise(rng, sigma, shape=(SIZE, SIZE)):
    """Seamless band-limited noise, ~0..1. sigma may be a (y, x) pair for streaks."""
    return standard(blur(rng.random(shape, dtype=np.float32), sigma))


def fbm(rng, sigmas, weights):
    out = np.zeros((SIZE, SIZE), np.float32)
    for s, w in zip(sigmas, weights):
        out += (noise(rng, s) - 0.5) * w
    return standard(out)


def voronoi(rng, cells, jitter=1.0):
    """Seamless Voronoi: (nearest-cell id, distance to the nearest edge proxy)."""
    pts = rng.random((cells, 2)) * SIZE
    ids = np.full((SIZE, SIZE), -1, np.int32)
    seed = np.zeros((SIZE, SIZE), bool)
    for i, (y, x) in enumerate(pts.astype(int) % SIZE):
        ids[y, x] = i
        seed[y, x] = True
    tiled = np.tile(seed, (3, 3))
    d, (iy, ix) = ndimage.distance_transform_edt(~tiled, return_indices=True)
    tid = np.tile(ids, (3, 3))[iy, ix]
    sl = slice(SIZE, 2 * SIZE)
    nearest = tid[sl, sl]
    dist = d[sl, sl].astype(np.float32)
    # a cheap edge measure: where the id changes within a pixel's neighbourhood
    edge = np.zeros_like(dist)
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        edge = np.maximum(edge, (np.roll(nearest, (dy, dx), (0, 1)) != nearest).astype(np.float32))
    return nearest, dist, edge


def palette(t, c0, c1):
    t = clamp01(t)[..., None]
    return np.array(c1, np.float32) * (1 - t) + np.array(c0, np.float32) * t


def stamps(rng, count, radius, shape=(SIZE, SIZE), elongate=1.0):
    """Sparse soft blotches (stains, dry patches), seamless."""
    out = np.zeros(shape, np.float32)
    for _ in range(count):
        cy, cx = rng.random(2) * SIZE
        r = radius * (0.5 + rng.random())
        yy, xx = np.ogrid[:SIZE, :SIZE]
        dy = np.minimum(np.abs(yy - cy), SIZE - np.abs(yy - cy))
        dx = np.minimum(np.abs(xx - cx), SIZE - np.abs(xx - cx)) / elongate
        out = np.maximum(out, np.exp(-((dy ** 2 + dx ** 2) / (r * r))))
    return out


# ------------------------------------------------------------------------ surfaces

def asphalt(spec, rng):
    grain = noise(rng, 0.7)
    mottle = fbm(rng, (60, 24, 9), (0.5, 0.3, 0.2))
    streak = noise(rng, (3.0, 40.0))             # along x: wheel-polished streaks
    stain = stamps(rng, 9, 7.0, elongate=2.5) * noise(rng, 2.0)
    t = 0.55 + 0.22 * (mottle - 0.5) + 0.18 * (grain - 0.5) + 0.12 * (streak - 0.5)
    color = palette(t, *spec["colors"])
    color = color * (1 - 0.25 * stain[..., None]) + np.array((70, 56, 40), np.float32) * 0.25 * stain[..., None]
    h = 0.5 + 0.35 * (grain - 0.5) + 0.25 * (mottle - 0.5)
    rough = spec["mean_roughness"] + 0.08 * (grain - 0.5) - 0.10 * clamp01((streak - 0.55) * 3)
    return clamp01(h), color, clamp01(rough), 2.2


def macadam(spec, rng):
    ids, dist, edge = voronoi(rng, 5200)
    tone = rng.random(ids.max() + 1).astype(np.float32)[ids]
    stone = clamp01(1 - dist / 3.2)                 # a raised crown to each aggregate cell
    dust = fbm(rng, (40, 14, 5), (0.5, 0.3, 0.2))
    ruts = 0.5 + 0.5 * np.sin(np.linspace(0, 2 * math.pi * 3, SIZE, endpoint=False))[:, None]  # 3 tracks per 6 m
    ruts = blur(np.broadcast_to(ruts, (SIZE, SIZE)).copy() * noise(rng, (2.0, 30.0)), (3.0, 12.0))
    hollows = stamps(rng, 6, 16.0, elongate=1.8)
    fine = noise(rng, 0.8)
    t = 0.55 + 0.25 * (tone - 0.5) * (1 - dust) + 0.25 * (dust - 0.5) + 0.10 * (fine - 0.5) - 0.18 * hollows
    color = palette(t - 0.10 * ruts, *spec["colors"])
    h = 0.5 + 0.22 * stone * (1 - 0.6 * dust) + 0.08 * (fine - 0.5) - 0.20 * hollows - 0.10 * ruts - 0.10 * edge
    rough = spec["mean_roughness"] + 0.05 * (fine - 0.5) - 0.06 * hollows
    return clamp01(h), color, clamp01(rough), 4.0


def brick(spec, rng):
    yy, xx = np.indices((SIZE, SIZE)).astype(np.float32)
    courses, per = 20, 10
    cw = SIZE / courses                      # course width along x
    bl = SIZE / per                          # brick length across y
    course = np.floor(xx / cw).astype(int)
    fx = (xx % cw) / cw
    yoff = yy + (course % 2) * bl * 0.5
    bidx = np.floor(yoff / bl).astype(int) % per
    fy = (yoff % bl) / bl
    joint_w = 1.6 / cw
    jx = np.minimum(fx, 1 - fx)
    jy = np.minimum(fy, 1 - fy) * (bl / cw)
    j = np.minimum(jx, jy)
    joint = clamp01(1 - j / joint_w)
    chamfer = clamp01(1 - j / (joint_w * 2.6))
    key = (course * 131 + bidx * 17) % 997
    tone = rng.random(1000).astype(np.float32)[key]
    fine = noise(rng, 0.8)
    wear = fbm(rng, (50, 16), (0.6, 0.4))
    t = 0.30 + 0.55 * tone + 0.12 * (fine - 0.5) - 0.10 * (wear - 0.5)
    color = palette(t, *spec["colors"])
    sand = np.array((128, 118, 100), np.float32)
    color = color * (1 - joint[..., None]) + sand * joint[..., None]
    color *= (1 - 0.18 * (chamfer - joint))[..., None]
    h = 0.62 - 0.40 * joint - 0.12 * (chamfer - joint) + 0.05 * (fine - 0.5)
    rough = spec["mean_roughness"] + 0.12 * joint + 0.05 * (fine - 0.5)
    return clamp01(h), color, clamp01(rough), 5.0


def cinders(spec, rng):
    base = fbm(rng, (50, 18, 6), (0.45, 0.35, 0.2))
    specks = clamp01((noise(rng, 0.6) - 0.62) * 6)
    pale = clamp01((noise(rng, 0.9) - 0.70) * 5)
    ruts = 0.5 + 0.5 * np.sin(np.linspace(0, 2 * math.pi * 2, SIZE, endpoint=False))[:, None]
    ruts = blur(np.broadcast_to(ruts, (SIZE, SIZE)).copy(), (4.0, 20.0)) * noise(rng, (4.0, 40.0))
    puddle = stamps(rng, 4, 18.0, elongate=2.0)
    t = 0.55 + 0.30 * (base - 0.5) - 0.35 * specks + 0.20 * pale - 0.20 * puddle - 0.10 * ruts
    color = palette(t, *spec["colors"])
    h = 0.5 + 0.18 * (base - 0.5) + 0.10 * specks - 0.18 * ruts - 0.12 * puddle
    rough = spec["mean_roughness"] - 0.25 * puddle + 0.03 * (base - 0.5)
    return clamp01(h), color, clamp01(rough), 3.2


def walk(spec, rng):
    yy, xx = np.indices((SIZE, SIZE)).astype(np.float32)
    half = SIZE / 2
    # joints across the walk at x = 0 and x = half (two 5-ft blocks); the walk's own edges
    # are the band edges, y = 0 and y = SIZE.
    dx_joint = np.minimum(xx % half, half - (xx % half))
    dy_edge = np.minimum(yy, SIZE - 1 - yy)
    joint = clamp01(1 - dx_joint / 1.6)
    edge = clamp01(1 - dy_edge / 2.0)
    # the tooled margin line about an inch inside each block's edge
    px_per_m_x, px_per_m_y = SIZE / spec["span_m"], SIZE / (6 * FT)
    mx, my = 0.025 * px_per_m_x, 0.025 * px_per_m_y
    margin = np.maximum(clamp01(1 - np.abs(dx_joint - mx) / 0.9), clamp01(1 - np.abs(dy_edge - my) / 0.9)) * 0.6
    mottle = fbm(rng, (40, 14, 5), (0.5, 0.3, 0.2))
    fine = noise(rng, 0.7)
    swirl = noise(rng, (6.0, 2.0))
    dirt = blur(np.maximum(joint, edge), 6.0) * noise(rng, 3.0)
    stain = stamps(rng, 3, 10.0) * noise(rng, 2.0)
    t = 0.62 + 0.20 * (mottle - 0.5) + 0.10 * (fine - 0.5) + 0.05 * (swirl - 0.5) - 0.30 * dirt - 0.20 * stain
    color = palette(t, *spec["colors"])
    color *= (1 - 0.35 * joint - 0.12 * margin - 0.15 * edge)[..., None]
    h = 0.6 - 0.45 * joint - 0.10 * margin - 0.10 * edge + 0.04 * (fine - 0.5) + 0.03 * (mottle - 0.5)
    rough = spec["mean_roughness"] + 0.10 * joint + 0.04 * (fine - 0.5)
    return clamp01(h), color, clamp01(rough), 4.0


def curb(spec, rng):
    yy, xx = np.indices((SIZE, SIZE)).astype(np.float32)
    half = SIZE / 2
    stone = (xx // half).astype(int)          # two stones per tile
    dx_joint = np.minimum(xx % half, half - (xx % half))
    joint = clamp01(1 - dx_joint / 1.4)
    dy = np.minimum(yy, SIZE - 1 - yy) / SIZE  # 0 at either arris
    arris = clamp01(1 - dy / 0.10)
    tone = np.where(stone == 0, rng.random(), rng.random()).astype(np.float32)
    # bedding in the stone runs along it; the tooling runs across the top
    bed = noise(rng, (60.0, 1.5))
    tooling = 0.5 + 0.5 * np.sin(xx * (2 * math.pi / 5.0))
    fine = noise(rng, (4.0, 0.7))
    t = 0.30 + 0.45 * tone + 0.20 * (bed - 0.5) + 0.08 * (fine - 0.5)
    color = palette(t, *spec["colors"])
    color *= (1 - 0.40 * joint - 0.18 * arris)[..., None]
    h = 0.6 - 0.40 * joint - 0.20 * arris + 0.03 * (tooling - 0.5) + 0.05 * (fine - 0.5)
    rough = spec["mean_roughness"] + 0.08 * joint + 0.05 * (fine - 0.5)
    return clamp01(h), color, clamp01(rough), 3.0


def grass(spec, rng):
    blades = noise(rng, (1.1, 0.45))
    tufts = fbm(rng, (8, 3, 1.2), (0.4, 0.35, 0.25))
    patch = fbm(rng, (70, 30), (0.6, 0.4))
    clover = clamp01((noise(rng, 3.0) - 0.72) * 5)
    dry = clamp01((noise(rng, 10.0) - 0.80) * 3) * 0.6
    t = 0.50 + 0.55 * (blades - 0.5) + 0.35 * (tufts - 0.5) + 0.25 * (patch - 0.5)
    color = palette(t, *spec["colors"])
    color = color * (1 - 0.35 * clover[..., None]) + np.array((104, 140, 64), np.float32) * 0.35 * clover[..., None]
    color = color * (1 - 0.55 * dry[..., None]) + np.array((140, 128, 78), np.float32) * 0.55 * dry[..., None]
    h = 0.5 + 0.30 * (blades - 0.5) + 0.25 * (tufts - 0.5)
    rough = spec["mean_roughness"] + 0.03 * (blades - 0.5)
    return clamp01(h), color, clamp01(rough), 2.6


# --------------------------------------------------------------------- yards (T-3488)
#
# The back and side yards behind the houses: brick and stone pavings by the rear doors,
# gravel to the carriage houses, a trodden drying yard and a dug bed. These five carry
# their relief in metres: each builds a height in metres, `relief` maps it to the 0..1
# master about a depth D, and the normal strength it returns is D over the metres per
# pixel, so the slope the renderer lights is the slope the surface has.

def mpp(spec):
    return spec["span_m"] / SIZE


def relief(h_m, depth_m):
    """A height in metres (about 0) as the 0..1 master, and the matching normal strength
    is depth_m / metres-per-pixel: see the callers."""
    return clamp01(0.5 + h_m / depth_m)


def mix(color, target, w):
    w = clamp01(w)[..., None]
    return color * (1 - w) + np.array(target, np.float32) * w


def downsample(a, ss):
    if ss == 1:
        return a
    s = a.shape
    return a.reshape(s[0] // ss, ss, s[1] // ss, ss, *s[2:]).mean(axis=(1, 3))


def strokes(rng, segs, ss=2, width=1):
    """Short straight strokes (grass blades, cracks) as a seamless 0..1 mask at SIZE*ss.
    segs is a list of (y0, x0, y1, x1) in SIZE px; drawn on a margin canvas, folded back."""
    n, m = SIZE * ss, 48 * ss
    im = Image.new("L", (n + 2 * m, n + 2 * m), 0)
    dr = ImageDraw.Draw(im)
    for y0, x0, y1, x1, v in segs:
        dr.line([((x0 % SIZE) * ss + m, (y0 % SIZE) * ss + m),
                 ((x1 - x0 + x0 % SIZE) * ss + m, (y1 - y0 + y0 % SIZE) * ss + m)],
                fill=int(v * 255), width=width)
    a = np.asarray(im, np.float32) / 255.0
    out = a[m:m + n, m:m + n].copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                y0, x0 = m + dy * n, m + dx * n
                ys, xs = slice(max(y0, 0), min(y0 + n, a.shape[0])), slice(max(x0, 0), min(x0 + n, a.shape[1]))
                part = a[ys, xs]
                ty, tx = ys.start - y0, xs.start - x0
                out[ty:ty + part.shape[0], tx:tx + part.shape[1]] = np.maximum(
                    out[ty:ty + part.shape[0], tx:tx + part.shape[1]], part)
    return out


def rounded_stones(rng, n, cy, cx, a, b, theta, crown, seat, ground, ss, power=0.55, lumpy=0.18):
    """Rasterise rounded stones on the torus at SIZE*ss: each an irregular ellipse
    (semi-axes a, b px of the SIZE grid, angle theta) whose top is a dome `crown` metres
    high seated at `seat` metres; a stone shows where it stands above `ground` (metres, at
    SIZE*ss) and above every other stone. Returns (height m, owner id or -1, rho) at
    SIZE*ss, rho being 0 at a stone's centre and 1 at its rim."""
    N = SIZE * ss
    zbest = ground.ravel().astype(np.float32).copy()
    owner = np.full(N * N, -1, np.int32)
    rho_out = np.ones(N * N, np.float32)
    k = rng.random((n, 4)).astype(np.float32)
    rad = np.ceil(np.maximum(a, b) * ss * (1 + lumpy) + 1).astype(int)
    for r in np.unique(rad):
        sel = np.nonzero(rad == r)[0]
        oy, ox = np.mgrid[-r:r + 1, -r:r + 1]
        oy, ox = oy.ravel().astype(np.float32), ox.ravel().astype(np.float32)
        step = max(1, 1_500_000 // oy.size)
        for c0 in range(0, sel.size, step):
            ch = sel[c0:c0 + step]
            py, px = cy[ch] * ss, cx[ch] * ss
            iy = np.floor(py)[:, None] + oy[None]
            ix = np.floor(px)[:, None] + ox[None]
            dy, dx = iy + 0.5 - py[:, None], ix + 0.5 - px[:, None]
            cs, sn = np.cos(theta[ch])[:, None], np.sin(theta[ch])[:, None]
            u = (dx * cs + dy * sn) / (a[ch][:, None] * ss)
            v = (-dx * sn + dy * cs) / (b[ch][:, None] * ss)
            ang = np.arctan2(v, u)
            kk = k[ch]
            wob = 1 + lumpy * (0.6 * (kk[:, 0:1] - 0.5) * np.cos(2 * ang + 6.3 * kk[:, 1:2])
                               + 0.8 * (kk[:, 2:3] - 0.5) * np.cos(3 * ang + 6.3 * kk[:, 3:4]))
            rho = np.sqrt(u * u + v * v) * wob
            inside = rho < 1
            z = seat[ch][:, None] + crown[ch][:, None] * np.power(np.clip(1 - rho * rho, 0, 1), power)
            idx = ((iy.astype(np.int64) % N) * N + (ix.astype(np.int64) % N))[inside]
            z = z[inside].astype(np.float32)
            rr = rho[inside].astype(np.float32)
            sid = np.broadcast_to(ch[:, None], inside.shape)[inside]
            order = np.lexsort((z, idx))
            idx, z, rr, sid = idx[order], z[order], rr[order], sid[order]
            last = np.ones(idx.size, bool)
            last[:-1] = idx[1:] != idx[:-1]
            idx, z, rr, sid = idx[last], z[last], rr[last], sid[last]
            win = z > zbest[idx]
            idx, z, rr, sid = idx[win], z[win], rr[win], sid[win]
            zbest[idx], owner[idx], rho_out[idx] = z, sid, rr
    return zbest.reshape(N, N), owner.reshape(N, N), rho_out.reshape(N, N)


def herringbone(spec, rng):
    """Common brick laid flat in a 45-degree herringbone. The 90-degree herringbone of a
    2:1 brick repeats on the lattice (1, 1), (4, 0) in brick widths; turned 45 degrees it
    tiles a square of side 12 * sqrt(2) widths, so a 0.105 m brick-and-joint makes the
    1.782 m tile and the pattern closes on itself at every edge."""
    w = SIZE / (12 * math.sqrt(2))                       # one brick width (with joint), px
    m = mpp(spec)
    yy, xx = np.indices((SIZE, SIZE)).astype(np.float32) + 0.5
    lay = 0.035 * (noise(rng, 22.0) - 0.5) * 2           # the bricklayer's own wander, widths
    qx = (xx + yy) / (math.sqrt(2) * w) + lay
    qy = (yy - xx) / (math.sqrt(2) * w) - lay
    cx, cy = np.floor(qx), np.floor(qy)
    d = np.mod(cx - cy, 4).astype(int)
    x0 = np.select([d == 0, d == 1], [cx, cx - 1], cx)
    y0 = np.select([d == 3], [cy], np.where(d == 2, cy - 1, cy))
    horiz = d <= 1
    x1 = x0 + np.where(horiz, 2, 1)
    y1 = y0 + np.where(horiz, 1, 2)
    # a brick's key, invariant under the tile's own translations (12, +-12) in q
    uu, vv = np.mod(x0 + y0, 24).astype(int), np.mod(y0 - x0, 24).astype(int)
    key = (horiz.astype(int) * 576 + uu * 24 + vv)
    nb = 1152
    # distance to the brick's edge, px, and the coordinate along its length (0..1)
    de = np.minimum(np.minimum(qx - x0, x1 - qx), np.minimum(qy - y0, y1 - qy)) * w
    along = np.where(horiz, (qx - x0) / 2, (qy - y0) / 2)
    across = np.where(horiz, qy - y0, qx - x0)
    joint_half = (0.0055 + 0.0015 * noise(rng, 12.0)) / m  # a 9-14 mm sand joint
    edge_wob = 0.5 * (noise(rng, 1.2) - 0.5) + 0.6 * (noise(rng, 4.0) - 0.5)
    de_j = de - joint_half + edge_wob
    # per brick: tone, a burnt (dark) or a soft salmon one now and then, its settle and tilt
    tone = rng.random(nb).astype(np.float32)
    kind = rng.random(nb)
    tilt_a = (rng.random(nb) - 0.5).astype(np.float32)
    tilt_b = (rng.random(nb) - 0.5).astype(np.float32)
    settle = (rng.random(nb) - 0.5).astype(np.float32)
    chip_k = rng.random(nb)
    chip_c = rng.integers(0, 4, nb)
    crack_k = rng.random(nb)
    crack_t = rng.random(nb).astype(np.float32)
    t_b, kd = tone[key], kind[key]
    traffic = fbm(rng, (90, 40), (0.6, 0.4))              # where feet go: polish, rounder arrises
    worn = clamp01((traffic - 0.45) * 2.2)
    # the arris: a worn brick is a soft pillow, its edge rounded over 3-6 mm
    round_px = (0.003 + 0.004 * worn) / m
    pillow = np.sqrt(clamp01(de_j / round_px))
    face = clamp01(de_j / 0.7)                            # 1 on the brick, 0 in the joint
    # chips: a corner knocked off one brick in ten; a crack across one in fourteen
    cxs = np.where(chip_c[key] % 2 == 0, along, 1 - along)
    cys = np.where(chip_c[key] // 2 == 0, across, 1 - across)
    chip_r = 0.18 + 0.22 * chip_k[key]
    chip = ((chip_k[key] < 0.10) & (np.hypot(cxs * 2, cys) < chip_r + 0.06 * (noise(rng, 1.5) - 0.5)))
    chip = chip.astype(np.float32)
    crack_line = np.abs(along - (0.25 + 0.5 * crack_t[key]) - 0.06 * (noise(rng, 5.0) - 0.5)) * 2 * w
    crack = ((crack_k[key] < 0.07) & (crack_line < 0.6)).astype(np.float32) * face
    fine = noise(rng, 0.6)
    grain = noise(rng, 1.6)
    mott = noise(rng, 7.0)
    pits = clamp01((noise(rng, 0.7) - 0.70) * 5) * face
    lime = clamp01((noise(rng, 0.8) - 0.80) * 6) * face
    # height, metres: the brick face, its tilt and settle, the sunken joint 6-9 mm down
    h = (0.0016 * settle[key] + 0.0014 * (tilt_a[key] * (along - 0.5) * 2 + tilt_b[key] * (across - 0.5) * 2)
         + 0.0004 * (grain - 0.5) + 0.00025 * (fine - 0.5) - 0.0004 * pits)
    h = h - 0.0035 * (1 - pillow)
    sand = -0.0075 + 0.0018 * (noise(rng, 2.5) - 0.5) * 2
    h = np.where(face > 0, h * face + sand * (1 - face), sand)
    h = h - 0.004 * chip * (0.6 + 0.4 * noise(rng, 1.0)) - 0.0018 * crack
    h = np.maximum(h, sand)
    # colour: red-brown commons, per-brick, with a few burnt clinkers and soft salmons
    c_hi, c_lo = np.array(spec["colors"][0], np.float32), np.array(spec["colors"][1], np.float32)
    t = 0.18 + 0.64 * t_b + 0.10 * (mott - 0.5) + 0.10 * (grain - 0.5) + 0.06 * (fine - 0.5)
    color = palette(t, c_hi, c_lo)
    burnt = (kd < 0.09).astype(np.float32)
    salmon = ((kd > 0.93)).astype(np.float32)
    color = mix(color, (78, 50, 44), 0.65 * burnt)
    color = mix(color, (164, 104, 80), 0.55 * salmon)
    # a brick's end often fires darker (flashing)
    flash = clamp01((np.abs(along - 0.5) - 0.32) * 5) * (tone[(key * 7) % nb] > 0.6)
    color = mix(color, (90, 54, 44), 0.35 * flash)
    color = mix(color, (60, 44, 38), 0.45 * pits)
    color = mix(color, (172, 150, 124), 0.35 * lime)
    # grime that ignores the bricks: soot and soil worked in, dust where it is dry
    grime = fbm(rng, (40, 14, 4), (0.5, 0.3, 0.2))
    color *= (1 - 0.16 * (grime - 0.5) * 2 * 0.6 - 0.05)[..., None]
    dusty = clamp01((noise(rng, 18.0) - 0.45) * 2) * (1 - worn)
    color = mix(color, (132, 116, 98), 0.22 * dusty * face)
    color *= (1 + 0.10 * (noise(rng, 0.9) - 0.5))[..., None]
    # worn faces read a little darker and richer, the edges a little dusted
    color *= (1 - 0.06 * worn * face)[..., None]
    dust_edge = clamp01(1 - de_j / 3.0) * face
    color = mix(color, (128, 112, 92), 0.18 * dust_edge)
    # the joint: sand gone to dirt, moss where the feet do not go
    jcol = palette(noise(rng, 1.0) * 0.7 + 0.15, (118, 104, 86), (70, 60, 50))
    shade = clamp01(1 - traffic) * noise(rng, 6.0)
    moss = clamp01((shade - 0.40) * 3.5) * clamp01((noise(rng, 1.4) - 0.35) * 2.5)
    jcol = mix(jcol, (66, 80, 42), 0.85 * moss)
    jcol = mix(jcol, (92, 104, 56), 0.4 * moss * clamp01((fine - 0.5) * 3))
    color = color * face[..., None] + jcol * (1 - face[..., None])
    color = mix(color, (110, 92, 78), 0.55 * chip)        # fresher, paler broken clay
    color = mix(color, (52, 40, 34), 0.7 * crack)
    # roughness: the polish where it is walked, the sand and moss matte
    rough = (0.80 - 0.14 * worn * face + 0.05 * (grain - 0.5) + 0.12 * (1 - face)
             + 0.08 * chip - 0.03 * moss)
    depth = 0.020
    return relief(h, depth), color, clamp01(rough), depth / m


def flagging(spec, rng):
    """Random-rectangular stone flagging: courses 0.6-1.0 m deep, each cut into slabs
    0.5-1.0 m long and now and then split in two, every course shifted so no joint lines
    up with the tile's edge; 10-15 mm joints, slabs settled unevenly."""
    m = mpp(spec)
    S = SIZE
    # courses: depths in px summing to the tile
    while True:
        rows = rng.uniform(0.55, 1.0, 3)
        rows = rows / rows.sum() * spec["span_across_m"]
        if rows.min() >= 0.55 and rows.max() <= 1.0:
            break
    yb = np.concatenate(([0], np.round(np.cumsum(rows) / m).astype(int)))
    yb[-1] = S
    slab = np.zeros((S, S), np.int32)
    x0m = np.zeros((S, S), np.float32)
    x1m, y0m, y1m = x0m.copy(), x0m.copy(), x0m.copy()
    xx = np.arange(S, dtype=np.float32) + 0.5
    sid = 0
    for r in range(3):
        ys, ye = yb[r], yb[r + 1]
        while True:
            ws = []
            while sum(ws) < spec["span_m"] - 1.0:
                ws.append(float(rng.uniform(0.5, 1.0)))
            rest = spec["span_m"] - sum(ws)
            if 0.5 <= rest <= 1.0:
                ws.append(rest)
                break
        off = rng.uniform(0, S)
        xs = (xx - off) % S
        xb = np.concatenate(([0], np.cumsum(ws) / m))
        xb[-1] = S
        for j in range(len(ws)):
            a, b = xb[j], xb[j + 1]
            cols = (xs >= a) & (xs < b)
            split = rng.random() < 0.5 and (ye - ys) * m > 0.7
            cut = ys + int((ye - ys) * rng.uniform(0.38, 0.62)) if split else ye
            for (ya, yz) in ((ys, cut), (cut, ye)) if split else ((ys, ye),):
                yyl = np.arange(ya, yz, dtype=np.float32)[:, None] + 0.5
                slab[ya:yz, cols] = sid
                x0m[ya:yz, cols] = (xs - a)[cols][None, :]
                x1m[ya:yz, cols] = (b - xs)[cols][None, :]
                y0m[ya:yz, cols] = yyl - ya
                y1m[ya:yz, cols] = yz - yyl
                sid += 1
    n = sid
    de = np.minimum(np.minimum(x0m, x1m), np.minimum(y0m, y1m))
    # local coordinates across each slab, -1..1, for its tilt
    lu = (x0m - x1m) / np.maximum(x0m + x1m, 1)
    lv = (y0m - y1m) / np.maximum(y0m + y1m, 1)
    joint_half = (0.006 + 0.0015 * noise(rng, 30.0)) / m
    ragged = 1.3 * (noise(rng, 1.0) - 0.5) + 1.6 * (noise(rng, 3.5) - 0.5) + 1.2 * (noise(rng, 9.0) - 0.5)
    de_j = de - joint_half + ragged
    # each slab's stone: a continuous run from buff-grey limestone (0) to blue-grey flag (1),
    # most of a yard's flags from one quarry and a few from another
    litho = np.clip(rng.beta(1.6, 2.6, n) + (rng.random(n) < 0.18) * 0.45, 0, 1).astype(np.float32)
    tone = rng.random(n).astype(np.float32)
    tilt_u = (rng.random(n) - 0.5).astype(np.float32)
    tilt_v = (rng.random(n) - 0.5).astype(np.float32)
    settle = (rng.random(n) - 0.5).astype(np.float32)
    bed_dir = rng.random(n) < 0.5
    blend = rng.random(n).astype(np.float32)
    blue = litho[slab]
    face = clamp01(de_j / 1.2)
    arris = np.sqrt(clamp01(de_j / (0.007 / m)))
    cleft = fbm(rng, (14, 5, 1.8), (0.5, 0.3, 0.2))
    fine = noise(rng, 0.6)
    grit = noise(rng, 1.1)
    # bedding: faint lamination streaks along the slab's long way (cleft stone)
    bed_x = noise(rng, (0.8, 9.0))
    bed_y = noise(rng, (9.0, 0.8))
    bed = np.where(bed_dir[slab], bed_x, bed_y)
    # within-slab mottle, decorrelated slab to slab by blending two fields
    mot_a, mot_b = fbm(rng, (30, 10, 3), (0.5, 0.3, 0.2)), fbm(rng, (30, 10, 3), (0.5, 0.3, 0.2))
    mot = mot_a * blend[slab] + mot_b * (1 - blend[slab])
    spall = clamp01((noise(rng, 4.0) - 0.64) * 4) * clamp01(1 - de_j / (0.045 / m))
    h = (0.0022 * settle[slab] + 0.0030 * (tilt_u[slab] * lu + tilt_v[slab] * lv)
         + 0.0012 * (cleft - 0.5) + 0.00025 * (fine - 0.5) + 0.0002 * (grit - 0.5)
         + 0.00025 * (bed - 0.5))
    h = h - 0.003 * (1 - arris) - 0.0025 * spall
    bottom = -0.009 + 0.002 * (noise(rng, 2.0) - 0.5) * 2
    h = np.where(face > 0, h * face + bottom * (1 - face), bottom)
    h = np.maximum(h, bottom)
    # colour: buff-grey to blue-grey, per slab, mottled within it
    t = 0.30 + 0.40 * tone[slab] + 0.22 * (mot - 0.5) + 0.08 * (cleft - 0.5) + 0.07 * (fine - 0.5)
    buff = palette(t, (162, 154, 138), (120, 113, 100))
    bluec = palette(t, (140, 142, 140), (100, 103, 104))
    color = buff * (1 - blue[..., None]) + bluec * blue[..., None]
    color *= (1 + 0.06 * (bed - 0.5) + 0.12 * (grit - 0.5) + 0.06 * (fine - 0.5))[..., None]
    # weathering: soot-and-water darkening, an iron stain, lichen dots, a worn path
    damp = fbm(rng, (40, 16, 6), (0.5, 0.3, 0.2))
    color *= (1 - 0.18 * clamp01((damp - 0.45) * 2.2))[..., None]
    edge_dirt = clamp01(1 - de_j / (0.04 / m)) * face
    color = mix(color, (98, 90, 76), 0.35 * edge_dirt * noise(rng, 3.0))
    rust = stamps(rng, 5, 9.0) * clamp01((noise(rng, 2.5) - 0.4) * 2)
    color = mix(color, (140, 108, 74), 0.30 * rust * (1 - blue))
    lich_w = clamp01((noise(rng, 0.9) - 0.76) * 6) * clamp01((damp - 0.45) * 3) * face
    lich_b = clamp01((noise(rng, 0.8) - 0.78) * 6) * clamp01((damp - 0.5) * 3) * face
    color = mix(color, (184, 182, 170), 0.45 * lich_w)
    color = mix(color, (58, 58, 52), 0.45 * lich_b)
    worn = clamp01((fbm(rng, (80, 30), (0.6, 0.4)) - 0.55) * 2.5)
    color = mix(color, (166, 160, 146), 0.10 * worn * face)
    color = mix(color, (128, 120, 106), 0.40 * spall)
    # the joint: dark soil, grass and moss creeping along some of it
    jsoil = palette(noise(rng, 1.2), (112, 100, 82), (64, 56, 46))
    green = clamp01((noise(rng, 20.0) - 0.40) * 3) * clamp01((noise(rng, 1.2) - 0.30) * 2.2)
    jcol = mix(jsoil, (70, 86, 42), 0.85 * green)
    jcol = mix(jcol, (96, 112, 56), 0.5 * green * clamp01((fine - 0.5) * 3))
    color = color * face[..., None] + jcol * (1 - face[..., None])
    # a few blades leaning out over the arris where the joint is green
    jt = (face < 0.5) & (green > 0.5)
    ys_, xs_ = np.nonzero(jt)
    pick = rng.random(ys_.size) < 0.035
    segs = []
    for y0, x0 in zip(ys_[pick], xs_[pick]):
        a_ = rng.random() * 2 * math.pi
        L = 2 + 4 * rng.random()
        segs.append((float(y0), float(x0), y0 + L * math.sin(a_), x0 + L * math.cos(a_), 0.6 + 0.4 * rng.random()))
    blades = downsample(strokes(rng, segs, ss=2, width=1), 2)
    color = mix(color, (84, 102, 48), 0.75 * blades)
    h = h + 0.0015 * blades * (face < 0.9)
    rough = (0.86 + 0.05 * (fine - 0.5) + 0.04 * (cleft - 0.5) - 0.10 * worn * face
             + 0.08 * (1 - face) - 0.04 * blue * face + 0.04 * spall)
    depth = 0.024
    return relief(h, depth), color, clamp01(rough), depth / m


def gravel(spec, rng):
    """Raked pea gravel: rounded stones 5-15 mm, tan, grey, buff and a few white, packed
    over a dusty bed, the rake's tines leaving faint ridges along x."""
    m = mpp(spec)
    ss = 2
    N = SIZE * ss
    area = (spec["span_m"] * spec["span_across_m"])
    dmm = np.clip(rng.lognormal(math.log(8.5), 0.32, 120000), 5.0, 15.0)
    # fill to ~1.45x coverage so the stones bury each other as a raked bed does
    cover = np.cumsum(math.pi * (dmm / 2000) ** 2 * 0.80)
    n = int(np.searchsorted(cover, area * 1.45))
    dmm = dmm[:n]
    cy, cx = rng.random(n) * SIZE, rng.random(n) * SIZE
    asp = rng.uniform(0.62, 1.0, n)
    a = (dmm / 2000) / m
    b = a * asp
    theta = rng.random(n) * math.pi
    # the rake: shallow ridges every ~28 mm across y, wandering (a whole number per tile)
    tine = SIZE / round(spec["span_across_m"] / 0.028)
    wander = noise(rng, 30.0)
    ridge_at = lambda y, x: np.sin(2 * math.pi * (y + 6 * (wander[(y.astype(int)) % SIZE, (x.astype(int)) % SIZE] - 0.5)) / tine)
    seat_rake = 0.0016 * ridge_at(cy, cx) * (0.5 + noise(rng, 40.0)[cy.astype(int) % SIZE, cx.astype(int) % SIZE])
    crown = (dmm / 1000) * rng.uniform(0.32, 0.5, n)
    seat = -crown * rng.uniform(0.15, 0.85, n) + seat_rake
    ground = (-0.004 + 0.0012 * (noise(rng, 3.0, (N, N)) - 0.5)).astype(np.float32)
    hz, owner, rho = rounded_stones(rng, n, cy, cx, a, b, theta, crown, seat, ground, ss, power=0.6, lumpy=0.22)
    # stone colours: the river-and-pit mix of a pea gravel
    pal = np.array([(168, 152, 126), (148, 142, 132), (128, 120, 108), (182, 172, 154),
                    (118, 102, 84), (156, 122, 96), (204, 200, 190), (100, 96, 92)], np.float32)
    wts = np.array([0.24, 0.20, 0.16, 0.12, 0.10, 0.08, 0.05, 0.05])
    pick = rng.choice(len(pal), n, p=wts)
    jit = rng.uniform(0.86, 1.12, (n, 1)).astype(np.float32)
    scol = pal[pick] * jit
    speck = noise(rng, 0.6, (N, N))
    soil = palette(noise(rng, 4.0, (N, N)), (134, 122, 104), (98, 88, 76))
    has = owner >= 0
    col = np.where(has[..., None], scol[np.maximum(owner, 0)], soil)
    # within a stone: a darker rim where it turns down, a pale dust on its crown, specks
    col = col * (1 - 0.12 * np.clip(rho, 0, 1) ** 3 * has)[..., None]
    col = mix(col, (178, 168, 150), 0.14 * clamp01(1 - rho) * has)
    col = col * (1 + 0.06 * (speck - 0.5) * has)[..., None]
    rough_ss = np.where(has, 0.62 + 0.18 * np.clip(rho, 0, 1), 0.95).astype(np.float32)
    # a half-pixel soften: the stones' rims are rounded, not stepped at the pixel
    h = blur(downsample(hz, ss), 0.5)
    color = downsample(col, ss)
    rough = blur(downsample(rough_ss, ss), 0.7)
    # contact shadow in the gaps: the bed reads darker under the stones
    gap = clamp01((blur(h, 1.2) - h) / 0.002)
    color *= (1 - 0.14 * gap)[..., None]
    # a raked bed is never even: finer, dustier stretches and cleaner, darker ones
    color *= (1 + 0.07 * (fbm(rng, (40, 14), (0.6, 0.4)) - 0.5) * 2)[..., None]
    depth = 0.020
    return relief(h, depth), color, clamp01(rough), depth / m


def earth(spec, rng):
    """A trodden service yard: compacted brown-grey earth, footworn hollows paler and
    smoother, the untrodden ground darker and looser with thin grass at its margins,
    a scatter of cinders and pebbles."""
    m = mpp(spec)
    traffic = fbm(rng, (70, 30, 12), (0.60, 0.28, 0.12))
    worn = clamp01((traffic - 0.42) * 2.4)
    loose = 1 - worn
    base = fbm(rng, (24, 8, 3, 1.2), (0.30, 0.30, 0.24, 0.16))
    grit = noise(rng, 0.5)
    sandy = noise(rng, 0.9)
    crumbs = clamp01((noise(rng, 0.9) - 0.58) * 4) * (0.35 + 0.65 * loose)
    # a dried crust on the walked ground, faintly broken into plates
    _, _, crack_e = voronoi(rng, 700)
    crack = blur(crack_e, 0.5) * clamp01((worn - 0.4) * 2) * clamp01((noise(rng, 8.0) - 0.45) * 3)
    # dusty bare patches against darker, damper soil, with edges you can see
    patches = clamp01((fbm(rng, (14, 5, 2), (0.5, 0.3, 0.2)) - 0.5) * 2.2 + 0.5)
    # scuffs: short smoothed streaks where boots and baskets drag
    scuff = blur(stamps(rng, 30, 5.0, elongate=3.0) * noise(rng, 2.0), 0.8) * worn
    h = (0.004 * (base - 0.5) + 0.0016 * (grit - 0.5) + 0.0008 * (sandy - 0.5) + 0.0012 * crumbs
         - 0.003 * worn + 0.0015 * loose * (noise(rng, 3.0) - 0.5) - 0.0004 * crack
         + 0.0008 * (patches - 0.5) - 0.0006 * scuff)
    color = palette(0.50 + 0.16 * (base - 0.5) + 0.22 * (grit - 0.5) + 0.12 * (sandy - 0.5),
                    (144, 132, 112), (96, 86, 72))
    color = mix(color, (152, 140, 120), 0.26 * patches * (0.4 + 0.6 * worn))   # dusty and pale
    color = mix(color, (92, 82, 68), 0.24 * (1 - patches) * (0.5 + 0.5 * loose))  # damper, humus
    color = mix(color, (112, 98, 82), 0.40 * crumbs)
    color = mix(color, (140, 130, 112), 0.25 * scuff)
    color = mix(color, (96, 88, 76), 0.25 * crack)
    # cinders (black, sparkly-matte) and pebbles
    nc = 1100
    cy, cx = rng.random(nc) * SIZE, rng.random(nc) * SIZE
    dmm = np.clip(rng.lognormal(math.log(7.0), 0.5, nc), 4.0, 26.0)
    a = dmm / 2000 / m
    is_cinder = rng.random(nc) < 0.40
    crown = dmm / 1000 * np.where(is_cinder, 0.25, 0.35)
    seat = h[cy.astype(int), cx.astype(int)] - crown * rng.uniform(0.2, 0.75, nc)
    ss = 2
    ground = np.repeat(np.repeat(h, ss, 0), ss, 1).astype(np.float32)
    hz, owner, rho = rounded_stones(rng, nc, cy, cx, a, a * rng.uniform(0.55, 1.0, nc),
                                    rng.random(nc) * math.pi, crown, seat, ground, ss, power=0.5, lumpy=0.35)
    scol = np.where(is_cinder[:, None], np.array((46, 44, 42), np.float32) * rng.uniform(0.8, 1.3, (nc, 1)),
                    np.array((150, 142, 128), np.float32) * rng.uniform(0.7, 1.15, (nc, 1))
                    * rng.uniform(0.92, 1.08, (nc, 3)))
    has_ss = owner >= 0
    stone_col = np.where(has_ss[..., None], scol[np.maximum(owner, 0)], 0)
    has = downsample(has_ss.astype(np.float32), ss)
    stone_col = downsample(stone_col, ss) / np.maximum(has, 1e-6)[..., None]
    color = color * (1 - has[..., None]) + stone_col * has[..., None]
    h = downsample(hz, ss)
    # thin grass at the margins of the untrodden ground: tufts of short strokes
    margin = clamp01(1 - np.abs(traffic - 0.40) / 0.06) * clamp01((noise(rng, 6.0) - 0.35) * 3)
    margin = np.maximum(margin, clamp01((0.30 - traffic) * 5) * 0.35)
    cand = np.nonzero(margin.ravel() > 0.3)[0]
    wsel = margin.ravel()[cand]
    nt = min(260, cand.size)
    tufts = rng.choice(cand, nt, replace=False, p=wsel / wsel.sum()) if nt else np.array([], int)
    segs = []
    for t_ in tufts:
        ty, tx = divmod(int(t_), SIZE)
        for _ in range(int(4 + rng.integers(0, 9))):
            ang = rng.random() * 2 * math.pi
            L = (0.012 + 0.03 * rng.random()) / m
            oy, ox = rng.normal(0, 1.2, 2)
            segs.append((ty + oy, tx + ox, ty + oy + L * math.sin(ang), tx + ox + L * math.cos(ang),
                         0.5 + 0.5 * rng.random()))
    blades = downsample(strokes(rng, segs, ss=2, width=1), 2)
    gcol = palette(noise(rng, 1.0), (124, 128, 72), (82, 92, 50))
    color = mix(color, gcol, 0.75 * clamp01(blades * 1.3))
    h = h + 0.003 * blades
    pebble = downsample((has_ss & ~is_cinder[np.maximum(owner, 0)]).astype(np.float32), ss)
    rough = 0.92 - 0.10 * worn - 0.06 * scuff + 0.04 * (grit - 0.5) - 0.12 * pebble
    depth = 0.020
    return relief(h, depth), color, clamp01(rough), depth / m


def loam(spec, rng):
    """Freshly dug and raked garden loam: a dark crumb, the rake's tines drawn along x
    every ~30 mm, clods and a few small stones left on top."""
    m = mpp(spec)
    ss = 2
    N = SIZE * ss
    tine = SIZE / round(spec["span_across_m"] / 0.030)    # a whole number of tines per tile
    yy, xx = np.indices((SIZE, SIZE)).astype(np.float32)
    wav = 5.0 * (noise(rng, (40.0, 60.0)) - 0.5) + 1.2 * (noise(rng, 6.0) - 0.5)
    ph = (yy + wav) / tine
    ph = ph + 0.18 * (noise(rng, (3.0, 8.0)) - 0.5) * 2
    k = np.floor(ph + 0.5)
    dist = np.abs(ph - k) * tine                           # px from the nearest tine's track
    n_t = int(round(SIZE / tine))
    t_amp = rng.uniform(0.3, 1.0, n_t).astype(np.float32)[np.mod(k, n_t).astype(int)]
    t_w = 1.3 + 1.2 * noise(rng, (4.0, 12.0))
    track = np.exp(-(dist / t_w) ** 2) * t_amp
    heave = np.exp(-((dist - 1.9 * t_w) / t_w) ** 2) * t_amp
    groove = 1 - track                                      # 0 in a tine's track
    rake_amp = clamp01((noise(rng, (14.0, 50.0)) - 0.30) * 1.8) * (0.6 + 0.4 * noise(rng, 3.0))
    base = fbm(rng, (30, 10, 3.5, 1.2), (0.30, 0.28, 0.24, 0.18))
    crumb = fbm(rng, (0.7, 1.4, 2.6), (0.4, 0.35, 0.25))
    h = (0.006 * (base - 0.5) + rake_amp * (0.0030 * (groove - 0.5) + 0.0010 * heave)
         + 0.0028 * (crumb - 0.5))
    ground = np.repeat(np.repeat(h, ss, 0), ss, 1).astype(np.float32)
    # clods and crumbs as lumpy stones of soil; a few true pebbles
    nclod = 26000
    dmm = np.clip(rng.lognormal(math.log(6.0), 0.55, nclod), 3.0, 45.0)
    cy, cx = rng.random(nclod) * SIZE, rng.random(nclod) * SIZE
    a = dmm / 2000 / m
    crown = dmm / 1000 * rng.uniform(0.25, 0.45, nclod)
    seat = -crown * rng.uniform(0.25, 0.85, nclod) + 0.0018 * rake_amp[cy.astype(int), cx.astype(int)] * (
        groove[cy.astype(int), cx.astype(int)] - 0.5)
    peb = rng.random(nclod) < 0.006
    hz, owner, rho = rounded_stones(rng, nclod, cy, cx, a, a * rng.uniform(0.55, 1.0, nclod),
                                    rng.random(nclod) * math.pi, crown, seat, ground, ss, power=0.45, lumpy=0.45)
    h = downsample(hz, ss)
    has_ss = owner >= 0
    # moisture: the dug soil is darker in the furrow bottoms, its exposed crumb tops dry paler
    hl = h - blur(h, 3.0)
    dry = clamp01(0.5 + hl / 0.003)
    color = palette(0.45 + 0.25 * (base - 0.5) + 0.25 * (crumb - 0.5), (92, 76, 60), (58, 48, 40))
    color = mix(color, (108, 92, 74), 0.45 * dry * clamp01((noise(rng, 2.0) - 0.3) * 2))
    color = mix(color, (52, 44, 38), 0.25 * (1 - groove) * rake_amp)
    ccol = palette(rng.random(nclod), (104, 88, 70), (66, 54, 44))
    ccol = np.where(peb[:, None], np.array((136, 130, 120), np.float32) * rng.uniform(0.8, 1.15, (nclod, 1)), ccol)
    clod_ss = np.where(has_ss[..., None], ccol[np.maximum(owner, 0)], 0)
    clod_ss = clod_ss * (1 - 0.25 * np.clip(rho, 0, 1) ** 2)[..., None]
    has = downsample(has_ss.astype(np.float32), ss)
    clod = downsample(clod_ss, ss) / np.maximum(has, 1e-6)[..., None]
    color = color * (1 - has[..., None]) + clod * has[..., None]
    gap = clamp01((blur(h, 1.0) - h) / 0.002)
    color *= (1 - 0.25 * gap)[..., None]
    pebs = downsample((has_ss & peb[np.maximum(owner, 0)]).astype(np.float32), ss)
    rough = 0.93 + 0.03 * (crumb - 0.5) - 0.25 * pebs - 0.04 * (1 - dry)
    depth = 0.030
    return relief(h, depth), color, clamp01(rough), depth / m


SURFACES = {"asphalt": asphalt, "macadam": macadam, "brick": brick, "cinder": cinders,
            "walk": walk, "curb": curb, "grass": grass,
            "herringbone": herringbone, "flagging": flagging, "gravel": gravel,
            "earth": earth, "loam": loam}


# ---------------------------------------------------------------------------- maps

def maps_from_height(h, strength):
    # gx is dh/dcol and gy is dh/drow, and a row runs DOWN the image. The OpenGL map's
    # green is +V, which runs UP it (three.js loads with flipY, so row 0 is v = 1), so
    # n = (-dh/du, -dh/dv, 1) = (-gx, +gy, 1). Until T-2296 this wrote -gy, which is the
    # DirectX map filed under the OpenGL name, and every street the renderer bound was
    # lit with its relief upside down across the street.
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    n = np.stack((-gx, gy, np.ones_like(h)), axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    gl = n * 0.5 + 0.5
    dx = gl.copy()
    dx[..., 1] = 1 - dx[..., 1]
    local = blur(h, 5) - h
    ao = clamp01(1 - np.maximum(local, 0) * 2.6)
    return gl, dx, ao


def as_u8(a):
    return np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)


def _write(path: Path, image: Image.Image, fmt: str, **kw):
    buf = io.BytesIO()
    image.save(buf, format=fmt, **kw)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(buf.getvalue())
    tmp.replace(path)


def save_png8(path, a):
    _write(path, Image.fromarray(as_u8(a)), "PNG", compress_level=9)


def save_png16(path, a):
    _write(path, Image.fromarray(np.clip(a * 65535 + 0.5, 0, 65535).astype(np.uint16)), "PNG", compress_level=9)


def save_jpg(path, a, quality):
    _write(path, Image.fromarray(as_u8(a)), "JPEG", quality=quality, optimize=True, subsampling=0)


def build(out: Path) -> list[dict]:
    manifest = []
    for i, spec in enumerate(MATERIALS):
        seed = 19040701 + i * 101
        rng = np.random.default_rng(seed)
        h, color, rough, strength = SURFACES[spec["kind"]](spec, rng)
        ngl, ndx, ao = maps_from_height(h, strength)
        metal = np.zeros_like(h)
        orm = np.stack((ao, rough, metal), axis=-1)
        d = out / spec["group"] / spec["id"]
        d.mkdir(parents=True, exist_ok=True)
        stem = spec["id"]
        save_png8(d / f"{stem}_basecolor.png", color / 255.0)
        save_png8(d / f"{stem}_normal_gl.png", ngl)
        save_png8(d / f"{stem}_normal_dx.png", ndx)
        save_png8(d / f"{stem}_roughness.png", rough)
        save_png16(d / f"{stem}_height16.png", h)
        save_png8(d / f"{stem}_ao.png", ao)
        save_png8(d / f"{stem}_metallic.png", metal)
        save_png8(d / f"{stem}_orm.png", orm)
        q_base, q_normal, q_orm = spec.get("web_quality", (86, 92, 90))
        save_jpg(d / f"{stem}_basecolor_web.jpg", color / 255.0, q_base)
        save_jpg(d / f"{stem}_normal_gl_web.jpg", ngl, q_normal)
        save_jpg(d / f"{stem}_orm_web.jpg", orm, q_orm)
        across = spec["span_across_m"]
        own = ("span_across_m", "orientation", "confidence", "web_quality")
        data = {
            **{k: v for k, v in spec.items() if k not in own},
            "span_along_m": spec["span_m"],
            "span_across_m": across,
            "resolution_px": SIZE,
            "px_per_m": round(SIZE / spec["span_m"], 2),
            "confidence": spec.get("confidence", "reconstructed appearance; which surface carries it is data/street_surfaces/1904.json's to say"),
            "orientation": spec.get("orientation", "image x = along the street (renderer u); image y = across it (v)"
                                    + ("; v spans the band's own width" if across == "band" else "")),
            "color_space": {"basecolor": "sRGB", "normal_gl": "linear", "normal_dx": "linear",
                            "roughness": "linear", "height16": "linear 16-bit", "ao": "linear",
                            "metallic": "linear", "orm": "linear; R=AO G=Roughness B=Metallic"},
            "web": {s: f"{stem}_{s}_web.jpg" for s in WEB_SUFFIXES},
            "seamless": True,
            "generator_seed": seed,
            "generation_method": "deterministic procedural synthesis (tools/generate_prairie_1904_pbr.py); no photograph sampled",
        }
        (d / "material.json").write_text(json.dumps(data, indent=2) + "\n")
        manifest.append(data)
    (out / "manifest.json").write_text(json.dumps(
        {"library": "Prairie Avenue 1904 street-surface PBR materials", "version": "1.1.0",
         "ticket": "T-1728", "materials": manifest}, indent=2) + "\n")
    contact_sheet(out, manifest)
    return manifest


def contact_sheet(out: Path, manifest: list[dict]):
    thumb, label, cols = 200, 46, 4
    rows = math.ceil(len(manifest) / cols)
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + label)), (26, 27, 25))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, m in enumerate(manifest):
        p = out / m["group"] / m["id"] / f'{m["id"]}_basecolor.png'
        im = Image.open(p).convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS)
        x, y = (i % cols) * thumb, (i // cols) * (thumb + label)
        sheet.paste(im, (x, y))
        draw.text((x + 6, y + thumb + 6), m["id"].replace("_", " "), font=font, fill=(235, 232, 220))
        across = m["span_across_m"]
        draw.text((x + 6, y + thumb + 22),
                  f'{m["span_m"]:.2f} m along x {"band" if across == "band" else f"{across:.2f} m"}',
                  font=font, fill=(166, 169, 157))
    buf = io.BytesIO()
    sheet.save(buf, format="JPEG", quality=88, optimize=True)
    (out / "contact_sheet.jpg").write_bytes(buf.getvalue())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent)
    a = ap.parse_args()
    for m in build(a.out):
        print(f'{m["group"]}/{m["id"]}: {m["span_m"]:.3f} m along, {m["px_per_m"]} px/m')


if __name__ == "__main__":
    main()
