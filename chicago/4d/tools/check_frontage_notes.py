#!/usr/bin/env python3
"""Does the party-line note say what the placement did? (T-0239)

`FRONTAGE_NOTE` in `tools/generate_block_infill.py` is the card a visitor opens on every
unit of a party-line street row, and it makes geometric claims about the building it is
printed on. Twice it made one the placement did not support, and twice a person reading
the file was what found it:

- T-0189 — the row was called the town's RIVER row on houses on Washington Street,
  400 m from the water;
- T-0208 — the note said the EAST wall was the anchored one on west-anchored runs, on
  nine of the twenty-seven records then carrying it.

`generate_block_infill.py --check` cannot catch either and never could. It re-derives
every committed record byte for byte FROM THE SAME TEMPLATE, so a template that says the
wrong thing re-derives the wrong thing perfectly and the gate stays green. That checks the
generator against itself. This checks the PROSE against the GEOMETRY.

WHAT IS READ, AND WHERE EACH SIDE COMES FROM. The claims are parsed out of the committed
note text (`phases[0].position.note`) and nothing else — not the recipe's anchor, not the
record's `reconstruction.frontage` block — because those are the inputs the sentence was
written from, and agreeing with them is what the regeneration gate already proves. The
measurements are taken off the committed footprint and the committed plat
(`data/traces/vectors/thompson_lots.json`, through `tools/block_faces.py`), the same
ground `place_frontage` stood the building on:

  1. "ON the {face} face of {block}, the block's {street} Street frontage" — the street
     the plat bounds that face of that block with is the street the sentence names;
  2. "Its front wall is {setback} m back from that lot line" — the footprint's face-side
     wall, projected onto the face's outward normal;
  3. "its {wall} wall" — the named wall is one of the two the run actually has ENDS at:
     on a north or south face those are its west and east walls, on an east or west face
     its south and north, read off the face's own axis rather than assumed;
  4. "is fixed by {anchor}" — the named wall stands where the anchor says:
       * "the {end} end of the run's own frontage, {c} m clear of the side lot line" —
         `c` in from that end of the lots the recipe entry declares for the run;
       * "the west wall of {X}" / "the east wall of {X}" — on that wall of X, measured
         off X's own committed footprint;
       * "{c} m west of {X}" — `c` west of X's west wall.

Every comparison uses the 5 mm the party-wall joins already use, widened by half a unit
of the last digit the sentence printed, so a figure the note rounds to 0.1 m is held to
what 0.1 m can say and no tighter.

THE T-0077 ROW IS NOT READ HERE. `tools/generate_inferred_infill.py` writes a sibling
note on the four Lake Street units of `blk_lake_clark` with a different sentence ("the
block's own east corner, 1.0 m clear of the platted corridor"). This tool selects on
T-0078's opening words and leaves that one alone rather than half-reading it.

    tools/check_frontage_notes.py              report every note and its readings
    tools/check_frontage_notes.py --check      the gate
    tools/check_frontage_notes.py --self-test  break the prose in memory; it must fire
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from block_faces import extent, face_frame, project  # noqa: E402
from measure_frontage_declaration import run_units  # noqa: E402
from plat_occupancy import footprints  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STRUCTURES = ROOT / "data" / "structures"
LOTS = ROOT / "data" / "traces" / "vectors" / "thompson_lots.json"
DATUM = ROOT / "data" / "datum.json"
PARCELS = ROOT / "data" / "reconstruction" / "1835_platted_block_parcels.json"
PREFIX = "recon_1835_blk_"
OPENING = "PARTY-LINE FRONTAGE, DERIVED FROM THE COMMITTED PLAT (T-0078)."

# The tolerance `check_frontage` holds a party line and a street line to: a placement is
# rounded to the millimetre before it is written.
JOIN_M = 0.005

NOTE_RE = re.compile(
    r"ON the (?P<face>\w+) face of (?P<block>blk_\w+), the block's (?P<street>.+?) Street "
    r"frontage, .*? Its front wall is (?P<setback>\d+(?:\.\d+)?) m back from that lot "
    r"line, .*?, and its (?P<wall>\w+) wall is fixed by (?P<anchor>.+?)\. The bearing is "
    r"the face's own, so the front looks square at (?P<street2>.+?) Street\.", re.S)
ANCHOR_RES = (
    ("end", re.compile(r"the (?P<end>\w+) end of the run's own frontage, "
                       r"(?P<clear>\d+(?:\.\d+)?) m clear of the side lot line at that end$")),
    ("wall_of", re.compile(r"the (?P<side>\w+) wall of (?P<target>[a-z0-9_]+), which it "
                           r"shares a party line with$")),
    ("clear_west", re.compile(r"(?P<clear>\d+(?:\.\d+)?) m west of (?P<target>[a-z0-9_]+), "
                              r"which stands proud of the platted line and so cannot share "
                              r"a wall with the row$")),
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def slack(printed: str) -> float:
    """5 mm, plus half a unit of the last digit the sentence printed."""
    decimals = len(printed.partition(".")[2])
    return JOIN_M + 0.5 * 10 ** -decimals


def compass(vector: tuple[float, float]) -> str:
    """The compass word for a direction on the ground: its larger component wins."""
    e, n = vector
    if abs(e) >= abs(n):
        return "east" if e > 0 else "west"
    return "north" if n > 0 else "south"


def ends(frame: dict, span: tuple[float, float]) -> dict[str, float]:
    """A run's two end walls by compass name, each as its along-face coordinate."""
    ahead = compass(frame["along"])
    behind = compass((-frame["along"][0], -frame["along"][1]))
    return {behind: span[0], ahead: span[1]}


def toward(frame: dict, word: str) -> float:
    """+1 if `word` is the way the face's along axis runs, -1 if it is the way back."""
    if compass(frame["along"]) == word:
        return 1.0
    if compass((-frame["along"][0], -frame["along"][1])) == word:
        return -1.0
    raise ValueError(word)


def parse(note: str) -> dict | None:
    m = NOTE_RE.search(note)
    if not m:
        return None
    claim = m.groupdict()
    for kind, pattern in ANCHOR_RES:
        a = pattern.match(claim["anchor"])
        if a:
            claim.update(a.groupdict(), kind=kind)
            return claim
    claim["kind"] = None
    return claim


def corpus() -> tuple[list[dict], dict[str, list[tuple[float, float]]]]:
    """Every committed record carrying T-0078's note, as {id, note, world}."""
    datum = load(DATUM)
    placed: dict[str, list[tuple[float, float]]] = {}
    for sid, world in footprints(datum):
        placed.setdefault(sid, world)
    out = []
    for path in sorted(STRUCTURES.glob(f"{PREFIX}*.json")):
        record = load(path)
        note = record["phases"][0]["position"].get("note") or ""
        if note.startswith(OPENING):
            out.append({"id": record["id"], "note": note, "world": placed[record["id"]]})
    return out, placed


def context() -> dict:
    grid = load(LOTS)
    blocks = {b["id"]: b for b in grid["blocks"]}
    run_of = {}
    for entry in load(PARCELS)["blocks"]:
        if entry.get("frontage"):
            for sid in run_units(entry):
                run_of[sid] = entry
    return {"blocks": blocks, "run_of": run_of}


def strip(entry: dict, block: dict, frame: dict) -> tuple[float, float]:
    """The run's own frontage along its face: the lots its recipe entry declares.

    The same span `frontage_strip` in the generator measures, read again here rather
    than imported, because the strip is ground and the ground is what the note is being
    held to. `measure_frontage_declaration.py --check` already gates that the declared
    lots are exactly the ones the run stands across.
    """
    along = [project(frame, tuple(p))[0]
             for i in entry["frontage"]["lots"] for p in block["lots"][int(i)]["polygon"]]
    return min(along), max(along)


def faults_of(item: dict, ctx: dict, placed: dict) -> tuple[list[str], dict]:
    sid, bad = item["id"], []
    claim = parse(item["note"])
    if claim is None:
        return [f"{sid}: the party-line note no longer reads as the template this gate "
                f"checks — a sentence nobody can parse is a sentence nobody is checking"], {}
    if claim["kind"] is None:
        return [f"{sid}: the note says its {claim['wall']} wall is fixed by "
                f"\"{claim['anchor']}\", which is no anchor this gate knows how to measure"], {}
    block = ctx["blocks"].get(claim["block"])
    if block is None:
        return [f"{sid}: the note stands it on {claim['block']}, which the plat does not "
                f"have"], {}
    if claim["face"] not in block["bounded_by"]:
        return [f"{sid}: the note names the {claim['face']} face, which a block does not "
                f"have"], {}
    frame = face_frame(block, claim["face"])
    plat_street = block["bounded_by"][claim["face"]].replace("_", " ").title()
    for said in {claim["street"], claim["street2"]}:
        if said != plat_street:
            bad.append(f"{sid}: the note calls the {claim['face']} face of {claim['block']} "
                       f"the {said} Street frontage, and the plat bounds that face with "
                       f"{plat_street} Street")
    world = item["world"]
    front = -max(project(frame, p)[1] for p in world)
    if abs(front - float(claim["setback"])) > slack(claim["setback"]):
        bad.append(f"{sid}: the note puts its front wall {claim['setback']} m back from the "
                   f"{claim['face']} lot line, and the footprint's front wall stands "
                   f"{front:.3f} m back")
    walls = ends(frame, extent(frame, world))
    if claim["wall"] not in walls:
        bad.append(f"{sid}: the note fixes its {claim['wall']} wall, and a run on the "
                   f"{claim['face']} face has its ends at its {' and '.join(sorted(walls))} "
                   f"walls")
        return bad, claim
    kind = claim["kind"]
    if kind == "end":
        entry = ctx["run_of"].get(sid)
        if entry is None:
            bad.append(f"{sid}: the note anchors it on the end of its run's frontage, and "
                       f"no recipe entry deals it a frontage run")
            return bad, claim
        if claim["end"] not in walls:
            bad.append(f"{sid}: the note anchors on the {claim['end']} end of a run on the "
                       f"{claim['face']} face, which has no such end")
            return bad, claim
        lo, hi = strip(entry, block, frame)
        edge = ends(frame, (lo, hi))[claim["end"]]
        target = edge - toward(frame, claim["end"]) * float(claim["clear"])
        tol = slack(claim["clear"])
        where = f"the {claim['end']} end of its run's frontage, {claim['clear']} m in"
    else:
        neighbour = placed.get(claim["target"])
        if neighbour is None:
            bad.append(f"{sid}: the note fixes it by {claim['target']}, which no committed "
                       f"footprint is called")
            return bad, claim
        theirs = ends(frame, extent(frame, neighbour))
        if kind == "wall_of":
            if claim["side"] not in theirs:
                bad.append(f"{sid}: the note names the {claim['side']} wall of "
                           f"{claim['target']}, which has no such wall along this face")
                return bad, claim
            target, tol = theirs[claim["side"]], JOIN_M
            where = f"the {claim['side']} wall of {claim['target']}"
        else:
            if "west" not in theirs:
                bad.append(f"{sid}: the note stands it west of {claim['target']} on the "
                           f"{claim['face']} face, which runs north and south")
                return bad, claim
            target = theirs["west"] + toward(frame, "west") * float(claim["clear"])
            tol = slack(claim["clear"])
            where = f"{claim['clear']} m west of {claim['target']}"
    gap = walls[claim["wall"]] - target
    if abs(gap) > tol:
        named = {w: v - target for w, v in walls.items()}
        hint = next((f" — it is the {w} wall that stands there" for w, d in named.items()
                     if w != claim["wall"] and abs(d) <= tol), "")
        bad.append(f"{sid}: the note says its {claim['wall']} wall is fixed by {where}, and "
                   f"that wall stands {abs(gap):.3f} m from it{hint}")
    return bad, claim


def survey() -> tuple[list[dict], list[str]]:
    items, placed = corpus()
    ctx = context()
    rows, bad = [], []
    for item in items:
        found, claim = faults_of(item, ctx, placed)
        bad += found
        rows.append({"id": item["id"], "claim": claim, "faults": found})
    return rows, bad


def self_test() -> None:
    items, placed = corpus()
    ctx = context()
    # The corpus is real and the parser reads all of it: a regex that quietly matched
    # nothing would make this gate green for ever.
    assert len(items) >= 40, len(items)
    claims = [faults_of(i, ctx, placed) for i in items]
    assert all(not f for f, _ in claims), [f for f, _ in claims if f]
    kinds = {(c["kind"], c["wall"]) for _, c in claims}
    for want in (("end", "east"), ("end", "west"), ("wall_of", "east"),
                 ("wall_of", "west"), ("clear_west", "east")):
        assert want in kinds, (want, kinds)
    faces = {c["face"] for _, c in claims}
    assert {"north", "south"} <= faces, faces

    def broken(item: dict, old: str, new: str) -> list[str]:
        assert old in item["note"], (item["id"], old)
        return faults_of(dict(item, note=item["note"].replace(old, new, 1)), ctx, placed)[0]

    by_kind = {}
    for item, (_, c) in zip(items, claims):
        by_kind.setdefault((c["kind"], c["wall"], c["face"]), item)
    # T-0208, put back: every anchored wall named the wrong way round must fire, and the
    # message must say which wall does stand there.
    for (kind, wall, face), item in by_kind.items():
        other = {"east": "west", "west": "east"}[wall]
        got = broken(item, f"its {wall} wall is fixed", f"its {other} wall is fixed")
        assert len(got) == 1 and f"the {wall} wall that stands there" in got[0], (kind, got)
    # a wall a north-face run does not have at either end
    item = by_kind[("end", "west", "north")]
    got = broken(item, "its west wall is fixed", "its north wall is fixed")
    assert len(got) == 1 and "has its ends at" in got[0], got
    # T-0189, put back: the right face called by another street's name
    got = broken(item, "the block's ", "the block's Water ")
    assert got and "the plat bounds that face" in got[0], got
    # the setback misstated by more than its printed precision
    claim = parse(item["note"])
    wrong = f"{float(claim['setback']) + 0.25:.2f}"
    got = broken(item, f"is {claim['setback']} m back", f"is {wrong} m back")
    assert len(got) == 1 and "front wall" in got[0], got
    # the corner margin misstated
    got = broken(item, f"{claim['clear']} m clear", f"{float(claim['clear']) + 1:.1f} m clear")
    assert len(got) == 1 and "the west end of its run's frontage" in got[0], got
    # the run's other end named
    got = broken(item, "the west end of the run", "the east end of the run")
    assert len(got) == 1, got
    # a party line named against a building the unit does not touch
    item = by_kind[("wall_of", "east", "north")]
    claim = parse(item["note"])
    stranger = next(i["id"] for i in items
                    if parse(i["note"])["block"] != claim["block"])
    got = broken(item, f"of {claim['target']},", f"of {stranger},")
    assert len(got) == 1 and "wall stands" in got[0], got
    # and a sentence reworded out from under the parser is a failure, not a skip
    got = broken(item, "is fixed by", "is held by")
    assert len(got) == 1 and "no longer reads" in got[0], got
    print(f"self-test: {len(items)} notes read, every broken claim refused")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    rows, bad = survey()
    if not args.check:
        for row in rows:
            c = row["claim"] or {}
            print(f"{row['id']}: {c.get('face')} face, {c.get('wall')} wall by "
                  f"{c.get('kind')} — {'OK' if not row['faults'] else 'FAULT'}")
    if bad:
        print("PARTY-LINE NOTES SAY WHAT THE PLACEMENT DID NOT")
        for line in bad:
            print(f"  - {line}")
        return 1
    print(f"verified {len(rows)} party-line notes against their footprints and the plat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
