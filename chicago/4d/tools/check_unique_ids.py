#!/usr/bin/env python3
"""No committed list may carry the same id twice — asserted on the BRANCH.

WHY THIS EXISTS, and it is three failures in one day rather than a principle.
On 2026-09-05 `dev`'s gate went red twice, and both times the cause was a
duplicate in a keyed list:

  04:00Z  two branches each minted ticket id T-0739 (repaired in #863)
  ~16:00Z #882 committed a SECOND, byte-identical `west_water` entry to
          data/streets/1835.json — its branch was cut before #875 landed the
          first one, and the merge kept both (repaired in #889)

A third came the same evening, from an agent staging a `UU` conflict with
`git add -A`. None of the three was caught on the branch that wrote it. All
three were found by check.sh running against `dev` AFTER the merge, which is
the expensive place to find anything: the dev gate is the base every open PR
inherits, so one duplicate parked nineteen PRs behind a red they had not
caused.

AND IT IS NOW WORSE THAN THAT. `dev` carries a ruleset requiring the `gate`
check. A red `dev` no longer merely discourages merging — it FORBIDS it. The
same fault that cost a morning would now stop the lane.

THE RULE IS DISCOVERED, NOT LISTED. A hand-maintained table of "lists to
check" is a table that goes stale the first time somebody adds a list, and the
list they add is the one that breaks. So this walks the committed JSON and
applies the rule wherever the SHAPE appears: a dict value that is a list of two
or more objects, every one of which carries an `id`. Measured over the tree on
the day it was written — 2,835 committed JSON files — that shape appears in 68
kinds of list and 67 of them were already clean. So the rule is not a new
constraint on anybody: it is what the data already obeys, written down, and the
single kind that did not obey it has since been fixed at the generator that
minted it (T-0828), so the rule now applies everywhere with no exception.

AND LISTS OF STRINGS, SINCE T-0829. A provenance or coverage list carries no
`id`, so the shape above never reached it. Every list of two or more strings is
now held as a SET unless MULTISETS names it; see that table for why the
multisets are named rather than the sets discovered.

THE EXCEPTION MACHINERY STAYS (see EXCEPTIONS), empty. An exception here is a
named, ticketed gap and never a silent skip, and the check refuses one the day
it stops being needed — which is how the last one came out.
"""
from __future__ import annotations

import argparse
import collections
import glob
import io
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Files big enough that parsing them on every gate run would be the slowest
# thing in it. None of the keyed lists live in one; the bound is stated so a
# future one is a deliberate decision rather than a silent omission.
SIZE_CAP = 12_000_000

# ── the exceptions, each with its reason and its ticket ────────────────────
#
# EMPTY, and it is worth saying how it got that way rather than deleting the
# table. It held one entry, three times over: `runs` in the three lot-line fence
# files repeated an id because the id UNDER-SPECIFIED rather than because a run
# was committed twice — a run was named `side_<block>_lot<n>`, and a lot has two
# sides, so the two side lines of one lot came out with one id between them.
# Asserting uniqueness there would have refused correct data, so the gap was
# named here instead of skipped, with the ticket that closes it.
#
# T-0828 closed it at the generator (`tools/generate_lot_line_fences.py`), which
# now mints `side_<lot>_<e|w|n|s>` — the id names the side, the two runs are two
# ids, and all three files rebuilt clean. So the rule below has no exception, and
# the exception the table was built for came out the way the design intended:
# the check reported it as unnecessary the moment it was, and asked for the
# deletion. Keep the table for the next one.
EXCEPTIONS: dict[tuple[str, str], str] = {}

# ── append-only ledgers, which have no `id` and a different rule ───────────
#
# `raised[]` legitimately holds SEVERAL entries for one domain — each is a
# separate dated decision with its own reasoning, and collapsing them would
# erase the history the file exists to keep. So the rule here is not "one entry
# per domain"; it is that no two entries are IDENTICAL, which is what a bad
# merge produces. The distinction matters: the wrong rule would refuse honest
# history, and this file collided on nearly every merge of 2026-09-05.
IDENTICAL_ONLY = [("tools/research_spend_baseline.json", "raised"),
                  ("tools/research_spend_baseline.json", "lowered")]

# ── lists of STRINGS: a set unless it is named a multiset here (T-0829) ────
#
# A provenance, coverage or citation list is a list of strings, so the `id` rule
# above never reaches it — and `data/research/*/coverage.json`'s
# `declarations[].items[]`, which T-0820 named, is exactly that shape. A repeated
# identifier in one is the same merge artefact as a repeated id.
#
# "No string twice" is not a rule on its own, because many string lists are
# MULTISETS — one element per row, where a repeat is the data saying two rows
# agree. Measured over the tree on 2026-10-04: 5,015 files, 594 kinds of string
# list, 40,489 lists, and 13 kinds carried a repeat. Twelve are multisets and are
# named below with what one element stands for. The thirteenth was `mentions` in
# the newspaper gazetteer — a set of clipping ids that three persons carried twice
# — and it was fixed at its generator (tools/compile_gazetteer.py), not named.
#
# WHY THE MULTISETS ARE NAMED AND THE SETS ARE NOT. The ticket's first candidate
# was to discover a key as a set when every OTHER list under it is clean. That
# fails open: two artefacts under one key at once (one merge can do it) make each
# look like a multiset to the other, and the rule goes quiet in the case it exists
# for. So, as with EXCEPTIONS above, coverage is discovered and the exemption is
# named: every string list in the tree is held as a set, a list added tomorrow is
# held without anybody registering it, and a new multiset costs one line here
# with its reason. An entry is per (file, key), so naming one file's multiset
# leaves the same key elsewhere held, and an entry whose key has left its file is
# reported so it is deleted rather than left to excuse a later list.
MULTISETS: dict[tuple[str, str], str] = {
    ("data/research/directories/claims/fergus_1843_civic.json", "by_ward"):
        "one element per person; two people in one ward print the ward twice",
    ("data/research/directories/claims/fergus_1843_civic.json", "names"):
        "one element per office as printed; John S. Wright held two",
    ("data/research/directories/claims/fergus_1843_civic.json", "entities"):
        "one element per office as printed, the same man named once per office",
    ("data/research/census_1840/resident_crosswalk.json", "outcomes"):
        "one element per head in an adjacent pair; both heads may share an outcome",
    ("data/traces/kinzie_addition_lot_lines.json", "rule_grades"):
        "one grade per lot rule read on the plat",
    ("data/traces/vectors/thompson_lots.json", "rule_grades"):
        "one grade per lot rule read on the plat",
    ("data/traces/vectors/thompson_lots.json", "printed"):
        "one element per lot whose frontage figure was read",
    ("data/traces/thompson_west_division_lots.json", "frontage_figures_read"):
        "one element per lot whose frontage figure was read",
    ("data/research/land_sales/ground.json", "shares_as_read"):
        "one element per share of a divided lot; equal shares read alike",
    ("data/reconstruction/1835_placement_policy.json", "coats"):
        "a weighted deck: an element repeated is a coat dealt more often",
    ("data/reconstruction/1835_placement_policy.json", "boom_ages"):
        "a weighted deck: an element repeated is an age dealt more often",
    ("data/reconstruction/1835_placement_policy.json", "colours"):
        "a weighted deck: an element repeated is a colour dealt more often",
    ("data/traces/west_grid_migration_order.json", "principal_roofs_on_the_better_face"):
        "one element per principal roof, by the slot it stands in",
    ("tools/forb_clamp_baseline.json", "_"):
        "prose, one element per line, with blank lines between paragraphs",
}


def keyed_lists(doc):
    """Every (key, list) in a document that carries the shape this rule is about."""
    if not isinstance(doc, dict):
        return
    for key, value in doc.items():
        if (isinstance(value, list) and len(value) > 1
                and all(isinstance(x, dict) for x in value)
                and all("id" in x for x in value)):
            yield key, value


def string_lists(node):
    """Every (key, list) at any depth whose value is two or more strings.

    No path is built on the way down: the walk visits every node of 5,000 files
    and a path string per node was most of its cost. `where` finds one on demand.
    """
    stack = [node]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for key, value in cur.items():
                if isinstance(value, list):
                    if len(value) > 1 and all(type(x) is str for x in value):
                        yield key, value
                    else:
                        stack.append(value)
                elif isinstance(value, dict):
                    stack.append(value)
        elif isinstance(cur, list):
            stack.extend(x for x in cur if isinstance(x, (dict, list)))


def where(node, target, at="$"):
    """The path to the list object `target` inside `node`, for a report."""
    if node is target:
        return at
    items = (node.items() if isinstance(node, dict)
             else enumerate(node) if isinstance(node, list) else ())
    for k, v in items:
        found = where(v, target, "%s.%s" % (at, k) if isinstance(node, dict)
                      else "%s[%d]" % (at, k))
        if found:
            return found
    return None


def scan(root: str) -> list[str]:
    problems = []
    # An exception that outlives its cause is coverage quietly switched off: the
    # ticket lands, the ids come good, and the entry stays behind still telling
    # the check to look away — so the NEXT duplicate in that list goes unseen and
    # nobody knows the rule stopped applying. Every exception that turns out to
    # be unnecessary is therefore reported, and the message asks for a deletion
    # rather than a fix. This is the one "failure" here that is good news.
    # Observed present and clean, rather than "not observed dirty" — an exception
    # whose file is absent (a sandbox, a deletion) is not evidence of anything.
    unneeded = set()
    multisets_seen = set()
    # data/ is the world; tools/ holds the ledgers; tickets/ holds tickets.json,
    # whose `tickets[]` is where the T-0739 collision came to rest. `ticket.mjs
    # check` catches that one at source and still should — this is the same fault
    # caught in the artefact, which costs nothing and needs no ticket machinery.
    # The published site/ mirror is deliberately NOT walked: it is a copy of
    # tickets.json, and a rule that reports one fault twice teaches people to
    # read past it.
    paths = sorted(glob.glob(os.path.join(root, "data", "**", "*.json"), recursive=True)
                   + glob.glob(os.path.join(root, "tools", "*.json"))
                   + glob.glob(os.path.join(root, "tickets", "*.json")))
    for path in paths:
        if os.path.getsize(path) > SIZE_CAP:
            continue
        rel = os.path.relpath(path, root)
        try:
            doc = json.load(io.open(path, encoding="utf-8"))
        except Exception as exc:                                   # noqa: BLE001
            problems.append("%s does not parse as JSON (%s)" % (rel, exc))
            continue

        for key, rows in keyed_lists(doc):
            counts = collections.Counter(r["id"] for r in rows)
            if (rel, key) in EXCEPTIONS:
                if max(counts.values()) == 1:
                    unneeded.add((rel, key))
                continue
            for bad, n in sorted(counts.items()):
                if n > 1:
                    bodies = {json.dumps(r, sort_keys=True) for r in rows if r["id"] == bad}
                    shape = ("%d IDENTICAL copies — a merge kept both" % n if len(bodies) == 1
                             else "%d entries sharing one id, with DIFFERENT bodies" % n)
                    problems.append("%s: %s[] carries id %r %s" % (rel, key, bad, shape))

        for key, values in string_lists(doc):
            if (rel, key) in MULTISETS:
                multisets_seen.add((rel, key))
                continue
            for bad, n in sorted(collections.Counter(values).items()):
                if n > 1:
                    problems.append(
                        "%s: %s holds %r %d times. A string list is a SET unless "
                        "MULTISETS in this file names it — remove the repeat, or, if "
                        "each element is one row and rows may agree, name (%r, %r) "
                        "there with what one element stands for."
                        % (rel, where(doc, values), bad[:80], n, rel, key))

        for want_rel, want_key in IDENTICAL_ONLY:
            if rel != want_rel:
                continue
            rows = doc.get(want_key) or []
            if not isinstance(rows, list):
                continue
            seen = collections.Counter(json.dumps(r, sort_keys=True) for r in rows)
            for body, n in seen.items():
                if n > 1:
                    problems.append(
                        "%s: %s[] holds %d IDENTICAL entries (%s…). Several entries per "
                        "domain are correct — each is a dated decision — but two the same "
                        "is a merge artefact."
                        % (rel, want_key, n, body[:90]))

    # A multiset entry outlives its list the same way an exception outlives its
    # ticket: the key leaves the file, the entry stays, and the next list given
    # that key there is excused unread. Reported only when the file is present —
    # an absent file is not evidence of anything.
    for rel, key in sorted(set(MULTISETS) - multisets_seen):
        if os.path.exists(os.path.join(root, rel)):
            problems.append(
                "%s carries no list of strings under %r any more, so its MULTISETS "
                "entry (%s) excuses nothing it was written for. DELETE that entry."
                % (rel, key, MULTISETS[(rel, key)]))

    for rel, key in sorted(unneeded):
        problems.append(
            "%s: %s[] no longer carries any id twice, so the EXCEPTIONS entry for it "
            "(%s) is switching the rule off for nothing. DELETE that entry — this "
            "failure is the ticket being finished." % (rel, key, EXCEPTIONS[(rel, key)]))
    return problems


# ── the assertions, and proof they fire ───────────────────────────────────
def self_test() -> int:
    ok = True

    def case(name: str, build, should_fire: bool):
        nonlocal ok
        with tempfile.TemporaryDirectory() as td:
            for d in ("data", "tools", "tickets"):
                os.makedirs(os.path.join(td, d))
            build(td)
            fired = bool(scan(td))
            good = fired == should_fire
            ok &= good
            print("  %s  %s" % ("ok   " if good else "FAIL ", name))

    def write(td, rel, doc):
        p = os.path.join(td, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        io.open(p, "w", encoding="utf-8").write(json.dumps(doc))

    def excepted(name: str, build, should_fire: bool):
        """A case run against a SYNTHETIC exception, installed for its duration.

        EXCEPTIONS is empty (T-0828), and these three assertions are about the
        machinery rather than about any entry in it. Pinning them to a real entry
        is what made them fail the day the last one came out — the entry went and
        took its own proof with it. So the exception under test is invented here,
        which keeps the machinery proven for whoever needs the next one.
        """
        entry = ("data/enclosures/fictitious_fence.json", "runs")
        EXCEPTIONS[entry] = "T-0000 (self-test only)"
        try:
            case(name, build, should_fire)
        finally:
            del EXCEPTIONS[entry]

    case("a list with two identical entries under one id is caught",
         lambda td: write(td, "data/streets/1835.json",
                          {"streets": [{"id": "west_water", "w": 1},
                                       {"id": "west_water", "w": 1}]}), True)
    case("…and so is one id on two DIFFERENT bodies",
         lambda td: write(td, "data/streets/1835.json",
                          {"streets": [{"id": "a", "w": 1}, {"id": "a", "w": 2}]}), True)
    case("a clean list passes, so a firing below means something",
         lambda td: write(td, "data/streets/1835.json",
                          {"streets": [{"id": "a"}, {"id": "b"}]}), False)
    case("the rule reaches a list nobody registered — it is discovered, not listed",
         lambda td: write(td, "data/some/new_layer.json",
                          {"whatevers": [{"id": "x"}, {"id": "x"}]}), True)
    case("the ticket id minted twice on 2026-09-05 is caught in tickets.json too",
         lambda td: write(td, "tickets/tickets.json",
                          {"tickets": [{"id": "T-0739", "title": "one"},
                                       {"id": "T-0739", "title": "another"}]}), True)
    case("a list whose rows carry no id is not this rule's business",
         lambda td: write(td, "data/x.json", {"rows": [{"n": 1}, {"n": 1}]}), False)
    case("a one-row list cannot duplicate anything",
         lambda td: write(td, "data/x.json", {"rows": [{"id": "a"}]}), False)
    excepted("a named exception is honoured, not re-reported",
             lambda td: write(td, "data/enclosures/fictitious_fence.json",
                              {"runs": [{"id": "side_lot1"}, {"id": "side_lot1"}]}), False)
    excepted("an exception whose list came good is reported, so it cannot outlive its ticket",
             lambda td: write(td, "data/enclosures/fictitious_fence.json",
                              {"runs": [{"id": "side_lot1_e"}, {"id": "side_lot1_w"}]}), True)
    excepted("…and an exception whose file is simply absent is not mistaken for that",
             lambda td: write(td, "data/streets/1835.json",
                              {"streets": [{"id": "a"}, {"id": "b"}]}), False)
    case("…but the same shape elsewhere is still caught",
         lambda td: write(td, "data/enclosures/other_fence.json",
                          {"runs": [{"id": "side_lot1"}, {"id": "side_lot1"}]}), True)
    case("the three lot-line fence files are now held by the rule like any other",
         lambda td: write(td, "data/enclosures/town_lot_line_rails.json",
                          {"runs": [{"id": "side_lot1"}, {"id": "side_lot1"}]}), True)
    case("two IDENTICAL raised[] entries are a merge artefact and are caught",
         lambda td: write(td, "tools/research_spend_baseline.json",
                          {"raised": [{"domain": "civic", "to": 3},
                                      {"domain": "civic", "to": 3}]}), True)
    case("…but SEVERAL entries for one domain are correct history and pass",
         lambda td: write(td, "tools/research_spend_baseline.json",
                          {"raised": [{"domain": "civic", "to": 3},
                                      {"domain": "civic", "to": 9}]}), False)
    # T-0829 — lists of strings.
    case("a coverage declaration naming one item twice is caught",
         lambda td: write(td, "data/research/church/coverage.json",
                          {"declarations": [{"scope": "x", "items": ["a", "b", "a"]}]}), True)
    case("…and a clean one passes",
         lambda td: write(td, "data/research/church/coverage.json",
                          {"declarations": [{"scope": "x", "items": ["a", "b"]}]}), False)
    case("the gazetteer's three doubled clippings would be caught, at any depth",
         lambda td: write(td, "data/research/newspapers/gazetteer.json",
                          {"persons": [{"id": "person_catton_mr", "mentions": [
                              "chicago_democrat_1835_07_01#c004",
                              "chicago_democrat_1835_07_01#c004"]}]}), True)
    case("a string list nobody registered is held — discovered, not listed",
         lambda td: write(td, "data/some/new_layer.json",
                          {"sources": ["src_a", "src_a"]}), True)
    def fergus(ward_key):
        # The file carries three named multisets; all three must be present, or
        # the two left out are (rightly) reported as entries to delete.
        return {"claims": [{"entities": ["J. S. Wright", "J. S. Wright"],
                            "normalized": {"names": ["J. S. Wright", "J. S. Wright"],
                                           ward_key: ["2", "2", "5"]}}]}
    fergus_rel = "data/research/directories/claims/fergus_1843_civic.json"
    case("a named multiset may repeat — one element per row, rows agreeing",
         lambda td: write(td, fergus_rel, fergus("by_ward")), False)
    case("…but its key in ANOTHER file is still a set",
         lambda td: write(td, "data/research/directories/claims/other.json",
                          {"claims": [{"normalized": {"by_ward": ["2", "2", "5"]}}]}), True)
    case("…and a multiset entry whose key has left its file is reported for deletion",
         lambda td: write(td, fergus_rel, fergus("wards")), True)
    case("a list of one string, or of mixed types, is not this rule's business",
         lambda td: write(td, "data/x.json", {"a": ["x"], "b": ["x", 1, "x"]}), False)
    case("unparseable JSON is reported rather than skipped",
         lambda td: io.open(os.path.join(td, "data", "x.json"), "w").write("{nope"), True)

    print("SELF-TEST %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()

    problems = scan(ROOT)
    if problems:
        print("DUPLICATE IDS IN COMMITTED LISTS:", file=sys.stderr)
        for p in problems:
            print("   " + p, file=sys.stderr)
        print("\nAn id that names two things is not an id. Fix it HERE, on the branch:\n"
              "a duplicate that reaches dev turns the gate red for every open PR, and\n"
              "dev's ruleset now refuses merges while it is.", file=sys.stderr)
        return 1
    print("unique ids: every committed list carries each id once"
          + (" (%d exception(s), each ticketed)" % len(EXCEPTIONS)
             if EXCEPTIONS else ", with no exception")
          + "; every list of strings is a set but the %d named multisets" % len(MULTISETS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
