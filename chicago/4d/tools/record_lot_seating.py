#!/usr/bin/env python3
"""Which lot of the NEW north-and-west grid every documented record stands on.

    python3 tools/record_lot_seating.py --check      re-derive, and assert the committed
                                                     records carry the seat measured here
    python3 tools/record_lot_seating.py --write      write the seats onto the records
    python3 tools/record_lot_seating.py --report     every seat, every grid, every refusal
    python3 tools/record_lot_seating.py --self-test  the refusals fire

T-1478, the second piece of T-1456 and the last line of T-1194's acceptance: *every
documented north or west record's lot recorded on the record, where the lot grid now
names it*. Until T-1194 there was one lot layer and it stopped at the main stem, so a
documented building north or west of the river stood on a block at best and on a bare
coordinate at worst. There are now four more grids out there — Thompson's North Division
tier, the West Division, the Michigan Street tract, Wabansia — and the School Section
tier beyond Madison. This is where a record is told which lot of them it fell on.

## THIS IS A MEASUREMENT AND NOT A CLAIM, WHICH IS THE WHOLE DESIGN

The corpus already has both of the things a record can SAY about a lot, and this is
neither of them:

  * `lot_claim` (T-0384, `docs/CORNER-ORDINAL.md`) — a record placed by an ordinal off a
    corner declaring that it claims NO lot.
  * `lot_address` (T-0423, `docs/LOT-ADDRESS.md`) — a record whose SOURCE prints a lot
    and a block, which is the plat's own language and the strongest placement statement
    the corpus makes.

`stands_on_lot` says something weaker and different: the footprint this project has
already committed, measured against a lot grid drawn AFTERWARDS, falls mostly on this
lot. No source said so. Nobody claimed it. It is the same arithmetic
`tools/plat_occupancy.py` does for the South Division's schedule, written down where a
reader of the record can see it, and `claims_lot` is `false` in every seat this module
writes so that no later reader can mistake the two. A record may carry `lot_claim` AND
`stands_on_lot` at once without contradiction — the first is what the newspaper claimed,
the second is where the ground under the building turned out to be — and the seat NEVER
relaxes the claim.

## WHOSE RECORDS

Documented ones: the `research` layer of `plat_occupancy.layers()`, and only that. The
other two layers are this project's own output — `reconstruction` count-units already
carry the programme's `block_id`/`lot_index`, and an `inferred_household` roof was raised
because an argued household needed somewhere to be. Writing a derived plat lot onto
either would let the reconstruction read back as a fact about the town, which is the one
thing the three-layer split exists to prevent. `--check` refuses a seat on either.

The Original Town is out of scope and stays out: its lots have been committed since
T-0221, its documented records are seated by `lot_address` and the block programme, and
re-seating them from here would be two rules for one question. Only the grids T-1194
raised are read.

## THE SEAT IS plat_occupancy's, NOT A SECOND RULE

`plat_occupancy.lot_holders` is imported, not copied: a building stands on the lot most
of it is on, and only if it reaches that lot's buildable inset. Two copies of one rule is
how they drift (that module's own docstring says so, and it exists because they did).
What is added here is the NUMBER, which the South Division never had: the North Division
tier's lots carry the numerals Thompson letters across them, the West Division's carry
the ones the sheet prints, and the School Section's carry the register's. Wabansia and
the Michigan Street tract carry none — their lots are ordered and unnumbered — so a seat
there says `lot_number: null` and states in `lot_number_withheld` that the grid gives no
numeral, rather than counting one off the polygon list and calling it a lot number.

## THE GRADE IS THE WEAKEST THING IT RESTS ON

A seat is exactly as good as the lot lines it fell inside and the numeral on them, and
both are read off the layer rather than typed here: `lot_lines_confidence` and
`lot_numbers_confidence` come from the block's own `confidence` block where it has one
and the layer's where it does not, and `confidence` is the weaker of the two. The West
Division's numerals are `documented` and its lot lines are not, so its seats are
`inferred` — the numeral does not carry the line. Nothing in this module can raise a
phase's own confidence and `--check` re-reads each seated record to prove none did.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STRUCTURES = DATA / "structures"
VECTORS = DATA / "traces" / "vectors"

sys.path.insert(0, str(ROOT / "tools"))

# The grids T-1194 raised beyond the Original Town, and where each one lives. A grid of
# `thompson_lots.json` is one of that file's `grid` values; the two tier files are whole
# layers of their own because their blocks are not cut between two committed street lines
# (each file's `why_this_file_and_not_thompson_lots` is the argument).
THOMPSON = VECTORS / "thompson_lots.json"
LAYERS: tuple[tuple[str, Path, str | None], ...] = (
    ("west_division", THOMPSON, "west_division"),
    ("michigan_st_tract", THOMPSON, "michigan_st_tract"),
    ("wabansia", THOMPSON, "wabansia"),
    ("kinzies_addition", THOMPSON, "kinzies_addition"),
    ("north_division_tier", VECTORS / "north_division_tier_lots.json", None),
    ("school_section_tier", VECTORS / "school_section_tier_lots.json", None),
)

# Weakest first. The seat takes the minimum of what it rests on, and a grade this list
# does not name is refused rather than defaulted.
GRADES = ("conjectural", "inferred", "documented")

# The record's own key order, so that seating a lot does not shuffle a file.
# `stands_on_lot` follows `lot_address` because the three are statements about the plat
# and read as a run: what the record claims is NOT its lot, what a source calls its lot,
# and what the ground under it turned out to be.
KEY_ORDER = ("id", "name", "aka", "archetype", "phases", "function", "occupants",
             "reconstruction", "lot_claim", "lot_address", "stands_on_lot", "land_owner",
             "xref", "_frontage", "research_note", "review_required",
             "resident_assignment")

FIELD = "stands_on_lot"


class SeatingError(RuntimeError):
    """A seat that rests on a grade nobody stated, a number nobody read, or a layer that
    has stopped saying what it said."""


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _grade(name: str, where: str, what: str) -> str:
    if name not in GRADES:
        raise SeatingError("%s grades its %s %r, which is not a confidence this corpus "
                           "has" % (where, what, name))
    return name


def _weakest(*grades: str) -> str:
    return min(grades, key=GRADES.index)


def grids(docs: dict[Path, dict] | None = None) -> list[dict]:
    """Every north-or-west lot grid, as {name, plat, layer, doc, blocks}.

    `docs` lets the self-test hand in a layer held in memory; a gate that edits the tree
    it is gating can leave it broken, so nothing here ever writes to `data/`.
    """
    docs = docs or {}
    out = []
    for name, path, grid_key in LAYERS:
        doc = docs.get(path) or load(path)
        blocks = [b for b in doc["blocks"]
                  if (grid_key is None or b.get("grid") == grid_key) and b.get("lots")]
        out.append({"name": name, "layer": str(path.relative_to(ROOT)), "doc": doc,
                    "blocks": blocks})
    return out


def _confidences(doc: dict, block: dict, lot: dict) -> tuple[str, str | None]:
    """(lot-line grade, lot-number grade) — read off the layer, never typed here."""
    block_conf = block.get("confidence") if isinstance(block.get("confidence"), dict) else {}
    doc_conf = doc.get("confidence")
    doc_conf = doc_conf if isinstance(doc_conf, dict) else {}
    lines = block_conf.get("lot_lines") or doc_conf.get("lot_lines")
    if lines is None and isinstance(doc.get("confidence"), str):
        lines = doc["confidence"]
    if lines is None:
        raise SeatingError("%s states no confidence for its lot lines, and a seat may "
                           "not invent one" % block["id"])
    numbers = None
    if lot_number(lot) is not None:
        numbers = (lot.get("plat_lot_confidence") or block_conf.get("lot_numbers")
                   or doc_conf.get("lot_numbers"))
        if numbers is None:
            raise SeatingError("%s prints a lot number and states no confidence for it"
                               % block["id"])
        numbers = _grade(numbers, block["id"], "lot numbers")
    return _grade(lines, block["id"], "lot lines"), numbers


def lot_number(lot: dict) -> int | None:
    """The numeral the sheet or the register puts on this lot, or None where it puts none.

    Two spellings across the layers and no third: `plat_lot_number` in `thompson_lots`
    and `lot` in the two tier files. `order` is NOT one of them — Wabansia's and the
    Michigan Street tract's lots are ordered along a face and carry no numeral at all,
    and reading a position as a number is exactly the invented citation this refuses.
    """
    for key in ("plat_lot_number", "lot"):
        if lot.get(key) is not None:
            return int(lot[key])
    return None


def _why_no_number(grid: dict, block: dict) -> str:
    return ("%s's lots carry no numeral: the grid orders them along the face and the "
            "sheet this file reads prints no lot number for them, so the seat names the "
            "block and the position in the block's own lot list and stops there."
            % grid["name"])


def _note(grid: dict, block: dict, lot: dict, share: float, number: int | None) -> str:
    where = ("lot %d" % number) if number is not None else "the unnumbered lot"
    return (
        "MEASURED, NOT CLAIMED (T-1478). This record's committed footprint lies %d%% on "
        "%s of %s in the %s grid, which is where tools/plat_occupancy.py seats it: a "
        "building stands on the lot most of it is on, and only if it reaches the part of "
        "that lot a roof could use. THE LOT GRID WAS DRAWN AFTER THE BUILDING WAS "
        "PLACED (T-1194 and its children), so this is an observation about the ground "
        "under a committed coordinate and NOT an address — no source names this lot, "
        "`claims_lot` is false, and nothing about the record's placement, footprint, "
        "form or confidence moved to write it. The seat is graded at the weaker of the "
        "lot lines this block states (%s) and the numeral on them (%s), read from %s."
        % (round(share * 100), where, block["id"], grid["name"],
           _confidences(grid["doc"], block, lot)[0],
           _confidences(grid["doc"], block, lot)[1] or "none — unnumbered",
           grid["layer"]))


def seat(docs: dict[Path, dict] | None = None,
         records: list[dict] | None = None) -> dict[str, dict]:
    """{structure_id: the `stands_on_lot` block it should carry}, derived from scratch."""
    from plat_occupancy import (LOT_MARGIN_M, SLIVER_M2, area, footprints, inset,  # noqa
                                layers, overlap_area)

    datum = load(DATA / "datum.json")
    layer_of = layers()
    placed = footprints(datum)
    if records is not None:
        keep = {r["id"] for r in records}
        placed = [(sid, poly) for sid, poly in placed if sid in keep]

    seats: dict[str, dict] = {}
    for grid in grids(docs):
        for block in grid["blocks"]:
            for index, lot in enumerate(block["lots"]):
                polygon = [tuple(p) for p in lot["polygon"]]
                room = inset(polygon, LOT_MARGIN_M)
                for sid, world in placed:
                    if layer_of.get(sid) != "research":
                        continue
                    here = overlap_area(world, polygon)
                    if here <= SLIVER_M2:
                        continue
                    if not room or overlap_area(world, room) <= SLIVER_M2:
                        continue
                    prior = seats.get(sid)
                    if prior is not None and prior["_area"] >= here:
                        continue
                    lines, numbers = _confidences(grid["doc"], block, lot)
                    number = lot_number(lot)
                    seats[sid] = {
                        "_area": here,
                        "_share": here / area(world) if area(world) else 0.0,
                        "_grid": grid, "_block": block, "_lot": lot,
                        "lines": lines, "numbers": numbers, "number": number,
                        "index": index,
                    }

    out: dict[str, dict] = {}
    for sid, found in sorted(seats.items()):
        grid, block, lot = found["_grid"], found["_block"], found["_lot"]
        number, share = found["number"], found["_share"]
        out[sid] = {
            "claims_lot": False,
            "grid": grid["name"],
            "plat": block.get("plat") or grid["doc"].get("plat"),
            "layer": grid["layer"],
            "block_id": block["id"],
            "lot_index": found["index"],
            "lot_number": number,
            "lot_number_withheld": None if number is not None
                                   else _why_no_number(grid, block),
            "lot_lines_confidence": found["lines"],
            "lot_numbers_confidence": found["numbers"],
            "confidence": _weakest(found["lines"], found["numbers"]) if found["numbers"]
                          else found["lines"],
            "footprint_share": round(share, 3),
            "derived_by": "tools/record_lot_seating.py",
            "note": _note(grid, block, lot, share, number),
        }
    return out


def _records() -> dict[str, tuple[Path, dict]]:
    return {path.stem: (path, load(path)) for path in sorted(STRUCTURES.glob("*.json"))}


def _indent(text: str) -> int:
    """The file's OWN indent, so that seating a lot does not reformat the record.

    Most of `data/structures/` is two-space and thirty-odd files are one-space. Which is
    house style is not this tool's question: a gate that rewhitespaces a file it only
    meant to add a key to buries its own change in three hundred lines of diff.
    """
    for line in text.split("\n")[1:]:
        stripped = len(line) - len(line.lstrip(" "))
        if stripped:
            return stripped
    return 2


def write() -> int:
    seats = seat()
    held = _records()
    changed = 0
    for sid, (path, record) in held.items():
        original = path.read_text(encoding="utf-8")
        want = seats.get(sid)
        if want is None:
            if FIELD in record:
                del record[FIELD]
            else:
                continue
        elif record.get(FIELD) == want:
            continue
        else:
            record[FIELD] = want
        ordered = {k: record[k] for k in KEY_ORDER if k in record}
        leftover = sorted(k for k in record if k not in ordered)
        if leftover:
            raise SeatingError("%s carries %s, which the key order does not name"
                               % (sid, ", ".join(leftover)))
        path.write_text(
            json.dumps(ordered, indent=_indent(original), ensure_ascii=False) + "\n",
            encoding="utf-8")
        changed += 1
    print("record lot seating: %d seat(s), %d record(s) rewritten"
          % (len(seats), changed))
    return 0


def check() -> int:
    seats = seat()
    held = _records()
    bad = 0
    for sid, want in sorted(seats.items()):
        entry = held.get(sid)
        if entry is None:
            print("  MISSING %s, which a lot seats" % sid)
            bad = 1
            continue
        record = entry[1]
        if record.get(FIELD) != want:
            print("  %s does not carry the %s the grid measures under it" % (sid, FIELD))
            bad = 1
        # Re-read where it is SPENT: a measured seat may not promote the thing it measured.
        for phase in record.get("phases") or []:
            position = phase.get("position") or {}
            if position.get("utm_e") is None:
                continue
            if position.get("confidence") not in ("documented", "inferred",
                                                  "conjectural", "reconstructed"):
                print("  %s has a placement graded %r, which is not a grade"
                      % (sid, position.get("confidence")))
                bad = 1
    from plat_occupancy import layers  # noqa: E402  (imported late: it reads data/)
    layer_of = layers()
    for sid, (_, record) in held.items():
        if FIELD not in record:
            continue
        if sid not in seats:
            print("  %s carries a %s no lot of the north-or-west grid measures"
                  % (sid, FIELD))
            bad = 1
        if layer_of.get(sid) != "research":
            print("  %s is a `%s` record and may not carry a measured plat seat"
                  % (sid, layer_of.get(sid)))
            bad = 1
        if record[FIELD].get("claims_lot") is not False:
            print("  %s's %s claims a lot; this block is a measurement" % (sid, FIELD))
            bad = 1
    if bad:
        return 1
    numbered = sum(1 for s in seats.values() if s["lot_number"] is not None)
    print("record lot seating: %d documented record(s) seated on the north-or-west grid, "
          "%d of them on a numbered lot" % (len(seats), numbered))
    return 0


def report() -> int:
    for grid in grids():
        lots = sum(len(b["lots"]) for b in grid["blocks"])
        print("%-22s %2d block(s) with lots, %3d lot(s)  %s"
              % (grid["name"], len(grid["blocks"]), lots, grid["layer"]))
    print()
    for sid, block in sorted(seat().items()):
        print("%-34s %-20s %-28s lot %-6s %s  (%d%% of the footprint)"
              % (sid, block["grid"], block["block_id"],
                 block["lot_number"] if block["lot_number"] is not None else "—",
                 block["confidence"], round(block["footprint_share"] * 100)))
    return 0


def self_test() -> int:
    failed = 0

    def case(what: str, break_it) -> None:
        nonlocal failed
        doc = load(THOMPSON)
        north = load(VECTORS / "north_division_tier_lots.json")
        docs = {THOMPSON: doc, VECTORS / "north_division_tier_lots.json": north}
        break_it(doc, north)
        try:
            seat(docs)
        except SeatingError:
            print("  ok:    refused %s" % what)
            return
        print("  FAIL:  accepted %s" % what)
        failed = 1

    def blocks_of(north: dict) -> list[dict]:
        """Every tier block that has lots — the grades live on the block, not the file."""
        return [b for b in north["blocks"] if b.get("lots")]

    def on_every_block(mutate):
        def apply(doc, north):
            north["confidence"] = {}
            for block in blocks_of(north):
                mutate(block)
        return apply

    case("a layer that states no confidence for its lot lines",
         on_every_block(lambda b: b["confidence"].pop("lot_lines")))
    case("a lot-line grade this corpus does not have",
         on_every_block(lambda b: b["confidence"].__setitem__("lot_lines", "certain")))
    case("a numbered lot whose numeral is graded by nobody",
         on_every_block(lambda b: b["confidence"].pop("lot_numbers")))
    case("a lot-number grade this corpus does not have",
         on_every_block(lambda b: b["confidence"].__setitem__("lot_numbers", "measured")))

    # An unnumbered grid is seated rather than refused, and says so in the record.
    north = load(VECTORS / "north_division_tier_lots.json")
    for block in north["blocks"]:
        for lot in block.get("lots") or []:
            lot.pop("lot", None)
    unnumbered = seat({THOMPSON: load(THOMPSON),
                       VECTORS / "north_division_tier_lots.json": north})
    tier = [s for s in unnumbered.values() if s["grid"] == "north_division_tier"]
    if tier and all(s["lot_number"] is None and s["lot_number_withheld"] for s in tier):
        print("  ok:    an unnumbered lot seats the block and withholds the numeral")
    else:
        print("  FAIL:  an unnumbered lot did not withhold its numeral")
        failed = 1

    seats = seat()
    if not seats:
        print("  FAIL  nothing is seated, so nothing can be broken")
        return 1
    if any(s["claims_lot"] for s in seats.values()):
        print("  FAIL  a measured seat claims a lot")
        failed = 1
    else:
        print("  ok:    no measured seat claims a lot")
    if any(s["confidence"] == "documented" for s in seats.values()):
        print("  FAIL  a seat is graded documented on conjectural or inferred lot lines")
        failed = 1
    else:
        print("  ok:    no seat is graded above the lot lines it fell inside")
    print("  ok:    %d documented record(s) seated across %d grid(s)"
          % (len(seats), len({s["grid"] for s in seats.values()})))
    return failed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    try:
        if args.report:
            return report()
        if args.write:
            return write()
        if args.self_test:
            return self_test()
        return check()
    except SeatingError as exc:
        print("RECORD LOT SEATING REFUSED: %s" % exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
