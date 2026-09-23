#!/usr/bin/env python3
"""Emit a contract-satisfying PLACEHOLDER GLB — pure Python, no Blender.

    python3 generators/placeholder.py                 write the placeholder
    python3 generators/placeholder.py --stdout-json   dump the glTF JSON chunk
    python3 generators/placeholder.py --check         verify without writing

Why this exists
---------------
The renderer track must not wait on the Blender track, and per
`docs/GLB-CONTRACT.md` a placeholder that does not satisfy the contract is worse
than none, because it lets the renderer develop against a fiction. So this
script writes the glTF binary by hand and satisfies the contract exactly:

  * `.glb`, glTF 2.0, Y-up right-handed, metres, authored about a local origin
    at ground level (y = 0 at the base of the walls);
  * one node per structure phase, named `<structure_id>__<phase_id>`, carrying
    `extras.structure_id` / `extras.phase_id` / `extras.scene_ids`;
  * a `_CONFIDENCE` SCALAR float attribute (componentType 5126) on every vertex,
    exercising all three levels — 0.0 attested, 0.5 inferred, 1.0 reconstructed.
    ALL THREE, because the asset's one job is to be the fixture the confidence
    view is tested against, and a level with no vertices behind it is a level the
    view's rendering of it cannot be demonstrated on (T-1112);
  * one material, one primitive, so it drops into a `BatchedMesh` as a single
    geometry; flat per-part colours come from a 4x1 palette texture the way
    `gltf-transform palette` would produce them.

What it is NOT
--------------
It is a box-ish massing, not architecture. Every dimension it uses is read out
of the real record at `data/structures/sauganash_hotel.json`; nothing is
invented here. The parts whose confidence the contract's worked example fixes
are mapped to the record's own attributes, so if the record's confidence changes
the placeholder's `_CONFIDENCE` values change with it.

The colours beyond the two documented ones (white paint, bright-blue shutters)
are placeholder colours and are recorded as such in `asset.extras`.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STRUCTURE = ROOT / "data" / "structures" / "sauganash_hotel.json"
OUT = ROOT / "assets" / "gltf" / "sauganash_hotel__frame_1831.placeholder.glb"
SIDECAR = ROOT / "data" / "sidecars" / "1835" / "sauganash_hotel.json"

STRUCTURE_ID = "sauganash_hotel"
PHASE_ID = "frame_1831"
SCENE_IDS = ["1835"]

# docs/GLB-CONTRACT.md, "The confidence channel"
CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}
WORST_FIRST = ("reconstructed", "inferred", "attested")

# Which record attributes drive which piece of geometry. This mapping IS the
# contract's worked example; the numbers come from the record, not from here.
# Rule: when several attributes drive one piece of geometry, the least confident
# wins. A wall whose height is a guess is a guessed wall.
PART_DRIVERS = {
    "walls": ["stories", "wall_height_m"],
    "roof": ["roof_type", "roof_pitch_deg"],
    "cross_wing": ["cross_wing", "cross_wing_end", "cross_wing_depth_m"],
    "log_wing": ["log_wing"],
    "shutters": ["shutters"],
}

# Palette texel index per part. One material + a tiny nearest-filtered palette is
# what `gltf-transform palette` produces, and it keeps the whole structure in one
# primitive so a BatchedMesh sees one geometry.
PALETTE = [
    ("#f2efe6", "walls", "white — documented (Wau-Bun: 'a pretentious white two-story building')"),
    ("#2f5fb0", "shutters", "bright blue — documented (Wau-Bun: 'with bright-blue wooden shutters')"),
    ("#6b5334", "log_wing", "PLACEHOLDER colour; no source attests the wing's finish"),
    ("#4a4640", "roof", "PLACEHOLDER colour; no source attests any roof finish, and "
                        "roof_type itself is only inferred"),
]
PALETTE_INDEX = {name: i for i, (_hex, name, _note) in enumerate(PALETTE)}


# --------------------------------------------------------------------------- #
# the record
# --------------------------------------------------------------------------- #

def load_phase() -> dict:
    doc = json.loads(STRUCTURE.read_text())
    for ph in doc.get("phases", []):
        if ph.get("id") == PHASE_ID:
            return doc, ph
    raise SystemExit(f"phase '{PHASE_ID}' not found in {STRUCTURE}")


def worst(levels: list[str]) -> str:
    for level in WORST_FIRST:
        if level in levels:
            return level
    raise SystemExit(f"no usable confidence in {levels}")


def part_confidence(phase: dict) -> dict[str, tuple[str, float]]:
    """Resolve each geometry part's confidence out of the record."""
    form = phase.get("form", {})
    out = {}
    for part, drivers in PART_DRIVERS.items():
        levels = []
        for attr in drivers:
            if attr not in form:
                raise SystemExit(
                    f"{STRUCTURE.name}: phase {PHASE_ID} has no form attribute "
                    f"'{attr}', which drives the '{part}' geometry. The placeholder "
                    f"refuses to guess — fix the mapping or the record."
                )
            levels.append(form[attr]["confidence"])
        level = worst(levels)
        out[part] = (level, CONFIDENCE_VALUE[level])
    return out


# --------------------------------------------------------------------------- #
# geometry
# --------------------------------------------------------------------------- #

class Mesh:
    """Flat-shaded triangle soup. Positions in metres, Y up, +X east, -Z north."""

    def __init__(self) -> None:
        self.pos: list[float] = []
        self.nrm: list[float] = []
        self.uv: list[float] = []
        self.conf: list[float] = []
        self.idx: list[int] = []

    def quad(self, a, b, c, d, normal, part, conf) -> None:
        base = len(self.pos) // 3
        u = (PALETTE_INDEX[part] + 0.5) / len(PALETTE)
        for v in (a, b, c, d):
            self.pos.extend(v)
            self.nrm.extend(normal)
            self.uv.extend((u, 0.5))
            self.conf.append(conf)
        self.idx.extend((base, base + 1, base + 2, base, base + 2, base + 3))

    def tri(self, a, b, c, normal, part, conf) -> None:
        base = len(self.pos) // 3
        u = (PALETTE_INDEX[part] + 0.5) / len(PALETTE)
        for v in (a, b, c):
            self.pos.extend(v)
            self.nrm.extend(normal)
            self.uv.extend((u, 0.5))
            self.conf.append(conf)
        self.idx.extend((base, base + 1, base + 2))

    def box(self, x0, y0, z0, x1, y1, z1, part, conf, skip=()) -> None:
        """Axis-aligned box, counter-clockwise wound, outward normals."""
        faces = {
            "px": ([(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)], (1, 0, 0)),
            "nx": ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], (-1, 0, 0)),
            "py": ([(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)], (0, 1, 0)),
            "ny": ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),
            "pz": ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1)),
            "nz": ([(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)], (0, 0, -1)),
        }
        for name, (verts, normal) in faces.items():
            if name in skip:
                continue
            self.quad(*verts, normal, part, conf)


def norm(v):
    m = sum(c * c for c in v) ** 0.5
    return tuple(c / m for c in v)


def build_mesh(phase: dict, conf: dict[str, tuple[str, float]]) -> tuple[Mesh, dict]:
    """The massing, straight out of the record's own numbers."""
    fp = phase["footprint"]["polygon"]
    xs = [p[0] for p in fp]
    ys = [p[1] for p in fp]
    width = max(xs) - min(xs)        # metres east-west
    depth = max(ys) - min(ys)        # metres north-south
    wall_h = phase["form"]["wall_height_m"]["value"]
    stories = phase["form"]["stories"]["value"]
    pitch_deg = phase["form"]["roof_pitch_deg"]["value"]
    has_wing = bool(phase["form"]["log_wing"]["value"])
    has_cross = bool(phase["form"]["cross_wing"]["value"])
    cross_end = phase["form"]["cross_wing_end"]["value"]
    cross_depth = phase["form"]["cross_wing_depth_m"]["value"]

    # The contract says the mesh is authored about "its own local origin, at
    # ground level". It does not say WHERE in plan that origin sits. This
    # placeholder puts it at the footprint centroid, which is the only choice
    # that survives a change of rotation without also moving the building.
    hx, hz = width / 2.0, depth / 2.0

    m = Mesh()
    c_walls = conf["walls"][1]
    c_roof = conf["roof"][1]
    c_wing = conf["log_wing"][1]
    c_shut = conf["shutters"][1]

    # main block — walls
    m.box(-hx, 0.0, -hz, hx, wall_h, hz, "walls", c_walls, skip=("py",))

    # Gable roof, ridge running east-west, spanning the block's DEPTH. The rise
    # is no longer a round number picked here: it falls out of the record's own
    # roof_pitch_deg over the half-span, which is what lets the cross wing below
    # stand at one ridge height with this block instead of merely near it.
    rise = hz * math.tan(math.radians(pitch_deg))
    ridge_y = wall_h + rise
    a = (-hx, wall_h, hz)
    b = (hx, wall_h, hz)
    c = (hx, ridge_y, 0.0)
    d = (-hx, ridge_y, 0.0)
    m.quad(a, b, c, d, norm((0, hz, rise)), "roof", c_roof)
    e = (hx, wall_h, -hz)
    f = (-hx, wall_h, -hz)
    g = (-hx, ridge_y, 0.0)
    h = (hx, ridge_y, 0.0)
    m.quad(e, f, g, h, norm((0, hz, -rise)), "roof", c_roof)
    m.tri((hx, wall_h, hz), (hx, wall_h, -hz), (hx, ridge_y, 0.0), (1, 0, 0), "roof", c_roof)
    m.tri((-hx, wall_h, -hz), (-hx, wall_h, hz), (-hx, ridge_y, 0.0), (-1, 0, 0), "roof", c_roof)

    # the attached log wing — inferred from the two retrospective depictions
    wing = None
    if has_wing:
        ww, wd, wh = 5.0, 4.0, 2.6
        wing = (-hx - ww, 0.0, hz - wd, -hx, wh, hz)
        m.box(*wing, "log_wing", c_wing, skip=("px",))
        # shallow shed roof over the wing
        m.quad((-hx - ww, wh, hz), (-hx, wh, hz), (-hx, wh + 0.6, hz - wd),
               (-hx - ww, wh + 0.6, hz - wd), norm((0, wd, 0.6)), "log_wing", c_wing)

    # shutters — the one documented visual feature, in pairs beside each opening
    sw, sh, sd = 0.42, 1.25, 0.07
    per_storey = 4
    storey_h = wall_h / max(stories, 1)
    n_shutters = 0
    for storey in range(stories):
        sy = storey * storey_h + storey_h * 0.30
        for i in range(per_storey):
            cx = -hx + width * (i + 0.5) / per_storey
            for side, zface, zsign in (("s", hz, 1.0), ("n", -hz, -1.0)):
                if side == "n" and i in (1, 2):
                    continue          # fewer openings on the back elevation
                for off in (-0.72, 0.72):
                    x0 = cx + off - sw / 2
                    z0 = min(zface, zface + sd * zsign)
                    z1 = max(zface, zface + sd * zsign)
                    m.box(x0, sy, z0, x0 + sw, sy + sh, z1, "shutters", c_shut)
                    n_shutters += 1

    # THE CROSS WING — the second two-storey mass, and the only part of this
    # massing graded `reconstructed`.
    #
    # The record carries it as three rows and they do not agree in confidence:
    # `cross_wing` is inferred off Braunhold's plate (two ridges meeting at one
    # apex, proved by arithmetic in tools/sauganash_apex_lines.py), `cross_wing_end`
    # is inferred by elimination off the plat, and `cross_wing_depth_m` is
    # INVENTED within a bound — docs/LIBERTIES.md L217 owns it. Least confident
    # wins, so the whole mass renders at 1.0, and that is the third level this
    # fixture exists to give the confidence view something to hide.
    #
    # Two gable ridges of one wall height and one pitch meet at a point only when
    # they span the same width, so the wing's span is this block's own depth; it
    # runs BACK from the rear elevation by the record's depth. It is painted out
    # of the same texels as the block — the paint row covers the structure, and
    # colour is not confidence; the channel carries that.
    cross = None
    if has_cross:
        half = hz                                   # the shared-apex span, halved
        if cross_end == "x_max":
            cx0, cx1 = hx - depth, hx
        elif cross_end == "x_min":
            cx0, cx1 = -hx, -hx + depth
        else:
            raise SystemExit(
                f"cross_wing_end is {cross_end!r}; the placeholder knows x_max and "
                f"x_min and refuses to guess an end.")
        cxr = (cx0 + cx1) / 2.0
        cz0, cz1 = -hz - cross_depth, -hz        # back is -Z, as the shutters read it
        c_cross = conf["cross_wing"][1]

        # walls: open where it meets the block, open at the top under its roof
        m.box(cx0, 0.0, cz0, cx1, wall_h, cz1, "walls", c_cross, skip=("pz", "py"))

        # roof: two slopes along the wing's own ridge, plus the rear gable. The
        # front gable is omitted — that end is inside the main block.
        m.quad((cx1, wall_h, cz1), (cx1, wall_h, cz0), (cxr, ridge_y, cz0),
               (cxr, ridge_y, cz1), norm((rise, half, 0)), "roof", c_cross)
        m.quad((cx0, wall_h, cz0), (cx0, wall_h, cz1), (cxr, ridge_y, cz1),
               (cxr, ridge_y, cz0), norm((-rise, half, 0)), "roof", c_cross)
        m.tri((cx1, wall_h, cz0), (cx0, wall_h, cz0), (cxr, ridge_y, cz0),
              (0, 0, -1), "roof", c_cross)
        cross = (cx0, cz0, cx1, cz1)

    stats = {
        "width_m": width, "depth_m": depth, "wall_height_m": wall_h,
        "stories": stories, "roof_pitch_deg": pitch_deg, "ridge_height_m": ridge_y,
        "log_wing": has_wing,
        "cross_wing": None if cross is None else {
            "end": cross_end, "span_m": depth, "depth_m": cross_depth,
            "ridge_height_m": ridge_y,
        },
        "shutter_leaves": n_shutters,
        "vertices": len(m.pos) // 3, "triangles": len(m.idx) // 3,
    }
    return m, stats


# --------------------------------------------------------------------------- #
# a 4x1 RGBA palette PNG, written by hand (zlib is stdlib, PIL is not)
# --------------------------------------------------------------------------- #

def png_palette() -> bytes:
    w, h = len(PALETTE), 1
    raw = bytearray()
    for _y in range(h):
        raw.append(0)                                   # filter type 0
        for hexrgb, _name, _note in PALETTE:
            r = int(hexrgb[1:3], 16)
            g = int(hexrgb[3:5], 16)
            b = int(hexrgb[5:7], 16)
            raw.extend((r, g, b, 255))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)  # 8-bit RGBA
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


# --------------------------------------------------------------------------- #
# glTF / GLB writing
# --------------------------------------------------------------------------- #

def pad4(b: bytes, fill: bytes = b"\x00") -> bytes:
    return b + fill * ((4 - len(b) % 4) % 4)


def build_glb(mesh: Mesh, conf: dict, stats: dict) -> bytes:
    blobs: list[bytes] = []
    views: list[dict] = []
    accessors: list[dict] = []

    def add_view(data: bytes, target: int | None = None) -> int:
        offset = sum(len(pad4(b)) for b in blobs)
        blobs.append(data)
        view = {"buffer": 0, "byteOffset": offset, "byteLength": len(data)}
        if target is not None:
            view["target"] = target
        views.append(view)
        return len(views) - 1

    def add_accessor(values, comps: int, ctype: int, kind: str,
                     target: int, minmax: bool) -> int:
        fmt = {5126: "<f", 5123: "<H"}[ctype]
        data = b"".join(struct.pack(fmt, v) for v in values)
        acc = {
            "bufferView": add_view(data, target),
            "componentType": ctype,
            "count": len(values) // comps,
            "type": kind,
        }
        if minmax:
            mins = [min(values[i::comps]) for i in range(comps)]
            maxs = [max(values[i::comps]) for i in range(comps)]
            acc["min"], acc["max"] = mins, maxs
        acc["_"] = None
        del acc["_"]
        accessors.append(acc)
        return len(accessors) - 1

    ARRAY, ELEMENT = 34962, 34963
    a_pos = add_accessor(mesh.pos, 3, 5126, "VEC3", ARRAY, True)
    a_nrm = add_accessor(mesh.nrm, 3, 5126, "VEC3", ARRAY, False)
    a_uv = add_accessor(mesh.uv, 2, 5126, "VEC2", ARRAY, False)
    # THE confidence channel. SCALAR float — never a colour, never a multiplier.
    a_conf = add_accessor(mesh.conf, 1, 5126, "SCALAR", ARRAY, True)
    if max(mesh.idx) > 65534:
        raise SystemExit("placeholder outgrew 16-bit indices; widen to 5125")
    a_idx = add_accessor(mesh.idx, 1, 5123, "SCALAR", ELEMENT, False)
    v_img = add_view(png_palette())

    levels = sorted({round(v, 3) for v in mesh.conf})
    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "4D Chicago generators/placeholder.py (pure Python, no Blender)",
            "extras": {
                "placeholder": True,
                "why": "Stand-in so the renderer can be built against docs/GLB-CONTRACT.md "
                       "before the Blender bake lands. Box-ish massing, not architecture.",
                "dimensions_from": "data/structures/sauganash_hotel.json (phase frame_1831)",
                "confidence_levels_present": levels,
                "confidence_by_part": {k: {"level": v[0], "value": v[1]}
                                       for k, v in conf.items()},
                "palette_note": "Only the white walls and the bright-blue shutters are "
                                "attested colours (Wau-Bun 1856). The log-wing and roof "
                                "colours are placeholders and attest to nothing.",
            },
        },
        "scene": 0,
        "scenes": [{"name": "1835", "nodes": [0]}],
        "nodes": [{
            "name": f"{STRUCTURE_ID}__{PHASE_ID}",
            "mesh": 0,
            # Identity, per the contract. The renderer resolves picks through
            # extras.structure_id, never by parsing the name — and it places the
            # node from the sidecar, so no world transform is baked here.
            "extras": {
                "structure_id": STRUCTURE_ID,
                "phase_id": PHASE_ID,
                "scene_ids": SCENE_IDS,
            },
        }],
        "meshes": [{
            "name": f"{STRUCTURE_ID}__{PHASE_ID}",
            "primitives": [{
                "attributes": {
                    "POSITION": a_pos,
                    "NORMAL": a_nrm,
                    "TEXCOORD_0": a_uv,
                    "_CONFIDENCE": a_conf,
                },
                "indices": a_idx,
                "material": 0,
                "mode": 4,
            }],
        }],
        "materials": [{
            "name": "structures_shared",
            "doubleSided": False,
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0, "texCoord": 0},
                "metallicFactor": 0.0,
                "roughnessFactor": 0.85,
            },
        }],
        "textures": [{"sampler": 0, "source": 0}],
        # NEAREST both ways: a palette atlas must not bleed between texels.
        "samplers": [{"magFilter": 9728, "minFilter": 9728,
                      "wrapS": 33071, "wrapT": 33071}],
        "images": [{"bufferView": v_img, "mimeType": "image/png",
                    "name": "structures_palette"}],
        "bufferViews": views,
        "accessors": accessors,
        "buffers": [{"byteLength": sum(len(pad4(b)) for b in blobs)}],
    }

    bin_chunk = b"".join(pad4(b) for b in blobs)
    json_chunk = pad4(json.dumps(gltf, separators=(",", ":")).encode("utf-8"), b" ")
    total = 12 + 8 + len(json_chunk) + 8 + len(bin_chunk)
    out = bytearray()
    out += b"glTF" + struct.pack("<II", 2, total)
    out += struct.pack("<I", len(json_chunk)) + b"JSON" + json_chunk
    out += struct.pack("<I", len(bin_chunk)) + b"BIN\x00" + bin_chunk
    return bytes(out), gltf


# --------------------------------------------------------------------------- #
# sidecar cross-check — the placeholder and the sidecar must not drift
# --------------------------------------------------------------------------- #

def verify_sidecar(structure: dict, phase: dict) -> list[str]:
    if not SIDECAR.exists():
        return [f"sidecar not present at {SIDECAR.relative_to(ROOT)} (skipped)"]
    side = json.loads(SIDECAR.read_text())
    problems = []
    if side.get("id") != structure["id"]:
        problems.append(f"sidecar id '{side.get('id')}' != record id '{structure['id']}'")
    if side.get("phase") != PHASE_ID:
        problems.append(f"sidecar phase '{side.get('phase')}' != '{PHASE_ID}'")
    form = phase.get("form", {})
    for name, attr in side.get("attributes", {}).items():
        if name not in form:
            continue
        if attr.get("confidence") != form[name].get("confidence"):
            problems.append(
                f"attribute '{name}': sidecar says {attr.get('confidence')}, "
                f"record says {form[name].get('confidence')}")
        if attr.get("value") != form[name].get("value"):
            problems.append(
                f"attribute '{name}': sidecar value {attr.get('value')!r} != "
                f"record value {form[name].get('value')!r}")
    for name in form:
        if name not in side.get("attributes", {}):
            problems.append(f"attribute '{name}' present in the record, missing from the sidecar")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="build in memory, write nothing")
    ap.add_argument("--stdout-json", action="store_true", help="dump the glTF JSON chunk")
    ap.add_argument("-o", "--out", type=Path, default=OUT)
    args = ap.parse_args()

    structure, phase = load_phase()
    conf = part_confidence(phase)
    mesh, stats = build_mesh(phase, conf)
    glb, gltf = build_glb(mesh, conf, stats)

    if args.stdout_json:
        print(json.dumps(gltf, indent=2))
        return 0

    # The fixture's one job. `renderers/web/js/confidence.js` reads the channel
    # back through levelOf() — >= 0.75 reconstructed, >= 0.25 inferred, else
    # attested — so it is not enough for three distinct numbers to be present:
    # each has to land in the band the view will read it as, on real vertices.
    # Checked here rather than asserted in a comment, because this asset exists
    # for no other reason (T-1112).
    present = sorted({round(v, 3) for v in mesh.conf})
    if present != [0.0, 0.5, 1.0]:
        print(f"FAIL  _CONFIDENCE carries {present}, not all three levels — "
              f"the confidence view would not be testable against this asset")
        return 1
    bands = {"attested": 0, "inferred": 0, "reconstructed": 0}
    for v in mesh.conf:
        bands["reconstructed" if v >= 0.75 else "inferred" if v >= 0.25 else "attested"] += 1
    missing = [lvl for lvl, n in bands.items() if n == 0]
    if missing:
        print(f"FAIL  no vertex reads back as {', '.join(missing)} through "
              f"confidence.js levelOf() — the view's rendering of that level has "
              f"no fixture behind it")
        return 1

    print(f"Sauganash Hotel, phase {PHASE_ID} — placeholder massing")
    print(f"  {stats['width_m']:.0f} x {stats['depth_m']:.0f} m footprint, "
          f"{stats['wall_height_m']} m walls, {stats['stories']} stories, "
          f"ridge {stats['ridge_height_m']:.1f} m")
    print(f"  {stats['vertices']} vertices, {stats['triangles']} triangles, "
          f"{stats['shutter_leaves']} shutter leaves, "
          f"log wing {'attached' if stats['log_wing'] else 'absent'}")
    cw = stats["cross_wing"]
    if cw:
        print(f"  cross wing at {cw['end']}: {cw['span_m']:.0f} m span x "
              f"{cw['depth_m']:.0f} m back, ridge {cw['ridge_height_m']:.1f} m — "
              f"one apex height with the block")
    print("  _CONFIDENCE as confidence.js levelOf() reads it back:")
    for level in ("attested", "inferred", "reconstructed"):
        print(f"    {level:<14} {bands[level]:>4} vertices")
    print("  _CONFIDENCE by part (worst driving attribute wins):")
    for part, (level, value) in sorted(conf.items()):
        drivers = ", ".join(PART_DRIVERS[part])
        print(f"    {part:<10} {value:<4} {level:<12} from: {drivers}")

    problems = verify_sidecar(structure, phase)
    if problems:
        print("  sidecar cross-check:")
        for p in problems:
            print(f"    {p}")
    else:
        print(f"  sidecar cross-check: {SIDECAR.relative_to(ROOT)} agrees with the record")

    if args.check:
        print(f"\n--check: {len(glb)} bytes, not written")
        return 1 if problems and SIDECAR.exists() else 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(glb)
    print(f"\nwrote {args.out.relative_to(ROOT)}  ({len(glb)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
