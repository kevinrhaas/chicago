#!/usr/bin/env python3
"""How much of the gazetteer a bare-surname merge rule would actually reach.

Ticket T-0341. `compile_gazetteer.py` refuses a merge when the two names share a
surname and carry different forename initials — the family rule, and it is right.
But `initials()` returns an empty tuple for a name with no forename at all, and an
empty tuple differs from every real one, so the guard also refuses the case it was
never aimed at: joining `[?] Blodget` to the same surname with the forename supplied.
Widening that is the owner's call and not a refactor, so this command does not change
the policy. It MEASURES what the widening would reach, so the ruling can be made on
numbers instead of on the four examples the ticket happened to hit.

The narrow test the ticket proposes: allow the merge when one side has NO forename at
all and the corpus holds EXACTLY ONE forenamed bearer of that surname; refuse it the
moment a second bearer stands, which is the family case the rule was written for.

    tools/probe_bare_surname_merges.py            the three counts and the admissible set
    tools/probe_bare_surname_merges.py --all      also list the refused and the unjoinable

This is a probe and not a gate: nothing in `check.sh` runs it, because there is no
assertion to make until the ruling exists. It reads the COMMITTED gazetteer.json —
that is, the fully-compiled corpus, after the 181 declared merges have been applied —
and it borrows `compile_gazetteer.py`'s own `surname()` and `initials()` so it cannot
drift from the guard it is reasoning about.
"""

import argparse
import collections
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAZETTEER = ROOT / "data" / "research" / "newspapers" / "gazetteer.json"


def _compile_gazetteer():
    spec = importlib.util.spec_from_file_location(
        "compile_gazetteer", ROOT / "tools" / "compile_gazetteer.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def classify():
    """Every forenameless person, and the forenamed bearers of its surname."""
    cg = _compile_gazetteer()
    persons = json.loads(GAZETTEER.read_text(encoding="utf-8"))["persons"]
    by_surname = collections.defaultdict(list)
    for p in persons:
        by_surname[cg.surname(p["name"])].append(p)

    rows = []
    for p in persons:
        if cg.initials(p["name"]) != ():
            continue
        bearers = [q["name"] for q in by_surname[cg.surname(p["name"])]
                   if cg.initials(q["name"]) != ()]
        # A marker says a forename WAS set and could not be read; a plain surname
        # asserts nothing at all. The owner may want to rule differently on each.
        marked = any(m in p["name"] for m in ("[", "…", "..."))
        # What the page actually set, kept beside the reading: it is the only thing a
        # reader can judge a contradiction from, and it cannot be judged mechanically
        # (`Ca Conger` is two letters READ; `n Whitcomb` is OCR debris in the same shape).
        printed = sorted({v["as_printed"] for v in p["variants"]})
        rows.append({"name": p["name"], "surname": cg.surname(p["name"]),
                     "bearers": bearers, "marked": marked, "printed": printed})
    return len(persons), rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--all", action="store_true",
                    help="also list the refused and the unjoinable, not only the admissible")
    args = ap.parse_args()

    total, rows = classify()
    one = [r for r in rows if len(r["bearers"]) == 1]
    many = [r for r in rows if len(r["bearers"]) > 1]
    none = [r for r in rows if not r["bearers"]]

    print("%d person(s) compiled, %d of them carrying no forename at all" % (total, len(rows)))
    print("  %3d ADMISSIBLE   exactly one forenamed bearer of the surname" % len(one))
    print("  %3d refused      two or more bearers — the family case the rule is for" % len(many))
    print("  %3d unjoinable   no forenamed bearer at all; nothing to merge into" % len(none))
    print("  of the %d, %d carry an unread-forename marker and %d are a plain surname"
          % (len(rows), sum(1 for r in rows if r["marked"]),
             sum(1 for r in rows if not r["marked"])))

    print("\nthe admissible set, in full — read `as printed` before declaring any of them:")
    for r in sorted(one, key=lambda r: r["surname"]):
        print("  %-22s -> %-28s as printed %-14s %s"
              % (r["name"], r["bearers"][0], ", ".join(r["printed"]),
                 "" if r["marked"] else "(PLAIN SURNAME — the page set no forename)"))
    if args.all:
        print("\nrefused — a second bearer stands:")
        for r in sorted(many, key=lambda r: r["surname"]):
            print("  %-24s %d bearers: %s" % (r["name"], len(r["bearers"]),
                                              ", ".join(r["bearers"][:4])))
        print("\nunjoinable — the surname has no forenamed bearer:")
        for r in sorted(none, key=lambda r: r["surname"]):
            print("  %s" % r["name"])


if __name__ == "__main__":
    main()
