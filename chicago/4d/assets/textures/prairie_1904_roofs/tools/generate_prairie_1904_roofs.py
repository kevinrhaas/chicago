#!/usr/bin/env python3
"""The Prairie Avenue 1904 roof-covering library (K04, T-2292): eleven deterministic PBR fabrics.

    python3 assets/textures/prairie_1904_roofs/tools/generate_prairie_1904_roofs.py

Requires numpy, scipy and Pillow. No photograph is sampled.

EVERY MODULE IS READ FROM DATA. A fabric's slate, tile, pan or sheet — its width,
exposure, joint, butt, bond and how many of them fill one tile — is
`data/components/prairie_1904/k04_roofs.json`'s, and this script draws exactly that
many: a tile is `columns x width` across the eave and `courses x exposure` up the
slope, so a K01 roof mapping TEXCOORD_0 = surface metres / tile_m lays its courses at
true size. Change a format there and regenerate here; never stretch a map to fit.

WHAT IS IN A MAP AND WHAT IS NOT. A covering map carries the courses it is made of —
each slate's butt step and side joint, the dressed bevel, the riven grain, the
per-slate tone — because a district of roofs cannot draw every slate as geometry.
Hips, ridges, verges, valleys, aprons, gutters and pipes are not in any map: they are
geometry built from the file's `profiles`. The flashing sheets are plain fabrics.

ORIENTATION. Image x runs along the eave (u). Image y runs up the slope, and the top
row is UPHILL: v grows upward, as glTF's TEXCOORD_0 is read here (the Glessner v4
convention, assets/textures/glessner-v4/generate.py), so the normal map is OpenGL +Y.
Each course's butt is its LOW edge, and the course above laps down over the one below.

Everything is computed at twice the size and box-filtered down, so a 3 mm joint
resolves as a soft line, not a stair of aliased pixels.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

LIB = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[4]
PROFILES = ROOT / "data" / "components" / "prairie_1904" / "k04_roofs.json"
VERSION = "1.0.0"
SIZE = 512
SS = 2
N = SIZE * SS
JPEG_QUALITY = 88

# Colour, roughness and metal per fabric: the appearance, which is ours (reconstructed).
LOOK = {
    "slate_pennsylvania": {"base": (58, 62, 70), "tone": .055, "rough": .62, "metal": 0.},
    "slate_vermont": {"palette": [((96, 106, 98), .55), ((88, 102, 92), .20), ((112, 110, 94), .12),
                                  ((80, 92, 84), .08), ((92, 82, 90), .05)],
                      "tone": .04, "rough": .64, "metal": 0.},
    "slate_fishscale": {"base": (60, 63, 71), "tone": .055, "rough": .62, "metal": 0.},
    "terracotta_flat_tile": {"base": (150, 72, 50), "tone": .07, "rough": .78, "metal": 0.},
    "copper_standing_seam": {"base": (112, 68, 48), "streak": (82, 52, 40), "rough": .48, "metal": .55},
    "tin_standing_seam_painted": {"base": (118, 52, 40), "chalk": (138, 84, 72), "rough": .62, "metal": 0.},
    "tin_flat_seam_painted": {"base": (114, 50, 39), "chalk": (136, 82, 70), "rough": .64, "metal": 0.},
    "copper_sheet": {"base": (110, 67, 48), "streak": (82, 52, 40), "rough": .46, "metal": .55},
    "lead_sheet": {"base": (112, 114, 117), "streak": (96, 98, 101), "rough": .62, "metal": .35},
    "zinc_sheet": {"base": (150, 156, 161), "streak": (132, 138, 144), "rough": .55, "metal": .55},
    "painted_tin_sheet": {"base": (118, 52, 40), "chalk": (138, 84, 72), "rough": .60, "metal": 0.},
}


def seed_of(fid: str) -> int:
    return int(hashlib.sha256(f"prairie_1904_roofs|{fid}".encode()).hexdigest()[:8], 16)


def noise(rng, sigma, aniso=(1., 1.)):
    """A periodic, unit-variance field at N x N; aniso stretches it (rows, cols)."""
    a = rng.standard_normal((N, N)).astype(np.float32)
    a = gaussian_filter(a, (sigma * aniso[0], sigma * aniso[1]), mode="wrap")
    return a / max(float(a.std()), 1e-7)


def phase(fab):
    """Where the first joint and butt fall, in metres from the tile's (u, v) origin.

    A quarter of a unit along the eave and half a course up the slope, so no tile edge
    lies on a joint or a butt: the tile wraps mid-slate, where nothing changes, and a
    seam at its edge would be a fault and not a course line.
    """
    m = fab["module"]
    if "slate_width_m" in m:
        return .25 * m["slate_width_m"], .5 * m["exposure_m"]
    if "sheet_u_m" in m and m["columns"] > 1:
        return .25 * m["sheet_u_m"], .5 * m["sheet_v_m"]
    return 0., 0.


def grid(tile, ph=(0., 0.)):
    """u, v in metres per pixel centre; row 0 is the top of the image, i.e. uphill.

    The returned coordinates are measured from the first joint and butt (`phase`).
    """
    q = (np.arange(N, dtype=np.float64) + .5) / N
    u = q[None, :] * tile[0] - ph[0]
    v = (1. - q[:, None]) * tile[1] - ph[1]
    return np.broadcast_to(u, (N, N)).copy(), np.broadcast_to(v, (N, N)).copy()


def coursed(fab, rng):
    """Slates or flat tiles in broken joint: height (m), unit index, frac up the exposure, joint."""
    m, tile = fab["module"], fab["tile_m"]
    w, e, t, jw = m["slate_width_m"], m["exposure_m"], m["thickness_m"], m["joint_m"]
    cols, rows = m["columns"], m["courses"]
    u, v = grid(tile, phase(fab))
    # The butt line wanders a millimetre or two: hand-laid, hand-dressed.
    wander = noise(rng, N / 160, (.15, 1.)) * .0012
    vv = v + wander
    c0 = np.floor(vv / e).astype(np.int64)
    if m["butt"] == "scalloped":
        r = m["butt_radius_m"]

        def butt(c):
            off = (np.mod(c, 2)) * .5 * w
            du = np.mod(u - off, w) - .5 * w
            return c * e + r - np.sqrt(np.clip(r * r - du * du, 0, None))
        c = np.where(vv >= butt(c0), c0, c0 - 1)
        frac = (vv - butt(c)) / e
    else:
        c = c0
        frac = vv / e - c
    off = np.mod(c, 2) * .5 * w
    col = np.floor((u - off) / w).astype(np.int64)
    du = (u - off) - (col + .5) * w
    ci, cc = np.mod(c, rows), np.mod(col, cols)
    unit = ci * cols + cc
    # Each slate sits a hair proud of or shy of its neighbours, and tilts a little.
    lift = rng.normal(0, .0008, rows * cols)[unit]
    tilt = rng.normal(0, .0006, rows * cols)[unit]
    h = t * (1. - np.clip(frac, 0, 1)) + lift + tilt * (du / w)
    # The dressed bevel along the butt and both sides, broken by chips.
    bevel = .004
    chip = np.clip(noise(rng, N / 300) * .5 + .2, 0, 1) * .002
    edge_d = np.minimum(np.clip(frac, 0, None) * e, .5 * w - np.abs(du))
    h -= np.clip((bevel - edge_d) / bevel, 0, 1) * (.0018 + chip)
    joint = (.5 * w - np.abs(du)) < .5 * jw
    h = np.where(joint, -.001, h)
    return h, unit, frac, joint


def standing_seam(fab, rng):
    m, tile = fab["module"], fab["tile_m"]
    pw, sh, sw = m["pan_width_m"], m["seam_height_m"], m["seam_width_m"]
    cs, stag = m["cross_seam_m"], m["cross_seam_stagger"]
    u, v = grid(tile)
    pan = np.floor(u / pw).astype(np.int64)
    d = np.minimum(np.mod(u, pw), pw - np.mod(u, pw))
    rib = sh * (1. - np.clip((d - .5 * sw) / (.5 * sw), 0, 1) ** 2)
    rib = np.where(d < .5 * sw, sh, np.where(d < sw, rib, 0.))
    # Oil-canning: each pan bellies a millimetre or so between its seams.
    belly = np.sin(np.pi * np.clip(d / (.5 * pw), 0, 1)) * (.0006 + .0006 * noise(rng, N / 18, (3., 1.)))
    vo = v - np.mod(pan, 2) * stag * cs
    dc = np.minimum(np.mod(vo, cs), cs - np.mod(vo, cs))
    cross = np.where(dc < .0065, .0018, 0.) * (d > sw)
    h = rib + belly + cross + noise(rng, 2.) * .00006
    seam = d < sw
    return h, seam, cross > 0


def flat_seam(fab, rng):
    m, tile = fab["module"], fab["tile_m"]
    su, sv, lk, lh = m["sheet_u_m"], m["sheet_v_m"], m["lock_m"], m["lock_height_m"]
    u, v = grid(tile, phase(fab))
    row = np.floor(v / sv).astype(np.int64)
    uo = u - np.mod(row, 2) * .5 * su
    du = np.minimum(np.mod(uo, su), su - np.mod(uo, su))
    dv = np.minimum(np.mod(v, sv), sv - np.mod(v, sv))
    lock = np.minimum(du, dv) < .5 * lk
    pillow = np.sin(np.pi * np.clip(du / (.5 * su), 0, 1)) * np.sin(np.pi * np.clip(dv / (.5 * sv), 0, 1))
    h = np.where(lock, lh, pillow * .0008) + noise(rng, 2.) * .00005
    return h, lock


def sheet(fab, rng, fid):
    h = noise(rng, N / 10) * .0012 + noise(rng, N / 40) * .0004 + noise(rng, 1.5) * .00004
    if fid == "lead_sheet":
        # Bossing marks: shallow dents a dresser's mallet leaves.
        dents = np.clip(noise(rng, N / 120) - 1.6, 0, None)
        h -= dents * .0008
    return h


def to_u8(a):
    return np.clip(a * 255. + .5, 0, 255).astype(np.uint8)


def srgb(c):
    return np.asarray(c, dtype=np.float32) / 255.


def downsample(a):
    if a.ndim == 2:
        return a.reshape(SIZE, SS, SIZE, SS).mean(axis=(1, 3))
    return a.reshape(SIZE, SS, SIZE, SS, a.shape[-1]).mean(axis=(1, 3))


def normals(h, tile):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / (2 * tile[0] / N)
    # Row 0 is uphill, so +v is UP the rows: the derivative is read upward (OpenGL +Y).
    dy = (np.roll(h, 1, 0) - np.roll(h, -1, 0)) / (2 * tile[1] / N)
    n = np.stack((-dx, -dy, np.ones_like(h)), -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    n = downsample(n)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n


def cavity(h):
    """Ambient occlusion from height: what sits below its surroundings is occluded."""
    hn = (h - h.min()) / max(float(np.ptp(h)), 1e-9)
    blur = gaussian_filter(hn, N / 256, mode="wrap")
    return np.clip(1. - 1.6 * np.clip(blur - hn, 0, None), .55, 1.)


def build(fab):
    fid = fab["id"]
    rng = np.random.default_rng(seed_of(fid))
    look = LOOK[fid]
    kind = fab["kind"]
    rough = np.full((N, N), look["rough"], np.float32)
    metal = np.full((N, N), look["metal"], np.float32)
    if kind in ("slate", "tile"):
        h, unit, frac, joint = coursed(fab, rng)
        units = fab["module"]["columns"] * fab["module"]["courses"]
        if "palette" in look:
            cols = np.array([srgb(c) for c, _ in look["palette"]])
            p = np.cumsum([w for _, w in look["palette"]])
            pick = np.searchsorted(p / p[-1], rng.random(units))
            per = cols[pick]
        else:
            per = np.tile(srgb(look["base"]), (units, 1))
        tone = 1. + rng.normal(0, look["tone"], units)
        alb = per[unit] * tone[unit][..., None]
        if kind == "slate":
            # Riven cleavage grain runs the slate's length (up the roof).
            grain = noise(rng, 1.4, (14., 1.)) * .035 + noise(rng, N / 90) * .02
        else:
            grain = noise(rng, 1.2) * .04 + noise(rng, N / 120) * .03
        alb = alb * (1. + grain)[..., None]
        alb = np.where(joint[..., None], alb * .55, alb)
        rough = rough + noise(rng, 3.) * .04 + np.where(joint, .12, 0.)
    elif kind == "standing_seam":
        h, seam, cross = standing_seam(fab, rng)
        base, alt = srgb(look["base"]), srgb(look.get("streak", look.get("chalk")))
        # Downslope streaking: long in v, narrow in u.
        streak = np.clip(noise(rng, 4., (24., 1.)) * .5 + .5, 0, 1) ** 2
        alb = base + (alt - base) * (streak * .22)[..., None]
        alb = alb * (1. + noise(rng, 1.2) * .02)[..., None]
        rough = rough + streak * .06 - np.where(seam, .05, 0.)
    elif kind == "flat_seam":
        h, lock = flat_seam(fab, rng)
        base, alt = srgb(look["base"]), srgb(look["chalk"])
        chalk = np.clip(noise(rng, N / 30) * .5 + .3, 0, 1)
        alb = base + (alt - base) * (chalk * .18)[..., None]
        alb = alb * (1. + noise(rng, 1.2) * .02)[..., None]
        alb = np.where(lock[..., None], alb * .94, alb)
        rough = rough + chalk * .05
    else:
        h = sheet(fab, rng, fid)
        base = srgb(look["base"])
        alt = srgb(look.get("streak", look.get("chalk", look["base"])))
        mott = np.clip(noise(rng, N / 24) * .5 + .5, 0, 1)
        streak = np.clip(noise(rng, 4., (24., 1.)) * .5 + .5, 0, 1) ** 2
        alb = base + (alt - base) * (.25 * mott + .15 * streak)[..., None]
        alb = alb * (1. + noise(rng, 1.2) * .015)[..., None]
        rough = rough + mott * .05
    tile = fab["tile_m"]
    n = normals(h.astype(np.float64), tile)
    ao = downsample(cavity(h))
    alb = downsample(np.clip(alb, 0, 1))
    rough = downsample(np.clip(rough, .05, 1))
    metal = downsample(metal)
    return {"basecolor": alb, "normal": n, "roughness": rough, "ao": ao, "metallic": metal}


def write(fab, maps):
    fid = fab["id"]
    out = LIB / fid
    out.mkdir(parents=True, exist_ok=True)
    alb = to_u8(maps["basecolor"])
    nrm = to_u8(maps["normal"] * .5 + .5)
    rgh = to_u8(maps["roughness"])
    orm = np.stack((to_u8(maps["ao"]), rgh, to_u8(maps["metallic"])), -1)
    Image.fromarray(alb, "RGB").save(out / f"{fid}_basecolor.png", optimize=True)
    Image.fromarray(nrm, "RGB").save(out / f"{fid}_normal_gl.png", optimize=True)
    Image.fromarray(rgh, "L").save(out / f"{fid}_roughness.png", optimize=True)
    Image.fromarray(orm, "RGB").save(out / f"{fid}_orm.png", optimize=True)
    for name, arr in (("basecolor", alb), ("normal_gl", nrm), ("orm", orm)):
        Image.fromarray(arr, "RGB").save(out / f"{fid}_{name}_web.jpg", quality=JPEG_QUALITY,
                                         optimize=True, progressive=False)
    tile = fab["tile_m"]
    mean = [int(round(x)) for x in alb.reshape(-1, 3).mean(0)]
    material = {
        "id": fid,
        "library": "prairie_1904_roofs",
        "version": VERSION,
        "ticket": "T-2292",
        "slot": fab["slot"],
        "kind": fab["kind"],
        "tile_m": tile,
        "module": fab["module"],
        "module_source": "data/components/prairie_1904/k04_roofs.json",
        "course_phase_m": [round(x, 6) for x in phase(fab)],
        "course_phase_rule": "the first vertical joint lies course_phase_m[0] along u and the first butt "
                             "course_phase_m[1] up v from the tile's origin; offset the roof's UV by them "
                             "to put a butt on the eave",
        "resolution_px": SIZE,
        "px_per_m": [round(SIZE / tile[0], 2), round(SIZE / tile[1], 2)],
        "mean_basecolor": mean,
        "mean_roughness": round(float(maps["roughness"].mean()), 3),
        "mean_metallic": round(float(maps["metallic"].mean()), 3),
        "orientation": "image x = along the eave (u); image y = up the slope with the top row uphill "
                       "(v grows upward); each course's butt is its low edge",
        "uv_rule": "TEXCOORD_0 = surface metres / tile_m (k01_contract.json scale_uv)",
        "color_space": {"basecolor": "sRGB", "normal_gl": "linear, OpenGL +Y",
                        "roughness": "linear", "orm": "linear; R=AO G=Roughness B=Metallic"},
        "web": {"basecolor": f"{fid}_basecolor_web.jpg", "normal_gl": f"{fid}_normal_gl_web.jpg",
                "orm": f"{fid}_orm_web.jpg"},
        "seamless": True,
        "generator_seed": seed_of(fid),
        "generation_method": "deterministic procedural synthesis (tools/generate_prairie_1904_roofs.py); "
                             "no photograph sampled",
        "confidence": fab["confidence"],
        "appearance": "reconstructed (docs/LIBERTIES.md L-k04-roof-library-2292)",
        "note": fab["note"],
    }
    (out / "material.json").write_text(json.dumps(material, indent=2) + "\n", encoding="utf-8")
    return material


def main() -> int:
    data = json.loads(PROFILES.read_text(encoding="utf-8"))
    mats = []
    for fab in data["fabrics"]:
        maps = build(fab)
        mats.append(write(fab, maps))
        print(f"  {fab['id']:28s} {fab['tile_m'][0]:.4f} x {fab['tile_m'][1]:.4f} m")
    manifest = {
        "library": "Prairie Avenue 1904 roof coverings and flashings (K04)",
        "version": VERSION,
        "ticket": "T-2292",
        "profiles": "data/components/prairie_1904/k04_roofs.json",
        "materials": [{"id": m["id"], "slot": m["slot"], "kind": m["kind"], "tile_m": m["tile_m"],
                       "material": f"{m['id']}/material.json"} for m in mats],
    }
    (LIB / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
