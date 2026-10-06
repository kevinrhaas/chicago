#!/usr/bin/env python3
"""What moving blocks 28 and 45 onto the West Division grid would cost, and what stops it (T-1479).

T-1455 cut the West Division on its own module — two columns of 180 ft lots backing
onto an 18 ft north-south alley, five rows of 75 3/5 ft — and left two cells behind.
`blk_lake_clinton` (plat block 28) and `blk_randolph_clinton` (block 45) stand between
Clinton and Canal, which is West Division ground, but they were already emitted by the
Original Town's grid on the SOUTH Division module: four lots to a face with an
east-west alley. They are carried in that grid's omissions with `already_derived_as`
and a reason, and the reason ends "that is its own ticket rather than this cell's".

This is that ticket's measurement. NOTHING MOVES HERE. No lot line is cut, no record
is re-seated, no block is re-emitted — this module writes numbers, exactly as
`tools/measure_west_division_module.py` did for T-0444, and for the same reason: the
move is refused by committed arithmetic, and a refusal in this project carries a
figure.

THE SHEET AND THE LAYER DISAGREE, AND THE SHEET IS `documented`. On each of these two
blocks `data/traces/thompson_west_division_lots.json` counts TEN lot numerals in the
West Division's own arrangement — 2|1, 3|4, 6|5, 7|8, 10|9, north to south, two columns
by five rows. The committed grid cuts EIGHT, four to a face, on the module of the other
division. That gap is the ticket, and it is not in dispute.

TWO INDEPENDENT REFUSALS STOP THE RE-CUT, and they matter separately because closing
one does not close the other.

1. **The module does not fit the committed lines.** The West Division block closes at
   378 ft square — 180 + 18 + 180 east to west, and 5 x 75 3/5 north to south, two sums
   sharing no figure and meeting to the foot. The committed street lines give these two
   blocks 315.2 ft and 326.1 ft of face. The two lot columns alone want 360 ft, so the
   arrangement does not fit before the alley is cut. What is short is this project's
   West Division street spacing — Clinton to Canal committed at 367.9 ft against the
   plat's own 458 ft module — and not the module, which is printed and closes.

2. **Neither block prints a dimension, and T-1455's grid WITHHOLDS such a block.** Both
   entries in the sheet reading carry `refused: "Both dimensions; no marginal figures."`
   Under the West Division grid's own rule a block with no figure of its own keeps its
   boundary, its numeral, its lot COUNT and its ground, and its lot LINES are withheld.
   So "moving these two onto that grid" does not produce ten lots. It produces none —
   and it would take the eight they have away from the records standing on them.

WHICH IS THE TICKET'S OWN FIRST QUESTION: what is a structure seated on a withdrawn lot
seated on? Today there is no answer, and the reason is measured here rather than
assumed: of the 35 blocks whose lot lines are withheld, NOT ONE carries a structure.
The case has never arisen, so no rule was ever written for it. `blk_randolph_clinton`
would be the first, and it would not arrive alone — see the seating counted below.

THE PRECONDITION IS OWNED AGAIN, AND BY T-1540. Both refusals name the street spacing.
Until 2026-09-24 they named T-0445 as the ticket that would move it — T-0444 reported the
gap, T-0445 was to close it, both closed, and the spacing stayed at 367.9 ft, so the
refusal text pointed a reader forward at work that had already been done. The owner ruled
on 2026-09-21 that a successor must own the whole question rather than the one number, and
T-1540 is that successor: `tools/measure_west_division_spacing.py` measures the gap on
EVERY interval of the West Division grid, not on this one, and finds that no single
centreline moved can close three of them, and that the plat gives a module and no
positions to take. T-1540 LANDED on 2026-09-24 (PR #25) and this precondition went red
rather than stale, which is what it was wired to do. The spacing question is answered, so
the pointer moves on to T-1479 — the ticket that re-cuts blocks 28 and 45 and was blocked
on exactly this — which the tickets repo unblocked when T-1540 landed. The guard re-arms
on it: the day T-1479 lands while this precondition still stands, this goes red again.

    tools/measure_west_grid_migration.py              -> print the derivation
    tools/measure_west_grid_migration.py --check      -> re-derive, byte for byte
    tools/measure_west_grid_migration.py --self-test  -> the assertions
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "traces" / "west_grid_migration_order.json"
FT_M = 0.3048

# The files this reading stands on. Every figure below comes out of one of them; none is
# typed in here, which is what keeps this a derivation rather than a memo with numbers.
LOTS = DATA / "traces" / "vectors" / "thompson_lots.json"
SHEET = DATA / "traces" / "thompson_west_division_lots.json"
STREETS = DATA / "streets" / "1835.json"

# The layers a lot id reaches. A block whose lot lines are withdrawn strands whatever is
# seated against them, and these are the committed files that do the seating.
SEATED_IN = (
    DATA / "enclosures" / "town_lot_line_rails.json",
    DATA / "enclosures" / "town_lot_line_boards.json",
    DATA / "enclosures" / "town_lot_line_pickets.json",
    DATA / "frontage" / "town_street_edge.json",
)

# The tickets the two refusals name as owning the street move, and which this module
# checks the state of rather than trusting the prose. Read out of tickets/, not asserted.
# The first two REPORTED and closed; the third is the successor the owner ruled must own
# the whole question, and it is the one that has to still be unfinished for this
# precondition to hold.
NAMED_BY_THE_REFUSAL = ("T-0444", "T-0445")
# T-1733. The ruling landed and T-1479 split, so this names WHAT IS STILL OWED and
# nothing else — the cell that could not be transposed at once. It deliberately does not
# name the ticket that cut the other cell: a pointer that records finished work as live
# work goes stale the moment that ticket closes, and the gate then goes red for whoever
# merges next (`ticket.mjs done` refuses a close that would leave one behind).
#
# T-1734 EMPTIED IT, which is the point of it being a list and not a sentence. Both cells
# both grids reach are now transposed — 28 by T-1733 and 45 by T-1734, which re-argued the
# deal that held it — so there is nothing left for this pointer to name. It stays here,
# empty, rather than being deleted: the precondition below is NOT retired by the move, and
# the day the committed Clinton-to-Canal spacing reaches the plat's own figure this
# reading has to be re-made by somebody. An empty tuple says "nobody owes this"; no tuple
# at all would say nobody ever could.
OWNS_THE_MOVE: tuple[str, ...] = ()
# Which blocks a reconstruction parcel has dealt roofs onto. This is what decides, in
# tools/generate_plat_lots.py, whether a cell may be transposed — so it is read here too,
# out of the same committed file, rather than the block ids being named in either place.
PARCELS = DATA / "reconstruction" / "1835_platted_block_parcels.json"
WEST_MODULE = "west_division_thompson_1830"
# The one cell that prints a depth of its own: plat block 50 reads lots 180 ft deep and
# withholds the frontage (T-2148), so refusal 2 holds for it on the frontage alone.
PRINTS_ITS_DEPTH = {50: 180}


def load(path: pathlib.Path):
    return json.loads(path.read_text())


def ticket_state(ticket_id: str) -> str | None:
    """A named ticket's state, off its own file's front matter."""
    for path in sorted((ROOT / "tickets").rglob(f"{ticket_id}-*.md")):
        head = path.read_text().split("---")[1]
        for line in head.splitlines():
            if line.startswith("state:"):
                return line.split(":", 1)[1].strip()
    return None


# The states a ticket passes through WHILE IT IS STILL OWED. The trace records only whether
# the work is owed, not where in the workflow it sits: a run that claims, reviews or blocks
# the ticket changes nothing this reading measures, and recording the raw state turned the
# gate red for every open pull request the moment T-1734 was claimed (2026-09-28).
# T-1734 CLOSED THE SAME DAY and `OWNS_THE_MOVE` is now empty, so nothing routes through
# here for the move any more. It still governs `NAMED_BY_THE_REFUSAL`, and it stays: the
# next ticket named on this reading gets the fix already made rather than the bug again.
STILL_OWED = {"open", "claimed", "review", "blocked-tech"}


def ticket_standing(ticket_id: str) -> str | None:
    """What the committed trace records: `open` for any in-flight state, else the state."""
    state = ticket_state(ticket_id)
    return "open" if state in STILL_OWED else state


def street_spacing_ft(streets: dict, west_id: str, east_id: str) -> float:
    """The committed centreline spacing, the same mean-easting difference the grid uses.

    `generate_plat_lots.module_for` computes its refusal against exactly this figure, so
    it is re-derived here from the same file rather than carried across — a centreline
    that moved would change both, and the check below would see it.
    """
    means = {}
    for street in streets["streets"]:
        points = [(float(e), float(n)) for e, n in street["path_local_enu_m"]]
        means[street["id"]] = sum(p[0] for p in points) / len(points)
    return abs(means[west_id] - means[east_id]) / FT_M


def seating(block_id: str) -> dict:
    """Everything committed that is seated on this block, by block id and by lot id.

    Counted rather than listed wherever the list would be long: the point of the figure
    is the SIZE of the re-seat, and a count that moves is a re-seat that has changed.
    """
    lot_pattern = re.compile(rf"{block_id}_lot\d+")
    structures, lots_reached = [], set()
    for path in sorted((DATA / "structures").glob("*.json")):
        text = path.read_text()
        if re.search(rf'"block_id"\s*:\s*"{block_id}"', text):
            structures.append(json.loads(text)["id"])

    layers = {}
    named_structures = set(structures)
    for path in SEATED_IN:
        if not path.exists():
            continue
        payload = load(path)
        rows = 0
        for key in ("runs", "openings", "edges", "records"):
            for entry in payload.get(key, []) or []:
                text = json.dumps(entry)
                hits = lot_pattern.findall(text)
                if not hits:
                    continue
                rows += 1
                lots_reached.update(hits)
                named_structures.update(re.findall(r"recon_1835_[a-z0-9_]+", text))
        if rows:
            layers[str(path.relative_to(ROOT))] = rows

    return {
        "structures_seated_by_block_id": sorted(structures),
        "lots_reached_by_a_committed_record": sorted(lots_reached),
        "rows_seated_on_those_lots": layers,
        "structures_named_on_those_lots": sorted(named_structures),
    }


def re_argued_deal(block_id: str, twin: dict, parcels: dict, streets: dict) -> dict:
    """The deal a transposed block carries, read against the faces it now has.

    T-1734, and it is the other half of "recording the move". `seating_by_lot` above says
    which lot each record landed on, which is true of any re-cut. This says what the
    RE-ARGUMENT did, which only a block carrying a dealt parcel has: which face each roof
    fronts now, what that face is graded in the committed street hierarchy, and whether
    the ranking the old deal was argued on survived the ninety-degree turn.

    NOTHING HERE IS A BEFORE-AND-AFTER. A distance a roof moved could not be re-derived
    from committed state a day later — only from a diff — and a figure in a derived file
    that its own tool cannot recompute is the thing `--check` exists to refuse. So this
    reads the deal and the grid as they now stand, and the move itself is recorded where a
    move belongs: in the commit, the changelog and the ticket.
    """
    traffic = {street["id"]: street.get("traffic") for street in streets["streets"]}
    bounded = twin["bounded_by"]
    pair = [bounded["west"], bounded["east"]]
    removed = [bounded["north"], bounded["south"]]
    lots = twin.get("lots") or []
    rank = {"principal": 3, "ordinary": 2, "light": 1}
    slots = []
    for parcel in parcels["blocks"]:
        if parcel["block_id"] != block_id:
            continue
        for slot in parcel["slots"]:
            index = slot.get("lot")
            lot = lots[index] if isinstance(index, int) and index < len(lots) else None
            slots.append({
                "family": slot["family"],
                "inventory_class": slot["inventory_class"],
                "lot_index": index,
                "plat_lot_number": lot.get("plat_lot_number") if lot else None,
                "column": lot.get("column") if lot else None,
                "row": lot.get("row") if lot else None,
                "stands_on": slot["stands_on"],
                "fronts": slot.get("fronts"),
                "that_face_is_graded": traffic.get(slot.get("fronts")),
            })
    better = max(pair, key=lambda s: rank.get(traffic.get(s), -1))
    principal = [s for s in slots if s["inventory_class"] == "principal_functional"]
    return {
        "the_faces_the_transpose_removed": {
            street: traffic.get(street) for street in removed},
        "the_faces_it_gave": {street: traffic.get(street) for street in pair},
        "the_better_of_the_new_pair": better,
        "no_slot_fronts_a_face_the_transpose_removed":
            not [s for s in slots if s["fronts"] in removed],
        "principal_roofs_on_the_better_face": sorted(
            s["family"] for s in principal if s["fronts"] == better),
        "principal_roofs_on_the_lighter_face": sorted(
            s["family"] for s in principal if s["fronts"] != better),
        "so": ("the rule the first deal was argued on — the better dwellings take the "
               "better street of the block's pair, by the grading in "
               "data/streets/1835.json — is re-applied to the pair the transpose gives. "
               "It is stated as a re-application and not as a confirmation: the ranking "
               "of the new pair is read here, and had it come out the other way about the "
               "four roofs would have crossed the alley."),
        "slots": slots,
    }


def seating_by_lot(block_id: str, twin: dict) -> list[dict]:
    """Which committed record holds which lot of this block, lot by lot.

    T-1733, and this is the "recording the move" half of the owner's ruling. `seating`
    above counts the whole block, which is the size of a re-seat; this says WHERE each
    record landed, which is the re-seat itself. Every figure is read off the committed
    layers as they now stand — a lot id in a run, an opening or a street edge — so the
    record cannot drift from the layer it describes.
    """
    rows: dict[str, dict] = {}
    for index, lot in enumerate(twin.get("lots") or []):
        rows[f"{block_id}_lot{index}"] = {
            "lot_id": f"{block_id}_lot{index}",
            "plat_lot_number": lot.get("plat_lot_number"),
            "plat_lot_confidence": lot.get("plat_lot_confidence"),
            "column": lot.get("column"),
            "row": lot.get("row"),
            "records": [],
            "structures": [],
        }
    for path in SEATED_IN:
        if not path.exists():
            continue
        payload = load(path)
        for key in ("runs", "openings", "edges", "records"):
            for entry in payload.get(key, []) or []:
                text = json.dumps(entry)
                for lot_id in re.findall(rf"{block_id}_lot\d+", text):
                    if lot_id not in rows:
                        continue
                    rows[lot_id]["records"].append(
                        f"{path.relative_to(ROOT)}:{entry.get('id')}")
                    for found in re.findall(r"recon_1835_[a-z0-9_]+", text):
                        if found not in rows[lot_id]["structures"]:
                            rows[lot_id]["structures"].append(found)
    for row in rows.values():
        row["records"] = sorted(set(row["records"]))
        row["structures"] = sorted(row["structures"])
    return [rows[k] for k in sorted(rows, key=lambda k: int(k.rsplit("lot", 1)[1]))]


def derive() -> dict:
    lots = load(LOTS)
    sheet = load(SHEET)
    streets = load(STREETS)
    module = sheet["the_west_division_block"]

    blocks = {b["id"]: b for b in lots["blocks"]}
    sheet_by_number = {b["plat_block_number"]: b for b in sheet["blocks"]}
    parcels = load(PARCELS)
    dealt: dict[str, list[str]] = {}
    for parcel in parcels["blocks"]:
        dealt.setdefault(parcel["block_id"], []).append(parcel["programme_phase"])

    # The pair is DERIVED from the grid's own omissions, never typed. An omission carrying
    # `already_derived_as` is precisely a cell the West Division grid gave up to the
    # Original Town's, which is the population this ticket is about — so a third one
    # appearing would arrive here on its own.
    carried = [o for o in lots["omitted"] if o.get("already_derived_as")]

    module_ew_ft = float(module["block_east_west_ft"])
    columns_ft = 2 * float(module["lot_depth_ft"])
    frontage_ft = float(module["lot_frontage_ft"])

    withheld_blocks = [b["id"] for b in lots["blocks"] if not b.get("lots")]
    withheld_carrying_a_structure = [
        b for b in withheld_blocks
        if seating(b)["structures_seated_by_block_id"]
        or seating(b)["lots_reached_by_a_committed_record"]
    ]

    rows = []
    for omission in sorted(carried, key=lambda o: o["plat_block_number"]["number"]):
        number = omission["plat_block_number"]["number"]
        twin_id = omission["already_derived_as"]
        twin = blocks[twin_id]
        read = sheet_by_number[number]
        face_ft = twin["frontage_m"] / FT_M
        depth_ft = twin["depth_m"] / FT_M
        derived_lots = len(twin.get("lots") or [])
        seated = seating(twin_id)
        rows.append({
            "plat_block_number": number,
            "omitted_from_the_west_grid_as": omission["id"],
            "derived_by_the_original_town_grid_as": twin_id,
            "bounded_by": omission["bounded_by"],
            "what_the_sheet_reads": {
                "lot_count": read["lot_count"],
                "arrangement": module["shape"].split(",")[0].strip().lower(),
                "lot_numerals_north_to_south": read["lot_numerals_north_to_south"],
                "rows": len(read["lot_numerals_north_to_south"]),
                "columns": len(read["lot_numerals_north_to_south"][0]),
                "region_on_the_sheet": read["region"],
                "dimensions_refused": read["refused"],
                "confidence": omission["plat_block_number"]["confidence"],
            },
            "what_the_layer_cuts": {
                "module": twin["module"]["module"],
                "lot_count": derived_lots,
                # A South Division cut states its lot frontage and its alley axis as
                # figures; the West Division's states the ARRANGEMENT, because the figure
                # it prints is not what is seated (T-1733). Each is read from the module
                # record the grid actually wrote, so this row says what the grid did
                # rather than what one of the two modules happens to be shaped like.
                "lot_frontage_ft": twin["module"].get("lot_frontage_ft"),
                "alley_runs": twin["module"].get(
                    "alley_runs", twin["module"].get("arrangement")),
            },
            "the_gap": (
                f"the sheet counts {read['lot_count']} lots in "
                f"{len(read['lot_numerals_north_to_south'])} rows of "
                f"{len(read['lot_numerals_north_to_south'][0])}; the layer cuts "
                f"{derived_lots} on the {twin['module']['module']} module, "
                f"{read['lot_count'] - derived_lots} fewer and in the other arrangement"),
            "refusal_1_the_module_does_not_fit": {
                "the_committed_face_ft": round(face_ft, 1),
                "the_committed_depth_ft": round(depth_ft, 1),
                "the_two_lot_columns_want_ft": round(columns_ft, 1),
                "the_block_wants_ft": module_ew_ft,
                "short_east_west_by_ft": round(module_ew_ft - face_ft, 1),
                "rows_the_depth_divides_into": round(depth_ft / frontage_ft, 2),
                "so": ("the arrangement does not fit before the alley is cut, and the "
                       "depth does not divide into whole lots of the printed frontage"),
            },
            "refusal_2_this_block_prints_no_dimension": {
                "refused_on_the_sheet": read["refused"],
                "lot_depth_ft": read["lot_depth_ft"],
                "lot_frontage_ft": read["lot_frontage_ft"],
                "so": ("under the West Division grid's own rule a block with no figure "
                       "of its own keeps its boundary, its numeral, its lot count and "
                       "its ground, and its lot LINES are withheld — so moving this "
                       "block onto that grid cuts no lots at all"),
            },
            "the_committed_seating_on_this_block": seated,
        })
        # T-1733, the owner's ruling of 2026-09-23 on T-1479 (option a of three): the
        # division's module MAY cut a cell printing no lot figures of its own, at
        # `inferred`, with every record on it re-seated onto the nearest new lot. Which
        # cell that happened to is read off the LAYER — a cell cut on the West Division's
        # module was transposed, one still on the South's was not — so this record cannot
        # claim a move the grid did not make.
        transposed = twin["module"]["module"] == WEST_MODULE
        row = rows[-1]
        row["the_ruling"] = {
            "ticket": "T-1479",
            "owner": "2026-09-23, via Manager",
            "answer": ("(a) Yes: cut with the documented module (inferred tier) and "
                       "re-seat each structure on the new lot nearest its present spot, "
                       "recording the move"),
            "so_neither_refusal_above_holds_a_cell_shut_any_more": (
                "both are still TRUE as arithmetic and both are re-derived above at the "
                "moment this file is written; what the ruling changed is what is done "
                "about them. An empty block was judged a worse answer than a block cut at "
                "a stated inference."),
        }
        if transposed:
            row["state"] = "transposed"
            row["the_gap_is_closed"] = (
                f"the sheet counts {read['lot_count']} lots in "
                f"{len(read['lot_numerals_north_to_south'])} rows of "
                f"{len(read['lot_numerals_north_to_south'][0])} and the layer now cuts "
                f"{derived_lots} on the {twin['module']['module']} module, in that "
                "arrangement, with every numeral read at its own position")
            row["what_the_cut_is_graded"] = {
                "the_module_carry": twin["module"].get("confidence"),
                "the_numerals": sorted({l.get("plat_lot_confidence")
                                        for l in twin.get("lots") or []}),
                "why_not_documented": (
                    "this block prints no dimension of its own, so the module that cuts it "
                    "comes from its tier. The numerals are ink in this block at their own "
                    "positions and are graded where they are read; the carry of the module "
                    "onto the block is an inference and is graded as one."),
            }
            # WHETHER A RE-CUT MOVES ANYTHING IS A PROPERTY OF THE BLOCK, NOT OF THE
            # RULING (T-1734). Block 28 carried no dealt parcel, so no position on it was
            # derived from a lot line and the re-cut moved no record a metre; block 45
            # carries one, and a dealt roof's position IS derived from its lot — the
            # generator reads the lot polygon and sets the roof off its street edge — so
            # re-cutting the block re-derives every one of them. Both sentences were
            # written here as one when only the first case existed. They are read off the
            # parcel file now, because a third cell will be one or the other and nobody
            # should have to guess which sentence applies.
            deal_here = sorted(dealt.get(twin_id, []))
            row["the_re_seat"] = {
                "rule": ("every committed record on this block holds the lot it now stands "
                         "on — the lot nearest its present spot, which after a re-cut that "
                         "fills the same block boundary is the lot it lies in."),
                "carries_a_dealt_parcel": deal_here,
                "so_the_positions_are": (
                    "RE-DERIVED. A dealt roof stands where its parcel's slot puts it off "
                    "its own lot's street or alley edge, so every position on this block "
                    "comes out of a lot line and the re-cut re-computes all of them; the "
                    "deal that decides WHICH lot had to be re-argued first, which is what "
                    "held this block while its twin moved. The meshes do not change and "
                    "nothing is rebaked even so: a re-seat moves a record's position and "
                    "rotation and leaves its footprint, form and asset exactly as they "
                    "were." if deal_here else
                    "UNCHANGED. The block carries no dealt parcel, so no position on it is "
                    "derived from a lot line: no record moved a metre and nothing was "
                    "rebaked."),
                "every_seating_on_this_block_moved_lot": True,
                "why": ("the transpose shares no line with the cut it replaced. The alley "
                        "turned from east-west to north-south, the faces turned through "
                        "ninety degrees, and the lot count went from eight to "
                        f"{derived_lots} — so no lot of the old cut survives to be kept."),
                "lot_by_lot": seating_by_lot(twin_id, twin),
            }
            if deal_here:
                row["the_deal_re_argued"] = re_argued_deal(
                    twin_id, twin, parcels, streets)
        else:
            row["state"] = "held"
            row["what_holds_this_block_now"] = {
                "not_the_arithmetic": (
                    "the ruling overrode both refusals above, and it landed: this block's "
                    "twin stands transposed on this same grid."),
                "its_own_deal": sorted(dealt.get(twin_id, [])),
                "why_that_holds_it": (
                    "the transpose turns the block through ninety degrees and its lots stop "
                    "fronting the east-west streets. A parcel that argued WHICH FAMILY "
                    "TAKES WHICH FACE argued it against faces the transpose removes, so "
                    "transposing this block silently would leave its dealt roofs standing "
                    "on an argument about ground that no longer exists."),
                "owed_by": "T-1734",
                "and_what_a_withheld_cut_would_strand_is_still_the_size_of_it": (
                    f"{len(seated['structures_named_on_those_lots'])} structure(s), "
                    f"{sum(seated['rows_seated_on_those_lots'].values())} seated row(s) "
                    f"across {len(seated['lots_reached_by_a_committed_record'])} lot(s)"),
            }

    spacing_ft = street_spacing_ft(streets, "clinton", "canal")
    module_street_ft = float(module["north_south_street_module_ft"])

    return {
        "_doc": (
            "T-1733, on the ruling T-1479 asked for. What moving plat blocks 28 and 45 "
            "onto the West Division grid cost, what the ruling overrode to do it, and "
            "which of the two moved. NOTHING IS MOVED BY THE TOOL THAT WRITES THIS FILE: "
            "it reads the committed grid and says what the grid did. Until 2026-09-28 it "
            "was a refusal with figures, and the figures are all still here — both "
            "refusals are re-derived on the committed lines every time this runs, because "
            "a ruling that overrides a refusal does not make the refusal's arithmetic "
            "wrong. BOTH blocks are transposed since 2026-09-28 — 28 by T-1733, which "
            "carried no deal to re-argue, and 45 by T-1734, which re-argued the one that "
            "held it onto Clinton and Canal — and which state each block is in comes out "
            "of committed files rather than out of prose, so a block going back to held "
            "would show here without this file being edited."),
        "tool": "tools/measure_west_grid_migration.py",
        "ticket": "T-1733",
        "parent_ticket": "T-1479",
        "successor": None,
        "both_cells_moved_by": ["T-1733", "T-1734"],
        "generated_from": [
            str(LOTS.relative_to(ROOT)),
            str(SHEET.relative_to(ROOT)),
            str(STREETS.relative_to(ROOT)),
            "data/structures/*.json",
        ] + [str(p.relative_to(ROOT)) for p in SEATED_IN],
        "blocks": rows,
        "the_precondition": {
            "committed_clinton_to_canal_ft": round(spacing_ft, 1),
            "the_plat_street_module_ft": module_street_ft,
            "short_by_ft": round(module_street_ft - spacing_ft, 1),
            "so": ("the West Division module cannot be seated on these blocks AT ITS "
                   "PRINTED SIZE until the committed Clinton and Canal centrelines carry "
                   "the plat's own spacing. That is a street move, which this ticket may "
                   "not make."),
            "reported_it_and_closed": {
                t: ticket_standing(t) for t in NAMED_BY_THE_REFUSAL},
            "owns_what_is_left": {t: ticket_standing(t) for t in OWNS_THE_MOVE},
            "and_the_finding": (
                "the first two tickets the refusal pointed forward to are CLOSED and the "
                "spacing is still short, so for a while the move was unowned and the "
                "prose in tools/generate_plat_lots.py sent a reader at work already done. "
                "T-1540 was the successor the owner ruled on 2026-09-21 must own the "
                "whole question — tools/measure_west_division_spacing.py is its "
                "measurement, and it finds the shortfall on every interval of the grid "
                "rather than on this one, against a plat that gives a module and no "
                "positions. It landed on 2026-09-24 and this block went red rather than "
                "stale, which is what it is for. And then the answer came: the owner ruled "
                "on 2026-09-23 that the module may cut a block printing no figures of its "
                "own at `inferred` without the spacing moving at all, so the re-cut no "
                "longer waits on this precondition — T-1479 split into the cell that could "
                "be transposed at once (T-1733) and the cell that could not, because its "
                "own deal had argued its roofs onto the faces the transpose removes. "
                "T-1734 re-argued that deal on 2026-09-28 and the second cell moved, so "
                "the MOVE IS DONE and this pointer names nobody. THE PRECONDITION IS NOT "
                "RETIRED BY THAT. It is the reason the printed module is still not seated "
                "at its printed size on either block, and the day Clinton and Canal reach "
                "the plat's 458 ft the shortfall figure above goes to zero and this "
                "reading has to be re-made."),
        },
        "the_first_question": {
            "asked_by_the_ticket": (
                "what is a structure seated on a withdrawn lot seated on?"),
            "blocks_whose_lot_lines_are_withheld": len(withheld_blocks),
            "of_those_carrying_a_committed_seating": len(withheld_carrying_a_structure),
            "so": ("the case has never arisen anywhere in town, which is why no rule was "
                   "ever written for it — and it has still never arisen, because the "
                   "ruling answered the question by never letting it arise. Withdrawing "
                   "these blocks' lot lines would have raised it against real seating; "
                   "re-cutting them raises it against nothing."),
            "answered_by": {
                "ticket": "T-1479",
                "owner": "2026-09-23",
                "the_answer": (
                    "a structure on a withdrawn lot is not a case this project has to "
                    "rule on, because the ground is never withdrawn. The lines are "
                    "RE-CUT rather than withheld, and every record standing on them is "
                    "re-seated onto the lot nearest where it already stands — which, for "
                    "a re-cut that fills the same block boundary, is the lot it lies in. "
                    "The count below is the check that the answer held: if a withheld "
                    "block ever carries a seating, the question arose after all."),
            },
        },
        "what_this_does_not_say": (
            "that the layer is wrong about the GROUND. Both blocks' boundaries, faces "
            "and areas are cut from committed centrelines and are not in question here; "
            "what the sheet contradicts is the lot ARRANGEMENT inside them. Nor does it "
            "say the sheet's ten numerals should be seated at the plat's printed size on "
            "this project's short spacing — that would put lot lines outside the block."),
    }


def report(d: dict) -> None:
    print("T-1733 and T-1734 — blocks 28 and 45 onto the West Division grid: what each "
          "move cost\n")
    for b in d["blocks"]:
        print(f"  plat block {b['plat_block_number']}  "
              f"{b['derived_by_the_original_town_grid_as']}  [{b['state'].upper()}]")
        r1 = b["refusal_1_the_module_does_not_fit"]
        print(f"    refusal 1  face {r1['the_committed_face_ft']} ft against the "
              f"{r1['the_block_wants_ft']:.0f} ft block — short {r1['short_east_west_by_ft']} ft; "
              f"the depth divides into {r1['rows_the_depth_divides_into']} lots")
        print(f"    refusal 2  {b['refusal_2_this_block_prints_no_dimension']['refused_on_the_sheet']} "
              "-> the grid would withhold its lot lines rather than cut them")
        print("    ruling     overrode both, 2026-09-23 — cut at `inferred`, re-seat onto "
              "the nearest new lot")
        if b["state"] == "transposed":
            print(f"    cut        {b['the_gap_is_closed']}")
            seat = b["the_re_seat"]
            held = [l for l in seat["lot_by_lot"] if l["records"]]
            print(f"    re-seated  {len(held)} of {len(seat['lot_by_lot'])} lots carry a "
                  f"committed record; "
                  f"{sum(len(l['records']) for l in seat['lot_by_lot'])} row(s), "
                  f"{len(set(x for l in seat['lot_by_lot'] for x in l['structures']))} "
                  f"structure(s); positions {seat['so_the_positions_are'].split('.')[0]}")
            deal = b.get("the_deal_re_argued")
            if deal:
                print(f"    re-argued  {', '.join(seat['carries_a_dealt_parcel'])} onto "
                      f"{' and '.join(deal['the_faces_it_gave'])}; the better face "
                      f"({deal['the_better_of_the_new_pair']}) takes "
                      f"{', '.join(deal['principal_roofs_on_the_better_face'])} and the "
                      f"lighter takes "
                      f"{', '.join(deal['principal_roofs_on_the_lighter_face'])}")
        else:
            w = b["what_holds_this_block_now"]
            print(f"    held       {b['the_gap']}")
            print(f"               by its own deal ({', '.join(w['its_own_deal'])}) "
                  f"-> {w['owed_by']}; "
                  f"{w['and_what_a_withheld_cut_would_strand_is_still_the_size_of_it']}")
    p = d["the_precondition"]
    print(f"\n  precondition  Clinton to Canal committed at {p['committed_clinton_to_canal_ft']} ft "
          f"against the plat's {p['the_plat_street_module_ft']:.0f} ft — short {p['short_by_ft']} ft")
    left = ", ".join(f"{k} is {v}" for k, v in p["owns_what_is_left"].items())
    print(f"                {', '.join(f'{k} is {v}' for k, v in p['reported_it_and_closed'].items())}"
          f"; what is left of the MOVE: {left or 'nothing — both cells are transposed'}")
    q = d["the_first_question"]
    print(f"\n  first question  ANSWERED (T-1479, 2026-09-23): the ground is never "
          f"withdrawn, so a structure on a withdrawn lot is not a case — and "
          f"{q['of_those_carrying_a_committed_seating']} of "
          f"{q['blocks_whose_lot_lines_are_withheld']} withheld blocks carry a seating, "
          f"which is the check that it held")


def write(d: dict) -> None:
    OUT.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


def check() -> int:
    if not OUT.exists():
        print(f"FAIL {OUT.relative_to(ROOT)} is not committed")
        return 1
    fresh = json.dumps(derive(), indent=1, ensure_ascii=False) + "\n"
    if fresh != OUT.read_text():
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

    # 1. The cells are the ones the West Division grid gave up, and only those. T-2148
    #    carried Clinton to Madison and so put plat block 50 between Clinton and Canal
    #    onto the Original Town's west tier, the third such cell; it arrived here on its
    #    own, as this measurement was written to let it, and it was cut on the West
    #    module from the start.
    ck(len(d["blocks"]) == 3, "exactly three cells stand in both grids")
    ck([b["plat_block_number"] for b in d["blocks"]] == [28, 45, 50],
       "the three cells are plat blocks 28, 45 and 50")

    # 2. The disagreement this ticket exists for: the sheet counts ten, the layer cuts
    #    eight, and the sheet's count is documented. If these ever meet, the ticket is done.
    for b in d["blocks"]:
        ck(b["what_the_sheet_reads"]["lot_count"] == 10,
           f"block {b['plat_block_number']}: the sheet counts ten lot numerals")
        ck(b["what_the_sheet_reads"]["rows"] == 5
           and b["what_the_sheet_reads"]["columns"] == 2,
           f"block {b['plat_block_number']}: read two columns by five rows")
        if b["state"] == "transposed":
            ck(b["what_the_layer_cuts"]["lot_count"] == b["what_the_sheet_reads"]["lot_count"],
               f"block {b['plat_block_number']}: a transposed cell must cut exactly the "
               "number of lots the sheet counts in it — a cut that lands on some other "
               "number has stopped reading the block and is making one up")
            ck(b["what_the_layer_cuts"]["module"] == WEST_MODULE,
               f"block {b['plat_block_number']}: a transposed cell is cut on the West "
               "Division's module")
        else:
            ck(b["what_the_layer_cuts"]["lot_count"] == 8,
               f"block {b['plat_block_number']}: a held cell still cuts eight")
            ck(b["what_the_layer_cuts"]["module"] == "south_division_thompson_1830",
               f"block {b['plat_block_number']}: a held cell is still on the South module")

    # 3. Refusal 1 must BIND, or the re-cut is not refused by arithmetic at all.
    for b in d["blocks"]:
        r = b["refusal_1_the_module_does_not_fit"]
        ck(r["short_east_west_by_ft"] > 0,
           f"block {b['plat_block_number']}: the block must be short east to west")
        ck(r["the_committed_face_ft"] < r["the_two_lot_columns_want_ft"],
           f"block {b['plat_block_number']}: the two lot columns alone must not fit, "
           "or the alley is the only thing in the way and the refusal is weaker "
           "than it is written")
        ck(abs(r["rows_the_depth_divides_into"] - 5) > 0.05,
           f"block {b['plat_block_number']}: the depth must NOT divide into five whole "
           "lots, or the north-south half of the refusal has stopped being true")

    # 4. Refusal 2 is independent of refusal 1 and must stand on its own: no printed
    #    dimension, therefore withheld. A figure appearing on the sheet retires it.
    for b in d["blocks"]:
        r = b["refusal_2_this_block_prints_no_dimension"]
        ck(r["lot_frontage_ft"] is None,
           f"block {b['plat_block_number']}: no frontage may be printed")
        ck(r["lot_depth_ft"] == PRINTS_ITS_DEPTH.get(b["plat_block_number"]),
           f"block {b['plat_block_number']}: the depth printed must be the sheet's "
           f"own ({PRINTS_ITS_DEPTH.get(b['plat_block_number'])}); read {r['lot_depth_ft']}")

    # 5. The seating is what makes this a re-seat rather than a layer edit. If it ever
    #    falls to nothing, the move becomes cheap and this measurement is stale.
    strands = sum(len(b["the_committed_seating_on_this_block"]
                      ["structures_named_on_those_lots"]) for b in d["blocks"])
    # The floor was seventeen while both blocks' lots were reached by the street-edge and
    # lot-line layers. T-1734 turned block 45 through ninety degrees, so its lots front
    # Clinton and Canal — streets `generate_frontage_works.py` does not lay, its
    # `EDGE_CROSS_STREETS` being empty for the triangle budget recorded beside it — and
    # three street-lining fence runs stopped naming its lots. What the floor is FOR is
    # unchanged: if the seating ever falls to nothing the move was free and this
    # measurement is stale. Sixteen is the figure the two cuts leave, and it is the
    # figure to notice moving.
    ck(strands >= 16, "at least sixteen structures stand on these two blocks' lots — "
                      f"read {strands}")
    ck(all(b["the_committed_seating_on_this_block"]["rows_seated_on_those_lots"]
           for b in d["blocks"]),
       "both blocks must carry seated rows in a committed layer")

    # 5b. T-1733. THE RULING IS RECORDED AS HAVING LANDED ON EXACTLY ONE OF THE TWO, and
    #     which one is read off the layer rather than named. Both halves are assertions
    #     about this project's own consistency: a cell cut on the West module that no
    #     ruling authorised, or a cell held for a deal it does not carry, is a grid saying
    #     one thing and a record saying another.
    states = sorted(b["state"] for b in d["blocks"])
    ck(states == ["transposed"] * 3,
       "EVERY cell must be transposed (block 50 was never held). T-1733 cut block 28, which carried no deal, and "
       "T-1734 cut block 45 after re-arguing the deal that held it; a cell reading `held` "
       "again means a parcel has come back onto it without `frontage_argued_on`, or one "
       "of the two tickets has been reverted. This is the assertion that was the other "
       f"way about until 2026-09-28, and it is the same consistency check. Read: {states}")
    for b in d["blocks"]:
        if b["state"] == "transposed":
            g = b["what_the_cut_is_graded"]
            ck(g["the_module_carry"] == "inferred",
               f"block {b['plat_block_number']}: the module CARRY must grade `inferred` "
               "and never `documented` — this block prints no dimension of its own, and "
               "the ruling permitted the carry, not a promotion of it")
            ck(g["the_numerals"] == ["documented"],
               f"block {b['plat_block_number']}: every lot numeral on a transposed cell "
               "is read at its own position in the block, so each grades `documented`; "
               f"read {g['the_numerals']}")
            seat = b["the_re_seat"]
            ck(len(seat["lot_by_lot"]) == b["what_the_sheet_reads"]["lot_count"],
               f"block {b['plat_block_number']}: the re-seat must account for every lot "
               "of the new cut, held or empty")
            ck(sorted(l["plat_lot_number"] for l in seat["lot_by_lot"])
               == sorted(n for row in b["what_the_sheet_reads"]
                         ["lot_numerals_north_to_south"] for n in row),
               f"block {b['plat_block_number']}: the cut lots must carry exactly the "
               "numerals the sheet reads in this block, each at its own position — a "
               "numeral moved to make the two agree is an invention")
            ck(any(l["records"] for l in seat["lot_by_lot"]),
               f"block {b['plat_block_number']}: some lot of the new cut must carry a "
               "committed record, or nothing was re-seated and the move was free")
        else:
            w = b["what_holds_this_block_now"]
            ck(w["its_own_deal"],
               f"block {b['plat_block_number']}: a held cell must be held by a DEALT "
               "PARCEL read out of data/reconstruction/1835_platted_block_parcels.json. "
               "If that parcel ever leaves the file, nothing holds this block and it is "
               "transposed with its twin rather than sitting on a stale reason")
            ck(ticket_state(w["owed_by"]) not in (None, "done"),
               f"block {b['plat_block_number']}: the ticket that owes this block must "
               f"resolve in tickets/ and must not read done while the block is still "
               f"held — {w['owed_by']} reads {ticket_state(w['owed_by'])}")

    # 6. The precondition, and the finding that nobody owns it. This is the assertion
    #    that turns stale the day someone files or reopens the street-move ticket.
    p = d["the_precondition"]
    ck(p["short_by_ft"] > 0, "the committed spacing must be short of the plat module")
    ck(p["the_plat_street_module_ft"] == 458, "the plat's street module is 458 ft")
    ck(all(v == "done" for v in p["reported_it_and_closed"].values()),
       "the two tickets that reported this gap must still be closed — if one reopens, "
       "the move has two owners and the successor's scope has to be re-cut")
    # Vacuously true now that the move is done and `OWNS_THE_MOVE` is empty, and that is
    # the right shape: it fires again the moment somebody names a ticket here, which is
    # the only way this pointer can go stale a second time.
    ck(all(v is not None for v in p["owns_what_is_left"].values()),
       "the ticket this refusal points a reader FORWARD at must resolve in tickets/. "
       "That is the whole fault this assertion exists for: for three days the prose "
       "named T-0445, which was already done, so a reader following it arrived at a "
       "closed ticket and the move looked owned when it was not. A named ticket that "
       "does not resolve at all is the same dead end one step worse. Whether the move "
       "has HAPPENED is not tested here — the spacing figure above tests that, and it "
       "goes red the day Clinton and Canal reach the plat's module")

    # 7. The first question's answer rests on the case never having arisen. One
    #    structure seated on a withheld block anywhere in town would answer it instead.
    q = d["the_first_question"]
    ck(q["blocks_whose_lot_lines_are_withheld"] >= 2, "some blocks are withheld")
    ck(q["of_those_carrying_a_committed_seating"] == 0,
       "no withheld block may carry a seating. Before the ruling this was the evidence "
       "the case had never arisen; it is now the evidence the ANSWER HELD — the ruling "
       "answers the question by re-cutting rather than withholding, so a withheld block "
       "carrying a seating would mean the ground was withdrawn from a record after all")
    ck("answered_by" in q and q["answered_by"]["ticket"] == "T-1479",
       "the first question must carry the ruling that answered it, with the ticket it was "
       "asked on — an answered question whose answer is not written down is an open one")

    if fail:
        for m in fail:
            print(f"  FAIL {m}")
        print(f"SELF-TEST FAIL — {len(fail)} case(s)")
        return 1
    print("SELF-TEST PASS — the pair, the sheet's ten against what each cell now cuts, "
          "both refusals still standing as arithmetic, the seating, both cells transposed "
          "at `inferred` with their numerals at their own positions and each re-seat "
          "accounted lot by lot, block 45's deal re-argued onto the faces the transpose "
          "gives, the precondition, and the first question's answer")
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
