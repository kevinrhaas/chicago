#!/usr/bin/env python3
"""Build the Prairie Avenue 1904 stone library, package K02 (T-2288, piece 1 of T-1844).

    python3 generate_prairie_1904_stone.py              # rebuild the library in place
    python3 generate_prairie_1904_stone.py --check      # library and profiles agree, no writes

Six seamless stone fabrics for the 1904 programme's walls, trim and foundations: rock-faced
granite, warm brown sandstone, Lemont limestone, Bedford limestone, smooth dressed trim and
foundation rubble. Each writes an sRGB base colour, an OpenGL (+Y) normal, linear roughness,
16-bit height and a packed ORM (R = AO, G = roughness, B = metallic), plus web JPEGs of the
three maps a renderer binds and a material.json.

METRIC, AS K01 REQUIRES. Every tile is a square of `tile_m` metres, and every size below is
written in metres and converted once at the tile's own pixel density, so a 3 mm feldspar
crystal is 3 mm on every fabric. A component maps TEXCOORD_0 = surface metres / tile_m
(data/components/prairie_1904/k01_contract.json, `uv`), so the grain reads at scale beside
any other component on the same library. Height is in metres too: the normal is the true
slope of `relief_m` at that density, not a strength dialled until it looked right.

NO JOINT IS PAINTED, with one exception. Courses, joints, arrises, rock-face projection and
chips are GEOMETRY that a component builds from data/components/prairie_1904/
k02_stone_profiles.json; these maps carry only what lies inside one stone's face. The
exception is random rubble, which has no courses for geometry to follow: its stones and its
recessed mortar are in the map, and its profile says so (`pattern_in_map`).

WHAT THESE ARE EVIDENCE OF: NOTHING. Which building wears which stone is the structure
record's to say, at its own tier; the colour, grain and dressing of every map is ours
(docs/LIBERTIES.md L-k02-stone-library-2288). No photograph is sampled. Image x runs along
the stone's natural bed (the wall's horizontal for a walling stone); image y is up the wall.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFile, ImageFont
from scipy import ndimage
from scipy.spatial import cKDTree

SIZE = 1024
ImageFile.MAXBLOCK = 1 << 24          # an optimised 1024 px JPEG overflows the default block
HERE = Path(__file__).resolve().parent.parent
PROFILES = HERE.parents[2] / "data" / "components" / "prairie_1904" / "k02_stone_profiles.json"

# colours are sRGB (light, dark); relief_m is the in-map height range a face carries
# (everything bigger is geometry); mean_roughness is the face's, before its variation.
FABRICS = [
    dict(id="granite_rock_faced", tile_m=1.6, dressing="rock_faced", seed=19040801,
         colors=((150, 150, 146), (92, 92, 90)), relief_m=0.006, mean_roughness=0.80,
         note="A grey, medium-grained granite with dark mica flecks and a few warm feldspars, "
              "split into angular fracture planes 4-10 cm across. Grey, not Glessner's pinkish "
              "stone: the landmark keeps its own library (assets/textures/glessner-v4/), and no "
              "1904 register row names granite on any other house."),
    dict(id="sandstone_brown", tile_m=1.2, dressing="tooled", seed=19040802,
         colors=((156, 112, 90), (118, 80, 64)), relief_m=0.001, mean_roughness=0.84,
         note="A warm red-brown sandstone of the Lake Superior or Connecticut kind the register's "
              "brownstone fronts name: fine sand grain, horizontal bedding laminae, sparse darker "
              "iron mottles, and a fine drove-tooled face."),
    dict(id="limestone_lemont", tile_m=1.2, dressing="pitched", seed=19040803,
         colors=((184, 174, 148), (142, 132, 110)), relief_m=0.0025, mean_roughness=0.88,
         note="Lemont (Joliet) dolomitic limestone, the local building stone: buff-grey with "
              "yellow-ochre iron staining, small solution pits, the odd dark stylolite seam along "
              "the bed, and a hammer-dressed face."),
    dict(id="limestone_bedford", tile_m=1.2, dressing="crandalled", seed=19040804,
         colors=((208, 199, 176), (178, 168, 146)), relief_m=0.0004, mean_roughness=0.80,
         note="Bedford (Indiana oolitic) limestone: pale buff-grey, an even sugary grain with "
              "sparse shell fragments, and a crandalled face of fine pick marks."),
    dict(id="dressed_trim", tile_m=0.9, dressing="rubbed", seed=19040805,
         colors=((214, 206, 186), (190, 181, 160)), relief_m=0.00025, mean_roughness=0.66,
         note="Smooth dressed trim for sills, lintels, belts, copings, voussoirs and carving: a "
              "rubbed pale limestone face with a very fine grain and faint rubbing arcs. Carving "
              "is geometry; this is the skin it is cut in."),
    dict(id="foundation_rubble", tile_m=2.0, dressing="random_rubble", seed=19040806,
         colors=((158, 150, 134), (104, 98, 88)), relief_m=0.028, mean_roughness=0.90,
         note="Random rubble for foundations and rear basement walls: irregular limestone and "
              "fieldstone pieces 0.15-0.45 m across in a sandy lime mortar recessed about 15 mm. "
              "The one fabric whose joints are in the map (random rubble has no courses)."),
]

MORTAR = (172, 164, 148)       # the sandy lime of glessner-v4 mortar, read by eye, not sampled

WEB = ("basecolor", "normal_gl", "orm")


# ---------------------------------------------------------------------------- fields

def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def blur(a, sigma):
    return ndimage.gaussian_filter(a, sigma=sigma, mode="wrap")


def standard(a):
    """Centre on 0.5 with +-3 standard deviations spanning 0..1."""
    return clamp01(0.5 + (a - a.mean()) / (6.0 * max(float(a.std()), 1e-9)))


class Tile:
    """One square tile of `tile_m` metres: every size is asked for in metres."""

    def __init__(self, spec):
        self.m = spec["tile_m"]
        self.ppm = SIZE / self.m
        self.rng = np.random.default_rng(spec["seed"])
        self.yy, self.xx = np.indices((SIZE, SIZE)).astype(np.float32)

    def px(self, metres):
        if isinstance(metres, tuple):
            return tuple(max(m * self.ppm, 0.45) for m in metres)
        return max(metres * self.ppm, 0.45)

    def noise(self, sigma_m):
        """Seamless band-limited noise, ~0..1; sigma_m may be (along y, along x)."""
        return standard(blur(self.rng.random((SIZE, SIZE), dtype=np.float32), self.px(sigma_m)))

    def fbm(self, sigmas_m, weights):
        out = np.zeros((SIZE, SIZE), np.float32)
        for s, w in zip(sigmas_m, weights):
            out += (self.noise(s) - 0.5) * w
        return standard(out)

    def cells(self, mean_size_m, warp_m=0.0, weight=0.0):
        """Seamless (domain-warped) Voronoi cells about `mean_size_m` across: the cell id,
        F2 - F1 in metres (0 on a cell boundary) and the offset from the cell's seed.
        `weight` (0..1) additively weights the seeds, so cells vary in size and their
        boundaries curve, instead of the even polygons of a plain Voronoi."""
        n = max(4, int(round((self.m / mean_size_m) ** 2)))
        pts = self.rng.random((n, 2)) * SIZE
        tiles = [pts + np.array((dy * SIZE, dx * SIZE)) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
        tiled = np.concatenate(tiles)
        qy, qx = self.yy + 0.5, self.xx + 0.5
        if warp_m:
            amp = self.px(warp_m)
            qy = qy + (self.noise(warp_m * 2.5) - 0.5) * 2 * amp
            qx = qx + (self.noise(warp_m * 2.5) - 0.5) * 2 * amp
        q = np.stack((qy.ravel(), qx.ravel()), axis=1)
        k = 6 if weight else 2
        d, idx = cKDTree(tiled).query(q, k=k)
        if weight:
            w = self.rng.uniform(0, weight * self.px(mean_size_m) * 0.5, n)
            d = d - w[idx % n]
            order = np.argsort(d, axis=1)[:, :2]
            d = np.take_along_axis(d, order, 1)
            idx = np.take_along_axis(idx, order, 1)
        cell = (idx[:, 0] % n).reshape(SIZE, SIZE)
        gap = ((d[:, 1] - d[:, 0]) / self.ppm).reshape(SIZE, SIZE).astype(np.float32)
        centre = tiled[idx[:, 0]]
        off = ((q - centre) / self.ppm).reshape(SIZE, SIZE, 2).astype(np.float32)
        return cell, gap, off, n

    def flecks(self, sigma_m, fraction):
        """A sparse mask covering about `fraction` of the tile, soft-edged."""
        f = self.noise(sigma_m)
        cut = float(np.quantile(f, 1 - fraction))
        return clamp01((f - cut) / max(1e-6, 1 - cut) * 4)


def palette(t, light, dark):
    t = clamp01(t)[..., None]
    return np.array(dark, np.float32) * (1 - t) + np.array(light, np.float32) * t


def mix(base, colour, w):
    w = clamp01(w)[..., None]
    return base * (1 - w) + np.array(colour, np.float32) * w


# ---------------------------------------------------------------------------- fabrics
# each returns (height in metres, sRGB colour 0..255, roughness 0..1)

def granite(spec, t: Tile):
    # Split-face fracture: each facet is a shallow conchoidal dish that rises to the ridge it
    # shares with its neighbours. The height is a function of F2 - F1 (0 on every ridge), so
    # it is continuous across every facet edge: a ridge, never a cliff, which read as a crack.
    cell, gap, off, n = t.cells(0.065, warp_m=0.012)
    depth = t.rng.uniform(0.4, 1.0, n).astype(np.float32)[cell]
    tilt = t.rng.normal(0, 0.05, (n, 2)).astype(np.float32)
    dish = -depth * (1 - np.exp(-gap / 0.018))
    lean = (tilt[cell, 0] * off[..., 0] + tilt[cell, 1] * off[..., 1]) * np.clip(gap / 0.02, 0, 1)
    crystals = t.noise(0.0012)
    h = 0.004 * dish + lean + (t.fbm((0.12, 0.03), (0.6, 0.4)) - 0.5) * 0.004 + (crystals - 0.5) * 0.0002
    tone = t.rng.normal(0, 0.05, n).astype(np.float32)[cell]
    c = palette(0.55 + 0.35 * (crystals - 0.5) + tone + 0.15 * (t.noise(0.08) - 0.5), *spec["colors"])
    mica = t.flecks(0.0011, 0.07)
    feldspar = t.flecks(0.0016, 0.05)
    quartz = t.flecks(0.0014, 0.12)
    c = mix(c, (44, 42, 42), mica * 0.9)
    c = mix(c, (176, 156, 140), feldspar * 0.6)
    c = mix(c, (186, 186, 184), quartz * 0.35)
    rough = spec["mean_roughness"] + 0.05 * (t.noise(0.03) - 0.5) - 0.12 * quartz - 0.06 * mica
    return h, c, rough


def sandstone(spec, t: Tile):
    laminae = t.noise((0.0025, 0.35))
    bands = t.noise((0.03, 0.8))
    grain = t.noise(0.0004)
    mottle = blur(t.flecks(0.012, 0.03), t.px(0.01))
    drove = 0.5 + 0.5 * np.sin(t.xx / t.px(0.0032) * 2 * math.pi + 3 * t.noise((0.05, 0.002)))
    strokes = clamp01((t.noise((0.03, 0.02)) - 0.45) * 4)  # the drove in patches, not ruled lines
    h = ((grain - 0.5) * 0.0004 + (drove - 0.5) * 0.00012 * strokes
         + (t.fbm((0.04, 0.012), (0.6, 0.4)) - 0.5) * 0.0005)
    c = palette(0.5 + 0.14 * (laminae - 0.5) + 0.30 * (bands - 0.5) + 0.40 * (grain - 0.5), *spec["colors"])
    c = mix(c, (84, 50, 38), mottle * 0.30)
    rough = spec["mean_roughness"] + 0.04 * (grain - 0.5) + 0.03 * (laminae - 0.5)
    return h, c, rough


def lemont(spec, t: Tile):
    grain = t.noise(0.0007)
    body = t.fbm((0.15, 0.05, 0.015), (0.5, 0.3, 0.2))
    stain = t.flecks(0.06, 0.18) * t.noise(0.012)
    pits = t.flecks(0.0012, 0.03) * clamp01((t.noise(0.04) - 0.55) * 5)
    wave = (t.noise((0.4, 0.05)) - 0.5) * t.px(0.02)
    seam_line = np.abs(((t.yy + wave) % SIZE) - SIZE * 0.62) < 0.8
    seam = blur(seam_line.astype(np.float32), 0.7) * t.flecks((0.03, 0.3), 0.35)
    dressing = t.fbm((0.03, 0.008), (0.65, 0.35))
    h = (dressing - 0.5) * 0.0018 + (grain - 0.5) * 0.0003 - pits * 0.0012
    c = palette(0.5 + 0.40 * (body - 0.5) + 0.20 * (grain - 0.5), *spec["colors"])
    c = mix(c, (172, 142, 92), blur(stain, t.px(0.006)) * 0.40)
    c = mix(c, (120, 112, 96), pits * 0.5)
    c = mix(c, (110, 104, 92), seam * 0.45)
    rough = spec["mean_roughness"] + 0.04 * (grain - 0.5) + 0.05 * pits
    return h, c, rough


def bedford(spec, t: Tile):
    ooids = t.noise(0.0004)
    body = t.fbm((0.2, 0.05), (0.6, 0.4))
    shells = t.flecks((0.0006, 0.002), 0.025)
    picks = t.flecks(0.0009, 0.08)
    h = (ooids - 0.5) * 0.00015 - picks * 0.00008 + (t.noise(0.02) - 0.5) * 0.0001
    c = palette(0.5 + 0.40 * (body - 0.5) + 0.25 * (ooids - 0.5), *spec["colors"])
    c = mix(c, (226, 220, 204), shells * 0.6)
    rough = spec["mean_roughness"] + 0.03 * (ooids - 0.5) + 0.04 * picks
    return h, c, rough


def dressed(spec, t: Tile):
    grain = t.noise(0.0003)
    body = t.fbm((0.25, 0.06), (0.6, 0.4))
    arcs = t.noise((0.0015, 0.03))                      # the rubbing stone's long strokes
    h = (grain - 0.5) * 0.00008 + (arcs - 0.5) * 0.00003 + (t.noise(0.03) - 0.5) * 0.00008
    c = palette(0.5 + 0.22 * (body - 0.5) + 0.18 * (grain - 0.5), *spec["colors"])
    rough = spec["mean_roughness"] + 0.03 * (grain - 0.5) + 0.02 * (arcs - 0.5)
    return h, c, rough


def rubble(spec, t: Tile):
    cell, gap, off, n = t.cells(0.24, warp_m=0.03, weight=0.9)
    joint_m = 0.018 + 0.012 * t.noise(0.08)                  # mortar 18-30 mm wide
    soft = clamp01((gap - joint_m) / 0.003)                  # the stone's edge, antialiased
    rise = clamp01((gap - joint_m) / 0.12)
    dome = 1 - (1 - rise) ** 2                               # a pillowed face, rising from its bed
    lift = t.rng.normal(0, 0.003, n).astype(np.float32)[cell]
    face = (t.fbm((0.05, 0.015, 0.004), (0.5, 0.3, 0.2)) - 0.5) * 0.006
    bed = -0.015 + (t.noise(0.002) - 0.5) * 0.001
    h = bed + (0.022 * dome + lift * dome + face * dome) * soft   # meets the mortar, no cliff
    kinds = np.array([(170, 162, 144), (142, 136, 124), (150, 132, 108), (118, 112, 104),
                      (186, 178, 156)], np.float32)
    pick = t.rng.integers(0, len(kinds), n)
    shade = t.rng.normal(1.0, 0.07, n).astype(np.float32)
    grain = t.noise(0.0008)
    within = t.fbm((0.06, 0.015), (0.6, 0.4))
    sc = kinds[pick][cell] * shade[cell][..., None] * (0.82 + 0.16 * grain + 0.2 * within)[..., None]
    mortar = np.array(MORTAR, np.float32) * (0.88 + 0.2 * t.noise(0.003))[..., None]
    c = mortar * (1 - soft[..., None]) + sc * soft[..., None]
    rough = 0.96 * (1 - soft) + (spec["mean_roughness"] - 0.04 + 0.05 * (grain - 0.5)) * soft
    return h, c, rough


DRESSINGS = {"rock_faced": granite, "tooled": sandstone, "pitched": lemont,
             "crandalled": bedford, "rubbed": dressed, "random_rubble": rubble}


# ---------------------------------------------------------------------------- maps

def normal_gl(h_m, ppm):
    """True slope of a height field in metres, OpenGL convention (+Y = image up)."""
    d = 1.0 / ppm
    gx = (np.roll(h_m, -1, 1) - np.roll(h_m, 1, 1)) / (2 * d)
    gy_down = (np.roll(h_m, -1, 0) - np.roll(h_m, 1, 0)) / (2 * d)
    n = np.stack((-gx, gy_down, np.ones_like(h_m)), axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def cavity_ao(h_m, ppm, relief):
    local = blur(h_m, 0.01 * ppm) - h_m
    return clamp01(1 - np.maximum(local, 0) / max(relief, 1e-9) * 1.6)


def half(a):
    return a.reshape(SIZE // 2, 2, SIZE // 2, 2, *a.shape[2:]).mean(axis=(1, 3))


def u8(a):
    return np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)


def encode(image: Image.Image, fmt: str, **kw) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format=fmt, **kw)
    return buf.getvalue()


def render(spec):
    t = Tile(spec)
    h, c, rough = DRESSINGS[spec["dressing"]](spec, t)
    # the dressing shapes the face; its declared relief sizes it, so a face is never
    # deeper than the fabric says (the 0.5-99.5 % span, so one stray pixel cannot set it)
    lo, hi = np.quantile(h, (0.005, 0.995))
    h = (h - np.median(h)) * (spec["relief_m"] / max(float(hi - lo), 1e-12))
    relief = float(h.max() - h.min())
    ngl = normal_gl(h, t.ppm)
    ao = cavity_ao(h, t.ppm, relief)
    rough = clamp01(rough)
    orm = np.stack((ao, rough, np.zeros_like(rough)), axis=-1)
    lo = float(h.min())  # height16's zero
    h01 = (h - lo) / max(relief, 1e-12)
    # albedo and normal at full size; the slow-varying detail maps (ORM, height) at half,
    # by a 2x2 box mean, which keeps the tile seamless and the library a third lighter
    orm_d, h_d = half(orm), half(h01)
    files = {
        "basecolor.png": encode(Image.fromarray(u8(clamp01(c / 255.0))), "PNG", compress_level=9),
        "normal_gl.png": encode(Image.fromarray(u8(ngl)), "PNG", compress_level=9),
        "orm.png": encode(Image.fromarray(u8(orm_d)), "PNG", compress_level=9),
        "height16.png": encode(Image.fromarray(np.clip(h_d * 65535 + 0.5, 0, 65535).astype(np.uint16)),
                               "PNG", compress_level=9),
        "basecolor_web.jpg": encode(Image.fromarray(u8(clamp01(c / 255.0))), "JPEG", quality=86,
                                    optimize=True, subsampling=0),
        "normal_gl_web.jpg": encode(Image.fromarray(u8(ngl)), "JPEG", quality=90, optimize=True, subsampling=0),
        "orm_web.jpg": encode(Image.fromarray(u8(orm_d)), "JPEG", quality=88, optimize=True, subsampling=0),
    }
    seam = float(np.abs(h01[:, 0] - h01[:, -1]).mean() + np.abs(h01[0, :] - h01[-1, :]).mean()) / 2
    inner = float(np.abs(h01[:, 1] - h01[:, 0]).mean() + np.abs(h01[1, :] - h01[0, :]).mean()) / 2
    stats = {
        "relief_m": round(relief, 5),
        "mean_roughness_measured": round(float(rough.mean()), 3),
        "mean_basecolor_srgb": [int(round(v)) for v in c.reshape(-1, 3).mean(0)],
        "seam_to_interior_step": round(seam / max(inner, 1e-9), 3),
    }
    return files, stats


def material_json(spec, files, stats):
    stem = spec["id"]
    return {
        "id": stem,
        "package": "K02",
        "dressing": spec["dressing"],
        "tile_m": [spec["tile_m"], spec["tile_m"]],
        "resolution_px": {"basecolor": SIZE, "normal_gl": SIZE, "orm": SIZE // 2, "height16": SIZE // 2},
        "px_per_m": round(SIZE / spec["tile_m"], 2),
        "height16_range_m": stats["relief_m"],
        "mean_roughness": spec["mean_roughness"],
        "measured": stats,
        "colors_srgb": [list(spec["colors"][0]), list(spec["colors"][1])],
        "note": spec["note"],
        "confidence": "reconstructed appearance; which building wears this stone is its structure record's to say, at its own tier",
        "orientation": "image x = along the stone's natural bed (the wall's horizontal for walling); image y = up the wall. "
                       "TEXCOORD_0 = surface metres / tile_m (K01 uv rule)",
        "joints": "geometry, from data/components/prairie_1904/k02_stone_profiles.json"
                  + ("; EXCEPT this fabric, whose random-rubble joints are in the map" if spec["dressing"] == "random_rubble" else ""),
        "color_space": {"basecolor": "sRGB", "normal_gl": "linear, OpenGL +Y",
                        "height16": "linear 16-bit, 0 = lowest point of height16_range_m",
                        "orm": "linear; R=AO G=Roughness B=Metallic"},
        "files": {name: f"{stem}_{name}" for name in files},
        "web": {s: f"{stem}_{s}_web.jpg" for s in WEB},
        "bytes": {name: len(b) for name, b in files.items()},
        "sha256": {name: hashlib.sha256(b).hexdigest() for name, b in files.items()},
        "seamless": True,
        "generator_seed": spec["seed"],
        "generation_method": "deterministic procedural synthesis (tools/generate_prairie_1904_stone.py); no photograph sampled",
    }


def contact_sheet(out: Path, built):
    thumb, label, cols = 256, 48, 3
    rows = math.ceil(len(built) / cols)
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + label)), (26, 27, 25))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, (spec, files) in enumerate(built):
        im = Image.open(io.BytesIO(files["basecolor.png"])).convert("RGB")
        # a 0.5 m window at every fabric's own scale, so the grains compare metre for metre
        crop = int(round(SIZE * 0.5 / spec["tile_m"]))
        im = im.crop((0, 0, crop, crop)).resize((thumb, thumb), Image.Resampling.LANCZOS)
        x, y = (i % cols) * thumb, (i // cols) * (thumb + label)
        sheet.paste(im, (x, y))
        draw.text((x + 6, y + thumb + 6), spec["id"].replace("_", " "), font=font, fill=(235, 232, 220))
        draw.text((x + 6, y + thumb + 24), f'0.50 m window · tile {spec["tile_m"]:.2f} m · {spec["dressing"]}',
                  font=font, fill=(166, 169, 157))
    (out / "contact_sheet.jpg").write_bytes(encode(sheet, "JPEG", quality=88, optimize=True))


def check_profiles(manifest) -> list[str]:
    problems = []
    prof = json.loads(PROFILES.read_text())
    ids = {m["id"]: m for m in manifest}
    for fid, p in prof["fabrics"].items():
        if fid not in ids:
            problems.append(f"profiles name {fid}, which the library does not build")
            continue
        if p.get("pattern_in_map", False) != (ids[fid]["dressing"] == "random_rubble"):
            problems.append(f"{fid}: pattern_in_map disagrees with its dressing ({ids[fid]['dressing']})")
    for fid in ids:
        if fid not in prof["fabrics"]:
            problems.append(f"{fid} is built but has no profile: a component could not lay it")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=HERE)
    ap.add_argument("--check", action="store_true",
                    help="read the committed manifest and profiles and report disagreements; write nothing")
    a = ap.parse_args()
    if a.check:
        manifest = json.loads((a.out / "manifest.json").read_text())["materials"]
        problems = check_profiles(manifest)
        for m in manifest:
            for name, digest in m["sha256"].items():
                p = a.out / m["id"] / m["files"][name]
                if not p.exists():
                    problems.append(f"{p.relative_to(a.out)} is missing")
        for p in problems:
            print("FAIL", p)
        print(f"{len(manifest)} fabrics, {len(problems)} problem(s)")
        sys.exit(1 if problems else 0)
    manifest, built = [], []
    for spec in FABRICS:
        files, stats = render(spec)
        if stats["seam_to_interior_step"] > 2.0:
            sys.exit(f"{spec['id']}: the tile's wrap edge steps {stats['seam_to_interior_step']}x an interior pixel")
        d = a.out / spec["id"]
        d.mkdir(parents=True, exist_ok=True)
        for name, b in files.items():
            (d / f'{spec["id"]}_{name}').write_bytes(b)
        mj = material_json(spec, files, stats)
        (d / "material.json").write_text(json.dumps(mj, indent=2) + "\n")
        manifest.append(mj)
        built.append((spec, files))
        print(f'{spec["id"]}: {spec["tile_m"]:.2f} m tile, {mj["px_per_m"]} px/m, relief {stats["relief_m"] * 1000:.2f} mm, '
              f'roughness {stats["mean_roughness_measured"]}, seam {stats["seam_to_interior_step"]}, '
              f'web {sum(mj["bytes"][f"{s}_web.jpg"] for s in WEB) // 1024} KiB')
    (a.out / "manifest.json").write_text(json.dumps(
        {"library": "Prairie Avenue 1904 stone library (K02)", "version": "1.0.0", "ticket": "T-2288",
         "parent": "T-1844", "contract": "data/components/prairie_1904/k01_contract.json",
         "profiles": "data/components/prairie_1904/k02_stone_profiles.json",
         "materials": manifest}, indent=2) + "\n")
    contact_sheet(a.out, built)
    if PROFILES.exists():
        problems = check_profiles(manifest)
        for p in problems:
            print("FAIL", p)
        if problems:
            sys.exit(1)


if __name__ == "__main__":
    main()
