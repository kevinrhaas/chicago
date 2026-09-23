#!/usr/bin/env python3
"""Generate the building material stacked on the lots that were going up — T-0057.

WHAT THIS IS, AND WHY IT IS A SECOND RECORD RATHER THAN A COLUMN ON THE FIRST.
`data/sources/chicago_democrat_1833_11_26.json` carries the village ordinances of
7 November 1833 complete, and **Ordinance 9 is about timber, stone, brick, boxes and
barrels stacked in the streets**. T-0040 drew the boxes and barrels — a merchant's stock
standing on his own frontage, `tools/generate_yard_goods.py` — and refused the other
three nouns in writing, because they are a different claim about a different kind of
ground: *timber, stone and brick are building material on a lot that is going up*, and
`data/yard/town_trade_goods.json` has no way to say which lot was building.

So the whole of this generator is one question, asked of the committed records rather
than of a taste: **which buildings does this dataset SAY were under construction on
1835-07-01?**

THE ANSWER, AND IT IS ONE. Of 343 structures standing on the scene date, 256 are
anonymous infill and 87 are named. Exactly one record states a construction state, and
states it `attested`: `lake_house_construction`, whose `function` is
`hotel_under_construction` off Andreas — 'the hotel was completed and thrown open to the
public in the autumn of 1836' — and whose `roof_type` is `none` for the same reason.
J. D. Bonnell, walking the town on 25 August 1835, saw 'the Lake House IN COURSE OF
CONSTRUCTION'; Harriet Martineau in June 1836 still called it 'a new hotel then
building'. It is the only building site this project can name, and it is a good one.

THE RULE. A lot gets building material iff

  1. it is a NAMED record — the id does not begin `inf_` or `recon_`. The 262 anonymous
     infill records carry a `documented_range.from` that is a PROGRAMME date and not a
     construction date, and `docs/LIBERTIES.md` L126 says so; reading one as a start of
     works would put a builder's yard on two hundred and fifty invented lots, which is
     the exact trap T-0057 was opened to avoid;
  2. its own record STATES the construction state — `attributes.function.value` ends
     `_under_construction`. NOT a date test. A `documented_range.from` inside 1835 is a
     first-attestation date for most of the records that carry one (a newspaper's first
     issue, a directory entry, a deed), and fourteen named records carry one; treating
     that as a groundbreaking would deal stacks of brick to a boarding house that had
     been standing for a year. They are refused here by name and with the reason;
  3. that function is `attested` or `inferred`, never `reconstructed` — the same clause
     the goods keep, for the same reason: invention squared;
  4. it is standing on the scene date (it is in `data/sidecars/1835/index.json`) and it
     is PLACED, with a committed footprint;
  5. nothing stands inside another building's committed footprint. Same clause 6 as the
     goods, and it is checked the same way.

WHICH MATERIALS, and this is dealt from the record and not from the ordinance's list in
order. Ordinance 9 names timber, stone and brick; what stands on a particular lot is what
that building is being built OF, as its own record states it:

  * BRICK because `construction` is `brick`, `attested`, in Andreas's own words — 'this
    hotel, which was built of brick, was three stories and a basement in height'. It is
    the one thing about this structure's fabric that is documented, and Blodgett's
    brickyard had been going on the North Side since the spring of 1833
    (`brickyard_north_side`), so the brick had somewhere to come from.
  * STONE because Andreas gives the building a BASEMENT in the same sentence, and a
    basement is masonry footing before it is anything else. `stories` on the record is a
    part-raised basement plus a first storey, which is precisely the stage of work a heap
    of footing stone belongs to.
  * TIMBER because a three-storey brick building of the period is floored, joisted and
    roofed in it, and is laid from timber scaffolding. Martineau, in the unfinished
    building in June 1836, was seated on 'a few chairs, and benches, and planks laid on
    trestles'.

WHERE, and the strip is a rule too. Material stands in a WORKING STRIP that runs round
the lot clear of the wall, dealt one material to a face beginning at the face the record
fronts and going round it, brick first because brick is the only fabric this record
attests and the front is where a visitor arrives. How many piles a face holds is
arithmetic on that face's run, capped per material. Nothing is placed by hand.

WHAT THIS RECORD DOES NOT CLAIM. It does not say material stood in the STREET, which is
the nuisance the ordinance actually legislated against: the street line at this site is
not resolved to better than the record's own 20 m position uncertainty, and drawing a
stack of brick into a traced roadway would be claiming a precision nobody has. It does
not date the delivery, it does not say how much material was on the ground, and it does
not draw a single brick — no source in this repository gives a brick or a course
dimension (`generators/common/materials.py`, substrate `brick`), so a stack is drawn as
stacked BLOCK and the courses are left out rather than invented at a modern module.

    tools/generate_lot_building_material.py           write the record
    tools/generate_lot_building_material.py --check   re-derive and diff (check.sh)
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SIDECARS = DATA / "sidecars" / "1835"
OUT = DATA / "yard" / "lot_building_material.json"

SCENE = "1835"
TARGET_DATE = "1835-07-01"
SOURCE_ORDINANCE = "chicago_democrat_1833_11_26"

# Clause 2. The suffix a record's `function.value` has to carry.
CONSTRUCTION_SUFFIX = "_under_construction"
# Clause 3.
FUNCTION_GRADES = {"attested", "documented", "inferred"}

# --------------------------------------------------------------------------- #
# THE PILES, and why their sizes live here rather than on the record's `form` —
# they do not. Every number below is written into `form` with its own grade and note,
# exactly as the goods' barrel and crate are, and the renderer reads them from there.
# What is here is the arithmetic that turns them into placements.
# --------------------------------------------------------------------------- #
# A stack of brick: 2.20 x 1.10 m on the ground and 1.05 m high, in two stepped tiers.
BRICK_STACK_M = (2.20, 1.10, 1.05)
BRICK_TIER_INSET_M = 0.18      # how far the upper tier is set back on the lower
BRICK_TIER_SPLIT = 0.62        # the share of the height the lower tier takes

# A squared building stick, 12 ft by 8 in, and how a pile of them is laid.
TIMBER_STICK_M = (3.66, 0.20, 0.20)
TIMBER_PER_COURSE = 5          # sticks side by side in one course
TIMBER_COURSES = (5, 4)        # courses high, dealt by the pile's own index
TIMBER_TOP_SHORT = 2           # the top course is short by this many sticks

# Rough footing stone, and how many blocks a heap is.
STONE_BLOCK_M = (0.70, 0.45, 0.35)
STONE_BLOCKS = 9
STONE_TIERS = 2

# The working strip.
WALL_CLEAR_M = 1.60            # from the wall plane to the near edge of the strip
END_CLEAR_M = 1.00             # never closer than this to the end of a face
BRICK_PITCH_M = 3.20           # centre to centre along a face
TIMBER_PITCH_M = 4.80
STONE_PITCH_M = 2.60
MIN_FACE_M = 4.0               # under this a face has no working strip on it

# One material to a face, in this order, starting at the face the record fronts and
# going round. `cap` is the most piles this record will put on one face, and the three
# caps are in the ratio the building needs the materials in rather than at one number:
# a three-storey brick house wants more brick on the ground than joists, and more joists
# than footing stone. The fourth face is left clear — a lot needs a way in.
MATERIALS = (
    ("brick", 4, BRICK_PITCH_M, BRICK_STACK_M[1]),
    ("timber", 3, TIMBER_PITCH_M, TIMBER_PER_COURSE * TIMBER_STICK_M[1]),
    ("stone", 2, STONE_PITCH_M, STONE_BLOCK_M[0] * 1.6),
)

# The near misses that deserve their own words. They are refused by clause 2 exactly as
# the others are — the rule does not know these ids — but a generic reason would hide
# what is interesting about them, and what is interesting is the whole finding.
SPECIAL_REFUSALS = {
    "north_pier": (
        "IT REALLY WAS UNDER CONSTRUCTION IN THE SCENE WEEK, and it is refused anyway. "
        "Its own phase note says the north pier grew from 700 ft at the end of 1834 to "
        "1,260 ft at the end of 1835 — about 3 ft of pier a day through the season this "
        "scene sits in the middle of — so this is a documented work in progress and not "
        "an attestation date. What it has not got is a LOT: it is federal harbour works "
        "standing in the lake, its material went out over the water on a scow, and "
        "Ordinance 9 is a village nuisance ordinance about the corporation's streets. "
        "Stacking timber and stone on the sand beside it would be a second claim about "
        "a second kind of ground, and this record does not make it."),
    "south_pier": (
        "The same as the north pier, and refused for the same two reasons: a documented "
        "extension through the summer of 1835, and no lot in the corporation to stack "
        "anything on."),
}

WHY_MATERIAL = {
    "brick": ("the record's `construction` is brick and `attested` — Andreas: 'this "
              "hotel, which was built of brick, was three stories and a basement in "
              "height'"),
    "timber": ("a three-storey building of the period is floored, joisted and roofed in "
               "timber and is laid from timber scaffolding; Martineau sat in the "
               "unfinished building on 'planks laid on trestles'"),
    "stone": ("Andreas gives the building a basement in the same sentence that gives it "
              "its brick, and a basement is masonry footing before it is anything else"),
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _round(x: float, places: int = 2) -> float:
    return round(x + 0.0, places)


def _to_enu(u: float, v: float, place: dict) -> tuple[float, float]:
    """A footprint coordinate to local ENU metres — the yard generator's frame.

    docs/GLB-CONTRACT.md: polygon `u` → +X, polygon `v` → −Z, ENU `local_e` → +X and
    `local_n` → −Z, and the node's yaw is `-rotation_deg` about +Y.
    """
    th = math.radians(-(place.get("rotation_deg") or 0.0))
    x, z = u, -v
    xr = x * math.cos(th) + z * math.sin(th)
    zr = -x * math.sin(th) + z * math.cos(th)
    return (place.get("local_e") or 0.0) + xr, (place.get("local_n") or 0.0) - zr


def _footprint_world(sidecar: dict) -> list[tuple[float, float]]:
    poly = (sidecar.get("footprint") or {}).get("polygon") or []
    place = sidecar.get("placement") or {}
    if place.get("local_e") is None or len(poly) < 3:
        return []
    return [_to_enu(u, v, place) for u, v in poly]


def _poly_contains(pt, poly) -> bool:
    x, y = pt
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            xc = xi + (y - yi) * (xj - xi) / ((yj - yi) or 1e-12)
            if x < xc:
                inside = not inside
        j = i
    return inside


def _standing() -> tuple[list[str], dict]:
    index = _load(SIDECARS / "index.json")
    ids = [s["id"] for s in index.get("structures", [])]
    cars = {}
    for sid in ids:
        path = SIDECARS / f"{sid}.json"
        if path.exists():
            cars[sid] = _load(path)
    return ids, cars


def _faces(poly: list, place: dict, bearing: float) -> list[dict]:
    """The four faces of a footprint's own bounding rectangle, front face first.

    The footprint frame's +v is the facade direction — `_front_edge` in the goods
    generator takes the max-`v` edge as the front wall and this agrees with it — so the
    faces run front (max v), right (max u), rear (min v), left (min u), which is
    clockwise seen from above and is the order a material is dealt in.
    """
    umin = min(p[0] for p in poly)
    umax = max(p[0] for p in poly)
    vmin = min(p[1] for p in poly)
    vmax = max(p[1] for p in poly)
    out = []
    specs = (
        # name,     the two ends in (u, v),                    outward bearing offset
        ("front", (umin, vmax), (umax, vmax), 0.0),
        ("right", (umax, vmax), (umax, vmin), 90.0),
        ("rear", (umax, vmin), (umin, vmin), 180.0),
        ("left", (umin, vmin), (umin, vmax), 270.0),
    )
    for name, a_uv, b_uv, off in specs:
        a = _to_enu(a_uv[0], a_uv[1], place)
        b = _to_enu(b_uv[0], b_uv[1], place)
        run = math.hypot(b[0] - a[0], b[1] - a[1])
        out.append({
            "name": name,
            "a": a,
            "b": b,
            "run": run,
            # The outward bearing is the record's own facade bearing turned by the
            # face's quarter — which is what makes the placement follow a rotated
            # footprint instead of the compass.
            "bearing": (bearing + off) % 360.0,
        })
    return out


def build_lots(ids: list[str], cars: dict) -> tuple[list, list, dict]:
    """Every lot that qualifies, every near miss refused by name, and the census."""
    lots: list[dict] = []
    refused: list[dict] = []
    census = {
        "standing": len(ids),
        "anonymous_refused": 0,
        "named_examined": 0,
        "named_with_1835_start_refused": 0,
        "state_not_stated_refused": 0,
        "qualified": 0,
    }
    worlds = {sid: _footprint_world(sc) for sid, sc in cars.items()}

    for sid in sorted(ids):
        sc = cars.get(sid)
        if sc is None:
            continue
        if sid.startswith("inf_") or sid.startswith("recon_"):
            census["anonymous_refused"] += 1                     # clause 1
            continue
        census["named_examined"] += 1
        attrs = sc.get("attributes") or {}
        fn = attrs.get("function") or {}
        value = str(fn.get("value") or "")
        starts_1835 = str((sc.get("documented_range") or {}).get("from") or "") \
            .startswith("1835")
        if not value.endswith(CONSTRUCTION_SUFFIX):              # clause 2
            census["state_not_stated_refused"] += 1
            if starts_1835:
                census["named_with_1835_start_refused"] += 1
                refused.append({
                    "structure_id": sid,
                    "name": sc.get("name"),
                    "function": value or None,
                    "documented_range_from":
                        (sc.get("documented_range") or {}).get("from"),
                    "why": (
                        "its documented range opens inside 1835, which is the nearest "
                        "thing to a start date this dataset carries and is NOT one: it "
                        "is the date the record is first attested — a first issue, a "
                        "directory line, a deed — and the record nowhere says the "
                        "building was going up on the scene date. Clause 2 asks the "
                        "record to SAY it, and this one does not."),
                })
            continue
        grade = fn.get("confidence")
        if grade not in FUNCTION_GRADES:                          # clause 3
            refused.append({
                "structure_id": sid, "name": sc.get("name"), "function": value,
                "why": f"the construction state itself is {grade}."})
            continue
        place = sc.get("placement") or {}
        poly = (sc.get("footprint") or {}).get("polygon") or []
        if len(poly) < 3 or place.get("local_e") is None:         # clause 4
            refused.append({
                "structure_id": sid, "name": sc.get("name"), "function": value,
                "why": "no placed footprint — no lot to stack anything on."})
            continue

        bearing = float(place.get("rotation_deg") or 0.0)
        faces = _faces(poly, place, bearing)
        others = [(oid, w) for oid, w in worlds.items() if oid != sid and len(w) >= 3]
        own = worlds.get(sid) or []

        items: list[dict] = []
        dropped: list[str] = []
        for (kind, cap, pitch, depth), face in zip(MATERIALS, faces):
            if face["run"] < MIN_FACE_M:
                continue
            usable = face["run"] - 2 * END_CLEAR_M
            n = max(0, min(cap, int(usable // pitch) + 1))
            if n <= 0:
                continue
            ax, an = face["a"]
            bx, bn = face["b"]
            L = math.hypot(bx - ax, bn - an) or 1.0
            along = ((bx - ax) / L, (bn - an) / L)
            # Outward is `along` turned LEFT in ENU, which for the front face is the
            # facade normal the goods generator already uses — bearing b gives
            # (sin b, cos b) — and for each later face is that normal turned by the
            # face's own quarter. Turned the other way every pile lands inside the
            # building, which is exactly what the first run of this generator did and
            # what clause 5 caught.
            out_e, out_n = -along[1], along[0]
            off = WALL_CLEAR_M + depth / 2
            # Centred on the face, so a pile is never crowded against one end when the
            # face is longer than the piles need.
            span = pitch * (n - 1)
            start = (face["run"] - span) / 2
            for i in range(n):
                t = start + i * pitch
                e = ax + along[0] * t + out_e * off
                nn = an + along[1] * t + out_n * off
                item = {
                    "kind": kind,
                    "at_local_enu_m": [_round(e), _round(nn)],
                    "bearing_deg": _round(face["bearing"], 1),
                    "face": face["name"],
                    "why_material": WHY_MATERIAL[kind],
                }
                if kind == "timber":
                    item["courses"] = TIMBER_COURSES[i % len(TIMBER_COURSES)]
                if kind == "brick":
                    item["tiers"] = 2
                if kind == "stone":
                    item["blocks"] = STONE_BLOCKS
                hit = next((oid for oid, w in others
                            if _poly_contains((e, nn), w)), None)
                if hit is None and own and _poly_contains((e, nn), own):
                    hit = sid
                if hit:                                            # clause 5
                    dropped.append(hit)
                    continue
                items.append(item)
        if dropped:
            refused.append({
                "structure_id": sid, "name": sc.get("name"), "function": value,
                "why": (f"{len(dropped)} pile(s) fell inside "
                        f"{sorted(set(dropped))[0]}'s committed footprint and are "
                        "dropped rather than nudged, because a nudged coordinate is a "
                        "placed one.")})
        if not items:
            continue
        census["qualified"] += 1
        lots.append({
            "structure_id": sid,
            "name": sc.get("name"),
            "function": value,
            "function_confidence": grade,
            "function_sources": fn.get("sources") or [],
            "construction": ((attrs.get("construction") or {}).get("value")),
            "construction_confidence":
                ((attrs.get("construction") or {}).get("confidence")),
            "why_building": (
                "the record states the construction state itself: its function on the "
                "scene date is a building site, and its roof_type is `none` for the "
                "same reason. It is the only structure in this scene that does."),
            "confidence": "reconstructed",
            "facade_bearing_deg": _round(bearing, 1),
            "wall_clear_m": WALL_CLEAR_M,
            "ground_quad_local_enu_m": [[_round(p[0]), _round(p[1])]
                                        for p in _footprint_world(sc)],
            "items": items,
        })

    lots.sort(key=lambda f: f["structure_id"])
    refused.sort(key=lambda r: r["structure_id"])
    return lots, refused, census


# --------------------------------------------------------------------------- #
# the record                                                                   #
# --------------------------------------------------------------------------- #

def record(lots: list, refused: list, census: dict) -> dict:
    return {
        "_doc": (
            "Building material stacked on the lots that were going up — the timber, "
            "stone and brick half of Ordinance 9, which T-0040 drew the boxes-and-"
            "barrels half of and refused the rest of in writing. The evidence is the "
            "same tier-1 ordinance (data/sources/chicago_democrat_1833_11_26.json) and "
            "it gives a TREATMENT and no location whatever, so 'which lot' is answered "
            "by a rule and tools/check.sh re-derives this file byte for byte. The rule's "
            "load-bearing clause is that the RECORD has to state the construction state "
            "itself: exactly one structure standing on the scene date does, and it "
            "states it attested. A pile of brick is NOT a structure record and NOT baked "
            "geometry — it is a small object standing on ground this project has already "
            "drawn, derived from a committed footprint and drawn by "
            "renderers/web/js/yard.js from these numbers alone, the same argument that "
            "lets data/enclosures/ draw a fence from a perimeter. docs/LIBERTIES.md L173 "
            "claims what is invented."),
        "id": "lot_building_material",
        "name": "Building material on the lots that were going up",
        "kind": "lot_building_material",
        "scene": SCENE,
        "target_date": TARGET_DATE,
        "coordinates": (
            "Local East-North-Up metres from data/datum.json's origin, the same frame "
            "data/enclosures/ and data/signage/ and the sidecars' placement.local_e / "
            "placement.local_n use."),
        "counts": {
            "lots": len(lots),
            "piles": sum(len(f["items"]) for f in lots),
            "piles_by_kind": {
                k: sum(1 for f in lots for it in f["items"] if it["kind"] == k)
                for k in ("brick", "timber", "stone")
            },
            "refused": len(refused),
        },
        "census": census,
        "existence": {
            "value": ("building material stood on the lots that were building in this "
                      "town"),
            "confidence": "reconstructed",
            "sources": [SOURCE_ORDINANCE],
            "note": (
                "THE TREATMENT IS ATTESTED AND THE PILE IS NOT. Ordinance 9 of "
                "7 November 1833 legislates about timber, stone and brick stacked in "
                "the streets of this village, twenty months before the scene date and "
                "by the people who had to walk round them, and a corporation does not "
                "legislate against a thing nobody does. What no source states is that "
                "any material stood on THIS lot on THIS day, in this quantity, in these "
                "positions. So the layer's existence is reconstructed, the whole of it "
                "carries `reconstructed` at the vertex, and a visitor who hides "
                "reconstructed gets a bare building site back — which is the truthful "
                "behaviour and the same one the goods keep."),
        },
        "ordinance": {
            "source_id": SOURCE_ORDINANCE,
            "value": ("timber, stone, brick, boxes and barrels stacked in the streets, "
                      "regulated by the village corporation"),
            "confidence": "attested",
            "note": (
                "Ordinance 9, 7 November 1833, printed complete in the Chicago Democrat "
                "of 26 November 1833. T-0040 drew the boxes and the barrels off this "
                "same clause and left the three building materials, saying in its own "
                "record that they are a different claim. This is that claim, and the "
                "difference is the whole of the rule below: a merchant's stock belongs "
                "to a trade, and building material belongs to a building that is going "
                "up."),
        },
        "form": {
            "brick_stack_m": {
                "value": list(BRICK_STACK_M),
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. A stack 2.20 x 1.10 m on the ground and 1.05 m high — "
                    "about 7 ft 3 by 3 ft 7 and 3 ft 5 — which is a barrow's round trip "
                    "wide and as high as brick is comfortably stacked by hand. Nothing "
                    "states how much brick stood on this lot or how it was piled. NO "
                    "INDIVIDUAL BRICK IS DRAWN and no course is drawn either: "
                    "generators/common/materials.py records that no source in this "
                    "repository gives a brick or a course dimension, so the rate is "
                    "unresolvable, and a course rhythm here would be a modern brick "
                    "module wearing an 1835 date. The stack is drawn as stacked block in "
                    "two stepped tiers, which reads as stacked brick without claiming a "
                    "dimension."),
            },
            "brick_tier_m": {
                "value": [BRICK_TIER_INSET_M, BRICK_TIER_SPLIT],
                "confidence": "reconstructed",
                "note": (
                    "INVENTED — the step, and it is drawing rather than claim. The upper "
                    "tier is set back 0.18 m on the lower and takes the top 38 per cent "
                    "of the height. A single box reads as a crate; the step is what makes "
                    "it read as material stacked by somebody."),
            },
            "timber_stick_m": {
                "value": list(TIMBER_STICK_M),
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. A squared building stick 3.66 m by 0.20 m square — 12 ft "
                    "by 8 in, recorded converted. Nothing attests a scantling, a length "
                    "or a saw in Chicago on this date. What bounds it is what the timber "
                    "is FOR: a floor joist and a scaffold standard in a building 15 m "
                    "deep, and 12 ft is the shortest stick that spans a room of it."),
            },
            "timber_pile": {
                "value": [TIMBER_PER_COURSE, list(TIMBER_COURSES), TIMBER_TOP_SHORT],
                "confidence": "reconstructed",
                "note": (
                    "INVENTED, and it is how a pile is drawn rather than a claim about "
                    "any pile. Five sticks side by side to a course, four or five courses "
                    "high by the pile's own index, and the top course short by two — "
                    "which is what a pile being worked off looks like and what stops two "
                    "piles on one lot being the same object twice. All courses lie the "
                    "same way: a stickered pile crosses its courses, and a crossing "
                    "course at this pile's width would be a stick 1.0 m long, which is "
                    "not the stick this record carries."),
            },
            "stone_block_m": {
                "value": list(STONE_BLOCK_M),
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. A rough block 0.70 x 0.45 x 0.35 m — a two-man lift, which "
                    "is what footing stone handled without a crane has to be. Nothing "
                    "states a stone, a quarry or a course for this basement. The heap is "
                    "nine of them in two tiers at their own angles, because rubble "
                    "delivered to a site is tipped and not laid, and the angles are the "
                    "renderer's the way a barrel's stave count is."),
            },
            "stone_heap": {
                "value": [STONE_BLOCKS, STONE_TIERS],
                "confidence": "reconstructed",
                "note": (
                    "INVENTED — nine blocks in two tiers. Drawing rather than claim, kept "
                    "on the record with the block's size so the renderer reaches for no "
                    "number of its own, the same division the goods' bench_plank_m "
                    "makes."),
            },
            "working_strip_m": {
                "value": [WALL_CLEAR_M, END_CLEAR_M],
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. The strip material stands in begins 1.60 m off the wall "
                    "plane and stops 1.00 m short of each end of a face. Nothing states "
                    "either. What bounds the first is the work: a bricklayer needs a "
                    "gangway between his stack and his wall, and 1.60 m is a barrow and "
                    "a man. What bounds the second is that a pile lapping the corner of "
                    "the building would stand in the next face's strip."),
            },
            "colours": {
                "value": None,
                "confidence": "reconstructed",
                "geometry": "renderer",
                "note": (
                    "THE BRICK IS NOT A NEW COLOUR AND THE STONE IS. Brick is this "
                    "town's ONE brick — generators/common/materials.py's BRICK, "
                    "inferred, off the Petford watercolour's brick chimneys, and the "
                    "same brick every framed house in the scene carries on its stack; "
                    "the material on this lot being that brick is the cheapest honest "
                    "answer, because it is the fabric the record already attests. Stone "
                    "has no row on the material sheet at all (substrate `stone` carries "
                    "no colour), so its tone is reconstructed and BOUNDED by two values "
                    "this project already ships: it is paler and greyer than the yard "
                    "layer's own timber, or the heap stops reading as stone beside the "
                    "sticks next to it, and it is darker than the chinking clay, which "
                    "is the same mineral sitting sheltered under an eave. Timber is the "
                    "yard layer's own timber tone unchanged — a sawn building stick and "
                    "a packing case are the same new wood, and inventing a second one "
                    "would be a claim about a saw."),
            },
        },
        "rule": {
            "note": (
                "A NAMED record (not inf_/recon_), whose own `attributes.function.value` "
                "ENDS `_under_construction` and is attested or inferred, standing on the "
                "scene date, placed with a committed footprint, and every pile clear of "
                "every committed footprint including its own. Which materials is dealt "
                "from what the record says the building is built OF, not from the "
                "ordinance's list in order. Where is arithmetic on the lot's own faces — "
                "one material to a face beginning at the face the record fronts and "
                "going round it, as many piles as the face's run holds at the material's "
                "pitch, capped. Read the clauses and their reasons in "
                "tools/generate_lot_building_material.py."),
            "construction_suffix": CONSTRUCTION_SUFFIX,
            "face_order": [m[0] for m in MATERIALS],
            "caps": {m[0]: m[1] for m in MATERIALS},
            "date_test_refused_note": (
                "THE CLAUSE THIS RULE DOES NOT HAVE IS A DATE TEST, and refusing to "
                "write one is the finding. `documented_range.from` inside 1835 is the "
                "nearest thing to a start date this dataset carries and it is not one: "
                "for the named records it is a FIRST ATTESTATION — a newspaper's first "
                "issue on 8 June 1835, a directory line, a deed — and for the 256 "
                "anonymous infill records it is a PROGRAMME date, which "
                "docs/LIBERTIES.md L126 states in as many words. Fourteen named records "
                "carry an 1835 opening and every one of them is refused by name in "
                "`refused` below with that reason. A date test would have dealt stacks "
                "of brick to a boarding house that had been standing a year, and to two "
                "hundred and fifty invented lots."),
            "street_refused_note": (
                "AND IT DOES NOT PUT ANYTHING IN THE STREET, which is what the ordinance "
                "actually legislated against. The one qualifying lot's own position note "
                "carries a working uncertainty of about 20 m and says which side of Rush "
                "Street it stands on is not documented at all; the traced centreline of "
                "Michigan Street in data/streets/1835.json runs some 30 m north of where "
                "this record's own georeference puts the frontage. Two numbers that "
                "disagree by more than the object is wide cannot place a stack of brick "
                "in a roadway, so the material stands on the LOT — which is where the "
                "ticket asked for it — and the street half of Ordinance 9 stays "
                "undrawn and said so."),
        },
        "lots": lots,
        "refused": refused,
        "research_note": (
            "WHAT WOULD MOVE ANY OF THIS. A second building site: any record that states "
            "a construction state on 1835-07-01 gets material by the same rule the day "
            "it is written, and the queue's own block programme is the likeliest source "
            "of one. A groundbreaking date for the Lake House: the 1835 groundbreaking "
            "is carried only by two unfootnoted compilations, and the record says so at "
            "length — a dated newspaper notice, a subscription list or a builder's "
            "account would move the whole structure off inferred. A brick dimension: "
            "any Chicago brick of the 1830s measured or stated would let a stack be "
            "drawn in courses instead of as block. A quarry: nothing reached says where "
            "footing stone for a north-side cellar came from, and the answer would give "
            "the heap a colour it currently has to bound."),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and diff, write nothing")
    args = ap.parse_args()
    ids, cars = _standing()
    lots, refused, census = build_lots(ids, cars)
    text = json.dumps(record(lots, refused, census), indent=2,
                      ensure_ascii=False) + "\n"
    piles = sum(len(f["items"]) for f in lots)
    if args.check:
        if not OUT.exists():
            print(f"LOT BUILDING MATERIAL DRIFT\n  - {OUT.relative_to(ROOT)} is missing")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"LOT BUILDING MATERIAL DRIFT\n  - {OUT.relative_to(ROOT)} has drifted "
                  "from the rule in tools/generate_lot_building_material.py")
            return 1
        print(f"verified {piles} pile(s) on {len(lots)} lot(s) that were building "
              f"({len(refused)} record(s) refused with a reason)")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {piles} pile(s) on {len(lots)} lot(s) "
          f"({len(refused)} refused)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
