#!/usr/bin/env python3
"""T-2234 — walk the family cycle until a lap moves nothing.

    python3 tools/settle_family_cycle.py --build           lap the cycle until a lap moves nothing
    python3 tools/settle_family_cycle.py --build --strict  …then the book with its owner gate, and
                                                           all six stages' --check, failing on red
    python3 tools/settle_family_cycle.py --check           the step sits where the manifest needs it,
                                                           and check.sh gates all six stages
    python3 tools/settle_family_cycle.py --self-test  the lap logic stops, and refuses, when it should

WHY THIS EXISTS. Six derived stages read each other in a ring, and no linear order of
`tools/derived_manifest.json` settles them:

    reconstruct_modelled_families.py   deals a wife and children to the men heading a house,
                                       and folds a refused woman-headed house into a married
                                       one (T-2020); it re-derives the order book as it goes
    reconstruct_women_children.py      deals the women and children the book still orders
                                       into houses of their own, and applies the re-family
                                       rule's moves to the cards it deals
    reconstruct_trade_households.py    the same for the trade households
    model_refamily_rule.py             reads the cards and the book and says WHICH held
                                       people move, naming each house and person
    refamily_moves_1835.py             writes the book's ledger row for every move a card
                                       carries
    build_order_book_1835.py           counts every cell, and refuses a cell left owing
                                       under a ticket nobody can claim

A sex reading that withdraws a modelled family frees the wife and child cells it filled.
The book then orders them again, women-and-children deals them, and the draw is
sequential and seeded, so every house after the first freed cell can change (T-2232 on
2026-10-09: 23 of 124 houses re-dealt and 2 new ones). The committed rule still names the
OLD houses, so women-and-children refuses it ("the rule re-families 3 of the 3 people on
hh_rc_gilbert_abigail"). The rule can't be rebuilt first, because it reads the deal it
refuses. The book can't build first either, because the freed cells read as owing under
the done T-1174 until the deal fills them.

THE LAP, and why it is in this order:

  1. the resident index, then modelled families, then the index again. Families unlinks a
     printed wife's card and the book reads the index, so a stale index crashes the next
     reader on a missing file (T-2234's first measurement).
  2. the book, with its live-owner gate OFF. Women-and-children reads its quota from the
     book, and the gate is a claim about the FINISHED chain (`cmd_build`'s own docstring).
  3. women-and-children, then trades, each with the committed rule. If a stage refuses the
     rule, the stage is dealt again with the rule's moves set aside. That is safe because
     a move is applied LAST, after the draw, and changes only the cell a card states,
     never who is on it (`reconstruct_women_children.refamily`). So the deal without the
     moves is the same deal.
  4. the index and the book again (gate off), then the rule, rebuilt from that deal.
  5. women-and-children and trades again, now with the rule that names their own houses;
     then the moves ledger, the index and the book.

A lap is SETTLED when it changes no byte of anything the cycle writes. Every stage runs
in its own process, because the stages cache what they read at import. Every stage that
re-derives the book mid-chain runs with the owner gate off, which is the one thing the
prelude changes (`OWNERS_GATE_OFF`).

SNAPSHOT HYGIENE. A refused stage can write part of its output before it refuses. The
lap that measured this (#554, 2026-10-09) ran six ad hoc laps that compounded: one cell
climbed 32, 34, 38, 42, 46, 50 against an order of 16. So the tree the cycle writes is
copied before the first lap. On a refusal that is not one of the stale rule's, on an
oscillation (a lap returns to a state an earlier lap left), or on running out of laps,
it is put back byte for byte, and the step fails, naming the stage and its last line.

WHAT IT DOES NOT DO. It rebuilds nothing above modelled families. The sex pass and
everything before it are the manifest's own steps, and this one sits directly below the
three stages it drives. It edits no stage's arithmetic and loosens no gate: the owner
gate is off only mid-chain, and the manifest's own book step re-derives the book with
it on, below this one. `--build --strict` does both here and fails on any red.

WHAT IT NEEDED BESIDES THE LAPS (T-2234, measured on #554). The laps alone did not
settle #554. The frozen family ruling (T-2021) still ordered the wife and children cells
of two houses it had admitted that T-2232's readings dissolved: Anne Maria Barney is read
female, and Charlotte Wesencraft is a printed bride whose card folds into her husband's
house. Those five cells read as owing. Women-and-children drew them as its own quota, and
the refused cell they sit in overran the quota it was drawn against. That was the 32, 34,
… 50 climb. `reconstruct_modelled_families.withdrawn_admissions` now takes such a house's
order with it (nobody is ruled in its place), and the book reads that off the stage's
ledger. With that in place #554 settles in ONE moving lap, and women-and-children's deal
does not move at all.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"

# Everything any stage of the cycle writes. Measured with `git status` after every stage
# on #554's branch and on dev. The households, the index and the derived reconstruction
# files sit under the first three. The book's and the rule's reports are top-level files
# in docs/RESEARCH, and copying that whole directory would mean 252 MB of research
# workbooks the cycle never touches.
WRITTEN_DIRS = ("data/residents", "data/reconstruction", "data/research/residents")
WRITTEN_GLOBS = ("docs/RESEARCH/*.md",)

MAX_LAPS = 6

# Run inside every stage's process. A filler re-deriving the book mid-chain takes the
# owner gate off, exactly as `build_order_book_1835.cmd_build(owners_gate=False)` is
# documented for; women-and-children, trades and families all call `ob.cmd_build()` bare,
# so the module function is wrapped before they import it.
#
# AND THE INDEX IS REBUILT BEFORE EVERY ONE OF THEM. The book reads data/residents/index.json,
# and a stage can unlink a card before it re-derives the book. Modelled families does this to
# a printed bride's own card (T-2234's first measurement: `hh_wesencraft_charlotte`,
# FileNotFoundError). So the book never reads an index that names a card that is gone.
OWNERS_GATE_OFF = (
    "import sys, subprocess; sys.path.insert(0, {tools!r}); "
    "import build_order_book_1835 as ob; _b = ob.cmd_build; "
    "_i = lambda: subprocess.run([sys.executable, {index!r}, '--write'], check=True, "
    "capture_output=True); "
    "ob.cmd_build = lambda owners_gate=False: (_i(), _b(owners_gate=False))[1]; "
)
# …and, for the deal with the STALE moves set aside, women-and-children applies only the
# moves that still describe a house it dealt, and drops the rest. A move still applies when
# it names exactly the people now on the house, sends them to one division, and moves them
# out of the division the house was dealt in. Those are the three tests `refamily` raises
# on, in the same words. Setting EVERY move aside is wrong, and was measured: on #554 it
# left persons/female/20_29/north/family/none at 31 of 16, past the quota the cell was
# drawn against, because the moves still valid are what keep the held surplus inside it.
# The trades stage has no per-house test to filter on, so its set-aside reads no moves.
MOVES_ASIDE = {
    "women": (
        "_r = m.refamily; "
        "m.refamily = lambda made, moves: _r(made, {{h: rows for h, rows in moves.items() "
        "if h not in made or ({{r['person'] for r in rows}} == "
        "{{p['id'] for p in made[h]['persons']}} "
        "and len({{r['to_bucket'].split('/')[3] for r in rows}}) == 1 "
        "and {{r['from_bucket'].split('/')[3] for r in rows}} == {{made[h]['division']}})}}); "
    ),
    "trades": "m.refamily_moves = lambda: {{}}; ",
}

STAGE = {
    "index": ("rebuild_resident_index", None),
    "families": ("reconstruct_modelled_families", "build"),
    "book": ("build_order_book_1835", "cmd_build"),
    "women": ("reconstruct_women_children", "build"),
    "trades": ("reconstruct_trade_households", "build"),
    "rule": ("model_refamily_rule", "cmd_build"),
    "moves": ("refamily_moves_1835", "cmd_build"),
}

# What a stage says when it refuses the RULE rather than the town: the two stages that
# carry moves check that a move names exactly the people the deal put on the house, in
# the division it dealt it in, and the trades stage checks the heads it re-familied
# against the cards. Anything else is a real refusal and stops the cycle.
STALE_RULE = (
    "the rule re-families",
    "the rule sends",
    "out of a division this stage did not deal",
    "heads re-familied",
    "carry a move",
)

LAP = (
    ("index", False), ("families", False), ("index", False), ("book", False),
    ("women", True), ("trades", True), ("index", False), ("book", False),
    ("rule", False),
    ("women", False), ("trades", False), ("moves", False), ("index", False),
    ("book", False),
)

CHECKS = (
    "reconstruct_modelled_families", "reconstruct_women_children",
    "reconstruct_trade_households", "refamily_moves_1835", "build_order_book_1835",
    "model_refamily_rule",
)


class Refused(Exception):
    def __init__(self, stage: str, tail: str):
        super().__init__(f"{stage}: {tail}")
        self.stage, self.tail = stage, tail


def program(stage: str, aside: bool) -> list[str]:
    module, call = STAGE[stage]
    if stage == "index":
        return [sys.executable, str(TOOLS / f"{module}.py"), "--write"]
    body = OWNERS_GATE_OFF.format(tools=str(TOOLS),
                                  index=str(TOOLS / "rebuild_resident_index.py"))
    body += f"import {module} as m; "
    if aside:
        body += MOVES_ASIDE[stage].format()
    body += f"rc = m.{call}(); sys.exit(rc or 0)"
    return [sys.executable, "-c", body]


def run(stage: str, aside: bool = False) -> None:
    p = subprocess.run(program(stage, aside), cwd=ROOT, capture_output=True, text=True)
    if p.returncode:
        lines = [ln for ln in (p.stdout + p.stderr).splitlines() if ln.strip()]
        raise Refused(stage, lines[-1].strip() if lines else f"exit {p.returncode}")


def stale_rule(refusal: Refused) -> bool:
    return refusal.stage in ("women", "trades") and any(s in refusal.tail for s in STALE_RULE)


def written_files() -> list[Path]:
    out = []
    for d in WRITTEN_DIRS:
        out += [p for p in (ROOT / d).rglob("*") if p.is_file()]
    for g in WRITTEN_GLOBS:
        out += [p for p in ROOT.glob(g) if p.is_file()]
    return sorted(out)


def fingerprint() -> str:
    h = hashlib.sha256()
    for p in written_files():
        h.update(str(p.relative_to(ROOT)).encode())
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


class Snapshot:
    """The written tree as it stood before the first lap, put back on any failure."""

    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="family-cycle-"))
        self.files = written_files()
        for p in self.files:
            dst = self.dir / p.relative_to(ROOT)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)

    def restore(self) -> None:
        keep = {p.relative_to(ROOT) for p in self.files}
        for p in written_files():
            if p.relative_to(ROOT) not in keep:
                p.unlink()
        for rel in keep:
            dst = ROOT / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.dir / rel, dst)

    def drop(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)


def lap(log) -> list[str]:
    """One lap. Returns the stages that had to set a stale rule aside."""
    aside = []
    for stage, may_set_aside in LAP:
        try:
            run(stage)
        except Refused as r:
            if not (may_set_aside and stale_rule(r)):
                raise
            log(f"    {stage}: the committed rule names houses this deal no longer "
                f"makes ({r.tail}); dealt with its moves set aside")
            run(stage, aside=True)
            aside.append(stage)
    return aside


def settle(laps: int, log, fp=fingerprint, one_lap=lap) -> int:
    """Lap until a lap moves nothing. Returns the number of laps that moved something.

    Raises Refused on a refusal, an oscillation or running out of laps; the caller puts
    the tree back."""
    seen = [fp()]
    for n in range(1, laps + 1):
        aside = one_lap(log)
        now = fp()
        if now == seen[-1]:
            if aside:
                # A lap that had to set the rule aside rewrote the rule after it, so an
                # unchanged fingerprint here would mean the rule came back as stale as it
                # went in. That is not a fixpoint.
                raise Refused("cycle", f"lap {n} set the rule aside and changed nothing")
            log(f"  lap {n}: moved nothing — settled")
            return n - 1
        if now in seen:
            raise Refused("cycle", f"lap {n} returned to the state lap "
                                   f"{seen.index(now)} left: the cycle oscillates")
        log(f"  lap {n}: moved" + (f" (rule set aside in {', '.join(aside)})" if aside else ""))
        seen.append(now)
    raise Refused("cycle", f"did not settle in {laps} laps")


def final_gate(log, strict: bool) -> list[str]:
    """Every stage's own --check on what the cycle settled to. With `strict`, the book is
    first re-derived WITH its owner gate, which is the gate's claim about the finished chain."""
    red = []
    if strict:
        p = subprocess.run([sys.executable, str(TOOLS / "build_order_book_1835.py"), "--build"],
                           cwd=ROOT, capture_output=True, text=True)
        if p.returncode:
            red.append("build_order_book_1835 --build: "
                       + ((p.stdout + p.stderr).strip().splitlines() or ["?"])[-1])
    for module in CHECKS:
        p = subprocess.run([sys.executable, str(TOOLS / f"{module}.py"), "--check"],
                           cwd=ROOT, capture_output=True, text=True)
        if p.returncode:
            fails = [ln.strip() for ln in (p.stdout + p.stderr).splitlines() if "FAIL" in ln]
            red.append(f"{module} --check: " + (fails[0] if fails else f"exit {p.returncode}"))
    for r in red:
        log(f"  {'RED ' if strict else 'NOTE'}  {r}")
    return red


def cmd_build(strict: bool = False) -> int:
    """Settle the cycle. Fails when it does not settle, and puts the tree back.

    WITHOUT `--strict` IT DOES NOT FAIL ON A RED CHECK, and that is deliberate. As a manifest
    step it sits at the foot of the residents stages, and the book's own step (and the
    readers between) sit far below it. A gate read here would be one step early on a merged
    tree, and a step that refuses halts `rederive.mjs --run` with the tree half rebuilt. So a
    red check is printed as a NOTE, and tools/check.sh, which runs every stage's own
    `--check` after the whole sequence, is the proof. `--strict` is the demonstration form
    T-2234's acceptance names: the book re-derived WITH its owner gate, then the six checks,
    and any red fails it."""
    log = print
    snap = Snapshot()
    try:
        moved = settle(MAX_LAPS, log)
    except Refused as r:
        snap.restore()
        snap.drop()
        print(f"FAIL the family cycle did not settle — {r}. The tree is put back as it "
              f"was before the first lap.")
        return 1
    snap.drop()
    red = final_gate(log, strict)
    if red and strict:
        print(f"FAIL the family cycle settled after {moved} moving lap(s), but {len(red)} "
              f"gate(s) are red on what it settled to (the tree is left settled so the red "
              f"can be read)")
        return 1
    print(f"OK: the family cycle settled after {moved} moving lap(s)"
          + ("; the book (owner gate on) and all six stages re-derive" if strict else
             f"; {6 - len(red)} of the six stages re-derive here"
             + (" (check.sh is the gate)" if red else "")))
    return 0


def cmd_check() -> int:
    """The step's own invariants, which are what make its fixpoint provable.

    Whether the layer IS at the fixpoint is not asked again here, because tools/check.sh
    already runs each of the six stages' own `--check`. Asking all six a second time would
    add about 25 s to a gate that already runs close to the lap's 590 s foreground limit.
    What only this tool can hold is that those six lines are there to ask it, and that the
    step sits where the manifest needs it: below the stages it drives, and above the book's
    own step, which re-derives the book with the owner gate on."""
    problems = []
    gate = (TOOLS / "check.sh").read_text(encoding="utf-8")
    for module in CHECKS:
        if f"python3 tools/{module}.py --check" not in gate:
            problems.append(f"tools/check.sh never runs {module}.py --check, so nothing "
                            f"proves the stage this cycle drives re-derives")
    manifest = json.loads((TOOLS / "derived_manifest.json").read_text(encoding="utf-8"))
    at = {s["command"][1]: i for i, s in enumerate(manifest["steps"])}
    me = at.get("tools/settle_family_cycle.py")
    if me is None:
        problems.append("tools/derived_manifest.json has no step for this tool")
    else:
        for module in ("reconstruct_modelled_families", "reconstruct_women_children",
                       "reconstruct_trade_households"):
            if at.get(f"tools/{module}.py", 10 ** 6) > me:
                problems.append(f"the step sits above {module}.py, which it drives")
        if at.get("tools/build_order_book_1835.py", -1) < me:
            problems.append("the step sits below the book's own step, so nothing re-derives "
                            "the book with its owner gate after it")
    for p in problems:
        print(f"  FAIL {p}")
    if problems:
        return 1
    print("OK: the family cycle's step sits below its stages and above the book, and "
          "check.sh asks all six stages to re-derive")
    return 0


def cmd_self_test() -> int:
    fails = []

    def expect(name, fn, want):
        try:
            got = fn()
        except Refused as r:
            got = ("refused", r.tail)
        ok = want(got)
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}: {got}")
        if not ok:
            fails.append(name)

    def scripted(states, aside_on=()):
        """A fake tree whose fingerprint after lap n is states[n]."""
        it = {"n": 0}

        def fp():
            return states[it["n"]]

        def one(_log):
            it["n"] += 1
            return ["women"] if it["n"] in aside_on else []
        return fp, one

    quiet = lambda *_: None
    fp, one = scripted(["a", "b", "c", "c"])
    expect("stops on the first lap that moves nothing", lambda: settle(6, quiet, fp, one),
           lambda g: g == 2)
    fp, one = scripted(["a", "a"])
    expect("an already-settled tree takes one lap and moves nothing",
           lambda: settle(6, quiet, fp, one), lambda g: g == 0)
    fp, one = scripted(["a", "b", "c", "b"])
    expect("refuses a lap that returns to an earlier lap's state",
           lambda: settle(6, quiet, fp, one),
           lambda g: g[0] == "refused" and "oscillates" in g[1])
    fp, one = scripted(["a", "b", "a"])
    expect("…including the state it started from",
           lambda: settle(6, quiet, fp, one),
           lambda g: g[0] == "refused" and "oscillates" in g[1])
    fp, one = scripted(list("abcdefgh"))
    expect("refuses a cycle that runs out of laps", lambda: settle(3, quiet, fp, one),
           lambda g: g[0] == "refused" and "did not settle in 3" in g[1])
    fp, one = scripted(["a", "a"], aside_on=(1,))
    expect("a lap that set the rule aside is not a fixpoint even if nothing moved",
           lambda: settle(6, quiet, fp, one),
           lambda g: g[0] == "refused" and "set the rule aside" in g[1])
    expect("a stale-rule refusal from women-and-children may be set aside",
           lambda: stale_rule(Refused("women", "FAIL the rule re-families 3 of the 3 "
                                               "people on hh_x: a house moves whole")),
           lambda g: g is True)
    expect("the same words from a stage that carries no moves may not",
           lambda: stale_rule(Refused("book", "FAIL the rule re-families 3 of 3")),
           lambda g: g is False)
    expect("a refusal about the town is never set aside",
           lambda: stale_rule(Refused("women", "FAIL the order book's fills are overfilled")),
           lambda g: g is False)
    expect("the prelude takes the owner gate off and nothing else",
           lambda: "owners_gate=False" in " ".join(program("women", False))
           and "refamily_moves" not in " ".join(program("women", False)),
           lambda g: g is True)
    expect("the set-aside deal drops only the moves that no longer fit a house",
           lambda: "m.refamily = lambda made, moves" in " ".join(program("women", True))
           and "m.refamily_moves = lambda: {}" in " ".join(program("trades", True)),
           lambda g: g is True)
    expect("the rule is rebuilt after the first deal and before the second",
           lambda: [s for s, _ in LAP].index("rule") > [s for s, _ in LAP].index("women")
           and [s for s, _ in LAP[9:]].count("women") == 1,
           lambda g: g is True)
    expect("only the first deal of a lap may set the rule aside",
           lambda: [s for s, a in LAP if a], lambda g: g == ["women", "trades"])

    # Snapshot hygiene on a real directory: a file changed, one added and one removed all
    # come back exactly.
    global ROOT, WRITTEN_DIRS, WRITTEN_GLOBS
    saved = ROOT, WRITTEN_DIRS, WRITTEN_GLOBS
    with tempfile.TemporaryDirectory() as tmp:
        ROOT = Path(tmp)
        WRITTEN_DIRS, WRITTEN_GLOBS = ("d",), ("r/*.md",)
        (ROOT / "d" / "sub").mkdir(parents=True)
        (ROOT / "r").mkdir()
        (ROOT / "d" / "a.json").write_text("a")
        (ROOT / "d" / "sub" / "b.json").write_text("b")
        (ROOT / "r" / "x.md").write_text("x")
        before = fingerprint()
        snap = Snapshot()
        (ROOT / "d" / "a.json").write_text("changed")
        (ROOT / "d" / "sub" / "b.json").unlink()
        (ROOT / "d" / "new.json").write_text("new")
        (ROOT / "r" / "x.md").write_text("y")
        moved = fingerprint() != before
        snap.restore()
        snap.drop()
        expect("a snapshot puts back a changed, a removed and an added file",
               lambda: (moved, fingerprint() == before), lambda g: g == (True, True))
    ROOT, WRITTEN_DIRS, WRITTEN_GLOBS = saved

    if fails:
        print(f"FAIL {len(fails)} self-test case(s)")
        return 1
    print("OK: settle_family_cycle self-test")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="with --build: the book with its owner gate, and fail on any red")
    args = ap.parse_args()
    if args.build:
        return cmd_build(args.strict)
    if args.check:
        return cmd_check()
    if args.self_test:
        return cmd_self_test()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
