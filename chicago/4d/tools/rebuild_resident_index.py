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

THE REDIRECT TABLE IS THE SECOND HALF OF THE SAME RULE (T-1144 acceptance 6).
`merged` is one row per card folded onto another, and the card it summarises is
`data/residents/merged/*.json` — kept whole, with a `merged_into` block, and
never deleted. That table was the one list in the manifest nobody derived, and
it had drifted in both directions by the time this was written:

  * `hh_vanderbogart_h` was retired under T-0842 and given NO row at all, so the
    id resolved to nothing — while the retired record itself says, in its own
    note, that "data/residents/index.json's `merged` table redirects the id".
  * `hh_blanchard_gantry` was carried under rule `C7`. T-0993 minted `C8` for
    that fold in the same ticket that made it, and `card_merge_rulings.json`
    says `C8`; `C7` is now the compound-surname particle rule, which is a
    different argument about a different name. The manifest row was the only
    place in the tree still naming the old letter to a reader.

Both are the shape T-0715 was opened about — a summary nobody re-derives — so
the answer is the same one: the RECORDS are authoritative, `merged` is derived
from them, and `tools/check.sh` re-derives it. On top of the tally this asserts
that every redirect ARRIVES: the household and person it names are live cards,
no retired id shadows a live one, and no redirect points at another retired
card. A redirect that does not arrive is refused, in `--check` and in `--write`
both, because writing it would publish a dead end.

WHAT IT DOES NOT TOUCH: `_doc`, `version`, `scene_date`, `dossier`,
`vocabulary`, `researched_not_resident`, `_merged_doc`, and any `counts` key
that is not derivable from the cards (the frozen
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
MERGED = RESIDENTS / "merged"
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
                  "projected_residents", "census_1840_linked", "civic_mint",
                  "merged_away")

# One redirect row, derived from one retired record in data/residents/merged/.
# The order is the committed one; every key is copied from the record's own
# `merged_into` block except `name`, which is read off the person the fold
# retired, inside the superseded card kept beneath it.
MERGED_ROW_KEYS = ("person", "household", "name", "merged_into_person",
                   "merged_into_household", "record_file", "rule", "cluster",
                   "ticket")


def _value(field):
    """A record's fields are {value, confidence, ...} blocks; the row copies the value."""
    return field.get("value") if isinstance(field, dict) else field


def load_households(root: Path | None = None) -> dict[Path, dict]:
    """Every household card on disk, which is the whole input to the derivation."""
    houses = (root or HOUSEHOLDS)
    return {p: json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(houses.glob("*.json"))}


def load_retired(root: Path | None = None) -> dict[Path, dict]:
    """Every retired card on disk, which is the whole input to the redirect table."""
    folder = (root or MERGED)
    if not folder.is_dir():
        return {}
    return {p: json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(folder.glob("*.json"))}


def retired_docs(docs) -> dict[Path, dict]:
    """The retired cards out of a pass's in-memory file map, by directory name.

    The same filter as `household_docs` one directory over. A pass that carries
    none is the ordinary case — all eight callers of `rebuild` write households
    and none of them retires a card — and `rebuild` reads the committed records
    off disk for them rather than deriving an empty table from their silence.
    """
    out = {}
    for path, doc in (docs or {}).items():
        path = Path(path)
        if path.suffix != ".json" or path.parent.name != "merged":
            continue
        if isinstance(doc, (str, bytes)):
            doc = json.loads(doc)
        if isinstance(doc, dict) and doc.get("id"):
            out[path] = doc
    return out


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


def merged_row_for(path: Path, doc: dict) -> dict:
    """One redirect row, derived from one retired record and nothing else."""
    into = doc.get("merged_into") or {}
    retired_person = into.get("person_merged")
    row = {
        "person": retired_person,
        "household": doc.get("id"),
        "name": _retired_name(doc, retired_person),
        "merged_into_person": into.get("person"),
        "merged_into_household": into.get("household"),
        "record_file": f"merged/{path.name}",
        "rule": into.get("rule"),
        "cluster": into.get("cluster"),
        "ticket": into.get("ticket"),
    }
    return {k: row[k] for k in MERGED_ROW_KEYS}


def _retired_name(doc: dict, person_id: str | None) -> str | None:
    """The retired person's name, as the superseded card itself printed it."""
    card = doc.get("superseded_record") or {}
    for person in card.get("persons") or []:
        if person.get("id") == person_id:
            return person.get("name")
    return None


def redirect_faults(index: dict, docs=None) -> list[str]:
    """Where a redirect does not ARRIVE at a live card. Empty is the only pass.

    The tally above can be perfectly re-derived and still describe a dead end:
    a row is a promise that an id resolves, and nothing was checking that the
    id it resolves TO is still in the layer. Four ways it can fail, and each is
    a sentence rather than a flag, because the repair differs for each.
    """
    houses = household_docs(docs) if docs is not None else load_households()
    live_households = {doc.get("id") for doc in houses.values()}
    live_persons = {person.get("id")
                    for doc in houses.values()
                    for person in (doc.get("persons") or [])}
    rows = index.get("merged") or []
    retired_ids = {row.get("household") for row in rows}

    out: list[str] = []
    for row in rows:
        rid, target = row.get("household"), row.get("merged_into_household")
        missing = [k for k in MERGED_ROW_KEYS if k != "name" and not row.get(k)]
        if missing:
            out.append(f"retired '{rid}' states no {', '.join(missing)}")
        if target in retired_ids:
            out.append(f"retired '{rid}' redirects to '{target}', which is itself "
                       f"retired — a redirect may not point at another redirect")
        elif target not in live_households:
            out.append(f"retired '{rid}' redirects to '{target}', which is not a "
                       f"household card")
        if row.get("merged_into_person") not in live_persons:
            out.append(f"retired '{rid}' redirects to person "
                       f"'{row.get('merged_into_person')}', who is in no household card")
        if rid in live_households:
            out.append(f"'{rid}' is retired and is also a live household card")
    return out


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

    # The retired cards. A caller's map carries them only if that pass retires
    # a card, and none of the eight does; for everyone else the committed
    # records ARE the layer, and reading an empty table out of a pass that was
    # never asked about redirects would delete 66 of them.
    retired = retired_docs(docs) or load_retired()
    index["merged"] = sorted(
        (merged_row_for(path, doc) for path, doc in retired.items()),
        key=lambda r: r["household"] or "")

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
        "merged_away": len(index["merged"]),
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
    was_m = {r.get("household"): r for r in committed.get("merged") or []}
    now_m = {r.get("household"): r for r in derived.get("merged") or []}
    for rid in sorted(set(was_m) | set(now_m), key=lambda x: x or ""):
        a, b = was_m.get(rid), now_m.get(rid)
        if a == b:
            continue
        if a is None:
            out.append(f"retired '{rid}' has a record and no redirect row, so the "
                       f"id resolves to nothing")
        elif b is None:
            out.append(f"retired '{rid}' has a redirect row and no record in "
                       f"data/residents/merged/")
        else:
            for key in sorted(set(a) | set(b)):
                if a.get(key) != b.get(key):
                    out.append(f"retired '{rid}' {key}: manifest {a.get(key)!r}, "
                               f"record {b.get(key)!r}")
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


def _retired(hid: str, person: str, into_person: str, into_household: str,
             **fields) -> tuple[Path, dict]:
    """One synthetic retired card, addressed as if it sat beside the live ones."""
    doc = {"id": hid,
           "merged_into": {"person": into_person, "household": into_household,
                           "person_merged": person,
                           "rule": fields.pop("rule", "C0"),
                           "cluster": fields.pop("cluster", "cluster"),
                           "ticket": fields.pop("ticket", "T-0839")},
           "superseded_record": {
               "id": hid,
               "persons": [{"id": person, "name": fields.pop("name", "A Name")}]}}
    doc.update(fields)
    return MERGED / f"{hid}.json", doc


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

    # --- the redirect table, and every way it can lie (T-1144 acceptance 6) --
    r_path, r_doc = _retired("hh_z_old", "p_z_old", "p_a1", "hh_a",
                             rule="C8", cluster="z", ticket="T-0993",
                             name="Zeb Old")
    r2_path, r2_doc = _retired("hh_y_old", "p_y_old", "p_b1", "hh_b")
    with_retired = dict(docs)
    with_retired[r_path], with_retired[r2_path] = r_doc, r2_doc
    red = rebuild({"counts": {}}, with_retired)
    mrows = {r["household"]: r for r in red["merged"]}

    check_that("a redirect row is the retired record's own merged_into block, "
               "and the retired name is read off the superseded card beneath it",
               mrows["hh_z_old"] == {
                   "person": "p_z_old", "household": "hh_z_old", "name": "Zeb Old",
                   "merged_into_person": "p_a1", "merged_into_household": "hh_a",
                   "record_file": "merged/hh_z_old.json", "rule": "C8",
                   "cluster": "z", "ticket": "T-0993"})
    check_that("redirect rows are ordered by the retired id, and tallied",
               [r["household"] for r in red["merged"]] == ["hh_y_old", "hh_z_old"]
               and red["counts"]["merged_away"] == 2)
    check_that("a pass that retires no card keeps the committed redirect table "
               "instead of deriving an empty one out of its silence",
               len(rebuild({"counts": {}}, docs)["merged"]) == len(load_retired()))
    check_that("a sound layer's redirects all arrive",
               redirect_faults(red, with_retired) == [])

    dead = _copy(red)
    dead["merged"][0]["merged_into_household"] = "hh_gone"
    check_that("a redirect to a household that is not a card is refused",
               any("is not a household card" in f
                   for f in redirect_faults(dead, with_retired)))

    chained = _copy(red)
    chained["merged"][0]["merged_into_household"] = "hh_z_old"
    check_that("a redirect that points at another retired card is refused",
               any("is itself retired" in f
                   for f in redirect_faults(chained, with_retired)))

    ghost = _copy(red)
    ghost["merged"][0]["merged_into_person"] = "p_gone"
    check_that("a redirect to a person who is in no household card is refused",
               any("is in no household card" in f
                   for f in redirect_faults(ghost, with_retired)))

    shadow = _copy(red)
    shadow["merged"][0]["household"] = "hh_a"
    check_that("a retired id that is also a live card is refused",
               any("is also a live household card" in f
                   for f in redirect_faults(shadow, with_retired)))

    blank = _copy(red)
    blank["merged"][0]["rule"] = None
    check_that("a redirect that states no rule is refused",
               any("states no rule" in f for f in redirect_faults(blank, with_retired)))

    # The two drifts this ticket found on `dev`, each as a case.
    lost = _copy(red)
    lost["merged"] = [r for r in lost["merged"] if r["household"] != "hh_z_old"]
    check_that("a retired record with no redirect row is caught, and the sentence "
               "says the id resolves to nothing (hh_vanderbogart_h, T-0842)",
               any("resolves to nothing" in d for d in differences(lost, red)))

    stale = _copy(red)
    stale["merged"][1]["rule"] = "C7"
    check_that("a redirect row whose rule disagrees with its record is caught "
               "(hh_blanchard_gantry, T-0993)",
               any("hh_z_old" in d and "rule" in d for d in differences(stale, red)))

    orphan = _copy(red)
    orphan["merged"].append({"household": "hh_none"})
    check_that("a redirect row with no record behind it is caught",
               any("no record in" in d for d in differences(orphan, red)))

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

    # A redirect that does not arrive is refused BEFORE the drift comparison,
    # and in --write as well as --check: the table can re-derive perfectly and
    # still send a reader to a card that is not there. The records are the
    # repair, not the manifest.
    faults = redirect_faults(derived)
    if faults:
        print("data/residents/merged/ holds a redirect that does not arrive at a "
              "live card:", file=sys.stderr)
        for line in faults:
            print(f"    {line}", file=sys.stderr)
        print("  Fix the retired record, or the household it names. The manifest "
              "is derived and is not the place to patch this.", file=sys.stderr)
        return 1

    if args.write:
        # The published mirror is NOT a copy - tools/publish.sh transforms the
        # residents layer and check_published_residents.mjs gates the transform -
        # so this writes the source and leaves the mirror to the publisher.
        INDEX.write_text(dumps(derived), encoding="utf-8")
        print(f"rebuilt {INDEX.relative_to(ROOT)} from "
              f"{derived['counts']['households']} household cards and "
              f"{derived['counts']['merged_away']} retired records")
        return 0
    if dumps(committed) == dumps(derived):
        print(f"data/residents/index.json re-derives from its "
              f"{derived['counts']['households']} household cards, and every one "
              f"of its {derived['counts']['merged_away']} redirects arrives at a "
              f"live card")
        return 0
    print("data/residents/index.json is DERIVED from the household cards and the "
          "retired records, and no longer matches them.\n"
          f"  The cards are authoritative. Run: {FIX}\n"
          "  What drifted:", file=sys.stderr)
    for line in differences(committed, derived):
        print(f"    {line}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
