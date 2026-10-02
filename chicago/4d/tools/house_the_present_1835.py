#!/usr/bin/env python3
"""HOUSE THE PRESENT: every household present on 1 July 1835 under a roof that stands.

T-1971, piece 1 of 2 of T-1965 (itself piece 2 of 7 of T-1215, the closeout of the whole
reconstruction). The owner's stop condition is *"every person in Chicago has a place to
live"*, and on the day this was written the town's own join said otherwise: of the
households the residents layer holds PRESENT on the scene date, 1,003 reached no roof, no
vessel and no camp — neither through their own `lives_at` nor through a sidecar seating
them. Meanwhile 223 dwellings of the reconstruction's own programme stood with nobody in
them at all. The people and the roofs were both committed; the join between them was not.

    tools/house_the_present_1835.py              write data/reconstruction/1835_housing_seats.json
    tools/house_the_present_1835.py --check      re-derive it and refuse drift, a seat on a roof
                                                 the scene does not stand, a household seated
                                                 twice, a present household left unhoused, or a
                                                 town above the census's people per dwelling
    tools/house_the_present_1835.py --report     the deal by rung, division and roof family
    tools/house_the_present_1835.py --self-test  break each guard in memory and prove it fires

## WHAT THIS WRITES, AND WHAT IT DOES NOT

One ledger, one seat per household. `tools/compile_scene.py` (`overlay_housing`) puts each
seat on the building card of the roof it names, beside the people `compile_residents` and
`overlay_lodgers` already put there, which is how the lodgers' seats already travel. **No
card is touched**: every folder of `data/residents/` is re-derived whole by its own stage
and two of those stages refuse a roof outright, so a `lives_at` written here would be
overwritten on the next rebuild — the seat lives beside the card, as T-1406's do. No roof
is raised and no record is edited; nobody is minted, and nobody is moved out of the
division their own card or the address book puts them in.

## THE DEAL, IN THE ORDER IT IS TAKEN

  1. **Dealt.** A household the platted or off-plat seating (T-1613, T-1614) already put
     under a standing roof — the address book's `dealt_roof` — takes that roof. That deal
     was argued once and is not re-argued here; this pass only joins it.
  2. **Families** (two or more people on the card), largest first, take a dwelling of the
     family their placement-policy clause admits (`applies_to`), in their own division. A
     household the address book never banded (the reconstructed trades, the readmitted
     and the underdocumented, who stand beside `households/`) takes any dwelling of its
     division — the band it would need is one nobody dealt, and this pass does not invent
     one. Where no roof of the clause stands in the division, the division's dwellings.
  3. **Single people** take a free ordinary-night bed in a lodging house of their division
     first (the lodging model's own count, never its crowded one), and board in the
     division's dwellings when the beds are gone.

Among the roofs a household may take, it takes the one that leaves the fewest people per
square metre of floor (footprint × storeys), ties broken by a seeded hash. That is the whole
of the placement: **the room is where the people go.** A household whose division is
`unplaced` is offered the whole town and lands where the room is.

## WHICH ROOFS, AND THE REFUSALS

A standing roof of the reconstruction layer whose family is a dwelling (D1–D7, H1–H3,
T1–T3). Refused, on T-1613's own rules:

  * every DOCUMENTED building — a policy deal that put an invented boarder under a
    researched house would read back as a fact about that house;
  * a roof whose sidecar already STATES its occupants ("Anonymous stock; no occupant is
    claimed", a named practice, a named shop) — a deal does not overturn a committed claim;
  * stores, workshops, warehouses, outbuildings and civic works (C, W, F, A, I, M).

## THE CEILING

The census of November 1835 counted 3,265 people in 398 dwellings — 8.204 a roof
(`data/reconstruction/1835_town_model.json`). `--check` refuses a deal whose present,
housed people per inhabited roof exceeds that, so the town this draws is never more crowded
than the town the enumerator walked four months later. The most crowded roof is printed
beside it, not hidden in the mean.

The invention is docs/LIBERTIES.md **L354**.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
YEAR = "1835"
OUT = DATA / "reconstruction" / "1835_housing_seats.json"
TICKET = "T-1971"
LIBERTY = "L354"

sys.path.insert(0, str(ROOT / "tools"))
from compile_scene import compile_residents  # noqa: E402

# The residents layer's folders of people OF the town; `transients` kept no residence by
# construction (T-1353) and `merged` cards were folded into another.
RESIDENT_FOLDERS = ("households", "reconstructed_trades", "lodgers", "underdocumented",
                    "readmitted", "institutional")
DIVISIONS = ("north", "south", "west")

DWELLING_FAMILIES = {"D1", "D2", "D3", "D4", "D5", "D6", "D7", "H1", "H2", "H3", "T1", "T2", "T3"}
LODGING_FAMILIES = {"H3", "T1", "T2", "T3"}
# A documented building counts as a DWELLING for the census's ratio by its own function.
# It is never offered to the deal (a researched house is not re-tenanted by a policy), but
# the enumerator counted it, so the ceiling does too.
DOCUMENTED_DWELLINGS = {
    "agency_house_residence", "boarding_house", "commanding_officers_quarters", "dwelling",
    "dwelling_and_store", "dwelling_and_trading_house", "dwelling_farmstead",
    "dwelling_former_school_use_unattested", "dwelling_to_let", "enlisted_mens_barracks",
    "hotel", "log_cabin_former_store_and_school_use_unattested",
    "log_house_former_school_use_unattested", "office_and_lodging", "officers_quarters",
    "residence", "store_and_dwelling", "store_residence", "tavern_inn",
}

# The census of November 1835 (town model, `people_per_dwelling_november_1835`).
CENSUS_PEOPLE_PER_DWELLING = 8.204

RELATION = {
    "dealt": "lived here",
    "family": "shared this roof",
    "boarder": "boarded here",
    "lodger": "lodged here",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def value_of(field):
    return field.get("value") if isinstance(field, dict) else field


def floor_area(polygon, stories) -> float:
    pts = polygon or []
    twice = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return round(abs(twice) / 2 * max(1.0, float(stories or 1)), 2)


def seed(*parts) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()


def read_inputs() -> dict:
    index = load(DATA / "sidecars" / YEAR / "index.json")
    roofs, standing = {}, set()
    for row in index["structures"]:
        standing.add(row["id"])
        record_path = DATA / "structures" / f"{row['id']}.json"
        record = load(record_path) if record_path.exists() else {}
        recon = record.get("reconstruction") or {}
        sidecar = load(DATA / row["sidecar"])
        attributes = sidecar.get("attributes") or {}
        roofs[row["id"]] = {
            "family": recon.get("family"),
            "district": recon.get("district"),
            "documented": not recon,
            "occupants": value_of(attributes.get("occupants")),
            "area": floor_area((sidecar.get("footprint") or {}).get("polygon"),
                               value_of(attributes.get("stories"))),
            "beds": (recon.get("capacity") or {}).get("beds_ordinary"),
            "function": value_of(record.get("function")),
            "assigned_to": (record.get("resident_assignment") or {}).get("household_id"),
        }

    cards = {}
    for folder in RESIDENT_FOLDERS:
        for path in sorted((DATA / "residents" / folder).glob("*.json")):
            card = load(path)
            if isinstance(card, dict) and card.get("id"):
                cards[card["id"]] = {"file": f"{folder}/{path.name}", "card": card}

    book = {r["id"]: r for r in load(DATA / "reconstruction" / "1835_address_book.json")["rows"]}
    policy = load(DATA / "reconstruction" / "1835_placement_policy.json")
    clauses = {c["id"]: set(c.get("applies_to") or []) for c in policy["clauses"]}
    boats = load(DATA / "boats" / "index.json").get("boats") or []

    # Who is ALREADY under a roof, read the way the building card is built — without
    # this pass's own overlay, so the ledger never reads itself.
    seated = {h["household"] for rows in compile_residents(housing=False).values() for h in rows}

    return {"roofs": roofs, "standing": standing, "cards": cards, "book": book,
            "clauses": clauses, "vessels": {b["id"] for b in boats if b.get("id")},
            "seated": seated}


def division_of(card: dict, row: dict | None) -> str | None:
    if row and (row.get("seat") or {}).get("division") in DIVISIONS:
        return row["seat"]["division"]
    for key in ("division", "division_reconstructed"):
        value = value_of(card.get(key))
        if value in DIVISIONS:
            return value
    return None


def deal(inputs: dict) -> dict:
    roofs, cards, book = inputs["roofs"], inputs["cards"], inputs["book"]
    standing, vessels, seated = inputs["standing"], inputs["vessels"], inputs["seated"]

    pool = {sid: r for sid, r in roofs.items()
            if r["family"] in DWELLING_FAMILIES and not r["documented"]
            and r["occupants"] in (None, "") and r["area"] > 0}

    # People already sleeping under each roof, from every overlay but this one. A row
    # that only WORKED there is somebody else's bed and is not counted.
    people = Counter()
    for sid, rows in compile_residents(housing=False).items():
        people[sid] += sum(len(h.get("persons") or []) for h in rows
                           if h.get("relation") != "worked here")
    lodging_beds = {sid: max(0, (r["beds"] or 0) - people[sid]) for sid, r in pool.items()
                    if r["family"] in LODGING_FAMILIES and r["beds"]}

    owed, already = [], 0
    for hid, entry in sorted(cards.items()):
        card = entry["card"]
        if value_of(card.get("present_on_scene_date")) != "present":
            continue
        where = value_of(card.get("lives_at"))
        if (where and (where in standing or where in vessels)) or hid in seated:
            already += 1
            continue
        owed.append(hid)

    seats, refused = [], []

    def place(hid, sid, rung, words):
        entry = cards[hid]
        n = len(entry["card"].get("persons") or [])
        people[sid] += n
        seats.append({"household": hid, "file": entry["file"], "place": sid,
                      "rung": rung, "relation": RELATION[rung], "persons": n,
                      "division": roofs[sid]["district"], "family": roofs[sid]["family"],
                      "words": words})

    def best(hid, candidates):
        return min(candidates, key=lambda sid: (
            round((people[sid] + len(cards[hid]["card"].get("persons") or [])) / pool[sid]["area"], 6),
            seed(hid, sid, TICKET)))

    # 1. dealt — the platted and off-plat seating already chose the roof.
    rest = []
    for hid in owed:
        dealt = (book.get(hid) or {}).get("dealt_roof") or {}
        sid = dealt.get("structure_id") if isinstance(dealt, dict) else None
        if sid in pool or (sid in roofs and roofs[sid]["assigned_to"] == hid):
            place(hid, sid, "dealt", f"the roof {dealt.get('dealt_by') or 'the seating'} dealt this "
                                     "household, joined here and not re-argued")
        else:
            rest.append(hid)

    def size(hid):
        return len(cards[hid]["card"].get("persons") or [])

    families = sorted((h for h in rest if size(h) >= 2), key=lambda h: (-size(h), seed(h, TICKET)))
    singles = sorted((h for h in rest if size(h) < 2), key=lambda h: seed(h, TICKET))

    def in_division(hid, families_ok):
        division = division_of(cards[hid]["card"], book.get(hid))
        return division, [sid for sid, r in pool.items()
                          if (division is None or r["district"] == division)
                          and r["family"] in families_ok]

    homes = DWELLING_FAMILIES - LODGING_FAMILIES
    # 2. families, by their clause's own families, else the division's dwellings.
    for hid in families:
        row = book.get(hid)
        clause = ((row or {}).get("seat") or {}).get("clause")
        admitted = inputs["clauses"].get(clause, set()) & homes
        division, roofs_ok = in_division(hid, admitted) if admitted else (None, [])
        how = f"a {'/'.join(sorted(admitted))} dwelling, as the {clause} clause admits"
        if not roofs_ok:
            division, roofs_ok = in_division(hid, homes)
            how = "a dwelling of its division" if division else "the town's least crowded dwelling"
        if not roofs_ok:
            refused.append({"household": hid, "why": "no dwelling of its division stands"})
            continue
        place(hid, best(hid, roofs_ok), "family", how)

    # 3. single people: a free ordinary bed in their division, then boarding.
    for hid in singles:
        division = division_of(cards[hid]["card"], book.get(hid))
        beds = [sid for sid, free in lodging_beds.items()
                if free > 0 and (division is None or pool[sid]["district"] == division)]
        if beds:
            sid = min(beds, key=lambda s: (-lodging_beds[s], seed(hid, s, TICKET)))
            lodging_beds[sid] -= 1
            place(hid, sid, "lodger", "a free ordinary-night bed of the lodging model")
            continue
        division, roofs_ok = in_division(hid, homes)
        if not roofs_ok:
            refused.append({"household": hid, "why": "no dwelling of its division stands"})
            continue
        place(hid, best(hid, roofs_ok),
              "boarder", "boarding in the division's least crowded dwelling" if division
              else "boarding in the town's least crowded dwelling")

    seats.sort(key=lambda s: s["household"])
    inhabited = {sid for sid, n in people.items() if n > 0}
    present_housed = sum(people[sid] for sid in inhabited)
    dwellings = {sid for sid, r in roofs.items()
                 if (r["family"] in DWELLING_FAMILIES and not r["documented"])
                 or (r["documented"] and r["function"] in DOCUMENTED_DWELLINGS)} | inhabited
    crowd = sorted(((people[sid], sid) for sid in pool), reverse=True)
    density = sorted(((round(people[sid] / pool[sid]["area"], 4), sid) for sid in pool),
                     reverse=True)
    return {
        "$schema_note": "DERIVED — regenerate with tools/house_the_present_1835.py; "
                        "tools/check.sh re-derives it. Do not hand-edit.",
        "id": "chicago_july_1835_housing_seats",
        "ticket": TICKET,
        "parent_ticket": "T-1965",
        "target_date": "1835-07-01",
        "generated_by": "tools/house_the_present_1835.py",
        "liberty": LIBERTY,
        "not_a_reading": "no page of any source is read here. Every seat is an adjudication over "
                         "committed records — which standing dwelling a present household with no "
                         "roof shares — and the roof over each of them is the invention. The "
                         "household is the residents layer's and is not touched.",
        "raises_no_roof": "every seat is a household put under a roof that already stands. No "
                          "record is written, no slot is requested and nothing is baked.",
        "inputs": [
            "data/residents/{" + ",".join(RESIDENT_FOLDERS) + "}/*.json",
            "data/reconstruction/1835_address_book.json",
            "data/reconstruction/1835_placement_policy.json",
            "data/reconstruction/1835_lodgers_seated.json (through compile_scene)",
            "data/sidecars/1835/index.json", "data/sidecars/1835/*.json",
            "data/structures/*.json", "data/boats/index.json",
        ],
        "counts": {
            "present_households_already_housed": already,
            "present_households_owed_a_roof": len(owed),
            "seated": len(seats),
            "refused": len(refused),
            "persons_seated": sum(s["persons"] for s in seats),
            "by_rung": dict(sorted(Counter(s["rung"] for s in seats).items())),
            "by_division": dict(sorted(Counter(s["division"] for s in seats).items())),
            "by_family": dict(sorted(Counter(s["family"] for s in seats).items())),
            "roofs_in_the_pool": len(pool),
            "roofs_the_deal_used": len({s["place"] for s in seats}),
            "of_them_assigned_to_their_own_household": len(
                {s["place"] for s in seats if s["place"] not in pool}),
        },
        "the_ceiling": {
            "census_people_per_dwelling": CENSUS_PEOPLE_PER_DWELLING,
            "source": "data/reconstruction/1835_town_model.json people_per_dwelling_november_1835 "
                      "(3,265 people in 398 dwellings)",
            "the_ratio_is": "people under a roof / standing dwellings — the enumerator's own "
                            "division, every dwelling counted whether this layer links "
                            "anybody to it or not",
            "standing_dwellings": len(dwellings),
            "people_under_a_roof": present_housed,
            "people_per_dwelling": round(present_housed / len(dwellings), 3) if dwellings else 0,
            "inhabited_roofs": len(inhabited),
            "people_per_inhabited_roof": round(present_housed / len(inhabited), 3) if inhabited else 0,
            "why_the_two_differ": "documented dwellings no card links and roofs whose record "
                                  "already states its occupants stand in the first count and "
                                  "are refused by this deal; who sleeps in them is T-1966's "
                                  "and T-1615's to settle, not a policy deal's",
            "most_crowded_roof": {"structure_id": crowd[0][1], "people": crowd[0][0],
                                  "floor_m2": pool[crowd[0][1]]["area"]} if crowd else None,
            "densest_roof": {"structure_id": density[0][1], "people_per_m2": density[0][0]}
            if density else None,
        },
        "seats": seats,
        "refused": refused,
    }


def render(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def problems(doc: dict, inputs: dict) -> list[str]:
    out = []
    pool_ok = {sid for sid, r in inputs["roofs"].items() if r["family"] in DWELLING_FAMILIES
               and not r["documented"] and r["occupants"] in (None, "")}
    seen = Counter(s["household"] for s in doc["seats"])
    for hid, n in seen.items():
        if n > 1:
            out.append(f"{hid} is seated {n} times")
        if hid in inputs["seated"]:
            out.append(f"{hid} is seated here and also housed by another overlay")
        if hid not in inputs["cards"]:
            out.append(f"{hid} is seated and no card holds it")
    for s in doc["seats"]:
        if s["place"] not in inputs["standing"]:
            out.append(f"{s['household']} is seated at {s['place']}, which the scene does not stand")
        elif s["place"] not in pool_ok and \
                inputs["roofs"][s["place"]]["assigned_to"] != s["household"]:
            out.append(f"{s['household']} is seated at {s['place']}, which this deal refuses")
    if doc["refused"]:
        out.append(f"{len(doc['refused'])} present household(s) left without a roof")
    ceiling = doc["the_ceiling"]
    if ceiling["people_per_dwelling"] > CENSUS_PEOPLE_PER_DWELLING:
        out.append(f"{ceiling['people_per_dwelling']} people per standing dwelling is above "
                   f"the census's {CENSUS_PEOPLE_PER_DWELLING}")
    return out


def report(doc: dict) -> str:
    c, t = doc["counts"], doc["the_ceiling"]
    return "\n".join([
        f"house the present (T-1971): {c['seated']} of {c['present_households_owed_a_roof']} owed "
        f"households seated, {c['refused']} refused ({c['present_households_already_housed']} "
        f"were already housed)",
        f"  by rung      {c['by_rung']}",
        f"  by division  {c['by_division']}",
        f"  by family    {c['by_family']}",
        f"  roofs        {c['roofs_the_deal_used']} used: {c['roofs_in_the_pool']} in the pool, "
        f"{c['of_them_assigned_to_their_own_household']} assigned to their own household",
        f"  ceiling      {t['people_per_dwelling']} people per standing dwelling "
        f"({t['people_under_a_roof']} under {t['standing_dwellings']}) against the census's "
        f"{t['census_people_per_dwelling']}; {t['people_per_inhabited_roof']} per inhabited "
        f"roof ({t['inhabited_roofs']}); most crowded {t['most_crowded_roof']}",
    ])


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

    expect("a seat on a roof the scene does not stand",
           lambda d: d["seats"][0].update(place="no_such_structure"))
    expect("a household seated twice", lambda d: d["seats"].append(dict(d["seats"][0])))
    expect("a seat on a documented building", lambda d: d["seats"][0].update(
        place=next(s for s, r in sorted(inputs["roofs"].items()) if r["documented"])))
    expect("a present household left unhoused",
           lambda d: d["refused"].append({"household": "hh_x", "why": "test"}))
    expect("a town above the census's crowding",
           lambda d: d["the_ceiling"].update(people_per_dwelling=9.0))
    if failures:
        print("SELF-TEST FAILED — the guard did not fire on: " + "; ".join(failures))
        return 1
    print("self-test: all five guards fire")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    inputs = read_inputs()
    if args.self_test:
        return self_test(inputs)
    doc = deal(inputs)
    if args.report:
        print(report(doc))
        return 0
    if args.check:
        errors = problems(doc, inputs)
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != render(doc):
            errors.append(f"{OUT.relative_to(ROOT)} is stale — run tools/house_the_present_1835.py")
        print(report(doc))
        if errors:
            print("HOUSING DEAL FAILED\n  - " + "\n  - ".join(errors))
            return 1
        return 0
    errors = problems(doc, inputs)
    OUT.write_text(render(doc), encoding="utf-8")
    print(report(doc))
    print(f"wrote {OUT.relative_to(ROOT)}")
    if errors:
        print("but it is not clean:\n  - " + "\n  - ".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
