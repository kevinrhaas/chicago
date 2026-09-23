#!/usr/bin/env python3
"""T-1353, stage `transients` — the summer crowd of 1835, counted apart from the town.

    python3 tools/reconstruct_transients_1835.py --build      draw them, write the cards
    python3 tools/reconstruct_transients_1835.py --check      re-derive and refuse drift
    python3 tools/reconstruct_transients_1835.py --report     who was drawn, and against what
    python3 tools/reconstruct_transients_1835.py --self-test  the rules, each refusing its own case

WHAT THIS STAGE IS. The Chicago American of 13 June 1835 puts the town's own population
at 2,500 to 3,000 and then says, in the next breath, that "strangers, to the amount of
some hundreds more, fill our public houses and streets". MORE — outside its own estimate.
T-1352 bounded those strangers at 192 to 900 persons on 1 July 1835 and deliberately
adopted no point, printing two candidates and leaving the choice here. This stage spends
one of them, mints the crowd as reconstructed persons, and keeps it OUT of the resident
count, because a visitor of the season is not a resident and the whole distinction is
what the model is built on.

THE POINT THIS STAGE ADOPTS: **384**, the reading `twice the 1843 rate`.

Why that one and not 550. The 384 stands on the only figure Chicago's own enumerator ever
printed for transients — 533 of them, in a row of his own, in the census of 1 August 1843 —
doubled because 1 July 1835 was a land-sale week and 1 August 1843 was not. The multiplier
is invented and the model says so; the RATE under it is measured. The 550 is the midpoint
of a newspaper's "some hundreds more", which is an editor's impression printed eighteen
days before the scene and BEFORE the sale crowd arrived, and which the same paper offers
as a phrase rather than as a count. This project prefers a measured comparandum with an
invented multiplier over a rhetorical band read at its middle, because the first names the
one invented step and the second is invented end to end. Both sit inside T-1352's bracket;
384 is the lower and this stage takes the lower, as the bracket's own floor row does.

AND THE CAPACITY ARGUMENT THAT LOOKS LIKE EVIDENCE AND IS NOT. The lodging model's BUILT
places carry 320 surge beds — the gap between their ordinary night and their crowded one —
and the minted cohort below is 307, which is a near-perfect fit and would read as a
confirmation. It is not one. The town of 1835 had 42 boarding houses and this
reconstruction has built five of them; the programme's full surge is 764, not 320, and the
fit is a measurement of how far the STRUCTURE band has got rather than of anything the
crowd did. Reading it the other way would let the reconstruction's own incompleteness
choose a population, so it is written down here and refused.

WHAT IT MINTS, AND THE FOUR THINGS IT REFUSES TO MINT. Of the 384, seventy-seven are set
aside and 307 are drawn. Each refusal has a reason a reader can check:

  1. THE NAMED LAND-SALE PURCHASERS. The Public Domain register enters 232 purchases at
     Chicago on 26-27 June 1835 from 105 distinct purchasers, of whom the resident
     crosswalk can place only 28 in the town — a floor of 77 visitors the register NAMES.
     A drawn person may never stand in for a person a source names, so those 77 slots are
     reserved and left empty. They are owed a reading, not a draw.
  2. THE CREWS ASHORE. T-1352 records 4 to 6 hulls lying at Chicago on the scene date from
     the Marine Journal of 4 July 1835, and no committed source in this corpus gives a
     crew complement for an 1830s lake schooner. Without one, a crew is a number this
     project would be inventing whole, so the hulls carry nobody and T-1372 — which seats
     the crews — is told what it is waiting for.
  3. THE HARBOUR-WORKS GANG. The federal harbour improvement was at work through 1835 and
     no committed source gives its strength in any month. Same refusal, same reason.
  4. THE TRAVELLERS OF BUSINESS AND OF STATE. The papers name these one at a time — the
     Democrat of 1 July has Lewis Cass, Secretary of War, arrived on the 29th in the
     steamer Michigan. A man a newspaper names is a reading waiting to be made, and
     drawing an invented traveller beside him would bury him.

  So the 307 are ONE row of T-1352's composition table: the immigrant and land-seeking
  parties awaiting lots — the row the sources describe as a crowd rather than as people
  they could name. "Our wharves are covered with men, women and children just landed from
  the vessels."

WHERE THEY SLEPT — and the one liberty this stage takes. T-1352 names six classes of
sleeping place, each a sentence in a committed source, and RANKS NONE OF THEM. No source
in this corpus gives a share. An equal deal across the six is therefore the only
apportionment that adds no ranking the record does not carry; it is stated as a liberty,
it is seeded, and every share is replaceable by a source that ranks them. 307 over six is
51 apiece with one over, and the remainder goes to the first class in the table's own
printed order.

  * The four ROOFED classes — a room in a public house, the floor of that room, the floor
    of a private house, a store house thrown open — become `party` households, and their
    `lodged_at` row resolves to the CLASS and not to a house. This stage names no inn and
    fills no bed: the lodging places' beds are dealt by T-1371 and T-1372 out of the
    lodging model's surge, and a transient seated into a tavern here would be booked into
    a bed that stage is about to sell twice.
  * The two OUT-OF-DOORS classes — the open sky upon the wharves, a tent at the landing
    place — become `camp` households whose `lodged_at` row names `the_landing_place`, the
    one camp ground a committed source actually puts people on ("Some build tents upon the
    spot they were landed from the boats"). It is a CANDIDATE, not a placement: T-1214
    owns where a camp stands and how large it is, and the row says so.

WHY `lodged_at[]` AND NOT `lives_at`. `lives_at` is the residence a household kept in this
town, and the town census counts a person as housed when it names a structure the scene
carries. A visitor of the season kept no residence, and writing one would move the resident
count — which is the one thing this ticket forbids. So the singular field stays null with
its reason on it, and where somebody slept for a fortnight travels in a plural list that
carries its own rung, its own tier and the ticket that resolves it.

NOTHING HERE IS A FINDING. Every person is graded `reconstructed`, carries the model row
and the seed that redraws them, and says in their own note what evidence retires them.
No Native or Metis person is written: T-1352 carries the Native-visitor row as a bracket
and not as people, stage `underdocumented` (T-1177) is the only stage that may mint one,
and this stage draws from the two eastern pools only — the crowd coming off the lake
vessels in June 1835 is the emigrant trade out of New England, New York and Ireland, and
the French colonial community of this country is the oldest RESIDENT community here
rather than a summer arrival.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESIDENTS = DATA / "residents"
HOUSEHOLDS = RESIDENTS / "households"
READMITTED = RESIDENTS / "readmitted"
MINTED_TRADES = RESIDENTS / "reconstructed_trades"
TRANSIENTS = RESIDENTS / "transients"

COHORT = DATA / "reconstruction" / "1835_transient_cohort.json"
CAMPS = DATA / "reconstruction" / "1835_camp_grounds.json"
LODGING = DATA / "reconstruction" / "1835_lodging_model.json"
COMPOSITION = DATA / "research" / "census_1840" / "composition_1840.json"
POOLS = DATA / "reconstruction" / "1835_invented_name_pools.json"
PROGRAMME = DATA / "reconstruction" / "1835_resident_reconstruction_programme.json"
LEDGER = DATA / "reconstruction" / "1835_transient_persons.json"

STAGE = "transients"
TICKET = "T-1353"
PARENT = "T-1178"
SCENE_DATE = "1835-07-01"
RECONSTRUCTED = "reconstructed"
PREFIX = "rc_"
SOURCE_PASS = "reconstructed_transient"
PRESENCE_KIND = "transient"

# The reading this stage spends, and the row of T-1352 it comes from.
POINT = 384
POINT_READING = "twice the 1843 rate"

# The land-sale purchasers the register names and the layer cannot place: the LOW end of
# T-1352's 77-109, because this stage reserves slots rather than claiming them.
RESERVED_NAMED_PURCHASERS = 77

# The 1840 size histogram is cut at eight, the same cut `modelled_families` and
# `women_and_children` make: the tail above it is boarding houses, hotels and crews.
KIN_MAX = 8

# The six bands the order book counts in, which is how a card prints an age.
BOOK_BANDS = (("under_10", 0, 10), ("10_19", 10, 20), ("20_29", 20, 30),
              ("30_39", 30, 40), ("40_49", 40, 50), ("50_plus", 50, None))
ADULT_BANDS = ("20_29", "30_39", "40_49", "50_plus")

# The two pools this stage draws from. `french_colonial` is deliberately not among them --
# see the module docstring.
POOLS_DRAWN = ("yankee", "irish")

# The sleeping-place classes, keyed off T-1352's own table rows in its printed order. The
# `place` strings below MUST match the committed model; --build reads the sentences from
# it and refuses if a row has moved, so this table can never quietly diverge from it.
ROOFED = "party"
OUT_OF_DOORS = "camp"
CLASSES = (
    ("a_room_in_a_public_house", "a room in a public house", ROOFED),
    ("the_floor_of_that_room", "the floor of that room", ROOFED),
    ("the_floor_of_a_private_house", "the floor of a private house", ROOFED),
    ("a_store_house_thrown_open", "a store house thrown open", ROOFED),
    ("the_open_sky_upon_the_wharves", "the open sky upon the wharves", OUT_OF_DOORS),
    ("a_tent_at_the_landing_place", "a tent at the landing place", OUT_OF_DOORS),
)
CAMP_GROUND = "the_landing_place"

# The keys this stage writes and --check re-derives. Everything else on a card belongs to
# another stage of the same programme and is that stage's to prove.
OWNED_KEYS = ("id", "name", "division", "head", "source_pass", "transient",
              "presence_kind", "lodged_at", "arrival", "lives_at", "works_at",
              "present_on_scene_date", "persons", "touches_removal", "review_required",
              "research_note")


# -------------------------------------------------------------------- the draw --

def draw(seed: str) -> int:
    return int.from_bytes(hashlib.blake2s(seed.encode("utf-8"), digest_size=8).digest(), "big")


def unit(seed: str) -> float:
    return draw(seed) / float(1 << 64)


def pick(seed: str, weighted: list):
    """The weighted choice a seed makes. `weighted` is [(item, weight), ...]."""
    total = float(sum(w for _, w in weighted))
    if total <= 0:
        raise SystemExit("a draw was asked to choose from nothing")
    at = unit(seed) * total
    run = 0.0
    for item, weight in weighted:
        run += float(weight)
        if at < run:
            return item
    return weighted[-1][0]


def step_past(seed: str, names: list, taken) -> str:
    """A name from the pool, stepping past one already spoken for. Deterministic."""
    start = draw(seed) % len(names)
    for offset in range(len(names)):
        candidate = names[(start + offset) % len(names)]
        if not taken(candidate):
            return candidate
    return names[start]


def slug(text: str) -> str:
    out = "".join(c.lower() if c.isalnum() else "_" for c in text)
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")


# ------------------------------------------------------------------ the inputs --

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cohort_tables() -> dict:
    """T-1352's model, with the two tables this stage reads pulled out by key."""
    doc = load(COHORT)
    out = {}
    for section in doc.get("sections", []):
        for key, table in (section.get("tables") or {}).items():
            out[key] = table
        for figure in section.get("figures", []):
            out.setdefault("figures", {})[figure["figure"]] = figure
    return out


def sleeping_rows(tables: dict) -> dict:
    """place -> the source and the sentence that establishes it. Refuses a moved row."""
    rows = {r["place"]: r for r in tables["where_they_slept"]["rows"]}
    missing = [place for _, place, _ in CLASSES if place not in rows]
    if missing:
        raise SystemExit(
            "TRANSIENTS REFUSED\n  - data/reconstruction/1835_transient_cohort.json no "
            "longer prints the sleeping-place class(es) this stage deals to: "
            f"{', '.join(missing)}. The quota is an equal deal over the classes THAT FILE "
            "names, so a class that has moved must move here too rather than be dealt to "
            "from memory.")
    return rows


def size_weights() -> list:
    """(size, households) from the 1840 Chicago schedule, cut at KIN_MAX.

    The only household-size distribution this corpus holds. A party travelling to a land
    sale is not a household, and the record says so; what the histogram supplies is the
    shape of how many people moved about together in this town, which is the nearest
    measured thing there is.
    """
    hist = load(COMPOSITION)["household_size"]["histogram"]
    return [(int(r["size"]), int(r["households"])) for r in hist
            if 1 <= int(r["size"]) <= KIN_MAX]


def pyramid() -> list:
    """((sex, band), persons) over the 1840 free-white age columns, folded to book bands."""
    edges = [(k, low, high) for k, low, high in BOOK_BANDS]
    counts: dict = {}
    for row in load(COMPOSITION)["age_bands"]["free_white"]:
        sex, low = row["sex"], int(row["low_edge"])
        band = next(k for k, lo, hi in edges if low >= lo and (hi is None or low < hi))
        counts[(sex, band)] = counts.get((sex, band), 0) + int(row["persons"])
    return sorted(counts.items())


def pools() -> dict:
    doc = load(POOLS)
    by_id = {c["id"]: c for c in doc["communities"]}
    missing = [p for p in POOLS_DRAWN if p not in by_id]
    if missing:
        raise SystemExit(f"TRANSIENTS REFUSED\n  - the name pools no longer carry "
                         f"{', '.join(missing)}")
    weights = (doc["trade_weights"]["_default"].get("weights") or {})
    return {"by_id": by_id,
            "weighted": [(by_id[p], int(weights.get(p, 1))) for p in POOLS_DRAWN]}


def names_already_borne() -> set:
    """Every name the layer carries, real or invented, folded for comparison."""
    out = set()
    for directory in (HOUSEHOLDS, READMITTED, MINTED_TRADES, TRANSIENTS):
        if not directory.exists():
            continue
        for path in sorted(directory.glob("hh_*.json")):
            for person in load(path).get("persons") or []:
                name = " ".join(str(person.get("name") or "").split()).lower()
                if name:
                    out.add(name)
    return out


def names_outside_this_stage() -> set:
    """The same, minus this stage's own cards: what a fresh draw must step past."""
    out = set()
    for directory in (HOUSEHOLDS, READMITTED, MINTED_TRADES):
        if not directory.exists():
            continue
        for path in sorted(directory.glob("hh_*.json")):
            for person in load(path).get("persons") or []:
                name = " ".join(str(person.get("name") or "").split()).lower()
                if name:
                    out.add(name)
    return out


def surname_for(seed: str, community: dict, people: list, taken: set,
                used: set) -> str:
    """A surname whose pool still has a free forename for everybody in this party.

    Every surname in both pools is already borne by a person this layer carries, so
    `step_past` over surnames alone would exhaust and hand back a name whose forenames are
    spoken for - which is how an invented person ends up wearing a real person's name. The
    step is made over a CAPACITY test instead: the surname must leave the community's male
    and female forename lists holding at least as many unspoken-for full names as this
    party has men and women. A surname this stage has already used is stepped past first,
    for variety; when every capable surname is already in use the deal takes the capable
    one it lands on rather than inventing a name outside the pools.
    """
    want_male = sum(1 for sex, _ in people if sex == "male")
    want_female = len(people) - want_male

    def capable(surname: str) -> bool:
        free = {"given_male": 0, "given_female": 0}
        for key in free:
            for given in community[key]:
                if f"{given} {surname}".lower() not in taken:
                    free[key] += 1
        return free["given_male"] >= want_male and free["given_female"] >= want_female

    names = community["surnames"]
    start = draw(seed) % len(names)
    fallback = None
    for offset in range(len(names)):
        candidate = names[(start + offset) % len(names)]
        if not capable(candidate):
            continue
        if candidate not in used:
            return candidate
        if fallback is None:
            fallback = candidate
    if fallback is not None:
        return fallback
    raise SystemExit(
        "TRANSIENTS REFUSED\n  - no surname in the "
        f"{community['label']} pool leaves a free forename for every member of a party of "
        f"{len(people)}. The pools are too small for the cohort this stage deals; widen "
        "data/reconstruction/1835_invented_name_pools.json rather than letting an invented "
        "person wear a real one's name.")


# ------------------------------------------------------------------- the quotas --

def quotas(minted: int) -> list:
    """The equal deal over the six classes, remainder to the first in printed order."""
    share, over = divmod(minted, len(CLASSES))
    return [share + (1 if i < over else 0) for i in range(len(CLASSES))]


def band_edges() -> dict:
    return {k: (low, None if high is None else high - 1) for k, low, high in BOOK_BANDS}


# ------------------------------------------------------------------- the records --

def band_block(band: str, seed: str, why: str) -> dict:
    low, high = band_edges()[band]
    return {
        "value": f"{low}-{high}" if high is not None else f"{low}+",
        "low": low,
        "high": high,
        "confidence": RECONSTRUCTED,
        "tier": RECONSTRUCTED,
        "basis": {
            "kind": "model",
            "id": "age_bands_1840",
            "note": f"Drawn from the 1840 Chicago schedule's free-white age columns, "
                    f"folded to the order book's six bands. {why}",
        },
        "seed": seed,
        "replaceable_by": {
            "kind": "person",
            "match": "a source that states this person's age or their birth year",
        },
        "note": "AN AGE BAND, NEVER A YEAR. This project writes no year it cannot read.",
    }


def person_record(pid: str, name: str, relationship: str, sex: str, band: str,
                  slot: str, community: dict, class_key: str, place: str,
                  kind: str) -> dict:
    where = ("in a camp at the landing place" if kind == OUT_OF_DOORS
             else "under a roof in the town")
    return {
        "id": pid,
        "name": name,
        "relationship": relationship,
        "grade": RECONSTRUCTED,
        "sex": sex,
        "age_band": band_block(
            band, f"{slot}:{relationship}:{pid}:age_band",
            "Nothing here is a reading of anybody's age."),
        "occupation": {
            "value": "none_recorded",
            "confidence": RECONSTRUCTED,
            "tier": "unknown",
            "note": "NO TRADE IS DRAWN FOR A VISITOR. The occupation model counts the "
                    "town's working people and this person is not one of them; a trade "
                    "written here would be spent out of a quota that belongs to the "
                    "residents.",
        },
        "name_basis": {
            "value": name,
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "model",
                "id": "1835_invented_name_pools",
                "note": f"Both parts are drawn from the {community['label']} pool, which "
                        f"is seeded from the attested residents of this town. The pool is "
                        f"chosen by the pools' own default weighting, restricted to the "
                        f"two eastern communities the emigrant trade of 1835 brought off "
                        f"the lake vessels.",
            },
            "seed": f"{slot}:{relationship}:{pid}:name",
            "replaceable_by": {
                "kind": "person",
                "match": "a source naming a real visitor of this town in the summer of 1835",
            },
            "note": "AN INVENTED NAME, AND IT IS NEVER EVIDENCE. No source names this "
                    "person. The name exists so a reader can tell one drawn visitor from "
                    "another, and it is checked against every name the layer already bears.",
        },
        "basis": {
            "kind": "model",
            "id": "1835_transient_cohort",
            "note": f"T-1352 bounds the strangers of 1 July 1835 at 192 to 900 and prints "
                    f"two candidate points; this stage spends {POINT}, the "
                    f"'{POINT_READING}' reading. This person is one of the {POINT} less the "
                    f"{RESERVED_NAMED_PURCHASERS} the land-sale register names, dealt to "
                    f"the sleeping-place class '{place}' and so sleeping {where}.",
        },
        "seed": f"{slot}:{relationship}:{pid}",
        "replaceable_by": {
            "kind": "person",
            "match": "a source naming a real member of the summer crowd of 1835, or a "
                     "re-reading of T-1352's bracket that no longer counts this person",
        },
        "reconstruction": {
            "stage": STAGE,
            "community": community["id"],
            "cohort_row": "immigrant families awaiting lots",
            "sleeping_class": class_key,
        },
        "note": "A VISITOR OF THE SEASON, NOT A RESIDENT. Counted apart from the town's "
                "own population, because the Chicago American counted them apart: it put "
                "the population at 2,500 to 3,000 and the strangers at 'some hundreds "
                "more'.",
    }


def lodged_at_row(kind: str, class_key: str, place: str, says: str, source: str) -> dict:
    """Where this household slept, at the rung the sources actually reach."""
    if kind == OUT_OF_DOORS:
        return {
            "kind": "camp",
            "place_id": CAMP_GROUND,
            "resolves_to": "camp_ground_candidate",
            "sleeping_class": class_key,
            "tier": RECONSTRUCTED,
            "confidence": "conjectural",
            "basis": {
                "kind": "source",
                "id": "1835_camp_grounds",
                "note": f"The one ground a committed source puts people on. {source}: "
                        f"“{says}”",
            },
            "replaceable_by": {
                "kind": "place",
                "match": "T-1214's placement of the camp grounds, which owns where a camp "
                         "stands and how large it is; this row names a CANDIDATE and never "
                         "a polygon",
            },
            "note": "A CANDIDATE, NOT A PLACEMENT. No coordinate is authored here and none "
                    "may be: docs/LIBERTIES.md refuses a fabricated location outright.",
        }
    return {
        "kind": "roofed_in_the_town",
        "place_id": class_key,
        "resolves_to": "sleeping_class",
        "sleeping_class": class_key,
        "tier": RECONSTRUCTED,
        "confidence": "conjectural",
        "basis": {
            "kind": "source",
            "id": "1835_transient_cohort",
            "note": f"The class, not the house. {source}: “{says}”",
        },
        "replaceable_by": {
            "kind": "place",
            "match": "T-1371 and T-1372, which deal the lodging model's surge beds to the "
                     "named and reconstructed lodging places; until they do, no inn is "
                     "named here, because a bed dealt twice is a bed invented once",
        },
        "note": "NO HOUSE IS NAMED. The lodging places' beds belong to the lodging model "
                "and are dealt by T-1371; this row reaches the rung the sources reach, "
                "which is the class of place and not the place.",
    }


def household_record(slot: str, hid: str, head_id: str, surname: str, persons: list,
                     kind: str, class_key: str, place: str, says: str, source: str,
                     quota: int, index: int) -> dict:
    lead = ("party" if kind == ROOFED else "camp")
    return {
        "id": hid,
        "name": f"The {surname} {lead} — a household of the summer's crowd",
        "division": "unplaced",
        "head": head_id,
        "source_pass": SOURCE_PASS,
        "transient": {
            "ticket": TICKET,
            "parent_ticket": PARENT,
            "stage": STAGE,
            "household_kind": kind,
            "cohort_row": "immigrant families awaiting lots",
            "sleeping_class": class_key,
            "sleeping_place": place,
            "slot": slot,
            "point_adopted": POINT,
            "point_reading": POINT_READING,
            "class_quota": quota,
            "ordinal_in_class": index,
            "stands_on": "T-1352 bounds the strangers of 1 July 1835 at 192 to 900 persons "
                         "and prints two candidate points without adopting one. This stage "
                         f"adopts {POINT} ('{POINT_READING}'), reserves "
                         f"{RESERVED_NAMED_PURCHASERS} slots for the land-sale purchasers "
                         "the register names, and deals the remainder equally across the "
                         "six sleeping-place classes the sources name and do not rank.",
            "withdrawn_if": "a source that ranks the sleeping-place classes, a re-reading "
                            "of T-1352's bracket that adopts the other candidate point, or "
                            "a source naming a real member of the crowd; the retirement "
                            "runs through --build, never by hand",
        },
        "presence_kind": {
            "value": PRESENCE_KIND,
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "rule",
                "id": "counted_apart_from_the_residents",
                "note": "Argued, not drawn. The Chicago American of 13 June 1835 puts the "
                        "strangers OUTSIDE its own population estimate, and Chicago's own "
                        "enumerator printed `Transient persons` as a row of its own in "
                        "1843. A transient is in the town on the day and is not a "
                        "resident; the town census reports the two apart for that reason.",
            },
            "replaceable_by": {
                "kind": "person",
                "match": "a source placing this household in the town before or after the "
                         "season, which would make them residents and not visitors",
            },
        },
        "lodged_at": [lodged_at_row(kind, class_key, place, says, source)],
        "arrival": {
            "value": None,
            "confidence": RECONSTRUCTED,
            "tier": "unknown",
            "note": "NOT DRAWN, AND NOT THE SAME QUESTION. The arrival model dates when a "
                    "household CAME TO STAY, and this one did not stay. The vessels landed "
                    "passengers on 28 and 29 June and on 2 and 3 July; which boat this "
                    "party came off is not recorded and is not derivable.",
            "seated_by": "nothing — a visitor of the season has no arrival year to fill",
        },
        "lives_at": {
            "value": None,
            "confidence": RECONSTRUCTED,
            "tier": "unknown",
            "note": "A VISITOR OF THE SEASON KEPT NO RESIDENCE. `lives_at` is the house a "
                    "household lived in and the town census counts a person as housed "
                    "through it; writing one here would move the resident count, which is "
                    "the one thing this cohort must not do. Where they slept is in "
                    "`lodged_at`, at the rung the sources reach.",
        },
        "works_at": {
            "value": None,
            "confidence": RECONSTRUCTED,
            "tier": "unknown",
            "note": "Not seated. No trade is drawn for a visitor, so there is no workplace "
                    "to name; the harbour-works gang, which would have had one, is refused "
                    "for want of a strength (see the ledger's refusals).",
        },
        "present_on_scene_date": {
            "value": "present",
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "rule",
                "id": "bounded_by_the_transient_cohort",
                "note": "Ordered, not argued: T-1352's bracket is a count of people IN the "
                        "town on 1 July 1835, so presence is the bound rather than a draw "
                        "made over it.",
            },
            "replaceable_by": {
                "kind": "person",
                "match": "a re-reading of T-1352's bracket that no longer counts this person",
            },
        },
        "persons": persons,
        "touches_removal": False,
        "review_required": False,
        "research_note": "RECONSTRUCTED VISITORS, NOT RESIDENTS. Nobody here is named by a "
                         "source. They are the summer crowd of 1835 the newspapers describe "
                         "and nobody counted, minted so the town's own population can be "
                         "read without them and the crowd can be read at all.",
    }


# --------------------------------------------------------------------- the plan --

def plan() -> dict:
    tables = cohort_tables()
    rows = sleeping_rows(tables)
    sizes = size_weights()
    bands = pyramid()
    pool = pools()
    taken = names_outside_this_stage()
    minted_total = POINT - RESERVED_NAMED_PURCHASERS
    shares = quotas(minted_total)

    households: list = []
    classes: list = []
    used_surnames: set = set()
    for (class_key, place, kind), quota in zip(CLASSES, shares):
        row = rows[place]
        says, source = row["says"], row["source"]
        seated, index = 0, 0
        while seated < quota:
            index += 1
            slot = f"{STAGE}:{class_key}:{index:03d}"
            size = pick(f"{slot}:party_size", sizes)
            size = min(size, quota - seated)
            community = pick(f"{slot}:name_pool_community", pool["weighted"])
            # Sex and band first, THEN the surname. Every surname in both pools is already
            # borne by somebody in this layer - the earlier stages have minted hundreds of
            # households - so a surname cannot be stepped past on its own account, and the
            # rule that matters is the one the programme actually states: no INVENTED FULL
            # NAME may be a name the layer already bears. Knowing how many men and how many
            # women this party holds is what lets the surname be chosen so that the pool
            # still offers a free forename for each of them.
            people = []
            for n in range(size):
                if n == 0:
                    # A party's head is an adult: the histogram counts people, not heads,
                    # and a child cannot be the one the record hangs on.
                    sex, band = pick(f"{slot}:head:sex_and_band",
                                     [(sb, c) for sb, c in bands if sb[1] in ADULT_BANDS])
                else:
                    sex, band = pick(f"{slot}:{n:02d}:sex_and_band", bands)
                people.append((sex, band))
            surname = surname_for(f"{slot}:surname", community, people, taken, used_surnames)
            used_surnames.add(surname)
            persons = []
            for n, (sex, band) in enumerate(people):
                relationship = "head" if n == 0 else "household_member"
                given_key = "given_male" if sex == "male" else "given_female"
                given = step_past(f"{slot}:{n:02d}:forename", community[given_key],
                                  lambda g, s=surname, t=taken: f"{g} {s}".lower() in t)
                name = f"{given} {surname}"
                taken.add(name.lower())
                pid = f"{PREFIX}{slug(surname)}_{slug(given)}"
                if n == 0:
                    head_id = pid
                persons.append(person_record(pid, name, relationship, sex, band, slot,
                                             community, class_key, place, kind))
            hid = f"hh_{head_id}"
            households.append({
                "slot": slot,
                "class_key": class_key,
                "kind": kind,
                "record": household_record(slot, hid, head_id, surname, persons, kind,
                                           class_key, place, says, source, quota, index),
            })
            seated += size
        classes.append({
            "key": class_key,
            "place": place,
            "household_kind": kind,
            "source": source,
            "says": says,
            "quota": quota,
            "households": index,
            "persons": seated,
            "lodged_at_rung": ("camp_ground_candidate" if kind == OUT_OF_DOORS
                               else "sleeping_class"),
        })

    ids = [h["record"]["id"] for h in households]
    if len(set(ids)) != len(ids):
        raise SystemExit("TRANSIENTS REFUSED\n  - the draw produced two households with the "
                         "same id; a surname pool has run short and the step-past rule "
                         "could not find a free name")
    return {"households": households, "classes": classes,
            "minted": minted_total, "shares": shares}


def ledger_document(p: dict) -> dict:
    built = {c["household_kind"]: 0 for c in p["classes"]}
    for c in p["classes"]:
        built[c["household_kind"]] += c["persons"]
    lodging = load(LODGING)["classes"]
    built_surge = sum(int(c["built_beds_crowded"]) - int(c["built_beds_ordinary"])
                      for c in lodging)
    return {
        "$schema_note": "DERIVED - regenerate with tools/reconstruct_transients_1835.py "
                        "--build; tools/check.sh re-derives it. Do not hand-edit: every "
                        "figure is a function of a committed file named in `inputs`.",
        "id": "chicago_july_1835_transient_persons",
        "ticket": TICKET,
        "parent": PARENT,
        "stage": STAGE,
        "target_date": SCENE_DATE,
        "generated_by": "tools/reconstruct_transients_1835.py --build",
        "spends": "data/reconstruction/1835_transient_cohort.json, which bounds the cohort "
                  "and adopts no point. This file adopts one and says which.",
        "inputs": [
            "data/reconstruction/1835_transient_cohort.json",
            "data/reconstruction/1835_camp_grounds.json",
            "data/reconstruction/1835_lodging_model.json",
            "data/reconstruction/1835_invented_name_pools.json",
            "data/research/census_1840/composition_1840.json",
        ],
        "the_point_adopted": {
            "persons": POINT,
            "reading": POINT_READING,
            "read_from": "data/reconstruction/1835_transient_cohort.json#size.tables."
                         "the_two_candidate_points",
            "why_this_one": "It stands on the only figure Chicago's own enumerator ever "
                            "printed for transients - 533 of them, a row of his own, in the "
                            "census of 1 August 1843 - doubled because 1 July 1835 was a "
                            "land-sale week and 1 August 1843 was not. The multiplier is "
                            "invented and T-1352 says so; the rate under it is measured. "
                            "The alternative, 550, is the midpoint of a newspaper's 'some "
                            "hundreds more', printed eighteen days before the scene and "
                            "before the sale crowd arrived, and offered as a phrase rather "
                            "than as a count.",
            "why_not_the_other": "A measured comparandum with one invented step is "
                                 "preferred to a rhetorical band read at its middle. Both "
                                 "sit inside T-1352's 192-900 bracket; this is the lower.",
        },
        "the_capacity_argument_this_file_refuses": {
            "built_surge_beds": built_surge,
            "programme_surge_beds": (int(load(LODGING)["reconciliation"]
                                         ["programme_total_crowded"])
                                     - int(load(LODGING)["reconciliation"]
                                           ["programme_total_ordinary"])),
            "persons_minted": p["minted"],
            "why_it_is_refused": "The BUILT lodging places carry a surge close to the "
                                 "minted cohort, which reads as a confirmation of the "
                                 "point adopted. It is not one. The town had 42 boarding "
                                 "houses and this reconstruction has built five; the "
                                 "programme's full surge is the figure above it, and the "
                                 "fit measures how far the structure band has got rather "
                                 "than anything the crowd did. Letting it choose a "
                                 "population would be reading this project's own "
                                 "incompleteness as evidence.",
        },
        "refusals": [
            {"row": "land-sale visitors and their agents",
             "slots_reserved": RESERVED_NAMED_PURCHASERS,
             "why": "The Public Domain register enters 232 purchases at Chicago on 26-27 "
                    "June 1835 from 105 distinct purchasers, of whom the resident "
                    "crosswalk can place only 28 in the town - a floor of 77 visitors the "
                    "register NAMES. A drawn person may never stand in for a person a "
                    "source names, so the slots are reserved and left empty.",
             "owed_to": "a reading of the tract-sales register against the resident layer"},
            {"row": "crews ashore",
             "slots_reserved": 0,
             "why": "T-1352 records 4 to 6 hulls lying at Chicago on the scene date and no "
                    "committed source in this corpus gives a crew complement for an 1830s "
                    "lake schooner. Without one a crew is a number invented whole, so the "
                    "hulls carry nobody. T-1372 has since SEATED those hulls — "
                    "data/reconstruction/1835_vessels_in_port.json names each one, her "
                    "master, her last port and her cargo, and moors her to the reach — and "
                    "left every one of them empty.",
             "owed_to": "a committed source that gives an 1830s Great Lakes schooner its "
                        "complement. The hulls are seated and the `lodged_at` rung of kind "
                        "`vessel` is gated and read; only the number is missing"},
            {"row": "the harbour-works gang",
             "slots_reserved": 0,
             "why": "The federal harbour improvement was at work through 1835 and no "
                    "committed source gives its strength in any month.",
             "owed_to": "T-1372, and a reading that gives the works a strength"},
            {"row": "travellers of business and of state",
             "slots_reserved": 0,
             "why": "The papers name these one at a time - the Democrat of 1 July 1835 has "
                    "Lewis Cass, Secretary of War, arrived on the 29th in the steamer "
                    "Michigan. A man a newspaper names is a reading waiting to be made, and "
                    "an invented traveller drawn beside him would bury him.",
             "owed_to": "a reading of the 1835 papers' visitor notices"},
        ],
        "the_liberty_this_stage_takes": {
            "what": "An EQUAL deal of the minted cohort across the six sleeping-place "
                    "classes T-1352 names, remainder to the first class in its printed "
                    "order.",
            "why": "No source in this corpus gives a share, and T-1352 ranks none of the "
                   "six. An equal deal is the only apportionment that adds no ranking the "
                   "record does not carry.",
            "retired_by": "a source that ranks the classes, or gives any one of them a count",
            "recorded_in": "docs/LIBERTIES.md",
        },
        "totals": {
            "point_adopted": POINT,
            "reserved_not_minted": RESERVED_NAMED_PURCHASERS,
            "persons_minted": p["minted"],
            "households_minted": len(p["households"]),
            "persons_by_household_kind": dict(sorted(built.items())),
            "households_by_household_kind": {
                kind: sum(1 for h in p["households"] if h["kind"] == kind)
                for kind in sorted({h["kind"] for h in p["households"]})},
            "resident_counts_this_file_moves": 0,
        },
        "classes": p["classes"],
        "minted": [{
            "id": h["record"]["id"],
            "file": f"transients/{h['record']['id']}.json",
            "household_kind": h["kind"],
            "sleeping_class": h["class_key"],
            "slot": h["slot"],
            "persons": len(h["record"]["persons"]),
        } for h in p["households"]],
    }


# --------------------------------------------------------------------- the modes --

def write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def build() -> int:
    p = plan()
    TRANSIENTS.mkdir(parents=True, exist_ok=True)
    keep = {h["record"]["id"] for h in p["households"]}
    for stale in sorted(TRANSIENTS.glob("hh_*.json")):
        if stale.stem not in keep:
            stale.unlink()
    for h in p["households"]:
        write_json(TRANSIENTS / f"{h['record']['id']}.json", h["record"])
    write_json(LEDGER, ledger_document(p))
    print(f"  wrote {p['minted']} reconstructed visitor(s) into "
          f"{len(p['households'])} household card(s), and the ledger")
    return 0


def check() -> int:
    p = plan()
    problems: list = []
    want = {h["record"]["id"]: h["record"] for h in p["households"]}
    have = {path.stem: load(path) for path in sorted(TRANSIENTS.glob("hh_*.json"))} \
        if TRANSIENTS.exists() else {}
    for hid in sorted(set(want) | set(have)):
        if hid not in have:
            problems.append(f"{hid}: the cohort deals this household and the layer does not "
                            f"carry it - re-run --stage {STAGE} --build")
        elif hid not in want:
            problems.append(f"{hid}: lives in data/residents/transients/ and no class of the "
                            f"cohort derives it")
        else:
            differing = sorted(k for k in OWNED_KEYS if have[hid].get(k) != want[hid].get(k))
            if differing:
                problems.append(f"{hid}: the committed record does not re-derive; "
                                f"{', '.join(differing)} differ(s)")
    ledger = json.dumps(ledger_document(p), indent=1, ensure_ascii=False) + "\n"
    if not LEDGER.exists():
        problems.append(f"{LEDGER.name} is missing")
    elif LEDGER.read_text(encoding="utf-8") != ledger:
        problems.append(f"{LEDGER.name} is not what the committed models re-derive")
    if problems:
        for problem in problems:
            print(f"  FAIL {problem}")
        return 1
    print(f"  ok    {p['minted']} visitor(s) in {len(p['households'])} household(s) "
          f"re-derive from T-1352's bracket, block for block")
    return 0


def report() -> int:
    p = plan()
    print(f"{TICKET} stage '{STAGE}' - the summer crowd of {SCENE_DATE}")
    print(f"  point adopted   {POINT} ({POINT_READING})")
    print(f"  reserved        {RESERVED_NAMED_PURCHASERS} for the purchasers the register names")
    print(f"  minted          {p['minted']} in {len(p['households'])} household(s)")
    for c in p["classes"]:
        print(f"    {c['key']:<32} {c['persons']:>4} in {c['households']:>3} "
              f"{c['household_kind']} household(s)")
    return 0


def self_test() -> int:
    """The rules, each broken on purpose."""
    cases = []

    def case(name, ok):
        cases.append((name, ok))

    share = quotas(307)
    case("the deal is equal and spends the whole cohort",
         sum(share) == 307 and max(share) - min(share) == 1 and share[0] == max(share))
    case("a cohort divisible by six deals evenly",
         quotas(306) == [51] * 6)
    case("the point adopted sits inside T-1352's bracket", 192 <= POINT <= 900)
    case("the reserved slots are the register's own floor and are not minted",
         POINT - RESERVED_NAMED_PURCHASERS == 307)

    # the sleeping classes must be the ones the committed model prints
    try:
        sleeping_rows(cohort_tables())
        case("every dealt class is a row of the committed cohort model", True)
    except SystemExit:
        case("every dealt class is a row of the committed cohort model", False)

    # a moved row must be refused rather than dealt to from memory
    moved = {"where_they_slept": {"rows": [{"place": "somewhere else", "source": "-",
                                            "says": "-"}]}}
    try:
        sleeping_rows(moved)
        case("a class the model no longer prints is refused", False)
    except SystemExit:
        case("a class the model no longer prints is refused", True)

    # no reviewed community may be drawn here
    case("the draw reaches only the two eastern pools",
         all(p not in ("french_colonial", "native", "metis") for p in POOLS_DRAWN))

    # the cards must not carry a residence
    p = plan()
    case("no minted household claims a residence",
         all(h["record"]["lives_at"]["value"] is None for h in p["households"]))
    case("every minted household is marked transient",
         all(h["record"]["presence_kind"]["value"] == PRESENCE_KIND
             for h in p["households"]))
    case("every minted household says where it slept",
         all(h["record"]["lodged_at"] and h["record"]["lodged_at"][0]["place_id"]
             for h in p["households"]))
    case("the camps name the one documented ground and nothing else",
         all(r["place_id"] == CAMP_GROUND
             for h in p["households"] if h["kind"] == OUT_OF_DOORS
             for r in h["record"]["lodged_at"]))
    case("no roofed party names a house",
         all(r["resolves_to"] == "sleeping_class"
             for h in p["households"] if h["kind"] == ROOFED
             for r in h["record"]["lodged_at"]))
    case("the draw is reproducible",
         [h["record"]["id"] for h in plan()["households"]]
         == [h["record"]["id"] for h in p["households"]])
    case("no invented name is a name the rest of the layer bears",
         not ({" ".join(str(person["name"]).split()).lower()
               for h in p["households"] for person in h["record"]["persons"]}
              & names_outside_this_stage()))
    case("every party's head is an adult",
         all(h["record"]["persons"][0]["age_band"]["low"] >= 20 for h in p["households"]))

    bad = 0
    for name, ok in cases:
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        bad += 0 if ok else 1
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return check()
    if args.report:
        return report()
    if args.build:
        return build()
    return report()


if __name__ == "__main__":
    raise SystemExit(main())
