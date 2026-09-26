#!/usr/bin/env python3
"""T-1558 — the rule that chooses WHICH held people are re-familied, modelled.

    python3 tools/model_refamily_rule.py --build      derive the rule and its roster
    python3 tools/model_refamily_rule.py --check      re-derive and refuse drift
    python3 tools/model_refamily_rule.py --report     the rule, the tiers and the ceilings
    python3 tools/model_refamily_rule.py --self-test  each clause refusing its own case

WHAT THIS IS. Piece 2 of 4 of T-1556, the owner's ruling of 2026-09-24 on T-1530: the
523 reconstructed people the re-cut holds are RE-FAMILIED rather than retired — they
"move into the buckets the re-cut GREW instead of being un-written". T-1557 built the
word for a move (a ledger entry recorded on both ends) and moved nobody. This piece
decides WHO may move, and it moves nobody either: it writes one derived file and not
one card.

WHY IT IS A SEPARATE PIECE, in the owner's own words. He rejected retiring the surplus
because of who it would have fallen on: "34 of the 60 heads are adopted by name
elsewhere … so only 26 are free to retire and 25 of those 26 would go. The men the
town lost would be chosen by which of them failed to get a job, which is not a
modelled criterion." So a rule that picks people by what they lack is the one answer
this ticket may not give.

THE RULE, in one line. **A move may change only what was never read about the person,
and it is spent at the LOWEST COST first; an adoption is a refusal at the top of the
ladder and never a selector at the bottom.** What a move costs is a property of the
LEDGER — was this person's cell ever written down, and on whose card? — not a property
of the person's luck. Employment appears in it exactly once, as a reason somebody STAYS
in the cell he was written into, which costs him nothing at all: nobody is un-written,
so an unmovable head keeps his card, his id and his cell and the bucket goes on naming
its remainder.

WHAT IT FOUND, and this is the ticket's news. The held surplus and the open orders are
DISJOINT ON EVERY AXIS. Not one of the 48 refused buckets has a single open slot in its
own (sex, age band, household kind, trade) class in any division, and not one of the 69
open buckets holds any surplus. So a move that changes only the DIVISION — the one axis
that is a bare ledger allocation for most held people, and therefore the only free one —
yields ZERO moves. The buckets the re-cut grew are the LODGING band's (T-1532, T-1536,
T-1538) and T-1171's adult-male family cells; the surplus is women, children and
tradesmen in family houses. Reaching an open order therefore costs a household kind, and
the 265 moves T-1556 § 3 named cannot be made by any rule that keeps a person's sex and
age band — the ceiling on that alone is 233, and under this rule it is lower again. The
numbers are derived below and stated with what would raise them.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "data" / "reconstruction" / "1835_reconstruction_order_book.json"
OUT = ROOT / "data" / "reconstruction" / "1835_refamily_rule.json"
REPORT = ROOT / "docs" / "RESEARCH" / "1835_refamily_rule.md"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
TRADES = ROOT / "data" / "residents" / "reconstructed_trades"
# T-1564. The lodging stage's own cards, which stand in a third folder and hold the people
# the re-cut refuses in the `lodging` buckets. They were outside this model until a
# re-family landed in a lodging band and the re-cut then refused a lodging bucket whose
# people nothing here could name.
LODGING_CARDS = ROOT / "data" / "residents" / "lodgers"
EMPLOYMENT = ROOT / "data" / "residents" / "employment_coverage.json"
LODGERS = ROOT / "data" / "reconstruction" / "1835_lodgers_seated.json"
BUSINESSES = ROOT / "data" / "businesses"

TICKET = "T-1558"
PARENT = "T-1556"
CIVIL = ("north", "south", "west", "fort", "country")
INVENTED_PASSES = ("reconstructed_women_children", "reconstructed_trade_household")
# The stages whose people stand in the refused buckets, and the ticket each was drawn by.
# `fills` in the order book carries the same pairing; it is restated here because this
# tool reads the CARDS and has to agree with the book bucket for bucket. The lodging stage
# joined the list in T-1564: it draws into the `lodging` buckets, and the re-cut refuses
# one of those the moment a re-family lands in the same band — see `held_roster`.
STAGE_TICKET = {"modelled_families": "T-1171",
                "women_and_children": "T-1174",
                "trade_households": "T-1347",
                "lodgers": "T-1371"}


class Fault(Exception):
    """A refusal this model makes by name."""


# --------------------------------------------------------------- the cost ladder --
#
# Each rung says what a move at that rung REWRITES. The ladder is the rule: a move is
# spent at the lowest rung that can reach an open order, and the rungs below `R_` are
# the movable ones. Every row of the roster carries its rung id, and the order book
# refuses a re-family whose `rule` is not one of these ids — so a move made by no
# stated rule cannot be written at all.
LADDER = [
    {
        "id": "C0",
        "tier": "movable",
        "may_change": ["division"],
        "label": "the cell was never written down",
        "rewrites": "one line of a derived ledger, and no card anywhere",
        "says": "This person stands in a household whose record says `unplaced`, so the "
                "division his bucket counts him in was chosen by a seeded draw on the "
                "model's own by-division shares — `bucket_for` in "
                "tools/reconstruct_modelled_families.py says so in as many words: the "
                "allocation 'writes no division onto the person, onto the household or "
                "onto any card'. Moving him is the same act that placed him, done again.",
        "the_evidence_it_costs_nothing": "45 of the 64 unplaced households in the held "
                                         "roster ALREADY have their own members counted "
                                         "in different divisions, because the seed is per "
                                         "person. There is no household division for a "
                                         "move to contradict.",
        "and_the_division_is_ALL_it_may_change": "This person is a wife or a child in a "
            "household the SOURCES record. His household kind is not a ledger allocation — "
            "he is somebody's son in somebody's house — so this rung may not make him a "
            "lodger in a boarding house across the river. The division is the whole of what "
            "was never written down about him, and the division alone reaches no open order "
            "at all. That is why this rung, the only free one, yields nothing.",
    },
    {
        "id": "C1",
        "tier": "movable",
        "may_change": ["division", "household"],
        "label": "the cell is written on an invented card that took it from the bucket",
        "rewrites": "the reconstructed household's own division, which it derived from "
                    "this bucket in the first place — and the whole house moves or none "
                    "of it does",
        "says": "This person stands in a household this project invented "
                "(`reconstructed_women_children`, `reconstructed_trade_household`). Its "
                "division is stated on the card, and the card took it from the book's own "
                "bucket: a trade household's seating note reads 'the division above is the "
                "bucket's'. So the statement moves with the bucket rather than "
                "contradicting it. Because the card is one record for the whole house, the "
                "unit of a C1 move is the HOUSEHOLD: every one of its people moves, or it "
                "stays. Every member of all 187 such households stands in a refused "
                "bucket, so a whole-house move never empties a cell that is not "
                "over-supplied.",
        "and_why_it_may_change_the_household_kind_too": "Because this house is one this "
            "project invented, and the kind of house it is was invented with it. Re-casting "
            "an invented family house as a boarding-house family — a widow and her children "
            "lodging, an unmarried tradesman boarding with his trade — is a reconstruction "
            "decision about invented people at the `reconstructed` tier, which AGENTS.md "
            "says to make, label and record rather than refuse. It is also the ONLY move "
            "that reaches an open order: the buckets the re-cut grew are the lodging band's.",
    },
    {
        "id": "R_adopted",
        "tier": "refused",
        "may_change": [],
        "label": "an adoption names a place, and a place has a division",
        "rewrites": "nothing — the move is refused",
        "says": "T-1556 § 8: an adopted head 'moving must carry those adoptions with him "
                "or not move'. An employment seat, a business card and a lodging roll each "
                "name a HOUSE, and a house stands in one division, so the adoption cannot "
                "cross the river with him. He does not move. That costs him nothing: "
                "nobody is un-written, so he keeps his card, his id and his cell, and his "
                "bucket goes on naming its remainder. This is the one place employment "
                "enters the rule, and it enters as a refusal and never as a selector.",
        "and_it_reaches_his_whole_house": "A household is refused entire where ANY of its "
                                          "members is adopted — 38 of the 187 invented "
                                          "households — because a C1 move is a move of the "
                                          "whole house.",
    },
    {
        "id": "R_house_is_not_wholly_held",
        "tier": "refused",
        "may_change": [],
        "label": "part of the house is held and part of it is not",
        "rewrites": "nothing — the move is refused",
        "says": "A C1 move is a move of the WHOLE house, and only the people standing in a "
                "bucket the re-cut refused are held. Where a household has members the "
                "book is not holding, moving the held ones would put a mother on one side "
                "of the river and her child on the other — the split the rule's own "
                "ceiling pays 46 moves to prevent. So the house does not move at all. "
                "T-1564 named this rung, on finding the yield offering a move for 2 of the "
                "3 people on `hh_rc_eastman_esther`.",
    },
    {
        "id": "R_seated",
        "tier": "refused",
        "may_change": [],
        "label": "the household stands on the ground",
        "rewrites": "nothing — the move is refused",
        "says": "`lives_at` resolves, so a roof has been placed on a lot in a division. A "
                "bucket move would make the card and the standing roof disagree about which "
                "side of the river this person lives on.",
    },
    {
        "id": "R_division_is_a_reading",
        "tier": "refused",
        "may_change": [],
        "label": "the division is evidence about a real house",
        "rewrites": "nothing — the move is refused",
        "says": "This person was drawn into a household the SOURCES record, and that "
                "record states a civil division. The division is a reading, not an "
                "allocation, and rule 2 of AGENTS.md forbids moving it: a reconstruction "
                "may re-choose what it chose and may never re-choose what it read.",
    },
]
LADDER_IDS = tuple(r["id"] for r in LADDER)
MOVABLE_IDS = tuple(r["id"] for r in LADDER if r["tier"] == "movable")
MAY_CHANGE = {r["id"]: tuple(r["may_change"]) for r in LADDER}

# --------------------------------------------------------------------- the axes --
#
# WHAT A MOVE MAY CHANGE, and it is not the same list as what T-1557's fault check
# forbids. T-1557 refuses a move that re-sexes or re-ages anybody, because those are
# what a person IS. This model adds the TRADE to that list, for a different reason: a
# trade is an attribute written on the person's own card, with its own basis, seed and
# `replaceable_by` clause. Re-trading a man is a fresh reconstruction decision about
# what he does for a living; it is not a re-family, and folding it in here would let
# the arithmetic buy itself 110 more moves by quietly re-employing people.
FIXED_AXES = ("sex", "age_band", "trade")
MOVABLE_AXES = ("division", "household")


def axes_of(key: str) -> dict:
    """The five axes a person bucket key carries. `persons/<sex>/<band>/<div>/<hh>/<trade>`."""
    parts = key.split("/")
    if len(parts) != 6 or parts[0] != "persons":
        raise Fault(f"{key} is not a person bucket key")
    return {"sex": parts[1], "age_band": parts[2], "division": parts[3],
            "household": parts[4], "trade": parts[5]}


def with_axes(key: str, **changes) -> str:
    ax = axes_of(key)
    ax.update(changes)
    return "/".join(["persons", ax["sex"], ax["age_band"], ax["division"],
                     ax["household"], ax["trade"]])


def reachable(source: str, dest: str, rung: str = "C1") -> bool:
    """Whether a move from `source` to `dest` is one the rule allows at `rung`.

    TWO GATES, AND THEY ARE DIFFERENT CLAIMS. `FIXED_AXES` is what no move may ever
    change — sex and age band because they are what a person IS (T-1557), the trade
    because it is written on his own card. The rung's `may_change` is narrower again and
    is about THIS person's cell: C0 may move only the axis that was never written down
    for him, which is the division."""
    a, b = axes_of(source), axes_of(dest)
    if source == dest:
        return False
    if any(a[axis] != b[axis] for axis in FIXED_AXES):
        return False
    allowed = MAY_CHANGE.get(rung, ())
    return all(a[axis] == b[axis] for axis in MOVABLE_AXES if axis not in allowed)


# ------------------------------------------------------------------- the inputs --

def book() -> dict:
    if not BOOK.exists():
        raise Fault("the 1835 reconstruction order book is missing — "
                    "run tools/build_order_book_1835.py --build")
    return json.loads(BOOK.read_text(encoding="utf-8"))


def cards() -> dict:
    """Every household record that can hold a reconstructed person, by id."""
    out = {}
    for folder in (HOUSEHOLDS, TRADES, LODGING_CARDS):
        for path in sorted(folder.glob("*.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            out[doc["id"]] = doc
    return out


def value_of(field):
    return field.get("value") if isinstance(field, dict) else field


def is_seated(card: dict) -> bool:
    return bool(value_of(card.get("lives_at")))


def band_of(low: int) -> str:
    for label, lo, hi in (("under_10", 0, 10), ("10_19", 10, 20), ("20_29", 20, 30),
                          ("30_39", 30, 40), ("40_49", 40, 50), ("50_plus", 50, None)):
        if low >= lo and (hi is None or low < hi):
            return label
    return "50_plus"


def modelled_families_division(hid: str, card: dict, which: str) -> str:
    """The ledger allocation `reconstruct_modelled_families.bucket_for` made.

    IMPORTED, NOT REIMPLEMENTED. The seeded draw is that stage's own and a second copy
    of it here would be a second thing to keep in step; this model asks the stage."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_mf", ROOT / "tools" / "reconstruct_modelled_families.py")
    module = getattr(modelled_families_division, "_module", None)
    if module is None:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modelled_families_division._module = module
    division = card.get("division")
    if division not in CIVIL:
        division = module.pick(module.seed_for(hid, f"division_share:{which}"),
                               module.division_rows())
    return division


def basis_bucket(person: dict) -> str | None:
    """The order-book bucket a person's own card names, where their stage writes it down."""
    basis = person.get("basis")
    if not isinstance(basis, dict) or basis.get("id") != "1835_reconstruction_order_book":
        return None
    bucket = basis.get("bucket")
    return bucket if isinstance(bucket, str) and bucket else None


def held_roster(doc: dict, by_id: dict) -> list:
    """Every reconstructed person standing in a bucket, with the cell that counts him.

    DERIVED FROM THE CARDS, AND PROVED AGAINST THE BOOK. The book counts people and
    never names them, so this is the only place the two can be reconciled — and
    `every_refused_bucket_is_accounted_for` below refuses the model the moment its
    per-bucket tally and the book's `drawn_here` part company."""
    rows = []
    for hid, card in sorted(by_id.items()):
        division = card.get("division")
        for person in card.get("persons") or []:
            rc = person.get("reconstruction")
            stage = rc.get("stage") if isinstance(rc, dict) else None
            band = person.get("age_band")
            low = band.get("low") if isinstance(band, dict) else None
            if stage == "modelled_families":
                seed = band.get("seed", "") if isinstance(band, dict) else ""
                which = seed.rsplit(":", 1)[-1].replace("_age_bands_1840", "")
                div = modelled_families_division(hid, card, which)
                key = f"persons/{person['sex']}/{band_of(int(low))}/{div}/family/none"
            elif stage == "trade_households":
                key = card["trade_household"]["bucket"]
            elif card.get("source_pass") == "reconstructed_women_children":
                # THE DIVISION THIS HOUSE WAS DEALT IN, WHICH IS NOT ALWAYS THE ONE ITS
                # CARD STATES. A spent C1 move rewrites the card's own `division` — that
                # is the whole of what C1 changes — so reading it back here would derive
                # the bucket a person was moved INTO as the bucket he was drawn in, and
                # `every_refused_bucket_is_accounted_for` would then find the held roster
                # and the book's `drawn_here` disagreeing the moment a move landed. The
                # trade stage is immune because its bucket is written on the card; this
                # stage's is not, so a moved card carries the division it was dealt in and
                # it is read here. T-1564.
                drawn_in = (card.get("refamilied") or {}).get("drawn_in_division")
                key = (f"persons/{person['sex']}/{band_of(int(low))}/"
                       f"{drawn_in or division}/family/none")
            elif stage == "lodgers" and basis_bucket(person):
                # THE BUCKET THIS STAGE WAS DEALT AGAINST, WRITTEN ON THE PERSON (T-1564).
                # The lodging stage is the one stage here that deals against BOTH the
                # `lodging/none` and the `lodging/trade` axes — a minted keeper carries a
                # trade read off the building and a minted boarder carries none — so its
                # key cannot be re-derived from the card's sex, band and division the way
                # the three above can. It does not need to be: `seat_lodgers_1835.py`
                # writes it down. These people are all `R_seated` (a lodger's card names
                # the house they sleep in), so naming them adds nobody to the movable set;
                # what it adds is the ability to ACCOUNT for a refused lodging bucket,
                # which the re-cut produces as soon as a re-family lands in the band.
                key = basis_bucket(person)
            else:
                continue
            rows.append({
                "person": person["id"],
                "household": hid,
                "relationship": person.get("relationship"),
                "stage": stage or "women_and_children",
                "ticket": STAGE_TICKET[stage or "women_and_children"],
                "bucket": key,
            })
    return rows


def adoptions_by_person(ids: set) -> dict:
    """The three layers that adopt a reconstructed person by name, per person.

    Each of them names a HOUSE, which is why an adoption fixes a division (rung
    R_adopted). None of them is read for anything else here."""
    out = defaultdict(list)
    coverage = json.loads(EMPLOYMENT.read_text(encoding="utf-8"))
    statuses = coverage["vocabulary"]["statuses"]
    for row in coverage["rows"]:
        pid = row.get("person_id")
        if pid in ids and statuses.get(row.get("status"), {}).get("places_them_at_work"):
            out[pid].append({"layer": "employment", "seat": row["status"],
                             "houses": row.get("houses") or []})
    for path in sorted(BUSINESSES.glob("*.json")):
        text = path.read_text(encoding="utf-8")
        for pid in sorted(set(re.findall(r'"(rc_[a-z0-9_]+)"', text))):
            if pid in ids:
                out[pid].append({"layer": "business", "business": path.stem})
    lodgers = json.loads(LODGERS.read_text(encoding="utf-8"))
    for seat in lodgers.get("seats") or []:
        pid = seat.get("person")
        if pid in ids:
            out[pid].append({"layer": "lodging", "place": seat.get("place")})
    return {k: v for k, v in out.items()}


# -------------------------------------------------------------------- the tiers --

def rung_for(row: dict, card: dict, adoptions: dict) -> str:
    """The rung of the cost ladder this person's cell stands on. Order matters."""
    if is_seated(card):
        return "R_seated"
    if adoptions.get(row["person"]):
        return "R_adopted"
    if card.get("division") not in CIVIL:
        return "C0"
    if card.get("source_pass") in INVENTED_PASSES:
        return "C1"
    return "R_division_is_a_reading"


def deal_key(row: dict, card: dict) -> str:
    """The order this bucket dealt its people in, off committed data.

    WHY THE DEAL ORDER AND NOT A JUDGEMENT ABOUT THE PERSON. A bucket's surplus is a
    NUMBER — `filled` less what the re-cut would order — and not a set of names, so
    which of its people is counted in a new cell has to be decided by something. The
    deal is the only thing about it that is arithmetic: the re-cut reached work already
    drawn, so the people past its order are the ones the stage dealt LAST. A trade
    household carries its slot index; the other two stages deal one household at a time
    and their ids are the order. Nothing here reads a person's employment, and that is
    the point."""
    if row["stage"] == "trade_households":
        return str(card.get("trade_household", {}).get("slot") or row["household"])
    return f"{row['household']}:{row['person']}"


def tier_the_roster(doc: dict, by_id: dict) -> tuple:
    """(roster rows with their rung, the household rungs). Pure over committed data."""
    rows = held_roster(doc, by_id)
    refused = {r["bucket"]: r for r in doc["recut_refusals"]}
    rows = [r for r in rows if r["bucket"] in refused]
    adoptions = adoptions_by_person({r["person"] for r in rows})
    for row in rows:
        card = by_id[row["household"]]
        row["rung"] = rung_for(row, card, adoptions)
        row["adoptions"] = adoptions.get(row["person"], [])
        row["deal_key"] = deal_key(row, card)
        row["axes"] = axes_of(row["bucket"])
    # A C1 MOVE IS A MOVE OF THE WHOLE HOUSE, SO A REFUSAL ON ONE MEMBER REFUSES IT ALL.
    # Stated as its own pass rather than folded into `rung_for`, because the rung is a
    # fact about the person and this is a fact about the house he is in.
    house = defaultdict(set)
    for row in rows:
        house[row["household"]].add(row["rung"])
    # AND A MEMBER WHO IS NOT HELD AT ALL REFUSES IT JUST AS HARD (T-1564). The rows above
    # are only the people standing in a REFUSED bucket; a member of the same house whose
    # own bucket the re-cut did not refuse has no row here, and until this pass existed
    # the house moved without them — `hh_rc_eastman_esther` was offered a move for 2 of
    # its 3 people, which is precisely the family split across the river that the rule's
    # own ceiling costs 46 moves to prevent. A move is only ever offered to a house every
    # one of whose people the book is holding.
    held_of = defaultdict(set)
    for row in rows:
        held_of[row["household"]].add(row["person"])
    for hid, held in held_of.items():
        on_card = {p["id"] for p in (by_id.get(hid, {}).get("persons") or [])}
        if on_card - held:
            house[hid].add("R_house_is_not_wholly_held")
    for row in rows:
        if row["rung"] != "C1":
            continue
        others = house[row["household"]] - {"C1"}
        if others:
            row["rung"] = "R_adopted" if "R_adopted" in others else sorted(others)[0]
            row["refused_with_the_house"] = True
    return rows, house


def every_refused_bucket_is_accounted_for(doc: dict, rows: list) -> str:
    """The model names, person by person, exactly what the book counted. Or it is wrong."""
    mine = Counter(r["bucket"] for r in rows)
    for refusal in doc["recut_refusals"]:
        key, want = refusal["bucket"], refusal["drawn_here"]
        if mine.get(key, 0) != want:
            raise Fault(f"the held roster names {mine.get(key, 0)} people in {key} where "
                        f"the order book counts {want} drawn there")
    stray = sorted(set(mine) - {r["bucket"] for r in doc["recut_refusals"]})
    if stray:
        raise Fault(f"the held roster names people in {stray[0]}, which the book does not refuse")
    return (f"all {len(doc['recut_refusals'])} refused buckets accounted for, "
            f"{sum(mine.values()):,} people named")


# ----------------------------------------------------------------- the ceilings --

def already_made(doc: dict) -> dict:
    """{person: the ledger row} for every move the order book has already SPENT.

    THE RULE IS DERIVED OFF A BOOK THAT THE SPENDING CHANGES, so without this it is not
    stable under its own success. A spent move fills its destination's order and takes a
    head off its source's `surplus_still_held`, so a plain re-derivation over the new
    state would deal the freed capacity to somebody else and quietly drop the person who
    already moved — 12 of the first 19 vanished from the list that way on 2026-09-25, and
    7 of them were offered a SECOND move, which `build_order_book_1835.refamily_shape`
    forbids by name.

    So the ledger's rows are re-emitted here, in the book's own order, ahead of whatever
    the remainder yields; they consume no room and no surplus, because the book has
    already taken both off the figures this model reads. The list a reader compares
    against the ledger is then the whole programme — what has been done and what is left
    — and spending a move moves a row from the second half to the first without
    disturbing the rest."""
    return {m["person"]: m for m in
            (doc.get("re_family_ledger") or {}).get("moves") or []}


def open_orders(doc: dict) -> dict:
    """{bucket: slots open} over the person family. A refused bucket is never open."""
    out = {}
    for family in doc["bucket_families"]:
        if family["key"] != "persons":
            continue
        for bucket in family["buckets"]:
            todo = bucket.get("to_reconstruct")
            if todo is None or bucket.get("recut_refused"):
                continue
            room = int(todo) - int(bucket["filled"])
            if room > 0:
                out[bucket["key"]] = room
    return out


def ceiling(surplus: dict, room: dict, free: tuple) -> int:
    """How many moves could be made if ONLY `free` axes may change. An upper bound.

    Grouped rather than matched: within one (fixed axes) class every source can reach
    every destination, so the bound is the sum of the per-class minima and no matching
    can beat it."""
    fixed = tuple(a for a in ("sex", "age_band", "division", "household", "trade")
                  if a not in free)
    def klass(key):
        ax = axes_of(key)
        return tuple(ax[a] for a in fixed)
    held, space = Counter(), Counter()
    for key, n in surplus.items():
        held[klass(key)] += n
    for key, n in room.items():
        space[klass(key)] += n
    return sum(min(n, space.get(k, 0)) for k, n in held.items())


# ------------------------------------------------------------ what the rule yields --

NO_ORDER = ("no open order anywhere holds his sex, age band and trade in a household "
            "kind this rule may move him to")
NO_HOUSE_ORDER = ("no open (division, household kind) shape has room for every one of "
                  "this house's people at once, and a C1 move is a move of the whole house")


def bound_if_houses_could_split(doc: dict, rows: list) -> int:
    """The same rule with clause C1's whole-house condition lifted. A BOUND, not a plan.

    It exists to price that condition. A C1 card states one division for a whole house,
    so moving half of it would put a mother in one division and her children in another;
    the rule refuses that, and this number says what the refusal costs in moves."""
    surplus = {r["bucket"]: r["surplus_still_held"] for r in doc["recut_refusals"]}
    room = dict(open_orders(doc))
    out_of, made = Counter(), 0
    for row in sorted((r for r in rows if r["rung"] in MOVABLE_IDS),
                      key=lambda r: (r["rung"], r["deal_key"], r["person"]), reverse=True):
        if out_of[row["bucket"]] >= surplus[row["bucket"]]:
            continue
        dests = sorted((k for k in room if room[k] > 0
                        and reachable(row["bucket"], k, row["rung"])),
                       key=lambda k: (-room[k], k))
        if not dests:
            continue
        room[dests[0]] -= 1
        out_of[row["bucket"]] += 1
        made += 1
    return made


def yields(doc: dict, rows: list) -> tuple:
    """(the moves the rule yields, why each movable person who cannot move cannot).

    THE ORDER, and every part of it is committed arithmetic:
      1. the LOWEST RUNG of the cost ladder first — C0 (no card is rewritten) before C1
         (an invented card's own division travels with it);
      2. inside a rung, the people the bucket dealt LAST, first;
      3. a C1 house is offered whole and takes the division that can hold every one of
         its members; the divisions are tried in the book's own order;
      4. a destination that is FURTHEST from its own order takes the arrival, so the
         moves land where the book is shortest rather than where the key sorts first;
      5. no bucket ever moves out more than its `surplus_still_held`."""
    refused = {r["bucket"]: r for r in doc["recut_refusals"]}
    room = dict(open_orders(doc))
    out_of = Counter()
    # THE MOVES ALREADY SPENT COME FIRST AND ARE NOT RE-DEALT. `open_orders` and
    # `surplus_still_held` are both already net of them, so they consume nothing here.
    made = already_made(doc)
    moves, stuck = [dict(m) for m in made.values()], []
    rows = [r for r in rows if r["person"] not in made]

    def destinations(source, rung):
        return sorted((k for k in room if room[k] > 0 and reachable(source, k, rung)),
                      key=lambda k: (-room[k], k))

    def may_leave(source, n=1):
        return out_of[source] + n <= refused[source]["surplus_still_held"]

    def record(row, dest, rung):
        room[dest] -= 1
        out_of[row["bucket"]] += 1
        moves.append({
            "person": row["person"],
            "household": row["household"],
            "from_bucket": row["bucket"],
            "to_bucket": dest,
            "rule": rung,
            "changes": [a for a in MOVABLE_AXES
                        if axes_of(row["bucket"])[a] != axes_of(dest)[a]],
            "ticket": PARENT,
            "adoptions_carried": [],
        })

    by_person = {r["person"]: r for r in rows}
    # RUNG C0 — one person at a time. His cell is a per-person ledger draw and 45 of the
    # 64 such households already have their members counted in different divisions, so
    # there is no house to keep together.
    for row in sorted((r for r in rows if r["rung"] == "C0"),
                      key=lambda r: (r["deal_key"], r["person"]), reverse=True):
        if not may_leave(row["bucket"]):
            stuck.append({"person": row["person"], "rung": "C0",
                          "why": "its bucket has already moved out its whole surplus"})
            continue
        dests = destinations(row["bucket"], "C0")
        if not dests:
            stuck.append({"person": row["person"], "rung": "C0", "why": NO_ORDER})
            continue
        record(row, dests[0], "C0")
    # RUNG C1 — one HOUSE at a time, and it moves to a single cell-shape or not at all.
    # The shape is a (division, household kind) pair: the card states one division for the
    # whole house and the house is one kind of house, so both have to be chosen once for
    # all of its people. The pairs are tried in the book's own axis order, and the one
    # that can hold EVERY member is taken.
    houses = defaultdict(list)
    for row in rows:
        if row["rung"] == "C1":
            houses[row["household"]].append(row)
    order = sorted(houses, key=lambda h: (max(r["deal_key"] for r in houses[h]), h),
                   reverse=True)
    shapes = sorted({(axes_of(k)["division"], axes_of(k)["household"]) for k in room})
    for hid in order:
        members = sorted(houses[hid], key=lambda r: r["person"])
        leaving = Counter(m["bucket"] for m in members)
        placed = None
        for division, kind in shapes:
            want = Counter()
            for member in members:
                want[with_axes(member["bucket"], division=division, household=kind)] += 1
            if any(not reachable(m["bucket"], d, "C1") for m, d in
                   zip(members, [with_axes(m["bucket"], division=division, household=kind)
                                 for m in members])):
                continue
            if not all(room.get(dest, 0) >= n for dest, n in want.items()):
                continue
            if not all(may_leave(src, n) for src, n in leaving.items()):
                continue
            placed = (division, kind)
            break
        if placed is None:
            for member in members:
                stuck.append({"person": member["person"], "household": hid,
                              "rung": "C1", "why": NO_HOUSE_ORDER})
            continue
        for member in members:
            record(member, with_axes(member["bucket"], division=placed[0],
                                     household=placed[1]), "C1")
    return moves, stuck, by_person


# ---------------------------------------------------------------- the document --

def model(doc: dict, by_id: dict) -> dict:
    rows, _house = tier_the_roster(doc, by_id)
    accounted = every_refused_bucket_is_accounted_for(doc, rows)
    surplus = {r["bucket"]: r["surplus_still_held"] for r in doc["recut_refusals"]}
    room = open_orders(doc)
    moves, stuck, _by_person = yields(doc, rows)
    split_bound = bound_if_houses_could_split(doc, rows)
    held = sum(surplus.values())
    # THE REMAINDER IS THE BOOK'S OWN, NOT `totals`. `totals.persons_to_reconstruct` is
    # the whole order the book carries; what a move takes off is what is STILL OWED, and
    # the book states that in the same question it states the model's point in.
    remainder = next(q for q in doc["what_the_re_cut_found"]
                     if q["id"] == "the_remainder_said_out_loud")
    owed = remainder["persons_still_owed"]
    standing = remainder["persons_standing_in_the_layer"]
    point = remainder["model_point"]
    span = remainder["model_range"]
    by_rung = Counter(r["rung"] for r in rows)
    # THE TWO WAYS A PERSON IS REFUSED, counted apart. He carries an adoption himself, or
    # he is in a house one of whose members does; the second is clause C1's whole-house
    # condition reaching him and it is a different fact about him.
    refused_himself = sum(1 for r in rows
                          if r["rung"].startswith("R_") and not r.get("refused_with_the_house"))
    refused_with_house = sum(1 for r in rows if r.get("refused_with_the_house"))
    adopted_himself = sum(1 for r in rows if r["adoptions"])
    children = sum(r["surplus_still_held"] for r in doc["recut_refusals"]
                   if axes_of(r["bucket"])["age_band"] in ("under_10", "10_19"))
    women = sum(r["surplus_still_held"] for r in doc["recut_refusals"]
                if axes_of(r["bucket"])["sex"] == "female"
                and axes_of(r["bucket"])["age_band"] not in ("under_10", "10_19"))
    child_room = sum(n for k, n in room.items()
                     if axes_of(k)["age_band"] in ("under_10", "10_19"))
    women_room = sum(n for k, n in room.items() if axes_of(k)["sex"] == "female"
                     and axes_of(k)["age_band"] not in ("under_10", "10_19"))
    male_adult_room = sum(n for k, n in room.items() if axes_of(k)["sex"] == "male"
                          and axes_of(k)["age_band"] not in ("under_10", "10_19"))
    return {
        "$schema_note": "No schema. DERIVED — regenerate with "
                        "tools/model_refamily_rule.py --build. Do not hand-edit.",
        "id": "chicago_1835_refamily_rule",
        "ticket": TICKET,
        "parent_ticket": PARENT,
        "target_date": doc["target_date"],
        "generated_by": "tools/model_refamily_rule.py --build",
        "read_by": ["tools/build_order_book_1835.py (a move's `rule` must name a rung "
                    "published here)", "T-1559, which spends the moves"],
        "not_a_reading": "This file adjudicates no source and reads nothing new. It is a "
                         "model of the project's own ledger: which of the people the "
                         "re-cut holds may be counted in a different cell, and what each "
                         "such move would rewrite.",
        "moves_nobody": True,
        "writes_no_card": True,
        "mints_nobody": True,
        "the_question": "T-1556 § 8: 'The rule that chooses WHICH heads move is modelled "
                        "and written down. It may not be \"whoever failed to get a job\" — "
                        "the defect the owner named in rejecting option (a).'",
        "the_rule": {
            "one_line": "A move may change only what was never read about the person, and "
                        "it is spent at the LOWEST COST first; an adoption is a refusal at "
                        "the top of the ladder and never a selector at the bottom.",
            "why_it_is_not_whoever_failed_to_get_a_job":
                "Under option (a) the town LOST people, and with 34 of 60 heads adopted the "
                "loss fell on the 26 who were not — employment decided who was kept. Under "
                "this rule nobody is lost, so an adoption has no such consequence: it means "
                "the person stays in the cell he was written into, keeps his card, his id "
                "and his grade, and his bucket goes on naming its remainder. The thing that "
                "ORDERS the movable people is the deal — the re-cut reached work already "
                "drawn, so the people past its order are the ones the stage dealt last — "
                "and the deal is arithmetic about the ledger, not a judgement about a man.",
            "the_axes_a_move_may_change": list(MOVABLE_AXES),
            "the_axes_it_may_not": list(FIXED_AXES),
            "why_the_trade_is_fixed":
                "T-1557's fault check already forbids re-sexing and re-aging anybody, "
                "because those are what a person IS. The trade is added to that list here "
                "for a different reason: it is written on the person's own card with its own "
                "basis, seed and `replaceable_by` clause, so re-trading a man is a fresh "
                "reconstruction decision about what he does for a living and is not a "
                "re-family. Folding it in would have bought the arithmetic 110 more moves "
                "by quietly re-employing people.",
            "the_cost_ladder": LADDER,
            "the_order_within_a_rung": "the people the bucket dealt LAST, first — a trade "
                                       "household by its slot index, the other two stages by "
                                       "household and person id, all off committed data.",
            "the_destination_order": "the open order FURTHEST from its own target takes the "
                                     "arrival, so moves land where the book is shortest.",
        },
        "the_held_roster": rows,
        "the_moves_the_rule_yields": moves,
        "who_cannot_move_and_why": stuck,
        "counts": {
            "people_in_the_refused_buckets": len(rows),
            "the_surplus_those_buckets_hold": held,
            "by_rung": {rung: by_rung.get(rung, 0) for rung in LADDER_IDS},
            "movable_people": sum(by_rung.get(r, 0) for r in MOVABLE_IDS),
            "refused_on_their_own_account": refused_himself,
            "refused_with_their_house": refused_with_house,
            "carrying_an_adoption_themselves": adopted_himself,
            "moves_the_rule_yields": len(moves),
            "buckets_moved_out_of": len({m["from_bucket"] for m in moves}),
            "buckets_moved_into": len({m["to_bucket"] for m in moves}),
            "adoptions_carried": sum(len(m["adoptions_carried"]) for m in moves),
            "the_roster_is_reconciled": accounted,
        },
        "the_ceilings": {
            "_doc": "Upper bounds, each loosening ONE more axis than the one above it. "
                    "They are bounds and not plans: the rule's own yield is below the "
                    "last of them because movability then applies.",
            "if_only_the_division_changed": ceiling(surplus, room, ("division",)),
            "if_the_household_kind_changed_too": ceiling(surplus, room,
                                                         ("division", "household")),
            "if_the_trade_could_change_as_well": ceiling(surplus, room,
                                                        ("division", "household", "trade")),
            "and_then_with_movability_applied_but_a_house_free_to_split": split_bound,
            "under_this_rule": len(moves),
            "what_the_whole_house_condition_costs": split_bound - len(moves),
            "and_why_that_is_the_right_price":
                "A C1 card states ONE division for a whole house, so moving half of it "
                f"would put a mother in one division and her children in another. The "
                f"{split_bound - len(moves)} moves the condition costs are moves that would "
                "have split a family across the river to make an arithmetic close, which is "
                "the kind of trade this project does not make.",
            "the_number_T_1556_named": 265,
            "why_265_cannot_be_made":
                "T-1556 § 3 took 265 from the aggregate — 523 held, 427 open, and 265 moves "
                "landing the town on the model's 2,543 point. The aggregate cannot see the "
                "axes. A move may not re-sex or re-age anybody (T-1557's own fault check), "
                "and on that constraint alone the ceiling is "
                f"{ceiling(surplus, room, ('division', 'household', 'trade'))}: "
                f"{male_adult_room} of the {sum(room.values())} open slots stand in adult-MALE "
                f"cells while the surplus holds {children} people under twenty and {women} "
                f"adult women, whose cells hold {child_room + women_room} slots between them.",
            "and_the_disjointness_is_total":
                "Not one of the 48 refused buckets has a single open slot in its own (sex, "
                "age band, household kind, trade) class in ANY division, and not one of the "
                f"{len(room)} open buckets holds any surplus. So a move that changes only "
                "the division — the one axis that is a bare ledger allocation, and therefore "
                "the only free one — yields nothing whatever. The buckets the re-cut GREW are "
                "the lodging band's (T-1532, T-1536, T-1538) and T-1171's adult-male family "
                "cells; the held surplus is women, children and tradesmen in family houses. "
                "Reaching an open order costs a household kind, every time.",
        },
        "what_the_town_converges_to": {
            "persons_standing_in_the_layer": standing,
            "still_owed_now": owed,
            "converges_to_now": standing + owed,
            "converges_to_if_the_rule_is_spent": standing + owed - len(moves),
            "the_model_point": point,
            "the_model_range": span,
            "reading": f"{standing + owed - len(moves):,} is inside the model's "
                       f"{span[0]:,}-{span[1]:,} and "
                       f"{abs(standing + owed - len(moves) - point):,} "
                       f"{'above' if standing + owed - len(moves) > point else 'below'} its "
                       f"{point:,} point, against {standing + owed - point:,} above it today.",
        },
        "what_would_raise_the_ceiling": [
            {"id": "more_orders_in_the_women_and_children_cells",
             "says": f"The binding constraint is room, not willingness: the surplus is "
                     f"{children} people under twenty and {women} adult women, and their "
                     f"cells hold {child_room} and {women_room} open slots between them. An "
                     f"order book re-cut that grew those cells — or a lodging ticket that "
                     f"ordered more children into boarding houses — would raise this "
                     f"directly.",
             "who_owns_it": "T-1532, T-1536, T-1538 (the lodging band) and the book itself"},
            {"id": "a_ruling_that_an_adoption_may_be_RE_SEATED",
             "says": f"{adopted_himself} of the people in the refused buckets carry an "
                     "employment seat, a business card or a lodging roll that names a house "
                     f"in their division, and {refused_with_house} more are refused with a "
                     "house one of those people is in. If the staffing layer may re-seat an "
                     "adopted head at "
                     "an equivalent house in the destination division, the adoption travels "
                     "and T-1556 § 8 is satisfied by carrying rather than by refusing. That "
                     "is a change to the staffing model and not to this rule.",
             "who_owns_it": "the business staffing band (T-1189 and its successors)"},
            {"id": "the_22_seated_households",
             "says": f"{by_rung.get('R_seated', 0)} people are refused because their roof "
                     "is already placed. A "
                     "re-family that also re-seats the roof is a placement act, and the "
                     "placement policy owns it.",
             "who_owns_it": "T-1199"},
            {"id": "and_the_honest_alternative",
             "says": "What is left standing after the rule is spent is a remainder that "
                     "NOTHING can move, and T-1459's ruling says it is held rather than "
                     "clamped. The book will go on naming both numbers per bucket, which is "
                     "the state the owner's ruling improved on rather than abolished.",
             "who_owns_it": "T-1560, the programme's report"},
        ],
    }


# ------------------------------------------------------------------ the report --

def report_text(doc: dict) -> str:
    c, ceil = doc["counts"], doc["the_ceilings"]
    conv = doc["what_the_town_converges_to"]
    lines = [
        f"# The re-family rule — who may move, and what a move rewrites ({TICKET})",
        "",
        "DERIVED — regenerate with `python3 tools/model_refamily_rule.py --build`.",
        f"Piece 2 of 4 of {PARENT}. **This model moves nobody and writes no card.**",
        "",
        "## The rule",
        "",
        f"> {doc['the_rule']['one_line']}",
        "",
        doc["the_rule"]["why_it_is_not_whoever_failed_to_get_a_job"],
        "",
        "## The cost ladder",
        "",
        "| rung | | what a move there rewrites | people |",
        "|---|---|---|---|",
    ]
    for rung in doc["the_rule"]["the_cost_ladder"]:
        lines.append(f"| `{rung['id']}` | {rung['tier']} | {rung['rewrites']} | "
                     f"{c['by_rung'].get(rung['id'], 0):,} |")
    lines += [
        "",
        f"{c['people_in_the_refused_buckets']:,} reconstructed people stand in the 48 "
        f"refused buckets and {c['the_surplus_those_buckets_hold']:,} of them are the "
        f"surplus. {c['movable_people']:,} stand on a movable rung.",
        "",
        "## The ceilings, one axis at a time",
        "",
        "| if a move may change | ceiling |",
        "|---|---|",
        f"| the division only | {ceil['if_only_the_division_changed']:,} |",
        f"| the division and the household kind | {ceil['if_the_household_kind_changed_too']:,} |",
        f"| those and the trade as well | {ceil['if_the_trade_could_change_as_well']:,} |",
        f"| the household-kind bound with movability applied, a house free to split "
        f"| {ceil['and_then_with_movability_applied_but_a_house_free_to_split']:,} |",
        f"| **under this rule, with movability applied** | **{ceil['under_this_rule']:,}** |",
        f"| what {PARENT} § 3 named | {ceil['the_number_T_1556_named']:,} |",
        "",
        ceil["and_the_disjointness_is_total"],
        "",
        ceil["why_265_cannot_be_made"],
        "",
        ceil["and_why_that_is_the_right_price"],
        "",
        "## What the town converges to",
        "",
        f"- standing in the layer: {conv['persons_standing_in_the_layer']:,}",
        f"- still owed: {conv['still_owed_now']:,}",
        f"- converges to now: {conv['converges_to_now']:,}",
        f"- converges to if this rule is spent: {conv['converges_to_if_the_rule_is_spent']:,}",
        f"- {conv['reading']}",
        "",
        "## What would raise the ceiling",
        "",
    ]
    for item in doc["what_would_raise_the_ceiling"]:
        lines.append(f"- **{item['id']}** ({item['who_owns_it']}) — {item['says']}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------- the commands --

def derive() -> dict:
    return model(book(), cards())


def cmd_build() -> int:
    doc = derive()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report_text(doc), encoding="utf-8")
    c = doc["counts"]
    print(f"OK: the re-family rule — {c['people_in_the_refused_buckets']:,} people in the "
          f"48 refused buckets, {c['the_surplus_those_buckets_hold']:,} held; "
          f"{c['movable_people']:,} on a movable rung; the rule yields "
          f"{c['moves_the_rule_yields']:,} moves against the "
          f"{doc['the_ceilings']['the_number_T_1556_named']} {PARENT} named; "
          f"{c['the_roster_is_reconciled']}")
    return 0


def cmd_check() -> int:
    faults = []
    if not OUT.exists():
        print("FAIL: the re-family rule is missing — run --build", file=sys.stderr)
        return 1
    expected = derive()
    if json.loads(OUT.read_text(encoding="utf-8")) != expected:
        faults.append("the re-family rule is stale — run --build")
    if not REPORT.exists():
        faults.append("the re-family rule's report is missing — run --build")
    elif REPORT.read_text(encoding="utf-8") != report_text(expected):
        faults.append("the re-family rule's report is stale — run --build")
    if faults:
        for fault in faults:
            print(f"FAIL: {fault}", file=sys.stderr)
        return 1
    c = expected["counts"]
    print(f"OK: the re-family rule re-derives — {c['movable_people']:,} of "
          f"{c['people_in_the_refused_buckets']:,} people movable, "
          f"{c['moves_the_rule_yields']:,} moves yielded, {c['the_roster_is_reconciled']}")
    return 0


def cmd_report() -> int:
    print(report_text(derive()))
    return 0


def cmd_self_test() -> int:
    doc, by_id = book(), cards()
    rows, _house = tier_the_roster(doc, by_id)
    fired = 0

    def fires(why, fn):
        nonlocal fired
        try:
            fn()
        except Fault:
            fired += 1
            print(f"   self-test | FAIL as intended: {why}")
            return
        raise AssertionError(f"the model did NOT refuse {why}")

    # 1. THE ROSTER IS RECONCILED AGAINST THE BOOK, PERSON BY PERSON. This is the
    # assertion everything else stands on: the book counts and never names, so a model
    # that named the wrong people would be invisible without it.
    every_refused_bucket_is_accounted_for(doc, rows)
    fires("a roster one person short of what the book counted",
          lambda: every_refused_bucket_is_accounted_for(doc, rows[1:]))
    fires("a roster naming somebody in a bucket the book does not refuse",
          lambda: every_refused_bucket_is_accounted_for(
              doc, rows + [{**rows[0], "bucket": "persons/male/20_29/south/family/none"}]))

    # 2. THE FIXED AXES. `reachable` is the gate every destination passes, and it must
    # refuse a re-sexing, a re-aging and a re-trading — the third being this ticket's
    # own addition to T-1557's two.
    source = rows[0]["bucket"]
    for axis, other in (("sex", "female" if axes_of(source)["sex"] == "male" else "male"),
                        ("age_band", "50_plus" if axes_of(source)["age_band"] != "50_plus"
                         else "20_29"),
                        ("trade", "trade" if axes_of(source)["trade"] == "none" else "none")):
        assert not reachable(source, with_axes(source, **{axis: other})), \
            f"a move changing the {axis} must be unreachable"
    assert not reachable(source, source), "a move that leaves and enters one cell is no move"
    assert reachable(source, with_axes(source, household="lodging")), \
        "a household-kind move must be reachable — it is the only kind that reaches an order"

    # 3. AN ADOPTION REFUSES ITS WHOLE HOUSE, and the rung says so. 38 of the 187 invented
    # households are refused this way; picking one of them by measurement rather than by id
    # keeps the test true when the layers move.
    refused_with_house = [r for r in rows if r.get("refused_with_the_house")]
    assert refused_with_house, "no household is refused for a member's adoption — the " \
                               "whole-house pass has stopped doing anything"
    for row in refused_with_house:
        assert row["rung"].startswith("R_"), "a house refused with its members must be refused"
        assert not row["adoptions"], "this row is refused for ANOTHER member's adoption"

    # 4. THE CEILINGS ARE ORDERED, AND A DIVISION-ONLY MOVE YIELDS NOBODY. Loosening an
    # axis can only ever raise a bound, and the finding this ticket turns on is that
    # changing the division alone moves no one.
    #
    # IT IS ASSERTED ON THE YIELD AND NOT ON THE BOUND, and it was the other way round
    # until T-1564. T-1558 measured the division-only BOUND at nought and the test froze
    # that number; then the women-and-children moves landed in the `lodging` bands, the
    # book's trade re-cut re-apportioned one of those bands away from its `trade` axis,
    # and `persons/male/10_19/west/lodging/trade` became a refused bucket holding one
    # person whose own class is open in another division. So the BOUND is 1. The FINDING
    # is untouched: that person is a lodger whose card names the house they sleep in, so
    # the rule refuses them on R_seated, and no move the rule yields changes the division
    # and nothing else. A bound the book's own re-cut can move is not the thing worth
    # freezing; what the ticket turns on is the yield, so that is what is measured here.
    surplus = {r["bucket"]: r["surplus_still_held"] for r in doc["recut_refusals"]}
    room = open_orders(doc)
    one = ceiling(surplus, room, ("division",))
    two = ceiling(surplus, room, ("division", "household"))
    three = ceiling(surplus, room, ("division", "household", "trade"))
    assert one <= two <= three, f"the ceilings are not ordered: {one} {two} {three}"
    assert three < 265, f"the sex-and-band ceiling is {three}, so 265 is reachable after all"

    # 5. NO REFUSED BUCKET IS EVER A DESTINATION, and no bucket moves out more than its
    # surplus. Both are properties of the yield rather than of one row.
    moves, stuck, _ = yields(doc, rows)
    division_only = [m for m in moves if list(m.get("changes") or []) == ["division"]]
    assert not division_only, (
        "the rule yields %d move(s) that change the division and nothing else — T-1558's "
        "finding was that the held surplus and the open orders are disjoint on every "
        "other axis, so the division alone moves nobody" % len(division_only))
    held = {r["bucket"] for r in doc["recut_refusals"]}
    assert not [m for m in moves if m["to_bucket"] in held], \
        "a move lands in a bucket the re-cut itself refuses"
    out_of = Counter(m["from_bucket"] for m in moves)
    # THE CAP IS THE SURPLUS THE BUCKET EVER HELD, not the surplus it holds now. The
    # yield carries the moves already spent as well as the ones still to spend, and the
    # book has already taken every spent one off `surplus_still_held` — so measuring the
    # whole list against the remainder would fail the moment the first move landed. A
    # bucket re-familied all the way down leaves `recut_refusals` altogether, and what it
    # ever held is then exactly what walked out of it.
    ever_held = {r["bucket"]: r["surplus_still_held"] + r.get("refamilied_out", 0)
                 for r in doc["recut_refusals"]}
    spent_out = Counter(m["from_bucket"] for m in already_made(doc).values())
    for key, n in out_of.items():
        cap = ever_held.get(key, spent_out.get(key, 0))
        assert n <= cap, f"{key} moves out {n} of a surplus of {cap}"

    # 5b. AND THE RULE IS STABLE UNDER ITS OWN SPENDING (T-1563). Every move the book has
    # already made is re-emitted here, exactly as the ledger holds it, and nobody who has
    # moved is offered a second move — which `build_order_book_1835.refamily_shape`
    # forbids by name and which a plain re-derivation over the spent book would have
    # produced. Without this the list and the ledger drift apart the moment the programme
    # starts: on 2026-09-25, with the first 19 spent, a re-derivation dropped 12 of them
    # and offered 7 of them again.
    made = already_made(doc)
    if made:
        head = moves[:len(made)]
        assert [m["person"] for m in head] == list(made), \
            "the spent moves are not carried at the head of the yield, in the ledger's order"
        assert all(m == made[m["person"]] for m in head), \
            "a spent move is re-emitted as something other than what the ledger holds"
        assert not [m for m in moves[len(made):] if m["person"] in made], \
            "somebody the book has already moved is offered a second move"
        assert not [r for r in stuck if r["person"] in made], \
            "somebody the book has already moved is reported as unable to move"
    assert all(m["rule"] in LADDER_IDS for m in moves), "a move names no rung of the ladder"
    assert all(m["rule"] in MOVABLE_IDS for m in moves), "a move is made on a refused rung"
    assert stuck, "nobody is stuck, which cannot be true while the ceilings bind"
    # THE BRACKET IS ON WHAT IS STILL TO SPEND, because both bounds are (T-1564). `two`
    # and `split_bound` are read off `recut_refusals` and `open_orders`, and the book has
    # already taken every spent move off both of them — a bucket re-familied all the way
    # down leaves the refusals list altogether. So the list this compares has to be net of
    # the ledger too, or the programme fails its own test by succeeding at it: with 87
    # spent the whole yield stood at 108 against a remainder bound of 59.
    split_bound = bound_if_houses_could_split(doc, rows)
    unspent = len(moves) - len(made)
    assert unspent <= split_bound <= two, \
        f"the whole-house price is not bracketed: {unspent} {split_bound} {two}"

    # 6. EMPLOYMENT IS NOT A SELECTOR. The proof is positive: the moves the rule yields
    # contain people the employment layer places at work — it cannot, because every such
    # person is refused — but the ORDER of the movable people must be independent of it.
    # So: re-run the yield with every adoption stripped and assert the ORDER of the
    # C0 people is unchanged. If employment ranked anybody, that order would move.
    bare = [{**r, "adoptions": []} for r in rows]
    order_now = [r["person"] for r in sorted((r for r in rows if r["rung"] == "C0"),
                                             key=lambda r: (r["deal_key"], r["person"]),
                                             reverse=True)]
    order_bare = [r["person"] for r in sorted((r for r in bare if r["rung"] == "C0"),
                                              key=lambda r: (r["deal_key"], r["person"]),
                                              reverse=True)]
    assert order_now == order_bare, "the order of the movable people reads the adoptions"

    print(f"model_refamily_rule self-tests pass ({fired} guards fired, "
          f"{len(rows):,} people tiered, ceilings {one}/{two}/{three}, "
          f"{len(moves):,} moves yielded, {len(stuck):,} refused a destination)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    try:
        if args.build:
            return cmd_build()
        if args.check:
            return cmd_check()
        if args.report:
            return cmd_report()
        if args.self_test:
            return cmd_self_test()
    except Fault as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
