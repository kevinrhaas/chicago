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

T-1653 CARRIES THE SAME PROMISE ONE LINK FURTHER. A `--only` bake built one roof and
then ran `tools/web_derivatives.sh` over every master in the tree — ~570, two npx
start-ups each, about eighteen minutes — because nothing told the derivative step
what had been built. Now build.py writes the masters it wrote (`--wrote`) and bake.sh
hands that list to `web_derivatives.sh --only a.glb,b.glb`. That is three files
agreeing about one selection, so this gate holds all three texts, asserts no master
name under assets/gltf/ carries the comma the list splits on, and its self-test runs
the derivative step itself on a fixture with a stub toolchain: a list derives its
members and nothing else, merges its record, and a name no master answers to or an
empty list is refused before a byte is written.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from common.selection import parse_only, refusal, selects  # noqa: E402

BAKE_SH = ROOT / "tools" / "bake.sh"
BUILD_PY = ROOT / "generators" / "build.py"
WEB_SH = ROOT / "tools" / "web_derivatives.sh"
MASTERS = ROOT / "assets" / "gltf"
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
    # T-1653: the derivative step's selection is the list the build wrote.
    if not re.search(r'build\.py -- "\$@" --wrote\b', bake_sh):
        rep.append("tools/bake.sh no longer asks build.py for the masters it wrote "
                   "(`--wrote`), so a `--only` bake cannot tell the derivative step "
                   "what it built and re-derives the whole town (T-1653).")
    if not re.search(r"^\s*tools/web_derivatives\.sh --only\b", bake_sh, re.M):
        rep.append("tools/bake.sh no longer passes a selection to "
                   "tools/web_derivatives.sh, so `--only <id>` derives every master in "
                   "the tree — ~18 minutes for one roof (T-1653).")
    if '"--wrote"' not in build_py:
        rep.append("generators/build.py no longer takes `--wrote`, which is the only "
                   "record of which phases and versions a selection resolved to "
                   "(T-1653).")
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
    masters = [p.relative_to(MASTERS).as_posix() for p in MASTERS.rglob("*.glb")]
    commas = [one for one in masters if "," in one]
    if commas:
        rep.append("these masters' paths contain a comma, which is the separator "
                   "`tools/web_derivatives.sh --only a,b` splits on (T-1653): "
                   + ", ".join(commas))
    return rep


# ------------------------------------------------- the derivative step, run (T-1653)
# A stand-in for the pinned toolchain: it answers `--version` with the pin, and for
# `optimize` / `meshopt` writes a small file carrying the pinned stamp, so the step
# under test is the committed script and only the npx it calls is fake. The same
# construction tools/test_glessner_v4_package_producer.py uses.
STUB_NPX = """#!/usr/bin/env python3
import os, sys
from pathlib import Path
args = sys.argv[1:]
args = args[args.index("gltf-transform") + 1:]
if os.environ.get("FIXTURE_TRANSFORM") == "unavailable":
    raise SystemExit(1)
if args[0] == "--version":
    print("4.5.0"); raise SystemExit()
command, source, target = args[:3]
Path(target).write_bytes(b"glTF-Transform v4.5.0 " + command.encode())
"""


def run_step(script: str, names: list[str], *args: str, mode: str = "optimized"):
    """Run a copy of `script` (web_derivatives.sh's text) over fixture masters."""
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "tools").mkdir()
        (root / "tools" / "web_derivatives.sh").write_text(script)
        # A full run asks for the ignored Glessner v4 master before it starts; the
        # fixture has none to recover, so its recovery is a no-op here.
        (root / "tools" / "recover_glessner_v4.py").write_text("")
        (root / "bin").mkdir()
        npx = root / "bin" / "npx"
        npx.write_text(STUB_NPX)
        npx.chmod(0o755)
        (root / "assets" / "gltf").mkdir(parents=True)
        for name in names:
            (root / "assets" / "gltf" / name).write_bytes(name.encode() * 400)
        (root / "assets" / "manifest.web.json").write_text(json.dumps(
            {"masters": {"untouched.glb": "kept"}}))
        env = {**os.environ, "PATH": f"{root / 'bin'}{os.pathsep}{os.environ['PATH']}",
               "FIXTURE_TRANSFORM": mode}
        done = subprocess.run(["bash", "tools/web_derivatives.sh", *args], cwd=root,
                              env=env, capture_output=True, text=True)
        web = root / "assets" / "web"
        made = sorted(p.name for p in web.glob("*.glb")) if web.is_dir() else []
        record = json.loads((root / "assets" / "manifest.web.json").read_text())
        return done.returncode, made, sorted(record.get("masters", {}))


def audit_step(script: str) -> list[str]:
    """What the derivative step does with a selection, run rather than read."""
    rep: list[str] = []
    town = ["a__p.glb", "b__p.glb", "c__p.glb", "terrain__e.glb"]
    code, made, record = run_step(script, town, "--only", "a__p.glb,terrain__e.glb")
    if code != 0 or made != ["a__p.glb", "terrain__e.glb"]:
        rep.append(f"`--only a,b` derived {made} (exit {code}), not exactly the two "
                   "masters it named.")
    elif record != ["a__p.glb", "terrain__e.glb", "untouched.glb"]:
        rep.append(f"`--only a,b` left the record reading {record}: a selection must "
                   "merge its masters in and keep every other entry.")
    code, made, _ = run_step(script, town, "--only", "a__p.glb", mode="unavailable")
    if code != 0 or made != ["a__p.glb"]:
        rep.append(f"without the toolchain, `--only a` copied {made} (exit {code}) — the "
                   "fallback must copy the selection, not every master in the tree.")
    code, made, record = run_step(script, town, "--only", "a__p.glb,nobody__p.glb")
    if code == 0 or made:
        rep.append(f"`--only` naming a master that does not exist ran (exit {code}, "
                   f"wrote {made}); it must be refused before any work.")
    code, made, _ = run_step(script, town, "--only", "")
    if code == 0 or made:
        rep.append(f"`--only \"\"` ran (exit {code}, wrote {made}); an empty selection "
                   "is not the whole town and must be refused.")
    code, made, record = run_step(script, town)
    if code != 0 or made != sorted(town) or record != sorted(town):
        rep.append(f"with no selection the step derived {made} and recorded {record} "
                   f"(exit {code}); a full run derives every master and rewrites the "
                   "record whole.")
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

    print("\n  -- the derivative step does what a selection says (T-1653)")
    web_sh = WEB_SH.read_text()
    live_step = audit_step(web_sh)
    if live_step:
        for line in live_step:
            fails.append(f"the committed derivative step: {line}")
    else:
        print("  ok    a list derives its members, an unknown or empty one is refused")

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

    arm("bake.sh stops asking build.py what it wrote (T-1653)",
        bake_sh.replace(" --wrote ", " "), build_py, "no longer asks build.py")
    arm("bake.sh derives the whole town again (T-1653)",
        re.sub(r'tools/web_derivatives\.sh --only "[^\n]*', "tools/web_derivatives.sh",
               bake_sh), build_py, "no longer passes a selection")
    arm("build.py drops --wrote (T-1653)",
        bake_sh, build_py.replace('"--wrote"', '"--written"'), "no longer takes `--wrote`")

    def arm_step(label: str, broken: str, expect: str) -> None:
        if broken == web_sh:
            fails.append(f"{label}: the break did not apply to web_derivatives.sh")
            return
        rep = audit_step(broken)
        if any(expect in line for line in rep):
            print(f"  ok    {label}")
        else:
            fails.append(f"{label}: NOT caught (findings: {rep})")

    arm_step("the step ignores the selection",
             web_sh.replace('[ -z "$ONLY" ] && return 0', "return 0"), "not exactly the two")
    arm_step("the fallback copies every master again",
             web_sh.replace('    cp -f "$f" "$OUT/"\n',
                            '    cp -f assets/gltf/*.glb "$OUT/"\n'), "the fallback must")
    arm_step("an unknown name is skipped rather than refused",
             web_sh.replace('[ -f "assets/gltf/$name" ] || missing=', ': || missing='),
             "must be refused before any work")
    arm_step("an empty selection reads as the whole town",
             web_sh.replace('elif [ -n "$ONLY_GIVEN" ]; then', 'elif false; then'),
             "is not the whole town")
    arm_step("a selection rewrites the record whole",
             web_sh.replace("if only and record.exists():", "if False:"),
             "must merge its masters in")
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
