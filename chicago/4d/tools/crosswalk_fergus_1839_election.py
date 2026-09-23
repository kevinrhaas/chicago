#!/usr/bin/env python3
"""The poll of 2 May 1837 against the four pools of 1835 names (T-0664).

The sibling of `crosswalk_fergus_1839.py`, and it imports that file's matching rule
rather than restating it, so the two cannot drift on the part that matters: SURNAME
must match after both are folded, AND the first initial of the given name must match.
A surname-only agreement is a REFUSAL. One 1835 name meeting more than one 1837 voter
is AMBIGUOUS and is filed as such; two 1835 people meeting one voter is CONTESTED and
no match is made.

WHAT IS DIFFERENT ABOUT THIS POOL, and it is the reason for a separate file. The 1839
directory gives a trade and a street, so a match there is enrichment. The 1837 poll
gives A WARD AND A VOTE, and nothing else — no trade, no address, no household. So a
match here carries exactly two things and they are both about 1837: the man was in
Chicago on 2 May 1837, and he was in that ward. Under the ratified grading ladder that
is CORROBORATION of continued residence for a person the project already holds, and it
is never, on its own, an 1835 resident.

A PROPOSAL. This file mints nobody and regrades nobody. T-0514 and T-0515 are the
passes allowed to write people; this is what they read.

  tools/crosswalk_fergus_1839_election.py            write the proposal
  tools/crosswalk_fergus_1839_election.py --check    rebuild and diff (the gate)
"""
import json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crosswalk_fergus_1839 as cw  # the rule, imported rather than restated
import name_agreement as na  # the further-initial refusal (T-0987 stretch 9)
import letter_list_bucket as llb  # the letter-list bucket refusal (T-1038)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLL = os.path.join(ROOT, "data/research/directories/claims/fergus_1839_election_1837.json")
OUT = os.path.join(ROOT, "data/research/directories/fergus_1839_election_crosswalk_1835.json")

# The roles the poll pages carry. A voter is a man who came to the poll; a nominee and a
# judge are men the party or the town put on the page, and they are matched too — a judge
# of election in 1837 is as good a corroboration as a voter, and there are eighteen of them.
PERSON_ROLES = ("voter", "nominee", "judge_of_election")


def row_of(claim):
    n = claim["normalized"]
    return {
        "claim": claim["id"],
        "as_printed": n["as_printed"],
        "printed_page": claim["locator"]["printed_page"],
        "role": n["role"],
        "ward_1837": n.get("ward"),
        "voted_for": n.get("voted_for"),
        "party": n.get("party"),
        "office": n.get("office"),
        # The two flags the reading carries forward, so a pass that spends this row
        # knows which lines the OCR handled badly.
        "column_run_on": bool(n.get("column_run_on")),
        "candidate_inferred": bool(n.get("candidate_inferred")),
    }


def index(claims):
    by_key, surnames = defaultdict(list), defaultdict(list)
    for c in claims:
        if c["normalized"].get("role") not in PERSON_ROLES:
            continue
        surname, given = cw.split_name(c["normalized"]["name"])
        if not surname:
            continue
        f = cw.fold(surname)
        if not f:
            continue
        surnames[f].append(c)
        i = cw.initial(given)
        if i:
            by_key[(f, i)].append(c)
    return by_key, surnames


def match_pool(pool, by_key, surnames, extra=None, bucket_refusals=None,
               middle_initial_refusals=None):
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
                    "rule": "The surname %r stands in the 1837 poll and no man under it "
                            "carries the initial %r of %r. A surname-only agreement is a "
                            "refusal." % (r["surname"], (i or "-").upper(), r["name"]),
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
                                "entry_1837": row_of(h)})
                    if extra:
                        rec.update(extra(r))
                    bucket_refusals.append(rec)
                continue
        # T-0987 stretch 9. THE FURTHER INITIALS, and this pool asks for them
        # because it is the one pool here whose rulings reach a CARD. The poll
        # prints `W. H. Clarke` and the town holds `W B Clarke`; the bucket
        # above compares the W and stops, so the poll line had been written onto
        # the wrong man's card. Applied where a card is reached and nowhere
        # else, which is the same scope T-0670 states on the directory file.
        mi_declined = None
        if middle_initial_refusals is not None:
            survivors, mi_refused, mi_declined = na.narrow_by_further_initials(
                r["given"], hits,
                lambda h: cw.split_name(h["normalized"]["name"])[1])
            for h, note in mi_refused:
                row = row_of(h)
                row.update(note)
                mrec = {"name": r["name"], "entry_1837": row}
                if extra:
                    mrec.update(extra(r))
                middle_initial_refusals.append(mrec)
            hits = survivors
            if not hits:
                continue
        rec = {"name": r["name"],
               "rule": "Surname %r folds to the same string as the 1837 entry's, and the "
                       "given name of both begins %s." % (r["surname"], i.upper()),
               "entries_1837": [row_of(h) for h in hits]}
        if mi_declined:
            rec["further_initials_declined"] = mi_declined
        if extra:
            rec.update(extra(r))
        (matched if len(hits) == 1 else ambiguous).append(rec)
    return matched, ambiguous, refused


CARRY_RULE = (
    "What a match may carry, and it is short: that the man was in Chicago on 2 May 1837 and "
    "in that ward. It is written as 1837 evidence with describes_date 1837-05-02, never as an "
    "1835 fact, and the person's grade does not move on this alone. Under the ratified ladder "
    "a second contemporary source is what lifts projected_resident, and a poll twenty-two "
    "months after the scene date is a second source about CONTINUED RESIDENCE, not about "
    "July 1835. The ward is a location in the CITY of 1837, whose six wards are drawn on "
    "printed page 46; it is not a location in the town of 1835 and does not place a house.")


def main():
    doc_in = json.load(open(POLL, encoding="utf-8"))
    claims = doc_in["claims"]
    by_key, surnames = index(claims)

    people = cw.residents()
    res_bucket_refused = []
    res_middle_initial_refused = []
    res_matched, res_ambiguous, res_refused = match_pool(
        people, by_key, surnames, bucket_refusals=res_bucket_refused,
        middle_initial_refusals=res_middle_initial_refused,
        extra=lambda r: {"person_id": r["person_id"], "household_id": r["household_id"],
                         "grade_1835": r["grade"]})
    # ONE 1837 VOTER, TWO 1835 PEOPLE is a collision, not a match.
    claimed = defaultdict(list)
    for m in res_matched:
        claimed[m["entries_1837"][0]["claim"]].append(m)
    contested = []
    for _, rivals in sorted(claimed.items()):
        if len(rivals) > 1:
            for m in rivals:
                m["contested_with"] = [x["name"] for x in rivals if x is not m]
                m["rule"] += (" CONTESTED: %d residents of 1835 meet this one 1837 entry on "
                              "that rule, and at most one of them is the man who voted. The "
                              "match is not made." % len(rivals))
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
        "_doc": "GENERATED by tools/crosswalk_fergus_1839_election.py. The poll of Chicago's "
                "first city election, 2 May 1837, as printed in Fergus 1839, against the 1835 "
                "residents layer, the voter and poll lists, the letter-list and newspaper "
                "persons, and the 1840 heads. A PROPOSAL: it changes no resident record, mints "
                "nobody and regrades nobody.",
        "generated_by": "tools/crosswalk_fergus_1839_election.py",
        "source_id": "fergus_chicago_directory_1839",
        "ticket": "T-0664",
        "rule": cw.__doc__.split("The rule, written out")[1].split("FOUR POOLS")[0].strip(),
        "scene_relation": "The poll is 2 May 1837, twenty-two months after the scene date of "
                          "1 July 1835, and it is printed in a volume Fergus completed in 1876 "
                          "out of Old Settlers' recollections. Evidence about 1837, reset in "
                          "1876.",
        "mints_or_regrades": False,
        "carry_rule": CARRY_RULE,
        "what_the_poll_does_not_give": "No trade, no address, no household and no house. The "
                                       "ward is the only location on the page, it is a ward of "
                                       "the CITY of 1837, and it places nobody in the town of "
                                       "1835.",
        "inputs": [
            {"what": "1837 poll persons indexed (voters, nominees, judges)",
             "path": "data/research/directories/claims/fergus_1839_election_1837.json",
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
            "residents_matched_one_entry": len(res_matched),
            "residents_ambiguous": len(res_ambiguous),
            "residents_contested": len(contested),
            "residents_surname_only_refused": len(res_refused),
            "residents_further_initial_disagreed_refused": len(res_middle_initial_refused),
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
            "middle_initial_refusals": sorted(
                res_middle_initial_refused,
                key=lambda m: (m["name"], m["entry_1837"]["claim"])),
            "letter_list_bucket_refusals": sorted(
                res_bucket_refused, key=lambda m: (m["name"], m["entry_1837"]["claim"])),
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
            print("fergus 1839 election crosswalk: the committed file does not match — "
                  "regenerate", file=sys.stderr)
            return 1
        print("fergus 1839 election crosswalk: matches the committed file")
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(doc["counts"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
