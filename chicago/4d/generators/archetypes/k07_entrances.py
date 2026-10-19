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
    "wall": "masonry", "reveal": "masonry", "porch_back": "masonry",
    "threshold": "stone", "head": "stone", "landing": "stone", "tread": "stone", "riser": "stone",
    "stair_end": "stone", "cheek": "stone", "area_wall": "area_brick", "coping": "stone", "guard": "stone",
    "frame": "joinery", "leaf": "joinery", "sash_outer": "joinery",
    "glass_outer": "glass", "glass_leaf": "glass",
    "hardware": "iron", "backing": "backing",
    "deck": "porch_timber", "skirt": "porch_timber", "post": "porch_timber", "beam": "porch_timber",
    "porch_roof": "porch_timber", "step_timber": "porch_timber",
    "terrace": "stone", "terrace_face": "stone", "baluster": "stone", "newel": "stone", "rail": "stone",
    # T-2500: a stone loggia on the terrace (1808's), its basement arch's void behind the hall's backing
    "pedestal": "stone", "column": "stone", "entablature": "stone", "loggia_wall": "stone",
    "balcony": "stone", "arch_reveal": "stone", "arch_back": "backing",
    "ground": "ground", "walk": "walk",
}
# The board, not the entrance: excluded from an entrance's costs and from the walk rule.
BOARD_ROLES = ("wall", "ground", "walk")
STAIR_TREADS = ("landing", "tread", "deck")


def _arc_y(arc, x):
    """The height of an arch's head polyline (right to left, as Region.outline draws it) at s=x."""
    for (xa, ya), (xb, yb) in zip(arc, arc[1:]):
        if xb - 1e-9 <= x <= xa + 1e-9:
            return ya if abs(xa - xb) < 1e-12 else ya + (yb - ya) * (x - xa) / (xb - xa)
    raise ValueError(f"s {x:.3f} is not under the arch")


def _porch_back(arc, s0, s1, a, b, Hd):
    """T-2817: the porch's back wall, the arch's outline less a door a..b under a flat head Hd:
    a strip each side of the door and the tympanum over it, each convex, each closed on the
    arch's own head polyline so that it meets the reveal's back edge vertex for vertex."""
    inside = lambda lo, hi: [q for q in arc if lo + 1e-9 < q[0] < hi - 1e-9]
    ya, yb = _arc_y(arc, a), _arc_y(arc, b)
    return [[(b, 0.0), (s1, 0.0)] + [q for q in arc if q[0] > b + 1e-9] + [(b, yb)],
            [(a, Hd), (b, Hd), (b, yb)] + inside(a, b) + [(a, ya)],
            [(s0, 0.0), (a, 0.0), (a, ya)] + [q for q in arc if q[0] < a - 1e-9]]


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
        self._arch_head = head
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
        pd = v.get("porch_door")
        if pd:
            # T-2817: the hole is a porch's mouth (1623's drawing: an arch as broad as the window's,
            # its door at the back to one side and the porch's back wall lit beside it). A wall at
            # the reveal's depth closes the arch round the door's own flat-headed opening, `width_m`
            # across under a head `height_m` up, its centre `s_m` off the arch's axis; the door and
            # its frame stand in that, and take their leaves, transom and glazing from it
            a, b = pd["s_m"] - pd["width_m"] / 2, pd["s_m"] + pd["width_m"] / 2
            Hd = pd["height_m"]
            arc = outline[2:]
            if not s0 + 0.1 <= a < b <= s1 - 0.1 or not Hd + 0.1 <= min(_arc_y(arc, a), _arc_y(arc, b)):
                raise ValueError(f"{v['id']}: a {pd['width_m']} m porch door at s {pd['s_m']:+.3f}, {Hd} m high, "
                                 f"does not stand 0.1 m inside its {W} m arch")
            for poly in _porch_back(arc, s0, s1, a, b, Hd):
                self.plane("porch_back", poly, rev)
            self.v = v = {**v, **{k: pd[k] for k in ("leaves", "panels", "transom_m", "transom_lights",
                                                      "glazed_rows", "rails_y_m") if k in pd}}
            hole, head, flat = Region(a, b, 0.0, top_y=Hd), Head("flat", a, b, Hd), True
            outline = hole.outline()
            self.meta["porch_door"] = {"s_m": [round(a, 4), round(b, 4)], "height_m": Hd}
        # frame: a face ring with no foot, and its sight edges
        self.ring("frame", outline, hole.outline(f, f, 0, f), rev)
        self.tube("frame", hole.outline(f, f, 0, f), rev, rev + fr["depth_m"])
        s0f, s1f, Hf = (hole.s0, hole.s1, hole.top_y) if pd else (s0, s1, H)
        day = Region(s0f + f, s1f - f, 0.0, top_y=Hf - f if flat else None, head=None if flat else head, head_inset=f)
        self.meta["daylight_s"] = [day.s0, day.s1]
        self._door(day, head, rev, fr)
        if pd:
            head = self._arch_head
        if v.get("carriage"):
            self._lintel(s0, s1, H, v["lintel"])
            self._guards(s0, s1)
        else:
            self._head_band([(s0, s1, head)], p["head_band"])
        kind = v["stair"]["kind"]
        if kind == "straight" and v["stair"].get("side"):
            self._side_stoop()
        elif kind == "straight":
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
        # T-2463: the stoop's axis, `axis_s_m` along the wall from the door's centre (1620's
        # door stands at the south end of a landing that runs on north into its porch)
        c = st.get("axis_s_m", 0.0)
        # T-2409: a terrace at the landing's height running along the front to one side;
        # it takes that side of the landing, so that cheek runs down the flight alone.
        # T-2450: one terrace a side, so `porch` is one or a list of two
        porch = st.get("porch")
        porches = porch if isinstance(porch, list) else ([porch] if porch else [])
        psides = [{"left": -1.0, "right": 1.0}[q["side"]] for q in porches]
        if len(set(psides)) != len(psides):
            raise ValueError("a stoop takes one terrace a side")
        W = self.v["clear_width_m"] / 2
        if (-W < c - half - 1e-9 and -1.0 not in psides) or (W > c + half + 1e-9 and 1.0 not in psides):
            raise ValueError(f"the door hangs off a stoop {c:+.3f} m off its axis, where no terrace carries it on")
        self.quad("landing", [(c - half, 0, 0), (c + half, 0, 0), (c + half, 0, L), (c - half, 0, L)], Y)
        self.probe(c, 0.0, L / 2, ("landing",), "the landing")
        if not cheeks:
            for x, hx in ((c - half, -1.0), (c + half, 1.0)):
                self.quad("stair_end", [(x, -R, 0), (x, -R, L), (x, 0, L), (x, 0, 0)], (hx, 0.0, 0.0))
        F = self._flight(c - half, c + half, 0.0, L, n, r, g, -1, not cheeks, end_floor=-R)
        self.meta["stair"] = {"risers": n, "riser_m": round(r, 5), "going_m": g, "foot_out_m": round(F, 4),
                              **({"axis_s_m": round(c, 4)} if c else {})}
        if cheeks:
            ch = p["cheek"]
            t, hc = ch["thickness_m"], ch["above_nosing_m"]
            yF = -(n - 1) * r + hc
            for sgn in (-1.0, 1.0):
                si, so = c + sgn * half, c + sgn * (half + t)
                o0 = L if sgn in psides else 0.0
                # T-2500: a terrace deeper than the landing (1808's loggia deck) is the flight's
                # cheek on its side as far as its own front, and the cheek runs on from there,
                # its top rising from the rake to the deck's edge
                Dq = next((q.get("out_m", L) for q, sd in zip(porches, psides) if sd == sgn), L)
                carved = any(q.get("loggia", {}).get("finish") == "ionic_carved" for q in porches)
                if carved:
                    self._scrolled_cheek(si, so, sgn, Dq if Dq > L else L, F, R, c, half, t, Dq > L, -(n - 1) * r)
                    if Dq > L:
                        self.quad("cheek", [(si,-R,L),(si,-R,Dq),(si,0,Dq),(si,0,L)],(-sgn,0,0))
                    else:
                        self._box("cheek",min(si,so),max(si,so),-R,.85,0,L)
                    continue
                if Dq > L:
                    o0 = Dq
                    self.quad("cheek", [(si, -R, L), (si, -R, Dq), (si, 0, Dq), (si, 0, L)], (-sgn, 0.0, 0.0))
                    prof = [(Dq, -R), (F, -R), (F, yF), (Dq, 0.0)]
                    rake = lambda o: (o - Dq) / (F - Dq) * yF
                    for k in range(1, n):
                        if L < L + (k - 0.5) * g < Dq:
                            self.probe(si, (-R + -k * r) / 2, L + (k - 0.5) * g, ("cheek",), f"the deck's side at step {k}")
                    for q_ in (si, so):
                        self.quad("cheek", [(q_, y, o) for o, y in prof], (sgn if q_ == so else -sgn, 0.0, 0.0))
                    self.quad("cheek", [(si, 0.0, Dq), (so, 0.0, Dq), (so, yF, F), (si, yF, F)], (0.0, F - Dq, -yF))
                    self.quad("cheek", [(si, -R, F), (so, -R, F), (so, yF, F), (si, yF, F)], OUT)
                    mid = c + sgn * (half + t / 2)
                    top, foot = (mid, rake(Dq + 0.15), Dq + 0.15), (mid, rake(F - 0.15), F - 0.15)
                    self.sockets[f"handrail_{'left' if sgn < 0 else 'right'}"] = [top, foot]
                    for pt in (top, foot):
                        self.probe(*pt, ("cheek",), "a handrail socket on its cheek")
                    continue
                prof = [(o0, -R), (F, -R), (F, yF), (L, hc)] + ([(0, hc)] if o0 == 0.0 else [])
                self.quad("cheek", [(si, y, o) for o, y in prof], (-sgn, 0.0, 0.0))
                self.quad("cheek", [(so, y, o) for o, y in prof], (sgn, 0.0, 0.0))
                if o0 == 0.0:
                    self.quad("cheek", [(si, hc, 0), (so, hc, 0), (so, hc, L), (si, hc, L)], Y)
                else:   # its back end, under the terrace's front edge
                    self.quad("cheek", [(si, -R, L), (so, -R, L), (so, hc, L), (si, hc, L)], (0.0, 0.0, -1.0))
                self.quad("cheek", [(si, hc, L), (so, hc, L), (so, yF, F), (si, yF, F)], (0.0, g, r))
                self.quad("cheek", [(si, -R, F), (so, -R, F), (so, yF, F), (si, yF, F)], OUT)
                mid = c + sgn * (half + t / 2)
                # on the terrace's side the cheek starts at L, so its top socket stands on the rake
                top = (mid, hc, L - 0.15) if o0 == 0.0 else (mid, hc - 0.15 * r / g, L + 0.15)
                foot = (mid, hc - (F - 0.15 - L) * r / g, F - 0.15)
                self.sockets[f"handrail_{'left' if sgn < 0 else 'right'}"] = [top, foot]
                for pt in (top, foot):
                    self.probe(*pt, ("cheek",), "a handrail socket on its cheek")
        for q, side in zip(porches, psides):
            deck = half + side * c       # the landing's edge, measured from the door away from the stoop
            self._terrace(q, side, deck + (p["cheek"]["thickness_m"] if cheeks else 0.0), deck, L, R)
        if st.get("balustrade"):
            self._stoop_balustrade(st["balustrade"], psides, half, L, F, n, r, g, R, c)

    # T-2530: a side stoop (1621's, the Building Budget drawing's) ------------------------
    def _side_stoop(self):
        """A landing at the floor running along the wall from `landing_s_m[0]` to
        `landing_s_m[1]` (run coordinates: s measured toward `run`), and from its near end a
        flight of the same equal risers running on along the wall, parallel to it, `out_m`
        clear of the face (a bay's projection) and `width_m` wide, down to grade. The
        landing is faced to grade along its street edge and across its far end; a solid
        cheek closes the flight's street side, its top raking with the nosings
        `cheek_above_nosing_m` over them (the kit's `above_nosing_m` unless the stoop says),
        and the flight's inner side is closed by its steps' ends. The foot opens toward
        `run`."""
        st, p = self.v["stair"], self.data["parts"]
        sd = st["side"]
        R = st["floor_m"]
        n, r = risers(R, p["stair"])
        g, w = st["going_m"], st["width_m"]
        k = {"left": -1.0, "right": 1.0}[sd["run"]]
        t0, t1 = sd["landing_s_m"]
        o0 = sd.get("out_m", 0.0)
        D = o0 + w
        ch = p["cheek"]
        t, hc = ch["thickness_m"], sd.get("cheek_above_nosing_m", ch["above_nosing_m"])
        W = self.v["clear_width_m"] / 2
        if not (t0 <= -W and W <= t1):
            raise ValueError(f"the door (±{W:.3f} m) does not open on its side landing ({t0:.3f}..{t1:.3f} m)")
        S = lambda q: k * q
        X = lambda h: (k * h, 0.0, 0.0)          # a face turned along the run
        self.quad("landing", [(S(t0), 0, 0), (S(t1), 0, 0), (S(t1), 0, D), (S(t0), 0, D)], Y)
        self.probe(S((t0 + t1) / 2), 0.0, D / 2, ("landing",), "the landing")
        if o0 > 0:     # the landing's near end, between the wall and the flight
            self.quad("stair_end", [(S(t1), -R, 0), (S(t1), -R, o0), (S(t1), 0, o0), (S(t1), 0, 0)], X(1.0))
            self.probe(S(t1), -R / 2, o0 / 2, ("stair_end",), "the landing's end beside the flight")
        for i in range(1, n + 1):
            a = t1 + (i - 1) * g
            lo, hi = -i * r, -(i - 1) * r
            self.quad("riser", [(S(a), lo, o0), (S(a), lo, D), (S(a), hi, D), (S(a), hi, o0)], X(1.0))
            self.probe(S(a), (lo + hi) / 2, (o0 + D) / 2, ("riser",), f"riser {i}")
            if i == n:
                break
            self.quad("tread", [(S(a), lo, o0), (S(a + g), lo, o0), (S(a + g), lo, D), (S(a), lo, D)], Y)
            self.probe(S(a + g / 2), lo, (o0 + D) / 2, ("tread",), f"tread {i}")
            self.quad("stair_end", [(S(a), -R, o0), (S(a + g), -R, o0), (S(a + g), lo, o0), (S(a), lo, o0)],
                      (0.0, 0.0, -1.0))
            self.probe(S(a + g / 2), (lo - R) / 2, o0, ("stair_end",), f"the end of step {i}")
        F = t1 + (n - 1) * g
        yF = -(n - 1) * r + hc
        # the landing faced to grade along its street edge and across its far end
        self.quad("stair_end", [(S(t0), -R, D), (S(t1), -R, D), (S(t1), 0, D), (S(t0), 0, D)], OUT)
        self.quad("stair_end", [(S(t0), -R, 0), (S(t0), -R, D), (S(t0), 0, D), (S(t0), 0, 0)], X(-1.0))
        self.probe(S((t0 + t1) / 2), -R / 2, D, ("stair_end",), "the landing's street face")
        self.probe(S(t0), -R / 2, D / 2, ("stair_end",), "the landing's far end")
        # the cheek along the flight's street side, its top `hc` over the nosings
        prof = [(t1, -R), (F, -R), (F, yF), (t1, hc)]
        self.quad("cheek", [(S(q), y, D + t) for q, y in prof], OUT)
        self.quad("cheek", [(S(q), y, D) for q, y in prof], (0.0, 0.0, -1.0))
        self.quad("cheek", [(S(t1), hc, D), (S(t1), hc, D + t), (S(F), yF, D + t), (S(F), yF, D)], (k * r, g, 0.0))
        self.quad("cheek", [(S(F), -R, D), (S(F), -R, D + t), (S(F), yF, D + t), (S(F), yF, D)], X(1.0))
        self.quad("cheek", [(S(t1), -R, D), (S(t1), -R, D + t), (S(t1), hc, D + t), (S(t1), hc, D)], X(-1.0))
        mid = D + t / 2
        top = (S(t1 + 0.15), hc - 0.15 * r / g, mid)
        foot = (S(F - 0.15), hc - (F - 0.15 - t1) * r / g, mid)
        self.sockets["handrail_street"] = [top, foot]
        for pt in (top, foot):
            self.probe(*pt, ("cheek",), "a handrail socket on its cheek")
        self.meta["stair"] = {"risers": n, "riser_m": round(r, 5), "going_m": g, "run": sd["run"],
                              "foot_s_m": round(S(F), 4), "foot_out_m": round((o0 + D) / 2, 4),
                              "reach_out_m": round(D + t, 4)}

    # T-2409: the terrace and the turned balustrades ------------------------------------
    TERRACE_REVEAL_M = 0.02
    def _terrace(self, porch, side, s_face, s_deck, L, R):
        """A stone terrace at the landing's height from the landing's `side` edge to
        `to_s_m` along the front, `L` deep, its back stepped out where `back` says the
        front stands proud ([s, out] from that s on), faced to grade. Its s are measured
        from the door's centre AWAY from the stoop, so a left terrace (side -1, T-2450) is
        the right one's mirror; where it runs on past the front's end (`wall_to_s_m`), its
        back is faced too, as nothing stands behind it there."""
        m = lambda t: side * t
        S = porch["to_s_m"]
        # T-2500: a terrace may stand deeper than the landing (1808's loggia deck); its
        # cheek-side face is the flight's cheek (_stoop), so its front runs from s_deck
        if porch.get("out_m", L) > L:
            L = porch["out_m"]
        # a back step at or behind the landing's edge sets the terrace's back from the start
        back = [(b[0], b[1]) for b in porch.get("back", [])]
        first = 0.0
        while back and back[0][0] <= s_deck + 1e-6:
            first = back.pop(0)[1]
        steps = [(s_deck, first)] + back
        edges = [q[0] for q in steps] + [S]
        for (a, back), b in zip(steps, edges[1:]):
            if not a < b or back >= L:
                raise ValueError(f"terrace step {a:.3f}..{b:.3f} m at {back} m is not a strip in front of the wall")
            self.quad("terrace", [(m(a), 0, back), (m(b), 0, back), (m(b), 0, L), (m(a), 0, L)], Y)
        lg = porch.get("loggia")
        if lg and lg.get("arch"):
            self._arch_face(lg["arch"], m, s_face, S, (s_deck + S) / 2, R, L)
        else:
            self.quad("terrace_face", [(m(s_face), -R, L), (m(S), -R, L), (m(S), 0, L), (m(s_face), 0, L)], OUT)
        last = steps[-1][1]
        self.quad("terrace_face", [(m(S), -R, last), (m(S), -R, L), (m(S), 0, L), (m(S), 0, last)], (side, 0.0, 0.0))
        W = porch.get("wall_to_s_m")
        if W is not None and W < S:
            if not steps[-1][0] <= W:
                raise ValueError(f"the front ends at {W:.3f} m, inside the terrace's last step")
            self.quad("terrace_face", [(m(W), -R, last), (m(S), -R, last), (m(S), 0, last), (m(W), 0, last)],
                      (0.0, 0.0, -1.0))
        self.probe(m((s_deck + S) / 2), 0.0, (last + L) / 2, ("terrace",), "the terrace")
        B = porch.get("balustrade")
        if B:
            # the newels stand REVEAL back from the terrace's edge, so the corner newel's face is
            # never on the plane of the cheek's end beside it (one face drawn twice)
            nm, o_n = B["newel_m"] / 2, L - B["newel_m"] / 2 - self.TERRACE_REVEAL_M
            corner = (m((s_face + s_deck) / 2 if s_face > s_deck else s_deck + nm), 0.0, o_n)
            far = (m(S - nm), 0.0, o_n)
            self._baluster_run(B, corner, far, B["height_m"])
            self._baluster_run(B, far, (m(S - nm), 0.0, last + nm), B["height_m"], skip_first=True)
        rec = {"s": [m(s_deck), m(S)], "out_m": L, "back": [[m(a), o] for a, o in steps]}
        self.meta["terrace" if side > 0 else "terrace_left"] = rec
        if lg:
            if W is not None and W < S:
                raise ValueError("a loggia stands on a terrace inside the front")
            self.meta["loggia"] = self._loggia(lg, m, side, s_deck, S, L)

    # T-2500: the loggia on a terrace, and the basement arch under it ---------------------
    def _arch_face(self, A, m, s0, s1, ca, R, L):
        """The terrace's front from s0 to s1, faced to grade, with a round-headed arch in it
        centred on ca, under the loggia's middle: the jambs `spring_m` over grade, the head a
        half round, its void `depth_m` deep and closed by the backing."""
        hw = A["span_m"] / 2
        ys = -R + A["spring_m"]
        if not (s0 + 0.2 <= ca - hw and ca + hw <= s1 - 0.2 and ys + hw <= -0.15):
            raise ValueError("the basement arch does not stand inside the terrace's face")
        k = A.get("segments", 12)
        arc = [(ca - hw * math.cos(math.pi * i / k), ys + hw * math.sin(math.pi * i / k)) for i in range(k + 1)]
        self.quad("terrace_face", [(m(s0), -R, L), (m(arc[0][0]), -R, L), (m(arc[0][0]), 0, L), (m(s0), 0, L)], OUT)
        self.quad("terrace_face", [(m(arc[-1][0]), -R, L), (m(s1), -R, L), (m(s1), 0, L), (m(arc[-1][0]), 0, L)], OUT)
        for (a, ya), (b, yb) in zip(arc, arc[1:]):
            self.quad("terrace_face", [(m(a), ya, L), (m(b), yb, L), (m(b), 0, L), (m(a), 0, L)], OUT)
        d = A["depth_m"]
        outline = [(arc[0][0], -R)] + arc + [(arc[-1][0], -R)]
        for (a, ya), (b, yb) in zip(outline, outline[1:]):
            mx, my = (a + b) / 2 - ca, (ya + yb) / 2 - ys
            self.quad("arch_reveal", [(m(a), ya, L), (m(b), yb, L), (m(b), yb, L - d), (m(a), ya, L - d)],
                      (-m(mx) if abs(mx) > 1e-9 else 0.0, -my if a != b else 0.0, 0.0))
        self.quad("arch_back", [(m(x), y, L - d) for x, y in outline], OUT)
        self.probe(m(ca), ys, L - d, ("arch_back",), "the basement arch's void")
        self.probe(m(s0 + 0.1), -R / 2, L, ("terrace_face",), "the terrace's face beside the arch")

    def _box(self, role, s0, s1, y0, y1, o0, o1, skip=()):
        """A closed block in the door's frame, s0 < s1 and o0 < o1; `skip` names the faces
        another part covers ('back', 'front', 'left', 'right', 'bottom', 'top')."""
        F = {"top": ([(s0, y1, o0), (s1, y1, o0), (s1, y1, o1), (s0, y1, o1)], Y),
             "bottom": ([(s0, y0, o0), (s1, y0, o0), (s1, y0, o1), (s0, y0, o1)], (0.0, -1.0, 0.0)),
             "front": ([(s0, y0, o1), (s1, y0, o1), (s1, y1, o1), (s0, y1, o1)], OUT),
             "back": ([(s0, y0, o0), (s1, y0, o0), (s1, y1, o0), (s0, y1, o0)], (0.0, 0.0, -1.0)),
             "left": ([(s0, y0, o0), (s0, y0, o1), (s0, y1, o1), (s0, y1, o0)], (-1.0, 0.0, 0.0)),
             "right": ([(s1, y0, o0), (s1, y0, o1), (s1, y1, o1), (s1, y1, o0)], (1.0, 0.0, 0.0))}
        for k, (pts, n) in F.items():
            if k not in skip:
                self.quad(role, pts, n)

    def _loggia(self, lg, m, side, s_deck, S, D):
        """1808's north entrance loggia (T-2500, the Inland Architect plate of February 1888):
        a pedestal at each front corner carrying a pair of turned columns, a solid parapet
        between the pedestals across the front and along the far side back to the wall, the
        near side left open to the flight, and over the columns an entablature block the
        loggia's whole plan, its soffit the loggia's ceiling and its top the balcony's floor,
        walled by the balcony's parapet on its three open sides. Every block is closed except
        where it meets the wall (o = 0) or another block."""
        lo = lambda a, b: (min(m(a), m(b)), max(m(a), m(b)))
        # in the mirrored frame "near" is the flight's side (s_deck), "far" the terrace's end (S)
        near_face, far_face = ("left", "right") if side > 0 else ("right", "left")
        carved = lg.get("finish") == "ionic_carved"
        P, C, E, B, W = lg["pedestal"], lg["columns"], lg["entablature"], lg["balcony"], lg["parapet"]
        pw, pd, ph = P["width_m"], P["depth_m"], P["height_m"]
        if not (2 * pw + 0.6 <= S - s_deck and pd < D):
            raise ValueError(f"the loggia's pedestals ({pw} x {pd} m) do not fit its {S - s_deck:.3f} x {D} m deck")
        for a, b, sk in ((s_deck, s_deck + pw, ()), (S - pw, S, ())):
            s0, s1 = lo(a, b)
            self._box("pedestal", s0, s1, 0.0, ph, D - pd, D, skip=("bottom",))
            self.probe(m((a + b) / 2), ph / 2, D, ("pedestal",), "a loggia pedestal's face")
        # the parapet between the pedestals, and along the far side to the wall
        wt, wh = W["thickness_m"], W["height_m"]
        if wh > ph:
            raise ValueError("the loggia's parapet stands over its pedestals")
        s0, s1 = lo(s_deck + pw, S - pw)
        if carved:
            self._pierced_panel(s0, s1, 0.0, wh, D-wt, D)
        else:
            self._box("loggia_wall", s0, s1, 0.0, wh, D - wt, D, skip=("bottom", "left", "right"))
        s0, s1 = lo(S - wt, S)
        self._box("loggia_wall", s0, s1, 0.0, wh, 0.0, D - pd, skip=("bottom", "back", "front"))
        self.probe(m((s_deck + S) / 2), wh / 2, D, ("loggia_wall",), "the loggia's front parapet")
        # the columns, two to a pedestal side by side along the front
        prof = [[float(r), float(y)] for r, y in C["profile"]]
        ch = C["height_m"]
        cols = []
        for a in (s_deck, S - pw):
            for f in (0.25, 0.75):
                cs, co = m(a + pw * f), D - pd / 2
                self._turn((cs, co), [(r, ph + ch * y) for r, y in prof], C["segments"], role="column")
                cols.append([round(cs, 4), round(co, 4)])
            if carved:
                # T-2565: the 1888 plate and the 1965 view both show ONE capital over each
                # pair, a carved block spanning both shafts, not a capital to a column
                self._paired_capital(*lo(a + 0.005, a + pw - 0.005), D - pd / 2, ph + ch)
        # the entablature over the whole plan, its soffit the ceiling
        y0, y1 = ph + ch, ph + ch + E["height_m"]
        s0, s1 = lo(s_deck, S)
        self._box("entablature", s0, s1, y0, y1, 0.0, D, skip=("back", "top"))
        self.probe(m((s_deck + S) / 2), (y0 + y1) / 2, D, ("entablature",), "the entablature's face")
        if carved:
            # T-2565: the balcony stands on a deep cornice; in the 1888 plate its corona throws
            # the heaviest shadow on the loggia, so it steps out in three to 0.22 m. Each
            # lower band's top lies under the next one's soffit and is left off.
            bands = ((y0, .09, .06), (y1 - .24, .07, .08), (y1 - .17, .06, .14), (y1 - .11, .11, .22))
            for i, (yy, hh, proud) in enumerate(bands):
                covered = 0 < i < len(bands) - 1
                self._box("entablature", s0-.03, s1+.03, yy, yy+hh, D, D+proud, skip=("back",)+(("top",) if covered else ()))
            for a,b in ((s_deck,s_deck+pw),(S-pw,S)):
                q0,q1=lo(a,b)
                for yy,hh,pd_ in ((0,.1,.05),(ph-.12,.12,.08)):
                    self._box("pedestal",q0-.03,q1+.03,yy,yy+hh,D,D+pd_,skip=("back",))
                # T-2769: the 1888 plate at its native 1559 px (about 75 px to the metre on
                # the pedestals, x 865-940 and 1100-1160, y 1585-1650) draws each pedestal's
                # field plain inside its border, as T-2585 read the balcony's dies; the leaf
                # scrolls T-1883 laid in it are not in the picture
                self._panel_relief(q0+.12,q1-.12,.23,ph-.2,D+.02,"pedestal",leaves=False)
            # T-2815: the plate also sees the south (flight-side) pedestal's side, x 872-886,
            # y 1590-1650, and draws its field in a border like the front's; no picture shows
            # the north pedestal's side, which stays plain
            fs = m(s_deck)
            out = 1.0 if fs > m(s_deck + pw) else -1.0
            e = .035
            for o0, o1, y0_, y1_ in ((D-pd+.1, D-.1, .23, .23+e), (D-pd+.1, D-.1, ph-.2-e, ph-.2),
                                     (D-pd+.1, D-pd+.1+e, .23+e, ph-.2-e), (D-.1-e, D-.1, .23+e, ph-.2-e)):
                sa_, sb_ = (fs, fs + out * e) if out > 0 else (fs + out * e, fs)
                skip = ("left",) if out > 0 else ("right",)
                if o1 - o0 < e + 1e-6:
                    skip += ("top", "bottom")
                self._box("pedestal", sa_, sb_, y0_, y1_, o0, o1, skip=skip)
        # the balcony: its floor and its parapet on the three open sides
        bt, bh = B["thickness_m"], B["height_m"]
        s0, s1 = lo(s_deck + bt, S - bt)
        self.quad("balcony", [(s0, y1, 0.0), (s1, y1, 0.0), (s1, y1, D - bt), (s0, y1, D - bt)], Y)
        s0, s1 = lo(s_deck, S)
        if carved:
            self._carved_balcony(s0, s1, y1, bh, D, bt, near=m(s_deck))
        else:
            self._box("balcony", s0, s1, y1, y1 + bh, D - bt, D, skip=("bottom",))
        for a in (s_deck, S - bt):
            s0, s1 = lo(a, a + bt)
            self._box("balcony", s0, s1, y1, y1 + bh, 0.0, D - bt, skip=("bottom", "back", "front"))
        self.probe(m((s_deck + S) / 2), y1 + bh / 2, D, ("balcony",), "the balcony's parapet")
        return {"s": [round(m(s_deck), 4), round(m(S), 4)], "out_m": D, "pedestal_top_m": ph,
                "columns": cols, "entablature_y_m": [round(y0, 4), round(y1, 4)],
                "balcony_top_m": round(y1 + bh, 4)}

    def _finish_faces(self, role, faces):
        for pts, hint in faces:
            if hint is None:
                a,b,c=pts[:3]
                u,v=[b[i]-a[i] for i in range(3)],[c[i]-a[i] for i in range(3)]
                hint=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
            if sum(x*x for x in hint)>1e-14:
                self.quad(role,pts,hint)

    def _pierced_panel(self,s0,s1,y0,h,d0,d1):
        b=.105
        for y in (y0,y0+h/2-b/2,y0+h-b):
            self._box("loggia_wall",s0,s1,y,y+b,d0,d1,skip=("left","right")+(("bottom",) if y==y0 else ()))
        n=max(2,round((s1-s0)/.30)); pitch=(s1-s0)/n
        for row in range(2):
            lo=y0+b if row==0 else y0+h/2+b/2
            hi=y0+h/2-b/2 if row==0 else y0+h-b
            for i in range(n+1):
                x=s0+i*pitch+(pitch/2 if row else 0)
                if x>=s1: continue
                self._box("loggia_wall",max(s0,x-b/2),min(s1,x+b/2),lo,hi,d0,d1,
                          skip=("top","bottom")+(("left",) if x-b/2<=s0 else ())+(("right",) if x+b/2>=s1 else ()))

    def _tube(self, role, path, rad, axis, sides=8):
        """T-2565: a round carved bead along `path` (s, y, out points in one plane), `axis`
        that plane's unit normal; each face's hint points out from the bead's centreline."""
        rings, norms = [], []
        for i, p in enumerate(path):
            a, b = path[max(0, i - 1)], path[min(len(path) - 1, i + 1)]
            t = [b[k] - a[k] for k in range(3)]
            n1 = (t[1] * axis[2] - t[2] * axis[1], t[2] * axis[0] - t[0] * axis[2], t[0] * axis[1] - t[1] * axis[0])
            ln = math.sqrt(sum(x * x for x in n1)) or 1.0
            n1 = [x / ln for x in n1]
            dirs = [[math.cos(q) * n1[k] + math.sin(q) * axis[k] for k in range(3)]
                    for q in (2 * math.pi * j / sides for j in range(sides))]
            rings.append([tuple(p[k] + rad * d[k] for k in range(3)) for d in dirs])
            norms.append(dirs)
        for i in range(len(rings) - 1):
            for j in range(sides):
                k = (j + 1) % sides
                h = tuple(norms[i][j][q] + norms[i][k][q] for q in range(3))
                self.quad(role, [rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]], h)
        for ring, (a, b) in ((rings[0], (path[1], path[0])), (rings[-1], (path[-2], path[-1]))):
            self.quad(role, ring, tuple(b[k] - a[k] for k in range(3)))

    def _volute(self, role, cs, cy, co, r, side, axis):
        """An Ionic volute: two and a half turns closing to an eye, carved on the face
        whose normal is `axis` (out for a front face, along s for an end)."""
        k = 40
        pts = []
        for i in range(k + 1):
            q, rr = 5.0 * math.pi * i / k, r * (1 - .6 * i / k)
            u, v = side * rr * math.cos(q), rr * math.sin(q)
            pts.append((cs + u, cy + v, co) if axis[0] == 0 else (cs, cy + v, co + u))
        self._tube(role, pts, .014, axis, 6)

    def _strap(self, role, path, w, o_in, o_out):
        """T-2585: a flat strap of width `w` along `path` (s, y points), standing from the
        plane `o_in` out to `o_out`; its face and its two edges, mitred at every turn so
        no two pieces of it overlap, its ends left to whatever it runs into."""
        face = 1.0 if o_out > o_in else -1.0
        def nrm(p, q):
            ts, ty = q[0] - p[0], q[1] - p[1]
            ln = math.hypot(ts, ty) or 1.0
            return -ty / ln, ts / ln
        ns = [nrm(p, q) for p, q in zip(path, path[1:])]
        off = []
        for i, (u, v) in enumerate(path):
            a, b = ns[max(0, i - 1)], ns[min(len(ns) - 1, i)]
            mx, my = a[0] + b[0], a[1] + b[1]
            ml = math.hypot(mx, my) or 1.0
            mx, my = mx / ml, my / ml
            k = w / 2 / max(.2, mx * b[0] + my * b[1])
            off.append(((u + mx * k, v + my * k), (u - mx * k, v - my * k)))
        for i, (sn, sy) in enumerate(ns):
            (pa, ma), (pb, mb) = off[i], off[i + 1]
            self.quad(role, [(u, v, o_out) for u, v in (pa, pb, mb, ma)], (0.0, 0.0, face))
            for (u0, v0), (u1, v1), sg in ((pa, pb, 1), (ma, mb, -1)):
                self.quad(role, [(u0, v0, o_in), (u1, v1, o_in), (u1, v1, o_out), (u0, v0, o_out)], (sg * sn, sg * sy, 0.0))

    def _paired_capital(self, s0, s1, d, y):
        """T-2585: one capital over a pair of shafts, read off the 1888 plate at its native
        1559 px (both capitals, x 860-945 and 1100-1165, y 1385-1405): a square-edged
        block about 0.2 m deep on the 0.89 m pair (12 px on 53), with NO volutes and no
        egg row. Its face carries a running zigzag, six strokes between a plain block at
        each end, the triangles between them sunk; a thin abacus over all. T-2565 read
        the zigzag's dark triangles as an egg row and the plain end blocks as volutes."""
        e, sink, fy = .09, .022, .035                   # end block, field depth, fillet height
        y0, y1, f = y - .20, y - .015, .21
        self._box("column", s0 - .01, s1 + .01, y1, y + .015, d - f - .015, d + f + .015)   # abacus
        self._box("column", s0, s1, y0, y1, d - f + sink, d + f - sink, skip=("top",))      # core
        for face in (-1, 1):
            oi, oo = d + face * (f - sink), d + face * f
            lo_, hi_ = sorted((oi, oo))
            for a, b in ((s0, s0 + e), (s1 - e, s1)):                                         # plain ends
                self._box("column", a, b, y0, y1, lo_, hi_, skip=("top", "back" if face > 0 else "front"))
            for v0, v1 in ((y0, y0 + fy), (y1 - fy, y1)):                                   # fillets
                self._box("column", s0 + e, s1 - e, v0, v1, lo_, hi_,
                          skip=("left", "right", "back" if face > 0 else "front") + (("top",) if v1 == y1 else ()))
            n, a, b = 6, s0 + e, s1 - e
            zz = [(a + (b - a) * i / n, (y0 + fy) if i % 2 == 0 else (y1 - fy)) for i in range(n + 1)]
            self._strap("column", zz, .032, oi, oo - face * .003)     # 3 mm shy of the frame it meets
        self.probe((s0 + s1) / 2, y1 - fy / 2, d + .21, ("column",), "a paired capital's fillet")

    def _rinceau(self, role, s0, s1, y0, y1, d):
        """T-2585: the balcony panel's carving as the 1888 plate (x 930-1150, y 1260-1330)
        and the 1965 view show it: one continuous running scroll of foliage across the
        field, a wavy stem with a tendril curling into every bay of the wave and a leaf
        at each tendril's root. The 1965 view counts four loops along the front; the
        leaves' cut and each curl's turns are below both pictures' grain."""
        yc, A = (y0 + y1) / 2, (y1 - y0) * .34
        n = max(2, round((s1 - s0) / .30))               # half-waves, each about 0.3 m
        lam = (s1 - s0) / n
        stem = [(s0 + (s1 - s0) * i / (8 * n), yc + A * math.sin(math.pi * i / 8), d) for i in range(8 * n + 1)]
        self._tube(role, stem, .02, (0.0, 0.0, 1.0), 6)
        lobe = lambda pts, r: self._tube(role, pts, r, (0.0, 0.0, 1.0), 5)
        for j in range(n):
            sg = 1 if j % 2 == 0 else -1                # the wave's crest side in this bay
            cx = s0 + (j + .5) * lam
            # the tendril leaves the stem past the crest and curls back under its arch
            r0, ey = A * .9, yc - sg * A * .12
            pts = [(cx + lam * .25, yc + sg * A * .7, d)]
            for i in range(29):
                q, rr = math.pi * 2.5 * i / 28, r0 * (1 - .8 * i / 28)
                pts.append((cx - rr * math.sin(q), ey + sg * rr * math.cos(q), d + .004))
            self._tube(role, pts, .02, (0.0, 0.0, 1.0), 6)
            # leaves: one sheathing the stem over the crest, one turned down off the node
            # where the stem crosses the field, one in the curl's mouth; each a fat lobe
            for lx, ly, ang, ln in ((cx - lam * .05, yc + sg * (A + .05), 0.0, .16),
                                    (cx - lam * .5, yc - sg * A * .5, -sg * 1.1, .14),
                                    (cx + lam * .32, yc - sg * A * .4, sg * .7, .11)):
                lobe([(lx + ln * t * math.cos(ang) - .02 * math.sin(math.pi * t) * math.sin(ang) * sg,
                       ly + ln * t * math.sin(ang) + .02 * math.sin(math.pi * t) * math.cos(ang) * sg, d + .004)
                      for t in (-.5 + i / 6 for i in range(7))], .026)

    def _panel_relief(self,s0,s1,y0,y1,d,role,leaves=True):
        from .k01_stone_finish import tube_faces
        # Sunk field bounded by a narrow bead, with low relief leaf scrolls. The exact
        # foliage is not resolved by the microfilm; this section is reconstructed.
        for x0,x1,lo,hi in ((s0,s1,y0,y0+.035),(s0,s1,y1-.035,y1),(s0,s0+.035,y0+.035,y1-.035),(s1-.035,s1,y0+.035,y1-.035)):
            self._box(role,x0,x1,lo,hi,d,d+.035,skip=("top","bottom") if x1-x0<.036 else ())
        n=max(1,round((s1-s0)/.42)) if leaves else 0
        for i in range(n):
            x=s0+(i+.5)*(s1-s0)/n; yc=(y0+y1)/2
            for side in (-1,1):
                pts=[(x+side*(.025+.10*math.sin(math.pi*j/16)),yc+(y1-y0)*.38*(2*j/16-1),d+.018) for j in range(17)]
                self._finish_faces(role,tube_faces(pts,.018,6))

    def _carved_balcony(self, s0, s1, y, h, d, thick, near):
        """T-2565: the balcony's front as both pictures show it: a solid panel with a LEVEL
        coping (the earlier curved top is not in either picture) between two square dies;
        the die on the flight's side carries the stepped stone finial the 1888 plate shows,
        the far one is capped flat against the wall."""
        dw = .38
        a, b = s0 + dw, s1 - dw
        self._box("balcony", a, b, y, y + h - .1, d - thick, d, skip=("bottom", "top", "left", "right"))
        self._box("balcony", a, b, y + h - .1, y + h, d - thick - .04, d + .06, skip=("left", "right"))   # coping
        # T-2585: under the carved field a plain base strip, about a third of the panel in the
        # 1888 plate, and a plain margin against each die; the scroll fills the rest
        self._box("balcony", a, b, y, y + .22, d, d + .03, skip=("bottom", "back", "left", "right"))      # base strip
        for x0, x1, die in ((a, a + .06, "left"), (b - .06, b, "right")):
            self._box("balcony", x0, x1, y + .22, y + h - .1, d, d + .03, skip=("bottom", "top", "back", die))
        self._rinceau("balcony", a + .1, b - .1, y + .24, y + h - .12, d + .014)
        for x0 in (s0, s1 - dw):
            x1 = x0 + dw
            self._box("balcony", x0, x1, y, y + h + .1, d - thick, d + .06, skip=("bottom", "top"))
            self._box("balcony", x0 - .03, x1 + .03, y + h + .1, y + h + .2, d - thick - .03, d + .09)
            # T-2585: the 1888 plate's right die carries a plain sunk panel in a raised border
            self._panel_relief(x0 + .07, x1 - .07, y + .14, y + h - .06, d + .072, "balcony", leaves=False)
            if min(abs(x0 - near), abs(x1 - near)) < 1e-6:
                c, o = (x0 + x1) / 2, d - thick / 2
                # stepped base, a pyramid cap and a ball, as the plate's corner finial reads
                for (hw, y_0, y_1) in ((.16, y + h + .2, y + h + .3), (.12, y + h + .3, y + h + .42)):
                    self._box("balcony", c - hw, c + hw, y_0, y_1, o - hw, o + hw, skip=("bottom",))
                t0 = y + h + .42
                for k in range(4):
                    q = [(c - .1, t0, o - .1), (c + .1, t0, o - .1), (c + .1, t0, o + .1), (c - .1, t0, o + .1)]
                    pa, pb = q[k], q[(k + 1) % 4]
                    mid = ((pa[0] + pb[0]) / 2 - c, .1, (pa[2] + pb[2]) / 2 - o)
                    self.quad("balcony", [pa, pb, (c, t0 + .3, o)], mid)
                from .k01_stone_finish import turned_faces
                self._finish_faces("balcony", turned_faces(c, o, [(.012, t0 + .27), (.05, t0 + .31), (.045, t0 + .37), (.012, t0 + .4)], 10))

    def _scrolled_cheek(self,si,so,sgn,start,F,R,c,half,t,terrace,low):
        # A concave swept stone cheek; tessellate in vertical strips, so no fan spans
        # the concavity. T-2565: both pictures end it at the street in a rolled foot,
        # a stone scroll lying across the cheek and standing proud of its outer face,
        # not in a scroll at its head; the sweep runs down onto the roll's crown.
        rr = .2
        Fc = F - rr
        end = -R + 2 * rr; peak = .85 if not terrace else 1.0
        top = lambda o: end + (peak - end) * (1 - (o - start) / (Fc - start)) ** 2
        N=32
        for i in range(N):
            a=start+(Fc-start)*i/N; b=start+(Fc-start)*(i+1)/N
            ya,yb=top(a),top(b)
            for x,n in ((si,-sgn),(so,sgn)):
                self.quad("cheek",[(x,-R,a),(x,-R,b),(x,yb,b),(x,ya,a)],(n,0,0))
            self.quad("cheek",[(si,ya,a),(so,ya,a),(so,yb,b),(si,yb,b)],(0,b-a,ya-yb))
        # the roll: its inner end set 15 mm back from the flight's face, its outer end 30 mm proud
        s_in, s_out = si + sgn * .015, so + sgn * .03
        self.quad("cheek", [(si, -R, Fc), (s_in, -R, Fc), (s_in, end, Fc), (si, end, Fc)], OUT)
        # the last step's end, in front of the roll's recessed inner end
        self.quad("cheek", [(si, -R, Fc), (si, -R, F), (si, low, F), (si, low, Fc)], (-sgn, 0, 0))
        K = 20
        ring = [(-R + rr + rr * math.sin(2 * math.pi * k / K), Fc + rr * math.cos(2 * math.pi * k / K)) for k in range(K)]
        for k in range(K):
            (ya, oa), (yb, ob) = ring[k], ring[(k + 1) % K]
            q = 2 * math.pi * (k + .5) / K
            self.quad("cheek", [(s_in, ya, oa), (s_out, ya, oa), (s_out, yb, ob), (s_in, yb, ob)], (0, math.sin(q), math.cos(q)))
        self.quad("cheek", [(s_in, y, o) for y, o in ring], (-sgn, 0, 0))
        self.quad("cheek", [(s_out, y, o) for y, o in ring], (sgn, 0, 0))
        self._volute("cheek", s_out + sgn * .006, -R + rr, Fc, rr * .85, 1, (sgn, 0.0, 0.0))
        self._volute("cheek", s_in - sgn * .006, -R + rr, Fc, rr * .85, 1, (-sgn, 0.0, 0.0))
        mid=(si+so)/2
        def mesh_top(o):
            q=(o-start)/(Fc-start)*N; i=min(N-1,int(q)); f=q-i
            a=start+(Fc-start)*i/N; b=start+(Fc-start)*(i+1)/N
            return top(a)*(1-f)+top(b)*f
        sockets=[(mid,mesh_top(start+.15),start+.15),(mid,mesh_top(Fc-.15),Fc-.15)]
        self.sockets[f"handrail_{'left' if sgn<0 else 'right'}"]=sockets
        for pt in sockets: self.probe(*pt,("cheek",),"a socket on the curved stone cheek")
        self.probe(s_out, -R + rr, Fc, ("cheek",), "the cheek's rolled foot")

    def _stoop_balustrade(self, B, psides, half, L, F, n, r, g, R, c=0.0):
        """A turned balustrade on each cheek's top, level beside the landing and raked down
        the flight, its rail at the terrace's height over the landing (the cheek's top is
        `above_nosing_m` over the nosing, so the balusters are that much shorter); on the
        side the terrace takes, it starts at the terrace's corner newel."""
        ch = self.data["parts"]["cheek"]
        hc, t = ch["above_nosing_m"], ch["thickness_m"]
        nm = B["newel_m"] / 2
        H = B["height_m"] - hc
        yF = -(n - 1) * r + hc
        foot = F - nm
        y_foot = hc + (yF - hc) * (foot - L) / (F - L)
        for sgn in (-1.0, 1.0):
            sc = c + sgn * (half + t / 2)
            if sgn in psides:   # from the terrace's corner newel (_terrace), down the rake
                self._baluster_run(B, (sc, hc, L - nm - self.TERRACE_REVEAL_M), (sc, y_foot, foot), H,
                                   skip_first=True)
            else:
                self._baluster_run(B, (sc, hc, nm), (sc, hc, L), H)
                self._baluster_run(B, (sc, hc, L), (sc, y_foot, foot), H, skip_first=True)

    def _baluster_run(self, B, a, b, H, skip_first=False):
        """Newels at a and b ((s, base y, out) on their centre lines), a rail between them
        H over the base line, turned balusters at no more than the pitch. A newel on a
        raked base is seated by its downhill side, so it never stands over the slope."""
        nm, (rw, rh) = B["newel_m"] / 2, B["rail_m"]
        ds, dy, do = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        run = math.hypot(ds, do)
        slope = abs(dy) / run
        sink = nm * slope
        top = lambda e: e[1] + H + B["newel_cap_m"]
        if not skip_first:
            self._newel((a[0], a[1] - sink, a[2]), top(a), nm)
        self._newel((b[0], b[1] - sink, b[2]), top(b), nm)
        us, uo = ds / run, do / run
        c0, c1 = nm / run, 1.0 - nm / run
        at = lambda f: (a[0] + ds * f, a[1] + dy * f, a[2] + do * f)
        side = (-uo * rw / 2, us * rw / 2)            # (s, out) across the run
        q = lambda e, k, y: (e[0] + k * side[0], e[1] + y, e[2] + k * side[1])
        e0, e1 = at(c0), at(c1)
        y0, y1 = H - rh, H
        self.quad("rail", [q(e0, -1, y1), q(e1, -1, y1), q(e1, 1, y1), q(e0, 1, y1)], Y)
        self.quad("rail", [q(e0, -1, y0), q(e1, -1, y0), q(e1, 1, y0), q(e0, 1, y0)], (0.0, -1.0, 0.0))
        for k in (-1, 1):
            self.quad("rail", [q(e0, k, y0), q(e1, k, y0), q(e1, k, y1), q(e0, k, y1)],
                      (k * side[0], 0.0, k * side[1]))
        prof = B["profile"]
        rmax = max(x[0] for x in prof)
        k = max(1, math.ceil((run - 2 * nm) / B["pitch_m"]))
        for i in range(k):
            s, y, o = at(c0 + (c1 - c0) * (i + 0.5) / k)
            yb = y - rmax * slope                     # seated into a raked base, never over it
            self._turn((s, o), [(rr, yb + (y0 - (yb - y)) * yy) for rr, yy in prof], B["segments"])
        self.meta["balusters"] = self.meta.get("balusters", 0) + k
        self.meta.setdefault("balustrade", []).append({"from": [round(x, 4) for x in a], "to": [round(x, 4) for x in b],
                                                       "balusters": k, "slope": round(dy / run, 4)})

    def _newel(self, c, y_top, nm):
        """A square newel from its base c (s, y, out) to y_top."""
        s, y, o = c
        a, b, o0, o1 = s - nm, s + nm, o - nm, o + nm
        self.quad("newel", [(a, y_top, o0), (b, y_top, o0), (b, y_top, o1), (a, y_top, o1)], Y)
        self.quad("newel", [(a, y, o1), (b, y, o1), (b, y_top, o1), (a, y_top, o1)], OUT)
        self.quad("newel", [(a, y, o0), (b, y, o0), (b, y_top, o0), (a, y_top, o0)], (0.0, 0.0, -1.0))
        for x, hx in ((a, -1.0), (b, 1.0)):
            self.quad("newel", [(x, y, o0), (x, y, o1), (x, y_top, o1), (x, y_top, o0)], (hx, 0.0, 0.0))
        self.probe(s, (y + y_top) / 2, o1, ("newel",), "a newel")

    def _turn(self, axis, prof, segs, role="baluster"):
        """A turned baluster: the profile [r, y] revolved about the vertical through axis (s, out)."""
        cs, co = axis
        ang = [2 * math.pi * k / segs for k in range(segs + 1)]
        for (r0, y0), (r1, y1) in zip(prof, prof[1:]):
            for a, b in zip(ang, ang[1:]):
                m = (a + b) / 2
                self.quad(role, [(cs + r0 * math.cos(a), y0, co + r0 * math.sin(a)),
                                       (cs + r0 * math.cos(b), y0, co + r0 * math.sin(b)),
                                       (cs + r1 * math.cos(b), y1, co + r1 * math.sin(b)),
                                       (cs + r1 * math.cos(a), y1, co + r1 * math.sin(a))],
                          (math.cos(m), 0.0, math.sin(m)))

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
