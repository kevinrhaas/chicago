#!/usr/bin/env python3
"""The town's completion audit: how far the four joins T-1215 names are from total.

T-1964, piece 1 of T-1215 (the closeout of the whole reconstruction). The owner's stop
condition is *"every person in Chicago has a place to live and a place to work"*, and
T-1215's first clause turns it into four joins over committed data:

1. **Housed.** Every resident card's household reaches a standing structure, a vessel or
   a camp — through its own `lives_at`, or because a structure's sidecar seats it under
   `residents[]` (the lodging houses and the reconstructed roofs carry their people that
   way round, and a card cannot point back at a bed). A household the housing deal counts
   APART with a stated reason (T-1972: absent on the scene date, or ruled present and
   waiting on a roof the scene does not stand yet) is not counted unhoused, and is not
   counted housed either: it has its own row, and a household still WAITING keeps the
   join from reading total. Presence is the card's, or T-1386's ruling where it has one.
2. **At work.** Every person of working age carries a workplace, or a stated reason why
   none is owed. This is a read of `data/residents/employment_coverage.json` (T-1461),
   which already adjudicates one employment answer per person; it is not re-decided here.
3. **Roofed.** Every business's primary location is a standing structure, or a stated
   limit (`street_only`, `unplaceable`, `anchored`) with the reason the limit holds —
   T-1147's limits, preserved and printed.
4. **Occupied.** Every standing structure carries somebody (a household, a lodger, a
   business, a reconstructed occupation), or a use that needs nobody (an outbuilding
   that names its yard, a civic or harbour work, a camp ground, a house to let, an
   anonymous roof whose use data/reconstruction/1835_stated_uses.json states, T-1988), or
   is one building of an establishment whose principal answers (`part_of`, T-1980), or
   says on its record why nobody is seated under it (`stated_use`, T-1985). A
   sidecar whose `occupants` attribute names people in prose but whose household card
   is not linked is counted on its own row, `occupants_in_prose_only`: the roof is not
   empty, but the person it names is not yet housed by the join, and that link is owed.

**This is a measurement, not a remedy.** It writes nobody, seats nobody and raises no
roof. What it writes is the gap list the remaining pieces of T-1215 close: T-1965 the
unhoused, T-1966 the work and the empty roofs. The gaps are therefore NOT a failure of
the gate — they are the work the town still owes, counted where a run can read them.

**What IS a failure is a dangling id**: a `lives_at` naming a structure the scene does
not carry, a sidecar seating a household no card holds, a workplace naming a business
that does not exist, a business premises naming a structure that is not standing. Those
are broken links, not headroom, and `--check` refuses them.

Every count is split by tier — `attested` / `inferred` / `reconstructed` — because the
closeout's own rule is that a reader can see how much of the finished town rests on
which rung.

    tools/audit_town_completion_1835.py              write data/render/town_completion_1835.json
                                                     and docs/RESEARCH/1835_town_completion.md
    tools/audit_town_completion_1835.py --check      fail on drift from the committed file,
                                                     or on any dangling id
    tools/audit_town_completion_1835.py --self-test  break one link of each kind in memory
                                                     and prove the check sees it
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
YEAR = "1835"
OUT = DATA / "render" / "town_completion_1835.json"
# The same numbers as a page a person reads (T-1967): every table by tier. Written from
# the audit document above and nothing else, so the two cannot disagree.
REPORT = ROOT / "docs" / "RESEARCH" / "1835_town_completion.md"

TIERS = ("attested", "inferred", "reconstructed")

# The folders of `data/residents/` whose cards are people of the town. `merged` is not
# one (its cards were folded into another), and `transients` is counted APART: the
# visitors of the season kept no residence by construction (T-1353), so they are never
# housed and never unhoused — they are reported on their own row, as town_census does.
RESIDENT_FOLDERS = ("households", "reconstructed_trades", "lodgers", "underdocumented",
                    "readmitted", "institutional")
TRANSIENT_FOLDER = "transients"

# A structure's `function.value`, read for the one question this file asks of it: does
# an EMPTY one of these owe somebody? A dwelling or a shop with nobody in it does. An
# outbuilding does not, once it names the yard it serves; a civic or harbour work, a
# camp ground and a house recorded to let do not at all.
OUTBUILDING = {
    "barn", "barn_or_carriage_shed", "hotel_stable", "outbuilding", "privy", "root_cellar",
    "sawpit_shed", "small_utility_building", "stable", "stable_and_wagon_yard",
    "tavern_stable", "wash_house", "woodshed_or_storage_shed", "military_barn",
}
CIVIC = {
    "artillery_house", "block_house", "church", "commanding_officers_quarters",
    "company_gardens", "council_house", "enlisted_mens_barracks", "garrison_flagstaff",
    "guard_house", "harbour_light", "harbour_works", "jail", "livestock_pound",
    "meeting_house_and_school", "meeting_house_school", "military_post_enclosure",
    "officers_quarters", "parade_and_drill_ground", "powder_magazine", "river_crossing",
    "school", "street_crossing", "hotel_under_construction",
}
CAMP = {"emigrant_camp"}
TO_LET = {"dwelling_to_let"}
DWELLING_WORDS = ("dwelling", "cottage", "house", "residence", "shanty", "cabin",
                  "boarding", "quarters", "hotel", "tavern")

# The employment ledger's reasons, read into the three answers this audit gives.
# T-1993: a domestic the taverns had no room for is in another household's service by the
# trade's own premises ruling, and a private household is not a house the register owes.
WORK_STATED = {"no_employer_named",           # the trade kept no premises: stated, not owed
               "in_service_in_another_household",
               "class_full_none_owed"}         # the class's count is met (T-1995)
WORK_OWED = {"class_held_no_house", "trade_attested_no_house_named",
             "no_ruling_on_the_trade", "keeps_their_own_house"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def value_of(field) -> str | None:
    if isinstance(field, dict):
        return field.get("value")
    return field


def tier_of(grade) -> str:
    return grade if grade in TIERS else "reconstructed"


def read_inputs() -> dict:
    sidecar_index = load(DATA / "sidecars" / YEAR / "index.json")
    structures = {}
    for row in sidecar_index["structures"]:
        record_path = DATA / "structures" / f"{row['id']}.json"
        record = load(record_path) if record_path.exists() else {}
        sidecar = load(DATA / row["sidecar"])
        attributes = sidecar.get("attributes") if isinstance(sidecar.get("attributes"), dict) else {}
        structures[row["id"]] = {"record": record, "residents": sidecar.get("residents") or [],
                                 "occupants": value_of(attributes.get("occupants"))}

    cards = {}
    for folder in RESIDENT_FOLDERS + (TRANSIENT_FOLDER,):
        for path in sorted((DATA / "residents" / folder).glob("*.json")):
            card = load(path)
            if isinstance(card, dict) and card.get("id"):
                cards[card["id"]] = {"folder": folder, "card": card}

    businesses = {}
    for path in sorted((DATA / "businesses").glob("*.json")) + \
            sorted((DATA / "businesses" / "authored").glob("*.json")):
        record = load(path)
        if isinstance(record, dict) and record.get("id") and "locations" in record:
            businesses[record["id"]] = record

    boats = load(DATA / "boats" / "index.json").get("boats") or []
    vessels = {b["id"] for b in boats if isinstance(b, dict) and b.get("id")}

    # Who the town holds present beyond the cards (T-1386's rulings), and who the housing
    # deal counted apart with a stated reason (T-1972): an absence on the day, or a ruled-in
    # household waiting for a roof the scene does not stand yet.
    rulings = load(DATA / "reconstruction" / "1835_presence_rulings.json")["rulings"]
    seats_path = DATA / "reconstruction" / "1835_housing_seats.json"
    apart = load(seats_path).get("counted_apart") or [] if seats_path.exists() else []

    # T-1988. A stated use (T-1782) reaches the card as an `occupants` block, but it names
    # nobody, so it is read from its own ledger as a use and never as a person owed a link.
    stated = load(DATA / "reconstruction" / "1835_stated_uses.json").get("rows") or []

    return {
        "structures": structures,
        "stated_uses": {row["structure_id"] for row in stated},
        "ruled_present": {r["household_id"] for r in rulings
                          if value_of(r.get("present_on_scene_date")) == "present"},
        "counted_apart": {r["household"]: r["why"] for r in apart},
        "cards": cards,
        "businesses": businesses,
        "vessels": vessels,
        "employment": load(DATA / "residents" / "employment_coverage.json")["rows"],
        "streets": load(DATA / "streets" / f"{YEAR}.json").get("streets") or [],
    }


def by_tier() -> dict:
    return {t: 0 for t in TIERS}


def audit(inputs: dict) -> dict:
    structures = inputs["structures"]
    cards = inputs["cards"]
    businesses = inputs["businesses"]
    vessels = inputs["vessels"]
    camps = {sid for sid, s in structures.items()
             if value_of(s["record"].get("function")) in CAMP}
    dangling: list[str] = []

    # --- 1. housed ----------------------------------------------------------------------
    seated_at: dict[str, str] = {}
    for sid, s in sorted(structures.items()):
        for entry in s["residents"]:
            hid = entry.get("household")
            if hid not in cards:
                dangling.append(f"structure {sid} seats household {hid}, which no card holds")
            else:
                seated_at.setdefault(hid, sid)

    housed = {"households": {"housed": 0, "unhoused": 0, "counted_apart": 0},
              "counted_apart": Counter(), "persons_counted_apart": Counter(),
              "persons_housed": by_tier(), "persons_unhoused": by_tier(),
              "present_on_scene_date": {"persons_housed": 0, "persons_unhoused": 0,
                                        "persons_waiting_on_a_roof": 0},
              "housed_through": Counter(), "unhoused_by_folder": Counter(),
              "unhoused_present_households": []}
    # The same four joins, split by tier for every kind of record the closeout names
    # (T-1967): the finished town has to say how much of it rests on which rung, and a
    # total without its tiers cannot. A household's tier is its head's grade — the
    # person the record is argued around — falling back to its first member.
    tiers = {
        "persons": {k: by_tier() for k in ("housed", "waiting_on_a_roof",
                                           "absent_on_the_scene_date", "unhoused")},
        "households": {k: by_tier() for k in ("housed", "waiting_on_a_roof",
                                              "absent_on_the_scene_date", "unhoused")},
        "businesses": {k: by_tier() for k in ("at_a_standing_structure", "stated_limit",
                                              "open")},
        "structures": {k: by_tier() for k in ("occupied", "occupants_in_prose_only",
                                              "use_stated", "empty_owing_somebody")},
        "streets": {k: by_tier() for k in ("course", "surface")},
    }
    lives_at_of: dict[str, str] = {}
    for hid, entry in sorted(cards.items()):
        if entry["folder"] == TRANSIENT_FOLDER:
            continue
        card = entry["card"]
        where = value_of(card.get("lives_at"))
        through = None
        if where:
            if where in structures:
                through = "camp" if where in camps else "lives_at"
                lives_at_of[hid] = where
            elif where in vessels:
                through = "vessel"
            else:
                dangling.append(f"household {hid} lives_at {where}, which the scene does not carry")
        if through is None and hid in seated_at:
            through = "seated_by_a_structure"
        persons = card.get("persons") or []
        present = (value_of(card.get("present_on_scene_date")) == "present"
                   or hid in inputs["ruled_present"])
        apart = None if through else inputs["counted_apart"].get(hid)
        status = "housed" if through else (apart if apart in tiers["persons"] else
                                           "unhoused" if not apart else None)
        if status:
            head = next((p for p in persons if p.get("id") == card.get("head")),
                        persons[0] if persons else {})
            tiers["households"][status][tier_of(head.get("grade"))] += 1
            for p in persons:
                tiers["persons"][status][tier_of(p.get("grade"))] += 1
        if through:
            housed["households"]["housed"] += 1
            housed["housed_through"][through] += 1
        elif apart:
            housed["households"]["counted_apart"] += 1
            housed["counted_apart"][apart] += 1
            housed["persons_counted_apart"][apart] += len(persons)
        else:
            housed["households"]["unhoused"] += 1
            housed["unhoused_by_folder"][entry["folder"]] += 1
            if present:
                housed["unhoused_present_households"].append(hid)
        if apart:
            if present:
                housed["present_on_scene_date"]["persons_waiting_on_a_roof"] += len(persons)
            continue
        side = "persons_housed" if through else "persons_unhoused"
        for p in persons:
            housed[side][tier_of(p.get("grade"))] += 1
        if present:
            housed["present_on_scene_date"][side] += len(persons)

    visitors = {"persons": 0, "lodged_at_stated": 0}
    for entry in cards.values():
        if entry["folder"] != TRANSIENT_FOLDER:
            continue
        for p in entry["card"].get("persons") or []:
            visitors["persons"] += 1
            if p.get("lodged_at") or entry["card"].get("lodged_at"):
                visitors["lodged_at_stated"] += 1

    # --- 2. at work ---------------------------------------------------------------------
    work = {"working_age": 0, "placed": by_tier(), "stated_no_fixed_premises": by_tier(),
            "owed": by_tier(), "no_trade_recorded": by_tier(), "owed_by_reason": Counter()}
    grade_of = {p.get("id"): p.get("grade")
                for e in cards.values() for p in e["card"].get("persons") or []}
    employed_at: Counter = Counter()
    for row in inputs["employment"]:
        for house in row.get("houses") or []:
            if house not in businesses:
                dangling.append(f"person {row['person_id']} works at {house}, "
                                "which no business record holds")
            else:
                employed_at[house] += 1
        if row.get("age_scope") != "working_age" or row.get("record_folder") == TRANSIENT_FOLDER:
            continue
        work["working_age"] += 1
        tier = tier_of(grade_of.get(row["person_id"]))
        reason = row.get("reason")
        if row.get("houses"):
            work["placed"][tier] += 1
        elif reason in WORK_STATED:
            work["stated_no_fixed_premises"][tier] += 1
        elif reason in WORK_OWED:
            work["owed"][tier] += 1
            work["owed_by_reason"][reason] += 1
        else:
            work["no_trade_recorded"][tier] += 1

    # --- 3. roofed ----------------------------------------------------------------------
    roofed = {"businesses": len(businesses), "at_a_standing_structure": by_tier(),
              "stated_limit": Counter(), "open": []}
    business_at: Counter = Counter()
    for bid, b in sorted(businesses.items()):
        locations = b.get("locations") or []
        for loc in locations:
            sid = loc.get("structure_id")
            if sid and sid not in structures:
                dangling.append(f"business {bid} names premises {sid}, which the scene does not carry")
            elif sid:
                business_at[sid] += 1
        primary = next((l for l in locations if l.get("primary")), locations[0] if locations else None)
        b_tier = tier_of((primary or {}).get("tier"))
        if primary and primary.get("structure_id") in structures:
            roofed["at_a_standing_structure"][b_tier] += 1
            tiers["businesses"]["at_a_standing_structure"][b_tier] += 1
        elif primary and primary.get("limit_reason"):
            roofed["stated_limit"][primary.get("kind") or "unstated_kind"] += 1
            tiers["businesses"]["stated_limit"][b_tier] += 1
        else:
            roofed["open"].append(bid)
            tiers["businesses"]["open"][b_tier] += 1

    # --- 4. occupied --------------------------------------------------------------------
    lived_in = Counter(lives_at_of.values())
    occupied = {"structures": len(structures), "occupied": by_tier(),
                "occupants_in_prose_only": by_tier(), "use_stated": Counter(),
                "empty_owing_somebody": Counter(), "empty": []}
    def bucket_of(sid: str) -> tuple[str, str, str]:
        """(bucket, key, tier) for one roof on its OWN evidence — `part_of` aside."""
        s = structures[sid]
        record = s["record"]
        function = value_of(record.get("function")) or ""
        recon = record.get("reconstruction") if isinstance(record.get("reconstruction"), dict) else {}
        tier = "reconstructed" if recon else tier_of(
            (record.get("function") or {}).get("confidence") if isinstance(record.get("function"), dict) else None)
        if s["residents"] or lived_in[sid] or business_at[sid] or recon.get("occupation"):
            return "occupied", tier, tier
        if function in TO_LET:
            return "use_stated", "vacant_to_let", tier
        if function in CAMP:
            return "use_stated", "camp_ground", tier
        if sid in inputs["stated_uses"]:
            return "use_stated", "stated_use_of_an_anonymous_roof", tier
        if s["occupants"]:
            return "occupants_in_prose_only", tier, tier
        if function in CIVIC:
            return "use_stated", "civic_or_works", tier
        if function in OUTBUILDING and (recon.get("yard_group") or recon.get("stands_on")):
            return "use_stated", "outbuilding_of_a_yard", tier
        # T-1985. A roof whose record SAYS why nobody is seated under it — a freight shed
        # whose keeper no source names, a house whose named occupant's card refuses the
        # seat, a house nobody is placed in on the scene date — is answered by that
        # statement, under its own reason, and never by a household invented to fill it.
        stated = record.get("stated_use") if isinstance(record.get("stated_use"), dict) else {}
        if stated.get("value") and stated.get("note"):
            return "use_stated", stated["value"], tier
        kind = ("outbuilding_naming_no_yard" if function in OUTBUILDING
                else "dwelling" if any(w in function for w in DWELLING_WORDS)
                else "house_of_trade")
        return "empty", kind, tier

    # T-1980. A roof that is ONE BUILDING OF AN ESTABLISHMENT — the post's barn, the
    # tannery's bark shed — names its principal in `part_of`, and its keepers are the
    # principal's. It is answered by that only while the principal answers on its own
    # evidence: a `part_of` naming a structure the scene does not carry, or one that is
    # itself empty, is a broken link and is reported as one, never counted as a use.
    for sid, s in sorted(structures.items()):
        bucket, key, tier = bucket_of(sid)
        principal = value_of(s["record"].get("part_of"))
        if principal and principal not in structures:
            dangling.append(f"structure {sid} is part of {principal}, which the scene does not carry")
        elif principal and bucket_of(principal)[0] == "empty":
            dangling.append(f"structure {sid} is part of {principal}, which is itself empty")
        elif principal and bucket == "empty":
            bucket, key = "use_stated", "part_of_an_establishment"
        # T-1985. The statement is about an EMPTY roof. Once somebody is seated there it
        # is stale, and it is refused rather than left to contradict the seat.
        stated = value_of(s["record"].get("stated_use"))
        if stated and bucket in ("occupied", "occupants_in_prose_only"):
            dangling.append(f"structure {sid} states why nobody is seated ({stated}), "
                            f"but somebody is")
        tiers["structures"]["empty_owing_somebody" if bucket == "empty" else bucket][tier] += 1
        if bucket == "empty":
            occupied["empty_owing_somebody"][key] += 1
            occupied["empty"].append(sid)
        else:
            occupied[bucket][key] += 1

    # --- 5. the streets: where each ran, and what it was surfaced with --------------------
    for street in inputs["streets"]:
        tiers["streets"]["course"][tier_of(street.get("geometry_confidence"))] += 1
        tiers["streets"]["surface"][tier_of(street.get("surface_confidence"))] += 1

    def plain(o):
        if isinstance(o, Counter):
            return dict(sorted(o.items()))
        if isinstance(o, dict):
            return {k: plain(v) for k, v in o.items()}
        if isinstance(o, list):
            return sorted(o)
        return o

    housed_n = housed["households"]["housed"]
    unhoused_n = housed["households"]["unhoused"]
    waiting_n = housed["counted_apart"].get("waiting_on_a_roof", 0)
    owed_n = sum(work["owed"].values())
    open_roofs = len(roofed["open"])
    empty_n = len(occupied["empty"])
    doc = {
        "$schema_note": "DERIVED — regenerate with tools/audit_town_completion_1835.py; "
                        "tools/check.sh re-derives it. Do not hand-edit.",
        "id": "1835_town_completion_audit",
        "ticket": "T-1964",
        "parent_ticket": "T-1215",
        "target_date": "1835-07-01",
        "generated_by": "tools/audit_town_completion_1835.py",
        "not_a_remedy": "A measurement over committed files: nobody is written, seated or "
                        "roofed here. The gaps are the work T-1215's remaining pieces close "
                        "(T-1965 the unhoused, T-1966 the work and the empty roofs); only a "
                        "dangling id fails the gate.",
        "inputs": [
            "data/sidecars/1835/index.json", "data/sidecars/1835/*.json",
            "data/structures/*.json", "data/boats/index.json",
            "data/residents/{" + ",".join(RESIDENT_FOLDERS + (TRANSIENT_FOLDER,)) + "}/*.json",
            "data/residents/employment_coverage.json",
            "data/reconstruction/1835_presence_rulings.json",
            "data/reconstruction/1835_housing_seats.json#counted_apart",
            "data/businesses/*.json", "data/businesses/authored/*.json",
            f"data/streets/{YEAR}.json",
        ],
        "summary": {
            "households_housed": housed_n,
            "households_unhoused": unhoused_n,
            "households_counted_apart": dict(sorted(housed["counted_apart"].items())),
            "working_age_persons_owed_a_workplace": owed_n,
            "businesses_neither_roofed_nor_stated": open_roofs,
            "structures_empty_owing_somebody": empty_n,
            "dangling_ids": len(dangling),
            "the_join_is_total": not (unhoused_n or waiting_n or owed_n or open_roofs or empty_n
                                      or dangling),
        },
        "housed": plain(housed),
        "visitors_counted_apart": visitors,
        "at_work": plain(work),
        "roofed": plain(roofed),
        "occupied": plain(occupied),
        "tiers": tiers,
        "dangling": sorted(dangling),
    }
    # The four joins as the City card shows them (T-1967): read here once, so the page
    # never re-derives a gap and cannot disagree with this file.
    doc["joins"] = [{"join": key, "label": label, "open": gap(doc), "what_keeps_it_open": what}
                    for key, label, gap, what in JOINS]
    return doc


def render(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


ROW_LABELS = {
    "housed": "housed", "waiting_on_a_roof": "counted apart — waiting on a roof",
    "absent_on_the_scene_date": "counted apart — absent on the scene date",
    "unhoused": "unhoused (owed a roof)",
    "at_a_standing_structure": "at a standing structure", "stated_limit": "a stated limit",
    "open": "neither (owed)",
    "occupied": "occupied", "occupants_in_prose_only": "occupants named in prose only",
    "use_stated": "a use that needs nobody", "empty_owing_somebody": "empty, owing somebody",
    "course": "where it ran", "surface": "what it was surfaced with",
    "placed": "at a workplace", "stated_no_fixed_premises": "no fixed premises (stated)",
    "owed": "owed a workplace", "no_trade_recorded": "no trade recorded",
}

# The four joins, in the closeout's order, with the figure that keeps each one open.
JOINS = (
    ("housed", "Every household housed",
     lambda d: d["summary"]["households_unhoused"]
     + d["summary"]["households_counted_apart"].get("waiting_on_a_roof", 0),
     "households without a roof yet"),
    ("at_work", "Every working person at a workplace",
     lambda d: d["summary"]["working_age_persons_owed_a_workplace"],
     "working people owed a workplace"),
    ("roofed", "Every business roofed or its limit stated",
     lambda d: d["summary"]["businesses_neither_roofed_nor_stated"],
     "businesses neither roofed nor given a stated limit"),
    ("occupied", "Every standing roof occupied or its use stated",
     lambda d: d["summary"]["structures_empty_owing_somebody"],
     "standing roofs empty and owed somebody"),
)


def share(n: int, whole: int) -> str:
    return f"{100 * n / whole:.1f} %" if whole else "—"


def tier_table(title: str, rows: dict, summed: bool = True) -> list[str]:
    totals = {t: sum(r[t] for r in rows.values()) for t in TIERS}
    whole = sum(totals.values())
    out = [f"### {title}", "",
           "| | attested | inferred | reconstructed | all |", "|---|---:|---:|---:|---:|"]
    for key, r in rows.items():
        out.append(f"| {ROW_LABELS.get(key, key)} | " + " | ".join(f"{r[t]:,}" for t in TIERS)
                   + f" | {sum(r.values()):,} |")
    if summed:
        out.append("| **all** | " + " | ".join(f"**{totals[t]:,}**" for t in TIERS)
                   + f" | **{whole:,}** |")
        out.append("| share | " + " | ".join(share(totals[t], whole) for t in TIERS) + " | |")
    return out + [""]


def render_markdown(doc: dict) -> str:
    s = doc["summary"]
    tiers = doc["tiers"]
    closed = sum(1 for j in doc["joins"] if j["open"] == 0)
    housed = tiers["persons"]["housed"]
    whole = sum(housed.values())
    lines = [
        "# The town's completion, 1 July 1835 — by tier",
        "",
        "> GENERATED by `tools/audit_town_completion_1835.py` from "
        "`data/render/town_completion_1835.json` (T-1967, a piece of T-1215). "
        "`tools/check.sh` re-derives it; do not hand-edit.",
        "",
        "The closeout of the reconstruction (T-1215) asks four joins of the committed data: every "
        "household housed, every working person at a workplace, every business roofed or its "
        "limit stated, every standing roof occupied or its use stated. This page prints how far "
        "each is from total, and every table split by the three tiers — **attested** (a source "
        "states it), **inferred** (reasoned from evidence about this particular thing) and "
        "**reconstructed** (built within stated bounds because the scene needs it). It is a "
        "measurement: nothing here seats, roofs or writes anybody.",
        "",
        f"## The joins — {closed} of {len(doc['joins'])} closed",
        "",
        "| join | state | what keeps it open |",
        "|---|---|---|",
    ]
    for j in doc["joins"]:
        n = j["open"]
        lines.append(f"| {j['label']} | {'closed' if n == 0 else 'open'} | "
                     f"{f'{n:,} ' + j['what_keeps_it_open'] if n else '—'} |")
    lines += [
        "",
        f"Dangling ids: **{s['dangling_ids']}**. The town is "
        + ("**complete to the reconstruction**: every join is total."
           if s["the_join_is_total"] else
           "**not yet complete**: the open joins above are the work T-1215's remaining "
           "pieces owe."),
        "",
        "## The three tiers' shares of the people housed",
        "",
        f"Of the **{whole:,}** people housed in a standing building: "
        + ", ".join(f"**{share(housed[t], whole)} {t}** ({housed[t]:,})" for t in TIERS) + ".",
        "",
        "## Every table by tier",
        "",
    ]
    lines += tier_table("Persons", tiers["persons"])
    lines += tier_table("Households (by the head's grade)", tiers["households"])
    work = doc["at_work"]
    lines += tier_table("Working-age persons", {k: work[k] for k in
                                                ("placed", "stated_no_fixed_premises",
                                                 "owed", "no_trade_recorded")})
    lines += tier_table("Businesses (by the primary location's tier)", tiers["businesses"])
    lines += tier_table("Standing structures", tiers["structures"])
    # Two questions asked of the same streets, so the rows are not summed.
    lines += tier_table("Streets (two questions of each street — not summed)",
                        tiers["streets"], summed=False)
    visitors = doc["visitors_counted_apart"]
    lines += [
        "Visitors of the season (T-1353) are counted apart and are in none of these tables: "
        f"{visitors['persons']:,} persons, {visitors['lodged_at_stated']:,} of them with a "
        "stated lodging.",
        "",
    ]
    return "\n".join(lines)


def report(doc: dict) -> str:
    s = doc["summary"]
    h = doc["housed"]
    return "\n".join([
        f"town completion (T-1215): the join is {'TOTAL' if s['the_join_is_total'] else 'not yet total'}",
        f"  housed      {s['households_housed']} households, {s['households_unhoused']} unhoused "
        f"({len(h['unhoused_present_households'])} of them present on the scene date); "
        f"counted apart {s['households_counted_apart']}",
        f"  at work     {s['working_age_persons_owed_a_workplace']} working-age persons owed a workplace",
        f"  roofed      {s['businesses_neither_roofed_nor_stated']} businesses neither roofed nor stated",
        f"  occupied    {s['structures_empty_owing_somebody']} standing structures empty and owing somebody",
        f"  dangling    {s['dangling_ids']}",
    ])


def check(doc: dict) -> list[str]:
    errors = [f"DANGLING: {d}" for d in doc["dangling"]]
    if not OUT.exists():
        errors.append(f"{OUT.relative_to(ROOT)} is missing — run tools/audit_town_completion_1835.py")
    elif OUT.read_text(encoding="utf-8") != render(doc):
        errors.append(f"{OUT.relative_to(ROOT)} is stale — run tools/audit_town_completion_1835.py")
    if not REPORT.exists() or REPORT.read_text(encoding="utf-8") != render_markdown(doc):
        errors.append(f"{REPORT.relative_to(ROOT)} is missing or stale — "
                      "run tools/audit_town_completion_1835.py")
    return errors


def self_test(inputs: dict) -> int:
    """Break one link of each kind and prove each is reported as dangling."""
    failures = []
    base = len(audit(inputs)["dangling"])

    def expect(label: str, mutate) -> None:
        broken = copy.deepcopy(inputs)
        mutate(broken)
        if len(audit(broken)["dangling"]) <= base:
            failures.append(label)

    def bad_lives_at(i):
        hid = next(h for h, e in sorted(i["cards"].items()) if e["folder"] == "households")
        i["cards"][hid]["card"]["lives_at"] = {"value": "no_such_structure"}

    def bad_seat(i):
        sid = next(iter(sorted(i["structures"])))
        i["structures"][sid]["residents"] = [{"household": "hh_no_such_household"}]

    def bad_workplace(i):
        i["employment"] = i["employment"] + [{"person_id": "nobody", "houses": ["biz_no_such_house"]}]

    def bad_premises(i):
        bid = next(iter(sorted(i["businesses"])))
        i["businesses"][bid]["locations"] = [{"primary": True, "structure_id": "no_such_structure"}]

    expect("a lives_at naming no structure", bad_lives_at)
    expect("a sidecar seating no card", bad_seat)
    expect("a workplace naming no business", bad_workplace)
    def bad_part_of(i):
        sid = next(iter(sorted(i["structures"])))
        i["structures"][sid]["record"]["part_of"] = {"value": "no_such_structure"}

    def empty_principal(i):
        # a principal made for the test, so it still bites once no real roof is empty
        i["structures"]["zz_self_test_empty_house"] = {
            "record": {"function": {"value": "dwelling"}}, "residents": [], "occupants": None}
        sid = next(iter(sorted(i["structures"])))
        i["structures"][sid]["record"]["part_of"] = {"value": "zz_self_test_empty_house"}

    expect("a premises naming no structure", bad_premises)
    expect("a part_of naming no structure", bad_part_of)
    expect("a part_of naming an empty principal", empty_principal)

    def stale_stated_use(i):
        # a stated use left on a roof somebody is seated in
        sid = next(sid for sid, st in sorted(i["structures"].items()) if st["residents"])
        i["structures"][sid]["record"]["stated_use"] = {
            "value": "occupancy_unattested", "confidence": "inferred", "note": "self-test"}

    expect("a stated use on an occupied roof", stale_stated_use)
    if failures:
        print("SELF-TEST FAILED — the check did not see: " + "; ".join(failures))
        return 1
    print("self-test: all seven broken links are refused")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    inputs = read_inputs()
    if args.self_test:
        return self_test(inputs)
    doc = audit(inputs)
    if args.check:
        errors = check(doc)
        print(report(doc))
        if errors:
            print("TOWN COMPLETION AUDIT FAILED\n  - " + "\n  - ".join(errors))
            return 1
        return 0
    OUT.write_text(render(doc), encoding="utf-8")
    REPORT.write_text(render_markdown(doc), encoding="utf-8")
    print(report(doc))
    print(f"wrote {OUT.relative_to(ROOT)} and {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
