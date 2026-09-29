#!/usr/bin/env python3
"""Deterministic original PBR studies for Glessner v4; no photographic pixels.

python assets/textures/glessner-v4/generate.py
Requires numpy, Pillow and scipy. The house's stone courses and moulded details
are geometry; these maps provide grain, mortar, clay laminations and metal aging.
The maps are reconstructed, bounded by the material descriptions and the visual
scale of existing HABS evidence, never measured samples of the historic surfaces.
"""
from __future__ import annotations
import hashlib
import json
import argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
from scipy.interpolate import LinearNDInterpolator

OUT = Path(__file__).resolve().parent
SIZE = 2048
DETAIL_SIZE = 1024
TILE_M = {"granite": (1.6, 1.6), "brick": (1.7272, 2.1336),
          "limestone": (1.2, 1.2), "terracotta": (2.4384, 1.95072),
          "copper": (2.4, 2.4), "oak": (0.8, 2.4), "painted_wood": (0.8, 2.4),
          "turf": (2.4, 2.4), "gravel": (2.0, 2.0)}


def field(rng, scale, size=SIZE):
    """Periodic scalar field, one source of deterministic multiscale detail."""
    a = rng.standard_normal((size, size)).astype(np.float32)
    a = gaussian_filter(a, scale, mode="wrap")
    return a / max(float(a.std()), 1e-7)


def smoothstep(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def fracture_field(rng, cells):
    """Seamless piecewise planar fracture, not smoothly rounded noise.

    Nine translated copies of an irregular triangular field make the tile's
    boundaries continuous. A periodic, low-amplitude domain warp breaks the
    obvious triangular facets into chipped irregular fracture planes instead of
    leaving a recognisable triangulation pattern on every rock-faced block.
    """
    y, x = np.indices((cells, cells), dtype=np.float32)
    p = np.stack(((x.ravel() + .5) / cells, (y.ravel() + .5) / cells), -1)
    p += rng.uniform(-.38 / cells, .38 / cells, p.shape)
    heights = rng.standard_normal(cells * cells).astype(np.float32)
    points = np.concatenate([p + (dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
    values = np.tile(heights, 9)
    interp = LinearNDInterpolator(points, values)
    q = (np.arange(SIZE, dtype=np.float32) + .5) / SIZE
    warp_x = field(rng, 28) * .015
    warp_y = field(rng, 28) * .015
    out = np.empty((SIZE, SIZE), dtype=np.float32)
    for start in range(0, SIZE, 128):
        xx, yy = np.meshgrid(q, q[start:start + 128])
        out[start:start + 128] = interp(xx + warp_x[start:start + 128],
                                       yy + warp_y[start:start + 128])
    return out / max(float(out.std()), 1e-7)


def normals(height, tile_m):
    # PNG scanlines run downward while UV v grows upward. The green derivative
    # is reversed here so glTF's tangent-space normal is OpenGL/Y+.
    size = height.shape[0]
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) / (2 * tile_m[0] / size)
    dy = (np.roll(height, 1, 0) - np.roll(height, -1, 0)) / (2 * tile_m[1] / size)
    n = np.stack((-dx, -dy, np.ones_like(height)), -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return np.clip((n * .5 + .5) * 255 + .5, 0, 255).astype(np.uint8)


def save(name, rgb, height, rough, description, seed):
    rgb = np.clip(rgb, 0.02, .94)
    # The stronger granite mineral contrast compresses less readily. Q89 keeps
    # its original 2K detail within the same shipped texture payload budget.
    quality = 89 if name == "granite" else 92
    Image.fromarray(np.uint8(rgb * 255 + .5)).save(OUT / f"{name}_basecolor.jpg", quality=quality,
                                               subsampling=0, optimize=True)
    # Low-pass before reducing resolution: high-frequency micro-normals shimmer
    # rather than looking like stone. Albedo keeps the 2K mineral detail.
    detail = gaussian_filter(height, 1.25, mode="wrap")[::2, ::2]
    Image.fromarray(normals(detail, TILE_M[name])).save(OUT / f"{name}_normal.png", optimize=True)
    rough = gaussian_filter(rough, 1.25, mode="wrap")[::2, ::2]
    quantised = np.clip(np.round(np.clip(rough, .05, 1) * 127) * 2, 0, 255)
    Image.fromarray(np.uint8(quantised)).save(
        OUT / f"{name}_roughness.png", optimize=True)
    return {"name": name, "albedo_size_px": int(rgb.shape[0]), "detail_size_px": int(detail.shape[0]),
            "tile_m": TILE_M[name], "seed": seed,
            "confidence": "reconstructed", "description": description,
            "albedo_colour_space": "sRGB", "normal_convention": "OpenGL +Y",
            "roughness_colour_space": "non-colour", "source_pixels": "none"}


def stone(name, seed, smooth=False):
    rng = np.random.default_rng(seed)
    fine = field(rng, .55)
    grain = field(rng, 1.9)
    medium = field(rng, 9)
    coarse = field(rng, 52)
    mineral = smoothstep(.7, 1.9, grain)
    pale = smoothstep(.55, 2.0, field(rng, 2.8))
    if smooth:
        base = np.array([.695, .675, .610], np.float32)
        tone = .012 * fine + .017 * medium + .015 * coarse
        h = .00010 * fine + .00035 * medium + .00065 * coarse
        rough = .79 + .045 * grain + .035 * coarse
    else:
        base = np.array([.655, .635, .596], np.float32)
        tone = .018 * fine + .021 * grain + .018 * medium + .014 * coarse
        fracture = fracture_field(rng, 13)
        splinter = fracture_field(rng, 34)
        h = (.000045 * fine + .00012 * grain + .0004 * medium + .0012 * coarse
             + .0055 * fracture + .0015 * splinter)
        rough = .83 + .028 * grain + .035 * medium
        tone += .006 * fracture
    rgb = base + tone[..., None]
    # Distinct dark mica and pale quartz/feldspar grains matter in close views;
    # the previous low-contrast speckle read as uniformly coloured stucco.
    dark_mineral = [.060, .059, .052] if smooth else [.155, .151, .141]
    pale_mineral = [.035, .037, .039] if smooth else [.060, .064, .068]
    rgb -= mineral[..., None] * np.array(dark_mineral)
    rgb += pale[..., None] * np.array(pale_mineral)
    note = ("Original fine limestone grain; dressing and block shapes are geometry." if smooth else
            "Original mineral grain over domain-warped angular split-face fracture planes at about "
            "4-14 cm scale, 5.5 mm large-plane variation and 1.5 mm smaller splinters. Physical courses, "
            "block silhouettes, bevels and chipped edges are geometry.")
    return save(name, rgb, h, rough, note + " No mortar lines are baked into the stone.", seed)


def brick():
    seed = 190402
    rng = np.random.default_rng(seed)
    # Brick beds and joints are actual geometry. Avoid a second conflicting bond.
    grit = field(rng, .8)
    soft = field(rng, 7)
    roughclay = field(rng, 2.1)
    shifts = .018 * field(rng, 35)
    bodycolour = np.array([.475, .287, .208]) + shifts[..., None]
    bodycolour += (.012 * grit + .021 * soft + .012 * roughclay)[..., None]
    fired = smoothstep(.8, 2.0, field(rng, 20))
    bodycolour -= fired[..., None] * np.array([.033, .022, .014])
    height = .00012 * grit + .00030 * roughclay + .0005 * soft
    rough = .815 + .025 * roughclay
    return save("brick", bodycolour, height, rough, "Reconstructed fired red-brown clay grain. "
                "Courses, bevelled arrises and mortar joints are geometry, not repeated in this map.", seed)


def terracotta():
    seed = 190403
    rng = np.random.default_rng(seed)
    grit, clay = field(rng, .6), field(rng, 7)
    shifts = .016 * field(rng, 44)
    rgb = np.array([.493, .240, .166]) + shifts[..., None]
    rgb += (.009 * grit + .012 * clay)[..., None]
    h = .00004 * grit + .00015 * clay
    rough = .71 + .035 * clay + .025 * grit
    return save("terracotta", rgb, h, rough, "Fine fired clay grain. Individual flat overlapping "
                "tiles, lapped noses and ridge caps are geometry; reconstructed exposure is "
                "0.12192 m (4.8 in), not Spanish barrel tile.", seed)


def copper():
    seed = 190404
    rng = np.random.default_rng(seed)
    fine, patches, large = field(rng, .65), field(rng, 24), field(rng, 104)
    patina = np.clip(.50 + .05 * patches + .04 * large, .25, .75)
    aged = np.array([.264, .283, .232])
    green = np.array([.299, .369, .301])
    rgb = aged + patina[..., None] * (green - aged)
    rgb += (.002 * fine + .002 * patches)[..., None]
    h = .00001 * fine + .00002 * patches
    rough = .56 + .12 * patina + .008 * patches
    return save("copper", rgb, h, rough, "Reconstructed 17-year copper weathering: brown metal with "
                "uneven muted green oxidation; standing seams belong to geometry. Modern bright "
                "turquoise oxidation is not asserted as the 1904 colour.", seed)


def oak(painted=False):
    seed = 190406 if painted else 190405
    rng = np.random.default_rng(seed)
    a = rng.standard_normal((SIZE, SIZE)).astype(np.float32)
    grain = gaussian_filter(a, (70, 1.0), mode="wrap")
    grain /= max(float(grain.std()), 1e-6)
    broad = gaussian_filter(a, (150, 12), mode="wrap")
    broad /= max(float(broad.std()), 1e-6)
    if painted:
        rgb = np.array([.160, .230, .195]) + (.0045 * grain + .004 * broad)[..., None]
        h = .000025 * grain
        rough = .46 + .025 * grain
        note = "Reconstructed muted dark green painted sash and carriage joinery; a thin "
        note += "smooth coating with restrained grain telegraphing, not a sampled modern finish."
    else:
        rgb = np.array([.213, .175, .120]) + (.011 * grain + .007 * broad)[..., None]
        h = .00006 * grain
        rough = .53 + .045 * grain
        note = "Subtle, vertically grained dark exterior oak. Reconstructed finish, not a sampled timber."
    return save("painted_wood" if painted else "oak", rgb, h, rough, note, seed)


def turf():
    """A short, irregularly clipped lawn, including blades and sparse dry thatch."""
    seed = 190407
    rng = np.random.default_rng(seed)
    n = 1024
    broad = field(rng, 35, n)
    fine = field(rng, .7, n)
    rgb = np.array([.233, .310, .131]) + (.017 * broad + .006 * fine)[..., None]
    canvas = Image.fromarray(np.uint8(np.clip(rgb, 0, 1) * 255))
    draw = ImageDraw.Draw(canvas)
    relief = Image.new("F", (n, n))
    hd = ImageDraw.Draw(relief)
    for _ in range(45000):
        x, y = rng.uniform(0, n, 2)
        angle = rng.uniform(0, 2 * np.pi)
        length = rng.uniform(3, 14)
        dx, dy = np.cos(angle) * length, np.sin(angle) * length
        brightness = rng.uniform(-.036, .047)
        colour = np.array([.251, .345, .143]) + brightness
        if rng.random() < .075:
            colour = np.array([.326, .329, .190]) + brightness
        colour = tuple(int(v * 255) for v in np.clip(colour, 0, 1))
        width = 1 if rng.random() < .68 else 2
        height = float(rng.uniform(.0005, .0034))
        shifts_x = [0] + ([n] if x + dx < 0 else []) + ([-n] if x + dx >= n else [])
        shifts_y = [0] + ([n] if y + dy < 0 else []) + ([-n] if y + dy >= n else [])
        for sx in shifts_x:
            for sy in shifts_y:
                line = (x + sx, y + sy, x + dx + sx, y + dy + sy)
                draw.line(line, fill=colour, width=width)
                hd.line(line, fill=height, width=width)
    rgb = np.asarray(canvas, dtype=np.float32) / 255
    rgb += (.008 * broad)[..., None]
    height = np.asarray(relief, dtype=np.float32) + .0004 * broad
    rough = .94 + .020 * field(rng, 3, n)
    return save("turf", rgb, height, rough, "Original short clipped grass with varied blade "
                "directions, restrained brown thatch and subtle patchiness. Reconstructed July "
                "1904 courtyard lawn, not a copied photograph or a claim about turf species.", seed)


def gravel():
    seed = 190408
    rng = np.random.default_rng(seed)
    n = 1024
    fine, aggregate = field(rng, .6, n), field(rng, 2.0, n)
    worn, broad = field(rng, 8, n), field(rng, 50, n)
    rgb = np.array([.493, .477, .433]) + (.016 * fine + .036 * aggregate
                                         + .014 * worn + .013 * broad)[..., None]
    pale = smoothstep(.9, 1.7, aggregate)
    rgb += pale[..., None] * .038
    height = .00010 * fine + .00075 * aggregate + .00025 * worn
    rough = .88 + .030 * aggregate + .020 * worn
    return save("gravel", rgb, height, rough, "Original compacted pale gravel and fine mineral "
                "aggregate, preserving the structure record's reconstructed 1904 carriage-drive "
                "reading. No modern concrete joints or slab dimensions are asserted.", seed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=list(TILE_M), help="regenerate one fabric and its hash record")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    recipes = {"granite": lambda: stone("granite", 190400),
               "limestone": lambda: stone("limestone", 190401, True),
               "brick": brick, "terracotta": terracotta, "copper": copper,
               "oak": oak, "painted_wood": lambda: oak(True), "turf": turf, "gravel": gravel}
    existing = OUT / "material-library.json"
    old = {m["name"]: m for m in json.loads(existing.read_text())["materials"]} if existing.exists() else {}
    if args.only:
        old[args.only] = recipes[args.only]()
        mats = [old[name] for name in recipes if name in old]
    else:
        mats = [fn() for fn in recipes.values()]
    assets = {}
    for p in sorted(OUT.iterdir()):
        if p.suffix in (".png", ".jpg"):
            assets[p.name] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
    doc = {"title": "Glessner v4 original material studies", "version": 1,
           "generated_by": "generate.py", "confidence": "reconstructed", "materials": mats,
           "rights": "Original procedural pixels; project-permissive terms in LICENSE.txt", "files": assets}
    (OUT / "material-library.json").write_text(json.dumps(doc, indent=2) + "\n")
    print(f"Generated {len(mats)} original PBR materials ({sum(v['bytes'] for v in assets.values()):,} bytes)")


if __name__ == "__main__":
    main()
