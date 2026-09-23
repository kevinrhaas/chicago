#!/usr/bin/env python3
"""THE ONCE-EACH RULE, in one place, for every spend pass that writes a paragraph (T-0846).

    python3 tools/spend_write_once.py --sweep      every marker, every card, what is doubled
    python3 tools/spend_write_once.py --self-test  the rule itself, both directions

WHY THIS EXISTS. Each spend pass finds its own work by a MARKER sentence and asks only two
questions about it: is the paragraph PRESENT on every card a ruling names (`gaps`), and does
any card carry it without a ruling behind it (`strays`). Neither question can see a card that
carries the marker TWICE, nor one carrying a superseded pass's paragraph about the same
source beside the current one. Both are things a re-run actually produces, because every
applier is add-only — `if MARKER not in note: note += paragraph` — so a pass whose wording
changed appends rather than overwrites.

T-0677 measured the hole rather than reasoning about it: running the pre-T-0636 version of
`spend_land_sales.py` against dev gave every one of its thirty-one cards a second paragraph
about the same register, differently worded and saying the same thing, and `tools/check.sh`
stayed GREEN. It closed the hole in that one tool and deliberately did not generalise ahead
of the second case.

T-0846 is the second case, and it found the population is larger than the ticket named. Of
the eight passes that touch a resident card, six write a marker paragraph into `note` and can
therefore double; the other two cannot, and the difference is worth stating because it is
what decides who needs this module:

  spend_census_1840_heads.py        marker paragraph   had a copy of the rule
  spend_civic_voter_lists.py        marker paragraph   T-0846 gives it the rule
  spend_fergus_1839_later_lists.py  marker paragraph   T-0846 gives it the rule
  spend_fergus_1839_lot_sale.py     marker paragraph   T-0846 gives it the rule
  spend_land_sales.py               marker paragraph   T-0677 wrote the rule here first
  spend_second_presbyterian_roll.py marker paragraph   had a copy of the rule
  spend_directories.py              a `directories` BLOCK, and `--check` compares the whole
                                    file byte-for-byte against what the pass re-derives
  spend_ladder_rungs.py             a `ladder_rule` FIELD at a fixed position, and `--check`
                                    compares the whole file the same way

The last two hold the once-each rule ALREADY, and hold it in a way a marker count cannot
reach: a JSON key exists once by construction, and `--check` re-derives the whole household
file and compares it byte-for-byte, so a doubled block does not survive. Both were staged red
under T-0846 to prove it rather than assert it — `spend_directories.py --check` reports DRIFT
on a household whose `directories.people` list is doubled, and `spend_ladder_rungs.py --check`
reports it on a card carrying a rung that derivation does not reach. (Its file comparison
covers the records the pass TOUCHES; a record it does not touch is covered by the `foreign`
invariant instead, which is what the second demonstration exercises.) They get the assertions
at the foot of `self_test` naming why they are absent from the table above, not a `doubles()`
they have no marker to count.

The three copies that existed before this module were also not the same rule. `land_sales`
counted the marker AND looked for a superseded wording; `census_1840_heads` and
`second_presbyterian_roll` counted the marker only. Six copies of a rule that had already
drifted at three is the argument for one implementation, and this is it.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOUSEHOLDS = ROOT / "data" / "residents" / "households"


def doubles_over(household_id: str, person: dict, marker: str,
                 superseded: tuple = ()) -> list:
    """The rule over ONE already-loaded person — what a self-test needs and the gate reuses.

    Two ways a card ends up saying one source twice, and both are silent to `gaps` and
    `strays`: this pass's own paragraph appended a second time, or a superseded pass's
    paragraph left standing beside it.
    """
    note = person.get("note") or ""
    out = []
    count = note.count(marker)
    if count > 1:
        out.append("%s/%s — carries this pass's paragraph %d times; a source is written "
                   "onto a card once" % (household_id, person.get("id"), count))
    for old in superseded:
        if old in note:
            out.append("%s/%s — carries a superseded paragraph about the same source "
                       "beside this one; a source is written onto a card once"
                       % (household_id, person.get("id")))
    return out


def doubles(marker: str, superseded: tuple = (), households: pathlib.Path = HOUSEHOLDS)\
        -> list:
    """…and every card in the town says this pass's source ONCE, however many passes ran."""
    bad = []
    for path in sorted(households.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for person in doc.get("persons") or []:
            bad.extend(doubles_over(doc.get("id") or path.stem, person, marker, superseded))
    return bad


# --- the sweep ------------------------------------------------------------------------

def _markers() -> list:
    """(tool name, marker) for every pass that writes a paragraph, read off the tools.

    Read rather than listed, so a seventh pass is swept the day it is written instead of
    the day somebody remembers to add it here.
    """
    out = []
    for path in sorted((ROOT / "tools").glob("spend_*.py")):
        if path.name == pathlib.Path(__file__).name:
            continue
        source = path.read_text(encoding="utf-8")
        if "MARKER not in note" not in source:
            continue
        module: dict = {}
        for line in source.splitlines():
            if line.startswith("MARKER = "):
                module["start"] = source.index(line)
                break
        if "start" not in module:
            continue
        # The literal, evaluated on its own: several are parenthesised over two lines.
        chunk, depth, text = source[module["start"] + len("MARKER = "):], 0, ""
        for i, ch in enumerate(chunk):
            text += ch
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if ch == "\n" and depth == 0:
                break
        out.append((path.name, eval(text, {"__builtins__": {}}, {})))  # noqa: S307
    return out


def sweep() -> int:
    """Every marker against every card — the measurement T-0846's acceptance asks for."""
    found = 0
    for name, marker in _markers():
        bad = doubles(marker)
        print("   %-38s %s" % (name, "%d doubled card(s)" % len(bad) if bad else "clean"))
        for line in bad[:10]:
            print("      %s" % line)
        found += len(bad)
    print("   %d card(s) carry a paragraph twice across %d pass(es)"
          % (found, len(_markers())))
    return 1 if found else 0


def _check_body(source: str) -> str:
    """The text of a pass's `check()`, so the wiring can be asserted and not assumed."""
    start = source.index("def check(")
    rest = source[start:]
    end = rest.index("\n\n\ndef ")
    return rest[:end]


# --- the rule's own assertions ----------------------------------------------------------

def self_test() -> int:
    failures = []

    def want(label, cond):
        if not cond:
            failures.append(label)

    marker = "A MARKER SENTENCE."
    old = "A SUPERSEDED SENTENCE ABOUT THE SAME SOURCE."

    clean = {"id": "p_x", "note": "Something else. " + marker + " And more."}
    want("the rule must stay silent on a card carrying the paragraph once",
         doubles_over("hh_x", clean, marker, (old,)) == [])

    doubled = {"id": "p_x", "note": clean["note"] + " " + marker + " Again."}
    want("the rule must fire on a card carrying this pass's paragraph twice",
         any("2 times" in d for d in doubles_over("hh_x", doubled, marker, (old,))))

    rival = {"id": "p_x", "note": clean["note"] + " " + old + " …"}
    want("the rule must fire on a superseded paragraph left standing beside this one",
         any("superseded" in d for d in doubles_over("hh_x", rival, marker, (old,))))

    want("a pass that declares no superseded wording must not fire on one",
         doubles_over("hh_x", rival, marker) == [])

    want("a card with no note at all must be silent",
         doubles_over("hh_x", {"id": "p_x"}, marker, (old,)) == [])

    # The sweep must SEE the passes, or it reports "clean" by finding nothing to check.
    names = [n for n, _m in _markers()]
    want("the sweep must find the passes that write a paragraph", len(names) >= 6)
    want("the sweep must find the pass T-0677 wrote the rule in",
         "spend_land_sales.py" in names)
    want("the sweep must find the three passes T-0846 gave the rule to",
         {"spend_civic_voter_lists.py", "spend_fergus_1839_later_lists.py",
          "spend_fergus_1839_lot_sale.py"} <= set(names))

    # And every pass that writes a paragraph must USE it, AND have it wired into `--check`:
    # a copy that drifts is the defect this module exists to end, and a `doubles()` nothing
    # calls is the same hole with a function in front of it. Both halves are asserted,
    # because T-0677's gate was real and still could not see five of its six siblings.
    for name, _marker in _markers():
        source = (ROOT / "tools" / name).read_text(encoding="utf-8")
        want("%s must call the shared once-each rule" % name,
             "spend_write_once.doubles(" in source)
        want("%s must wire doubles() into its --check" % name,
             "doubles()" in _check_body(source))

    # THE TWO PASSES THAT NEED NO `doubles()`, asserted rather than remembered. They hold the
    # once-each rule more strongly than a marker count can — `--check` re-derives the WHOLE
    # household file and compares it byte-for-byte, so no byte this pass did not derive can
    # survive, and a JSON key exists once by construction. What could quietly undo that is
    # somebody giving one of them an add-only `note` applier; if that happens `_markers()`
    # picks it up above and the "must call the shared rule" assertion fails. These two
    # assertions are the other side of the same guard: they say WHY it is absent today.
    for name in ("spend_directories.py", "spend_ladder_rungs.py"):
        source = (ROOT / "tools" / name).read_text(encoding="utf-8")
        want("%s must write no add-only marker paragraph, or it needs the shared rule"
             % name, "MARKER not in note" not in source)
        want("%s must hold the rule by whole-file re-derivation instead" % name,
             'read_text(encoding="utf-8") != text' in source)

    for line in failures:
        print("   FAIL: %s" % line)
    if failures:
        print("   %d assertion(s) failed" % len(failures))
        return 1
    print("   OK: the once-each rule holds in both directions, and all %d paragraph pass(es) "
          "call it" % len(_markers()))
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    if "--sweep" in sys.argv:
        return sweep()
    print(__doc__.strip().splitlines()[0])
    return sweep()


if __name__ == "__main__":
    raise SystemExit(main())
