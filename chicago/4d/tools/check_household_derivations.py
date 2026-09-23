#!/usr/bin/env python3
"""Every generated file under data/research/ that derives from the household tree
is re-derived by tools/check.sh.

    tools/check_household_derivations.py --check      the gate
    tools/check_household_derivations.py --self-test  its own assertions still fire

T-0856 ask 2. T-0856 was one instance of a shape this project keeps finding — T-0757,
T-0814, T-0715, T-0691 are the same fault in four other writers: a generated artefact
nobody re-derives. Its second ask was to say what ELSE under data/research/ derives
from data/residents/households/ and is likewise ungated, because "a household fold
moves every refusal string in every domain that prints one, and this cannot be the
only one."

Answering that once, in a PR body, answers it for a day. The household tree is folded
and renamed most weeks, and a new domain reader lands most weeks too, so the answer
this tool computes is the only kind that stays true: ENUMERATE the class and require
every member to be gated. As of T-0856 read_census_1830.py was the only ungated member,
and this is red the moment there is another.

WHAT COUNTS AS A MEMBER. A JSON file under data/research/ that names its own generator
in `generated_by` (the domain shape research_domains.py --check requires), whose
generator reads data/residents/households/. Files with no `generated_by` are hand
authored and are not this tool's business.

WHAT COUNTS AS GATED. The generator is invoked in tools/check.sh under one of the
flags below, each of which re-derives the artefact and diffs it against the committed
bytes. This list is deliberately short and explicit: a generator run under some OTHER
flag is not re-derived by that run, and reads as ungated here on purpose.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "data" / "research"
CHECK_SH = ROOT / "tools" / "check.sh"
HOUSEHOLDS = "residents/households"

# Flags under which a generator re-derives its artefact and diffs it. `--gate` is
# freeze.gate(), which is that same diff by another name (select_resident_research_*).
REDERIVING_FLAGS = {"--check", "--check-properties", "--gate", "--all"}


def gated_generators(check_sh: str) -> dict[str, set[str]]:
    """Generators tools/check.sh actually INVOKES, and under which flags.

    A name in a comment is not an invocation — the whole fault T-0856 records is a
    tool this file discusses at length and never calls.
    """
    found: dict[str, set[str]] = {}
    for line in check_sh.splitlines():
        line = line.strip()
        if line.startswith("#"):
            continue
        m = re.search(r"tools/([A-Za-z0-9_]+\.py)\s+(.*)", line)
        if not m:
            continue
        found.setdefault(m.group(1), set()).update(re.findall(r"--[a-z-]+", m.group(2)))
    return found


def members(research: Path, tools: Path) -> dict[str, list[str]]:
    """Household-derived generated files under data/research/, by generator."""
    out: dict[str, list[str]] = {}
    for path in sorted(research.rglob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue
        stated = doc.get("generated_by") or doc.get("_generated_by")
        if not stated:
            continue
        m = re.search(r"([A-Za-z0-9_]+\.py)", str(stated))
        if not m:
            continue
        src = tools / m.group(1)
        if not src.exists():
            continue
        if HOUSEHOLDS not in src.read_text(encoding="utf-8"):
            continue
        out.setdefault(m.group(1), []).append(str(path.relative_to(research.parent.parent)))
    return out


def survey(research: Path, tools: Path, check_sh: str):
    invoked = gated_generators(check_sh)
    ungated = []
    gated = []
    for gen, files in sorted(members(research, tools).items()):
        if REDERIVING_FLAGS & invoked.get(gen, set()):
            gated.append((gen, files))
        else:
            ungated.append((gen, files))
    return gated, ungated


def run() -> int:
    gated, ungated = survey(RESEARCH, ROOT / "tools", CHECK_SH.read_text(encoding="utf-8"))
    for gen, files in ungated:
        print("FAIL %s writes %d file(s) under data/research/ off the household tree "
              "and tools/check.sh never re-derives it: %s"
              % (gen, len(files), ", ".join(files)))
    if ungated:
        print("     A household fold moves every refusal string in every domain that "
              "prints one. Give the generator a --check that re-derives into a scratch "
              "tree and diffs, and add a step for it beside its siblings (T-0856).")
        return 1
    print("%d generator(s) derive %d file(s) under data/research/ from the household "
          "tree, and this gate re-derives every one"
          % (len(gated), sum(len(f) for _, f in gated)))
    return 0


def self_test() -> int:
    import tempfile
    failures = []

    def holds(label, got, want):
        if got != want:
            failures.append("%s: got %r, wanted %r" % (label, got, want))

    holds("a commented-out invocation is not an invocation",
          gated_generators("# python3 tools/read_census_1830.py --check"), {})
    holds("a real invocation is read with its flags",
          gated_generators("  python3 tools/read_census_1830.py --check"),
          {"read_census_1830.py": {"--check"}})
    holds("freeze.gate counts as a re-derivation",
          bool(REDERIVING_FLAGS & gated_generators(
              "  python3 tools/select_resident_research_pass_13.py --gate"
          ).get("select_resident_research_pass_13.py", set())), True)
    holds("a non-re-deriving flag does not count",
          bool(REDERIVING_FLAGS & gated_generators(
              "  python3 tools/verify_fergus_1839_first_ward.py --offline"
          ).get("verify_fergus_1839_first_ward.py", set())), False)

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        research = tmp / "data" / "research" / "dom"
        research.mkdir(parents=True)
        tools = tmp / "tools"
        tools.mkdir()

        def gen(name, reads_households):
            body = "read(%r)\n" % (HOUSEHOLDS if reads_households else "somewhere/else")
            (tools / name).write_text(body, encoding="utf-8")

        def artefact(name, generated_by):
            doc = {"generated_by": generated_by} if generated_by else {"note": "by hand"}
            (research / name).write_text(json.dumps(doc), encoding="utf-8")

        gen("reads_hh.py", True)
        gen("reads_other.py", False)
        artefact("a.json", "tools/reads_hh.py --build")
        artefact("b.json", "tools/reads_other.py --build")
        artefact("c.json", None)

        root = tmp / "data" / "research"
        gated, ungated = survey(root, tools, "  python3 tools/reads_other.py --check")
        holds("the household-derived ungated generator is named",
              [g for g, _ in ungated], ["reads_hh.py"])
        holds("a generator that does not read the household tree is not this gate's",
              [g for g, _ in gated], [])

        gated, ungated = survey(root, tools, "  python3 tools/reads_hh.py --check")
        holds("gating it clears it", ungated, [])
        holds("…and it is then counted", [g for g, _ in gated], ["reads_hh.py"])

        gated, ungated = survey(root, tools, "  python3 tools/reads_hh.py --build")
        holds("--build is not a re-derivation", [g for g, _ in ungated], ["reads_hh.py"])

    for f in failures:
        print("FAIL %s" % f)
    if not failures:
        print("check_household_derivations: the enumeration and the gating rule hold")
    return 1 if failures else 0


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return run()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
