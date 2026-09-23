#!/usr/bin/env python3
"""The Fort Dearborn Addition bidders of June 1839 against the pools of 1835 names (T-0666).

The sibling of `crosswalk_fergus_1839_election.py`, and like it, it imports
`crosswalk_fergus_1839`'s matching rule rather than restating it, so the three cannot
drift on the part that matters: SURNAME must match after both are folded, AND the first
initial of the given name must match. A surname-only agreement is a REFUSAL. One 1835
name meeting more than one bidder is AMBIGUOUS; two 1835 people meeting one bidder is
CONTESTED and no match is made.

WHAT IS DIFFERENT ABOUT THIS POOL, and it is the reason for a separate file. The 1839
directory gives a trade and a street. The 1837 poll gives a ward and a vote. This list
gives A PRICE AND A LOT, and the lot is the thing to be careful with: it is ground in
the FORT DEARBORN ADDITION, which was the garrison's reservation in July 1835 and was
not lots at all. So a match here says the man was in Chicago in June 1839 and had money
to bid; it does NOT place him, or his house, or his trade, anywhere in the town of 1835.
The block and lot are carried on the match so a later pass can see them, and they are
labelled 1839 ground on every one.

THE OTHER HAZARD IS THE SPELLING, and it is worse here than on the poll pages. This
list is initials and abbreviations almost throughout — `L. R. Lyon`, `Thos. Dyer`,
`Geo. L. Campbell`, `J. H. Kinzie` — so the initial rule is doing nearly all the work
and the surname is doing the rest. `crosswalk_fergus_1839`'s fold and its refusal of a
surname-only agreement are what keep that honest, and the refusals are filed as fully
as the matches for the same reason they are there: an absent match reads exactly like a
pair nobody has looked at.

A PROPOSAL. This file mints nobody and regrades nobody. T-0514 and T-0515 are the
passes allowed to write people; this is what they read.

  tools/crosswalk_fergus_1839_lots.py            write the proposal
  tools/crosswalk_fergus_1839_lots.py --check    rebuild and diff (the gate)
"""
import json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crosswalk_fergus_1839 as cw  # the rule, imported rather than restated

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOTS = os.path.join(ROOT, "data/research/directories/claims/fergus_1839_ft_dearborn_lots.json")
OUT = os.path.join(ROOT, "data/research/directories/fergus_1839_lots_crosswalk_1835.json")


def bidders(claims):
    """One entry per NAME, carrying every lot that name bid on.

    A man bids twenty times on these pages — John King, jr. takes nine consecutive lots
    of block 9 — and twenty matches for one man is twenty chances to read the same
    corroboration as twenty. The pool is names; the lots ride along.
    """
    out = {}
    for c in claims:
        name = c["normalized"].get("bidder")
        if not name:
            continue
        e = out.setdefault(name, {"name": name, "lots": [], "claims": []})
        e["claims"].append(c["id"])
        e["lots"].append({
            "claim": c["id"],
            "block": c["normalized"]["block"],
            "block_carried": c["normalized"]["block_carried"],
            "lot": c["normalized"]["lot"],
            "amount_usd": c["normalized"]["amount_usd"],
            "as_printed": c["normalized"]["as_printed"],
            "printed_page": c["locator"]["printed_page"],
            "bidder_ditto": c["normalized"]["bidder_ditto"],
            "bidder_braced": c["normalized"]["bidder_braced"],
        })
    for e in out.values():
        paid = [l["amount_usd"] for l in e["lots"] if l["amount_usd"] is not None]
        e["lots_bid"] = len(e["lots"])
        e["amount_read_usd"] = sum(paid)
        e["lots_whose_price_the_scan_destroyed"] = len(e["lots"]) - len(paid)
    return out


def row_of(entry):
    return {"bidder_as_printed": entry["name"], "lots_bid": entry["lots_bid"],
            "amount_read_usd": entry["amount_read_usd"],
            "lots_whose_price_the_scan_destroyed":
                entry["lots_whose_price_the_scan_destroyed"],
            "lots": entry["lots"]}


def index(pool):
    by_key, surnames = defaultdict(list), defaultdict(list)
    for entry in pool.values():
        surname, given = cw.split_name(entry["name"])
        if not surname:
            continue
        f = cw.fold(surname)
        if not f:
            continue
        surnames[f].append(entry)
        i = cw.initial(given)
        if i:
            by_key[(f, i)].append(entry)
    return by_key, surnames


def match_pool(pool, by_key, surnames, extra=None):
    matched, ambiguous, refused = [], [], []
    for r in pool:
        f, i = cw.fold(r["surname"]), cw.initial(r["given"])
        hits = by_key.get((f, i), []) if i else []
        if not hits:
            if f in surnames:
                refused.append({
                    "name": r["name"],
                    "candidates_under_that_surname": len(surnames[f]),
                    "rule": "The surname %r stands among the Fort Dearborn Addition "
                            "bidders and no bidder under it carries the initial %r of "
                            "%r. A surname-only agreement is a refusal."
                            % (r["surname"], (i or "-").upper(), r["name"]),
                })
            continue
        rec = {"name": r["name"],
               "rule": "Surname %r folds to the same string as the bidder's, and the "
                       "given name of both begins %s." % (r["surname"], i.upper()),
               "bids_1839": [row_of(h) for h in hits]}
        if extra:
            rec.update(extra(r))
        (matched if len(hits) == 1 else ambiguous).append(rec)
    return matched, ambiguous, refused


CARRY_RULE = (
    "What a match may carry, and it is short: that the man was in Chicago between the 10th "
    "and the 24th of June 1839 and bid at the Fort Dearborn Addition sale. It is written as "
    "1839 evidence with describes_date 1839-06, never as an 1835 fact, and the person's "
    "grade does not move on this alone. Under the ratified ladder a second contemporary "
    "source is what lifts projected_resident, and a land sale four years after the scene "
    "date is a second source about CONTINUED RESIDENCE, not about July 1835. THE LOT IS NOT "
    "A LOCATION FOR 1835: the Fort Dearborn Addition is the Beaubien, or Reservation, lands, "
    "which in July 1835 were the garrison's ground and were not platted into lots at all. It "
    "places no house, no shop and no household in the town this project builds.")


def main():
    doc_in = json.load(open(LOTS, encoding="utf-8"))
    pool = bidders(doc_in["claims"])
    by_key, surnames = index(pool)

    people = cw.residents()
    res_matched, res_ambiguous, res_refused = match_pool(
        people, by_key, surnames,
        extra=lambda r: {"person_id": r["person_id"], "household_id": r["household_id"],
                         "grade_1835": r["grade"]})
    # ONE BIDDER, TWO 1835 PEOPLE is a collision, not a match.
    claimed = defaultdict(list)
    for m in res_matched:
        claimed[m["bids_1839"][0]["bidder_as_printed"]].append(m)
    contested = []
    for _, rivals in sorted(claimed.items()):
        if len(rivals) > 1:
            for m in rivals:
                m["contested_with"] = [x["name"] for x in rivals if x is not m]
                m["rule"] += (" CONTESTED: %d residents of 1835 meet this one bidder on that "
                              "rule, and at most one of them is the man who bid. The match is "
                              "not made." % len(rivals))
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

    doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/crosswalk_fergus_1839_lots.py. The bidders at the Fort "
                "Dearborn Addition sale of 10-24 June 1839, as printed in Fergus 1839, "
                "against the 1835 residents layer, the voter and poll lists, the letter-list "
                "and newspaper persons, and the 1840 heads. A PROPOSAL: it changes no "
                "resident record, mints nobody and regrades nobody.",
        "generated_by": "tools/crosswalk_fergus_1839_lots.py",
        "source_id": "fergus_chicago_directory_1839",
        "ticket": "T-0666",
        "rule": cw.__doc__.split("The rule, written out")[1].split("FOUR POOLS")[0].strip(),
        "scene_relation": "The sale ran 10-24 June 1839, four years after the scene date of "
                          "1 July 1835, on ground that in 1835 was the Fort Dearborn "
                          "reservation. Evidence about 1839, printed in a volume Fergus "
                          "completed in 1876.",
        "mints_or_regrades": False,
        "carry_rule": CARRY_RULE,
        "what_the_sale_does_not_give": "No trade, no address in the town of 1835, no "
                                       "household and no house. The block and lot are the "
                                       "only location on the page, they are ground platted "
                                       "in 1839 out of the garrison's reservation, and they "
                                       "place nobody in the town of 1835.",
        "spelling_note": "The bidders are printed as initials and abbreviations almost "
                         "throughout, so the initial rule carries nearly the whole match and "
                         "the refusals are correspondingly many. A bidder whose name the scan "
                         "destroyed — `!c . Walker`, `J- Burgess` — folds to nothing that "
                         "meets anybody, and is left unmatched rather than repaired.",
        "inputs": [
            {"what": "distinct bidders read at the sale",
             "path": "data/research/directories/claims/fergus_1839_ft_dearborn_lots.json",
             "n": len(pool)},
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
            "bidders": len(pool),
            "bidders_with_a_usable_surname": sum(len(v) for v in surnames.values()),
            "residents_matched_one_bidder": len(res_matched),
            "residents_ambiguous": len(res_ambiguous),
            "residents_contested": len(contested),
            "residents_surname_only_refused": len(res_refused),
            "voters_matched_one_bidder": len(v_matched),
            "voters_ambiguous": len(v_ambiguous),
            "voters_surname_only_refused": len(v_refused),
            "letter_list_matched_one_bidder": len(l_matched),
            "letter_list_ambiguous": len(l_ambiguous),
            "letter_list_surname_only_refused": len(l_refused),
            "heads_1840_matched_one_bidder": len(h_matched),
            "heads_1840_ambiguous": len(h_ambiguous),
            "heads_1840_surname_only_refused": len(h_refused),
        },
        "residents": {
            "matches": sorted(res_matched, key=lambda m: m["name"]),
            "contested": sorted(contested, key=lambda m: m["name"]),
            "ambiguous": sorted(res_ambiguous, key=lambda m: m["name"]),
            "refusals": sorted(res_refused, key=lambda m: m["name"]),
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
            print("fergus 1839 lots crosswalk: the committed file does not match — "
                  "regenerate", file=sys.stderr)
            return 1
        print("fergus 1839 lots crosswalk: matches the committed file")
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(doc["counts"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
