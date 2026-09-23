#!/usr/bin/env python3
"""T-1171, stage `modelled_families` — a family for every head the sources leave alone.

    python3 tools/reconstruct_modelled_families.py --build     draw them, write the cards
    python3 tools/reconstruct_modelled_families.py --check     re-derive and refuse drift
    python3 tools/reconstruct_modelled_families.py --report    who was drawn, and against what
    python3 tools/reconstruct_modelled_families.py --self-test the rules, each refusing its own case

WHAT THIS STAGE IS. `data/residents/` holds 1,258 household records for 1,282 people —
1.02 people a record. The town of 1 July 1835 was not one person a roof: the model's own
reading is 469 to 816 households for 2,350 to 3,265 people. The gap is not a hole in the
evidence, it is the SHAPE of the evidence: a letter list, a voter roll and a subscription
name a man and never his wife, and a household record minted off one of them carries the
man alone. This stage gives the head the family the household model says he had, and says
in every record that it did so.

WHAT IT MAY NOT DO. Only the head's own household is filled, and only where the record
admits one. Seven refusals, each with a reason a reader can check:

  1. A household whose presence on the scene date is still unsettled gets nothing. The
     order book counts only present households as known (its rule 3) and offers the
     unsettled ones to T-1172 as the roster's R1 class. A family drawn onto an unsettled
     head would order the same person twice, once here and once there.
     SETTLED MEANS THE CARD **OR** T-1386'S RULING, since 2026-09-20. T-1386 adjudicated
     the 827 attested and inferred people the layer had left on an unruled `uncertain`
     and wrote 820 household rulings to `data/reconstruction/1835_presence_rulings.json`,
     a derived sidecar the card does not carry. The order book, the town census and the
     population profile all read that file; this stage did not, and so refused 822
     households the project had already ruled were in the town — 89 heads eligible where
     429 are. That was the staleness T-1463 named when it reopened this ticket, and it is
     why the stage measured itself against a town of 1,140 when the book's own town stood
     at 2,267. The two evidenced absences the file names stay out.
  2. A `letter_list` mint gets nothing. That record argues for a PERSON and not for a
     household — "one member, no dwelling, no division, no trade, no family" is its own
     research note, and `mint_letter_list_residents.py --gate` PROVES no record there
     gained a roof, a trade or a second member. This stage is not the thing that breaks
     a standing gate.
  3. A household that already holds a second person gets nothing. A head whose family a
     source names, counts or rules on is not a head the sources leave alone: T-1313 and
     T-1314 own those, and this stage draws only where they do not.
  3a. AN EVIDENCE-ONLY CONTAINER GETS NOTHING, since 2026-09-21 (T-1369). The five
     `hh_inf_*` records are not households the sources record — the occupation census
     raised each roof because a town of 3,265 people in 398 dwellings needed that trade,
     and the register then put a documented man under it. The man and his trade are
     attested; the dwelling is a hypothesis, and `hh_inf_cooper_north_04`'s own
     `party_size_on_arrival` has always said what follows from that: "The layer infers
     households, not families: the person entries here are the ones the trade argument
     requires and nothing counts wives or children, because counting them would multiply a
     hypothesis by an invention." This stage's rules did not know that and drew ten kin
     into four of the five, which is the red `nothing was drawn into an evidence-only
     household` stood at on dev from 2026-09-18. The rule the smoke asserts and the rule
     this stage applies are the same rule now. A dwelling these men are DOCUMENTED to have
     kept retires the container, not the refusal; until a source says one did, the trade
     argument is met by naming the man and stops there.
  4. The fort and the country outside the town get nothing. T-1176 musters the garrison
     and the order book never apportions the fort division.
  5. A household under a standing review gets nothing, and neither does a head whose own
     trade says he kept no wife. AGENTS.md's Indigenous-history review confines a Native or
     Metis reconstruction to T-1177's stage, and the programme asserts that from the other
     side; a household flagged `review_required` or `touches_removal` is in that hands, not
     this stage's. And a model that gave Father St Cyr a wife would be inventing against
     the record rather than into a gap in it, which is the one draw no quota excuses.

  6. A married house the order book has no woman left for is not half-drawn — it is
     refused whole, and the cell that refused it is named. Seating the children of a
     marriage the book would not seat would put a cottage of infants with no mother on
     the ground and would read as evidence of a family nobody drew. 310 houses stand
     refused this way today, 147 of them in `persons/female/20_29/south/family/none`:
     T-1174 and T-1347 drew the women the pyramid was short as their OWN records rather
     than into these houses, and re-housing them is T-1179's convergence.

  And one bound that is not a refusal: NOBODY BUT KIN IS DRAWN. The household types carry
  servants, apprentices and journeymen, and the size the 1840 histogram draws is of the
  whole house. This stage seats the KIN CORE — a wife and children — because the servant
  and the apprentice are priced by the staffing model T-1183 has not written yet and the
  lodger is seated by T-1175. The drawn size is therefore a floor on the house and the
  printed household-size distribution says so rather than claiming the model's own shape.

THE DRAW, AND WHY EVERY PIECE OF IT IS REPRODUCIBLE. Nothing here is random: every value
comes from `blake2s(seed)` over a seed a reader can retype, and the seed is printed on the
record that carries the value. `--check` strips this stage out of the committed layer,
draws it again and refuses a single differing byte, so the layer is a function of the
model files and not of the day it was run.

THE ORDER BOOK IS THE QUOTA. Every drawn person is counted into a bucket of
`data/reconstruction/1835_reconstruction_order_book.json` (sex x age x division x household
type x trade) and a bucket that would go past its `to_reconstruct` REFUSES the draw instead.
The refusals are counted and printed; they are the book doing its job, not a defect.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
MODEL = ROOT / "data" / "reconstruction" / "1835_town_model.json"
COMPOSITION = ROOT / "data" / "research" / "census_1840" / "composition_1840.json"
POOLS = ROOT / "data" / "reconstruction" / "1835_invented_name_pools.json"
BOOK = ROOT / "data" / "reconstruction" / "1835_reconstruction_order_book.json"
LEDGER = ROOT / "data" / "reconstruction" / "1835_modelled_families.json"
RULINGS = ROOT / "data" / "reconstruction" / "1835_presence_rulings.json"

STAGE = "modelled_families"
TICKET = "T-1171"
SCENE_DATE = "1835-07-01"
SCENE_YEAR = 1835
RECONSTRUCTED = "reconstructed"
PREFIX = "rc_"
CIVIL = ("south", "west", "north")

# The kin core a household of this size holds, once the head is seated. Sizes above
# eight are the 1840 tail and this stage does not draw them: the model reads that tail
# as "boarding houses, hotels and crews", which is lodging and belongs to T-1175.
KIN_MAX = 8

# Trades whose holder the sources place under a vow of celibacy. A Catholic priest kept no
# wife, and drawing one for Father St Cyr would be an invention the record itself refutes —
# the one kind of draw a model may never make. Protestant ministers married and are not
# here: Jeremiah Porter's household is a family the sources name.
CELIBATE_TRADES = ("priest",)

# The evidence-only containers T-0489 kept: `hh_inf_*`, named "Evidence-only household
# — <head>", one head the papers name and no dwelling that is anything but hypothesis.
# Both markers are asserted to agree in `--check`, so neither can drift alone.
EVIDENCE_ONLY_ID = "hh_inf_"
EVIDENCE_ONLY_NAME = "Evidence-only household"

# The order book's own six bands, so a drawn person can be counted into its buckets.
BOOK_BANDS = (("under_10", 0, 10), ("10_19", 10, 20), ("20_29", 20, 30),
              ("30_39", 30, 40), ("40_49", 40, 50), ("50_plus", 50, None))


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


_RULED = None


def ruled_present() -> frozenset:
    """The households T-1386 ruled into the town of 1 July 1835.

    `present_on_scene_date` ON THE CARD IS NOT THE WHOLE RULING. T-1386 adjudicated the
    827 attested and inferred people the layer left on an unruled `uncertain` and wrote
    its 820 household rulings to `data/reconstruction/1835_presence_rulings.json`, a
    DERIVED sidecar the card itself does not carry. The order book reads that file and
    counts those households KNOWN and PRESENT (its `population_ruled_in`, summed into
    `known` by T-1463); so do the town census and the population profile. This stage read
    the card alone and therefore refused 822 households the project had already ruled were
    in the town — the staleness T-1463 named, and the reason the layer stood at 1.02 people
    a record while the book's own population counted 2,267.

    The rulings are a floor and never a veto: a card that already says `present` stays
    present, and the two evidenced absences the file names are not in this set."""
    global _RULED
    if _RULED is None:
        rows = json.loads(RULINGS.read_text(encoding="utf-8"))["rulings"]
        _RULED = frozenset(r["household_id"] for r in rows
                           if value_of(r.get("present_on_scene_date")) == "present")
    return _RULED


def table(section_key: str, table_key: str) -> dict:
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    for section in model["sections"]:
        if section["key"] == section_key:
            return section["tables"][table_key]
    raise SystemExit(f"the town model carries no {section_key}.{table_key}")


def size_rows() -> list:
    """The 1840 size histogram, cut to the kin range. The head_rule's own instruction:
    a head the sources do not give a family gets one drawn at his own size band and never
    at the mean, because a town drawn at the mean has no small households and no tail."""
    rows = table("households_and_families", "size_histogram_1840")["rows"]
    return [(int(r["size"]), int(r["households"])) for r in rows
            if 1 <= int(r["size"]) <= KIN_MAX]


def age_rows() -> list:
    """The 1840 free-white bands: (sex, low_edge, persons, printed band)."""
    rows = json.loads(COMPOSITION.read_text(encoding="utf-8"))["age_bands"]["free_white"]
    return [(r["sex"], int(r["low_edge"]), int(r["persons"]), r["band"]) for r in rows]


def division_rows() -> list:
    return [(r["division"], float(r["share"]))
            for r in table("population", "by_division")["rows"]]


def pools() -> dict:
    return json.loads(POOLS.read_text(encoding="utf-8"))


def book_band(age_low: int) -> str:
    for label, low, high in BOOK_BANDS:
        if age_low >= low and (high is None or age_low < high):
            return label
    return "50_plus"


# ------------------------------------------------------------- who is eligible --

def head_of(card: dict):
    persons = card.get("persons") or []
    if len(persons) != 1:
        return None
    person = persons[0]
    return person if person.get("relationship") == "head" else None


def settled_present(card: dict, ruled=None) -> bool:
    """Is this household in the town of 1 July 1835? The card first, T-1386's ruling
    after it. Both are the project's own answer to the same question; the card is simply
    the half of it that predates the adjudication."""
    if value_of(card.get("present_on_scene_date")) == "present":
        return True
    if value_of(card.get("present_on_scene_date")) == "absent":
        return False
    if ruled is None:
        ruled = ruled_present()
    return card.get("id") in ruled


def evidence_only(card: dict) -> bool:
    """Is this record an evidence-only container rather than a household? T-0489 kept five
    of them: the occupation census raised a roof because the town of 3,265 in 398 dwellings
    needed a cooper, a joiner, a physician, a tailor and a tavern keeper, and the register
    later put a documented man under each. What is attested there is the MAN and his trade;
    the dwelling, its position and its footprint are conjectural and no source says he kept
    a house at all. Read by either marker, because a record that lost one and kept the other
    is a drift `--check` should refuse rather than a household this stage may fill."""
    return (str(card.get("id") or "").startswith(EVIDENCE_ONLY_ID)
            or str(card.get("name") or "").startswith(EVIDENCE_ONLY_NAME))


def eligibility(card: dict, ruled=None) -> tuple:
    """(eligible, the refusal). One rule a line, in the docstring's order.

    `ruled` is the T-1386 ruling set; it defaults to the committed one and is passed
    explicitly only by the self-test, which owns no household id in the file."""
    if ruled is None:
        ruled = ruled_present()
    if not settled_present(card, ruled):
        return False, "presence on the scene date is not settled (T-1172's roster holds it)"
    if str(card.get("source_pass") or "") == "letter_list":
        return False, "a letter-list mint argues for a person and not for a household"
    if evidence_only(card):
        return False, ("an evidence-only container holds read evidence and not a "
                       "household to draw a family into")
    persons = card.get("persons") or []
    if len(persons) > 1:
        return False, "a source already names, counts or rules on this household's family"
    head = head_of(card)
    if head is None:
        return False, "the record carries no single head to draw a family around"
    if head.get("grade") not in ("attested", "inferred"):
        return False, "the head is not a person the sources name"
    if card.get("division") not in CIVIL and card.get("division") != "unplaced":
        return False, "the fort and the country outside the town are not this stage's"
    if card.get("review_required") or card.get("touches_removal"):
        return False, ("the household carries a standing review, and only T-1177's stage "
                       "may reconstruct within one")
    if (value_of(head.get("occupation")) or "") in CELIBATE_TRADES:
        return False, "the head's own trade says he kept no wife"
    if (value_of(head.get("sex_basis")) or head.get("sex")) != "male":
        return False, "a woman heading her own household is the age pyramid's, T-1174"
    band = head.get("age_band")
    if not isinstance(band, dict) or band.get("low") is None or int(band["low"]) < 20:
        return False, "the head is not an adult the household model seats as a husband"
    return True, ""


# ---------------------------------------------------------------- naming a kin --

def surname_of(name: str) -> str:
    """The family name a wife and a child take. The head's own, as his card prints it."""
    parts = [p for p in str(name or "").replace(",", " ").split() if p]
    parts = [p for p in parts if p not in ("[?]", "Jr.", "Sr.", "jr.", "sr.")]
    return parts[-1] if parts else "Unnamed"


def community_for(head: dict, hid: str, pool: dict) -> dict:
    """Which naming pool a household's kin are drawn from. Trade weights where the pools
    carry one for the head's trade, the general documented stock otherwise."""
    occupation = value_of(head.get("occupation")) or "_default"
    weights = pool["trade_weights"].get(occupation) or pool["trade_weights"]["_default"]
    by_id = {c["id"]: c for c in pool["communities"]}
    weighted = [(by_id[k], v) for k, v in sorted((weights.get("weights") or {}).items())
                if k in by_id]
    if not weighted:
        weighted = [(by_id["yankee"], 1)]
    return pick(seed_for(hid, "name_pool_community"), weighted)


def forename(seed: str, community: dict, sex: str, taken: set) -> str:
    """A forename from the pool. Deterministic, and it steps on past a name already
    borne by a real person of this family — an invention a reader could mistake for a
    finding is the one thing the pools may never produce."""
    names = community["given_male" if sex == "male" else "given_female"]
    start = draw(seed) % len(names)
    for offset in range(len(names)):
        candidate = names[(start + offset) % len(names)]
        if candidate.lower() not in taken:
            return candidate
    return names[start]


# ----------------------------------------------------------------- the writing --

def person_record(pid: str, name: str, relationship: str, sex: str, band: dict,
                  seed: str, basis_note: str, name_seed: str, name_note: str,
                  community: dict, head_name: str) -> dict:
    """A reconstructed person, carrying everything the record contract asks of one."""
    return {
        "id": pid,
        "name": name,
        "relationship": relationship,
        "grade": RECONSTRUCTED,
        "sex": sex,
        "age_band": band,
        "occupation": {
            "value": "none_recorded",
            "confidence": RECONSTRUCTED,
            "note": "No trade is drawn for a reconstructed kin member. The occupation "
                    "model is spent on heads and on the trades the town is short of "
                    "(T-1173); a wife's and a child's work in an 1835 household is real "
                    "and unrecorded, and this project will not invent a column for it.",
        },
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
                "match": f"a source naming a member of {head_name}'s family",
            },
            "note": "AN INVENTED NAME, AND IT IS NEVER EVIDENCE. The surname is the "
                    f"head's own, as his card prints it; the forename is drawn from the "
                    f"{community['label']} pool, which is seeded from the attested "
                    "residents of this town and not from a story about who lived here. "
                    "No source names this person.",
        },
        "basis": {
            "kind": "model",
            "id": "size_histogram_1840",
            "note": basis_note,
        },
        "seed": seed,
        "replaceable_by": {
            "kind": "person",
            "match": f"a source naming this head's family",
        },
        "reconstruction": {
            "programme": "1835_resident_reconstruction",
            "stage": STAGE,
            "ticket": TICKET,
            "community": community["id"],
            "review_required": False,
        },
        "note": "RECONSTRUCTED, NOT FOUND. Nobody is named by any source here. This "
                "person exists because the household model says the head kept a house "
                f"of this size, and the whole of what is claimed is that: a {relationship} "
                "of that house, of this sex and in this age band, drawn from the 1840 "
                "Chicago schedule and reproducible from the seed printed above. A source "
                "naming this head's family retires them. No figure is drawn (L1).",
    }


def band_block(low: int, high, printed: str, seed: str, why: str) -> dict:
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


# ------------------------------------------------------------------ the quota --

def quota() -> dict:
    """Bucket key -> how many more persons that bucket will take.

    THIS STAGE'S OWN FILLS ARE ADDED BACK. `filled` on a bucket counts what every stage
    has put in it, including the last run of this one, and a draw that read its own
    previous answer as a spent quota would draw fewer people on the second build than on
    the first — which is the one thing `--check` may not tolerate. The quota this stage
    draws against is therefore the book as it stood before this stage last ran, and what
    other stages have filled is still subtracted.
    """
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    ours = Counter()
    for entry in book.get("fills") or []:
        if entry.get("ticket") == TICKET:
            ours[entry.get("bucket")] += int(entry.get("records") or 0)
    out = {}
    for family in book["bucket_families"]:
        if family["key"] != "persons":
            continue
        for bucket in family["buckets"]:
            todo = bucket.get("to_reconstruct")
            if todo is not None:
                out[bucket["key"]] = (int(todo) - int(bucket.get("filled") or 0)
                                      + ours[bucket["key"]])
    return out


def bucket_for(hid: str, card: dict, sex: str, age_low: int, which: str) -> str:
    """The order book cell a drawn person is counted into.

    The DIVISION is the household's where the record places it. Where it does not —
    1,186 of the 1,258 records say `unplaced` — the person is allocated to a division
    by a seeded draw on the model's own by-division shares. That allocation is a LEDGER
    ACT and nothing else: it writes no division onto the person, onto the household or
    onto any card, and the record goes on saying the household's place is unknown. The
    book apportions unplaced KNOWN people pro rata for the same reason (its rule 2); this
    is the same arithmetic, done one person at a time so it can be reproduced."""
    division = card.get("division")
    if division not in CIVIL:
        division = pick(seed_for(hid, f"division_share:{which}"), division_rows())
    return f"persons/{sex}/{book_band(age_low)}/{division}/family/none"


# -------------------------------------------------------------------- the pass --

def without_this_pass(card: dict) -> dict:
    """The card as it stood before this stage ran. The basis of `--check`."""
    out = json.loads(json.dumps(card))
    out["persons"] = [p for p in (out.get("persons") or []) if not ours(p)]
    out.pop("modelled_family", None)
    return out


def ours(person: dict) -> bool:
    rc = person.get("reconstruction")
    return isinstance(rc, dict) and rc.get("stage") == STAGE


def real_names(base: dict) -> set:
    out = set()
    for card in base.values():
        for person in card.get("persons") or []:
            name = " ".join(str(person.get("name") or "").split()).lower()
            if name:
                out.add(name)
    return out


def fill(base: dict) -> tuple:
    """(cards with this stage's people, the ledger). Pure over `base`."""
    out = json.loads(json.dumps(base))
    pool = pools()
    sizes = size_rows()
    ages = age_rows()
    left = quota()
    taken = real_names(base)

    female_adult = [(r, r[2]) for r in ages if r[0] == "female" and 20 <= r[1] < 60]
    child_bands = [(r, r[2]) for r in ages if r[1] < 20]
    male_children = sum(r[2] for r in ages if r[0] == "male" and r[1] < 20)
    all_children = sum(r[2] for r in ages if r[1] < 20)
    boy_rate = male_children / float(all_children)

    counts = Counter()
    refusals = Counter()
    refused_buckets = Counter()
    drawn_band = Counter()
    drawn_size = Counter()
    refused_size = Counter()
    kin_size = Counter()
    fills = Counter()
    per_card = {}

    # THE ORDER THE QUOTA IS SPENT IN, AND WHY IT IS NOT PLAIN hid ORDER. A household
    # the card itself rules present was drawn for before T-1386's rulings were honoured
    # here, and the owner's ruling of 2026-09-20 (T-1459) is that nobody this stage has
    # already drawn is un-drawn. The seeds are per-household, so every such house draws
    # the same family it drew before; only the ORDER the book is spent in could take a
    # slot away from one. So they are served first, and the households T-1386 ruled in
    # follow them. Both keys are committed data, so `--check` re-derives the same order.
    ruled = ruled_present()

    def service_order(hid: str) -> tuple:
        card = out[hid]
        return (0 if value_of(card.get("present_on_scene_date")) == "present" else 1, hid)

    for hid in sorted(out, key=service_order):
        card = out[hid]
        ok, why = eligibility(card, ruled)
        if not ok:
            refusals[why] += 1
            continue
        head = head_of(card)
        head_name = str(head.get("name") or "")
        head_low = int(head["age_band"]["low"])
        surname = surname_of(head_name)
        community = community_for(head, hid, pool)
        family_names = {surname.lower()}

        size = pick(seed_for(hid, "household_size"), [(s, n) for s, n in sizes])
        # THE SIZE HISTOGRAM MEASURES THE MODEL, NOT THE BOOK. Every eligible head is
        # counted here, before the order book has spoken, because what this table tests
        # is whether the 1840 size distribution is being SAMPLED faithfully. A house the
        # book then refuses is a fact about the quota and is counted as one, below.
        drawn_size[size] += 1
        members = []
        household_type = ("solitary" if size == 1
                          else "married_couple" if size == 2 else "family_with_children")

        if size >= 2:
            # THE WIFE. Her band is drawn from the 1840 female adult columns and never
            # above the head's own band: the city returned 146.8 men per 100 women aged
            # twenty and over, and the surplus is young unmarried men, so a wife older
            # than her husband's decade is the shape the schedule least supports. This is
            # the spacing rule, and it is an assumption of the model rather than a reading.
            allowed = [(r, w) for r, w in female_adult if r[1] <= head_low]
            if not allowed:
                allowed = female_adult
            wseed = seed_for(hid, "wife_age_bands_1840")
            row = pick(wseed, allowed)
            low = row[1]
            high = None if low >= 50 else low + (5 if low < 20 else 10) - 1
            given = forename(seed_for(hid, "wife_forename"), community, "female", family_names)
            family_names.add(given.lower())
            name = f"{given} {surname}"
            bucket = bucket_for(hid, card, "female", low, "wife")
            if left.get(bucket, 0) <= 0:
                # THE WIFE IS THE HOUSE. The model drew this house married; if the book
                # has no woman left for her cell, the married house is not a house this
                # stage may half-draw. Seating the children of a marriage the book would
                # not seat would put a fatherless-looking cottage of infants on the
                # ground and would read as evidence of a family nobody drew. The whole
                # house is refused, the cell that refused it is named, and the head is
                # left exactly as the sources leave him.
                refused_buckets[bucket] += 1
                refusals["the order book has no woman left in this house's cell"] += 1
                counts["houses_the_book_refused"] += 1
                refused_size[size] += 1
                continue
            else:
                left[bucket] -= 1
                fills[bucket] += 1
                members.append(person_record(
                    f"{PREFIX}{hid[3:]}_wife", name, "wife", "female",
                    band_block(low, high, row[3], wseed,
                               "Never above the head's own band: the spacing rule of the "
                               "household model, which the 1840 adult sex ratio argues for "
                               "and no source states."),
                    seed_for(hid, "household_size"),
                    f"The household model drew this house at {size} people from the 1840 "
                    f"city's size histogram, at the head's own band and not at the mean. A "
                    f"house of {size} with a head of {head_low} and over is a married house, "
                    f"and this is its wife.",
                    seed_for(hid, "wife_forename"),
                    f"The forename is drawn from the {community['label']} pool; the surname "
                    f"is the head's own.",
                    community, head_name))
                drawn_band[book_band(low)] += 1
                counts["wives"] += 1

        counts["heads_drawn_for"] += 1

        # THE CHILDREN. What the drawn size leaves once the head and his wife are seated.
        # No child is born after the scene date and none is older than the marriage the
        # head's own age allows, so the eldest is capped at his age band's low minus 20.
        wanted = max(0, size - 2)
        cap = min(19, max(0, head_low - 20))
        for index in range(wanted):
            cseed = seed_for(hid, f"child_{index + 1}_age_bands_1840")
            allowed = [(r, w) for r, w in child_bands if r[1] <= cap]
            if not allowed:
                allowed = [(r, w) for r, w in child_bands if r[1] == 0]
            row = pick(cseed, allowed)
            low = row[1]
            high = low + (5 if low < 20 else 10) - 1
            sseed = seed_for(hid, f"child_{index + 1}_sex_ratio")
            sex = "male" if unit(sseed) < boy_rate else "female"
            given = forename(seed_for(hid, f"child_{index + 1}_forename"),
                             community, sex, family_names)
            family_names.add(given.lower())
            relationship = "son" if sex == "male" else "daughter"
            bucket = bucket_for(hid, card, sex, low, f"child_{index + 1}")
            if left.get(bucket, 0) <= 0:
                refused_buckets[bucket] += 1
                continue
            left[bucket] -= 1
            fills[bucket] += 1
            members.append(person_record(
                f"{PREFIX}{hid[3:]}_child_{index + 1}", f"{given} {surname}",
                relationship, sex,
                band_block(low, high, row[3], cseed,
                           f"Capped at {cap} years: nobody is born after {SCENE_DATE}, and "
                           f"no child of this house is older than the marriage the head's "
                           f"own age band allows."),
                seed_for(hid, "household_size"),
                f"The household model drew this house at {size} people; the head and his "
                f"wife seated, {wanted} of them are children.",
                seed_for(hid, f"child_{index + 1}_forename"),
                f"The forename is drawn from the {community['label']} pool; the surname "
                f"is the head's own.",
                community, head_name))
            drawn_band[book_band(low)] += 1
            counts["children"] += 1

        # THE BLOCK GOES IMMEDIATELY AFTER `present_on_scene_date`, not at the end.
        # Several research passes own a trailing key and rebuild the card by popping
        # theirs and appending it again (`old_settler_deaths` before `directories`, in
        # spend_old_settlers.py); a new key at the end would move under them and their
        # byte-for-byte --check would read it as drift. `resident_mint_carry` puts it in
        # this same slot when a mint rebuilds the card, and the two have to agree.
        rebuilt = {}
        for key, value in card.items():
            rebuilt[key] = value
            if key == "present_on_scene_date":
                rebuilt["modelled_family"] = None  # placed, filled in below
        card.clear()
        card.update(rebuilt)
        card["persons"] = (card.get("persons") or []) + members
        card["modelled_family"] = {
            "stage": STAGE,
            "ticket": TICKET,
            "household_type": household_type,
            "size_drawn": size,
            "kin_seated": 1 + len(members),
            "seed": seed_for(hid, "household_size"),
            "note": "The kin core only. A servant, an apprentice or a journeyman this "
                    "house may have held is priced by T-1183 and seated by T-1173; a "
                    "boarder is seated by T-1175. The drawn size is a floor on the house.",
        }
        kin_size[1 + len(members)] += 1
        per_card[hid] = {"size_drawn": size, "kin_seated": 1 + len(members),
                         "household_type": household_type}

    ledger = {
        "_doc": "DERIVED — regenerate with tools/reconstruct_modelled_families.py --build. "
                "The measurement this stage is held to: what was drawn, against the model "
                "rows it was drawn from. Do not hand-edit.",
        "id": "1835_modelled_families",
        "ticket": TICKET,
        "stage": STAGE,
        "target_date": SCENE_DATE,
        "generated_by": "tools/reconstruct_modelled_families.py --build",
        "not_a_reading": "no source was opened; nobody here is named by one",
        "heads_drawn_for": counts["heads_drawn_for"],
        "people_drawn": counts["wives"] + counts["children"],
        "wives": counts["wives"],
        "children": counts["children"],
        "refused_by_eligibility": dict(sorted(refusals.items())),
        "refused_by_the_order_book": dict(sorted(refused_buckets.items())),
        "houses_the_book_refused": counts["houses_the_book_refused"],
        "size_drawn_histogram": {str(k): v for k, v in sorted(drawn_size.items())},
        "size_refused_histogram": {str(k): v for k, v in sorted(refused_size.items())},
        "kin_seated_histogram": {str(k): v for k, v in sorted(kin_size.items())},
        "drawn_into_bands": dict(sorted(drawn_band.items())),
        "fills": dict(sorted(fills.items())),
        "by_household": {k: per_card[k] for k in sorted(per_card)},
    }
    return out, ledger


# ------------------------------------------------------------------ the tables --

def present(live: dict) -> list:
    """The people the order book counts as the town: the present households alone. The
    still-unruled ones are the roster's, and measuring the whole layer against a town's
    sex ratio would measure the naming sources instead — the letter lists are 94.3% male
    and they are two records in three here.

    `present` here means what the ORDER BOOK means by it, which since T-1386 includes the
    820 households it ruled into the town. Counting only the cards that carry the word
    would measure this stage against a town of 1,140 that the book itself stopped using
    when it summed the rulings into `known` (T-1463)."""
    return [p for card in live.values() for p in (card.get("persons") or [])
            if settled_present(card)]


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


def model_range() -> list:
    for section in json.loads(MODEL.read_text(encoding="utf-8"))["sections"]:
        if section["key"] == "population":
            for figure in section["figures"]:
                if figure["figure"] == "males_per_100_females":
                    return [figure["low"], figure["high"]]
    return None


def measurement(base: dict, live: dict, ledger: dict) -> dict:
    """The acceptance's printed tables: the layer, against the model it was drawn from.

    THE SEX RATIO IS PRINTED AND IT IS NOT YET IN BRACKET, and that is a reading of the
    town rather than a defect of this stage. The present layer stood at 1,414.8 men per
    100 women aged twenty and over because two records in three are a letter-list name and
    that roll is 94.3% male. A wife for every head the sources leave alone moves it a long
    way and cannot close it: the women the pyramid still lacks are 855 people in T-1174's
    buckets, and the ratio reaches the model's range when they land and T-1179 converges
    the layer. Reporting it as met here would be the invention this programme exists to
    refuse."""
    model_size = table("households_and_families", "size_histogram_1840")["rows"]
    total_1840 = sum(int(r["households"]) for r in model_size if 1 <= int(r["size"]) <= KIN_MAX)
    shape = {str(r["size"]): round(int(r["households"]) / total_1840, 4)
             for r in model_size if 1 <= int(r["size"]) <= KIN_MAX}
    drawn_total = sum(ledger["size_drawn_histogram"].values()) or 1
    drawn = {k: round(v / drawn_total, 4) for k, v in ledger["size_drawn_histogram"].items()}

    before, _ = sex_ratio(present(base))
    after, adults = sex_ratio(present(live))
    wanted = model_range()
    people = present(live)
    pyramid = Counter()
    for person in people:
        band = person.get("age_band")
        low = band.get("low") if isinstance(band, dict) else None
        if low is not None:
            pyramid[book_band(int(low))] += 1
    return {
        "the_town_the_book_counts": "present households only",
        "people_before_this_stage": len(present(base)),
        "people_after_this_stage": len(people),
        "adults_after_this_stage": adults,
        "adult_sex_ratio_before": before,
        "adult_sex_ratio_after": after,
        "the_model_s_range": wanted,
        "inside_the_model_s_range": (after is not None and wanted is not None
                                     and wanted[0] <= after <= wanted[1]),
        "what_closes_it": "T-1174 (done, 856/856) and T-1347 (done, 308/308) drew the "
                          "women and children the pyramid was short, but they were drawn "
                          "as their own records and not into these houses: 310 married "
                          "houses this stage drew stand with no woman left in their cell. "
                          "Re-housing them is T-1179's convergence, and it is what closes "
                          "this ratio; nothing this stage may draw does.",
        "age_pyramid_after": dict(sorted(pyramid.items())),
        "household_size_1840_share": shape,
        "household_size_drawn_share": drawn,
        "largest_share_gap": round(max(
            abs(drawn.get(k, 0.0) - v) for k, v in shape.items()), 4) if shape else None,
    }


# --------------------------------------------------------------------- modes --

def build() -> int:
    base = {hid: without_this_pass(card) for hid, card in cards().items()}
    filled, ledger = fill(base)
    written = 0
    for hid, card in filled.items():
        path = HOUSEHOLDS / f"{hid}.json"
        text = dumps(card)
        if path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            written += 1
    ledger["measurement"] = measurement(base, filled, ledger)
    LEDGER.write_text(dumps(ledger), encoding="utf-8")
    write_fills(ledger)
    print("  wrote %s" % LEDGER.relative_to(ROOT))
    print("  %d card(s) rewritten; %d head(s) given a family, %d wives and %d children "
          "drawn" % (written, ledger["heads_drawn_for"], ledger["wives"], ledger["children"]))
    return 0


def write_fills(ledger: dict) -> None:
    """Carry this stage's fills into the order book and re-derive it. The book's own
    `--build` refuses an overfilled bucket, so the quota is enforced twice: once here as
    the draw is made, and once by the book that is the quota."""
    import build_order_book_1835 as ob
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    kept = [f for f in book.get("fills", []) if f.get("ticket") != TICKET]
    kept += [{"bucket": key, "ticket": TICKET, "stage": STAGE, "records": n,
              "by": "tools/reconstruct_modelled_families.py --build"}
             for key, n in sorted(ledger["fills"].items())]
    book["fills"] = kept
    BOOK.write_text(json.dumps(book, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ob.cmd_build()


def check() -> int:
    live = cards()
    base = {hid: without_this_pass(card) for hid, card in live.items()}
    filled, ledger = fill(base)
    bad = [hid for hid in sorted(live) if dumps(live[hid]) != dumps(filled[hid])]
    if bad:
        print("  FAIL %d card(s) are not what this stage derives: %s"
              % (len(bad), ", ".join(bad[:6])))
        return 1
    ledger["measurement"] = measurement(base, filled, ledger)
    if not LEDGER.exists() or LEDGER.read_text(encoding="utf-8") != dumps(ledger):
        print("  FAIL %s is not what --build writes" % LEDGER.relative_to(ROOT))
        return 1
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    ours_fills = {f["bucket"]: int(f.get("records") or 0)
                  for f in book.get("fills", []) if f.get("ticket") == TICKET}
    if ours_fills != {k: v for k, v in ledger["fills"].items()}:
        print("  FAIL the order book's fills for %s are not this stage's ledger" % TICKET)
        return 1
    print("  ok    %d head(s) carry a drawn family; %d people re-derive from their seeds"
          % (ledger["heads_drawn_for"], ledger["people_drawn"]))
    print("  ok    the order book carries %d fill(s) for %s and no bucket is overfilled"
          % (len(ours_fills), TICKET))
    return 0


def report() -> int:
    base = {hid: without_this_pass(card) for hid, card in cards().items()}
    filled, ledger = fill(base)
    stats = measurement(base, filled, ledger)
    print("HEADS THE SOURCES LEAVE ALONE, AND WHAT WAS DRAWN")
    print("   heads drawn for %5d   wives %5d   children %5d"
          % (ledger["heads_drawn_for"], ledger["wives"], ledger["children"]))
    print("WHY A HOUSEHOLD WAS PASSED OVER")
    for why, n in sorted(ledger["refused_by_eligibility"].items(), key=lambda kv: -kv[1]):
        print("   %5d  %s" % (n, why))
    print("HOUSES THE ORDER BOOK COULD NOT SEAT")
    print("   %5d  married houses the model drew and the book has no woman left for"
          % ledger["houses_the_book_refused"])
    for size, n in sorted(ledger["size_refused_histogram"].items(), key=lambda kv: int(kv[0])):
        print("   %5d  at size %s" % (n, size))
    print("HOUSEHOLD SIZE — the 1840 city against the size the model drew")
    for size in sorted(stats["household_size_1840_share"], key=int):
        print("   %2s  1840 %6.4f   drawn %6.4f" % (
            size, stats["household_size_1840_share"][size],
            stats["household_size_drawn_share"].get(size, 0.0)))
    print("   largest share gap %s" % stats["largest_share_gap"])
    print("THE TOWN THE BOOK COUNTS — present households, before and after the draw")
    print("   people %5d -> %5d   adult sex ratio %s -> %s   the model's range %s"
          % (stats["people_before_this_stage"], stats["people_after_this_stage"],
             stats["adult_sex_ratio_before"], stats["adult_sex_ratio_after"],
             stats["the_model_s_range"]))
    print("   inside the model's range: %s — %s"
          % (stats["inside_the_model_s_range"], stats["what_closes_it"]))
    for band, n in sorted(stats["age_pyramid_after"].items()):
        print("   %-9s %5d" % (band, n))
    if ledger["refused_by_the_order_book"]:
        print("REFUSED BY THE ORDER BOOK — the quota doing its job")
        for bucket, n in sorted(ledger["refused_by_the_order_book"].items()):
            print("   %5d  %s" % (n, bucket))
    return 0


# ------------------------------------------------------------------ self-test --

def self_test() -> int:
    failures = []

    checked = []

    def fires(what: str, ok: bool) -> None:
        print("   %-64s %s" % (what, "ok" if ok else "FAIL"))
        checked.append(what)
        if not ok:
            failures.append(what)

    base = {"id": "hh_x", "division": "south", "source_pass": "civic",
            "present_on_scene_date": {"value": "present"},
            "persons": [{"id": "x", "name": "John Smith", "relationship": "head",
                         "grade": "attested", "sex": "male",
                         "age_band": {"value": "30-39", "low": 30, "high": 39}}]}

    def card(**over):
        out = json.loads(json.dumps(base))
        out.update(over)
        return out

    fires("a present, civic, single-head, adult male household is eligible",
          eligibility(card())[0] is True)
    fires("an uncertain presence no ruling settles is refused",
          eligibility(card(present_on_scene_date={"value": "uncertain"}),
                      frozenset())[0] is False)
    fires("an uncertain presence T-1386 ruled present is admitted",
          eligibility(card(present_on_scene_date={"value": "uncertain"}),
                      frozenset({"hh_x"}))[0] is True)
    fires("an evidenced absence is refused however it was ruled",
          eligibility(card(present_on_scene_date={"value": "absent"}),
                      frozenset({"hh_x"}))[0] is False)
    fires("every household the rulings file names was ruled present",
          len(ruled_present()) == 820)
    fires("a letter-list mint is refused",
          eligibility(card(source_pass="letter_list"))[0] is False)
    fires("an evidence-only container is refused by its id",
          eligibility(card(id="hh_inf_cooper_north_04"), frozenset({"hh_inf_cooper_north_04"}))[0] is False)
    fires("an evidence-only container is refused by its name alone",
          eligibility(card(name="Evidence-only household — John Smith"))[0] is False)
    fires("the two evidence-only markers name the same five records",
          sorted(hid for hid, c in cards().items() if str(hid).startswith(EVIDENCE_ONLY_ID))
          == sorted(hid for hid, c in cards().items()
                    if str(c.get("name") or "").startswith(EVIDENCE_ONLY_NAME)))
    fires("no evidence-only container carries a person this stage drew",
          not [p_["id"] for c in cards().values() if evidence_only(c)
               for p_ in c.get("persons") or []
               if (p_.get("reconstruction") or {}).get("stage") == STAGE])
    fires("a household that already holds a second person is refused",
          eligibility(card(persons=base["persons"] + [dict(base["persons"][0], id="y")]))[0] is False)
    fires("the fort is refused", eligibility(card(division="fort"))[0] is False)
    fires("a household under a standing review is refused",
          eligibility(card(review_required=True))[0] is False
          and eligibility(card(touches_removal=True))[0] is False)
    fires("a head the sources place under a vow is refused",
          eligibility(card(persons=[dict(base["persons"][0],
                                         occupation={"value": "priest"})]))[0] is False)
    fires("a woman heading her own household is refused",
          eligibility(card(persons=[dict(base["persons"][0], sex="female")]))[0] is False)
    fires("a head under twenty is refused",
          eligibility(card(persons=[dict(base["persons"][0],
                                         age_band={"value": "15-19", "low": 15, "high": 19})]))[0] is False)
    fires("a head with no age band is refused",
          eligibility(card(persons=[{k: v for k, v in base["persons"][0].items()
                                     if k != "age_band"}]))[0] is False)

    fires("the same seed draws the same face twice",
          draw("hh_x:household_size") == draw("hh_x:household_size"))
    fires("two households draw different faces",
          draw("hh_x:household_size") != draw("hh_y:household_size"))
    fires("the size histogram is cut at the kin range",
          all(1 <= s <= KIN_MAX for s, _ in size_rows()))
    fires("a forename steps past a name the family already bears",
          forename("s", {"given_male": ["John", "Samuel"], "given_female": []},
                   "male", {"john"}) == "Samuel")
    fires("an age of 9 bands as a child", book_band(9) == "under_10")
    fires("an age of 50 bands as the open cohort", book_band(50) == "50_plus")
    fires("a surname is the head's last printed word",
          surname_of("[?] G. Abbot") == "Abbot")
    fires("a drawn person names the stage that wrote them",
          ours({"reconstruction": {"stage": STAGE}}) and not ours({"grade": "attested"}))

    print("   %d rule(s) checked, %d failed" % (len(checked), len(failures)))
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
