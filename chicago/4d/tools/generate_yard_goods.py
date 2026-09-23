#!/usr/bin/env python3
"""Generate the goods standing at the town's trading frontages — the yard layer.

WHAT THIS IS. `docs/ROADMAP.md` K5 (c) asks for *"yard objects: wagons/drays …, crates
and barrels at the stores"*, and ticket T-0040 is that clause for the taverns and the
stores. Unlike the signboards one layer over, this one does not start from silence: the
town legislated about it.

THE EVIDENCE, AND IT IS AN ORDINANCE. `data/sources/chicago_democrat_1833_11_26.json`
carries the village ordinances of 7 November 1833 complete, and **Ordinance 9 is about
timber, stone, brick, boxes and barrels stacked in the streets**. A corporation does not
legislate against a thing nobody does. That is a tier-1 contemporary statement that
Chicago's streets in the town's own first winter had boxes and barrels standing in them,
made twenty months before the scene date and by the people who had to walk round them.

What the ordinance does NOT give is a single location. It says the town, not the corner.
So the shape of this record is the same as the pickets' and the signboards': the evidence
is a TREATMENT and the answer to "why this frontage" has to be a RULE.

THE RULE, and every clause is doing work. A frontage gets goods iff

  1. it is a NAMED record — the id does not begin `inf_` or `recon_` and the name does not
     begin "Reconstructed". The archetype tables' own rule is *never invent business, sign
     text or goods for an anonymous slot*, and it names goods explicitly;
  2. its `function` is a GOODS-KEEPING TRADE — one whose stock arrived in boxes and
     barrels off a lake schooner and stood on the ground before it went inside. The
     taverns and hotels are in for the reason the stores are: a public house takes its
     provisions in by the barrel and puts the empties back out. Smithies, tanneries,
     manufactories, stables, churches, schools, the court-house and the jail are out —
     they kept stuff, but not a merchant's stock on a public frontage;
  3. that function is `attested` or `inferred`. A `reconstructed` trade gets no goods,
     for the same reason it gets no sign: invention squared;
  4. it is standing on the scene date (it is in `data/sidecars/1835/index.json`);
  5. it stands on the TOWN's ground. The fort's provision store and the sutler's store
     are refused in writing: they are federal ground inside a palisade, outside the
     corporation whose ordinance is the whole evidence here, and there is no public
     street in front of either of them;
  6. the strip in front of its facade is clear — nothing is placed where it would stand
     inside another building's committed footprint.

WHERE THE GOODS STAND is then DERIVED, not placed, exactly as a board's anchor is.
`docs/GLB-CONTRACT.md` fixes the frame: polygon `u` → +X, polygon `v` → −Z, and
`rotation_deg` is the FACADE BEARING, so the front wall is the footprint's own max-`v`
edge. The goods stand against that wall, 0.55 m out from its plane, at the end of the
frontage the signboard does not occupy — `tools/generate_business_signboards.py` hangs
its board 1.7 m toward +u of the facade centre, so this piles the barrels from the −u end
and the door between them stays clear. How many is arithmetic on the frontage and not a
lottery: one barrel per 2.2 m of usable wall, capped at four, a crate past them once
there is 4 m of wall to hold one, and a second crate stacked on it at 7 m.

THE ATTESTED WAGON, and why it used to be the only one. No source in this repository puts
a wagon at any place in this town on any day. One place is named for them:
`data/enclosures/western_hotel_wagon_yard.json`, whose attested sentence is *"In the rear
was the large stable and the yard into which the trains were driven."* So a wagon stands
in the yard the source calls a wagon yard, at the point in it derived to be furthest from
every fence line and every committed wall. That wagon and the Green Tree's are the two
addresses evidence reaches, and until T-0064 they were the only wagons in Chicago.

THE TOWN'S OWN WAGONS (T-0064), AND THE RESTRAINT THAT WAS OVERRULED. This file used to
end the paragraph above with *"Scattering drays along Lake Street would be this record
inventing traffic"*, and the record's own research note filed the rest of a frontier
town's traffic as an open ticket. **The owner closed it, 2026-08-18, verbatim: "there can
be more wagons! of course there would be more wagons all over the place in a frontier
town."** His standing ruling of the same day covers the tier: *"you are totally fine to be
liberal with adding reconstructed items when i ask for things, you can just label and mark
them as such."* So the wagons are scattered now, every one of them `reconstructed`, every
one of them carded and marked — and WHERE each one stands is still a rule rather than a
list somebody typed, because that is the only part of this the evidence can hold.

THE STANDS ARE OFFERED BY THE STREETS AND KEPT BY THE GROUND. A stand is offered every
`TOWN_PITCH_M` of a street's own centreline — 34 m on a principal street, 70 m on an
ordinary one, 110 m down a lane, because that is the traffic each carries — at the verge
outside the travelled track. Then the ground answers, and it refuses far more than it
keeps. A stand is refused IN WRITING, with its reason, if it would put a wagon inside a
committed footprint or within a metre of one; on a plank walk or a board crossing
(`data/frontage/`, the same rectangles `frontage.js` hands the planters as `keepOut`); in
a dooryard garden or an animal pen (`data/enclosures/`'s own `ground.treatment` — a wagon
belongs on a WORKING yard's worn earth and nowhere else behind a fence); in the travelled
track of any street including its own, at a crossing most of all; on a wharf deck or a
beached hull; below the water surface or off the modelled ground; or within six metres of
a wagon already standing. Both sides of the street are tried, in a stated order, and a
stand that fails on both records both reasons.

WHAT THE PICTURES DRIVE, and it is the type rather than the place. The owner's brief
(`data/sources/assets/owner_brief_2026_08_18/README.md`) draws an ox-drawn COVERED WAGON
TRAIN on the river street (image 11), farm wagons in the Green Tree's yard and a covered
wagon under its shed (image 7), and a covered wagon on the open road (image 12). A tier-5
retrospective view may drive furniture and setting and may never drive a coordinate, so
the plates decide WHAT stands and the street lines decide WHERE: the river street's wagons
are all covered and all drawn up the same way, a principal street alternates covered and
farm box, an ordinary street runs farm boxes with a two-wheeled cart at every third stand,
and a lane gets carts. NO DRAFT ANIMAL IS DRAWN ANYWHERE — this project models no fauna in
the scene at all (`renderers/web/js/fauna.js` is a card, not a herd) — so every wagon here
stands UNHITCHED: tongues and shafts down on the ground, and the ox-yokes laid by on the
grass beside the covered wagons and the yard wagons.

WHAT IS INVENTED is every object on this record: that these particular frontages had goods
out on 1 July 1835, how many, and what a barrel, a crate and a wagon of this place and year
looked like. All of it is graded `reconstructed` and claimed in `docs/LIBERTIES.md` L131.

THE MARKS ON THEM (T-0065), AND THE RESTRAINT THAT WAS OVERRULED. This file used to end the
paragraph above with *"no barrel carries a mark, a brand, a merchant's name or a stencil, and
no crate is labelled"* — L25's discipline for the one documented sign, generalised twice.
**The owner closed it, 2026-08-18, verbatim: "you can add period correct names and brands and
labels to things."** His standing ruling of the same day covers the tier: *"you are totally
fine to be liberal with adding reconstructed items when i ask for things, you can just label
and mark them as such."* It is the same override T-0064 took for the wagons and T-0066 for the
signboards, and the answer is the same shape: the mark is `reconstructed`, it is dealt by a
RULE rather than typed, and `docs/LIBERTIES.md` L166 states its bounds.

WHAT A MARK MAY SAY, and every clause of this is a fence around the invention.

  * **The house's own name** — already in this dataset, already attested, already painted on
    the board one layer over. `_house_mark` takes the possessive owner out of the record's
    name ("P. F. W. Peck's Store" -> "P. F. W. PECK") and otherwise keeps the name the
    signboard paints, so a cask at Peck's door and the board over it agree.
  * **A commodity word from the trade's OWN attested description.** The dossiers write these
    businesses up in their own advertisements' words — Peck *"advertising dry goods, hardware
    and groceries"*, Brewster & Hogan *"dealers in dry goods, groceries and hardware"*, Jones's
    *"grocery and provision store"* — so the CATEGORY a stencil names is the category the
    source names, and only the individual word on the individual cask is invented. The stocks
    are in `MARK_STOCKS`, one list per trade class, each list bounded by that description.
  * **A destination, and one port.** A packing case in transit carried its consignee and where
    it was going, so the cases read the house's mark over "CHICAGO". The forwarding houses'
    cases add the port they came from, and the port is not free either: the schooner arrivals
    the dossiers record come from BUFFALO (`docs/research/04-structures-south.md`, the
    *Jackson* from Buffalo 1833-06-27).
  * **Nothing else.** No trademark, no maker nobody in this town is recorded as dealing with,
    no price, no date, no slogan. A word that is not the house's own name or a period commodity
    of its own attested trade does not go on a barrel.

WHICH MARK LANDS ON WHICH CASK is dealt, not chosen: `_rank` is a sha1 of the structure id, so
the deal is the same on every run and two neighbouring frontages do not both open with FLOUR.
Every third cask on a frontage carries the HOUSE's brand instead of a commodity, because a
cooper's or a merchant's brand burned into the head is as period-correct as the stencil and it
is what ties the goods to the door they stand at.

    python3 tools/generate_yard_goods.py            write the record
    python3 tools/generate_yard_goods.py --check    re-derive and diff
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "generators"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from archetypes.frame_tavern_params import from_phase as _tavern_params  # noqa: E402
from heightfield import Heightfield  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SIDECARS = DATA / "sidecars" / "1835"
STRUCTURES = DATA / "structures"
ENCLOSURES = DATA / "enclosures"
FRONTAGE = DATA / "frontage"
STREETS = DATA / "streets" / "1835.json"
WHARVES = DATA / "wharves" / "river_landings.json"
BOATS = DATA / "boats" / "era_boats.json"
EPOCH = DATA / "terrain" / "epochs" / "e1834_harbor_cut"
OUT = DATA / "yard" / "town_trade_goods.json"

# Clause 2. `function.value` as the structure records write it, and why goods belong on
# that ground. The phrase on the right is quoted into the record, frontage by frontage.
GOODS_TRADES = {
    "tavern_inn": "a public house takes its provisions in by the barrel and puts the empties back out",
    "hotel": "a public house takes its provisions in by the barrel and puts the empties back out",
    "boarding_house": "a lodging house is fed out of the same barrels a tavern is",
    "store": "a counter whose stock arrives in boxes and barrels off a lake schooner",
    "store_residence": "a counter whose stock arrives in boxes and barrels off a lake schooner",
    "store_and_dwelling": "a counter whose stock arrives in boxes and barrels off a lake schooner",
    "dwelling_and_store": "a counter whose stock arrives in boxes and barrels off a lake schooner",
    "dwelling_and_trading_house": "a trading house's stock stands on the ground before it goes inside",
    "grocery_and_provision_store": "provisions are sold out of the barrel they arrived in",
    "drug_store": "a counter whose stock arrives in boxes and barrels off a lake schooner",
    "printing_office_and_store": "an office that sold over a counter, and paper travels in cases",
    "forwarding_and_commission_store": "a forwarding house IS goods standing between a vessel and a wagon",
    "forwarding_commission_warehouse": "a forwarding house IS goods standing between a vessel and a wagon",
    "auction_room": "an auction's lots stand out where they can be looked over",
}

# Clause 3.
TRADE_GRADES = {"attested", "documented", "inferred"}

# Clause 5. Federal ground inside the palisade. The corporation's ordinance is the whole
# evidence on this record and it did not reach these two doors.
FORT_TRADES = {"provision store", "sutler's store"}

# --------------------------------------------------------------------------- #
# THE MARKS (T-0065)                                                           #
# --------------------------------------------------------------------------- #

# Which stock a trade's casks carry. The KEY is the class, the trades map onto it below,
# and every list is bounded by what the dossiers say that class of business dealt in —
# never by what would look good on a barrel.
MARK_STOCK_CLASS = {
    "tavern_inn": "provision",
    "hotel": "provision",
    "boarding_house": "provision",
    "grocery_and_provision_store": "provision",
    "store": "counter",
    "store_residence": "counter",
    "store_and_dwelling": "counter",
    "dwelling_and_store": "counter",
    "printing_office_and_store": "counter",
    "drug_store": "druggist",
    "dwelling_and_trading_house": "trading",
    "forwarding_and_commission_store": "forwarding",
    "forwarding_commission_warehouse": "forwarding",
    "auction_room": "auction",
}

# The words themselves, and what bounds each list.
MARK_STOCKS = {
    # A public house is fed out of the same barrels a provision store is, and the
    # dossiers write Jones's up as a "grocery and provision store" in its own 1834
    # advertisement's words.
    "provision": ["FLOUR", "PORK", "SALT", "WHISKEY", "CIDER", "VINEGAR"],
    # Peck "advertising dry goods, hardware and groceries", Brewster & Hogan "dealers in
    # dry goods, groceries and hardware" — the counter trades' own descriptions.
    "counter": ["FLOUR", "SALT", "SUGAR", "COFFEE", "NAILS", "WHISKEY"],
    # A druggist's barrels are a druggist's: oil, spirits and the two bulk salts every
    # period shop list carries. Carpenter's trade is attested; the stock is not.
    "druggist": ["LINSEED OIL", "TURPENTINE", "EPSOM SALTS", "ALUM"],
    # A trading house's stock stands on the ground before it goes inside. These four
    # were originally kept to "the provisions and the two dry stores every frontier
    # counter held" — a plausibility argument with no source under it, which is the one
    # place L166's fence (a commodity word out of the trade's OWN attested description)
    # could not be met, because Beaubien's trading house has no attested description of
    # its stock. T-0596 gave them one: all four are named in the American Fur Company's
    # own catalogue of goods furnished for the trade of the Chicago country, filed as
    # bk_afc_018 — flour, barrel salt, gunpowder and tobacco. THE LIST DID NOT CHANGE
    # AND MAY NOT GROW FROM THAT CATALOGUE: it is c.1828 and it is a district rather
    # than a shop, so it corroborates a word already standing and warrants no new one.
    # Nothing here names or depicts the people the house traded with, which is
    # AGENTS.md's L1 constraint and is not relaxed by a citation. Ruling: L221.
    "trading": ["FLOUR", "SALT", "POWDER", "TOBACCO"],
    # A forwarding house's barrels are somebody else's, in transit between a vessel and
    # a wagon — the produce the lake trade moved out of this river.
    "forwarding": ["FLOUR", "PORK", "SALT", "POTASH"],
    # An auction's lots are whatever came off the last vessel.
    "auction": ["FLOUR", "SALT", "NAILS", "TOBACCO"],
}

# What a packing case says when it is not carrying a shipping mark: the class's own dry
# goods, in the one word a case would be stencilled with.
MARK_CASE_WORD = {
    "provision": "TEA",
    "counter": "DRY GOODS",
    "druggist": "GLASS",
    # HARDWARE: the catalogue's half axes, covered copper kettles, nails, fine steels,
    # gun flints, kettle chains, pen knives and stirrup irons (bk_afc_018, T-0596).
    "trading": "HARDWARE",
    "forwarding": "MERCHANDISE",
    "auction": "SUNDRIES",
}

# The one port this project can name. `docs/research/04-structures-south.md` records the
# schooner Jackson arriving from Buffalo on 1833-06-27 and the Illinois entering the
# river in 1834; Buffalo is the lake head this dataset has in writing, so it is the only
# place of shipment a case is allowed to name.
MARK_PORT = "BUFFALO"

# Every third cask carries the house's brand rather than a commodity word.
MARK_BRAND_EVERY = 3


def _rank(sid: str, n: int) -> int:
    """A stable integer for a structure id, so the deal is the same on every run.

    hashlib rather than `hash()` for the reason tools/generate_business_signboards.py
    gives at the same line: Python randomises string hashing per process, and a record
    that re-derives differently on the next run is not a derivation.
    """
    return int(hashlib.sha1(sid.encode("utf-8")).hexdigest()[:8], 16) % n


def _slew(wid: str, envelope_deg: float) -> float:
    """How far off its derived bearing one wagon stands, dealt from its own id.

    T-0836. `_rank` for the same reason every other invented attribute on this layer
    uses it: the deal has to be the same on every run, and `check.sh` re-derives this
    record byte for byte. The envelope is walked end to end in `WAGON_SLEW_STEPS`, so
    the middle step is dead square — a town where NO wagon is square would be as much
    an invention as one where they all are.
    """
    step = _rank(wid, WAGON_SLEW_STEPS)
    return _round(-envelope_deg + step * (2.0 * envelope_deg / (WAGON_SLEW_STEPS - 1)), 1)


def _house_mark(name: str) -> str:
    """The house's own mark, as a stencil or a brand would carry it.

    The possessive owner where the record's name has one — "P. F. W. Peck's Store" is
    marked "P. F. W. PECK", "Newberry & Dole's Forwarding and Commission Warehouse" is
    "NEWBERRY & DOLE" — because that is the part a merchant burned into a stave, and the
    trailing trade words are this dataset saying what the building is. Where there is no
    possessive the mark is the name the signboard paints, less the parenthetical that
    disambiguates the model rather than naming the house: "Tremont House (the first)" is
    marked "TREMONT HOUSE", the same string tools/generate_business_signboards.py's
    `_sign_text` puts on the board over the door.
    """
    text = " ".join((name or "").split())
    if text.endswith(")") and "(" in text:
        text = text[:text.rindex("(")].strip()
    for poss in ("'s ", "\u2019s "):
        if poss in text:
            text = text[:text.index(poss)]
            break
    # A brand does not open with the definite article: "The Chicago Democrat Office" is
    # marked CHICAGO DEMOCRAT OFFICE, the way a masthead's own name reads.
    if text.lower().startswith("the "):
        text = text[4:]
    return text.upper()


def _mark_items(items: list, sid: str, name: str, trade: str) -> None:
    """Deal every barrel and case on one frontage its mark, in place.

    The deal is `_rank(sid)` offset so the town does not read FLOUR, FLOUR, FLOUR down a
    street, and the ORDER within a frontage is the order the objects were stood out, so
    the mark a cask carries is a function of where it stands and nothing else.
    """
    klass = MARK_STOCK_CLASS.get(trade)
    if klass is None:
        return
    stock = MARK_STOCKS[klass]
    house = _house_mark(name)
    start = _rank(sid, len(stock))
    barrel_i = 0
    crate_i = 0
    for item in items:
        if item["kind"] == "barrel":
            if barrel_i % MARK_BRAND_EVERY == MARK_BRAND_EVERY - 1:
                item["mark"] = {
                    "lines": [house],
                    "letterform": "brand",
                    "says": "house",
                }
            else:
                item["mark"] = {
                    "lines": [stock[(start + barrel_i) % len(stock)]],
                    "letterform": "stencil",
                    "says": "commodity",
                }
            barrel_i += 1
        elif item["kind"] == "crate":
            if crate_i == 0:
                lines = [house, "CHICAGO"]
                if klass == "forwarding":
                    lines = [house, "CHICAGO", f"FROM {MARK_PORT}"]
                item["mark"] = {"lines": lines, "letterform": "shipping",
                                "says": "shipping"}
            else:
                item["mark"] = {"lines": [MARK_CASE_WORD[klass]],
                                "letterform": "stencil", "says": "commodity"}
            crate_i += 1


# THE OBJECTS, and why their sizes are here rather than on the record. A barrel's girth
# and a crate's boards are HOW a thing is drawn, not a claim about any shop — the same
# division the enclosure layer makes between a fence's line (the record's) and a rail's
# thickness (the renderer's). They are written into the record's `form` block once, graded
# and noted there, and the renderer reads them from it.
BARREL_H_M = 0.84          # 33 in — a provision barrel on its head
BARREL_BELLY_D_M = 0.53    # 21 in at the bilge
BARREL_HEAD_D_M = 0.45     # 17.5 in at the head
CRATE_L_M = 1.05
CRATE_W_M = 0.72
CRATE_H_M = 0.62
CRATE_2_SCALE = 0.72       # the case stacked on the first one is smaller

STANDOFF_M = 0.55          # from the facade plane to the goods' own centre line
END_CLEAR_M = 0.50         # never closer than this to the end of the wall
BARREL_PITCH_M = 0.62      # centre to centre in a row: a barrel and a hand's width
MIN_FRONTAGE_M = 2.0       # under this there is no footway to stand anything on
BARREL_PER_M = 2.2         # one upright barrel per this much usable wall
BARREL_MAX = 4
CRATE_AT_M = 4.0           # usable wall before a crate is put out
CRATE2_AT_M = 7.0          # and before a second one is stacked on it
LAID_AT_M = 5.0            # a public house's empty, on its side, at this much wall

# THE WAGON. A farm wagon of the period, recorded converted from feet.
WAGON_BODY_L_M = 3.05      # 10 ft
WAGON_BODY_W_M = 1.07      # 3 ft 6 in
WAGON_BODY_H_M = 0.55
WAGON_BED_Y_M = 0.95       # the bed's underside above the ground
WAGON_REAR_WHEEL_D_M = 1.37   # 4 ft 6 in
WAGON_FRONT_WHEEL_D_M = 1.07  # 3 ft 6 in
WAGON_TONGUE_M = 2.75
WAGON_CLEAR_M = 1.6        # the half-width of ground a parked wagon needs round it

# THE TWO-WHEELED CART — T-0064's third type, and the cheapest vehicle in the town. One
# axle, tall wheels, a short box and a pair of shafts instead of a tongue. Every number
# invented and recorded converted, the same as the farm wagon's above.
CART_BODY_L_M = 1.98       # 6 ft 6 in
CART_BODY_W_M = 1.07       # 3 ft 6 in, the same track as the wagon
CART_BODY_H_M = 0.50
CART_WHEEL_D_M = 1.42      # 4 ft 8 in — a cart wheel is taller than a wagon's
CART_BED_Y_M = 0.86        # the bed's underside above the ground
CART_SHAFT_M = 2.44        # 8 ft, down on the grass because nothing is in them

# THE OX-YOKE LAID BY. No draft animal is drawn anywhere in this scene, so a wagon that
# came in off the road stands unhitched and its yoke lies on the grass beside it. A beam
# and two bows, invented, recorded converted from feet.
YOKE_BEAM_M = 1.42         # 4 ft 8 in between the bows
YOKE_BEAM_SQ_M = 0.12
YOKE_BOW_M = 0.34          # the bow's own reach past the beam
YOKE_BOW_SQ_M = 0.05
YOKE_OFFSET_M = 1.35       # from the wagon's centreline, out on the near side

# --------------------------------------------------------------------------- #
# THE TOWN'S OWN WAGONS — T-0064. Every constant here is a RULE'S parameter rather
# than a claim about any wagon: how often a street offers a stand, and how much air a
# wagon has to have round it before this record will draw one. The wagon itself is
# still the farm wagon above.
# --------------------------------------------------------------------------- #
# How much street run buys one offered stand, by the street record's OWN `traffic`
# class. A principal street carries the traffic and is where a wagon stands waiting;
# a lane sees one now and then. Nothing measures this and nothing could; what makes
# it a rule rather than a scatter is that it is arithmetic on a committed centreline.
TOWN_PITCH_M = {"principal": 48.0, "ordinary": 90.0, "light": 140.0}
TOWN_PITCH_DEFAULT_M = 140.0
# THE RIVER STREET IS THE ONE STREET A PICTURE SPEAKS ABOUT. Image 11 of the owner's
# brief draws an ox-drawn COVERED WAGON TRAIN on it — a run of tilts nose to tail, not
# one wagon standing by itself — so South Water's stands are offered four times as
# often as any other principal street's and every one of them is covered. The plate
# gives the FORM and the density; the committed centreline still gives every metre.
TOWN_TRAIN_STREET = "south_water"
TOWN_TRAIN_PITCH_M = 20.0
# A wagon stands where there is a town to stand in. Past this from every committed
# footprint the street is running out into the prairie, and a wagon parked in the
# grass two blocks past the last house would be this record inventing a reason.
TOWN_REACH_M = 16.0
TOWN_TRACK_CLEAR_M = 1.00   # between a wagon's own ground and any travelled track
TOWN_WALK_CLEAR_M = 0.60    # and any plank walk or board crossing
TOWN_WALL_CLEAR_M = 1.00    # and any committed wall
TOWN_WHARF_CLEAR_M = 0.80   # and any committed wharf deck
TOWN_HULL_CLEAR_M = 4.00    # and any hull drawn up on the bank
TOWN_DRY_M = 0.60           # over the water surface, under the wheels
TOWN_EDGE_INSET_M = 3.00    # off the heightfield's own edge
TOWN_GAP_M = 1.20           # of air between one wagon's ground and the next's
WAGON_HALF_W_M = 0.75       # the wagon's own half-width over its hubs

# HOW FAR OFF SQUARE ONE WAGON STANDS — T-0836. Every stand above is derived square to
# something: to the road it serves, or to the yard's own long axis. That is where the
# rule PUTS a wagon; it is not how a wagon that has been left standing actually sits.
# Nobody squared an unhitched wagon to a kerb in 1835 — there was no kerb, the verge was
# mud and grass, and a man who has backed a loaded box up to a door and dropped the
# tongue leaves it where it stopped. So each wagon is slewed off its derived bearing by
# an angle dealt from its OWN id, inside an envelope that says how hard the manoeuvre
# was: smallest for one driven up ALONG a road, where the road itself lines it up;
# larger for one backed SQUARE to the road, which is the harder manoeuvre and the one a
# driver judges over his shoulder; largest in a YARD, where there is no line to work to
# at all. The envelope is a claim about how the town LOOKED, and it is written down:
# docs/LIBERTIES.md L230. The slew is dealt, never chosen and never random — the same
# sha1-of-the-id `_rank` deals every other invented attribute on this layer with.
WAGON_SLEW_ALONG_DEG = 6.0
WAGON_SLEW_SQUARE_DEG = 12.0
WAGON_SLEW_YARD_DEG = 15.0
WAGON_SLEW_STEPS = 9        # of the envelope, end to end, so the deal is reproducible

# What each kind is called in the prose of its own record.
KIND_WORDS = {
    "farm_box": "farm box wagon",
    "covered": "covered emigrant wagon",
    "cart": "two-wheeled cart",
}

# Clause: fenced ground. `data/enclosures/` states what the ground inside each fence is
# (T-0067). A wagon belongs on a WORKING yard's worn earth; a dooryard garden and an
# animal pen are refused in writing.
WORKING_YARD_TREATMENT = "worn_earth"
YARD_WAGON_MAX = 3          # per working yard, the attested one included
YARD_LATTICE_M = 0.5

# THE GREEN TREE'S YARD — ticket T-0080, and the first place in this town where a
# PICTURE rather than a rule says what stood outside a door. The Trowbridge drawing
# of the inn (data/sources/assets/owner_brief_2026_08_18/README.md, image 7) shows
# farm wagons standing in the yard and a bench against the front wall. It is a tier-5
# retrospective view and may drive furniture and setting as this project's third tier,
# never a coordinate — so WHAT is here comes from the plate and WHERE is derived from
# the committed footprint, the same division every layer on this ground keeps.
GREEN_TREE_ID = "green_tree_tavern"
GT_WALL_CLEAR_M = 1.0      # a wagon stands this far off the rear wall it is drawn up to
GT_WAGON_MAX = 3           # the yard's own width decides the count; this is its ceiling

# THE WAGON SHED AT THE GREEN TREE — ticket T-0081, the second thing the Trowbridge
# drawing puts on this inn's ground: an OPEN-SIDED WAGON SHED with a COVERED WAGON
# standing under it. Everything here is a size, never a place; where the shed stands
# is derived from the committed footprint the same way the wagons' stands were.
GT_SHED_END_M = 0.50       # air past each end of the wagon's body, along the wall
GT_SHED_HEADROOM_M = 0.35  # clear air over the tilt at the open eave
GT_SHED_PITCH_DEG = 12.0   # the lean-to's fall, out from the wall it leans on
GT_SHED_POST_M = 0.14      # 5.5 in square posts under the open side
GT_SHED_PLATE_M = 0.16     # the plates and the rafters over them

# THE TILT — the covered wagon's canvas, on bows over the same farm wagon body the
# yard already draws. A rise and an overhang, and nothing else: the bows under it
# are not drawn for the reason the barrels' hoops are not.
WAGON_TILT_RISE_M = 1.10       # the canvas's rise over the body's top rail
WAGON_TILT_OVERHANG_M = 0.12   # the canvas pulled past the end bows

# THE BENCH. A backless plank bench, recorded converted from feet: 6 ft long, 14 in
# deep, 18 in to the seat, on two plank ends. Not one of those numbers is a record's.
BENCH_L_M = 1.83
BENCH_SEAT_D_M = 0.36
BENCH_SEAT_H_M = 0.46
BENCH_PLANK_T_M = 0.045


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _round(x: float, places: int = 2) -> float:
    """Round toward a stable decimal so `--check` diffs bytes, not float noise."""
    return round(x + 0.0, places) + 0.0


def _to_enu(u: float, v: float, place: dict) -> tuple[float, float]:
    """A footprint coordinate to local ENU metres — the signboard generator's frame.

    docs/GLB-CONTRACT.md: polygon `u` → +X, polygon `v` → −Z, ENU `local_e` → +X and
    `local_n` → −Z, and the node's yaw is `-rotation_deg` about +Y.
    """
    th = math.radians(-(place.get("rotation_deg") or 0.0))
    x, z = u, -v
    xr = x * math.cos(th) + z * math.sin(th)
    zr = -x * math.sin(th) + z * math.cos(th)
    return (place.get("local_e") or 0.0) + xr, (place.get("local_n") or 0.0) - zr


def _front_edge(polygon: list) -> tuple[float, float, float]:
    """The front wall: the footprint's max-`v` edge, as (u_min, u_max, v)."""
    vmax = max(p[1] for p in polygon)
    on = [p[0] for p in polygon if abs(p[1] - vmax) < 1e-6]
    if len(on) < 2:
        return 0.0, 0.0, vmax
    return min(on), max(on), vmax


def _footprint_world(sidecar: dict) -> list[tuple[float, float]]:
    """A committed footprint in local ENU metres, placed and rotated."""
    poly = (sidecar.get("footprint") or {}).get("polygon") or []
    place = sidecar.get("placement") or {}
    if place.get("local_e") is None or len(poly) < 3:
        return []
    return [_to_enu(u, v, place) for u, v in poly]


def _poly_contains(pt, poly) -> bool:
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def _dist_to_polygon(pt, poly) -> float:
    """Distance from a point to a polygon's boundary; negative when inside it."""
    x, y = pt
    best = float("inf")
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2))
        best = min(best, math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)))
    return -best if _poly_contains(pt, poly) else best


def _dist_to_path(pt, path) -> float:
    """Distance from a point to an open polyline — a fence run is not a ring."""
    x, y = pt
    best = float("inf")
    for i in range(len(path) - 1):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2))
        best = min(best, math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)))
    return best


def _standing() -> tuple[list[str], dict]:
    index = _load(SIDECARS / "index.json")
    ids = [s["id"] for s in index.get("structures", [])]
    cars = {}
    for sid in ids:
        path = SIDECARS / f"{sid}.json"
        if path.exists():
            cars[sid] = _load(path)
    return ids, cars


# --------------------------------------------------------------------------- #
# the frontages                                                                #
# --------------------------------------------------------------------------- #

def build_frontages(ids: list[str], cars: dict) -> tuple[list, list]:
    worlds = {sid: _footprint_world(sc) for sid, sc in cars.items()}
    frontages: list[dict] = []
    refused: list[dict] = []

    for sid in ids:
        sc = cars.get(sid)
        if sc is None:
            continue
        attrs = sc.get("attributes") or {}
        fn = attrs.get("function") or {}
        trade = fn.get("value")
        if trade in FORT_TRADES:
            refused.append({"structure_id": sid, "trade": trade, "why": (
                "it stands on federal ground inside the fort's palisade. The whole "
                "evidence on this record is the village corporation's Ordinance 9 of "
                "7 November 1833, and the corporation's streets did not reach this door; "
                "there is no public frontage in front of it to stand a barrel on. The "
                "garrison's stores are a different claim and would need a different "
                "source.")})
            continue                                            # clause 5
        if trade not in GOODS_TRADES:
            continue                                            # clause 2
        if sid.startswith(("inf_", "recon_")) or \
                (sc.get("name") or "").startswith("Reconstructed"):
            refused.append({"structure_id": sid, "trade": trade, "why": (
                "an anonymous slot. The archetype tables' own rule — never invent "
                "business, sign text or GOODS for an anonymous slot — names goods in as "
                "many words, and this record keeps it.")})
            continue                                            # clause 1
        grade = fn.get("confidence")
        if grade not in TRADE_GRADES:
            refused.append({"structure_id": sid, "trade": trade, "why": (
                f"the trade itself is {grade}. Stock standing outside a business this "
                "project reconstructed would be an invention resting on an invention.")})
            continue                                            # clause 3

        place = sc.get("placement") or {}
        poly = (sc.get("footprint") or {}).get("polygon") or []
        if len(poly) < 3 or place.get("local_e") is None:
            refused.append({"structure_id": sid, "trade": trade,
                            "why": "no placed footprint — no frontage to stand goods on."})
            continue
        u0, u1, vmax = _front_edge(poly)
        run = (u1 - u0) - 2 * END_CLEAR_M
        if run < MIN_FRONTAGE_M:
            refused.append({"structure_id": sid, "trade": trade, "why": (
                f"only {max(run, 0):.2f} m of usable frontage — under the "
                f"{MIN_FRONTAGE_M:.2f} m this record calls a footway.")})
            continue

        bearing = float(place.get("rotation_deg") or 0.0)
        # Out of the wall, in ENU. `rotation_deg` IS the facade bearing, so the outward
        # normal is (sin b, cos b) and the along-wall direction is the +u axis.
        b = math.radians(bearing)
        others = [(oid, w) for oid, w in worlds.items() if oid != sid and len(w) >= 3]

        def at(u_along: float) -> tuple[float, float]:
            e, n = _to_enu(u_along, vmax, place)
            return e + math.sin(b) * STANDOFF_M, n + math.cos(b) * STANDOFF_M

        items: list[dict] = []
        n_barrels = max(1, min(BARREL_MAX, int(run // BARREL_PER_M)))
        u = u0 + END_CLEAR_M + BARREL_PITCH_M / 2
        for _ in range(n_barrels):
            e, n = at(u)
            items.append({"kind": "barrel", "pose": "upright",
                          "at_local_enu_m": [_round(e), _round(n)],
                          "bearing_deg": _round(bearing, 1)})
            u += BARREL_PITCH_M
        if run >= LAID_AT_M and trade in ("tavern_inn", "hotel", "boarding_house"):
            u += 0.35
            e, n = at(u)
            items.append({"kind": "barrel", "pose": "laid",
                          "at_local_enu_m": [_round(e), _round(n)],
                          "bearing_deg": _round(bearing, 1)})
            u += 0.65
        if run >= CRATE_AT_M:
            u += CRATE_L_M / 2 + 0.15
            e, n = at(u)
            items.append({"kind": "crate", "tier": 0,
                          "at_local_enu_m": [_round(e), _round(n)],
                          "bearing_deg": _round(bearing, 1)})
            if run >= CRATE2_AT_M:
                items.append({"kind": "crate", "tier": 1,
                              "at_local_enu_m": [_round(e), _round(n)],
                              "bearing_deg": _round(bearing, 1)})
            u += CRATE_L_M / 2

        # Clause 6. Nothing stands inside a neighbour's committed footprint.
        kept, dropped = [], []
        for item in items:
            pt = tuple(item["at_local_enu_m"])
            hit = next((oid for oid, w in others if _poly_contains(pt, w)), None)
            if hit:
                dropped.append(hit)
            else:
                kept.append(item)
        if dropped:
            refused.append({"structure_id": sid, "trade": trade, "why": (
                f"{len(dropped)} object(s) fell inside "
                f"{sorted(set(dropped))[0]}'s committed footprint, which stands over "
                "this frontage's own strip; they are dropped rather than nudged, because "
                "a nudged coordinate is a placed one.")})
        if not kept:
            continue

        # T-0065. The marks are dealt over what STANDS, after clause 6 has taken away
        # anything that fell inside a neighbour's footprint — so a dropped cask does not
        # leave a hole in the deal and the third-cask brand still lands on a third cask.
        _mark_items(kept, sid, sc.get("name") or "", trade)

        quad = [_to_enu(uu, vv, place) for uu, vv in (
            (min(p[0] for p in poly), min(p[1] for p in poly)),
            (max(p[0] for p in poly), min(p[1] for p in poly)),
            (max(p[0] for p in poly), max(p[1] for p in poly)),
            (min(p[0] for p in poly), max(p[1] for p in poly)))]

        frontages.append({
            "structure_id": sid,
            "name": sc.get("name"),
            "trade": trade,
            "trade_confidence": grade,
            "why_goods": GOODS_TRADES[trade],
            "confidence": "reconstructed",
            "facade_bearing_deg": _round(bearing, 1),
            "frontage_m": _round(u1 - u0),
            "usable_frontage_m": _round(run),
            "standoff_m": STANDOFF_M,
            "ground_quad_local_enu_m": [[_round(p[0]), _round(p[1])] for p in quad],
            "items": kept,
        })

    frontages.sort(key=lambda f: f["structure_id"])
    refused.sort(key=lambda r: r["structure_id"])
    return frontages, refused


# --------------------------------------------------------------------------- #
# the wagon                                                                    #
# --------------------------------------------------------------------------- #

def build_wagons(cars: dict) -> tuple[list, list]:
    """One wagon, in the yard a source calls a wagon yard, at a derived point."""
    path = ENCLOSURES / "western_hotel_wagon_yard.json"
    if not path.exists():
        return [], [{"enclosure_id": "western_hotel_wagon_yard",
                     "why": "the enclosure record is missing — no wagon is drawn."}]
    yard = _load(path)
    runs = [r.get("path_local_enu_m") or [] for r in yard.get("runs", [])]
    pts = [p for r in runs for p in r]
    if len(pts) < 3:
        return [], [{"enclosure_id": yard.get("id"),
                     "why": "the yard record carries no fence line to derive a stand from."}]
    e_lo, e_hi = min(p[0] for p in pts), max(p[0] for p in pts)
    n_lo, n_hi = min(p[1] for p in pts), max(p[1] for p in pts)

    walls = [(sid, w) for sid, w in
             ((sid, _footprint_world(sc)) for sid, sc in cars.items()) if len(w) >= 3]

    # THE STAND IS SEARCHED, NOT CHOSEN: a 0.25 m lattice over the yard's own bounding
    # box, keeping the point whose least clearance — to every committed wall and to
    # every fence line of the yard — is greatest. Ties break toward the south and then
    # the west, so the answer does not depend on iteration order.
    best, best_clear = None, -1.0
    step = 0.25
    steps_e = int((e_hi - e_lo) / step)
    steps_n = int((n_hi - n_lo) / step)
    for i in range(steps_n + 1):
        n = _round(n_lo + i * step, 3)
        for j in range(steps_e + 1):
            e = _round(e_lo + j * step, 3)
            clear = min(min(_dist_to_polygon((e, n), w) for _, w in walls),
                        min(_dist_to_path((e, n), r) for r in runs if len(r) >= 2))
            if clear > best_clear + 1e-9:
                best, best_clear = (e, n), clear
    if best is None or best_clear < WAGON_CLEAR_M:
        return [], [{"enclosure_id": yard.get("id"), "why": (
            f"the widest clear stand in the yard is {max(best_clear, 0):.2f} m from the "
            f"nearest wall or fence, under the {WAGON_CLEAR_M:.2f} m a parked wagon "
            "needs. No wagon is drawn rather than one drawn through a wall.")}]

    # The yard is longer north-south than east-west and its two gateways are on Canal
    # (west) and Randolph (north), so a wagon standing in it stands along the yard's own
    # long axis. The bearing is the axis, derived from the box, not picked.
    bearing = 0.0 if (n_hi - n_lo) >= (e_hi - e_lo) else 90.0
    return [{
        "id": "western_hotel_wagon_yard_wagon",
        "in_enclosure": yard.get("id"),
        "belongs_to": "western_hotel",
        "confidence": "reconstructed",
        "at_local_enu_m": [_round(best[0]), _round(best[1])],
        "bearing_deg": _round(bearing, 1),
        "kind": "farm_box",
        "clearance_m": _round(best_clear),
        "note": (
            "THE ATTESTED WAGON — the one stand in this town that rests on a source "
            "rather than on a rule. No source this project holds puts a wagon at any "
            "place in Chicago on any day. One place is NAMED for them: "
            "data/enclosures/western_hotel_wagon_yard"
            ".json rests on chicagology_prefire278's 'In the rear was the large stable "
            "and the yard into which the trains were driven', which is a yard, in a "
            "stated place, that wagons were driven into. THE STAND IS DERIVED: a 0.25 m "
            "lattice over the yard's own bounding box, keeping the point whose least "
            f"clearance to every committed wall and every fence line is greatest — "
            f"{_round(best_clear):.2f} m here. The bearing is the yard's long axis. What "
            "is invented is that a wagon was standing in it at noon on 1 July 1835, and "
            "the wagon itself: docs/LIBERTIES.md L131. The town's OTHER wagons — the ones "
            "standing at the street verges and filling this yard round it — are T-0064's "
            "and rest on nothing but the owner's instruction and a rule: L162."
        ),
    }], [{"enclosure_id": "*", "why": (
        "EVERY OTHER PLACE IN THE TOWN, refused in writing UNTIL 2026-08-21, AND THE "
        "REFUSAL IS NOW OVERRULED. This entry used to read: 'docs/ROADMAP.md K5 (c) "
        "offers wagons/drays (documented mired on Lake St) — this project holds no "
        "source record for that, and a dray dropped into Lake Street on the strength of "
        "a roadmap parenthesis would be traffic invented to look busy … the yard whose "
        "own name is the attestation gets the wagon, and the rest wait for a source.' No "
        "source arrived. The OWNER did, 2026-08-18: 'there can be more wagons! of course "
        "there would be more wagons all over the place in a frontier town.' T-0064 is "
        "that instruction and the town's wagons below are it, every one of them "
        "reconstructed and every one of them placed by a rule over the committed street "
        "lines rather than by a hand — see `town_wagon_rule` on this record and "
        "docs/LIBERTIES.md L162. What is still refused, and refused for the same reason "
        "as before, is a wagon standing IN a travelled track: a dray mired in Lake "
        "Street is a scene this project has no source for and would be a claim about the "
        "road as well as about the wagon.")}]


# --------------------------------------------------------------------------- #
# the Green Tree's yard                                                        #
# --------------------------------------------------------------------------- #

def build_green_tree_yard(cars: dict) -> tuple[list, list, list, list]:
    """The wagons, the bench and the wagon shed the Trowbridge view puts at this inn.

    The plate gives the FURNITURE — wagons in the yard, a bench against the front
    wall, an open-sided wagon shed with a covered wagon under it — and a tier-5
    retrospective view may not give a position. So every stand here is derived from
    `data/structures/green_tree_tavern.json`'s own committed footprint and placement,
    and any stand that comes out inside another building's committed wall is refused
    in writing rather than nudged.
    """
    sc = cars.get(GREEN_TREE_ID)
    if not sc:
        return [], [], [], [{"structure_id": GREEN_TREE_ID, "why": (
            "the inn is not standing in data/sidecars/1835 — nothing is put in its yard.")}]
    place = sc.get("placement") or {}
    poly = (sc.get("footprint") or {}).get("polygon") or []
    if place.get("local_e") is None or len(poly) < 3:
        return [], [], [], [{"structure_id": GREEN_TREE_ID, "why": (
            "the inn has no placed footprint — nothing in its yard can be derived.")}]

    u0 = min(p[0] for p in poly)
    u1 = max(p[0] for p in poly)
    v0 = min(p[1] for p in poly)
    v1 = max(p[1] for p in poly)
    front_w = u1 - u0                     # the front wall's own width, 25 ft here
    bearing = float(place.get("rotation_deg") or 0.0)      # the facade bearing

    walls = [(sid, w) for sid, w in
             ((sid, _footprint_world(other)) for sid, other in cars.items()
              if sid != GREEN_TREE_ID) if len(w) >= 3]

    refused: list = []

    # ---- the rear ell, which moved the wall the wagons draw up to ---------- #
    # Since T-0083 the record BUILDS John Gray's low rear addition — a gabled
    # tail off the rear gable end, form.rear_ell, sized by the archetype's own
    # parameters. It stands on the ground the wagons stood on, so the wagons
    # draw up square to ITS far wall instead: same rule, measured from the built
    # rear face. The depth is read from the same parameter resolution the
    # generator uses, so the two cannot drift apart.
    ell_d = 0.0
    rec = _load(STRUCTURES / f"{GREEN_TREE_ID}.json")
    ph = next((p for p in rec.get("phases", []) if p.get("id") == sc.get("phase")),
              (rec.get("phases") or [None])[0])
    if ph is not None and rec.get("archetype") == "frame_tavern":
        tp = _tavern_params(ph)
        if tp.rear_ell:
            ell_d = tp.rear_ell_depth_m

    # ---- the wagons -------------------------------------------------------- #
    # THE YARD'S DEPTH IS THE HOUSE'S OWN FRONT WIDTH, measured from the built
    # rear face (the ell's far wall where the record builds one). Nothing
    # measures this yard, and a yard has to be some depth before a wagon can be
    # put in it; the only length this record holds for the building is its
    # footprint, so the ground behind the built rear face is taken to run back
    # as far as the front is wide. It is an invention and is claimed as one —
    # but it is bounded by the building rather than picked, and it never
    # reaches the next street.
    rear_v = v0 - ell_d
    yard_depth = front_w
    reach = GT_WALL_CLEAR_M + WAGON_BODY_L_M + WAGON_TONGUE_M
    wagons: list = []
    if reach > yard_depth:
        refused.append({"structure_id": GREEN_TREE_ID, "why": (
            f"a wagon with its tongue down reaches {reach:.2f} m back from the wall and "
            f"the yard is taken as {yard_depth:.2f} m deep — no wagon is drawn rather "
            "than one standing in the next lot.")})
    else:
        # Drawn up square to the built rear face, tongues out into the yard: the
        # wagons stand across the yard, not along it, because that face is the
        # only line in the record to be square to.
        v_centre = rear_v - (GT_WALL_CLEAR_M + WAGON_BODY_L_M / 2)
        lo = u0 + WAGON_CLEAR_M
        hi = u1 - WAGON_CLEAR_M
        pitch = 2 * WAGON_CLEAR_M
        n = 0 if hi < lo else min(GT_WAGON_MAX, int((hi - lo) / pitch) + 1)
        if n == 0:
            refused.append({"structure_id": GREEN_TREE_ID, "why": (
                f"the rear wall is {front_w:.2f} m wide and a parked wagon needs "
                f"{2 * WAGON_CLEAR_M:.2f} m of it — no stand fits.")})
        # From the FAR end of the wall inward, so the order does not depend on which
        # way the footprint happens to be wound.
        for i in range(n):
            u = hi - i * pitch
            e, nn = _to_enu(u, v_centre, place)
            clear = min([_dist_to_polygon((e, nn), w) for _, w in walls] or [1e9])
            if clear < WAGON_CLEAR_M:
                refused.append({"structure_id": GREEN_TREE_ID, "why": (
                    f"the stand at local E {_round(e)} N {_round(nn)} is {clear:.2f} m "
                    f"from the nearest committed wall, under the {WAGON_CLEAR_M:.2f} m a "
                    "parked wagon needs — that wagon is not drawn.")})
                continue
            wagons.append({
                "id": f"green_tree_tavern_yard_wagon_{i + 1}",
                "belongs_to": GREEN_TREE_ID,
                "kind": "farm_box",
                "confidence": "reconstructed",
                "at_local_enu_m": [_round(e), _round(nn)],
                "bearing_deg": _round((bearing + 180.0) % 360.0, 1),
                "clearance_m": _round(min(clear, 999.0)),
                "note": (
                    "A FARM WAGON IN THE GREEN TREE'S YARD, and the picture is the whole "
                    "reason it is here. The Trowbridge drawing of this inn "
                    "(data/sources/assets/owner_brief_2026_08_18/README.md, image 7) "
                    "shows farm wagons standing in its yard — a tier-5 retrospective "
                    "view, which may drive furniture and setting and may never drive a "
                    "coordinate. So WHERE is derived: the wagons stand drawn up square "
                    "to the building's built rear face — since T-0083 that is the rear "
                    "ell's far wall — tongues out, "
                    f"{GT_WALL_CLEAR_M:.2f} m clear of it, spaced at the "
                    f"{2 * WAGON_CLEAR_M:.2f} m of ground a parked wagon needs, laid in "
                    "from the far end of that wall. The yard is taken to run back as far "
                    "as the front is wide, which is the only length this record has. "
                    "What is invented is the depth of that yard, that a wagon stood in it "
                    "at noon on 1 July 1835, and the wagon itself: docs/LIBERTIES.md L131 "
                    "and L133."
                ),
            })

    # ---- the bench --------------------------------------------------------- #
    # AGAINST THE FRONT WALL, at the end of the frontage the goods do not occupy.
    # The barrels pile from the -u end, so the +u end at ground level is the clear
    # one — the same division of one wall three layers already make. Until T-0082
    # this inn also carried a wall board hung 1.7 m toward +u at 2.55 m up, which
    # was the third of the three; that board now stands on a post at the street
    # corner and the frontage layer owns it, and the bench is unmoved because it
    # was never the board it had to miss — it is 2 m under where the board hung.
    benches: list = []
    u_c = u1 - END_CLEAR_M - BENCH_L_M / 2
    if u_c - BENCH_L_M / 2 < u0:
        refused.append({"structure_id": GREEN_TREE_ID, "why": (
            f"the front wall is {front_w:.2f} m and a {BENCH_L_M:.2f} m bench with "
            f"{END_CLEAR_M:.2f} m of end clearance does not stand on it — no bench.")})
    else:
        e, nn = _to_enu(u_c, v1 + BENCH_SEAT_D_M / 2, place)
        benches.append({
            "id": "green_tree_tavern_front_bench",
            "belongs_to": GREEN_TREE_ID,
            "kind": "bench",
            "confidence": "reconstructed",
            "at_local_enu_m": [_round(e), _round(nn)],
            "bearing_deg": _round(bearing, 1),
            "note": (
                "THE BENCH AGAINST THE FRONT WALL, and the people on it are not drawn. "
                "The Trowbridge drawing of this inn "
                "(data/sources/assets/owner_brief_2026_08_18/README.md, image 7) shows a "
                "bench of sitters against the front wall of the Green Tree. THE SITTERS "
                "ARE REFERENCE ONLY — AGENTS.md's standing constraint on depicting people "
                "is not relaxed by a plate, and v1 ships no human figures at all — so what "
                "is taken from the picture is the BENCH, which is the buildable fact in it. "
                "Its stand is derived: against the front wall at the +u end, "
                f"{END_CLEAR_M:.2f} m in from the end of the frontage, which is the end "
                "the barrels do not pile at. Its size is invented: docs/LIBERTIES.md L133."
            ),
        })

    # ---- the wagon shed, and the covered wagon standing in it -------------- #
    sheds, shed_wagons, shed_refused = _green_tree_wagon_shed(sc, place, poly, walls)
    wagons.extend(shed_wagons)
    refused.extend(shed_refused)

    return wagons, benches, sheds, refused


def _green_tree_wagon_shed(sc: dict, place: dict, poly: list,
                           walls: list) -> tuple[list, list, list]:
    """The open-sided wagon shed at the inn's yard end, and the tilt under it.

    WHAT THE PLATE GIVES: an open-sided wagon shed attached at the left of the
    house with a covered wagon standing under it. WHAT IT MAY NOT GIVE: which
    wall, and how big. Both are derived here.

    WHICH WALL, and this is the one judgement in the function. The plate's word is
    "left", which is a word about a viewpoint and not about a building — so it is
    read as *the end of the elevation away from the streets*, and three committed
    facts say the same wall. The placement record puts the front on Canal (west)
    and the long side on Lake (south), so the yard is the north and east ground.
    T-0080's two farm wagons already stand off the east (rear) wall, one metre
    clear of it. That leaves the NORTH side wall, which is the only wall of this
    inn that is neither a street frontage nor already occupied — and a wagon shed
    is a yard building, entered off the yard rather than off a corporation street.
    WHAT IS NOT HONOURED, said out loud rather than smoothed over: the committed
    massing runs this building's ridge along its depth (`frame_tavern` lays the
    ridge on the longer axis, 12.19 m here against 7.62 m), which puts its GABLES
    on the front and the rear and makes the north wall an eaves wall. So the shed
    stands at the left END and not at a gable, and the gable half of the plate is
    a correction to the building's fabric, which is bake-gated and is T-0083's.

    HOW BIG is arithmetic on numbers this record already carries: the bay is as
    long as the wagon's body with half a metre of air at each end, as deep as the
    ground `WAGON_CLEAR_M` gives a parked wagon, and its open eave stands a
    hand's breadth over the tilt it has to cover.
    """
    refused: list = []
    u0 = min(p[0] for p in poly)
    u1 = max(p[0] for p in poly)
    v0 = min(p[1] for p in poly)
    v1 = max(p[1] for p in poly)
    side_run = v1 - v0                      # the north wall's own run, 40 ft here
    bearing = float(place.get("rotation_deg") or 0.0)
    # The outward normal of the +u wall as a compass bearing. The facade's normal
    # is +v and its bearing is the placement's rotation, and +u is a quarter turn
    # from +v in this frame — the same derivation `_to_enu` does, read backwards.
    out_bearing = (bearing + 90.0) % 360.0

    depth = 2 * WAGON_CLEAR_M                       # out from the wall
    length = WAGON_BODY_L_M + 2 * GT_SHED_END_M     # along the wall
    tilt_top = WAGON_BED_Y_M + WAGON_BODY_H_M + WAGON_TILT_RISE_M
    eave = tilt_top + GT_SHED_HEADROOM_M            # the open side's plate
    head = eave + depth * math.tan(math.radians(GT_SHED_PITCH_DEG))

    if length > side_run:
        return [], [], [{"structure_id": GREEN_TREE_ID, "why": (
            f"a bay long enough for a wagon is {length:.2f} m and the side wall runs "
            f"{side_run:.2f} m — no shed is drawn rather than one longer than the "
            "wall it leans on.")}]
    # A lean-to is spiked to a wall UNDER that wall's own eaves. The record states
    # this building's wall height, so the constraint is checkable rather than
    # eyeballed, and a shed that would stand through the clapboard is refused.
    wall_h = ((sc.get("attributes") or {}).get("wall_height_m") or {}).get("value")
    if isinstance(wall_h, (int, float)) and head + GT_SHED_PLATE_M > wall_h:
        return [], [], [{"structure_id": GREEN_TREE_ID, "why": (
            f"the lean-to's plate would meet the wall {head + GT_SHED_PLATE_M:.2f} m "
            f"up and the record gives this building {wall_h:.2f} m of wall — no shed "
            "is drawn rather than one through the first-floor windows.")}]

    # The bay stands at the YARD end of that wall: it starts at the rear wall's own
    # plane and runs forward, so it is behind the Canal frontage the sign, the bench
    # and the barrels occupy, and it never reaches the Lake Street corner.
    v_c = v0 + length / 2
    u_c = u1 + depth / 2
    e, nn = _to_enu(u_c, v_c, place)

    # Clearance is measured from the covered ground's own corners, not from its
    # centre: a 3.2 x 4.05 m roof is the largest thing this layer has ever put on
    # the ground and its centre clearing a wall says nothing about its corners.
    corners = [_to_enu(u, v, place) for u, v in (
        (u1, v0), (u1, v0 + length), (u1 + depth, v0 + length), (u1 + depth, v0))]
    clear = min([_dist_to_polygon(c, w) for c in corners for _, w in walls] or [1e9])
    if clear < GT_WALL_CLEAR_M:
        return [], [], [{"structure_id": GREEN_TREE_ID, "why": (
            f"the shed's covered ground comes within {clear:.2f} m of another "
            f"committed wall, under the {GT_WALL_CLEAR_M:.2f} m a building is given — "
            "no shed is drawn rather than one built into a neighbour.")}]

    shed = {
        "id": "green_tree_tavern_wagon_shed",
        "belongs_to": GREEN_TREE_ID,
        "kind": "wagon_shed",
        "confidence": "reconstructed",
        "at_local_enu_m": [_round(e), _round(nn)],
        "bearing_deg": _round(out_bearing, 1),
        "length_m": _round(length),
        "depth_m": _round(depth),
        "eave_m": _round(eave),
        "head_m": _round(head),
        "clearance_m": _round(min(clear, 999.0)),
        "note": (
            "AN OPEN-SIDED WAGON SHED AT THE INN'S YARD END, and the picture is the "
            "whole reason it is here. The Trowbridge drawing of this inn "
            "(data/sources/assets/owner_brief_2026_08_18/README.md, image 7) shows an "
            "open-sided wagon shed attached at the left of the house with a covered "
            "wagon standing under it — a tier-5 retrospective view, which may drive "
            "furniture and setting and may never drive a coordinate. WHICH WALL IS "
            "DERIVED: the placement record puts the front on Canal and the long side "
            "on Lake, T-0080's wagons already stand off the rear wall, and that leaves "
            "the north side wall — the only one of this inn's four that is neither a "
            "street frontage nor already occupied, and a wagon shed is entered off a "
            "yard rather than off a corporation street. WHAT IS NOT HONOURED: the "
            "committed massing lays this building's ridge along its longer axis, which "
            "puts its gables on the front and the rear, so this stands at the left END "
            "and not at a gable; the gable is a correction to the building's fabric and "
            "is bake-gated (T-0083). HOW BIG IS ARITHMETIC on numbers already here: the "
            f"bay is {length:.2f} m along the wall (the wagon's body and "
            f"{GT_SHED_END_M:.2f} m of air at each end) by {depth:.2f} m out from it "
            f"(the ground a parked wagon is given), its open eave stands {eave:.2f} m "
            f"up ({GT_SHED_HEADROOM_M:.2f} m over the tilt it covers) and its plate "
            f"meets the wall {head:.2f} m up at {GT_SHED_PITCH_DEG:.0f} degrees. What "
            "is invented is that this inn had a wagon shed on 1 July 1835 and every "
            "dimension of it: docs/LIBERTIES.md L134. NOT THE SAME THING as the low "
            "one-storey additions John Gray describes at each end of the house — those "
            "are attributes of the BUILDING, dated three to six years after the scene "
            "and deliberately excluded from its footprint; this is a yard structure on "
            "the yard's own ground, and it does not date them."
        ),
    }

    # The covered wagon standing under it, on the same centre as the bay: a shed
    # a wagon cannot stand in is not what the plate shows. It is the yard's own
    # farm wagon with a tilt over it, laid along the wall because that is the way
    # a 4.05 m bay takes a 3.05 m body, tongue down and out of the open end.
    wagon = {
        "id": "green_tree_tavern_shed_wagon",
        "belongs_to": GREEN_TREE_ID,
        "under_shed": shed["id"],
        "kind": "covered",
        "tilt": True,
        "confidence": "reconstructed",
        "at_local_enu_m": [_round(e), _round(nn)],
        "bearing_deg": _round((out_bearing + 90.0) % 360.0, 1),
        "clearance_m": _round(min(clear, 999.0)),
        "note": (
            "THE COVERED WAGON UNDER THE SHED, from the same plate and standing on the "
            "same derived centre as the bay over it. It is the farm wagon this record "
            "already draws — the body, the wheels and the tongue are L131's invented "
            "numbers and have not moved — with a TILT added: canvas on bows, "
            f"{WAGON_TILT_RISE_M:.2f} m of rise over the body's top rail and "
            f"{WAGON_TILT_OVERHANG_M:.2f} m pulled past the end bows, open at both "
            "ends. The bows themselves are not drawn, for the reason the barrels' "
            "hoops are not: under the canvas there is nothing to see. It lies ALONG "
            "the wall because that is how a 4.05 m bay takes a 3.05 m body, with the "
            "tongue down and out of the open end into the yard. What is invented is "
            "the wagon, the tilt and the fact that either stood here on 1 July 1835: "
            "docs/LIBERTIES.md L131 and L134."
        ),
    }
    return [shed], [wagon], refused


# --------------------------------------------------------------------------- #
# the town's own wagons — T-0064                                               #
# --------------------------------------------------------------------------- #

def _town_world(cars: dict) -> dict:
    """Everything a wagon standing in this town has to keep clear of, read ONCE.

    Every entry here is read out of the record that already owns it, and nothing is
    restated: the plank walks are the same rectangles `frontage.js` hands the planters
    as `keepOut`, the fenced interiors are the same rings `yards.js` lays its ground
    treatments over and answers `treatmentAt` from, the travelled tracks are the same
    half-widths `streets.js` draws and `generate_frontage_works.py` refuses a signpost
    against, and the wharf decks and beached hulls are `wharves.keepOut` and
    `boats.keepOut`. A second mechanism for any of them would be a second answer, and
    two answers about the same ground is how a wagon ends up standing on a footway.
    """
    walls = [(sid, w) for sid, w in
             ((sid, _footprint_world(sc)) for sid, sc in cars.items()) if len(w) >= 3]

    streets = []
    for s in _load(STREETS).get("streets", []):
        path = [tuple(p) for p in s.get("path_local_enu_m", [])]
        if len(path) < 2:
            continue
        streets.append({
            "id": s["id"],
            "name": s.get("name_1835") or s["id"],
            "path": path,
            "track_w": float(s.get("track_width_m") or 7.0),
            "traffic": s.get("traffic") or "light",
        })
    streets.sort(key=lambda s: s["id"])

    # The walks, segment by segment with their own half-width — exactly the rectangles
    # `frontage.js` builds for `keepOut`, derived here from the same records.
    walks = []
    for path in sorted(FRONTAGE.glob("*.json")):
        if path.name == "index.json":
            continue
        rec = _load(path)
        for walk in rec.get("walks", []):
            line = walk.get("centreline_local_enu_m") or []
            half = float(walk.get("width_m") or 1.83) / 2.0
            for i in range(len(line) - 1):
                walks.append((tuple(line[i]), tuple(line[i + 1]), half,
                              walk.get("id") or rec.get("id")))

    # The fenced interiors and what the record says the ground inside each one IS.
    # `yards.js` bounds them the same two ways and in the same order: an authored
    # interior ring where the record carries one, otherwise every run that closes.
    fenced = []
    for path in sorted(ENCLOSURES.glob("*.json")):
        if path.name == "index.json":
            continue
        rec = _load(path)
        ground = rec.get("ground") or {}
        treatment = ground.get("treatment")
        if not treatment:
            continue
        authored = ground.get("interior_local_enu_m")
        # One ring is `[[e, n], ...]` and several are `[[[e, n], ...], ...]`, which is
        # what T-0097's fort apron carries: the ground a record covers is not always
        # simply connected, and `yards.js` tells the two apart the same way, by the
        # depth of the first coordinate.
        rings = []
        if isinstance(authored, list) and authored and isinstance(authored[0], list) \
                and authored[0]:
            if isinstance(authored[0][0], list):
                rings = [r for r in authored if isinstance(r, list) and len(r) >= 3]
            elif len(authored) >= 3:
                rings = [authored]
        if rings:
            runs = [[tuple(p) for p in (r.get("path_local_enu_m") or [])]
                    for r in rec.get("runs", [])]
            for r in rings:
                fenced.append({"record": rec["id"], "treatment": treatment,
                               "ring": [tuple(p) for p in r], "runs": runs})
            continue
        for run in rec.get("runs", []):
            pts = [tuple(p) for p in (run.get("path_local_enu_m") or [])]
            if len(pts) >= 4 and math.hypot(pts[0][0] - pts[-1][0],
                                            pts[0][1] - pts[-1][1]) < 0.5:
                fenced.append({"record": rec["id"], "treatment": treatment,
                               "ring": pts[:-1], "runs": [pts]})

    decks = [w["deck_quad_local_enu_m"] for w in _load(WHARVES).get("wharves", [])
             if len(w.get("deck_quad_local_enu_m") or []) >= 3]
    hulls = [tuple(b["position_local_enu_m"]) for b in _load(BOATS).get("boats", [])
             if b.get("state") == "beached" and b.get("position_local_enu_m")]

    hf = Heightfield.load(EPOCH)
    if hf is None:
        raise SystemExit(f"no heightfield at {EPOCH}")
    return {"walls": walls, "streets": streets, "walks": walks, "fenced": fenced,
            "decks": decks, "hulls": hulls, "hf": hf,
            "water_m": float(hf.meta.get("water_surface_m", 0.0))}


def _quads_overlap(a: list, b: list) -> bool:
    """Do two convex quadrilaterals share any ground? Separating axis, exactly.

    Written out rather than approximated by a distance between anchors, because two
    wagons standing seven metres apart nose to nose still have their tongues through
    each other: a wagon is 3 m of body and up to 2.75 m of pole lying on the grass in
    front of it, and the pole is the half of it a centre-to-centre distance cannot see.
    """
    for poly in (a, b):
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            ax, ay = -(y2 - y1), (x2 - x1)
            L = math.hypot(ax, ay)
            if L == 0:
                continue
            ax, ay = ax / L, ay / L
            pa = [p[0] * ax + p[1] * ay for p in a]
            pb = [p[0] * ax + p[1] * ay for p in b]
            if max(pa) < min(pb) - 1e-9 or max(pb) < min(pa) - 1e-9:
                return False
    return True


def _ground_quad(e: float, n: float, bearing: float, back: float,
                 fore: float, margin: float = 0.0) -> list:
    """The ground a wagon covers: its body and whatever is down on the grass.

    `bearing` is the compass bearing the wagon's NOSE points, which is the frame
    `renderers/web/js/yard.js` builds from (forward is (sin b, cos b) in ENU). `back`
    reaches behind the stand and `fore` ahead of it, so a tongue or a pair of shafts
    lying on the ground is inside the rectangle the refusals are tested against — the
    thing a visitor actually trips over.
    """
    b = math.radians(bearing)
    fe, fn = math.sin(b), math.cos(b)
    se, sn = math.cos(b), -math.sin(b)
    half = WAGON_HALF_W_M + margin
    return [(e + fe * a + se * s, n + fn * a + sn * s)
            for a, s in ((-back - margin, -half), (-back - margin, half),
                         (fore + margin, half), (fore + margin, -half))]


def _wagon_ground(wagon: dict, margin: float = 0.0) -> list:
    """The ground an already-recorded wagon covers, read back off the record."""
    back, fore = _kind_reach(wagon.get("kind") or "farm_box")
    at = wagon["at_local_enu_m"]
    return _ground_quad(at[0], at[1], wagon.get("bearing_deg") or 0.0, back, fore, margin)


def _stand_refusal(quad: list, world: dict, taken: list) -> str | None:
    """Why this stand may not have a wagon on it, or None. Ordered most-telling first."""
    pts = list(quad) + [(sum(p[0] for p in quad) / 4.0, sum(p[1] for p in quad) / 4.0)]
    hf = world["hf"]
    lo_e = hf.origin_e + TOWN_EDGE_INSET_M
    hi_e = hf.origin_e + (hf.cols - 1) * hf.cell_m - TOWN_EDGE_INSET_M
    lo_n = hf.origin_n + TOWN_EDGE_INSET_M
    hi_n = hf.origin_n + (hf.rows - 1) * hf.cell_m - TOWN_EDGE_INSET_M
    for p in pts:
        if not (lo_e <= p[0] <= hi_e and lo_n <= p[1] <= hi_n):
            return ("it reaches off the modelled ground, where there is no terrain to "
                    "stand a wheel on.")
        if hf.height(p[0], p[1]) < world["water_m"] + TOWN_DRY_M:
            return (f"the ground under it is under {TOWN_DRY_M:.2f} m over the water "
                    "surface — a wagon standing in the river or in the slough would be "
                    "a claim about the bank, not about the wagon.")
    for sid, poly in world["walls"]:
        if any(_dist_to_polygon(p, poly) < TOWN_WALL_CLEAR_M for p in pts):
            return (f"it stands within {TOWN_WALL_CLEAR_M:.2f} m of {sid}'s committed "
                    "footprint — a wagon drawn through a wall.")
    for a, b, half, wid in world["walks"]:
        if any(_dist_to_path(p, [a, b]) < half + TOWN_WALK_CLEAR_M for p in pts):
            return (f"it stands on the plank walk {wid} (T-0119). A footway is a floor "
                    "and a wagon parked across it is the town's own Ordinance 9 "
                    "complaint, drawn.")
    for interior in world["fenced"]:
        if interior["treatment"] == WORKING_YARD_TREATMENT:
            continue
        if any(_poly_contains(p, interior["ring"]) for p in pts):
            what = {"dooryard_garden": "a kept dooryard garden",
                    "trodden_earth": "an animal pen"}.get(
                        interior["treatment"], interior["treatment"])
            return (f"it stands inside {interior['record']}, which its own record calls "
                    f"{what} (T-0067). A wagon belongs on a working yard's worn earth; "
                    "it does not stand in the cabbages or in the pound.")
    for st in world["streets"]:
        if any(_dist_to_path(p, st["path"]) < st["track_w"] / 2 + TOWN_TRACK_CLEAR_M - 1e-6
               for p in pts):
            return (f"it reaches into the {st['name']} travelled track, which is where "
                    "a visitor walks. Nothing on this layer is drawn in a roadway.")
    for deck in world["decks"]:
        if any(_dist_to_polygon(p, deck) < TOWN_WHARF_CLEAR_M for p in pts):
            return "it stands on a committed wharf deck, which is a floor over water."
    centre = pts[-1]
    for hull in world["hulls"]:
        if math.hypot(centre[0] - hull[0], centre[1] - hull[1]) < TOWN_HULL_CLEAR_M:
            return "it stands on a hull drawn up on the bank."
    # And the wagons already standing, GROUND against ground rather than anchor against
    # anchor: `taken` carries each one's own rectangle, its pole included, already grown
    # by the gap this record keeps between two parked wagons.
    for other in taken:
        if _quads_overlap(quad, other):
            return ("another wagon already stands on that ground — its body, or the pole "
                    f"it has down on the grass, is inside the {TOWN_GAP_M:.2f} m of air "
                    "this record keeps between two parked wagons.")
    return None


def _street_kind(street: dict, ordinal: int) -> str:
    """WHICH VEHICLE, decided by the street's own `traffic` class and the ordinal.

    Arithmetic, not a lottery, and the plates decide the vocabulary rather than the
    place. The RIVER STREET is the one street a picture speaks about: image 11 of the
    owner's brief draws an ox-drawn covered wagon train on it, so every stand on South
    Water is covered and they are all drawn up the same way. A principal street
    alternates covered and farm box; an ordinary street runs farm boxes with a cart at
    every third stand; a lane gets carts, because a cart is what goes down a lane.
    """
    if street["id"] == TOWN_TRAIN_STREET:
        return "covered"
    if street["traffic"] == "principal":
        return "covered" if ordinal % 2 == 0 else "farm_box"
    if street["traffic"] == "ordinary":
        return "cart" if ordinal % 3 == 0 else "farm_box"
    return "cart"


def _lateral_reach(back: float, fore: float, slew_deg: float, square: bool) -> float:
    """How far a slewed wagon reaches SIDEWAYS of its own stand, toward the road.

    T-0836, and it is the whole cost of standing a wagon askew. The stand's offset from
    a centreline was `WAGON_HALF_W_M` (drawn up along the road) or half the body length
    (backed square to it) — both of them the reach of a wagon squared to the road, and
    both of them leaving exactly 0.05 m of slack over `TOWN_TRACK_CLEAR_M`. Slew such a
    wagon by a single degree and a corner 4 m from its stand swings 7 cm into the
    travelled track, which `_stand_refusal` refuses — correctly. So the offset has to
    know the slew: this returns the greatest perpendicular reach of the slewed
    rectangle, corner included, and the stand is set back by it. A wagon standing askew
    takes more of the verge than one standing square, which is what a verge is for.
    """
    th = math.radians(abs(slew_deg))
    if square:
        return WAGON_BODY_L_M / 2 * math.cos(th) + WAGON_HALF_W_M * math.sin(th)
    return WAGON_HALF_W_M * math.cos(th) + max(back, fore) * math.sin(th)


def _kind_reach(kind: str) -> tuple[float, float]:
    """How far a vehicle of this kind reaches behind and ahead of its own stand."""
    if kind == "cart":
        return CART_BODY_L_M / 2, CART_BODY_L_M / 2 + CART_SHAFT_M
    return WAGON_BODY_L_M / 2, WAGON_BODY_L_M / 2 + WAGON_TONGUE_M


def _walk_street(street: dict, pitch: float):
    """Every offered station along a centreline: (point, unit heading, ordinal)."""
    path = street["path"]
    total = sum(math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
                for i in range(len(path) - 1))
    at = pitch / 2.0
    k = 0
    while at < total:
        acc = 0.0
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            seg = math.hypot(b[0] - a[0], b[1] - a[1])
            if seg <= 0:
                continue
            if acc + seg >= at:
                t = (at - acc) / seg
                k += 1
                yield ((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t),
                       ((b[0] - a[0]) / seg, (b[1] - a[1]) / seg), k)
                break
            acc += seg
        at += pitch


def build_town_wagons(cars: dict, placed: list) -> tuple[list, list]:
    """The wagons standing about the town — at the street verges and in the yards.

    T-0064, and the owner's instruction is the whole reason it exists: *"there can be
    more wagons! of course there would be more wagons all over the place in a frontier
    town."* What that instruction does NOT supply is a single coordinate, so this is the
    same shape of derivation the barrels already are — a rule over committed lines, with
    every refusal written down beside what it refused.
    """
    world = _town_world(cars)
    wagons: list = []
    refused: list = []
    # Every wagon already on the record, as the GROUND it covers rather than as a point:
    # the two the evidence reaches and the two in the Green Tree's yard are handed in,
    # and nothing here is stood on ground one of them is already on.
    taken = [_wagon_ground(w, TOWN_GAP_M) for w in placed]
    off_town = 0

    # ---- A. the street verges --------------------------------------------- #
    for street in world["streets"]:
        pitch = (TOWN_TRAIN_PITCH_M if street["id"] == TOWN_TRAIN_STREET
                 else TOWN_PITCH_M.get(street["traffic"], TOWN_PITCH_DEFAULT_M))
        square_ok = street["traffic"] != "principal"
        for point, head, k in _walk_street(street, pitch):
            kind = _street_kind(street, k)
            back, fore = _kind_reach(kind)
            # SQUARE TO THE ROAD at every third stand of a quieter street, nose to the
            # lot line so the pole lies away from the traffic. A principal street's edge
            # is where a wagon stands ALONG it; a lane has the room to back one in.
            square = square_ok and k % 3 == 0
            wid = f"town_wagon_{street['id']}_{k}"
            # T-0836: and then slewed off that square by its own dealt angle, inside the
            # envelope the manoeuvre earns. Applied HERE, before the ground is tested,
            # because a wagon standing askew covers askew ground — slewing the record
            # alone would draw a wagon across a stand this rule had cleared as square.
            slew = _slew(wid, WAGON_SLEW_SQUARE_DEG if square else WAGON_SLEW_ALONG_DEG)
            reasons = []
            stood = False
            # BOTH SIDES ARE TRIED, in a stated order: the side the ordinal names first,
            # then the other. The order alternates down the street, which is what keeps
            # a run of stands from all piling onto one verge — and trying the second
            # side is what puts a train on the river street, whose north verge is the
            # river and refuses every time.
            for side in ((1, -1) if k % 2 else (-1, 1)):
                nrm = (-head[1] * side, head[0] * side)
                lateral = _lateral_reach(back, fore, slew, square)
                off = street["track_w"] / 2 + TOWN_TRACK_CLEAR_M + lateral + 0.05
                e = point[0] + nrm[0] * off
                n = point[1] + nrm[1] * off
                near = min((_dist_to_polygon((e, n), w) for _, w in world["walls"]),
                           default=1e9)
                if near > TOWN_REACH_M:
                    off_town += 1
                    continue
                # THE BEARING IS THE SIDE'S, not the ordinal's: a wagon at a road edge
                # is drawn up facing the way traffic on its own side goes, so every
                # wagon on one verge faces one way and the other verge faces back — a
                # train where the stands run together, and two orientations everywhere
                # else, without a single number being picked.
                if square:
                    bearing = math.degrees(math.atan2(nrm[0], nrm[1])) % 360.0
                else:
                    head_b = math.degrees(math.atan2(head[0], head[1])) % 360.0
                    bearing = head_b if side > 0 else (head_b + 180.0) % 360.0
                bearing = (bearing + slew) % 360.0
                quad = _ground_quad(e, n, bearing, back, fore)
                why = _stand_refusal(quad, world, taken)
                if why:
                    reasons.append(f"on the {'left' if side > 0 else 'right'} verge, {why}")
                    continue
                yoked = kind == "covered"
                wagons.append({
                    "id": wid,
                    "kind": kind,
                    "stands_on": street["id"],
                    "belongs_to": None,
                    "tilt": kind == "covered",
                    "yoke": yoked,
                    "confidence": "reconstructed",
                    "at_local_enu_m": [_round(e), _round(n)],
                    "bearing_deg": _round(bearing, 1),
                    "drawn_up": "square to the road" if square else "along the road",
                    "slew_deg": slew,
                    # T-0688. The envelope this slew was dealt inside, and the number of
                    # steps it was dealt over, carried ON the record. The smoke's variety
                    # clause used to count distinct STREET bearings, which no wagon rule
                    # controls; it now asks the deal about itself, and it asks these two
                    # numbers rather than repeating 6/12/15/9 in a second file that can
                    # drift from this one.
                    "slew_envelope_deg": WAGON_SLEW_SQUARE_DEG if square else WAGON_SLEW_ALONG_DEG,
                    "slew_steps": WAGON_SLEW_STEPS,
                    "clear_of_track_m": _round(off - lateral - street["track_w"] / 2),
                    "note": (
                        f"A {KIND_WORDS[kind]} standing at the verge of "
                        f"{street['name']}, and it is HERE because the rule put it here. "
                        "The owner asked for the town's wagons, 2026-08-18: 'there can be "
                        "more wagons! of course there would be more wagons all over the "
                        "place in a frontier town.' He gave no place, so the place is "
                        f"derived: a stand is offered every {pitch:.0f} m along this "
                        f"street's committed centreline (its traffic class is "
                        f"'{street['traffic']}'), at the verge "
                        f"{_round(off - lateral - street['track_w'] / 2):.2f} m clear of "
                        "the travelled track, drawn up "
                        f"{'square to the road' if square else 'along the road'} and "
                        "facing the way traffic on this side of it goes — and then "
                        f"slewed {abs(slew):.1f} degrees "
                        f"{'off that square' if abs(slew) > 1e-9 else 'not at all'}"
                        f"{'' if abs(slew) < 1e-9 else (' to the left' if slew < 0 else ' to the right')}"
                        ", because nobody squared an unhitched wagon to a verge that was "
                        "mud and grass: the angle is dealt from this wagon's own id "
                        f"inside an envelope of {WAGON_SLEW_SQUARE_DEG if square else WAGON_SLEW_ALONG_DEG:.0f} "
                        "degrees, which is a claim about how the town looked and is "
                        "written down at docs/LIBERTIES.md L230. THE TEAM IS NOT "
                        "DRAWN and never will be: this project models no animal in the "
                        "scene, so the wagon stands unhitched with its "
                        f"{'shafts' if kind == 'cart' else 'tongue'} down on the ground"
                        f"{' and its ox-yoke laid by on the grass' if yoked else ''}. "
                        "Everything about it is invented — that it stood here at noon on "
                        "1 July 1835, whose it was, and what it was carrying, which is "
                        "why it carries no mark of any kind: docs/LIBERTIES.md L162."
                    ),
                })
                taken.append(_ground_quad(e, n, bearing, back, fore, TOWN_GAP_M))
                stood = True
                break
            if not stood and reasons:
                refused.append({"stand": f"{street['id']} {k}", "street": street["name"],
                                "why": " · ".join(reasons)})

    # ---- B. the working yards ---------------------------------------------- #
    # Clause: a wagon behind a fence stands on WORKING ground. `data/enclosures/` states
    # what the ground inside each of its fences is (T-0067) and `yards.js` draws it; the
    # yards whose treatment is worn earth are the ones a wagon was driven into, and this
    # fills them round whatever already stands there.
    for interior in world["fenced"]:
        if interior["treatment"] != WORKING_YARD_TREATMENT:
            continue
        ring = interior["ring"]
        e_lo, e_hi = min(p[0] for p in ring), max(p[0] for p in ring)
        n_lo, n_hi = min(p[1] for p in ring), max(p[1] for p in ring)
        bearing = 0.0 if (n_hi - n_lo) >= (e_hi - e_lo) else 90.0
        here = [q for q in taken
                if any(_poly_contains(p, ring) for p in q)]
        room = YARD_WAGON_MAX - len(here)
        if room <= 0:
            refused.append({"stand": interior["record"], "why": (
                f"the yard already carries {len(here)} wagon(s), which is the "
                f"{YARD_WAGON_MAX} a yard this size is given — no more are stood in it "
                "rather than a yard packed to look busy.")})
            continue
        # The stands are SEARCHED on a lattice and taken openest-first, the same way the
        # attested wagon's own stand is: the point whose least clearance to every fence
        # line and every committed wall is greatest, then the next one that is still a
        # parked wagon's width of ground away from everything already standing.
        lattice = []
        rows = int((n_hi - n_lo) / YARD_LATTICE_M)
        cols = int((e_hi - e_lo) / YARD_LATTICE_M)
        for i in range(rows + 1):
            n = _round(n_lo + i * YARD_LATTICE_M, 3)
            for j in range(cols + 1):
                e = _round(e_lo + j * YARD_LATTICE_M, 3)
                if not _poly_contains((e, n), ring):
                    continue
                clear = min([_dist_to_polygon((e, n), w) for _, w in world["walls"]]
                            + [_dist_to_path((e, n), r) for r in interior["runs"]
                               if len(r) >= 2])
                if clear < WAGON_CLEAR_M:
                    continue
                lattice.append((clear, e, n))
        lattice.sort(key=lambda c: (-c[0], c[2], c[1]))
        stood = 0
        passed_over = 0
        last_why = None
        for clear, e, n in lattice:
            if stood >= room:
                break
            kind = "covered" if stood % 2 == 0 else "farm_box"
            back, fore = _kind_reach(kind)
            wid = f"town_wagon_{interior['record']}_{stood + 1}"
            # T-0836, and the yard is where the envelope is widest: a yard has no road
            # to line a wagon up on, so the axis below is the rule's own convenience
            # rather than anything a driver was working to.
            slew = _slew(wid, WAGON_SLEW_YARD_DEG)
            face = ((bearing + 180.0) % 360.0 if stood % 2 else bearing) + slew
            face %= 360.0
            quad = _ground_quad(e, n, face, back, fore)
            # A lattice slot whose ground is already under a wagon is passed over in
            # silence — the search is walking a 0.5 m grid and half of it is under the
            # wagon it just stood. Every OTHER reason is counted and the last one is
            # quoted, so the yard's own entry says what the ground refused rather than
            # burying the record under four hundred near-identical lines.
            if any(_quads_overlap(quad, other) for other in taken):
                continue
            why = _stand_refusal(quad, world, taken)
            if why:
                passed_over += 1
                last_why = why
                continue
            wagons.append({
                "id": wid,
                "kind": kind,
                "in_enclosure": interior["record"],
                "belongs_to": None,
                "tilt": kind == "covered",
                "yoke": True,
                "confidence": "reconstructed",
                "at_local_enu_m": [_round(e), _round(n)],
                "bearing_deg": _round(face, 1),
                "drawn_up": "along the yard's long axis",
                "slew_deg": slew,
                # T-0688, as above: the deal's own envelope and step count, on the record.
                "slew_envelope_deg": WAGON_SLEW_YARD_DEG,
                "slew_steps": WAGON_SLEW_STEPS,
                "clearance_m": _round(clear),
                "note": (
                    f"A {KIND_WORDS[kind]} standing in {interior['record']}, whose "
                    "own record calls the ground inside it worn earth — a WORKING yard "
                    "(T-0067), which is the only fenced ground on this layer a wagon is "
                    "allowed on. The stand is searched, not chosen: a "
                    f"{YARD_LATTICE_M:.2f} m lattice over the yard's own interior ring, "
                    "openest first, keeping only points whose least clearance to every "
                    "committed wall and every fence line of this yard is at least "
                    f"{WAGON_CLEAR_M:.2f} m — {_round(clear):.2f} m here — and whose "
                    "ground, pole included, is clear of every wagon already standing. The "
                    "bearing is the yard's own long axis, turned end for end at every "
                    "second wagon the way a yard full of them stands, and then slewed "
                    f"{abs(slew):.1f} degrees off it — dealt from this wagon's own id "
                    f"inside an envelope of {WAGON_SLEW_YARD_DEG:.0f} degrees, the "
                    "widest on this layer because a yard has no road to line a wagon up "
                    "on (docs/LIBERTIES.md L230). THE TEAM IS NOT "
                    "DRAWN: the wagon is unhitched, tongue down and yoke laid by on the "
                    "ground. Invented entirely — docs/LIBERTIES.md L162."
                ),
            })
            taken.append(_ground_quad(e, n, face, back, fore, TOWN_GAP_M))
            stood += 1
        if passed_over:
            refused.append({"stand": interior["record"], "why": (
                f"{passed_over} lattice slot(s) inside this yard were open ground and "
                "were still refused, the last of them because " + last_why)})
    refused.append({"stand": "*", "why": (
        f"{off_town} offered stand(s) fell more than {TOWN_REACH_M:.0f} m from every "
        "committed footprint in the town and are not enumerated one by one. Past that "
        "the street is running out into the prairie: a wagon parked in the grass two "
        "blocks beyond the last house would be this record inventing a reason for it to "
        "be there, and the reason is the whole of what an invented object has to have.")})
    return wagons, refused


# --------------------------------------------------------------------------- #
# the record                                                                   #
# --------------------------------------------------------------------------- #

def record(frontages: list, refused: list, wagons: list, wagons_refused: list,
           benches: list, sheds: list) -> dict:
    items = sum(len(f["items"]) for f in frontages)
    return {
        "_doc": (
            "Goods standing on the town's own ground — barrels and cases on the "
            "footway at the taverns and the stores, the bench against the Green Tree's "
            "front wall, the open-sided wagon shed at its yard end, and THE TOWN'S "
            "WAGONS: the one the source calls a wagon yard carries, the ones a picture "
            "puts in the Green Tree's, and the farm wagons, covered emigrant wagons and "
            "two-wheeled carts standing at the street verges and in the working yards "
            "all over a frontier town (T-0064). NOT structure records and NOT geometry that comes out "
            "of Blender: a barrel on a footway is a small object standing on ground this "
            "project has already drawn, so it is derived from the committed footprints "
            "and placements and drawn at load by renderers/web/js/yard.js — the same "
            "argument that lets the enclosure layer draw a fence from a perimeter and "
            "the signage layer hang a board off a wall. Generated by "
            "tools/generate_yard_goods.py and re-derived byte for byte by "
            "tools/check.sh, because 'which frontage gets goods' is a rule and a rule "
            "has to be auditable."
        ),
        "id": "town_trade_goods",
        "name": "Goods at the town's trading frontages",
        "kind": "yard_goods",
        "scene": "1835",
        "target_date": "1835-07-01",
        "coordinates": (
            "Local East-North-Up metres from data/datum.json's origin, the same frame "
            "data/enclosures/ and data/signage/ and the sidecars' placement.local_e / "
            "local_n use."
        ),
        "counts": {
            "frontages": len(frontages),
            "objects": items,
            "wagons": len(wagons),
            "wagons_by_kind": {
                kind: sum(1 for w in wagons if (w.get("kind") or "farm_box") == kind)
                for kind in ("farm_box", "covered", "cart")
            },
            "wagons_at_street_verges": sum(1 for w in wagons if w.get("stands_on")),
            "wagons_in_yards": sum(1 for w in wagons if w.get("in_enclosure")),
            "wagon_stands_refused": len(wagons_refused),
            "benches": len(benches),
            "sheds": len(sheds),
            "marked_objects": sum(
                1 for f in frontages for it in f["items"] if it.get("mark")),
            "distinct_marks": len({
                " / ".join(it["mark"]["lines"])
                for f in frontages for it in f["items"] if it.get("mark")}),
        },
        "existence": {
            "value": True,
            "confidence": "reconstructed",
            "sources": ["chicago_democrat_1833_11_26", "chicagology_prefire278"],
            "note": (
                "UNLIKE THE SIGNBOARDS ONE LAYER OVER, THIS ONE DOES NOT START FROM "
                "SILENCE — THE TOWN LEGISLATED ABOUT IT. The village ordinances of "
                "7 November 1833 are carried complete in the first issue of the Chicago "
                "Democrat (data/sources/chicago_democrat_1833_11_26.json, tier 1, "
                "verified from the scan), and ORDINANCE 9 IS ABOUT TIMBER, STONE, BRICK, "
                "BOXES AND BARRELS STACKED IN THE STREETS. A corporation does not "
                "legislate against a thing nobody does: that is a contemporary statement, "
                "by the people who had to walk round them, that Chicago's streets had "
                "boxes and barrels standing in them. WHAT IT DOES NOT GIVE IS A "
                "LOCATION — it says the town, not the corner, and it is twenty months "
                "before the scene date. So the FACT of goods on a public frontage is "
                "well founded and WHICH frontage is a rule, and the rule is what this "
                "record is generated from. The wagon rests on a second source and one "
                "sentence of it: chicagology_prefire278's 'the yard into which the trains "
                "were driven'. NOTHING HERE IS PROMOTED ABOVE reconstructed on the "
                "strength of either: no source states that any of these particular "
                "buildings had anything outside its door on 1 July 1835."
            ),
        },
        "ordinance": {
            "source_id": "chicago_democrat_1833_11_26",
            "value": "Ordinance 9: timber, stone, brick, boxes and barrels stacked in the streets",
            "confidence": "attested",
            "note": (
                "Quoted here as the source record's own summary of the item, not as a "
                "transcription of the ordinance's text — the page image is the source and "
                "this project's holding of it is a summary line in "
                "data/sources/chicago_democrat_1833_11_26.json § what_it_supplies. WHAT "
                "THIS LAYER DELIBERATELY DOES NOT DO WITH IT: the ordinance is about "
                "goods IN THE STREETS, which is the stronger reading, and nothing here is "
                "drawn in a roadway. Every object stands within 0.55 m of the wall it "
                "belongs to, on the footway strip — the restrained reading, chosen "
                "because a barrel standing in the travelled way would be a claim about "
                "the width of the road as well as about the goods, and because the "
                "roadway is where a visitor walks. TIMBER, STONE AND BRICK ARE NOT DRAWN "
                "EITHER: they are building material on a lot under construction rather "
                "than a merchant's stock on his own frontage, they belong to whichever "
                "building was going up that week, and this record has no way to say "
                "which. That half of Ordinance 9 is filed as its own ticket."
            ),
        },
        "form": {
            "barrel_height_m": {
                "value": BARREL_H_M,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. 0.84 m is 33 in, the height of a provision barrel of the "
                    "period standing on its head. No source in this repository gives the "
                    "size of any cask in Chicago. What bounds it is the trade the "
                    "research already holds: docs/research/08-fauna.md records Hubbard "
                    "packing 5,000 hogs in 1834 that had to be 'stowed away in bulk' for "
                    "want of barrels until they came from Cleveland at a dollar apiece, "
                    "so the barrel here is the provision barrel that trade turned on."
                ),
            },
            "barrel_belly_diameter_m": {
                "value": BARREL_BELLY_D_M,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. 0.53 m is 21 in at the bilge. Nothing attests it. It is "
                    "the proportion a coopered cask has to have — the staves bow or they "
                    "cannot be drawn up tight — and it is what makes the object read as "
                    "a barrel rather than as a drum."
                ),
            },
            "barrel_head_diameter_m": {
                "value": BARREL_HEAD_D_M,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. 0.45 m is 17.5 in at the head, about six sevenths of the "
                    "bilge. Nothing attests it. NO HOOPS ARE DRAWN AS SEPARATE "
                    "GEOMETRY — a hoop is 20 mm of iron and at any distance a visitor "
                    "stands it is a line, not a solid, so drawing one would spend "
                    "triangles on something the eye cannot resolve."
                ),
            },
            "crate_size_m": {
                "value": [CRATE_L_M, CRATE_W_M, CRATE_H_M],
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. A case 1.05 x 0.72 x 0.62 m — a two-man lift. Nothing "
                    "attests a case, its size or its boards. Ordinance 9 names 'boxes' "
                    "and this is what this record draws one as. The second case stacked "
                    "on it is 0.72 of its size, which is nothing but the difference that "
                    "makes a stack read as two objects."
                ),
            },
            "wagon_body_m": {
                "value": [WAGON_BODY_L_M, WAGON_BODY_W_M, WAGON_BODY_H_M],
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. A body 10 ft by 3 ft 6 in and 22 in deep, recorded "
                    "converted, on wheels 4 ft 6 in behind and 3 ft 6 in in front — a "
                    "farm wagon, which is what 'the trains driven into the yard' were. "
                    "Not one of those numbers is attested for Chicago or for this yard. "
                    "The spoke count, the rim and the hub are the renderer's and are "
                    "claimed in the same liberty."
                ),
            },
            "cart_m": {
                "value": [CART_BODY_L_M, CART_BODY_W_M, CART_BODY_H_M,
                          CART_WHEEL_D_M, CART_BED_Y_M, CART_SHAFT_M],
                "confidence": "reconstructed",
                "note": (
                    "INVENTED — T-0064's third vehicle, and the cheapest thing on wheels "
                    "in this town. A two-wheeled cart: a body 6 ft 6 in by 3 ft 6 in and "
                    "20 in deep, on a single pair of 4 ft 8 in wheels, with 8 ft shafts "
                    "instead of a tongue. Not one of those numbers is attested for "
                    "Chicago. What bounds them is the vehicle: a cart's wheels have to "
                    "be taller than a wagon's because they carry the load alone, and its "
                    "body has to sit on the axle because there is no second one to "
                    "balance against. Why a cart at all: 'more wagons all over the place' "
                    "is not one vehicle repeated sixty times, and a cart is what went "
                    "down a lane. THE SHAFTS ARE DOWN ON THE GROUND — there is no animal "
                    "in them and there never will be."
                ),
            },
            "ox_yoke_m": {
                "value": [YOKE_BEAM_M, YOKE_BEAM_SQ_M, YOKE_BOW_M, YOKE_BOW_SQ_M],
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. A yoke beam 4 ft 8 in between the bows, 4.7 in square, "
                    "with the two bows showing 13 in past it, lying on the grass beside "
                    "a wagon that came in off the road. Nothing attests a yoke in "
                    "Chicago. IT IS HERE BECAUSE THE ANIMALS ARE NOT: this project draws "
                    "no fauna in the scene at all, so a wagon cannot be shown hitched, "
                    "and a covered wagon standing with its tongue on the ground and "
                    "nothing else to say for itself reads as abandoned rather than "
                    "outspanned. The yoke laid by is the honest half of a team — the "
                    "same argument the Green Tree's empty bench makes about the sitters "
                    "in its plate."
                ),
            },
            "bench_size_m": {
                "value": [BENCH_L_M, BENCH_SEAT_D_M, BENCH_SEAT_H_M],
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. A backless plank bench 6 ft long, 14 in deep and 18 in to "
                    "the seat, on two plank ends, recorded converted. The Trowbridge view "
                    "of the Green Tree shows a bench against the front wall and shows how "
                    "long it is only against the people sitting on it, who are reference "
                    "and are not drawn — so the length is read off the wall it stands "
                    "against rather than off them, and the section is a joiner's plank of "
                    "the period and nothing more. Nothing attests any of it."
                ),
            },
            "bench_plank_m": {
                "value": BENCH_PLANK_T_M,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED — 45 mm of sawn plank for the seat and its two ends. HOW a "
                    "bench is drawn rather than a claim about this one, kept on the record "
                    "with its other sizes so the renderer reaches for no number of its own."
                ),
            },
            "wagon_tilt_m": {
                "value": [WAGON_TILT_RISE_M, WAGON_TILT_OVERHANG_M],
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. The covered wagon's canvas rises 1.10 m over the body's "
                    "top rail — about 3 ft 7 in, which is the height a person has to "
                    "have to sit under a tilt — and is pulled 0.12 m past the end bows. "
                    "Nothing attests a covered wagon at this inn or anywhere in this "
                    "town; the Trowbridge drawing of the Green Tree shows one standing "
                    "under its wagon shed and the ordinary width of the same farm wagon "
                    "body is what the arch springs from. THE BOWS ARE NOT DRAWN AS "
                    "SEPARATE GEOMETRY, the barrels' hoops' argument exactly: under the "
                    "canvas there is nothing to see. The tilt is open at both ends, "
                    "which is what the plate shows and is also the honest half — a "
                    "gathered canvas end is a shape nothing here can state."
                ),
            },
            "shed_bay_m": {
                "value": [WAGON_BODY_L_M + 2 * GT_SHED_END_M, 2 * WAGON_CLEAR_M],
                "confidence": "reconstructed",
                "note": (
                    "INVENTED, but it is arithmetic on numbers this record already "
                    "carries rather than a pair of figures picked to look right: the "
                    "bay is the wagon's own 3.05 m body with 0.50 m of air at each end, "
                    "by the 3.20 m of ground WAGON_CLEAR_M gives a parked wagon. "
                    "Nothing measures this shed, and no source states that the Green "
                    "Tree had one — the Trowbridge drawing shows it. Its stand is "
                    "derived from the committed footprint and is argued on the shed's "
                    "own record."
                ),
            },
            "shed_timber_m": {
                "value": [GT_SHED_POST_M, GT_SHED_PLATE_M],
                "confidence": "reconstructed",
                "note": (
                    "INVENTED — 0.14 m posts under the open side and 0.16 m plates and "
                    "rafters over them, which is a 5.5 in stick and a 6 in one. HOW the "
                    "shed is drawn rather than a claim about this one, kept on the "
                    "record with its other sizes so the renderer reaches for no number "
                    "of its own, the same division bench_plank_m makes."
                ),
            },
            "shed_pitch_deg": {
                "value": GT_SHED_PITCH_DEG,
                "confidence": "reconstructed",
                "note": (
                    "INVENTED. A lean-to falling 12 degrees away from the wall it is "
                    "spiked to — 0.68 m over the bay's 3.20 m. Nothing states the "
                    "shed's roof, its pitch or its covering. What bounds it is the "
                    "shape: the roof has to shed water away from the house and has to "
                    "clear the tilt at its low edge, and 12 degrees is the shallowest "
                    "fall that does both over this depth. The roof is drawn as boards "
                    "in the layer's own timber, not as shingles: nothing says which, "
                    "and boards are what an open shed in this town was likeliest to "
                    "carry."
                ),
            },
            "marks": {
                "value": None,
                "confidence": "reconstructed",
                "geometry": "absent",
                "note": (
                    "NOT DRAWN, AND IT IS THE SAME DISCIPLINE THE SIGNBOARDS KEEP. No "
                    "barrel carries a brand, a merchant's name, a stencil or a mark of "
                    "any kind, and no case is labelled. Nothing this project holds says "
                    "what was in any barrel in Chicago on this date, still less whose it "
                    "was, and painted names on two hundred casks would be the most "
                    "conspicuous fiction in the scene — the point docs/LIBERTIES.md L25 "
                    "settled for the one documented sign and L130 generalised."
                ),
            },
        },
        "mark_rule": {
            "note": (
                "T-0065. Every barrel and every case on this record carries a MARK, and "
                "the mark is dealt by a rule rather than typed. The owner asked for it "
                "on 2026-08-18 — \u201cyou can add period correct names and brands and "
                "labels to things\u201d — and the tier is his standing ruling of the same "
                "day: reconstructed, labelled as such, and bounded. What a mark may say "
                "is the whole of the invention's fence: the HOUSE'S OWN NAME, which is "
                "already in this dataset and already painted on the board over the door; "
                "a COMMODITY WORD out of the trade's own attested description (Peck "
                "advertising dry goods, hardware and groceries; Jones's grocery and "
                "provision store), so the category is the source's and only the word on "
                "the individual cask is invented; and, on a case in transit, its "
                "destination and the one port this project can name in writing. Nothing "
                "else — no trademark, no maker this town is not recorded as dealing "
                "with, no price, no date, no slogan. Read the clauses in "
                "tools/generate_yard_goods.py and the bounds in docs/LIBERTIES.md L166. "
                "THE ONE CLASS THAT COULD NOT MEET THE SECOND CLAUSE NOW DOES: the "
                "trading house's FLOUR, SALT, POWDER, TOBACCO and HARDWARE were chosen "
                "on period plausibility because Beaubien's trading house has no "
                "attested description of its stock, and T-0596 found all five in the "
                "American Fur Company's own catalogue of goods furnished for the trade "
                "of the Chicago country (bk_afc_018). No word was added, moved or "
                "relettered on the strength of it — that catalogue is c.1828 and names "
                "a district rather than a shop, so docs/LIBERTIES.md L221 admits it as "
                "corroboration for a word already standing and refuses it as a warrant "
                "for a new one. Nothing in this town letters, models or pictures the "
                "Indian trade or the people it was with."
            ),
            "confidence": "reconstructed",
            "stocks": {k: list(v) for k, v in sorted(MARK_STOCKS.items())},
            "case_words": dict(sorted(MARK_CASE_WORD.items())),
            "port": MARK_PORT,
            "brand_every": MARK_BRAND_EVERY,
            "deal_note": (
                "Which word lands on which cask is a sha1 of the structure id offset "
                "into the trade class's stock list, then the cask's own place in the "
                "row — the same deal tools/generate_business_signboards.py uses to "
                "choose a colourway, and for the same reason: two neighbouring "
                "frontages must not both open with FLOUR, and the answer must be the "
                "same on every run. Every third cask carries the house's brand instead "
                "of a commodity, burned into the head the way a cooper's or a "
                "merchant's mark was."
            ),
            "letterforms_note": (
                "Three, and they are the signboards' faces one layer down (T-0066): a "
                "STENCIL for a commodity word, cut with the bridges a stencil plate "
                "leaves; a BRAND for the house's own mark on a barrel head; and a "
                "SHIPPING mark, brush-written, on the face of a packing case. The "
                "letterform is invented exactly as the boards' is (L159) and is drawn "
                "by renderers/web/js/yard.js on one canvas atlas, so a mark costs no "
                "triangles and the layer keeps its one material."
            ),
        },
        "rule": {
            "note": (
                "A named record (not inf_/recon_, not 'Reconstructed'), a GOODS-KEEPING "
                "trade whose stock arrived in boxes and barrels, that trade attested or "
                "inferred rather than reconstructed, standing on the scene date, on the "
                "TOWN's ground rather than inside the fort's palisade, and a strip in "
                "front of the facade clear of every other committed footprint. How many "
                "objects is arithmetic on the frontage — one barrel per 2.2 m of usable "
                "wall to a cap of four, a case past them at 4 m, a second case stacked "
                "at 7 m, and a public house's empty laid on its side at 5 m — never a "
                "lottery. Read the clauses and their reasons in "
                "tools/generate_yard_goods.py."
            ),
            "goods_trades": sorted(GOODS_TRADES),
            "excluded_trades_note": (
                "Smithies, cooperages, tanneries, brickyards, packing and slaughter "
                "houses, manufactories, stables, warehouses without a counter, the "
                "churches, the schools, the court-house, the jail, the agency house and "
                "every dwelling are outside the trade list. Several of them plainly kept "
                "stuff outside — a cooperage most of all — but what they kept was tools "
                "and material rather than a merchant's stock on a public frontage, and "
                "the rule would be guessing. The fort's provision store and sutler's "
                "store are refused separately and in writing: federal ground, no "
                "corporation street in front of the door."
            ),
            "placement_note": (
                "The goods stand at the end of the frontage the SIGNBOARD does not "
                "occupy. tools/generate_business_signboards.py hangs its board 1.7 m "
                "toward +u of the facade's centre, so this piles from the -u end and the "
                "door between them stays clear — two layers derived from the same wall "
                "that would otherwise be derived into each other. The Green Tree is the "
                "one frontage here with no wall board to keep clear of (T-0082 moved its "
                "board to a post at the street corner), and the goods pile from the same "
                "end anyway: the barrels were derived before the board moved and moving "
                "them now would be a change nothing asked for."
            ),
        },
        "town_wagon_rule": {
            "confidence": "reconstructed",
            "ticket": "T-0064",
            "instruction": (
                "The owner, 2026-08-18, verbatim: 'there can be more wagons! of course "
                "there would be more wagons all over the place in a frontier town.' And "
                "the standing ruling that grades them, from the same day: 'you are "
                "totally fine to be liberal with adding reconstructed items when i ask "
                "for things, you can just label and mark them as such.'"
            ),
            "offered_note": (
                "A stand is OFFERED every "
                f"{TOWN_PITCH_M['principal']:.0f} m along a principal street's committed "
                f"centreline, every {TOWN_PITCH_M['ordinary']:.0f} m along an ordinary "
                f"one and every {TOWN_PITCH_M['light']:.0f} m down a lane — the street "
                "record's own `traffic` class, which is the only thing in this dataset "
                "that ranks one street above another. The RIVER STREET is offered a "
                f"stand every {TOWN_TRAIN_PITCH_M:.0f} m instead, because image 11 of "
                "the owner's brief draws a covered wagon TRAIN on it rather than one "
                "wagon standing by itself. The stand sits at the verge, "
                f"{TOWN_TRACK_CLEAR_M:.2f} m clear of the travelled track's own edge, on "
                "whichever side of the road the ground will take it — the side the "
                "ordinal names is tried first and the other second, which is what puts "
                "the river street's train on its landward verge without a coordinate "
                "being written for it. A wagon faces the way traffic on ITS side goes, "
                "so one verge faces up the street and the other faces back down it; at "
                "every third stand of a quieter street it is backed square to the road "
                "instead, nose to the lot line. Nothing here is a chosen number: change "
                "the committed centreline and every wagon on it moves."
            ),
            "slew_note": (
                "AND THEN IT IS TURNED OFF THAT BEARING — T-0836, docs/LIBERTIES.md "
                "L230. Everything above squares a wagon to the thing it serves, which is "
                "where a rule PUTS a wagon and is not how one that has been left "
                "standing sits: there was no kerb to square to, the verge was mud and "
                "grass, and a driver who backed a loaded box to a door and dropped the "
                "tongue left it where it stopped. So each wagon carries a `slew_deg` of "
                "its own, dealt from its id by the same sha1 rank that deals every other "
                "invented attribute here and walked across its envelope in "
                f"{WAGON_SLEW_STEPS} steps — so the middle step is dead square and some "
                "of them still are. The envelope is graded by the manoeuvre: up to "
                f"{WAGON_SLEW_ALONG_DEG:.0f} degrees drawn up along a road, which lines "
                f"the wagon up itself; up to {WAGON_SLEW_SQUARE_DEG:.0f} backed square "
                "to one, which a driver judges over his shoulder; up to "
                f"{WAGON_SLEW_YARD_DEG:.0f} in a yard, which offers no line to work to "
                "at all. THE CLEARANCES ARE NOT WEAKENED FOR IT: the stand is set back "
                "by the greatest perpendicular reach of the SLEWED rectangle, corner "
                "included, so an askew wagon takes more of the verge and still stands "
                "the full clearance clear of every track, wall and footway below."
            ),
            "refusal_note": (
                "A stand is REFUSED, in writing and with its reason, if it would put a "
                f"wagon within {TOWN_WALL_CLEAR_M:.2f} m of a committed footprint; on a "
                "plank walk or a board crossing (data/frontage/, the same rectangles "
                "frontage.js hands the planters as keepOut — a footway is a floor); "
                "inside a fence whose own record calls the ground a dooryard garden or "
                "an animal pen (data/enclosures/ ground.treatment, T-0067 — a wagon "
                "belongs on a working yard's worn earth and nowhere else behind a "
                f"fence); within {TOWN_TRACK_CLEAR_M:.2f} m of ANY street's travelled "
                "track including its own, which is what refuses nearly every stand "
                "offered at a crossing; on a committed wharf deck or a hull drawn up on "
                f"the bank; on ground under {TOWN_DRY_M:.2f} m over the water surface or "
                f"off the modelled field; or where its own ground — the "
                f"body and the pole down on the grass — comes within {TOWN_GAP_M:.2f} m "
                "of a wagon already standing. The refusals are on this record under "
                "`wagons_refused`, one entry per stand, with both sides' reasons where "
                "both sides were tried and both failed."
            ),
            "reach_m": TOWN_REACH_M,
            "reach_note": (
                f"And a stand more than {TOWN_REACH_M:.0f} m from every committed "
                "footprint is not offered at all. Past that the street is running out "
                "into the prairie, and a wagon parked in the grass two blocks beyond the "
                "last house would be this record inventing a reason for it — the reason "
                "being the whole of what an invented object has to have. Those are "
                "counted rather than enumerated; the count is the last entry of "
                "`wagons_refused`."
            ),
            "kinds_note": (
                "WHICH VEHICLE is the street's own traffic class again, and the plates "
                "supply the vocabulary rather than the place: the river street is all "
                "covered wagons (image 11), a principal street alternates covered and "
                "farm box, an ordinary street runs farm boxes with a two-wheeled cart at "
                "every third stand, and a lane gets carts. NO DRAFT ANIMAL IS DRAWN "
                "ANYWHERE. This project models no fauna in the scene — "
                "renderers/web/js/fauna.js is a card and not a herd — so every wagon on "
                "this record stands UNHITCHED, tongue or shafts down on the ground, and "
                "the covered wagons and the yard wagons have their ox-yokes laid by on "
                "the grass. No human figure is drawn either, here or anywhere in this "
                "project."
            ),
            "yards_note": (
                "Behind a fence the rule is different and stricter: the only fenced "
                f"ground a wagon may stand on is a yard whose own record calls it "
                f"'{WORKING_YARD_TREATMENT}' (T-0067), and the stands in it are searched "
                f"on a {YARD_LATTICE_M:.2f} m lattice openest-first — the point whose "
                "least clearance to every committed wall and every fence line of that "
                "yard is greatest — to a ceiling of "
                f"{YARD_WAGON_MAX} wagons including whatever already stands there."
            ),
        },
        "frontages": frontages,
        "wagons": wagons,
        "benches": benches,
        "sheds": sheds,
        "refused": refused,
        "wagons_refused": wagons_refused,
        "research_note": (
            "WHAT WOULD MOVE ANY OF THIS OFF RECONSTRUCTION: the missing fourth page of "
            "the Democrat's first issue, which would carry more of the ordinances and may "
            "carry Ordinance 9's own text and its penalty; any later Chicago corporation "
            "order about obstructions, which would say what was being obstructed with; an "
            "insurance or tax description of a South Water Street lot; a traveller's "
            "account of walking the street; or the pre-fire photographs of surviving "
            "1830s frontages actually opened at their holding institutions. WHAT THIS "
            "RECORD IS STILL SHORT OF, stated rather than left to be noticed: Ordinance "
            "9's timber, stone and brick are not drawn at all; and nothing stands in a "
            "roadway though the ordinance is about roadways. WHAT IS NO LONGER SHORT, "
            "and it is worth being exact about what changed: this note used to end 'the "
            "wagons in this town still stand at two addresses out of hundreds', and "
            "T-0064 answered it on the owner's instruction rather than on a source. The "
            "town's wagons are spread now, and NOT ONE OF THEM IS BETTER EVIDENCED THAN "
            "IT WAS — the two the evidence reaches are still the wagon-yard's and the "
            "Green Tree's, everything else is `reconstructed` on a rule, and the rule is "
            "on this record under `town_wagon_rule` so it can be argued with. WHAT WOULD "
            "MOVE THE REST: a teamster's or a forwarding house's day-book naming what "
            "stood in the street; a Chicago corporation order about vehicles left "
            "standing, which would put a number on the thing Ordinance 9 only implies; "
            "or any dated view of a Chicago street before 1840. THE SHED IS THE FIRST ROOF THIS "
            "LAYER HAS EVER DRAWN, and it is worth saying what that does not mean: it "
            "is not a structure record, it has no archetype and it is not baked, "
            "because it is derived from a committed footprint the way a fence and a "
            "signboard are. If a second yard building is ever wanted the question to "
            "ask first is whether it belongs here or in data/structures/."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and diff, write nothing")
    args = ap.parse_args()
    ids, cars = _standing()
    frontages, refused = build_frontages(ids, cars)
    wagons, wagons_refused = build_wagons(cars)
    gt_wagons, benches, sheds, gt_refused = build_green_tree_yard(cars)
    wagons = wagons + gt_wagons
    wagons_refused = wagons_refused + gt_refused
    # T-0064's town wagons come LAST, and they are handed every stand already taken so
    # nothing new is stood where something already is. The order is also the record's
    # order, which keeps the two evidence-backed wagons at the head of the list where a
    # reader meets them first.
    town_wagons, town_refused = build_town_wagons(cars, wagons)
    wagons = wagons + town_wagons
    wagons_refused = wagons_refused + town_refused
    text = json.dumps(record(frontages, refused, wagons, wagons_refused, benches, sheds),
                      indent=2, ensure_ascii=False) + "\n"
    objects = sum(len(f["items"]) for f in frontages)
    if args.check:
        if not OUT.exists():
            print(f"YARD GOODS DRIFT\n  - {OUT.relative_to(ROOT)} is missing")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"YARD GOODS DRIFT\n  - {OUT.relative_to(ROOT)} has drifted from the "
                  f"rule in tools/generate_yard_goods.py")
            return 1
        print(f"verified {objects} object(s) on {len(frontages)} trading frontage(s), "
              f"{len(wagons)} wagon(s) ({len(town_wagons)} of them the town's), "
              f"{len(benches)} bench(es) and {len(sheds)} shed(s) "
              f"({len(refused)} frontage(s) and {len(town_refused)} wagon stand(s) "
              "refused with a reason)")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {objects} object(s) on {len(frontages)} "
          f"frontage(s), {len(wagons)} wagon(s) ({len(town_wagons)} of them the town's), "
          f"{len(benches)} bench(es), {len(sheds)} shed(s) "
          f"({len(refused)} frontage(s) and {len(town_refused)} wagon stand(s) refused)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
