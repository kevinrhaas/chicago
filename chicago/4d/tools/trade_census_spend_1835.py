#!/usr/bin/env python3
"""SPENDING THE DECEMBER 1835 TRADE CENSUS: who the town can actually name.

T-1006 set the town against `bk_mose1_006` — the State count taken between
1 September and December 1835 — and left five classes SHORT and three empty.
This is the other half, T-1007: what the corpus can honestly put against those
gaps, and what is left over when it has.

    tools/trade_census_spend_1835.py --build       write the spend record
    tools/trade_census_spend_1835.py --check       re-derive it and refuse drift
    tools/trade_census_spend_1835.py --self-test   the guards, fired on fixtures

THE FINDING THIS TOOL EXISTS TO CARRY.  The business register is compiled from
PRINTED NOTICES, so its four "physician" records are four physician ADVERTISEMENTS
and never were the town's physicians.  Five more doctors — Egan, Harmon, Goodhue,
Kimberly and Temple — have sat on resident cards off Andreas and the Democrat the
whole time with no business record anywhere, because a physician with a practice
does not have to advertise it.  The same is true of Pruyne and Kimberly's drug
store, the second in the town, which no surviving notice advertises.  Joining the
two layers is the whole of the shortfall this project can close without inventing
anybody, and the residue after it is the measured gap.

AND THE SECOND FINDING, WHICH CHANGES THE SIZE OF THE FIRST.  The census's lawyer
and physician lines count PEOPLE; the register counts RECORDS.  Nineteen lawyer
records are fourteen men — Caton alone holds four of them, under three spellings
of his own name and one firm — so the lawyer shortfall is eight and not three.
A comparison that does not say which unit it is counting in is not a comparison.

WHAT THIS TOOL MAY NOT DO.  It creates no person, no business and no building; it
raises no confidence; it merges no two names into one.  Every practitioner it
counts is already in this repository and the ruling is only ever which layer holds
him.  Where nothing names anybody the count stays short and says so — under the
owner's 2026-09-02 ruling the ceiling on such a gap is anonymous stock, never an
invented man.  Its refusals are as load-bearing as its counts and are written out
rather than dropped.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTER = ROOT / "data" / "research" / "newspapers" / "register_1835.json"
CROSSWALK = ROOT / "data" / "research" / "books" / "trade_census_1835_crosswalk.json"
RULINGS = ROOT / "data" / "research" / "books" / "trade_census_1835_spend_rulings.json"
SPEND = ROOT / "data" / "research" / "books" / "trade_census_1835_spend.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
STRUCTURES = ROOT / "data" / "structures"

SCENE_DATE = "1835-07-01"
DATE_CAUTION = (
    "THE COUNT IS NOT OF THE SCENE, and spending it does not make it so. It was taken "
    "between 1 September and December 1835; the scene is 1 July 1835. Every practitioner "
    "named below stands in the July town on the evidence of his OWN card or notice and "
    "never on the census's arithmetic, and where the count is still short after them the "
    "residue is a measured gap and not a hole to fill with people."
)


class Fault(Exception):
    """A defect in the rulings, phrased for the person who must fix it."""


# ---------------------------------------------------------------------------
# the join


def build(register: dict, crosswalk: dict, rulings: dict, residents: dict,
          structures: set) -> dict:
    """One row per ruled class: who is named, in which layer, and what is left."""
    ruled = {c["class"]: c for c in rulings["classes_ruled"]}
    if not ruled:
        raise Fault("no class is ruled at all")

    by_class = {c["class"]: c for c in crosswalk["classes"]}
    for name in ruled:
        if name not in by_class:
            raise Fault(f"a class the T-1006 crosswalk does not hold: {name}")

    businesses = {b["id"] for b in register["businesses"]}
    occ_map = _occupation_map(rulings)

    # every practitioner must resolve, in whichever layer claims him
    seen_keys, assigned = set(), set()
    for row in rulings["practitioners"]:
        key = row["key"]
        if key in seen_keys:
            raise Fault(f"two practitioner rulings under one key: {key}")
        seen_keys.add(key)
        if not str(row.get("basis") or "").strip():
            raise Fault(f"a practitioner ruling with no basis: {key}")
        if not row["classes"]:
            raise Fault(f"a practitioner ruling that names no class: {key}")
        for cls in row["classes"]:
            if cls not in ruled:
                raise Fault(f"practitioner {key} is put on a class this file does not rule: {cls}")
        pid = row.get("person_id")
        if pid is not None and pid not in residents:
            raise Fault(f"practitioner {key} names a person the residents layer does not hold: {pid}")
        for bid in row["business_ids"]:
            if bid not in businesses:
                raise Fault(f"practitioner {key} names a business the register does not hold: {bid}")
            assigned.add(bid)
        if pid is None and not row["business_ids"]:
            raise Fault(f"practitioner {key} stands in neither layer — no card and no notice. "
                        "This file may not mint a man from a census line.")

    for row in rulings["register_records_not_assigned"]:
        if row["business_id"] not in businesses:
            raise Fault(f"an unassigned record naming no business: {row['business_id']}")
        if not str(row.get("basis") or "").strip():
            raise Fault(f"an unassigned record with no basis: {row['business_id']}")
        assigned.add(row["business_id"])

    # THE SILENT-OMISSION GUARD, BOTH WAYS.
    # Every register record on a ruled class must be somebody's or explicitly nobody's,
    # and every resident card whose occupation counts must be somebody. Either omission
    # would shrink the town quietly, which is the one failure T-0988 was written to end.
    for name in ruled:
        for bid in by_class[name]["business_ids"]:
            if bid not in assigned:
                raise Fault(
                    f"the register's {bid} carries the {name} class and no practitioner "
                    "ruling claims it. Assign it, or list it under "
                    "register_records_not_assigned with the reason it names nobody.")

    claimed_people = {r["person_id"] for r in rulings["practitioners"] if r.get("person_id")}
    refusals = []
    for pid, person in sorted(residents.items()):
        rule = occ_map.get(person["occupation"])
        if rule is None:
            continue
        if not rule["counts"]:
            refusals.append({
                "person_id": pid, "name": person["name"], "occupation": person["occupation"],
                "would_be_class": rule["class"], "refused_because": rule["basis"],
            })
            continue
        if pid not in claimed_people:
            raise Fault(
                f"{pid} is on a resident card as {person['occupation']!r}, which this file "
                f"counts on the {rule['class']} line, and no practitioner ruling holds him. "
                "A card the count cannot see is a man the town loses.")

    classes = []
    for name, rule in ((n, ruled[n]) for n in ruled):
        holders = [r for r in rulings["practitioners"] if name in r["classes"]]
        establishments = sorted({r["establishment"] for r in holders})
        unnamed = [r for r in rulings["register_records_not_assigned"] if r["class"] == name]
        from_cards = [r for r in holders if not r["business_ids"]]
        unit = rule["unit"]
        held = len(establishments) if unit == "establishment" else len(holders)
        held += len(unnamed)
        classes.append({
            "class": name,
            "census_line": rule["census_line"],
            "census_count": rule["census_count"],
            "unit": unit,
            "unit_basis": rule["unit_basis"],
            "register_records": len(by_class[name]["business_ids"]),
            "named_practitioners": len(holders),
            "named_establishments": len(establishments),
            "held_in_the_counted_unit": held,
            "unnamed_records_held": len(unnamed),
            "not_reached": max(0, rule["census_count"] - held),
            "spent_from_resident_cards": [
                {"key": r["key"], "name": r["name"], "person_id": r["person_id"],
                 "establishment": r["establishment"], "basis": r["basis"]}
                for r in from_cards
            ],
            "practitioner_keys": [r["key"] for r in holders],
            "residual_rule": rule["residual_rule"],
        })

    for inst in rulings["institutions"]:
        if inst["has_building"]:
            raise Fault(f"{inst['id']} is recorded with a building. The census's lyceum line "
                        "is answered by a society, and T-1007 forbids raising a roof for it.")
        for link in inst["links"]:
            if link["kind"] == "structure" and link["id"] not in structures:
                raise Fault(f"{inst['id']} links a structure the town does not hold: {link['id']}")
            if link["kind"] == "person" and link["id"] not in residents:
                raise Fault(f"{inst['id']} links a person the residents layer does not hold: {link['id']}")

    for gap in rulings["documented_absences"]:
        if gap["absence_kind"] == "notice_of_absence" and not gap["claims"]:
            raise Fault(f"{gap['id']} is called a notice of absence and cites no notice")
        if gap["absence_kind"] == "no_corpus_record" and gap["claims"]:
            raise Fault(f"{gap['id']} is called a gap in the corpus and then cites the corpus")

    totals = {
        "classes_spent": len(classes),
        "census_counted_across_them": sum(c["census_count"] for c in classes),
        "held_after_the_spend": sum(c["held_in_the_counted_unit"] for c in classes),
        "not_reached": sum(c["not_reached"] for c in classes),
        "practitioners_ruled": len(rulings["practitioners"]),
        "class_rows_spent_from_resident_cards": sum(
            len(c["spent_from_resident_cards"]) for c in classes),
        "people_spent_from_resident_cards": len({
            r["person_id"] for c in classes for r in c["spent_from_resident_cards"]}),
        "institutions_recorded": len(rulings["institutions"]),
        "documented_absences": len(rulings["documented_absences"]),
        "refusals": len(refusals),
    }

    return {
        "schema": 1,
        "domain": "books",
        "source_id": rulings["source_id"],
        "claim_id": rulings["claim_id"],
        "generated_by": "tools/trade_census_spend_1835.py --build",
        "ticket": "T-1007",
        "not_a_reading": (
            "an adjudication over records this project already holds — the business "
            "register, the residents layer and four newspaper notices — set against a "
            "count it already read. No page of any source is read here."
        ),
        "_doc": __doc__,
        "scene_date": SCENE_DATE,
        "census_window": crosswalk["census_window"],
        "date_caution": DATE_CAUTION,
        "creates_nothing": (
            "NOTHING IN data/residents/, data/structures/ OR data/assets/ WAS EDITED. Every "
            "practitioner counted below was already in this repository before this record "
            "existed; the spend is the JOIN and not a creation. No confidence is raised, no "
            "two names are merged, and where the count is still short nobody is invented to "
            "close it — the ceiling on a residue is anonymous stock, under the owner's "
            "2026-09-02 ruling, and this record places none of that either."
        ),
        "unit_note": (
            "THE CENSUS COUNTS IN TWO DIFFERENT UNITS AND THE REGISTER COUNTS IN A THIRD. "
            "'Twenty-two lawyers' and 'fourteen physicians' count men; 'four druggists' and "
            "'two breweries' sit in a run of establishments and are read as premises; the "
            "register counts NOTICES, and one man may hold four of them. Each class below "
            "states the unit it is compared in and why."
        ),
        "classes": classes,
        "institutions": rulings["institutions"],
        "documented_absences": rulings["documented_absences"],
        "refusals": refusals,
        "open_questions": rulings["open_questions"],
        "totals": totals,
    }


def _occupation_map(rulings: dict) -> dict:
    out = {}
    for row in rulings["occupation_classes"]:
        if row["occupation"] in out:
            raise Fault(f"two occupation rulings for {row['occupation']!r}")
        if not str(row.get("basis") or "").strip():
            raise Fault(f"an occupation ruling with no basis: {row['occupation']}")
        out[row["occupation"]] = row
    return out


# ---------------------------------------------------------------------------
# the layers


def load_residents() -> dict:
    out = {}
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        for person in card.get("persons", []):
            occ = (person.get("occupation") or {}).get("value") or "none_recorded"
            out[person["id"]] = {
                "name": person.get("name"), "occupation": occ, "household": card["id"],
            }
    return out


def load_structures() -> set:
    return {json.loads(p.read_text(encoding="utf-8")).get("id")
            for p in STRUCTURES.glob("*.json")}


def load() -> tuple:
    return (
        json.loads(REGISTER.read_text(encoding="utf-8")),
        json.loads(CROSSWALK.read_text(encoding="utf-8")),
        json.loads(RULINGS.read_text(encoding="utf-8")),
        load_residents(),
        load_structures(),
    )


def render(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def report(doc: dict) -> str:
    out = ["", "class                    unit           census   held   not reached", "-" * 66]
    for c in doc["classes"]:
        out.append(f"{c['class']:<25}{c['unit']:<15}{c['census_count']:>6}"
                   f"{c['held_in_the_counted_unit']:>7}{c['not_reached']:>14}")
    out.append("-" * 66)
    t = doc["totals"]
    out.append(f"{'TOTAL':<40}{t['census_counted_across_them']:>6}"
               f"{t['held_after_the_spend']:>7}{t['not_reached']:>14}")
    out.append(f"\n{t['people_spent_from_resident_cards']} men spent out of the residents "
               f"layer, on {t['class_rows_spent_from_resident_cards']} of the census's lines, "
               f"none of whom had a business record at all.")
    out.append(f"{t['institutions_recorded']} institutions recorded and neither given a "
               f"building; {t['documented_absences']} documented absences; "
               f"{t['refusals']} refusals written out.")
    out.append(f"{t['not_reached']} of {t['census_counted_across_them']} the corpus cannot "
               f"name. That residue is a measured gap.")
    return "\n".join(out)


def cmd_build() -> int:
    doc = build(*load())
    SPEND.write_text(render(doc), encoding="utf-8")
    print(f"wrote {SPEND.relative_to(ROOT)}")
    print(report(doc))
    return 0


def cmd_check() -> int:
    if not SPEND.exists():
        print(f"FAIL: {SPEND.relative_to(ROOT)} does not exist — run --build", file=sys.stderr)
        return 1
    try:
        fresh = render(build(*load()))
    except Fault as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if fresh != SPEND.read_text(encoding="utf-8"):
        print(f"FAIL: {SPEND.relative_to(ROOT)} no longer re-derives from the register, the "
              "residents layer and the rulings. Run tools/trade_census_spend_1835.py --build "
              "and read the diff — a moved count means a card changed trade or a practitioner "
              "changed layer.", file=sys.stderr)
        return 1
    t = json.loads(SPEND.read_text(encoding="utf-8"))["totals"]
    print(f"the trade-census spend re-derives: {t['practitioners_ruled']} practitioners on "
          f"{t['classes_spent']} classes, {t['not_reached']} of "
          f"{t['census_counted_across_them']} still not reached")
    return 0


# ---------------------------------------------------------------------------
# the self-test: every guard above, fired


def _fixture() -> tuple:
    register = {"businesses": [{"id": "b1"}, {"id": "b2"}]}
    crosswalk = {"census_window": "1835-09-01/1835-12-31", "classes": [
        {"class": "physician", "business_ids": ["b1", "b2"]},
    ]}
    rulings = {
        "source_id": "s", "claim_id": "c",
        "classes_ruled": [{"class": "physician", "census_count": 4,
                           "census_line": "four physicians", "unit": "person",
                           "unit_basis": "x", "residual_rule": "y"}],
        "occupation_classes": [
            {"occupation": "physician", "class": "physician", "counts": True, "basis": "x"},
            {"occupation": "dentist", "class": "physician", "counts": False, "basis": "no line"},
        ],
        "practitioners": [
            {"key": "p1", "name": "A", "classes": ["physician"], "person_id": None,
             "business_ids": ["b1"], "establishment": "A's", "basis": "x"},
            {"key": "p2", "name": "B", "classes": ["physician"], "person_id": "r1",
             "business_ids": [], "establishment": "B's", "basis": "x"},
        ],
        "register_records_not_assigned": [
            {"business_id": "b2", "class": "physician", "basis": "names nobody"},
        ],
        "institutions": [{"id": "i1", "has_building": False, "links": [
            {"kind": "person", "id": "r1"}, {"kind": "structure", "id": "st1"}]}],
        "documented_absences": [
            {"id": "bank", "absence_kind": "notice_of_absence", "claims": ["x:c001"]},
            {"id": "lottery_office", "absence_kind": "no_corpus_record", "claims": []},
        ],
        "open_questions": [],
    }
    residents = {
        "r1": {"name": "B", "occupation": "physician", "household": "hh_b"},
        "r2": {"name": "C", "occupation": "dentist", "household": "hh_c"},
        "r3": {"name": "D", "occupation": "none_recorded", "household": "hh_d"},
    }
    return register, crosswalk, rulings, residents, {"st1"}


def _fires(args, fragment: str) -> None:
    try:
        build(*args)
    except Fault as exc:
        assert fragment in str(exc), f"wrong fault for {fragment!r}: {exc}"
        return
    raise AssertionError(f"no fault raised where one was due: {fragment}")


def cmd_self_test() -> int:
    import copy

    args = _fixture()
    doc = build(*args)
    cls = doc["classes"][0]
    assert cls["named_practitioners"] == 2 and cls["unnamed_records_held"] == 1, cls
    assert cls["held_in_the_counted_unit"] == 3 and cls["not_reached"] == 1, cls
    assert [r["person_id"] for r in cls["spent_from_resident_cards"]] == ["r1"], cls
    assert doc["refusals"][0]["person_id"] == "r2", doc["refusals"]

    # A CARD THE COUNT CANNOT SEE — the physician on a card and in no ruling.
    a = copy.deepcopy(args); a[3]["r9"] = {"name": "E", "occupation": "physician", "household": "h"}
    _fires(a, "no practitioner ruling holds him")

    # A REGISTER RECORD NOBODY CLAIMS.
    a = copy.deepcopy(args); a[2]["register_records_not_assigned"] = []
    _fires(a, "no practitioner ruling claims it")

    # A MAN IN NEITHER LAYER — minted from the census line.
    a = copy.deepcopy(args)
    a[2]["practitioners"].append({"key": "p9", "name": "Z", "classes": ["physician"],
                                  "person_id": None, "business_ids": [],
                                  "establishment": "Z's", "basis": "x"})
    _fires(a, "stands in neither layer")

    # a practitioner naming a person or a business nothing holds
    a = copy.deepcopy(args); a[2]["practitioners"][1]["person_id"] = "r99"
    _fires(a, "a person the residents layer does not hold")
    a = copy.deepcopy(args); a[2]["practitioners"][0]["business_ids"] = ["b99"]
    _fires(a, "a business the register does not hold")

    # rulings that say nothing
    a = copy.deepcopy(args); a[2]["practitioners"][0]["basis"] = " "
    _fires(a, "no basis")
    a = copy.deepcopy(args); a[2]["practitioners"][0]["classes"] = []
    _fires(a, "names no class")
    a = copy.deepcopy(args); a[2]["practitioners"][0]["classes"] = ["tavern"]
    _fires(a, "a class this file does not rule")
    a = copy.deepcopy(args); a[2]["practitioners"][1]["key"] = "p1"
    _fires(a, "two practitioner rulings under one key")
    a = copy.deepcopy(args)
    a[2]["occupation_classes"].append({"occupation": "physician", "class": "physician",
                                       "counts": True, "basis": "x"})
    _fires(a, "two occupation rulings")

    # A ROOF FOR THE LYCEUM — the thing this ticket exists to forbid.
    a = copy.deepcopy(args); a[2]["institutions"][0]["has_building"] = True
    _fires(a, "recorded with a building")

    # an institution linking something the town does not hold
    a = copy.deepcopy(args); a[2]["institutions"][0]["links"][0]["id"] = "r99"
    _fires(a, "links a person the residents layer does not hold")
    a = copy.deepcopy(args); a[2]["institutions"][0]["links"][1]["id"] = "st99"
    _fires(a, "links a structure the town does not hold")

    # an absence that cites the wrong thing, in either direction
    a = copy.deepcopy(args); a[2]["documented_absences"][0]["claims"] = []
    _fires(a, "cites no notice")
    a = copy.deepcopy(args); a[2]["documented_absences"][1]["claims"] = ["x"]
    _fires(a, "then cites the corpus")

    # a class the T-1006 crosswalk never measured
    a = copy.deepcopy(args); a[2]["classes_ruled"][0]["class"] = "cooper"
    _fires(a, "a class the T-1006 crosswalk does not hold")

    # THE ESTABLISHMENT UNIT: two men in one shop are one shop.
    a = copy.deepcopy(args)
    a[2]["classes_ruled"][0]["unit"] = "establishment"
    a[2]["practitioners"][1]["establishment"] = "A's"
    cls = build(*a)["classes"][0]
    assert cls["named_practitioners"] == 2 and cls["named_establishments"] == 1, cls
    assert cls["held_in_the_counted_unit"] == 2, cls

    print("trade_census_spend_1835 self-tests pass (17 guards)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    try:
        if args.build:
            return cmd_build()
        if args.check:
            return cmd_check()
        if args.self_test:
            return cmd_self_test()
    except Fault as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(report(build(*load())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
