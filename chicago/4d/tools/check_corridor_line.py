#!/usr/bin/env python3
"""Every reader of the platted grid says WHICH LINE its answer stands on.

T-0419, and the owner's ruling of 2026-09-21 that closed it. Two lines run down each
platted street of this town and they do not coincide:

* the **drawn** line — the committed centreline in `data/streets/1835.json`, which is also
  the block grid's own control: `generate_plat_lots.block_edges` offsets THAT line by the
  platted half-module to get the block faces, so a block, a lot and the roof standing on it
  are all seated on it.
* the **control** line — the same corridor re-centred onto the street's committed survey
  control, which is what the owner's earlier ruling of 2026-08-29 (T-0009) asked the
  platted corridor to be derived from.

On the two streets whose control the drawn line does not reproduce they disagree, and the
disagreement is the whole of T-0419: `docs/CORRIDOR-LINES.md` records it, and
`tools/measure_corridor_strip.py --gate` pins the ground it leaves between them.

**The ruling did not pick one line. It required every reader to say which it took.** A
reader answering a question about a BLOCK, a lot or a roof stands on the drawn line; a
reader answering a question about where the PLAT put the roadway stands on the control
line; neither is the other's control. The fault T-0419 found was not a wrong line — it was
a reader that never said, so nobody could tell whether its number was about the plat or
about the town. This gate makes that fault impossible to reintroduce by accident: a module
that reads a line-bearing name and does not declare is red, and so is one whose declaration
disagrees with the calls it actually makes.

**How a module declares.** Two module-level constants, which is why they are greppable:

    CORRIDOR_LINE = "drawn"        # one of plat_corridors.LINES
    CORRIDOR_LINE_WHY = "…"        # what question this module is asking, in one line

**What the declaration is checked AGAINST is the syntax tree, not the text.** Every one of
these modules discusses both lines at length in its prose, so a grep for `from_control`
would report almost all of them as control readers. `ast` is read instead, so a line named
in a docstring or a comment is a line discussed and a line named in a call is a line taken.

The derivation, and each rule is here because a module in this tree exercises it:

* `control_offsets(…)`                → takes the CONTROL line.
* `corridors(from_control=<truthy>)`  → CONTROL. A non-literal argument counts as control,
  because `measure_corridor_intrusion` passes its own `FROM_CONTROL` flag: a module that
  CAN ask for the control line is a module that reads it.
* `corridors()` or `corridors(False)` → DRAWN.
* `block_edges(…)`                    → DRAWN, since the block faces are that line offset.
* `intrusion(polygon)`                → DRAWN: with no lanes of its own it builds the drawn
  ones. `intrusion(polygon, lanes)` counts as NEITHER — it follows the lanes it is handed,
  and every caller here hands it lanes it has already been charged for. Reading the second
  argument as "drawn" would have made `measure_corridor_intrusion`, the one tool in the
  project whose whole subject is the control line, declare the drawn one.

    tools/check_corridor_line.py              the census, one line per reader
    tools/check_corridor_line.py --gate       the check check.sh runs
    tools/check_corridor_line.py --json       the census, machine-readable
    tools/check_corridor_line.py --self-test  the assertions still fire when broken
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from plat_corridors import LINES  # noqa: E402

# The module that DERIVES both lines is not a reader of them, and it is the one place the
# vocabulary above lives. It is excluded by name rather than by a rule, because a rule that
# excluded "whatever defines corridors()" would excuse a second definition of them.
DEFINER = "tools/plat_corridors.py"

# The names that carry a line. `sampled`, `SAMPLE_M` and `QUOTED_M` do not: a polygon
# sampler and two quoting tolerances say nothing about which line a caller took, and a
# module that imports only those owes no declaration.
CORRIDOR_NAMES = {"corridors", "control_offsets", "intrusion"}
GRID_NAMES = {"block_edges"}
LINE_NAMES = CORRIDOR_NAMES | GRID_NAMES

SOURCE_MODULES = {"plat_corridors", "generate_plat_lots"}

# Where a reader can live. `tickets/` is a separate repository, `site/` is a generated
# mirror, and neither is this project's Python.
SEARCH = ("tools", "generators", "renderers")
SKIP_PARTS = {"__pycache__", "tickets", "site", "node_modules"}


def _calls(tree: ast.AST) -> list[tuple[str, list, list]]:
    """Every call in the tree as (name, positional args, keywords).

    `name` is the bare function name whether it was called bare or through a module alias,
    so `plat_corridors.control_offsets()` and `control_offsets()` are the same reading.
    """
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        else:
            continue
        out.append((name, node.args, node.keywords))
    return out


def _is_false(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is False


def read(path: Path, source: str | None = None) -> dict | None:
    """What one file imports, what lines it takes, and what it declares.

    Returns None for a file that reads no line-bearing name — it is not a reader and owes
    nothing. Syntax this project cannot parse is a different gate's business (`check.sh`
    runs one); here it is reported rather than swallowed.
    """
    text = path.read_text(encoding="utf-8") if source is None else source
    tree = ast.parse(text, filename=str(path))

    imported: set[str] = set()
    aliased = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in SOURCE_MODULES:
            imported |= {a.name for a in node.names} & LINE_NAMES
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name in SOURCE_MODULES:
                    aliased = True
    if not imported and not aliased:
        return None

    takes: set[str] = set()
    for name, args, keywords in _calls(tree):
        if name not in LINE_NAMES:
            continue
        if name == "control_offsets":
            takes.add("control")
        elif name == "block_edges":
            takes.add("drawn")
        elif name == "corridors":
            given = ([a for a in args[:1]]
                     + [k.value for k in keywords if k.arg == "from_control"])
            if not given:
                takes.add("drawn")
            elif all(_is_false(g) for g in given):
                takes.add("drawn")
            else:
                takes.add("control")
        elif name == "intrusion":
            # One argument means it derives its own lanes, and those are the drawn ones.
            # Two means it follows lanes the caller has already been charged for.
            if len(args) + len([k for k in keywords if k.arg == "lanes"]) < 2:
                takes.add("drawn")

    if not imported and not takes:
        # `import generate_plat_lots as south_division` and then only `FT_M` and
        # `ground_reading`: the two tier cutters import the module whole and take no line
        # from it. A whole-module import is only a reading when a line-bearing name is
        # actually called through it — otherwise every module that borrowed a foot-to-metre
        # constant would owe a declaration about a line it never asks for.
        return None

    declared, why = None, None
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if target.id == "CORRIDOR_LINE" and isinstance(node.value, ast.Constant):
            declared = node.value.value
        elif target.id == "CORRIDOR_LINE_WHY" and isinstance(node.value, ast.Constant):
            why = node.value.value

    expected = ("both" if takes == {"drawn", "control"}
                else next(iter(takes)) if takes else None)
    return {
        "path": path.as_posix(),
        "imports": sorted(imported) + (["<module>"] if aliased and not imported else []),
        "takes": sorted(takes),
        "expected": expected,
        "declared": declared,
        "why": why,
    }


def readers(root: Path | None = None) -> list[dict]:
    root = ROOT if root is None else root
    out = []
    for folder in SEARCH:
        base = root / folder
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            if SKIP_PARTS & set(path.parts):
                continue
            entry = read(path)
            if entry is None:
                continue
            entry["path"] = path.relative_to(root).as_posix()
            if entry["path"] == DEFINER:
                continue
            out.append(entry)
    return out


def faults(census: list[dict]) -> list[str]:
    """Every way a reader can fail to say which line it took."""
    out = []
    for r in census:
        where = r["path"]
        if r["declared"] is None:
            out.append(f"{where}: reads {', '.join(r['imports'])} and declares no "
                       f"CORRIDOR_LINE (it takes the {r['expected']} line)")
            continue
        if r["declared"] not in LINES:
            out.append(f"{where}: CORRIDOR_LINE = {r['declared']!r} is not one of "
                       f"{', '.join(LINES)}")
            continue
        if not (r["why"] or "").strip():
            out.append(f"{where}: CORRIDOR_LINE_WHY is missing or empty — the declaration "
                       f"has to say which question it is answering")
        if r["expected"] is None:
            out.append(f"{where}: imports {', '.join(r['imports'])} and calls none of "
                       f"them, so nothing here can confirm the declaration")
        elif r["declared"] != r["expected"]:
            out.append(f"{where}: declares {r['declared']!r} but its calls take the "
                       f"{r['expected']} line ({', '.join(r['takes'])})")
    return out


def census_lines(census: list[dict]) -> list[str]:
    width = max((len(r["path"]) for r in census), default=0)
    return [f"  {r['path']:<{width}}  {(r['declared'] or '—'):<7}  {r['why'] or ''}"
            for r in census]


# --- the assertions, and they are meant to fire -------------------------------------

_HEAD = "from plat_corridors import corridors, control_offsets, intrusion\n"


def _one(source: str) -> list[str]:
    entry = read(Path("tools/fixture.py"), source=source)
    if entry is None:
        return ["fixture reads no line-bearing name"]
    return faults([entry])


def self_test() -> int:
    cases: list[tuple[str, bool, str]] = []

    def case(label: str, source: str, should_fail: bool) -> None:
        got = _one(source)
        ok = bool(got) == should_fail
        cases.append((label, ok, "; ".join(got) or "no fault"))

    decl = 'CORRIDOR_LINE = "drawn"\nCORRIDOR_LINE_WHY = "a roof on a lot"\n'
    case("1. a reader that declares nothing is caught",
         _HEAD + "lanes = corridors()\n", True)
    case("2. a declaration that is not one of the three is caught",
         _HEAD + 'CORRIDOR_LINE = "the plat"\nCORRIDOR_LINE_WHY = "x"\nlanes = corridors()\n',
         True)
    case("3. an empty reason is caught",
         _HEAD + 'CORRIDOR_LINE = "drawn"\nCORRIDOR_LINE_WHY = "  "\nlanes = corridors()\n',
         True)
    case("4. 'drawn' over a call that asks for the control line is caught",
         _HEAD + decl + "lanes = corridors(from_control=True)\n", True)
    case("5. 'drawn' over control_offsets() is caught",
         _HEAD + decl + "off = control_offsets()\n", True)
    case("6. 'control' over the drawn call is caught",
         _HEAD + 'CORRIDOR_LINE = "control"\nCORRIDOR_LINE_WHY = "the plat"\n'
         "lanes = corridors()\n", True)
    case("7. 'both' when only one line is taken is caught",
         _HEAD + 'CORRIDOR_LINE = "both"\nCORRIDOR_LINE_WHY = "x"\nlanes = corridors()\n',
         True)
    case("8. an import with no call cannot confirm anything, and is caught",
         _HEAD + decl, True)
    case("9. …and the three honest declarations pass",
         _HEAD + decl + "lanes = corridors()\nd = intrusion(poly)\n", False)
    case("10. 'control' over corridors(from_control=FROM_CONTROL) passes — a flag that "
         "CAN ask for it does",
         _HEAD + 'CORRIDOR_LINE = "control"\nCORRIDOR_LINE_WHY = "the plat"\n'
         "FROM_CONTROL = True\nlanes = corridors(from_control=FROM_CONTROL)\n", False)
    case("11. 'both' over the two calls together passes",
         _HEAD + 'CORRIDOR_LINE = "both"\nCORRIDOR_LINE_WHY = "the disagreement itself"\n'
         "a = corridors(False)\nb = corridors(True)\n", False)
    case("12. corridors(False) is the drawn line, not the control one",
         _HEAD + decl + "lanes = corridors(False)\n", False)
    case("13. intrusion(poly, lanes) follows the lanes it is given and is charged for "
         "neither line",
         _HEAD + 'CORRIDOR_LINE = "control"\nCORRIDOR_LINE_WHY = "the plat"\n'
         "lanes = corridors(from_control=True)\nd = intrusion(poly, lanes)\n", False),
    case("14. a line named in a DOCSTRING is a line discussed, not a line taken",
         '"""This module explains control_offsets() and corridors(from_control=True).\n\n'
         'It takes neither.\n"""\n' + _HEAD + decl + "lanes = corridors()\n", False)
    case("15. …and one named in a COMMENT likewise",
         _HEAD + decl + "# corridors(from_control=True) is the other question\n"
         "lanes = corridors()\n", False)

    # A module that imports only the line-free helpers is not a reader at all.
    only_sampled = read(Path("tools/fixture.py"),
                        source="from plat_corridors import sampled, SAMPLE_M\n"
                               "pts = sampled(poly)\n")
    cases.append(("16. a module importing only `sampled` owes no declaration",
                  only_sampled is None, "not a reader" if only_sampled is None
                  else "reported as a reader"))

    committed = faults(readers())
    cases.append(("17. …and the committed tree has no fault in it",
                  not committed, "; ".join(committed) or "clean"))

    for label, ok, detail in cases:
        print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
        if not ok:
            print(f"          {detail}")
    bad = sum(1 for _, ok, _ in cases if not ok)
    print(f"  {bad} failure(s)")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gate", action="store_true", help="the check check.sh runs")
    ap.add_argument("--json", action="store_true", help="the census, machine-readable")
    ap.add_argument("--self-test", action="store_true", help="the assertions still fire")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    census = readers()
    if args.json:
        print(json.dumps({"readers": census, "faults": faults(census)}, indent=2))
        return 0

    bad = faults(census)
    counts = {line: sum(1 for r in census if r["declared"] == line) for line in LINES}
    tally = ", ".join(f"{counts[line]} {line}" for line in LINES)
    if args.gate:
        if bad:
            print(f"corridor lines FAIL — {len(bad)} reader(s) do not say which line "
                  f"they take:")
            for fault in bad:
                print(f"  * {fault}")
            return 1
        print(f"corridor lines OK — {len(census)} readers of the platted grid, each "
              f"declaring which line it takes ({tally})")
        return 0

    print(f"{len(census)} readers of the platted grid ({tally})\n")
    print("\n".join(census_lines(census)))
    if bad:
        print()
        for fault in bad:
            print(f"  FAULT  {fault}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
