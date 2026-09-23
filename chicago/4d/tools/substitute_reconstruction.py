#!/usr/bin/env python3
"""What a new attested record would retire, before anything is retired (T-1441, of T-1190).

    python3 tools/substitute_reconstruction.py --dry-run <candidate.json>
    python3 tools/substitute_reconstruction.py --dry-run --fixture   the shipped example
    python3 tools/substitute_reconstruction.py --report   the substitutable population
    python3 tools/substitute_reconstruction.py --check    the liberty shares, re-counted
    python3 tools/substitute_reconstruction.py --self-test

THE PROMISE THIS TOOL MAKES GOOD.

The owner, on why a reconstructed record is marked as one: *"so if we get new research we
can replace the reconstructed person or business with an inferred or attested one later."*
Every reconstructed record already says on its face what would retire it — `replaceable_by`
in prose, `withdrawn_if` in the reconstruction block. Nothing until now could take a new
source and ANSWER the question those fields pose: which records does this retire, and what
exactly happens to the town when it does.

Answering it by hand is how the promise gets broken. A reader with a new directory line
would have to open 32 firms and 308 trade heads, read 340 sentences of prose, and decide;
and the parts of the retirement that are not in the record at all — the order-book row that
re-opens, the roof that has to be carried rather than demolished, the liberty whose count
has to be restated — are exactly the parts a hand-read forgets. So this prints the plan.

THIS TOOL WRITES NOTHING, EVER, AND THAT IS THE DESIGN.

`--dry-run` is the only mode that takes a candidate, and there is no `--build` beside it.
Every reconstructed record says the same thing about its own retirement — *"the retirement
runs through --build, never by hand"* — and the `--build` it means is its OWN generator's:
`reconstruct_businesses_1835.py`, `reconstruct_trade_households.py`. Those tools re-derive a
whole population from the order book, and a record that is no longer ordered stops being
written. A second tool that reached in and deleted one record would put the layer off its
fixed point and `check.sh` would go red at the next step. What retires a reconstruction is
therefore the SOURCE, entered where sources are entered; this file is the reading of what
that entry will cost, made before it is made.

THE MATCH, AND THE THREE THINGS IT ASKS.

A candidate is a small JSON document describing a record the research has just won — see
`tools/fixtures/substitution_candidate.json`, which is the shipped example and the fixture
`--self-test` runs over. Three predicates, and a record matches only if all three hold:

  1. **THE TRADE OR CLASS AGREES.** A business candidate names the December 1835 census
     class its house belongs to (`business_class`) or the occupation it is kept at
     (`trade`); a person candidate names the trade. A reconstructed record stands for a
     count of its class, so a candidate of another class replaces nothing.
  2. **THE PLACE DOES NOT DISAGREE.** Where the candidate names a division and the record
     names one too, they must be the same. Where the record names none, the match stands
     and the plan says the place was never narrowed — silence is not disagreement.
  3. **THE SCENE DATE AGREES.** A candidate that was not in the town on 1 July 1835
     retires nothing standing in it. `present_at_scene_date: false` matches nothing, and
     says so rather than printing an empty list.

AND IT NEVER PICKS BETWEEN MATCHES. Two reconstructed millineries on Lake Street are not
ranked: neither is more this candidate's than the other on any authority, which is the same
limit `adopt_street_faces.py` states about order within a face. Where the class leaves more
than one, all of them are printed and the choice is named as the operator's — a tool that
chose would be inventing the one fact the evidence does not carry.

THE RETIREMENT, AND THE THREE PARTS OF IT A HAND-READ LOSES.

  * **THE ID IS REDIRECTED, NOT DELETED.** A retired id keeps pointing at the record that
    replaced it. The town is walked through links and a reader who bookmarked a house may
    not find a hole where it stood.
  * **THE ROOF IS CARRIED.** Four of the 32 firms stand on a committed structure. The
    building is not the reconstruction — it was there before the firm was dealt onto it and
    stays after — so the new record takes the roof and nothing is demolished. A firm on a
    `street_only` face has no roof to carry and the plan says so.
  * **THE ORDER-BOOK ROW RE-OPENS.** Seven of the 32 fill a census quota. An attested house
    of that class raises `known` by one, which lowers `to_reconstruct` by one, and the
    retirement lowers `filled` by one: the row closes by being ANSWERED rather than by
    being filled. The other twenty-five were bought by a trade head and have no row — they
    are withdrawn with the head, and the plan names the head.

Each plan also names the `docs/LIBERTIES.md` entry whose count the retirement moves, which
is the part of this that has to be re-counted rather than remembered — see below.

WHICH LIBERTY COVERS WHICH FIRM, AND WHY THE MAP IS TYPED HERE.

The six entries that carry the reconstructed firms all declare the same `Scope:` — the
POPULATION, 32 houses of trade — and then state in their own prose how many of the 32 are
theirs: *"TWO are this entry's"*, *"of which FIFTEEN are this entry's"*. `compile_liberties`
re-derives the population and fails on drift. It has never re-derived the SHARE, because
nothing in a firm record names its liberty: a firm carries the ticket that built it and the
liberty carries no ticket at all, so the two cannot be joined out of the data.

`LIBERTY_OF_TICKET` below is that join, typed once and held honest from both ends. The
shares are NOT typed: one side is counted off the records on disk, the other is read out of
each entry's own sentence, and `--check` requires them to agree and to sum to the population
`compile_liberties` counts. A share that moves — a group rebuilt with one house more — now
fails a gate instead of leaving a word like FIFTEEN standing over fourteen firms.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUSINESSES = ROOT / "data" / "businesses"
TRADE_HEADS = ROOT / "data" / "residents" / "reconstructed_trades"
ORDER_BOOK = ROOT / "data" / "reconstruction" / "1835_reconstruction_order_book.json"
LIBERTIES = ROOT / "data" / "liberties.json"
FIXTURE = ROOT / "tools" / "fixtures" / "substitution_candidate.json"

SCENE_DATE = "1835-07-01"

# The join nothing in the data carries: the build ticket a reconstructed firm prints in
# `reconstruction.ticket`, against the liberty entry that admits that group. Typed, because
# a firm names no liberty and a liberty names no ticket; checked, because both counts are
# derived — see the docstring.
LIBERTY_OF_TICKET = {
    "T-1184": "L254",   # the apothecaries, the first group and the quota row
    "T-1377": "L255",   # the two Black-owned firms of the free_black sub-stage
    "T-1408": "L257",   # the boarding houses the buildings already stood for
    "T-1185": "L258",   # the mechanics' group: a brewery and a jeweller's shop
    "T-1418": "L259",   # two law offices and a physician's room
    "T-1424": "L260",   # two livery stables and two lumber yards
    "T-1419": "L262",   # the fifteen service houses
}

# The number-words the liberty prose states a share in. A closed list on purpose: a parser
# that guessed at "several" would be reading a claim that was never made.
WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20,
}

CANDIDATE_FIELDS = ("kind", "id", "name", "tier")
KINDS = ("business", "person")
TIERS = ("attested", "inferred")


class Fault(Exception):
    """A refusal, printed rather than raised through."""


def load(path: Path):
    with path.open() as fh:
        return json.load(fh)


# ---------------------------------------------------------------- the populations

def reconstructed_firms() -> list[dict]:
    """Every business record this project supplied rather than read."""
    out = []
    for path in sorted(BUSINESSES.rglob("*.json")):
        if path.name.endswith(".schema.json"):
            continue
        doc = load(path)
        if isinstance(doc, dict) and doc.get("provenance") == "reconstructed":
            out.append(doc)
    return out


def reconstructed_heads() -> list[dict]:
    """The reconstructed trade heads — the people a named tradesman retires.

    Deliberately not every reconstructed person. The other stages — women and children,
    lodgers, transients, the garrison — are retired by a re-cut of the order book and not
    by a name, which their own `withdrawn_if` says; a source naming one of those people
    would be a reading against a bucket, not a substitution, and this tool would have to
    invent the rule to answer it.
    """
    out = []
    for path in sorted(TRADE_HEADS.glob("*.json")):
        card = load(path)
        if isinstance(card, dict) and card.get("trade_household"):
            out.append(card)
    return out


def business_buckets() -> dict[str, dict]:
    for family in load(ORDER_BOOK)["bucket_families"]:
        if family.get("key") == "businesses":
            return {b["key"]: b for b in family["buckets"]}
    raise Fault("the order book holds no `businesses` bucket family")


# ---------------------------------------------------------------- reading a record

def firm_class(firm: dict) -> set[str]:
    """Every word this firm answers a class question with."""
    words = set(firm.get("type") or [])
    if firm.get("occupation"):
        words.add(firm["occupation"])
    bucket = (firm.get("reconstruction") or {}).get("bucket")
    if bucket:
        words.add(bucket.split("/")[-1])
    return {w for w in words if w and w != "other"}


def firm_division(firm: dict) -> str | None:
    """The division a firm's own seat names, or None where it narrows to nothing.

    A `street_only` face does not name a division — assigning premises to a division is
    T-1182's audit and T-1198's seating, and reading one off a street here would be this
    tool making that ruling in passing.
    """
    for loc in firm.get("locations") or []:
        if loc.get("division"):
            return loc["division"]
    return None


def firm_roof(firm: dict) -> str | None:
    for loc in firm.get("locations") or []:
        if loc.get("structure_id"):
            return loc["structure_id"]
    return None


def firm_head(firm: dict) -> dict | None:
    return (firm.get("reconstruction") or {}).get("trade_head")


def head_trade(card: dict) -> str | None:
    return (card.get("trade_household") or {}).get("trade")


# ---------------------------------------------------------------- the match

def candidate_read(doc: dict) -> dict:
    """Refuse a candidate that has not said what it is."""
    for field in CANDIDATE_FIELDS:
        if not doc.get(field):
            raise Fault("a candidate must name its `%s`" % field)
    if doc["kind"] not in KINDS:
        raise Fault("`kind` is one of %s, not %r" % ("/".join(KINDS), doc["kind"]))
    if doc["tier"] not in TIERS:
        raise Fault(
            "`tier` is one of %s. A reconstruction is not retired by another "
            "reconstruction: only a reading replaces a record this project supplied"
            % "/".join(TIERS))
    if doc["tier"] == "attested" and not (doc.get("source_id") or doc.get("claim_ids")):
        raise Fault(
            "an attested candidate owes a `source_id` or a `claim_ids`. "
            "`documented` REQUIRES a source record — docs/PROVENANCE.md")
    if not (doc.get("trade") or doc.get("business_class")):
        raise Fault("a candidate names the `trade` it is kept at, or its `business_class`")
    return doc


def _place_holds(candidate: dict, division: str | None) -> tuple[bool, str]:
    theirs = candidate.get("division")
    if not theirs or not division:
        return True, ("the record's place was never narrowed to a division"
                      if not division else "the candidate names no division")
    if theirs == division:
        return True, "both stand in the %s division" % division
    return False, "the candidate is %s and this record is %s" % (theirs, division)


def matches(candidate: dict) -> tuple[list[dict], list[str]]:
    """The reconstructed records this candidate would retire, and why the rest stand."""
    notes = []
    if candidate.get("present_at_scene_date") is False:
        return [], ["This candidate was not in the town on %s, so it stands in for "
                    "nothing that was. Nothing is retired." % SCENE_DATE]

    wanted = {w for w in (candidate.get("trade"), candidate.get("business_class")) if w}
    found = []

    if candidate["kind"] == "business":
        for firm in reconstructed_firms():
            classes = firm_class(firm)
            if not (classes & wanted):
                continue
            held, why = _place_holds(candidate, firm_division(firm))
            if not held:
                notes.append("%s is of the class and stands anyway: %s"
                             % (firm["id"], why))
                continue
            found.append({"kind": "business", "record": firm, "place": why})
    else:
        for card in reconstructed_heads():
            if head_trade(card) not in wanted:
                continue
            held, why = _place_holds(candidate, card.get("division"))
            if not held:
                notes.append("%s is of the trade and stands anyway: %s"
                             % (card["id"], why))
                continue
            found.append({"kind": "person", "record": card, "place": why})

    found.sort(key=lambda m: m["record"]["id"])
    return found, notes


# ---------------------------------------------------------------- the retirement

def plan(candidate: dict, match: dict, buckets: dict, shares: dict) -> dict:
    record = match["record"]
    out = {
        "retires": record["id"],
        "name": record.get("name"),
        "place": match["place"],
        "redirect": "%s → %s" % (record["id"], candidate["id"]),
        "performed_by": None,
        "roof": None,
        "order_book": None,
        "head": None,
        "liberty": None,
        "replaceable_by": record.get("replaceable_by"),
    }

    if match["kind"] == "business":
        recon = record.get("reconstruction") or {}
        out["performed_by"] = "tools/reconstruct_businesses_1835.py --build"
        out["withdrawn_if"] = recon.get("withdrawn_if")
        roof = firm_roof(record)
        out["roof"] = ("carry %s to %s — the building stood before this firm was dealt "
                       "onto it and is not demolished with it" % (roof, candidate["id"])
                       if roof else
                       "none to carry: this house holds a street face and no premises")
        bucket_key = recon.get("bucket")
        if bucket_key and bucket_key in buckets:
            b = buckets[bucket_key]
            known = b["known"] + (1 if candidate["kind"] == "business" else 0)
            out["order_book"] = {
                "bucket": bucket_key,
                "before": {"target": b["target"], "known": b["known"],
                           "to_reconstruct": b["to_reconstruct"], "filled": b["filled"]},
                "after": {"target": b["target"], "known": known,
                          "to_reconstruct": max(b["target"] - known, 0),
                          "filled": b["filled"] - 1},
                "reading": "the row closes by being answered: the census count is met by "
                           "a house somebody wrote down instead of one this project dealt",
            }
        else:
            head = firm_head(record)
            out["order_book"] = {
                "bucket": None,
                "reading": "no row to free. No census line reaches this class, so no "
                           "count of it was ever short; the house was bought by a trade "
                           "head and is withdrawn with the head.",
            }
            if head:
                out["head"] = "%s (%s) keeps standing on their own person bucket — " \
                              "retiring the house does not retire the head, and the " \
                              "head retiring does retire the house" \
                              % (head.get("person_id"), head.get("trade"))
        liberty = LIBERTY_OF_TICKET.get(recon.get("ticket"))
        out["liberty"] = (
            "%s: its share falls from %d to %d, and the sentence stating it has to be "
            "restated in docs/LIBERTIES.md" % (liberty, shares[liberty], shares[liberty] - 1)
            if liberty and liberty in shares else
            "no liberty entry is mapped to ticket %r — add it to LIBERTY_OF_TICKET"
            % recon.get("ticket"))
    else:
        th = record.get("trade_household") or {}
        # The card is a household and the reconstruction is its HEAD: what an attested
        # tradesman replaces is the person the order book drew, and the house goes with
        # him because it was written to hold him.
        out["retires"] = record.get("head") or record["id"]
        out["redirect"] = "%s → %s (and the card %s it heads)" % (
            out["retires"], candidate["id"], record["id"])
        out["performed_by"] = "tools/reconstruct_trade_households.py --build"
        out["withdrawn_if"] = th.get("withdrawn_if")
        out["roof"] = ("none to carry: T-1199 seats these households and this card is "
                       "not seated" if not (record.get("lives_at") or {}).get("value")
                       else "carry %s" % record["lives_at"]["value"])
        out["order_book"] = {
            "bucket": th.get("bucket"),
            "reading": "the person bucket this head was ordered out of takes the "
                       "attested person instead; the slot %s is not re-dealt"
                       % th.get("slot"),
        }
        out["liberty"] = ("L248: the trade-household share falls by one and its count "
                          "has to be restated")
    return out


# ---------------------------------------------------------------- the liberty re-count

def declared_shares() -> dict[str, int]:
    """Each entry's own statement of how many of the 32 firms are its own."""
    out = {}
    for lib in load(LIBERTIES)["liberties"]:
        lid = lib["id"]
        if lid not in LIBERTY_OF_TICKET.values():
            continue
        for field in lib.get("fields", []):
            text = field["text"]
            hit = re.search(r"\*{0,2}(\w+)\*{0,2}\s+are this entry's", text)
            if hit:
                out[lid] = _number(hit.group(1), lid)
                break
            hit = re.search(r"\*{0,2}(\w+)\*{0,2}\s+firms\b", text)
            if hit:
                out[lid] = _number(hit.group(1), lid)
                break
        if lid not in out:
            raise Fault("%s carries no sentence stating its own share of the "
                        "reconstructed firms" % lid)
    return out


def _number(token: str, lid: str) -> int:
    if token.isdigit():
        return int(token)
    word = WORD_NUMBERS.get(token.lower())
    if word is None:
        raise Fault("%s states its share as %r, which is not a number this parser "
                    "reads — see WORD_NUMBERS" % (lid, token))
    return word


def counted_shares(firms: list[dict] | None = None) -> dict[str, int]:
    """The same shares, counted off the records on disk."""
    out = {lid: 0 for lid in LIBERTY_OF_TICKET.values()}
    for firm in (reconstructed_firms() if firms is None else firms):
        ticket = (firm.get("reconstruction") or {}).get("ticket")
        lid = LIBERTY_OF_TICKET.get(ticket)
        if lid is None:
            raise Fault("%s was built by %r and no liberty entry is mapped to it"
                        % (firm["id"], ticket))
        out[lid] += 1
    return out


def population() -> int:
    """What `compile_liberties` counts the Scope over — the third statement."""
    for lib in load(LIBERTIES)["liberties"]:
        scope = lib.get("scope") or {}
        if scope.get("enumeration") == "businesses.records[reconstructed]":
            return scope["count"]
    raise Fault("no liberty declares the `businesses.records[reconstructed]` scope")


def recount(firms: list[dict] | None = None,
            declared: dict[str, int] | None = None,
            pop: int | None = None) -> list[str]:
    counted = counted_shares(firms)
    said = declared_shares() if declared is None else declared
    total = population() if pop is None else pop
    problems = []
    for lid in sorted(counted, key=lambda k: int(k[1:])):
        if counted[lid] != said.get(lid):
            problems.append(
                "%s says %s of the reconstructed firms are its own and %d are — "
                "restate the sentence, and the prose that reasons from it"
                % (lid, said.get(lid), counted[lid]))
    if sum(counted.values()) != total:
        problems.append(
            "the entries' shares sum to %d and the scope counts %d reconstructed "
            "firms — %d house(s) are covered by no liberty entry"
            % (sum(counted.values()), total, total - sum(counted.values())))
    return problems


# ---------------------------------------------------------------- the modes

def _print_plan(p: dict, n: int) -> None:
    print("  %d. %s — %s" % (n, p["retires"], p["name"]))
    print("     place        %s" % p["place"])
    print("     redirect     %s" % p["redirect"])
    print("     roof         %s" % p["roof"])
    ob = p["order_book"]
    if ob.get("bucket") and ob.get("before"):
        print("     order book   %s  %s → %s"
              % (ob["bucket"], ob["before"], ob["after"]))
        print("                  %s" % ob["reading"])
    else:
        print("     order book   %s" % ob["reading"])
        if ob.get("bucket"):
            print("                  bucket %s" % ob["bucket"])
    if p.get("head"):
        print("     head         %s" % p["head"])
    print("     liberty      %s" % p["liberty"])
    print("     performed by %s" % p["performed_by"])


def dry_run(path: Path) -> int:
    candidate = candidate_read(load(path))
    print("CANDIDATE  %s — %s (%s, %s)"
          % (candidate["id"], candidate["name"], candidate["kind"], candidate["tier"]))
    if candidate.get("source_id"):
        print("           source %s" % candidate["source_id"])
    found, notes = matches(candidate)
    print()
    if not found:
        print("RETIRES NOTHING.")
        for note in notes:
            print("  %s" % note)
        if not notes:
            print("  No reconstructed record of this class stands in the town. The "
                  "candidate is an addition, not a substitution.")
        return 0

    buckets = business_buckets()
    shares = declared_shares()
    print("WOULD RETIRE %d reconstructed record(s):" % len(found))
    print()
    for n, match in enumerate(found, 1):
        _print_plan(plan(candidate, match, buckets, shares), n)
        print()
    if len(found) > 1:
        print("THE CHOICE IS YOURS, AND IT IS NOT IN THE EVIDENCE. %d records answer "
              "this candidate's class and place equally; nothing ranks them, so this "
              "tool prints them all rather than picking one." % len(found))
    for note in notes:
        print("  also: %s" % note)
    print()
    print("NOTHING HAS BEEN RETIRED. Enter the source where sources are entered and "
          "re-run the generator named above; it rebuilds the population from the order "
          "book and stops writing a record that is no longer ordered.")
    return 0


def report() -> int:
    firms = reconstructed_firms()
    heads = reconstructed_heads()
    buckets = business_buckets()
    print("THE SUBSTITUTABLE POPULATION")
    print("  %d reconstructed firms, %d reconstructed trade heads" % (len(firms), len(heads)))
    quota = [f for f in firms if (f.get("reconstruction") or {}).get("bucket") in buckets]
    roofed = [f for f in firms if firm_roof(f)]
    print("  %d firm(s) fill a census quota; %d stand on a committed roof"
          % (len(quota), len(roofed)))
    print()
    print("THE LIBERTY SHARES, RE-COUNTED")
    counted, said = counted_shares(firms), declared_shares()
    for lid in sorted(counted, key=lambda k: int(k[1:])):
        mark = "ok  " if counted[lid] == said.get(lid) else "DRIFT"
        print("  %s %s  counted %2d   its own sentence says %s"
              % (mark, lid, counted[lid], said.get(lid)))
    print("  %d firm(s) covered, scope counts %d" % (sum(counted.values()), population()))
    problems = recount(firms)
    for problem in problems:
        print("  %s" % problem)
    return 1 if problems else 0


def check() -> int:
    problems = recount()
    for firm in reconstructed_firms():
        recon = firm.get("reconstruction") or {}
        if not firm.get("replaceable_by"):
            problems.append("%s carries no `replaceable_by` — a reconstruction that "
                            "does not say what would retire it cannot be substituted"
                            % firm["id"])
        if not recon.get("withdrawn_if"):
            problems.append("%s carries no `reconstruction.withdrawn_if`" % firm["id"])
    for card in reconstructed_heads():
        if not (card.get("trade_household") or {}).get("withdrawn_if"):
            problems.append("%s carries no `trade_household.withdrawn_if`" % card["id"])
    if problems:
        print("FAIL: %d problem(s)" % len(problems))
        for problem in problems:
            print("  %s" % problem)
        return 1
    counted = counted_shares()
    print("  %d reconstructed firms and %d trade heads each say what would retire them"
          % (sum(counted.values()), len(reconstructed_heads())))
    print("  liberty shares agree with the records: %s"
          % ", ".join("%s %d" % (lid, counted[lid])
                      for lid in sorted(counted, key=lambda k: int(k[1:]))))
    return 0


# ---------------------------------------------------------------- the self-test

def _firm(fid, ticket, klass, bucket=None, roof=None, division=None, head=None):
    loc = {"kind": "street_only", "structure_id": roof, "street_id": "lake",
           "division": division, "primary": True}
    recon = {"ticket": ticket, "group": "fixture", "bucket": bucket,
             "withdrawn_if": "a source naming a real house of this class"}
    if head:
        recon["trade_head"] = {"person_id": head, "trade": klass}
    return {"id": fid, "name": fid, "provenance": "reconstructed", "type": [klass],
            "occupation": klass, "locations": [loc], "reconstruction": recon,
            "replaceable_by": "a directory naming a real house of this class"}


def self_test() -> int:
    print("  the rule, held over fixtures")
    print()
    fired = []

    def refuses(doc, needle):
        try:
            candidate_read(doc)
        except Fault as exc:
            assert needle in str(exc), "refused for the wrong reason: %s" % exc
            fired.append(needle)
            print("  ok    refused: %s" % str(exc)[:96])
            return
        raise AssertionError("a candidate that should have been refused passed: %r" % doc)

    good = {"kind": "business", "id": "biz_x", "name": "X", "tier": "attested",
            "source_id": "s", "business_class": "brewery"}
    refuses({**good, "tier": "reconstructed"}, "not retired by another reconstruction")
    refuses({**good, "source_id": None}, "owes a `source_id`")
    refuses({**good, "business_class": None}, "names the `trade`")
    refuses({**good, "kind": "roof"}, "`kind` is one of")
    candidate_read(good)
    print("  ok    …and a candidate that names its class, tier and source passes")
    print()

    # THE MATCH, over a fixture population rather than the committed town.
    fixture = [
        _firm("rcb_a_brewery", "T-1185", "brewery", bucket="businesses/brewery"),
        _firm("rcb_b_brewery", "T-1185", "brewery", bucket="businesses/brewery",
              division="west"),
        _firm("rcb_c_millinery", "T-1419", "millinery", roof="recon_1835_north_h1_007",
              head="rc_c_head"),
    ]
    global reconstructed_firms
    keep = reconstructed_firms
    reconstructed_firms = lambda: list(fixture)  # noqa: E731
    try:
        found, notes = matches(good)
        assert [m["record"]["id"] for m in found] == ["rcb_a_brewery", "rcb_b_brewery"], \
            "the class match did not take both breweries: %s" % found
        print("  ok    a brewery candidate with no division takes both breweries — "
              "silence is not disagreement")

        found, notes = matches({**good, "division": "south"})
        assert [m["record"]["id"] for m in found] == ["rcb_a_brewery"], \
            "a south candidate took a west record"
        assert notes and "west" in notes[0], "the standing record went unexplained"
        print("  ok    …and one that names the south division leaves the west house "
              "standing, with its reason: %s" % notes[0][:60])

        found, _ = matches({**good, "business_class": "tannery"})
        assert found == [], "a class nothing reconstructed matched something"
        print("  ok    a class the town reconstructed none of retires nothing")

        found, notes = matches({**good, "present_at_scene_date": False})
        assert found == [] and SCENE_DATE in notes[0], "a later house retired a standing one"
        print("  ok    a candidate that was not here on %s retires nothing" % SCENE_DATE)
        print()

        # THE PLAN — the three parts a hand-read loses.
        buckets = {"businesses/brewery": {"target": 2, "known": 1, "to_reconstruct": 1,
                                          "filled": 1}}
        shares = {"L258": 2, "L262": 15}
        p = plan(good, {"kind": "business", "record": fixture[0], "place": "-"},
                 buckets, shares)
        assert p["order_book"]["after"] == {"target": 2, "known": 2, "to_reconstruct": 0,
                                            "filled": 0}, p["order_book"]
        print("  ok    the quota row closes by being answered — known 1→2, "
              "to_reconstruct 1→0, filled 1→0")
        assert "none to carry" in p["roof"], p["roof"]
        assert p["liberty"].startswith("L258: its share falls from 2 to 1"), p["liberty"]
        print("  ok    …and it names the liberty whose share falls: %s" % p["liberty"][:56])

        p = plan(good, {"kind": "business", "record": fixture[2], "place": "-"},
                 buckets, shares)
        assert p["roof"].startswith("carry recon_1835_north_h1_007"), p["roof"]
        assert "not demolished" in p["roof"]
        print("  ok    a firm on a committed roof carries the roof rather than "
              "demolishing it")
        assert p["order_book"]["bucket"] is None and "no row to free" in p["order_book"]["reading"]
        assert p["head"] and "rc_c_head" in p["head"]
        print("  ok    …and a house no census line reaches frees no row and names "
              "its head instead")
        assert p["redirect"] == "rcb_c_millinery → biz_x"
        print("  ok    the retired id is redirected, never deleted")
    finally:
        reconstructed_firms = keep

    print()
    # THE LIBERTY RE-COUNT, broken in memory against the committed entries.
    said = declared_shares()
    counted = counted_shares()
    assert recount() == [], "the committed town does not pass its own re-count"
    print("  ok    the committed shares agree: %s"
          % ", ".join("%s %d" % (k, counted[k]) for k in sorted(counted, key=lambda x: int(x[1:]))))
    moved = dict(said)
    moved["L262"] = said["L262"] + 1
    problems = recount(declared=moved)
    assert problems and "L262" in problems[0], problems
    fired.append("share drift")
    print("  ok    a liberty whose sentence says one house more than stands is "
          "caught — %s" % problems[0][:80])
    problems = recount(pop=population() + 1)
    assert problems and "covered by no liberty entry" in problems[-1], problems
    fired.append("uncovered firm")
    print("  ok    a firm covered by no entry at all is caught — %s" % problems[-1][:80])
    short = [f for f in reconstructed_firms() if
             (f.get("reconstruction") or {}).get("ticket") != "T-1184"]
    problems = recount(firms=short)
    assert problems and "L254" in problems[0], problems
    print("  ok    …and a group rebuilt with fewer houses than its sentence claims "
          "is caught — %s" % problems[0][:80])
    assert _number("FIFTEEN", "L262") == 15 and _number("15", "L262") == 15
    try:
        _number("several", "L262")
    except Fault as exc:
        assert "not a number this parser reads" in str(exc)
        fired.append("unreadable share")
        print("  ok    a share stated as a word the parser does not know is refused, "
              "not guessed at")
    print()
    print("  the shipped fixture runs against the committed town")
    assert FIXTURE.exists(), "tools/fixtures/substitution_candidate.json is missing"
    assert dry_run(FIXTURE) == 0
    print()
    print("%d guards fired, the rule holds over the fixture and the committed town."
          % len(fired))
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    try:
        if args[:1] == ["--dry-run"]:
            rest = args[1:]
            path = FIXTURE if rest[:1] == ["--fixture"] or not rest else Path(rest[0])
            sys.exit(dry_run(path))
        fn = {"--report": report, "--check": check, "--self-test": self_test}.get(
            args[0] if args else "--report")
        if fn is None:
            raise SystemExit(__doc__)
        sys.exit(fn())
    except Fault as exc:
        raise SystemExit("REFUSED: %s" % exc)
