"""T-2995: a K01 mansard on SOME of a house's walls — the rest carried up as a straight brick storey.

TICKET T-2995 (piece 2 of T-2962). The 1911 Sanborn draws a mansard as a dashed line inside a
building's outline (the sheet's key: 'Mansard roof'), and on 1736 Prairie that line runs only
along the street front and along the 18th Street wall back to the brick bay (u about 9.9): none
along the north wall, none over the rear. The north wall's figures, '12 12 8', are a wall
thickness for each of three storeys (the key: 'Figures 20, 16, 12, 8 indicate thickness of wall
in inches'), so the north wall stands brick to the third storey's head. K05's mansard (T-2370)
rings all four walls; this module takes it off the walls the record names:

  resolve()       the record's `mansard.straight` bounded: the rear always, the north wall from
                  the rear to `north_to_u_m`, the south wall from the rear to `south_to_u_m`
                  (the house's depth on either means the whole side), the parapet's upstand
  elements()      before the union: on each straight run a brick parapet standing on its wall
                  from the soffit to `upstand_m` over the curb, coped (K05's parapet_element,
                  the flat roof's and the gable's); after it, a cutter outside each straight
                  run's wall plane from under the soffit to the parapet's top, whose faces are
                  `parapet`: the eave box and the lower faces are cut away there, and where the
                  cut crosses a mansard face that runs on (the street front's at the north wall,
                  the south face at `south_to_u_m`) the face's section is closed in the wall's
                  brick — the wall carried up the mansard's profile
  cornice_cut()   the wall head's run the straight walls take, in K10's perimeter s, so the
                  brackets and bed moulding stop where the eave box does
  gutter_dead()   the gutter's run they take, in the rainwater perimeter, and its stop ends

Every number is the record's or K05's (k05_roofs.json parts.parapet, parts.coping);
docs/LIBERTIES.md L-k01-1736-roof-rear-2995 says which.
"""

from __future__ import annotations


SKIN_M = 0.002    # how far proud of a wall's face the lower cutter leaves the eave box: its cut is never
                  # emitted, and it must not lie in the wall face's plane. Two of K01's 1 mm weld quanta:
                  # at 0.5 mm the strip it leaves welded to nothing, and the roof check read its soffit
                  # as degenerate, doubled and misoriented triangles (check_roof_kit, T-2995)


def _err(msg):
    from .k01_frontage_params import ParamError
    return ParamError(f"mansard.straight: {msg}")


def resolve(s: dict, *, depth: float, width: float, side_wall: float, dormers: list) -> dict:
    """The record's `mansard.straight` resolved and bounded, or {} when it names none."""
    if not s:
        return {}
    import json
    from .k01_frontage_params import ROOT
    k5 = json.loads((ROOT / "data" / "components" / "prairie_1904" / "k05_roofs.json").read_text())
    if s.get("rear") is not True:
        raise _err("the straight walls run from the rear (`rear: true`); a mansard on the rear alone is not built")
    north, south = float(s.get("north_to_u_m", 0.0)), float(s.get("south_to_u_m", 0.0))
    for side, u in (("north", north), ("south", south)):
        if not (u == 0.0 or 1.0 <= u <= depth):
            raise _err(f"{side}_to_u_m {u}: 0 (the side keeps its mansard) or 1.0 m to the depth {depth}")
    if north >= depth and south >= depth:
        raise _err("every wall straight leaves only the street front's mansard; build it as a flat roof's front")
    up = float(s.get("upstand_m", k5["parts"]["parapet"]["upstand_min_m"]))
    if not k5["parts"]["parapet"]["upstand_min_m"] <= up <= 1.0:
        raise _err(f"upstand_m {up}: {k5['parts']['parapet']['upstand_min_m']}-1.0 m over the curb")
    for d in dormers:
        face, at = d["face"], float(d["along_m"])
        if face == "rear" or (face == "north" and at < north + 1.0) or (face == "south" and at < south + 1.0):
            raise _err(f"a {face} dormer at {at} m stands on a straight wall (or within 1.0 m of where its "
                       "mansard face ends)")
    return {"north_u_m": min(north, depth), "south_u_m": min(south, depth), "upstand_m": up,
            "thickness_m": float(side_wall), "coping_m": float(k5["parts"]["coping"]["thickness_m"]),
            "drip_m": float(k5["parts"]["coping"]["drip_m"])}


def elements(p, k5, hs: float):
    """The parapets (joined before the union) and the cutters (taken away after it), in the K01
    frame (x = u, z = -v), for the resolved mansard `p.mansard` whose soffit is at `hs`.

    A parapet stands on its wall's top, the eave datum the K01 walls rise to. Each straight run
    takes two cutters. The LOWER, from under the soffit to the eave datum, takes the eave box
    away to SKIN_M off the wall's plane, so its cut lies just proud of the wall's own face and is
    `wall` (never emitted, as the oriel's cut is): the wall's face is what shows there, and the
    two never share a plane. The UPPER, from the eave datum to just under the coping's drip,
    cuts on the plane itself, and its face there is `parapet`: the third storey's brick face.
    Both end in `parapet`, so where a mansard face runs on past a straight run's end (the
    street front's at the north wall, the south face at `south_to_u_m`) its section, the eave
    box's and the lower face's, is closed in the wall's brick."""
    m, s = p.mansard, p.mansard["straight"]
    D, W, o, E = p.depth_m, p.width_m, p.eave_overhang_m, p.eave_m
    tw, cp, dr = s["thickness_m"], s["coping_m"], s["drip_m"]
    top = m["curb_m"] + s["upstand_m"]
    far, lo, hi = o + 1.0, hs - 0.5, top - 0.002

    def pair(plane, out, c0, c1, P):
        sk = SKIN_M if out > 0 else -SKIN_M
        on = lambda i, a, b: "parapet" if abs(a[0] - plane) < 1e-9 and abs(b[0] - plane) < 1e-9 else "wall"  # noqa: E731
        return [k5.extrude([(plane + out, lo), (plane + sk, lo), (plane + sk, E), (plane + out, E)], c0, c1, P,
                           "wall", "parapet", "parapet"),
                k5.extrude([(plane + out, E), (plane, E), (plane, hi), (plane + out, hi)], c0, c1, P,
                           on, "parapet", "parapet")]

    solids = k5.parapet_element({}, [(-W, top), (0.0, top)], (0.0, tw), "x", tw, E, cp, dr, 0.0, 0.0)
    cutters = pair(0.0, -far, -W - far, far, k5.frame("z"))
    for u, (c0, c1), plane, out in ((s["north_u_m"], (-W, -W + tw), -W, -far),
                                    (s["south_u_m"], (-tw, 0.0), 0.0, far)):
        if u <= 0.0:
            continue
        solids += k5.parapet_element({}, [(0.0, top), (u, top)], (c0, c1), "z", tw, E, cp, dr, 0.0, 0.0)
        # along x: the frame's a is z, so the plane is an edge of the section, and the far end
        # is where a mansard face running on past the straight run is cut
        cutters += pair(plane, out, -far, D + far if u >= D else u, k5.frame("x"))
    return solids, cutters, top


def perimeter_span(p) -> tuple[float, float]:
    """The straight walls' run of the wall head as K10 lays it (the street front from south to
    north, then north from the front, the rear from north to south, the south from the rear):
    one span, from where the north wall turns straight to where the south wall stops being."""
    s = p.mansard["straight"]
    D, W = p.depth_m, p.width_m
    return W + D - s["north_u_m"], 2 * W + D + s["south_u_m"]


def gutter_dead(p, A: float, starts: list, P: float):
    """The gutter's dead run, in the rainwater perimeter (its corners `A` past the walls'), and a
    stop end at each live end; a straight wall's own cut face stands where the gutter stops."""
    s = p.mansard["straight"]
    D, W = p.depth_m, p.width_m
    d0 = A + W if s["north_u_m"] >= D else starts[1] + A + D - s["north_u_m"]
    d1 = starts[3] + A + s["south_u_m"] if s["south_u_m"] < D else P + A
    dead = [(d0, d1)] if d1 <= P else [(d0, P), (0.0, d1 - P)]
    return dead, [(d0 % P, 1.0), (d1 % P, -1.0)]
