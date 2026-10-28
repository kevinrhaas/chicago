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
    # T-2961: a veranda roof's slopes, which a house lays in its own roof covering
    "porch_roof_top": "porch_timber",
    "terrace": "stone", "terrace_face": "stone", "baluster": "stone", "newel": "stone", "rail": "stone",
    # T-2500: a stone loggia on the terrace (1808's), its basement arch's void behind the hall's backing
    "pedestal": "stone", "column": "stone", "entablature": "stone", "loggia_wall": "stone",
    "balcony": "stone", "arch_reveal": "stone", "arch_back": "backing",
    # T-3134: a broad arch's heavy transom beam under its fanlight (1812's, the Levy print)
    "transom_beam": "stone",
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
            ros = v.get("rise_over_span", 0.125)   # T-2952: a porch arch's own segment
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
        # T-2910: a loggia's arch runs through the front wall alone; the room is behind it
        lg = v.get("loggia")
        dt = lg["front_wall_m"] if lg else rev
        n = len(outline)
        c = (0.0, H / 2)
        for i in range(1, n):
            a, b = outline[i], outline[(i + 1) % n]
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            self.face("reveal", [self.P(a[0], a[1], 0), self.P(b[0], b[1], 0),
                                 self.P(b[0], b[1], dt), self.P(a[0], a[1], dt)], (c[0] - m[0], c[1] - m[1], 0.0))
        self.face("threshold", [self.P(s0, 0, 0), self.P(s1, 0, 0), self.P(s1, 0, dt), self.P(s0, 0, dt)], Y)
        pd = v.get("porch_door")
        if pd and lg:
            # T-2910: the door in the loggia's back wall, on the room's floor under its ceiling
            a, b = pd["s_m"] - pd["width_m"] / 2, pd["s_m"] + pd["width_m"] / 2
            Hd = pd["height_m"]
            sa, sb = lg["s_m"]
            if not sa + 0.15 <= a < b <= sb - 0.15 or not Hd + 0.2 <= lg["ceiling_m"]:
                raise ValueError(f"{v['id']}: a {pd['width_m']} m loggia door at s {pd['s_m']:+.3f}, {Hd} m high, "
                                 f"does not stand in its back wall (s {sa}..{sb}, ceiling {lg['ceiling_m']} m)")
            rev = lg["depth_m"]
            self._loggia_room(lg, outline[2:], s0, s1, a, b, Hd)
            self.v = v = {**v, **{k: pd[k] for k in ("leaves", "panels", "transom_m", "transom_lights",
                                                      "glazed_rows", "rails_y_m") if k in pd}}
            hole, head, flat = Region(a, b, 0.0, top_y=Hd), Head("flat", a, b, Hd), True
            outline = hole.outline()
            self.meta["porch_door"] = {"s_m": [round(a, 4), round(b, 4)], "height_m": Hd}
            self.meta["reveal_depth_m"] = rev
        elif pd:
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
        mouth = day   # T-3228: the backing closes the whole mouth, side light and fanlight included
        sl = v.get("side_light")
        if sl and head.kind != "flat":
            # T-2952: a broad arch's mouth (1812's, the Levy print): the transom at the spring, the
            # segment over it glazed in lights, and under it the leaves, a pier and a side light
            # T-3134: or a heavy moulded beam `transom_beam` deep, the fanlight standing on it
            tb = v.get("transom_beam")
            y_leaf = head.spring - (tb["depth_m"] if tb else bar)
            self._bar(day, y_leaf, head.spring, d, rev + fr["depth_m"])
            fan = Region(day.s0, day.s1, head.spring, head=head, head_inset=day.head_inset)
            b1 = day.s1 - sl["width_m"]
            a1 = b1 - sl["pier_m"]
            if tb:
                self._beam(day, y_leaf, head.spring, d, tb)
            if v.get("fanlight_columns"):
                self._column_fan(fan, d, sa, mu, st, v["fanlight_columns"], ((day.s0 + a1) / 2, (a1 + b1) / 2))
            else:
                self._sash("sash_outer", fan, d, sa, mu, (v.get("transom_lights", 3), 1), (st, st, st, st), "fanlight")
            self.plane("porch_back", box(a1, b1, 0.0, y_leaf), d)
            self.plane("porch_back", box(b1, day.s1, 0.0, sl["sill_m"]), d)
            self._sash("sash_outer", Region(b1, day.s1, sl["sill_m"], top_y=y_leaf), d, sa, mu, (1, 1),
                       (st, st, st, st), "side_light")
            self.meta["side_light"] = {"s_m": [round(b1, 4), round(day.s1, 4)], "sill_m": sl["sill_m"],
                                       "pier_m": [round(a1, 4), round(b1, 4)]}
            day = Region(day.s0, a1, 0.0, top_y=y_leaf)
            has_glass = True
        elif head.kind == "round":
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
            outline = mouth.outline()
            self.tube("backing", outline, rev + fr["depth_m"], d_back)
            self.plane("backing", outline, d_back)
            self.meta["depth_backing_m"] = round(d_back, 4)

    def _beam(self, day, y0, y1, d, tb):
        """T-3134: the transom beam's mouldings, as the Levy print shows 1812's: a cap
        `cap_m` [high, proud] under the fanlight and a bead `bead_m` [high, proud] along its
        foot, each run the beam's length between the frame's faces, before its face at `d`."""
        for (h, pr), top in ((tb["cap_m"], True), (tb["bead_m"], False)):
            ya, yb = (y1 - h, y1) if top else (y0, y0 + h)
            e = d - pr
            self.plane("transom_beam", box(day.s0, day.s1, ya, yb), e)
            for y, hy in ((ya, -1.0), (yb, 1.0)):
                self.face("transom_beam", [self.P(day.s0, y, e), self.P(day.s1, y, e), self.P(day.s1, y, d),
                                           self.P(day.s0, y, d)], (0.0, hy, 0.0))
            # its ends, only where they stand before the frame's face (behind it the frame's
            # sight edges are the same plane)
            rev = d - self.data["parts"]["stop_m"]
            for x, hx in ((day.s0, -1.0), (day.s1, 1.0)) if e < rev - 1e-6 else ():
                self.face("transom_beam", [self.P(x, ya, e), self.P(x, yb, e), self.P(x, yb, rev),
                                           self.P(x, ya, rev)], (hx, 0.0, 0.0))
        self.meta["transom_beam"] = {"from_m": round(y0, 4), "to_m": round(y1, 4)}

    def _column_fan(self, fan, d, sa, mu, st, fc, centres):
        """T-3134: a fanlight of three lights parted by two narrow columns of small panes
        (1812's, the Levy print: one over the meeting of the leaves, one over the pier), each
        column `width_m` between its posts and divided in `rows` panes by bars to the arch."""
        w, pw = fc["width_m"], mu["width_m"]
        xs0, xs1 = fan.s0 + st, fan.s1 - st
        (c1, c2) = centres
        edges = [xs0, c1 - w / 2 - pw, c1 - w / 2, c1 + w / 2, c1 + w / 2 + pw, c2 - w / 2 - pw, c2 - w / 2,
                 c2 + w / 2, c2 + w / 2 + pw, xs1]
        if any(b - a < 0.1 for a, b in zip(edges[::2], edges[1::2])):
            raise ValueError(f"{self.v['id']}: two {w} m fanlight columns at s {c1:+.3f}, {c2:+.3f} leave a light "
                             f"under 0.1 m")
        lens = [b - a for a, b in zip(edges[::2], edges[1::2])]
        keep = self.v
        self.v = {**keep, "light_ratios": lens, "post_m": pw}
        g = self._sash("sash_outer", fan, d, sa, mu, (5, 1), (st, st, st, st), "fanlight")
        self.v = keep
        arc = fan.outline(st, st, st, st)[2:]
        y0 = fan.y0 + st
        rows = int(fc["rows"])
        for xa, xb in ((edges[2], edges[3]), (edges[6], edges[7])):
            yt = min(_arc_y(arc, xa), _arc_y(arc, xb))
            rh = (yt - y0 - pw * (rows - 1)) / rows
            for j in range(1, rows):
                yb = y0 + j * rh + (j - 1) * pw
                self.plane("sash_outer", box(xa, xb, yb, yb + pw), d)
                for ye, hy in ((yb, -1.0), (yb + pw, 1.0)):
                    self.face("sash_outer", [self.P(xa, ye, d), self.P(xb, ye, d), self.P(xb, ye, g),
                                             self.P(xa, ye, g)], (0.0, hy, 0.0))
        self.meta["fanlight_columns"] = {"s_m": [[round(edges[2], 4), round(edges[3], 4)],
                                                 [round(edges[6], 4), round(edges[7], 4)]], "rows": rows}

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
                riser_role="riser", end_floor=None, sb_at=None, sa_at=None):
        """n risers from y0, the first at out0, each `g` further out; sign -1 descends
        (a stoop, risers facing the street), +1 climbs (an area stair, facing the door).
        T-3134: `sb_at(out)`, where a flared cheek carries the flight's right-hand end out
        as it descends, is that end's s at each riser's and nosing's line; T-3144: `sa_at`
        the left-hand end's, where that cheek is carried out or drawn in."""
        rn = (0.0, 0.0, 1.0 if sign < 0 else -1.0)
        at = sb_at or (lambda o: sb)
        at_a = sa_at or (lambda o: sa)
        for k in range(1, n + 1):
            a = out0 + (k - 1) * g
            ya, yb = y0 + sign * (k - 1) * r, y0 + sign * k * r
            lo, hi = min(ya, yb), max(ya, yb)
            ba = at(a)
            self.quad(riser_role, [(at_a(a), lo, a), (ba, lo, a), (ba, hi, a), (at_a(a), hi, a)], rn)
            self.probe((sa + sb) / 2, (lo + hi) / 2, a, (riser_role,), f"riser {k}")
            if k == n:
                break
            yt = yb
            # T-3134: under a flared cheek the tread's end follows the cheek's inner face, kink by kink
            nodes = set(getattr(at, "nodes", ())) | set(getattr(at_a, "nodes", ()))
            kinks = sorted(o for o in nodes if a + 1e-9 < o < a + g - 1e-9)
            for oa, ob in zip([a] + kinks, kinks + [a + g]):
                self.quad(tread_role, [(at_a(oa), yt, oa), (at(oa), yt, oa), (at(ob), yt, ob), (at_a(ob), yt, ob)], Y)
            self.probe((sa + sb) / 2, yt, a + g / 2, (tread_role,), f"tread {k}")
            if ends:
                for x, hx in ((sa, -1.0), (sb, 1.0)):
                    self.quad(end_role, [(x, end_floor, a), (x, end_floor, a + g), (x, yt, a + g), (x, yt, a)],
                              (hx, 0.0, 0.0))
            ym = (end_floor + yt) / 2 if end_floor is not None else yt / 2
            for x in (at_a(a + g / 2), at(a + g / 2)):
                self.probe(x, ym, a + g / 2, (end_role,) if ends else ("cheek", "area_wall"),
                           f"the end of step {k}")
        return out0 + (n - 1) * g

    @staticmethod
    def _flares(sw):
        """T-3144: a swept stoop's `flare`, one {side, out_m} or a list of one a side."""
        fl = sw.get("flare") or []
        fl = fl if isinstance(fl, list) else [fl]
        sides = [f["side"] for f in fl]
        if len(set(sides)) != len(sides) or set(sides) - {"left", "right"}:
            raise ValueError(f"a swept stoop flares each of its two cheeks once at most, not {sides}")
        return {f["side"]: f for f in fl}

    def _flare_at(self, sw, L, F, n, g, side="right"):
        """T-3134: a swept cheek's flare (`flare`: the side it carries out, and `out_m`) as a
        function of out: nothing beside the landing, then out along the sweep's own reversed
        curve to `out_m` at the foot block, piecewise straight between the nosings' lines so
        the treads' ends and the cheek's inner face are one line. None without a flare.
        T-3144: either cheek may flare, and a negative `out_m` draws it in toward the stoop's
        axis instead (1812's south cheek, the Levy print); the value is measured outward
        from the axis on that side, so the caller turns it into s with the side's sign."""
        fl = self._flares(sw).get(side)
        if not fl:
            return None
        o1, m = F - sw["block_m"], fl["out_m"]
        smooth = lambda o: 0.0 if o <= L else m if o >= o1 else m * (1.0 - math.cos(math.pi * (o - L) / (o1 - L))) / 2.0
        nodes = sorted({round(L + k * g, 9) for k in range(n)} | {round(o1, 9), round(F, 9)})
        vals = [smooth(o) for o in nodes]

        def at(o):
            if o <= nodes[0]:
                return vals[0]
            for (oa, va), (ob, vb) in zip(zip(nodes, vals), zip(nodes[1:], vals[1:])):
                if o <= ob + 1e-12:
                    return va + (vb - va) * (o - oa) / (ob - oa)
            return vals[-1]
        return at, nodes

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
        # T-3135: or the floor of a projection the arch is cut into carries that end (1812's)
        held = {{"left": -1.0, "right": 1.0}[x] for x in st.get("carried", ())}
        if (-W < c - half - 1e-9 and -1.0 not in psides and -1.0 not in held) or \
                (W > c + half + 1e-9 and 1.0 not in psides and 1.0 not in held):
            raise ValueError(f"the door hangs off a stoop {c:+.3f} m off its axis, where no terrace carries it on")
        self.quad("landing", [(c - half, 0, 0), (c + half, 0, 0), (c + half, 0, L), (c - half, 0, L)], Y)
        self.probe(c, 0.0, L / 2, ("landing",), "the landing")
        if not cheeks:
            for x, hx in ((c - half, -1.0), (c + half, 1.0)):
                self.quad("stair_end", [(x, -R, 0), (x, -R, L), (x, 0, L), (x, 0, 0)], (hx, 0.0, 0.0))
        # T-3134: a swept cheek flared out on the stoop's right (1812's north cheek, the Levy print);
        # T-3144: and the left one carried out or drawn in (1812's south cheek, drawn in to its newel)
        sw = st.get("swept") or {}
        swept = cheeks and st.get("cheek_form") == "swept"
        ends = {}
        for side, sgn in (("left", -1.0), ("right", 1.0)):
            fl = self._flare_at(sw, L, L + (n - 1) * g, n, g, side) if swept else None
            if fl:
                ends[side] = (lambda f, k: lambda o: c + k * (half + f(o)))(fl[0], sgn)
                ends[side].nodes = fl[1]
        if swept and 2 * half + sum(f["out_m"] for f in self._flares(sw).values()) < 0.6:
            raise ValueError("a swept stoop's cheeks are drawn in to leave less than 0.6 m of tread at its foot")
        F = self._flight(c - half, c + half, 0.0, L, n, r, g, -1, not cheeks, end_floor=-R,
                         sb_at=ends.get("right"), sa_at=ends.get("left"))
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
                # T-2918: a record may ask for the carved cheek on a plain stoop (1811's plate)
                if carved or st.get("cheek_form") == "scrolled":
                    self._scrolled_cheek(si, so, sgn, Dq if Dq > L else L, F, R, c, half, t, Dq > L, -(n - 1) * r,
                                         st.get("scroll_block_m", 0.0), st.get("scroll_bow"))
                    if Dq > L:
                        self.quad("cheek", [(si,-R,L),(si,-R,Dq),(si,0,Dq),(si,0,L)],(-sgn,0,0))
                    elif sgn in psides and not carved:
                        # T-3186: an open terrace at the landing's depth takes that side of the
                        # landing, so the cheek's head stands on its front edge, its back end above
                        # the deck faced toward the wall (1901's portico)
                        self.quad("cheek", [(si,0,L),(so,0,L),(so,.85,L),(si,.85,L)],(0,0,-1))
                    else:
                        self._box("cheek",min(si,so),max(si,so),-R,.85,0,L)
                    continue
                if st.get("cheek_form") == "swept" and (not porches or all(q.get("parapet") for q in porches)):
                    # T-2910; T-2952: beside a terrace the cheek starts at the landing's edge
                    self._swept_cheek(si, so, sgn, L, F, R, n, r, g, st["swept"], start=o0)
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
        # T-2960: a veranda open under its deck (1736's) faces its terraces with a skirt over a void
        self._open_under = (st.get("veranda") or {}).get("open_under")
        for q, side in zip(porches, psides):
            deck = half + side * c       # the landing's edge, measured from the door away from the stoop
            self._terrace(q, side, deck + (p["cheek"]["thickness_m"] if cheeks else 0.0), deck, L, R)
        if st.get("balustrade"):
            self._stoop_balustrade(st["balustrade"], psides, half, L, F, n, r, g, R, c)
        if st.get("veranda"):
            spans = [(c - half, c + half)] + [
                (c + half, q["to_s_m"]) if side > 0 else (-q["to_s_m"], c - half)
                for q, side in zip(porches, psides)]
            if any(q.get("out_m", L) > L for q in porches):
                raise ValueError("a veranda stands on a deck one depth: its terraces take no out_m")
            self._veranda(st["veranda"], spans, c, half, L)

    # T-2933: a timber veranda over the landing and its terraces (1736's, the c. 1890 photograph)
    def _veranda(self, V, spans, c, half, L):
        """Square posts on the deck's front edge at `posts_s_m` (from the door's centre), a
        beam over them the deck's whole run, and a hipped lean-to roof from the wall out past
        the beam: its soffit flat at the beam's top, a fascia round its three open sides and
        its top rising `rise_m` to a ridge on the wall, hipped at both ends at the front's
        pitch. A post stands on the deck (a terrace or the landing) and never in the flight's
        mouth, so the stair comes up between two of them."""
        ps, ph, inset = V["post_m"], V["height_m"], V["inset_m"]
        bw, bh = V["beam_m"]
        ov, rise, t = V["roof"]["overhang_m"], V["roof"]["rise_m"], V["roof"]["thickness_m"]
        sa, sb = min(a for a, _ in spans), max(b for _, b in spans)
        oc = L - inset - ps / 2
        # T-2960: open under the deck, each post runs on down past it to grade, the pier the
        # deck stands on, clear in front of the void the terrace's face is set back to
        ou = V.get("open_under")
        y_foot = -self.v["stair"]["floor_m"] if ou else 0.0
        if ou and not 0.0 < ou["skirt_m"] < -y_foot:
            raise ValueError(f"the deck's skirt is {ou['skirt_m']} m, and the deck stands {-y_foot:.3f} m high")
        if ou and oc - ps / 2 <= L - ou["recess_m"] + 1e-6:
            raise ValueError(f"the void under the deck is set back {ou['recess_m']} m, behind posts "
                             f"{L - oc + ps / 2:.3f} m deep: it must clear them")
        for i, x in enumerate(V["posts_s_m"]):
            a, b = x - ps / 2, x + ps / 2
            if not any(s0 - 1e-6 <= a and b <= s1 + 1e-6 for s0, s1 in spans):
                raise ValueError(f"veranda post {i + 1} at s {x:+.3f} does not stand on the deck {spans}")
            if a < c + half - 1e-6 and b > c - half + 1e-6:
                raise ValueError(f"veranda post {i + 1} at s {x:+.3f} stands in the flight's mouth "
                                 f"(s {c - half:+.3f}..{c + half:+.3f})")
            self._box("post", a, b, y_foot, ph, oc - ps / 2, oc + ps / 2, skip=("bottom", "top"))
            self.probe(x, ph / 2, oc + ps / 2, ("post",), f"veranda post {i + 1}")
            if ou:
                self.probe(x, y_foot / 2, oc + ps / 2, ("post",), f"veranda post {i + 1}'s pier")
        yb0, yb1 = ph, ph + bh
        self._box("beam", sa, sb, yb0, yb1, oc - bw / 2, oc + bw / 2, skip=("top",))
        # the roof: soffit, fascia, the front slope and a hip at each end, closed on the wall
        Lo = oc + bw / 2 + ov
        ra, rb = sa - ov, sb + ov
        if rb - ra < 2 * Lo:
            raise ValueError(f"a veranda {rb - ra:.2f} m long and {Lo:.2f} m deep has no ridge to hip")
        ye, yt, yr = yb1, yb1 + t, yb1 + t + rise
        down = (0.0, -1.0, 0.0)
        self.quad("porch_roof", [(ra, ye, 0), (rb, ye, 0), (rb, ye, Lo), (ra, ye, Lo)], down)
        self.quad("porch_roof", [(ra, ye, Lo), (rb, ye, Lo), (rb, yt, Lo), (ra, yt, Lo)], OUT)
        for xx, hx in ((ra, -1.0), (rb, 1.0)):
            self.quad("porch_roof", [(xx, ye, 0), (xx, ye, Lo), (xx, yt, Lo), (xx, yt, 0)], (hx, 0.0, 0.0))
        # T-2961: the slopes are the roof's covering, not its painted joinery (1736's photograph
        # draws its slope textured and darker than the fascia under it)
        self.quad("porch_roof_top", [(ra, yt, Lo), (rb, yt, Lo), (rb - Lo, yr, 0), (ra + Lo, yr, 0)], (0.0, Lo, rise))
        self.quad("porch_roof_top", [(ra, yt, 0), (ra, yt, Lo), (ra + Lo, yr, 0)], (-rise, Lo, 0.0))
        self.quad("porch_roof_top", [(rb, yt, 0), (rb, yt, Lo), (rb - Lo, yr, 0)], (rise, Lo, 0.0))
        self.probe((ra + rb) / 2, ye, Lo / 2, ("porch_roof",), "the veranda's soffit")
        self.meta["veranda"] = {"posts_s_m": list(V["posts_s_m"]), "post_top_m": ph, "beam_y_m": [yb0, yb1],
                                "roof_y_m": [ye, yr], "extent_s": [ra, rb], "extent_out_m": round(Lo, 4),
                                **({"post_foot_m": y_foot, "open_under": dict(ou)} if ou else {})}

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
        ou = getattr(self, "_open_under", None)
        if lg and lg.get("arch"):
            self._arch_face(lg["arch"], m, s_face, S, (s_deck + S) / 2, R, L)
        elif ou:
            # T-2960: a timber deck on its posts, open beneath (1736's veranda, the c. 1890
            # photograph): a skirt board the deck's front, its underside closed back to the
            # void, and the dark of the space under the deck `recess_m` behind the front
            sk, rc = ou["skirt_m"], ou["recess_m"]
            a_, b_ = sorted((m(s_face), m(S)))
            self.quad("skirt", [(m(s_face), -sk, L), (m(S), -sk, L), (m(S), 0, L), (m(s_face), 0, L)], OUT)
            self.quad("skirt", [(a_, -sk, L - rc), (b_, -sk, L - rc), (b_, -sk, L), (a_, -sk, L)], (0.0, -1.0, 0.0))
            self.quad("arch_back", [(m(s_face), -R, L - rc), (m(S), -R, L - rc), (m(S), -sk, L - rc),
                                    (m(s_face), -sk, L - rc)], OUT)
            self.probe(m((s_face + S) / 2), -sk / 2, L, ("skirt",), "the deck's skirt")
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
        if porch.get("parapet"):
            self._parapet(porch["parapet"], m, side, s_face, S, L)
            B = None
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

    # T-2910: a loggia behind the arch (1801's corner loggia, the Taylor photograph) -----
    def _loggia_room(self, lg, arc, s0, s1, a, b, Hd):
        """The room behind a loggia's arch: its floor at the door's, a flat ceiling
        `ceiling_m` up, its sides at `s_m` and its back wall at `depth_m` behind the outer
        face, the door a..b (flat head Hd) in that back wall. The front wall's inner face
        is the room's, round the arch (`arc`, its head right to left, from the jambs'
        spring). `side_arch` opens one side wall onto the street round the corner: a round
        arch `clear_width_m` across centred `centre_m` behind the front, its crown
        `clear_height_m` over the floor, through a `wall_m` wall, and optionally a corbelled
        `balcony` under it on the outer face. Every face is convex: what stands round an
        arch is cut in strips, one to each segment of the head."""
        tf, D, Hc = lg["front_wall_m"], lg["depth_m"], lg["ceiling_m"]
        sa, sb = lg["s_m"]
        if not (sa < s0 and s1 < sb and tf < D and max(y for _, y in arc) + 0.1 <= Hc):
            raise ValueError(f"the loggia (s {sa}..{sb}, {tf}..{D} m deep, ceiling {Hc} m) does not hold its arch")
        self.quad("threshold", [(sa, 0.0, -tf), (sb, 0.0, -tf), (sb, 0.0, -D), (sa, 0.0, -D)], Y)
        self.quad("reveal", [(sa, Hc, -tf), (sb, Hc, -tf), (sb, Hc, -D), (sa, Hc, -D)], (0.0, -1.0, 0.0))

        def round_hole(pieces, lo, hi, arc_):
            """The rectangle lo..hi x 0..Hc less a round-headed hole on `arc_` (right to left)."""
            x0, x1 = arc_[-1][0], arc_[0][0]
            pieces.append([(lo, 0.0), (x0, 0.0), (x0, Hc), (lo, Hc)])
            pieces.append([(x1, 0.0), (hi, 0.0), (hi, Hc), (x1, Hc)])
            for (xa, ya), (xb, yb) in zip(arc_, arc_[1:]):
                if xa - xb > 1e-9:
                    pieces.append([(xb, yb), (xa, ya), (xa, Hc), (xb, Hc)])
            return pieces

        for poly in round_hole([], sa, sb, arc):   # the front wall's inner face
            self.quad("reveal", [(x, y, -tf) for x, y in poly], (0.0, 0.0, -1.0))
        for poly in ([(sa, 0.0), (a, 0.0), (a, Hc), (sa, Hc)], [(b, 0.0), (sb, 0.0), (sb, Hc), (b, Hc)],
                     [(a, Hd), (b, Hd), (b, Hc), (a, Hc)]):   # the back wall round the door
            self.quad("porch_back", [(x, y, -D) for x, y in poly], OUT)
        sd = lg.get("side_arch")
        for x, k in ((sa, -1.0), (sb, 1.0)):
            if not sd or (sd["side"] == "left") != (k < 0):
                self.quad("reveal", [(x, 0.0, -tf), (x, 0.0, -D), (x, Hc, -D), (x, Hc, -tf)], (-k, 0.0, 0.0))
                continue
            c, w, h = sd["centre_m"], sd["clear_width_m"], sd["clear_height_m"]
            d0, d1 = c - w / 2, c + w / 2
            if not tf + 0.1 <= d0 or not d1 <= D - 0.1 or not h + 0.1 <= Hc:
                raise ValueError(f"the loggia's side arch ({d0:.3f}..{d1:.3f} m, crown {h} m) does not stand in "
                                 f"its side wall ({tf}..{D} m, ceiling {Hc} m)")
            hd = Head("round", d0, d1, h - w / 2)
            ring = Region(d0, d1, 0.0, head=hd).outline()
            xo = x + k * sd["wall_m"]
            for poly in round_hole([], tf, D, ring[2:]):
                self.quad("reveal", [(x, y, -d) for d, y in poly], (-k, 0.0, 0.0))
            cy = h / 2
            for i in range(1, len(ring)):
                p0, p1 = ring[i], ring[(i + 1) % len(ring)]
                m = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
                self.quad("reveal", [(x, p0[1], -p0[0]), (xo, p0[1], -p0[0]), (xo, p1[1], -p1[0]), (x, p1[1], -p1[0])],
                          (0.0, cy - m[1], m[0] - c))
            self.quad("threshold", [(x, 0.0, -d0), (xo, 0.0, -d0), (xo, 0.0, -d1), (x, 0.0, -d1)], Y)
            self.meta["side_arch"] = {"s_m": round(xo, 4), "depth_m": [round(d0, 4), round(d1, 4)],
                                      "spring_m": round(hd.spring, 4), "crown_m": round(hd.apex(), 4)}
            bal = sd.get("balcony")
            if bal:
                # its top the arch's sill, its face `height_m` deep, then corbelled back into the wall
                # `corbel_m` lower, `span_m` [from, to] behind the front and `out_m` before the wall
                (e0, e1), out, hb, hc_ = bal["span_m"], bal["out_m"], bal["height_m"], bal["corbel_m"]
                xf = xo + k * out
                lo, hi = sorted((xo, xf))
                self._box("balcony", lo, hi, -hb, 0.0, -e1, -e0, skip=("left" if k > 0 else "right", "bottom"))
                yb = -hb - hc_
                for e in (e0, e1):
                    self.quad("balcony", [(xo, -hb, -e), (xf, -hb, -e), (xo, yb, -e)], (0.0, 0.0, 1.0 if e == e0 else -1.0))
                self.quad("balcony", [(xf, -hb, -e0), (xf, -hb, -e1), (xo, yb, -e1), (xo, yb, -e0)], (k * hc_, -out, 0.0))
                self.meta["side_arch"]["balcony"] = {"out_m": out, "foot_m": round(yb, 4)}
                cv = lg.get("carving")
                if cv:   # T-2923: its carved face, the Taylor photograph's
                    self._balcony_panels(xf, k, e0, e1, hb, cv["balcony_panels"])
                    self.meta["side_arch"]["balcony"]["panels"] = cv["balcony_panels"]

    def _balcony_panels(self, x, k, e0, e1, hb, n):
        """T-2923: the side arch's balcony face (at `x`, facing `k`) carved in `n` panels, as the
        Taylor photograph shows 1801's: raised ribs round and between them, 0.03 m inside the
        face's edges, and a raised lozenge in each. The print's carving inside the panels is
        not readable; the lozenges stand for it (docs/LIBERTIES.md L-kimball-1801-loggia-carving-2923)."""
        to3 = lambda a, b, z: (x + k * z, b, a)
        hint, rib, h, m = (float(k), 0.0, 0.0), 0.05, 0.02, 0.03
        a0, a1, b0, b1 = -e1 + m, -e0 - m, -hb + m, -m
        rect = lambda x0, x1, y0, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        self._raised("balcony", to3, rect(a0, a1, b0, b0 + rib), h, hint)
        self._raised("balcony", to3, rect(a0, a1, b1 - rib, b1), h, hint)
        step = (a1 - a0 - rib) / n
        for i in range(n + 1):
            x0 = a0 + i * step
            self._raised("balcony", to3, rect(x0, x0 + rib, b0 + rib, b1 - rib), h, hint)
        for i in range(n):
            ac, bc = a0 + rib + (i + 0.5) * step - rib / 2, (b0 + b1) / 2
            hw, hh = min(0.12, (step - rib) / 2 - 0.05), (b1 - b0) / 2 - rib - 0.05
            self._raised("balcony", to3, [(ac, bc - hh), (ac + hw, bc), (ac, bc + hh), (ac - hw, bc)], h, hint)

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
        # T-2845: the far pedestal may stand in from the terrace's end (1808's, the first-floor
        # plan under the 1888 plate, stands it about 0.2 m in from the north corner)
        fi = P.get("far_inset_m", 0.0)
        Sp = S - fi
        if not (fi >= 0.0 and 2 * pw + 0.6 <= Sp - s_deck and pd < D):
            raise ValueError(f"the loggia's pedestals ({pw} x {pd} m, the far one {fi} m in) do not fit its "
                             f"{S - s_deck:.3f} x {D} m deck")
        for a, b, sk in ((s_deck, s_deck + pw, ()), (Sp - pw, Sp, ())):
            s0, s1 = lo(a, b)
            self._box("pedestal", s0, s1, 0.0, ph, D - pd, D, skip=("bottom",))
            self.probe(m((a + b) / 2), ph / 2, D, ("pedestal",), "a loggia pedestal's face")
        # the parapet between the pedestals, and along the far side to the wall
        wt, wh = W["thickness_m"], W["height_m"]
        if wh > ph:
            raise ValueError("the loggia's parapet stands over its pedestals")
        s0, s1 = lo(s_deck + pw, Sp - pw)
        if carved:
            self._pierced_panel(s0, s1, 0.0, wh, D-wt, D)
        else:
            self._box("loggia_wall", s0, s1, 0.0, wh, D - wt, D, skip=("bottom", "left", "right"))
        # T-2845: the side parapet may stand in from the terrace's end too (the plan draws
        # 1808's on its north pedestal's middle), its outer face `side_inset_m` in
        si_ = W.get("side_inset_m", 0.0)
        if not (0.0 <= si_ and Sp - pw <= S - si_ - wt and S - si_ <= Sp):
            raise ValueError(f"the loggia's side parapet ({si_} m in) does not land on its far pedestal")
        s0, s1 = lo(S - si_ - wt, S - si_)
        # T-2877: a rear pedestal stands where the side parapet met the wall, so it runs from that
        rd0 = lg["rear"]["depth_m"] if lg.get("rear") else 0.0
        self._box("loggia_wall", s0, s1, 0.0, wh, rd0, D - pd, skip=("bottom", "back", "front"))
        self.probe(m((s_deck + S) / 2), wh / 2, D, ("loggia_wall",), "the loggia's front parapet")
        # the columns, two to a pedestal side by side along the front
        prof = [[float(r), float(y)] for r, y in C["profile"]]
        ch = C["height_m"]
        cols = []
        # T-2845: the pair's shafts `pitch_m` apart about the pedestal's middle (the kit's
        # default, half the pedestal's width, set them at its quarters); the turned profile
        # must not run the two into each other
        pitch = C.get("pitch_m", pw / 2)
        rmax = max(r for r, _ in prof)
        if not 2 * rmax <= pitch:
            raise ValueError(f"the loggia's shafts ({2 * rmax:.3f} m across) overlap at a {pitch} m pitch")
        for a in (s_deck, Sp - pw):
            for f in (-0.5, 0.5):
                cs, co = m(a + pw / 2 + pitch * f), D - pd / 2
                self._turn((cs, co), [(r, ph + ch * y) for r, y in prof], C["segments"], role="column")
                cols.append([round(cs, 4), round(co, 4)])
            if carved:
                # T-2565: the 1888 plate and the 1965 view both show ONE capital over each
                # pair, a carved block spanning both shafts, not a capital to a column;
                # T-2845: on a pedestal narrower than the pair it spans the shafts' tops
                hw_ = max(pw / 2 - 0.005, pitch / 2 + prof[-1][0])
                self._paired_capital(*lo(a + pw / 2 - hw_, a + pw / 2 + hw_), D - pd / 2, ph + ch)
        # T-2877: a REAR ROW, a pedestal against the wall behind each front one carrying a
        # pair of turned shafts under a paired capital (1808's: the 1888 plate draws a pair
        # behind each front one). The pair stands `axis_m` off the wall, `pitch_m` apart,
        # its profile's radii scaled by `radius_scale`; each defaults to the front's. T-2882: a
        # RESPOND, a flat pier `respond_m` deep and the pedestal's width, may stand on the wall
        # behind the pair from the pedestal's top to the ceiling (1808's: the first-floor plan
        # draws a block about 0.24 m deep at the wall behind each front pedestal, and the plate
        # draws its lit south face beside the north rear pair)
        rear, rcols = lg.get("rear"), []
        if rear:
            rw, rd = rear.get("width_m", pw), rear["depth_m"]
            ra, rp, rk = rear.get("axis_m", rd / 2), rear.get("pitch_m", pitch), rear.get("radius_scale", 1.0)
            rprof = [(r * rk, y) for r, y in prof]
            rr = max(r for r, _ in rprof)
            if not (2 * rr <= rp and rr <= ra <= rd - rr and rd + 0.6 <= D - pd):
                raise ValueError(f"the loggia's rear pairs ({2 * rr:.3f} m shafts at a {rp} m pitch, {ra} m off the "
                                 f"wall) do not stand on their {rd} m pedestals, or leave no deck behind the front ones")
            rs = rear.get("respond_m", 0.0)
            if not 0.0 <= rs <= ra - rr:
                raise ValueError(f"the loggia's rear respond ({rs} m deep) runs into its pair, whose shafts stand "
                                 f"{ra - rr:.3f} m off the wall")
            for a in (s_deck, Sp - pw):
                c = a + pw / 2
                q0, q1 = lo(c - rw / 2, c + rw / 2)
                self._box("pedestal", q0, q1, 0.0, ph, 0.0, rd, skip=("bottom", "back"))
                self.probe(m(c), ph / 2, rd, ("pedestal",), "a rear pedestal's face")
                for f in (-0.5, 0.5):
                    cs = m(c + rp * f)
                    self._turn((cs, ra), [(r, ph + ch * y) for r, y in rprof], C["segments"], role="column")
                    rcols.append([round(cs, 4), round(ra, 4)])
                if carved:
                    hr = max(rw / 2 - 0.005, rp / 2 + rprof[-1][0])
                    self._paired_capital(*lo(c - hr, c + hr), ra, ph + ch)
                    for yy, hh, pd_ in ((0, .1, .05), (ph - .12, .12, .08)):
                        self._box("pedestal", q0 - .03, q1 + .03, yy, yy + hh, rd, rd + pd_,
                                  skip=("back",) + (("bottom",) if yy == 0 else ()))   # on the deck
                    self._panel_relief(q0 + .12, q1 - .12, .23, ph - .2, rd + .02, "pedestal", leaves=False)
                if rs > 0.0:
                    # on the pedestal's top, under the ceiling, against the wall
                    self._box("pedestal", q0, q1, ph, ph + ch, 0.0, rs, skip=("bottom", "top", "back"))
                    self.probe(m(c), ph + ch / 2, rs, ("pedestal",), "a rear respond's face")
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
            for a,b in ((s_deck,s_deck+pw),(Sp-pw,Sp)):
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
                "columns": cols, **({"rear_columns": rcols} if rcols else {}), "entablature_y_m": [round(y0, 4), round(y1, 4)],
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

    def _parapet(self, pp, m, side, a, b, L):
        """T-2952: a stone parapet `height_m` high along a terrace's front from the cheek's face
        (a) to the terrace's end (b), its face on the terrace's edge, pierced by `holes` [rows,
        columns] of square holes `hole_m` across, spaced evenly in its length and height."""
        H, t = pp["height_m"], pp["thickness_m"]
        rows, cols = pp["holes"]
        hw, hh = pp["hole_m"]
        o0, o1 = L - t, L
        gx = (b - a - cols * hw) / (cols + 1)
        gy = (H - rows * hh) / (rows + 1)
        if gx < 0.03 or gy < 0.03:
            raise ValueError(f"a parapet {b - a:.3f} m long and {H} m high holds no {rows} by {cols} holes")
        xs = [a]
        for i in range(cols):
            xs += [a + gx * (i + 1) + hw * i, a + (gx + hw) * (i + 1)]
        xs.append(b)
        ys = [0.0]
        for j in range(rows):
            ys += [gy * (j + 1) + hh * j, (gy + hh) * (j + 1)]
        ys.append(H)
        hole = lambda i, j: i % 2 == 1 and j % 2 == 1
        for i in range(len(xs) - 1):
            for j in range(len(ys) - 1):
                x0, x1, y0, y1 = xs[i], xs[i + 1], ys[j], ys[j + 1]
                if hole(i, j):
                    for (p, q, nrm) in (((x0, y0), (x1, y0), (0.0, 1.0, 0.0)), ((x0, y1), (x1, y1), (0.0, -1.0, 0.0))):
                        self.quad("cheek", [(m(p[0]), p[1], o0), (m(q[0]), q[1], o0), (m(q[0]), q[1], o1),
                                            (m(p[0]), p[1], o1)], nrm)
                    for xe, sg in ((x0, 1.0), (x1, -1.0)):
                        self.quad("cheek", [(m(xe), y0, o0), (m(xe), y1, o0), (m(xe), y1, o1), (m(xe), y0, o1)],
                                  (side * sg, 0.0, 0.0))
                    continue
                for o, nrm in ((o1, OUT), (o0, (0.0, 0.0, -1.0))):
                    self.quad("cheek", [(m(x0), y0, o), (m(x1), y0, o), (m(x1), y1, o), (m(x0), y1, o)], nrm)
        self.quad("cheek", [(m(a), H, o0), (m(b), H, o0), (m(b), H, o1), (m(a), H, o1)], Y)
        self.quad("cheek", [(m(b), 0.0, o0), (m(b), H, o0), (m(b), H, o1), (m(b), 0.0, o1)], (side, 0.0, 0.0))
        self.probe(m((a + b) / 2), H, (o0 + o1) / 2, ("cheek",), "the parapet's top")
        self.meta["parapet"] = {"s": [m(a), m(b)], "height_m": H, "holes": [rows, cols]}

    def _swept_cheek(self, si, so, sgn, L, F, R, n, r, g, sw, start=0.0):
        """T-2910: 1801's cheek walls, as the Taylor photograph shows them: the top level
        `head_m` over the landing beside it, then swept down in one reversed curve (level at
        both ends, steepest at its middle) to a block `block_m` long at the flight's foot whose
        top stands `foot_m` over grade. Laid in vertical strips, so no face spans a curve;
        the top never comes within 0.1 m of the nosing line it runs beside."""
        h0, yF, blk = sw["head_m"], -R + sw["foot_m"], sw["block_m"]
        o1 = F - blk
        if not L < o1 or not yF < h0:
            raise ValueError(f"a swept cheek: its block ({blk} m) and its foot ({sw['foot_m']} m over grade) "
                             f"leave no sweep between the landing and the foot")
        N = 24
        top = lambda o: h0 if o <= L else yF if o >= o1 else \
            yF + (h0 - yF) * (1.0 + math.cos(math.pi * (o - L) / (o1 - L))) / 2.0
        cuts = ([0.0] if start < L else []) + [L] + [L + (o1 - L) * i / N for i in range(1, N)] + [o1, F]
        # T-3134: the right cheek flared out as it descends, its strips cut at the nosings' lines too;
        # T-3144: either cheek, out (a positive out_m) or in toward the axis (a negative one)
        side = "right" if sgn > 0 else "left"
        fl = self._flare_at(sw, L, F, n, g, side)
        dx = (lambda f: lambda o: sgn * f(o))(fl[0]) if fl else (lambda o: 0.0)
        if fl:
            cuts = sorted({round(x, 9) for x in cuts} | {o for o in fl[1] if L < o < o1})
        # T-3144: a row of small openings through the cheek under its top, along the sweep
        holes = self._cheek_holes(sw, side, L, o1, top, n, r, g)
        if holes:
            cuts = sorted({round(x, 9) for x in cuts} | {round(o, 9) for h in holes for o in h})
        nw = sw.get("newel")
        if nw:   # T-3134: the foot block is a newel; the cheek's strips stop at it
            cuts = [o for o in cuts if o <= o1 + 1e-9]
        if start >= L:   # T-2952: beside a terrace its back end stands on the terrace's front edge
            self.quad("cheek", [(si, -R, L), (so, -R, L), (so, h0, L), (si, h0, L)], (0.0, 0.0, -1.0))
        for k in range(1, n):   # the nosing of tread k stands at L + (k-1)g, -k r: and k g further out
            for o in (L + (k - 1) * g, min(L + k * g, F)):
                if top(o) < -k * r + 0.1 - 1e-9:
                    raise ValueError(f"a swept cheek dips to {top(o):.3f} m over tread {k}'s nosing at "
                                     f"{-k * r:.3f} m, {o:.3f} m out")
        u0, u1 = (sw.get("pierced") or {}).get("under_m", 0.0), None
        if holes:
            u1 = u0 + sw["pierced"]["hole_m"][1]
        for a, b in zip(cuts, cuts[1:]):
            ya, yb = top(a), top(b)
            da, db = dx(a), dx(b)
            # an opening may span several strips (a nosing's line can fall inside it)
            hole = next(((h0_, h1_) for h0_, h1_ in holes if h0_ - 1e-6 <= a and b <= h1_ + 1e-6), None)
            for x, hx in ((si, -sgn), (so, sgn)):
                nrm = (hx * (b - a), 0.0, -hx * (db - da))
                if not hole:
                    self.quad("cheek", [(x + da, -R, a), (x + db, -R, b), (x + db, yb, b), (x + da, ya, a)], nrm)
                    continue
                # the face under the opening and over it; the opening's sill and head run with the top
                self.quad("cheek", [(x + da, -R, a), (x + db, -R, b), (x + db, yb - u1, b), (x + da, ya - u1, a)], nrm)
                self.quad("cheek", [(x + da, ya - u0, a), (x + db, yb - u0, b), (x + db, yb, b), (x + da, ya, a)], nrm)
            if hole:   # its four reveals, through the cheek's thickness
                self.quad("cheek", [(si + da, ya - u1, a), (so + da, ya - u1, a), (so + db, yb - u1, b),
                                    (si + db, yb - u1, b)], (0.0, b - a, ya - yb))
                self.quad("cheek", [(si + da, ya - u0, a), (so + da, ya - u0, a), (so + db, yb - u0, b),
                                    (si + db, yb - u0, b)], (0.0, -(b - a), yb - ya))
                for o, d, y_, k in ((a, da, ya, 1.0), (b, db, yb, -1.0)):
                    if abs(o - hole[0]) > 1e-6 and abs(o - hole[1]) > 1e-6:
                        continue   # an inner cut of the opening, not one of its ends
                    self.quad("cheek", [(si + d, y_ - u1, o), (so + d, y_ - u1, o), (so + d, y_ - u0, o),
                                        (si + d, y_ - u0, o)], (0.0, 0.0, k))
            self.quad("cheek", [(si + da, ya, a), (so + da, ya, a), (so + db, yb, b), (si + db, yb, b)],
                      (0.0, b - a, ya - yb))
        if nw:
            self._newel_foot(si + dx(F), sgn, o1, F, -R, yF, nw)
        else:
            self.quad("cheek", [(si, -R, F), (so, -R, F), (so, yF, F), (si, yF, F)], OUT)
        cv = (self.v.get("loggia") or {}).get("carving")
        if cv:   # T-2923: the foot block's carved faces (the Taylor photograph's)
            self._carved_block(si, so, sgn, o1, F, -R, yF, cv["foot_blocks"]["proud_m"])
        mid = (si + so) / 2
        a, b = (cuts[1], cuts[2]) if start < L else (cuts[0], cuts[1])
        fm = si + dx(F) + sgn * nw["width_m"] / 2 if nw else mid
        top_s, foot_s = (mid + dx((a + b) / 2), (top(a) + top(b)) / 2, (a + b) / 2), (fm, yF, (o1 + F) / 2)
        self.sockets[f"handrail_{'left' if sgn < 0 else 'right'}"] = [top_s, foot_s]
        for pt in (top_s, foot_s):
            self.probe(*pt, ("cheek",), "a handrail socket on its cheek")
        self.meta.setdefault("swept_cheeks", {"head_m": h0, "foot_m": sw["foot_m"], "block_m": blk})
        if holes:
            self.meta["pierced_cheek"] = {"side": side, "openings": len(holes),
                                          "out_m": [round(holes[0][0], 4), round(holes[-1][1], 4)]}

    def _cheek_holes(self, sw, side, L, o1, top, n, r, g):
        """T-3144: `pierced` {side, count, hole_m [along the run, high], under_m}: a row of
        `count` openings through that swept cheek, each `under_m` under its top and running
        with it (so a parallelogram where the top falls), spaced evenly along the sweep from
        the landing's edge to the foot block, as the Levy print shows 1812's north cheek. Their
        sills stand clear of the treads they run beside by 0.05 m at least. [] without one."""
        pc = sw.get("pierced")
        if not pc or pc["side"] != side:
            return []
        k, (w, h), u = pc["count"], pc["hole_m"], pc["under_m"]
        gap = (o1 - L - k * w) / (k + 1)
        if k < 1 or w <= 0 or h <= 0 or u < 0.03 or gap < 0.05:
            raise ValueError(f"a swept cheek {o1 - L:.3f} m along its sweep holds no {k} openings {w} m across "
                             f"{u} m under its top")
        out = []
        for i in range(k):
            a = L + gap + i * (w + gap)
            b = a + w
            for o in (a, b):
                tread = -min(n - 1, max(1, math.floor((o - L) / g) + 1)) * r
                if top(o) - u - h < tread + 0.05 - 1e-9:
                    raise ValueError(f"a swept cheek's opening {i + 1} has its sill at {top(o) - u - h:.3f} m, "
                                     f"within 0.05 m of the tread beside it at {tread:.3f} m, {o:.3f} m out")
            out.append((a, b))
        return out

    def _newel_foot(self, si, sgn, o1, F, y0, yF, nw):
        """T-3134: a swept cheek's foot as a newel, as the Levy print shows 1812's: a square
        pedestal `width_m` across from the cheek's inner face outward and the foot block's
        length, under a moulded cap `cap_m` [high, overhang] whose top is the cheek's foot
        line, a turned knob `knob_m` high on it, and a carved panel on its front and its outer
        face, standing for the print's carving (docs/LIBERTIES.md)."""
        w, (ch, ov), kh = nw["width_m"], nw["cap_m"], nw["knob_m"]
        a, b = sorted((si, si + sgn * w))
        yc = yF - ch
        self._box("cheek", a, b, y0, yc, o1, F, skip=("bottom", "top"))
        self._box("cheek", a - ov, b + ov, yc, yF, o1 - ov, F + ov)
        cs, co = (a + b) / 2, (o1 + F) / 2
        kr = min(w, F - o1) * 0.22
        prof = [(kr * 1.1, yF), (kr * 1.1, yF + kh * 0.12), (kr * 0.55, yF + kh * 0.3), (kr * 0.6, yF + kh * 0.42),
                (kr, yF + kh * 0.7), (kr * 0.7, yF + kh * 0.92), (kr * 0.3, yF + kh)]
        self._turn((cs, co), prof, 12, role="cheek")
        top = [(cs + kr * 0.3 * math.cos(2 * math.pi * i / 12), yF + kh, co + kr * 0.3 * math.sin(2 * math.pi * i / 12))
               for i in range(12)]
        self.quad("cheek", top[::-1], Y)
        m, h = 0.06, 0.02
        b0, b1 = y0 + max(0.15, (yc - y0) * 0.45), yc - 0.08
        for inset, z in ((0.0, h), (0.035, h * 1.8)):
            self._raised("cheek", lambda p_, q_, z_: (p_, q_, F + z_),
                         [(a + m + inset, b0 + inset), (b - m - inset, b0 + inset), (b - m - inset, b1 - inset),
                          (a + m + inset, b1 - inset)], z, OUT)
            xo = b if sgn > 0 else a
            self._raised("cheek", lambda p_, q_, z_: (xo + sgn * z_, q_, p_),
                         [(o1 + m + inset, b0 + inset), (F - m - inset, b0 + inset), (F - m - inset, b1 - inset),
                          (o1 + m + inset, b1 - inset)], z, (float(sgn), 0.0, 0.0))
        self.probe(cs, yF, co, ("cheek",), "the newel's cap")
        self.meta.setdefault("newels", []).append({"s_m": [round(a, 4), round(b, 4)], "out_m": [round(o1, 4), round(F, 4)],
                                                   "cap_top_m": round(yF, 4), "knob_m": kh})

    def _raised(self, role, to3, poly, h, hint):
        """A convex outline `poly` ((a, b), counter-clockwise) on a face, raised `h` off it:
        `to3(a, b, z)` is the face's point `z` before it, `hint` the face's outward normal.
        Its sides start 0.005 m inside the face; it has no back."""
        self.quad(role, [to3(a, b, h) for a, b in poly], hint)
        for i in range(len(poly)):
            (a0, b0), (a1, b1) = poly[i], poly[(i + 1) % len(poly)]
            o, e = to3((a0 + a1) / 2, (b0 + b1) / 2, 0.0), to3((a0 + a1) / 2 + b1 - b0, (b0 + b1) / 2 + a0 - a1, 0.0)
            self.quad(role, [to3(a0, b0, -0.005), to3(a1, b1, -0.005), to3(a1, b1, h), to3(a0, b0, h)],
                      tuple(e[k] - o[k] for k in range(3)))

    def _tablet(self, role, to3, a0, a1, b0, b1, h, hint):
        """A round-headed tablet [a0, a1] x [b0, b1] raised `h` off a face, its head a half
        circle on its width, and its field 0.035 m inside raised further, so each reads as a
        moulded frame round its panel."""
        for inset, z in ((0.0, h), (0.035, h * 1.6)):
            x0, x1, y0, y1 = a0 + inset, a1 - inset, b0 + inset, b1 - inset
            r = (x1 - x0) / 2
            sp = y1 - r
            poly = [(x0, y0), (x1, y0)] + [((x0 + x1) / 2 + r * math.cos(math.pi * i / 8), sp + r * math.sin(math.pi * i / 8))
                                           for i in range(9)]
            self._raised(role, to3, poly, z, hint)

    def _carved_block(self, si, so, sgn, o1, F, y0, y1, h):
        """T-2923: the foot block of a swept cheek carved as the Taylor photograph shows 1801's:
        a round-headed tablet on its front and two side by side on its outer face. The print's
        tracery is finer than it can be read at; the tablets stand for it
        (docs/LIBERTIES.md L-kimball-1801-loggia-carving-2923)."""
        lo, hi = sorted((si, so))
        m = 0.05
        b0, b1 = y0 + 0.12, y1 - 0.08
        # the front, `F` out: a along s, b up
        self._tablet("cheek", lambda a, b, z: (a, b, F + z), lo + m, hi - m, b0, b1, h, OUT)
        # the outer face, at `so` facing `sgn`: a along the run, out from the wall
        n = 2
        w = (F - o1 - m * (n + 1)) / n
        to3 = lambda a, b, z: (so + sgn * z, b, a)
        for k in range(n):
            a0 = o1 + m + k * (w + m)
            self._tablet("cheek", to3, a0, a0 + w, b0, b1, h, (float(sgn), 0.0, 0.0))

    def _scrolled_cheek(self,si,so,sgn,start,F,R,c,half,t,terrace,low,blk=0.0,bow=None):
        # A concave swept stone cheek; tessellate in vertical strips, so no fan spans
        # the concavity. T-2565: both pictures end it at the street in a rolled foot,
        # a stone scroll lying across the cheek and standing proud of its outer face,
        # not in a scroll at its head; the sweep runs down onto the roll's crown.
        # T-2984: or the roll stands `blk` up on a plain foot block under its front half
        # (1811's plate), the sweep running down onto its crown there
        # T-3186: or the sweep's power `bow` from 1 (a straight rake onto the roll, 1901's
        # print) toward 2, the concave fall every scrolled cheek had before it
        rr = .2
        Fc = F - rr
        base = -R + blk
        end = base + 2 * rr; peak = .85 if not terrace else 1.0
        top = lambda o: end + (peak - end) * (1 - (o - start) / (Fc - start)) ** (2 if bow is None else bow)
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
        ring = [(base + rr + rr * math.sin(2 * math.pi * k / K), Fc + rr * math.cos(2 * math.pi * k / K)) for k in range(K)]
        for k in range(K):
            (ya, oa), (yb, ob) = ring[k], ring[(k + 1) % K]
            q = 2 * math.pi * (k + .5) / K
            self.quad("cheek", [(s_in, ya, oa), (s_out, ya, oa), (s_out, yb, ob), (s_in, yb, ob)], (0, math.sin(q), math.cos(q)))
        self.quad("cheek", [(s_in, y, o) for y, o in ring], (-sgn, 0, 0))
        self.quad("cheek", [(s_out, y, o) for y, o in ring], (sgn, 0, 0))
        self._volute("cheek", s_out + sgn * .006, base + rr, Fc, rr * .85, 1, (sgn, 0.0, 0.0))
        self._volute("cheek", s_in - sgn * .006, base + rr, Fc, rr * .85, 1, (-sgn, 0.0, 0.0))
        if blk > 0.0:   # the foot block, grade to the roll's underside, under its front half
            self._box("cheek", min(si, so), max(si, so), -R, base, Fc, F)
        mid=(si+so)/2
        def mesh_top(o):
            q=(o-start)/(Fc-start)*N; i=min(N-1,int(q)); f=q-i
            a=start+(Fc-start)*i/N; b=start+(Fc-start)*(i+1)/N
            return top(a)*(1-f)+top(b)*f
        sockets=[(mid,mesh_top(start+.15),start+.15),(mid,mesh_top(Fc-.15),Fc-.15)]
        self.sockets[f"handrail_{'left' if sgn<0 else 'right'}"]=sockets
        for pt in sockets: self.probe(*pt,("cheek",),"a socket on the curved stone cheek")
        self.probe(s_out, base + rr, Fc, ("cheek",), "the cheek's rolled foot")

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
