"""The K06 window kit: every window a true aperture, written straight to glTF.

TICKET T-2297 (piece 1 of T-1848, K06). The kit's sizes are data in
`data/components/prairie_1904/k06_windows.json`; this module reads them and builds
each variant as the openings T-2298 will put on the 1808 exemplar:

  the hole       cut through a wall panel, T-junction free (a cell grid around a
                 flat head, curve strips over an arched one)
  reveal         jambs and head soffit in the wall's own body, outer face to frame
  sill           stone, weathered to fall outward, horns into the jambs, a throated
                 drip under the nose
  head band      a flat lintel, or an arch band from spring to spring
  frame          the box frame's face ring and its sight edges
  sash           one or two sashes, each in its own plane (a double-hung pair's
                 upper sash in the outer track), rails, stiles and muntins
  glass          one thin transparent layer per pane, set into its sash
  blind, curtain behind the innermost glass, inside the room
  backing        the daylight outline carried back and capped: a dark room, so no
                 ray through a pane reaches the sky
  well           a basement light's area well, below grade
  open           (T-1890) a loggia's opening: no frame, sash or glass, the hole carried
                 on dark past the reveal and capped, its mullions the loggia's posts

WHY PURE PYTHON — the reasons k01_frontage.py gives: the gate measures vertices
(depth order, a closed reveal, no doubled faces, one transparent layer), and they
are easiest to hold when this module writes them. `Prim` and the vector helpers are
K01's own, so a K06 face is built exactly as a K01 face is.

    python3 generators/archetypes/k06_windows.py           write the specimen GLB
    python3 generators/archetypes/k06_windows.py --check   refuse if it is stale
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

from archetypes.k01_frontage import Prim, _add, _cross, _dot, _mul, _sub, _unit  # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / "data" / "components" / "prairie_1904" / "k06_windows.json"
GENERATOR = "chicago-4d generators/archetypes/k06_windows.py (K06, T-2297)"
RECONSTRUCTED = 1.0  # k01_frontage_params.CONFIDENCE_VALUE["reconstructed"]

Y = (0.0, 1.0, 0.0)

# Role -> material. A role is what the gate measures (its depth stage); a material
# is what a renderer binds. Fixed order: the file is the same bytes every run.
ROLE_MATERIAL = {
    "wall": "masonry", "reveal": "masonry", "mullion": "masonry",
    "sill": "sill_stone", "head": "head_stone",
    "frame": "joinery", "sash_outer": "joinery", "sash_inner": "joinery",
    "glass_outer": "glass", "glass_inner": "glass",
    "came": "lead_came",
    "blind": "blind", "curtain": "curtain", "backing": "backing",
    "well": "well_brick", "ground": "ground",
}
# The board, not the opening: excluded from an opening's costs.
BOARD_ROLES = ("wall", "ground")


def materials(data: dict) -> dict:
    p = data["parts"]
    g = p["glass"]
    return {
        "masonry": {"color": (0.70, 0.62, 0.50), "roughness": 0.9},
        "sill_stone": {"color": (0.78, 0.74, 0.66), "roughness": 0.85},
        "head_stone": {"color": (0.76, 0.72, 0.64), "roughness": 0.85},
        "joinery": {"color": (0.12, 0.19, 0.14), "roughness": 0.55},
        "glass": {"color": tuple(g["base_color"]), "roughness": g["roughness"],
                  "metallic": g["metallic"], "alpha": g["alpha"]},
        "lead_came": {"color": (0.22, 0.23, 0.24), "roughness": 0.5, "metallic": 0.3},
        "blind": {"color": tuple(p["blind"]["color"]), "roughness": 0.95},
        "curtain": {"color": tuple(p["curtain"]["color"]), "roughness": 0.9},
        "backing": {"color": tuple(p["backing"]["color"]), "roughness": 1.0},
        "well_brick": {"color": (0.55, 0.30, 0.22), "roughness": 0.92},
        "ground": {"color": (0.36, 0.34, 0.30), "roughness": 1.0},
    }


def seed_of(component_id: str, index: int, structure_id: str = "k06_window_kit") -> int:
    """K01's seed rule (k01_contract.json `seed`)."""
    return int(hashlib.sha256(f"{structure_id}|{component_id}|{index}".encode()).hexdigest()[:8], 16)


# -- 2D helpers in the wall plane (s along the wall, y up) ---------------------------------

def _seqsum(xs) -> float:
    """T-3091: a sum added left to right, so a built mesh's bytes never depend on the Python
    minor version's built-in summation (3.12 compensates; T-2363)."""
    t = 0.0
    for x in xs:
        t += x
    return t


def area2(poly) -> float:
    a = 0.0
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        a += p[0] * q[1] - q[0] * p[1]
    return a / 2


def clip(subject, clipper):
    """Sutherland-Hodgman: `subject` clipped to the convex CCW polygon `clipper`."""
    out = list(subject)
    for i, a in enumerate(clipper):
        b = clipper[(i + 1) % len(clipper)]
        inp, out = out, []
        if not inp:
            break
        side = lambda p: (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        for j, p in enumerate(inp):
            q = inp[(j + 1) % len(inp)]
            sp, sq = side(p), side(q)
            if sp >= 0:
                out.append(p)
            if (sp >= 0) != (sq >= 0):
                t = sp / (sp - sq)
                out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def box(s0, s1, y0, y1):
    return [(s0, y0), (s1, y0), (s1, y1), (s0, y1)]


def rise_over_span(v: dict, data: dict) -> float:
    """A segmental head's rise over its span: the kit's working figure, or (T-2818) the
    variant's own, where a drawing reads a flatter head (1623's broad basement light)."""
    return float(v.get("rise_over_span", data["arch"]["segmental"]["working_rise_over_span"]))


class Head:
    """The top of a clear opening s0..s1 whose jambs rise to `spring`."""

    def __init__(self, kind: str, s0: float, s1: float, spring: float, rise_over_span: float = 0.125,
                 radius_ratio: float = 1.0):
        self.kind, self.s0, self.s1, self.spring = kind, s0, s1, spring
        span = s1 - s0
        self.cx, half = (s0 + s1) / 2, span / 2
        # each half's arc is centred on the springing line: on the opposite jamb for the
        # equilateral head, nearer the middle (T-2457: a blunter, drop head) for a radius
        # under the span; 0.5 would be round
        self.cl, self.cr = s0, s1
        if kind == "flat":
            self.rise = 0.0
        elif kind == "segmental":
            self.rise = span * rise_over_span
            self.R = (half * half + self.rise * self.rise) / (2 * self.rise)
            self.cy = spring - (self.R - self.rise)
        elif kind == "round":
            self.rise, self.R, self.cy = half, half, spring
        elif kind == "elliptical":
            # T-3134: a half ellipse on the springing line, its semi-axes the half span and
            # `rise_over_span` of the span: steep at the jambs, flatter at the crown than a
            # segment (1812 Prairie's porch arch, the Levy print)
            self.rise, self.cy = span * rise_over_span, spring
            self.R = half
        elif kind == "pointed" and radius_ratio != 1.0:
            if not 0.5 < radius_ratio < 1.0:
                raise ValueError(f"a drop head's radius_ratio must lie between 0.5 and 1, not {radius_ratio}")
            self.R = span * radius_ratio
            self.cl, self.cr = s1 - self.R, s0 + self.R
            self.rise = math.sqrt(self.R * self.R - (self.R - half) ** 2)
        elif kind == "pointed":
            self.R = span
            self.rise = math.sqrt(span * span - half * half)
        else:
            raise ValueError(f"unknown head {kind!r}")
        self.span = span

    def apex(self) -> float:
        return self.spring + self.rise

    def curve(self, inset: float, xa: float, xb: float):
        """The head inset by `inset` (negative: outward), from x=xa (right) to x=xb (left)."""
        if self.kind == "flat":
            return [(xa, self.spring - inset), (xb, self.spring - inset)]
        if self.kind == "elliptical":
            # an inset ellipse: both semi-axes drawn in by `inset`, its vertices at equal
            # steps of the parametric angle (the round head's 12 over the half)
            ra, rb = self.R - inset, self.rise - inset
            ta = math.acos(max(-1, min(1, (xa - self.cx) / ra)))
            tb = math.acos(max(-1, min(1, (xb - self.cx) / ra)))
            n = 12
            return [(self.cx + ra * math.cos(ta + (tb - ta) * i / n), self.cy + rb * math.sin(ta + (tb - ta) * i / n))
                    for i in range(n + 1)]
        if self.kind in ("segmental", "round"):
            r = self.R - inset
            n = 12 if self.kind == "round" else 8
            ta, tb = math.acos(max(-1, min(1, (xa - self.cx) / r))), math.acos(max(-1, min(1, (xb - self.cx) / r)))
            return [(self.cx + r * math.cos(ta + (tb - ta) * i / n), self.cy + r * math.sin(ta + (tb - ta) * i / n))
                    for i in range(n + 1)]
        r, n = self.R - inset, 6
        out = []
        # right half: the arc centred on the LEFT jamb's spring (the drop head's left centre)
        ac = lambda q: math.acos(max(-1.0, min(1.0, q)))
        cl, cr = self.cl, self.cr
        ta, tb = ac((xa - cl) / r), ac((self.cx - cl) / r)
        out += [(cl + r * math.cos(ta + (tb - ta) * i / n), self.spring + r * math.sin(ta + (tb - ta) * i / n))
                for i in range(n + 1)]
        ta, tb = ac((self.cx - cr) / r), ac((xb - cr) / r)
        out += [(cr + r * math.cos(ta + (tb - ta) * i / n), self.spring + r * math.sin(ta + (tb - ta) * i / n))
                for i in range(1, n + 1)]
        return out


class Region:
    """A rectangle s0..s1 from y0 up, closed by a flat top or by a head's curve."""

    def __init__(self, s0, s1, y0, top_y=None, head=None, head_inset=0.0):
        self.s0, self.s1, self.y0, self.top_y, self.head, self.head_inset = s0, s1, y0, top_y, head, head_inset

    def outline(self, l=0.0, r=0.0, b=0.0, t=0.0):
        """CCW: bottom-left, bottom-right, then the top from right to left."""
        xa, xb = self.s1 - r, self.s0 + l
        if self.head is None:
            top = [(xa, self.top_y - t), (xb, self.top_y - t)]
        else:
            top = self.head.curve(self.head_inset + t, xa, xb)
            if self.head.kind == "segmental" and top[0][1] < self.y0 + b - 1e-9:
                # T-2889: a region that starts on a segmental head's spring (a fanlight's):
                # the arc, inset, meets the spring line inside the jambs, so the region is
                # the segment over that line, its corners where the inset arc crosses it
                r_ = self.head.R - self.head_inset - t
                dx = math.sqrt(max(0.0, r_ * r_ - (self.y0 + b - self.head.cy) ** 2))
                xa, xb = self.head.cx + dx, self.head.cx - dx
                top = self.head.curve(self.head_inset + t, xa, xb)
                top[0], top[-1] = (xa, self.y0 + b), (xb, self.y0 + b)   # on the line exactly
            elif self.head.kind == "elliptical" and top[0][1] < self.y0 + b - 1e-9:
                # T-3134: the same on a half ellipse's spring (1812's porch fanlight): its corners
                # where the inset ellipse crosses the region's foot
                ra, rb = self.head.R - self.head_inset - t, self.head.rise - self.head_inset - t
                q = max(-1.0, min(1.0, (self.y0 + b - self.head.cy) / rb))
                dx = ra * math.sqrt(max(0.0, 1.0 - q * q))
                xa, xb = self.head.cx + dx, self.head.cx - dx
                top = self.head.curve(self.head_inset + t, xa, xb)
                top[0], top[-1] = (xa, self.y0 + b), (xb, self.y0 + b)
        return [(xb, self.y0 + b), (xa, self.y0 + b)] + top


# -- the builder ----------------------------------------------------------------------------

class Opening:
    """One variant built about its own `sill` socket (k01_contract.json opening family):
    origin at the centre of the sill on the outer face, +X along the wall, +Z out."""

    def __init__(self, variant: dict, data: dict, origin=(0.0, 0.0, 0.0), index: int = 0):
        self.v, self.data, self.O = variant, data, origin
        self.prims: dict[str, Prim] = {}
        self.panes: list[dict] = []   # every glass pane as built: sash key + 2D polygon + depth
        self.holes: list[list] = []   # each hole's outline at the outer face
        self.seed = seed_of(variant["id"], index)
        self.meta: dict = {}

    # faces ---------------------------------------------------------------------
    def P(self, s, y, d):
        """s along the wall, y up, d BEHIND the outer face (z = -d)."""
        return (self.O[0] + s, self.O[1] + y, self.O[2] - d)

    def face(self, role, pts, hint):
        # T-2366: a round head's region that starts on its own spring (a fanlight's, a
        # fixed light's upper pane) repeats a corner; a repeated point is no vertex
        # (kept to round heads, whose regions alone do it: the flat and segmental
        # variants' meshes, which committed houses carry, stay their bytes). T-2889: a
        # segmental fanlight's region starts on its spring the same way
        # T-3134: and a half-elliptical head's, which no committed mesh carried before it
        if self.v.get("head") in ("round", "elliptical") or self.v.get("operation") == "double_hung_fanlight":
            pts = [q for i, q in enumerate(pts) if math.dist(q, pts[i - 1]) > 1e-6]
            if len(pts) < 3:
                return
        n = (0.0, 0.0, 0.0)
        for i, a in enumerate(pts):
            b = pts[(i + 1) % len(pts)]
            n = _add(n, ((a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]),
                         (a[0] - b[0]) * (a[1] + b[1])))
        if math.sqrt(_dot(n, n)) < 1e-12:
            return
        n = _unit(n)
        if _dot(n, hint) < 0:
            n = _mul(n, -1)
        au = _cross(Y, n)
        au = _unit(au) if _dot(au, au) > 1e-9 else (1.0, 0.0, 0.0)
        av = _cross(n, au)
        self.prims.setdefault(role, Prim(role)).face(list(pts), n, (pts[0], au, av, 1.0, 1.0, 0.0, 0.0),
                                                     RECONSTRUCTED)

    def plane(self, role, poly2, d, hint=(0.0, 0.0, 1.0)):
        self.face(role, [self.P(s, y, d) for s, y in poly2], hint)

    def ring(self, role, outer, inner, d):
        for i in range(len(outer)):
            j = (i + 1) % len(outer)
            self.plane(role, [outer[i], outer[j], inner[j], inner[i]], d)

    def tube(self, role, poly2, d0, d1, inward=True):
        """Side faces of `poly2` extruded from depth d0 to d1, facing its inside."""
        c = (sum(p[0] for p in poly2) / len(poly2), sum(p[1] for p in poly2) / len(poly2))
        for i in range(len(poly2)):
            a, b = poly2[i], poly2[(i + 1) % len(poly2)]
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            h = (c[0] - m[0], c[1] - m[1], 0.0) if inward else (m[0] - c[0], m[1] - c[1], 0.0)
            self.face(role, [self.P(a[0], a[1], d0), self.P(b[0], b[1], d0),
                             self.P(b[0], b[1], d1), self.P(a[0], a[1], d1)], h)

    def proud(self, role, poly2, out_d):
        """A slab standing proud of the outer face by out_d: front and edges, never the back."""
        self.plane(role, poly2, -out_d)
        self.tube(role, poly2, 0.0, -out_d, inward=False)

    # parts ---------------------------------------------------------------------
    def build(self):
        v, p = self.v, self.data["parts"]
        ov = v.get("overrides", {})
        rev = ov.get("reveal_depth_m", p["reveal_depth_m"]["value"])
        fr, sa, mu = p["frame"], p["sash"], p["muntin"]
        sill = p["sill"]
        W, H = v["clear_width_m"], v["clear_height_m"]
        bays = v.get("bays", 1)
        mull = v.get("mullion_m", 0.0)
        bw = (W - mull * (bays - 1)) / bays
        fall = sill["fall_m"]
        run = rev + sill["projection_m"]
        y_frame = fall * rev / run          # the sill's top where it meets the frame
        self.meta.update({"reveal_depth_m": rev, "bay_width_m": bw, "bays": bays,
                          "sill_top_at_frame_m": y_frame})
        holes = []
        for k in range(bays):
            s0 = -W / 2 + k * (bw + mull)
            s1 = s0 + bw
            kind = v["head"]
            if kind == "flat":
                head = Head("flat", s0, s1, H)
            else:
                ros = rise_over_span(v, self.data)
                rr = v.get("head_radius_ratio", 1.0)    # T-2457: a drop head, its radius under the span
                h0 = Head(kind, s0, s1, 0.0, ros, rr)
                head = Head(kind, s0, s1, H - h0.rise, ros, rr)
            holes.append((s0, s1, head))
        self.meta["heads"] = [{"kind": h.kind, "span_m": round(h.span, 4), "rise_m": round(h.rise, 4),
                               "spring_m": round(h.spring, 4)} for _, _, h in holes]
        for (s0, s1, head) in holes:
            hole = Region(s0, s1, 0.0, top_y=None if head.kind != "flat" else head.spring,
                          head=None if head.kind == "flat" else head)
            outline = hole.outline()
            self.holes.append(outline)
            self._reveal(outline, rev, y_frame)
            if v["operation"] == "open":
                self._open(s0, s1, head, rev, y_frame, p)
                continue
            daylight = self._frame(s0, s1, head, rev, y_frame, fr)
            self._glaze(daylight, head, rev, fr, sa, mu, s0, s1)
        self._sill(holes, rev, run, sill)
        # T-2886: a light set between columns takes a narrower band over its head than the
        # kit's, so it fits the run between their shafts (1637's south bay's cheeks)
        hb = {**p["head_band"], **({"width_m": ov["head_band_m"]} if "head_band_m" in ov else {})}
        self._head_band(holes, hb)
        if v.get("well"):
            self._well(holes, p["well"])
        return self

    def _reveal(self, outline, rev, y_frame):
        """Jambs and soffit from the outer face to the frame. The bottom edge is the sill's."""
        n = len(outline)
        for i in range(1, n):          # skip edge 0 (bottom-left -> bottom-right): the sill
            a, b = outline[i], outline[(i + 1) % n]
            ya_f = y_frame if abs(a[1]) < 1e-9 else a[1]
            yb_f = y_frame if abs(b[1]) < 1e-9 else b[1]
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            c = (sum(q[0] for q in outline) / n, sum(q[1] for q in outline) / n)
            self.face("reveal", [self.P(a[0], a[1], 0), self.P(b[0], b[1], 0),
                                 self.P(b[0], yb_f, rev), self.P(a[0], ya_f, rev)],
                      (c[0] - m[0], c[1] - m[1], 0.0))

    def _open(self, s0, s1, head, rev, y_frame, p):
        """T-1890: an OPEN opening, a loggia's (1801's gabled section, in the Taylor print): no
        frame, sash or glass, the hole carried on past the reveal as the loggia's dark depth and
        capped `backing.depth_m` behind the reveal, so the eye meets shadow, never sky; the
        mullions between its bays are its posts."""
        reg = Region(s0, s1, y_frame, top_y=None if head.kind != "flat" else head.spring,
                     head=None if head.kind == "flat" else head)
        outline = reg.outline()
        d_back = rev + p["backing"]["depth_m"]
        self.tube("backing", outline, rev, d_back)
        self.plane("backing", outline, d_back)
        self.meta["depth_backing_m"] = round(d_back, 4)

    def _frame(self, s0, s1, head, rev, y_frame, fr):
        f = fr["face_m"]
        reg = Region(s0, s1, y_frame, top_y=None if head.kind != "flat" else head.spring,
                     head=None if head.kind == "flat" else head)
        outer = reg.outline()
        inner = reg.outline(f, f, f, f)
        self.ring("frame", outer, inner, rev)
        self.tube("frame", inner, rev, rev + fr["depth_m"])
        self.meta.setdefault("daylight", []).append(inner)
        return Region(s0 + f, s1 - f, y_frame + f, top_y=None if head.kind != "flat" else head.spring - f,
                      head=None if head.kind == "flat" else head, head_inset=f)

    def _cols(self, xs0, xs1, cols, mw):
        """The lights across a sash, xs0..xs1, and the bars between them: `cols` equal lights
        between muntins `mw` wide, or (T-3091) lights in the variant's `light_ratios` between
        posts `post_m` wide, where a picture draws them unequal (1812 Prairie's large window,
        its middle light wider than the two beside it). Each light and bar is (from, to)."""
        lr = self.v.get("light_ratios")
        if lr and len(lr) == cols and cols > 1:
            pw = float(self.v.get("post_m", mw))
            span, tot, x, cells = xs1 - xs0 - pw * (cols - 1), _seqsum(float(r_) for r_ in lr), xs0, []
            for r_ in lr:
                cells.append((x, x + span * r_ / tot))
                x = cells[-1][1] + pw
            return cells, [(a[1], b[0]) for a, b in zip(cells, cells[1:])]
        cw = (xs1 - xs0 - mw * (cols - 1)) / cols
        cells = [(xs0 + i * (cw + mw), xs0 + i * (cw + mw) + cw) for i in range(cols)]
        bars = [(xs0 + i * cw + (i - 1) * mw, xs0 + i * cw + (i - 1) * mw + mw) for i in range(1, cols)]
        return cells, bars

    def _sash(self, role, reg: Region, d, sa, mu, panes, rails, key):
        """A sash ring at depth d, its muntins, and its glass panes behind."""
        l, r, b, t = rails
        outer, inner = reg.outline(), reg.outline(l, r, b, t)
        self.ring(role, outer, inner, d)
        g = d + self.data["parts"]["glass"]["setback_m"]
        self.tube(role, inner, d, g)
        cols, rows = panes
        mw = mu["width_m"]
        xs0, xs1 = reg.s0 + l, reg.s1 - r
        ys0 = reg.y0 + b
        ys1 = max(q[1] for q in inner)
        cells_x, bars_x = self._cols(xs0, xs1, cols, mw)
        # rows divide the straight part of the sash, so an arched top stays one row
        y_top_flat = min(q[1] for q in inner[2:])
        rh = (y_top_flat - ys0 - mw * (rows - 1)) / rows
        for x0, x1 in bars_x:
            bar = clip(box(x0, x1, ys0, ys1 + 1), inner)
            self.plane(role, bar, d)
            for xe in (x0, x1):
                yt = max(q[1] for q in clip(box(xe - 1e-4, xe + 1e-4, ys0, ys1 + 1), inner))
                self.face(role, [self.P(xe, ys0, d), self.P(xe, yt, d), self.P(xe, yt, g), self.P(xe, ys0, g)],
                          (-1.0 if xe == x0 else 1.0, 0.0, 0.0))
        for j in range(1, rows):
            y0 = ys0 + j * rh + (j - 1) * mw
            for xa, xb in cells_x:   # between the vertical bars, so no crossing is drawn twice
                self.plane(role, box(xa, xb, y0, y0 + mw), d)
                for ye, hy in ((y0, -1.0), (y0 + mw, 1.0)):
                    self.face(role, [self.P(xa, ye, d), self.P(xb, ye, d), self.P(xb, ye, g),
                                     self.P(xa, ye, g)], (0.0, hy, 0.0))
        glass_role = "glass_outer" if role == "sash_outer" else "glass_inner"
        for i, (x0, x1) in enumerate(cells_x):
            for j in range(rows):
                y0 = ys0 + j * (rh + mw)
                y1 = y0 + rh if j < rows - 1 else ys1 + 1
                cell = clip(box(x0, x1, y0, y1), inner)
                if len(cell) >= 3 and abs(area2(cell)) > 1e-8:
                    self.plane(glass_role, cell, g)
                    self.panes.append({"sash": key, "poly": cell, "depth_m": g, "col": i, "row": j})
        return g

    def _glaze(self, day: Region, head, rev, fr, sa, mu, s0, s1):
        v, p = self.v, self.data["parts"]
        op = v["operation"]
        stop = 0.012
        d_out = rev + stop
        d_in = d_out + sa["thickness_m"] + sa["parting_m"]
        st, tr, br, mr = sa["stile_m"], sa["top_rail_m"], sa["bottom_rail_m"], sa["meeting_rail_m"]
        panes = tuple(v["panes"])
        flat = head.kind == "flat"
        top_flat = day.top_y if flat else head.spring
        inner_glass = None
        if op in ("double_hung", "double_hung_fanlight", "double_hung_transom"):
            sash_top = top_flat
            if op == "double_hung_fanlight":
                tb = 0.06
                sash_top = head.spring - tb
                bar = box(day.s0, day.s1, sash_top, head.spring)
                self.plane("frame", bar, rev + stop)
                self.face("frame", [self.P(day.s0, sash_top, rev + stop), self.P(day.s1, sash_top, rev + stop),
                                    self.P(day.s1, sash_top, rev + fr["depth_m"]),
                                    self.P(day.s0, sash_top, rev + fr["depth_m"])], (0.0, -1.0, 0.0))
                fan = Region(day.s0, day.s1, head.spring, head=head, head_inset=fr["face_m"])
                self._fanlight(fan, head, d_out, v.get("fanlight_bars", 5), mu)
            if op == "double_hung_transom":
                sash_top = self._transom(day, rev, stop, fr, sa, mu, d_out)
            arched_upper = op == "double_hung" and not flat
            meet = (day.y0 + (sash_top if not arched_upper else head.spring)) / 2
            up = Region(day.s0, day.s1, meet - mr, top_y=None if arched_upper else sash_top,
                        head=head if arched_upper else None, head_inset=day.head_inset)
            self._sash("sash_outer", up, d_out, sa, mu, panes, (st, st, mr, tr), "upper")
            low = Region(day.s0, day.s1, day.y0, top_y=meet)
            inner_glass = self._sash("sash_inner", low, d_in, sa, mu, panes, (st, st, br, mr), "lower")
            self.meta["meeting_rail_m"] = round(meet, 4)
        elif op == "casement_pair_transom":
            # T-2534: a French window — two casement leaves meeting at its middle, down to the
            # floor it opens onto, under a transom bar and a fixed transom light
            sash_top = self._transom(day, rev, stop, fr, sa, mu, d_out)
            mid = (day.s0 + day.s1) / 2
            for a, b, key in ((day.s0, mid, "leaf_left"), (mid, day.s1, "leaf_right")):
                inner_glass = self._sash("sash_outer", Region(a, b, day.y0, top_y=sash_top), d_out, sa, mu,
                                         panes, (st, st, br, tr), key)
        elif op == "casement_transom":
            # T-2752: a casement under a transom bar and its fixed light, in each light of a
            # mullioned group (1625 Prairie's photograph: two or four lights, the transom about
            # a third down)
            sash_top = self._transom(day, rev, stop, fr, sa, mu, d_out)
            inner_glass = self._sash("sash_outer", Region(day.s0, day.s1, day.y0, top_y=sash_top), d_out, sa, mu,
                                     panes, (st, st, br, tr), "casement")
        else:  # fixed, casement, fixed_leaded: one sash in the outer track
            inner_glass = self._sash("sash_outer", day, d_out, sa, mu, panes, (st, st, br, tr), "fixed")
            if op == "fixed_leaded":
                self._cames(day, (st, st, br, tr), inner_glass)
        self._room(day, head, rev, fr, inner_glass, p, top_flat)

    def _transom(self, day: Region, rev, stop, fr, sa, mu, d_out):
        """A transom bar `transom_m` under the daylight's top and the fixed light over it;
        returns the top of what opens under the bar."""
        v, st = self.v, sa["stile_m"]
        if v.get("tiers"):
            return self._tiers(day, rev, fr, sa, mu, d_out)
        tb = 0.06
        t_bot = day.top_y - v["transom_m"]
        sash_top = t_bot - tb
        self.plane("frame", box(day.s0, day.s1, sash_top, t_bot), rev + stop)
        self.face("frame", [self.P(day.s0, sash_top, rev + stop), self.P(day.s1, sash_top, rev + stop),
                            self.P(day.s1, sash_top, rev + fr["depth_m"]),
                            self.P(day.s0, sash_top, rev + fr["depth_m"])], (0.0, -1.0, 0.0))
        self._sash("sash_outer", Region(day.s0, day.s1, t_bot, top_y=day.top_y), d_out, sa, mu,
                   (v.get("transom_lights", 3), 1), (st, st, st, st), "transom")
        self._transom_grid(Region(day.s0, day.s1, t_bot, top_y=day.top_y), st, d_out, mu)
        return sash_top

    def _transom_grid(self, reg: Region, st, d, mu):
        """T-3091: a transom light glazed in small squares (1812 Prairie's north window and its
        projection's transom lights, the Levy photograph): `transom_grid` [across, up] lights
        between muntin bars laid over the light's one glass, as the fanlight lattice is
        (T-2819), the upright bars a millimetre before the level ones. Nothing without it."""
        tg = self.v.get("transom_grid")
        if not tg:
            return
        cols, rows = int(tg[0]), int(tg[1])
        inner = reg.outline(st, st, st, st)
        x0, x1 = min(q[0] for q in inner), max(q[0] for q in inner)
        y0, y1 = min(q[1] for q in inner), max(q[1] for q in inner)
        mw = mu["width_m"]
        cw, rh = (x1 - x0 - mw * (cols - 1)) / cols, (y1 - y0 - mw * (rows - 1)) / rows
        for i in range(1, cols):
            xa = x0 + i * cw + (i - 1) * mw
            self.plane("sash_outer", box(xa, xa + mw, y0, y1), d - 0.001)
        for j in range(1, rows):
            ya = y0 + j * rh + (j - 1) * mw
            self.plane("sash_outer", box(x0, x1, ya, ya + mw), d)

    def _tiers(self, day: Region, rev, fr, sa, mu, d_out):
        """T-2815: fixed lights in tiers over the sash, each on a stone bar across the hole
        (Keith's bow on the 1888 plate: a main sash, a light over it and a top light).
        `tiers` names the bar's depth and each light's clear height, bottom up, measured on
        the hole as the picture's stone reveals draw them; the top light runs to the head.
        Each bar is the wall's stone, its face on the wall's face, back to the frame's back;
        returns the top of the sash under the lowest bar."""
        v, st = self.v, sa["stile_m"]
        bar, lights = float(v["tiers"]["bar_m"]), [float(h) for h in v["tiers"]["lights_m"]]
        H, d_back = v["clear_height_m"], rev + fr["depth_m"]
        top = H
        for n, h in reversed(list(enumerate(lights, 1))):
            lo = top - h
            b0, b1 = lo - bar, lo
            self.plane("mullion", box(day.s0 - fr["face_m"], day.s1 + fr["face_m"], b0, b1), 0.0)
            for y, hy in ((b0, -1.0), (b1, 1.0)):
                self.face("mullion", [self.P(day.s0 - fr["face_m"], y, 0.0), self.P(day.s1 + fr["face_m"], y, 0.0),
                                      self.P(day.s1 + fr["face_m"], y, d_back),
                                      self.P(day.s0 - fr["face_m"], y, d_back)], (0.0, hy, 0.0))
            self._sash("sash_outer", Region(day.s0, day.s1, b1, top_y=min(top, day.top_y)), d_out, sa, mu,
                       (v.get("transom_lights", 3), 1), (st, st, st, st), f"tier{n}")
            self._transom_grid(Region(day.s0, day.s1, b1, top_y=min(top, day.top_y)), st, d_out, mu)
            top = b0
        if top - day.y0 < 0.6:
            raise ValueError(f"{v['id']}: its tiers leave a {top - day.y0:.2f} m sash under them")
        self.meta["tiers_m"] = round(top, 4)
        return top

    def _fanlight(self, fan: Region, head, d, bars, mu):
        outer = fan.outline()
        st = self.data["parts"]["sash"]["stile_m"]
        inner = fan.outline(st, st, 0, st)
        self.ring("sash_outer", outer, inner, d)
        g = d + self.data["parts"]["glass"]["setback_m"]
        self.tube("sash_outer", inner, d, g)
        cx, cy = head.cx, head.spring
        r = head.R - fan.head_inset - st
        if self.v.get("fanlight_grid_m"):
            self._fanlight_grid(inner, d, g, cx, cy, r, mu)
            return
        # sectors between radial bar centre-lines, each a convex wedge
        angles = [math.pi * k / (bars + 1) for k in range(bars + 2)]
        for k in range(bars + 1):
            a0, a1 = angles[k], angles[k + 1]
            wedge = [(cx, cy)] + [(cx + r * math.cos(a0 + (a1 - a0) * i / 3), cy + r * math.sin(a0 + (a1 - a0) * i / 3))
                                  for i in range(4)]
            wedge = clip(wedge, inner)
            self.plane("glass_outer", wedge, g)
            self.panes.append({"sash": "fanlight", "poly": wedge, "depth_m": g, "col": k, "row": 0})
        hw = mu["width_m"] / 2
        ma = self.v.get("middle_arch")
        if ma:   # T-3091: the bars start where the middle light's arch leaves them
            arch = self._middle_arch(fan, head, inner, d, mu, ma)
        else:
            # the bars spring from a half-round hub, so no two of them overlap at the centre
            hub = 0.07
            self.plane("sash_outer", [(cx + hub * math.cos(math.pi * i / 12), cy + hub * math.sin(math.pi * i / 12))
                                      for i in range(13)], d)
        for k in range(1, bars + 1):
            a = angles[k]
            u, n = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
            if ma:
                (mx, my), ro = arch
                b_ = u[0] * (cx - mx) + u[1] * (cy - my)
                hub = -b_ + math.sqrt(max(0.0, b_ * b_ - ((cx - mx) ** 2 + (cy - my) ** 2 - ro * ro)))
                if hub >= r - 0.02:
                    continue
            c0 = (cx + u[0] * hub, cy + u[1] * hub)
            bar = [(c0[0] + n[0] * hw, c0[1] + n[1] * hw), (c0[0] - n[0] * hw, c0[1] - n[1] * hw),
                   (cx - n[0] * hw + u[0] * r, cy - n[1] * hw + u[1] * r),
                   (cx + n[0] * hw + u[0] * r, cy + n[1] * hw + u[1] * r)]
            bar = clip(bar, inner)
            if area2(bar) < 0:
                bar = bar[::-1]
            self.plane("sash_outer", bar, d)

    def _arc_band(self, inner, c, r0, r1, a0, a1, d, n):
        """A curved bar between radii r0 and r1 about c, from angle a0 to a1, in `n` convex
        pieces each clipped to the fanlight's glass."""
        for i in range(n):
            t0, t1 = a0 + (a1 - a0) * i / n, a0 + (a1 - a0) * (i + 1) / n
            q = [(c[0] + r0 * math.cos(t0), c[1] + r0 * math.sin(t0)), (c[0] + r1 * math.cos(t0), c[1] + r1 * math.sin(t0)),
                 (c[0] + r1 * math.cos(t1), c[1] + r1 * math.sin(t1)), (c[0] + r0 * math.cos(t1), c[1] + r0 * math.sin(t1))]
            piece = clip(q if area2(q) > 0 else q[::-1], inner)
            if len(piece) >= 3 and abs(area2(piece)) > 1e-7:
                self.plane("sash_outer", piece if area2(piece) > 0 else piece[::-1], d)

    def _middle_arch(self, fan: Region, head, inner, d, mu, ma):
        """T-3091: a fanlight whose middle light carries an arched head of its own (1812
        Prairie's large window over the balcony, the Levy photograph): the lights under the
        spring stand in `light_ratios` between posts `post_m` wide; over the middle one a
        segmental bar `band_m` deep rises `rise_m` from the posts' heads; a post bar, the
        posts' own width, runs on from each post's head to the head, leaning `post_lean_deg`
        out from upright; and a concentric bar `ring_m` inside the head's own curve crosses
        the radial bars. Each stands a millimetre before the last, so no two are coplanar.
        Returns the arch's centre and outer radius, where the radial bars begin."""
        st = self.data["parts"]["sash"]["stile_m"]
        cols = self.v["panes"][0]
        cells, posts = self._cols(fan.s0 + st, fan.s1 - st, cols, mu["width_m"])
        m0, m1 = cells[cols // 2]
        sp, rise, band = head.spring, float(ma["rise_m"]), float(ma["band_m"])
        half = (m1 - m0) / 2
        ra = (half * half + rise * rise) / (2 * rise)
        c = ((m0 + m1) / 2, sp + rise - ra)
        ta = math.asin(max(-1.0, min(1.0, (sp - c[1]) / ra)))
        self._arc_band(inner, c, ra, ra + band, ta, math.pi - ta, d - 0.003, 12)
        lean = math.radians(float(ma.get("post_lean_deg", 0.0)))
        for p0, p1 in posts:
            sg = -1.0 if (p0 + p1) / 2 < c[0] else 1.0
            u = (sg * math.sin(lean), math.cos(lean))
            L = head.apex() - sp + 1.0
            bar = [(p0, sp), (p1, sp), (p1 + u[0] * L, sp + u[1] * L), (p0 + u[0] * L, sp + u[1] * L)]
            piece = clip(bar if area2(bar) > 0 else bar[::-1], inner)
            if len(piece) >= 3 and abs(area2(piece)) > 1e-7:
                self.plane("sash_outer", piece if area2(piece) > 0 else piece[::-1], d - 0.002)
        if ma.get("ring_m"):
            rc = head.R - fan.head_inset - st - float(ma["ring_m"])
            hc = (head.cx, head.cy)
            tr = math.asin(max(-1.0, min(1.0, (sp - hc[1]) / rc)))
            hw = mu["width_m"] / 2
            self._arc_band(inner, hc, rc - hw, rc + hw, tr, math.pi - tr, d - 0.001, 24)
        return c, ra + band

    def _fanlight_grid(self, inner, d, g, cx, cy, r, mu):
        """T-2819: a fanlight glazed as a lattice of square lights (1623 Prairie's drawing: a
        grid of small square panes in its window's round head) — one glass behind a grid of
        muntin bars `fanlight_grid_m` [across, up] apart, centred on the head's axis and
        laid up from the spring, each bar clipped to the head; the upright bars stand a
        millimetre before the level ones, so their crossings are never coplanar."""
        self.plane("glass_outer", inner, g)
        self.panes.append({"sash": "fanlight", "poly": inner, "depth_m": g, "col": 0, "row": 0})
        qw, qh = self.v["fanlight_grid_m"]
        hw = mu["width_m"] / 2
        n = int(r / qw + 0.5)
        bars = [[(cx + k * qw - hw, cy), (cx + k * qw + hw, cy), (cx + k * qw + hw, cy + r), (cx + k * qw - hw, cy + r)]
                for k in range(-n, n + 1) if abs(k * qw) < r - hw]
        bars += [[(cx - r, cy + k * qh - hw), (cx + r, cy + k * qh - hw), (cx + r, cy + k * qh + hw), (cx - r, cy + k * qh + hw)]
                 for k in range(1, int(r / qh) + 1) if k * qh < r - hw]
        for i, bar in enumerate(bars):
            piece = clip(bar, inner)
            if len(piece) >= 3 and abs(area2(piece)) > 1e-7:
                if area2(piece) < 0:
                    piece = piece[::-1]
                self.plane("sash_outer", piece, d - (0.001 if bar[0][1] == cy else 0.0))

    def _cames(self, day: Region, rails, g):
        """Diamond quarries on lead cames, the two diagonal families a millimetre apart
        in depth so their crossings are never coplanar."""
        qw, qh = self.v["quarry_m"]
        cm = self.v["came_m"]
        bd = self.v.get("border_m")    # T-3091: quarries in a field inside a border
        inner = day.outline(*rails) if not bd else day.outline(*(x + bd for x in rails))
        xs = [q[0] for q in inner]
        ys = [q[1] for q in inner]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        L = (x1 - x0) + (y1 - y0) + qw + qh
        for fam, (sgn, dd) in enumerate(((1, 0.003), (-1, 0.002))):
            dirv = _unit((qw / 2 * sgn, qh / 2, 0.0))
            nrm = (-dirv[1], dirv[0])
            k_lo, k_hi = -int(L / qw) - 2, int(L / qw) + 2
            for k in range(k_lo, k_hi + 1):
                bx = x0 + k * qw if sgn > 0 else x1 - k * qw
                base = (bx, y0)
                a = (base[0] - dirv[0] * L, base[1] - dirv[1] * L)
                b = (base[0] + dirv[0] * L, base[1] + dirv[1] * L)
                hw = cm / 2
                strip = [(a[0] + nrm[0] * hw, a[1] + nrm[1] * hw), (a[0] - nrm[0] * hw, a[1] - nrm[1] * hw),
                         (b[0] - nrm[0] * hw, b[1] - nrm[1] * hw), (b[0] + nrm[0] * hw, b[1] + nrm[1] * hw)]
                if area2(strip) < 0:
                    strip = strip[::-1]
                piece = clip(strip, inner)
                if len(piece) >= 3 and abs(area2(piece)) > 1e-7:
                    self.plane("came", piece, g - dd)
        if bd:
            self._border(day, rails, inner, g, cm, bd)

    def _border(self, day: Region, rails, field, g, cm, bd):
        """T-3091: a leaded light's border and medallion (1812 Prairie's small arched window,
        the Levy photograph: a patterned light, a border of small panes round a figured field):
        a came round the field `border_m` in from the sash, the border between cut into panes
        about `border_pane_m` long, and a came ring `roundel_m` in radius about the head's
        centre, the field's medallion. Each family stands a millimetre before the quarries'."""
        outer = day.outline(*rails)
        hw = cm / 2
        def strip(a, b, w):
            t = _unit((b[0] - a[0], b[1] - a[1], 0.0))
            n = (-t[1] * w, t[0] * w)
            q = [(a[0] + n[0], a[1] + n[1]), (a[0] - n[0], a[1] - n[1]), (b[0] - n[0], b[1] - n[1]),
                 (b[0] + n[0], b[1] + n[1])]
            return q if area2(q) > 0 else q[::-1]
        self.ring("came", day.outline(*(x + bd - hw for x in rails)), day.outline(*(x + bd + hw for x in rails)),
                  g - 0.004)
        c = (_seqsum(q[0] for q in field) / len(field), _seqsum(q[1] for q in field) / len(field))
        per = [(a, b, math.dist(a, b)) for a, b in zip(outer, outer[1:] + outer[:1]) if math.dist(a, b) > 1e-4]
        total = _seqsum(L for _, _, L in per)
        n = max(4, int(total / float(self.v.get("border_pane_m", 0.15)) + 0.5))
        for k in range(n):
            t, acc = total * (k + 0.5) / n, 0.0
            for a, b, L in per:
                if acc + L >= t:
                    f = (t - acc) / L
                    q = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
                    break
                acc += L
            dv = _unit((c[0] - q[0], c[1] - q[1], 0.0))
            e = (q[0] + dv[0] * bd * 1.6, q[1] + dv[1] * bd * 1.6)
            piece = clip(strip(q, e, hw), outer)
            if len(piece) >= 3 and abs(area2(piece)) > 1e-8:
                self.plane("came", piece if area2(piece) > 0 else piece[::-1], g - 0.005)
        rr = self.v.get("roundel_m")
        if rr and day.head is not None:
            m = (day.head.cx, day.head.spring)
            for i in range(24):
                t0, t1 = 2 * math.pi * i / 24, 2 * math.pi * (i + 1) / 24
                q = [(m[0] + (rr - hw) * math.cos(t0), m[1] + (rr - hw) * math.sin(t0)),
                     (m[0] + (rr + hw) * math.cos(t0), m[1] + (rr + hw) * math.sin(t0)),
                     (m[0] + (rr + hw) * math.cos(t1), m[1] + (rr + hw) * math.sin(t1)),
                     (m[0] + (rr - hw) * math.cos(t1), m[1] + (rr - hw) * math.sin(t1))]
                piece = clip(q, field)
                if len(piece) >= 3 and abs(area2(piece)) > 1e-8:
                    self.plane("came", piece if area2(piece) > 0 else piece[::-1], g - 0.006)

    def _room(self, day: Region, head, rev, fr, inner_glass, p, top_flat):
        """Blind, curtain edges and the enclosed dark room, all behind the innermost glass."""
        sa, bl, cu, bk = p["sash"], p["blind"], p["curtain"], p["backing"]
        d_blind = inner_glass - p["glass"]["setback_m"] + sa["thickness_m"] + bl["gap_m"]
        d_cur = d_blind + cu["gap_m"]
        d_back = inner_glass + bk["depth_m"]
        d_tube0 = rev + fr["depth_m"]
        outline = day.outline()
        self.tube("backing", outline, d_tube0, d_back)
        self.plane("backing", outline, d_back)
        lo, hi = bl["drop_range"]
        drop = lo + (hi - lo) * ((self.seed >> 8) & 0xFFFF) / 65535.0
        yt = top_flat
        yb = yt - drop * (yt - day.y0)
        e = 0.008
        self.plane("blind", box(day.s0 + e, day.s1 - e, yb, yt), d_blind)
        self.proud_box_depth("blind", day.s0 + e, day.s1 - e, yb - bl["lath_m"], yb, d_blind, d_blind + 0.02)
        cw = cu["width_fraction"] * (day.s1 - day.s0)
        k, fd = cu["folds"], cu["fold_depth_m"]
        for side in ((0, 1) if self.v.get("curtains", True) else ()):
            xa = day.s0 if side == 0 else day.s1 - cw
            pts = [xa + cw * i / (2 * k) for i in range(2 * k + 1)]
            for i in range(2 * k):
                da = d_cur + (fd if i % 2 else 0.0)
                db = d_cur + (0.0 if i % 2 else fd)
                self.face("curtain", [self.P(pts[i], day.y0, da), self.P(pts[i + 1], day.y0, db),
                                      self.P(pts[i + 1], yt, db), self.P(pts[i], yt, da)], (0.0, 0.0, 1.0))
        self.meta.update({"blind_drop": round(drop, 4), "depth_blind_m": round(d_blind, 4),
                          "depth_curtain_m": round(d_cur, 4), "depth_backing_m": round(d_back, 4)})

    def proud_box_depth(self, role, s0, s1, y0, y1, d0, d1):
        self.plane(role, box(s0, s1, y0, y1), d0)
        self.face(role, [self.P(s0, y0, d0), self.P(s1, y0, d0), self.P(s1, y0, d1), self.P(s0, y0, d1)],
                  (0.0, -1.0, 0.0))

    def _sill(self, holes, rev, run, sill):
        """Stone, falling outward, horns into the jambs, a throated drip under the nose."""
        pr, h, horn, fall = sill["projection_m"], sill["height_m"], sill["horn_m"], sill["fall_m"]
        dr = sill["drip"]
        s0, s1 = holes[0][0] - horn, holes[-1][1] + horn
        top = lambda x: -fall * x / run      # x: out of the face (+), so the frame is x = -rev
        yb = -h
        gf = pr - dr["from_front_m"]           # groove's front edge, out of the face
        gb = gf - dr["width_m"]
        gy = yb + dr["depth_m"]
        Z = lambda s, y, out: self.P(s, y, -out)
        # inside each reveal: the sill's top from the frame to the face
        for (a, b, _h) in holes:
            self.face("sill", [Z(a, top(-rev), -rev), Z(b, top(-rev), -rev), Z(b, top(0), 0), Z(a, top(0), 0)], Y)
        # proud of the face, across the horns
        self.face("sill", [Z(s0, top(0), 0), Z(s1, top(0), 0), Z(s1, top(pr), pr), Z(s0, top(pr), pr)], Y)
        self.face("sill", [Z(s0, top(pr), pr), Z(s1, top(pr), pr), Z(s1, yb, pr), Z(s0, yb, pr)], (0, 0, 1))
        down = (0.0, -1.0, 0.0)
        self.face("sill", [Z(s0, yb, pr), Z(s1, yb, pr), Z(s1, yb, gf), Z(s0, yb, gf)], down)
        self.face("sill", [Z(s0, yb, gf), Z(s1, yb, gf), Z(s1, gy, gf), Z(s0, gy, gf)], (0, 0, -1))
        self.face("sill", [Z(s0, gy, gf), Z(s1, gy, gf), Z(s1, gy, gb), Z(s0, gy, gb)], down)
        self.face("sill", [Z(s0, gy, gb), Z(s1, gy, gb), Z(s1, yb, gb), Z(s0, yb, gb)], (0, 0, 1))
        self.face("sill", [Z(s0, yb, gb), Z(s1, yb, gb), Z(s1, yb, 0), Z(s0, yb, 0)], down)
        for s, hx in ((s0, -1.0), (s1, 1.0)):   # the ends: the profile, in three convex pieces
            for piece in ([(gf, top(gf)), (pr, top(pr)), (pr, yb), (gf, yb)],
                          [(gb, top(gb)), (gf, top(gf)), (gf, gy), (gb, gy)],
                          [(0, top(0)), (gb, top(gb)), (gb, yb), (0, yb)]):
                self.face("sill", [Z(s, y, o) for o, y in piece], (hx, 0.0, 0.0))
        self.meta["sill"] = {"top_at_face_m": 0.0, "nose_m": round(top(pr), 4), "drip_groove_out_m": [gb, gf]}

    def _head_band(self, holes, hb):
        w, out = hb["width_m"], hb["proud_m"]
        s0, s1, head = holes[0][0], holes[-1][1], holes[0][2]
        if head.kind == "flat":
            ear = hb.get("ear_m", 0.12)     # T-2883: a narrow K08 light's lintel stops at its jambs
            self.proud("head", box(s0 - ear, s1 + ear, head.spring, head.spring + w), out)
            return
        inner = head.curve(0.0, s1, s0)
        outer = head.curve(-w, s1 + w, s0 - w)
        for i in range(len(inner) - 1):
            self.plane("head", [inner[i], inner[i + 1], outer[i + 1], outer[i]], -out)
        c = (head.cx, head.spring)
        for curve, sgn in ((outer, 1.0), (inner, -1.0)):
            for i in range(len(curve) - 1):
                a, b = curve[i], curve[i + 1]
                m = ((a[0] + b[0]) / 2 - c[0], (a[1] + b[1]) / 2 - c[1])
                self.face("head", [self.P(a[0], a[1], 0), self.P(b[0], b[1], 0),
                                   self.P(b[0], b[1], -out), self.P(a[0], a[1], -out)], (sgn * m[0], sgn * m[1], 0.0))
        for a, b in ((inner[0], outer[0]), (inner[-1], outer[-1])):
            self.face("head", [self.P(a[0], a[1], 0), self.P(b[0], b[1], 0),
                               self.P(b[0], b[1], -out), self.P(a[0], a[1], -out)], (0.0, -1.0, 0.0))

    def _well(self, holes, wl):
        s0, s1 = holes[0][0] - wl["side_m"], holes[-1][1] + wl["side_m"]
        pj, fl, cp = wl["projection_m"], -wl["floor_below_sill_m"], wl["coping_m"]
        grade = self.meta["grade_m"] = holes[0][2].spring - 0.15
        Z = lambda s, y, o: self.P(s, y, -o)
        self.face("well", [Z(s0, fl, 0), Z(s1, fl, 0), Z(s1, fl, pj), Z(s0, fl, pj)], Y)
        g2 = grade + cp
        self.face("well", [Z(s0, fl, 0), Z(s0, fl, pj), Z(s0, g2, pj), Z(s0, g2, 0)], (1, 0, 0))
        self.face("well", [Z(s1, fl, 0), Z(s1, fl, pj), Z(s1, g2, pj), Z(s1, g2, 0)], (-1, 0, 0))
        self.face("well", [Z(s0, fl, pj), Z(s1, fl, pj), Z(s1, g2, pj), Z(s0, g2, pj)], (0, 0, -1))
        t = wl["wall_m"]
        for (a, b, o0, o1) in ((s0 - t, s0, 0, pj), (s1, s1 + t, 0, pj), (s0 - t, s1 + t, pj, pj + t)):
            self.face("well", [Z(a, g2, o0), Z(b, g2, o0), Z(b, g2, o1), Z(a, g2, o1)], Y)
        self.face("well", [Z(s0 - t, grade, pj + t), Z(s1 + t, grade, pj + t), Z(s1 + t, g2, pj + t),
                           Z(s0 - t, g2, pj + t)], (0, 0, 1))
        for (x, hx) in ((s0 - t, -1.0), (s1 + t, 1.0)):
            self.face("well", [Z(x, grade, 0), Z(x, grade, pj + t), Z(x, g2, pj + t), Z(x, g2, 0)], (hx, 0, 0))
        self.meta["well"] = {"s": [s0, s1], "projection_m": pj, "floor_m": fl, "grade_m": grade}


# -- the specimen board: each variant in its own wall panel -----------------------------------

PANEL_PAD = 0.7
PANEL_GAP = 0.6


def wall_panel(o: Opening, thickness: float):
    """The board's wall around an opening's holes, a T-junction-free cell grid."""
    holes = o.holes
    s_lo = min(q[0] for h in holes for q in h) - PANEL_PAD
    s_hi = max(q[0] for h in holes for q in h) + PANEL_PAD
    apex = max(q[1] for h in holes for q in h)
    well = o.meta.get("well")
    y_lo = (well["floor_m"] if well else -0.6)
    y_hi = apex + 0.6
    xb = {s_lo, s_hi}
    yb = {y_lo, y_hi, 0.0}
    flat_tops = []
    for h in holes:
        xs = [q[0] for q in h]
        xb |= {min(xs), max(xs)}
        spring = h[2][1]          # the top's first point: the right jamb's head
        yb.add(spring)
        flat_tops.append((min(xs), max(xs), spring, len(h) == 4))
    if well:
        xb |= set(well["s"])
        yb.add(well["grade_m"])
    xb, yb = sorted(xb), sorted(yb)
    for i in range(len(xb) - 1):
        for j in range(len(yb) - 1):
            sc, yc = (xb[i] + xb[i + 1]) / 2, (yb[j] + yb[j + 1]) / 2
            if any(a < sc < b and 0 < yc < sp for a, b, sp, _ in flat_tops):
                continue
            if any(a < sc < b and yc > sp and not isflat for a, b, sp, isflat in flat_tops):
                continue      # over an arch: the curve strips below fill it
            if well and yc < well["grade_m"] and not (well["s"][0] < sc < well["s"][1]):
                continue      # below grade, outside the well: in the ground
            o.plane("wall", box(xb[i], xb[i + 1], yb[j], yb[j + 1]), 0.0)
    for h, (a, b, sp, isflat) in zip(holes, flat_tops):
        if isflat:
            continue
        top = h[2:]
        for k in range(len(top) - 1):
            p, q = top[k], top[k + 1]
            o.plane("wall", [(q[0], q[1]), (p[0], p[1]), (p[0], y_hi), (q[0], y_hi)], 0.0)
    # the board's returns and back, so its rooms are boxed in like a house's
    D = max(o.meta["depth_backing_m"] + 0.1, thickness)
    for x, hx in ((s_lo, -1.0), (s_hi, 1.0)):
        o.face("wall", [o.P(x, y_lo, 0), o.P(x, y_hi, 0), o.P(x, y_hi, D), o.P(x, y_lo, D)], (hx, 0.0, 0.0))
    o.face("wall", [o.P(s_lo, y_hi, 0), o.P(s_hi, y_hi, 0), o.P(s_hi, y_hi, D), o.P(s_lo, y_hi, D)], Y)
    o.plane("wall", box(s_lo, s_hi, y_lo, y_hi), D, (0.0, 0.0, -1.0))
    # ground in front of the panel, and round the well
    g = well["grade_m"] if well else y_lo
    G = 1.0
    if well:
        w0, w1, pj = well["s"][0], well["s"][1], well["projection_m"]
        cells = [(s_lo, w0, 0, G), (w1, s_hi, 0, G), (w0, w1, pj, G)]
    else:
        cells = [(s_lo, s_hi, 0, G)]
    for (a, b, o0, o1) in cells:
        o.face("ground", [o.P(a, g, -o0), o.P(b, g, -o0), o.P(b, g, -o1), o.P(a, g, -o1)], Y)
    o.meta["panel"] = {"s": [s_lo, s_hi], "y": [y_lo, y_hi], "thickness_m": thickness}
    return s_hi - s_lo


def load() -> dict:
    return json.loads(DATA.read_text())


def build_variant(v: dict, data: dict, origin=(0.0, 0.0, 0.0), board: bool = True) -> Opening:
    o = Opening(v, data, origin).build()
    if board:
        wall_panel(o, data["host_wall"]["thickness_m"])
    return o


def build_kit(data: dict | None = None) -> list[Opening]:
    data = data or load()
    out, x = [], 0.0
    for v in data["variants"]:
        probe = build_variant(v, data, board=True)
        s_lo, s_hi = probe.meta["panel"]["s"]
        o = build_variant(v, data, origin=(x - s_lo, 0.0, 0.0))
        out.append(o)
        x += (s_hi - s_lo) + PANEL_GAP
    return out


def triangles(o: Opening, include_board: bool = False) -> int:
    return sum(len(p.idx) // 3 for r, p in o.prims.items() if include_board or r not in BOARD_ROLES)


# -- glTF -------------------------------------------------------------------------------------

def _pad(b: bytes, fill: bytes = b"\x00") -> bytes:
    return b + fill * ((4 - len(b) % 4) % 4)


def to_glb(kit: list[Opening], data: dict) -> bytes:
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
        entry = {"name": f"k06_{name}", "pbrMetallicRoughness": {
            "baseColorFactor": [*[round(c, 4) for c in m["color"]], alpha],
            "metallicFactor": m.get("metallic", 0.0), "roughnessFactor": m["roughness"]}}
        if alpha < 1.0:
            entry["alphaMode"] = "BLEND"
        materials_out.append(entry)
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
            "component_id": o.v["id"], "family": "opening", "seed": o.seed,
            "origin": [round(c, 4) for c in o.O],
            "triangles_opening": triangles(o), "triangles_with_board": triangles(o, True),
            "sockets": {"sill": [0.0, 0.0, 0.0],
                        "head": [0.0, round(max(q[1] for h in o.holes for q in h), 4), 0.0],
                        "sash_plane": [0.0, 0.0, -round(o.meta["reveal_depth_m"] + 0.012, 4)]},
            "params": {k: o.v[k] for k in ("head", "clear_width_m", "clear_height_m", "operation", "panes")},
            "measured": {k: o.meta[k] for k in ("depth_blind_m", "depth_curtain_m", "depth_backing_m",
                                                "blind_drop", "heads") if k in o.meta}}})   # T-1890: an open one hangs no blind
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
        "extras": {"k06": {"data": "data/components/prairie_1904/k06_windows.json", "ticket": "T-2297",
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
                  f"{DATA.relative_to(ROOT)}: run python3 generators/archetypes/k06_windows.py")
            return 1
        print(f"ok   {out.relative_to(ROOT)} is the generator's bytes ({len(blob)} B)")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    print(f"wrote {out.relative_to(ROOT)} ({len(blob)} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
