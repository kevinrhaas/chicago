#!/usr/bin/env python3
"""Who lived and worked where in July 1835, written once as rules with their evidence.

The owner asked for it in one sentence: *"spread the businesses and residences and all
other civic and other structures across the city correctly along lot lines and corners
and lots … I think you will have multiple buildings per lot in many cases in the major
streets … do what you can to make the location of reconstructed businesses and residents
as reasonable and accurate as a historian would."*

The project already held most of that policy — in six different places, none of them
readable as a rule:

    T-0024  the face rule's non-dwelling clause — a store never on a `light` street
    T-0023  the end rule — the better roof nearer the drawbridge
    T-0022  the frontage-fabric ruling — log trade buildings DO stand on principal streets
    T-0079  the density standard — three party-line units per lot
    T-0213  the trade share by street class
    K1      "businesses toward the river and the built streets, residences further out"

Three of those are modules that each re-typed the same numbers. This one writes the
policy down, gives the numbers ONE home, and hands the seating tickets a file instead of
a memory.

## What is authored here and what is read from the tree

The CLAUSES are authored — they are this project's reading of how an 1835 lake town
arranged itself, and every one of them carries its tier and its evidence. Everything
printed BESIDE a clause is re-read from the committed tree on every run: how many of its
evidence records stand, what class of street each is nearest, and the setbacks they keep.
`--check` rebuilds the file and refuses any drift between the two, which is what makes a
clause a reading of the record rather than a preference about frontage.

## The one-source-of-truth clause, and it is the part with teeth

Five numbers were typed into four modules, under seven names. They now live in `constants` and the modules
import them:

    street_line_m        2.71   STREET_LINE_M         measure_frontage_fabric
    party_line_unit_m    6.072  PARTY_LINE_UNIT_M     measure_end_rule
    trade_letters        C F W  TRADE_LETTERS         measure_frontage_fabric
                                LIGHT_STREET_ZERO     generate_block_infill
    non_dwelling_letters CFTWI  NON_DWELLING          measure_face_rule
                                NON_DWELLING_LETTERS  generate_block_infill
    commercial_letter    C      COMMERCIAL            measure_face_rule

Assertion 5 below reads each module's source and fails if one of them carries its own
copy of a constant again. A single source of truth that nothing checks is a comment.

## The outliers are evidence, and the policy notes them

A documented building standing against its own clause is not a fault in the record; it is
the record telling you something the clause does not say. `--score` finds them by
measurement and this module supplies the reason for each by hand — and assertion 3
refuses an outlier nobody has explained, so a new one cannot appear silently. Eleven
stand today and they fall into three groups: the unplatted military reservation, which
has no street frontage to take a better or worse face of; Wolf Point and the north bank,
where the nearest committed centreline is across the river; and the north division, which
in July 1835 has almost no street control at all.

**No roof moves.** This module reads; it writes one file and never a structure.

    tools/placement_policy_1835.py              the policy, with its witness
    tools/placement_policy_1835.py --score      every documented roof against its clause
    tools/placement_policy_1835.py --build      rewrite data/…/1835_placement_policy.json
    tools/placement_policy_1835.py --check      exit 1 on drift or a broken assertion
    tools/placement_policy_1835.py --self-test  break the assertions and watch them fire
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TOOLS = ROOT / "tools"

POLICY = DATA / "reconstruction" / "1835_placement_policy.json"

CLASSES = ("principal", "ordinary", "light")

# ------------------------------------------------------------------ the constants
#
# `value` is the number as it stood in the module that used to own it; `read_by` is the
# module that imports it now, and assertion 5 holds that module to it.

CONSTANTS = [
    {"name": "street_line_m", "value": 2.71, "unit": "m",
     "read_by": [{"module": "tools/measure_frontage_fabric.py",
                  "name": "STREET_LINE_M"}],
     "derivation": "the empty gap in the town's own setback distribution, at its "
                   "midpoint — re-derive with measure_frontage_fabric.py --setbacks. A "
                   "building at or inside this stands ON the street line; anything "
                   "further back stands in the block behind it."},
    {"name": "party_line_unit_m", "value": 6.072, "unit": "m",
     "read_by": [{"module": "tools/measure_end_rule.py",
                  "name": "PARTY_LINE_UNIT_M"}],
     "derivation": "the mean width of the committed party-line units, from the core "
                   "density standard's derivation in tools/reconcile_665.py: eighteen "
                   "units, 5.04 m to 6.75 m, mean 6.072 m."},
    {"name": "trade_letters", "value": ["C", "F", "W"], "unit": "family letters",
     "read_by": [{"module": "tools/measure_frontage_fabric.py",
                  "name": "TRADE_LETTERS"},
                 {"module": "tools/generate_block_infill.py",
                  "name": "LIGHT_STREET_ZERO"}],
     "derivation": "the families that make a building a place of trade: C stores and "
                   "mixed use, F warehouses and freight, W workshops. T is lodging and "
                   "is deliberately not one of them; --trade prints both readings. The "
                   "same three letters are the ones the documented record puts a zero "
                   "on for light streets, which is why the block generator reads them "
                   "under its own name."},
    {"name": "non_dwelling_letters", "value": ["C", "F", "T", "W", "I"],
     "unit": "family letters",
     "read_by": [{"module": "tools/measure_face_rule.py", "name": "NON_DWELLING"},
                 {"module": "tools/generate_block_infill.py",
                  "name": "NON_DWELLING_LETTERS"}],
     "derivation": "the letters the face rule does NOT rank. A is excluded on purpose: "
                   "a yard building is placed by the ancillary clause, which is a rule "
                   "about the lot and not about the street."},
    {"name": "commercial_letter", "value": "C", "unit": "family letter",
     "read_by": [{"module": "tools/measure_face_rule.py", "name": "COMMERCIAL"}],
     "derivation": "the letter whose documented instances stand on the street line "
                   "rather than at a dwelling's typology setback — 13 of 15 at T-0024, "
                   "and every one of those on a platted street."},
]

# ------------------------------------------------------------------ the clauses
#
# `prefers` / `avoids` vocabulary, and nothing else parses:
#   class:principal|ordinary|light   the committed traffic class of the nearest street
#   street:<id>                      a named street in data/streets/1835.json
#   division:south|north|west        the division the record stands in
#   lot:corner|mid                   lot position within its block face
#   ground:river_frontage|branch|outside_plat|wet|unplatted
#
# `setback_class`:
#   street_line   at or inside constants.street_line_m
#   typology      a dwelling's 4.0–7.5 m front yard
#   yard          behind its own principal roof, off the block alley
#   unplatted     no street frontage to keep a setback from
#
# `multi_building_lot_rule`:
#   party_line_run        the density standard's party-line units, up to three per lot
#   principal_plus_ancillary   one principal roof and its yard buildings
#   one_principal_roof    one roof, and the lot is not subdivided
#   not_applicable        the record is not seated on a platted lot

CLAUSES = [
    {"id": "commercial_front",
     "applies_to": ["C1", "C2", "C3", "C4", "F1", "F2", "F3", "F4"],
     "prefers": ["class:principal", "street:south_water", "street:lake",
                 "street:dearborn", "street:clark", "lot:corner"],
     "avoids": ["class:light"],
     "multi_building_lot_rule": "party_line_run",
     "setback_class": "street_line",
     "tier": "documented",
     "evidence": ["carpenter_south_water_store", "h_jones_store", "hogan_store",
                  "jh_kinzie_forwarding_store", "john_holbrook_store",
                  "pruyne_kimball_drugstore", "frederick_thomas_shop",
                  "thomas_church_store", "dole_warehouse_south", "old_bank_building",
                  "newberry_dole_warehouse", "kinzie_hunter_warehouse"],
     "note": "Trade takes the built streets and the river front, corners first, and it "
             "stands on the line rather than behind a yard. Not one documented store or "
             "warehouse in this town stands on a light street, and that zero — not a "
             "preference about frontage — is what the clause rests on."},

    {"id": "professional_row",
     "applies_to": ["C1"],
     "prefers": ["class:principal", "street:lake", "street:clark", "street:dearborn",
                 "division:south"],
     "avoids": ["class:light", "ground:outside_plat"],
     "multi_building_lot_rule": "party_line_run",
     "setback_class": "street_line",
     "tier": "inferred",
     "evidence": ["old_bank_building", "bates_auction_room", "chicago_democrat_office",
                  "chicago_american_office", "cook_county_courthouse_1835"],
     "note": "Offices — law, land, press, auction, insurance — sit by the public square "
             "and the hotels rather than on the river front, because their traffic is "
             "the town's own and not the lake's. Inferred, and the evidence is thin: "
             "the two printing offices and the auction room are on Clark and Dearborn "
             "within a block of the square, the old bank building is on Lake, and the "
             "court house the reconciliation credits no family is cited for its "
             "position and not counted in the witness."},

    {"id": "mechanics_streets",
     "applies_to": ["W1", "W2", "W3", "W4"],
     "prefers": ["class:ordinary", "street:state", "street:dearborn", "street:clark",
                 "street:canal", "lot:mid"],
     "avoids": ["class:light"],
     "multi_building_lot_rule": "principal_plus_ancillary",
     "setback_class": "street_line",
     "tier": "documented",
     "evidence": ["pierce_blacksmith_shop", "goss_cobb_saddlery",
                  "mason_blacksmith_shop", "philo_carpenter_log_shop",
                  "blacksmith_shop_state_st"],
     "note": "A shop needs to be found but does not need the best frontage in town: the "
             "mechanics take the side streets and the Canal Street approach, on the "
             "line, with their yard behind. Five documented workshops stand on a "
             "street; five of the eight documented W roofs are on ordinary streets."},

    {"id": "heavy_and_noxious_trades",
     "applies_to": ["W5"],
     "prefers": ["ground:branch", "ground:river_frontage", "street:canal",
                 "division:west"],
     "avoids": ["class:principal", "lot:corner"],
     "multi_building_lot_rule": "not_applicable",
     "setback_class": "unplatted",
     "tier": "documented",
     "evidence": ["clybourn_slaughterhouse", "elston_soap_candle_manufactory",
                  "miller_tannery", "newberry_dole_slaughterhouse_south_branch"],
     "note": "Packing, tanning, slaughtering and soap-boiling go to the branches and "
             "out of the town's nose, on the water that carries their waste away. All "
             "four documented instances stand well off any platted street line, and "
             "three of the four are on a branch."},

    {"id": "merchant_and_professional_dwellings",
     "applies_to": ["H1", "H2", "D7"],
     "prefers": ["class:ordinary", "street:randolph", "street:washington",
                 "street:clark", "street:lake", "lot:corner"],
     "avoids": ["ground:branch", "ground:wet"],
     "multi_building_lot_rule": "principal_plus_ancillary",
     "setback_class": "typology",
     "tier": "inferred",
     "evidence": ["cobweb_castle", "heacock_house_monroe", "james_kinzie_house"],
     "note": "The better houses take the Randolph–Washington tier a block back from the "
             "trade, and the north tier under Kinzie: off the noise, on dry ground, "
             "with a garden. Inferred — the town holds one documented H roof and it is "
             "Cobweb Castle, on the north side, which is itself the clause's own "
             "outlier."},

    {"id": "tradesman_dwellings",
     "applies_to": ["D3", "D4", "D5", "D6"],
     "prefers": ["class:ordinary", "division:south", "lot:mid"],
     "avoids": ["ground:wet"],
     "multi_building_lot_rule": "party_line_run",
     "setback_class": "typology",
     "tier": "inferred",
     "evidence": ["harmon_log_cabin", "madore_beaubien_house", "lasalle_lake_house"],
     "note": "The frame cottages fall on the side streets behind the principal "
             "frontages — the back of the same blocks the stores front, which is how a "
             "block parcel comes to deal its meanest roof to its worst street."},

    {"id": "labourer_dwellings",
     "applies_to": ["D1", "D2"],
     "prefers": ["class:light", "division:west", "division:north", "lot:mid",
                 "ground:outside_plat"],
     "avoids": ["street:south_water", "street:lake"],
     "multi_building_lot_rule": "one_principal_roof",
     "setback_class": "typology",
     "tier": "inferred",
     "evidence": ["clybourn_cabins", "robinson_caldwell_cabins", "chappel_infant_school"],
     "note": "Cabins and shanties take the small lots, the fringes and the ground "
             "nobody is bidding on — Kinzie's Addition, the west clusters, the prairie "
             "edge. Inferred from the two documented cabin groups, both well outside "
             "the plat, and from the lot prices the land-sale register records."},

    {"id": "lodging_near_the_landings",
     "applies_to": ["T1", "T2", "T3", "H3"],
     "prefers": ["class:principal", "street:lake", "street:dearborn", "street:canal",
                 "lot:corner", "ground:river_frontage"],
     "avoids": ["ground:branch"],
     "multi_building_lot_rule": "principal_plus_ancillary",
     "setback_class": "street_line",
     "tier": "documented",
     "evidence": ["sauganash_hotel", "green_tree_tavern", "new_york_house",
                  "mansion_house", "tremont_house_1", "exchange_coffee_house",
                  "western_hotel", "wolf_point_tavern", "brown_boarding_house"],
     "note": "An inn stands where the traveller arrives: the bridge head, the forks, "
             "the stage and wagon approaches, the lake landing. Nine documented lodging "
             "roofs, and every one of them is on a corner, an approach or the water — "
             "with its stable in the yard behind it."},

    {"id": "farms_and_country_seats",
     "applies_to": ["D1", "A2"],
     "prefers": ["ground:outside_plat", "division:west", "division:north"],
     "avoids": ["class:principal", "lot:corner"],
     "multi_building_lot_rule": "not_applicable",
     "setback_class": "unplatted",
     "tier": "documented",
     "evidence": ["jb_beaubien_homestead", "beaubien_barn", "clybourn_cabins",
                  "robinson_caldwell_cabins"],
     "note": "The places held before the plat stay where they were held: Beaubien's on "
             "the lakefront reservation, Clybourn's on the North Branch, Robinson and "
             "Caldwell's on the west ground. They are not seated by any of this — they "
             "are the reason the policy has to say 'outside the plat' at all."},

    {"id": "institutions_stand_where_named",
     "applies_to": ["I1", "I2", "I3"],
     "prefers": ["class:ordinary", "street:clark", "street:randolph",
                 "street:washington"],
     "avoids": [],
     "multi_building_lot_rule": "one_principal_roof",
     "setback_class": "street_line",
     "tier": "documented",
     "evidence": ["first_presbyterian_church", "temple_building", "log_jail",
                  "north_side_school_1833", "walker_meeting_house", "st_marys_church",
                  "council_house", "chicago_lighthouse_1832", "watkins_school_house"],
     "note": "A public building nobody named is the claim that an institution stood "
             "here and left no record. `generate_block_infill.py` refuses the "
             "institutional families to a block parcel BY NAME (L93), so this clause "
             "seats nothing: it records where the nine named ones stand so a future "
             "parcel cannot quietly invent a tenth."},

    {"id": "ancillary_behind_its_own_roof",
     "applies_to": ["A1", "A2", "A3", "A4", "A5"],
     "prefers": ["lot:mid"],
     "avoids": ["class:principal"],
     "multi_building_lot_rule": "principal_plus_ancillary",
     "setback_class": "yard",
     "tier": "documented",
     "evidence": ["western_hotel_stable", "wolf_point_tavern_stable",
                  "fort_dearborn_big_barn", "fort_dearborn_wash_house"],
     "note": "Stables, privies, woodsheds and smokehouses go off the block alley behind "
             "the roof they serve. This predates the face rule and is a rule about the "
             "LOT, which is why A is not one of the face rule's letters."},

    {"id": "garrison_reservation",
     "applies_to": ["M1"],
     "prefers": ["ground:unplatted", "division:south"],
     "avoids": ["lot:corner", "lot:mid"],
     "multi_building_lot_rule": "not_applicable",
     "setback_class": "unplatted",
     "tier": "documented",
     "evidence": ["fort_dearborn_barracks", "fort_dearborn_officers_quarters",
                  "fort_dearborn_magazine", "fort_dearborn_blockhouse"],
     "note": "The military reservation was UNPLATTED in 1835 and no street crossed it "
             "(`data/reconstruction/1835_no_build_ground.json`). A building inside the "
             "fence has no street frontage to take a better or a worse face of, so no "
             "frontage clause reaches one — and the face rule's own zero is a statement "
             "about buildings that front streets."},
]

# --------------------------------------------------- the multi-building lot ruling
#
# The owner's "multiple buildings per lot in many cases in the major streets", written as
# a number and sourced. Derived fields are filled by build().

MULTI_BUILDING_LOT = {
    "principal_street_lot": {
        "rule": "party_line_run",
        "principal_roofs_max": 3,
        "basis": "the core density standard (T-0079): three party-line units per lot, "
                 "each one party_line_unit_m wide, sharing side walls.",
        "evidence": ["wright_building_to_let_a", "wright_building_to_let_b"],
        "note": "Wright's pair of buildings-to-let stand 5.00 m and 4.99 m off the "
                "Randolph line, side by side on one frontage: the documented instance "
                "of a lot carrying more than one principal roof.",
    },
    "back_street_lot": {
        "rule": "one_principal_roof",
        "principal_roofs_max": 1,
        "basis": "the dwelling typology setback and the block parcels' own arrangement "
                 "notes — a cottage on a side street keeps its front yard and its "
                 "dooryard, and the lot is not subdivided.",
        "evidence": [],
        "note": "Stated as the complement of the principal-street rule. No documented "
                "back-street lot in this town carries two principal roofs.",
    },
}

# ------------------------------------------------------- the outliers, and their reasons
#
# --score finds these by measurement. The reason is authored, and assertion 3 refuses an
# outlier that has none — so a new one cannot appear without somebody saying why.
#
# WHAT MOVED ON 2026-09-20, AND IT WAS THE STREETS RATHER THAN THE BUILDINGS (T-1191).
# This policy was written the day before the north bank had corridors. Seventeen of the
# twenty-two reasons below were therefore measured against a line on the FAR side of the
# river — the only committed corridor within reach of a north-side roof was South Water's
# or State's. T-1191 reads the north bank off Thompson's 1830 plat and Wright's 1834
# sheet, and every one of those readings is now taken against a north-bank line instead.
# Nothing was re-typed, nothing was moved to make it fit, and no confidence changed.
#
# Four reasons went away with the measurement that earned them, which is assertion 3
# working:
#
#   watkins_school_house   390 m off State, across the river → -8.40 m inside Michigan
#                          Street's north-bank corridor. Its own reason said it was "the
#                          same absence of street control as the Steamboat Hotel, not a
#                          placement"; T-1191 supplied the street control, and the school
#                          house now conforms to the institutional clause on its own line.
#   miller_tannery         153 m off South Water → 60.79 m off Market Street's north-bank
#                          corridor, which the noxious-trades clause allows on the branch
#                          ground. Andreas still places it against Miller's tavern rather
#                          than against a street; it simply no longer BREACHES one.
#   fort_dearborn_out_building_a / _b   312 m and 323 m off Lake, a principal street the
#                          ancillary clause avoids → 198.31 m and 195.52 m off Kinzie,
#                          which is ordinary, so the clause stops firing and both read as
#                          conforming. THIS ONE WAS AN ARTEFACT, WAS RECORDED AS ONE, AND
#                          IS FIXED — T-1429, and the two reasons are restored below.
#                          `nearest_frontage` now carries the bank test this paragraph
#                          asked for: it refuses a corridor the river stands between, and
#                          it refuses a stretch of corridor standing IN the river, which
#                          is what Kinzie's east end is. Read that function's docstring
#                          for both clauses and for why one of them does not reach.
#
# TWENTY-SIX READINGS MOVED WITH THAT FIX and all of them the same way: the whole Fort
# Dearborn reservation, the Beaubien cluster east of it and the south pier were being
# credited with Kinzie Street across the channel, and every one of them now measures to
# Lake Street on its own bank. Three of the fort's ancillary roofs — beaubien_barn,
# fort_dearborn_big_barn and fort_dearborn_wash_house — were conforming ONLY because
# the street they were measured against was ordinary, and they are outliers with their
# own reasons below now that the street is the one on their side of the water. Two
# north-bank roofs moved the other way, off Kinzie's submerged end onto Michigan Street,
# and both still conform. Nothing was retyped and no coordinate moved.

OUTLIER_REASONS = {
    "blacksmith_shop_state_st":
        "the GOVERNMENT smithy, not a mechanic's: it belongs to the agency "
        "establishment the 1821 treaty obliged the United States to keep at Chicago, "
        "and it stands in the north-side cluster round Cobweb Castle. Since T-1191 put "
        "the north bank's own corridors in the reading it is nearest Wolcott at 45.85 m "
        "rather than South Water at 97 m across the channel — a truer line and still not "
        "a frontage. The record is flagged review_required and nothing here seats it.",
    "brickyard_north_side":
        "the clay is where the clay is. A brickyard is seated by its material and not "
        "by its frontage — 31.43 m off Clark Street's north-bank corridor since T-1191, "
        "and 89 m off South Water's line across the river before it.",
    "chicago_lighthouse_1832":
        "at the river mouth on the federal reserve — a lighthouse is seated by the "
        "harbour and not by a street.",
    "council_house":
        "on the lakefront reservation ground east of the platted town.",
    "beaubien_barn":
        "Jean Baptiste Beaubien's own barn on his own ground east of the fort, outside "
        "the plat: an ancillary roof 347.65 m from Lake Street's corridor edge is behind "
        "its own house and not on anybody's frontage. It read Kinzie at 80.93 m until "
        "T-1429, which is a north-bank street across the channel.",
    "fort_dearborn_big_barn":
        "inside the unplatted military reservation, 270.75 m from Lake Street's corridor "
        "edge: the garrison's own barn, seated behind the fort and not on a street. Same "
        "correction as its neighbours — Kinzie at 95.89 m was across the water.",
    "fort_dearborn_shop":
        "inside the unplatted military reservation: the garrison's own workshop, not a "
        "mechanic's shop on a street. Its nearest corridor is Lake Street's at 381.64 m "
        "since T-1429 put the river in the reading; the Kinzie line at 157.87 m that "
        "T-1191 briefly gave it is on the far bank and was never its frontage.",
    "fort_dearborn_out_building_a":
        "inside the unplatted military reservation, 312.17 m from Lake Street's corridor "
        "edge: the ancillary clause's 'behind its own roof' is a statement about a "
        "platted lot and there is no lot here. T-1191 read it 198.31 m off Kinzie and "
        "this reason had to be withdrawn; T-1429's bank test refuses that line — it is "
        "Kinzie's east end, which stands under the 1834 harbour cut — and restores it.",
    "fort_dearborn_out_building_b":
        "inside the unplatted military reservation, 322.71 m from Lake Street's corridor "
        "edge, as its pair. Withdrawn by T-1191 and restored by T-1429 for the same "
        "reason.",
    "fort_dearborn_wash_house":
        "inside the unplatted military reservation, 420.22 m from Lake Street's corridor "
        "edge: the garrison washed its own linen behind its own palisade. It read Kinzie "
        "at 144.13 m until T-1429, across the channel.",
    "fort_dearborn_us_factors_house":
        "inside the unplatted military reservation — see the garrison clause. No street "
        "crossed the reservation in 1835.",
    "kinzie_hunter_warehouse":
        "on the north bank of the main river: its frontage is the WATER, which is what "
        "a forwarding warehouse wants. Since T-1191 the line beside it is Market Street's "
        "north-bank corridor at 4.16 m rather than South Water's across the channel, and "
        "standing that close to a light back street is not taking its face.",
    "miller_house":
        "on the north bank, at the forks. It is nearest Market Street's north-bank "
        "corridor at 60.66 m since T-1191 and was nearest South Water's line at 138 m "
        "across the river before it; neither is a face this house takes.",
    "north_bank_shed_dearborn_e1": "a north-bank freight shed: its frontage is the water.",
    "north_bank_shed_dearborn_e2": "a north-bank freight shed: its frontage is the water.",
    "north_bank_shed_dearborn_e3": "a north-bank freight shed: its frontage is the water.",
    "north_bank_shed_dearborn_w": "a north-bank freight shed: its frontage is the water.",
    "north_side_school_1833":
        "the north-side school, 4.32 m off Clark Street's north-bank corridor since "
        "T-1191 and 90 m off the South Water line across the river before it. The "
        "institutional clause puts a named institution on its line and this one stands "
        "back off a light street, which is where the school house was built.",
    "robert_kinzie_store":
        "at Wolf Point, off the platted grid: the store fronts the forks and the ferry "
        "landing, and Lake Street's line is 27 m away because Lake ENDS at the river.",
    "steamboat_hotel":
        "north division. Until T-1191 State was simply the nearest line, 203 m off "
        "across the river; the hotel is now read against Kinzie at 20.47 m, which is a "
        "real north-bank line and still a setback no lodging clause allows.",
    "walker_meeting_house":
        "on the west ground 48 m off the Canal line, at the edge of what was platted.",
    "wolf_point_tavern":
        "at the forks, 40 m off Lake's line: the tavern fronts the ferry and the two "
        "branches, which is precisely why it stands there.",
    "wolf_point_tavern_stable":
        "the tavern's own stable, at the forks with it.",
}


# ------------------------------------------------------------------ the committed file

def policy() -> dict:
    """The committed policy. This is what every other module reads."""
    return json.loads(POLICY.read_text(encoding="utf-8"))


def constant(name: str):
    """One shared number, by name. The three measure modules call this and nothing else."""
    for row in policy()["constants"]:
        if row["name"] == name:
            return row["value"]
    raise KeyError(f"{name} is not a constant of the 1835 placement policy")


def clause(clause_id: str) -> dict:
    for row in policy()["clauses"]:
        if row["id"] == clause_id:
            return row
    raise KeyError(f"{clause_id} is not a clause of the 1835 placement policy")


# ------------------------------------------------------------------ the reading

def _tree():
    """The committed census, the reconciliation's families, and the street classes.

    Imported inside the function on purpose: `measure_frontage_fabric` imports THIS
    module for its constants, and a module-level import here would close the circle.
    """
    sys.path.insert(0, str(TOOLS))
    from measure_frontage_fabric import (  # noqa: E402
        census, documented_families, street_traffic)
    return census(), documented_families(), street_traffic()


def clauses_for(family: str) -> list[dict]:
    return [c for c in CLAUSES if family in c["applies_to"]]


def _breaches(row: dict, clause_row: dict, street_line_m: float) -> list[str]:
    """Why this clause refuses this record — empty if it does not.

    Only the two MEASURABLE terms are scored. `division:`, `lot:` and `ground:` terms are
    declarative: this project has no committed lot-position field for a documented record
    and no division index, so scoring them would be scoring an absence. They are printed
    with the clause and spent by the seating tickets, not here.
    """
    out = []
    if row["class"] and f"class:{row['class']}" in clause_row["avoids"]:
        out.append(f"stands on a {row['class']} street, which {clause_row['id']} avoids")
    if clause_row["setback_class"] == "street_line" and not row["on_line"]:
        out.append(f"stands {row['setback_m']:.2f} m off the street line "
                   f"({street_line_m} m), and {clause_row['id']} puts it on the line")
    return out


def reading(street_line_m: float | None = None) -> dict:
    """Every DOCUMENTED roof the reconciliation credits a family, against its clauses.

    A letter may be covered by more than one clause — a D1 is a labourer's cabin under
    one and a pre-plat country place under another — and a record CONFORMS if any of its
    clauses accepts it. Clauses are alternatives for a letter, not a conjunction.
    """
    if street_line_m is None:
        street_line_m = 2.71
        for row in CONSTANTS:
            if row["name"] == "street_line_m":
                street_line_m = row["value"]
    census, families, traffic = _tree()
    rows = []
    for row in census["rows"]:
        if row["layer"] != "research":
            continue
        family = families.get(row["id"])
        if not family:
            continue
        matched = clauses_for(family)
        scored = {c["id"]: _breaches({**row, "class": traffic.get(row["street"])},
                                     c, street_line_m) for c in matched}
        conforms = bool(matched) and any(not v for v in scored.values())
        rows.append({"id": row["id"], "family": family, "street": row["street"],
                     "class": traffic.get(row["street"]), "setback_m": row["setback_m"],
                     "on_line": row["on_line"],
                     "clauses": [c["id"] for c in matched],
                     "breaches": scored, "conforms": conforms})
    return {"rows": rows, "street_line_m": street_line_m}


def outliers(result: dict | None = None) -> list[dict]:
    """The documented roofs no clause of their own letter accepts, with their reason."""
    result = result or reading()
    out = []
    for row in result["rows"]:
        if row["conforms"] or not row["clauses"]:
            continue
        why = sorted({m for v in row["breaches"].values() for m in v})
        out.append({"id": row["id"], "family": row["family"], "street": row["street"],
                    "class": row["class"], "setback_m": round(row["setback_m"], 2),
                    "measured": why,
                    "reason": OUTLIER_REASONS.get(row["id"])})
    return sorted(out, key=lambda r: r["id"])


def witness(clause_row: dict, result: dict) -> dict:
    """What the clause's own evidence does, re-read from the tree on every build."""
    by_id = {r["id"]: r for r in result["rows"]}
    seen = [by_id[i] for i in clause_row["evidence"] if i in by_id]
    setbacks = sorted(round(r["setback_m"], 2) for r in seen)
    return {
        "evidence_records": len(clause_row["evidence"]),
        "standing_with_a_street": len(seen),
        "by_street_class": {k: sum(1 for r in seen if r["class"] == k) for k in CLASSES},
        "on_the_street_line": sum(1 for r in seen if r["on_line"]),
        "setback_m_min": setbacks[0] if setbacks else None,
        "setback_m_max": setbacks[-1] if setbacks else None,
    }


# ------------------------------------------------------------------ the assertions

def _assignment(source: str, name: str) -> str | None:
    match = re.search(rf"^{re.escape(name)}\s*=\s*(.+)$", source, re.M)
    return match.group(1) if match else None


def failures(result: dict | None = None) -> list[str]:
    """The five assertions. See the module docstring."""
    result = result or reading()
    census, families, _ = _tree()
    committed = {r["id"] for r in census["rows"]}
    known = {f["id"] for f in json.loads(
        (DATA / "reconstruction" / "1835_family_archetype_crosswalk.json")
        .read_text(encoding="utf-8"))["families"]}
    out = []

    # 1. No phantom citation. A clause may only cite a record this tree holds.
    cited = [(c["id"], i) for c in CLAUSES for i in c["evidence"]]
    cited += [(f"multi_building_lot.{k}", i)
              for k, v in MULTI_BUILDING_LOT.items() for i in v["evidence"]]
    for where, record_id in cited:
        if record_id not in committed:
            out.append(f"{where} cites `{record_id}`, which is not a committed record")

    # 2. The provenance contract, applied to the policy itself: a `documented` clause
    #    needs a record behind it, an inferred or conjectural one needs its reasoning.
    for c in CLAUSES:
        if c["tier"] == "documented" and not c["evidence"]:
            out.append(f"{c['id']} claims tier `documented` and cites no record")
        if c["tier"] != "documented" and not (c.get("note") or "").strip():
            out.append(f"{c['id']} is tier `{c['tier']}` and states no reasoning")

    # 3. Every outlier is explained, and every explanation still has its outlier. The
    #    first half stops a new outlier appearing silently; the second stops the reasons
    #    rotting on after the record that earned them has moved or been retyped.
    found = outliers(result)
    for row in found:
        if not row["reason"]:
            out.append(f"{row['id']} ({row['family']}) stands against every clause of "
                       f"its letter and nothing here says why: "
                       f"{'; '.join(row['measured'])}")
    stale = set(OUTLIER_REASONS) - {r["id"] for r in found}
    for record_id in sorted(stale):
        out.append(f"OUTLIER_REASONS explains `{record_id}`, which is no longer an "
                   f"outlier — delete the reason or find out what moved")

    # 4. No family letter without a seat rule. The crosswalk is the vocabulary the whole
    #    programme deals from; a letter this policy does not cover is a roof the seating
    #    tickets would have to place on instinct.
    covered = {f for c in CLAUSES for f in c["applies_to"]}
    for family in sorted(known - covered):
        out.append(f"family {family} has no clause: the seating tickets would place it "
                   f"on instinct")
    for family in sorted(covered - known):
        out.append(f"a clause applies to family {family}, which the archetype crosswalk "
                   f"does not carry")

    # 5. One source of truth, and this is the half with teeth. Each constant names the
    #    module that reads it; that module must take it from here rather than carry its
    #    own copy again.
    for row in CONSTANTS:
        for reader in row["read_by"]:
            module, name = reader["module"], reader["name"]
            path = ROOT / module
            if not path.exists():
                out.append(f"{module} is named as the reader of `{row['name']}` and "
                           f"does not exist")
                continue
            source = path.read_text(encoding="utf-8")
            rhs = _assignment(source, name)
            if rhs is None:
                out.append(f"{module} no longer defines {name}, which `{row['name']}` "
                           f"is declared to feed")
            elif "constant(" not in rhs:
                out.append(f"{module} sets {name} = {rhs.strip()} — its own copy of "
                           f"`{row['name']}`, which this file is supposed to be the "
                           f"only source of")
    return out


# ------------------------------------------------------------------ the build

def build() -> dict:
    result = reading()
    return {
        "$schema_note":
            "DERIVED — regenerate with tools/placement_policy_1835.py --build; "
            "tools/check.sh re-derives it. The clauses are AUTHORED in that module and "
            "every figure beside one is re-read from the committed tree. Do not "
            "hand-edit: --check rebuilds this file and refuses any drift.",
        "id": "chicago_july_1835_placement_policy",
        "ticket": "T-1195",
        "target_date": "1835-07-01",
        "generated_by": "tools/placement_policy_1835.py --build",
        "not_a_reading":
            "no page of any source is read here. This is an adjudication over committed "
            "records: where the town's 93 documented roofs actually stand, written as "
            "the rule the seating tickets deal by. No roof moves.",
        "scope":
            "T-1198 and T-1199 seat by this file; T-1200 through T-1214 build by it. "
            "The clauses are alternatives for a family letter, not a conjunction — a "
            "record conforms if any clause of its letter accepts it.",
        "inputs": [
            "data/structures/*.json",
            "data/streets/1835.json",
            "data/reconstruction/1835_existing_roof_reconciliation.json",
            "data/reconstruction/1835_family_archetype_crosswalk.json",
        ],
        "vocabulary": {
            "prefers_and_avoids": [
                "class:principal|ordinary|light — the committed traffic class of the "
                "nearest street",
                "street:<id> — a named street in data/streets/1835.json",
                "division:south|north|west",
                "lot:corner|mid — lot position within the block face",
                "ground:river_frontage|branch|outside_plat|wet|unplatted",
            ],
            "scored_here": [
                "class:* in `avoids`", "setback_class `street_line`"],
            "declarative": [
                "division:*", "lot:*", "ground:*", "everything in `prefers`",
                "— this project holds no committed lot-position field for a documented "
                "record and no division index, so scoring them would be scoring an "
                "absence. The seating tickets spend them; this file does not gate them."],
            "setback_class": [
                "street_line — at or inside constants.street_line_m",
                "typology — a dwelling's 4.0–7.5 m front yard",
                "yard — behind its own principal roof, off the block alley",
                "unplatted — no street frontage to keep a setback from",
            ],
        },
        "constants": CONSTANTS,
        "multi_building_lot": MULTI_BUILDING_LOT,
        "clauses": [{**c, "witness": witness(c, result)} for c in CLAUSES],
        "coverage": {
            "documented_roofs_with_a_family": len(result["rows"]),
            "conforming": sum(1 for r in result["rows"] if r["conforms"]),
            "outliers": len(outliers(result)),
            "by_family": {f: sorted(c["id"] for c in clauses_for(f))
                          for f in sorted({r["family"] for r in result["rows"]})},
        },
        "outliers": outliers(result),
    }


def _dump(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


# ------------------------------------------------------------------ printing

def _report(result: dict) -> str:
    lines = ["\n   the 1835 placement policy — every documented roof against its clause\n",
             "   family  record                                   street        class"
             "      setback   verdict"]
    for row in sorted(result["rows"], key=lambda r: (r["family"], r["id"])):
        verdict = "conforms" if row["conforms"] else "OUTLIER"
        lines.append(f"   {row['family']:<8}{row['id']:<41}{row['street']:<14}"
                     f"{str(row['class']):<11}{row['setback_m']:>8.2f} m  {verdict}")
    lines.append("\n   the outliers, and what each one is telling you\n")
    for row in outliers(result):
        lines.append(f"   {row['family']:<5}{row['id']}")
        lines.append(f"         measured: {'; '.join(row['measured'])}")
        lines.append(f"         reason:   {row['reason'] or '(NONE — assertion 3 fires)'}")
    conforming = sum(1 for r in result["rows"] if r["conforms"])
    lines.append(f"\n   {conforming} of {len(result['rows'])} documented roofs conform to "
                 f"a clause of their own family letter;")
    lines.append(f"   {len(outliers(result))} stand against every clause of it and are "
                 f"recorded as evidence rather than corrected.\n")
    return "\n".join(lines)


def _clause_table() -> str:
    result = reading()
    lines = ["\n   the clauses, and what the record puts behind each\n",
             "   clause                             tier         applies to"
             "                n  prin  ord  light  on-line"]
    for c in CLAUSES:
        w = witness(c, result)
        applies = " ".join(c["applies_to"])
        if len(applies) > 24:
            applies = applies[:21] + "…"
        lines.append(
            f"   {c['id']:<37}{c['tier']:<13}{applies:<25}"
            f"{w['standing_with_a_street']:>3}"
            f"{w['by_street_class']['principal']:>6}"
            f"{w['by_street_class']['ordinary']:>5}"
            f"{w['by_street_class']['light']:>7}"
            f"{w['on_the_street_line']:>9}")
    lines.append("\n   the shared constants, and who reads each one now\n")
    for row in CONSTANTS:
        lines.append(f"   {row['name']:<24}{str(row['value']):<28}"
                     f"{', '.join(r['module'].replace('tools/', '') + ':' + r['name'] for r in row['read_by'])}")
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ the self-test

def self_test() -> int:
    print("  the five assertions, broken in memory against the committed policy\n")
    checks = []

    out = failures()
    checks.append(("the committed policy passes all five",
                   not out, "; ".join(out) or "clean"))

    # 1 — a citation nothing stands behind.
    keep = CLAUSES[0]["evidence"]
    CLAUSES[0]["evidence"] = keep + ["no_such_store_on_south_water"]
    out = failures()
    checks.append(("a clause citing a record this tree does not hold is caught",
                   any("not a committed record" in m for m in out),
                   "; ".join(out) or "nothing"))
    CLAUSES[0]["evidence"] = keep

    # 2 — the provenance contract, applied to the policy's own rows.
    keep_tier = CLAUSES[1]["tier"]
    keep_note = CLAUSES[1]["note"]
    CLAUSES[1]["note"] = "  "
    out = failures()
    checks.append(("an inferred clause that states no reasoning is caught",
                   any("states no reasoning" in m for m in out),
                   "; ".join(out) or "nothing"))
    CLAUSES[1]["tier"], CLAUSES[1]["note"] = keep_tier, keep_note

    # 3 — both halves: a new outlier nobody explained, and an explanation gone stale.
    result = reading()
    victim = next(r for r in result["rows"] if r["conforms"] and r["clauses"])
    victim["conforms"] = False
    victim["breaches"] = {victim["clauses"][0]: ["moved onto a light street, in memory"]}
    out = failures(result)
    checks.append(("an unexplained outlier is caught",
                   any(victim["id"] in m and "nothing here says why" in m for m in out),
                   "; ".join(m for m in out if victim["id"] in m) or "nothing"))

    OUTLIER_REASONS["a_store_that_was_never_here"] = "a reason for nothing"
    out = failures()
    checks.append(("…and a reason left behind by an outlier that went away is caught",
                   any("no longer an outlier" in m for m in out),
                   "; ".join(m for m in out if "no longer" in m) or "nothing"))
    del OUTLIER_REASONS["a_store_that_was_never_here"]

    # 4 — a family letter with nothing to seat it by.
    keep_applies = CLAUSES[0]["applies_to"]
    CLAUSES[0]["applies_to"] = [f for f in keep_applies if f != "C4"]
    out = failures()
    checks.append(("a family letter left without a clause is caught",
                   any("family C4 has no clause" in m for m in out),
                   "; ".join(m for m in out if "C4" in m) or "nothing"))
    CLAUSES[0]["applies_to"] = keep_applies

    # 5 — the one-source-of-truth clause, against a module that took its copy back.
    keep_readers = CONSTANTS[0]["read_by"]
    CONSTANTS[0]["read_by"] = [{"module": "tools/placement_policy_1835.py",
                                "name": "STREET_LINE_M"}]
    out = failures()
    checks.append(("a module carrying its own copy of a shared constant is caught",
                   any("only source of" in m or "no longer defines" in m for m in out),
                   "; ".join(m for m in out if "street_line_m" in m) or "nothing"))
    CONSTANTS[0]["read_by"] = keep_readers

    ok = True
    for label, passed, detail in checks:
        print(f"  {'ok  ' if passed else 'FAIL'}  {label} — {detail[:150]}")
        ok &= passed
    print("\nSELF-TEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


# ------------------------------------------------------------------ the CLI

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build", action="store_true",
                        help="rewrite data/reconstruction/1835_placement_policy.json")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 on drift from the tree or a broken assertion")
    parser.add_argument("--score", action="store_true",
                        help="every documented roof against the clauses of its family")
    parser.add_argument("--self-test", action="store_true",
                        help="break the five assertions in memory and watch them fire")
    parser.add_argument("--quiet", action="store_true", help="print only the verdict")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if args.build:
        POLICY.write_text(_dump(build()), encoding="utf-8")
        print(f"  wrote {POLICY.relative_to(ROOT)}")
        return 0

    if args.score:
        print(_report(reading()))
        return 0

    out = failures()
    if args.check:
        rebuilt = _dump(build())
        if not POLICY.exists():
            out.append(f"{POLICY.relative_to(ROOT)} is not committed — run --build")
        elif POLICY.read_text(encoding="utf-8") != rebuilt:
            out.append(f"{POLICY.relative_to(ROOT)} no longer matches what this module "
                       f"builds from the committed tree — run --build and read the diff")

    if not args.quiet:
        print(_clause_table())
    if out:
        print("THE 1835 PLACEMENT POLICY IS BREACHED")
        for message in out:
            print(f"  - {message}")
        return 1 if args.check else 0
    result = reading()
    print(f"  {len(CLAUSES)} clauses over {len(CONSTANTS)} shared constants; "
          f"{sum(1 for r in result['rows'] if r['conforms'])} of {len(result['rows'])} "
          f"documented roofs conform, {len(outliers(result))} recorded as outliers with "
          f"their reason")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
