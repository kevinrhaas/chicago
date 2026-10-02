#!/usr/bin/env python3
"""What a new attested record would retire, before anything is retired (T-1441, of T-1190).

    python3 tools/substitute_reconstruction.py --dry-run <candidate.json>
    python3 tools/substitute_reconstruction.py --dry-run --fixture   the shipped example
    python3 tools/substitute_reconstruction.py --dry-run tools/fixtures/substitution_candidate_roof.json
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

AND A ROOF, WHICH IS RETIRED BY ITS LOT (T-1968).

The anonymous roofs stand for no trade, so a `kind: "structure"` candidate names the
`lot_id` the lot ledger writes and its class, principal or ancillary, and retires the
anonymous roof of that class standing there — read by the ledger's own family rule, never
a building a source put on the lot. The plan carries who lives and works under it, leaves
the roof programme where it stands (L81: a named discovery substitutes and never adds), and
names the generator and the liberty; nothing is typed for it, because the ledger, the
programme phase and the liberties' own covers already join it.
`tools/fixtures/substitution_candidate_roof.json` is the shipped example.

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
ROOF_FIXTURE = ROOT / "tools" / "fixtures" / "substitution_candidate_roof.json"
STRUCTURES = ROOT / "data" / "structures"
LOT_LEDGER = ROOT / "data" / "reconstruction" / "1835_lot_ledger.json"
ROOF_PROGRAMME = ROOT / "data" / "reconstruction" / "1835_665_roof_programme.json"

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
    "T-1766": "L307",   # four Canal approach firms on non-lodging trade roofs
    "T-2001": "L360",   # seven houses of trade no census line reaches
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
KINDS = ("business", "person", "structure")
ROOF_CLASSES = ("principal_functional", "ancillary")

# T-1968: which generator writes an anonymous roof, by the programme phase its own record
# names. A prefix, because the platted-block deals name a phase per block and per deal.
GENERATOR_OF_PHASE = (
    ("phase3_platted_block", "tools/generate_block_infill.py"),
    ("phase1_south_mixed_blocks", "tools/generate_inferred_infill.py"),
    ("phase2_north_division_initial", "tools/generate_north_infill.py"),
    ("phase2_west_wolf_point_approaches", "tools/generate_west_infill.py"),
    ("phase2_inferred_households", "tools/generate_inferred_households.py"),
    ("canal_approach_trade_1835", "tools/generate_canal_approach_trade.py"),
    ("west_freight_forks_1835", "tools/generate_west_freight.py"),
)

# The liberties that cover EVERY reconstruction (`recon_*`, `inf_*`) state a rule for the
# whole layer and carry no count of roofs; retiring one roof moves none of them, so the
# plan names the entries that cover the roof by its own id or by its own block.
TOWN_WIDE_COVERS = ("recon_*", "inf_*")
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


def lot_rows() -> dict[str, dict]:
    return {row["lot_id"]: row for row in load(LOT_LEDGER)["lots"]}


def structure(sid: str) -> dict | None:
    path = STRUCTURES / ("%s.json" % sid)
    return load(path) if path.exists() else None


def reconstructed_roofs_on_lots() -> list[tuple[dict, dict]]:
    """Every anonymous roof the lot ledger stands on a lot, with its lot — the roofs a
    building read onto that lot would retire."""
    out = []
    for row in load(LOT_LEDGER)["lots"]:
        for sid in row["standing"]:
            rec = structure(sid)
            if rec and rec.get("reconstruction"):
                out.append((rec, row))
    return out


def roof_class(sid: str, row: dict) -> str | None:
    """The class the LOT LEDGER counts this roof in — its family read by the ledger's own
    rule (A1-A5 ancillary, every other family principal). Not the record's
    `inventory_class`: the plan's promise is that the lot's count does not move, which is
    a statement about the ledger's count, and six platted-block dwellings carry an
    `inventory_class` the ledger does not count them by (T-1968's finding). None where
    the ledger names no family."""
    from seat_platted_ground_1835 import ANCILLARY_LETTERS        # noqa: PLC0415
    family = (row.get("standing_families") or {}).get(sid)
    if family is None:
        return None
    return "ancillary" if family in ANCILLARY_LETTERS else "principal_functional"


def generator_of(roof: dict) -> str | None:
    phase = (roof.get("reconstruction") or {}).get("programme_phase") or ""
    return next((tool for prefix, tool in GENERATOR_OF_PHASE if phase.startswith(prefix)),
                None)


def liberties_of_roof(sid: str) -> list[str]:
    """The entries that cover this roof by its own id or by its own block — derived from
    the compiled liberties, never typed."""
    from fnmatch import fnmatch                                   # noqa: PLC0415
    out = []
    for lib in load(LIBERTIES)["liberties"]:
        pats = {c.get("structure") for c in lib.get("covers") or []
                if "*" in (c.get("structure") or "")} - set(TOWN_WIDE_COVERS)
        if sid in (lib.get("subjects") or []) or any(fnmatch(sid, p) for p in pats):
            out.append(lib["id"])
    return out


def firms_on(sid: str) -> list[str]:
    """Every business, of any tier, whose own location names this roof."""
    out = []
    for path in sorted(BUSINESSES.rglob("*.json")):
        if path.name.endswith(".schema.json"):
            continue
        doc = load(path)
        if isinstance(doc, dict) and any(loc.get("structure_id") == sid
                                         for loc in doc.get("locations") or []):
            out.append(doc["id"])
    return out


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
    if doc["kind"] == "structure":
        # A roof is retired by the ground it stands on, not by a trade. An anonymous roof
        # off the plat names no lot, so a building read without one is an addition to the
        # programme — and saying which lot is the reading this tool cannot make for it.
        if not doc.get("lot_id"):
            raise Fault("a structure candidate names the `lot_id` it stands on, as the "
                        "lot ledger writes it (`blk_<block>#NN`)")
        if doc.setdefault("inventory_class", "principal_functional") not in ROOF_CLASSES:
            raise Fault("`inventory_class` is one of %s, not %r"
                        % ("/".join(ROOF_CLASSES), doc["inventory_class"]))
        return doc
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

    if candidate["kind"] == "structure":
        return roof_matches(candidate)

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


def roof_matches(candidate: dict, lots: dict | None = None,
                 read=structure) -> tuple[list[dict], list[str]]:
    """THE LOT, AND THE CLASS OF ROOF. A building read onto a lot retires the anonymous
    roof of its own class standing there — a dwelling the dwelling, a stable the yard
    building — and nothing a source put there. Where the lot's rule seats more than one
    roof of the class (a party-line run carries three), every one is printed and the choice
    is the operator's, for the reason `matches` gives."""
    lots = lot_rows() if lots is None else lots
    row = lots.get(candidate["lot_id"])
    if row is None:
        raise Fault("%s is not a lot in data/reconstruction/1835_lot_ledger.json"
                    % candidate["lot_id"])
    place = "lot %s, fronting %s — its rule is %s, at most %d principal roof(s)" % (
        row["lot_id"], row.get("fronts") or "no street", row["multi_building_rule"],
        row["principal_roofs_max"])
    found, notes = [], []
    for sid in row["standing"]:
        rec = read(sid)
        if rec is None:
            notes.append("%s is named by the lot ledger and has no record" % sid)
            continue
        recon = rec.get("reconstruction")
        if not recon:
            notes.append("%s stands: a source put it on this lot, and only a "
                         "reconstruction is retired" % sid)
            continue
        if roof_class(sid, row) != candidate["inventory_class"]:
            notes.append("%s stands: the lot ledger counts it %s and the candidate is %s"
                         % (sid, roof_class(sid, row), candidate["inventory_class"]))
            continue
        found.append({"kind": "structure", "record": rec, "place": place, "lot": row})
    if not found:
        notes.append("Lot %s holds no anonymous %s roof, so the building is an addition to "
                     "it; the lot ledger reads the lot `%s` today%s." % (
                         row["lot_id"], candidate["inventory_class"], row["state"],
                         " and will read it over its rule" if row["state"] == "at_capacity"
                         and candidate["inventory_class"] == "principal_functional" else ""))
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

    if match["kind"] == "structure":
        return roof_plan(candidate, match, out)

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
        elif recon.get("trade_roof"):
            # T-1766's firm fills no census quota and provides no lodging beds.
            # Substitution carries the physical workplace while retaining its keeper;
            # retiring a firm never implies demolition or retirement of a person.
            trade_roof = recon["trade_roof"]
            out["performed_by"] = (
                "replace the allocation in data/reconstruction/1835_canal_approach_occupancy.json "
                "and its authored firm; tools/canal_approach_occupancy.py --build "
                "must be updated to preserve that documented replacement")
            out["order_book"] = {
                "bucket": None,
                "reading": "no firm quota row to free: this house was bought by an "
                           "already standing trade roof. Keep the physical roof and "
                           "its roof-programme accounting; no lodging beds were invented.",
            }
            out["head"] = "%s (%s), household %s, keeps standing on their own person " \
                          "bucket. Replacing this firm does not retire the keeper or " \
                          "assert that the keeper lived at the workplace." % (
                              trade_roof.get("keeper_person_id"),
                              trade_roof.get("occupation"),
                              trade_roof.get("keeper_household_id"))
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


def roof_plan(candidate: dict, match: dict, out: dict, programme: dict | None = None,
              liberties=liberties_of_roof, firms=firms_on) -> dict:
    """The retirement of an anonymous roof, and the three parts of it a hand-read loses:
    who lives and works under it (carried, not evicted), the programme count (unchanged —
    L81's rule that a named discovery substitutes and never adds), and the entry whose
    count of anonymous roofs on the block has to be restated."""
    record, row = match["record"], match["lot"]
    recon = record.get("reconstruction") or {}
    sid = record["id"]
    tool = generator_of(record)
    out["performed_by"] = (
        "%s — it re-derives the roofs of programme phase %s, and must be taught to leave "
        "lot %s's %s slot to the read building" % (
            tool, recon.get("programme_phase"), row["lot_id"], roof_class(sid, row))
        if tool else "no generator is mapped to programme phase %r — add it to "
                     "GENERATOR_OF_PHASE" % recon.get("programme_phase"))
    out["withdrawn_if"] = "parcel-specific evidence for this lot (L81: a contemporary tax, " \
                          "assessment, deed, insurance or surveyed building register)"
    out["roof"] = ("this record IS the roof: %s stands in its place on lot %s and takes its "
                   "seat in the lot ledger, so the lot's count of %s roofs does not move"
                   % (candidate["id"], row["lot_id"], roof_class(sid, row)))
    carried = []
    occ = (record.get("occupants") or {}).get("value")
    if occ:
        carried.append("occupants: %s" % occ)
    hh = (record.get("resident_assignment") or {}).get("household_id")
    if hh:
        carried.append("household %s" % hh)
    carried += ["business %s" % fid for fid in firms(sid)]
    out["carried"] = carried or ["nobody: the roof is empty, so nothing is re-seated"]
    prog = load(ROOF_PROGRAMME) if programme is None else programme
    generated = prog["standing"]["by_source"].get("generated")
    out["order_book"] = {
        "bucket": None,
        "reading": "the %d-roof programme does not move: one generated roof (%s of them) "
                   "leaves and one read roof enters, so %d still remain to place — a named "
                   "discovery substitutes for a compatible anonymous roof and never "
                   "increases the total (L81)" % (
                       prog["remaining"]["of_target"], generated, prog["remaining"]["roofs"]),
    }
    libs = liberties(sid)
    out["liberty"] = ("%s: the count of anonymous roofs %s falls by one, and the "
                      "sentence stating it has to be restated in docs/LIBERTIES.md"
                      % (", ".join(libs), "each states" if len(libs) > 1 else "it states")
                      if libs else
                      "no entry covers %s by its id or its block — a roof without its "
                      "liberty is a gap in docs/LIBERTIES.md" % sid)
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
            # T-1525: `is` as well as `are`. The regex was written when every share was
            # plural; a share can fall to one, and it did — L259's physician's room was
            # withdrawn and the entry now states a single law office. A parser that reads
            # only the plural would have made the prose ungrammatical to stay legible to
            # it, which is the wrong way round.
            hit = re.search(r"\*{0,2}(\w+)\*{0,2}\s+(?:are|is) this entry's", text)
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
    for n_carried, line in enumerate(p.get("carried") or []):
        print("     %s %s" % ("carried     " if n_carried == 0 else "            ", line))
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
          "re-run the generator named above; it rebuilds the population from the %s "
          "and stops writing a record that is no longer ordered."
          % ("roof programme" if candidate["kind"] == "structure" else "order book"))
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
    roofs = reconstructed_roofs_on_lots()
    print("  %d anonymous roofs stand on %d platted lots, each retired by a building read "
          "onto its lot" % (len(roofs), len({row["lot_id"] for _, row in roofs})))
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
    roofs = reconstructed_roofs_on_lots()
    problems += roof_coverage(roofs)
    if problems:
        print("FAIL: %d problem(s)" % len(problems))
        for problem in problems:
            print("  %s" % problem)
        return 1
    counted = counted_shares()
    print("  %d reconstructed firms and %d trade heads each say what would retire them"
          % (sum(counted.values()), len(reconstructed_heads())))
    print("  %d anonymous roofs on %d platted lots each name the generator and the liberty "
          "a building read onto the lot would move"
          % (len(roofs), len({row["lot_id"] for _, row in roofs})))
    print("  liberty shares agree with the records: %s"
          % ", ".join("%s %d" % (lid, counted[lid])
                      for lid in sorted(counted, key=lambda k: int(k[1:]))))
    return 0


def roof_coverage(roofs: list[tuple[dict, dict]], liberties=liberties_of_roof) -> list[str]:
    """T-1968: every anonymous roof the lot ledger stands on a lot can be substituted —
    its class is one a candidate can name, a generator is mapped to its phase, and a
    liberty covers it by its own id or its block. A roof missing any of the three would
    print a plan that cannot be carried out, and that is found here rather than on the
    day the source arrives."""
    out = []
    for rec, row in roofs:
        recon = rec.get("reconstruction") or {}
        if roof_class(rec["id"], row) not in ROOF_CLASSES:
            out.append("%s on %s: the lot ledger names no family for it, so no candidate "
                       "can name its class" % (rec["id"], row["lot_id"]))
        if not generator_of(rec):
            out.append("%s: no generator is mapped to programme phase %r"
                       % (rec["id"], recon.get("programme_phase")))
        if not liberties(rec["id"]):
            out.append("%s: no liberty covers it by its id or its block" % rec["id"])
    return out


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
    # T-1766: the four actual non-lodging firms preserve roof and keeper, and never
    # make up a business quota or reuse a lodging capacity on substitution.
    trade_roofs = [f for f in reconstructed_firms()
                   if (f.get("reconstruction") or {}).get("trade_roof")]
    assert len(trade_roofs) == 4, "the four Canal trade roofs must remain covered"
    for firm in trade_roofs:
        tr = firm["reconstruction"]["trade_roof"]
        retirement = plan(good, {"kind": "business", "record": firm, "place": "fixture"},
                          {}, {"L307": 4})
        assert tr["structure_id"] in retirement["roof"]
        assert "not demolished" in retirement["roof"]
        assert tr["keeper_person_id"] in retirement["head"]
        assert "does not retire" in retirement["head"]
        assert retirement["order_book"]["bucket"] is None
        assert "no lodging beds" in retirement["order_book"]["reading"]
        assert "canal_approach_occupancy.py" in retirement["performed_by"]
        assert retirement["liberty"].startswith("L307: its share falls from 4 to 3")
    print("  ok    all four trade-roof substitutions retain roof and keeper, free no quota and name L307")

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
    # T-1968: THE ROOF — matched by its lot and the ledger's class, over fixture lots.
    roof = {"kind": "structure", "id": "bldg_x", "name": "X", "tier": "attested",
            "source_id": "s", "lot_id": "blk_f#01"}
    refuses({**roof, "lot_id": None}, "names the `lot_id`")
    refuses({**roof, "inventory_class": "civic"}, "`inventory_class` is one of")
    assert candidate_read(dict(roof))["inventory_class"] == "principal_functional"
    print("  ok    …and a roof that names no class is read as a principal roof")

    def _roof(sid, phase="phase3_platted_block_f"):
        return {"id": sid, "name": sid, "reconstruction": {
            "status": "inferred_anonymous", "programme_phase": phase},
            "resident_assignment": {"household_id": "hh_f"} if sid == "recon_f_d1" else {}}
    town = {"recon_f_d1": _roof("recon_f_d1"), "recon_f_d2": _roof("recon_f_d2"),
            "recon_f_a1": _roof("recon_f_a1"), "read_f": {"id": "read_f", "name": "read"}}
    lot = {"lot_id": "blk_f#01", "fronts": "lake", "multi_building_rule": "party_line_run",
           "principal_roofs_max": 3, "state": "at_capacity",
           "standing": ["read_f", "recon_f_a1", "recon_f_d1", "recon_f_d2"],
           "standing_families": {"read_f": "C1", "recon_f_a1": "A1", "recon_f_d1": "D1",
                                 "recon_f_d2": "D2"}}
    found, notes = roof_matches(candidate_read(dict(roof)), {"blk_f#01": lot}, town.get)
    assert [m["record"]["id"] for m in found] == ["recon_f_d1", "recon_f_d2"], found
    assert any("read_f stands: a source put it" in n for n in notes), notes
    assert any("recon_f_a1 stands: the lot ledger counts it ancillary" in n for n in notes)
    fired.append("roof by lot and class")
    print("  ok    a dwelling read onto a party-line lot offers both anonymous dwellings, "
          "leaves the stable and the read store standing")
    found, _ = roof_matches({**candidate_read(dict(roof)), "inventory_class": "ancillary"},
                            {"blk_f#01": lot}, town.get)
    assert [m["record"]["id"] for m in found] == ["recon_f_a1"], found
    print("  ok    …and a stable read onto it retires the yard building only")
    empty = {**lot, "standing": ["read_f"], "standing_families": {"read_f": "C1"}}
    found, notes = roof_matches(candidate_read(dict(roof)), {"blk_f#01": empty}, town.get)
    assert found == [] and "addition" in notes[-1] and "over its rule" in notes[-1], notes
    print("  ok    a lot with no anonymous roof of the class takes an addition, and an "
          "at-capacity lot says it will read over its rule")
    try:
        roof_matches({**candidate_read(dict(roof)), "lot_id": "blk_nowhere#09"},
                     {"blk_f#01": lot}, town.get)
        raise AssertionError("a lot the ledger does not hold was matched")
    except Fault as exc:
        assert "is not a lot" in str(exc)
        fired.append("unknown lot")
        print("  ok    a lot the ledger does not hold is refused")
    prog = {"standing": {"by_source": {"generated": 10}},
            "remaining": {"of_target": 20, "roofs": 4}}
    p = roof_plan(roof, {"kind": "structure", "record": town["recon_f_d1"],
                         "place": "-", "lot": lot},
                  {"retires": "recon_f_d1", "redirect": "recon_f_d1 → bldg_x"}, prog,
                  liberties=lambda sid: ["L1"], firms=lambda sid: ["biz_f"])
    assert p["carried"] == ["household hh_f", "business biz_f"], p["carried"]
    assert "does not move" in p["order_book"]["reading"] and "4 still remain" in \
        p["order_book"]["reading"]
    assert p["liberty"].startswith("L1: the count of anonymous roofs it states falls")
    assert p["performed_by"].startswith("tools/generate_block_infill.py")
    print("  ok    the plan carries the household and the business, leaves the programme "
          "where it stands and names the liberty and the generator")
    gaps = roof_coverage([({**town["recon_f_d1"], "reconstruction": {
        "programme_phase": "phase9_nowhere"}}, lot)], liberties=lambda sid: [])
    assert len(gaps) == 2 and "no generator" in gaps[0] and "no liberty" in gaps[1], gaps
    fired.append("roof coverage")
    print("  ok    a roof no generator writes and no liberty covers is caught by --check")
    print()
    print("  the shipped fixtures run against the committed town")
    assert FIXTURE.exists(), "tools/fixtures/substitution_candidate.json is missing"
    assert dry_run(FIXTURE) == 0
    print()
    assert ROOF_FIXTURE.exists(), "tools/fixtures/substitution_candidate_roof.json is missing"
    found, _ = matches(candidate_read(load(ROOF_FIXTURE)))
    assert [m["record"]["id"] for m in found] == ["recon_1835_blk_south_water_wells_d1_05"], \
        "the shipped roof no longer retires the anonymous dwelling on its lot: %s" % found
    assert dry_run(ROOF_FIXTURE) == 0
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
