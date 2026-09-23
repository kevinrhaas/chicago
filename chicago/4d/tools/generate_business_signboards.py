#!/usr/bin/env python3
"""Generate the town's business signboards — what each one says, and how it hangs.

WHAT THIS IS. `docs/ROADMAP.md` K5 (b) asked for *"signboards on businesses"* and ticket
T-0039 built the layer: a plank on a bracket, hung off a wall this project had already
drawn, on every frontage a rule selected. Every one of those boards was BLANK, and every
one was hung the same way, because L25 and L130 read the absence of any recorded WORDING
as a reason to paint nothing at all.

T-0066 OVERRULES THAT, on the owner's instruction of 2026-08-18, verbatim: *"you can and
should put the name of the location on the sign board. the sign boards should have
variation in color and style and signage font and color, some signs may hang from an
awning and others may be on the building or painted on the face of the building. you
need to add more signage and be period correct and it is fine if they are
reconstructions."* The standing ruling on invention applies: *"you are totally fine to be
liberal with adding reconstructed items when i ask for things, you can just label and
mark them as such."* So this record now carries, for every board:

  * the WORDING — what a signwriter lettered on that frontage: see SIGN_WORDING below;
  * a MOUNTING — bracket-hung over the footway, hung under an awning, fixed flat on the
    building, standing on a post at the street edge, or the name painted straight onto
    the face of the building;
  * a STYLE — ground colour, letter colour, letterform and panel, from a table of the
    combinations the trade actually used, assigned so that no two boards within
    `NEIGHBOUR_M` of each other share a mounting, a style or a ground colour.

THAT LAST PROMISE IS LOCAL, AND SINCE T-0405 SO IS THE RULE THAT KEEPS IT. Both the
mounting and the style now enter their tables at a point derived from the board's OWN
structure id, and the only thing that can move a board off that point is a board within
`NEIGHBOUR_M` of it. It used to be the frontage's position in its trade class, dealt out
as the walk went down the town in id order, so admitting one frontage in the middle of
the alphabet re-dealt every frontage after it — eleven boards, the furthest 904 m off,
four of them changing what they SAID, when `frederick_thomas_shop` was admitted (T-0263).
The promise is now asserted rather than assumed (`_neighbours_differ`, every build) and
the locality is provable (`--prove-locality`, which withholds each board in turn).

`docs/LIBERTIES.md` **L159** is the claim for the mounting and the style, and **L169**
for the wording.

T-0130 CORRECTS THE WORDING, and the correction is the owner's, 2026-08-21, verbatim:
*"philo would not have referred to his own place as log drug store, it would be philo
carpenter, drugs and medicines, or druggist or whatever he would have referred to himself
as on the sign, that may be different than the name of the building for us, the sign may
read differently historically."* And, of the next one: *"same with hogan's store."* And,
widening it to the set: *"i guess do a pass on all those signs and make sure they feel
right for the era."*

T-0066 painted the STRUCTURE RECORD'S OWN `name` on the board, less a trailing
parenthetical, and this docstring used to defend that: *"the card a visitor opens by
tapping the board has to say what the board says."* THAT COLLAPSED TWO DIFFERENT OBJECTS.

  * A record's `name` is OUR LABEL FOR A BUILDING — descriptive, disambiguating, written
    so a modern reader knows which structure is meant: "Philo Carpenter's Log Drug Store",
    "Hogan's Store", "Tremont House (the first)". The word "log" is in there because the
    walls are log. No druggist painted the construction of his own shop on his own board.
  * A SIGNBOARD carries what the TRADE lettered — the proprietor or the firm, and the
    trade he practised, in the register a signwriter actually worked in.

So the two fields are now separate and are allowed to differ. The structure keeps its
`name` for the card and the search box; the board carries `sign_text` out of
SIGN_WORDING. What the two must still agree about is WHO THIS IS: every entry declares a
`sign_identity` — the proprietor, the firm or the house — and this file refuses to build
unless that identity appears in the board AND in the card. `tools/smoke_renderer.mjs`
asserts the same thing at run time, over every sign and at the Tremont's own board. That
is a CORRECTION of T-0066's string-equality assertion, not a relaxation of it.

THE RULE THAT CHOOSES A FRONTAGE, and every clause is doing work. A structure gets a
sign iff

  1. it is a NAMED record — the id does not begin `inf_` or `recon_` and the name does
     not begin "Reconstructed". The archetype tables already carry this rule in as many
     words: *never invent business, sign text or goods for an anonymous slot*. An
     anonymous roof dealt a trade by a schedule has no proprietor to announce, and now
     that the boards carry NAMES the clause matters more than it did when they were
     blank: there would be no name to paint;
  2. its `function` is a trade this project will announce. Two classes of them now:
     a PUBLIC TRADE, whose customer was a stranger arriving on foot off the street (a
     public house, a lodging house, a shop counter, the auction room, the printing
     offices that also sold over one) — these get a BOARD; and, added by T-0066, a
     WORKS OR WAREHOUSE trade, whose custom came by name and by cart — these get the
     firm's name PAINTED ON THE BUILDING and never a board swinging over a footway
     nobody walked. Stables, churches, schools, the court-house, the jail, the agency
     house and the fort stay outside both lists;
  3. that function is `attested` or `inferred`. A `reconstructed` trade gets no sign —
     inventing a sign for an invented business is invention squared;
  4. it is standing on the scene date (it is in `data/sidecars/1835/index.json`);
  5. it does not already carry a sign. One record does, and duplicating it would put
     two boards on the Wolf Point Tavern;
  6. it does not already carry a NAMED board on a post at its corner on the frontage
     layer (the Green Tree — T-0082, L135);
  7. and, for the works and warehouse class only, its name carries a PROPRIETOR — a
     possessive or an ampersand. A works painted whose it was. A building this project
     names by a later nickname ("The Old Bank Building") has no proprietor to paint,
     and painting the nickname would put a twentieth-century label on an 1835 wall;
  8. and the name this board would letter is a name the corpus still puts INSIDE the
     building on the scene date. A LABEL MAY OUTLIVE A TENANCY AND A SIGN MAY NOT, and
     that is one sentence's difference between two objects this file already keeps
     apart. A record's `name` is a modern caption — it is how a reader finds the
     building, and it goes on carrying the trade the building was known by long after
     that trade has moved, exactly as a town goes on calling a corner by the shop that
     used to be on it. A BOARD IS AN ASSERTION IN THE PRESENT TENSE: it stands in the
     scene at 1 July 1835, a walker reads it as a statement about what is behind that
     wall today, and if the register no longer agrees with it the board is simply
     wrong. So where a record's name belongs to a tenancy this project has followed
     OUT of the building, there is no name left to letter, and this rule refuses
     rather than substituting one — the same refusal clause 1 makes for an anonymous
     slot and clause 7 for a works with no proprietor, reached from the other side.
     The substitute is the trap: a frontage whose departed trade is the only name the
     corpus offers invites a replacement lettered off whatever else is in the file,
     and a for-sale notice or an advertisement from a year before the scene date does
     NOT attest who kept a counter on the day. Where the corpus cannot name who traded
     there on the scene date, THE WALL IS LEFT BLANK, in writing, in `refused`. See
     docs/PROVENANCE.md § A label may outlive a tenancy; a sign may not.

WHERE THE SIGN GOES is then DERIVED, not placed. `docs/GLB-CONTRACT.md` fixes the frame:
polygon `u` → +X, polygon `v` → −Z, and `rotation_deg` is the FACADE BEARING, so the
front wall is the footprint's own max-`v` edge and the direction it faces is the bearing
itself. A hanging board hangs to one side of that edge's centre and clear of the eave;
a wall board and a painted name are centred on it. A POST is the one mounting that
stands in the street rather than on the building, so it is refused — in writing, and the
next mounting in the cycle is taken — wherever the fronting street's own travelled track
comes too close, or wherever the frontage layer already lays a plank walk outside that
wall. That test is `data/streets/1835.json`'s, the same one
`tools/generate_frontage_works.py` uses.

    python3 tools/generate_business_signboards.py            write the record
    python3 tools/generate_business_signboards.py --check    re-derive and diff
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# The archetypes' own set-out, read without Blender. `facade_openings` is the one
# place that answers WHERE THE OPENINGS ARE, and every rectangle it returns is
# computed by the same function the mesh is built from — see its module docstring
# and T-0459.
sys.path.insert(0, str(ROOT / "generators"))
from archetypes import facade_openings  # noqa: E402
from archetypes.frame_storefront_params import from_phase as _storefront_params  # noqa: E402
from archetypes.log_dwelling_params import from_phase as _log_dwelling_params  # noqa: E402
from archetypes.outbuilding_params import from_phase as _outbuilding_params  # noqa: E402

# The scene, and the phase of each record that stands on it.
TARGET_DATE = "1835-07-01"
_RESOLVERS = {
    "frame_storefront": _storefront_params,
    "log_dwelling": _log_dwelling_params,
    "outbuilding": _outbuilding_params,
}
SIDECARS = DATA / "sidecars" / "1835"
STRUCTURES = DATA / "structures"
STREETS = DATA / "streets" / "1835.json"
FRONTAGE = DATA / "frontage"
OUT = DATA / "signage" / "town_business_signboards.json"

# Clause 2, first class. Trades whose customer was a stranger off the street. The
# value on the left is `function.value` as the structure records write it; the phrase
# on the right is why a sign belongs on that door and is quoted into the record.
PUBLIC_TRADES = {
    "tavern_inn": "a public house takes its custom from the road",
    "hotel": "a public house takes its custom from the road",
    "boarding_house": "lodging is sold to arrivals who have to find the door",
    "store": "a counter open to the street",
    "store_residence": "a counter open to the street, with the keeper living over it",
    "store_and_dwelling": "a counter open to the street, with the keeper living over it",
    "dwelling_and_store": "a counter open to the street, with the keeper living over it",
    "grocery_and_provision_store": "a counter open to the street",
    "drug_store": "a counter open to the street",
    "forwarding_and_commission_store": "a counting-room a shipper has to find from the wharf",
    "auction_room": "a sale room whose whole trade is being found on the day",
    "saddlery_and_harness_shop": "a craft shop selling finished goods over a counter",
    "printing_office": "an office that took job work and subscriptions from callers",
    "printing_office_and_store": "an office that took job work and sold over a counter",
    "physicians_office": "a consulting room a stranger has to be able to find",
    "shop": "a shop front on a street of stores",
}

# Clause 2, second class — added 2026-08-21 with T-0066. A works or a warehouse did not
# hang a board over a footway; it painted the firm's name on the front, where a carter
# and a shipper could read it off the river or off the road. That is the distinction
# L130's excluded-trades note drew when it left these frontages mute, and the answer to
# it is a DIFFERENT MOUNTING rather than a different silence.
WORKS_TRADES = {
    "blacksmith_shop": "a smith's shop, named on its front for the carter who needs one",
    "forwarding_commission_warehouse": "a warehouse names its firm for the shipper on the river",
    "warehouse_and_slaughter_yard": "a warehouse names its firm for the shipper on the river",
    "slaughterhouse_packing": "a packing house names the firm the drover is delivering to",
    "packing_house": "a packing house names the firm the drover is delivering to",
    "tannery": "a tan-yard names its master for the trade that brings him hides",
    "soap_candle_manufactory": "a manufactory names the firm whose goods leave by the cart-load",
    "brickyard": "a brickyard names its owner for the builder ordering by the thousand",
}

# Which cycle of mountings a trade draws from. Two frontages of the same class in the
# same street get DIFFERENT mountings because the cycle advances; two of different
# classes differ because the cycles do not start in the same place.
TRADE_CLASS = {
    **{t: "house" for t in ("tavern_inn", "hotel", "boarding_house")},
    **{t: "counter" for t in (
        "store", "store_residence", "store_and_dwelling", "dwelling_and_store",
        "grocery_and_provision_store", "drug_store", "shop",
        "saddlery_and_harness_shop")},
    **{t: "office" for t in (
        "printing_office", "printing_office_and_store", "auction_room",
        "forwarding_and_commission_store", "physicians_office")},
    **{t: "works" for t in WORKS_TRADES},
}

# THE MOUNTINGS, and why each class draws from the cycle it does.
#
#  * a PUBLIC HOUSE is read from up the road by somebody who has not arrived yet, so its
#    name goes where it is seen furthest — under a hood over the door, out on a bracket,
#    or on a post at the street edge (which is exactly what the Green Tree does, images 6
#    and 7 of the owner's brief, and what T-0082 already drew there);
#  * a COUNTER is read from the footway by somebody already outside it, so a bracket
#    board over the walk, a board fixed on the front, an awning board, or the name
#    straight on the boards of the building — the Tremont street scene (image 5) shows a
#    whole row of painted fronts;
#  * an OFFICE or a sale room is a door among doors and mostly took a modest board on the
#    building itself;
#  * a WORKS paints its front and never hangs anything (see WORKS_TRADES above).
MOUNTING_CYCLE = {
    "house": ["awning_board", "bracket_board", "post_board"],
    "counter": ["bracket_board", "wall_board", "awning_board", "facade_painted"],
    "office": ["wall_board", "bracket_board", "facade_painted"],
    "works": ["facade_painted"],
}

# THE STYLES. Ground, letters, letterform and panel — the combinations an American
# signwriter of the 1830s worked in. Nothing here is a Chicago record: no wording,
# device or colour of any sign in this town survives, so the whole table is
# reconstruction and is graded as one (L159). What it is NOT is arbitrary: black
# grounds with gilt letters, white lead grounds with black, ochre (the cheapest
# pigment on any colourman's shelf), Venetian red, Prussian blue and Brunswick green
# are the trade's ordinary stock, and the letterforms are the four the period's
# specimen books actually sell — the signwriter's roman, the fat face that is the
# 1830s display letter, the Egyptian slab that arrives with it, and the plain block.
# `aspect` is the board's width-to-height and is part of the variation: two boards on
# one street should not be the same rectangle either.
STYLES = [
    {"id": "gold_on_black", "ground": "#141009", "letter": "#c9a227",
     "face": "signwriter", "panel": "plain", "aspect": 1.85,
     "note": "gilt letters on a black ground, shaded — the commonest painted board of the trade"},
    {"id": "black_on_white", "ground": "#e8e1cf", "letter": "#191410",
     "face": "fat_face", "panel": "double_rule", "aspect": 2.10,
     "note": "black on a white lead ground, the cheapest board a signwriter could sell"},
    {"id": "cream_on_green", "ground": "#1d3226", "letter": "#e7ddc0",
     "face": "signwriter", "panel": "single_rule", "aspect": 1.70,
     "note": "cream on a Brunswick-green ground"},
    {"id": "black_on_ochre", "ground": "#c19a52", "letter": "#1a1309",
     "face": "egyptian", "panel": "plain", "aspect": 2.35,
     "note": "black Egyptian on a yellow-ochre ground"},
    {"id": "cream_on_red", "ground": "#7c3020", "letter": "#efe3c8",
     "face": "fat_face", "panel": "single_rule", "aspect": 1.95,
     "note": "cream fat face on Venetian red"},
    {"id": "white_on_blue", "ground": "#22344f", "letter": "#e9e6dc",
     "face": "grotesque", "panel": "plain", "aspect": 2.20,
     "note": "white block letters on a Prussian-blue ground"},
    {"id": "gold_on_green", "ground": "#16261c", "letter": "#c8a63c",
     "face": "signwriter", "panel": "oval", "aspect": 1.75,
     "note": "gilt letters in an oval field on a dark green ground"},
    {"id": "black_on_timber", "ground": "#cbc2b1", "letter": "#241a10",
     "face": "grotesque", "panel": "plain", "aspect": 2.00,
     "note": "black on a bare weathered board — the tone L130 hung the town's blank boards in"},
    {"id": "red_on_white", "ground": "#e9e2d1", "letter": "#8c2f1f",
     "face": "egyptian", "panel": "oval", "aspect": 1.80,
     "note": "vermilion Egyptian on a white ground"},
    {"id": "white_on_brown", "ground": "#4a3121", "letter": "#e6dccb",
     "face": "fat_face", "panel": "double_rule", "aspect": 2.45,
     "note": "white fat face on a chocolate-brown ground"},
]

# Clause 3.
TRADE_GRADES = {"attested", "documented", "inferred"}

# --- WHAT THE BOARDS SAY (T-0130) -------------------------------------------
#
# THE REGISTER, taken from the advertisements themselves rather than from a modern eye:
# the PROPRIETOR OR FIRM first and largest, the TRADE beneath it, and the PLACE last and
# smallest. Carpenter's 1835 advertisement heads itself "PHILO CARPENTER, Wholesale &
# Retail Druggist, … South Water Street, Chicago"; Brewster, Hogan & Co.'s reads
# "BREWSTER, HOGAN & CO. Forwarding & Commission MERCHANTS, Chicago—Illinois". Both put
# the man or the firm on the top line in the largest letter, the trade in a second face
# beneath, and the place last. That hierarchy is the record's (`sign_lines` carries the
# role of each line) and `renderers/web/js/signage.js` letters it.
#
# PERIOD SPELLING IS THEIRS AND IS KEPT. "Stationary" for stationery, "Sattinetts",
# "Merselles", the em-dashed "Chicago—Illinois" — a board that modernises its own
# spelling stops feeling like 1835, which is half of what the owner asked for.
#
# WHERE THE 1833 AND 1835 COPY DIFFER, THE 1835 WINS. The scene is 1 July 1835 and firms
# rewrote their lines: Carpenter advertises "DRUGS AND MEDICINES" in 1833 and calls
# himself "Wholesale & Retail Druggist" by 1835.
#
# THE TIERS, AND WHY NOT ONE OF THEM IS `attested` YET. The owner supplied seven pages of
# 1833-35 Chicago newspaper advertising as IMAGES IN CONVERSATION on 2026-08-21 and ruled,
# verbatim: *"I will give you all those data sources later in a more comprehensive form
# proceed where you can and label reconstruction or inferred with a note as you like"*.
# So a wording taken off those pages is graded `inferred` — reasoned from a document about
# THIS PARTICULAR FIRM — and every one of those notes says what the advertisement says,
# where it came from, that the transcription is not yet a citation, and that it is to be
# UPGRADED TO `attested` when the page images land in `data/sources/assets/`. A
# transcription in a ticket is not a source record, and this file will not pretend it is.
# A wording with no surviving advertisement is `reconstructed` and built out of the trade
# vocabulary those same pages evidence.
PENDING = (
    "TRANSCRIBED FROM OWNER-SUPPLIED PAGE IMAGES, 2026-08-21, WHICH ARE NOT YET COMMITTED "
    "to data/sources/assets/, so this is graded `inferred` rather than `attested` on the "
    "owner's own ruling of that day: \"I will give you all those data sources later in a "
    "more comprehensive form proceed where you can and label reconstruction or inferred "
    "with a note as you like\". UPGRADE THIS VALUE TO `attested` when the pages are "
    "committed as a source record and this note can cite one."
)

# The device Carpenter's own advertisement names. A device belongs to a shop only where
# that shop's own advertisement names one — see the note.
DEVICES = {
    "golden_mortar": {
        "id": "golden_mortar",
        "label": "a mortar and pestle, gilt",
        "colour": "#d9b036",
        "shade": "#7a5c14",
        "confidence": "inferred",
        "note": (
            "A CHICAGO SIGNBOARD DESCRIBED BY ITS OWN OWNER, IN PRINT, IN THE SCENE YEAR. "
            "Philo Carpenter's 1835 advertisement heads itself \"PHILO CARPENTER, "
            "Wholesale & Retail Druggist, AT THE SIGN OF THE GOLDEN MORTAR, South Water "
            "Street, Chicago\". A mortar and pestle is the druggist's universal device, "
            "and a Detroit house advertising on the same pages \"at the sign of the Large "
            "Pitcher\" shows the convention was live and ordinary. So this board carries "
            "the device PAINTED rather than the phrase lettered: the sign is what he "
            "described, not a sentence about it. THIS IS THE OPPOSITE CASE TO L25, WHICH "
            "STANDS UNTOUCHED — L25 withholds the Wolf Point wolf because that IMAGE was "
            "never described, and here the owner of the shop describes his own board. "
            "What is invented is the DRAUGHTSMANSHIP: the outline is a plain bowl, rim "
            "and pestle, no ornament and no ground line. " + PENDING
        ),
    },
}

# HOW MANY LINES EACH MOUNTING CARRIES. A signwriter letters what fits: a plank swinging
# over a footway takes the man and his trade, and a board fixed flat on a wall or a name
# painted across a whole front has room for the street as well. This is why `sign_text`
# is resolved AFTER the mounting is chosen and not before.
LINES_BY_MOUNTING = {
    "bracket_board": 2,
    "awning_board": 2,
    "post_board": 2,
    "wall_board": 3,
    "facade_painted": 3,
}

# EVERY BOARD IN THE TOWN, in the trade's own words where they survive.
#
#   name         line 1 — the proprietor, the firm or the house, largest
#   trade        line 2 — the trade, in the period's own words
#   trade_short  line 2 where the mounting has room for two lines only
#   place        line 3 — the street or the town, smallest, where the board has room
#   identity     the token the board and the card must BOTH carry (see _norm)
#   grade        `inferred` (a firm's own advertisement) or `reconstructed`
#   device       a painted device, where the firm's own advertisement names one
#   sources      COMMITTED source records only — the owner's 2026-08-21 pages are not
#                committed and are described in `why` instead
#   why          what the evidence says, quoted, and what would upgrade the grade
SIGN_WORDING = {
    "bates_auction_room": {
        "name": "J. BATES, JR.", "trade": "Auctioneer", "identity": "Bates",
        "grade": "inferred",
        "why": (
            "His own advertisement signs itself \"J. BATES, JR.\" over the single trade "
            "word \"Auctioneer\" — the whole of a sale-room's copy, because an auctioneer "
            "sells his name. The record's own label, \"John Bates Jr.'s Auction Room\", "
            "describes the building for a modern reader; the board carries the man. "
            + PENDING
        ),
    },
    "brickyard_north_side": {
        "name": "T. K. BLODGETT", "trade": "Brick Maker", "identity": "Blodgett",
        "grade": "reconstructed",
        "why": (
            "No advertisement for this yard is in the pages read. Andreas names Tyler K. "
            "Blodgett and calls him \"undoubtedly the first brick-maker\", and the "
            "record's own occupants block carries him, so the board is built in the "
            "register the pages evidence — proprietor, then trade — out of the trade's "
            "own word. Reconstructed: nobody records that this yard announced itself at "
            "all, let alone in these words."
        ),
    },
    "brown_boarding_house": {
        "name": "RUFUS BROWN", "trade": "Boarding House", "identity": "Brown",
        "grade": "reconstructed",
        "why": (
            "No advertisement for this house is in the pages read. \"Boarding House\" is "
            "the period's own term and the record's own function; the proprietor is the "
            "record's. Reconstructed."
        ),
    },
    "carpenter_south_water_store": {
        "name": "PHILO CARPENTER", "trade": "Wholesale & Retail Druggist",
        "trade_short": "Druggist", "place": "South Water Street",
        "identity": "Carpenter", "grade": "inferred", "device": "golden_mortar",
        "why": (
            "HIS OWN 1835 WORDS, AND THE SCENE IS 1835. The advertisement heads itself "
            "\"PHILO CARPENTER, Wholesale & Retail Druggist, AT THE SIGN OF THE GOLDEN "
            "MORTAR, South Water Street, Chicago\" and goes on \"has just received and now "
            "offers for sale, one of the largest and best selected assortments of DRUGS "
            "AND MEDICINES, Paints, Oils, & Dye-Stuffs, ever offered in the State of "
            "Illinois\". Man, trade, street — in that order, which is the order the board "
            "letters. THIS IS THE FRONTAGE THE ADVERTISEMENT PLACES ON SOUTH WATER STREET, "
            "so it is this board and not his older Lake Street shop that carries the "
            "golden mortar. The 1833 copy for the same man reads \"DRUGS AND MEDICINES\" "
            "and is used on that older shop, because firms rewrote their lines and this "
            "project models the later day. " + PENDING
        ),
    },
    "chicago_american_office": {
        "name": "CHICAGO AMERICAN", "trade": "Printing Office",
        "identity": "Chicago American", "grade": "reconstructed",
        "why": (
            "The paper was twenty-three days old on the scene date and no advertisement "
            "of its own is in the pages read. A newspaper office announced the PAPER — the "
            "Democrat's own imprint does exactly that — so the board carries the title and "
            "the trade, in the register the pages evidence. T. O. Davis's name is on the "
            "record and deliberately not on the board: a paper's office was known by its "
            "paper. Reconstructed."
        ),
    },
    # chicago_democrat_office HAD AN ENTRY HERE AND IT IS GONE (T-1064). The board read
    # CHICAGO DEMOCRAT / Printing Office / South Water & Clark Streets off the paper's own
    # imprint, which is a good citation for where the Democrat was PRINTED IN 1833 and not
    # for what stood on that wall on 1 July 1835 — the press had left the corner by then
    # (T-0403), so clause 8 refuses the frontage and VACATED_NAMES carries the whole
    # argument. The wording is deleted rather than left standing unused, because a fully
    # lettered entry sitting here is an invitation to re-select the frontage and paint it.
    "clybourn_slaughterhouse": {
        "name": "A. CLYBOURNE", "trade": "Slaughtering & Packing",
        "identity": "Clybourne", "grade": "reconstructed",
        "why": (
            "No advertisement for this plant is in the pages read. Andreas has Clybourne "
            "killing for the garrison from 1827 and packing commercially from 1833, and "
            "\"packing\" is the trade's own word in this town — Newberry & Dole's own "
            "advertising uses it. The record's label calls the building a \"Log "
            "Slaughter-House\", which is this project describing walls; a drover reading "
            "the front needed the firm and the trade. Reconstructed."
        ),
    },
    "dole_warehouse_south": {
        "name": "GEO. W. DOLE", "trade": "Forwarding & Commission Merchant",
        "trade_short": "Forwarding & Commission", "identity": "Dole",
        "grade": "reconstructed",
        "why": (
            "The firm NEWBERRY & DOLE advertises in both 1833 and 1835 and its warehouse "
            "on the north bank carries that firm's own line. THIS building is Dole's own "
            "1832 warehouse and slaughter yard on the south side, and no advertisement in "
            "the pages read is signed by Dole alone — so the trade words are the firm's "
            "and the single-partner line is ours. Reconstructed for that reason rather "
            "than for any doubt about the trade."
        ),
    },
    "elston_soap_candle_manufactory": {
        "name": "DANIEL ELSTON & CO.", "trade": "Chicago Soap and Candle Manufactory",
        "trade_short": "Soap & Candle Manufactory", "identity": "Elston",
        "grade": "inferred", "sources": ["chicago_democrat_1833_11_26"],
        "why": (
            "The firm's own advertisement heads itself \"Chicago Soap and Candle "
            "Manufactory\" over \"DANIEL ELSTON & CO.\", and pays cash for tallow and for "
            "house ashes. It is in the committed issue of 26 November 1833 as well as in "
            "the owner's pages — with one caveat that travels with the name and is the "
            "committed source record's own: the word after the ampersand is OBLITERATED BY "
            "AN INK BLOT, and \"Co.\" is a reasonable expansion rather than a reading. "
            "Graded `inferred` for that, and because an advertisement is not a description "
            "of a board."
        ),
    },
    "exchange_coffee_house": {
        "name": "EXCHANGE COFFEE HOUSE", "trade": "Public House",
        "identity": "Exchange", "grade": "reconstructed",
        "why": (
            "No advertisement for this house is in the pages read. \"Public House\" is E. "
            "Wentworth's own trade line on the 1833 page and is the period's word for what "
            "this building was; the house name is the one Mark Beaubien's successors "
            "christened it with in 1834. A coffee house of these years lodged and fed "
            "people, and the record's own note says so. Reconstructed."
        ),
    },
    "john_holbrook_store": {
        "name": "JOHN HOLBROOK", "trade": "Clothing, Boots & Shoes",
        "trade_short": "Clothing & Boots", "place": "Wholesale & Retail",
        "identity": "Holbrook", "grade": "inferred",
        "sources": ["chicago_democrat_1833_1835", "chicago_american_1835"],
        "why": (
            "THE WORDING IS THE ADVERTISEMENT'S OWN HEAD, AND TWO PAPERS SET IT. The "
            "Chicago Democrat of 1835-06-10 heads the column \"[C]L[O]T[H]ING, BOOTS & "
            "SHOES, WHOLESALE AND RETAIL\" and signs it \"JOHN HOLBROOK\" (page 3 "
            "column 2, claim chicago_democrat_1835_06_10#c010); the Chicago American of "
            "1835-06-13 heads the same card \"[H]at[s], Clothing, Boo[ts and Shoes \u2026] "
            "WHOLESALE & [RETAIL]\" (claim chicago_american_1835_06_13#c012). Man, then "
            "trade, which is the register T-0130 fixed this table in, and the words are "
            "his own rather than this project's label for them. THE THIRD LINE IS THE "
            "TERMS AND NOT THE STREET: both printings set WHOLESALE AND RETAIL in their "
            "own head, and it is the thing a trader passing the door needed to know. THE "
            "COUNT OF DOORS IS DELIBERATELY NOT ON THE BOARD \u2014 'one door from "
            "Dearborn street' is how a newspaper reader FINDS the shop, and a customer "
            "standing in front of the board has already found it. THE READING IS "
            "TRANSCRIPTION-MEDIATED, flagged under the owner's ruling of 2026-08-28, with "
            "the brackets left in. WHAT KEEPS THIS `inferred` RATHER THAN BETTER is that a "
            "transcription is not a page image; UPGRADE IT TO `attested` when either "
            "paper's scans are committed as a source record and this note can cite the "
            "plate."
        ),
    },
    "frederick_thomas_shop": {
        "name": "FREDERICK THOMAS", "trade": "Druggist & Apothecary",
        "trade_short": "Druggist", "place": "Drugs, Paints & Dye Stuffs",
        "identity": "Thomas", "grade": "inferred",
        "sources": ["chicago_american_1835"],
        "why": (
            "HIS OWN HEADING, AND IT IS ALREADY SET LIKE A SIGNBOARD: \"FREDERIC[K] "
            "THOMA[S], D[r]ug[gi]st and Apothec[ary], W[at]er Street\" \u2014 The Chicago "
            "American, 1835-07-04, page 4 column 5, claim chicago_american_1835_07_04#c005, "
            "over the dateline \"Chicago, June [2]d, 18[35]\". Man, then trade, which is "
            "the register T-0130 fixed this table in, and the two words of the trade are "
            "his own rather than this project's label for it. THE THIRD LINE IS THE GOODS "
            "AND NOT THE STREET, DELIBERATELY. His June printings head themselves \"[Drugs "
            "and] PAINTS\" and keep \"Chemicals, Perfumery [and] Dye Stuffs\" "
            "(1835-06-08 page 3 column 6, claim #c016; 1835-06-13 page 4 column 6, claim "
            "#c018), so the line is quoted stock. The street is NOT put on this board "
            "because the transcription cannot read it: 1835-06-13 gives \"a[t the] "
            "Drawbridge, W[ater?] [s]t[r]eet\" with the question mark the transcription "
            "itself set, and a store at the drawbridge could front either bank \u2014 the "
            "extraction refuses to record a street for that reason and a signwriter's "
            "board is not the place to invent one. THE READING IS TRANSCRIPTION-MEDIATED, "
            "flagged under the owner's ruling of 2026-08-28, with the brackets left in. "
            "WHAT KEEPS THIS `inferred` RATHER THAN BETTER is the same thing that keeps "
            "Goss & Cobb's there: an advertisement heading is still not a description of a "
            "signboard, and nobody records that this shop announced itself at all."
        ),
    },
    "goss_cobb_saddlery": {
        "name": "S. B. COBB", "trade": "Saddle, Harness & Trunk Manufactory",
        "place": "Lake & Canal Streets", "identity": "Cobb",
        "grade": "inferred",
        "sources": ["chicago_american_1835", "chicago_democrat_1833_11_26"],
        "why": (
            "THIS BOARD USED TO LETTER A FIRM THAT NO LONGER EXISTED ON THE SCENE DATE, "
            "AND THE CHICAGO AMERICAN IS WHAT SAYS SO. Its first two issues carry the "
            "dissolution — \"NOTICE. [Th]e co-partnership heretofore [existing under] the "
            "firm of Go[ss] & Cob[b] [is] this day [dis]solved by m[ut]ual consent. "
            "OL[IVE]R GOS[S]. S. B. [C]O[BB]. Chicago, Feb. 18, 183[5].\" — four and a "
            "half months before 1 July 1835. Beside it on the same page is Cobb's own "
            "card, and the board is now lettered from ITS heading rather than the 1833 "
            "one: \"[S]A[D]DLE, HARNESS & TRUNK M[anufa]c[tor]y. S[. ]B[. ]COB[B] "
            "[w]il[l] [c]o[nt]in[ue] the [above business] at his shop\" "
            "(`chicago_american_1835_06_13#c016`, page 3 column 6; the same card is set "
            "on 1835-06-08 and again on 1835-07-11, ten days after the scene date). "
            "THE PLACE LINE IS STILL THE DEMOCRAT'S, and deliberately: the American loses "
            "the cross street in all three printings, so \"Lake & Canal Streets\" comes "
            "from the 1833 advertisement that this record's position is derived from and "
            "not from the 1835 ones. T-0305 holds that cross street open on the page "
            "images. WHAT KEEPS THE WORDING `inferred` is unchanged and is not about "
            "which paper it came from: an advertisement heading is still not a "
            "description of a signboard."
        ),
    },
    "h_jones_store": {
        "name": "JONES", "trade": "Grocery & Provision Store",
        "identity": "Jones", "grade": "inferred",
        "sources": ["chicago_democrat_1833_11_26"],
        "why": (
            "The advertisement is headed \"Grocery & Provision Store\" and signed by Jones "
            "— which is the board, in the order the trade wrote it. THE INITIAL IS "
            "DELIBERATELY NOT PAINTED, and that is this record refusing to decide "
            "something its own source record refuses to decide: Andreas writes \"H. "
            "Jones\", the advertisement in the committed issue reads \"B. JONES\", and the "
            "structure record carries the surname and not the initial because B and H are "
            "among the easiest letters to confuse in a display face of this period on a "
            "damaged sheet. A board that picked one would be the signage layer settling a "
            "question the dataset has left open."
        ),
    },
    "harmon_loomis_store": {
        "name": "HARMON, LOOMIS & CO.", "trade": "Dry Goods, Groceries & Hardware",
        "trade_short": "Dry Goods & Groceries", "identity": "Harmon",
        "grade": "inferred",
        "why": (
            "THE 1835 LINE, PREFERRED OVER THE 1833 ONE. The firm advertises in 1835 as "
            "\"HARMON, LOOMIS & CO.\" under the head \"New Goods!\", offering \"Dry Goods, "
            "Groceries and Hard Ware\"; the 1833 pages carry the same house as \"C. & I. "
            "HARMON\" with \"Dry Goods, Crockery, Hardware, Wet and Dry Groceries\" and "
            "again as \"HARMON, LOOMIS & CO.\". The later name is the one standing on the "
            "scene date, and the record's own `aka` already carries both. " + PENDING
        ),
    },
    "hogan_store": {
        "name": "BREWSTER, HOGAN & CO.", "trade": "Forwarding & Commission Merchants",
        "trade_short": "Forwarding & Commission", "place": "Chicago—Illinois",
        "identity": "Hogan", "grade": "inferred",
        "why": (
            "THE IDENTITY IS CORRECTED, NOT JUST THE WORDING. The firm's own advertisement "
            "reads \"BREWSTER, HOGAN & CO. Forwarding & Commission MERCHANTS, "
            "Chicago—Illinois\", and adds dry goods and groceries below. Our label, "
            "\"Hogan's Store\", is a shorthand for one partner; the building's own record "
            "already knows better and lists \"Brewster, Hogan & Co.'s store\" in its `aka` "
            "and names the firm in its change note — the log store was partitioned, post "
            "office on one side and this firm's store on the other. THE PAGES ALSO "
            "DISTINGUISH A SECOND HOGAN and this board is not him: \"J. S. C. HOGAN\", "
            "\"Dry Goods, Groceries, Hardware, Crockery and Glass Ware\", \"South Water "
            "Street, one door below Dearborn\" — a different trade at a different address "
            "from this building at the Lake Street junction. Whether the model should ALSO "
            "carry J. S. C. Hogan's South Water store is a placement question and is "
            "raised, not silently answered. " + PENDING
        ),
    },
    "jh_kinzie_forwarding_store": {
        "name": "JOHN H. KINZIE", "trade": "Forwarding & Commission Merchant",
        "trade_short": "Forwarding & Commission", "place": "Agent, Troy & Erie Line",
        "identity": "Kinzie", "grade": "inferred",
        "why": (
            "His own line, and the 1835 form of it: \"JOHN H. KINZIE, Forwarding & "
            "Commission Merchant … Agent for the Troy & Erie Line\", the 1833 pages "
            "carrying the same man as a \"Storage, Forwarding & Commission Merchant\" for "
            "the same line. The agency is on the third line because that is what a "
            "shipper walking the street needed to read; it is the place line's slot and "
            "it does the place line's job. " + PENDING
        ),
    },
    "kinzie_hunter_warehouse": {
        "name": "KINZIE & HUNTER", "trade": "Forwarding & Commission Merchants",
        "trade_short": "Forwarding & Commission", "identity": "Kinzie",
        "grade": "reconstructed",
        "why": (
            "No advertisement for this firm is in the pages read. The record's own "
            "function is `forwarding_commission_warehouse` and its note says the trade is "
            "held by association with the neighbouring dock rather than by any statement — "
            "Andreas separately has a Kinzie, Hunter & Co. in the LUMBER trade in these "
            "years. So the trade words are the town's own, the firm is the record's, and "
            "the whole line is reconstructed. If the lumber reading is right the board "
            "should read \"Lumber Dealer & Commission Merchant\", which is David Carver's "
            "own 1835 line and is the form to reach for; that is a research question, not "
            "a wording one."
        ),
    },
    "madore_beaubien_house": {
        "name": "MADORE BEAUBIEN", "trade": "Dry Goods & Groceries",
        "identity": "Beaubien", "grade": "reconstructed",
        "why": (
            "No advertisement for him is in the pages read. He was licensed as a merchant "
            "in 1831 — the year the building went up — and the record's own `aka` carries "
            "\"Madore Beaubien's store\", so the board carries the man and the plainest of "
            "the town's own counter trades. The record's label, \"Madore Beaubien's Log "
            "House\", is this project naming a building by its walls. Reconstructed."
        ),
    },
    "mansion_house": {
        "name": "MANSION HOUSE", "trade": "Public House", "identity": "Mansion",
        "grade": "reconstructed",
        "why": (
            "No advertisement for this house is in the pages read, though the 1833 pages "
            "locate Matthias Mason's smithy \"nearly opposite Graves' Tavern\", which is "
            "this building under its keeper's name. \"Public House\" is E. Wentworth's own "
            "1833 trade line. The house name is the one the record carries at the scene "
            "date, when Markle rather than Graves had it. Reconstructed."
        ),
    },
    "mason_blacksmith_shop": {
        "name": "MATTHIAS MASON & CO.", "trade": "Blacksmithing",
        "identity": "Mason", "grade": "inferred",
        "sources": ["chicago_democrat_1833_11_26"],
        "why": (
            "The firm's own advertisement is headed \"Blacksmithing Business\" over "
            "\"MATTHIAS MASON & CO.\", on \"Main-street, nearly opposite Graves' Tavern\". "
            "The board takes the firm and the trade word and NOT the address: "
            "\"Main-street\" is a street name this project does not otherwise hold, "
            "recorded as a finding in docs/RESEARCH/residents_1835.md § 7, and lettering "
            "it here would be the signage layer asserting a street the streets layer does "
            "not carry."
        ),
    },
    "miller_house": {
        "name": "MILLER HOUSE", "trade": "Store", "identity": "Miller",
        "grade": "reconstructed",
        "why": (
            "The hardest board in the set, and the wording is deliberately thin. The "
            "record's function on the scene date is a store with the keeper living over "
            "it; its occupants are NOT attested at that date; Samuel Miller had removed to "
            "the place that became Michigan City and the tavern had reverted to store use "
            "after 1832. So there is no proprietor to letter, and the board carries the "
            "name the settlement knew the building by — \"Miller House\", \"Miller's "
            "Tavern\", \"Fork Tavern\" are its own `aka` — over the plainest period word "
            "for what it was doing. Inventing a keeper or a stock would be worse than a "
            "thin board. Reconstructed."
        ),
    },
    "miller_tannery": {
        "name": "JOHN MILLER", "trade": "Tannery", "identity": "Miller",
        "grade": "reconstructed",
        "why": (
            "No advertisement for this tan-yard is in the pages read. The function is the "
            "best-attested thing about the building — \"a log house … that he used as a "
            "tannery, Chicago's first recorded factory\" — and the proprietor is named. "
            "The board carries the two and drops the walls. Reconstructed."
        ),
    },
    "new_york_house": {
        "name": "NEW YORK HOUSE", "trade": "Public House", "identity": "New York House",
        "grade": "reconstructed",
        "why": (
            "No advertisement for this house is in the pages read, and the two the "
            "Chicago American does carry are its TENANTS' — a physician and a travelling "
            "dentist, each giving \"the New York House\" as his address (1835-06-13, p. 3 "
            "cols. 2 and 3). That is evidence the house was a known landmark a reader "
            "could find, which is the argument for a board at all; it is not the house's "
            "own copy, so the trade line is not its own words. \"Public House\" is E. "
            "Wentworth's own 1833 trade line and the period's word for what this building "
            "was. Johnson and Stevens kept it and are not lettered, for the same reason "
            "W. H. Stow is not on the Western Hotel's board. Reconstructed."
        ),
    },
    "newberry_dole_slaughterhouse_south_branch": {
        "name": "NEWBERRY & DOLE", "trade": "Slaughtering & Packing",
        "place": "South Branch", "identity": "Newberry", "grade": "reconstructed",
        "why": (
            "The FIRM's own advertised line is the forwarding one and it is lettered on "
            "their warehouse. For this plant the pages give nothing: what is recorded is "
            "Andreas's sentence about a slaughter-house on the South Branch where three "
            "hundred cattle and fourteen hundred hogs were packed in its first season. So "
            "the firm is theirs and the trade line is ours, out of the town's own word for "
            "the trade. Reconstructed."
        ),
    },
    "newberry_dole_warehouse": {
        "name": "NEWBERRY & DOLE",
        "trade": "Storage, Forwarding & Commission Merchants",
        "trade_short": "Forwarding & Commission", "place": "Agents, Merchants Line",
        "identity": "Newberry", "grade": "inferred",
        "sources": ["chicago_democrat_1833_11_26"],
        "why": (
            "THE 1835 LINE, PREFERRED OVER THE 1833 ONE, and the 1833 one is in a "
            "committed source: \"NEWBERRY & DOLE, Forwarding & Commission MERCHANTS\" in "
            "the issue of 26 November 1833, which this project's own record calls \"the "
            "first contemporary document in this dataset and about as good as evidence of "
            "a trade gets, since the advertiser was paying for it and his customers had to "
            "be able to find him\". By 1835 the firm advertises as \"Storage, Forwarding "
            "and Commission Merchants\" and \"Agents for the Merchants Line\", and the "
            "agency goes on the third line because that is what a shipper needed off the "
            "river. " + PENDING
        ),
    },
    "peck_store": {
        "name": "P. F. W. PECK", "trade": "Dry Goods, Groceries & Hardware",
        "trade_short": "Dry Goods & Groceries", "place": "South Water Street",
        "identity": "Peck", "grade": "inferred",
        "why": (
            "The 1833 pages carry \"P. F. PECK\" at the corner of LaSalle and South Water "
            "with staple articles, salt, flour, butter and feathers, and the same man "
            "reports the town's prices current for the Democrat. The record independently "
            "has him \"advertising dry goods, hardware and groceries through 1834-35\", "
            "which is the trade line the board takes; the street is his own. Graded "
            "`inferred` and not better because the goods line is assembled from the record "
            "and the page rather than lifted whole off one advertisement. " + PENDING
        ),
    },
    "philo_carpenter_log_shop": {
        "name": "PHILO CARPENTER", "trade": "Drugs and Medicines",
        "trade_short": "Druggist", "identity": "Carpenter", "grade": "inferred",
        "sources": ["chicago_democrat_1833_11_26"],
        "why": (
            "HIS 1833 WORDS ON HIS 1832 SHOP, and the split is deliberate. The "
            "advertisement dated 22 November 1833 in the committed issue reads \"PHILO "
            "CARPENTER, CHICAGO—ILL. Will keep constantly on hand, a general assortment of "
            "DRUGS AND MEDICINES, Oils, Paints, Dye-Stuffs, &c. &c.\" — name first, trade "
            "second, which is the board. By 1835 he has rewritten himself as a \"Wholesale "
            "& Retail Druggist\" AT THE SIGN OF THE GOLDEN MORTAR on South Water Street, "
            "and that later line and that device go on the South Water frontage, not on "
            "this one. A FINDING THIS BOARD RAISES RATHER THAN BURIES: this record's own "
            "occupants block says NO SOURCE REACHED NAMES ANYONE IN THIS BUILDING IN 1835 "
            "and its change note calls the log shop's survival doubtful once he had the "
            "South Water store. If the shop had passed to another keeper by 1 July 1835, "
            "this board names the wrong man — which is a research question for the "
            "structure record, not a wording that can be fixed here. " + PENDING
        ),
    },
    "pierce_blacksmith_shop": {
        "name": "A. PIERCE", "trade": "Blacksmithing", "place": "Lake & Canal Streets",
        "identity": "Pierce", "grade": "reconstructed",
        "why": (
            "A FINDING RAISED RATHER THAN ADOPTED. The 1833 pages carry \"PIERCE & "
            "ABBOTT\" under the head \"New Blacksmith Shop\", which is very probably this "
            "smithy — but this project's record names Asahel Pierce alone as builder and "
            "proprietor and says nothing about a partner, and a signage layer is not the "
            "place to add one to a structure record. So the board letters the man the "
            "record carries, in the register the pages evidence, graded `reconstructed`; "
            "if the structure record adopts the partnership the board should become "
            "\"PIERCE & ABBOTT\" and rise to `inferred` with it. The street is the "
            "record's own `aka`."
        ),
    },
    "pruyne_kimball_drugstore": {
        "name": "PRUYNE & KIMBALL", "trade": "Druggists",
        "place": "South Water Street", "identity": "Pruyne",
        "grade": "reconstructed",
        "why": (
            "No advertisement for this partnership is in the pages read, and the trade "
            "word is borrowed rather than theirs: \"Druggist\" is Carpenter's own 1835 "
            "self-description, which is what makes it the right period word for the "
            "town's second drug store. Andreas gives the partnership and the street and "
            "nothing else. A NEAR-MISS WORTH RAISING: the 1835 pages carry \"P. PRYNE & "
            "CO.\" twice, both times in the grocery and dry-goods line rather than the "
            "drug line — whether that is the same Pruyne is a research question this "
            "board does not answer. Reconstructed."
        ),
    },
    "robert_kinzie_store": {
        "name": "R. A. KINZIE", "trade": "Dry Goods & Groceries", "identity": "Kinzie",
        "grade": "reconstructed",
        "why": (
            "No advertisement for him is in the pages read. The record has a storehouse "
            "dealing in groceries and Indian goods and its keeper among the town's "
            "licensed traders, and it warns that the trade's continuity past the 1833 "
            "treaty is not attested. The board therefore carries the counter trade the "
            "town's own advertising uses and says nothing about the Indian trade, which "
            "the record will not stand behind at the scene date. Reconstructed."
        ),
    },
    "sauganash_hotel": {
        "name": "SAUGANASH HOTEL", "trade": "Public House", "identity": "Sauganash",
        "grade": "reconstructed",
        "why": (
            "No advertisement for this house is in the pages read. \"Public House\" is E. "
            "Wentworth's own 1833 trade line. The house name is the one the town used and "
            "the record carries; its earlier names, Eagle Exchange Tavern and Chicago "
            "Hotel, are in its `aka` and belong to earlier years. Reconstructed."
        ),
    },
    "steamboat_hotel": {
        "name": "JOHN DAVIS", "trade": "Steam-Boat Hotel",
        "place": "North Water Street", "identity": "Steamboat Hotel",
        "grade": "inferred",
        "why": (
            "THE PAGES AND THE RECORD SAY THE SAME THING INDEPENDENTLY, which is the "
            "strongest agreement in the set. The 1835 pages carry \"JOHN DAVIS, Steam-Boat "
            "Hotel, North Water Street\"; Andreas, separately, has \"The Steamboat Hotel, "
            "on North Water Street, near Kinzie, was kept in 1835 by John Davis\". Man, "
            "house, street — the board is the advertisement. The hyphen is the "
            "advertisement's own spelling and is kept. " + PENDING
        ),
    },
    "thomas_church_store": {
        "name": "THOMAS CHURCH", "trade": "Dry Goods & Groceries", "identity": "Church",
        "grade": "reconstructed",
        "why": (
            "No advertisement for him is in the pages read. The source names him as the "
            "BUILDER of the first store building on Lake Street and says nothing about who "
            "kept it or what it sold — the record says so in as many words. So the board "
            "carries the name the record carries over the plainest of the town's own "
            "counter trades, and it is reconstructed twice over: the wording is ours, and "
            "so is the assumption that the builder was the keeper."
        ),
    },
    "tremont_house_1": {
        "name": "TREMONT HOUSE", "trade": "Public House", "identity": "Tremont House",
        "grade": "reconstructed",
        "why": (
            "No advertisement for the house is in the pages read, though attorneys on them "
            "give their offices as \"opposite the Tremont House\", which is the house being "
            "used as a landmark by strangers — exactly what a hotel's board is for. "
            "\"Public House\" is E. Wentworth's own 1833 trade line. The record's "
            "parenthetical, \"(the first)\", is this project telling itself which of three "
            "Tremonts it models and was never on a board. Ira Couch kept it and is "
            "deliberately not lettered: an inn of this town announced its HOUSE. "
            "Reconstructed."
        ),
    },
    "western_hotel": {
        "name": "WESTERN HOTEL", "trade": "Public House", "identity": "Western Hotel",
        "grade": "reconstructed",
        "why": (
            "No advertisement for this house is in the pages read. \"Public House\" is E. "
            "Wentworth's own 1833 trade line, and this is the west-side wagon-trade house "
            "— \"the stopping place for all the farmers town from the west\" — whose "
            "custom came off the road and had to read the board from it. W. H. Stow built "
            "it and kept it, and is not lettered for the same reason Ira Couch is not. "
            "Reconstructed."
        ),
    },
}

# What a wording may be graded. `attested` is deliberately absent: see PENDING.
WORDING_GRADES = {"inferred", "reconstructed"}

# Clause 6, added 2026-08-18 with ticket T-0082 and kept by T-0066. A frontage whose OWN
# reference view shows a board on a POST at the corner does not also get a second board
# hung on its wall by this rule. The Green Tree is the only one: images 6 and 7 of the
# owner's brief (data/sources/assets/owner_brief_2026_08_18/README.md) both show one
# board at this inn, both put it on a post, and image 7 says GREEN TREE is on it — which
# is now drawn, lettered, by the frontage layer (data/frontage/green_tree_frontage.json,
# docs/LIBERTIES.md L135). That board is the town's exemplar for the post mounting this
# record now uses elsewhere; drawing a second sign here would be the town making the same
# claim twice.
POST_BOARD_IDS = {
    "green_tree_tavern": (
        "it carries a NAMED board on its own post at the street corner instead. "
        "Images 6 and 7 of data/sources/assets/owner_brief_2026_08_18/README.md both "
        "show ONE board at this inn, post-mounted at the corner and lettered GREEN "
        "TREE; it is drawn from data/frontage/green_tree_frontage.json by "
        "renderers/web/js/frontage.js (T-0082, docs/LIBERTIES.md L135). That board is "
        "the exemplar this record's own post mounting is copied from. A second sign "
        "here would be this layer drawing the same claim a second time."
    ),
}

# Clause 8, added 2026-09-12 with ticket T-1064. A frontage whose record is NAMED for a
# trade the corpus has followed OUT of the building before 1 July 1835. The name stays on
# the card — it is how the building is found, and a town goes on calling a corner by the
# shop that used to be on it — but a board is read in the present tense by somebody
# standing in front of it, so it is refused and the wall is left blank. The reason each
# one is here is written out, because the substitute is the trap: the replacement a
# frontage like this invites is lettered off a notice from a year before the scene date,
# and a notice that OFFERS a store for sale does not attest who kept it on the day.
VACATED_NAMES = {
    "chicago_democrat_office": (
        "the name on this record belongs to a tenancy that had LEFT before the scene "
        "date, so there is nothing here to letter. The Chicago Democrat's colophon "
        "gives this corner on 1833-11-26, 1834-01-07, 1834-08-27, 1834-09-17 and "
        "1834-12-03 and then prints the office 'over Messrs. Jones & King['s] "
        "Hard[ware store]' in South Water street on 1835-05-20 and again on 1835-08-05 "
        "(T-0403), so the press was gone seven weeks at the latest before 1 July 1835 "
        "and CHICAGO DEMOCRAT / Printing Office painted on this front asserted a trade "
        "the paper itself had printed its way out of. The RECORD KEEPS THE NAME — a "
        "label is a caption and not a claim about who is inside on a day — and this "
        "record's `function` has narrowed to `store`, which is the half of it the "
        "corpus does not follow out of the door. NOTHING IS LETTERED IN ITS PLACE, "
        "deliberately. The only name the corpus offers for what traded here afterwards "
        "is W. Kimball's, and it comes out of chicago_democrat_1834_10_08 c005, which "
        "OFFERS 'the store now occupied by W. Kimball, and as the office of the "
        "Democrat' for sale with possession in November 1834 — a landlord clearing the "
        "building, not a report of who kept the counter eight months later. Painting "
        "W. KIMBALL here would assert at the scene date the very tenancy that source "
        "declines to report, which is worse than the board it replaced. The wall is "
        "left blank until something says who stood behind it."
    ),
}


# HOW A SIGN IS DRAWN, and why these numbers are here rather than in a renderer. The
# bracket board's arm, drop and hangers are still the wolf sign's own geometry, copied
# from generators/archetypes/log_dwelling.py::_sign, so the town has one convention for
# hanging a board. Everything T-0066 adds — the awning hood, the wall board's cap, the
# post's stand, the painted band — is invented here in every dimension and the record
# carries each number so the renderer can draw it and this file can bound its reach.
ARM_M = 1.15            # the bracket arm, out of the wall
DROP_M = 0.20           # hangers, arm to board
BOARD_T_M = 0.05
OFFSET_M = 1.7          # a hanging board sits this far off the facade's centre
END_CLEAR_M = 0.6       # and never closer than this to the end of the wall
EAVE_CLEAR_M = 0.30
MAX_HEIGHT_M = 2.55

AWNING_PROJECTION_M = 1.45   # the hood over the door, out of the wall
AWNING_DROP_M = 0.34         # its outer edge below its inner one — the fall of a hood
AWNING_MARGIN_M = 0.45       # hood wider than the board it shelters, each side
WALL_BOARD_PROUD_M = 0.02    # a board fixed flat on the front stands this far off it
BAND_PROUD_M = 0.03          # a name painted on the boards, this far proud to draw
BAND_FOOT_M = 2.30           # and its foot this high, clear of any door head
BAND_EAVE_CLEAR_M = 0.25     # unless the wall has not the height, then under the eave
POST_STAND_M = 1.90          # a post stands this far out from the facade
POST_CLEAR_M = 1.00          # and must leave this much between it and the track edge
POST_ARM_M = 1.30

# The board's own size. A board is as long as its name needs and no longer, inside the
# range the mounting allows and inside the frontage it hangs on.
BOARD_SIZE = {
    "bracket_board": {"base": 0.72, "min": 0.88, "max": 1.46, "aspect_mul": 1.00},
    "awning_board": {"base": 0.84, "min": 1.02, "max": 1.66, "aspect_mul": 1.18},
    "wall_board": {"base": 1.00, "min": 1.24, "max": 2.30, "aspect_mul": 1.45},
    "post_board": {"base": 0.88, "min": 1.10, "max": 1.58, "aspect_mul": 1.05},
    "facade_painted": {"base": 1.70, "min": 2.10, "max": 4.30, "aspect_mul": 2.30},
}
PER_LETTER_M = 0.030
BOARD_H_MIN_M = 0.34
BOARD_H_MAX_M = 1.15
FACADE_MIN_FRONTAGE_M = 3.0   # under this a painted band has nowhere to run

# T-0130: a board is now sized off its LONGEST LINE rather than off the whole string,
# because the wording is a hierarchy of two or three lines and not one run of words. Two
# corrections come with that.
#
#  * A second and third line want width as well as height — a firm and a trade set one
#    over the other read wider than either alone — so each extra line adds this much.
#  * They want height too, but ONLY where the board is fixed to the building. A board
#    hung over a footway cannot grow downwards without hanging into the people walking
#    under it, and its head is already fixed by the eave; a board fixed flat on a wall
#    and a name painted across a front have the whole elevation to grow into.
LINE_WIDTH_BONUS_M = 0.30
LINE_H_MUL = {1: 1.00, 2: 1.22, 3: 1.42}
LINE_H_MOUNTINGS = {"wall_board", "facade_painted"}

# A PAINTED DEVICE NEEDS BOARD, and it must not take it off the lettering. Exactly one
# board in this town carries one, and it gets this much extra plank to stand in — added
# to the ceiling as well as to the want, because "as long as its name needs and no
# longer" becomes "as long as its name and its device need" when a shop has both.
DEVICE_W_M = 0.38
DEVICE_SHARE = 0.30       # of the board's face, reserved for the device, left-hand end

# Two signs closer together than this must not share a mounting, a style or a ground
# colour. 40 m is about a platted lot and a half — near enough that a walker sees both
# at once, which is the test the owner set: *no two are alike on a street*.
NEIGHBOUR_M = 40.0

# The post's street test, borrowed whole from tools/generate_frontage_works.py so that
# two layers deciding "may something stand in this street" decide it the same way.
STREET_REACH_M = 22.0
FRONTAGE_DOMINANCE = 0.5

# --- THE OPENINGS A FLAT BOARD MUST STAY OFF (T-0459) ------------------------
#
# The owner reported from the dev preview that boards sit over doors and over
# windows on walls with blank face going spare — the Sauganash Hotel's is the one
# in the screenshot, over a window bay — and a sweep found it was not some of them
# but ALL TWENTY of the flat-mounted boards. The cause was one missing input: this
# file mentions doors sixteen times, every one of them trade reasoning ("an office
# is a door among doors"), and never once as geometry. It reasoned carefully about
# WHICH door a board belonged beside and had no idea where any of them were.
#
# The owner allowed three moves, in this order of preference, and this is that
# order: MOVE the board onto blank face on the same wall; RESHAPE it — the same
# copy on a longer, narrower board, since nothing in the sources fixes a sign's
# aspect and a signwriter letters what fits; or SHRINK it onto the door front,
# which is what a modest office took anyway. Nothing here changes a word of the
# copy: the rectangle moves, and the lettering scales with it.
SIGN_CLEAR_M = 0.10       # blank face that has to show around a board, every side
SIGN_END_CLEAR_M = 0.20   # ...and at the ends of the wall itself
RESHAPE_H_FLOOR_M = 0.34  # narrowest a reshaped board may be lettered on
RESHAPE_H_STEP_M = 0.02
RESHAPE_MAX_ASPECT = 9.0  # a board longer than this is a batten, not a sign
WALL_CAP_CLEAR_M = 0.09   # the rain cap `signage.js` stands over a wall board
DOOR_KINDS = ("door", "shop_door")
DOOR_BOARD_MARGIN_M = 0.07   # stile left showing either side of a board on a leaf
DOOR_BOARD_DROP_M = 0.10     # ...and below the head it hangs under
DOOR_BOARD_H_MIN_M = 0.20
DOOR_BOARD_PROUD_M = 0.06    # clear of the leaf and its battens, not of the wall

# Clause 5 and the log_dwelling default, mirrored: `wall_height_m` is optional on a
# record and the archetype resolves 2.5 m for one storey, 4.6 m for more. A board
# hung off a wall this project never measured is hung off the same number the wall
# itself is drawn at, which is the only way the two can agree.
DEFAULT_WALL_M = {1: 2.5, None: 2.5}
DEFAULT_WALL_MULTI_M = 4.6


def _separation(signs: list) -> list:
    """Every pair of boards within `NEIGHBOUR_M` that shares a mounting, a style or a
    ground colour — the promise at the head of this file, MEASURED (T-0405).

    It used to be assumed. The de-confliction loop below walks a cycle and takes the
    first mounting a neighbour has not taken, and there are two ways that can still
    land on a repeat: a class whose cycle is ONE mounting long (a works paints its
    front and hangs nothing, so two works on one corner must both be painted), and a
    cycle whose every entry a wall refused, where the loop's last step is taken anyway.
    The first is the rule working; the second is the rule failing. Returning the pairs
    rather than a bare true/false is what lets `_neighbours_differ` tell them apart and
    the record carry the permitted ones by name.
    """
    pairs = []
    for i, a in enumerate(signs):
        for b in signs[i + 1:]:
            gap = math.hypot(a["anchor_local_enu_m"][0] - b["anchor_local_enu_m"][0],
                             a["anchor_local_enu_m"][1] - b["anchor_local_enu_m"][1])
            if gap > NEIGHBOUR_M:
                continue
            shares = []
            if a["mounting"] == b["mounting"]:
                shares.append(("mounting", a["mounting"]))
            if a["style"]["id"] == b["style"]["id"]:
                shares.append(("style", a["style"]["id"]))
            if a["style"]["ground"] == b["style"]["ground"]:
                shares.append(("ground", a["style"]["ground"]))
            for what, value in shares:
                only = min(len(MOUNTING_CYCLE[a["trade_class"]]),
                           len(MOUNTING_CYCLE[b["trade_class"]]))
                pairs.append({
                    "a": a["structure_id"], "b": b["structure_id"],
                    "gap_m": _round(gap, 1), "share": what, "value": value,
                    "allowed": what == "mounting" and only == 1,
                    "why": ("one of these two trades is a %s, and the %s cycle is a "
                            "single mounting — a works paints its front and hangs "
                            "nothing at all, so two of them inside "
                            "%.0f m cannot differ and this project would rather say so "
                            "than hang a plank on a works to make a rule come out."
                            % (min((a, b), key=lambda s: len(MOUNTING_CYCLE[s["trade_class"]]))["trade_class"],
                               min((a, b), key=lambda s: len(MOUNTING_CYCLE[s["trade_class"]]))["trade_class"],
                               NEIGHBOUR_M)
                           if what == "mounting" and only == 1 else
                           "NOT ALLOWED — the cycle had somewhere else to go."),
                })
    return sorted(pairs, key=lambda p: (p["a"], p["b"], p["share"]))


def _wordings_differ(signs: list) -> None:
    """NO TWO BOARDS IN THE TOWN MAY LETTER THE SAME THING (T-0405).

    The mounting decides how many lines a board has room for, so a board's TEXT is a
    tier of its SIGN_WORDING entry rather than the whole of it — and a re-deal that
    drops a line can therefore erase a distinction the table argued for. T-0130 is the
    case: Philo Carpenter's log shop is worded "Drugs and Medicines" and his South
    Water store "Wholesale & Retail Druggist" precisely so a walker can tell the two
    shops of one druggist apart, and both entries shorten to "Druggist". At two lines
    each, the two boards would read `PHILO CARPENTER / Druggist` and `PHILO CARPENTER /
    Druggist`, and the argument would be gone with nothing in the record saying it had
    been. The wording tiers are a decision of the table; the deal must not be able to
    undo one in silence, so it is refused here instead.
    """
    seen: dict[str, str] = {}
    for s in sorted(signs, key=lambda s: s["structure_id"]):
        first = seen.get(s["sign_text"])
        if first is not None:
            raise SystemExit(
                "SIGN WORDING COLLAPSED: %s and %s both letter %r. The mounting each "
                "was dealt has room for fewer lines than its SIGN_WORDING entry "
                "carries, and the tier they fall back to is the same one — so two "
                "boards the table deliberately words apart would read alike. Word the "
                "shorter tiers apart, or argue in the entry's own `why` why these two "
                "trades may say the same thing."
                % (first, s["structure_id"], s["sign_text"]))
        seen[s["sign_text"]] = s["structure_id"]


def _neighbours_differ(signs: list) -> list:
    """Assert the separation, and hand the permitted exceptions back for the record."""
    pairs = _separation(signs)
    broken = [p for p in pairs if not p["allowed"]]
    if broken:
        raise SystemExit(
            "SIGN SEPARATION: the rule at the head of this file promises that no two "
            "boards within %.0f m share a mounting, a style or a ground colour, and "
            "%d pair(s) do:\n%s"
            % (NEIGHBOUR_M, len(broken),
               "\n".join("  %s / %s at %.1f m share a %s (%s)"
                          % (p["a"], p["b"], p["gap_m"], p["share"], p["value"])
                          for p in broken)))
    return pairs


def _prove_locality() -> int:
    """ADMITTING ONE FRONTAGE MUST REACH ONLY ITS NEIGHBOURS (T-0405).

    The claim this file makes since T-0405 is that a board's deal is a function of its
    own id and of the boards it can SEE, so admitting a frontage in the middle of the
    town changes that frontage and any board whose `NEIGHBOUR_M` separation actually
    required a different deal — and no others. This proves it the only way a claim like
    that can be proved: every board in turn is withheld, the town is re-derived without
    it, and every difference is held against the distance from the board that was
    withheld. A difference further off than `NEIGHBOUR_M` is the defect T-0405 records.

    It was measured before the fix on the insertion the ticket names: admitting
    `frederick_thomas_shop` re-dealt eleven other boards, the furthest 904.4 m away,
    and four of them changed what they said.
    """
    base = build_record()[0]
    by_id = {s["structure_id"]: s for s in base}
    original = _candidates
    far = 0
    print("locality: withholding each of the %d boards in turn" % len(base))
    for sid in sorted(by_id):
        globals()["_candidates"] = lambda: (
            [c for c in original()[0] if c["sid"] != sid], original()[1])
        try:
            without = {s["structure_id"]: s for s in build_record()[0]}
        finally:
            globals()["_candidates"] = original
        anchor = by_id[sid]["anchor_local_enu_m"]
        for other, was in sorted(without.items()):
            now = by_id.get(other)
            if now is None:
                continue
            if (now["mounting"], now["sign_text"], now["style"]["id"]) == \
                    (was["mounting"], was["sign_text"], was["style"]["id"]):
                continue
            gap = math.hypot(now["anchor_local_enu_m"][0] - anchor[0],
                             now["anchor_local_enu_m"][1] - anchor[1])
            mark = "  " if gap <= NEIGHBOUR_M else "FAR"
            if gap > NEIGHBOUR_M:
                far += 1
            print("  %s %-30s reaches %-30s at %8.1f m%s"
                  % (mark, sid, other, gap,
                     "" if gap <= NEIGHBOUR_M else "  <-- OUTSIDE %.0f m" % NEIGHBOUR_M))
    if far:
        print("LOCALITY FAILED: %d reach(es) outside %.0f m" % (far, NEIGHBOUR_M))
        return 1
    print("locality: every reach is inside %.0f m" % NEIGHBOUR_M)
    return 0


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _round(x: float, places: int = 3) -> float:
    """Round toward a stable decimal so `--check` diffs bytes, not float noise."""
    return round(x + 0.0, places) + 0.0


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _rank(sid: str, n: int) -> int:
    """A stable integer for a structure id, for the style preference order.

    hashlib rather than `hash()`: Python randomises string hashing per process, and a
    record that re-derives differently on the next run is not a derivation.
    """
    return int(hashlib.sha1(sid.encode("utf-8")).hexdigest()[:8], 16) % n


def _to_enu(u: float, v: float, place: dict) -> tuple[float, float]:
    """A footprint coordinate to local ENU metres.

    docs/GLB-CONTRACT.md: polygon `u` → +X, polygon `v` → −Z, ENU `local_e` → +X and
    `local_n` → −Z, and the node's yaw is `-rotation_deg` about +Y. Composing those
    three lines is this function and nothing else; it is verified against the Green
    Tree, whose record says its front is on Canal to the west and whose rotation is
    270, by `--check` refusing any drift in the numbers below.
    """
    th = math.radians(-(place.get("rotation_deg") or 0.0))
    x, z = u, -v
    xr = x * math.cos(th) + z * math.sin(th)
    zr = -x * math.sin(th) + z * math.cos(th)
    return (place.get("local_e") or 0.0) + xr, (place.get("local_n") or 0.0) - zr


def _front_edge(polygon: list) -> tuple[float, float, float]:
    """The front wall: the footprint's max-`v` edge, as (u_min, u_max, v).

    Rotation 0 faces north and +v is north, so the wall a bearing points out of is
    the one at the largest v. Both L-shaped footprints in the set (Miller House, the
    Western Hotel) reach their full u-extent at that v, so the general case and the
    rectangle agree; a footprint that did not would be caught by the guard below.
    """
    vmax = max(p[1] for p in polygon)
    on = [p[0] for p in polygon if abs(p[1] - vmax) < 1e-6]
    if len(on) < 2:
        return 0.0, 0.0, vmax
    return min(on), max(on), vmax


def _nearest_on_path(pt, path) -> tuple[float, tuple[float, float]]:
    """(distance, foot) from a point to an open polyline in local ENU metres."""
    x, y = pt
    best = (float("inf"), (x, y))
    for i in range(len(path) - 1):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2))
        fx, fy = x1 + t * dx, y1 + t * dy
        d = math.hypot(x - fx, y - fy)
        if d < best[0]:
            best = (d, (fx, fy))
    return best


def _front_wall(sid: str) -> dict | None:
    """The front elevation of `sid` and everything standing on it, or None.

    None where the archetype has no reader in `facade_openings` — which is a
    different answer from "this wall is blank", and the caller treats it as one: it
    refuses to hang a board flat on a wall nobody has read rather than guessing.
    """
    path = STRUCTURES / f"{sid}.json"
    if not path.exists():
        return None
    st = _load(path)
    arch = st.get("archetype")
    if arch not in _RESOLVERS:
        return None
    for ph in st.get("phases", []):
        rng = ph.get("documented_range") or {}
        if rng.get("from", "") <= TARGET_DATE <= rng.get("to", "9999-99-99"):
            try:
                return facade_openings.front_wall(arch, _RESOLVERS[arch](ph, st))
            except Exception:      # noqa: BLE001 — a record the param check owns
                return None
    return None


def _fits(wall: dict, u: float, w: float, z0: float, z1: float) -> bool:
    """Is a board of this extent standing clear of everything on the wall?"""
    lo = wall["u0"] + SIGN_END_CLEAR_M
    hi = wall["u1"] - SIGN_END_CLEAR_M
    if u - w / 2 < lo - 1e-9 or u + w / 2 > hi + 1e-9:
        return False
    return not facade_openings.overlaps(
        wall, u - w / 2 - SIGN_CLEAR_M, u + w / 2 + SIGN_CLEAR_M,
        z0 - SIGN_CLEAR_M, z1 + SIGN_CLEAR_M)


def _nearest_clear(wall: dict, want_u: float, w: float,
                   z0: float, z1: float) -> float | None:
    """The centre nearest `want_u` at which a board of width `w` stands clear at
    this band, or None if the band is full.

    A wall is a rectangle with rectangles cut out of it, so "is there room" is one
    interval subtraction in `u`. Nearest rather than widest: a name belongs as close
    to the middle of its own front as the openings allow, and sliding it to the far
    end of the building to find the largest gap would answer the wrong question.
    """
    spans = facade_openings.clear_spans(wall, z0 - SIGN_CLEAR_M, z1 + SIGN_CLEAR_M,
                                        SIGN_CLEAR_M)
    lo = wall["u0"] + SIGN_END_CLEAR_M
    hi = wall["u1"] - SIGN_END_CLEAR_M
    best = None
    for a, c in spans:
        a, c = max(a, lo), min(c, hi)
        if c - a < w - 1e-9:
            continue
        u = _clamp(want_u, a + w / 2, c - w / 2)
        if best is None or abs(u - want_u) < abs(best - want_u):
            best = u
    return best


def _band_top(mounting: str, h: float, wall_height: float, head: float) -> float:
    """The top of a flat board of height `h`, by its mounting.

    A wall board hangs at the eave-clear height a board hangs at; a PAINTED NAME
    goes above the door head, at `BAND_FOOT_M`, dropping back under the eave only
    where the wall has not the height for both. Both rules are the ones this file
    already kept — they are gathered here because reshaping changes `h`, and a top
    computed once from the old height would float the new board.
    """
    if mounting != "facade_painted":
        return head
    top = min(BAND_FOOT_M + h, wall_height - BAND_EAVE_CLEAR_M)
    return max(top, h + 0.4)


def _has_flat_face(wall: dict, w_min: float) -> bool:
    """Could a board `w_min` wide be fixed flat on this wall at ANY height?

    Asked by the mounting cycle, before the wording and therefore before the board's
    real size is known, because "may a name be fixed flat here at all" is a fact
    about the building and not about what it says. A door counts: a board shrunk
    onto the leaf is the third of the owner's three moves and is still a flat
    mounting. An OPEN-SIDED shed passes neither test and is the case this exists
    for — a drying shed open along its whole length has no front to paint.
    """
    if any(o["kind"] in DOOR_KINDS for o in wall["openings"]):
        return True
    edges = sorted({0.0, wall["wall_height_m"]}
                   | {o["z0"] for o in wall["openings"]}
                   | {o["z1"] for o in wall["openings"]})
    for z0 in edges:
        z1 = z0 + BOARD_H_MIN_M
        if z1 > wall["wall_height_m"] + 1e-9:
            continue
        if _nearest_clear(wall, (wall["u0"] + wall["u1"]) / 2.0, w_min, z0, z1) \
                is not None:
            return True
    return False


def _tops(mounting: str, h: float, wall_height: float, head: float,
          want_top: float, openings: list) -> list:
    """Heights the head of a board of this height may take, nearest the wanted one
    first.

    The candidates are not a scan: they are the edges of what is already on the wall
    — just under an opening, just over it — plus the wanted height and the highest
    the mounting allows. A wall is mostly blank, so the interesting heights are the
    few where the blankness starts and stops.
    """
    lo = h + 0.40
    hi = (wall_height - BAND_EAVE_CLEAR_M) if mounting == "facade_painted" else head
    cands = {want_top, hi}
    for o in openings:
        cands.add(o["z0"] - SIGN_CLEAR_M)
        cands.add(o["z1"] + SIGN_CLEAR_M + h)
    ok = sorted({round(t, 4) for t in cands if lo - 1e-9 <= t <= hi + 1e-9},
                key=lambda t: (abs(t - want_top), -t))
    return ok


def _fit_flat(wall: dict | None, mounting: str, want_u: float, w: float, h: float,
              wall_height: float, head: float, w_ceiling: float) -> dict:
    """Place a flat-mounted board clear of the openings behind it.

    Returns the placement and, whatever the outcome, the account of it: what the
    board would have covered where it was going, and what was done about it. The
    three moves are the owner's, in his order of preference.
    """
    cap = WALL_CAP_CLEAR_M if mounting == "wall_board" else 0.0
    top = _band_top(mounting, h, wall_height, head)
    out = {"u": want_u, "w": w, "h": h, "top": top, "proud_m": None, "on": None,
           "action": "already clear", "covered": [], "note": None}
    if wall is None:
        out["action"] = "no reading"
        out["note"] = ("no rule reads this archetype's front elevation, so the "
                       "board is left where the trade put it and this is the "
                       "record of that")
        return out

    covered = sorted({o["kind"] for o in facade_openings.overlaps(
        wall, want_u - w / 2 - SIGN_CLEAR_M, want_u + w / 2 + SIGN_CLEAR_M,
        top - h - SIGN_CLEAR_M, top + cap + SIGN_CLEAR_M)})
    out["covered"] = covered
    if _fits(wall, want_u, w, top - h, top + cap):
        return out

    # 1. MOVE IT — the same board, on blank face on the same wall. Along the wall
    # first and up or down it second, which is what "the same height if it can" means
    # in practice: the candidates are ordered by how far the board's head has to
    # travel, and the first that clears wins, so a board that only needs to slide
    # sideways never rises. A painted band may go as high as the eave allows because
    # that is where paint goes on a front; a hung BOARD may not go above `head`,
    # which is the eave-clear human height this file has always hung boards at.
    for top2 in _tops(mounting, h, wall_height, head, top, wall["openings"]):
        u = _nearest_clear(wall, want_u, w, top2 - h, top2 + cap)
        if u is None:
            continue
        out["u"], out["top"], out["action"] = u, top2, "moved"
        moves = []
        if abs(u - want_u) > 5e-3:
            moves.append(f"{abs(u - want_u):.2f} m along the front")
        if abs(top2 - top) > 5e-3:
            moves.append(f"{abs(top2 - top):.2f} m "
                         + ("up" if top2 > top else "down") + " it")
        out["note"] = (f"moved {' and '.join(moves)}, off {' and '.join(covered)}, "
                       "onto blank face")
        return out

    # 2. RESHAPE IT — the same copy, longer and narrower, in a band that is clear
    # across the front. Nothing in the sources fixes a sign's aspect; the lettering
    # scales with the rectangle, so the copy is untouched.
    h2 = h - RESHAPE_H_STEP_M
    while h2 >= RESHAPE_H_FLOOR_M - 1e-9:
        w2 = min(w * h / h2, w_ceiling)
        if w2 / h2 <= RESHAPE_MAX_ASPECT and w2 >= w:
            base2 = _band_top(mounting, h2, wall_height, head)
            for top2 in _tops(mounting, h2, wall_height, head, base2,
                              wall["openings"]):
                u2 = _nearest_clear(wall, want_u, w2, top2 - h2, top2 + cap)
                if u2 is None:
                    continue
                out.update({"u": u2, "w": w2, "h": h2, "top": top2,
                            "action": "reshaped"})
                out["note"] = (
                    f"the copy would not clear {' and '.join(covered)} on a "
                    f"{w:.2f} x {h:.2f} m board, so the same words are lettered on a "
                    f"longer and narrower {w2:.2f} x {h2:.2f} m one, which does")
                return out
        h2 -= RESHAPE_H_STEP_M

    # 3. SHRINK IT ONTO THE DOOR FRONT — a small board on the leaf itself, which is
    # what a modest office took anyway. Reported per building with the measurement,
    # because this is the case where the wall genuinely has no face to spare.
    doors = [o for o in wall["openings"] if o["kind"] in DOOR_KINDS]
    if doors:
        d = max(doors, key=lambda o: o["u1"] - o["u0"])
        w3 = (d["u1"] - d["u0"]) - 2 * DOOR_BOARD_MARGIN_M
        h3 = max(min(h * w3 / w, d["z1"] - d["z0"] - 2 * DOOR_BOARD_DROP_M),
                 DOOR_BOARD_H_MIN_M)
        out.update({"u": (d["u0"] + d["u1"]) / 2.0, "w": w3, "h": h3,
                    "top": d["z1"] - DOOR_BOARD_DROP_M, "on": d,
                    "proud_m": DOOR_BOARD_PROUD_M, "action": "shrunk to the door"})
        out["note"] = (
            f"this front has no {w:.2f} m of blank face at any height a name can be "
            f"read at — every band is taken by {' and '.join(covered)} — so the board "
            f"is shrunk to {w3:.2f} x {h3:.2f} m and fixed to the door itself")
        return out

    out["action"] = "no face and no door"
    out["note"] = ("neither blank face nor a door to fix a board to; the flat "
                   "mounting is refused and the cycle advances")
    return out


def _streets() -> dict:
    doc = _load(STREETS)
    out = {}
    for s in doc.get("streets", []):
        out[s["id"]] = {
            "name": s.get("name_1835") or s["id"],
            "path": [tuple(p) for p in s.get("path_local_enu_m", [])],
            "track_w": float(s.get("track_width_m") or 7.0),
        }
    return out


def _street_facing(mid, normal, streets: dict):
    """Which street a wall faces: the nearest centreline that lies IN FRONT of it.

    The same two tests `tools/generate_frontage_works.py::_street_facing` makes, for
    the same reason: a rear wall can be as close to a street as a front wall is to
    another one, and a street that runs BESIDE a wall rather than in front of it is
    not the street that wall's sign stands in.
    """
    best = (None, {}, float("inf"))
    for sid, st in streets.items():
        if len(st["path"]) < 2:
            continue
        d, foot = _nearest_on_path(mid, st["path"])
        outward = (foot[0] - mid[0]) * normal[0] + (foot[1] - mid[1]) * normal[1]
        if outward <= 0 or d > STREET_REACH_M:
            continue
        if outward < FRONTAGE_DOMINANCE * d:
            continue
        if d < best[2]:
            best = (sid, st, d)
    return best


def _frontage_walled() -> set:
    """Buildings the frontage layer already lays a plank walk outside of.

    A post stands where a walk lies. Rather than working out which of the two moves,
    this refuses the post at those frontages and takes the next mounting in the cycle
    — a refusal that is written into the record instead of being a silent nudge.
    """
    out = set()
    if not FRONTAGE.is_dir():
        return out
    for path in sorted(FRONTAGE.glob("*.json")):
        if path.name == "index.json":
            continue
        doc = _load(path)
        for walk in doc.get("walks", []):
            if walk.get("belongs_to"):
                out.add(walk["belongs_to"])
    return out


def _norm(s: str) -> str:
    """Letters and digits only, upper case — the form identities are compared in.

    "Steam-Boat Hotel" on a board and "Steamboat Hotel" on a card are the same house
    written two ways, and the advertisement's own hyphen is kept on the board because
    period spelling is part of the point. So the comparison drops everything that is not
    a letter or a digit rather than asking the two objects to agree on punctuation.
    """
    return "".join(ch for ch in s.upper() if ch.isalnum())


def _sign_wording(sid: str, name: str, mounting: str) -> dict:
    """What is lettered on THIS board, and why it is not the record's own name.

    THE TWO OBJECTS ARE DIFFERENT AND T-0066 COLLAPSED THEM. A record's `name` is this
    project's label for a STRUCTURE — "Philo Carpenter's Log Drug Store" — and a board
    carries what a signwriter lettered for a TRADE. Read the SIGN_WORDING table above for
    the register and the tiers; this function only picks how much of an entry fits the
    mounting the rule has already chosen, and holds the one invariant that survives the
    separation: the board and the card must agree about WHO this is.

    Raises rather than falling back. A frontage the rule newly selects and the table does
    not word would otherwise quietly go back to carrying the museum caption, which is the
    exact defect this replaced.
    """
    entry = SIGN_WORDING.get(sid)
    if entry is None:
        raise SystemExit(
            f"SIGN WORDING MISSING: {sid} is selected for a board and "
            f"tools/generate_business_signboards.py has no wording for it. Add an entry "
            f"to SIGN_WORDING — the proprietor or firm, the trade in the period's own "
            f"words, the tier and the reason. Do NOT let it fall back to the record's "
            f"name: that is the defect T-0130 corrected.")
    grade = entry["grade"]
    if grade not in WORDING_GRADES:
        raise SystemExit(f"SIGN WORDING GRADE: {sid} is graded {grade!r}; only "
                         f"{sorted(WORDING_GRADES)} are available (see PENDING).")

    room = LINES_BY_MOUNTING[mounting]
    lines = [{"text": entry["name"], "role": "name"}]
    trade = entry.get("trade_short") if room < 3 and entry.get("trade_short") \
        else entry.get("trade")
    if trade:
        lines.append({"text": trade, "role": "trade"})
    if room >= 3 and entry.get("place"):
        lines.append({"text": entry["place"], "role": "place"})
    text = " / ".join(ln["text"] for ln in lines)

    # THE INVARIANT THAT REPLACES STRING EQUALITY. The board and the card are allowed to
    # differ — that is the whole correction — but a visitor who reads a name off a plank
    # and then taps the plank must not be shown a different business. So the entry names
    # the identity and this refuses to build unless it is in both objects.
    ident = entry["identity"]
    if _norm(ident) not in _norm(text):
        raise SystemExit(f"SIGN IDENTITY: {sid}'s board reads {text!r} and does not "
                         f"carry its declared identity {ident!r}.")
    if _norm(ident) not in _norm(name):
        raise SystemExit(f"SIGN IDENTITY: {sid}'s card reads {name!r} and does not "
                         f"carry its declared identity {ident!r} — the board and the "
                         f"card would disagree about whose business this is.")
    # No board carries this project's own way of describing a building.
    if "LOG" in [w.strip(",.").upper() for w in text.split()]:
        raise SystemExit(f"SIGN WORDING: {sid}'s board reads {text!r}. No signwriter "
                         f"painted the construction of a shop on its own board.")

    why = entry["why"]
    if room < 3 and entry.get("place"):
        why += (f" The board is a {mounting.replace('_', ' ')}, which carries "
                f"{room} lines, so the place line — \"{entry['place']}\" — is not "
                f"lettered here: a signwriter letters what fits.")
    if room < 3 and entry.get("trade_short"):
        why += (f" For the same reason the trade is shortened from "
                f"\"{entry['trade']}\" to \"{entry['trade_short']}\".")

    out = {
        "lines": lines,
        "text": text,
        "identity": ident,
        "grade": grade,
        "why": why,
        "sources": list(entry.get("sources") or []),
    }
    if entry.get("device"):
        # `share` is how much of the board's face the device stands in, and it is on the
        # record rather than in the renderer for the same reason every other dimension
        # here is: a board's proportions are the record's business.
        out["device"] = dict(DEVICES[entry["device"]], share=DEVICE_SHARE)
    return out


def _candidates() -> tuple[list, list]:
    """Every frontage the rule selects, with its trade class — and every refusal."""
    index = _load(SIDECARS / "index.json")
    standing = [s["id"] for s in index.get("structures", [])]
    picked: list[dict] = []
    refused: list[dict] = []

    for sid in standing:
        sc_path = SIDECARS / f"{sid}.json"
        if not sc_path.exists():
            continue
        sc = _load(sc_path)
        attrs = sc.get("attributes") or {}
        fn = attrs.get("function") or {}
        trade = fn.get("value")
        if trade not in PUBLIC_TRADES and trade not in WORKS_TRADES:
            continue                                            # clause 2
        name = sc.get("name") or ""
        if sid.startswith(("inf_", "recon_")) or name.startswith("Reconstructed"):
            refused.append({"structure_id": sid, "trade": trade, "why": (
                "an anonymous slot. The archetype tables' own rule — never invent "
                "business, sign text or goods for an anonymous slot — and this record "
                "keeps it. Now that a board carries a NAME there is not even one to "
                "paint.")})
            continue                                            # clause 1
        grade = fn.get("confidence")
        if grade not in TRADE_GRADES:
            refused.append({"structure_id": sid, "trade": trade, "why": (
                f"the trade itself is {grade}. A sign for a business this project "
                "reconstructed would be an invention resting on an invention.")})
            continue                                            # clause 3

        if sid in VACATED_NAMES:
            refused.append({"structure_id": sid, "trade": trade,
                            "why": VACATED_NAMES[sid]})
            continue                                            # clause 8

        if sid in POST_BOARD_IDS:
            refused.append({"structure_id": sid, "trade": trade,
                            "why": POST_BOARD_IDS[sid]})
            continue                                            # clause 6

        struct = _load(STRUCTURES / f"{sid}.json")
        already = [ph.get("id") for ph in struct.get("phases", [])
                   if (ph.get("form") or {}).get("sign")]
        if already:
            refused.append({"structure_id": sid, "trade": trade, "why": (
                "it already has one. This is the single record in the dataset that "
                "ATTESTS a sign, and the board hangs in its GLB already "
                f"(phase {already[0]}, docs/LIBERTIES.md L25). A second board here "
                "would be this layer duplicating the only real one.")})
            continue                                            # clause 5

        if trade in WORKS_TRADES and not ("'s" in name or "&" in name):
            refused.append({"structure_id": sid, "trade": trade, "why": (
                f"'{name}' carries no proprietor — no possessive and no ampersand. A "
                "works painted WHOSE it was, and this project names this building by a "
                "later nickname rather than by a firm; painting the nickname would put "
                "a modern label on an 1835 wall.")})
            continue                                            # clause 7

        place = sc.get("placement") or {}
        poly = (sc.get("footprint") or {}).get("polygon") or []
        if len(poly) < 3:
            refused.append({"structure_id": sid, "trade": trade,
                            "why": "no footprint polygon — no wall to put a sign on."})
            continue
        u0, u1, vmax = _front_edge(poly)
        if u1 - u0 < 1.2:
            refused.append({"structure_id": sid, "trade": trade, "why": (
                "the front wall is under 1.2 m of frontage — narrower than the board.")})
            continue

        picked.append({
            "sid": sid, "name": name, "trade": trade, "grade": grade,
            "sc": sc, "place": place, "poly": poly,
            "u0": u0, "u1": u1, "vmax": vmax,
            "cls": TRADE_CLASS[trade],
        })

    picked.sort(key=lambda c: c["sid"])
    refused.sort(key=lambda r: r["structure_id"])
    return picked, refused


def _reach(mounting: str, w: float, geom: dict) -> float:
    """The furthest, ON THE GROUND PLAN, any vertex of this sign may sit from its
    own anchor.

    Carried on the record so the smoke can hold every sign to ITS OWN bound rather
    than to one number wide enough for the largest mounting — a transposed axis is
    metres out, and a per-sign bound catches it on the smallest board too. Horizontal
    only, because that is the mistake it is looking for: a sign hung at the wrong
    HEIGHT is caught by the wall-base rule and by the eye, and a sign hung on the
    wrong AXIS is caught here.

    The 0.12 m is the renderer's own small timber — hanger straps, the strut under a
    bracket, the knee brace under a post arm, the cap over a wall board. Those are
    how a sign is DRAWN rather than a claim about any shop, so they stay in
    renderers/web/js/signage.js, and this leaves them room.
    """
    if mounting == "bracket_board":
        out = ARM_M
        along = w / 2.0
    elif mounting == "awning_board":
        out = AWNING_PROJECTION_M
        along = max(w, geom["awning_width_m"]) / 2.0
    elif mounting == "wall_board":
        out = WALL_BOARD_PROUD_M + BOARD_T_M
        along = w / 2.0
    elif mounting == "post_board":
        out = POST_STAND_M + geom["post_square_m"]
        along = POST_ARM_M * 0.55 + w / 2.0
    else:                                          # facade_painted
        out = BAND_PROUD_M
        along = w / 2.0
    return math.hypot(out, along) + 0.12


def build_record() -> tuple[list, list, list]:
    picked, refused = _candidates()
    streets = _streets()
    walled = _frontage_walled()

    # WHERE A FRONTAGE ENTERS ITS CLASS'S CYCLE, and it is the frontage's OWN id that
    # decides (T-0405). It used to be the frontage's POSITION in the class — a counter
    # dealt out as the walk went down the town in id order — and a counter dealt down a
    # list has the property that inserting one frontage in the middle of it advances
    # every frontage after it by one. Measured on T-0263's diff: admitting
    # `frederick_thomas_shop` re-dealt ELEVEN other boards, the furthest 904 m away,
    # and four of them changed what they SAID, because the mounting decides how many
    # lines a board has room for. The rule this file states is LOCAL — no two boards
    # within `NEIGHBOUR_M` hang alike — and a local rule must not renumber the town to
    # admit one frontage in the middle of the alphabet.
    #
    # `_rank` is the same stable per-id device the style preference order already uses:
    # a board's entry point is a function of its own id and nothing else, so a board's
    # deal can only move when a board it can actually SEE moves. The de-confliction
    # below is what still separates neighbours, and it is the only thing that should:
    # it reads `signs`, so an insertion reaches a board when — and only when — the new
    # board lands within `NEIGHBOUR_M` of it. `_insertion_is_local` asserts exactly
    # that, and `_neighbours_differ` asserts the separation still holds.
    for cand in picked:
        cand["rank"] = _rank(cand["sid"], len(MOUNTING_CYCLE[cand["cls"]]))

    signs: list[dict] = []
    for cand in picked:
        sid = cand["sid"]
        place = cand["place"]
        poly = cand["poly"]
        u0, u1, vmax = cand["u0"], cand["u1"], cand["vmax"]
        frontage = u1 - u0
        mid = (u0 + u1) / 2.0
        attrs = cand["sc"].get("attributes") or {}

        stories = ((attrs.get("stories") or {}).get("value"))
        wall = (attrs.get("wall_height_m") or {}).get("value")
        wall_from = "the record"
        if wall is None:
            wall = DEFAULT_WALL_M.get(stories, DEFAULT_WALL_MULTI_M) \
                if stories in DEFAULT_WALL_M else DEFAULT_WALL_MULTI_M
            wall_from = ("the archetype's default, because the record carries no "
                         "wall height — the same number the wall itself is drawn at")
        head = min(wall - EAVE_CLEAR_M, MAX_HEIGHT_M)

        # The centre of the front wall, in ENU, and the way it faces — the two things
        # every mounting test below needs.
        bearing = place.get("rotation_deg") or 0.0
        rad = math.radians(bearing)
        normal = (math.sin(rad), math.cos(rad))          # outward, in ENU
        mid_enu = _to_enu(mid, vmax, place)

        # WHAT IS ALREADY ON THAT WALL (T-0459). Read before the mounting is chosen,
        # because "may a board be fixed flat here at all" is one of the questions the
        # cycle asks, and it cannot be answered by a wall nobody has read.
        front = _front_wall(sid)

        # --- the mounting -----------------------------------------------------
        cycle = MOUNTING_CYCLE[cand["cls"]]
        near = [s for s in signs
                if math.hypot(s["anchor_local_enu_m"][0] - mid_enu[0],
                              s["anchor_local_enu_m"][1] - mid_enu[1]) <= NEIGHBOUR_M]
        taken_mount = {s["mounting"] for s in near}
        mount_notes: list[str] = []
        mounting = None
        for step in range(len(cycle)):
            trial = cycle[(cand["rank"] + step) % len(cycle)]
            if trial == "post_board":
                if sid in walled:
                    mount_notes.append(
                        "a post was refused here because the frontage layer already "
                        "lays a plank walk outside this wall, and a post stands where "
                        "the walk lies")
                    continue
                st_id, st, dist = _street_facing(mid_enu, normal, streets)
                if st_id is None:
                    mount_notes.append(
                        "a post was refused here because no street lies in front of "
                        "this wall within "
                        f"{STREET_REACH_M:.0f} m — a post here would stand in a yard")
                    continue
                reach = dist - POST_STAND_M - st["track_w"] / 2.0
                if reach < POST_CLEAR_M:
                    mount_notes.append(
                        f"a post was refused here because the {st['name']} track "
                        f"reaches to within {reach + POST_CLEAR_M:.2f} m of where the "
                        "post would stand")
                    continue
            if trial in ("facade_painted", "wall_board") and front is not None \
                    and not _has_flat_face(front, BOARD_SIZE[trial]["min"]):
                mount_notes.append(
                    f"a {trial.replace('_', ' ')} was refused here because this front "
                    f"has no {BOARD_SIZE[trial]['min']:.2f} m of blank face at any "
                    "height and no door to fix a board to — every elevation of it is "
                    "open bay, and a name lettered there would hang in the air "
                    "between the posts")
                continue
            if trial in ("facade_painted", "wall_board") and front is None:
                mount_notes.append(
                    f"a {trial.replace('_', ' ')} was refused here because no rule "
                    "reads this archetype's front elevation, and a board fixed flat "
                    "on a wall whose openings are unknown is the fault T-0459 "
                    "records — so the cycle advances rather than guessing")
                continue
            if trial == "facade_painted" and frontage < FACADE_MIN_FRONTAGE_M:
                mount_notes.append(
                    f"a painted name was refused here because the front wall is "
                    f"{frontage:.2f} m — under the {FACADE_MIN_FRONTAGE_M:.1f} m a band "
                    "needs to run")
                continue
            if trial in taken_mount and step + 1 < len(cycle):
                mount_notes.append(
                    f"a {trial.replace('_', ' ')} is what this frontage's place in the "
                    f"{cand['cls']} cycle asks for, and a sign within "
                    f"{NEIGHBOUR_M:.0f} m already hangs that way — so the cycle "
                    "advances rather than repeating a neighbour")
                continue                       # a neighbour already hangs one this way
            mounting = trial
            break
        if mounting is None:
            # EVERY MOUNTING IN THIS CLASS'S CYCLE WAS REFUSED, which before T-0459
            # could not happen: the loop fell through to the cycle's first entry and
            # put the board up anyway. A works paints its front and hangs nothing, so
            # a works with no front to paint has nowhere for a board at all, and the
            # honest answer is the refusal with its reason rather than a name
            # lettered across an opening.
            refused.append({"structure_id": sid, "trade": cand["trade"],
                            "why": "; ".join(mount_notes)})
            continue

        # --- the style --------------------------------------------------------
        taken_style = {s["style"]["id"] for s in near}
        taken_ground = {s["style"]["ground"] for s in near}
        start = _rank(sid, len(STYLES))
        style = STYLES[start]
        for relax in (0, 1):
            found = None
            for k in range(len(STYLES)):
                s = STYLES[(start + k) % len(STYLES)]
                if s["id"] in taken_style:
                    continue
                if relax == 0 and s["ground"] in taken_ground:
                    continue
                found = s
                break
            if found:
                style = found
                break

        # --- WHAT IT SAYS, which the mounting has to be known to answer -------
        # A signwriter letters what fits, so the wording is resolved AFTER the mounting
        # rather than before it: a plank swinging over a footway takes the man and his
        # trade, and a name painted across a whole front has room for his street too.
        word = _sign_wording(sid, cand["name"], mounting)
        text = word["text"]
        n_lines = len(word["lines"])
        longest = max(len(ln["text"]) for ln in word["lines"])

        # --- the sign's own size ----------------------------------------------
        size = BOARD_SIZE[mounting]
        extra = DEVICE_W_M if word.get("device") else 0.0
        w = _clamp(size["base"] + PER_LETTER_M * longest
                   + LINE_WIDTH_BONUS_M * (n_lines - 1) + extra,
                   size["min"], size["max"] + extra)
        # The ceiling is the frontage's, and a RESHAPED board may grow up to it but
        # no further: a name is lettered on the building, not across its corners.
        w_ceiling = max((frontage - 1.2) if mounting == "facade_painted"
                        else (frontage - 2 * END_CLEAR_M), 0.7)
        w = max(min(w, w_ceiling), 0.7)
        tall = LINE_H_MUL[n_lines] if mounting in LINE_H_MOUNTINGS else 1.0
        h = _clamp(w / (style["aspect"] * size["aspect_mul"]) * tall,
                   BOARD_H_MIN_M, BOARD_H_MAX_M)

        # --- where it sits on the wall ----------------------------------------
        # A hanging board sits to one side of the door. A wall board and a painted
        # band used to be centred on the front — which is where a painted name goes,
        # and is also where the door is, which is the whole of T-0459. They are now
        # fitted to the wall: moved onto blank face, or reshaped to a band that is
        # clear across the front, or shrunk onto the door itself, in that order.
        fit = None
        if mounting in ("bracket_board", "awning_board", "post_board"):
            u = mid + OFFSET_M
            if u > u1 - END_CLEAR_M:
                u = max(mid, u1 - END_CLEAR_M)
        else:
            fit = _fit_flat(front, mounting, mid, w, h, float(wall), head, w_ceiling)
            u, w, h = fit["u"], _round(fit["w"], 2), _round(fit["h"], 2)
        e, n = _to_enu(u, vmax, place)
        quad = [_to_enu(uu, vv, place) for uu, vv in (
            (min(p[0] for p in poly), min(p[1] for p in poly)),
            (max(p[0] for p in poly), min(p[1] for p in poly)),
            (max(p[0] for p in poly), max(p[1] for p in poly)),
            (min(p[0] for p in poly), max(p[1] for p in poly)))]

        geom: dict = {}
        if mounting == "bracket_board":
            geom["arm_m"] = ARM_M
            geom["hanger_drop_m"] = DROP_M
        elif mounting == "awning_board":
            geom["awning_projection_m"] = AWNING_PROJECTION_M
            geom["awning_drop_m"] = AWNING_DROP_M
            geom["awning_width_m"] = _round(
                min(w + 2 * AWNING_MARGIN_M, max(w + 0.2, frontage - 0.8)), 2)
            geom["hanger_drop_m"] = DROP_M
        elif mounting == "wall_board":
            geom["proud_m"] = WALL_BOARD_PROUD_M
        elif mounting == "post_board":
            geom["stand_m"] = POST_STAND_M
            geom["arm_m"] = POST_ARM_M
            geom["hanger_drop_m"] = DROP_M
            # The pole's height is invented inside a hand's range of the Green Tree's
            # 3.60 m, varied by the same stable rank the style uses so that two posts
            # in one street are not the same stick.
            geom["post_height_m"] = _round(3.30 + 0.12 * (_rank(sid, 5)), 2)
            geom["post_square_m"] = 0.16
        else:
            geom["proud_m"] = BAND_PROUD_M
        # A board fixed to the DOOR stands off the leaf and its battens, not off the
        # wall plane the leaf is hung in.
        if fit and fit["proud_m"] is not None:
            geom["proud_m"] = fit["proud_m"]

        # THE DATUM, and it is not the same one for every mounting. A sign fixed to
        # a building is measured from the base of that building's walls — the LOWEST
        # of a 5x5 grid of terrain samples under the footprint, which is where
        # buildings.js puts the walls, and any other rule floats a board off its own
        # wall on sloping ground. A POST is not on the building: it stands in the
        # street, on the ground under itself, so its head is measured from there and
        # `arm_height_m` says nothing about it.
        # A PAINTED NAME GOES ABOVE THE DOOR HEAD, which a hung board does not have
        # to think about; `_band_top` is that rule, and it lives beside the fit
        # because reshaping changes the board's height and a top computed from the
        # old one would float the new board off its own wall.
        head_y = _round(fit["top"] if fit else head, 2)
        datum = ("the base of this building's walls — the lowest of a 5x5 terrain "
                 "grid over the footprint, as buildings.js sets it")
        if fit and fit["action"] == "shrunk to the door":
            datum = ("the base of this building's walls — the lowest of a 5x5 terrain "
                     "grid over the footprint, as buildings.js sets it. This board is "
                     "on the door leaf rather than on the wall, so its head is the "
                     "door's head less a hand's breadth")
        if mounting == "post_board":
            datum = ("the ground under the post itself, sampled where it stands: the "
                     "post is in the street, not on the building. `post_height_m` is "
                     "its head over that ground and `arm_height_m` does not apply")

        sign = {
            "structure_id": sid,
            "name": cand["name"],
            "sign_text": text,
            "sign_lines": word["lines"],
            "sign_identity": word["identity"],
            "sign_text_from": word["why"],
            "sign_text_confidence": word["grade"],
            "sign_text_sources": word["sources"],
            "trade": cand["trade"],
            "trade_confidence": cand["grade"],
            "trade_class": cand["cls"],
            "why_a_board": PUBLIC_TRADES.get(cand["trade"])
            or WORKS_TRADES[cand["trade"]],
            "confidence": "reconstructed",
            "mounting": mounting,
            "mounting_note": "; ".join(mount_notes) or None,
            "style": style,
            "anchor_local_enu_m": [_round(e, 2), _round(n, 2)],
            "facade_bearing_deg": _round(bearing, 1),
            "arm_height_m": head_y,
            "height_datum": datum,
            "board_w_m": _round(w, 2),
            "board_h_m": _round(h, 2),
            "board_thickness_m": BOARD_T_M,
            "geometry": geom,
            "reach_m": _round(_reach(mounting, w, geom), 2),
            "wall_height_m": _round(float(wall), 2),
            "wall_height_from": wall_from,
            "frontage_m": _round(frontage, 2),
            "ground_quad_local_enu_m": [[_round(p[0], 2), _round(p[1], 2)]
                                        for p in quad],
        }
        # THE ACCOUNT OF THE FIT (T-0459), on every flat-mounted board whether or
        # not it had to move — "already clear" is a measurement and not a silence,
        # and the sweep in `findings` counts these rather than summarising them.
        # `openings` is what the renderer's smoke holds the board against, so the
        # rectangles travel with the sign that has to stay off them.
        if fit is not None:
            sign["opening_fit"] = {
                "action": fit["action"],
                "covered_before": fit["covered"],
                # The ONE rectangle this board is allowed to stand over, and only
                # ever a door it is deliberately fixed to. Null everywhere else, and
                # the smoke reads it that way: anything a board covers that is not
                # this is the fault T-0459 exists to stop coming back.
                "fixed_to": ({"kind": fit["on"]["kind"],
                              "u0": _round(fit["on"]["u0"], 2),
                              "u1": _round(fit["on"]["u1"], 2),
                              "z0": _round(fit["on"]["z0"], 2),
                              "z1": _round(fit["on"]["z1"], 2)}
                             if fit["on"] else None),
                "note": fit["note"],
                "wall_span_local_m": ([_round(front["u0"], 2), _round(front["u1"], 2)]
                                      if front else None),
                "board_span_local_m": [_round(u - w / 2, 2), _round(u + w / 2, 2)],
                "openings": [
                    {"kind": o["kind"], "u0": _round(o["u0"], 2),
                     "u1": _round(o["u1"], 2), "z0": _round(o["z0"], 2),
                     "z1": _round(o["z1"], 2)}
                    for o in (front["openings"] if front else [])],
            }
        # A DEVICE ONLY WHERE THE SHOP'S OWN ADVERTISEMENT NAMES ONE. Exactly one does.
        if word.get("device"):
            sign["sign_device"] = word["device"]
        signs.append(sign)

    # THE PROMISE, CHECKED (T-0405). The head of this file says no two boards within
    # `NEIGHBOUR_M` hang alike; the loop above only ever TRIES to make that true, and
    # until now nothing read back whether it had. This refuses to build when it has not,
    # and hands the permitted exceptions on so the record can carry them by name.
    separation = _neighbours_differ(signs)
    _wordings_differ(signs)

    return signs, refused, separation


def _opening_sweep(signs: list) -> dict:
    """THE SWEEP T-0459 ASKED FOR, over every sign in the record: whether it stood
    over an opening where the trade rule put it, and what was done about it.

    Counted per sign and not summarised, because the summary is what let this run
    for a month — twenty boards over doors and windows, on walls with blank face
    going spare, and the record said only that fourteen names were painted and six
    boards were fixed flat.
    """
    rows = []
    counts: dict[str, int] = {}
    for s in signs:
        fit = s.get("opening_fit")
        if fit is None:
            action = "not flat on the wall"
            covered = []
        else:
            action = fit["action"]
            covered = fit["covered_before"]
        counts[action] = counts.get(action, 0) + 1
        rows.append({
            "structure_id": s["structure_id"],
            "mounting": s["mounting"],
            "covered_an_opening_before": bool(covered),
            "covered_before": covered,
            "done": action,
        })
    return {
        "note": (
            "Every sign in the record, and what the opening test did with it. A board "
            "on a BRACKET, an AWNING or a POST stands off the wall on an arm, a hood "
            "or a stick of its own and cannot cover an opening, so it is swept as "
            "`not flat on the wall` rather than as clear — the test applies to the "
            "boards fixed flat against a facade and to the names painted straight on "
            "one. `already clear` is a measurement and not a silence: it means the "
            "board was tested against this building's own door and window rectangles "
            "and stood off all of them where the trade rule had already put it."
        ),
        "flat_mounted": sum(1 for r in rows if r["done"] != "not flat on the wall"),
        "counts": {k: counts[k] for k in sorted(counts)},
        "signs": sorted(rows, key=lambda r: r["structure_id"]),
    }


def record(signs: list, refused: list, separation: list) -> dict:
    mounts: dict[str, int] = {}
    tiers: dict[str, int] = {}
    for s in signs:
        mounts[s["mounting"]] = mounts.get(s["mounting"], 0) + 1
        g = s["sign_text_confidence"]
        tiers[g] = tiers.get(g, 0) + 1
    return {
        "_doc": (
            "The town's business signs. NOT structure records and NOT geometry that "
            "comes out of Blender: a board is a plank on a bracket, a hood, a post or "
            "a wall this project has already drawn, and a painted name is paint on a "
            "wall it has already drawn, so all of it is derived from the committed "
            "footprint and placement and drawn at load by "
            "renderers/web/js/signage.js — the same argument that lets the enclosure "
            "layer draw a fence from a perimeter. Generated by "
            "tools/generate_business_signboards.py and re-derived byte for byte by "
            "tools/check.sh, because 'which frontage gets a sign, what it says, how it "
            "hangs and what colour it is' is a rule and a rule has to be auditable."
        ),
        "id": "town_business_signboards",
        "name": "Signs on the town's business frontages",
        "kind": "signage",
        "scene": "1835",
        "target_date": TARGET_DATE,
        "coordinates": (
            "Local East-North-Up metres from data/datum.json's origin, the same frame "
            "data/enclosures/ and the sidecars' placement.local_e / local_n use."
        ),
        "existence": {
            "value": True,
            "confidence": "reconstructed",
            "sources": ["drloih_wolf_point", "chicago_democrat_1833_11_26"],
            "note": (
                "NO SOURCE STATES THAT ANY OF THESE PARTICULAR BUILDINGS CARRIED A "
                "SIGN, and this record never says one does. What is held is the "
                "bound: one Chicago business of these years is attested to have hung "
                "a sign — the Wolf Point Tavern's painted wolf, by about 1833 — and "
                "the town's first newspaper, 26 November 1833, is full of businesses "
                "trading under names at named addresses, in a settlement whose own "
                "sources describe its houses being known BY their signs (the Wolf "
                "Point house is 'under the sign of the Travelers' Home'; the Exchange "
                "Coffee House's later 'Illinois Exchange' is recorded as a change of "
                "sign). A named trade on a public street announced itself, and how it "
                "did so in 1830s America is not in dispute. That is a reconstruction "
                "in this project's third tier, not an attestation, and it is graded "
                "and claimed as one: docs/LIBERTIES.md L130 for the fact of a sign, "
                "L159 for its wording, its mounting and its colours. THE GREEN TREE "
                "PLATE IS NOT PART OF THE ARGUMENT — docs/ROADMAP.md K5 (b) cites its "
                "hanging sign, but data/sources/chm_green_tree_1859.json records that "
                "the image has never been seen and is unverified, so it underwrites "
                "nothing here."
            ),
        },
        "lettering": {
            "value": ("what the trade wrote — the proprietor or firm, the trade, and "
                      "the place, in the period's own words and spelling"),
            "confidence": "reconstructed",
            "geometry": "canvas texture, drawn at load",
            "tiers": {k: tiers[k] for k in sorted(tiers)},
            "note": (
                "DRAWN SINCE 2026-08-21, AND RE-WORDED THE SAME DAY. This block used to "
                "read 'NOT DRAWN, AND THAT IS THE WHOLE DISCIPLINE OF THIS LAYER', on "
                "L25's reasoning generalised: no source gives the wording of any sign in "
                "this town, so every board stayed a blank plank. The owner's instruction "
                "of 2026-08-18 overruled it — 'you can and should put the name of the "
                "location on the sign board … it is fine if they are reconstructions' — "
                "and T-0066 then painted THE RECORD'S OWN `name` on every board. "
                "T-0130 CORRECTS THAT, on the owner's word of 2026-08-21: 'philo would "
                "not have referred to his own place as log drug store, it would be philo "
                "carpenter, drugs and medicines, or druggist or whatever he would have "
                "referred to himself as on the sign, that may be different than the name "
                "of the building for us, the sign may read differently historically' — "
                "and, widening it, 'i guess do a pass on all those signs and make sure "
                "they feel right for the era'. A record's `name` is OUR LABEL FOR A "
                "BUILDING ('Philo Carpenter's Log Drug Store'); a board carries what a "
                "signwriter lettered. The two are now separate fields and are allowed to "
                "differ. What they must still agree about is WHO: every sign declares a "
                "`sign_identity` that appears in the board AND in the card, the "
                "generator refuses to build without it, and tools/smoke_renderer.mjs "
                "asserts it at run time over every sign. THE REGISTER is the "
                "advertisements' own — proprietor or firm first and largest, the trade "
                "beneath, the place last and smallest — carried per line in `sign_lines` "
                "and lettered in that hierarchy by renderers/web/js/signage.js. Period "
                "spelling is theirs and is kept. THE TIERS: a wording taken off a firm's "
                "own advertisement is `inferred`; one built out of the evidenced trade "
                "vocabulary for a business that left no advertisement is "
                "`reconstructed`. NOT ONE IS `attested` YET, and each note says why and "
                "what would change it — the seven 1833-35 newspaper pages behind these "
                "wordings were supplied as images in conversation on 2026-08-21 and are "
                "not committed to data/sources/assets/, so they are transcriptions and a "
                "transcription is not a citation. The owner's ruling of that day is the "
                "authority for proceeding anyway: 'I will give you all those data sources "
                "later in a more comprehensive form proceed where you can and label "
                "reconstruction or inferred with a note as you like.' The LETTERFORM, "
                "the colours and the panel remain `style`, a table of the combinations "
                "the trade worked in rather than of anything Chicago recorded "
                "(docs/LIBERTIES.md L159; L169 for the wording). ONE DEVICE IS NOW "
                "PAINTED and it is the one a Chicago tradesman described himself: "
                "Carpenter's golden mortar, `sign_device` — see its own note. No other "
                "board carries an image, and L25 is untouched: it withholds the Wolf "
                "Point wolf because that IMAGE was never described, which is the "
                "opposite case to a shop whose own advertisement names its sign."
            ),
        },
        "treatment": {
            "confidence": "reconstructed",
            "note": (
                "Five mountings, chosen by the trade's class and de-conflicted against "
                "every sign within "
                f"{NEIGHBOUR_M:.0f} m so that no two neighbours hang alike: "
                "`bracket_board` (the wolf sign's own geometry — a plank hung by two "
                "straps 0.20 m under a 1.15 m bracket arm, 1.7 m to one side of the "
                "facade's centre and clear of the eave), `awning_board` (the same "
                f"plank under a hood {AWNING_PROJECTION_M} m deep that falls "
                f"{AWNING_DROP_M} m to its outer edge), `wall_board` (a board fixed "
                "flat on the front under a cap), `post_board` (a pole at the street "
                f"edge {POST_STAND_M} m out from the wall, with a cross-arm and the "
                "board under it — the Green Tree's own arrangement, T-0082) and "
                "`facade_painted` (the name straight onto the boards of the building, "
                "no board at all — what image 5 of the owner's brief shows across the "
                f"Tremont's row, standing with its foot {BAND_FOOT_M} m up so it "
                "clears a door head, or lower where the wall has not the height for "
                f"that and {BAND_EAVE_CLEAR_M} m of eave besides). Not one of those "
                "numbers is a record's. A sign's "
                "SIZE is derived from the length of its own name inside the range its "
                "mounting allows and inside the frontage it stands on; its `aspect` "
                "comes from its style, so two boards on one street are not the same "
                "rectangle either."
            ),
            "mountings": {k: mounts[k] for k in sorted(mounts)},
        },
        "opening_sweep": _opening_sweep(signs),
        "rule": {
            "note": (
                "A named record (not inf_/recon_, not 'Reconstructed'), a trade this "
                "project will announce — a PUBLIC TRADE whose customer arrived on foot "
                "off the street, which gets a board, or a WORKS OR WAREHOUSE trade "
                "whose custom came by name and by cart, which gets its firm painted on "
                "the front — that trade attested or inferred rather than "
                "reconstructed, standing on the scene date, no sign on the record "
                "already, no named board already standing on a post at its corner on "
                "the frontage layer, and (for a works only) a proprietor in its own "
                "name. Read the clauses and their reasons in "
                "tools/generate_business_signboards.py."
            ),
            "public_trades": sorted(PUBLIC_TRADES),
            "works_trades": sorted(WORKS_TRADES),
            "mounting_cycles": MOUNTING_CYCLE,
            "lines_by_mounting": LINES_BY_MOUNTING,
            "styles": [s["id"] for s in STYLES],
            "neighbour_m": NEIGHBOUR_M,
            "cycle_entry": (
                "WHERE A FRONTAGE ENTERS ITS CLASS'S CYCLE is a function of its own "
                "structure id — `_rank`, the same stable per-id device the style "
                "preference order uses — and of nothing else (T-0405). It used to be "
                "the frontage's POSITION in its class, a counter dealt out as the walk "
                "went down the town in id order, and a counter dealt down a list has "
                "the property that admitting one frontage in the middle of it advances "
                "every frontage after it by one: admitting `frederick_thomas_shop` "
                "re-dealt eleven other boards, the furthest 904 m away, and four of "
                "them changed what they SAID, because the mounting decides how many "
                "lines a board has room for. The rule this layer states is LOCAL, so "
                "its deal is local: a board's mounting can only move when a board it "
                "can SEE moves. `--prove-locality` withholds each board in turn and "
                "holds every consequence against the distance from it."),
            "separation": {
                "note": (
                    "The promise above, MEASURED rather than assumed, every build: "
                    "every pair of boards within "
                    f"{NEIGHBOUR_M:.0f} m that shares a mounting, a style or a ground "
                    "colour. The generator REFUSES TO BUILD on any pair not listed "
                    "here as allowed. A mounting may be shared only where one of the "
                    "two trades belongs to a class whose cycle is a single mounting — "
                    "a works paints its front and hangs nothing at all, so two works "
                    "on one corner cannot differ, and this project would rather say so "
                    "than hang a plank on a works to make a rule come out."),
                "pairs_within_neighbour_m_sharing_something": separation,
            },
            "wording_note": (
                "WHAT A BOARD MAY SAY, and it is a rule rather than a list somebody "
                "liked. Every board is worded from SIGN_WORDING in "
                "tools/generate_business_signboards.py: the proprietor or firm, the "
                "trade in the period's own words, and the place — in that order, which "
                "is the order the advertisements themselves use. The generator refuses "
                "to build a board for a frontage the table does not word, refuses one "
                "whose declared `sign_identity` is not in both the board and the card, "
                "and refuses one that carries the word 'log' — the three ways the old "
                "behaviour could come back. How much of an entry is lettered depends on "
                "the mounting: `lines_by_mounting` above, because a signwriter letters "
                "what fits and a plank swinging over a footway holds less than a name "
                "painted across a whole front."
            ),
            "excluded_trades_note": (
                "Stables, churches, schools, the court-house, the jail, the agency "
                "house, the fort and every dwelling are outside both trade lists. A "
                "stable is the yard of the house that owns it and announces nothing of "
                "its own; the rest are not trades. Frederick Thomas's shop is refused "
                "one clause further down, because its own record says no source reached "
                "says what he sold."
            ),
        },
        "signs": signs,
        "refused": refused,
        "research_note": (
            "THE FIRST THING TO DO, AND IT IS ALREADY HALF DONE: COMMIT THE SEVEN PAGES. "
            "The wordings graded `inferred` above are transcribed from 1833-35 Chicago "
            "newspaper pages the owner supplied as IMAGES IN CONVERSATION on 2026-08-21 "
            "— one carrying 'Chicago, Dec. 31, 1833' with a 'CHICAGO PRICES CURRENT … "
            "Reported for the Democrat by P. F. Peck' that identifies the Chicago "
            "Democrat, one 'Chicago, Dec. 4, 1833', and several of 1835 carrying an "
            "'ARRIVALS OF VESSELS AT CHICAGO, 1835' table and a Post Office list of "
            "letters remaining 'on the 31st day of March, 1835'. Drop those images into "
            "data/sources/assets/ with a source record and EVERY `inferred` WORDING HERE "
            "BECOMES A CANDIDATE FOR `attested`, one board at a time, each note already "
            "saying what its page says. Goss & Cobb's is the nearest: its page is "
            "committed already. WHAT WOULD MOVE THE REST — the fact of a sign, its "
            "colours and its mounting — is unchanged: a Chicago or Cook County sign "
            "ordinance of the 1830s; an insurance, tax or sale description naming a shop "
            "sign; any of the pre-fire photographs of a surviving 1830s frontage "
            "actually being opened at its holding institution (the Green Tree 1859 "
            "plate, ICHi-040230, is the nearest and is unseen); or a traveller's account "
            "of walking South Water Street."
        ),
        "findings": [
            "J. S. C. HOGAN advertises in 1835 from 'South Water Street, one door below "
            "Dearborn' in dry goods, groceries, hardware, crockery and glass ware. The "
            "model carries ONE Hogan building, the log store at the Lake Street junction, "
            "which its own record identifies as Brewster, Hogan & Co.'s. The pages "
            "distinguish the two businesses and the model does not — a placement "
            "question, raised rather than silently answered.",
            "PIERCE & ABBOTT advertise a 'New Blacksmith Shop' on the 1833 pages. This "
            "project's record names Asahel Pierce alone as builder and proprietor. If the "
            "partnership is his, the board should read PIERCE & ABBOTT and rise from "
            "`reconstructed` to `inferred`; a signage generator is not the place to add a "
            "partner to a structure record.",
            "P. PRYNE & CO. appears twice on the 1835 pages, both times in groceries and "
            "dry goods, never in drugs. The model carries Pruyne & Kimball as a drug "
            "store on Andreas's word. Whether these are the same Pruyne is unresolved and "
            "the board says nothing about it.",
            "Two 1835 advertisements locate themselves BY A NEIGHBOUR — Wm. H. Taylor's "
            "boot store 'a few rods north of Newberry & Dole's', J. Curtiss's office "
            "'first door west of Jones, King & Co.' — and a third 'opposite the Tremont "
            "House'. Those are checkable against this model's own placements and are a "
            "wayfinding gift for whoever takes the placement sweep.",
            "Firms the pages name and the model does not yet carry at all: WM. H. TAYLOR "
            "(boot, shoe and leather), J. H. MULFORD (watches and jewelry), DAVID CARVER "
            "(lumber dealer and commission merchant), MAGIE & WILKINSON (boots, shoes and "
            "hats), F. J. CONANT (clothing warehouse), Doct. WM. H. KENNICOTT (medicine "
            "and dentistry), and a bench of attorneys. Each is a placement question, not "
            "a wording one, and none has been invented a building here.",
            "Out-of-town houses advertise on the same pages — Patterson, Gardner & Mather "
            "of Detroit 'at the sign of the Large Pitcher', Cromelien, Brothers & Co. of "
            "New York. They are useful as REGISTER and must never be hung in Chicago. The "
            "Large Pitcher is quoted in the golden mortar's note for exactly that reason: "
            "it shows the convention was ordinary, and it belongs to Detroit.",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and diff, write nothing")
    ap.add_argument("--prove-locality", action="store_true",
                    help="withhold each board in turn and prove that admitting one "
                         "frontage reaches no board further off than NEIGHBOUR_M")
    args = ap.parse_args()
    if args.prove_locality:
        return _prove_locality()
    signs, refused, separation = build_record()
    text = json.dumps(record(signs, refused, separation), indent=2,
                      ensure_ascii=False) + "\n"
    if args.check:
        if not OUT.exists():
            print(f"SIGNBOARD DRIFT\n  - {OUT.relative_to(ROOT)} is missing")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"SIGNBOARD DRIFT\n  - {OUT.relative_to(ROOT)} has drifted from the "
                  f"rule in tools/generate_business_signboards.py")
            return 1
        print(f"verified {len(signs)} business signs "
              f"({len(refused)} frontage(s) refused with a reason)")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {len(signs)} business signs "
          f"({len(refused)} refused)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
