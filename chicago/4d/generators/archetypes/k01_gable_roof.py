"""T-2459: a K01 house's GABLE roof — 1619 Prairie's roof behind its wall gable.

TICKET T-2459 (piece 1 of T-2429, of T-2421). Treat & Foltz's drawing of John H. Hamline's
house (`building_budget_1886_06_hamline_farwell_houses`) slates a steep roof behind the wall
gable, and carries the house's south side wall up above it as a crow-stepped parapet, rising
from the front corner to a tall stack at the ridge. K01's hip cannot be read that way: its
south face falls away from the wall, so nothing on it rises with the wall. The record names
`roof_form: "gable"` and its `gable_roof` (k01_frontage_params._gable_roof resolves and bounds
it); this module builds it as the closed elements k01_frontage.roof joins into ONE solid, as it
joins the hip:

  the attic   the street slope at roof_pitch_deg from the front eave to a ridge parallel to
              the front, `ridge_back_m` behind the wall, and the rear slope down to the rear
              wall's head; its eave boxes front and rear, the soffit level all round at the
              hip's own height, so K10's brackets stand under it unchanged
  parapets    each side wall carried up from the wall head, its own thickness, the attic
              dying into its inner face: `stepped` (crow steps, each level, clearing the
              covering behind it by K05's upstand and carrying its own coping, a level top at
              the ridge) or `coped` (one coping following the slopes at that clearance)

The street slope is the hip's street plane, so the K05 dormer (1619's wall gable) is cut into
it exactly as before. K05's own `parapet_element` builds each parapet, so the slab and its
coping are the kit's. Every number is the record's or K05's (k05_roofs.json parts.parapet,
parts.coping), and docs/LIBERTIES.md L-k01-1619-gable-roof-2459 says which.
"""

from __future__ import annotations

import math

TOP_HALF_M = 0.45          # the parapet's level top either side of the ridge (K05's stepped default)
# The parapet's front end stops this far behind the street wall's plane. A wall gable's face
# (1619's) stands IN that plane, and two coplanar faces in the union split the gable's face
# along the parapet's edges into a zero-area sliver (check_roof_kit's degenerate rule): 5 mm
# behind it, nothing is coplanar and nothing a visitor can see has moved.
FRONT_SET_M = 0.005


def line(style: str, steps: int, D: float, xr: float, E: float, tf: float, tb: float,
         up: float, top: float, th: float = TOP_HALF_M) -> list:
    """The parapet's top line in (u, y) from the rear wall's plane (u 0) to the front's (u D):
    every point clears the covering under it by `up`; its head, about the ridge at u `xr`,
    stands level at `top`."""
    def roof(x):
        return E + min((D - x) * tf, x * tb)
    if style == "coped":
        return [(0.0, E + up), (xr - th, top), (xr + th, top), (D, E + up)]
    pts = []
    # the rear slope: from the rear wall up to the head, each step level at the covering
    # under its higher (inner) end, plus the upstand
    a, b = 0.0, xr - th
    for k in range(steps):
        x0, x1 = a + (b - a) * k / steps, a + (b - a) * (k + 1) / steps
        h = roof(x1) + up
        pts += [(x0, h), (x1, h)]
    pts += [(xr - th, top), (xr + th, top)]
    # the street slope: from the head down to the front wall
    a, b = xr + th, D
    for k in range(steps):
        x0, x1 = a + (b - a) * k / steps, a + (b - a) * (k + 1) / steps
        h = roof(x0) + up
        pts += [(x0, h), (x1, h)]
    out = []
    for q in pts:                 # a riser is two points at one u; drop exact repeats
        if not out or math.dist(out[-1], q) > 1e-9:
            out.append(q)
    return out


def elements(p, k5, E: float, o: float, f: float):
    """The attic and the two parapets as closed K05 elements in the K01 frame (x is u, rear
    wall 0 and street front D; z is -v, south 0 and north -W), with the body under the attic;
    and the heights the rest of the roof is built to: the soffit, the front eave's top, the
    ridge."""
    g = p.gable
    D, W = p.depth_m, p.width_m
    tf = math.tan(math.radians(p.roof_pitch_deg))
    tb = math.tan(math.radians(g["back_pitch_deg"]))
    xr, yr = D - g["ridge_back_m"], g["ridge_m"]
    hef, her = E - o * tf, E - o * tb          # each eave's fascia top, out `o` past its wall
    hs = hef - f                               # the soffit, level all round: the hip's own
    P = k5.frame("z")
    # the attic runs the whole width; its ends are the eave boxes' ends beyond the walls'
    # planes, and over the walls they lie in the parapets' outer faces, which are joined
    # FIRST so the union keeps the parapet's face there and drops the attic's
    attic = k5.extrude([(-o, hs), (D + o, hs), (D + o, hef), (xr, yr), (-o, her)], -W, 0.0, P,
                       k5.by_edge("covering", "soffit", "fascia"), "fascia", "fascia")
    tw, up = g["parapet_m"], g["upstand_m"]
    top = yr + g["top_above_ridge_m"]
    solids, lines = [], {}
    for side, (c0, c1) in (("south", (-tw, 0.0)), ("north", (-W, -W + tw))):
        e = g["ends"][side]
        ln = [(min(x, D - FRONT_SET_M), y) for x, y in line(e["style"], e.get("steps", 0), D, xr, E, tf, tb, up, top)]
        # each parapet stands on its wall from the soffit up, the wall's top under the eave
        solids += k5.parapet_element({}, ln, (c0, c1), "z", tw, hs, g["coping_m"], g["drip_m"], 0.0, 0.0)
        lines[side] = [[round(a, 4), round(b, 4)] for a, b in ln]
    solids += [attic, k5.body_box(0.0, D, -W, 0.0, hs - 1.0, hs)]
    return solids, hs, hef, {"ridge_m": yr, "parapet_top_m": round(top, 4), "parapet_lines": lines}
