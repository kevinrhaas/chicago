#!/usr/bin/env python3
"""The city register of 1839 and the mayors and sheriffs against the four pools of 1835
names (T-0665).

The sibling of `crosswalk_fergus_1839.py` and `crosswalk_fergus_1839_election.py`, and
it imports the first one's matching rule rather than restating it, so the three cannot
drift on the part that matters: SURNAME must match after both are folded, AND the first
initial of the given name must match. A surname-only agreement is a REFUSAL. One 1835
name meeting more than one register entry is AMBIGUOUS; two 1835 people meeting one
entry is CONTESTED and no match is made.

WHAT IS DIFFERENT ABOUT THIS POOL, and it is the reason for a separate file.

  * The 1839 directory gives a trade and a street, so a match there is enrichment.
  * The 1837 poll gives a ward and a vote.
  * THIS POOL GIVES AN OFFICE — and an office is the strongest single thing a name can
    carry, because it is the town saying who a man was, not a clerk writing down that
    he existed. A man who was city treasurer in 1839 is a man of standing in 1839, and
    if the project already holds him in 1835 that is a biography, not a coincidence.

  * AND THE TABLES REACH BACK BEHIND THE SCENE DATE, which nothing else in this volume
    does. The sheriffs of Cook County are printed from 1831: James Kinzie in 1831,
    Stephen Forbes in 1832, Silas W. Sherman in 1834 and 1836. A match on one of those
    four rows is not later evidence at all — it is a CONTEMPORARY office, held in or
    across the scene year, and the crosswalk marks it `reaches_scene: true` and says
    which years. That is the useful yield of these two pages and it is four rows wide.

WHAT A MATCH MAY NOT DO. Every row of the mayors' table and every line of the city
register postdates the scene: Chicago was not a city until March 1837. So a register
match is corroboration of CONTINUED RESIDENCE and nothing more, and under the ratified
grading ladder later evidence alone never makes an 1835 resident.

A PROPOSAL. This file mints nobody and regrades nobody. T-0514 and T-0515 are the
passes allowed to write people; this is what they read.

  tools/crosswalk_fergus_1839_register.py            write the proposal
  tools/crosswalk_fergus_1839_register.py --check    rebuild and diff (the gate)
"""
import json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crosswalk_fergus_1839 as cw  # the rule, imported rather than restated
import letter_list_bucket as llb  # the letter-list bucket refusal (T-1038)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTER = os.path.join(ROOT,
                        "data/research/directories/claims/fergus_1839_city_register.json")
OUT = os.path.join(ROOT,
                   "data/research/directories/fergus_1839_register_crosswalk_1835.json")

SCENE_YEAR = 1835
# The scene date sits inside the term the 1834 sheriff row opens, and the 1832 row's term
# runs up to it. Those are the only rows of these two pages whose office is contemporary
# with the town, and the reading's own derivation is what says so.
SCENE_REACHING_YEARS = (1831, 1832, 1834, 1836)


def reaches_scene(n):
    """Whether the office this entry carries was held in or across 1835.

    The sheriffs' table prints ELECTION years and the terms run to the next row, so the
    1834 row covers the scene date outright and the 1832 row's term runs up to it. 1831
    and 1836 are the rows on either side of that pair and are marked as near, not as
    covering. Nothing on printed page 38 reaches: the city did not exist."""
    if n.get("role") != "sheriff_of_cook_county":
        return None
    year = n.get("year")
    if year == 1834:
        return "covers"
    if year in (1831, 1832, 1836):
        return "adjacent"
    return None


def row_of(claim):
    n = claim["normalized"]
    return {
        "claim": claim["id"],
        "as_printed": n["as_printed"],
        "printed_page": claim["locator"]["printed_page"],
        "role": n.get("role"),
        "office": n.get("office"),
        "body": n.get("body"),
        "ward_1839": n.get("ward"),
        "year": n.get("year"),
        "ex_officio": bool(n.get("ex_officio")),
        # The two flags the reading carries forward, so a pass that spends this row knows
        # which lines the OCR handled badly and which years this reading repaired.
        "column_run_on": bool(n.get("column_run_on")),
        "year_ocr_repaired": bool(n.get("year_ocr_repaired")),
        "reaches_scene": reaches_scene(n),
    }


def index(claims):
    """Persons only, and only those with a usable given name. The board of health is
    three bare surnames and cannot be indexed under the rule at all — it is counted as
    unindexable rather than dropped silently."""
    by_key, surnames, unindexable = defaultdict(list), defaultdict(list), []
    for c in claims:
        if c["kind"] != "person":
            continue
        surname, given = cw.split_name(c["normalized"]["name"])
        if not surname:
            unindexable.append({"claim": c["id"], "as_printed": c["normalized"]["name"],
                                "why": "no surname could be split off the printed name"})
            continue
        f = cw.fold(surname)
        if not f:
            unindexable.append({"claim": c["id"], "as_printed": c["normalized"]["name"],
                                "why": "the surname folds to nothing"})
            continue
        surnames[f].append(c)
        i = cw.initial(given)
        if i:
            by_key[(f, i)].append(c)
        else:
            unindexable.append({
                "claim": c["id"], "as_printed": c["normalized"]["name"],
                "why": "the page prints a surname with no given name, so the rule's "
                       "first-initial half has nothing to test"})
    return by_key, surnames, unindexable


def match_pool(pool, by_key, surnames, extra=None, bucket_refusals=None):
    ll_index = llb.buckets(llb.pool())
    matched, ambiguous, refused = [], [], []
    for r in pool:
        f, i = cw.fold(r["surname"]), cw.initial(r["given"])
        hits = by_key.get((f, i), []) if i else []
        if not hits:
            if f in surnames:
                refused.append({
                    "name": r["name"],
                    "candidates_under_that_surname": len(surnames[f]),
                    "rule": "The surname %r stands on printed pages 38-39 and no man "
                            "under it carries the initial %r of %r. A surname-only "
                            "agreement is a refusal."
                            % (r["surname"], (i or "-").upper(), r["name"]),
                })
            continue
        # T-1038. THE CARD IS AN INITIAL THE LETTER LIST PRINTS TWICE. The post
        # office's returns print another name under this surname and this
        # initial IN FULL, and mint_letter_list_residents.py seats one household
        # per surname — so the card stands for readings the corpus cannot
        # separate, and a later list has not met any one of them.
        if bucket_refusals is not None:
            bucket = llb.refusal(r["name"], r.get("letter_list_only"), ll_index)
            if bucket:
                for h in hits:
                    rec = dict(bucket)
                    rec.update({"name": r["name"], "record_id": row_of(h)["claim"],
                                "entry_1839": row_of(h)})
                    if extra:
                        rec.update(extra(r))
                    bucket_refusals.append(rec)
                continue
        rows = [row_of(h) for h in hits]
        # A TABLE PRINTS A MAN TWICE. Augustus Garrett is mayor in 1843 and again in
        # 1845, Silas W. Sherman sheriff in 1834 and again in 1836. Two hits on identical
        # printed names is one man re-elected, not two men one name might be; it is still
        # not a single-entry match and is still filed as ambiguous, but a reader should
        # not have to work out which kind of ambiguity it is.
        reprint = len(rows) > 1 and len({row["as_printed"] for row in rows}) == 1
        rec = {"name": r["name"],
               "same_man_reprinted": reprint,
               "rule": "Surname %r folds to the same string as the register entry's, and "
                       "the given name of both begins %s." % (r["surname"], i.upper()),
               "entries_1839": rows,
               "offices": sorted({row["office"] for row in rows if row["office"]}),
               "reaches_scene": sorted({row["reaches_scene"] for row in rows
                                        if row["reaches_scene"]})}
        if extra:
            rec.update(extra(r))
        (matched if len(hits) == 1 else ambiguous).append(rec)
    return matched, ambiguous, refused


CARRY_RULE = (
    "What a match may carry, and it depends on WHICH TABLE it landed in. A match on printed "
    "page 38, or on any row of the mayors' table, is 1839-or-later evidence: it says the man "
    "held that office in that year and was therefore in Chicago in that year, it is written "
    "with the row's own describes_date and never as an 1835 fact, and the person's grade does "
    "not move on it alone — a later appearance is corroboration of CONTINUED RESIDENCE, not "
    "of July 1835. A match on the sheriffs' rows of 1831, 1832, 1834 or 1836 is different in "
    "kind: the office is contemporary with the town, the 1834 row's term covers the scene date "
    "outright, and such a match carries reaches_scene. Even there the SOURCE is a retrospect — "
    "a table running to 1874, set in 1876 out of Old Settlers' recollections per the compiler's "
    "warning on printed page 3 — so it may be cited as a contemporary office and may not be "
    "graded `documented` without a second, nearer record. The ward on printed page 38 is a ward "
    "of the CITY of 1839 and places no house in the town of 1835.")


def main():
    doc_in = json.load(open(REGISTER, encoding="utf-8"))
    claims = doc_in["claims"]
    by_key, surnames, unindexable = index(claims)

    people = cw.residents()
    res_bucket_refused = []
    res_matched, res_ambiguous, res_refused = match_pool(
        people, by_key, surnames, bucket_refusals=res_bucket_refused,
        extra=lambda r: {"person_id": r["person_id"], "household_id": r["household_id"],
                         "grade_1835": r["grade"]})
    # ONE REGISTER ENTRY, TWO 1835 PEOPLE is a collision, not a match.
    claimed = defaultdict(list)
    for m in res_matched:
        claimed[m["entries_1839"][0]["claim"]].append(m)
    contested = []
    for _, rivals in sorted(claimed.items()):
        if len(rivals) > 1:
            for m in rivals:
                m["contested_with"] = [x["name"] for x in rivals if x is not m]
                m["rule"] += (" CONTESTED: %d residents of 1835 meet this one register "
                              "entry on that rule, and at most one of them is the man who "
                              "held the office. The match is not made." % len(rivals))
                contested.append(m)
    res_matched = [m for m in res_matched if "contested_with" not in m]
    for m in res_matched:
        m["carry_rule"] = CARRY_RULE

    voters = cw.list_pool(cw.VOTERS, "entries",
                          lambda r: r.get("normalized") or r.get("as_read"),
                          lambda r: r.get("list"))
    v_matched, v_ambiguous, v_refused = match_pool(voters, by_key, surnames)
    letters = cw.list_pool(cw.GAZETTEER, "persons", lambda r: r.get("name"),
                           lambda r: r.get("id"))
    l_matched, l_ambiguous, l_refused = match_pool(letters, by_key, surnames)
    heads = cw.list_pool(cw.HEADS_1840, "heads",
                         lambda r: r.get("normalized") or r.get("as_read"),
                         lambda r: r.get("familysearch_id"))
    h_matched, h_ambiguous, h_refused = match_pool(heads, by_key, surnames)

    scene_rows = [row_of(c) for c in claims if reaches_scene(c["normalized"])]
    scene_matched = [m for m in res_matched if m["reaches_scene"]]

    doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/crosswalk_fergus_1839_register.py. The city register of "
                "Chicago for 1839 and the printed tables of mayors and sheriffs, as read out "
                "of Fergus 1839 printed pages 38-39, against the 1835 residents layer, the "
                "voter and poll lists, the letter-list and newspaper persons, and the 1840 "
                "heads. A PROPOSAL: it changes no resident record, mints nobody and regrades "
                "nobody.",
        "generated_by": "tools/crosswalk_fergus_1839_register.py",
        "source_id": "fergus_chicago_directory_1839",
        "ticket": "T-0665",
        "rule": cw.__doc__.split("The rule, written out")[1].split("FOUR POOLS")[0].strip(),
        "scene_relation": "The city register is 1839's, four years after the scene date of "
                          "1 July 1835, and Chicago was not a city until March 1837 — so no "
                          "office on printed page 38 existed in the town. The one exception "
                          "on these two pages is the sheriffs' table, which is printed from "
                          "1831 and whose 1834 row covers the scene date. The volume itself "
                          "is Fergus's 1876 completion out of Old Settlers' recollections.",
        "mints_or_regrades": False,
        "carry_rule": CARRY_RULE,
        "what_the_register_does_not_give": "No trade, no address, no household and no house. "
                                           "The ward on printed page 38 is a ward of the CITY "
                                           "of 1839, drawn in 1837, and it places nobody in "
                                           "the town of 1835.",
        "scene_reaching_rows": {
            "what": "The only rows on printed pages 38-39 whose office is contemporary with "
                    "the town. The sheriffs' table prints election years and the terms run to "
                    "the next row, so the 1834 row covers 1 July 1835 outright and the rows "
                    "at 1831, 1832 and 1836 stand beside it.",
            "years": list(SCENE_REACHING_YEARS),
            "rows": scene_rows,
            "residents_matched": [{"name": m["name"], "person_id": m["person_id"],
                                   "grade_1835": m["grade_1835"],
                                   "reaches_scene": m["reaches_scene"],
                                   "entries_1839": m["entries_1839"]}
                                  for m in sorted(scene_matched, key=lambda m: m["name"])],
        },
        "unindexable": {
            "what": "Register entries the matching rule cannot test, because the page prints "
                    "no given name. They are counted here rather than dropped, so a reader "
                    "can see what the rule declined to look at.",
            "entries": sorted(unindexable, key=lambda u: u["claim"]),
        },
        "inputs": [
            {"what": "register and table persons indexed",
             "path": "data/research/directories/claims/fergus_1839_city_register.json",
             "n": sum(len(v) for v in surnames.values())},
            {"what": "residents layer, persons", "path": "data/residents/households/",
             "n": len(people)},
            {"what": "voter, poll and tax list entries (T-0493)",
             "path": "data/research/civic/voter_crosswalk.json", "n": len(voters)},
            {"what": "letter-list and newspaper persons",
             "path": "data/research/newspapers/gazetteer.json", "n": len(letters)},
            {"what": "1840 heads of household read in this repo",
             "path": "data/research/census_1840/resident_crosswalk.json", "n": len(heads)},
        ],
        "counts": {
            "register_persons_indexed": sum(len(v) for v in surnames.values()),
            "register_persons_unindexable": len(unindexable),
            "scene_reaching_rows": len(scene_rows),
            "scene_reaching_residents_matched": len(scene_matched),
            "residents_matched_one_entry": len(res_matched),
            "residents_ambiguous": len(res_ambiguous),
            "residents_ambiguous_same_man_reprinted": sum(
                1 for m in res_ambiguous if m["same_man_reprinted"]),
            "residents_contested": len(contested),
            "residents_surname_only_refused": len(res_refused),
            "residents_letter_list_bucket_refused": len(res_bucket_refused),
            "voters_matched_one_entry": len(v_matched),
            "voters_ambiguous": len(v_ambiguous),
            "voters_surname_only_refused": len(v_refused),
            "letter_list_matched_one_entry": len(l_matched),
            "letter_list_ambiguous": len(l_ambiguous),
            "letter_list_surname_only_refused": len(l_refused),
            "heads_1840_matched_one_entry": len(h_matched),
            "heads_1840_ambiguous": len(h_ambiguous),
            "heads_1840_surname_only_refused": len(h_refused),
        },
        "residents": {
            "matches": sorted(res_matched, key=lambda m: m["name"]),
            "contested": sorted(contested, key=lambda m: m["name"]),
            "ambiguous": sorted(res_ambiguous, key=lambda m: m["name"]),
            "refusals": sorted(res_refused, key=lambda m: m["name"]),
            "letter_list_bucket_refusals": sorted(
                res_bucket_refused, key=lambda m: (m["name"], m["entry_1839"]["claim"])),
        },
        "voters": {"matches": sorted(v_matched, key=lambda m: m["name"]),
                   "ambiguous": sorted(v_ambiguous, key=lambda m: m["name"]),
                   "refusals": sorted(v_refused, key=lambda m: m["name"])},
        "letter_list": {"matches": sorted(l_matched, key=lambda m: m["name"]),
                        "ambiguous": sorted(l_ambiguous, key=lambda m: m["name"]),
                        "refusals": sorted(l_refused, key=lambda m: m["name"])},
        "heads_1840": {"matches": sorted(h_matched, key=lambda m: m["name"]),
                       "ambiguous": sorted(h_ambiguous, key=lambda m: m["name"]),
                       "refusals": sorted(h_refused, key=lambda m: m["name"])},
    }
    if "--check" in sys.argv:
        if json.load(open(OUT, encoding="utf-8")) != doc:
            print("fergus 1839 register crosswalk: the committed file does not match — "
                  "regenerate", file=sys.stderr)
            return 1
        print("fergus 1839 register crosswalk: matches the committed file")
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(doc["counts"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
