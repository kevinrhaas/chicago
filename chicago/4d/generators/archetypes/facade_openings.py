"""Where the openings are on a building's front wall — the one place that answers it.

WHY THIS MODULE EXISTS (T-0459). The owner reported, from the dev preview, that
signboards sit over doors and over windows on walls with blank face going spare;
the Sauganash Hotel's board hangs across a window bay. The cause was not a bad
rule, it was a MISSING INPUT: `tools/generate_business_signboards.py` mentions
doors sixteen times and not once as geometry. Every mention is trade reasoning —
*"lodging is sold to arrivals who have to find the door"* — and the generator
reasoned carefully about which door a board belonged beside while having no idea
where any of them were. So a board was placed at a height and an offset that
suited the trade, and whatever was behind it was behind it.

WHAT IT IS. A Blender-free reader of the archetypes' own set-out. Each archetype's
`*_params` module now states its front elevation's rectangles from the same shared
constants the builder draws them with, and this module composes those into one
answer — so a board placed clear of these rectangles is placed clear of the
geometry a visitor sees. They live in the params modules for the reason
`shopfront_head_z` always has: the commit gate has to read them and the commit gate
has no Blender.

AND THE BUILDERS READ IT (T-0520). For a while they did not: each computed the same
rectangles inline, so the answer this module gives and the mesh a visitor sees were
two copies of one arithmetic held together by a written rule. `frame_storefront`,
`log_dwelling` and `outbuilding` now build their front elevations from these same
functions, so an opening has one place to be moved. Closing that gap cost a
town-wide rebake on its own — the staleness hash covers each builder module byte
for byte, and editing three of them staled 212 of the town's 349 assets.

THE FRAME. `u` runs along the front wall from the footprint polygon's own origin;
`z` is metres above the base of the walls, the datum `buildings.js` sets and the
one the signage record already measures `arm_height_m` in. The archetypes build
their front elevation on the footprint's max-v edge and so does
`_front_edge` in the sign generator, so the two frames are the same frame and no
transform is needed. `u0`/`u1` are the extent of REAL WALL on that plane, which is
not always the footprint's full width: a log dwelling with a front addition faces
the town with a block narrower than its own footprint.

An archetype with no rule here returns None rather than an empty list, and the
difference matters: an empty list says "this wall is blank", None says "nobody
has read this wall yet", and a caller must not hang a board flat on the second.
"""

from __future__ import annotations

from archetypes import frame_storefront_params as _storefront
from archetypes import log_dwelling_params as _log
from archetypes import outbuilding_params as _outbuilding

# Kinds that are holes in the wall, as against applied joinery standing on it.
# Both refuse a signboard; only the first is an "opening" in the ticket's sense.
HOLE_KINDS = frozenset({"door", "window", "shop_door", "show_window",
                        "loft_door", "vent", "open_bay"})


def _storefront_front(p) -> dict:
    mx0, _my0, mx1, _my1 = _storefront.main_extent(p)
    return {"u0": mx0, "u1": mx1, "wall_height_m": float(p.wall_height_m),
            "openings": _storefront.front_openings(p)}


def _outbuilding_front(p) -> dict:
    return {"u0": 0.0, "u1": float(p.width_m),
            "wall_height_m": float(p.wall_height_m),
            "openings": _outbuilding.front_openings(p)}


_FRONT = {
    "frame_storefront": _storefront_front,
    "log_dwelling": _log.front_wall,
    "outbuilding": _outbuilding_front,
}

# Archetypes with no reader yet. Named rather than merely absent, so that a caller
# reporting "no rule for this wall" can say whether the archetype is one this
# project knows about. frame_tavern is the one that matters: it carries eight signs
# today, every one of them on a bracket, an awning or a post, so nothing is hung
# flat on a tavern wall and nothing is silently wrong. The day one is, the caller
# refuses the flat mounting and says so rather than guessing.
UNREAD = ("bridge_timber", "fort_structure", "frame_dwelling", "frame_tavern",
          "palisade", "pier_crib")


def front_wall(archetype: str, params) -> dict | None:
    """`{u0, u1, wall_height_m, openings}` for the front elevation, or None.

    Each opening is `{kind, u0, u1, z0, z1}`. `kind` distinguishes a hole (see
    `HOLE_KINDS`) from applied joinery a board must also stay off — a shopfront
    fascia, or the blank signboard an archetype nails to it.
    """
    fn = _FRONT.get(archetype)
    return None if fn is None else fn(params)


def front_openings(archetype: str, params) -> list[dict] | None:
    wall = front_wall(archetype, params)
    return None if wall is None else wall["openings"]


def clear_spans(wall: dict, z0: float, z1: float, margin_m: float = 0.0) -> list[tuple]:
    """The stretches of `wall` between `u0` and `u1` that nothing occupies between
    heights `z0` and `z1`, widened by `margin_m` around every obstruction.

    A board is a rectangle and a wall is a rectangle with rectangles cut out of it,
    so "is there room" is one interval subtraction in `u` at the band the board would
    occupy. Returned left to right; an empty list means the band is full.
    """
    spans = [(wall["u0"], wall["u1"])]
    for o in wall["openings"]:
        if o["z1"] <= z0 or o["z0"] >= z1:
            continue                      # clears it vertically
        a, c = o["u0"] - margin_m, o["u1"] + margin_m
        cut: list[tuple] = []
        for s0, s1 in spans:
            if c <= s0 or a >= s1:
                cut.append((s0, s1))
                continue
            if a > s0:
                cut.append((s0, a))
            if c < s1:
                cut.append((c, s1))
        spans = cut
    return [(a, c) for a, c in spans if c - a > 1e-9]


def overlaps(wall: dict, u0: float, u1: float, z0: float, z1: float) -> list[dict]:
    """Every obstruction a board of this extent would stand over."""
    return [o for o in wall["openings"]
            if o["u0"] < u1 and o["u1"] > u0 and o["z0"] < z1 and o["z1"] > z0]
