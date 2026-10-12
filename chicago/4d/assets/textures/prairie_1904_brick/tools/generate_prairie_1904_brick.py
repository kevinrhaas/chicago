#!/usr/bin/env python3
"""Build the Prairie Avenue 1904 K03 brick library (T-2290).

    python3 generate_prairie_1904_brick.py                 # rebuild the library in place
    python3 generate_prairie_1904_brick.py --study DIR     # ...and render the light study into DIR
    python3 generate_prairie_1904_brick.py --check         # every file still hashes as the manifest says

Package K03 of the T-1837 Prairie programme, piece 1 of T-1845. It follows the K01 metric
contract (data/components/prairie_1904/k01_contract.json § scale_uv): TEXCOORD_0 is surface
metres divided by a fabric's tile_m, so every fabric here states its tile in metres and a
0.2 m brick reads as 0.2 m beside any other component.

THREE KINDS OF OUTPUT, and only the first is a fabric a component binds at full detail:

  * FABRICS (brick/<id>/, mortar/<id>/): joint-free clay and mortar grain, seamless, 1 m tile at
    1024 px. No course, joint or brick edge is in any of these maps. At full detail a
    component builds every brick and its recessed mortar bed as geometry (the Glessner v4
    rule, generators/archetypes/masonry_house_v4_detail.py) and maps these onto it.
  * profiles.json: the joints, bonds, specials and per-brick firing variation as DATA, in
    metres. T-2291's components read it; so does this script, which is the proof that it is
    enough to build a wall from.
  * PANELS (panel/<id>/): bonded wall tiles RENDERED FROM profiles.json and the fabrics, for
    the balanced and light exports only, where a district cannot afford a mesh per brick.
    They are a derived product: change a joint in profiles.json and they change with it.

WHAT THESE ARE EVIDENCE OF: NOTHING. Colour, grain, joint, bond and firing spread are
reconstructed (docs/LIBERTIES.md L-k03-brick-library-2290). Which house is which brick is the
T-1837 study's register to say, read per house by T-2291 and the refinement tickets; the `uses`
each fabric lists are the register's own build specifications, quoted, not a ruling.

No photograph is sampled. Image x is along the course (renderer u), image y is up the wall
(v, image top = up).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
FABRIC_PX = 1024
FABRIC_TILE_M = 1.0
PANEL_PX_PER_M = 600.0
SUPERSAMPLE = 2
VERSION = "1.0.0"
TICKET = "T-2290"
LIBERTY = "L-k03-brick-library-2290"
SEED0 = 19040701 + 2290

# The brick module is Glessner v4's (masonry_house_v4_detail.py: 0.2159 m along, 0.066675 m a
# course), so every brick on the street registers with the one canonical asset. Each fabric's
# own joint width is taken out of that module, not added to it.
MODULE_M = 0.2159
COURSE_M = 0.066675
BED_DEPTH_M = 0.1016

# ----------------------------------------------------------------------------- the data

JOINT_PROFILES = {
    # recess_*_frac: how far back the mortar face sits at the joint's top and bottom edge, as
    # a fraction of the fabric's recess_m. A bed joint's face is the straight line between.
    "flush": {"description": "struck off flush with the face; a thin flat line barely behind the arrises",
              "recess_top_frac": 1.0, "recess_bottom_frac": 1.0},
    "struck": {"description": "pressed back at the bottom, flush at the top: a ledge on the brick below catches water",
               "recess_top_frac": 0.0, "recess_bottom_frac": 1.0},
    "weathered": {"description": "pressed back at the top, flush at the bottom: sloped to shed water off the brick below",
                  "recess_top_frac": 1.0, "recess_bottom_frac": 0.0},
    "raked": {"description": "raked out square to a uniform depth, so each course casts a shadow line",
              "recess_top_frac": 1.0, "recess_bottom_frac": 1.0},
}

BONDS = {
    "running": {
        "description": "stretcher (running) bond: every unit a stretcher, each course offset half a module",
        "period_modules": 1.0,
        "courses": [{"units": ["S"], "offset_modules": 0.0}, {"units": ["S"], "offset_modules": 0.5}],
    },
    "common_6": {
        "description": "common (American) bond: five stretcher courses, then a header course tying the wythes",
        "period_modules": 1.0,
        "courses": [{"units": ["S"], "offset_modules": o} for o in (0.0, 0.5, 0.0, 0.5, 0.0)]
                   + [{"units": ["H"], "offset_modules": 0.0}]
                   + [{"units": ["S"], "offset_modules": o} for o in (0.5, 0.0, 0.5, 0.0, 0.5)]
                   + [{"units": ["H"], "offset_modules": 0.0}],
    },
    "flemish": {
        "description": "Flemish bond: stretcher and header alternate in every course, each header centred on the stretcher below",
        "period_modules": 1.5,
        "courses": [{"units": ["S", "H"], "offset_modules": 0.0}, {"units": ["S", "H"], "offset_modules": 0.75}],
    },
}
UNIT_MODULES = {"S": 1.0, "H": 0.5}

MORTARS = [
    {"id": "mortar_dark", "kind": "mortar", "seed": 11,
     "colors": [[70, 62, 57], [44, 40, 38]], "sand": [[96, 88, 80], 0.10], "mean_roughness": 0.86,
     "note": "Fine dark-tinted mortar for tight pressed-brick joints: a lime-and-sand putty darkened to read with a dark red face. The tint is reconstructed; the register's Sherman entry asks for 'tight dark joints' and names no recipe."},
    {"id": "mortar_lime", "kind": "mortar", "seed": 12,
     "colors": [[184, 176, 158], [150, 142, 126]], "sand": [[206, 198, 178], 0.16], "mean_roughness": 0.92,
     "note": "Sandy lime mortar for common and rough brick: warm grey-cream with visible sand and the odd lime nodule, the Glessner v4 mortar's family at the brick library's scale. Clean 1904 condition; soot and damp are condition masks (T-2291), not this map."},
]

BRICKS = [
    {"id": "pressed_red", "kind": "pressed", "seed": 1,
     "colors": [[142, 52, 38], [104, 34, 27]], "mean_roughness": 0.58,
     "joint": {"width_m": 0.004, "recess_m": 0.0006, "profile": "flush", "mortar": "mortar_dark"},
     "arris": {"bevel_m": 0.0012, "chip": None},
     "face_relief_m": 0.0004,
     "variants": [
         {"id": "body", "weight": 0.62, "tint": [1.00, 1.00, 1.00]},
         {"id": "darker_burn", "weight": 0.22, "tint": [0.90, 0.88, 0.90]},
         {"id": "lighter_burn", "weight": 0.12, "tint": [1.07, 1.06, 1.04]},
         {"id": "flashed", "weight": 0.04, "tint": [0.80, 0.76, 0.80]},
     ],
     "bonds": ["running", "flemish"],
     "uses": [
         {"record": "pa-2100-18", "register": "Pressed dark-red brick with tight dark joints, contrasting sandstone bands"},
         {"record": "pa-2126-20", "register": "Five-bay red-brick front, pale marble trim and belts"},
         {"record": "pa-213–217-e.-cullerton-street-27", "register": "213/217 red brick and sandstone"},
     ],
     "not_for": "service walls, party walls and rear ranges (common_buff), or any front the register gives to stone",
     "note": "Dry-pressed face brick: a dense, smooth, even red face with crisp arrises, a faint press sheen and only fine pinholes; laid with thin dark joints so the wall reads as one colour field. Body colour and burn spread are reconstructed."},
    {"id": "common_buff", "kind": "common", "seed": 2,
     "colors": [[196, 162, 124], [160, 122, 92]], "mean_roughness": 0.86,
     "joint": {"width_m": 0.009, "recess_m": 0.003, "profile": "weathered", "mortar": "mortar_lime"},
     "arris": {"bevel_m": 0.003, "chip": {"probability": 0.10, "depth_m": 0.004, "length_m": [0.006, 0.02]}},
     "face_relief_m": 0.0012,
     "variants": [
         {"id": "body", "weight": 0.48, "tint": [1.00, 1.00, 1.00]},
         {"id": "salmon_soft", "weight": 0.22, "tint": [1.04, 0.97, 0.92]},
         {"id": "grey_tan", "weight": 0.18, "tint": [0.95, 0.95, 0.96]},
         {"id": "hard_burnt", "weight": 0.12, "tint": [0.87, 0.81, 0.78]},
     ],
     "bonds": ["common_6", "running"],
     "uses": [
         {"record": "pa-1612-1", "register": "Smooth ashlar street face, common-brick returns"},
         {"record": "pa-1808-6", "register": "Common-brick side and rear ranges"},
         {"record": "pa-1912-10", "register": "Brownstone walls and brick service range"},
         {"record": "pa-2130-42", "register": "Stone-front block with brick rear"},
         {"record": "pa-2031-nrhp", "register": "stone front, brick party walls"},
     ],
     "not_for": "a street front the register names as pressed or rough brick",
     "note": "Common (service) brick for returns, party walls, rear ranges and coach houses: a sandy buff-to-salmon body, softer arrises, sand and lime specks, wider struck joints and a broader firing spread than a face brick. Colour and spread are reconstructed, kept in the Glessner v4 common brick's grey-tan family."},
    {"id": "dark_fired", "kind": "clinker", "seed": 3,
     "colors": [[92, 52, 50], [52, 32, 34]], "mean_roughness": 0.55,
     "joint": {"width_m": 0.006, "recess_m": 0.002, "profile": "struck", "mortar": "mortar_lime"},
     "arris": {"bevel_m": 0.002, "chip": {"probability": 0.06, "depth_m": 0.003, "length_m": [0.005, 0.014]}},
     "face_relief_m": 0.0010,
     "variants": [
         {"id": "body", "weight": 0.55, "tint": [1.00, 1.00, 1.00]},
         {"id": "plum", "weight": 0.25, "tint": [1.08, 0.94, 1.06]},
         {"id": "near_black", "weight": 0.20, "tint": [0.78, 0.78, 0.80]},
     ],
     "bonds": ["flemish"],
     "uses": [
         {"record": None, "register": "the study's 'dark fired variants' (ASSET-CATALOG K03): an accent unit, not a wall fabric"},
     ],
     "not_for": "a whole wall; it is the header of a Flemish front or a single course, and no register entry yet names one",
     "note": "Overburnt, kiln-end brick: purple-brown to near-black, partly vitrified with glassy specks and small bloats. Offered as the header of a Flemish bond and nowhere else until a house's evidence asks for it."},
    {"id": "rough_red_brown", "kind": "rough", "seed": 4,
     "colors": [[132, 70, 50], [94, 50, 38]], "mean_roughness": 0.90,
     "joint": {"width_m": 0.010, "recess_m": 0.005, "profile": "raked", "mortar": "mortar_lime"},
     "arris": {"bevel_m": 0.002, "chip": {"probability": 0.45, "depth_m": 0.006, "length_m": [0.008, 0.035]}},
     "face_relief_m": 0.0025,
     "variants": [
         {"id": "body", "weight": 0.50, "tint": [1.00, 1.00, 1.00]},
         {"id": "browner", "weight": 0.25, "tint": [0.94, 0.92, 0.86]},
         {"id": "redder", "weight": 0.15, "tint": [1.08, 0.96, 0.94]},
         {"id": "dark_end", "weight": 0.10, "tint": [0.78, 0.74, 0.74]},
     ],
     "bonds": ["running"],
     "uses": [
         {"record": "pa-2009-17", "register": "Rough red-brown brick, brownstone basement/copings"},
     ],
     "not_for": "any front other than one the register calls rough; its chipped arris is Mayer's, not a general weathering",
     "note": "Rough-faced red-brown brick: a torn, dragged face with pits and grit, irregular chipped arrises and deep raked joints that put a shadow under every course. Colour, tear and chip rate are reconstructed."},
]

SPECIALS = {
    "stretcher": {"face": "length x height", "length_m": "module - joint", "height_m": "course - joint"},
    "header": {"face": "bed depth x height, set across the wall to tie the wythes",
               "length_m": "module/2 - joint", "note": "the header's face is a half module so it registers with the stretcher joints"},
    "soldier": {"face": "height x length, stood on end", "width_m": "course x 1.5 - joint, rounded to the bond", "height_m": "module - joint",
                "use": "a flat head over an opening or a band; reads the bond's module, never a free width"},
    "rowlock": {"face": "height x bed depth, on edge", "use": "segmental and round arch rings, sills and the cap of a garden wall"},
    "segmental_arch": {"rings": [1, 3], "ring_unit": "rowlock", "rise_to_span": [0.08, 0.18],
                       "taper": "the bricks stay rectangular and the JOINT wedges: joint at the intrados is the fabric's joint width, at the extrados it opens to whatever closes the ring, capped at 2.5 x the joint width; past that add a ring",
                       "keystone": "none in brick unless the house's evidence shows one"},
    "jack_arch": {"unit": "soldier", "skew_deg": [60, 70], "taper": "joints fan from a common centre below the opening", "use": "flat heads where the register calls for them"},
    "string_course": {"forms": ["projecting stretcher course, 0.012-0.025 m proud", "rowlock band", "soldier band"],
                      "rule": "projects from the wall plane; its top is weathered (sloped) so it sheds water. A band in a different fabric is the house's call (sandstone and marble belts are K02's)"},
    "corner_return": {"rule": "the bond turns the corner unbroken: a course that ends in a stretcher on one face starts with a header-length return on the other, so the half-module offset continues round the quoin. Flemish and common-bond header courses take a queen closer (a quarter-module cut) beside the quoin header",
                      "closer_m": "module/4 - joint"},
}

PANELS = [
    {"id": "pressed_red_running", "fabric": "pressed_red", "bond": "running", "modules": 4, "courses": 12,
     "for": "a pressed-brick street front (Sherman-type) at the balanced and light exports"},
    {"id": "common_buff_common_6", "fabric": "common_buff", "bond": "common_6", "modules": 4, "courses": 12,
     "for": "common-brick returns, party walls, rear ranges and coach houses"},
    {"id": "rough_red_brown_running", "fabric": "rough_red_brown", "bond": "running", "modules": 4, "courses": 12,
     "for": "the Mayer front (pa-2009-17)"},
    {"id": "pressed_red_flemish_dark_headers", "fabric": "pressed_red", "bond": "flemish", "header_fabric": "dark_fired",
     "modules": 3, "courses": 12,
     "for": "a Georgian Revival option (pa-2126-20, pa-1700-52) - Flemish bond with burnt headers; no register entry yet attests the bond"},
]

# ---------------------------------------------------------------------------- noise


def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def blur(a, sigma):
    return ndimage.gaussian_filter(a, sigma=sigma, mode="wrap")


def standard(a):
    return clamp01(0.5 + (a - a.mean()) / (6.0 * max(float(a.std()), 1e-6)))


def noise(rng, sigma, size=FABRIC_PX):
    return standard(blur(rng.random((size, size), dtype=np.float32), sigma))


def fbm(rng, sigmas, weights, size=FABRIC_PX):
    out = np.zeros((size, size), np.float32)
    for s, w in zip(sigmas, weights):
        out += (noise(rng, s, size) - 0.5) * w
    return standard(out)


def specks(rng, density, radius_px, size=FABRIC_PX):
    """Sparse seamless round specks (sand grains, lime nodules, pits): 0..1 coverage."""
    seeds = (rng.random((size, size)) < density).astype(np.float32)
    return clamp01(blur(seeds, radius_px) * (2 * math.pi * radius_px * radius_px))


def mix(t, c0, c1):
    t = clamp01(t)[..., None]
    return np.array(c0, np.float32) * (1 - t) + np.array(c1, np.float32) * t


# ------------------------------------------------------------------------ fabrics
# Each returns (height in metres, sRGB colour 0..255, linear roughness 0..1).

def fabric_pressed(spec, rng):
    body = fbm(rng, (90, 30, 8), (0.5, 0.35, 0.15))
    fine = noise(rng, 0.8)
    pins = specks(rng, 0.0009, 0.9)
    press = noise(rng, (2.0, 60.0))            # faint drag of the press along the course
    color = mix(body * 0.75 + fine * 0.25, spec["colors"][1], spec["colors"][0])
    color *= (1 - 0.18 * pins)[..., None]
    h = (fine - 0.5) * 0.00012 + (press - 0.5) * 0.00008 - pins * 0.0006
    rough = clamp01(spec["mean_roughness"] + (fine - 0.5) * 0.08 + (press - 0.5) * 0.06 + pins * 0.2)
    return h, color, rough


def fabric_common(spec, rng):
    body = fbm(rng, (120, 40, 10), (0.45, 0.35, 0.2))
    grain = noise(rng, 1.0)
    sand = specks(rng, 0.004, 0.7)
    lime = specks(rng, 0.00003, 1.6)
    pits = specks(rng, 0.0003, 0.9)
    color = mix(body * 0.7 + grain * 0.3, spec["colors"][1], spec["colors"][0])
    color = color * (1 - 0.35 * sand)[..., None] + np.array([226, 214, 190], np.float32) * (0.35 * sand)[..., None]
    color = color * (1 - 0.5 * lime)[..., None] + np.array([226, 220, 204], np.float32) * (0.5 * lime)[..., None]
    color *= (1 - 0.12 * pits)[..., None]
    h = (grain - 0.5) * 0.0004 + (fbm(rng, (24, 6), (0.6, 0.4)) - 0.5) * 0.0008 + sand * 0.00015 - pits * 0.0006
    rough = clamp01(spec["mean_roughness"] + (grain - 0.5) * 0.1 + pits * 0.08)
    return h, color, rough


def fabric_clinker(spec, rng):
    body = fbm(rng, (70, 20, 6), (0.45, 0.35, 0.2))
    glaze = clamp01((noise(rng, 3.0) - 0.62) * 6.0)        # vitrified, glassy patches
    bloat = specks(rng, 0.0005, 2.0)
    color = mix(body, spec["colors"][1], spec["colors"][0])
    color = color * (1 - 0.35 * glaze)[..., None] + np.array([38, 30, 38], np.float32) * (0.35 * glaze)[..., None]
    h = (body - 0.5) * 0.0006 + bloat * 0.0008 + (noise(rng, 1.2) - 0.5) * 0.0002
    rough = clamp01(spec["mean_roughness"] + 0.12 - glaze * 0.45 + (body - 0.5) * 0.08)
    return h, color, rough


def fabric_rough(spec, rng):
    body = fbm(rng, (110, 35, 9), (0.45, 0.35, 0.2))
    # the wire-cut / sanded face: short torn ridges along the course over a coarse lumpy body
    tear = standard(blur(rng.random((FABRIC_PX, FABRIC_PX), dtype=np.float32), (1.6, 5.0)))
    lump = noise(rng, 7.0)
    grit = specks(rng, 0.003, 0.8)
    pits = specks(rng, 0.0007, 1.1)
    color = mix(body * 0.85 + lump * 0.15, spec["colors"][1], spec["colors"][0])
    color *= (0.96 + 0.04 * tear)[..., None]
    color = color * (1 - 0.25 * grit)[..., None] + np.array([168, 120, 92], np.float32) * (0.25 * grit)[..., None]
    color *= (1 - 0.15 * pits)[..., None]
    h = (tear - 0.5) * 0.0007 + (lump - 0.5) * 0.0012 + (body - 0.5) * 0.0008 - pits * 0.0012 + grit * 0.0002
    rough = clamp01(spec["mean_roughness"] + (tear - 0.5) * 0.06)
    return h, color, rough


def fabric_mortar(spec, rng):
    body = fbm(rng, (60, 14, 3), (0.4, 0.35, 0.25))
    sand = specks(rng, 0.02, 0.7)
    nodule = specks(rng, 0.00008, 2.0)
    color = mix(body, spec["colors"][1], spec["colors"][0])
    sc, sw = spec["sand"]
    color = color * (1 - sw * 2 * sand)[..., None] + np.array(sc, np.float32) * (sw * 2 * sand)[..., None]
    color = color * (1 - 0.6 * nodule)[..., None] + np.array([236, 232, 220], np.float32) * (0.6 * nodule)[..., None]
    h = (body - 0.5) * 0.0006 + sand * 0.0002
    rough = clamp01(spec["mean_roughness"] + (body - 0.5) * 0.06)
    return h, color, rough


FABRICS = {"pressed": fabric_pressed, "common": fabric_common, "clinker": fabric_clinker,
           "rough": fabric_rough, "mortar": fabric_mortar}

# ---------------------------------------------------------------------------- maps


def normal_gl(h, px_per_m_x, px_per_m_y):
    """OpenGL (+Y up the image) tangent-space normal from a height field in metres.
    Image row 0 is the TOP of the wall, so up (+v) is -row."""
    dhdx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * px_per_m_x
    dhdrow = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * px_per_m_y
    n = np.stack((-dhdx, dhdrow, np.ones_like(h)), axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n


def ambient_occlusion(h, px_per_m, scale_m):
    sigma = max(1.0, scale_m * px_per_m)
    local = blur(h, sigma) - h
    # a recess darkens, it never goes black: diffuse sky still reaches a 5 mm joint
    return np.clip(1 - np.maximum(local, 0) / max(scale_m, 1e-6) * 1.6, 0.45, 1.0)


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


COLOR_SPACE = {"basecolor": "sRGB", "normal_gl": "linear, OpenGL +Y (up the wall)", "roughness": "linear",
               "height16": "linear 16-bit; 0 = height_range_m[0], 65535 = height_range_m[1]",
               "orm": "linear; R=AO G=Roughness B=Metallic"}
WEB = ("basecolor", "normal_gl", "orm")


def write_maps(d: Path, stem: str, h, color, rough, ppm_x, ppm_y, ao_scale_m):
    d.mkdir(parents=True, exist_ok=True)
    n = normal_gl(h, ppm_x, ppm_y)
    ao = ambient_occlusion(h, (ppm_x + ppm_y) / 2, ao_scale_m)
    orm = np.stack((ao, rough, np.zeros_like(rough)), axis=-1)
    lo, hi = float(h.min()), float(h.max())
    save_png8(d / f"{stem}_basecolor.png", color / 255.0)
    save_png8(d / f"{stem}_normal_gl.png", n * 0.5 + 0.5)
    save_png8(d / f"{stem}_roughness.png", rough)
    save_png16(d / f"{stem}_height16.png", (h - lo) / max(hi - lo, 1e-9))
    save_png8(d / f"{stem}_orm.png", orm)
    save_jpg(d / f"{stem}_basecolor_web.jpg", color / 255.0, 86)
    save_jpg(d / f"{stem}_normal_gl_web.jpg", n * 0.5 + 0.5, 92)
    save_jpg(d / f"{stem}_orm_web.jpg", orm, 90)
    return n, ao, (round(lo, 6), round(hi, 6))


def measured(color, rough):
    return {"mean_srgb": [int(round(float(c))) for c in color.reshape(-1, 3).mean(0)],
            "mean_roughness": round(float(rough.mean()), 3)}


# ---------------------------------------------------------------------------- fabrics


def build_fabrics(out: Path):
    built, records = {}, []
    for spec in BRICKS + MORTARS:
        seed = SEED0 + spec["seed"] * 101
        rng = np.random.default_rng(seed)
        h, color, rough = FABRICS[spec["kind"]](spec, rng)
        group = "mortar" if spec["kind"] == "mortar" else "brick"
        d = out / group / spec["id"]
        _, _, hr = write_maps(d, spec["id"], h, color, rough, FABRIC_PX / FABRIC_TILE_M,
                              FABRIC_PX / FABRIC_TILE_M, 0.004)
        built[spec["id"]] = (h, color, rough)
        rec = {
            "id": spec["id"], "group": group, "role": "fabric",
            "kind": spec["kind"],
            "tile_m": [FABRIC_TILE_M, FABRIC_TILE_M], "resolution_px": FABRIC_PX,
            "px_per_m": FABRIC_PX / FABRIC_TILE_M,
            "uv_rule": "K01 scale_uv: TEXCOORD_0 = surface metres / tile_m (data/components/prairie_1904/k01_contract.json)",
            "joints_in_map": False,
            "orientation": "image x = along the course (u); image y = up the wall (v), image top = up",
            "height_range_m": list(hr),
            **measured(color, rough),
            "note": spec["note"],
            "confidence": "reconstructed appearance; which house wears it is the T-1837 register's to say",
            "liberty": LIBERTY,
            "color_space": COLOR_SPACE,
            "web": {s: f'{spec["id"]}_{s}_web.jpg' for s in WEB},
            "seamless": True,
            "generator_seed": seed,
            "generation_method": "deterministic procedural synthesis (tools/generate_prairie_1904_brick.py); no photograph sampled",
        }
        (d / "material.json").write_text(json.dumps(rec, indent=2) + "\n")
        records.append(rec)
    return built, records


# ---------------------------------------------------------------------------- panels


def sample_wrap(img, ys, xs):
    """Bilinear, wrapping sample of a (H, W[, C]) fabric at fabric-pixel coordinates."""
    if img.ndim == 2:
        return ndimage.map_coordinates(img, [ys, xs], order=1, mode="grid-wrap")
    return np.stack([ndimage.map_coordinates(img[..., c], [ys, xs], order=1, mode="grid-wrap")
                     for c in range(img.shape[-1])], axis=-1)


def unit_rng(seed, course, unit, salt=0):
    return np.random.default_rng([seed, course, unit, salt])


def course_layout(bond, course_idx, width_modules):
    """[(x0_m, length_m, kind, unit_id)] covering [0, width) with the bond's offset, wrapping."""
    c = bond["courses"][course_idx % len(bond["courses"])]
    width_m = width_modules * MODULE_M
    cycle = [UNIT_MODULES[u] * MODULE_M for u in c["units"]]
    x = -c["offset_modules"] * MODULE_M
    units, k = [], 0
    while x > 0:
        x -= sum(cycle)
    while x < width_m - 1e-9:
        for j, length in enumerate(cycle):
            if x + length > 1e-9 and x < width_m - 1e-9:
                units.append((x, length, c["units"][j], k))
            x += length
            k += 1
    # A unit straddling the tile edge is ONE unit with its wrapped twin: key it by where it
    # starts, modulo the tile, so both copies draw the same brick.
    return [(x0, length, kind, int(round((x0 % width_m) / MODULE_M * 4000)) % int(round(width_m / MODULE_M * 4000)))
            for (x0, length, kind, _k) in units]


def build_panel(panel, fabrics, profiles):
    fab = profiles["fabrics"][panel["fabric"]]
    hfab = profiles["fabrics"].get(panel.get("header_fabric") or panel["fabric"])
    bond = profiles["bonds"][panel["bond"]]
    joint = fab["joint"]
    mortar_id = joint["mortar"]
    jw, recess = joint["width_m"], joint["recess_m"]
    prof = profiles["joint_profiles"][joint["profile"]]
    width_m = panel["modules"] * MODULE_M
    height_m = panel["courses"] * COURSE_M
    W = int(round(width_m * PANEL_PX_PER_M))
    H = int(round(height_m * PANEL_PX_PER_M))
    S = SUPERSAMPLE
    ppm_x, ppm_y = W / width_m, H / height_m
    xs = (np.arange(W * S) + 0.5) / (W * S) * width_m
    ys_top = (np.arange(H * S) + 0.5) / (H * S) * height_m          # 0 at the image top
    X, YT = np.meshgrid(xs, ys_top)
    Y = height_m - YT                                              # metres up from the panel foot

    seed = SEED0 + hash_seed(panel["id"])
    height = np.zeros_like(X)
    color = np.zeros(X.shape + (3,), np.float32)
    rough = np.zeros_like(X)
    mortar_h, mortar_c, mortar_r = fabrics[mortar_id]
    fpx = FABRIC_PX / FABRIC_TILE_M
    m_h = sample_wrap(mortar_h, YT * fpx, X * fpx)
    m_c = sample_wrap(mortar_c, YT * fpx, X * fpx)
    m_r = sample_wrap(mortar_r, YT * fpx, X * fpx)

    course = np.floor(Y / COURSE_M).astype(int)
    vy = Y - course * COURSE_M                                     # 0..course, up from the bed below
    for ci in range(panel["courses"]):
        rows = course == ci
        if not rows.any():
            continue
        units = course_layout(bond, ci, panel["modules"])
        for (x0, length, kind, uid) in units:
            spec = hfab if kind == "H" else fab
            fid = panel.get("header_fabric") if kind == "H" and panel.get("header_fabric") else panel["fabric"]
            uid_wrapped = uid
            r = unit_rng(seed, ci, uid_wrapped)
            # this unit covers [x0, x0+length) and its wrapped copy
            for shift in (0.0, width_m, -width_m):
                a = x0 + shift
                sel = rows & (X >= a) & (X < a + length)
                if not sel.any():
                    continue
                u = X[sel] - a
                v = vy[sel]
                paint_unit(sel, u, v, length, spec, fid, fabrics, r, height, color, rough, jw, recess, prof,
                           m_h[sel], m_c[sel], m_r[sel], ci, uid_wrapped, seed)
    # supersample down
    def down(a):
        if a.ndim == 2:
            return a.reshape(H, S, W, S).mean(axis=(1, 3))
        return a.reshape(H, S, W, S, a.shape[-1]).mean(axis=(1, 3))
    return down(height), down(color), down(rough), (W, H, ppm_x, ppm_y, width_m, height_m)


def hash_seed(text):
    return int(hashlib.sha256(text.encode()).hexdigest()[:8], 16) % 100000


def paint_unit(sel, u, v, length, spec, fid, fabrics, r, height, color, rough, jw, recess, prof,
               mh, mc, mr, ci, uid, seed):
    # per-unit draws, independent: no alternating pattern, no checkerboard
    variants = spec["variants"]
    w = np.array([vv["weight"] for vv in variants])
    k = int(r.choice(len(variants), p=w / w.sum()))
    tint = np.array(variants[k]["tint"], np.float32)
    ox, oy = r.random(2) * FABRIC_TILE_M                           # each brick its own piece of clay
    tilt = (r.random(2) - 0.5) * 2 * spec["face_relief_m"]         # a brick is never laid dead flat
    fh, fc, fr = fabrics[fid]
    fpx = FABRIC_PX / FABRIC_TILE_M
    b_h = sample_wrap(fh, (COURSE_M - v + oy) * fpx, (u + ox) * fpx)
    b_c = sample_wrap(fc, (COURSE_M - v + oy) * fpx, (u + ox) * fpx) * tint
    b_r = sample_wrap(fr, (COURSE_M - v + oy) * fpx, (u + ox) * fpx)

    half = jw / 2
    dx = np.minimum(u - half, length - half - u)
    dy = np.minimum(v - half, COURSE_M - half - v)
    bevel = spec["arris"]["bevel_m"]
    edge = np.minimum(dx, dy)
    on_brick = edge >= 0
    # chipped arrises: a few bites out of the edge band, drawn per unit
    chip = spec["arris"].get("chip")
    bite = np.zeros_like(u)
    if chip:
        n_chips = r.binomial(4, chip["probability"])
        for _ in range(int(n_chips)):
            side = int(r.integers(4))
            lo_l, hi_l = chip["length_m"]
            clen = lo_l + r.random() * (hi_l - lo_l)
            depth = chip["depth_m"] * (0.5 + r.random())
            along = u if side < 2 else v
            span = length if side < 2 else COURSE_M
            c0 = r.random() * span
            from_edge = (v - half) if side == 0 else (COURSE_M - half - v) if side == 1 else \
                        (u - half) if side == 2 else (length - half - u)
            reach = clen * 0.35
            inside = np.clip(1 - np.abs(along - c0) / (clen / 2), 0, 1) * np.clip(1 - from_edge / reach, 0, 1)
            bite = np.maximum(bite, inside * depth)
    ramp = np.clip(edge / max(bevel, 1e-6), 0, 1)
    face = (b_h - b_h.mean() if b_h.size else b_h) + tilt[0] * (u / length - 0.5) + tilt[1] * (v / COURSE_M - 0.5)
    brick_h = face - bevel * 0.6 * (1 - ramp) ** 2 - bite
    # mortar: recessed, and on a bed joint sloped between the profile's top and bottom recess.
    # t runs 0 -> 1 from the joint's bottom edge to its top; this course holds the upper half
    # of the joint below it and the lower half of the joint above it.
    t = np.where(v < half, (v + half) / jw, np.where(v > COURSE_M - half, (v - (COURSE_M - half)) / jw, -1.0))
    bed_frac = prof["recess_bottom_frac"] * (1 - t) + prof["recess_top_frac"] * t
    perp_frac = (prof["recess_bottom_frac"] + prof["recess_top_frac"]) / 2
    frac = np.where(t >= 0, bed_frac, perp_frac)
    mortar_surface = -recess * frac + (mh - 0.0003)
    in_mortar = ~on_brick | (brick_h < mortar_surface)
    hh = np.where(in_mortar, mortar_surface, brick_h)
    shade = (1 - 0.25 * (bite / max(chip["depth_m"], 1e-6) if chip else 0))
    cc = np.where(in_mortar[:, None], mc, b_c * (np.clip(shade, 0.6, 1.0)[:, None] if chip else 1.0))
    rr = np.where(in_mortar, mr, b_r)
    height[sel] = hh
    color[sel] = cc
    rough[sel] = rr


def build_panels(out: Path, fabrics, profiles):
    records = []
    for panel in PANELS:
        h, color, rough, (W, H, ppm_x, ppm_y, width_m, height_m) = build_panel(panel, fabrics, profiles)
        d = out / "panel" / panel["id"]
        n, ao, hr = write_maps(d, panel["id"], h, np.clip(color, 0, 255), rough, ppm_x, ppm_y, 0.006)
        fab = profiles["fabrics"][panel["fabric"]]
        rec = {
            "id": panel["id"], "group": "panel", "role": "lod_panel",
            "lod": ["balanced", "light"],
            "fabric": panel["fabric"], "bond": panel["bond"],
            **({"header_fabric": panel["header_fabric"]} if panel.get("header_fabric") else {}),
            "mortar": fab["joint"]["mortar"], "joint": fab["joint"],
            "tile_m": [round(width_m, 6), round(height_m, 6)],
            "repeat": {"modules": panel["modules"], "courses": panel["courses"]},
            "resolution_px": [W, H], "px_per_m": [round(ppm_x, 3), round(ppm_y, 3)],
            "uv_rule": "K01 scale_uv: TEXCOORD_0 = surface metres / tile_m; u = 0 on a perpend, v = 0 on a bed joint's centre",
            "joints_in_map": True,
            "derived_from": "profiles.json + the fabric and mortar maps, by this generator; never hand-edited",
            "for": panel["for"],
            "not_for": "the full export, where every brick is geometry and the joint-free fabric maps apply",
            "orientation": "image x = along the course (u); image y = up the wall (v), image top = up",
            "height_range_m": list(hr),
            **measured(np.clip(color, 0, 255), rough),
            "confidence": "reconstructed appearance and bond; see the fabric's material.json and the liberty",
            "liberty": LIBERTY,
            "color_space": COLOR_SPACE,
            "web": {s: f'{panel["id"]}_{s}_web.jpg' for s in WEB},
            "seamless": True,
            "generation_method": "deterministic: rasterised from profiles.json at 2x supersampling (tools/generate_prairie_1904_brick.py)",
        }
        (d / "material.json").write_text(json.dumps(rec, indent=2) + "\n")
        records.append((rec, h, color, rough, n, ao))
    return records


# ---------------------------------------------------------------------------- profiles


def profiles_doc():
    fabrics = {}
    for b in BRICKS:
        fabrics[b["id"]] = {
            "unit": {"module_m": MODULE_M, "course_m": COURSE_M,
                     "stretcher_m": [round(MODULE_M - b["joint"]["width_m"], 6), round(COURSE_M - b["joint"]["width_m"], 6)],
                     "header_m": [round(MODULE_M / 2 - b["joint"]["width_m"], 6), round(COURSE_M - b["joint"]["width_m"], 6)],
                     "bed_depth_m": BED_DEPTH_M},
            "joint": b["joint"],
            "arris": b["arris"],
            "face_relief_m": b["face_relief_m"],
            "variants": b["variants"],
            "variation_rule": "each unit draws ONE variant by weight, independently, from a generator seeded by (component seed, course, unit): no alternating, banded or checkerboard pattern, and the same wall draws the same bricks on every machine (K01 § seed)",
            "bonds": b["bonds"],
            "uses": b["uses"],
            "not_for": b["not_for"],
            "fabric": f'brick/{b["id"]}/material.json',
            "confidence": "reconstructed",
            "note": b["note"],
        }
    return {
        "library": "Prairie Avenue 1904 K03 brick library - profiles",
        "version": VERSION, "ticket": TICKET, "parent": "T-1845", "programme": "T-1837",
        "read_by": "T-2291 (the K03 wall on a named target) and every Prairie component that builds brick",
        "rule": "Joints, bonds, specials and firing spread are DATA here, in metres. No fabric map carries a joint; a component builds them from this file at full detail, and the lod panels are rendered from it for the balanced and light exports.",
        "module": {"length_m": MODULE_M, "course_m": COURSE_M, "bed_depth_m": BED_DEPTH_M,
                   "why": "the Glessner v4 brick module (generators/archetypes/masonry_house_v4_detail.py), so every brick in the district registers with the canonical asset; each fabric's joint comes out of the module rather than being added to it",
                   "confidence": "reconstructed - no 1904 brick size for these houses is a source here"},
        "condition": "Clean 1904 bodies. Soot, damp, efflorescence and dirt are condition masks laid over the fabric (T-2291), never baked into it, so body clay and dirt stay separable.",
        "fabrics": fabrics,
        "mortars": {m["id"]: {"fabric": f'mortar/{m["id"]}/material.json', "note": m["note"], "confidence": "reconstructed"}
                    for m in MORTARS},
        "joint_profiles": JOINT_PROFILES,
        "bonds": BONDS,
        "unit_modules": UNIT_MODULES,
        "specials": SPECIALS,
        "panels": [{"id": p["id"], "fabric": p["fabric"], "bond": p["bond"],
                    **({"header_fabric": p["header_fabric"]} if p.get("header_fabric") else {}),
                    "modules": p["modules"], "courses": p["courses"], "for": p["for"],
                    "material": f'panel/{p["id"]}/material.json'} for p in PANELS],
        "liberty": LIBERTY,
    }


def check_profiles(doc):
    errs = []
    mortars = set(doc["mortars"])
    for fid, f in doc["fabrics"].items():
        j = f["joint"]
        if j["mortar"] not in mortars:
            errs.append(f"{fid}: mortar {j['mortar']} is not in the library")
        if j["profile"] not in doc["joint_profiles"]:
            errs.append(f"{fid}: joint profile {j['profile']} unknown")
        if not 0 < j["width_m"] < COURSE_M / 3:
            errs.append(f"{fid}: joint {j['width_m']} m is not a joint")
        for bnd in f["bonds"]:
            if bnd not in doc["bonds"]:
                errs.append(f"{fid}: bond {bnd} unknown")
        if abs(sum(v["weight"] for v in f["variants"]) - 1) > 1e-6:
            errs.append(f"{fid}: variant weights do not sum to 1")
    for p in doc["panels"]:
        b = doc["bonds"][p["bond"]]
        if (p["modules"] / b["period_modules"]) % 1:
            errs.append(f"{p['id']}: {p['modules']} modules is not a whole number of {p['bond']} periods")
        if p["courses"] % len(b["courses"]):
            errs.append(f"{p['id']}: {p['courses']} courses is not a whole number of {p['bond']} cycles")
        if p["bond"] not in doc["fabrics"][p["fabric"]]["bonds"]:
            errs.append(f"{p['id']}: {p['fabric']} is not offered in {p['bond']}")
    return errs


# ---------------------------------------------------------------------------- study

def srgb_to_lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def shade(h, color, rough, n, ao, ppm, light):
    alb = srgb_to_lin(np.clip(color, 0, 255))
    if light == "diffuse":
        # overcast sky: hemisphere light, no direct sun
        e = (0.62 + 0.38 * n[..., 2]) * ao
        out = alb * e[..., None] * 0.95
    else:
        el, az = math.radians(14.0), math.radians(150.0)          # low sun from the upper left
        L = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
        ndl = np.clip((n * L).sum(-1), 0, 1)
        # height-field shadow: march toward the light in image space
        step_px = 1.0
        dx, drow = math.cos(az) * step_px, -math.sin(az) * step_px
        rise = math.tan(el) / ppm * step_px
        lit = np.ones_like(h, dtype=bool)
        for k in range(1, 40):
            hs = ndimage.shift(h, (-drow * k, -dx * k), order=1, mode="grid-wrap")
            lit &= hs <= h + rise * k
        Hh = (L + np.array([0, 0, 1])) / np.linalg.norm(L + np.array([0, 0, 1]))
        ndh = np.clip((n * Hh).sum(-1), 0, 1)
        shin = 2 + (1 - rough) * 60
        spec = 0.04 * (shin + 2) / 8 * ndh ** shin * ndl
        direct = (alb * ndl[..., None] + spec[..., None]) * lit[..., None] * 3.2
        out = direct + alb * 0.10 * ao[..., None]
    return as_u8(lin_to_srgb(out))


def study(out: Path, study_dir: Path, fabric_records, panel_records):
    study_dir.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default()
    cell_w = max(r[0]["resolution_px"][0] for r in panel_records)
    cell_h = max(r[0]["resolution_px"][1] for r in panel_records)
    label = 36
    sheet = Image.new("RGB", (cell_w * 2 + 30, (cell_h + label) * len(panel_records) + 40), (24, 24, 22))
    draw = ImageDraw.Draw(sheet)
    draw.text((10, 10), "K03 brick panels rendered from profiles.json - raking light (14 deg, upper left) | diffuse overcast",
              font=font, fill=(235, 232, 220))
    costs = []
    for i, (rec, h, color, rough, n, ao) in enumerate(panel_records):
        W, H = rec["resolution_px"]
        ppm = sum(rec["px_per_m"]) / 2
        y0 = 40 + i * (cell_h + label)
        for j, light in enumerate(("raking", "diffuse")):
            img = Image.fromarray(shade(h, color, rough, n, ao, ppm, light))
            sheet.paste(img, (10 + j * (cell_w + 10), y0))
        bar = int(round(0.1 * ppm))
        draw.rectangle((10, y0 + H + 6, 10 + bar, y0 + H + 10), fill=(235, 232, 220))
        draw.text((16 + bar, y0 + H + 2), f'10 cm   {rec["id"]}  ({rec["fabric"]}, {rec["bond"]} bond, '
                  f'{rec["joint"]["width_m"] * 1000:.0f} mm {rec["joint"]["profile"]} joint in {rec["mortar"]})',
                  font=font, fill=(200, 198, 188))
    buf = io.BytesIO()
    sheet.save(buf, format="JPEG", quality=90, optimize=True)
    (study_dir / "k03_brick_study.jpg").write_bytes(buf.getvalue())
    # the joint-free fabrics, at 1:1 over a 25 cm crop, both lights
    crop = 256
    fs = Image.new("RGB", (crop * 2 + 30, (crop + label) * len(fabric_records) + 40), (24, 24, 22))
    fd = ImageDraw.Draw(fs)
    fd.text((10, 10), "K03 fabrics, joint-free, 25 x 25 cm at 1 px/mm - raking | diffuse", font=font, fill=(235, 232, 220))
    for i, rec in enumerate(fabric_records):
        d = out / rec["group"] / rec["id"]
        c = np.asarray(Image.open(d / f'{rec["id"]}_basecolor.png').convert("RGB"), np.float32)[:crop, :crop]
        nn = np.asarray(Image.open(d / f'{rec["id"]}_normal_gl.png').convert("RGB"), np.float32)[:crop, :crop] / 255 * 2 - 1
        nn /= np.linalg.norm(nn, axis=-1, keepdims=True)
        orm = np.asarray(Image.open(d / f'{rec["id"]}_orm.png').convert("RGB"), np.float32)[:crop, :crop] / 255
        h16 = np.asarray(Image.open(d / f'{rec["id"]}_height16.png'), np.float32)[:crop, :crop] / 65535
        lo, hi = rec["height_range_m"]
        hm = lo + h16 * (hi - lo)
        y0 = 40 + i * (crop + label)
        for j, light in enumerate(("raking", "diffuse")):
            fs.paste(Image.fromarray(shade(hm, c, orm[..., 1], nn, orm[..., 0], rec["px_per_m"], light)),
                     (10 + j * (crop + 10), y0))
        fd.text((10, y0 + crop + 4), f'{rec["id"]}  mean sRGB {rec["mean_srgb"]}  roughness {rec["mean_roughness"]}',
                font=font, fill=(200, 198, 188))
    buf = io.BytesIO()
    fs.save(buf, format="JPEG", quality=90, optimize=True)
    (study_dir / "k03_fabric_study.jpg").write_bytes(buf.getvalue())


# ---------------------------------------------------------------------------- manifest

def file_costs(out: Path, recs):
    rows = []
    for rec in recs:
        d = out / rec["group"] / rec["id"]
        files = sorted(p for p in d.iterdir() if p.is_file())
        web = [p for p in files if p.name.endswith("_web.jpg")]
        px = rec["resolution_px"]
        px = px * px if isinstance(px, int) else px[0] * px[1]
        rows.append({"id": rec["id"], "group": rec["group"], "pixels_per_map": px,
                     "master_bytes": sum(p.stat().st_size for p in files if not p.name.endswith("_web.jpg")),
                     "web_bytes": sum(p.stat().st_size for p in web)})
    return rows


def all_files(out: Path):
    return sorted(p for p in out.rglob("*") if p.is_file() and p.name != "manifest.json"
                  and "__pycache__" not in p.parts)


def sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build(out: Path, study_dir: Path | None):
    profiles = profiles_doc()
    errs = check_profiles(profiles)
    if errs:
        raise SystemExit("profiles.json refuses itself:\n  " + "\n  ".join(errs))
    (out / "profiles.json").write_text(json.dumps(profiles, indent=2) + "\n")
    fabrics, fabric_records = build_fabrics(out)
    panel_records = build_panels(out, fabrics, profiles)
    costs = file_costs(out, fabric_records + [r[0] for r in panel_records])
    if study_dir:
        study(out, study_dir, fabric_records, panel_records)
    manifest = {
        "library": "Prairie Avenue 1904 K03 brick library", "version": VERSION, "ticket": TICKET,
        "parent": "T-1845", "liberty": LIBERTY,
        "fabrics": [r["id"] for r in fabric_records if r["group"] == "brick"],
        "mortars": [r["id"] for r in fabric_records if r["group"] == "mortar"],
        "panels": [r[0]["id"] for r in panel_records],
        "costs": costs,
        "totals": {"master_bytes": sum(c["master_bytes"] for c in costs),
                   "web_bytes": sum(c["web_bytes"] for c in costs)},
        "files": {str(p.relative_to(out)): sha(p) for p in all_files(out)},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def check(out: Path):
    man = json.loads((out / "manifest.json").read_text())
    bad = [f for f, h in man["files"].items() if not (out / f).is_file() or sha(out / f) != h]
    extra = [str(p.relative_to(out)) for p in all_files(out) if str(p.relative_to(out)) not in man["files"]]
    errs = check_profiles(json.loads((out / "profiles.json").read_text()))
    for line in [f"changed or missing: {f}" for f in bad] + [f"not in the manifest: {f}" for f in extra] + errs:
        print("FAIL", line)
    if bad or extra or errs:
        raise SystemExit(1)
    print(f"ok - {len(man['files'])} files hash as the manifest says; profiles.json holds")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=HERE)
    ap.add_argument("--study", type=Path, default=None)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        check(a.out)
        return
    man = build(a.out, a.study)
    for c in man["costs"]:
        print(f'{c["group"]}/{c["id"]}: {c["pixels_per_map"]:,} px/map, masters {c["master_bytes"]:,} B, web {c["web_bytes"]:,} B')
    print(f'total masters {man["totals"]["master_bytes"]:,} B, web {man["totals"]["web_bytes"]:,} B')


if __name__ == "__main__":
    main()
