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
MATERIALS = [
    dict(id="sheet_asphalt", directional=False, group="roadway", span_m=4.0, span_across_m=4.0,
         kind="asphalt", mean_roughness=0.70, colors=((92, 90, 86), (60, 59, 57)),
         note="Sheet asphalt (lake asphalt and sand on a concrete base) about one season old: "
              "a fine sand grain, a faint mottle, wheel-polished streaks along the street and "
              "sparse horse-droppings stains. Colour and wear are reconstructed (L294)."),
    dict(id="macadam_limestone", directional=False, group="roadway", span_m=6.0, span_across_m=6.0,
         kind="macadam", mean_roughness=0.92, colors=((160, 154, 140), (112, 108, 99)),
         note="Water-bound crushed-limestone macadam, worn: pale dusty binder over angular "
              "aggregate, wheel tracks along the street and patched hollows. The city's own "
              "1 Dec 1904 report lists these streets as macadam 'in need of repair'; the look "
              "is reconstructed (L294)."),
    dict(id="vitrified_paving_brick", directional=True, group="roadway", span_m=2.12, span_across_m=2.12,
         kind="brick", mean_roughness=0.80, colors=((122, 64, 50), (84, 52, 46)),
         note="Vitrified paving brick laid on edge across the street in running bond, sand "
              "joints: 20 courses of 0.106 m along and 10 bricks of 0.212 m across per tile (a "
              "4 x 8.5 in brick with its joint). The brick size and colour are reconstructed "
              "(L294)."),
    dict(id="earth_and_cinders", directional=False, group="alley", span_m=4.0, span_across_m=4.0,
         kind="cinder", mean_roughness=0.95, colors=((88, 80, 68), (46, 45, 43)),
         note="An unimproved alley: graded earth dressed with ashes and cinders, rutted along "
              "its length. Reconstructed (L295)."),
    dict(id="portland_cement_walk", directional=True, group="walk", span_m=10 * FT, span_across_m="band",
         kind="walk", mean_roughness=0.82, colors=((182, 179, 171), (150, 147, 140)),
         note="Portland cement concrete walk with a trowelled top worn matte, jointed in "
              "blocks: the tile is two blocks along and one across, the 5 x 6 ft blocks of the "
              "1905 code's sec. 2062. The material is reconstructed (L294)."),
    dict(id="sandstone_curbstone", directional=True, group="curb", span_m=12 * FT, span_across_m="band",
         kind="curb", mean_roughness=0.85, colors=((180, 171, 150), (140, 133, 118)),
         note="Buff sandstone curbstones seen from above, two 6-ft stones per tile with a "
              "tooled top and weathered arrises. Sandstone is what the Board of Local "
              "Improvements' 1902-03 ordinances name when they name a curbstone; the stone "
              "and its length here are reconstructed (L294)."),
    dict(id="grass_plat", directional=False, group="parkway", span_m=3.0, span_across_m=3.0,
         kind="grass", mean_roughness=0.95, colors=((86, 112, 52), (58, 80, 38)),
         note="A mown grass plat in July: mixed greens, clover and a few dry patches. The "
              "1905 code's sec. 2077 names grass plats for this space; the turf is "
              "reconstructed (L294)."),
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


SURFACES = {"asphalt": asphalt, "macadam": macadam, "brick": brick, "cinder": cinders,
            "walk": walk, "curb": curb, "grass": grass}


# ---------------------------------------------------------------------------- maps

def maps_from_height(h, strength):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    n = np.stack((-gx, -gy, np.ones_like(h)), axis=-1)
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
        save_jpg(d / f"{stem}_basecolor_web.jpg", color / 255.0, 86)
        save_jpg(d / f"{stem}_normal_gl_web.jpg", ngl, 92)
        save_jpg(d / f"{stem}_orm_web.jpg", orm, 90)
        across = spec["span_across_m"]
        data = {
            **{k: v for k, v in spec.items() if k != "span_across_m"},
            "span_along_m": spec["span_m"],
            "span_across_m": across,
            "resolution_px": SIZE,
            "px_per_m": round(SIZE / spec["span_m"], 2),
            "confidence": "reconstructed appearance; which surface carries it is data/street_surfaces/1904.json's to say",
            "orientation": "image x = along the street (renderer u); image y = across it (v)"
                           + ("; v spans the band's own width" if across == "band" else ""),
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
        {"library": "Prairie Avenue 1904 street-surface PBR materials", "version": "1.0.0",
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
