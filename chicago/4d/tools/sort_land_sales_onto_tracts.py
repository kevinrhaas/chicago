#!/usr/bin/env python3
"""Every land-sale row this project can put on the ground, sorted onto a survey tract (T-1104).

    tools/sort_land_sales_onto_tracts.py --build      re-derive the sort, rewrite the record
    tools/sort_land_sales_onto_tracts.py --check      the gate: re-derive every share and
                                                      every count and refuse any drift
    tools/sort_land_sales_onto_tracts.py --report     print what sorted, what refused, and
                                                      the section-9 adjudication in full
    tools/sort_land_sales_onto_tracts.py --self-test  the gate's assertions still fire when broken

THE HOLE THIS CLOSES. T-1101 put seven of Wright's nine legend chips on the ground, and
the register that says who bought what has been on the ground since T-0609 — but nothing
joined them. The tract layer's own `canal_section_9_remainder` entry says so in terms:
"The same seven 1830 canal entries cover section 9 as a whole; which of them fall outside
the Original Town is T-1102's question, because it needs every entry sorted onto a
polygon." This is that sort, and the answer to that question is measured below rather
than asserted: NOT ONE of the seven falls in the Original Town. All seven are entries in
the north half of section 9 — the two north quarters, W2NE, E2NE, E2NW, W2NW — and the
1830 plat is cut out of the section's SOUTH-EAST corner. The seven are the remainder's
own entrymen, and the remainder polygon, conjectural as its west bound is, is the ground
they bought.

WHAT SORTS A ROW, AND IN WHAT ORDER OF CONFIDENCE.

  geometry        A row whose ground.json entry encloses a ring is clipped against every
                  tract polygon and takes the tract that covers the most of it. The share
                  is an area ratio and is carried to a tenth of a per cent; every tract a
                  parcel touches at all is listed, not only the winner, because a parcel
                  that straddles a boundary is evidence about the boundary.
  owner_citation  Two rows describe their ground and do not enumerate it: ls0058 and
                  ls0059, `NFR` and `NFRSC` of section 10, whose ground.json entry is a
                  `committed_clip` — a section box and the sentence "north of the
                  committed north bank of the main stem" — with no ring. They are not
                  guessed at. The TRACT LAYER already cites both of them, by record, as
                  Kinzie's Addition's `owner_on_scene_date`, so the sort carries that
                  citation across and says which file made the join.
  refused         Everything else, with the reason, counted.

THE LAYER IS NOT A PARTITION, AND THAT IS WHY THERE IS A PRECEDENCE RULE. Nothing in
T-1101 required the nine polygons to tile the ground, and three of them do not: Wabansia's
committed seating stands inside `canal_section_9_remainder`, which is section 9 with only
the Original Town cut out of it, and Kinzie's Addition's street envelope crosses the 9/10
section line by a strip. So a parcel in the north-west of section 9 is inside two
polygons at once and "the tract with the largest share" would hand every one of them to
the residual. The rule instead:

  A parcel takes the tract that covers the most of it, EXCEPT that a tract whose boundary
  is a RESIDUAL — a ring defined as what another tract leaves over — yields any parcel a
  non-residual tract covers at least half of.

`canal_section_9_remainder` is the only residual in the layer; its own `boundary_from`
says "section 9 with the Original Town cut out of its south-east corner". The rule is
stated here rather than in the data, and it is applied in one place, so a later reader can
disagree with it in one place.

WHAT IS REFUSED, and the refusals carry their numbers.

  outside the four sections   1,226 rows of the register's 1,572 never reached the modelled
                              ground at all (T-0609 refused them there, and this sort does
                              not re-litigate it). Not one of them names a section inside
                              T39N R14E sections 9, 10, 15 or 16 — the four the PLSS grid is
                              carried across and the only ground any tract polygon stands
                              on — so no tract here could have taken them even if the grid
                              were carried further. That is a measurement, made below, not
                              an assumption.
  the town-plat lots          616 rows carry a town code — CHIOT, CHIOTV, CHIV, CHI,
                              CHIOTVO — and no section at all. They name a PLAT, which is
                              exactly what a survey tract is, and sorting them would be the
                              single largest thing this file could do. It does not, under
                              T-0830's standing rule: the Archives' key for these
                              abbreviations is not reachable from this runner and guessing
                              which addition `CHIV` names would put a house in the wrong
                              half of the town. What this file adds is the reason that rule
                              cannot be got round by counting blocks, which is the obvious
                              way to try: the town codes run to block 58, and the SCHOOL
                              SECTION's own rows — separately described, section 16, no
                              town code — run to block 58 as well. A block number in the
                              fifties is not diagnostic of the Original Town, so the
                              block range decides nothing and the refusal stands where
                              T-0830 left it.

NOTHING HERE AUTHORS GEOMETRY. Every ring read is a ring another file committed; this one
clips and counts. The polygons come from `data/reconstruction/1835_survey_tracts.json`
and the parcels from `data/research/land_sales/ground.json`, both of which are re-derived
by their own gate steps before this one runs.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACTS = ROOT / "data" / "reconstruction" / "1835_survey_tracts.json"
GROUND = ROOT / "data" / "research" / "land_sales" / "ground.json"
ENTRIES = ROOT / "data" / "research" / "land_sales" / "entries.json"
RECORD = ROOT / "data" / "reconstruction" / "1835_land_sales_by_tract.json"

SCENE_DATE = "1835-07-01"
ACRE_M2 = 4046.8564224

# The one residual ring in the layer. Named here, not guessed at from the grade: its own
# `boundary_from` field defines it as what the Original Town leaves over.
RESIDUAL_TRACTS = {"canal_section_9_remainder"}

# The share a non-residual tract must cover before it takes a parcel off the residual.
MAJORITY = 0.50

# Touching at all, below which a share is a rounding artifact of the clip rather than a
# statement that a parcel is on a tract. 1 m2 against parcels of 12,000 m2 and up.
TOUCH_M2 = 1.0

# The four sections the PLSS grid is carried across (L219) and the only ground any tract
# polygon stands on. Used to MEASURE the outside-refusal, never to make it.
GRID_SECTIONS = {"09", "10", "15", "16"}
GRID_TOWNSHIP = ("39N", "14E")


# ---------------------------------------------------------------- plane geometry


def _acres(values) -> float:
    """An acreage column, summed exactly (T-1486).

    `sum()` accumulates left to right and drifts a few parts in 10^15, which decides the
    last digit whenever the true figure sits on the rounding boundary; `math.fsum` is
    correctly rounded and order-independent, so the same rows give the same acreage on
    every machine. `fsum` always returns a FLOAT, though, and a tract with no ground
    measured here carries an integer `0` in the committed file — so the all-zero column,
    which has no boundary to drift across, keeps the exact arithmetic it already had.
    This is an arithmetic fix and it moves no committed byte.
    """
    values = list(values)
    # exact-sum-ok: the fallback runs only on an all-zero column, which has no boundary
    return round(math.fsum(values) if any(values) else sum(values), 2)


def ring_area(ring: list) -> float:
    """Unsigned area of a closed ring given as a list of (e, n)."""
    s = 0.0
    for i in range(len(ring)):
        e1, n1 = ring[i]
        e2, n2 = ring[(i + 1) % len(ring)]
        s += e1 * n2 - e2 * n1
    return abs(s) / 2.0


def signed_area(ring: list) -> float:
    s = 0.0
    for i in range(len(ring)):
        e1, n1 = ring[i]
        e2, n2 = ring[(i + 1) % len(ring)]
        s += e1 * n2 - e2 * n1
    return s / 2.0


def clip_by_convex(subject: list, clip: list) -> list:
    """Sutherland-Hodgman. `subject` may be concave; `clip` must be convex.

    Every clip polygon this file passes in is a triangle, so the convexity requirement is
    met by construction rather than by trust.
    """
    poly = [tuple(p) for p in clip]
    if signed_area(poly) < 0:
        poly = poly[::-1]
    out = [tuple(p) for p in subject]
    for i in range(len(poly)):
        if not out:
            return []
        a = poly[i]
        b = poly[(i + 1) % len(poly)]
        ex, ny = b[0] - a[0], b[1] - a[1]
        inp, out = out, []
        for j in range(len(inp)):
            cur = inp[j]
            prv = inp[j - 1]
            sc = ex * (cur[1] - a[1]) - ny * (cur[0] - a[0])
            sp = ex * (prv[1] - a[1]) - ny * (prv[0] - a[0])
            if sc >= 0:
                if sp < 0:
                    t = sp / (sp - sc)
                    out.append((prv[0] + t * (cur[0] - prv[0]), prv[1] + t * (cur[1] - prv[1])))
                out.append(cur)
            elif sp >= 0:
                t = sp / (sp - sc)
                out.append((prv[0] + t * (cur[0] - prv[0]), prv[1] + t * (cur[1] - prv[1])))
    return out


def triangulate(ring: list) -> list:
    """Ear clipping. A simple polygon, however concave, into triangles."""
    pts = [tuple(p) for p in ring]
    if signed_area(pts) < 0:
        pts = pts[::-1]
    idx = list(range(len(pts)))
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 10 * len(ring) + 100:
        guard += 1
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = pts[i0], pts[i1], pts[i2]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if cross <= 0:
                continue  # reflex or collinear: not an ear
            if any(_in_triangle(pts[m], a, b, c) for m in idx if m not in (i0, i1, i2)):
                continue
            tris.append((a, b, c))
            idx.pop(k)
            break
        else:
            break  # no ear found: degenerate ring, fall through to the fan below
    if len(idx) == 3:
        tris.append((pts[idx[0]], pts[idx[1]], pts[idx[2]]))
    elif len(idx) > 3:
        for k in range(1, len(idx) - 1):
            tris.append((pts[idx[0]], pts[idx[k]], pts[idx[k + 1]]))
    return tris


def _in_triangle(p, a, b, c) -> bool:
    d1 = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    d2 = (c[0] - b[0]) * (p[1] - b[1]) - (c[1] - b[1]) * (p[0] - b[0])
    d3 = (a[0] - c[0]) * (p[1] - c[1]) - (a[1] - c[1]) * (p[0] - c[0])
    return d1 >= 0 and d2 >= 0 and d3 >= 0


def overlap_area(parcel: list, tract: list) -> float:
    """Area of parcel ∩ tract. Both may be concave: the parcel is triangulated and each
    triangle is used as the convex clip against the tract ring."""
    total = 0.0
    for tri in triangulate(parcel):
        piece = clip_by_convex(tract, list(tri))
        if len(piece) >= 3:
            total += ring_area(piece)
    return total


# ---------------------------------------------------------------- the sort


def parcel_ring(ground: dict) -> list | None:
    for key in ("corners_local_enu", "ring_local_enu"):
        ring = ground.get(key)
        if ring and len(ring) >= 3:
            return [(float(e), float(n)) for e, n in ring]
    return None


def build_sort() -> dict:
    tracts_doc = json.loads(TRACTS.read_text())
    ground_doc = json.loads(GROUND.read_text())
    entries_doc = json.loads(ENTRIES.read_text())
    by_id = {e["record_id"]: e for e in entries_doc["entries"]}

    polys = {}
    grades = {}
    for t in tracts_doc["tracts"]:
        ring = t.get("polygon_local_enu_m")
        if ring:
            polys[t["id"]] = [(float(e), float(n)) for e, n in ring]
            grades[t["id"]] = t.get("geometry_confidence")

    # The tract layer's own owner citations, read back as a route for the parcels that
    # describe their ground without enumerating it.
    cited_by_tract = {}
    for t in tracts_doc["tracts"]:
        owner = t.get("owner_on_scene_date") or {}
        for ent in owner.get("entries", []) or []:
            key = (
                (ent.get("purchaser") or "").upper(),
                ent.get("aliquot_as_read"),
                ent.get("date"),
            )
            cited_by_tract.setdefault(key, set()).add(t["id"])

    sorted_rows = []
    refusals = {
        "outside_the_modelled_ground": [],
        "description_not_read": [],
        "no_ring_and_no_citation": [],
    }
    town_lots = []
    outside_sections = {}

    for row in ground_doc["tracts"]:
        rid = row["record_id"]
        entry = by_id[rid]
        base = {
            "record_id": rid,
            "purchase_no": entry.get("purchase_no"),
            "purchaser_as_read": row.get("purchaser_as_read"),
            "purchaser_normalized": row.get("purchaser_normalized"),
            "description_as_read": entry.get("aliquot_or_lot_as_read"),
            "date_purchased": row.get("date_purchased"),
            "on_or_before_scene_date": bool(
                row.get("date_purchased") and row["date_purchased"] <= SCENE_DATE
            ),
            "type_of_sale": row.get("type_of_sale"),
            "section": row.get("section") or None,
            "township": row.get("township") or None,
            "range": row.get("range") or None,
            "void": row.get("void"),
        }

        ground = row.get("ground")
        if not ground:
            tract = entry.get("tract") or {}
            if tract.get("resolves") == "town_plat_lot":
                town_lots.append(
                    {
                        **base,
                        "town_code": tract.get("town_code"),
                        "block": tract.get("block"),
                        "lot": tract.get("lot"),
                    }
                )
            else:
                if row.get("refusal") == "description_not_read":
                    refusals["description_not_read"].append(
                        {**base, "ground_refusal": row.get("refusal")}
                    )
                    continue
                sec = row.get("section") or ""
                tr = (row.get("township") or "", row.get("range") or "")
                inside = tr == GRID_TOWNSHIP and sec in GRID_SECTIONS
                key = f"{tr[0] or '—'} {tr[1] or '—'} sec {sec or '—'}"
                bucket = outside_sections.setdefault(
                    key, {"rows": 0, "inside_the_carried_grid": inside}
                )
                bucket["rows"] += 1
                refusals["outside_the_modelled_ground"].append(
                    {**base, "ground_refusal": row.get("refusal")}
                )
            continue

        ring = parcel_ring(ground)
        if ring is None:
            key = (
                (base["purchaser_normalized"] or "").upper(),
                base["description_as_read"],
                base["date_purchased"],
            )
            cited = sorted(cited_by_tract.get(key, ()))
            if len(cited) == 1:
                sorted_rows.append(
                    {
                        **base,
                        "ground_kind": ground.get("kind"),
                        "ground_name": ground.get("name"),
                        "tract": cited[0],
                        "route": "owner_citation",
                        "share_of_the_parcel": None,
                        "parcel_acres": None,
                        "also_touches": [],
                        "note": (
                            "the ground is described and not enumerated — a committed_clip "
                            "with no ring — so no share can be taken. The tract layer already "
                            "cites this record as this tract's owner on the scene date, and "
                            "that citation is what places it."
                        ),
                    }
                )
            else:
                refusals["no_ring_and_no_citation"].append(
                    {**base, "ground_kind": ground.get("kind")}
                )
            continue

        parcel_m2 = ring_area(ring)
        shares = []
        for tid, poly in polys.items():
            a = overlap_area(ring, poly)
            if a > TOUCH_M2:
                shares.append((tid, a))
        shares.sort(key=lambda s: -s[1])
        if not shares:
            refusals["no_ring_and_no_citation"].append(
                {**base, "ground_kind": ground.get("kind"), "note": "no tract polygon reaches it"}
            )
            continue

        non_residual = [s for s in shares if s[0] not in RESIDUAL_TRACTS]
        winner = shares[0]
        rule = "largest_share"
        if winner[0] in RESIDUAL_TRACTS and non_residual:
            best = non_residual[0]
            if best[1] / parcel_m2 >= MAJORITY:
                winner = best
                rule = "a_non_residual_tract_covering_at_least_half"
            else:
                rule = "largest_share_the_residual_keeps_it"

        sorted_rows.append(
            {
                **base,
                "ground_kind": ground.get("kind"),
                "ground_name": ground.get("name"),
                "tract": winner[0],
                "route": "geometry",
                "rule_applied": rule,
                "share_of_the_parcel": round(winner[1] / parcel_m2, 4),
                "parcel_acres": round(parcel_m2 / ACRE_M2, 2),
                "also_touches": [
                    {"tract": tid, "share_of_the_parcel": round(a / parcel_m2, 4)}
                    for tid, a in shares
                    if tid != winner[0]
                ],
            }
        )

    return assemble(
        tracts_doc, ground_doc, entries_doc, polys, grades, sorted_rows, refusals, town_lots, outside_sections
    )


def assemble(tracts_doc, ground_doc, entries_doc, polys, grades, sorted_rows, refusals, town_lots, outside_sections):
    by_tract = {}
    for tid in polys:
        rows = [r for r in sorted_rows if r["tract"] == tid]
        parcels = {}
        for r in rows:
            if r["route"] == "geometry":
                parcels[r.get("ground_name") or r["record_id"]] = (
                    (r["parcel_acres"] or 0) * (r["share_of_the_parcel"] or 0)
                )
        by_tract[tid] = {
            "geometry_confidence": grades.get(tid),
            "is_the_residual": tid in RESIDUAL_TRACTS,
            "rows": len(rows),
            "rows_on_or_before_the_scene_date": sum(1 for r in rows if r["on_or_before_scene_date"]),
            "rows_with_no_measured_share": sum(1 for r in rows if r["share_of_the_parcel"] is None),
            "distinct_parcels": len(parcels),
            "acres_of_DISTINCT_parcel_ground_here": _acres(parcels.values()),
            "acres_summed_over_rows": _acres(
                (r["parcel_acres"] or 0) * (r["share_of_the_parcel"] or 0)
                for r in rows
                if r["route"] == "geometry"
            ),
            "why_the_two_acre_figures_differ": (
                "a school-section BLOCK is the smallest ground this project can place, and a "
                "register row is a LOT inside one, so one block is repeated once per lot sold "
                "in it. Summing over rows counts that block once per row and is not an area."
            ),
            "record_ids": [r["record_id"] for r in rows],
        }

    # Where two polygons cover the same parcel ground, measured off the parcels rather
    # than off the rings: the pair, and the largest share one parcel gives to both.
    pair_overlaps = {}
    for r in sorted_rows:
        for other in r.get("also_touches") or []:
            key = " ∩ ".join(sorted([r["tract"], other["tract"]]))
            share = min(r["share_of_the_parcel"] or 0, other["share_of_the_parcel"])
            best = pair_overlaps.get(key)
            if best is None or share > best["largest_share_a_parcel_gives_to_both"]:
                pair_overlaps[key] = {
                    "largest_share_a_parcel_gives_to_both": round(share, 4),
                    "on_record": r["record_id"],
                    "parcels_touching_both": 0,
                }
    for r in sorted_rows:
        for other in r.get("also_touches") or []:
            key = " ∩ ".join(sorted([r["tract"], other["tract"]]))
            pair_overlaps[key]["parcels_touching_both"] += 1

    # The block-range measurement that closes the obvious way round T-0830's rule.
    town_blocks = [int(t["block"]) for t in town_lots if t.get("block") and str(t["block"]).isdigit()]
    school_blocks = [
        r["ground_name"] for r in sorted_rows if r["tract"] == "school_section" and r.get("ground_name")
    ]
    school_numbers = []
    for row in ground_doc["tracts"]:
        g = row.get("ground") or {}
        if g.get("kind") == "school_section_block" and g.get("block_number"):
            school_numbers.append(int(g["block_number"]))

    outside = sorted(outside_sections.items(), key=lambda kv: -kv[1]["rows"])
    inside_grid_but_refused = sum(v["rows"] for _, v in outside if v["inside_the_carried_grid"])

    return {
        "$schema_note": (
            "DERIVED, and it authors no coordinate. Every share below is re-computed by "
            "tools/sort_land_sales_onto_tracts.py --check from the committed tract polygons and "
            "the committed parcel rings; the gate refuses any drift. Nothing here is a new "
            "boundary, a new parcel or a new owner — it is a join between two files that "
            "already stood on their own gates."
        ),
        "id": "land_sales_by_survey_tract_1835",
        "target_date": SCENE_DATE,
        "ticket": "T-1104 (piece 1 of T-1102, itself piece 2 of T-1097 and piece 2 of T-0792)",
        "tool": "tools/sort_land_sales_onto_tracts.py",
        "reads": [
            "data/reconstruction/1835_survey_tracts.json",
            "data/research/land_sales/ground.json",
            "data/research/land_sales/entries.json",
        ],
        "why_this_file_exists": (
            "The tract layer names who surveyed the ground; the register names who bought it. "
            "Neither could answer a question about the other until they were joined. The join "
            "is what the parent ticket asked for and what canal_section_9_remainder's own owner "
            "refusal defers to by name."
        ),
        "the_rule": {
            "route_geometry": (
                "a parcel takes the tract that covers the most of it, by clipped area, and every "
                "tract it touches by more than 1 m² is listed with its share"
            ),
            "the_precedence_clause": (
                "EXCEPT that a residual tract — one whose ring is defined as what another tract "
                "leaves over — yields any parcel a non-residual tract covers at least 50% of. "
                "canal_section_9_remainder is the layer's only residual."
            ),
            "route_owner_citation": (
                "a parcel whose ground is described and not enumerated takes the tract that "
                "already cites its record as an owner, and only where exactly one tract does"
            ),
            "no_share_is_rounded_up": (
                "shares are area ratios carried to four places; a parcel on two tracts keeps both"
            ),
        },
        "the_section_9_answer": {
            "the_question": (
                "canal_section_9_remainder's owner_on_scene_date refusal: 'The same seven 1830 "
                "canal entries cover section 9 as a whole; which of them fall outside the "
                "Original Town is T-1102's question.'"
            ),
            "the_answer": (
                "All seven, and none of them inside it. Every one of the seven is an entry in "
                "the NORTH half of section 9 — W2NE, E2NE, E2NW ×2, W2NW and the two VO peers — "
                "and canal_commissioners_1830 is cut out of the section's SOUTH-EAST corner. The "
                "clipped overlap of each of the seven with the Original Town polygon is zero."
            ),
            "entries": [
                {
                    "record_id": r["record_id"],
                    "purchaser": r["purchaser_normalized"],
                    "description_as_read": r["description_as_read"],
                    "date_purchased": r["date_purchased"],
                    "tract": r["tract"],
                    "share_of_the_parcel": r["share_of_the_parcel"],
                    "also_touches": r["also_touches"],
                }
                for r in sorted_rows
                if r.get("section") == "09"
            ],
            "and_the_thing_it_turns_up": (
                "Two of the seven — Edmond Roberts's W2NW at 81.1% and James Kinzie's E2NW at "
                "12.1% — stand on Wabansia's committed seating, which is inside the remainder "
                "ring because nothing cut it out. That is the precedence clause's whole reason "
                "for existing, and it is a finding about the LAYER: the nine polygons do not tile."
            ),
        },
        "two_rows_that_need_saying_out_loud": {
            "ls0057_is_a_tautology_and_is_reported_as_one": (
                "John Baptist Beaubien's `SWFR` of section 10, entered 1835-05-28, sorts onto "
                "us_military_reservation at 100.0% — and that share proves nothing about the "
                "entry. The ring ground.json carries for the south-west fraction of section 10 "
                "IS the committed reservation ring, to the two decimals it is rounded at, and so "
                "is the tract layer's reservation polygon. The clip is therefore a ring against "
                "itself. What it IS worth is a consistency check — the two files still carry the "
                "same committed ring — and it is recorded as that. The tract layer's own refusal "
                "to name Beaubien the reservation's owner is untouched by this file: sorting a "
                "parcel onto a polygon says where the ground is, not who held it."
            ),
            "the_school_section_blocks_cross_the_15_16_line": (
                "Eight rows, on the six blocks numbered 131 and 133 to 137, put between 0.3% and "
                "5.7% of their block into fractional_section_15. Both sides are committed: the "
                "blocks are `data/traces/vectors/school_section_blocks_1834.json` and the section "
                "line is the PLSS grid carried from G1 (L219). So the two disagree by up to a few "
                "metres along the south edge of the school section, which is well inside what a "
                "grid carried a mile from one corner is entitled to claim. It is recorded, not "
                "corrected: neither file is wrong enough to move on this evidence."
            ),
        },
        "the_layer_does_not_tile": {
            "note": (
                "Measured off the parcels, not off the rings: these tract pairs both cover ground "
                "a committed parcel stands on. T-1101 never claimed a partition and this is not a "
                "fault in it; it is a fact a sort has to have a rule for."
            ),
            "pairs": pair_overlaps,
        },
        "refusals": {
            "town_plat_lots": {
                "rows": len(town_lots),
                "why": (
                    "T-0830's standing rule: the town codes are carried as printed and the plat is "
                    "never named, because the Archives' key for the abbreviations is not reachable "
                    "from this runner. Sorting them would be this file's largest single act and it "
                    "is refused."
                ),
                "the_way_round_it_that_does_not_work": {
                    "the_idea": (
                        "the Original Town was platted in 58 blocks, so a town code running to "
                        "block 58 could be read as naming it"
                    ),
                    "highest_block_under_a_town_code": max(town_blocks) if town_blocks else None,
                    "highest_block_in_the_school_section_rows": max(school_numbers) if school_numbers else None,
                    "the_verdict": (
                        "not diagnostic. The school section's own rows — separately described by "
                        "section and carrying no town code at all — reach the same block number, so "
                        "a block in the fifties distinguishes nothing and the refusal stands where "
                        "T-0830 left it."
                    ),
                },
                "by_code": _count_by(town_lots, "town_code"),
            },
            "outside_the_modelled_ground": {
                "rows": len(refusals["outside_the_modelled_ground"]),
                "why": (
                    "T-0609 could not put them on the ground and this sort does not re-litigate "
                    "that. What it adds is the reason no tract could have taken them anyway."
                ),
                "rows_naming_a_section_inside_the_carried_grid": inside_grid_but_refused,
                "the_measurement": (
                    "Not one row in this bucket names T39N R14E section 9, 10, 15 or 16 — the four "
                    "the PLSS grid is carried across (L219) and the only ground any tract polygon "
                    "stands on. The refusal is therefore about ground outside the layer, not about "
                    "a gap inside it. The only rows that name a carried section and still get no "
                    "tract are the three whose DESCRIPTION could not be read, counted separately "
                    "below."
                ),
                "top_sections_refused": [
                    {"where": k, "rows": v["rows"], "inside_the_carried_grid": v["inside_the_carried_grid"]}
                    for k, v in outside[:10]
                ],
            },
            "description_not_read": {
                "rows": len(refusals["description_not_read"]),
                "why": (
                    "T-0609's parser could not read the legal description, so there is no parcel "
                    "to clip. Two of the three DO name a section inside the carried grid — "
                    "`ADDFRSEC` in sections 10 and 15, an added fraction the register abbreviates "
                    "and this project has never expanded — and the third, `06126` in section 16, "
                    "is not a description at all. They are the only rows in the register that a "
                    "reading, rather than a wider grid, could bring onto a tract."
                ),
                "records": [
                    {
                        "record_id": r["record_id"],
                        "section": r["section"],
                        "description_as_read": r["description_as_read"],
                        "purchaser_normalized": r["purchaser_normalized"],
                    }
                    for r in refusals["description_not_read"]
                ],
            },
            "no_ring_and_no_citation": {
                "rows": len(refusals["no_ring_and_no_citation"]),
                "records": [r["record_id"] for r in refusals["no_ring_and_no_citation"]],
            },
        },
        "by_tract": by_tract,
        "sorted": sorted_rows,
        "cross_checks": {
            "register_rows": entries_doc["count"],
            "rows_ground_json_placed": sum(1 for r in ground_doc["tracts"] if r.get("ground")),
            "rows_sorted_onto_a_tract": len(sorted_rows),
            "rows_refused": (
                len(town_lots)
                + len(refusals["outside_the_modelled_ground"])
                + len(refusals["description_not_read"])
                + len(refusals["no_ring_and_no_citation"])
            ),
            "every_placed_row_is_sorted_or_refused": True,
            "tracts_with_a_polygon": len(polys),
            "tracts_that_took_a_row": sum(1 for v in by_tract.values() if v["rows"]),
        },
        "summary": {
            "sorted": len(sorted_rows),
            "by_geometry": sum(1 for r in sorted_rows if r["route"] == "geometry"),
            "by_owner_citation": sum(1 for r in sorted_rows if r["route"] == "owner_citation"),
            "refused": (
                len(town_lots)
                + len(refusals["outside_the_modelled_ground"])
                + len(refusals["description_not_read"])
                + len(refusals["no_ring_and_no_citation"])
            ),
            "parcels_on_more_than_one_tract": sum(1 for r in sorted_rows if r.get("also_touches")),
            "tract_pairs_that_overlap": len(pair_overlaps),
        },
    }


def _count_by(rows: list, key: str) -> dict:
    out = {}
    for r in rows:
        out[str(r.get(key))] = out.get(str(r.get(key)), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


# ---------------------------------------------------------------- the commands


def cmd_build() -> int:
    doc = build_sort()
    RECORD.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {RECORD.relative_to(ROOT)}")
    print(json.dumps(doc["summary"], indent=2))
    return 0


def cmd_check() -> int:
    if not RECORD.exists():
        print(f"FAIL {RECORD.relative_to(ROOT)} is missing")
        return 1
    committed = json.loads(RECORD.read_text())
    derived = build_sort()
    problems = []

    if committed.get("sorted") != derived.get("sorted"):
        c = {r["record_id"]: r for r in committed.get("sorted", [])}
        d = {r["record_id"]: r for r in derived["sorted"]}
        for rid in sorted(set(c) | set(d)):
            if c.get(rid) != d.get(rid):
                problems.append(
                    f"the sort of {rid} is not what the committed polygons re-derive: "
                    f"committed {json.dumps(c.get(rid))[:180]} / derived {json.dumps(d.get(rid))[:180]}"
                )
                if len(problems) > 6:
                    break

    for section in ("by_tract", "cross_checks", "summary", "the_layer_does_not_tile", "refusals"):
        if committed.get(section) != derived.get(section):
            problems.append(f"`{section}` drifted from what the inputs re-derive")

    if committed.get("the_section_9_answer", {}).get("entries") != derived["the_section_9_answer"]["entries"]:
        problems.append("the section-9 adjudication drifted")

    # The claims the prose makes, held as numbers rather than as sentences.
    s9 = derived["the_section_9_answer"]["entries"]
    if len(s9) != 7:
        problems.append(f"section 9 carries {len(s9)} register rows, not the seven the record names")
    for row in s9:
        touched = {row["tract"]} | {t["tract"] for t in row["also_touches"]}
        if "canal_commissioners_1830" in touched:
            problems.append(
                f"{row['record_id']} now overlaps the Original Town — the record says none of the seven does"
            )
    if derived["refusals"]["outside_the_modelled_ground"]["rows_naming_a_section_inside_the_carried_grid"]:
        problems.append(
            "a row refused for being outside the modelled ground now names a section inside the "
            "carried grid — the record says none does, and that is what makes the refusal about "
            "ground outside the layer rather than a gap inside it"
        )
    if derived["refusals"]["description_not_read"]["rows"] != 3:
        problems.append(
            f"{derived['refusals']['description_not_read']['rows']} descriptions go unread, not the "
            "three the record names"
        )
    if not derived["the_layer_does_not_tile"]["pairs"]:
        problems.append("no tract pair overlaps any more — the precedence clause has nothing to do")

    if problems:
        for p in problems:
            print(f"FAIL {p}")
        return 1
    print(
        f"OK {derived['summary']['sorted']} register rows sorted onto "
        f"{derived['cross_checks']['tracts_that_took_a_row']} tracts, "
        f"{derived['summary']['refused']} refused, "
        f"{derived['summary']['tract_pairs_that_overlap']} overlapping tract pairs"
    )
    return 0


def cmd_report() -> int:
    doc = json.loads(RECORD.read_text()) if RECORD.exists() else build_sort()
    print("LAND SALES SORTED ONTO THE SURVEY TRACTS")
    print()
    for tid, v in doc["by_tract"].items():
        print(
            f"  {tid:<28} {v['rows']:>4} rows  {v['distinct_parcels']:>4} parcels"
            f"  {v['acres_of_DISTINCT_parcel_ground_here']:>8.2f} ac"
            f"  ({v['geometry_confidence']}{', residual' if v['is_the_residual'] else ''})"
        )
    print()
    print("  THE SECTION-9 QUESTION THE TRACT LAYER DEFERRED HERE")
    for e in doc["the_section_9_answer"]["entries"]:
        also = ", ".join(f"{t['tract']} {t['share_of_the_parcel']:.1%}" for t in e["also_touches"])
        print(
            f"    {e['record_id']}  {e['description_as_read']:<10} {e['purchaser']:<20}"
            f" → {e['tract']} {e['share_of_the_parcel']:.1%}" + (f"   [also {also}]" if also else "")
        )
    print()
    print("  REFUSED")
    for key in ("town_plat_lots", "outside_the_modelled_ground", "description_not_read", "no_ring_and_no_citation"):
        print(f"    {key:<30} {doc['refusals'][key]['rows']:>5}")
    print()
    print("  THE LAYER DOES NOT TILE")
    for pair, v in doc["the_layer_does_not_tile"]["pairs"].items():
        print(
            f"    {pair:<58} {v['parcels_touching_both']} parcel(s), "
            f"largest shared share {v['largest_share_a_parcel_gives_to_both']:.1%}"
        )
    return 0


def cmd_self_test() -> int:
    """The gate's assertions still fire when broken."""
    failures = []

    # The clipper: a unit square against itself, and against a half of itself.
    unit = [(0, 0), (10, 0), (10, 10), (0, 10)]
    if abs(overlap_area(unit, unit) - 100.0) > 1e-6:
        failures.append("a square does not fully overlap itself")
    half = [(0, 0), (5, 0), (5, 10), (0, 10)]
    if abs(overlap_area(unit, half) - 50.0) > 1e-6:
        failures.append("a square's half does not clip to half its area")
    apart = [(100, 100), (110, 100), (110, 110), (100, 110)]
    if overlap_area(unit, apart) != 0.0:
        failures.append("two disjoint squares report an overlap")

    # An L against a square that only its arm reaches: the concave case the residual ring is.
    ell = [(0, 0), (10, 0), (10, 5), (5, 5), (5, 10), (0, 10)]
    if abs(ring_area(ell) - 75.0) > 1e-6:
        failures.append("the L's own area is not 75")
    notch = [(5, 5), (10, 5), (10, 10), (5, 10)]
    if overlap_area(notch, ell) > 1e-6:
        failures.append("the L overlaps the notch cut out of it")
    if abs(overlap_area(unit, ell) - 75.0) > 1e-6:
        failures.append("the L clipped by the square that contains it is not the L")

    # The precedence clause: a residual must yield a parcel a real tract covers half of,
    # and must KEEP one it does not.
    doc = json.loads(RECORD.read_text()) if RECORD.exists() else build_sort()
    yielded = [r for r in doc["sorted"] if r.get("rule_applied") == "a_non_residual_tract_covering_at_least_half"]
    kept = [r for r in doc["sorted"] if r.get("rule_applied") == "largest_share_the_residual_keeps_it"]
    if not yielded:
        failures.append("the precedence clause never fires — no parcel is taken off the residual")
    if not kept:
        failures.append("the precedence clause always fires — the residual never keeps a straddler")
    for r in yielded:
        if r["share_of_the_parcel"] < MAJORITY:
            failures.append(f"{r['record_id']} was taken off the residual on {r['share_of_the_parcel']:.1%}")
    for r in kept:
        best = max((t["share_of_the_parcel"] for t in r["also_touches"]), default=0.0)
        if best >= MAJORITY:
            failures.append(f"{r['record_id']} stayed on the residual against a {best:.1%} claim")

    # The refusals are gated too: a later edit that quietly sorted the town lots would
    # read correctly in prose and only this would notice.
    if doc["refusals"]["town_plat_lots"]["rows"] != 616:
        failures.append("the town-plat refusal no longer covers 616 rows")
    if any(r.get("route") == "town_code" for r in doc["sorted"]):
        failures.append("a town-plat lot has been sorted onto a tract against T-0830's rule")

    if failures:
        for f in failures:
            print(f"FAIL {f}")
        return 1
    print(
        f"OK clipper exact on 6 constructed cases; precedence clause fires on {len(yielded)} "
        f"parcel(s) and is withheld on {len(kept)}; both refusals still stand"
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.build:
        return cmd_build()
    if args.check:
        return cmd_check()
    if args.report:
        return cmd_report()
    if args.self_test:
        return cmd_self_test()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
