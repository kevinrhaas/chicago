#!/usr/bin/env python3
"""Which control seats the West Division's five north-south lines, and what the plat's module would cost (T-1540).

The owner ruled on T-1479, 2026-09-21: *"Clinton to Canal stands at 367.9 ft against the
plat's 458 ft. That 90 ft is a real defect and it is nobody's: T-0444 and T-0445 both
closed without moving it, which is how a measured error becomes part of the town by
default. A successor ticket owns it. … THE SUCCESSOR OWNS THE WHOLE QUESTION, not just
the number … A ticket that only says '458 not 367.9' will close the same way its two
predecessors did."*

So this module does not say '458 not 367.9'. NOTHING MOVES HERE: no centreline is
edited, no block re-emitted, no record re-seated. It writes numbers, in the manner of
tools/measure_west_division_module.py and tools/measure_west_grid_migration.py, and the
numbers are four.

1. **THE TWO CONTROLS ARE NOT RIVALS, AND THAT IS THE ANSWER TO THE FIRST QUESTION.**
   Every one of the five lines is seated on `osm_streets_2026` — modern surviving
   geometry, warped through the 1834 datum — and every one of them carries
   `thompson_plat_1830` for the claim that the street EXISTED. Not one of them was ever
   placed by the plat's module, because the sheet reading refuses to place anything:
   `data/traces/thompson_west_division_lots.json` says in its own confidence note that
   `documented` "grades THE FIGURES AND THE COUNTS … It does not grade any position:
   nothing here says where in the world a block is." So the plat gives a MODULE and no
   position; the survey gives POSITIONS and no module. Neither can be swapped for the
   other, and "which of the two is the control" has different answers for the two
   questions a control answers.

2. **THE GAP IS ON EVERY INTERVAL, NOT ON ONE, AND IT IS NOT EVEN.** Clinton to Canal is
   the interval T-0444 reported and T-1479's refusals name, but its two neighbours are
   short as well, by different amounts. That is the finding that stops this ticket
   closing the way its predecessors did: a single street line moved east or west cannot
   fix three unequal intervals, so "move Clinton" is not the shape of the repair.

3. **NOT EVERY GAP IS A DEFECT.** `data/datum.json` fits the 1834 sheets to modern
   ground at 17.5 m RMS, and a spacing error smaller than that cannot be told apart from
   the georeferencing. Each interval is therefore reported against that residual rather
   than against zero, and at least one of them sits inside it.

4. **WHAT THE PLAT WOULD COST IS PRICED, NOT ASSERTED.** If the module wins, the grid
   has to hang off one anchor and step 458 ft, and the two candidate anchors give
   different answers — one of them moves the only line in the division with a physical
   control, whose east kerb is committed to stand on the 1834 waterline. Both are
   computed, and what is seated on the present spacing is counted beside them.

    tools/measure_west_division_spacing.py              -> print the derivation
    tools/measure_west_division_spacing.py --check      -> re-derive, byte for byte
    tools/measure_west_division_spacing.py --self-test  -> the assertions
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "traces" / "west_division_spacing_control.json"
FT_M = 0.3048

# The files this reading stands on. Every figure below comes out of one of them.
STREETS = DATA / "streets" / "1835.json"
SHEET = DATA / "traces" / "thompson_west_division_lots.json"
LOTS = DATA / "traces" / "vectors" / "thompson_lots.json"
DATUM = DATA / "datum.json"

# The layers a lot id reaches — the committed files that do the seating. Same list as
# tools/measure_west_grid_migration.py reads, for the same reason: what is seated on
# this spacing is what would have to be re-seated if the lines move.
SEATED_IN = (
    DATA / "enclosures" / "town_lot_line_rails.json",
    DATA / "enclosures" / "town_lot_line_boards.json",
    DATA / "enclosures" / "town_lot_line_pickets.json",
    DATA / "frontage" / "town_street_edge.json",
)

# What a source id means about a LINE'S POSITION, as opposed to about the street's
# existence. Nothing is asserted about a street here that its own record does not carry:
# these are the committed source ids, grouped by the kind of claim they can support.
PLACES_A_LINE = {
    "osm_streets_2026": "modern surviving street geometry, warped through the datum",
    "wright_1834": "a georeferenced 1834 sheet",
    "hathaway_1834": "a georeferenced 1834 sheet",
    "chicago_dpw_1891_streets": "an 1891 municipal street survey",
}
ATTESTS_EXISTENCE_ONLY = {
    "thompson_plat_1830": "the plat that DRAWS the street and prints the module",
    "fergus_chicago_directory_1839": "a directory that names the street",
}


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def mean_east(street: dict) -> float:
    pts = [(float(e), float(n)) for e, n in street["path_local_enu_m"]]
    return sum(p[0] for p in pts) / len(pts)


def seating_between(block_ids: set[str]) -> dict:
    """Everything committed that is seated on these blocks, by block id and by lot id.

    Counted rather than listed wherever the list would be long: the point of the figure
    is the SIZE of what a street move would drag with it, and a count that changes is a
    re-seat that has changed.
    """
    patterns = [re.compile(rf"{b}_lot\d+") for b in sorted(block_ids)]
    structures, lots_reached, named = [], set(), set()
    for path in sorted((DATA / "structures").glob("*.json")):
        text = path.read_text(encoding="utf-8")
        hit = re.search(r'"block_id"\s*:\s*"([a-z0-9_]+)"', text)
        if hit and hit.group(1) in block_ids:
            structures.append(json.loads(text)["id"])
    named.update(structures)

    layers = {}
    for path in SEATED_IN:
        if not path.exists():
            continue
        payload = load(path)
        rows = 0
        for key in ("runs", "openings", "edges", "records"):
            for entry in payload.get(key, []) or []:
                text = json.dumps(entry)
                hits = [h for p in patterns for h in p.findall(text)]
                if not hits:
                    continue
                rows += 1
                lots_reached.update(hits)
                named.update(re.findall(r"recon_1835_[a-z0-9_]+", text))
        if rows:
            layers[str(path.relative_to(ROOT))] = rows

    return {
        "structures_seated_by_block_id": len(structures),
        "structures_named_on_those_lots": len(named),
        "lots_reached_by_a_committed_record": len(lots_reached),
        "rows_seated_on_those_lots": layers,
    }


def derive() -> dict:
    streets = load(STREETS)
    sheet = load(SHEET)
    lots = load(LOTS)
    datum = load(DATUM)
    module = sheet["the_west_division_block"]

    residual_m = float(datum["derivation"]["residual_m"])
    module_ft = float(module["north_south_street_module_ft"])
    module_m = module_ft * FT_M

    # THE LINES ARE DERIVED, NEVER TYPED. The West Division's north-south streets are the
    # ones the sheet reading names as bounding its blocks, taken off the committed lot
    # layer's own `bounded_by` — so a sixth line seated tomorrow arrives here on its own,
    # and a line dropped disappears from the measurement rather than being asserted.
    west_grid = [b for b in lots["blocks"] if b.get("grid") == "west_division"]
    named_in_the_grid = {b["bounded_by"][side] for b in west_grid for side in ("west", "east")}
    by_id = {s["id"]: s for s in streets["streets"]}
    lines = sorted((by_id[i] for i in named_in_the_grid if i in by_id),
                   key=mean_east, reverse=True)

    line_rows = []
    for street in lines:
        sources = list(street.get("sources") or [])
        line_rows.append({
            "id": street["id"],
            "name_1835": street.get("name_1835"),
            "mean_east_local_m": round(mean_east(street), 2),
            "geometry_confidence": street.get("geometry_confidence"),
            "sources": sources,
            "what_places_this_line": {s: PLACES_A_LINE[s] for s in sources
                                      if s in PLACES_A_LINE},
            "what_only_attests_the_street": {s: ATTESTS_EXISTENCE_ONLY[s] for s in sources
                                             if s in ATTESTS_EXISTENCE_ONLY},
        })

    # 1. THE TWO CONTROLS.
    plat_places_nothing = module["confidence_note"]
    controls = {
        "the_survey_control": {
            "source_id": "osm_streets_2026",
            "lines_it_places": [r["id"] for r in line_rows
                                if "osm_streets_2026" in r["sources"]],
            "of": len(line_rows),
            "what_it_gives": "a position for each line, and no module",
            "carried_through": (f"data/datum.json, an affine fit of the 1834 sheets to "
                                f"modern ground at {residual_m} m RMS"),
        },
        "the_plat_control": {
            "source_id": "thompson_plat_1830",
            "lines_it_attests": [r["id"] for r in line_rows
                                 if "thompson_plat_1830" in r["sources"]],
            "of": len(line_rows),
            "the_module_ft": module_ft,
            "the_module_m": round(module_m, 3),
            "module_confidence": module["confidence"],
            "what_it_gives": "a module, a count and an arrangement, and no position",
            "in_its_own_words": plat_places_nothing,
        },
        "so": ("the two are not rivals for the same job. NOT ONE of these lines was ever "
               "placed by the plat — the sheet reading refuses to place anything, in its "
               "own confidence note — and the plat is the only thing that says the grid "
               "should be even. A ruling that 'the plat wins' therefore cannot mean "
               "'take the plat's positions', because it has none; it can only mean "
               "'impose the module on an anchor', which is priced below."),
    }

    # 2. THE INTERVALS, and 3. the residual each is tested against.
    intervals = []
    for west, east in zip(line_rows[1:], line_rows):
        gap_m = abs(east["mean_east_local_m"] - west["mean_east_local_m"])
        short_ft = module_ft - gap_m / FT_M
        blocks_here = [b["id"] for b in lots["blocks"]
                       if {b.get("bounded_by", {}).get("west"),
                           b.get("bounded_by", {}).get("east")} == {west["id"], east["id"]}]
        intervals.append({
            "east": east["id"],
            "west": west["id"],
            "committed_m": round(gap_m, 2),
            "committed_ft": round(gap_m / FT_M, 1),
            "the_plat_asks_ft": module_ft,
            "short_by_ft": round(short_ft, 1),
            "short_by_m": round(short_ft * FT_M, 2),
            "the_datum_residual_m": residual_m,
            "inside_the_datum_residual": abs(short_ft) * FT_M <= residual_m,
            "blocks_cut_between_these_lines": sorted(blocks_here),
        })

    inner = [i for i in intervals if i["short_by_ft"] > 0]
    outside = [i for i in inner if not i["inside_the_datum_residual"]]

    # 4. IS THE COMMITTED GRID A SCALED COPY OF THE PLAT, AND CAN ONE LINE CLOSE IT?
    #    Two separate answers, kept apart because the weaker one is the one most easily
    #    over-claimed. The SPREAD between intervals is compared with the datum residual,
    #    and the riverfront interval is held out of that comparison: its east line is the
    #    division's easternmost, seated off the committed waterline rather than off the
    #    grid, so it is not evidence about how the grid was cut. On the grid proper the
    #    spread does NOT outrun the residual, and this file says so rather than leaning
    #    on a figure the georeferencing could have produced. What does not depend on the
    #    residual at all is the COUNT: moving one centreline changes exactly the two
    #    intervals that touch it, and there are more short intervals than that.
    widths_ft = [i["committed_ft"] for i in intervals]
    spread_ft = max(widths_ft) - min(widths_ft)
    grid_proper = intervals[1:]
    grid_widths_ft = [i["committed_ft"] for i in grid_proper]
    grid_spread_ft = max(grid_widths_ft) - min(grid_widths_ft)
    scaled = {
        "all_intervals": {
            "the_widest_ft": max(widths_ft),
            "the_narrowest_ft": min(widths_ft),
            "spread_ft": round(spread_ft, 1),
            "spread_m": round(spread_ft * FT_M, 2),
            "spread_exceeds_the_residual": spread_ft * FT_M > residual_m,
        },
        "the_grid_proper": {
            "held_out": intervals[0]["east"],
            "why_held_out": ("the division's easternmost line is its riverfront street, "
                             "seated off the committed 1834 waterline rather than off "
                             "the grid, so the interval behind it is not evidence about "
                             "how the grid was cut"),
            "the_widest_ft": max(grid_widths_ft),
            "the_narrowest_ft": min(grid_widths_ft),
            "spread_ft": round(grid_spread_ft, 1),
            "spread_m": round(grid_spread_ft * FT_M, 2),
            "spread_exceeds_the_residual": grid_spread_ft * FT_M > residual_m,
            "so": ("inside the grid the intervals differ by LESS than the datum's own "
                   "residual, so their unevenness on its own does not refute a single "
                   "module — this file will not claim that it does."),
        },
        "the_datum_residual_m": residual_m,
        "but_one_line_cannot_close_it": {
            "intervals_short_of_the_plat": len([i for i in intervals if i["short_by_ft"] > 0]),
            "intervals_a_single_centreline_reaches": 2,
            "so": ("this does not depend on the residual at all. A centreline moved east "
                   "or west changes exactly the two intervals that touch it, and more "
                   "than two are short — so no one street move closes the gap, and the "
                   "repair is not 'move Clinton'. That is the arithmetic T-0444 and "
                   "T-0445 did not have when they closed on the single figure."),
        },
    }

    # The total, across the whole division — the figure that is hardest to explain away
    # as georeferencing, because the residual does not accumulate with the module.
    span_m = abs(line_rows[0]["mean_east_local_m"] - line_rows[-1]["mean_east_local_m"])
    span_asks_m = (len(line_rows) - 1) * module_m
    across = {
        "from": line_rows[0]["id"],
        "to": line_rows[-1]["id"],
        "intervals": len(line_rows) - 1,
        "committed_m": round(span_m, 2),
        "committed_ft": round(span_m / FT_M, 1),
        "the_plat_asks_m": round(span_asks_m, 2),
        "the_plat_asks_ft": round(span_asks_m / FT_M, 1),
        "short_by_m": round(span_asks_m - span_m, 2),
        "short_by_ft": round((span_asks_m - span_m) / FT_M, 1),
        "as_a_share_of_the_plat": round((span_asks_m - span_m) / span_asks_m, 4),
        "times_the_datum_residual": round((span_asks_m - span_m) / residual_m, 2),
        "so": ("the whole division is narrower than the plat draws it, by more than the "
               "datum's own uncertainty, so the difference is not the georeferencing "
               "alone even where a single interval's share of it is."),
    }
    # And again with the riverfront line held out, for the same reason it is held out of
    # the spread: it is seated on the waterline, not on the grid, and it is the one
    # interval that runs the other way. The grid proper is shorter still.
    grid_span_m = abs(line_rows[1]["mean_east_local_m"] - line_rows[-1]["mean_east_local_m"])
    grid_asks_m = (len(line_rows) - 2) * module_m
    across["the_grid_proper"] = {
        "from": line_rows[1]["id"],
        "to": line_rows[-1]["id"],
        "intervals": len(line_rows) - 2,
        "committed_ft": round(grid_span_m / FT_M, 1),
        "the_plat_asks_ft": round(grid_asks_m / FT_M, 1),
        "short_by_ft": round((grid_asks_m - grid_span_m) / FT_M, 1),
        "as_a_share_of_the_plat": round((grid_asks_m - grid_span_m) / grid_asks_m, 4),
        "times_the_datum_residual": round((grid_asks_m - grid_span_m) / residual_m, 2),
        "so": ("holding the riverfront line out does not soften the finding, it sharpens "
               "it: the three intervals the plat's module actually governs are shorter "
               "together than the four are."),
    }

    # 5. WHAT MOVES IF THE PLAT WINS. Two anchors, because the choice of anchor IS the
    #    question, and each is a different bill.
    anchors = []
    for anchor in (line_rows[0], line_rows[1]):
        index = line_rows.index(anchor)
        moves, total = [], 0.0
        for position, row in enumerate(line_rows):
            wanted = anchor["mean_east_local_m"] - (position - index) * module_m
            delta = wanted - row["mean_east_local_m"]
            total += abs(delta)
            moves.append({
                "id": row["id"],
                "committed_east_local_m": row["mean_east_local_m"],
                "the_plat_wants_east_local_m": round(wanted, 2),
                "moves_m": round(delta, 2),
                "moves_ft": round(delta / FT_M, 1),
                "direction": "east" if delta > 0.005 else ("west" if delta < -0.005 else "held"),
            })
        anchors.append({
            "anchor": anchor["id"],
            "why_this_anchor": (
                "the only line in the division with a PHYSICAL control — T-0445 seats its "
                "east kerb on the committed 1834 waterline, so it is the one line whose "
                "position is held by the modelled ground rather than by a modern street"
                if anchor["id"] == "west_water" else
                "the best-surviving line of the grid proper — it carries an 1891 "
                "municipal survey as well as both 1834 sheets and the modern street, "
                "which is more control than any other line here has"),
            "lines": moves,
            "total_absolute_movement_m": round(total, 2),
            "the_largest_single_move_m": round(max(abs(m["moves_m"]) for m in moves), 2),
        })

    # 6. WHAT IS SEATED ON THE SHORT SPACING TODAY.
    between = {i["id"] for i in line_rows}
    seated_blocks = {b["id"] for b in lots["blocks"]
                     if {b.get("bounded_by", {}).get("west"),
                         b.get("bounded_by", {}).get("east")} <= between
                     and b.get("bounded_by")}
    seated = seating_between(seated_blocks)
    seated.update({
        "blocks_cut_between_these_lines": len(seated_blocks),
        "blocks_by_grid": {
            grid: sum(1 for b in lots["blocks"]
                      if b["id"] in seated_blocks and b.get("grid") == grid)
            for grid in sorted({b.get("grid") for b in lots["blocks"]
                                if b["id"] in seated_blocks})},
        "blocks_with_their_lot_lines_cut": sum(
            1 for b in lots["blocks"] if b["id"] in seated_blocks and b.get("lots")),
        "lots_cut": sum(len(b.get("lots") or []) for b in lots["blocks"]
                        if b["id"] in seated_blocks),
        "so": ("every one of these blocks is bounded by two of the five lines, so its "
               "face, its area, its lot lines and everything seated against them are "
               "measured off the present spacing. Moving a line re-cuts the blocks on "
               "both sides of it, and this is the size of that."),
    })

    return {
        "_doc": (
            "T-1540. Which control seats the West Division's north-south lines, what the "
            "plat's 458 ft module would cost if it were imposed on them, and what is "
            "seated on the spacing they have today. NOTHING IS MOVED BY THE TOOL THAT "
            "WRITES THIS FILE: no centreline is edited, no block re-emitted, no record "
            "re-seated. It is a measurement, in the manner of "
            "tools/measure_west_division_module.py, and it exists because the owner "
            "ruled on 2026-09-21 that the successor to T-0444 and T-0445 must own the "
            "whole question rather than the one number those two closed on."),
        "tool": "tools/measure_west_division_spacing.py",
        "ticket": "T-1540",
        "generated_from": [str(p.relative_to(ROOT)) for p in (STREETS, SHEET, LOTS, DATUM)]
                          + ["data/structures/*.json"]
                          + [str(p.relative_to(ROOT)) for p in SEATED_IN],
        "the_lines": line_rows,
        "the_two_controls": controls,
        "the_intervals": intervals,
        "intervals_short_of_the_plat": len(inner),
        "intervals_short_by_more_than_the_datum_residual": len(outside),
        "across_the_division": across,
        "is_the_committed_grid_the_plat_module_rescaled": scaled,
        "what_moves_if_the_plat_wins": anchors,
        "what_is_seated_on_the_short_spacing_today": seated,
        "what_this_leaves_to_decide": {
            "the_question": (
                "the plat has no positions to take. Its own sheet reading says "
                "`documented` grades the figures and the counts and NOT any position, so "
                "'the plat wins' cannot mean 'adopt the plat's centrelines' — there are "
                "none. It can only mean imposing the module on an anchor, which replaces "
                "five lines seated on survey control with five lines derived from a "
                "figure that grades no position. That is a downgrade, and it is priced "
                "above rather than argued for here."),
            "what_the_record_supports": (
                "leaving the five lines where their own control puts them, publishing the "
                "disagreement with the plat on every interval instead of on one, and "
                "treating the 458 ft module as a figure the committed grid cannot carry "
                "at printed size — which is what tools/generate_plat_lots.py already does "
                "block by block in `closure_against_the_committed_lines`. On that reading "
                "the shortfall is recorded, not repaired, and T-1479's refusal 1 is "
                "PERMANENT rather than pending: no street move is coming that would let "
                "the printed module be seated at printed size."),
            "what_only_the_owner_can_settle": (
                "whether this reconstruction is a georeferenced dataset that records its "
                "disagreement with the plat, or a plat reconstruction that seats the "
                "draughtsman's module and accepts a warped fit to modern ground. That is "
                "a question about what the project IS, it costs 113 m or 165 m of street "
                "movement depending on the anchor, and it re-cuts everything counted in "
                "`what_is_seated_on_the_short_spacing_today`. It is asked on its own "
                "ticket rather than decided here."),
        },
        "what_this_does_not_say": (
            "that any of these five lines is in the wrong place. Each is seated on the "
            "best control its own record carries, and three of them were seated by "
            "tickets that said in writing what would move them. Nor does it say the "
            "plat's module is wrong: it closes to the foot on two readings that share no "
            "figure. What it says is that the two cannot both be true of the same ground, "
            "that the difference is bigger than the datum's own uncertainty and uneven "
            "across the division, and that choosing between them is a street move with a "
            "price — which is stated here so that it can be decided rather than inherited."),
    }


def report(d: dict) -> None:
    print("T-1540 — the West Division's north-south spacing: which control, and what the plat would cost\n")
    print("  the lines, east to west")
    for r in d["the_lines"]:
        placed = ", ".join(r["what_places_this_line"]) or "nothing"
        print(f"    {r['id']:12} E {r['mean_east_local_m']:9.2f} m  {r['geometry_confidence']:9}  placed by {placed}")
    c = d["the_two_controls"]
    print(f"\n  controls      survey places {len(c['the_survey_control']['lines_it_places'])} of "
          f"{c['the_survey_control']['of']} lines; the plat attests "
          f"{len(c['the_plat_control']['lines_it_attests'])} and places 0")
    print("\n  the intervals")
    for i in d["the_intervals"]:
        tag = "within the datum residual" if i["inside_the_datum_residual"] else "beyond the datum residual"
        word = "short" if i["short_by_ft"] > 0 else " over"
        print(f"    {i['east']:12}->{i['west']:12} {i['committed_ft']:7.1f} ft against "
              f"{i['the_plat_asks_ft']:.0f} — {word} {abs(i['short_by_ft']):5.1f} ft "
              f"({abs(i['short_by_m']):5.2f} m, {tag})")
    s = d["is_the_committed_grid_the_plat_module_rescaled"]
    g, o = s["the_grid_proper"], s["but_one_line_cannot_close_it"]
    print(f"\n  even?         inside the grid the intervals spread {g['spread_ft']} ft "
          f"({g['spread_m']} m) against a {s['the_datum_residual_m']} m residual — "
          f"{'beyond' if g['spread_exceeds_the_residual'] else 'not enough to refute one module'}")
    print(f"  one line?     no — {o['intervals_short_of_the_plat']} intervals are short and a "
          f"centreline reaches {o['intervals_a_single_centreline_reaches']}")
    a = d["across_the_division"]
    print(f"  across        {a['from']} to {a['to']}: {a['committed_ft']} ft against "
          f"{a['the_plat_asks_ft']} — short {a['short_by_ft']} ft "
          f"({a['times_the_datum_residual']}x the datum residual, {a['as_a_share_of_the_plat']:.1%})")
    gp = a["the_grid_proper"]
    print(f"                {gp['from']} to {gp['to']} alone: {gp['committed_ft']} ft against "
          f"{gp['the_plat_asks_ft']} — short {gp['short_by_ft']} ft "
          f"({gp['times_the_datum_residual']}x the residual, {gp['as_a_share_of_the_plat']:.1%})")
    print("\n  if the plat wins")
    for anchor in d["what_moves_if_the_plat_wins"]:
        print(f"    anchored on {anchor['anchor']:12} {anchor['total_absolute_movement_m']:7.2f} m of "
              f"total movement, largest single move {anchor['the_largest_single_move_m']} m")
    w = d["what_is_seated_on_the_short_spacing_today"]
    print(f"\n  seated on it  {w['blocks_cut_between_these_lines']} blocks "
          f"({w['blocks_with_their_lot_lines_cut']} with lot lines cut, {w['lots_cut']} lots), "
          f"{w['structures_named_on_those_lots']} structures, "
          f"{sum(w['rows_seated_on_those_lots'].values())} seated rows")


def write(d: dict) -> None:
    OUT.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


def check() -> int:
    if not OUT.exists():
        print(f"FAIL {OUT.relative_to(ROOT)} is not committed")
        return 1
    fresh = json.dumps(derive(), indent=1, ensure_ascii=False) + "\n"
    if fresh != OUT.read_text(encoding="utf-8"):
        print(f"FAIL {OUT.relative_to(ROOT)} does not re-derive from its inputs")
        return 1
    print(f"OK {OUT.relative_to(ROOT)} re-derives byte for byte")
    return 0


def self_test() -> int:
    d = derive()
    fail = []

    def ck(cond, msg):
        if not cond:
            fail.append(msg)

    # 1. The lines are the grid's own, derived off `bounded_by`, and every one of them
    #    resolves in the committed street file. A sixth seated tomorrow arrives on its own.
    ck(len(d["the_lines"]) >= 5,
       "the West Division's blocks must be bounded by at least the plat's five "
       "north-south streets")
    ck([r["id"] for r in d["the_lines"]]
       == sorted((r["id"] for r in d["the_lines"]),
                 key=lambda i: -next(x["mean_east_local_m"] for x in d["the_lines"]
                                     if x["id"] == i)),
       "the lines must come out east to west")

    # 2. The answer to the ticket's first question rests on this and nothing else: the
    #    plat has never placed one of these lines, and the survey has placed them all.
    c = d["the_two_controls"]
    ck(len(c["the_survey_control"]["lines_it_places"]) == len(d["the_lines"]),
       "every line must be placed by the modern survey — if one is not, the control is "
       "no longer uniform and the ruling below has to be re-argued for that line")
    ck(len(c["the_plat_control"]["lines_it_attests"]) == len(d["the_lines"]),
       "every line must carry the plat as a source, or the plat is not attesting this grid")
    ck("does not grade any position" in c["the_plat_control"]["in_its_own_words"],
       "the sheet reading must still refuse to place anything — this quotation is the "
       "whole reason the plat cannot be a position control, and it is read from the "
       "committed file rather than restated here")
    ck(c["the_plat_control"]["the_module_ft"] == 458,
       "the plat's north-south street module is 458 ft")

    # 3. The finding that makes this ticket different from T-0444 and T-0445: the gap is
    #    on EVERY interval of the grid proper, not on Clinton to Canal alone.
    inner = [i for i in d["the_intervals"] if i["short_by_ft"] > 0]
    ck(len(inner) >= 3,
       "at least three intervals must be short of the plat module — the day only one is, "
       "'move Clinton' becomes the shape of the repair again and this finding is stale")
    named = {(i["east"], i["west"]) for i in inner}
    ck(("canal", "clinton") in named,
       "the interval T-0444 reported and T-1479's refusals name must be among them")

    # 4. Not every gap is a defect, and not every gap is noise. Both halves must hold, or
    #    the datum test is decorative.
    ck(d["intervals_short_by_more_than_the_datum_residual"] >= 1,
       "at least one interval must be short by more than the datum's own residual, or "
       "the whole gap is inside the georeferencing and there is nothing to repair")
    ck(any(i["inside_the_datum_residual"] for i in inner),
       "at least one short interval must sit INSIDE the residual, or the measurement is "
       "not discriminating and every interval could be called a defect")

    # 5. WHAT REFUSES 'move Clinton and be done'. Two assertions, and the second is the
    #    one that must not be allowed to lean on the first. The spread INSIDE the grid is
    #    smaller than the datum residual, so it proves nothing on its own and this file
    #    is held to saying so; what does the work is the count, which no residual touches.
    s = d["is_the_committed_grid_the_plat_module_rescaled"]
    ck(not s["the_grid_proper"]["spread_exceeds_the_residual"],
       "the grid-proper spread must stay INSIDE the datum residual, or the file's own "
       "hedge is wrong and the unevenness has become evidence in its own right — which "
       "would be a stronger finding than this one is written to carry")
    o = s["but_one_line_cannot_close_it"]
    ck(o["intervals_short_of_the_plat"] > o["intervals_a_single_centreline_reaches"],
       "more intervals must be short than one centreline can reach, or a single street "
       "move closes the gap after all and T-0444's framing was right")

    # 6. The whole-division figure must outrun the residual, which is the thing that
    #    cannot be explained away interval by interval.
    a = d["across_the_division"]
    ck(a["short_by_m"] > a["intervals"] * 0 and a["times_the_datum_residual"] > 1,
       "the division must be short by more than one datum residual across its whole width")
    ck(a["intervals"] == len(d["the_lines"]) - 1,
       "the span must be measured across every interval the lines make")
    ck(a["the_grid_proper"]["times_the_datum_residual"]
       >= a["times_the_datum_residual"],
       "holding the riverfront interval out must not WEAKEN the finding — if it ever "
       "does, the shortfall is being carried by the one line that is not seated on the "
       "grid, and the reading has to be re-argued around that")

    # 7. The price. Both anchors must move something, and the anchor with the physical
    #    control must be the one that holds the waterline — if anchoring on Canal ever
    #    stopped moving West Water, the two bills would be the same and the choice free.
    anchors = {a["anchor"]: a for a in d["what_moves_if_the_plat_wins"]}
    ck(len(anchors) == 2, "two candidate anchors must be priced")
    for name, anchor in anchors.items():
        ck(any(m["direction"] == "held" for m in anchor["lines"]),
           f"anchored on {name}, the anchor itself must be held")
        ck(anchor["total_absolute_movement_m"] > 0,
           f"anchored on {name}, the plat must move at least one line")
    if "west_water" in anchors and "canal" in anchors:
        moved = next(m for m in anchors["canal"]["lines"] if m["id"] == "west_water")
        ck(abs(moved["moves_m"]) > 0,
           "anchoring on canal must move west_water, whose east kerb is committed to the "
           "1834 waterline — that is the cost that makes the anchor a real choice")

    # 8. What is seated on the present spacing. If it ever fell to nothing the street
    #    move would be cheap and this measurement would not be worth gating.
    w = d["what_is_seated_on_the_short_spacing_today"]
    ck(w["blocks_cut_between_these_lines"] >= 11,
       "at least eleven blocks stand between these five lines")
    ck(w["lots_cut"] >= 46, "at least forty-six lots are cut inside them")
    ck(w["structures_named_on_those_lots"] > 0 and w["rows_seated_on_those_lots"],
       "structures and seated rows must stand on those lots, or moving a line costs "
       "nothing and the refusal in T-1479 is guarding a cheap move")

    if fail:
        for m in fail:
            print(f"  FAIL {m}")
        print(f"SELF-TEST FAIL — {len(fail)} case(s)")
        return 1
    print("SELF-TEST PASS — the derived lines, the two controls, the gap on every "
          "interval, the datum test discriminating both ways, the spread held inside "
          "the residual, the count that closes it anyway, the whole-division figure "
          "with and without the riverfront, both anchors priced and the seating counted")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    if "--check" in sys.argv:
        raise SystemExit(check())
    data = derive()
    report(data)
    if "--write" in sys.argv:
        write(data)
