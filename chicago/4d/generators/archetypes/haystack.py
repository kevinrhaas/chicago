"""haystack — one round stack of hay, pitched by hand round a stack pole.

See `haystack_params` for the evidence, the form and every dimension. This module builds
the stack and writes its glTF itself, in pure Python, with no Blender (the K12/K16 route,
T-2266): `generators/haystack_emit.py` calls `glb()` for each record and
`generators/mesh_inputs.py` hashes this file and that one, and nothing else, into the
asset's freshness record. That is why the archetype is not in `generators/emit.py`: every
Blender-built mesh hashes emit.py's bytes, so registering a new archetype there re-stales
the whole town (722 assets on 2026-10-15, `tools/measure_generator_half.py`).

The stack is a surface of revolution of the params' half-section, centred in the
footprint square, with its girth made a little irregular and its pole leaning a little,
both from fixed functions of the segment so that two builds make the same bytes. Faces
are flat-shaded, as the Blender exports of the other archetypes are.

## No figure, no animal

docs/LIBERTIES.md L1 binds every vertex here, and the cattle Wau-Bun puts among the
stacks are not drawn either: what stands at Lee's Place is the hay.
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import materials  # noqa: E402
from archetypes.haystack_params import POLE_ABOVE_M, POLE_SIDE_M, HaystackParams  # noqa: E402

GENERATOR = "chicago-4d generators/archetypes/haystack.py (T-2510)"

M_BODY, M_TOP, M_POLE = 0, 1, 2

# Hay in the stack. A new stack is the pale gold-green of hay cured in the swath; the
# outside of a stack that has stood a winter greys and darkens, and the top, raked to
# shed the rain, goes first in either. Chosen against the camps' canvas (whose 0.65
# tone-mapped to white in the lit browser) and the prairie cover, so a stack reads as
# hay beside the grass and never as a pale cone: the first values here (0.50, 0.445,
# 0.25 for new hay) came out a grey beige at Lee's Place in the lit browser, and the
# winter's stack could hardly be told from the summer's.
HAY_RGBA = {
    "new": {"body": (0.540, 0.430, 0.170, 1.0), "top": (0.400, 0.330, 0.160, 1.0)},
    "weathered": {"body": (0.380, 0.330, 0.220, 1.0), "top": (0.270, 0.240, 0.170, 1.0)},
}
# The stack pole: a peeled sapling, greyed.
POLE_RGBA = (0.330, 0.290, 0.230, 1.0)

SEGMENTS = 18


def _jitter(i: int, k: int = 0) -> float:
    """A fixed value in [-1, 1] for segment `i`, channel `k`. Deterministic."""
    x = math.sin((i + 1) * 12.9898 + (k + 1) * 78.233) * 43758.5453
    return 2.0 * (x - math.floor(x)) - 1.0


class _Mesh:
    """Polygons in the archetype's frame (x east, y north, z up at rotation 0), each with
    its material and confidence. Fanned into triangles when written."""

    def __init__(self):
        self.polys: list[tuple[list, int, float]] = []

    def add_poly(self, pts, conf: float, mat: int) -> None:
        self.polys.append(([tuple(float(c) for c in p) for p in pts], mat, float(conf)))


def mesh(params: HaystackParams) -> _Mesh:
    """The stack's polygons, its foot's centre at the middle of the footprint square."""
    params.validate()
    b = _Mesh()
    conf = params.worst_conf("diameter_m", "height_m", "condition")
    pole_conf = params.worst_conf("stack_pole")
    cx = cy = params.side_m / 2.0
    prof = params.profile()
    n = SEGMENTS
    # Each column of the stack bulges or settles by up to 4 % of its radius, so the
    # girth is a hand-built one and not a lathe's; the peak stays on the axis.
    wob = [1.0 + 0.04 * _jitter(i, 1) for i in range(n)]
    ang = [2.0 * math.pi * i / n for i in range(n)]
    rings = []
    for r, z in prof[:-1]:
        rings.append([(cx + r * wob[i] * math.cos(ang[i]), cy + r * wob[i] * math.sin(ang[i]), z)
                      for i in range(n)])
    shoulder = 3  # the profile's shoulder pair: the top's material starts above it
    for j in range(len(rings) - 1):
        mat = M_BODY if j < shoulder else M_TOP
        lo, hi = rings[j], rings[j + 1]
        for i in range(n):
            k = (i + 1) % n
            b.add_poly([lo[i], lo[k], hi[k], hi[i]], conf, mat)
    peak = (cx, cy, prof[-1][1])
    last = rings[-1]
    for i in range(n):
        b.add_poly([last[i], last[(i + 1) % n], peak], conf, M_TOP)
    # The foot is closed so the stack is a solid from below (a walker on the bank
    # looks down at no stack's hollow).
    b.add_poly([rings[0][i] for i in reversed(range(n))], conf, M_BODY)

    if params.stack_pole:
        # The pole the stack was built round, standing clear of the peak and leaning a
        # little; it starts inside the top so no gap shows where it leaves the hay.
        h = POLE_SIDE_M / 2.0
        lean = 0.06
        z0, z1 = prof[-1][1] - 0.6, prof[-1][1] + POLE_ABOVE_M
        x1, y1 = cx + lean, cy + 0.5 * lean
        quad = [(-h, -h), (h, -h), (h, h), (-h, h)]
        for i in range(4):
            (ax, ay), (bx, by) = quad[i], quad[(i + 1) % 4]
            b.add_poly([(cx + ax, cy + ay, z0), (cx + bx, cy + by, z0),
                        (x1 + bx, y1 + by, z1), (x1 + ax, y1 + ay, z1)], pole_conf, M_POLE)
        b.add_poly([(x1 + x, y1 + y, z1) for x, y in quad], pole_conf, M_POLE)
    return b


def material_specs(params: HaystackParams) -> list[tuple[str, tuple, float]]:
    hay = HAY_RGBA[params.condition]
    wood_r = materials.SUBSTRATES["hewn_log"].roughness
    return [("hay", hay["body"], 0.98), ("hay_top", hay["top"], 0.98),
            ("stack_pole", POLE_RGBA, wood_r)]


def _pad(blob: bytes, fill: bytes = b"\x00") -> bytes:
    return blob + fill * ((4 - len(blob) % 4) % 4)


def _unit_normal(pts) -> tuple:
    """Newell's normal of a planar-ish polygon, in the archetype's z-up frame."""
    nx = ny = nz = 0.0
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        nx += (p[1] - q[1]) * (p[2] + q[2])
        ny += (p[2] - q[2]) * (p[0] + q[0])
        nz += (p[0] - q[0]) * (p[1] + q[1])
    m = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / m, ny / m, nz / m)


def glb(params: HaystackParams, structure_id: str, phase_id: str) -> bytes:
    """The structure's GLB. glTF is y-up: the archetype's (x, y, z) is written as
    (x, z, -y), a rotation, so no face turns inside out (docs/GLB-CONTRACT.md)."""
    m = mesh(params)
    specs = material_specs(params)
    to_gl = lambda p: (round(p[0], 5), round(p[2], 5), round(-p[1], 5))  # noqa: E731
    bin_ = bytearray()
    views, accessors, prims = [], [], []

    def view(blob: bytes, target: int) -> int:
        nonlocal bin_
        off = len(bin_)
        bin_ += _pad(blob)
        views.append({"buffer": 0, "byteOffset": off, "byteLength": len(blob), "target": target})
        return len(views) - 1

    def accessor(values, ctype, typ, comps, target, minmax=False) -> int:
        flat = [x for v in values for x in (v if comps > 1 else (v,))]
        fmt = {5126: "f", 5123: "H", 5125: "I"}[ctype]
        acc = {"bufferView": view(struct.pack(f"<{len(flat)}{fmt}", *flat), target),
               "componentType": ctype, "count": len(values), "type": typ}
        if minmax:
            acc["min"] = [struct.unpack("<f", struct.pack("<f", min(v[k] for v in values)))[0]
                          for k in range(comps)]
            acc["max"] = [struct.unpack("<f", struct.pack("<f", max(v[k] for v in values)))[0]
                          for k in range(comps)]
        accessors.append(acc)
        return len(accessors) - 1

    for mi in range(len(specs)):
        pos, nrm, uv, conf, idx = [], [], [], [], []
        for pts, mat, c in m.polys:
            if mat != mi:
                continue
            nz = _unit_normal(pts)
            ngl = (round(nz[0], 4), round(nz[2], 4), round(-nz[1], 4))
            base = len(pos)
            for p in pts:
                pos.append(to_gl(p))
                nrm.append(ngl)
                # A cylindrical map: round the stack, and up it.
                a = math.atan2(p[1] - params.side_m / 2.0, p[0] - params.side_m / 2.0)
                uv.append((round(a / (2.0 * math.pi) + 0.5, 4), round(p[2] / params.height_m, 4)))
                conf.append(c)
            for k in range(1, len(pts) - 1):
                idx += [base, base + k, base + k + 1]
        if not idx:
            continue
        prims.append({"attributes": {
            "POSITION": accessor(pos, 5126, "VEC3", 3, 34962, True),
            "NORMAL": accessor(nrm, 5126, "VEC3", 3, 34962),
            "TEXCOORD_0": accessor(uv, 5126, "VEC2", 2, 34962),
            "_CONFIDENCE": accessor(conf, 5126, "SCALAR", 1, 34962)},
            "indices": accessor(idx, 5123 if len(pos) < 65536 else 5125, "SCALAR", 1, 34963),
            "material": mi})
    name = f"{structure_id}__{phase_id}"
    gltf = {
        "asset": {"version": "2.0", "generator": GENERATOR},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": name, "mesh": 0,
                   "extras": {"structure_id": structure_id, "phase_id": phase_id}}],
        "meshes": [{"name": name, "primitives": prims}],
        "materials": [{"name": n, "doubleSided": True, "pbrMetallicRoughness": {
            "baseColorFactor": [round(x, 4) for x in rgba], "metallicFactor": 0.0,
            "roughnessFactor": round(r, 4)}} for n, rgba, r in specs],
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(bin_)}],
    }
    js = _pad(json.dumps(gltf, separators=(",", ":"), sort_keys=True).encode(), b" ")
    body = bytes(bin_)
    total = 12 + 8 + len(js) + 8 + len(body)
    return (struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<I4s", len(js), b"JSON") + js
            + struct.pack("<I4s", len(body), b"BIN\x00") + body)
