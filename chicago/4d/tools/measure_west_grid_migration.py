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

THE PRECONDITION IS UNOWNED. Both refusals name the street spacing, and both name the
ticket that would move it: T-0445. T-0444 reported the gap and T-0445 was to close it.
Both are closed, and the committed spacing is still 367.9 ft — the refusal text in
`generate_plat_lots.py` still points forward to a ticket that has already been done.
That is recorded here as a finding, not repaired: moving a street line is not this
module's to do, and it is not this ticket's either.

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
NAMED_BY_THE_REFUSAL = ("T-0444", "T-0445")


def load(path: pathlib.Path):
    return json.loads(path.read_text())


def ticket_state(ticket_id: str) -> str | None:
    """A named ticket's state, off its own file's front matter."""
    for path in sorted((ROOT / "tickets").glob(f"{ticket_id}-*.md")):
        head = path.read_text().split("---")[1]
        for line in head.splitlines():
            if line.startswith("state:"):
                return line.split(":", 1)[1].strip()
    return None


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


def derive() -> dict:
    lots = load(LOTS)
    sheet = load(SHEET)
    streets = load(STREETS)
    module = sheet["the_west_division_block"]

    blocks = {b["id"]: b for b in lots["blocks"]}
    sheet_by_number = {b["plat_block_number"]: b for b in sheet["blocks"]}

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
                "lot_frontage_ft": twin["module"]["lot_frontage_ft"],
                "alley_runs": twin["module"]["alley_runs"],
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
            "what_a_withheld_cut_would_strand": seated,
        })

    spacing_ft = street_spacing_ft(streets, "clinton", "canal")
    module_street_ft = float(module["north_south_street_module_ft"])

    return {
        "_doc": (
            "T-1479. What moving plat blocks 28 and 45 onto the West Division grid would "
            "cost, and the committed arithmetic that refuses it. NOTHING IS MOVED BY THE "
            "TOOL THAT WRITES THIS FILE: no lot line is cut, no record re-seated, no "
            "block re-emitted. It is a measurement, in the manner of "
            "tools/measure_west_division_module.py, and its purpose is that the ticket's "
            "refusal carries figures."),
        "tool": "tools/measure_west_grid_migration.py",
        "ticket": "T-1479",
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
            "so": ("the West Division module cannot be seated on these blocks until the "
                   "committed Clinton and Canal centrelines carry the plat's own "
                   "spacing. That is a street move, which this ticket may not make."),
            "named_as_owning_the_move": {
                t: ticket_state(t) for t in NAMED_BY_THE_REFUSAL},
            "and_the_finding": (
                "both tickets the refusal points forward to are CLOSED, and the spacing "
                "is still short. The move is therefore unowned: no open ticket carries "
                "it, and the prose in tools/generate_plat_lots.py points a reader at "
                "work that has already been done. A successor is owed."),
        },
        "the_first_question": {
            "asked_by_the_ticket": (
                "what is a structure seated on a withdrawn lot seated on?"),
            "blocks_whose_lot_lines_are_withheld": len(withheld_blocks),
            "of_those_carrying_a_committed_seating": len(withheld_carrying_a_structure),
            "so": ("the case has never arisen, which is why no rule was ever written "
                   "for it. Withdrawing these two blocks' lot lines would raise it for "
                   "the first time, and would raise it against real seating rather "
                   "than against an empty block — so the rule has to be written before "
                   "the move, not discovered during it."),
        },
        "what_this_does_not_say": (
            "that the layer is wrong about the GROUND. Both blocks' boundaries, faces "
            "and areas are cut from committed centrelines and are not in question here; "
            "what the sheet contradicts is the lot ARRANGEMENT inside them. Nor does it "
            "say the sheet's ten numerals should be seated at the plat's printed size on "
            "this project's short spacing — that would put lot lines outside the block."),
    }


def report(d: dict) -> None:
    print("T-1479 — blocks 28 and 45 onto the West Division grid: what it would cost\n")
    for b in d["blocks"]:
        print(f"  plat block {b['plat_block_number']}  "
              f"{b['derived_by_the_original_town_grid_as']}")
        print(f"    {b['the_gap']}")
        r1 = b["refusal_1_the_module_does_not_fit"]
        print(f"    refusal 1  face {r1['the_committed_face_ft']} ft against the "
              f"{r1['the_block_wants_ft']:.0f} ft block — short {r1['short_east_west_by_ft']} ft; "
              f"the depth divides into {r1['rows_the_depth_divides_into']} lots")
        print(f"    refusal 2  {b['refusal_2_this_block_prints_no_dimension']['refused_on_the_sheet']} "
              f"-> the grid withholds its lot lines rather than cutting them")
        s = b["what_a_withheld_cut_would_strand"]
        print(f"    strands    {len(s['structures_named_on_those_lots'])} structures, "
              f"{sum(s['rows_seated_on_those_lots'].values())} seated rows across "
              f"{len(s['lots_reached_by_a_committed_record'])} lots")
    p = d["the_precondition"]
    print(f"\n  precondition  Clinton to Canal committed at {p['committed_clinton_to_canal_ft']} ft "
          f"against the plat's {p['the_plat_street_module_ft']:.0f} ft — short {p['short_by_ft']} ft")
    print(f"                {', '.join(f'{k} is {v}' for k, v in p['named_as_owning_the_move'].items())}")
    q = d["the_first_question"]
    print(f"\n  first question  {q['of_those_carrying_a_committed_seating']} of "
          f"{q['blocks_whose_lot_lines_are_withheld']} withheld blocks carry a seating "
          f"— the case has never arisen")


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

    # 1. The pair is the two the West Division grid gave up, and only those two.
    ck(len(d["blocks"]) == 2, "exactly two cells stand in both grids")
    ck([b["plat_block_number"] for b in d["blocks"]] == [28, 45],
       "the two cells are plat blocks 28 and 45")

    # 2. The disagreement this ticket exists for: the sheet counts ten, the layer cuts
    #    eight, and the sheet's count is documented. If these ever meet, the ticket is done.
    for b in d["blocks"]:
        ck(b["what_the_sheet_reads"]["lot_count"] == 10,
           f"block {b['plat_block_number']}: the sheet counts ten lot numerals")
        ck(b["what_the_sheet_reads"]["rows"] == 5
           and b["what_the_sheet_reads"]["columns"] == 2,
           f"block {b['plat_block_number']}: read two columns by five rows")
        ck(b["what_the_layer_cuts"]["lot_count"] == 8,
           f"block {b['plat_block_number']}: the layer cuts eight")
        ck(b["what_the_layer_cuts"]["module"] == "south_division_thompson_1830",
           f"block {b['plat_block_number']}: the layer cut it on the South module")

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
        ck(r["lot_depth_ft"] is None and r["lot_frontage_ft"] is None,
           f"block {b['plat_block_number']}: neither dimension may be printed")

    # 5. The seating is what makes this a re-seat rather than a layer edit. If it ever
    #    falls to nothing, the move becomes cheap and this measurement is stale.
    strands = sum(len(b["what_a_withheld_cut_would_strand"]
                      ["structures_named_on_those_lots"]) for b in d["blocks"])
    ck(strands >= 17, "at least seventeen structures stand on these two blocks' lots")
    ck(all(b["what_a_withheld_cut_would_strand"]["rows_seated_on_those_lots"]
           for b in d["blocks"]),
       "both blocks must carry seated rows in a committed layer")

    # 6. The precondition, and the finding that nobody owns it. This is the assertion
    #    that turns stale the day someone files or reopens the street-move ticket.
    p = d["the_precondition"]
    ck(p["short_by_ft"] > 0, "the committed spacing must be short of the plat module")
    ck(p["the_plat_street_module_ft"] == 458, "the plat's street module is 458 ft")
    ck(all(v == "done" for v in p["named_as_owning_the_move"].values()),
       "both tickets the refusal names must still be closed, or the move has an owner "
       "again and this finding is out of date")

    # 7. The first question's answer rests on the case never having arisen. One
    #    structure seated on a withheld block anywhere in town would answer it instead.
    q = d["the_first_question"]
    ck(q["blocks_whose_lot_lines_are_withheld"] >= 2, "some blocks are withheld")
    ck(q["of_those_carrying_a_committed_seating"] == 0,
       "no withheld block may carry a seating — if one does, the rule this ticket owes "
       "already exists somewhere and must be read off it rather than written")

    if fail:
        for m in fail:
            print(f"  FAIL {m}")
        print(f"SELF-TEST FAIL — {len(fail)} case(s)")
        return 1
    print("SELF-TEST PASS — the pair, the ten-against-eight gap, both refusals, the "
          "seating, the unowned precondition and the unanswered first question")
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
