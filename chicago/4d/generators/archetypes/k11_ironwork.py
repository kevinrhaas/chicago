"""The K11 ironwork kit: fences, a gate on piers, a boundary wall, an area grille, a stoop
rail and an iron-and-glass canopy, every member real geometry written straight to glTF.

TICKET T-2318 (piece 1 of T-1853, K11). The kit's sizes are data in
`data/components/prairie_1904/k11_ironwork.json`; this module reads them and builds each
variant on its own specimen board the way T-2319 will build them on a property:

  fence        a stone curb, square posts with acorn finials, flat rails, pickets through
               the rails, and either a spear on every picket or a band of C-scrolls
  gate         two stone piers under caps and urns, a walk gate hung on two pintle
               hinges and drawn part open into the yard, a latch keeper on the far pier,
               a run of spear fence from each pier to an end post
  wall         a brick boundary wall, piers, a saddleback coping between them, caps, urns
  grille       square bars let into a basement window's reveal through two flats
  rail         an iron rail on each side of a stone stoop: newels, a raked handrail and
               two balusters to a tread
  canopy       rafters let into the wall on quadrant brackets, a front beam, one sheet of
               glass falling away from the wall, glazing bars, tie rods

IRONWORK IS A FRAME OF MEMBERS THAT HOLD ONE ANOTHER. So, unlike K09's and K10's open
mouldings, nearly every piece here is a CLOSED solid that passes through what carries
it: a picket through its rail, a rail into its post, a post into its curb, a curb, a pier
and a wall past grade. `tools/check_ironwork_kit.py` measures that on the built
geometry (K09's `rooted` rule), along with the gate's swing, the opening it guards, the
fence's rhythm and the walking-distance floor below which a bar shimmers.

    python3 generators/archetypes/k11_ironwork.py           write the specimen GLB
    python3 generators/archetypes/k11_ironwork.py --check   refuse if it is stale
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

from archetypes.k01_frontage import _add, _mul, _sub  # noqa: E402
from archetypes.k09_trim import Mesh, Piece, _pad, area2, box, lathe, prism, tube  # noqa: E402
from archetypes.k10_cornices import ribbon  # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / "data" / "components" / "prairie_1904" / "k11_ironwork.json"
GENERATOR = "chicago-4d generators/archetypes/k11_ironwork.py (K11, T-2318)"

X, Y, Z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)

# Role -> material, in a fixed order so the file is the same bytes every run.
ROLE_MATERIAL = {"wall": "masonry", "stoop": "stoop_stone", "iron": "wrought_iron", "stone": "dressed_stone",
                 "brick": "brick", "glass": "glass", "backing": "backing", "ground": "ground"}
BOARD_ROLES = ("wall", "stoop", "backing", "ground")
MATERIALS = {
    "masonry": {"color": (0.55, 0.36, 0.28), "roughness": 0.92, "metallic": 0.0},
    "stoop_stone": {"color": (0.62, 0.58, 0.52), "roughness": 0.9, "metallic": 0.0},
    "wrought_iron": {"color": (0.07, 0.07, 0.075), "roughness": 0.6, "metallic": 0.6},
    "dressed_stone": {"color": (0.74, 0.69, 0.60), "roughness": 0.85, "metallic": 0.0},
    "brick": {"color": (0.50, 0.27, 0.20), "roughness": 0.9, "metallic": 0.0},
    "glass": {"color": (0.55, 0.63, 0.66), "roughness": 0.08, "metallic": 0.0, "alpha": 0.35},
    "backing": {"color": (0.032, 0.028, 0.025), "roughness": 1.0, "metallic": 0.0},
    "ground": {"color": (0.36, 0.34, 0.30), "roughness": 1.0, "metallic": 0.0},
}


def seed_of(component_id: str, index: int, structure_id: str = "k11_ironwork_kit") -> int:
    """K01's seed rule (k01_contract.json `seed`)."""
    return int(hashlib.sha256(f"{structure_id}|{component_id}|{index}".encode()).hexdigest()[:8], 16)


# -- builders ---------------------------------------------------------------------------------

def block(m: Mesh, o, U, V, W):
    """A closed parallelepiped from corner `o` spanned by U, V and W."""
    c = lambda i, j, k: _add(_add(_add(o, _mul(U, i)), _mul(V, j)), _mul(W, k))
    mid = c(0.5, 0.5, 0.5)
    for f in ([c(0, 0, 0), c(1, 0, 0), c(1, 1, 0), c(0, 1, 0)], [c(0, 0, 1), c(1, 0, 1), c(1, 1, 1), c(0, 1, 1)],
              [c(0, 0, 0), c(1, 0, 0), c(1, 0, 1), c(0, 0, 1)], [c(0, 1, 0), c(1, 1, 0), c(1, 1, 1), c(0, 1, 1)],
              [c(0, 0, 0), c(0, 1, 0), c(0, 1, 1), c(0, 0, 1)], [c(1, 0, 0), c(1, 1, 0), c(1, 1, 1), c(1, 0, 1)]):
        fc = tuple(sum(p[i] for p in f) / 4 for i in range(3))
        m.poly(f, _sub(fc, mid))


def slab_x(m: Mesh, outline, x0, x1):
    """A closed solid: an outline in the (z, y) plane carried along X from x0 to x1."""
    m.poly([(x1, y, z) for z, y in outline], X)
    m.poly([(x0, y, z) for z, y in outline], _mul(X, -1))
    s = 1.0 if area2(outline) > 0 else -1.0
    for i in range(len(outline)):
        (za, ya), (zb, yb) = outline[i], outline[(i + 1) % len(outline)]
        hint = (0.0, -s * (zb - za), s * (yb - ya))
        m.poly([(x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb)], hint)


def turn(m: Mesh, ax, az, th):
    """Rotate a mesh about the vertical axis through (ax, az) by th radians, so +X goes
    toward -Z (a gate leaf opening into the yard)."""
    c, s = math.cos(th), math.sin(th)
    m.pos = [(ax + (x - ax) * c + (z - az) * s, y, az - (x - ax) * s + (z - az) * c) for x, y, z in m.pos]
    m.nrm = [(x * c + z * s, y, -x * s + z * c) for x, y, z in m.nrm]


def even(a, b, pitch):
    """Centres evenly inside a..b at no more than `pitch`, none on either end."""
    n = max(1, math.ceil((b - a) / pitch) - 1)
    return [a + (b - a) * (i + 1) / (n + 1) for i in range(n)]


class Variant:
    def __init__(self, v, data, origin=(0.0, 0.0, 0.0), index=0):
        self.v, self.data, self.O = v, data, origin
        self.P = data["parts"]
        self.pieces: list[Piece] = []
        self.seed = seed_of(v["id"], index)
        self.meta: dict = {"rhythm": {}}
        self.n: dict = {}

    def piece(self, name, role, rests, host=None, **meta):
        p = Piece(name, role, rests, host, **meta)
        self.pieces.append(p)
        return p

    def name(self, kind):
        self.n[kind] = self.n.get(kind, 0) + 1
        return f"{kind} {self.n[kind]}"

    # boards ----------------------------------------------------------------------------
    def ground(self, x0, x1, z0=-1.2, z1=1.2):
        g = self.piece("ground", "ground", "board")
        g.mesh.poly([(x0, 0.0, z0), (x1, 0.0, z0), (x1, 0.0, z1), (x0, 0.0, z1)], Y)
        self.meta["panel"] = {"x": [x0, x1]}

    def wall_board(self, x0, x1, h, z=0.0, hole=None, depth=0.3):
        """A wall face at z; with a hole (x0, x1, y0, y1) a reveal `depth` deep and a dark back."""
        w = self.piece("wall", "wall", "board")
        outer = [(x0, 0.0, z), (x1, 0.0, z), (x1, h, z), (x0, h, z)]
        if hole:
            a, b, c, d = hole
            w.mesh.poly(outer, Z, holes=[[(a, c, z), (a, d, z), (b, d, z), (b, c, z)]])
            tube(w.mesh, [(a, c), (b, c), (b, d), (a, d)], z - depth, z)
            k = self.piece("backing", "backing", "board")
            k.mesh.poly([(a, c, z - depth), (b, c, z - depth), (b, d, z - depth), (a, d, z - depth)], Z)
        else:
            w.mesh.poly(outer, Z)
        return w

    # parts -----------------------------------------------------------------------------
    def member(self, name, role, host, x0, x1, y0, y1, z0, z1, **meta):
        p = self.piece(name, role, "rooted", host, **meta)
        box(p.mesh, x0, x1, y0, y1, z0, z1)
        return p

    def finial(self, host, cx, cz, y_top, profile, sink=0.02, role="iron", **meta):
        p = self.piece(self.name("finial"), role, "rooted", host, **meta)
        lathe(p.mesh, (cx, cz), [(r, y_top - sink + y) for r, y in profile], 12)
        return p

    def spear(self, host, cx, y_top, **meta):
        S = self.P["spear"]
        stub, b = 0.006, S["barb_m"] / 2
        y1 = y_top + 0.02
        out = [(cx - stub, y_top - 0.02), (cx + stub, y_top - 0.02), (cx + stub, y1), (cx + b, y1 - 0.005),
               (cx + 0.008, y1 + 0.03), (cx, y_top + S["height_m"]), (cx - 0.008, y1 + 0.03), (cx - b, y1 - 0.005),
               (cx - stub, y1)]
        p = self.piece(self.name("spear"), "iron", "rooted", host, **meta)
        prism(p.mesh, out, -S["thickness_m"] / 2, S["thickness_m"] / 2, back=True)
        return p

    def curb(self, x0, x1):
        C = self.P["curb"]
        return self.member(self.name("curb"), "stone", "ground", x0, x1, -C["sink_m"], C["height_m"],
                           -C["width_m"] / 2, C["width_m"] / 2)

    def post(self, x, curb_name, y_top):
        Q = self.P["post"]
        h = Q["section_m"] / 2
        y0 = self.P["curb"]["height_m"] - Q["sink_m"]
        p = self.member(self.name("post"), "iron", curb_name, x - h, x + h, y0, y_top, -h, h, post=True)
        self.finial(p.name, x, 0.0, y_top, Q["finial"])
        return p

    def panel(self, fa, fb, host, style, group, gate=False, y_base=None):
        """Rails, pickets and spears or scrolls between two faces fa < fb (a post's or a
        pier's), the rails let into both; returns the top of the pickets."""
        R, K, S = self.P["rail"], self.P["picket"], self.P["spear"]
        base = self.P["curb"]["height_m"] if y_base is None else y_base
        let, rh, rt = 0.02, R["height_m"], R["thickness_m"]
        yb, yt = base + R["bottom_m"], base + R["top_m"]
        bottom = self.member(self.name("bottom rail"), "iron", host, fa - let, fb + let, yb, yb + rh, -rt / 2, rt / 2,
                             gate=gate)
        self.member(self.name("top rail"), "iron", host, fa - let, fb + let, yt, yt + rh, -rt / 2, rt / 2, gate=gate)
        if style == "scroll":
            ym = yt - self.P["scroll"]["band_m"]
            self.member(self.name("band rail"), "iron", host, fa - let, fb + let, ym, ym + rh, -rt / 2, rt / 2,
                        gate=gate)
        s = K["section_m"]
        xs = even(fa, fb, K["pitch_m"])
        top = yt + rh + S["rise_m"] if style == "spear" else yt + rh - 0.01
        names = []
        for x in xs:
            p = self.member(self.name("picket"), "iron", bottom.name, x - s / 2, x + s / 2, yb + 0.01, top,
                            -s / 2, s / 2, rhythm=group, gate=gate)
            names.append(p.name)
            if style == "spear":
                self.spear(p.name, x, top, gate=gate)
        self.meta["rhythm"].setdefault(group, {"axis": 0, "member": s})
        if style == "scroll":
            C = self.P["scroll"]
            ym = yt - C["band_m"]
            yc = (ym + rh + yt) / 2
            for (xa, xb), nm in zip(zip(xs, xs[1:]), names):
                clear = xb - xa - s
                r0 = C["radius_of_clear"] * clear
                cx = xa + s / 2 + r0
                line = [(xa, yc)]
                for j in range(15):
                    q = j / 14
                    ang = math.pi - q * C["turn"] * math.pi
                    rr = r0 * (1 - 0.5 * q)
                    line.append((cx + rr * math.cos(ang), yc + rr * math.sin(ang)))
                p = self.piece(self.name("scroll"), "iron", "rooted", nm, gate=gate)
                prism(p.mesh, ribbon(line, C["ribbon_m"]), -C["iron_m"] / 2, C["iron_m"] / 2, back=True)
        return top

    def fence_run(self, x0, x1, style, group, host_a=None, host_b=None):
        """A run of fence on a curb from x0 to x1: a post at each end not let into a pier
        (`host_a` / `host_b`), posts between at no more than the data's panel length."""
        Q, R, S = self.P["post"], self.P["rail"], self.P["spear"]
        h = Q["section_m"] / 2
        y_post = self.P["curb"]["height_m"] + R["top_m"] + R["height_m"] + S["rise_m"] + S["height_m"] + 0.02
        ca = x0 - (0.05 if host_a else 0.12)
        cb = x1 + (0.05 if host_b else 0.12)
        curb = self.curb(ca, cb)
        ends = [x0 + (0 if host_a else h), x1 - (0 if host_b else h)]
        n = max(1, math.ceil((ends[1] - ends[0]) / Q["panel_max_m"]))
        xs = [ends[0] + (ends[1] - ends[0]) * i / n for i in range(n + 1)]
        faces, hosts = [], []
        for i, x in enumerate(xs):
            if (i == 0 and host_a) or (i == len(xs) - 1 and host_b):
                faces.append((x, x))
                hosts.append(host_a if i == 0 else host_b)
            else:
                p = self.post(x, curb.name, y_post)
                faces.append((x - h, x + h))
                hosts.append(p.name)
        for i in range(len(xs) - 1):
            self.panel(faces[i][1], faces[i + 1][0], hosts[i], style, f"{group} panel {i + 1}")
        return xs

    def pier(self, cx, urn=True, half=None, h=None, role="stone"):
        Pr = self.P["pier"]
        half = half or Pr["section_m"] / 2
        h = h or Pr["height_m"]
        p = self.member(self.name("pier"), role, "ground", cx - half, cx + half, -Pr["sink_m"], h, -half, half,
                        pier=True)
        o = Pr["cap_overhang_m"]
        cap = self.member(self.name("pier cap"), "stone", p.name, cx - half - o, cx + half + o,
                          h - Pr["cap_sink_m"], h - Pr["cap_sink_m"] + Pr["cap_height_m"], -half - o, half + o)
        if urn:
            self.finial(cap.name, cx, 0.0, h - Pr["cap_sink_m"] + Pr["cap_height_m"], Pr["urn"], sink=Pr["urn_sink_m"],
                        role="stone")
        return p

    # variants --------------------------------------------------------------------------
    def build(self):
        getattr(self, "_" + self.v["kind"])()
        return self

    def _fence(self):
        L = self.v["length_m"]
        self.ground(-L / 2 - 0.4, L / 2 + 0.4)
        self.fence_run(-L / 2, L / 2, self.v["style"], "pickets")
        self.meta["focus"] = [0.0, 0.8, 0.0]

    def _gate(self):
        v, G, Pr = self.v, self.P["gate"], self.P["pier"]
        c, ps, stub = v["clear_m"], Pr["section_m"], v["stub_m"]
        xa, xb = -c / 2, c / 2                     # the opening, between the piers' inner faces
        self.ground(xa - ps - stub - 0.5, xb + ps + stub + 0.5)
        p1 = self.pier(xa - ps / 2)
        p2 = self.pier(xb + ps / 2)
        self.fence_run(xa - ps - stub, xa - ps, "spear", "pickets left", host_b=p1.name)
        self.fence_run(xb + ps, xb + ps + stub, "spear", "pickets right", host_a=p2.name)
        # hinges: a pintle let into pier 1, a barrel on it, the leaf's hinge stile in both barrels
        hx = xa + G["hinge_offset_m"]
        hr, hh, pm = G["hinge_radius_m"], G["hinge_height_m"], G["pintle_m"] / 2
        for y in G["hinges"]:
            pin = self.member(self.name("pintle"), "iron", p1.name, xa - 0.06, hx, y - pm, y + pm, -pm, pm, gate=True)
            b = self.piece(self.name("hinge"), "iron", "rooted", pin.name, gate=True, hinge=True)
            lathe(b.mesh, (hx, 0.0), [(0.0, y - hh / 2), (hr, y - hh / 2), (hr, y + hh / 2), (0.0, y + hh / 2)], 12)
        k = G["keeper_proud_m"]
        self.member("latch keeper", "iron", p2.name, xb - k, xb + 0.06, 0.88, 0.92, -0.015, 0.015, gate=True)
        # the leaf, built shut in the fence line, then turned on its hinge axis
        before = len(self.pieces)
        sm, sd, rt = G["stile_m"] / 2, G["stile_depth_m"] / 2, G["rail_thickness_m"] / 2
        Lw = (xb - k - G["keeper_gap_m"]) - hx
        Hg = G["height_m"]
        self.member("hinge stile", "iron", "hinge 1", hx - sm, hx + sm, 0.06, Hg, -sd, sd, gate=True, leaf=True)
        x_l = hx + Lw
        rails = []
        for y in (0.1, 0.5, Hg - 0.08):
            rails.append(self.member(self.name("leaf rail"), "iron", "hinge stile", hx, x_l - sm, y, y + 0.04, -rt, rt,
                                     gate=True, leaf=True))
        self.member("latch stile", "iron", rails[-1].name, x_l - 2 * sm, x_l, 0.06, Hg, -sd, sd, gate=True, leaf=True)
        s, S = self.P["picket"]["section_m"], self.P["spear"]
        top = Hg + S["rise_m"]
        for x in even(hx + sm, x_l - 2 * sm, self.P["picket"]["pitch_m"]):
            p = self.member(self.name("picket"), "iron", rails[0].name, x - s / 2, x + s / 2, 0.11, top, -s / 2, s / 2,
                            gate=True, leaf=True, rhythm="leaf")
            self.spear(p.name, x, top, gate=True, leaf=True)
        self.meta["rhythm"]["leaf"] = {"axis": 0, "member": s}
        th = math.radians(G["drawn_deg"])
        for p in self.pieces[before:]:
            turn(p.mesh, hx, 0.0, th)
        self.meta["gate"] = {"opening": [xa, xb], "hinge": [hx, 0.0], "drawn_deg": G["drawn_deg"],
                             "pier": [xa - ps, xa, -ps / 2, ps / 2]}
        self.meta["focus"] = [0.0, 0.85, 0.0]

    def _wall(self):
        L, Wd = self.v["length_m"], self.P["wall"]
        t, H, ph = Wd["thickness_m"], Wd["height_m"], Wd["pier_m"] / 2
        self.ground(-L / 2 - 0.6, L / 2 + 0.6)
        w = self.member("wall", "brick", "ground", -L / 2, L / 2, -Wd["sink_m"], H, -t / 2, t / 2)
        n = math.ceil(L / Wd["pier_spacing_max_m"])
        xs = [-L / 2 + L * i / n for i in range(n + 1)]
        for i, x in enumerate(xs):
            self.pier(x, urn=i in (0, len(xs) - 1), half=ph, h=H + Wd["pier_rise_m"], role="brick")
        c = t / 2 + Wd["coping_overhang_m"]
        y0 = H - Wd["coping_sink_m"]
        prof = [(-c, y0), (c, y0), (c, H + Wd["coping_rise_m"] - 0.02), (0.0, H + Wd["coping_rise_m"] + Wd["coping_ridge_m"]),
                (-c, H + Wd["coping_rise_m"] - 0.02)]
        for a, b in zip(xs, xs[1:]):          # each bay's coping dies 60 mm into the pier at each end
            p = self.piece(self.name("coping"), "stone", "rooted", w.name, coping=True)
            slab_x(p.mesh, prof, a + ph - 0.06, b - ph + 0.06)
        self.meta["piers"] = xs
        self.meta["wall"] = {"t": t}
        self.meta["focus"] = [0.0, 1.2, 0.0]

    def _grille(self):
        v, G = self.v, self.P["grille"]
        a, b = -v["window_w_m"] / 2, v["window_w_m"] / 2
        c, d = v["sill_m"], v["sill_m"] + v["window_h_m"]
        self.ground(-1.1, 1.1, -1.2, 1.2)
        self.wall_board(-1.1, 1.1, 1.9, hole=(a, b, c, d))
        z1 = -G["set_back_m"]
        bm, li = G["bar_m"], G["let_in_m"]
        for x in even(a, b, G["pitch_m"]):
            self.member(self.name("bar"), "iron", "wall", x - bm / 2, x + bm / 2, c - li, d + li, z1 - bm, z1,
                        rhythm="bars")
        self.meta["rhythm"]["bars"] = {"axis": 0, "member": bm}
        ft = G["flat_thickness_m"]
        zf = z1 - bm / 2
        for q in G["flats"]:
            y = c + (d - c) * q
            self.member(self.name("flat"), "iron", "wall", a - li, b + li, y - G["flat_m"] / 2, y + G["flat_m"] / 2,
                        zf - ft / 2, zf + ft / 2)
        self.meta["focus"] = [0.0, (c + d) / 2, -0.05]

    def _rail(self):
        v, R = self.v, self.P["stair_rail"]
        N, r, t, w = v["risers"], v["riser_m"], v["tread_m"], v["width_m"]
        zl = -(N - 1) * t
        zw = zl - v["landing_m"]
        self.ground(-1.6, 1.6, zw, 1.2)
        self.wall_board(-1.6, 1.6, 2.6 + N * r, z=zw)
        out = [(0.0, -0.1), (0.0, r)]
        for i in range(1, N):
            out += [(-i * t, i * r), (-i * t, (i + 1) * r)]
        out += [(zw - 0.1, N * r), (zw - 0.1, -0.1)]
        st = self.piece("stoop", "stoop", "board")
        slab_x(st.mesh, out, -w / 2, w / 2)
        nose = lambda z: r + (-z) * r / t                 # the nosing line, on every nose
        tread = lambda z: min(N, math.floor(-z / t) + 1) * r
        Hr, nm, bm, rm, rw = R["height_m"], R["newel_m"] / 2, R["baluster_m"] / 2, R["rail_m"], R["rail_width_m"]
        z_n1, z_n2 = -t / 4, zl - t / 4
        for side, xr in (("left", -w / 2 + R["inset_m"]), ("right", w / 2 - R["inset_m"])):
            news = []
            for zn in (z_n1, z_n2):
                yt = nose(zn) + Hr + 0.12
                p = self.member(self.name("newel"), "iron", "stoop", xr - nm, xr + nm, tread(zn) - 0.05, yt,
                                zn - nm, zn + nm)
                self.finial(p.name, xr, zn, yt, self.P["post"]["finial"])
                news.append(p)
            S = (xr, nose(z_n1) + Hr, z_n1)
            E = (xr, nose(z_n2) + Hr, z_n2)
            U = _sub(E, S)
            ln = math.hypot(U[1], U[2])
            Wn = (0.0, -U[2] / ln, U[1] / ln)
            if Wn[1] < 0:
                Wn = _mul(Wn, -1)
            o = _sub(_sub(S, (rw / 2, 0.0, 0.0)), _mul(Wn, rm / 2))
            hr = self.piece(self.name("handrail"), "iron", "rooted", news[0].name)
            block(hr.mesh, o, U, (rw, 0.0, 0.0), _mul(Wn, rm))
            zs = [-(i * t + q * t) for i in range(N - 1) for q in (0.25, 0.75)][1:]
            for zb in zs:
                self.member(self.name("baluster"), "iron", "stoop", xr - bm, xr + bm, tread(zb) - 0.03, nose(zb) + Hr,
                            zb - bm, zb + bm, rhythm=f"balusters {side}")
            self.meta["rhythm"][f"balusters {side}"] = {"axis": 2, "member": 2 * bm}
        self.meta["focus"] = [0.0, 1.3, zl / 2]

    def _canopy(self):
        v, C = self.v, self.P["canopy"]
        W, y0, P = v["width_m"], v["height_m"], C["projection_m"]
        tp = math.tan(math.radians(C["pitch_deg"]))
        g = lambda z: y0 - z * tp                       # the underside of the glass
        self.ground(-W / 2 - 0.5, W / 2 + 0.5, -0.2, 1.8)
        self.wall_board(-W / 2 - 0.5, W / 2 + 0.5, y0 + 1.2)
        n = math.ceil((W - 0.2) / C["rafter_spacing_max_m"])
        xs = [-W / 2 + 0.1 + (W - 0.2) * i / n for i in range(n + 1)]
        ra, rb, D = C["rafter_m"] / 2, C["rib_m"] / 2, C["rafter_depth_m"]
        for x in xs:
            p = self.piece(self.name("rafter"), "iron", "rooted", "wall", rafter=True)
            slab_x(p.mesh, [(-0.03, g(-0.03) - D), (P, g(P) - D), (P, g(P) + 0.003), (-0.03, g(-0.03) + 0.003)],
                   x - ra, x + ra)
            yb, ze = y0 - C["rib_drop_m"], P - 0.04
            B = g(ze) - 0.05 - yb
            line = [(-0.03 + (ze + 0.03) * math.sin(f), yb + B * (1 - math.cos(f)))
                    for f in (math.pi / 2 * j / 16 for j in range(17))]
            q = self.piece(self.name("bracket"), "iron", "rooted", "wall")
            slab_x(q.mesh, ribbon(line, C["rib_width_m"]), x - rb, x + rb)
        gl = self.piece("glass", "glass", "rooted", "rafter 1", glass=True)
        gt = C["glass_m"]
        slab_x(gl.mesh, [(-0.02, g(-0.02)), (P + 0.04, g(P + 0.04)), (P + 0.04, g(P + 0.04) + gt), (-0.02, g(-0.02) + gt)],
               -W / 2, W / 2)
        beam = self.piece("front beam", "iron", "rooted", "rafter 1")
        slab_x(beam.mesh, [(P - 0.03, g(P) - 0.065), (P + 0.09, g(P) - 0.065), (P + 0.09, g(P) + 0.01),
                           (P - 0.03, g(P) + 0.01)], -W / 2 - 0.02, W / 2 + 0.02)
        nb = math.ceil(W / C["bar_spacing_max_m"])
        bh = C["bar_m"] / 2
        for i in range(nb + 1):
            x = -W / 2 + 0.03 + (W - 0.06) * i / nb
            p = self.piece(self.name("glazing bar"), "iron", "rooted", "glass")
            slab_x(p.mesh, [(-0.03, g(-0.03) + gt - 0.004), (P + 0.035, g(P + 0.035) + gt - 0.004),
                            (P + 0.035, g(P + 0.035) + gt + 0.025), (-0.03, g(-0.03) + gt + 0.025)], x - bh, x + bh)
        rm = C["rod_m"]
        for x in (xs[0], xs[-1]):
            S = (x, y0 + 0.75, -0.03)
            E = (x, g(P), P + 0.07)           # into the beam, in front of the glass's edge
            U = _sub(E, S)
            ln = math.hypot(U[1], U[2])
            Wn = (0.0, -U[2] / ln * rm, U[1] / ln * rm)
            p = self.piece(self.name("tie rod"), "iron", "rooted", "wall")
            block(p.mesh, _sub(_sub(S, (rm / 2, 0.0, 0.0)), _mul(Wn, 0.5)), U, (rm, 0.0, 0.0), Wn)
        self.meta["canopy"] = {"pitch_deg": C["pitch_deg"]}
        self.meta["focus"] = [0.0, y0 - 0.3, P / 2]


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
    materials_out = []
    for n in mat_names:
        M = MATERIALS[n]
        mat = {"name": f"k11_{n}", "pbrMetallicRoughness": {
            "baseColorFactor": [*[round(c, 4) for c in M["color"]], M.get("alpha", 1.0)],
            "metallicFactor": M["metallic"], "roughnessFactor": M["roughness"]}}
        if "alpha" in M:
            mat["alphaMode"] = "BLEND"
            mat["doubleSided"] = True
        materials_out.append(mat)
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
            "component_id": var.v["id"], "family": "ironwork", "kind": var.v["kind"],
            "seed": var.seed, "origin": [round(c, 4) for c in var.O],
            "pieces": sum(1 for p in var.pieces if p.role not in BOARD_ROLES),
            "triangles_trim": triangles(var), "triangles_with_board": triangles(var, True),
            "focus": [round(c, 4) for c in var.meta["focus"]],
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
        "extras": {"k11": {"data": "data/components/prairie_1904/k11_ironwork.json", "ticket": "T-2318",
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
                  f"{DATA.relative_to(ROOT)}: run python3 generators/archetypes/k11_ironwork.py")
            return 1
        print(f"ok   {out.relative_to(ROOT)} is the generator's bytes ({len(blob)} B)")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    print(f"wrote {out.relative_to(ROOT)} ({len(blob)} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
