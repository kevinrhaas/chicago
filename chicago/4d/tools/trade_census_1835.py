#!/usr/bin/env python3
"""THE DECEMBER 1835 TRADE CENSUS, SET AGAINST THE TOWN'S OWN BUSINESS REGISTER.

Moses and Kirkland print, at page 95 of volume 1, the State count taken between
1 September and December 1835: forty-four stores, two book stores, four druggists,
two silversmiths and jewellers, two tin and copper manufactories, two printing
offices, two breweries, one steam saw-mill, one iron foundry, four storage and
forwarding houses, eight taverns, one lottery office, one bank, five churches,
seven schools, twenty-two lawyers, fourteen physicians, and a lyceum and reading
room.  That paragraph is `bk_mose1_006`, read by T-0581, and until this tool it had
never been spent: **the project held no denominator for its business layer.**

It could not be compared, either, because the register's `trade` is free prose off
the printed notice — 152 distinct strings for 206 businesses.  The class comes from
`data/research/newspapers/trade_class_rulings.json`, one ruling per printed string,
and this tool joins the two and writes the comparison.

    tools/trade_census_1835.py --build       write the crosswalk
    tools/trade_census_1835.py --check       re-derive it and refuse any drift
    tools/trade_census_1835.py --self-test   the guards, fired on fixtures

THE DATE IS THE WHOLE OF THE CAUTION, and it is written into the record rather than
into a reader's memory.  The count is two to five months AFTER the scene date of
1 July 1835, in the fastest-growing months the town had.  A shortfall against it is
never evidence that a business stood in July, and this file's every figure says so.

WHAT THIS TOOL MAY NOT DO.  It classifies and it counts.  It creates nothing, it
places nothing, and it upgrades no confidence: the spending of the gap it measures
is T-1007's, on T-0404's liberty, and a run that finds a hole here files a ticket
rather than a building.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAZETTEER = ROOT / "data" / "research" / "newspapers" / "gazetteer.json"
RULINGS = ROOT / "data" / "research" / "newspapers" / "trade_class_rulings.json"
CROSSWALK = ROOT / "data" / "research" / "books" / "trade_census_1835_crosswalk.json"

CLAIM = "bk_mose1_006"
SOURCE = "moses_kirkland_history_of_chicago_v1"
SCENE_DATE = "1835-07-01"
CENSUS_WINDOW = "1835-09-01/1835-12-31"
DATE_CAUTION = (
    "THE COUNT IS NOT OF THE SCENE. It was taken between 1 September and December 1835; "
    "the scene is 1 July 1835, two to five months earlier and in the fastest-growing "
    "months the town had. A class where the town holds fewer than the census counted is "
    "NOT thereby a hole in the July town — some of those forty-four stores opened in "
    "September. Every figure below is to be read with that gap in front of it."
)


class Fault(Exception):
    """A defect in the rulings or the register, phrased for the person who must fix it."""


# ---------------------------------------------------------------------------
# the join


def classify(gazetteer: dict, rulings: dict) -> list:
    """One row per business in the register: its printed trade, and its class.

    Every fault this raises is a SILENT MISCOUNT if it does not. A business whose
    printed trade no ruling covers would simply not appear in any class and the
    denominator would be set against a town missing a house — which is the exact
    failure T-0988 exists to end ("no business is silently left out of the count").
    """
    known = {row["id"] for row in rulings["vocabulary"]}
    by_trade = {}
    for row in rulings["trade_rulings"]:
        if row["trade"] in by_trade:
            raise Fault(f"two rulings for one printed trade: {row['trade']!r}")
        by_trade[row["trade"]] = row
    overrides = {row["business_id"]: row for row in rulings["business_overrides"]}

    for row in rulings["trade_rulings"] + rulings["business_overrides"]:
        for cls in row["classes"]:
            if cls not in known:
                raise Fault(f"ruling names a class the vocabulary does not hold: {cls}")
        if not row["classes"]:
            raise Fault(f"a ruling that names no class at all: {row}")
        if not str(row.get("basis") or "").strip():
            raise Fault(f"a ruling with no basis: {row}")

    rows = []
    seen_trades = set()
    for biz in gazetteer["businesses"]:
        trade = biz.get("trade")
        override = overrides.get(biz["id"])
        if trade:
            ruling = by_trade.get(trade)
            if ruling is None:
                raise Fault(
                    f"{biz['id']}: no ruling covers the printed trade {trade!r}. "
                    "Rule it in trade_class_rulings.json — a business with no class is a "
                    "business the census cannot be set against.")
            seen_trades.add(trade)
            if override:
                raise Fault(
                    f"{biz['id']}: an override for a business whose notice DOES print a "
                    "trade. Overrides are for notices that print none; rule the string.")
            classes, basis, ruled_by = ruling["classes"], ruling["basis"], "trade"
            scope = ruling.get("scope") or "in_town"
        else:
            if override is None:
                raise Fault(
                    f"{biz['id']}: the notice prints no trade and no override rules it. "
                    "Rule it by id off the goods, or say it is not_stated.")
            classes, basis, ruled_by = override["classes"], override["basis"], "business"
            scope = override.get("scope") or "in_town"
        rows.append({
            "business_id": biz["id"],
            "name": biz["name"],
            "trade": trade,
            "classes": sorted(classes),
            "scope": scope,
            "ruled_by": ruled_by,
            "basis": basis,
            "built_at_scene_date": bool(biz.get("built_at_scene_date")),
        })

    orphans = sorted(set(by_trade) - seen_trades)
    if orphans:
        raise Fault(
            "rulings for printed trades the register no longer carries — a ruling that has "
            "outlived its reading is a judgement nobody can check:\n  "
            + "\n  ".join(repr(o) for o in orphans))
    for business_id in sorted(overrides):
        if not any(r["business_id"] == business_id for r in rows):
            raise Fault(f"an override naming no business in the register: {business_id}")

    rows.sort(key=lambda r: r["business_id"])
    return rows


def compare(rows: list, rulings: dict) -> list:
    """One ruling per enumerated class: the census's count, and the town's.

    Anchored on `claim_id` so measure_research_spend.py can see the paragraph spent —
    once, deduped, which is right: this is ONE claim ruled onto the whole layer.
    """
    out = []
    for entry in rulings["vocabulary"]:
        cls = entry["id"]
        members = [r for r in rows if cls in r["classes"]]
        in_town = [r for r in members if r["scope"] == "in_town"]
        at_scene = [r for r in in_town if r["built_at_scene_date"]]
        census = entry["census_count"]
        row = {
            "claim_id": CLAIM,
            "class": cls,
            "census_line": entry["census_line"],
            "census_count": census,
            "compared": entry["compared"],
            "town_records_in_town": len(in_town),
            "town_records_at_scene_date": len(at_scene),
            "town_records_outside_town": len(members) - len(in_town),
            "business_ids": [r["business_id"] for r in in_town],
        }
        if census is None or not entry["compared"]:
            row["outcome"] = "not_compared"
            row["delta"] = None
        else:
            row["delta"] = len(at_scene) - census
            if len(at_scene) == census:
                row["outcome"] = "town_matches_census"
            elif len(at_scene) < census:
                row["outcome"] = "town_holds_fewer_than_the_census_counted"
            else:
                row["outcome"] = "town_holds_more_than_the_census_counted"
        row["note"] = entry["note"] or (
            "the town holds nothing for this line" if not members else None)
        out.append(row)
    return out


def build(gazetteer: dict, rulings: dict) -> dict:
    rows = classify(gazetteer, rulings)
    classes = compare(rows, rulings)
    compared = [c for c in classes if c["outcome"] not in ("not_compared",)]
    empty = [c["class"] for c in compared if c["town_records_in_town"] == 0]
    return {
        "schema": 1,
        "domain": "books",
        "source_id": SOURCE,
        "claim_id": CLAIM,
        "generated_by": "tools/trade_census_1835.py --build",
        "ticket": "T-1006",
        "not_a_reading": (
            "an adjudication of a claim this domain has already read, set against the "
            "business register — no page of any source is read here"),
        "_doc": __doc__.strip(),
        "scene_date": SCENE_DATE,
        "census_window": CENSUS_WINDOW,
        "date_caution": DATE_CAUTION,
        "does_not_follow": (
            "NOTHING IN data/residents/, data/structures/ OR data/assets/ WAS EDITED BY THIS "
            "MEASUREMENT. It creates no business, places no roof and names no person. Where "
            "the town holds fewer than the census counted, that gap is T-1007's to spend on "
            "T-0404's liberty and only where a source NAMES the business; where it holds "
            "none at all, the class is a documented zero and not an invitation to invent."),
        "note": (
            "The class of each business is ruled in "
            "data/research/newspapers/trade_class_rulings.json, once per printed trade "
            "string, and the boundaries that decide the hard cases are stated there as "
            "B1-B6. Disagree with a count by disagreeing with a boundary."),
        "classes": classes,
        "totals": {
            "businesses_in_register": len(rows),
            "in_town": sum(1 for r in rows if r["scope"] == "in_town"),
            "outside_town": sum(1 for r in rows if r["scope"] != "in_town"),
            "at_scene_date": sum(1 for r in rows
                                 if r["scope"] == "in_town" and r["built_at_scene_date"]),
            "carrying_no_enumerated_class": sum(
                1 for r in rows if set(r["classes"]) <= {"other", "not_stated"}),
            "not_stated": sum(1 for r in rows if "not_stated" in r["classes"]),
            "census_enumerated_total": sum(
                c["census_count"] for c in classes
                if c["census_count"] is not None and c["compared"]),
            "town_enumerated_total_at_scene_date": sum(
                c["town_records_at_scene_date"] for c in classes if c["compared"]
                and c["census_count"] is not None),
        },
        "classes_the_town_holds_nothing_for": sorted(empty),
        "register_cautions": rulings["register_cautions"],
        "classification": rows,
    }


# ---------------------------------------------------------------------------
# the commands


def render(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def load() -> tuple:
    return json.loads(GAZETTEER.read_text(encoding="utf-8")), \
        json.loads(RULINGS.read_text(encoding="utf-8"))


def cmd_build() -> int:
    doc = build(*load())
    CROSSWALK.write_text(render(doc), encoding="utf-8")
    print(f"wrote {CROSSWALK.relative_to(ROOT)}")
    print(report(doc))
    return 0


def report(doc: dict) -> str:
    out = ["", "class                          census   town(1 Jul)   delta", "-" * 60]
    for c in doc["classes"]:
        if not c["compared"] or c["census_count"] is None:
            continue
        out.append(f"{c['class']:<30}{c['census_count']:>6}{c['town_records_at_scene_date']:>13}"
                   f"{c['delta']:>+8}")
    out.append("-" * 60)
    t = doc["totals"]
    out.append(f"{'TOTAL (enumerated classes)':<30}{t['census_enumerated_total']:>6}"
               f"{t['town_enumerated_total_at_scene_date']:>13}")
    out.append(f"\n{t['businesses_in_register']} businesses ruled: {t['in_town']} in town, "
               f"{t['outside_town']} printed as standing outside it, "
               f"{t['not_stated']} whose notice prints no trade at all.")
    out.append(f"{t['carrying_no_enumerated_class']} carry no enumerated class — the trades the "
               "December count does not count.")
    if doc["classes_the_town_holds_nothing_for"]:
        out.append("the town holds NOTHING for: "
                   + ", ".join(doc["classes_the_town_holds_nothing_for"]))
    out.append("\n" + doc["date_caution"])
    return "\n".join(out)


def cmd_check() -> int:
    if not CROSSWALK.exists():
        print(f"FAIL: {CROSSWALK.relative_to(ROOT)} does not exist — run --build", file=sys.stderr)
        return 1
    try:
        fresh = render(build(*load()))
    except Fault as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if fresh != CROSSWALK.read_text(encoding="utf-8"):
        print(f"FAIL: {CROSSWALK.relative_to(ROOT)} no longer re-derives from the register and "
              "the rulings. Run tools/trade_census_1835.py --build and read the diff — a "
              "changed count means a business changed class or a reading changed.", file=sys.stderr)
        return 1
    print(f"the December 1835 trade count re-derives: "
          f"{json.loads(fresh)['totals']['businesses_in_register']} businesses classified, "
          f"none left out")
    return 0


# ---------------------------------------------------------------------------
# the self-test: every guard above, fired


def _fixture() -> tuple:
    gaz = {"businesses": [
        {"id": "b1", "name": "A", "trade": "tavern", "built_at_scene_date": True},
        {"id": "b2", "name": "B", "trade": None, "built_at_scene_date": True},
    ]}
    rules = {
        "vocabulary": [
            {"id": "tavern", "census_line": "eight taverns", "census_count": 8,
             "compared": True, "note": None},
            {"id": "other", "census_line": "(not an enumerated class)", "census_count": None,
             "compared": True, "note": None},
        ],
        "trade_rulings": [{"trade": "tavern", "classes": ["tavern"], "basis": "printed"}],
        "business_overrides": [{"business_id": "b2", "classes": ["other"], "basis": "goods"}],
        "register_cautions": [],
    }
    return gaz, rules


def _fires(gaz, rules, fragment: str) -> None:
    try:
        classify(gaz, rules)
    except Fault as exc:
        assert fragment in str(exc), f"wrong fault for {fragment!r}: {exc}"
        return
    raise AssertionError(f"no fault raised where one was due: {fragment}")


def cmd_self_test() -> int:
    import copy

    gaz, rules = _fixture()
    rows = classify(gaz, rules)
    assert [r["business_id"] for r in rows] == ["b1", "b2"], rows
    assert rows[0]["classes"] == ["tavern"] and rows[1]["ruled_by"] == "business"

    # a printed trade nothing rules — the silent miscount T-0988 exists to end
    g = copy.deepcopy(gaz)
    g["businesses"].append({"id": "b3", "name": "C", "trade": "bakery",
                            "built_at_scene_date": True})
    _fires(g, rules, "no ruling covers the printed trade")

    # a notice printing no trade and no override
    g = copy.deepcopy(gaz)
    g["businesses"].append({"id": "b4", "name": "D", "trade": None,
                            "built_at_scene_date": True})
    _fires(g, rules, "no override rules it")

    # a ruling that has outlived its reading
    r = copy.deepcopy(rules)
    r["trade_rulings"].append({"trade": "livery", "classes": ["other"], "basis": "x"})
    _fires(gaz, r, "outlived its reading")

    # a class the vocabulary does not hold
    r = copy.deepcopy(rules)
    r["trade_rulings"][0]["classes"] = ["innkeeper"]
    _fires(gaz, r, "class the vocabulary does not hold")

    # a ruling with no basis, and one with no class
    r = copy.deepcopy(rules)
    r["trade_rulings"][0]["basis"] = "  "
    _fires(gaz, r, "no basis")
    r = copy.deepcopy(rules)
    r["trade_rulings"][0]["classes"] = []
    _fires(gaz, r, "names no class")

    # an override for a business whose notice DOES print a trade
    r = copy.deepcopy(rules)
    r["business_overrides"].append({"business_id": "b1", "classes": ["other"], "basis": "x"})
    _fires(gaz, r, "an override for a business whose notice DOES print")

    # two rulings for one printed string
    r = copy.deepcopy(rules)
    r["trade_rulings"].append({"trade": "tavern", "classes": ["other"], "basis": "x"})
    _fires(gaz, r, "two rulings for one printed trade")

    # an override naming nothing in the register
    r = copy.deepcopy(rules)
    r["business_overrides"].append({"business_id": "b9", "classes": ["other"], "basis": "x"})
    _fires(gaz, r, "an override naming no business")

    # THE DATE. A record dated out of the scene is counted apart from the scene town.
    g = copy.deepcopy(gaz)
    g["businesses"][0]["built_at_scene_date"] = False
    doc = build(g, rules)
    tav = next(c for c in doc["classes"] if c["class"] == "tavern")
    assert tav["town_records_in_town"] == 1 and tav["town_records_at_scene_date"] == 0, tav
    assert tav["delta"] == -8, tav
    assert DATE_CAUTION in doc["date_caution"]

    # scope: a house printed as standing outside the town is not counted in it
    r = copy.deepcopy(rules)
    r["trade_rulings"][0]["scope"] = "outside_town"
    doc = build(gaz, r)
    tav = next(c for c in doc["classes"] if c["class"] == "tavern")
    assert tav["town_records_in_town"] == 0 and tav["town_records_outside_town"] == 1, tav

    print("trade_census_1835 self-tests pass (11 guards)")
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
    print(render(build(*load())) if False else report(build(*load())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
