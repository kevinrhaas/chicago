#!/usr/bin/env python3
"""Norris 1844 against the 1835 residents (T-0555).

The ONLY place a name in an 1844 directory is allowed to touch a person standing
in the scene of 1 July 1835. It touches them as CORROBORATION and as CANDIDATE
ENRICHMENT, never as an 1835 fact: under the ratified grading ladder an 1844
listing alone never makes an 1835 resident, and nothing here regrades anybody.
The file this writes is a proposal for the pass that spends it; it changes no
resident record.

The rule, written out so it reads back without the code:
  SURNAME must match after both are folded (case, punctuation and the scanner's
  usual confusions removed), AND the first initial of the given name must match.
  A surname-only agreement is a REFUSAL, however good it looks — Norris lists
  eleven Smiths. AND, since T-0670, where BOTH readings print a full forename and
  the two full forenames DISAGREE the match is refused as well: the initial rule
  was written for a town of 848 names and it declared `Abbott, Thomas L.` onto
  Titus H. Abbott once T-0514 minted 532 more. An initial standing against a full
  name is untouched and stays a match. The forename rule lives in
  tools/name_agreement.py, which carries its own self-test. Where one 1835 person
  meets more than one 1844 entry on that rule the match is AMBIGUOUS and is filed
  as such, not resolved.
"""
import json, os, re, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reconstructed_person import is_reconstructed  # noqa: E402
import name_agreement as na  # the forename rule, imported rather than restated
import letter_list_bucket as llb  # the letter-list bucket refusal (T-1038)
import named_by_the_page as nbp  # the whole printed name (T-0987 stretch 14), likewise
import tiebreak            # the tie discriminator (T-0696), likewise
import trade_recorded     # "does the layer hold a trade?" (T-0867), likewise

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRIES = os.path.join(ROOT, "data/research/directories/claims/norris_1844_directory_entries.json")
HH = os.path.join(ROOT, "data/residents/households")
INDEX = os.path.join(ROOT, "data/residents/index.json")
OUT = os.path.join(ROOT, "data/research/directories/norris_1844_crosswalk_1835.json")

# The scanner's standing confusions in this volume, folded out of the surname
# before it is compared. Nothing here changes a quote.
FOLD = [(r"[^a-z]", ""), (r"^mc", "mac"), (r"^m$", ""), (r"ii", "n"), (r"rn", "m"),
        (r"vv", "w"), (r"1", "l"), (r"0", "o")]


# The titles are name_agreement's vocabulary, imported rather than restated
# (T-0987 stretch 8): four crosswalks each carried their own copy, the copies
# drifted, and not one of them held a rank spelled out in full.
TITLES = na.TITLES + na.SUFFIXES


def fold(name: str) -> str:
    s = (name or "").lower()
    for pat, rep in FOLD:
        s = re.sub(pat, rep, s)
    return s


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
    """Every person the 1835 layer holds, with the household they belong to."""
    out = []
    for fn in sorted(os.listdir(HH)):
        if not fn.endswith(".json"):
            continue
        doc = json.load(open(os.path.join(HH, fn), encoding="utf-8"))
        for p in doc.get("persons") or []:
            # T-1171: a person the reconstruction programme DREW is not a name any source printed.
            # Matching one to a printed name would be this project reading its own invention
            # back as evidence. reconstructed_person.py holds the rule.
            if is_reconstructed(p):
                continue
            name = (p.get("name") or "").strip()
            if not name or p.get("id", "").endswith("_household"):
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
    entries = json.load(open(ENTRIES, encoding="utf-8"))["claims"]
    # THE ENTRIES THIS PASS NEVER LOOKS AT, SAID OUT LOUD (T-1023).
    #
    # An entry with no surname is skipped here, and until T-1023 it was skipped in
    # silence — which is the whole reason five men the reader had refused to cap
    # (T-1018's `empty_prefix`) could leave the town's reach without anything
    # printing a number. A reading fault upstream showed up downstream as nothing
    # at all. So the skip is now a LIST, written into the output beside the counts,
    # and a name-less entry has to say why it holds no name.
    set_aside = []
    for c in entries:
        n = c["normalized"]
        if n["firm"] or n["surname"]:
            continue
        why = "no surname, and the reading does not say why"
        if n.get("turned_line"):
            why = ("a turned line read with %s, not a name — %s"
                   % (n["turned_line"]["joins"], n["turned_line"]["why"]))
        elif n.get("name_overrun", {}).get("refused"):
            why = ("the reader refused to cap the comma span: %s"
                   % n["name_overrun"]["why"])
        set_aside.append({"entry_id": c["id"], "kind": c["kind"],
                          "as_printed": n.get("as_printed"), "why": why})
    by_key = defaultdict(list)
    for c in entries:
        n = c["normalized"]
        if n["firm"] or not n["surname"]:
            continue
        key = (fold(n["surname"]), initial(n["given"]))
        if key[0] and key[1]:
            by_key[key].append(c)
    surnames = defaultdict(list)
    for c in entries:
        n = c["normalized"]
        if not n["firm"] and n["surname"]:
            surnames[fold(n["surname"])].append(c)

    matches, ambiguous, refusals, forename_refusals = [], [], [], []
    middle_initial_refusals = []
    page_name_refusals = []
    wife_axis_refusals = []
    bucket_refusals = []
    ll_index = llb.buckets(llb.pool())
    people = residents()
    for r in people:
        key = (fold(r["surname"]), initial(r["given"]))
        hits = by_key.get(key, [])
        if not hits:
            if fold(r["surname"]) in surnames:
                refusals.append({
                    "resident": r["name"], "person_id": r["person_id"],
                    "surname_in_1844": r["surname"],
                    "candidates": len(surnames[fold(r["surname"])]),
                    "rule": na.no_forename_refusal(r["name"], r["surname"], "Norris 1844",
                                                   len(surnames[fold(r["surname"])]))
                            if not initial(r["given"]) else
                            "The surname %r is in Norris 1844 and no entry under it carries "
                            "the initial %r of %r. A surname-only agreement is a refusal."
                            % (r["surname"], initial(r["given"]).upper(), r["name"]),
                })
            continue
        def row_of(h):
            return {
                "claim": h["id"],
                "as_printed": h["normalized"]["as_printed"],
                "printed_page": h["locator"]["printed_page"],
                "occupation_1844": h["normalized"]["occupation"],
                # T-1114. The place the trade is carried on, which Norris prints inside
                # the trade line and marks with nothing. It is carried here so the entry
                # row still says where the man traded now that `occupation_1844` is the
                # trade alone — and it is NOT offered in `could_carry`: spending a place
                # of business onto an 1835 card is the spend layer's ruling to make, not
                # this crosswalk's, and `address` on a card is a residence.
                "place_of_business_1844": h["normalized"].get("place_of_business"),
                "address_1844": h["normalized"]["address"],
            }
        # T-1038. THE CARD IS AN INITIAL THE LETTER LIST PRINTS TWICE. Refused
        # before the forename rule is asked, because the rule cannot see the
        # reading this card was seated over — and it is that reading, not this
        # one, that the entry would have to answer.
        bucket = llb.refusal(r["name"], r["letter_list_only"], ll_index)
        if bucket:
            for h in hits:
                row = dict(bucket)
                row.update({"resident": r["name"], "person_id": r["person_id"],
                            "household_id": r["household_id"],
                            "grade_1835": r["grade"], "record_id": h["id"],
                            "entry_1844": row_of(h)})
                bucket_refusals.append(row)
            continue
        kept, refused = [], []
        for h in hits:
            note = na.refusal(r["given"], h["normalized"]["given"])
            (refused if note else kept).append((h, note))
        for h, note in refused:
            row = row_of(h)
            row.update(note)
            forename_refusals.append({
                "resident": r["name"], "person_id": r["person_id"],
                "grade_1835": r["grade"], "entry_1844": row,
            })
        # T-0987 stretch 9. THE FURTHER INITIALS. The bucket above matched the
        # FIRST initial and `na.refusal` weighed the first forename; nothing had
        # ever compared a middle initial both readings print, so `H. B. Clarke`
        # stood against `Clarke, H. W.` on the H they share. Only initials both
        # sides set are compared, and the helper declines to fire where firing
        # would promote a SILENT survivor over a refused rival that spoke.
        survivors, mi_refused, mi_declined = na.narrow_by_further_initials(
            r["given"], [h for h, _ in kept], lambda h: h["normalized"]["given"])
        for h, note in mi_refused:
            row = row_of(h)
            row.update(note)
            middle_initial_refusals.append({
                "resident": r["name"], "person_id": r["person_id"],
                "grade_1835": r["grade"], "entry_1844": row,
            })
        kept = [(h, None) for h in survivors]
        if not kept:
            continue
        # T-0987 stretch 14. THE WHOLE PRINTED NAME, WORD FOR WORD — the clause
        # above weighs only the initials BOTH readings set, so an entry that
        # stops early is a silence and refuses nothing. R6's honorific runs
        # first, and a generational suffix the reading does not carry stops the
        # comparison. tools/named_by_the_page.py carries all three.
        page_declined = None
        if len(kept) > 1:
            survivors, honorific = nbp.honorific_must_agree(
                r["name"], [h for h, _ in kept],
                lambda h: h["normalized"]["printed_name"])
            for h, note in honorific:
                row = row_of(h)
                row.update({"clause": note["clause"], "rule": note["why"],
                            "honorific": note["honorific"]})
                wife_axis_refusals.append({
                    "resident": r["name"], "person_id": r["person_id"],
                    "grade_1835": r["grade"], "entry_1844": row})
            kept = [(h, None) for h in survivors]
        if len(kept) > 1:
            winner, note = nbp.decide(
                r["given"], [h for h, _ in kept],
                lambda h: h["normalized"]["given"], reading_name=r["name"],
                name_of=lambda h: h["normalized"]["printed_name"])
            if winner is not None:
                for h, _ in kept:
                    if h is winner:
                        continue
                    row = row_of(h)
                    row.update({"clause": note["clause"], "rule": note["why"]})
                    page_name_refusals.append({
                        "resident": r["name"], "person_id": r["person_id"],
                        "grade_1835": r["grade"], "entry_1844": row})
                kept = [(winner, None)]
            else:
                page_declined = note["why"]
        rows = [row_of(h) for h, _ in kept]
        rec = {
            "resident": r["name"], "person_id": r["person_id"],
            "household_id": r["household_id"], "grade_1835": r["grade"],
            "occupation_1835": r["occupation"],
            "occupation_1835_confidence": r["occupation_confidence"],
            "lives_at_1835": r["lives_at"], "works_at_1835": r["works_at"],
            "rule": "Surname %r folds to the same string as the 1844 entry's, and the "
                    "given name of both begins %s." % (r["surname"], initial(r["given"]).upper()),
            "entries_1844": rows,
        }
        if mi_declined:
            rec["further_initials_declined"] = mi_declined
        if page_declined:
            rec["whole_name_declined"] = page_declined
        carries = []
        # `none_recorded` IS NO OCCUPATION. The residents layer writes that
        # sentinel where a person's trade was never attested, so the truthiness
        # test this line used to make read 23 of the 48 matched people as
        # already having a trade and reported `could_carry_occupation: 0` — a
        # nil that looked like a finding and was a bug. Twenty-one of them have
        # a trade printed against their name in 1844 (T-0569).
        if trade_recorded.absent(r["occupation"]) and any(x["occupation_1844"] for x in rows):
            carries.append("occupation")
        if not r["lives_at"] and any(x["address_1844"] for x in rows):
            carries.append("address")
        rec["could_carry"] = carries
        rec["carry_rule"] = ("Whatever is carried is carried as 1844 evidence with "
                             "describes_date 1844 on the note, never as an 1835 fact, and "
                             "the grade of the person does not move.")
        rec["resident_given_is_initial_only"] = all(
            len(t.strip(".,")) <= 1 for t in r["given"].split() if t.strip(".,").isalpha())
        (matches if len(rows) == 1 else ambiguous).append(rec)

    # ONE 1844 ENTRY, TWO 1835 PEOPLE is not a match, it is a collision — Anson H.
    # Taylor and Augustine Deodat Taylor both meet "Taylor, A. D." on the initial
    # rule and at most one of them is that man. Contested pairs come out of matches.
    claimed = defaultdict(list)
    for m in matches:
        claimed[m["entries_1844"][0]["claim"]].append(m)

    # T-0987 stretch 14. THE SAME CLAUSE ON THE OTHER AXIS. The collision below
    # asks which of two people of 1835 a printed line names and has only the
    # first initial that put them both there. `Hogan, John S. C.` sets three
    # words and the town's John S. C. Hogan sets those three; `Morrison,
    # Orsemus` is the tax list's Orsemus and not the poll list's Ordemus; and
    # `Brown, Rufus B.` is the warehouseman's and not his wife's (R6, first).
    given_1835 = {p["person_id"]: p["given"] for p in people}
    given_1844 = {c["id"]: c["normalized"]["given"] for c in entries}
    printed_name_1844 = {c["id"]: c["normalized"]["printed_name"] for c in entries}
    page_named, wife_refused = [], []
    for cid, rivals in sorted(claimed.items()):
        if len(rivals) < 2:
            continue
        printed = given_1844.get(cid, "")
        given_of = lambda m: given_1835.get(m["person_id"], "")
        kept_r, wives = nbp.honorific_must_agree(
            printed, rivals, lambda m: m["resident"])
        for m, note in wives:
            wife_refused.append({"resident": m["resident"], "person_id": m["person_id"],
                                 "entry_1844": m["entries_1844"][0], **note})
        if len(kept_r) > 1:
            winner, note = nbp.decide(
                printed, kept_r, given_of,
                reading_name=printed_name_1844.get(cid, ""),
                name_of=lambda m: m["resident"], one_body=False)
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
                               "entry_1844": m["entries_1844"][0],
                               "named_instead": winner["resident"],
                               "clause": note["clause"], "rule": note["why"]})
            m["_not_named"] = True
        winner["named_by_the_page"] = {
            "over": [m["resident"] for m in rivals if m is not winner], **note}
        claimed[cid] = [winner]
    matches = [m for m in matches if not m.pop("_not_named", False)]

    contested = []
    for claim_id, rivals in sorted(claimed.items()):
        if len(rivals) > 1:
            for m in rivals:
                m["contested_with"] = [x["resident"] for x in rivals if x is not m]
                m["rule"] += (" CONTESTED: %d residents of 1835 meet this one 1844 entry on "
                              "that rule, and at most one of them is the man printed. The "
                              "match is not made." % len(rivals))
                contested.append(m)
    matches = [m for m in matches if "contested_with" not in m]

    # T-0696. THE TIE DISCRIMINATOR. A trade may NARROW a tie and never make one
    # a match: the narrowed tie is filed below in `discriminated`, the losing
    # side is filed as SILENT rather than contradicted, nothing moves into
    # `matches` and no grade moves. A premises and a year are REFUSED
    # discriminators — tools/tiebreak.py carries both refusals and why.
    discriminated = []
    for _cid, rivals in sorted(claimed.items()):
        if len(rivals) < 2:
            continue
        printed = rivals[0]["entries_1844"][0]["occupation_1844"]
        result = tiebreak.narrow([
            {"key": m["person_id"], "occupation_1835": m["occupation_1835"],
             "printed": printed} for m in rivals])
        winner = next((m for m in rivals if m["person_id"] == result["named"]), None)
        note = tiebreak.block(result, winner["occupation_1835"] if winner else None,
                              winner["occupation_1835_confidence"] if winner else None)
        for m in rivals:
            m["discriminator"] = note or {"kind": tiebreak.KIND, "named": None,
                                          "why": result["why"], "sides": result["sides"]}
        if note:
            discriminated.append({
                "tie": "contested",
                "entry_1844": rivals[0]["entries_1844"][0]["as_printed"],
                "claim": _cid,
                "rivals": [m["resident"] for m in rivals],
                "named": winner["resident"],
                "person_id": winner["person_id"],
                "discriminator": note,
            })

    # The other shape of the same tie: one person of 1835 meeting several
    # printed lines. The sides are the printed entries and the trade is the one
    # the resident carries, so the same rule reads it without restatement.
    for m in ambiguous:
        result = tiebreak.narrow([
            {"key": e["claim"], "occupation_1835": m["occupation_1835"],
             "printed": e["occupation_1844"]} for e in m["entries_1844"]])
        note = tiebreak.block(result, m["occupation_1835"], m["occupation_1835_confidence"])
        m["discriminator"] = note or {"kind": tiebreak.KIND, "named": None,
                                      "why": result["why"], "sides": result["sides"]}
        if note:
            named = next(e for e in m["entries_1844"] if e["claim"] == result["named"])
            discriminated.append({
                "tie": "ambiguous",
                "resident": m["resident"],
                "person_id": m["person_id"],
                "entries": len(m["entries_1844"]),
                "named": named["as_printed"],
                "claim": named["claim"],
                "discriminator": note,
            })

    doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/crosswalk_norris_1844.py. Norris's 1844 directory against "
                "the 825 households of the 1835 residents layer. A PROPOSAL: it changes no "
                "resident record, and under the ratified ladder an 1844 listing alone never "
                "makes an 1835 resident.",
        "generated_by": "tools/crosswalk_norris_1844.py",
        "source_id": "norris_directory_1844",
        "rule": __doc__.split("The rule, written out")[1].strip(),
        "discriminator_rule": tiebreak.__doc__.split("THE RULING")[1].split(
            "Run it directly")[0].strip(),
        "refused_discriminators": tiebreak.REFUSED_DISCRIMINATORS,
        "whole_name_rule": nbp.__doc__.split("THE RULING")[1].split(
            "WHAT THE WORD-COUNT TEST IS FOR")[0].strip(),
        "wife_rule": nbp.__doc__.split("A WIFE IS NOT HER HUSBAND")[1].split(
            "The honorific must stand")[0].strip(),
        "counts": {
            "residents_considered": len(people),
            "1844_entries_read": len(entries),
            "1844_entries_set_aside_for_want_of_a_surname": len(set_aside),
            "matched_one_1844_entry": len(matches),
            "matched_more_than_one_ambiguous": len(ambiguous),
            "one_1844_entry_contested_by_two_residents": len(contested),
            "surname_present_initial_absent_refused": len(refusals),
            "letter_list_bucket_refused": len(bucket_refusals),
            "residents_that_refusal_reaches": len({b["person_id"] for b in bucket_refusals}),
            "further_initial_disagreed_refused": len(middle_initial_refusals),
            "residents_that_further_initial_refusal_reaches": len(
                {f["person_id"] for f in middle_initial_refusals}),
            "initial_agreed_forenames_disagreed_refused": len(forename_refusals),
            "of_those_a_garbled_printed_forename": sum(
                1 for f in forename_refusals if f["entry_1844"]["garbled_reading"]),
            "residents_left_with_no_1844_entry_by_that_refusal": len(
                {f["person_id"] for f in forename_refusals}
                - {m["person_id"] for m in matches + ambiguous + contested}),
            "entries_the_whole_name_refused": len(page_name_refusals),
            "residents_that_whole_name_refusal_reaches": len(
                {f["person_id"] for f in page_name_refusals}),
            "entries_a_female_honorific_refused": len(wife_axis_refusals),
            "contests_the_page_named": len(
                {n["entry_1844"]["claim"] for n in page_named}),
            "residents_not_named_by_a_contested_entry": len(page_named),
            "residents_held_off_a_husbands_entry": len(wife_refused),
            "ties_narrowed_by_a_trade": len(discriminated),
            "of_those_contested": sum(1 for d in discriminated if d["tie"] == "contested"),
            "of_those_ambiguous": sum(1 for d in discriminated if d["tie"] == "ambiguous"),
            "could_carry_occupation": sum(1 for m in matches if "occupation" in m["could_carry"]),
            "could_carry_address": sum(1 for m in matches if "address" in m["could_carry"]),
        },
        "set_aside_for_want_of_a_surname": sorted(set_aside,
                                                  key=lambda e: e["entry_id"]),
        "matches": sorted(matches, key=lambda m: m["resident"]),
        "discriminated": sorted(discriminated, key=lambda d: (d["tie"], d["claim"])),
        "contested": sorted(contested, key=lambda m: m["resident"]),
        "ambiguous": sorted(ambiguous, key=lambda m: m["resident"]),
        "refusals": sorted(refusals, key=lambda m: m["resident"]),
        "letter_list_bucket_refusals": sorted(
            bucket_refusals, key=lambda m: (m["resident"], m["entry_1844"]["claim"])),
        "middle_initial_refusals": sorted(middle_initial_refusals,
                                          key=lambda x: x["resident"]),
        "forename_refusals": sorted(forename_refusals,
                                    key=lambda m: (m["resident"], m["entry_1844"]["claim"])),
        "whole_name_refusals": sorted(
            page_name_refusals, key=lambda m: (m["resident"], m["entry_1844"]["claim"])),
        "female_honorific_refusals": sorted(
            wife_axis_refusals, key=lambda m: (m["resident"], m["entry_1844"]["claim"])),
        "not_named_by_the_page": sorted(
            page_named, key=lambda m: (m["entry_1844"]["claim"], m["resident"])),
        "held_off_a_husbands_entry": sorted(
            wife_refused, key=lambda m: (m["entry_1844"]["claim"], m["resident"])),
    }
    if "--check" in sys.argv:
        if json.load(open(OUT, encoding="utf-8")) != doc:
            print("norris crosswalk: committed file does not match — regenerate", file=sys.stderr)
            return 1
        print("norris crosswalk: matches the committed file")
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(doc["counts"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
