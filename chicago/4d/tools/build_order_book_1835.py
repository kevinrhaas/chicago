#!/usr/bin/env python3
"""THE 1835 RECONSTRUCTION ORDER BOOK: known minus model, resolved into work.

T-1166, which closes the 1835 TOWN ANALYSIS band. Every model above states a
TARGET (T-1293, folding T-1161..T-1165); the profile states what is KNOWN
(T-1160); the roster states which REAL NAMES are still on offer (T-1159). The
order book is the subtraction — and, because a subtraction nobody can spend is
just another number, it is the subtraction resolved into buckets, each with the
ticket that owns filling it and a counter that ticket writes back.

    tools/build_order_book_1835.py --build       write the book and its report
    tools/build_order_book_1835.py --check       re-derive both and refuse drift
    tools/build_order_book_1835.py --self-test   the guards, fired on fixtures

WHAT THIS TOOL IS.  An ADJUDICATION over files this repository already holds and
already gates, exactly as the town model is. It reads no page of any source,
opens no network, names nobody, ages nobody, houses nobody, and creates no
person, household, business or building. Every quantity it prints is a function
of a committed derived file, and the file is named beside the quantity.

WHAT A BUCKET IS.  A cell of the town, keyed by the axes the models bound:
persons by sex x age band x division x household type x trade, households by
type x division, businesses by class, structures by archetype group x division.
Each carries `target` (the model), `known_attested` / `known_inferred` (the
layer), `to_reconstruct` (the difference), the `owning_ticket` that must fill
it, and `filled` — the counter a filler increments through its own `--build`.

THE FOUR RULES THIS BOOK ADDS, AND WHY EACH IS STATED RATHER THAN HIDDEN.

1. A POINT FROM A RANGE.  The town model answers in ranges on purpose, and a
   quota cannot be a range: a filler asked for "between 469 and 816 households"
   builds nothing. Where the model gives a `point` the book takes it; where it
   gives only `low` and `high` the book takes the MIDPOINT, rounds half up, and
   carries the range beside it so the reader can see the width of what was
   collapsed. The midpoint is a planning figure and never a claim about 1835.

2. THE UNRESOLVED KNOWN.  A named person the layer cannot place in a cell is
   still a person standing in the town, and a book that ignored them would order
   their replacement a second time. So the known who cannot be resolved onto an
   axis are subtracted PRO RATA across the cells of that axis, which is the only
   distribution that keeps the totals honest without asserting where anybody was.

3. PRESENCE IS THE TEST FOR "KNOWN", AND T-1386 IS WHERE PRESENCE IS READ.
   The first cut of this rule counted only a record whose own `present_on_scene_date`
   said `present`, and left the 820 `uncertain` ones to T-1172's re-admission as
   roster class R1: counting a household as known AND offering it on the roster
   would order one person twice.  T-1386 RE-ADMITTED THEM (2026-09-19).  827 people
   are ruled into the town on the owner's standing rule — an attested or inferred
   resident is in the population unless there is EVIDENCE they were not — and they
   stand in the layer today, which is why the landing card counts 2,267 people and
   this book counted 457.  So the double-count the rule was written to stop has
   INVERTED: leaving them out of `known` does not decline to order them twice, it
   orders a replacement for 826 people already standing (T-1463).
       The rule is therefore read against the rulings file as well as the index: a
   household is known when the index records it `present`, or when T-1386 rules it
   present.  The two `evidenced_absences` stay out, because evidence of absence is
   exactly what the rule asks for; and the roster stays a LICENCE rather than a
   quota (rule `real_names_first`), so counting these once orders nobody twice.
       THIS APPLIES A RULING RATHER THAN MAKING ONE.  A run that finds a new
   modelling decision required here is to stop and say so, not to invent it.

4. THE FORT IS NOT APPORTIONED.  The garrison of 1 July 1835 is a return to be
   read (T-1176), not a share of a town model, so the fort division's person and
   household targets are `null` and its bucket says which ticket bounds them.
   Whatever T-1176 returns is subtracted from the civilian quota at the next
   `--build`, which is why that ticket is named in the bucket rather than guessed at.

THE COUNTERS ARE CARRIED, NOT RE-DERIVED.  `filled` and the `fills` ledger are
written by the reconstruction tools, not by this one, so `--check` re-derives
every bucket from the inputs, carries the committed counters across unchanged,
and then REFUSES an overfilled bucket or a fill naming no ticket. That is what
makes the book a quota rather than a report: a filler that bypasses it is red.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "data" / "reconstruction" / "1835_reconstruction_order_book.json"
REPORT = ROOT / "docs" / "RESEARCH" / "1835_reconstruction_order_book.md"

MODEL = ROOT / "data" / "reconstruction" / "1835_town_model.json"
PROFILE = ROOT / "data" / "reconstruction" / "1835_population_profile.json"
ROSTER = ROOT / "data" / "reconstruction" / "1835_borderline_roster.json"
PROGRAMME = ROOT / "data" / "reconstruction" / "1835_665_roof_programme.json"
INVENTORY = ROOT / "data" / "reconstruction" / "1835_building_inventory.json"
CROSSWALK = ROOT / "data" / "research" / "books" / "trade_census_1835_crosswalk.json"
COMPOSITION = ROOT / "data" / "research" / "census_1840" / "composition_1840.json"
RESIDENTS = ROOT / "data" / "residents" / "index.json"
REGISTER = ROOT / "data" / "research" / "newspapers" / "register_1835.json"

SCENE_DATE = "1835-07-01"

# The divisions the town model and the building programme both speak in. `fort`
# is carried but never apportioned — see rule 4 in the docstring.
CIVIL_DIVISIONS = ("south", "west", "north")
DIVISIONS = CIVIL_DIVISIONS + ("fort",)

# The age bands the book orders in. The 1840 schedule prints thirteen bands a sex
# and the extract uses ten; these six are those ten folded at the edges the
# reconstruction tickets actually act on — a child, a youth, and four adult
# decades, the last open. `low` is inclusive, `high` exclusive, `None` open.
AGE_BANDS = (
    ("under_10", 0, 10, "a child: the age pyramid's floor and the schedule's first two columns"),
    ("10_19", 10, 20, "a youth: at school, apprenticed, or at work in the household"),
    ("20_29", 20, 30, "the port's largest cohort by a wide margin"),
    ("30_39", 30, 40, "the second cohort: most heads of household sit here"),
    ("40_49", 40, 50, "established heads"),
    ("50_plus", 50, None, "the oldest cohort the schedule counts in any number"),
)
ADULT_FROM = 20

# The resident layer's own age labels, folded onto the book's bands. The layer cuts
# finer than the book at the bottom (0-4, 5-9, 10-14, 15-19) and coarser at the top
# (50+), so the fold is written here rather than guessed at a call site: a label this
# table does not hold is a Fault, never a silent drop.
LAYER_AGE_BANDS = {
    "0-4": "under_10", "5-9": "under_10", "0-9": "under_10",
    "10-14": "10_19", "15-19": "10_19", "10-19": "10_19",
    "20-29": "20_29", "30-39": "30_39", "40-49": "40_49",
    "50-59": "50_plus", "50+": "50_plus", "60-69": "50_plus",
    "70-79": "50_plus", "80-89": "50_plus", "80+": "50_plus",
}

# The household types a person can be seated in. `transient` is the summer of
# 1835's own cohort and the model does not bound it: T-1178 does.
HOUSEHOLD_TYPES = (
    ("family", "a household of kin — a head, a spouse where there was one, children, servants and apprentices"),
    ("lodging", "a bed in a boarding house, an inn, a hotel, aboard a vessel or over a shop"),
    ("garrison", "the fort establishment: the companies, the staff and the soldiers' families"),
    ("transient", "in the town on 1 July 1835 and not of it: the land-sale crowd, the immigrants waiting for lots, the works gang"),
)

# Which ticket fills a person bucket. Read top-down; the first rule that matches
# owns the cell. Written here rather than in prose so the book can be audited
# against the queue.
PERSON_TICKET_RULES = (
    ("fort division", lambda a: a["division"] == "fort", "T-1176"),
    ("the transient cohort", lambda a: a["household_type"] == "transient", "T-1178"),
    # T-1500 repointed this off its split parent on 2026-09-21 (T-1420), the same
    # sweep and the same reason as T-1347's two lines below. T-1175 — fill the beds —
    # split into T-1370 (the lodging model), T-1371 (seat the boarders) and T-1372,
    # and every piece of that tree that fills a bed has since closed; its one live
    # descendant, T-1407, is the crews and the harbour-works gang and nothing else.
    # So the 278 persons these 59 buckets still order were ordered by nobody, which
    # is the hole `every_work_order_names_a_live_ticket` refuses. T-1500 carries the
    # remainder to the queue as a row the owner can rank. Who fills WHICH bed is a
    # modelling decision and is not taken here.
    ("a bed rather than a household", lambda a: a["household_type"] == "lodging", "T-1500"),
    # T-1347 repointed this off its split parent. T-1173 was the epic; it split into
    # T-1346 (read the 1839 trade table) and T-1347 (draw the heads), and a bucket whose
    # owning ticket is a SPLIT parent names nobody who can act on it (T-1237).
    ("an adult at a trade", lambda a: a["trade"] == "trade", "T-1347"),
    ("a woman or a person under twenty", lambda a: a["sex"] == "female" or a["age_band"] in ("under_10", "10_19"), "T-1174"),
    ("otherwise: a family drawn from the household model", lambda a: True, "T-1171"),
)

# The roster's classes, and the ticket each class is offered to. A roster class is
# a LICENCE to use a real read name; it is not a quota, and it is reported against
# its ticket rather than smeared across cells that cannot hold it.
ROSTER_TICKETS = {
    "R1_in_window_uncertain": "T-1172",
    "R2_in_window_single_source": "T-1172",
    "R3_1834_return_or_muster": "T-1172",
    "R4_surname_only_census": "T-1170",
    "R5_later_only_backprojectable": "T-1172",
    "R6_native_metis_black": "T-1177",
}

# Household types against the roof groups that hold them, and the ticket that
# reconstructs the household (not the roof — that is the structure band).
HOUSEHOLD_BUCKETS = (
    ("family_dwelling", "ordinary_dwellings", "T-1171"),
    ("store_residence", "stores_mixed_use", "T-1171"),
    # Swept with the person rule above (T-1420 -> T-1500). Both of these rows are
    # discharged — every boarding house and inn the model wants is standing — so the
    # gate does not reach them; they move only so that one household type does not
    # answer to two different tickets depending on which family you read.
    ("boarding_house", "larger_boarding_houses", "T-1500"),
    ("inn_tavern", "inns_taverns", "T-1500"),
    # T-1188 split (T-1410, T-1411); the institutional HOUSEHOLDS are the people who
    # lived at a church, a parsonage or a school. T-1410's three establishments — post
    # office, land office, county rooms — house nobody. T-1411 split in turn (T-1421,
    # T-1422) and both children closed WITHOUT writing a household: they wrote
    # establishments and the hands about them, which is a different thing from the people
    # who slept there. So this bucket is undone work that lost its owner, and it goes to
    # T-1189 — every working person a workplace and every workplace its people — which is
    # the live ticket that puts real persons at these establishments (T-1422).
    ("institutional", "institutional_public", "T-1189"),
    ("garrison", "fort_principal", "T-1176"),
)

# Which build ticket owns a structure group in a division. The queue's 5C band is
# cut by district and street, so this maps the programme's own group x district
# matrix onto the ten build tickets.
STRUCTURE_TICKETS = {
    ("south", "ordinary_dwellings"): "T-1203",
    ("south", "stores_mixed_use"): "T-1201",
    ("south", "larger_boarding_houses"): "T-1209",
    ("south", "inns_taverns"): "T-1201",
    ("south", "workshops"): "T-1201",
    ("south", "warehouses_freight"): "T-1200",
    ("south", "institutional_public"): "T-1202",
    ("south", "barns_stables"): "T-1212",
    ("south", "small_outbuildings"): "T-1212",
    ("west", "ordinary_dwellings"): "T-1208",
    ("west", "stores_mixed_use"): "T-1207",
    ("west", "larger_boarding_houses"): "T-1209",
    ("west", "inns_taverns"): "T-1207",
    ("west", "workshops"): "T-1207",
    ("west", "warehouses_freight"): "T-1207",
    ("west", "institutional_public"): "T-1208",
    ("west", "barns_stables"): "T-1212",
    ("west", "small_outbuildings"): "T-1212",
    ("north", "ordinary_dwellings"): "T-1206",
    ("north", "stores_mixed_use"): "T-1205",
    ("north", "larger_boarding_houses"): "T-1209",
    ("north", "inns_taverns"): "T-1205",
    ("north", "workshops"): "T-1205",
    ("north", "warehouses_freight"): "T-1205",
    ("north", "institutional_public"): "T-1205",
    ("north", "barns_stables"): "T-1212",
    ("north", "small_outbuildings"): "T-1212",
    ("fort", "fort_principal"): "T-1204",
    ("fort", "stores_mixed_use"): "T-1204",
    ("fort", "workshops"): "T-1204",
    ("fort", "barns_stables"): "T-1204",
    ("fort", "small_outbuildings"): "T-1204",
}

# Which business ticket owns a December 1835 trade-census class.
#
# T-1188 WAS SPLIT (T-1410, T-1411) and the three classes it owned went with the half
# that owns them: the printing offices, the churches and the schools are T-1411's. The
# other half, T-1410, owns the post office, the land office and the county's own rooms —
# which the State census never enumerates, so it takes no class here at all and the book
# orders nothing for it. A bucket whose `owning_ticket` names a ticket in state `split`
# points at work nobody can claim, which is why this table moves with a split.
BUSINESS_TICKETS = {
    "store": "T-1184",
    "book_store": "T-1184",
    "druggist": "T-1184",
    "silversmith_jeweller": "T-1185",
    "tin_and_copper_manufactory": "T-1185",
    # FINISHED CLASSES, HANDED ON RATHER THAN LEFT POINTING AT A SPENT TICKET (T-1422).
    # T-1411 and both its children are closed and neither row orders anything: the press
    # reads 2 against the census's 2 once the Democrat's two notices are ruled one house,
    # and the churches are `compared: false` by T-0988's ruling. What was left for both was
    # that the finished count PRINTS, which was T-1190's own sentence.
    #
    # AND T-1442 PRINTED IT (docs/RESEARCH/business-layer-final-2026-09.md, 2026-09-20),
    # which spends T-1190: its three pieces all closed, so the parent is finished work and
    # a row pointing at it points at a ticket nobody can claim. These three rows have no
    # work left of their own — each orders nought, and the church row orders nought BECAUSE
    # the crosswalk declines to compare it. They are handed to T-1215, the closing
    # convergence, because the last thing any business row is still owed is to be reconciled
    # in the completion report that ticket opens; nothing smaller is left to own them.
    "printing_office": "T-1215",
    "brewery": "T-1185",
    "steam_saw_mill": "T-1187",
    "iron_foundry": "T-1185",
    "storage_and_forwarding": "T-1187",
    "tavern": "T-1187",
    "lottery_office": "T-1182",
    "bank": "T-1182",
    # BOTH PARENTS SPLIT ON 2026-09-20 and each row follows its own heir.
    # T-1188 split, so the civic rows move to T-1411, the churches, schools and press
    # as establishments — this branch's own reassignment.
    "church": "T-1215",
    # THE SCHOOLS ARE READ AT THE SCENE DATE NOW (T-1428, 2026-09-20). The crosswalk used
    # to count seven at 1 July because it read the gazetteer's `built_at_scene_date`; the
    # register says two of those seven had not opened, so it holds five, and the two the
    # census counted in the autumn are named and dated as opening in August. Both halves
    # moved together — the crosswalk reads `present_at_scene_date` and the book holds an
    # explained shortfall apart from a quota — so this row orders nothing and says why.
    # What was left for it was the same as the churches': the finished count PRINTS, and
    # T-1442 printed it, so this row follows the two above to T-1215.
    "school": "T-1215",
    # T-1186 was split on 2026-09-20 when the unit ruling below turned out to be a
    # demonstration of its own; T-1418 is the piece that owns these two rows and T-1419
    # the services, which the census enumerates nowhere and which therefore own no bucket.
    "lawyer": "T-1418",
    "physician": "T-1418",
    "lyceum_and_reading_room": "T-1182",
    "other": "T-1182",
    "not_stated": "T-1182",
}

# The ground each division waits on before its structure buckets can be built.
#
# SWEPT TO LIVE OWNERS ON 2026-09-21 (T-1420). Every id here was a closed or split
# ticket, which is the T-1237 failure this file already carries twice above: a bucket
# whose owning ticket is a split parent names nobody who can act on it. `ticket.mjs
# done` prints the warning at the moment the last child closes and says in as many
# words that it "fails the re-derivation, in a tool this PR does not run" — so the
# re-derivation now runs it: `every_work_order_names_a_live_ticket` below refuses a
# dead work order on every --build and --check, and this table cannot silt again.
#
# What the sweep found, read off the ticket tree rather than asserted:
#   T-1191  done 2026-09-20 — the North Division's platted corridors ARRIVED.
#   T-1194  split, and all three children (T-1436, T-1437, T-1438) have closed
#           through their own grandchildren: the lot grid north and west of the
#           river ARRIVED. Ground that has arrived is not a wait.
#   T-1192  split; its live piece is T-1414, the West Division's and Wabansia's
#           corridors and small lots. That is the successor T-1420 was filed for.
#   T-1193  split; its live frontier is T-1444 (via T-1417 and T-1431), and all
#           three of those say West Division in their own titles. The north half of
#           T-1193 — the field regenerated to N +760 so the North Division's second
#           parcel has ground — closed with T-1416.
#
# SOUTH AND NORTH ARE EMPTY, AND THAT IS NOT A CLAIM THAT THEIR GROUND IS WHOLE. It
# is the narrower statement this table can make: no LIVE ticket owns what they still
# wait on. The programme's own `waiting_on` prose on each gated row is where the gap
# is recorded and is unchanged by this sweep — the south's last tier waits on the S9
# street control ROADMAP has recorded as owed, and the Michigan Street tract's four
# north rows wait on T-1080, the tract's own unsettled name and platter. Filing an
# owner for either would be inventing one; naming a closed ticket was worse.
GROUND_TICKETS = {
    "south": [],
    "west": ["T-1414", "T-1444"],
    "north": [],
    "fort": [],
}


class Fault(Exception):
    """A refusal. Never a warning: an order book with a hole in it is not a quota."""


# ---------------------------------------------------------------- arithmetic --

def point_of(fig: dict) -> tuple[int, str]:
    """The quota a figure hands the book, and the sentence that says how."""
    low, high, pt = fig.get("low"), fig.get("high"), fig.get("point")
    if low is None or high is None:
        raise Fault(f"the figure {fig.get('figure')!r} carries no range at all")
    if high < low:
        raise Fault(f"the figure {fig.get('figure')!r} is inverted: {low}..{high}")
    if pt is not None:
        return int(round(pt)), f"the model's own point within {low:,}-{high:,}"
    mid = int((low + high) / 2 + 0.5)
    return mid, f"the midpoint of the model's {low:,}-{high:,}, rounded half up"


def largest_remainder(total: int, weights: dict[str, float]) -> dict[str, int]:
    """Apportion `total` across `weights` so the parts sum to it exactly.

    Deterministic by construction: the remainder order breaks ties on the key,
    so two builds on the same inputs are byte-identical.
    """
    if total < 0:
        raise Fault(f"an apportionment of a negative total: {total}")
    mass = sum(weights.values())
    if mass <= 0:
        raise Fault("an apportionment across weights that sum to zero")
    exact = {k: total * (w / mass) for k, w in weights.items()}
    out = {k: int(v) for k, v in exact.items()}
    short = total - sum(out.values())
    order = sorted(weights, key=lambda k: (-(exact[k] - out[k]), k))
    for k in order[:short]:
        out[k] += 1
    if sum(out.values()) != total:
        raise Fault(f"an apportionment that does not close: {sum(out.values())} of {total}")
    return out


def subtract_pro_rata(targets: dict[str, int], unresolved: int) -> dict[str, int]:
    """Spread `unresolved` known people across cells in proportion to their target.

    Rule 2 of the docstring. A person the layer cannot place is still standing in
    the town; the book must not order a replacement for them.
    """
    if unresolved <= 0:
        return {k: 0 for k in targets}
    live = {k: v for k, v in targets.items() if v > 0}
    if not live:
        raise Fault("the unresolved known have nowhere to go: every target is zero")
    return {**{k: 0 for k in targets}, **largest_remainder(min(unresolved, sum(live.values())), live)}


# --------------------------------------------------------------------- inputs --

def load(root: Path = ROOT) -> dict:
    paths = {
        "model": root / "data" / "reconstruction" / "1835_town_model.json",
        "profile": root / "data" / "reconstruction" / "1835_population_profile.json",
        "roster": root / "data" / "reconstruction" / "1835_borderline_roster.json",
        "programme": root / "data" / "reconstruction" / "1835_665_roof_programme.json",
        "inventory": root / "data" / "reconstruction" / "1835_building_inventory.json",
        "crosswalk": root / "data" / "research" / "books" / "trade_census_1835_crosswalk.json",
        "trade_spend": root / "data" / "research" / "books" / "trade_census_1835_spend.json",
        "composition": root / "data" / "research" / "census_1840" / "composition_1840.json",
        "residents": root / "data" / "residents" / "index.json",
        "register": root / "data" / "research" / "newspapers" / "register_1835.json",
        "presence_rulings": root / "data" / "reconstruction" / "1835_presence_rulings.json",
    }
    out = {}
    for key, path in paths.items():
        if not path.exists():
            raise Fault(f"the order book's input {path.name} is missing — it cannot be built without it")
        out[key] = json.loads(path.read_text(encoding="utf-8"))
    return out


def figure(model: dict, section_key: str, name: str) -> dict:
    for s in model.get("sections", []):
        if s.get("key") != section_key:
            continue
        for f in s.get("figures", []):
            if f.get("figure") == name:
                return f
    raise Fault(f"the town model carries no figure {section_key}.{name}")


# ------------------------------------------------------------ the shape of it --

def sex_shares(model: dict) -> dict[str, float]:
    """Male / female shares from the model's sex ratio, which is the 1840 adult one."""
    ratio = figure(model, "population", "males_per_100_females")
    pt, _ = ratio.get("point"), None
    if pt is None:
        raise Fault("the sex ratio carries no point and the book cannot halve a ratio")
    male = float(pt) / (100.0 + float(pt))
    return {"male": male, "female": 1.0 - male}


def age_shares(composition: dict) -> dict[str, dict[str, float]]:
    """The 1840 free-white pyramid, folded to the book's bands, WITHIN each sex.

    Within-sex rather than overall, because the sex split is the model's (1835's
    adult ratio) and the 1840 overall ratio is a different town four years on.
    """
    rows = composition.get("age_bands", {}).get("free_white", [])
    if not rows:
        raise Fault("the 1840 composition carries no free-white age bands")
    out: dict[str, dict[str, float]] = {"male": {}, "female": {}}
    totals = {"male": 0, "female": 0}
    for sex in ("male", "female"):
        counts = {name: 0 for name, _, _, _ in AGE_BANDS}
        for row in rows:
            if row.get("sex") != sex:
                continue
            edge = int(row["low_edge"])
            for name, low, high, _ in AGE_BANDS:
                if edge >= low and (high is None or edge < high):
                    counts[name] += int(row["persons"])
                    break
            else:
                raise Fault(f"the 1840 band at age {edge} falls in none of the book's bands")
        total = sum(counts.values())
        if total <= 0:
            raise Fault(f"the 1840 pyramid counts no {sex}s at all")
        totals[sex] = total
        out[sex] = {k: v / total for k, v in counts.items()}
    return out


def _flat(value):
    """A layer attribute is either the bare value or a {value, confidence, ...} block."""
    if isinstance(value, dict):
        return value.get("value")
    return value


def trade_participation(model: dict, composition: dict, root: Path = ROOT) -> dict:
    """WHO THIS TOWN'S OWN SOURCES RECORD AT WORK — read, not assumed (T-1459).

    The book's first cut drew its employed persons out of the ADULT cells alone, on
    the reading that an occupation is an adult's. That is an assumption, and the 1840
    schedule cannot settle it: its seven industry columns count `persons in each
    family employed`, carry no sex and no age at all (composition_1840.json
    `industry.note`), and the extract holds them only as household totals. So the age
    floor of the trade cut has to come from somewhere, and the honest somewhere is
    the town's own record.

    This reads it: every person in the resident layer whose OCCUPATION is `attested`
    or `inferred` — read from a source rather than drawn by a reconstruction stage —
    counted by the book's own bands. A person the layer grades `reconstructed` is
    skipped by name: they exist only because a stage drew them against this book, and
    a cut calibrated on its own output is not a reading.

    It returns a participation FACTOR per band: the band's workers per unit of the
    1840 pyramid's population in that band, against the same rate among adults. Both
    halves come from the same instrument, so the survivorship that inflates a record
    of trades — the sources that print an occupation print proprietors and heads of
    household — inflates numerator and denominator alike and cancels to first order.
    That cancellation is the argument, and it is why the factor is a RELATIVE rate
    rather than the record's own 94.5% male, which is survivorship and nothing else.

    A band the record does not reach gets 0.0 and orders nobody. The floor is
    therefore measured on every build: if a later reading finds a working child, the
    band opens by itself; if the nine youths here were withdrawn, it shuts.
    """
    households = root / "data" / "residents" / "households"
    if not households.is_dir():
        raise Fault("the resident layer's households/ is missing — the trade cut cannot be read")
    workers: Counter = Counter()
    by_sex: Counter = Counter()
    labels: Counter = Counter()
    skipped_reconstructed = 0
    for path in sorted(households.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        for person in record.get("persons", []):
            occupation = person.get("occupation") or {}
            if occupation.get("confidence") not in ("attested", "inferred"):
                continue
            value = occupation.get("value")
            if not value or value == "none_recorded":
                continue
            if person.get("grade") == "reconstructed":
                skipped_reconstructed += 1
                continue
            label = _flat(person.get("age_band"))
            if label not in LAYER_AGE_BANDS:
                raise Fault(f"the resident layer ages {person.get('id')} in a band the book "
                            f"cannot fold: {label!r}")
            band = LAYER_AGE_BANDS[label]
            workers[band] += 1
            labels[label] += 1
            by_sex[_flat(person.get("sex")) or "unrecorded"] += 1

    sexes = sex_shares(model)
    ages = age_shares(composition)
    shares = {band: sum(sexes[sex] * ages[sex][band] for sex in sexes)
              for band, _, _, _ in AGE_BANDS}
    adult_bands = [band for band, low, _, _ in AGE_BANDS if low >= ADULT_FROM]
    adult_workers = sum(workers[b] for b in adult_bands)
    adult_share = sum(shares[b] for b in adult_bands)
    if adult_workers <= 0 or adult_share <= 0:
        raise Fault("the resident layer records no adult at a trade, so the book has no rate "
                    "to cut the younger bands against")
    adult_rate = adult_workers / adult_share

    factors = {}
    for band, low, _, _ in AGE_BANDS:
        if low >= ADULT_FROM:
            factors[band] = 1.0
        elif workers[band] and shares[band] > 0:
            factors[band] = min(1.0, (workers[band] / shares[band]) / adult_rate)
        else:
            factors[band] = 0.0

    reached = [band for band, low, _, _ in AGE_BANDS if low < ADULT_FROM and factors[band] > 0]
    return {
        "read_from": "data/residents/households/*.json — every person whose occupation is "
                     "attested or inferred, which is to say read from a source",
        "workers": dict(sorted(workers.items())),
        "workers_total": sum(workers.values()),
        "workers_by_sex": dict(sorted(by_sex.items())),
        "layer_labels": dict(sorted(labels.items())),
        "reconstructed_skipped": skipped_reconstructed,
        "pyramid_shares": {k: round(v, 6) for k, v in sorted(shares.items())},
        "adult_workers": adult_workers,
        "factors": {k: round(v, 6) for k, v in sorted(factors.items())},
        "bands_reopened": reached,
        "the_age_argument": (
            f"{sum(workers.values())} people in the resident layer carry an occupation a source "
            f"records. {workers['10_19']} of them are in the book's 10_19 band — and every one of "
            f"those is labelled 15-19 by the layer, so the record reaches below twenty and stops "
            f"at fifteen. Per unit of the 1840 pyramid's population that is "
            f"{factors['10_19']:.4f} of the adult rate, which is the weight the band enters the "
            f"cut at. The band under ten has no worker in the record at all and is left shut."),
        "the_sex_argument_is_refused": (
            f"{by_sex.get('male', 0)} of the {sum(by_sex.values())} are men. That is not a licence "
            f"to cut the trade remainder male: the sources that print an occupation — notices, "
            f"poll lists, the trade census, the directories — print PROPRIETORS and heads of "
            f"household, and a record of who advertised is not a record of who worked. The town "
            f"model's own occupations section says the same thing from the other side: the 1840 "
            f"schedule's seven columns have no row for domestic service, 'which a port with this "
            f"adult sex ratio certainly had', and the trade split understates household labour "
            f"'by an amount this model cannot bound'. Both arguments point one way and neither "
            f"bounds a number, so the SEX of the trade remainder is NOT re-cut. The book keeps "
            f"the population's own split, and the hands a shop wants that only a man can fill "
            f"stand short with the reason said out loud."),
    }


def division_shares(inventory: dict) -> dict[str, float]:
    """Where the civilian town was, taken from the roof programme's own district targets."""
    districts = inventory.get("districts", {})
    weights = {}
    for d in CIVIL_DIVISIONS:
        target = districts.get(d, {}).get("target")
        if not target:
            raise Fault(f"the building inventory sets no roof target for the {d} division")
        weights[d] = float(target)
    mass = sum(weights.values())
    return {k: v / mass for k, v in weights.items()}


def ruled_present(rulings: dict | None) -> dict:
    """The households T-1386 ruled into the town of 1 July 1835, keyed by id.

    `evidenced_absences` are deliberately NOT among the rulings — that stage leaves
    them out because a dated departure or a dated appearance elsewhere is the one
    thing that keeps a resident out of the count, and this book inherits that.
    """
    if rulings is None:
        return {}
    rows = rulings.get("rulings")
    if not rows:
        raise Fault("the presence rulings carry no rulings: T-1386's file is empty")
    out = {}
    for row in rows:
        hid = row.get("household_id")
        if not hid:
            raise Fault("a presence ruling names no household")
        if ((row.get("present_on_scene_date") or {}).get("value")) == "present":
            out[hid] = row
    return out


def known_layer(residents: dict, rulings: dict | None = None) -> dict:
    """The known people and households, read off the committed resident index AND
    off T-1386's presence rulings.

    Rule 3: a household is known when the index records it `present` on the scene
    date, OR when T-1386 rules it present. Until T-1463 only the first clause
    existed and the 820 `uncertain` households — 827 people who stand in the layer
    today — were counted unknown, so every bucket ordered their replacement.

    Called with `rulings=None` this returns the PRE-RULING cut. Nothing ships off
    that number: `build` uses it only to tell a quota the re-cut shrinks under work
    already drawn (refused by name) from a filler that overfilled its own quota
    (a fault), which are two different reds and must not be read as one.

    AND A RECONSTRUCTED PERSON IS NOT KNOWN. `known` is what the SOURCES give the town;
    a reconstructed person is the order being filled, and `filled` is their counter.
    Counting them here as well would retire their own quota a second time — a bucket
    that drew its last person would read `filled: n` against `to_reconstruct: 0` and the
    overfill gate would fire on a stage that obeyed it exactly. T-1171 was the first
    stage to write a person and the first to meet this; it read zero before that.
    """
    households = residents.get("households", [])
    if not households:
        raise Fault("the resident index carries no households")
    ruled = ruled_present(rulings)
    out = {
        "households_total": len(households),
        "households_present": 0,
        "households_uncertain": 0,
        "households_ruled_present": 0,
        "households_evidenced_absent": 0,
        "households_reconstructed": 0,
        "persons_total": 0,
        "persons_standing": 0,
        "persons_ruled_present": 0,
        "persons_present": 0,
        "persons_present_attested": 0,
        "persons_present_inferred": 0,
        "persons_present_by_division": {d: 0 for d in DIVISIONS},
        "households_present_by_division": {d: 0 for d in DIVISIONS},
        "persons_present_unplaced": 0,
        "households_present_unplaced": 0,
        "households_with_a_lives_at": 0,
        "households_with_a_works_at": 0,
    }
    for hh in households:
        persons = int(hh.get("persons") or 0)
        out["persons_total"] += persons
        presence = hh.get("present_on_scene_date")
        from_a_ruling = presence == "uncertain" and hh.get("id") in ruled
        if presence == "uncertain":
            out["households_uncertain"] += 1
            if not from_a_ruling:
                continue
        elif presence != "present":
            out["households_evidenced_absent"] += 1
            continue
        # EVERY PERSON PAST THIS LINE IS STANDING IN THE TOWN, named or drawn. It is the
        # figure the landing card prints and the one the remainder is measured against
        # (T-1463): `persons_standing + still owed` is what the town converges to, and a
        # book whose sum overshoots the model is ordering somebody who already exists.
        out["persons_standing"] += persons
        grades = hh.get("grades") or {}
        named = persons - int(grades.get("reconstructed") or 0)
        # AND A RECONSTRUCTED HOUSEHOLD IS NOT KNOWN EITHER (T-1174). The paragraph above
        # says why for a person; a household nobody is named in is the same thing one level
        # up. `women_and_children` is the first stage to write a household rather than to
        # draw into one, and while these counted as known its own quota fell by one for
        # every house it made — so the second build of the same stage derived 65 houses
        # where the first derived 124, and `--check` could never have held it. A wholly
        # reconstructed house is the order being filled; `filled` is its counter.
        if persons and named == 0:
            out["households_reconstructed"] += 1
            continue
        out["households_present"] += 1
        if from_a_ruling:
            out["households_ruled_present"] += 1
            out["persons_ruled_present"] += named
        out["persons_present"] += named
        out["persons_present_attested"] += int(grades.get("attested") or 0)
        out["persons_present_inferred"] += int(grades.get("inferred") or 0)
        division = hh.get("division")
        if division in out["persons_present_by_division"]:
            out["persons_present_by_division"][division] += named
            out["households_present_by_division"][division] += 1
        else:
            out["persons_present_unplaced"] += named
            out["households_present_unplaced"] += 1
        if hh.get("lives_at"):
            out["households_with_a_lives_at"] += 1
        if hh.get("works_at"):
            out["households_with_a_works_at"] += 1
    return out


# -------------------------------------------------------------------- buckets --

def person_buckets(model: dict, composition: dict, inventory: dict, known: dict,
                   participation: dict | None = None) -> dict:
    pop_fig = figure(model, "population", "population_on_1_july_1835")
    town, town_basis = point_of(pop_fig)
    lodging_fig = figure(model, "lodging_and_institutions", "share_of_the_town_in_lodging")
    lodging_low, lodging_high = float(lodging_fig["low"]), float(lodging_fig["high"])
    lodging_share = (lodging_low + lodging_high) / 2.0
    employed_fig = figure(model, "occupations", "employed_persons")
    employed, employed_basis = point_of(employed_fig)

    sexes = sex_shares(model)
    ages = age_shares(composition)
    divisions = division_shares(inventory)

    # The civilian town, apportioned. Targets first, on the model's own marginals:
    # sex x age within sex x division x household type. The fort is not in here
    # (rule 4) and neither is the transient cohort (T-1178 bounds it).
    weights: dict[str, float] = {}
    axes: dict[str, dict] = {}
    for sex, sex_share in sexes.items():
        for band, _, _, _ in AGE_BANDS:
            for division, div_share in divisions.items():
                for htype in ("family", "lodging"):
                    share = sex_share * ages[sex][band] * div_share
                    share *= lodging_share if htype == "lodging" else (1.0 - lodging_share)
                    key = f"{sex}/{band}/{division}/{htype}"
                    weights[key] = share
                    axes[key] = {"sex": sex, "age_band": band, "division": division,
                                 "household_type": htype, "trade": "none"}
    targets = largest_remainder(town, weights)

    # Then the employed, drawn out of the adult cells only. A trade is a column of
    # the 1840 schedule that counts persons in families and cannot be split by sex,
    # so the book splits it by nothing but the population already in each cell.
    adult = {k: targets[k] for k in targets
             if next(b for b in AGE_BANDS if b[0] == axes[k]["age_band"])[1] >= ADULT_FROM}
    if sum(adult.values()) < employed:
        raise Fault(f"the model wants {employed:,} employed persons and the town model's own "
                    f"adults number {sum(adult.values()):,}")
    employed_by_cell = largest_remainder(employed, {k: float(v) for k, v in adult.items() if v > 0})

    # THE RE-CUT'S WANT (T-1459), computed beside the standing cut rather than in place of
    # it. `employed_by_cell` above is what the book ordered before the owner's ruling of
    # 2026-09-20 and is the baseline every refusal is measured from; this is the same draw
    # with the younger bands entering at the participation the town's own record measures
    # (`trade_participation`). Nothing here moves a bucket — `build` does that, and only
    # across each bucket's UNFILLED remainder, because the ruling protects what is drawn.
    recut_by_cell: dict[str, int] = {}
    if participation:
        factors = participation["factors"]
        eligible = {k: float(targets[k]) * factors[axes[k]["age_band"]] for k in targets}
        eligible = {k: v for k, v in eligible.items() if v > 0}
        if sum(targets[k] for k in eligible) < employed:
            raise Fault(f"the model wants {employed:,} employed persons and the bands the record "
                        f"reaches hold {sum(targets[k] for k in eligible):,}")
        recut_by_cell = largest_remainder(employed, eligible)

    # The known, subtracted. What the layer resolves onto a division is subtracted
    # there; what it cannot is spread pro rata (rule 2).
    resolved = {d: known["persons_present_by_division"][d] for d in CIVIL_DIVISIONS}
    unresolved = known["persons_present_unplaced"]
    known_by_cell = {k: 0 for k in targets}
    for division in CIVIL_DIVISIONS:
        cells = {k: float(targets[k]) for k in targets if axes[k]["division"] == division}
        for k, v in subtract_pro_rata({k: targets[k] for k in cells}, resolved[division]).items():
            known_by_cell[k] += v
    for k, v in subtract_pro_rata(targets, unresolved).items():
        known_by_cell[k] += v

    attested_share = (known["persons_present_attested"] / known["persons_present"]) if known["persons_present"] else 0.0
    buckets = []
    for key in sorted(targets):
        a = axes[key]
        cell_employed = employed_by_cell.get(key, 0)
        wants = recut_by_cell.get(key, 0)
        for trade in ("trade", "none"):
            target = cell_employed if trade == "trade" else targets[key] - cell_employed
            if target <= 0 and wants <= 0 and trade == "trade":
                continue
            share_of_cell = (target / targets[key]) if targets[key] else 0.0
            k_total = int(round(known_by_cell[key] * share_of_cell))
            k_att = int(round(k_total * attested_share))
            axes_out = {**a, "trade": trade}
            owner, why = person_owner(axes_out)
            buckets.append({
                "key": f"persons/{key}/{trade}",
                "axes": axes_out,
                "target": target,
                "known_attested": k_att,
                "known_inferred": k_total - k_att,
                "to_reconstruct": max(0, target - k_total),
                "filled": 0,
                "owning_ticket": owner,
                "basis": why,
            })
            if trade == "trade":
                buckets[-1]["recut_wants"] = wants
                if target <= 0:
                    # A CELL THE FIRST CUT SHUT. It exists because T-1459's re-cut reached
                    # the band; it has no quota in the cut that came before it, so it is
                    # marked rather than left to look like a bucket that has always been here.
                    buckets[-1]["reopened_by_the_re_cut"] = True

    buckets.append({
        "key": "persons/garrison/fort",
        "axes": {"sex": "any", "age_band": "any", "division": "fort",
                 "household_type": "garrison", "trade": "any"},
        "target": None,
        "known_attested": known["persons_present_by_division"]["fort"],
        "known_inferred": 0,
        "to_reconstruct": None,
        "filled": 0,
        "owning_ticket": "T-1176",
        "basis": "NOT APPORTIONED. The garrison of 1 July 1835 is a return to be read — the "
                 "companies of the 5th Infantry to their strength, the staff and the soldiers' "
                 "families — and T-1176 bounds it from the sources. Whatever it returns is "
                 "subtracted from the civilian quota at the next --build.",
    })
    buckets.append({
        "key": "persons/transient/town",
        "axes": {"sex": "any", "age_band": "any", "division": "any",
                 "household_type": "transient", "trade": "any"},
        "target": None,
        "known_attested": 0,
        "known_inferred": 0,
        "to_reconstruct": None,
        "filled": 0,
        "owning_ticket": "T-1178",
        "basis": "NOT APPORTIONED. The town model bounds the town's RESIDENTS; the land-sale "
                 "crowd, the immigrants awaiting lots, the harbour gang and the crews ashore "
                 "are in the town on 1 July 1835 and not of it. T-1178 bounds the cohort and "
                 "says where it slept.",
    })

    return {
        "town_target": town,
        "town_target_basis": town_basis,
        "town_target_range": [pop_fig["low"], pop_fig["high"]],
        "employed_target": employed,
        "employed_basis": employed_basis,
        "lodging_share": round(lodging_share, 4),
        "lodging_share_range": [lodging_low, lodging_high],
        "buckets": buckets,
    }


#: THE STAGES WHOSE DRAW IS STABLE UNDER A QUOTA CHANGE, so the re-cut below may spend
#: what they have left undrawn. A stage earns a place here ONE WAY: by dealing against a
#: COMMITTED BASIS rather than against the book's live `to_reconstruct`, so re-cutting a
#: bucket it has drawn against cannot re-deal the people standing on it. T-1503 did that
#: for the lodging stage and proves it — `seat_lodgers_1835.py --self-test` re-cuts a
#: throwaway copy of this book and asserts that not one card moves.
#:
#: NOTHING GOES ON THIS LIST WITHOUT THAT DEMONSTRATION. A stage that reads the room live
#: re-deals its ENTIRE draw when one slot of it moves, and the cost is measured: the
#: re-cut of 2026-09-21 re-dealt 25 of 56 invented boarders and took six further gate
#: steps red with them, because other layers had adopted them by name.
REMAINDER_STABLE_STAGES = {
    "T-1371": "tools/seat_lodgers_1835.py — deals against the committed `quota_basis` in "
              "data/reconstruction/1835_lodgers_seated.json (T-1503)",
}


def _hand_out(total: int, wants: dict[str, int], caps: dict[str, int]) -> dict[str, int]:
    """Hand `total` out in proportion to `wants`, and never past a key's `caps`.

    A plain largest-remainder cannot do this: the moment one key is capped its surplus
    has to go back into the pot and be re-shared among the keys still open, or the sum
    handed out is short of the total. So this rounds, caps, and re-shares what capping
    freed until either the total is spent or every key is full.
    """
    out = {k: 0 for k in wants}
    live = {k: v for k, v in wants.items() if v > 0 and caps.get(k, 0) > 0}
    remaining = int(total)
    while remaining > 0 and live:
        moved = 0
        for key, share in largest_remainder(remaining, {k: float(v) for k, v in live.items()}).items():
            room = caps[key] - out[key]
            take = min(share, room)
            out[key] += take
            moved += take
            if out[key] >= caps[key]:
                live.pop(key, None)
        remaining -= moved
        if moved == 0:
            break
    return out


def recut_trade_remainder(buckets: list, participation: dict, drawn_by: dict) -> dict:
    """THE OWNER'S RULING OF 2026-09-20 APPLIED: only the unfilled remainder moves (T-1459).

    The re-cut wants trade slots in a band the first cut shut. It cannot simply take
    them: every slot it would move out of an adult cell, and every slot it would move
    into a younger one, may already have a person standing on it. So the move is
    bounded on BOTH sides by what is undrawn —

      * an adult trade bucket gives up at most `to_reconstruct - filled`;
      * a younger cell takes at most what its own NON-trade sibling has undrawn, because
        a child already drawn as a child is not re-drawn as a shop boy.

    — and the total moved is the smaller of the two sides, so the book's employed total
    is exactly preserved and no cell's population changes. Every cap that bound the
    re-cut is NAMED with both numbers. That is the whole of the ruling: the cut changes,
    and the 1,370 people standing in the book do not move.
    """
    pairs: dict[str, dict] = {}
    for bucket in buckets:
        if bucket["axes"].get("trade") not in ("trade", "none"):
            continue
        cell, kind = bucket["key"].rsplit("/", 1)
        pairs.setdefault(cell, {})[kind] = bucket

    unaudited: dict[str, list] = {}

    def undrawn(bucket):
        """What this bucket can give up or take: its remainder — unless the stage that drew
        there re-deals its whole draw when the quota moves, in which case nothing.

        THE ARITHMETIC OF THE RULING is that a bucket's remainder is
        `to_reconstruct - filled`, and a re-cut confined to that reaches nobody already
        drawn. A STAGE, though, need not be confined to it, and the one that was not cost
        the whole re-cut: `tools/seat_lodgers_1835.py` used to read a lodging bucket's
        WHOLE `to_reconstruct`, so moving one slot of a bucket it had drawn against
        re-derived its ENTIRE draw. Run on 2026-09-21, that re-cut moved 35 slots into the
        reopened 10_19 band, `seat_lodgers_1835.py --check` went red at once, and
        re-deriving it re-dealt 25 of its 56 invented boarders — the same count in the same
        13 houses, nobody retired — after which SIX further gate steps failed, because
        `rc_cavanagh_johanna`, a boarder the stage had invented, is adopted by name as the
        keeper of `rcb_cavanagh_boarding_house` in the business layer, seated by the
        employment join and answered for by the employment coverage pass.

        So the test is not "has anything been drawn here" — it is "is the stage that drew
        here STABLE UNDER A QUOTA CHANGE". T-1503 made the lodging stage stable, by
        committing the room its deal was dealt against and dealing against that; the list
        of stages that have earned the same is `REMAINDER_STABLE_STAGES`, and a bucket
        whose fills all come from that list gives up its remainder like any other. A
        bucket a stage NOT on the list has drawn against still gives up nothing, and the
        stage is named in `unaudited` so the refusal says whose draw it is protecting
        rather than that something, somewhere, was drawn.
        """
        remainder = max(0, (bucket.get("to_reconstruct") or 0) - (bucket.get("filled") or 0))
        if not bucket.get("filled"):
            return remainder
        drew = sorted(drawn_by.get(bucket["key"], ()))
        loose = [t for t in drew if t not in REMAINDER_STABLE_STAGES]
        if loose or not drew:
            unaudited[bucket["key"]] = loose or ["(a fill naming no ticket)"]
            return 0
        return remainder

    wants_gain, caps_gain, wants_lose, caps_lose = {}, {}, {}, {}
    for cell, pair in pairs.items():
        trade = pair.get("trade")
        if trade is None:
            continue
        delta = int(trade.get("recut_wants", trade["target"])) - int(trade["target"])
        if delta > 0:
            wants_gain[cell] = delta
            caps_gain[cell] = undrawn(pair["none"]) if "none" in pair else 0
        elif delta < 0:
            wants_lose[cell] = -delta
            caps_lose[cell] = undrawn(trade)

    # THE ROOM IS THE BAND'S, NOT THE CELL'S. A cell that cannot take its share of the
    # re-cut — because the people who would have filled it are already drawn — does not
    # forfeit the band's slots; they spill to the cells of the same move that still have a
    # remainder, which is the book's own rule for a quantity that cannot sit where it was
    # apportioned (rule 2). The cell that could not take its share is named in `refusals`
    # so the spill is visible rather than inferred, and the sum is still bounded by what
    # is undrawn on BOTH sides, which is the ruling.
    room_to_gain = sum(caps_gain.values())
    room_to_lose = sum(caps_lose.values())
    moved = min(sum(wants_gain.values()), room_to_gain, room_to_lose)

    gained = _hand_out(moved, wants_gain, caps_gain)
    lost = _hand_out(moved, wants_lose, caps_lose)

    refusals = []
    for cell, want in sorted(wants_gain.items()):
        got = gained.get(cell, 0)
        if got < want:
            sibling = pairs[cell].get("none")
            refusals.append({
                "cell": cell,
                "direction": "into",
                "owning_ticket": pairs[cell]["trade"].get("owning_ticket"),
                "the_re_cut_wanted": want,
                "the_remainder_could_pay": got,
                "already_drawn_in_the_way": (sibling or {}).get("filled", 0),
                "drawn_by": (sibling or {}).get("owning_ticket"),
                "the_unaudited_stages_that_drew_here":
                    unaudited.get((sibling or {}).get("key"), []),
                "why": "the re-cut would seat a working youth in a cell drawn against by a "
                       "stage that is NOT stable under a quota change: it reads the "
                       "bucket's whole `to_reconstruct`, so re-cutting one undrawn slot "
                       "re-deals its entire draw. The stages that HAVE been made stable "
                       "are in `REMAINDER_STABLE_STAGES` and their remainder is spent "
                       "freely (T-1503 put the lodging stage there). This cell's is not, "
                       "so it is refused by name rather than clamped in silence.",
            })
    for cell, want in sorted(wants_lose.items()):
        took = lost.get(cell, 0)
        if took < want and caps_lose.get(cell, 0) < want:
            refusals.append({
                "cell": cell,
                "direction": "out of",
                "owning_ticket": pairs[cell]["trade"].get("owning_ticket"),
                "the_re_cut_wanted": want,
                "the_remainder_could_pay": took,
                "already_drawn_in_the_way": pairs[cell]["trade"].get("filled", 0),
                "drawn_by": pairs[cell]["trade"].get("owning_ticket"),
                "the_unaudited_stages_that_drew_here":
                    unaudited.get(pairs[cell]["trade"]["key"], []),
                "why": "the re-cut wanted more out of this cell than it has undrawn, or "
                       "than a stage not yet stable under a quota change will let go. It "
                       "is held where it stands, and the slots it could not give up were "
                       "sought from cells with a remainder to spend.",
            })

    if moved == sum(wants_gain.values()):
        why_it_stopped = ("The remainder paid for the re-cut in full: the book's employed total "
                          "is unchanged, no cell's population changed, and nothing a stage has "
                          "drawn against was touched.")
    elif room_to_gain == 0:
        why_it_stopped = (
            "**NOTHING MOVED, and that is the finding.** Every cell of the reopened band has "
            "been drawn against — by T-1174, which drew its children at home, and by T-1175, "
            "which seated its boarders — so the band has no remainder at all. The owner's "
            "ruling of 2026-09-20 re-cuts the remainder and nothing else, and here there is "
            "none: the town's whole 10-19 order is spent. The shop boys the staffing model "
            "wants therefore cannot be minted out of this book as it stands, and that is the "
            "answer T-1448 is owed — not a number, but the reason there is no number.")
    else:
        why_it_stopped = (
            "The remainder could not pay for the re-cut in full. Every cell that could not "
            "take or give its share is named below with the ticket that spent there.")

    for cell, delta in list(gained.items()) + [(k, -v) for k, v in lost.items()]:
        if not delta:
            continue
        pairs[cell]["trade"]["target"] += delta
        pairs[cell]["trade"]["to_reconstruct"] += delta
        pairs[cell]["none"]["target"] -= delta
        pairs[cell]["none"]["to_reconstruct"] -= delta

    # A CELL THE RE-CUT REOPENED AND COULD NOT PAY FOR IS NOT A BUCKET. It orders nobody
    # and holds nobody, and the reason it is empty is already in `refusals` with both
    # numbers — so it is dropped rather than carried as a row of noughts.
    dropped = [b for b in buckets
               if b["axes"].get("trade") == "trade" and not b["target"] and not b["filled"]]
    for bucket in dropped:
        buckets.remove(bucket)

    return {
        "ruling": "the owner's ruling of 2026-09-20 on T-1448's three answers: re-cut the book "
                  "(option 1), and re-cut JUST THE REMAINDER",
        "ticket": "T-1459",
        "what_moved": moved,
        "the_re_cut_wanted": sum(wants_gain.values()),
        "the_younger_bands_had_undrawn": room_to_gain,
        "the_adult_cells_had_undrawn": room_to_lose,
        "bands_reopened": participation["bands_reopened"],
        "participation": participation,
        "into": {k: v for k, v in sorted(gained.items()) if v},
        "out_of": {k: v for k, v in sorted(lost.items()) if v},
        "refusals": refusals,
        "why_it_stopped": why_it_stopped,
        "remainder_stable_stages": dict(sorted(REMAINDER_STABLE_STAGES.items())),
        "held_by_an_unaudited_stage": {k: v for k, v in sorted(unaudited.items())},
        "what_would_unlock_it": (
            "THE FIRST HALF OF THIS IS DONE (T-1503). The lodging stage now deals against a "
            "committed `quota_basis` instead of the book's live `to_reconstruct`, so its "
            "buckets' remainder is spendable and re-cutting them moves none of its 56 "
            "boarders — its own `--self-test` re-cuts a copy of this book and asserts it. "
            "What is left is the stages still reading the room live, named bucket by bucket "
            "in `held_by_an_unaudited_stage`: give each of them a committed basis of its own "
            "and add it to `REMAINDER_STABLE_STAGES`. The alternative — an owner ruling that "
            "people already drawn may be re-dealt — is still not this ticket's to take, and "
            "is no longer needed for the lodging band."),
        "cells_reopened_and_left_empty": sorted(b["key"] for b in dropped),
        "nobody_already_drawn_moved": True,
        "the_sex_axis": participation["the_sex_argument_is_refused"],
    }


def person_owner(axes: dict) -> tuple[str, str]:
    for why, test, ticket in PERSON_TICKET_RULES:
        if test(axes):
            return ticket, why
    raise Fault(f"no ticket owns the person bucket {axes}")


def household_buckets(model: dict, inventory: dict, known: dict) -> dict:
    hh_fig = figure(model, "households_and_families", "households_on_1_july_1835")
    total, basis = point_of(hh_fig)
    matrix = inventory.get("district_group_matrix", {})
    if not matrix:
        raise Fault("the building inventory carries no district/group matrix")

    weights: dict[str, float] = {}
    for htype, group, _ in HOUSEHOLD_BUCKETS:
        row = matrix.get(group)
        if row is None:
            raise Fault(f"the inventory's matrix has no row for {group}")
        for division in CIVIL_DIVISIONS:
            roofs = float(row.get(division) or 0)
            if roofs > 0:
                weights[f"{htype}/{division}"] = roofs
    targets = largest_remainder(total, weights)

    resolved = {d: known["households_present_by_division"][d] for d in CIVIL_DIVISIONS}
    known_by_cell = {k: 0 for k in targets}
    for division in CIVIL_DIVISIONS:
        cells = {k: targets[k] for k in targets if k.endswith("/" + division)}
        for k, v in subtract_pro_rata(cells, resolved[division]).items():
            known_by_cell[k] += v
    for k, v in subtract_pro_rata(targets, known["households_present_unplaced"]).items():
        known_by_cell[k] += v

    owners = {h: t for h, _, t in HOUSEHOLD_BUCKETS}
    buckets = []
    for key in sorted(targets):
        htype, division = key.split("/")
        buckets.append({
            "key": f"households/{key}",
            "axes": {"household_type": htype, "division": division},
            "target": targets[key],
            "known": known_by_cell[key],
            "to_reconstruct": max(0, targets[key] - known_by_cell[key]),
            "filled": 0,
            "owning_ticket": owners[htype],
            "basis": f"the model's {total:,} households apportioned on the inventory's own "
                     f"{htype} roof count in the {division} division",
        })
    buckets.append({
        "key": "households/garrison/fort",
        "axes": {"household_type": "garrison", "division": "fort"},
        "target": None,
        "known": known["households_present_by_division"]["fort"],
        "to_reconstruct": None,
        "filled": 0,
        "owning_ticket": "T-1176",
        "basis": "NOT APPORTIONED — the fort's establishment is read, not modelled (rule 4).",
    })
    return {
        "households_target": total,
        "households_target_basis": basis,
        "households_target_range": [hh_fig["low"], hh_fig["high"]],
        "known_present": known["households_present"],
        # WAS `known_uncertain_offered_to_T-1172`. They are not offered any more: T-1386
        # ruled them into the town and T-1463 counts them known, so the name would be a
        # label for work that has happened (the roster still offers the NAMES, which is a
        # licence and not a quota — see `the_roster_is_not_double_counted`).
        "known_uncertain_in_the_index_ruled_in_by_T-1386": known["households_ruled_present"],
        "buckets": buckets,
    }



# THE TWO CENSUS LINES THAT COUNT MEN, AND THE BRACKET THE SCENE DATE PUTS THEM IN.
#
# Every other enumerated line of the December 1835 State census counts PREMISES — four
# druggists, eight taverns, two breweries — and the register counts premises too, so the
# two sit in one unit and `target - known` is a quota. Two lines do not: "twenty-two
# lawyers" and "fourteen physicians" count PEOPLE, and T-1007's spend
# (`trade_census_1835_spend.json`) is the adjudication that says so and does the join —
# eighteen lawyer records are thirteen men, five of them second printings of one office,
# and three physician records are eight men once the resident cards carrying Egan, Harmon,
# Goodhue, Kimberly and Temple are read alongside them. Set the census's men against the
# register's NOTICES and the book orders four lawyers the town already has and eleven
# physicians it is nothing like short of.
#
# AND THE COUNT IS NOT OF THE SCENE. The census was returned between 1 September and
# December 1835 over a town of 3,297; the scene is 1 July 1835, and the town model brackets
# that day's population between 2,353 and 3,265. A class of men who serve a population
# scales with it, so the number practising on the scene date is bracketed by the same two
# ratios, and the book orders to the LOW END of that bracket and never above it: a
# reconstruction that filled to the December figure would put into the July town the
# practitioners who arrived in the three months after it.
#
# The bracket is stated on the bucket rather than folded into a number, and the low end is
# floored rather than rounded, because a fraction of a physician is a physician this town
# is not known to have had.
PERSON_UNIT_SPEND = "data/research/books/trade_census_1835_spend.json"


def person_unit_brackets(spend: dict, model: dict) -> dict:
    """`{class: bracket}` for the census lines T-1007's spend rules are counted in MEN."""
    july = figure(model, "population", "population_on_1_july_1835")
    census_pop = figure(model, "population", "recorded_state_count_september_to_december_1835")
    denominator = int(census_pop.get("low") or 0)
    if denominator <= 0:
        raise Fault("the town model carries no State-census population to scale the trade "
                    "lines by, and a bracket cannot be drawn without one")
    low_pop, high_pop = int(july["low"]), int(july["high"])
    if low_pop > high_pop:
        raise Fault("the town model's population bracket for the scene date is inverted")
    out = {}
    for row in spend.get("classes", []):
        if row.get("unit") != "person":
            continue
        name = row["class"]
        count = int(row["census_count"])
        held = row.get("held_in_the_counted_unit")
        if held is None:
            raise Fault(f"the spend rules {name!r} in men and does not say how many the town "
                        f"holds in that unit; the book will not guess it")
        out[name] = {
            "unit": "person",
            "unit_basis": row.get("unit_basis"),
            "census_count": count,
            "held_in_the_counted_unit": int(held),
            "register_records": int(row.get("register_records") or 0),
            "low": (count * low_pop) // denominator,
            "high": (count * high_pop) // denominator,
            "scaled_by": {
                "state_census_population": denominator,
                "scene_date_population_low": low_pop,
                "scene_date_population_high": high_pop,
                "figure": "population_on_1_july_1835",
            },
            "method": (f"The census counts {count} in a town of {denominator}; the town model "
                       f"brackets 1 July 1835 between {low_pop} and {high_pop} people. A "
                       f"profession scales with the population it serves, so the scene date "
                       f"holds between {(count * low_pop) // denominator} and "
                       f"{(count * high_pop) // denominator} of them. The book orders to the "
                       f"low end, floored."),
            "source": PERSON_UNIT_SPEND,
            "ticket": "T-1418",
        }
    return out


def business_buckets(crosswalk: dict, register: dict, spend: dict,
                     model: dict) -> dict:
    classes = crosswalk.get("classes", [])
    if not classes:
        raise Fault("the trade-census crosswalk carries no classes")
    documented_zero = set(crosswalk.get("classes_the_town_holds_nothing_for", []))
    brackets = person_unit_brackets(spend, model)
    buckets = []
    for row in sorted(classes, key=lambda r: r["class"]):
        name = row["class"]
        # A class the December census never put a figure against — `other` and
        # `not_stated` — is not a quota: the book orders against printed counts or
        # not at all. `compared: false` is carried rather than skipped, because a
        # class the crosswalk declined to compare (the churches) still has a census
        # figure and still has a ticket that must answer for it.
        if row.get("census_count") is None:
            continue
        census_count = int(row["census_count"])
        known = int(row["town_records_at_scene_date"])
        # A SHORTFALL THE EVIDENCE HAS ALREADY EXPLAINED IS NOT A QUOTA (T-1428). The
        # census was taken between September and December; the crosswalk names, per class,
        # the register's houses whose OPENING is dated after 1 July — houses that account
        # for one of the autumn figures each while honestly standing outside the July town.
        # Ordering a reconstruction against that difference would commission an invention
        # to fill a gap two dated notices have already filled, which is exactly what
        # `does_not_follow` forbids: the spend goes "only where a source NAMES the
        # business", and here the source names it, dates it, and puts it after the scene.
        # So the difference is held apart, the bucket orders against what is left, and the
        # row says which is which rather than arriving at nought by luck.
        if "records_opening_after_scene_date" not in row:
            raise Fault(
                f"the crosswalk's {name!r} row does not say how many of its houses opened "
                "after the scene date, so a shortfall cannot be told from a quota. "
                "Re-run tools/trade_census_1835.py --build.")
        explained = int(row["records_opening_after_scene_date"])
        ticket = BUSINESS_TICKETS.get(name)
        if ticket is None:
            raise Fault(f"no ticket owns the business class {name!r}")
        zero = name in documented_zero
        # A CLASS THE CROSSWALK DECLINED TO COMPARE IS NOT A QUOTA (T-1442). `compared:
        # false` is a ruling ABOUT THE CLASS and not a silence in it: T-0988 holds that a
        # church is a structure and not a trade, so the December figure and the register's
        # congregations are not two sides of one subtraction and the difference between
        # them is not a hole. The book cut the quota anyway until this closeout — target 5
        # minus known 4 ordered a fifth church, against `docs/RESEARCH/business-layer.md`,
        # which had already ruled in writing that "the census counts five and the town
        # holds four, and the fifth is not invented" and said what a fifth would need: a
        # source naming it, and none reached does. So the row is still CARRIED, with both
        # figures on it and its ticket beside them — a class dropped from the book is a
        # class nothing answers for — and it simply orders nothing and says why.
        not_compared = not zero and not bool(row.get("compared"))
        # A CLASS THE CENSUS COUNTS IN MEN IS ORDERED IN MEN, and to the scene date's
        # bracket rather than to the December return. Both halves of the row move
        # together — the target to the bracket's low end and `known` to the men the
        # spend holds — because a quota with one unit on each side of the subtraction
        # is not a quota. Every other class keeps the premises reading it always had.
        bracket = None if zero else brackets.get(name)
        if bracket is None:
            target = 0 if zero else census_count
            basis = ("a DOCUMENTED ZERO of the December 1835 State census — the town held none, "
                     "and none is reconstructed" if zero else
                     f"the December 1835 State census prints {census_count}; the register holds "
                     f"{known} at the scene date")
            if explained and not zero:
                # The ids stay in the crosswalk. The book is cohorts and counts, and a
                # record id inside it is a house this adjudication had no licence to name.
                basis += (f". {explained} more stand in the register with an opening announced "
                          "AFTER 1 July — named and dated in the trade-census crosswalk — so "
                          "that much of the difference is a house the sources already account "
                          "for rather than a hole to fill; the book orders "
                          f"{max(0, target - known - explained)} and not "
                          f"{max(0, target - known)}")
            if not_compared:
                basis += (". The crosswalk does not COMPARE this class — "
                          f"{row.get('note') or 'compared: false'} — so the difference is not a "
                          "shortfall and the book orders nothing against it. The row is carried "
                          "with both figures so the class still has a ticket answering for it")
        else:
            if not_compared:
                # A bracket IS a comparison — it sets the class's scene-date target from its
                # census figure. A class the crosswalk declines to compare cannot also carry
                # one, and the book refuses the contradiction rather than picking a winner.
                raise Fault(
                    f"{name!r} carries a scene-date bracket cut from its census figure, and the "
                    "crosswalk declines to compare the class. A bracket is a comparison, so "
                    "those two rulings contradict. Rule the class compared, or take it off the "
                    "bracket list in data/research/books/trade_census_1835_spend.json.")
            target = bracket["low"]
            known = bracket["held_in_the_counted_unit"]
            basis = (f"the December 1835 State census prints {census_count} — a line that counts "
                     f"MEN and not premises (T-1007). The town holds {known} of them at the scene "
                     f"date against {bracket['register_records']} register records, and the "
                     f"scene date's population brackets the class between {bracket['low']} and "
                     f"{bracket['high']}. The book orders to the low end, {target}")
            if explained:
                # The correction below is in PREMISES and this row is in MEN. Nobody has
                # ruled how a house that opened in August converts into the men the
                # December line counts, so the book refuses rather than guessing a rate.
                raise Fault(
                    f"{name!r} is ordered in MEN and the crosswalk holds {explained} of its "
                    "houses as opening after the scene date. A premises correction cannot be "
                    "subtracted from a count of men without a ruling that says at what rate. "
                    "Rule it, or take the class off the bracket list.")
        buckets.append({
            "key": f"businesses/{name}",
            "axes": {"class": name, "division": "unassigned"},
            "census_line": row.get("census_line"),
            "census_count": 0 if zero else census_count,
            "unit": "person" if bracket else "establishment",
            "scene_bracket": bracket,
            "target": 0 if zero else target,
            "known": known,
            "to_reconstruct": 0 if (zero or not_compared)
                              else max(0, target - known - explained),
            "records_opening_after_scene_date": explained,
            "filled": 0,
            "owning_ticket": ticket,
            "documented_zero": zero,
            "staff_implied": None,
            "staff_owning_ticket": "T-1183",
            "compared_by_the_crosswalk": bool(row.get("compared")),
            "crosswalk_note": row.get("note"),
            "basis": basis,
        })
    totals = crosswalk.get("totals", {})
    return {
        "register_total": int(totals.get("businesses_in_register") or 0),
        "at_scene_date": int(totals.get("at_scene_date") or 0),
        "census_enumerated_total": int(totals.get("census_enumerated_total") or 0),
        "register_businesses_read": len(register.get("businesses", [])),
        "division_note": "EVERY BUSINESS BUCKET IS `unassigned` BY DIVISION TODAY, and that is a "
                         "reading rather than a hole: the register carries a street where the "
                         "paper printed one and no division at all, and assigning premises to a "
                         "division is T-1182's audit and T-1198's seating. The key carries the "
                         "axis so those tickets fill it rather than re-cut the book.",
        "staffing_note": "The STAFF each business implies is T-1183's model and is not guessed at "
                         "here; T-1189 staffs them from it.",
        "buckets": buckets,
    }


def structure_buckets(inventory: dict, programme: dict, occupancy: dict) -> dict:
    matrix = inventory.get("district_group_matrix", {})
    remaining = programme.get("remaining", {}).get("by_district_group", {})
    standing_total = programme.get("standing", {}).get("structure_records")
    buckets = []
    for group in sorted(matrix):
        row = matrix[group]
        for division in DIVISIONS:
            target = int(row.get(division) or 0)
            if target <= 0:
                continue
            to_build = int((remaining.get(division) or {}).get(group) or 0)
            standing = target - to_build
            ticket = STRUCTURE_TICKETS.get((division, group))
            if ticket is None:
                raise Fault(f"no build ticket owns {group} in the {division} division")
            buckets.append({
                "key": f"structures/{group}/{division}",
                "axes": {"group": group, "division": division},
                "target": target,
                "standing": standing,
                "to_build": to_build,
                "to_retire_or_redeal": max(0, -standing) if standing < 0 else 0,
                "filled": 0,
                "owning_ticket": ticket,
                "ground_waits_on": GROUND_TICKETS[division],
                "basis": f"the inventory's district/group matrix sets {target}; the 668-roof "
                         f"programme leaves {to_build} of them to build",
            })
    return {
        "roof_target": int(inventory.get("targets", {}).get("roof_total") or 0),
        "standing_records": standing_total,
        "standing_with_an_occupant": occupancy["with_occupants"],
        "standing_without_an_occupant": occupancy["without_occupants"],
        "to_build_total": int(programme.get("remaining", {}).get("roofs") or 0),
        "redeal_note": "A roof standing where the order book has nobody to put in it is a "
                       "SUBSTITUTION for T-1197, never a demolition: "
                       f"{occupancy['without_occupants']} of the {standing_total} standing records "
                       "carry no occupants block today, and T-1197 re-audits them against this book.",
        "buckets": buckets,
    }


def occupancy_of(root: Path = ROOT) -> dict:
    """Standing structure records, and how many carry an `occupants` block."""
    directory = root / "data" / "structures"
    if not directory.is_dir():
        raise Fault("data/structures is missing — the book cannot count standing roofs")
    with_occ = without = 0
    for path in sorted(directory.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict) or "id" not in doc:
            continue
        if doc.get("occupants"):
            with_occ += 1
        else:
            without += 1
    if with_occ + without == 0:
        raise Fault("data/structures holds no structure records at all")
    return {"records": with_occ + without, "with_occupants": with_occ, "without_occupants": without}


def ground_buckets(programme: dict) -> dict:
    buckets = []
    for row in programme.get("schedule", []):
        if row.get("state") != "gated":
            continue
        division = row.get("district")
        buckets.append({
            "key": f"ground/{row['id']}",
            "axes": {"division": division},
            "roofs_gated": int(row.get("headroom") or row.get("capacity_roofs") or 0),
            "waiting_on": row.get("waiting_on"),
            "owning_tickets": GROUND_TICKETS.get(division, []),
            "filled": 0,
        })
    coverage = programme.get("coverage", {})
    return {
        "roofs_on_committed_ground": int(coverage.get("schedulable_on_committed_ground") or 0),
        "roofs_gated_on_coverage": int(coverage.get("gated_on_coverage") or 0),
        "statement": coverage.get("statement"),
        "buckets": buckets,
    }


INVENTORY_FILE = "data/reconstruction/1835_building_inventory.json"


def restates_the_programme(fig: dict, model_value: int, programme_value: int) -> bool:
    """True when a delta row sets the roof programme beside a figure read OFF it.

    The town model's lodging figures are built straight from
    `district_group_matrix` (model_town_1835.build_lodging reads
    `larger_boarding_houses`, `inns_taverns`, `institutional_public` and
    `fort_principal` out of it), so putting one of them beside that same matrix
    is not a check on the roofs — it is the matrix agreeing with itself. A figure
    that CANNOT fail must not be printed as though it passed (T-1439).

    Two conditions, because naming the inventory as a source is not on its own
    disqualifying: `inns_and_taverns` reads the inventory AND the trade-census
    crosswalk and goes past the matrix (15 against its 10), so that row is a real
    disagreement. Only a figure that names the inventory AND lands exactly on the
    groups it is compared against is a restatement rather than a comparison.
    """
    return INVENTORY_FILE in (fig.get("derived_from") or []) and model_value == programme_value


def programme_deltas(model: dict, inventory: dict, programme: dict,
                     persons: dict, households: dict) -> list[dict]:
    """Where a model target and the 668-roof programme disagree.

    The book carries THE MODEL — that is what the band above it is for — and
    lists the difference here so T-1196 can re-cut the schedule against it rather
    than discover the disagreement halfway through a district.

    EVERY ROW NAMES BOTH SIDES (T-1439). `programme_groups` is the list of
    `district_group_matrix` groups summed on the programme side, and
    `restates_the_programme` says whether the model side was read off those same
    groups. Both exist because the row they were written for was wrong twice over:
    `institutional_and_public` reported a delta of ten roofs by taking the model's
    high end — which counts the fort's ten principal roofs — against
    `institutional_public` alone, while the programme schedules those ten under
    `fort_principal`. 9 + 10 = 19 and the two files already agreed. Naming the
    groups makes that omission impossible to make silently; and once the units
    match, the corrected zero is a restatement rather than an agreement, which is
    the same thing the `boarding_houses` row beside it had been reporting as a
    pass for a year.
    """
    matrix = inventory.get("district_group_matrix", {})

    def group(*names: str) -> int:
        total = 0
        for name in names:
            if name not in matrix:
                raise Fault(f"the roof programme's district_group_matrix carries no group "
                            f"{name!r}, so a delta row compares against nothing")
            total += int(matrix[name].get("total") or 0)
        return total

    dwellings = figure(model, "households_and_families", "dwellings_the_programme_schedules")
    per_dwelling = figure(model, "households_and_families", "people_per_dwelling_november_1835")
    ordinary = group("ordinary_dwellings")
    boarding_model = figure(model, "lodging_and_institutions", "larger_boarding_houses")
    boarding_programme = group("larger_boarding_houses")
    institutional = figure(model, "lodging_and_institutions", "institutional_and_public_roofs")
    # BOTH GROUPS. The model's high end is "9 institutional or public roofs outside the
    # fort and 10 principal roofs inside it", and the programme schedules the inside ten
    # under `fort_principal`. Reading only `institutional_public` here charged the roof
    # programme ten roofs it already had.
    institutional_groups = ["institutional_public", "fort_principal"]
    institutional_programme = group(*institutional_groups)
    fort_principal = group("fort_principal")
    inns = figure(model, "lodging_and_institutions", "inns_and_taverns")
    inns_programme = group("inns_taverns")
    roof_total = int(inventory.get("targets", {}).get("roof_total") or 0)
    out = [
        {"id": "households_against_dwellings", "owning_ticket": "T-1196",
         "model": households["households_target"], "programme": ordinary,
         "delta": households["households_target"] - ordinary,
         "programme_groups": ["ordinary_dwellings"],
         "restates_the_programme": False,
         "statement": f"The household model wants {households['households_target']:,} households "
                      f"and the programme schedules {ordinary:,} ordinary dwellings "
                      f"({dwellings['low']}-{dwellings['high']} in the model's own reading). More "
                      "than one household to a roof is the resolution the census's own "
                      f"{per_dwelling['low']} people per dwelling implies; T-1196 re-cuts the "
                      "schedule to say how many."},
        {"id": "boarding_houses", "owning_ticket": "T-1196",
         "model": int(boarding_model["low"]), "programme": boarding_programme,
         "delta": int(boarding_model["low"]) - boarding_programme,
         "programme_groups": ["larger_boarding_houses"],
         "restates_the_programme": restates_the_programme(
             boarding_model, int(boarding_model["low"]), boarding_programme),
         "statement": f"NOT A CHECK: the model's {int(boarding_model['low'])} larger boarding "
                      f"houses ARE district_group_matrix.larger_boarding_houses — "
                      "model_town_1835.build_lodging reads the figure straight off the roof "
                      f"programme — so this row cannot disagree, and its zero says nothing "
                      f"about whether {boarding_programme} is the right number of boarding "
                      "roofs. An independent count is owed to T-1196 with the re-cut."},
        {"id": "inns_and_taverns", "owning_ticket": "T-1196",
         "model": int(inns["high"]), "programme": inns_programme,
         "delta": int(inns["high"]) - inns_programme,
         "programme_groups": ["inns_taverns"],
         "restates_the_programme": restates_the_programme(
             inns, int(inns["high"]), inns_programme),
         "statement": f"The model reads {inns['low']}-{inns['high']} inns and taverns; the "
                      f"programme schedules {inns_programme}. This one is a real disagreement: "
                      "the model's ceiling is the business layer's count at the scene date, "
                      "not a figure read back off the programme."},
        {"id": "institutional_and_public", "owning_ticket": "T-1196",
         "model": int(institutional["high"]), "programme": institutional_programme,
         "delta": int(institutional["high"]) - institutional_programme,
         "programme_groups": institutional_groups,
         "restates_the_programme": restates_the_programme(
             institutional, int(institutional["high"]), institutional_programme),
         "statement": f"NOT A CHECK: the model reads {institutional['low']}-"
                      f"{institutional['high']} institutional and public roofs — "
                      f"{institutional['low']} outside the fort and {fort_principal} principal "
                      f"roofs inside it — and the programme schedules those same two groups, "
                      f"institutional_public ({group('institutional_public')}) and "
                      f"fort_principal ({fort_principal}), for {institutional_programme}. Both "
                      "ends of the model are read off that matrix, so the row cannot disagree. "
                      "Until T-1439 it reported a delta of ten by taking the fort's roofs on "
                      "the model's side and not on the programme's, which is the schedule "
                      "charged for ten roofs it already had."},
        {"id": "people_per_roof", "owning_ticket": "T-1196",
         "model": persons["town_target"],
         "programme": roof_total,
         "delta": 0,
         "programme_groups": [],
         "restates_the_programme": False,
         "statement": f"{persons['town_target']:,} people under "
                      f"{roof_total:,} roofs is the "
                      "ratio the completed town must meet; the census's own reading for November "
                      f"1835 is {per_dwelling['low']} people per dwelling over 398 dwellings."},
    ]
    # A ROW THAT CANNOT DISAGREE MUST SAY SO IN ITS OWN TEXT, or the table reads as five
    # comparisons when it carries three. The flag and the sentence are written by the same
    # hand and drift apart silently; this is what stops them.
    for row in out:
        says = row["statement"].startswith("NOT A CHECK:")
        if says != bool(row["restates_the_programme"]):
            raise Fault(f"the delta row {row['id']!r} is "
                        f"{'a restatement' if row['restates_the_programme'] else 'a comparison'} "
                        f"and its statement says otherwise")
        if row["restates_the_programme"] and row["delta"] != 0:
            raise Fault(f"the delta row {row['id']!r} restates the programme and still reports "
                        f"a delta of {row['delta']}")
    return out


def invariants(known: dict, persons: dict, households: dict, structures: dict,
               business_buckets_: list[dict]) -> list[dict]:
    uncompared_classes = sum(1 for b in business_buckets_
                             if not b.get("compared_by_the_crosswalk"))
    business_class_count = len(business_buckets_)
    return [
        {"id": "every_person_housed", "owning_ticket": "T-1215",
         "statement": "Every person in the layer — attested, inferred or reconstructed — is a "
                      "member of a household or a lodging place that is seated on a roof.",
         "measured_now": f"{known['households_with_a_lives_at']} of "
                         f"{known['households_present']} present households name a lives_at."},
        {"id": "every_working_person_has_a_workplace", "owning_ticket": "T-1189",
         "statement": "Every person carrying a trade, profession or employment has a workplace, "
                      "or a stated `no fixed workplace`.",
         "measured_now": f"{known['households_with_a_works_at']} of "
                         f"{known['households_present']} present households name a works_at."},
        {"id": "every_business_has_staff", "owning_ticket": "T-1189",
         "statement": "Every business — attested, inferred or reconstructed — carries the staff "
                      "T-1183's model implies for its kind.",
         "measured_now": "not yet measurable: the authored business layer is T-1180."},
        {"id": "every_structure_occupied_or_its_use_stated", "owning_ticket": "T-1197",
         "statement": "Every standing roof carries an occupant or a stated use.",
         "measured_now": f"{structures['standing_without_an_occupant']} of "
                         f"{structures['standing_records']} standing records carry no occupants block."},
        {"id": "dwellings_ratio_within_its_bracket", "owning_ticket": "T-1215",
         "statement": "The town census's people-per-dwelling ratio is met within the model's bracket.",
         "measured_now": f"the book orders {persons['town_target']:,} people into "
                         f"{households['households_target']:,} households."},
        {"id": "an_uncompared_class_orders_nothing", "owning_ticket": "T-1442",
         "statement": "A trade-census class the crosswalk rules `compared: false` carries its "
                      "figures but orders no reconstruction: the difference between a census "
                      "line and the register is only a shortfall where the crosswalk has ruled "
                      "the two comparable.",
         "measured_now": f"carried uncompared: {uncompared_classes} of {business_class_count} "
                         "enumerated business classes, each ordering nought."},
        {"id": "no_bucket_overfilled", "owning_ticket": "T-1166",
         "statement": "No bucket's `filled` exceeds its `to_reconstruct`; a filler that bypasses "
                      "the book is red in check.sh.",
         "measured_now": "enforced by --check on every gate run."},
    ]


def presence_agrees(known: dict, before: dict, rulings: dict) -> None:
    """THE GUARD THAT KEEPS THIS FROM GOING STALE IN SILENCE AGAIN (T-1463).

    The book read `1835_presence_rulings.json` for a year and reported what summing it
    in WOULD give, while every quota was cut as though it said nothing. Nothing fired,
    because nothing compared the two. This does: `known` must equal the pre-ruling cut
    plus the attested and inferred people the rulings' own `counts` block says it ruled
    into the town. Regenerate the rulings without rebuilding the book, or stop summing
    them in, and the gate is red rather than quietly 826 people short.
    """
    counts = rulings.get("counts") or {}
    by_grade = counts.get("persons_by_residence_grade") or {}
    if not by_grade:
        raise Fault("the presence rulings carry no persons_by_residence_grade to check against")
    # A RECONSTRUCTED PERSON IS NOT KNOWN wherever they stand, so the rulings add only
    # the people the SOURCES name. The `reconstructed` grade is somebody else's `filled`.
    ruled_known = sum(int(by_grade.get(g) or 0) for g in ("attested", "inferred"))
    expected = before["persons_present"] + ruled_known
    if known["persons_present"] != expected:
        raise Fault(
            f"the book's known and T-1386's presence rulings disagree: the book counts "
            f"{known['persons_present']} known where the index gives {before['persons_present']} "
            f"and the rulings add {ruled_known} named people, which is {expected}")
    households = int((counts.get("households_ruled") or 0))
    if known["households_ruled_present"] > households:
        raise Fault(
            f"the book counts {known['households_ruled_present']} households ruled present "
            f"where the rulings rule {households}")


# ----------------------------------------------------------------- the build --

def build(data: dict, fills: list | None = None, occupancy: dict | None = None) -> dict:
    fills = list(fills or [])
    for fill in fills:
        if not isinstance(fill, dict) or not fill.get("ticket") or not fill.get("bucket"):
            raise Fault("a fill in the ledger names no ticket or no bucket")
    known = known_layer(data["residents"], data["presence_rulings"])
    before = known_layer(data["residents"])
    presence_agrees(known, before, data["presence_rulings"])
    occ = occupancy if occupancy is not None else occupancy_of()
    participation = trade_participation(data["model"], data["composition"])
    persons = person_buckets(data["model"], data["composition"], data["inventory"], known,
                             participation)
    households = household_buckets(data["model"], data["inventory"], known)
    # THE QUOTAS AS THEY STOOD BEFORE THE RULINGS WERE SUMMED IN, for one purpose only:
    # telling a re-cut apart from an overfill. Every person already drawn was drawn
    # against these, so a bucket whose new quota falls under its own `filled` is the
    # re-cut reaching work already done — REFUSED BY NAME below, with both numbers, and
    # held at what was drawn. A `filled` above even the pre-ruling quota is a filler that
    # bypassed the book, which is the original fault and stays one.
    quota_before = {b["key"]: b["to_reconstruct"] for b in
                    person_buckets(data["model"], data["composition"], data["inventory"],
                                   before)["buckets"]
                    + household_buckets(data["model"], data["inventory"], before)["buckets"]}
    # AND FOR THE FAMILIES THAT PRE-RULING CUT CANNOT REACH, THE QUOTA THE WORK WAS
    # DRAWN AGAINST IS THE BOOK'S OWN LAST ORDER (T-1299). `quota_before` is built from
    # the person and household buckets, because the rulings it holds constant are about
    # people; a BUSINESS bucket's order moves for a different reason — the town reads a
    # documented practitioner and `known` rises — and the same thing then happens to it.
    # T-1299 admitted a press reading of 1 July 1835 that named L. G. Curtiss an attorney,
    # the lawyer line's `known` went from 13 to 14, and the order fell to 1 under the 2
    # T-1418 had already drawn against the 2 this book ordered. That is the re-cut's case
    # exactly — a quota shrinking under work already done — and the owner's ruling of
    # 2026-09-20 covers it: nothing already drawn moves. What stays a FAULT, and the
    # distinction this whole mechanism exists to keep, is a `filled` above even the order
    # the book carried when the work was drawn: that is a filler bypassing the book.
    committed_order = {}
    if BOOK.exists():
        committed_order = {
            b["key"]: b.get("to_reconstruct", b.get("to_build"))
            for fam in json.loads(BOOK.read_text(encoding="utf-8"))["bucket_families"]
            for b in fam["buckets"]}
    recut_refusals = []
    businesses = business_buckets(data["crosswalk"], data["register"], data["trade_spend"],
                                  data["model"])
    structures = structure_buckets(data["inventory"], data["programme"], occ)
    ground = ground_buckets(data["programme"])

    # SUMMED, NOT KEYED. This was a dict comprehension over `fills` until T-1174, so two
    # stages filling the SAME bucket kept only the last of them: `modelled_families` put
    # 300 wives and children into the family buckets and `women_and_children` put 556 more
    # into the same 24 of them, and the book printed 556 as though the first 300 had never
    # happened. Worse, the `no_bucket_overfilled` invariant below was reading that same
    # number, so the one gate that is supposed to refuse an overfilled bucket could not
    # have seen an overfill made by two tickets between them.
    counted = Counter()
    # WHO DREW, NOT JUST HOW MANY. The re-cut below spends a bucket's remainder only where
    # every stage that has drawn there is stable under a quota change, so it needs the
    # tickets and not only the counter — see `REMAINDER_STABLE_STAGES`.
    drawn_by: dict[str, set] = {}
    for fill in fills:
        counted[fill["bucket"]] += int(fill.get("records") or 0)
        if int(fill.get("records") or 0):
            drawn_by.setdefault(fill["bucket"], set()).add(fill.get("ticket") or "")
    families = []
    for key, title, lead, payload in (
        ("persons", "Persons", "Who the town still has to be given, by sex, age, division, "
         "household and trade.", persons),
        ("households", "Households", "The households the model wants, by kind and division.", households),
        ("businesses", "Businesses", "The December 1835 State census set against the register the "
         "town already holds.", businesses),
        ("structures", "Structures", "The roofs the 668-roof programme still owes, by archetype "
         "group and division.", structures),
        ("ground", "Ground first", "The streets, terrain and lots a structure bucket waits on.", ground),
    ):
        buckets = payload.pop("buckets")
        for b in buckets:
            b["filled"] = counted.get(b["key"], 0)
        families.append({"key": key, "title": title, "lead": lead,
                         "summary": payload, "buckets": buckets})

    # THE TRADE RE-CUT RUNS BETWEEN THE COUNTERS AND THE QUOTA CHECK, and it has to: it is
    # bounded by each bucket's undrawn remainder, so it cannot run before `filled` is
    # known — and the quota a bucket is judged against is the re-cut one, so it cannot run
    # after the check either. A bucket the re-cut GROWS is not overfilled by a counter that
    # sat inside its new order.
    trade_re_cut = recut_trade_remainder(families[0]["buckets"], participation, drawn_by)

    for family in families:
        for b in family["buckets"]:
            todo = b.get("to_reconstruct", b.get("to_build"))
            if todo is not None and b["filled"] > todo:
                was = quota_before.get(b["key"])
                cause = "the_re_cut_reached_work_already_drawn"
                if was is None:
                    was = committed_order.get(b["key"])
                    cause = "a_documented_reading_shrank_the_order"
                if was is not None and b["filled"] <= was:
                    recut_refusals.append({
                        "bucket": b["key"],
                        "owning_ticket": b.get("owning_ticket"),
                        "cause": cause,
                        "quota_it_was_drawn_against": was,
                        "the_re_cut_would_have_ordered": todo,
                        "already_drawn": b["filled"],
                        "held_at": b["filled"],
                        "why": ("the re-cut would put this bucket's order under the people "
                                "already drawn against it."
                                if cause == "the_re_cut_reached_work_already_drawn" else
                                "the town read a practitioner it can name and this bucket's "
                                "order fell under the records already drawn against it. The "
                                "town over-supplies this class by the difference, and the "
                                "surplus is retired by the ticket that owns the bucket rather "
                                "than by this one.") +
                               " The owner's ruling of 2026-09-20 "
                               "(T-1459) holds here: no bucket's target falls below what has "
                               "been drawn against it, and the refusal is named with both "
                               "numbers rather than clamped in silence.",
                    })
                    b["to_reconstruct"] = b["filled"]
                    b["recut_refused"] = True
                else:
                    raise Fault(f"the bucket {b['key']} is overfilled: {b['filled']} of {todo}")

    spent = Counter()
    for fill in fills:
        spent[fill["ticket"]] += int(fill.get("records") or 0)
    spent_by = [{"ticket": t, "records": n,
                 "buckets": sorted({f["bucket"] for f in fills if f["ticket"] == t})}
                for t, n in sorted(spent.items(), key=lambda kv: (-kv[1], kv[0]))]

    roster = data["roster"].get("counts", {}).get("by_class", {})
    offered = {k: v for k, v in sorted(roster.items()) if k in ROSTER_TICKETS}

    doc = {
        "$schema_note": "DERIVED — regenerate with tools/build_order_book_1835.py --build; "
                        "tools/check.sh re-derives it. Do not hand-edit. The `fills` ledger and "
                        "each bucket's `filled` are written by the reconstruction tools.",
        "id": "chicago_july_1835_reconstruction_order_book",
        "ticket": "T-1166",
        "target_date": SCENE_DATE,
        "generated_by": "tools/build_order_book_1835.py --build",
        "not_a_reading": "an adjudication over committed derived files — no page of any source "
                         "was opened, nobody is named, nobody is aged, nobody is housed",
        "inputs": [
            "data/reconstruction/1835_town_model.json",
            "data/reconstruction/1835_population_profile.json",
            "data/reconstruction/1835_borderline_roster.json",
            "data/reconstruction/1835_665_roof_programme.json",
            "data/reconstruction/1835_building_inventory.json",
            "data/research/books/trade_census_1835_crosswalk.json",
            "data/research/books/trade_census_1835_spend.json",
            "data/research/census_1840/composition_1840.json",
            "data/residents/index.json",
            "data/research/newspapers/register_1835.json",
            "data/structures/*.json",
        ],
        "method": {
            "point_from_range": "Where the town model gives a point the book takes it; where it "
                                "gives only a range the book takes the MIDPOINT, rounded half up, "
                                "and carries the range beside it. A quota cannot be a range.",
            "unresolved_known": "A named person or household the layer cannot place on an axis is "
                                "subtracted PRO RATA across that axis's cells, so the book never "
                                "orders a replacement for somebody already standing in the town.",
            "presence_is_the_test": "A household is known when the index records it `present` on "
                                    "the scene date, or when T-1386's presence rulings rule it "
                                    "present. The 820 `uncertain` households hold 827 people who "
                                    "stand in the layer, so counting them unknown ordered a "
                                    "replacement for each of them (T-1463). The two evidenced "
                                    "absences stay out; the roster stays a licence, not a quota, "
                                    "so counting these once orders nobody twice.",
            "the_re_cut_does_not_reach_work_already_done": "Summing the rulings into `known` "
                                    "shrinks quotas people have already been drawn against. No "
                                    "bucket's order falls below its own `filled`: the re-cut is "
                                    "REFUSED there by name, with both numbers, in `recut_refusals` "
                                    "— never clamped in silence (the owner's ruling of 2026-09-20).",
            "the_fort_is_read_not_apportioned": "The garrison and its households carry a null "
                                                "target; T-1176 reads the return and the civilian "
                                                "quota is re-cut at the next --build.",
            "rounding": "Largest remainder throughout, ties broken on the bucket key, so two "
                        "builds on one set of inputs are byte-identical.",
            "real_names_first": "The roster (T-1159) offers every name the corpus printed and "
                                "withheld. It is a licence on WHICH name a filler uses and never "
                                "a quota, so it is counted against its ticket rather than smeared "
                                "across cells that cannot hold it.",
        },
        "known_layer": known,
        # THE POPULATION THE RULINGS PUT IN THE TOWN (T-1386), AND NOW SUMMED INTO
        # `known_layer` RATHER THAN STATED BESIDE IT (T-1463). This block stood here for a
        # year saying what summing the rulings in WOULD give — 1,283 against the 457 the
        # book cut its quotas from — and declining to do it, on the reasoning that shrinking
        # quotas under work already drawn would trip the overfill gate. That reasoning was
        # right about the mechanism and wrong about the answer: the gate is what
        # `recut_refusals` is for, and the price of waiting was that every bucket ordered a
        # replacement for 826 people standing in the layer. The owner found it off the
        # landing card — 2,267 people against a 2,536 target with 929 still on order, a town
        # that would have converged to ~3,196. The block is kept, and now RECONCILES.
        "population_ruled_in": {
            "ticket": "T-1386",
            "source": "data/reconstruction/1835_presence_rulings.json",
            "summed_into_known": True,
            "summed_by": "T-1463",
            "persons_ruled_present": int(
                (data["presence_rulings"].get("counts") or {}).get("persons_ruled") or 0),
            "households_ruled_present": int(
                (data["presence_rulings"].get("counts") or {}).get("households_ruled") or 0),
            "by_presence_tier": (data["presence_rulings"].get("counts") or {}
                                 ).get("persons_by_tier") or {},
            "by_residence_grade": (data["presence_rulings"].get("counts") or {}
                                   ).get("persons_by_residence_grade") or {},
            # A PRESENCE TIER IS NOT A RESIDENCE GRADE, and the difference is why 826 and not
            # 148 enter `known`. `by_presence_tier` prices HOW the ruling was reached — 679 of
            # the 827 are `carried` by the standing rule rather than read on the day. That is
            # the confidence of the PRESENCE, and it is carried on every one of those cards
            # already. `by_residence_grade` is who the person is to the sources: 276 attested
            # and 550 inferred, 1 reconstructed. `known` is what the sources give the town, so
            # it takes the 826 named and leaves the 1 reconstructed to somebody's `filled`.
            "what_known_takes": "the 826 attested and inferred; the 1 reconstructed is a fill",
            "persons_known_before_the_rulings": before["persons_present"],
            "persons_known_now": known["persons_present"],
            "households_known_before_the_rulings": before["households_present"],
            "households_known_now": known["households_present"],
            "the_roster_is_not_double_counted": "R1 offers these names to T-1172 as a LICENCE "
                                                "to use a real read name, never as a quota "
                                                "(rule `real_names_first`), and T-1386 has "
                                                "already re-admitted them into the layer. "
                                                "Counting them known orders nobody twice; it "
                                                "stops ordering them once.",
            "what_re_cuts_the_quotas": ["T-1196", "T-1197", "T-1179"],
        },
        # THE RE-CUT'S REFUSALS. Empty is the healthy state; a row is a bucket whose new
        # order would have fallen under the people already drawn against it, held at what
        # was drawn and named here with both numbers.
        "recut_refusals": recut_refusals,
        # THE TRADE RE-CUT (T-1459), carried whole: the record it was read from, the factor
        # it put on each band, what moved, and every cell where a person already drawn stood
        # in its way. The SEX of the remainder is not re-cut and the block says why in terms.
        "trade_re_cut": trade_re_cut,
        # WHO HAS ALREADY SPENT AGAINST THIS BOOK, named with what they spent, so a reader can
        # tell the settled parts of the book from the open ones. A re-cut that moved a quota
        # under a stage which already spent is the one failure T-1459 exists to make
        # impossible, and this is the list it is measured against.
        "spent_by": spent_by,
        "roster_offered": {
            "total": int(data["roster"].get("counts", {}).get("offered") or 0),
            "by_class": offered,
            "tickets": {k: ROSTER_TICKETS[k] for k in sorted(offered)},
        },
        "totals": {
            "persons_target": persons["town_target"],
            "persons_known": known["persons_present"],
            "persons_to_reconstruct": sum(b["to_reconstruct"] or 0 for b in families[0]["buckets"]),
            "households_target": households["households_target"],
            "households_known": known["households_present"],
            "households_to_reconstruct": sum(b["to_reconstruct"] or 0 for b in families[1]["buckets"]),
            "businesses_target": sum(b["target"] for b in families[2]["buckets"]),
            "businesses_known": sum(b["known"] for b in families[2]["buckets"]),
            "businesses_to_reconstruct": sum(b["to_reconstruct"] for b in families[2]["buckets"]),
            "roofs_target": structures["roof_target"],
            "roofs_standing": structures["standing_records"],
            "roofs_to_build": structures["to_build_total"],
            # THE NUMBER SAID OUT LOUD (T-1463). `persons_standing` is what the layer holds
            # on 1 July 1835 — the landing card's figure — and `persons_still_owed` is what
            # the book has left to order after its counters. Their sum is what this town
            # converges to, and it is the one line that would have caught the over-order.
            "persons_standing": known["persons_standing"],
            "persons_still_owed": sum(
                max(0, (b["to_reconstruct"] or 0) - b["filled"]) for b in families[0]["buckets"]),
            "persons_when_the_book_is_filled": known["persons_standing"] + sum(
                max(0, (b["to_reconstruct"] or 0) - b["filled"]) for b in families[0]["buckets"]),
            "persons_target_range": list(persons["town_target_range"]),
            "households_standing": known["households_present"] + known["households_reconstructed"],
            "households_still_owed": sum(
                max(0, (b["to_reconstruct"] or 0) - b["filled"]) for b in families[1]["buckets"]),
        },
        # WHAT THE RE-CUT FOUND, written into the book rather than into a report nobody
        # re-derives (T-1463). Two of these are adjudications the ticket asked for out
        # loud, and the third is a collision this run declines to rule on.
        "what_the_re_cut_found": recut_findings(known, before, families, recut_refusals),
        "bucket_families": families,
        "programme_deltas": programme_deltas(data["model"], data["inventory"],
                                             data["programme"], persons, households),
        "invariants": invariants(known, persons, households, structures,
                                 families[2]["buckets"]),
        "fills": fills,
    }
    if len(doc["bucket_families"]) != 5:
        raise Fault("the order book is five bucket families; fewer is a book with a hole in it")
    return doc


def converges_inside_the_model(doc: dict) -> str:
    """THE OVERSHOOT GATE (T-1463), asked of the SHIPPED book on every --build and --check.

    The bug this ticket exists to remove was invisible for a year because nothing multiplied
    the book's remainder out against the town already standing: 2,267 people stood, 843 were
    still on order, and 3,110 was never set beside a model that wanted 2,536. This sets them
    beside each other and says the number out loud whether it passes or fails.

    It is NOT an invariant of the bucket algebra, which is why it lives here and not in
    `build`. `persons_still_owed` is `to_reconstruct - filled`, so a fixture book with a
    partial ledger re-orders people already drawn and lands wherever its fixture puts it.
    The committed book carries the whole ledger, and it is the one that has to close.
    """
    t = doc["totals"]
    lands, low, high = t["persons_when_the_book_is_filled"], *t["persons_target_range"]
    said = (f"{t['persons_standing']:,} standing plus {t['persons_still_owed']:,} still owed "
            f"is {lands:,}, against a model of {t['persons_target']:,} within {low:,}-{high:,}")
    if not low <= lands <= high:
        raise Fault(f"the book orders a town outside the model: {said}. A remainder that lands "
                    f"outside the range is ordering people the layer already holds, or too few "
                    f"to reach the town")
    return said


DEAD_TICKET_STATES = ("done", "split", "withdrawn")
TICKETS = ROOT / "tickets"


def ticket_states(directory: Path = TICKETS) -> dict[str, str]:
    """Every ticket id in the queue against its state, read off the front matter.

    A CHECK INPUT AND NEVER A BUILD INPUT. Nothing the book EMITS may depend on what
    the queue happens to hold this morning, or two builds of the same data would
    differ and `--check` would be measuring the queue instead of the arithmetic. So
    this is read by the gate below and by nothing else; the owner tables above stay
    hand-written, with their reasoning beside them, exactly as they were.
    """
    out = {}
    if not directory.is_dir():
        return out
    for path in sorted(directory.glob("T-*.md")):
        head = path.read_text(encoding="utf-8").split("---")
        if len(head) < 3:
            continue
        fields = dict(re.findall(r"^(\w+): (.*)$", head[1], re.M))
        if fields.get("id"):
            out[fields["id"].strip()] = fields.get("state", "").strip()
    return out


def every_work_order_names_a_live_ticket(doc: dict, states: dict[str, str] | None = None) -> str:
    """THE WORK-ORDER GATE (T-1420), asked on every --build and --check.

    THE FAILURE IT REMOVES. `ticket.mjs done` already prints a NOTE when a close
    leaves a split parent with no live child: "any research unit that defers to it by
    id is now stranded (T-1237). That fails the re-derivation, in a tool this PR does
    not run." This is that tool. Until now nothing re-derived the order book against
    the queue, so the note was advice a closing run could read and walk past, and by
    2026-09-21 thirteen of the twenty-four ids the book's owner tables named had
    closed or split under it — the west ground still waiting on T-1192 eight days
    after T-1192 became two tickets, which is what T-1420 was filed for.

    WHAT IS A WORK ORDER, AND WHAT IS NOT. A bucket's `owning_ticket`,
    `owning_tickets` and `ground_waits_on` say who MUST DO the work that is left.
    They are the only forward-looking ticket ids in this book, and a forward-looking
    id naming a ticket nobody can claim is a hole. Everything else the book stamps
    with a ticket is BACKWARD-looking and must never move: `fills[].ticket` is who
    actually filled a bucket, `recut_refusals` and `programme_deltas` record who made
    a ruling, `roster_offered.tickets` records who a licence was offered to, and the
    book's own `ticket` is who wrote it. Those are provenance, and rewriting
    provenance to keep a gate quiet would be the worse defect by far.

    AND ONLY WHERE THERE IS WORK LEFT. A bucket the town has already filled keeps the
    id of the ticket that filled it, because that is the same fact `fills` carries and
    there is nothing left to order. So the gate fires exactly when a run is told to do
    something by a ticket that no longer exists — which is also why it stays quiet
    through the ordinary close, where a ticket ends by discharging its own buckets.

    A BLOCKED TICKET IS LIVE. `blocked-owner` and `blocked-tech` are on the board,
    carry a `blocked_on`, and unblock; `done`, `split` and `withdrawn` name nobody.
    """
    states = ticket_states() if states is None else states
    holes = []
    for family in doc.get("bucket_families", []):
        for bucket in family.get("buckets", []):
            owed = bucket.get("to_reconstruct")
            if owed is None:
                owed = bucket.get("to_build")
            if owed is None:
                owed = bucket.get("roofs_gated")
            left = max(0, (owed or 0) - (bucket.get("filled") or 0))
            if left <= 0:
                continue
            named = [bucket.get("owning_ticket")] + list(bucket.get("owning_tickets") or [])
            named += list(bucket.get("ground_waits_on") or [])
            for ticket in named:
                if not ticket:
                    continue
                state = states.get(ticket)
                if state is None:
                    holes.append(f"{bucket['key']} is ordered by {ticket}, which is not a ticket")
                elif state in DEAD_TICKET_STATES:
                    holes.append(f"{bucket['key']} has {left} left and is ordered by "
                                 f"{ticket}, which is {state}")
    if holes:
        raise Fault("the book orders work from tickets nobody can claim — sweep the owner "
                    "tables onto the live successors (T-1420): " + "; ".join(sorted(holes)[:8])
                    + (f" (+{len(holes) - 8} more)" if len(holes) > 8 else ""))
    if not states:
        return "the queue could not be read, so no work order was checked"
    ordered = sum(1 for f in doc.get("bucket_families", []) for b in f.get("buckets", []))
    return f"every work order across {ordered} buckets names a ticket a run can still claim"


def recut_findings(known: dict, before: dict, families: list, refusals: list) -> list[dict]:
    """The three things summing T-1386 into `known` made measurable (T-1463)."""
    def owed(fam, ticket=None):
        return sum(max(0, (b["to_reconstruct"] or 0) - b["filled"]) for b in fam["buckets"]
                   if ticket is None or b["owning_ticket"] == ticket)
    persons, households = families[0], families[1]
    p_1171, h_1171 = owed(persons, "T-1171"), owed(households, "T-1171")
    held = sum(r["already_drawn"] - r["the_re_cut_would_have_ordered"] for r in refusals)
    target = persons["summary"]["town_target"]
    low, high = persons["summary"]["town_target_range"]
    standing = known["persons_standing"]
    still = owed(persons)
    return [
        {
            "id": "t_1171_adjudicated",
            "asks": "T-1171 closed 2026-09-18 (PR #1476) having drawn 124 of 556, and the "
                    "presence rulings landed 2026-09-19 — the day after. Was its 432 real, "
                    "or an artifact of a quota cut against a town that did not yet hold the "
                    "827 ruled-in people?",
            "the_answer_is": "BOTH, and the split is measured rather than argued.",
            "household_leg_before": 58, "household_leg_now": h_1171,
            "person_leg_before": 374, "person_leg_now": p_1171,
            "measured": f"Of the 432, the household leg is DISCHARGED: T-1171's household quota "
                        f"was 182 against 124 drawn and the re-cut takes it to its own drawn "
                        f"figure, so it owes {h_1171}. The person leg is PART artifact: 374 "
                        f"before, {p_1171} now. The remainder is owed and is not a counting "
                        f"error, so T-1171 REOPENS for it.",
            "verdict": "reopen T-1171 for the persons; the households are discharged",
        },
        {
            "id": "the_remainder_said_out_loud",
            "asks": "What does the town converge to if every remaining order is filled?",
            "persons_standing_in_the_layer": standing,
            "persons_still_owed": still,
            "converges_to": standing + still,
            "model_point": target, "model_range": [low, high],
            "measured": f"{standing:,} standing plus {still:,} still owed is {standing + still:,}, "
                        f"inside the model's {low:,}-{high:,}. Before the re-cut the same sum was "
                        f"{standing:,} + 843 = {standing + 843:,}, and the book was ordering a "
                        f"replacement for 826 people already in the layer. It is {standing + still - target:,} "
                        f"above the model's {target:,} point, and that surplus is the {held:,} people "
                        f"drawn into {len(refusals)} buckets past what the re-cut would now order — "
                        f"named in `recut_refusals`, held rather than clamped, and retired or "
                        f"re-familied by T-1196, T-1197 and T-1179 rather than by this book.",
        },
        {
            "id": "households_are_counted_in_two_different_units",
            "asks": "The model wants 643 households and the layer now holds "
                    f"{known['households_present'] + known['households_reconstructed']:,} records. "
                    "Are those the same thing?",
            "the_answer_is": "NOT THIS RUN'S TO MAKE — reported, not acted on.",
            "households_known_before_the_rulings": before["households_present"],
            "households_known_now": known["households_present"],
            "model_target": households["summary"]["households_target"],
            "model_range": list(households["summary"]["households_target_range"]),
            "measured": "814 of the 820 records T-1386 ruled present hold exactly ONE person, and "
                        "424 of them are a single name off a post-office letter list. A letter-list "
                        "name evidences a PERSON in the town; whether it evidences a HOUSEHOLD in "
                        "the model's sense — the model's own average is 3.9 people to a house — is "
                        "a modelling question, and the persons re-cut does not depend on the answer. "
                        "The household quota therefore reads 0 owed today. That is arithmetic the "
                        "ruling forces, not a finding that the town has all the houses it needs.",
            "declined": "T-1463 says a run that finds a new modelling decision required is to stop "
                        "and say so rather than invent it. This is that. Filed for the owner.",
        },
    ]


# ---------------------------------------------------------------- the report --

def report_text(doc: dict) -> str:
    t = doc["totals"]
    out = [
        "# The 1835 reconstruction order book",
        "",
        "> DERIVED from `data/reconstruction/1835_reconstruction_order_book.json`. Regenerate with",
        "> `tools/build_order_book_1835.py --build`; `tools/check.sh` re-derives both. Do not hand-edit.",
        "",
        f"**T-1166.** Known minus model, per bucket, with the ticket that owns filling it. "
        f"The town converges to **{t['persons_target']:,} people** in "
        f"**{t['households_target']:,} households**, working "
        f"**{t['businesses_target']:,} enumerated businesses**, under "
        f"**{t['roofs_target']:,} roofs**.",
        "",
        "| | target | known | to reconstruct |",
        "|---|---:|---:|---:|",
        f"| Persons | {t['persons_target']:,} | {t['persons_known']:,} | {t['persons_to_reconstruct']:,} |",
        f"| Households | {t['households_target']:,} | {t['households_known']:,} | {t['households_to_reconstruct']:,} |",
        f"| Businesses (enumerated classes) | {t['businesses_target']:,} | {t['businesses_known']:,} | {t['businesses_to_reconstruct']:,} |",
        f"| Roofs | {t['roofs_target']:,} | {t['roofs_standing']:,} | {t['roofs_to_build']:,} |",
        "",
        f"**{t['persons_standing']:,} people stand in the layer today** and "
        f"**{t['persons_still_owed']:,}** are still owed after the counters, so the town this "
        f"book converges to is **{t['persons_when_the_book_is_filled']:,}** — inside the model's "
        f"{t['persons_target_range'][0]:,}-{t['persons_target_range'][1]:,}. `--build` and "
        "`--check` both refuse a remainder that lands outside it.",
        "",
        "## What the re-cut found",
        "",
        "> T-1463 summed T-1386's presence rulings into `known`. These are the three things "
        "that made measurable, carried in the book so they cannot go stale in a report.",
        "",
    ]
    for f in doc.get("what_the_re_cut_found", []):
        out += ["", f"### {f['id'].replace('_', ' ')}", "", f"*{f['asks']}*", "", f["measured"]]
        if f.get("verdict"):
            out.append(f"\n**Verdict:** {f['verdict']}")
        if f.get("declined"):
            out.append(f"\n**Declined:** {f['declined']}")
    refusals = doc.get("recut_refusals", [])
    out += ["", "## Where the re-cut was refused", "",
            f"{len(refusals)} bucket{'' if len(refusals) == 1 else 's'} would have had "
            "their order cut below the people already drawn against them. The owner's ruling "
            "of 2026-09-20 refuses that by name rather than clamping it: each is held at what "
            "was drawn, and the surplus is retired or re-familied by T-1196, T-1197 and T-1179.", ""]
    if refusals:
        out += ["| bucket | ticket | cause | quota it was drawn against | the re-cut would "
                "order | drawn |", "|---|---|---|---:|---:|---:|"]
        for r in refusals:
            out.append(f"| `{r['bucket']}` | {r['owning_ticket']} | "
                       f"{r.get('cause', 'the_re_cut_reached_work_already_drawn')} | "
                       f"{r['quota_it_was_drawn_against']:,} | "
                       f"{r['the_re_cut_would_have_ordered']:,} | {r['already_drawn']:,} |")
    rc = doc.get("trade_re_cut") or {}
    if rc:
        pt = rc["participation"]
        out += [
            "", "## The trade cut, re-cut on its remainder", "",
            "> **T-1459**, on the owner's ruling of 2026-09-20: take option 1 — re-cut the book — "
            "and re-cut **just the remainder**.", "",
            "### The age of a working person is read, not assumed", "",
            pt["the_age_argument"], "",
            "| band | workers the sources record | share of the 1840 pyramid | weight in the trade cut |",
            "|---|---:|---:|---:|",
        ]
        for band, _, _, _ in AGE_BANDS:
            out.append(f"| `{band}` | {pt['workers'].get(band, 0):,} | "
                       f"{pt['pyramid_shares'][band]:.4f} | {pt['factors'][band]:.4f} |")
        out += [
            "", f"Read from {pt['read_from']}. "
            f"{pt['reconstructed_skipped']:,} person(s) the layer grades `reconstructed` were "
            "skipped: a stage's own draw is not evidence for the cut that produced it.", "",
            "### The sex of the remainder is NOT re-cut", "",
            pt["the_sex_argument_is_refused"], "",
            "### What moved", "",
            f"The re-cut wanted **{rc['the_re_cut_wanted']:,}** trade slots in the bands it "
            f"reopened. The younger bands held **{rc['the_younger_bands_had_undrawn']:,}** undrawn "
            f"and the adult cells it would draw from held **{rc['the_adult_cells_had_undrawn']:,}**, "
            f"so **{rc['what_moved']:,}** moved and the book's employed total did not change. "
            "Every cell below is a `lodging` cell on both sides, because every `family` cell of "
            "the reopened band is drawn out: the working youths this book still orders are "
            "BOARDERS — an apprentice or a shop hand sleeping where he works — which is a "
            "consequence of what is already drawn and not a claim about 1835.", "",
            "| into | slots |", "|---|---:|",
        ]
        for cell, n in rc["into"].items():
            out.append(f"| `{cell}` | {n:,} |")
        out += ["", "| out of | slots |", "|---|---:|"]
        for cell, n in rc["out_of"].items():
            out.append(f"| `{cell}` | {n:,} |")
        out += ["", f"**{len(rc['refusals'])} cell(s) could not take or give their share**, "
                "because the people who would have filled them are already drawn. Each is named "
                "with both numbers; none was clamped in silence, and no person already drawn "
                "moved.", ""]
        if rc["refusals"]:
            out += ["| cell | the re-cut wanted | the remainder could pay | already drawn | by |",
                    "|---|---:|---:|---:|---|"]
            for r in rc["refusals"]:
                out.append(f"| `{r['cell']}` ({r['direction']}) | "
                           f"{r['the_re_cut_wanted']:,} | {r['the_remainder_could_pay']:,} | "
                           f"{r['already_drawn_in_the_way']:,} | {r.get('drawn_by') or '—'} |")
        out += ["", "### Who has already spent against this book", "",
                "The re-cut's one forbidden move is to pull a quota out from under a stage that "
                "has already drawn on it. These are the stages that have, so a reader can tell "
                "the settled parts of the book from the open ones:", "",
                "| ticket | persons drawn | buckets |", "|---|---:|---:|"]
        for row in doc.get("spent_by", []):
            out.append(f"| {row['ticket']} | {row['records']:,} | {len(row['buckets']):,} |")
        out.append("")

    out += [
        "",
        "## The rules this book adds",
        "",
    ]
    for key, text in doc["method"].items():
        out.append(f"- **{key.replace('_', ' ')}** — {text}")
    out += ["", "## Real names before invented ones", "",
            f"The roster offers {doc['roster_offered']['total']:,} names the corpus printed and this "
            "project withheld. Each class is a licence, not a quota:", "",
            "| class | offered | ticket |", "|---|---:|---|"]
    for cls, n in doc["roster_offered"]["by_class"].items():
        out.append(f"| `{cls}` | {n:,} | {doc['roster_offered']['tickets'][cls]} |")

    for family in doc["bucket_families"]:
        out += ["", f"## {family['title']}", "", family["lead"], ""]
        summary = family["summary"]
        for k, v in summary.items():
            if isinstance(v, (int, float)):
                out.append(f"- `{k}`: {v:,}")
            elif isinstance(v, str):
                out.append(f"- `{k}`: {v}")
            elif isinstance(v, list):
                out.append(f"- `{k}`: {', '.join(str(x) for x in v)}")
        out += ["", "| bucket | target | known | to do | filled | ticket |", "|---|---:|---:|---:|---:|---|"]
        for b in family["buckets"]:
            target = b.get("target", b.get("roofs_gated"))
            known = b.get("known", (b.get("known_attested", 0) + b.get("known_inferred", 0))
                          if "known_attested" in b else b.get("standing"))
            todo = b.get("to_reconstruct", b.get("to_build"))
            owner = b.get("owning_ticket") or ", ".join(b.get("owning_tickets", []))
            fmt = lambda v: "—" if v is None else f"{v:,}"
            out.append(f"| `{b['key']}` | {fmt(target)} | {fmt(known)} | {fmt(todo)} "
                       f"| {b['filled']:,} | {owner} |")

    restatements = [d for d in doc["programme_deltas"] if d.get("restates_the_programme")]
    out += ["", "## Where the model and the roof programme disagree", "",
            "The book carries THE MODEL. Every difference is listed here for T-1196, which "
            "re-cuts the 668-roof schedule against it. `programme groups` names the "
            "`district_group_matrix` groups summed on the programme side; a row marked NOT A "
            "CHECK reads its model figure off those same groups and therefore cannot "
            f"disagree ({len(restatements)} of {len(doc['programme_deltas'])} do).", "",
            "| | model | programme | delta | programme groups |",
            "|---|---:|---:|---:|---|"]
    for d in doc["programme_deltas"]:
        groups = ", ".join(f"`{g}`" for g in d.get("programme_groups") or []) or "—"
        out.append(f"| **{d['id']}** — {d['statement']} | {d['model']:,} | {d['programme']:,} "
                   f"| {d['delta']:+,} | {groups} |")

    out += ["", "## The invariants the convergence tickets assert", ""]
    for inv in doc["invariants"]:
        out.append(f"- **{inv['id']}** ({inv['owning_ticket']}) — {inv['statement']} "
                   f"*Now:* {inv['measured_now']}")
    out.append("")
    return "\n".join(out)


# ------------------------------------------------------------------ commands --

def _fills_on_disk() -> list:
    if not BOOK.exists():
        return []
    try:
        return json.loads(BOOK.read_text(encoding="utf-8")).get("fills", [])
    except json.JSONDecodeError as exc:
        raise Fault(f"the committed order book is not JSON: {exc}") from exc


def cmd_build() -> int:
    doc = build(load(), _fills_on_disk())
    lands = converges_inside_the_model(doc)
    owners = every_work_order_names_a_live_ticket(doc)
    BOOK.parent.mkdir(parents=True, exist_ok=True)
    BOOK.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report_text(doc), encoding="utf-8")
    n = sum(len(f["buckets"]) for f in doc["bucket_families"])
    print(f"OK: 1835 reconstruction order book — {n} buckets in "
          f"{len(doc['bucket_families'])} families; {doc['totals']['persons_to_reconstruct']:,} "
          f"persons, {doc['totals']['households_to_reconstruct']:,} households, "
          f"{doc['totals']['businesses_to_reconstruct']:,} businesses and "
          f"{doc['totals']['roofs_to_build']:,} roofs to reconstruct; {lands}; {owners}")
    return 0


def cmd_check() -> int:
    faults = []
    if not BOOK.exists():
        print("FAIL: the 1835 reconstruction order book is missing — run --build", file=sys.stderr)
        return 1
    expected = build(load(), _fills_on_disk())
    if json.loads(BOOK.read_text(encoding="utf-8")) != expected:
        faults.append("the 1835 reconstruction order book is stale — run --build")
    if not REPORT.exists():
        faults.append("the order book's report is missing — run --build")
    elif REPORT.read_text(encoding="utf-8") != report_text(expected):
        faults.append("the order book's report is stale — run --build")
    if faults:
        for f in faults:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    t = expected["totals"]
    print(f"OK: 1835 reconstruction order book — {t['persons_to_reconstruct']:,} persons, "
          f"{t['households_to_reconstruct']:,} households, "
          f"{t['businesses_to_reconstruct']:,} businesses, {t['roofs_to_build']:,} roofs to go; "
          f"{converges_inside_the_model(expected)}; "
          f"{every_work_order_names_a_live_ticket(expected)}")
    return 0


def cmd_self_test() -> int:
    data = load()
    occ = occupancy_of()
    fired = 0

    def fires(why, fn):
        nonlocal fired
        try:
            fn()
        except Fault:
            fired += 1
            print(f"   fires: {why}")
            return
        raise AssertionError(f"did not fire: {why}")

    # AN APPORTIONMENT CLOSES OR IT IS NOT ONE.
    assert sum(largest_remainder(100, {"a": 1, "b": 1, "c": 1}).values()) == 100
    assert largest_remainder(10, {"a": 1, "b": 1}) == {"a": 5, "b": 5}
    # …and it is DETERMINISTIC: the same weights give the same answer, tie or no tie.
    assert largest_remainder(7, {"a": 1, "b": 1, "c": 1}) == largest_remainder(7, {"c": 1, "b": 1, "a": 1})
    fires("an apportionment across weights that sum to zero",
          lambda: largest_remainder(5, {"a": 0}))
    fires("an apportionment of a negative total", lambda: largest_remainder(-1, {"a": 1}))

    # A POINT FROM A RANGE, and an inverted range is a fault rather than a negative quota.
    assert point_of({"figure": "x", "low": 10, "high": 20, "point": None})[0] == 15
    assert point_of({"figure": "x", "low": 10, "high": 20, "point": 12})[0] == 12
    fires("an inverted range", lambda: point_of({"figure": "x", "low": 20, "high": 10}))
    fires("a figure with no range at all", lambda: point_of({"figure": "x"}))

    # A MISSING INPUT IS A FAULT, not a book quietly built without it.
    fires("an input file the book cannot read", lambda: load(Path("/nonexistent-root-for-the-self-test")))

    # THE UNRESOLVED KNOWN ARE SUBTRACTED, NEVER DROPPED.
    spread = subtract_pro_rata({"a": 10, "b": 30}, 20)
    assert sum(spread.values()) == 20, spread
    assert spread["b"] > spread["a"], spread
    assert sum(subtract_pro_rata({"a": 3, "b": 1}, 0).values()) == 0

    # AN OVERFILLED BUCKET IS RED. This is the whole point of the counters: a filler
    # that writes more records than its quota cannot merge.
    # PAST ITS QUOTA MEANS PAST THE PRE-RULING ONE TOO (T-1463): a `filled` that sits
    # between the re-cut quota and the quota the filler was actually given is the re-cut
    # reaching work already done, and that is REFUSED by name rather than faulted. Only a
    # figure above both is a filler that bypassed the book, so the fixture clears both.
    doc = build(data, [], occ)
    # A BUCKET IN A BAND THE TRADE RE-CUT CANNOT REACH, which the book's first row no longer
    # is. T-1459 made a 10_19 bucket's quota a function of what is DRAWN against it — the
    # re-cut is bounded by each bucket's undrawn remainder — so a fixture that varies the
    # ledger there varies the quota it is testing against, and measures nothing. A band the
    # record reaches nobody working in weighs 0.0 and neither side of the move touches it;
    # that is the stable ground the overfill fixtures stand on. Picked off the factors
    # rather than typed, so it follows the reading if a later source opens or shuts a band.
    shut_bands = [band for band, _, _, _ in AGE_BANDS
                  if doc["trade_re_cut"]["participation"]["factors"][band] == 0.0]
    assert shut_bands, "every band is in the trade cut; the overfill fixtures have no fixed bucket"
    first = next(b for b in doc["bucket_families"][0]["buckets"]
                 if b["axes"].get("age_band") in shut_bands and (b["to_reconstruct"] or 0) > 0)
    BYPASS = 10_000
    fires("a bucket filled past its quota",
          lambda: build(data, [{"ticket": "T-1347", "bucket": first["key"],
                                "records": (first["to_reconstruct"] or 0) + BYPASS}], occ))
    fires("a fill that names no ticket",
          lambda: build(data, [{"bucket": first["key"], "records": 1}], occ))

    # TWO TICKETS FILLING ONE BUCKET ARE ADDED, NOT OVERWRITTEN (T-1174). Both
    # `modelled_families` and `women_and_children` fill the family buckets, and while this
    # was a dict comprehension the second ticket's row simply replaced the first's — so a
    # bucket could be filled to twice its quota and the overfill gate above would never
    # have fired, because it was reading the same replaced number.
    halves = [{"ticket": "T-1171", "bucket": first["key"], "records": 1},
              {"ticket": "T-1174", "bucket": first["key"], "records": 2}]
    # LOOKED UP BY KEY, NOT BY POSITION: the book's first row moves whenever the cut does,
    # and T-1459 moved it.
    def row(doc_, key):
        return next(b for b in doc_["bucket_families"][0]["buckets"] if b["key"] == key)

    assert row(build(data, halves, occ), first["key"])["filled"] == 3
    fires("two tickets overfilling one bucket between them",
          lambda: build(data, [{"ticket": "T-1171", "bucket": first["key"],
                                "records": first["to_reconstruct"] or 0},
                               {"ticket": "T-1174", "bucket": first["key"],
                                "records": BYPASS}], occ))

    # AND THE TWO REDS ARE NOT ONE RED. A `filled` inside the gap between the re-cut quota
    # and the pre-ruling one builds cleanly and is NAMED in `recut_refusals`; it does not
    # fault, and the bucket is held at what was drawn rather than clamped to the re-cut.
    inside = build(data, [{"ticket": "T-1174", "bucket": first["key"],
                           "records": (first["to_reconstruct"] or 0) + 1}], occ)
    named = [r for r in inside["recut_refusals"] if r["bucket"] == first["key"]]
    assert len(named) == 1 and named[0]["held_at"] == (first["to_reconstruct"] or 0) + 1, named
    bucket = row(inside, first["key"])
    assert bucket["to_reconstruct"] == bucket["filled"] and bucket["recut_refused"], bucket

    # THE PRESENCE RULINGS AND THE BOOK'S `known` MUST AGREE (T-1463). This is the guard
    # that would have caught the over-order: the book read the rulings for a year, reported
    # what summing them in would give, and cut every quota as though they said nothing.
    stale = copy.deepcopy(data)
    stale["presence_rulings"]["counts"]["persons_by_residence_grade"]["inferred"] += 7
    fires("the book's known and T-1386's presence rulings disagree",
          lambda: build(stale, [], occ))
    gone = copy.deepcopy(data)
    gone["presence_rulings"]["rulings"] = []
    fires("a presence rulings file with no rulings in it", lambda: build(gone, [], occ))

    # AND THE TOWN THE FILLED BOOK CONVERGES TO MUST SIT INSIDE THE MODEL'S OWN RANGE.
    # A ledger with one record in it leaves the whole quota outstanding on top of a town
    # that already holds the people it was drawn for, which is the shape of the bug.
    fires("a book whose remainder would order a town outside the model's range",
          lambda: converges_inside_the_model(
              build(data, [{"ticket": "T-1171", "bucket": first["key"], "records": 1}], occ)))
    # AND THE SHIPPED BOOK SAYS THE COMMITTED TOWN OUT LOUD. Read off the committed
    # book rather than typed in here: the figure moves whenever a stage draws or
    # retires a person, and a number written into a self-test goes stale silently —
    # 2,267 was typed here on 2026-09-20 and was wrong four people later (T-1369).
    committed_standing = json.loads(BOOK.read_text(encoding="utf-8"))["totals"]["persons_standing"]
    assert (f"{committed_standing:,} standing"
            in converges_inside_the_model(build(data, _fills_on_disk(), occ)))

    # THE RE-CUT IS REFUSED, NOT CLAMPED, WHERE IT REACHES WORK ALREADY DRAWN (T-1463).
    # Every refusal names its bucket, what the re-cut would have ordered and what was
    # drawn, and holds the order at the drawn figure. The owner's ruling of 2026-09-20.
    shipped = build(data, _fills_on_disk(), occ)
    for r in shipped["recut_refusals"]:
        assert r["already_drawn"] == r["held_at"] > r["the_re_cut_would_have_ordered"], r
        assert r["already_drawn"] <= r["quota_it_was_drawn_against"], r
        b = next(x for fam in shipped["bucket_families"] for x in fam["buckets"]
                 if x["key"] == r["bucket"])
        assert b["to_reconstruct"] == b["filled"] and b["recut_refused"], b
    assert shipped["totals"]["persons_known"] == shipped["population_ruled_in"]["persons_known_now"]

    # ---- THE TRADE RE-CUT (T-1459) -------------------------------------------------
    # The ruling has two halves and both are guarded: the cut changes, and nothing already
    # drawn moves. These fire on the SHIPPED book, so they are a statement about what is
    # committed and not about a fixture.
    rc = shipped["trade_re_cut"]

    # 1. THE AGE FLOOR IS READ, NOT ASSUMED. A band the sources record nobody working in
    #    weighs nothing and orders nobody; a band they do reach weighs what the record
    #    measures, and never more than an adult.
    pt = rc["participation"]
    for band, low, _, _ in AGE_BANDS:
        if low >= ADULT_FROM:
            assert pt["factors"][band] == 1.0, band
        elif pt["workers"].get(band):
            assert 0 < pt["factors"][band] <= 1.0, (band, pt["factors"][band])
        else:
            assert pt["factors"][band] == 0.0, band
    assert pt["workers_total"] == sum(pt["workers"].values()) > 0
    assert rc["bands_reopened"], "the record reaches under twenty and the book shut every band"

    # 2. THE RE-CUT NEVER LOWERS A BUCKET BELOW ITS `filled` — the guard the ticket asks
    #    for by name. Asserted over every person bucket of the shipped book, not just the
    #    ones that moved, because the failure this forbids is a quota going under a stage
    #    that already spent.
    for b in shipped["bucket_families"][0]["buckets"]:
        if b["to_reconstruct"] is None:
            continue
        assert b["to_reconstruct"] >= b["filled"], b

    # 3. THE TOWN DOES NOT CHANGE SIZE. A re-cut moves slots between a cell's `trade` and
    #    `none` buckets; it never mints or retires a person, so what goes in equals what
    #    comes out and the book's employed total is the model's, before and after.
    assert sum(rc["into"].values()) == sum(rc["out_of"].values()) == rc["what_moved"]
    employed = sum(b["target"] for b in shipped["bucket_families"][0]["buckets"]
                   if b["axes"].get("trade") == "trade")
    assert employed == shipped["bucket_families"][0]["summary"]["employed_target"], employed

    # 4. EVERY CAP THAT BOUND THE RE-CUT IS NAMED, with both numbers and the drawn figure
    #    that stood in its way. A refusal that paid in full is not a refusal.
    for r in rc["refusals"]:
        assert r["the_remainder_could_pay"] < r["the_re_cut_wanted"], r
        assert r["direction"] in ("into", "out of") and r["cell"] and r["owning_ticket"], r
    assert rc["what_moved"] <= min(rc["the_re_cut_wanted"],
                                   rc["the_younger_bands_had_undrawn"],
                                   rc["the_adult_cells_had_undrawn"]), rc

    # 5. AND A RECORD THAT REACHED NOBODY UNDER TWENTY SHUTS THE BAND AGAIN. The floor is
    #    a reading, so withdrawing the reading has to withdraw the order — otherwise the
    #    band would stand open on a sentence somebody typed once.
    layer = known_layer(data["residents"], data["presence_rulings"])
    opened = person_buckets(data["model"], data["composition"], data["inventory"], layer, pt)
    reopened = [b for b in opened["buckets"] if b["axes"].get("trade") == "trade"
                and b["axes"]["age_band"] in rc["bands_reopened"]]
    assert reopened and sum(b["recut_wants"] for b in reopened) == rc["the_re_cut_wanted"] > 0, \
        "the record reaches under twenty and the cut asked for nothing there"
    shut = copy.deepcopy(pt)
    shut["factors"] = {k: (1.0 if v == 1.0 else 0.0) for k, v in shut["factors"].items()}
    reverted = person_buckets(data["model"], data["composition"], data["inventory"], layer, shut)
    assert not [b for b in reverted["buckets"]
                if b["axes"].get("trade") == "trade" and b["axes"]["age_band"] == "10_19"], \
        "the reopened band survived the record that opened it being withdrawn"

    # 5b. AND A CELL SPENT IN BY A STAGE THAT IS NOT REMAINDER-STABLE IS REFUSED WHOLE, not
    #     shaved. This is the clause that stopped the re-cut on 2026-09-21: a stage reading a
    #     bucket's whole `to_reconstruct` re-deals its ENTIRE draw when one slot of it moves.
    #     T-1503 gave the lodging stage a committed basis instead, so its cells are shaved to
    #     their remainder like any unspent one — and what this asserts now is the narrower,
    #     true thing: every cell the re-cut touched is spent in only by stages on
    #     `REMAINDER_STABLE_STAGES`, and no bucket of one was shaved below its own counter.
    fills_on_disk = _fills_on_disk()
    drew_in_cell: dict[str, set] = {}
    for fill in fills_on_disk:
        if int(fill.get("records") or 0):
            cell = fill["bucket"].rsplit("/", 1)[0]
            drew_in_cell.setdefault(cell, set()).add(fill.get("ticket") or "")
    by_key = {b["key"]: b for b in shipped["bucket_families"][0]["buckets"]}
    for cell, n in list(rc["into"].items()) + list(rc["out_of"].items()):
        loose = sorted(t for t in drew_in_cell.get(cell, ())
                       if t not in REMAINDER_STABLE_STAGES)
        assert not loose, (cell, n, loose)
        for kind in ("trade", "none"):
            bucket = by_key.get("%s/%s" % (cell, kind))
            if bucket is not None:
                assert (bucket.get("to_reconstruct") or 0) >= (bucket.get("filled") or 0), bucket
    #     And a cell the block says is HELD names the stage holding it, which is the half the
    #     old clause could not say — it knew only that something, somewhere, had been drawn.
    for key, held_by in rc["held_by_an_unaudited_stage"].items():
        assert held_by and all(t not in REMAINDER_STABLE_STAGES for t in held_by), (key, held_by)
        assert key.rsplit("/", 1)[0] not in rc["into"], key
    assert rc["why_it_stopped"] and rc["what_would_unlock_it"]
    assert rc["remainder_stable_stages"] == REMAINDER_STABLE_STAGES

    # 6. AND THE SEVEN STAGES THAT HAVE SPENT ARE NAMED WITH WHAT THEY SPENT, which is the
    #    list the re-cut is audited against.
    assert shipped["spent_by"] and all(row["records"] > 0 and row["buckets"]
                                       for row in shipped["spent_by"]), shipped["spent_by"]
    assert sum(row["records"] for row in shipped["spent_by"]) == sum(
        int(f.get("records") or 0) for f in _fills_on_disk())

    # A SHORTFALL THE EVIDENCE EXPLAINS IS NOT A QUOTA (T-1428). The December census
    # prints seven schools; the register holds five at the scene date and names two more
    # whose opening was announced in August. The bucket must order NOUGHT, and must say
    # that it is nought because the sources account for the difference — not reach it by
    # luck and not order two inventions against it.
    school = next(b for b in doc["bucket_families"][2]["buckets"]
                  if b["key"] == "businesses/school")
    assert school["known"] == 5 and school["census_count"] == 7, school
    assert school["records_opening_after_scene_date"] == 2, school
    assert school["to_reconstruct"] == 0, school
    assert "opening announced" in school["basis"].lower(), school["basis"]

    # THE FORT'S TEN PRINCIPAL ROOFS ARE ON BOTH SIDES OR NEITHER (T-1439). The model's
    # institutional high end counts them; the programme schedules them under
    # `fort_principal`. Reading `institutional_public` alone on the programme side charged
    # the roof schedule ten roofs it already had, and that false delta stood in the book
    # and on the page for a year. The two files agree, and the row must say 19 against 19.
    deltas = {d["id"]: d for d in doc["programme_deltas"]}
    inst = deltas["institutional_and_public"]
    assert inst["programme_groups"] == ["institutional_public", "fort_principal"], inst
    assert inst["model"] == inst["programme"] == 19 and inst["delta"] == 0, inst

    # AND A ROW THAT CANNOT DISAGREE IS NOT REPORTED AS AN AGREEMENT. Both institutional
    # ends and the boarding-house figure are read off `district_group_matrix` by
    # model_town_1835.build_lodging, so setting them beside that matrix is the matrix
    # agreeing with itself. `inns_and_taverns` names the same file and goes PAST it — 11
    # from the business layer against the matrix's 10 — so it is a real comparison, and
    # the flag has to tell the two apart rather than blanket every lodging row.
    #
    # THE DELTA WAS 5 UNTIL T-1471 (2026-09-21) AND IS 1, because the business layer's
    # figure stopped counting one house twice. Four of its fifteen scene-date tavern
    # records were re-settings of two standing advertisements — E. Wentworth's Flag Creek
    # notice and the Eagle Tavern's chair-and-harness notice — and trade_class_rulings.json
    # now folds them, so fifteen records read as eleven houses. The flag below is
    # unchanged and is the point of the assertion: a smaller real disagreement is still a
    # real disagreement, and it must not start reading as the matrix agreeing with itself.
    assert inst["restates_the_programme"] is True, inst
    assert deltas["boarding_houses"]["restates_the_programme"] is True, deltas["boarding_houses"]
    assert deltas["inns_and_taverns"]["restates_the_programme"] is False, deltas["inns_and_taverns"]
    assert deltas["inns_and_taverns"]["delta"] == 1, deltas["inns_and_taverns"]
    for d in doc["programme_deltas"]:
        assert d["statement"].startswith("NOT A CHECK:") == d["restates_the_programme"], d
    p_sum, h_sum = doc["bucket_families"][0]["summary"], doc["bucket_families"][1]["summary"]
    unsourced = copy.deepcopy(data)
    figure(unsourced["model"], "lodging_and_institutions",
           "institutional_and_public_roofs")["derived_from"] = []
    fires("a delta row whose NOT A CHECK sentence no longer matches its flag",
          lambda: programme_deltas(unsourced["model"], unsourced["inventory"],
                                   unsourced["programme"], p_sum, h_sum))

    # A PROGRAMME SIDE THAT NAMES A GROUP THE MATRIX DOES NOT CARRY IS A FAULT, not a
    # silent nought — which is the shape a typo in a group name would take.
    bent = copy.deepcopy(data)
    bent["inventory"]["district_group_matrix"].pop("fort_principal")
    fires("a delta row summing a matrix group that does not exist",
          lambda: programme_deltas(bent["model"], bent["inventory"], bent["programme"],
                                   p_sum, h_sum))

    # A CLASS THE CROSSWALK DECLINES TO COMPARE ORDERS NOTHING (T-1442). The December
    # census prints five churches and the register holds four, but T-0988 rules a church a
    # structure and not a trade and the crosswalk row is `compared: false`, so the two
    # figures are not the sides of one subtraction. The book used to cut a quota of one
    # from them and the Businesses family could therefore never read full. It must carry
    # the row with both figures and order NOUGHT, and say which ruling stopped it.
    church = next(b for b in doc["bucket_families"][2]["buckets"]
                  if b["key"] == "businesses/church")
    assert church["census_count"] == 5 and church["known"] == 4, church
    assert church["compared_by_the_crosswalk"] is False, church
    assert church["to_reconstruct"] == 0, church
    assert "does not COMPARE" in church["basis"], church["basis"]

    # …AND A ROW THE CROSSWALK RULES COMPARABLE STILL ORDERS ITS SHORTFALL, so the guard
    # above cannot be read as a blanket amnesty for every business row.
    compared_shortfall = next(b for b in doc["bucket_families"][2]["buckets"]
                              if b["key"] == "businesses/druggist")
    assert compared_shortfall["to_reconstruct"] == 2, compared_shortfall

    # …AND A BRACKET ON AN UNCOMPARED CLASS IS A CONTRADICTION, not a quota in men that
    # slips past the guard because it is cut on the other branch.
    unruled = copy.deepcopy(data)
    for row in unruled["crosswalk"]["classes"]:
        if row["class"] == "lawyer":
            row["compared"] = False
    fires("a bracket is a comparison, so those two rulings contradict",
          lambda: business_buckets(unruled["crosswalk"], unruled["register"],
                                   unruled["trade_spend"], unruled["model"]))

    # AND THE BOOK REFUSES A CROSSWALK THAT CANNOT TELL IT WHICH IS WHICH, rather than
    # reading a missing key as a zero and quietly ordering the invention again.
    stale = copy.deepcopy(data)
    for row in stale["crosswalk"]["classes"]:
        row.pop("records_opening_after_scene_date", None)
    fires("does not say how many of its houses opened after the scene date",
          lambda: business_buckets(stale["crosswalk"], stale["register"],
                                   stale["trade_spend"], stale["model"]))

    # A CLASS COUNTED IN MEN CANNOT TAKE A CORRECTION MEASURED IN PREMISES.
    mixed = copy.deepcopy(data)
    for row in mixed["crosswalk"]["classes"]:
        if row["class"] == "lawyer":
            row["records_opening_after_scene_date"] = 1
    fires("cannot be subtracted from a count of men",
          lambda: business_buckets(mixed["crosswalk"], mixed["register"],
                                   mixed["trade_spend"], mixed["model"]))

    # EVERY BUCKET NAMES A TICKET, and every ticket named is in the reconstruction bands.
    for family in doc["bucket_families"]:
        for b in family["buckets"]:
            owners = [b["owning_ticket"]] if b.get("owning_ticket") else b.get("owning_tickets", [])
            for owner in owners:
                assert owner.startswith("T-1"), (b["key"], owner)

    # THE PERSON TOTALS CLOSE ON THE MODEL'S OWN NUMBER.
    persons = doc["bucket_families"][0]["buckets"]
    apportioned = sum(b["target"] for b in persons if b["target"] is not None)
    assert apportioned == doc["totals"]["persons_target"], (apportioned, doc["totals"])

    # NOBODY IS NAMED. The book is cohorts and counts; a record id in it would be a
    # person this adjudication had no licence to place.
    text = json.dumps(doc["bucket_families"])
    for forbidden in ("hh_", "person_", "business_", "recon_1835_"):
        assert forbidden not in text, f"the order book names a {forbidden} record"

    # AND THE CHILD SHARE THE PYRAMID PRODUCES SITS INSIDE THE MODEL'S BRACKET —
    # the one place the 1840 shape could silently disagree with the 1835 model.
    child = sum(b["target"] for b in persons
                if b["target"] is not None and b["axes"]["age_band"] == "under_10")
    share = child / doc["totals"]["persons_target"]
    band = figure(data["model"], "population", "share_under_ten")
    assert band["low"] <= share <= band["high"], (share, band["low"], band["high"])

    # TWO BUILDS ARE BYTE-IDENTICAL.
    assert json.dumps(build(data, [], occ), sort_keys=True) == json.dumps(doc, sort_keys=True)

    # A WORK ORDER FROM A TICKET NOBODY CAN CLAIM IS A HOLE (T-1420), and the gate
    # fires on the STATE rather than on a list of ids, so it catches the next split
    # as well as the thirteen this sweep found. The three cases that must NOT fire
    # matter as much as the one that must: a blocked ticket is a live owner, a
    # discharged bucket keeps the id of whoever discharged it, and a backward-looking
    # stamp — `fills[].ticket`, `roster_offered.tickets` — is provenance and is never
    # read by this gate at all.
    def named(b):
        return [t for t in [b.get("owning_ticket"), *(b.get("owning_tickets") or []),
                            *(b.get("ground_waits_on") or [])] if t]

    def left(b):
        owed = b.get("to_reconstruct") or b.get("to_build") or b.get("roofs_gated") or 0
        return owed - (b.get("filled") or 0)

    buckets = [b for f in doc["bucket_families"] for b in f["buckets"]]
    owed_by = next(b for b in buckets if left(b) > 0 and b.get("owning_ticket"))
    states = {t: "open" for b in buckets for t in named(b)}
    every_work_order_names_a_live_ticket(doc, states)
    every_work_order_names_a_live_ticket(doc, {**states, owed_by["owning_ticket"]: "blocked-tech"})
    for dead in ("done", "split", "withdrawn"):
        fires(f"a bucket with work left ordered by a {dead} ticket",
              lambda d=dead: every_work_order_names_a_live_ticket(
                  doc, {**states, owed_by["owning_ticket"]: d}))
    fires("a bucket ordered by an id that is not a ticket at all",
          lambda: every_work_order_names_a_live_ticket(
              doc, {k: v for k, v in states.items() if k != owed_by["owning_ticket"]}))
    # A DONE TICKET ON A FULLY DISCHARGED BUCKET IS FINE — that is what this asserts.
    # It has to pick a ticket that owns NO bucket with work left, not merely A bucket
    # with none: the gate is asked per TICKET, so marking one done fails the moment it
    # also owns a live bucket, and the fixture would then be measuring the wrong thing.
    # This fixture builds with NO fills, so which quotas sit at nought is a property of
    # the re-cut rather than of the town, and T-1459 moved it — the 10-19 bands became a
    # function of what is drawn against them. Choosing by ticket rather than by bucket
    # is what makes the case survive that.
    live_owners = {t for b in buckets if left(b) > 0 for t in named(b)}
    discharged = next(b for b in buckets if b.get("owning_ticket") and left(b) <= 0
                      and b["owning_ticket"] not in live_owners)
    every_work_order_names_a_live_ticket(doc, {**states, discharged["owning_ticket"]: "done"})
    assert "T-1166" not in {t for b in buckets for t in named(b)}, \
        "the book's own authoring ticket is provenance and must not be a work order"

    print(f"build_order_book_1835 self-tests pass ({fired} guards fired, "
          f"{sum(len(f['buckets']) for f in doc['bucket_families'])} buckets, "
          f"child share {share:.3f} inside {band['low']}-{band['high']}, no record named)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    try:
        if args.build:
            return cmd_build()
        if args.check:
            return cmd_check()
        if args.self_test:
            return cmd_self_test()
    except Fault as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
