#!/usr/bin/env python3
"""Mint the staffing shortfall the order book can pay for (T-1448, of T-1434).

    tools/mint_staffing_hands_1835.py --build       write the cards and the ledger
    tools/mint_staffing_hands_1835.py --check       re-derive them, refuse drift
    tools/mint_staffing_hands_1835.py --self-test   the guards, fired on the real data

WHAT THIS STAGE IS. `tools/staffing_mint_order_1835.py` derived the order and refused to
run it: the shops want 130 hands over 88 houses and the order book had slots for 36 of
them. That file exists to make the choice askable, and it was asked. The owner ruled on
2026-09-20 — RE-CUT THE BOOK, and re-cut just the remainder — T-1459 ran the re-cut and
T-1503 freed the 10-19 band it needed. The arithmetic settled at **36 payable, 94 with
nowhere to come from**, and this stage spends those 36.

It mints nobody the order does not name. Every hand here is one `paid_from` entry of one
row of `1835_staffing_mint_order.json`, and that file re-derives byte for byte under its
own `--check` in `tools/check.sh`. If a business record changes its occupation, or the
book re-cuts, the order moves first and this stage moves with it.

THE THREE THINGS EACH HAND CARRIES, which is what T-1448 asked for.

  ITS HOUSE.  `works_at` is the business the order names — not a draw. The row exists
              because THAT house is short of THAT role, so the join is the order's and
              is the one thing on the card that is not invented.
  ITS ROLE.   `occupation` is the row's `occupation_term`, which the staffing model took
              from the 1839 directory's own classes and which is in the residents
              vocabulary. `relationship` is the row's `household_relationship`.
  WHERE IT SLEPT.  The staffing model gives every role a `lives_on_premises` figure —
              a share, between 0 and 1 — and this stage DRAWS against it, per hand, on
              a printed seed. The draw says "on the premises" or "boarded out"; it does
              not say which roof, and `lives_at` is null on every card here with that
              reason written on it. Only 4 of the 27 houses in this order are seated on
              a structure at all, so a roof-level answer was never available for 23 of
              them, and T-1199 is the stage that seats a reconstructed household.

WHY A LODGER, AND WHY THAT IS THE ORDER'S CHOICE RATHER THAN A DRAW. Every slot the book
has left at a trade is a `lodging/trade` bucket — "a working lodger, a bed rather than a
household". So a hand the book can pay for is a hand counted as lodging, whatever the
premises draw says: boarding out is still lodging, and the bed is somebody's to seat. A
hand who kept his own house would be a `family/trade` person and those cells are drawn
out, which is a real part of why 94 hands go unpaid. That is a liberty and it is recorded
as one in `docs/LIBERTIES.md`: the household TYPE is the order's, not a reading.

WHAT IT DOES NOT DO.
  * It does not re-deal the order. `pay_the_demand` decided who is paid and out of which
    bucket, in a stated deterministic order, and re-deciding it here would be dealing to
    the quota. This stage reads `paid_from` and spends exactly that.
  * It does not write to a committed card. Nothing in `data/residents/households/`,
    `readmitted/`, `reconstructed_trades/` or `lodgers/` is touched, and no business
    record is written to — `staff[]` is T-1449's close, not this stage's.
  * It draws no family. A hand's kin, if the model owes him one, are `family/none` in the
    book and belong to T-1171 and T-1174; seating them here would order them twice.
  * It draws no figure and no arrival (L1, and the arrival circle T-1169 owns).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

RESIDENTS = ROOT / "data" / "residents"
MINTED = RESIDENTS / "staffing_hands"

BUSINESSES = ROOT / "data" / "businesses"
ORDER = ROOT / "data" / "reconstruction" / "1835_staffing_mint_order.json"
POOLS = ROOT / "data" / "reconstruction" / "1835_invented_name_pools.json"
BOOK = ROOT / "data" / "reconstruction" / "1835_reconstruction_order_book.json"
LEDGER = ROOT / "data" / "reconstruction" / "1835_staffing_hands.json"

STAGE = "staffing_hands"
TICKET = "T-1448"
PARENT = "T-1434"
PROGRAMME = "chicago_1835_resident_reconstruction"
TARGET_DATE = "1835-07-01"
RECONSTRUCTED = "reconstructed"
SOURCE_PASS = "reconstructed_staffing_hand"

#: The book's bands, written as a card reads them.
BAND_EDGES = {"10_19": (10, 19), "20_29": (20, 29), "30_39": (30, 39),
              "40_49": (40, 49), "50_plus": (50, None)}

DIVISIONS = ("north", "south", "west")


class Fault(Exception):
    pass


# -------------------------------------------------------------------- the draw --

def draw(seed: str) -> int:
    return int.from_bytes(hashlib.blake2s(seed.encode("utf-8"), digest_size=8).digest(), "big")


def unit(seed: str) -> float:
    return draw(seed) / float(1 << 64)


def pick(seed: str, weighted: list):
    total = float(sum(w for _, w in weighted))
    if total <= 0:
        raise Fault("a draw was asked to choose from nothing")
    at = unit(seed) * total
    run = 0.0
    for item, weight in weighted:
        run += float(weight)
        if at < run:
            return item
    return weighted[-1][0]


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def slug(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", plain.lower())).strip("_")


# ------------------------------------------------------------------ the inputs --

def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


#: The order, overridable IN MEMORY ONLY. `--self-test` has to ask what this stage would
#: draw against a re-cut purse, and the honest way to ask is not to write a re-cut one to
#: disk: a gate step that touches the live tree is refused by
#: `tools/measure_step_isolation.mjs`, and rightly — a self-test that edits a committed
#: file and puts it back is one interrupted run away from leaving the tree wrong.
_ORDER_OVERRIDE: dict | None = None


def order_doc() -> dict:
    return json.loads(json.dumps(_ORDER_OVERRIDE)) if _ORDER_OVERRIDE else _load(ORDER)


def layer() -> tuple:
    """(every name in the layer, the names REAL people bear, every person id).

    The same three sets `reconstruct_trade_households.py` builds and for the same
    reasons — but over EVERY card directory under `data/residents/`, not the two that
    stage names. It reads `households/` and `readmitted/` because those are the two its
    own siblings write; by the time this stage runs there are six more, and four of them
    mint `rc_` ids out of these same pools. Scanning only the obvious ones drew EIGHT
    people who already existed — `rc_goodrich_luther`, `rc_ingalls_erastus` and six more
    — and the duplicate-id gate over `data/sidecars/1835/people.json` is what said so.
    An id that names two people is not an id, so the set is taken from the directories
    on disk rather than from a list a new stage can fall off.
    """
    all_names, real, ids = set(), set(), set()
    for directory in sorted(d for d in RESIDENTS.iterdir()
                            if d.is_dir() and d != MINTED):
        if not directory.exists():
            continue
        for path in sorted(directory.glob("hh_*.json")):
            card = _load(path)
            for person in card.get("persons") or []:
                name = " ".join(str(person.get("name") or "").split()).lower()
                pid = str(person.get("id") or "")
                if pid:
                    ids.add(pid)
                if not name:
                    continue
                all_names.add(name)
                if person.get("grade") != RECONSTRUCTED:
                    real.add(name)
    return all_names, real, ids


def vocabulary() -> set:
    index = _load(RESIDENTS / "index.json")
    return set(index["vocabulary"]["occupations"])


def business(business_id: str) -> dict:
    path = BUSINESSES / f"{business_id}.json"
    if not path.exists():
        raise Fault(f"the order names {business_id} and there is no such business record")
    return _load(path)


def premises_of(record: dict) -> dict:
    """The house's own seat, as the business record states it — never widened."""
    locations = [loc for loc in record.get("locations") or [] if loc.get("primary")]
    locations = locations or (record.get("locations") or [])
    if not locations:
        return {"structure_id": None, "street_id": None, "kind": None}
    first = locations[0]
    return {"structure_id": first.get("structure_id"),
            "street_id": first.get("street_id"),
            "kind": first.get("kind")}


# -------------------------------------------------------------------- the plan --

def deal_from_the_order() -> list:
    """The purse as the live order spends it: (business, role, role_row, bucket, hands)."""
    order = order_doc()
    return [{"business_id": row["business_id"], "role": row["role"],
             "role_row": row["role_row"], "bucket": spent["bucket"],
             "hands": int(spent["hands"])}
            for row in order["rows"] if row.get("paid")
            for spent in row["paid_from"]]


def committed_deal() -> list:
    """THE DEAL AS IT WAS DEALT, carried forward rather than re-read (T-1503's rule).

    The order this stage spends is itself derived from the book's live outstanding
    slots, so re-cutting the book re-prices the purse — and a re-priced purse pays for
    a DIFFERENT set of hands, out of different buckets, under different seeds. Every
    card here would then be re-drawn: different names, different bands, different
    houses. That is exactly the fault T-1503 measured on the lodging stage, where a
    re-cut re-dealt 25 of 56 invented boarders and took six further gate steps red with
    them, because other layers had adopted them by name.

    So the deal is COMMITTED, in this stage's own ledger, one row per (house, role,
    bucket) — and the four things that keep that honest are T-1503's four:

      * it is committed, so `--check` re-derives the same people from the same numbers
        and `--build` twice running is a fixed point;
      * it is CLOSED. A slot the book opens afterwards is not in this purse; re-minting
        against it is a decision, not a re-derivation;
      * where the live order has since moved, the divergence is STATED row by row in
        `quota_basis.the_order_has_moved` rather than silently absorbed; and
      * a re-cut may not take the order out from under somebody already standing, so
        `refuse_if_the_book_shrank` fails if a bucket's live `to_reconstruct` has fallen
        below what this stage drew out of it.
    """
    if not LEDGER.exists():
        return deal_from_the_order()
    rows = (_load(LEDGER).get("quota_basis") or {}).get("deal")
    return [dict(row) for row in rows] if rows else deal_from_the_order()


def hands() -> list:
    """One entry per HAND the deal pays for, in the order the order file carries it.

    No re-dealing. `staffing_mint_order_1835.py --build` already decided who is paid and
    out of which bucket, in a stated deterministic order that it documents as "an
    arithmetic of slots"; re-deciding it here would be dealing to the quota. The index
    below counts within a (business, division, role, role_row) so a seed names one hand
    for ever, whatever else moves in the file.
    """
    order = order_doc()
    rows_by_key = {(row["business_id"], row["role"], row["role_row"]): row
                   for row in order["rows"]}
    out, counter = [], {}
    for spent in committed_deal():
        row = rows_by_key.get((spent["business_id"], spent["role"], spent["role_row"]))
        if row is None:
            raise Fault(
                f"the committed deal names {spent['business_id']} / {spent['role']} row "
                f"{spent['role_row']} and the order no longer carries that row — a house "
                f"or a staffing class has changed under a minted hand")
        bucket = spent["bucket"]
        sex, band, division = bucket.split("/")[1:4]
        for _ in range(int(spent["hands"])):
            key = (row["business_id"], division, row["role"], row["role_row"])
            counter[key] = counter.get(key, 0) + 1
            out.append({
                "business_id": row["business_id"],
                "business_name": row["business_name"],
                "establishment_class": row["establishment_class"],
                "reads_as": row["reads_as"],
                "role": row["role"],
                "role_row": row["role_row"],
                "occupation_term": row["occupation_term"],
                "household_relationship": row["household_relationship"],
                "sex_rule": row["sex_rule"],
                "role_age_band": row["age_band"],
                "lives_on_premises": row["lives_on_premises"],
                "basis": row["basis"],
                "bucket": bucket,
                "sex": sex,
                "band": band,
                "division": division,
                "index": counter[key],
                "slot": (f"{STAGE}:{row['business_id']}:{division}:{row['role']}:"
                         f"{row['role_row']}:{counter[key]:03d}"),
            })
    return out


# ----------------------------------------------------------------- the drawing --

def community_for(occupation: str, slot: str, pool: dict) -> dict:
    weights = pool["trade_weights"].get(occupation) or pool["trade_weights"]["_default"]
    by_id = {c["id"]: c for c in pool["communities"]}
    weighted = [(by_id[k], v) for k, v in sorted((weights.get("weights") or {}).items())
                if k in by_id]
    if not weighted:
        weighted = [(by_id["yankee"], 1)]
    return pick(f"{slot}:name_pool_community", weighted)


def name_for(hand: dict, pool: dict, taken_names: set, taken_ids: set) -> tuple:
    """A name nobody in the layer bears and an id nobody holds.

    THE WHOLE POOL IS SEARCHED, not one draw and one retry — the rule
    `reconstruct_trade_households.py` arrived at after `Mary Burke` was drawn twice out
    of these same lists. The draw picks where to start; the search steps through every
    (surname, forename) pair from there.
    """
    slot = hand["slot"]
    community = community_for(hand["occupation_term"], slot, pool)
    surnames = community["surnames"]
    givens = community["given_male" if hand["sex"] == "male" else "given_female"]
    first = draw(f"{slot}:surname")
    second = draw(f"{slot}:forename")
    for step_s in range(len(surnames)):
        surname = surnames[(first + step_s) % len(surnames)]
        for step_g in range(len(givens)):
            given = givens[(second + step_g) % len(givens)]
            full = f"{given} {surname}"
            pid = f"rc_{slug(surname)}_{slug(given)}"
            if full.lower() in taken_names or pid in taken_ids:
                continue
            taken_names.add(full.lower())
            taken_ids.add(pid)
            return full, pid, community
    raise Fault(f"{slot}: every name in the {community['id']} pool is already borne")


def band_block(band: str, seed: str) -> dict:
    low, high = BAND_EDGES[band]
    return {
        "value": f"{low}-{high}" if high is not None else f"{low}+",
        "low": low,
        "high": high,
        "confidence": RECONSTRUCTED,
        "tier": RECONSTRUCTED,
        "basis": {
            "kind": "model",
            "id": "1835_reconstruction_order_book",
            "note": f"The bucket that ordered this person is {band}; the band is the "
                    f"order, not a draw. Nothing here is a reading of anybody's age.",
        },
        "seed": seed,
        "replaceable_by": {
            "kind": "person",
            "match": "a source that states this person's age or their birth year",
        },
        "note": "AN AGE BAND, NEVER A YEAR. The order book counts in the 1840 schedule's "
                "bands and this project writes no year it cannot read.",
    }


def slept(hand: dict) -> dict:
    """Where this hand slept, drawn against the staffing model's own share.

    `lives_on_premises` is a SHARE — the part of the hands in a role who lived in — and
    this is the draw that spends it. A share of 0 or 1 is not drawn against at all; it is
    the model stating the answer, and a draw over it would be noise dressed as evidence.

    IT DOES NOT NAME A ROOF, and it is written so no reader can take it for one. A house
    that seats its own hands is still an UNSEATED house here: 23 of the 27 in this order
    carry a street and no structure, so the roof does not exist to be named. T-1199 seats
    a reconstructed household on the lot grid, and that is where the roof comes from.
    """
    share = float(hand["lives_on_premises"])
    seed = f"{hand['slot']}:sleeps_on_premises"
    if share <= 0.0:
        on_premises, how = False, "the model gives this role no hands living in"
    elif share >= 1.0:
        on_premises, how = True, "the model has every hand in this role living in"
    else:
        on_premises = unit(seed) < share
        how = (f"drawn against the model's share of {share:g} for this role, and the "
               f"draw says {'in' if on_premises else 'out'}")
    return {
        "value": "on the premises" if on_premises else "boarded out",
        "on_premises": on_premises,
        "confidence": RECONSTRUCTED,
        "tier": RECONSTRUCTED,
        "basis": {
            "kind": "model",
            "id": "1835_business_staffing_model",
            "note": f"`lives_on_premises` for {hand['role']} in {hand['reads_as']} is "
                    f"{share:g} — {how}.",
        },
        "seed": seed,
        "replaceable_by": {
            "kind": "person",
            "match": "a source stating where a hand of this house slept",
        },
        "note": "WHETHER, NOT WHERE. This says the hand slept at his work or away from "
                "it and names no roof: the house is not seated on a structure and T-1199 "
                "is the stage that seats one. Either way he is counted as lodging, "
                "because the only slot the book had left for a working man is a "
                "`lodging/trade` slot.",
    }


def person_for(hand: dict, pool: dict, taken_names: set, taken_ids: set) -> dict:
    full, pid, community = name_for(hand, pool, taken_names, taken_ids)
    slot = hand["slot"]
    return {
        "id": pid,
        "name": full,
        "relationship": hand["household_relationship"],
        "grade": RECONSTRUCTED,
        "sex": hand["sex"],
        "age_band": band_block(hand["band"], f"{slot}:age_band"),
        "name_basis": {
            "value": full,
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "model",
                "id": "1835_invented_name_pools",
                "note": f"Both parts are drawn from the {community['id']} pool, weighted "
                        f"for {hand['occupation_term']} where the pools speak to that "
                        f"trade and from the general stock where they do not.",
            },
            "seed": f"{slot}:forename",
            "replaceable_by": {
                "kind": "person",
                "match": "a source naming a real hand of this house",
            },
            "note": "AN INVENTED NAME, AND IT IS NEVER EVIDENCE. No source names this "
                    "person. The name exists so a reader can tell one drawn hand from "
                    "another, and it is checked against every real name in the layer.",
        },
        "basis": {
            "kind": "model",
            "id": "1835_staffing_mint_order",
            "note": f"The staffing model wants a {hand['role']} at "
                    f"{hand['business_name']} that no card in the layer holds, and the "
                    f"order book's bucket {hand['bucket']} had a slot to pay for one. "
                    f"Both halves had to be true: 94 of the 130 hands the shops want "
                    f"have no slot and are not minted.",
        },
        "seed": f"{slot}:forename",
        "replaceable_by": {
            "kind": "person",
            "match": "a source naming a person who worked at this house, who would take "
                     "this place instead",
        },
        "reconstruction": {
            "stage": STAGE,
            "programme": PROGRAMME,
            "community": community["id"],
            "review_required": False,
        },
        "resident_subtype": "reconstructed_staffing_hand",
        "occupation": {
            "value": hand["occupation_term"],
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "model",
                "id": "1835_business_staffing_model",
                "note": f"The house's class is {hand['establishment_class']} and the "
                        f"model staffs that class with this role at its typical band. "
                        f"The term is the model's, from the 1839 directory's classes, "
                        f"and is in the residents vocabulary.",
            },
            "seed": f"{slot}:role",
            "replaceable_by": {
                "kind": "person",
                "match": "a source naming this house's hands and their trades",
            },
        },
        "slept": slept(hand),
        "note": "RECONSTRUCTED, NOT FOUND. Nobody is named by any source here. This "
                "person exists because a house this project holds a record for is short "
                "of a hand its class is staffed with, and the order book had a slot to "
                "count him in. The whole of what is claimed is that: a man of this band "
                "worked this trade at this house. He is reproducible from the seeds "
                "printed above and a real name retires him. No figure is drawn (L1).",
    }


# --------------------------------------------------------------------- the fill --

def fill() -> tuple:
    pool = _load(POOLS)
    vocab = vocabulary()
    all_names, real_names, ids = layer()
    taken_names, taken_ids = set(all_names), set(ids)

    cards, fills, ledger_rows = {}, {}, []
    for hand in hands():
        if hand["occupation_term"] not in vocab:
            raise Fault(f"{hand['slot']}: `{hand['occupation_term']}` is not in the "
                        f"residents vocabulary and may not be written onto a person")
        record = business(hand["business_id"])
        hid = f"hh_staff_{hand['business_id'][4:]}_{hand['division']}"
        person = person_for(hand, pool, taken_names, taken_ids)
        if person["name"].lower() in real_names:
            raise Fault(f"{hand['slot']}: drew {person['name']}, which a real person bears")
        card = cards.get(hid)
        if card is None:
            card = cards[hid] = card_for(hid, hand, record)
        card["persons"].append(person)
        card["staffing_hands"]["hands_minted"] += 1
        fills[hand["bucket"]] = fills.get(hand["bucket"], 0) + 1
        ledger_rows.append({
            "person": person["id"],
            "name": person["name"],
            "household": hid,
            "file": f"staffing_hands/{hid}.json",
            "business": hand["business_id"],
            "business_name": hand["business_name"],
            "role": hand["role"],
            "occupation": hand["occupation_term"],
            "bucket": hand["bucket"],
            "division": hand["division"],
            "slept": person["slept"]["value"],
            "slot": hand["slot"],
        })
    return cards, {"fills": fills, "minted": ledger_rows}


def card_for(hid: str, hand: dict, record: dict) -> dict:
    seat = premises_of(record)
    return {
        "id": hid,
        "name": f"The hands of {hand['business_name']}",
        "division": hand["division"],
        "head": None,
        "source_pass": SOURCE_PASS,
        "staffing_hands": {
            "ticket": TICKET,
            "parent_ticket": PARENT,
            "stage": STAGE,
            "business": hand["business_id"],
            "business_name": hand["business_name"],
            "establishment_class": hand["establishment_class"],
            "reads_as": hand["reads_as"],
            "premises": seat,
            "hands_minted": 0,
            "stands_on": "The staffing model gives this house's class a typical number "
                         "of hands at each role, the layer holds fewer, and the order "
                         "book had an outstanding `lodging/trade` slot to count the "
                         "difference in. `1835_staffing_mint_order.json` carries the "
                         "arithmetic and re-derives under its own gate.",
            "withdrawn_if": "a source naming this house's hands, a staffing model that "
                            "no longer wants them, or a re-cut order book with no slot "
                            "to pay for them; the retirement runs through --build, "
                            "never by hand",
            "note": "A CONTAINER, NOT A FAMILY. `data/residents/` cannot carry a person "
                    "outside a household, and the hands of one house were not kin. This "
                    "record holds the working places of one house in one division and "
                    "claims no relation between the people in them beyond the work.",
        },
        "household_owed": {
            "size_drawn": None,
            "seated_by": "T-1171 and T-1174 (a hand's own kin, if the model owes him "
                         "any), T-1179 (converge)",
            "note": "NOT DRAWN HERE. A hand's kin are `family/none` in the order book "
                    "and that quota belongs to T-1171 and T-1174; drawing them here "
                    "would order the same people twice.",
        },
        "arrival": {
            "value": None,
            "confidence": RECONSTRUCTED,
            "tier": "unknown",
            "note": "NOT DRAWN HERE, AND THE REASON IS A CIRCLE. The arrival model's own "
                    "distribution is computed over the compiled scene and the scene "
                    "carries these cards; an arrival written here would move the table "
                    "that drew it. The programme's arrival stage owns this block.",
            "seated_by": "T-1169 (the arrival fill), T-1179 (converge)",
        },
        "lives_at": {
            "value": None,
            "confidence": RECONSTRUCTED,
            "tier": "unknown",
            "note": "NOT SEATED, AND NOT FOR WANT OF ASKING. Each person here carries a "
                    "`slept` block saying whether he lived at his work or boarded out, "
                    "drawn against the staffing model's own share for his role — but "
                    "that names no roof. 23 of the 27 houses in this order carry a "
                    "street and no structure, so there is no premises id to write, and "
                    "T-1199 is the stage that seats a reconstructed household on the lot "
                    "grid. The division above is the order book bucket's.",
            "seated_by": "T-1199 (the placement policy)",
        },
        "works_at": {
            "value": hand["business_id"],
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "model",
                "id": "1835_staffing_mint_order",
                "note": "THE ONE THING ON THIS CARD THAT IS NOT A DRAW. These people "
                        "exist because this house is short of hands; the house is the "
                        "reason for the person, so the workplace is the order rather "
                        "than a draw made over it.",
            },
            "replaceable_by": {
                "kind": "person",
                "match": "a source naming who worked at this house",
            },
        },
        "present_on_scene_date": {
            "value": "present",
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "rule",
                "id": "ordered_by_the_reconstruction_order_book",
                "note": "Ordered, not argued: the book counts these people as missing "
                        "FROM the town of 1 July 1835, so presence is the order rather "
                        "than a draw made over it.",
            },
            "replaceable_by": {
                "kind": "person",
                "match": "a re-cut order book that no longer orders these buckets",
            },
        },
        "touches_removal": False,
        "review_required": False,
        "persons": [],
    }


def basis_block() -> dict:
    """The deal as it will be committed, and every way the live order has moved off it.

    `deal` is what this stage dealt against — on a first build the live order's own
    `paid_from`, and on every build after that this same block read back. Nothing here
    is absorbed silently: a row the order no longer pays for, a row it pays for that is
    not in this purse, and a row whose bucket or count has changed are each named.
    """
    deal = committed_deal()
    live = deal_from_the_order()
    key = lambda row: (row["business_id"], row["role"], row["role_row"], row["bucket"])
    live_by_key = {key(row): row for row in live}
    deal_by_key = {key(row): row for row in deal}
    return {
        "$note": "DERIVED, and the purse this stage dealt against. T-1503's rule: the "
                 "order is itself priced off the book's outstanding slots, so reading "
                 "it live would re-draw every card here the next time the book is "
                 "re-cut. The purse is recorded once and carried, and every divergence "
                 "is stated below rather than absorbed.",
        "owning_ticket": TICKET,
        "read_from": "`paid_from` in data/reconstruction/1835_staffing_mint_order.json "
                     "on the build that first recorded it; carried unchanged after that",
        "deal": deal,
        "hands": sum(int(row["hands"]) for row in deal),
        "the_order_has_moved": {
            "no_longer_paid_for": sorted(k[0] + "/" + k[1] + "#" + str(k[2])
                                         for k in deal_by_key if k not in live_by_key),
            "paid_for_since": sorted(k[0] + "/" + k[1] + "#" + str(k[2])
                                     for k in live_by_key if k not in deal_by_key),
            "count_changed": [
                {"row": k[0] + "/" + k[1] + "#" + str(k[2]), "bucket": k[3],
                 "dealt_against": deal_by_key[k]["hands"],
                 "the_order_pays_now": live_by_key[k]["hands"]}
                for k in sorted(set(deal_by_key) & set(live_by_key))
                if deal_by_key[k]["hands"] != live_by_key[k]["hands"]],
            "reads_as": "A divergence here is a decision for a run to make, never a "
                        "re-derivation: re-minting against a purse that has moved "
                        "retires people other layers may already name. The cards stand "
                        "on `deal` until a ticket says otherwise.",
        },
    }


def refuse_if_the_book_shrank(fills: dict) -> None:
    """The one thing a re-cut may not do: take the order out from under somebody standing.

    A bucket may be re-cut freely under these cards — that is what the committed purse
    is for — but it may not be re-cut BELOW what this stage has already drawn out of it,
    because then the book would be ordering fewer people than are standing in it. The
    book's own `no_bucket_overfilled` invariant says the same thing from the other side;
    this says it here, where the stage can name which of its own hands is stranded.
    """
    book = _load(BOOK)
    live = {}
    for family in book.get("bucket_families") or []:
        for bucket in family.get("buckets") or []:
            live[bucket.get("key")] = int(bucket.get("to_reconstruct") or 0)
    for bucket, drew in sorted(fills.items()):
        if bucket not in live:
            raise Fault(f"{bucket} has gone from the order book and {drew} hand(s) of "
                        f"this stage stand in it")
        if live[bucket] < drew:
            raise Fault(f"{bucket} is now ordered at {live[bucket]} and this stage has "
                        f"already drawn {drew} out of it — a re-cut may not take the "
                        f"order out from under somebody already standing")


# ------------------------------------------------------------- the measurement --

def measurement(cards: dict, ledger: dict) -> dict:
    order = order_doc()
    minted = ledger["minted"]
    by_role, by_division, by_slept = {}, {}, {}
    for row in minted:
        by_role[row["role"]] = by_role.get(row["role"], 0) + 1
        by_division[row["division"]] = by_division.get(row["division"], 0) + 1
        by_slept[row["slept"]] = by_slept.get(row["slept"], 0) + 1
    collision = order["the_collision"]
    return {
        "hands_the_shops_want": order["the_demand"]["hands_wanted"],
        "houses_short": order["the_demand"]["houses_short"],
        "the_book_could_pay_for": collision["what_the_book_could_pay_for_today"],
        "hands_minted": len(minted),
        "hands_unpaid": collision["what_would_go_unpaid"],
        "houses_staffed_here": len({row["business"] for row in minted}),
        "containers_written": len(cards),
        "by_role": dict(sorted(by_role.items())),
        "by_division": dict(sorted(by_division.items())),
        "where_they_slept": dict(sorted(by_slept.items())),
        "buckets_filled": len(ledger["fills"]),
        "every_hand_names_its_house": all(row["business"] for row in minted),
        "nobody_is_minted_twice": len({row["person"] for row in minted}) == len(minted),
        "the_ninety_four": "THE SHOPS ARE STILL SHORT, AND BY MOST OF WHAT THEY WANT. "
                           "94 of the 130 hands have no slot in the book to be counted "
                           "in: 25 of the slots left are women's and every hand wanted "
                           "is a man or a role the model calls predominantly male, and "
                           "the rest is a plain shortfall on the count. T-1459 made the "
                           "sex refusal on the evidence and did not withdraw it, so "
                           "those houses stand short and the business card says so — "
                           "which was always the third of the order's three answers.",
    }


# ---------------------------------------------------------------------- modes --

README = """# data/residents/staffing_hands/

DERIVED. Written by `tools/mint_staffing_hands_1835.py --build` (T-1448, of T-1434), the
`staffing_hands` stage of the 1835 resident reconstruction programme. Do not hand-edit a
card here: `--check` re-derives the whole directory and refuses a differing byte, and
`tools/check.sh` runs it.

Every person here is `grade: reconstructed` and **nobody in this directory is named by any
source**. They exist because a business record this project holds is short of a hand its
class is staffed with AND the reconstruction order book had an outstanding `lodging/trade`
slot to count that hand in. Both halves had to be true, which is why there are 36 of them
and not the 130 the shops want.

A card here is a CONTAINER for one house's hands in one division — not a family. Each
person carries the house he worked at, the role the staffing model wants, the bucket that
ordered him, and a `slept` block saying whether he lived at his work or boarded out. It
names no roof: T-1199 seats a reconstructed household on the lot grid.

The directory is deliberately OUTSIDE `data/residents/households/`, for the reason
`reconstructed_trades/` is: that directory is re-derived by the research mints and
`data/residents/index.json` is derived from it, so a reconstruction that is not a reading
lives here and is overlaid onto the scene by `tools/compile_scene.py`.
"""


def ledger_doc(cards: dict, ledger: dict) -> dict:
    return {
        "$schema_note": "DERIVED. Written by tools/mint_staffing_hands_1835.py --build; "
                        "tools/check.sh re-derives it. Do not hand-edit.",
        "id": "chicago_1835_staffing_hands",
        "ticket": TICKET,
        "parent_ticket": PARENT,
        "stage": STAGE,
        "target_date": TARGET_DATE,
        "generated_by": "tools/mint_staffing_hands_1835.py --build",
        "not_a_reading": "NOTHING HERE IS A READING. Every person in this ledger is "
                         "invented within the bounds two derived files set: the staffing "
                         "model's typical band for the house's class, and the order "
                         "book's outstanding slots. No page of any source was read to "
                         "write it, and no source_id is claimed for anybody in it.",
        "inputs": {
            "the_order": "data/reconstruction/1835_staffing_mint_order.json",
            "the_book": "data/reconstruction/1835_reconstruction_order_book.json",
            "the_names": "data/reconstruction/1835_invented_name_pools.json",
            "the_houses": "data/businesses/",
        },
        "what_it_does_not_do": {
            "it_does_not_re_deal_the_order": "`pay_the_demand` in "
                "tools/staffing_mint_order_1835.py decided who is paid and out of which "
                "bucket. This stage reads `paid_from` and spends exactly that.",
            "it_writes_to_no_committed_card": "Nothing in households/, readmitted/, "
                "reconstructed_trades/ or lodgers/ is touched, and no business record is "
                "written to — `staff[]` is T-1449's close.",
            "it_draws_no_family": "A hand's kin are `family/none` in the book and belong "
                "to T-1171 and T-1174.",
            "it_seats_nobody": "T-1199 seats a reconstructed household on the lot grid. "
                "The `slept` block says whether, never where.",
        },
        "quota_basis": basis_block(),
        "fills": dict(sorted(ledger["fills"].items())),
        "minted": ledger["minted"],
        "measurement": measurement(cards, ledger),
    }


def write(cards: dict) -> tuple:
    MINTED.mkdir(parents=True, exist_ok=True)
    wanted = {f"{hid}.json" for hid in cards}
    removed = 0
    for path in sorted(MINTED.glob("hh_*.json")):
        if path.name not in wanted:
            path.unlink()
            removed += 1
    written = 0
    for hid, card in sorted(cards.items()):
        path = MINTED / f"{hid}.json"
        text = dumps(card)
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            written += 1
    (MINTED / "README.md").write_text(README, encoding="utf-8")
    return written, removed


def write_fills(ledger: dict) -> None:
    """Carry this stage's fills into the order book and re-derive it. The book's own
    `--build` refuses an overfilled bucket, so the quota is enforced twice."""
    import build_order_book_1835 as ob
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    kept = [f for f in book.get("fills", []) if f.get("ticket") != TICKET]
    kept += [{"bucket": key, "ticket": TICKET, "stage": STAGE, "records": n,
              "by": "tools/mint_staffing_hands_1835.py --build"}
             for key, n in sorted(ledger["fills"].items())]
    book["fills"] = kept
    BOOK.write_text(json.dumps(book, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ob.cmd_build()


def cmd_build() -> int:
    cards, ledger = fill()
    refuse_if_the_book_shrank(ledger["fills"])
    written, removed = write(cards)
    doc = ledger_doc(cards, ledger)
    LEDGER.write_text(dumps(doc), encoding="utf-8")
    write_fills(ledger)
    m = doc["measurement"]
    print(f"  minted {m['hands_minted']} hands into {m['containers_written']} containers "
          f"over {m['houses_staffed_here']} houses "
          f"({written} written, {removed} removed)")
    print(f"  wrote {LEDGER.relative_to(ROOT)}")
    return 0


def cmd_check() -> int:
    if not LEDGER.exists():
        print("the staffing-hands ledger has never been written — run --build")
        return 1
    cards, ledger = fill()
    refuse_if_the_book_shrank(ledger["fills"])
    want = ledger_doc(cards, ledger)
    have = _load(LEDGER)
    if have != want:
        print("the staffing-hands ledger is not what its inputs re-derive — run "
              "tools/mint_staffing_hands_1835.py --build")
        return 1
    on_disk = {p.name for p in MINTED.glob("hh_*.json")}
    if on_disk != {f"{hid}.json" for hid in cards}:
        print("data/residents/staffing_hands/ holds a different set of cards than its "
              "inputs re-derive — run --build")
        return 1
    for hid, card in sorted(cards.items()):
        if (MINTED / f"{hid}.json").read_text(encoding="utf-8") != dumps(card):
            print(f"data/residents/staffing_hands/{hid}.json differs from its "
                  f"re-derivation — run --build, never a hand edit")
            return 1
    book = _load(BOOK)
    mine = {f["bucket"]: f["records"] for f in book.get("fills", [])
            if f.get("ticket") == TICKET}
    if mine != ledger["fills"]:
        print("the order book's fills for this stage are not the ones it minted — run "
              "--build")
        return 1
    print(f"  {len(ledger['minted'])} hands in {len(cards)} containers re-derive")
    return 0


# ------------------------------------------------------------------ self-test --

def cmd_self_test() -> int:
    failures = []

    def fires(label, run):
        try:
            run()
        except (Fault, AssertionError, KeyError):
            print(f"   self-test | ok      {label}")
            return
        failures.append(label)
        print(f"   self-test | FAIL    {label}")

    def holds(label, run):
        try:
            run()
            print(f"   self-test | ok      {label}")
        except Exception as exc:                        # noqa: BLE001
            failures.append(f"{label}: {exc}")
            print(f"   self-test | FAIL    {label}: {exc}")

    cards, ledger = fill()
    minted = ledger["minted"]
    order = _load(ORDER)

    # 1. The mint spends exactly what the order says it may, bucket by bucket.
    holds("the fills equal the order's `paid_from`, bucket by bucket", lambda: _same(
        ledger["fills"],
        _paid_by_bucket(order)))

    # 2. Nobody is minted into a bucket with no outstanding slot.
    holds("every bucket spent was outstanding in the book", lambda: _outstanding(ledger))

    # 3. An id may never name two people.
    holds("no person id is used twice", lambda: _assert(
        len({r["person"] for r in minted}) == len(minted), "an id names two people"))

    # 4. No invented name is a real person's name.
    holds("no invented name is borne by a real person", lambda: _no_real_name(minted))

    # 5. A hand whose occupation is outside the vocabulary is refused.
    fires("an occupation outside the residents vocabulary is refused", lambda: _person(
        {**_a_hand(), "occupation_term": "aeronaut"}))

    # 6. A share of 0 never draws a hand living in, and a share of 1 always does.
    holds("the premises share of 0 and 1 are stated, not drawn", lambda: _assert(
        slept({**_a_hand(), "lives_on_premises": 0.0})["on_premises"] is False
        and slept({**_a_hand(), "lives_on_premises": 1.0})["on_premises"] is True,
        "a stated share was drawn against"))

    # 7. The draw is deterministic: one slot, one name, every time.
    holds("the draw is reproducible from its seed", lambda: _assert(
        fill()[1]["minted"] == minted, "two builds drew different people"))

    # 8. THE PLACE ON `REMAINDER_STABLE_STAGES` IS EARNED HERE, and nowhere else. The
    #    order this stage spends is priced off the book's outstanding slots, so a re-cut
    #    re-prices the purse; the committed `quota_basis.deal` is what stops that
    #    re-drawing every card. The demonstration is T-1503's: move every bucket this
    #    stage drew against, re-derive, and assert that not one person moves.
    holds("a re-cut of every bucket it drew against moves not one card",
          lambda: _stable_under_a_recut(minted, ledger))

    if failures:
        print(f"\nCHECK FAIL — {len(failures)} assertion(s) did not fire")
        return 1
    print(f"\n  {8 - len(failures)} of 8 assertions firing")
    return 0


def _assert(condition, why):
    if not condition:
        raise AssertionError(why)


def _same(have, want):
    _assert(have == want, f"{have} != {want}")


def _paid_by_bucket(order: dict) -> dict:
    out = {}
    for row in order["rows"]:
        for spent in row.get("paid_from") or []:
            out[spent["bucket"]] = out.get(spent["bucket"], 0) + int(spent["hands"])
    return dict(sorted(out.items()))


def _outstanding(ledger: dict) -> None:
    order = _load(ORDER)
    have = {b["bucket"]: b["outstanding"] for b in order["what_the_book_can_pay"]["buckets"]}
    for bucket, spent in ledger["fills"].items():
        _assert(bucket in have, f"{bucket} was not an outstanding slot")
        _assert(spent <= have[bucket], f"{bucket} spent {spent} of {have[bucket]}")


def _no_real_name(minted: list) -> None:
    _all, real, _ids = layer()
    for row in minted:
        _assert(row["name"].lower() not in real,
                f"{row['name']} is borne by a person a source names")


def _stable_under_a_recut(minted: list, ledger: dict) -> None:
    """Re-cut every bucket this stage drew against, on a throwaway order, and re-derive.

    The purse is the thing that moves under a re-cut, so the re-cut is SIMULATED where it
    lands: in `staffing_mint_order_1835.json`'s `paid_from`, whose buckets are shifted to
    the cells this stage did not spend. A stage that read that live would re-draw every
    card — names, bands, houses and all. This one reads `quota_basis.deal`, so it must
    not. The throwaway order never reaches the disk: `order_doc()` is overridden in
    memory, because a gate step that writes the live tree is refused and a self-test that
    puts a committed file back afterwards is one interrupted run from leaving it wrong.
    """
    global _ORDER_OVERRIDE
    order = _load(ORDER)
    others = [b for b in order["what_the_book_can_pay"]["buckets"]
              if b["bucket"] not in ledger["fills"]]
    if not others:
        raise AssertionError("the order has no unspent bucket to re-cut into")
    moved = 0
    for row in order["rows"]:
        for spent in row.get("paid_from") or []:
            spent["bucket"] = others[moved % len(others)]["bucket"]
            moved += 1
    _assert(moved > 0, "nothing was re-cut, so nothing was demonstrated")
    try:
        _ORDER_OVERRIDE = order
        again = fill()[1]["minted"]
    finally:
        _ORDER_OVERRIDE = None
    _assert(again == minted,
            f"a re-cut of {moved} slot(s) moved a card: the deal is being read live")


def _a_hand() -> dict:
    return hands()[0]


def _person(hand: dict):
    vocab = vocabulary()
    if hand["occupation_term"] not in vocab:
        raise Fault(f"`{hand['occupation_term']}` is not in the residents vocabulary")
    return hand


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.build:
            return cmd_build()
        if args.check:
            return cmd_check()
        if getattr(args, "self_test"):
            return cmd_self_test()
    except Fault as exc:
        print(f"the staffing-hands mint refused: {exc}")
        return 1
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
