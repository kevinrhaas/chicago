#!/usr/bin/env python3
"""The one owner of data/residents/index.json (T-0715).

The manifest is a SUMMARY of data/residents/households/*.json and nothing else.
Every row's `head`, `division`, `persons`, `grades`, `lives_at`, `works_at`,
`present_on_scene_date`, `review_required` and its four evidence flags are
denormalised copies of the record on disk, and `counts` is a tally of those rows.

Before this module, four minting passes and four rewriting passes each patched
the SLICE of the manifest they owned and left the rest verbatim:

    keep = [r for r in index["households"] if r["id"] not in mine_ids]

So a household that no pass owned - an `hh_inf_*` inferred household, a
documented resident, a letter-list mint - could have its grade changed by any
other pass and keep a manifest row saying something else for ever, and the
totals, summed from the ROWS, inherited the error. Landing #797 found 18 such
households, 12 of them people this project had itself regraded, and no writer
in the tree would have healed them.

The fix is not a better patch. It is that the manifest has ONE derivation, over
the WHOLE layer, that every writer calls:

    from rebuild_resident_index import rebuild
    rebuild(index, docs)          # docs: {Path: household dict}, the whole layer

and that `tools/check.sh` re-derives it, so drift is a red build rather than a
hunt through 19 per-household errors.

    python3 tools/rebuild_resident_index.py --check      re-derive and compare
    python3 tools/rebuild_resident_index.py --write      re-derive and write
    python3 tools/rebuild_resident_index.py --self-test  break every rule on purpose

The argument list is PARSED, not sniffed (T-0871). It used to be read as
`"--write" in argv` and nothing else, so `--wrtie` typed for `--write` fell
through to the compare path, printed that the manifest re-derives, wrote
nothing, and exited 0 — the same quiet staleness T-0715 was opened about, one
level up. An unrecognised flag is now a refusal.

WHAT IT DOES NOT TOUCH: `_doc`, `version`, `scene_date`, `dossier`,
`vocabulary`, `researched_not_resident`, and any `counts` key that is not
derivable from the cards (the frozen
`reconstructed_removed_in_2026_09_02_synthesis` figure is the one today). Those
are authored, not summarised, and a derivation that overwrote them would be
deleting evidence to make a tally tidy.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESIDENTS = ROOT / "data" / "residents"
HOUSEHOLDS = RESIDENTS / "households"
INDEX = RESIDENTS / "index.json"

PROJECTED = "projected_resident"
GRADES = ("attested", "inferred", "reconstructed")

# The row's key order, fixed here rather than inherited from whichever pass
# happened to mint the household. Every committed shape is a subset of this
# order, so adopting it is a normalisation and not a reshuffle.
ROW_KEYS = ("id", "file", "letter_list_only", "civic_mint", "head", "division",
            "persons", "grades", "lives_at", "works_at", "present_on_scene_date",
            "review_required", PROJECTED, "census_1840_linked")

# The count keys this derivation owns. Anything else in `counts` is authored and
# is carried through untouched, in its committed position.
DERIVED_COUNTS = ("households", "persons", "by_grade", "letter_list_only",
                  "projected_residents", "census_1840_linked", "civic_mint")


def _value(field):
    """A record's fields are {value, confidence, ...} blocks; the row copies the value."""
    return field.get("value") if isinstance(field, dict) else field


def load_households(root: Path | None = None) -> dict[Path, dict]:
    """Every household card on disk, which is the whole input to the derivation."""
    houses = (root or HOUSEHOLDS)
    return {p: json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(houses.glob("*.json"))}


def household_docs(docs) -> dict[Path, dict]:
    """The household cards out of a pass's in-memory file map.

    Passes carry mixed maps - the manifest itself, a register, a proposal - so
    the filter is on the layer's own directory, not on the caller's discipline.
    """
    out = {}
    for path, doc in (docs or {}).items():
        path = Path(path)
        if path.name == "index.json" or path.suffix != ".json":
            continue
        if path.parent.name != "households":
            continue
        if isinstance(doc, (str, bytes)):
            doc = json.loads(doc)
        if isinstance(doc, dict) and doc.get("id"):
            out[path] = doc
    return out


def row_for(path: Path, doc: dict) -> dict:
    """One manifest row, derived from one household card and nothing else."""
    persons = doc.get("persons") or []
    tally: dict[str, int] = {}
    for person in persons:
        grade = person.get("grade")
        if grade:
            tally[grade] = tally.get(grade, 0) + 1
    row = {
        "id": doc.get("id"),
        "file": f"households/{path.name}",
        "head": doc.get("head"),
        "division": doc.get("division"),
        "persons": len(persons),
        "grades": dict(sorted(tally.items())),
        "lives_at": _value(doc.get("lives_at")),
        "works_at": _value(doc.get("works_at")),
        "present_on_scene_date": _value(doc.get("present_on_scene_date")),
        "review_required": bool(doc.get("review_required")),
    }
    # The evidence flags, each present only when true - the shape the manifest
    # already carries, and the shape the Evidence panel reads.
    if any(p.get("letter_list_only") for p in persons):
        row["letter_list_only"] = True
    if any(p.get("civic_mint") for p in persons):
        row["civic_mint"] = True
    if any(p.get("resident_subtype") == PROJECTED for p in persons):
        row[PROJECTED] = True
    linked = sum(1 for p in persons if p.get("later_census"))
    if linked:
        row["census_1840_linked"] = linked
    return {k: row[k] for k in ROW_KEYS if k in row}


def rebuild(index: dict, docs=None) -> dict:
    """Re-derive EVERY row and every derived count from the cards, in place.

    `docs` is a pass's in-memory {path: household} map - the whole layer as that
    pass will leave it, not the slice it minted. Omit it to read the committed
    cards off disk.
    """
    houses = household_docs(docs) if docs is not None else load_households()
    rows = sorted((row_for(path, doc) for path, doc in houses.items()),
                  key=lambda r: r["id"])
    index["households"] = rows

    grades = {g: 0 for g in GRADES}
    for row in rows:
        for grade, n in row["grades"].items():
            grades[grade] = grades.get(grade, 0) + n
    people = [p for doc in houses.values() for p in (doc.get("persons") or [])]
    derived = {
        "households": len(rows),
        "persons": sum(r["persons"] for r in rows),
        "by_grade": grades,
        "letter_list_only": sum(1 for p in people if p.get("letter_list_only")),
        "projected_residents": sum(1 for p in people
                                   if p.get("resident_subtype") == PROJECTED),
        "census_1840_linked": sum(1 for p in people if p.get("later_census")),
        "civic_mint": sum(1 for p in people if p.get("civic_mint")),
    }
    counts = dict(index.get("counts") or {})
    counts.update(derived)                       # in place for keys already there
    index["counts"] = counts
    return index


def dumps(obj) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=False) + "\n"


def differences(committed: dict, derived: dict, limit: int = 12) -> list[str]:
    """Human sentences for what drifted, ordered rows-then-counts."""
    out: list[str] = []
    was = {r.get("id"): r for r in committed.get("households") or []}
    now = {r.get("id"): r for r in derived.get("households") or []}
    for hid in sorted(set(was) | set(now)):
        a, b = was.get(hid), now.get(hid)
        if a == b:
            continue
        if a is None:
            out.append(f"household '{hid}' has a card and no manifest row")
        elif b is None:
            out.append(f"household '{hid}' has a manifest row and no card")
        else:
            for key in sorted(set(a) | set(b)):
                if a.get(key) != b.get(key):
                    out.append(f"household '{hid}' {key}: manifest {a.get(key)!r}, "
                               f"cards {b.get(key)!r}")
    ca, cb = committed.get("counts") or {}, derived.get("counts") or {}
    for key in DERIVED_COUNTS:
        if ca.get(key) != cb.get(key):
            out.append(f"counts.{key}: manifest {ca.get(key)!r}, cards {cb.get(key)!r}")
    if len(out) > limit:
        out = out[:limit] + [f"… and {len(out) - limit} more"]
    return out


FIX = "python3 tools/rebuild_resident_index.py --write"


# --- the self-test -----------------------------------------------------------
#
# T-0871. This was the only re-derivation gate in the tree without one, and a
# rule that has never been shown to fail is a rule nobody has tested. The case
# list is the one PR #926 carried — an independent implementation of T-0715 that
# #924 beat to the merge — rewritten against dev's `rebuild(index, docs)`.
#
# Nothing here touches data/residents/index.json. The town below is three people
# in two households, built in memory: `household_docs` filters on the parent
# directory's NAME, so these paths never have to exist on disk.

def _card(hid: str, persons: list[dict], **fields) -> tuple[Path, dict]:
    """One synthetic household card, addressed as if it sat in the layer."""
    doc = {"id": hid, "head": fields.pop("head", f"{hid}_head"),
           "division": fields.pop("division", "north"), "persons": persons}
    doc.update(fields)
    return HOUSEHOLDS / f"{hid}.json", doc


def _copy(obj):
    return json.loads(json.dumps(obj))


def self_test() -> int:
    """Every rule the derivation follows and every refusal --check makes, broken."""
    fails: list[str] = []

    def check_that(label, cond):
        if not cond:
            fails.append(label)
        print(("  ok   " if cond else "  FAIL ") + label)

    a_path, a_doc = _card(
        "hh_a",
        [{"id": "p_a1", "grade": "attested", "civic_mint": True},
         {"id": "p_a2", "grade": "inferred", "letter_list_only": True,
          "later_census": "1840_head_0001"}],
        lives_at={"value": "Lake Street", "confidence": "documented"},
        present_on_scene_date={"value": True, "confidence": "inferred"})
    b_path, b_doc = _card(
        "hh_b",
        [{"id": "p_b1", "grade": "reconstructed", "resident_subtype": PROJECTED}],
        review_required=True)
    docs = {a_path: a_doc, b_path: b_doc}

    derived = rebuild({"counts": {}}, docs)
    rows = {r["id"]: r for r in derived["households"]}
    counts = derived["counts"]

    # --- what the derivation says -------------------------------------------
    check_that("grades tally the persons, household by household and in total",
               rows["hh_a"]["grades"] == {"attested": 1, "inferred": 1}
               and rows["hh_b"]["grades"] == {"reconstructed": 1}
               and counts["by_grade"] == {"attested": 1, "inferred": 1,
                                          "reconstructed": 1})
    check_that("a flag is written only when it is true",
               rows["hh_a"].get("letter_list_only") is True
               and rows["hh_a"].get("civic_mint") is True
               and rows["hh_a"].get("census_1840_linked") == 1
               and "letter_list_only" not in rows["hh_b"]
               and "civic_mint" not in rows["hh_b"]
               and "census_1840_linked" not in rows["hh_b"])
    check_that("projected_resident comes off the person's resident_subtype",
               rows["hh_b"].get(PROJECTED) is True and PROJECTED not in rows["hh_a"])
    check_that("every derived count is the tally of the cards, not of the old file",
               counts["households"] == 2 and counts["persons"] == 3
               and counts["letter_list_only"] == 1
               and counts["projected_residents"] == 1
               and counts["census_1840_linked"] == 1
               and counts["civic_mint"] == 1)
    check_that("a {value, confidence} block contributes its value, and an "
               "unstated one reads as None",
               rows["hh_a"]["lives_at"] == "Lake Street"
               and rows["hh_a"]["present_on_scene_date"] is True
               and rows["hh_b"]["lives_at"] is None
               and rows["hh_b"]["works_at"] is None)
    check_that("review_required is a bool on every row, stated or not",
               rows["hh_b"]["review_required"] is True
               and rows["hh_a"]["review_required"] is False)
    check_that("key order is canonical, whatever order the card carried",
               all(list(r) == [k for k in ROW_KEYS if k in r] for r in rows.values()))
    check_that("rows are ordered by id, not by the filesystem",
               [r["id"] for r in derived["households"]] == ["hh_a", "hh_b"])

    again = rebuild(_copy(derived), docs)
    check_that("a rebuild of a rebuild is a no-op",
               dumps(again) == dumps(derived))

    authored = rebuild({"counts": {"reconstructed_removed_in_2026_09_02_synthesis": 7,
                                   "households": 99}}, docs)["counts"]
    check_that("an authored count is carried through untouched, in its own place",
               authored["reconstructed_removed_in_2026_09_02_synthesis"] == 7
               and authored["households"] == 2
               and list(authored)[0] == "reconstructed_removed_in_2026_09_02_synthesis")

    # --- what --check refuses, each broken on purpose ------------------------
    check_that("a manifest that matches its cards reports nothing",
               differences(_copy(derived), derived) == [])

    regraded = _copy(derived)
    regraded["households"][0]["grades"] = {"attested": 2}
    check_that("a row whose grade disagrees with its card is caught",
               any("hh_a" in d and "grades" in d for d in differences(regraded, derived)))

    no_row = _copy(derived)
    no_row["households"] = [r for r in no_row["households"] if r["id"] != "hh_b"]
    check_that("a card with no manifest row is caught",
               any("has a card and no manifest row" in d
                   for d in differences(no_row, derived)))

    no_card = _copy(derived)
    no_card["households"].append({"id": "hh_z", "file": "households/hh_z.json"})
    check_that("a manifest row with no card is caught",
               any("has a manifest row and no card" in d
                   for d in differences(no_card, derived)))

    ghost_key = _copy(derived)
    ghost_key["households"][0]["nickname"] = "the brick row"
    check_that("a row key no derivation emits is named, not ignored",
               any("nickname" in d for d in differences(ghost_key, derived)))

    false_flag = _copy(derived)
    false_flag["households"][1]["letter_list_only"] = True
    check_that("a flag written when it is false is caught",
               any("hh_b" in d and "letter_list_only" in d
                   for d in differences(false_flag, derived)))

    moved = []
    for key in DERIVED_COUNTS:
        broken = _copy(derived)
        was = broken["counts"][key]
        broken["counts"][key] = {"attested": 999} if isinstance(was, dict) else 999
        if not any(d.startswith(f"counts.{key}:") for d in differences(broken, derived)):
            moved.append(key)
    check_that(f"each of the {len(DERIVED_COUNTS)} derived counts is caught when "
               f"moved ({', '.join(DERIVED_COUNTS)})", not moved)

    over = _copy(derived)
    over["households"] = [dict(r, persons=r["persons"] + 1) for r in over["households"]]
    check_that("the drift report is capped, and says how many it did not print",
               any("more" in d for d in differences(over, derived, limit=1)))

    # --- what the argument list refuses --------------------------------------
    #
    # The fault this ticket is named for: `--wrtie` used to report success and
    # write nothing. Run for real, because it is the PARSER under test and an
    # in-process call would not exercise it.
    def run(*args):
        return subprocess.run([sys.executable, str(Path(__file__).resolve()), *args],
                              capture_output=True, text=True)

    typo = run("--wrtie")
    check_that("a typo'd --write is REFUSED, not silently read as a check",
               typo.returncode != 0 and "--wrtie" in (typo.stderr + typo.stdout))
    check_that("...and an unrecognised flag of any kind is refused too",
               run("--nonsense-flag").returncode != 0
               and run("--selftest").returncode != 0)
    check_that("--check still passes on the committed manifest",
               run("--check").returncode == 0)

    print(f"\n{len(fails)} failure(s)")
    return 1 if fails else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Re-derive data/residents/index.json from the household cards.")
    ap.add_argument("--check", action="store_true",
                    help="re-derive and compare (the default, and what check.sh runs)")
    ap.add_argument("--write", action="store_true", help="re-derive and write")
    ap.add_argument("--self-test", action="store_true",
                    help="prove every assertion above fires when broken")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    committed = json.loads(INDEX.read_text(encoding="utf-8"))
    derived = rebuild(json.loads(json.dumps(committed)))
    if args.write:
        # The published mirror is NOT a copy - tools/publish.sh transforms the
        # residents layer and check_published_residents.mjs gates the transform -
        # so this writes the source and leaves the mirror to the publisher.
        INDEX.write_text(dumps(derived), encoding="utf-8")
        print(f"rebuilt {INDEX.relative_to(ROOT)} from "
              f"{derived['counts']['households']} household cards")
        return 0
    if dumps(committed) == dumps(derived):
        print(f"data/residents/index.json re-derives from its "
              f"{derived['counts']['households']} household cards")
        return 0
    print("data/residents/index.json is DERIVED from the household cards and no "
          "longer matches them.\n"
          f"  The cards are authoritative. Run: {FIX}\n"
          "  What drifted:", file=sys.stderr)
    for line in differences(committed, derived):
        print(f"    {line}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
