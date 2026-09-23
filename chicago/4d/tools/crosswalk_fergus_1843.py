#!/usr/bin/env python3
"""Fergus 1843 against the 1835 residents (T-0571).

The ONLY place a name in an 1843 directory is allowed to touch a person standing
in the scene of 1 July 1835. It touches them as CORROBORATION and as CANDIDATE
ENRICHMENT, never as an 1835 fact: under the ratified grading ladder a later
listing alone never makes an 1835 resident, and nothing here regrades anybody.
The file this writes is a proposal for the pass that spends it (T-0569); it
changes no resident record.

The rule, written out so it reads back without the code:
  SURNAME must match after both are folded (case, punctuation and the
  transcriber's usual confusions removed), AND the first initial of the given
  name must match. A surname-only agreement is a REFUSAL, however good it looks —
  Fergus lists thirty-one Smiths. AND, since T-0670, where BOTH readings print a
  full forename and the two full forenames DISAGREE the match is refused as well:
  the initial rule was written for a town of 848 names and it declared
  `Abbott, Thomas L.` onto Titus H. Abbott once T-0514 minted 532 more. An
  initial standing against a full name is untouched and stays a match. The
  forename rule lives in tools/name_agreement.py, which carries its own
  self-test. Where one 1835 person meets more than one 1843 entry on that rule
  the match is AMBIGUOUS and is filed as such, not resolved; where two 1835
  people meet one 1843 entry it is CONTESTED and no match is made.

  AND THE THING COUNTED IS A PERSON, NOT A PRINTING (T-0987 stretch 7). This
  volume is two directories bound as one, and a tradesman who paid for a notice
  in the business directory also stands in the alphabetical roll — so Fergus
  prints him twice, and the ambiguity test above used to read his own notice as a
  rival for him. `tools/printed_twice.py` is the rule that folds a notice onto
  the roll entry it can only be; where it cannot, the notice stands as its own
  candidate exactly as before and the refusal names the clause that was silent.
  The notice is not discarded: it is carried on the roll entry's row as
  `also_printed`, quotable, and the whole ledger of 106 notices — attached and
  refused — stands in `printed_twice` below.

WHAT THIS DIRECTORY CARRIES THAT NORRIS'S DOES NOT is a date of death. Fergus
compiled the volume in 1896 and set each man's death in brackets after his entry —
"[died June 6, 1882, aged 67.]" — which, with the age, is a year of birth. Those
brackets are carried onto the match as `death_note_1843` for T-0574, which is the
ticket that reads them as birth years. They are not spent here.
"""
import json, os, re, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import name_agreement as na  # the forename rule, imported rather than restated
import printed_twice as pt  # one man, two printings (T-0987 stretch 7), likewise
import tiebreak            # the tie discriminator (T-0696), likewise
import trade_recorded     # "does the layer hold a trade?" (T-0867), likewise
import letter_list_bucket as llb  # the letter-list bucket refusal (T-1038)
import named_by_the_page as nbp  # the whole printed name (T-0987 stretch 14), likewise
import surname_one_letter_away as ola  # the surname one letter off (stretch 15)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRIES = os.path.join(ROOT, "data/research/directories/claims/fergus_1843_directory_entries.json")
HH = os.path.join(ROOT, "data/residents/households")
OUT = os.path.join(ROOT, "data/research/directories/fergus_1843_crosswalk_1835.json")

# The transcriber's and the printer's standing confusions in this volume, folded
# out of the surname before it is compared. Nothing here changes a quote.
FOLD = [(r"[^a-z]", ""), (r"^mc", "mac"), (r"^m$", ""), (r"ii", "n"), (r"rn", "m"),
        (r"vv", "w"), (r"1", "l"), (r"0", "o")]
DEATH = re.compile(r"^(died|d\.|killed|suicide|drowned|lost)", re.I)


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


def death_note(entry):
    for note in entry["normalized"].get("bracket_notes") or []:
        if DEATH.match(note.strip()):
            return note
    return None


def row_of(entry, also=None):
    n = entry["normalized"]
    row = {
        "claim": entry["id"],
        "as_printed": n["as_printed"],
        "page": entry["locator"]["page"],
        "section": n["section"],
        "trade_heading": n["trade_heading"],
        "occupation_1843": n["occupation"],
        "address_1843": n["address"],
        "death_note_1843": death_note(entry),
    }
    # The same man's other printing in this volume (T-0987 stretch 7). It is not
    # a second candidate and it is not thrown away: it is his, and it is quoted.
    for notice in (also or {}).get(entry["id"], []):
        row.setdefault("also_printed", []).append({
            "claim": notice["id"],
            "as_printed": notice["normalized"]["as_printed"],
            "page": notice["locator"]["page"],
            "section": notice["normalized"]["section"],
            "trade_heading": notice["normalized"]["trade_heading"],
            "occupation_1843": notice["normalized"]["occupation"],
            "address_1843": notice["normalized"]["address"],
        })
    return row


def main():
    entries = json.load(open(ENTRIES, encoding="utf-8"))["claims"]
    # ONE MAN, TWO PRINTINGS (T-0987 stretch 7). Fold the business directory's
    # notices onto the roll entries they belong to FIRST, so that what is
    # bucketed below — and so what the ambiguity and contest tests count — is a
    # PERSON of this volume and not a printing of one.
    also, notice_notes = pt.fold(entries, fold)
    folded = {n["notice"] for n in notice_notes if n["attached"]}
    by_key, surnames = defaultdict(list), defaultdict(list)
    for c in entries:
        n = c["normalized"]
        if n["firm"] or not n["surname"] or c["id"] in folded:
            continue
        f = fold(n["surname"])
        if not f:
            continue
        surnames[f].append(c)
        i = initial(n["given"])
        if i:
            by_key[(f, i)].append(c)

    matches, ambiguous, refusals, forename_refusals = [], [], [], []
    middle_initial_refusals = []
    page_name_refusals = []
    wife_axis_refusals = []
    bucket_refusals = []
    ll_index = llb.buckets(llb.pool())
    people = residents()
    for r in people:
        f, i = fold(r["surname"]), initial(r["given"])
        hits = by_key.get((f, i), [])
        if not hits:
            if f in surnames:
                refusals.append({
                    "resident": r["name"], "person_id": r["person_id"],
                    "surname_in_1843": r["surname"],
                    "candidates": len(surnames[f]),
                    "rule": na.no_forename_refusal(r["name"], r["surname"], "Fergus 1843",
                                                   len(surnames[f])) if not i else
                            "The surname %r is in Fergus 1843 and no entry under it carries "
                            "the initial %r of %r. A surname-only agreement is a refusal."
                            % (r["surname"], i.upper(), r["name"]),
                })
            continue
        # T-1038. An initial the post office's returns also print in full under
        # the same surname stands for readings the corpus cannot separate, and
        # the mint pass seats one household per surname. Refused before the
        # forename rule, which can only weigh the reading that was seated.
        bucket = llb.refusal(r["name"], r["letter_list_only"], ll_index)
        if bucket:
            for h in hits:
                row = dict(bucket)
                row.update({"resident": r["name"], "person_id": r["person_id"],
                            "household_id": r["household_id"],
                            "grade_1835": r["grade"], "record_id": h["id"],
                            "entry_1843": row_of(h, also)})
                bucket_refusals.append(row)
            continue
        kept, refused = [], []
        for h in hits:
            note = na.refusal(r["given"], h["normalized"]["given"])
            (refused if note else kept).append((h, note))
        for h, note in refused:
            row = row_of(h, also)
            row.update(note)
            forename_refusals.append({
                "resident": r["name"], "person_id": r["person_id"],
                "grade_1835": r["grade"], "entry_1843": row,
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
            row = row_of(h, also)
            row.update(note)
            middle_initial_refusals.append({
                "resident": r["name"], "person_id": r["person_id"],
                "grade_1835": r["grade"], "entry_1843": row,
            })
        kept = [(h, None) for h in survivors]
        if not kept:
            continue
        # T-0987 stretch 14. THE WHOLE PRINTED NAME, WORD FOR WORD. The clause
        # above weighs only the initials BOTH readings set, so an entry that
        # STOPS EARLY is a silence and refuses nothing. This one asks whether the
        # page sets THIS NAME and no other — the same number of words, word for
        # word, and the closest fit of the candidates or none at all.
        # tools/named_by_the_page.py carries the rule and its refusals.
        page_declined = None
        if len(kept) > 1:
            # R6 first, on this axis too: Fergus 1843 prints `Brown, Rufus B.`
            # at 458 and `Brown, Mrs. Rufus B.` at 459, so the volume separates
            # the pair itself and each reading takes its own.
            survivors, honorific = nbp.honorific_must_agree(
                r["name"], [h for h, _ in kept],
                lambda h: h["normalized"]["printed_name"])
            for h, note in honorific:
                row = row_of(h, also)
                row.update({"clause": note["clause"], "rule": note["why"],
                            "honorific": note["honorific"]})
                wife_axis_refusals.append({
                    "resident": r["name"], "person_id": r["person_id"],
                    "grade_1835": r["grade"], "entry_1843": row})
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
                    row = row_of(h, also)
                    row.update({"clause": note["clause"], "rule": note["why"]})
                    page_name_refusals.append({
                        "resident": r["name"], "person_id": r["person_id"],
                        "grade_1835": r["grade"], "entry_1843": row})
                kept = [(winner, None)]
            else:
                page_declined = note["why"]
        rows = [row_of(h, also) for h, _ in kept]
        rec = {
            "resident": r["name"], "person_id": r["person_id"],
            "household_id": r["household_id"], "grade_1835": r["grade"],
            "occupation_1835": r["occupation"],
            "occupation_1835_confidence": r["occupation_confidence"],
            "lives_at_1835": r["lives_at"], "works_at_1835": r["works_at"],
            "rule": "Surname %r folds to the same string as the 1843 entry's, and the "
                    "given name of both begins %s." % (r["surname"], i.upper()),
            "entries_1843": rows,
        }
        if mi_declined:
            rec["further_initials_declined"] = mi_declined
        if page_declined:
            rec["whole_name_declined"] = page_declined
        carries = []
        # `none_recorded` IS NO OCCUPATION (T-0867). The residents layer writes
        # that sentinel where a person's trade was never attested, and the
        # truthiness test this line used to make read every one of them as
        # already traded — so this file reported `could_carry_occupation: 0`
        # beside Norris's fixed twin reporting 63, on a directory that prints a
        # trade against most of its names. The predicate is imported now, not
        # restated, because restating it is how two of the four got it wrong.
        if trade_recorded.absent(r["occupation"]) and any(
                x["occupation_1843"] for x in rows):
            carries.append("occupation")
        if not r["lives_at"] and any(x["address_1843"] for x in rows):
            carries.append("address")
        if any(x["death_note_1843"] for x in rows):
            carries.append("death_note")
        rec["could_carry"] = carries
        rec["carry_rule"] = ("Whatever is carried is carried as 1843 evidence with "
                             "describes_date 1843 on the note, never as an 1835 fact, and "
                             "the grade of the person does not move. The death note is "
                             "T-0574's, not this file's.")
        rec["resident_given_is_initial_only"] = all(
            len(t.strip(".,")) <= 1 for t in r["given"].split() if t.strip(".,").isalpha())
        (matches if len(rows) == 1 else ambiguous).append(rec)

    # ONE 1843 ENTRY, TWO 1835 PEOPLE is not a match, it is a collision, and at
    # most one of them is the man printed. Contested pairs come out of matches.
    claimed = defaultdict(list)
    for m in matches:
        claimed[m["entries_1843"][0]["claim"]].append(m)

    # T-0987 stretch 14. THE SAME CLAUSE ON THE OTHER AXIS. The collision below
    # asks which of two people of 1835 a printed line names and has only the
    # first initial that put them both there, so it answers "neither" and files
    # a contest. The page usually says: `Hogan, John Stephen Coates` sets three
    # words and the town's `John S. C. Hogan` sets those three, `Morrison,
    # Orsemus` is the tax list's Orsemus and not the poll list's Ordemus, and
    # `Wright, John Stephen` is the Prairie Farmer's John S. Wright and not the
    # town's bare John. R6 runs FIRST: a wife standing on her husband's own name
    # is not a rival to be weighed against him, she is not in the contest at all.
    given_1843 = {c["id"]: c["normalized"]["given"] for c in entries}
    given_1835 = {p["person_id"]: p["given"] for p in people}
    printed_name_1843 = {c["id"]: c["normalized"]["printed_name"] for c in entries}
    page_named, wife_refused = [], []
    for cid, rivals in sorted(claimed.items()):
        if len(rivals) < 2:
            continue
        printed = given_1843.get(cid, "")
        given_of = lambda m: given_1835.get(m["person_id"], "")
        kept_r, wives = nbp.honorific_must_agree(
            printed, rivals, lambda m: m["resident"])
        for m, note in wives:
            wife_refused.append({"resident": m["resident"], "person_id": m["person_id"],
                                 "entry_1843": m["entries_1843"][0], **note})
        if len(kept_r) > 1:
            winner, note = nbp.decide(
                printed, kept_r, given_of,
                reading_name=printed_name_1843.get(cid, ""),
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
                               "entry_1843": m["entries_1843"][0],
                               "named_instead": winner["resident"],
                               "clause": note["clause"], "rule": note["why"]})
            m["_not_named"] = True
        winner["named_by_the_page"] = {
            "over": [m["resident"] for m in rivals if m is not winner], **note}
        claimed[cid] = [winner]
    matches = [m for m in matches if not m.pop("_not_named", False)]

    contested = []
    for _, rivals in sorted(claimed.items()):
        if len(rivals) > 1:
            for m in rivals:
                m["contested_with"] = [x["resident"] for x in rivals if x is not m]
                m["rule"] += (" CONTESTED: %d residents of 1835 meet this one 1843 entry on "
                              "that rule, and at most one of them is the person printed. The "
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
        printed = rivals[0]["entries_1843"][0]["occupation_1843"]
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
                "entry_1843": rivals[0]["entries_1843"][0]["as_printed"],
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
             "printed": e["occupation_1843"]} for e in m["entries_1843"]])
        note = tiebreak.block(result, m["occupation_1835"], m["occupation_1835_confidence"])
        m["discriminator"] = note or {"kind": tiebreak.KIND, "named": None,
                                      "why": result["why"], "sides": result["sides"]}
        if note:
            named = next(e for e in m["entries_1843"] if e["claim"] == result["named"])
            discriminated.append({
                "tie": "ambiguous",
                "resident": m["resident"],
                "person_id": m["person_id"],
                "entries": len(m["entries_1843"]),
                "named": named["as_printed"],
                "claim": named["claim"],
                "discriminator": note,
            })

    # THE SURNAME ONE LETTER AWAY (T-0987 stretch 15). The join above reaches a
    # person of 1835 through the folded surname and then compares it EXACTLY,
    # while `name_agreement.agrees` allows a forename one letter of variation and
    # says why. So an entry the volume sets one letter off the town's spelling is
    # invisible to the join, and the resident lands in the initial-absent pool
    # with a refusal that reads `surname present`. Enumerated here and REFUSED
    # here — the module promotes nothing — because the volume sets both spellings
    # as separately populated surnames, and the printed volume's own OCR reads the
    # same letters on every one of the lines. See tools/surname_one_letter_away.py.
    one_letter = []
    reached = defaultdict(list)
    for rf in refusals:
        f = fold(rf["surname_in_1843"])
        i = initial(next(r for r in people
                         if r["person_id"] == rf["person_id"])["given"])
        if not i:
            continue
        for v in ola.variants(f, surnames):
            for c in surnames[v]:
                if initial(c["normalized"]["given"]) == i:
                    reached[c["id"]].append(rf["resident"])
    for rf in refusals:
        f = fold(rf["surname_in_1843"])
        i = initial(next(r for r in people
                         if r["person_id"] == rf["person_id"])["given"])
        if not i:
            continue
        for v in ola.variants(f, surnames):
            for c in surnames[v]:
                if initial(c["normalized"]["given"]) != i:
                    continue
                n = c["normalized"]
                row = ola.refusal(rf["resident"], rf["surname_in_1843"],
                                  n["printed_name"], n["surname"],
                                  len(surnames[f]), len(surnames[v]), "Fergus 1843",
                                  contested_by=len(set(reached[c["id"]])))
                row["person_id"] = rf["person_id"]
                row["claim"] = c["id"]
                row["as_printed"] = n["as_printed"]
                hand = ola.SECOND_HAND_BY_CLAIM.get(c["id"])
                row["second_hand"] = {
                    "source_id": ola.SECOND_HAND_SOURCE,
                    "text": ola.SECOND_HAND_TEXT,
                    "line": hand["line"], "reads": hand["reads"],
                } if hand else None
                one_letter.append(row)

    doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/crosswalk_fergus_1843.py. Fergus's 1843 directory against "
                "the 1835 residents layer. A PROPOSAL: it changes no resident record, and "
                "under the ratified ladder an 1843 listing alone never makes an 1835 "
                "resident. T-0569 is the pass that spends it; T-0574 is the pass that "
                "spends the death notes.",
        "generated_by": "tools/crosswalk_fergus_1843.py",
        "source_id": "fergus_chicago_directory_1843",
        "rule": __doc__.split("The rule, written out")[1].split("WHAT THIS DIRECTORY")[0].strip(),
        "discriminator_rule": tiebreak.__doc__.split("THE RULING")[1].split(
            "Run it directly")[0].strip(),
        "refused_discriminators": tiebreak.REFUSED_DISCRIMINATORS,
        "whole_name_rule": nbp.__doc__.split("THE RULING")[1].split(
            "WHAT THE WORD-COUNT TEST IS FOR")[0].strip(),
        "wife_rule": nbp.__doc__.split("A WIFE IS NOT HER HUSBAND")[1].split(
            "The honorific must stand")[0].strip(),
        "counts": {
            "residents_considered": len(people),
            "matched_one_1843_entry": len(matches),
            "matched_more_than_one_ambiguous": len(ambiguous),
            "one_1843_entry_contested_by_two_residents": len(contested),
            "surname_present_initial_absent_refused": len(refusals),
            "of_those_an_entry_one_letter_off_the_surname": len(
                {o["person_id"] for o in one_letter}),
            "entries_one_letter_off_a_refused_surname": len(
                {o["claim"] for o in one_letter}),
            "of_those_overturned": 0,
            "letter_list_bucket_refused": len(bucket_refusals),
            "residents_that_refusal_reaches": len({b["person_id"] for b in bucket_refusals}),
            "further_initial_disagreed_refused": len(middle_initial_refusals),
            "residents_that_further_initial_refusal_reaches": len(
                {f["person_id"] for f in middle_initial_refusals}),
            "initial_agreed_forenames_disagreed_refused": len(forename_refusals),
            "of_those_a_garbled_printed_forename": sum(
                1 for f in forename_refusals if f["entry_1843"]["garbled_reading"]),
            "residents_left_with_no_1843_entry_by_that_refusal": len(
                {f["person_id"] for f in forename_refusals}
                - {m["person_id"] for m in matches + ambiguous + contested}),
            "entries_the_whole_name_refused": len(page_name_refusals),
            "residents_that_whole_name_refusal_reaches": len(
                {f["person_id"] for f in page_name_refusals}),
            "contests_the_page_named": len(
                {n["entry_1843"]["claim"] for n in page_named}),
            "residents_not_named_by_a_contested_entry": len(page_named),
            "residents_held_off_a_husbands_entry": len(wife_refused),
            "entries_a_female_honorific_refused": len(wife_axis_refusals),
            "ties_narrowed_by_a_trade": len(discriminated),
            "of_those_contested": sum(1 for d in discriminated if d["tie"] == "contested"),
            "of_those_ambiguous": sum(1 for d in discriminated if d["tie"] == "ambiguous"),
            "could_carry_occupation": sum(1 for m in matches if "occupation" in m["could_carry"]),
            "could_carry_address": sum(1 for m in matches if "address" in m["could_carry"]),
            "could_carry_death_note": sum(1 for m in matches
                                          if "death_note" in m["could_carry"]),
            "business_directory_notices_with_a_surname": len(notice_notes),
            "notices_folded_onto_their_own_roll_entry": len(folded),
            "notices_standing_as_their_own_candidate": len(notice_notes) - len(folded),
            "roll_entries_carrying_a_notice": len(also),
        },
        "printed_twice": {
            "rule": pt.__doc__.split("THE RULE")[1].split("WHAT THIS IS NOT")[0].strip(),
            "what_this_is_not": pt.__doc__.split("WHAT THIS IS NOT.")[1].strip(),
            "notes": sorted(notice_notes, key=lambda n: n["notice"]),
        },
        "matches": sorted(matches, key=lambda m: m["resident"]),
        "discriminated": sorted(discriminated, key=lambda d: (d["tie"], d["claim"])),
        "contested": sorted(contested, key=lambda m: m["resident"]),
        "ambiguous": sorted(ambiguous, key=lambda m: m["resident"]),
        "refusals": sorted(refusals, key=lambda m: m["resident"]),
        "surname_one_letter_away": {
            "rule": ola.__doc__.split("THE RULING, and it refuses all sixteen.")[1]
                    .split("WHAT IT IS A SYMPTOM OF")[0].strip(),
            "what_this_is_not": ola.__doc__.split("WHAT THIS IS NOT.")[1].strip(),
            "second_hand": ola.SECOND_HAND_SOURCE,
            "refusals": sorted(one_letter, key=lambda m: (m["resident"], m["claim"])),
        },
        "letter_list_bucket_refusals": sorted(
            bucket_refusals, key=lambda m: (m["resident"], m["entry_1843"]["claim"])),
        "middle_initial_refusals": sorted(middle_initial_refusals,
                                          key=lambda x: x["resident"]),
        "forename_refusals": sorted(forename_refusals,
                                    key=lambda m: (m["resident"], m["entry_1843"]["claim"])),
        "whole_name_refusals": sorted(
            page_name_refusals, key=lambda m: (m["resident"], m["entry_1843"]["claim"])),
        "not_named_by_the_page": sorted(
            page_named, key=lambda m: (m["entry_1843"]["claim"], m["resident"])),
        "held_off_a_husbands_entry": sorted(
            wife_refused, key=lambda m: (m["entry_1843"]["claim"], m["resident"])),
        "female_honorific_refusals": sorted(
            wife_axis_refusals, key=lambda m: (m["resident"], m["entry_1843"]["claim"])),
    }
    if "--check" in sys.argv:
        if json.load(open(OUT, encoding="utf-8")) != doc:
            print("fergus crosswalk: committed file does not match — regenerate",
                  file=sys.stderr)
            return 1
        print("fergus crosswalk: matches the committed file")
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(doc["counts"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
