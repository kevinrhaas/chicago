#!/usr/bin/env python3
"""Which lot of the platted grid every committed footprint stands on.

ROADMAP T-A7. **One implementation, imported by both halves.** T-A6 made the
schedule's room a function of FREE LOTS rather than of roofs, and required the two
halves to derive occupancy "the same way" — which they did, by each carrying its own
copy of the same rule. `tools/reconcile_665.py` decided how many principal roofs a
block could take; `tools/generate_block_infill.py` decided whether the lot the recipe
named was free. Two copies of one rule is how they drift, and a schedule that deals a
roof its own generator refuses is the failure T-A6 exists to prevent. Both now call
this module and there is nothing left to disagree about.

**A building stands on the lot most of it is on, measured, and occupies that lot when
it reaches the part of it another roof would need.** Two tests, and each answers a
failure the centroid rule could not.

*Test one — one building, one lot, by area.* The centroid is a proxy for the building,
and it fails in exactly the case the plat grid was built to handle: a building placed
from typed coordinates before the module existed, standing a metre or two proud of its
own street frontage. Its centroid is then in the ROADWAY, so it stands on no lot of any
block, while a quarter of the building sits on the lot a principal roof is about to be
dealt. Measured on the committed dataset at T-A7, fourteen records were in that
position, the Temple Building among them: 27 % of it is on `blk_south_water_franklin`
lot 0 and it read as standing on nothing at all. Nothing MOVES lot under this test —
every record that has a centroid in a lot has its greatest overlap in the same lot —
so it only ever finds ground the old rule could not see.

*Test two — it has to reach the buildable part.* A footprint may lap over a lot line
without taking anything from the lot: the generator already requires every new roof to
clear its own lot lines by `LOT_MARGIN_M` = 1.5 m, so a neighbour lapping only into
that margin strip has taken a strip no roof could have used anyway. Kinzie's store is
the case — 9.7 m² of it lies on `blk_south_water_franklin` lot 2 and none of it inside
the lot's buildable inset, so that lot is free and the schedule may deal it a roof. The
test needs no constant of its own; it is the placement gate's own margin, read from
the generator so the two cannot drift apart.

Together they are also what keeps this from being a rule that condemns the town it
already built. `recon_1835_west_018` laps 11.9 m² onto `blk_randolph_clinton` lot 2,
where T-A4 stands a principal roof: test one seats that building on lot 4, where 82 %
of it is, so lot 2 stays the roof's own. Whether two roofs three metres apart on
neighbouring lots is right is the separation gate's question and it passed at the time.

The overlap is exact rather than sampled: lot polygons are convex, so clipping the
footprint against the lot (Sutherland–Hodgman) gives the intersection itself. The
subject polygon need not be convex; the clip polygon must be, which is checked.

`SLIVER_M2` is a numerical tolerance and not a policy. Two polygons that share an edge
intersect in a few square millimetres of rounding, and the tolerance is far below
anything a placement gate allows.

## THE ONE EXCEPTION — a business front is shared, and the owner said so

**Owner's ruling, 2026-08-27.** Reconciling the South Water placements with the
committed plat seated five documented stores on lots the roof schedule had already
dealt to that street's anonymous frontage runs (T-0199). Nothing overlapped — every one
of them was checked against every committed footprint in the town and the worst overlap
was zero — so what failed was a RULE, one principal roof to a lot, and the fork went to
the owner because it decides what the town's business front IS rather than where one
building stands. **He was asked whether a platted business-front lot may carry a
documented store at the street AND an anonymous dwelling behind it, or whether the lot
rule holds and the town gives eight roofs and two households back. He chose the first**,
on the reasoning the ticket recommended: the geometry already permits it, and the other
answer pays eight roofs and two households for a rule the corrected data had itself
called into question.

So `exclusive_lots` is the rule the schedule and the generator both ask, and it is
`occupied_lots` less this clause. **A lot of a block's declared business front is not
exhausted by a researched building standing at the street on it.** All three of these
hold or the lot is taken, exactly as before:

1. **The face is a business front.** The lot is named in that block's own `frontage`
   run in `data/reconstruction/1835_platted_block_parcels.json` — a face the block
   programme deals a commercial row, with its `why` written down. An interior lot, a
   side lot, or any lot of a block with no frontage run is untouched by this.
2. **The standing building is researched, not invented.** `researched_ids()` — a record
   this project's own reconstruction programmes wrote is not a documented store, and
   two anonymous roofs on one lot is still one roof too many.
3. **It stands AT the street.** Its street wall is no further back from the committed
   frontage line than the run's own units stand plus one lot margin
   (`setback_m + LOT_MARGIN_M`, both read from the block's own recipe, neither invented
   here). A documented building standing back in the depth of its lot takes the lot,
   because the ground the row needs is the ground it is on.

**Nothing physical is relaxed.** The footprints still may not overlap, still must clear
each other by the separation gate's three metres, still must stand inside their own lot
lines by `LOT_MARGIN_M`, and still may not lap a platted corridor. This clause moves one
line only: whether a documented storefront ALONE entitles a lot, and on a business front
the answer is now no.

**And it did not need a second clause to hold, which is worth recording because the first
attempt wrote one.** Standing the five stores on the plat left one pair at 2.40 m —
`recon_1835_blk_south_water_wells_d1_05` and `carpenter_south_water_store`, side by side
along the face with their fronts level — under the three-metre gate. That gap is AUTHORED,
not derived: that slot stands `clear_west_of` the store by a stated `clear_m`, and
`generate_block_infill.place_frontage`'s own note says where the number belongs — *"the
three-metre separation rule — not this recipe — is what fixes the size of the break"*.
2.4 m was authored while the store stood 6.62 m out in the roadway, where the along-face
break was not the real gap at all. So the RECIPE moved to the gate (2.4 → 3.0 m, with
`clear_why` beside it) rather than the gate to the recipe. One rule changed in this work,
and it is the one above.

## AND ONE RECORD MAY DECLARE THAT IT HOLDS NO LOT AT ALL

**Owner's ruling, 2026-08-30 (T-0384, `docs/CORNER-ORDINAL.md`).** An advertisement that
counts doors off a named corner — "on South-Water st. one door from Dearborn street" —
places a store along a face, and *an ordinal is still not a lot*. A record placed that way
carries a `lot_claim` block saying so, and `no_lot_claim_ids` below is where the
declaration is read: such a record is not a HOLDER of the lot for the clause above, so it
neither entitles the lot nor exhausts it. It is still counted by `occupied_lots`, still a
roof of its block, and still bound by every physical gate. The function's own docstring
carries the reasoning, including why the transparency deliberately runs one way only.
"""

from __future__ import annotations

import functools
import json
import math
from pathlib import Path

from block_faces import face_frame, project

ROOT = Path(__file__).resolve().parent.parent
STRUCTURES = ROOT / "data" / "structures"

# THE THREE EVIDENCE LAYERS, read in ONE place (T-0221). `research` is a record somebody
# recovered from a source; `inferred_household` is a roof the trade-census programme
# raised because an argued household needed somewhere to be; `reconstruction` is a
# count-unit of the 665-roof programme. They are never merged: one of them is this
# project's own output and cannot be read back as evidence about the town.
LAYERS = ("research", "inferred_household", "reconstruction")

# What each `reconstruction.status` means in layer terms. The statuses are the schema's
# own enum (`data/structures.schema.json`), whose description carries the rule this
# module reads: "Named/documented structures do not carry this block."
_LAYER_BY_STATUS = {
    "inferred_anonymous": "reconstruction",
    "inferred_household": "inferred_household",
}

# Where a block's BUSINESS FRONT is declared: the block-parcel recipes' own `frontage`
# entry, face and lots and setback, with the reasoning beside it. Read here rather than
# passed in by each caller for the same reason `LOT_MARGIN_M` is authored here — the
# schedule and the generator must not be able to be handed two different answers.
PARCELS = ROOT / "data" / "reconstruction" / "1835_platted_block_parcels.json"

# A tenth of a metre square. See the module docstring: a tolerance, not a threshold.
SLIVER_M2 = 0.01

# The margin every new roof must keep from its own lot lines. Authored HERE and imported
# by `tools/generate_block_infill.py`, which enforces it on the roofs it places, because
# the two are the same number: the buildable part of a lot is the lot inset by the
# margin, and a neighbour lapping only into the margin strip has taken nothing a roof
# could have stood on. Side lot lines are conjectural (K7: four lots to a face is a
# reading of ONE block), so a wall ON one would be asserting a line the grid does not
# have — which is why the margin exists at all.
LOT_MARGIN_M = 1.5


def world_polygon(phase: dict, datum: dict) -> list[tuple[float, float]]:
    """A phase's footprint in the scene's local ENU frame, metres from the datum."""
    pos, poly = phase["position"], phase["footprint"]["polygon"]
    theta = math.radians(float(pos.get("rotation_deg") or 0))
    cos, sin = math.cos(theta), math.sin(theta)
    e0 = float(pos["utm_e"]) - float(datum["origin_utm_e"])
    n0 = float(pos["utm_n"]) - float(datum["origin_utm_n"])
    return [(e0 + u * cos + v * sin, n0 - u * sin + v * cos) for u, v in poly]


def footprints(datum: dict, exclude: set[str] | frozenset[str] = frozenset()
               ) -> list[tuple[str, list[tuple[float, float]]]]:
    """(structure_id, world polygon) for every committed phase that has both.

    Every phase, not the first: a structure that was rebuilt on a different footprint
    stands on whichever lots its phases stand on, and the ledger counts the roof once
    either way.
    """
    placed: list[tuple[str, list[tuple[float, float]]]] = []
    for path in sorted(STRUCTURES.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record["id"] in exclude:
            continue
        for phase in record.get("phases") or []:
            position = phase.get("position") or {}
            polygon = (phase.get("footprint") or {}).get("polygon") or []
            if position.get("utm_e") is None or len(polygon) < 3:
                continue
            placed.append((record["id"], world_polygon(phase, datum)))
    return placed


def _signed_area(poly: list[tuple[float, float]]) -> float:
    total = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        total += x1 * y2 - x2 * y1
    return total / 2


def area(poly: list[tuple[float, float]]) -> float:
    return abs(_signed_area(poly))


def _convex(poly: list[tuple[float, float]]) -> bool:
    sign = 0
    for i in range(len(poly)):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % len(poly)]
        cx, cy = poly[(i + 2) % len(poly)]
        cross = (bx - ax) * (cy - by) - (by - ay) * (cx - bx)
        if abs(cross) < 1e-9:
            continue
        here = 1 if cross > 0 else -1
        if sign == 0:
            sign = here
        elif here != sign:
            return False
    return True


def overlap_area(subject: list[tuple[float, float]],
                 convex_clip: list[tuple[float, float]]) -> float:
    """Area the subject polygon shares with a CONVEX clip polygon, in square metres."""
    if not _convex(convex_clip):
        raise SystemExit("plat_occupancy: the clip polygon is not convex, so the "
                         "intersection below would be silently wrong. Lot polygons are "
                         "convex by construction — a concave one is the finding")
    clip = convex_clip if _signed_area(convex_clip) > 0 else convex_clip[::-1]

    def inside(p, a, b) -> bool:
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0

    def crossing(p1, p2, a, b):
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = p1, p2, a, b
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if denom == 0:
            return p2
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    out = list(subject)
    for i in range(len(clip)):
        a, b = clip[i], clip[(i + 1) % len(clip)]
        source, out = out, []
        if not source:
            return 0.0
        previous = source[-1]
        for point in source:
            if inside(point, a, b):
                if not inside(previous, a, b):
                    out.append(crossing(previous, point, a, b))
                out.append(point)
            elif inside(previous, a, b):
                out.append(crossing(previous, point, a, b))
            previous = point
    return area(out) if len(out) >= 3 else 0.0


def inset(convex_poly: list[tuple[float, float]], metres: float
          ) -> list[tuple[float, float]]:
    """The convex polygon shrunk by `metres` on every side — a lot's buildable part.

    Returns an empty list where the inset eats the polygon, which on a lot of these
    proportions cannot happen and on a hypothetical narrow one correctly means no roof
    fits.
    """
    poly = convex_poly if _signed_area(convex_poly) > 0 else convex_poly[::-1]
    out = list(poly)
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        length = math.dist(a, b)
        if length == 0:
            continue
        # inward normal of a counter-clockwise edge
        nx, ny = -(b[1] - a[1]) / length, (b[0] - a[0]) / length
        a2 = (a[0] + nx * metres, a[1] + ny * metres)
        b2 = (b[0] + nx * metres, b[1] + ny * metres)
        source, out = out, []
        if not source:
            return []

        def keeps(p, a2=a2, b2=b2) -> bool:
            return (b2[0] - a2[0]) * (p[1] - a2[1]) - (b2[1] - a2[1]) * (p[0] - a2[0]) >= 0

        def meet(p1, p2, a2=a2, b2=b2):
            (x1, y1), (x2, y2), (x3, y3), (x4, y4) = p1, p2, a2, b2
            denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if denom == 0:
                return p2
            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
            return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

        previous = source[-1]
        for point in source:
            if keeps(point):
                if not keeps(previous):
                    out.append(meet(previous, point))
                out.append(point)
            elif keeps(previous):
                out.append(meet(previous, point))
            previous = point
    return out if len(out) >= 3 else []


def lot_holders(grid: dict, datum: dict,
                exclude: set[str] | frozenset[str] = frozenset()
                ) -> dict[str, dict[int, list[str]]]:
    """{block_id: {lot_index: [every structure standing on it, by id]}}.

    Both tests, in order: a building's lot is the one it has the greatest area on, and
    it occupies that lot only if it reaches inside the lot's buildable inset. See the
    module docstring for why each is there and what each was measured against.

    `occupied_lots` names one holder per lot, which is all a "is this lot taken" answer
    ever needed. The owner's business-front clause needs the LIST: a lot the run already
    stands on is not freed by a documented store also standing at the street on it, and
    with only the first id in hand — `carpenter_south_water_store` sorts before
    `recon_1835_blk_south_water_wells_d1_05` — the row unit is invisible and the lot
    reads free. That is the schedule offering a block room it is already using.
    """
    frames = [(block["id"], index, [tuple(p) for p in lot["polygon"]])
              for block in grid["blocks"] for index, lot in enumerate(block["lots"])]
    buildable = {(bid, index): inset(polygon, LOT_MARGIN_M)
                 for bid, index, polygon in frames}

    held: dict[str, dict[int, list[str]]] = {}
    for structure_id, world in footprints(datum, exclude):
        seat, best = None, SLIVER_M2
        for bid, index, polygon in frames:
            here = overlap_area(world, polygon)
            if here > best:
                seat, best = (bid, index), here
        if seat is None:
            continue
        room = buildable[seat]
        if not room or overlap_area(world, room) <= SLIVER_M2:
            continue
        held.setdefault(seat[0], {}).setdefault(seat[1], []).append(structure_id)
    return held


def occupied_lots(grid: dict, datum: dict,
                  exclude: set[str] | frozenset[str] = frozenset()
                  ) -> dict[str, dict[int, str]]:
    """{block_id: {lot_index: the structure standing on it}} across the whole grid.

    Where two structures hold one lot the first by id is named. The map's job is to say
    the lot is taken and by something nameable, not to arbitrate between them — that
    two roofs share a lot is the separation gate's question, and this one's answer is
    the same either way.
    """
    return {block_id: {index: ids[0] for index, ids in sorted(lots.items())}
            for block_id, lots in lot_holders(grid, datum, exclude).items()}


def layer_of_record(record: dict) -> str:
    """Which of the three evidence layers a record belongs to, read off THE RECORD.

    A record one of the generating programmes wrote carries the `reconstruction` block
    that programme writes, and a researched one does not — `data/structures.schema.json`
    states it as a rule ("Named/documented structures do not carry this block") and its
    `status` enum names which programme wrote it. So the layer is a fact the record
    already carries, and this is the only place it is read.

    **It used not to be.** Until T-0221 the layer was read off the ID PREFIX in
    `tools/measure_street_frontage.layer_of` — `recon_1835_*` reconstruction, `inf_*`
    inferred household, everything else research — which is a proxy for this, and a
    proxy that misses `physicians_office`: it carries neither prefix and is nonetheless
    a product of the inferred-household programme, `reconstruction.status:
    "inferred_household"`, occupation physician. Measured across the committed dataset
    the two readings agree on every record but that one. The direction of the
    disagreement is what made it worth closing rather than noting: an INVENTED record
    reading as documented is how a clause about documented buildings, and a gate that
    asserts zero of the generated layers, get crossed by a filename.

    A record built in memory can be asked here; `layer_of` is the same question about a
    committed id. Two readings of one fact is this project's recurring defect and there
    is now one.
    """
    block = record.get("reconstruction")
    if block is None:
        return "research"
    status = block.get("status")
    if status not in _LAYER_BY_STATUS:
        raise ValueError(
            f"{record.get('id')!r} carries a reconstruction block with status "
            f"{status!r}, which no evidence layer is defined for; add it to "
            f"plat_occupancy._LAYER_BY_STATUS beside the schema enum it comes from")
    return _LAYER_BY_STATUS[status]


@functools.lru_cache(maxsize=1)
def layers() -> dict[str, str]:
    """{structure id: evidence layer} across every committed record, from the records."""
    out: dict[str, str] = {}
    for path in sorted(STRUCTURES.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        out[record["id"]] = layer_of_record(record)
    return out


def researched_ids() -> set[str]:
    """Every structure id this project did not itself invent.

    The research layer of `layers()`, which reads each record rather than its name — see
    `layer_of_record` for why that distinction has a record in it.
    """
    return {sid for sid, layer in layers().items() if layer == "research"}


def no_lot_claim_ids() -> set[str]:
    """Every committed structure that declares, in a field, that it stands on no lot.

    **The owner's ruling of 2026-08-30 (T-0384), in code.** A store placed by an ORDINAL
    OFF A CORNER — "on South-Water st. one door from Dearborn street" — is fixed to a
    position along a street face, counted from a crossing. That is narrower than the
    street and it is *not a lot*: the ruling says so in terms, and `docs/CORNER-ORDINAL.md`
    carries it. Such a record declares `lot_claim: {"claims_lot": false, "lot": null}` and
    this is the one place the declaration bites.

    **It bites on ENTITLEMENT, and on nothing physical.** The clause below asks whether a
    lot of a business front is held by ONE documented store standing at the street; a
    record that claims no lot is not a holder of the lot for that question, so it neither
    entitles the lot nor exhausts it, and the schedule and the generator see the lot
    exactly as they would if this record named a different street. Everything physical is
    untouched: the footprint still may not overlap, still clears its neighbours by the
    separation gate's three metres, still stands inside the block's own lot lines and still
    may not lap a platted corridor. `tools/measure_corner_ordinals.py` is the gate that
    holds all of that together.

    **`occupied_lots` still counts it, which is deliberate.** The record physically stands
    where it stands, is a roof of its block, and has to be subtracted from that block's
    headroom exactly as any other roof is — the same reason `occupied_lots` and
    `exclusive_lots` were split in the first place. Only the entitlement question reads
    this set.

    **And the transparency is one-directional, which is the conservative half.** A lot held
    ONLY by no-lot-claim records has no documented store entitling it under the clause, so
    it reads as taken and the run is not dealt it. That is the cautious answer and it costs
    nothing today: no such lot exists. Making it free would be a second ruling, about
    ground rather than about evidence, and it is not made here.
    """
    out = set()
    for path in sorted(STRUCTURES.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        claim = record.get("lot_claim")
        if claim and claim.get("claims_lot") is False:
            out.add(record["id"])
    return out


def business_fronts() -> dict[str, list[dict]]:
    """{block_id: [frontage entry, …]} — the faces the block programme deals a row.

    A block may appear twice in the recipes (`blk_randolph_dearborn` is dealt its
    Randolph face and its Washington face by two different parcels), so the entries
    are collected rather than replaced.
    """
    parcels = json.loads(PARCELS.read_text(encoding="utf-8"))
    fronts: dict[str, list[dict]] = {}
    for block in parcels["blocks"]:
        frontage = block.get("frontage")
        if frontage:
            fronts.setdefault(block["block_id"], []).append(frontage)
    return fronts


def declared_front(frontage: dict) -> list[int]:
    """The lots of this face the entry declares to be the block's BUSINESS FRONT.

    T-1053. `frontage["lots"]` is the ground the run measurably stands across, and that
    is a smaller thing than the face the owner's 2026-08-27 clause is about: he ruled
    that a platted BUSINESS-FRONT LOT may carry a documented store at the street and an
    anonymous dwelling behind it, and a lot does not stop being on the business front
    because this parcel's row happened to stop one lot short of it. The two questions
    shared one list until T-0449 measured three entries whose run reached less ground
    than they declared, and narrowing those lists to the truth would have withdrawn the
    owner's ruling from three lots as a side effect of a bookkeeping repair.

    So an entry MAY name `business_front` beside `lots`. Where it does not, the run's
    own ground is the front — which is what every entry meant before this field existed,
    so the default keeps the town's occupancy map exactly where it was.
    """
    front = frontage.get("business_front")
    return [int(index) for index in (frontage["lots"] if front is None else front)]


def shared_business_fronts(grid: dict, datum: dict,
                           exclude: set[str] | frozenset[str] = frozenset(),
                           held: dict[str, dict[int, list[str]]] | None = None
                           ) -> dict[str, dict[int, str]]:
    """{block_id: {lot_index: the documented store standing at the street on it}}.

    The owner's 2026-08-27 clause, in code. See the module docstring for the ruling and
    for all three tests; this is only their arithmetic. The street wall is measured on
    the face's own outward normal out of `tools/block_faces.py`, which is the same line
    `tools/generate_plat_lots.py` builds the block edge from and the same one the run
    itself is set back from — so "at the street" is a distance from the committed plat,
    never from a modern kerb.

    A FOURTH condition falls straight out of the third: the store has to be the only
    thing seated on the lot. A lot the anonymous run ALREADY stands on has been used;
    the clause says a documented storefront does not exhaust a business-front lot, not
    that such a lot can never be exhausted. This is why the two halves can call one
    function and still get the answers they each need — the generator asks it with its
    own records excluded, so the store stands alone and the run may be dealt the lot;
    the schedule asks it with nothing excluded, sees the run standing there too, and
    does not offer the block that lot a second time.
    """
    held = lot_holders(grid, datum, exclude) if held is None else held
    fronts = business_fronts()
    documented = researched_ids()
    # A record that declares it claims no lot is not a holder of one for this question.
    # See `no_lot_claim_ids` for the ruling and for what the transparency does not relax.
    transparent = no_lot_claim_ids()
    blocks = {block["id"]: block for block in grid["blocks"]}

    walls: dict[tuple[str, str], float] = {}     # (block_id+face, structure) -> outward
    shared: dict[str, dict[int, str]] = {}
    for block_id, lots in held.items():
        for frontage in fronts.get(block_id, []):
            frame = face_frame(blocks[block_id], frontage["face"])
            reach = float(frontage["setback_m"]) + LOT_MARGIN_M
            dealt = set(declared_front(frontage))
            for index, holders in lots.items():
                claimants = [h for h in holders if h not in transparent]
                if index not in dealt or len(claimants) != 1:
                    continue
                holder = claimants[0]
                if holder not in documented:
                    continue
                key = (f"{block_id}:{frontage['face']}", holder)
                if key not in walls:
                    walls[key] = max(
                        project(frame, point)[1]
                        for sid, world in footprints(datum, exclude) if sid == holder
                        for point in world)
                # outward is INTO the street, so a wall behind the line reads negative
                if walls[key] >= -reach:
                    shared.setdefault(block_id, {})[index] = holder
    return shared


def exclusive_lots(grid: dict, datum: dict,
                   exclude: set[str] | frozenset[str] = frozenset()
                   ) -> dict[str, dict[int, str]]:
    """The occupancies that BAR another roof — `occupied_lots` less the shared fronts.

    THIS is the map a schedule or a generator asks before it deals a lot a roof;
    `occupied_lots` stays the truthful answer to "what stands on this lot", because a
    documented store on a shared business front still stands there, still counts as a
    roof of its block, and still has to be subtracted from that block's headroom.
    Reading one map for both questions is how the two facts were ever confused.
    """
    held = lot_holders(grid, datum, exclude)
    taken = {block_id: {index: ids[0] for index, ids in sorted(lots.items())}
             for block_id, lots in held.items()}
    shared = shared_business_fronts(grid, datum, exclude, held)
    if not shared:
        return taken
    return {block_id: {index: holder for index, holder in lots.items()
                       if index not in shared.get(block_id, {})}
            for block_id, lots in taken.items()}


def block_of_structure(taken: dict[str, dict[int, str]]) -> dict[str, str]:
    """{structure_id: the block whose lots it stands on}, from an occupancy map.

    The ledger attributes a roof to a block by its position POINT, which is the same
    proxy failing the same way: three documented buildings — the Exchange Coffee House,
    Harmon & Loomis's store and the Tremont House — have their position point in the
    roadway and their building on a lot, so they were counted as standing in no block
    at all while occupying one of its eight lots. A roof that stands on a block's lot
    stands in that block.
    """
    home: dict[str, str] = {}
    for block_id, lots in sorted(taken.items()):
        for _, structure_id in sorted(lots.items()):
            home.setdefault(structure_id, block_id)
    return home
