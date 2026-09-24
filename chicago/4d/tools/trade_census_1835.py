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

THE AUTHORED LAYER IS COUNTED TOO, SINCE T-1404.  The register is no longer the whole
of the town's business layer: `data/businesses/authored/` holds the houses a human or a
tool wrote down where the paper printed none — the inferred shops T-1404 raises for
tradesmen whose dated role reaches the scene date, and the reconstructed firms T-1184
onward draw against this very crosswalk.  Counting the register alone made those houses
invisible to the comparison AND to the order book cut from it, so the book would have
ordered eleven physicians reconstructed over a layer that names eight.  An authored
record carries its census class on itself, in `type`, ruled by whoever wrote it; it needs
no trade ruling and gets none, and `ruled_by` says `authored_record` so the two
populations can never be confused in the classification table.

A RECONSTRUCTED HOUSE IS NOT COUNTED, and the reason is the order book.  Its
`businesses/*` buckets are cut as census count MINUS what the town knows, and the
reconstructions those buckets order are carried in `filled`, a separate counter.  Count a
reconstructed firm as known and the same house is subtracted twice: the two druggists
T-1184 drew against a shortfall of two would close the shortfall AND stand in `filled`,
and the book's own overfill guard fires.  So `load()` passes the authored records whose
`provenance` is not `reconstructed` — the attested and inferred houses a source stands
behind — and the drawn ones stay where they belong, in the counter of the bucket that
ordered them.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAZETTEER = ROOT / "data" / "research" / "newspapers" / "gazetteer.json"
REGISTER = ROOT / "data" / "research" / "newspapers" / "register_1835.json"
RULINGS = ROOT / "data" / "research" / "newspapers" / "trade_class_rulings.json"
CROSSWALK = ROOT / "data" / "research" / "books" / "trade_census_1835_crosswalk.json"
AUTHORED = ROOT / "data" / "businesses" / "authored"

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


def classify(gazetteer: dict, rulings: dict, register: dict,
             authored: list | None = None) -> tuple:
    """One row per business in the register: its printed trade, and its class.

    Every fault this raises is a SILENT MISCOUNT if it does not. A business whose
    printed trade no ruling covers would simply not appear in any class and the
    denominator would be set against a town missing a house — which is the exact
    failure T-0988 exists to end ("no business is silently left out of the count").
    """
    known = {row["id"] for row in rulings["vocabulary"]}
    not_counted: list = []
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

    # The register's dated reading of every gazetteer record, indexed once. The register
    # is compiled FROM the gazetteer (compile_register.py), so a gazetteer id it does not
    # carry means the two have drifted apart and no count taken across them can be trusted.
    presence = {}
    for rec in register["businesses"]:
        exclusion = rec.get("exclusion")
        presence[rec["id"]] = {
            "present": bool(rec.get("present_at_scene_date")),
            "exclusion": exclusion,
            "opened_after": exclusion == "opening_announced_after_scene_date",
        }
    missing = sorted({b["id"] for b in gazetteer["businesses"]} - set(presence))
    if missing:
        raise Fault(
            "the register does not carry every business the gazetteer does, so the scene-date "
            "reading cannot be taken for: " + ", ".join(missing)
            + ". Re-run tools/compile_register.py --build.")

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
            # THE SCENE-DATE READING IS THE REGISTER'S, NOT THE GAZETTEER'S (T-1428).
            # `built_at_scene_date` is compile_gazetteer.py's survival flag and it means
            # ONE thing: "a documented business stands in the 1835 town unless a claim
            # contradicts it", false only on a dissolution, removal or replacement
            # notice. It says nothing about a house whose OPENING is announced after
            # 1 July, and it goes false on a dissolution announced AFTER 1 July for a
            # firm that was plainly standing on the day. The register carries the dated
            # judgement in `present_at_scene_date`, with the reason in `exclusion`, and
            # that is the field a count of the July town must read. The authored branch
            # below has always read it; this branch read the other one.
            "present_at_scene_date": presence[biz["id"]]["present"],
            "scene_date_exclusion": presence[biz["id"]]["exclusion"],
            "opened_after_scene_date": presence[biz["id"]]["opened_after"],
        })

    for rec in sorted(authored or [], key=lambda r: r["id"]):
        classes = sorted(rec.get("type") or [])
        if not classes:
            raise Fault(f"{rec['id']}: an authored record naming no class at all. Its `type` IS "
                        "its ruling; a house with none is a house outside the count.")
        # A CLASS THE 1835 TRADE CENSUS NEVER COUNTED IS OUTSIDE THE COMPARISON, NOT A
        # FAULT (owner, 2026-09-20). `known` is the vocabulary of CENSUS CLASSES, and the
        # whole of this table is the register read against that census. T-1188's civic
        # establishments — the post office, the land office, the county offices — are
        # houses the town certainly held and that the trade census never enumerated: they
        # are not a printed trade and were never in its denominator. Counting them would
        # put a house on one side of a comparison the other side cannot hold, and faulting
        # on them stops the build over a record that is doing nothing wrong.
        #
        # So they are set OUTSIDE the count and NAMED there. This file's own rule is that
        # "no business is silently left out of the count" (T-0988), and the answer to that
        # is a row saying which houses are out and why — not a fault, and not a silence.
        # A record MIXING a census class with a non-census one is still a fault: that is a
        # record that cannot decide which side of the comparison it is on.
        outside = [c for c in classes if c not in known]
        if outside and len(outside) != len(classes):
            raise Fault(f"{rec['id']}: an authored record mixes census classes with classes "
                        f"the census never counted ({', '.join(outside)}); a house stands on "
                        "one side of this comparison or the other, not both")
        if outside:
            not_counted.append({
                "business_id": rec["id"],
                "name": rec.get("name"),
                "classes": classes,
                "why": ("The 1835 trade census enumerates printed TRADES. This house carries "
                        "a class it never counted, so it stands outside this comparison "
                        "rather than in it — named here so it is not silently left out."),
            })
            continue
        rows.append({
            "business_id": rec["id"],
            "name": rec.get("name"),
            "trade": rec.get("trade"),
            "classes": classes,
            "scope": "in_town",
            "ruled_by": "authored_record",
            "basis": (f"AUTHORED, NOT PRINTED. `{rec['id']}` carries its own census class in "
                      f"`type` and its own grade in `provenance: {rec.get('provenance')}`; the "
                      "ruling was made by whoever wrote the record and is read off it here."),
            "present_at_scene_date": bool(rec.get("present_at_scene_date")),
            "scene_date_exclusion": None,
            "opened_after_scene_date": False,
        })

    orphans = sorted(set(by_trade) - seen_trades)
    if orphans:
        raise Fault(
            "rulings for printed trades the register no longer carries — a ruling that has "
            "outlived its reading is a judgement nobody can check:\n  "
            + "\n  ".join(repr(o) for o in orphans))
    register_ids = {b["id"] for b in gazetteer["businesses"]}
    for business_id in sorted(overrides):
        if business_id not in register_ids:
            raise Fault(f"an override naming no business in the register: {business_id}")

    # TWO NOTICES RULED TO BE ONE HOUSE (T-1422). The fold moves the COUNT and nothing
    # else: both records stand, both keep their claims, and the class row names the pair.
    # Every guard here exists because the alternative to it is a count nobody can audit.
    by_id = {row["business_id"]: row for row in rows}
    folded_into = {}
    for fold in one_house_rulings(rulings):
        folded, into = fold["folded"], fold["into"]
        if folded == into:
            raise Fault(f"a one-house ruling folding {folded} into itself")
        for side in (folded, into):
            if side not in register_ids:
                raise Fault(f"a one-house ruling naming no business in the register: {side}")
            if side not in by_id:
                raise Fault(f"a one-house ruling naming {side}, which this table does not rule")
        if not str(fold.get("basis") or "").strip():
            raise Fault(f"a one-house ruling with no basis: {folded} into {into}")
        if folded in folded_into:
            raise Fault(f"{folded} is folded twice; a house is folded once")
        # A HOUSE FOLDED INTO A HOUSE THAT IS ITSELF FOLDED would leave the survivor out
        # of the count altogether, which is the opposite of what a fold is for.
        if into in folded_into or any(f == into for f in folded_into):
            raise Fault(f"{folded} is folded into {into}, which is itself folded away")
        shared = set(by_id[folded]["classes"]) & set(by_id[into]["classes"])
        if not shared:
            raise Fault(
                f"a one-house ruling joining {folded} and {into}, which share no census "
                "class. Two notices of different classes are two houses, and a ruling that "
                "says otherwise is reclassifying one of them without saying so.")
        for cls in fold["classes"]:
            if cls not in shared:
                raise Fault(
                    f"a one-house ruling folding {folded} into {into} in class {cls!r}, "
                    "which is not a class both of them carry")
        folded_into[folded] = fold
    for row in rows:
        fold = folded_into.get(row["business_id"])
        row["folded_into"] = fold["into"] if fold else None
        row["folded_in_classes"] = list(fold["classes"]) if fold else []

    rows.sort(key=lambda r: r["business_id"])
    not_counted.sort(key=lambda r: r["business_id"])
    return rows, not_counted


def one_house_rulings(rulings: dict) -> list:
    """The folds, or none. Absent means nobody has ruled one, which is the normal state."""
    return list((rulings.get("one_house_rulings") or {}).get("rulings") or [])


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
        # A HOUSE FOLDED INTO ANOTHER IS STILL A RECORD AND IS NO LONGER A COUNT. It is
        # dropped from both totals and named in `folded_business_ids`, so the reader sees
        # the pair rather than a number that quietly got smaller (T-1422).
        folded = [r for r in in_town if cls in r["folded_in_classes"]]
        standing = [r for r in in_town if cls not in r["folded_in_classes"]]
        at_scene = [r for r in standing if r["present_at_scene_date"]]
        # A SHORTFALL THE EVIDENCE EXPLAINS IS NOT A HOLE IN THE JULY TOWN (T-1428). The
        # census was taken between September and December; a house the register excludes
        # because its OPENING was announced after 1 July is a house that house-by-house
        # accounts for one of the December figures without standing in the July one. It is
        # named here — count and ids — so that whoever subtracts the two knows how much of
        # the difference is already spoken for, and does not commission an invention to
        # fill a gap two dated notices have explained.
        later = [r for r in standing if r["opened_after_scene_date"]]
        census = entry["census_count"]
        row = {
            "claim_id": CLAIM,
            "class": cls,
            "census_line": entry["census_line"],
            "census_count": census,
            "compared": entry["compared"],
            "town_records_in_town": len(standing),
            "town_records_at_scene_date": len(at_scene),
            "town_records_outside_town": len(members) - len(in_town),
            "records_opening_after_scene_date": len(later),
            "business_ids_opening_after_scene_date": [r["business_id"] for r in later],
            "business_ids": [r["business_id"] for r in standing],
            "folded_business_ids": [{"business_id": r["business_id"],
                                     "into": r["folded_into"]} for r in folded],
        }
        if census is None or not entry["compared"]:
            row["outcome"] = "not_compared"
            row["delta"] = None
            row["shortfall_explained_by_later_openings"] = None
        else:
            row["delta"] = len(at_scene) - census
            row["shortfall_explained_by_later_openings"] = min(
                len(later), max(0, census - len(at_scene)))
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


def build(gazetteer: dict, rulings: dict, register: dict,
          authored: list | None = None) -> dict:
    rows, not_counted = classify(gazetteer, rulings, register, authored)
    register = [r for r in rows if r["ruled_by"] != "authored_record"]
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
        "outside_the_census_classes": {
            "_doc": ("Authored houses whose census class the 1835 trade census never "
                     "enumerated — T-1188's civic establishments among them. They stand "
                     "OUTSIDE this comparison rather than in it: the census counts printed "
                     "TRADES, and a post office is not one. Named here because this table's "
                     "rule is that no business is silently left out of the count (T-0988); "
                     "being outside a comparison and being invisible are different things."),
            "count": len(not_counted),
            "records": not_counted,
        },
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
            "businesses_in_register": len(register),
            "authored_records_counted": len(rows) - len(register),
            "businesses_counted": len(rows),
            "in_town": sum(1 for r in rows if r["scope"] == "in_town"),
            "outside_town": sum(1 for r in rows if r["scope"] != "in_town"),
            "at_scene_date": sum(1 for r in rows
                                 if r["scope"] == "in_town" and r["present_at_scene_date"]
                                 and not r["folded_into"]),
            "folded_into_another_house": sum(1 for r in rows if r["folded_into"]),
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
    authored = [doc for doc in (json.loads(p.read_text(encoding="utf-8"))
                                for p in sorted(AUTHORED.glob("*.json")))
                if doc.get("provenance") != "reconstructed"]
    return (json.loads(GAZETTEER.read_text(encoding="utf-8")),
            json.loads(RULINGS.read_text(encoding="utf-8")),
            json.loads(REGISTER.read_text(encoding="utf-8")),
            authored)


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
    out.append(f"\n{t['businesses_counted']} businesses ruled "
               f"({t['businesses_in_register']} printed in the register, "
               f"{t['authored_records_counted']} authored): {t['in_town']} in town, "
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
          f"{json.loads(fresh)['totals']['businesses_counted']} businesses classified, "
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


def _register_for(gaz: dict, excluded: dict | None = None) -> dict:
    """The register fixture for a gazetteer fixture: every house present at the scene date
    unless the caller excludes it, which is what compile_register.py writes. Built rather
    than hand-kept so a new fixture record cannot silently fall out of the join."""
    out = excluded or {}
    return {"businesses": [{"id": b["id"], "name": b.get("name"),
                            "present_at_scene_date": b["id"] not in out,
                            "exclusion": out.get(b["id"])}
                           for b in gaz["businesses"]]}


def _fires_authored(gaz, rules, authored, fragment: str) -> None:
    try:
        classify(gaz, rules, _register_for(gaz), authored)
    except Fault as exc:
        assert fragment in str(exc), f"wrong fault for {fragment!r}: {exc}"
        return
    raise AssertionError(f"no fault raised where one was due: {fragment}")


def _fires(gaz, rules, fragment: str) -> None:
    try:
        classify(gaz, rules, _register_for(gaz))
    except Fault as exc:
        assert fragment in str(exc), f"wrong fault for {fragment!r}: {exc}"
        return
    raise AssertionError(f"no fault raised where one was due: {fragment}")


def cmd_self_test() -> int:
    import copy

    gaz, rules = _fixture()
    rows, _ = classify(gaz, rules, _register_for(gaz))
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

    # THE DATE. A record dated out of the scene is counted apart from the scene town —
    # and the reading that decides it is the REGISTER's (T-1428), not the gazetteer's.
    reg = _register_for(gaz, {"b1": "contradicted_before_scene_date"})
    doc = build(gaz, rules, reg)
    tav = next(c for c in doc["classes"] if c["class"] == "tavern")
    assert tav["town_records_in_town"] == 1 and tav["town_records_at_scene_date"] == 0, tav
    assert tav["delta"] == -8, tav
    assert DATE_CAUTION in doc["date_caution"]

    # AND THE GAZETTEER'S SURVIVAL FLAG NO LONGER MOVES THE COUNT ON ITS OWN. It goes
    # false on a dissolution notice whatever that notice's date, so a firm wound up on
    # 22 July was dropped from a count of the town on 1 July. The register keeps it.
    g = copy.deepcopy(gaz)
    g["businesses"][0]["built_at_scene_date"] = False
    doc = build(g, rules, _register_for(g))
    tav = next(c for c in doc["classes"] if c["class"] == "tavern")
    assert tav["town_records_at_scene_date"] == 1, tav

    # A HOUSE THAT OPENED AFTER THE SCENE DATE is out of the July count and NAMED there,
    # and the shortfall it leaves against the autumn census is marked as explained.
    reg = _register_for(gaz, {"b1": "opening_announced_after_scene_date"})
    doc = build(gaz, rules, reg)
    tav = next(c for c in doc["classes"] if c["class"] == "tavern")
    assert tav["town_records_at_scene_date"] == 0, tav
    assert tav["records_opening_after_scene_date"] == 1, tav
    assert tav["business_ids_opening_after_scene_date"] == ["b1"], tav
    assert tav["shortfall_explained_by_later_openings"] == 1, tav
    row = next(r for r in doc["classification"] if r["business_id"] == "b1")
    assert row["opened_after_scene_date"] is True, row
    assert row["scene_date_exclusion"] == "opening_announced_after_scene_date", row

    # A REGISTER THAT HAS DRIFTED FROM THE GAZETTEER cannot be joined at all.
    short = _register_for(gaz)
    short["businesses"] = [b for b in short["businesses"] if b["id"] != "b1"]
    try:
        build(gaz, rules, short)
    except Fault as exc:
        assert "does not carry every business" in str(exc), exc
    else:
        raise AssertionError("no fault where the register is missing a gazetteer record")

    # scope: a house printed as standing outside the town is not counted in it
    r = copy.deepcopy(rules)
    r["trade_rulings"][0]["scope"] = "outside_town"
    doc = build(gaz, r, _register_for(gaz))
    tav = next(c for c in doc["classes"] if c["class"] == "tavern")
    assert tav["town_records_in_town"] == 0 and tav["town_records_outside_town"] == 1, tav

    # THE AUTHORED LAYER. A record carries its own class and is counted beside the register.
    doc = build(gaz, rules, _register_for(gaz), [{"id": "biz_x_tavern_keeper", "name": "X, tavern keeper",
                              "trade": "tavern keeper", "type": ["tavern"],
                              "provenance": "authored", "present_at_scene_date": True}])
    tav = next(c for c in doc["classes"] if c["class"] == "tavern")
    assert tav["town_records_at_scene_date"] == 2, tav
    assert doc["totals"]["businesses_in_register"] == 2, doc["totals"]
    assert doc["totals"]["authored_records_counted"] == 1, doc["totals"]
    row = next(r for r in doc["classification"] if r["business_id"] == "biz_x_tavern_keeper")
    assert row["ruled_by"] == "authored_record", row

    # an authored record naming no class at all is still a fault
    _fires_authored(gaz, rules, [{"id": "biz_y", "type": []}], "naming no class at all")

    # A CLASS THE CENSUS NEVER COUNTED IS OUTSIDE THE COMPARISON, NOT A FAULT (owner,
    # 2026-09-20). It used to raise; T-1188's civic houses are the case that showed it
    # should not. The guard is that it lands in `outside_the_census_classes` and NOT in
    # the classification — outside and invisible are different things.
    rows, outside = classify(gaz, rules, _register_for(gaz),
                             [{"id": "biz_y", "name": "Y", "type": ["civic"]}])
    assert [r["business_id"] for r in outside] == ["biz_y"], outside
    assert all(r["business_id"] != "biz_y" for r in rows), rows
    assert outside[0]["classes"] == ["civic"], outside

    # ...and a record MIXING a census class with one the census never counted still is,
    # because such a house cannot say which side of the comparison it stands on.
    _fires_authored(gaz, rules, [{"id": "biz_y", "type": ["tavern", "civic"]}],
                    "mixes census classes with classes the census never counted")

    # TWO NOTICES RULED TO BE ONE HOUSE (T-1422). The fold has to move the count, name
    # the pair, and refuse every way of writing a fold that would make the count
    # unauditable — which is most of the ways of writing one.
    def folding(**over):
        r = copy.deepcopy(rules)
        fold = {"folded": "b3", "into": "b1", "classes": ["tavern"],
                "ticket": "T-0000", "basis": "one house, two printed styles"}
        fold.update(over)
        r["one_house_rulings"] = {"rulings": [fold]}
        return r

    g = copy.deepcopy(gaz)
    g["businesses"].append({"id": "b3", "name": "A, tavern keeper", "trade": "tavern",
                            "built_at_scene_date": True})
    doc = build(g, folding(), _register_for(g))
    tav = next(c for c in doc["classes"] if c["class"] == "tavern")
    assert tav["town_records_at_scene_date"] == 1, tav
    assert tav["town_records_in_town"] == 1, tav
    assert tav["business_ids"] == ["b1"], tav
    assert tav["folded_business_ids"] == [{"business_id": "b3", "into": "b1"}], tav
    assert doc["totals"]["folded_into_another_house"] == 1, doc["totals"]
    # and the folded record is still IN the classification: folded is not deleted
    assert any(r["business_id"] == "b3" for r in doc["classification"]), doc["classification"]

    _fires(g, folding(folded="b1"), "folding b1 into itself")
    _fires(g, folding(folded="nobody"), "naming no business in the register")
    _fires(g, folding(basis="  "), "with no basis")
    _fires(g, folding(into="b2"), "share no census class")
    _fires(g, folding(classes=["other"]), "which is not a class both of them carry")

    # a house folded into a house that is itself folded would leave BOTH out of the count
    r = folding()
    r["one_house_rulings"]["rulings"].append(
        {"folded": "b1", "into": "b3", "classes": ["tavern"], "basis": "and back again"})
    _fires(g, r, "which is itself folded away")

    # the same house folded twice
    r = folding()
    r["one_house_rulings"]["rulings"].append(
        {"folded": "b3", "into": "b1", "classes": ["tavern"], "basis": "again"})
    _fires(g, r, "is folded twice")

    # no rulings section at all is the NORMAL state and is not a fault
    doc = build(g, rules, _register_for(g))
    tav = next(c for c in doc["classes"] if c["class"] == "tavern")
    assert tav["town_records_at_scene_date"] == 2, tav
    assert tav["folded_business_ids"] == [], tav

    print("trade_census_1835 self-tests pass (24 guards)")
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
