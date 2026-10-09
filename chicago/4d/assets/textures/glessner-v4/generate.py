#!/usr/bin/env python3
"""Ten deterministic original PBR studies for Glessner v4; no photographic pixels.

python assets/textures/glessner-v4/generate.py
Requires numpy, Pillow and scipy. The house's stone courses and moulded details
are geometry; these maps provide grain, mortar, clay laminations and metal aging.
The maps are reconstructed, bounded by the material descriptions and the visual
scale of existing HABS evidence, never measured samples of the historic surfaces.
The separate granite_photographic_basecolor.png, turf_photographic_basecolor.png
and turf_patch_photographic_basecolor.png are original generated bitmaps; this
recipe preserves them unchanged and never regenerates or overwrites them.
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
          "limestone": (1.2, 1.2), "mortar": (1.2, 1.2), "terracotta": (2.4384, 1.95072),
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
    # Only break mathematical triangle edges slightly; a stronger warp bent
    # the whole split plane into a crumpled sheet in the close-view review.
    warp_x = field(rng, 28) * .004
    warp_y = field(rng, 28) * .004
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
    bodycolour = np.array([.490, .415, .320]) + shifts[..., None]
    bodycolour += (.012 * grit + .021 * soft + .012 * roughclay)[..., None]
    fired = smoothstep(.8, 2.0, field(rng, 20))
    bodycolour -= fired[..., None] * np.array([.033, .022, .014])
    # Intrinsic uneven clay fabric, not modern spalling or soot. Coherent
    # patches alter roughness at centimetre scale rather than each brick being
    # either perfectly polished or uniformly matte.
    clay = field(rng, 14)
    height = .00016 * grit + .00040 * roughclay + .00070 * soft + .00060 * clay
    rough = np.clip(.825 + .028 * roughclay + .042 * clay, .71, .94)
    return save("brick", bodycolour, height, rough, "Reconstructed grey-tan common-brick clay grain. "
                "Courses, bevelled arrises and mortar joints are geometry, not repeated in this map.", seed)


def mortar():
    seed = 190409
    rng = np.random.default_rng(seed)
    sand, fine = field(rng, .8, 1024), field(rng, .6, 1024)
    trowel, broad = field(rng, 9, 1024), field(rng, 72.5, 1024)
    # Match the previous joint's overall beige tone. Change its fabric, not the
    # joint width or a claim about later repointing, algae, damage or staining.
    rgb = np.array([.550, .526, .456]) + (.010 * sand + .010 * trowel + .012 * broad)[..., None]
    pale = smoothstep(.8, 1.8, sand)
    rgb += pale[..., None] * np.array([.020, .019, .016])
    height = .00012 * fine + .00024 * sand + .00025 * trowel
    rough = np.clip(.91 + .025 * sand + .017 * broad, .84, .98)
    return save("mortar", rgb, height, rough,
                "Original reconstructed sandy lime-mortar fabric. Fine mineral grains and restrained "
                "trowelled variation, no later soot or decay; the actual recessed joints are geometry.", seed)


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
                "tiles, lapped noses and ridge caps are geometry. This grain-only fabric "
                "contains no tile module; roof_tiles supplies the mapped joints.", seed)


def roof_tiles():
    """Original numeric tile surface; HABS module, inferred 1904 continuity.

    This is the continuous roof bed / light mesh, not the separate grain-only
    material on full-model tiles and ridge caps. No historic pixels are used.
    """
    record=json.loads((OUT.parents[2]/"data/structures/glessner_house.json").read_text())
    spec=record['phases'][0]['form']['v4_detail']['value']['roof_tiles']
    width,exposure=spec['width_in']*.0254,spec['exposure_in']*.0254
    columns,rows=spec['texture_columns'],spec['texture_rows']
    TILE_M['roof_tiles']=(columns*width,rows*exposure)
    seed=190403
    rng=np.random.default_rng(seed)
    grit,clay=field(rng,.6),field(rng,7)
    # Image top is v=1; Blender and the standalone glTF writer share this UV.
    yy,xx=np.mgrid[:SIZE,:SIZE]
    v=(1-(yy+.5)/SIZE)*rows
    row=np.floor(v).astype(int);course=v-row
    u=(xx+.5)/SIZE*columns-.5*(row%2)
    col=np.floor(u).astype(int);across=u-col
    variation=rng.uniform(-.012,.012,(rows,columns))[row%rows,col%columns]
    edge=np.minimum(across,1-across)*width
    joint=1-smoothstep(spec['joint_m']/2,spec['joint_m']/2+.001,edge)
    nose=1-smoothstep(0,.003,course*exposure)
    rgb=np.array([.493,.240,.166])+(.009*grit+.012*clay+variation)[...,None]
    rgb*=1-(.12*joint+.045*nose)[...,None]
    # Bounded lap and narrow open side joint; no baked directional lighting.
    height=.00004*grit+.00015*clay+.0015*(1-course)-.001*joint
    rough=.71+.035*clay+.025*grit+.035*joint
    return save('roof_tiles',rgb,height,rough,
        'HABS IL-1015 printed p.21: 6-inch tile width, 5-inch exposed course. '
        'Inferred 1904 continuity, checked against Taylor 2135. Red baked unglazed '
        'clay from Glessner 1923; later tar excluded. Stagger, joints, lap relief '
        'and exact colour reconstructed. Sixteen columns by sixteen courses.',seed)


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
        rgb = np.array([.380, .275, .165]) + (.014 * grain + .011 * broad)[..., None]
        h = .00006 * grain
        rough = np.clip(.51 + .035 * grain, .40, .61)
        note = "Warm brown vertically grained exterior oak with restrained varnish roughness. Reconstructed finish, not a sampled timber."
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
    parser.add_argument("--only", choices=[*TILE_M,"roof_tiles"], help="regenerate one fabric and its hash record")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    recipes = {"granite": lambda: stone("granite", 190400),
               "limestone": lambda: stone("limestone", 190401, True), "mortar": mortar,
               "brick": brick, "terracotta": terracotta, "roof_tiles": roof_tiles, "copper": copper,
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
    generated = sorted(OUT.glob("*_provenance.json"))
    if generated:
        doc["generated_albedos"] = [json.loads(path.read_text()) for path in generated]
        doc["rights"] = "Original procedural and generated pixels; project-permissive terms in LICENSE.txt"
    (OUT / "material-library.json").write_text(json.dumps(doc, indent=2) + "\n")
    print(f"Generated {len(mats)} original PBR materials ({sum(v['bytes'] for v in assets.values()):,} bytes)")


if __name__ == "__main__":
    main()
