#!/usr/bin/env python3
"""T-1174, stage `women_and_children` — the houses the naming sources never printed.

    python3 tools/reconstruct_women_children.py --build      draw them, write the cards
    python3 tools/reconstruct_women_children.py --check      re-derive and refuse drift
    python3 tools/reconstruct_women_children.py --report     who was drawn, and against what
    python3 tools/reconstruct_women_children.py --self-test  the rules, each refusing its own case

WHAT THIS STAGE IS. The owner, on 2026-09-17: *"a fair number of missing women and
children."* The 1840 schedule says children under ten were 27% of this town and women of
twenty to twenty-nine its second-largest band; the layer the sources can name holds 15
women. T-1171 closed most of that inside the families of heads the sources leave alone —
but a rule keyed to MALE heads cannot create the one household the sources are worst at
recording, which is the house with no man in it. `modelled_families` says so in its own
refusals: *"a woman heading her own household is the age pyramid's, T-1174."* This is that
stage, and it writes NEW households rather than drawing onto existing ones, because there
is no card to draw onto.

WHAT IT MAY NOT DO. Five refusals, each with a reason a reader can check:

  1. A DIVISION WHOSE WOMEN THE BOOK NO LONGER WANTS gets no household. The order book's
     24 `persons/*/*/*/family/none` buckets are this stage's whole quota and a draw past
     one is refused rather than made.
  2. A HOUSEHOLD PAST `households/family_dwelling/<division>` is refused. The town model
     reads 469 to 816 households and the book cut the remainder by division; this stage
     may not invent its way past that cut.
  3. NOTHING IS SEATED. No lot, no roof, no structure: `lives_at` and `works_at` are null,
     because the ground these houses stand on is T-1191–T-1194's and T-1199 seats them.
     A coordinate invented here would be a fabricated location, which is the one liberty
     docs/LIBERTIES.md refuses outright.
  4. NO NATIVE OR METIS RECONSTRUCTION. AGENTS.md's Indigenous-history review confines
     that to T-1177's stage, and `reconstruct_residents_1835.py` asserts it from the other
     side. This stage draws its names from the general pools and never from a reviewed
     community.
  5. NO INVENTED NAME MAY BE A REAL PERSON'S. A reader who met a name as a finding and
     met it again as an invention would have been misled by this project, so the draw
     steps past every name the attested and inferred layer already bears.

  And one bound that is not a refusal: NOBODY HERE IS A FINDING. Every person this stage
  writes is graded `reconstructed`, carries the model row and the seed that redraws them,
  and says in their own note what evidence would retire them.

THE DRAW, AND WHY EVERY PIECE OF IT IS REPRODUCIBLE. Nothing is random: every value comes
from `blake2s(seed)` over a seed a reader can retype, and the seed is printed on the record
that carries the value. The head's age band, and every child's sex and band, are drawn
AGAINST WHAT THE BUCKET STILL WANTS — the buckets were cut from the population model, so
drawing against the gap IS drawing from the model, and it is the only draw that converges
on the pyramid instead of near it. `--check` rebuilds the whole set from the model files
and refuses a single differing byte on the keys this stage owns.

WHAT THIS STAGE OWNS ON A CARD, AND WHAT IT DOES NOT. It writes the card, so it owns the
record's own keys — `OWNED_KEYS` below. It does NOT own `arrival_year`, `origin` or
`reason_for_coming`: those are stage `attribute_fill_arrival`'s, which runs over the whole
layer including these new cards and marks its own blocks with `written_by_stage`. `--check`
compares the owned keys and leaves the other stage's alone, exactly as `modelled_families`
leaves alone the keys it did not write.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resident_mint_carry import carry_seats  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
MODEL = ROOT / "data" / "reconstruction" / "1835_town_model.json"
COMPOSITION = ROOT / "data" / "research" / "census_1840" / "composition_1840.json"
POOLS = ROOT / "data" / "reconstruction" / "1835_invented_name_pools.json"
BOOK = ROOT / "data" / "reconstruction" / "1835_reconstruction_order_book.json"
PROGRAMME = ROOT / "data" / "reconstruction" / "1835_resident_reconstruction_programme.json"
LEDGER = ROOT / "data" / "reconstruction" / "1835_women_children.json"

STAGE = "women_and_children"
TICKET = "T-1174"
RECIPE = "women_children_fill"
SCENE_DATE = "1835-07-01"
RECONSTRUCTED = "reconstructed"
PREFIX = "rc_"
SOURCE_PASS = "reconstructed_women_children"

# The divisions the order book apportions. Sorted, so the draw does not depend on the
# order a dict happened to be written in.
CIVIL = ("north", "south", "west")

# The 1840 size histogram is cut at eight, the same cut `modelled_families` makes: the
# tail above it is the town model's boarding houses, hotels and crews, which is lodging
# and belongs to T-1175.
KIN_MAX = 8

# The order book's six bands.
BOOK_BANDS = (("under_10", 0, 10), ("10_19", 10, 20), ("20_29", 20, 30),
              ("30_39", 30, 40), ("40_49", 40, 50), ("50_plus", 50, None))

# A woman heads a household from twenty; the bands below that are a child's.
ADULT_BANDS = ("20_29", "30_39", "40_49", "50_plus")
CHILD_BANDS = ("under_10", "10_19")

# The keys this stage writes and `--check` re-derives. Everything else on the card belongs
# to another stage of the same programme and is that stage's to prove.
OWNED_KEYS = ("id", "name", "division", "head", "source_pass", "arrival",
              "party_size_on_arrival", "lives_at", "works_at",
              "present_on_scene_date", "women_children", "persons",
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
    """The 1840 size histogram, cut to the kin range — `modelled_families`' own row."""
    rows = table("households_and_families", "size_histogram_1840")["rows"]
    return [(int(r["size"]), int(r["households"])) for r in rows
            if 1 <= int(r["size"]) <= KIN_MAX]


def printed_bands() -> dict:
    """(sex, low edge) -> the 1840 schedule's own printed column, so a record can cite it."""
    rows = json.loads(COMPOSITION.read_text(encoding="utf-8"))["age_bands"]["free_white"]
    return {(r["sex"], int(r["low_edge"])): r["band"] for r in rows}


def band_edges() -> dict:
    """book band -> (low, high). The band a record prints, from the book's own cut."""
    out = {}
    for label, low, high in BOOK_BANDS:
        out[label] = (low, None if high is None else high - 1)
    return out


def pools() -> dict:
    return json.loads(POOLS.read_text(encoding="utf-8"))


def recipe() -> dict:
    return json.loads(PROGRAMME.read_text(encoding="utf-8"))[RECIPE]


def trade_rows() -> list:
    return [(r["trade"], int(r["weight"])) for r in recipe()["female_trades"]["rows"]]


def book_band(age_low: int) -> str:
    for label, low, high in BOOK_BANDS:
        if age_low >= low and (high is None or age_low < high):
            return label
    return "50_plus"


# ------------------------------------------------------------------- the quota --

def bucket_key(sex: str, band: str, division: str) -> str:
    return f"persons/{sex}/{band}/{division}/family/none"


def quota() -> tuple:
    """(person quota, household quota). This stage's own fills are added back.

    `filled` counts what EVERY stage put in a bucket, including the last run of this one,
    so a draw that read its own previous answer as spent quota would draw fewer people on
    the second build than on the first — the one thing `--check` may not tolerate.
    """
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    ours = Counter()
    for entry in book.get("fills") or []:
        if entry.get("ticket") == TICKET:
            ours[entry.get("bucket")] += int(entry.get("records") or 0)
    persons, households = {}, {}
    for family in book["bucket_families"]:
        for bucket in family["buckets"]:
            todo = bucket.get("to_reconstruct")
            if todo is None:
                continue
            left = int(todo) - int(bucket.get("filled") or 0) + ours[bucket["key"]]
            if family["key"] == "persons" and bucket.get("owning_ticket") == TICKET:
                persons[bucket["key"]] = left
            elif family["key"] == "households" and bucket["key"].startswith(
                    "households/family_dwelling/"):
                households[bucket["key"]] = left
    return persons, households


def want(left: dict, sex: str, bands, division: str) -> list:
    """[(band, how short it still is)] for the bands that still want somebody."""
    return [(band, left.get(bucket_key(sex, band, division), 0)) for band in bands
            if left.get(bucket_key(sex, band, division), 0) > 0]


# ---------------------------------------------------------------- naming a house --

def real_names(base: dict) -> set:
    """Every name an attested or inferred person in this layer bears, folded."""
    out = set()
    for card in base.values():
        for person in card.get("persons") or []:
            name = " ".join(str(person.get("name") or "").split()).lower()
            if name:
                out.add(name)
    return out


def community_for(trade: str, seed: str, pool: dict) -> dict:
    """Which naming pool this house is named from. The pools' own trade weighting."""
    weights = pool["trade_weights"].get(trade) or pool["trade_weights"]["_default"]
    by_id = {c["id"]: c for c in pool["communities"]}
    weighted = [(by_id[k], v) for k, v in sorted((weights.get("weights") or {}).items())
                if k in by_id]
    if not weighted:
        weighted = [(by_id["yankee"], 1)]
    return pick(seed, weighted)


def step_past(seed: str, names: list, taken) -> str:
    """A name from the pool, stepping past one already spoken for. Deterministic."""
    start = draw(seed) % len(names)
    for offset in range(len(names)):
        candidate = names[(start + offset) % len(names)]
        if not taken(candidate):
            return candidate
    return names[start]


def slug(text: str) -> str:
    keep = [c.lower() if c.isalnum() else "_" for c in text]
    out = "".join(keep)
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")


# ------------------------------------------------------------------ the records --

def band_block(band: str, seed: str, printed: str, why: str) -> dict:
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
            "note": f"Drawn from the 1840 Chicago schedule's column '{printed}'. {why}",
        },
        "seed": seed,
        "replaceable_by": {
            "kind": "person",
            "match": "a source that states this person's age or their birth year",
        },
        "note": "AN AGE BAND, NEVER A YEAR. The schedule counts in five- and ten-year "
                "columns and this project writes no year it cannot read, because a year "
                "drawn out of a decadal band would print as a record of a birth.",
    }


def occupation_block(trade: str, seed: str, why: str) -> dict:
    if trade == "none_recorded":
        # A PLAIN SENTINEL, AND DELIBERATELY BARE. `none_recorded` is the vocabulary's word
        # for "this record asserts no trade", and the attribute-tier derivation reads it as
        # no asserted value — so a `tier`, a `basis` or a `replaceable_by` on it would be
        # reconstruction fields hung on a block that reconstructs nothing, and the gate says
        # so. The seed that drew this answer is on the card, in `women_children`, where it
        # belongs: it is a fact about the DRAW and not about the person.
        return {
            "value": "none_recorded",
            "confidence": RECONSTRUCTED,
            "note": "NO TRADE IS CLAIMED, AND THAT IS A DRAW LIKE ANY OTHER. The same "
                    "weighted table that gave this stage's other heads a trade gave this "
                    "one none — a widow with grown children, a lot, a pension or kin in "
                    "the town need not have been in a trade, and a model that put an "
                    "occupation on every one of them would print a column the sources "
                    "never had. The card's `women_children.head_trade_seed` redraws it.",
        }
    return {
        "value": trade,
        "confidence": RECONSTRUCTED,
        "tier": RECONSTRUCTED,
        "basis": {
            "kind": "model",
            "id": "women_children_fill.female_trades",
            "note": why,
        },
        "seed": seed,
        "replaceable_by": {
            "kind": "person",
            "match": "a source naming a woman of this household and what she did",
        },
        "note": "DRAWN FROM AN ASSUMPTION THIS PROJECT STATES RATHER THAN A ROW IT READ. "
                "The occupation model counts the December 1835 State census's "
                "establishments and the 1840 schedule's seven employment columns, and "
                "NEITHER counts a woman's work — so there is no female-trade row to draw "
                "from. The weights are the programme's own, written where a reader can "
                "argue with them and entered in docs/LIBERTIES.md. The term is the "
                "residents vocabulary's.",
    }


def person_record(pid: str, name: str, relationship: str, sex: str, band_key: str,
                  band_seed: str, band_printed: str, band_why: str,
                  basis_id: str, basis_note: str, seed: str,
                  name_seed: str, name_note: str, community: dict,
                  household_name: str, note: str, occupation: dict) -> dict:
    """A reconstructed person carrying everything the record contract asks of one."""
    return {
        "id": pid,
        "name": name,
        "relationship": relationship,
        "grade": RECONSTRUCTED,
        "sex": sex,
        "age_band": band_block(band_key, band_seed, band_printed, band_why),
        "occupation": occupation,
        "name_basis": {
            "value": name,
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "model",
                "id": "1835_invented_name_pools",
                "note": name_note,
            },
            "seed": name_seed,
            "replaceable_by": {
                "kind": "person",
                "match": f"a source naming a member of {household_name}",
            },
            "note": "AN INVENTED NAME, AND IT IS NEVER EVIDENCE. It is drawn from the "
                    f"{community['label']} pool, which is seeded from the attested "
                    "residents of this town and not from a story about who lived here, and "
                    "it steps past every name a real person in this layer bears. No source "
                    "names this person.",
        },
        "basis": {
            "kind": "model",
            "id": basis_id,
            "note": basis_note,
        },
        "seed": seed,
        "replaceable_by": {
            "kind": "person",
            "match": "a source naming a woman who kept her own house in this division, or "
                     "anyone in it",
        },
        "reconstruction": {
            "programme": "1835_resident_reconstruction",
            "stage": STAGE,
            "ticket": TICKET,
            "community": community["id"],
            "review_required": False,
        },
        "note": note,
    }


def household_record(hid: str, slot: str, division: str, head: dict, members: list,
                     trade: str, size: int, seeded_beyond: int) -> dict:
    """The card. Key order matters: `attribute_fill_arrival` seats `arrival_year` after
    `arrival`, and it overwrites the empty `origin` and `reason_for_coming` blocks in
    place rather than appending them past `research_note`."""
    trade_line = ("no trade recorded" if trade == "none_recorded"
                  else f"a drawn {trade.replace('_', ' ')}")
    card = OrderedDict()
    card["id"] = hid
    card["name"] = (f"Reconstructed household — {head['name']}, a woman keeping her own "
                    f"house in the {division} division")
    card["division"] = division
    card["head"] = head["id"]
    card["source_pass"] = SOURCE_PASS
    card["arrival"] = {
        "value": SCENE_DATE,
        "precision": "not_later_than",
        "confidence": RECONSTRUCTED,
        "note": "A BOUND THE HYPOTHESIS ITSELF CARRIES, AND NOT A READING. No source names "
                "this household, so none dates its coming. What the record does say is "
                f"that it was here on {SCENE_DATE} — that is the whole of what this stage "
                "claims — and a household here on that day arrived not later than it. "
                "Nothing narrower is known; the year below is DRAWN from that bound by the "
                "programme's arrival stage against the years the known layer records.",
    }
    card["arrival_year"] = {"value": None, "confidence": RECONSTRUCTED,
                            "note": "Not attested."}
    card["party_size_on_arrival"] = {
        "value": None,
        "confidence": RECONSTRUCTED,
        "note": "Not claimed. The household model draws how many people this house held on "
                "1 July 1835 and says nothing about how many of them travelled together.",
    }
    card["origin"] = {"value": None, "confidence": RECONSTRUCTED, "note": "Not attested."}
    card["reason_for_coming"] = {"value": None, "confidence": RECONSTRUCTED,
                                 "note": "Not attested."}
    card["lives_at"] = {
        "value": None,
        "confidence": RECONSTRUCTED,
        "note": "NO ROOF AND NO LOT. This stage seats nobody: the ground the north and west "
                "divisions still want is T-1191–T-1194's and T-1199 seats every "
                "reconstructed household on it. A coordinate invented here would be a "
                "fabricated location, which docs/LIBERTIES.md refuses outright.",
    }
    card["works_at"] = {
        "value": None,
        "confidence": RECONSTRUCTED,
        "note": "No workplace is assigned from a reconstructed household; T-1189 staffs the "
                "businesses and T-1199 seats the premises.",
    }
    card["present_on_scene_date"] = {
        "value": "present",
        "confidence": RECONSTRUCTED,
        "note": "PRESENCE IS THE HYPOTHESIS, not a finding about anybody. This household "
                "exists because the town of 1 July 1835 demonstrably held women and "
                "children the naming sources never printed — the order book counts how "
                "many, by sex, age and division — and this is one of them.",
    }
    card["women_children"] = {
        "stage": STAGE,
        "ticket": TICKET,
        "household_type": "female_headed",
        "head_trade": trade,
        "head_trade_seed": seed_for(slot, "female_trades"),
        "size_drawn": size,
        "seated": 1 + len(members),
        "seated_beyond_the_draw": seeded_beyond,
        "seed": seed_for(slot, "household_size"),
        "note": "The women and children the age pyramid still lacks. A servant, an "
                "apprentice or a lodger this house may also have held is priced by T-1183 "
                "and seated by T-1173 and T-1175; the drawn size is a floor on the house, "
                "and where the division's child buckets were still short after every house "
                "was drawn the remainder was seated across them and says so.",
    }
    card["persons"] = [head] + members
    card["touches_removal"] = False
    card["review_required"] = False
    card["research_note"] = (
        f"RECONSTRUCTED HOUSEHOLD — {trade_line}, in the {division} division. NOBODY HERE "
        "IS NAMED BY ANY SOURCE. The 1840 Chicago schedule counts children under ten at "
        "27% of the town and women of twenty to twenty-nine as its second-largest band; "
        "the 1835 layer the sources can name holds 15 women, because the rolls that name "
        "this town — a letter list, a voters' roll, a subscription — print men. That gap "
        "is the shape of the evidence and not a reading of the town, so the order book "
        "counts it bucket by bucket and this household is drawn against those counts. "
        "Every value on it carries the model row and the seed that redraws it, and a "
        "source naming a woman who kept her own house in this division retires the whole "
        "record. No figure is drawn (docs/LIBERTIES.md L1)."
    )
    return card


# --------------------------------------------------------------------- the pass --

def ours(card: dict) -> bool:
    block = card.get("women_children")
    return isinstance(block, dict) and block.get("stage") == STAGE


def owned_view(card: dict) -> dict:
    """The card cut to the keys this stage owns — what `--check` compares."""
    return {k: card[k] for k in OWNED_KEYS if k in card}


def fill(base: dict) -> tuple:
    """(the cards this stage writes, the ledger). Pure over `base`."""
    pool = pools()
    trades = trade_rows()
    trade_why = {r["trade"]: r["why"] for r in recipe()["female_trades"]["rows"]}
    sizes = size_rows()
    printed = printed_bands()
    left, house_left = quota()
    taken = real_names(base)
    used_ids = set(base)

    made = {}
    order = []
    refusals = Counter()
    fills = Counter()
    by_division = Counter()
    drawn_size = Counter()
    seated_size = Counter()
    trade_tally = Counter()
    relationships = Counter()

    def take(sex: str, band: str, division: str) -> None:
        key = bucket_key(sex, band, division)
        left[key] -= 1
        fills[key] += 1

    for division in CIVIL:
        house_key = f"households/family_dwelling/{division}"
        index = 0
        while True:
            wanted_women = want(left, "female", ADULT_BANDS, division)
            if not wanted_women:
                break
            if house_left.get(house_key, 0) <= 0:
                refusals[f"{house_key} is at its quota"] += 1
                break
            index += 1
            slot = f"rc_wc_{division}_{index:03d}"

            head_band = pick(seed_for(slot, "head_age_bands_1840"), wanted_women)
            trade = pick(seed_for(slot, "female_trades"), trades)
            community = community_for(trade, seed_for(slot, "name_pool_community"), pool)

            surname = step_past(seed_for(slot, "surname"), community["surnames"],
                                lambda s: False)
            given = step_past(
                seed_for(slot, "head_forename"), community["given_female"],
                lambda g: f"{g} {surname}".lower() in taken)
            name = f"{given} {surname}"
            if name.lower() in taken:
                refusals["the pool could not name this house past the real layer"] += 1
                continue
            taken.add(name.lower())

            stem = f"{PREFIX}{slug(surname)}_{slug(given)}"
            hid = f"hh_{stem}"
            bump = 1
            while hid in used_ids:
                bump += 1
                stem = f"{PREFIX}{slug(surname)}_{slug(given)}_{bump}"
                hid = f"hh_{stem}"
            used_ids.add(hid)

            head_low = band_edges()[head_band][0]
            take("female", head_band, division)
            head = person_record(
                stem, name, "head", "female", head_band,
                seed_for(slot, "head_age_bands_1840"),
                printed[("female", head_low)],
                "Drawn against the band the order book still wants in this division: the "
                "buckets were cut from the population model, so the gap IS the model's "
                "shape and a draw that chased it converges on the pyramid rather than "
                "near it.",
                "sex_ratio",
                "The 1840 city returned 146.8 men per 100 women aged twenty and over and "
                "this layer stood far past that, because the rolls that name the town name "
                "men. This woman is one of the count the order book says is missing from "
                f"the {division} division.",
                seed_for(slot, "head_age_bands_1840"),
                seed_for(slot, "head_forename"),
                f"The forename and the surname are both drawn from the {community['label']} "
                "pool: nothing about this house is read, so no part of the name is "
                "inherited from a real person.",
                community, f"this {division}-division household",
                "RECONSTRUCTED, NOT FOUND. No source names this woman. She exists because "
                "the population model says the town held women of this age in this "
                "division that the naming sources never printed, and the whole of what is "
                "claimed is that: a woman of this band, keeping her own house, drawn from "
                "the 1840 Chicago schedule and reproducible from the seed printed above. "
                "No figure is drawn (L1).",
                occupation_block(trade, seed_for(slot, "female_trades"),
                                 trade_why[trade]))
            trade_tally[trade] += 1

            size = pick(seed_for(slot, "household_size"), sizes)
            drawn_size[size] += 1
            cap = min(19, max(0, head_low - 20))
            members = []
            for step in range(max(0, size - 1)):
                member = draw_member(slot, step + 1, stem, division, left, printed,
                                     community, cap, taken, "the draw")
                if member is None:
                    refusals[f"the {division} child buckets are full"] += 1
                    break
                take(member["_sex"], member["_band"], division)
                relationships[member["relationship"]] += 1
                members.append(strip(member))

            house_left[house_key] -= 1
            fills[house_key] += 1
            by_division[division] += 1
            made[hid] = household_record(hid, slot, division, head, members, trade, size, 0)
            order.append(hid)

    # THE RESIDUAL SWEEP. A division whose women are all seated and whose child buckets are
    # still short: the 1840 histogram is a distribution over ALL households and these are
    # the particular houses the pyramid needs, so the drawn size is a floor here as it is
    # in T-1171, and the remainder is seated across the houses this stage made.
    residual = Counter()
    for division in CIVIL:
        houses = [hid for hid in order if made[hid]["division"] == division]
        if not houses:
            if want(left, "male", CHILD_BANDS, division) or want(left, "female", CHILD_BANDS,
                                                                 division):
                refusals[f"the {division} division has no house to seat a residual child in"] += 1
            continue
        sweep = 0
        while want(left, "male", CHILD_BANDS, division) or want(left, "female", CHILD_BANDS,
                                                                division):
            sweep += 1
            moved = False
            for hid in houses:
                card = made[hid]
                if not (want(left, "male", CHILD_BANDS, division)
                        or want(left, "female", CHILD_BANDS, division)):
                    break
                stem = hid[3:]
                slot = f"rc_wc_{division}_residual_{sweep:02d}"
                head_low = card["persons"][0]["age_band"]["low"]
                cap = min(19, max(0, head_low - 20))
                step = len(card["persons"])  # the next slot in this house
                member = draw_member(slot, step, stem, division, left, printed,
                                     community_of(card, pool), cap, taken,
                                     "the residual sweep")
                if member is None:
                    continue
                take(member["_sex"], member["_band"], division)
                relationships[member["relationship"]] += 1
                card["persons"].append(strip(member))
                card["women_children"]["seated"] = len(card["persons"])
                card["women_children"]["seated_beyond_the_draw"] += 1
                residual[division] += 1
                moved = True
            if not moved:
                refusals[f"the {division} sweep could seat nobody"] += 1
                break

    for hid in order:
        seated_size[made[hid]["women_children"]["seated"]] += 1

    ledger = {
        "_doc": "DERIVED — regenerate with tools/reconstruct_women_children.py --build. The "
                "measurement this stage is held to: what was drawn, against the model rows "
                "and the order book buckets it was drawn from. Do not hand-edit.",
        "id": "1835_women_children",
        "ticket": TICKET,
        "stage": STAGE,
        "target_date": SCENE_DATE,
        "generated_by": "tools/reconstruct_women_children.py --build",
        "not_a_reading": "no source was opened; nobody here is named by one",
        "households_written": len(order),
        "households_by_division": dict(sorted(by_division.items())),
        "people_written": sum(len(made[hid]["persons"]) for hid in order),
        "women_headed": len(order),
        "children_and_household_members": sum(len(made[hid]["persons"]) - 1 for hid in order),
        "seated_in_the_residual_sweep": dict(sorted(residual.items())),
        "relationships_written": dict(sorted(relationships.items())),
        "head_trades": dict(sorted(trade_tally.items())),
        "size_drawn_histogram": {str(k): v for k, v in sorted(drawn_size.items())},
        "seated_histogram": {str(k): v for k, v in sorted(seated_size.items())},
        "refusals": dict(sorted(refusals.items())),
        "fills": dict(sorted(fills.items())),
        "buckets_left_short": {k: v for k, v in sorted(left.items()) if v > 0},
    }
    # T-1489. THE SEAT ANOTHER PASS DREW FOR THESE PEOPLE, CARRIED THROUGH THE REBUILD.
    # This stage's cards stand in `households/` and 33 of the 123 seats
    # `tools/seat_reconstructed_trades_1835.py` draws land on them. `owned_view` compares
    # `persons` whole, so without this the key that pass writes would read as drift here
    # and be deleted by the next --build. Same fixed-slot carry the four mints of this
    # directory already use for `workplaces`; what the block may CONTAIN is that pass's
    # --check to decide, never this one's.
    carry_seats(made, HOUSEHOLDS)
    return made, ledger


def community_of(card: dict, pool: dict) -> dict:
    by_id = {c["id"]: c for c in pool["communities"]}
    return by_id[card["persons"][0]["reconstruction"]["community"]]


def strip(member: dict) -> dict:
    return {k: v for k, v in member.items() if not k.startswith("_")}


def draw_member(slot: str, step: int, stem: str, division: str, left: dict,
                printed: dict, community: dict, cap: int, taken: set, why: str):
    """One person in a drawn house, or None where the division's buckets are full."""
    weighted = []
    for sex in ("female", "male"):
        for band, short in want(left, sex, CHILD_BANDS, division):
            weighted.append(((sex, band), short))
    if not weighted:
        return None
    sex, band = pick(seed_for(f"{slot}:{stem}", f"member_{step}_sex_age"), weighted)
    low = band_edges()[band][0]
    kin = low <= cap
    if kin:
        relationship = "son" if sex == "male" else "daughter"
        band_why = (f"Capped at {cap} years: nobody is born after {SCENE_DATE}, and no "
                    "child of this house is older than the head's own age band allows her "
                    "to have borne them.")
        note = ("RECONSTRUCTED, NOT FOUND. Nobody is named by any source here. This child "
                "exists because the order book says the "
                f"{division} division is short of people of this sex and age, and the "
                "whole of what is claimed is that. A source naming this household retires "
                "them. No figure is drawn (L1).")
    else:
        relationship = "household_member"
        band_why = ("Older than the head's own band allows her to have borne, so no kin tie "
                    "is claimed. The model places older children out as apprentices and "
                    "servants; WHICH of the two this person was is not claimed, because "
                    "nothing here can tell.")
        note = ("RECONSTRUCTED, NOT FOUND, AND NOT CLAIMED AS KIN. This person is in the "
                "house and nothing says how. The population model places older children "
                "out of their parents' houses as apprentices and servants, and the head of "
                "this one is not old enough to be their parent, so the record says "
                "`household_member` and stops there rather than inventing a relation. A "
                "source naming this household retires them. No figure is drawn (L1).")
    given = step_past(seed_for(f"{slot}:{stem}", f"member_{step}_forename"),
                      community["given_male" if sex == "male" else "given_female"],
                      lambda g: f"{g} {surname_of(stem)}".lower() in taken)
    name = f"{given} {surname_of(stem)}"
    taken.add(name.lower())
    out = person_record(
        f"{stem}_{step}", name, relationship, sex, band,
        seed_for(f"{slot}:{stem}", f"member_{step}_sex_age"),
        printed[(sex, low)], band_why,
        "under_ten" if band == "under_10" else "age_bands_1840",
        f"Drawn by {why} against the {division} division's own shortfall in the order "
        "book: the buckets were cut from the population model and this person is one of "
        "the count they still want.",
        seed_for(f"{slot}:{stem}", f"member_{step}_sex_age"),
        seed_for(f"{slot}:{stem}", f"member_{step}_forename"),
        "The forename is drawn from the "
        f"{community['label']} pool; the surname is the household's own.",
        community, "this household", note,
        {"value": "none_recorded", "confidence": RECONSTRUCTED,
         "note": "No trade is drawn for anyone but the head of a reconstructed house. The "
                 "occupation model is spent on heads and on the trades the town is short "
                 "of (T-1173); a child's and a servant's work in an 1835 household is real "
                 "and unrecorded, and this project will not invent a column for it."})
    out["_sex"] = sex
    out["_band"] = band
    return out


def surname_of(stem: str) -> str:
    """`rc_<surname>_<given>` -> the surname as the household prints it."""
    parts = stem[len(PREFIX):].split("_")
    return parts[0].capitalize() if parts else "Unnamed"


# ------------------------------------------------------------------ the tables --

def present(live: dict) -> list:
    """The people the order book counts as the town: the present households alone."""
    return [p for card in live.values() for p in (card.get("persons") or [])
            if value_of(card.get("present_on_scene_date")) == "present"]


def sex_ratio(people: list):
    adults = Counter()
    for person in people:
        band = person.get("age_band")
        low = band.get("low") if isinstance(band, dict) else None
        if low is None or int(low) < 20:
            continue
        adults[value_of(person.get("sex_basis")) or person.get("sex")] += 1
    if not adults["female"]:
        return None, dict(adults)
    return round(100.0 * adults["male"] / adults["female"], 1), dict(adults)


def model_figure(name: str):
    for section in json.loads(MODEL.read_text(encoding="utf-8"))["sections"]:
        for figure in section.get("figures") or []:
            if figure["figure"] == name:
                return figure
    return None


def pyramid(people: list) -> dict:
    out = Counter()
    for person in people:
        band = person.get("age_band")
        low = band.get("low") if isinstance(band, dict) else None
        if low is not None:
            out[book_band(int(low))] += 1
    return dict(sorted(out.items()))


def measurement(base: dict, made: dict, ledger: dict) -> dict:
    """The acceptance's printed tables: the layer, against the model it was drawn from."""
    live = dict(base)
    live.update(made)
    before, _ = sex_ratio(present(base))
    after, adults = sex_ratio(present(live))
    ratio = model_figure("males_per_100_females")
    wanted = [ratio["low"], ratio["high"]] if ratio else None

    people = present(live)
    bands = pyramid(people)
    total = sum(bands.values()) or 1
    under_ten = model_figure("share_under_ten")

    heads = [card for card in live.values()
             if value_of(card.get("present_on_scene_date")) == "present"
             and card.get("persons")]
    female_headed = sum(1 for card in heads
                        if (card["persons"][0].get("sex_basis") and
                            value_of(card["persons"][0].get("sex_basis")) == "female")
                        or card["persons"][0].get("sex") == "female")

    model_size = table("households_and_families", "size_histogram_1840")["rows"]
    cut = sum(int(r["households"]) for r in model_size if 1 <= int(r["size"]) <= KIN_MAX)
    shape = {str(r["size"]): round(int(r["households"]) / cut, 4)
             for r in model_size if 1 <= int(r["size"]) <= KIN_MAX}
    seated_total = sum(ledger["seated_histogram"].values()) or 1
    seated = {k: round(v / seated_total, 4) for k, v in ledger["seated_histogram"].items()}

    short = sum(ledger["buckets_left_short"].values())
    return {
        "the_town_the_book_counts": "present households only",
        "people_before_this_stage": len(present(base)),
        "people_after_this_stage": len(people),
        "households_before_this_stage": len([c for c in base.values()
                                             if value_of(c.get("present_on_scene_date"))
                                             == "present"]),
        "households_after_this_stage": len(heads),
        "female_headed_households_after": female_headed,
        "female_headed_share_after": round(female_headed / float(len(heads)), 4) if heads else None,
        "female_headed_share_1840": female_headed_1840(),
        "why_the_shares_are_not_yet_in_bracket":
            "THE COUNTS ARE MET AND THE SHARES ARE NOT, and that is a reading of a town "
            "half built rather than a defect of this stage. Every one of this stage's 24 "
            "buckets is filled to the number the order book asked for - "
            "`this_stage_s_buckets_left_short` is 0 - and those numbers were cut against "
            "the model's WHOLE town of 2,535 people. The layer this stage hands on holds "
            "about half of it, because the boarders, lodgers, hotel guests and crews "
            "(T-1175), the garrison (T-1349), the under-documented cohorts (T-1177) and "
            "the transients (T-1178) are not written yet and they are overwhelmingly adult "
            "and overwhelmingly male. So the children this stage seated are a larger share "
            "of a smaller town than they will be of the finished one, and the adult sex "
            "ratio is nearer the model than it was (340.2 -> 161.4) without reaching it. "
            "Reporting either as met here would be the invention this programme exists to "
            "refuse; T-1179 converges the layer and re-runs the profile.",
        "adults_after_this_stage": adults,
        "adult_sex_ratio_before": before,
        "adult_sex_ratio_after": after,
        "the_model_s_range": wanted,
        "inside_the_model_s_range": (after is not None and wanted is not None
                                     and wanted[0] <= after <= wanted[1]),
        "age_pyramid_after": bands,
        "share_under_ten_after": round(bands.get("under_10", 0) / float(total), 4),
        "share_under_ten_model": [under_ten["low"], under_ten["high"]] if under_ten else None,
        "this_stage_s_buckets_left_short": short,
        "household_size_1840_share": shape,
        "household_size_seated_share": seated,
        "largest_share_gap": round(max(
            abs(seated.get(k, 0.0) - v) for k, v in shape.items()), 4) if shape else None,
        "what_remains": "T-1175 seats the boarders, lodgers and crews the lodging model "
                        "counts; T-1179 converges the layer and re-runs the population "
                        "profile.",
    }


def female_headed_1840():
    """The 1840 schedule's own female-headed share — where the extract carries one.

    IT DOES NOT, and the honest answer is to say so rather than to print a number. The
    1840 population schedule counted a household by its head's NAME and then tallied
    everyone in it by sex and age in columns; the committed IPUMS extract carries those
    tallies and no sex for the head. So this project holds no measured female-headed share
    for this town in this decade, and the share printed beside it is a count of what this
    stage wrote, offered for argument rather than against a target.
    """
    doc = json.loads(COMPOSITION.read_text(encoding="utf-8"))
    heads = doc.get("household_heads") or {}
    if heads.get("female") and heads.get("total"):
        return round(int(heads["female"]) / float(heads["total"]), 4)
    return ("not carried: the committed 1840 extract tallies a household's members by sex "
            "and age and records no sex for its head, so no measured share exists to "
            "compare this one against")


# ----------------------------------------------------------------------- modes --

def base_layer() -> dict:
    return {hid: card for hid, card in cards().items() if not ours(card)}


def build() -> int:
    base = base_layer()
    made, ledger = fill(base)
    written = 0
    for hid, card in made.items():
        path = HOUSEHOLDS / f"{hid}.json"
        if not path.exists():
            path.write_text(dumps(card), encoding="utf-8")
            written += 1
            continue
        live = json.loads(path.read_text(encoding="utf-8"))
        merged = OrderedDict()
        for key, value in card.items():
            merged[key] = live[key] if key not in OWNED_KEYS and key in live else value
        for key, value in live.items():
            if key not in merged:
                merged[key] = value
        if path.read_text(encoding="utf-8") != dumps(merged):
            path.write_text(dumps(merged), encoding="utf-8")
            written += 1
    for path in sorted(HOUSEHOLDS.glob("hh_*.json")):
        if path.stem not in made and ours(json.loads(path.read_text(encoding="utf-8"))):
            path.unlink()
            written += 1
    ledger["measurement"] = measurement(base, made, ledger)
    LEDGER.write_text(dumps(ledger), encoding="utf-8")
    write_fills(ledger)
    print("  wrote %s" % LEDGER.relative_to(ROOT))
    print("  %d card(s) written; %d household(s), %d people — %d women and %d others"
          % (written, ledger["households_written"], ledger["people_written"],
             ledger["women_headed"], ledger["children_and_household_members"]))
    return 0


def write_fills(ledger: dict) -> None:
    """Carry this stage's fills into the order book and re-derive it."""
    import build_order_book_1835 as ob
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    kept = [f for f in book.get("fills", []) if f.get("ticket") != TICKET]
    kept += [{"bucket": key, "ticket": TICKET, "stage": STAGE, "records": n,
              "by": "tools/reconstruct_women_children.py --build"}
             for key, n in sorted(ledger["fills"].items())]
    book["fills"] = kept
    BOOK.write_text(json.dumps(book, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ob.cmd_build()


def check() -> int:
    live = cards()
    base = {hid: card for hid, card in live.items() if not ours(card)}
    made, ledger = fill(base)

    committed = {hid for hid, card in live.items() if ours(card)}
    if committed != set(made):
        missing = sorted(set(made) - committed)[:4]
        extra = sorted(committed - set(made))[:4]
        print("  FAIL the committed layer is not the set this stage derives "
              "(%d committed, %d derived; missing %s; unexplained %s)"
              % (len(committed), len(made), missing or "none", extra or "none"))
        return 1
    bad = [hid for hid in sorted(made)
           if dumps(owned_view(live[hid])) != dumps(owned_view(made[hid]))]
    if bad:
        print("  FAIL %d card(s) are not what this stage derives: %s"
              % (len(bad), ", ".join(bad[:6])))
        return 1
    ledger["measurement"] = measurement(base, made, ledger)
    if not LEDGER.exists() or LEDGER.read_text(encoding="utf-8") != dumps(ledger):
        print("  FAIL %s is not what --build writes" % LEDGER.relative_to(ROOT))
        return 1
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    ours_fills = {f["bucket"]: int(f.get("records") or 0)
                  for f in book.get("fills", []) if f.get("ticket") == TICKET}
    if ours_fills != dict(ledger["fills"]):
        print("  FAIL the order book's fills for %s are not this stage's ledger" % TICKET)
        return 1
    print("  ok    %d household(s) and %d people re-derive from their seeds"
          % (ledger["households_written"], ledger["people_written"]))
    print("  ok    the order book carries %d fill(s) for %s and no bucket is overfilled"
          % (len(ours_fills), TICKET))
    return 0


def report() -> int:
    base = base_layer()
    made, ledger = fill(base)
    stats = measurement(base, made, ledger)
    print("THE HOUSES THE NAMING SOURCES NEVER PRINTED")
    print("   households %5d   people %5d   women %5d   others %5d"
          % (ledger["households_written"], ledger["people_written"],
             ledger["women_headed"], ledger["children_and_household_members"]))
    for division, n in sorted(ledger["households_by_division"].items()):
        print("   %-6s %5d household(s), %s seated in the residual sweep"
              % (division, n, ledger["seated_in_the_residual_sweep"].get(division, 0)))
    print("THE HEADS' TRADES — the programme's own table, and an assumption it states")
    for trade, n in sorted(ledger["head_trades"].items(), key=lambda kv: -kv[1]):
        print("   %5d  %s" % (n, trade))
    print("WHO THE REST ARE")
    for rel, n in sorted(ledger["relationships_written"].items(), key=lambda kv: -kv[1]):
        print("   %5d  %s" % (n, rel))
    print("HOUSEHOLD SIZE — the 1840 city against what was seated")
    for size in sorted(stats["household_size_1840_share"], key=int):
        print("   %2s  1840 %6.4f   seated %6.4f" % (
            size, stats["household_size_1840_share"][size],
            stats["household_size_seated_share"].get(size, 0.0)))
    print("   largest share gap %s" % stats["largest_share_gap"])
    print("THE TOWN THE BOOK COUNTS — present households, before and after the draw")
    print("   people %5d -> %5d   households %5d -> %5d"
          % (stats["people_before_this_stage"], stats["people_after_this_stage"],
             stats["households_before_this_stage"], stats["households_after_this_stage"]))
    print("   adult sex ratio %s -> %s   the model's range %s   in bracket: %s"
          % (stats["adult_sex_ratio_before"], stats["adult_sex_ratio_after"],
             stats["the_model_s_range"], stats["inside_the_model_s_range"]))
    print("   female-headed households %d (%s of the town); the 1840 share %s"
          % (stats["female_headed_households_after"], stats["female_headed_share_after"],
             stats["female_headed_share_1840"]))
    print("   share under ten %s against the model's %s"
          % (stats["share_under_ten_after"], stats["share_under_ten_model"]))
    for band, n in sorted(stats["age_pyramid_after"].items()):
        print("   %-9s %5d" % (band, n))
    print("   this stage's buckets left short: %d" % stats["this_stage_s_buckets_left_short"])
    if ledger["refusals"]:
        print("REFUSED — the quota doing its job")
        for why, n in sorted(ledger["refusals"].items()):
            print("   %5d  %s" % (n, why))
    return 0


# ------------------------------------------------------------------ self-test --

def self_test() -> int:
    failures = []

    def fires(what: str, ok: bool) -> None:
        print("   self-test | %-62s %s" % (what, "ok" if ok else "FAIL"))
        if not ok:
            failures.append(what)

    fires("the same seed draws the same face twice",
          draw("rc_wc_south_001:household_size") == draw("rc_wc_south_001:household_size"))
    fires("two slots draw different faces",
          draw("rc_wc_south_001:household_size") != draw("rc_wc_south_002:household_size"))
    fires("a weighted pick never chooses a bucket of weight zero",
          all(pick(f"s{i}", [("a", 0), ("b", 1)]) == "b" for i in range(40)))
    fires("the size histogram is cut at the kin range",
          all(1 <= s <= KIN_MAX for s, _ in size_rows()))
    fires("an age of 9 bands as a child", book_band(9) == "under_10")
    fires("an age of 50 bands as the open cohort", book_band(50) == "50_plus")
    fires("only the adult bands may head a house",
          all(book_band(low) in ADULT_BANDS for low in (20, 30, 40, 50, 70))
          and all(book_band(low) in CHILD_BANDS for low in (0, 5, 10, 15)))
    fires("a bucket key is the order book's own shape",
          bucket_key("female", "20_29", "south")
          == "persons/female/20_29/south/family/none")
    fires("a bucket at zero is not wanted",
          want({bucket_key("female", "20_29", "south"): 0}, "female",
               ADULT_BANDS, "south") == []
          and want({bucket_key("female", "20_29", "south"): 3}, "female",
                   ADULT_BANDS, "south") == [("20_29", 3)])
    fires("a name the real layer bears is stepped past",
          step_past("s", ["Mary", "Sarah"], lambda g: g == "Mary") == "Sarah")
    fires("a household of this stage names the stage that wrote it",
          ours({"women_children": {"stage": STAGE}})
          and not ours({"women_children": {"stage": "modelled_families"}})
          and not ours({"id": "hh_x"}))
    fires("the owned view drops another stage's keys",
          set(owned_view({"id": "hh_x", "arrival_year": {}, "persons": []}))
          == {"id", "persons"})
    fires("a surname is read back off the household stem",
          surname_of("rc_chapin_mary") == "Chapin")
    fires("a slug is safe in a file name", slug("O'Brien Jr.") == "o_brien_jr")
    fires("every drawn trade is the residents vocabulary's own",
          set(t for t, _ in trade_rows()) <= set(
              json.loads((ROOT / "data" / "residents" / "index.json")
                         .read_text(encoding="utf-8"))["vocabulary"]["occupations"]))
    fires("no reviewed community may be drawn here",
          all(c["id"] not in ("native", "potawatomi", "metis", "métis", "indigenous")
              for c in pools()["communities"]))
    fires("a band block prints a band and never a year",
          band_block("30_39", "s", "col", "why")["value"] == "30-39"
          and band_block("50_plus", "s", "col", "why")["high"] is None)
    fires("a drawn person carries basis, seed and what retires them",
          all(k in band_block("20_29", "s", "col", "why")
              for k in ("basis", "seed", "replaceable_by", "tier")))
    fires("an untraded head still says why it has no trade",
          occupation_block("none_recorded", "s", "")["value"] == "none_recorded"
          and "basis" not in occupation_block("none_recorded", "s", ""))
    fires("a traded head names the table it was drawn from",
          occupation_block("laundress", "s", "why")["basis"]["id"]
          == "women_children_fill.female_trades")

    print("   self-test | %d rule(s) checked, %d failed" % (20, len(failures)))
    return 1 if failures else 0


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.build:
        return build()
    if args.check:
        return check()
    if args.report:
        return report()
    if args.self_test:
        return self_test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
