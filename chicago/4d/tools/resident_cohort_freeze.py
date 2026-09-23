#!/usr/bin/env python3
"""What a FROZEN research cohort manifest is, on both the gate and the write (T-0764).

    tools/resident_cohort_freeze.py --self-test    the assertions, fired against breakage

    freeze.gate(path, derived, label)              what --gate asserts
    freeze.write(path, derived, message)           what a regeneration is allowed to change

THE GATE CONTRACT BELOW IS T-0745's, taken from `steward/t-0745-cohort-freeze-gate`
unchanged; that branch's ticket said "take it or leave it, but do not lose it". T-0764
is the other half of the same defect and it is the half that loses evidence: exempting
the snapshot from the GATE stops a manifest being called stale, but the documented
remedy for a stale manifest — regenerate without `--gate` — still OVERWRITES the
snapshot with today's tree. `write()` below is the half that was missing.

WHY THIS FILE EXISTS. Eight cohort manifests are written by
`tools/select_resident_research_*.py` and each one is described, in its own text, as
frozen: "the ids are frozen, so a resident minted later is not retro-claimed as
researched", and "a person who acquires a research row after this does NOT make the
manifest stale". Every one of them was nevertheless gated by RE-DERIVING the whole
document from today's tree and demanding byte equality. Those two statements cannot
both hold. A re-derivation asserts the tree has not moved since the freeze, and the
tree moving is precisely what the cohorts are for:

  * researching a cohort writes a `resident_research` row onto each of its members,
    which is what `researched_ids()` refuses at selection — so a completed pass makes
    its own gate fire. On 2026-09-05 cohorts 13, 14 and 15 were red on all 76 of 76
    of their own people;
  * a source landing on a card moves that person's `sources`, `grade` and
    `occupation` — so the pilot, pass 2 and pass 3 manifests read `stale` because
    three of their 225 people had gained a land-sales entry and a death notice.

Neither is a defect in the manifest. Both were reported as one, for two days, on
every branch cut from dev.

WHAT IS FROZEN, AND SO WHAT IS GATED. The manifest is a RESERVATION and an identity
lock: it says which people this pass owns, in a fixed order, and nothing about them
that a later reading may not change. So the gate asserts the frozen thing —

  1. the committed file's person ids, IN ORDER, are the ones the selector's frame
     still yields.  This is the collision lock three parallel runs work against;
  2. every id still names a real person in `data/residents/households/`, carrying a
     name, and not an unnamed placeholder ("the rest of the household, unnamed").
     THIS is the staleness the manifests' own text describes — a person who VANISHES,
     or turns into a count;
  3. every committed row carries exactly the fields the selector emits, so a snapshot
     cell cannot be silently dropped or invented;
  4. everything in the document OUTSIDE `people` and `population_frame` matches the
     derivation exactly.

— and it does not assert the SNAPSHOT: the per-person `starting_*`, `sources`,
`letter_list_returns` and `stratum` cells, and the `population_frame` counts, which
record the tree as it stood when the cohort was fixed. It reports how many of them
have moved since, because that number is worth seeing and is not a failure.

AND SO WHAT A REGENERATION MAY CHANGE. `write()` carries the committed snapshot
forward. A person already in the manifest keeps the `starting_*`, `sources`,
`letter_list_returns` and `stratum` cells the manifest was frozen with, and the
document keeps its committed `population_frame`; a person the frame yields for the
first time is frozen at today's values, because that is the moment that person's
cohort membership begins. Everything else — the identity cells the tree owns, and
every document field outside the snapshot — is rewritten from the derivation, which
is what a regeneration is for.

WHAT THIS CANNOT RECOVER. The snapshots on disk today are NOT the day each cohort was
fixed: every manifest has been regenerated between five and fifteen times since, most
recently by PR #863 on 2026-09-05, and each of those writes replaced the freeze with
the tree of its own afternoon. Nothing here reconstructs those values — a snapshot
lifted out of an old commit and re-committed today would be this project asserting a
provenance it cannot show, which is the one thing it does not do. What this file
guarantees is forward: from its first write, a cell is written once.

WHAT THIS DOES NOT WEAKEN. The novelty refusal — "zero overlap with the people who
already carry a research row" — is meaningful when a cohort is SELECTED and is
self-refuting afterwards, so it stays on the write path, unchanged and still fatal
there. A new manifest claiming somebody another pass has ruled on is refused before
it is ever committed.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESIDENTS = ROOT / "data" / "residents"
HOUSEHOLDS = RESIDENTS / "households"
MERGED = RESIDENTS / "merged"

# The document keys that record the tree as it stood at the freeze rather than the
# reservation itself. Everything else is compared exactly.
SNAPSHOT_DOC_KEYS = ("population_frame",)

# The per-person cells that record the tree at the freeze. `starting_*` is a prefix
# because the selectors each emit their own set of them (evidence, grade, presence,
# occupation); the rest are named. Everything not matched here — `person_id`,
# `household_id`, `name`, `selection_reason` — is the reservation or the tree's own
# identity, and a regeneration is allowed to rewrite it.
SNAPSHOT_ROW_KEYS = ("sources", "letter_list_returns", "stratum")


def is_snapshot_key(key: str) -> bool:
    return key.startswith("starting_") or key in SNAPSHOT_ROW_KEYS


def folded_people(root: Path | None = None) -> dict:
    """Every person a landed merge ruling folded, by id, READ FROM THE STUB.

    A COHORT MEMBER RULED A DUPLICATE HAS NOT LEFT THE TOWN (T-0842). The town-card
    consolidation promises that "every `person_id` any file cites — the crosswalks,
    identity_master.json, the smoke cohorts, the placed-resident parcels — still
    resolves to a person": the record is copied whole to `data/residents/merged/` and
    `data/residents/index.json` grows a redirect. Every cohort gate was nevertheless
    reading the fold as an absence and refusing outright — "frozen cohort member
    vanderbogart_h is no longer in the town" — and the cohort gates were the one
    reader that promise did not reach. It surfaced the first time a ruling reached a
    frozen cohort, which is the day T-0842 folded `vanderbogart_h` onto
    `vanderbogart_henry`; before that no folded card had ever been in one.

    THE STUB IS READ, NOT THE SURVIVOR, and that is the whole point. The stub is the
    record exactly as it stood when the merge landed, so a frozen snapshot stays
    frozen: a ruling may decide that two cards are one man, and it may not thereby
    rewrite what a past research pass recorded itself as having studied. The gate
    that matters — a cohort member who is in no household and no stub either — still
    fires, because a deletion is not a redirect.
    """
    merged = (root / "merged") if root is not None else MERGED
    out = {}
    if not merged.is_dir():
        return out
    for path in sorted(merged.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        record = doc.get("superseded_record") or {}
        for person in record.get("persons") or []:
            if person.get("id"):
                out[person["id"]] = (record, person)
    return out


def folded_into(root: Path | None = None) -> dict:
    """person_id -> the person id a landed ruling folded it onto, from the redirect table."""
    index = (root or RESIDENTS) / "index.json"
    if not index.is_file():
        return {}
    doc = json.loads(index.read_text(encoding="utf-8"))
    return {row["person"]: row["merged_into_person"]
            for row in doc.get("merged") or []
            if row.get("person") and row.get("merged_into_person")}


def redirected(ids) -> list:
    """The members of `ids` a landed ruling folded, each named with its survivor.

    One line a cohort gate can print, so a manifest that studies a person the town has
    since ruled a duplicate SAYS so instead of quietly still counting them.
    """
    into = folded_into()
    return ["%s (now carried by %s)" % (pid, into[pid]) for pid in ids if pid in into]


def live_people() -> dict:
    """Every person the cohorts may claim, by id, as (household, person).

    The layer, plus the people a landed merge ruling folded out of it — see
    `folded_people()` for why a fold is a redirect and not a disappearance. A live
    record always wins over a stub of the same id.
    """
    out = folded_people()
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        hh = json.loads(path.read_text(encoding="utf-8"))
        for person in hh.get("persons", []):
            if person.get("id"):
                out[person["id"]] = (hh, person)
    return out


def is_placeholder(person: dict) -> bool:
    name = person.get("name") or ""
    return not name.strip() or "unnamed" in name.lower()


def _ids(doc: dict) -> list:
    return [row.get("person_id") for row in doc.get("people", [])]


def check(committed: dict, derived: dict, people: dict) -> tuple[list, int]:
    """The four assertions. Returns (failures, cells that moved since the freeze)."""
    fails = []

    # 4 — everything outside the snapshot is compared exactly.
    for key in derived:
        if key in SNAPSHOT_DOC_KEYS or key == "people":
            continue
        if committed.get(key) != derived[key]:
            fails.append("%s differs from the derivation" % key)
    for key in committed:
        if key not in derived:
            fails.append("%s is in the committed manifest and not in the derivation" % key)

    # 1 — the ids, in order.
    have, want = _ids(committed), _ids(derived)
    if have != want:
        if set(have) == set(want):
            fails.append("the committed manifest holds the frame's people in a different order")
        else:
            gone = [p for p in have if p not in set(want)]
            new = [p for p in want if p not in set(have)]
            if gone:
                fails.append("the committed manifest claims people the frame no longer yields: %s"
                             % sorted(gone))
            if new:
                fails.append("the frame yields people the committed manifest does not claim: %s"
                             % sorted(new))

    moved = 0
    for row in committed.get("people", []):
        pid = row.get("person_id")
        # 2 — the person is still a real, named person in the tree.
        if pid not in people:
            fails.append("%s is claimed by the manifest and is in no household" % pid)
            continue
        if is_placeholder(people[pid][1]):
            fails.append("%s has become an unnamed placeholder, which no cohort may claim" % pid)
        # 3 — the row carries exactly the fields the selector emits.
        mirror = next((r for r in derived.get("people", []) if r.get("person_id") == pid), None)
        if mirror is None:
            continue
        if set(row) != set(mirror):
            fails.append("%s's row carries %s, and the selector emits %s"
                         % (pid, sorted(row), sorted(mirror)))
            continue
        moved += sum(1 for k in mirror if row[k] != mirror[k])
    return fails, moved


def preserve(committed: dict | None, derived: dict) -> tuple[dict, int]:
    """The document a regeneration may write. Returns (doc, cells held back).

    The derivation, with every snapshot cell the committed manifest already carries put
    back over it. A person the committed manifest does not hold is frozen at today's
    values; a document with no committed manifest beside it IS the freeze and passes
    through untouched.
    """
    if committed is None:
        return derived, 0
    doc = copy.deepcopy(derived)
    held = 0

    for key in SNAPSHOT_DOC_KEYS:
        if key in doc and key in committed:
            if doc[key] != committed[key]:
                held += 1
            doc[key] = copy.deepcopy(committed[key])

    frozen = {row.get("person_id"): row for row in committed.get("people", [])}
    for row in doc.get("people", []):
        was = frozen.get(row.get("person_id"))
        if was is None:
            continue
        for key in list(row):
            # A cell the committed row does not carry is a field the selector has
            # since started emitting; it freezes now, at today's value.
            if is_snapshot_key(key) and key in was:
                if row[key] != was[key]:
                    held += 1
                row[key] = copy.deepcopy(was[key])
    return doc, held


def write(path: Path, derived: dict, message: str) -> int:
    """Regenerate one manifest without rewriting its freeze."""
    committed = None
    if path.exists():
        committed = json.loads(path.read_text(encoding="utf-8"))
    doc, held = preserve(committed, derived)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    note = ""
    if held:
        note = ("; %d snapshot cell(s) held at the value the cohort was frozen with, "
                "which a regeneration may not rewrite" % held)
    print("%s%s" % (message, note))
    return 0


def gate(path: Path, derived: dict, label: str) -> int:
    """Run the gate for one committed manifest. Raises SystemExit on failure."""
    if not path.exists():
        raise SystemExit("%s does not exist; write it without --gate" % path.relative_to(ROOT))
    committed = json.loads(path.read_text(encoding="utf-8"))
    fails, moved = check(committed, derived, live_people())
    if fails:
        raise SystemExit("%s is not the frame's frozen cohort:\n  - %s"
                         % (path.relative_to(ROOT), "\n  - ".join(fails)))
    note = ""
    if moved:
        note = ("; %d snapshot cell(s) have moved since the freeze, which is the research "
                "landing and not staleness" % moved)
    print("%s: %d people, the frozen reservation is intact%s"
          % (label, len(committed.get("people", [])), note))
    return 0


# ------------------------------------------------ stratum membership (T-0870)


class Membership:
    """Whether a frozen member still matches the stratum it was DRAWN from.

    Two different questions wear the same shape in these selectors and only one of
    them is a defect. That a member has LEFT the town, turned into an unnamed count
    or gone `reconstructed` is staleness, and `check()` above refuses it on every
    path — that is assertion 2 of the gate contract. That a member's
    `letter_list_only` flag, or the presence value its stratum is named for, has
    MOVED in the tree is the research landing: it is the identical reading T-0764
    already takes of a moved snapshot cell, arriving through a different door. Until
    T-0870 it raised `SystemExit` on the `--gate` path and stopped the build.

    So the assertion is kept and its DIRECTION is scoped, exactly as
    `select_resident_research_pass_13.derive(minting=...)` scopes its own (T-0492).
    Minting a cohort still refuses a member the stratum no longer describes: the
    freeze is being taken, and a frame that does not match the tree is not a frame.
    Once frozen, the same finding is counted and named, and the gate stays green.

        drift = freeze.Membership(minting=not args.gate and not OUT.exists())
        ...
        drift.holds(bool(person.get("letter_list_only")),
                    "%s: no longer marked letter_list_only" % person_id)
        ...
        for line in drift.report("resident research pass two"):
            print(line)

    A selector that takes no `Membership` gets a frozen one, because minting is a
    rare and explicit act: `tools/compile_resident_research_pilot.py` re-derives pass
    five's cohort to compare against the committed manifest, and a flag that moved
    under a finished pass must not stop that comparison either.
    """

    def __init__(self, minting: bool):
        self.minting = minting
        self.moved: list[str] = []

    def holds(self, condition, message: str) -> bool:
        """Assert `condition` while minting; record it as moved once frozen."""
        if condition:
            return True
        if self.minting:
            raise SystemExit(message)
        self.moved.append(message)
        return False

    def report(self, label: str) -> list[str]:
        """The gate's lines for what moved — the voice `gate()` uses for a moved cell."""
        if not self.moved:
            return []
        return ["%s: %d member(s) have moved out of the stratum they were drawn from "
                "since the freeze, which is the research landing and not staleness"
                % (label, len(self.moved))] + ["   - %s" % line for line in self.moved]


def stratum_self_test(label: str, probes) -> int:
    """Prove a selector's stratum tests fire both ways (T-0870, acceptance 3).

    Each probe is `(case, run)` where `run(drift, moved)` puts ONE member through the
    selector's stratum test — `moved=True` for a member the stratum no longer
    describes, `moved=False` for one it still does. Four things must hold, and the
    last two are the ones this ticket bought:

      minting + unmoved  → nothing;      minting + moved  → SystemExit naming it;
      frozen  + unmoved  → nothing;      frozen  + moved  → one reported line, green.
    """
    bad = 0
    for case, run in probes:
        detail, ok = "", False
        try:
            run(Membership(minting=True), False)
            try:
                run(Membership(minting=True), True)
                detail = "minting did not refuse the moved member"
            except SystemExit as stop:
                quiet, noisy = Membership(minting=False), Membership(minting=False)
                run(quiet, False)
                run(noisy, True)
                if quiet.moved:
                    detail = "the gate reported an unmoved member: %s" % quiet.moved
                elif len(noisy.moved) != 1:
                    detail = "the gate reported %d line(s), wanted 1" % len(noisy.moved)
                elif noisy.moved[0] != str(stop):
                    detail = "minting said %r and the gate said %r" % (str(stop), noisy.moved[0])
                else:
                    ok, detail = True, noisy.moved[0]
        except SystemExit as stop:
            detail = "an unmoved member was refused: %s" % stop
        bad += 0 if ok else 1
        print("  %s %s → %s" % ("ok   " if ok else "FAIL ", case, detail[:110]))
    print("%s stratum self-test: %d case(s), %d failed" % (label, len(probes), bad))
    return 1 if bad else 0


# ---------------------------------------------------------------- the self-test

def _fixture():
    derived = {
        "_doc": "a cohort",
        "generated_by": "tools/select_resident_research_test.py",
        "population_frame": {"eligible_real_named_people": 400, "sample_size": 2},
        "people": [
            {"person_id": "a_one", "name": "A One", "stratum": "s", "starting_grade": "inferred"},
            {"person_id": "b_two", "name": "B Two", "stratum": "s", "starting_grade": "inferred"},
        ],
    }
    people = {"a_one": ({}, {"id": "a_one", "name": "A One"}),
              "b_two": ({}, {"id": "b_two", "name": "B Two"})}
    return derived, people


def self_test() -> int:
    derived, people = _fixture()
    cases, bad = [], 0

    def case(label, committed, live, expect_fail):
        nonlocal bad
        fails, _moved = check(committed, derived, live)
        ok = bool(fails) == expect_fail
        if not ok:
            bad += 1
        cases.append(("ok   " if ok else "FAIL ", label,
                      fails[0] if fails else "no failure"))

    case("the committed manifest IS the derivation", copy.deepcopy(derived), people, False)

    moved = copy.deepcopy(derived)
    moved["people"][0]["starting_grade"] = "attested"
    moved["population_frame"]["eligible_real_named_people"] = 999
    case("a snapshot cell moving is the research landing, not staleness", moved, people, False)

    reordered = copy.deepcopy(derived)
    reordered["people"].reverse()
    case("the ids in a different order fail", reordered, people, True)

    swapped = copy.deepcopy(derived)
    swapped["people"][0]["person_id"] = "c_three"
    case("a person the frame no longer yields fails", swapped, people, True)

    case("a person who has left the residents layer fails",
         copy.deepcopy(derived), {"a_one": people["a_one"]}, True)

    case("a person who has become an unnamed placeholder fails",
         copy.deepcopy(derived),
         {**people, "b_two": ({}, {"id": "b_two", "name": "The rest, unnamed"})}, True)

    dropped = copy.deepcopy(derived)
    del dropped["people"][1]["starting_grade"]
    case("a snapshot field dropped from a row fails", dropped, people, True)

    invented = copy.deepcopy(derived)
    invented["people"][1]["starting_trade"] = "cooper"
    case("a field invented on a row fails", invented, people, True)

    doc = copy.deepcopy(derived)
    doc["generated_by"] = "tools/somebody_elses_selector.py"
    case("a document field outside the snapshot must match exactly", doc, people, True)

    # ---- the write path: what a regeneration may and may not rewrite (T-0764)

    def wcase(label, ok, detail):
        nonlocal bad
        if not ok:
            bad += 1
        cases.append(("ok   " if ok else "FAIL ", label, detail))

    # The tree has moved under a committed cohort in every way it can: a grade rose, a
    # source landed, the household count changed, and one member moved house.
    committed = copy.deepcopy(derived)
    today = copy.deepcopy(derived)
    today["people"][0]["starting_grade"] = "attested"
    today["people"][0]["household_id"] = "hh_moved"
    today["people"][1]["stratum"] = "t"
    today["population_frame"]["eligible_real_named_people"] = 999
    kept, held = preserve(committed, today)

    wcase("a regeneration may not rewrite a starting_* cell",
          kept["people"][0]["starting_grade"] == "inferred",
          "starting_grade stayed %r" % kept["people"][0]["starting_grade"])
    wcase("a regeneration may not rewrite the population frame",
          kept["population_frame"]["eligible_real_named_people"] == 400,
          "frame stayed %r" % kept["population_frame"]["eligible_real_named_people"])
    wcase("a regeneration may not rewrite a member's stratum",
          kept["people"][1]["stratum"] == "s", "stratum stayed %r" % kept["people"][1]["stratum"])
    wcase("a regeneration DOES rewrite the tree's own identity cells",
          kept["people"][0]["household_id"] == "hh_moved",
          "household_id followed the tree to %r" % kept["people"][0]["household_id"])
    wcase("the held-back cells are counted and reported", held == 3, "held %d" % held)

    # A cohort with nothing committed beside it is being frozen right now.
    first, held_first = preserve(None, copy.deepcopy(today))
    wcase("the first write IS the freeze and passes through untouched",
          first == today and held_first == 0, "held %d" % held_first)

    # A person the committed manifest never held freezes at today's values.
    grew = copy.deepcopy(today)
    grew["people"].append({"person_id": "c_three", "name": "C Three", "stratum": "u",
                           "starting_grade": "attested"})
    kept2, _ = preserve(committed, grew)
    wcase("a member the freeze does not hold is frozen at today's values",
          kept2["people"][2]["starting_grade"] == "attested", "new member took today's grade")

    # And what is written stays gateable: the preserved document must pass check().
    fails, _ = check(kept, today, people)
    wcase("what a regeneration writes still passes the gate against today's derivation",
          not fails, fails[0] if fails else "no failure")

    # ---- a fold is a redirect, not a disappearance (T-0842)

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "merged").mkdir()
        (root / "merged" / "hh_folded.json").write_text(json.dumps({
            "id": "hh_folded",
            "merged_into": {"person": "b_two", "household": "hh_b"},
            "superseded_record": {"id": "hh_folded",
                                  "persons": [{"id": "c_folded", "name": "C Folded"}]},
        }), encoding="utf-8")
        (root / "index.json").write_text(json.dumps({
            "households": [],
            "merged": [{"person": "c_folded", "household": "hh_folded",
                        "merged_into_person": "b_two"}],
        }), encoding="utf-8")
        found = folded_people(root)
        wcase("a person a landed ruling folded is still resolvable, out of its stub",
              "c_folded" in found and found["c_folded"][1]["name"] == "C Folded",
              "resolved %s" % sorted(found))
        wcase("…and the stub is what is read, so a frozen snapshot cannot be rewritten "
              "by a later ruling",
              found["c_folded"][0]["id"] == "hh_folded",
              "read from %r" % found["c_folded"][0]["id"])
        wcase("…and the redirect table names the survivor, so a gate can say who carries them",
              folded_into(root).get("c_folded") == "b_two",
              "folded onto %r" % folded_into(root).get("c_folded"))
        (root / "merged" / "hh_folded.json").unlink()
        wcase("a person in no household AND no stub is still a failure — a deletion is "
              "not a redirect",
              "c_folded" not in folded_people(root), "gone is still gone")

    # ---- the membership scope: minting refuses, gating reports (T-0870)

    def mcase(label, ok, detail):
        nonlocal bad
        if not ok:
            bad += 1
        cases.append(("ok   " if ok else "FAIL ", label, detail))

    message = "a_one: no longer marked letter_list_only"
    try:
        Membership(minting=True).holds(False, message)
        refused = "it did not raise"
    except SystemExit as stop:
        refused = "" if str(stop) == message else "raised %r" % str(stop)
    mcase("minting REFUSES a member the stratum no longer describes",
          not refused, refused or "raised, with the member named")

    frozen = Membership(minting=False)
    unmoved = frozen.holds(True, "never reached")
    moved = frozen.holds(False, message)
    lines = frozen.report("a cohort")
    mcase("…and once frozen the same finding is reported, named, and green",
          unmoved and not moved and frozen.moved == [message] and len(lines) == 2
          and "research landing and not staleness" in lines[0]
          and lines[1] == "   - " + message,
          " | ".join(lines) or "nothing was reported")

    mcase("a cohort with nothing moved says nothing",
          Membership(minting=False).report("a cohort") == [], "no lines")

    for mark, label, detail in cases:
        print("  %s %s → %s" % (mark, label, detail[:110]))
    print("cohort freeze self-test: %d case(s), %d failed" % (len(cases), bad))
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    ap.error("nothing to do: --self-test is this file's only entry point")


if __name__ == "__main__":
    raise SystemExit(main())
