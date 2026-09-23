#!/usr/bin/env python3
"""The scene-date register: who and what the papers put in Chicago on 1 July 1835.

    tools/compile_register.py --build       recompile register_1835.json
    tools/compile_register.py --check       the gate
    tools/compile_register.py --self-test   the gate's assertions still fire

WHAT THIS IS FOR (T-0262). The reading passes filled `gazetteer.json` with 221
businesses and 2,201 people read out of the 1833-1835 papers. A gazetteer is an
index of what was PRINTED; it says nothing about what the model should build. This
turns it into the register the seeding tickets work from — for every business, is it
standing on the scene date, where, and what does the town have to do about it; for
every person, is that somebody the town already has, somebody it invented a stand-in
for, or somebody new.

NOTHING HERE IS AUTHORED. The register is derived, wholly, from the gazetteer and
from the committed dataset beside it, and `--check` re-derives it and refuses a
committed file that a rebuild would not produce. That is the same contract
gazetteer.json is under and for the same reason: a hand-edited register is a place to
quietly promote a business into the town without an argument.

THE OWNER'S THREE RULINGS, 2026-08-28, and where each one lands here:

  1. A LETTER-LIST NAME IS ENOUGH TO MINT A RESIDENT. So a person known only from the
     post-office lists takes an action like any other — `new_resident` — and carries
     `letter_list_only: true` beside it. The counts report the two strengths
     separately, because 1,594 of the 2,201 are letter-list-only and a total that
     hides that is a number nobody can act on.
  2. TRANSCRIPTION-MEDIATED READINGS GRADE `documented`. Nothing here re-grades
     anything; the flag lives on the claim and travels with it.
  3. A DOCUMENTED BUSINESS IS BUILT AT THE SCENE DATE UNLESS CONTRADICTED — and this
     tool reads the word BEFORE in that ruling, which the gazetteer does not.
     `built_at_scene_date` there is `not contradicted_by`, whatever the contradiction
     is dated: a firm dissolved in August 1835 is struck out of a July town it was
     demonstrably standing in. The exclusion test here is a contradiction dated ON OR
     BEFORE the scene date. A LATER one is recorded, not obeyed —
     `dissolved_after_scene_date` — and the business stands.

TWO EXCLUSIONS, AND THE SECOND ONE NOW READS THE PAPER RATHER THAN A PROXY (T-0356).
T-0262 asked to exclude "entries whose only 1835 evidence `announces_opening` after
Jul 1", and there was no such field to read, so this tool used the derivable proxy
instead: a business whose FIRST issue postdated the scene date was excluded as
`first_evidence_after_scene_date`. Conservative in the direction provenance wants,
and NOT the same question — and the re-read of the thirty-eight it caught is what
settles that. Wm. H. Taylor's boot store advertised over a dateline of 8 JULY 1834,
Wm. H. Kennicott said he had practised dentistry in the town "for the past year",
Samuel Lewis's music-school copy is dated 22 June, S. Abell's 24 June and John
Holbrook's 10 June. Five houses excluded from a town they were printed standing in,
because the first SURVIVING issue that carried them falls in August.

So `announces_opening` is a field now (tools/compile_gazetteer.py § OPENING_DATINGS)
and the exclusion reads it. The DATING is what decides:

  stated    the paper names a date the house WILL open. After the scene date, that is
            the paper saying it was not open then — `opening_announced_after_scene_date`.
            Four houses: Cromelien's wine branch (14 Aug), Everts' high school for young
            gentlemen (10 Aug), Hunt's for young ladies (17 Aug) and Lyon's wholesale
            grocery (1 Sep).
  effected  an opening already made, dated by the advertisement's own dateline. It bounds
            the opening from ABOVE and can never exclude — "has opened", printed on 7
            August, is silent about 1 July. On or before the scene date it is the
            opposite: positive evidence the house stood.
  undated   an opening the printing dates nowhere. It decides nothing either way.

WHAT REPLACED THE PROXY IS NOT NOTHING. A business first printed in August and never
announcing an opening now stands in the July town under ruling 3 — documented, not
contradicted — and that is a LIBERTY, the forward twin of `survival_liberty_required`.
`backdating_liberty_required` names it: existence documented only after the scene date,
presence on the scene date assumed, and no opening notice dated on or before it to
carry the assumption. It is computed here and never asserted, exactly as its twin is.

WHAT AN ACTION MEANS, for the seeding tickets that consume this:

  enrich_existing  a committed structure already carries this business, matched on the
                   proprietors' surnames. The town needs a fuller record, not a roof.
  new_building     nothing committed carries it AND the paper's own placement resolves
                   against the committed town — a corner of two platted streets, or a
                   landmark that is a committed structure, or one hop through another
                   documented business that is. Placeable; T-0263's queue.
  street_only      documented and placeable no further than a street face. The paper
                   named a street this town has, and nothing narrower.
  unplaceable      no street the model holds, OR the firm's own record puts it out of
                   town (T-0355, `outside_plat`). Recorded, not buildable.

AND WHAT A PERSON ACTION MEANS:

  enrich           `data/residents/` already holds this person — matched EITHER by the
                   card the minting passes wrote from this very printed name (the card's
                   id is that name normalized, so the link outlives any later correction
                   of the display string; T-0866) OR, failing that, under the gazetteer's
                   OWN identity policy (surname plus forename initials, imported from
                   compile_gazetteer so the two tools cannot drift).
  replace_invented a documented person whose occupation is one the town INVENTED a
                   household for. The candidate to retire that invention (T-0264).
  new_resident     everybody else. Ruling 1: a letter-list name is enough.

THE RETIREMENT COUNT IS A COUNT OF INVENTED HOUSEHOLDS, NOT OF PEOPLE, and it is
capped per trade by construction: three documented tailors retire at most the number
of invented tailors the town holds. Reporting the matched persons instead would
report 2,201 people retiring 133 households, which is not a number about anything.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compile_gazetteer import (  # noqa: E402  — the identity policy has one home
    REPO, ROOT, RESEARCH, GAZETTEER,
    SCENE_DATE, dumps, firm_surnames, initials, load_json, slug, surname, unmarked,
)
# THE MINTING KEYS, imported from the passes that own them rather than re-derived here
# (T-0866). A card minted from a printed name is keyed by that pass's `plain_fragment`
# of the name, so a third copy of the function living in this file would be a link that
# can drift out of agreement with the link it is meant to be.
#
# AND THERE ARE TWO OF THEM, WHICH IS THE POINT OF ASKING RATHER THAN ASSUMING. The two
# passes do not read a printed name the same way: the letter-list pass knows the lists'
# SURNAME-FIRST setting, so `Mills Joel C.` is a Mills to it and a Mr C. to the
# documented pass. Ask each mint for the key IT would have written, and match only
# against the cards it actually wrote. `mint_civic_residents.py` and
# `mint_placed_residents.py` both take the documented pass's copy, so they share its key.
from mint_documented_residents import plain_fragment as documented_fragment  # noqa: E402
from mint_letter_list_residents import plain_fragment as letter_list_fragment  # noqa: E402

MINT_KEY = {
    "letter_list": letter_list_fragment,
    "documented": documented_fragment,
    "civic": documented_fragment,
    "placed": documented_fragment,
}

import re  # noqa: E402

REGISTER = RESEARCH / "register_1835.json"
STRUCTURES = ROOT / "data" / "structures"
STREETS = ROOT / "data" / "streets" / "1835.json"
RESIDENTS = ROOT / "data" / "residents"

SCHEMA_VERSION = 1

BUSINESS_ACTIONS = ("enrich_existing", "new_building", "street_only", "unplaceable")
PERSON_ACTIONS = ("enrich", "replace_invented", "new_resident")
EXCLUSIONS = ("contradicted_before_scene_date", "opening_announced_after_scene_date")

# Words that carry no identity in a name or an anchor: articles, the honorifics the
# papers set before a name, and the four nouns that appear in half the storefronts in
# town. Dropping them is what lets "Messrs. Newberry & Dole's store" meet the committed
# record "Newberry & Dole Warehouse"; keeping them would make every anchor unique.
ANCHOR_STOP = {
    "the", "a", "an", "of", "and", "at", "in", "on", "s", "to", "his", "their", "its",
    "street", "streets", "st", "sts", "messrs", "mr", "mrs", "dr", "esq", "jr", "sen",
    "new", "chicago", "late", "one", "two", "three", "door", "doors", "opposite",
    "next", "near", "above", "below", "east", "west", "north", "south", "side",
}

# The trade a paper prints is prose; `data/residents/` speaks a closed occupation
# vocabulary. This is the whole of the translation between them and it is deliberately
# a table rather than a matcher: a fuzzy trade match would silently retire an invented
# household on a word that happened to collide. First hit in order wins, so the
# compound trades sit above the words they contain.
TRADE_TO_OCCUPATION = (
    # ORDER IS THE RULE HERE: the first needle that appears anywhere in the printed
    # trade wins, so a longer trade whose letters contain a shorter one has to be
    # listed above it. "mill" sits inside "milliner", which is how every milliner in
    # this corpus was being compiled as a MILLER (T-0376) — Elmira Fowler, who
    # advertised "Millinery & Dress Making" on Dearborn Street in November 1834, and
    # Mrs H. Sherman, who took a room two doors from the Mansion House a month later.
    # A dressmaker recorded as a grain miller is not a near miss; it is a trade the
    # paper never gives her, and this project may not mint a resident over one.
    ("millinery", "milliner"),
    ("milliner", "milliner"),
    ("dress making", "dressmaker"),
    ("dressmaking", "dressmaker"),
    ("dress maker", "dressmaker"),
    ("dressmaker", "dressmaker"),
    ("forwarding and commission", "forwarding_and_commission"),
    ("boarding house", "boarding_house_keeper"),
    ("soap", "soap_and_candle_maker"),
    ("candle", "soap_and_candle_maker"),
    ("ship carpenter", "ship_carpenter"),
    ("dry goods", "dry_goods_merchant"),
    ("hardware", "hardware_merchant"),
    ("harness", "harness_maker"),
    ("watchmaker", "watchmaker"),
    ("wheelwright", "wheelwright"),
    ("lumber", "lumber_merchant"),
    ("attorney", "attorney"),
    ("counsellor", "attorney"),
    ("auction", "auctioneer"),
    ("bakery", "baker"),
    ("bake", "baker"),
    ("baker", "baker"),
    ("barber", "barber_surgeon"),
    ("blacksmith", "blacksmith"),
    ("brick", "brickmaker"),
    ("builder", "builder"),
    ("butcher", "butcher"),
    ("cabinet", "joiner"),
    ("carpenter", "carpenter"),
    ("chair", "joiner"),
    ("clothier", "clothier"),
    ("clothing", "clothier"),
    ("cooper", "cooper"),
    ("dentist", "dentist"),
    ("drover", "drover"),
    ("druggist", "druggist"),
    ("drug", "druggist"),
    ("editor", "editor"),
    ("ferry", "ferryman"),
    ("gunsmith", "gunsmith"),
    ("grocer", "grocer"),
    ("grocery", "grocer"),
    ("groceries", "grocer"),
    ("hotel", "hotel_keeper"),
    ("joiner", "joiner"),
    ("mason", "mason"),
    ("miller", "miller"),
    ("mill", "miller"),
    ("painter", "painter"),
    ("physician", "physician"),
    ("plasterer", "plasterer"),
    ("post office", "postmaster"),
    ("printer", "printer"),
    ("printing", "printer"),
    ("saddler", "saddler"),
    ("saddle", "saddler"),
    ("sailmaker", "sailmaker"),
    ("sawyer", "sawyer"),
    ("school", "schoolteacher"),
    ("shoemaker", "shoemaker"),
    ("boot", "shoemaker"),
    ("shoe", "shoemaker"),
    ("surveyor", "surveyor"),
    ("tailor", "tailor"),
    ("tanner", "tanner"),
    ("tavern", "tavern_keeper"),
    ("public house", "tavern_keeper"),
    ("teamster", "teamster"),
    ("trader", "trader"),
    ("merchant", "merchant"),
    ("store", "merchant"),
)

# T-0418 — sixteen trades the papers print that this vocabulary had no word for, and
# three it already had a word for and no needle to reach it with. THEY ARE A SECOND
# TABLE, READ AFTER THE FIRST HAS FAILED, on purpose. First hit wins, so a needle
# added above would outrank a reading the register already makes, and this ticket is
# about the people it reads NOTHING for: a new word may fill a null and may never
# displace a trade the corpus already resolved. (It would otherwise: John Watkins,
# who kept the town's first school AND sold books, would stop being a schoolteacher,
# and E. K. Hubbard would stop retiring the merchant household the town invented for
# want of him.) Within the block the usual ordering rule holds — "house and land
# agent" above "land agent", the land office's two officers a phrase apart. The nine
# printed phrases this project REFUSES to translate are in TRADE_NOT_IN_VOCABULARY
# below, checked before both tables, which is what keeps the Postmaster General of
# the United States out of the "postmaster" needle.
TRADE_TO_OCCUPATION_T0418 = (
    ("register of the land office", "land_office_register"),
    ("register, united states land office", "land_office_register"),
    ("house and land agent", "land_agent"),
    ("house and lot agent", "land_agent"),
    ("houses and lots", "land_agent"),
    ("land agent", "land_agent"),
    ("insurance", "insurance_agent"),
    ("harbour agent", "harbour_agent"),
    ("harbor agent", "harbour_agent"),
    ("master mariner", "master_mariner"),
    ("justice of the peace", "justice_of_the_peace"),
    ("militia officer", "militia_officer"),
    ("army officer", "army_officer"),
    ("postmaster", "postmaster"),
    ("sheriff", "sheriff"),
    ("provision dealer", "provision_dealer"),
    ("coffee house", "coffee_house_keeper"),
    ("refectory", "refectory_keeper"),
    ("restorator", "refectory_keeper"),
    ("bookseller", "bookseller"),
    ("stationer", "stationer"),
    ("tinsmith", "tinsmith"),
    ("sheet iron", "tinsmith"),
    ("founder", "founder"),
    ("stove dealer", "stove_dealer"),
    ("stove and hollow ware", "stove_dealer"),
    ("hollow ware", "stove_dealer"),
)

# T-0661 — the OTHER printed trades this vocabulary could not say. T-0418 adjudicated
# the 36 phrases the newspaper register itself refused; sweeping the WHOLE gazetteer
# the same way leaves 128 more printed phrases that no table above reads, across both
# the persons and the businesses. This is the third table, and it is asked LAST for
# the same reason the second is asked second: a word added here may fill a null and
# may never displace a reading the corpus already resolves. Twenty-one new words joined
# `data/residents/index.json`'s vocabulary with it; the rest are needles onto words
# that were already there and that nothing ever reached — `soldier`, `farmer`,
# `minister`, `indian_agent`, `county_clerk`, `packer`, `speculator`.
# docs/RESEARCH/occupation_vocabulary_1835.md argues every one of them, and the 33
# phrases this project REFUSES are in TRADE_NOT_IN_VOCABULARY below, checked first.
#
# ORDER IS THE RULE HERE TOO. "painting" sits above "carriage" because Brown offers
# "carriage, sign, ornamental and figure painting, and gilding" and he is a painter,
# not a carriage maker. The vessel masters take two-word needles because a bare
# "master" would take the dancing master and the schoolmaster with them.
TRADE_TO_OCCUPATION_T0661 = (
    # --- the town's and the county's own offices. T-0418 settled that this vocabulary
    # carries an office held AT CHICAGO — sheriff, county clerk, postmaster, register
    # of the land office are all in it already — and the same reasoning admits the
    # rest of the town's bench and board. An office held at Washington, at Vandalia or
    # on a circuit is refused below, on T-0418's own ground.
    ("president of the board of trustees", "town_president"),
    ("president, board of trustees", "town_president"),
    ("president of the town trustees", "town_president"),
    ("clerk of the board of trustees", "town_clerk"),
    ("secretary, board of trustees", "town_clerk"),
    ("secretary to the town trustees", "town_clerk"),
    ("town clerk", "town_clerk"),
    ("assessor", "town_assessor"),
    ("fire warden", "fire_warden"),
    ("public administrator", "public_administrator"),
    ("clerk of the circuit court", "county_clerk"),
    ("clerk of the cook circuit court", "county_clerk"),
    ("clerk of the county commissioners' court", "county_clerk"),
    ("clerk of court", "county_clerk"),
    ("county clerk", "county_clerk"),
    ("justice", "justice_of_the_peace"),
    ("indian agent", "indian_agent"),
    ("receiver, united states land office", "land_office_receiver"),
    ("receiver of public moneys", "land_office_receiver"),
    # --- the garrison and the militia. `army_officer` and `militia_officer` were both
    # in the vocabulary and between them reached four commissions; these are the ranks
    # and staff appointments the papers actually print. The Cook county regiment is
    # THIS county's militia, mustered at this town, which is why its colonel and its
    # adjutant take the militia word rather than a refusal.
    ("commissary of subsistence", "army_officer"),
    ("post adjutant", "army_officer"),
    ("commanding the post", "army_officer"),
    ("u.s. army", "army_officer"),
    ("colonel of the cook county regiment", "militia_officer"),
    ("regimental adjutant", "militia_officer"),
    ("soldier", "soldier"),
    # --- the lake. `master_mariner` has been a word since T-0418 and no needle ever
    # reached it; ten schooner masters, three ship masters and one sloop master are
    # the largest single group in the sweep.
    ("schooner master", "master_mariner"),
    ("ship master", "master_mariner"),
    ("sloop master", "master_mariner"),
    # --- the pulpit. `minister` was in the vocabulary from the beginning with nothing
    # to reach it. A Baptist pastor is a minister of that denomination; the vocabulary
    # keeps `priest` for the Catholic cure and `chaplain` for the garrison's.
    ("baptist pastor", "minister"),
    ("clergyman", "minister"),
    ("minister", "minister"),
    # --- the law. Ten men are printed "solicitor in chancery" and read nothing.
    ("solicitor", "attorney"),
    ("conveyancer", "attorney"),
    ("law", "attorney"),
    # --- physic. `physician` and `druggist` both existed; neither reached a botanic
    # practitioner, a chemist or a notice that offers "medicine and surgery".
    ("botanic", "physician"),
    ("medicine and surgery", "physician"),
    ("patent medicine", "druggist"),
    ("chemist", "druggist"),
    # --- the trades the vocabulary had no word for at all.
    ("painting", "painter"),
    ("carriage", "carriage_maker"),
    ("sleigh", "carriage_maker"),
    ("hat manufactur", "hatter"),
    ("hatter", "hatter"),
    ("brew", "brewer"),
    ("confection", "confectioner"),
    ("livery", "livery_stable_keeper"),
    ("pedlar", "pedlar"),
    ("trunk maker", "trunk_maker"),
    ("silversmith", "silversmith"),
    ("jeweller", "jeweller"),
    ("jewelry", "jeweller"),
    ("liquor", "liquor_dealer"),
    ("engineer", "engineer"),
    ("superintendent of public works", "engineer"),
    ("mail contractor", "mail_contractor"),
    ("dancing master", "dancing_master"),
    ("music teacher", "music_teacher"),
    ("piano", "music_teacher"),
    # --- needles onto words the vocabulary already had.
    # An inn is a tavern, and `tavern_keeper` is this vocabulary's word for the man who
    # keeps one. The single holder in this corpus, Trowbridge, is named in one notice
    # for the "EAGLE COFFEE HOUSE (TROWBRIDGE'S)" — an inn under the town's other name
    # for it — so this needle is the one addition in T-0661 that moves a row of the
    # register's action ledger, from `new_resident` to `replace_invented` against the
    # four tavern-keeper households the town invented for want of a documented one.
    # That is an ADDITION, not a displacement: his occupation was null before it.
    ("innkeeper", "tavern_keeper"),
    ("newspaper publisher", "editor"),
    ("academy", "schoolteacher"),
    # "ship chandler" ABOVE "chandler": a ship chandler victuals and rigs vessels and
    # is not a maker of candles. Daniel Elston, the one "chandler" the gazetteer prints,
    # is a soap and candle maker by his own notice; Fergus 1839 prints four ship
    # chandlers, and reading them as candle makers would be exactly the class of silent
    # collision T-0376's milliner-as-miller taught this table to fear.
    ("ship chandler", "ship_chandler"),
    ("chandler", "soap_and_candle_maker"),
    ("pork curer", "packer"),
    ("tinner", "tinsmith"),
    ("stove manufacturer", "stove_dealer"),
    ("castings", "founder"),
    ("ironmonger", "hardware_merchant"),
    ("cloak", "dressmaker"),
    ("habit maker", "dressmaker"),
    ("surveying", "surveyor"),
    ("provisions", "provision_dealer"),
    ("forwarder", "forwarding_and_commission"),
    ("storage keeper", "forwarding_and_commission"),
    ("land speculator", "speculator"),
    ("houses and lands", "land_agent"),
    ("leasing town lots", "land_agent"),
    ("letting agent", "land_agent"),
    ("land dealer", "land_agent"),
    ("farmer", "farmer"),
    ("merchandise", "merchant"),
    ("crockery", "merchant"),
    ("leather", "merchant"),
    ("commission dealer", "merchant"),
    ("shopkeeper", "merchant"),
)

# T-0418, the other half of the same ruling: printed phrases this project declines to
# translate, and the reason for each. Matched on the WHOLE printed phrase rather than
# as a substring, because a refusal is a ruling about one phrase and a substring
# refusal would silently take the trades that contain it - a bare "agent" would
# retire the insurance agent, the harbour agent and the land agent in the table above.
# Checked BEFORE that table, which is what keeps the Postmaster General of the United
# States out of the "postmaster" needle.
# docs/RESEARCH/occupation_vocabulary_1835.md argues each one; a printed trade that is
# neither here nor in the table above is simply unread, and reads back as
# `occupation: null` exactly as it did before.
TRADE_NOT_IN_VOCABULARY = {
    # An office of another government seat. This is the vocabulary of the town's
    # RESIDENTS, and a word for one of these is an invitation to raise a Chicago
    # household for a man the same record places at Washington or at Vandalia.
    "postmaster general": "the Postmaster General of the United States, at Washington",
    "governor of illinois": "the Governor of Illinois, whose record places him at Vandalia",
    "judge of the fifth judicial circuit": "a circuit bench, not a Chicago livelihood",
    # A single act, not a living. Nobody was an appraiser for a living: three men were
    # named to appraise one estate in one notice in November 1833.
    "appraiser": "named to appraise one estate in one notice; not a trade",
    "administratrix": "a probate role in one estate; not a trade",
    "judge of election": "one day's duty at one poll; not a trade",
    # Named, but not named as anything.
    "agent": "an agent of nothing the notice states",
    "ventriloquist": ("a travelling exhibitor: one notice, one night's entertainment, "
                      "and no second issue that puts him in the town at all"),
    "mechanic": "the papers' word for any skilled hand; choosing which would be invention",
    # A property relation: what he held, not what he did - and a vessel belongs on the
    # boat's own record rather than in a man's trade.
    "steamboat owner": "the notice gives the vessel he owned, not the work he did",
}

# T-0661, the other half of the same ruling, and it follows T-0418's four grounds
# exactly. Matched on the WHOLE printed phrase, checked before all three tables.
T0661_NOT_IN_VOCABULARY = {
    # An office of another government seat. This vocabulary is the town's; a word for
    # one of these invites the mint to raise a Chicago household for a man the same
    # record places at Washington, at Vandalia or on a circuit.
    "secretary of war": "the Secretary of War, at Washington",
    "secretary of state of illinois": "a state office held at Vandalia",
    "circuit judge": "a circuit bench, not a Chicago livelihood",
    # A single act or a temporary duty, not a living.
    "clerk pro tem": "one meeting's duty at one board; the office itself is town_clerk",
    "clerk pro tem. of the board of trustees":
        "one meeting's duty at one board; the office itself is town_clerk",
    "railroad commissioner": ("a commission to organise the Chicago and Vincennes Rail "
                              "Road, which never ran; the four Chicago men who held it "
                              "are read by their own printed trades and the fifth, "
                              "William B. Archer, promoted it from Clark county"),
    "price reporter for the chicago democrat":
        "a duty the paper's price current names; P. F. Peck's living is printed elsewhere",
    "map publisher": "one map, published once, by a firm whose living is the Indian trade",
    "judge of election": "one day's duty at one poll; not a trade",
    # Named as an agent, and the notice does not say the agency is a living. T-0418
    # refused a bare "agent" on this ground; these are agencies performed BESIDE a
    # printed trade, at another man's office or another town's wharf.
    "newspaper agent": ("subscriptions received at his own auction room: an "
                        "accommodation beside the auctioneer's trade"),
    "newspaper subscription agent": ("subscriptions received at another man's office; "
                                     "an accommodation, not a living"),
    "steamboat agent": ("taking freight and passage for a boat is the forwarding trade, "
                        "and the two so printed are read by it already (John H. Kinzie) "
                        "or are a St. Joseph house (J. Griffiths & Co.)"),
    "manufacturers' agent": ("an agency for manufacturers the notice does not name, "
                             "held beside Holbrook's own printed trades"),
    "hat manufacturers and wholesale dealers, detroit":
        "a Detroit house advertising in Chicago; the notice gives Jefferson Avenue",
    # A property relation: what he held, not what he did.
    "land owner": "a holding, not a trade",
    "property owner": "a holding, not a trade",
    "landlord": "a holding, not a trade; Temple's living is printed as physician",
    # A vessel's service. T-0418 put vessel ownership on the boat's own record in
    # data/boats/ rather than in a man's trade, and a packet run is the same shape.
    "lake packet": "a vessel's run; it belongs on the boat's record, not in a trade",
    "packet service for freight and passengers between chicago and the mouth of the st. joseph":
        "a vessel's run; it belongs on the boat's record, not in a trade",
    # The notice states no trade at all.
    "[not stated in the notice]": "the notice states no trade",
    "unstated — the notice announces only its closing": "the notice states no trade",
    "unstated — the notice announces only its dissolution": "the notice states no trade",
    "corn, sold from a barn": ("one lot of corn from a barn on the Dupage, which the "
                               "gazetteer's own note places outside the plat"),
}
TRADE_NOT_IN_VOCABULARY.update(T0661_NOT_IN_VOCABULARY)


# --------------------------------------------------------------------------
# normalising an anchor, a name and a street


def words(text):
    """The identity-bearing words of a name or an anchor, lower-cased."""
    t = unmarked(text or "").lower().replace("&", " and ")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return [w for w in t.split() if w and w not in ANCHOR_STOP]


def street_key(name):
    """'South Water-street' → 'south_water'. The plat's key, or '' for a road it lacks."""
    t = re.sub(r"[^a-z0-9]+", " ", (name or "").lower())
    t = re.sub(r"\b(street|streets|st|sts)\b", " ", t)
    return "_".join(t.split())


def occupation_of(text, table=TRADE_TO_OCCUPATION + TRADE_TO_OCCUPATION_T0418
                                    + TRADE_TO_OCCUPATION_T0661):
    """The residents vocabulary's word for a printed trade, or None.

    `table` is how a caller reading a person with SEVERAL printed trades keeps the
    T-0418 additions from displacing an established reading: ask with the first table
    across all of them, and only then with the second (see the person loop in build).
    """
    t = (text or "").lower()
    if t.strip().strip(".,;") in TRADE_NOT_IN_VOCABULARY:
        return None
    for needle, occ in table:
        if needle in t:
            return occ
    return None


# --------------------------------------------------------------------------
# the committed town, read once


def read_town(structures_dir=STRUCTURES, streets_file=STREETS, residents_dir=RESIDENTS):
    """Index the committed dataset the register resolves against.

    Read in sorted filename order and reduced to sets, so the register does not depend
    on the order a filesystem hands back.
    """
    town = {"structures": [], "streets": {}, "street_paths": {}, "residents": [],
            "invented": {}, "has_creek": False}

    for path in sorted(Path(structures_dir).glob("*.json")):
        d = load_json(path)
        names = [d.get("name") or ""] + list(d.get("aka") or [])
        occ_prose = (d.get("occupants") or {}).get("value") or ""
        occ = scene_date_occupants(occ_prose)
        function = (d.get("function") or {}).get("value")
        town["structures"].append({
            "id": d["id"],
            "name": d.get("name"),
            "name_words": [set(words(n)) for n in names if words(n)],
            "aka_head_words": [set(words(head_of(n))) for n in names[1:] if words(head_of(n))],
            "occupant_words": set(words(occ)),
            # The same line with NOTHING struck out, so `match_occupant` can tell a
            # building this firm was never in from one it has LEFT (T-0403).
            "occupant_words_all": set(words(occ_prose)),
            "occupant_text": occ,
            "aka_texts": [head_of(n) for n in names[1:]],
            "identity_text": " ; ".join([d.get("name") or "", occ_prose]
                                        + [head_of(n) for n in names[1:]]),
            "function": function,
            "occupation": occupation_of((function or "").replace("_", " ")),
            "anonymous": d["id"].startswith(("recon_", "inf_")),
        })

    # Where two records share a name_1835 the register has to choose, and the choice must
    # not be the file's line order. T-0451 seated the North Division's six lines as the
    # committed South Division streets CONTINUED across the river, so `dearborn` and
    # `dearborn_north` both read "Dearborn Street" — and the plat letters no name in any
    # North Division corridor, so nothing on the sheet tells them apart either. A bare
    # street name in these newspapers is the South Division line: that is where the
    # advertising town stood, and it is the reach every ordinal in this register is
    # counted along. So the record reaching furthest SOUTH takes the name, and the North
    # Division line stays reachable by its id. Before this, seating those six lines
    # re-anchored 90 fields of the register onto the wrong side of the water.
    #
    # T-0877 FOUND THE RULE'S UNSTATED HALF. "Furthest south" was a proxy for "the street
    # the advertising town walked on", sound while the only rival was across the river and
    # wrong the moment a rival appeared BELOW the town. Wright's School Section is a mile
    # of ruled grid south of Madison, and seven of its north-south lines are lettered with
    # names the town also uses — Clinton, Canal, Market, Wells, Clark, State. Every one of
    # them reaches a mile further south than the street it shares a name with, so the bare
    # proxy would have handed the printed name to unopened prairie: a notice reading
    # "Clark st." would have resolved a mile from the town that printed it.
    #
    # So the proxy is replaced by the thing it stood for, and the data already says it.
    # A record the town USED carries no `opened` flag at all — the twenty-eight streets of
    # the 1830 plats, the fort's two ways — while every survey line seated since is
    # `opened: false`, `track_width_m: 0`, "platted, unopened, unworn". A printed street
    # name in a newspaper or a directory is a place somebody walked to, so an unopened line
    # never takes a name from a street that was open, whichever reaches further south.
    # Within each of those two groups the T-0451 rule is unchanged, which is what keeps
    # `dearborn` ahead of `dearborn_north` (neither carries the flag) and what keeps the
    # School Section's own line ahead of a hypothetical rival further north (both do).
    # Measured when it landed: the winner of every name key in the register was unchanged.
    for s in sorted(load_json(streets_file).get("streets", []),
                    key=lambda r: (r.get("opened") is False,
                                   min(p[1] for p in r["path_local_enu_m"]))):
        # A street with no name — the eight unnamed tiers Wright rules across the School
        # Section carry `name_1835: null` — has no key for a printed name to match, and
        # `street_key(None)` is the EMPTY string. Seated, it made "" a live key and every
        # notice this town could not place resolved onto it: 62 businesses moved from
        # `unplaceable` to `street_only` on a street no paper names (T-0797).
        key = street_key(s["name_1835"])
        if key:
            town["streets"].setdefault(key, s["id"])
        town["streets"][s["id"]] = s["id"]
        # The committed centreline, kept so `streets_cross` can ask the plat whether a
        # named corner exists rather than assume it (T-0771).
        town["street_paths"].setdefault(s["id"], s["path_local_enu_m"])

    # The creek marker in OUTSIDE_MARKERS is only sound while this stays False.
    town["has_creek"] = any(
        "creek" in n.lower()
        for st in town["structures"] for n in [st["name"] or ""] + st["aka_texts"])

    for path in sorted(Path(residents_dir, "households").glob("*.json")):
        d = load_json(path)
        for p in d.get("persons", []):
            occ = p.get("occupation")
            town["residents"].append({
                "household": d["id"],
                "person": p["id"],
                "name": p.get("name"),
                "grade": p.get("grade"),
                "occupation": occ.get("value") if isinstance(occ, dict) else occ,
                # Which pass wrote this card, or None where a hand authored it. It is
                # what says whether the person id is a printed name normalized or just
                # an id, and the register's rename-proof link turns on that (T-0866).
                "source_pass": d.get("source_pass"),
            })

    # The invented layer, per trade: how many households the town raised because no
    # documented person was available for that trade. This is the ceiling on what the
    # register can retire, and it is a count of HOUSEHOLDS — one invented cooper's
    # household is one thing to retire however many people it holds.
    for r in town["residents"]:
        if r["grade"] in ("reconstructed", "inferred") and r["occupation"]:
            town["invented"].setdefault(r["occupation"], set()).add(r["household"])
    town["invented"] = {k: sorted(v) for k, v in sorted(town["invented"].items())}
    return town


def match_landmarks(town, anchor_words):
    """EVERY committed structure an anchor NAMES, in id order. A list, never a pick.

    Whole-set equality, not containment: an anchor is only a landmark when it is the
    same set of identity-bearing words as a record's name or aka. Containment would put
    'the store' on the first store in the town.

    AND IT RETURNS ALL OF THEM, BECAUSE A NAME IS NOT ALWAYS ONE BUILDING. This used to
    end `return sorted(hits)[0] if hits else None`, which is an alphabetical tie-break
    wearing a resolution's clothes: where two committed records answer to one name, the
    register seated the business in whichever id sorted first and wrote "the landmark is
    the committed structure X" over a coin toss, with nothing in the file to say a
    second record had answered to the same name. `structures_sharing_a_name` in the
    register's `compiled_from` block counts the town's exposure (T-0386); the named case
    is John Wright's two buildings to let, `wright_building_to_let_a` and `_b`, which
    are one advertisement's two buildings under one proprietor's name, and the piers,
    the two branch bridges and the school houses are the same shape. `resolve_anchor`
    refuses the ambiguity rather than taking the first.
    """
    if not anchor_words:
        return []
    return sorted({s["id"] for s in town["structures"]
                   if any(anchor_words == pool for pool in s["name_words"])})


# A phrase that locates a building by ANOTHER building is not that building's name.
# `aka: ["the cabins near Wentworth's tavern"]` names cabins; the tavern in it is the
# landmark they are near. Cutting an aka at its first locative word is what stops a
# surname on the far side of that word from being read as an occupant, which is how
# Elijah Wentworth's tavern on Flag Creek matched a row of log cabins at Wolf Point.
LOCATIVE = re.compile(
    r"\b(near|next|adjoining|adjacent|opposite|behind|beside|between|above|below|"
    r"at|on|by|from|off|over|under|toward|towards|facing)\b", re.I)


def head_of(name):
    """A name with any locative tail cut away. 'Log cabins at Wolf Point' → 'Log cabins'."""
    return LOCATIVE.split(name or "", maxsplit=1)[0]


# A DATE QUALIFICATION ON AN OCCUPANT IS A STATEMENT THAT HE IS NOT THERE NOW (T-0355).
# `wolf_point_tavern_stable` records "the tavern's keeper of the day — Elijah Wentworth
# in 1831, William Walters on the scene date", and the sentence names its scene-date
# occupant in the same breath as the man who preceded him. Read whole, the line put
# E. Wentworth's tavern — which is on Flag Creek, eighteen miles out on the Ottawa road
# — inside a Wolf Point stable, three times over.
#
# The clause is the unit, because that is how these lines are written: a comma, a
# semicolon or a spaced dash separates one tenancy from the next. A clause that dates
# ITSELF to a year the scene date does not fall in describes a FORMER occupant and is
# no evidence of who is in the building on 1 July 1835. A clause carrying no year at
# all says nothing about date and is kept — the great majority of these lines.
#
# Only the WORDS are filtered. `occupant_text` reports the scene-date reading so the
# register's evidence quotes what actually matched, and `identity_text` keeps the whole
# prose, because a forename printed anywhere in the record can still contradict a
# paper's (initials_compatible is a veto, and a veto wants every word it can get).
OCCUPANT_CLAUSE = re.compile(r"\s*[;,]\s*|\s+[\u2014\u2013-]\s+")
YEAR_SPAN = re.compile(r"\b(1[78]\d\d)(?:\s*[-\u2013]\s*(\d{2,4}))?\b")


def year_spans(text):
    """Every year or year range a clause states, as inclusive (from, to) pairs.

    '1833-34' is 1833 to 1834 and '1834-1836' is 1834 to 1836; a two-digit tail takes
    its century from the year it hangs off, which is how the committed records write it.
    """
    out = []
    for start, tail in YEAR_SPAN.findall(text or ""):
        start = int(start)
        end = start
        if tail:
            end = int(tail)
            if end < 100:
                end += start - start % 100
        out.append((start, max(start, end)))
    return out


def scene_date_occupants(text, scene_year=SCENE_DATE.year):
    """An occupants line with the clauses it dates away from the scene date struck out.

    Returns the surviving clauses rejoined. A clause survives when it states no year, or
    when a year it states — or a range it states — covers the scene year.
    """
    kept = []
    for clause in OCCUPANT_CLAUSE.split(text or ""):
        clause = clause.strip()
        if not clause:
            continue
        spans = year_spans(clause)
        if spans and not any(a <= scene_year <= b for a, b in spans):
            continue
        kept.append(clause)
    return "; ".join(kept)


FORENAME_RUN = r"((?:[A-Z][A-Za-z]*\.?\s+){0,3})"


#: A generational tag standing AFTER the family name — 'John Bates Jr.'. It reads as a
#: capitalised word, so the scan below took it for the surname and left Bates inside the
#: forename run, and 'bates' was then printed by this record in no surname position at
#: all. The tag is not a name and is taken off before the scan (T-1042).
GENERATIONAL = re.compile(r",?\s+\b(?:Jr|Jun|Junr|Sr|Senr|Esq|Esqr|2d|3d)\b\.?", re.I)


def forenames_before(text, sn):
    """Every forename run this text prints before the surname `sn`, as word tuples.

    'John H. Kinzie, forwarding merchant' → [('john', 'h')]. An empty run — the surname
    printed bare, as 'Jones, grocer' — yields the empty tuple, which is compatible with
    anything: a record that does not print a forename cannot contradict one.

    NO RUN AT ALL is a different answer and the guard below acts on it: it means this
    record prints the word somewhere OTHER than in surname position, as 'Dr Elijah Dewey
    Harmon' prints Dewey for a middle name.
    """
    out = []
    for m in re.finditer(FORENAME_RUN + r"\b([A-Z][a-z]+)\b", GENERATIONAL.sub("", text or "")):
        if slug(m.group(2)) != sn:
            continue
        out.append(tuple(w.strip(".").lower() for w in m.group(1).split()))
    return out


def forenames_of(name):
    """The forename words of a printed name, in order. 'R. A. Kinzie' → ('r', 'a').

    The generational tag comes off first, comma and all. It is not a forename, and while
    it stayed on, 'J. Bates, jr.' read as a man whose forename was Jr — which disagreed
    with the John the record prints and refused a match this reading should make (T-1042).
    """
    name = GENERATIONAL.sub("", unmarked(name or "")).strip()
    fore = name.split(",", 1)[1] if "," in name else " ".join(name.split()[:-1])
    return tuple(w.lower() for w in re.findall(r"[^\W\d_]+", fore, re.UNICODE))


def forenames_agree(a, b):
    """Two forename runs for one surname, compared as far as both of them go.

    The initial has to match, which is the papers' abbreviating habit respected. TWO
    SPELLED-OUT FORENAMES HAVE TO MATCH WHOLE, which is the refinement a building needs
    and a letter list does not: 'John S. Kinzie' and the James Kinzie House share an
    initial and are two different Kinzies, and an initials-only rule put the one inside
    the other.
    """
    for x, y in zip(a, b):
        if not x or not y or x[0] != y[0]:
            return False
        if len(x) > 1 and len(y) > 1 and x != y:
            return False
    return True


def initials_compatible(text, require, proprietors):
    """The person half of the identity policy, applied to a BUILDING's own prose.

    A firm matches a record on surnames (T-0304), which is right for firms and wrong for
    the men a building is named after: J. H. Kinzie's store and R. A. Kinzie were one
    surname and two brothers, and matching on 'kinzie' alone put the younger brother's
    business inside the elder's store. So where the record prints a forename for the
    surname and the paper prints one too, they must agree on the initials they share —
    the same prefix rule the resident match uses, because the papers abbreviate.

    IT IS ASKED OF THE WHOLE RECORD, not of the field the surname was found in. A record
    named 'Dole's Warehouse' whose occupants line reads 'George W. Dole' prints a
    forename; letting the bare name match on its own would just route every disagreement
    round the guard by dropping to the next tier.
    """
    for who in proprietors:
        for sn in firm_surnames(who) & require:
            mine = forenames_of(who)
            if not mine:
                continue
            # THE WORD IS IN THE RECORD; IS IT THERE AS A FAMILY NAME? (T-1042). The
            # pools this guard backs are word sets, so any capitalised word in the
            # record's prose can satisfy a required surname — and 'S. Dewey', a joiner,
            # matched Dr Elijah DEWEY Harmon's log cabin on a middle name. Where the
            # paper prints a forename for the surname, the record must print that surname
            # as a surname; printing the word in some other position is not the same man.
            if not forenames_before(text, sn):
                return False
            runs = [r for r in forenames_before(text, sn) if r]
            if not runs:
                continue
            if not any(forenames_agree(r, mine) for r in runs):
                return False
    return True


def match_occupant(town, require, business_occupation, proprietors):
    """The committed structure that ALREADY CARRIES this firm, with its evidence tier.

    Returns (structure_id, tier) or (None, None). Three tiers, tried in order, and the
    third is the only one that has to argue:

      occupants  the record's own statement of who is in the building. Trusted alone:
                 a building can hold a printing office and a dry-goods store at once,
                 and demanding that the trades agree would throw away exactly the
                 record that says both are there.
      name       the record is NAMED for the firm.
      aka        an alternate name carries the firm — accepted only when the trades
                 also agree, because an aka is where a record keeps its loosest
                 descriptions. 'Taylor's tavern' is a real aka of the Wolf Point
                 Tavern and W. H. Taylor's boot and shoe store is a different Taylor.

    ANONYMOUS RECONSTRUCTED AND INFERRED ROOFS ARE NOT CANDIDATES. `recon_*` and `inf_*`
    are invented buildings; one of them cannot ALREADY carry a documented business, and
    quietly matching a firm into one would launder an invention into the documented
    layer. Putting a documented business into an anonymous roof is a decision T-0263
    makes deliberately, with the adoption written down.

    AND A NAME OUTLIVES A TENANCY, SO AN UNDATED ONE MAY NOT PUT BACK A TENANT THE DATED
    LINE HAS JUST TAKEN OUT (T-0403). `occupants` is the only statement a committed
    record makes about who is inside that this register READS FOR A DATE —
    `scene_date_occupants` strikes the clauses whose years do not cover the scene. The
    `name` and `aka` tiers below are undated by nature: a building is called what it was
    called, and it goes on being called that after the tenant it was named for has gone.
    So a record that says "John Calhoun's Chicago Democrat printing office 1833-1834"
    and is also `aka` "John Calhoun's printing office" had the firm struck out of its
    occupants line by the date and handed straight back by its own alternate name, one
    tier down — which is the dated statement silently overruled by the undated one, and
    it is worse than never having asked, because the register then prints `match_tier:
    aka` as if a judgement had been made.

    The Chicago Democrat's office is the case. The paper's own colophon moves it off the
    corner of South Water and Clark between 1834-01-07 and 1835-05-20 (identity.json
    `anchor_changes`), so on the scene date the printing office is not in the building at
    that corner — but the building is still named for it, and still `aka` "John Calhoun's
    printing office", because that is what it was. The rule is general and not about this
    house: where a structure's UNDATED occupants line carries the firm and its scene-dated
    one does not, that structure is out of the `name` and `aka` tiers as well. The record
    has spoken about this firm, with a date, and the answer was no.
    """
    if not require:
        return None, None, None
    # The records whose own occupants line dates this firm away from the scene. Asked
    # with the same initials guard the tiers use, so a namesake the record never claimed
    # cannot silence a match: `identity_text` is built from the UNDATED prose, which is
    # what this question is about.
    departed = {s["id"] for s in town["structures"]
                if not s["anonymous"]
                and require <= s["occupant_words_all"]
                and not require <= s["occupant_words"]
                and initials_compatible(s["identity_text"], require, proprietors)}
    for tier in ("occupants", "name", "aka"):
        hits = []
        for s in town["structures"]:
            if s["anonymous"]:
                continue
            if tier != "occupants" and s["id"] in departed:
                continue
            if tier == "occupants":
                pools, text = [s["occupant_words"]], s["occupant_text"]
            elif tier == "name":
                pools, text = s["name_words"][:1], s["name"] or ""
            else:
                pools, text = s["aka_head_words"], " ; ".join(s["aka_texts"])
                if not (business_occupation and s["occupation"] == business_occupation):
                    continue
            if not any(pool and require <= pool for pool in pools):
                continue
            if not initials_compatible(s["identity_text"], require, proprietors):
                continue
            hits.append((s["occupation"] != business_occupation, s["id"], text))
        if hits:
            # The trades agreeing is the tie-break, then the id — so a firm that matches
            # both a tavern and that tavern's stable lands on the tavern, and the choice
            # does not depend on the order the files were read in.
            _, sid, text = sorted(hits)[0]
            return sid, tier, text
    return None, None, None


# OUTSIDE THE PLAT IS A THING THE PAPERS SAY, AND SAYING IT ENDS THE MATTER (T-0355).
# A tavern eighteen miles out on the Ottawa road cannot be in a Wolf Point stable
# whoever kept it, and no reading of a committed record's prose should be able to put
# it there. This is the general form of that fault: the firm's OWN record states where
# it stands, and when what it states is outside the committed town, no match against
# the committed town is admissible — not on an occupants line, not on a name, not on
# an aka, and the town does not build it either.
#
# THREE MARKERS, AND EACH IS A POSITIVE STATEMENT, never an absence. A business the
# papers place nowhere is `unplaceable` already and is not this; a business this rule
# excludes is one whose own printed placement puts it out of town.
#
#   miles   a distance in miles. The plat is under a mile across, so nothing inside it
#           is ever described in miles.
#   road    a ROAD LEADING TO somewhere. The town's own ways are streets and are named
#           as streets; 'the road from Chicago leading to Ottawa' is a road out of it.
#   creek   a named creek. The committed town holds the river and its two branches and
#           no creek of any name — checked in read_town, not asserted here — so a named
#           creek is ground this reconstruction does not cover.
#
# Counted over the 242 gazetteer businesses on 2026-08-29: five hits, and all five are
# genuinely out of town (the four Flag Creek readings of Wentworth's tavern, and Richard
# M. Sweet's barn on the Dupage, which the gazetteer's own note already calls outside).
OUTSIDE_MARKERS = (
    ("a distance in miles", re.compile(r"\b(?:[A-Za-z0-9-]+\s+)?miles?\b", re.I)),
    ("a road leading out of town", re.compile(r"\broad\b[^.;]{0,40}?\bto\b", re.I)),
    ("a named creek", re.compile(r"\b[A-Z][a-z]+\s+Creek\b")),
)


def structures_sharing_a_name(town):
    """How many identity-word sets the committed town holds under MORE THAN ONE record.

    The exposure `match_landmarks` refuses: every one of these is a name an anchor could
    print and no record could claim alone. Derived on every build so the figure cannot
    go stale in prose, and reported by `--check` (T-0386).
    """
    seen = {}
    for s in town["structures"]:
        for pool in s["name_words"]:
            if pool:
                seen.setdefault(frozenset(pool), set()).add(s["id"])
    return sum(1 for ids in seen.values() if len(ids) > 1)


def outside_the_plat(business, town):
    """Why the firm's own record puts it outside the committed town, or None.

    Reads everything the gazetteer prints about WHERE the business is — its name, which
    is the paper's own wording, and every field of its placement. A marker that names a
    creek is only believed while the committed town holds no creek; if one is ever
    committed the marker retires itself rather than mis-excluding a business on it.
    """
    placement = business.get("placement") or {}
    text = " | ".join(str(placement.get(k) or "")
                      for k in ("anchor", "offset_normalized", "offset_text", "note"))
    text = (business.get("name") or "") + " | " + text
    for why, pattern in OUTSIDE_MARKERS:
        if why == "a named creek" and town["has_creek"]:
            continue
        m = pattern.search(text)
        if m:
            return "%s — %r" % (why, m.group(0).strip())
    return None


CORNER = re.compile(r"corner of\s+(.{0,40}?)\s+and\s+(.{0,40})", re.I)

# "one door from Dearborn street", "two doors north of Lake street" — a COUNT OF DOORS
# off a named cross street. The owner ruled on 2026-08-30 (T-0384) that this is an
# ordinal off the corner and not a street and nothing narrower; `docs/CORNER-ORDINAL.md`
# is the policy and this regex is the only place the phrase is recognised, so a reading
# pass writes `class: relative`, an `anchor` naming the cross street and an
# `offset_normalized` carrying the count, and gets the ordinal reading without deciding
# anything. THE COUNT IS THE SOURCE'S AND THE METRES ARE NOT (L215).
ORDINAL_COUNT = {"one": 1, "first": 1, "two": 2, "second": 2, "three": 3, "third": 3,
                 "four": 4, "fourth": 4, "five": 5, "fifth": 5, "six": 6, "sixth": 6}
# 'a few doors below' is deliberately NOT here and must not be added: 'few' is not a
# count, and a placement that cannot say how many doors is a reach of the street.
ORDINAL_DOOR = re.compile(
    r"\b(%s)\s+doors?\b\s*(north|south|east|west)?\s+(?:from|of|above|below)\s+(.{0,40})"
    % "|".join(sorted(ORDINAL_COUNT)), re.I)


def streets_in(town, text, require_suffix):
    """Every platted street a phrase names, as street ids.

    The plat's own names are the dictionary, matched whole-word with a hyphen or a space
    between the parts, because the papers set 'South Water-street' and 'South Water
    street' interchangeably.

    `require_suffix` asks that the name be FOLLOWED by 'st'/'street', and it is the
    difference between reading a phrase and reading a corner. In free prose it must be
    on: 'Lake' alone is a lake here as often as a street, and 'the road to Lake Michigan'
    is not a placement on Lake Street. Inside 'corner of X and Y' it must be off,
    because the papers write the suffix once for both — 'corner of Dearborn and
    Lake-sts.' names two streets and suffixes neither of them.
    """
    found = set()
    for key, sid in town["streets"].items():
        if "_" not in key and len(key) < 4:
            continue
        pattern = r"\b%s\b" % key.replace("_", "[ -]")
        if require_suffix:
            pattern += r"[ -]*(?:street|streets|st|sts)\b"
        if re.search(pattern, text or "", re.I):
            found.add(sid)
    return sorted(found)


def streets_cross(town, a, b):
    """Do two platted streets actually MEET? Asked of the committed centrelines (T-0771).

    An ordinal counts doors from a CORNER, and a corner is a crossing. Two streets being
    platted and different does not make one: **Randolph Street and South Water Street are
    both east-west lines of the Original Town and run parallel for their whole length.**
    Clark, Filer & Co. advertise "their ware house on South water St. five doors east of
    the corner of Randolph st.", and the first three tests pass it — two platted streets,
    not the same one — so without this test the register would count five doors east of a
    corner that has never existed and stand a documented warehouse on it.

    The answer is taken from `data/streets/1835.json`'s committed `path_local_enu_m`, the
    same geometry every other placement is measured against, by segment intersection.
    Nothing is inferred: if the plat's own lines meet, there is a corner, and if they do
    not, there is not one. A street the town holds no path for cannot be shown to cross
    anything and is refused, which is the cautious direction.
    """
    def segments(sid):
        path = town.get("street_paths", {}).get(sid) or []
        return list(zip(path, path[1:]))

    def side(o, a, b):
        return ((a[0] - o[0]) * (b[1] - o[1])) - ((a[1] - o[1]) * (b[0] - o[0]))

    def meets(p, q, r, t):
        d1, d2 = side(r, t, p), side(r, t, q)
        d3, d4 = side(p, q, r), side(p, q, t)
        if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
            return True
        # A T-junction is a corner: an endpoint lying ON the other line counts.
        for o, x, y in ((r, t, p), (r, t, q), (p, q, r), (p, q, t)):
            if abs(side(o, x, y)) < 1e-9 and \
                    min(o[0], x[0]) - 1e-9 <= y[0] <= max(o[0], x[0]) + 1e-9 and \
                    min(o[1], x[1]) - 1e-9 <= y[1] <= max(o[1], x[1]) + 1e-9:
                return True
        return False

    return any(meets(p, q, r, t)
               for p, q in segments(a) for r, t in segments(b))


def ordinal_off_a_corner(town, placement):
    """A count of doors off a named cross street, resolved — or None.

    **The owner's ruling of 2026-08-30 (T-0384), in code.** Asked whether "one door from
    Dearborn street" places a store or is a street and nothing narrower, he chose: *read
    it as an ordinal off the corner*. So the phrase is NARROWER than the street it stands
    on — it counts doors from a crossing, which is a position along a face — and this
    reading runs BEFORE the `street` fallback and AFTER the landmark ones, which is the
    whole of its precedence:

    - after `structure` and `business`, so "first door west of Jones, King & Co." stays a
      landmark hop. An ordinal off a BUILDING is placed by that building and was always
      read that way; nothing about those claims changes here.
    - before `street`, because a reach of a street is what this phrase was being read as
      and is exactly the reading the owner overturned.

    Three things must hold, and each refuses a real phrase rather than a hypothetical one:

    1. the offset counts DOORS, in a word this project will translate to a number.
       'a few doors below Messrs. Newberry & Dole' names no count and stays unresolved.
    2. its reference resolves to exactly ONE platted street, suffix required — the same
       test `street` uses, so a phrase that could not have been read as a street cannot
       be read as an ordinal off one either.
    3. the business's OWN street is platted and is a different street. "two doors north
       of Lake street" said by a house on Lake Street is not an ordinal off a corner;
       the crossing an ordinal counts from is the crossing of two streets.
    4. the two streets MEET on the committed plat. Different is not crossing, and the
       corpus prints the difference: Randolph and South Water are parallel east-west
       lines of the Original Town, so Clark, Filer & Co.'s "five doors east of the corner
       of Randolph st." counts from a corner that does not exist. Asked of the streets'
       own centrelines by `streets_cross`; see T-0771.

    What comes back names the crossing in `streets` (the pair, as `corner` does) and the
    reading itself in `ordinal`, so a gate can read the count without parsing prose.
    **The count is the source's; the metres between two doors are this project's** —
    `docs/CORNER-ORDINAL.md` and L215 own that arithmetic, and no part of it is here.
    """
    # The fields are searched in order and the FIRST that carries the phrase supplies it,
    # rather than concatenating them: `offset_normalized` is the reading after OCR
    # judgment and `offset_text` is the raw column, and joining the two quotes a phrase
    # that stands in neither.
    m = None
    for field in ("offset_normalized", "offset_text"):
        m = ORDINAL_DOOR.search(str(placement.get(field) or ""))
        if m:
            break
    if not m:
        return None
    reference = streets_in(town, m.group(3), True)
    if len(reference) != 1:
        return None
    # The placement's own `street` is a declared field and not free prose, so the suffix
    # is not required of it — 'South Water' and 'South Water Street' are one answer.
    along = streets_in(town, placement.get("street"), False)
    if len(along) != 1 or along[0] == reference[0]:
        return None
    # 4. THE TWO STREETS MUST ACTUALLY MEET (T-0771). Different is not crossing: Randolph
    # and South Water are parallel east-west lines and have no corner, so Clark, Filer &
    # Co.'s "five doors east of the corner of Randolph st." counts from nothing this plat
    # holds. Asked of the committed centrelines by `streets_cross` above.
    if not streets_cross(town, along[0], reference[0]):
        return None
    count = ORDINAL_COUNT[m.group(1).lower()]
    direction = (m.group(2) or "").lower() or None
    return {
        "kind": "corner_ordinal", "target": None,
        "streets": sorted({along[0], reference[0]}), "via": None,
        "ordinal": {"count": count, "direction": direction,
                    "along": along[0], "from_street": reference[0],
                    "phrase": " ".join(m.group(0).split())},
        "note": "An ordinal off a corner: %d door%s%s the %s crossing, counted along %s. "
                "The count of doors is the paper's; how far one door is from the corner "
                "is this project's reconstruction (docs/CORNER-ORDINAL.md, L215)."
                % (count, "" if count == 1 else "s",
                   " %s of" % direction if direction else " from",
                   reference[0], along[0]),
    }


def resolve_anchor(town, business, by_firm):
    """Where the paper's own placement lands in the committed town.

    Seven outcomes, and the note on each says which one and why, because the seeding
    tickets have to be able to argue with it:

      corner     both streets named are on the committed plat
      structure  the landmark is a committed structure
      business   the landmark is another DOCUMENTED business which is itself resolved —
                 one hop and no more. 'One door east of Brewster, Hogan & Co.' is only
                 as placed as Brewster, Hogan & Co. is, and a chain of guesses is not
                 a placement.
      corner_ordinal
                 the offset counts DOORS off a named cross street — 'on South-Water st.
                 one door from Dearborn street'. A position along a face, and the owner
                 ruled on 2026-08-30 that it places a store; see `ordinal_off_a_corner`
                 above for the three tests and `docs/CORNER-ORDINAL.md` for the ruling.
      street     the anchor is a REACH of a platted street and nothing narrower — 'the
                 east end of South Water-street'. It is a real resolution and it is not
                 a placement, so it reads as its own kind rather than as a failure.
      ambiguous  the anchor NAMES something the town holds, and the town holds it more
                 than once. 'J. Wright's' is `wright_building_to_let_a` and `_b`. This
                 is a finding and not a failure: the name was recognised and the choice
                 between the records is not the paper's to make, so it is refused and
                 both are named. It never places (T-0386).
      unresolved everything else, stated

    Only the first three and `corner_ordinal` put a building on the ground; `street` and
    `unresolved` do not, which is what the action rules below turn on.
    """
    placement = business.get("placement") or {}
    text = " ".join(str(x) for x in (placement.get("anchor"),
                                     placement.get("offset_normalized"),
                                     placement.get("offset_text")) if x)
    if not text.strip():
        return {"kind": "unresolved", "target": None, "streets": None, "via": None,
                "note": "The paper gives no anchor."}

    m = CORNER.search(text)
    if m:
        a, b = streets_in(town, m.group(1), False), streets_in(town, m.group(2), False)
        pair = sorted(set(a) | set(b))
        if len(a) == 1 and len(b) == 1 and len(pair) == 2:
            return {"kind": "corner", "target": None, "streets": pair, "via": None,
                    "note": "A crossing of two platted streets: %s." % " and ".join(pair)}
        return {"kind": "unresolved", "target": None, "streets": None, "via": None,
                "note": "A corner of %r and %r, and the plat resolves %s."
                        % (m.group(1).strip(), m.group(2).strip(),
                           "both sides to %s" % pair if pair else "neither side")}

    anchor_words = set(words(placement.get("anchor")))
    if anchor_words:
        sids = match_landmarks(town, anchor_words)
        if len(sids) > 1:
            return {"kind": "ambiguous", "target": None, "streets": None, "via": None,
                    "note": "The landmark %r is the name of %d committed structures — "
                            "%s — and the anchor does not say which. Refused: the paper "
                            "names one building and this project holds more than one "
                            "under that name, so any pick between them would be this "
                            "file's and not the paper's."
                            % (placement.get("anchor"), len(sids), ", ".join(sids))}
        if sids:
            return {"kind": "structure", "target": sids[0], "streets": None, "via": None,
                    "note": "The landmark is the committed structure %s." % sids[0]}
        # One hop: the landmark is another documented business. Same refusal — the
        # corpus prints one house under more than one heading, so a firm name can
        # answer for two records here exactly as a building name can above.
        others = sorted({other_id for other_id, other in by_firm
                         if other_id != business["id"] and other
                         and set(words(other)) == anchor_words})
        if len(others) > 1:
            return {"kind": "ambiguous", "target": None, "streets": None, "via": None,
                    "note": "The landmark %r is the name of %d documented businesses — "
                            "%s — and the anchor does not say which. Refused: one hop "
                            "off a house this corpus holds twice is not a placement."
                            % (placement.get("anchor"), len(others), ", ".join(others))}
        if others:
            return {"kind": "business", "target": None, "streets": None,
                    "via": others[0],
                    "note": "The landmark is another documented business (%s), which "
                            "places this one exactly as well as that one is placed."
                            % others[0]}
    ordinal = ordinal_off_a_corner(town, placement)
    if ordinal:
        return ordinal
    named = streets_in(town, placement.get("anchor"), True)
    if named:
        return {"kind": "street", "target": None, "streets": named, "via": None,
                "note": "The anchor is a reach of %s and names nothing narrower."
                        % " and ".join(named)}
    return {"kind": "unresolved", "target": None, "streets": None, "via": None,
            "note": "The anchor %r names nothing the committed town holds."
                    % (placement.get("anchor") or text)}


# --------------------------------------------------------------------------
# the register


def anchor_change(town, business, by_firm):
    """The dated anchor change a house's own printings carry, resolved (T-0345).

    `anchor` above resolves the ONE placement the gazetteer holds live at the scene
    date. This is the rest of the history, and it exists because holding a superseded
    anchor as a second standing placement is how a placement sweep puts one shop in two
    places: Matthias Mason & Co.'s notice reads "nearly opposite Graves' Tavern" to
    1834-06-11 and "opposite the Tremont House" from 1834-09-10, and the register
    carried both as if they were live at once.

    Every superseded anchor is resolved against the committed town the same way the
    live one is, so a later pass can see what each reading WOULD have placed — which is
    the whole difference between a shop that moved and a landmark that was renamed, and
    this file decides neither.
    """
    change = business.get("anchor_change")
    if not change:
        return None
    return {
        "live_anchor": change["live_anchor"],
        "live_reason": change["live_reason"],
        "changes": change["changes"],
        "rule": change["rule"],
        "cannot_say": change["cannot_say"],
        "history": [dated_anchor(town, business, by_firm, w)
                    for w in change["history"]],
    }


# structure / corner / business put a building on the ground, `street` names a reach and
# nothing narrower, `unresolved` is a statement that the town holds no such thing. An
# anchor printed four ways is resolved on its BEST reading, because the four are declared
# to be one landmark and "Graves' Tavern" resolving where "Graves' Tavern, on Main-street"
# does not is a fact about how much of the sentence one reading pass swept into the field.
# `ambiguous` outranks `unresolved` because it RECOGNISED the name and outranks nothing
# else, because it places nothing: a reading that resolves to a street beats a reading
# that resolves to two buildings and cannot choose.
# `corner_ordinal` ranks WITH `corner` and `structure` rather than above them, although it
# is the narrower phrase, because this rank chooses between a house's several PRINTINGS
# and 'corner of Lake and Clark' is not a worse address than 'one door from Clark street'.
# Where a house prints both, the tie-break below keeps the earlier reading, which is the
# rule already governing a corner against a landmark.
ANCHOR_KIND_RANK = {"unresolved": 0, "ambiguous": 1, "street": 2, "business": 3,
                    "corner": 4, "structure": 4, "corner_ordinal": 4}


def dated_anchor(town, business, by_firm, window):
    """One anchor of a dated history, with every reading of it resolved."""
    readings = [dict(r, resolved=resolve_anchor(
        town, {"id": business["id"], "placement": r["placement"]}, by_firm))
        for r in window["readings"]]
    best = max(readings,
               key=lambda r: (ANCHOR_KIND_RANK.get(r["resolved"]["kind"], 0),
                              -readings.index(r)))
    return {
        "anchor": window["anchor"],
        "first_issue": window["first_issue"],
        "last_issue": window["last_issue"],
        "claims": window["claims"],
        "live_at_scene_date": window["live_at_scene_date"],
        "resolved": best["resolved"],
        "resolved_on_reading": best["anchor"],
        "readings": [{"anchor": r["anchor"], "first_issue": r["first_issue"],
                      "last_issue": r["last_issue"], "claims": r["claims"],
                      "resolved": r["resolved"]} for r in readings],
    }


def minted_link_problems(persons, minted_card):
    """THE INVARIANT, AS A GATE (T-0866 acceptance 3). Above is the fix; this is the
    thing that must still be true after somebody edits the fix.

    It is asked of the EMITTED rows and of the town's own cards, not of the matcher, so
    it fires whatever the matcher comes to do — which is why it lives out here where a
    self-test can hand it rows the matcher would never produce. A printed name that a
    mint turned into a card must reach that card, and no other. Both halves have been
    live faults: the register called 37 rows "a named person the town does not hold"
    while holding a card minted from that very name, and a display-string match handed
    17 more of them to a different person of the same surname.
    """
    out = []
    for entry in persons:
        card = minted_card(entry["name"])
        if not card:
            continue
        if entry["action"] != "enrich":
            out.append(
                "%s: %r, but the %s pass minted %s from this very printed name — the "
                "town holds this person and the register says it does not"
                % (entry["id"], entry["action"], card["source_pass"], card["person"]))
        elif entry["action_target"] != card["person"]:
            out.append(
                "%s: enriches %s, but the %s pass minted %s from this very printed "
                "name — the row belongs to the card it was minted from"
                % (entry["id"], entry["action_target"], card["source_pass"],
                   card["person"]))
    return out


def compile_register(gazetteer, town, quiet=True):
    """Derive the register. Returns (doc, problems). Nothing here reads the clock."""
    problems = []
    scene = SCENE_DATE.isoformat()
    by_firm = sorted((b["id"], b["name"]) for b in gazetteer["businesses"])

    businesses = []
    for b in sorted(gazetteer["businesses"], key=lambda x: x["id"]):
        first, last = b["evidence"]["first_issue"], b["evidence"]["last_issue"]

        # Ruling 3, with the word BEFORE honoured (see the module docstring).
        before = [c for c in b["contradicted_by"] if c["issue"] <= scene]
        after = [c for c in b["contradicted_by"] if c["issue"] > scene]
        exclusion, exclusion_note = None, None
        if before:
            exclusion = "contradicted_before_scene_date"
            exclusion_note = ("Contradicted on or before the scene date by %s."
                              % ", ".join("%s (%s, %s)" % (c["claim"], c["kind"], c["issue"])
                                          for c in before))
        # T-0356. Only a STATED future opening can exclude, and it excludes on its own
        # date. An `effected` or `undated` announcement is recorded and obeyed by nothing.
        announced = b.get("opening_announced") or []
        stated_after = sorted(o for o in announced
                              if o.get("dating") == "stated" and (o.get("iso") or "") > scene)
        if not before and stated_after:
            o = stated_after[0]
            exclusion = "opening_announced_after_scene_date"
            exclusion_note = ("%s announces this house opening on %s, after the scene date "
                              "— \u201c%s\u201d. %s"
                              % (o["claim"], o["iso"], o["verbatim"], o["note"]))

        # The forward twin of the survival liberty: documented only after the scene date,
        # and standing in the July town on the assumption that it was already there.
        opened_by_scene = any((o.get("iso") or "") <= scene for o in announced if o.get("iso"))
        backdating = (exclusion is None and first > scene and not opened_by_scene)

        entry = {
            "id": b["id"],
            "name": b["name"],
            "trade": b.get("trade"),
            "occupation": occupation_of(b.get("trade")),
            "proprietors": b.get("proprietors") or [],
            # T-0398. The gazetteer derives which of those strings are people and which
            # are the house's own trading style, and the register carries both rather
            # than making every reader re-derive it. A consumer that means PEOPLE reads
            # `partners`; `proprietors` is still the union of what the claims read and is
            # what a surname pass wants, because a style carries surnames too.
            "partners": b.get("partners") or [],
            "firm_styles": b.get("firm_styles") or [],
            "street": b.get("street"),
            "street_id": town["streets"].get(street_key(b.get("street"))),
            "placement_class": (b.get("placement") or {}).get("class"),
            "evidence": {"first_issue": first, "last_issue": last},
            "present_at_scene_date": exclusion is None,
            "exclusion": exclusion,
            "exclusion_note": exclusion_note,
            "dissolved_after_scene_date": [c["claim"] for c in after] if after else [],
            "opening_announced": announced,
            "survival_liberty_required": bool(b.get("survival_liberty_required")) and exclusion is None,
            "backdating_liberty_required": backdating,
            "anchor": resolve_anchor(town, b, by_firm),
            "anchor_change": anchor_change(town, b, by_firm),
            "outside_plat": outside_the_plat(b, town),
            "action": None,
            "action_target": None,
            "match_tier": None,
            "match_evidence": None,
            "action_note": None,
        }

        # enrich_existing: the committed town already carries this house, matched on
        # ALL the partners' surnames. The partners come out of the gazetteer's OWN firm
        # policy (T-0304), because a `proprietors` entry is routinely a whole style —
        # 'Clark, Filer & Co.', 'H. Doty & Co.', 'Kinzie & Hall' — and taking its last
        # word for a surname reads those three firms as 'co', 'co' and 'hall'. Two of
        # them then matched Daniel Elston's soap works, whose occupants line ends '& Co.'
        require = set()
        for p in entry["proprietors"]:
            require |= firm_surnames(p)
        require.discard("")
        committed, tier, evidence = (None, None, None)
        if not entry["outside_plat"]:
            committed, tier, evidence = match_occupant(
                town, require, entry["occupation"], entry["proprietors"])

        if exclusion is not None:
            entry["action"] = "unplaceable"
            entry["action_note"] = ("Excluded from the scene-date town: %s "
                                    "No action; the record is kept so the exclusion can "
                                    "be argued with." % exclusion_note)
        elif entry["outside_plat"]:
            entry["action"] = "unplaceable"
            entry["action_note"] = (
                "The paper puts this business outside the committed town — %s — so no "
                "structure inside it carries the firm and none is built for it. %s"
                % (entry["outside_plat"], entry["anchor"]["note"]))
        elif committed:
            entry["action"] = "enrich_existing"
            entry["action_target"] = committed
            entry["match_tier"] = tier
            entry["match_evidence"] = evidence
            entry["action_note"] = ("%s already stands and its %s carries %s — %r. The "
                                    "papers add trade, goods and dates to a record that "
                                    "exists." % (committed, tier, ", ".join(sorted(require)),
                                                 (evidence or "")[:160]))
        elif entry["anchor"]["kind"] in ("corner", "structure", "business",
                                         "corner_ordinal"):
            entry["action"] = "new_building"
            entry["action_target"] = (entry["anchor"]["target"]
                                      or entry["anchor"]["via"]
                                      or "+".join(entry["anchor"]["streets"] or []))
            entry["action_note"] = ("Placeable against the committed town. %s"
                                    % entry["anchor"]["note"])
        elif entry["street_id"]:
            entry["action"] = "street_only"
            entry["action_target"] = entry["street_id"]
            entry["action_note"] = ("The paper names %s and nothing narrower; %s"
                                    % (entry["street"], entry["anchor"]["note"][0].lower()
                                       + entry["anchor"]["note"][1:]))
        else:
            entry["action"] = "unplaceable"
            entry["action_note"] = ("No street the model holds. %s"
                                    % entry["anchor"]["note"])

        if entry["action"] not in BUSINESS_ACTIONS:
            problems.append("%s: action %r is not in the vocabulary" % (b["id"], entry["action"]))
        if entry["action"] in ("enrich_existing", "new_building") and not entry["action_target"]:
            problems.append("%s: a %s action must name its committed target or anchor"
                            % (b["id"], entry["action"]))
        if not entry["present_at_scene_date"] and not entry["exclusion_note"]:
            problems.append("%s: an exclusion must name its contradiction" % b["id"])
        if entry["placement_class"] is None:
            problems.append("%s: no placement class" % b["id"])
        # The three ways a dated anchor history could quietly go back to being two
        # standing placements, which is the defect T-0345 is about.
        ac = entry["anchor_change"]
        if ac:
            live = [w for w in ac["history"] if w["live_at_scene_date"]]
            if len(live) != 1:
                problems.append("%s: %d of this house's anchors are live at the scene "
                                "date — exactly one printed anchor stands on %s, which "
                                "is the whole point of dating the change"
                                % (b["id"], len(live), scene))
            elif live[0]["anchor"] != ac["live_anchor"]:
                problems.append("%s: the live anchor is named %r and the dated history "
                                "makes it %r" % (b["id"], ac["live_anchor"],
                                                 live[0]["anchor"]))
            elif entry["anchor"] not in [r["resolved"] for r in live[0]["readings"]]:
                problems.append("%s: the row resolves its anchor to something no reading "
                                "of the LIVE printing resolves to (%s) — the register "
                                "would be placing this house against a superseded "
                                "printing" % (b["id"], entry["anchor"]["note"]))
            for w in ac["history"]:
                # T-0773. `street` PLACES NOTHING — the docstring on `resolve_anchor`
                # says so and `ANCHOR_KIND_RANK` ranks it below everything that does —
                # so a reading that resolves to a street is not a second PLACE, it is a
                # reading the pass swept less of the sentence into. That is the same
                # thing `unresolved` is, and this gate already excused `unresolved`
                # while refusing the half-swept case beside it. G. Spring is where it
                # showed: eleven printings of one card, of which 1834-05-28 survives as
                # "[corne]r [F]ra[n]klin and South W[at]er-str[ee]t" — the word "of" lost
                # with the type, so `CORNER` does not match and the reach of South Water
                # Street is all that resolves. Refusing that grouping would have said the
                # corner and one of its own two streets are two places.
                #
                # It is excused only where the coarser reading is CONTAINED by the
                # placing one. A street the placing resolution does not name is still two
                # different things declared one landmark, and still fails.
                placed = {(r["resolved"]["kind"], r["resolved"]["target"],
                           r["resolved"]["via"], tuple(r["resolved"]["streets"] or []))
                          for r in w["readings"]
                          if r["resolved"]["kind"] not in ("unresolved", "street")}
                reaches = {tuple(r["resolved"]["streets"] or [])
                           for r in w["readings"] if r["resolved"]["kind"] == "street"}
                if len(placed) > 1:
                    problems.append(
                        "%s: the readings grouped under the anchor %r resolve to %d "
                        "different things in the committed town (%s) — they were "
                        "declared one landmark, and one landmark is one place"
                        % (b["id"], w["anchor"], len(placed),
                           ", ".join(sorted(str(x) for x in placed))))
                elif not placed and len(reaches - {()}) > 1:
                    problems.append(
                        "%s: the readings grouped under the anchor %r resolve to %d "
                        "different reaches of the plat (%s) and to nothing that places — "
                        "they were declared one landmark, and one landmark is one place"
                        % (b["id"], w["anchor"], len(reaches),
                           ", ".join(sorted(str(x) for x in reaches))))
                elif placed:
                    named = set(next(iter(placed))[3])
                    stray = [r for r in reaches if r and not set(r) <= named]
                    if stray:
                        problems.append(
                            "%s: the readings grouped under the anchor %r resolve to %s "
                            "and also to %s, which it does not name — a coarser reading "
                            "of one landmark is a reach of that landmark's own streets, "
                            "and anything else is a second place"
                            % (b["id"], w["anchor"], sorted(named) or "no street",
                               ", ".join(sorted(str(list(x)) for x in stray))))
        businesses.append(entry)

    # ONE GROUND, ONE ROOF (T-0411). The gazetteer can now say that one business is
    # another's PREMISES — the shop a paper is printed at, the store an agency is kept
    # at — which is neither a merge nor a refusal, and until this the register could not
    # hear it. It showed on the pair the relation was built for: `business_the_chicago_
    # democrat` and `business_chicago_democrat_printing_office` are one man's paper and
    # one man's shop at one corner, and the register took `enrich_existing` on the
    # committed `chicago_democrat_office` for the shop and `new_building` at
    # `clark+south_water` for the paper — a SECOND roof at the same corner for a
    # business that has no ground of its own. (The two fall on different sides of
    # `match_occupant` for a reason worth writing down: the shop's proprietors are
    # ['John Calhoun'] and the paper's are ['John Calhoun', 'Calhoun, J.'], so the
    # required surname set for the paper is {calhoun, j} and no occupant line carries a
    # partner named J.)
    #
    # So the WHOLE follows its PART, because the part IS the ground: it takes the part's
    # action and target verbatim rather than computing its own. This is deliberately
    # narrow. It fires only where the part is actually placed — `enrich_existing` or
    # `new_building` — and only where the whole was about to raise or name ground of its
    # own; a part the register cannot place says nothing about the whole, and a whole
    # already enriched onto a structure is left alone rather than moved.
    by_id = {e["id"]: e for e in businesses}
    for b in sorted(gazetteer["businesses"], key=lambda x: x["id"]):
        for edge in b.get("parts") or []:
            if edge.get("kind") != "premises":
                continue
            whole, part = by_id.get(b["id"]), by_id.get(edge.get("business_id"))
            if not whole or not part:
                continue
            if part["action"] not in ("enrich_existing", "new_building"):
                continue
            if whole["action"] not in ("new_building", "street_only"):
                continue
            was, was_target = whole["action"], whole["action_target"]
            whole["action"] = part["action"]
            whole["action_target"] = part["action_target"]
            whole["match_tier"] = part["match_tier"]
            whole["match_evidence"] = part["match_evidence"]
            whole["action_note"] = (
                "%s is declared the premises %s is carried on (identity.json "
                "premises_relations), so it stands where its premises stands and raises "
                "no ground of its own: %s at %s, taken from %s. Without the relation this "
                "record took %s at %s — a second roof for a business that has none. %s"
                % (part["name"], whole["name"], whole["action"], whole["action_target"],
                   part["id"], was, was_target, part["action_note"] or ""))

    # ---- persons -----------------------------------------------------------
    # The identity key is the gazetteer's own: surname plus forename initials, so
    # 'Cohen, P.' never becomes 'Cohen, J.' here either. A resident whose forename is
    # printed whole and a gazetteer name printed 'P. Cohen' share initials ('p',) and
    # match; two initials against one match only on the leading one, which is what the
    # papers' own abbreviating habit requires.
    resident_by_key = {}
    for r in town["residents"]:
        key = (surname(r["name"] or ""), initials(r["name"] or ""))
        if key[0]:
            resident_by_key.setdefault(key, []).append(r)

    # THE LINK THAT SURVIVES A RENAME (T-0866). The key above is the card's stored
    # DISPLAY string, and this project rewrites display strings whenever a reading is
    # corrected — T-0638 moved 36 of them, and T-0721 rewrote three letter-list cards
    # (`8. G. Abbot` became `[?] G. Abbot`). Every such rewrite silently unlinked the
    # card from the printed name it was MINTED FROM, and the register then said of two
    # people the town holds that it does not hold them: the exact untruth T-0692 is
    # about, in a derived file.
    #
    # So do not ask the display string. Ask the minting pass's own key: every mint in
    # this project (`letter_list`, `documented`, `civic`, `placed`) writes its person id
    # as `plain_fragment(printed name)`, so the ID IS THE PRINTED NAME NORMALIZED — and
    # an id does not move when a reading is corrected. That restores the contract
    # `mint_letter_list_residents.py` states of itself: "the moment this pass mints
    # somebody the compiler stops calling him `new_resident`".
    #
    # It is exactly as sound as the mint's own identity decision and no sounder: two
    # printed names collide here only when they carry the same surname and the same
    # given words, which is the case the passes already refuse to mint twice. A
    # HAND-AUTHORED card is excluded — its id was never derived from a printing, so an
    # id that happens to equal a fragment is a coincidence and not a link.
    minted_from_printed = {}
    for r in town["residents"]:
        if r.get("source_pass") in MINT_KEY:
            minted_from_printed.setdefault((r["source_pass"], r["person"]), r)

    def minted_card(name):
        """The card a mint wrote FROM this printed name, or None."""
        for pass_name, key in MINT_KEY.items():
            card = minted_from_printed.get((pass_name, key(name)))
            if card:
                return card
        return None

    def resident_match(name):
        minted = minted_card(name)
        if minted:
            return minted
        sn, ini = surname(name), initials(name)
        if not sn:
            return None
        for key, rs in sorted(resident_by_key.items()):
            if key[0] != sn:
                continue
            other = key[1]
            n = min(len(ini), len(other))
            if ini[:n] == other[:n] and (n > 0 or not ini and not other):
                return rs[0]
        return None

    # Two tables, asked in order, and the order is the whole of T-0418's promise that
    # its sixteen new words fill a null rather than displacing a reading: a man printed
    # as both a schoolteacher and a bookseller is read by the established table first,
    # across every trade the corpus gives him and the trade of his firm, and only a man
    # nothing there reaches is offered to the new words.
    trade_of_person = {}
    for table in (TRADE_TO_OCCUPATION, TRADE_TO_OCCUPATION_T0418,
                  TRADE_TO_OCCUPATION_T0661):
        d = {}
        for b in gazetteer["businesses"]:
            occ = occupation_of(b.get("trade"), table)
            if not occ:
                continue
            for p in b.get("proprietors") or []:
                d.setdefault(slug(p), occ)
        trade_of_person[id(table)] = d

    persons = []
    for p in sorted(gazetteer["persons"], key=lambda x: x["id"]):
        occ = None
        for table in (TRADE_TO_OCCUPATION, TRADE_TO_OCCUPATION_T0418,
                      TRADE_TO_OCCUPATION_T0661):
            for o in p.get("occupations") or []:
                occ = occupation_of(o, table)
                if occ:
                    break
            occ = occ or trade_of_person[id(table)].get(slug(p["name"]))
            if occ:
                break
        match = resident_match(p["name"])
        entry = {
            "id": p["id"],
            "name": p["name"],
            "occupation": occ,
            "letter_list_only": bool(p.get("letter_list_only")),
            "first_seen": p.get("first_seen"),
            "last_seen": p.get("last_seen"),
            "action": None,
            "action_target": None,
            "action_note": None,
        }
        if match:
            entry["action"] = "enrich"
            entry["action_target"] = match["person"]
            # How the link was made is part of what the row asserts: matched on the id
            # the mint wrote from this printed name, or on surname-plus-initials against
            # the card's display string (T-0866).
            if match is minted_card(p["name"]):
                how = ("the %s pass minted that card from this printed name, so the link "
                       "is the card's id and not its display string"
                       % match["source_pass"])
            else:
                how = ("matched under the gazetteer's identity policy, surname plus "
                       "forename initials")
            entry["action_note"] = ("data/residents/ already holds this person as %s "
                                    "(%s, %s) — %s. The papers add mentions and dates."
                                    % (match["person"], match["household"], match["grade"], how))
        elif occ and occ in town["invented"]:
            entry["action"] = "replace_invented"
            entry["action_target"] = occ
            entry["action_note"] = ("A documented %s. The town invented %d household(s) "
                                    "of this trade because no documented person was "
                                    "available; this is a candidate to retire one."
                                    % (occ, len(town["invented"][occ])))
        else:
            entry["action"] = "new_resident"
            entry["action_note"] = ("Ruling 1: a named person the town does not hold. "
                                    + ("Known only from the post-office letter lists."
                                       if entry["letter_list_only"] else
                                       "Named in a claim other than a letter list."))
        if entry["action"] not in PERSON_ACTIONS:
            problems.append("%s: action %r is not in the vocabulary" % (p["id"], entry["action"]))
        persons.append(entry)

    # THE INVARIANT, AS A GATE (T-0866 acceptance 3). Above is the fix; this is the
    # thing that will still be true after somebody edits the fix. It is asked of the
    # emitted rows, not of the matcher, so it fires whatever the matcher comes to do:
    # a printed name that a mint turned into a card must reach that card, and no other.
    # Both halves have been live faults — the register called 28 letter-list cards it
    # holds "a named person the town does not hold", and a display-string match can
    # equally hand a minted card's row to a different person of the same initials.
    problems.extend(minted_link_problems(persons, minted_card))

    # ---- counts ------------------------------------------------------------
    def tally(rows, field):
        out = {}
        for r in rows:
            out[r[field] or "none"] = out.get(r[field] or "none", 0) + 1
        return dict(sorted(out.items()))

    present = [b for b in businesses if b["present_at_scene_date"]]
    candidates = {}
    for p in persons:
        if p["action"] == "replace_invented":
            candidates.setdefault(p["action_target"], 0)
            candidates[p["action_target"]] += 1
    # Capped per trade: N documented tailors retire at most the invented tailors held.
    retirable = {t: min(n, len(town["invented"].get(t, [])))
                 for t, n in sorted(candidates.items())}

    counts = {
        "businesses": {
            "total": len(businesses),
            "present_at_scene_date": len(present),
            "excluded": tally([b for b in businesses if b["exclusion"]], "exclusion"),
            "by_action": tally(businesses, "action"),
            "by_placement_class": tally(businesses, "placement_class"),
            "present_by_action": tally(present, "action"),
            "outside_the_plat": sum(1 for b in businesses if b["outside_plat"]),
            "survival_liberty_required": sum(1 for b in present if b["survival_liberty_required"]),
            "backdating_liberty_required": sum(1 for b in present
                                               if b["backdating_liberty_required"]),
            "dissolved_after_scene_date": sum(1 for b in businesses if b["dissolved_after_scene_date"]),
        },
        "persons": {
            "total": len(persons),
            "by_action": tally(persons, "action"),
            "letter_list_only": sum(1 for p in persons if p["letter_list_only"]),
        },
        "invented_residents": {
            "households_by_trade": {k: len(v) for k, v in town["invented"].items()},
            "households_total": sum(len(v) for v in town["invented"].values()),
            "retirable_by_trade": {k: v for k, v in retirable.items() if v},
            "retirable_total": sum(retirable.values()),
        },
    }

    doc = {
        "schema": SCHEMA_VERSION,
        "generated_by": "tools/compile_register.py --build",
        "scene_date": scene,
        "_doc": ("DERIVED, NEVER AUTHORED. Rebuilt from gazetteer.json and the committed "
                 "town by tools/compile_register.py; tools/check.sh refuses a committed "
                 "copy a rebuild would not produce. Edit the gazetteer or the dataset, "
                 "not this file."),
        "compiled_from": {
            "gazetteer": {"claims": gazetteer["counts"]["claims"],
                          "persons": gazetteer["counts"]["persons"],
                          "businesses": gazetteer["counts"]["businesses"]},
            "structures": len(town["structures"]),
            "structures_sharing_a_name": structures_sharing_a_name(town),
            "streets": len({v for v in town["streets"].values()}),
            "resident_persons": len(town["residents"]),
        },
        "counts": counts,
        "businesses": businesses,
        "persons": persons,
    }
    if not quiet:
        print("  ok    %d business(es) → %s" % (len(businesses), counts["businesses"]["by_action"]))
        print("        %d person(s) → %s" % (len(persons), counts["persons"]["by_action"]))
    return doc, problems


# --------------------------------------------------------------------------
# build, check, self-test


def build():
    doc, problems = compile_register(load_json(GAZETTEER), read_town(), quiet=False)
    for p in problems:
        print("  FAIL  " + p, file=sys.stderr)
    if problems:
        return 1
    REGISTER.write_text(dumps(doc), encoding="utf-8")
    print("  wrote %s" % REGISTER.relative_to(REPO))
    return 0


def check():
    bad = []
    if not REGISTER.exists():
        return ["%s is missing — run tools/compile_register.py --build"
                % REGISTER.relative_to(REPO)]
    doc, problems = compile_register(load_json(GAZETTEER), read_town())
    bad.extend(problems)

    committed = REGISTER.read_text(encoding="utf-8")
    if committed != dumps(doc):
        bad.append("%s is not what a rebuild produces — run "
                   "tools/compile_register.py --build and commit the result"
                   % REGISTER.relative_to(REPO))

    # The acceptance clause of T-0262, kept as a gate rather than a claim in a PR:
    # every action names a target where its own kind requires one, and every exclusion
    # names its contradiction. Re-asserted against the COMMITTED file, because that is
    # what the seeding tickets read.
    on_disk = load_json(REGISTER)
    for b in on_disk.get("businesses", []):
        if b["action"] in ("enrich_existing", "new_building") and not b["action_target"]:
            bad.append("%s: %s names no target" % (b["id"], b["action"]))
        if b["exclusion"] and not b["exclusion_note"]:
            bad.append("%s: excluded and says nothing about why" % b["id"])
        if not b["exclusion"] and not b["present_at_scene_date"]:
            bad.append("%s: absent from the scene date with no exclusion" % b["id"])
    for p in on_disk.get("persons", []):
        if p["action"] not in PERSON_ACTIONS:
            bad.append("%s: action %r is not in the vocabulary" % (p["id"], p["action"]))
        if not p["action_note"]:
            bad.append("%s: an action with no note" % p["id"])

    # The two T-0257 fixtures, named in the ticket's acceptance: they resolve to an
    # action with a committed target, or the register says precisely why not. Pinned
    # here so a change that quietly drops them out of the town cannot pass.
    for fixture in ("business_peter_cohen", "business_j_s_c_hogan"):
        row = next((b for b in on_disk["businesses"] if b["id"] == fixture), None)
        if row is None:
            bad.append("%s: the T-0257 fixture is not in the register" % fixture)
            continue
        if not row["action_note"]:
            bad.append("%s: the T-0257 fixture takes an action it does not explain" % fixture)
    if not bad:
        print("  ok    register: %d business(es), %d person(s), %d invented household(s) retirable"
              % (len(on_disk["businesses"]), len(on_disk["persons"]),
                 on_disk["counts"]["invented_residents"]["retirable_total"]))
        ambiguous = [b["id"] for b in on_disk["businesses"]
                     if b["anchor"]["kind"] == "ambiguous"]
        print("  ok    %d committed name(s) are held by more than one structure; an "
              "anchor naming one is refused, not placed (%d today)"
              % (on_disk["compiled_from"]["structures_sharing_a_name"], len(ambiguous)))
    return bad


def self_test():
    """Every assertion above must be capable of firing."""
    town = {
        "structures": [
            {"id": "dole_warehouse_south", "name": "Dole's Warehouse",
             "name_words": [{"dole", "warehouse"}], "aka_head_words": [], "aka_texts": [],
             "occupant_words": {"dole", "forwarder"},
             "occupant_words_all": {"dole", "forwarder"},
             "occupant_text": "George W. Dole, forwarder", "function": "warehouse",
             "identity_text": "Dole's Warehouse ; George W. Dole, forwarder",
             "occupation": None, "anonymous": False},
            {"id": "wolf_point_tavern", "name": "Wolf Point Tavern",
             "name_words": [{"wolf", "point", "tavern"}, {"taylor", "tavern"}],
             "aka_head_words": [{"taylor", "tavern"}], "aka_texts": ["Taylor's tavern"],
             "occupant_words": {"william", "walters", "landlord"},
             "occupant_words_all": {"william", "walters", "landlord"},
             "occupant_text": "William Walters, landlord", "function": "tavern_inn",
             "identity_text": "Wolf Point Tavern ; William Walters, landlord ; Taylor's tavern",
             "occupation": "tavern_keeper", "anonymous": False},
            # T-0386's own case, and it is a real one: ONE advertisement of two
            # buildings to let under one proprietor's name. Nothing distinguishes them
            # but the (east)/(west) disambiguators this project added, so an anchor
            # reading 'John Wright's Building to Let' answers to both.
            {"id": "wright_building_to_let_a", "name": "John Wright's Building to Let",
             "name_words": [{"john", "wright", "building", "let"}],
             "aka_head_words": [], "aka_texts": [], "occupant_words": set(),
             "occupant_words_all": set(),
             "occupant_text": "", "function": "dwelling_to_let",
             "identity_text": "John Wright's Building to Let",
             "occupation": None, "anonymous": False},
            {"id": "wright_building_to_let_b", "name": "John Wright's Building to Let",
             "name_words": [{"john", "wright", "building", "let"}],
             "aka_head_words": [], "aka_texts": [], "occupant_words": set(),
             "occupant_words_all": set(),
             "occupant_text": "", "function": "dwelling_to_let",
             "identity_text": "John Wright's Building to Let",
             "occupation": None, "anonymous": False},
            # T-0406's own case, and the real record's shape: a record whose NAME
            # carries a disambiguator the printed corpus never uses — there was a second
            # Tremont House — and an AKA carrying the plain form the Democrat prints.
            {"id": "tremont_house_1", "name": "Tremont House (the first)",
             "name_words": [{"tremont", "house", "first"}, {"tremont", "house"}],
             "aka_head_words": [{"tremont", "house"}], "aka_texts": ["Tremont House"],
             "occupant_words": set(), "occupant_words_all": set(),
             "occupant_text": "", "function": "tavern_inn",
             "identity_text": "Tremont House (the first) ; Tremont House",
             "occupation": None, "anonymous": False},
            # T-0403's own shape: a building whose occupants line DATES its namesake
            # tenant away from the scene, and whose name and aka go on carrying him.
            {"id": "democrat_office_fixture", "name": "The Chicago Democrat Office",
             "name_words": [{"chicago", "democrat", "office"},
                            {"john", "calhoun", "printing", "office"}],
             "aka_head_words": [{"john", "calhoun", "printing", "office"}],
             "aka_texts": ["John Calhoun's printing office"],
             "occupant_words": set(),
             "occupant_words_all": {"john", "calhoun", "chicago", "democrat",
                                    "printing", "office"},
             "occupant_text": "", "function": "printing_office_and_store",
             "identity_text": "The Chicago Democrat Office ; John Calhoun's Chicago "
                              "Democrat printing office 1833-1834 ; John Calhoun's "
                              "printing office",
             "occupation": "printer", "anonymous": False},
            # T-1042's two records, and the whole of the difference between them: one
            # prints the required surname as a MIDDLE name and the other prints it as a
            # family name with a generational tag after it. A word-set pool cannot tell
            # them apart, so `initials_compatible` has to.
            {"id": "harmon_log_cabin", "name": "Harmon's Log Cabin",
             "name_words": [{"harmon", "log", "cabin"}],
             "aka_head_words": [], "aka_texts": [],
             "occupant_words": {"dr", "elijah", "dewey", "harmon"}, "occupant_words_all": {"dr", "elijah", "dewey", "harmon"},
             "occupant_text": "Dr Elijah Dewey Harmon", "function": "dwelling",
             "identity_text": "Harmon's Log Cabin ; Dr Elijah Dewey Harmon",
             "occupation": None, "anonymous": False},
            {"id": "bates_auction_room", "name": "Bates's Auction Room",
             "name_words": [{"bates", "auction", "room"}],
             "aka_head_words": [], "aka_texts": [],
             "occupant_words": {"john", "bates", "auctioneer"}, "occupant_words_all": {"john", "bates", "auctioneer"},
             "occupant_text": "John Bates Jr.; auctioneer", "function": "store",
             "identity_text": "Bates's Auction Room ; John Bates Jr.; auctioneer",
             "occupation": None, "anonymous": False},
            {"id": "recon_1835_north_i2_015", "name": "Reconstructed meeting hall #015",
             "name_words": [{"reconstructed", "meeting", "hall", "015"}],
             "aka_head_words": [], "aka_texts": [], "occupant_words": set(),
             "occupant_words_all": set(),
             "occupant_text": "", "function": "meeting hall",
             "identity_text": "Reconstructed meeting hall #015",
             "occupation": None, "anonymous": True},
        ],
        # `dearborn` is in the fixture so the ordinal cases below can quote the phrase the
        # corpus actually prints rather than a stand-in.
        "streets": {"south_water": "south_water", "clark": "clark", "lake": "lake",
                    "dearborn": "dearborn"},
        # The plat's own shape, in miniature: South Water and Lake are the east-west
        # lines and Clark and Dearborn cross them. The ordinal cases need real geometry
        # because the fourth test asks whether two streets MEET (T-0771), and the pair
        # that does NOT — two parallel east-west lines — is the case it exists to refuse.
        "street_paths": {"south_water": [[100.0, 0.0], [800.0, 0.0]],
                         "lake": [[-320.0, -112.0], [900.0, -112.0]],
                         "clark": [[600.0, -400.0], [600.0, 20.0]],
                         "dearborn": [[700.0, -400.0], [700.0, 20.0]]},
        "residents": [{"household": "hh_x", "person": "cohen_peter", "name": "Peter Cohen",
                       "grade": "attested", "occupation": "clothier"},
                      {"household": "hh_inf_baker", "person": "inf_baker_01",
                       "name": "Silas Stiles", "grade": "reconstructed", "occupation": "baker"},
                      # T-0866's own shape: a card the letter-list pass minted from the
                      # printed 'Gabbs, James I1.', whose DISPLAY string was later
                      # corrected to mark the initial nobody can read. The id is the
                      # printed name and did not move; the display string did.
                      {"household": "hh_gabbs_james_i1", "person": "gabbs_james_i1",
                       "name": "James [?] Gabbs", "grade": "inferred",
                       "occupation": None, "source_pass": "letter_list"},
                      # And the case the two mints read differently: the letter lists set
                      # the surname FIRST, so this card is a Mills to the pass that wrote
                      # it and a Mr C. to the documented pass's reading of the same words.
                      {"household": "hh_mills_joel_c", "person": "mills_joel_c",
                       "name": "Joel C. Mills", "grade": "inferred",
                       "occupation": None, "source_pass": "letter_list"}],
        "invented": {"baker": ["hh_inf_baker"]},
        "has_creek": False,
    }
    failures = []
    CASES = [0]

    def unit(label, got, want):
        CASES[0] += 1
        if got != want:
            failures.append("%s: got %r, wanted %r" % (label, got, want))

    def case(label, gaz, want):
        CASES[0] += 1
        doc, problems = compile_register(gaz, town)
        if problems:
            failures.append("%s: unexpected problems %r" % (label, problems))
            return None
        got = want(doc)
        if got is not True:
            failures.append("%s: %s" % (label, got))
        return doc

    def gaz(businesses=(), persons=()):
        return {"counts": {"claims": 0, "persons": len(persons), "businesses": len(businesses)},
                "businesses": list(businesses), "persons": list(persons)}

    def biz(bid, **kw):
        b = {"id": bid, "name": kw.get("name", bid), "trade": kw.get("trade"),
             "proprietors": kw.get("proprietors", []), "street": kw.get("street"),
             "goods": [], "placement": kw.get("placement", {"class": "none", "anchor": None}),
             "evidence": {"first_issue": kw.get("first", "1834-01-01"),
                          "last_issue": kw.get("last", "1835-06-01"), "copy_dates": []},
             "contradicted_by": kw.get("contradicted", []),
             "opening_announced": kw.get("announced", []),
             "mentions": [], "built_at_scene_date": True,
             "survival_liberty_required": kw.get("survival", False)}
        if kw.get("anchor_change"):
            b["anchor_change"] = kw["anchor_change"]
        return b

    def refuses(label, gaz, want):
        """A case that must be REFUSED, and on the sentence it is refused with."""
        CASES[0] += 1
        _, problems = compile_register(gaz, town)
        if not any(want in p for p in problems):
            failures.append("%s: expected a refusal mentioning %r, got %r"
                            % (label, want, problems))

    def person(pid, name, **kw):
        return {"id": pid, "name": name, "variants": [], "mentions": [],
                "first_seen": "1835-01-01", "last_seen": "1835-06-01",
                "letter_list_only": kw.get("letter_list_only", False),
                "occupations": kw.get("occupations", []), "associated_places": []}

    # 1. A contradiction BEFORE the scene date excludes; one AFTER does not.
    case("contradiction before the scene date excludes",
         gaz([biz("b1", contradicted=[{"claim": "c#1", "kind": "notice", "issue": "1834-06-11"}])]),
         lambda d: True if d["businesses"][0]["exclusion"] == "contradicted_before_scene_date"
         else "excluded as %r" % d["businesses"][0]["exclusion"])
    case("a dissolution AFTER the scene date leaves the firm standing",
         gaz([biz("b1", street="South Water Street",
                  contradicted=[{"claim": "c#1", "kind": "notice", "issue": "1835-08-08"}])]),
         lambda d: True if (d["businesses"][0]["present_at_scene_date"]
                            and d["businesses"][0]["dissolved_after_scene_date"] == ["c#1"])
         else "present=%r after=%r" % (d["businesses"][0]["present_at_scene_date"],
                                       d["businesses"][0]["dissolved_after_scene_date"]))

    # 2. T-0356. The exclusion reads the paper's own opening notice, and the DATING is
    #    what decides. Every case below was a live reading in the 1835 corpus.
    def opening(dating, iso, claim="c#1", verbatim="will open", note="a reading"):
        return {"claim": claim, "issue": "1835-08-05", "dating": dating, "iso": iso,
                "verbatim": verbatim, "note": note}

    case("a STATED opening after the scene date excludes, and quotes the paper",
         gaz([biz("b1", first="1835-08-05", last="1835-08-05",
                  announced=[opening("stated", "1835-08-14",
                                     verbatim="open a Branch of their House")])]),
         lambda d: True if (d["businesses"][0]["exclusion"] == "opening_announced_after_scene_date"
                            and "1835-08-14" in d["businesses"][0]["exclusion_note"]
                            and "open a Branch of their House" in d["businesses"][0]["exclusion_note"])
         else "excluded as %r, %r" % (d["businesses"][0]["exclusion"],
                                      d["businesses"][0]["exclusion_note"]))
    case("a STATED opening on or before the scene date does not exclude",
         gaz([biz("b1", street="Lake Street", first="1835-08-05", last="1835-08-05",
                  announced=[opening("stated", "1835-06-20")])]),
         lambda d: True if d["businesses"][0]["present_at_scene_date"]
         else "excluded as %r" % d["businesses"][0]["exclusion"])
    case("an EFFECTED opening after the scene date never excludes — it bounds from above",
         gaz([biz("b1", street="Lake Street", first="1835-08-19", last="1835-08-19",
                  announced=[opening("effected", "1835-08-18", verbatim="she has taken a room")])]),
         lambda d: True if (d["businesses"][0]["present_at_scene_date"]
                            and d["businesses"][0]["action"] == "street_only")
         else "excluded as %r" % d["businesses"][0]["exclusion"])
    case("an UNDATED opening decides nothing",
         gaz([biz("b1", street="Lake Street", first="1835-08-05", last="1835-08-05",
                  announced=[opening("undated", None, verbatim="has just opened")])]),
         lambda d: True if d["businesses"][0]["present_at_scene_date"]
         else "excluded as %r" % d["businesses"][0]["exclusion"])
    case("a contradiction before the scene date outranks a stated opening",
         gaz([biz("b1", first="1835-08-05", last="1835-08-05",
                  announced=[opening("stated", "1835-08-14")],
                  contradicted=[{"claim": "c#9", "kind": "notice", "issue": "1834-06-11"}])]),
         lambda d: True if d["businesses"][0]["exclusion"] == "contradicted_before_scene_date"
         else "excluded as %r" % d["businesses"][0]["exclusion"])

    # 2b. THE PROXY IS GONE, and this is the case that proves it: a house whose first
    #     surviving issue is August and whose copy is dated a year earlier stands in the
    #     July town, on no liberty at all. Wm. H. Taylor's boot store, 8 July 1834.
    case("first evidence after the scene date no longer excludes by itself",
         gaz([biz("b1", street="Lake Street", first="1835-08-08", last="1835-08-08")]),
         lambda d: True if (d["businesses"][0]["present_at_scene_date"]
                            and d["businesses"][0]["exclusion"] is None)
         else "excluded as %r" % d["businesses"][0]["exclusion"])
    case("standing on August evidence alone is a backdating liberty",
         gaz([biz("b1", street="Lake Street", first="1835-08-08", last="1835-08-08")]),
         lambda d: True if d["businesses"][0]["backdating_liberty_required"]
         else "backdating_liberty_required=%r" % d["businesses"][0]["backdating_liberty_required"])
    case("an opening dated before the scene date clears the backdating liberty",
         gaz([biz("b1", street="Lake Street", first="1835-08-05", last="1835-08-05",
                  announced=[opening("effected", "1834-07-08",
                                     verbatim="HAS opened an extensive Boot, Shoe and Leather Store")])]),
         lambda d: True if (d["businesses"][0]["present_at_scene_date"]
                            and not d["businesses"][0]["backdating_liberty_required"])
         else "backdating_liberty_required=%r" % d["businesses"][0]["backdating_liberty_required"])
    case("a house documented before the scene date owes no backdating liberty",
         gaz([biz("b1", street="Lake Street", first="1834-05-01", last="1835-06-01")]),
         lambda d: True if not d["businesses"][0]["backdating_liberty_required"]
         else "backdating_liberty_required=%r" % d["businesses"][0]["backdating_liberty_required"])

    # 3. The four actions, each on its own ground.
    case("a committed structure carrying the proprietor takes enrich_existing",
         gaz([biz("b1", proprietors=["George W. Dole"], street="South Water Street")]),
         lambda d: True if (d["businesses"][0]["action"] == "enrich_existing"
                            and d["businesses"][0]["action_target"] == "dole_warehouse_south")
         else "action=%r target=%r" % (d["businesses"][0]["action"],
                                       d["businesses"][0]["action_target"]))
    # T-1042, both halves. The reading of the proprietor string is what put these two
    # businesses in front of the guard at all — before it, 'Dewey, S.' carried an invented
    # surname 's' that missed the cabin by accident, and 'J. Bates, jr.' carried 'jr'
    # instead of 'bates' and missed the auction room for good.
    case("a record printing the surname as a MIDDLE name is not this man",
         gaz([biz("b1", proprietors=["Dewey, S."], trade="cabinet making")]),
         lambda d: True if (d["businesses"][0]["action"] == "unplaceable"
                            and d["businesses"][0]["action_target"] is None)
         else "action=%r target=%r" % (d["businesses"][0]["action"],
                                       d["businesses"][0]["action_target"]))
    case("a generational tag after the family name does not hide the family name",
         gaz([biz("b1", proprietors=["J. Bates, jr."], trade="auctioneer")]),
         lambda d: True if (d["businesses"][0]["action"] == "enrich_existing"
                            and d["businesses"][0]["action_target"] == "bates_auction_room")
         else "action=%r target=%r" % (d["businesses"][0]["action"],
                                       d["businesses"][0]["action_target"]))
    case("a corner of two platted streets takes new_building",
         gaz([biz("b1", street="South Water Street", placement={
             "class": "corner", "anchor": "the corner of South Water and Clark streets"})]),
         lambda d: True if (d["businesses"][0]["action"] == "new_building"
                            and d["businesses"][0]["anchor"]["streets"] == ["clark", "south_water"])
         else "action=%r anchor=%r" % (d["businesses"][0]["action"], d["businesses"][0]["anchor"]))
    # …and the fifth thing that can decide one: a declared premises relation (T-0411).
    def premises_edge(b, part_id, part_name, kind="premises"):
        b["parts"] = [{"kind": kind, "business": part_name, "business_id": part_id,
                       "witnesses": ["the fixture"],
                       "relation_rule": "the fixture's own declaration"}]
        return b

    case("a business standing on another's premises takes its premises' roof",
         gaz([premises_edge(biz("b1", street="South Water Street", placement={
                  "class": "corner",
                  "anchor": "the corner of South Water and Clark streets"}),
              "b2", "b2"),
              biz("b2", proprietors=["George W. Dole"], street="South Water Street")]),
         lambda d: True if (d["businesses"][0]["action"] == "enrich_existing"
                            and d["businesses"][0]["action_target"] == "dole_warehouse_south")
         else "action=%r target=%r" % (d["businesses"][0]["action"],
                                       d["businesses"][0]["action_target"]))
    case("a premises the register cannot place leaves the whole where it was",
         gaz([premises_edge(biz("b1", street="South Water Street", placement={
                  "class": "corner",
                  "anchor": "the corner of South Water and Clark streets"}),
              "b2", "b2"),
              biz("b2", street="Flag Creek", placement={"class": "none", "anchor": None})]),
         lambda d: True if d["businesses"][0]["action"] == "new_building"
         else "action=%r" % d["businesses"][0]["action"])
    case("a whole already enriched onto a structure is not moved by the relation",
         gaz([premises_edge(biz("b1", proprietors=["George W. Dole"],
                                street="South Water Street"), "b2", "b2"),
              biz("b2", street="South Water Street", placement={
                  "class": "corner",
                  "anchor": "the corner of South Water and Clark streets"})]),
         lambda d: True if (d["businesses"][0]["action"] == "enrich_existing"
                            and d["businesses"][0]["action_target"] == "dole_warehouse_south")
         else "action=%r target=%r" % (d["businesses"][0]["action"],
                                       d["businesses"][0]["action_target"]))

    case("a street with no anchor takes street_only",
         gaz([biz("b1", street="Lake Street", placement={"class": "street_only", "anchor": None})]),
         lambda d: True if (d["businesses"][0]["action"] == "street_only"
                            and d["businesses"][0]["action_target"] == "lake")
         else "action=%r target=%r" % (d["businesses"][0]["action"],
                                       d["businesses"][0]["action_target"]))
    case("no street the model holds takes unplaceable",
         gaz([biz("b1", street="Flag Creek", placement={"class": "none", "anchor": None})]),
         lambda d: True if d["businesses"][0]["action"] == "unplaceable"
         else "action=%r" % d["businesses"][0]["action"])

    # 4. The one-hop chain, and that it is only one hop.
    case("a landmark that is another documented business resolves one hop",
         gaz([biz("b1", name="Newberry & Dole", street="South Water Street"),
              biz("b2", street="South Water Street", placement={
                  "class": "relative", "anchor": "Messrs. Newberry & Dole"})]),
         lambda d: True if (d["businesses"][1]["anchor"]["kind"] == "business"
                            and d["businesses"][1]["anchor"]["via"] == "b1")
         else "anchor=%r" % d["businesses"][1]["anchor"])

    # 4a. T-0386. A NAME THE TOWN HOLDS TWICE IS REFUSED, NEVER TIE-BROKEN. The pick
    #     this replaces was `sorted(hits)[0]` — an alphabetical coin toss that the
    #     register then reported as "the landmark is the committed structure X".
    case("an anchor naming TWO committed structures is refused, not placed",
         gaz([biz("b1", street="South Water Street", placement={
             "class": "relative", "anchor": "John Wright's Building to Let"})]),
         lambda d: True if (d["businesses"][0]["anchor"]["kind"] == "ambiguous"
                            and d["businesses"][0]["anchor"]["target"] is None
                            and "wright_building_to_let_a" in d["businesses"][0]["anchor"]["note"]
                            and "wright_building_to_let_b" in d["businesses"][0]["anchor"]["note"]
                            and d["businesses"][0]["action"] == "street_only")
         else "anchor=%r action=%r" % (d["businesses"][0]["anchor"],
                                       d["businesses"][0]["action"]))
    # 4b. T-0406. AN AKA IS HOW A RECORD ANSWERS TO THE NAME THE PAPERS PRINT, and it
    #     resolves on the SAME whole-set rule as a name. The committed Tremont is named
    #     "Tremont House (the first)" and the Democrat prints "the Tremont House" — the
    #     anchor of six advertisements. Loosening the rule to containment would have
    #     resolved it and would also have put "the store" on the first store in the town.
    case("an anchor resolves on a record's AKA, not only on its name",
         gaz([biz("b1", street="Lake Street", placement={
             "class": "relative", "anchor": "the Tremont House"})]),
         lambda d: True if (d["businesses"][0]["anchor"]["kind"] == "structure"
                            and d["businesses"][0]["anchor"]["target"] == "tremont_house_1")
         else "anchor=%r" % d["businesses"][0]["anchor"])
    case("…and the aka still only matches WHOLE: a SUBSET names nothing",
         gaz([biz("b1", street="Lake Street", placement={
             "class": "relative", "anchor": "the Tremont"})]),
         lambda d: True if (d["businesses"][0]["anchor"]["kind"] == "unresolved"
                            and d["businesses"][0]["action"] == "street_only")
         else "anchor=%r action=%r" % (d["businesses"][0]["anchor"],
                                       d["businesses"][0]["action"]))
    case("…and a SUPERSET names nothing either",
         gaz([biz("b1", street="Lake Street", placement={
             "class": "relative", "anchor": "the Tremont House stables"})]),
         lambda d: True if d["businesses"][0]["anchor"]["kind"] == "unresolved"
         else "anchor=%r" % d["businesses"][0]["anchor"])
    case("…and an anchor naming exactly ONE still places on it",
         gaz([biz("b1", street="Lake Street", placement={
             "class": "relative", "anchor": "Dole's Warehouse"})]),
         lambda d: True if (d["businesses"][0]["anchor"]["kind"] == "structure"
                            and d["businesses"][0]["anchor"]["target"] == "dole_warehouse_south"
                            and d["businesses"][0]["action"] == "new_building")
         else "anchor=%r action=%r" % (d["businesses"][0]["anchor"],
                                       d["businesses"][0]["action"]))
    case("an anchor naming TWO documented businesses is refused on the hop too",
         gaz([biz("b1", name="Newberry & Dole", street="South Water Street"),
              biz("b2", name="Newberry & Dole", street="South Water Street"),
              biz("b3", street="South Water Street", placement={
                  "class": "relative", "anchor": "Messrs. Newberry & Dole"})]),
         lambda d: True if (d["businesses"][2]["anchor"]["kind"] == "ambiguous"
                            and d["businesses"][2]["anchor"]["via"] is None
                            and d["businesses"][2]["action"] == "street_only")
         else "anchor=%r action=%r" % (d["businesses"][2]["anchor"],
                                       d["businesses"][2]["action"]))
    unit("the town's exposure is counted, not asserted",
         structures_sharing_a_name(town), 1)

    # 4b. The guards on enrich_existing, each on the case that forced it.
    case("a firm style in `proprietors` yields its PARTNERS, not its '& Co.'",
         gaz([biz("b1", proprietors=["H. Doty & Co."], street="Lake Street")]),
         lambda d: True if d["businesses"][0]["action"] != "enrich_existing"
         else "matched %r on a firm suffix" % d["businesses"][0]["action_target"])
    case("two spelled-out forenames must match whole, not by initial",
         gaz([biz("b1", proprietors=["Georgina Dole"], street="Lake Street")]),
         lambda d: True if d["businesses"][0]["action"] != "enrich_existing"
         else "Georgina matched George's warehouse")
    case("an abbreviated forename still matches a spelled-out one",
         gaz([biz("b1", proprietors=["G. W. Dole"], street="Lake Street")]),
         lambda d: True if d["businesses"][0]["action_target"] == "dole_warehouse_south"
         else "target=%r" % d["businesses"][0]["action_target"])
    case("an aka matches only when the trades agree",
         gaz([biz("b1", proprietors=["E. Taylor"], trade="boots and shoes",
                  street="Lake Street")]),
         lambda d: True if d["businesses"][0]["action"] != "enrich_existing"
         else "a boot store matched %r" % d["businesses"][0]["action_target"])
    case("…and it does match when they do",
         gaz([biz("b1", proprietors=["E. Taylor"], trade="tavern", street="Lake Street")]),
         lambda d: True if (d["businesses"][0]["action"] == "enrich_existing"
                            and d["businesses"][0]["match_tier"] == "aka")
         else "action=%r tier=%r" % (d["businesses"][0]["action"],
                                     d["businesses"][0]["match_tier"]))
    case("an anonymous reconstructed roof is never an enrich_existing target",
         gaz([biz("b1", proprietors=["Amos Hall"], street="Lake Street")]),
         lambda d: True if d["businesses"][0]["action"] != "enrich_existing"
         else "matched the invented roof %r" % d["businesses"][0]["action_target"])
    case("a reach of a platted street resolves as a street, not as a failure",
         gaz([biz("b1", street="South Water Street", placement={
             "class": "relative", "anchor": "the east end of South Water-street"})]),
         lambda d: True if (d["businesses"][0]["anchor"]["kind"] == "street"
                            and d["businesses"][0]["action"] == "street_only")
         else "anchor=%r action=%r" % (d["businesses"][0]["anchor"]["kind"],
                                       d["businesses"][0]["action"]))

    # 4b-ii. THE ORDINAL OFF A CORNER (T-0384, the owner's ruling of 2026-08-30). Every
    # one of these is a phrase this corpus actually prints, so the tests say what the
    # reading does and does not reach rather than what a hypothetical reader might write.
    def ordinal(anchor, offset, street="South Water Street"):
        return gaz([biz("b1", street=street, placement={
            "class": "relative", "anchor": anchor, "street": street,
            "offset_normalized": offset})])

    case("a count of doors off a cross street is an ordinal, and it places",
         ordinal("Dearborn Street",
                 "on South-Water st. one door from Dearborn street"),
         lambda d: True if (d["businesses"][0]["anchor"]["kind"] == "corner_ordinal"
                            and d["businesses"][0]["anchor"]["ordinal"]["count"] == 1
                            and d["businesses"][0]["anchor"]["ordinal"]["from_street"] == "dearborn"
                            and d["businesses"][0]["anchor"]["ordinal"]["along"] == "south_water"
                            and d["businesses"][0]["action"] == "new_building")
         else "anchor=%r action=%r" % (d["businesses"][0]["anchor"],
                                       d["businesses"][0]["action"]))
    case("…and the direction is carried when the paper prints one",
         ordinal("Lake Street", "two doors north of Lake street",
                 street="Clark Street"),
         lambda d: True if (d["businesses"][0]["anchor"]["kind"] == "corner_ordinal"
                            and d["businesses"][0]["anchor"]["ordinal"]["count"] == 2
                            and d["businesses"][0]["anchor"]["ordinal"]["direction"] == "north")
         else "anchor=%r" % (d["businesses"][0]["anchor"],))
    case("two streets that never meet are no corner, however platted both are (T-0771)",
         ordinal("Lake Street",
                 "on South-Water st. five doors east of the corner of Lake street"),
         lambda d: True if (d["businesses"][0]["anchor"]["kind"] != "corner_ordinal"
                            and d["businesses"][0]["action"] == "street_only")
         else "two parallel east-west lines were read as a crossing: anchor=%r"
              % (d["businesses"][0]["anchor"],))
    case("'a few doors below' counts nothing and is refused the ordinal reading",
         ordinal("Newberry & Dole", "a few doors below Messrs. Newberry & Dole"),
         lambda d: True if d["businesses"][0]["anchor"]["kind"] != "corner_ordinal"
         else "a phrase with no count was read as an ordinal")
    case("an ordinal off a LANDMARK stays a landmark hop, not a corner ordinal",
         ordinal("Brewster, Hogan & Co.",
                 "one door east of Brewster, Hogan & Co."),
         lambda d: True if d["businesses"][0]["anchor"]["kind"] != "corner_ordinal"
         else "a building anchor was read as a street crossing")
    case("doors counted off the house's OWN street name no crossing and are refused",
         ordinal("South Water Street",
                 "two doors east of South Water street"),
         lambda d: True if d["businesses"][0]["anchor"]["kind"] != "corner_ordinal"
         else "one street was read as a crossing of itself")
    case("a reach of a street with no count is still a street, not an ordinal",
         ordinal("Lake Street", "on the east end of Lake street"),
         lambda d: True if (d["businesses"][0]["anchor"]["kind"] == "street"
                            and d["businesses"][0]["action"] == "street_only")
         else "anchor=%r action=%r" % (d["businesses"][0]["anchor"]["kind"],
                                       d["businesses"][0]["action"]))

    # 4c. THE DATED ANCHOR CHANGE (T-0345). A house whose printed anchor changed on a
    # date carries ONE live placement and the superseded ones as dated history; the
    # guards below are the three ways that could go back to being two standing
    # placements, which is the defect the ticket is about.
    def reading(a, first, last):
        return {"anchor": a, "class": "relative", "first_issue": first,
                "last_issue": last, "claims": ["c#%s" % a],
                "placement": {"class": "relative", "anchor": a}}

    def window(name, live, readings, first="1834-01-01", last="1834-06-01"):
        return {"anchor": name, "why": None, "first_issue": first, "last_issue": last,
                "readings": [reading(a, first, last) for a in readings],
                "claims": ["c#%s" % a for a in readings], "live_at_scene_date": live,
                "placement": {"class": "relative", "anchor": readings[0]}}

    def history(*windows, **kw):
        return {"rule": "the anchor changed", "cannot_say": "which side of it moved",
                "live_anchor": kw.get("live_anchor", "the hotel"),
                "live_reason": "the later of the two, printed before the scene date",
                "changes": [], "history": list(windows)}

    case("a superseded anchor is resolved and kept, and does not place the house",
         gaz([biz("b1", street="Lake Street",
                  placement={"class": "relative", "anchor": "the hotel"},
                  anchor_change=history(
                      window("Wolf Point Tavern", False, ["Wolf Point Tavern"]),
                      window("the hotel", True, ["the hotel"],
                             "1834-09-10", "1834-12-10")))]),
         lambda d: True if (
             d["businesses"][0]["anchor_change"]["history"][0]["resolved"]["target"]
             == "wolf_point_tavern"
             and d["businesses"][0]["anchor"]["kind"] == "unresolved"
             and d["businesses"][0]["action"] == "street_only")
         else "superseded=%r live=%r action=%r"
              % (d["businesses"][0]["anchor_change"]["history"][0]["resolved"],
                 d["businesses"][0]["anchor"], d["businesses"][0]["action"]))
    case("an anchor printed four ways resolves on the reading that resolves best",
         gaz([biz("b1", street="Lake Street",
                  placement={"class": "relative", "anchor": "the hotel"},
                  anchor_change=history(
                      window("Wolf Point Tavern", False,
                             ["Wolf Point Tavern, on Main-street", "Wolf Point Tavern"]),
                      window("the hotel", True, ["the hotel"],
                             "1834-09-10", "1834-12-10")))]),
         lambda d: True if (
             d["businesses"][0]["anchor_change"]["history"][0]["resolved_on_reading"]
             == "Wolf Point Tavern")
         else "resolved on %r"
              % d["businesses"][0]["anchor_change"]["history"][0]["resolved_on_reading"])
    refuses("two anchors live at the scene date is two standing placements",
            gaz([biz("b1", street="Lake Street",
                     placement={"class": "relative", "anchor": "the hotel"},
                     anchor_change=history(
                         window("Wolf Point Tavern", True, ["Wolf Point Tavern"]),
                         window("the hotel", True, ["the hotel"])))]),
            "are live at the scene date")
    refuses("the named live anchor must be the one the dates make live",
            gaz([biz("b1", street="Lake Street",
                     placement={"class": "relative", "anchor": "the hotel"},
                     anchor_change=history(
                         window("Wolf Point Tavern", True, ["Wolf Point Tavern"]),
                         window("the hotel", False, ["the hotel"])))]),
            "the dated history makes it")
    refuses("the row may not place the house on a superseded printing",
            gaz([biz("b1", street="Lake Street",
                     placement={"class": "relative", "anchor": "Wolf Point Tavern"},
                     anchor_change=history(
                         window("Dole's Warehouse", False, ["Dole's Warehouse"]),
                         window("the hotel", True, ["the hotel"])))]),
            "no reading of the LIVE printing resolves to")
    refuses("readings called one landmark may not resolve to two",
            gaz([biz("b1", street="Lake Street",
                     placement={"class": "relative", "anchor": "the hotel"},
                     anchor_change=history(
                         window("the tavern", False,
                                ["Wolf Point Tavern", "Dole's Warehouse"]),
                         window("the hotel", True, ["the hotel"])))]),
            "one landmark is one place")
    # T-0773. The same grouping with a COARSER reading of the one landmark rather than a
    # second one: a corner, and one of the two streets that make it, which is what a
    # printing reads as when the word "corner" goes with the type.
    case("a reach of the landmark's own street is one landmark, not two",
         gaz([biz("b1", street="Lake Street",
                  placement={"class": "relative", "anchor": "the hotel"},
                  anchor_change=history(
                      window("the corner of Lake and Clark streets", False,
                             ["the corner of Lake and Clark streets", "Clark-street"]),
                      window("the hotel", True, ["the hotel"])))]),
         lambda d: True if (
             d["businesses"][0]["anchor_change"]["history"][0]["resolved"]["kind"]
             == "corner")
         else "resolved %r"
              % d["businesses"][0]["anchor_change"]["history"][0]["resolved"])
    refuses("a reach the landmark does not name is still a second place",
            gaz([biz("b1", street="Lake Street",
                     placement={"class": "relative", "anchor": "the hotel"},
                     anchor_change=history(
                         window("the corner of Lake and Clark streets", False,
                                ["the corner of Lake and Clark streets",
                                 "South Water-street"]),
                         window("the hotel", True, ["the hotel"])))]),
            "which it does not name")
    refuses("two reaches and nothing that places is two landmarks",
            gaz([biz("b1", street="Lake Street",
                     placement={"class": "relative", "anchor": "the hotel"},
                     anchor_change=history(
                         window("the street", False,
                                ["Clark-street", "South Water-street"]),
                         window("the hotel", True, ["the hotel"])))]),
            "different reaches of the plat")
    # 4c. T-0355 — the two readings that put a Flag Creek tavern in a Wolf Point stable.
    # First the occupants line that caused it, read directly, because the town fixture
    # above supplies `occupant_words` ready-made and cannot exercise the clause filter.
    unit("a clause dated to another year is not a scene-date occupant",
         scene_date_occupants("the tavern's keeper of the day \u2014 Elijah Wentworth in "
                              "1831, William Walters on the scene date"),
         "the tavern's keeper of the day; William Walters on the scene date")
    unit("a clause stating no year is kept whole",
         scene_date_occupants("William Walters, landlord"), "William Walters; landlord")
    unit("a range that covers the scene date is kept",
         scene_date_occupants("William Walters 1833-1836"), "William Walters 1833-1836")
    unit("a two-digit range takes its century from its own head",
         scene_date_occupants("Eliza Chappel and her infant school, 1833-34"),
         "Eliza Chappel and her infant school")
    unit("a year range is one span, not two loose years",
         year_spans("1833-34 and 1836"), [(1833, 1834), (1836, 1836)])

    # 4d. T-0403 — a name outlives a tenancy, and the undated tiers may not put back a
    # tenant the dated occupants line has just struck out. The fixture record is named
    # and `aka`'d for John Calhoun and dates his office to 1833-1834, so at the scene
    # date the firm is not in it; before this rule the occupants tier said no and the aka
    # tier said yes one line later, and the register printed `match_tier: aka`.
    case("a firm its own record dates away is not handed back by the building's aka",
         gaz([biz("b1", name="Chicago Democrat printing office",
                  proprietors=["John Calhoun"], trade="newspaper and job printing",
                  street="South Water Street",
                  placement={"class": "relative",
                             "anchor": "Messrs. Jones & King's hardware store",
                             "street": "South Water Street"})]),
         lambda d: True if (d["businesses"][0]["action"] == "street_only"
                            and d["businesses"][0]["match_tier"] is None)
         else "action=%r tier=%r target=%r" % (d["businesses"][0]["action"],
                                               d["businesses"][0]["match_tier"],
                                               d["businesses"][0]["action_target"]))
    # And the other half, which is what keeps the rule from being a blanket refusal: the
    # SAME record, asked about the tenant its occupants line does not date away.
    case("a firm the same record does not date away still matches on the occupants line",
         gaz([biz("b1", proprietors=["William Walters"], trade="tavern",
                  street="Lake Street")]),
         lambda d: True if (d["businesses"][0]["action"] == "enrich_existing"
                            and d["businesses"][0]["action_target"] == "wolf_point_tavern")
         else "action=%r target=%r" % (d["businesses"][0]["action"],
                                       d["businesses"][0]["action_target"]))

    # Then the guard the fault generalises to: the firm's own record says where it is.
    case("a distance in miles refuses every match into the committed town",
         gaz([biz("b1", proprietors=["George W. Dole"], street="Lake Street", placement={
             "class": "relative", "anchor": "thirteen miles south of Chicago"})]),
         lambda d: True if (d["businesses"][0]["action"] == "unplaceable"
                            and d["businesses"][0]["outside_plat"])
         else "action=%r outside=%r" % (d["businesses"][0]["action"],
                                        d["businesses"][0]["outside_plat"]))
    case("a road leading out of town refuses it too",
         gaz([biz("b1", proprietors=["George W. Dole"], placement={
             "class": "relative", "anchor": "the road from Chicago leading to Ottawa"})]),
         lambda d: True if d["businesses"][0]["action"] == "unplaceable"
         else "action=%r target=%r" % (d["businesses"][0]["action"],
                                       d["businesses"][0]["action_target"]))
    case("a named creek in the firm's own name refuses it, placement or no placement",
         gaz([biz("b1", name="E. Wentworth's tavern, Flag Creek",
                  proprietors=["George W. Dole"])]),
         lambda d: True if (d["businesses"][0]["action"] == "unplaceable"
                            and "Flag Creek" in d["businesses"][0]["outside_plat"])
         else "action=%r outside=%r" % (d["businesses"][0]["action"],
                                        d["businesses"][0]["outside_plat"]))
    case("a firm the papers do NOT put out of town still enriches",
         gaz([biz("b1", proprietors=["George W. Dole"], street="Lake Street")]),
         lambda d: True if (d["businesses"][0]["action"] == "enrich_existing"
                            and d["businesses"][0]["outside_plat"] is None)
         else "action=%r outside=%r" % (d["businesses"][0]["action"],
                                        d["businesses"][0]["outside_plat"]))

    # 5. The identity policy is the gazetteer's, imported and not re-invented.
    case("a resident already held takes enrich",
         gaz(persons=[person("p1", "P. Cohen")]),
         lambda d: True if (d["persons"][0]["action"] == "enrich"
                            and d["persons"][0]["action_target"] == "cohen_peter")
         else "action=%r target=%r" % (d["persons"][0]["action"], d["persons"][0]["action_target"]))
    case("a different forename initial NEVER matches a resident",
         gaz(persons=[person("p1", "J. Cohen")]),
         lambda d: True if d["persons"][0]["action"] == "new_resident"
         else "action=%r" % d["persons"][0]["action"])
    # T-0866: the link is to the card the mint wrote from this printed name, so it
    # outlives the display string. Under the initials policy alone `Gabbs, James I1.`
    # reads ('j', 'i') against the corrected card's ('j', '?') and matches nothing.
    case("a card renamed since it was minted is still the person the papers print",
         gaz(persons=[person("p1", "Gabbs, James I1.", letter_list_only=True)]),
         lambda d: True if (d["persons"][0]["action"] == "enrich"
                            and d["persons"][0]["action_target"] == "gabbs_james_i1")
         else "action=%r target=%r" % (d["persons"][0]["action"], d["persons"][0]["action_target"]))
    case("the surname-first setting is read by the pass that mints from it",
         gaz(persons=[person("p1", "Mills Joel C.", letter_list_only=True)]),
         lambda d: True if (d["persons"][0]["action"] == "enrich"
                            and d["persons"][0]["action_target"] == "mills_joel_c")
         else "action=%r target=%r" % (d["persons"][0]["action"], d["persons"][0]["action_target"]))
    case("and the row says which of the two links carried it",
         gaz(persons=[person("p1", "Gabbs, James I1.", letter_list_only=True)]),
         lambda d: True if "minted that card from this printed name" in d["persons"][0]["action_note"]
         else "note=%r" % d["persons"][0]["action_note"])
    case("a name no mint wrote a card from is still ruled by the identity policy",
         gaz(persons=[person("p1", "P. Cohen")]),
         lambda d: True if "surname plus forename initials" in d["persons"][0]["action_note"]
         else "note=%r" % d["persons"][0]["action_note"])

    # …and the gate over it fires on both halves, asked of rows the matcher above can no
    # longer produce — which is the whole reason it is a separate function (T-0866).
    minted = {"person": "gabbs_james_i1", "source_pass": "letter_list"}
    unit("the gate catches a minted card called a stranger",
         bool(minted_link_problems(
             [{"id": "p1", "name": "Gabbs, James I1.", "action": "new_resident",
               "action_target": None}], lambda n: minted)), True)
    unit("the gate catches a minted card's row handed to somebody else",
         bool(minted_link_problems(
             [{"id": "p1", "name": "Gabbs, James I1.", "action": "enrich",
               "action_target": "gabbs_james"}], lambda n: minted)), True)
    unit("and it is silent where the row reaches its own card",
         minted_link_problems(
             [{"id": "p1", "name": "Gabbs, James I1.", "action": "enrich",
               "action_target": "gabbs_james_i1"}], lambda n: minted), [])

    case("a documented baker is a candidate to retire the invented one",
         gaz(persons=[person("p1", "Amos Thing", occupations=["baker"])]),
         lambda d: True if (d["persons"][0]["action"] == "replace_invented"
                            and d["persons"][0]["action_target"] == "baker")
         else "action=%r target=%r" % (d["persons"][0]["action"], d["persons"][0]["action_target"]))
    case("a letter-list name still mints a resident, flagged",
         gaz(persons=[person("p1", "Obadiah Nobody", letter_list_only=True)]),
         lambda d: True if (d["persons"][0]["action"] == "new_resident"
                            and d["persons"][0]["letter_list_only"])
         else "action=%r flag=%r" % (d["persons"][0]["action"], d["persons"][0]["letter_list_only"]))

    # 6. The retirement count is capped by what the town actually invented.
    case("three documented bakers retire ONE invented baker household",
         gaz(persons=[person("p%d" % i, "%s Baker%d" % (n, i), occupations=["baker"])
                      for i, n in enumerate(("Amos", "Ezra", "Silas"), start=1)]),
         lambda d: True if d["counts"]["invented_residents"]["retirable_total"] == 1
         else "retirable=%r" % d["counts"]["invented_residents"]["retirable_total"])

    # 7. Determinism: the same inputs twice, byte for byte.
    g = gaz([biz("b1", proprietors=["George W. Dole"], street="Lake Street")],
            [person("p1", "P. Cohen")])
    if dumps(compile_register(g, town)[0]) != dumps(compile_register(g, town)[0]):
        failures.append("determinism: two compiles of one input differ")

    for f in failures:
        print("  FAIL  " + f, file=sys.stderr)
    if not failures:
        print("  ok    %d self-test case(s)" % CASES[0])
    return 1 if failures else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.build:
        return build()
    if args.self_test:
        return self_test()
    bad = check()
    for b in bad:
        print("  FAIL  " + b, file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
