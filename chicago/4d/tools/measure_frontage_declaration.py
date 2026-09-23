#!/usr/bin/env python3
"""Does a frontage run stand across every lot its recipe entry declares?

T-0429 found the first one that did not. `blk_south_water_lasalle`'s first deal
declared lots 0, 2 and 4 of its South Water face and its three units stood on lot 4
alone: the run is anchored `corner: east` and packed back west until the roofs it was
dealt ran out, which happened inside the eastmost lot. T-0449 was opened to measure the
other eight entries of that row and correct them the same way. This tool is that
measurement, committed so it is a gate rather than a reading somebody once took.

WHAT IS MEASURED. A frontage entry's `lots` list is projected onto the block face out of
`tools/block_faces.py`, and so is every committed footprint of the entry's own frontage
slots. A lot is REACHED when the run's along-face span overlaps the lot's, and lots that
do not come to the face at all are not candidates — `frontage_strip` in
`tools/generate_block_infill.py` refuses those with the same test, so the two files agree
about which lots a north-face run could possibly stand on. Nothing here authors a
coordinate: the run's span is read off the committed structure records and the lot spans
off the committed plat grid.

WHAT THE FIELD TURNED OUT TO BE DOING, and why the correction took a second ticket.
`frontage.lots` was answering three questions at once:

  1. the run's own strip — `frontage_strip` runs it from the west line of the westmost
     declared lot to the east line of the eastmost, and an east-anchored run takes its
     anchor off that eastmost line;
  2. the block's lot classes — `check_block` puts every declared lot in `built on by this
     parcel`, which is also what makes an ancillary yard building on that lot stand
     behind a roof of the same parcel;
  3. the block's declared BUSINESS FRONT — `shared_business_fronts` in
     `tools/plat_occupancy.py` applied the owner's 2026-08-27 clause (a documented store
     at the street does not exhaust a business-front lot) to the same list.

So narrowing a declaration to the ground its run measurably stands on did not only
retract a false claim: it withdrew the owner's ruling from the lots it dropped, and on
this row two of them carry a documented store with a yard building of the same parcel
behind it. That is what made the three remaining corrections unrunnable in T-0449, and
all three were conceded here rather than fixed.

T-1053 SEPARATED THE QUESTIONS AND THE CONCESSIONS ARE GONE. Question 3 moved to its own
field: an entry may name `business_front` beside `lots`, and where it does not the run's
own ground is the front, so the town's occupancy map did not move by a lot. `lots` is
left meaning one thing — the ground the run measurably stands across — and this tool
gates it EXACTLY. Question 2 came out in the wash: the three yard buildings were standing
in the yards of lots their households' roofs were not on, which is the false statement
the over-declaration had been covering, and each was re-lotted onto the lot of the roof
it serves.

    franklin  [4, 6] -> [6]     privy re-lotted 4 -> 6, lot 4 named open
    wells  [0, 2, 4] -> [2, 4]  privy re-lotted 0 -> 4, lot 0 stays on `business_front`
    dearborn [0,2,4] -> [4]     privy re-lotted 0 -> 4, lots 0 and 2 stay on the front

WHAT IS GATED NOW. Every entry's `lots` is exactly the lots its run stands across — a
run dealt ground it never reaches is a failure at the commit that writes it, which is
the whole point of gating a reading nobody would otherwise take twice. And a
`business_front`, where one is named, has to CONTAIN the run's own ground and to lie on
the entry's own face: a front that does not cover the run it fronts is not a front, and
a clause pointed at a lot of some other face is pointed at nothing.

    tools/measure_frontage_declaration.py            report every entry
    tools/measure_frontage_declaration.py --check    the gate
    tools/measure_frontage_declaration.py --self-test
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from block_faces import extent, face_frame, project
from plat_occupancy import declared_front, footprints

ROOT = Path(__file__).resolve().parent.parent
LOTS = ROOT / "data" / "traces" / "vectors" / "thompson_lots.json"
DATUM = ROOT / "data" / "datum.json"
PARCELS = ROOT / "data" / "reconstruction" / "1835_platted_block_parcels.json"
PREFIX = "recon_1835_blk_"

# The same half-metre `frontage_strip` allows a lot before it calls it off the face, and
# the same sliver an overlap has to beat before it counts as standing across a lot.
REACH_M = 0.5
OVERLAP_M = 0.01

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_units(entry: dict) -> list[str]:
    """The record ids of the entry's own frontage slots, numbered as the generator does."""
    seq0 = int(entry.get("seq_start", 1))
    return [f"{PREFIX}{entry['block_id'].removeprefix('blk_')}_{slot['family'].lower()}_{seq:02d}"
            for seq, slot in enumerate(entry["slots"], start=seq0)
            if slot.get("stands_on") == "frontage"]


def reached(entry: dict, block: dict, placed: dict[str, list[tuple[float, float]]]
            ) -> tuple[list[int], tuple[float, float]]:
    """(the lots the run measurably stands across, its along-face span, the face's lots)."""
    frame = face_frame(block, entry["frontage"]["face"])
    spans = [extent(frame, placed[sid]) for sid in run_units(entry) if sid in placed]
    if not spans:
        raise SystemExit(f"{entry['programme_phase']}: the entry names a frontage run "
                         f"and no committed record stands on it")
    run = (min(s[0] for s in spans), max(s[1] for s in spans))
    out, on_face = [], []
    for index, lot in enumerate(block["lots"]):
        corners = [project(frame, tuple(p)) for p in lot["polygon"]]
        if max(c[1] for c in corners) < -REACH_M:
            continue                                  # this lot is not on this face
        lo, hi = min(c[0] for c in corners), max(c[0] for c in corners)
        on_face.append(index)
        if min(run[1], hi) - max(run[0], lo) > OVERLAP_M:
            out.append(index)
    return out, run, on_face


def survey() -> list[dict]:
    grid, datum = load(LOTS), load(DATUM)
    blocks = {block["id"]: block for block in grid["blocks"]}
    placed: dict[str, list[tuple[float, float]]] = {}
    for sid, world in footprints(datum):
        placed.setdefault(sid, world)
    out = []
    for entry in load(PARCELS)["blocks"]:
        if not entry.get("frontage"):
            continue
        lots, run, on_face = reached(entry, blocks[entry["block_id"]], placed)
        declared = [int(i) for i in entry["frontage"]["lots"]]
        out.append({"phase": entry["programme_phase"], "block": entry["block_id"],
                    "face": entry["frontage"]["face"],
                    "declared": declared, "reached": lots, "run": run,
                    "front": declared_front(entry["frontage"]),
                    "on_face": on_face,
                    "over": [i for i in declared if i not in lots]})
    return out


def faults(rows: list[dict]) -> list[str]:
    """Every way a frontage declaration can be untrue, in one list.

    T-1053 retired the CONCEDED table this function used to carry. A concession is a
    reading held open because the repair was coupled to something else; the coupling is
    gone, so a concession here would now only be a defect nobody had got to.
    """
    bad = []
    for row in rows:
        if row["over"]:
            bad.append(
                f"{row['phase']}: the run stands {row['run'][0]:.2f} m to "
                f"{row['run'][1]:.2f} m along its face, which is lot(s) {row['reached']}, "
                f"and the entry declares {row['declared']} — lot(s) {row['over']} carry "
                f"none of it")
        missing = [i for i in row["declared"] if i not in row["front"]]
        if missing:
            bad.append(
                f"{row['phase']}: `business_front` is {row['front']} and the run stands "
                f"on lot(s) {missing}, which it does not name. A block's business front "
                f"has to contain the run that fronts it")
        off = [i for i in row["front"] if i not in row["on_face"]]
        if off:
            bad.append(
                f"{row['phase']}: `business_front` names lot(s) {off}, which do not come "
                f"to the {row['face']} face at all. The owner's business-front clause "
                f"cannot reach a lot of another face")
    return bad


def self_test() -> None:
    grid = load(LOTS)
    block = next(b for b in grid["blocks"] if b["id"] == "blk_south_water_lasalle")
    frame = face_frame(block, "north")
    # The lots of a north face alternate with the Lake-face lots and the two project onto
    # the same stretch of the along axis, so the reach filter is what keeps a Lake lot out
    # of a South Water answer. Without it every north-face run reads twice the ground.
    north = [i for i, lot in enumerate(block["lots"])
             if max(project(frame, tuple(p))[1] for p in lot["polygon"]) >= -REACH_M]
    assert north == [0, 2, 4, 6], north
    # An entry that declares exactly what it reaches is silent, and T-0429's corrected
    # lasalle entry is the worked example the whole ticket is measured against.
    rows = survey()
    lasalle = next(r for r in rows if r["phase"] == "phase3_platted_block_south_water_lasalle")
    assert lasalle["declared"] == lasalle["reached"] == [4], lasalle
    assert not lasalle["over"], lasalle
    # T-1053. The gate has to fire on each of the three untruths it now knows about,
    # and a check nobody has watched fail has not been tested. Break each one in memory.
    assert not faults(rows), faults(rows)
    one = rows[0]
    over = faults([dict(one, declared=one["declared"] + [9],
                        front=one["front"] + [9], on_face=one["on_face"] + [9],
                        over=[9])])
    assert len(over) == 1 and "carry none of it" in over[0], over
    short = faults([dict(one, front=[i for i in one["front"]
                                     if i != one["declared"][0]])])
    assert len(short) == 1 and "has to contain the run" in short[0], short
    off = faults([dict(one, front=one["front"] + [99])])
    assert len(off) == 1 and "do not come" in off[0], off
    # And the three T-0449 entries are the worked examples: each declares only the
    # ground its run stands on, and each keeps a business front wider than that ground.
    for phase, lots, front in (
            ("phase3_platted_block_south_water_franklin", [6], [4, 6]),
            ("phase3_platted_block_south_water_wells", [2, 4], [0, 2, 4]),
            ("phase3_platted_block_south_water_dearborn", [4], [0, 2, 4])):
        row = next(r for r in rows if r["phase"] == phase)
        assert row["declared"] == row["reached"] == lots, row
        assert row["front"] == front, row
    print("measure_frontage_declaration self-test: ok")


def main() -> int:
    args = sys.argv[1:]
    if "--self-test" in args:
        self_test()
        return 0
    rows = survey()
    bad = faults(rows)
    if "--check" in args:
        for line in bad:
            print(f"  {line}")
        if bad:
            print(f"{len(bad)} frontage declaration fault(s)")
            return 1
        fronts = sum(1 for r in rows if r["front"] != r["declared"])
        print(f"{len(rows)} frontage entr(ies) measured, none over-declared, "
              f"{fronts} naming a business front wider than their own run")
        return 0
    for row in rows:
        flag = "  <-- over-declared" if row["over"] else ""
        front = "" if row["front"] == row["declared"] else f"  front {row['front']}"
        print(f"{row['phase']:<55} declared {str(row['declared']):<10} "
              f"reached {str(row['reached']):<10} "
              f"run {row['run'][0]:7.2f}..{row['run'][1]:7.2f} m{flag}{front}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
