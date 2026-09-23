#!/usr/bin/env python3
"""THE BUSINESS SIDE OF THE STAFFING JOIN: the hands the seating seated, written on
the houses that took them, with each house's shortfall stated beside them.

T-1462, piece 2 of 2 of T-1449, of T-1434, of T-1189.

    tools/staff_the_houses_1835.py --build       write the overlay
    tools/staff_the_houses_1835.py --check       re-derive it, refuse drift
    tools/staff_the_houses_1835.py --self-test   the guards, fired on the real data

THE GAP THIS CLOSES. T-1433 seated 124 reconstructed trade-holders in 84 houses and
wrote every seat down in `data/residents/reconstructed_seating.json` — a join BESIDE
the layer, which is what its own header calls it, keyed on `person_id` and touching
nothing. So the town knew where those people worked and **the houses did not**. Open
any one of the 84 business cards and its `staff` was empty, its "Who kept it" printed
the keeper alone, and a house standing at half the hands the staffing model gives its
class read exactly like a house standing at all of them. Two readings of one town from
two ends, with nothing holding the ends together — the same fault T-1432 fixed for the
attested half, still open for the reconstructed one.

WHAT IT WRITES, AND WHY AS AN OVERLAY. `data/businesses/*.json` is DERIVED: the
compiler rewrites each record whole from the newspaper register and `--check` refuses a
committed copy a rebuild would not produce. So a reconstructed hand cannot be written
onto a record — it has to be laid over one, exactly as T-1422's
`data/businesses/rulings/establishment_staffing.json` is, and by the same
`apply_*_overlay` machinery. The difference between the two is what a reader most needs
to know about them: that one is a RULING, hand-authored and cited, and this one is
DERIVED, a restatement of the seating join and nothing else. A ruling that moved when a
tool ran would not be a ruling; a derivation that had to be hand-maintained would rot.

IT MINTS NOBODY. Every row here is a seat `reconstructed_seating.json` already holds,
carried across at ITS OWN tier — `reconstructed`, every one of them — with its own
seed, its own basis prose and its own `replaceable_by`. No person is written, no
business is raised, no seat is invented and no seat is upgraded by being copied. The
mint of the REMAINING shortfall is T-1448's order and the stage that draws against it;
what this does is make the shortfall visible on the house it belongs to, so a
half-filled house cannot read as a full one while that mint is pending.

WHY THE ROLE ON A STAFF ROW IS THE RELATIONSHIP AND NOT THE TRADE. The staffing model
carries two words for every hand: `role`, which is the TRADE the hand works (a baker, a
dressmaker), and `household_relationship`, which is what that hand IS at the house (a
journeyman, an apprentice, a servant, a clerk, a member of the household). The
businesses schema's `role` enum is the second vocabulary — it is the resident layer's
own relationship words, held in common so that a person's household role and their
workplace role are the same word — and `tools/validate.py` polices both the staff row
and the `workplaces` entry it becomes against it. So the relationship is what goes in
`role`, the trade goes beside it in `occupation`, and the row reads as what it is: a
journeyman baker at this bakery. Writing `baker` into `role` would have meant adding
sixteen occupation words to a relationship enum to close one join, which is a
vocabulary ruling and not this ticket's to make.

THE SHORTFALL IS STATED, NOT LEFT TO BE COMPUTED. Each entry carries a `staffing` block
of the schema's own shape — the class, the model's own prose for it, one `hands` row per
role the model gives the class, `drawn` true only where a seat stands for it — and a
`shortfall` beside it saying, in numbers and in a sentence, how many hands the model
puts about this kind of house at its typical band, how many this town has seated, and
how many it is still short. A house at its band and a house at half of it now say so
themselves.

WHAT IT DOES NOT DO. It does not fill the order book's employment buckets: the book is
ordering replacements against a known-population figure T-1463 is re-cutting, and a
stage that drew against it today would draw against a number about to move. It does not
touch the attested half — T-1432's rows stay exactly where they are, and where this
overlay names a house T-1422's ruling also names, the ruling's own staff rows are
carried forward ahead of these and the compiler asserts that they were.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEATING = ROOT / "data" / "residents" / "reconstructed_seating.json"
STAFFING_MODEL = ROOT / "data" / "reconstruction" / "1835_business_staffing_model.json"
ESTABLISHMENT_STAFFING = ROOT / "data" / "businesses" / "rulings" / "establishment_staffing.json"
BUSINESS_SCHEMA = ROOT / "data" / "businesses.schema.json"
OVERLAY_OUT = ROOT / "data" / "reconstruction" / "1835_business_staff_overlay.json"

SCENE_DATE = "1835-07-01"
TICKET = "T-1462"
PARENT_TICKET = "T-1449"


class Fault(Exception):
    """A refusal, printed and exited on. Never a warning."""


# ------------------------------------------------------------------ reading --

def load() -> dict:
    for path in (SEATING, STAFFING_MODEL, BUSINESS_SCHEMA):
        if not path.exists():
            raise Fault(f"{path.relative_to(ROOT)} is missing")
    seating = json.loads(SEATING.read_text(encoding="utf-8"))
    model = json.loads(STAFFING_MODEL.read_text(encoding="utf-8"))
    schema = json.loads(BUSINESS_SCHEMA.read_text(encoding="utf-8"))
    ruling = ({} if not ESTABLISHMENT_STAFFING.exists()
              else json.loads(ESTABLISHMENT_STAFFING.read_text(encoding="utf-8")))
    return {
        "seating": seating,
        "classes": {c["class"]: c for c in model["classes"]},
        "roles": set(schema["$defs"]["role"]["enum"]),
        "tiers": set(schema["$defs"]["tier"]["enum"]),
        "ruling": {e["business_id"]: e for e in (ruling.get("entries") or [])},
    }


def seats(seating: dict) -> dict:
    """The seated rows, by business id, in the seating's own order.

    A row that seats nobody — the keeper owed premises, the soldier at a post the
    layer holds no record for — is not a seat and does not appear. Its reason is the
    seating join's to state and it states it there.
    """
    by_house: dict = {}
    for row in seating.get("rows") or []:
        if row.get("kind") != "seated":
            continue
        bid = row.get("business_id")
        if not bid:
            raise Fault(f"{row.get('person_id')} is seated and names no house — the "
                        "seating join is inconsistent with itself")
        by_house.setdefault(bid, []).append(row)
    return by_house


# ----------------------------------------------------------------- deriving --

def hand_of(spec: dict, drawn: int) -> dict:
    """One `hands` row: what the model puts about this kind of house in this role,
    and whether a seat of this pass stands for it. Names nobody, by construction —
    the compiler refuses a hand carrying a person id or a name."""
    hand = {
        "role": spec["household_relationship"],
        "occupation": spec["role"],
        "household_relationship": spec["household_relationship"],
        "count_low": spec["count_low"],
        "count_typical": spec["count_typical"],
        "count_high": spec["count_high"],
        "seats_drawn": drawn,
        "drawn": drawn > 0,
        "basis": spec.get("basis") or "the 1835 business staffing model",
    }
    if not hand["drawn"]:
        hand["why_not_drawn"] = (
            "The reconstructed seating had nobody of this trade left to seat here. A "
            "source naming a hand at this house would write one in, and T-1448's mint "
            "order is the count of what the town still owes it.")
    return hand


def shortfall_of(hands: list, rows: list) -> dict:
    """What the house still wants, in numbers and in a sentence.

    COUNTED OVER THE MODEL'S TYPICAL BAND, not its high end: the high end is what a
    house of the class COULD carry and the typical is what the model says one did, and
    a shortfall measured against the ceiling would read every ordinary house as short.
    The keeper is never counted — the model's bands exclude the principal, which is the
    shop-household rule it states for itself.
    """
    by_role: list = []
    for hand in hands:
        by_role.append({
            "occupation": hand.get("occupation"),
            "household_relationship": hand["household_relationship"],
            "count_low": hand["count_low"],
            "count_typical": hand["count_typical"],
            "count_high": hand["count_high"],
            "seats_drawn": hand.get("seats_drawn") or 0,
            "short_by": max(0, hand["count_typical"] - (hand.get("seats_drawn") or 0)),
        })
    typical = sum(r["count_typical"] for r in by_role)
    taken = sum(r["seats_drawn"] for r in by_role)
    short = sum(r["short_by"] for r in by_role)
    # THE SHORTFALL IS SUMMED PER ROLE AND NEVER OFF THE TOTALS, because a second
    # dressmaker does not stand in for the clerk this house has not got. So a house can
    # carry the model's number of hands and still be short, and `against_the_band` is
    # the figure that makes the arithmetic legible: how many of the seats it does carry
    # fall inside a role's own typical band. typical − against_the_band == short_by,
    # always, which is the identity the sentence below is written to.
    against = sum(min(r["seats_drawn"], r["count_typical"]) for r in by_role)
    if typical == 0:
        statement = (f"The staffing model puts no hand about this kind of house at its "
                     f"typical band; this house carries {taken}.")
    elif short == 0:
        statement = (f"The staffing model puts {typical} hand(s) about this kind of house "
                     f"at its typical band and this house carries {taken}. It is at its "
                     f"band.")
    elif against == taken:
        statement = (f"The staffing model puts {typical} hand(s) about this kind of house "
                     f"at its typical band and this house carries {taken}. It stands "
                     f"{short} short, and stands short rather than being quietly filled.")
    else:
        statement = (f"The staffing model puts {typical} hand(s) about this kind of house "
                     f"at its typical band. This house carries {taken}, {against} of them "
                     f"in a role that still wanted one, so it stands {short} short — short "
                     f"rather than quietly filled, and short in the roles named below "
                     f"rather than in the total.")
    return {
        "typical_wanted": typical,
        "seats_taken": taken,
        "seats_against_the_band": against,
        "short_by": short,
        "by_role": by_role,
        "statement": statement,
        "counted_here": ("the reconstructed hands this overlay seats. A hand a SOURCE "
                         "names carries its own citation in staff[] and is counted by the "
                         "attested join, not by this."),
        "replaceable_by": ("a source naming a hand at this house, which retires the seat "
                           "it replaces, or the mint T-1448 ordered, which draws the rest"),
    }


def staff_row(row: dict, relationship: str) -> dict:
    """One seat, as the seating join already states it. Nothing is added but the
    words that make it a business row rather than a resident one."""
    basis = row.get("basis") or {}
    return {
        "name": row.get("person_name"),
        "person_id": row.get("person_id"),
        "role": relationship,
        "occupation": row.get("role"),
        # NOT UPGRADED BY BEING COPIED: the seat's own tier travels with it.
        "tier": row.get("tier"),
        "basis": (f"{basis.get('note') or ''} Seated by tools/"
                  f"seat_reconstructed_trades_1835.py ({row.get('ticket')}) off "
                  f"{basis.get('id') or 'the staffing model'}; carried onto this record by "
                  f"tools/staff_the_houses_1835.py ({TICKET}).").strip(),
        "seed": row.get("seed"),
        "replaceable_by": ((row.get("replaceable_by") or {}).get("match")
                           or "a source naming who worked here"),
    }


def entry_for(bid: str, rows: list, data: dict) -> dict:
    """One house: the hands it took, and what it still wants."""
    classes = data["classes"]
    klass = rows[0].get("establishment_class")
    for row in rows:
        if row.get("establishment_class") != klass:
            raise Fault(f"{bid}: the seating gives this house two establishment classes "
                        f"({klass} and {row.get('establishment_class')})")
    spec = classes.get(klass)
    if spec is None:
        raise Fault(f"{bid}: the seating reads this house as '{klass}', which the 1835 "
                    f"business staffing model holds no class for")

    # WHICH MODEL ROW EACH SEAT STANDS FOR. The model gives a class its hands in order
    # and may give it the same trade twice — a tavern's three domestics are the cook and
    # the chambermaids, and they are three rows, not one row of three. Seats of a trade
    # therefore fill that trade's rows in the model's own order, each row up to its own
    # high end, which is the only assignment that is both deterministic and inside every
    # band the seating was already gated against.
    wanted: dict = {}
    for row in rows:
        wanted[row.get("role")] = wanted.get(row.get("role"), 0) + 1
    remaining = dict(wanted)
    hands = []
    for hand_spec in spec["staff_roles"]:
        trade = hand_spec["role"]
        take = min(remaining.get(trade, 0), hand_spec["count_high"])
        remaining[trade] = remaining.get(trade, 0) - take
        hands.append(hand_of(hand_spec, take))
    left = {t: n for t, n in remaining.items() if n > 0}
    if left:
        raise Fault(f"{bid}: the seating puts {left} in this house past every band the "
                    f"model gives a '{klass}' — a seat with no row to stand for it is a "
                    f"person invented by a pass that invents nobody")

    relationship = {}
    for hand_spec in spec["staff_roles"]:
        relationship.setdefault(hand_spec["role"], hand_spec["household_relationship"])
    staff = [staff_row(row, relationship[row.get("role")]) for row in rows]

    ruling = data["ruling"].get(bid)
    if ruling is not None:
        # THE RULING GOES FIRST AND IS NEVER DROPPED. T-1422 authored five of these
        # houses a staffing block and, where it named one, its own staff rows. This
        # overlay is laid over that one, so it carries the ruling's rows forward ahead
        # of its own and keeps the ruling's block — a derived pass may add to a
        # judgement and may not overwrite one. compile_businesses.py asserts the prefix.
        staff = [copy.deepcopy(r) for r in (ruling.get("staff") or [])] + staff
        block = copy.deepcopy(ruling.get("staffing") or {})
        drawn_roles = {r["role"] for r in staff}
        for hand in block.get("hands") or []:
            stands = (hand["role"] in drawn_roles
                      or hand["household_relationship"] in drawn_roles)
            if stands and not hand.get("drawn"):
                hand["drawn"] = True
                hand["why_not_drawn"] = None
        block["shortfall"] = shortfall_of(
            [dict(h, seats_drawn=_seats_for(h, wanted, spec)) for h in (block.get("hands") or [])],
            rows)
        return {
            "business_id": bid,
            "establishment_class": klass,
            "over_ruling": True,
            "staff": staff,
            "staffing": block,
        }

    return {
        "business_id": bid,
        "establishment_class": klass,
        "over_ruling": False,
        "staff": staff,
        "staffing": {
            "class": klass,
            "reads_as": spec["reads_as"],
            "principal_role": None,
            "principal_is": None,
            "hands": hands,
            "writes_no_person": True,
            "basis": ("the 1835 business staffing model's band for this class, with the "
                      "reconstructed seats T-1433 put in this house marked drawn"),
            "replaceable_by": ("a source naming the hands of this house, which retires "
                               "every reconstructed seat it covers"),
            "shortfall": shortfall_of(hands, rows),
        },
    }


def _seats_for(hand: dict, wanted: dict, spec: dict) -> int:
    """How many seats stand for one of the RULING's hands. The ruling writes its hands
    in its own vocabulary — T-1422's schools say `teacher` where the model says
    `schoolteacher` — so the join is made on the relationship, which both hold in
    common, and capped at the ruling's own high end."""
    total = 0
    for hand_spec in spec["staff_roles"]:
        if hand_spec["household_relationship"] == hand["household_relationship"]:
            total += wanted.get(hand_spec["role"], 0)
    return min(total, hand["count_high"])


def derive(data: dict) -> dict:
    by_house = seats(data["seating"])
    entries = [entry_for(bid, rows, data) for bid, rows in sorted(by_house.items())]
    for entry in entries:
        for row in entry["staff"]:
            if row["role"] not in data["roles"]:
                raise Fault(f"{entry['business_id']}: role '{row['role']}' is not one the "
                            f"businesses schema holds")
            if row["tier"] not in data["tiers"]:
                raise Fault(f"{entry['business_id']}: tier '{row['tier']}' is not one the "
                            f"grade ladder holds")
            if row["tier"] in ("inferred", "reconstructed") and not (row.get("basis") or "").strip():
                raise Fault(f"{entry['business_id']}: a {row['tier']} row states no basis")
            if row["tier"] == "reconstructed" and not (row.get("seed") or "").strip():
                raise Fault(f"{entry['business_id']}: a reconstructed row carries no seed — "
                            "T-1158 asks every reconstructed value for one")
        # THE SHORTFALL'S OWN ARITHMETIC, ASSERTED RATHER THAN TRUSTED. A shortfall that
        # did not close would be a number a reader could not check and would be worse
        # than none at all, since the whole point of the block is that a half-filled
        # house cannot read as a full one.
        short = entry["staffing"]["shortfall"]
        if short["typical_wanted"] - short["seats_against_the_band"] != short["short_by"]:
            raise Fault(f"{entry['business_id']}: the shortfall does not close — "
                        f"{short['typical_wanted']} wanted less "
                        f"{short['seats_against_the_band']} against the band is not "
                        f"{short['short_by']}")
    return entries


def document(data: dict, entries: list) -> dict:
    seated_rows = sum(len(rows) for rows in seats(data["seating"]).values())
    carried = sum(len(e["staff"]) for e in entries) - seated_rows
    short = sum(e["staffing"]["shortfall"]["short_by"] for e in entries)
    at_band = sum(1 for e in entries if e["staffing"]["shortfall"]["short_by"] == 0)
    return {
        "$schema_note": ("DERIVED — regenerate with tools/staff_the_houses_1835.py --build; "
                         "tools/check.sh re-derives it. Do not hand-edit."),
        "id": "1835_business_staff_overlay",
        "ticket": TICKET,
        "parent_ticket": PARENT_TICKET,
        "target_date": SCENE_DATE,
        "generated_by": "tools/staff_the_houses_1835.py --build",
        "read_by": "tools/compile_businesses.py",
        "not_a_reading": ("an overlay over committed files — no page of any source is read "
                          "here, no person is written, no business is raised and no seat is "
                          "invented. Every row restates one the reconstructed seating "
                          "already holds."),
        "mints_nobody": True,
        "writes_no_person": True,
        "what_it_writes": ("staff[] rows on the compiled business records the T-1433 seating "
                           "seats a hand in, and a staffing block beside them stating that "
                           "house's shortfall against the 1835 business staffing model"),
        "inputs": [
            "data/residents/reconstructed_seating.json",
            "data/reconstruction/1835_business_staffing_model.json",
            "data/businesses/rulings/establishment_staffing.json",
        ],
        "counts": {
            "houses_taking_a_reconstructed_hand": len(entries),
            "reconstructed_staff_rows_written": seated_rows,
            "ruling_rows_carried_forward": carried,
            "houses_over_a_t1422_ruling": sum(1 for e in entries if e["over_ruling"]),
            "houses_at_their_typical_band": at_band,
            "houses_still_short": len(entries) - at_band,
            "hands_still_wanted_at_the_typical_band": short,
        },
        "what_this_does_not_do": {
            "it_mints_nobody": ("the shortfall above is stated and not filled; T-1448's "
                                "order is the count of what a mint would be allowed to draw"),
            "it_fills_no_bucket": ("the reconstruction order book's employment buckets stay "
                                   "exactly where the stages that earned them left them. The "
                                   "book is ordering against a known-population figure "
                                   "T-1463 is re-cutting, and a stage drawing against it "
                                   "today would draw against a number about to move."),
            "it_touches_no_attested_row": ("T-1432's join is untouched, and where T-1422's "
                                           "ruling names a house this overlay also names, "
                                           "the ruling's rows are carried forward ahead of "
                                           "these and the compiler asserts it"),
        },
        "entries": entries,
    }


# ------------------------------------------------------------------ commands --

def cmd_build() -> int:
    data = load()
    doc = document(data, derive(data))
    OVERLAY_OUT.parent.mkdir(parents=True, exist_ok=True)
    OVERLAY_OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    c = doc["counts"]
    print(f"OK: the business side of the staffing join — {c['reconstructed_staff_rows_written']} "
          f"reconstructed hands written onto {c['houses_taking_a_reconstructed_hand']} houses, "
          f"{c['houses_still_short']} of them still short of their band by "
          f"{c['hands_still_wanted_at_the_typical_band']} hand(s), nobody minted")
    return 0


def cmd_check() -> int:
    if not OVERLAY_OUT.exists():
        raise Fault(f"{OVERLAY_OUT.relative_to(ROOT)} has never been built")
    data = load()
    doc = document(data, derive(data))
    on_disk = json.loads(OVERLAY_OUT.read_text(encoding="utf-8"))
    if json.dumps(doc, sort_keys=True) != json.dumps(on_disk, sort_keys=True):
        raise Fault(f"{OVERLAY_OUT.relative_to(ROOT)} no longer re-derives from its inputs — "
                    "run tools/staff_the_houses_1835.py --build")
    c = doc["counts"]
    print(f"OK: the business side of the staffing join re-derives — "
          f"{c['reconstructed_staff_rows_written']} hands on "
          f"{c['houses_taking_a_reconstructed_hand']} houses, "
          f"{c['houses_still_short']} still short by "
          f"{c['hands_still_wanted_at_the_typical_band']}")
    return 0


def cmd_self_test() -> int:
    fired = 0

    def fires(what, fn):
        nonlocal fired
        try:
            fn()
        except Fault:
            fired += 1
            return
        raise SystemExit(f"FAIL: the guard against {what} did not fire")

    data = load()
    derive(data)  # the real data passes, or nothing below means anything

    def seated_house(copy_of):
        for bid, rows in sorted(seats(copy_of["seating"]).items()):
            if not copy_of["ruling"].get(bid):
                return bid, rows
        raise SystemExit("FAIL: the seating seats nobody outside T-1422's ruling")

    # ONE: a seat past every band the model gives the class is a person invented here.
    over = copy.deepcopy(data)
    bid, rows = seated_house(over)
    twin = copy.deepcopy(rows[0])
    twin["person_id"] = twin["person_id"] + "_twin"
    for _ in range(9):
        over["seating"]["rows"].append(copy.deepcopy(twin))
    fires("a house staffed past the model's own high end", lambda: derive(over))

    # TWO: a class the staffing model does not hold cannot be staffed off it.
    unknown = copy.deepcopy(data)
    for row in unknown["seating"]["rows"]:
        if row.get("kind") == "seated":
            row["establishment_class"] = "a_class_the_model_never_heard_of"
            break
    fires("a house read as a class the model holds no band for", lambda: derive(unknown))

    # THREE: two classes for one house is the seating disagreeing with itself.
    split = copy.deepcopy(data)
    bid, rows = seated_house(split)
    target = [r for r in split["seating"]["rows"]
              if r.get("kind") == "seated" and r.get("business_id") == bid]
    if len(target) < 2:
        extra = copy.deepcopy(target[0])
        extra["person_id"] = extra["person_id"] + "_second"
        split["seating"]["rows"].append(extra)
        target.append(extra)
    target[-1]["establishment_class"] = "tavern_or_hotel" if target[0][
        "establishment_class"] != "tavern_or_hotel" else "bakery"
    fires("one house read as two classes", lambda: derive(split))

    # FOUR: a seat with no seed is a reconstructed value T-1158 cannot unpick.
    seedless = copy.deepcopy(data)
    for row in seedless["seating"]["rows"]:
        if row.get("kind") == "seated":
            row["seed"] = ""
            break
    fires("a reconstructed seat carrying no seed", lambda: derive(seedless))

    # FIVE: a seated row naming no house.
    homeless = copy.deepcopy(data)
    for row in homeless["seating"]["rows"]:
        if row.get("kind") == "seated":
            row["business_id"] = None
            break
    fires("a seated row naming no house", lambda: derive(homeless))

    # SIX: the shortfall is measured against the typical band, and it says so. A house
    # at its band and a house at half of it must not print the same sentence.
    entries = derive(data)
    at_band = [e for e in entries if e["staffing"]["shortfall"]["short_by"] == 0]
    short = [e for e in entries if e["staffing"]["shortfall"]["short_by"] > 0]
    if not at_band or not short:
        raise SystemExit("FAIL: the overlay cannot tell a full house from a half-filled one")
    if at_band[0]["staffing"]["shortfall"]["statement"] == short[0]["staffing"]["shortfall"]["statement"]:
        raise SystemExit("FAIL: a house at its band and a house short of it print the "
                         "same sentence")
    fired += 1

    # SEVEN: the shortfall closes on every house, and a house is refused if it does not.
    broken = copy.deepcopy(entries[0])
    broken["staffing"]["shortfall"]["short_by"] += 1

    def refuse_broken():
        short = broken["staffing"]["shortfall"]
        if short["typical_wanted"] - short["seats_against_the_band"] != short["short_by"]:
            raise Fault("the shortfall does not close")

    fires("a shortfall whose arithmetic does not close", refuse_broken)

    doc = document(data, entries)
    c = doc["counts"]
    print(f"staff_the_houses_1835 self-tests pass ({fired} guards fired, "
          f"{c['reconstructed_staff_rows_written']} hands on "
          f"{c['houses_taking_a_reconstructed_hand']} houses, "
          f"{c['houses_still_short']} still short, nobody minted)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    try:
        if args.build:
            return cmd_build()
        if args.check:
            return cmd_check()
        if args.self_test:
            return cmd_self_test()
    except Fault as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
