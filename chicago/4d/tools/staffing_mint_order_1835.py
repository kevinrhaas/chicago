#!/usr/bin/env python3
"""THE MINT ORDER FOR THE SHOP HANDS — what the staffing model still wants, and what
the reconstruction order book can pay for.

    tools/staffing_mint_order_1835.py --build       write the order
    tools/staffing_mint_order_1835.py --check       re-derive it, refuse drift
    tools/staffing_mint_order_1835.py --self-test   the guards, fired on the real data

T-1448, of T-1434, of T-1189. It mints nobody. It writes no person, raises no business
and touches no committed card: the whole of what it does is set two derived files
beside each other and count.

WHY THIS STANDS BETWEEN T-1433 AND THE MINT. T-1432 carried the attested half of the
staffing join across — 145 rows a source names. T-1433 seated the reconstructed
residents who had a trade and nowhere to follow it — 124 seats in 84 houses. T-1434
was then to MINT the shortfall: new reconstructed hands wherever a house still stands
short of the staffing model's typical band. The first thing the mint has to know is
how many people it is allowed to invent, and this project has exactly one answer to
that question — `data/reconstruction/1835_reconstruction_order_book.json`, which is
the quota every reconstruction stage draws against and whose `no_bucket_overfilled`
invariant refuses a stage that draws past it.

Set the two side by side and they do not agree, and the disagreement is not small:

  * the shops want more hands than the book has slots left,
  * every hand the shops want is a man, and a large share of the book's remaining
    slots are women's,
  * and every slot that could pay is owned by another stage.

So the mint cannot simply run. Either the book is re-cut — the town's remaining
working people are younger and more male than a cut shaped by the 1840 schedule
assumes — or the staffing model comes down off its typical band, or the shops stand
short and the town says why. That is a ruling about what the town IS, not a detail of
how a tool draws, and T-1166 owns the book. This file is the adjudication that makes
the ruling askable: every number in it re-derives from committed files, and `--check`
refuses a byte that has drifted since.

THE FIRST ANSWER HAS SINCE BEEN RULED AND SPENT, and this file says so from the book
rather than from memory. The owner ruled the re-cut on 2026-09-20; it ran, it opened
the 10-19 band the apprentices and shop boys stand in, and it REFUSED the sex axis on
the evidence — so it did not make the mint payable to the typical band. The prose in
`the_question` and `the_collision` used to be literal strings written against the book
as it stood before that, and by 2026-09-25 three of them were flatly false: they went
on calling a band drawn out that carries outstanding slots. Every clause that names a
quantity is now DERIVED from the same `rows` and `slots` the numbers beside it come
from, and the self-test fires on the wording as well as on the figure. An adjudication
that narrates a state it no longer measures is worse than no adjudication at all.

And the second answer is now PRICED. `the_demand` had always promised that `count_low`
was "carried on every row so a reader can price the other two answers"; it was not
carried at all, so the one answer arithmetic could settle was the one nobody could
read. Every row now carries `count_low` and `short_by_at_the_low_band`, and
`the_collision.at_the_model_s_low_band` pays that smaller demand from the same purse
in the same order.

AND THE OWNER HAS NOW RULED — option (a), the LOW band, on 2026-09-25. So this file's
job changed: the question above is answered, and what an answered question needs is not
another asking but a PRICE THE MINT CAN BE RUN FROM. `the_owner_s_ruling` is that price,
and pricing it turned up two axes the payment had never looked at and a bound nothing had
counted:

  * THE HOUSEHOLD AXIS. `pay_the_demand` matches a hand to a slot on sex and age band
    only. Every slot it can reach is a `lodging/trade` bucket — a person the book orders
    into a lodging household — and the staffing model's OWN `the_shop_household_rule`
    puts the on-premises share of these roles in the EMPLOYER'S household instead. A
    tavern keeper the model states at `lives_on_premises: 1.0` is a household member at
    every share of the role, and a lodging slot is the wrong household type for them.
    The book's `family/trade` cells, which would be the right one, are drawn out.
  * THE BED BOUND. A lodging slot is a quota, not a bed, and a lodger has to sleep in a
    house that stands. `1835_lodgers_seated.json` is now an input for exactly that
    reason: it is the committed bed accounting, and it says every ordinary-night bed in
    every built lodging place is slept in and answers "may anything more be minted
    here" with No. So the hands the ruling buys in slots cannot be seated in beds.

Both are read off committed files, neither is asserted here, and the self-test fires on
each. The ruling is not thereby refused — it stands, and `mintable_today` is what it can
actually buy on the town as committed, which is the figure the mint stage needs and the
one no earlier pass of this file could have printed.

WHAT IT IS NOT. It is not a roster. No name is drawn, no card is written, no bucket's
`filled` is incremented and no `fills` row is added — an order is not a fill, and the
book's counters stay exactly where the stages that earned them left them. It is also
not a re-cut of the book: reading a book and proposing one are different acts, and
this tool only reads.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUSINESSES = ROOT / "data" / "businesses"
MODEL = ROOT / "data" / "reconstruction" / "1835_business_staffing_model.json"
ORDER_BOOK = ROOT / "data" / "reconstruction" / "1835_reconstruction_order_book.json"
SEATING = ROOT / "data" / "residents" / "reconstructed_seating.json"
#: The committed bed accounting of the boarders stage (T-1371, of T-1175). A
#: `lodging/trade` slot is a quota and a bed is a place to sleep; this file is the only
#: committed statement of how many of the second there are.
LODGERS_SEATED = ROOT / "data" / "reconstruction" / "1835_lodgers_seated.json"
OUT = ROOT / "data" / "reconstruction" / "1835_staffing_mint_order.json"

TICKET = "T-1448"
PARENT_TICKET = "T-1434"
GRANDPARENT_TICKET = "T-1189"
TARGET_DATE = "1835-07-01"

#: The staffing model counts hands in its own age vocabulary and the order book counts
#: people in the 1840 schedule's bands. Neither is wrong and they are not the same
#: ruler, so a slot can only pay for a hand where the two OVERLAP in years. The years
#: below are the ones each vocabulary's own term states; nothing is widened to make a
#: band reach a slot it does not reach.
ROLE_BAND_YEARS = {
    "youth_12_18": (12, 18),
    "young_adult_16_25": (16, 25),
    "adult_18_45": (18, 45),
    "adult_any": (18, 120),
}
BOOK_BAND_YEARS = {
    "under_10": (0, 9),
    "10_19": (10, 19),
    "20_29": (20, 29),
    "30_39": (30, 39),
    "40_49": (40, 49),
    "50_plus": (50, 120),
}

#: Which of the book's sexes a role's sex rule may be paid out of. `predominantly_male`
#: is paid as male and SAYS SO: the model's own gloss is "men in the great majority; a
#: woman in the role is not refused", and a tool that quietly read that as `either`
#: would spend a woman's slot on the strength of a word that only declines to refuse one.
SEX_RULE_PAYS_FROM = {
    "male": ["male"],
    "predominantly_male": ["male"],
    "female": ["female"],
    "predominantly_female": ["female"],
    "either": ["male", "female"],
}


class Fault(Exception):
    pass


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _businesses() -> list:
    return [_load(p) for p in sorted(BUSINESSES.glob("*.json")) if p.name != "index.json"]


# ---------------------------------------------------------------- the demand --

def staffable(businesses: list, model: dict) -> list:
    """The houses the staffing model staffs, and no other. A record with no
    `occupation` is no kind of establishment and the model already refuses those by
    name in `unstaffed_records`; a record the register does not place at the scene
    date is not open to be short of anybody."""
    classes = {}
    for klass in model.get("classes") or []:
        for occupation in klass.get("occupations_in_this_class") or []:
            classes[occupation] = klass
    refused = {row["id"] for row in model.get("unstaffed_records") or []}
    out = []
    for business in businesses:
        if not business.get("present_at_scene_date"):
            continue
        occupation = business.get("occupation")
        if not occupation or occupation not in classes or business["id"] in refused:
            continue
        out.append((business, classes[occupation]))
    out.sort(key=lambda row: row[0]["id"])
    return out


def hands_already_in_the_house(businesses: list, seating: dict) -> dict:
    """(business id, role) -> hands standing in it today, from BOTH halves of the join
    already done: the `staff[]` rows the register itself prints, and T-1433's seats.
    A proprietor or a partner is not a hand — the model counts principals separately
    and `principals_already_in_the_layer` is its own figure."""
    counts: dict = {}
    for business in businesses:
        for row in business.get("staff") or []:
            key = (business["id"], row.get("role"))
            counts[key] = counts.get(key, 0) + 1
    for row in seating.get("rows") or []:
        if row.get("kind") != "seated":
            continue
        key = (row.get("business_id"), row.get("role"))
        counts[key] = counts.get(key, 0) + 1
    return counts


def demand(businesses: list, model: dict, seating: dict) -> list:
    """One row per house and role row the typical band is short in.

    A CLASS CAN NAME THE SAME ROLE TWICE — a printing office wants a journeyman
    printer AND a printer's boy, both `role: printer` — so the hands standing in a
    house are allotted across that role's rows before any of them is called short.
    Without that, every hand counted against both rows and the shortfall read low;
    with it, a hand fills the first row it can and the second row is honestly short.
    """
    standing = hands_already_in_the_house(businesses, seating)
    rows = []
    for business, klass in staffable(businesses, model):
        by_role: dict = {}
        for role in klass.get("staff_roles") or []:
            by_role.setdefault(role["role"], []).append(role)
        for name, role_rows in sorted(by_role.items()):
            pool = standing.get((business["id"], name), 0)
            # The same allotment again at the model's LOW band, on its own pool, so the
            # second of the three answers can be priced row by row rather than from a
            # pair of totals. It has to be a separate pass: a hand that fills the first
            # row to its TYPICAL count may only be owed to the low one, and the hands
            # left for the second row differ accordingly.
            low_pool = pool
            low_short = []
            for role in role_rows:
                low = int(role.get("count_low") or 0)
                taken_low = min(low_pool, low)
                low_pool -= taken_low
                low_short.append(low - taken_low)
            for index, role in enumerate(role_rows):
                typical = int(role.get("count_typical") or 0)
                taken = min(pool, typical)
                pool -= taken
                short = typical - taken
                if short <= 0:
                    continue
                rows.append({
                    "business_id": business["id"],
                    "business_name": business.get("name"),
                    "establishment_class": klass["class"],
                    "reads_as": klass.get("reads_as"),
                    "role": name,
                    "role_row": index,
                    "occupation_term": role.get("occupation_term"),
                    "household_relationship": role.get("household_relationship"),
                    "sex_rule": role.get("sex_rule"),
                    "age_band": role.get("age_band"),
                    "lives_on_premises": role.get("lives_on_premises"),
                    "count_low": int(role.get("count_low") or 0),
                    "count_typical": typical,
                    "count_high": int(role.get("count_high") or 0),
                    "standing_today": taken,
                    "short_by": short,
                    "short_by_at_the_low_band": low_short[index],
                    "basis": role.get("basis"),
                    "note": role.get("note"),
                })
    rows.sort(key=lambda r: (r["business_id"], r["role"], r["role_row"]))
    return rows


# ------------------------------------------------------- what the book holds --

def outstanding_trade_slots(book: dict) -> list:
    """The book's `.../trade` person buckets with slots left — `to_reconstruct` less
    `filled`. A bucket whose stage has already drawn it out is not a slot: the book's
    `no_bucket_overfilled` invariant is what makes that a fact and not a convention."""
    family = next((f for f in book.get("bucket_families") or []
                   if f.get("key") == "persons"), None)
    if family is None:
        raise Fault("the order book carries no `persons` bucket family")
    slots = []
    for bucket in family.get("buckets") or []:
        axes = bucket.get("axes") or {}
        if axes.get("trade") != "trade":
            continue
        left = int(bucket.get("to_reconstruct") or 0) - int(bucket.get("filled") or 0)
        if left <= 0:
            continue
        slots.append({
            "bucket": bucket.get("key"),
            "sex": axes.get("sex"),
            "age_band": axes.get("age_band"),
            "division": axes.get("division"),
            "household_type": axes.get("household_type"),
            "outstanding": left,
            "owning_ticket": bucket.get("owning_ticket"),
        })
    slots.sort(key=lambda s: s["bucket"])
    return slots


def bands_overlap(role_band: str, book_band: str) -> bool:
    low_a, high_a = ROLE_BAND_YEARS[role_band]
    low_b, high_b = BOOK_BAND_YEARS[book_band]
    return low_a <= high_b and low_b <= high_a


def pay_the_demand(rows: list, slots: list) -> dict:
    """Spend the book's outstanding slots on the demand, and report the residue.

    THE ORDER IS STATED AND DETERMINISTIC, because it decides who goes unpaid. Demand
    is taken in the order the rows already carry — business id, then role, then the
    role's own row — and each hand is paid from the first overlapping bucket by key.
    No draw, no seed and no weighting: this is an arithmetic of slots, and a weighted
    one would read as a placement decision the mint has not been authorised to make.
    """
    purse = {slot["bucket"]: slot["outstanding"] for slot in slots}
    by_bucket = {slot["bucket"]: slot for slot in slots}
    paid_rows = []
    for row in rows:
        want = row["short_by"]
        sexes = SEX_RULE_PAYS_FROM.get(row["sex_rule"], [])
        payable = [key for key in sorted(purse)
                   if by_bucket[key]["sex"] in sexes
                   and bands_overlap(row["age_band"], by_bucket[key]["age_band"])]
        spent = []
        for key in payable:
            if want <= 0:
                break
            take = min(want, purse[key])
            if take <= 0:
                continue
            purse[key] -= take
            want -= take
            spent.append({"bucket": key, "hands": take})
        paid_rows.append({
            **row,
            "paid_from": spent,
            "paid": row["short_by"] - want,
            "unpaid": want,
        })
    return {
        "rows": paid_rows,
        "purse_left": {key: left for key, left in sorted(purse.items()) if left > 0},
    }


def lives_in_the_employer_s_household(model: dict) -> set:
    """The `class/role/relationship` keys the staffing model's own shop-household rule
    lists under `who_lives_in` — the roles whose holders it houses with their employer
    rather than in lodgings of their own. Read, never restated: the rule is T-1163's and
    this file has no licence to widen or narrow it."""
    rule = model.get("the_shop_household_rule") or {}
    return set(rule.get("who_lives_in") or [])


def _household_key(row: dict) -> str:
    return f"{row['establishment_class']}/{row['role']}/{row['household_relationship']}"


def _placement_tally(rows: list, businesses: list) -> dict:
    """Paid hands by what the register makes of their house's place — `premises` where a
    structure holds it, `street_only` where a street does and no building, `unplaceable`
    where neither. The division axis can only be priced for the first two, which is why
    this counts rather than asserts."""
    by_id = {business["id"]: business for business in businesses}
    out: dict = {}
    for row in rows:
        business = by_id.get(row["business_id"]) or {}
        primary = next((loc for loc in business.get("locations") or []
                        if loc.get("primary")), None)
        kind = (primary or {}).get("kind") or "no_location_row"
        out[kind] = out.get(kind, 0) + row["paid"]
    return out


def outstanding_family_trade_slots(book: dict) -> int:
    """The `family/trade` slots left — the household type a hand who sleeps in the
    employer's house would have to be paid from. Counted so that "there is no purse for
    them" is a measurement rather than an assertion."""
    family = next((f for f in book.get("bucket_families") or []
                   if f.get("key") == "persons"), None)
    if family is None:
        raise Fault("the order book carries no `persons` bucket family")
    left = 0
    for bucket in family.get("buckets") or []:
        axes = bucket.get("axes") or {}
        if axes.get("trade") != "trade" or axes.get("household_type") != "family":
            continue
        left += max(0, int(bucket.get("to_reconstruct") or 0)
                    - int(bucket.get("filled") or 0))
    return left


def the_bed_bound(lodgers: dict) -> dict:
    """The boarders stage's own bed accounting, quoted. A `lodging/trade` slot is a
    quota; a bed is somewhere to sleep. Nothing here is computed — every figure and the
    sentence with them are `1835_lodgers_seated.json`'s, so this file cannot go on
    pricing a mint against beds the town has stopped having."""
    measurement = lodgers.get("measurement") or {}
    reconciled = measurement.get("the_two_counts_reconciled") or {}
    if "ordinary_night_beds_still_empty" not in measurement:
        raise Fault("the committed lodging accounting no longer states how many "
                    "ordinary-night beds stand empty")
    return {
        "read_from": "data/reconstruction/1835_lodgers_seated.json",
        "ticket": lodgers.get("ticket"),
        "built_lodging_places": measurement.get("built_lodging_places"),
        "ordinary_night_beds": measurement.get("ordinary_night_beds"),
        "ordinary_night_beds_slept_in": measurement.get("occupied_after_this_stage"),
        "ordinary_night_beds_still_empty":
            int(measurement.get("ordinary_night_beds_still_empty") or 0),
        "lodging_places_unbuilt": reconciled.get("lodging_places_unbuilt"),
        "may_anything_more_be_minted_here":
            reconciled.get("may_anything_more_be_minted_here"),
    }


# ----------------------------------------------------------------- the order --

def _tally(rows: list, key) -> list:
    out: dict = {}
    for row in rows:
        out[key(row)] = out.get(key(row), 0) + row["short_by"]
    return [{"key": list(k) if isinstance(k, tuple) else k, "hands": v}
            for k, v in sorted(out.items())]


def order(data: dict) -> dict:
    rows = demand(data["businesses"], data["model"], data["seating"])
    slots = outstanding_trade_slots(data["book"])
    paid = pay_the_demand(rows, slots)
    wanted = sum(row["short_by"] for row in rows)
    unpaid = sum(row["unpaid"] for row in paid["rows"])
    by_sex: dict = {}
    by_band: dict = {}
    for row in rows:
        by_sex[row["sex_rule"]] = by_sex.get(row["sex_rule"], 0) + row["short_by"]
        by_band[row["age_band"]] = by_band.get(row["age_band"], 0) + row["short_by"]
    purse_by_sex: dict = {}
    for slot in slots:
        purse_by_sex[slot["sex"]] = purse_by_sex.get(slot["sex"], 0) + slot["outstanding"]
    youth_slots = sum(slot["outstanding"] for slot in slots
                      if bands_overlap("youth_12_18", slot["age_band"]))
    youth_wanted = sum(row["short_by"] for row in rows if row["age_band"] == "youth_12_18")
    youth_slots_by_sex: dict = {}
    for slot in slots:
        if bands_overlap("youth_12_18", slot["age_band"]):
            youth_slots_by_sex[slot["sex"]] = (youth_slots_by_sex.get(slot["sex"], 0)
                                               + slot["outstanding"])
    payable_from_a_woman = sum(row["short_by"] for row in rows
                               if "female" in SEX_RULE_PAYS_FROM.get(row["sex_rule"], []))
    slots_outstanding = sum(slot["outstanding"] for slot in slots)
    payable = wanted - unpaid
    recut = data["book"].get("trade_re_cut") or {}

    # THE SECOND ANSWER, PRICED. `the_demand` has always claimed that `count_low` is
    # carried on every row "so a reader can price the other two answers", and until
    # 2026-09-25 it was not carried at all — so the one answer the arithmetic could
    # actually settle was the one nobody could read. Coming down to the model's low
    # band is a smaller demand against the SAME purse, so it is paid the same way.
    low_rows = [{**row, "short_by": row["short_by_at_the_low_band"]}
                for row in rows if row["short_by_at_the_low_band"] > 0]
    low_paid = pay_the_demand(low_rows, slots)
    low_wanted = sum(row["short_by"] for row in low_rows)
    low_unpaid = sum(row["unpaid"] for row in low_paid["rows"])
    low_payable = low_wanted - low_unpaid

    # THE RULED BAND, CARRIED ONTO THE ROWS. The owner ruled the low band, so the
    # allocation it implies stops being an aside in `the_collision` and becomes the
    # mint's own input: house by house, which bucket pays for which hand. Merged by
    # (house, role, role row) rather than by position, because the low pass runs over a
    # FILTERED set of rows and a positional merge would silently shift the payments one
    # house to the left the first time a row dropped out of it.
    low_by_key = {(row["business_id"], row["role"], row["role_row"]): row
                  for row in low_paid["rows"]}

    # AND WHAT THE RULED ALLOCATION ACTUALLY BUYS, on two axes `pay_the_demand` does not
    # look at and a bound nothing had counted. Neither is a refusal of the ruling: the
    # ruling is the band, and these are what the band costs on the town as committed.
    lives_in = lives_in_the_employer_s_household(data["model"])
    ruled = [row for row in low_paid["rows"] if row["paid"] > 0]
    housed_with_the_employer = sum(row["paid"] for row in ruled
                                   if _household_key(row) in lives_in)
    certainly_housed = sum(row["paid"] for row in ruled
                           if float(row["lives_on_premises"] or 0) >= 1.0)
    family_trade_left = outstanding_family_trade_slots(data["book"])
    beds = the_bed_bound(data["lodgers"])
    needing_a_bed = low_payable - certainly_housed
    mintable_today = min(needing_a_bed, beds["ordinary_night_beds_still_empty"])
    by_premises_share: dict = {}
    for row in ruled:
        share = float(row["lives_on_premises"] or 0)
        key = f"{share:.1f}"
        by_premises_share[key] = by_premises_share.get(key, 0) + row["paid"]

    # THE SENTENCES BELOW ARE DERIVED, NOT WRITTEN. Three of them used to be literals,
    # and by 2026-09-25 all three were false: the re-cut this file asked for had run
    # (T-1459, T-1503, T-1525) and opened the very band they said was drawn out, so the
    # adjudication was arguing from a book that had moved under it. A file whose whole
    # job is to make a ruling askable may not narrate a state it no longer measures, so
    # every clause that names a quantity now reads that quantity off `slots`/`rows` and
    # the assertions below fire on the wording as well as on the number.
    if payable_from_a_woman == 0:
        on_the_sex_reads_as = (
            f"Every one of the {wanted} hands the shops want is a man or a role the "
            f"model calls predominantly male — not one of them could be paid from a "
            f"woman's slot. "
            f"{purse_by_sex.get('female', 0)} of the book's {slots_outstanding} "
            f"outstanding slots are women's, and they cannot be spent here at all.")
    else:
        on_the_sex_reads_as = (
            f"{payable_from_a_woman} of the {wanted} hands wanted may be paid from a "
            f"woman's slot, against {purse_by_sex.get('female', 0)} women's slots of "
            f"the book's {slots_outstanding} outstanding. The other "
            f"{wanted - payable_from_a_woman} are men's, or roles the model calls "
            f"predominantly male, and the women's slots cannot be spent on them.")
    if youth_slots == 0:
        on_the_age_reads_as = (
            f"The apprentice and the shop boy are {youth_wanted} of the {wanted} hands "
            f"wanted. The book's 10-19 trade buckets are drawn out, so there is no slot "
            f"a boy could be minted into without re-cutting.")
    else:
        on_the_age_reads_as = (
            f"The apprentice and the shop boy are {youth_wanted} of the {wanted} hands "
            f"wanted, and the band that reaches them is NO LONGER DRAWN OUT: "
            f"{youth_slots} slot(s) stand outstanding in it, "
            f"{youth_slots_by_sex.get('male', 0)} of them men's and so spendable on a "
            f"boy, {youth_slots_by_sex.get('female', 0)} of them women's and so not. "
            f"The age bar this file was written against is paid for; the sex bar is not.")

    return {
        "$schema_note": "DERIVED — regenerate with tools/staffing_mint_order_1835.py "
                        "--build; tools/check.sh re-derives it. Do not hand-edit.",
        "id": "1835_staffing_mint_order",
        "ticket": TICKET,
        "parent_ticket": PARENT_TICKET,
        "grandparent_ticket": GRANDPARENT_TICKET,
        "target_date": TARGET_DATE,
        "generated_by": "tools/staffing_mint_order_1835.py --build",
        "not_a_reading": "an adjudication over committed files — no page of any source "
                         "is read here",
        "mints_nobody": True,
        "writes_no_person": True,
        "raises_no_business": True,
        "fills_no_bucket": "An order is not a fill. Nothing here increments a bucket's "
                           "`filled` or adds a row to the order book's `fills` ledger; "
                           "those counters stay where the stages that earned them left "
                           "them, and the mint is what will move them.",
        "inputs": [
            "data/businesses/*.json",
            "data/reconstruction/1835_business_staffing_model.json",
            "data/reconstruction/1835_reconstruction_order_book.json",
            "data/residents/reconstructed_seating.json",
            "data/reconstruction/1835_lodgers_seated.json",
        ],
        "what_the_re_cut_returned": {
            "what_it_is": "The first of the answers below was RULED by the owner and "
                          "has since been SPENT: the book was re-cut. These are the "
                          "re-cut's own words and figures, read from "
                          "data/reconstruction/1835_reconstruction_order_book.json, so "
                          "that this file cannot go on arguing from a book that has "
                          "moved under it.",
            "ruling": recut.get("ruling"),
            "ticket": recut.get("ticket"),
            "slots_the_re_cut_wanted": recut.get("the_re_cut_wanted"),
            "slots_that_moved": recut.get("what_moved"),
            "why_it_stopped": recut.get("why_it_stopped"),
            "the_sex_axis": recut.get("the_sex_axis"),
            "and_the_mint_is_still_short": (
                f"After the re-cut, {payable} of the {wanted} hands are payable and "
                f"{unpaid} are not. The re-cut opened the band the shop boys stand in "
                f"— {youth_slots} slot(s) outstanding in it now — and refused the sex "
                f"axis on the evidence. The sex bar is what the {unpaid} stand behind, "
                f"and re-cutting again cannot move it."),
        },
        "the_question": {
            "for": "the owner, and T-1166 which owns the order book",
            "asked": f"The shops want {wanted} hands and the book has "
                     f"{slots_outstanding} outstanding trade slots, of which "
                     f"{purse_by_sex.get('female', 0)} are women's and cannot be spent "
                     f"on them. Spent greedily in the stated order the book pays for "
                     f"{payable} and leaves {unpaid} with nowhere to come from — and "
                     f"every payable slot belongs to another stage. Which gives way?",
            "the_answers_as_this_project_sees_them": [
                "RE-CUT THE BOOK (T-1166) — RULED, RUN AND SPENT; see "
                "`what_the_re_cut_returned` above. It opened the band the shop boys "
                "stand in and it refused the sex axis on the evidence, so it did not "
                "make the mint payable to the typical band. This answer is no longer "
                "on the table, and the two below are.",
                f"COME DOWN OFF THE TYPICAL BAND. Staff every house to the model's own "
                f"`count_low` instead and the demand falls from {wanted} hands to "
                f"{low_wanted}, of which the book pays for {low_wanted - low_unpaid} "
                f"and leaves {low_unpaid} short. `count_low` and "
                f"`short_by_at_the_low_band` are carried on every row below, so this "
                f"answer prices house by house and not only in totals. A low-band town "
                f"is inside the staffing model's own stated range.",
                "LET THE HOUSES STAND SHORT AND SAY SO. Mint nothing, and let the "
                "business card print the shortfall as the honest state of the evidence. "
                "It costs the layer nothing and it is the only answer that invents "
                "nobody.",
            ],
            "answered": "ANSWERED on 2026-09-25 — the owner took the second answer, "
                        "the model's LOW band. The three are kept below because the "
                        "ruling is only readable against what it chose between. What "
                        "the answer buys is `the_owner_s_ruling` above.",
            "what_this_tool_will_not_do": "Choose. Every one of them changes what the "
                                          "town IS, and this file exists to make the "
                                          "choice askable with numbers rather than to "
                                          "make it quietly by running.",
        },
        "the_demand": {
            "what_it_is": "The hands the staffing model's TYPICAL band wants and no "
                          "house has. `count_low` and `count_high` are carried on every "
                          "row so a reader can price the other two answers.",
            "hands_wanted": wanted,
            "houses_short": len({row["business_id"] for row in rows}),
            "houses_staffable": len(staffable(data["businesses"], data["model"])),
            "by_sex_rule": dict(sorted(by_sex.items())),
            "by_age_band": dict(sorted(by_band.items())),
            "by_role": _tally(rows, lambda r: (r["occupation_term"], r["sex_rule"],
                                               r["age_band"])),
        },
        "what_the_book_can_pay": {
            "what_it_is": "The order book's `.../trade` person buckets with slots left. "
                          "Every one of them is a `lodging/trade` bucket and every one "
                          "is owned by T-1532, the working lodgers — so a mint that "
                          "spends them spends another stage's quota, which is itself "
                          "part of the question above. T-1532 because T-1175, which held "
                          "these buckets when this sentence was written, split and left "
                          "them ordered by nobody; T-1420 swept the book onto the live "
                          "placeholder T-1500 on 2026-09-21, and T-1500 cut the bed "
                          "buckets three ways on 2026-09-24, the `lodging/trade` third "
                          "of them to T-1532. The stage is the same stage throughout.",
            "slots_outstanding": sum(slot["outstanding"] for slot in slots),
            "by_sex": dict(sorted(purse_by_sex.items())),
            "owning_tickets": sorted({slot["owning_ticket"] for slot in slots
                                      if slot.get("owning_ticket")}),
            "buckets": slots,
        },
        "the_collision": {
            "on_the_count": {
                "hands_wanted": wanted,
                "slots_outstanding": sum(slot["outstanding"] for slot in slots),
                "short_by": wanted - sum(slot["outstanding"] for slot in slots),
            },
            "on_the_sex": {
                "hands_wanted_that_may_be_paid_from_a_woman_s_slot": sum(
                    row["short_by"] for row in rows
                    if "female" in SEX_RULE_PAYS_FROM.get(row["sex_rule"], [])),
                "women_s_slots_outstanding": purse_by_sex.get("female", 0),
                "reads_as": on_the_sex_reads_as,
            },
            "on_the_age": {
                "boys_wanted_12_to_18": youth_wanted,
                "slots_outstanding_in_a_band_that_reaches_them": youth_slots,
                "slots_in_that_band_by_sex": dict(sorted(youth_slots_by_sex.items())),
                "reads_as": on_the_age_reads_as,
            },
            "what_the_book_could_pay_for_today": wanted - unpaid,
            "what_would_go_unpaid": unpaid,
            "slots_that_would_be_left": paid["purse_left"],
            "at_the_model_s_low_band": {
                "what_it_is": "The same arithmetic against the second answer — every "
                              "house staffed to `count_low` rather than to the typical "
                              "band, paid from the same purse in the same order.",
                "hands_wanted": low_wanted,
                "houses_short": len({row["business_id"] for row in low_rows}),
                "what_the_book_could_pay_for": low_wanted - low_unpaid,
                "what_would_go_unpaid": low_unpaid,
                "slots_that_would_be_left": low_paid["purse_left"],
            },
        },
        "the_owner_s_ruling": {
            "what_it_is": "The owner's answer to the question below, and what it buys "
                          "on the town as committed. The question is ANSWERED; this "
                          "block is the price the mint stage runs from.",
            "asked": "2026-09-25",
            "answered": "2026-09-25",
            "answer": "a",
            "what_it_ruled": "Mint to the model's LOW band: the hands the book can pay "
                             "for minted out of the outstanding lodging/trade slots, "
                             "the houses it cannot reach left short and saying so on "
                             "the business card.",
            "why_that_one": "It is the band the staffing model itself states for this "
                            "case, it leaves the smallest unexplained gap, and the "
                            "houses it fills are chosen by a stated band rather than by "
                            "the order the arithmetic happens to run in.",
            "hands_the_ruling_wants": low_wanted,
            "hands_the_book_pays_for_in_slots": low_payable,
            "houses_left_short": low_unpaid,
            "on_the_household_axis": {
                "what_it_is": "A slot is not only a sex and an age band; it is also a "
                              "HOUSEHOLD TYPE, and `pay_the_demand` does not look at "
                              "one. Every slot it can reach is a `lodging/trade` "
                              "bucket — a person the book orders into a lodging "
                              "household — and the staffing model's own "
                              "`the_shop_household_rule` houses the on-premises share "
                              "of these roles with their EMPLOYER instead.",
                "the_rule_it_reads":
                    (data["model"].get("the_shop_household_rule") or {}).get("rule"),
                "hands_paid_for_whose_role_the_rule_houses_with_the_employer":
                    housed_with_the_employer,
                "hands_paid_for_the_model_houses_there_at_every_share": certainly_housed,
                "family_trade_slots_outstanding": family_trade_left,
                "reads_as": (
                    f"Of the {low_payable} hands the ruling buys, "
                    f"{housed_with_the_employer} hold a role the model's own rule "
                    f"houses with their employer, and {certainly_housed} of those it "
                    f"states at `lives_on_premises: 1.0` — a household member at every "
                    f"share of the role, and so not a lodger a `lodging/trade` slot can "
                    f"pay for at all. The household type that could pay for them is "
                    f"`family/trade`, and it has {family_trade_left} slot(s) "
                    f"outstanding."),
                "hands_paid_for_by_the_share_the_model_states": dict(
                    sorted(by_premises_share.items(), key=lambda kv: -float(kv[0]))),
            },
            "on_the_bed_bound": {
                "what_it_is": "A lodging slot is a quota and a bed is somewhere to "
                              "sleep, and the second is the binding one. A lodger has "
                              "to be seated in a house that stands, on the boarders "
                              "stage's own bed accounting — the same bound T-1532 is "
                              "blocked on.",
                **beds,
                "hands_of_the_ruling_that_would_need_a_bed": needing_a_bed,
                "reads_as": (
                    f"{needing_a_bed} of the {low_payable} hands the ruling buys would "
                    f"have to be seated as lodgers, and "
                    f"{beds['ordinary_night_beds_still_empty']} ordinary-night bed(s) "
                    f"stand empty in the "
                    f"{beds['built_lodging_places']} built lodging places. The "
                    f"{beds['lodging_places_unbuilt']} lodging roofs the model "
                    f"schedules and nothing has raised are where the rest of the beds "
                    f"are."),
            },
            "mintable_today": mintable_today,
            "reads_as": (
                f"The ruling stands and the arithmetic under it is unchanged: "
                f"{low_wanted} hands wanted at the low band, {low_payable} of them "
                f"payable in slots. What the town cannot do today is SEAT them. "
                f"{certainly_housed} are household members the lodging purse is the "
                f"wrong household type for, and the {needing_a_bed} left need a bed "
                f"against {beds['ordinary_night_beds_still_empty']} empty. So "
                f"{mintable_today} of them can be minted on the files as committed. "
                f"This is a bed bound and a household-type bound, not a ruling that "
                f"has been refused, and neither can be lifted by re-cutting the book."
                if mintable_today < low_payable else
                f"The ruling is payable and seatable: {mintable_today} of the "
                f"{low_payable} hands it buys can be minted on the files as "
                f"committed."),
            "waits_on": [
                "T-1209 — raise the lodging roofs the model schedules; the beds are "
                "there and nowhere else",
                "T-1538 — seat the houses once they stand",
                "T-1532 — the working lodgers, blocked on the same bound, whose "
                "lodging/trade buckets this purse is",
            ],
            "and_the_division_axis_is_not_priced_either": {
                "what_it_is": "A third axis the payment does not look at: a slot names "
                              "the DIVISION the book is short of a person in, and a "
                              "hand is paid from the first bucket by key whatever "
                              "division its house stands in. It is named here and not "
                              "closed here, because for most of these houses it cannot "
                              "be: the register places no premises for them.",
                "hands_paid_for_by_the_placement_of_their_house": dict(sorted(
                    _placement_tally(ruled, data["businesses"]).items())),
                "filed_as": "T-1566, beside this one",
            },
        },
        "rows": [
            {
                **row,
                "paid_from_at_the_low_band": low_by_key.get(
                    (row["business_id"], row["role"], row["role_row"]),
                    {}).get("paid_from", []),
                "paid_at_the_low_band": low_by_key.get(
                    (row["business_id"], row["role"], row["role_row"]),
                    {}).get("paid", 0),
                "unpaid_at_the_low_band": low_by_key.get(
                    (row["business_id"], row["role"], row["role_row"]),
                    {}).get("unpaid", 0),
            }
            for row in paid["rows"]
        ],
        "how_the_two_vocabularies_were_matched": {
            "why": "The staffing model counts hands in its own age terms and the book "
                   "counts people in the 1840 schedule's bands. A slot pays for a hand "
                   "only where the two OVERLAP in years, and nothing is widened to make "
                   "a band reach a slot it does not reach.",
            "the_model_s_bands": {k: list(v) for k, v in sorted(ROLE_BAND_YEARS.items())},
            "the_book_s_bands": {k: list(v) for k, v in sorted(BOOK_BAND_YEARS.items())},
            "sex_rules_pay_from": {k: list(v) for k, v in sorted(SEX_RULE_PAYS_FROM.items())},
            "predominantly_male": "paid as male. The model's own gloss declines to "
                                  "refuse a woman the role; declining to refuse is not "
                                  "evidence of one, and spending a woman's slot on it "
                                  "would read that word as if it were.",
        },
        "what_this_does_not_do": {
            "it_does_not_mint": "T-1434's mint is the act this file prices, and the "
                               "question it made askable has been answered — the low "
                               "band, 2026-09-25. What stands between the ruling and the "
                               "mint now is `the_owner_s_ruling.mintable_today`: a "
                               "lodging slot is not a bed and the built houses have "
                               "none empty, and the hands the model puts in their "
                               "employer's household would need a `family/trade` slot, "
                               "of which none is outstanding. Minting past either would "
                               "overfill the book, which its `no_bucket_overfilled` "
                               "invariant refuses, or seat a lodger in a bed the town "
                               "does not have.",
            "it_does_not_re_cut_the_book": "Reading a book and proposing one are "
                                           "different acts. T-1166 owns the cut.",
            "it_does_not_seat_anybody": "T-1449 closes the join — the minted hands on "
                                        "the businesses' `staff[]`, every working-age "
                                        "person a workplace or an explicit reason, and "
                                        "the business card printing its people.",
            "the_domestics_are_not_here": "T-1433 found 62 reconstructed domestics it "
                                          "could not seat because the taverns and hotels "
                                          "are already full to the model's HIGH band. "
                                          "That is a town owed more lodging houses, not "
                                          "a house short of hands, and it is not a row "
                                          "in this order.",
        },
    }


def build_data() -> dict:
    return {
        "businesses": _businesses(),
        "model": _load(MODEL),
        "book": _load(ORDER_BOOK),
        "seating": _load(SEATING),
        "lodgers": _load(LODGERS_SEATED),
    }


def _write(doc: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ------------------------------------------------------------------- the CLI --

def cmd_build() -> int:
    doc = order(build_data())
    _write(doc)
    ruling = doc["the_owner_s_ruling"]
    print(f"wrote {OUT.relative_to(ROOT)} — {doc['the_demand']['hands_wanted']} hand(s) "
          f"wanted over {doc['the_demand']['houses_short']} house(s); the book can pay "
          f"for {doc['the_collision']['what_the_book_could_pay_for_today']} and "
          f"{doc['the_collision']['what_would_go_unpaid']} would go unpaid. At the "
          f"ruled LOW band: {ruling['hands_the_ruling_wants']} wanted, "
          f"{ruling['hands_the_book_pays_for_in_slots']} payable in slots, "
          f"{ruling['mintable_today']} mintable today")
    return 0


def cmd_check() -> int:
    if not OUT.exists():
        raise Fault(f"{OUT.relative_to(ROOT)} has never been built — run "
                    "tools/staffing_mint_order_1835.py --build")
    was = _load(OUT)
    now = order(build_data())
    if was != now:
        raise Fault(f"{OUT.relative_to(ROOT)} no longer re-derives from the files it "
                    "reads — run tools/staffing_mint_order_1835.py --build and read the "
                    "diff before committing it")
    print(f"{OUT.relative_to(ROOT)} re-derives — "
          f"{now['the_demand']['hands_wanted']} hand(s) wanted, "
          f"{now['what_the_book_can_pay']['slots_outstanding']} slot(s) outstanding")
    return 0


def cmd_self_test() -> int:
    """Fourteen assertions, fired on the real data by breaking it on a copy."""
    data = build_data()
    doc = order(data)
    failures = []

    def fires(name, fn):
        try:
            fn()
        except (Fault, AssertionError):
            return
        failures.append(name)

    # 1. A house at or above the typical band in a role is never counted short in it.
    for row in doc["rows"]:
        if row["standing_today"] >= row["count_typical"]:
            failures.append("a house already at its typical band was counted short")
            break

    # 2. Every demand row names a sex rule and an age band the two vocabularies know.
    for row in doc["rows"]:
        if row["sex_rule"] not in SEX_RULE_PAYS_FROM or row["age_band"] not in ROLE_BAND_YEARS:
            failures.append("a demand row carries a sex rule or age band no vocabulary knows")
            break

    # 3. The hands already standing are counted. Drop T-1433's seats and the demand must rise.
    thinner = dict(data)
    thinner["seating"] = {**data["seating"], "rows": []}
    if order(thinner)["the_demand"]["hands_wanted"] <= doc["the_demand"]["hands_wanted"]:
        failures.append("dropping the seated hands did not raise the demand — "
                        "the standing count is not being read")

    # 4. No bucket is ever spent past its outstanding slots.
    spent: dict = {}
    for row in doc["rows"]:
        for payment in row["paid_from"]:
            spent[payment["bucket"]] = spent.get(payment["bucket"], 0) + payment["hands"]
    for slot in doc["what_the_book_can_pay"]["buckets"]:
        if spent.get(slot["bucket"], 0) > slot["outstanding"]:
            failures.append(f"{slot['bucket']} was spent past its outstanding slots")
            break

    # 5. A slot only pays where the bands overlap and the sex rule allows it.
    by_bucket = {s["bucket"]: s for s in doc["what_the_book_can_pay"]["buckets"]}
    for row in doc["rows"]:
        for payment in row["paid_from"]:
            slot = by_bucket[payment["bucket"]]
            if slot["sex"] not in SEX_RULE_PAYS_FROM[row["sex_rule"]] \
                    or not bands_overlap(row["age_band"], slot["age_band"]):
                failures.append("a slot paid for a hand it does not reach")
                break

    # 6. --check refuses a hand-edited order.
    fires("--check accepted a hand-edited order", lambda: _check_against({
        **doc, "the_demand": {**doc["the_demand"], "hands_wanted": 0}}))

    # 7. The order book with no outstanding trade slot pays for nobody.
    empty = dict(data)
    book = json.loads(json.dumps(data["book"]))
    for family in book["bucket_families"]:
        if family["key"] != "persons":
            continue
        for bucket in family["buckets"]:
            bucket["filled"] = bucket["to_reconstruct"]
    empty["book"] = book
    if order(empty)["the_collision"]["what_the_book_could_pay_for_today"] != 0:
        failures.append("a drawn-out book still paid for hands")

    # 8. THE PROSE TRACKS THE COUNT. The sentence under `on_the_age` may only say the
    #    boys' band is drawn out when it is: the literal it replaced went on saying so
    #    for four days after the re-cut had opened it. Fired both ways — on the real
    #    book, which has slots in that band, and on the drawn-out copy from 7.
    live_age = doc["the_collision"]["on_the_age"]
    if live_age["slots_outstanding_in_a_band_that_reaches_them"] > 0 \
            and "drawn out" in live_age["reads_as"].lower() \
            and "no longer drawn out" not in live_age["reads_as"].lower():
        failures.append("the age sentence calls the boys' band drawn out while its own "
                        "count says slots stand in it")
    empty_age = order(empty)["the_collision"]["on_the_age"]
    if empty_age["slots_outstanding_in_a_band_that_reaches_them"] == 0 \
            and "no longer drawn out" in empty_age["reads_as"].lower():
        failures.append("the age sentence called a drawn-out band open")

    # 9. THE LOW BAND IS A REAL SECOND PASS, not the typical demand scaled. Every role
    #    the model states low at or below typical, and the low-band demand is therefore
    #    never the larger of the two.
    for row in doc["rows"]:
        if row["count_low"] > row["count_typical"]:
            failures.append(f"{row['business_id']}/{row['role']} states a low band above "
                            "its typical one, so the low-band pricing is not bounded")
            break
    if doc["the_collision"]["at_the_model_s_low_band"]["hands_wanted"] > \
            doc["the_demand"]["hands_wanted"]:
        failures.append("the low band wants more hands than the typical band")

    # 10. The re-cut block is the BOOK's words, not this file's. Change the book's and
    #     the order must change with it.
    moved = dict(data)
    book_moved = json.loads(json.dumps(data["book"]))
    book_moved["trade_re_cut"]["why_it_stopped"] = "a sentence this file did not write"
    moved["book"] = book_moved
    if order(moved)["what_the_re_cut_returned"]["why_it_stopped"] \
            == doc["what_the_re_cut_returned"]["why_it_stopped"]:
        failures.append("the re-cut block does not follow the order book's own words")

    # 11. THE BED BOUND IS THE LODGING FILE'S, NOT THIS ONE'S. Empty beds on a copy and
    #     `mintable_today` must rise with them. A bound this file asserted rather than
    #     read would be a bound that stays true after the town stops being like that,
    #     which is the failure mode the derived prose above was written against.
    bedded = dict(data)
    lodgers = json.loads(json.dumps(data["lodgers"]))
    lodgers["measurement"]["ordinary_night_beds_still_empty"] = 500
    bedded["lodgers"] = lodgers
    if order(bedded)["the_owner_s_ruling"]["mintable_today"] \
            <= doc["the_owner_s_ruling"]["mintable_today"]:
        failures.append("emptying the town's beds did not raise what the ruling can "
                        "mint — the bed bound is not being read")
    fires("the bed bound survived a lodging file that states no bed count",
          lambda: the_bed_bound({"measurement": {}}))

    # 12. THE HOUSEHOLD AXIS IS THE STAFFING MODEL'S OWN RULE. Empty `who_lives_in` on a
    #     copy and the count of hands it houses with the employer must fall to nought.
    unhoused = dict(data)
    model_copy = json.loads(json.dumps(data["model"]))
    model_copy["the_shop_household_rule"]["who_lives_in"] = []
    unhoused["model"] = model_copy
    if order(unhoused)["the_owner_s_ruling"]["on_the_household_axis"][
            "hands_paid_for_whose_role_the_rule_houses_with_the_employer"] != 0:
        failures.append("the household axis does not follow the staffing model's own "
                        "`who_lives_in` rule")

    # 13. THE RULED ALLOCATION IS THE LOW BAND'S AND IS BOUNDED BY IT. Every row's ruled
    #     payment plus its ruled residue is that row's low-band shortfall exactly, and
    #     the total paid is the figure the ruling block prints. A merge that shifted the
    #     payments between rows would pass on the totals alone and fail here.
    ruled_paid = 0
    for row in doc["rows"]:
        if row["paid_at_the_low_band"] + row["unpaid_at_the_low_band"] \
                != row["short_by_at_the_low_band"]:
            failures.append(f"{row['business_id']}/{row['role']} carries a ruled "
                            "allocation that does not add up to its low-band shortfall")
            break
        ruled_paid += row["paid_at_the_low_band"]
    if ruled_paid != doc["the_owner_s_ruling"]["hands_the_book_pays_for_in_slots"]:
        failures.append("the ruled allocation on the rows does not total what the "
                        "ruling block says the book pays for")

    # 14. AND IT NEVER SPENDS A BUCKET PAST ITS SLOTS EITHER. The low pass runs over the
    #     same purse as the typical one, so the guard that holds for 4 has to hold here.
    ruled_spent: dict = {}
    for row in doc["rows"]:
        for payment in row["paid_from_at_the_low_band"]:
            ruled_spent[payment["bucket"]] = (ruled_spent.get(payment["bucket"], 0)
                                              + payment["hands"])
    for slot in doc["what_the_book_can_pay"]["buckets"]:
        if ruled_spent.get(slot["bucket"], 0) > slot["outstanding"]:
            failures.append(f"{slot['bucket']} was spent past its outstanding slots at "
                            "the ruled band")
            break

    for failure in failures:
        print(f"  FAILED: {failure}", file=sys.stderr)
    if failures:
        print(f"{len(failures)} assertion(s) did not hold", file=sys.stderr)
        return 1
    print("self-test: every assertion fires")
    return 0


def _check_against(doc: dict) -> None:
    """The comparison `--check` makes, on a document handed in rather than read from
    disk — so the self-test can fire it on a mutated copy without touching the tree."""
    if doc != order(build_data()):
        raise Fault("the order does not re-derive")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.build:
            return cmd_build()
        if args.check:
            return cmd_check()
        if args.self_test:
            return cmd_self_test()
    except Fault as fault:
        print(f"staffing_mint_order_1835: {fault}", file=sys.stderr)
        return 1
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
