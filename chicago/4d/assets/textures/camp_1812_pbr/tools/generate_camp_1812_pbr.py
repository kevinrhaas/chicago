#!/usr/bin/env python3
"""Build the 1812 Potawatomi camp's surface library (T-3342).

    python3 assets/textures/camp_1812_pbr/tools/generate_camp_1812_pbr.py

Three seamless, deterministic tiles for the natural coverings of the camp of the August
1812 gathering on the State Street creek, in the 1835 library's map-for-map layout
(base colour, OpenGL normal, ORM, height) at 1024 px, plus a 512 px `_web.jpg` of the
three maps the renderer binds:

- **cattail_mat** — a lodge mat of cattail leaves laid side by side and sewn through
  with bark cord. Wau-Bun ch. VII: the rushes "laid side by side, and fastened at each
  extremity, they pass their shuttle, a long flat needle made of bone, to which is
  attached a piece of cordage formed of the bark of a tree, through each rush". Forsyth
  (1827) names the plant, "puc-wy ... a kind of rushes or flags" (Blair 1912 v2 p. 227),
  which Gerard's note there reads as the cat-tail flag, Typha latifolia. Image y is UP
  the lodge (the leaves run up it, to shed the rain); image x is round it, and the cord
  rows cross the leaves, eight to the metre.
- **elm_bark** — the outer face of a sheet of elm bark, the summer house's covering
  (Forsyth: the "bark huts or summer residences"; Wau-Bun's "neat bark wigwams"). Grey
  ridges of cork interlacing over red-brown furrows, the grain up the image, with a
  little lichen.
- **bough_thatch** — the leafy boughs laid over an arbor's poles (Skinner 1927, a Prairie
  Potawatomi narrator's "bough arbor"), a few days cut and starting to brown.

No photograph is embedded, sampled or traced: every map is procedural. The look of each is
a reconstruction bounded by the texts above (docs/LIBERTIES.md L-1812-potawatomi-camp-2515).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

SIZE = 1024
WEB = 512
LIB = Path(__file__).resolve().parent.parent

MATERIALS = [
    dict(id="cattail_mat", span_m=1.0, seed=18120814, mean_roughness=0.88,
         note="A lodge mat of cattail leaves (Typha latifolia) laid side by side and sewn "
              "through with bark cord in rows 125 mm apart: Wau-Bun ch. VII's method, "
              "Forsyth's 'puc-wy'. Leaves run up the image. Colour, leaf widths and wear "
              "are reconstructed."),
    dict(id="elm_bark", span_m=1.2, seed=18120815, mean_roughness=0.93,
         note="The outer face of a sheet of elm bark: interlacing grey cork ridges over "
              "red-brown furrows, grain up the image, a little lichen. The covering of "
              "the summer bark house (Forsyth 1827; Wau-Bun). Reconstructed appearance."),
    dict(id="bough_thatch", span_m=1.5, seed=18120816, mean_roughness=0.90,
         note="Cut leafy boughs laid over an arbor's poles, a few days wilted: green "
              "going to brown, twigs between. Skinner 1927's 'bough arbor'. Reconstructed."),
    # T-3401: the hay of the stacks at Lee's Place (generators/archetypes/haystack.py).
    dict(id="hay_stack", span_m=1.2, seed=18120406, mean_roughness=0.92, group="hay_1812",
         liberty="L-1812-lees-place-haystacks-2510",
         note="The outside of a round stack of prairie hay, pitched by fork and combed down "
              "so it sheds the rain: cured stems and blades lying down the slope in "
              "forkfuls, straw gold through tan to grey-green, dark gaps between. Image y "
              "is UP the stack. Reconstructed (Wau-Bun ch. XVIII puts the stacks; no "
              "picture of them exists)."),
    dict(id="hay_weathered", span_m=1.2, seed=18120407, mean_roughness=0.95, group="hay_1812",
         liberty="L-1812-lees-place-haystacks-2510",
         note="The thatch of a stack that has stood through weather: the outer hay bleached "
              "to silver-grey and brown, matted flat by rain, with dark damp streaks and "
              "spots of mould. Image y is UP the stack. Reconstructed."),
    dict(id="hay_cut", span_m=0.9, seed=18120408, mean_roughness=0.90, group="hay_1812",
         liberty="L-1812-lees-place-haystacks-2510",
         note="The inside of a stack where hay has been pulled or cut out of it for the "
              "stock: the packed hay of the heart, greener and brighter than the outside, "
              "stems every way in layers. Reconstructed."),
]


def norm01(a):
    lo, hi = float(a.min()), float(a.max())
    return (a - lo) / max(hi - lo, 1e-9)


def noise(rng, shape, sigma):
    """Periodic smooth noise: white noise blurred with wrap-around, so it tiles."""
    a = rng.standard_normal(shape).astype(np.float32)
    if isinstance(sigma, (tuple, list)):
        a = ndimage.gaussian_filter(a, sigma=sigma, mode="wrap")
    else:
        a = ndimage.gaussian_filter(a, sigma=sigma, mode="wrap")
    return norm01(a)


def fbm(rng, shape, sigmas, weights):
    out = np.zeros(shape, np.float32)
    for s, w in zip(sigmas, weights):
        out += w * noise(rng, shape, s)
    return norm01(out)


def normal_from_height(h, strength):
    """OpenGL (+Y up the image) normal from a height map in [0, 1], wrapping."""
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    # image rows grow DOWN; +Y (green) points up the image, so a height that rises
    # toward the top row (smaller row index) tilts the normal +Y: ny = +dy.
    nx, ny, nz = -dx, dy, np.ones_like(h)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / ln, ny / ln, nz / ln], -1)
    return ((n * 0.5 + 0.5) * 255.0 + 0.5).clip(0, 255).astype(np.uint8)


def ao_from_height(h, radius=6.0, depth=1.0):
    blur = ndimage.gaussian_filter(h, radius, mode="wrap")
    cav = np.clip((blur - h) * depth * 6.0, 0.0, 1.0)
    return np.clip(1.0 - cav, 0.0, 1.0)


def to_u8(rgb):
    return (np.clip(rgb, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def lerp(a, b, t):
    t = t[..., None] if np.ndim(t) == 2 else t
    return np.asarray(a, np.float32) * (1 - t) + np.asarray(b, np.float32) * t


# ------------------------------------------------------------------ cattail mat

def cattail_mat(seed):
    rng = np.random.default_rng(seed)
    S = SIZE
    px_m = S / 1.0
    y, x = np.mgrid[0:S, 0:S].astype(np.float32)
    # Leaf columns: widths 12-28 mm, summing exactly to the tile so it wraps.
    widths = []
    while sum(widths) < S:
        widths.append(rng.uniform(0.012, 0.028) * px_m)
    widths = np.array(widths)
    widths *= S / widths.sum()
    edges = np.concatenate([[0], np.cumsum(widths)])
    # each leaf wanders a little sideways up the mat (a periodic wobble)
    wob = (noise(rng, (S, 1), (90, 0))[:, 0] - 0.5) * 4.0
    lean = (noise(rng, (1, S), (0, 30))[0] - 0.5) * 3.0
    xs = (x + wob[:, None] + lean[None, :] * (y / S)) % S
    idx = np.searchsorted(edges, xs, side="right") - 1
    idx = np.clip(idx, 0, len(widths) - 1)
    left = edges[idx]
    w = widths[idx]
    t = (xs - left) / w                      # 0..1 across the leaf
    # leaf cross-section: a flattened, slightly cupped blade with a midrib
    blade = np.sin(np.pi * np.clip(t, 0, 1)) ** 0.35
    midrib = np.exp(-((t - 0.5) / 0.06) ** 2) * 0.12
    # per-leaf colour: straw, olive, weathered grey, each a little different
    n = len(widths)
    # neighbouring leaves came off the same bundle, so the hue drifts across the mat
    # rather than jumping leaf to leaf
    walk = ndimage.gaussian_filter1d(rng.standard_normal(n), 3.0, mode="wrap")
    hue = np.clip(0.5 + walk / (3.6 * walk.std() + 1e-9) + rng.uniform(-0.08, 0.08, n), 0, 1)
    tone = rng.uniform(0.88, 1.08, n)
    straw = np.array([0.58, 0.49, 0.33])
    olive = np.array([0.47, 0.44, 0.30])
    grey = np.array([0.50, 0.47, 0.41])
    base = np.where(hue[:, None] < 0.45, straw * (1 - hue[:, None] / 0.45) + olive * (hue[:, None] / 0.45),
                    olive * (1 - (hue[:, None] - 0.45) / 0.55) + grey * ((hue[:, None] - 0.45) / 0.55))
    base = base * tone[:, None]
    col = base[idx]
    # each leaf's tone wanders along its length (a leaf is paler at its tip, and the
    # sun reached some of it more than the rest)
    along = noise(rng, (S, 64), (50, 0.01))
    col = col * (0.88 + 0.24 * np.take_along_axis(along, idx % 64, 1)[..., None])
    # long fibres along each leaf: noise stretched up the image
    fib = noise(rng, (S, S), (24, 0.7))
    col = col * (0.86 + 0.24 * fib[..., None])
    # cord rows: eight to the metre, each a twisted bark cord 7 mm across
    rows = 8
    pitch = S / rows
    phase = (y + (noise(rng, (1, S), (0, 60))[0] - 0.5)[None, :] * 6.0) % pitch
    dcord = np.abs(phase - pitch / 2)
    cord_w = 0.0035 * px_m
    cord = np.clip(1.0 - dcord / cord_w, 0, 1)
    twist = 0.5 + 0.5 * np.sin((x + y * 0.9) * 2 * np.pi / (0.006 * px_m))
    cord_col = np.array([0.33, 0.25, 0.16]) * (0.8 + 0.35 * twist[..., None])
    # the leaves are pulled in under each cord
    pull = np.exp(-(dcord / (0.012 * px_m)) ** 2)
    # weathering: broad blotches, greyer and paler where the sun and rain reached
    wx = fbm(rng, (S, S), (180, 70, 22), (0.5, 0.3, 0.2))
    col = lerp(col, col * 0.78 + np.array([0.10, 0.10, 0.10]), np.clip((wx - 0.55) * 2.2, 0, 1) * 0.6)
    dirt = fbm(rng, (S, S), (90, 12), (0.7, 0.3))
    col = col * (0.9 + 0.18 * dirt[..., None])
    # gaps between leaves: darker, the shadowed underlap
    gap = np.clip(1.0 - np.minimum(t, 1 - t) / 0.09, 0, 1)
    col = col * (1.0 - 0.38 * gap[..., None])
    col = lerp(col, lerp(col, cord_col, 0.55), cord)
    h = 0.55 * blade + midrib - 0.30 * pull + 0.06 * fib
    h = h * (1 - cord) + (0.85 + 0.1 * twist) * cord
    h = h - 0.35 * gap
    h = norm01(ndimage.gaussian_filter(h, 0.6, mode="wrap"))
    rough = np.clip(0.86 + 0.08 * (1 - fib) - 0.05 * cord + 0.04 * wx, 0, 1)
    return col, h, rough, 5.0


# ------------------------------------------------------------------ elm bark

def _worley(rng, S, n, sy):
    """Periodic anisotropic cellular noise: (F1, F2) to n points, cells stretched sy
    times taller than wide."""
    pts = rng.random((n, 2)) * S
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    f1 = np.full((S, S), 1e9, np.float32)
    f2 = np.full((S, S), 1e9, np.float32)
    for px, py in pts:
        dx = np.abs(xx - px); dx = np.minimum(dx, S - dx)
        dy = np.abs(yy - py); dy = np.minimum(dy, S - dy) / sy
        d = np.sqrt(dx * dx + dy * dy)
        f2 = np.where(d < f1, f1, np.minimum(f2, d))
        f1 = np.minimum(f1, d)
    return f1, f2


def elm_bark(seed):
    rng = np.random.default_rng(seed)
    S = SIZE
    yy, xx = np.mgrid[0:S, 0:S]
    warp = (noise(rng, (S, S), (40, 90)) - 0.5) * 30
    f1, f2 = _worley(rng, S, 420, 7.0)
    edge = (f2 - f1)
    edge = edge[yy, ((xx + warp).astype(int)) % S]
    furrow = np.clip(1.0 - edge / 7.0, 0, 1) ** 1.6         # 1 in the furrow
    g1, g2 = _worley(rng, S, 700, 0.35)
    small = np.clip(1.0 - (g2 - g1) / 3.0, 0, 1) ** 2        # cross-checks in the cork
    flake = fbm(rng, (S, S), (6, 2, 0.8), (0.5, 0.3, 0.2))
    fine = noise(rng, (S, S), (1.0, 0.5))
    ridge = 1.0 - furrow
    h = 0.80 * ridge - 0.18 * small * ridge + 0.12 * flake * ridge + 0.05 * fine
    top = np.array([0.56, 0.53, 0.47])       # weathered grey cork
    mid = np.array([0.43, 0.38, 0.32])
    deep = np.array([0.22, 0.16, 0.12])      # red-brown inner furrows
    # long fibrous ridges up the sheet: noise stretched along the grain
    fibre = fbm(rng, (S, S), ((40, 2.5), (14, 1.2), (5, 0.6)), (0.5, 0.3, 0.2))
    col = lerp(mid, top, np.clip(fibre * 1.3 - 0.15 - small * 0.3, 0, 1)[..., None])
    col = lerp(col, deep, (furrow * 0.65)[..., None])
    col = col * (0.88 + 0.2 * flake[..., None])
    h = h + 0.15 * fibre * ridge
    big = fbm(rng, (S, S), (160, 60), (0.6, 0.4))
    col = col * (0.86 + 0.24 * big[..., None])
    lich = noise(rng, (S, S), 3.0)
    lich_m = np.clip((lich - 0.78) * 8.0, 0, 1) * ridge * np.clip((big - 0.45) * 3, 0, 1)
    col = lerp(col, np.array([0.56, 0.58, 0.48]), lich_m * 0.8)
    h = norm01(ndimage.gaussian_filter(h, 0.7, mode="wrap"))
    rough = np.clip(0.90 + 0.06 * furrow - 0.04 * lich_m, 0, 1)
    return col, h, rough, 10.0


# ------------------------------------------------------------------ bough thatch

def _leaf_stamp(L, W, angle):
    """A pointed elliptical leaf as (alpha, shade, height) on its own small grid."""
    r = int(math.ceil(max(L, W) / 2 + 2))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1].astype(np.float32)
    c, s = math.cos(angle), math.sin(angle)
    u = (xx * c + yy * s) / (L / 2)
    v = (-xx * s + yy * c) / (W / 2)
    # pointed at both ends: the half-width narrows as |u| grows
    half = np.clip(1 - u * u, 0, 1) ** 0.75
    inside = (np.abs(u) <= 1) & (np.abs(v) <= half)
    alpha = inside.astype(np.float32)
    dome = np.clip(1 - (v / np.maximum(half, 1e-3)) ** 2, 0, 1) * np.clip(1 - u * u, 0, 1)
    vein = np.exp(-(v / 0.08) ** 2) * inside
    return alpha, dome, vein


def bough_thatch(seed):
    rng = np.random.default_rng(seed)
    S = SIZE
    px_m = S / 1.5
    col = np.zeros((S, S, 3), np.float32)
    h = np.zeros((S, S), np.float32)
    # the dark of the mass behind the outermost leaves
    under = fbm(rng, (S, S), (40, 10), (0.6, 0.4))
    col[:] = np.array([0.10, 0.10, 0.06]) * (0.7 + 0.6 * under[..., None])
    h[:] = 0.15 * under
    # twigs first, then leaves over them
    for _ in range(120):
        x0, y0 = rng.uniform(0, S, 2)
        ang = rng.uniform(0, 2 * np.pi)
        ln = rng.uniform(0.08, 0.35) * px_m
        for k in range(int(ln)):
            px = int(x0 + math.cos(ang) * k) % S
            py = int(y0 + math.sin(ang) * k) % S
            for dx in (-1, 0, 1):
                col[py, (px + dx) % S] = (0.26, 0.20, 0.14)
                h[py, (px + dx) % S] = 0.35
    greens = [np.array(c) for c in ((0.24, 0.30, 0.12), (0.30, 0.34, 0.14), (0.36, 0.33, 0.15),
                                    (0.42, 0.34, 0.16), (0.30, 0.26, 0.12), (0.20, 0.25, 0.11))]
    n_leaves = 2600
    for i in range(n_leaves):
        L = rng.uniform(0.05, 0.11) * px_m
        W = L * rng.uniform(0.38, 0.6)
        ang = rng.uniform(0, 2 * np.pi)
        alpha, dome, vein = _leaf_stamp(L, W, ang)
        r = alpha.shape[0] // 2
        cx, cy = rng.uniform(0, S, 2)
        layer = (i + 1) / n_leaves
        g = greens[rng.integers(len(greens))] * rng.uniform(0.75, 1.2)
        brown = rng.random() < 0.28
        if brown:
            g = np.array([0.40, 0.29, 0.15]) * rng.uniform(0.8, 1.15)
        shade = 0.70 + 0.45 * layer
        ys = (np.arange(-r, r + 1) + int(cy)) % S
        xs = (np.arange(-r, r + 1) + int(cx)) % S
        sub_h = h[np.ix_(ys, xs)]
        lh = 0.25 + 0.6 * layer + 0.12 * dome
        m = (alpha > 0) & (lh > sub_h)
        if not m.any():
            continue
        leaf_col = g[None, None, :] * shade * (0.85 + 0.25 * dome[..., None]) * (1 - 0.18 * vein[..., None])
        sub_c = col[np.ix_(ys, xs)]
        sub_c[m] = leaf_col[m]
        sub_h[m] = lh[m]
        col[np.ix_(ys, xs)] = sub_c
        h[np.ix_(ys, xs)] = sub_h
    h = norm01(ndimage.gaussian_filter(h, 0.8, mode="wrap"))
    rough = np.clip(0.80 + 0.15 * (1 - h), 0, 1)
    return col, h, rough, 7.0


# ------------------------------------------------------------------ hay (T-3401)

def _strands(rng, S, col, h, n, length_px, width_px, angle, palette, layer0, layer1,
             tone_field=None, curl=0.0, ang_field=None):
    """Paint `n` hay stems over (col, h), each a slightly bent round stem, wrapping.

    `angle` is (mean, spread) in radians from straight DOWN the image (stems combed down
    the stack); `palette` is a list of (rgb, weight); a stem lies on top of what is under
    it only where it stands higher (the bough sheet's rule), so later stems overlay."""
    cols = np.array([c for c, _ in palette], np.float32)
    w = np.array([wt for _, wt in palette], np.float64)
    w = w / w.sum()
    for i in range(n):
        L = rng.uniform(*length_px)
        W = rng.uniform(*width_px)
        x0, y0 = rng.uniform(0, S, 2)
        a = rng.normal(angle[0], angle[1])
        if ang_field is not None:
            a += (ang_field[int(y0) % S, int(x0) % S] - 0.5) * 1.6
        # direction: angle 0 points down the image (+row)
        dx, dy = math.sin(a), math.cos(a)
        bend = rng.normal(0.0, curl)
        r = int(L / 2 + W + 3)
        ys = (np.arange(-r, r + 1) + int(y0)) % S
        xs = (np.arange(-r, r + 1) + int(x0)) % S
        yy, xx = np.mgrid[-r:r + 1, -r:r + 1].astype(np.float32)
        # coordinates along (u) and across (v) the stem, with a gentle bow
        u = xx * dx + yy * dy
        v = -xx * dy + yy * dx
        un = u / (L / 2)
        v = v - bend * (L / 2) * (un * un - 1.0) * -1.0 * 0.15
        inside = (np.abs(un) <= 1.0)
        # stems taper to a point at the head and are cut square at the butt
        half = W * np.where(un > 0, np.clip(1.0 - un, 0.15, 1.0) ** 0.6, 1.0)
        d = np.abs(v) / np.maximum(half, 1e-3)
        m = inside & (d < 1.0)
        if not m.any():
            continue
        round_ = np.sqrt(np.clip(1.0 - d * d, 0, 1))
        c = cols[rng.choice(len(cols), p=w)] * rng.uniform(0.82, 1.15)
        if tone_field is not None:
            c = c * (0.80 + 0.40 * tone_field[int(y0) % S, int(x0) % S])
        layer = layer0 + (layer1 - layer0) * (i / max(n - 1, 1))
        lh = layer + 0.18 * round_
        sub_h = h[np.ix_(ys, xs)]
        m = m & (lh > sub_h)
        if not m.any():
            continue
        # a stem is lit along its crown and darker at its flanks; a node or two darkens it
        node = 1.0 - 0.25 * (np.abs(np.sin(un * rng.uniform(2.0, 5.0) + rng.uniform(0, 6))) < 0.06)
        shade = (0.62 + 0.45 * round_) * node
        sub_c = col[np.ix_(ys, xs)]
        sub_c[m] = (c[None, None, :] * shade[..., None])[m]
        sub_h[m] = lh[m]
        col[np.ix_(ys, xs)] = sub_c
        h[np.ix_(ys, xs)] = sub_h


STRAW = (0.66, 0.55, 0.32)
GOLD = (0.62, 0.48, 0.22)
TAN = (0.52, 0.42, 0.27)
SAGE = (0.46, 0.45, 0.28)     # grass cured green in the swath
OLIVE = (0.38, 0.37, 0.20)
RUSSET = (0.46, 0.32, 0.18)   # a sedge or a seed head among the grass
SILVER = (0.58, 0.56, 0.50)
GREYBROWN = (0.40, 0.36, 0.30)
DUN = (0.30, 0.26, 0.20)


def _hay(seed, palette, under, n_stems, angle_spread, clump_sigma, curl, mat=0.0):
    rng = np.random.default_rng(seed)
    S = SIZE
    px_m = S / 1.2
    col = np.zeros((S, S, 3), np.float32)
    h = np.zeros((S, S), np.float32)
    deep = fbm(rng, (S, S), (50, 12), (0.6, 0.4))
    col[:] = np.array(under, np.float32) * (0.6 + 0.8 * deep[..., None])
    h[:] = 0.10 * deep
    # forkfuls: patches of the stack lie their own way and wear their own tone
    ang = noise(rng, (S, S), clump_sigma)
    tone = fbm(rng, (S, S), (clump_sigma * 1.5, clump_sigma * 0.5), (0.6, 0.4))
    # the bulk, under: shorter, broken stems in every direction (the stack's body)
    _strands(rng, S, col, h, n_stems // 3, (0.04 * px_m, 0.12 * px_m), (0.9, 1.8), (0.0, 1.2),
             palette, 0.10, 0.45, tone, curl)
    # the combed outer layer: long stems lying down the slope
    _strands(rng, S, col, h, n_stems, (0.10 * px_m, 0.32 * px_m), (0.9, 2.2), (0.0, angle_spread),
             palette, 0.40, 0.95, tone, curl, ang)
    # a few broad blades among the stems
    _strands(rng, S, col, h, n_stems // 12, (0.08 * px_m, 0.20 * px_m), (2.0, 3.4),
             (0.0, angle_spread * 1.2), palette, 0.45, 0.98, tone, curl * 1.5, ang)
    if mat:
        # rain flattens the outside: the relief is lower and the gaps shallower
        h = h * (1.0 - 0.35 * mat) + 0.35 * mat * ndimage.gaussian_filter(h, 3.0, mode="wrap")
    big = fbm(rng, (S, S), (200, 80), (0.6, 0.4))
    col = col * (0.86 + 0.26 * big[..., None])
    h = norm01(ndimage.gaussian_filter(h, 0.5, mode="wrap"))
    return rng, col, h, big


def _cured(col, keep, lift):
    """Cured hay is a muted colour: the sheet's saturation drawn toward its own grey by
    (1 - keep), then lifted. Read against the owner's screenshot at sunset, where the first
    sheets went a rusty orange that hay never is."""
    grey = (0.30 * col[..., 0] + 0.55 * col[..., 1] + 0.15 * col[..., 2])[..., None]
    return (grey + (col - grey) * keep) * lift


def hay_stack(seed):
    pal = [(STRAW, 3.0), (GOLD, 3.0), (TAN, 2.0), (SAGE, 2.0), (OLIVE, 1.0), (RUSSET, 0.6),
           (GREYBROWN, 0.8)]
    rng, col, h, big = _hay(seed, pal, (0.16, 0.12, 0.06), 5200, 0.30, 26, 0.35)
    # the sun bleaches the very outside a little paler in places
    bleach = np.clip((big - 0.55) * 2.5, 0, 1) * h
    col = lerp(col, col * 0.85 + np.array([0.12, 0.11, 0.09]), bleach * 0.5)
    col = _cured(col, 0.62, 1.06)
    rough = np.clip(0.88 + 0.10 * (1 - h), 0, 1)
    return col, h, rough, 9.0


def hay_weathered(seed):
    pal = [(SILVER, 3.0), (GREYBROWN, 3.5), (DUN, 2.0), (TAN, 1.2), (OLIVE, 0.5)]
    rng, col, h, big = _hay(seed, pal, (0.10, 0.09, 0.07), 4600, 0.18, 34, 0.20, mat=1.0)
    S = SIZE
    # rain runs down the thatch: dark damp streaks, long and narrow, down the image
    streak = noise(rng, (S, S), (60, 2.5))
    col = col * (1.0 - 0.30 * np.clip((streak - 0.55) * 3.0, 0, 1)[..., None])
    # mould: small dark spots where the wet sat longest
    spot = noise(rng, (S, S), 2.5)
    mould = np.clip((spot - 0.80) * 9.0, 0, 1) * np.clip((big - 0.4) * 2, 0, 1)
    col = lerp(col, np.array([0.10, 0.10, 0.08]), mould * 0.7)
    col = _cured(col, 0.80, 1.04)
    rough = np.clip(0.92 + 0.07 * (1 - h), 0, 1)
    return col, h, rough, 7.0


def hay_cut(seed):
    pal = [(GOLD, 3.0), (STRAW, 2.0), (SAGE, 3.0), (OLIVE, 2.0), (TAN, 1.0), (RUSSET, 0.4)]
    rng = np.random.default_rng(seed)
    S = SIZE
    px_m = S / 0.9
    col = np.zeros((S, S, 3), np.float32)
    h = np.zeros((S, S), np.float32)
    deep = fbm(rng, (S, S), (40, 10), (0.6, 0.4))
    col[:] = np.array((0.20, 0.17, 0.08), np.float32) * (0.6 + 0.8 * deep[..., None])
    h[:] = 0.10 * deep
    tone = fbm(rng, (S, S), (30, 10), (0.6, 0.4))
    # the heart of a stack: packed layers, stems mostly across (the stack was laid in
    # rounds), cut or torn short where the hay was pulled
    _strands(rng, S, col, h, 6000, (0.03 * px_m, 0.14 * px_m), (0.9, 2.0), (math.pi / 2, 0.55),
             pal, 0.1, 0.95, tone, 0.4)
    # the layers of each day's pitching show as faint bands across the face
    yy = np.arange(S, dtype=np.float32)[:, None]
    band = 0.5 + 0.5 * np.sin(yy * 2 * np.pi * 5 / S + 3 * noise(rng, (1, S), (0, 80))[0][None, :])
    col = col * (0.88 + 0.16 * band[..., None])
    col = _cured(col, 0.70, 1.12)
    h = norm01(ndimage.gaussian_filter(h, 0.5, mode="wrap"))
    rough = np.clip(0.86 + 0.10 * (1 - h), 0, 1)
    return col, h, rough, 8.0


BUILDERS = {"cattail_mat": cattail_mat, "elm_bark": elm_bark, "bough_thatch": bough_thatch,
            "hay_stack": hay_stack, "hay_weathered": hay_weathered, "hay_cut": hay_cut}


def write(mat: dict) -> None:
    sid = mat["id"]
    out = LIB / sid
    out.mkdir(parents=True, exist_ok=True)
    col, h, rough, strength = BUILDERS[sid](mat["seed"])
    ao = ao_from_height(h)
    # bake a little of the occlusion into the colour, as a photograph would show it
    col = col * (0.75 + 0.25 * ao[..., None])
    base = to_u8(col)
    nrm = normal_from_height(h, strength)
    orm = np.stack([to_u8(ao), to_u8(rough), np.zeros_like(to_u8(ao))], -1)
    h16 = (h * 65535.0 + 0.5).astype(np.uint16)
    Image.fromarray(base, "RGB").save(out / f"{sid}_basecolor.png", optimize=True)
    Image.fromarray(nrm, "RGB").save(out / f"{sid}_normal_gl.png", optimize=True)
    Image.fromarray(orm, "RGB").save(out / f"{sid}_orm.png", optimize=True)
    Image.fromarray(h16).save(out / f"{sid}_height16.png")
    web = {}
    for k, arr in (("basecolor", base), ("normal_gl", nrm), ("orm", orm)):
        im = Image.fromarray(arr, "RGB").resize((WEB, WEB), Image.LANCZOS)
        name = f"{sid}_{k}_web.jpg"
        opts = dict(quality=90, subsampling=0 if k != "basecolor" else 2)
        try:
            im.save(out / name, optimize=True, **opts)
        except OSError:
            # some libjpeg builds refuse `optimize` on a 4:4:4 noisy sheet ("Suspension
            # not allowed here"); the plain Huffman tables are a few per cent larger
            im.save(out / name, **opts)
        web[k] = name
    sheet = {
        "id": sid,
        "group": mat.get("group", "camp_1812"),
        "span_m": mat["span_m"],
        "mean_roughness": mat["mean_roughness"],
        "resolution_px": SIZE,
        "web_resolution_px": WEB,
        "px_per_m": round(SIZE / mat["span_m"], 2),
        "orientation": "image x = round the covering (u, horizontal); image y = up it (v)",
        "note": mat["note"],
        "confidence": "reconstructed appearance; the covering's material is inferred from "
                      "the texts the record cites (%s)" % mat.get("liberty", "L-1812-potawatomi-camp-2515"),
        "color_space": {"basecolor": "sRGB", "normal_gl": "linear", "orm": "linear; R=AO G=Roughness B=Metallic",
                        "height16": "linear 16-bit"},
        "web": web,
        "seamless": True,
        "generator_seed": mat["seed"],
        "generation_method": "deterministic procedural synthesis (tools/generate_camp_1812_pbr.py); "
                             "no photograph sampled",
    }
    (out / "material.json").write_text(json.dumps(sheet, indent=2) + "\n")
    print(f"wrote {sid}")


def main(argv=None) -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma list of material ids (default: all)")
    only = set(filter(None, ap.parse_args(argv).only.split(",")))
    for m in MATERIALS:
        if not only or m["id"] in only:
            write(m)
    manifest = {"library": "camp_1812_pbr", "version": "1.1.0", "ticket": "T-3342, T-3401",
                "materials": [m["id"] for m in MATERIALS]}
    (LIB / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
