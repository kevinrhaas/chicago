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

T-3050: `hip_mass` adds a K05 hip over the low-v end of the block (1811 Prairie's tall hipped
roof over its bay, the 1888 plate), its street face in the attic's street plane; the attic
then starts inside it and only the high-v wall is a parapet.

T-3063: `rear_fall` drops the rear slope steeply from the ridge to a flat DECK running to the
rear wall, and the coped parapet over it falls with it to a level wall head (1811 Prairie's
south wall behind its tall stack, level in the 1888 plate and the Chicagology print).

T-3730: `raised_front` carries the front's high-v part, from `from_v_m` to the north wall, up
as wall to its own eave at `eave_m` (2130 Prairie's, beside its round tower: both photographs
of 2140 draw that wall up to the cone's eave course while the front's low-v part eaves at the
house's own), and roofs it as one closed solid joined into the union: a street face from that
eave to the ridge, a hip falling south at `south_pitch_deg` over the lower part's street slope
(the valley the Chicagology print draws), its eave box out the house's overhang to the front
and the south, and a rear face buried in the attic behind the ridge. Under it a wall block in
the parapet's role stands from inside the walls' tops to its soffit, so the face above the
lower eave and the cheek over the lower slope are wall; k01_frontage lays them in the front's
stone (`raised_front_box`). docs/LIBERTIES.md L-k01-2130-murdoch-3730 says which numbers are read.
"""

from __future__ import annotations

import math

TOP_HALF_M = 0.45          # the parapet's level top either side of the ridge (K05's stepped default)
# The parapet's front end stops this far behind the street wall's plane. A wall gable's face
# (1619's) stands IN that plane, and two coplanar faces in the union split the gable's face
# along the parapet's edges into a zero-area sliver (check_roof_kit's degenerate rule): 5 mm
# behind it, nothing is coplanar and nothing a visitor can see has moved.
FRONT_SET_M = 0.005
# T-3063: a rear fall's deck falls to the rear wall a quarter inch to the foot, a tin deck's
# usual fall, so it sheds water and its covering has an up-slope to course along
DECK_FALL = 1.0 / 48.0
# T-3730: a raised front's rear face stands this far behind the ridge, inside the attic, and its
# ridge this far under the attic's, so the two street planes cross just in front of the ridge
# instead of sharing it (a shared edge splits into slivers in the union)
RAISED_BACK_M = 2.0
RAISED_RIDGE_DROP_M = 0.02
RAISED_SINK_M = 0.3        # its wall block's foot, this far down inside the walls' tops


def resolve_raised(r: dict, *, depth, width, eave, ridge_back, ridge, overhang, side_wall, fascia) -> dict:
    """T-3730: `gable_roof.raised_front` checked against the gable roof it stands in."""
    from .k01_frontage_params import ParamError
    keys = {"from_v_m", "eave_m", "south_pitch_deg"}
    if not isinstance(r, dict) or set(r) != keys:
        raise ParamError(f"gable_roof.raised_front takes {sorted(keys)}")
    v0, e2, sp = float(r["from_v_m"]), float(r["eave_m"]), float(r["south_pitch_deg"])
    if not 1.0 + side_wall <= v0 <= width - 1.0:
        raise ParamError(f"gable_roof.raised_front.from_v_m {v0}: clear of the south parapet, 1 m short of the width {width}")
    if not eave + 0.5 <= e2 <= ridge - 1.5:
        raise ParamError(f"gable_roof.raised_front.eave_m {e2}: 0.5 m over the eave {eave}, 1.5 m under the ridge {ridge:.3f}")
    if not 30.0 <= sp <= 70.0:
        raise ParamError(f"gable_roof.raised_front.south_pitch_deg {sp}: 30-70")
    top = ridge - RAISED_RIDGE_DROP_M
    ts = (top - e2) / ridge_back
    if math.degrees(math.atan(ts)) < 20.0:
        raise ParamError(f"gable_roof.raised_front: its street face falls at {math.degrees(math.atan(ts)):.1f} deg; "
                         f"under 20 a slate roof sheds no water")
    hef = e2 - overhang * ts
    # the hip's ridge end stands north of its eave by the rise over its pitch; it must leave a ridge
    zr = v0 - overhang + (top - hef) / math.tan(math.radians(sp))
    if zr >= width - side_wall:
        raise ParamError(f"gable_roof.raised_front.south_pitch_deg {sp}: its hip reaches the ridge at v {zr:.2f}, "
                         f"past the north parapet")
    return {"from_v_m": v0, "eave_m": e2, "south_pitch_deg": sp, "street_pitch_deg": round(math.degrees(math.atan(ts)), 4),
            "fascia_top_m": round(hef, 4), "soffit_m": round(hef - fascia, 4), "ridge_m": round(top, 4),
            "hip_ridge_v_m": round(zr, 4)}


def raised(k5, r: dict, D: float, W: float, xr: float, hs: float, o: float) -> tuple:
    """T-3730: the raised front's wall block and its roof (module doc), in the K01 frame, and
    the box its wall faces stand in (x0, x1, z0, z1, y0) for k01_frontage's stone."""
    zs, zn = -r["from_v_m"], -W + FRONT_SET_M
    xa, xw, X1, Zs = xr - RAISED_BACK_M, D - FRONT_SET_M, D + o, -r["from_v_m"] + o
    hs2, hef, top = r["soffit_m"], r["fascia_top_m"], r["ridge_m"]
    zr = -r["hip_ridge_v_m"]
    wall = k5.body_box(xa, xw, zn, zs, hs - RAISED_SINK_M, hs2, role="parapet")
    A, B, C, Dd = (xa, hs2, zn), (X1, hs2, zn), (X1, hs2, Zs), (xa, hs2, Zs)
    A1, B1, C1, D1 = ((q[0], hef, q[2]) for q in (A, B, C, Dd))
    Rn, Rs = (xr, top, zn), (xr, top, zr)
    faces = [([A, B, C, Dd], "soffit", (0.0, -1.0, 0.0)),
             ([B, C, C1, B1], "fascia", (1.0, 0.0, 0.0)),
             ([C, Dd, D1, C1], "fascia", (0.0, 0.0, 1.0)),
             ([Dd, A, A1, D1], "fascia", (-1.0, 0.0, 0.0)),
             ([A, B, B1, A1], "fascia", (0.0, 0.0, -1.0)),
             ([B1, C1, Rs, Rn], "covering", (1.0, 1.0, 0.0)),
             ([C1, D1, Rs], "covering", (0.0, 1.0, 1.0)),
             ([D1, A1, Rn, Rs], "covering", (-1.0, 1.0, 0.0)),
             ([A1, B1, Rn], "parapet", (0.0, 0.0, -1.0))]
    roof = [pl for pl in (k5.oriented(q, role, h) for q, role, h in faces) if pl]
    return [wall, roof], (xa, D + 1e-3, zn - 1e-3, zs + 1e-3, hs - RAISED_SINK_M)


def line(style: str, steps: int, D: float, xr: float, E: float, tf: float, tb: float,
         up: float, top: float, th: float = TOP_HALF_M, fall: dict | None = None) -> list:
    """The parapet's top line in (u, y) from the rear wall's plane (u 0) to the front's (u D):
    every point clears the covering under it by `up`; its head, about the ridge at u `xr`,
    stands level at `top`. T-3063: over a rear fall's deck (`fall`, coped only) the line runs
    level at the deck + `up` from the rear wall to where the fall meets the deck, and climbs
    from there to the head's rear end, `head_back_m` behind the ridge: steeper than the fall,
    so it clears it all the way."""
    def roof(x):
        return E + min((D - x) * tf, x * tb)
    if style == "coped" and fall:
        y0 = fall["deck_m"] + up
        return [(0.0, y0), (fall["deck_from_m"], y0), (xr - fall["head_back_m"], top), (xr + th, top), (D, E + up)]
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
    # T-3050: under a hipped mass the attic starts inside the hip, at `attic_from_m`
    hm = g.get("hip_mass")
    z1 = -hm["attic_from_m"] if hm else 0.0
    rf = g.get("rear_fall")
    # T-3063: behind a rear fall the attic's back is the fall down to the deck, level to the
    # rear wall's plane, where the deck stops: no eave overhangs it
    outline = ([(0.0, hs), (D + o, hs), (D + o, hef), (xr, yr), (rf["deck_from_m"], rf["deck_m"]),
                (0.0, rf["deck_m"] - rf["deck_from_m"] * DECK_FALL)] if rf else [(-o, hs), (D + o, hs), (D + o, hef), (xr, yr), (-o, her)])
    attic = k5.extrude(outline, -W, z1, P,
                       k5.by_edge("covering", "soffit", "fascia"), "fascia", "fascia")
    tw, up = g["parapet_m"], g["upstand_m"]
    top = yr + g["top_above_ridge_m"]
    solids, lines = [], {}
    for side, (c0, c1) in (("south", (-tw, 0.0)), ("north", (-W, -W + tw))):
        if side not in g["ends"]:
            continue
        e = g["ends"][side]
        ln = [(min(x, D - FRONT_SET_M), y)
              for x, y in line(e["style"], e.get("steps", 0), D, xr, E, tf, tb, up, top, fall=rf)]
        # each parapet stands on its wall from the soffit up, the wall's top under the eave
        solids += k5.parapet_element({}, ln, (c0, c1), "z", tw, hs, g["coping_m"], g["drip_m"], 0.0, 0.0)
        lines[side] = [[round(a, 4), round(b, 4)] for a, b in ln]
    solids.append(attic)
    box = None
    if g.get("raised_front"):   # T-3730: the front's high-v part carried up to its own eave
        more, box = raised(k5, g["raised_front"], D, W, xr, hs, o)
        solids += more
    if hm:   # T-3050: the hipped mass over the low-v end, its street face the attic's street plane
        if hm["apex_v_m"] is None:
            hip, _ = k5.hip_element(0.0, D, -hm["v_m"], 0.0, E, tf, o, f)
        else:   # its end faces pitched to the apex's place: K05's ring stack, as the hip's
            X0, X1, Z0, Z1 = -o, D + o, -hm["v_m"] - o, o
            rise = (D / 2 + o) * tf
            tn = math.tan(math.radians(hm["end_pitch_deg"]["north"]))
            ts = math.tan(math.radians(hm["end_pitch_deg"]["south"]))
            za, zb, xc = Z0 + rise / tn, Z1 - rise / ts, D / 2
            zb = max(zb, za)   # a pyramid: the two ends meet at the apex
            rect = k5.inset_rect(X0, X1, Z0, Z1, 0.0)
            hip = k5.ring_stack([(hs, rect), (hef, rect), (hef + rise, [(xc, za), (xc, za), (xc, zb), (xc, zb)])],
                                ["fascia", "covering"], "soffit")
        solids.append(hip)
    solids.append(k5.body_box(0.0, D, -W, 0.0, hs - 1.0, hs))
    return solids, hs, hef, {"ridge_m": yr, "parapet_top_m": round(top, 4), "parapet_lines": lines,
                             **({"hip_apex_m": hm["apex_m"]} if hm else {}),
                             **({"raised_front_box": box} if box else {})}
