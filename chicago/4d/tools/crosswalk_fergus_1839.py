#!/usr/bin/env python3
"""Fergus' 1839 directory against the four pools of 1835 names (T-0506).

The ONLY place a name in the 1839 directory is allowed to touch a person standing
in the scene of 1 July 1835. It touches them as CORROBORATION and as CANDIDATE
ENRICHMENT, never as an 1835 fact: under the ratified grading ladder a later
listing alone never makes an 1835 resident, and NOTHING HERE MINTS OR REGRADES
ANYBODY. The file this writes is a proposal for the passes that spend it —
T-0513 consolidates it, T-0514 and T-0515 are the ones allowed to write people.

The rule, written out so it reads back without the code:
  SURNAME must match after both are folded (case, punctuation and the
  transcriber's usual confusions removed), AND the first initial of the given
  name must match. A surname-only agreement is a REFUSAL, however good it looks —
  this directory lists forty-one Smiths. Where one 1835 name meets more than one
  1839 entry on that rule the match is AMBIGUOUS and is filed as such, not
  resolved; where two 1835 people meet one 1839 entry it is CONTESTED and no match
  is made.

FOUR POOLS, because the ticket asks for four and they are not the same object.
The residents layer is the town as it stands, and a match there is enrichment of a
record that already exists. The voter, poll and tax entries (T-0493), the
letter-list and newspaper persons, and the 1840 heads are LISTS OF NAMES, and a
match there is one more line of evidence about a name the project has not yet
made into a person. They are counted separately and never mixed.

WHAT THIS DIRECTORY WILL NOT GIVE, however well a name matches: an address. Fergus
prints on page 3 that no street but Lake carried numbers in 1839 and that "the
numbers now given are those of the present day" — 1876's. The street NAME crosses;
the number does not, and `address_is_street_only` says which rows are which.

T-0670'S FORENAME RULE, AND WHY IT TOO READS ONE POOL OF THE FOUR. Where BOTH
readings print a full forename and the two disagree, the match is REFUSED and the
refusal is filed — tools/name_agreement.py is the rule, imported rather than
restated. It is applied to the RESIDENTS pool, where a false match writes a trade
onto a person's card, and not to the three lists of names, which mint nobody here
and are consumed by spend passes of their own whose ties are theirs to re-derive;
`forename_rule_scope` below says so on the file. Running it matters most for the
ties: an 1839 line whose own forename contradicts the 1835 name was standing in
the tie pool, and a discriminator weighing that line can name it.

THE TIE DISCRIMINATOR (T-0696), AND WHY IT READS ONE POOL OF THE FOUR. A trade may
NARROW a tie and never make it a match; a premises and a year may not. The rule is
tools/tiebreak.py and it is run here over the RESIDENTS pool only — not because
that pool is the interesting one, but because a discriminator needs a trade on the
1835 side of the tie and the residents layer is the only one of the four pools that
holds one. The voter and poll lists, the letter-list persons and the 1840 heads are
lists of NAMES: there is nothing on their side to narrow on, so their ties stand by
the construction of the pool rather than by a ruling, and `discriminator_scope`
below says so on the file.
"""
import json, os, re, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trade_recorded     # "does the layer hold a trade?" (T-0867), imported not restated
import tiebreak            # the tie discriminator (T-0696), likewise
import name_agreement as na  # the forename rule (T-0670), likewise
import letter_list_bucket as llb  # the letter-list bucket refusal (T-1038)
import named_by_the_page as nbp  # the whole printed name (T-0987 stretch 14), likewise

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRIES = os.path.join(ROOT, "data/research/directories/claims/fergus_1839_directory_entries.json")
HH = os.path.join(ROOT, "data/residents/households")
VOTERS = os.path.join(ROOT, "data/research/civic/voter_crosswalk.json")
GAZETTEER = os.path.join(ROOT, "data/research/newspapers/gazetteer.json")
HEADS_1840 = os.path.join(ROOT, "data/research/census_1840/resident_crosswalk.json")
OUT = os.path.join(ROOT, "data/research/directories/fergus_1839_crosswalk_1835.json")

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
        if tok.strip(".,'\"").lower() in TITLES:
            continue
        for ch in tok:
            if ch.isalpha():
                return ch.lower()
    return ""


def split_name(name: str):
    """A pool name as surname + given. 'W. H. Adams' and 'Adams, W. H.' both work.

    A name that is a RANK and a surname and NOTHING ELSE — `Major Handy`,
    `Judge Silver`, `Jun Marknoble` — returns an EMPTY given (T-0987 stretch 8).
    It used to return the rank AS the given, so the pool keyed Major Handy on the
    M of Major and met `Handy, Major` on it: a match made on a rank on both sides
    and not on a man. It must not swing to returning nothing at all either, which
    is what the old `len(parts) < 2` would now do — a row dropped here is a row no
    refusal is ever filed for, and clause 1 of this programme asks that nothing be
    left silent. So the surname is kept and the given is empty, and the caller
    files the refusal that names the missing forename.
    """
    name = (name or "").strip()
    if "," in name:
        surname, given = name.split(",", 1)
        return surname.strip(" ."), given.strip(" .")
    parts = [p for p in name.replace(".", ". ").split() if p]
    kept = [p for p in parts if p.strip(".,").lower() not in TITLES]
    if len(kept) == 1 and len(parts) > 1:
        return kept[0].strip(" ."), ""
    if len(kept) < 2:
        return "", ""
    return kept[-1].strip(" ."), " ".join(kept[:-1])


def residents():
    """Every person the 1835 layer holds, with the household they belong to."""
    out = []
    for fn in sorted(os.listdir(HH)):
        if not fn.endswith(".json"):
            continue
        doc = json.load(open(os.path.join(HH, fn), encoding="utf-8"))
        for p in doc.get("persons") or []:
            name = (p.get("name") or "").strip()
            if not name or (p.get("id") or "").endswith("_household"):
                continue
            surname, given = split_name(name)
            if not surname:
                continue
            out.append({
                "name": name, "surname": surname, "given": given,
                "person_id": p.get("id"), "household_id": doc.get("id"),
                "letter_list_only": bool(p.get("letter_list_only")),
                "grade": p.get("grade"),
                "occupation": ((p.get("occupation") or {}).get("value")),
                "occupation_confidence": ((p.get("occupation") or {}).get("confidence")),
                "lives_at": ((doc.get("lives_at") or {}).get("value")),
            })
    return out


def list_pool(path, key, name_of, label_of):
    doc = json.load(open(path, encoding="utf-8"))
    out = []
    for row in doc.get(key) or []:
        name = name_of(row)
        surname, given = split_name(name)
        if not surname:
            continue
        out.append({"name": name, "surname": surname, "given": given,
                    "label": label_of(row)})
    return out


def row_of(entry):
    n = entry["normalized"]
    return {
        "claim": entry["id"],
        "as_printed": n["as_printed"],
        "printed_page": entry["locator"]["printed_page"],
        "occupation_1839": n["occupation"],
        "address_1839": n["address"],
        "streets_1839": n["streets"],
        # Fergus's own warning, applied per row: a number off Lake street is 1876's.
        "address_is_street_only": bool(n["number_is_1876"]),
    }


def index(entries):
    by_key, surnames = defaultdict(list), defaultdict(list)
    for c in entries:
        n = c["normalized"]
        if n["firm"] or not n["surname"]:
            continue
        f = fold(n["surname"])
        if not f:
            continue
        surnames[f].append(c)
        i = initial(n["given"])
        if i:
            by_key[(f, i)].append(c)
    return by_key, surnames


def match_pool(pool, by_key, surnames, extra=None, forename_refusals=None,
               bucket_refusals=None, middle_initial_refusals=None,
               page_name_refusals=None, wife_axis_refusals=None):
    """One pool against the index. Returns (matched, ambiguous, refused).

    T-0670's forename rule is applied where the CALLER hands in a list to file
    its refusals into, and not otherwise — see `forename_rule_scope` on the
    generated file for why only one of the four pools asks for it. T-1038's
    letter-list bucket refusal is handed in the same way and for the same
    reason: it asks whether a POOL ROW is a card the mint pass seated over
    another reading, and only the residents pool holds cards.
    """
    ll_index = llb.buckets(llb.pool())
    matched, ambiguous, refused = [], [], []
    for r in pool:
        page_declined = None
        f, i = fold(r["surname"]), initial(r["given"])
        hits = by_key.get((f, i), []) if i else []
        if not hits:
            if f in surnames:
                refused.append({
                    "name": r["name"],
                    "candidates_under_that_surname": len(surnames[f]),
                    "rule": na.no_forename_refusal(r["name"], r["surname"], "Fergus 1839", len(surnames[f])) if not i else
                            "The surname %r is in Fergus 1839 and no entry under it carries "
                            "the initial %r of %r. A surname-only agreement is a refusal."
                            % (r["surname"], i.upper(), r["name"]),
                })
            continue
        # T-1038. The card prints an INITIAL that the post office's returns also
        # print in full under the same surname, and the mint pass seats one
        # household per surname — so the card stands for readings the corpus
        # cannot separate. This file showed the contest before the rule existed:
        # in its own letter-list pool below, f1839_e1338 matches BOTH `S.
        # Sherwood` and `Stephen Sherwood`, and only the residents pool could
        # not see it, because only one of the two was ever minted.
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
        # T-0670. BOTH READINGS PRINT A FULL FORENAME AND THE TWO DISAGREE: refused,
        # and the refusal is FILED, never dropped. An initial standing against a full
        # name is untouched — that is the case the initial rule exists to serve.
        if forename_refusals is not None:
            kept = []
            for h in hits:
                note = na.refusal(r["given"], h["normalized"]["given"])
                if note:
                    row = row_of(h)
                    row.update(note)
                    rec = {"name": r["name"], "entry_1839": row}
                    if extra:
                        rec.update(extra(r))
                    forename_refusals.append(rec)
                else:
                    kept.append(h)
            hits = kept
            if not hits:
                continue
            # T-0987 stretch 9. THE FURTHER INITIALS, scoped exactly as T-0670's
            # forename rule is: this pool and no other. The bucket matched the
            # FIRST initial and nothing had ever compared a middle one both
            # readings print. The helper declines to fire where firing would
            # promote a SILENT survivor over a refused rival that spoke.
            if middle_initial_refusals is None:
                middle_initial_refusals = []
            survivors, mi_refused, mi_declined = na.narrow_by_further_initials(
                r["given"], hits, lambda h: h["normalized"]["given"])
            for h, note in mi_refused:
                row = row_of(h)
                row.update(note)
                mrec = {"name": r["name"], "entry_1839": row}
                if extra:
                    mrec.update(extra(r))
                middle_initial_refusals.append(mrec)
            hits = survivors
            if not hits:
                continue
            # T-0987 stretch 14. THE WHOLE PRINTED NAME, WORD FOR WORD. The clause
            # above weighs only the initials BOTH readings set, so an entry that
            # STOPS EARLY is a silence and refuses nothing: `H. B. Clarke` stood
            # against `Clarke, Dr. Henry` and `Clarke, Henry B.` with the tie
            # unbroken, because the first prints no second word to disagree with.
            # This one asks the other question — does the page set THIS NAME and no
            # other, same number of words and word for word — and where exactly one
            # entry does, that entry is the match and the rest are refused with the
            # clause. tools/named_by_the_page.py carries the rule.
            if page_name_refusals is not None and len(hits) > 1:
                # R6 first, on this axis too: where the volume prints the pair
                # itself, each reading takes its own and neither is a rival of
                # the other's entry. Where it does not, nothing is refused.
                hits, honorific = nbp.honorific_must_agree(
                    r["name"], hits, lambda h: h["normalized"]["printed_name"])
                for h, note in honorific:
                    row = row_of(h)
                    row.update({"clause": note["clause"], "rule": note["why"],
                                "honorific": note["honorific"]})
                    hrec = {"name": r["name"], "entry_1839": row}
                    if extra:
                        hrec.update(extra(r))
                    wife_axis_refusals.append(hrec)
            if page_name_refusals is not None and len(hits) > 1:
                winner, note = nbp.decide(
                    r["given"], hits, lambda h: h["normalized"]["given"],
                    reading_name=r["name"],
                    name_of=lambda h: h["normalized"]["printed_name"])
                if winner is not None:
                    for h in hits:
                        if h is winner:
                            continue
                        row = row_of(h)
                        row.update({"clause": note["clause"], "rule": note["why"]})
                        prec = {"name": r["name"], "entry_1839": row}
                        if extra:
                            prec.update(extra(r))
                        page_name_refusals.append(prec)
                    hits = [winner]
                else:
                    page_declined = note["why"]
        rec = {"name": r["name"],
               "rule": "Surname %r folds to the same string as the 1839 entry's, and the "
                       "given name of both begins %s." % (r["surname"], i.upper()),
               "entries_1839": [row_of(h) for h in hits]}
        if forename_refusals is not None and mi_declined:
            rec["further_initials_declined"] = mi_declined
        if page_declined:
            rec["whole_name_declined"] = page_declined
        if extra:
            rec.update(extra(r))
        (matched if len(hits) == 1 else ambiguous).append(rec)
    return matched, ambiguous, refused


def main():
    entries = json.load(open(ENTRIES, encoding="utf-8"))["claims"]
    by_key, surnames = index(entries)

    people = residents()
    res_forename_refused = []
    res_bucket_refused = []
    res_middle_initial_refused = []
    res_page_name_refused = []
    res_wife_axis_refused = []
    res_matched, res_ambiguous, res_refused = match_pool(
        people, by_key, surnames,
        forename_refusals=res_forename_refused,
        middle_initial_refusals=res_middle_initial_refused,
        bucket_refusals=res_bucket_refused,
        page_name_refusals=res_page_name_refused,
        wife_axis_refusals=res_wife_axis_refused,
        extra=lambda r: {"person_id": r["person_id"], "household_id": r["household_id"],
                         "grade_1835": r["grade"], "occupation_1835": r["occupation"],
                         "occupation_1835_confidence": r["occupation_confidence"],
                         "lives_at_1835": r["lives_at"]})
    # What a match COULD carry, if the pass that spends it decides to. The residents
    # layer writes `none_recorded` where it holds no trade, and 738 of its 849 people
    # carry that — an absent trade is the field's most common value, not a null.
    for m in res_matched:
        carries = []
        # This file had the predicate right from the start and two of its four
        # siblings did not, so it is stated once now and imported (T-0867).
        if trade_recorded.absent(m["occupation_1835"]) and any(
                x["occupation_1839"] for x in m["entries_1839"]):
            carries.append("occupation")
        if any(x["streets_1839"] for x in m["entries_1839"]):
            carries.append("street_1839")
        m["could_carry"] = carries
        m["carry_rule"] = ("Whatever is carried is carried as 1839 evidence with "
                           "describes_date 1839 on the note, never as an 1835 fact, and the "
                           "grade of the person does not move. The street NAME may cross; "
                           "the street NUMBER may not — see address_is_street_only.")

    # ONE 1839 ENTRY, TWO 1835 PEOPLE is a collision, not a match.
    claimed = defaultdict(list)
    for m in res_matched:
        claimed[m["entries_1839"][0]["claim"]].append(m)

    # T-0987 stretch 14. THE SAME CLAUSE ON THE OTHER AXIS, and nothing in this
    # chain had ever run it here: the collision below asks which of two people of
    # 1835 a printed line names and then answers "neither", because the only rule
    # it has is the first initial that put them both there. The page usually says.
    # `King, Byram` is the town's Byram King and not its Byra; `Hogan, John S. C.`
    # sets three words and the town's John S. C. Hogan sets those three; `Morrison,
    # Orsemus` is the tax list's Orsemus and not the poll list's Ordemus. Exactly
    # one fit or nothing happens, so `Clark, John` still chooses between no John A.
    # and no John K. R6 runs FIRST, because a wife standing on her husband's own
    # name is not a rival to be weighed against him — she is not in the contest.
    given_1839 = {c["id"]: c["normalized"]["given"] for c in entries}
    printed_name_1839 = {c["id"]: c["normalized"]["printed_name"] for c in entries}
    page_named, wife_refused = [], []
    for cid, rivals in sorted(claimed.items()):
        if len(rivals) < 2:
            continue
        printed = given_1839.get(cid, "")
        kept, wives = nbp.honorific_must_agree(printed, rivals, lambda m: m["name"])
        for m, note in wives:
            wife_refused.append({"name": m["name"], "person_id": m["person_id"],
                                 "household_id": m["household_id"],
                                 "entry_1839": m["entries_1839"][0], **note})
        if len(kept) > 1:
            winner, note = nbp.decide(
                printed, kept, lambda m: split_name(m["name"])[1],
                reading_name=printed_name_1839.get(cid, ""),
                name_of=lambda m: m["name"], one_body=False)
        elif kept:
            winner, note = kept[0], {"clause": nbp.WIFE_CLAUSE, "named": None,
                                     "why": "the only reading left after R6"}
        else:
            winner, note = None, None
        losers = [m for m in rivals if m is not winner]
        if winner is None:
            continue
        for m in losers:
            page_named.append({"name": m["name"], "person_id": m["person_id"],
                               "household_id": m["household_id"],
                               "entry_1839": m["entries_1839"][0],
                               "named_instead": winner["name"],
                               "clause": note["clause"], "rule": note["why"]})
        winner["named_by_the_page"] = {"over": [m["name"] for m in losers], **note}
        claimed[cid] = [winner]
        for m in losers:
            m["_not_named"] = True
    res_matched = [m for m in res_matched if not m.pop("_not_named", False)]

    contested = []
    for _, rivals in sorted(claimed.items()):
        if len(rivals) > 1:
            for m in rivals:
                m["contested_with"] = [x["name"] for x in rivals if x is not m]
                m["rule"] += (" CONTESTED: %d residents of 1835 meet this one 1839 entry on "
                              "that rule, and at most one of them is the person printed. The "
                              "match is not made." % len(rivals))
                contested.append(m)
    res_matched = [m for m in res_matched if "contested_with" not in m]

    # T-0696. THE TIE DISCRIMINATOR, over the residents pool — the only one of the four
    # with a trade on the 1835 side. A trade may NARROW a tie and never make it a match:
    # the narrowing is filed below in `residents.discriminated`, the losing side is filed
    # as SILENT rather than contradicted, nothing moves into `matches` and no grade moves
    # in either direction. A premises and a year are REFUSED discriminators, and
    # tools/tiebreak.py carries both refusals with their reasons. EVERY tie gets a ruling:
    # where the trade names two sides or none the tie stands, and `discriminator` says so
    # on the record rather than leaving the row silent.
    discriminated = []
    for _cid, rivals in sorted(claimed.items()):
        if len(rivals) < 2:
            continue
        printed = rivals[0]["entries_1839"][0]["occupation_1839"]
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
                "entry_1839": rivals[0]["entries_1839"][0]["as_printed"],
                "claim": _cid,
                "printed_page": rivals[0]["entries_1839"][0]["printed_page"],
                "rivals": [m["name"] for m in rivals],
                "named": winner["name"],
                "person_id": winner["person_id"],
                "household_id": winner["household_id"],
                "discriminator": note,
            })

    # The other shape of the same tie: one person of 1835 meeting several printed lines.
    # The sides are the printed entries and the trade is the one the resident carries, so
    # the same rule reads it without restatement.
    for m in res_ambiguous:
        result = tiebreak.narrow([
            {"key": e["claim"], "occupation_1835": m["occupation_1835"],
             "printed": e["occupation_1839"]} for e in m["entries_1839"]])
        note = tiebreak.block(result, m["occupation_1835"], m["occupation_1835_confidence"])
        m["discriminator"] = note or {"kind": tiebreak.KIND, "named": None,
                                      "why": result["why"], "sides": result["sides"]}
        if note:
            named = next(e for e in m["entries_1839"] if e["claim"] == result["named"])
            discriminated.append({
                "tie": "ambiguous",
                "resident": m["name"],
                "person_id": m["person_id"],
                "household_id": m["household_id"],
                "entries": len(m["entries_1839"]),
                "named": named["as_printed"],
                "claim": named["claim"],
                "printed_page": named["printed_page"],
                "discriminator": note,
            })

    voters = list_pool(VOTERS, "entries", lambda r: r.get("normalized") or r.get("as_read"),
                       lambda r: r.get("list"))
    v_matched, v_ambiguous, v_refused = match_pool(voters, by_key, surnames)
    letters = list_pool(GAZETTEER, "persons", lambda r: r.get("name"),
                        lambda r: r.get("id"))
    l_matched, l_ambiguous, l_refused = match_pool(letters, by_key, surnames)
    heads = list_pool(HEADS_1840, "heads", lambda r: r.get("normalized") or r.get("as_read"),
                      lambda r: r.get("familysearch_id"))
    h_matched, h_ambiguous, h_refused = match_pool(heads, by_key, surnames)

    # THE NARROWING MAY NOT NAME ONE PRINTED LINE FOR TWO PEOPLE OF 1835. Two
    # ambiguous residents narrowed onto the same entry is a CONTESTED group wearing
    # another shape, and contested is the one thing the matching rule refuses by
    # construction — so both narrowings come out and the ties stand. Before T-0670
    # was applied above this fired on Fergus's three Taylors: `Taylor, Augustin
    # Deodat, carpenter and builder` was named for BOTH Anson H. Taylor and
    # Augustine Deodat Taylor, each an 1835 carpenter. It is kept as a gate rather
    # than retired with the cause, because it is the invariant and not the symptom.
    by_claim = defaultdict(list)
    for d in discriminated:
        if d["tie"] == "ambiguous":
            by_claim[d["claim"]].append(d)
    collisions = []
    for cid, rows in sorted(by_claim.items()):
        if len(rows) < 2:
            continue
        collisions.append({
            "claim": cid,
            "entry_1839": rows[0]["named"],
            "residents": [r["resident"] for r in rows],
            "rule": "The trade narrowed this one printed line onto %d people of 1835, which "
                    "is a contested group in another shape. Both narrowings are withdrawn "
                    "and the ties stand: at most one of them is the person printed, and the "
                    "trade cannot say which." % len(rows),
        })
        for r in rows:
            for m in res_ambiguous:
                if m["person_id"] == r["person_id"]:
                    m["discriminator"] = {
                        "kind": tiebreak.KIND, "named": None,
                        "why": "the trade named one side, and that side was named for "
                               "another person of 1835 as well — withdrawn",
                        "sides": r["discriminator"]["sides"],
                    }
    withdrawn = {id(r) for rows in by_claim.values() if len(rows) > 1 for r in rows}
    discriminated = [d for d in discriminated if id(d) not in withdrawn]

    doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/crosswalk_fergus_1839.py. Fergus' 1839 directory against "
                "the 1835 residents layer, the voter and poll lists, the letter-list and "
                "newspaper persons, and the 1840 heads. A PROPOSAL: it changes no resident "
                "record, mints nobody and regrades nobody. Under the ratified ladder an 1839 "
                "listing alone never makes an 1835 resident.",
        "generated_by": "tools/crosswalk_fergus_1839.py",
        "source_id": "fergus_chicago_directory_1839",
        "ticket": "T-0506",
        "rule": __doc__.split("The rule, written out")[1].split("FOUR POOLS")[0].strip(),
        "scene_relation": "1839 is four years after the scene date of 1 July 1835, and this "
                          "volume is Fergus's 1876 completion of a list first set up from "
                          "memory in 1839. Evidence about 1839, recalled in 1876.",
        "mints_or_regrades": False,
        "discriminator_rule": tiebreak.__doc__.split("THE RULING")[1].split(
            "Run it directly")[0].strip(),
        "refused_discriminators": tiebreak.REFUSED_DISCRIMINATORS,
        "whole_name_rule": nbp.__doc__.split("THE RULING")[1].split(
            "WHAT THE WORD-COUNT TEST IS FOR")[0].strip(),
        "wife_rule": nbp.__doc__.split("A WIFE IS NOT HER HUSBAND")[1].split(
            "The honorific must stand")[0].strip(),
        "forename_rule": na.__doc__.split("The tightening, written out")[1].split(
            "This module is the rule")[0].strip(),
        "forename_rule_scope": "T-0670's forename rule is applied to the residents pool "
                               "only. That is where a false match writes a trade or an "
                               "address onto the card of a person this town stands up; the "
                               "voter and poll lists, the letter-list persons and the 1840 "
                               "heads are lists of names this file mints nobody from, and "
                               "their ties belong to the spend passes that consume them "
                               "(T-0513, T-0514, T-0515) rather than to this stretch. Their "
                               "counts below are therefore unmoved and are NOT to be read as "
                               "having passed the rule.",
        "discriminator_scope": "The T-0696 discriminator is run over the residents pool "
                               "only. It needs a trade on the 1835 side of the tie, and the "
                               "residents layer is the only one of the four pools that holds "
                               "one — the voter and poll lists, the letter-list persons and "
                               "the 1840 heads are lists of names. Their ties stand by the "
                               "construction of the pool, not by a ruling that weighed "
                               "anything, and this file does not pretend otherwise.",
        "address_rule": "An address number in this directory is an 1876 number everywhere "
                        "except Lake street, on the compiler's own statement (printed page 3). "
                        "Only the street name crosses; address_is_street_only marks every row "
                        "where the printed number must be dropped.",
        "inputs": [
            {"what": "Fergus 1839 personal entries indexed", "n": sum(len(v) for v in surnames.values())},
            {"what": "residents layer, persons", "path": "data/residents/households/", "n": len(people)},
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
            "voters_matched_one_entry": len(v_matched),
            "voters_ambiguous": len(v_ambiguous),
            "voters_surname_only_refused": len(v_refused),
            "letter_list_matched_one_entry": len(l_matched),
            "letter_list_ambiguous": len(l_ambiguous),
            "letter_list_surname_only_refused": len(l_refused),
            "heads_1840_matched_one_entry": len(h_matched),
            "heads_1840_ambiguous": len(h_ambiguous),
            "heads_1840_surname_only_refused": len(h_refused),
            "residents_further_initial_disagreed_refused": len(
                res_middle_initial_refused),
            "residents_that_further_initial_refusal_reaches": len(
                {f["person_id"] for f in res_middle_initial_refused}),
            "residents_initial_agreed_forenames_disagreed_refused": len(
                res_forename_refused),
            "of_those_a_garbled_printed_forename": sum(
                1 for f in res_forename_refused if f["entry_1839"]["garbled_reading"]),
            "residents_left_with_no_entry_by_that_refusal": len(
                {f["person_id"] for f in res_forename_refused}
                - {m["person_id"] for m in res_matched + res_ambiguous + contested}),
            "residents_letter_list_bucket_refused": len(res_bucket_refused),
            "residents_that_refusal_reaches": len({b["person_id"] for b in res_bucket_refused}),
            "residents_entries_the_whole_name_refused": len(res_page_name_refused),
            "residents_that_whole_name_refusal_reaches": len(
                {f["person_id"] for f in res_page_name_refused}),
            "residents_contests_the_page_named": len(
                {n["entry_1839"]["claim"] for n in page_named}),
            "residents_not_named_by_a_contested_entry": len(page_named),
            "residents_held_off_a_husbands_entry": len(wife_refused),
            "entries_a_female_honorific_refused": len(res_wife_axis_refused),
            "residents_ties_narrowed_by_a_trade": len(discriminated),
            "of_those_contested": sum(1 for d in discriminated if d["tie"] == "contested"),
            "of_those_ambiguous": sum(1 for d in discriminated if d["tie"] == "ambiguous"),
            "residents_narrowings_withdrawn_as_a_collision": len(collisions),
            "residents_ties_left_standing": len(contested) + len(res_ambiguous) - sum(
                len(d.get("rivals", [])) if d["tie"] == "contested" else 1
                for d in discriminated),
            "residents_could_carry_occupation": sum(
                1 for m in res_matched if "occupation" in m["could_carry"]),
            "residents_could_carry_street": sum(
                1 for m in res_matched if "street_1839" in m["could_carry"]),
        },
        "residents": {
            "matches": sorted(res_matched, key=lambda m: m["name"]),
            "discriminated": sorted(discriminated, key=lambda d: (d["tie"], d["claim"])),
            "contested": sorted(contested, key=lambda m: m["name"]),
            "ambiguous": sorted(res_ambiguous, key=lambda m: m["name"]),
            "refusals": sorted(res_refused, key=lambda m: m["name"]),
            "middle_initial_refusals": sorted(
                res_middle_initial_refused,
                key=lambda m: (m["name"], m["entry_1839"]["claim"])),
            "forename_refusals": sorted(res_forename_refused,
                                        key=lambda m: (m["name"], m["entry_1839"]["claim"])),
            "letter_list_bucket_refusals": sorted(
                res_bucket_refused, key=lambda m: (m["name"], m["entry_1839"]["claim"])),
            "narrowings_withdrawn_as_a_collision": collisions,
            "whole_name_refusals": sorted(
                res_page_name_refused,
                key=lambda m: (m["name"], m["entry_1839"]["claim"])),
            "not_named_by_the_page": sorted(
                page_named, key=lambda m: (m["entry_1839"]["claim"], m["name"])),
            "held_off_a_husbands_entry": sorted(
                wife_refused, key=lambda m: (m["entry_1839"]["claim"], m["name"])),
            "female_honorific_refusals": sorted(
                res_wife_axis_refused,
                key=lambda m: (m["name"], m["entry_1839"]["claim"])),
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
            print("fergus 1839 crosswalk: the committed file does not match — regenerate",
                  file=sys.stderr)
            return 1
        print("fergus 1839 crosswalk: matches the committed file")
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(doc["counts"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
