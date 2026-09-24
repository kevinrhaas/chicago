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
  * every hand the shops want is a man, and two fifths of the book's remaining
    slots are women's,
  * and the shops want boys of twelve to eighteen, in a band where the book has
    no outstanding slot at all.

So the mint cannot simply run. Either the book is re-cut — the town's remaining
working people are younger and more male than a cut shaped by the 1840 schedule
assumes — or the staffing model comes down off its typical band, or the shops stand
short and the town says why. That is a ruling about what the town IS, not a detail of
how a tool draws, and T-1166 owns the book. This file is the adjudication that makes
the ruling askable: every number in it re-derives from committed files, and `--check`
refuses a byte that has drifted since.

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
                    "count_typical": typical,
                    "count_high": int(role.get("count_high") or 0),
                    "standing_today": taken,
                    "short_by": short,
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
        ],
        "the_question": {
            "for": "the owner, and T-1166 which owns the order book",
            "asked": "The shops want more hands than the book has slots left, they are "
                     "all men, and a fifth of them are boys in a band where the book "
                     "has nothing outstanding at all. Which gives way?",
            "the_three_answers_as_this_project_sees_them": [
                "RE-CUT THE BOOK (T-1166). The town's remaining working people are "
                "younger and more male than a cut shaped by the 1840 schedule's bands "
                "makes them. This is the answer that lets the mint run to the typical "
                "band, and it moves a quota five other stages draw against.",
                "COME DOWN OFF THE TYPICAL BAND. Staff every house to what the book can "
                "pay for and record the rest as a town owed more working men than it "
                "holds. The staffing model's `count_low` is 65 hands against the "
                "typical 202, so a low-band town is within the model's own range.",
                "LET THE HOUSES STAND SHORT AND SAY SO. Mint nothing, and let the "
                "business card print the shortfall as the honest state of the evidence. "
                "It costs the layer nothing and it is the only answer that invents "
                "nobody.",
            ],
            "what_this_tool_will_not_do": "Choose. Every one of the three changes what "
                                          "the town IS, and this file exists to make the "
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
                          "is owned by T-1500, the lodgers stage — so a mint that spends "
                          "them spends another stage's quota, which is itself part of "
                          "the question above. T-1500 because T-1175, which held these "
                          "buckets when this sentence was written, split and left them "
                          "ordered by nobody; T-1420 swept the book onto live owners on "
                          "2026-09-21 and the stage is the same stage.",
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
                "reads_as": "Every hand the shops want is a man or a role the model "
                            "calls predominantly male, and the book's remaining slots "
                            "are two fifths women's. Those slots cannot be spent here "
                            "at all.",
            },
            "on_the_age": {
                "boys_wanted_12_to_18": youth_wanted,
                "slots_outstanding_in_a_band_that_reaches_them": youth_slots,
                "reads_as": "The apprentice and the shop boy are a fifth of the demand. "
                            "The book's 10-19 trade buckets are drawn out, so there is "
                            "no slot a boy could be minted into without re-cutting.",
            },
            "what_the_book_could_pay_for_today": wanted - unpaid,
            "what_would_go_unpaid": unpaid,
            "slots_that_would_be_left": paid["purse_left"],
        },
        "rows": paid["rows"],
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
            "it_does_not_mint": "T-1434's mint is the act this file makes askable. Until "
                                "the question above is answered, minting to the typical "
                                "band would either overfill the book — which its "
                                "`no_bucket_overfilled` invariant refuses — or put 129 "
                                "people into the town outside the only quota this "
                                "project holds.",
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
    }


def _write(doc: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ------------------------------------------------------------------- the CLI --

def cmd_build() -> int:
    doc = order(build_data())
    _write(doc)
    print(f"wrote {OUT.relative_to(ROOT)} — {doc['the_demand']['hands_wanted']} hand(s) "
          f"wanted over {doc['the_demand']['houses_short']} house(s); the book can pay "
          f"for {doc['the_collision']['what_the_book_could_pay_for_today']} and "
          f"{doc['the_collision']['what_would_go_unpaid']} would go unpaid")
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
    """Six assertions, fired on the real data by breaking it on a copy."""
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
