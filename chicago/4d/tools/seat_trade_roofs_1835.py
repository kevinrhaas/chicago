#!/usr/bin/env python3
"""THE EMPTY TRADE ROOFS, OFFERED TO THE KEEPERS WHO HAVE NO HOUSE. T-1989.

Piece 2 of T-1986 (the anonymous programme roofs left empty), under T-1966 (place the work).

    tools/seat_trade_roofs_1835.py --build      write the deal
    tools/seat_trade_roofs_1835.py --check      re-derive it, refuse drift
    tools/seat_trade_roofs_1835.py --report     each roof, who took it or why nobody could
    tools/seat_trade_roofs_1835.py --self-test  the guards, fired on the real data

## WHAT WAS LEFT

Four anonymous roofs of a TRADE family stood with nobody under them after every other
programme had passed: a joiner's shop on Randolph at Des Plaines (W2), a narrow warehouse at
the forks (F2), a large riverside work shop on Wolcott (W5) and a narrow two-storey store on
Lake (C3). The roof redeal (T-1445) kept all four — "the order book has an occupant class for
a roof of this family in this division and the placement policy accepts the family where it
stands" — so a stated use (`1835_stated_uses.json`, L310) would break that file's rule (b):
it would lose somebody a roof. The housing deal (T-1971, L354) refuses stores, workshops and
warehouses by design, because they are where people WORK.

And the people who should work in them were already in the town. The employment ledger
(`data/residents/employment_coverage.json`, T-1461) owes 170 reconstructed keepers a house
of their own (`keeps_their_own_house`): the premises ruling gives their trade a shop, a store
or a counting-room of its own, and nobody has said where it stands. Each of them sleeps
somewhere — the housing deal put them under a dwelling — and works nowhere.

## THE DEAL

Each roof in `SCOPE` is offered to the keepers that the employment ledger owes a house of
their own and whose card names no workplace (`works_at`), in the roof's own division, whose
trade the roof's family serves:

  * W2 "Carpenter or joiner shop" — the crosswalk's own label names the two trades.
  * F2 "Narrow two-story warehouse" — the premises ruling's `forwarding_and_commission_store`.
  * C3 "Narrow two-story store" — the premises rulings' `store` and
    `grocery_and_provision_store` signage.
  * W5 "Sawmill, boat-repair, or riverside shop" — the placement policy admits it only under
    `heavy_and_noxious_trades` ("packing, tanning, slaughtering and soap-boiling"), so the
    premises rulings' tannery, packing-house, slaughterhouse and soap-and-candle signage.

Every term is read out of a committed file (`MATCH` says which); none is typed from memory.
The roof goes to the keeper whose own roof — the card's `lives_at`, else the housing deal's
seat — stands nearest it, ties broken by a seeded hash. One keeper a roof, one roof a
keeper. **No source places any of these people at any of these roofs**: the keeper is the
residents layer's, with their own grade on their own card; the roof is the 668-roof
programme's; what is invented is which of them meet, and it is docs/LIBERTIES.md **L356**.

The seat travels beside the card, as the housing deal's do: `tools/compile_scene.py`
(`overlay_trade_roofs`) puts the keeper on the roof's card as "worked here". No card and no
structure record is written, so every stage that re-derives a card byte for byte still does.

## A ROOF NOBODY CAN TAKE SAYS SO

Where no keeper qualifies the roof is written to `unseatable` with the count that proves it
and the reason in words, and the building card says why nobody is seated there (`stated_use`,
the surface T-1985 built). That is a measurement of who the town holds, not a stated use: the
roof's verdict stays `keep`, and the first keeper of its trade the layer gains takes it on
the next build with no edit here.

## WHAT THIS DOES NOT DO

It does not move the employment ledger. The keepers seated here still read
`keeps_their_own_house` in `employment_coverage.json` until T-1982 joins this deal into it,
so the audit's at-work count does not fall here; its occupied count does.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
YEAR = "1835"
OUT = DATA / "reconstruction" / "1835_trade_roof_seats.json"
TICKET = "T-1989"
LIBERTY = "L356"

sys.path.insert(0, str(ROOT / "tools"))
from compile_scene import compile_residents  # noqa: E402

# The roofs this ticket owns: the four trade roofs the audit left empty after T-1985 and
# T-1988, every one a `keep` in the roof redeal. A roof added here is a ticket's decision.
SCOPE = (
    "recon_1835_blk_west_randolph_des_plaines_w2_01",
    "recon_1835_forks_freight_f2_001",
    "recon_1835_north_w5_040",
    "recon_1835_south_c3_015",
)

# Which keepers a family serves, and the committed line each term is read from.
MATCH = {
    "W2": {"occupations": ["carpenter", "joiner"],
           "read_from": "data/reconstruction/1835_family_archetype_crosswalk.json W2 label "
                        "'Carpenter or joiner shop'"},
    "F2": {"signage": ["forwarding_and_commission_store"],
           "read_from": "data/businesses/rulings/premises_rulings.json signage_function of "
                        "forwarding_and_commission — a counting-room with a warehouse behind it"},
    "C3": {"signage": ["store", "grocery_and_provision_store"],
           "read_from": "data/businesses/rulings/premises_rulings.json signage_function "
                        "'store' and 'grocery_and_provision_store'"},
    "W5": {"signage": ["tannery", "packing_house", "slaughterhouse_packing",
                       "soap_candle_manufactory"],
           "read_from": "data/reconstruction/1835_placement_policy.json clause "
                        "heavy_and_noxious_trades (the only clause admitting W5) and the "
                        "premises rulings' signage for the four trades it names"},
}
OWED_REASON = "keeps_their_own_house"
RESIDENT_FOLDERS = ("households", "reconstructed_trades", "lodgers", "underdocumented",
                    "readmitted", "institutional")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def value_of(field):
    return field.get("value") if isinstance(field, dict) else field


def seed(*parts) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def read_inputs() -> dict:
    index = load(DATA / "sidecars" / YEAR / "index.json")
    roofs, standing = {}, set()
    for row in index["structures"]:
        standing.add(row["id"])
        path = DATA / "structures" / f"{row['id']}.json"
        if not path.exists():
            continue
        record = load(path)
        position = (record.get("phases") or [{}])[0].get("position") or {}
        sidecar = load(DATA / row["sidecar"])
        roofs[row["id"]] = {
            "family": (record.get("reconstruction") or {}).get("family"),
            "district": (record.get("reconstruction") or {}).get("district"),
            "anonymous": bool(record.get("reconstruction")),
            "function": value_of(record.get("function")),
            "at": (position.get("utm_e"), position.get("utm_n")),
            "occupants": value_of((sidecar.get("attributes") or {}).get("occupants")),
        }

    cards = {}
    for folder in RESIDENT_FOLDERS:
        for path in sorted((DATA / "residents" / folder).glob("*.json")):
            card = load(path)
            if isinstance(card, dict) and card.get("id"):
                cards[card["id"]] = {"file": f"{folder}/{path.name}", "card": card}

    premises = {r["occupation"]: r for r in
                load(DATA / "businesses" / "rulings" / "premises_rulings.json")["rulings"]}
    housing = load(DATA / "reconstruction" / "1835_housing_seats.json")
    business_at = set()
    for path in sorted((DATA / "businesses").glob("*.json")) + \
            sorted((DATA / "businesses" / "authored").glob("*.json")):
        b = load(path)
        if isinstance(b, dict):
            business_at |= {l.get("structure_id") for l in b.get("locations") or []}
    # Who already works or sleeps under each roof, from every overlay but the housing deal
    # and this one — `housing=False` is how this pass reads the town without reading itself.
    seated_at = {sid: [h["household"] for h in rows]
                 for sid, rows in compile_residents(housing=False).items()}
    off_plat = {s["structure_id"]: s for s in
                load(DATA / "reconstruction" / "1835_off_plat_seats.json").get("seats") or []
                if s.get("structure_id")}
    return {
        "roofs": roofs, "standing": standing, "cards": cards, "premises": premises,
        "housing": {s["household"]: s["place"] for s in housing.get("seats") or []},
        "business_at": business_at, "seated_at": seated_at, "off_plat": off_plat,
        "employment": load(DATA / "residents" / "employment_coverage.json")["rows"],
    }


def serves(family: str, trade: str | None, premises: dict) -> bool:
    rule = MATCH.get(family) or {}
    if trade in rule.get("occupations", ()):
        return True
    return (premises.get(trade) or {}).get("signage_function") in rule.get("signage", ())


def home_of(hid: str, inputs: dict) -> str | None:
    card = (inputs["cards"].get(hid) or {}).get("card") or {}
    where = value_of(card.get("lives_at"))
    return where if where in inputs["roofs"] else inputs["housing"].get(hid)


def metres(a: tuple, b: tuple) -> float | None:
    if None in a or None in b:
        return None
    return round(math.dist(a, b), 1)


def keepers(inputs: dict) -> list[dict]:
    """Every person the employment ledger owes a house of their own and no card roofs."""
    out = []
    for row in inputs["employment"]:
        if row.get("reason") != OWED_REASON or row.get("houses"):
            continue
        entry = inputs["cards"].get(row["household_id"])
        if not entry or value_of(entry["card"].get("works_at")):
            continue
        person = next((p for p in entry["card"].get("persons") or []
                       if p.get("id") == row["person_id"]), {})
        out.append({"person_id": row["person_id"], "name": person.get("name", ""),
                    "household": row["household_id"], "file": entry["file"],
                    "division": entry["card"].get("division"), "trade": row.get("trade"),
                    "grade": person.get("grade", "reconstructed")})
    return out


def deal(inputs: dict) -> dict:
    roofs, pool = inputs["roofs"], keepers(inputs)
    taken, seats, unseatable = set(), [], []
    for sid in SCOPE:
        roof = roofs[sid]
        family, division = roof["family"], roof["district"]
        candidates = [k for k in pool if k["division"] == division
                      and serves(family, k["trade"], inputs["premises"])]
        free = [k for k in candidates if k["person_id"] not in taken]

        def reach(k):
            home = home_of(k["household"], inputs)
            d = metres(roof["at"], roofs[home]["at"]) if home in roofs else None
            return (d if d is not None else math.inf, seed(k["person_id"], sid, TICKET))

        if free:
            k = min(free, key=reach)
            taken.add(k["person_id"])
            home = home_of(k["household"], inputs)
            d = reach(k)[0]
            seats.append({
                "structure_id": sid, "family": family, "division": division,
                "person_id": k["person_id"], "name": k["name"], "household": k["household"],
                "file": k["file"], "trade": k["trade"], "grade": k["grade"],
                "home": home, "metres_from_home": None if d == math.inf else d,
                "keepers_offered": len(candidates), "relation": "worked here",
                "words": (f"keeping a {k['trade'].replace('_', ' ')}'s house of their own: the "
                          f"nearest of {len(candidates)} {division} division keeper(s) of a trade "
                          f"this roof serves, who had no workplace"
                          + (f", {round(d)} m from their own roof" if d != math.inf else "")),
            })
            continue
        adoption = inputs["off_plat"].get(sid)
        note = (f"NO KEEPER OF ITS TRADE IS LEFT IN THE {division.upper()} DIVISION. This "
                f"{(roof['function'] or 'roof').replace('_', ' ')} is offered to every keeper the "
                f"employment ledger owes a house of their own whose card names no workplace, in "
                f"its own division, of a trade its family serves ({MATCH[family]['read_from']}), "
                f"and there are {len(candidates)}.")
        if adoption:
            entry = inputs["cards"].get(adoption["id"]) or {}
            works = value_of((entry.get("card") or {}).get("works_at"))
            d = metres(roof["at"], roofs[works]["at"]) if works in roofs else None
            note += (f" The off-plat deal (T-1614) adopted it for {adoption.get('name')}, but "
                     f"that household's own card puts its works at {works}"
                     + (f", {round(d)} m away" if d is not None else "")
                     + ", so seating it here would give one firm a second works nobody records.")
        note += (" So nobody is seated here and nobody is invented to be: the first keeper of "
                 "its trade the town gains takes it on the next build.")
        unseatable.append({"structure_id": sid, "family": family, "division": division,
                           "keepers_offered": len(candidates),
                           "adopted_by": (adoption or {}).get("id"),
                           "value": "no_keeper_of_its_trade", "note": note})
    return {
        "$schema_note": ("DERIVED — regenerate with tools/seat_trade_roofs_1835.py --build; "
                         "tools/check.sh re-derives it. Do not hand-edit."),
        "id": "chicago_july_1835_trade_roof_seats",
        "ticket": TICKET, "parent_ticket": "T-1986", "target_date": "1835-07-01",
        "generated_by": "tools/seat_trade_roofs_1835.py", "liberty": LIBERTY,
        "not_a_reading": ("no page of any source is read here. Every seat is an adjudication "
                          "over committed records — which keeper owed a house of their own "
                          "keeps it under which standing trade roof — and the meeting is the "
                          "invention. The keeper's card is not touched."),
        "raises_no_roof": "every seat is a keeper put under a roof that already stands.",
        "inputs": ["data/residents/employment_coverage.json",
                   "data/residents/{households,reconstructed_trades,lodgers,underdocumented,"
                   "readmitted,institutional}/*.json",
                   "data/businesses/rulings/premises_rulings.json",
                   "data/reconstruction/1835_housing_seats.json",
                   "data/reconstruction/1835_off_plat_seats.json",
                   "data/structures/*.json", "data/sidecars/1835/index.json"],
        "match": MATCH,
        "counts": {"roofs": len(SCOPE), "seated": len(seats), "unseatable": len(unseatable),
                   "keepers_owed_a_house": len(pool)},
        "seats": seats,
        "unseatable": unseatable,
    }


def render(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def problems(doc: dict, inputs: dict) -> list[str]:
    out, roofs = [], inputs["roofs"]
    pool = {k["person_id"]: k for k in keepers(inputs)}
    answered = [r["structure_id"] for r in doc["seats"] + doc["unseatable"]]
    for sid in SCOPE:
        if answered.count(sid) != 1:
            out.append(f"{sid} is answered {answered.count(sid)} times, not once")
    for sid in answered:
        roof = roofs.get(sid)
        if sid not in SCOPE:
            out.append(f"{sid} is not a roof this deal owns")
        elif sid not in inputs["standing"] or not roof or not roof["anonymous"]:
            out.append(f"{sid} is not a standing anonymous roof")
        elif roof["occupants"] or inputs["seated_at"].get(sid) or sid in inputs["business_at"]:
            out.append(f"{sid} is already occupied by another programme")
    people = [s["person_id"] for s in doc["seats"]]
    for s in doc["seats"]:
        k = pool.get(s["person_id"])
        if people.count(s["person_id"]) > 1:
            out.append(f"{s['person_id']} keeps two roofs")
        if not k:
            out.append(f"{s['person_id']} is seated and the ledger owes them no house")
        elif k["division"] != roofs[s["structure_id"]]["district"]:
            out.append(f"{s['person_id']} is seated outside their own division")
        elif not serves(roofs[s["structure_id"]]["family"], k["trade"], inputs["premises"]):
            out.append(f"{s['person_id']} ({k['trade']}) is seated in a roof their trade "
                       "does not keep")
    for u in doc["unseatable"]:
        if u["keepers_offered"]:
            out.append(f"{u['structure_id']} is called unseatable with "
                       f"{u['keepers_offered']} keeper(s) to offer it to")
        if not u.get("note") or not u.get("value"):
            out.append(f"{u['structure_id']} is unseatable and says no reason")
    return out


def report(doc: dict) -> str:
    lines = [f"trade roofs (T-1989): {doc['counts']['seated']} seated, "
             f"{doc['counts']['unseatable']} with no keeper to offer, of "
             f"{doc['counts']['roofs']}; {doc['counts']['keepers_owed_a_house']} keepers owed "
             "a house of their own"]
    for s in doc["seats"]:
        lines.append(f"  {s['structure_id']}  {s['family']}  {s['name']} ({s['trade']}), "
                     f"nearest of {s['keepers_offered']}")
    for u in doc["unseatable"]:
        lines.append(f"  {u['structure_id']}  {u['family']}  nobody: "
                     f"{u['keepers_offered']} keepers of its trade in the {u['division']}")
    return "\n".join(lines)


def self_test(inputs: dict) -> int:
    failures = []
    base = deal(inputs)
    if problems(base, inputs):
        failures.append("the committed deal is not clean to begin with")

    def expect(label, mutate):
        doc = copy.deepcopy(base)
        mutate(doc)
        if not problems(doc, inputs):
            failures.append(label)

    other = next(k for k in keepers(inputs) if k["trade"] == "milliner")
    expect("a roof outside the deal's scope",
           lambda d: d["seats"][0].update(structure_id="recon_1835_west_001"))
    expect("a roof left unanswered", lambda d: d["seats"].pop())
    expect("a keeper given two roofs", lambda d: d["seats"][1].update(
        person_id=d["seats"][0]["person_id"]))
    expect("a keeper of a trade the roof does not serve",
           lambda d: d["seats"][0].update(person_id=other["person_id"]))
    expect("a person the ledger owes no house",
           lambda d: d["seats"][0].update(person_id="nobody_at_all"))
    expect("a roof called unseatable while keepers wait",
           lambda d: d["unseatable"][0].update(keepers_offered=3))
    expect("an unseatable roof that gives no reason",
           lambda d: d["unseatable"][0].update(note=""))
    if failures:
        print("SELF-TEST FAILED — the guard did not fire on: " + "; ".join(failures))
        return 1
    print("self-test: all seven guards fire")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    inputs = read_inputs()
    if args.self_test:
        return self_test(inputs)
    doc = deal(inputs)
    errors = problems(doc, inputs)
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != render(doc):
            errors.append(f"{OUT.relative_to(ROOT)} is stale — run "
                          "tools/seat_trade_roofs_1835.py --build")
        print(report(doc))
        if errors:
            print("TRADE ROOF DEAL FAILED\n  - " + "\n  - ".join(errors))
            return 1
        return 0
    if args.build:
        OUT.write_text(render(doc), encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)}")
    print(report(doc))
    if errors:
        print("not clean:\n  - " + "\n  - ".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
