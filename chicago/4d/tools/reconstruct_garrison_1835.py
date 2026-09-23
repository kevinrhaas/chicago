#!/usr/bin/env python3
"""T-1349, stage `garrison` — the companies of the 5th Infantry to their strength.

    python3 tools/reconstruct_garrison_1835.py --build      write the cards
    python3 tools/reconstruct_garrison_1835.py --check      re-derive and refuse drift
    python3 tools/reconstruct_garrison_1835.py --report     the return, and what it rests on
    python3 tools/reconstruct_garrison_1835.py --self-test  the rules, each refusing its own case

WHAT THIS STAGE IS. `data/reconstruction/1835_reconstruction_order_book.json` carries two
buckets it refuses to apportion — `persons/garrison/fort` and `households/garrison/fort` —
with the same basis on both: *"NOT APPORTIONED. The garrison of 1 July 1835 is a return to
be read."* The town model says it in its own voice too: *"The garrison of Fort Dearborn on
1 July 1835 is not modelled here. The fort's strength is a roster question owned by
T-1176."* This stage is the return. It reads the establishment from the statute that fixed
it, takes the company count from the only source this project holds, and writes the men.

WHAT IT READS, AND WHERE EVERY NUMBER COMES FROM.

  THE ESTABLISHMENT — `us_statutes_1821_army_peace_establishment`, § 2, verbatim:
  each infantry company "shall consist of one captain, one first lieutenant, one second
  lieutenant, three sergeants, four corporals, two musicians, and forty-two privates."
  Fifty-four all ranks, fifty-one of them enlisted. That Act was the law of the peace
  establishment on 1 July 1835 and this project reads no act between it and the scene date
  that moves an infantry company's strength.

  THE COMPANY COUNT — Andreas vol. 1, through `docs/RESEARCH/fort_dearborn.md`: two
  companies of U.S. infantry at the post in 1833, the post held continuously from June 1832
  to 29 December 1836, and NO strength figure for mid-1835 anywhere this project has
  reached. Two companies is therefore `reconstructed` and not a reading, and the record
  says so in those words.

  THE ENLISTMENT BAND — `us_army_general_regulations_1835`, Recruiting Service art. 19:
  "All free white male persons, above the age of 18, and under 35 years … may be enlisted.
  This regulation, so far as it respects the height and age of the recruit, shall not
  extend to musicians, or to those soldiers who may re-enlist into the service." So a
  private's age band is drawn uniform over 18-35 and banded; a sergeant is a re-enlisted man
  and draws past 35; a musician is exempt at the bottom and may be a boy.

  THE QUARTERING CHECK — the same Regulations, Quarter Master's Department art. 31: "To
  every six non-commissioned officers, musicians, privates, and servants, including the
  authorized number of washerwomen, two hundred and twenty-five square feet of room, at
  posts above the 38th degree of north latitude." Chicago is above it. Run against this
  project's own barracks footprint that allowance is an INDEPENDENT bound on the garrison,
  and `--report` prints it. It does not come out comfortable; § 4 of the memo says so.

WHAT IT REFUSES, each with a reason a reader can check:

  1. NO OFFICER IS INVENTED. The establishment gives each company a captain and two
     lieutenants — six commissioned officers across two companies — and this stage writes
     NONE of them. T-1348 ruled every officer this layer can name against the post, admitted
     one and refused eleven; minting six more under invented names would put commissioned
     officers of the United States Army into this town that no source has, in the one part of
     the layer where a reader is most likely to take a name for a finding. The establishment
     is printed; the officers are left as a stated gap.
  2. NO REVIEWED COMMUNITY. Art. 19 enlisted "free white male persons" and no others, so the
     rank and file may not be drawn from the Native, Métis or free Black pools — and the
     exclusion is the Army's, recorded here as a fact about the institution rather than
     passed over. AGENTS.md's Indigenous-history review confines those reconstructions to
     T-1177 in any case, and `reconstruct_residents_1835.py` asserts it from the other side.
  3. NO INVENTED NAME MAY BE A REAL PERSON'S. The draw steps past every name the attested
     and inferred layer already bears, and past every name this stage has already drawn.
  4. NO INVENTED SOLDIER MAY BEAR A NAMED RESIDENT'S FAMILY NAME. Stronger than 3, and this
     stage needs it where the civilian stages do not: a hundred men over a pool of
     thirty-six surnames puts three of each name into the town, and a research pass that
     RESOLVES a printed name against the resident layer then has three more candidates than
     it had. `mint_civic_residents.py` minted a 393rd civic person the first time this stage
     ran, because six invented Tuttles had made the town's one real Tuttle ambiguous. An
     invention that changes how a source is read has become evidence.
  4. NO NUMBER IS SETTLED THAT A SOURCE COULD SETTLE. The strength is the establishment, not
     a return; frontier companies stood below it and this project has no post return. The
     ledger carries that sentence and every person carries `replaceable_by` naming the
     muster roll that would retire them wholesale.

WHAT IT WRITES. Two company cards at `fort_dearborn_barracks`, one per company, holding the
enlisted men who were not married; eight married-soldier households, four to a company, each
holding a soldier, his wife at the laundress allowance, and the children the household model
draws; and one sutler at `fort_dearborn_sutlers_store`. Nothing else at the post moves:
`hh_greene_john` and `hh_maxwell_philip` are the layer's own and this stage does not touch
them.

THE DRAW IS REPRODUCIBLE OR IT IS NOTHING. Every value comes from `blake2s(seed)` over a
seed a reader can retype, and the seed is printed on the record that carries the value.
`--check` rebuilds every card this stage owns and refuses one differing byte.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
STRUCTURES = ROOT / "data" / "structures"
MODEL = ROOT / "data" / "reconstruction" / "1835_town_model.json"
COMPOSITION = ROOT / "data" / "research" / "census_1840" / "composition_1840.json"
POOLS = ROOT / "data" / "reconstruction" / "1835_invented_name_pools.json"
PROGRAMME = ROOT / "data" / "reconstruction" / "1835_resident_reconstruction_programme.json"
LEDGER = ROOT / "data" / "reconstruction" / "1835_garrison.json"

STAGE = "garrison"
TICKET = "T-1349"
RECIPE = "garrison_fill"
SCENE_DATE = "1835-07-01"
RECONSTRUCTED = "reconstructed"
PREFIX = "rc_"
SOURCE_PASS = "reconstructed_garrison"
DIVISION = "fort"

BARRACKS = "fort_dearborn_barracks"
SUTLERS_STORE = "fort_dearborn_sutlers_store"

ACT = "us_statutes_1821_army_peace_establishment"
REGS = "us_army_general_regulations_1835"

# § 2 of the Act of 2 March 1821, transcribed. The three commissioned ranks are carried so
# the establishment PRINTS complete; refusal 1 is what stops them being written.
ESTABLISHMENT = (
    ("captain", 1, "commissioned"),
    ("first_lieutenant", 1, "commissioned"),
    ("second_lieutenant", 1, "commissioned"),
    ("sergeant", 3, "enlisted"),
    ("corporal", 4, "enlisted"),
    ("musician", 2, "enlisted"),
    ("private", 42, "enlisted"),
)

COMPANIES = 2
LAUNDRESSES_PER_COMPANY = 4

# The order book's six bands.
BOOK_BANDS = (("under_10", 0, 10), ("10_19", 10, 20), ("20_29", 20, 30),
              ("30_39", 30, 40), ("40_49", 40, 50), ("50_plus", 50, None))
CHILD_BANDS = ("under_10", "10_19")
ADULT_BANDS = ("20_29", "30_39", "40_49", "50_plus")

# Art. 19's own limits, and the two exemptions it prints.
ENLIST_LOW, ENLIST_HIGH = 18, 35

# Art. 31's quartering allowance, and the latitude it is keyed to.
SQFT_PER_SIX = 225
SQFT_PER_M2 = 10.7639

# A soldier's family is drawn from the 1840 civilian size histogram cut here. The cut is a
# liberty and docs/LIBERTIES.md carries it: nothing this project holds counts the families
# of a frontier garrison, and a married soldier's quarters was one room.
FAMILY_SIZE_MIN, FAMILY_SIZE_MAX = 2, 6

# The keys this stage writes and `--check` re-derives. Everything else on a card belongs to
# another stage of the same programme and is that stage's to prove.
OWNED_KEYS = ("id", "name", "division", "head", "source_pass", "arrival",
              "party_size_on_arrival", "lives_at", "works_at",
              "present_on_scene_date", "garrison", "persons",
              "touches_removal", "review_required", "research_note")


# -------------------------------------------------------------------- the draw --

def seed_for(household_id: str, bucket: str) -> str:
    """The seed a reader can retype. The programme's `seed_rule`, exactly."""
    return f"{household_id}:{bucket}"


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


# ------------------------------------------------------------------ the inputs --

def cards() -> dict:
    return {path.stem: json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(HOUSEHOLDS.glob("hh_*.json"))}


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def value_of(block):
    return block.get("value") if isinstance(block, dict) else block


def table(section_key: str, table_key: str) -> dict:
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    for section in model["sections"]:
        if section["key"] == section_key:
            return section["tables"][table_key]
    raise SystemExit(f"the town model carries no {section_key}.{table_key}")


def size_rows() -> list:
    """The 1840 size histogram, cut to a soldier's quarters."""
    rows = table("households_and_families", "size_histogram_1840")["rows"]
    return [(int(r["size"]), int(r["households"])) for r in rows
            if FAMILY_SIZE_MIN <= int(r["size"]) <= FAMILY_SIZE_MAX]


def composition_rows() -> list:
    return json.loads(COMPOSITION.read_text(encoding="utf-8"))["age_bands"]["free_white"]


def printed_bands() -> dict:
    """(sex, low edge) -> the 1840 schedule's own printed column, so a record can cite it."""
    return {(r["sex"], int(r["low_edge"])): r["band"] for r in composition_rows()}


def band_edges() -> dict:
    return {label: (low, None if high is None else high - 1) for label, low, high in BOOK_BANDS}


def book_band(age_low: int) -> str:
    for label, low, high in BOOK_BANDS:
        if age_low >= low and (high is None or age_low < high):
            return label
    return "50_plus"


def composition_weights(sex: str, bands) -> list:
    """The 1840 schedule's own persons-counts, collapsed onto the book's bands."""
    want = set(bands)
    weights: Counter = Counter()
    for row in composition_rows():
        if row["sex"] != sex:
            continue
        band = book_band(int(row["low_edge"]))
        if band in want:
            weights[band] += int(row["persons"])
    return [(band, weights[band]) for band in bands if weights[band] > 0]


def printed_for(sex: str, band: str) -> str:
    """The schedule column a drawn band should cite: the lowest one inside the band."""
    low, _ = band_edges()[band]
    columns = printed_bands()
    for edge in sorted({int(r["low_edge"]) for r in composition_rows()}):
        if book_band(edge) == band and (sex, edge) in columns:
            return columns[(sex, edge)]
    return band


def pools() -> dict:
    return json.loads(POOLS.read_text(encoding="utf-8"))


def programme() -> dict:
    return json.loads(PROGRAMME.read_text(encoding="utf-8"))


def recipe() -> dict:
    return programme()[RECIPE]


def community_rows() -> list:
    return [(r["community"], int(r["weight"])) for r in recipe()["recruiting_communities"]["rows"]]


# ----------------------------------------------------------- the age of a soldier --

def enlistment_weights() -> list:
    """Uniform over art. 19's own 18-35, banded on the order book's cut.

    Not a model row and not pretending to be one: the regulation states who MAY be
    enlisted and says nothing about the shape of the ages inside that range, so the only
    honest draw is the flat one, and the weight of a band is the count of eligible years
    that fall in it.
    """
    weights = []
    for label, low, high in BOOK_BANDS:
        top = ENLIST_HIGH if high is None else min(high - 1, ENLIST_HIGH)
        years = top - max(low, ENLIST_LOW) + 1
        if years > 0:
            weights.append((label, years))
    return weights


def age_weights_for(rank: str) -> tuple:
    """(weighted bands, the sentence the record prints about why)."""
    if rank == "sergeant":
        return ([("20_29", 10), ("30_39", 10), ("40_49", 6)],
                "A sergeant is a soldier who re-enlisted, and art. 19 exempts a "
                "re-enlisting soldier from the age limit it sets on a recruit — so his band "
                "is drawn across the serving ages and not inside the recruiting window.")
    if rank == "musician":
        return ([("10_19", 6), ("20_29", 4)],
                "Art. 19's age limit 'shall not extend to musicians'. The regulation lifts "
                "the bottom of the window and states no other, so a musician is drawn young "
                "and the record claims nothing narrower than that.")
    return (enlistment_weights(),
            "Drawn uniform over art. 19's own recruiting window — above 18 and under 35 — "
            "and banded on the order book's cut. The regulation states who may be enlisted "
            "and nothing about the shape of the ages inside it, so a flat draw is the only "
            "one that adds no claim.")


# ---------------------------------------------------------------- naming a man --

def real_names(base: dict) -> set:
    """Every name anybody in this layer bears — read OR invented.

    Refusal 3 is usually stated against the attested and inferred layer, and that is the
    half that matters most: a reader who met a name as a finding and met it again as an
    invention would have been misled. But an invented name repeated is the same fault
    pointed at the reconstruction itself, so the fold takes `rc_` people too. That makes
    this stage's draw depend on the stages ABOVE it in the programme — `women_and_children`
    is the one that bites — which is why the build order matters and why the dossier writes
    it down.
    """
    taken = set()
    for card in base.values():
        for person in card.get("persons") or []:
            name = " ".join(str(person.get("name") or "").split()).lower()
            if name:
                taken.add(name)
    return taken


def borne_surnames(base: dict) -> set:
    """Every family name an ATTESTED or INFERRED person of this town bears.

    Refusal 4, and it is the one this stage learned the hard way. A hundred soldiers drawn
    over a pool of thirty-six surnames puts three men of each name into the town, and the
    research passes that RESOLVE a printed name against the resident layer then have three
    more candidates than they had — `tools/mint_civic_residents.py` minted a 393rd civic
    person the first time this stage ran, because six invented Tuttles had made the town's
    one real Tuttle ambiguous. An invention that changes how a source is READ has stopped
    being a reconstruction and become evidence, which is the one thing this project cannot
    let it be. So the draw takes only surnames NOBODY NAMED IN THIS TOWN BEARS.
    """
    out = set()
    for card in base.values():
        for person in card.get("persons") or []:
            if person.get("grade") not in ("attested", "inferred"):
                continue
            parts = str(person.get("name") or "").split()
            if parts:
                out.add(parts[-1].lower())
    return out


def free_surnames(community: dict, borne: set) -> list:
    names = [n for n in community["surnames"] if n.lower() not in borne]
    if not names:
        raise SystemExit(f"every surname in the {community['id']} pool is borne by a named "
                         f"resident; refusal 4 leaves this stage nothing to draw")
    return names


def step_past(seed: str, names: list, taken) -> str:
    """The pool entry the seed lands on, stepped forward until it is free."""
    if not names:
        raise SystemExit("a name pool is empty")
    start = draw(seed) % len(names)
    for offset in range(len(names)):
        candidate = names[(start + offset) % len(names)]
        if candidate not in taken:
            return candidate
    raise SystemExit(f"every name in a pool of {len(names)} is already borne")


def pool_of(pool_id: str, base_pools: dict) -> dict:
    for community in base_pools["communities"]:
        if community["id"] == pool_id:
            return community
    raise SystemExit(f"the name pools carry no community {pool_id!r}")


def slug(text: str) -> str:
    keep = [c.lower() if c.isalnum() else "_" for c in text]
    out = "".join(keep)
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")


def name_a_person(slot: str, sex: str, community: dict, taken_names: set,
                  taken_ids: set, borne: set) -> tuple:
    """(person id, full name, given seed, surname seed). Steps past every taken name."""
    key = "given_male" if sex == "male" else "given_female"
    surnames = free_surnames(community, borne)
    surname_seed = seed_for(slot, "surname")
    given_seed = seed_for(slot, "given_name")
    for bump in range(64):
        s_seed = surname_seed if bump == 0 else f"{surname_seed}#{bump}"
        g_seed = given_seed if bump == 0 else f"{given_seed}#{bump}"
        surname = step_past(s_seed, surnames, set())
        given = step_past(g_seed, community[key], set())
        name = f"{given} {surname}"
        pid = f"{PREFIX}{slug(surname)}_{slug(given)}"
        if name.lower() not in taken_names and pid not in taken_ids:
            taken_names.add(name.lower())
            taken_ids.add(pid)
            return pid, name, g_seed, s_seed
    raise SystemExit(f"could not name {slot} without colliding")


# ------------------------------------------------------------------ the records --

def band_block(band: str, seed: str, sex: str, why: str) -> dict:
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
            "note": f"Banded on the 1840 Chicago schedule's column '{printed_for(sex, band)}'. {why}",
        },
        "seed": seed,
        "replaceable_by": {
            "kind": "person",
            "match": "a muster roll, a descriptive book or an enlistment paper of the "
                     "Chicago post giving this soldier's age",
        },
        "note": "AN AGE BAND, NEVER A YEAR. The schedule counts in five- and ten-year "
                "columns and this project writes no year it cannot read, because a year "
                "drawn out of a decadal band would print as a record of a birth.",
    }


def name_basis(name: str, seed: str, community: dict, what: str) -> dict:
    return {
        "value": name,
        "confidence": RECONSTRUCTED,
        "tier": RECONSTRUCTED,
        "basis": {
            "kind": "model",
            "id": "1835_invented_name_pools",
            "note": f"Drawn from the {community['label']} pool. {what}",
        },
        "seed": seed,
        "replaceable_by": {
            "kind": "person",
            "match": "a muster roll or post return of Fort Dearborn naming the men of its "
                     "companies on or about 1 July 1835",
        },
        "note": "AN INVENTED NAME, AND IT IS NEVER EVIDENCE. It is drawn from a pool seeded "
                "from the attested residents of this town, and it steps past every name a "
                "real person in this layer bears. No source names this person. The Army kept "
                "muster rolls of exactly these men; this project has not read one.",
    }


def occupation_block(trade: str, why: str) -> dict:
    return {
        "value": trade,
        "confidence": RECONSTRUCTED,
        "tier": RECONSTRUCTED,
        "basis": {"kind": "rule", "id": f"{RECIPE}.establishment", "note": why},
        "replaceable_by": {
            "kind": "person",
            "match": "a muster roll or post return of the Chicago post naming this person "
                     "and what they did at it",
        },
        "note": "THE TRADE IS THE ESTABLISHMENT'S, not a reading about a man. The Act of 2 "
                "March 1821 fixes what a company of infantry consisted of; this person is "
                "one of those places, filled.",
    }


def soldier_person(pid: str, name: str, relationship: str, rank: str, slot: str,
                   band: str, band_seed: str, band_why: str, community: dict,
                   name_block: dict, company: int) -> dict:
    return {
        "id": pid,
        "name": name,
        "relationship": relationship,
        "grade": RECONSTRUCTED,
        "sex": "male",
        "age_band": band_block(band, band_seed, "male", band_why),
        "occupation": occupation_block(
            "soldier",
            f"A {rank.replace('_', ' ')} of the {ordinal(company)} company — one of the "
            f"{count_of(rank)} the Act of 2 March 1821 § 2 gives an infantry company."),
        "name_basis": name_block,
        "basis": {
            "kind": "rule",
            "id": f"{RECIPE}.establishment",
            "note": "THE ESTABLISHMENT, FILLED. The Act of 2 March 1821 § 2 fixes an "
                    "infantry company at three sergeants, four corporals, two musicians and "
                    "forty-two privates under three officers; Andreas puts two companies of "
                    "infantry at this post and the post was held on the scene date. This "
                    "person is one of those hundred and two enlisted places.",
        },
        "replaceable_by": {
            "kind": "person",
            "match": "a muster roll, post return or descriptive book of Fort Dearborn for "
                     "1835, which would retire every drawn soldier at once",
        },
        "reconstruction": {
            "programme": "1835_resident_reconstruction",
            "stage": STAGE,
            "ticket": TICKET,
            "community": community["id"],
            "company": company,
            "rank": rank,
            "review_required": False,
        },
        "note": "A SOLDIER OF THE GARRISON, DRAWN INTO A PLACE THE STATUTE FIXES. Nobody "
                "named him and nobody counted him: what is claimed is that the post was "
                "held on 1 July 1835 and that a held post of two companies had this many "
                "men in it at establishment. Frontier companies stood below establishment "
                "and this project has no return, so the number is a ceiling the ledger "
                "states rather than a strength anybody reported.",
    }


def ordinal(n: int) -> str:
    return {1: "first", 2: "second", 3: "third", 4: "fourth"}.get(n, f"{n}th")


def count_of(rank: str) -> str:
    for name, n, _ in ESTABLISHMENT:
        if name == rank:
            return {1: "one", 2: "two", 3: "three", 4: "four", 42: "forty-two"}.get(n, str(n))
    return "one"


def woman_person(pid: str, name: str, band: str, band_seed: str, community: dict,
                 name_block: dict, company: int) -> dict:
    return {
        "id": pid,
        "name": name,
        "relationship": "wife",
        "grade": RECONSTRUCTED,
        "sex": "female",
        "age_band": band_block(
            band, band_seed, "female",
            "Drawn on the 1840 Chicago schedule's own counts of free white women in each "
            "band. Nothing this project holds counts the women of a garrison, so the town's "
            "own pyramid is the nearest shape there is and the record says so."),
        "occupation": occupation_block(
            "laundress",
            "One of the washerwomen the Army allowed a company and paid out of the company "
            "fund. The 1835 General Regulations art. 30 has laundresses 'employed to wash "
            "soldier's clothing … paid according to a rate to be fixed by the council of "
            "administration', and arts. 27 and 31 settle their debts and quarter them "
            "alongside the men — so the allowance is in the regulations even though the "
            "NUMBER allowed is not printed in them. See the ledger's `laundresses` block."),
        "name_basis": name_block,
        "basis": {
            "kind": "rule",
            "id": f"{RECIPE}.laundresses",
            "note": "THE LAUNDRESS ALLOWANCE, FILLED. The Regulations quarter, pay and settle "
                    "the debts of the company's washerwomen without printing how many a "
                    "company was allowed; four a company is the figure this project's own "
                    "ticket states and it is carried as an instruction, not as a reading. "
                    "She is written into a married soldier's household of the same company, "
                    "because an unattached woman resident at a post is the stronger claim of "
                    "the two and no source supports either.",
        },
        "replaceable_by": {
            "kind": "person",
            "match": "a muster roll, post return or company book of the Chicago post naming "
                     "its laundresses",
        },
        "reconstruction": {
            "programme": "1835_resident_reconstruction",
            "stage": STAGE,
            "ticket": TICKET,
            "community": community["id"],
            "company": company,
            "review_required": False,
        },
        "note": f"A LAUNDRESS OF THE {ordinal(company).upper()} COMPANY, married into the "
                "household this card is headed by — `relationship` says where she stands "
                "inside it, and no source is being quoted about anybody. Nobody named her. "
                "What is claimed is that a held post of two companies had washerwomen at it, "
                "because its own regulations quarter them, pay them and rule on their "
                "accounts.",
    }


def child_person(pid: str, name: str, sex: str, band: str, band_seed: str,
                 community: dict, name_block: dict, size_seed: str, company: int) -> dict:
    return {
        "id": pid,
        "name": name,
        "relationship": "child",
        "grade": RECONSTRUCTED,
        "sex": sex,
        "age_band": band_block(
            band, band_seed, sex,
            "Drawn on the 1840 Chicago schedule's own counts in the child bands."),
        "occupation": {
            "value": "none_recorded",
            "confidence": RECONSTRUCTED,
            "note": "A child. No trade is claimed and none is drawn.",
        },
        "name_basis": name_block,
        "basis": {
            "kind": "model",
            "id": "household_size",
            "note": "Drawn from the 1840 schedule's household-size histogram, cut to the "
                    f"{FAMILY_SIZE_MIN}-{FAMILY_SIZE_MAX} range a married soldier's quarters "
                    "could hold. THE HISTOGRAM IS CIVILIAN. Nothing this project holds counts "
                    "the families of a frontier garrison, so a civilian town's own "
                    "distribution stands in for one, and docs/LIBERTIES.md carries that.",
        },
        "seed": size_seed,
        "replaceable_by": {
            "kind": "person",
            "match": "a post return, chaplain's register or company book naming the children "
                     "at the Chicago post",
        },
        "reconstruction": {
            "programme": "1835_resident_reconstruction",
            "stage": STAGE,
            "ticket": TICKET,
            "community": community["id"],
            "company": company,
            "review_required": False,
        },
        "note": "A SOLDIER'S CHILD. Drawn, not counted: the Army's returns counted women and "
                "children at a post and this project has read none of them.",
    }


def sutler_person(pid: str, name: str, band: str, band_seed: str, community: dict,
                  name_block: dict) -> dict:
    return {
        "id": pid,
        "name": name,
        "relationship": "head",
        "grade": RECONSTRUCTED,
        "sex": "male",
        "age_band": band_block(
            band, band_seed, "male",
            "Drawn on the 1840 Chicago schedule's own counts of free white men of trading "
            "age. No source gives this man's age because no source gives this man."),
        "occupation": occupation_block(
            "sutler",
            "The post trader. `fort_dearborn_sutlers_store` is an attested building of the "
            "fort with an attested function, and a sutler's store standing at a held post "
            "had a sutler in it."),
        "name_basis": name_block,
        "basis": {
            "kind": "rule",
            "id": f"{RECIPE}.sutler",
            "note": "A BUILDING WITH A FUNCTION, OCCUPIED. The sutler's store is `attested` "
                    "in this dataset on Andreas and Wentworth, the post was held on the "
                    "scene date, and the structure record states in its own words that who "
                    "held the sutlership at Chicago on 1835-07-01 was not established — "
                    "Andreas's sutler of about 1830 is five years early and a different "
                    "question, and is NOT reused here. One sutler is drawn; his household "
                    "is not, because nothing suggests its shape.",
        },
        "replaceable_by": {
            "kind": "person",
            "match": "a source naming the sutler of Fort Dearborn on or about 1 July 1835",
        },
        "reconstruction": {
            "programme": "1835_resident_reconstruction",
            "stage": STAGE,
            "ticket": TICKET,
            "community": community["id"],
            "review_required": False,
        },
        "note": "THE POST TRADER, DRAWN. A man stands here because a building of this "
                "function stood at a held post; his name is invented and his household is "
                "not claimed at all.",
    }


# ------------------------------------------------------------------- the cards --

def common_card(hid: str, name: str, head_id: str, lives_at: str, seated_why: str,
                present_why: str, seat_rule: str) -> OrderedDict:
    """Key order matters: `attribute_fill_arrival` seats `arrival_year` after `arrival`."""
    card = OrderedDict()
    card["id"] = hid
    card["name"] = name
    card["division"] = DIVISION
    card["head"] = head_id
    card["source_pass"] = SOURCE_PASS
    card["arrival"] = {
        "value": SCENE_DATE,
        "precision": "not_later_than",
        "confidence": RECONSTRUCTED,
        "note": "A BOUND THE HYPOTHESIS CARRIES, NOT A READING. No source names these "
                "people, so none dates their coming. What the record says is that the post "
                f"was held on {SCENE_DATE} — that is the whole of what this stage claims — "
                "and a soldier at a held post arrived not later than the day. A company of "
                "the 5th Infantry moved on orders and the year below is DRAWN by the "
                "programme's arrival stage, not read off a return.",
    }
    card["arrival_year"] = {"value": None, "confidence": RECONSTRUCTED,
                            "note": "Not attested."}
    card["party_size_on_arrival"] = {
        "value": None,
        "confidence": RECONSTRUCTED,
        "note": "Not claimed. The establishment says how many men a company held on the "
                "scene date and nothing about how they travelled to the post.",
    }
    card["origin"] = {"value": None, "confidence": RECONSTRUCTED, "note": "Not attested."}
    card["reason_for_coming"] = {"value": None, "confidence": RECONSTRUCTED,
                                 "note": "Not attested."}
    card["lives_at"] = {
        "value": lives_at,
        "confidence": RECONSTRUCTED,
        "tier": RECONSTRUCTED,
        "basis": {"kind": "rule", "id": seat_rule, "note": seated_why},
        "replaceable_by": {
            "kind": "household",
            "match": "a source placing these people at a named building of the post, or a "
                     "plan of the post that assigns its quarters",
        },
        "note": seated_why,
    }
    card["works_at"] = {
        "value": None,
        "confidence": RECONSTRUCTED,
        "note": "THE POST IS THE WORKPLACE AND THE POST IS THE DWELLING. A separate "
                "`works_at` would assert a second building for the same duty; the fort's "
                "own structures carry the garrison on their occupants blocks.",
    }
    card["present_on_scene_date"] = {
        "value": "present",
        "confidence": RECONSTRUCTED,
        "tier": RECONSTRUCTED,
        "basis": {"kind": "rule", "id": "the_post_was_held_on_the_scene_date",
                  "note": present_why},
        "replaceable_by": {
            "kind": "household",
            "match": "a post return or order showing the Chicago post unmanned on or about "
                     "1 July 1835",
        },
        "note": present_why,
    }
    return card


def company_card(company: int, head_id: str, members: list, drawn: int, married: list) -> dict:
    hid = f"hh_rc_garrison_company_{company}"
    card = common_card(
        hid,
        f"The {ordinal(company)} company of the 5th Infantry — the men in barracks",
        head_id,
        BARRACKS,
        "SEATED IN THE BUILDING THIS DATASET HOLDS FOR THEM. "
        "`fort_dearborn_barracks` carries an `attested` function of "
        "`enlisted_mens_barracks` and an occupants block reading 'enlisted men of the 5th "
        "Infantry garrison'. Which men is what this stage supplies; the building was "
        "already theirs. No coordinate is invented — the roof exists in the record.",
        "PRESENCE IS THE POST'S, NOT A FINDING ABOUT ANY MAN. "
        "docs/RESEARCH/fort_dearborn.md establishes that Fort Dearborn was held "
        "continuously from June 1832 to 29 December 1836, so it was held on the scene date "
        "and a held post has its companies in it.",
        "the_barracks_is_the_building_this_dataset_holds_for_them")
    card["garrison"] = {
        "stage": STAGE,
        "ticket": TICKET,
        "household_type": "garrison",
        "formation": "company",
        "company": company,
        "regiment": "5th Infantry",
        "establishment_enlisted": enlisted_per_company(),
        "in_barracks": len(members),
        "married_out_of_barracks": len(married),
        "married_households": married,
        "officers_not_written": commissioned_per_company(),
        "note": "A BARRACK ROOM IS NOT A FAMILY, and this card is not claiming it is. The "
                "resident layer's unit is the household and a company mess has no other "
                "shape to take here; `head` is the card's own grammar, filled with the "
                "company's senior sergeant because the format requires a person and the "
                "statute gives the company no other senior enlisted man. The three "
                "commissioned officers the establishment gives this company are NOT "
                "written — see the ledger's `officers` block and T-1348.",
    }
    card["persons"] = members
    card["touches_removal"] = False
    card["review_required"] = False
    card["research_note"] = (
        f"THE {ordinal(company).upper()} COMPANY OF THE 5TH INFANTRY, AT ESTABLISHMENT. "
        "NOBODY HERE IS NAMED BY ANY SOURCE. The Act of 2 March 1821 § 2 fixes an infantry "
        "company at one captain, one first lieutenant, one second lieutenant, three "
        "sergeants, four corporals, two musicians and forty-two privates; Andreas puts two "
        "companies of infantry at this post in 1833 and the post was held continuously to "
        "December 1836, but NO STRENGTH FIGURE FOR MID-1835 WAS REACHED. So the number is "
        "the establishment and not a return, which is a ceiling rather than a count — "
        "frontier companies stood below establishment as a matter of course. Ages are drawn "
        "inside the recruiting window the 1835 General Regulations art. 19 prints. Every "
        "name is invented and every value carries the seed that redraws it; a muster roll "
        "of this post for 1835 retires the whole card. No figure is drawn "
        "(docs/LIBERTIES.md L1)."
    )
    return card


def married_card(hid: str, company: int, soldier: dict, wife: dict, children: list,
                 size: int, size_seed: str) -> dict:
    card = common_card(
        hid,
        f"A married soldier's household of the {ordinal(company)} company — "
        f"{soldier['name']}, {wife['name']} and their children",
        soldier["id"],
        BARRACKS,
        "SEATED AT THE BARRACKS, AND THE RECORD SAYS WHY THAT IS THE WEAKEST LINE ON THIS "
        "CARD. The 1835 General Regulations quarter washerwomen inside the same allowance "
        "as the men (art. 31) but this project has no plan of married quarters at Chicago "
        "and the 1830 Harrison plan labels none. The barracks is where the dataset can put "
        "them without inventing a building; a hut outside the palisade, which is where "
        "married soldiers often were, would be a structure nobody drew.",
        "PRESENCE IS THE POST'S. The fort was held on the scene date; a held company had "
        "its washerwomen with it because its own regulations provided for them.",
        "no_married_quarters_are_drawn_so_the_barracks_carries_them")
    card["garrison"] = {
        "stage": STAGE,
        "ticket": TICKET,
        "household_type": "garrison",
        "formation": "married_soldier",
        "company": company,
        "regiment": "5th Infantry",
        "size_drawn": size,
        "seated": 1 + 1 + len(children),
        "seed": size_seed,
        "note": "One of the four washerwomen a company was allowed, written into a married "
                "soldier's household of that company, with the children the household model "
                "draws. The "
                "size is drawn from the 1840 civilian histogram cut to a married soldier's "
                "quarters; nothing this project holds counts a garrison's families.",
    }
    card["persons"] = [soldier, wife] + children
    card["touches_removal"] = False
    card["review_required"] = False
    card["research_note"] = (
        "A MARRIED SOLDIER'S HOUSEHOLD AT FORT DEARBORN. NOBODY HERE IS NAMED BY ANY SOURCE. "
        "The Army's own regulations quarter, pay and settle the accounts of the washerwomen "
        "of a company without printing how many a company was allowed; four a company is the "
        "figure this project states, carried as an instruction and graded reconstructed like "
        "everything else on this card. The woman is written as the soldier's wife because an "
        "unattached woman living at a post is the stronger of the two claims and no source "
        "supports either. A post return or a chaplain's register for the Chicago post "
        "retires the card whole. No figure is drawn (docs/LIBERTIES.md L1)."
    )
    return card


def sutler_card(person: dict) -> dict:
    hid = f"hh_{person['id']}"
    card = common_card(
        hid,
        f"The post sutler's household — {person['name']}",
        person["id"],
        SUTLERS_STORE,
        "SEATED IN THE BUILDING WHOSE FUNCTION HE IS. `fort_dearborn_sutlers_store` carries "
        "an `attested` function of `sutlers_store` on Andreas and Wentworth. A sutler at a "
        "post lived at his store; the building exists in the record and no coordinate is "
        "invented.",
        "PRESENCE IS THE POST'S AND THE BUILDING'S. The fort was held on the scene date and "
        "its sutler's store stood; the man in it is drawn, and the structure record already "
        "states that who held the sutlership in 1835 was not established.",
        "the_sutler_lived_at_the_sutlers_store")
    card["garrison"] = {
        "stage": STAGE,
        "ticket": TICKET,
        "household_type": "garrison",
        "formation": "sutler",
        "regiment": "5th Infantry",
        "seated": 1,
        "note": "One man, and no household drawn around him. Andreas's sutler of about 1830 "
                "is five years early and a different question; he is not reused.",
    }
    card["persons"] = [person]
    card["touches_removal"] = False
    card["review_required"] = False
    card["research_note"] = (
        "THE POST SUTLER. NOBODY HERE IS NAMED BY ANY SOURCE. `fort_dearborn_sutlers_store` "
        "is an attested building with an attested function and its own record says who held "
        "the sutlership at Chicago on 1835-07-01 was not established. This card fills the "
        "function and claims nothing else: no family, no partners, no stock. A source naming "
        "the sutler of 1835 retires it. No figure is drawn (docs/LIBERTIES.md L1)."
    )
    return card


def enlisted_per_company() -> int:
    return sum(n for _, n, kind in ESTABLISHMENT if kind == "enlisted")


def commissioned_per_company() -> int:
    return sum(n for _, n, kind in ESTABLISHMENT if kind == "commissioned")


# --------------------------------------------------------------------- the pass --

def ours(card: dict) -> bool:
    return card.get("source_pass") == SOURCE_PASS


def owned_view(card: dict) -> dict:
    return {k: card[k] for k in OWNED_KEYS if k in card}


def enlisted_roll() -> list:
    """The company's enlisted places, in the statute's own order."""
    roll = []
    for rank, n, kind in ESTABLISHMENT:
        if kind != "enlisted":
            continue
        for i in range(1, n + 1):
            roll.append((rank, i))
    return roll


def fill(base: dict) -> tuple:
    """Draw the whole garrison. Returns (cards by id, the ledger)."""
    pool_data = pools()
    comms = community_rows()
    taken_names = real_names(base)
    borne = borne_surnames(base)
    taken_ids = {p.get("id") for card in base.values() for p in (card.get("persons") or [])}
    sizes = size_rows()
    female_adult = composition_weights("female", ("20_29", "30_39", "40_49"))
    child_by_sex = {sex: composition_weights(sex, CHILD_BANDS) for sex in ("male", "female")}
    sex_at_birth = [("male", sum(w for _, w in child_by_sex["male"])),
                    ("female", sum(w for _, w in child_by_sex["female"]))]

    made: dict = {}
    ledger_companies = []
    for company in range(1, COMPANIES + 1):
        roll = enlisted_roll()
        # Which places are held by married men. Drawn once, on the company, so the roll and
        # the marriages do not move when either is re-read.
        eligible = [i for i, (rank, _) in enumerate(roll) if rank != "musician"]
        married_at = []
        for k in range(LAUNDRESSES_PER_COMPANY):
            seed = seed_for(f"garrison/company_{company}", f"laundress_{k + 1}")
            free = [i for i in eligible if i not in married_at]
            married_at.append(free[draw(seed) % len(free)])
        married_at = sorted(married_at)

        in_barracks, married_cards, married_ids = [], [], []
        for index, (rank, number) in enumerate(roll):
            slot = f"garrison/company_{company}/{rank}_{number}"
            community_id = pick(seed_for(slot, "recruiting_communities"), comms)
            community = pool_of(community_id, pool_data)
            pid, name, given_seed, _ = name_a_person(slot, "male", community,
                                                     taken_names, taken_ids, borne)
            bands, why = age_weights_for(rank)
            band_seed = seed_for(slot, "enlistment_band")
            band = pick(band_seed, bands)
            block = name_basis(name, given_seed, community,
                               "The Army recruited this town's own communities and the pools "
                               "carry two of the three the parent ticket names; no German "
                               "pool exists, and the ledger states that gap rather than "
                               "filling it from another.")
            person = soldier_person(pid, name,
                                    "head" if index in married_at else "household_member",
                                    rank, slot, band, band_seed, why, community, block,
                                    company)
            if index not in married_at:
                in_barracks.append(person)
                continue

            # A married man, his laundress wife and the children the model draws.
            hid = f"hh_{pid}"
            size_seed = seed_for(hid, "household_size")
            size = pick(size_seed, sizes)
            wife_slot = f"{slot}/wife"
            w_pid, w_name, w_given, _ = name_a_person(wife_slot, "female", community,
                                                      taken_names, taken_ids, borne)
            w_band = pick(seed_for(wife_slot, "age_bands_1840"), female_adult)
            wife = woman_person(w_pid, w_name, w_band,
                                seed_for(wife_slot, "age_bands_1840"), community,
                                name_basis(w_name, w_given, community,
                                           "A woman of this company's married quarters, "
                                           "drawn from the same pool as the head."),
                                company)
            children = []
            for c in range(1, max(0, size - 2) + 1):
                c_slot = f"{slot}/child_{c}"
                sex = pick(seed_for(c_slot, "sex_ratio"), sex_at_birth)
                c_pid, c_name, c_given, _ = name_a_person(c_slot, sex, community,
                                                          taken_names, taken_ids, borne)
                c_band = pick(seed_for(c_slot, "age_bands_1840"), child_by_sex[sex])
                children.append(child_person(
                    c_pid, c_name, sex, c_band, seed_for(c_slot, "age_bands_1840"),
                    community,
                    name_basis(c_name, c_given, community,
                               "A child of this household, drawn from its own pool."),
                    size_seed, company))
            made[hid] = married_card(hid, company, person, wife, children, size, size_seed)
            married_cards.append(hid)
            married_ids.append(pid)

        # THE SENIOR SERGEANT STILL IN BARRACKS CARRIES THE CARD'S `head`. A barrack room
        # has no head and the card says so in its own `garrison.note`; the resident layer's
        # format requires exactly one, and the statute gives a company no senior enlisted
        # man but its sergeants.
        head = next(p for p in in_barracks
                    if (p.get("reconstruction") or {}).get("rank") == "sergeant")
        head["relationship"] = "head"
        card = company_card(company, head["id"], in_barracks, len(roll), married_cards)
        made[card["id"]] = card
        ledger_companies.append({
            "company": company,
            "card": card["id"],
            "establishment_enlisted": enlisted_per_company(),
            "in_barracks": len(in_barracks),
            "married_households": married_cards,
            "officers_not_written": commissioned_per_company(),
        })

    # The sutler.
    s_slot = "garrison/sutler"
    s_community = pool_of(pick(seed_for(s_slot, "recruiting_communities"), comms), pool_data)
    s_pid, s_name, s_given, _ = name_a_person(s_slot, "male", s_community,
                                              taken_names, taken_ids, borne)
    s_band = pick(seed_for(s_slot, "age_bands_1840"),
                  composition_weights("male", ("20_29", "30_39", "40_49")))
    sutler = sutler_person(s_pid, s_name, s_band, seed_for(s_slot, "age_bands_1840"),
                           s_community,
                           name_basis(s_name, s_given, s_community,
                                      "A trader at a United States post; the pool is the "
                                      "town's own and the weighting is the stage's."))
    card = sutler_card(sutler)
    made[card["id"]] = card

    return made, ledger(made, ledger_companies, sutler)


# ------------------------------------------------------------------- the ledger --

def barracks_area_m2() -> float:
    """The east range's drawn footprint, from the structure record itself."""
    record = json.loads((STRUCTURES / f"{BARRACKS}.json").read_text(encoding="utf-8"))
    polygon = record["phases"][0]["footprint"]["polygon"]
    area = 0.0
    for i in range(len(polygon)):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % len(polygon)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def quartering_check(to_quarter: int) -> dict:
    """Art. 31 read against this project's own barracks. It does not come out comfortable."""
    area = barracks_area_m2()
    sqft = area * SQFT_PER_M2
    holds = int(sqft // SQFT_PER_SIX) * 6
    return {
        "allowance": f"{SQFT_PER_SIX} square feet to every six non-commissioned officers, "
                     "musicians, privates and servants, including the authorized number of "
                     "washerwomen, at posts above the 38th degree of north latitude",
        "source": REGS,
        "locator": "Quarter Master's Department, art. 31",
        "barracks": BARRACKS,
        "footprint_m2": round(area, 1),
        "footprint_sqft": round(sqft),
        "one_floor_quarters": holds,
        "to_quarter": to_quarter,
        "shortfall_on_one_floor": max(0, to_quarter - holds),
        "reading": "A CHECK THIS STAGE RUNS AND DOES NOT ACT ON. The barracks record argues "
                   "its own footprint partly from coherence — 'the largest building in the "
                   "complex, which is what a barracks for two companies of infantry should "
                   "be'. The Regulations' own allowance turns that argument into a number, "
                   "and on ONE floor the drawn range does not reach it. Three readings "
                   "survive and this stage picks none: the barracks had more than one floor "
                   "(the usual form, and the record asserts no storey count); or the "
                   "footprint is short, which the record already invites at plus or minus 20 "
                   "per cent; or the companies stood below establishment, which is the "
                   "likeliest thing of all and is exactly what the establishment ceiling "
                   "cannot see. Recorded for the ticket; nothing here is reduced to fit.",
    }


def ledger(made: dict, companies: list, sutler: dict) -> dict:
    people = [p for card in made.values() for p in card["persons"]]
    by_sex = Counter(p["sex"] for p in people)
    by_band = Counter(value_of(p["age_band"]) for p in people)
    by_trade = Counter(value_of(p["occupation"]) for p in people)
    # Art. 31 counts non-commissioned officers, musicians, privates and servants,
    # "including the authorized number of washerwomen" — the enlisted and the laundresses,
    # and nobody else. Children and the sutler are not in the allowance.
    to_quarter = sum(1 for p in people
                     if value_of(p["occupation"]) in ("soldier", "laundress"))
    return OrderedDict((
        ("_doc", "THE RETURN THE ORDER BOOK ASKED FOR. `persons/garrison/fort` and "
                 "`households/garrison/fort` carry no target because the fort's strength is "
                 "read and not apportioned; this file is what stage `garrison` returns, and "
                 "tools/reconstruct_garrison_1835.py --check re-derives every number in it. "
                 "IT IS AN ESTABLISHMENT AND NOT A RETURN OF PRESENT-FOR-DUTY. No muster "
                 "roll, post return or strength figure for Fort Dearborn in mid-1835 has "
                 "been reached by this project; frontier companies stood below establishment "
                 "as a matter of course, so every figure here is a CEILING."),
        ("id", "chicago_july_1835_garrison_return"),
        ("ticket", TICKET),
        ("parent", "T-1176"),
        ("target_date", SCENE_DATE),
        ("generated_by", "tools/reconstruct_garrison_1835.py --build"),
        ("checked_by", "tools/reconstruct_garrison_1835.py --check (wired in tools/check.sh)"),
        ("dossier", "docs/RESEARCH/fort_dearborn_garrison_strength_1835.md"),
        ("establishment", {
            "source": ACT,
            "locator": "§ 2",
            "quoted": "each of which shall consist of one captain, one first lieutenant, one "
                      "second lieutenant, three sergeants, four corporals, two musicians, and "
                      "forty-two privates",
            "per_company": [{"rank": r, "number": n, "kind": k} for r, n, k in ESTABLISHMENT],
            "per_company_all_ranks": sum(n for _, n, _ in ESTABLISHMENT),
            "per_company_enlisted": enlisted_per_company(),
            "note": "The law of the peace establishment on 1 July 1835. This project reads "
                    "no act between 2 March 1821 and the scene date that moves an infantry "
                    "company's strength; if one exists, it retires this block.",
        }),
        ("companies", {
            "number": COMPANIES,
            "regiment": "5th Infantry",
            "confidence": RECONSTRUCTED,
            "source": "andreas_1884_v1",
            "via": "docs/RESEARCH/fort_dearborn.md § 2",
            "note": "Andreas gives two companies of U.S. infantry at the post in 1833 and "
                    "nothing later; the post was held continuously from June 1832 to 29 "
                    "December 1836. TWO COMPANIES IN 1835 IS A CARRY-FORWARD OF A 1833 "
                    "READING, not a reading of the scene year, and is graded accordingly.",
        }),
        ("officers", {
            "at_establishment": COMPANIES * commissioned_per_company(),
            "written": 0,
            "named_at_the_post_by_the_layer": ["greene_john", "maxwell_philip",
                                               "allen_lieut_james"],
            "refusal": "NO OFFICER IS INVENTED. T-1348 ruled every officer this layer can "
                       "place at Chicago in the window against the post, admitted one and "
                       "refused eleven with the clause that refused each. Minting six "
                       "company officers under invented names would put commissioned "
                       "officers of the United States Army into this town that no source "
                       "has. The establishment is printed and the gap is stated.",
        }),
        ("laundresses", {
            "per_company": LAUNDRESSES_PER_COMPANY,
            "written": COMPANIES * LAUNDRESSES_PER_COMPANY,
            "confidence": RECONSTRUCTED,
            "source": REGS,
            "what_the_regulations_say": "The 1835 General Regulations quarter the "
                                        "washerwomen of a company inside the men's own "
                                        "allowance (art. 31), pay them at a rate the council "
                                        "of administration fixes (art. 30) and settle their "
                                        "accounts against the soldier's pay (arts. 27, 29) — "
                                        "and refer throughout to 'the authorized number of "
                                        "washerwomen' WITHOUT PRINTING IT.",
            "what_they_do_say_about_number": "Art. 82 quarters washerwomen for straw 'in the "
                                             "proportion of one to every seventeen persons', "
                                             "which over this establishment would give six "
                                             "rather than eight.",
            "note": "FOUR A COMPANY IS THE PROJECT'S OWN FIGURE, carried from this ticket's "
                    "instruction, and it is not the figure the one regulation that prints a "
                    "proportion would give. The divergence is stated rather than resolved "
                    "and docs/LIBERTIES.md carries it.",
        }),
        ("sutler", {
            "written": 1,
            "person": sutler["id"],
            "seated_at": SUTLERS_STORE,
            "note": "One man at an attested building with an attested function. No family, "
                    "no partners, no stock is claimed. Andreas's sutler of about 1830 is "
                    "five years early and is not reused.",
        }),
        ("written", {
            "households": len(made),
            "persons": len(people),
            "by_sex": dict(sorted(by_sex.items())),
            "by_age_band": dict(sorted(by_band.items())),
            "by_trade": dict(sorted(by_trade.items())),
            "companies": companies,
        }),
        ("the_strength_this_returns", {
            "enlisted_at_establishment": COMPANIES * enlisted_per_company(),
            "enlisted_written": sum(1 for p in people
                                    if value_of(p["occupation"]) == "soldier"),
            "laundresses": sum(1 for p in people
                               if value_of(p["occupation"]) == "laundress"),
            "children": sum(1 for p in people if p["relationship"] == "child"),
            "sutler": 1,
            "all_persons": len(people),
            "note": "The enlisted figure IS the establishment: no place is left empty and "
                    "none is added. Everything above it is drawn.",
        }),
        ("the_quartering_check", quartering_check(to_quarter)),
        ("what_retires_this_whole_file", "A muster roll, post return, descriptive book or "
                                          "monthly return of Fort Dearborn for 1835. The "
                                          "Army kept all four; this project has read none."),
    ))


# ------------------------------------------------------------------------ modes --

def build(write: bool) -> int:
    base = {k: v for k, v in cards().items() if not ours(v)}
    made, book = fill(base)
    changed = 0
    for hid, card in sorted(made.items()):
        path = HOUSEHOLDS / f"{hid}.json"
        existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        if existing is not None:
            # Keep every key another stage owns; rewrite only this stage's.
            merged = OrderedDict(existing)
            for key in OWNED_KEYS:
                if key in card:
                    merged[key] = card[key]
            card = merged
        if existing is None or dumps(existing) != dumps(card):
            changed += 1
            if write:
                path.write_text(dumps(card), encoding="utf-8")
    stale = [hid for hid, card in cards().items() if ours(card) and hid not in made]
    for hid in stale:
        changed += 1
        if write:
            (HOUSEHOLDS / f"{hid}.json").unlink()
    if write:
        LEDGER.write_text(dumps(book), encoding="utf-8")
    print(f"  built  {STAGE}: {len(made)} household(s), "
          f"{book['written']['persons']} person(s); {changed} file(s) rewritten"
          f"{'' if write else ' (dry run)'}")
    return 0


def check() -> int:
    live = cards()
    base = {k: v for k, v in live.items() if not ours(v)}
    made, book = fill(base)
    errors = []
    prog = programme()
    stage_keys = set(stages_of(prog))
    for hid, card in sorted(made.items()):
        path = HOUSEHOLDS / f"{hid}.json"
        if not path.exists():
            errors.append(f"{hid}: stage '{STAGE}' derives this household and it is not in "
                          f"the tree — run --build")
            continue
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        if dumps(owned_view(on_disk)) != dumps(owned_view(card)):
            errors.append(f"{hid}: the committed card no longer matches the draw. A draw "
                          f"that cannot be reproduced is not a reconstruction — run "
                          f"tools/reconstruct_garrison_1835.py --build")
    for hid, card in sorted(live.items()):
        if ours(card) and hid not in made:
            errors.append(f"{hid}: carries source_pass '{SOURCE_PASS}' and no draw produces "
                          f"it — a card no stage claims is a card the programme cannot "
                          f"re-derive")
    for hid, card in sorted(made.items()):
        for person in card["persons"]:
            check_person(f"{hid}:{person['id']}", person, stage_keys, errors.append)
    if LEDGER.exists():
        if dumps(json.loads(LEDGER.read_text(encoding="utf-8"))) != dumps(book):
            errors.append(f"{LEDGER.name}: the committed return no longer re-derives from "
                          f"the cards — run --build")
    else:
        errors.append(f"{LEDGER.name}: the return is missing — run --build")
    if errors:
        for line in errors:
            print(f"  FAIL  {line}")
        return 1
    print(f"  OK: stage '{STAGE}' re-derives {len(made)} household(s) and "
          f"{book['written']['persons']} person(s), and the return matches")
    return 0


def stages_of(prog: dict) -> list:
    return [s["key"] for s in prog["stages"]]


def check_person(where: str, person: dict, stage_keys, error) -> None:
    """The record contract, this stage's own copy — the same one the programme holds."""
    basis = person.get("basis")
    if not isinstance(basis, dict) or basis.get("kind") not in ("model", "rule"):
        error(f"{where}: a reconstructed person needs a basis of kind model or rule")
        return
    if not str(basis.get("note") or "").strip():
        error(f"{where}: basis.note must state why this person follows from that basis")
    seed = person.get("seed")
    if basis["kind"] == "model" and not str(seed or "").strip():
        error(f"{where}: a person drawn from a model needs the seed that redraws them")
    if basis["kind"] == "rule" and seed is not None:
        error(f"{where}: a person argued from a rule carries no seed; nothing was drawn")
    rep = person.get("replaceable_by")
    if not isinstance(rep, dict) or not str(rep.get("match") or "").strip():
        error(f"{where}: replaceable_by must say which evidence retires this person")
    rc = person.get("reconstruction") or {}
    if rc.get("stage") not in stage_keys:
        error(f"{where}: the person must name a programme stage, not {rc.get('stage')!r}")
    if not str((person.get("name_basis") or {}).get("value") or "").strip():
        error(f"{where}: an invented name carries a name_basis naming the pool it came from")


def report() -> int:
    base = {k: v for k, v in cards().items() if not ours(v)}
    made, book = fill(base)
    e = book["establishment"]
    print(f"THE GARRISON OF FORT DEARBORN, {SCENE_DATE} — an establishment, not a return\n")
    print(f"  the act        {e['source']} § 2: {e['per_company_all_ranks']} all ranks a "
          f"company, {e['per_company_enlisted']} of them enlisted")
    print(f"  the companies  {book['companies']['number']}, "
          f"{book['companies']['regiment']} ({book['companies']['confidence']}: a 1833 "
          f"reading carried forward)")
    print(f"  officers       {book['officers']['at_establishment']} at establishment, "
          f"{book['officers']['written']} written — no officer is invented")
    print(f"  enlisted       {book['the_strength_this_returns']['enlisted_written']} written, "
          f"at establishment")
    print(f"  laundresses    {book['the_strength_this_returns']['laundresses']}, "
          f"{LAUNDRESSES_PER_COMPANY} a company")
    print(f"  children       {book['the_strength_this_returns']['children']}, drawn")
    print(f"  sutler         1")
    print(f"  households     {book['written']['households']}   persons  "
          f"{book['written']['persons']}\n")
    q = book["the_quartering_check"]
    print(f"  THE QUARTERING CHECK (art. 31, {SQFT_PER_SIX} sq ft to every six)")
    print(f"    {q['barracks']}: {q['footprint_m2']} m2 = {q['footprint_sqft']} sq ft")
    print(f"    quarters {q['one_floor_quarters']} on one floor against "
          f"{q['to_quarter']} to quarter — short by {q['shortfall_on_one_floor']}")
    print()
    for row in book["written"]["companies"]:
        print(f"  company {row['company']}: {row['in_barracks']} in barracks, "
              f"{len(row['married_households'])} married households")
    return 0


def self_test() -> int:
    failures = []

    # The establishment is the statute's, and nothing may quietly round it.
    if enlisted_per_company() != 51 or commissioned_per_company() != 3:
        failures.append("the transcribed establishment no longer reads 3 officers and 51 "
                        "enlisted — check it against the Act of 2 March 1821 § 2")

    # The enlistment window is art. 19's, and a band outside it may not be drawn.
    bands = dict(enlistment_weights())
    if "under_10" in bands or "50_plus" in bands:
        failures.append("a private's band reaches outside art. 19's 18-35 window")
    if bands.get("20_29") != 10 or bands.get("30_39") != 6 or bands.get("10_19") != 2:
        failures.append("the flat draw over 18-35 no longer weights the bands by their own "
                        "eligible years")

    # A seed is a string a reader can retype, and it redraws the same value twice.
    s = seed_for("hh_rc_garrison_company_1", "household_size")
    if s != "hh_rc_garrison_company_1:household_size" or draw(s) != draw(s):
        failures.append("the seed rule is not the programme's, or a draw is not repeatable")
    if draw(s) == draw(seed_for("hh_rc_garrison_company_1", "sex_ratio")):
        failures.append("two buckets of one household draw the same value")

    # Refusal 1: no officer is written. The establishment's commissioned ranks may not
    # appear in the enlisted roll.
    if any(rank in ("captain", "first_lieutenant", "second_lieutenant")
           for rank, _ in enlisted_roll()):
        failures.append("an officer reached the enlisted roll — refusal 1 is not holding")

    # Refusal 2: the recruiting communities are the pools this stage may draw from, and a
    # reviewed community may not be among them.
    reviewed = {"native", "potawatomi", "metis", "métis", "indigenous", "french_colonial"}
    if any(c in reviewed for c, _ in community_rows()):
        failures.append("a reviewed community is in the recruiting draw — refusal 2 is not "
                        "holding; AGENTS.md confines those to T-1177")

    # Refusal 3: the draw steps past a taken name rather than writing it twice.
    if step_past("x", ["Adams", "Brown"], {"Adams", "Brown"} - {"Brown"}) != "Brown":
        failures.append("the name draw does not step past a name already borne")

    # Refusal 4: a surname a named resident bears is not in the draw at all.
    kept = free_surnames({"id": "t", "surnames": ["Tuttle", "Bacon"]}, {"tuttle"})
    if kept != ["Bacon"]:
        failures.append("refusal 4 is not holding: a surname borne by a named resident is "
                        "still in the soldiers' draw")
    try:
        free_surnames({"id": "t", "surnames": ["Tuttle"]}, {"tuttle"})
    except SystemExit:
        pass
    else:
        failures.append("refusal 4 does not refuse an exhausted pool; it would fall back to "
                        "a borne surname instead of stopping")

    # The quartering check has to be able to come out SHORT, or it is not a check.
    q = quartering_check(10_000)
    if q["shortfall_on_one_floor"] <= 0:
        failures.append("the quartering check cannot report a shortfall, so it is not "
                        "checking anything")
    if quartering_check(1)["shortfall_on_one_floor"] != 0:
        failures.append("the quartering check reports a shortfall where there is none")

    for line in failures:
        print(f"  FAIL  {line}")
    if failures:
        return 1
    print("  OK: the establishment, the enlistment window, the seed rule and all three "
          "refusals still fire when broken (four of them)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
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
    if args.build or args.dry_run:
        return build(write=not args.dry_run)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
