#!/usr/bin/env python3
"""THE 1835 BUSINESS STAFFING MODEL: how many hands each kind of house employed.

T-1183. Zero of the 197 business records carries a staff member, and the
relationship vocabulary has admitted `clerk`, `apprentice`, `journeyman` and
`servant` all along with nobody standing in any of them. T-1189 is the ticket
that will write those people. This file is the RULE it writes them by, so that
a reconstructed clerk is a claim about a KIND OF HOUSE and not about a whim.

    tools/build_staffing_model_1835.py --build       write the model and its report
    tools/build_staffing_model_1835.py --check       re-derive both and refuse drift
    tools/build_staffing_model_1835.py --self-test   the guards, fired on fixtures

WHAT THIS TOOL IS, AND THE ONE LINE OF ITS ACCEPTANCE THAT MATTERS MOST. It
reads no page of any source, opens no network, and **writes no person**. It
reads the committed business layer, the committed 1839 trade table, the town
model and the trade-census crosswalk, and it emits a table of ESTABLISHMENT
KINDS with the roles each kind employed. The dry run at the end applies that
table to the layer as it stands and prints the staff the town implies, by role
and by sex, against the town model's own employment figure. No id of a person
appears anywhere in the output and the self-test holds that directly.

WHERE THE NUMBERS COME FROM, SAID HONESTLY. Three bases, and every role row
declares which one it stands on:

  `attested_in_the_layer`        the business records themselves name the hand.
  `directory_1839`               Fergus's 1839 list, read by T-1346, counts the
                                 trade. Four years late and a bigger town; a
                                 PRIOR, never a count of 1835.
  `period_convention`            the project holds no figure. The row says so,
                                 names its analogue, and is reconstructed.

THE ONE RATIO THIS MODEL ACTUALLY DERIVES. The 1839 directory prints 152 clerks
against the commerce trades' principals, and that quotient — computed here, not
typed — is the model's calibration for counting-house labour. It is applied to
the LAYER'S OWN principals to predict a clerk total, and the per-establishment
rule below is then checked against that prediction rather than asserted past
it. When the two disagree the model says so in `reconciliation` and does not
quietly move either.

THE DIRECTORY IS A FLOOR FOR SERVICE, NOT A COUNT, and this is the finding that
stops the calibration being used everywhere. Against 50 keepers of taverns,
boarding houses and refectories, the 1839 list prints **two** bar-keepers, one
laundress and five domestics, and no hostler, cook or chambermaid at all. A
directory of that shape is a list of householders; it did not canvass servants.
So every service role here is `period_convention` with the under-record stated,
and the town model's own open question — that the 1840 industry columns have no
row for domestic service at all — is carried into the report rather than
papered over.

WHAT IT REFUSES. A business the layer gives no trade to is carried in the
`unclassified` class with no staff and the reason on the row: inventing an
establishment kind for it is T-1182's audit done here, by a tool with no licence
to do it. A role term the residents vocabulary does not hold is listed in
`vocabulary_gaps` and may not be written onto a person until index.json carries
it — the same rule the 1839 trade table already states for its own rows.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL_OUT = ROOT / "data" / "reconstruction" / "1835_business_staffing_model.json"
REPORT = ROOT / "docs" / "RESEARCH" / "1835_business_staffing_model.md"

BUSINESSES = ROOT / "data" / "businesses"
TRADE_TABLE_1839 = ROOT / "data" / "research" / "directories" / "fergus_1839_trade_table.json"
TOWN_MODEL = ROOT / "data" / "reconstruction" / "1835_town_model.json"
CROSSWALK = ROOT / "data" / "research" / "books" / "trade_census_1835_crosswalk.json"
RESIDENT_INDEX = ROOT / "data" / "residents" / "index.json"

SCENE_DATE = "1835-07-01"
TICKET = "T-1183"

#: This model's OWN age vocabulary, and it is deliberately not the residents
#: layer's. Those bands (`adult_by_role`, `child_by_baptism`, …) say how a card's
#: age was EVIDENCED; these say what age a kind of hand was. Mixing them would
#: read as evidence where there is none.
AGE_BANDS = {
    "youth_12_18": "a boy or girl bound or hired young — the apprentice, the tavern boy",
    "young_adult_16_25": "the clerkship and journeyman years, before a man sets up for himself",
    "adult_18_45": "a working adult of no more exact age",
    "adult_any": "any adult; the role says nothing about age",
}

#: How a role's sex is ruled. `either` is a real answer and not a shrug: it is
#: the answer wherever the sources show both and neither predominates.
SEX_RULES = {
    "male": "men only, on every case the sources show",
    "female": "women only, on every case the sources show",
    "predominantly_male": "men in the great majority; a woman in the role is not refused",
    "predominantly_female": "women in the great majority; a man in the role is not refused",
    "either": "the sources show both and neither predominates",
}

BASES = {
    "attested_in_the_layer": "a business record in this project names a hand of this kind",
    "directory_1839": "Fergus's 1839 directory, read by T-1346, counts the trade",
    "period_convention": "the project holds no figure; the row is reconstructed from the "
                         "practice of the trade and names its analogue",
}

#: The 1839 rows that are STAFF and not principals. The calibration's denominator
#: is the commerce trades minus these, because a clerk is not a house.
STAFF_TRADES_1839 = {"clerk", "warehouseman", "bar_keeper", "domestic", "laundress",
                     "steward", "foreman", "student"}

#: Keepers of houses of entertainment in 1839 — the denominator of the service
#: under-record finding.
ENTERTAINMENT_TRADES_1839 = {"tavern_keeper", "boarding_house_keeper", "refectory_keeper"}

#: Which staffing class each of the layer's own `occupation` terms falls in.
#: Read off the record, never off its name. A term absent here is a gap the
#: build REFUSES rather than silently dropping into `unclassified`.
CLASS_OF_OCCUPATION = {
    "dry_goods_merchant": "dry_goods_store",
    "merchant": "dry_goods_store",
    "clothier": "dry_goods_store",
    "grocer": "grocery_and_provision_store",
    "provision_dealer": "grocery_and_provision_store",
    "liquor_dealer": "grocery_and_provision_store",
    "hardware_merchant": "hardware_or_stove_store",
    "stove_dealer": "hardware_or_stove_store",
    "druggist": "drug_store",
    "bookseller": "book_store",
    "milliner": "millinery_and_dressmaking",
    "dressmaker": "millinery_and_dressmaking",
    "jeweller": "small_luxury_shop",
    "hatter": "small_luxury_shop",
    "confectioner": "small_luxury_shop",
    "forwarding_and_commission": "forwarding_and_warehouse",
    "lumber_merchant": "lumber_yard",
    "auctioneer": "auction_and_commission_room",
    "land_agent": "land_or_insurance_office",
    "insurance_agent": "land_or_insurance_office",
    "tavern_keeper": "tavern_or_hotel",
    "hotel_keeper": "tavern_or_hotel",
    "printer": "printing_office",
    "attorney": "law_office",
    "physician": "physician_practice",
    "dentist": "dentist_stand",
    "schoolteacher": "school",
    "blacksmith": "smithy",
    "joiner": "wood_trades_shop",
    "carriage_maker": "wood_trades_shop",
    "tailor": "tailor_shop",
    "shoemaker": "shoemaker_shop",
    "harness_maker": "leather_shop",
    "tinsmith": "tinner_shop",
    "baker": "bakery",
    "butcher": "butcher_shop",
    "painter": "painter_shop",
    "livery_stable_keeper": "livery_stable",
    "miller": "mill",
    "brewer": "brewery",
    "founder": "foundry",
    "soap_and_candle_maker": "soap_and_candle_works",
    "surveyor": "surveyor_office",
    "postmaster": "post_office",
}

#: Which 1840 industry column each class's principals were counted under, so the
#: dry run can be set beside the town model's employment figure in its own units.
COLUMN_1840 = {
    "dry_goods_store": "Commerce",
    "grocery_and_provision_store": "Commerce",
    "hardware_or_stove_store": "Commerce",
    "drug_store": "Commerce",
    "book_store": "Commerce",
    "millinery_and_dressmaking": "Manufactures and trades",
    "small_luxury_shop": "Manufactures and trades",
    "forwarding_and_warehouse": "Commerce",
    "lumber_yard": "Commerce",
    "auction_and_commission_room": "Commerce",
    "land_or_insurance_office": "Commerce",
    "tavern_or_hotel": "Commerce",
    "printing_office": "Manufactures and trades",
    "law_office": "Learned professions and engineers",
    "physician_practice": "Learned professions and engineers",
    "dentist_stand": "Learned professions and engineers",
    "school": "Learned professions and engineers",
    "smithy": "Manufactures and trades",
    "wood_trades_shop": "Manufactures and trades",
    "tailor_shop": "Manufactures and trades",
    "shoemaker_shop": "Manufactures and trades",
    "leather_shop": "Manufactures and trades",
    "tinner_shop": "Manufactures and trades",
    "bakery": "Manufactures and trades",
    "butcher_shop": "Manufactures and trades",
    "painter_shop": "Manufactures and trades",
    "livery_stable": "Commerce",
    "mill": "Manufactures and trades",
    "brewery": "Manufactures and trades",
    "foundry": "Manufactures and trades",
    "soap_and_candle_works": "Manufactures and trades",
    "surveyor_office": "Learned professions and engineers",
    "post_office": "Learned professions and engineers",
    "unclassified": None,
}

#: A class's prose name, for the report and for anything that prints a row.
CLASS_WORDS = {
    "dry_goods_store": "a dry-goods store",
    "grocery_and_provision_store": "a grocery and provision store",
    "hardware_or_stove_store": "a hardware or stove store",
    "drug_store": "a drug store",
    "book_store": "a book store",
    "millinery_and_dressmaking": "a millinery or dressmaking room",
    "small_luxury_shop": "a jeweller's, hatter's or confectioner's shop",
    "forwarding_and_warehouse": "a forwarding and commission house",
    "lumber_yard": "a lumber yard",
    "auction_and_commission_room": "an auction and commission room",
    "land_or_insurance_office": "a land or insurance office",
    "tavern_or_hotel": "a tavern or hotel",
    "printing_office": "a printing office",
    "law_office": "a law office",
    "physician_practice": "a physician's practice",
    "dentist_stand": "a dentist's stand",
    "school": "a school",
    "smithy": "a blacksmith's shop",
    "wood_trades_shop": "a joiner's or carriage maker's shop",
    "tailor_shop": "a tailoring establishment",
    "shoemaker_shop": "a boot and shoe shop",
    "leather_shop": "a saddler's and harness maker's shop",
    "tinner_shop": "a tin and copper manufactory",
    "bakery": "a bakery",
    "butcher_shop": "a butcher's shop",
    "painter_shop": "a painter's shop",
    "livery_stable": "a livery stable",
    "mill": "a mill",
    "brewery": "a brewery",
    "foundry": "an iron foundry",
    "soap_and_candle_works": "a soap and candle works",
    "surveyor_office": "a surveyor's office",
    "post_office": "the post office",
    "unclassified": "a business the layer gives no trade to",
}

# ---------------------------------------------------------------- the rules --
# THE TABLE. One tuple per role a class employed:
#   (occupation_term, household_relationship, low, typical, high,
#    sex_rule, age_band, lives_on_premises, basis, note)
# `lives_on_premises` is the SHOP HOUSEHOLD RULE T-1163 shares: the share of
# holders of that role who slept in the proprietor's house or over the shop.
# Every `period_convention` note names the analogue it reasons from, because a
# row with no analogue is an opinion wearing a schema.
R = tuple
STAFFING_RULES: dict[str, list] = {
    "dry_goods_store": [
        R(("clerk", "clerk", 1, 1, 2, "male", "young_adult_16_25", 0.5, "directory_1839",
           "The counting-house clerk is the one role the directory counts in bulk — 152 of "
           "them, the largest single trade in the 1839 list after the carpenters — and the "
           "printed forms name their houses outright ('clerk stiles burton'). A young man "
           "boarding with his employer or over the store is the ordinary arrangement; half "
           "is this model's reading of 'often', and it is a reading.")),
        R(("labourer", "household_member", 0, 0, 1, "male", "adult_18_45", 0.0,
           "period_convention",
           "A porter to shift goods, at the larger houses only. Analogue: the 1839 list's "
           "seven porters, counted under labourer, against 151 commerce principals.")),
    ],
    "grocery_and_provision_store": [
        R(("clerk", "clerk", 0, 1, 1, "male", "young_adult_16_25", 0.5, "directory_1839",
           "A grocery is a smaller counting house than a dry-goods store and the low end is "
           "the keeper alone. Same clerk calibration, one step down.")),
        R(("labourer", "household_member", 0, 0, 1, "male", "adult_18_45", 0.0,
           "period_convention", "A hand for barrels and the drayage. Analogue: as above.")),
    ],
    "hardware_or_stove_store": [
        R(("clerk", "clerk", 0, 1, 1, "male", "young_adult_16_25", 0.5, "directory_1839",
           "Counted with the commerce clerks; the trade is a store whatever it sells.")),
        R(("tinsmith", "journeyman", 0, 0, 1, "male", "young_adult_16_25", 0.25,
           "period_convention",
           "A stove dealer who fits and repairs keeps a tinner. Analogue: the town's own "
           "tin and copper manufactories, which the census counts separately.")),
    ],
    "drug_store": [
        R(("clerk", "clerk", 0, 1, 1, "male", "young_adult_16_25", 0.5, "directory_1839",
           "13 druggists in 1839 and the commerce clerk share over them. The druggist's "
           "clerk is often reading medicine, which is why he boards in the house.")),
    ],
    "book_store": [
        R(("clerk", "clerk", 0, 1, 1, "either", "young_adult_16_25", 0.5, "directory_1839",
           "A book store is a store. `either`: the trade is one of the few a town of this "
           "date let a woman keep counter in, and the directory refuses neither.")),
    ],
    "millinery_and_dressmaking": [
        R(("dressmaker", "journeyman", 0, 1, 2, "female", "young_adult_16_25", 0.3,
           "period_convention",
           "The needle trades ran on assistants and the 1835 notices advertise for them. "
           "Analogue: the 1839 list's six milliners and its tailoresses, and the 1840 "
           "column that has no row for them at all.")),
        R(("dressmaker", "apprentice", 0, 0, 1, "female", "youth_12_18", 0.6,
           "period_convention",
           "A girl bound to the needle, living in. Analogue: as above.")),
    ],
    "small_luxury_shop": [
        R(("clerk", "clerk", 0, 0, 1, "either", "young_adult_16_25", 0.4, "period_convention",
           "A jeweller's, hatter's or confectioner's is a one-hand shop at this date. "
           "Analogue: the 1839 list's 7 watchmakers and 5 hatters, none with a counted hand.")),
    ],
    "forwarding_and_warehouse": [
        R(("clerk", "clerk", 1, 1, 2, "male", "young_adult_16_25", 0.4, "directory_1839",
           "The forwarding house is the heaviest clerical trade on the river: 15 forwarding "
           "and commission principals in 1839 and the bookkeepers counted with the clerks.")),
        R(("labourer", "household_member", 1, 2, 3, "male", "adult_18_45", 0.0,
           "directory_1839",
           "Warehousemen: the 1839 list prints the term only twice, which is the floor and "
           "not the count — a warehouse on the South Water landings was worked by hands the "
           "directory booked as labourers, of whom it counts 73.")),
        R(("teamster", "household_member", 0, 1, 2, "male", "adult_18_45", 0.0,
           "directory_1839",
           "41 teamsters and 30 draymen in 1839, against a river trade this one grew out of.")),
    ],
    "lumber_yard": [
        R(("labourer", "household_member", 1, 2, 3, "male", "adult_18_45", 0.0,
           "period_convention",
           "A yard is piled and loaded by hand. Analogue: the forwarding houses above, whose "
           "warehouse labour this model prices the same way.")),
    ],
    "auction_and_commission_room": [
        R(("clerk", "clerk", 0, 1, 1, "male", "young_adult_16_25", 0.4, "directory_1839",
           "A sale is cried by the auctioneer and booked by somebody. 9 auctioneers in 1839.")),
        R(("labourer", "household_member", 0, 0, 1, "male", "adult_18_45", 0.0,
           "period_convention", "A porter on sale days. Analogue: the stores above.")),
    ],
    "land_or_insurance_office": [
        R(("clerk", "clerk", 0, 0, 1, "male", "young_adult_16_25", 0.3, "directory_1839",
           "25 land agents in 1839; the office is the principal and his papers, and a clerk "
           "only at the busiest.")),
    ],
    "tavern_or_hotel": [
        R(("tavern_keeper", "household_member", 1, 1, 1, "predominantly_male", "adult_any", 1.0,
           "period_convention",
           "The bar-keeper. `bar_keeper` is NOT in the residents occupation vocabulary and is "
           "carried here under the nearest term it does hold; see `vocabulary_gaps`. "
           "Analogue: the 1839 list's two bar-keepers against 50 keepers of houses — a floor, "
           "and the clearest evidence in this file that the directory did not canvass service.")),
        R(("labourer", "household_member", 0, 1, 1, "male", "adult_18_45", 0.7,
           "period_convention",
           "The hostler, who is a house's stable. `hostler` is outside the vocabulary. "
           "Analogue: the livery stables below, and the 1839 list's silence.")),
        R(("domestic", "servant", 1, 1, 1, "female", "adult_18_45", 0.8, "period_convention",
           "The cook. A house that feeds travellers cooks every day of the week. Analogue: "
           "the 1839 list's five domestics against a town of 4,000 — a floor, not a count.")),
        R(("domestic", "servant", 0, 1, 2, "female", "young_adult_16_25", 0.9,
           "period_convention",
           "Chambermaids, by the number of beds. Analogue: the lodging model's per-place "
           "capacities, which this row does not itself read.")),
        R(("domestic", "servant", 0, 1, 1, "male", "youth_12_18", 1.0, "period_convention",
           "The boy — boots, errands, the yard. Analogue: as above.")),
    ],
    "printing_office": [
        R(("printer", "journeyman", 1, 1, 2, "male", "young_adult_16_25", 0.3,
           "directory_1839",
           "Journeymen at case and press. The 1839 list counts 15 printers — compositors, "
           "pressmen and job printers — against 2 editors, and the two offices of the 1835 "
           "census are the establishments those hands worked in four years earlier.")),
        R(("printer", "apprentice", 0, 1, 2, "male", "youth_12_18", 0.8, "period_convention",
           "The apprentice, who lives in. Analogue: the journeyman row above; the project "
           "holds no roll of the Democrat's or the American's hands — see "
           "docs/RESEARCH/chicago_democrat_office.md, which reads the imprint and no roll.")),
    ],
    "law_office": [
        R(("clerk", "clerk", 0, 0, 1, "male", "young_adult_16_25", 0.3, "period_convention",
           "The student-at-law, who read in an office rather than at a school. Analogue: the "
           "1839 list's 11 students against 45 attorneys, a quarter of them.")),
    ],
    "physician_practice": [
        R(("clerk", "clerk", 0, 0, 1, "male", "young_adult_16_25", 0.4, "period_convention",
           "A physician's student, on the same footing as the law student. Analogue: as above.")),
    ],
    "dentist_stand": [],
    "school": [
        R(("schoolteacher", "household_member", 0, 0, 1, "either", "adult_any", 0.0,
           "period_convention",
           "An assistant, at the larger schools only; the town's schools of 1835 are one "
           "room and one teacher. Analogue: the 1839 list's 13 schoolteachers.")),
    ],
    "smithy": [
        R(("blacksmith", "journeyman", 0, 1, 1, "male", "young_adult_16_25", 0.3,
           "period_convention",
           "The striker, who swings while the smith holds. Analogue: the 1839 list's 48 "
           "smiths in a town that had 5 shops in 1835.")),
        R(("blacksmith", "apprentice", 0, 0, 1, "male", "youth_12_18", 0.7,
           "period_convention", "A bound boy. Analogue: as above.")),
    ],
    "wood_trades_shop": [
        R(("joiner", "journeyman", 0, 1, 2, "male", "young_adult_16_25", 0.2,
           "directory_1839",
           "The building trades are the largest in the 1839 list — 133 carpenters and 54 "
           "builders — and a master's shop is where they stood.")),
        R(("joiner", "apprentice", 0, 1, 1, "male", "youth_12_18", 0.6, "period_convention",
           "Analogue: the journeyman row above.")),
    ],
    "tailor_shop": [
        R(("tailor", "journeyman", 0, 1, 2, "male", "young_adult_16_25", 0.3,
           "directory_1839", "42 tailors in 1839 against 7 tailoring houses here.")),
        R(("dressmaker", "journeyman", 0, 1, 2, "female", "adult_18_45", 0.1,
           "period_convention",
           "The tailoress, who sewed what the cutter cut. Analogue: the 1839 list's printed "
           "'cloak maker and tailoress', counted under tailor, and the millinery rows above.")),
        R(("tailor", "apprentice", 0, 0, 1, "male", "youth_12_18", 0.6, "period_convention",
           "Analogue: the journeyman row above.")),
    ],
    "shoemaker_shop": [
        R(("shoemaker", "journeyman", 0, 1, 1, "male", "young_adult_16_25", 0.3,
           "directory_1839", "27 shoemakers in 1839 against 8 shops here.")),
        R(("shoemaker", "apprentice", 0, 0, 1, "male", "youth_12_18", 0.6, "period_convention",
           "Analogue: the journeyman row above.")),
    ],
    "leather_shop": [
        R(("harness_maker", "journeyman", 0, 1, 1, "male", "young_adult_16_25", 0.3,
           "directory_1839", "6 harness makers in 1839 against 3 shops here.")),
        R(("harness_maker", "apprentice", 0, 0, 1, "male", "youth_12_18", 0.6,
           "period_convention", "Analogue: the journeyman row above.")),
    ],
    "tinner_shop": [
        R(("tinsmith", "journeyman", 0, 1, 1, "male", "young_adult_16_25", 0.3,
           "directory_1839", "8 tinsmiths in 1839; the census counts 2 manufactories in 1835.")),
        R(("tinsmith", "apprentice", 0, 1, 1, "male", "youth_12_18", 0.6, "period_convention",
           "Analogue: the journeyman row above.")),
    ],
    "bakery": [
        R(("baker", "journeyman", 0, 1, 1, "male", "young_adult_16_25", 0.5, "directory_1839",
           "11 bakers in 1839. A bakehouse is worked at night and the hand sleeps there.")),
        R(("labourer", "household_member", 0, 0, 1, "male", "youth_12_18", 0.3,
           "period_convention", "A boy on the delivery basket. Analogue: the bakehouse above.")),
    ],
    "butcher_shop": [
        R(("butcher", "journeyman", 0, 1, 1, "male", "adult_18_45", 0.2, "directory_1839",
           "16 butchers in 1839 against the one shop and the market here.")),
    ],
    "painter_shop": [
        R(("painter", "journeyman", 0, 1, 1, "male", "young_adult_16_25", 0.2,
           "directory_1839", "14 painters in 1839; the trade works in pairs.")),
        R(("painter", "apprentice", 0, 0, 1, "male", "youth_12_18", 0.5, "period_convention",
           "Analogue: the journeyman row above.")),
    ],
    "livery_stable": [
        R(("labourer", "household_member", 1, 1, 2, "male", "adult_18_45", 0.6,
           "period_convention",
           "Hostlers. `hostler` is outside the vocabulary; see `vocabulary_gaps`. Analogue: "
           "the 11 livery stable keepers of 1839, against whom the list prints no hostler.")),
        R(("labourer", "household_member", 0, 1, 1, "male", "youth_12_18", 0.8,
           "period_convention", "The stable boy. Analogue: as above.")),
    ],
    "mill": [
        R(("sawyer", "household_member", 1, 2, 3, "male", "adult_18_45", 0.2,
           "directory_1839",
           "6 sawyers and 7 millers in 1839; a steam saw-mill is a gang and not a man.")),
    ],
    "brewery": [
        R(("labourer", "household_member", 1, 2, 3, "male", "adult_18_45", 0.2,
           "directory_1839", "3 brewers in 1839 for 2 breweries in the 1835 census — the "
           "principals only; the mash was worked by hands the list booked as labourers.")),
    ],
    "foundry": [
        R(("founder", "journeyman", 1, 2, 4, "male", "adult_18_45", 0.1, "directory_1839",
           "12 founders in 1839. A furnace is the largest hand-count of any shop in town.")),
    ],
    "soap_and_candle_works": [
        R(("labourer", "household_member", 0, 1, 2, "male", "adult_18_45", 0.1,
           "directory_1839", "8 soap and candle makers in 1839 across a handful of works.")),
    ],
    "surveyor_office": [
        R(("labourer", "household_member", 0, 1, 2, "male", "adult_18_45", 0.0,
           "period_convention",
           "Chainmen, hired by the survey and not by the year. Analogue: the 13 surveyors of "
           "1839, against whom the list prints no chainman.")),
    ],
    "post_office": [
        R(("clerk", "clerk", 0, 0, 1, "either", "adult_any", 0.0, "period_convention",
           "An assistant in the office. Analogue: the two postmasters of 1839.")),
    ],
    "unclassified": [],
}

#: Roles this model names that data/residents/index.json does not hold as an
#: occupation. T-1189 may not write them onto a person until it does.
ROLE_TERMS_WANTED = {
    "bar_keeper": "the tavern and hotel bar, carried here as `tavern_keeper`",
    "hostler": "the tavern, hotel and livery stable, carried here as `labourer`",
    "cook": "the tavern and hotel kitchen, carried here as `domestic`",
    "chambermaid": "the tavern and hotel chambers, carried here as `domestic`",
    "warehouseman": "the forwarding houses, carried here as `labourer`",
    "student_at_law": "the law offices, carried here as `clerk`",
}


class Fault(Exception):
    """A refusal, printed and exited on. Never a warning."""


# ------------------------------------------------------------------ reading --

def load() -> dict:
    if not BUSINESSES.is_dir():
        raise Fault("the business layer is missing")
    businesses = []
    for path in sorted(BUSINESSES.glob("*.json")):
        businesses.append(json.loads(path.read_text(encoding="utf-8")))
    if not businesses:
        raise Fault("the business layer holds no records")
    return {
        "businesses": businesses,
        "trade_1839": json.loads(TRADE_TABLE_1839.read_text(encoding="utf-8")),
        "town_model": json.loads(TOWN_MODEL.read_text(encoding="utf-8")),
        "crosswalk": json.loads(CROSSWALK.read_text(encoding="utf-8")),
        "vocabulary": json.loads(RESIDENT_INDEX.read_text(encoding="utf-8"))["vocabulary"],
    }


def classify(record: dict) -> str:
    """The staffing class of one business, READ off its own trade term.

    A record with an occupation the table has never heard of is a REFUSAL and
    not an `unclassified`: the two mean different things, and collapsing them
    would hide a vocabulary term nobody has priced.
    """
    occ = record.get("occupation")
    if occ is None:
        return "unclassified"
    if occ not in CLASS_OF_OCCUPATION:
        raise Fault(f"{record['id']} carries occupation `{occ}`, which no staffing class "
                    "prices — add it to CLASS_OF_OCCUPATION or rule it unstaffed")
    return CLASS_OF_OCCUPATION[occ]


def principals(record: dict) -> int:
    """People the layer already has working this house: proprietors and partners.

    Deduplicated by person id where the record carries one, because a man who is
    both proprietor and partner of the same firm is one worker.
    """
    seen, loose = set(), 0
    for person in list(record.get("proprietors") or []) + list(record.get("partners") or []):
        pid = person.get("person_id") if isinstance(person, dict) else None
        if pid:
            seen.add(pid)
        else:
            loose += 1
    return len(seen) + loose


# -------------------------------------------------------------- calibration --

def calibrate_1839(trade_1839: dict) -> dict:
    """THE ONE RATIO THIS MODEL DERIVES, and the finding that bounds its use."""
    rows = {r["trade"]: r for r in trade_1839["rows"]}
    commerce = {t: r["count"] for t, r in rows.items()
                if r["column_1840"] == "Commerce" and t not in STAFF_TRADES_1839}
    principals_1839 = sum(commerce.values())
    clerks_1839 = rows.get("clerk", {}).get("count", 0)
    if principals_1839 <= 0 or clerks_1839 <= 0:
        raise Fault("the 1839 trade table no longer holds the clerk calibration's terms")
    keepers = sum(rows[t]["count"] for t in sorted(ENTERTAINMENT_TRADES_1839) if t in rows)
    service = {t: rows.get(t, {}).get("count", 0)
               for t in ("bar_keeper", "domestic", "laundress")}
    # THE LIKE-FOR-LIKE DENOMINATOR, and why there are two of these. The broad
    # ratio divides the clerks by EVERY commerce principal, tavern and livery
    # keepers included, and those trades keep no counting house — so it is the
    # wrong denominator for a rule that gives clerks only to stores and offices.
    # The second ratio divides by exactly the 1839 trades this model's own class
    # table sends to a class with a clerk row. BOTH ARE PRINTED, because
    # narrowing a denominator is also how a model is quietly tuned until it
    # passes, and the reader is owed the wider number beside the one used.
    clerk_classes = {c for c, roles in STAFFING_RULES.items()
                     if any(r[0] == "clerk" for r in roles)}
    like = {t: c for t, c in commerce.items()
            if CLASS_OF_OCCUPATION.get(t) in clerk_classes}
    like_principals = sum(like.values())
    if like_principals <= 0:
        raise Fault("no 1839 trade maps to a class this model gives a clerk to")
    return {
        "clerks_per_commerce_principal": {
            "clerks_1839": clerks_1839,
            "commerce_principals_1839": principals_1839,
            "ratio": round(clerks_1839 / principals_1839, 5),
            "trades_counted_as_principals": sorted(commerce),
            "trades_held_back_as_staff": sorted(STAFF_TRADES_1839),
            "what_it_is": "clerks per PERSON in a commerce trade, not per establishment — "
                          "the directory counts people and prints no houses. It is the WIDE "
                          "reading, and it divides by tavern and livery keepers who kept no "
                          "counting house; the like-for-like ratio below is the one the "
                          "reconciliation uses, and this one stands beside it so that the "
                          "narrowing is visible.",
            "date_caution": trade_1839["date_note"],
            "source_ids": [trade_1839["source_id"]],
        },
        "clerks_per_clerk_employing_principal": {
            "clerks_1839": clerks_1839,
            "principals_1839": like_principals,
            "ratio": round(clerks_1839 / like_principals, 5),
            "trades_counted_as_principals": sorted(like),
            "trades_dropped_from_the_wide_denominator": sorted(
                set(commerce) - set(like)),
            "what_it_is": "the same 152 clerks over only those 1839 trades that this "
                          "model's class table sends to an establishment with a clerk in "
                          "it. A trade the 1839 list counts and this town holds no record "
                          "of — the banker, the ship chandler — falls out of the "
                          "denominator with the taverns, and that is a NARROWING: it "
                          "raises the ratio and so flatters the model. It is used because "
                          "it is the only comparison in matching units, and the wide "
                          "reading above is printed so the reader can take the other view.",
            "date_caution": trade_1839["date_note"],
            "source_ids": [trade_1839["source_id"]],
        },
        "the_directory_did_not_canvass_service": {
            "keepers_of_houses_of_entertainment_1839": keepers,
            "bar_keepers_printed": service["bar_keeper"],
            "domestics_printed": service["domestic"],
            "laundresses_printed": service["laundress"],
            "hostlers_printed": 0,
            "cooks_printed": 0,
            "chambermaids_printed": 0,
            "finding": f"{keepers} keepers of taverns, boarding houses and refectories stand "
                       f"in the 1839 list against {service['bar_keeper']} bar-keepers, "
                       f"{service['domestic']} domestics and {service['laundress']} laundress. "
                       "No hostler, cook or chambermaid is printed at all. That is a list of "
                       "householders, so it is a FLOOR for service labour and never a count — "
                       "which is why every service row in this model is `period_convention`.",
            "source_ids": [trade_1839["source_id"]],
        },
    }


def employed_bracket(town_model: dict) -> dict:
    for section in town_model["sections"]:
        if section["key"] != "occupations":
            continue
        for fig in section["figures"]:
            if fig["figure"] == "employed_persons":
                return {"low": fig["low"], "high": fig["high"], "method": fig["method"]}
    raise Fault("the town model no longer carries an `employed_persons` figure")


# ------------------------------------------------------------- the dry run --

def dry_run(businesses: list, classes_used: dict) -> dict:
    """Apply the table to the layer AS IT STANDS. Counts only; nobody is named."""
    by_role: dict[tuple, dict] = {}
    totals = {"low": 0, "typical": 0, "high": 0}
    by_sex = {k: {"low": 0, "typical": 0, "high": 0}
              for k in ("male", "female", "either", "predominantly_male",
                        "predominantly_female")}
    living_in = {"low": 0.0, "typical": 0.0, "high": 0.0}
    for cls, n in sorted(classes_used.items()):
        for term, rel, low, typ, high, sex, band, live_in, basis, note in STAFFING_RULES[cls]:
            key = (term, rel, sex, band)
            row = by_role.setdefault(key, {
                "occupation_term": term, "household_relationship": rel, "sex_rule": sex,
                "age_band": band,
                "low": 0, "typical": 0, "high": 0, "from_classes": [],
            })
            row["low"] += low * n
            row["typical"] += typ * n
            row["high"] += high * n
            row["from_classes"].append(cls)
            for bucket, count in (("low", low), ("typical", typ), ("high", high)):
                totals[bucket] += count * n
                by_sex[sex][bucket] += count * n
                living_in[bucket] += count * n * live_in
    for row in by_role.values():
        row["from_classes"] = sorted(set(row["from_classes"]))
    layer_principals = sum(principals(b) for b in businesses)
    return {
        "businesses_staffed": sum(classes_used.values()),
        "principals_already_in_the_layer": layer_principals,
        "staff_by_role": sorted(by_role.values(),
                                key=lambda r: (-r["typical"], r["occupation_term"],
                                               r["household_relationship"], r["age_band"])),
        "staff_by_sex_rule": {k: v for k, v in sorted(by_sex.items()) if v["high"]},
        "staff_total": totals,
        "staff_living_on_the_premises": {k: round(v, 1) for k, v in living_in.items()},
        "working_persons_implied": {k: layer_principals + v for k, v in totals.items()},
        "not_a_roster": "Counts of ROLES over establishments. No person is named, drawn or "
                        "written; T-1189 does that and this is the quota it does it to.",
    }


def reconcile(run: dict, calibration: dict, employed: dict,
              clerk_class_principals: int, modelled_clerks: int) -> dict:
    """Set the dry run against the two figures that can contradict it.

    THE COMPARISON IS IN MATCHING UNITS OR IT IS WORTHLESS. Both sides here are
    counting-house clerks over counting-house principals: the 1839 denominator
    is the trades this model's class table gives a clerk to, and the numerator
    is the clerks this model puts in exactly those classes. The first draft
    divided all 152 clerks by all 312 commerce principals and compared that to
    every clerk in the model, taverns and liveries on one side and law students
    on the other, and reported a 66% overshoot that was mostly the mismatch.
    """
    like = calibration["clerks_per_clerk_employing_principal"]
    wide = calibration["clerks_per_commerce_principal"]
    predicted_clerks = round(clerk_class_principals * like["ratio"], 1)
    predicted_wide = round(clerk_class_principals * wide["ratio"], 1)
    clerk_gap = round(modelled_clerks - predicted_clerks, 1)
    implied = run["working_persons_implied"]
    inside = employed["low"] <= implied["typical"] <= employed["high"]
    return {
        "against_the_clerk_calibration": {
            "layer_principals_in_clerk_employing_classes": clerk_class_principals,
            "ratio_1839_like_for_like": like["ratio"],
            "clerks_the_1839_ratio_predicts": predicted_clerks,
            "clerks_this_model_puts_in_those_classes": modelled_clerks,
            "delta": clerk_gap,
            "tolerance": round(max(5.0, 0.25 * predicted_clerks), 1),
            "agrees": abs(clerk_gap) <= max(5.0, 0.25 * predicted_clerks),
            "on_the_wide_ratio_instead": {
                "ratio_1839_wide": wide["ratio"],
                "clerks_predicted": predicted_wide,
                "delta": round(modelled_clerks - predicted_wide, 1),
                "note": "The wide ratio divides the same clerks by tavern, livery and "
                        "boarding-house keepers as well, and on it the model looks "
                        "over-clerked. Printed rather than buried: it is the reading a "
                        "sceptic would take.",
            },
            "if_it_disagrees": "The per-house rules are period convention and the ratio is a "
                               "1839 measurement of a bigger town. A disagreement is STATED "
                               "here and neither side is moved to close it; T-1189 spends "
                               "against the rules and reports the residual.",
        },
        "against_the_town_model_employment": {
            "employed_persons_low": employed["low"],
            "employed_persons_high": employed["high"],
            "working_persons_implied_typical": implied["typical"],
            "working_persons_implied_low": implied["low"],
            "working_persons_implied_high": implied["high"],
            "inside_the_bracket": inside,
            "method": employed["method"],
            "what_it_does_not_mean": "The town model's employed persons counts EVERY working "
                                     "person — the labourers of the harbour works, the "
                                     "garrison, the farmers outside the limits, the domestic "
                                     "service the 1840 columns have no row for. The businesses "
                                     "of this layer are a PART of that figure, so falling "
                                     "below the low end is expected and falling above it is a "
                                     "refusal.",
        },
    }


# ----------------------------------------------------------------- the build --

def build(data: dict) -> dict:
    businesses = [b for b in data["businesses"] if b.get("present_at_scene_date")]
    classes_used: dict[str, int] = {}
    unclassified = []
    for record in businesses:
        cls = classify(record)
        classes_used[cls] = classes_used.get(cls, 0) + 1
        if cls == "unclassified":
            unclassified.append({
                "id": record["id"], "name": record.get("name"),
                "type": record.get("type"),
                "why_no_staff": "The layer gives this record no `occupation`, so there is no "
                                "establishment kind to staff it as. Giving it one here would "
                                "be T-1182's audit performed by a tool with no licence for it.",
            })
    for cls in sorted(classes_used):
        if cls not in STAFFING_RULES:
            raise Fault(f"class `{cls}` is used by the layer and has no staffing rule")

    calibration = calibrate_1839(data["trade_1839"])
    employed = employed_bracket(data["town_model"])
    run = dry_run(businesses, classes_used)
    clerk_classes = {c for c, roles in STAFFING_RULES.items()
                     if any(r[0] == "clerk" for r in roles)}
    clerk_class_principals = sum(
        principals(b) for b in businesses if classify(b) in clerk_classes)
    modelled_clerks = sum(
        r[3] * classes_used.get(cls, 0)
        for cls in clerk_classes for r in STAFFING_RULES[cls] if r[0] == "clerk")
    rec = reconcile(run, calibration, employed, clerk_class_principals, modelled_clerks)

    occupations = set(data["vocabulary"]["occupations"])
    relationships = set(data["vocabulary"]["relationships"])
    classes = []
    for cls in sorted(STAFFING_RULES):
        roles = []
        for term, rel, low, typ, high, sex, band, live_in, basis, note in STAFFING_RULES[cls]:
            if term not in occupations:
                raise Fault(f"{cls} names occupation `{term}`, which the residents "
                            "vocabulary does not hold")
            if rel not in relationships:
                raise Fault(f"{cls} names relationship `{rel}`, which the residents "
                            "vocabulary does not hold")
            if not low <= typ <= high:
                raise Fault(f"{cls}/{term} is not ordered low <= typical <= high")
            roles.append({
                "role": term, "occupation_term": term, "household_relationship": rel,
                "count_low": low, "count_typical": typ, "count_high": high,
                "sex_rule": sex, "age_band": band,
                "lives_on_premises": live_in,
                "basis": basis, "note": note,
                "source_ids": ([data["trade_1839"]["source_id"]]
                               if basis == "directory_1839" else []),
            })
        classes.append({
            "class": cls,
            "reads_as": CLASS_WORDS[cls],
            "occupations_in_this_class": sorted(
                o for o, c in CLASS_OF_OCCUPATION.items() if c == cls),
            "column_1840": COLUMN_1840[cls],
            "establishments_at_the_scene_date": classes_used.get(cls, 0),
            "staff_roles": roles,
            "staff_per_establishment": {
                "low": sum(r["count_low"] for r in roles),
                "typical": sum(r["count_typical"] for r in roles),
                "high": sum(r["count_high"] for r in roles),
            },
        })

    return {
        "$schema_note": "DERIVED — regenerate with tools/build_staffing_model_1835.py "
                        "--build; tools/check.sh re-derives it. Do not hand-edit.",
        "id": "1835_business_staffing_model",
        "ticket": TICKET,
        "target_date": SCENE_DATE,
        "generated_by": "tools/build_staffing_model_1835.py --build",
        "not_a_reading": "an adjudication over committed files — no page of any source is "
                         "read here, and no person is written",
        "writes_no_person": True,
        "inputs": [
            "data/businesses/*.json",
            "data/research/directories/fergus_1839_trade_table.json",
            "data/reconstruction/1835_town_model.json",
            "data/research/books/trade_census_1835_crosswalk.json",
            "data/residents/index.json",
        ],
        "vocabularies": {
            "age_bands": AGE_BANDS,
            "sex_rules": SEX_RULES,
            "bases": BASES,
            "age_bands_are_this_model_s_own": "These say what age a kind of hand was. The "
                                              "residents layer's age bands say how a card's "
                                              "age was EVIDENCED. They are different "
                                              "questions and this file does not mix them.",
        },
        "calibration": calibration,
        "classes": classes,
        "the_shop_household_rule": {
            "shared_with": "T-1163",
            "rule": "`lives_on_premises` is the share of holders of a role who slept in the "
                    "proprietor's house or over the shop, and `household_relationship` is the "
                    "term their card carries in that household. A clerk at 0.5 means half the "
                    "clerks of that class are household members of their employer and half "
                    "keep their own lodging or board elsewhere.",
            "who_lives_in": sorted(
                {f"{cls}/{r['role']}/{r['household_relationship']}"
                 for c in classes for r in c["staff_roles"] for cls in [c["class"]]
                 if r["lives_on_premises"] >= 0.5}),
            "not_a_seating": "A share is not a bed. The lodging model (T-1370) owns capacity "
                             "and T-1371 owns who sleeps where; this rule only says which "
                             "staff are candidates for the employer's household.",
        },
        "vocabulary_gaps": [
            {"term": term, "wanted_for": why,
             "rule": "may not be written onto a person until data/residents/index.json "
                     "carries it"}
            for term, why in sorted(ROLE_TERMS_WANTED.items())
        ],
        "unstaffed_records": sorted(unclassified, key=lambda r: r["id"]),
        "dry_run": run,
        "reconciliation": rec,
        "open_questions": [
            {"question": "Is the 1839 clerk ratio a prior for 1835 at all?",
             "why_it_matters": "It is the only staffing figure the project holds, and 1839 is "
                               "a town with a bank, a canal and four more years of growth. "
                               "The model uses it to CHECK its rules and not to set them, "
                               "which is the most weight it will bear.",
             "owned_by": ["T-1183", "T-1189"]},
            {"question": "What does the town do about the service labour no source counts?",
             "why_it_matters": "The 1840 industry columns have no row for domestic service "
                               "and the 1839 directory prints five domestics. The town model "
                               "already says its trade split understates household labour by "
                               "an amount it cannot bound; this model reconstructs that "
                               "labour for businesses and cannot bound it either.",
             "owned_by": ["T-1183", "T-1163", "T-1189"]},
            {"question": "The records the layer gives no trade to.",
             "why_it_matters": f"{len(unclassified)} of the {len(businesses)} houses standing "
                               "at the scene date carry no `occupation`, so they are staffed "
                               "by nobody here. T-1182's audit is what fixes that, and until "
                               "it runs this model understates the town.",
             "owned_by": ["T-1182"]},
        ],
    }


# ---------------------------------------------------------------- the report --

def report_text(doc: dict) -> str:
    rec = doc["reconciliation"]
    cal = doc["calibration"]["clerks_per_commerce_principal"]
    like = doc["calibration"]["clerks_per_clerk_employing_principal"]
    svc = doc["calibration"]["the_directory_did_not_canvass_service"]
    run = doc["dry_run"]
    out = [
        "# The 1835 business staffing model",
        "",
        f"**Derived** — `{doc['generated_by']}` · ticket {doc['ticket']} · "
        f"scene date {doc['target_date']}. Do not hand-edit.",
        "",
        "Every business in this town was, until this file, worked by its proprietor and "
        "nobody else. The relationship vocabulary has held `clerk`, `apprentice`, "
        "`journeyman` and `servant` since the resident layer was built and not one person "
        "stood in any of them. This is the rule T-1189 staffs by — **it writes no person, "
        "and names none**.",
        "",
        "## The ratio derived here, and the narrower one beside it",
        "",
        f"Fergus's 1839 directory prints **{cal['clerks_1839']} clerks** against "
        f"**{cal['commerce_principals_1839']} principals** in the commerce trades — a ratio of "
        f"**{cal['ratio']}** clerks per commerce head. It is clerks per PERSON and not per "
        "house, because the directory counts people and prints no establishments, so it is "
        "used to predict a clerk TOTAL and to check the per-house rules below. It never sets "
        "them.",
        "",
        f"That denominator includes tavern and livery keepers, who kept no counting house. "
        f"Divided instead by only the {like['principals_1839']} principals in the 1839 trades "
        f"this model's own class table gives a clerk to, the ratio is **{like['ratio']}**. "
        "That narrowing raises the ratio and so flatters the model, which is why both are "
        "printed and the reconciliation below reports the delta on each.",
        "",
        f"> {cal['date_caution']}",
        "",
        "## And the finding that bounds it",
        "",
        f"{svc['finding']}",
        "",
        "## The classes",
        "",
        "| establishment | at the scene date | staff low–typical–high | roles |",
        "|---|---:|---|---|",
    ]
    for c in doc["classes"]:
        per = c["staff_per_establishment"]
        roles = ", ".join(f"{r['role']} ({r['household_relationship']}, {r['age_band']})"
                          for r in c["staff_roles"]) or "—"
        out.append(f"| {c['reads_as']} | {c['establishments_at_the_scene_date']} | "
                   f"{per['low']}–{per['typical']}–{per['high']} | {roles} |")
    out += ["", "## Every role, with its basis", ""]
    for c in doc["classes"]:
        if not c["staff_roles"]:
            continue
        out += [f"### {c['reads_as']} — {c['establishments_at_the_scene_date']} at the scene "
                f"date", ""]
        for r in c["staff_roles"]:
            out += [f"- **{r['role']}** as *{r['household_relationship']}* — "
                    f"{r['count_low']}–{r['count_typical']}–{r['count_high']}, "
                    f"{r['sex_rule']}, {r['age_band']}, lives in "
                    f"{int(round(r['lives_on_premises'] * 100))}% · `{r['basis']}`  \n"
                    f"  {r['note']}"]
        out.append("")
    out += ["## The shop household rule", "",
            doc["the_shop_household_rule"]["rule"], "",
            doc["the_shop_household_rule"]["not_a_seating"], "",
            "## The dry run over the layer as it stands", "",
            f"{run['businesses_staffed']} businesses standing on {doc['target_date']}, "
            f"{run['principals_already_in_the_layer']} proprietors and partners already on "
            f"their records.", "",
            "| role | as | sex | age | low | typical | high |",
            "|---|---|---|---|---:|---:|---:|"]
    for r in run["staff_by_role"]:
        out.append(f"| {r['occupation_term']} | {r['household_relationship']} | "
                   f"{r['sex_rule']} | {r['age_band']} | {r['low']} | {r['typical']} | "
                   f"{r['high']} |")
    t = run["staff_total"]
    w = run["working_persons_implied"]
    out += ["", f"**Staff implied:** {t['low']}–{t['typical']}–{t['high']}, of whom "
                f"{run['staff_living_on_the_premises']['typical']} live on the premises at the "
                "typical figure.",
            "", f"**Working persons implied** (principals + staff): "
                f"{w['low']}–{w['typical']}–{w['high']}.", ""]
    clerk = rec["against_the_clerk_calibration"]
    wide = clerk["on_the_wide_ratio_instead"]
    emp = rec["against_the_town_model_employment"]
    out += ["## Reconciliation", "",
            f"- **Against the 1839 clerk ratio, like for like.** "
            f"{clerk['layer_principals_in_clerk_employing_classes']} principals stand in the "
            f"layer's clerk-employing classes; × {clerk['ratio_1839_like_for_like']} that "
            f"predicts {clerk['clerks_the_1839_ratio_predicts']} clerks, and the per-house "
            f"rules put {clerk['clerks_this_model_puts_in_those_classes']} there — a delta of "
            f"{clerk['delta']} against a tolerance of {clerk['tolerance']}. "
            + ("They agree." if clerk["agrees"] else "**They disagree, and neither is moved.**"),
            f"- **And on the wide ratio.** Divide the same 1839 clerks by every commerce "
            f"principal, tavern and livery keepers included, and the ratio falls to "
            f"{wide['ratio_1839_wide']}, predicting {wide['clerks_predicted']} — a delta of "
            f"{wide['delta']}. {wide['note']}",
            f"- **Against the town model's employment.** "
            f"{emp['working_persons_implied_typical']} working persons implied, against "
            f"{emp['employed_persons_low']}–{emp['employed_persons_high']} employed persons. "
            + ("Inside the bracket." if emp["inside_the_bracket"]
               else "Below the low end, which is expected: " + emp["what_it_does_not_mean"]),
            ""]
    if doc["vocabulary_gaps"]:
        out += ["## Terms the residents vocabulary does not hold", "",
                "Each is carried under the nearest term index.json does hold, and may not be "
                "written onto a person until the vocabulary carries the real one.", "",
                "| wanted | for | carried as |", "|---|---|---|"]
        for g in doc["vocabulary_gaps"]:
            carried = g["wanted_for"].split("carried here as ")[-1].strip("`")
            out.append(f"| `{g['term']}` | {g['wanted_for'].split(', carried')[0]} | "
                       f"`{carried}` |")
        out.append("")
    if doc["unstaffed_records"]:
        out += [f"## The {len(doc['unstaffed_records'])} houses this model cannot staff", "",
                "No `occupation` on the record, so no establishment kind, so no staff. "
                "T-1182's audit is what fixes this.", ""]
        for r in doc["unstaffed_records"]:
            out.append(f"- `{r['id']}` — {r['name']}")
        out.append("")
    out += ["## Open questions", ""]
    for q in doc["open_questions"]:
        out.append(f"- **{q['question']}** {q['why_it_matters']} ({', '.join(q['owned_by'])})")
    out.append("")
    return "\n".join(out)


# -------------------------------------------------------------- the commands --

def cmd_build() -> int:
    doc = build(load())
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    MODEL_OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report_text(doc), encoding="utf-8")
    run = doc["dry_run"]
    print(f"OK: 1835 business staffing model — {len(doc['classes'])} establishment classes over "
          f"{run['businesses_staffed']} houses, {run['staff_total']['low']}–"
          f"{run['staff_total']['typical']}–{run['staff_total']['high']} staff implied, "
          "nobody written")
    return 0


def cmd_check() -> int:
    if not MODEL_OUT.exists():
        raise Fault(f"{MODEL_OUT.relative_to(ROOT)} has never been built")
    doc = build(load())
    on_disk = json.loads(MODEL_OUT.read_text(encoding="utf-8"))
    if json.dumps(doc, sort_keys=True) != json.dumps(on_disk, sort_keys=True):
        raise Fault(f"{MODEL_OUT.relative_to(ROOT)} no longer re-derives from its inputs — "
                    "run tools/build_staffing_model_1835.py --build")
    if REPORT.read_text(encoding="utf-8") != report_text(doc):
        raise Fault(f"{REPORT.relative_to(ROOT)} no longer re-derives from the model — "
                    "run tools/build_staffing_model_1835.py --build")
    # THE REFUSALS. A model that staffs the town past what the town model can
    # employ has invented workers, and a model that has written a person has
    # done T-1189's job without its acceptance.
    emp = doc["reconciliation"]["against_the_town_model_employment"]
    if emp["working_persons_implied_high"] > emp["employed_persons_high"]:
        raise Fault("the staffing model's HIGH end puts more people to work in the business "
                    "layer alone than the town model employs in the whole town")
    text = json.dumps(doc)
    for forbidden in ("person_", "rc_", "hh_", "\"persons\""):
        if forbidden in text:
            raise Fault(f"the staffing model carries a {forbidden} — it writes no person")
    print(f"OK: the 1835 business staffing model re-derives — {len(doc['classes'])} classes, "
          f"{doc['dry_run']['staff_total']['typical']} staff at the typical figure, "
          f"{len(doc['unstaffed_records'])} houses unstaffed for want of a trade")
    return 0


def cmd_self_test() -> int:
    fired = 0

    def fires(what, fn):
        nonlocal fired
        try:
            fn()
        except Fault:
            fired += 1
            return
        raise AssertionError(f"guard did not fire: {what}")

    # AN UNPRICED TRADE IS A REFUSAL, NOT A ZERO. This is the difference between
    # a business the layer gives no trade to — carried, with the reason — and a
    # trade term nobody has priced, which must stop the build.
    assert classify({"id": "x", "occupation": None}) == "unclassified"
    assert classify({"id": "x", "occupation": "grocer"}) == "grocery_and_provision_store"
    fires("a business whose trade no class prices",
          lambda: classify({"id": "biz_x", "occupation": "aeronaut"}))

    # EVERY PRICED TRADE HAS A RULE, AND EVERY RULE IS ORDERED AND IN VOCABULARY.
    for cls in set(CLASS_OF_OCCUPATION.values()) | {"unclassified"}:
        assert cls in STAFFING_RULES, cls
        assert cls in CLASS_WORDS and cls in COLUMN_1840, cls
    vocab = json.loads(RESIDENT_INDEX.read_text(encoding="utf-8"))["vocabulary"]
    for cls, roles in STAFFING_RULES.items():
        for term, rel, low, typ, high, sex, band, live_in, basis, note in roles:
            assert term in vocab["occupations"], (cls, term)
            assert rel in vocab["relationships"], (cls, rel)
            assert low <= typ <= high, (cls, term)
            assert sex in SEX_RULES and band in AGE_BANDS, (cls, term)
            assert 0.0 <= live_in <= 1.0, (cls, term)
            assert basis in BASES, (cls, basis)
            # A RECONSTRUCTED ROW NAMES ITS ANALOGUE. Without one it is an
            # opinion wearing a schema, which is the failure this file exists
            # to avoid.
            if basis == "period_convention":
                assert "nalogue" in note, (cls, term, note)

    # A PROPRIETOR WHO IS ALSO A PARTNER IS ONE WORKER.
    assert principals({"proprietors": [{"person_id": "p1"}],
                       "partners": [{"person_id": "p1"}]}) == 1
    assert principals({"proprietors": [{"person_id": "p1"}, {}], "partners": []}) == 2
    assert principals({}) == 0

    # THE CALIBRATION IS COMPUTED, NOT TYPED, and the clerk is held out of its
    # own denominator — counting clerks as commerce principals would halve the
    # ratio silently.
    data = load()
    cal = calibrate_1839(data["trade_1839"])["clerks_per_commerce_principal"]
    assert "clerk" not in cal["trades_counted_as_principals"]
    assert 0.0 < cal["ratio"] < 2.0, cal
    assert abs(cal["ratio"] - cal["clerks_1839"] / cal["commerce_principals_1839"]) < 1e-5
    # THE NARROWED DENOMINATOR IS A SUBSET OF THE WIDE ONE AND SO RAISES THE
    # RATIO. If it ever did not, the class table and the calibration would have
    # drifted apart and the reconciliation would be comparing nothing.
    like = calibrate_1839(data["trade_1839"])["clerks_per_clerk_employing_principal"]
    assert set(like["trades_counted_as_principals"]) <= set(
        cal["trades_counted_as_principals"])
    assert like["ratio"] >= cal["ratio"], (like["ratio"], cal["ratio"])
    assert "tavern_keeper" in like["trades_dropped_from_the_wide_denominator"]
    fires("a 1839 table with the calibration's terms gone",
          lambda: calibrate_1839({"rows": [], "date_note": "", "source_id": "x"}))

    # THE DIRECTORY'S SERVICE FLOOR IS REAL AND THE MODEL LEANS ON IT.
    svc = calibrate_1839(data["trade_1839"])["the_directory_did_not_canvass_service"]
    assert svc["keepers_of_houses_of_entertainment_1839"] > 10 * max(
        1, svc["bar_keepers_printed"]), svc
    for cls in ("tavern_or_hotel", "livery_stable"):
        assert all(r[8] == "period_convention" for r in STAFFING_RULES[cls]), cls

    # THE REAL BUILD CLOSES, AND IS BYTE-IDENTICAL TWICE OVER.
    doc = build(data)
    assert json.dumps(build(data), sort_keys=True) == json.dumps(doc, sort_keys=True)

    # THE DRY RUN IS ARITHMETIC OVER THE CLASSES AND NOT A SECOND OPINION.
    by_class = sum(c["staff_per_establishment"]["typical"]
                   * c["establishments_at_the_scene_date"] for c in doc["classes"])
    assert by_class == doc["dry_run"]["staff_total"]["typical"], by_class

    # AND IT NEVER EMPLOYS MORE OF THE TOWN THAN THE TOWN MODEL DOES.
    emp = doc["reconciliation"]["against_the_town_model_employment"]
    assert emp["working_persons_implied_high"] <= emp["employed_persons_high"], emp

    # NOBODY IS NAMED, DRAWN OR WRITTEN. The single line of the acceptance.
    text = json.dumps(doc)
    for forbidden in ("person_", "rc_", "hh_"):
        assert forbidden not in text, forbidden
    assert doc["writes_no_person"] is True

    run = doc["dry_run"]
    print(f"build_staffing_model_1835 self-tests pass ({fired} guards fired, "
          f"{len(doc['classes'])} classes, {run['staff_total']['low']}–"
          f"{run['staff_total']['typical']}–{run['staff_total']['high']} staff implied over "
          f"{run['businesses_staffed']} houses, nobody written)")
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
