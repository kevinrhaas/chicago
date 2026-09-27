"""The `--only` form bake.sh documents is the form build.py implements (T-1652).

    python3 tools/check_only_selection.py              report
    python3 tools/check_only_selection.py --gate       exit 1 on a disagreement
    python3 tools/check_only_selection.py --self-test   break each assertion

WHY A GATE AND NOT JUST A FIX. The defect this stands beside was not a wrong
line of code; it was two files disagreeing about what a flag means, with nothing
holding them together. `tools/bake.sh` documented `--only a,b,c` and passed
`"$@"` through; `generators/build.py` compared `st["id"] != args.only` for
equality, so the documented form matched none of 422 ids, built nothing, and
exited 1 saying only `0 asset(s) built`. The usage was a promise one file made
about another file's behaviour, and a promise with no gate behind it is the same
shape as AGENTS.md's changelog rule before T-0409: true until someone edits the
other file.

So this is the same construction as `tools/check_haze_reach.mjs`, which holds a
renderer literal against the terrain box that determines it: read both texts,
assert they still say the same thing, and fail where they part. The rule itself
— what a comma list means, and what an unknown id costs — lives once in
`generators/common/selection.py`, which cannot be imported inside a gate if it
imports bpy, and does not.

It also asserts the precondition the comma form needs from the DATA: no
structure id may contain a comma. An id with a comma in it would make `a,b`
ambiguous between one structure and two, and no amount of careful parsing
recovers from that — the separator has to be a character the ids cannot use.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from common.selection import parse_only, refusal, selects  # noqa: E402

BAKE_SH = ROOT / "tools" / "bake.sh"
BUILD_PY = ROOT / "generators" / "build.py"
STRUCTURES = ROOT / "data" / "structures"

# The documented form, written exactly as bake.sh's usage writes it. This literal
# is the contract; if the usage is reworded, this is the line to reword with it.
DOC_FORM = "--only a,b,c"


def audit_texts(bake_sh: str, build_py: str) -> list[str]:
    """The disagreements between what bake.sh promises and what build.py does."""
    rep: list[str] = []

    if DOC_FORM not in bake_sh:
        rep.append(f"tools/bake.sh no longer documents `{DOC_FORM}`. If the comma "
                   "form was withdrawn, withdraw it from build.py and from "
                   "generators/common/selection.py in the same change — and from "
                   "this gate, which is the record that it was ever promised.")
    if '"$@"' not in bake_sh:
        rep.append("tools/bake.sh no longer passes `\"$@\"` through to build.py, so "
                   "its own usage is no longer a statement about build.py's flags. "
                   "Whatever it does instead has to be documented where it happens.")
    if DOC_FORM not in build_py:
        rep.append(f"generators/build.py does not document `{DOC_FORM}` in its "
                   "module docstring, which is the only usage a caller running it "
                   "under Blender directly (as bake.sh does) will read.")

    # Anchored at column 0: build.py imports at module level, and an anchored
    # match is what makes the assertion fire on an import that has been COMMENTED
    # OUT rather than deleted — which is how a rule usually stops being read.
    if not re.search(r"^from\s+common\.selection\s+import", build_py, re.M):
        rep.append("generators/build.py does not import the selection rule from "
                   "common.selection. A second copy of the rule is how the first "
                   "one drifted; see generators/common/phases.py for the same "
                   "lesson learned on `drawn_by`.")
    if re.search(r"!=\s*args\.only", build_py):
        rep.append("generators/build.py compares a structure id against `args.only` "
                   "for EQUALITY. That is the T-1652 defect exactly: a comma list "
                   "matches no id, so the documented form silently builds nothing.")
    if re.search(r"if\s+args\.only\b", build_py):
        rep.append("generators/build.py tests `args.only` for truth. `--only \"\"` is "
                   "falsy, so that test reads an empty selection — an unexpanded "
                   "shell variable — as no selection at all, and bakes the whole "
                   "town. Ask `parse_only(...) is None` for absence instead.")
    return rep


def audit_rule() -> list[str]:
    """The rule still means what the documented form says, and the ids allow it."""
    rep: list[str] = []

    example = DOC_FORM.split(None, 1)[1]
    got = parse_only(example)
    if got != ["a", "b", "c"]:
        rep.append(f"the documented example `{example}` reads as {got!r}, not three ids.")
    if parse_only(None) is not None:
        rep.append("no flag no longer reads as no selection.")
    if parse_only("") is None:
        rep.append("an empty selection no longer reads differently from no selection.")
    if refusal(["nobody_answers_to_this"], ["a", "b"]) is None:
        rep.append("an id no record answers to is no longer refused.")
    if not selects(None, "anything"):
        rep.append("no selection no longer builds every record.")

    ids = []
    for path in sorted(STRUCTURES.glob("*.json")):
        try:
            ids.append(json.loads(path.read_text())["id"])
        except (ValueError, KeyError) as e:
            rep.append(f"{path.name} has no readable id: {e}")
    commas = [one for one in ids if "," in one]
    if commas:
        rep.append("these structure ids contain a comma, which is the separator the "
                   f"documented `{DOC_FORM}` form splits on, so a selection naming "
                   f"them is ambiguous: {', '.join(commas)}")
    if not ids:
        rep.append(f"no structure records found under {STRUCTURES}.")
    return rep


# ----------------------------------------------------------------------- self-test

def self_test() -> int:
    fails: list[str] = []
    bake_sh = BAKE_SH.read_text()
    build_py = BUILD_PY.read_text()

    def arm(label: str, bake: str, build: str, expect: str) -> None:
        rep = audit_texts(bake, build)
        if any(expect in line for line in rep):
            print(f"  ok    {label}")
        else:
            fails.append(f"{label}: NOT caught (findings: {rep})")

    print("\n  -- the committed pair agrees")
    live = audit_texts(bake_sh, build_py) + audit_rule()
    if live:
        for line in live:
            fails.append(f"the committed tree disagrees: {line}")
    else:
        print("  ok    bake.sh's documented form is the form build.py implements")

    print("\n  -- and each assertion fires when the pair is broken")
    arm("the usage drops the comma form",
        bake_sh.replace(DOC_FORM, "--only <id>"), build_py, "no longer documents")
    arm("bake.sh stops passing its arguments through",
        bake_sh.replace('"$@"', "--all"), build_py, "no longer passes")
    arm("build.py stops documenting the form",
        bake_sh, build_py.replace(DOC_FORM, "--only <id>"), "does not document")
    arm("build.py grows its own copy of the rule",
        bake_sh, build_py.replace("from common.selection import", "# from common.selection import"),
        "does not import the selection rule")
    arm("the equality comparison comes back (the T-1652 defect)",
        bake_sh, build_py + '\n        if args.xonly and st["id"] != args.only:\n',
        "for EQUALITY")
    arm("the falsy-empty test comes back",
        bake_sh, build_py + "\n    if args.only:\n        pass\n", "tests `args.only` for truth")

    print()
    for f in fails:
        print(f"  FAIL  {f}")
    print("ONLY-FORM SELF-TEST " + ("PASS" if not fails else "FAIL"))
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gate", action="store_true", help="exit 1 on a disagreement")
    ap.add_argument("--self-test", action="store_true",
                    help="break each assertion and prove it fires")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    rep = audit_texts(BAKE_SH.read_text(), BUILD_PY.read_text()) + audit_rule()
    for line in rep:
        print(f"  FAIL  {line}")
    if rep and args.gate:
        return 1
    print(f"ONLY-FORM PASS — `{DOC_FORM}` is documented by tools/bake.sh, "
          "implemented by generators/build.py through common.selection, and "
          "unambiguous over every structure id"
          if not rep else "ONLY-FORM FINDINGS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
