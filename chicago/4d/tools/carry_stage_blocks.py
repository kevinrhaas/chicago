#!/usr/bin/env python3
"""T-1169: a research mint re-derives the record it owns and KEEPS the blocks it does not.

THE COLLISION THIS SETTLES. Four passes mint `data/residents/households/*.json` from
their registers, and each one's `--check` re-derives the whole file and compares it
byte for byte — `mint_documented_residents.py` says so itself: "ONE OWNER FOR THE
MANIFEST". That was true while the mints were the only writers. T-1167 opened a
second kind of writer over the same files — the reconstruction programme, whose
stages write ATTRIBUTE blocks onto households the mints own — and T-1169 is the
first stage to actually write one. The moment it did, three mints reported drift on
1,247 files: not because the record they derive had changed, but because the file
now carries something they never derived.

Both passes are right, and the fix is to say what each owns. Ownership here is
PER ATTRIBUTE, not per file, which is the grain T-1158 already cut for tiers: the
mint owns the record and every block it derives, and a reconstruction stage owns
exactly the blocks carrying its own `written_by_stage` mark. So a mint re-derives
its record and then carries the marked blocks back in, and the two can neither
overwrite each other nor drift apart.

WHAT THIS IS NOT. It is not a way for a mint to acquire a reconstructed value. The
blocks it carries are ones ALREADY COMMITTED by the one writer allowed to make them
(`tools/reconstruct_residents_1835.py`), they are re-derived and re-checked by that
writer's own `--check` on every commit, and a block that does not re-derive is a
gate failure there. Nothing here mints anything: it copies a committed block from
the file on disk back into the file about to be written to the same path.

AND IT IS NOT A HOLE IN THE REFUSAL. `refuse_reconstructed_grade.refuse_texts()`
guards the person-level `grade`, which this never touches — a carried block is an
attribute of a person, not a person. The mints keep their call, unchanged.

  python3 tools/carry_stage_blocks.py --check
  python3 tools/carry_stage_blocks.py --self-test
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

# The mark a reconstruction stage puts on every block it writes. It is the whole of
# how ownership is decided here, and it is the same mark
# `reconstruct_residents_1835.py --check` re-derives from.
MARKER = "written_by_stage"

# Where a carried block is seated when the re-derived record has no key for it, so a
# mint's output and the stage's output agree on field order and the byte comparison
# above stays meaningful. A key not named here is appended.
AFTER = {"arrival_year": "arrival"}

# The mints that must carry. Named rather than discovered, on the same reasoning
# `refuse_reconstructed_grade.WIRED_WRITERS` is: a writer that quietly stops carrying
# would delete a stage's work on its next `--build`, and a shorter list would hide it.
WIRED_MINTS = {
    "tools/mint_documented_residents.py",
    "tools/mint_letter_list_residents.py",
    "tools/mint_placed_residents.py",
    "tools/mint_civic_residents.py",
}
CALL = "carry(doc)"


def owned(block) -> bool:
    return isinstance(block, dict) and bool(str(block.get(MARKER) or "").strip())


def stage_blocks(doc: dict) -> dict:
    """The top-level attribute blocks a reconstruction stage owns in `doc`."""
    return {k: v for k, v in doc.items() if owned(v)}


def carry(doc: dict, committed: dict | None = None) -> dict:
    """`doc` with the committed record's stage-owned blocks seated back into it.

    `committed` defaults to the record already on disk at this household's own path,
    which is what a mint wants: it is re-deriving that exact file.
    """
    hid = doc.get("id")
    if committed is None:
        path = HOUSEHOLDS / f"{hid}.json"
        if not path.exists():
            return doc
        committed = json.loads(path.read_text(encoding="utf-8"))
    keep = stage_blocks(committed)
    if not keep:
        return doc

    out: dict = {}
    for key, value in doc.items():
        # A block the mint derives AND a stage owns is the stage's: the stage is
        # downstream, its value re-derives from the programme, and the mint's is the
        # empty one it always writes.
        out[key] = keep.pop(key, value)
        anchor = AFTER.get(key)
        for pending in [k for k, a in AFTER.items() if a == key and k in keep]:
            out[pending] = keep.pop(pending)
        del anchor
    for key, value in keep.items():
        out[key] = value
    return out


def self_test() -> int:
    failures = 0

    def check(name, got, want):
        nonlocal failures
        if got != want:
            failures += 1
            print(f"  FAIL {name}: {got!r} != {want!r}")
        else:
            print(f"  ok    {name}")

    mint = {"id": "hh_x", "arrival": {"value": "1835-06-30", "confidence": "inferred"},
            "origin": {"value": None, "confidence": "reconstructed", "note": "Not attested."},
            "persons": []}
    stage = dict(mint)
    stage["arrival_year"] = {"value": 1834, "confidence": "reconstructed",
                             MARKER: "attribute_fill_arrival"}
    stage["origin"] = {"value": "New England", "confidence": "reconstructed",
                       MARKER: "attribute_fill_arrival"}

    out = carry(json.loads(json.dumps(mint)), stage)
    check("a block the stage owns survives the mint's re-derivation",
          out["origin"]["value"], "New England")
    check("a block only the stage has is carried in too", out["arrival_year"]["value"], 1834)
    check("and it is seated where the stage seats it, so the byte comparison holds",
          list(out), ["id", "arrival", "arrival_year", "origin", "persons"])
    check("the mint's own fields are untouched", out["arrival"], mint["arrival"])

    unmarked = {"id": "hh_x", "origin": {"value": "Vermont", "confidence": "attested"}}
    out = carry(json.loads(json.dumps(mint)), unmarked)
    check("a value NO stage marks is not carried - it is the mint's to derive",
          out["origin"]["value"], None)

    out = carry(json.loads(json.dumps(mint)), {"id": "hh_x"})
    check("a record with nothing to carry comes back unchanged", out, mint)

    # the wiring, read from the source rather than trusted
    missing = [m for m in sorted(WIRED_MINTS)
               if CALL not in (ROOT / m).read_text(encoding="utf-8")]
    check("every mint that re-derives a household still carries", missing, [])
    return 1 if failures else 0


def cmd_check() -> int:
    missing = [m for m in sorted(WIRED_MINTS)
               if CALL not in (ROOT / m).read_text(encoding="utf-8")]
    if missing:
        for m in missing:
            print(f"  FAIL {m} re-derives a household record and does not call {CALL} - its "
                  f"next --build would delete every block a reconstruction stage owns")
        return 1
    marked = 0
    stages: dict = {}
    for path in sorted(HOUSEHOLDS.glob("hh_*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for block in stage_blocks(doc).values():
            marked += 1
            key = block[MARKER]
            stages[key] = stages.get(key, 0) + 1
    print(f"  OK: {len(WIRED_MINTS)} mint(s) carry; {marked} block(s) in "
          f"data/residents/ are owned by a reconstruction stage "
          f"({', '.join(f'{k}: {v}' for k, v in sorted(stages.items())) or 'none yet'})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return cmd_check()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
