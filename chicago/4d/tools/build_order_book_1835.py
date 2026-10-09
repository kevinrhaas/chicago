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
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# THE WALK OVER A SPLIT IS ONE DEFINITION AND NOT THREE (T-1581) — see that module.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ticket_liveness  # noqa: E402
from town_year import touches_year  # noqa: E402  (T-1732)
BOOK = ROOT / "data" / "reconstruction" / "1835_reconstruction_order_book.json"
REPORT = ROOT / "docs" / "RESEARCH" / "1835_reconstruction_order_book.md"

MODEL = ROOT / "data" / "reconstruction" / "1835_town_model.json"
PROFILE = ROOT / "data" / "reconstruction" / "1835_population_profile.json"
ROSTER = ROOT / "data" / "reconstruction" / "1835_borderline_roster.json"
PROGRAMME = ROOT / "data" / "reconstruction" / "1835_665_roof_programme.json"
INVENTORY = ROOT / "data" / "reconstruction" / "1835_building_inventory.json"
RECONCILIATION = ROOT / "data" / "reconstruction" / "1835_existing_roof_reconciliation.json"
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

# THE FAMILY ROWS' OWNER, swept off T-1171 on 2026-10-03 (T-2019). T-1171 split into
# T-2019 (measure the re-housing the town's own women allow), T-2020 (make those moves)
# and T-2021 (rule on the married houses no woman in the town can be wife to). A bucket
# naming a SPLIT ticket orders work nobody can claim (T-1237), so the rows T-1171 owned
# move to the piece that owns what is left of its order once the moves are made: T-2021
# decides whether the book orders more women or the heads stand alone, and the men and
# houses still owed here are the same question. The modelled-families STAGE keeps its
# own ticket, T-1171, on its fills; that is who drew, not who is owed.
# SWEPT AGAIN ON T-2021's CLOSE (2026-10-03). The ruling ordered more women — exactly what
# the houses it admitted drew — and did NOT discharge the men and the family and store
# households these rows still order: those are a reconciliation against the head records
# awaiting a household, which is T-2043's. A row that still owes work may not name a
# ticket that is finished.
# SWEPT AGAIN ON T-2043's SPLIT (2026-10-08, ported by T-2186 so every branch's gate
# stops reading a split owner). T-2043 split into T-2187 (rule on the adult men the book
# still orders into family houses) and T-2188 (seat the family and store households), so
# the person rows go to the first and the household rows to the second.
# The two halves were never one question. The MEN are a counting artifact, measured and ruled by
# T-2187 (`ADULT_MEN_OWNER`, `adult_men_ruling` below): the known people are credited to the
# cells PRO RATA, so the town's named heads — men, nearly every one — were counted partly
# as women and children, and the adult-male family cells read short of men the cards hold
# several hundred over. The HOUSEHOLDS are real work: 392 family and store houses the model
# wants, and 1,244 present head records with no reading about a dwelling to form them
# around. That is T-2188's.
# SWEPT AGAIN ON T-2188's SPLIT (2026-10-08, ported by T-2190 so its gate stops reading a
# split owner): the family dwellings go to T-2193, which counts the ones the town already
# forms around held heads, and the store residences to T-2194.
# RULED ON T-2194 (2026-10-09, `store_residence_ruling` below): the store rows ordered more
# households than the town has store roofs, and the order above one household a roof is
# discharged. What is left is a keeper for each store roof that stands empty, and T-2236
# seats one from the store-trade heads the town already holds.
FAMILY_OWNER = "T-2187"
FAMILY_HOUSEHOLD_OWNER = "T-2193"
STORE_RULING_TICKET = "T-2194"
STORE_RESIDENCE_OWNER = "T-2236"
ADULT_MEN_OWNER = FAMILY_OWNER
# …and the ruling T-2021 made, whose fills are an order of their own (`family_ruling_orders`).
FAMILY_RULING_TICKET = "T-2021"

# Which ticket fills a person bucket. Read top-down; the first rule that matches
# owns the cell. Written here rather than in prose so the book can be audited
# against the queue.
PERSON_TICKET_RULES = (
    ("fort division", lambda a: a["division"] == "fort", "T-1176"),
    ("the transient cohort", lambda a: a["household_type"] == "transient", "T-1178"),
    # THE BED BUCKETS, cut three ways by T-1500 on 2026-09-24.
    #
    # T-1420's sweep (2026-09-21) found these cells ordered by T-1175, which had split,
    # and every piece of that tree that fills a bed had closed. It repointed them at
    # T-1500 as ONE placeholder owner and said so: "Who fills WHICH bed is a modelling
    # decision and is not taken here." T-1500 is that decision, and the answer is that
    # the remainder is not one job. It is three, and the boarders stage
    # (`tools/seat_lodgers_1835.py`) had already drawn the lines, in the three refusals
    # it wrote against itself — so the cut below is quoted from the town's own work
    # rather than picked, which is why it is a rule on the axes and not a table of cells.
    #
    # The stage's own summary of what it left: "the rest wait on the 37 unbuilt boarding
    # houses, the crews and the works gang (T-1372), the trades this stage does not deal,
    # and the children who are keepers' families rather than boarders."
    #
    #   refusal 2, NO TRADE IS DEALT      -> T-1532, the working lodgers
    #   refusal 3, NO CHILDREN            -> T-1533, the minted keepers' own families
    #                                        (shipped; its remainder was T-1536, now
    #                                        shipped too, and is T-2023's)
    #   the 37 unbuilt boarding houses    -> T-1534, the boarders proper, bed-bound
    #
    # On the book as T-1500 read it, the 278 still owed divide 61 / 86 / 131 across the
    # three, over 30 / 12 / 24 of the 66 cells. The order of the rules matters once: a
    # 10-19-year-old AT A TRADE is an apprentice boarding where they work, so the trade
    # rule takes those six cells before the under-twenty rule sees them. There is no
    # `under_10` trade cell — children carry no trade — so nothing else turns on it.
    #
    # T-1407 (the crews and the harbour-works gang) stays the one live descendant of
    # T-1175 and is NOT given cells here: a crew sleeps aboard rather than in a division's
    # house, and the book has no axis that separates them. T-1534 carries that refusal.
    # SWEPT OFF T-1532 ONTO T-2023 ON 2026-10-04 (T-2076). T-1532 dealt the working
    # lodgers and closed with every cell at its order. Then T-2076 read the second printing
    # of eleven letter-list names onto their cards, three arrival bounds moved from 1835 to
    # 1834, the town model's 1 July floor rose by five and `persons/female/30_39/south/
    # lodging/trade` ordered three more beds than it held. A cell with work left may not
    # name a finished ticket (T-1420), and the bed-bound remainder of the lodging cells is
    # T-2023's — "seat the lodging remainder as lodging roofs rise" — exactly as the
    # children's rule below already names it, by the same rule: a bucket names who does
    # what is LEFT. seat_lodgers_1835.py keeps its fills under T-1532's quota.
    ("a working lodger, a bed rather than a household",
     lambda a: a["household_type"] == "lodging" and a["trade"] == "trade", "T-2023"),
    # T-1536 succeeds T-1533 here, on the day T-1533 shipped. T-1533 drew the children of
    # the six keepers the boarders stage MINTED — ten of the eighty-six — and the other
    # seventy-six are not reachable from that stage at all: they are the children of
    # DOCUMENTED keepers, whose families are T-1171's draw and T-1179's convergence, and
    # the children of the 37 boarding houses the lodging model schedules and nobody has
    # built, where there is no keeper to be kin to. A bucket must name who does what is
    # LEFT, so it names the successor rather than the ticket whose fills stand in it.
    # T-1536 CLOSED on 2026-10-03: its youths' top-up (seat_lodgers_1835.py) boarded the
    # eleven `10_19` the book still ordered, which leaves the band at its order. What is
    # left is nine under-tens in the South and the West, and a child is drawn as a keeper's
    # kin or not at all — so they come with the keepers of the lodging roofs not yet
    # raised, through T-1533's draw, which is T-2023's roof-by-roof remainder.
    ("a child of the house, a bed rather than a household",
     lambda a: a["household_type"] == "lodging" and a["age_band"] in ("under_10", "10_19"),
     "T-2023"),
    # T-1534 split into T-1537 and T-1538 on 2026-09-24 and the cells follow the split,
    # not the parent: a bucket whose owning ticket is a SPLIT parent names nobody who can
    # act on it (T-1237), and this gate is what says so. T-1538 is the beds — "fill the
    # 131 adult beds… as T-1209 raises the 36 unbuilt lodging roofs" — so the person cells
    # are its. The HOUSEHOLD rows below are T-1538's too, and T-1537 was the wrong owner
    # for them for the reason this gate exists: T-1537 is a RECONCILIATION, and it closes
    # the moment it lands. What it reconciles is the COUNTER — the fifteen lodging
    # households the boarders stage had already built and filed no fill for — and once
    # those fifteen are counted, 49 are still ordered and every one of them waits on a
    # roof. A row that still owes work may not name a ticket that is finished.
    # T-1538 CLOSED on 2026-10-03 with a frozen top-up (seat_lodgers_1835.py) that seated
    # the one bed the book still ordered; what is left waits on a roof and is T-2023's.
    ("a boarder, a bed rather than a household",
     lambda a: a["household_type"] == "lodging", "T-2023"),
    # T-1347 repointed this off its split parent. T-1173 was the epic; it split into
    # T-1346 (read the 1839 trade table) and T-1347 (draw the heads), and a bucket whose
    # owning ticket is a SPLIT parent names nobody who can act on it (T-1237).
    # SWEPT ON T-2178 (2026-10-08). T-1347 drew the trade heads and is done; its cells sat
    # at their order until six St Mary's infants, carded as heads and counted in them,
    # were ruled not yet born on the day and left one owing. Every cell that reaches this
    # rule is a FAMILY cell (the fort, transient and lodging rows are taken above), so
    # what is left in it is the family reconciliation, which is FAMILY_OWNER's.
    # Repointed on T-2043's split: what reaches the two rules below is an adult man in a
    # family house, at a trade or not (women and the young are taken by T-1174's rule
    # first), so it is T-2187's ruling on the adult men, which discharges what the cards
    # already hold. A row that owes again once it has closed is a re-ruling, and the
    # live-ticket gate says so.
    ("an adult at a trade", lambda a: a["trade"] == "trade", ADULT_MEN_OWNER),
    ("a woman or a person under twenty", lambda a: a["sex"] == "female" or a["age_band"] in ("under_10", "10_19"), "T-1174"),
    ("otherwise: a family drawn from the household model", lambda a: True, ADULT_MEN_OWNER),
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
    ("family_dwelling", "ordinary_dwellings", FAMILY_HOUSEHOLD_OWNER),
    ("store_residence", "stores_mixed_use", STORE_RESIDENCE_OWNER),
    # Swept with the person rule above (T-1420 -> T-1500 -> T-1534 -> T-1537 on
    # 2026-09-24, T-1534 having split the same day). Of
    # T-1500's three successors T-1534 is the one that holds a lodging HOUSEHOLD: the
    # other two fill beds inside a house somebody else's ticket keeps.
    #
    # These two rows were DISCHARGED when the sweep moved them — every boarding house and
    # inn the model wanted was standing, so the gate did not reach them and they moved
    # only so that one household type would not answer to two tickets depending on which
    # family you read. T-1476 ended that on 2026-09-24: separating a household RECORD
    # from a household in the town model took the count from 124 to 563 and reopened 64
    # lodging houses (boarding_house 51, inn_tavern 13). So the rows carry work again, the
    # gate does reach them, and T-1534 — the roofs-and-beds piece — is the right owner for
    # them for the same reason it owns the boarders: a house has to stand before it holds
    # anybody.
    #
    # AND T-1537 SETTLED WHAT THE 64 ACTUALLY WERE. T-1534's acceptance asked for these
    # two counts to be reconciled before either half of its order was minted, and the
    # answer was that the boarders stage had built FIFTEEN of these households into
    # `data/residents/lodgers/` and filed a fill for not one of them — so the book ordered
    # all 64 a second time and the progress bars on "Reconstructing the town" read nought
    # for a band that had run. The stage files them now; these rows carry the 49 that are
    # left, and all 49 wait on a roof. So the owner is T-1538, not T-1537: every one of
    # the town's 144 ordinary night beds is slept in and all 16 built lodging places hold a
    # household, and T-1537 is a counter that closes when it lands.
    # T-1538 seated the one bed the book still ordered and left the rest to T-2023
    # (2026-10-03): the West's adults with no free bed and the houses with no roof yet.
    ("boarding_house", "larger_boarding_houses", "T-2023"),
    ("inn_tavern", "inns_taverns", "T-2023"),
    # T-1188 split (T-1410, T-1411); the institutional HOUSEHOLDS are the people who
    # lived at a church, a parsonage or a school. T-1410's three establishments — post
    # office, land office, county rooms — house nobody. T-1411 split in turn (T-1421,
    # T-1422) and both children closed WITHOUT writing a household: they wrote
    # establishments and the hands about them, which is a different thing from the people
    # who slept there.
    #
    # It went to T-1189 next, "the live ticket that puts real persons at these
    # establishments", and T-1189 has since split too — T-1432 and T-1433 done, T-1434
    # split onto T-1448 and T-1449, and not one of that tree writes a HOUSEHOLD; they
    # staff businesses. The row was quiet through all of it because the quota read 0
    # owed, and T-1476's ruling is what made it speak: with the house count taken
    # against houses rather than records, these three cells order 11 households and
    # order them from a ticket nobody can claim. T-1531 is filed for them.
    ("institutional", "institutional_public", "T-1531"),
    ("garrison", "fort_principal", "T-1176"),
)

# Which build ticket owns a structure group in a division. The queue's 5C band is
# cut by district and street, so this maps the programme's own group x district
# matrix onto the ten build tickets.
STRUCTURE_TICKETS = {
    # T-1203 WAS SPLIT on 2026-09-28 (T-1707, T-1708, T-1709, T-1710) and this row moved
    # with it, for the reason the T-1200 block below states at length: a bucket whose
    # `owning_ticket` names a ticket in state `split` orders work nobody can claim, and the
    # gate says so — it went red on this cell within the hour, reading "structures/
    # ordinary_dwellings/south has 67 left and is ordered by T-1203, which is split".
    #
    # THE CELL GOES TO T-1708, and the measurement is which children raise an ORDINARY
    # DWELLING. The cell reads 176 target, 109 standing, 67 to build. Of the four children
    # T-1707 raises no roof at all — it carries the Original Town's seven south columns from
    # their terrain clip at N -400 to Madison Street, which is street control on ground
    # T-0219 already modelled, and its own title says it is what
    # `south_plat_beyond_committed_control`'s 104 roofs still WAIT on. T-1709 is the South
    # Branch noxious-trade band: work bays, cooperage and tannery yards, stables and sheds —
    # trade fabric, not dwellings. That leaves two, and T-1708 is the first: "the cottages and
    # yard buildings the South balance deals to the plat's last tier, on the blocks the street
    # carry emitted" is this cell in as many words. T-1710 carries the rest of the district's
    # dwellings — the country seats' reconstructed neighbours and the Fort Dearborn Addition —
    # and closes the district's books, so the row moves to T-1710 when T-1708 closes with the
    # cell still owing, the same rule T-1681 was named under one line down.
    #
    # SWEPT ONTO T-1751 ON 2026-09-29, AND NOT ONTO T-1710, BECAUSE T-1710'S SUBTREE IS
    # EXHAUSTED. T-1708 raised eleven roofs on `blk_washington_wells` and closes with this cell
    # still owing 59, so the rule above asks for the row to move — but the successor it names
    # went to `split` while this tier was being dealt, and both of the children it split into
    # (T-1712, T-1713) are `done`. So there is no live descendant of T-1203 left to hold the
    # cell, which is what `ticket_liveness.py` says in as many words when this close is
    # attempted: "T-1203 loses its last live descendant when T-1708 close(s)". A bucket whose
    # owning ticket cannot be claimed orders work nobody can do, which is the exact red this
    # comment block was written about, and the gate's own instruction is to repoint it at live
    # work in the pull request that closes the ticket.
    #
    # T-1751 IS THAT WORK, AND IT IS THE NEXT BLOCK OF THIS VERY TIER — `blk_washington_frank-
    # lin`, which the platted deal holds seven slots on, an ordinary-dwelling build in the
    # South Division in as many words. It is in `review` with its own pull request open, and
    # review is LIVE by the liveness walk's own definition (only `done`, `withdrawn` and
    # `split` are cold), so it can hold the cell today; an earlier draft of this sweep argued
    # that a ticket in review could not, and that was simply wrong about the relation.
    #
    # WHAT IS TRUE IS THAT THE ROW WILL MOVE AGAIN, and that is the chain working rather than
    # failing. 59 roofs is far more than one block, T-1751 will close with the cell still
    # owing, and the row will then follow the remainder to whatever block ticket is live —
    # exactly as the north cell three entries below has now been swept three times in two
    # days, T-1206 -> T-1742 -> T-1748 -> T-1754. The rule is the same every time: the cell
    # goes to the live ticket that raises the dwellings that are LEFT.
    #
    # AND SWEPT ONTO T-1735 ON 2026-09-29, BY THAT RULE AND ON THE SAME TIER. T-1751 raised
    # thirteen roofs on `blk_washington_franklin` and closes with this cell still owing 54, so
    # the row moves to the live ticket that raises the dwellings LEFT. `blk_washington_lasalle`
    # is the next block of this very tier — the platted deal holds seven slots on it and T-1735
    # is "the seven cottages and yard buildings the platted deal holds on blk_washington_lasalle"
    # in as many words — and it is in `review` with its own pull request open, which the
    # liveness walk counts as live. It will move again when that block closes with the cell
    # still owing; 54 roofs is far more than one block, and the chain is the point.
    #
    # AND SWEPT ONTO T-1758 ON 2026-09-29, ON THE FOURTH LAP OF THIS SAME BRANCH, BECAUSE
    # T-1735 HAS SINCE MERGED. The sweep above was sound when it was made — T-1735 was in
    # `review` with PR #181 open, and review is live — but that pull request landed on `dev`
    # and the ticket went `done`, so the cell was left ordered by a ticket nobody can claim
    # and every re-derivation on this branch failed on that row: "structures/ordinary_dwellings
    # /south has 55 left and is ordered by T-1735, which is done". The rule does not change,
    # only the row it lands on: the cell goes to the live ticket that raises the dwellings
    # that are LEFT. `blk_washington_market` is the next block of this very tier and T-1758 is
    # "the seven cottages and yard buildings the platted deal holds on blk_washington_market"
    # in as many words, `open` and claimable today. THIS IS THE SWEEP BEING A CHAIN RATHER
    # THAN A FIX: 55 roofs is far more than one block, so the cell will move again when
    # T-1758 closes with it still owing, exactly as the north cell four entries below has
    # moved five times in three days.
    #
    # AND SWEPT ONTO T-2130 ON 2026-10-05 (T-2131), BECAUSE T-1758 WAS SPLIT AT 06:09Z — into
    # T-2129 (the Market block's five houses) and T-2130 (the Dearborn and Clark blocks' slots)
    # — and a row naming a split ticket orders work nobody can claim. That took dev's own gate
    # red on this one row, after the split's own branch had gated green, and every open pull
    # request with it.
    #
    # AND ON TO T-1755 WITH T-2130's OWN PR, because T-2130 raises the Dearborn and Clark blocks
    # to their lot ceilings and closes with the cell still owing — a row naming a done ticket
    # orders work nobody can claim, exactly as a split one does. T-1755 is "the South
    # Division's remaining ordinary dwellings ... after the plat's last tier" in as many words,
    # `open` and claimable, so the row stops moving with every block of this tier and waits
    # where the remainder is owned.
    #
    # DEV MOVED IT TO T-2144 FIRST, the moment the split landed, so the row would name a
    # claimable child; T-2144 is this PR and goes `done` when it merges, so the row moves
    # one piece on, to T-2145, in the same commit.
    #
    # AND ON TO T-2145 WITH T-2144's OWN PR (2026-10-05). The owner answered T-1755's
    # question (b) — cross Madison onto the School Section's Madison-Monroe tier — and the
    # run that took it split it four ways: T-2144 joins the tier to the grid and the
    # schedule, and T-2145/T-2146/T-2147 build its Clark, Wells and Market blocks. The row
    # waits on the first build piece, the one the tier's dwellings are dealt to next.
    #
    # AND ON TO T-2146 WITH T-2145's OWN PR (2026-10-06). T-2145 builds the Clark blocks
    # (118, 119) and goes `done` when it merges, so the row moves one piece on to the Wells
    # blocks (94, 95), the next build piece still open.
    #
    # AND ON TO T-2147 WITH T-2146's OWN PR (2026-10-06). T-2146 builds the Wells blocks
    # and goes `done` when it merges, so the row moves to the Market block (81), the last
    # build piece of the tier still live.
    #
    # AND ON TO T-2176 WITH T-2147's OWN PR (2026-10-08). T-2147 built block 81's six dwellings
    # and goes `done` when it merges; the seating's fixpoint over them leaves South dwellings
    # still ordered (a D4 slot on block 81's lot 1, a D5 on block 95's), and T-2176 owns them.
    #
    # AND ON TO T-2182 WITH T-2176's OWN PR (2026-10-08). T-2176 built the two dwellings the
    # seating asked for (block 81's lot 1 and block 95's, a D5 and a D6 once T-2174 had
    # re-dealt the schedule) and no `slot` request is left on the plat; the schedule still
    # deals the South six dwellings nobody asks for, on the South Water blocks (one of them
    # gated), and T-2182 owns them.
    #
    # AND ON TO T-2239 WITH T-2238's OWN PR (2026-10-09). T-2182 was split: T-2238 built the
    # wedge's D5 the seating asked for (blk_south_water_market's lot 7, after T-2195 cut the
    # wedge), and no `slot` request is left on the plat; the five the schedule still deals
    # (a D2 and a D4 on blk_south_water_wells, a D2, D4 and D5 gated) are T-2239's.
    ("south", "ordinary_dwellings"): "T-2239",
    # T-1201 WAS SPLIT on 2026-09-27 (T-1680, T-1681, T-1682, T-1683) and its three rows
    # moved with it, for the reason the T-1200 block below states at length: a bucket
    # whose `owning_ticket` names a ticket in state `split` orders work nobody can claim,
    # and the gate says so. Of the four children only two raise anything — T-1681 turns
    # the Lake frontage of the Dearborn and Clark blocks from cottages into stores, and
    # T-1682 does the same for the Franklin, La Salle, Wells, Market and Clinton blocks
    # and takes the mechanics' shops onto their State and Dearborn faces. T-1680 is a
    # variant ticket against roofs already standing (W1's forge stack) and raises none,
    # exactly as T-1639's own children did not, so it owns no cell.
    #
    # STORES GO TO T-1694, AND THE ROW'S OWN HISTORY IS THE ARGUMENT. It has now been
    # swept three times in one afternoon, each sweep sound when it was made and overtaken
    # by the next close: T-1680 sent it to T-1682 ("the W1-W4 shops are its second half in
    # as many words"); T-1682 measured that, could not spend it, and sent it to T-1681
    # ("the first of the two live raisers, and the row moves to T-1682 when it closes with
    # the cell still owing") — but T-1682 merged the same afternoon, so the successor it
    # promised was already `done`; T-1683 was then the last live child of T-1201, and it
    # merged too (#138) while this piece was being re-cut on dev. T-1681 closes with the
    # pull request this row moves in, so ALL FOUR CHILDREN OF T-1201 ARE NOW CLOSED and
    # the split parent has no live descendant either. There is no ticket left in that
    # family to name, and the harm of naming one anyway is the route
    # `ticket_liveness.py`'s own header describes: the gate reads `review`, which is live,
    # and the `done` that takes dev red lands afterwards, when the settle workflow runs.
    #
    # SO THE CELL GETS A TICKET OF ITS OWN, filed the way T-1684 was filed for the
    # workshops row one line below — by the run that found the hole, carrying the
    # measurement rather than an opinion. T-1694: the cell reads 41 standing of 42 with
    # one owed, and every block of the Lake-Randolph tier reads `at_capacity`, so the last
    # south store has no ground in the platted core to stand on. That is a question about
    # where it goes, not a build somebody can just take, and it is not this piece's to
    # answer: re-familying a fourth roof to close the cell would be inventing a trade,
    # which is the refusal `blk_lake_dearborn` is already recorded under.
    # WORKSHOPS GO TO T-1684, and the sentence this replaces is why the row could not stay
    # on T-1682. T-1680's sweep (above, an hour earlier) sent it to T-1682 because "the
    # W1-W4 shops on State and Dearborn are its second half in as many words" — sound at
    # the time, and T-1682 then MEASURED that second half and could not spend it. The whole
    # `fronts` vocabulary the 22-block recipe uses is `lake`, `randolph`, `south_water`,
    # `washington` — the four LONG faces — and not one slot in this programme's history has
    # been dealt onto a cross-street face, so a W2-W4 shop on State or Dearborn needs a
    # short-face placement term the recipe does not have. Every block on those faces reads
    # `at_capacity` or deals no W head (`blk_south_water_dearborn`'s 4 of headroom is dealt
    # A3, D6, D7, H1), and the only W-family roof this town holds anywhere is
    # `recon_1835_north_w5_040`, in the North Division: neither a slot to deal nor a shop to
    # re-family. T-1684 carries that measurement and owns the question, and T-1682 closes
    # with the pull request this row moved in — so leaving the row on it would put a `done`
    # ticket in a DEAD_TICKET_STATES cell and take dev red the moment the settle workflow
    # ran, which is the exact harm the sweep above exists to prevent.
    ("south", "stores_mixed_use"): "T-1694",
    # T-1209 WAS SPLIT on 2026-10-01 (T-1775..T-1780) and the boarding houses' three cells
    # moved to T-1779, the child that RAISES the houses still owed; T-1777 rules where they
    # may stand first and T-1778 their form, and neither raises a roof the book counts.
    # T-1779 WAS SPLIT in turn on 2026-10-01 (T-1809, T-1810). All three cells move to
    # T-1810, the piece that raises every house the book still orders past the two
    # Washington-tier seats; T-1809 raises one South house and closes first, so a cell left
    # on it would order work from a done ticket the moment it settles (swept by T-1802).
    # T-1810 WAS SPLIT in turn on 2026-10-02 (T-1950..T-1953). T-1950 raises the plan's last
    # H3 on blk_washington_clark and closes first, so no cell stays on it; the South's cell
    # moves to T-1951 (the plan's H3s on the Dearborn and Market blocks, whose free lots are
    # all requested), the West's to T-1953 (on T-1414's ground) and the North's to T-1952.
    # T-1951 raised the three H3s the plan held on those two blocks when it was claimed
    # (two on blk_washington_market, one on blk_washington_dearborn) and closes on them, so
    # the cell moves to T-1957, which owns the five the book still orders: the one H3 the
    # schedule re-apportions to blk_washington_market once those three stand, the one on
    # the gated blk_south_water_market, and three the plan holds no roof for at all.
    # T-1957 SPLIT on 2026-10-08 (ported by T-2190 so its gate stops reading a split
    # owner): T-2195 cuts the Market wedge into lots and T-2196 raises the South's two owed
    # boarding houses on them, so the cell moves to T-2196.
    ("south", "larger_boarding_houses"): "T-2196",
    # The taverns' cell is FULL — 5 of 5, nothing owed — so this names the child that
    # would answer for it if it ever owed again: T-1683 closes the district's books and
    # states its headroom, which is where a cell that reopens would be found.
    ("south", "inns_taverns"): "T-1683",
    # T-1684 WAS SPLIT on 2026-10-05 (T-2133, T-2134). T-2133 gives the generator the
    # cross-street term and deals no roof, so the cell moves to T-2134, the piece that deals
    # the W2-W4 shops onto a Dearborn face with it.
    ("south", "workshops"): "T-2134",
    # T-1200 WAS SPLIT on 2026-09-26 (T-1638, T-1639, T-1640, T-1641) and this row moved
    # with it, for the reason BUSINESS_TICKETS states below: a bucket whose `owning_ticket`
    # names a ticket in state `split` orders work nobody can claim. Of the four children the
    # freight band is T-1640's in as many words — "the freight sheds and landings behind
    # South Water, on the river-bank band the south-bank ground rule allows" — while T-1638
    # writes keepers onto seated roofs, T-1639 raises the street line's stores and
    # warehouses, and T-1641 closes the district's books.
    #
    # DECIDED 2026-09-27 (T-1640), because two runs had resolved this row differently
    # within an hour of the split and the next sweep would have flipped it a third time:
    # it stays a SINGLE ticket and does not become the `owning_tickets` tuple PR #95
    # wrote. The tuple's reasoning was that T-1639 owes the F1-F3 warehouses on the
    # street line while T-1640 owes the sheds behind them, and the inventory holds both
    # halves in one cell it does not cut. That reasoning is sound and the conclusion no
    # longer follows: T-1639 is in state `split` — its own children (T-1660, T-1662,
    # T-1663, T-1665, T-1667) are door and bay tickets against roofs ALREADY STANDING,
    # and not one of them raises a roof. So there is no live run owing a roof out of this
    # cell but T-1640, and naming a split ticket beside it orders work nobody can claim,
    # which is the fault this block's first paragraph exists to prevent. When the cell is
    # cut for real — the street-line warehouses apart from the sheds behind them — it is
    # the INVENTORY that should cut it, not a tuple in the order book.
    #
    # MOVED TO T-1672 on 2026-09-27, in the pull request that closed T-1640. T-1640 built
    # `south_bank_shed_dearborn_e2`, which took the last position the south-bank ground
    # rule admits at the generators' 0.30 m relief clause — `takes_more` now reads 0 there
    # — and the cell still owes three roofs. So this row cannot stay on T-1640 without
    # ordering work from a ticket nobody can claim, which is the fault the paragraph above
    # was written for; T-1672 owns the question the three remaining roofs actually pose,
    # which is WHERE they stand now that the bank is full.
    #
    # AND T-1672 CUT IT, IN THE INVENTORY, WHICH IS WHAT THE PARAGRAPH ABOVE ASKED FOR. The
    # cell is banded — see the note before `structure_buckets` — so it no longer orders as
    # one bucket and each band names its own owner: the river bank is CLOSED at what stands
    # and the street line carries the whole order, on T-1673. This entry is what a banded
    # cell falls back to if its bands are ever taken out of the inventory, so it names the
    # half that would still owe. It is not read while the bands stand.
    #
    # AND ON TO T-2175 WHEN T-1673 WAS SPLIT (2026-10-08, T-2174 + T-2175). T-2174 raises the
    # street line's F2 and goes `done` when it merges, so the order moves to the piece that
    # carries the rest of the line, as the band in the inventory does.
    ("south", "warehouses_freight"): "T-2175",
    # T-1202 WAS SPLIT on 2026-09-27 and closed with T-1688, the Randolph tier's books, so
    # this row named a ticket nobody can claim (T-1705). It orders nothing — the five
    # civic roofs the matrix sets all stand, and T-1202 raised none of them, so its id here
    # was never the provenance of a fill that the gate's own rule would have kept. A sixth
    # civic roof in the South would be the programme re-budgeted, and the ticket that owns
    # the programme's remainders is T-1983, "the programme reconciled", the same owner the
    # South's stable and outbuilding rows below were moved to for the same reason. T-1983
    # was split on 2026-10-08 and its roof re-budget went to T-2156, so this row follows.
    # T-2156 WAS SPLIT the same day (T-2165, T-2166), and T-2166 in turn (T-2167, T-2168);
    # the re-budget went to T-2168.
    # T-2168 was split as well (T-2169, T-2170); the re-budget question is T-2170's.
    ("south", "institutional_public"): "T-2170",
    # T-1212 WAS SPLIT on 2026-10-02 (T-1958..T-1961): the stables and the privies were
    # T-1960's, "wells, privies and stables by household", in all three divisions.
    # MOVED TO T-1215, THEN T-1967, by the pull request that closed T-1960. T-1960 dealt its privies and
    # stables to the YARD LAYER (data/yard/town_yard_outbuildings.json, drawn at load) —
    # a privy behind every dwelling lot the plat reaches — and raised no roof, so the roofs
    # these cells still count are not owed by any yard deal. T-1215, which converges the
    # programme and owns its remainders, is the ticket that answered for them; it was split the
    # same day (T-1964..T-1970) and T-1967, "the programme reconciled", answered next.
    # T-1967 shipped the completion report and the City card's completion row and handed
    # "the programme reconciled" — these roofs with it — to T-1983, which answers now.
    # Naming the closed T-1960 or the split T-1215 would order work nobody can claim.
    # T-1983 WAS SPLIT on 2026-10-08 (T-2154..T-2156) and its roofs went to T-2156, "build
    # or re-budget the barns_stables and small_outbuildings roofs" — the piece that answers
    # for these cells, here and in the West and North rows below.
    # T-2156 WAS SPLIT on 2026-10-08 too: T-2165 dealt the yard roofs the schedule places
    # on lots that can hold them (the South's barn and smokehouse, the North's stable), and
    # T-2166 (split again the same day into T-2167, the West's four on blk_washington_clinton,
    # and T-2168) took the rest. The South's last barn is T-2147's block 81 while that PR is
    # open, so these rows name T-2168, the live owner of what is left, and not T-2165, which
    # closes with nothing of the South's still owed to it. T-2168 was then split too
    # (T-2169, the West's last three on blk_washington_clinton; T-2170, the North's five
    # barns and the re-budget question), so the South's rows name T-2147 itself — the
    # build that carries the South's one owed barn (an A2 on blk_school_section_tier_81).
    # T-2147 was re-dealt over T-2146 (2026-10-08) and the schedule no longer gives block 81
    # a yard roof, so the South's one owed barn moves to T-2176 with its owed dwellings.
    # T-2176 built the South's last owed barn (an A2 behind the D3 on blk_south_water_wells'
    # lot 7) and the row reads 0 owed; the pair follows the dwellings to T-2182 so a row that
    # re-opens when the schedule re-apportions still names a live ticket. T-2182 was split
    # (2026-10-09) and the pair follows the dwellings on to T-2239.
    ("south", "barns_stables"): "T-2239",
    ("south", "small_outbuildings"): "T-2239",
    # T-1208 WAS SPLIT on 2026-10-01 (T-1781..T-1785): T-1783 opened the outer platted West
    # blocks at a West density and built blk_west_randolph_des_plaines's three cottages. What
    # is left in this cell — blk_west_lake_canal's four dealt cottages and the district
    # balance beyond committed control — moves to T-1784, the sibling that owns that ground,
    # and T-1784 was itself split the same hour, so to its live child T-1794, which raises the
    # West's owed dwellings on the extended ground. T-1794 then landed (#216) seating farm
    # families in the barn cabins, and T-1773 (#217) took lot 1 of blk_west_lake_canal for its
    # warehouse, so that block's deal is three cottages now, not four. With T-1781..T-1784 all
    # closed, the one live ticket whose acceptance hands T-1208 on "with the West's exact
    # remainder" is T-1774, the West book-closer, and the 19 left here move to it, with the
    # finding written on that ticket (the queue is over its ceiling for a new line).
    # T-1774 WAS SPLIT on 2026-10-01 (T-1826, T-1827). T-1826 closed the books and handed
    # T-1208 on: every ticket in T-1208's chain was split or done, so the 16 left here went
    # to T-1829, filed for exactly this remainder, blk_west_lake_canal's three cottages first.
    # T-1829 built blk_west_lake_canal's three cottages (2026-10-05) and handed the 12 left
    # here, and the West rows below, to T-2132: every lot-ruled West block reads at_capacity.
    # T-2132 cut plat block 44 on its own two printed depths and built its four (2026-10-05),
    # and handed the 8 left here, and the West rows below, to T-2143.
    # T-2143 carried Canal and West Water to Madison, brought plat block 51 onto the layer
    # and built its six (2026-10-05), and handed the 2 left here, and the West rows below,
    # to T-2148: blocks 48-50 on the same tier print 180 ft and wait only on three lines.
    # T-2148 carried Clinton, Jefferson and Des Plaines to Madison and built plat block 50's
    # thirteen roofs (2026-10-06): West dwellings read 75 of 75, and the one freight roof
    # left (block 50's F3, deferred because the block is inland) goes with these rows to
    # T-2150, filed for exactly that.
    ("west", "ordinary_dwellings"): "T-2150",
    # T-1207 WAS SPLIT on 2026-09-29 (T-1760 … T-1764) and these four rows move with it, by
    # the same test the T-1206 and T-1754 sweeps below and above used: WHICH CHILD RAISES THE
    # ROOFS THAT ARE LEFT. The gate went red on three of them within twenty minutes of the
    # split — "structures/stores_mixed_use/west has 2 left and is ordered by T-1207, which is
    # split", and the same for workshops (3) and warehouses_freight (1) — and it blocked every
    # branch open on this repo at the time, not only the one that split the ticket.
    #   stores_mixed_use and workshops -> T-1763, which names their remainder outright: "the
    #     grocery and blacksmith the memo seats on the Canal Street approach". Those two are
    #     the two left in stores and the works trade on that approach.
    #   inns_taverns -> T-1762, "the named Wolf Point taverns' and the Miller house's yards".
    #     This row has 0 left and the gate was therefore silent about it; it is swept anyway,
    #     because a row pointing at a split ticket is wrong whether or not it currently orders
    #     anything, and the next roof drawn against it would find nobody to claim it.
    #   warehouses_freight -> T-1773. T-1764 was itself split on 2026-09-30, and its first
    #     child names this remainder exactly: "The West's last freight roof: a two-storey
    #     warehouse at Lake and West Water facing the forks, built and baked." Keep the live
    #     owner on that child while its sibling T-1774 closes the wider books after the other
    #     Wolf Point pieces land.
    # T-1767 gate repair: T-1763 split; T-1766 explicitly owned these two remainders.
    # T-1766 landed (#206) and both rows still order work, so they move to T-1774,
    # which closes the West's books and hands T-1208 "the West's exact remainder".
    # Both read complete (6 of 6, 8 of 8) when T-1774 split, and move with the remainder to
    # T-1829 so the row names a live ticket.
    ("west", "stores_mixed_use"): "T-2150",
    ("west", "larger_boarding_houses"): "T-1953",
    ("west", "inns_taverns"): "T-1762",
    ("west", "workshops"): "T-2150",
    # T-1764 WAS SPLIT on 2026-10-01: T-1773 is "the West's last freight roof" by name.
    # T-1773 landed (#217) and the row reads 2 of 2; it moves to its sibling T-1774, which
    # names T-1773 in the builds it closes the Wolf Point books behind. When T-1774 split
    # it moved to T-1827: recon_1835_west_046 is one of this row's two F1 roofs, and its H2
    # verdict, which T-1827 carries out, takes a roof out of this row. T-1827 did (046 is
    # an H2 house now), so the row reads 1 of 2 and the freight roof it orders goes with the
    # rest of the West's remainder to T-1829, which already holds stores and workshops.
    ("west", "warehouses_freight"): "T-2150",
    # T-1208 was split the same hour (T-1781): its closer T-1785 answers for this empty cell.
    ("west", "institutional_public"): "T-1785",
    ("west", "barns_stables"): "T-2169",  # T-2156 -> T-2166 -> T-2168 -> T-2169, above
    ("west", "small_outbuildings"): "T-2169",  # T-2156 -> T-2166 -> T-2168 -> T-2169, above
    # T-1206 WAS SPLIT on 2026-09-28 (T-1741, T-1742) and this row moved with it, for the
    # reason the T-1200 block below states at length: a bucket whose `owning_ticket` names a
    # ticket in state `split` orders work nobody can claim, and the gate says so — it went red
    # on this cell within the hour of the split, reading "structures/ordinary_dwellings/north
    # has 35 left and is ordered by T-1206, which is split".
    #
    # THE CELL WENT TO T-1742, and the two children divided on whether either raises a roof.
    # T-1741 reads the lot lines Wright draws inside Kinzie's Addition and cuts the cells he
    # divides to lots — ground control, the rule T-1437 withheld, and it raises nothing.
    # T-1742 was this cell in as many words: it builds the addition and the north tier to their
    # seats on the lots that reading cuts, the labourers' and mechanics' cabins, shanties and
    # small cottages. It is the only live descendant that raises a dwelling, so the 35 are its.
    #
    # AND T-1742 WAS SPLIT IN TURN on 2026-09-29 (T-1747, T-1748), one roof-raising run into
    # the cell, which fired this same gate again inside the hour: "has 34 left and is ordered
    # by T-1742, which is split". The row moves once more, by the same rule and to the same
    # test — which of the children raises the dwellings that are LEFT. T-1747 is one block,
    # blk_indiana_north_wolcott's first roofs on its Indiana and Illinois faces, and says in
    # its own title that the rest of that block's lots stay open. T-1748 is "the rest of
    # Kinzie's Addition and the north tier", the remaining wolcott lots and the Rush-Pine
    # fringe: it is this cell's remainder in as many words, so the 34 are its.
    #
    # AND T-1748 WAS SPLIT on 2026-09-29 (T-1753, T-1754), and the gate fired again: "has 32
    # left and is ordered by T-1748, which is split". Same rule, same test. T-1753 is one
    # block, blk_indiana_north_cass's first roofs, with the rest of that block's lots left
    # open in its own title; T-1754 is "the north tier's remaining roofs", the further wolcott
    # and cass lots and the Rush-Pine fringe — the cell's remainder again, so the 32 are its.
    # (Moved by T-1732's run, which found dev red on this step after the split.)
    #
    # AND T-1754 WAS SPLIT on 2026-09-29 (T-1756, T-1757), and the gate fired a fourth
    # time: "has 32 left and is ordered by T-1754, which is split". Same rule, same test.
    # T-1756 names its own bound — "two more tradesman cottages and their yard buildings
    # on blk_indiana_north_wolcott, the alternation kept and the rest of the block open" —
    # so it is a slice and not the rest. T-1757 is the further cass lots once that block's
    # first roofs land AND the Rush-Pine fringe settled, which is where the order the
    # other child does not take has to land, so the 32 are its.
    # (Moved by T-1257's run, which found this step red on the tree it was merging.)
    # (T-1756's own run, which made the split, reached the same cell by the same test and
    # takes dev's wording here rather than restating it. Its one addition is WHY the split
    # was made, because that is what makes T-1757 the remainder rather than a second slice:
    # T-1754's cass lots wait on T-1753's first roofs, open in PR #189 and not on dev, and
    # its Rush-Pine fringe blocks -- blk_indiana_north_rush, blk_illinois_north_rush and
    # blk_illinois_north_wolcott -- are apportioned `roofs: 0` by the district deal, so the
    # whole of the north's remaining 55 sit on the wolcott and cass blocks.)
    #
    # AND T-1757 IS THE LAST OF THAT LINE, so on 2026-09-29 the row moves for the FIFTH time
    # and for the first time NOT onto a child: `ticket_liveness.py` fired on T-1757's own
    # close -- "has 26 left and is ordered by T-1757, which is done" -- and T-1757 has no
    # sibling left to take it. T-1206, T-1742, T-1748 and T-1754 all lose their last live
    # descendant with it, so the test that served four times ("which child raises the
    # dwellings that are LEFT") has no answer and a NEW ticket would be a second copy of one
    # already open. The 26 go to **T-1746**, which is the live ticket that owns their
    # question in as many words: "the seating pass asks twenty roofs of Kinzie's Addition's
    # two subdivided blocks and the north-division memo will not carry twenty: rule which of
    # the two moves, or carry the surplus off the addition". That is what the 26 ARE. Both
    # subdivided blocks are now at the memo's own ceiling -- four roofs each, every one with
    # open ground on both sides along its own face, and no fifth position on either that does
    # not adjoin a standing roof -- and the three other lotted cells of the Addition are
    # apportioned `roofs: 0`, so there is nowhere on this addition the 26 can stand without
    # either the memo or the seating giving way. Ordering them from T-1746 is the order book
    # saying so: the next run on this cell rules, and does not deal.
    #
    # T-1746 RULED, 2026-10-05: the memo stands and the seating gives way. The 26 stand
    # south of Michigan Street as recipe rows 68-93 of 1835_north_division_initial_parcel.json
    # (`addition_surplus`, L393), so the row reads 0 left. It keeps T-1746's name as the
    # ticket that closed it; a later raise of the North's target is a new ticket.
    ("north", "ordinary_dwellings"): "T-1746",
    ("north", "stores_mixed_use"): "T-1205",
    ("north", "larger_boarding_houses"): "T-1952",
    ("north", "inns_taverns"): "T-1205",
    ("north", "workshops"): "T-1205",
    # T-1205 built the North's three stores, its tavern and its two workshops on the north
    # face of Kinzie Street (L368) and closes with ONE warehouse owed: it belongs on the North
    # Water bank, the one north street graded `light`, and no committed clause seats a
    # warehouse there. T-2022 is filed for exactly that cell.
    ("north", "warehouses_freight"): "T-2022",
    ("north", "institutional_public"): "T-1205",
    ("north", "barns_stables"): "T-2170",  # T-2156 -> T-2166 -> T-2168 -> T-2170, above
    ("north", "small_outbuildings"): "T-2170",  # T-2156 -> T-2166 -> T-2168 -> T-2170, above
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
    # demonstration of its own; T-1418 was the piece that owned these two rows and T-1419
    # the services, which the census enumerates nowhere and which therefore own no bucket.
    #
    # T-1418 CLOSED, AND ONE OF ITS TWO ROWS THEN GREW WORK AGAIN (T-1525, 2026-09-24).
    # Both rows read filled the day it closed, so the id sat here as the record of who
    # filled them and the work-order gate below stayed quiet — which is the rule that gate
    # states in as many words: a bucket with nothing left keeps the id of the ticket that
    # filled it. Then the parish register's 120 residents (T-0841) raised the town model's
    # low end from 2,353 to 2,363, both professions scale with the population they serve,
    # and `physician` went from ordering 9 to ordering 10 against 9 drawn. A row with work
    # left and a `done` ticket on it is exactly the hole T-1420 was filed for, so it is
    # swept — onto T-1529, filed for that tenth physician, because T-1418's whole tree is
    # closed and there was no live successor to sweep it onto.
    #
    # `lawyer` STAYS ON T-1418 and that is deliberate. It orders 1 against 2 drawn, so it
    # has nothing left, and its surplus is a different question from its order: T-1506
    # owns retiring the second reconstructed lawyer. Moving this id would rewrite the
    # record of who filled the row to keep a gate quiet that is not complaining.
    "lawyer": "T-1418",
    "physician": "T-1529",
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
#   T-1193  split; its live frontier was T-1444 (via T-1417 and T-1431), and all
#           three of those say West Division in their own titles. The north half of
#           T-1193 — the field regenerated to N +760 so the North Division's second
#           parcel has ground — closed with T-1416.
#
# T-1444 CLOSED, AND THE WEST ROW IS SWEPT AGAIN (2026-09-26). It was the last live
# descendant of all three of T-1193, T-1417 and T-1431, so its close is the T-1237
# failure above recurring on the row the 2026-09-21 sweep had just repaired: a ground
# row naming a ticket nobody can claim. `ticket_liveness.py` said so on this branch
# rather than on the next one to gate, which is what that step is for.
#   What T-1444 owned ARRIVED. The committed heightfield spans E -705..1,700 m and
# `generate_west_infill.py --check` re-derives all 55 of the recipe's reviewed
# placements with 0 withheld, so the West Division's held slots have ground and are
# standing on it. Ground that has arrived is not a wait — the same reading that
# emptied T-1191's and T-1194's rows above, applied to the row they left behind.
#   T-1414 STAYS, AND IS WHAT THE WEST ROW WAITS ON NOW: street control west of
# Clinton and Canal is still owed and T-1414's own title owes it. The other half of
# the row's `waiting_on` prose — no unified terrain, hydrology or map coverage past
# local E -700 m — has no live owner, and by the rule below that silence is the
# statement this table makes rather than a ticket invented to fill it.
#
# SOUTH AND NORTH ARE EMPTY, AND THAT IS NOT A CLAIM THAT THEIR GROUND IS WHOLE. It
# is the narrower statement this table can make: no LIVE ticket owns what they still
# wait on. The programme's own `waiting_on` prose on each gated row is where the gap
# is recorded and is unchanged by this sweep — the south's last tier waits on the S9
# street control ROADMAP has recorded as owed, and the Michigan Street tract's four
# north rows wait on T-1080, the tract's own unsettled name and platter. Filing an
# owner for either would be inventing one; naming a closed ticket was worse.
# T-1414 CLOSES, AND THE WEST ROW EMPTIES ON THE SAME READING (2026-10-03). What it
# owed is committed: the West Division's tiers (Carroll, Fulton, Des Plaines) and
# Wabansia's seven corridors are in the platted corridor layer (street_control.json §
# west_bank), on top of the lots and alleys T-1455 cut. The two streets it held out are
# a refusal (West Water, cut from the waterline) and a question (Jefferson north of
# Kinzie, filed as T-2018) — and neither is ground the west row's roofs wait on:
# south of Kinzie Jefferson's own corridor is already measured by
# generate_west_infill.py, and north of it the ground is Wabansia's, whose corridors have
# arrived. Ground that has arrived is not a wait, and the rest of the row's
# `waiting_on` prose still has no live owner, so by the rule above it names none.
GROUND_TICKETS = {
    "south": [],
    "west": [],
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
        # THE TWO SEATING PASSES (T-1620). The book has always been able to say how many
        # households the town still owes; it could not say how many of them now have
        # GROUND. T-1613 dealt the committed plat and T-1614 the ground the plat does not
        # draw, and both files are derived and re-derived by their own tools — so the book
        # reads them and adds nothing to them.
        "platted_seats": root / "data" / "reconstruction" / "1835_platted_seats.json",
        "off_plat_seats": root / "data" / "reconstruction" / "1835_off_plat_seats.json",
    }
    out = {}
    for key, path in paths.items():
        if not path.exists():
            raise Fault(f"the order book's input {path.name} is missing — it cannot be built without it")
        out[key] = json.loads(path.read_text(encoding="utf-8"))
    # T-2021's FAMILY RULING, the one input that may be absent: it is written once, by the
    # modelled-families stage, on the first build of a tree that held none. Until then the
    # book orders nothing for it.
    ruling = root / "data" / "reconstruction" / "1835_family_ruling.json"
    out["family_ruling"] = (json.loads(ruling.read_text(encoding="utf-8"))
                            if ruling.exists() else {})
    # …LESS THE CELLS OF THE HOUSES IT ADMITTED THAT A LATER READING WITHDREW (T-2234). The
    # ruling stays frozen. The modelled-families stage names the withdrawn houses and holds
    # the cells they take with them to those houses' own frozen rows. A fixture tree has no
    # ledger, and orders the ruling whole.
    families = root / "data" / "reconstruction" / "1835_modelled_families.json"
    out["family_ruling_withdrawn"] = (
        (json.loads(families.read_text(encoding="utf-8")).get("family_ruling") or {})
        .get("orders_withdrawn") or {}) if families.exists() else {}
    # T-2187's MEASURE, read off the cards the index points at. Only the committed tree
    # carries it; a fixture book has none, and orders as it always did.
    out["adult_men"] = adult_men_on_the_cards(out["residents"], out["presence_rulings"],
                                              root / "data" / "residents")
    return out


def adult_men_on_the_cards(residents: dict, rulings: dict, folder: Path) -> dict:
    """THE MEN THE TOWN ALREADY HOLDS, BY THEIR OWN CARDS (T-2187).

    `known_layer` reads the index, which counts people and not who they are, and
    `person_buckets` spreads them over the cells PRO RATA (rule 2). For most purposes that
    is the honest thing to do with a count. For the adult men it is not, because the named
    town is not a cross-section of the model: two records in three are a letter-list name,
    and that roll is 94.3% male. Spread pro rata, the named heads are credited mostly to
    women's and children's cells, and the adult-male family cells read short of men.

    So this reads each present card — the same test `known_layer` applies: `present`, or
    `uncertain` and ruled in — and counts the NAMED persons (never a reconstructed one,
    whose cell is `filled`) the card itself gives as male and aged twenty or more. The fort
    and the man outside the town are not the civil town the cells apportion. A man whose
    card carries no age is not counted, and the count of them is said."""
    ruled = ruled_present(rulings)
    men, unaged = Counter(), 0
    for hh in residents.get("households", []):
        presence = hh.get("present_on_scene_date")
        if not (presence == "present" or (presence == "uncertain" and hh.get("id") in ruled)):
            continue
        division = hh.get("division")
        if division not in CIVIL_DIVISIONS + ("unplaced",):
            continue
        card = json.loads((folder / hh["file"]).read_text(encoding="utf-8"))
        for person in card.get("persons") or []:
            if person.get("grade") == "reconstructed":
                continue
            basis = person.get("sex_basis")
            sex = (basis.get("value") if isinstance(basis, dict) else basis) or person.get("sex")
            if sex != "male":
                continue
            band = person.get("age_band")
            low = band.get("low") if isinstance(band, dict) else None
            if low is None:
                unaged += 1
            elif int(low) >= ADULT_FROM:
                men[division] += 1
    return {"named_adult_men": sum(men.values()),
            "by_division": {d: men[d] for d in CIVIL_DIVISIONS + ("unplaced",)},
            "named_men_with_no_age_not_counted": unaged}


def adult_men_ruling(buckets: list, measure: dict) -> dict:
    """T-2187: the adult men the family cells order, set against the men the town holds. In place.

    The model's civil town wants a number of men aged twenty and over; the town holds its
    NAMED adult men (read off the cards, `adult_men_on_the_cards`) and the adult men the
    stages DREW (`filled` in the adult-male cells). Whatever the town still lacks of the
    model's figure is all the men it can be owed. The family cells' remainder above that is
    the pro-rata credit's artifact, and it is DISCHARGED here: the cell's order falls to its
    own `filled`, and `discharged_by_the_men_ruling` carries what it was ordering, so the
    discharge is read rather than clamped in silence. Cells are walked in key order, so a
    partial discharge is the same discharge on every build. Nobody is retired, moved or
    drawn; a cell that would owe again when the town stops holding the men reopens on the
    next build."""
    def adult_man(a: dict) -> bool:
        return (a.get("sex") == "male" and a.get("division") in CIVIL_DIVISIONS
                and a.get("household_type") in ("family", "lodging")
                and a.get("age_band") not in ("under_10", "10_19"))
    men = [b for b in buckets if adult_man(b["axes"])]
    target = sum(b["target"] for b in men)
    drawn = sum(b["filled"] for b in men)
    named = measure["named_adult_men"]
    lacking = max(0, target - named - drawn)
    cells = [b for b in sorted(men, key=lambda b: b["key"])
             if b["axes"]["household_type"] == "family"
             and b.get("owning_ticket") == ADULT_MEN_OWNER
             and (b["to_reconstruct"] or 0) > b["filled"]]
    ordered = sum((b["to_reconstruct"] or 0) - b["filled"] for b in cells)
    left = max(0, ordered - lacking)
    discharged = {}
    for b in cells:
        if not left:
            break
        take = min(left, (b["to_reconstruct"] or 0) - b["filled"])
        b["discharged_by_the_men_ruling"] = take
        b["to_reconstruct"] -= take
        discharged[b["key"]] = take
        left -= take
    credited = sum(b.get("known_attested", 0) + b.get("known_inferred", 0) for b in men)
    return {
        "ticket": ADULT_MEN_OWNER,
        "asks": "The family cells order adult men the town does not hold. Does it hold them?",
        "model_civil_adult_men": target,
        "named_adult_men_on_the_cards": named,
        "named_by_division": measure["by_division"],
        "named_men_with_no_age_not_counted": measure["named_men_with_no_age_not_counted"],
        "adult_men_drawn": drawn,
        "the_town_holds": named + drawn,
        "the_pro_rata_credit_gave_these_cells": credited,
        "the_family_cells_ordered": ordered,
        "the_town_still_lacks": lacking,
        "discharged": sum(discharged.values()),
        "discharged_by_cell": discharged,
        "measured": (f"The model's civil town wants {target:,} men aged twenty and over. The "
                     f"present cards name {named:,} and the stages drew {drawn:,}, so the town "
                     f"holds {named + drawn:,}"
                     + (f", {named + drawn - target:,} over the model's figure"
                        if named + drawn >= target else f", {lacking:,} short of it")
                     + f". The pro-rata credit gave these cells {credited:,} of the named; the "
                     f"rest were counted in women's and children's cells. The family cells "
                     f"ordered {ordered:,} more and {sum(discharged.values()):,} are discharged."),
        "what_this_does_not_do": "It moves nobody, retires nobody and draws nobody, and it "
                                 "does not touch the women's or children's cells, whose orders "
                                 "the same credit holds down: that is T-1174's and T-2021's "
                                 "ground, and their own ratio and under-ten gates bound it.",
    }


def store_residence_ruling(households: list, structures: list) -> dict | None:
    """T-2194: the store households the book orders, set against the store roofs. In place.

    `household_buckets` weights each household type on the roofs of its group, and the
    model's households are more than the town's roofs, so every row carries about one and a
    half households a roof. For a dwelling that is the town doubling up, which a model of more
    households than the November count's 398 dwellings already assumes. For a store it is not
    (an inference, stated as one): the weighting's
    own comment says a store-residence holds A household, the keeper's, living in the store,
    and a second family in the same store is not a store residence. So the order above one
    household for each store roof standing in the division is DISCHARGED: the cell's order
    falls by it, and `discharged_by_the_store_ruling` carries what it was ordering. The
    inventory's store roofs all stand (`structures/stores_mixed_use/*`), so the roofs read here
    are the town's and not a schedule's. Nobody is moved, minted or retired, and the
    discharged households are not re-apportioned to the dwelling rows: the model's
    households are a midpoint, and the book says how far it moved from it."""
    roofs = {b["key"].rsplit("/", 1)[1]: int(b.get("standing") or 0) for b in structures
             if b["key"].startswith("structures/stores_mixed_use/")}
    cells = [b for b in sorted(households, key=lambda b: b["key"])
             if b["axes"].get("household_type") == "store_residence"
             and b["axes"].get("division") in CIVIL_DIVISIONS]
    if not cells or not roofs:
        return None
    rows = {}
    for b in cells:
        division = b["axes"]["division"]
        standing = roofs.get(division, 0)
        owed = max(0, (b["to_reconstruct"] or 0) - b["filled"])
        take = min(owed, max(0, b["target"] - standing))
        if take:
            b["discharged_by_the_store_ruling"] = take
            b["to_reconstruct"] -= take
        rows[division] = {"store_roofs_standing": standing,
                          "store_households_ordered": b["target"],
                          "discharged": take,
                          "still_owed": max(0, (b["to_reconstruct"] or 0) - b["filled"])}
    ordered = sum(r["store_households_ordered"] for r in rows.values())
    standing = sum(r["store_roofs_standing"] for r in rows.values())
    discharged = sum(r["discharged"] for r in rows.values())
    still = sum(r["still_owed"] for r in rows.values())
    return {
        "ticket": STORE_RULING_TICKET,
        "asks": "The book orders store households no standing store roof seats a held head "
                "in. Does it over-order them, or is the residents index short?",
        "by_division": rows,
        "store_roofs_standing": standing,
        "store_households_ordered": ordered,
        "discharged": discharged,
        "still_owed": still,
        "still_owed_by": STORE_RESIDENCE_OWNER,
        "measured": (f"The book ordered {ordered:,} store households on the town's {standing:,} "
                     f"civil store roofs, {ordered / standing:.2f} a roof, because the "
                     f"households are apportioned on roof counts. A store residence is one "
                     f"household, the keeper's, so {discharged:,} are discharged and "
                     f"{still:,} are still owed: a keeper for a store roof that stands with "
                     f"nobody in it."),
        "ruling": "BOTH. The book over-orders the store rows, by what it ordered above one "
                  "household a store roof, and that is discharged here. And the index is "
                  "short: the household quota counts houses off the residents index alone, "
                  "so the trade households the reconstruction drew as heads of their own and "
                  "seated on a roof, the readmitted and the underdocumented are outside the "
                  "count. They are people the cards hold present, not an order to fill, and "
                  f"{STORE_RESIDENCE_OWNER} forms the store households still owed from the "
                  "store-trade heads among them rather than from anybody new.",
        "what_this_does_not_do": "It moves, mints and retires nobody, it does not re-apportion "
                                 "the discharged households to the dwelling rows, and it does "
                                 "not count the households outside the index: that count "
                                 "moves every household row and is T-2237's.",
    }


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
        # T-1476's second unit. `households_present` counts RECORDS present in the
        # layer; `houses_present` counts the ones the owner's ruling of 2026-09-21
        # lets stand as a HOUSE, which is what the model's 643 is a count of. The
        # clause that decided each is on its own manifest row (`dwelling_evidence`,
        # derived by rebuild_resident_index.DWELLING_CLAUSES) and is not re-read here.
        "houses_present": 0,
        "houses_present_by_division": {d: 0 for d in DIVISIONS},
        "houses_present_unplaced": 0,
        "records_awaiting_a_household": 0,
        "houses_present_by_clause": {},
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
        clause = hh.get("dwelling_evidence")
        a_house = bool(clause)
        if a_house:
            out["houses_present"] += 1
            out["houses_present_by_clause"][clause] = (
                out["houses_present_by_clause"].get(clause, 0) + 1)
        else:
            out["records_awaiting_a_household"] += 1
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
            if a_house:
                out["houses_present_by_division"][division] += 1
        else:
            out["persons_present_unplaced"] += named
            out["households_present_unplaced"] += 1
            if a_house:
                out["houses_present_unplaced"] += 1
        if hh.get("lives_at"):
            out["households_with_a_lives_at"] += 1
        if hh.get("works_at"):
            out["households_with_a_works_at"] += 1
    out["houses_present_by_clause"] = dict(
        sorted(out["houses_present_by_clause"].items(), key=lambda kv: (-kv[1], kv[0])))
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
    # T-1536 deals the `10_19` lodging youths — the very cells this re-cut pays the
    # working youths out of — against a room read live ONCE and then carried, so a
    # re-cut of the cell's order re-deals nobody it seated. Left off this list, its first
    # fill closed those cells' remainder to the re-cut and the adult cells were shaved
    # under the boarders already standing in them.
    "T-1536": "tools/seat_lodgers_1835.py — the youths' top-up, dealt against the "
              "committed `quota_basis.youth_top_up` in "
              "data/reconstruction/1835_lodgers_seated.json",
    "T-1538": "tools/seat_lodgers_1835.py — the top-up room, read live once and carried in "
              "`quota_basis.top_up` of the same file, so a re-cut moves nobody it seats "
              "(T-1538; named here on 2026-10-03 when T-1205's re-cut first touched a cell "
              "it had drawn in)",
    "T-1532": "tools/seat_lodgers_1835.py — the working lodgers, dealt against the "
              "committed `quota_basis.working_lodgers` in the same file, read once and "
              "carried, so a re-cut re-deals nobody they seat",
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


def institutional_lodging() -> dict:
    """The adjudication of the nine standing institutional roofs (T-1531).

    Hand-authored, because it is nine judgements about nine committed records and not a
    derivation of anything. `tools/reconstruct_institutional_households.py` mints against
    the same file, so the order and the mint cannot disagree about which roofs hold
    anybody.
    """
    path = ROOT / "data" / "reconstruction" / "1835_institutional_lodging.json"
    if not path.exists():
        raise Fault("the institutional lodging adjudication is missing: the household "
                    "quota cannot weight the institutional cells without it")
    doc = json.loads(path.read_text(encoding="utf-8"))
    capable = doc.get("lodging_capable_by_division")
    rows = doc.get("adjudication") or []
    if not isinstance(capable, dict) or not rows:
        raise Fault("the institutional lodging adjudication carries no roofs or no "
                    "lodging_capable_by_division")
    for division, n in sorted(capable.items()):
        counted = sum(1 for r in rows
                      if r.get("holds_a_household") and r.get("division") == division)
        if int(n) != counted:
            raise Fault(f"the institutional adjudication says {n} lodging-capable roof(s) "
                        f"in the {division} division and admits {counted}")
    return doc


def _apportioned_on(htype: str) -> str:
    """What a household bucket's order was apportioned on, in words.

    Written out rather than inlined in the f-string it feeds: a conditional
    spanning several lines inside an f-string expression is Python 3.12 syntax
    (PEP 701) and this repository runs 3.11, where it does not parse at all.
    The wording is unchanged.
    """
    if htype == "institutional":
        return ("institutional roofs whose own record puts a household under them "
                "(1835_institutional_lodging, T-1531)")
    return f"inventory's own {htype} roof count"


def household_buckets(model: dict, inventory: dict, known: dict) -> dict:
    hh_fig = figure(model, "households_and_families", "households_on_1_july_1835")
    total, basis = point_of(hh_fig)
    matrix = inventory.get("district_group_matrix", {})
    if not matrix:
        raise Fault("the building inventory carries no district/group matrix")

    # A CHURCH IS NOT A DWELLING, AND THE WEIGHT NOW SAYS SO (T-1531). Every other row
    # here weights its household type on the roofs of its group, which is right for a
    # group whose roofs are houses: a dwelling holds a household, a store-residence holds
    # a household, an inn holds several. `institutional_public` is the one group where
    # that does not follow. Its nine standing roofs are four places of worship or meeting,
    # two schools and three civic buildings, and weighting them like dwellings ordered
    # TWELVE households onto them — more than one per roof, across a jail, a council house
    # and a light tower. Nobody had asked the roofs the question; T-1476 made the quota
    # speak and the twelve appeared, ordered from a ticket nobody could claim.
    #
    # `1835_institutional_lodging.json` is that question asked once of each of the nine,
    # out of each committed record's own `function`, `occupants` and `research_note`. TWO
    # hold a household — the Watkins house, whose own function is domestic, and the light,
    # whose keepership is recorded at "$350 a year with quarters" — and the other seven
    # are refused there by name, each with the sentence that refuses it. This is NOT a
    # re-cut of the roof row: nine roofs stand and nine are still ordered. What moves is
    # only how many HOUSEHOLDS hang on them.
    capable = institutional_lodging()["lodging_capable_by_division"]
    weights: dict[str, float] = {}
    for htype, group, _ in HOUSEHOLD_BUCKETS:
        row = matrix.get(group)
        if row is None:
            raise Fault(f"the inventory's matrix has no row for {group}")
        for division in CIVIL_DIVISIONS:
            if htype == "institutional":
                roofs = float(capable.get(division) or 0)
            else:
                roofs = float(row.get(division) or 0)
            if roofs > 0:
                weights[f"{htype}/{division}"] = roofs
    targets = largest_remainder(total, weights)

    # THE QUOTA IS AGAINST HOUSES, NOT RECORDS (T-1476, the owner's ruling of
    # 2026-09-21). `households_present_by_division` counts every record the layer
    # holds present, and 1,175 of the 1,393 are a name off a letter list or a
    # parish entry with nothing in them about a dwelling. Subtracting those from a
    # model of 643 HOUSES took the household quota to `0 owed`, which was never
    # true and is the symptom T-1476 was raised about. The count that answers
    # "how many houses does the town still owe" is the one that counts houses.
    resolved = {d: known["houses_present_by_division"][d] for d in CIVIL_DIVISIONS}
    known_by_cell = {k: 0 for k in targets}
    for division in CIVIL_DIVISIONS:
        cells = {k: targets[k] for k in targets if k.endswith("/" + division)}
        for k, v in subtract_pro_rata(cells, resolved[division]).items():
            known_by_cell[k] += v
    for k, v in subtract_pro_rata(targets, known["houses_present_unplaced"]).items():
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
            "basis": (
                f"the model's {total:,} households apportioned on the "
                f"{_apportioned_on(htype)} in the "
                f"{division} division"),
        })
    buckets.append({
        "key": "households/garrison/fort",
        "axes": {"household_type": "garrison", "division": "fort"},
        "target": None,
        "known": known["houses_present_by_division"]["fort"],
        "to_reconstruct": None,
        "filled": 0,
        "owning_ticket": "T-1176",
        "basis": "NOT APPORTIONED — the fort's establishment is read, not modelled (rule 4).",
    })
    return {
        "households_target": total,
        "households_target_basis": basis,
        "households_target_range": [hh_fig["low"], hh_fig["high"]],
        "known_present": known["houses_present"],
        # The other unit, carried beside it so the book never has to be asked which
        # of the two a reader is looking at (T-1476).
        "known_present_records": known["households_present"],
        "known_present_awaiting_a_household": known["records_awaiting_a_household"],
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


# THE BANDS INSIDE ONE CELL (T-1672), AND WHY A CELL EVER NEEDS CUTTING.
#
# The inventory's group x district matrix is the finest cut the programme has, and for
# nine of its ten groups that is enough: one ticket builds a division's cottages, and the
# table above names it. It was not enough for the SOUTH's `warehouses_freight`, and the
# row said so out loud for a day.
#
# That cell holds two kinds of roof standing on two kinds of GROUND. The warehouses stand
# on platted ground — South Water Street's own party lines and the Lake Street blocks —
# and were T-1639's to raise. The freight SHEDS stand behind them on the unplatted river
# margin at the Dearborn reach, and are T-1640's. One cell can name only one owner, so two
# runs disagreed about who owned the whole row: PR #95 wrote an `owning_tickets` tuple over
# it and `dev` kept a single ticket. Then T-1639's tree closed — T-1647, T-1648, T-1659,
# T-1662 and T-1663 all `done` — with the cell's order still unspent, and the remainder
# silted onto the SHED ticket, whose ground `tools/measure_south_bank_ground.py` reports
# at capacity and whose frontage T-0134 refuses in writing. The row ordered roofs from a
# ticket that cannot honestly raise one, and no gate could see it because the two halves
# were one number.
#
# So the cell is cut where its two kinds of ground part — in the inventory, which is the
# document that authored the cell, rather than in a tuple here — and each half is owed
# apart. A band is one of exactly two things and says which in its own record:
#
#   * a CLOSED band names its members by id prefix and owes NOTHING. Its target IS what
#     stands in it, so it cannot order a roof at all; what closed it is written in the
#     band as `closed_by`, so re-opening it means re-reading those refusals rather than
#     editing a number. It is exempt from the work-order gate for that gate's own ordinary
#     reason: a bucket with nothing left keeps the id of the ticket that filled it.
#   * the REMAINDER band takes the rest of the cell — every roof the closed bands do not
#     hold, and the WHOLE of the cell's order. It is the half that still owes, so it is
#     the half whose ticket `every_work_order_names_a_live_ticket` holds to being live.
#
# NOTHING ABOUT THE PROGRAMME MOVES. A band's target, standing and order are read from the
# same two documents the cell's are, the closed bands are counted off the standing records
# themselves, and the bands must add back up to the cell on all three figures —
# `bands_add_back_up_to_their_cell` below, which is the whole guard against a cut being
# used as a quiet re-budget. A band is a finer ADDRESS for work already counted.


def cell_bands(inventory: dict, group: str, division: str) -> list[dict] | None:
    """The bands the inventory cuts one group x district cell into, or None."""
    banded = ((inventory.get("district_group_bands") or {}).get(group) or {}).get(division)
    if not banded:
        return None
    bands = list(banded.get("bands") or ())
    if len(bands) < 2:
        raise Fault(f"the inventory cuts {group}/{division} into {len(bands)} band(s): a cut "
                    "makes two halves or it is not a cut")
    return bands


def band_members_are_in_their_cell(held: list[str], group: str, division: str, band: str,
                                   reconciliation: dict) -> None:
    """A closed band's members belong to the cell it cuts, or its prefix has gone stale.

    Read through `reconcile_665.group_of` and the existing-roof reconciliation the
    668-roof programme itself reads, for the reason `measure_group_district_rows` states
    about its own count: this gate and the ledger it audits must never be counting
    different towns.
    """
    import reconcile_665 as ledger  # noqa: PLC0415
    rows = {r.get("structure_id"): r for r in reconciliation.get("records", [])}
    for sid in held:
        row = rows.get(sid)
        if row is None:
            raise Fault(f"band {band} of {group}/{division} holds {sid}, which the existing-roof "
                        "reconciliation does not place: a band cannot name a roof the programme "
                        "has not classified")
        family = row.get("likely_family") or ""
        if not family:
            raise Fault(f"band {band} of {group}/{division} holds {sid}, which the reconciliation "
                        "gives no family")
        was = (row.get("district"), ledger.group_of(family))
        if was != (division, group):
            raise Fault(f"band {band} of {group}/{division} holds {sid}, which the reconciliation "
                        f"places in {was[0]}/{was[1]}")


def bands_add_back_up_to_their_cell(bands: list[dict], cell: dict,
                                    group: str, division: str) -> None:
    """A band is a finer address for work already counted, never a re-budget."""
    for field in ("target", "standing", "to_build"):
        got = sum(b[field] for b in bands)
        if got != cell[field]:
            raise Fault(f"the bands of {group}/{division} carry {got} against the cell's "
                        f"{cell[field]} for `{field}`: a cut re-addresses the cell's work, it "
                        "does not re-budget it")
    for b in bands:
        if b["target"] != b["standing"] + b["to_build"]:
            raise Fault(f"band {b['key']} reads a target of {b['target']} against "
                        f"{b['standing']} standing and {b['to_build']} to build")


def banded_buckets(cell: dict, bands: list[dict], group: str, division: str,
                   standing_ids: frozenset[str], reconciliation: dict) -> list[dict]:
    """One bucket per band of a cell the inventory cuts. See the note above."""
    out: list[dict | None] = []
    remainder: tuple[int, dict] | None = None
    taken = 0
    for band in bands:
        for field in ("id", "title", "owning_ticket", "why"):
            if not band.get(field):
                raise Fault(f"a band of {group}/{division} carries no `{field}`")
        prefix = band.get("member_id_prefix")
        if not prefix:
            if band.get("members") != "the rest of the cell":
                raise Fault(f"band {band['id']} of {group}/{division} names its members neither "
                            "by id prefix nor as the rest of the cell")
            if remainder is not None:
                raise Fault(f"the inventory cuts {group}/{division} with two remainder bands: "
                            "the cell's order would be ordered twice")
            remainder = (len(out), band)
            out.append(None)
            continue
        if band.get("owes") != "nothing":
            raise Fault(f"band {band['id']} of {group}/{division} names its members by id prefix "
                        "and still claims an order: only a closed band is named that way")
        if not band.get("closed_by"):
            raise Fault(f"band {band['id']} of {group}/{division} owes nothing and says nothing "
                        "about what closed it")
        held = sorted(i for i in standing_ids if i.startswith(prefix))
        if not held:
            raise Fault(f"band {band['id']} of {group}/{division} matches no standing record on "
                        f"`{prefix}`: the prefix or the band has gone stale")
        band_members_are_in_their_cell(held, group, division, band["id"], reconciliation)
        taken += len(held)
        out.append({**cell, "key": f"{cell['key']}/{band['id']}",
                    "axes": {**cell["axes"], "band": band["id"]},
                    "target": len(held), "standing": len(held), "to_build": 0,
                    "to_retire_or_redeal": 0,
                    "owning_ticket": band["owning_ticket"],
                    "band_title": band["title"], "band_members": held,
                    "band_closed_by": list(band["closed_by"]),
                    "basis": f"a CLOSED band: {len(held)} roof(s) stand in it, it orders none, "
                             f"and {', '.join(band['closed_by'])} closed it — {band['why']}"})
    if remainder is None:
        raise Fault(f"the inventory cuts {group}/{division} into closed bands only: the cell's "
                    "order has nowhere to go")
    if taken > cell["standing"]:
        raise Fault(f"the closed bands of {group}/{division} hold {taken} roofs against the "
                    f"cell's {cell['standing']} standing")
    at, band = remainder
    out[at] = {**cell, "key": f"{cell['key']}/{band['id']}",
               "axes": {**cell["axes"], "band": band["id"]},
               "target": cell["target"] - taken, "standing": cell["standing"] - taken,
               "to_build": cell["to_build"],
               "to_retire_or_redeal": max(0, taken - cell["standing"]),
               "owning_ticket": band["owning_ticket"],
               "band_title": band["title"],
               "basis": f"the REMAINDER band: the cell's {cell['target']} less the "
                        f"{taken} roof(s) its closed band(s) hold, and the whole of the "
                        f"{cell['to_build']} the 668-roof programme still orders here — "
                        f"{band['why']}"}
    made = [b for b in out if b is not None]
    bands_add_back_up_to_their_cell(made, cell, group, division)
    return made


def structure_buckets(inventory: dict, programme: dict, occupancy: dict) -> dict:
    matrix = inventory.get("district_group_matrix", {})
    remaining = programme.get("remaining", {}).get("by_district_group", {})
    standing_total = programme.get("standing", {}).get("structure_records")
    # THE IDS ARE ONLY READ FOR A CELL THE INVENTORY CUTS, and they come off the same walk
    # over `data/structures` that counted the occupancy beside them.
    standing_ids = frozenset(occupancy.get("ids") or ())
    reconciliation: dict = {}
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
            cell = {
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
            }
            bands = cell_bands(inventory, group, division)
            if bands is None:
                buckets.append(cell)
                continue
            if not reconciliation:
                reconciliation = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
            buckets.extend(banded_buckets(cell, bands, group, division,
                                          standing_ids, reconciliation))
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
    ids = []
    for path in sorted(directory.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict) or "id" not in doc:
            continue
        if not touches_year(doc):
            continue    # T-1732: the 1835 town's roofs only; tools/town_year.py
        ids.append(doc["id"])
        if doc.get("occupants"):
            with_occ += 1
        else:
            without += 1
    if with_occ + without == 0:
        raise Fault("data/structures holds no structure records at all")
    # `ids` IS CARRIED, NOT PUBLISHED. It is the walk a banded cell counts its closed
    # bands off (T-1672); the book's own summary takes only the three counts below.
    return {"records": with_occ + without, "with_occupants": with_occ,
            "without_occupants": without, "ids": tuple(ids)}


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
         "statement": (f"NOT A CHECK: the model reads {inns['low']}-{inns['high']} inns and "
                       f"taverns and the programme schedules {inns_programme}. The model's "
                       "ceiling is the highest of the programme, the census and the business "
                       "layer's count at the scene date, and while the layer's count stands "
                       "at or below the programme's the ceiling IS the programme's figure, so "
                       "this row cannot disagree until the layer passes it again (T-1808)."
                       if restates_the_programme(inns, int(inns["high"]), inns_programme) else
                       f"The model reads {inns['low']}-{inns['high']} inns and taverns; the "
                       f"programme schedules {inns_programme}. This one is a real disagreement: "
                       "the model's ceiling is the business layer's count at the scene date, "
                       "not a figure read back off the programme.")},
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


# ------------------------------------------------------ the re-family ledger --
#
# THE OWNER'S RULING OF 2026-09-24 (T-1556, answering T-1530). The re-cut holds 523
# reconstructed people across 48 person buckets that it would no longer order. They
# are not retired: "the surplus heads move into the buckets the re-cut GREW instead
# of being un-written". A move is therefore neither a retirement nor a fresh draw,
# and the book had no third word for it — every count it keeps is a DRAW, written by
# a stage into `fills`, and the only way a bucket's `filled` could ever fall was for
# somebody to be un-written. T-1459's ruling of 2026-09-20 forbids exactly that.
#
# So a move is recorded as a MOVE, ON BOTH ENDS. The person keeps his card, his id,
# his `residence_grade` and every citation on him; what changes is which cell of the
# ladder he is counted in. The bucket he left keeps `drawn_here` — the draw is never
# un-written — and says what left it in `refamilied_out`; the bucket he entered says
# `refamilied_in`, and its order is filled by a person the town already holds rather
# than by a stranger. `filled` is the arithmetic of the three, and it is what every
# quota, refusal and overfill gate below already reads, so they all stay true without
# being taught a new word.
#
# THIS LEDGER MOVES NOBODY. T-1557 builds the accounting and leaves `moves` empty on
# purpose: WHICH heads move is a modelled rule and is T-1558's, and the moves
# themselves are T-1559's. What is built here is the thing both of those need to be
# checkable — every row names the person, the bucket he left, the bucket he entered,
# the order he filled, the rule that chose him and the adoptions travelling with him,
# and `--check` re-derives the whole book, so a hand-written row cannot survive.
REFAMILY_REQUIRED = ("person", "from_bucket", "to_bucket", "ticket", "rule")
# THE RULE A MOVE NAMES IS NOW A RUNG SOMEBODY PUBLISHED (T-1558). T-1557 required every
# row to NAME the rule that chose its head and could not check the name, because no rule
# existed yet; `data/reconstruction/1835_refamily_rule.json` publishes the cost ladder and
# this book refuses a move whose `rule` is not one of its MOVABLE rungs. Build order: the
# book first (the rule model reads it), then the rule, then the book again — the only thing
# that travels back here is the rung ids and the rule's one line, both literals in
# tools/model_refamily_rule.py, so the two cannot chase each other.
REFAMILY_RULE = ROOT / "data" / "reconstruction" / "1835_refamily_rule.json"


def refamily_rule() -> dict | None:
    """The published rule, or None while T-1558's model has not been built yet."""
    if not REFAMILY_RULE.exists():
        return None
    try:
        doc = json.loads(REFAMILY_RULE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Fault(f"the re-family rule is not JSON: {exc}") from exc
    ladder = (doc.get("the_rule") or {}).get("the_cost_ladder") or []
    if not ladder:
        raise Fault("the re-family rule publishes no cost ladder")
    return {
        "ticket": doc.get("ticket"),
        "one_line": (doc.get("the_rule") or {}).get("one_line"),
        "rungs": [r["id"] for r in ladder],
        "movable": [r["id"] for r in ladder if r.get("tier") == "movable"],
        # HOW MANY THE RULE YIELDS, so the ledger below can say whether it is SPENT
        # without a number being typed beside it. T-1558 found 73 where the aggregate
        # had suggested 265, and the two can only be told apart by reading the list.
        "yields": len(doc.get("the_moves_the_rule_yields") or []),
    }


def refamily_shape(moves: list | None, rule: dict | None = None) -> list:
    """The checks a move row can be given before the buckets are cut."""
    rows = list(moves or [])
    seen = set()
    for m in rows:
        if not isinstance(m, dict):
            raise Fault("a row in the re-family ledger is not a record")
        missing = [f for f in REFAMILY_REQUIRED if not m.get(f)]
        if missing:
            raise Fault(f"a re-family move names no {', no '.join(missing)}")
        if m["from_bucket"] == m["to_bucket"]:
            raise Fault(f"the re-family move of {m['person']} leaves and enters "
                        f"{m['from_bucket']}, which is not a move")
        # THE ADOPTIONS TRAVEL WITH HIM OR HE DOES NOT MOVE (T-1556 § 8). An adopted
        # head — one holding an employment seat, named on a business card or on a
        # lodging roll — carries those adoptions across, and the row says so out loud
        # even when the list is empty. A missing field is a row that never considered
        # the question, which is the defect the owner named.
        if not isinstance(m.get("adoptions_carried"), list):
            raise Fault(f"the re-family move of {m['person']} does not say which "
                        f"adoptions travel with him")
        # AND THE RULE IT NAMES IS A RUNG THE MODEL PUBLISHED, on a MOVABLE tier. A move
        # standing on a refused rung is the rule contradicting itself, and a rung nobody
        # published is the un-checkable string T-1557 had to accept.
        if rule and m["rule"] not in rule["movable"]:
            known = ", ".join(rule["movable"]) or "none"
            raise Fault(f"the re-family move of {m['person']} names the rule "
                        f"{m['rule']!r}, which is not a movable rung of "
                        f"{rule['ticket']}'s cost ladder ({known})")
        if m["person"] in seen:
            raise Fault(f"{m['person']} is re-familied twice; a person has one bucket")
        seen.add(m["person"])
    return rows


def refamily_against_buckets(moves: list, buckets: list, drawn: Counter) -> None:
    """The checks that need the cut ladder: both ends real, the same person, room to land."""
    by_key = {b["key"]: b for b in buckets}
    out = Counter()
    for m in moves:
        for end in ("from_bucket", "to_bucket"):
            if m[end] not in by_key:
                raise Fault(f"the re-family move of {m['person']} names {m[end]}, "
                            f"which is not a person bucket in this book")
        src, dst = by_key[m["from_bucket"]], by_key[m["to_bucket"]]
        # A MOVE MAY NOT RE-SEX ANYBODY, NOR RE-AGE HIM. Division, household kind and
        # trade are what the reconstruction chose for him and may be re-chosen; sex and
        # age band are what he IS, and a book that moved them would be inventing a
        # different person under the same id.
        for axis in ("sex", "age_band"):
            if src["axes"].get(axis) != dst["axes"].get(axis):
                raise Fault(
                    f"the re-family move of {m['person']} would change his {axis} from "
                    f"{src['axes'].get(axis)} to {dst['axes'].get(axis)}")
        out[m["from_bucket"]] += 1
        if out[m["from_bucket"]] > drawn.get(m["from_bucket"], 0):
            raise Fault(f"{m['from_bucket']} re-families out more people than were "
                        f"ever drawn there")


# WHERE THE PROGRAMME FINISHES, AND IT IS NOT NOUGHT (T-1597, the owner's answer of
# 2026-09-25). `the_programme` read `settled: still == 0` — the programme finishes when
# nobody is held, and only then — and that is a finish line the rule built to carry the
# ruling cannot reach. T-1558's rule yields every move the axes allow and then stops:
# 129 of them, all spent by T-1563 and T-1564, with 395 people left in 44 buckets the
# rule REFUSES for reasons that are each a rule and not a gap (a house moves whole or not
# at all; a move may not change a person's sex or age band). So the step stood
# permanently unsettled, which by the work-order gate below made it a live order that had
# to name a ticket a run could claim — and each run that took that ticket found the same
# fixpoint and handed it to the next. The owner was asked which of three things the 395
# are, and ruled option (a), verbatim:
#
#   "They remain held, recorded as held, and the programme is settled at its fixpoint
#    rather than at zero — the refusals stand as written and the book says so."
#
# THE FINISH LINE IS THEREFORE THE RULE'S OWN FIXPOINT: settled when the rule yields no
# further move. That is arithmetic exactly as before and still not opinion — what the
# ruling changed is WHICH arithmetic. Nobody is un-written, no confidence moves and no
# refusal is reworded, which are the three things T-1597 forbade; and the residue is not
# silent, because the step carries its count, the buckets that hold it and the refusal
# holding each person, summing to the count rather than standing beside it.
#
# AND IT REOPENS IF THE RULE IS EVER WIDENED, which is option (b) the owner did NOT take.
# A wider rule yields more moves than are spent, this step goes unsettled, and the
# work-order gate asks for a live owner again. That is what keeps this a fixpoint rather
# than a decree: the programme is settled while the rule is spent, and only while.
def the_programme_step(still: int, refusals: list, moves: list, rule: dict | None) -> dict:
    """The programme's own step: settled at the rule's fixpoint, with the residue named."""
    left_to_spend = None if rule is None else max(0, rule["yields"] - len(moves))
    by_refusal: Counter = Counter()
    for row in refusals:
        by_refusal[row.get("cause", "the_re_cut_reached_work_already_drawn")] += row.get(
            "surplus_still_held",
            row["already_drawn"] - row["the_re_cut_would_have_ordered"])
    step = {
        "ticket": "T-1597",
        "settled": left_to_spend == 0,
        "the_finish_line": "the rule's own fixpoint: the programme is settled when "
                           "T-1558's rule yields no further move, and not when nobody is "
                           "held. `settled` is arithmetic either way — what the ruling "
                           "changed is which arithmetic.",
        "the_ruling_that_set_it": "owner, 2026-09-25, answering T-1597 with option (a): "
                                  "\"They remain held, recorded as held, and the "
                                  "programme is settled at its fixpoint rather than at "
                                  "zero — the refusals stand as written and the book says "
                                  "so.\" It is the ruling of 2026-09-24 asked again of "
                                  "the residue that rule could not reach.",
        "moves_the_rule_still_yields": left_to_spend,
        "people_still_held": still,
        "buckets_they_are_held_in": len(refusals),
        "and_what_holds_each_of_them": [{"refusal": cause, "people": n}
                                       for cause, n in sorted(by_refusal.items())],
        "the_rungs_the_rule_refuses_on": ([r for r in rule["rungs"]
                                           if r not in rule["movable"]] if rule else None),
        "what_becomes_of_them": "nothing, and that is the ruling: each keeps the card, the "
                                "id, the seed and the confidence the stage that drew him "
                                "wrote, counted in a cell the sources have since shown the "
                                "town did not need that many of. Every one of the buckets "
                                "goes on naming both its figures (T-1459), "
                                "docs/LIBERTIES.md L268 is the admission, and "
                                "docs/RESEARCH/1835_refamily_programme.md is the "
                                "arithmetic.",
        "what_would_reopen_it": "a wider rule. Option (b) — loosening whole-house, sex or "
                                "age band — was not taken; if it ever is, the rule yields "
                                "more moves than are spent, this step goes unsettled, and "
                                "the work-order gate asks for a live owner again.",
    }
    if rule is None:
        step["why_it_cannot_be_settled_here"] = (
            "T-1558's rule is not built in this tree, so there is no fixpoint to settle at "
            "and the programme cannot be finished.")
    return step


def refamily_ledger(moves: list, buckets: list, refusals: list, totals_owed: int,
                    rule: dict | None = None) -> dict:
    """The book's account of what has moved, what is still held, and where it could land."""
    held = sum(r["already_drawn"] - r["the_re_cut_would_have_ordered"] for r in refusals)
    still = sum(r.get("surplus_still_held",
                      r["already_drawn"] - r["the_re_cut_would_have_ordered"]) for r in refusals)
    headroom = sum(max(0, (b["to_reconstruct"] or 0) - b["filled"]) for b in buckets)
    moved_from = sorted({m["from_bucket"] for m in moves})
    moved_into = sorted({m["to_bucket"] for m in moves})
    return {
        "ticket": "T-1557",
        "ruling": "the owner's ruling of 2026-09-24 on T-1530, carried in T-1556: the "
                  "surplus the re-cut holds is RE-FAMILIED rather than retired — the heads "
                  "move into the buckets the re-cut grew instead of being un-written",
        "what_a_move_is": "one reconstructed person counted in a different cell of the same "
                          "ladder. His card, his id, his residence_grade and every citation "
                          "on him are untouched; his sex and age band may not change; the "
                          "bucket he left keeps its `drawn_here` and names him in "
                          "`refamilied_out`, and the bucket he entered fills one of its "
                          "orders with a person the town already holds.",
        "what_a_move_is_not": "a retirement (nobody is un-written, which is T-1459's ruling "
                              "of 2026-09-20) and a draw (no stranger enters the town, so "
                              "the population does not move — only what is still OWED does).",
        "who_chooses_who_moves": ({
            "ticket": rule["ticket"],
            "settled": True,
            "rule": rule["one_line"],
            "the_rungs_a_move_may_name": rule["movable"],
            "the_rungs_it_refuses_on": [r for r in rule["rungs"] if r not in rule["movable"]],
            "read_from": "data/reconstruction/1835_refamily_rule.json",
            "why": "T-1558 modelled it against the adoption layers and published the cost "
                   "ladder there, with the tier of every held person and the ceilings the "
                   "axes impose. `refamily_shape` above refuses a move whose `rule` is not "
                   "one of the movable rungs, so the naming T-1557 required is now checked "
                   "rather than trusted.",
        } if rule else {
            "ticket": "T-1558",
            "settled": False,
            "why": "the rule is modelled against the adoption layers and is not this "
                   "ticket's. Every row must NAME the rule that chose its head, so a move "
                   "made before the rule exists cannot be written without saying so.",
        }),
        "who_makes_the_moves": {
            "ticket": "T-1559",
            "settled": bool(rule) and len(moves) >= rule["yields"],
            "the_rule_yields": rule["yields"] if rule else None,
            "spent": len(moves),
            "still_to_spend": (max(0, rule["yields"] - len(moves)) if rule else None),
            "spent_by": sorted({(m.get("carried_by") or {}).get("ticket")
                                for m in moves if (m.get("carried_by") or {}).get("ticket")}),
            "how_a_move_is_spent": "on the CARD first, and in this ledger second. The mint "
                                   "that derives a held head carries the move inside its "
                                   "own derivation — where the seed, the name and the id "
                                   "are already fixed, so a moved card re-derives byte for "
                                   "byte — and `tools/refamily_moves_1835.py --build` "
                                   "writes a row here ONLY where the card it names already "
                                   "says the same thing. So this ledger cannot claim a "
                                   "move the residents layer has not made, and a row typed "
                                   "into it by hand does not survive a --build.",
        },
        # THE PROGRAMME ITSELF IS A STEP, and `settled` is arithmetic rather than
        # opinion: it finishes where T-1558's rule does, which is the owner's ruling of
        # 2026-09-25 and is `the_programme_step` above. Every step here
        # carrying `settled: false` is a forward-looking work order, and
        # `every_work_order_names_a_live_ticket` refuses one whose ticket has closed
        # (T-1530). It has to, because the prose this ledger replaced handed the same
        # 523 people to T-1196, T-1197 and T-1179 for four days after all three had
        # closed, through every green gate — a refused bucket has `to_reconstruct` set
        # down to `filled`, so the bucket sweep reads 0 left and steps over it by design.
        # SWEPT TO A LIVE SUCCESSOR ON 2026-09-25 (T-1564's own PR, by the rule above
        # and T-1420's). T-1556 is the owner's ruling and it is SPLIT: T-1557, T-1558 and
        # T-1560 closed, and T-1559's last piece is T-1564 — the 54 women and children —
        # so the moment T-1564 settles, T-1556 has no live descendant and this order names
        # nobody. It is the case T-1581's ticket_liveness.py was written for, and it fired
        # on the PR that caused it rather than on the next branch to gate, which is the
        # whole point of that step. The order is still LIVE and must stay live: `settled`
        # is arithmetic, 395 people are still held across 44 refused buckets, and it is
        # T-1597 that owed them an answer, and T-1597 GOT one: the owner ruled on
        # 2026-09-25 that they remain held and that the programme is settled at the rule's
        # fixpoint rather than at nought. `the_programme_step` above is that finish line,
        # with the 395 and the refusal holding each of them written down beside it, and
        # `the_programme_finishes_where_the_rule_does` holds the two to each other. The
        # ruling of 2026-09-24 is unchanged and is still cited as T-1556 everywhere it is
        # quoted below.
        "the_programme": the_programme_step(still, refusals, moves, rule),
        "moves": moves,
        "counts": {
            "moves": len(moves),
            "people_moved": len({m["person"] for m in moves}),
            "buckets_moved_out_of": len(moved_from),
            "buckets_moved_into": len(moved_into),
            "adoptions_carried": sum(len(m.get("adoptions_carried") or []) for m in moves),
        },
        "the_held_surplus": {
            "buckets_refused": len(refusals),
            "people_held": held,
            "people_still_held": still,
            "open_headroom_in_person_buckets": headroom,
            "why_the_headroom_matters": "a held head moved into an open order fills that "
                                        "order without drawing a stranger, so each move "
                                        "takes one person off what is still owed rather "
                                        "than out of the town.",
        },
        "what_it_would_converge_to": {
            "still_owed_now": totals_owed,
            "still_owed_if_every_held_head_moved": max(0, totals_owed - min(held, headroom)),
            "note": "the model's point is what decides HOW MANY move, and that number is "
                    "T-1559's to spend; this book states the two ends of the range.",
        },
    }


# ----------------------------------------------------------------- the build --


# --------------------------------------------------------------------------- seats
#
# WHERE THE HOUSEHOLDS THE BOOK ORDERED ARE STANDING (T-1620, the second piece of
# T-1615 off T-1199).
#
# The book has always been able to say how many households the town still owes.
# It could not say how many of them now have GROUND, and that is the number the
# 5C build tickets are actually waiting on: a household with a lot is a roof
# somebody can raise, and a household without one is still an entry in a ledger.
#
# Two committed passes answer it, in order, and the order is the whole arithmetic:
# T-1613 offered every banded household the committed plat's 226 lots, and T-1614
# offered the 1,374 it handed on the ground the plat does not draw. So the second
# pass's `rows_in_scope` IS the first pass's `owed`, and a chain that does not join
# is a file that moved under this one — refused by name below rather than summed
# into a total that looks right.
#
# EVERY FIGURE HERE IS READ, NONE IS COMPUTED TWICE. Both seat files carry their
# own `counts`, derived and re-derived by their own tools and gated in check.sh;
# this reads those counts and the six slot rows, joins them, and adds nothing. A
# seat is either an ADOPTION — a household put under a roof that already stands —
# or a SLOT, a request the build tickets fulfil. Nothing here raises a roof.
SEAT_PASSES = (
    ("platted", "platted_seats", "T-1613",
     "The committed plat",
     "the 226 lots of the Thompson plat the lot ledger enumerates",
     "lots_taken", "lots"),
    ("off_plat", "off_plat_seats", "T-1614",
     "The ground the plat does not draw",
     "the tier lots, School Section blocks, Kinzie's Addition, survey tracts and camp "
     "grounds the off-plat ledger enumerates",
     "parcels_taken", "parcels"),
)


def seats_against_roofs(data: dict, structures: dict) -> dict:
    """The two seating passes, joined, against the roofs the town already has."""
    passes, chain = [], None
    for key, input_key, ticket, title, ground, taken_key, taken_word in SEAT_PASSES:
        doc = data[input_key]
        c = doc.get("counts") or {}
        if not c:
            raise Fault(f"the {key} seats file carries no counts — the book cannot read it")
        scope = int(c.get("rows_in_scope") or 0)
        seated = int(c.get("seated") or 0)
        owed = int(c.get("owed") or 0)
        adopted = int(c.get("roofs_adopted") or 0)
        slots = int(c.get("slots_requested") or 0)
        if seated + owed != scope:
            raise Fault(f"the {key} seating pass seats {seated} and owes {owed} of "
                        f"{scope} rows — its own arithmetic does not close")
        if adopted + slots != seated:
            raise Fault(f"the {key} seating pass seats {seated} but adopts {adopted} and "
                        f"requests {slots} — a seat is an adoption or a slot and nothing else")
        if chain is not None and scope != chain:
            raise Fault(f"the {key} seating pass was offered {scope} rows and the pass "
                        f"before it handed on {chain} — the two files have moved apart")
        chain = owed
        passes.append({
            "key": key, "ticket": ticket, "title": title, "ground": ground,
            "generated_by": doc.get("generated_by"),
            "rows_offered": scope, "seated": seated, "handed_on": owed,
            "roofs_adopted": adopted, "slots_requested": slots,
            "roofs_offered_for_adoption": int(c.get("roofs_offered_for_adoption") or 0),
            "roofs_held_back": int(c.get("roofs_held_back") or 0),
            "ground_taken": int(c.get(taken_key) or 0), "ground_taken_unit": taken_word,
            "by_district": dict(sorted((c.get("by_district") or {}).items())),
            "by_clause": dict(sorted((c.get("by_clause") or {}).items())),
        })
    # THE SIX SLOTS, NAMED. A slot is the only forward-looking thing either pass wrote:
    # the plat had headroom of the right family on a block and no standing roof to adopt,
    # so it asked for one. They are carried whole — household, block, lot and family —
    # because a request nobody can read is a request nobody fulfils.
    slots = [{
        "household_id": s.get("id"), "name": s.get("name"), "district": s.get("district"),
        "clause": s.get("clause"), "block_id": s.get("block_id"), "lot_id": s.get("lot_id"),
        "family": s.get("family"), "why": s.get("why"),
    } for s in (data["platted_seats"].get("seats") or []) if s.get("how") == "slot"]
    slots += [{
        "household_id": s.get("id"), "name": s.get("name"), "district": s.get("district"),
        "clause": s.get("clause"), "block_id": s.get("block_id"), "lot_id": s.get("lot_id"),
        "family": s.get("family"), "why": s.get("why"),
    } for s in (data["off_plat_seats"].get("seats") or []) if s.get("how") == "slot"]
    asked = sum(p["slots_requested"] for p in passes)
    if len(slots) != asked:
        raise Fault(f"the seating passes count {asked} slot(s) and carry {len(slots)} slot "
                    f"row(s) — the count and the rows disagree")
    seated = sum(p["seated"] for p in passes)
    adopted = sum(p["roofs_adopted"] for p in passes)
    standing = int(structures.get("standing_records") or 0)
    blocks = sorted({s["block_id"] for s in slots if s.get("block_id")})
    return {
        "statement": (
            "Two committed passes have offered every banded household ground: the plat "
            "first, then the ground the plat does not draw. This is what they seated, "
            "against the roofs the town already has. A seat is an ADOPTION — a household "
            "put under a roof that already stands — or a SLOT, a request the build "
            "tickets fulfil. Neither pass raises a roof, and nothing here is a claim "
            "about 1835: it is the reconstruction's own progress, read off two derived "
            "files and joined."),
        "inputs": [p["generated_by"] for p in passes],
        "rows_offered": passes[0]["rows_offered"],
        "seated": seated,
        "still_owed": passes[-1]["handed_on"],
        "roofs_adopted": adopted,
        "slots_requested": len(slots),
        "roofs_standing": standing,
        "roofs_standing_unseated": max(0, standing - adopted),
        "share_of_standing_roofs_seated": (round(adopted / standing, 4) if standing else None),
        "passes": passes,
        "requested_slots": slots,
        "slot_blocks": blocks,
        "what_the_slots_wait_on": (
            f"{len(slots)} slot(s) on {len(blocks)} block(s) — {', '.join(blocks)}. A slot "
            f"is headroom the block's own committed plan still holds, so the recipe that "
            f"deals that block is where it is spent." if slots else
            "no slot was requested: every seat is an adoption of a roof already standing."),
        "what_is_left": (
            f"{passes[-1]['handed_on']:,} of the {passes[0]['rows_offered']:,} banded "
            f"households are still on no ground at all. The reasons are written row by "
            f"row in both files' `owed`, and the clause each one waits on is carried "
            f"there rather than summarised away."),
    }


def build(data: dict, fills: list | None = None, occupancy: dict | None = None,
          moves: list | None = None) -> dict:
    fills = list(fills or [])
    for fill in fills:
        if not isinstance(fill, dict) or not fill.get("ticket") or not fill.get("bucket"):
            raise Fault("a fill in the ledger names no ticket or no bucket")
    rule = refamily_rule()
    moves = refamily_shape(moves, rule)
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
        # THE ORDER THE WORK WAS DRAWN AGAINST, AND NOT WHAT IS LEFT OF IT (T-1564). This
        # is the committed book's word that a bucket's draw was legitimate when it was
        # made, and a re-family LOWERS a bucket's standing order — the heads that walked
        # out took it down with them. So a bucket that was ordered at 60, drew 60 and has
        # since re-familied 8 of them away commits `to_reconstruct: 52`, and reading that
        # back as the order the 60 were drawn against says the draw was never allowed. The
        # book writes `drawn_here` on exactly the buckets a move touched, precisely so the
        # draw stays readable underneath the move; it is preferred here. Found when the
        # re-family programme settled and the order book could no longer rebuild itself.
        # LESS WHAT T-2021's RULING ADDED: it is ordered and filled apart, after this
        # yardstick is read (`family_ruling_orders`), so it is no part of the order the
        # quota's own work was drawn against.
        committed_order = {
            b["key"]: (lambda v: v - b.get("ordered_by_the_family_ruling", 0)
                       if v is not None else None)(
                b.get("drawn_here", b.get("to_reconstruct", b.get("to_build"))))
            for fam in json.loads(BOOK.read_text(encoding="utf-8"))["bucket_families"]
            for b in fam["buckets"]}
    # AND THE ORDER A LANDED MOVE FILLED, WHICH `drawn_here` CANNOT SAY (T-2078). A move's
    # destination draws nobody, so its `drawn_here` is 0 and the yardstick above reads it as
    # never ordered. What the committed book does say is the order it carried with the move
    # already counted inside it: `to_reconstruct` beside `refamilied_in`. T-2078 wrote 39
    # letter-list residents, the known layer's pro-rata share in
    # `persons/female/40_49/north/lodging/trade` rounded from 0 to 1, and that cell's order
    # fell to 0 under the one head T-1563 had already landed in it against an order of 1.
    # That is T-0841's case on the arriving end of a move instead of the drawing end, and
    # the owner's ruling of 2026-09-20 (T-1459) covers it the same way: the person is on a
    # card and nothing already counted moves. A landing the committed book never carried,
    # or more landings than it carried, is still a move into a closed order and a FAULT.
    committed_landing = {}
    if BOOK.exists():
        committed_landing = {
            b["key"]: {"order": b.get("to_reconstruct") or 0,
                       "landed": b["refamilied_in"]}
            for fam in json.loads(BOOK.read_text(encoding="utf-8"))["bucket_families"]
            for b in fam["buckets"] if b.get("refamilied_in")}

    def landed_against_an_open_order(b: dict) -> bool:
        was = committed_landing.get(b["key"])
        return bool(was and b.get("refamilied_in", 0) <= was["landed"]
                    and b["filled"] <= was["order"])
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
    # THE RULING'S FILLS ARE COUNTED APART (T-2021). The family ruling orders exactly what
    # its houses drew, so its cells are an order and a fill of the same size, added AFTER
    # the re-cut and the overfill gate have read the quota. Folded into `counted` they would
    # read to the re-cut as a draw past the order every refused cell was drawn against.
    ruled_fills = Counter()
    # WHO DREW, NOT JUST HOW MANY. The re-cut below spends a bucket's remainder only where
    # every stage that has drawn there is stable under a quota change, so it needs the
    # tickets and not only the counter — see `REMAINDER_STABLE_STAGES`.
    drawn_by: dict[str, set] = {}
    for fill in fills:
        if fill.get("ticket") == FAMILY_RULING_TICKET:
            ruled_fills[fill["bucket"]] += int(fill.get("records") or 0)
            continue
        counted[fill["bucket"]] += int(fill.get("records") or 0)
        if int(fill.get("records") or 0):
            drawn_by.setdefault(fill["bucket"], set()).add(fill.get("ticket") or "")
    # WHO LEFT AND WHO ARRIVED. A re-family is recorded on both ends, so the two
    # counters are built together and neither can exist without the other.
    moved_out, moved_in = Counter(), Counter()
    for m in moves:
        moved_out[m["from_bucket"]] += 1
        moved_in[m["to_bucket"]] += 1
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
            # DRAWN, MOVED OUT, MOVED IN — and `filled` is the arithmetic of the three.
            # `drawn_here` is never lowered by a move, because a move un-writes nobody
            # (T-1459's ruling); the two move counters are what make a `filled` below the
            # draw READABLE rather than a bucket quietly losing people. They are written
            # only where they are non-zero, so a book with an empty re-family ledger is
            # byte-identical to the book before T-1557.
            drawn = counted.get(b["key"], 0)
            out, into = moved_out.get(b["key"], 0), moved_in.get(b["key"], 0)
            b["filled"] = drawn - out + into
            if out or into:
                b["drawn_here"] = drawn
                if out:
                    b["refamilied_out"] = out
                if into:
                    b["refamilied_in"] = into
        families.append({"key": key, "title": title, "lead": lead,
                         "summary": payload, "buckets": buckets})

    # THE TRADE RE-CUT RUNS BETWEEN THE COUNTERS AND THE QUOTA CHECK, and it has to: it is
    # bounded by each bucket's undrawn remainder, so it cannot run before `filled` is
    # known — and the quota a bucket is judged against is the re-cut one, so it cannot run
    # after the check either. A bucket the re-cut GROWS is not overfilled by a counter that
    # sat inside its new order.
    trade_re_cut = recut_trade_remainder(families[0]["buckets"], participation, drawn_by)

    # THE RE-FAMILY LEDGER IS ADJUDICATED AGAINST THE CUT LADDER, not against the raw
    # axes: both ends have to be real person buckets, the two ends have to be the same
    # person, a bucket cannot move out more people than were ever drawn in it, and a
    # head may only land where an order is actually open. That last one is the check
    # the overfill gate below CANNOT make on its own — a destination which is itself
    # held by the re-cut would swallow an arrival inside its own refusal and read as
    # though the move had filled something.
    refamily_against_buckets(moves, families[0]["buckets"], counted)
    for b in families[0]["buckets"]:
        if (b.get("refamilied_in") and b["filled"] > (b["to_reconstruct"] or 0)
                and not landed_against_an_open_order(b)):
            raise Fault(
                f"the re-family ledger lands {b['refamilied_in']} head(s) in {b['key']}, "
                f"which orders {b['to_reconstruct']} and already holds "
                f"{b.get('drawn_here', b['filled'])}: a move needs an open order to fill")

    for family in families:
        for b in family["buckets"]:
            todo = b.get("to_reconstruct", b.get("to_build"))
            if todo is not None and b["filled"] > todo:
                was = quota_before.get(b["key"])
                cause = "the_re_cut_reached_work_already_drawn"
                # AND A PERSON BUCKET'S ORDER FALLS THE SAME WAY A BUSINESS BUCKET'S DOES
                # (T-0841). The pre-ruling cut is only the right yardstick while it is
                # ABOVE what was drawn: it is computed from the residents layer as it
                # stands, so the moment the town READS documented people into a cell, the
                # pre-ruling quota falls too and the test above stops telling a re-cut
                # apart from a filler — it calls both a filler. Measured reading St Mary's
                # baptismal register into the ladder: 25 more documented men aged 20-29 in
                # a south-side family trade, this cell's cut 60 -> 35, and its 60 drawn
                # were every one of them drawn against the 60 THIS BOOK ORDERED. That is
                # the T-1299 case exactly, one family over, and the owner's ruling of
                # 2026-09-20 covers it: nothing already drawn moves. So the fallback the
                # business families take is taken here too, and it is a fallback rather
                # than a replacement — `filled` above even the order the work was drawn
                # against is still a filler bypassing the book, and still a FAULT.
                if was is None or was < b["filled"]:
                    committed = committed_order.get(b["key"])
                    if committed is not None and committed >= b["filled"]:
                        was, cause = committed, "a_documented_reading_shrank_the_order"
                    elif was is None:
                        was, cause = committed, "a_documented_reading_shrank_the_order"
                landed = (family["key"] == "persons" and b.get("refamilied_in")
                          and landed_against_an_open_order(b))
                if landed:
                    # Read on the order the move landed against, whatever the pre-ruling
                    # cut says: on this end of a move the re-cut drew nobody, so it is
                    # never the re-cut that closed the order.
                    was = committed_landing[b["key"]]["order"]
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
                        # WHAT HAS LEFT THIS BUCKET ALREADY (T-1557). A refusal names the
                        # draw it still carries AND the heads the re-family ledger has
                        # moved out of it, so the surplus can be read shrinking. A bucket
                        # re-familied all the way down to the re-cut's order stops being a
                        # refusal at all — `filled > todo` is simply no longer true — which
                        # is how the 48 rows retire themselves one head at a time.
                        "drawn_here": b.get("drawn_here", b["filled"]),
                        "refamilied_out": b.get("refamilied_out", 0),
                        "surplus_still_held": b["filled"] - todo,
                        **({"refamilied_in": b["refamilied_in"]} if landed else {}),
                        "why": ("the re-cut would put this bucket's order under the people "
                                "already drawn against it."
                                if cause == "the_re_cut_reached_work_already_drawn" else
                                "the town read more people it can name, the known layer's "
                                "share of this cell grew, and its order fell under the "
                                "head(s) the re-family ledger had already landed in it "
                                "against an open order (T-2078). Nobody is moved back; the "
                                "surplus is the owning ticket's to retire."
                                if landed and not b.get("drawn_here") else
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

    family_ruling_orders(families[0]["buckets"], data.get("family_ruling") or {}, ruled_fills,
                         data.get("family_ruling_withdrawn") or {})
    men_ruling = (adult_men_ruling(families[0]["buckets"], data["adult_men"])
                  if data.get("adult_men") else None)
    store_ruling = store_residence_ruling(families[1]["buckets"], families[3]["buckets"])

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
            "households_known": known["houses_present"],
            "households_known_records": known["households_present"],
            "households_awaiting_a_household": known["records_awaiting_a_household"],
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
            "households_standing": known["houses_present"] + known["households_reconstructed"],
            "households_still_owed": sum(
                max(0, (b["to_reconstruct"] or 0) - b["filled"]) for b in families[1]["buckets"]),
        },
        # WHERE THE ORDERED HOUSEHOLDS ARE STANDING (T-1620). The totals above say how
        # many households the town still owes; this says how many of them now have
        # GROUND, which is the number the 5C build tickets are waiting on. Read off
        # T-1613's and T-1614's own derived counts and joined — nothing is recomputed
        # here and no seat is dealt here.
        "seats_against_roofs": seats_against_roofs(data, structures),
        # WHAT THE RE-CUT FOUND, written into the book rather than into a report nobody
        # re-derives (T-1463). Two of these are adjudications the ticket asked for out
        # loud, and the third is a collision this run declines to rule on.
        "what_the_re_cut_found": recut_findings(known, before, families, recut_refusals),
        # THE ADULT MEN, RULED ON THEIR CARDS (T-2187). Absent from a book built without
        # the measure, so a fixture book is byte-identical to one built before it.
        **({"adult_men_ruling": men_ruling} if men_ruling else {}),
        # THE STORE ROWS, RULED AGAINST THE STORE ROOFS (T-2194).
        **({"store_residence_ruling": store_ruling} if store_ruling else {}),
        "bucket_families": families,
        "programme_deltas": programme_deltas(data["model"], data["inventory"],
                                             data["programme"], persons, households),
        "invariants": invariants(known, persons, households, structures,
                                 families[2]["buckets"]),
        "fills": fills,
        # THE RE-FAMILY LEDGER (T-1557), the third word the book needed: a person moved
        # between cells is neither retired nor drawn, and this is where each move is
        # recorded on both ends. Empty by design — T-1558 models WHICH heads move and
        # T-1559 spends them.
        "re_family_ledger": refamily_ledger(
            moves, families[0]["buckets"], recut_refusals,
            sum(max(0, (b["to_reconstruct"] or 0) - b["filled"])
                for b in families[0]["buckets"]), rule),
    }
    if len(doc["bucket_families"]) != 5:
        raise Fault("the order book is five bucket families; fewer is a book with a hole in it")
    return doc


def family_ruling_orders(buckets: list, ruling: dict, ruled_fills: Counter,
                         withdrawn: dict | None = None) -> None:
    """T-2021: the cells the family ruling orders, and what its houses filled. In place.

    The ruling (`data/reconstruction/1835_family_ruling.json`, frozen) gave each married
    house it admitted the whole family the household model drew for it, and wrote down the
    cells those people fall in. Each is an ORDER here — `to_reconstruct` rises by it and
    `ordered_by_the_family_ruling` says so — and the ruling's fills fill it. So no cell is
    overfilled and none is left owing, and the town the book converges to rises by exactly
    the people the ruling seated, which the ruling itself held under the count. A fill the
    ruling did not order, or one past it, is a FAULT: that would be the ruling's ticket
    drawing past its own word.

    `withdrawn` is the cells of the admitted houses a later reading withdrew (T-2234, read
    off the modelled-families ledger). Each one leaves the order with its house, so the
    ruling never orders a family for a house that is not one. Withdrawing more than the
    ruling ordered is a FAULT."""
    orders = {k: int(v) for k, v in (ruling.get("orders") or {}).items()}
    for key, n in (withdrawn or {}).items():
        if int(n) > orders.get(key, 0):
            raise Fault(f"{FAMILY_RULING_TICKET}'s withdrawn houses take {n} from {key}, "
                        f"where its ruling orders {orders.get(key, 0)}")
        orders[key] -= int(n)
    by_key = {b["key"]: b for b in buckets}
    for key in sorted(set(orders) | set(ruled_fills)):
        b = by_key.get(key)
        if b is None:
            raise Fault(f"the family ruling orders into {key}, which is not a person bucket")
        order, filled = orders.get(key, 0), ruled_fills.get(key, 0)
        if filled > order:
            raise Fault(f"{FAMILY_RULING_TICKET} fills {filled} in {key} where its ruling "
                        f"orders {order}")
        b["ordered_by_the_family_ruling"] = order
        b["to_reconstruct"] = (b["to_reconstruct"] or 0) + order
        b["filled"] += filled
        if "drawn_here" in b:
            b["drawn_here"] += filled


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

    THE SCAN ITSELF IS SHARED (T-1581). It had been written out here and again in
    `research_spend_ledger`, and a ticket whose front matter one of them parsed and
    the other did not would have put the two gates on different queues.
    """
    return ticket_liveness.read_tree(tickets_dir=directory)[0]


def ticket_children(directory: Path = TICKETS) -> dict[str, list[str]]:
    """Every ticket that has a parent, indexed by the parent — a CHECK INPUT only.

    A `split` ticket is a grouping record and its children are the runs that discharge
    it. Nothing the book EMITS may depend on this, for the reason written on
    `ticket_states`; the gate below reads it and nothing else does.
    """
    return ticket_liveness.children_of(ticket_liveness.read_tree(tickets_dir=directory)[1])


def every_work_order_names_a_live_ticket(doc: dict, states: dict[str, str] | None = None,
                                         children: dict[str, list[str]] | None = None) -> str:
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

    AND A BUCKET IS NOT THE ONLY PLACE WORK IS ORDERED FROM (T-1530). Every step of
    `re_family_ledger` carrying `settled: false` is a forward-looking work order, and
    it is the one class the bucket sweep above CANNOT reach: a refused bucket has
    `to_reconstruct` set down to `filled`, so it reads 0 left and is skipped by design.
    That is how 523 held people sat in prose naming T-1196, T-1197 and T-1179 — all
    three closed — through four days of green gates, and how the ledger that replaced
    the prose could go the same way as its own pieces close.

    A SPLIT PROGRAMME IS LIVE WHILE ONE OF ITS PIECES IS, and only here. The asymmetry
    with a bucket is the point: a bucket names the single run that owes it, so a split
    leaves the next run guessing which child it is — the T-1192 stranding this sweep
    exists for. The re-family programme is the opposite, because the owner ruled on
    2026-09-24 that all 523 are ONE unit: the grouping ticket IS the owner and its
    children are its runs. What must never go stale is that somebody is still on it.
    """
    states = ticket_states() if states is None else states
    children = ticket_children() if children is None else children
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
    # A PIECE THAT HAS ITSELF SPLIT IS LIVE THROUGH ITS OWN PIECES (T-1575). T-1556
    # split into T-1557..T-1560, and T-1559 split in turn into T-1563 and T-1564; when
    # T-1560 closed on 2026-09-25 a one-level read saw three `done` and one `split`
    # and called the programme ended while T-1564 — 54 of its moves — stood open two
    # levels down. A split is a grouping record at every depth, so the walk goes
    # through it to the runs that discharge it, and a closed piece still ends the walk.
    #
    # THE WALK IS `tools/ticket_liveness.py`'s NOW (T-1581), where the ledger's
    # `split_live` and `ticket.mjs done` read the same relation. This gate's leaf set
    # is the book's own — `ORDER_BOOK_ALIVE`, in which a BLOCKED ticket is live,
    # because it is on the board, carries a `blocked_on` and unblocks.
    def live_pieces_of(ticket, seen=()):
        return ticket_liveness.live_pieces_of(ticket, states, children,
                                              ticket_liveness.ORDER_BOOK_ALIVE)

    steps, carried = [], []
    for name, step in sorted((doc.get("re_family_ledger") or {}).items()):
        if not isinstance(step, dict) or step.get("settled") is not False:
            continue
        ticket = step.get("ticket")
        state = states.get(ticket) if ticket else None
        steps.append(name)
        if not ticket:
            holes.append(f"the re-family programme's {name} is ordered by nobody")
        elif state is None:
            holes.append(f"the re-family programme's {name} is ordered by {ticket}, "
                         f"which is not a ticket")
        elif state == "split":
            pieces = live_pieces_of(ticket)
            if pieces:
                carried.append(f"{name} through {', '.join(sorted(pieces))}")
            else:
                holes.append(f"the re-family programme's {name} is ordered by {ticket}, "
                             f"which is split and has no live piece left — the programme "
                             f"ended with people still held")
        elif state in DEAD_TICKET_STATES:
            holes.append(f"the re-family programme's {name} is ordered by {ticket}, "
                         f"which is {state}")
    if holes:
        raise Fault("the book orders work from tickets nobody can claim — sweep the owner "
                    "tables onto the live successors (T-1420): " + "; ".join(sorted(holes)[:8])
                    + (f" (+{len(holes) - 8} more)" if len(holes) > 8 else ""))
    if not states:
        return "the queue could not be read, so no work order was checked"
    ordered = sum(1 for f in doc.get("bucket_families", []) for b in f.get("buckets", []))
    said = f"every work order across {ordered} buckets names a ticket a run can still claim"
    if steps:
        said += (f", and so do the re-family programme's {len(steps)} unsettled step(s)"
                 + (f" ({'; '.join(carried)})" if carried else ""))
    return said


def the_programme_finishes_where_the_rule_does(doc: dict) -> str:
    """THE FINISH-LINE GATE (T-1597), asked on every --build and --check.

    The work-order gate above asks whether an UNSETTLED step names somebody who can
    still act. It cannot ask the question underneath it — whether `settled` says the
    truth — and until the owner's answer of 2026-09-25 there was nothing to ask: the
    finish line was `still == 0` and the only way to reach it was to move everybody.

    The finish line is the rule's fixpoint now, so `settled` is a claim about TWO other
    documents and this holds it to them:

      * it agrees with the rule's own remainder — settled exactly when the rule yields
        no further move, read off `who_makes_the_moves`' spent-against-yielded and never
        from the flag itself;
      * the residue it settles over is the refusal table's arithmetic — the count is the
        held surplus the book already states, and the refusal holding each person sums to
        that count rather than sitting beside it;
      * and a programme settled with people still held SAYS SO, in words, naming the
        ruling that set the line and what becomes of them. A settled step orders nobody,
        so the work-order gate goes quiet on it; that quiet must not be the only record
        that 395 invented people are still standing where the re-cut found them.

    The last clause is the one worth the file. `settled: true` with an empty residue
    statement would take every gate in this project green while saying nothing at all
    about the people it settles over, which is the shape of the four-day silence
    `every_work_order_names_a_live_ticket` was written for.
    """
    ledger = doc.get("re_family_ledger") or {}
    step = ledger.get("the_programme")
    if not isinstance(step, dict):
        raise Fault("the re-family ledger states no programme step at all, so nothing says "
                    "where the programme finishes")
    held = ledger.get("the_held_surplus") or {}
    makes = ledger.get("who_makes_the_moves") or {}
    left, yields_, spent = (step.get("moves_the_rule_still_yields"),
                            makes.get("the_rule_yields"), makes.get("spent"))
    if yields_ is not None and spent is not None and left != max(0, yields_ - spent):
        raise Fault(f"the programme says the rule still yields {left} move(s) while the "
                    f"ledger says {spent} of {yields_} are spent")
    if bool(step.get("settled")) is not (left == 0):
        raise Fault(f"the programme reads settled={step.get('settled')!r} with {left} "
                    f"move(s) the rule still yields: the finish line is the rule's "
                    f"fixpoint (T-1597) and `settled` may not be set by hand")
    still = step.get("people_still_held")
    if still != held.get("people_still_held"):
        raise Fault(f"the programme holds {still} people and the book's own surplus holds "
                    f"{held.get('people_still_held')}")
    named = sum((row.get("people") or 0) for row in step.get("and_what_holds_each_of_them") or ())
    if named != still:
        raise Fault(f"the programme holds {still} people and names the refusal that holds "
                    f"{named} of them")
    if step.get("settled") and (still or 0) > 0:
        if step.get("buckets_they_are_held_in") != held.get("buckets_refused"):
            raise Fault(f"the programme settles over {step.get('buckets_they_are_held_in')} "
                        f"refused bucket(s) and the book refuses "
                        f"{held.get('buckets_refused')}")
        for field in ("the_finish_line", "the_ruling_that_set_it", "what_becomes_of_them",
                      "what_would_reopen_it"):
            if not str(step.get(field) or "").strip():
                raise Fault(f"the programme is settled with {still} people still held and "
                            f"states no {field}: a settled step orders nobody, so this is "
                            f"the only place the residue is recorded (T-1597)")
    if not step.get("settled"):
        return (f"the re-family programme is unsettled with {left} move(s) the rule still "
                f"yields")
    if (still or 0) == 0:
        return "the re-family programme is settled with nobody held"
    return (f"the re-family programme is settled at its rule's fixpoint, with {still:,} "
            f"people recorded as held in {step['buckets_they_are_held_in']} refused "
            f"bucket(s)")


def recut_findings(known: dict, before: dict, families: list, refusals: list) -> list[dict]:
    """What the re-cut made measurable — T-1463's three, and T-1525's fourth.

    The fourth is the one a refusal cannot say on its own. `recut_refusals` records
    every bucket the re-cut would have cut below what was already drawn, one row at a
    time; the DOCUMENTED ones are a different fact from the rest, because they are not
    a quota drifting under a draw but the town reading a person it can name and finding
    it had already reconstructed a stranger in that place. Those are over-supplies with
    a size, and the size is the thing a run retiring them has to know.
    """
    def owed(fam, ticket=None):
        return sum(max(0, (b["to_reconstruct"] or 0) - b["filled"]) for b in fam["buckets"]
                   if ticket is None or b["owning_ticket"] == ticket)
    persons, households = families[0], families[1]
    p_1171 = owed(persons, FAMILY_OWNER)
    h_1171 = owed(households, FAMILY_HOUSEHOLD_OWNER) + owed(households, STORE_RESIDENCE_OWNER)
    held = sum(r["already_drawn"] - r["the_re_cut_would_have_ordered"] for r in refusals)
    target = persons["summary"]["town_target"]
    low, high = persons["summary"]["town_target_range"]
    standing = known["persons_standing"]
    still = owed(persons)
    shrank = [r for r in refusals
              if r.get("cause") == "a_documented_reading_shrank_the_order"]
    over = [{"bucket": r["bucket"],
             "owning_ticket": r["owning_ticket"],
             "already_drawn": r["already_drawn"],
             "the_re_cut_would_have_ordered": r["the_re_cut_would_have_ordered"],
             "over_supplied_by": r["already_drawn"] - r["the_re_cut_would_have_ordered"]}
            for r in sorted(shrank, key=lambda r: -(r["already_drawn"]
                                                    - r["the_re_cut_would_have_ordered"]))]
    over_total = sum(b["over_supplied_by"] for b in over)
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
            "asks": "The model wants 643 households and the layer holds "
                    f"{known['households_present'] + known['households_reconstructed']:,} records. "
                    "Are those the same thing?",
            "the_answer_is": "NO — RULED BY THE OWNER, 2026-09-21, and carried here (T-1476).",
            "ruling": "A name on a post-office letter list is evidence that a man was at "
                      "Chicago. It is not evidence that he kept a house. A record whose whole "
                      "evidence says nothing about a dwelling is a PERSON AWAITING A "
                      "HOUSEHOLD, so the record count and the house count are two units and "
                      f"{known['households_present'] + known['households_reconstructed']:,} "
                      "against 643 is a BACKLOG, not a contradiction.",
            "households_known_before_the_rulings": before["households_present"],
            "records_known_now": known["households_present"],
            "houses_known_now": known["houses_present"],
            "records_awaiting_a_household": known["records_awaiting_a_household"],
            "houses_by_clause": dict(known["houses_present_by_clause"]),
            "model_target": households["summary"]["households_target"],
            "model_range": list(households["summary"]["households_target_range"]),
            "measured": f"Of the {known['households_present']:,} records the layer holds present, "
                        f"{known['houses_present']:,} carry a reading about a dwelling and "
                        f"{known['records_awaiting_a_household']:,} do not. The quota is taken "
                        f"against the {known['houses_present']:,}, so it stops reading 0 owed — "
                        "which was never true and was the symptom that raised this — and starts "
                        "reading what the town still owes in houses.",
            "the_test_is_the_evidence_not_the_head_count":
                "A one-person record is not held out because it holds one person; a man may "
                "well have lived alone. It is held out where its whole evidence is a name on "
                "a list. The clause that lets a record stand as a house is written on its own "
                "manifest row as `dwelling_evidence` and is tallied above — so which of the "
                "records are which is readable off the layer and not asserted here.",
            "what_this_does_not_do": "Nothing is retired, nothing is re-graded and nobody is "
                                     "downgraded. Every record stays as it is, with its evidence "
                                     "and its grade; what changes is which question it answers. "
                                     "A record answers both the moment something seats him, and "
                                     "the derivation picks that up on the next rebuild.",
        },
        {
            "id": "a_documented_reading_shrank_an_order_the_town_had_drawn",
            "asks": "The parish register's 120 documented residents (T-0841) land in buckets "
                    "the town had already reconstructed strangers into. Where did reading a "
                    "person the town can name put a bucket's order UNDER what was drawn "
                    "against it, and by how many people?",
            "the_answer_is": f"{len(over)} bucket(s), over-supplied by {over_total:,} in all.",
            "buckets": over,
            "over_supplied_by": over_total,
            "measured": (
                ("; ".join(
                    f"`{b['bucket']}` holds {b['already_drawn']:,} drawn against an order of "
                    f"{b['the_re_cut_would_have_ordered']:,} — over-supplied by "
                    f"{b['over_supplied_by']:,}" for b in over)
                 or "no bucket's order was shrunk by a documented reading")
                + f". That is {over_total:,} reconstructed people standing where the sources "
                  "now name someone else, and it is a different fault from the rest of "
                  "`recut_refusals`: those are quotas drifting under a draw, this is the town "
                  "learning it invented a person it did not need. Nothing here is clamped and "
                  "nothing already drawn moves — T-1459 — so the book keeps ordering the "
                  "larger figure and names the surplus instead."),
            "declined": "RETIRING a reconstructed card is the bucket owner's work and not this "
                        "book's: a book that deleted people to make its own arithmetic close "
                        "would be reconstructing backwards. T-1347, which drew the trade band, "
                        "has closed, so T-1530 is filed for the south-side 20-29 surplus and "
                        "T-1506 owns the surplus lawyer.",
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
        "> T-1463 summed T-1386's presence rulings into `known`, and T-1525 read the parish "
        "register into it. These are the things that made measurable, carried in the book "
        "so they cannot go stale in a report.",
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
            "was drawn. The three tickets this paragraph used to hand the surplus to — "
            "T-1196, T-1197 and T-1179 — are all closed; the owner's ruling of 2026-09-24 "
            "(T-1556) hands it to the re-family programme below, where the held heads move "
            "into the buckets the re-cut grew instead of being un-written.", ""]
    if refusals:
        out += ["| bucket | ticket | cause | quota it was drawn against | the re-cut would "
                "order | drawn | re-familied out | still held |",
                "|---|---|---|---:|---:|---:|---:|---:|"]
        for r in refusals:
            out.append(f"| `{r['bucket']}` | {r['owning_ticket']} | "
                       f"{r.get('cause', 'the_re_cut_reached_work_already_drawn')} | "
                       f"{r['quota_it_was_drawn_against']:,} | "
                       f"{r['the_re_cut_would_have_ordered']:,} | {r['already_drawn']:,} | "
                       f"{r.get('refamilied_out', 0):,} | {r.get('surplus_still_held', 0):,} |")
    rf = doc.get("re_family_ledger") or {}
    if rf:
        h, c = rf["the_held_surplus"], rf["counts"]
        conv = rf["what_it_would_converge_to"]
        out += ["", "## The re-family ledger", "",
                rf["ruling"] + ".", "",
                f"**A move is** {rf['what_a_move_is']}", "",
                f"**A move is not** {rf['what_a_move_is_not']}", "",
                f"{h['people_held']:,} held head(s) stand across {h['buckets_refused']:,} "
                f"refused bucket(s), and {h['open_headroom_in_person_buckets']:,} slot(s) of "
                f"order stand open elsewhere in the persons ladder. "
                f"{h['why_the_headroom_matters'][0].upper()}"
                f"{h['why_the_headroom_matters'][1:]}", "",
                f"**{c['moves']:,} move(s) have been made**, carrying "
                f"{c['adoptions_carried']:,} adoption(s) out of {c['buckets_moved_out_of']:,} "
                f"bucket(s) and into {c['buckets_moved_into']:,}. The book is owed "
                f"{conv['still_owed_now']:,} people now, and would be owed "
                f"{conv['still_owed_if_every_held_head_moved']:,} if every held head moved. "
                f"{conv['note'][0].upper()}{conv['note'][1:]}", "",
                f"Which heads move is {rf['who_chooses_who_moves']['ticket']}'s "
                f"({'settled' if rf['who_chooses_who_moves']['settled'] else 'not settled'}): "
                f"{rf['who_chooses_who_moves']['why']} The moves themselves are "
                f"{rf['who_makes_the_moves']['ticket']}'s.", ""]
        prog = rf.get("the_programme") or {}
        if prog:
            out += [f"**The programme is "
                    f"{'settled' if prog.get('settled') else 'not settled'}**, and its "
                    f"finish line is {prog['the_finish_line']} "
                    f"{prog['the_ruling_that_set_it']}", ""]
            if prog.get("settled") and (prog.get("people_still_held") or 0) > 0:
                out += [f"{prog['people_still_held']:,} person(s) remain held in "
                        f"{prog['buckets_they_are_held_in']:,} refused bucket(s), and what "
                        f"becomes of them is {prog['what_becomes_of_them']}", "",
                        "| the refusal that holds them | people |", "|---|---:|"]
                out += [f"| `{r['refusal']}` | {r['people']:,} |"
                        for r in prog["and_what_holds_each_of_them"]]
                out += ["", f"What would reopen it: {prog['what_would_reopen_it']}", ""]
        if rf["moves"]:
            out += ["| person | out of | into | order filled | rule | ticket | adoptions |",
                    "|---|---|---|---|---|---|---:|"]
            for m in rf["moves"]:
                out.append(f"| `{m['person']}` | `{m['from_bucket']}` | `{m['to_bucket']}` | "
                           f"{m.get('order_filled', '')} | {m['rule']} | {m['ticket']} | "
                           f"{len(m.get('adoptions_carried') or []):,} |")
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

    sr = doc["seats_against_roofs"]
    out += ["", "## Where the ordered households are standing", "", sr["statement"], "",
            f"- offered ground: {sr['rows_offered']:,}",
            f"- seated: {sr['seated']:,} — {sr['roofs_adopted']:,} by adopting a roof that "
            f"already stands, {sr['slots_requested']:,} by asking for one",
            f"- still on no ground at all: {sr['still_owed']:,}",
            f"- of the {sr['roofs_standing']:,} roofs the town already has, "
            f"{sr['roofs_adopted']:,} now carry a reconstructed household",
            "", "| pass | ticket | offered | seated | adopted | slots | handed on |",
            "|---|---|---:|---:|---:|---:|---:|"]
    for pass_ in sr["passes"]:
        out.append(f"| {pass_['title']} | {pass_['ticket']} | {pass_['rows_offered']:,} | "
                   f"{pass_['seated']:,} | {pass_['roofs_adopted']:,} | "
                   f"{pass_['slots_requested']:,} | {pass_['handed_on']:,} |")
    out += ["", sr["what_the_slots_wait_on"], ""]
    if sr["requested_slots"]:
        out += ["| household | block | lot | family | clause |", "|---|---|---|---|---|"]
        for slot in sr["requested_slots"]:
            out.append(f"| `{slot['household_id']}` | `{slot['block_id']}` | "
                       f"`{slot['lot_id']}` | {slot['family']} | `{slot['clause']}` |")
    out += ["", sr["what_is_left"]]

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
        if family["key"] == "households" and doc.get("store_residence_ruling"):
            ruling = doc["store_residence_ruling"]
            out += ["", f"**The store rows, ruled ({ruling['ticket']}).** {ruling['measured']} "
                        f"{ruling['ruling']}"]

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

def splice_fills(fills: list, tickets, rows: list) -> list:
    """A filler's rows go back WHERE ITS ROWS STOOD, never to the end (T-1968).

    Every filler used to drop its own rows and append the new ones, so the ledger's order
    recorded which tool ran LAST rather than anything about the town. A PR that re-ran
    `reconstruct_businesses_1835.py --build` alone left its lawyer row at the foot of the
    ledger; the next `rederive.mjs --run` re-ran three household stages past it and moved
    56 rows above it; the next lone business build moved it back. A fourteen-line diff
    about nothing, on every lap, and `--run` was never a fixed point of a committed tree.

    Still never re-sorted — the ledger keeps the order the stages first filled it in, and a
    writer's own rows keep the order it emits them in. A writer whose tickets hold no row
    yet appends, as before; one that built nothing clears its rows, as before.
    """
    tickets = set(tickets)
    out, placed = [], False
    for fill in fills:
        if fill.get("ticket") in tickets:
            if not placed:
                out += rows
                placed = True
            continue
        out.append(fill)
    return out if placed else out + list(rows)


def _fills_on_disk() -> list:
    if not BOOK.exists():
        return []
    try:
        return json.loads(BOOK.read_text(encoding="utf-8")).get("fills", [])
    except json.JSONDecodeError as exc:
        raise Fault(f"the committed order book is not JSON: {exc}") from exc


def _moves_on_disk() -> list:
    """The re-family ledger carries forward off the committed book, exactly as `fills` do."""
    if not BOOK.exists():
        return []
    try:
        book = json.loads(BOOK.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Fault(f"the committed order book is not JSON: {exc}") from exc
    return (book.get("re_family_ledger") or {}).get("moves", [])


def cmd_build(owners_gate: bool = True) -> int:
    """Re-derive the book. `owners_gate=False` is for a FILLER re-deriving it mid-chain.

    T-2189. A filler that WITHDRAWS people — the modelled-families stage taking the wives
    and children off a head ruled dead before the day — leaves the cells it vacated owing
    until the stage that fills them runs next (T-1174's women and children, one step
    below it). Whether every owed row names a live ticket is a claim about the FINISHED
    book, so it is held at the book's own `--build` and `--check`, which run after every
    filler; refusing it mid-chain stopped the chain one step short of the stage that pays
    the debt. The overfill check, which is about the filler's own draw, is never deferred.
    """
    doc = build(load(), _fills_on_disk(), moves=_moves_on_disk())
    lands = converges_inside_the_model(doc)
    owners = (every_work_order_names_a_live_ticket(doc) if owners_gate else
              "the live-owner gate is the book's own --build's, after every filler")
    finish = the_programme_finishes_where_the_rule_does(doc)
    BOOK.parent.mkdir(parents=True, exist_ok=True)
    BOOK.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report_text(doc), encoding="utf-8")
    n = sum(len(f["buckets"]) for f in doc["bucket_families"])
    print(f"OK: 1835 reconstruction order book — {n} buckets in "
          f"{len(doc['bucket_families'])} families; {doc['totals']['persons_to_reconstruct']:,} "
          f"persons, {doc['totals']['households_to_reconstruct']:,} households, "
          f"{doc['totals']['businesses_to_reconstruct']:,} businesses and "
          f"{doc['totals']['roofs_to_build']:,} roofs to reconstruct; {lands}; {owners}; "
          f"{finish}")
    return 0


def cmd_check() -> int:
    faults = []
    if not BOOK.exists():
        print("FAIL: the 1835 reconstruction order book is missing — run --build", file=sys.stderr)
        return 1
    expected = build(load(), _fills_on_disk(), moves=_moves_on_disk())
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
          f"{every_work_order_names_a_live_ticket(expected)}; "
          f"{the_programme_finishes_where_the_rule_does(expected)}")
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
    # AND ONE THE FAMILY RULING ORDERS NOTHING INTO (T-2021): a ruled cell's order carries
    # the ruling's fills on top of the re-cut's, so `to_reconstruct + 1` there is no longer
    # inside the gap the fixtures below stand in, and they would fault for the ruling's
    # reason rather than their own.
    first = next(b for b in doc["bucket_families"][0]["buckets"]
                 if b["axes"].get("age_band") in shut_bands and (b["to_reconstruct"] or 0) > 0
                 and not b.get("ordered_by_the_family_ruling"))
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
    # Built the way cmd_build builds it, re-family ledger and all (T-2078): without the
    # moves the same book owes 130 more people, and once the letter-list gains raised the
    # standing town that move-less book crossed the model's ceiling while the shipped one
    # sat inside it, so the assertion was testing a book nobody ships.
    committed_standing = json.loads(BOOK.read_text(encoding="utf-8"))["totals"]["persons_standing"]
    assert (f"{committed_standing:,} standing"
            in converges_inside_the_model(build(data, _fills_on_disk(), occ, moves=_moves_on_disk())))

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

    # ---- THE RE-FAMILY LEDGER (T-1557) ---------------------------------------------
    # The owner's ruling of 2026-09-24 (T-1556) turns the 48 refused buckets' surplus from
    # something retired into something MOVED, and these guards are the whole difference:
    # a move that cannot be read on both ends is a retirement wearing a different word.
    # The fixtures move ONE head between two real person buckets of the same sex and age
    # band, because that is the only move the ruling permits.
    people = shipped["bucket_families"][0]["buckets"]
    held = next(b for b in people if b.get("recut_refused"))
    twin = next(b for b in people
                if b["key"] != held["key"]
                and b["axes"].get("sex") == held["axes"].get("sex")
                and b["axes"].get("age_band") == held["axes"].get("age_band")
                and (b["to_reconstruct"] or 0) > b["filled"])
    other_sex = next((b for b in people
                      if b["axes"].get("age_band") == held["axes"].get("age_band")
                      and b["axes"].get("sex") != held["axes"].get("sex")
                      and (b["to_reconstruct"] or 0) > b["filled"]), None)

    def move(**over):
        row = {"person": "res_self_test_head", "from_bucket": held["key"],
               "to_bucket": twin["key"], "order_filled": twin.get("owning_ticket"),
               # A RUNG THE MODEL PUBLISHES, since T-1558. The fixture used to name
               # `the_self_test` here and the book could not tell: the string was
               # un-checkable. It reads the ladder now, so this row stands or falls with
               # the same gate a real move does.
               "rule": (refamily_rule() or {}).get("movable", ["C1"])[-1],
               "ticket": "T-1557", "adoptions_carried": []}
        row.update(over)
        return row

    # THE SHIPPED BOOK MOVES NOBODY, and says so rather than staying silent about it.
    ledger = shipped["re_family_ledger"]
    assert ledger["moves"] == [] and ledger["counts"]["moves"] == 0, ledger["counts"]
    # …AND ITS ACCOUNT OF THE SURPLUS IS THE REFUSAL TABLE'S OWN ARITHMETIC, not a
    # number typed beside it.
    assert ledger["the_held_surplus"]["people_held"] == sum(
        r["surplus_still_held"] for r in shipped["recut_refusals"])
    assert ledger["the_held_surplus"]["buckets_refused"] == len(shipped["recut_refusals"])
    assert (ledger["what_it_would_converge_to"]["still_owed_now"]
            == shipped["totals"]["persons_still_owed"])
    # AN EMPTY LEDGER CHANGES NOTHING. The book with no moves in it is the book that
    # stood before this ledger existed, bucket for bucket.
    assert [b["filled"] for b in people] == [
        b["filled"] for b in build(data, _fills_on_disk(), occ, [])["bucket_families"][0]["buckets"]]

    # A MOVE IS RECORDED ON BOTH ENDS, and `filled` is the arithmetic of the three
    # numbers rather than a count that quietly fell.
    moved = build(data, _fills_on_disk(), occ, [move()])
    src = row(moved, held["key"])
    dst = row(moved, twin["key"])
    assert src["drawn_here"] == held["filled"] and src["refamilied_out"] == 1, src
    assert src["filled"] == held["filled"] - 1, src
    assert dst["refamilied_in"] == 1 and dst["filled"] == twin["filled"] + 1, dst
    # …and the bucket it left stops claiming the surplus that walked out of it.
    left = next(r for r in moved["recut_refusals"] if r["bucket"] == held["key"])
    was = next(r for r in shipped["recut_refusals"] if r["bucket"] == held["key"])
    assert left["refamilied_out"] == 1 and left["surplus_still_held"] == was["surplus_still_held"] - 1, left
    # …and one order is filled without a stranger entering the town: the people
    # standing do not move, what is still OWED falls by one.
    assert moved["totals"]["persons_standing"] == shipped["totals"]["persons_standing"]
    assert moved["totals"]["persons_still_owed"] == shipped["totals"]["persons_still_owed"] - 1

    fires("a re-family move that names no person",
          lambda: build(data, _fills_on_disk(), occ, [move(person=None)]))
    fires("a re-family move that names no rule that chose the head",
          lambda: build(data, _fills_on_disk(), occ, [move(rule=None)]))
    # AND A RULE NOBODY PUBLISHED, OR ONE PUBLISHED AS A REFUSAL (T-1558). The first was
    # un-checkable until the cost ladder existed; the second is the rule contradicting
    # itself — a move standing on the rung that refuses it.
    if refamily_rule():
        fires("a re-family move naming a rule that is not a rung of the cost ladder",
              lambda: build(data, _fills_on_disk(), occ, [move(rule="whoever_lacked_a_job")]))
        refusing = [r for r in refamily_rule()["rungs"]
                    if r not in refamily_rule()["movable"]]
        fires("a re-family move standing on a rung the rule refuses on",
              lambda: build(data, _fills_on_disk(), occ, [move(rule=refusing[0])]))
    fires("a re-family move that does not say which adoptions travel with the head",
          lambda: build(data, _fills_on_disk(), occ, [move(adoptions_carried=None)]))
    fires("a re-family move that leaves and enters the same bucket",
          lambda: build(data, _fills_on_disk(), occ, [move(to_bucket=held["key"])]))
    fires("a re-family move into a bucket that is not in this book",
          lambda: build(data, _fills_on_disk(), occ, [move(to_bucket="persons/no/such/cell")]))
    fires("one person re-familied twice",
          lambda: build(data, _fills_on_disk(), occ, [move(), move()]))
    fires("a bucket re-familying out more heads than were ever drawn in it",
          lambda: build(data, _fills_on_disk(), occ,
                        [move(person=f"res_self_test_{n}") for n in range(held["filled"] + 1)]))
    if other_sex is not None:
        fires("a re-family move that would re-sex the head",
              lambda: build(data, _fills_on_disk(), occ, [move(to_bucket=other_sex["key"])]))
    # AND A HEAD MAY ONLY LAND WHERE AN ORDER IS OPEN. A destination which is itself
    # held by the re-cut would otherwise swallow the arrival inside its own refusal.
    full = next((b for b in people
                 if b["key"] != held["key"] and b.get("recut_refused")
                 and b["axes"].get("sex") == held["axes"].get("sex")
                 and b["axes"].get("age_band") == held["axes"].get("age_band")), None)
    if full is not None:
        fires("a re-family move into a bucket with no order left to fill",
              lambda: build(data, _fills_on_disk(), occ, [move(to_bucket=full["key"])]))

    # …UNLESS THE ORDER WAS OPEN WHEN IT LANDED AND A READING SHRANK IT SINCE (T-2078). One
    # head more than the destination's room stands in for an order that fell under its
    # landings. A committed book that carried those landings against an order that held
    # them makes it a refusal by name; one that carried fewer landings, or none, leaves it
    # the fault above. The committed book is swapped for a fixture and put back.
    over = (twin["to_reconstruct"] or 0) - twin["filled"] + 1
    if held["filled"] >= over:
        heads = [move(person=f"res_self_test_landed_{n}") for n in range(over)]
        committed = json.loads(BOOK.read_text(encoding="utf-8"))

        def with_landed(landed):
            # The written book leaves out a trade cell nobody has drawn in, so the
            # destination is put in rather than looked up.
            fixture = copy.deepcopy(committed)
            persons_fam = fixture["bucket_families"][0]["buckets"]
            persons_fam[:] = [b for b in persons_fam if b["key"] != twin["key"]]
            persons_fam.append({**twin, "to_reconstruct": twin["filled"] + over,
                                "refamilied_in": landed})
            path = Path(tempfile.mkstemp(suffix=".json")[1])
            path.write_text(json.dumps(fixture), encoding="utf-8")
            made.append(path)
            return path

        made: list[Path] = []

        saved = globals()["BOOK"]
        try:
            globals()["BOOK"] = with_landed(over)
            kept = build(data, _fills_on_disk(), occ, heads)
            refused = next(r for r in kept["recut_refusals"] if r["bucket"] == twin["key"])
            assert (refused["cause"] == "a_documented_reading_shrank_the_order"
                    and refused["refamilied_in"] == over and refused["held_at"]
                    == twin["filled"] + over and "T-2078" in refused["why"]), refused
            globals()["BOOK"] = with_landed(over - 1)
            fires("more heads landed in a shrunk order than the committed book carried",
                  lambda: build(data, _fills_on_disk(), occ, heads))
        finally:
            globals()["BOOK"] = saved
            for path in made:
                path.unlink(missing_ok=True)

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
    #
    # AND SINCE T-1808 (2026-10-02) THE INNS ROW IS A RESTATEMENT AGAIN, by the same flag.
    # Mark Beaubien's and Alanson Sweet's in-window tavern firms are answered by the two
    # Washington-tier houses the placement pass seats them on, which are reconstructed
    # roof firms the trade census does not count, so the layer reads nine at the scene date
    # against the programme's ten and the ceiling falls back onto the programme's figure.
    # The flag follows the numbers; what is held here is that it does, in both directions.
    inns_row = deltas["inns_and_taverns"]
    assert inst["restates_the_programme"] is True, inst
    assert deltas["boarding_houses"]["restates_the_programme"] is True, deltas["boarding_houses"]
    assert inns_row["restates_the_programme"] is (inns_row["delta"] == 0), inns_row
    assert inns_row["delta"] >= 0, inns_row
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

    # EVERY BUCKET NAMES A TICKET. This read `startswith("T-1")` — the reconstruction
    # bands were all T-1xxx when it was written — until T-1171's split put its rows on
    # T-2021 (T-2019) and the queue's numbering passed the prefix. Whether the ticket is
    # still claimable is `every_work_order_names_a_live_ticket`'s question, not this one's.
    for family in doc["bucket_families"]:
        for b in family["buckets"]:
            owners = [b["owning_ticket"]] if b.get("owning_ticket") else b.get("owning_tickets", [])
            for owner in owners:
                assert re.fullmatch(r"T-\d{4}", owner), (b["key"], owner)

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
    # The shipped ledger's own unsettled steps are part of the fixture now: the gate
    # reads them too, so a `states` built from the buckets alone would fail every case
    # below for a reason none of them is about.
    states = {t: "open" for b in buckets for t in named(b)}
    states.update({step["ticket"]: "open"
                   for step in (doc.get("re_family_ledger") or {}).values()
                   if isinstance(step, dict) and step.get("ticket")})
    every_work_order_names_a_live_ticket(doc, states, {})
    every_work_order_names_a_live_ticket(
        doc, {**states, owed_by["owning_ticket"]: "blocked-tech"}, {})
    for dead in ("done", "split", "withdrawn"):
        fires(f"a bucket with work left ordered by a {dead} ticket",
              lambda d=dead: every_work_order_names_a_live_ticket(
                  doc, {**states, owed_by["owning_ticket"]: d}, {}))
    fires("a bucket ordered by an id that is not a ticket at all",
          lambda: every_work_order_names_a_live_ticket(
              doc, {k: v for k, v in states.items() if k != owed_by["owning_ticket"]}, {}))
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
    every_work_order_names_a_live_ticket(doc, {**states, discharged["owning_ticket"]: "done"}, {})
    assert "T-1166" not in {t for b in buckets for t in named(b)}, \
        "the book's own authoring ticket is provenance and must not be a work order"

    # AN UNSETTLED STEP OF THE RE-FAMILY PROGRAMME IS A WORK ORDER TOO (T-1530). Every
    # case below is asserted against a MADE ledger rather than the shipped one, because
    # what the queue holds this morning may not decide whether a gate is proven — and
    # because a settled programme carries no unsettled step at all, which is the healthy
    # state and can prove nothing. That is exactly how the prose hand-off this ledger
    # replaced stayed green for four days.
    def with_ledger(**steps):
        return {**doc, "re_family_ledger": {
            "ticket": "T-1557",
            **{k: {"ticket": t, "settled": settled} for k, (t, settled) in steps.items()}}}

    def gate(d, st, ch=None):
        return every_work_order_names_a_live_ticket(d, st, ch or {})

    live = with_ledger(the_programme=("T-9000", False), who_makes_the_moves=("T-9003", False))
    gate(live, {**states, "T-9000": "open", "T-9003": "claimed"})
    gate(live, {**states, "T-9000": "blocked-owner", "T-9003": "review"})
    for dead in ("done", "withdrawn"):
        fires(f"an unsettled re-family step ordered by a {dead} ticket",
              lambda d=dead: gate(live, {**states, "T-9000": d, "T-9003": "open"}))
    fires("an unsettled re-family step ordered by an id that is not a ticket at all",
          lambda: gate(live, {**states, "T-9003": "open"}))
    fires("an unsettled re-family step ordered by nobody at all",
          lambda: gate(with_ledger(the_programme=(None, False)), states))
    # A SETTLED STEP ORDERS NOBODY, so a closed ticket on one is not a hole — that is
    # what finishing the programme looks like and the gate must not block it.
    gate(with_ledger(the_programme=("T-9000", True)), {**states, "T-9000": "done"})
    # A SPLIT PROGRAMME IS LIVE WHILE A PIECE OF IT IS, and dead the moment none is.
    # Both halves are asserted: accepting `split` unconditionally would be the stranding
    # the bucket sweep refuses, and refusing it would strand the programme.
    split = with_ledger(the_programme=("T-9000", False))
    kin = {"T-9000": ["T-9001", "T-9002"]}
    gate(split, {**states, "T-9000": "split", "T-9001": "done", "T-9002": "claimed"}, kin)
    fires("a split re-family programme whose every piece has closed",
          lambda: gate(split, {**states, "T-9000": "split", "T-9001": "done",
                               "T-9002": "withdrawn"}, kin))
    fires("a split re-family programme with no pieces at all",
          lambda: gate(split, {**states, "T-9000": "split"}))
    # AND A SPLIT PIECE IS LIVE THROUGH ITS OWN PIECES (T-1575): the programme's only
    # live work two levels down keeps it owned, and closing that last grandchild ends it.
    deep = {"T-9000": ["T-9001", "T-9002"], "T-9002": ["T-9004", "T-9005"]}
    gate(split, {**states, "T-9000": "split", "T-9001": "done", "T-9002": "split",
                 "T-9004": "review", "T-9005": "open"}, deep)
    fires("a split re-family programme whose split piece's pieces have all closed",
          lambda: gate(split, {**states, "T-9000": "split", "T-9001": "done",
                               "T-9002": "split", "T-9004": "done",
                               "T-9005": "withdrawn"}, deep))

    # WHERE THE PROGRAMME FINISHES (T-1597). Every case is built by hand rather than taken
    # off the shipped book, because the shipped book is AT its fixpoint and a gate can only
    # be proved by the states it refuses.
    def prog(spent=129, **over):
        step = {"settled": True, "moves_the_rule_still_yields": 0, "people_still_held": 9,
                "buckets_they_are_held_in": 2,
                "and_what_holds_each_of_them": [{"refusal": "a_rule", "people": 9}],
                "the_finish_line": "the rule's fixpoint",
                "the_ruling_that_set_it": "the owner, 2026-09-25",
                "what_becomes_of_them": "nothing", "what_would_reopen_it": "a wider rule"}
        step.update(over)
        return {"re_family_ledger": {
            "the_programme": step,
            "the_held_surplus": {"people_still_held": 9, "buckets_refused": 2},
            "who_makes_the_moves": {"the_rule_yields": 129, "spent": spent}}}

    finish = the_programme_finishes_where_the_rule_does
    assert "settled at its rule's fixpoint" in finish(prog()), finish(prog())
    # The two other healthy ends: nobody left held, and moves still to spend.
    empty = prog(people_still_held=0, buckets_they_are_held_in=0,
                 and_what_holds_each_of_them=[])
    empty["re_family_ledger"]["the_held_surplus"] = {"people_still_held": 0,
                                                     "buckets_refused": 0}
    assert "settled with nobody held" in finish(empty), finish(empty)
    assert "unsettled with 4" in finish(prog(spent=125, settled=False,
                                             moves_the_rule_still_yields=4))
    fires("a programme step the ledger does not state at all",
          lambda: finish({"re_family_ledger": {}}))
    fires("a programme settled while the rule still yields a move",
          lambda: finish(prog(spent=125, moves_the_rule_still_yields=4)))
    fires("a programme unsettled at the rule's own fixpoint",
          lambda: finish(prog(settled=False)))
    fires("a programme whose remainder disagrees with the moves the ledger has spent",
          lambda: finish(prog(spent=100)))
    fires("a programme whose count of the held disagrees with the book's own surplus",
          lambda: finish(prog(people_still_held=8)))
    fires("a programme that does not say which refusal holds every one of the held",
          lambda: finish(prog(and_what_holds_each_of_them=[{"refusal": "a_rule",
                                                            "people": 4}])))
    fires("a programme settled over more refused buckets than the book refuses",
          lambda: finish(prog(buckets_they_are_held_in=3)))
    for field in ("the_finish_line", "the_ruling_that_set_it", "what_becomes_of_them",
                  "what_would_reopen_it"):
        fires(f"a programme settled with people still held and no {field}",
              lambda f=field: finish(prog(**{f: "   "})))
    # AND THE BOOK AS IT SHIPS IS AT THE FIXPOINT, which is the state the ruling settled:
    # the rule is spent in full, nobody moves again, and the residue is written down. This
    # is asserted against the book built WITH the moves on disk — `shipped` above is the
    # no-moves fixture, where the programme is correctly unsettled with all 129 to spend.
    finish(shipped)
    assert shipped["re_family_ledger"]["the_programme"]["settled"] is False
    on_disk = build(data, _fills_on_disk(), occ, moves=_moves_on_disk())
    prg = on_disk["re_family_ledger"]["the_programme"]
    assert prg["settled"] is True and prg["moves_the_rule_still_yields"] == 0, prg
    assert prg["people_still_held"] == sum(
        r["surplus_still_held"] for r in on_disk["recut_refusals"]), prg
    assert sum(r["people"] for r in prg["and_what_holds_each_of_them"]) \
        == prg["people_still_held"], prg
    assert finish(on_disk).startswith("the re-family programme is settled at its rule's "
                                      "fixpoint"), finish(on_disk)


    # THE CUT'S OWN REFUSALS (T-1672). A cell cut into bands is a finer address for work
    # already counted, and every way that could stop being true is red here. The fixtures
    # bend the committed cut — the SOUTH's `warehouses_freight`, the one cell the inventory
    # bands today — because bending the real one is what proves the real one is held.
    def banded(mutate):
        bent = copy.deepcopy(data)
        cut = bent["inventory"]["district_group_bands"]["warehouses_freight"]["south"]
        mutate(cut)
        return lambda: structure_buckets(bent["inventory"], bent["programme"], occ)

    def band_of(cut, band_id):
        return next(b for b in cut["bands"] if b["id"] == band_id)

    # The committed cut itself: two bands, and the closed one holds the sheds.
    cells = {b["key"]: b for b in structure_buckets(
        data["inventory"], data["programme"], occ)["buckets"]}
    bank = cells["structures/warehouses_freight/south/river_bank"]
    line = cells["structures/warehouses_freight/south/street_line"]
    assert bank["to_build"] == 0 and bank["target"] == bank["standing"], bank
    assert all(i.startswith("south_bank_shed_dearborn_") for i in bank["band_members"]), bank
    assert "structures/warehouses_freight/south" not in cells, "the cut cell still orders as one"
    assert line["to_build"] == data["programme"]["remaining"]["by_district_group"]["south"][
        "warehouses_freight"], line
    fires("a cell cut into one band, which is not a cut",
          banded(lambda cut: cut.__setitem__("bands", cut["bands"][:1])))
    fires("a cell cut with two remainder bands, so its order would be ordered twice",
          banded(lambda cut: cut["bands"].append({**band_of(cut, "street_line"),
                                                  "id": "second_remainder"})))
    fires("a closed band whose id prefix matches no standing record",
          banded(lambda cut: band_of(cut, "river_bank").__setitem__(
              "member_id_prefix", "no_such_roof_")))
    fires("a closed band that names its members by prefix and still claims an order",
          banded(lambda cut: band_of(cut, "river_bank").__setitem__("owes", "one shed")))
    fires("a closed band that says nothing about what closed it",
          banded(lambda cut: band_of(cut, "river_bank").pop("closed_by")))
    fires("a band carrying no owning ticket",
          banded(lambda cut: band_of(cut, "street_line").pop("owning_ticket")))
    fires("a band that names its members neither by prefix nor as the rest of the cell",
          banded(lambda cut: band_of(cut, "street_line").__setitem__("members", "some of it")))
    # A PREFIX THAT REACHES INTO ANOTHER CELL. The four north-bank sheds at the same reach
    # are the nearest thing to this band that is not in it — same plate, same drawbridge,
    # the other side of the water — so they are the fixture: a band may only hold roofs the
    # programme has classified into the cell it cuts.
    fires("a closed band whose prefix reaches a roof in another division",
          banded(lambda cut: band_of(cut, "river_bank").__setitem__(
              "member_id_prefix", "north_bank_shed_dearborn_")))
    fires("bands that do not add back up to their cell, which would be a quiet re-budget",
          lambda: bands_add_back_up_to_their_cell(
              [{**bank, "target": bank["target"] + 1}, line],
              {"target": bank["target"] + line["target"], "standing": 0, "to_build": 0},
              "warehouses_freight", "south"))
    fires("a band whose own target, standing and order do not close",
          lambda: bands_add_back_up_to_their_cell(
              [{**line, "to_build": line["to_build"] + 1, "standing": line["standing"] - 1,
                "target": line["target"] + 1}],
              {"target": line["target"] + 1, "standing": line["standing"] - 1,
               "to_build": line["to_build"] + 1}, "warehouses_freight", "south"))

    # THE SEATING JOIN'S FOUR REFUSALS (T-1620). The book reads two files it does not
    # write, and every one of its seat figures is a sum across them — so a file that
    # moves under it must be RED here rather than quietly re-summed into a total that
    # still looks right. The four are: a pass whose own seated-plus-owed misses its
    # scope; a pass whose adoptions and slots miss its seated; a second pass offered a
    # different number of rows from the one the first handed on; and a slot count that
    # disagrees with the slot rows carried beside it. None of them can be repaired here,
    # because the repair is re-deriving the file that moved.
    def seats_with(pass_key, **counts):
        bent = copy.deepcopy(data)
        bent[pass_key]["counts"].update(counts)
        return lambda: seats_against_roofs(bent, structure_buckets(
            bent["inventory"], bent["programme"], occ))

    # The literal is a tripwire and not a target: it moves when a seating pass rules
    # differently, and the ruling is what has to be argued for. A seating file that moves
    # under this join must be RED, not quietly re-summed, so restate it against the files
    # whenever it moves. It was 176; T-1611 re-dealt six platted-block yard buildings into
    # rear cottages, which the deal adopted, taking it to 182; T-1622 lost two of those to
    # the street-face adoption policy and T-1626 gave them back to the households that had
    # asked, holding it at 184; then T-1623 refused the four slots the platted deal still
    # asked for on the lots the schedule's own sizing keeps open, taking it to 180. T-1651
    # takes it to 181 — the platted pass's 109 plus the off-plat pass's 72, both read off
    # the committed files. THE RULING BEHIND THAT ONE SEAT: the street-face business deal
    # now prefers a roof the reconstruction raised as a house of trade, so the dwellings it
    # holds changed, and the platted deal — which takes from the same pool of anonymous
    # roofs and may not read the business deal's allocation — reached one more
    # `tradesman_dwellings` seat in the South Division. Nothing was raised for it and no
    # roof moved; a dwelling the business deal had been standing a shop in went back to the
    # households. The two deals running blind to one pool is T-1669.
    #
    # T-1707 TAKES IT TO 211, AND THIRTY OF THE SEATS ARE SLOTS. The platted pass goes
    # 109 -> 139 and the off-plat pass holds at 72. Nothing was adopted that was not adopted
    # before: all 30 of the new seats are SLOTS, which is the first time either pass has
    # carried one since T-1623 refused the last four. The ruling behind them is a ruling
    # about GROUND and not about households. Carrying the Original Town's seven north-south
    # columns from their terrain clip at N -400 to Madison Street let
    # `generate_plat_lots.py` emit the plat's last tier — six blocks and 48 lots between
    # Market and State — and the 665-roof programme marks all six `open` with 27 roofs of
    # headroom each, where the South Division's only open blocks before were two South Water
    # blocks whose free lots T-1623's rule reserves. So the deal could ask, and it asked 19
    # merchant and professional households and 11 tradesmen's onto them. A slot is a request
    # and not a roof: T-1708 raises them.
    #
    # T-1733 AND T-1716 TOGETHER TAKE IT TO 212, AND THIRTY-ONE OF THE SEATS ARE SLOTS.
    # Two rulings about GROUND and one standing roof, composing in opposite directions on
    # the same platted pass, which went 139 -> 140.
    #
    # T-1733 added two. `blk_lake_clinton` is plat block 28, between Clinton and Canal, and
    # it stands on West Division ground while being emitted by the Original Town's grid; the
    # owner ruled on 2026-09-23 (T-1479, option a) that the West Division's own arrangement
    # may cut a block printing no lot figures of its own, at `inferred`, so the cell went
    # from eight lots four-to-a-face to TEN in two columns fronting Clinton and Canal. Two
    # more lots on a block the 665-roof programme already marks `open`, and the deal asked
    # for both: the Adams household on the Canal face and the Baxley household on the
    # Clinton face. This is the same shape of cause as T-1707's and it is worth saying so:
    # a ruling about GROUND, not about households. Nothing was adopted that was not adopted
    # before — 109 both sides of the change — and no roof moved a metre.
    #
    # T-1716 took one back. The keeper's quarters at the Chicago light is a standing roof
    # the programme counts, so the family plan it draws for `blk_washington_clark` falls
    # from two principal roofs to one, and the household that had the second slot goes back
    # on the owed list. Nothing was raised on the plat and no seat moved: one request the
    # plan no longer has room for is withdrawn, and it is withdrawn in writing.
    #
    # AND T-1741 TAKES IT TO 232, WITH TWENTY MORE SLOTS, ON THE NORTH SIDE THIS TIME. The
    # same shape again, and for the same kind of reason: a ruling about GROUND, not about
    # households. Kinzie's Addition stood with twenty-seven blocks and no lot line in any of
    # them — no lot rule had been read for that plat — so the whole North Division's headroom
    # was 0 and T-1205 is blocked-tech on it. Reading the rules Wright actually draws inside
    # the Addition's cells cut 60 lots on the five he rules, the programme marks them `open`,
    # and the platted pass goes 140 -> 160: eleven households onto blk_indiana_north_wolcott
    # and nine onto blk_indiana_north_cass, thirteen of them tradesmen's, six merchant and
    # professional and one labourer's (T-1744 corrected the "eleven labourers'" this comment
    # and L270 first carried). All twenty are SLOTS.
    # A slot is a request and not a roof: T-1742 raises them.
    #
    # T-1734 added the other two, from the same ruling and the second of the same pair of
    # blocks. `blk_randolph_clinton` is plat block 45, between Clinton and Canal one tier
    # south of 28, and it could not be cut with its twin: a block parcel had already dealt
    # seven roofs onto it, argued face by face against Randolph and Washington, and the
    # transpose removes both of those faces. T-1734 re-argued that deal onto Clinton and
    # Canal — the two better cottages to Canal, which the committed street hierarchy grades
    # `ordinary` against Clinton's `light`, exactly as the first argument had put them on
    # Randolph against Washington — and the cell then moved. Its two new lots took two
    # slots, the Adams and Bennett households, both on the Canal face. Again nothing was
    # adopted that was not adopted before: 109 across all four of these changes. What DID
    # move, and is the difference from 28, is the seven roofs themselves — a dealt roof
    # stands where its parcel's slot puts it off its own lot's edge, so re-cutting the block
    # re-derived every position and rotation on it. No mesh changed and nothing was rebaked.
    #
    # AND T-1736 TAKES IT TO 235, WITH THE FIRST BUILD ON THE LAST TIER. Every change
    # above was a ruling about GROUND; this one is a BUILD, and it moves the deal the other
    # way about. `blk_washington_clark`'s two cottages now stand, so the block has no
    # principal room left to offer and its last slot goes: the platted pass runs
    # 162 -> 163 with 111 adoptions against 109, and 52 slots against
    # 53. 31 adopted seats move roof behind the two Beaubien households that take the
    # new cottages — the adoption step outbids the slot step for a quiet street, which is the
    # T-1622 precedence — every one of them in the South Division and none left roofless.
    # The two slot-holders the build displaced end ADOPTED on blk_lake_clark, and
    # hh_chamberlain_l_c, who had no lot at all, takes the slot the cascade frees on
    # blk_washington_wells. Read at the chain's fixpoint, not one pass in.
    #
    # AND T-1747 TAKES IT TO 237, WITH THE FIRST BUILD IN KINZIE'S ADDITION. Two of the
    # eleven slot requests standing against `blk_indiana_north_wolcott` are raised, and
    # unlike the Clark block this one keeps its slots: it is dealt 2 principal roofs out of
    # a plan holding 33, so it still has room to offer and the pass runs 163 -> 165 with
    # 113 adoptions against 111 and the SAME 52 slots. Neither cottage went to the
    # household that asked — hh_allin_richard and hh_almond_axtell_2 adopted them off the
    # block to the east, and hh_baily_john and hh_bailly_joseph end holding slots there
    # instead — which is the T-1622 precedence again and is recorded in L293. Off-plat is
    # unmoved at 72, so the total is 165 + 72. Read at the chain's fixpoint, not one pass in.
    #
    # AND T-1708 TAKES IT TO 242, WHICH IS THE BIGGEST STEP THIS JOIN HAS TAKEN. All seven
    # slot requests standing against `blk_washington_wells` are raised, plus four yard
    # buildings, and the block behaves like the Clark one rather than the Addition one: its
    # principal room is dealt out, so it offers no slot afterwards. The platted pass runs
    # 165 -> 170 with 120 adoptions against 113 and 50 slots against 52 — 26 of the 50 still
    # on this tier — and off-plat is unmoved at 72, so the total is 170 + 72. The cascade is
    # total this time and not partial: NOT ONE of the seven households the block was sized
    # against is seated on it. All seven re-seat as slots on blk_washington_lasalle and
    # blk_washington_market, the seven roofs go to the seven the clause order scores higher on
    # these lots, and five households that had no lot at all reach one. That is the T-1622
    # precedence a third time, and it is recorded in L298. Read at the chain's fixpoint, not
    # one pass in — this one took eight passes and oscillated for four of them.
    #
    # AND T-1735 TAKES IT TO 249, with the tier's south-west block. The eleven roofs on
    # `blk_washington_lasalle` answer the seven slot requests T-1708's own cascade re-seated
    # onto this block and blk_washington_market, so the two deals are one argument read in two
    # steps: Wells raised its seven and pushed its seven on, LaSalle raises the seven that
    # arrived. The gain is SEVEN this time and not four, and the reason is the lap rather than
    # the deal: T-1756 landed on `dev` first and its own cascade had already absorbed the
    # vacancies the earlier laps of this branch were paying for, so there was nothing left to
    # cascade away. The platted pass runs 170 -> 177 with 129 adoptions against 122 and 48
    # slots unmoved, 1,301 handed on against 1,308, and off-plat is unmoved at 72, so the total
    # is 177 + 72. What the tier's remainder does is NOT what it did a paragraph above: its
    # slot count is unmoved at 26 and Clark's at 5, because the seven this block was sized
    # against re-slot onto its neighbours — blk_washington_dearborn takes seven where
    # blk_washington_lasalle had them — as fast as its own roofs take them off the table. What
    # moves is the BAND, 14 merchant and professional against 12 tradesmen's becoming 14
    # tradesmen's against 12. That is the T-1622 precedence a fourth time, and it is recorded
    # in L300. Read at the chain's fixpoint, not one pass in, and read off the committed seats
    # files rather than predicted: 1835_platted_seats.json counts seated 177 (129 adopted, 48
    # slots, 1,301 handed on) and 1835_off_plat_seats.json counts seated 72 of the 1,301 it was
    # handed.
    #
    # AND T-1751 TAKES IT TO 249 AND LEAVES IT THERE, WHICH IS THE CLEANEST SUBSTITUTION THIS
    # ROW HAS RECORDED. `blk_washington_franklin` was dealt out to its lot ceiling — seven
    # dwellings and six yard buildings — so the platted pass runs 177 -> 177 with 138 adoptions
    # against 131 and 39 slots against 46, the off-plat pass is unmoved at 72, and the rows
    # handed on stand at 1,301. Seven requests became seven roofs and the seat total did not
    # move a place: the gain is in the ADOPTION table and the loss is in the SLOT table, which
    # is what a block dealt to its ceiling does — it can hold no further request, so its own
    # seven had to go somewhere and every one of them found an `open` block in its own clause
    # and division. NOT ONE of the seven the block was sized against is seated on it:
    # hh_beaubien_monique re-slots onto blk_washington_clark, hh_beddlecome_ash, hh_beech_reuben,
    # hh_benediet_loma, hh_chattin_clark and hh_chevalier_joseph onto blk_washington_dearborn,
    # hh_chiney_ralph onto blk_washington_market. The roofs go to hh_bailly_esther,
    # hh_baines_robert, hh_bates_john_jr, hh_beaubien_caroline, hh_beeson_william,
    # hh_bench_reuben and hh_brookes_samuel, and 59 households change roof behind them — the
    # largest cascade any deal here has set off. That is the T-1622 precedence a fifth time, and
    # it is recorded in L304. Read at the chain's fixpoint, not one pass in: this one took SEVEN
    # runs of the whole chain — the address book, the platted deal, the keeper naming, the block
    # infill, the roof re-audit and this book each feeding the next — and it read 174 seats for
    # four of those passes before it settled at 177.
    # 249 -> 255 on 2026-10-01 (T-1783): opening the three lot-ruled outer West blocks gave
    # the platted pass six more seats, 177 -> 183 — three adoptions of the three cottages
    # built on blk_west_randolph_des_plaines and three slots asked of blk_west_lake_canal's
    # three dealt ones (T-1773's warehouse took that block's lot 1) — and the off-plat pass
    # stands at 72.
    # 255 -> 256 on 2026-10-01 (T-1827): `recon_1835_west_046`, re-dealt from a freight
    # shed to an H2, is a standing roof the merchant-and-professional clause admits, so the
    # platted pass adopts it on blk_west_randolph_des_plaines#01 (183 -> 184); the household
    # is a letter-list name the keeper pass refuses to name (T-0379), as on west_008.
    # 256 -> 255 on 2026-10-02 (T-1952): the North's H3 boarding house on
    # blk_indiana_north_cass#01 takes the lot hh_beaubien_john_s's D5 slot stood on. He
    # re-slots onto blk_indiana_north_wolcott#07, the wolcott requests step down a lot each
    # and hh_bourassa_lon is handed on; the schedule's re-apportioned plan moves the South's
    # Washington-tier slots the same way, hh_berger_f_c in and hh_cleaveland_wm_p out. The
    # house itself is adopted by no one (no North banded row is admitted by the one clause
    # that takes an H3), so the platted pass reads 184 -> 183 at the chain's fixpoint.
    # 255 -> 254 on 2026-10-02 (T-1950): the third H3 boarding house on blk_washington_clark
    # takes lot 0, which hh_beaubien_monique's D7 slot had asked for; she moves along the
    # block, the slots behind her shift a lot, and hh_berger_f_c, left with only kept-open
    # lots, is owed to T-1614 (183 -> 182 platted seats, L270, L345).
    # 254 -> 251 on 2026-10-02 (T-1951): the South's last three planned H3s stand on
    # blk_washington_market#04/#05 and blk_washington_dearborn#02, all three lots a slot
    # request had asked for; hh_bently_wm_t, hh_benton_datas_e and hh_clarke_h_b are owed
    # to T-1614 (182 -> 179 platted seats, L270, L349).
    # 251 -> 252 on 2026-10-02 (T-1989): `recon_1835_west_013`, re-dealt from a utility shed
    # to a D2 on Lake west of Canal, is a standing roof `labourer_dwellings` admits off the
    # plat, so the off-plat pass adopts it for hh_rc_doyle_ellen (72 -> 73, L271, L265).
    # 252 -> 251 on 2026-10-04 (T-1679): the Mansion House moves one lot east onto the
    # D2 shanty's lot and the shanty takes the Dearborn corner, where `labourer_dwellings`
    # seats no one; hh_clark_john_k and nine more step down one roof each and
    # hh_humphrey_fre_lemuel is owed to T-1614 (179 -> 178 platted seats, L270, L373).
    # 251 -> 255 on 2026-10-05 (T-2132): plat block 44 is cut on its own two printed depths
    # and its four houses raised; the four households that asked for them are seated on
    # standing West roofs and nobody is handed on (178 -> 182 platted seats, L270, L313).
    # 255 -> 289 on 2026-10-05 (T-2144): the School Section tier's five South blocks join
    # the plat on the owner's T-1755 ruling and the schedule gives them room, so 34
    # households the platted pass had handed on are dealt a slot there (182 -> 216 platted
    # seats, L270) — requests T-2145..T-2147 raise.
    # 289 -> 295 on 2026-10-05 (T-2143, merged over T-2144): Canal and West Water are carried to Madison, plat
    # block 51 comes onto the layer and its six houses are raised; the six households that
    # asked for them are seated on standing West roofs and nobody is handed on (216 -> 222
    # platted seats, L270, L313).
    # 295 -> 308 on 2026-10-05 (T-1746, merged over T-2143): the North's 26 owed dwellings stand
    # south of Michigan Street instead of on Kinzie's Addition; the thirteen households whose
    # slots stood on its two blocks are seated off the plat under standing North roofs, and
    # thirteen more owed North households beside them (222 -> 209 platted seats, 73 -> 99
    # off-plat, L270, L271, L393).
    # 308 -> 311 on 2026-10-06 (T-2148, merged over T-1746): Clinton, Jefferson and Des
    # Plaines are carried to Madison, plat blocks 48-50 come onto the layer and block 50's
    # thirteen roofs are raised; the four households that asked for its houses are seated
    # on standing West roofs, older households adopt the new ones, and the platted pass
    # seats three more at its fixpoint (209 -> 212 platted seats, 99 off-plat, L270, L394).
    # 311 holds on 2026-10-08 (T-2146, merged over T-2165 and T-2167): thirteen Wells-block
    # houses dealt to the post-T-2148 requests; older households adopt them, the requesters
    # are seated on standing roofs or re-slot on block 81, and the settled pass seats 212 on
    # the plat and 99 off it, as before.
    # 311 -> 313 on 2026-10-08 (T-2147, re-dealt over T-2146): block 81's six dwellings;
    # six older households adopt them and the walk settles two seats up on the plat
    # (212 -> 214 platted seats, 99 off-plat, L270, L397).
    # 313 -> 312 on 2026-10-08 (T-2170, lapped over T-2147): the North's five owed A2 barns
    # stand behind the Wolcott-Kinzie core's houses, so the 668-roof schedule re-deals the
    # roofs it held for them; the South's two remaining slot requests (block 81 lot 1, block
    # 95 lot 1) are no longer planned, one household is dealt the D2 slot the new plan puts on
    # block 95 and the settled pass seats 213 on the plat and 99 off it (L270, L407).
    # 312 -> 313 on 2026-10-08 (T-2174, on top of T-2170): an F2 warehouse takes
    # blk_south_water_dearborn's last unreserved free lot and the schedule returns that
    # block's D2 and D6 to the South balance; the School Section tier re-deals a D5 slot on
    # block 81 and a D6 on block 95 (213 -> 214 platted seats, 99 off-plat, L270, L406).
    # 313 -> 314 on 2026-10-09 (T-2195, lapped over T-2176, which had held it at 313 by
    # building block 81's D5 and block 95's D6): the Market wedge's four lots open a D5, an F4
    # and an H3 in the schedule, and the D5 is dealt as a slot on the wedge's lot 7 to one
    # household the deal had handed on (214 -> 215 platted, 99 off-plat, L270, L409).
    assert seats_against_roofs(data, structure_buckets(
        data["inventory"], data["programme"], occ))["seated"] == 314
    fires("a seating pass whose seated and owed miss its own scope",
          seats_with("platted_seats", owed=1))
    fires("a seating pass whose adoptions and slots miss its own seated count",
          seats_with("platted_seats", roofs_adopted=99))
    fires("a second seating pass offered rows the first did not hand on",
          seats_with("off_plat_seats", rows_in_scope=7, seated=7, owed=0))
    # The fixture bends the count AWAY from the rows, in whichever direction the files
    # currently sit: since T-1707 the platted pass carries slot rows on the plat's last tier
    # — 19 of them since T-1751 dealt blk_washington_franklin out to its ceiling, which took
    # that block's own seven off the table and left 7 on blk_washington_dearborn, 7 on
    # blk_washington_market and 5 on blk_washington_clark, the tier's first FALL in slots — so
    # claiming ONE of them is as much a
    # disagreement as claiming one where the pass carried none — which is what this fixture said until that ticket, when T-1623 had
    # refused the last four and the count stood at zero.
    fires("a slot count that disagrees with the slot rows carried beside it",
          seats_with("platted_seats", slots_requested=1, roofs_adopted=99))
    dropped = copy.deepcopy(data)
    dropped["platted_seats"]["counts"] = {}
    fires("a seats file with no counts at all",
          lambda: seats_against_roofs(dropped, structure_buckets(
              dropped["inventory"], dropped["programme"], occ)))

    # T-1968: a filler's rows go back where they stood, whoever ran last.
    ledger = [{"ticket": "T-A", "bucket": "a"}, {"ticket": "T-B", "bucket": "b"},
              {"ticket": "T-C", "bucket": "c"}]
    new_b = [{"ticket": "T-B", "bucket": "b2"}, {"ticket": "T-B", "bucket": "b3"}]
    assert [f["bucket"] for f in splice_fills(ledger, {"T-B"}, new_b)] == \
        ["a", "b2", "b3", "c"], "a filler's rows moved off their place in the ledger"
    assert [f["bucket"] for f in splice_fills(ledger, {"T-D"}, [{"ticket": "T-D",
            "bucket": "d"}])] == ["a", "b", "c", "d"], "a first fill did not append"
    assert [f["bucket"] for f in splice_fills(ledger, {"T-B"}, [])] == ["a", "c"], \
        "a filler that built nothing kept its rows"
    once = splice_fills(ledger, {"T-B"}, new_b)
    assert splice_fills(once, {"T-B"}, new_b) == once, "splicing is not a fixed point"

    # T-2187: the men ruling discharges only what the town already holds of the model's
    # adult men — a town short of them keeps that much on order, and the walk is the same
    # walk on every build.
    def man_cell(key, division, target, order, filled=0, htype="family"):
        return {"key": key, "target": target, "to_reconstruct": order, "filled": filled,
                "owning_ticket": ADULT_MEN_OWNER,
                "axes": {"sex": "male", "age_band": "20_29", "division": division,
                         "household_type": htype, "trade": "none"}}
    short = [man_cell("m/a", "south", 60, 30), man_cell("m/b", "west", 40, 20)]
    ruled = adult_men_ruling(short, {"named_adult_men": 80, "by_division": {},
                                     "named_men_with_no_age_not_counted": 0})
    assert ruled["the_town_still_lacks"] == 20 and ruled["discharged"] == 30, ruled
    assert [b["to_reconstruct"] for b in short] == [0, 20], "the walk is not in key order"
    held = [man_cell("m/a", "south", 60, 30), man_cell("m/b", "west", 40, 20, htype="lodging")]
    assert adult_men_ruling(held, {"named_adult_men": 500, "by_division": {},
                                   "named_men_with_no_age_not_counted": 0})["discharged"] == 30
    assert held[1]["to_reconstruct"] == 20, "the men ruling discharged a lodging cell"
    assert "adult_men_ruling" in doc, "the committed book carries no ruling on the adult men"
    # T-2234: A WITHDRAWN ADMISSION TAKES ITS ORDER WITH IT, AND NO MORE THAN IT ORDERED.
    cell = lambda: {"key": "persons/female/20_29/north/family/none", "to_reconstruct": 4,
                    "filled": 4}
    ruled_cell = cell()
    family_ruling_orders([ruled_cell], {"orders": {ruled_cell["key"]: 3}},
                         Counter({ruled_cell["key"]: 2}), {ruled_cell["key"]: 1})
    assert (ruled_cell["ordered_by_the_family_ruling"], ruled_cell["to_reconstruct"],
            ruled_cell["filled"]) == (2, 6, 6), ruled_cell
    fires("a withdrawn house takes more from a cell than the ruling ordered there",
          lambda: family_ruling_orders([cell()], {"orders": {cell()["key"]: 1}}, Counter(),
                                       {cell()["key"]: 2}))
    fires("the ruling's houses fill past an order its withdrawals cut",
          lambda: family_ruling_orders([cell()], {"orders": {cell()["key"]: 2}},
                                       Counter({cell()["key"]: 2}), {cell()["key"]: 1}))

    # T-2194: the store ruling discharges only the order above one household a standing
    # store roof, never below what a cell has filled, and leaves a division's dwelling rows
    # alone.
    def hh_cell(htype, division, target, order, filled=0):
        return {"key": f"households/{htype}/{division}", "target": target,
                "to_reconstruct": order, "filled": filled,
                "axes": {"household_type": htype, "division": division}}
    def roof_cell(division, standing):
        return {"key": f"structures/stores_mixed_use/{division}", "standing": standing}
    cells = [hh_cell("store_residence", "south", 62, 44), hh_cell("store_residence", "west", 9, 8, 7),
             hh_cell("family_dwelling", "south", 258, 184)]
    ruled = store_residence_ruling(cells, [roof_cell("south", 42), roof_cell("west", 6)])
    assert [b["to_reconstruct"] for b in cells] == [24, 7, 184], cells
    assert ruled["discharged"] == 21 and ruled["still_owed"] == 24, ruled
    assert store_residence_ruling(cells[2:], [roof_cell("south", 42)]) is None, \
        "a book with no store rows carried a store ruling"
    assert "store_residence_ruling" in doc, "the committed book carries no ruling on the store rows"

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
