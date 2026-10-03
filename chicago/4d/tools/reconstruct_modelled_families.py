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
     the ground and would read as evidence of a family nobody drew. The ledger lists every
     house refused this way (`houses_the_book_refused_by_household`, 368 on 2026-10-03).
     T-1174 and T-1347 drew the women the pyramid was short as their OWN records rather
     than into these houses. `re_housing` (T-2019) measures how many of T-1174's
     woman-headed houses could be the wife and children of one of them, by this stage's
     own spacing rule and child cap, and T-2020 MAKES THOSE MOVES: each pair's woman-headed
     card folds into the refused house, she as his wife and her children with her (see
     `marry`). T-2021 rules on the houses no woman in the town fits. A move cannot close
     the sex ratio printed below — it puts nobody new in the town — and the measurement
     says so.

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
FOLDS = ROOT / "data" / "reconstruction" / "1835_folded_houses.json"
RULING = ROOT / "data" / "reconstruction" / "1835_family_ruling.json"

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
                  community: dict, head_name: str, ticket: str = TICKET) -> dict:
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
            "ticket": ticket,
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


def kin_core(hid: str, head_name: str, head_low: int, surname: str, community: dict,
             size: int, rows: tuple, take, card: dict, ticket: str = TICKET,
             avoid: frozenset = frozenset(), initials: frozenset = frozenset()) -> tuple:
    """(members, the wife cell that refused the house or None, their book bands, the
    child cells that refused a child). The wife and children of one married house, drawn
    by the household model's rules from seeds keyed on the house alone.

    `take(bucket)` says whether the cell will seat one more person, and spends it if so.
    The draw is the same whoever asks: the first pass asks the order book, and T-2021's
    ruling asks nothing, because its houses were admitted against the town's range before
    they were drawn. So a house the ruling admits draws the very family the book refused
    it — the same names, bands and seeds — and nothing about it depends on which pass
    seated it."""
    female_adult, child_bands, boy_rate = rows
    family_names = {surname.lower()}
    # `avoid` is every full name the rest of the layer already bears. A forename that
    # would make one of them under this surname is stepped past, exactly as a forename of
    # this family is — the first pass passes nothing, so its draw is the one it always was.
    tail = " " + surname.lower()
    family_names |= {n[:-len(tail)] for n in avoid if surname and n.endswith(tail)}
    # `initials` is every `surname|initial` key a real-name stage refuses to mint past.
    # A forename that would put this surname and initial on an invented person is
    # stepped past too, or the re-admission would read the invention as the real man
    # already in the town and withhold him.
    blocked = {k.split("|", 1)[1] for k in initials
               if surname and k.split("|", 1)[0] == readmit_key(f"x {surname}").split("|")[0]}
    if blocked:
        family_names |= {n.lower() for n in community["given_male"] + community["given_female"]
                         if n[:1].lower() in blocked}
    members, bands, short = [], [], []
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
        if not take(bucket):
            return [], bucket, [], []
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
            community, head_name, ticket))
        bands.append(book_band(low))

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
        if not take(bucket):
            short.append(bucket)
            continue
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
            community, head_name, ticket))
        bands.append(book_band(low))
    return members, None, bands, short


def place_block(card: dict, members: list, block: dict) -> None:
    """Seat `members` on the card and write this stage's block where it belongs.

    THE BLOCK GOES IMMEDIATELY AFTER `present_on_scene_date`, not at the end. Several
    research passes own a trailing key and rebuild the card by popping theirs and
    appending it again (`old_settler_deaths` before `directories`, in
    spend_old_settlers.py); a new key at the end would move under them and their
    byte-for-byte --check would read it as drift. `resident_mint_carry` puts it in this
    same slot when a mint rebuilds the card, and the two have to agree."""
    rebuilt = {}
    for key, value in card.items():
        rebuilt[key] = value
        if key == "present_on_scene_date":
            rebuilt["modelled_family"] = None  # placed, filled in below
    card.clear()
    card.update(rebuilt)
    card["persons"] = (card.get("persons") or []) + members
    card["modelled_family"] = block


def fill(base: dict, ruling: dict | None = None) -> tuple:
    """(cards with this stage's people, the ledger). Pure over `base` and the ruling."""
    if ruling is None:
        ruling = load_ruling()
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
    refused_houses = {}

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

        size = pick(seed_for(hid, "household_size"), [(s, n) for s, n in sizes])
        # THE SIZE HISTOGRAM MEASURES THE MODEL, NOT THE BOOK. Every eligible head is
        # counted here, before the order book has spoken, because what this table tests
        # is whether the 1840 size distribution is being SAMPLED faithfully. A house the
        # book then refuses is a fact about the quota and is counted as one, below.
        drawn_size[size] += 1
        members = []
        household_type = ("solitary" if size == 1
                          else "married_couple" if size == 2 else "family_with_children")

        def take(bucket: str) -> bool:
            if left.get(bucket, 0) <= 0:
                return False
            left[bucket] -= 1
            fills[bucket] += 1
            return True

        members, wife_cell, bands, short = kin_core(
            hid, head_name, head_low, surname, community, size,
            (female_adult, child_bands, boy_rate), take, card)
        if wife_cell is not None:
            # THE WIFE IS THE HOUSE. The model drew this house married; if the book
            # has no woman left for her cell, the married house is not a house this
            # stage may half-draw. Seating the children of a marriage the book would
            # not seat would put a fatherless-looking cottage of infants on the
            # ground and would read as evidence of a family nobody drew. The whole
            # house is refused, the cell that refused it is named, and the head is
            # left exactly as the sources leave him.
            refused_buckets[wife_cell] += 1
            refusals["the order book has no woman left in this house's cell"] += 1
            counts["houses_the_book_refused"] += 1
            refused_size[size] += 1
            refused_houses[hid] = {"wife_cell": wife_cell, "head_band_low": head_low,
                                   "size_drawn": size}
            continue
        counts["heads_drawn_for"] += 1
        for bucket in short:
            refused_buckets[bucket] += 1
        drawn_band.update(bands)
        if size >= 2:
            counts["wives"] += 1
        counts["children"] += len(members) - (1 if size >= 2 else 0)

        place_block(card, members, {
            "stage": STAGE,
            "ticket": TICKET,
            "household_type": household_type,
            "size_drawn": size,
            "kin_seated": 1 + len(members),
            "seed": seed_for(hid, "household_size"),
            "note": "The kin core only. A servant, an apprentice or a journeyman this "
                    "house may have held is priced by T-1183 and seated by T-1173; a "
                    "boarder is seated by T-1175. The drawn size is a floor on the house.",
        })
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
        "houses_the_book_refused_by_household": {k: refused_houses[k]
                                                  for k in sorted(refused_houses)},
    }
    ledger["re_housing"] = re_housing(base, refused_houses)

    # T-2020: THE PAIRS ARE CARRIED ONTO THE CARDS. Only after the draw and the
    # measurement, both of which read `base` and neither of which a fold may disturb: the
    # move is held to the numbers T-2019 measured, so it is made from them, never beside
    # them. Each host was refused whole above, so he still stands alone in `out`.
    folds = {}
    married = Counter()
    married_kin = Counter()
    for pair in ledger["re_housing"]["pairs"]:
        hid, her_hid = pair["house"], pair["wife_and_children_from"]
        size = refused_houses[hid]["size_drawn"]
        out[hid], folds[her_hid] = marry(out[hid], out.pop(her_hid), size,
                                         seed_for(hid, "household_size"))
        block = out[hid]["modelled_family"]
        per_card[hid] = {"size_drawn": size, "kin_seated": block["kin_seated"],
                         "household_type": block["household_type"],
                         "married_from": her_hid}
        married["houses"] += 1
        married["people"] += block["kin_seated"] - 1
        married[refused_houses[hid]["wife_cell"].split("/")[3]] += 1
        married_kin[block["kin_seated"]] += 1
    ledger["by_household"] = {k: per_card[k] for k in sorted(per_card)}
    ledger["married_from_the_town"] = {
        "ticket": FOLD_TICKET,
        "of": TICKET,
        "houses": married["houses"],
        "people_moved": married["people"],
        "by_division": {d: married[d] for d in CIVIL if married[d]},
        "kin_seated_histogram": {str(k): v for k, v in sorted(married_kin.items())},
        "houses_still_refused": len(refused_houses) - married["houses"],
        "what_moved": "Each pair of `re_housing` carried onto the cards: the woman-headed "
                      "house T-1174 dealt folds into the married house the order book "
                      "refused a wife, she as his wife and every member of her house with "
                      "her. Nobody is drawn, nobody is retired, no name, id, sex, age band "
                      "or seed changes, and the order book's person cells are untouched — "
                      "she is still counted where T-1174 dealt her. What the town loses is "
                      "a household for every pair; `%s` keeps each folded card's own keys "
                      "so the fold re-derives." % FOLDS.relative_to(ROOT),
    }

    # T-2021: THE HOUSES THE RULING ADMITS ARE GIVEN THEIR FAMILIES. Last of all, after
    # the folds, because the ruling is about the houses NO woman in the town could be wife
    # to, and which those are is only known once T-2020's pairs are made. The admitted
    # houses were read once and frozen in RULING (`--rule`), so nothing here is a live
    # quota: each house draws the very family the book refused it, by `kin_core`, with
    # the same seeds, and its people are filed as T-2021's fills, which is what the order
    # book orders for it. A frozen house that is no longer refused — a source named his
    # family, or a woman in the town now fits him — is passed over and counted, never
    # drawn twice.
    hosts = {pair["house"] for pair in ledger["re_housing"]["pairs"]}
    still_refused = [h for h in refused_houses if h not in hosts]
    rows = (female_adult, child_bands, boy_rate)
    # THE RULING DRAWS LAST AND MAY NOT TAKE A NAME ANOTHER STAGE STANDS ON. The trade
    # heads, the lodgers and the readmitted step past every name in `households/` when
    # they draw, so a ruled wife who happened to take one of their names would re-deal
    # them — and the businesses that adopted them by name with them. So the ruling steps
    # past every name the layer bears, on every card in every resident directory, and
    # every name this pass has already drawn — past the surname and first initial of every
    # real person the re-admission minted, which is the key it withholds a reading on —
    # and past every 1840 census head, because
    # the resident synthesis bridges any card whose name is the only one to match a
    # census head, and an invented child would be bridged to a real man's household.
    town = set(taken) | other_directory_names() | census_1840_heads()
    protected = readmitted_keys()
    ruled = Counter()
    ruled_kin = Counter()
    ruled_fills = Counter()
    ruled_band = Counter()
    passed_over = []

    def given(bucket: str) -> bool:
        ruled_fills[bucket] += 1
        return True

    for hid in ruling.get("houses") or []:
        if hid not in out or hid not in refused_houses or hid in hosts:
            passed_over.append(hid)
            continue
        card = out[hid]
        head = head_of(card)
        head_name = str(head.get("name") or "")
        size = refused_houses[hid]["size_drawn"]
        members, _, bands, _ = kin_core(
            hid, head_name, int(head["age_band"]["low"]), surname_of(head_name),
            community_for(head, hid, pool), size, rows, given, card, RULING_TICKET,
            town, protected)
        place_block(card, members, {
            "stage": STAGE,
            "ticket": TICKET,
            "household_type": "married_couple" if size == 2 else "family_with_children",
            "size_drawn": size,
            "kin_seated": 1 + len(members),
            "seed": seed_for(hid, "household_size"),
            "note": KIN_NOTE,
            RULED_KEY: {
                "ticket": RULING_TICKET,
                "what_happened": (
                    "DRAWN UNDER A RULING, NOT A QUOTA. The household model drew this "
                    "house married at %d, and the order book had no woman left in its "
                    "wife's cell; no woman the town already holds fits him either. "
                    "T-2021 ruled that such a house is given its whole drawn family while "
                    "the town stays inside the model's own range for 1 July 1835 — at "
                    "most 3,265, the November count — and this house was admitted "
                    "under it. The wife and children are the ones the model drew for "
                    "this house from its own seeds, at the `reconstructed` tier; no "
                    "source names them, and none says %s married." % (
                        size, head_name or "this head")),
            },
        })
        per_card[hid] = {"size_drawn": size, "kin_seated": 1 + len(members),
                         "household_type": card["modelled_family"]["household_type"],
                         "ruled": RULING_TICKET}
        town |= {" ".join(m["name"].split()).lower() for m in members}
        ruled["houses"] += 1
        ruled["wives"] += 1
        ruled["children"] += len(members) - 1
        ruled[refused_houses[hid]["wife_cell"].split("/")[3]] += 1
        ruled_kin[1 + len(members)] += 1
        ruled_band.update(bands)
    ledger["by_household"] = {k: per_card[k] for k in sorted(per_card)}
    ledger["family_ruling"] = {
        "ticket": RULING_TICKET,
        "of": TICKET,
        "ruling": ruling.get("ruling"),
        "frozen_in": str(RULING.relative_to(ROOT)),
        "houses_no_woman_in_the_town_fits": len(still_refused),
        "houses_admitted": ruling.get("admitted", len(ruling.get("houses") or [])),
        "houses_given_their_family": ruled["houses"],
        "frozen_houses_passed_over": sorted(passed_over),
        "houses_standing_alone": len(still_refused) - ruled["houses"],
        "people_drawn": ruled["wives"] + ruled["children"],
        "wives": ruled["wives"],
        "children": ruled["children"],
        "by_division": {d: ruled[d] for d in CIVIL if ruled[d]},
        "kin_seated_histogram": {str(k): v for k, v in sorted(ruled_kin.items())},
        "drawn_into_bands": dict(sorted(ruled_band.items())),
        "fills": dict(sorted(ruled_fills.items())),
        "the_bound": ruling.get("the_bound"),
    }
    return out, ledger, folds


# ------------------------------------------------------------- the re-housing --
#
# T-2019, piece 1 of 3 of the last bullet of T-1171. The bullet says the married houses the
# book refuses a wife are seated by MOVING women the town already holds — "no new woman is
# drawn for them; the ones already in the town are moved". Before anybody moves, this
# measures how many can be: which of T-1174's woman-headed houses could be the wife and
# children of which refused house, by the same rules this stage draws a wife by. It MOVES
# NOBODY and writes no card; T-2020 carries the pairs onto the cards and is held to these
# numbers, so the move cannot redefine its own success. T-2021 owns what is left over.

#: The stage whose houses are the pool. The bullet names T-1347's women too; they are not
#: in it, and the reason is written into `re_housing` rather than left to a reader.
WOMEN_PASS = "reconstructed_women_children"
WOMEN_TYPE = "female_headed"


def match(heads: list, women: list) -> list:
    """[(head household, woman's household)] — the most pairs the rules allow. Pure.

    `heads` is [(division, head band low, household id)]; `women` is [(division, the
    lowest head band she may marry, household id)]. A woman may be wife to a head of her
    own division whose band is at least her floor. That is a THRESHOLD, so the greedy
    order is the optimal one: serve the most constrained head first (lowest band), and
    give him the woman nobody younger could take (highest floor at or under his band).
    Ties break on the id, so the pairing is a function of the committed files."""
    pairs = []
    used = set()
    for division, low, hid in sorted(heads, key=lambda h: (h[0], h[1], h[2])):
        fits = [w for w in women
                if w[2] not in used and w[0] == division and w[1] <= low]
        if not fits:
            continue
        best = max(fits, key=lambda w: (w[1], w[2]))
        used.add(best[2])
        pairs.append((hid, best[2]))
    return pairs


def wife_floor(card: dict):
    """(the lowest head band this woman may marry into, why not) for one T-1174 house.

    The two rules are this stage's own, read from the other end: THE SPACING RULE puts a
    wife never above her husband's band, so he is at least her band; THE CHILD CAP puts no
    child older than his band's low minus twenty, so he is at least her eldest plus
    twenty. A house that would pass the kin range of eight once he joins it is held back,
    and so is one T-1564 has already re-familied (its card carries a move recorded on both
    ends, and a second move is T-2020's decision, not this measurement's)."""
    persons = card.get("persons") or []
    head = next((p for p in persons if p.get("id") == card.get("head")), None)
    band = (head or {}).get("age_band")
    if not isinstance(band, dict) or band.get("low") is None:
        return None, "the head carries no age band"
    if card.get("review_required") or card.get("touches_removal"):
        return None, "under a standing review"
    if 1 + len(persons) > KIN_MAX:
        return None, "past the kin range of %d once a husband joins it" % KIN_MAX
    if card.get("refamilied"):
        return None, "already re-familied by T-1564"
    floor = int(band["low"])
    for person in persons:
        child = person.get("age_band")
        if person is head or not isinstance(child, dict) or child.get("low") is None:
            continue
        floor = max(floor, int(child["low"]) + 20)
    return floor, None


def female_headed_share(households: list):
    heads = Counter()
    for card in households:
        head = next((p for p in card.get("persons") or []
                     if p.get("id") == card.get("head")), None)
        if head is not None:
            heads[value_of(head.get("sex_basis")) or head.get("sex")] += 1
    total = sum(heads.values())
    return heads["female"], total


TRADES = ROOT / "data" / "residents" / "reconstructed_trades"


def trade_women() -> str:
    """Why T-1347's women are not in the pool, with the counts read off their cards."""
    trades = Counter()
    for path in sorted(TRADES.glob("hh_*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        head = next((p for p in card.get("persons") or []
                     if p.get("id") == card.get("head")), None)
        if head is not None and head.get("sex") == "female":
            trades[(card.get("trade_household") or {}).get("trade")] += 1
    return ("T-1347's women, whom the bullet also names: %d of them, in "
            "`data/residents/reconstructed_trades/`, which the seating, staffing, business "
            "and lodging stages all read as heads of a trade. %d are dealt `domestic`, a "
            "live-in servant and the last person this model should marry, and %d "
            "`boarding_house_keeper`, the lodging stage's keepers. Moving them is a re-deal "
            "of those stages, not a re-housing." % (
                sum(trades.values()), trades["domestic"], trades["boarding_house_keeper"]))


def re_housing(base: dict, refused: dict) -> dict:
    """How many of the refused married houses the town's own women could be wife to."""
    ruled = ruled_present()
    heads = [(houses["wife_cell"].split("/")[3], houses["head_band_low"], hid)
             for hid, houses in refused.items()]
    women, held, held_back_ids = [], Counter(), set()
    pool = [card for card in base.values()
            if card.get("source_pass") == WOMEN_PASS
            and (card.get("women_children") or {}).get("household_type") == WOMEN_TYPE
            and settled_present(card, ruled)]
    for card in pool:
        floor, why = wife_floor(card)
        if floor is None:
            held[why] += 1
            if why == "already re-familied by T-1564":
                held_back_ids.add(card["id"])
            continue
        women.append((card.get("division"), floor, card["id"]))
    pairs = match(heads, women)
    widened = list(women)
    for card in pool:
        if card["id"] in held_back_ids:
            plain = dict(card)
            plain.pop("refamilied", None)
            floor, why = wife_floor(plain)
            if floor is not None:
                widened.append((card.get("division"), floor, card["id"]))
    widened_pairs = match(heads, widened)

    taken = {w for _, w in pairs}
    married = {h for h, _ in pairs}
    left_cells = Counter(refused[h]["wife_cell"] for h in refused if h not in married)
    households = [card for card in base.values() if settled_present(card, ruled)]
    women_heads, total = female_headed_share(households)
    moved = len(pairs)
    return {
        "ticket": "T-2019",
        "of": "T-1171",
        "moves_nobody": "A measurement, taken on the layer as T-1174 dealt it (the fold is "
                        "undone first), so the move cannot redefine its own success. T-2020 "
                        "carries exactly these pairs onto the cards (`married_from_the_town`), "
                        "and T-2021 rules on the houses no woman in the town can be wife to.",
        "the_pool": "T-1174's woman-headed houses (`%s`, household type `%s`), present on "
                    "the scene date. They stand in `data/residents/households/`, the same "
                    "directory as the heads this stage draws for." % (WOMEN_PASS, WOMEN_TYPE),
        "not_in_the_pool": trade_women(),
        "the_rules": [
            "the division of the refused wife's cell — the stage's own ledger allocation "
            "for a head whose card says `unplaced` — is the woman's card's division",
            "the spacing rule: a wife is never above her husband's band",
            "the child cap: no child of the house is older than his band's low minus 20",
            "the kin range: the joined house holds at most %d" % KIN_MAX,
        ],
        "houses_refused_a_wife": len(refused),
        "houses_refused_by_division": dict(sorted(Counter(h[0] for h in heads).items())),
        "woman_headed_houses": len(pool),
        "woman_headed_houses_by_division": dict(sorted(
            Counter(card.get("division") for card in pool).items())),
        "held_back": dict(sorted(held.items())),
        "matched": moved,
        "matched_by_division": dict(sorted(Counter(
            refused[h]["wife_cell"].split("/")[3] for h, _ in pairs).items())),
        "matched_if_the_re_familied_moved_too": len(widened_pairs),
        "houses_no_woman_in_the_town_fits": len(refused) - moved,
        "houses_no_woman_fits_by_wife_cell": dict(sorted(left_cells.items())),
        "women_left_heading_their_own_house": len(pool) - len(taken),
        "female_headed_households": {
            "before": [women_heads, total],
            "after": [women_heads - moved, total - moved],
            "share_before": round(women_heads / float(total), 4) if total else None,
            "share_after": (round((women_heads - moved) / float(total - moved), 4)
                            if total - moved else None),
            "note": "Present households, as the order book counts the town. A move folds "
                    "one house into another, so the town loses a household for every pair "
                    "and the female-headed share falls on both ends of the fraction.",
        },
        "pairs": [{"house": h, "wife_and_children_from": w} for h, w in pairs],
    }


# --------------------------------------------------------------------- the fold --
#
# T-2020, piece 2 of 3 of T-1171's last bullet. The pairs above are carried onto the cards:
# her card folds into his, she as his wife and her children with her. THE FOLD IS EXACT
# AND IT IS UNDONE BEFORE EVERY DERIVATION. Every stage here derives from the layer as it
# stood before it ran, and T-1174's derives her house from seeds keyed on that house — so
# both stages first `unfold` the committed layer back into the woman-headed houses T-1174
# dealt, draw from that, and fold again. What makes the fold exact is that it changes one
# word on one person (her `relationship`, `head` to `wife`), says so on her, and keeps the
# rest of her card in `FOLDS`, a derived file, rather than on his card: her arrival, her
# origin and the research note that says how her house was drawn are T-1174's statements
# about a house, and printed on his card they would read as his.

FOLD_TICKET = "T-2020"
#: T-2021, piece 3 of 3: the ruling on the houses no woman in the town can be wife to.
RULING_TICKET = "T-2021"
RULED_KEY = "ruled"
#: On every person a fold moved: the house they were dealt in and what they were in it.
FOLD_KEY = "folded_in"
#: Inside the host's `modelled_family`: whose house was folded in, and why.
MARRIED_KEY = "married"
KIN_NOTE = ("The kin core only. A servant, an apprentice or a journeyman this house may "
            "have held is priced by T-1183 and seated by T-1173; a boarder is seated by "
            "T-1175. The drawn size is a floor on the house.")


def load_folds() -> dict:
    if not FOLDS.exists():
        return {}
    return json.loads(FOLDS.read_text(encoding="utf-8")).get("houses") or {}


def folds_doc(folds: dict) -> dict:
    return {
        "_doc": "DERIVED — regenerate with tools/reconstruct_modelled_families.py --build. "
                "Do not hand-edit.",
        "id": "1835_folded_houses",
        "ticket": FOLD_TICKET,
        "of": TICKET,
        "generated_by": "tools/reconstruct_modelled_families.py --build",
        "what_this_is": "The woman-headed houses T-1174 dealt that T-2020 folded into a "
                        "married house the order book had refused a wife. Each is the "
                        "folded card as it stood, its `persons` cut to the ids that now "
                        "stand on the host's card. It is how the fold is undone before "
                        "every derivation (`unfold`), so both stages draw from the layer "
                        "T-1174 dealt and `--check` re-derives the fold byte for byte. It "
                        "is not a record of a household the town holds: these houses are "
                        "gone from it, and their people keep house with the men named in "
                        "`folded_into`.",
        "houses": {k: folds[k] for k in sorted(folds)},
    }


def marry(host: dict, her: dict, size: int, seed: str) -> tuple:
    """(his card with her house folded in, the folded card's sidecar row). Pure.

    `host` is a card this stage drew a married house for and the order book refused a
    wife: one head, no block of this stage's on it. `her` is a T-1174 woman-headed house
    as that stage dealt it."""
    moved = []
    for person in her.get("persons") or []:
        record = json.loads(json.dumps(person))
        dealt_as = record.get("relationship")
        if record.get("id") == her.get("head"):
            record["relationship"] = "wife"
        record[FOLD_KEY] = {
            "ticket": FOLD_TICKET,
            "from_household": her["id"],
            "relationship_as_dealt": dealt_as,
        }
        moved.append(record)
    wife = next(p for p in moved if p.get("id") == her.get("head"))
    head_name = str((head_of(host) or {}).get("name") or "")
    block = {
        "stage": STAGE,
        "ticket": TICKET,
        "household_type": "married_couple" if len(moved) == 1 else "family_with_children",
        "size_drawn": size,
        "kin_seated": 1 + len(moved),
        "seed": seed,
        "note": KIN_NOTE,
        MARRIED_KEY: {
            "ticket": FOLD_TICKET,
            "wife": wife["id"],
            "from_household": her["id"],
            "what_happened": (
                "NOT DRAWN FOR THIS HOUSE: MOVED INTO IT. The household model drew this "
                "house married and the order book had no woman left in its wife's cell, so "
                "no wife was drawn. %s headed a house of her own, dealt by T-1174 to fill "
                "the women and children the age pyramid lacked; she fits this house by its "
                "own rules — her division, a band never above his, no child older than his "
                "band allows — and T-2020 folds her house into his: she is his wife here and "
                "the %d of her house come with her. Every name, age band and seed is the "
                "one T-1174 drew; the children keep the surname they were dealt with. Both "
                "people are the town's invention at the `reconstructed` tier, and the "
                "marriage is too: no source says %s married anybody."
                % (wife.get("name"), len(moved) - 1, head_name or "this head")),
        },
    }
    out = {}
    for key, value in host.items():
        out[key] = value
        if key == "present_on_scene_date":
            out["modelled_family"] = block
    if "modelled_family" not in out:
        out["modelled_family"] = block
    out["persons"] = list(host.get("persons") or []) + moved
    card = json.loads(json.dumps(her))
    card["persons"] = [p["id"] for p in her.get("persons") or []]
    return out, {"folded_into": host["id"], "card": card}


def unfold(live: dict, folds: dict | None = None) -> tuple:
    """(the layer as T-1174 dealt it, {folded house: host}). The inverse of `marry`.

    Every folded house is restored from `FOLDS` with its own people taken back off the
    host, and every host is stripped of what the fold put there. A folded person no row
    accounts for, or a row whose people are not all on its host, is refused by name: the
    fold is undone exactly or not at all."""
    folds = load_folds() if folds is None else folds
    out = dict(live)
    hosts = {}
    for her_hid, row in sorted(folds.items()):
        host = live.get(row.get("folded_into"))
        if host is None:
            raise SystemExit("FAIL %s is folded into %s, which the layer does not hold"
                             % (her_hid, row.get("folded_into")))
        if her_hid in live:
            raise SystemExit("FAIL %s stands as a card AND as a house folded into %s"
                             % (her_hid, host["id"]))
        moved = {p["id"]: p for p in host.get("persons") or []
                 if (p.get(FOLD_KEY) or {}).get("from_household") == her_hid}
        card = json.loads(json.dumps(row["card"]))
        if set(card["persons"]) != set(moved):
            raise SystemExit("FAIL the people of %s on %s are not the folded house's"
                             % (her_hid, host["id"]))
        restored = []
        for pid in card["persons"]:
            person = json.loads(json.dumps(moved[pid]))
            person["relationship"] = person.pop(FOLD_KEY)["relationship_as_dealt"]
            restored.append(person)
        card["persons"] = restored
        out[her_hid] = card
        hosts[her_hid] = host["id"]
    for hid, card in live.items():
        stray = [p.get("id") for p in card.get("persons") or []
                 if FOLD_KEY in p and p[FOLD_KEY].get("from_household") not in hosts]
        if stray:
            raise SystemExit("FAIL %s carries folded people no fold accounts for: %s"
                             % (hid, ", ".join(stray[:4])))
        if hid not in hosts.values():
            continue
        stripped = json.loads(json.dumps(card))
        stripped["persons"] = [p for p in stripped["persons"] if FOLD_KEY not in p]
        block = stripped.get("modelled_family")
        if isinstance(block, dict):
            block.pop(MARRIED_KEY, None)
        out[hid] = stripped
    return out, hosts


def female_headed_now(live: dict):
    """[female-headed, households] over the present households of the layer as it stands."""
    ruled = ruled_present()
    return list(female_headed_share([c for c in live.values() if settled_present(c, ruled)]))


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


def what_closes_it(ledger: dict) -> str:
    """The sentence the measurement ends on, with its counts read off the ledger.

    It said for a week that re-housing T-1174's and T-1347's women "is what closes this
    ratio", with 310 typed into it while the ledger beside it counted 368. Both were
    wrong, and T-2019 is where that was measured: a move puts nobody new in the town, so
    it cannot move a count of men against women at all."""
    rh = ledger.get("re_housing") or {}
    fr = ledger.get("family_ruling") or {}
    return ("NO MOVE CLOSES IT, AND THE RULING ONLY NARROWS IT. %d married houses stood "
            "refused because the book had no woman left in their cell. %d took the wife and "
            "children of one of T-1174's woman-headed houses (T-2019, T-2020), which moves "
            "nobody between the sexes. Of the %d no woman in the town fits, T-2021's ruling "
            "gave %d their whole drawn family (%d people) while the town stays inside the "
            "model's range for 1 July 1835, and %d stand alone because their families would "
            "carry it past the 3,265 the range ends at. What is left of the gap is the adult "
            "men the town already holds: there are more of them than a town of that size has "
            "women for." % (
                ledger["houses_the_book_refused"], rh.get("matched", 0),
                rh.get("houses_no_woman_in_the_town_fits", 0),
                fr.get("houses_given_their_family", 0), fr.get("people_drawn", 0),
                fr.get("houses_standing_alone", 0)))


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
        "what_closes_it": what_closes_it(ledger),
        "female_headed_households_after_the_moves": female_headed_now(live),
        "age_pyramid_after": dict(sorted(pyramid.items())),
        "household_size_1840_share": shape,
        "household_size_drawn_share": drawn,
        "largest_share_gap": round(max(
            abs(drawn.get(k, 0.0) - v) for k, v in shape.items()), 4) if shape else None,
    }


# --------------------------------------------------------------------- modes --

# ------------------------------------------------------------------- the ruling --
#
# T-2021, piece 3 of 3 of T-1171's last bullet: the houses no woman in the town can be wife
# to. The ticket offered two answers — a re-cut that orders more women, or heads that stand
# alone — and the ruling is BOTH, partitioned by a bound the order book already carries
# rather than one invented here: the town model's range for 1 July 1835, whose top is the
# November 1835 town count (3,265). Every such house drawn whole would carry the town past
# that count; a wife and no children would leave houses the model drew at five to eight as
# childless couples in a town whose under-ten share is already below the model's bracket.
# So a house is given its WHOLE drawn family, in a seeded order, while the town the book
# converges to stays at or under the count, and a house whose family would carry it past
# stands alone. The 1,254 adult men already present are what put the town near the top of
# its range: at the model's own 146.8 they imply about 854 adult women, and 288 stand.
#
# THE ADMITTED HOUSES ARE READ ONCE AND FROZEN (`--rule`), the T-1538 shape: a re-cut of
# the book, or a stage upstream drawing one more person, must not re-deal a family this
# ruling seated. `--build` reads the frozen list and never recomputes it.

def other_directory_names() -> set:
    """Every person's name on a card outside `households/` — the trade heads, the lodgers,
    the readmitted, the transients and the institutions — lower-cased and single-spaced."""
    out = set()
    for directory in sorted(HOUSEHOLDS.parent.iterdir()):
        if not directory.is_dir() or directory == HOUSEHOLDS:
            continue
        for path in sorted(directory.glob("hh_*.json")):
            for person in json.loads(path.read_text(encoding="utf-8")).get("persons") or []:
                name = " ".join(str(person.get("name") or "").split()).lower()
                if name:
                    out.add(name)
    return out


def readmit_key(name: str) -> str:
    from readmit_borderline_roster import name_key
    return name_key(name)


def readmitted_keys() -> set:
    """`surname|initial` of every person `readmit_borderline_roster.py` minted under a read
    name. They carry `grade: reconstructed` — the presence is the reconstruction — but the
    name is a reading, so it is the one an invention must not stand in front of."""
    out = set()
    for path in sorted((HOUSEHOLDS.parent / "readmitted").glob("hh_*.json")):
        for person in json.loads(path.read_text(encoding="utf-8")).get("persons") or []:
            key = readmit_key(person.get("name"))
            if key:
                out.add(key)
    return out


def census_1840_heads() -> set:
    """The 1840 census heads the resident synthesis bridges a card to by name, keyed the
    way it keys them (`synthesize_resident_research.name_key`)."""
    import csv
    from synthesize_resident_research import CENSUS_CSV, name_key
    if not CENSUS_CSV.exists():
        return set()
    out = set()
    with CENSUS_CSV.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            key = name_key(row.get("head_name_normalized") or row.get("head_name_transcribed"))
            if key:
                out.add(key)
    return out


def load_ruling() -> dict:
    if not RULING.exists():
        return {}
    return json.loads(RULING.read_text(encoding="utf-8"))


def population_top() -> int:
    for section in json.loads(MODEL.read_text(encoding="utf-8"))["sections"]:
        if section["key"] == "population":
            for figure in section["figures"]:
                if figure["figure"] == "population_on_1_july_1835":
                    return int(figure["high"])
    raise SystemExit("the town model carries no population_on_1_july_1835 range")


def admit(houses: list, kin: dict, room: int) -> tuple:
    """(admitted, standing alone). Pure. `houses` in the order they are served; a house is
    admitted whole if its kin fit the room left, and otherwise stands alone while the
    houses after it are still offered what is left — so the room is spent, never
    overrun, and no house is half-drawn."""
    admitted, alone = [], []
    for hid in houses:
        if kin[hid] <= room:
            admitted.append(hid)
            room -= kin[hid]
        else:
            alone.append(hid)
    return admitted, alone


def lodging_place_ids() -> set:
    """Every place the lodging model gives beds, which T-1371 deals."""
    from seat_lodgers_1835 import lodging_model
    return {place["id"] for place in lodging_model().get("places") or []}


def ruling_order(hid: str) -> str:
    return hashlib.blake2s(seed_for(hid, "family_ruling_order").encode("utf-8")).hexdigest()


def rule(force: bool = False) -> int:
    """Read the ruling's houses once, and freeze them."""
    if RULING.exists() and not force:
        print("  REFUSED %s is frozen; --rule --force re-reads it, and re-deals every "
              "family it seats" % RULING.relative_to(ROOT))
        return 1
    base = base_layer(cards())
    _, ledger, _ = fill(base, {})
    hosts = {pair["house"] for pair in ledger["re_housing"]["pairs"]}
    refused = ledger["houses_the_book_refused_by_household"]
    # A HEAD WHOSE CARD ALREADY LIVES AT A LODGING PLACE IS NOT OFFERED. His bed is one of
    # the lodging model's, which T-1371 deals; a family drawn onto it would take beds the
    # boarders stand on and re-deal them — and the businesses that adopted them by name.
    inns = lodging_place_ids()
    lodged = sorted(h for h in refused if h not in hosts
                    and value_of(base[h].get("lives_at")) in inns)
    candidates = sorted((h for h in refused if h not in hosts and h not in lodged),
                        key=lambda h: (ruling_order(h), h))
    kin = {h: refused[h]["size_drawn"] - 1 for h in candidates}
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    already = sum(int(f.get("records") or 0) for f in book.get("fills") or []
                  if f.get("ticket") == RULING_TICKET)
    converges = int(book["totals"]["persons_when_the_book_is_filled"]) - already
    top = population_top()
    admitted, alone = admit(candidates, kin, top - converges)
    doc = {
        "_doc": "FROZEN — written once by tools/reconstruct_modelled_families.py --rule and "
                "read by --build; it is not re-derived, so a re-cut re-deals nobody it "
                "seats (the T-1538 shape). Do not hand-edit.",
        "id": "1835_family_ruling",
        "ticket": RULING_TICKET,
        "of": TICKET,
        "target_date": SCENE_DATE,
        "not_a_reading": "a ruling over committed derived files — no page of any source "
                         "was opened",
        "ruling": "A married house the order book refused a wife, and no woman in the "
                  "town fits, is given its whole drawn family — wife and children, by the "
                  "stage's own seeds — while the town the book converges to stays inside "
                  "the town model's range for 1 July 1835; a house whose family would "
                  "carry it past the range's top stands alone.",
        "the_bound": {
            "population_on_1_july_1835_top": top,
            "what_the_top_is": "the November 1835 town count; the town model's range for "
                               "the scene date ends at it",
            "the_book_converged_to_without_the_ruling": converges,
            "room": top - converges,
            "kin_offered": sum(kin.values()),
            "kin_admitted": sum(kin[h] for h in admitted),
            "the_town_converges_to": converges + sum(kin[h] for h in admitted),
        },
        "order": "blake2s of `<house>:family_ruling_order`, then the id; a house whose "
                 "family does not fit the room left stands alone and the houses after it "
                 "are still offered the rest",
        "houses_offered": len(candidates),
        "not_offered_living_at_a_lodging_place": lodged,
        "admitted": len(admitted),
        "standing_alone": len(alone),
        "houses": admitted,
        "alone": alone,
    }
    RULING.write_text(dumps(doc), encoding="utf-8")
    print("  froze %s: %d of %d houses admitted, %d kin, the town converges to %d of %d"
          % (RULING.relative_to(ROOT), len(admitted), len(candidates),
             doc["the_bound"]["kin_admitted"], doc["the_bound"]["the_town_converges_to"], top))
    return 0


def base_layer(live: dict) -> dict:
    """The layer as it stood before this stage ran: unfolded, then this pass stripped."""
    return {hid: without_this_pass(card) for hid, card in unfold(live)[0].items()}


def build() -> int:
    base = base_layer(cards())
    filled, ledger, folds = fill(base)
    written = 0
    for hid, card in filled.items():
        path = HOUSEHOLDS / f"{hid}.json"
        text = dumps(card)
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            written += 1
    for hid in sorted(folds):
        path = HOUSEHOLDS / f"{hid}.json"
        if path.exists():
            path.unlink()
            written += 1
    FOLDS.write_text(dumps(folds_doc(folds)), encoding="utf-8")
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
    rows = [{"bucket": key, "ticket": TICKET, "stage": STAGE, "records": n,
              "by": "tools/reconstruct_modelled_families.py --build"}
             for key, n in sorted(ledger["fills"].items())]
    # T-2021's draw is filed under its own ticket: the book ORDERS exactly these, so its
    # rows have to be told apart from the quota T-1171 drew against.
    rows += [{"bucket": key, "ticket": RULING_TICKET, "stage": STAGE, "records": n,
              "by": "tools/reconstruct_modelled_families.py --build"}
             for key, n in sorted(ledger["family_ruling"]["fills"].items())]
    book["fills"] = ob.splice_fills(book.get("fills", []), {TICKET, RULING_TICKET}, rows)
    BOOK.write_text(json.dumps(book, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ob.cmd_build()


def check() -> int:
    live = cards()
    base = base_layer(live)
    filled, ledger, folds = fill(base)
    if set(live) != set(filled):
        print("  FAIL the layer's cards are not the set this stage leaves (%d standing, "
              "%d derived; folded but standing %s; missing %s)"
              % (len(live), len(filled), sorted(set(live) - set(filled))[:4],
                 sorted(set(filled) - set(live))[:4]))
        return 1
    bad = [hid for hid in sorted(live) if dumps(live[hid]) != dumps(filled[hid])]
    if bad:
        print("  FAIL %d card(s) are not what this stage derives: %s"
              % (len(bad), ", ".join(bad[:6])))
        return 1
    if not FOLDS.exists() or FOLDS.read_text(encoding="utf-8") != dumps(folds_doc(folds)):
        print("  FAIL %s is not what --build writes" % FOLDS.relative_to(ROOT))
        return 1
    ledger["measurement"] = measurement(base, filled, ledger)
    if not LEDGER.exists() or LEDGER.read_text(encoding="utf-8") != dumps(ledger):
        print("  FAIL %s is not what --build writes" % LEDGER.relative_to(ROOT))
        return 1
    # THE MOVE IS HELD TO THE MEASUREMENT. T-2019 printed what the female-headed share
    # would become if its pairs were made; the layer that now stands must read exactly that.
    promised = ledger["re_housing"]["female_headed_households"]["after"]
    stands = ledger["measurement"]["female_headed_households_after_the_moves"]
    if promised != stands:
        print("  FAIL the moves leave %s female-headed households of %s; T-2019 measured %s"
              % (stands[0], stands[1], promised))
        return 1
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    ours_fills = {f["bucket"]: int(f.get("records") or 0)
                  for f in book.get("fills", []) if f.get("ticket") == TICKET}
    if ours_fills != {k: v for k, v in ledger["fills"].items()}:
        print("  FAIL the order book's fills for %s are not this stage's ledger" % TICKET)
        return 1
    ruled_fills = {f["bucket"]: int(f.get("records") or 0)
                   for f in book.get("fills", []) if f.get("ticket") == RULING_TICKET}
    if ruled_fills != ledger["family_ruling"]["fills"]:
        print("  FAIL the order book's fills for %s are not the ruling's draw" % RULING_TICKET)
        return 1
    fr = ledger["family_ruling"]
    if fr["frozen_houses_passed_over"]:
        print("  FAIL %d house(s) the ruling froze are no longer refused a wife (%s): the "
              "ruling stands on a layer that has moved under it — re-read it with --rule "
              "--force and say why" % (len(fr["frozen_houses_passed_over"]),
                                       ", ".join(fr["frozen_houses_passed_over"][:4])))
        return 1
    converges = int(book["totals"]["persons_when_the_book_is_filled"])
    if fr["houses_admitted"] and converges > population_top():
        print("  FAIL the town the book converges to is %d, past the %d the ruling is "
              "bounded by" % (converges, population_top()))
        return 1
    print("  ok    %d head(s) carry a drawn family; %d people re-derive from their seeds"
          % (ledger["heads_drawn_for"], ledger["people_drawn"]))
    print("  ok    %d woman-headed house(s) fold into a refused married house, exactly the "
          "pairs T-2019 measured" % ledger["married_from_the_town"]["houses"])
    print("  ok    the order book carries %d fill(s) for %s and no bucket is overfilled"
          % (len(ours_fills), TICKET))
    print("  ok    %d house(s) given their family under %s's ruling (%d people); the town "
          "converges to %d of %d" % (fr["houses_given_their_family"], RULING_TICKET,
                                     fr["people_drawn"], converges, population_top()))
    return 0


def report() -> int:
    base = base_layer(cards())
    filled, ledger, _ = fill(base)
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
    rh = ledger["re_housing"]
    fh = rh["female_headed_households"]
    print("THE RE-HOUSING THE TOWN'S OWN WOMEN ALLOW — measured on the layer as dealt (T-2019)")
    print("   %5d  houses refused a wife   %s"
          % (rh["houses_refused_a_wife"], rh["houses_refused_by_division"]))
    print("   %5d  woman-headed houses     %s"
          % (rh["woman_headed_houses"], rh["woman_headed_houses_by_division"]))
    for why, n in rh["held_back"].items():
        print("   %5d    held back: %s" % (n, why))
    print("   %5d  pairs the rules allow   %s   (%d if the re-familied moved too)"
          % (rh["matched"], rh["matched_by_division"],
             rh["matched_if_the_re_familied_moved_too"]))
    print("   %5d  houses no woman in the town fits" % rh["houses_no_woman_in_the_town_fits"])
    for cell, n in rh["houses_no_woman_fits_by_wife_cell"].items():
        print("   %5d    %s" % (n, cell))
    print("   %5d  women left heading their own house"
          % rh["women_left_heading_their_own_house"])
    print("   female-headed households %d of %d (%s) -> %d of %d (%s)"
          % (fh["before"][0], fh["before"][1], fh["share_before"],
             fh["after"][0], fh["after"][1], fh["share_after"]))
    mt = ledger["married_from_the_town"]
    print("THE MOVES MADE (T-2020)")
    print("   %5d  woman-headed houses folded into a married house   %s"
          % (mt["houses"], mt["by_division"]))
    print("   %5d  people moved, the women among them   kin seated %s"
          % (mt["people_moved"], mt["kin_seated_histogram"]))
    print("   %5d  married houses still refused a wife (T-2021)" % mt["houses_still_refused"])
    print("   female-headed households now %s"
          % (stats["female_headed_households_after_the_moves"],))
    fr = ledger["family_ruling"]
    bound = fr.get("the_bound") or {}
    print("THE RULING ON THE HOUSES NO WOMAN IN THE TOWN FITS (T-2021)")
    print("   %5d  houses no woman in the town fits" % fr["houses_no_woman_in_the_town_fits"])
    print("   %5d  given their whole drawn family   %s   kin seated %s"
          % (fr["houses_given_their_family"], fr["by_division"], fr["kin_seated_histogram"]))
    print("   %5d  people drawn: %d wives, %d children"
          % (fr["people_drawn"], fr["wives"], fr["children"]))
    print("   %5d  houses standing alone — their families would carry the town past %s"
          % (fr["houses_standing_alone"], bound.get("population_on_1_july_1835_top")))
    print("   the town the book converges to: %s without the ruling, %s with it"
          % (bound.get("the_book_converged_to_without_the_ruling"),
             bound.get("the_town_converges_to")))
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
    # T-1525 RESTATED THIS FROM 820 TO 936, AND THE NUMBER IS THE POINT OF THE GUARD.
    # `1835_presence_rulings.json` is DERIVED, so it re-derives over whatever layer it is
    # run against; a literal here is what makes a population change arrive as a decision
    # instead of as a silent re-count. Minting the 120 households St Mary's baptismal
    # register names put 116 more households through the same adjudication, every one of
    # them ruled `present` — the file still carries no other verdict, which is the half of
    # this assertion that is not the count.
    fires("every household the rulings file names was ruled present",
          len(ruled_present()) == 936)
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

    # T-2019, the re-housing measurement.
    fires("a woman marries only into her own division",
          match([("south", 30, "hh_h")], [("west", 20, "hh_w")]) == [])
    fires("a woman is never wife to a head below her floor",
          match([("south", 20, "hh_h")], [("south", 30, "hh_w")]) == [])
    fires("the lowest head is served first and takes the highest floor he fits",
          match([("south", 40, "hh_b"), ("south", 20, "hh_a")],
                [("south", 20, "hh_x"), ("south", 40, "hh_y")])
          == [("hh_a", "hh_x"), ("hh_b", "hh_y")])
    fires("no woman is wife to two heads",
          len(match([("south", 30, "hh_a"), ("south", 30, "hh_b")],
                    [("south", 20, "hh_x")])) == 1)
    woman = {"id": "hh_w", "head": "w", "persons": [
        {"id": "w", "sex": "female", "age_band": {"low": 20}},
        {"id": "c", "sex": "male", "age_band": {"low": 15}}]}
    fires("the child cap lifts a woman's floor to her eldest plus twenty",
          wife_floor(woman)[0] == 35)
    fires("a house past the kin range is held back",
          wife_floor(dict(woman, persons=woman["persons"] + [
              {"id": "k%d" % i, "age_band": {"low": 0}} for i in range(KIN_MAX - 2)]))[0]
          is None)
    fires("a house T-1564 already re-familied is held back",
          wife_floor(dict(woman, refamilied={"rule": "C1"}))[0] is None)
    live = cards()
    filled, ledger, folds = fill(base_layer(live))
    fires("every pair names a refused house",
          all(p_["house"] in ledger["houses_the_book_refused_by_household"]
              for p_ in ledger["re_housing"]["pairs"]))

    # T-2020, the fold.
    head = {"id": "hh_h", "head": "h", "present_on_scene_date": {"value": "present"},
            "persons": [{"id": "h", "name": "John Smith", "relationship": "head"}]}
    hers = {"id": "hh_w", "head": "w", "division": "south", "women_children": {},
            "persons": [{"id": "w", "name": "Mary Brown", "relationship": "head"},
                        {"id": "c", "name": "Ann Brown", "relationship": "daughter"}]}
    host, row = marry(head, hers, 4, "hh_h:household_size")
    fires("she is his wife and her children come with her",
          [(p_["id"], p_["relationship"]) for p_ in host["persons"]]
          == [("h", "head"), ("w", "wife"), ("c", "daughter")])
    fires("the block sits after the presence, as a drawn family's does",
          list(host)[list(host).index("present_on_scene_date") + 1] == "modelled_family")
    fires("nobody is renamed by the fold",
          [p_["name"] for p_ in host["persons"][1:]] == ["Mary Brown", "Ann Brown"])
    back, hosts = unfold({"hh_h": host}, {"hh_w": row})
    fires("unfold restores her card exactly", dumps(back["hh_w"]) == dumps(hers))
    fires("unfold strips the host back to his lone head",
          [p_["id"] for p_ in back["hh_h"]["persons"]] == ["h"]
          and MARRIED_KEY not in back["hh_h"]["modelled_family"] and hosts == {"hh_w": "hh_h"})
    stray = json.loads(json.dumps(host))
    try:
        unfold({"hh_h": stray}, {})
        fires("a folded person no fold accounts for is refused", False)
    except SystemExit:
        fires("a folded person no fold accounts for is refused", True)
    try:
        unfold({"hh_h": host, "hh_w": hers}, {"hh_w": row})
        fires("a house both standing and folded is refused", False)
    except SystemExit:
        fires("a house both standing and folded is refused", True)
    fires("the fold carries exactly the measured pairs",
          sorted(folds) == sorted(p_["wife_and_children_from"]
                                  for p_ in ledger["re_housing"]["pairs"]))
    fires("no folded house stands in the layer", not set(folds) & set(filled))

    # T-2021: THE RULING'S ADMISSION. Whole houses, in order, never past the room.
    got, alone = admit(["a", "b", "c", "d"], {"a": 3, "b": 5, "c": 1, "d": 2}, 6)
    fires("the ruling admits whole houses and never overruns the range's room",
          got == ["a", "c", "d"] and alone == ["b"])
    fires("a house too big for what is left stands alone and smaller ones are still offered",
          admit(["x", "y"], {"x": 9, "y": 1}, 4) == (["y"], ["x"]))
    fires("no room admits nobody", admit(["a"], {"a": 1}, 0) == ([], ["a"]))
    _, frozen_ledger, _ = fill(base_layer(cards()), {"houses": ["hh_no_such_house"]})
    fires("a frozen house that is no longer refused is passed over, never drawn",
          frozen_ledger["family_ruling"]["frozen_houses_passed_over"] == ["hh_no_such_house"]
          and frozen_ledger["family_ruling"]["houses_given_their_family"] == 0)
    fires("the frozen ruling admits no house past the model's range",
          (load_ruling().get("the_bound") or {}).get("the_town_converges_to", 0)
          <= population_top())

    print("   %d rule(s) checked, %d failed" % (len(checked), len(failures)))
    return 1 if failures else 0


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--rule", action="store_true",
                    help="read T-2021's admitted houses once and freeze them")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    if args.rule:
        return rule(args.force)
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
