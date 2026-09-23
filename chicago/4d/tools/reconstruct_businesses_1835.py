#!/usr/bin/env python3
"""THE 1835 BUSINESS RECONSTRUCTION — one writer, five groups, one quota.

    python3 tools/reconstruct_businesses_1835.py --group stores_and_provisions --build
    python3 tools/reconstruct_businesses_1835.py --check          # every built group
    python3 tools/reconstruct_businesses_1835.py --self-test

T-1184 builds this and T-1185 … T-1188 reuse it. The five reconstruction tickets of the
business band differ in exactly one thing — WHICH ROWS OF THE ORDER BOOK THEY OWN — and the
order book already says which, on every bucket, in `owning_ticket`. So a group here is a key
and a ticket number, the classes are READ from the book rather than restated, and a ticket
that re-cuts the book moves this tool's quota with it. Nothing about the quota lives in this
file; what lives here is the rule for turning a quota row into a house of trade.

WHAT A RECONSTRUCTED BUSINESS IS, AND WHAT IT IS NOT. It is a firm the December 1835 State
census counts and the newspaper register does not hold: the census prints four druggists and
the register carries two, so the town of 1 July 1835 had two apothecaries' shops nobody
wrote the name of. This tool writes those two. It is NOT a reading, it carries no source, it
may never be promoted, and every field on it names the rule that drew it and the evidence
that would retire it — `reconstruction.basis`, `reconstruction.seed`, `replaceable_by`.

THE PROPRIETOR IS ADOPTED, NEVER MINTED. `tools/reconstruct_residents_1835.py` is the one
writer of a person graded `reconstructed` and this tool is deliberately not a second one.
The resident band's `trade_households` stage (T-1347, of T-1173) already drew heads at the
trades the town was short of, and every one of those cards says so itself: "the business
band (T-1184 … T-1188) ADOPTS these heads as its proprietors rather than minting its own, so
the two bands fill one quota." A group whose class orders more houses than that band drew
heads for is REFUSED here rather than quietly under-filled — the shortfall is the resident
band's to draw, and a business tool that minted its own proprietor would order the same
person twice.

THE STYLE IS PERIOD OR IT IS NOTHING. `docs/RESEARCH/business-naming-1835.md` is the guide,
written from the 196 firm styles the register prints, and STYLES below is its executable
half. A reconstructed firm may not reuse an attested firm style, an attested house's name,
or an attested proprietor's name; `--check` refuses each.

THE LOCATION IS A LIMIT. Every record here takes a `street_only` location on a face the
placement rule allows for its class and division — no lot, no roof, no coordinate. T-1195
writes the placement policy properly and T-1199 seats these houses on the lot grid; until
then the face is a deal off a stated rule and the `limit_reason` says exactly that.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compile_businesses import (  # noqa: E402
    derive_proprietor_community,
    person_communities,
)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESIDENTS = DATA / "residents"
TRADE_HOUSEHOLDS = RESIDENTS / "reconstructed_trades"
AUTHORED = DATA / "businesses" / "authored"
ORDER_BOOK = DATA / "reconstruction" / "1835_reconstruction_order_book.json"
STREETS = DATA / "streets" / "1835.json"
LEDGER = DATA / "reconstruction" / "1835_business_reconstruction.json"
LODGING_MODEL = DATA / "reconstruction" / "1835_lodging_model.json"
LODGERS = DATA / "residents" / "lodgers"
VESSELS_IN_PORT = DATA / "reconstruction" / "1835_vessels_in_port.json"

PROGRAMME = "chicago_1835_business_reconstruction"
SCENE_DATE = "1835-07-01"


# ------------------------------------------------------------------- the five groups

GROUPS = {
    "stores_and_provisions": {
        "ticket": "T-1184",
        "title": "stores, book stores and the drug and provision trades",
    },
    "mechanics_shops": {"ticket": "T-1185", "title": "the mechanics' shops"},
    # T-1186 split on 2026-09-20: T-1418 owns the two census rows this group fills
    # (the professions), T-1419 the services the census enumerates nowhere. The ticket here
    # is the ORDER BOOK's — whose buckets this group spends — and it stays T-1418's; the
    # services are ordered by no bucket at all and each of their records names T-1419 for
    # itself, out of TRADE_QUOTA below.
    "professions_and_services": {"ticket": "T-1418",
                                 "title": "the professions and the services"},
    "lodging_river_and_transport": {
        "ticket": "T-1187", "title": "lodging, the river and transport"},
    "civic_church_school_and_press": {
        "ticket": "T-1188", "title": "the civic, church, school and press establishments"},
}


# ------------------------------------------------- the second quota: a roof, not a count
#
# THE ORDER BOOK CANNOT ORDER A BOARDING HOUSE, and that is a property of the census
# rather than a hole in the book. `business_buckets` in tools/build_order_book_1835.py
# orders against PRINTED COUNTS or not at all, and the December 1835 State census
# enumerates taverns — eight of them, all attested, and the town keeps eight — while it
# never enumerates a boarding house at all. So no shortfall of this class can ever be
# counted, and the first quota has nothing to say about the one part of the lodging
# economy this town demonstrably had: the 1840 schedule's 8.2 people to a dwelling.
#
# What this project HAS already committed is the BUILDING. Five boarding houses stand in
# `data/structures/`; the lodging model (T-1370) apportioned each of them beds out of a
# bracket the town model owns; the lodgers stage (T-1371) put people in those beds and
# named a keeper for every reconstructed one. A house with beds, lodgers and a keeper and
# no firm behind it is an establishment the business layer cannot see — it does not appear
# in the Businesses view, its building card names no trade, and the keeper's own card can
# say she keeps a boarding house while nothing in the town holds one.
#
# So the roof is the quota. One record per STANDING reconstructed lodging roof of the
# class below, and never one for a slot the roof programme has scheduled and not built:
# the 37 unbuilt boarding houses are 333 beds with no roof over them (T-1196 re-derives
# the programme, T-1409 raises the houses) and a firm in a building site is a fiction of a
# different kind. The named houses are not touched either — who kept the New York House in
# 1835 is a research question, and the lodgers stage refused to answer it for exactly this
# reason; their keepers come from the register through T-1404.
ROOF_QUOTA = {
    "lodging_river_and_transport": {
        "ticket": "T-1408",
        "lodging_class": "boarding_house",
        # THE CENSUS CLASS A BOARDING HOUSE TAKES, and why it is not its own. `type` is the
        # ONE taxonomy — the December 1835 State census's classes — so that a business
        # counts against the census without a second crosswalk. That census has no boarding
        # -house line, and `other` is precisely its bucket for a class it never put a figure
        # against. Typing these houses `tavern` would spend the eight-tavern count the
        # register already fills; minting a class the census never printed would put a
        # nineteenth line in a taxonomy whose whole job is to match an eighteen-line
        # document. The trade is carried in `trade` and `occupation`, which are free of it.
        "type": "other",
        "trade": "boarding house",
        "occupation": "boarding_house_keeper",
    },
}

# THE KEEPER'S POSSESSIVE, form 5 of docs/RESEARCH/business-naming-1835.md, which is the
# form this town's own lodging houses take: *Miss Bayne's Boarding and Day School* in the
# register, *Rufus Brown's Boarding House* on the one boarding house the structure layer
# names. NO HONORIFIC IS DEALT. Three of the four keepers the lodgers stage drew are women,
# and `Mrs.` would assert a marriage, `Miss` a want of one; the cards carry neither, because
# the stage minted them as solitary keepers and nothing in the layer says which. A style
# that reached for the honorific would be inventing a marital status to make a sign read
# well — so the possessive stands on the name alone, which asserts only what the card holds.
ROOF_STYLES = {
    "boarding_house": {
        "forms": [
            ("{given} {surname}'s boarding house",
             "the possessive in full, as the structure layer's own *Rufus Brown's Boarding "
             "House* prints it"),
            ("{surname}'s boarding house",
             "the possessive with the forename cut, as *Ingersoll's tavern stand* and "
             "*Stuart's confectionary and perfumery* print it in the register"),
        ],
    },
}


# ------------------------------------- the third quota: a trade, not a count and not a roof
#
# THE ORDER BOOK CANNOT ORDER A LIVERY STABLE EITHER, and for the same reason it cannot
# order a boarding house: `business_buckets` orders against PRINTED COUNTS or not at all,
# and the December 1835 State census's eighteen lines reach the taverns, the stores and the
# saw-mill and never reach a livery stable or a lumber yard. But the roof form of T-1408
# does not rescue these two. A boarding house had a BUILDING already committed — beds
# apportioned, lodgers seated, a keeper named — and the firm was the only thing missing.
# Nothing in `data/structures/` is a livery stable. There is no roof to point at.
#
# What there IS, and what nothing else in this tool has yet spent, is THE HEAD. The
# resident band's `trade_households` stage drew two men at `livery_stable_keeper` and two
# at `lumber_merchant` — drawn because the 1839 trade table says the town was short of
# them, and every one of those cards says in its own `works_at` that the business band
# adopts these heads rather than minting its own. A head at one of those trades and no
# house behind it is the mirror image of T-1408's fault: there the building had no firm,
# here the KEEPER has no firm, and in both cases the business layer cannot see an
# establishment this project has already committed itself to.
#
# So the trade is the quota, and the rule is the meaning of the word. `livery_stable_keeper`
# names, inside the occupation itself, the thing kept; so does `lumber_merchant`, whose
# trade in this town is a YARD on the water — the register's one printed yard is "announced
# for the opening of navigation". A trade whose word names a house of trade orders one
# house per head. A trade whose word names an EMPLOYMENT — `teamster`, `boatman`, `seaman`,
# `sawyer` — orders nothing here; the man is somebody else's hand and T-1189 seats him.
# RIVER_AND_TRANSPORT below is that ruling written out, trade by trade, so that no head is
# passed over in silence: the ledger prints every one of them with the kind of absence it is.
#
# THE CLASS IS `other` AND MAY NEVER BE OTHERWISE. Typing a lumber yard
# `storage_and_forwarding` would spend a count the register already over-holds — four
# printed houses ordered, eight standing — exactly as typing a boarding house `tavern`
# would spend the eight-tavern count. `--check` refuses a trade row whose census class is
# one the order book enumerates, by name.
TRADE_QUOTA = {
    "lodging_river_and_transport": {
        "ticket": "T-1424",
        "trades": {
            "livery_stable_keeper": {
                "house": "livery_stable",
                # `other` is the census's bucket for a trade the register printed and the
                # enumeration has no line for, and the register prints two liveries.
                "type": "other",
                "trade": "livery stable",
                "occupation": "livery_stable_keeper",
                "basis": ("the occupation names the house: a livery stable keeper keeps a "
                          "livery stable, and the register prints two of them — Lathrop "
                          "Johnson & Co., livery, and the Livery Stable at the Point — "
                          "against a census that enumerates neither"),
            },
            "lumber_merchant": {
                "house": "lumber_yard",
                "type": "other",
                "trade": "lumber yard",
                "occupation": "lumber_merchant",
                "basis": ("a lumber merchant in this town keeps a YARD: the register's one "
                          "printed house of the trade is a lumber yard and warehouse "
                          "announced for the opening of navigation, 1834, and the census "
                          "enumerates no yard at all"),
            },
        },
    },
    # THE SERVICES THE CENSUS ENUMERATES NOWHERE (T-1419, of T-1186). The professions half
    # of this group is ordered against two printed counts — twenty-two lawyers and fourteen
    # physicians — and T-1418 spent them. NONE of the four trades below is a line of the
    # December 1835 State census, so none of them has an order-book bucket and none of them
    # can be short of a count; what this town's research HAS committed is the person. The
    # resident band drew each of these heads at a trade whose own word names the house, and
    # every one of the four is a trade the register itself prints houses of.
    "professions_and_services": {
        "ticket": "T-1419",
        "trades": {
            "land_agent": {
                "house": "land_office",
                "type": "other",
                "trade": "land agency",
                "occupation": "land_agent",
                "basis": ("a land agent kept an office and the register prints three houses "
                          "of the trade — J. C. Goodhue, land agent; W. G. Blanchard, house "
                          "and land agent, on Lake Street; and one unnamed house and land "
                          "agent — against a census that enumerates no land office at all"),
            },
            "milliner": {
                "house": "millinery",
                "type": "other",
                "trade": "millinery",
                "occupation": "milliner",
                "basis": ("a millinery is a shop front, and the register prints three of "
                          "them at the scene date — Elmira Fowler on Dearborn Street, Mrs. "
                          "H. Sherman and [Mrs.] Herman at the Mansion House — all under "
                          "the one trade line 'millinery and dress making', against a "
                          "census with no line for a milliner"),
            },
            "dressmaker": {
                "house": "dress_making_shop",
                "type": "other",
                "trade": "dress making",
                "occupation": "dressmaker",
                "basis": ("the register's one printed house of the trade is Sarah D. Howe's "
                          "dress, cloak and habit making on Lake Street, and the December "
                          "census enumerates no dress maker"),
            },
            "barber_surgeon": {
                "house": "barbers_shop",
                "label": "barber's shop",
                "type": "other",
                "trade": "barber's shop",
                "occupation": "barber_surgeon",
                "basis": ("a barber keeps a shop front — PUBLIC_TRADES `shop` of the "
                          "signage rule — and this project already stands one of them, "
                          "rcb_fb_barbers_shop, on T-1377's documented floor of the town's "
                          "free Black residents; that floor is an argument about PEOPLE and "
                          "it orders no second shop, so the second shop is bought by the "
                          "head or not at all"),
            },
        },
    },
}

# THE FORMS, each drawn from the register's own printings of these two trades, as STYLES is
# for the counted classes. There are only three printed houses between them, so there are
# only the lines those three carry and nothing is composed.
TRADE_STYLES = {
    "livery_stable": {
        "forms": [
            ("{initial}. {surname}, {goods}",
             "the form 'Lathrop Johnson & Co., livery' prints, with the firm cut to the "
             "sole keeper it is — an initial and a surname, as 'S. Foot' and 'A. Garrett' "
             "print elsewhere in the register"),
            ("{given} {surname}, {goods}",
             "the same with the forename in full, as 'Frederick Thomas, drugs and paints' "
             "and 'William F. Lyon, Wholesale Grocery Store' print it"),
        ],
        "goods": [
            ("livery", "the trade line the register prints under Lathrop Johnson & Co."),
            ("livery stable",
             "the register's own words for the trade in 'the Livery Stable at the Point'"),
        ],
    },
    "lumber_yard": {
        "forms": [
            ("{initial}. {surname}, {goods}",
             "the sole trader's signature, form 1 of the naming guide: 'B. Jones, grocery "
             "and provision store', 'J. C. Goodhue, land agent'"),
            ("{surname}'s {goods}",
             "the keeper's possessive, form 5, which this town puts on its yards and open "
             "grounds: 'A. Clybourn's market on the market square'"),
        ],
        "goods": [
            ("lumber yard",
             "the head of the register's own line, 'the lumber yard and warehouse announced "
             "for the opening of navigation, 1834'"),
            ("lumber yard and store house",
             "that same house's trade line — 'lumber yard and store house, on sale and "
             "commission' — cut to its two heads, the third being a commission the "
             "reconstruction does not claim"),
        ],
    },    # AND THE FOUR SERVICE HOUSES, on the same footing: every form and every goods line
    # below is a printing of THAT TRADE in this register, except the barber's, which has no
    # printing in the corpus at all and takes the naming guide's own sole-trader forms with
    # the one trade word the project already stands a barber's shop under.
    "land_office": {
        "forms": [
            ("{initial}. {surname}, {goods}",
             "the form the register prints this trade in twice over — 'J. C. Goodhue, land "
             "agent' and 'W. G. Blanchard, house and land agent' — which is also form 1 of "
             "the naming guide, the commonest signature in the corpus"),
            ("{given} {surname}, {goods}",
             "the same signature with the forename in full, the attested minority form "
             "('Frederick Thomas, drugs and paints', 'William F. Lyon, Wholesale Grocery "
             "Store')"),
        ],
        "goods": [
            ("land agent", "the trade line the register prints under J. C. Goodhue"),
            ("house and land agent",
             "the trade line the register prints under W. G. Blanchard, and again over its "
             "one unnamed house of the trade"),
        ],
    },
    "millinery": {
        "forms": [
            ("{given} {surname}, {goods}",
             "the form the register prints the trade in: 'Elmira Fowler', the one milliner "
             "it names in full and without an honorific"),
            ("{initial}. {surname}, {goods}",
             "form 1 of the naming guide, the corpus's commonest signature — and the form "
             "'Mrs. H. Sherman' prints once the honorific is cut, which this programme cuts "
             "everywhere (docs/LIBERTIES.md § L257)"),
        ],
        "goods": [
            ("millinery",
             "the head of the trade line all three printed millineries carry, 'millinery "
             "and dress making'"),
            ("millinery and dress making",
             "that line whole, as Elmira Fowler, Mrs. H. Sherman and [Mrs.] Herman all "
             "print it"),
        ],
    },
    "dress_making_shop": {
        "forms": [
            ("{given} {surname}, {goods}",
             "the form the register prints the trade in: 'Sarah D. Howe', the town's one "
             "printed dress maker, named in full"),
            ("{initial}. {surname}, {goods}",
             "form 1 of the naming guide, the corpus's commonest signature"),
        ],
        "goods": [
            ("dress making",
             "the trade's own words in the register, from the tail of 'millinery and dress "
             "making' and the head of Sarah D. Howe's own line"),
            ("dress, cloak and habit making",
             "Sarah D. Howe's trade line whole, as the register prints it"),
        ],
    },
    "barbers_shop": {
        "forms": [
            ("{given} {surname}, {goods}",
             "THE TRADE HAS NO PRINTING IN THIS CORPUS and no form is composed for it: this "
             "is the naming guide's form 1 with the forename in full, and it is the form "
             "the project's one standing barber's shop already takes — 'Benjamin Anderson, "
             "barber' (rcb_fb_barbers_shop, T-1377)"),
            ("{initial}. {surname}, {goods}",
             "the same signature with the initial, which is form 1's majority reading in "
             "the register — 'A. Garrett', 'S. Foot', 'S. Dewey'"),
        ],
        "goods": [
            ("barber",
             "the one trade word this project already stands a barber's shop under, and no "
             "second line is dealt: the register prints none for the trade, and the naming "
             "guide refuses a goods line composed for a class rather than taken from it"),
        ],
    },
}

# AND THE FACES, on the same footing as FACES above: a rule stated from where the register
# puts the trade, and no further. T-1195 re-cuts these when the placement policy is written.
TRADE_FACES = {
    # A LIVERY STANDS WITH THE TAVERNS IT SERVES. The one livery the register places is
    # "at the Point" — the forks, where the west and north roads reach the town and where
    # Wolf Point's taverns stand. It is not a retail front; it wants a yard, a gate and the
    # road. So the rule is the approach and the hotel streets, and never the river bank.
    "livery_stable": {
        "south": ["lake", "dearborn", "randolph"],
        "north": ["kinzie", "north_water"],
        "west": ["canal", "west_water"],
    },
    # A LUMBER YARD WANTS WATER. The register's own yard is announced for the OPENING OF
    # NAVIGATION, which is how lumber reached this town and how it left it; the trade takes
    # the working banks, on the same rule the brewery does, and never a retail street.
    "lumber_yard": {
        "south": ["south_water", "market"],
        "north": ["north_water", "kinzie"],
        "west": ["west_water", "canal"],
    },
    # A LAND OFFICE IS A DOOR AMONG DOORS, on the same rule the law offices take: the one
    # land agent the register resolves a place for is W. G. Blanchard on LAKE STREET, and
    # the two business streets either side of it follow Lake rather than a rule of their
    # own. Goodhue and the unnamed house are unplaced, so Lake leads on the one placing
    # there is and nothing narrower is claimed.
    "land_office": {
        "south": ["lake", "south_water", "dearborn"],
        "north": ["kinzie", "north_water"],
        "west": ["canal", "west_water"],
    },
    # A MILLINERY IS A RETAIL FRONT and never a working bank. Elmira Fowler advertises from
    # DEARBORN STREET and Sherman and Herman both sit at the Mansion House on Lake, so the
    # rule is the two shopping streets and no third. North of the river that is Kinzie, the
    # north division's store street, and in the west it is the Canal Street approach — the
    # same reading the book store takes, for the same reason: a shop a customer walks to.
    "millinery": {
        "south": ["lake", "dearborn"],
        "north": ["kinzie"],
        "west": ["canal"],
    },
    # A DRESS MAKING SHOP TAKES THE MILLINERY'S RULE, and the register argues it directly:
    # Sarah D. Howe prints from LAKE STREET, and the trade shares its one printed trade line
    # with the millineries.
    "dress_making_shop": {
        "south": ["lake", "dearborn"],
        "north": ["kinzie"],
        "west": ["canal"],
    },
    # A BARBER'S SHOP IS A SHOP FRONT TOO — `shop` of the signage rule, and the Chicago
    # American of August 1835 counts the barber among the town's mechanics' shops. The
    # register places none, so the rule is the shop-front rule and not a reading.
    "barbers_shop": {
        "south": ["lake", "dearborn"],
        "north": ["kinzie"],
        "west": ["canal"],
    },
}

# EVERY RIVER AND TRANSPORT TRADE THE RESIDENT BAND DREW A HEAD AT, AND WHAT BECOMES OF IT.
# The acceptance clause of T-1424 and the reason the ledger carries a table rather than a
# count: a head with no house is not one thing. Some are houses this programme built; one
# is a class whose count the register already over-holds, so the shortfall was in PERSONS
# and never in establishments; most are employments, which have no premises to keep at all;
# and two are deferred to T-1425 with the evidence they wait on named. A trade missing from
# this table is REFUSED by name rather than passed over, which is the whole point of it.
# THE CLOSED VOCABULARY OF `kind`, so that a new ruling has to be declared rather than
# typed. `deferred` stays in it — T-1425 emptied it and a later ticket may fill it again —
# but a deferral now has to name a ticket that is STILL OPEN, which is the guard this
# ticket's own history asks for: T-1424 deferred two heads on a stated reason that was
# already false, and nothing re-read it until the successor ran.
# `census_bucket` joined it with T-1419: a class the order book DOES hold a bucket of, which
# is ordered by the printed count and filled by the ticket that owns the bucket — the ruling
# the professions needed and the river trades never did.
RIVER_KINDS = ("house_of_trade", "census_bucket", "count_already_held", "employment",
               "commands_a_vessel", "contract_not_premises", "deferred")

RIVER_AND_TRANSPORT = {
    "livery_stable_keeper": {
        "kind": "house_of_trade",
        "why": "the trade names the house; this programme builds one per head.",
    },
    "lumber_merchant": {
        "kind": "house_of_trade",
        "why": "the trade names the house; this programme builds one per head.",
    },
    "forwarding_and_commission": {
        "kind": "count_already_held",
        "why": ("NO ESTABLISHMENT TO ORDER, AND THAT IS NOT THE SAME AS NO MAN TO PLACE. "
                "The December 1835 State census prints four storage and forwarding houses "
                "and the register holds EIGHT at the scene date, so "
                "`businesses/storage_and_forwarding` leaves nothing to reconstruct and the "
                "'gap beyond the attested four' T-1409 went looking for is not there. The "
                "resident band still drew these heads, and rightly: it draws against the "
                "PERSON buckets, off the 1839 trade table's share of men at a trade, and a "
                "town can be short of forwarding clerks while holding twice the houses it "
                "was counted for. So these men are hands at houses that already stand, and "
                "T-1189 seats them; a firm minted here would be a ninth house against a "
                "count of four."),
    },
    "teamster": {
        "kind": "employment",
        "why": ("NO PREMISES. A teamster drives another man's team or his own off the "
                "street; the dray is the trade and there is no house of it to build. The "
                "livery stables above are where the town's hire teams stood, and T-1189 "
                "seats these men at the houses, yards and landings that employed them."),
    },
    "boatman": {
        "kind": "employment",
        "why": ("NO PREMISES. A boatman is a hand on the water — the ferry at the forks, "
                "the lighters working the bar, the river craft. T-1189 seats him."),
    },
    "seaman": {
        "kind": "employment",
        "why": ("NO PREMISES. A seaman's berth is a vessel and not a house of trade; the "
                "vessels themselves are T-1425's."),
    },
    "sawyer": {
        "kind": "employment",
        "why": ("NO PREMISES, AND THE MILL IS ALREADY STANDING. The census prints one steam "
                "saw-mill and the register holds two at the scene date, so the class orders "
                "nothing; a sawyer is a hand in one of them and T-1189 seats him."),
    },
    "master_mariner": {
        "kind": "commands_a_vessel",
        "why": ("A MASTER COMMANDS A VESSEL, NOT A PREMISES — and T-1425 settled it with "
                "the marine list in front of it. T-1424 deferred this head on the ground "
                "that 'no source in data/sources/ prints the port of Chicago's arrivals "
                "and clearances for 1835'. THAT WAS WRONG WHEN IT WAS WRITTEN. The "
                "Marine Journal of the Chicago American heads PORT OF CHICAGO and enters "
                "arrivals and clearances week by week; the column of 4 July 1835 spans "
                "the scene date itself, and the reading has been committed since T-1372 "
                "at data/reconstruction/1835_vessels_in_port.json — six hulls, four of "
                "them mastered by name. Having it changes nothing about the ruling and "
                "everything about its standing: the column gives masters and gives no man "
                "a house, the four it names are lake masters entered at this port and not "
                "householders of this town, and a house of trade cannot be ordered for a "
                "trade whose premises float. WHAT THE LIST DID BUY is the join T-1425 "
                "made instead — two of those hulls ARE houses in this register, the "
                "Chicago & St. Joseph packets, and the vessels file now says so hull by "
                "hull. A packet is a business; commanding one is not."),
    },
    "mail_contractor": {
        "kind": "contract_not_premises",
        "why": ("A CONTRACT IS NOT A SHOP, and T-1425 closes the deferral without "
                "building anything. The mail contractor holds a ROUTE under the Post "
                "Office Department; the office at the end of it is a civic establishment "
                "T-1410 already built, and this corpus gives the contractor no stage yard, "
                "no stable and no stand of his own — the stage and stable yard T-1424 "
                "wondered about is a building nobody printed. The hire teams of this town "
                "stood at the two livery stables the trade quota built, which is where a "
                "route's horses would be kept by a man who kept no yard. So the head is a "
                "contract and keeps no house, and T-1189 seats him where the work was "
                "done."),
    },
}

# AND THE ONE T-1409 ASKED FOR THAT NO HEAD STANDS BEHIND. The resident band drew nobody at
# the harbour works — there is no `contractor` and no `pier hand` in its occupation
# vocabulary — so the works reach this table nowhere, and a reader of a head-by-head
# adjudication would be entitled to think the question had never been put. It was, and the
# answer is a refusal with the missing document named: see `the_contractor_this_file_cannot
# _name` in data/reconstruction/1835_vessels_in_port.json, which T-1425 wrote beside the
# hulls. The federal improvement was at work across the scene date and no committed source
# names a contractor, a foreman or a strength in any month of 1835; the nearest thing the
# tree holds is a tier-3 retrospective making Samuel Jackson foreman from June 1833, two
# seasons early and unbounded at the far end. The business band orders no house for a man it
# cannot name.
PIER_WORKS = {
    "kind": "refused_no_source",
    "ticket": "T-1425",
    "why": ("THE PIER WORKS ARE A PUBLIC UNDERTAKING AND THIS CORPUS CANNOT NAME THEIR "
            "CONTRACTOR. T-1409 asked for the pier-works contractor and his gang beside "
            "the vessels in port. No head in the resident band stands at the works — the "
            "occupation vocabulary has no `contractor` and no pier hand — so no trade row "
            "above reaches them, and the ask would otherwise vanish between the rows. The "
            "federal harbour improvement was at work across the scene date; both piers are "
            "committed structures and the 1835 appropriation was $32,800; and no committed "
            "source gives the works a contractor, a foreman or a strength in any month of "
            "1835. data/reconstruction/1835_transient_cohort.json prices the gang "
            "'bounded: no' for the same reason."),
    "nearest_thing_the_tree_holds": ("data/sources/resident_research_cook_harbor_jackson.json "
                                     "— a tier-3 retrospective making Samuel Jackson foreman "
                                     "of the harbour construction 'for some time' from June "
                                     "1833: two seasons early, unbounded at the far end, and "
                                     "not a claim about 1 July 1835."),
    "replaceable_by": ("The Chief Engineer's annual report for 1835, or the House Document "
                       "series — named and unfound in docs/RESEARCH/north_pier.md, dossier "
                       "01. A strength for the works in the season of 1835 retires this "
                       "refusal and orders whatever it orders."),
    "written_beside_the_hulls": "data/reconstruction/1835_vessels_in_port.json",
}


# EVERY PROFESSIONAL AND SERVICE TRADE THE RESIDENT BAND DREW A HEAD AT, AND WHAT BECOMES OF
# IT. The acceptance clause of T-1419 and the twin of the table above. The professions half
# of this group was ordered against two PRINTED COUNTS and T-1418 spent them; the services
# half has no count at all, because the December 1835 State census's eighteen lines reach
# none of these trades. So the rows below carry one kind the river table did not need —
# `census_bucket`, a class the book DOES hold a bucket of, which is ordered by the count and
# never by the head — and the four houses this ticket builds are bought by the head instead.
# Two trades the parent ticket argued for are REFUSED HERE BY NAME rather than passed over:
# the dentist's stand, and the laundress's washing as a house of trade.
SERVICES = {
    "land_agent": {
        "kind": "house_of_trade",
        "why": "the trade names the house; this programme builds one per head.",
    },
    "milliner": {
        "kind": "house_of_trade",
        "why": "the trade names the house; this programme builds one per head.",
    },
    "dressmaker": {
        "kind": "house_of_trade",
        "why": "the trade names the house; this programme builds one per head.",
    },
    "barber_surgeon": {
        "kind": "house_of_trade",
        "why": ("THE ARGUMENT RESTATED, WHICH IS WHAT T-1186 ASKED FOR BEFORE A SECOND "
                "BARBER WAS RAISED. The old programme's argument was a COUNT — a barber "
                "bucket in the order book — and it was refused, because the December census "
                "prints no barber and the book orders against printed counts or not at all. "
                "The argument here is not a count: this project already stands one barber's "
                "shop, rcb_fb_barbers_shop, on T-1377's documented floor of the town's free "
                "Black residents, and that floor argues about PEOPLE and orders no second "
                "shop. What is committed is the second head — the resident band drew Daniel "
                "Brady at barber_surgeon — and the trade names the shop he keeps. One head, "
                "one shop, withdrawn with him."),
    },
    "attorney": {
        "kind": "census_bucket",
        "why": ("THE COUNT IS PRINTED, SO THE COUNT ORDERS. The December 1835 State census "
                "counts twenty-two lawyers, the order book holds the bucket and T-1418 "
                "filled it; a head left over is a man the printed count does not reach, and "
                "a house raised for him here would spend a count the register may already "
                "hold. T-1189 gives him his place of work."),
    },
    "physician": {
        "kind": "census_bucket",
        "why": ("THE COUNT IS PRINTED, SO THE COUNT ORDERS. The census counts fourteen "
                "physicians and T-1418 filled that bucket against the register's standing "
                "rooms; the same rule as the lawyers, for the same reason."),
    },
    "surveyor": {
        "kind": "employment",
        "why": ("NO PREMISES, AND THE ONE PRINTED SURVEYOR SIGNS A COMMISSION AND NOT A "
                "HOUSE. Surveying is done in the field and the plat drawn where the "
                "surveyor lodges; the register's L. G. Curtiss prints as 'Deputy Surveyor "
                "of Cook County', which is an office held and not a shop kept, and no "
                "source gives this town a surveyor's office in 1835. The premises rulings "
                "rule the trade `no_fixed_premises` and this ticket leaves that standing."),
    },
    "laundress": {
        "kind": "employment",
        "why": ("THE RULING T-1404 DEFERRED TO T-1186, MADE HERE. Washing was taken in at "
                "the laundress's own dwelling or done at her employer's, and neither is a "
                "house of trade: a dwelling that takes in washing is a dwelling, and work "
                "done in another household's kitchen is done on premises the laundress does "
                "not keep. The role carries `premises: no_fixed_premises` and no house is "
                "raised. This does not touch rcb_fb_washing_and_ironing, which is an "
                "establishment T-1377's documented floor argues for directly and which "
                "stands on that argument and not on this one."),
    },
    "domestic": {
        "kind": "employment",
        "why": ("NO PREMISES. Domestic service is given in another household's house; the "
                "workplace link is T-1189's, which staffs every establishment with real "
                "persons, and nothing here raises a house. There is no `seamstress` in the "
                "resident layer's closed occupation vocabulary, so the parent's third "
                "female service trade has no row to rule on and is not invented one."),
    },
    "dentist": {
        "kind": "count_already_held",
        "why": ("THE STAND ARGUED BY T-1186 IS REFUSED, AND BY NAME. The register already "
                "prints this town's dentistry at the scene date — Wm. H. Kennicott, Surgeon "
                "Dentist, in two printings, a travelling dentist at the New York House and "
                "one unidentified — and the resident band drew NO head at the trade. So "
                "there is neither a count short nor a man to house: a stand raised here "
                "would be an establishment invented out of nothing, which is the one thing "
                "this programme refuses."),
    },
    "schoolteacher": {
        # NOT `deferred`, and T-1425's own fault check is why: T-1188 is a SPLIT parent and
        # a deferral to one is work nobody owns. The schools are not waiting on anything —
        # they are a COUNTED class, already ordered and already filled by the group that
        # owns the bucket, which is exactly what `census_bucket` says.
        "kind": "census_bucket",
        "why": ("THE COUNT IS PRINTED, SO THE COUNT ORDERS — and it is not this ticket's "
                "count. The December census counts seven schools, the order book holds that "
                "bucket for the civic, church, school and press group, and that group filled "
                "it with the keepers the register already names. A teaching establishment "
                "raised here would spend a count from outside the group that owns it."),
    },
    "music_teacher": {
        "kind": "employment",
        "why": ("NO PREMISES. Taught in the pupil's house or in a room hired for the term — "
                "the premises rulings' own words — so there is nothing kept to raise. The "
                "counted schools are T-1188's and a music master is not one of them."),
    },
}


# WHICH TABLE ADJUDICATES WHICH GROUP. Each trade quota above must be covered by a table
# here, and `trade_buckets` refuses a quota row the table does not call a `house_of_trade` —
# the table is the ruling and the quota follows it, never the reverse.
TRADE_ADJUDICATION = {
    "lodging_river_and_transport": {
        "ticket": "T-1424",
        "ticket_text": "T-1424, adjudication completed by T-1425",
        "rulings": RIVER_AND_TRANSPORT,
        "of": "river or transport",
        "ledger_key": "river_and_transport",
        "pier_works": True,
    },
    "professions_and_services": {
        "ticket": "T-1419",
        "ticket_text": "T-1419",
        "rulings": SERVICES,
        "of": "professional or service",
        "ledger_key": "services",
    },
}


# THE TRADES A CENSUS CLASS IS KEPT BY, in the resident layer's own occupation vocabulary.
# ONE ROW PER CLASS THIS TOOL HAS BEEN ASKED TO BUILD, and no further: a class whose group
# has not run yet is not guessed at here, because deciding that a `refectory_keeper` keeps a
# tavern rather than a store is T-1187's ruling to make and not T-1184's. A bucket whose
# class is missing from this table is refused by name, with the ticket that owes the row.
TRADE_CLASS = {
    "druggist": ["druggist"],
    "store": ["dry_goods_merchant", "grocer", "hardware_merchant", "merchant"],
    "book_store": [],
    # THE TWO CLASSES THE CENSUS COUNTS IN MEN take exactly one trade each, and that is
    # the point of them: "twenty-two lawyers" is twenty-two men, so one drawn head is one
    # office and the person count and the establishment count are the same number. A
    # second trade folded in here would break that identity.
    "lawyer": ["attorney"],
    "physician": ["physician"],
    # T-1185, THE MECHANICS' SHOPS. The book gives this ticket four classes and owes it
    # heads for two. `brewer` is the resident band's own word and the register's: the
    # Chicago Brewery's occupation line reads `brewer`. `silversmith_jeweller` is one shop
    # in this town and three words in two vocabularies — the register grades J. H. Mulford
    # `jeweller` and advertises "Watches", "Clocks", "Silver Ware" and "Indian silver work"
    # over one counter, and the resident band drew its head at `watchmaker`; all three
    # names are listed so a re-cut of either vocabulary still finds the shop.
    "brewery": ["brewer"],
    "silversmith_jeweller": ["jeweller", "silversmith", "watchmaker"],
    # AND TWO THE BOOK OWES NOTHING, which is a ruling and not an omission. The iron
    # foundry stands at its census target (Dart & Co., castings) and the tin and copper
    # trade stands ABOVE it — four printed houses against the December census's two. An
    # empty list here says the class is mapped and draws no head; a class MISSING from
    # this table is refused by name, and the two must not be confused.
    "iron_foundry": [],
    "tin_and_copper_manufactory": [],
}

# THE FACE A CLASS TAKES, by division, in the order a seeded deal reads them. From the
# register's own distribution of the 61 street-only businesses it prints, which puts the
# retail trades on South Water, Lake and Dearborn in the south division, on the Wolcott–
# Kinzie core and the North Water bank in the north, and on the Canal Street approach and
# West Water in the west. T-1195 writes the placement policy with its evidence and re-cuts
# this; until it does, the rule is this table and the record says so.
FACES = {
    "druggist": {
        "south": ["lake", "south_water", "dearborn"],
        "north": ["kinzie", "north_water"],
        "west": ["canal", "west_water"],
    },
    "store": {
        "south": ["south_water", "lake", "dearborn"],
        "north": ["kinzie", "north_water"],
        "west": ["canal", "west_water"],
    },
    "book_store": {
        "south": ["lake", "dearborn"],
        "north": ["kinzie"],
        "west": ["canal"],
    },
    # THE PROFESSIONS SIT WHERE THE REGISTER ALREADY PUTS THEM. Of the law offices the
    # register resolves a place for, South Water carries Collins & Caton, J. Curtiss and
    # J. D. Caton; Dearborn carries G. Spring, H. C. Bennett and both printings of S.
    # Abell; Lake carries Russell E. Heacock and John Dean Caton. Those three faces, in
    # that order of weight, are the south-division rule.
    "lawyer": {
        "south": ["south_water", "dearborn", "lake"],
        "north": ["kinzie", "north_water"],
        "west": ["canal", "west_water"],
    },
    # AND BOTH PLACED PHYSICIANS ARE ON LAKE STREET: Dr. J. H. Barnard against the New
    # York House and Dr. W. G. Austin "on Lake Street, near the post office" (the American
    # of 8 August 1835). Lake leads, and the two business streets either side of it follow
    # it rather than a rule of their own.
    "physician": {
        "south": ["lake", "south_water", "dearborn"],
        "north": ["kinzie", "north_water"],
        "west": ["canal", "west_water"],
    },
    # A BREWERY IS NOT A SHOP FRONT. It wants water, fuel and room for a yard, and the
    # town's one attested brewery is a river house, not a Lake Street one. It takes the
    # working banks — the North Water bank in the north division, which is where the
    # register's heavy trades sit, the river front and the Market Street branch face in
    # the south, West Water in the west — and never a retail street.
    "brewery": {
        "south": ["south_water", "market"],
        "north": ["north_water", "kinzie"],
        "west": ["west_water", "canal"],
    },
    # The silversmith and jeweller is a retail front: J. H. Mulford, the one house of the
    # class the register prints, advertises from South Water Street.
    "silversmith_jeweller": {
        "south": ["south_water", "lake", "dearborn"],
        "north": ["kinzie", "north_water"],
        "west": ["canal", "west_water"],
    },
}

# THE PERIOD FORMS, each one attested in the register, with the attested house that carries
# it named beside it so a reader can check the form against a printing. `docs/RESEARCH/
# business-naming-1835.md` is the argument; this is the half a program can run.
STYLES = {
    "druggist": {
        "forms": [
            ("{initial}. {surname}, {goods}",
             "the form 'Frederick Thomas, drugs and paints' prints, with the forename cut to "
             "an initial as 'J. B. Brown, Dearborn Street grocery' and 'S. Foot' do"),
            ("{given} {surname}, {goods}",
             "the form 'Frederick Thomas, drugs and paints' and 'William F. Lyon, Wholesale "
             "Grocery Store' print in full"),
        ],
        "goods": [
            ("drugs and medicines", "Philo Carpenter's own trade line in the register"),
            ("drugs, medicines and dye stuffs",
             "the goods line of Frederick Thomas and Philo Carpenter, cut to the three heads "
             "both of them advertise"),
        ],
        "trade": "druggist and apothecary",
        "occupation": "druggist",
    },
    "store": {
        "forms": [
            ("{initial}. {surname}, {goods}",
             "the form 'B. Jones, grocery and provision store' prints"),
            ("{given} {surname}, {goods}",
             "the form 'William F. Lyon, Wholesale Grocery Store' prints"),
        ],
        "goods": [
            ("dry goods, groceries and hardware",
             "the goods line P. Pruyne & Co. and Clark, Filer & Co. advertise"),
            ("grocery and provision store", "B. Jones's own trade line in the register"),
        ],
        "trade": "store",
        "occupation": None,
    },
    "lawyer": {
        "forms": [
            ("{initial}. {surname}, {goods}",
             "the form 'J. Curtiss, Attorney and Counsellor at Law', 'R. Stewart, attorney' "
             "and 'S. Abell, attorney and counsellor' print — an initial, the surname, and "
             "the practice's own line"),
            ("{given} {surname}, {goods}",
             "the form 'Ebenezer S. More, attorney at law' prints in full"),
        ],
        # EVERY LINE HERE IS A LINE THE REGISTER PRINTS, verbatim, and there are three of
        # them because the town's own notices carry three. Nothing is composed.
        "goods": [
            ("attorney at law",
             "the trade line of Ebenezer S. More and of R. Stewart in the register"),
            ("attorney and counsellor at law",
             "the trade line of Edward W. Casey and James Grant"),
            ("attorney and counsellor at law, and solicitor in chancery",
             "the fullest of the three, and the commonest: G. Spring, H. C. Bennett, J. "
             "Curtiss, Henry Moore and John Dean Caton all print it"),
        ],
        "trade": "attorney and counsellor at law",
        "occupation": "attorney",
    },
    "physician": {
        # THE DOCTOR'S TITLE IS THE FIRM STYLE, and both of the register's physicians carry
        # it: 'Dr. J. H. Barnard' sets the title, initials and surname and no trade at all,
        # and 'Dr. W. G. Austin, botanic physician' sets the same with a line after it.
        "forms": [
            ("Dr. {initial}. {surname}",
             "the form 'Dr. J. H. Barnard' prints — the title, the initials and the surname, "
             "and no trade line"),
            ("Dr. {initial}. {surname}, {goods}",
             "the form 'Dr. W. G. Austin, botanic physician' prints — the same, with the "
             "practice's line after it"),
        ],
        # ONE LINE, AND DELIBERATELY. Austin's own line names the BOTANIC system, which is a
        # medical school a reconstructed man may not be dealt into: the register knows what
        # Austin practised because Austin advertised it, and nothing knows it of a man
        # nobody wrote down. 'Physician' is the register's other printed line and it claims
        # only the trade the census counted.
        "goods": [
            ("physician", "the trade line the register prints under Dr. J. H. Barnard"),
        ],
        "trade": "physician",
        "occupation": "physician",
    },
    "brewery": {
        "forms": [
            ("{initial}. {surname}, {goods}",
             "the initial-and-surname signature is the commonest in the corpus — "
             "'B. Jones, grocery and provision store', 'S. B. Cobb, saddle, harness and "
             "trunk manufactory'"),
            ("{given} {surname}, {goods}",
             "the forename in full is the minority form and is attested — "
             "'William F. Lyon, Wholesale Grocery Store', 'Frederick Thomas, drugs and "
             "paints'"),
        ],
        "goods": [
            ("brewery",
             "the only word the corpus prints for this class: the register carries one "
             "brewery, 'the Chicago Brewery', with no goods line under it, so the trade "
             "word stands alone rather than a list being composed for it"),
        ],
        "trade": "brewing",
        "occupation": "brewer",
        # THE TIGHTER BOUND, STATED ON THE RECORD RATHER THAN ACTED ON.
        "caveat": (
            "A TIGHTER COUNT STANDS UNAPPLIED, AND THIS RECORD CARRIES IT. The book takes "
            "its target from the December 1835 State census, which prints two breweries. "
            "But the Chicago American of 15 August 1835 takes stock of the town six weeks "
            "AFTER the scene date and counts 'one brewery, one furnace (just going up)' — "
            "one, where December counts two. If the American is right for 1 July 1835 then "
            "the town's second brewery arrived in the autumn and this house does not stand "
            "at the scene date at all. That is the Sept-Dec 1835 crosswalk's ruling to make "
            "and it has not made it: this bucket reads `compared_by_the_crosswalk: true` "
            "and `crosswalk_note: null`. The house therefore stands on the book's quota, "
            "with the count that would retire it printed here; a crosswalk that rules the "
            "American in re-cuts the bucket and --build withdraws this record, which is "
            "the only way it may ever go."),
    },
    "silversmith_jeweller": {
        "forms": [
            ("{initial}. {surname}, {goods}",
             "the initial-and-surname signature is the commonest in the corpus, and the "
             "one attested house of this class signs by surname — 'J. H. Mulford'"),
            ("{given} {surname}, {goods}",
             "the forename in full is attested — 'Frederick Thomas, drugs and paints', "
             "'William F. Lyon, Wholesale Grocery Store'"),
        ],
        "goods": [
            ("watches, jewelry, engravings and fancy goods",
             "J. H. Mulford's own trade line in the register — the one attested house of "
             "the class, and the only goods line the corpus prints for it"),
        ],
        "trade": "watches, jewelry, engravings and fancy goods",
        "occupation": "jeweller",
    },
}


# ------------------------------------------------------------------------- the plumbing

def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def draw(seed, options):
    """The seed rule of the reconstruction programme, unchanged: a STRING a reader can
    retype, hashed with blake2s and read big-endian, indexing a list nobody reorders."""
    digest = hashlib.blake2s(seed.encode("utf-8"), digest_size=8).digest()
    return options[int.from_bytes(digest, "big") % len(options)]


def order_book_buckets(ticket, book=None):
    """The business rows of the order book this ticket owns, in the book's own order."""
    book = book or load_json(ORDER_BOOK)
    family = next(f for f in book["bucket_families"] if f["key"] == "businesses")
    return [b for b in family["buckets"] if b.get("owning_ticket") == ticket]


def trade_heads(root=None):
    """Every reconstructed trade head the resident band drew, by trade, in slot order."""
    root = Path(root or TRADE_HOUSEHOLDS)
    heads = {}
    for path in sorted(root.glob("*.json")):
        doc = load_json(path)
        block = doc.get("trade_household") or {}
        head = next((p for p in doc.get("persons", []) if p.get("id") == doc.get("head")), None)
        if not block.get("trade") or head is None:
            continue
        heads.setdefault(block["trade"], []).append({
            "household_id": doc["id"],
            "person_id": head["id"],
            "name": head["name"],
            "division": doc["division"],
            "slot": block["slot"],
            "trade": block["trade"],
            "community": (head.get("reconstruction") or {}).get("community"),
        })
    for rows in heads.values():
        rows.sort(key=lambda r: r["slot"])
    return heads


def attested_strings(businesses_dir=None):
    """Every firm style, house name and proprietor name the register already prints —
    the collision set an invention may not walk into.

    A DRAWN HAND IS NOT A PRINTED NAME (T-1462). Since the reconstructed seating was
    laid onto the compiled records, `staff` carries 124 rows this project drew itself,
    each at `reconstructed` tier — and they are the same people the trade households
    are built out of. Counting them here made the collision set eat its own tail: Almira
    Sawyer was refused a dressmaking shop of her own because a pass had just seated
    Almira Sawyer in somebody else's. The set is what a SOURCE prints, so a row this
    project reconstructed is not part of it, and the tier is how the record says which
    it is.
    """
    root = Path(businesses_dir or (DATA / "businesses"))
    names, people = set(), set()
    for path in sorted(root.glob("biz_*.json")):
        doc = load_json(path)
        names.add(doc["name"].strip().lower())
        for style in doc.get("firm_styles") or []:
            names.add(style.strip().lower())
        for field in ("proprietors", "partners", "staff"):
            for person in doc.get(field) or []:
                if person.get("tier") == "reconstructed":
                    continue
                people.add((person.get("name") or "").strip().lower())
    return names, people


# ------------------------------------------------------------------- building a record

def initials(name):
    parts = [p for p in name.split() if p]
    return parts[0], parts[-1]


def firm_style(spec, head, seed):
    given, surname = initials(head["name"])
    form, form_basis = draw(seed + ":firm_form", spec["forms"])
    goods, goods_basis = draw(seed + ":goods_line", spec["goods"])
    name = form.format(initial=given[0], given=given, surname=surname, goods=goods)
    return name, goods, ("The style is dealt on the seed printed beside it from the period "
                         "forms the register itself carries: %s. The goods line is %s."
                         % (form_basis, goods_basis))


def record_for(group, bucket, head, ordinal, communities, streets):
    cls = bucket["axes"]["class"]
    spec = STYLES[cls]
    slot = "%s:%s:%03d" % (group, bucket["key"], ordinal)
    name, goods, style_basis = firm_style(spec, head, slot)
    _, surname = initials(head["name"])
    faces = FACES[cls][head["division"]]
    face = draw(slot + ":street_face", faces)

    # A CLASS MAY CARRY A COUNT THAT ARGUES AGAINST ITS OWN BUCKET, and where it does the
    # record says so in its own basis rather than in a document beside it: a reader holding
    # the card holds the objection to it. `caveat` is optional and a class without one is
    # written exactly as it was before this key existed.
    basis_note = ("%s. The book leaves %d of this class to reconstruct and this is one of "
                  "them. %s" % (bucket["basis"].rstrip("."), bucket["to_reconstruct"],
                                style_basis))
    if spec.get("caveat"):
        basis_note += " " + spec["caveat"]

    proprietor = {
        "name": head["name"],
        "person_id": head["person_id"],
        "register_person_id": None,
        "role": "proprietor",
        "from": None,
        "to": None,
        "tier": "reconstructed",
        "basis": (
            "ADOPTED, NOT MINTED. %s is the reconstructed trade head the resident band's "
            "`trade_households` stage drew at %s in the %s division (slot %s), and that card "
            "says itself that the business band adopts these heads rather than minting its "
            "own. One quota, filled once: this house is the establishment that head keeps."
            % (head["name"], head["trade"], head["division"], head["slot"])),
        "source_id": None,
        "claim_ids": [],
    }

    record = {
        "id": "rcb_%s_%s" % (surname.lower().replace("'", "").replace(".", ""), cls),
        "register_id": None,
        "name": name,
        "provenance": "reconstructed",
        "type": [cls],
        "trade": spec["trade"],
        "occupation": spec["occupation"],
        "goods": [goods],
        "firm_styles": [],
        "proprietors": [proprietor],
        "partners": [],
        "staff": [],
        "locations": [{
            "kind": "street_only",
            "structure_id": None,
            "street_id": face,
            "face": None,
            "primary": True,
            "from": None,
            "to": None,
            "tier": "reconstructed",
            "basis": (
                "A FACE, NOT A PREMISES. The placement rule for a %s kept by a %s-division "
                "household deals this house onto %s; the face is drawn on the seed printed in "
                "`reconstruction.seed` from the faces that rule allows, and no lot, roof or "
                "coordinate is claimed. T-1195 writes the placement policy with its evidence "
                "and T-1199 seats this house on the lot grid."
                % (cls, head["division"], streets.get(face, face))),
            "limit_reason": (
                "No source places this house, because no source names it: it exists because "
                "the December 1835 State census counts more of its class than the register "
                "holds. The street is the reconstruction's own deal and stops there."),
        }],
        "dates": {
            "opened": None,
            "closed": None,
            "precision": "unbounded",
            "tier": "reconstructed",
            "basis": (
                "NOTHING DATES THIS HOUSE. The census that orders it was taken in December "
                "1835 and counts a standing trade, not an opening; the record claims that the "
                "house was trading on %s and nothing about either end." % SCENE_DATE),
        },
        "evidence": {},
        "present_at_scene_date": True,
        "exclusion": None,
        "exclusion_note": None,
        "proprietor_community": derive_proprietor_community(
            [proprietor], [], communities),
        "customers": [],
        "sources": [],
        "claim_ids": [],
        "liberties": {"survival_required": False, "backdating_required": False},
        "review_required": False,
        "replaceable_by": (
            "A register, directory or deed naming a real house of this class in the %s "
            "division in 1835 — that house takes this slot and this record is withdrawn."
            % head["division"]),
        "reconstruction": {
            "programme": PROGRAMME,
            "group": group,
            "ticket": GROUPS[group]["ticket"],
            "bucket": bucket["key"],
            "slot": slot,
            "seed": slot,
            "basis": {
                "kind": "model",
                "id": "1835_reconstruction_order_book",
                "note": basis_note,
            },
            "withdrawn_if": (
                "a source naming a real house of this class, or a re-cut of the order book "
                "that no longer orders this bucket; the retirement runs through --build, "
                "never by hand"),
        },
    }
    return record


# ------------------------------------------------------- the roofs, and who keeps them

def lodging_places(model=None):
    """Every lodging place the model holds, with its beds — the model's own order."""
    model = model or load_json(LODGING_MODEL)
    return list(model["places"])


def roof_keepers(root=None):
    """`{place: keeper}` for the lodging households the lodgers stage wrote a head on.

    Read off the households rather than off that stage's ledger, for the reason the
    liberty counter reads the business records rather than the business index: the
    ledger is a derivation of these cards, and adopting a person out of a derivation
    would be adopting a summary of them.
    """
    root = Path(root or LODGERS)
    out = {}
    for path in sorted(root.glob("*.json")):
        doc = load_json(path)
        block = doc.get("lodging_household") or {}
        head = next((p for p in doc.get("persons", []) if p.get("id") == doc.get("head")), None)
        if not block.get("place") or head is None:
            continue
        out[block["place"]] = {
            "household_id": doc["id"],
            "person_id": head["id"],
            "name": head["name"],
            "sex": head.get("sex"),
            "division": doc["division"],
            "community": (head.get("reconstruction") or {}).get("community"),
        }
    return out


def roof_buckets(group, model=None, keepers=None):
    """The standing reconstructed lodging roofs this group owes a firm, by division.

    Shaped like an order-book bucket so the build loop reads one list, and carrying its
    places so the record can name the roof that bought it. A roof whose keeper the lodgers
    stage never named is NOT ordered: this tool adopts a keeper and never mints one, and a
    house with nobody to keep it is a shortfall stated rather than a person invented.
    """
    spec = ROOF_QUOTA.get(group)
    if spec is None:
        return []
    keepers = keepers if keepers is not None else roof_keepers()
    by_division, unkept = {}, []
    for place in lodging_places(model):
        if place["class"] != spec["lodging_class"] or place["standing"] != "reconstructed":
            continue
        keeper = keepers.get(place["id"])
        if keeper is None:
            unkept.append(place["id"])
            continue
        by_division.setdefault(keeper["division"], []).append(dict(place, keeper=keeper))
    buckets = []
    for division in sorted(by_division):
        places = by_division[division]
        buckets.append({
            "key": "lodging/%s/%s" % (spec["lodging_class"], division),
            "axes": {"class": spec["lodging_class"], "division": division},
            "to_reconstruct": len(places),
            "owning_ticket": spec["ticket"],
            "places": places,
            "unkept": sorted(unkept),
            "basis": ("the lodging model gives %d standing %s roof(s) in the %s division "
                      "their beds and the lodgers stage named a keeper for each"
                      % (len(places), spec["lodging_class"].replace("_", " "), division)),
        })
    return buckets


def roof_style(place, seed):
    given, surname = initials(place["keeper"]["name"])
    form, form_basis = draw(seed + ":firm_form", ROOF_STYLES[place["class"]]["forms"])
    return form.format(initial=given[0], given=given, surname=surname), form_basis


def record_for_roof(group, bucket, place, ordinal, communities):
    spec = ROOF_QUOTA[group]
    keeper = place["keeper"]
    slot = "%s:%s:%03d" % (group, bucket["key"], ordinal)
    name, style_basis = roof_style(place, slot)
    _, surname = initials(keeper["name"])

    proprietor = {
        "name": keeper["name"],
        "person_id": keeper["person_id"],
        "register_person_id": None,
        "role": "proprietor",
        "from": None,
        "to": None,
        "tier": "reconstructed",
        "basis": (
            "ADOPTED, NOT MINTED. %s is the keeper the lodgers stage (T-1371) drew for this "
            "house and printed in data/reconstruction/1835_lodgers_seated.json § keepers; "
            "that card reads the trade off the building it stands in and heads %s. One "
            "quota, filled once: this record is the house they keep, not a second person."
            % (keeper["name"], keeper["household_id"])),
        "source_id": None,
        "claim_ids": [],
    }

    record = {
        "id": "rcb_%s_boarding_house" % surname.lower().replace("'", "").replace(".", ""),
        "register_id": None,
        "name": name,
        "provenance": "reconstructed",
        "type": [spec["type"]],
        "trade": spec["trade"],
        "occupation": spec["occupation"],
        "goods": [],
        "firm_styles": [],
        "proprietors": [proprietor],
        "partners": [],
        "staff": [],
        "locations": [{
            "kind": "premises",
            "structure_id": place["id"],
            "street_id": None,
            "face": None,
            "primary": True,
            "from": None,
            "to": None,
            "tier": "reconstructed",
            "basis": (
                "THE ROOF IS THE PREMISES, and it is the one thing here that was not dealt. "
                "This firm exists because %s stands in data/structures/ with %d ordinary-"
                "night beds in it; the building came first and the house of trade is what "
                "the building was missing. No street is claimed beyond the one the roof "
                "already stands on, and no coordinate is written here at all."
                % (place["id"], place["beds_ordinary"])),
            "limit_reason": None,
        }],
        "dates": {
            "opened": None,
            "closed": None,
            "precision": "unbounded",
            "tier": "reconstructed",
            "basis": (
                "NOTHING DATES THIS HOUSE. The roof it occupies is an anonymous count-unit "
                "dated to the year and to nothing narrower, and a keeping is not an "
                "opening; the record claims that the house was letting beds on %s and "
                "nothing about either end." % SCENE_DATE),
        },
        "evidence": {},
        "present_at_scene_date": True,
        "exclusion": None,
        "exclusion_note": None,
        "proprietor_community": derive_proprietor_community([proprietor], [], communities),
        "customers": [],
        "sources": [],
        "claim_ids": [],
        "liberties": {"survival_required": False, "backdating_required": False},
        "review_required": False,
        "replaceable_by": (
            "A source naming whoever kept a boarding house in the %s division in 1835 — "
            "that keeper takes this roof and this record is withdrawn with the drawn one."
            % bucket["axes"]["division"]),
        "reconstruction": {
            "programme": PROGRAMME,
            "group": group,
            "ticket": spec["ticket"],
            "roof": {
                "structure_id": place["id"],
                "class": place["class"],
                "beds_ordinary": place["beds_ordinary"],
                "keeper_person_id": keeper["person_id"],
                "keeper_household_id": keeper["household_id"],
                "note": (
                    "A STANDING ROOF, NOT A SHORTFALL. The December 1835 State census "
                    "enumerates taverns and never boarding houses, so the order book holds "
                    "no bucket of this class to point at and no count of it is short. What "
                    "is committed is the building: %s stands, the lodging model apportioned "
                    "it %d ordinary-night beds out of a bracket the town model owns, and "
                    "the lodgers stage put people in them and named %s their keeper. The "
                    "firm is what was missing, and it is withdrawn with the roof."
                    % (place["id"], place["beds_ordinary"], keeper["name"])),
            },
            "seed": slot,
            "basis": {
                "kind": "model",
                "id": "1835_lodging_model",
                "note": ("%s. %s. The style is dealt on the seed printed beside it from the "
                         "keeper's possessive, form 5 of the naming guide: %s. No honorific "
                         "is dealt, because nothing on this keeper's card says whether they "
                         "were married, widowed or single and a sign that said so would be "
                         "inventing it."
                         % (bucket["basis"].rstrip("."),
                            ("the keeper is a woman" if keeper["sex"] == "female"
                             else "the keeper is a man" if keeper["sex"] == "male"
                             else "the keeper's sex is not stated"),
                            style_basis)),
            },
            "withdrawn_if": (
                "the retirement of the roof itself, a re-cut lodging model that gives this "
                "house no beds, or a source naming whoever really kept it; the retirement "
                "runs through --build, never by hand"),
        },
    }
    return record


# --------------------------------------------- the trades, and the houses they name

def census_enumerated_classes(book=None):
    """The classes the order book carries a bucket for — the ones a count can be short of.

    Read off the book rather than listed here, so a re-cut that adds a class moves this
    refusal with it. A reconstructed house typed into one of these spends a printed count.
    """
    book = book or load_json(ORDER_BOOK)
    family = next(f for f in book["bucket_families"] if f["key"] == "businesses")
    return {b["axes"]["class"] for b in family["buckets"]}


def trade_buckets(group, heads=None, book=None):
    """The reconstructed trade heads this group owes a house, by trade and division.

    Shaped like an order-book bucket so the build loop reads one list, and carrying its
    heads so the record can name the man who bought it. The refusals are here rather than
    in the record writer because a quota that cannot be stated must not be half-built.
    """
    spec = TRADE_QUOTA.get(group)
    if spec is None:
        return []
    heads = heads if heads is not None else trade_heads()
    enumerated = census_enumerated_classes(book)
    buckets = []
    for trade in sorted(spec["trades"]):
        row = spec["trades"][trade]
        house = row["house"]
        if row["type"] in enumerated:
            raise SystemExit(
                "the trade quota types a %s as %r and the order book enumerates that class: "
                "a reconstructed house of it would spend a printed count the register may "
                "already hold. A trade the census never counted takes `other`."
                % (trade, row["type"]))
        if house not in TRADE_STYLES or house not in TRADE_FACES:
            raise SystemExit(
                "the trade quota orders a %s and this tool carries no style or face row for "
                "%r. Add them to TRADE_STYLES and TRADE_FACES with the register printings "
                "that argue them." % (trade, house))
        adjudication = TRADE_ADJUDICATION[group]["rulings"]
        if adjudication.get(trade, {}).get("kind") != "house_of_trade":
            raise SystemExit(
                "the trade quota orders a house for %s and the adjudication table does not "
                "call that trade a house_of_trade. The table is the ruling; the quota "
                "follows it." % trade)
        by_division = {}
        for head in heads.get(trade, []):
            by_division.setdefault(head["division"], []).append(head)
        for division in sorted(by_division):
            rows = by_division[division]
            buckets.append({
                "key": "trade/%s/%s" % (house, division),
                "axes": {"class": house, "division": division},
                "to_reconstruct": len(rows),
                "owning_ticket": spec["ticket"],
                "trade": trade,
                "heads": rows,
                "basis": ("the resident band drew %d head(s) at %s in the %s division and %s"
                          % (len(rows), trade.replace("_", " "), division, row["basis"])),
            })
    return buckets


def trade_style(house, head, seed):
    given, surname = initials(head["name"])
    spec = TRADE_STYLES[house]
    form, form_basis = draw(seed + ":firm_form", spec["forms"])
    goods, goods_basis = draw(seed + ":goods_line", spec["goods"])
    name = form.format(initial=given[0], given=given, surname=surname, goods=goods)
    return name, goods, ("The style is dealt on the seed printed beside it from the period "
                         "forms the register itself carries: %s. The goods line is %s."
                         % (form_basis, goods_basis))


def house_label(row, house):
    """What a house of trade is CALLED in prose. The key is an identifier and reads like
    one — `barbers_shop` unsplits to "barbers shop" — so a row may carry its own words."""
    return row.get("label") or house.replace("_", " ")


def record_for_trade(group, bucket, head, ordinal, communities, streets):
    spec = TRADE_QUOTA[group]
    row = spec["trades"][bucket["trade"]]
    house = bucket["axes"]["class"]
    label = house_label(row, house)
    slot = "%s:%s:%03d" % (group, bucket["key"], ordinal)
    name, goods, style_basis = trade_style(house, head, slot)
    _, surname = initials(head["name"])
    face = draw(slot + ":street_face", TRADE_FACES[house][head["division"]])

    proprietor = {
        "name": head["name"],
        "person_id": head["person_id"],
        "register_person_id": None,
        "role": "proprietor",
        "from": None,
        "to": None,
        "tier": "reconstructed",
        "basis": (
            "ADOPTED, NOT MINTED. %s is the reconstructed trade head the resident band's "
            "`trade_households` stage drew at %s in the %s division (slot %s), and that card "
            "says itself that the business band adopts these heads rather than minting its "
            "own. Here the head is not merely the proprietor of the house — the head IS what "
            "bought it, because no count of this class was ever printed to be short of."
            % (head["name"], head["trade"], head["division"], head["slot"])),
        "source_id": None,
        "claim_ids": [],
    }

    return {
        "id": "rcb_%s_%s" % (surname.lower().replace("'", "").replace(".", ""), house),
        "register_id": None,
        "name": name,
        "provenance": "reconstructed",
        "type": [row["type"]],
        "trade": row["trade"],
        "occupation": row["occupation"],
        "goods": [goods],
        "firm_styles": [],
        "proprietors": [proprietor],
        "partners": [],
        "staff": [],
        "locations": [{
            "kind": "street_only",
            "structure_id": None,
            "street_id": face,
            "face": None,
            "primary": True,
            "from": None,
            "to": None,
            "tier": "reconstructed",
            "basis": (
                "A FACE, NOT A PREMISES. The placement rule for a %s kept by a %s-division "
                "household deals this house onto %s; the face is drawn on the seed printed "
                "in `reconstruction.seed` from the faces that rule allows, and no lot, roof "
                "or coordinate is claimed. T-1195 writes the placement policy with its "
                "evidence and T-1199 seats this house on the lot grid."
                % (label, head["division"], streets.get(face, face))),
            "limit_reason": (
                "No source places this house, because no source names it: it exists because "
                "the resident band drew a %s the town was short of, and the trade names the "
                "house he keeps. The street is the reconstruction's own deal and stops "
                "there." % bucket["trade"].replace("_", " ")),
        }],
        "dates": {
            "opened": None,
            "closed": None,
            "precision": "unbounded",
            "tier": "reconstructed",
            "basis": (
                "NOTHING DATES THIS HOUSE. The head who keeps it is ordered onto the scene "
                "date and to nothing narrower, and a keeping is not an opening; the record "
                "claims that the house was trading on %s and nothing about either end."
                % SCENE_DATE),
        },
        "evidence": {},
        "present_at_scene_date": True,
        "exclusion": None,
        "exclusion_note": None,
        "proprietor_community": derive_proprietor_community([proprietor], [], communities),
        "customers": [],
        "sources": [],
        "claim_ids": [],
        "liberties": {"survival_required": False, "backdating_required": False},
        "review_required": False,
        "replaceable_by": (
            "A register, directory or deed naming a real %s in the %s division in 1835 — "
            "that house takes this slot and this record is withdrawn with the head."
            % (label, head["division"])),
        "reconstruction": {
            "programme": PROGRAMME,
            "group": group,
            "ticket": spec["ticket"],
            "trade_head": {
                "person_id": head["person_id"],
                "household_id": head["household_id"],
                "trade": head["trade"],
                "head_slot": head["slot"],
                "note": ("A TRADE HEAD, NOT A SHORTFALL AND NOT A ROOF. The December 1835 "
                         "State census's eighteen lines never reach this class, so the order "
                         "book holds no bucket to point at and no count of it can be short; "
                         "and nothing in data/structures/ is a %s, so there is no committed "
                         "building to buy the firm either. What IS committed is the man: the "
                         "resident band drew %s at %s because the 1839 trade table says the "
                         "town was short of the trade, and %s. The house is withdrawn with "
                         "the head."
                         % (label, head["name"],
                            head["trade"].replace("_", " "), row["basis"])),
            },
            "seed": slot,
            "basis": {
                "kind": "rule",
                "id": "the_trade_names_the_house",
                "note": "%s. %s" % (bucket["basis"].rstrip("."), style_basis),
            },
            "withdrawn_if": (
                "the retirement of the head himself, a re-cut of the order book that no "
                "longer orders his person bucket, or a source naming a real house of this "
                "class; the retirement runs through --build, never by hand"),
        },
    }


def ticket_state(number):
    """The state a ticket file carries, or None if the tree holds no such ticket."""
    for path in (ROOT / "tickets").glob("%s-*.md" % number):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("state:"):
                return line.split(":", 1)[1].strip()
    return None


def adjudication_faults(table):
    """THE THREE THINGS AN ADJUDICATED ROW MAY NOT DO, checked rather than trusted.

    T-1425's own history is the argument for this. T-1424 deferred two heads to T-1425
    and stated a reason — that no source in this corpus prints the port of Chicago's
    arrivals and clearances — which was already false when it was written: the reading
    had been committed since T-1372. Nothing re-read it, because a deferral was prose
    and prose is not checked. These three are what CAN be checked:

    1. `kind` is one of RIVER_KINDS, so a new ruling is declared and not typed.
    2. A `deferred` row names a ticket that is STILL OPEN. A deferral to a ticket that
       has closed is work nobody owns, and it reads as a reason in the published ledger.
    3. A ruling that leans on a committed reading names a file the tree still holds. The
       `commands_a_vessel` ruling stands on the marine list; if that file goes, the
       ruling is standing on nothing and must be re-argued rather than quietly kept.
    """
    faults = []
    for row in table["rows"]:
        if row["kind"] not in RIVER_KINDS:
            faults.append("%s: adjudicated `%s`, which is not one of %r"
                          % (row["trade"], row["kind"], list(RIVER_KINDS)))
        if row["kind"] == "deferred":
            state = ticket_state(row.get("deferred_to") or "")
            if state is None:
                faults.append("%s: deferred to '%s', which is not a ticket in this tree"
                              % (row["trade"], row.get("deferred_to")))
            elif state in ("done", "split", "blocked"):
                faults.append("%s: deferred to %s, which is `%s` — a deferral to a closed "
                              "ticket is work nobody owns"
                              % (row["trade"], row["deferred_to"], state))
    # CHECKS 3 AND 4 ARE ABOUT WHAT A TABLE CARRIES, so they ask the table rather than
    # assuming the river's. A group whose rulings never reach a hull stands on no marine
    # list, and a group nobody asked a pier-works question of owes no refusal.
    if any(row["kind"] == "commands_a_vessel" for row in table["rows"]):
        if not (VESSELS_IN_PORT.exists()
                and (load_json(VESSELS_IN_PORT).get("vessels") or [])):
            faults.append("the `commands_a_vessel` ruling stands on the marine list at %s, "
                          "which is gone or enters no hull; re-argue the ruling rather than "
                          "keeping it" % VESSELS_IN_PORT.relative_to(ROOT))
    if "the_pier_works" in table:
        works = table.get("the_pier_works") or {}
        for key in ("why", "nearest_thing_the_tree_holds", "replaceable_by"):
            if not (works.get(key) or "").strip():
                faults.append("the pier works are refused with no `%s` printed" % key)
    return faults


def trade_adjudication_table(group):
    """EVERY HEAD AT ONE OF THIS GROUP'S TRADES, AND WHAT BECAME OF IT — the acceptance of
    T-1424 for the river and transport trades and of T-1419 for the services.

    Read off the heads and off the records on disk, for the reason lodging_table reads off
    disk: --build writes every record before it writes this ledger, so disk is the complete
    picture and one group's build is not. A trade in the table that the resident band drew
    no head at still prints, with an empty list, because the ruling stands whether or not
    anybody was drawn into it.
    """
    spec = TRADE_ADJUDICATION[group]
    rulings = spec["rulings"]
    heads = trade_heads()
    kept = {}
    for path in sorted(list((DATA / "businesses").glob("biz_*.json"))
                       + list(AUTHORED.glob("*.json"))):
        doc = load_json(path)
        for person in doc.get("proprietors") or []:
            if person.get("person_id"):
                kept.setdefault(person["person_id"], doc["id"])
    rows, unhoused = [], 0
    for trade in sorted(rulings):
        ruling = rulings[trade]
        people = []
        for head in heads.get(trade, []):
            firm = kept.get(head["person_id"])
            if ruling["kind"] == "house_of_trade" and not firm:
                unhoused += 1
            people.append({
                "person_id": head["person_id"],
                "name": head["name"],
                "division": head["division"],
                "head_slot": head["slot"],
                "firm": firm,
            })
        rows.append({
            "trade": trade,
            "kind": ruling["kind"],
            "deferred_to": ruling.get("ticket"),
            "heads": len(people),
            "why": ruling["why"],
            "people": people,
        })
    return {
        "_doc": ("EVERY RECONSTRUCTED HEAD AT A %s TRADE, and the house of "
                 "trade behind it or the reason there is none. `kind` says which sort of "
                 "absence a headless trade is: `house_of_trade` this programme builds, "
                 "`census_bucket` the order book counts and another ticket fills, "
                 "`count_already_held` the register already over-holds, `employment` has no "
                 "premises to keep, `commands_a_vessel` keeps a hull and not a house, "
                 "`contract_not_premises` holds a route and not a stand, `deferred` waits "
                 "on the ticket named. No head is passed over in silence — that is what "
                 "this table is for." % spec["of"].upper()),
        "ticket": spec["ticket_text"],
        "trades": len(rows),
        "heads": sum(r["heads"] for r in rows),
        "heads_this_programme_owes_a_house": unhoused,
        "heads_still_deferred": sum(r["heads"] for r in rows if r["kind"] == "deferred"),
        "rows": rows,
        # THE ASK NO ROW CAN CARRY. T-1409 wanted the pier-works contractor and his gang
        # beside the vessels; no head stands at the works, so the trade rows are silent
        # about them and the silence would read as an omission. This is the refusal, with
        # the document that would retire it named. It is the RIVER table's and no other's:
        # a group with no such ask carries no such key rather than an empty one.
        **({"the_pier_works": PIER_WORKS} if spec.get("pier_works") else {}),
    }


def river_and_transport_table():
    """T-1424's table, by its own name."""
    return trade_adjudication_table("lodging_river_and_transport")


# ------------------------------------------------------------------------ build / check

def build_group(group, communities=None, streets=None, heads=None, book=None):
    """Every record this group's order-book rows call for, in the book's own order."""
    communities = communities if communities is not None else person_communities()
    streets = streets if streets is not None else {
        s["id"]: s.get("name_1835") or s["id"] for s in load_json(STREETS)["streets"]}
    heads = heads if heads is not None else trade_heads()
    records, shortfalls = [], []
    taken = set()
    for bucket in order_book_buckets(GROUPS[group]["ticket"], book):
        owed = bucket["to_reconstruct"]
        if owed <= 0:
            continue
        cls = bucket["axes"]["class"]
        if cls not in TRADE_CLASS or cls not in STYLES:
            raise SystemExit(
                "the order book orders %d of class %r for %s and this tool carries no trade "
                "row or style for it. Add them to TRADE_CLASS and STYLES with the argument "
                "for the mapping, in the ticket that owns the bucket (%s) — a class guessed "
                "at by another group's ticket is a ruling made in the wrong place."
                % (owed, cls, group, bucket["owning_ticket"]))
        candidates = [h for trade in TRADE_CLASS[cls] for h in heads.get(trade, [])]
        candidates = sorted((h for h in candidates if h["person_id"] not in taken),
                            key=lambda h: h["slot"])
        if len(candidates) < owed:
            shortfalls.append((bucket["key"], owed, len(candidates)))
            continue
        for ordinal, head in enumerate(candidates[:owed], start=1):
            taken.add(head["person_id"])
            records.append(record_for(group, bucket, head, ordinal, communities, streets))
    if shortfalls:
        raise SystemExit(
            "the resident band has not drawn enough trade heads for %s:\n%s\n"
            "This tool ADOPTS heads and never mints one — minting here would order the same "
            "person twice. The shortfall is T-1173's to draw." % (group, "\n".join(
                "  %s orders %d and %d head(s) stand at its trades" % row for row in shortfalls)))
    # AND THE ROOFS THAT STAND. The second quota, in the same loop and on the same rules:
    # one record per standing lodging roof, a keeper adopted rather than minted, and a
    # premises location in the building that bought it.
    for bucket in roof_buckets(group):
        for ordinal, place in enumerate(bucket["places"], start=1):
            records.append(record_for_roof(group, bucket, place, ordinal, communities))
    # AND THE HEADS THAT STAND AT A TRADE THAT NAMES A HOUSE. The third quota, on the same
    # rules again: one record per drawn head, the man adopted rather than minted, and a
    # street face off a stated rule because there is no building to point at.
    for bucket in trade_buckets(group, heads):
        for ordinal, head in enumerate(bucket["heads"], start=1):
            if head["person_id"] in taken:
                raise SystemExit(
                    "%s is already the proprietor of a house this group built against a "
                    "count, and the trade quota would give him a second: one quota, filled "
                    "once." % head["person_id"])
            taken.add(head["person_id"])
            records.append(
                record_for_trade(group, bucket, head, ordinal, communities, streets))
    records.sort(key=lambda r: r["id"])
    return records


def collisions(records, businesses_dir=None):
    """An invented style may not be a style the register already prints, and an invented
    house may not be two houses. The name of a real proprietor is checked too: this tool
    adopts a reconstructed person, so a style carrying a real person's name would be one."""
    names, people = attested_strings(businesses_dir)
    bad, seen, ids, proprietors = [], set(), set(), {}
    for record in records:
        key = record["name"].strip().lower()
        if key in names:
            bad.append("%s: the style %r is one the register already prints"
                       % (record["id"], record["name"]))
        if key in seen:
            bad.append("%s: two reconstructed houses trade under %r" % (record["id"], record["name"]))
        seen.add(key)
        # AND TWO HOUSES MAY NOT SHARE A FILE. The id is built from the keeper's surname and
        # the class, so two keepers of one trade who happen to share a surname would write
        # one record over the other and the build would quietly come out one house short —
        # a shortfall nothing states, which is the one kind this programme must not produce.
        if record["id"] in ids:
            bad.append("%s: two reconstructed houses claim this id; one would overwrite the "
                       "other and the town would be a house short with nothing saying so"
                       % record["id"])
        ids.add(record["id"])
        # AND A HEAD MAY NOT KEEP TWO HOUSES. The three forms adopt out of three different
        # lists — the trade heads, the lodgers stage's keepers, and the trade heads again —
        # and nothing upstream stops one man appearing in two of them. One person, one
        # house: a second would fill one quota twice and count the same man as two
        # establishments.
        for person in record["proprietors"]:
            pid = person.get("person_id")
            if pid and pid in proprietors:
                bad.append("%s: %s already keeps %s; one head, one house"
                           % (record["id"], pid, proprietors[pid]))
            if pid:
                proprietors[pid] = record["id"]
        for person in record["proprietors"] + record["partners"] + record["staff"]:
            if (person["name"] or "").strip().lower() in people:
                bad.append("%s: %r is a name the register prints on a real house"
                           % (record["id"], person["name"]))
            if person["tier"] != "reconstructed":
                bad.append("%s: %r is graded %r on a reconstructed house"
                           % (record["id"], person["name"], person["tier"]))
        if record["sources"] or record["claim_ids"]:
            bad.append("%s: a reconstructed house cites a source" % record["id"])
    return bad


def lodging_table(built):
    """BEDS AGAINST KEEPERS: every lodging place that stands, and the firm behind it.

    The acceptance clause of T-1408, and the reason it is a TABLE rather than a number:
    a house is unkept for more than one reason and the reasons are not interchangeable.
    A reconstructed roof with no firm is this programme's debt. A documented house with no
    firm is a RESEARCH question — the lodgers stage refused to put a drawn proprietor
    inside the New York House and the Sauganash on exactly that ground, and so does this —
    and its keeper reaches the business layer through the register or not at all. The
    table states which, per house, so neither can hide inside the other's count.
    """
    # READ OFF DISK, NOT OFF THE BUILD. --build writes every record before it writes this
    # ledger, so disk is the complete picture and the build's own dict is not: a run that
    # rebuilds one group would otherwise print the other group's standing roofs as unkept.
    firms, seated = business_premises()
    keepers = roof_keepers()
    rows, owed = [], 0
    for place in lodging_places():
        firm = firms.get(place["id"]) or None
        register = sorted(set(seated.get(place["id"], [])))
        keeper = keepers.get(place["id"])
        if place["standing"] == "reconstructed":
            kept_by = "this programme" if firm else None
            if not firm:
                owed += 1
                why = ("NO FIRM. The lodgers stage named no keeper for this roof, so there "
                       "is nobody to adopt and this programme mints none."
                       if keeper is None else
                       "NO FIRM, AND THE KEEPER IS STANDING. This is this programme's debt.")
            else:
                why = None
        else:
            kept_by = "the register" if register else None
            why = (None if register else
                   "A DOCUMENTED HOUSE WITH NO FIRM IN THE REGISTER. Who kept it on the "
                   "scene date is a research question and not a draw; T-1404 raises the "
                   "attested keepers the sources do name, and a reconstructed proprietor "
                   "is never written into a documented building.")
        rows.append({
            "place": place["id"],
            "name": place["name"],
            "class": place["class"],
            "standing": place["standing"],
            "beds_ordinary": place["beds_ordinary"],
            "beds_crowded": place["beds_crowded"],
            "keeper_person": (keeper or {}).get("person_id"),
            "firm": firm,
            "businesses_in_the_register_at_this_roof": register,
            "kept_by": kept_by,
            "why_not": why,
        })
    return {
        "_doc": ("BEDS AGAINST KEEPERS. Every place data/reconstruction/"
                 "1835_lodging_model.json stands, and the house of trade behind it. "
                 "`kept_by` is null where there is none, and `why_not` says which kind of "
                 "absence it is."),
        "places": len(rows),
        "reconstructed_roofs_this_programme_owes_a_firm": owed,
        "rows": rows,
    }


def business_premises(businesses_dir=None):
    """`({roof: firm}, {structure: [register ids]})` — who is seated in which building.

    Two maps, because the two mean different things. The first is what THIS programme
    bought with a standing roof. The second is every other house of trade the layer seats
    in a building, which is what a documented lodging house's keeper would arrive as.
    Read off the records rather than off data/businesses/index.json, because the index is
    derived from them and this table is asked while a build is deciding what it will say.
    """
    root = Path(businesses_dir or (DATA / "businesses"))
    firms, seated = {}, {}
    for path in sorted(list(root.glob("biz_*.json")) + list((root / "authored").glob("*.json"))):
        doc = load_json(path)
        roof = (doc.get("reconstruction") or {}).get("roof") or {}
        if roof.get("structure_id"):
            firms[roof["structure_id"]] = doc["id"]
            continue
        for loc in doc.get("locations") or []:
            if loc.get("kind") == "premises" and loc.get("structure_id"):
                seated.setdefault(loc["structure_id"], []).append(doc["id"])
    return firms, seated


def ledger(built):
    """What was built, by group, class and street — the counts the ticket asks be printed."""
    streets = {s["id"]: s.get("name_1835") or s["id"] for s in load_json(STREETS)["streets"]}
    groups = {}
    for group, records in sorted(built.items()):
        by_class, by_street, by_roof = {}, {}, {}
        for record in records:
            by_class[record["type"][0]] = by_class.get(record["type"][0], 0) + 1
            # A HOUSE BOUGHT BY A ROOF HAS NO STREET TO COUNT, and it is not silently
            # dropped into a `null` row: it is counted by the building it stands in, which
            # is the stronger statement of the two. The street table stays the street table.
            face = record["locations"][0]["street_id"]
            if face is None:
                roof = record["locations"][0]["structure_id"]
                by_roof[roof] = by_roof.get(roof, 0) + 1
                continue
            label = streets.get(face, face)
            by_street[label] = by_street.get(label, 0) + 1
        groups[group] = {
            "ticket": GROUPS[group]["ticket"],
            "title": GROUPS[group]["title"],
            "records": len(records),
            "by_class": dict(sorted(by_class.items())),
            "by_street": dict(sorted(by_street.items())),
            "by_roof": dict(sorted(by_roof.items())),
            "ids": [r["id"] for r in records],
            "proprietors_adopted": [r["proprietors"][0]["person_id"] for r in records],
        }
    return {
        "_doc": ("DERIVED from the reconstruction order book and the resident band's trade "
                 "heads by tools/reconstruct_businesses_1835.py. Do not hand-edit: --check "
                 "re-derives this file and every record it counts, and tools/check.sh runs "
                 "it. The counts are the ticket's own acceptance — by class and by street."),
        "id": PROGRAMME,
        "target_date": SCENE_DATE,
        "written_by": "tools/reconstruct_businesses_1835.py",
        "quota": "data/reconstruction/1835_reconstruction_order_book.json → bucket_families[businesses]",
        "proprietors": ("ADOPTED from data/residents/reconstructed_trades/, never minted. "
                        "tools/reconstruct_residents_1835.py is the one writer of a person."),
        "style_guide": "docs/RESEARCH/business-naming-1835.md",
        "liberty": "docs/LIBERTIES.md § L254",
        "records": sum(len(r) for r in built.values()),
        "groups": groups,
        "lodging": lodging_table(built),
        # BOTH ADJUDICATION TABLES, under their own names. A key here is a contract with
        # whatever reads the ledger, so the river table keeps the name it was published
        # under and the services table takes one of its own.
        **{spec["ledger_key"]: trade_adjudication_table(group)
           for group, spec in sorted(TRADE_ADJUDICATION.items())},
    }


def fills_for(built):
    """`{ticket: {bucket key: records}}` — this build's contribution to the order book."""
    out = {}
    for group, records in built.items():
        ticket = GROUPS[group]["ticket"]
        for record in records:
            # A HOUSE BOUGHT BY A ROOF FILLS NOTHING HERE, and that is not an omission: the
            # order book holds no bucket of its class to fill, which is the whole reason the
            # roof form exists. Carrying it would write a fill against a key the book does
            # not have, and the book's own --build would then be asked to count it.
            bucket = record["reconstruction"].get("bucket")
            if not bucket:
                continue
            out.setdefault(ticket, {})
            out[ticket][bucket] = out[ticket].get(bucket, 0) + 1
    return out


def write_fills(built):
    """Carry this build's fills into the order book and re-derive it.

    `filled` is A COUNTER A FILLER INCREMENTS, and the book's own --build refuses an
    overfilled bucket — so the quota the ticket says these houses may not exceed is
    enforced by the book as well as by the loop above. A group that built nothing still
    clears its own rows, which is how a re-cut that drops a bucket retires its houses.
    """
    import build_order_book_1835 as order_book

    book = load_json(ORDER_BOOK)
    mine = fills_for(built)
    tickets = {GROUPS[g]["ticket"] for g in built}
    kept = [f for f in book.get("fills", []) if f.get("ticket") not in tickets]
    for ticket, buckets in sorted(mine.items()):
        group = next(g for g, spec in GROUPS.items() if spec["ticket"] == ticket)
        kept += [{"bucket": key, "ticket": ticket, "stage": group, "records": n,
                  "by": "tools/reconstruct_businesses_1835.py --build"}
                 for key, n in sorted(buckets.items())]
    # APPENDED, NEVER RE-SORTED. The ledger is in the order the stages filled it and two
    # runs rewriting it whole would collide on every line of a file neither of them changed.
    book["fills"] = kept
    with open(ORDER_BOOK, "w", encoding="utf-8") as handle:
        json.dump(book, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    order_book.cmd_build()


def write(docs, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(docs, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def built_groups():
    """The groups that have records on disk — the ones --check must re-derive."""
    live = set()
    for path in sorted(AUTHORED.glob("rcb_*.json")):
        block = load_json(path).get("reconstruction") or {}
        if block.get("group") in GROUPS:
            live.add(block["group"])
    return sorted(live)


def build(groups):
    built = {}
    for group in groups:
        records = build_group(group)
        bad = collisions(records)
        if bad:
            raise SystemExit("\n".join(["the build refuses itself:"] + ["  " + b for b in bad]))
        built[group] = records
    AUTHORED.mkdir(parents=True, exist_ok=True)
    for group, records in built.items():
        for record in records:
            write(record, AUTHORED / ("%s.json" % record["id"]))
    for path in sorted(AUTHORED.glob("rcb_*.json")):
        block = load_json(path).get("reconstruction") or {}
        if block.get("group") in built and path.stem not in {
                r["id"] for r in built[block["group"]]}:
            path.unlink()
    # THE LEDGER IS THE WHOLE LAYER, NOT THIS RUN. A --build takes one group, because a
    # group is one ticket's quota — but the ledger counts every reconstructed house the
    # town carries, so a group this run did not touch is RE-DERIVED here rather than
    # written empty. It was written empty until T-1408, and nobody could see it while one
    # group existed: the second group's first build blanked the first group's counts and
    # --check then reported the ledger as a hand edit, naming the wrong file and the wrong
    # fault. A ledger that forgets a group when another is rebuilt is not a ledger.
    whole = {g: build_group(g) for g in built_groups() if g not in built}
    whole.update(built)
    write(ledger(whole), LEDGER)
    write_fills(built)
    for group, records in sorted(built.items()):
        print("%s (%s): %d reconstructed business record(s)"
              % (group, GROUPS[group]["ticket"], len(records)))
        for record in records:
            print("   %-28s %-12s %s" % (record["id"], record["type"][0], record["name"]))
    return 0


def check(groups=None):
    groups = groups or built_groups()
    if not groups:
        print("OK: no group of the business reconstruction has been built yet")
        return 0
    bad = []
    built = {}
    for group in groups:
        records = build_group(group)
        built[group] = records
        bad += collisions(records)
        on_disk = {p.stem for p in AUTHORED.glob("rcb_*.json")
                   if (load_json(p).get("reconstruction") or {}).get("group") == group}
        want = {r["id"] for r in records}
        for extra in sorted(on_disk - want):
            bad.append("%s: on disk and the order book does not order it" % extra)
        for missing in sorted(want - on_disk):
            bad.append("%s: the order book orders it and it is not on disk" % missing)
        for record in records:
            path = AUTHORED / ("%s.json" % record["id"])
            if path.exists() and load_json(path) != record:
                bad.append("%s: does not re-derive from its seeds — hand-edited?" % record["id"])
    # AND THE ORDER BOOK'S COUNTER AGREES. `filled` is carried rather than re-derived, so
    # a build that wrote records and did not carry its fill would leave the book reading a
    # quota it had already spent — and the book's overfill gate reading the wrong number.
    tickets = {GROUPS[g]["ticket"] for g in groups}
    book_fills = {}
    for fill in load_json(ORDER_BOOK).get("fills", []):
        if (fill.get("by", "").startswith("tools/reconstruct_businesses_1835.py")
                and fill.get("ticket") in tickets):
            book_fills.setdefault(fill["ticket"], {})[fill["bucket"]] = int(fill["records"])
    if book_fills != fills_for(built):
        bad.append("the order book's fills for %s are not what a rebuild counts: %r against %r"
                   % (", ".join(sorted(tickets)), book_fills, fills_for(built)))

    # AND NO HEAD THE TRADE QUOTA ORDERS A HOUSE FOR IS LEFT WITHOUT ONE. The ledger would
    # print the debt either way; this makes it RED, which is what the stop condition of
    # T-1424 asks for — a head drawn at a trade that names a house, and no house.
    for group, spec in sorted(TRADE_ADJUDICATION.items()):
        table = trade_adjudication_table(group)
        if table["heads_this_programme_owes_a_house"]:
            bad.append("%d %s head(s) stand at a trade that names a house of trade and keep "
                       "none; see `%s` in the ledger"
                       % (table["heads_this_programme_owes_a_house"], spec["of"],
                          spec["ledger_key"]))
        bad += adjudication_faults(table)

    want_ledger = ledger(built)
    if not LEDGER.exists():
        bad.append("%s is missing — run --build" % LEDGER.relative_to(ROOT))
    elif load_json(LEDGER) != want_ledger:
        bad.append("%s does not match a rebuild" % LEDGER.relative_to(ROOT))
    if bad:
        print("\n".join(["the business reconstruction does not re-derive:"]
                        + ["  " + b for b in bad]))
        return 1
    print("OK: %d reconstructed business record(s) over %d group(s) re-derive from their seeds"
          % (sum(len(r) for r in built.values()), len(built)))
    return 0


# ------------------------------------------------------------------------- the self-test

def self_test():
    """Every refusal above, fired once."""
    failures = []

    def expect(name, fn, needle):
        try:
            fn()
        except SystemExit as exc:
            if needle in str(exc):
                return
            failures.append("%s: refused for the wrong reason: %s" % (name, exc))
            return
        failures.append("%s: was not refused" % name)

    book = load_json(ORDER_BOOK)
    communities = person_communities()
    streets = {s["id"]: s.get("name_1835") or s["id"] for s in load_json(STREETS)["streets"]}
    heads = trade_heads()

    # 1. A class the tool carries no style or trade row for is refused by name.
    fake = json.loads(json.dumps(book))
    family = next(f for f in fake["bucket_families"] if f["key"] == "businesses")
    family["buckets"].append({
        "key": "businesses/lottery_office", "axes": {"class": "lottery_office"},
        "target": 1, "known": 0, "to_reconstruct": 1, "filled": 0,
        "owning_ticket": "T-1184", "basis": "a fixture"})
    expect("an unmapped class",
           lambda: build_group("stores_and_provisions", communities, streets, heads, fake),
           "carries no trade row or style")

    # 2. A quota the resident band has no heads for is refused, never under-filled.
    greedy = json.loads(json.dumps(book))
    family = next(f for f in greedy["bucket_families"] if f["key"] == "businesses")
    for bucket in family["buckets"]:
        if bucket["key"] == "businesses/druggist":
            bucket["to_reconstruct"] = 99
    expect("a quota past the heads drawn",
           lambda: build_group("stores_and_provisions", communities, streets, heads, greedy),
           "has not drawn enough trade heads")

    # 3. A style the register already prints is refused.
    records = build_group("stores_and_provisions", communities, streets, heads)
    clash = json.loads(json.dumps(records))
    clash[0]["name"] = "Philo Carpenter"
    bad = collisions(clash)
    if not any("already prints" in b for b in bad):
        failures.append("an attested firm style was not refused")

    # 4. A reconstructed house that cites a source is refused.
    cited = json.loads(json.dumps(records))
    cited[0]["sources"] = ["chicago_newspapers_1833_1835"]
    if not any("cites a source" in b for b in collisions(cited)):
        failures.append("a reconstructed house citing a source was not refused")

    # 5. Two houses under one style are refused.
    twinned = json.loads(json.dumps(records)) * 2
    if not any("two reconstructed houses" in b for b in collisions(twinned)):
        failures.append("a duplicated style was not refused")

    # 6. The draw is a function of the seed string and nothing else.
    again = build_group("stores_and_provisions", communities, streets, heads)
    if again != records:
        failures.append("two builds of one group differ")

    # 7. Every proprietor is a person the resident layer holds, and is reconstructed.
    ids = {h["person_id"] for rows in heads.values() for h in rows}
    for record in records:
        for person in record["proprietors"]:
            if person["person_id"] not in ids:
                failures.append("%s: proprietor %s is not an adopted trade head"
                                % (record["id"], person["person_id"]))

    # 8. Two houses may not claim one id — one would overwrite the other on disk and the
    #    town would come out a house short with nothing saying so.
    same_id = json.loads(json.dumps(records))[:1] * 2
    same_id[1]["name"] = same_id[1]["name"] + " the second"
    if not any("claim this id" in b for b in collisions(same_id)):
        failures.append("two houses sharing an id were not refused")

    # 9. THE SECOND QUOTA. A standing lodging roof buys a firm, and the record says so the
    #    way the schema demands: a roof block, no order-book bucket, and a premises
    #    location in the very building that bought it.
    roofs = [r for r in build_group("lodging_river_and_transport")
             if (r["reconstruction"].get("roof") or {}).get("structure_id")]
    if not roofs:
        failures.append("the lodging group builds no house on a standing roof")
    for record in roofs:
        block = record["reconstruction"]
        if block.get("bucket") or block.get("slot"):
            failures.append("%s: bought by a roof and naming an order-book row too"
                            % record["id"])
        seat = record["locations"][0]
        if seat["kind"] != "premises" or seat["structure_id"] != block["roof"]["structure_id"]:
            failures.append("%s: bought by a roof it does not stand on" % record["id"])
        if record["proprietors"][0]["person_id"] != block["roof"]["keeper_person_id"]:
            failures.append("%s: keeps a house with somebody else's keeper" % record["id"])

    # 10. A roof whose keeper the lodgers stage never named is NOT ordered. This tool
    #     adopts a keeper and mints nobody, so an unkept roof is a shortfall stated in the
    #     ledger rather than a person invented to fill it.
    keeperless = roof_buckets("lodging_river_and_transport", keepers={})
    if keeperless:
        failures.append("a lodging roof with no keeper was still ordered a firm")

    # 11. A ROOF FILLS NO ORDER-BOOK BUCKET, because the book holds none of its class. A
    #     fill written against a key the book does not have would be counted by the book's
    #     own --build and there is nothing there to count.
    if fills_for({"lodging_river_and_transport": roofs}):
        failures.append("a house bought by a roof wrote a fill into the order book")

    # 10. A class that carries a caveat prints it on every record it writes, and a class
    #    that carries none is written exactly as it was before the key existed. The
    #    brewery of T-1185 is the standing example: the Chicago American of 15 August 1835
    #    counts one brewery where the December census counts two, and a reader holding the
    #    card must hold that objection too.
    mechanics = build_group("mechanics_shops", communities, streets, heads)
    for record in mechanics:
        cls = record["type"][0]
        caveat = STYLES[cls].get("caveat")
        note = record["reconstruction"]["basis"]["note"]
        if caveat and caveat not in note:
            failures.append("%s: the %s caveat is not on the record it qualifies"
                            % (record["id"], cls))
        if not caveat and "TIGHTER COUNT" in note:
            failures.append("%s: an uncaveated class printed a caveat" % record["id"])
    for record in records:
        if "TIGHTER COUNT" in record["reconstruction"]["basis"]["note"]:
            failures.append("%s: the caveat leaked onto a class that carries none"
                            % record["id"])

    # 9. An empty trade row is a RULING — the class is mapped and draws no head — and is
    #    not the same thing as a class missing from the table, which is refused by name.
    for cls in ("iron_foundry", "tin_and_copper_manufactory"):
        if TRADE_CLASS.get(cls) != []:
            failures.append("%s: the book owes T-1185 no houses of this class and the "
                            "trade row should say so with an empty list" % cls)

    # 12. THE THIRD QUOTA. A drawn trade head buys a firm, and the record says so the way
    #     the schema demands: a trade_head block, no order-book bucket and no roof, the head
    #     himself as the sole proprietor, and a street-only face because there is nothing of
    #     the class standing to seat it on.
    kept = []
    for group in sorted(TRADE_ADJUDICATION):
        mine = [r for r in build_group(group)
                if (r["reconstruction"].get("trade_head") or {}).get("person_id")]
        if not mine:
            failures.append("%s builds no house on a drawn trade head" % group)
        kept.extend(mine)
    for record in kept:
        block = record["reconstruction"]
        if block.get("bucket") or block.get("slot") or block.get("roof"):
            failures.append("%s: bought by a trade head and naming another form too"
                            % record["id"])
        if [p["person_id"] for p in record["proprietors"]] != [block["trade_head"]["person_id"]]:
            failures.append("%s: the head who bought this house does not keep it"
                            % record["id"])
        if record["locations"][0]["kind"] != "street_only":
            failures.append("%s: bought by a trade head and seated on something narrower "
                            "than a street" % record["id"])
        if record["type"][0] in census_enumerated_classes():
            failures.append("%s: typed into a class the census enumerates, spending a "
                            "printed count" % record["id"])

    # 13. A TRADE ROW THAT WOULD SPEND A PRINTED COUNT IS REFUSED BY NAME. The whole reason
    #     the form exists is that the census never counted these classes; a row typed into
    #     one it DID count is the failure the form was built to avoid.
    def spend_a_count():
        saved = TRADE_QUOTA["lodging_river_and_transport"]["trades"]["lumber_merchant"]["type"]
        TRADE_QUOTA["lodging_river_and_transport"]["trades"]["lumber_merchant"]["type"] = \
            "storage_and_forwarding"
        try:
            trade_buckets("lodging_river_and_transport", heads, book)
        finally:
            TRADE_QUOTA["lodging_river_and_transport"]["trades"]["lumber_merchant"]["type"] = saved
    expect("a trade row spending a printed count", spend_a_count,
           "the order book enumerates that class")

    # 14. And a trade the adjudication table does not call a house of trade may not be
    #     built one: the table is the ruling and the quota follows it, never the reverse.
    def quota_past_the_ruling():
        saved = RIVER_AND_TRANSPORT["lumber_merchant"]["kind"]
        RIVER_AND_TRANSPORT["lumber_merchant"]["kind"] = "employment"
        try:
            trade_buckets("lodging_river_and_transport", heads, book)
        finally:
            RIVER_AND_TRANSPORT["lumber_merchant"]["kind"] = saved
    expect("a quota the adjudication does not carry", quota_past_the_ruling,
           "does not call that trade a house_of_trade")

    # 15. ONE HEAD, ONE HOUSE. The three forms adopt out of three lists and nothing upstream
    #     stops a man appearing in two; a second house would count him as two establishments.
    twice = json.loads(json.dumps(kept))[:1] * 2
    twice[1]["id"] = twice[1]["id"] + "_again"
    twice[1]["name"] = twice[1]["name"] + ", second stand"
    if not any("one head, one house" in b for b in collisions(twice)):
        failures.append("a head keeping two houses was not refused")

    # 16. EVERY RIVER AND TRANSPORT HEAD IS ADJUDICATED. The stop condition of T-1424: a
    #     head at a `house_of_trade` trade with no firm behind it is this programme's debt,
    #     and every other head carries a printed reason it keeps no house.
    for group, spec in sorted(TRADE_ADJUDICATION.items()):
        table = trade_adjudication_table(group)
        if table["heads_this_programme_owes_a_house"]:
            failures.append("%d %s head(s) the trade quota orders a house for have none"
                            % (table["heads_this_programme_owes_a_house"], spec["of"]))
        for row in table["rows"]:
            if not (row.get("why") or "").strip():
                failures.append("%s: adjudicated with no reason printed" % row["trade"])
            if row["kind"] == "deferred" and not row.get("deferred_to"):
                failures.append("%s: deferred to nothing" % row["trade"])
        failures += adjudication_faults(table)

    # 17. AND A DEFERRAL THAT OUTLIVES ITS TICKET IS CAUGHT. The assertion still fires:
    #     defer a row to a ticket that is closed and `adjudication_faults` says so.
    saved = dict(RIVER_AND_TRANSPORT["seaman"])
    RIVER_AND_TRANSPORT["seaman"] = {"kind": "deferred", "ticket": "T-1424",
                                     "why": "a deferral to a ticket that has closed"}
    try:
        if not adjudication_faults(river_and_transport_table()):
            failures.append("a head deferred to the closed T-1424 did not go red")
    finally:
        RIVER_AND_TRANSPORT["seaman"] = saved

    # 18. AND EVERY QUOTA ROW IS COVERED BY A TABLE. A group that orders houses and has no
    #     adjudication table would build them on no ruling at all; the two must be added
    #     together or neither.
    for group in TRADE_QUOTA:
        if group not in TRADE_ADJUDICATION:
            failures.append("%s orders houses on a trade quota and no table adjudicates it"
                            % group)

    if failures:
        print("\n".join(["self-test FAILED:"] + ["  " + f for f in failures]))
        return 1
    print("OK: 19 assertions of the business reconstruction still fire")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--group", action="append", choices=sorted(GROUPS),
                        help="the reconstruction group to build; repeatable")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.build:
        if not args.group:
            parser.error("--build wants a --group: a group is one ticket's quota")
        return build(args.group)
    if args.check:
        return check(args.group)
    parser.error("one of --build, --check or --self-test")


if __name__ == "__main__":
    raise SystemExit(main())
