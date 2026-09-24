#!/usr/bin/env python3
"""T-1347 (of T-1173), stage `trade_households` — the town's mechanics and labourers.

    python3 tools/reconstruct_trade_households.py --build      draw them, write the cards
    python3 tools/reconstruct_trade_households.py --check      re-derive and refuse drift
    python3 tools/reconstruct_trade_households.py --report     who was drawn, against what
    python3 tools/reconstruct_trade_households.py --self-test  the rules, each refusing its case

WHAT THIS STAGE IS. The order book carries twenty-four buckets whose axis reads
`family/trade` — an adult in a family household who works at something — and every one of
them is short. 308 people across the three civil divisions, 197 men and 111 women, and no
roster of 1835 Chicago prints them: the letter lists name merchants and the subscription
rolls name subscribers, and the men who dug the harbour and drove the drays and the women
who kept the boarding houses and sewed for the town were never written down. This stage
draws them as HEADS OF THEIR OWN HOUSEHOLDS, each with a trade, a name from the pools, an
age band from the bucket that ordered them. No arrival: that table is computed over the
scene these cards are overlaid into, so drawing from it here would move the table that drew
them, and the research layer's own arrival fills (T-1169) re-derive from it.

WHERE THE TRADES COME FROM, AND WHAT IS NOT DONE WITH THEM. T-1346 counted every printed
trade in the Fergus 1839 directory against this project's controlled vocabulary — 1,377
mapped entries over 88 trades — and that table is the only per-trade share the corpus
yields. The table's own `how_to_use_it` says what this stage does with it: draw from
`rows`, renormalised over the trades being drawn for, and never write a trade whose
`in_vocabulary` is false. The 1839 shape is FOUR YEARS LATE and this stage does not hide
that: it is the shape of the town the same people built, read back onto the year they
were building it, and the ledger says so beside every count.

FOUR REFUSALS, EACH ONE WRITTEN RATHER THAN QUIETLY TAKEN.

  1. NO SENIORITY RULE. T-1173's rules sketched "labourers young, master tradesmen
     older", and this stage does not take it. The 1839 table carries no ages and the 1840
     schedule carries no trades, so nothing in this corpus prices the association; a
     seniority curve drawn here would be a liberty invented to make a table look like a
     town. Each trade is dealt across the age bands in proportion to the bands the order
     book actually ordered, and the master/journeyman split is T-1183's, which is the
     ticket that models how a business was staffed.

  2. NO KIN. Every drawn head is owed a family — the 1840 size histogram says a Chicago
     household of that year held 4.4 people — and this stage writes the size it is owed
     onto the card and seats nobody in it. The kin of a family household are
     `family/none` in the order book and that quota is T-1174's and T-1171's, not this
     stage's: drawing them here would order the same 930 women and children twice, which
     is the one arithmetic the book exists to prevent. `household_owed` carries the drawn
     size, the seed that drew it and the ticket that seats it.

  3. NO ARRIVAL. The arrival model's `arrival_year_of_the_known_layer` is derived from the
     compiled scene and the scene carries these cards, so an arrival written here moves the
     table that drew it — and T-1169's fills over 1,440 research cards re-derive from that
     table, so the whole research layer would move under a stage that is not supposed to
     touch it. The block says so and names the stage that owns it.

  4. NO TRADE PAST ITS CEILING. Where the December 1835 State census counts a class one
     person keeps — fourteen physicians, twenty-two lawyers, four druggists — the town
     model's own `against_the_state_census` table says how many more the town is short,
     and this stage may not draw past that number. A class the town already matches draws
     nobody. The count a ceiling refuses is not lost: it falls to the RESIDUAL trade, and
     the ledger prints the arithmetic rather than absorbing it.

THE RESIDUAL. Day labour for the men and domestic service for the women. Neither is an
establishment, so neither is enumerated by a census that counts stores and shops, and
neither advertises, subscribes or signs; they are the work the record cannot see, and a
model that let the directory's shares stand unadjusted would give this town more printers
than labourers. The residual is where the ceilings' refusals go and where the rounding
remainder goes, and the ledger states it as a number, not as a rule.

WHERE THE CARDS LIVE. `data/residents/reconstructed_trades/`, beside T-1172's
`readmitted/` and for the same reason: `data/residents/households/` is re-derived by the
research mints and `data/residents/index.json` is derived from that directory, so a
reconstruction that is not a reading lives outside both and is overlaid onto the scene by
`tools/compile_scene.py`. Nothing here reaches back into a research card.

EVERY VALUE IS REPRODUCIBLE. Nothing is random: each value comes from `blake2s(seed)` over
a seed a reader can retype, and the seed is printed on the record that carries the value.
`--check` re-derives the whole directory and refuses a single differing byte.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resident_mint_carry import carry_seats  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESIDENTS = ROOT / "data" / "residents"
HOUSEHOLDS = RESIDENTS / "households"
READMITTED = RESIDENTS / "readmitted"
MINTED = RESIDENTS / "reconstructed_trades"
MODEL = ROOT / "data" / "reconstruction" / "1835_town_model.json"
POOLS = ROOT / "data" / "reconstruction" / "1835_invented_name_pools.json"
BOOK = ROOT / "data" / "reconstruction" / "1835_reconstruction_order_book.json"
TRADE_TABLE = ROOT / "data" / "research" / "directories" / "fergus_1839_trade_table.json"
LEDGER = ROOT / "data" / "reconstruction" / "1835_trade_households.json"

STAGE = "trade_households"
TICKET = "T-1347"
PARENT = "T-1173"
PROGRAMME_ID = "chicago_1835_resident_reconstruction"
SCENE_DATE = "1835-07-01"
SCENE_YEAR = 1835
RECONSTRUCTED = "reconstructed"
PREFIX = "rc_"
SOURCE_PASS = "reconstructed_trade_household"

# The residual trade of each sex — the work the record cannot see. See the docstring.
RESIDUAL = {"male": "labourer", "female": "domestic"}

# A woman's trade set. Every term is in `vocabulary.occupations`, and every one of them is
# here because THIS LAYER'S OWN WOMEN are recorded at it or because the reconstruction
# programme names it as women's work. The six the layer records — tavern_keeper,
# refectory_keeper, schoolteacher, boarding_house_keeper, dressmaker, hardware_merchant —
# are the evidence that a woman of this town kept her own house at her own trade; the
# three the programme names — laundress, domestic, milliner — are the trades T-1174's own
# title lists and that no 1835 roster would ever have printed. A woman is not drawn into a
# trade this project has no woman at: that would be a claim about who did what, made by a
# model, on no evidence at all.
WOMENS_TRADES = {
    "boarding_house_keeper": "the layer records a woman keeping a boarding house",
    "domestic": "the programme names domestic service as women's work; the residual",
    "dressmaker": "the layer records a woman at it",
    "hardware_merchant": "the layer records a woman at it — a widow keeping the store on",
    "laundress": "the programme names it, and the name pools carry a weighting for it",
    "milliner": "the vocabulary's own women's trade beside dressmaker",
    "refectory_keeper": "the layer records a woman keeping a refectory",
    "schoolteacher": "the layer records a woman teaching",
    "tavern_keeper": "the layer records two women keeping taverns",
}

# A trade this stage may never write onto a civil-division head, and why. TWO KINDS, and
# neither is a ceiling: a ceiling is a number and these are categorical.
#
#   THE GARRISON'S. The order book's own method says the fort "is read, not apportioned" —
#   T-1176 reads the post return and T-1349 musters the companies — so a soldier, an army
#   officer, a post surgeon or a chaplain drawn into the south division would be a man the
#   garrison already holds, counted twice and in the wrong place.
#
#   THE TOWN'S SINGULAR OFFICES. There was one sheriff of Cook County, one postmaster, one
#   Indian agent, one lighthouse keeper, one receiver and one register at the land office.
#   The civic mint already names the man in each, from the record; drawing a second is not
#   filling a gap in the evidence, it is inventing a second sheriff.
#
# A trade refused here is not lost: it never enters the deal, so its share falls to the
# rest of the set and the ledger prints the list with its reasons.
REFUSED_TRADES = {
    "army_officer": "the garrison's — the fort is read, not apportioned (T-1176, T-1349)",
    "army_surgeon": "the garrison's — the fort is read, not apportioned (T-1176, T-1349)",
    "chaplain": "the garrison's — the fort is read, not apportioned (T-1176, T-1349)",
    "soldier": "the garrison's — the fort is read, not apportioned (T-1176, T-1349)",
    "county_clerk": "a singular county office the civic mint already names",
    "harbour_agent": "a singular federal office the civic mint already names",
    "indian_agent": "a singular federal office the civic mint already names",
    "land_office_receiver": "a singular federal office the civic mint already names",
    "land_office_register": "a singular federal office the civic mint already names",
    "lighthouse_keeper": "a singular federal office the civic mint already names",
    "postmaster": "a singular federal office the civic mint already names",
    "public_administrator": "a singular county office the civic mint already names",
    "sheriff": "a singular county office the civic mint already names",
    "sub_agent": "a singular federal office the civic mint already names",
}

# A person-trade whose ceiling the December 1835 State census sets, and the class it is
# counted under. ONE PERSON KEEPS ONE OF THESE, so the establishment count IS a person
# count: fourteen physicians is fourteen physicians. A trade not named here has no census
# ceiling, because the class it would fall under counts premises and not people — forty-
# four stores were kept by more than forty-four men, and reading that line as a person
# ceiling would shrink the town's commerce to its shop fronts.
CENSUS_CEILINGS = {
    "physician": "physician",
    "attorney": "lawyer",
    "druggist": "druggist",
    "printer": "printing_office",
    "schoolteacher": "school",
    "tavern_keeper": "tavern",
    "brewer": "brewery",
    "silversmith": "silversmith_jeweller",
    "jeweller": "silversmith_jeweller",
    "founder": "iron_foundry",
    "bookseller": "book_store",
}

# The order book's own six bands.
BOOK_BANDS = (("under_10", 0, 10), ("10_19", 10, 20), ("20_29", 20, 30),
              ("30_39", 30, 40), ("40_49", 40, 50), ("50_plus", 50, None))
BAND_EDGES = {"20_29": (20, 29), "30_39": (30, 39), "40_49": (40, 49), "50_plus": (50, None)}


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


def allocate(total: int, weights: list) -> dict:
    """Largest remainder, ties broken on the key. The order book's own `rounding` rule,
    so two builds on one set of inputs are byte-identical and no count is a float."""
    total = int(total)
    if total <= 0:
        return {}
    mass = float(sum(w for _, w in weights))
    if mass <= 0:
        return {}
    exact = [(key, total * float(w) / mass) for key, w in weights]
    out = {key: int(value) for key, value in exact}
    short = total - sum(out.values())
    order = sorted(exact, key=lambda kv: (-(kv[1] - int(kv[1])), str(kv[0])))
    for index in range(short):
        out[order[index % len(order)][0]] += 1
    return {k: v for k, v in out.items() if v}


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def value_of(block):
    return block.get("value") if isinstance(block, dict) else block


# ------------------------------------------------------------------ the inputs --

def model() -> dict:
    return json.loads(MODEL.read_text(encoding="utf-8"))


def table(section_key: str, table_key: str) -> dict:
    for section in model()["sections"]:
        if section["key"] == section_key:
            return section["tables"][table_key]
    raise SystemExit(f"the town model carries no {section_key}.{table_key}")


def trade_rows() -> list:
    """The 1839 directory's trades this project may write onto a person: the mapped rows
    whose term the 1835 controlled vocabulary carries. The table's own instruction."""
    doc = json.loads(TRADE_TABLE.read_text(encoding="utf-8"))
    return [(r["trade"], int(r["count"])) for r in doc["rows"]
            if r.get("in_vocabulary") and r["trade"] not in REFUSED_TRADES]


def ceilings() -> dict:
    """trade -> how many more people of that trade the December census leaves room for.
    A class the town already matches or exceeds leaves room for nobody — and NEITHER DOES
    A CLASS WHOSE SHORTFALL THE SOURCES ALREADY ACCOUNT FOR (T-1428). The December return
    was taken two to five months after the scene, and the register names houses whose
    OPENING was announced after 1 July: each of those stands behind one of the December
    figures while honestly standing outside the July town. Counting them as room would
    deal a reconstructed keeper against a gap two dated notices fill by name — the
    seven schools, of which the town holds five and Everts and Hunt opened in August."""
    by_class = {r["class"]: r for r in table("occupations", "against_the_state_census")["rows"]}
    out = {}
    for trade, klass in sorted(CENSUS_CEILINGS.items()):
        row = by_class.get(klass)
        if row is None:
            continue
        if "opened_after_the_scene_date" not in row:
            raise SystemExit(
                f"the town model's {klass!r} row does not say how many of its houses opened "
                "after the scene date, so a shortfall cannot be told from room. "
                "Re-run tools/model_town_1835.py --build.")
        out[trade] = max(0, int(row["census_count"]) - int(row["town_at_scene_date"])
                         - int(row["opened_after_the_scene_date"]))
    return out


def size_rows() -> list:
    rows = table("households_and_families", "size_histogram_1840")["rows"]
    return [(int(r["size"]), int(r["households"])) for r in rows if int(r["size"]) >= 1]


def pools() -> dict:
    return json.loads(POOLS.read_text(encoding="utf-8"))


def vocabulary() -> set:
    """The controlled occupation words. The 1839 table's own bound: a term this file does
    not carry may not be written onto a person, whatever a directory printed."""
    index = json.loads((RESIDENTS / "index.json").read_text(encoding="utf-8"))
    return set(index["vocabulary"]["occupations"])


def buckets() -> list:
    """(key, sex, band, division, capacity) for every `family/trade` bucket the book
    orders. THIS STAGE'S OWN FILLS ARE ADDED BACK, for T-1171's reason: a draw that read
    its own previous answer as a spent quota would draw fewer people on the second build
    than on the first, and `--check` may not tolerate that."""
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    ours = Counter()
    for entry in book.get("fills") or []:
        if entry.get("ticket") == TICKET:
            ours[entry.get("bucket")] += int(entry.get("records") or 0)
    out = []
    for family in book["bucket_families"]:
        if family["key"] != "persons":
            continue
        for bucket in family["buckets"]:
            axes = bucket["axes"]
            if axes.get("household_type") != "family" or axes.get("trade") != "trade":
                continue
            todo = bucket.get("to_reconstruct")
            if todo is None:
                continue
            capacity = int(todo) - int(bucket.get("filled") or 0) + ours[bucket["key"]]
            out.append((bucket["key"], axes["sex"], axes["age_band"],
                        axes["division"], max(0, capacity)))
    return sorted(out)


def layer() -> tuple:
    """(every name in the layer, the names REAL people bear, every person id).

    THREE SETS, BECAUSE THEY DO THREE JOBS. The programme's collision check is that an
    invented name may never be an ATTESTED OR INFERRED person's name — a reader who met
    the name as a finding would meet it again as an invention. The other two are weaker
    and still necessary: a name another reconstruction already drew is avoided where the
    pools allow it, and an ID another stage already used may NEVER be reused, because an
    id that names two people is not an id. T-1174 writes its female-headed households
    into `households/` and draws from the same pools, so both of those are live.
    """
    all_names, real, ids = set(), set(), set()
    for directory in (HOUSEHOLDS, READMITTED):
        if not directory.exists():
            continue
        for path in sorted(directory.glob("hh_*.json")):
            card = json.loads(path.read_text(encoding="utf-8"))
            for person in card.get("persons") or []:
                name = " ".join(str(person.get("name") or "").split()).lower()
                pid = str(person.get("id") or "")
                if pid:
                    ids.add(pid)
                if not name:
                    continue
                all_names.add(name)
                if person.get("grade") != RECONSTRUCTED:
                    real.add(name)
    return all_names, real, ids


# ------------------------------------------------------------------- the plan --

def trade_plan() -> dict:
    """sex -> {trade: heads}. Shares from the 1839 table, ceilings from the December
    census, the remainder to the residual. Pure arithmetic — nothing is drawn here."""
    rows = dict(trade_rows())
    caps = ceilings()
    per_sex = Counter()
    for _key, sex, _band, _division, capacity in buckets():
        per_sex[sex] += capacity

    out = {}
    workings = {}
    for sex in sorted(per_sex):
        residual = RESIDUAL[sex]
        if sex == "female":
            weights = [(trade, rows.get(trade, 0) or 1) for trade in sorted(WOMENS_TRADES)]
            reason = ("the trades this layer's own women are recorded at, and the three the "
                      "programme names, weighted by the 1839 directory's count where the "
                      "table carries the row and by one where it does not — a trade the "
                      "directory never printed for anyone is not thereby impossible, it is "
                      "unprinted, and it draws at the table's floor")
        else:
            weights = [(trade, count) for trade, count in sorted(rows.items())]
            reason = ("every mapped 1839 trade the 1835 vocabulary carries, at its own "
                      "printed count, renormalised over the set")
        planned = allocate(per_sex[sex], weights)
        refused = {}
        for trade in sorted(planned):
            ceiling = caps.get(trade)
            if ceiling is None or planned[trade] <= ceiling:
                continue
            refused[trade] = planned[trade] - ceiling
            planned[trade] = ceiling
            if not planned[trade]:
                del planned[trade]
        moved = sum(refused.values())
        if moved:
            planned[residual] = planned.get(residual, 0) + moved
        out[sex] = dict(sorted(planned.items()))
        workings[sex] = {
            "heads_ordered": per_sex[sex],
            "weighted_by": reason,
            "residual_trade": residual,
            "refused_by_a_census_ceiling": dict(sorted(refused.items())),
            "moved_to_the_residual": moved,
            "residual_total": planned.get(residual, 0),
        }
    return {"by_sex": out, "workings": workings, "ceilings": dict(sorted(caps.items()))}


def deal() -> list:
    """The slots, in order: (bucket, sex, band, division, trade, n). Each trade is spread
    across that sex's buckets in proportion to what each bucket ordered — the refusal of
    a seniority rule, done as arithmetic rather than asserted in a comment."""
    plan = trade_plan()
    by_sex = defaultdict(list)
    for key, sex, band, division, capacity in buckets():
        if capacity:
            by_sex[sex].append((key, band, division, capacity))

    slots = []
    for sex in sorted(by_sex):
        weights = [(key, capacity) for key, _band, _division, capacity in by_sex[sex]]
        room = {key: capacity for key, capacity in weights}
        assigned = defaultdict(list)
        # Deal the largest trades first, so the rounding remainder of a big trade does not
        # get pushed into a bucket a small one has already filled.
        for trade, total in sorted(plan["by_sex"][sex].items(), key=lambda kv: (-kv[1], kv[0])):
            share = allocate(total, [(k, room[k]) for k, _c in weights if room[k]])
            spill = total
            for key in sorted(share):
                take = min(share[key], room[key])
                if take:
                    assigned[key].append((trade, take))
                    room[key] -= take
                    spill -= take
            # Whatever a bucket could not hold goes to the buckets that still have room,
            # in bucket-key order. The town's quota is the bound, never a trade's share.
            for key, _band, _division, _capacity in by_sex[sex]:
                if spill <= 0:
                    break
                take = min(spill, room[key])
                if take:
                    assigned[key].append((trade, take))
                    room[key] -= take
                    spill -= take
        for key, band, division, _capacity in by_sex[sex]:
            index = 0
            for trade, count in sorted(assigned[key]):
                for _ in range(count):
                    index += 1
                    slots.append((key, sex, band, division, trade, index))
    return slots


# ---------------------------------------------------------------- the drawing --

def community_for(trade: str, slot_seed: str, pool: dict) -> dict:
    weights = pool["trade_weights"].get(trade) or pool["trade_weights"]["_default"]
    by_id = {c["id"]: c for c in pool["communities"]}
    weighted = [(by_id[k], v) for k, v in sorted((weights.get("weights") or {}).items())
                if k in by_id]
    if not weighted:
        weighted = [(by_id["yankee"], 1)]
    return pick(f"{slot_seed}:name_pool_community", weighted)


def step_past(seed: str, names: list, taken: set) -> str:
    """A name from the pool, stepping past one already borne. Deterministic."""
    start = draw(seed) % len(names)
    for offset in range(len(names)):
        candidate = names[(start + offset) % len(names)]
        if candidate.lower() not in taken:
            return candidate
    return names[start]


def band_block(band: str, seed: str) -> dict:
    low, high = BAND_EDGES[band]
    return {
        "value": f"{low}-{high}" if high is not None else f"{low}+",
        "low": low,
        "high": high,
        "confidence": RECONSTRUCTED,
        "tier": RECONSTRUCTED,
        "basis": {
            "kind": "model",
            "id": "1835_reconstruction_order_book",
            "note": f"The bucket that ordered this person is {band}; the band is the "
                    f"order, not a draw. Nothing here is a reading of anybody's age.",
        },
        "seed": seed,
        "replaceable_by": {
            "kind": "person",
            "match": "a source that states this person's age or their birth year",
        },
        "note": "AN AGE BAND, NEVER A YEAR. The order book counts in the 1840 schedule's "
                "bands and this project writes no year it cannot read.",
    }


def card_for(slot, pool, sizes, caps, taken_names: set, taken_ids: set) -> dict:
    bucket, sex, band, division, trade, index = slot
    slot_id = f"{STAGE}:{bucket}:{trade}:{index:03d}"
    community = community_for(trade, slot_id, pool)
    surnames = community["surnames"]
    givens = community["given_male" if sex == "male" else "given_female"]
    # THE WHOLE POOL IS SEARCHED, NOT ONE DRAW AND ONE RETRY. The draw picks where in the
    # two lists to start; the search then steps through every (surname, forename) pair
    # from there and takes the first whose full name nobody in the layer bears and whose
    # id nobody holds. A single retry is what lets `Mary Burke` be drawn twice — once
    # here and once by T-1174, which draws its Irish laundresses from this same pool.
    first = draw(f"{slot_id}:surname")
    second = draw(f"{slot_id}:forename")
    surname = surnames[first % len(surnames)]
    given = givens[second % len(givens)]
    for step_s in range(len(surnames)):
        candidate_surname = surnames[(first + step_s) % len(surnames)]
        for step_g in range(len(givens)):
            candidate_given = givens[(second + step_g) % len(givens)]
            full = f"{candidate_given} {candidate_surname}"
            pid = f"{PREFIX}{candidate_surname.lower()}_{candidate_given.lower()}"
            if full.lower() not in taken_names and pid not in taken_ids:
                surname, given = candidate_surname, candidate_given
                break
        else:
            continue
        break
    name = f"{given} {surname}"
    # Every pair in the pool spoken for is possible and is not a failure: the programme's
    # id scheme carries it on the suffix, and the NAME may then repeat another
    # reconstruction's — never a real person's, which the contract check proves separately.
    base = f"{PREFIX}{surname.lower()}_{given.lower()}"
    pid, suffix = base, 1
    while pid in taken_ids:
        suffix += 1
        pid = f"{base}_{suffix}"
    taken_ids.add(pid)
    taken_names.add(name.lower())

    size = pick(f"{slot_id}:household_size", sizes)
    ceiling = caps.get(trade)

    person = {
        "id": pid,
        "name": name,
        "relationship": "head",
        "grade": RECONSTRUCTED,
        "sex": sex,
        "age_band": band_block(band, f"{slot_id}:age_band"),
        "occupation": {
            "value": trade,
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "model",
                "id": "fergus_1839_trade_table",
                "note": (f"Dealt, not drawn. The order book ordered {bucket.rsplit('/', 3)[0]}"
                         f"-class adults at a trade in the {division} division, and the "
                         f"1839 directory's share of {trade} over the trades this stage "
                         f"draws for decides how many of them work at it. The 1839 volume "
                         f"is four years after the scene and its shape is read back onto "
                         f"1835 knowingly."
                         + (f" The December 1835 State census leaves room for {ceiling} "
                            f"more of this trade and this stage did not draw past it."
                            if ceiling is not None else "")),
            },
            "seed": f"{slot_id}:trade_deal",
            "replaceable_by": {
                "kind": "person",
                "match": "a source naming a person of this trade in this division, which "
                         "would spend this slot on a real name instead",
            },
            "note": "NO ROLE ROW. `roles[]` is the canonical record of a trade and its "
                    "generator reads the research mints' directory, which this one is "
                    "deliberately outside of; the convergence stage (T-1179) is where "
                    "these cards join that tree. Nothing about this trade is dated.",
        },
        "name_basis": {
            "value": name,
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "model",
                "id": "1835_invented_name_pools",
                "note": f"Both parts are drawn from the {community['label']} pool, which is "
                        f"seeded from the attested residents of this town. The pool is "
                        f"chosen by the weighting the pools file carries for {trade}.",
            },
            "seed": f"{slot_id}:forename",
            "replaceable_by": {
                "kind": "person",
                "match": "a source naming a real person of this trade and division",
            },
            "note": "AN INVENTED NAME, AND IT IS NEVER EVIDENCE. No source names this "
                    "person. The name exists so a reader can tell one drawn head from "
                    "another, and it is checked against every real name in the layer.",
        },
        "basis": {
            "kind": "model",
            "id": "1835_reconstruction_order_book",
            "note": f"The book's bucket {bucket} ordered this person: the town model's "
                    f"employed-persons figure, cut by sex, age band and division, less "
                    f"everyone the sources already name there.",
        },
        "seed": f"{slot_id}:trade_deal",
        "replaceable_by": {
            "kind": "person",
            "match": "a source naming a resident of this trade, sex, age band and "
                     "division, who would stand in this slot instead",
        },
        "reconstruction": {
            "stage": STAGE,
            "programme": PROGRAMME_ID,
            "community": community["id"],
            "review_required": False,
        },
        "resident_subtype": "reconstructed_trade_head",
        "note": "RECONSTRUCTED, NOT FOUND. Nobody is named by any source here. This person "
                "exists because the town model says the town of 1 July 1835 employed more "
                "people than its rosters print, and the whole of what is claimed is that: "
                f"an adult of this sex and band, in the {division} division, at {trade}. "
                "The trade is dealt from the 1839 directory's shares and the person is "
                "reproducible from the seeds printed above. A real name retires them. No "
                "figure is drawn (L1).",
    }

    hid = f"hh_{pid}"
    return {
        "id": hid,
        "name": f"The {surname} household — a trade the rosters never printed",
        "division": division,
        "head": pid,
        "source_pass": SOURCE_PASS,
        "trade_household": {
            "ticket": TICKET,
            "parent_ticket": PARENT,
            "stage": STAGE,
            "bucket": bucket,
            "slot": slot_id,
            "trade": trade,
            "stands_on": "The order book's `family/trade` bucket for this sex, band and "
                         "division is short by the number of people this stage drew, and "
                         "the 1839 trade table is the only per-trade share the corpus "
                         "yields.",
            "withdrawn_if": "a source naming a real resident of this trade and division, "
                            "or a re-cut of the order book that no longer orders this "
                            "bucket; the retirement runs through --build, never by hand",
        },
        "household_owed": {
            "size_drawn": size,
            "kin_seated": 1,
            "seed": f"{slot_id}:household_size",
            "seated_by": "T-1174 (women and children), T-1175 (lodgers), T-1179 (converge)",
            "note": "THE FAMILY THIS HEAD IS OWED, AND NOT SEATED HERE. The 1840 size "
                    "histogram drew this house at %d people. Its kin are `family/none` in "
                    "the order book and that quota belongs to T-1174 and T-1171; seating "
                    "them here would order the same people twice." % size,
        },
        "arrival": {
            "value": None,
            "confidence": RECONSTRUCTED,
            "tier": "unknown",
            "note": "NOT DRAWN HERE, AND THE REASON IS A CIRCLE. The arrival model's own "
                    "distribution — `arrival_year_of_the_known_layer` — is computed over "
                    "the compiled scene, and the scene carries these cards; an arrival "
                    "written here would move the table that drew it, and the research "
                    "layer's own arrival fills (T-1169) re-derive from that table. The "
                    "programme's arrival stage owns this block, and T-1179 is where these "
                    "cards join the tree it runs over.",
            "seated_by": "T-1169 (the arrival fill), T-1179 (converge)",
        },
        "lives_at": {
            "value": None,
            "confidence": RECONSTRUCTED,
            "tier": "unknown",
            "note": "Not seated. T-1199 seats the reconstructed households on the lot "
                    "grid by the placement policy; the division above is the bucket's.",
        },
        "works_at": {
            "value": None,
            "confidence": RECONSTRUCTED,
            "tier": "unknown",
            "note": "Not seated. T-1189 staffs the businesses, and the business band "
                    "(T-1184 … T-1188) ADOPTS these heads as its proprietors rather than "
                    "minting its own, so the two bands fill one quota.",
        },
        "present_on_scene_date": {
            "value": "present",
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "rule",
                "id": "ordered_by_the_reconstruction_order_book",
                "note": "Ordered, not argued: the book counts this person as missing FROM "
                        "the town of 1 July 1835, so presence is the order rather than a "
                        "draw made over it.",
            },
            "replaceable_by": {
                "kind": "person",
                "match": "a re-cut order book that no longer orders this bucket",
            },
        },
        "persons": [person],
        "touches_removal": False,
        "review_required": False,
        "research_note": "WRITTEN BY tools/reconstruct_trade_households.py (T-1347, of "
                         "T-1173), the `trade_households` stage of the 1835 resident "
                         "reconstruction programme. This file is NOT research and is not a "
                         "mint output: data/residents/households/ is re-derived by the mint "
                         "writers and data/residents/index.json is derived from that "
                         "directory, so a reconstruction lives here instead and is "
                         "overlaid onto the scene by tools/compile_scene.py. "
                         "docs/LIBERTIES.md carries the invention.",
    }


def fill() -> tuple:
    """(cards by id, the ledger). Pure over the committed inputs."""
    pool = pools()
    sizes = size_rows()
    caps = ceilings()
    plan = trade_plan()
    taken_names, _real, taken_ids = layer()

    cards = {}
    by_trade = Counter()
    by_division = Counter()
    by_community = Counter()
    by_band = Counter()
    fills = Counter()
    sizes_owed = Counter()

    for slot in deal():
        card = card_for(slot, pool, sizes, caps, taken_names, taken_ids)
        cards[card["id"]] = card
        by_trade[slot[4]] += 1
        by_division[slot[3]] += 1
        by_band[slot[2]] += 1
        by_community[card["persons"][0]["reconstruction"]["community"]] += 1
        fills[slot[0]] += 1
        sizes_owed[card["household_owed"]["size_drawn"]] += 1

    ordered = sum(capacity for _k, _s, _b, _d, capacity in buckets())
    ledger = {
        "_doc": "DERIVED — regenerate with tools/reconstruct_trade_households.py --build. "
                "What this stage drew, against the model rows it drew from. Do not "
                "hand-edit.",
        "id": "1835_trade_households",
        "ticket": TICKET,
        "parent_ticket": PARENT,
        "stage": STAGE,
        "target_date": SCENE_DATE,
        "generated_by": "tools/reconstruct_trade_households.py --build",
        "not_a_reading": "no source was opened; nobody here is named by one",
        "reads": [
            "data/reconstruction/1835_reconstruction_order_book.json",
            "data/research/directories/fergus_1839_trade_table.json",
            "data/reconstruction/1835_town_model.json",
            "data/reconstruction/1835_invented_name_pools.json",
        ],
        "heads_ordered": ordered,
        "heads_drawn": len(cards),
        "the_plan": plan,
        "by_trade": dict(sorted(by_trade.items(), key=lambda kv: (-kv[1], kv[0]))),
        "by_division": dict(sorted(by_division.items())),
        "by_age_band": dict(sorted(by_band.items())),
        "by_community": dict(sorted(by_community.items())),
        "household_size_owed": {str(k): v for k, v in sorted(sizes_owed.items())},
        "kin_seated": 0,
        "kin_owed": sum(int(k) * v for k, v in sizes_owed.items()) - len(cards),
        "the_kin_hand_off": "Every head above is owed the family the 1840 size histogram "
                            "drew for them and none of it is seated here: the kin of a "
                            "family household are `family/none` in the order book and that "
                            "quota is T-1174's and T-1171's. T-1179 converges the two.",
        "trades_this_stage_may_not_write": dict(sorted(REFUSED_TRADES.items())),
        "the_seniority_rule_refused": "T-1173's rules sketched 'labourers young, master "
                                      "tradesmen older'. The 1839 table carries no ages "
                                      "and the 1840 schedule carries no trades, so nothing "
                                      "in this corpus prices it; each trade is dealt "
                                      "across the bands in proportion to what the book "
                                      "ordered, and T-1183 owns the master/journeyman "
                                      "split.",
        "minted": [{"id": hid, "file": f"reconstructed_trades/{hid}.json",
                    "bucket": cards[hid]["trade_household"]["bucket"],
                    "trade": cards[hid]["trade_household"]["trade"],
                    "division": cards[hid]["division"]}
                   for hid in sorted(cards)],
        "fills": dict(sorted(fills.items())),
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
    carry_seats(cards, MINTED)
    return cards, ledger


# ------------------------------------------------------------- the measurement --

def measurement(cards: dict, ledger: dict) -> dict:
    """The acceptance's printed table: the buckets, against what was put in them."""
    ordered = {key: capacity for key, _s, _b, _d, capacity in buckets()}
    filled = ledger["fills"]
    short = {key: ordered[key] - filled.get(key, 0)
             for key in sorted(ordered) if ordered[key] - filled.get(key, 0)}
    rows = dict(trade_rows())
    total_1839 = float(sum(rows.values())) or 1.0
    drawn_total = float(ledger["heads_drawn"]) or 1.0
    shape = {}
    for trade, count in sorted(ledger["by_trade"].items()):
        shape[trade] = {
            "drawn": count,
            "drawn_share": round(count / drawn_total, 4),
            "share_1839": round(rows.get(trade, 0) / total_1839, 4),
        }
    return {
        "buckets_ordered": len(ordered),
        "heads_ordered": sum(ordered.values()),
        "heads_drawn": ledger["heads_drawn"],
        "every_bucket_filled": not short,
        "buckets_still_short": short,
        "distinct_trades": len(ledger["by_trade"]),
        "trade_shape_against_1839": shape,
        "the_residual": {sex: ledger["the_plan"]["workings"][sex]["residual_total"]
                         for sex in sorted(ledger["the_plan"]["workings"])},
        "kin_owed_and_not_seated": ledger["kin_owed"],
    }


# --------------------------------------------------------------------- modes --

def write(cards: dict, ledger: dict) -> tuple:
    MINTED.mkdir(parents=True, exist_ok=True)
    wanted = {f"{hid}.json" for hid in cards}
    removed = 0
    for path in sorted(MINTED.glob("hh_*.json")):
        if path.name not in wanted:
            path.unlink()
            removed += 1
    written = 0
    for hid, card in sorted(cards.items()):
        path = MINTED / f"{hid}.json"
        text = dumps(card)
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            written += 1
    readme = MINTED / "README.md"
    readme.write_text(README, encoding="utf-8")
    return written, removed


def write_fills(ledger: dict) -> None:
    """Carry this stage's fills into the order book and re-derive it. The book's own
    `--build` refuses an overfilled bucket, so the quota is enforced twice."""
    import build_order_book_1835 as ob
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    kept = [f for f in book.get("fills", []) if f.get("ticket") != TICKET]
    kept += [{"bucket": key, "ticket": TICKET, "stage": STAGE, "records": n,
              "by": "tools/reconstruct_trade_households.py --build"}
             for key, n in sorted(ledger["fills"].items())]
    book["fills"] = kept
    BOOK.write_text(json.dumps(book, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ob.cmd_build()


def build() -> int:
    cards, ledger = fill()
    written, removed = write(cards, ledger)
    ledger["measurement"] = measurement(cards, ledger)
    LEDGER.write_text(dumps(ledger), encoding="utf-8")
    write_fills(ledger)
    print("  wrote %s" % LEDGER.relative_to(ROOT))
    print("  %d head(s) drawn into %d bucket(s); %d card(s) written, %d retired"
          % (ledger["heads_drawn"], len(ledger["fills"]), written, removed))
    return 0


def check() -> int:
    cards, ledger = fill()
    ledger["measurement"] = measurement(cards, ledger)
    live = {path.stem: path.read_text(encoding="utf-8")
            for path in sorted(MINTED.glob("hh_*.json"))} if MINTED.exists() else {}
    want = {hid: dumps(card) for hid, card in cards.items()}
    if set(live) != set(want):
        missing = sorted(set(want) - set(live))[:6]
        extra = sorted(set(live) - set(want))[:6]
        print("  FAIL the committed directory is not this stage's set "
              "(missing %s, extra %s)" % (missing, extra))
        return 1
    bad = [hid for hid in sorted(want) if live[hid] != want[hid]]
    if bad:
        print("  FAIL %d card(s) are not what this stage derives: %s"
              % (len(bad), ", ".join(bad[:6])))
        return 1
    if not LEDGER.exists() or LEDGER.read_text(encoding="utf-8") != dumps(ledger):
        print("  FAIL %s is not what --build writes" % LEDGER.relative_to(ROOT))
        return 1
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    ours = {f["bucket"]: int(f.get("records") or 0)
            for f in book.get("fills", []) if f.get("ticket") == TICKET}
    if ours != dict(ledger["fills"]):
        print("  FAIL the order book's fills for %s are not this stage's ledger" % TICKET)
        return 1
    allowed = set(dict(trade_rows())) | set(WOMENS_TRADES) | set(RESIDUAL.values())
    stray = sorted(n for n in ledger["by_trade"] if n not in allowed)
    if stray:
        print("  FAIL a trade this stage may not write was written: %s" % stray)
        return 1
    outside = sorted(set(ledger["by_trade"]) - vocabulary())
    if outside:
        print("  FAIL a trade outside data/residents/index.json's controlled vocabulary "
              "was written onto a person: %s" % outside)
        return 1
    print("  ok    %d head(s) re-derive from their seeds into %d bucket(s), %d trade(s)"
          % (ledger["heads_drawn"], len(ours), ledger["measurement"]["distinct_trades"]))
    print("  ok    the order book carries this stage's fills and no bucket is overfilled")
    return 0


def report() -> int:
    cards, ledger = fill()
    stats = measurement(cards, ledger)
    print("THE TRADE HOUSEHOLDS THE ORDER BOOK ORDERS")
    print("   buckets %3d   heads ordered %4d   heads drawn %4d   every bucket filled: %s"
          % (stats["buckets_ordered"], stats["heads_ordered"], stats["heads_drawn"],
             stats["every_bucket_filled"]))
    print("THE PLAN — what each sex's heads were dealt, and what a ceiling refused")
    for sex in sorted(ledger["the_plan"]["workings"]):
        work = ledger["the_plan"]["workings"][sex]
        print("   %-7s ordered %4d   residual %-10s %4d   refused by a ceiling %d"
              % (sex, work["heads_ordered"], work["residual_trade"],
                 work["residual_total"], work["moved_to_the_residual"]))
        for trade, n in sorted(work["refused_by_a_census_ceiling"].items()):
            print("       ceiling refused %2d of %s" % (n, trade))
    print("TRADE — the 1839 directory's share against the draw")
    for trade, row in sorted(shape_order(stats["trade_shape_against_1839"])):
        print("   %-26s drawn %4d  %6.4f   1839 %6.4f"
              % (trade, row["drawn"], row["drawn_share"], row["share_1839"]))
    print("DIVISION %s" % ledger["by_division"])
    print("BAND     %s" % ledger["by_age_band"])
    print("POOL     %s" % ledger["by_community"])
    print("KIN      %d owed by the household model and seated by T-1174/T-1179, 0 here"
          % ledger["kin_owed"])
    return 0


def shape_order(shape: dict) -> list:
    return sorted(shape.items(), key=lambda kv: (-kv[1]["drawn"], kv[0]))


README = """# data/residents/reconstructed_trades/

DERIVED. Written by `tools/reconstruct_trade_households.py --build` (T-1347, of T-1173),
the `trade_households` stage of the 1835 resident reconstruction programme. Do not
hand-edit a card here: `--check` re-derives the whole directory and refuses a differing
byte, and `tools/check.sh` runs it.

Every person here is `grade: reconstructed` and **nobody in this directory is named by any
source**. They exist because the order book counts the town of 1 July 1835 as short of
that many adults at a trade in that division, and each card says on its face which bucket
ordered it, which seed drew every value and what evidence would retire the person.

The directory is deliberately OUTSIDE `data/residents/households/`, for the reason
`readmitted/` is: that directory is re-derived by the research mints and
`data/residents/index.json` is derived from it, so a reconstruction that is not a reading
lives here and is overlaid onto the scene by `tools/compile_scene.py`.
"""


# ------------------------------------------------------------------ self-test --

def self_test() -> int:
    failures = []

    def fires(what: str, ok: bool) -> None:
        print("   %-70s %s" % (what, "ok" if ok else "FAIL"))
        if not ok:
            failures.append(what)

    fires("the same seed draws the same face twice", draw("a:b") == draw("a:b"))
    fires("two slots draw different faces", draw("a:b") != draw("a:c"))
    fires("largest remainder lands the whole total",
          sum(allocate(7, [("a", 1), ("b", 1), ("c", 1)]).values()) == 7)
    fires("largest remainder breaks its ties on the key",
          allocate(1, [("b", 1), ("a", 1)]) == {"a": 1})
    fires("an empty total allocates nothing", allocate(0, [("a", 1)]) == {})

    caps = ceilings()
    fires("a class the town already matches leaves room for nobody",
          caps.get("printer") == 0 and caps.get("schoolteacher") == 0)
    # THE FIGURES ARE LIVE AND THE ASSERTION IS NOT A CONSTANT. `physician` read 11 until
    # T-1404 raised the five attested physicians' offices the business layer had no record
    # of; the ceiling is census minus what the town can NAME, so naming five of them is
    # exactly what is supposed to move it. It is kept as a number rather than recomputed
    # here on purpose — a self-test that derives its own expectation asserts nothing.
    fires("a class the town is short of leaves room for the difference",
          caps.get("physician") == 6 and caps.get("attorney") == 4)

    rows = dict(trade_rows())
    fires("no trade outside the 1835 vocabulary reaches the draw",
          "drayman" not in rows and "gardener" not in rows and "labourer" in rows)
    fires("the garrison's trades and the town's singular offices never reach the draw",
          not (set(rows) & set(REFUSED_TRADES)) and "soldier" in REFUSED_TRADES)

    plan = trade_plan()
    fires("every head the book orders is dealt a trade",
          sum(plan["by_sex"]["male"].values()) + sum(plan["by_sex"]["female"].values())
          == sum(c for _k, _s, _b, _d, c in buckets()))
    fires("no trade is dealt past its census ceiling",
          all(plan["by_sex"][sex].get(t, 0) <= caps[t]
              for sex in plan["by_sex"] for t in caps))
    fires("a woman is drawn only into a trade this layer records a woman at",
          set(plan["by_sex"]["female"]) <= set(WOMENS_TRADES))
    fires("every trade this stage may write is a controlled vocabulary word",
          (set(rows) | set(WOMENS_TRADES) | set(RESIDUAL.values())) <= vocabulary())
    fires("what a ceiling refuses reaches the residual, and is not lost",
          all(plan["workings"][sex]["moved_to_the_residual"]
              <= plan["workings"][sex]["residual_total"] for sex in plan["workings"]))

    slots = deal()
    fires("the deal fills every bucket to its capacity and no further",
          Counter(s[0] for s in slots)
          == Counter({k: c for k, _s, _b, _d, c in buckets() if c}))
    fires("the deal is stable across two runs", deal() == slots)

    cards, ledger = fill()
    fires("every drawn head is a head of their own household",
          all(len(c["persons"]) == 1 and c["persons"][0]["relationship"] == "head"
              for c in cards.values()))
    fires("no kin is seated by this stage",
          ledger["kin_seated"] == 0 and ledger["kin_owed"] > 0)
    fires("every id is unique and marked as an invention",
          len(cards) == len({c["persons"][0]["id"] for c in cards.values()})
          and all(c["persons"][0]["id"].startswith(PREFIX) for c in cards.values()))
    _all, real, layer_ids = layer()
    fires("no invented name is an attested or inferred person's name",
          not any(c["persons"][0]["name"].lower() in real for c in cards.values()))
    fires("no drawn id is one the layer already holds",
          not (layer_ids & {c["persons"][0]["id"] for c in cards.values()}))
    fires("no reviewed community is written by this stage",
          all(c["persons"][0]["reconstruction"]["community"]
              in {"yankee", "irish", "french_colonial"} for c in cards.values()))

    import reconstruct_residents_1835 as rr
    problems = []
    prog = rr.load_programme()
    keys = {s["key"] for s in rr.stages(prog).values()} | set(rr.stages(prog))
    for hid, card in sorted(cards.items()):
        rr.check_reconstructed_person(hid, card["persons"][0], keys,
                                      lambda w, m: problems.append((w, m)))
    fires("every drawn person satisfies the programme's record contract", not problems)

    print("   %d rule(s) checked, %d failed" % (23, len(failures)))
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
