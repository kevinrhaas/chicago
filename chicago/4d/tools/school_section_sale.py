#!/usr/bin/env python3
"""T-1017: what the town's own school-section sale of October 1833 can and cannot check.

    python3 tools/school_section_sale.py --build
    python3 tools/school_section_sale.py --check
    python3 tools/school_section_sale.py --self-test

WHY THIS EXISTS. `data/research/land_sales/resident_rulings.json` upholds a proposal
only where the town's own record of a person carries something the register's row can
be CHECKED against beyond a bare name — a middle initial the register repeats, a trade
the purchase is consistent with, a second document, or the register's own Residence
column. Two refusals of September 2026, RUSSELL SAMUEL and SKINNER JOSEPH, both turned
on an argument that is none of those four and was filed rather than used: the rows are
at the town's OWN school-section sale, and a man on the town's tax list of the same
year is the kind of man who bought there. T-0990 declined to decide it in the middle of
a cohort, because admitting it would have reopened rulings already made.

This file is the arithmetic that decides it. It measures the sale out of the register
and sets the town's side of it beside the rest of the register, so the question is
answered by counting rather than by how the argument sounds.

WHAT IT IS NOT. Nothing here mints, regrades or matches anybody, and no figure below is
a ruling. The ruling it supports is hand-authored where every other ruling in this
domain lives — `resident_rulings.json` -> `questions_ruled` -> T-1017 — and the note
that reasons it out is `docs/RESEARCH/school_section_sale_1833.md`.

WHAT IT READS. `entries.json`, the committed reading of the Illinois State Archives'
tract register, for the sale itself; `resident_crosswalk.json`, which is derived from
that register and the residents layer, for the town's side. The sale needs no date
range and no section guessed at: the register carries its own code for it in
`type_of_sale`, and `SC` and section 16 of T39N R14E are the same 337 rows, which is
the first thing --self-test proves.

THE THREE INVARIANTS THE RULING RESTS ON are asserted, not merely printed, because a
ruling that stops being true should fail a build rather than wait to be noticed:

  1. The sale is NOT EXCLUSIVE — some buyers carry a surname the residents layer holds
     nobody of at all.
  2. The sale does not CARRY a name on its own — fewer than half its buyer spellings
     hold an upheld match, so the criterion would be wrong more often than right.
  3. The sale cannot SEPARATE two bearers of a name — its own pages print more than one
     spelling of the same surname, which is the WENTWORTH reasoning of T-0990 applied
     to the sale instead of to the register as a whole.

The enrichment that argues the other way is measured too, and honestly: the sale IS
several times richer in town-side names than the rest of the register. That is a fact
about the sale's population, and the ruling says why a population cannot check a row.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "data" / "research" / "land_sales"
ENTRIES = DOMAIN / "entries.json"
CROSSWALK = DOMAIN / "resident_crosswalk.json"
RULINGS = DOMAIN / "resident_rulings.json"
OUT = DOMAIN / "school_section_sale_1833.json"

SALE_CODE = "SC"

# The register's own words for "the residents layer holds nobody of this surname". The
# crosswalk writes this sentence and nothing else writes it; a purchaser all of whose
# refusals read this way has no town-side claimant to be confused with.
SURNAME_ABSENT = re.compile(r"refused against 0 residents named", re.I)
CITES_THE_SALE = re.compile(r"school.section", re.I)


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def money(x: float) -> float:
    return round(x + 0.0, 2)


def pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 1) if d else 0.0


def priced_by_acre(rows) -> dict:
    """Price per acre over the rows that actually state an acreage.

    A row that states none is a town lot, and it is priced as a lot. Silently folding
    those into a rate would flatter the school section's — the one figure here that
    says most plainly what kind of sale it was.
    """
    with_acres = [e for e in rows if float(e["acres"] or 0) > 0]
    acres = money(sum(float(e["acres"]) for e in with_acres))
    price = money(sum(float(e["total_price"] or 0) for e in with_acres))
    return {
        "rows": len(with_acres),
        "acres": acres,
        "price": price,
        "per_acre": money(price / acres) if acres else 0,
    }


def classify(name: str, matches: dict, refusals: dict) -> str:
    """Where a purchaser spelling stands against the residents layer.

    Every purchaser spelling in the register is in exactly one of the crosswalk's two
    lists, so these five readings partition them. `upheld`/`named` are adjudications;
    `surname_absent` is not an adjudication at all but a fact about the layer, which is
    why the ruling leans on it hardest.
    """
    ms = matches.get(name, [])
    if ms:
        ruled = [(m.get("ruling") or {}).get("ruling") for m in ms]
        if "upheld" in ruled:
            return "upheld"
        if "named" in ruled:
            return "named"
        if ruled and all(r == "refused" for r in ruled):
            return "match_refused"
        return "match_unruled"
    rs = refusals.get(name, [])
    if rs and all(SURNAME_ABSENT.search(r.get("rule", "") or "") for r in rs):
        return "surname_absent"
    return "refused_against_a_rival"


READINGS = ["upheld", "named", "match_refused", "match_unruled",
            "refused_against_a_rival", "surname_absent"]


def side(names, matches, refusals) -> dict:
    c = collections.Counter(classify(n, matches, refusals) for n in names)
    total = len(names)
    return {
        "purchaser_spellings": total,
        "readings": {k: c.get(k, 0) for k in READINGS},
        "share_upheld_pct": pct(c.get("upheld", 0), total),
        "share_surname_absent_pct": pct(c.get("surname_absent", 0), total),
    }


def build() -> dict:
    entries = load(ENTRIES)["entries"]
    cross = load(CROSSWALK)
    rulings = load(RULINGS)

    sale = [e for e in entries if e["type_of_sale"] == SALE_CODE]
    rest = [e for e in entries if e["type_of_sale"] != SALE_CODE]
    sale_names = sorted({e["purchaser_as_read"] for e in sale})
    rest_names = sorted({e["purchaser_as_read"] for e in rest} - set(sale_names))

    matches = collections.defaultdict(list)
    for m in cross["matches"]:
        matches[m["purchaser_as_read"]].append(m)
    refusals = collections.defaultdict(list)
    for r in cross["refusals"]:
        refusals[r["a"]].append(r)

    tracts = sorted({(e["township"], e["range"], e["section"], e["meridian"])
                     for e in sale})
    by_name = collections.Counter(e["purchaser_as_read"] for e in sale)
    acres = collections.Counter()
    price = collections.Counter()
    for e in sale:
        acres[e["purchaser_as_read"]] += float(e["acres"] or 0)
        price[e["purchaser_as_read"]] += float(e["total_price"] or 0)

    surname = collections.defaultdict(set)
    for n in sale_names:
        surname[n.split()[0]].add(n)
    repeated = {k: sorted(v) for k, v in sorted(surname.items()) if len(v) > 1}

    absent = [n for n in sale_names
              if classify(n, matches, refusals) == "surname_absent"]

    cited = collections.Counter()
    tickets = set()
    for r in rulings["ruled"]:
        if CITES_THE_SALE.search(r.get("reasoning", "") or ""):
            cited[r["ruling"]] += 1
            tickets.add(r["ticket"])

    total_price = money(sum(float(e["total_price"] or 0) for e in sale))

    # 252 of the 337 rows are TOWN LOTS, which the register prices without stating an
    # acreage; the other 85 are whole blocks and state one. Dividing the whole price by
    # the stated acres would therefore invent a rate three times too high, so the rate
    # below is taken on the block rows alone and says so.
    priced = priced_by_acre(sale)

    return {
        "schema": 1,
        "domain": "land_sales",
        "source_id": "isa_public_domain_land_tract_sales",
        "generated_by": "tools/school_section_sale.py --build",
        "question": ("T-1017 — is buying at the town's OWN school-section sale a check "
                     "on a town-side name, or still a bare name?"),
        "the_ruling_is_not_here": (
            "This file is the arithmetic. The ruling is hand-authored at "
            "data/research/land_sales/resident_rulings.json -> questions_ruled -> "
            "T-1017, and reasoned out at docs/RESEARCH/school_section_sale_1833.md."),
        "the_sale": {
            "what_names_it": ("the register's own type_of_sale code, not a date range "
                              "this project chose: SC and section 16 of T39N R14E are "
                              "the same rows, and --self-test holds that"),
            "type_of_sale_code": SALE_CODE,
            "tracts": [{"township": t, "range": r, "section": s, "meridian": m}
                       for t, r, s, m in tracts],
            "dates": sorted({e["date_purchased"] for e in sale}),
            "rows": len(sale),
            "purchaser_spellings": len(sale_names),
            "total_price": total_price,
            "rows_sold_as_town_lots_with_no_acreage_stated":
                len(sale) - priced["rows"],
            "what_the_ground_fetched": dict(priced, compare_with={
                code: priced_by_acre([e for e in entries
                                      if e["type_of_sale"] == code])
                for code in sorted({e["type_of_sale"] for e in entries}
                                   - {SALE_CODE})}),
            "volumes_and_pages": sorted({e["volume"] + "/" + e["page"] for e in sale}),
        },
        "the_rest_of_the_register": {
            "rows": len(rest),
            "purchaser_spellings_not_also_at_the_sale": len(rest_names),
            "acres": money(sum(float(e["acres"] or 0) for e in rest)),
            "total_price": money(sum(float(e["total_price"] or 0) for e in rest)),
        },
        "largest_hands_at_the_sale": [
            {"purchaser_as_read": n, "rows": by_name[n],
             "acres": money(acres[n]), "total_price": money(price[n]),
             "stands_as": classify(n, matches, refusals)}
            for n in sorted(by_name, key=lambda n: (-by_name[n], n))[:12]
        ],
        "the_town_side": {
            "measured_against": "data/research/land_sales/resident_crosswalk.json",
            "note": ("These readings move whenever a ruling is made or the residents "
                     "layer grows, so a later run that rules on this domain must re-run "
                     "--build. That coupling is deliberate: it is what keeps the figures "
                     "the ruling quotes from going quietly stale."),
            "at_the_sale": side(sale_names, matches, refusals),
            "everywhere_else": side(rest_names, matches, refusals),
        },
        "surnames_the_layer_holds_nobody_of": {
            "count": len(absent),
            "purchasers": absent,
        },
        "surnames_the_sale_itself_prints_more_than_once": {
            "count": len(repeated),
            "surnames": repeated,
        },
        "rulings_that_already_cite_the_sale": {
            "total": sum(cited.values()),
            "by_ruling": dict(sorted(cited.items())),
            "tickets": sorted(tickets),
            "note": ("The sale is named in reasoning on both sides already — it is the "
                     "corroboration in an uphold and the thing refused to carry a row in "
                     "a refusal. What it has never been is the ground."),
        },
    }


def invariants(doc) -> list:
    """The three the ruling rests on. A flip here reopens T-1017 rather than passing."""
    bad = []
    at = doc["the_town_side"]["at_the_sale"]
    if at["readings"]["surname_absent"] < 1:
        bad.append("the sale now reaches no buyer whose surname the layer lacks — "
                   "T-1017 rested on it NOT being a townsmen-only roll; reopen it")
    if at["share_upheld_pct"] >= 50.0:
        bad.append("upheld matches are now a majority of the sale's buyers (%.1f%%) — "
                   "T-1017 rested on the criterion being wrong more often than right; "
                   "reopen it" % at["share_upheld_pct"])
    if doc["surnames_the_sale_itself_prints_more_than_once"]["count"] < 1:
        bad.append("the sale no longer prints a surname twice — T-1017's third arm was "
                   "that it cannot separate two bearers of a name; reopen it")
    return bad


def self_test() -> int:
    failed = 0

    def bad(msg):
        nonlocal failed
        failed += 1
        print("   FAIL " + msg)

    entries = load(ENTRIES)["entries"]

    # 1. The code and the section are the same rows. Everything downstream reads the
    # code, so a register that ever sold SC off section 16 — or sold section 16 under
    # another code — would silently change what "the sale" means.
    by_code = {e["record_id"] for e in entries if e["type_of_sale"] == SALE_CODE}
    by_tract = {e["record_id"] for e in entries
                if (e["section"], e["township"], e["range"]) == ("16", "39N", "14E")}
    if by_code != by_tract:
        bad("SC and section 16 of T39N R14E are no longer the same rows "
            "(%d vs %d)" % (len(by_code), len(by_tract)))

    doc = build()

    # 2. The arithmetic closes on the register.
    sale = [e for e in entries if e["type_of_sale"] == SALE_CODE]
    if doc["the_sale"]["rows"] != len(sale):
        bad("the row count does not close on the register")
    if doc["the_sale"]["purchaser_spellings"] != len({e["purchaser_as_read"] for e in sale}):
        bad("the purchaser count does not close on the register")
    if money(sum(float(e["total_price"] or 0) for e in sale)) != doc["the_sale"]["total_price"]:
        bad("the price does not close on the register")

    # 3. The readings partition the buyers — no spelling counted twice, none dropped.
    at = doc["the_town_side"]["at_the_sale"]
    if sum(at["readings"].values()) != at["purchaser_spellings"]:
        bad("the readings do not partition the sale's purchaser spellings")

    # 4. The enrichment the ruling concedes is real, and is stated in the direction it
    # actually runs. If this ever reverses, the note's prose is wrong, not just stale.
    other = doc["the_town_side"]["everywhere_else"]
    if not at["share_upheld_pct"] > other["share_upheld_pct"]:
        bad("the sale is no longer richer in upheld matches than the rest of the "
            "register — the note concedes an enrichment that would not exist")
    if not at["share_surname_absent_pct"] < other["share_surname_absent_pct"]:
        bad("the sale no longer carries fewer unknown surnames than the rest of the "
            "register — same")

    # 5. The three invariants fire when broken, and pass on the real document.
    for msg in invariants(doc):
        bad("invariant broken on the committed data: " + msg)
    for name, mutate in (
        ("a townsmen-only roll",
         lambda d: d["the_town_side"]["at_the_sale"]["readings"].update(surname_absent=0)),
        ("upheld in the majority",
         lambda d: d["the_town_side"]["at_the_sale"].update(share_upheld_pct=50.0)),
        ("no surname printed twice",
         lambda d: d["surnames_the_sale_itself_prints_more_than_once"].update(count=0)),
    ):
        broken = json.loads(dumps(doc))
        mutate(broken)
        if not invariants(broken):
            bad("the invariant for %r does not fire when broken" % name)

    # 6. Nobody is minted: the output may name purchaser SPELLINGS, which are the
    # register's own strings, and must carry no resident id and no household id.
    blob = dumps(doc)
    for needle in ('"resident_id"', '"household_id"', '"hh_'):
        if needle in blob:
            bad("a residents-layer identifier reached the output: %s" % needle)

    if failed:
        print("   %d assertion(s) failed" % failed)
        return 1
    print("   OK: SC is section 16 and nothing else, %d rows and %d buyers close on the "
          "register, the readings partition them, the enrichment runs the way the note "
          "says, and all three invariants fire when broken"
          % (doc["the_sale"]["rows"], doc["the_sale"]["purchaser_spellings"]))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    doc = build()
    if args.check:
        broken = invariants(doc)
        if broken:
            for msg in broken:
                print("   FAIL " + msg)
            return 1
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != dumps(doc):
            print("   FAIL %s is stale or hand-edited; rebuild it with "
                  "tools/school_section_sale.py --build" % OUT.relative_to(ROOT))
            return 1
        at = doc["the_town_side"]["at_the_sale"]
        print("   ok    %s re-derives — %d rows, %d buyers, %.1f%% upheld against "
              "%.1f%% elsewhere, and %d buyers the layer has no surname for"
              % (OUT.relative_to(ROOT), doc["the_sale"]["rows"],
                 doc["the_sale"]["purchaser_spellings"], at["share_upheld_pct"],
                 doc["the_town_side"]["everywhere_else"]["share_upheld_pct"],
                 at["readings"]["surname_absent"]))
        return 0
    OUT.write_text(dumps(doc), encoding="utf-8")
    at = doc["the_town_side"]["at_the_sale"]
    print("wrote %s — %d rows over %d days, %d buyer spellings, %s acres of whole "
          "blocks inside a $%s sale; "
          "%.1f%% upheld at the sale against %.1f%% elsewhere, and %d buyers carry a "
          "surname the layer holds nobody of"
          % (OUT.relative_to(ROOT), doc["the_sale"]["rows"],
             len(doc["the_sale"]["dates"]), doc["the_sale"]["purchaser_spellings"],
             doc["the_sale"]["what_the_ground_fetched"]["acres"],
             doc["the_sale"]["total_price"],
             at["share_upheld_pct"],
             doc["the_town_side"]["everywhere_else"]["share_upheld_pct"],
             at["readings"]["surname_absent"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
