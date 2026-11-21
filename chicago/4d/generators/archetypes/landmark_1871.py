"""landmark_1871 — the pre-fire city's masonry landmarks, in pure Python (T-3688).

See `landmark_1871_params` for the composition a record carries. Like the K12, K16,
haystack and monument archetypes this module writes its glTF itself with no Blender, and
`generators/landmark_1871_emit.py` calls `glb()` for each record; `mesh_inputs` hashes this
file, the emitter and the params module into each asset's freshness record.

## What it reuses from 1904

The materials are the 1904 kits', so the landmarks wear the same stone, brick, slate and
tin as Prairie Avenue's K01 houses: the K02 stone library's Lemont limestone (the "Athens
marble" Chicago quarried at Lemont and Joliet, of which the Sherman House, the Court House
wings and the Chamber of Commerce were built) and its dressed trim; the K03 brick panels;
the K04 Vermont slate and painted standing-seam tin. The elements are the K01 kit's in
kind, cut to a public building's scale: K06's sash and glass in deep reveals, K09's
window heads (a cornice hood, a moulded arch with its keystone, a pediment), K10's
bracketed cornice swept round the whole block, K02's rusticated base and long-and-short
quoins, K05's mansard with its curb and dormers. They are rebuilt here rather than called,
because the K01 contract's ranges are a house's (a principal floor of 0.8-1.8 m, a front of
a few bays) and widening them would re-stale every Prairie Avenue house.

## The fire's hook

Every material carries a role in the node's `extras.fire.roles` — `roof` (slate, tin,
domes, cupolas: what burns and falls), `glazing` (glass and sash: what breaks), `walls`
(the masonry that stood afterwards), `trim` and `iron` — so the fire renderer (T-3687) can
hide what fell, char what stood and leave the shell, without a second mesh. A record's
`fire` block (inside `form.composition`) says which shell this building left — its `fate`,
what was `left` standing and the `time` — and lands in `extras.fire.shell`.
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from archetypes.landmark_1871_params import LandmarkParams  # noqa: E402


def _seqsum(xs):
    """Add left to right, one term at a time: 3.11's `sum()` spelled out, so the bytes
    agree on every CPython (T-2363; prairie_draft._seqsum). Never call the built-in
    `sum()` in this module: `tools/check_exact_sums.py` counts them."""
    total = 0
    for x in xs:
        total = total + x
    return total

GENERATOR = "chicago-4d generators/archetypes/landmark_1871.py (T-3688)"
ROOT = Path(__file__).resolve().parents[2]
STONE = ROOT / "assets" / "textures" / "prairie_1904_stone"   # K02
ROOFS = ROOT / "assets" / "textures" / "prairie_1904_roofs"   # K04
T1835 = ROOT / "assets" / "textures" / "chicago_1835_pbr"     # the 1835 town's wood (T-3689)
#: the 1835 maps are 1024 px PNG masters; a landmark embeds them at this size, as JPEG
K1835_PX = 256
BRICK = ROOT / "assets" / "textures" / "prairie_1904_brick"   # K03

CONF = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

#: name -> (library, fabric or None, linear colour, roughness, fire role, extra)
MATERIALS = {
    "stone_wall": ("k02", "limestone_lemont", (1.0, 1.0, 1.0), 0.88, "walls", {}),
    "marble_wall": ("k02", "limestone_bedford", (1.0, 1.0, 1.0), 0.84, "walls", {}),
    # stone darkened by a decade or more of soft-coal smoke, as the 1860s photographs show it
    "stone_weathered": ("k02", "limestone_lemont", (0.58, 0.56, 0.52), 0.9, "walls", {}),
    "brick_wall": ("k03", "pressed_red_running", (1.0, 1.0, 1.0), 0.9, "walls", {}),
    "brick_cream": ("k03", "common_buff_common_6", (1.0, 0.97, 0.86), 0.9, "walls", {}),
    "stone_trim": ("k02", "dressed_trim", (1.0, 1.0, 1.0), 0.86, "trim", {}),
    "iron_stone": (None, None, (0.62, 0.58, 0.50), 0.62, "iron", {}),
    "joint": (None, None, (0.20, 0.19, 0.17), 0.95, "walls", {}),
    "slate": ("k04", "slate_vermont", (1.0, 1.0, 1.0), 0.62, "roof", {}),
    "tin": ("k04", "tin_standing_seam_painted", (1.0, 1.0, 1.0), 0.6, "roof", {}),
    "tin_dark": (None, None, (0.07, 0.075, 0.07), 0.55, "roof", {}),
    "glass": (None, None, (0.05, 0.065, 0.075), 0.04, "glazing", {"alpha": 0.42}),
    "sash": (None, None, (0.16, 0.12, 0.08), 0.6, "glazing", {}),
    "backing": (None, None, (0.018, 0.017, 0.016), 1.0, "glazing", {}),
    "door": (None, None, (0.24, 0.14, 0.07), 0.55, "glazing", {}),
    "iron": (None, None, (0.05, 0.05, 0.055), 0.55, "iron", {}),
    "clock": (None, None, (0.80, 0.78, 0.72), 0.5, "roof", {}),
    "awning": (None, None, (0.62, 0.57, 0.46), 0.95, "roof", {}),
    # T-3689: the frame city, in the 1835 town's own wood (textures/chicago_1835_pbr):
    # white-lead clapboard (painted, a record's `tint` gives its colour), the same boards
    # unpainted and weathered, sawn boards for barns and sheds, and weathered shingles
    "clapboard": ("k1835", "walls/clapboard_white_lead_paint", (1.0, 1.0, 1.0), 0.7, "walls", {}),
    "clapboard_bare": ("k1835", "walls/clapboard_weathered_oak", (1.0, 1.0, 1.0), 0.86, "walls", {}),
    "boards": ("k1835", "walls/vertical_sawn_board", (1.0, 1.0, 1.0), 0.88, "walls", {}),
    "shingle": ("k1835", "roofs/wood_shingles_weathered", (1.0, 1.0, 1.0), 0.85, "roof", {}),
    "wood_trim": (None, None, (0.40, 0.37, 0.32), 0.8, "trim", {}),
    "wood_white": (None, None, (0.80, 0.79, 0.74), 0.7, "trim", {}),
    # the old City Cemetery's grass-grown grave mounds (T-3689): sod, a flat colour
    "sod": (None, None, (0.11, 0.15, 0.05), 0.97, "walls", {}),
    # and the lake shore's sand, the 1835 kit's own dune sand
    "sand": ("k1835", "ground/lake_michigan_dune_sand", (1.0, 1.0, 1.0), 0.95, "walls", {}),
}
ROLE_OF = {k: v[4] for k, v in MATERIALS.items()}
WALL_MAT = {"marble": "marble_wall", "lockport_marble": "marble_wall", "limestone": "stone_wall",
            "lockport_weathered": "stone_weathered", "limestone_pale": "marble_wall",
            "brick_red": "brick_wall", "brick_cream": "brick_cream", "iron_stone": "iron_stone",
            "clapboard": "clapboard", "clapboard_bare": "clapboard_bare", "boards": "boards",
            "sod": "sod", "sand": "sand"}


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(v):
    m = math.sqrt(_dot(v, v)) or 1.0
    return (v[0] / m, v[1] / m, v[2] / m)


def _tile(mat: str) -> tuple:
    lib, fab = MATERIALS[mat][0], MATERIALS[mat][1]
    if lib == "k02":
        return tuple(json.loads((STONE / fab / "material.json").read_text())["tile_m"])
    if lib == "k04":
        return tuple(json.loads((ROOFS / fab / "material.json").read_text())["tile_m"])
    if lib == "k03":
        return tuple(json.loads((BRICK / "panel" / fab / "material.json").read_text())["tile_m"])
    if lib == "k1835":
        span = json.loads((T1835 / fab / "material.json").read_text())["span_m"]
        return (span, span)
    return (1.0, 1.0)


def _images(mat: str) -> dict:
    lib, fab = MATERIALS[mat][0], MATERIALS[mat][1]
    if lib == "k02":
        m = json.loads((STONE / fab / "material.json").read_text())
        return {"basecolor": STONE / fab / m["web"]["basecolor"], "normal": STONE / fab / m["web"]["normal_gl"]}
    if lib == "k04":
        m = json.loads((ROOFS / fab / "material.json").read_text())
        return {"basecolor": ROOFS / fab / m["web"]["basecolor"], "normal": ROOFS / fab / m["web"]["normal_gl"]}
    if lib == "k03":
        m = json.loads((BRICK / "panel" / fab / "material.json").read_text())
        return {"basecolor": BRICK / "panel" / fab / m["web"]["basecolor"],
                "normal": BRICK / "panel" / fab / m["web"]["normal_gl"]}
    if lib == "k1835":
        stem = fab.split("/")[-1]
        return {"basecolor": T1835 / fab / f"{stem}_basecolor.png", "normal": T1835 / fab / f"{stem}_normal_gl.png"}
    return {}


def _image_bytes(src: Path) -> bytes:
    """A map's bytes as the GLB embeds them: the K02-K04 web JPEGs as they are, the 1835
    PNG masters scaled to K1835_PX and saved as JPEG (as city_context_emit does)."""
    if src.suffix == ".png":
        import io
        from PIL import Image
        im = Image.open(src).convert("RGB").resize((K1835_PX, K1835_PX), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=88, optimize=False)
        return buf.getvalue()
    return src.read_bytes()


def texture_files() -> list:
    """Every map a landmark may embed: mesh_inputs hashes them."""
    return sorted({p for m in MATERIALS for p in _images(m).values()})


class _Prim:
    def __init__(self, tile):
        self.tile = tile
        self.pos, self.nrm, self.uv, self.conf, self.idx = [], [], [], [], []


class Mesh:
    """Indexed, flat-shaded faces per material, with metric UVs (the K01 rule:
    TEXCOORD_0 = surface metres over the tile, image y up the wall)."""

    def __init__(self):
        self.prims = {}

    def _prim(self, mat):
        if mat not in self.prims:
            self.prims[mat] = _Prim(_tile(mat))
        return self.prims[mat]

    def face(self, mat, pts, conf, hint=None):
        """A planar convex polygon. Wound to face `hint` when given, else as passed."""
        n = (0.0, 0.0, 0.0)
        for i, a in enumerate(pts):
            b = pts[(i + 1) % len(pts)]
            n = _add(n, ((a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]),
                         (a[0] - b[0]) * (a[1] + b[1])))
        if _dot(n, n) < 1e-14:
            return
        n = _unit(n)
        if hint is not None and _dot(n, hint) < 0:
            pts = list(reversed(pts))
            n = _mul(n, -1)
        pr = self._prim(mat)
        tu, tv = pr.tile
        if abs(n[2]) > 0.95:
            t = (1.0, 0.0, 0.0)
        else:
            t = _unit((-n[1], n[0], 0.0))
        b = _cross(n, t)
        base = len(pr.pos)
        for p in pts:
            pr.pos.append(p)
            pr.nrm.append(n)
            pr.uv.append((_dot(p, t) / tu, -_dot(p, b) / tv))
            pr.conf.append(conf)
        for i in range(1, len(pts) - 1):
            pr.idx += [base, base + i, base + i + 1]

    def quad(self, mat, a, b, c, d, conf, hint=None):
        self.face(mat, [a, b, c, d], conf, hint)

    def box(self, mat, corners, conf, skip=()):
        """A convex hexahedron from its 8 corners: bottom 0-3, top 4-7, each ring the same way
        round. Faces wound outward from its centre; `skip` names faces left out
        ('bottom', 'top', 0..3 for the sides from corner i to i+1)."""
        c = _mul(corners[0], 0.0)
        for p in corners:
            c = _add(c, _mul(p, 1 / 8))
        faces = {"bottom": [corners[0], corners[1], corners[2], corners[3]],
                 "top": [corners[4], corners[5], corners[6], corners[7]]}
        for i in range(4):
            j = (i + 1) % 4
            faces[i] = [corners[i], corners[j], corners[j + 4], corners[i + 4]]
        for k, f in faces.items():
            if k in skip:
                continue
            fc = _mul(_add(_add(f[0], f[1]), _add(f[2], f[3])), 0.25)
            self.face(mat, f, conf, _sub(fc, c))

    def prism(self, mat, ring, z0, z1, conf, top=True, bottom=False, center=None):
        """A vertical prism over a convex ring of (x, y)."""
        n = len(ring)
        cx = _seqsum(p[0] for p in ring) / n
        cy = _seqsum(p[1] for p in ring) / n
        for i in range(n):
            a, b = ring[i], ring[(i + 1) % n]
            mid = ((a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cy, 0.0)
            self.quad(mat, (a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1), conf, mid)
        if top:
            self.face(mat, [(p[0], p[1], z1) for p in ring], conf, (0, 0, 1))
        if bottom:
            self.face(mat, [(p[0], p[1], z0) for p in ring], conf, (0, 0, -1))

    @property
    def triangles(self):
        return _seqsum(len(p.idx) // 3 for p in self.prims.values())


class Frame:
    """A wall's own frame: s along it (left to right seen from outside), z up, d outward."""

    def __init__(self, origin, tangent, normal):
        self.o, self.t, self.n = origin, tangent, normal

    def p(self, s, z, d=0.0):
        return (self.o[0] + self.t[0] * s + self.n[0] * d,
                self.o[1] + self.t[1] * s + self.n[1] * d, z)

    @property
    def out(self):
        return (self.n[0], self.n[1], 0.0)

    def fbox(self, m, mat, s0, s1, z0, z1, d0, d1, conf, skip=()):
        """A box in this frame: s0-s1 along, z0-z1 up, d0-d1 out (d1 > d0)."""
        cs = [self.p(s0, z0, d1), self.p(s1, z0, d1), self.p(s1, z0, d0), self.p(s0, z0, d0)]
        cs += [(q[0], q[1], z1) for q in cs]
        m.box(mat, cs, conf, skip)


def face_frame(box, face):
    x0, y0, x1, y1 = box
    if face == "S":
        return Frame((x0, y0), (1, 0), (0, -1)), x1 - x0
    if face == "N":
        return Frame((x1, y1), (-1, 0), (0, 1)), x1 - x0
    if face == "E":
        return Frame((x1, y0), (0, 1), (1, 0)), y1 - y0
    return Frame((x0, y1), (0, -1), (-1, 0)), y1 - y0


# --------------------------------------------------------------------------- openings


def _arc(o, a, b, zt):
    """The head of an opening a-b whose rectangle stops at zt: points left to right."""
    w = b - a
    kind = o["kind"]
    if kind in ("round", "pair_round", "door_round", "oculus"):
        r = w / 2
        n = 8
        return [((a + b) / 2 + r * math.cos(math.pi - math.pi * i / n), zt + r * math.sin(math.pi * i / n))
                for i in range(n + 1)]
    if kind == "segment":
        rise = o.get("rise", w * 0.15)
        R = (w * w / 4 + rise * rise) / (2 * rise)
        zc = zt + rise - R
        th = math.asin((w / 2) / R)
        n = 4
        return [((a + b) / 2 + R * math.sin(-th + 2 * th * i / n), zc + R * math.cos(-th + 2 * th * i / n))
                for i in range(n + 1)]
    if kind in ("pointed", "door_pointed"):
        # an equilateral Gothic head (T-3689): each side struck from the far springer
        n = 4
        left = [(b + w * math.cos(math.pi - (math.pi / 3) * i / n), zt + w * math.sin(math.pi - (math.pi / 3) * i / n))
                for i in range(n + 1)]
        right = [(a + w * math.cos(math.pi / 3 - (math.pi / 3) * i / n), zt + w * math.sin(math.pi / 3 - (math.pi / 3) * i / n))
                 for i in range(1, n + 1)]
        return left + right
    return [(a, zt), (b, zt)]


def _rise(o, w):
    k = o["kind"]
    if k in ("round", "pair_round", "door_round", "oculus"):
        return w / 2
    if k == "segment":
        return o.get("rise", w * 0.15)
    if k in ("pointed", "door_pointed"):
        return w * math.sqrt(3) / 2
    return 0.0


def wall(m: Mesh, fr: Frame, s0, s1, z0, z1, openings, mat, conf, course=None, rustic=False):
    """The wall s0-s1 x z0-z1 of frame `fr`, cut by `openings` — each a dict with s (centre),
    w, z (sill above z0... given absolute here as zs) and h and kind — then courses on its
    solid pieces. Openings must lie inside the band and not overlap."""
    ops = sorted(openings, key=lambda o: o["s"])
    out = fr.out
    pieces = []
    x = s0
    for o in ops:
        a, b = o["s"] - o["w"] / 2, o["s"] + o["w"] / 2
        zs, zh = o["zs"], o["zs"] + o["h"]
        zt = zh - _rise(o, o["w"])
        if a > x + 1e-6:
            pieces.append((x, a, z0, z1))
        if zs > z0 + 1e-6:
            pieces.append((a, b, z0, zs))
        if zh < z1 - 1e-6:
            pieces.append((a, b, zh, z1))
        arc = _arc(o, a, b, zt)
        if len(arc) > 2:
            mid = len(arc) // 2
            tl, tr = fr.p(a, zh), fr.p(b, zh)
            for i in range(mid):
                m.face(mat, [tl, fr.p(*arc[i]), fr.p(*arc[i + 1])], conf, out)
            for i in range(mid, len(arc) - 1):
                m.face(mat, [tr, fr.p(*arc[i]), fr.p(*arc[i + 1])], conf, out)
            m.face(mat, [tl, fr.p(*arc[mid]), tr], conf, out)
        x = b
    if s1 > x + 1e-6:
        pieces.append((x, s1, z0, z1))
    for (a, b, za, zb) in pieces:
        m.quad(mat, fr.p(a, za), fr.p(b, za), fr.p(b, zb), fr.p(a, zb), conf, out)
        if course:
            step = course
            z = math.floor(za / step) * step + step
            while z < zb - 0.02:
                th = 0.035 if rustic else 0.012
                m.quad("joint", fr.p(a, z - th / 2, 0.004), fr.p(b, z - th / 2, 0.004),
                       fr.p(b, z + th / 2, 0.004), fr.p(a, z + th / 2, 0.004), conf, out)
                z += step


def opening_fill(m: Mesh, fr: Frame, o, conf, trim="stone_trim"):
    """Reveal, glazing, sash, sill and head of one cut opening."""
    a, b = o["s"] - o["w"] / 2, o["s"] + o["w"] / 2
    zs, zh = o["zs"], o["zs"] + o["h"]
    zt = zh - _rise(o, o["w"])
    kind = o["kind"]
    depth = o.get("depth", 0.30)
    outline = [(a, zs), (b, zs)] + _arc(o, a, b, zt)[::-1][:-1] if False else None
    arc = _arc(o, a, b, zt)
    # outline anticlockwise seen from outside: a,zs -> b,zs -> up right side -> arc right to left
    ring = [(a, zs), (b, zs)] + list(reversed(arc))
    cx = (a + b) / 2
    cz = (zs + zh) / 2
    for i in range(len(ring)):
        p0, p1 = ring[i], ring[(i + 1) % len(ring)]
        if abs(p0[0] - p1[0]) < 1e-9 and abs(p0[1] - p1[1]) < 1e-9:
            continue
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        hint_s, hint_z = cx - mid[0], cz - mid[1]
        hint = (fr.t[0] * hint_s, fr.t[1] * hint_s, hint_z)
        m.quad(o.get("reveal", "stone_wall"), fr.p(p0[0], p0[1], 0), fr.p(p1[0], p1[1], 0),
               fr.p(p1[0], p1[1], -depth), fr.p(p0[0], p0[1], -depth), conf, hint)
    back = [fr.p(q[0], q[1], -depth) for q in ring]
    if kind.startswith("door"):
        m.face("door", back, conf, fr.out)
        # the leaves' meeting stile and panels' rails, read as dark lines
        m.quad("iron", fr.p(cx - 0.03, zs, -depth + 0.01), fr.p(cx + 0.03, zs, -depth + 0.01),
               fr.p(cx + 0.03, zt, -depth + 0.01), fr.p(cx - 0.03, zt, -depth + 0.01), conf, fr.out)
        if zh - zs > 3.2:   # a fanlight over the leaves
            m.quad("sash", fr.p(a, zt - 0.08, -depth + 0.02), fr.p(b, zt - 0.08, -depth + 0.02),
                   fr.p(b, zt, -depth + 0.02), fr.p(a, zt, -depth + 0.02), conf, fr.out)
    else:
        m.face("backing", [fr.p(q[0], q[1], -depth - o.get("back", 0.4)) for q in ring], conf, fr.out)
        m.face("glass", back, conf, fr.out)
        gd = -depth + 0.015
        bar = 0.05 if kind != "store" else 0.09
        bars = []
        if kind == "store":
            n = max(1, round((b - a) / 1.6))
            for k in range(1, n):
                bars.append(("v", a + (b - a) * k / n))
            bars.append(("h", zt - 0.55))
        else:
            if (b - a) > 0.75 or kind == "pair_round":
                bars.append(("v", cx))
            if kind != "oculus":
                bars.append(("h", zs + (zt - zs) * 0.52))
        mat = "iron" if kind == "store" else "sash"
        for k, v in bars:
            if k == "v":
                top = zh if kind in ("round", "pair_round", "segment", "oculus", "pointed") else zt
                m.quad(mat, fr.p(v - bar / 2, zs, gd), fr.p(v + bar / 2, zs, gd),
                       fr.p(v + bar / 2, top, gd), fr.p(v - bar / 2, top, gd), conf, fr.out)
            else:
                m.quad(mat, fr.p(a, v - bar / 2, gd), fr.p(b, v - bar / 2, gd),
                       fr.p(b, v + bar / 2, gd), fr.p(a, v + bar / 2, gd), conf, fr.out)
        if kind != "store":   # the frame round the sash, inside the reveal
            f = 0.07
            m.quad("sash", fr.p(a, zs, gd), fr.p(b, zs, gd), fr.p(b, zs + f, gd), fr.p(a, zs + f, gd), conf, fr.out)
            m.quad("sash", fr.p(a, zs, gd), fr.p(a + f, zs, gd), fr.p(a + f, zt, gd), fr.p(a, zt, gd), conf, fr.out)
            m.quad("sash", fr.p(b - f, zs, gd), fr.p(b, zs, gd), fr.p(b, zt, gd), fr.p(b - f, zt, gd), conf, fr.out)
    # sill
    if kind not in ("store", "door_round", "door_flat", "door_pointed", "oculus"):
        fr.fbox(m, trim, a - 0.1, b + 0.1, zs - 0.12, zs, -0.02, 0.09, conf, skip=("bottom",))
    hood = o.get("hood", "none")
    if hood == "cornice":
        fr.fbox(m, trim, a - 0.12, b + 0.12, zh + 0.05, zh + 0.30, -0.02, 0.06, conf, skip=("bottom",))
        fr.fbox(m, trim, a - 0.22, b + 0.22, zh + 0.30, zh + 0.44, -0.02, 0.17, conf)
    elif hood in ("arch", "segment") and len(arc) > 2:
        wband = 0.16
        cxz = ((a + b) / 2, zt)
        for i in range(len(arc) - 1):
            p0, p1 = arc[i], arc[i + 1]

            def outp(p):
                if o["kind"] == "segment":
                    return (p[0], p[1] + wband)
                dx, dz = p[0] - cxz[0], p[1] - cxz[1]
                r = math.hypot(dx, dz) or 1.0
                return (p[0] + dx / r * wband, p[1] + dz / r * wband)
            q0, q1 = outp(p0), outp(p1)
            m.quad(trim, fr.p(p0[0], p0[1], 0.07), fr.p(q0[0], q0[1], 0.07),
                   fr.p(q1[0], q1[1], 0.07), fr.p(p1[0], p1[1], 0.07), conf, fr.out)
            m.quad(trim, fr.p(q0[0], q0[1], 0.0), fr.p(q1[0], q1[1], 0.0),
                   fr.p(q1[0], q1[1], 0.07), fr.p(q0[0], q0[1], 0.07), conf,
                   (fr.t[0] * ((q0[0] + q1[0]) / 2 - cxz[0]), fr.t[1] * ((q0[0] + q1[0]) / 2 - cxz[0]),
                    (q0[1] + q1[1]) / 2 - cxz[1]))
        fr.fbox(m, trim, cx - 0.12, cx + 0.12, zh - 0.10, zh + 0.22, -0.02, 0.12, conf, skip=("bottom",))
    elif hood == "pediment":
        fr.fbox(m, trim, a - 0.15, b + 0.15, zh + 0.05, zh + 0.25, -0.02, 0.12, conf, skip=("bottom",))
        pk = zh + 0.25 + (b - a + 0.4) * 0.22
        tri = [fr.p(a - 0.2, zh + 0.25, 0.13), fr.p(b + 0.2, zh + 0.25, 0.13), fr.p(cx, pk, 0.13)]
        m.face(trim, tri, conf, fr.out)
        for (p, q) in ((tri[0], tri[2]), (tri[2], tri[1])):
            pb, qb = _sub(p, _mul(fr.out, 0.15)), _sub(q, _mul(fr.out, 0.15))
            m.quad(trim, p, q, (q[0], q[1], q[2] + 0.06), (p[0], p[1], p[2] + 0.06), conf, (0, 0, 1))
            m.quad(trim, (p[0], p[1], p[2] + 0.06), (q[0], q[1], q[2] + 0.06),
                   (qb[0], qb[1], qb[2] + 0.06), (pb[0], pb[1], pb[2] + 0.06), conf, (0, 0, 1))


# --------------------------------------------------------------------------- facades


def bay_centres(spec, length):
    if spec is None:
        return []
    if "at" in spec:
        return [float(s) for s in spec["at"]]
    n = int(spec["n"])
    ml, mr = (spec.get("margin", [1.5, 1.5]) + [spec.get("margin", [1.5, 1.5])[0]])[:2] \
        if isinstance(spec.get("margin"), list) else (spec.get("margin", 1.5),) * 2
    if n == 1:
        return [length / 2]
    step = (length - ml - mr) / (n - 1)
    return [ml + step * i for i in range(n)]


def storey_z(block):
    z = [block.get("z0", 0.0)]
    for h in block["storeys"]:
        z.append(z[-1] + h)
    return z


def block_faces(m: Mesh, block, conf):
    """Walls, openings, belts, quoins of one block. Returns its wall head z."""
    zs_block = storey_z(block)
    mat = WALL_MAT[block.get("wall", "limestone")]
    trim = block.get("trim", "stone_trim")
    course = block.get("course_m")
    faces = block.get("faces") or {}
    box = block["box"]
    for fk in ("S", "E", "N", "W"):
        f = faces.get(fk, "blank")
        if f == "none":
            continue
        # a face may divide its height its own way (the Chamber's front windows run lower
        # than the side's, over no shop fronts): `levels` replaces the block's storeys there
        fd = f if isinstance(f, dict) else {}
        zs = storey_z({"z0": block.get("z0", 0.0), "storeys": fd["levels"]}) if fd.get("levels") else zs_block
        rustic_n = fd.get("rustic_storeys", block.get("rustic_storeys", 0))
        fr, L = face_frame(box, fk)
        bays = bay_centres(f.get("bays"), L) if isinstance(f, dict) else []
        specs = (f.get("storeys") or []) if isinstance(f, dict) else []
        skip = {tuple(x) for x in (f.get("skip") or [])} if isinstance(f, dict) else set()
        over = (f.get("override") or []) if isinstance(f, dict) else []
        for k in range(len(zs) - 1):
            za, zb = zs[k], zs[k + 1]
            ops = []
            spec = specs[k] if k < len(specs) else None
            sbays = bay_centres(spec["bays"], L) if spec and spec.get("bays") else bays
            for i, s in enumerate(sbays):
                o = {x: y for x, y in spec.items() if x != "bays"} if spec else None
                for ov in over:
                    if i in ov.get("bays", [i]) and k in ov.get("storeys", [k]):
                        o = dict(o or {}, **{x: y for x, y in ov.items() if x not in ("bays", "storeys")})
                if not o or o.get("kind") == "blank" or (i, k) in skip:
                    continue
                o["s"] = s
                o["zs"] = za + o.get("sill", 0.9)
                o.setdefault("h", 2.4)
                o.setdefault("w", 1.2)
                o.setdefault("kind", "flat")
                o["reveal"] = mat
                ops.append(o)
            rustic = k < rustic_n
            wall(m, fr, 0.0, L, za, zb, ops, mat, conf,
                 course=(0.5 if rustic else course), rustic=rustic)
            for o in ops:
                opening_fill(m, fr, o, conf, trim)
                if o["kind"] == "store":   # the iron colonettes either side of a shop front
                    for e in (o["s"] - o["w"] / 2, o["s"] + o["w"] / 2):
                        fr.fbox(m, "iron", e - 0.09, e + 0.09, o["zs"], o["zs"] + o["h"], -0.05, 0.08, conf, skip=("bottom",))
            if isinstance(f, dict) and k == 0 and f.get("awnings"):
                aw = f["awnings"]
                for i, s in enumerate(bays):
                    if aw != "all" and i not in aw:
                        continue
                    w = (spec or {}).get("w", 1.2) + 0.4
                    ztop = zb - 0.35
                    m.quad("awning", fr.p(s - w / 2, ztop, 0.05), fr.p(s + w / 2, ztop, 0.05),
                           fr.p(s + w / 2, ztop - 0.9, 1.7), fr.p(s - w / 2, ztop - 0.9, 1.7), conf, (0, 0, 1))
                    m.quad("awning", fr.p(s - w / 2, ztop - 0.9, 1.7), fr.p(s + w / 2, ztop - 0.9, 1.7),
                           fr.p(s + w / 2, ztop - 1.15, 1.7), fr.p(s - w / 2, ztop - 1.15, 1.7), conf, fr.out)
        # pilaster strips (rusticated where the block's base is), full height
        if isinstance(f, dict):
            for pl in f.get("pilasters") or []:
                ps, pw = pl["s"], pl.get("w", 1.2)
                pd = pl.get("proj", 0.15)
                zt_ = zs[pl.get("to", len(zs) - 1)]
                fr.fbox(m, mat, ps - pw / 2, ps + pw / 2, zs[0], zt_, 0.0, pd, conf, skip=("bottom",))
                z = zs[0] + 0.5
                while z < zt_ - 0.05:
                    m.quad("joint", fr.p(ps - pw / 2, z - 0.02, pd + 0.004), fr.p(ps + pw / 2, z - 0.02, pd + 0.004),
                           fr.p(ps + pw / 2, z + 0.02, pd + 0.004), fr.p(ps - pw / 2, z + 0.02, pd + 0.004), conf, fr.out)
                    z += 0.5
        # belts at the floor lines asked for
        for k in fd.get("belts", block.get("belts", [])):
            z = zs[k]
            fr.fbox(m, trim, -0.06, L + 0.06, z - 0.12, z + 0.12, -0.02, 0.07, conf)
        if block.get("water_table"):
            fr.fbox(m, trim, -0.05, L + 0.05, zs[0], zs[0] + block["water_table"], -0.02, 0.06, conf, skip=("bottom",))
        # quoins at a face's two ends, long and short in turn
        if block.get("quoins"):
            q0 = zs[min(rustic_n, len(zs) - 1)]
            j = 0
            z = q0
            while z < zs[-1] - 0.05:
                h = min(0.5, zs[-1] - z)
                for end in (0, 1):
                    ln = 0.85 if (j + end) % 2 == 0 else 0.5
                    a, b = (0.0, ln) if end == 0 else (L - ln, L)
                    fr.fbox(m, trim, a, b, z + 0.02, z + h - 0.02, -0.02, 0.035, conf, skip=("bottom",))
                z += h
                j += 1
    return zs_block[-1]


def _profile(kind, proj):
    """A cornice's section, (out, up) from the wall face at the wall head."""
    if kind == "light":
        return [(0, -0.45), (0.06, -0.45), (0.06, -0.3), (proj * 0.6, -0.15), (proj, -0.1), (proj, 0.05), (0, 0.05)]
    return [(0, -0.95), (0.08, -0.95), (0.08, -0.62), (0.18, -0.55), (0.18, -0.42),
            (proj, -0.3), (proj, -0.08), (proj + 0.06, 0.0), (proj + 0.06, 0.08), (0, 0.08)]


def sweep_box(m, mat, box, sides, z, profile, conf):
    """Sweep a section round the named sides of a box at height z (mitred where two meet)."""
    x0, y0, x1, y1 = box
    order = ["S", "E", "N", "W"]
    for si, side in enumerate(order):
        if side not in sides:
            continue
        prev_on = order[si - 1] in sides
        next_on = order[(si + 1) % 4] in sides
        fr, L = face_frame(box, side)
        for i in range(len(profile) - 1):
            (o0, u0), (o1, u1) = profile[i], profile[i + 1]
            a0 = -o0 if prev_on else 0.0
            b0 = L + o0 if next_on else L
            a1 = -o1 if prev_on else 0.0
            b1 = L + o1 if next_on else L
            p = [fr.p(a0, z + u0, o0), fr.p(b0, z + u0, o0), fr.p(b1, z + u1, o1), fr.p(a1, z + u1, o1)]
            du, do = u1 - u0, o1 - o0
            hint = _add(_mul(fr.out, du), (0, 0, -do)) if abs(du) + abs(do) > 0 else fr.out
            m.quad(mat, *p, conf, hint)
        for end, on in ((0.0, prev_on), (L, next_on)):
            if on:
                continue
            ring = [fr.p(end, z + u, o) for (o, u) in profile]
            tan = (fr.t[0] * (-1 if end == 0 else 1), fr.t[1] * (-1 if end == 0 else 1), 0)
            m.face(mat, ring, conf, tan)


def brackets(m, mat, box, sides, z, proj, spacing, conf):
    for side in sides:
        fr, L = face_frame(box, side)
        n = max(2, int(L / spacing))
        for i in range(n + 1):
            s = 0.3 + (L - 0.6) * i / n
            fr.fbox(m, mat, s - 0.11, s + 0.11, z - 0.62, z - 0.3, 0.0, proj * 0.92, conf, skip=("top",))


def battlement(m: Mesh, pts, z, spec, mat, conf):
    """A crenellated parapet (T-3689) along the closed ring `pts` (anticlockwise seen from
    above) from z: a solid band `base` high, then merlons `merlon` wide and `h` high with
    `gap` between them, `depth` thick, set flush with the wall face."""
    h, base = spec.get("h", 0.9), spec.get("base", 0.35)
    mw, gap, dep = spec.get("merlon", 0.8), spec.get("gap", 0.55), spec.get("depth", 0.45)
    proj = spec.get("proj", 0.0)
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 1e-6:
            continue
        t = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        fr = Frame(a, t, (t[1], -t[0]))
        fr.fbox(m, mat, -proj, L + proj, z, z + base, -dep, proj, conf, skip=("bottom",))
        k = max(1, round((L + gap) / (mw + gap)))
        w = (L + gap) / k - gap
        for j in range(k):
            s0 = j * (w + gap)
            fr.fbox(m, mat, s0 - (proj if j == 0 else 0.0), s0 + w + (proj if j == k - 1 else 0.0),
                    z + base, z + base + h, -dep, proj, conf, skip=("bottom",))


def roof(m: Mesh, block, ztop, conf, sides):
    x0, y0, x1, y1 = block["box"]
    r = block.get("roof") or {"kind": "flat"}
    cov = r.get("covering", "slate")
    kind = r["kind"]
    if kind == "flat":
        par = block.get("parapet")
        if par:
            for side in sides:
                fr, L = face_frame(block["box"], side)
                fr.fbox(m, WALL_MAT[block.get("wall", "limestone")], 0.0, L, ztop, ztop + par, -0.35, 0.0, conf, skip=("bottom",))
                fr.fbox(m, "stone_trim", -0.05, L + 0.05, ztop + par, ztop + par + 0.12, -0.42, 0.06, conf)
        m.face("tin_dark" if cov == "slate" else cov,
               [(x0, y0, ztop + 0.04), (x1, y0, ztop + 0.04), (x1, y1, ztop + 0.04), (x0, y1, ztop + 0.04)], conf, (0, 0, 1))
        if block.get("battlement"):
            battlement(m, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], ztop + (par or 0), block["battlement"],
                       WALL_MAT[block.get("wall", "limestone")], conf)
        return ztop + (par or 0)
    if kind == "hip":
        h = r["h"]
        e = r.get("eave", 0.3)
        ring = [(x0 - e, y0 - e), (x1 + e, y0 - e), (x1 + e, y1 + e), (x0 - e, y1 + e)]
        w, d = x1 - x0, y1 - y0
        if w >= d:
            ridge = [(x0 + d / 2, (y0 + y1) / 2), (x1 - d / 2, (y0 + y1) / 2)]
            m.face(cov, [(*ring[0], ztop), (*ring[1], ztop), (*ridge[1], ztop + h), (*ridge[0], ztop + h)], conf, (0, -1, 1))
            m.face(cov, [(*ring[2], ztop), (*ring[3], ztop), (*ridge[0], ztop + h), (*ridge[1], ztop + h)], conf, (0, 1, 1))
            m.face(cov, [(*ring[1], ztop), (*ring[2], ztop), (*ridge[1], ztop + h)], conf, (1, 0, 1))
            m.face(cov, [(*ring[3], ztop), (*ring[0], ztop), (*ridge[0], ztop + h)], conf, (-1, 0, 1))
        else:
            ridge = [((x0 + x1) / 2, y0 + w / 2), ((x0 + x1) / 2, y1 - w / 2)]
            m.face(cov, [(*ring[1], ztop), (*ring[2], ztop), (*ridge[1], ztop + h), (*ridge[0], ztop + h)], conf, (1, 0, 1))
            m.face(cov, [(*ring[3], ztop), (*ring[0], ztop), (*ridge[0], ztop + h), (*ridge[1], ztop + h)], conf, (-1, 0, 1))
            m.face(cov, [(*ring[0], ztop), (*ring[1], ztop), (*ridge[0], ztop + h)], conf, (0, -1, 1))
            m.face(cov, [(*ring[2], ztop), (*ring[3], ztop), (*ridge[1], ztop + h)], conf, (0, 1, 1))
        return ztop + h
    if kind == "gable":
        # T-3689: a pitched roof over a frame house or barn, its ridge along the block's
        # longer side unless `ridge` names the axis ("x" or "y"); the gable ends are
        # closed in the block's own wall, the eaves and rakes run out by `eave`.
        h = r["h"]
        e = r.get("eave", 0.3)
        wmat = WALL_MAT[block.get("wall", "limestone")]
        along_x = r.get("ridge", "x" if (x1 - x0) >= (y1 - y0) else "y") == "x"
        if along_x:
            ym = (y0 + y1) / 2
            a0, a1 = x0 - e, x1 + e
            m.face(cov, [(a0, y0 - e, ztop - e * h / ((y1 - y0) / 2)), (a1, y0 - e, ztop - e * h / ((y1 - y0) / 2)),
                         (a1, ym, ztop + h), (a0, ym, ztop + h)], conf, (0, -1, 1))
            m.face(cov, [(a1, y1 + e, ztop - e * h / ((y1 - y0) / 2)), (a0, y1 + e, ztop - e * h / ((y1 - y0) / 2)),
                         (a0, ym, ztop + h), (a1, ym, ztop + h)], conf, (0, 1, 1))
            m.face(wmat, [(x0, y0, ztop), (x0, y1, ztop), (x0, ym, ztop + h)], conf, (-1, 0, 0))
            m.face(wmat, [(x1, y0, ztop), (x1, y1, ztop), (x1, ym, ztop + h)], conf, (1, 0, 0))
        else:
            xm = (x0 + x1) / 2
            a0, a1 = y0 - e, y1 + e
            dz = e * h / ((x1 - x0) / 2)
            m.face(cov, [(x0 - e, a1, ztop - dz), (x0 - e, a0, ztop - dz), (xm, a0, ztop + h), (xm, a1, ztop + h)], conf, (-1, 0, 1))
            m.face(cov, [(x1 + e, a0, ztop - dz), (x1 + e, a1, ztop - dz), (xm, a1, ztop + h), (xm, a0, ztop + h)], conf, (1, 0, 1))
            m.face(wmat, [(x0, y0, ztop), (x1, y0, ztop), (xm, y0, ztop + h)], conf, (0, -1, 0))
            m.face(wmat, [(x0, y1, ztop), (x1, y1, ztop), (xm, y1, ztop + h)], conf, (0, 1, 0))
        return ztop + h
    # mansard: a curved or straight lower slope to a curb, then a low deck
    h = r["h"]
    i0 = r.get("inset", 0.25)
    run = r.get("run", h * 0.32)
    curve = r.get("curve", 0.0)   # how far the slope bellies out at mid-height
    n = 4 if curve else 1
    rings = []
    for k in range(n + 1):
        t = k / n
        off = i0 + run * t - curve * math.sin(math.pi * t)
        rings.append((off, ztop + h * t))
    for k in range(n):
        (oa, za), (ob, zb) = rings[k], rings[k + 1]
        ca = [(x0 + oa, y0 + oa), (x1 - oa, y0 + oa), (x1 - oa, y1 - oa), (x0 + oa, y1 - oa)]
        cb = [(x0 + ob, y0 + ob), (x1 - ob, y0 + ob), (x1 - ob, y1 - ob), (x0 + ob, y1 - ob)]
        for j, nrm in enumerate([(0, -1, 0.4), (1, 0, 0.4), (0, 1, 0.4), (-1, 0, 0.4)]):
            q = (j + 1) % 4
            m.quad(cov, (*ca[j], za), (*ca[q], za), (*cb[q], zb), (*cb[j], zb), conf, nrm)
    off, zc = rings[-1]
    # the curb: a moulded band, then the deck in tin
    cring = (x0 + off, y0 + off, x1 - off, y1 - off)
    sweep_box(m, "stone_trim" if r.get("curb", "stone") == "stone" else "tin_dark", cring, ["S", "E", "N", "W"], zc,
              [(0, -0.05), (0.12, -0.05), (0.12, 0.12), (0, 0.12)], conf)
    m.face("tin_dark", [(x0 + off, y0 + off, zc + 0.1), (x1 - off, y0 + off, zc + 0.1),
                        (x1 - off, y1 - off, zc + 0.1), (x0 + off, y1 - off, zc + 0.1)], conf, (0, 0, 1))
    if r.get("cresting"):
        for side in ["S", "E", "N", "W"]:
            fr, L = face_frame(cring, side)
            fr.fbox(m, "iron", 0, L, zc + 0.12, zc + 0.55, -0.02, 0.0, conf, skip=("bottom", "top"))
    # dormers on the slope, at the face's bays or where named
    for dk, dsp in (r.get("dormers") or {}).items():
        fr, L = face_frame(block["box"], dk)
        faces = block.get("faces") or {}
        fsp = faces.get(dk) if isinstance(faces.get(dk), dict) else {}
        at = dsp.get("at") or bay_centres(fsp.get("bays"), L)
        for s in at:
            dormer(m, fr, s, ztop, i0, run, h, dsp, conf, cov)
    return zc


def dormer(m, fr, s, ztop, i0, run, h, d, conf, cov):
    w, dh = d.get("w", 1.4), d.get("h", min(h * 0.75, 2.6))
    zb = ztop + d.get("z_off", 0.35)
    front = -(i0 + run * (zb - ztop) / h) - 0.05
    back = front - max(0.9, run)
    kind = d.get("kind", "arched")
    body = d.get("body", "stone_trim")
    if kind == "oculus":
        # a round light in a moulded frame set in the slope's face
        r = w / 2
        cz = zb + dh / 2
        ring = [(s + r * math.cos(2 * math.pi * i / 12), cz + r * math.sin(2 * math.pi * i / 12)) for i in range(12)]
        outer = [(s + (r + 0.18) * math.cos(2 * math.pi * i / 12), cz + (r + 0.18) * math.sin(2 * math.pi * i / 12)) for i in range(12)]
        for i in range(12):
            j = (i + 1) % 12
            m.quad(body, fr.p(*ring[i], front + 0.12), fr.p(*outer[i], front + 0.12),
                   fr.p(*outer[j], front + 0.12), fr.p(*ring[j], front + 0.12), conf, fr.out)
            m.quad(body, fr.p(*outer[i], front - 0.4), fr.p(*outer[j], front - 0.4),
                   fr.p(*outer[j], front + 0.12), fr.p(*outer[i], front + 0.12), conf,
                   (fr.t[0] * (outer[i][0] - s), fr.t[1] * (outer[i][0] - s), outer[i][1] - cz))
        m.face("glass", [fr.p(*q, front + 0.06) for q in ring], conf, fr.out)
        m.face("backing", [fr.p(*q, front - 0.3) for q in ring], conf, fr.out)
        return
    zt = zb + dh
    fr.fbox(m, body, s - w / 2 - 0.15, s + w / 2 + 0.15, zb, zt, back, front, conf, skip=("bottom",))
    o = {"kind": "round" if kind == "arched" else "flat", "s": s, "w": w - 0.25, "zs": zb + 0.25,
         "h": dh - 0.55, "hood": "none", "depth": 0.12, "reveal": body}
    # the light, laid on the dormer's face as glass in a frame (not cut through it)
    a, b = o["s"] - o["w"] / 2, o["s"] + o["w"] / 2
    arc = _arc(o, a, b, o["zs"] + o["h"] - _rise(o, o["w"]))
    ring = [(a, o["zs"]), (b, o["zs"])] + list(reversed(arc))
    m.face("glass", [fr.p(q[0], q[1], front + 0.01) for q in ring], conf, fr.out)
    m.quad("sash", fr.p(s - 0.03, o["zs"], front + 0.015), fr.p(s + 0.03, o["zs"], front + 0.015),
           fr.p(s + 0.03, o["zs"] + o["h"], front + 0.015), fr.p(s - 0.03, o["zs"] + o["h"], front + 0.015), conf, fr.out)
    # its head: a pediment, a segment or a round hood
    hk = d.get("head", "pediment")
    if hk == "pediment":
        tri = [fr.p(s - w / 2 - 0.3, zt, front + 0.08), fr.p(s + w / 2 + 0.3, zt, front + 0.08),
               fr.p(s, zt + (w + 0.6) * 0.28, front + 0.08)]
        m.face(body, tri, conf, fr.out)
        tb = [(q[0] + fr.n[0] * (back - front - 0.08), q[1] + fr.n[1] * (back - front - 0.08), q[2]) for q in tri]
        m.quad(cov, tri[0], tri[2], tb[2], tb[0], conf, (-fr.t[0], -fr.t[1], 1))
        m.quad(cov, tri[2], tri[1], tb[1], tb[2], conf, (fr.t[0], fr.t[1], 1))
    else:
        fr.fbox(m, body, s - w / 2 - 0.3, s + w / 2 + 0.3, zt, zt + 0.25, back, front + 0.1, conf)


def tower(m: Mesh, t, conf):
    """A stack of prisms (square, octagonal or round) with openings and a cap."""
    cx, cy = t["at"]
    z = t.get("z0", 0.0)
    plan = t.get("plan", "square")
    sides = {"square": 4, "octagon": 8, "round": 12}[plan]
    wallmat = WALL_MAT[t.get("wall", "limestone")]
    for st in t["stages"]:
        w, h = st["w"], st["h"]
        R = (w / 2) / math.cos(math.pi / sides)
        rot = math.pi / sides if plan != "square" else math.pi / 4
        ring = [(cx + R * math.cos(rot + 2 * math.pi * i / sides), cy + R * math.sin(rot + 2 * math.pi * i / sides))
                for i in range(sides)]
        side_len = 2 * R * math.sin(math.pi / sides)
        op = st.get("openings")
        for i in range(sides):
            a, b = ring[i], ring[(i + 1) % sides]
            tx, ty = (b[0] - a[0]) / side_len, (b[1] - a[1]) / side_len
            fr = Frame(a, (tx, ty), (ty, -tx))
            ops = []
            if op and (op.get("faces") is None or i in op["faces"]):
                n = op.get("count", 1)
                for k in range(n):
                    o = {"kind": op.get("kind", "round"), "w": op.get("w", side_len * 0.45),
                         "h": op.get("h", h * 0.6), "s": side_len * (k + 1) / (n + 1),
                         "hood": op.get("hood", "none"), "depth": op.get("depth", 0.25), "reveal": wallmat}
                    o["zs"] = z + op.get("sill", (h - o["h"]) / 2)
                    ops.append(o)
            wall(m, fr, 0.0, side_len, z, z + h, ops, wallmat, conf)
            for o in ops:
                if op.get("louvre"):
                    o2 = dict(o)
                    opening_fill(m, fr, dict(o2, kind=o2["kind"]), conf)
                else:
                    opening_fill(m, fr, o, conf)
            if st.get("clock"):
                cz = z + h * st.get("clock_at", 0.55)
                rr = st.get("clock_r", min(side_len, h) * 0.3)
                circ = [fr.p(side_len / 2 + rr * math.cos(2 * math.pi * k / 16), cz + rr * math.sin(2 * math.pi * k / 16), 0.03)
                        for k in range(16)]
                m.face("clock", circ, conf, fr.out)
                m.quad("iron", fr.p(side_len / 2 - 0.02, cz, 0.04), fr.p(side_len / 2 + 0.02, cz, 0.04),
                       fr.p(side_len / 2 + 0.02, cz + rr * 0.8, 0.04), fr.p(side_len / 2 - 0.02, cz + rr * 0.8, 0.04), conf, fr.out)
        if st.get("cornice", True):
            proj = st.get("cornice_proj", 0.35)
            R2 = R + proj
            ring2 = [(cx + R2 * math.cos(rot + 2 * math.pi * i / sides), cy + R2 * math.sin(rot + 2 * math.pi * i / sides))
                     for i in range(sides)]
            m.prism("stone_trim", ring2, z + h - 0.05, z + h + 0.3, conf, top=True, bottom=True)
        if st.get("battlement"):
            bt = st["battlement"]
            Rt = R + bt.get("out", 0.0)
            ringt = [(cx + Rt * math.cos(rot + 2 * math.pi * i / sides), cy + Rt * math.sin(rot + 2 * math.pi * i / sides))
                     for i in range(sides)]
            battlement(m, ringt, z + h + (0.3 if st.get("cornice", True) else 0.0), bt, wallmat, conf)
        if st.get("balustrade"):
            Rb = R + st.get("cornice_proj", 0.35) - 0.1
            ringb = [(cx + Rb * math.cos(rot + 2 * math.pi * i / sides), cy + Rb * math.sin(rot + 2 * math.pi * i / sides))
                     for i in range(sides)]
            m.prism("stone_trim", ringb, z + h + 0.3, z + h + 1.1, conf, top=False)
        z += h + (0.3 if st.get("cornice", True) else 0.0)
    cap = t.get("cap") or {"kind": "flat"}
    w = t["stages"][-1]["w"] * cap.get("w_ratio", 1.0)
    R = (w / 2) / math.cos(math.pi / sides)
    rot = math.pi / sides if plan != "square" else math.pi / 4
    ch = cap.get("h", w * 0.6)
    mat = cap.get("covering", "tin_dark")
    kind = cap["kind"]
    seg = 16 if kind in ("dome", "bell", "lantern_dome") and plan != "square" else sides
    if kind == "pyramid":
        apex = (cx, cy, z + ch)
        for i in range(sides):
            a = (cx + R * math.cos(rot + 2 * math.pi * i / sides), cy + R * math.sin(rot + 2 * math.pi * i / sides), z)
            b = (cx + R * math.cos(rot + 2 * math.pi * (i + 1) / sides), cy + R * math.sin(rot + 2 * math.pi * (i + 1) / sides), z)
            mid = ((a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cy, 0.5)
            m.face(mat, [a, b, apex], conf, mid)
        ztop = z + ch
    elif kind in ("dome", "bell", "lantern_dome"):
        prof = []
        rings = 7
        for k in range(rings + 1):
            t_ = k / rings
            if kind == "bell":   # an ogee: swelling out then drawing in to a neck
                r = R * (1.0 + 0.12 * math.sin(math.pi * t_) - 0.85 * t_ ** 1.6)
            else:
                r = R * math.cos(t_ * math.pi / 2)
            prof.append((max(r, 0.02), z + ch * (math.sin(t_ * math.pi / 2) if kind != "bell" else t_)))
        for k in range(rings):
            (ra, za), (rb, zb) = prof[k], prof[k + 1]
            for i in range(seg):
                a0 = rot + 2 * math.pi * i / seg
                a1 = rot + 2 * math.pi * (i + 1) / seg
                pa0 = (cx + ra * math.cos(a0), cy + ra * math.sin(a0), za)
                pa1 = (cx + ra * math.cos(a1), cy + ra * math.sin(a1), za)
                pb1 = (cx + rb * math.cos(a1), cy + rb * math.sin(a1), zb)
                pb0 = (cx + rb * math.cos(a0), cy + rb * math.sin(a0), zb)
                am = (a0 + a1) / 2
                m.quad(mat, pa0, pa1, pb1, pb0, conf, (math.cos(am), math.sin(am), (zb - za) / max(ch, 0.1)))
        ztop = prof[-1][1]
        if kind == "lantern_dome":
            lw = cap.get("lantern_w", w * 0.28)
            lh = cap.get("lantern_h", lw * 1.6)
            lr = [(cx + lw / 2 * math.cos(2 * math.pi * i / 8 + math.pi / 8), cy + lw / 2 * math.sin(2 * math.pi * i / 8 + math.pi / 8)) for i in range(8)]
            m.prism("stone_trim", lr, ztop - 0.2, ztop + lh, conf)
            m.prism(mat, [(cx + (p[0] - cx) * 1.25, cy + (p[1] - cy) * 1.25) for p in lr], ztop + lh, ztop + lh + 0.2, conf)
            apex = (cx, cy, ztop + lh + 0.2 + lw * 0.5)
            for i in range(8):
                a, b = lr[i], lr[(i + 1) % 8]
                m.face(mat, [(*a, ztop + lh + 0.2), (*b, ztop + lh + 0.2), apex], conf,
                       ((a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cy, 0.4))
            ztop = apex[2]
    else:
        ring = [(cx + R * math.cos(rot + 2 * math.pi * i / sides), cy + R * math.sin(rot + 2 * math.pi * i / sides)) for i in range(sides)]
        m.face("tin_dark", [(*p, z + 0.05) for p in ring], conf, (0, 0, 1))
        ztop = z
    fh = t.get("finial", 0.0)
    if fh:
        fr_ = [(cx + 0.06 * math.cos(2 * math.pi * i / 6), cy + 0.06 * math.sin(2 * math.pi * i / 6)) for i in range(6)]
        m.prism("iron", fr_, ztop - 0.1, ztop + fh, conf)
        bl = [(cx + 0.2 * math.cos(2 * math.pi * i / 8), cy + 0.2 * math.sin(2 * math.pi * i / 8)) for i in range(8)]
        m.prism("iron", bl, ztop + fh * 0.3, ztop + fh * 0.3 + 0.35, conf, bottom=True)


def pediment(m, blocks, g, conf):
    b = blocks[g["block"]]
    fr, L = face_frame(b["box"], g["face"])
    z = g.get("z", storey_z(b)[-1] + 0.08)
    s, w, h = g["s"], g["w"], g["h"]
    th = g.get("depth", 0.5)
    kind = g.get("kind", "pediment")
    if kind == "segment":
        n = 8
        R = (w * w / 4 + h * h) / (2 * h)
        zc = z + h - R
        th0 = math.asin((w / 2) / R)
        top = [(s + R * math.sin(-th0 + 2 * th0 * i / n), zc + R * math.cos(-th0 + 2 * th0 * i / n)) for i in range(n + 1)]
    elif kind == "scroll":
        top = [(s - w / 2, z), (s - w / 2, z + h * 0.45), (s - w * 0.3, z + h * 0.55), (s - w * 0.18, z + h * 0.85),
               (s, z + h), (s + w * 0.18, z + h * 0.85), (s + w * 0.3, z + h * 0.55), (s + w / 2, z + h * 0.45), (s + w / 2, z)]
    else:
        top = [(s - w / 2, z), (s, z + h), (s + w / 2, z)]
    ring = [(s - w / 2, z)] + [q for q in top if not (abs(q[1] - z) < 1e-9 and abs(q[0] - (s - w / 2)) < 1e-9)]
    if abs(ring[-1][1] - z) > 1e-9:
        ring.append((s + w / 2, z))
    # front and back faces, fanned from the base centre (the outline is star-shaped from there)
    c = (s, z)
    for d, hint in ((0.02, fr.out), (-th, _mul(fr.out, -1))):
        for i in range(len(ring) - 1):
            m.face(g.get("material", "stone_trim"), [fr.p(*c, d), fr.p(*ring[i], d), fr.p(*ring[i + 1], d)], conf, hint)
    for i in range(len(ring) - 1):
        p0, p1 = ring[i], ring[i + 1]
        if abs(p0[1] - z) < 1e-9 and abs(p1[1] - z) < 1e-9:
            continue
        mid = ((p0[0] + p1[0]) / 2 - s, (p0[1] + p1[1]) / 2 - z)
        m.quad(g.get("covering", "tin_dark") if kind != "scroll" else "stone_trim",
               fr.p(*p0, 0.12), fr.p(*p1, 0.12), fr.p(*p1, -th), fr.p(*p0, -th), conf,
               (fr.t[0] * mid[0], fr.t[1] * mid[0], mid[1] + 0.01))
    if g.get("clock"):
        cz = z + h * 0.45
        rr = min(w, h) * 0.22
        circ = [fr.p(s + rr * math.cos(2 * math.pi * k / 16), cz + rr * math.sin(2 * math.pi * k / 16), 0.05) for k in range(16)]
        m.face("clock", circ, conf, fr.out)
    if g.get("oculus"):
        cz = z + h * 0.42
        rr = min(w, h) * 0.18
        circ = [fr.p(s + rr * math.cos(2 * math.pi * k / 12), cz + rr * math.sin(2 * math.pi * k / 12), 0.05) for k in range(12)]
        m.face("glass", circ, conf, fr.out)


def porch(m, blocks, p, conf):
    b = blocks[p["block"]]
    fr, L = face_frame(b["box"], p["face"])
    s0, s1, h, dep = p["s0"], p["s1"], p["h"], p["depth"]
    z0 = p.get("z0", 0.0)
    n = p.get("columns", 4)
    for i in range(n):
        s = s0 + 0.35 + (s1 - s0 - 0.7) * i / max(1, n - 1)
        ring = [fr.p(s + 0.25 * math.cos(2 * math.pi * k / 8), z0, dep - 0.35 + 0.25 * math.sin(2 * math.pi * k / 8))[:2]
                for k in range(8)]
        m.prism(p.get("material", "stone_trim"), ring, z0, z0 + h, conf, top=False)
    slab = p.get("slab", 0.8)
    fr.fbox(m, p.get("material", "stone_trim"), s0, s1, z0 + h, z0 + h + slab, 0.0, dep, conf)
    if p.get("balcony"):
        fr.fbox(m, "iron", s0, s1, z0 + h + slab, z0 + h + slab + 0.95, dep - 0.05, dep, conf, skip=("bottom", "top"))


def steps(m, blocks, p, conf):
    b = blocks[p["block"]]
    fr, L = face_frame(b["box"], p["face"])
    n, rise, tread = p["n"], p.get("rise", 0.17), p.get("tread", 0.32)
    for i in range(n):
        fr.fbox(m, p.get("material", "stone_trim"), p["s0"], p["s1"], 0.0, rise * (n - i), 0.0, tread * (i + 1) + p.get("landing", 0.0) * (i == 0),
                conf, skip=("bottom",))


def build(params: LandmarkParams) -> Mesh:
    params.validate()
    c = params.composition
    m = Mesh()
    base_conf = CONF.get(c.get("confidence", "inferred"), 0.5)
    blocks = c["blocks"]
    for b in blocks:
        conf = CONF.get(b.get("confidence"), base_conf)
        zt = block_faces(m, b, conf)
        faces = b.get("faces") or {}
        sides = [k for k in ("S", "E", "N", "W") if faces.get(k, "blank") != "none"]
        cor = b.get("cornice")
        if cor:
            prof = _profile(cor.get("kind", "bracketed"), cor.get("proj", 0.8))
            sweep_box(m, cor.get("material", "stone_trim"), b["box"], sides, zt, prof, conf)
            if cor.get("brackets"):
                brackets(m, cor.get("material", "stone_trim"), b["box"], sides, zt, cor.get("proj", 0.8), cor["brackets"], conf)
            zt += 0.08
        roof(m, b, zt, conf, sides)
    for g in c.get("pediments") or []:
        pediment(m, blocks, g, CONF.get(g.get("confidence"), base_conf))
    for t in c.get("towers") or []:
        tower(m, t, CONF.get(t.get("confidence"), base_conf))
    for p in c.get("porches") or []:
        porch(m, blocks, p, CONF.get(p.get("confidence"), base_conf))
    for p in c.get("steps") or []:
        steps(m, blocks, p, CONF.get(p.get("confidence"), base_conf))
    for ch in c.get("chimneys") or []:
        x, y = ch["at"]
        w, d = ch.get("w", 1.0), ch.get("d", 0.6)
        m.prism(ch.get("material", "brick_wall"), [(x - w / 2, y - d / 2), (x + w / 2, y - d / 2), (x + w / 2, y + d / 2), (x - w / 2, y + d / 2)],
                ch["z0"], ch["z0"] + ch["h"], CONF.get(ch.get("confidence"), base_conf))
    for f in c.get("flagpoles") or []:
        x, y, z = f["at"]
        ring = [(x + 0.07 * math.cos(2 * math.pi * k / 6), y + 0.07 * math.sin(2 * math.pi * k / 6)) for k in range(6)]
        m.prism("iron", ring, z, z + f["h"], base_conf)
    return m


def _pad(b: bytes, fill: bytes = b"\x00") -> bytes:
    return b + fill * ((4 - len(b) % 4) % 4)


def glb(params: LandmarkParams, structure_id: str, phase_id: str, fire: dict | None = None) -> bytes:
    # The shell this building left: the composition's own `fire` block unless one is passed.
    src = fire if fire is not None else (params.composition.get("fire") or {})
    shell = {k: src[k] for k in ("fate", "left", "time") if k in src}
    """The structure's GLB, glTF y-up: the frame's (x, y, z) is written as (x, z, -y)."""
    m = build(params)
    tint = params.composition.get("tint") or {}
    bin_ = bytearray()
    views, accessors = [], []

    def view(data: bytes, target=None):
        nonlocal bin_
        off = len(bin_)
        bin_ += _pad(data)
        v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target:
            v["target"] = target
        views.append(v)
        return len(views) - 1

    def accessor(values, ctype, typ, comps, target, minmax=False):
        flat = [x for v in values for x in (v if comps > 1 else (v,))]
        fmt = {5126: "f", 5125: "I", 5123: "H"}[ctype]
        acc = {"bufferView": view(struct.pack(f"<{len(flat)}{fmt}", *flat), target),
               "componentType": ctype, "count": len(values), "type": typ}
        if minmax:
            acc["min"] = [struct.unpack("<f", struct.pack("<f", min(v[k] for v in values)))[0] for k in range(comps)]
            acc["max"] = [struct.unpack("<f", struct.pack("<f", max(v[k] for v in values)))[0] for k in range(comps)]
        accessors.append(acc)
        return len(accessors) - 1

    images, textures, image_of = [], [], {}
    materials, primitives, roles = [], [], {}
    for name in MATERIALS:   # fixed order: the same bytes every run
        pr = m.prims.get(name)
        if pr is None or not pr.idx:
            continue
        lib, fab, color, rough, role, extra = MATERIALS[name]
        color = tuple(round(c * t, 4) for c, t in zip(color, tint.get(name, (1.0, 1.0, 1.0))))
        mat = {"name": name, "pbrMetallicRoughness": {"baseColorFactor": [*color, extra.get("alpha", 1.0)],
                                                      "metallicFactor": 0.0, "roughnessFactor": rough}}
        if "alpha" in extra:
            mat["alphaMode"] = "BLEND"
        if color == (1.0, 1.0, 1.0) and "alpha" not in extra:
            del mat["pbrMetallicRoughness"]["baseColorFactor"]
        imgs = _images(name)
        for r_, src in imgs.items():
            if (fab, r_) not in image_of:
                images.append({"name": src.stem.removesuffix("_web"), "mimeType": "image/jpeg",
                               "bufferView": view(_image_bytes(src))})
                textures.append({"sampler": 0, "source": len(images) - 1})
                image_of[(fab, r_)] = len(textures) - 1
        if imgs:
            mat["pbrMetallicRoughness"]["baseColorTexture"] = {"index": image_of[(fab, "basecolor")], "texCoord": 0}
            mat["normalTexture"] = {"index": image_of[(fab, "normal")], "texCoord": 0}
        materials.append(mat)
        roles.setdefault(role, []).append(name)
        pos = [(round(p[0], 4), round(p[2], 4), round(-p[1], 4)) for p in pr.pos]
        nrm = [(round(n[0], 4), round(n[2], 4), round(-n[1], 4)) for n in pr.nrm]
        uv = [(round(u[0], 5), round(u[1], 5)) for u in pr.uv]
        primitives.append({
            "attributes": {"POSITION": accessor(pos, 5126, "VEC3", 3, 34962, True),
                           "NORMAL": accessor(nrm, 5126, "VEC3", 3, 34962),
                           "TEXCOORD_0": accessor(uv, 5126, "VEC2", 2, 34962),
                           "_CONFIDENCE": accessor(pr.conf, 5126, "SCALAR", 1, 34962)},
            "indices": accessor(pr.idx, 5123 if len(pos) < 65536 else 5125, "SCALAR", 1, 34963),
            "material": len(materials) - 1})
    name = f"{structure_id}__{phase_id}"
    extras = {"structure_id": structure_id, "phase_id": phase_id,
              "fire": {"roles": roles, **({"shell": shell} if shell else {})}}
    gltf = {"asset": {"version": "2.0", "generator": GENERATOR}, "scene": 0, "scenes": [{"nodes": [0]}],
            "nodes": [{"name": name, "mesh": 0, "extras": extras}],
            "meshes": [{"name": name, "primitives": primitives}], "materials": materials,
            "accessors": accessors, "bufferViews": views, "buffers": [{"byteLength": len(bin_)}]}
    if images:
        gltf |= {"images": images, "textures": textures,
                 "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}]}
    js = _pad(json.dumps(gltf, separators=(",", ":"), sort_keys=True).encode(), b" ")
    body = bytes(bin_)
    total = 12 + 8 + len(js) + 8 + len(body)
    return (struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<I4s", len(js), b"JSON") + js
            + struct.pack("<I4s", len(body), b"BIN\x00") + body)
