#!/usr/bin/env python3
"""The fabric-by-household rule: a reconstructed roof's finish says whose house it is.

T-1816, piece 1 of T-1210. The owner, on the town as built: *"make sure that businesses
and residences are correctly designed with the correct building materials and correct
surfaces, weathered appropriately, based on the type of person living there, like a
doctor or financial person, trader might have a nice house … or a laborer might have a
small not as nice house."*

WHAT IT REPLACES. Six generators dealt the four finish fields of an anonymous roof
without asking who it was for. `finish_for` hashed the record id (or stepped the
sequence) into a wall finish, and `roof_condition` and `age_state` were both
`(…)[seq % 4]` — so the two were locked together on every record, a merchant's house was
as likely to be silvered and patched as a shanty, and the fourth roof of every parcel was
always the newest. Nothing a visitor could read off a facade said anything about the
town's people.

WHAT DECIDES NOW, in this order:

1. **The keeper the record names.** Where `data/reconstruction/1835_roof_keepers.json`
   WROTE a household onto the roof (`resident_assignment.status: assigned`, 23 roofs),
   that household's own trade decides the class through `seat_known_1835.TRADE_CLAUSE` —
   the table the seat was dealt by — and its arrival year decides the age: a house is no
   older than its household's arrival in the town. The 80 seats T-0379 REFUSED (letter-
   list names) and the 45 still owed are never read: a household the project will not
   put under a roof does not get to paint it.
2. **The family's own household class.** Everywhere else — and for a keeper with no
   recorded trade — the reconstruction spec's family label already says whose building
   it is: an older log cabin or a shanty is a labourer's, a frame cottage a tradesman's,
   a merchant's or professional house a merchant's, a boarding house a keeper's, a store
   a shopkeeper's or a merchant's, a works a tradesman's shop, a shed or warehouse the
   freight trade's, and a stable or privy belongs to a yard. The age is then the class's
   own window into the boom (`AGES_BY_FAMILY`), dealt within it by a hash of the id.

BARE BOARDS FOLLOW THE AGE, and the sheet sets the clock: `weathered_timber` is "bare
stock silvered off by a season or two of weather", so a house raised in 1834 has already
silvered by July 1835 and only the scene year's own building is new-sawn.

WHAT EACH CLASS MAY WEAR (`CLASSES`), from materials.md's vocabulary and nothing new:
coatings are what money bought — the merchant's house is always coated (red oxide, ochre
or lime), a tradesman's sometimes (a cheap earth or lime wash), a labourer's never; a
boarding house is limewashed; works, freight and yard buildings are bare boards. Bare
stock follows the age (new-sawn, then silvered, then patched), and so does the roof,
held better on the houses money maintained and let go to patches on the cabins.
`white_paint` is the Sauganash's ALONE and no class can deal it.

THE GRADE does not move: every value this writes is `reconstructed`, as the programme's
deal was. A class bounds the reconstruction; it does not prove the paint. The rule and
its reasoning are L330 and materials.md §12.

THE FORM, T-1817 (piece 2 of T-1210). The same class and age now deal what a frame
building is BUILT as, not only what it is painted: `construction` by the age (a roof of
the 1834–35 boom is balloon-framed, the method this town invented in 1833; one of the
1832–33 town or older is braced), and on a frame house the `porch` and `shutters` by the
class (a merchant's or keeper's house a roofed porch and, on most, shutters; a
tradesman's cottage a plain stoop or nothing; a labourer's neither). Only a value the
programme dealt `reconstructed` is ever written; an attested or inferred one is never
moved (`apply_form`, `--self-test`). T-1838 added the glazing (L343). T-1839 adds the
trim and the chimney's head on a frame house by the class, and bounds the siding stock
by it: `tools/siding_stock.py` still deals the stock and still separates neighbours
(T-0112), but only inside the stocks the class's row allows (`SIDING_OF_CLASS`). The
cladding is not dealt — the archetype builds clapboard and nothing else — and nor is
the chimney's brick, which is inferred (chimneys.md §2). The reasoning is L338 and L352.

    python3 tools/fabric_rule_1835.py --check      every record agrees with the rule
    python3 tools/fabric_rule_1835.py --self-test  the rule's guarantees, by breaking them
    python3 tools/fabric_rule_1835.py --report     the class/finish mix, printed
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
STRUCTURES = DATA / "structures"
KEEPERS = DATA / "reconstruction" / "1835_roof_keepers.json"
HOUSEHOLDS = DATA / "residents" / "households"

AGES = ("new", "recent", "established", "older_frontier")

#: Arrival year → age. A house raised in the scene's own year is new timber; one raised
#: the year before has had a winter; 1832–33 is the first boom's; older is the frontier's.
def age_for_year(year: int) -> str:
    if year >= 1835:
        return "new"
    if year == 1834:
        return "recent"
    if year >= 1832:
        return "established"
    return "older_frontier"


#: The rule, one row per household class. `coat_share` is the fraction of the class's
#: roofs that wear a coating, and `coats` the coatings it may draw (equal weight). Bare
#: walls and roofs are read off the age. Every key is a materials.py FINISHES or
#: ROOF_CONDITIONS key; `--self-test` refuses any that is not.
CLASSES: dict[str, dict] = {
    "merchant": {
        "rule": "F-M", "who": "a merchant's or professional man's",
        "coat_share": 1.0, "coats": ("red_oxide", "ochre", "whitewash"),
        "bare": {"new": "fresh_timber", "recent": "fresh_timber",
                 "established": "weathered_timber", "older_frontier": "weathered_timber"},
        "roof": {"new": "fresh", "recent": "fresh", "established": "weathered",
                 "older_frontier": "weathered"},
        "why": "money bought the coat and kept the roof: the better houses are painted "
               "or washed, and their shingles are renewed before they patch",
    },
    "keeper": {
        "rule": "F-B", "who": "a boarding-house or tavern keeper's",
        "coat_share": 1.0, "coats": ("whitewash", "whitewash", "ochre"),
        "bare": {"new": "fresh_timber", "recent": "fresh_timber",
                 "established": "weathered_timber", "older_frontier": "weathered_timber"},
        "roof": {"new": "fresh", "recent": "weathered", "established": "darkened",
                 "older_frontier": "darkened"},
        "why": "a house that took in the public showed it a clean face, and lime was the "
               "cheapest clean face there was",
    },
    "tradesman": {
        "rule": "F-T", "who": "a tradesman's",
        "coat_share": 0.3, "coats": ("ochre", "whitewash"),
        "bare": {"new": "fresh_timber", "recent": "weathered_timber",
                 "established": "weathered_timber", "older_frontier": "mixed_patch"},
        "roof": {"new": "fresh", "recent": "weathered", "established": "darkened",
                 "older_frontier": "darkened"},
        "why": "mostly bare boards silvering with their age, a cheap earth or lime wash "
               "on some",
    },
    "labourer": {
        "rule": "F-L", "who": "a labourer's",
        "coat_share": 0.0, "coats": (),
        "bare": {"new": "fresh_timber", "recent": "mixed_patch",
                 "established": "weathered_timber", "older_frontier": "mixed_patch"},
        "roof": {"new": "fresh", "recent": "weathered", "established": "patched",
                 "older_frontier": "patched"},
        "why": "never coated; boards from whatever stock came to hand, and a roof mended "
               "rather than renewed",
    },
    "works": {
        "rule": "F-W", "who": "a tradesman's shop",
        "coat_share": 0.0, "coats": (),
        "bare": {"new": "fresh_timber", "recent": "weathered_timber",
                 "established": "mixed_patch", "older_frontier": "mixed_patch"},
        "roof": {"new": "fresh", "recent": "weathered", "established": "patched",
                 "older_frontier": "patched"},
        "why": "a working building is bare boards, patched where the work wore it",
    },
    "freight": {
        "rule": "F-F", "who": "the freight trade's",
        "coat_share": 0.0, "coats": (),
        "bare": {"new": "fresh_timber", "recent": "weathered_timber",
                 "established": "weathered_timber", "older_frontier": "weathered_timber"},
        "roof": {"new": "fresh", "recent": "weathered", "established": "darkened",
                 "older_frontier": "darkened"},
        "why": "a shed or warehouse is bare boards, new with the boom's trade",
    },
    "yard": {
        "rule": "F-Y", "who": "a yard building's",
        "coat_share": 0.0, "coats": (),
        "bare": {"new": "fresh_timber", "recent": "weathered_timber",
                 "established": "weathered_timber", "older_frontier": "mixed_patch"},
        "roof": {"new": "fresh", "recent": "weathered", "established": "darkened",
                 "older_frontier": "patched"},
        "why": "a stable, privy or shed is never coated",
    },
}

#: The reconstruction spec's family label (1835_family_archetype_crosswalk.json) read as
#: the household it was built for. The labels are quoted so the reading can be checked.
CLASS_OF_FAMILY: dict[str, tuple[str, str]] = {
    "D1": ("labourer", "an older log cabin"),
    "D2": ("labourer", "a rough plank dwelling or shanty"),
    "D3": ("tradesman", "a one-room frame cottage"),
    "D4": ("tradesman", "a two-room frame cottage"),
    "D5": ("tradesman", "a deep-plan frame cottage"),
    "D6": ("tradesman", "a one-and-a-half-story cottage"),
    "D7": ("tradesman", "a small two-story frame house"),
    "H1": ("merchant", "a larger one-and-a-half-story house"),
    "H2": ("merchant", "a merchant's or professional house"),
    "H3": ("keeper", "a boarding house"),
    "C1": ("tradesman", "a small shop, grocery or land office"),
    "C2": ("tradesman", "a store-residence"),
    "C3": ("merchant", "a narrow two-story store"),
    "C4": ("merchant", "a wide two-story store"),
    "T1": ("keeper", "a public house"), "T2": ("keeper", "a frontier inn"),
    "W1": ("works", "a blacksmith shop"), "W2": ("works", "a carpenter's shop"),
    "W3": ("works", "a cooper's or wheelwright's shop"),
    "W4": ("works", "a small artisan's shop"),
    "W5": ("works", "a riverside shop"),
    "F1": ("freight", "a freight shed"), "F2": ("freight", "a two-story warehouse"),
    "F3": ("freight", "a river warehouse"), "F4": ("freight", "a lumber shed"),
    "A1": ("yard", "a stable"), "A2": ("yard", "a barn or carriage shed"),
    "A3": ("yard", "a privy"), "A4": ("yard", "a woodshed"),
    "A5": ("yard", "a small utility shed"),
}

#: Where no keeper dates the house, the window of the boom its type was built in. The
#: November 1835 census counts 3,265 people in 398 dwellings, against a village of a few
#: hundred in 1833: most of the town was new or one winter old in July 1835. An older
#: log cabin is the exception by its own label; a shanty went up for the boom.
AGES_BY_FAMILY: dict[str, tuple[str, ...]] = {
    "D1": ("established", "older_frontier"),
    "D2": ("new", "recent"),
    "H1": ("new", "recent"), "H2": ("new", "recent"),
    "C3": ("new", "recent"), "C4": ("new", "recent"),
    "H3": ("new", "recent", "established"),
    "T1": ("new", "recent", "established"), "T2": ("new", "recent", "established"),
    "F1": ("new", "recent"), "F2": ("new", "recent"), "F3": ("new", "recent"),
    "F4": ("new", "recent"),
    "W1": ("recent", "established"), "W2": ("recent", "established"),
    "W3": ("recent", "established"), "W4": ("recent", "established"),
    "W5": ("recent", "established"),
    "A1": AGES, "A2": AGES, "A3": AGES, "A4": AGES, "A5": AGES,
}
#: Every other family — the frame cottages and small stores — the boom's own spread.
BOOM_AGES = ("new", "new", "recent", "recent", "established")

#: T-1817 — THE FORM. The frame archetypes, and the two values only a house builds.
FRAME_ARCHETYPES = ("frame_dwelling", "frame_storefront", "frame_tavern")
FRAMES = ("balloon_frame", "braced_frame")
#: Chicago's balloon frame is dated to 1833 (St Mary's, Augustine D. Taylor —
#: `andreas_1884_v1`, as frame_dwelling_params quotes it); the boom that followed was
#: raised that way. A house of the 1832–33 town or older was framed the old way.
FRAME_OF_AGE = {"new": "balloon_frame", "recent": "balloon_frame",
                "established": "braced_frame", "older_frontier": "braced_frame"}
#: Per class: the porch as (value, cumulative share) steps — a draw past the last step
#: is no porch — and the shutters as (share, colours). `bright_blue` is the
#: Sauganash's attested pair and, like `white_paint`, no class deals it.
FORMS: dict[str, dict] = {
    "merchant": {"porch": (("roofed", 0.75), ("stoop", 1.0)),
                 "shutters": (0.6, ("green", "green", "black")),
                 "why": "the house money built faced the street with a roofed porch over "
                        "the door and hung board shutters at most of its windows"},
    "keeper": {"porch": (("roofed", 1.0),), "shutters": (0.3, ("green",)),
               "why": "a house that took in the public sheltered its door, and a few "
                      "hung shutters"},
    "tradesman": {"porch": (("stoop", 0.6),), "shutters": (0.0, ()),
                  "why": "a plank stoop at the door on most, and no shutters"},
    "labourer": {"porch": (), "shutters": (0.0, ()),
                 "why": "neither porch nor shutters: the door opens onto the ground"},
}
#: T-1838 — THE GLAZING, per class, as (value, cumulative share) steps: the sash and the
#: pane (`frame_dwelling_params.GLAZINGS`). 6 x 8 in is the one pane attested at
#: Chicago (the Green Tree; Gale's guest chamber), so it is what the cottages and
#: shops glaze with; the larger boxed lights went to the houses that could pay for
#: them. No source glazes any particular house here (docs/LIBERTIES.md L343).
GLAZING: dict[str, tuple] = {
    "merchant": (("12_over_12_8x10", 0.5), ("12_over_12_7x9", 1.0)),
    "keeper": (("12_over_12_7x9", 1.0),),
    "tradesman": (("12_over_12_6x8", 0.7), ("9_over_6_6x8", 1.0)),
    "labourer": (("6_over_6_6x8", 0.7), ("9_over_6_6x8", 1.0)),
}
GLAZING_WHY = {
    "merchant": "the larger boxed lights, 8 x 10 or 7 x 9 in, twelve to a sash",
    "keeper": "7 x 9 in lights, twelve to a sash, at a house that took in the public",
    "tradesman": "the attested Chicago pane, 6 x 8 in, mostly twelve-over-twelve",
    "labourer": "the attested 6 x 8 in pane in the fewest lights, six or nine to a sash",
}


#: T-1839 — THE TRIM, per class: how heavily the sawn trim boxes the frame
#: (`frame_dwelling_params.TRIMS`). `plain` is the trim the archetype has always built,
#: so a tradesman's cottage does not move; a house that took in or impressed the public
#: boxed its corners in wider boards under a deeper frieze, and a labourer's house had
#: the narrowest boards that would keep the weather out of a corner. No source trims any
#: house here (docs/LIBERTIES.md L352).
TRIM: dict[str, str] = {"merchant": "boxed", "keeper": "boxed", "tradesman": "plain",
                        "labourer": "scant"}
TRIM_WHY = {
    "boxed": "wide corner boards under a deep frieze, the trim of a house built to be seen",
    "plain": "the plain corner boards and frieze a sided frame needs to keep water out",
    "scant": "the narrowest corner boards and frieze that keep the weather out",
}
#: T-1839 — THE CHIMNEY FABRIC. Every framed house's stack is brick, inferred and
#: never dealt (docs/RESEARCH/chimneys.md §2: an interior stack carries a fire through a
#: timber roof and the masonry Chicago had was brick). What the class deals is the
#: brickwork at the HEAD: the corbel course the archetype has always laid, doubled on the
#: houses money built, and left off the labourer's (`frame_dwelling_params.CHIMNEY_HEADS`).
CHIMNEY_HEAD: dict[str, str] = {"merchant": "double_corbel", "keeper": "double_corbel",
                                "tradesman": "corbel", "labourer": "plain"}
CHIMNEY_HEAD_WHY = {
    "double_corbel": "a brick stack finished in two corbelled courses",
    "corbel": "a brick stack finished in one corbelled course",
    "plain": "a brick stack carried straight up, with no corbel at its head",
}
#: T-1839 — THE SIDING STOCK, per class, reconciled with T-0112's neighbour separation
#: (`tools/siding_stock.py` reads this). A narrower exposure is more boards, more
#: nailing and more planing to hang the same wall, so the finest stock went on the
#: houses that could pay for it and the widest on the ones that could not; inside its
#: class's stocks a roof is still advanced off every neighbour within 60 m. A class not
#: named here (freight, works, yard) draws from all four. Metres, as `STOCKS` holds them.
SIDING_OF_CLASS: dict[str, tuple[float, ...]] = {
    "merchant": (0.114, 0.127),
    "keeper": (0.127, 0.140),
    "tradesman": (0.127, 0.140, 0.152),
    "labourer": (0.140, 0.152),
}
SIDING_WHY = {
    "merchant": "the narrowest stock, 4.5 or 5 in to the weather",
    "keeper": "a 5 or 5.5 in stock",
    "tradesman": "the common stock, 5 to 6 in to the weather",
    "labourer": "the widest stock, 5.5 or 6 in to the weather",
}


def glazing_words(key: str) -> str:
    """`12_over_12_8x10` → '12-over-12 sash of 8 × 10 in glass'."""
    up, _over, lo, pane = key.split("_")
    w, h = pane.split("x")
    return f"{up}-over-{lo} sash of {w} × {h} in glass"


TRIM_WORDS = {"boxed": "boxed corners", "plain": "plain corner boards",
              "scant": "scant corner boards"}
FORM_WORDS = {"balloon_frame": "on a balloon frame", "braced_frame": "on a braced frame"}
FORM_NOTE = ("RECONSTRUCTED BY THE FABRIC RULE (T-1817, docs/LIBERTIES.md L338). Dealt by "
             "tools/fabric_rule_1835.py from the household class and age it reads for this "
             "roof, not from evidence about this building: ")


def form_for_class(sid: str, klass: str, age: str, archetype: str) -> dict:
    """Construction, porch, shutters and glazing for one frame roof; `{}` for any other."""
    if archetype not in FRAME_ARCHETYPES:
        return {}
    out = {"construction": FRAME_OF_AGE[age]}
    if archetype != "frame_dwelling":
        return out
    row = FORMS.get(klass, FORMS["tradesman"])
    draw = _fraction(sid, "porch")
    out["porch"] = next((v for v, upto in row["porch"] if draw < upto), None)
    share, colours = row["shutters"]
    out["shutters"] = (colours[int(_fraction(sid, "shutter_colour") * len(colours))]
                       if colours and _fraction(sid, "shutters") < share else None)
    draw = _fraction(sid, "glazing")
    steps = GLAZING.get(klass, GLAZING["tradesman"])
    out["glazing"] = next(v for v, upto in steps if draw < upto)
    out["trim"] = TRIM.get(klass, TRIM["tradesman"])
    out["chimney_head"] = CHIMNEY_HEAD.get(klass, CHIMNEY_HEAD["tradesman"])
    return out


def form_why(key: str, klass: str, age: str) -> str:
    if key == "construction":
        return (f"the roof's age is {age!r}; a building of the 1834–35 boom is balloon-"
                "framed, the method dated here to 1833, and one of the 1832–33 town or "
                "older is braced (rule FORM-C).")
    if key == "glazing":
        return (f"{klass} class — {GLAZING_WHY.get(klass, GLAZING_WHY['tradesman'])} "
                "(rule FORM-G).")
    if key == "trim":
        trim = TRIM.get(klass, TRIM["tradesman"])
        return f"{klass} class — {TRIM_WHY[trim]} (rule FORM-T)."
    if key == "chimney_head":
        head = CHIMNEY_HEAD.get(klass, CHIMNEY_HEAD["tradesman"])
        return (f"{klass} class — {CHIMNEY_HEAD_WHY[head]}; the stack's brick is "
                "inferred and not dealt (rule FORM-H).")
    row = FORMS.get(klass, FORMS["tradesman"])
    return f"{klass} class — {row['why']} (rule FORM-{key[0].upper()})."


def apply_form(body: dict, fabric: dict) -> dict:
    """Write the rule's form into a generator's form body, mutated and returned.

    Only a `reconstructed` value is ever replaced or removed, and `construction` only
    where it is already a frame: an attested or inferred value, a log or a plank wall
    is never moved. A value the rule deals as absent (no porch, no shutters) is removed
    only if it too was reconstructed.
    """
    want = fabric.get("form") or {}
    basis = fabric["fabric_basis"]
    template = body.get("construction") or {}
    for key, value in want.items():
        cur = body.get(key)
        if isinstance(cur, dict) and cur.get("confidence") != "reconstructed":
            continue
        if key == "construction" and (cur or {}).get("value") not in FRAMES:
            continue
        if value is None:
            body.pop(key, None)
            continue
        body[key] = {"value": value, "confidence": "reconstructed",
                     "sources": list(template.get("sources") or []),
                     "note": FORM_NOTE + form_why(key, basis["class"], fabric["age_state"])}
    return body

#: seat_known_1835's clause, read as a class. A clause with no class here (the garrison,
#: the farms) leaves the family's class standing.
CLASS_OF_CLAUSE = {
    "merchant_and_professional_dwellings": "merchant",
    "tradesman_dwellings": "tradesman",
    "heavy_and_noxious_trades": "works",
    "labourer_dwellings": "labourer",
    "lodging_near_the_landings": "keeper",
}

PAINT_OF = {"whitewash": "whitewash", "red_oxide": "red"}

WALL_WORDS = {
    "fresh_timber": "new-sawn", "weathered_timber": "silvered", "mixed_patch": "patched",
    "ochre": "ochre-washed", "whitewash": "whitewashed", "red_oxide": "red-painted",
}
ROOF_WORDS = {"fresh": "a new roof", "weathered": "a weathered roof",
              "darkened": "a weather-darkened roof", "patched": "a patched roof"}
AGE_WORDS = {"new": "new-built", "recent": "a year old",
             "established": "from the 1832–33 town", "older_frontier": "older than the boom"}
SUBSTRATE_WORDS = {"log_dwelling": "hewn logs", "outbuilding": "boards"}


def _fraction(key: str, salt: str) -> float:
    digest = hashlib.sha256(f"fabric:{salt}:{key}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2 ** 64


@lru_cache(maxsize=1)
def _keepers() -> dict[str, str]:
    """structure id → household id, for the seats name_the_keepers WROTE and no other."""
    doc = json.loads(KEEPERS.read_text(encoding="utf-8"))
    return {row["structure_id"]: row["household_id"] for row in doc["written"]}


@lru_cache(maxsize=None)
def _household(hid: str) -> dict:
    """The keeper's trade and arrival year, read off their own card."""
    card = json.loads((HOUSEHOLDS / f"{hid}.json").read_text(encoding="utf-8"))
    trade = next((p["occupation"]["value"] for p in card.get("persons") or ()
                  if (p.get("occupation") or {}).get("value") not in (None, "none_recorded")),
                 None)
    year = (card.get("arrival_year") or {}).get("value")
    if year is None and (card.get("arrival") or {}).get("value"):
        year = int(str(card["arrival"]["value"])[:4])
    # "The Abbott household — a name the town's own records carry": the gloss after the
    # dash is the card's, and the Built line wants only whose house it is.
    name = (card.get("name") or hid).split(" — ")[0]
    return {"id": hid, "trade": trade, "year": year, "name": name}


@lru_cache(maxsize=1)
def _trade_clause() -> dict[str, str]:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from seat_known_1835 import TRADE_CLAUSE  # noqa: E402
    return TRADE_CLAUSE


def deal(sid: str, family: str, archetype: str, keeper: str | None = None) -> dict:
    """The four finish fields and the `fabric_basis` for one reconstructed roof.

    `keeper` defaults to the household the roof keepers ledger wrote onto `sid`.
    Deterministic in its inputs: the generators' `--check`s stay byte-exact.
    """
    keeper = keeper if keeper is not None else _keepers().get(sid)
    klass, type_words = CLASS_OF_FAMILY.get(family, ("tradesman", f"a {family} roof"))
    household = _household(keeper) if keeper else None
    by = "type"
    if household and household["trade"]:
        traded = CLASS_OF_CLAUSE.get(_trade_clause().get(household["trade"], ""))
        if traded and family[0] in "DHC":
            klass, by = traded, "trade"
    if household and household["year"]:
        age = age_for_year(int(household["year"]))
    else:
        window = AGES_BY_FAMILY.get(family, BOOM_AGES)
        age = window[int(_fraction(sid, "age") * len(window))]
    row = CLASSES[klass]
    if row["coats"] and _fraction(sid, "coat") < row["coat_share"]:
        finish = row["coats"][int(_fraction(sid, "which") * len(row["coats"]))]
    else:
        finish = row["bare"][age]
    roof = row["roof"][age]
    substrate = SUBSTRATE_WORDS.get(archetype, "clapboard")
    wall = (substrate if archetype == "log_dwelling"
            else f"{WALL_WORDS[finish]} {substrate}")
    form = form_for_class(sid, klass, age, archetype)
    if form:
        wall += f" {FORM_WORDS[form['construction']]}"
        extras = (([glazing_words(form["glazing"])] if form.get("glazing") else [])
                  + ([TRIM_WORDS[form["trim"]]] if form.get("trim") else [])
                  + ([f"{form['shutters'].replace('_', ' ')} shutters"]
                     if form.get("shutters") else [])
                  + {"roofed": ["a roofed porch"], "stoop": ["a stoop"]}
                  .get(form.get("porch"), []))
        if extras:
            listed = (", ".join(extras[:-1]) + " and " + extras[-1] if len(extras) > 1
                      else extras[0])
            wall += ", " + listed + ","
    if household:
        whose = f"{household['name']}'s"
        if household["trade"]:
            whose += f", a {household['trade'].replace('_', ' ')}"
        when = (f"in Chicago since {household['year']}" if household["year"]
                else "their arrival undated")
        words = f"{wall} under {ROOF_WORDS[roof]} — {whose}, {when} (rule {row['rule']})"
    else:
        words = (f"{wall} under {ROOF_WORDS[roof]} — {type_words}, {AGE_WORDS[age]} "
                 f"(rule {row['rule']}: {row['who']} by its type)")
    basis = {"rule": row["rule"], "class": klass, "by": "keeper" if household else "type",
             "household": keeper or None, "words": words}
    if household and by == "trade":
        basis["by"] = "keeper_trade"
    return {"finish_key": finish, "paint": PAINT_OF.get(finish, "unpainted"),
            "roof_condition": roof, "age_state": age, "fabric_basis": basis, "form": form}


def policy_table() -> dict:
    """The rule as the placement policy prints it (T-1195's file, T-1210's clause)."""
    return {
        "ticket": "T-1816",
        "dealt_by": "tools/fabric_rule_1835.py — every anonymous-roof generator deals "
                    "finish_key, paint, roof_condition and age_state through it",
        "order": [
            "1. the keeper 1835_roof_keepers.json WROTE onto the roof: their trade "
            "(seat_known_1835.TRADE_CLAUSE) sets the class of a dwelling or store, their "
            "arrival year the age. Refused and owed seats are never read.",
            "2. otherwise the family's household class (class_of_family), its age dealt "
            "inside the family's window of the boom (ages_by_family)."],
        "classes": {k: {kk: (list(vv) if isinstance(vv, tuple) else vv)
                        for kk, vv in v.items()} for k, v in CLASSES.items()},
        "class_of_family": {k: list(v) for k, v in CLASS_OF_FAMILY.items()},
        "ages_by_family": {k: list(v) for k, v in AGES_BY_FAMILY.items()},
        "boom_ages": list(BOOM_AGES),
        "white_paint": "the Sauganash's alone — no class deals it",
        "liberty": "L330",
        "form": {
            "ticket": "T-1817",
            "construction_by_age": dict(FRAME_OF_AGE),
            "frame_archetypes": list(FRAME_ARCHETYPES),
            "porch_and_shutters_by_class": {
                k: {"porch": [list(p) for p in v["porch"]],
                    "shutters": {"share": v["shutters"][0], "colours": list(v["shutters"][1])},
                    "why": v["why"]} for k, v in FORMS.items()},
            "glazing_by_class": {k: {"glazing": [list(g) for g in v], "why": GLAZING_WHY[k]}
                                 for k, v in GLAZING.items()},
            "trim_by_class": {k: {"trim": v, "why": TRIM_WHY[v]} for k, v in TRIM.items()},
            "chimney_head_by_class": {k: {"head": v, "why": CHIMNEY_HEAD_WHY[v]}
                                      for k, v in CHIMNEY_HEAD.items()},
            "siding_stock_by_class": {
                "ticket": "T-1839",
                "dealt_by": "tools/siding_stock.py deal_records, inside the class's stocks "
                            "and then off every neighbour within 60 m (T-0112)",
                "classes": {k: {"stocks_m": list(v), "why": SIDING_WHY[k]}
                            for k, v in SIDING_OF_CLASS.items()},
                "other_classes": "all four stocks"},
            "cladding": "clapboard on every frame dwelling — the one wall the archetype "
                        "builds; a vertical-board wall is a freight or works building's "
                        "and is not dealt here",
            "chimney_fabric": "brick on every framed house, inferred (chimneys.md §2), "
                              "never dealt; the class deals only the head",
            "never_moved": "an attested or inferred value, and any construction that is not a frame",
            "liberty": "L338, L343, L352"},
    }


# --------------------------------------------------------------------- the gate


def _records():
    for path in sorted(STRUCTURES.glob("*.json")):
        yield path, json.loads(path.read_text(encoding="utf-8"))


def check() -> list[str]:
    errors = []
    for path, rec in _records():
        recon = rec.get("reconstruction") or {}
        if "fabric_basis" not in recon:
            if recon.get("finish_key") and recon.get("status") == "inferred_anonymous":
                errors.append(f"{path.name}: an anonymous roof dealt a finish outside the rule")
            continue
        want = deal(rec["id"], recon["family"], rec.get("archetype", ""))
        for key in ("finish_key", "roof_condition", "age_state", "fabric_basis"):
            if recon.get(key) != want[key]:
                errors.append(f"{path.name}: reconstruction.{key} is {recon.get(key)!r}, "
                              f"the rule deals {want[key]!r}")
        for phase in rec.get("phases") or ():
            form = phase.get("form") or {}
            for key, value in want["form"].items():
                cur = form.get(key)
                if isinstance(cur, dict) and cur.get("confidence") != "reconstructed":
                    continue
                if key == "construction" and (cur or {}).get("value") not in FRAMES:
                    continue
                if (cur or {}).get("value") != value:
                    errors.append(f"{path.name}: form.{key} is "
                                  f"{(cur or {}).get('value')!r}, the rule deals {value!r}")
            paint = (form.get("paint") or {})
            if paint and paint.get("confidence") == "reconstructed" \
                    and paint.get("value") != want["paint"]:
                errors.append(f"{path.name}: form.paint is {paint.get('value')!r}, the "
                              f"rule deals {want['paint']!r}")
    return errors


def report() -> None:
    from collections import Counter
    by_class, finishes, coated, total, pts = Counter(), Counter(), 0, 0, []
    for _path, rec in _records():
        recon = rec.get("reconstruction") or {}
        basis = recon.get("fabric_basis")
        if not basis:
            continue
        total += 1
        by_class[(basis["class"], basis["by"])] += 1
        finishes[recon["finish_key"]] += 1
        coated += PAINT_OF.get(recon["finish_key"]) is not None
        for phase in rec.get("phases") or ():
            pos = phase.get("position") or {}
            if "utm_e" in pos:
                pts.append((pos["utm_e"], pos["utm_n"], recon["finish_key"]))
                break
    shared = 0
    for i, (e, n, f) in enumerate(pts):
        near = min(((math.hypot(e - e2, n - n2), f2) for j, (e2, n2, f2) in enumerate(pts)
                    if j != i), default=None)
        shared += bool(near and near[1] == f)
    print(f"{total} reconstructed roofs dealt by the fabric rule")
    for (klass, by), n in sorted(by_class.items()):
        print(f"  {klass:<10} by {by:<12} {n}")
    print("  finishes: " + ", ".join(f"{k} {v}" for k, v in finishes.most_common()))
    print(f"  coated (lime or paint): {coated} of {total} — the rest bare or earth-washed")
    print(f"  nearest neighbour shares the wall finish: {shared} of {len(pts)} "
          f"(T-1818's jitter is what separates them)")


def self_test() -> int:
    sys.path.insert(0, str(ROOT))
    from generators.common import materials  # noqa: E402
    failures = []
    walls, roofs = set(materials.FINISHES), set(materials.ROOF_CONDITIONS)
    for klass, row in CLASSES.items():
        for value in (*row["coats"], *row["bare"].values()):
            if value not in walls:
                failures.append(f"{klass} deals {value!r}, not a material-sheet finish")
            if value == "white_paint":
                failures.append(f"{klass} deals white_paint, which is the Sauganash's")
        for value in row["roof"].values():
            if value not in roofs:
                failures.append(f"{klass} deals roof {value!r}, not a sheet condition")
    for fam in CLASS_OF_FAMILY:
        for i in range(40):
            got = deal(f"selftest_{fam}_{i}", fam, "frame_dwelling", keeper="")
            if got["finish_key"] == "white_paint":
                failures.append(f"{fam} dealt white_paint")
            if got["fabric_basis"]["household"] is not None:
                failures.append(f"{fam}: no keeper, yet the basis names one")
    # a keeper's arrival year decides the age, whatever the family's window says
    keepers = _keepers()
    if keepers:
        sid, hid = next(iter(sorted(keepers.items())))
        hh = _household(hid)
        got = deal(sid, "D1", "log_dwelling")
        if hh["year"] and got["age_state"] != age_for_year(int(hh["year"])):
            failures.append(f"{sid}: keeper arrived {hh['year']} but the age is "
                            f"{got['age_state']}")
        if got["fabric_basis"]["household"] != hid:
            failures.append(f"{sid}: the basis does not name its keeper {hid}")
    # a merchant's house is always coated, a labourer's never
    for i in range(60):
        if deal(f"selftest_m_{i}", "H2", "frame_dwelling",
                keeper="")["finish_key"] not in CLASSES["merchant"]["coats"]:
            failures.append("an H2 house came out bare")
            break
        if deal(f"selftest_l_{i}", "D2", "frame_dwelling", keeper="")["finish_key"] in PAINT_OF:
            failures.append("a shanty came out coated")
            break
    # T-1817: the form. An attested or inferred value is never moved, nor a log wall;
    # a labourer's house gets no porch or shutters; the Sauganash's blue is never dealt.
    fab = deal("selftest_form_h2", "H2", "frame_dwelling", keeper="")
    fab["form"].update(porch="roofed", shutters="green")
    held = {"construction": {"value": "braced_frame", "confidence": "inferred", "note": "x"},
            "porch": {"value": "stoop", "confidence": "documented", "sources": ["s"]}}
    got = apply_form({k: dict(v) for k, v in held.items()}, fab)
    if got["construction"] != held["construction"] or got["porch"] != held["porch"]:
        failures.append("apply_form moved an inferred or documented form value")
    logs = apply_form({"construction": {"value": "log", "confidence": "reconstructed"}}, fab)
    if logs["construction"]["value"] != "log":
        failures.append("apply_form re-framed a log wall")
    none = deal("selftest_form_none", "D3", "frame_dwelling", keeper="")
    none["form"].update(porch=None, shutters=None)
    gone = apply_form({"construction": {"value": "balloon_frame", "confidence": "reconstructed"},
                       "porch": {"value": "stoop", "confidence": "reconstructed"}}, none)
    if "porch" in gone:
        failures.append("apply_form kept a reconstructed porch the rule deals as none")
    for i in range(80):
        lab = form_for_class(f"selftest_lab_{i}", "labourer", "new", "frame_dwelling")
        if lab.get("porch") or lab.get("shutters"):
            failures.append("a labourer's house was dealt a porch or shutters")
            break
        mer = form_for_class(f"selftest_mer_{i}", "merchant", "recent", "frame_dwelling")
        if mer.get("shutters") == "bright_blue":
            failures.append("a merchant's house was dealt the Sauganash's blue shutters")
            break
        if not mer.get("porch") or mer["construction"] != "balloon_frame":
            failures.append("a merchant's 1834 house came out without a porch or balloon frame")
            break
        # T-1838: every glazing dealt is one the archetype builds, and the boxed
        # sizes follow the money — no labourer behind 8 x 10s, no merchant behind 6 x 8s
        if lab["glazing"].endswith(("7x9", "8x10")) or mer["glazing"].endswith("6x8"):
            failures.append("a glazing went to the wrong class")
            break
    sys.path.insert(0, str(ROOT / "generators"))
    from archetypes.frame_dwelling_params import (CHIMNEY_HEADS, GLAZINGS,  # noqa: E402
                                                  TRIMS)
    dealt = {v for steps in GLAZING.values() for v, _ in steps}
    if dealt - set(GLAZINGS):
        failures.append(f"the rule deals glazings the archetype cannot build: "
                        f"{sorted(dealt - set(GLAZINGS))}")
    # T-1839: every trim and head dealt is one the archetype builds; the boxed trim and
    # the doubled head follow the money; the siding stocks are the shared set's, the
    # finest no wider than the widest, and the merchant's never the labourer's.
    if set(TRIM.values()) - set(TRIMS) or set(CHIMNEY_HEAD.values()) - set(CHIMNEY_HEADS):
        failures.append("the rule deals a trim or chimney head the archetype cannot build")
    for klass in ("merchant", "keeper", "tradesman", "labourer"):
        got = form_for_class(f"selftest_trim_{klass}", klass, "new", "frame_dwelling")
        if got.get("trim") != TRIM[klass] or got.get("chimney_head") != CHIMNEY_HEAD[klass]:
            failures.append(f"a {klass}'s house was not dealt its row's trim and head")
    if TRIM["labourer"] == "boxed" or TRIM["merchant"] != "boxed" \
            or CHIMNEY_HEAD["labourer"] == "double_corbel":
        failures.append("the boxed trim or the doubled head went to the wrong class")
    from siding_stock import STOCKS  # noqa: E402
    stock_set = {m for _, m in STOCKS}
    for klass, stocks in SIDING_OF_CLASS.items():
        if set(stocks) - stock_set or not stocks:
            failures.append(f"{klass} siding stocks {stocks} are not the shared set's")
    if max(SIDING_OF_CLASS["merchant"]) >= max(SIDING_OF_CLASS["labourer"]) \
            or set(SIDING_OF_CLASS["merchant"]) & set(SIDING_OF_CLASS["labourer"]):
        failures.append("the merchant's siding is no finer than the labourer's")
    if form_for_class("selftest_cabin", "merchant", "new", "log_dwelling"):
        failures.append("a log house was dealt a frame form")
    # the gate catches a record that drifted off the rule
    for path, rec in _records():
        recon = rec.get("reconstruction") or {}
        if "fabric_basis" in recon:
            other = next(k for k in walls if k != recon["finish_key"] and k in WALL_WORDS)
            recon["finish_key"] = other
            if not any(path.name in e for e in _check_one(path, rec)):
                failures.append("check() did not refuse a drifted finish")
            break
    for f in failures:
        print(f"FAIL {f}")
    print("fabric rule self-test: " + ("PASS" if not failures else "FAIL"))
    return 1 if failures else 0


def _check_one(path: Path, rec: dict) -> list[str]:
    recon = rec["reconstruction"]
    want = deal(rec["id"], recon["family"], rec.get("archetype", ""))
    return [f"{path.name}: {k}" for k in ("finish_key", "roof_condition", "age_state")
            if recon.get(k) != want[k]]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.report:
        report()
        return 0
    errors = check()
    for e in errors[:40]:
        print(f"  - {e}")
    if errors:
        print(f"FABRIC RULE DRIFT: {len(errors)} value(s) off the rule")
        return 1
    report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
