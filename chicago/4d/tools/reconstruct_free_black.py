#!/usr/bin/env python3
"""The free Black town of 1835, written to the floor of the only bracket the corpus gives.

    tools/reconstruct_free_black.py --build       write the record, the cards and the firms
    tools/reconstruct_free_black.py --check       the gate: everything re-derives
    tools/reconstruct_free_black.py --report      the derivation, printed
    tools/reconstruct_free_black.py --self-test   the rules, each refusing its own case

T-1377, piece 3 of T-1177. The `free_black` sub-stage of stage `underdocumented` of the
1835 resident reconstruction programme; `native_and_metis` (T-1376) is the sub-stage
beside it and `tools/reconstruct_underdocumented.py` is that one's writer. The two share
`data/residents/underdocumented/` and sweep their own id prefixes out of it — `hh_um_`
there, `hh_fb_` here.

THE MEASUREMENT THIS STAGE WAS OPENED ON. T-1375 derived a community for every person in
the layer and printed the result: of 2,626 people, the ones reading `free_black` were
**nobody**. That is not a finding about 1835 Chicago. It is a finding about this project:
the town had free Black residents, the corpus says so, and no stage had ever been licensed
to write one.

WHAT IS DIFFERENT HERE FROM THE SUB-STAGE BESIDE IT. T-1376 had a roll with names on it,
so it CARDED men — read names, no invention. This stage has no names at all. The corpus
counts free Black people at Chicago twice and names none of them inside the window, so
what this stage writes is a RECONSTRUCTED COHORT: people drawn from a pool, every one
`rc_fb_`-prefixed, graded `reconstructed`, and retired by the first source that names a
real free Black resident of this town. Nobody here is a person the sources found.

THE BRACKET, and both ends of it are read rather than assumed:

  FLOOR — August 1833. Andreas, quoted in this layer's own card for John Dean Caton:
  he "defended six or seven free coloured men before the Court of County Commissioners
  and obtained certificates of freedom for them, his fee a dollar from each." Under the
  Illinois black law then in force a free Black person resident in the state had to hold
  and record such a certificate, so the six or seven were men establishing a lawful
  residence at Chicago — not travellers through it. That is a COUNT of adult men, and it
  is the only count of Black people at Chicago the corpus makes before the scene date.

  CEILING — 1840. `data/research/census_1840/composition_1840.json`, derived from the
  committed IPUMS extract, counts 53 free coloured persons in a town of 4,834. Carried
  back at the same share onto the town model's point reading for 1 July 1835 (2,536
  persons), that is about 27 people, and about 25 to 35 over the model's whole range.

  This stage writes the FLOOR and says so. The head-room between the floor and the
  ceiling is real and is left standing, because filling it would be inventing people
  against a share carried back across five years of the fastest growth this town ever
  had — a different claim from the one the floor makes.

WHY NO PERSISTENCE DRAW. T-1376 priced each of its men against the persistence model,
because there the subject was a NAME: a man named once in 1832 may have left. Here the
subject is a COUNT, and a count does not leave. Between the 1833 reading and the 1840
one the town went from a few hundred people to nearly five thousand and its free Black
population from six or seven men to fifty-three persons; no monotone path between those
two readings passes below six on 1 July 1835. So the floor is carried forward whole, and
the men who carry it are not the men Caton defended — they are the cohort those men are
the count of.

THE NAME POOL, and what is honest about it. `data/reconstruction/1835_invented_name_pools.json`
gains a `free_black` community. Its SURNAMES are the six the 1840 Chicago schedule prints
on lines the borderline roster classes R6 on its own `community_term_in_the_reading` rule
— the only free Black naming this corpus holds, anywhere. Its GIVEN names are the town's
own stock, and that is not a shortcut: every one of the five given names the schedule
prints in that block (George, John, Joseph, Samuel, Eliza) is already borne by a real
person of this town, which `--self-test` asserts against the committed layer. What this
pool contributes that no other pool can is its surnames.

Two rules keep the pool from becoming a back-projection of six real people:

  1. NO DRAWN NAME MAY REPRODUCE AN ATTESTED READING. The six surnames come off six
     people the 1840 census names; a draw that put a pool given name back beside its own
     printed surname would be minting that person into 1835, which is exactly what the
     roster refused when it classed those rows `later_only`.
  2. NO DRAWN NAME MAY BE BORNE BY ANYBODY IN THE LAYER. The same rule every invented
     name in this programme is held to, and `reconstruct_residents_1835.py` enforces it
     over the committed cards as well.

THE TRADES ARE A LIBERTY AND SAY SO. The corpus records no occupation for any Black
person at Chicago before 1840 — no advertisement, no directory line, no roll. The seven
trades dealt here are the service, carrying and labouring trades of a northern lake town,
and choosing to deal from them rather than from the merchant and professional classes is
an assumption about the 1835 labour market and not a reading of anything. It is written
into `docs/LIBERTIES.md`, it is on the face of every card it touched, and any source
naming a free Black resident of Chicago at a trade retires it.

EVERY RECORD HERE IS `review_required`. Not for the reason the sub-stage beside it is —
this is not the removal — but because AGENTS.md refuses a bare flag and this cohort is
the one the project has the least evidence about and the most responsibility toward: a
reconstruction of Black residents of a town inside a state whose black laws bounded their
residence, drawn from six surnames and no biography at all. `touches_removal` is FALSE,
deliberately, because writing it true would borrow the weight of a subject this stage is
not about.
"""

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resident_mint_carry import carry_seats  # noqa: E402

from reconstruct_residents_1835 import (  # noqa: E402
    RECONSTRUCTED, UNDERDOCUMENTED_STAGE, check_reconstructed_person, load_programme,
    stages)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESIDENTS = DATA / "residents"
CARDS = RESIDENTS / "underdocumented"
HOUSEHOLDS = RESIDENTS / "households"
CATON = HOUSEHOLDS / "hh_caton_john_dean.json"
ROSTER = DATA / "reconstruction" / "1835_borderline_roster.json"
PAGES = DATA / "research" / "census_1840" / "pages"
COMPOSITION = DATA / "research" / "census_1840" / "composition_1840.json"
TOWN_CENSUS = DATA / "town_census.json"
POOLS = DATA / "reconstruction" / "1835_invented_name_pools.json"
OUT = DATA / "reconstruction" / "1835_free_black.json"
FIRMS = DATA / "businesses" / "authored"

STAGE = UNDERDOCUMENTED_STAGE
SUB_STAGE = "free_black"
TICKET = "T-1377"
PARENT = "T-1177"
COMMUNITY = "free_black"
SCENE_DATE = dt.date(1835, 7, 1)
CARD_PREFIX = "hh_fb_"
PERSON_PREFIX = "rc_fb_"
FIRM_PREFIX = "rcb_fb_"
SCHEMA = 1

POOL_ID = "free_black"
ROSTER_CLASS = "R6_native_metis_black"
ROSTER_COMMUNITY = "black"
# The leaf that counts the town instead of enumerating it. Fifteen of its thirty lines
# carry free-coloured cells and NOT ONE of them is a household: they are the enumerator's
# own recapitulation, and a reader who counts them meets the same people twice.
RECAPITULATION = "recapitulation"

# The 1833 reading, as the Caton card prints it. Parsed rather than typed so the count
# cannot drift from the sentence it comes from.
CATON_PHRASE = re.compile(
    r"defended\s+(six|seven)\s+or\s+(six|seven)\s+free\s+coloured\s+men", re.I)
WORDS = {"six": 6, "seven": 7}
# A position the reader could not settle. The schedule's transcriptions mark them.
UNREAD = re.compile(r"[\[\]?]")

# The trades this stage deals, and the liberty is that this list exists at all.
TRADES = ["barber", "cook", "waiter", "drayman", "labourer", "whitewasher", "sawyer"]
# The trade the one firm-keeping woman of this cohort works at.
WOMANS_TRADE = "laundress"

TRADE_LIBERTY = (
    "A LIBERTY, DECLARED. No source in this corpus records an occupation for any Black "
    "person at Chicago before 1840 — not an advertisement, not a directory line, not a "
    "roll. The seven trades this stage deals are the service, carrying and labouring "
    "trades of a northern lake town, and dealing from them rather than from the "
    "merchant and professional classes is an assumption about the 1835 labour market. "
    "Nothing here says a free Black man at Chicago could not keep a store or read law; "
    "it says this project has no reading either way and has written down which way it "
    "guessed. docs/LIBERTIES.md carries it.")

FLOOR_RULE = (
    "THE FLOOR OF THE 1835 BRACKET, CARRIED FORWARD WHOLE. Caton's fee in August 1833 "
    "counts six or seven free coloured men at Chicago, each of them before the Court of "
    "County Commissioners for the certificate of freedom the Illinois black law made the "
    "condition of a lawful residence. The 1840 census counts fifty-three free coloured "
    "persons in the same town. No monotone path between those two readings passes below "
    "the 1833 count on 1 July 1835, so the count is carried and not drawn against a "
    "persistence rate — the subject here is a COUNT, and a count does not leave town.")

REFUSALS = {
    "the_given_name_carries_an_unread_position": (
        "The schedule's given name has a bracketed position in it — `Sam[l]` — so the "
        "forename is a supplied reading and not a printed one. The SURNAME on the same "
        "line is admitted, because that part of the reading is whole; the forename is "
        "not carried into a pool of given names."),
    "the_surname_is_not_settled_on_the_page": (
        "The roster's reading leaves an unread position inside the surname, so the "
        "normalised string is not a name — `T. M. Monta[?]on` normalises to `monta on`, "
        "two words neither of which is the surname. A pool that carried it would be "
        "offering a reading the page does not make."),
    "the_reading_gives_an_initial_and_not_a_given_name": (
        "The schedule prints an initial where the given name would be. An initial is "
        "not a name and cannot enter a pool of given names; the SURNAME on the same "
        "line is admitted, because that part of the reading is whole."),
    "later_only_and_this_stage_mints_nobody_from_1840": (
        "Every one of these readings is dated 1840, five years after the scene, and the "
        "borderline roster classes it `later_only` for that reason. This stage does not "
        "back-project a single one of them into a person. What it takes from the page is "
        "the NAMING STOCK — surnames, without the people who bore them — and the pool's "
        "own rule refuses any draw that puts a given name back beside its printed "
        "surname."),
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def name_key(name: str) -> str:
    """`surname | first initial`, the discriminator the directory crosswalks match on."""
    words = [w.strip(".,") for w in str(name or "").split() if w.strip(".,")]
    if not words:
        return ""
    return f"{words[-1].lower()}|{words[0][0].lower()}"


def draw(seed: str) -> int:
    return int.from_bytes(hashlib.blake2s(seed.encode("utf-8"), digest_size=8).digest(),
                          "big")


def unit(seed: str) -> float:
    return draw(seed) / float(1 << 64)


def step_past(seed: str, names: list, taken: set) -> str:
    """A name from the pool, stepping past one already taken. Deterministic."""
    start = draw(seed) % len(names)
    for offset in range(len(names)):
        candidate = names[(start + offset) % len(names)]
        if candidate.lower() not in taken:
            return candidate
    return names[start]


# ------------------------------------------------------------------ the readings --

def caton_count() -> tuple:
    """(low, high) — the count of free Black men the 1833 reading makes, parsed."""
    card = load(CATON)
    text = json.dumps(card, ensure_ascii=False)
    match = CATON_PHRASE.search(text)
    if not match:
        raise SystemExit("the Caton card no longer carries the 1833 reading this stage "
                         "stands on; the floor cannot be derived")
    a, b = WORDS[match.group(1).lower()], WORDS[match.group(2).lower()]
    return min(a, b), max(a, b)


def is_recapitulation(page: dict) -> bool:
    return RECAPITULATION in str(page.get("read_pass") or "").lower()


def free_coloured_households() -> tuple:
    """(entirely free-coloured households, households with one or more in a white one).

    Both read off the enumerated leaves only. The recapitulation leaf is excluded by its
    own description of itself, and that exclusion is a --self-test case: it carries
    fifteen lines of free-coloured cells and not one of them is a household.
    """
    entirely, mixed, skipped = [], [], []
    for path in sorted(PAGES.glob("*.json")):
        page = load(path)
        if is_recapitulation(page):
            skipped.append(page.get("familysearch_id"))
            continue
        for rec in page.get("records") or []:
            cells = rec.get("cells") or {}
            coloured = sum(v for k, v in cells.items() if k.startswith("fc_") and v)
            if not coloured:
                continue
            white = sum(v for k, v in cells.items()
                        if (k.startswith("m_") or k.startswith("f_")) and v)
            row = {
                "page": page.get("familysearch_id"),
                "line": rec.get("line"),
                "as_read": rec.get("as_read"),
                "free_coloured": coloured,
                "free_white": white,
                "cells": {k: v for k, v in sorted(cells.items())
                          if k.startswith("fc_") and v},
            }
            (entirely if white == 0 else mixed).append(row)
    return entirely, mixed, skipped


def naming_stock() -> dict:
    """The surnames and given names the corpus attests for Black people in this town.

    READ OFF `name_as_read` AND NOT OFF `normalised`. The roster normalises for its own
    matching and the normalisation breaks names: `Eliza Askie` normalises to `eliza as ie`,
    whose last word is `ie`, which is not a surname and not anything. The printed string
    is the evidence here, as it is everywhere else in this project.
    """
    roster = load(ROSTER)
    rows, surnames, given, withheld = [], [], [], []
    for row in roster.get("rows") or []:
        if row.get("class") != ROSTER_CLASS or row.get("community") != ROSTER_COMMUNITY:
            continue
        as_read = " ".join(str(row.get("name_as_read") or "").split())
        rows.append({"row_id": row.get("row_id"), "name_as_read": row.get("name_as_read"),
                     "normalised": row.get("normalised"),
                     "community_term": row.get("community_term"),
                     "ledger_disposition": row.get("ledger_disposition")})
        words = [w.strip(".,") for w in as_read.split() if w.strip(".,")]
        if len(words) < 2 or UNREAD.search(words[-1]) or len(words[-1]) < 2:
            withheld.append({"reading": row.get("name_as_read"),
                             "reason": "the_surname_is_not_settled_on_the_page"})
            continue
        surnames.append(words[-1].capitalize())
        forename = words[0]
        if UNREAD.search(forename):
            withheld.append({"reading": row.get("name_as_read"),
                             "reason": "the_given_name_carries_an_unread_position"})
        elif len(forename) < 2:
            withheld.append({
                "reading": row.get("name_as_read"),
                "reason": "the_reading_gives_an_initial_and_not_a_given_name"})
        else:
            given.append(forename.capitalize())
    attested = sorted({" ".join(w.strip(".,") for w in
                               str(r["name_as_read"]).split()).lower() for r in rows})
    return {
        "rows": rows,
        "surnames": sorted(set(surnames)),
        "given_printed": sorted(set(given)),
        "attested_readings": attested,
        "withheld": withheld,
    }


def layer_names() -> set:
    """Every name a person the sources NAME bears, lowercased. Never a reconstruction."""
    names = set()
    for directory in ("households", "readmitted", "merged"):
        for path in sorted((RESIDENTS / directory).glob("hh_*.json")):
            doc = load(path)
            record = doc.get("superseded_record", doc)
            for person in record.get("persons") or []:
                if person.get("grade") == RECONSTRUCTED:
                    continue
                name = " ".join(str(person.get("name") or "").split()).lower()
                if name:
                    names.add(name)
    return names


def layer_given_names() -> set:
    """The first word of every real person's name — the town's own given-name stock."""
    out = set()
    for name in layer_names():
        first = name.replace("(", " ").split()
        if first:
            out.add(first[0].strip(".,").lower())
    return out


def ceiling() -> dict:
    """The 1840 share, carried back onto the town model's reading of the scene."""
    comp = load(COMPOSITION)["totals"]
    census = load(TOWN_CENSUS)["people"]
    scene = census["scene"]
    share = comp["free_coloured_persons"] / float(comp["persons"])
    return {
        "free_coloured_persons_1840": comp["free_coloured_persons"],
        "persons_1840": comp["persons"],
        "slaves_1840": comp.get("slaves"),
        "share_1840": round(share, 5),
        "town_model_point_reading_1835": scene["target"],
        "town_model_range_1835": [scene["target_low"], scene["target_high"]],
        "persons_at_the_same_share": int(scene["target"] * share),
        "persons_at_the_same_share_over_the_range": [
            int(scene["target_low"] * share), int(scene["target_high"] * share)],
        "note": ("NOT A READING OF 1835 AND NEVER USED AS ONE. The 1840 share is carried "
                 "back across five years in which this town grew faster than at any other "
                 "time in its history, so it bounds the scene from above and no more. "
                 "This stage writes the floor; the head-room stays open."),
    }


# -------------------------------------------------------------------- the cohort --

def household_shapes(entirely: list) -> list:
    """The shapes an entirely free-coloured household took in 1840, smallest first.

    THE SAMPLE IS THREE HOUSEHOLDS AND THIS FILE SAYS SO EVERYWHERE IT IS USED. It is
    also the only reading of a free Black household in this town the corpus holds.
    """
    shapes, set_aside = [], []
    for row in entirely:
        cells = row["cells"]
        men = sum(v for k, v in cells.items() if k.startswith("fc_m_") and "u10" not in k)
        women = sum(v for k, v in cells.items() if k.startswith("fc_f_") and "u10" not in k)
        children = sum(v for k, v in cells.items() if k.endswith("u10"))
        shape = {
            "page": row["page"], "line": row["line"], "as_read": row["as_read"],
            "adult_men": men, "adult_women": women, "children_under_10": children,
            "persons": row["free_coloured"],
        }
        # THE ONE HOUSEHOLD A MAN DOES NOT HEAD IS SET ASIDE, NOT DISCARDED. The floor
        # this stage carries is a count of MEN — Caton's fee counts men before the county
        # court — so every household written here is headed by one, and a shape with no
        # adult man in it cannot be dealt to such a head without inventing the man the
        # page does not show. It is recorded below so the omission is legible.
        (shapes if men else set_aside).append(shape)
    key = lambda s: (s["persons"], str(s["page"]), s["line"])
    return sorted(shapes, key=key), sorted(set_aside, key=key)


def attribute(value, note, basis=None, seed=None, replaceable=None, tier=None):
    block = {"value": value, "confidence": RECONSTRUCTED,
             "tier": tier or ("unknown" if value is None else RECONSTRUCTED)}
    if basis:
        block["basis"] = basis
    if seed:
        block["seed"] = seed
    if replaceable:
        block["replaceable_by"] = replaceable
    block["note"] = note
    return block


def person_record(pid, name, relationship, sex, slot_seed, occupation, occupation_note,
                  pool_note, note):
    person = {
        "id": pid,
        "name": name,
        "relationship": relationship,
        "grade": RECONSTRUCTED,
        "sex": sex,
        "sex_basis": {
            "value": sex, "confidence": RECONSTRUCTED, "tier": RECONSTRUCTED,
            "note": ("The shape this person fills is sexed by the 1840 schedule's own "
                     "free-coloured columns, which count men and women separately. The "
                     "sex is the shape's, not a draw made over this person."),
        },
        "occupation": occupation,
        "name_basis": {
            "value": name, "confidence": RECONSTRUCTED, "tier": RECONSTRUCTED,
            "basis": {"kind": "model", "id": "1835_invented_name_pools",
                      "note": pool_note},
            "seed": f"{slot_seed}:name",
            "replaceable_by": {"kind": "person",
                               "match": "any source naming a free Black resident of "
                                        "Chicago on or before 1 July 1835"},
            "note": ("AN INVENTED NAME, AND IT IS NEVER EVIDENCE. No source names this "
                     "person. The surname is drawn from the six the 1840 schedule prints "
                     "in its free-coloured block and the given name from the town's own "
                     "stock; no draw may reproduce a printed reading, and none may take "
                     "a name a real person of this layer bears."),
        },
        "basis": {"kind": "rule", "id": "the_1833_count_is_the_floor_of_the_1835_bracket",
                  "note": FLOOR_RULE},
        "replaceable_by": {
            "kind": "person",
            "match": ("a source naming a free Black resident of Chicago inside the "
                      "window — the 1833 certificates of freedom themselves would "
                      "retire this whole cohort and name the men it stands for"),
        },
        "reconstruction": {
            "stage": STAGE,
            "sub_stage": SUB_STAGE,
            "programme": "chicago_1835_resident_reconstruction",
            "community": COMMUNITY,
            "review_required": True,
        },
        "resident_subtype": "underdocumented_resident",
        "sources": ["andreas_1884_v1"],
        "note": note,
    }
    if occupation_note:
        person["occupation"]["note"] = occupation_note
    return person


def derive():
    low, high = caton_count()
    entirely, mixed, skipped = free_coloured_households()
    shapes, shapes_set_aside = household_shapes(entirely)
    stock = naming_stock()
    pools = load(POOLS)
    pool = next((c for c in pools["communities"] if c["id"] == POOL_ID), None)
    if pool is None:
        raise SystemExit("data/reconstruction/1835_invented_name_pools.json carries no "
                         f"`{POOL_ID}` community; the pool is this stage's input")
    taken = layer_names()
    printed = {r.lower() for r in stock["attested_readings"]}
    # The discriminator this project's directory crosswalks match on — surname and first
    # initial. `Samuel Anderson` and the schedule's `Sam[l] Anderson` are the same key,
    # and a reader who met the first would take it for the second.
    printed_keys = {name_key(r) for r in stock["attested_readings"]}
    surnames = list(pool["surnames"])
    given_male = list(pool["given_male"])
    given_female = list(pool["given_female"])

    heads = high  # the upper reading of `six or seven` — see the module docstring
    cards, minted, firms = {}, [], {}
    used_names = set()
    trade_order = list(TRADES)

    used_given = set()

    def choose(seed, given_list, surname):
        """A given name for this surname: unique in the layer, unique here, and never
        the one the 1840 page prints beside that surname.

        Two passes. The first refuses a forename already standing somewhere in this
        cohort, so seven households do not come out carrying three Williams; the second
        allows the repeat, because a town of thirteen people drawing on fourteen
        forenames will have one and refusing it would be fussier than the evidence.
        """
        blocked = set(taken) | used_names
        for avoid_repeats in (True, False):
            for offset in range(len(given_list)):
                candidate = given_list[(draw(seed) + offset) % len(given_list)]
                full = f"{candidate} {surname}".lower()
                if full in blocked or full in printed:
                    continue
                if name_key(full) in printed_keys:
                    continue
                if avoid_repeats and candidate.lower() in used_given:
                    continue
                return candidate
        raise SystemExit(f"the {POOL_ID} pool cannot name a person for {surname} without "
                         f"repeating a name the layer already carries")

    def slot_of(i):
        return f"{SUB_STAGE}:floor:{i + 1:03}"

    def shape_of(i):
        return shapes[int(unit(f"{slot_of(i)}:shape") * len(shapes))]

    # The one woman of this cohort dealt a trade keeps the washing and ironing house, and
    # she is drawn from the heads whose household shape HAS an adult woman in it. Drawing
    # over all seven instead would land the firm on a household of one man about half the
    # time and quietly write no firm at all.
    with_a_wife = [i for i in range(heads) if shape_of(i)["adult_women"]]
    washerwoman = (with_a_wife[int(unit(f"{SUB_STAGE}:washerwoman") * len(with_a_wife))]
                   if with_a_wife else None)

    for i in range(heads):
        slot = slot_of(i)
        surname = surnames[i % len(surnames)]
        given = choose(f"{slot}:head", given_male, surname)
        used_given.add(given.lower())
        name = f"{given} {surname}"
        used_names.add(name.lower())
        hid = f"{CARD_PREFIX}{surname.lower()}_{given.lower()}"
        pid = f"{PERSON_PREFIX}{surname.lower()}_{given.lower()}"
        trade = trade_order[i % len(trade_order)]
        shape = shape_of(i)

        pool_note = (
            f"The surname is one of the {len(surnames)} the 1840 Chicago schedule prints "
            f"on lines the borderline roster classes {ROSTER_CLASS} on its own "
            f"`community_term_in_the_reading` rule — the only free Black naming this "
            f"corpus holds. The given name is the town's own stock: every given name the "
            f"schedule prints in that block is already borne by a real person of this "
            f"town, so this pool invents surnames' company and not a second naming "
            f"tradition.")
        occupation = attribute(
            trade, None,
            basis={"kind": "model", "id": "1835_free_black_trade_liberty",
                   "note": TRADE_LIBERTY},
            seed=f"{slot}:trade",
            replaceable={"kind": "person",
                         "match": "any source naming a free Black resident of Chicago "
                                  "at a trade"})
        occupation["note"] = (
            "DEALT, NOT READ. The trade is dealt round the seven this stage carries, in "
            "the order the slot falls, so it is reproducible from the seed above and "
            "from nothing else. No source gives this person a trade and none gives any "
            "Black person at Chicago one before 1840.")
        head = person_record(
            pid, name, "head", "male", slot, occupation, None, pool_note,
            note=("RECONSTRUCTED, NOT FOUND. Nobody is named by any source here. This "
                  "person exists because the corpus counts six or seven free coloured "
                  "men at Chicago in August 1833 and the 1840 census counts fifty-three "
                  "free coloured persons there, and between those two readings the town "
                  "of 1 July 1835 cannot hold fewer free Black men than 1833 did. The "
                  "whole of what is claimed is a free Black adult man of this town. "
                  "REVIEW REQUIRED: this is a reconstruction of a Black resident of a "
                  "town inside a state whose black laws made a certificate of freedom "
                  "the condition of his residence, written from six surnames and no "
                  "biography at all; AGENTS.md's standard holds it for review before a "
                  "scene carrying it may be marked released. No figure is drawn (L1)."))
        persons = [head]

        wife = None
        if shape["adult_women"]:
            wgiven = choose(f"{slot}:wife", given_female, surname)
            used_given.add(wgiven.lower())
            wname = f"{wgiven} {surname}"
            used_names.add(wname.lower())
            wid = f"{PERSON_PREFIX}{surname.lower()}_{wgiven.lower()}"
            keeps_firm = i == washerwoman
            wtrade = WOMANS_TRADE if keeps_firm else "none_recorded"
            woccupation = attribute(
                wtrade, None,
                basis=({"kind": "model", "id": "1835_free_black_trade_liberty",
                        "note": TRADE_LIBERTY} if keeps_firm else None),
                seed=(f"{slot}:wife_trade" if keeps_firm else None),
                replaceable=({"kind": "person",
                              "match": "any source naming a free Black woman of Chicago "
                                       "at a trade"} if keeps_firm else None),
                tier=(RECONSTRUCTED if keeps_firm else "unknown"))
            woccupation["note"] = (
                "DEALT, NOT READ — and the only woman of this cohort dealt a trade, "
                "because the firm below needs a keeper and the corpus names none. The "
                "liberty above is the same one the men's trades stand on."
                if keeps_firm else
                "No source records an occupation for this person, and this stage does "
                "not deal one to a woman it has not also given a firm. The silence is "
                "the record's, not a finding that she kept no trade.")
            wife = person_record(
                wid, wname, "wife", "female", f"{slot}:wife", woccupation, None,
                pool_note,
                note=("RECONSTRUCTED, NOT FOUND. She fills the adult woman of the "
                      "household shape this card was dealt — one of the three entirely "
                      "free-coloured households the 1840 Chicago schedule enumerates, "
                      "which is every reading of a free Black household this corpus "
                      "holds. REVIEW REQUIRED, for the reason the head's card gives. No "
                      "figure is drawn (L1)."))
            persons.append(wife)

        # A SECOND OR THIRD ADULT WOMAN UNDER THE SAME ROOF, where the schedule counts
        # one. The page says how many stood there and says nothing about who they were,
        # so neither does this: `household_member` and no kinship claimed.
        for n in range(max(0, shape["adult_women"] - 1)):
            oseed = f"{slot}:woman:{n + 2}"
            ogiven = choose(oseed, given_female, surname)
            used_given.add(ogiven.lower())
            oname = f"{ogiven} {surname}"
            used_names.add(oname.lower())
            persons.append(person_record(
                f"{PERSON_PREFIX}{surname.lower()}_{ogiven.lower()}", oname,
                "household_member", "female", oseed,
                attribute("none_recorded", "No source records an occupation for this "
                                           "person.", tier="unknown"),
                None, pool_note,
                note=("RECONSTRUCTED, NOT FOUND. A second adult woman under this roof, "
                      "because the 1840 household shape this card was dealt counts two "
                      "and names neither. No kinship is claimed: sister, mother, "
                      "sister-in-law, boarder or servant are all readings the schedule's "
                      "tick marks cannot separate, and this project writes none of them. "
                      "REVIEW REQUIRED, for the reason the head's card gives. No figure "
                      "is drawn (L1).")))

        for n in range(shape["children_under_10"]):
            cseed = f"{slot}:child:{n + 1}"
            csex = "female" if unit(f"{cseed}:sex") < 0.5 else "male"
            clist = given_female if csex == "female" else given_male
            cgiven = choose(cseed, clist, surname)
            used_given.add(cgiven.lower())
            cname = f"{cgiven} {surname}"
            used_names.add(cname.lower())
            cid = f"{PERSON_PREFIX}{surname.lower()}_{cgiven.lower()}"
            coccupation = attribute("none_recorded", "A child under ten. No trade, and "
                                                     "no source that would give one.",
                                    tier="unknown")
            persons.append(person_record(
                cid, cname, "child", csex, cseed, coccupation, None, pool_note,
                note=("RECONSTRUCTED, NOT FOUND. A child under ten, filling the "
                      "under-ten cell of the 1840 household shape this card was dealt. "
                      "No age in years is written because the schedule counts in bands "
                      "and this project writes no year it cannot read. REVIEW REQUIRED, "
                      "for the reason the head's card gives. No figure is drawn (L1).")))

        card = {
            "id": hid,
            "name": f"The {surname} household — a free Black household of 1835",
            "division": "unplaced",
            "head": pid,
            "source_pass": "reconstructed_underdocumented",
            "underdocumented": {
                "ticket": TICKET,
                "parent": PARENT,
                "stage": STAGE,
                "sub_stage": SUB_STAGE,
                "rule": "the_1833_count_is_the_floor_of_the_1835_bracket",
                "slot": slot,
                "stands_on": FLOOR_RULE,
                "household_shape": shape,
                "withdrawn_if": ("a source naming the free Black residents of Chicago in "
                                 "1835 — the Court of County Commissioners' certificates "
                                 "of freedom above all — which would replace this whole "
                                 "cohort with the men it stands for; or a re-cut of the "
                                 "bracket that no longer puts the floor at this count. "
                                 "The retirement runs through --build, never by hand"),
            },
            "arrival": attribute(None, (
                "NOT DRAWN. The 1833 reading dates an appearance in a courtroom and not "
                "an arrival, and this stage will not invent one. The programme's arrival "
                "stage owns this block and T-1179 is where these cards join it."),
                tier="unknown"),
            "origin": attribute(None, (
                "NOT WRITTEN, AND THE SILENCE IS THE POINT. The corpus says where its "
                "white residents came from and says nothing at all about where any Black "
                "resident of this town came from. Free, freed, born in Illinois or come "
                "up from a slave state — the record does not say, and an origin written "
                "here would be this project answering the one question its sources most "
                "conspicuously do not."), tier="unknown"),
            "lives_at": attribute(None, (
                "Not seated. T-1199 seats the reconstructed households on the lot grid "
                "by the placement policy; this card carries no division because no "
                "reading places a free Black household in one."), tier="unknown"),
            "works_at": attribute(None, (
                "Not seated. The two firms this stage writes carry their keepers; "
                "T-1189 staffs the business layer."), tier="unknown"),
            "present_on_scene_date": attribute(
                "present", ("Present because the floor is carried, not because a draw "
                            "was made. See the rule above."),
                basis={"kind": "rule",
                       "id": "the_1833_count_is_the_floor_of_the_1835_bracket",
                       "note": FLOOR_RULE},
                replaceable={"kind": "household",
                             "match": "a re-cut of the bracket that no longer puts the "
                                      "floor of 1 July 1835 at the August 1833 count"}),
            "persons": persons,
            "touches_removal": False,
            "review_required": True,
            "research_note": (
                f"WRITTEN BY tools/reconstruct_free_black.py ({TICKET}, of {PARENT}), the "
                f"`{SUB_STAGE}` sub-stage of the `{STAGE}` stage of the 1835 resident "
                f"reconstruction programme, under the owner's ruling of 2026-09-17 "
                f"recorded in AGENTS.md. This file is NOT research and is not a mint "
                f"output: data/residents/households/ is re-derived by the mint writers "
                f"and data/residents/index.json is derived from that directory, so a card "
                f"written here lives beside the re-admissions and is overlaid onto the "
                f"scene by tools/compile_scene.py. REVIEW REQUIRED and touches_removal "
                f"FALSE, both deliberate: this is a reconstruction of Black residents and "
                f"not of the removal, and borrowing that flag would borrow the weight of "
                f"a subject this stage is not about. "
                f"docs/RESEARCH/black_chicago_1835.md lists every source read and every "
                f"refusal; docs/LIBERTIES.md carries the trade liberty."),
        }
        cards[hid] = card
        minted.append({
            "household_id": hid,
            "person_id": pid,
            "name": name,
            # The key every consumer of a `minted` list reads — tools/derive_person_community.py
            # walks the reconstruction records by it to find the cards they wrote.
            "file": f"underdocumented/{hid}.json",
            "trade": trade,
            "community": COMMUNITY,
            "review_required": True,
            "touches_removal": False,
            "household_shape": shape,
            "persons": len(persons),
            "slot": slot,
        })
        if trade == "barber":
            firms[f"{FIRM_PREFIX}barbers_shop"] = firm_record(
                f"{FIRM_PREFIX}barbers_shop",
                f"{name}, barber",
                "A barber's shop kept by a free Black resident of the town",
                pid, name, "barber", slot)
        if wife is not None and wife["occupation"]["value"] == WOMANS_TRADE:
            firms[f"{FIRM_PREFIX}washing_and_ironing"] = firm_record(
                f"{FIRM_PREFIX}washing_and_ironing",
                f"{wife['name']}, washing and ironing",
                "A washing and ironing establishment kept by a free Black woman of the "
                "town",
                wife["id"], wife["name"], WOMANS_TRADE, f"{slot}:wife")

    record = {
        "$schema_note": ("DERIVED. Rebuild with tools/reconstruct_free_black.py --build; "
                         "tools/check.sh re-derives it and refuses a differing byte."),
        "id": "chicago_1835_free_black",
        "schema": SCHEMA,
        "ticket": TICKET,
        "parent_ticket": PARENT,
        "stage": STAGE,
        "sub_stage": SUB_STAGE,
        "target_date": SCENE_DATE.isoformat(),
        "generated_by": "tools/reconstruct_free_black.py",
        "not_a_reading": (
            "NOBODY IN THIS FILE IS A PERSON A SOURCE NAMES. The corpus counts free Black "
            "people at Chicago twice and names none of them inside the window. What is "
            "written here is the COUNT, carried, with people drawn from a pool to carry "
            "it — every one of them retired by the first source that names a real free "
            "Black resident of this town."),
        "the_bracket": {
            "floor": {
                "count_of_men": [low, high],
                "written": heads,
                "as_of": "1833-08",
                "source": "andreas_1884_v1",
                "reading": ("Andreas, quoted in data/residents/households/"
                            "hh_caton_john_dean.json: in August 1833 Caton 'defended six "
                            "or seven free coloured men before the Court of County "
                            "Commissioners and obtained certificates of freedom for them, "
                            "his fee a dollar from each.'"),
                "why_the_upper_reading": (
                    "The phrase's two readings differ by one man. The ticket's ask is the "
                    "low end of the bracket AT LEAST, and seven is the reading under "
                    "which the cohort is at or above the floor whichever of the two the "
                    "page means."),
                "why_it_is_a_residence_and_not_a_passage": (
                    "A certificate of freedom was what the Illinois black law made the "
                    "condition of a free Black person's residence in the state. Men "
                    "before the county court for one are men settling, not passing."),
                "rule": FLOOR_RULE,
            },
            "ceiling": ceiling(),
            "what_this_stage_wrote": "the floor",
            "the_head_room_is_left_standing": (
                "Between the floor written here and the ceiling above there is room for "
                "roughly twenty more people. It is not filled, because filling it would "
                "mean inventing them against a share carried back across five years of "
                "the fastest growth this town ever had. A later ticket with a reading in "
                "hand may take it."),
        },
        "the_1840_households": {
            "note": ("SHAPES, NEVER PEOPLE — composition_1840.json's own rule, and this "
                     "stage is held to it. What is read off these lines is how many "
                     "adults and children stood under a free Black roof, not who they "
                     "were."),
            "entirely_free_coloured": entirely,
            "free_coloured_within_a_white_household": mixed,
            "shapes_drawn_from": shapes,
            "shapes_set_aside_because_no_adult_man_stands_in_them": {
                "shapes": shapes_set_aside,
                "why": ("The floor this stage carries counts MEN — Caton's fee counts men "
                        "before the Court of County Commissioners — so every household "
                        "written here is headed by one. The 1840 reading shows a "
                        "free Black household headed by a woman, and dealing that shape "
                        "to a male head would invent the man the page does not show. "
                        "The woman-headed household of this town is real and is NOT "
                        "written here; it is left for a stage whose unit is a household "
                        "rather than a count of men."),
            },
            "the_sample_is_small_and_this_file_says_so": (
                f"{len(shapes)} household(s). It is also every reading of a free Black "
                f"household this corpus holds."),
            "the_recapitulation_leaf_is_excluded": {
                "pages": skipped,
                "why": ("That leaf COUNTS the town instead of enumerating it. Fifteen of "
                        "its lines carry free-coloured cells and not one of them is a "
                        "household; a reader who took them for households would meet the "
                        "same people twice and would read this town as holding five "
                        "times the free Black households it does."),
            },
        },
        "the_naming_stock": {
            "rows": stock["rows"],
            "surnames": stock["surnames"],
            "given_names_printed": stock["given_printed"],
            "attested_readings_no_draw_may_reproduce": stock["attested_readings"],
            "withheld": stock["withheld"],
            "refusals": REFUSALS,
            "note": ("The roster classed these rows R6 on its own "
                     "`community_term_in_the_reading` rule and dated every one of them "
                     "`later_only`. Not one is minted into 1835. The SURNAMES enter the "
                     "pool; the people do not."),
        },
        "the_trades": {
            "dealt": TRADES,
            "the_womans_trade": WOMANS_TRADE,
            "liberty": TRADE_LIBERTY,
        },
        "counts": {
            "households": len(cards),
            "persons": sum(len(c["persons"]) for c in cards.values()),
            "adult_men": heads,
            "adult_women": sum(1 for c in cards.values() for p in c["persons"]
                               if p["relationship"] in ("wife", "household_member")),
            "of_those_wives": sum(1 for c in cards.values() for p in c["persons"]
                                  if p["relationship"] == "wife"),
            "children": sum(1 for c in cards.values() for p in c["persons"]
                            if p["relationship"] == "child"),
            "firms": len(firms),
            "surnames_available": len(surnames),
        },
        "minted": minted,
        "firms": sorted(firms),
        "what_this_stage_does_not_write": [
            "THE FREE BLACK RESIDENTS WHO LIVED UNDER SOMEBODY ELSE'S ROOF. Three of the "
            "1840 leaves enumerate a single free coloured person inside an otherwise "
            "white household — the live-in cook, driver or servant. That person belongs "
            "inside a card data/residents/households/ owns and the mint writers re-derive, "
            "so seating them is T-1179's at the convergence and not this stage's.",
            "A NATION, A BIRTHPLACE OR A ROUTE. See `origin` on every card.",
            "ANY PERSON THE 1840 CENSUS NAMES. The roster dates all seven readings "
            "`later_only` and this stage back-projects none of them.",
        ],
    }
    # T-1489. THE SEAT ANOTHER PASS DREW FOR THESE PEOPLE, CARRIED THROUGH THE REBUILD.
    # `tools/seat_reconstructed_trades_1835.py` points a reconstructed trade-holder with
    # no attested workplace at a house the business layer already holds, and writes the
    # answer onto the person as `persons[].employment`. It runs AFTER this stage, and
    # this stage derives its directory whole and compares it byte for byte — so without
    # this the key would be deleted on the next --build and reported as drift by the
    # pass that wrote it. It is the same fixed-slot carry the four `households/` mints
    # already use for `workplaces`; what the block may CONTAIN is that pass's --check to
    # decide, never this one's.
    carry_seats(cards, CARDS)
    return record, cards, firms


def firm_record(fid, name, what, person_id, person_name, occupation, slot):
    low, high = caton_count()
    return {
        "id": fid,
        "register_id": None,
        "name": name,
        "provenance": "reconstructed",
        "type": ["other"],
        "trade": what,
        "occupation": occupation,
        "goods": [],
        "firm_styles": [],
        "proprietors": [{
            "name": person_name,
            "person_id": person_id,
            "register_person_id": None,
            "role": "proprietor",
            "from": None,
            "to": None,
            "tier": RECONSTRUCTED,
            "basis": ("RECONSTRUCTED, NOT FOUND. No source names a Black-owned business "
                      "at Chicago in 1835 or names anybody who kept one. This firm "
                      "exists because its keeper does: the free Black cohort T-1377 "
                      "writes to the floor of the 1833-1840 bracket is dealt trades, and "
                      "a trade with a premises is a firm. Written by "
                      "tools/reconstruct_free_black.py from slot " + slot + "."),
            "source_id": None,
            "claim_ids": [],
        }],
        "partners": [],
        "staff": [],
        "locations": [{
            "kind": "unplaceable",
            "structure_id": None,
            "street_id": None,
            "face": None,
            "primary": True,
            "from": None,
            "to": None,
            "tier": RECONSTRUCTED,
            "basis": ("Unplaceable, and not for want of looking. No reading in this "
                      "corpus puts a free Black household or business on any street of "
                      "this town, so the record carries its limit rather than a guess."),
            "limit_reason": ("Nothing places this house. The cohort it belongs to is "
                             "unplaced for the same reason — no reading puts a free Black "
                             "household or business on any street of this town — and "
                             "T-1199 seats the reconstructed layer when the placement "
                             "policy is written."),
        }],
        "dates": {
            "opened": None,
            "closed": None,
            "precision": "unbounded",
            "tier": RECONSTRUCTED,
            "basis": ("No opening and no closing. The firm is reconstructed onto the "
                      "scene date and carries no date it cannot read."),
        },
        "evidence": {"first_issue": None, "last_issue": None, "copy_dates": []},
        "present_at_scene_date": True,
        "exclusion": None,
        "exclusion_note": None,
        "proprietor_community": {
            "value": COMMUNITY,
            "tier": RECONSTRUCTED,
            "rule": "proprietors_agree",
            "basis": ("The one keeper this record names is a reconstructed free Black "
                      "resident and the card says so. A house is not its keeper, so the "
                      "reading is an inference about the house and is capped there — and "
                      "under that, at the tier of the person it is read off, which is a "
                      "reconstruction."),
            "from": [{
                "person_id": person_id,
                "name": person_name,
                "role": "proprietor",
                "community": COMMUNITY,
                "tier": RECONSTRUCTED,
            }],
        },
        "customers": [],
        "sources": [],
        "claim_ids": [],
        "liberties": {"survival_required": False, "backdating_required": False},
        "review_required": True,
        "replaceable_by": ("Any source naming a Black-owned business at Chicago in 1835, "
                           "or naming the person who kept one. REVIEW REQUIRED: this is "
                           "a reconstructed Black-owned firm written where the corpus is "
                           "silent, and AGENTS.md's standard holds it for review before a "
                           "scene carrying it may be marked released."),
        # WHAT BOUGHT THIS HOUSE — a DOCUMENTED FLOOR, not a quota row (owner, 2026-09-19).
        # T-1184's contract asks every reconstructed business to name the order-book row
        # that bought it. These two do not fill a modelled shortfall: they stand for a
        # count the corpus makes directly, and the order book holds no barber or
        # washing-and-ironing bucket at all — the programme that would mint one (T-1186)
        # has not run. Naming a bucket here would either spend T-1186's quota before it
        # runs or file documented evidence as an estimate, so compile_businesses.py takes
        # the floor form instead and holds it to its own citation.
        "reconstruction": {
            "programme": "chicago_1835_resident_reconstruction",
            "group": SUB_STAGE,
            "ticket": TICKET,
            "floor": {
                "count": high,
                "of": "free Black men resident at Chicago",
                "as_of": "1833-08",
                "sources": ["andreas_1884_v1"],
                "note": FLOOR_RULE,
                "why_a_firm_and_not_only_a_person": (
                    "The floor is a count of PEOPLE. This record exists because one of "
                    "them keeps a trade with a premises, and a trade with a premises is "
                    "a firm — the trades are dealt under L255 and the firm follows the "
                    "keeper. It is not an order against a shortfall in the business "
                    "model, which is why it names no bucket."),
            },
            "seed": slot,
            "basis": {
                "kind": "rule",
                "id": "the_1833_count_is_the_floor_of_the_1835_bracket",
                "note": FLOOR_RULE,
            },
            "withdrawn_if": (
                "a source naming a Black-owned business at Chicago in 1835 or the person "
                "who kept one; a source naming a free Black resident at a trade, which "
                "retires the trade liberty this firm stands on; or a re-cut of the "
                "bracket that no longer puts the floor at the August 1833 count. The "
                "retirement runs through --build, never by hand."),
        },
    }


# ----------------------------------------------------------------------- writing --

def emit(record, cards, firms, write: bool) -> list:
    drift = []

    def settle(path: Path, payload: dict):
        text = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        elif not path.exists() or path.read_text(encoding="utf-8") != text:
            drift.append(str(path.relative_to(ROOT)))

    settle(OUT, record)
    for hid, card in sorted(cards.items()):
        settle(CARDS / f"{hid}.json", card)
    for fid, firm in sorted(firms.items()):
        settle(FIRMS / f"{fid}.json", firm)

    # Each sub-stage sweeps its OWN prefix out of the shared directory: `hh_um_` is
    # T-1376's and `hh_fb_` is this one's. A sweep of everything would have the two
    # writers deleting each other's cards on alternate builds.
    wanted = {f"{hid}.json" for hid in cards}
    existing = {p.name for p in CARDS.glob(f"{CARD_PREFIX}*.json")} if CARDS.is_dir() else set()
    for stale in sorted(existing - wanted):
        if write:
            (CARDS / stale).unlink()
        else:
            drift.append(f"data/residents/underdocumented/{stale} "
                         f"(committed, no longer derived)")
    wanted_firms = {f"{fid}.json" for fid in firms}
    have = {p.name for p in FIRMS.glob(f"{FIRM_PREFIX}*.json")} if FIRMS.is_dir() else set()
    for stale in sorted(have - wanted_firms):
        if write:
            (FIRMS / stale).unlink()
        else:
            drift.append(f"data/businesses/authored/{stale} (committed, no longer derived)")
    return drift


def build() -> int:
    prog = load_programme()
    if STAGE not in stages(prog):
        print(f"FAIL the programme carries no '{STAGE}' stage", file=sys.stderr)
        return 2
    record, cards, firms = derive()
    emit(record, cards, firms, write=True)
    c = record["counts"]
    print(f"  ok    {c['households']} free Black household(s), {c['persons']} person(s) "
          f"and {c['firms']} firm(s) written")
    return 0


def check() -> int:
    prog = load_programme()
    problems = []

    def error(where, msg):
        problems.append(f"{where}: {msg}")

    record, cards, firms = derive()
    real = layer_names()
    for hid, card in sorted(cards.items()):
        if not card.get("review_required"):
            error(hid, "every card of this sub-stage carries review_required")
        if card.get("touches_removal") is not False:
            error(hid, "touches_removal is FALSE here on purpose; this is not the removal")
        for person in card["persons"]:
            check_reconstructed_person(f"{hid}:{person['id']}", person,
                                       set(stages(prog)), error)
            if person["reconstruction"].get("community") != COMMUNITY:
                error(hid, f"a card of this sub-stage must carry community `{COMMUNITY}`")
            if not person["id"].startswith(PERSON_PREFIX):
                error(hid, f"every person here is invented and wears `{PERSON_PREFIX}`")
            if " ".join(person["name"].split()).lower() in real:
                error(hid, f"the invented name {person['name']!r} is borne by a real "
                           f"person of this layer")
            prose = person.get("note") or ""
            if "REVIEW REQUIRED" not in prose:
                error(hid, "a flagged record says why in its own words and names the "
                           "subject it is held for (AGENTS.md)")
    pool = next((c for c in load(POOLS)["communities"] if c["id"] == POOL_ID), None)
    stock = naming_stock()
    if sorted(pool["surnames"]) != stock["surnames"]:
        error("1835_invented_name_pools.json",
              f"the `{POOL_ID}` pool's surnames {sorted(pool['surnames'])} are not the "
              f"ones the roster's R6 `black` rows actually print {stock['surnames']} — "
              f"the pool is a restatement of that reading and may not drift from it")
    floor = record["the_bracket"]["floor"]
    if record["counts"]["adult_men"] < floor["count_of_men"][0]:
        error("the_bracket", "the cohort stands below the floor it was written to")
    for drifted in emit(record, cards, firms, write=False):
        error(drifted, "does not re-derive; run --build")
    if problems:
        for p in problems:
            print(f"  FAIL {p}")
        return 1
    c = record["counts"]
    print(f"  ok    {c['households']} free Black household(s) and {c['persons']} person(s) "
          f"re-derive, every one review_required with its own sentence")
    print(f"  ok    {c['firms']} Black-owned firm(s) re-derive, each read off its keeper")
    print(f"  ok    the cohort stands at or above the floor of the bracket "
          f"({floor['count_of_men'][0]}-{floor['count_of_men'][1]} men, August 1833)")
    return 0


def report() -> int:
    record, cards, firms = derive()
    b = record["the_bracket"]
    print(f"{record['id']} — {TICKET}, stage `{STAGE}` / `{SUB_STAGE}`")
    print(f"  floor   {b['floor']['count_of_men']} men, {b['floor']['as_of']} — "
          f"{b['floor']['written']} written")
    print(f"  ceiling {b['ceiling']['persons_at_the_same_share']} persons "
          f"({b['ceiling']['persons_at_the_same_share_over_the_range']} over the range), "
          f"from {b['ceiling']['free_coloured_persons_1840']} of "
          f"{b['ceiling']['persons_1840']} in 1840")
    h = record["the_1840_households"]
    print(f"  1840    {len(h['entirely_free_coloured'])} entirely free-coloured "
          f"household(s), {len(h['free_coloured_within_a_white_household'])} free "
          f"coloured person(s) inside a white one; recapitulation leaf excluded: "
          f"{h['the_recapitulation_leaf_is_excluded']['pages']}")
    print(f"  pool    {record['the_naming_stock']['surnames']}")
    c = record["counts"]
    print(f"  wrote   {c['households']} household(s), {c['persons']} person(s) "
          f"({c['adult_men']} men, {c['adult_women']} women of whom "
          f"{c['of_those_wives']} are wives, {c['children']} children), "
          f"{c['firms']} firm(s)")
    for m in record["minted"]:
        print(f"    {m['name']:24} {m['trade']:12} {m['persons']} person(s)")
    for fid in record["firms"]:
        print(f"    firm  {fid}  {firms[fid]['name']}")
    return 0


def self_test() -> int:
    failures = []

    def case(name, ok):
        print(f"  {'ok   ' if ok else 'FAIL '} {name}")
        if not ok:
            failures.append(name)

    low, high = caton_count()
    case("the floor is parsed from the Caton card and not typed here",
         (low, high) == (6, 7))

    entirely, mixed, skipped = free_coloured_households()
    case("the recapitulation leaf is excluded, and it is exactly one leaf",
         len(skipped) == 1)
    recap = [p for p in PAGES.glob("*.json") if is_recapitulation(load(p))]
    recap_rows = sum(1 for p in recap for r in load(p).get("records") or []
                     if any(k.startswith("fc_") and v
                            for k, v in (r.get("cells") or {}).items()))
    case("and excluding it is not cosmetic — it carries free-coloured lines that are "
         "not households", recap_rows > len(entirely))
    case("an entirely free-coloured household carries no free-white cell",
         all(r["free_white"] == 0 for r in entirely))
    case("a mixed household does", all(r["free_white"] > 0 for r in mixed))

    stock = naming_stock()
    pool = next(c for c in load(POOLS)["communities"] if c["id"] == POOL_ID)
    case("the committed pool's surnames are exactly the ones the roster's rows print",
         sorted(pool["surnames"]) == stock["surnames"])
    case("and `Eliza Askie` is in it, which reading the roster's `normalised` is not",
         "Askie" in stock["surnames"]
         and any(r["normalised"] == "eliza as ie" for r in stock["rows"]))
    case("an unread surname position is refused",
         any(w["reason"] == "the_surname_is_not_settled_on_the_page"
             for w in stock["withheld"]))
    case("a bracketed forename is refused while its whole surname is kept",
         any(w["reason"] == "the_given_name_carries_an_unread_position"
             for w in stock["withheld"])
         and "Anderson" in stock["surnames"])
    case("every refusal recorded names a reason this file states",
         all(w["reason"] in REFUSALS for w in stock["withheld"]))

    town = layer_given_names()
    printed_given = [g.lower() for g in stock["given_printed"]]
    case("EVERY given name the 1840 free-coloured block prints is already borne by a "
         "real person of this town — which is why the pool's given list is the town's",
         bool(printed_given) and all(g in town for g in printed_given))

    record, cards, firms = derive()
    printed = {r.lower() for r in stock["attested_readings"]}
    drawn = {" ".join(p["name"].split()).lower()
             for c in cards.values() for p in c["persons"]}
    case("no drawn name reproduces a reading the 1840 page prints",
         not (drawn & printed))
    case("and none shares a reading's surname-and-initial key either",
         not ({name_key(n) for n in drawn} & {name_key(r) for r in printed}))
    case("no drawn name is borne by a real person of this layer",
         not (drawn & layer_names()))
    case("every person is invented and wears the invented prefix",
         all(p["id"].startswith(PERSON_PREFIX)
             for c in cards.values() for p in c["persons"]))
    case("every card is review_required and touches_removal is false",
         all(c["review_required"] and c["touches_removal"] is False
             for c in cards.values()))
    case("no card writes an origin",
         all(c["origin"]["value"] is None for c in cards.values()))
    case("the cohort stands at or above the floor",
         record["counts"]["adult_men"] >= low)
    case("and every person written is accounted for by a relationship",
         record["counts"]["persons"] == (record["counts"]["adult_men"]
                                         + record["counts"]["adult_women"]
                                         + record["counts"]["children"]))
    case("and below the ceiling the 1840 share carries back",
         record["counts"]["persons"]
         <= record["the_bracket"]["ceiling"]["persons_at_the_same_share"])
    case("every household shape came off an entirely free-coloured 1840 household",
         all(m["household_shape"]["page"] in {r["page"] for r in entirely}
             for m in record["minted"]))
    case("and every card holds exactly as many people as its shape counts",
         all(m["persons"] == m["household_shape"]["persons"] for m in record["minted"]))
    case("every shape dealt has an adult man in it, because the floor counts men",
         all(m["household_shape"]["adult_men"] >= 1 for m in record["minted"]))
    case("each firm reads its community off the keeper it names",
         all(f["proprietor_community"]["value"] == COMMUNITY
             and [r["person_id"] for r in f["proprietor_community"]["from"]]
             == [p["person_id"] for p in f["proprietors"]]
             for f in firms.values()))
    case("the trade liberty is on the face of every card that was dealt one",
         all("LIBERTY" in json.dumps(p["occupation"])
             for c in cards.values() for p in c["persons"]
             if p["occupation"]["value"] not in ("none_recorded", None)))

    if failures:
        print(f"  {len(failures)} case(s) failed")
        return 1
    print(f"  ok    26 rule(s) hold")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
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
    raise SystemExit(main())
