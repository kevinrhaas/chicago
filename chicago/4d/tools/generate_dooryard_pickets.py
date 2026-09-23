#!/usr/bin/env python3
"""Generate the town's dooryard garden pickets — the enclosure layer's third record.

WHAT THIS IS. `docs/ROADMAP.md` K5 (a) cites the Kinzie-view plate for *"picket-fenced
garden plots and Lombardy poplars"* and says in the same breath what the citation is
worth: it is a reference for TREATMENT, and the house itself stays excluded from the
1835 scene. So this project has a picture of what a garden fence in this town looked
like and not one word about where any of them stood. That asymmetry is the whole
difficulty of ticket T-0052, and it is why the answer is a RULE rather than a list:
the record has to be able to say, of every fence it draws, on what basis that
particular lot got one.

THE RULE, and every clause of it is doing work. A lot gets a dooryard picket iff

  1. it is a platted lot in `data/traces/vectors/thompson_lots.json` — so the ground
     the fence stands on is the committed plat grid and not a shape invented here;
  2. exactly ONE committed building centre stands in it — a lot shared with a shop, a
     stable or a second dwelling has no undivided dooryard this record could bound,
     and guessing where the division ran would be an invention on top of an invention;
  3. that building is a dwelling by BOTH archetype (`frame_dwelling` / `log_dwelling`)
     and function (`dwelling`, or a cottage/house band of the reconstruction
     schedule) — the Mansion House, Eliza Chappel's infant school and the Temple
     Building all sit alone on a platted lot and none of them is a house lot;
  4. a household is recorded as living there. A garden is a HOUSEHOLD'S. John Wright's
     two buildings to let are excluded by this clause and by their own records, which
     say in as many words that "the honest reading of 'to let' is a building whose
     tenant this project cannot name";
  5. the plot the first four clauses leave — the rear of the lot, clear of the house
     and inside the lot lines — is big enough to be a garden and hits no other
     building's committed footprint.

Every metre of every perimeter below is then DERIVED from the committed lot polygon
and the committed footprint. Nothing here is hand-placed, which is what makes every
garden fence auditable rather than a number someone typed; `--check` re-derives the
record byte for byte in `tools/check.sh`.

HOW MANY IS AN OUTPUT, NOT A SETTING. No count is written down here, because the rule
above decides it afresh on every run and the committed record is the only place it is
true. It has been eighteen (2026-08-18), fifteen, thirteen and — since T-0516 withdrew
the stale `occupants` prose clause 4 reads — ONE. Whether clause 4 is the right test at
all is the owner's open question, T-0772: a garden could follow the HOUSE rather than
the HOUSEHOLD. Do not restate a count in this docstring or in `docs/LIBERTIES.md` L129;
both went stale by seventeen once already.

WHAT IS INVENTED is the treatment and the plot geometry — the fence type, its height,
its pale rhythm, the size of the plot, its position at the back of the lot and the gate
in its house-facing side. All of it is graded `reconstructed` and claimed in
`docs/LIBERTIES.md` L129. No source states that any of these particular households kept
a garden, and this record never says one did: it says the town's house lots are drawn
with the plate's treatment, and names the rule that chose them.

    python3 tools/generate_dooryard_pickets.py            write the record
    python3 tools/generate_dooryard_pickets.py --check    re-derive and diff
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import enclosure_owners

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
LOTS_PATH = DATA / "traces" / "vectors" / "thompson_lots.json"
SIDECARS = DATA / "sidecars" / "1835"
STRUCTURES = DATA / "structures"
OUT = DATA / "enclosures" / "town_dooryard_pickets.json"

DWELLING_ARCHETYPES = {"frame_dwelling", "log_dwelling"}

# The reconstruction schedule's house bands, plus the plain word. Anything else that
# happens to be built as a dwelling — a tavern, a school, a meeting house — is not a
# house lot, and the three that sit alone on a platted lot are named in the docstring.
def is_dwelling_function(value: str) -> bool:
    v = (value or "").strip().lower()
    if v in {"dwelling", "residence"}:
        return True
    return any(word in v for word in ("dwelling", "cottage", "house", "shanty",
                                      "cabin")) and \
        not any(word in v for word in ("boarding", "school", "meeting", "warehouse",
                                       "tavern", "hotel", "store", "shop", "wash",
                                       "court", "guard", "packing", "slaughter"))

# THE PLOT, in feet and recorded converted, per data/datum.json's units rule.
LOT_MARGIN_M = 0.914      # 3 ft off the lot line — the fence is inside the lot
REAR_CLEAR_M = 3.048      # 10 ft of open dooryard between the back wall and the plot
MAX_DEPTH_M = 6.096       # 20 ft
MAX_WIDTH_M = 8.534       # 28 ft
MIN_DEPTH_M = 4.572       # 15 ft — under this it is a bed, not a garden; skip the lot
MIN_WIDTH_M = 6.096       # 20 ft
GATE_WIDTH_M = 1.067      # 3 ft 6 in, in the side that faces the house


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def poly_contains(pt, poly) -> bool:
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def footprint_world(sidecar) -> list[tuple[float, float]]:
    """The building's footprint in local ENU metres, placed and rotated."""
    fp = (sidecar.get("footprint") or {}).get("polygon") or []
    pl = sidecar.get("placement") or {}
    e0, n0 = pl.get("local_e"), pl.get("local_n")
    th = math.radians(pl.get("rotation_deg") or 0.0)
    c, s = math.cos(th), math.sin(th)
    return [(e0 + x * c - y * s, n0 + x * s + y * c) for x, y in fp]


def convex_overlap(a, b) -> bool:
    """Separating-axis test for two convex polygons; touching does not count."""
    for poly in (a, b):
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            ax, ay = -(y2 - y1), x2 - x1
            la = math.hypot(ax, ay) or 1.0
            ax, ay = ax / la, ay / la
            pa = [ax * px + ay * py for px, py in a]
            pb = [ax * px + ay * py for px, py in b]
            if max(pa) <= min(pb) + 1e-9 or max(pb) <= min(pa) + 1e-9:
                return False
    return True


def lot_frame(block, lot):
    """(frontage midpoint, along-width unit, along-depth unit, width, depth).

    A lot is a quadrilateral with two END edges (the street frontage and the rear
    line) and two SIDE edges. The ends are the pair whose length matches the block's
    stated frontage module; the street one is the end farther from the block's own
    centroid, because a lot's rear is the inside of its block.
    """
    poly = lot["polygon"]
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    bx = sum(p[0] for p in block["boundary_local_enu_m"]) / len(block["boundary_local_enu_m"])
    by = sum(p[1] for p in block["boundary_local_enu_m"]) / len(block["boundary_local_enu_m"])
    edges = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        edges.append((math.hypot(q[0] - p[0], q[1] - p[1]), p, q))
    # the two shortest edges are the ends: a lot is 80 ft on the street and deeper than
    # it is wide everywhere in this grid.
    ends = sorted(edges, key=lambda e: e[0])[:2]
    def mid(e):
        return ((e[1][0] + e[2][0]) / 2, (e[1][1] + e[2][1]) / 2)
    front, rear = sorted(ends, key=lambda e: -math.hypot(mid(e)[0] - bx, mid(e)[1] - by))
    fm, rm = mid(front), mid(rear)
    ux, uy = front[2][0] - front[1][0], front[2][1] - front[1][1]
    lu = math.hypot(ux, uy) or 1.0
    ux, uy = ux / lu, uy / lu
    vx, vy = rm[0] - fm[0], rm[1] - fm[1]
    lv = math.hypot(vx, vy) or 1.0
    vx, vy = vx / lv, vy / lv
    return fm, (ux, uy), (vx, vy), lu, lv


def candidates(require_household=True):
    """Every platted lot that passes clauses 1–4, with its house."""
    lots = load(LOTS_PATH)
    sidecars = {}
    for path in sorted(SIDECARS.glob("*.json")):
        sc = load(path)
        pl = sc.get("placement") or {}
        if pl.get("local_e") is None:
            continue
        sidecars[path.stem] = sc
    occupancy: dict[tuple[str, int], list[str]] = {}
    for sid, sc in sidecars.items():
        pl = sc["placement"]
        for block in lots["blocks"]:
            for i, lot in enumerate(block["lots"]):
                if poly_contains((pl["local_e"], pl["local_n"]), lot["polygon"]):
                    occupancy.setdefault((block["id"], i), []).append(sid)
    out = []
    for block in lots["blocks"]:
        for i, lot in enumerate(block["lots"]):
            here = occupancy.get((block["id"], i), [])
            if len(here) != 1:
                continue
            sid = here[0]
            sc = sidecars[sid]
            if sc.get("archetype") not in DWELLING_ARCHETYPES:
                continue
            st = load(STRUCTURES / f"{sid}.json")
            fn = st.get("function")
            fn = fn.get("value") if isinstance(fn, dict) else fn
            if not is_dwelling_function(fn):
                continue
            if require_household:
                occ = st.get("occupants")
                if not occ or "hh_" not in json.dumps(occ):
                    continue
            out.append((block, i, lot, sid, sc, fn))
    return out, sidecars


def plot_for(block, index, lot, sid, sc, all_sidecars):
    """The garden rectangle, derived; or (None, why) when the lot cannot carry one."""
    fm, (ux, uy), (vx, vy), width, depth = lot_frame(block, lot)

    def to_lot(p):
        dx, dy = p[0] - fm[0], p[1] - fm[1]
        return (dx * ux + dy * uy, dx * vx + dy * vy)

    house = [to_lot(p) for p in footprint_world(sc)]
    hv_max = max(p[1] for p in house)
    hu_mid = (min(p[0] for p in house) + max(p[0] for p in house)) / 2

    # A DOORYARD garden is the yard by the door, so the plot starts where the dooryard
    # ends and runs back from there — it is not pushed to the far end of a deep lot.
    v_start = max(hv_max + REAR_CLEAR_M, LOT_MARGIN_M)
    v_end = min(v_start + MAX_DEPTH_M, depth - LOT_MARGIN_M)
    if v_end - v_start < MIN_DEPTH_M:
        over = hv_max - (depth - LOT_MARGIN_M)
        why = (f"the committed house stands at the rear of its lot — its back face is "
               f"{over:.2f} m past the lot's own rear line — " if over > 0 else
               f"only {max(v_end - v_start, 0):.2f} m of lot is left behind the house — ")
        return None, (why + f"so nothing {MIN_DEPTH_M:.2f} m deep fits behind it")
    d = v_end - v_start

    w = min(MAX_WIDTH_M, width - 2 * LOT_MARGIN_M)
    if w < MIN_WIDTH_M:
        return None, f"the lot is only {width:.2f} m wide between its side lines"
    # `u` is measured from the MIDDLE of the frontage, because that is where the lot
    # frame's origin sits, so the side lot lines are at plus and minus half the width.
    edge = width / 2 - LOT_MARGIN_M
    u_lo = min(max(hu_mid - w / 2, -edge), edge - w)
    u_hi = u_lo + w

    def to_world(u, v):
        return (round(fm[0] + ux * u + vx * v, 2), round(fm[1] + uy * u + vy * v, 2))

    corners = [to_world(u_lo, v_start), to_world(u_hi, v_start),
               to_world(u_hi, v_end), to_world(u_lo, v_end)]
    for other_id, other in all_sidecars.items():
        if other_id == sid:
            continue
        fp = footprint_world(other)
        if len(fp) >= 3 and convex_overlap(corners, fp):
            return None, (f"the derived plot overlaps {other_id}'s committed footprint, "
                          f"which stands over the lot line")
    gate = to_world((u_lo + u_hi) / 2, v_start)
    return {"corners": corners, "gate": gate, "width_m": round(w, 2),
            "depth_m": round(d, 2)}, None


def build_record():
    cands, sidecars = candidates()
    runs, openings, refused = [], [], []
    links = enclosure_owners.household_links()
    for block, index, lot, sid, sc, fn in cands:
        plot, why = plot_for(block, index, lot, sid, sc, sidecars)
        if plot is None:
            refused.append(f"{block['id']} lot {index} ({sid}): {why}")
            continue
        ring = plot["corners"] + [plot["corners"][0]]
        lot_id = f"{block['id']}_lot{index}"
        runs.append({
            "id": lot_id,
            "path_local_enu_m": ring,
            # WHOSE GARDEN THIS IS (T-0637), by the same derivation the lot-line fences
            # use — and it lands on ONE of these thirteen plots, which is a finding and not
            # a bug in the join. Clause 4 above admits a lot on the strength of the
            # structure record's `occupants` PROSE naming a household; the committed
            # household index carries a real `lives_at` for twenty households in the whole
            # town, and only Elijah Harmon's is on a lot this record reaches. The gap is
            # the address work's (T-0514) and the stale-prose problem is T-0516's;
            # tools/enclosure_owners.py counts both rather than papering over them.
            "belongs_to": enclosure_owners.owners_for(
                [(lot_id, lot["polygon"], [sid])], ring, links),
            "note": (
                f"THE HOUSE LOT: {block['id']} lot {index} of the platted grid, holding "
                f"{sid} ({fn}) and nothing else. IT PASSES THE RULE THIS RECORD IS BUILT "
                f"ON — one building on the lot, a dwelling by archetype and by function, "
                f"and a household recorded as living in it — and the rule is the answer to "
                f"'why this lot': no source puts a garden here or anywhere else in the "
                f"town. THE RECTANGLE IS DERIVED AND NOT PLACED: "
                f"{plot['width_m']:.2f} x {plot['depth_m']:.2f} m at the back of the lot, "
                f"{LOT_MARGIN_M:.3f} m inside the rear and side lot lines, "
                f"{REAR_CLEAR_M:.3f} m or more clear of the house's own back face, and "
                f"centred on the house. Every metre of it comes from "
                f"data/traces/vectors/thompson_lots.json and this building's committed "
                f"footprint; the SIZE of the plot and its position at the rear are the "
                f"invention, and they are the same for every lot on this record. THE "
                f"CEILING ON THE PLOT — 28 x 20 ft — is invented twice over: nothing "
                f"states a garden's size, and the number is additionally bounded by the "
                f"renderer's own triangle budget, because a paled fence is thousands of "
                f"small boxes and this layer draws in one pass. docs/LIBERTIES.md L129 "
                f"claims that, on the precedent of L121."
            ),
        })
        openings.append({
            "id": f"{block['id']}_lot{index}_gate",
            "on": "dooryard",
            "at_local_enu_m": list(plot["gate"]),
            "width_m": GATE_WIDTH_M,
            "confidence": "reconstructed",
            "note": (
                "INVENTED, like every gateway on this layer. A garden that is worked "
                "daily from the house has a way in from the house, so the gap is centred "
                "in the side that faces the back door; 3 ft 6 in is a person with a hoe "
                "or a basket, not a team. NO GATE LEAF IS DRAWN — the fence simply stops, "
                "the way it does at the wagon yard and the pound, because a hung gate "
                "would be an invention on top of an invention."
            ),
        })
    return runs, openings, refused


def record(runs, openings, refused):
    owners = enclosure_owners.tally([{"runs": runs}])
    prose = enclosure_owners.prose_report(
        sid for run in runs for entry in run["belongs_to"] for sid in entry["structures"])
    return {
        "id": "town_dooryard_pickets",
        "name": "The town's dooryard garden pickets",
        "aka": ["the garden plots", "the kitchen gardens"],
        "kind": "garden",
        "scene": "1835",
        "target_date": "1835-07-01",
        "generated_by": "tools/generate_dooryard_pickets.py",
        "generated_from": [
            "data/traces/vectors/thompson_lots.json",
            "data/sidecars/1835/*.json",
            "data/structures/*.json",
        ],
        "belongs_to": [],
        "belongs_to_rule": enclosure_owners.rule_block(owners, prose),
        "documented_range": {
            "from": "1835-01-01",
            "to": "1835-12-31",
            "confidence": "reconstructed",
            "sources": [],
            "note": (
                "THE RANGE IS THE SCENE YEAR AND NOTHING MORE. No source dates a garden "
                "fence in this town, because no source mentions one. The range is a "
                "housekeeping bound so that this record answers the same date gate every "
                "other record answers, and it should not be read as evidence that these "
                "fences went up in 1835 or came down in 1836."
            ),
        },
        "existence": {
            "value": True,
            "confidence": "reconstructed",
            "sources": ["kurz_allison_1893"],
            "note": (
                "NOTHING ATTESTS A GARDEN FENCE ON ANY LOT IN THIS TOWN, and this record "
                "does not claim one. What is attested is a TREATMENT, on the far bank and "
                "on a plate drawn decades later: the Kinzie-view lithograph shows the long "
                "low house with its piazza, a row of Lombardy poplars and PICKET-FENCED "
                "GARDEN PLOTS. A tier-5 retrospective view may drive massing, materials "
                "and setting and may never drive a coordinate, which is precisely how it "
                "is used here: the plate says what a garden fence in this place looked "
                "like, and the RULE in tools/generate_dooryard_pickets.py says which lots "
                "get one. The claim this record makes is 'the town's house lots are drawn "
                "with the plate's treatment', not 'these households kept gardens'. "
                "THE SOURCE IS NAMED SINCE 2026-09-13 (T-0055), AND THE PLATE TURNED OUT "
                "TO BE ONE THIS PROJECT ALREADY HELD. This block used to read 'SOURCES IS "
                "DELIBERATELY EMPTY AND THAT IS THE FINDING: this project holds NO source "
                "record for the Kinzie-view plate', because the plate reached the "
                "repository as an owner-supplied crop with a README and nothing else "
                "(data/sources/assets/prefire_views_kevin_2026_08/p6_1.png, plate '12'). "
                "It is PANEL 12 of `kurz_allison_1893` — Kurz & Allison, 'Chicago In Early "
                "Days, 1779-1857' (1893), a chromolithograph of fifteen numbered vignettes "
                "the project has held as a source record since before this layer existed. "
                "The match is measured, not recognised: the crop and the sheet's "
                "lower-left vignette both carry the printed numeral '12.'; the sheet's own "
                "key reads 'No. 12.  The Old Kinzie Mansion, built 1832.  Population "
                "310.'; and a normalised cross-correlation of the crop against the "
                "committed sheet peaks at 0.797 on that vignette against 0.341 anywhere in "
                "the control panel. So the old finding was right that nothing was cited "
                "and wrong that nothing existed — the record was here and no line joined "
                "it. WHAT THAT DOES NOT DO is strengthen this fence. The plate is still "
                "tier 5, still published fifty-eight years after the scene date, still of "
                "a house on the north bank that this scene excludes, and it still bounds a "
                "treatment and attests nothing about these lots; the confidence above "
                "stays 'reconstructed' for exactly the reasons it always did. What it "
                "changes is that a reader can now reach the Library of Congress sheet "
                "instead of a 391-pixel crop, and that the plate's rights are settled on "
                "the object — its own foot carries 'Copyrighted 1893 by Kurz & Allison', "
                "long expired, so the image this layer leans on is public domain."
            ),
        },
        "runs": runs,
        "openings": openings,
        "form": {
            "fence_type": {
                "value": "picket",
                "confidence": "reconstructed",
                "note": (
                    "INVENTED, and it is the one value on this record with a picture "
                    "behind it. The Kinzie-view plate — panel 12 of `kurz_allison_1893`, "
                    "identified in the existence note — shows PICKETS: close-set vertical "
                    "pales, not the open horizontal rails this layer draws at the wagon "
                    "yard and the pound, and that difference is the whole point of the "
                    "distinction: a rail fence turns a team and a picket fence keeps "
                    "poultry out of the vegetables. The plate is tier 5 and it is of a "
                    "house on the north bank that this scene excludes, so it bounds a "
                    "treatment and attests nothing about these lots."
                ),
            },
            "height_m": {
                "value": 1.22,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. 1.22 m is 4 ft, recorded converted. Nothing attests a "
                    "height. The bound is the use, read against the two fences already in "
                    "this dataset: a garden pale turns poultry and a rooting hog off a bed "
                    "of vegetables, which needs less than the Western Hotel's 4 ft 6 in "
                    "yard fence (that one turns a hitched team) and far less than the "
                    "pound's 6 ft (that one holds a beast that means to leave). Four feet "
                    "is the least that does the garden's job. A Chicago or Cook County "
                    "lawful-fence ordinance of the 1830s would replace this number "
                    "outright, and this project holds none."
                ),
            },
            "rail_courses": {
                "value": 2,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. Two stringers is what a pale fence of this height is built "
                    "on — the pales carry the closure and the rails only hold them in "
                    "line, which is the opposite of the rail fences on this layer, where "
                    "the courses ARE the fence. Nothing attests a count."
                ),
            },
            "post_spacing_m": {
                "value": 2.44,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. 2.44 m is 8 ft, the same bay as the pound, because it is "
                    "the same reason — the span a sawn rail of the period is cut to carry. "
                    "Nothing attests a bay."
                ),
            },
            "post_size_m": {
                "value": 0.10,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. A 0.10 m post is a 4-inch stick, the lightest on this layer "
                    "and lighter than the yard fence's 0.14 m: a garden fence is not leaned "
                    "on by anything heavier than a gardener. Nothing attests it."
                ),
            },
            "picket_width_m": {
                "value": 0.089,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. 0.089 m is 3.5 in — a riven or sawn pale off the same pile "
                    "of stuff the town's frame houses are boarded from. Nothing attests a "
                    "pale, its width, or that these fences were made of sawn timber at all."
                ),
            },
            "picket_gap_m": {
                "value": 0.089,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. A pale-wide gap is the rhythm the Kinzie-view plate reads "
                    "as at the scale it is drawn, and it is the number that decides whether "
                    "this fence looks like a wall or like a fence. Nothing attests it. It is "
                    "recorded here rather than left to the renderer for the same reason the "
                    "post rhythm is: the number a visitor is looking at should be one this "
                    "file states."
                ),
            },
        },
        "ground": {
            "value": "cultivated garden ground",
            "confidence": "reconstructed",
            "geometry": "drawn",
            "treatment": "dooryard_garden",
            "note": (
                "DRAWN SINCE 2026-08-21 (T-0067). This block used to read 'NOT DRAWN, AND "
                "SAYING SO IS THE POINT' — the ground inside these fences was the prairie "
                "sward the flora layer plants everywhere else in the town, which made a "
                "garden fence a rectangle of pales around nothing. The owner named exactly "
                "that on 2026-08-18: 'fences around properties inside the fence would not be "
                "wild prairie but curated lawn and garden or animal pens'. So the sward is "
                "suppressed inside every plot on this record and renderers/web/js/yards.js "
                "lays `dooryard_garden` in its place: short kept green over the plot, a bank "
                "of tilled beds in rows on the side away from the gateway, and a trodden "
                "path in from the gateway itself. NO NEW COORDINATE IS AUTHORED FOR ANY OF "
                "IT — every run on this record already closes a ring, and the ground is that "
                "ring; the beds and the path are derived inside it from the plot's own axes "
                "and this record's own gateway, and both are clipped to the ring so neither "
                "can escape its fence. WHAT IS STILL TRUE IS THE OLD ADMISSION'S REASON: a "
                "kitchen garden is beds and bare earth and a crop that changes with the "
                "month, and nothing states what was grown on any lot in this town. The "
                "treatment is therefore graded reconstructed like the fence over it, it "
                "disappears with the rest of that tier, and docs/LIBERTIES.md L158 claims "
                "the scheme on the precedent of L129."
            ),
        },
        "refused": refused,
        "research_note": (
            "THE EVIDENCE HERE IS A TREATMENT AND NOT A LOCATION, which is why this record "
            "is generated from a rule instead of authored lot by lot. Read the rule in "
            "tools/generate_dooryard_pickets.py — it is the answer to 'why this lot' and it "
            "is enforced on every commit, because tools/check.sh re-derives this file byte "
            "for byte. In short: one building on a platted lot, a dwelling by archetype and "
            "by function, a household living in it, and room at the back for a plot that "
            "hits nothing. WHAT THE CLAUSES COST is visible in the count — the platted grid "
            "holds 144 lots and this record fences a fraction of them, because most lots "
            "hold more than one building or none, and the town's house lots outside the "
            "19 platted blocks (the West Division approaches, the reservation, the North "
            "Division) have no lot geometry to derive a plot from at all. WHAT WOULD CHANGE "
            "IT: a Chicago or Cook County fence ordinance of the 1830s, which would settle "
            "the height and probably the pale rhythm; any tax, insurance or sale description "
            "of a town lot naming a garden or a fence; and the North Division street control "
            "docs/ROADMAP.md S9 still records as owed, which is what keeps two thirds of the "
            "plat off this grid."
        ),
    }


def compare_rules() -> int:
    """Both readings of clause 4, counted — the measurement T-0772 is blocked on.

    Writes nothing. The HOUSEHOLD rule is the one in force: a garden is a household's,
    and the lot is admitted on the structure record's `occupants` prose naming an `hh_`
    id. The HOUSE rule is the alternative: one dwelling alone on a platted lot has a
    kitchen garden behind it by archetype and by function, whoever lived in it. Clause 5
    — room at the back for a plot that hits nothing — is applied to both, so the two
    numbers below are gardens actually drawable and not pools.
    """
    house_pool, sidecars = candidates(require_household=False)
    hh_pool, _ = candidates(require_household=True)

    def drawable(pool):
        ok, refused = [], []
        for block, index, lot, sid, sc, fn in pool:
            plot, why = plot_for(block, index, lot, sid, sc, sidecars)
            (refused if plot is None else ok).append((f"{block['id']}_lot{index}", sid, why))
        return ok, refused

    house_ok, house_no = drawable(house_pool)
    hh_ok, hh_no = drawable(hh_pool)
    hh_ids = {r[0] for r in hh_ok}
    print("CLAUSE 4, BOTH WAYS — T-0772's question, counted against the tree in front of it")
    print(f"  the HOUSEHOLD rule (in force): {len(hh_pool)} lot(s) admitted, "
          f"{len(hh_ok)} garden(s) drawn, {len(hh_no)} refused for want of room")
    print(f"  the HOUSE rule (the alternative): {len(house_pool)} lot(s) admitted, "
          f"{len(house_ok)} garden(s) drawn, {len(house_no)} refused for want of room")
    added = [(lot_id, sid) for lot_id, sid, _ in house_ok if lot_id not in hh_ids]
    print(f"  gardens the house rule would ADD: {len(added)}")
    # HOW WELL FOUNDED IS THE HOUSE UNDER EACH ADDED GARDEN, in the project's own grading
    # of what the building IS. A garden behind a reconstructed cottage is an invention
    # resting on an invention, which is the cost the owner is being asked to weigh.
    by_grade: dict[str, int] = {}
    for lot_id, sid in added:
        st = load(STRUCTURES / f"{sid}.json")
        fn = st.get("function")
        grade = fn.get("confidence", "ungraded") if isinstance(fn, dict) else "ungraded"
        by_grade[grade] = by_grade.get(grade, 0) + 1
        print(f"    + {lot_id}  {sid}  ({grade})")
    for grade in sorted(by_grade):
        print(f"  added, by the house's own function grade: {grade} {by_grade[grade]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and diff, write nothing")
    ap.add_argument("--compare-rules", action="store_true", help="count clause 4 both ways; write nothing")
    args = ap.parse_args()
    if args.compare_rules:
        return compare_rules()
    runs, openings, refused = build_record()
    text = json.dumps(record(runs, openings, refused), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not OUT.exists():
            print(f"DOORYARD PICKET DRIFT\n  - {OUT.relative_to(ROOT)} is missing")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"DOORYARD PICKET DRIFT\n  - {OUT.relative_to(ROOT)} has drifted from "
                  f"the rule in tools/generate_dooryard_pickets.py")
            return 1
        print(f"verified {len(runs)} dooryard garden plots on platted house lots "
              f"({len(refused)} lot(s) refused for want of room)")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {len(runs)} dooryard garden plots "
          f"({len(refused)} lot(s) refused for want of room)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
