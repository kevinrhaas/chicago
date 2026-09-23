#!/usr/bin/env python3
"""Norris's 1844 ADVERTISING DIRECTORY against the 1835 residents (T-0568).

    tools/crosswalk_norris_1844_advertiser.py [--check]

The only place a name on an 1844 advertising card is allowed to touch a person
standing in the scene of 1 July 1835. It touches them as CORROBORATION and as a
CANDIDATE trade, never as an 1835 fact: under the ratified grading ladder an 1844
listing alone never makes an 1835 resident, and nothing here regrades anybody or
writes a business. The file this writes is a proposal for T-0569, which spends it.

THE RULE, written out so it reads back without the code:
  A card names PROPRIETORS. Each proprietor whose printed name carries both a
  surname and a given name or initial is compared against every person in the
  residents layer. The SURNAME must match after both are folded (case, punctuation
  and the scanner's standing confusions removed) AND the first initials must agree.
  A surname-only agreement is a REFUSAL, however good it looks — Norris lists
  eleven Smiths, and a card that says only "Skinner & Smith" says two surnames and
  nothing else. Where an 1835 person meets more than one card on that rule the match
  is AMBIGUOUS and is filed as such, not resolved; where two 1835 people meet THE
  SAME PRINTED PROPRIETOR the match is CONTESTED and is not made.

  A CONTEST IS BETWEEN TWO READINGS OF ONE PRINTED NAME, NOT TWO NAMES ON ONE CARD
  (T-0987, stretch 2). A card is a firm's advertisement and names its partners: card
  n1844_ad0046 prints "A. Loyd" AND "H. A. Blakesley", and the two 1835 residents who
  meet them meet a name each. Keying the contest on the card alone made rivals of
  partners — of men the card says stood in business TOGETHER — and withheld three
  matches the rule had already made. The key is the printed proprietor.

WHAT A MATCH IS WORTH, and it is less than it looks. An advertising card is a
SUBSCRIPTION: the firms in this section are the ones that paid Norris, so the
section is not the town's trades but the part of them with money for display type in
1844. A match therefore says that a surname and an initial the 1835 layer holds also
stood over a Chicago shop nine years later. That is corroboration of continuity and
a candidate trade, and the carry, when T-0569 makes it, is stated as 1844 evidence.
"""
import json, os, re, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import name_agreement as na  # the title and suffix vocabulary, imported not restated
import tiebreak            # the tie discriminator (T-0696), imported not restated
import trade_recorded     # "does the layer hold a trade?" (T-0867), likewise
import letter_list_bucket as llb  # the letter-list bucket refusal (T-1038)
import named_by_the_page as nbp  # the whole printed name (T-0987 stretch 14), likewise

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(ROOT, "data/research/directories/claims/norris_1844_advertiser.json")
HH = os.path.join(ROOT, "data/residents/households")
OUT = os.path.join(ROOT, "data/research/directories/norris_1844_advertiser_crosswalk_1835.json")

# The same fold the directory-proper crosswalk uses, so the two files agree about
# what "the same surname" means and can be read side by side.
FOLD = [(r"[^a-z]", ""), (r"^mc", "mac"), (r"^m$", ""), (r"ii", "n"), (r"rn", "m"),
        (r"vv", "w"), (r"1", "l"), (r"0", "o")]
# The titles are name_agreement's vocabulary, imported rather than restated
# (T-0987 stretch 8): four crosswalks each carried their own copy, the copies
# drifted, and not one of them held a rank spelled out in full.
TITLES = na.TITLES
# `junr` and `md` are this volume's own, and are kept: its tokeniser splits on
# whitespace alone, so "M.D." reaches the test as one word here and as two
# everywhere else.
SUFFIXES = na.SUFFIXES + ("junr", "md")


def fold(name: str) -> str:
    s = (name or "").lower()
    for pat, rep in FOLD:
        s = re.sub(pat, rep, s)
    return s


def split_printed(name: str):
    """A printed proprietor name into (given, surname). Returns (None, None) when the
    card gives a surname alone — 'Skinner', 'Hovey' — which is never enough to match."""
    toks = [t.strip(".,'\"") for t in (name or "").replace(",", " ").split()]
    toks = [t for t in toks if t and t.strip(".").lower() not in SUFFIXES]
    toks = [t for t in toks if t.lower() not in TITLES]
    if len(toks) < 2:
        return None, None
    return " ".join(toks[:-1]), toks[-1]


def initial(given: str) -> str:
    for tok in (given or "").split():
        bare = tok.strip(".,'\"").lower()
        if bare in TITLES:
            continue
        for ch in tok:
            if ch.isalpha():
                return ch.lower()
    return ""


def residents():
    out = []
    for fn in sorted(os.listdir(HH)):
        if not fn.endswith(".json"):
            continue
        doc = json.load(open(os.path.join(HH, fn), encoding="utf-8"))
        for p in doc.get("persons") or []:
            name = (p.get("name") or "").strip()
            if not name or (p.get("id") or "").endswith("_household"):
                continue
            parts = name.replace(",", " ").split()
            if len(parts) < 2:
                continue
            out.append({
                "person_id": p.get("id"),
                "household_id": doc.get("id"),
                "letter_list_only": bool(p.get("letter_list_only")),
                "name": name,
                "surname": parts[-1],
                "given": " ".join(parts[:-1]),
                "grade": p.get("grade"),
                "occupation": ((p.get("occupation") or {}).get("value")),
                "occupation_confidence": ((p.get("occupation") or {}).get("confidence")),
                "lives_at": ((doc.get("lives_at") or {}).get("value")),
                "works_at": ((doc.get("works_at") or {}).get("value")),
            })
    return out


def main():
    cards = json.load(open(CARDS, encoding="utf-8"))["claims"]

    # Every proprietor the advertiser names, keyed for matching. A card with three
    # partners offers three names; a card with none offers none.
    by_key = defaultdict(list)
    surnames = defaultdict(list)
    named, surname_only = 0, 0
    for c in cards:
        for printed in c["normalized"]["proprietors"]:
            given, surname = split_printed(printed)
            if not surname:
                surname_only += 1
                _, bare = None, [t.strip(".,'\"") for t in printed.split() if t.strip(".,'\"")]
                if bare:
                    surnames[fold(bare[-1])].append((c, printed))
                continue
            named += 1
            row = (c, printed)
            surnames[fold(surname)].append(row)
            if fold(surname) and initial(given):
                by_key[(fold(surname), initial(given))].append(row)

    def card_row(c, printed):
        n = c["normalized"]
        return {
            "claim": c["id"],
            "proprietor_as_printed": printed,
            "firm": n["firm"],
            "trade_1844": n["trade"],
            "address_1844": n["address"],
            "printed_page": c["locator"]["printed_page"],
        }

    matches, ambiguous, refusals = [], [], []
    bucket_refusals = []
    page_name_refusals, wife_axis_refusals = [], []
    ll_index = llb.buckets(llb.pool())
    people = residents()
    for r in people:
        key = (fold(r["surname"]), initial(r["given"]))
        hits = by_key.get(key, [])
        if not hits:
            if fold(r["surname"]) in surnames:
                refusals.append({
                    "resident": r["name"], "person_id": r["person_id"],
                    "surname_on_a_card": r["surname"],
                    "cards_under_that_surname": len(surnames[fold(r["surname"])]),
                    "rule": "The surname %r stands on an 1844 advertising card and no "
                            "proprietor under it carries the initial %r of %r. A "
                            "surname-only agreement is a refusal."
                            % (r["surname"], initial(r["given"]).upper() or "-", r["name"]),
                })
            continue
        # T-1038. A card that prints only an initial the post office's returns
        # print in full under the same surname takes nothing from a later
        # volume. It matters most HERE: Norris's alphabetical entry for the
        # jeweler says "(See card)", so a refusal that reached only the
        # directory proper would have let his own advertising card carry the
        # same trade and the same 144 Lake street to the same person.
        bucket = llb.refusal(r["name"], r["letter_list_only"], ll_index)
        if bucket:
            for c, printed in hits:
                row = dict(bucket)
                row.update({"resident": r["name"], "person_id": r["person_id"],
                            "household_id": r["household_id"],
                            "grade_1835": r["grade"], "record_id": card_row(c, printed)["claim"],
                            "card_1844": card_row(c, printed)})
                bucket_refusals.append(row)
            continue
        # T-0987 stretch 14. THE WHOLE PRINTED NAME, WORD FOR WORD. This file
        # keys a card on the surname and the first initial of the proprietor and
        # weighs nothing else at all — it never imported T-0670's forename rule
        # or stretch 9's further initials either (stretch 2 found that and left
        # it). The clause asks whether the printed proprietor IS this name: the
        # same number of words, word for word, closest of the candidates or none.
        page_declined = None
        if len(hits) > 1:
            kept_h, honorific = nbp.honorific_must_agree(
                r["name"], hits, lambda h: h[1])
            for h, note in honorific:
                row = card_row(*h)
                row.update({"clause": note["clause"], "rule": note["why"],
                            "honorific": note["honorific"]})
                wife_axis_refusals.append({
                    "resident": r["name"], "person_id": r["person_id"],
                    "grade_1835": r["grade"], "card_1844": row})
            hits = kept_h
        if len(hits) > 1:
            winner, note = nbp.decide(
                r["given"], hits, lambda h: split_printed(h[1])[0],
                reading_name=r["name"], name_of=lambda h: h[1])
            if winner is not None:
                for h in hits:
                    if h is winner:
                        continue
                    row = card_row(*h)
                    row.update({"clause": note["clause"], "rule": note["why"]})
                    page_name_refusals.append({
                        "resident": r["name"], "person_id": r["person_id"],
                        "grade_1835": r["grade"], "card_1844": row})
                hits = [winner]
            else:
                page_declined = note["why"]
        rows = [card_row(c, printed) for c, printed in hits]
        rec = {
            "resident": r["name"], "person_id": r["person_id"],
            "household_id": r["household_id"], "grade_1835": r["grade"],
            "occupation_1835": r["occupation"],
            "occupation_1835_confidence": r["occupation_confidence"],
            "lives_at_1835": r["lives_at"], "works_at_1835": r["works_at"],
            "rule": "Surname %r folds to the same string as the card's, and the given "
                    "name of both begins %s." % (r["surname"], initial(r["given"]).upper()),
            "cards_1844": rows,
        }
        if page_declined:
            rec["whole_name_declined"] = page_declined
        carries = []
        # `none_recorded` IS NO OCCUPATION (T-0867) — the same predicate, and the
        # same bug, as the directory-proper crosswalk carried until this ticket.
        if trade_recorded.absent(r["occupation"]) and any(x["trade_1844"] for x in rows):
            carries.append("trade")
        if not r["works_at"] and any(x["address_1844"] for x in rows):
            carries.append("place_of_business")
        rec["could_carry"] = carries
        rec["carry_rule"] = ("Whatever is carried is carried as 1844 evidence with "
                             "describes_date 1844 on the note, never as an 1835 fact, "
                             "and the grade of the person does not move. An advertising "
                             "card is a paid subscription: it is evidence that the firm "
                             "existed in 1844 and none at all that it existed in 1835.")
        (matches if len(rows) == 1 else ambiguous).append(rec)

    # A contest is two residents reading the SAME PRINTED NAME, so the key is the
    # card AND the proprietor as printed. Two partners advertising together are not
    # rivals: see the rule above, and T-0987 stretch 2 for the three it withheld.
    claimed = defaultdict(list)
    for m in matches:
        card = m["cards_1844"][0]
        claimed[(card["claim"], card["proprietor_as_printed"])].append(m)

    # T-0987 stretch 14, the other axis: which of two people of 1835 the printed
    # proprietor is. R6 first — a card paid for under a man's own name is not his
    # wife's, whatever the first initial says.
    given_1835 = {p["person_id"]: p["given"] for p in people}
    page_named, wife_refused = [], []
    for key, rivals in sorted(claimed.items()):
        if len(rivals) < 2:
            continue
        printed = key[1]
        given_of = lambda m: given_1835.get(m["person_id"], "")
        kept_r, wives = nbp.honorific_must_agree(
            printed, rivals, lambda m: m["resident"])
        for m, note in wives:
            wife_refused.append({"resident": m["resident"], "person_id": m["person_id"],
                                 "card_1844": m["cards_1844"][0], **note})
        if len(kept_r) > 1:
            winner, note = nbp.decide(
                split_printed(printed)[0], kept_r, given_of,
                reading_name=printed, name_of=lambda m: m["resident"], one_body=False)
        elif kept_r:
            winner, note = kept_r[0], {"clause": nbp.WIFE_CLAUSE, "named": None,
                                       "why": "the only reading left after R6"}
        else:
            winner, note = None, None
        if winner is None:
            continue
        for m in rivals:
            if m is winner:
                continue
            page_named.append({"resident": m["resident"], "person_id": m["person_id"],
                               "card_1844": m["cards_1844"][0],
                               "named_instead": winner["resident"],
                               "clause": note["clause"], "rule": note["why"]})
            m["_not_named"] = True
        winner["named_by_the_page"] = {
            "over": [m["resident"] for m in rivals if m is not winner], **note}
        claimed[key] = [winner]
    matches = [m for m in matches if not m.pop("_not_named", False)]

    contested = []
    for _, rivals in sorted(claimed.items()):
        if len(rivals) > 1:
            for m in rivals:
                m["contested_with"] = [x["resident"] for x in rivals if x is not m]
                m["rule"] += (" CONTESTED: %d residents of 1835 meet the printed name %r on "
                              "that rule, and at most one of them is the man who paid for "
                              "it. The match is not made."
                              % (len(rivals), m["cards_1844"][0]["proprietor_as_printed"]))
                contested.append(m)
    matches = [m for m in matches if "contested_with" not in m]

    # EVERY TIE IS OFFERED THE DISCRIMINATOR, and the offer is recorded whether or
    # not it fires (T-0987 acceptance 1: nothing in a stretch is left silent). The
    # terms are T-0696's and are not restated here — a trade may NARROW a tie and
    # never make a match, a premises and a year may not; tools/tiebreak.py carries
    # both refusals and their reasons.
    discriminated = []
    for key, rivals in sorted(claimed.items()):
        if len(rivals) < 2:
            continue
        _cid, printed_name = key
        printed = rivals[0]["cards_1844"][0]["trade_1844"]
        result = tiebreak.narrow([
            {"key": m["person_id"], "occupation_1835": m["occupation_1835"],
             "printed": printed} for m in rivals])
        winner = next((m for m in rivals if m["person_id"] == result["named"]), None)
        note = tiebreak.block(result,
                              winner["occupation_1835"] if winner else None,
                              winner["occupation_1835_confidence"] if winner else None)
        for m in rivals:
            m["discriminator"] = note or {"kind": tiebreak.KIND, "named": None,
                                          "why": result["why"], "sides": result["sides"]}
        if note:
            discriminated.append({
                "tie": "contested",
                "proprietor_as_printed": printed_name,
                "claim": _cid,
                "rivals": [m["resident"] for m in rivals],
                "named": winner["resident"],
                "person_id": winner["person_id"],
                "discriminator": note,
            })

    # The other shape of the same tie: one person of 1835 meeting several cards.
    # The sides are the cards and the trade is the one the resident carries, so the
    # same rule reads it without restatement.
    for m in ambiguous:
        result = tiebreak.narrow([
            {"key": c["claim"], "occupation_1835": m["occupation_1835"],
             "printed": c["trade_1844"]} for c in m["cards_1844"]])
        note = tiebreak.block(result, m["occupation_1835"],
                              m["occupation_1835_confidence"])
        m["discriminator"] = note or {"kind": tiebreak.KIND, "named": None,
                                      "why": result["why"], "sides": result["sides"]}
        if note:
            named_card = next(c for c in m["cards_1844"] if c["claim"] == result["named"])
            discriminated.append({
                "tie": "ambiguous",
                "resident": m["resident"],
                "person_id": m["person_id"],
                "cards": len(m["cards_1844"]),
                "named": named_card["firm"],
                "claim": named_card["claim"],
                "discriminator": note,
            })

    doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/crosswalk_norris_1844_advertiser.py. The proprietors "
                "of Norris's 1844 Advertising Directory against the 1835 residents layer. "
                "A PROPOSAL: it changes no resident record and writes no business, and "
                "under the ratified ladder an 1844 card alone never makes an 1835 "
                "resident or an 1835 business.",
        "generated_by": "tools/crosswalk_norris_1844_advertiser.py",
        "source_id": "norris_directory_1844",
        "rule": __doc__.split("THE RULE, written out")[1].split("WHAT A MATCH")[0].strip(),
        "what_a_match_is_worth": __doc__.split("WHAT A MATCH IS WORTH")[1].strip(),
        "discriminator_rule": tiebreak.__doc__.split("THE RULING")[1].split(
            "Run it directly")[0].strip(),
        "refused_discriminators": tiebreak.REFUSED_DISCRIMINATORS,
        "whole_name_rule": nbp.__doc__.split("THE RULING")[1].split(
            "WHAT THE WORD-COUNT TEST IS FOR")[0].strip(),
        "wife_rule": nbp.__doc__.split("A WIFE IS NOT HER HUSBAND")[1].split(
            "The honorific must stand")[0].strip(),
        "counts": {
            "cards": len(cards),
            "proprietor_names_printed": named + surname_only,
            "proprietors_with_a_given_name_or_initial": named,
            "proprietors_printed_as_a_surname_alone_unmatchable": surname_only,
            "residents_considered": len(people),
            "matched_one_card": len(matches),
            "matched_more_than_one_ambiguous": len(ambiguous),
            "one_printed_proprietor_contested_by_two_residents": len(contested),
            "surname_present_initial_absent_refused": len(refusals),
            "letter_list_bucket_refused": len(bucket_refusals),
            "residents_that_refusal_reaches": len({b["person_id"] for b in bucket_refusals}),
            "cards_the_whole_name_refused": len(page_name_refusals),
            "residents_that_whole_name_refusal_reaches": len(
                {f["person_id"] for f in page_name_refusals}),
            "cards_a_female_honorific_refused": len(wife_axis_refusals),
            "contests_the_page_named": len(
                {n["card_1844"]["claim"] for n in page_named}),
            "residents_not_named_by_a_contested_card": len(page_named),
            "residents_held_off_a_husbands_card": len(wife_refused),
            "ties_offered_the_trade_discriminator": len(ambiguous) + len(contested),
            "ties_narrowed_by_a_trade": len(discriminated),
            "of_those_contested": sum(1 for d in discriminated if d["tie"] == "contested"),
            "of_those_ambiguous": sum(1 for d in discriminated if d["tie"] == "ambiguous"),
            "could_carry_trade": sum(1 for m in matches if "trade" in m["could_carry"]),
            "could_carry_place_of_business": sum(
                1 for m in matches if "place_of_business" in m["could_carry"]),
        },
        "matches": sorted(matches, key=lambda m: m["resident"]),
        "discriminated": sorted(discriminated, key=lambda d: (d["tie"], d["claim"])),
        "contested": sorted(contested, key=lambda m: m["resident"]),
        "ambiguous": sorted(ambiguous, key=lambda m: m["resident"]),
        "refusals": sorted(refusals, key=lambda m: m["resident"]),
        "letter_list_bucket_refusals": sorted(
            bucket_refusals, key=lambda m: (m["resident"], m["card_1844"]["claim"])),
        "whole_name_refusals": sorted(
            page_name_refusals, key=lambda m: (m["resident"], m["card_1844"]["claim"])),
        "female_honorific_refusals": sorted(
            wife_axis_refusals, key=lambda m: (m["resident"], m["card_1844"]["claim"])),
        "not_named_by_the_page": sorted(
            page_named, key=lambda m: (m["card_1844"]["claim"], m["resident"])),
        "held_off_a_husbands_card": sorted(
            wife_refused, key=lambda m: (m["card_1844"]["claim"], m["resident"])),
    }
    if "--check" in sys.argv:
        if not os.path.exists(OUT):
            print("advertiser crosswalk: %s is not committed" % OUT, file=sys.stderr)
            return 1
        if json.load(open(OUT, encoding="utf-8")) != doc:
            print("advertiser crosswalk: committed file does not match — regenerate",
                  file=sys.stderr)
            return 1
        print("advertiser crosswalk: matches the committed file")
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(doc["counts"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
