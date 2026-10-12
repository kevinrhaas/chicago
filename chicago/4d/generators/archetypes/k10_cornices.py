"""The K10 cornice kit: cornices, parapets, dormer faces and cresting, every piece real
geometry written straight to glTF.

TICKET T-2316 (piece 1 of T-1852, K10). The kit's sizes are data in
`data/components/prairie_1904/k10_cornices.json`; this module reads them and builds each
variant on a specimen wall the way T-2317 will build them on a house:

  bracketed cornice  a frieze, scrolled brackets at an even spacing (single or paired, a
                     raised frieze panel between pairs), a soffit and a crown
  entablature        architrave, frieze and a dentilled cornice
  balustrade         a crowning cornice, a plinth, turned balusters, pedestals, a rail
                     and urns
  shaped gable       a Dutch gable's outline, its coping swept along all of it and dying
                     into a kneeler at each eave, a finial at the apex
  dormer             a pedimented dormer standing on a roof slope over a bracketed eave:
                     face, cheeks and roof seated on the slope, a horizontal cornice
                     returned on the cheeks, a raking cornice of two stepped bands
  cresting           a ridge cap, and on it cast-iron posts, bars, C-scrolls and spears

A RUN TURNS ITS CORNERS. Every frieze, crown, coping and rail is one section swept along
the wall head and mitred at each corner, so a return is the same moulding carried round,
and a run ends by dying into a wall or by a capped return: never in the air. The pavilion
board most variants stand on is a block projecting from a taller wall behind it, so each
run turns two outside corners and dies into that wall at both ends.

Every piece RESTS on what carries it, as in K09 (whose mesh primitives this module
reuses): an open piece leaves its open edges lying on another surface, a closed piece
passes through its host's surface, and nothing lays a face on another face.
`tools/check_cornice_kit.py` measures all of it on the built geometry.

    python3 generators/archetypes/k10_cornices.py           write the specimen GLB
    python3 generators/archetypes/k10_cornices.py --check   refuse if it is stale
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from archetypes.k01_frontage import _add, _cross, _dot, _mul, _sub, _unit  # noqa: E402
from archetypes.k09_trim import Mesh, Piece, _pad, area2, box, lathe, prism, tube  # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / "data" / "components" / "prairie_1904" / "k10_cornices.json"
GENERATOR = "chicago-4d generators/archetypes/k10_cornices.py (K10, T-2316)"

X, Y, Z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)

# Role -> material, in a fixed order so the file is the same bytes every run.
ROLE_MATERIAL = {"wall": "masonry", "roof": "slate", "timber": "painted_timber", "metal": "pressed_metal",
                 "stone": "dressed_stone", "iron": "cast_iron", "backing": "backing", "ground": "ground"}
BOARD_ROLES = ("wall", "roof", "backing", "ground")
MATERIALS = {
    "masonry": {"color": (0.55, 0.36, 0.28), "roughness": 0.92, "metallic": 0.0},
    "slate": {"color": (0.24, 0.25, 0.28), "roughness": 0.8, "metallic": 0.0},
    "painted_timber": {"color": (0.86, 0.82, 0.72), "roughness": 0.7, "metallic": 0.0},
    "pressed_metal": {"color": (0.55, 0.58, 0.52), "roughness": 0.55, "metallic": 0.0},
    "dressed_stone": {"color": (0.74, 0.69, 0.60), "roughness": 0.85, "metallic": 0.0},
    "cast_iron": {"color": (0.07, 0.07, 0.075), "roughness": 0.6, "metallic": 0.6},
    "backing": {"color": (0.032, 0.028, 0.025), "roughness": 1.0, "metallic": 0.0},
    "ground": {"color": (0.36, 0.34, 0.30), "roughness": 1.0, "metallic": 0.0},
}


def seed_of(component_id: str, index: int, structure_id: str = "k10_cornice_kit") -> int:
    """K01's seed rule (k01_contract.json `seed`)."""
    return int(hashlib.sha256(f"{structure_id}|{component_id}|{index}".encode()).hexdigest()[:8], 16)


# -- builders ---------------------------------------------------------------------------------

def sweep(m: Mesh, path, U, profile, side=1.0, closed=False, caps=(False, False), cap_close=(), sgn=None):
    """K09's sweep, with two additions: a CLOSED section (its last point joined back to
    its first, so the piece is a solid tube), and a cap closed through extra section
    points (`cap_close`, appended to the ring) where the open section alone would close
    on a diagonal. Mitred at every vertex; open on its seat unless closed."""
    prof = list(profile) + ([profile[0]] if closed else [])
    segN = []
    for j in range(len(path) - 1):
        T = _unit(_sub(path[j + 1], path[j]))
        segN.append(_mul(_unit(_cross(T, U)), side))
    vN, vS = [], []
    for i in range(len(path)):
        if i == 0 or i == len(path) - 1:
            vN.append(segN[0 if i == 0 else -1])
            vS.append(1.0)
        else:
            N = _unit(_add(segN[i - 1], segN[i]))
            vN.append(N)
            vS.append(1.0 / max(0.2, _dot(N, segN[i - 1])))
    at = lambda i, n, u: _add(_add(path[i], _mul(vN[i], n * vS[i])), _mul(U, u))
    rings = [[at(i, n, u) for n, u in prof] for i in range(len(path))]
    if sgn is None:
        sgn = 1.0 if area2(profile) > 0 else -1.0
    for k in range(len(prof) - 1):
        en, eu = prof[k + 1][0] - prof[k][0], prof[k + 1][1] - prof[k][1]
        ln = math.hypot(en, eu) or 1.0
        on, ou = sgn * eu / ln, -sgn * en / ln
        for i in range(len(path) - 1):
            na = _unit(_add(_mul(vN[i], on), _mul(U, ou)))
            nb = _unit(_add(_mul(vN[i + 1], on), _mul(U, ou)))
            m.quad([rings[i][k], rings[i + 1][k], rings[i + 1][k + 1], rings[i][k + 1]], [na, nb, nb, na])
    for end, cap in zip((0, len(path) - 1), caps):
        if cap:
            ring = (rings[end][:-1] if closed else rings[end]) + [at(end, n, u) for n, u in cap_close]
            T = _unit(_sub(path[1], path[0])) if end == 0 else _unit(_sub(path[-1], path[-2]))
            m.poly(ring, _mul(T, -1) if end == 0 else T)
    return rings


class Run:
    """One straight stretch of wall head in plan: from `a` (x, z) along `t` for `L`,
    its face looking along `o`. `corners` says which ends turn an outside corner."""

    def __init__(self, name, a, b, corners):
        self.name, self.a, self.corners = name, a, corners
        d = (b[0] - a[0], b[1] - a[1])
        self.L = math.hypot(*d)
        self.t = (d[0] / self.L, 0.0, d[1] / self.L)
        self.o = (-self.t[2], 0.0, self.t[0])      # the outward side, left of travel seen from above

    def at(self, s, y, n=0.0):
        """The point `s` along the run at height y, `n` out from its face."""
        return (self.a[0] + self.t[0] * s + self.o[0] * n, y, self.a[1] + self.t[2] * s + self.o[2] * n)


def face_box(m: Mesh, run: Run, s0, s1, y0, y1, n0, n1, skip=()):
    """A box on a run's face: along it s0..s1, up y0..y1, out n0..n1; named faces skipped."""
    P = lambda s, y, n: run.at(s, y, n)
    faces = {
        "front": ([P(s0, y0, n1), P(s1, y0, n1), P(s1, y1, n1), P(s0, y1, n1)], run.o),
        "back": ([P(s0, y0, n0), P(s1, y0, n0), P(s1, y1, n0), P(s0, y1, n0)], _mul(run.o, -1)),
        "start": ([P(s0, y0, n0), P(s0, y0, n1), P(s0, y1, n1), P(s0, y1, n0)], _mul(run.t, -1)),
        "end": ([P(s1, y0, n0), P(s1, y0, n1), P(s1, y1, n1), P(s1, y1, n0)], run.t),
        "top": ([P(s0, y1, n0), P(s1, y1, n0), P(s1, y1, n1), P(s0, y1, n1)], Y),
        "bottom": ([P(s0, y0, n0), P(s1, y0, n0), P(s1, y0, n1), P(s0, y0, n1)], _mul(Y, -1)),
    }
    for k, (f, h) in faces.items():
        if k not in skip:
            m.poly(f, h)


def console(m: Mesh, run: Run, s, y_top, n0, w, h, pj, curl):
    """A scrolled bracket `s` along a run, its back on the face n0 out from the wall, its
    top under a soffit at y_top: an S in side view, open on the face and under the soffit."""
    ss = [i / 14 for i in range(15)]
    outline = [(0.0, 0.0)] + [(pj * (1 - curl * (3 * q * q - 2 * q ** 3)), -h * q) for q in ss] + [(0.0, -h)]
    P = lambda a, z_, y_: run.at(a, y_top + y_, n0 + z_)
    for a, sg in ((s - w / 2, -1.0), (s + w / 2, 1.0)):
        m.poly([P(a, z_, y_) for z_, y_ in outline], _mul(run.t, sg))
    ccw = area2(outline) > 0
    for k in range(len(outline)):
        A, B = outline[k], outline[(k + 1) % len(outline)]
        if (A[0] == 0.0 and B[0] == 0.0) or (A[1] == 0.0 and B[1] == 0.0):
            continue      # open against the frieze and under the soffit
        e = (B[0] - A[0], B[1] - A[1])
        nz, ny = (e[1], -e[0]) if ccw else (-e[1], e[0])
        hint = _add(_mul(run.o, nz), _mul(Y, ny))
        m.poly([P(s - w / 2, A[0], A[1]), P(s + w / 2, A[0], A[1]), P(s + w / 2, B[0], B[1]),
                P(s - w / 2, B[0], B[1])], hint)


def ribbon(center, width):
    """A flat strip `width` wide about a polyline, as one closed outline."""
    L, R = [], []
    for i, p in enumerate(center):
        a = center[max(0, i - 1)]
        b = center[min(len(center) - 1, i + 1)]
        d = (b[0] - a[0], b[1] - a[1])
        ln = math.hypot(*d) or 1.0
        nx, ny = -d[1] / ln * width / 2, d[0] / ln * width / 2
        L.append((p[0] + nx, p[1] + ny))
        R.append((p[0] - nx, p[1] - ny))
    return L + list(reversed(R))


def positions(L, c, spacing, corners):
    """Bracket (or pair) centres along a run of length L: one `c` from every corner end,
    evenly between at no more than `spacing`."""
    a, b = c, L - c
    if b - a < spacing / 2:
        return [b if corners[1] else (a if corners[0] else L / 2)]
    n = math.ceil((b - a) / spacing)
    return [a + (b - a) * i / n for i in range(n + 1)]


class Variant:
    def __init__(self, v, data, origin=(0.0, 0.0, 0.0), index=0):
        self.v, self.data, self.O = v, data, origin
        self.P = data["parts"]
        self.pieces: list[Piece] = []
        self.seed = seed_of(v["id"], index)
        self.meta: dict = {"runs": {}}
        self.role = v["material"]

    def piece(self, name, role, rests, host=None, **meta):
        p = Piece(name, role, rests, host, **meta)
        self.pieces.append(p)
        return p

    def profile(self, name):
        return [tuple(q) for q in self.P["profiles"][name]["points"]]

    # boards ----------------------------------------------------------------------------
    def pavilion(self, W, H, T, E=0.75, above=1.3):
        """A block W wide, H high, projecting T from a wall behind it that is wider by E
        each side and taller by `above`: its face, its two returns, its top (a flat deck),
        the wall behind, the ground. Returns the three runs of its wall head."""
        w = self.piece("wall", "wall", "board")
        m = w.mesh
        m.poly([(-W / 2, 0.0, 0.0), (W / 2, 0.0, 0.0), (W / 2, H, 0.0), (-W / 2, H, 0.0)], Z)
        for x, hx in ((-W / 2, -1.0), (W / 2, 1.0)):
            m.poly([(x, 0.0, 0.0), (x, H, 0.0), (x, H, -T), (x, 0.0, -T)], (hx, 0.0, 0.0))
        m.poly([(-W / 2, H, 0.0), (W / 2, H, 0.0), (W / 2, H, -T), (-W / 2, H, -T)], Y)
        xl, xh = -W / 2 - E, W / 2 + E
        m.poly([(xl, 0.0, -T), (xh, 0.0, -T), (xh, H + above, -T), (xl, H + above, -T)], Z)
        g = self.piece("ground", "ground", "board")
        g.mesh.poly([(xl, 0.0, -T), (xh, 0.0, -T), (xh, 0.0, 1.0), (xl, 0.0, 1.0)], Y)
        self.meta["panel"] = {"x": [xl, xh], "y": [0.0, H + above]}
        self.meta["head"] = H
        return [Run("left", (-W / 2, -T), (-W / 2, 0.0), (False, True)),
                Run("front", (-W / 2, 0.0), (W / 2, 0.0), (True, True)),
                Run("right", (W / 2, 0.0), (W / 2, -T), (True, False))]

    def gabled(self, W, H, D, pitch, E=0.3):
        """A block W wide, H to its eave, D deep, under a ridge along X at its mid-depth:
        its face, two gable-end walls, two roof slopes (one piece, `roof`), the ground."""
        tp = math.tan(math.radians(pitch))
        Hr = H + D / 2 * tp
        w = self.piece("wall", "wall", "board")
        w.mesh.poly([(-W / 2, 0.0, 0.0), (W / 2, 0.0, 0.0), (W / 2, H, 0.0), (-W / 2, H, 0.0)], Z)
        w.mesh.poly([(-W / 2, 0.0, -D), (W / 2, 0.0, -D), (W / 2, H, -D), (-W / 2, H, -D)], _mul(Z, -1))
        for x, hx in ((-W / 2, -1.0), (W / 2, 1.0)):
            w.mesh.poly([(x, 0.0, 0.0), (x, H, 0.0), (x, Hr, -D / 2), (x, H, -D), (x, 0.0, -D)], (hx, 0.0, 0.0))
        r = self.piece("roof", "roof", "board")
        r.mesh.poly([(-W / 2, H, 0.0), (W / 2, H, 0.0), (W / 2, Hr, -D / 2), (-W / 2, Hr, -D / 2)], (0.0, 1.0, tp))
        r.mesh.poly([(-W / 2, H, -D), (W / 2, H, -D), (W / 2, Hr, -D / 2), (-W / 2, Hr, -D / 2)], (0.0, 1.0, -tp))
        g = self.piece("ground", "ground", "board")
        g.mesh.poly([(-W / 2 - E, 0.0, -D), (W / 2 + E, 0.0, -D), (W / 2 + E, 0.0, 1.0), (-W / 2 - E, 0.0, 1.0)], Y)
        self.meta["panel"] = {"x": [-W / 2 - E, W / 2 + E], "y": [0.0, Hr]}
        self.meta["head"] = H
        self.meta["roof"] = {"H": H, "tan": tp, "ridge": Hr, "D": D}
        return Hr

    # parts -----------------------------------------------------------------------------
    def run_path(self, runs, y):
        return [runs[0].at(0.0, y)] + [r.at(r.L, y) for r in runs]

    def moulding(self, name, runs, y, profile, caps=False, cap_close=(), sgn=None, closed=False, rests="open",
                 host=None, role=None):
        """One section swept along every run at height y, mitred at the corners."""
        n_out = max(n for n, _ in profile)
        mid = runs[len(runs) // 2]
        p = self.piece(name, role or self.role, rests, host,
                       proj=None if closed else {"m": round(n_out, 6), "face_z": mid.a[1],
                                                 "cx": mid.a[0] + mid.L / 2, "half": mid.L / 2},
                       run_names=[r.name for r in runs])
        sweep(p.mesh, self.run_path(runs, y), Y, profile, side=1.0, closed=closed,
              caps=(caps, caps), cap_close=cap_close, sgn=sgn)
        return p

    def bracket_course(self, runs, y_soffit, n_face, frieze_h, paired=False):
        B = self.P["bracket"]
        w, h, pj, curl = B["width_m"], B["height_m"], B["projection_m"], B["curl"]
        offs = [-(B["pair_gap_m"] / 2 + w / 2), B["pair_gap_m"] / 2 + w / 2] if paired else [0.0]
        k = 0
        out = {}
        for r in runs:
            pos = positions(r.L, B["corner_m"], B["spacing_m"], r.corners)
            out[r.name] = pos
            self.meta["runs"][r.name] = {"L": r.L, "corners": list(r.corners), "brackets": pos}
            for s in pos:
                for d in offs:
                    k += 1
                    p = self.piece(f"bracket {k}", self.role, "open", bracket={"run": r.name, "s": s})
                    console(p.mesh, r, s + d, y_soffit, n_face, w, min(h, frieze_h), pj, curl)
        return out, (B["pair_gap_m"] / 2 + w if paired else w / 2)

    # variants --------------------------------------------------------------------------
    def build(self):
        getattr(self, "_" + self.v["kind"])()
        return self

    def _eave(self, runs, H, crown, caps, paired=False, panels=False):
        """Frieze, brackets and crown under a wall head at H."""
        F = self.P["frieze"]
        prof = self.profile(crown)
        ch = max(u for _, u in prof)
        ys = H - ch
        fp, fh = F["proud_m"], F["height_m"]
        self.moulding("frieze", runs, ys - fh, [(0.0, 0.0), (fp, 0.0), (fp, fh)], caps=caps, cap_close=[(0.0, fh)])
        self.moulding("crown", runs, ys, prof, caps=caps)
        pos, half = self.bracket_course(runs, ys, fp, fh, paired)
        if panels:
            FP = self.P["frieze_panel"]
            k = 0
            for r in runs:
                ps = pos[r.name]
                for a, b in zip(ps, ps[1:]):
                    s0, s1 = a + half + FP["gap_m"], b - half - FP["gap_m"]
                    if s1 - s0 < 0.05:
                        continue
                    k += 1
                    p = self.piece(f"frieze panel {k}", self.role, "open")
                    face_box(p.mesh, r, s0, s1, ys - fh + FP["inset_m"], ys - FP["inset_m"], fp, fp + FP["proud_m"],
                             skip=("back",))
        return ys

    def _bracketed(self):
        v = self.v
        runs = self.pavilion(v["width_m"], v["height_m"], v["depth_m"])
        self._eave(runs, v["height_m"], v["crown"], False, v["paired"], v["panels"])
        self.meta["focus"] = [0.0, v["height_m"] - 0.45, 0.0]

    def _entablature(self):
        v = self.v
        H = v["height_m"]
        runs = self.pavilion(v["width_m"], H, v["depth_m"])
        arch, cor = self.profile("entablature_architrave"), self.profile("entablature_cornice")
        ah, chh = max(u for _, u in arch), max(u for _, u in cor)
        fp, fh = v["frieze_proud_m"], v["frieze_height_m"]
        y_c = H - chh
        y_f = y_c - fh
        y_a = y_f - ah
        self.moulding("architrave", runs, y_a, arch)
        self.moulding("frieze", runs, y_f, [(fp, 0.0), (fp, fh)], sgn=1.0)
        self.moulding("cornice", runs, y_c, cor)
        D = self.P["dentil"]
        u0, u1 = D["band_u_m"]
        k = 0
        for r in runs:
            span = r.L - 2 * D["corner_m"]
            n = int(span // D["pitch_m"]) + 1
            s0 = (r.L - (n - 1) * D["pitch_m"]) / 2
            for i in range(n):
                s = s0 + i * D["pitch_m"]
                k += 1
                p = self.piece(f"dentil {k}", self.role, "open", dentil={"run": r.name, "s": s})
                face_box(p.mesh, r, s - D["width_m"] / 2, s + D["width_m"] / 2, y_c + u1 - D["height_m"], y_c + u1,
                         D["band_n_m"], D["band_n_m"] + D["depth_m"], skip=("back", "top"))
        self.meta["dentil_band"] = [y_c + u0, y_c + u1]
        self.meta["focus"] = [0.0, H - 0.6, 0.0]

    def _balustrade(self):
        v = self.v
        H = v["height_m"]
        runs = self.pavilion(v["width_m"], H, v["depth_m"])
        B = self.P["balustrade"]
        pt, ph, bh = B["plinth_m"], B["plinth_height_m"], B["baluster_height_m"]
        cor = self.profile("parapet_cornice")
        self.moulding("cornice", runs, H - max(u for _, u in cor), cor)
        self.moulding("plinth", runs, H, [(0.0, 0.0), (0.0, ph), (-pt, ph), (-pt, 0.0)])
        y0, y1 = H + ph, H + ph + bh
        rail = self.profile("rail")
        self.moulding("rail", runs, y1, rail, closed=True)
        W, T = v["width_m"], v["depth_m"]
        k = 0
        corners = [(-W / 2, -1.0), (W / 2, 1.0)]
        for cx, sx in corners:       # one pedestal at each front corner, shared by two runs
            k += 1
            p = self.piece(f"pedestal {k}", self.role, "open", pedestal="corner")
            x0, x1 = sorted((cx, cx - sx * pt))
            box(p.mesh, x0, x1, y0, y1, -pt, 0.0, skip=("bottom", "top"))
        bal = [(r, y) for r, y in B["baluster"]]
        nb = 0
        self.meta["balusters"] = []
        for r in runs:
            lo = pt if r.corners[0] else 0.0
            hi = r.L - (pt if r.corners[1] else 0.0)
            n_ped = max(0, math.ceil((hi - lo) / B["pedestal_spacing_max_m"]) - 1)
            peds = [lo + (hi - lo) * (i + 1) / (n_ped + 1) for i in range(n_ped)]
            edges = [lo]
            for s in peds:
                k += 1
                p = self.piece(f"pedestal {k}", self.role, "open", pedestal="run")
                pw = B["pedestal_m"]
                face_box(p.mesh, r, s - pw / 2, s + pw / 2, y0, y1, -pt, 0.0, skip=("bottom", "top"))
                edges += [s - pw / 2, s + pw / 2]
            edges.append(hi)
            for a, b in zip(edges[::2], edges[1::2]):
                n = max(1, round((b - a) / B["pitch_m"]))
                step = (b - a) / n
                xs = []
                for i in range(n):
                    s = a + step * (i + 0.5)
                    c = r.at(s, 0.0, -pt / 2)
                    nb += 1
                    p = self.piece(f"baluster {nb}", self.role, "open")
                    lathe(p.mesh, (c[0], c[2]), [(rr, y0 + bh * yy) for rr, yy in bal], B["segments"])
                    xs.append(s)
                self.meta["balusters"].append({"run": r.name, "step": step, "n": n})
        top = y1 + max(u for _, u in rail)
        for i, (cx, sx) in enumerate(corners):
            p = self.piece(f"urn {i + 1}", self.role, "open")
            lathe(p.mesh, (cx - sx * pt / 2, -pt / 2), [(rr, top + yy) for rr, yy in B["urn"]], B["segments"])
        self.meta["corner_pedestals"] = len(corners)
        self.meta["focus"] = [0.0, H + 0.35, 0.0]

    def _gable(self):
        v, G = self.v, self.P["gable"]
        W, E, T = v["width_m"], v["height_m"], v["thickness_m"]
        cop = self.profile("gable_coping")
        o = max(abs(u) for _, u in cop) - T / 2
        x0 = -W / 2 + G["kneeler_m"]
        x1 = x0 + G["shoulder_m"]
        yN = E + G["shoulder_rise_m"]
        yT = yN + G["neck_m"]
        half = [(x0, E), (x0 + 0.06, E)]
        # the shoulder resampled at an even arc length, never nearer the neck's inside corner
        # than the coping is deep: a mitre shorter than its own section folds the coping
        depth = max(n for n, _ in cop)
        dense = [(x0 + 0.06 + (x1 - x0 - 0.06) * q, E + G["shoulder_rise_m"] * (3 * q * q - 2 * q ** 3))
                 for q in (i / 400 for i in range(401))]
        arc = [0.0]
        for a, b in zip(dense, dense[1:]):
            arc.append(arc[-1] + math.dist(a, b))
        n_seg = max(2, round(arc[-1] / G["shoulder_step_m"]))
        for i in range(1, n_seg):
            target = arc[-1] * i / n_seg
            if arc[-1] - target < 1.4 * depth:
                break
            j = next(k for k, a in enumerate(arc) if a >= target)
            half.append(dense[j])
        half.append(dense[-1])
        half.append((x1, yT))
        span, rise = -2 * x1, G["cap_rise_m"]
        R = (span * span / 4 + rise * rise) / (2 * rise)
        cy = yT + rise - R
        a = math.asin(span / 2 / R)
        cap_arc = [(R * math.sin(-a + 2 * a * i / 16), cy + R * math.cos(-a + 2 * a * i / 16)) for i in range(1, 16)]
        path = half + cap_arc + [(-x, y) for x, y in reversed(half)]
        w = self.piece("wall", "wall", "board")
        m = w.mesh
        face = [(-W / 2, 0.0), (W / 2, 0.0), (W / 2, E)] + list(reversed(path)) + [(-W / 2, E)]
        m.poly([(x, y, 0.0) for x, y in face], Z)
        m.poly([(x, y, -T) for x, y in face], _mul(Z, -1))
        top = [(-W / 2, E)] + path + [(W / 2, E)]
        for (ax, ay), (bx, by) in zip(top, top[1:]):
            m.poly([(ax, ay, 0.0), (bx, by, 0.0), (bx, by, -T), (ax, ay, -T)], (-(by - ay), bx - ax, 0.0))
        for x, hx in ((-W / 2, -1.0), (W / 2, 1.0)):
            m.poly([(x, 0.0, 0.0), (x, E, 0.0), (x, E, -T), (x, 0.0, -T)], (hx, 0.0, 0.0))
        g = self.piece("ground", "ground", "board")
        g.mesh.poly([(-W / 2 - 0.4, 0.0, -T), (W / 2 + 0.4, 0.0, -T), (W / 2 + 0.4, 0.0, 1.0), (-W / 2 - 0.4, 0.0, 1.0)], Y)
        c = self.piece("coping", self.role, "open", run_names=["gable"])
        sweep(c.mesh, [(x, y, -T / 2) for x, y in path], Z, cop, side=-1.0)
        for i, sx in enumerate((-1.0, 1.0)):
            k = self.piece(f"kneeler {i + 1}", self.role, "rooted", host="wall")
            xa, xb = sorted((sx * (W / 2 + 0.03), sx * -x0))
            box(k.mesh, xa, xb, E - G["kneeler_sink_m"], E + G["kneeler_height_m"], -T - o, o)
        yA = yT + rise
        ridge = max(n for n, _ in cop)
        f = self.piece("finial", self.role, "rooted", host="coping")
        y0 = yA + ridge - G["finial_sink_m"]
        lathe(f.mesh, (0.0, -T / 2), [(r, y0 + y) for r, y in G["finial"]], 12)
        self.meta["panel"] = {"x": [-W / 2 - 0.4, W / 2 + 0.4], "y": [0.0, yA]}
        self.meta["head"] = E
        self.meta["gable"] = {"path": path, "T": T}
        self.meta["focus"] = [0.0, yT, 0.0]

    def _dormer(self):
        v, Dm = self.v, self.P["dormer"]
        W, H, D, pitch = v["width_m"], v["height_m"], v["depth_m"], v["roof_pitch_deg"]
        self.gabled(W, H, D, pitch)
        ret = v["eave_return_m"]
        runs = [Run("left return", (-W / 2, -ret), (-W / 2, 0.0), (False, True)),
                Run("front", (-W / 2, 0.0), (W / 2, 0.0), (True, True)),
                Run("right return", (W / 2, 0.0), (W / 2, -ret), (True, False))]
        self._eave(runs, H, v["crown"], True)
        # the dormer, on the front slope
        tp = math.tan(math.radians(pitch))
        s, wd, dh = Dm["set_back_m"], Dm["width_m"], Dm["face_height_m"]
        tq = math.tan(math.radians(Dm["pediment_pitch_deg"]))
        roof_y = lambda z: H - z * tp
        y_fb = roof_y(-s)
        y_d = y_fb + dh
        y_dr = y_d + wd / 2 * tq
        z_b = -(y_d - H) / tp
        z_r0 = -(y_dr - H) / tp
        zf = -s
        ww = Dm["window_width_m"]
        corn = self.profile("dormer_cornice")
        hc = max(u for _, u in corn)
        ys, yt = y_fb + Dm["sill_m"], y_d - hc - Dm["window_top_gap_m"]
        hole = [(-ww / 2, ys), (ww / 2, ys), (ww / 2, yt), (-ww / 2, yt)]
        on = {"on_roof": True}
        f = self.piece("dormer face", "timber", "open", **on)
        f.mesh.poly([(x, y, zf) for x, y in [(-wd / 2, y_fb), (wd / 2, y_fb), (wd / 2, y_d), (0.0, y_dr), (-wd / 2, y_d)]],
                    Z, holes=[[(x, y, zf) for x, y in hole]])
        rv = self.piece("dormer reveal", "timber", "open", **on)
        tube(rv.mesh, hole, zf, zf - Dm["recess_m"])
        bk = self.piece("dormer window back", "backing", "board", **on)
        bk.mesh.poly([(x, y, zf - Dm["recess_m"]) for x, y in hole], Z)
        ch = self.piece("dormer cheeks", "timber", "open", **on)
        for sx in (-1.0, 1.0):
            x = sx * wd / 2
            ch.mesh.poly([(x, y_fb, zf), (x, y_d, zf), (x, y_d, z_b)], (sx, 0.0, 0.0))
        rf = self.piece("dormer roof", "roof", "open", **on)
        for sx in (-1.0, 1.0):
            x = sx * wd / 2
            rf.mesh.poly([(0.0, y_dr, zf), (x, y_d, zf), (x, y_d, z_b), (0.0, y_dr, z_r0)], (sx * tq, 1.0, 0.0))
        rt = Dm["return_m"]
        druns = [Run("dormer left", (-wd / 2, zf - rt), (-wd / 2, zf), (False, True)),
                 Run("dormer front", (-wd / 2, zf), (wd / 2, zf), (True, True)),
                 Run("dormer right", (wd / 2, zf), (wd / 2, zf - rt), (True, False))]
        self.moulding("dormer cornice", druns, y_d - hc, corn, caps=True, role="timber")
        self.pieces[-1].meta.update(on)
        cq = math.sqrt(1 + tq * tq)        # 1 / cos q
        off = 0.0
        prev = None
        for i, band in enumerate(Dm["rake_bands"]):
            yo, yi = y_dr - off * cq, y_dr - (off + band["width_m"]) * cq
            xo, xi = (yo - y_d) / tq, (yi - y_d) / tq
            poly = [(-xo, y_d), (0.0, yo), (xo, y_d), (xi, y_d), (0.0, yi), (-xi, y_d)]
            opened = {2, 5} | ({0, 1} if prev is not None else set())
            p = self.piece(f"rake {'crown' if i == 0 else 'fascia'}", "timber", "open", **on)
            prism(p.mesh, poly, zf, zf + band["proud_m"], open_edges=opened)
            off += band["width_m"]
            prev = band
        self.meta["dormer"] = {"z_face": zf, "y_foot": y_fb, "y_eave": y_d, "y_ridge": y_dr, "z_valley": z_r0}
        self.meta["focus"] = [0.0, (H + y_dr) / 2, zf / 2]

    def _cresting(self):
        v, C = self.v, self.P["cresting"]
        W, H, D, pitch = v["width_m"], v["height_m"], v["depth_m"], v["roof_pitch_deg"]
        Hr = self.gabled(W, H, D, pitch)
        zr = -D / 2
        rc = self.piece("ridge cap", "metal", "rooted", host="roof")
        cap = self.profile("ridge_cap")
        sweep(rc.mesh, [(-W / 2 + 0.02, Hr, zr), (W / 2 - 0.02, Hr, zr)], Y, cap, closed=True, caps=(True, True))
        top_cap = max(u for _, u in cap)
        self.cresting(0.0, W - 0.4, Hr + top_cap, zr)
        self.meta["focus"] = [0.0, Hr + 0.15, zr]

    def cresting(self, xc, L, y_cap, zr, host="ridge cap"):
        """The iron cresting along X, centred on xc and L long, its base bar let 7 mm into
        a ridge cap whose top is at y_cap along z = zr (T-2317 lays it on a house's own
        ridge roll this way)."""
        C = self.P["cresting"]
        yb0 = y_cap - 0.007
        yb1 = yb0 + C["bar_height_m"]
        b = self.piece("base bar", "iron", "rooted", host=host)
        box(b.mesh, xc - L / 2, xc + L / 2, yb0, yb1, zr - C["bar_m"] / 2, zr + C["bar_m"] / 2)
        n = math.ceil(L / C["post_spacing_max_m"])
        posts = [xc - L / 2 + L * i / n for i in range(n + 1)]
        pm, ptop = C["post_m"] / 2, yb0 + 0.01 + C["post_height_m"]
        for i, x in enumerate(posts):
            p = self.piece(f"post {i + 1}", "iron", "rooted", host="base bar")
            box(p.mesh, x - pm, x + pm, yb0 + 0.01, ptop, zr - pm, zr + pm)
            f = self.piece(f"post finial {i + 1}", "iron", "rooted", host=f"post {i + 1}")
            lathe(f.mesh, (x, zr), [(r, ptop - 0.01 + y) for r, y in C["finial"]], 10)
        yt0 = yb0 + C["top_bar_y_m"]
        t = self.piece("top bar", "iron", "rooted", host="post 1")
        box(t.mesh, xc - L / 2, xc + L / 2, yt0, yt0 + C["top_bar_height_m"], zr - C["top_bar_m"] / 2, zr + C["top_bar_m"] / 2)
        th = C["iron_m"] / 2
        r0, turn, sw = C["scroll_radius_m"], C["scroll_turn"], C["scroll_width_m"]
        yc = yb1 + 0.1
        k = 0
        for xa, xb in zip(posts, posts[1:]):
            xm = (xa + xb) / 2
            for sx in (-1.0, 1.0):
                xs = xm + sx * 0.03
                line = [(xs, (yb0 + yb1) / 2), (xs, yc - 0.03)]
                for j in range(25):
                    q = j / 24
                    ang = math.pi - q * turn * math.pi
                    rr = r0 * (1 - 0.55 * q)
                    line.append((xs + sx * (r0 + rr * math.cos(ang)), yc + rr * math.sin(ang)))
                k += 1
                p = self.piece(f"scroll {k}", "iron", "rooted", host="base bar")
                prism(p.mesh, ribbon(line, sw), zr - th, zr + th, back=True)
            y1 = yb0 + C["spear_height_m"]
            sp = [(xm - 0.006, (yb0 + yb1) / 2), (xm + 0.006, (yb0 + yb1) / 2), (xm + 0.006, y1), (xm + 0.028, y1 + 0.012),
                  (xm, y1 + 0.075), (xm - 0.028, y1 + 0.012), (xm - 0.006, y1)]
            p = self.piece(f"spear {k // 2}", "iron", "rooted", host="base bar")
            prism(p.mesh, sp, zr - th, zr + th, back=True)
        self.meta["cresting"] = {"posts": posts, "L": L}
        return posts


def load() -> dict:
    return json.loads(DATA.read_text())


PANEL_GAP = 0.6


def build_variant(v: dict, data: dict, origin=(0.0, 0.0, 0.0), index: int = 0) -> Variant:
    return Variant(v, data, origin, index).build()


def place(var: Variant):
    """Move every piece by the variant's origin (the specimen lays the boards in a row)."""
    ox, oy, oz = var.O
    for p in var.pieces:
        p.mesh.pos = [(x + ox, y + oy, z + oz) for x, y, z in p.mesh.pos]
    return var


def build_kit(data: dict | None = None) -> list[Variant]:
    data = data or load()
    out, x = [], 0.0
    for i, v in enumerate(data["variants"]):
        probe = build_variant(v, data, index=i)
        lo, hi = probe.meta["panel"]["x"]
        probe.O = (x - lo, 0.0, 0.0)
        out.append(place(probe))
        x += (hi - lo) + PANEL_GAP
    return out


def triangles(var: Variant, include_board: bool = False) -> int:
    return sum(p.mesh.triangles() for p in var.pieces if include_board or p.role not in BOARD_ROLES)


# -- glTF -------------------------------------------------------------------------------------

def to_glb(kit: list[Variant], data: dict) -> bytes:
    bin_ = bytearray()
    views, accessors, meshes, nodes = [], [], [], []

    def view(blob: bytes, target):
        nonlocal bin_
        off = len(bin_)
        bin_ += _pad(blob)
        views.append({"buffer": 0, "byteOffset": off, "byteLength": len(blob), "target": target})
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

    mat_names = list(MATERIALS)
    materials_out = [{"name": f"k10_{n}", "pbrMetallicRoughness": {
        "baseColorFactor": [*[round(c, 4) for c in MATERIALS[n]["color"]], 1.0],
        "metallicFactor": MATERIALS[n]["metallic"], "roughnessFactor": MATERIALS[n]["roughness"]}} for n in mat_names]
    for var in kit:
        by_mat: dict[str, list[Mesh]] = {}
        for role in ROLE_MATERIAL:
            for p in var.pieces:
                if p.role == role and p.mesh.idx:
                    by_mat.setdefault(ROLE_MATERIAL[role], []).append(p.mesh)
        prims_out = []
        for name in mat_names:
            if name not in by_mat:
                continue
            pos, nrm, uv, conf, idx = [], [], [], [], []
            seen: dict = {}       # weld: one vertex per (position, normal, uv)
            for m in by_mat[name]:
                for i in m.idx:
                    key = (tuple(round(c, 5) for c in m.pos[i]), tuple(round(c, 4) for c in m.nrm[i]),
                           tuple(round(c, 4) for c in m.uv[i]))
                    if key not in seen:
                        seen[key] = len(pos)
                        pos.append(key[0])
                        nrm.append(key[1])
                        uv.append(key[2])
                        conf.append(m.conf[i])
                    idx.append(seen[key])
            ctype = 5123 if len(pos) < 65536 else 5125
            prims_out.append({"attributes": {
                "POSITION": accessor(pos, 5126, "VEC3", 3, 34962, True),
                "NORMAL": accessor(nrm, 5126, "VEC3", 3, 34962),
                "TEXCOORD_0": accessor(uv, 5126, "VEC2", 2, 34962),
                "_CONFIDENCE": accessor(conf, 5126, "SCALAR", 1, 34962)},
                "indices": accessor(idx, ctype, "SCALAR", 1, 34963),
                "material": mat_names.index(name)})
        meshes.append({"name": var.v["id"], "primitives": prims_out})
        top = max(q[1] for p in var.pieces for q in p.mesh.pos)
        nodes.append({"name": var.v["id"], "mesh": len(meshes) - 1, "extras": {
            "component_id": var.v["id"], "family": "cornice", "kind": var.v["kind"], "material": var.v["material"],
            "seed": var.seed, "origin": [round(c, 4) for c in var.O],
            "pieces": sum(1 for p in var.pieces if p.role not in BOARD_ROLES),
            "triangles_trim": triangles(var), "triangles_with_board": triangles(var, True),
            "head_m": round(var.meta["head"], 4), "focus": [round(c, 4) for c in var.meta["focus"]],
            "sockets": {"base": [0.0, 0.0, 0.0], "top": [0.0, round(top, 4), 0.0]}}})
    gltf = {
        "asset": {"version": "2.0", "generator": GENERATOR},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials_out,
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(bin_)}],
        "extras": {"k10": {"data": "data/components/prairie_1904/k10_cornices.json", "ticket": "T-2316",
                           "contract": "data/components/prairie_1904/k01_contract.json"}},
    }
    js = _pad(json.dumps(gltf, separators=(",", ":"), sort_keys=True).encode(), b" ")
    body = bytes(bin_)
    total = 12 + 8 + len(js) + 8 + len(body)
    return (struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<I4s", len(js), b"JSON") + js
            + struct.pack("<I4s", len(body), b"BIN\x00") + body)


def main(argv) -> int:
    data = load()
    blob = to_glb(build_kit(data), data)
    out = ROOT / data["specimen"]
    if "--check" in argv:
        if not out.exists() or out.read_bytes() != blob:
            print(f"FAIL {out.relative_to(ROOT)} is not what the generator builds from "
                  f"{DATA.relative_to(ROOT)}: run python3 generators/archetypes/k10_cornices.py")
            return 1
        print(f"ok   {out.relative_to(ROOT)} is the generator's bytes ({len(blob)} B)")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    print(f"wrote {out.relative_to(ROOT)} ({len(blob)} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
