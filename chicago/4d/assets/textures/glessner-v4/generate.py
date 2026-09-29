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
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, zoom

OUT = Path(__file__).resolve().parent
SIZE = 2048
DETAIL_SIZE = 1024
TILE_M = {"granite": (1.6, 1.6), "brick": (1.7272, 2.1336),
          "limestone": (1.2, 1.2), "terracotta": (2.4384, 1.95072),
          "copper": (2.4, 2.4), "oak": (0.8, 2.4), "painted_wood": (0.8, 2.4)}


def field(rng, scale, size=SIZE):
    """Periodic scalar field, one source of deterministic multiscale detail."""
    a = rng.standard_normal((size, size)).astype(np.float32)
    a = gaussian_filter(a, scale, mode="wrap")
    return a / max(float(a.std()), 1e-7)


def smoothstep(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


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
    Image.fromarray(np.uint8(rgb * 255 + .5)).save(OUT / f"{name}_basecolor.jpg", quality=92,
                                               subsampling=0, optimize=True)
    # Low-pass before reducing resolution: high-frequency micro-normals shimmer
    # rather than looking like stone. Albedo keeps the 2K mineral detail.
    detail = gaussian_filter(height, 1.25, mode="wrap")[::2, ::2]
    Image.fromarray(normals(detail, TILE_M[name])).save(OUT / f"{name}_normal.png", optimize=True)
    rough = gaussian_filter(rough, 1.25, mode="wrap")[::2, ::2]
    quantised = np.clip(np.round(np.clip(rough, .05, 1) * 127) * 2, 0, 255)
    Image.fromarray(np.uint8(quantised)).save(
        OUT / f"{name}_roughness.png", optimize=True)
    return {"name": name, "albedo_size_px": SIZE, "detail_size_px": DETAIL_SIZE,
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
        h = .00010 * fine + .00030 * grain + .0012 * medium + .0022 * coarse
        rough = .83 + .05 * grain + .025 * medium
    rgb = base + tone[..., None]
    rgb -= mineral[..., None] * np.array([.060, .059, .052])
    rgb += pale[..., None] * np.array([.035, .037, .039])
    return save(name, rgb, h, rough, "Original fine mineral grain; physical courses, bevels and "
                "rock-faced relief are generated geometry. No mortar lines baked into the stone.", seed)


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
    patina = np.clip(.50 + .15 * patches + .12 * large, .05, .95)
    aged = np.array([.264, .283, .232])
    green = np.array([.299, .369, .301])
    rgb = aged + patina[..., None] * (green - aged)
    rgb += (.008 * fine + .009 * patches)[..., None]
    h = .00004 * fine + .00009 * patches
    rough = .45 + .30 * patina + .025 * patches
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
        rgb = np.array([.182, .194, .142]) + (.0045 * grain + .004 * broad)[..., None]
        h = .000025 * grain
        rough = .46 + .025 * grain
        note = "Reconstructed dark olive painted sash and carriage joinery; a thin "
        note += "smooth coating with restrained grain telegraphing, not a sampled modern finish."
    else:
        rgb = np.array([.213, .175, .120]) + (.011 * grain + .007 * broad)[..., None]
        h = .00006 * grain
        rough = .53 + .045 * grain
        note = "Subtle, vertically grained dark exterior oak. Reconstructed finish, not a sampled timber."
    return save("painted_wood" if painted else "oak", rgb, h, rough, note, seed)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mats = [stone("granite", 190400), stone("limestone", 190401, True), brick(), terracotta(), copper(), oak(), oak(True)]
    assets = {}
    for p in sorted(OUT.iterdir()):
        if p.suffix in (".png", ".jpg"):
            assets[p.name] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
    doc = {"title": "Glessner v4 original material studies", "version": 1,
           "generated_by": "generate.py", "confidence": "reconstructed", "materials": mats,
           "rights": "Original procedural pixels; project-permissive terms in LICENSE.txt", "files": assets}
    (OUT / "material-library.json").write_text(json.dumps(doc, indent=2) + "\n")
    print(f"Generated {len(mats)} original {SIZE}-pixel PBR materials ({sum(v['bytes'] for v in assets.values()):,} bytes)")


if __name__ == "__main__":
    main()
