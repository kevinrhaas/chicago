"""The K07 entrance kit: every door a real opening with a real way up to it, written to glTF.

TICKET T-2303 (piece 1 of T-1849, K07). The kit's sizes are data in
`data/components/prairie_1904/k07_entrances.json`; this module reads them and builds
each variant as the entrances T-2304 will put on the 1808 exemplar:

  the hole       cut through a wall panel, T-junction free, flat or arched
  reveal         jambs and head soffit in the wall's own body, outer face to frame;
                 the threshold closes the bottom (and floors a declared vestibule)
  frame          the door frame's face ring and its sight edges; no sill member
  leaves         one or two panelled leaves, rails and stiles at the frame's stop,
                 panels sunk behind them, standing just clear of the threshold
  glass          a transom, fanlight or glazed panel: K06's sash and glass
  backing        the hall behind any glass, carried back and capped
  hardware       knobs at the lock rail; strap hinges on a carriage leaf
  head           a flat lintel or arch band; a carriage opening's bearing lintel
  stair          a straight stone stoop between cheek walls, bowed stone steps, a
                 timber porch with its steps, or a basement area stair, every riser
                 equal and solved from the floor height, landing on the threshold
                 and standing on grade

WHY PURE PYTHON — the reasons k06_windows.py gives, and the same `Opening` faces:
the gate measures vertices (the landing at the floor, the foot on grade, equal
risers, closed steps, the walk clear), so this module writes them itself.

    python3 generators/archetypes/k07_entrances.py           write the specimen GLB
    python3 generators/archetypes/k07_entrances.py --check   refuse if it is stale
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from archetypes.k01_frontage import Prim  # noqa: E402
from archetypes.k06_windows import Head, Opening, Region, _pad, box, seed_of  # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / "data" / "components" / "prairie_1904" / "k07_entrances.json"
GENERATOR = "chicago-4d generators/archetypes/k07_entrances.py (K07, T-2303)"

Y = (0.0, 1.0, 0.0)
OUT = (0.0, 0.0, 1.0)

# Role -> material. A role is what the gate measures; a material is what a renderer
# binds. Fixed order: the file is the same bytes every run.
ROLE_MATERIAL = {
    "wall": "masonry", "reveal": "masonry",
    "threshold": "stone", "head": "stone", "landing": "stone", "tread": "stone", "riser": "stone",
    "stair_end": "stone", "cheek": "stone", "area_wall": "area_brick", "coping": "stone", "guard": "stone",
    "frame": "joinery", "leaf": "joinery", "sash_outer": "joinery",
    "glass_outer": "glass", "glass_leaf": "glass",
    "hardware": "iron", "backing": "backing",
    "deck": "porch_timber", "skirt": "porch_timber", "post": "porch_timber", "beam": "porch_timber",
    "porch_roof": "porch_timber", "step_timber": "porch_timber",
    "ground": "ground", "walk": "walk",
}
# The board, not the entrance: excluded from an entrance's costs and from the walk rule.
BOARD_ROLES = ("wall", "ground", "walk")
STAIR_TREADS = ("landing", "tread", "deck")


def materials(data: dict) -> dict:
    p = data["parts"]
    g = p["glass"]
    return {
        "masonry": {"color": (0.70, 0.62, 0.50), "roughness": 0.9},
        "stone": {"color": (0.66, 0.60, 0.52), "roughness": 0.85},
        "area_brick": {"color": (0.55, 0.30, 0.22), "roughness": 0.92},
        "joinery": {"color": (0.26, 0.15, 0.09), "roughness": 0.5},
        "glass": {"color": tuple(g["base_color"]), "roughness": g["roughness"],
                  "metallic": g["metallic"], "alpha": g["alpha"]},
        "iron": {"color": tuple(p["hardware"]["color"]), "roughness": 0.45, "metallic": 0.6},
        "backing": {"color": tuple(p["backing"]["color"]), "roughness": 1.0},
        "porch_timber": {"color": (0.84, 0.81, 0.72), "roughness": 0.7},
        "ground": {"color": (0.36, 0.34, 0.30), "roughness": 1.0},
        "walk": {"color": (0.58, 0.57, 0.54), "roughness": 0.95},
    }


def risers(height: float, stair: dict) -> tuple[int, float]:
    """Integer risers solved from a height: n = round(height / target), each height / n."""
    n = max(1, round(height / stair["riser_target_m"]))
    return n, height / n


class Entrance(Opening):
    """One variant built about its `threshold` socket: origin at the centre of the door
    opening on the outer face, at the floor it serves; +X along the wall, +Z out."""

    def __init__(self, variant: dict, data: dict, origin=(0.0, 0.0, 0.0), index: int = 0):
        super().__init__(variant, data, origin, index)
        self.seed = seed_of(variant["id"], index, "k07_entrance_kit")
        self.probes: list[tuple] = []    # (point, roles, what): a face of `roles` must hold the point
        self.sockets: dict = {}

    def Q(self, s, y, out):
        """s along the wall, y up, `out` in front of the outer face."""
        return self.P(s, y, -out)

    def quad(self, role, pts, hint):
        self.face(role, [self.Q(*p) for p in pts], hint)

    def probe(self, s, y, out, roles, what):
        self.probes.append((self.Q(s, y, out), tuple(roles), what))

    # the opening ----------------------------------------------------------------
    def build(self):
        v, p = self.v, self.data["parts"]
        W, H = v["clear_width_m"], v["clear_height_m"]
        s0, s1 = -W / 2, W / 2
        rev = v.get("reveal_depth_m", p["reveal_depth_m"]["value"])
        fr = p["frame"]
        f = fr["face_m"]
        kind = v["head"]
        if kind == "flat":
            head = Head("flat", s0, s1, H)
        else:
            ros = 0.125
            head = Head(kind, s0, s1, H - Head(kind, s0, s1, 0.0, ros).rise, ros)
        flat = kind == "flat"
        hole = Region(s0, s1, 0.0, top_y=H if flat else None, head=None if flat else head)
        outline = hole.outline()
        self.holes.append(outline)
        self.meta.update({"reveal_depth_m": rev, "head": {"kind": kind, "span_m": W, "rise_m": round(head.rise, 4),
                                                          "spring_m": round(head.spring, 4)},
                          "host_wall_m": v.get("host_wall_m", self.data["host_wall"]["thickness_m"])})
        # reveal: every edge but the bottom, which is the threshold's
        n = len(outline)
        c = (0.0, H / 2)
        for i in range(1, n):
            a, b = outline[i], outline[(i + 1) % n]
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            self.face("reveal", [self.P(a[0], a[1], 0), self.P(b[0], b[1], 0),
                                 self.P(b[0], b[1], rev), self.P(a[0], a[1], rev)], (c[0] - m[0], c[1] - m[1], 0.0))
        self.face("threshold", [self.P(s0, 0, 0), self.P(s1, 0, 0), self.P(s1, 0, rev), self.P(s0, 0, rev)], Y)
        # frame: a face ring with no foot, and its sight edges
        self.ring("frame", outline, hole.outline(f, f, 0, f), rev)
        self.tube("frame", hole.outline(f, f, 0, f), rev, rev + fr["depth_m"])
        day = Region(s0 + f, s1 - f, 0.0, top_y=H - f if flat else None, head=None if flat else head, head_inset=f)
        self.meta["daylight_s"] = [day.s0, day.s1]
        self._door(day, head, rev, fr)
        if v.get("carriage"):
            self._lintel(s0, s1, H, v["lintel"])
            self._guards(s0, s1)
        else:
            self._head_band([(s0, s1, head)], p["head_band"])
        kind = v["stair"]["kind"]
        if kind == "straight":
            self._stoop()
        elif kind == "bowed":
            self._bowed()
        elif kind == "porch":
            self._porch()
        elif kind == "area":
            self._area()
        self.meta["grade_m"] = self.grade()
        return self

    def grade(self) -> float:
        st = self.v["stair"]
        if st["kind"] == "area":
            return st["area_depth_m"]
        return -st.get("floor_m", 0.0)

    def _door(self, day: Region, head, rev, fr):
        v, p = self.v, self.data["parts"]
        stop, bar = p["stop_m"], p["transom_bar_m"]
        d = rev + stop
        sa, mu = p["sash"], p["muntin"]
        st = sa["stile_m"]
        top = day.top_y if head.kind == "flat" else head.spring
        has_glass = False
        if head.kind == "round":
            y_leaf = head.spring - bar
            self._bar(day, y_leaf, head.spring, d, rev + fr["depth_m"])
            fan = Region(day.s0, day.s1, head.spring, head=head, head_inset=fr["face_m"])
            self._fanlight(fan, head, d, v.get("fanlight_bars", 5), mu)
            has_glass = True
        elif v.get("transom_m"):
            t0 = top - v["transom_m"]
            y_leaf = t0 - bar
            self._bar(day, y_leaf, t0, d, rev + fr["depth_m"])
            reg = (Region(day.s0, day.s1, t0, top_y=day.top_y) if head.kind == "flat"
                   else Region(day.s0, day.s1, t0, head=head, head_inset=day.head_inset))
            self._sash("sash_outer", reg, d, sa, mu, (v.get("transom_lights", 1), 1), (st, st, st, st), "transom")
            has_glass = True
        else:
            if head.kind != "flat":
                raise ValueError(f"{v['id']}: an arched head needs a transom_m or a round fanlight")
            y_leaf = top
        nl = v["leaves"]
        w = (day.s1 - day.s0) / nl
        lf = p["leaf"]
        for k in range(nl):
            a, b = day.s0 + k * w, day.s0 + (k + 1) * w
            hinge = "left" if (nl == 1 or k == 0) else "right"
            has_glass |= self._leaf(a, b, lf["gap_m"], y_leaf, d, hinge)
        self.meta["leaf_top_m"] = round(y_leaf, 4)
        if has_glass:
            deepest = max(pn["depth_m"] for pn in self.panes)
            d_back = deepest + p["backing"]["depth_m"]
            outline = day.outline()
            self.tube("backing", outline, rev + fr["depth_m"], d_back)
            self.plane("backing", outline, d_back)
            self.meta["depth_backing_m"] = round(d_back, 4)

    def _bar(self, day, y0, y1, d, d1):
        self.plane("frame", box(day.s0, day.s1, y0, y1), d)
        self.face("frame", [self.P(day.s0, y0, d), self.P(day.s1, y0, d), self.P(day.s1, y0, d1),
                            self.P(day.s0, y0, d1)], (0.0, -1.0, 0.0))

    def _leaf(self, a, b, y0, y1, d, hinge) -> bool:
        """A panelled leaf: its framing at the stop, panels sunk behind; glazed rows glass."""
        v, p = self.v, self.data["parts"]
        lf = p["leaf"]
        cols, rows = v["panels"]
        st, ms = lf["stile_m"], lf["mid_stile_m"]
        rails_y = v.get("rails_y_m", [lf["lock_rail_y_m"]] * (rows - 1))
        if len(rails_y) != rows - 1:
            raise ValueError(f"{v['id']}: {rows} panel rows need {rows - 1} rails, not {len(rails_y)}")
        lr = lf["lock_rail_m"]
        ys = [y0, y0 + lf["bottom_rail_m"]]
        for ry in rails_y:
            ys += [ry - lr / 2, ry + lr / 2]
        ys += [y1 - lf["top_rail_m"], y1]
        pw = (b - a - 2 * st - (cols - 1) * ms) / cols
        xs = [a, a + st]
        for i in range(1, cols):
            xs += [a + st + i * pw + (i - 1) * ms, a + st + i * (pw + ms)]
        xs += [b - st, b]
        if any(q1 <= q0 for q0, q1 in zip(ys, ys[1:])) or pw <= 0:
            raise ValueError(f"{v['id']}: its leaf's rails and panels do not fit a {y1 - y0:.2f} m leaf")
        glazed = set(v.get("glazed_rows", []))
        rec = lf["panel_recess_m"]
        gs = p["glass"]["setback_m"]
        glass = False
        for i in range(len(xs) - 1):
            for j in range(len(ys) - 1):
                cell = box(xs[i], xs[i + 1], ys[j], ys[j + 1])
                panel = i % 2 == 1 and j % 2 == 1
                if not panel:
                    self.plane("leaf", cell, d)
                    continue
                row = j // 2
                depth = d + (gs if row in glazed else rec)
                self.tube("leaf", cell, d, depth)
                if row in glazed:
                    self.plane("glass_leaf", cell, depth)
                    self.panes.append({"sash": "leaf", "poly": cell, "depth_m": depth, "col": i // 2, "row": row})
                    glass = True
                else:
                    self.plane("leaf", cell, depth)
        # the leaf's foot, which the gap leaves open to view
        self.face("leaf", [self.P(a, y0, d), self.P(b, y0, d), self.P(b, y0, d + lf["thickness_m"]),
                           self.P(a, y0, d + lf["thickness_m"])], (0.0, -1.0, 0.0))
        hw = p["hardware"]
        k = hw["knob_m"] / 2
        ky = lf["lock_rail_y_m"]
        kx = (b - hw["knob_from_edge_m"]) if hinge == "left" else (a + hw["knob_from_edge_m"])
        knob = box(kx - k, kx + k, ky - k, ky + k)
        self.plane("hardware", knob, d - hw["knob_proud_m"])
        self.tube("hardware", knob, d, d - hw["knob_proud_m"], inward=False)
        if self.v.get("carriage"):
            sw, sp = hw["strap_width_m"], hw["strap_proud_m"]
            for hy in (y0 + 0.35, (y0 + y1) / 2, y1 - 0.35):
                xa, xb = (a + 0.02, a + 0.02 + hw["strap_length_m"]) if hinge == "left" else \
                    (b - 0.02 - hw["strap_length_m"], b - 0.02)
                strap = box(xa, xb, hy - sw / 2, hy + sw / 2)
                self.plane("hardware", strap, d - sp)
                self.tube("hardware", strap, d, d - sp, inward=False)
        return glass

    def _lintel(self, s0, s1, H, ln):
        b, h, pr = ln["bearing_m"], ln["height_m"], ln["proud_m"]
        self.proud("head", box(s0 - b, s1 + b, H, H + h), pr)
        self.meta["lintel"] = {"s": [s0 - b, s1 + b], "y": [H, H + h]}

    def _guards(self, s0, s1):
        g = self.data["parts"]["guard_stone"]
        w, pr, h = g["width_m"], g["proud_m"], g["height_m"]
        for a, b, side in ((s0 - w, s0, -1.0), (s1, s1 + w, 1.0)):
            self.quad("guard", [(a, h, 0), (b, h, 0), (b, h, pr), (a, h, pr)], Y)
            self.quad("guard", [(a, 0, pr), (b, 0, pr), (b, h, pr), (a, h, pr)], OUT)
            for x, hx in ((a, -1.0), (b, 1.0)):
                self.quad("guard", [(x, 0, 0), (x, 0, pr), (x, h, pr), (x, h, 0)], (hx, 0.0, 0.0))

    # the stairs -----------------------------------------------------------------
    def _flight(self, sa, sb, y0, out0, n, r, g, sign, ends, end_role="stair_end", tread_role="tread",
                riser_role="riser", end_floor=None):
        """n risers from y0, the first at out0, each `g` further out; sign -1 descends
        (a stoop, risers facing the street), +1 climbs (an area stair, facing the door)."""
        rn = (0.0, 0.0, 1.0 if sign < 0 else -1.0)
        for k in range(1, n + 1):
            a = out0 + (k - 1) * g
            ya, yb = y0 + sign * (k - 1) * r, y0 + sign * k * r
            lo, hi = min(ya, yb), max(ya, yb)
            self.quad(riser_role, [(sa, lo, a), (sb, lo, a), (sb, hi, a), (sa, hi, a)], rn)
            self.probe((sa + sb) / 2, (lo + hi) / 2, a, (riser_role,), f"riser {k}")
            if k == n:
                break
            yt = yb
            self.quad(tread_role, [(sa, yt, a), (sb, yt, a), (sb, yt, a + g), (sa, yt, a + g)], Y)
            self.probe((sa + sb) / 2, yt, a + g / 2, (tread_role,), f"tread {k}")
            if ends:
                for x, hx in ((sa, -1.0), (sb, 1.0)):
                    self.quad(end_role, [(x, end_floor, a), (x, end_floor, a + g), (x, yt, a + g), (x, yt, a)],
                              (hx, 0.0, 0.0))
            ym = (end_floor + yt) / 2 if end_floor is not None else yt / 2
            for x in (sa, sb):
                self.probe(x, ym, a + g / 2, (end_role,) if ends else ("cheek", "area_wall"),
                           f"the end of step {k}")
        return out0 + (n - 1) * g

    def _stoop(self):
        st = self.v["stair"]
        p = self.data["parts"]
        R = st["floor_m"]
        n, r = risers(R, p["stair"])
        g, L, half = st["going_m"], st["landing_m"], st["width_m"] / 2
        cheeks = st.get("cheeks", False)
        self.quad("landing", [(-half, 0, 0), (half, 0, 0), (half, 0, L), (-half, 0, L)], Y)
        self.probe(0.0, 0.0, L / 2, ("landing",), "the landing")
        if not cheeks:
            for x, hx in ((-half, -1.0), (half, 1.0)):
                self.quad("stair_end", [(x, -R, 0), (x, -R, L), (x, 0, L), (x, 0, 0)], (hx, 0.0, 0.0))
        F = self._flight(-half, half, 0.0, L, n, r, g, -1, not cheeks, end_floor=-R)
        self.meta["stair"] = {"risers": n, "riser_m": round(r, 5), "going_m": g, "foot_out_m": round(F, 4)}
        if cheeks:
            ch = p["cheek"]
            t, hc = ch["thickness_m"], ch["above_nosing_m"]
            yF = -(n - 1) * r + hc
            for sgn in (-1.0, 1.0):
                si, so = sgn * half, sgn * (half + t)
                prof = [(0, -R), (F, -R), (F, yF), (L, hc), (0, hc)]
                self.quad("cheek", [(si, y, o) for o, y in prof], (-sgn, 0.0, 0.0))
                self.quad("cheek", [(so, y, o) for o, y in prof], (sgn, 0.0, 0.0))
                self.quad("cheek", [(si, hc, 0), (so, hc, 0), (so, hc, L), (si, hc, L)], Y)
                self.quad("cheek", [(si, hc, L), (so, hc, L), (so, yF, F), (si, yF, F)], (0.0, g, r))
                self.quad("cheek", [(si, -R, F), (so, -R, F), (so, yF, F), (si, yF, F)], OUT)
                mid = sgn * (half + t / 2)
                top = (mid, hc, L - 0.15)
                foot = (mid, hc - (F - 0.15 - L) * r / g, F - 0.15)
                self.sockets[f"handrail_{'left' if sgn < 0 else 'right'}"] = [top, foot]
                for pt in (top, foot):
                    self.probe(*pt, ("cheek",), "a handrail socket on its cheek")

    def _bowed(self):
        st = self.v["stair"]
        R = st["floor_m"]
        n, r = risers(R, self.data["parts"]["stair"])
        g, L = st["going_m"], st["landing_m"]
        th = math.radians(st["half_angle_deg"])
        c = st["centre_behind_m"]
        rho = [c + L + k * g for k in range(n)]           # rho[k-1]: riser k's radius
        m = 10
        phis = [-th + 2 * th * i / m for i in range(m + 1)]
        pt = lambda rr, ph: (rr * math.sin(ph), -c + rr * math.cos(ph))   # (s, out)
        r_wall = c / math.cos(th)
        land = [(-c * math.tan(th), 0.0)] + [pt(rho[0], ph) for ph in phis] + [(c * math.tan(th), 0.0)]
        self.quad("landing", [(s, 0, o) for s, o in land], Y)
        self.probe(0.0, 0.0, L / 2, ("landing",), "the landing")
        self.meta["landing_half_width_at_wall_m"] = round(c * math.tan(th), 4)
        for k in range(1, n + 1):
            ya, yb = -(k - 1) * r, -k * r
            rr = rho[k - 1]
            for i in range(m):
                (sa, oa), (sb, ob) = pt(rr, phis[i]), pt(rr, phis[i + 1])
                pm = (phis[i] + phis[i + 1]) / 2
                self.quad("riser", [(sa, yb, oa), (sb, yb, ob), (sb, ya, ob), (sa, ya, oa)],
                          (math.sin(pm), 0.0, math.cos(pm)))
            self.probe(0.0, (ya + yb) / 2, rr - c, ("riser",), f"riser {k}")
            if k == n:
                break
            r2 = rho[k]
            for i in range(m):
                q = [pt(rr, phis[i]), pt(rr, phis[i + 1]), pt(r2, phis[i + 1]), pt(r2, phis[i])]
                self.quad("tread", [(s, yb, o) for s, o in q], Y)
            self.probe(0.0, yb, (rr + r2) / 2 - c, ("tread",), f"tread {k}")
        # the ends: radial faces at +-theta, one per step, from grade to its top
        for k in range(0, n):
            ra, rb = (r_wall, rho[0]) if k == 0 else (rho[k - 1], rho[k])
            yt = -k * r
            for sg in (-1.0, 1.0):
                ph = sg * th
                (sa, oa), (sb, ob) = pt(ra, ph), pt(rb, ph)
                hint = (sg * math.cos(th), 0.0, -math.sin(th))
                self.quad("stair_end", [(sa, -R, oa), (sb, -R, ob), (sb, yt, ob), (sa, yt, oa)], hint)
                (sm, om) = pt((ra + rb) / 2, ph)
                self.probe(sm, (yt - R) / 2, om, ("stair_end",), f"the end of step {k}")
        F = rho[n - 1] - c
        self.meta["stair"] = {"risers": n, "riser_m": round(r, 5), "going_m": g, "foot_out_m": round(F, 4)}

    def _porch(self):
        st = self.v["stair"]
        p = self.data["parts"]
        pp = p["porch"]
        R = st["floor_m"]
        n, r = risers(R, p["stair"])
        g, D, hw = st["going_m"], st["deck_m"], st["deck_width_m"] / 2
        hs = st["step_width_m"] / 2
        dt, ss = pp["deck_thickness_m"], pp["skirt_set_m"]
        self.quad("deck", [(-hw, 0, 0), (hw, 0, 0), (hw, 0, D), (-hw, 0, D)], Y)
        self.probe(0.0, 0.0, D / 2, ("deck",), "the porch deck")
        for a, b in ((-hw, -hs), (hs, hw)):
            self.quad("deck", [(a, -dt, D), (b, -dt, D), (b, 0, D), (a, 0, D)], OUT)
        for x, hx in ((-hw, -1.0), (hw, 1.0)):
            self.quad("deck", [(x, -dt, 0), (x, -dt, D), (x, 0, D), (x, 0, 0)], (hx, 0.0, 0.0))
        down = (0.0, -1.0, 0.0)
        self.quad("deck", [(-hw, -dt, D - ss), (hw, -dt, D - ss), (hw, -dt, D), (-hw, -dt, D)], down)
        for a, b in ((-hw, -hw + ss), (hw - ss, hw)):
            self.quad("deck", [(a, -dt, 0), (b, -dt, 0), (b, -dt, D - ss), (a, -dt, D - ss)], down)
        ks = hw - ss
        self.quad("skirt", [(-ks, -R, D - ss), (ks, -R, D - ss), (ks, -dt, D - ss), (-ks, -dt, D - ss)], OUT)
        for x, hx in ((-ks, -1.0), (ks, 1.0)):
            self.quad("skirt", [(x, -R, 0), (x, -R, D - ss), (x, -dt, D - ss), (x, -dt, 0)], (hx, 0.0, 0.0))
        F = self._flight(-hs, hs, 0.0, D, n, r, g, -1, True, end_role="step_timber", tread_role="step_timber",
                         riser_role="step_timber", end_floor=-R)
        self.meta["stair"] = {"risers": n, "riser_m": round(r, 5), "going_m": g, "foot_out_m": round(F, 4)}
        # posts, beam and the porch's roof deck
        ps, pi, ph = pp["post_m"], pp["post_inset_m"], st["post_height_m"]
        bw, bh = pp["beam_m"]
        oc = D - pi - ps / 2
        xs0, xs1 = -hw + pi + ps / 2, hw - pi - ps / 2
        npst = st["posts"]
        for i in range(npst):
            x = xs0 + (xs1 - xs0) * i / (npst - 1)
            a, b, o0, o1 = x - ps / 2, x + ps / 2, oc - ps / 2, oc + ps / 2
            self.quad("post", [(a, 0, o1), (b, 0, o1), (b, ph, o1), (a, ph, o1)], OUT)
            self.quad("post", [(a, 0, o0), (b, 0, o0), (b, ph, o0), (a, ph, o0)], (0.0, 0.0, -1.0))
            for xx, hx in ((a, -1.0), (b, 1.0)):
                self.quad("post", [(xx, 0, o0), (xx, 0, o1), (xx, ph, o1), (xx, ph, o0)], (hx, 0.0, 0.0))
            self.probe(x, ph / 2, o1, ("post",), f"post {i + 1}")
        ba, bb, b0, b1 = -hw + pi, hw - pi, oc - bw / 2, oc + bw / 2
        yb0, yb1 = ph, ph + bh
        self.quad("beam", [(ba, yb0, b1), (bb, yb0, b1), (bb, yb1, b1), (ba, yb1, b1)], OUT)
        self.quad("beam", [(ba, yb0, b0), (bb, yb0, b0), (bb, yb1, b0), (ba, yb1, b0)], (0.0, 0.0, -1.0))
        self.quad("beam", [(ba, yb0, b0), (bb, yb0, b0), (bb, yb0, b1), (ba, yb0, b1)], down)
        for xx, hx in ((ba, -1.0), (bb, 1.0)):
            self.quad("beam", [(xx, yb0, b0), (xx, yb0, b1), (xx, yb1, b1), (xx, yb1, b0)], (hx, 0.0, 0.0))
        ov, rt = pp["roof_overhang_m"], pp["roof_thickness_m"]
        ra, rb, ro = -hw - ov, hw + ov, D + ov
        y0, y1 = yb1, yb1 + rt
        self.quad("porch_roof", [(ra, y1, 0), (rb, y1, 0), (rb, y1, ro), (ra, y1, ro)], Y)
        self.quad("porch_roof", [(ra, y0, 0), (rb, y0, 0), (rb, y0, ro), (ra, y0, ro)], down)
        self.quad("porch_roof", [(ra, y0, ro), (rb, y0, ro), (rb, y1, ro), (ra, y1, ro)], OUT)
        for xx, hx in ((ra, -1.0), (rb, 1.0)):
            self.quad("porch_roof", [(xx, y0, 0), (xx, y0, ro), (xx, y1, ro), (xx, y1, 0)], (hx, 0.0, 0.0))
        self.meta["porch"] = {"roof_y_m": [y0, y1], "beam_y_m": [yb0, yb1], "post_top_m": ph,
                              "extent_s": [ra, rb], "extent_out_m": ro}

    def _area(self):
        st = self.v["stair"]
        p = self.data["parts"]
        R = st["area_depth_m"]
        n, r = risers(R, p["stair"])
        g, A, hw = st["going_m"], st["landing_m"], st["width_m"] / 2
        self.quad("landing", [(-hw, 0, 0), (hw, 0, 0), (hw, 0, A), (-hw, 0, A)], Y)
        self.probe(0.0, 0.0, A / 2, ("landing",), "the area floor")
        F = self._flight(-hw, hw, 0.0, A, n, r, g, +1, False)
        self.meta["stair"] = {"risers": n, "riser_m": round(r, 5), "going_m": g, "foot_out_m": round(F, 4)}
        ar = p["area"]
        t, cp = ar["wall_m"], ar["coping_m"]
        top = R + cp
        for sgn in (-1.0, 1.0):
            si, so = sgn * hw, sgn * (hw + t)
            self.quad("area_wall", [(si, 0, 0), (si, 0, F), (si, top, F), (si, top, 0)], (-sgn, 0.0, 0.0))
            self.quad("coping", [(si, top, 0), (so, top, 0), (so, top, F), (si, top, F)], Y)
            self.quad("coping", [(so, R, 0), (so, R, F), (so, top, F), (so, top, 0)], (sgn, 0.0, 0.0))
            self.quad("coping", [(si, R, F), (so, R, F), (so, top, F), (si, top, F)], OUT)
            mid = sgn * (hw + t / 2)
            sk = [(mid, top, 0.15), (mid, top, F - 0.15)]
            self.sockets[f"handrail_{'left' if sgn < 0 else 'right'}"] = sk
            for q in sk:
                self.probe(*q, ("coping",), "a handrail socket on its coping")
        self.meta["area"] = {"s": [-hw - t, hw + t], "inner_s": [-hw, hw], "out_m": F}


# -- the specimen board: each variant in its own wall panel ----------------------------------

PANEL_PAD = 0.6
PANEL_GAP = 1.6
WALK_M = 1.6


def wall_panel(o: Entrance):
    """The board's wall around the door, its returns and back, the ground and the walk."""
    v = o.v
    outline = o.holes[0]
    xs = [q[0] for q in outline]
    s0, s1 = min(xs), max(xs)
    grade = o.meta["grade_m"]
    area = o.meta.get("area")
    built = [q for r, pr in o.prims.items() if r not in BOARD_ROLES for q in pr.pos]
    s_lo = min(q[0] for q in built) - o.O[0] - PANEL_PAD
    s_hi = max(q[0] for q in built) - o.O[0] + PANEL_PAD
    apex = max(q[1] for q in outline)
    y_hi = max(apex + 0.8, max(q[1] for q in built) - o.O[1] + 0.4)
    y_lo = min(grade, 0.0)
    spring = outline[2][1]
    isflat = len(outline) == 4
    xb = {s_lo, s_hi, s0, s1}
    yb = {y_lo, y_hi, 0.0, spring}
    if area:
        xb |= set(area["inner_s"])
        yb.add(grade)
    xb, yb = sorted(xb), sorted(yb)
    for i in range(len(xb) - 1):
        for j in range(len(yb) - 1):
            sc, yc = (xb[i] + xb[i + 1]) / 2, (yb[j] + yb[j + 1]) / 2
            if s0 < sc < s1 and 0 < yc < spring:
                continue
            if s0 < sc < s1 and yc > spring and not isflat:
                continue      # over an arch: the curve strips below fill it
            if area and yc < grade and not (area["inner_s"][0] < sc < area["inner_s"][1]):
                continue      # below grade, outside the area: in the ground
            o.plane("wall", box(xb[i], xb[i + 1], yb[j], yb[j + 1]), 0.0)
    if not isflat:
        top = outline[2:]
        for k in range(len(top) - 1):
            p, q = top[k], top[k + 1]
            o.plane("wall", [(q[0], q[1]), (p[0], p[1]), (p[0], y_hi), (q[0], y_hi)], 0.0)
    D = max(o.meta.get("depth_backing_m", 0.0) + 0.1, o.meta["host_wall_m"],
            o.meta["reveal_depth_m"] + o.data["parts"]["frame"]["depth_m"] + 0.1)
    for x, hx in ((s_lo, -1.0), (s_hi, 1.0)):
        o.face("wall", [o.P(x, y_lo, 0), o.P(x, y_hi, 0), o.P(x, y_hi, D), o.P(x, y_lo, D)], (hx, 0.0, 0.0))
    o.face("wall", [o.P(s_lo, y_hi, 0), o.P(s_hi, y_hi, 0), o.P(s_hi, y_hi, D), o.P(s_lo, y_hi, D)], Y)
    o.plane("wall", box(s_lo, s_hi, y_lo, y_hi), D, (0.0, 0.0, -1.0))
    G = v["front_yard_m"]
    if area:
        a0, a1, F = area["s"][0], area["s"][1], area["out_m"]
        cells = [(s_lo, a0, 0, G), (a1, s_hi, 0, G), (a0, a1, F, G)]
    else:
        cells = [(s_lo, s_hi, 0, G)]
    for (a, b, o0, o1) in cells:
        o.quad("ground", [(a, grade, o0), (b, grade, o0), (b, grade, o1), (a, grade, o1)], Y)
    o.quad("walk", [(s_lo, grade, G), (s_hi, grade, G), (s_hi, grade, G + WALK_M), (s_lo, grade, G + WALK_M)], Y)
    o.meta["panel"] = {"s": [s_lo, s_hi], "y": [y_lo, y_hi]}


def load() -> dict:
    return json.loads(DATA.read_text())


def build_variant(v: dict, data: dict, origin=(0.0, 0.0, 0.0), board: bool = True) -> Entrance:
    o = Entrance(v, data, origin).build()
    if board:
        wall_panel(o)
    return o


def build_kit(data: dict | None = None) -> list[Entrance]:
    data = data or load()
    out, x = [], 0.0
    for v in data["variants"]:
        probe = build_variant(v, data, board=True)
        s_lo, s_hi = probe.meta["panel"]["s"]
        out.append(build_variant(v, data, origin=(x - s_lo, 0.0, 0.0)))
        x += (s_hi - s_lo) + PANEL_GAP
    return out


def triangles(o: Entrance, include_board: bool = False) -> int:
    return sum(len(p.idx) // 3 for r, p in o.prims.items() if include_board or r not in BOARD_ROLES)


def cost_class(v: dict) -> str:
    return "carriage" if v.get("carriage") else ("porch" if v["stair"]["kind"] == "porch" else "entrance")


# -- glTF -------------------------------------------------------------------------------------

def to_glb(kit: list[Entrance], data: dict) -> bytes:
    mats = materials(data)
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

    mat_names = list(mats)
    materials_out = []
    for name in mat_names:
        m = mats[name]
        alpha = m.get("alpha", 1.0)
        entry = {"name": f"k07_{name}", "pbrMetallicRoughness": {
            "baseColorFactor": [*[round(c, 4) for c in m["color"]], alpha],
            "metallicFactor": m.get("metallic", 0.0), "roughnessFactor": m["roughness"]}}
        if alpha < 1.0:
            entry["alphaMode"] = "BLEND"
        materials_out.append(entry)
    rnd = lambda q: [round(c, 4) for c in q]
    for o in kit:
        by_mat: dict[str, list[Prim]] = {}
        for role in ROLE_MATERIAL:   # fixed order
            if role in o.prims and o.prims[role].idx:
                by_mat.setdefault(ROLE_MATERIAL[role], []).append(o.prims[role])
        prims_out = []
        for name in mat_names:
            if name not in by_mat:
                continue
            pos, nrm, uv, conf, idx = [], [], [], [], []
            for pr in by_mat[name]:
                base = len(pos)
                pos += [tuple(round(c, 5) for c in q) for q in pr.pos]
                nrm += pr.nrm
                uv += pr.uv
                conf += pr.conf
                idx += [base + i for i in pr.idx]
            ctype = 5123 if len(pos) < 65536 else 5125
            prims_out.append({"attributes": {
                "POSITION": accessor(pos, 5126, "VEC3", 3, 34962, True),
                "NORMAL": accessor(nrm, 5126, "VEC3", 3, 34962),
                "TEXCOORD_0": accessor(uv, 5126, "VEC2", 2, 34962),
                "_CONFIDENCE": accessor(conf, 5126, "SCALAR", 1, 34962)},
                "indices": accessor(idx, ctype, "SCALAR", 1, 34963),
                "material": mat_names.index(name)})
        meshes.append({"name": o.v["id"], "primitives": prims_out})
        nodes.append({"name": o.v["id"], "mesh": len(meshes) - 1, "extras": {
            "component_id": o.v["id"], "family": "entrance", "seed": o.seed,
            "origin": rnd(o.O),
            "triangles_entrance": triangles(o), "triangles_with_board": triangles(o, True),
            "sockets": {"threshold": [0.0, 0.0, 0.0],
                        "head": [0.0, round(max(q[1] for q in o.holes[0]), 4), 0.0],
                        "grade": [0.0, round(o.meta["grade_m"], 4), 0.0],
                        **{k: [[round(q[0], 4), round(q[1], 4), round(q[2], 4)] for q in pts]
                           for k, pts in sorted(o.sockets.items())}},
            "params": {k: o.v[k] for k in ("head", "clear_width_m", "clear_height_m", "leaves", "panels",
                                            "front_yard_m")},
            "measured": {"stair": o.meta.get("stair"), "head": o.meta["head"],
                         "leaf_top_m": o.meta["leaf_top_m"]}}})
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
        "extras": {"k07": {"data": "data/components/prairie_1904/k07_entrances.json", "ticket": "T-2303",
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
                  f"{DATA.relative_to(ROOT)}: run python3 generators/archetypes/k07_entrances.py")
            return 1
        print(f"ok   {out.relative_to(ROOT)} is the generator's bytes ({len(blob)} B)")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    print(f"wrote {out.relative_to(ROOT)} ({len(blob)} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
