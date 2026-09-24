#!/usr/bin/env python3
"""T-1371 (of T-1175), stage `lodgers` — the boarders, in the beds the town had.

    python3 tools/seat_lodgers_1835.py --build      seat them, write the cards
    python3 tools/seat_lodgers_1835.py --check      re-derive and refuse drift
    python3 tools/seat_lodgers_1835.py --report     who sleeps where, against what
    python3 tools/seat_lodgers_1835.py --self-test  the rules, each refusing its case

WHAT THIS STAGE IS. T-1370 gave every lodging place the dataset holds an ordinary-night
and a full capacity and seated nobody in them: fifteen built houses with 135 ordinary
beds between them, and thirty people on their cards — eight keepers and their families.
This stage fills the ordinary-night figure. It is piece 2 of 3 of T-1175; piece 3
(T-1372) has the crews of the vessels in port, the hands at the works, and the card that
prints who lived in a house.

THE ORDER THE BEDS ARE FILLED IN, and it is the parent ticket's, not this tool's.

  1. THE SOLITARY HEADS THE HOUSEHOLD MODEL ALREADY DREW. Two stages of this programme
     have already decided that a man kept no family: T-1171 drew five named heads as
     `solitary`, and T-1173 drew fourteen of its trade heads at a household size of one.
     Nineteen people the model itself says lived alone, none of whom has a roof. They are
     seated FIRST, because a bed filled by somebody the layer already holds is a bed that
     costs the town nothing — it is not a new person, it is a person given somewhere to
     sleep, and it takes a house off the lot queue T-1199 would otherwise have to find
     ground for.

  2. THE SHORT BEDS, filled with lodgers drawn against the order book's own
     `household_type: lodging` buckets. Nothing is invented past the quota: the book
     ordered 544 people into lodging households and this piece spends part of that order.

  3. THE KEEPER. A reconstructed lodging house with no keeper is not a lodging house, so
     the five roofs the reconstruction programme raised as lodging places are given one,
     at the trade their own `function` states. A NAMED house is never given a keeper:
     who kept the New York House in 1835 is a research question and inventing an answer
     would put a fabricated proprietor into a documented building.

THE MIX. Professionals and land agents at the Tremont, the Sauganash and the Mansion
House; mechanics at the Green Tree, the Steamboat and the smaller houses; labourers and
the people no roster gives a trade on the floors of the boarding houses. That is the
parent ticket's sentence, implemented as the literal named lists it gives, because the
grouping is NOT the same as the records' `function` field — the Steamboat Hotel is a
`hotel` and stands in the mechanics' list all the same. A seat is a RULE and not a draw:
the house with the most free beds in the group takes the next person, ties broken on the
id, so two runs over one layer seat the same people in the same houses without a seed.

WHAT IT REFUSES, each one written rather than quietly taken.

  1. NO DIVISION, NO MINT — AND SINCE T-1535 THAT IS A MUCH NARROWER REFUSAL. A person
     drawn into a lodging house has to be ordered out of the book's bucket for a
     division. `data/structures/*.json` carries no division field, and this stage used to
     read that as the dataset saying nothing, so the New York House and the Sauganash
     Hotel — two documented houses the residents layer attaches nobody to, between them
     ELEVEN empty ordinary-night beds and every other built house full — minted nobody.
     That was a fact about where this tool looked. `1835_existing_roof_reconciliation`
     has settled every documented roof standing on the scene date into a district since
     T-0283's programme work, and it names both of them: south, and south. So the
     division is read, in this order, off the programme's own district for the roof, then
     off a household the residents layer attaches to the house, then off that
     reconciliation — last, so that nothing already resolved moves. A house all three are
     silent about, or one reconciled into the `fort` district, which is not one of the
     town's three civil divisions, still mints nobody and the ledger still says why.
     Seating somebody already in the layer there is allowed either way, because a person
     the town already counts needs no bucket.

  2. NO TRADE IS DEALT. The book's `lodging/trade` buckets want working lodgers and this
     stage does not fill them, because dealing a trade is T-1173's machinery and the
     1839 directory's shares are its table. The lodgers minted here carry
     `none_recorded`, the same as the people the rosters print without one, and the
     `lodging/trade` order stays open for the stage that can price it. The only trade
     written anywhere here is a minted keeper's, and that is read off the building's own
     `function` rather than dealt.

  3. NO CHILDREN. The book orders 156 people under ten into lodging households. They are
     the keepers' own families, not boarders — a child does not take a bed at a tavern on
     their own account — so this stage draws only the adult and adolescent bands and
     leaves the `under_10` lodging order to the stage that completes a keeper's family.

  4. NO KEEPER'S FAMILY IS DRAWN. "With each keeper's own household complete" is in this
     ticket's title, and the completion is NOT this stage's to make: the kin of a
     household are `family/none` in the order book and that quota belongs to T-1171 and
     T-1174. What this stage does instead is STATE the shortfall — the `keepers` table
     names every lodging place's keeper, how many people stand on their card, and the
     ticket that owes them the rest. Piece 1 of this same parent (T-1370) refused the
     staffing model in its own title for the same reason and named T-1183; this is that
     refusal made twice, which is what a split ticket looks like when the title was
     written before the dependency was read.

  5. A KEEPER IS NOT ANOTHER HOUSE'S BOARDER. Two of T-1173's fourteen solitary heads are
     boarding-house keepers. They are held out of the boarder pool and not seated: their
     division is the order book's and this stage may not move it, so which house they
     kept is T-1199's placement question.

WHERE THE CARDS LIVE. `data/residents/lodgers/`, beside T-1172's `readmitted/` and
T-1347's `reconstructed_trades/`, and for the same reason: `data/residents/households/`
is re-derived by the research mints and `data/residents/index.json` is derived from that
directory, so a reconstruction that is not a reading lives outside both and is overlaid
onto the scene by `tools/compile_scene.py`. Nothing here reaches back into a research
card — a seated head keeps their own card untouched and the seat is carried in this
stage's ledger, which is the same shape T-1172's presence rulings already use.

EVERY VALUE IS REPRODUCIBLE. Each drawn value comes from `blake2s(seed)` over a seed a
reader can retype, and the seed is printed on the record that carries it. `--check`
re-derives the whole directory and refuses a single differing byte.

AND THE ROOM IT IS ALL DEALT AGAINST IS COMMITTED (T-1503). The deal is proportional to
what the order book has left in each cell, so reading the book live made the whole draw
move whenever the book was re-cut — and a re-cut of 35 undrawn slots on 2026-09-21
re-dealt 25 of the 56 boarders below, which other layers had by then adopted by name.
The quota this stage deals against is therefore recorded once, in `quota_basis` in its
own ledger, and carried: the book may be re-cut underneath it and not one card moves.
`committed_basis()` states the whole argument, `refuse_a_recut_under_the_draw()` is the
floor under it, and the `--self-test` proves it by re-cutting a copy of the book.
"""

from __future__ import annotations

import argparse
import hashlib
import tempfile
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
RESIDENTS = ROOT / "data" / "residents"
HOUSEHOLDS = RESIDENTS / "households"
READMITTED = RESIDENTS / "readmitted"
TRADES = RESIDENTS / "reconstructed_trades"
MINTED = RESIDENTS / "lodgers"
RECON = ROOT / "data" / "reconstruction"
LODGING = RECON / "1835_lodging_model.json"
BOOK = RECON / "1835_reconstruction_order_book.json"
POOLS = RECON / "1835_invented_name_pools.json"
FAMILIES = RECON / "1835_modelled_families.json"
TRADE_LEDGER = RECON / "1835_trade_households.json"
ROOF_RECONCILIATION = RECON / "1835_existing_roof_reconciliation.json"
LEDGER = RECON / "1835_lodgers_seated.json"

STAGE = "lodgers"
TICKET = "T-1371"
#: The keepers' own children (T-1533). A SECOND TICKET IN ONE TOOL, and the reason is
#: `--check`: this stage re-derives `data/residents/lodgers/` byte for byte, so a
#: separate tool could not write one person onto a card here without the gate reading it
#: as drift. The children are therefore drawn by this tool and counted against their own
#: ticket in the order book, so the book still says which piece of work filled which cell.
CHILD_TICKET = "T-1533"
PARENT = "T-1175"
PROGRAMME_ID = "chicago_1835_resident_reconstruction"
SCENE_DATE = "1835-07-01"
RECONSTRUCTED = "reconstructed"
PREFIX = "rc_"
SOURCE_PASS = "reconstructed_lodging_household"

BAND_EDGES = {"under_10": (0, 9), "10_19": (10, 19), "20_29": (20, 29),
              "30_39": (30, 39), "40_49": (40, 49), "50_plus": (50, None)}
#: The bands a LODGER may be drawn into, WRITTEN OUT rather than read off `BAND_EDGES`.
#: `under_10` is refused a bed — refusal 3 above — and T-1533 added it to the edges so a
#: keeper's child can carry a band; deriving this tuple from the keys would have let that
#: one line deal infants into the boarding houses as boarders.
ADULT_BANDS = ("10_19", "20_29", "30_39", "40_49", "50_plus")

#: The band a keeper's child is drawn into by this stage. The `10_19` lodging cells are
#: discharged — the boarders stage filled 16 of 16 — so a child the household model draws
#: into adolescence is refused here and the refusal is written, never re-banded downward.
CHILD_BAND = "under_10"

#: The mix, as the parent ticket states it. The first two groups are NAMED HOUSES and not
#: a class test, because the ticket names them: the Steamboat Hotel's record says `hotel`
#: and the sentence puts it with the mechanics all the same.
PROFESSIONAL_HOUSES = ("tremont_house_1", "sauganash_hotel", "mansion_house")
MECHANIC_HOUSES = ("green_tree_tavern", "steamboat_hotel")

#: Which group a person's own trade sends them to. A trade in neither set — and
#: `none_recorded`, which is most of this layer — goes to the boarding houses, which is
#: the parent's own default: "labourers on the floors of the boarding houses".
PROFESSIONAL_TRADES = frozenset({
    "attorney", "physician", "druggist", "land_agent", "merchant", "dry_goods_merchant",
    "hardware_merchant", "lumber_merchant", "grocer", "auctioneer", "clerk", "editor",
    "schoolteacher", "justice_of_the_peace", "army_officer", "sheriff", "surveyor",
    "postmaster", "minister", "banker", "forwarding_merchant", "commission_merchant",
})
MECHANIC_TRADES = frozenset({
    "blacksmith", "carpenter", "joiner", "cooper", "wheelwright", "wagon_maker", "tailor",
    "shoemaker", "tanner", "saddler", "tinner", "mason", "painter", "baker", "butcher",
    "printer", "boatman", "millwright", "brickmaker", "gunsmith", "hatter", "cabinetmaker",
})

#: The trade a minted keeper carries, read off the house's own `function`. Never dealt.
KEEPER_TRADE = {"boarding_house": "boarding_house_keeper", "inn_tavern": "tavern_keeper"}

#: What a person sleeping in a house of each class is called. A boarding house sold board
#: — a bed and a table, by the week; an inn sold a bed by the night. The words are the
#: residents vocabulary's own (`relationships`), and the distinction is the houses', not
#: a claim about any one person's terms.
RELATION = {"boarding_house": "boarder", "inn_tavern": "lodger"}

#: A keeper whose own trade is keeping a house is not seated as somebody else's boarder.
KEEPER_TRADES = frozenset({"boarding_house_keeper", "tavern_keeper", "hotel_keeper"})

DIVISIONS = ("south", "north", "west")


# -------------------------------------------------------------------- the draw --

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


def allocate(total: int, weights: list) -> dict:
    """Largest remainder, ties broken on the key — the order book's own rounding rule, so
    two builds over one set of inputs are byte-identical and no count is a float."""
    total = int(total)
    if total <= 0:
        return {}
    mass = float(sum(w for _, w in weights))
    if mass <= 0:
        return {}
    exact = [(key, total * float(w) / mass) for key, w in weights]
    out = {key: int(value) for key, value in exact}
    short = total - sum(out.values())
    order = sorted(exact, key=lambda kv: (-(kv[1] - int(kv[1])), str(kv[0])))
    for index in range(short):
        out[order[index % len(order)][0]] += 1
    return {k: v for k, v in out.items() if v}


def allocate_within(total: int, weights: list, capacity: dict) -> tuple:
    """`allocate()`, but no cell is dealt more than the room it actually has left.

    T-1535. The deal above is proportional and knows nothing about capacity, which is
    fine where the room is large against the deal and wrong where it is not: the two
    houses T-1535 brings in are dealt against what the BOOK has left today rather than
    against this stage's frozen basis, and two of the south cells they weigh on have four
    slots and no more. Over-dealing one of them is refused by `refuse()` — correctly, as
    "a re-cut has taken the order out from under people already standing" — so the deal
    has to respect the ceiling itself.

    Largest remainder is kept, and the surplus a clamped cell sheds is re-dealt over the
    cells that still have room, until the total is spent or the room is. Returns the deal
    and what could NOT be dealt, because a bed left empty for want of an order is a thing
    the ledger says out loud rather than a number that quietly disappears.
    """
    out: dict = {}
    left = int(total)
    while left > 0:
        pool = [(key, w) for key, w in weights if capacity.get(key, 0) - out.get(key, 0) > 0]
        if not pool:
            break
        moved = 0
        for key, count in allocate(left, pool).items():
            take = min(count, capacity.get(key, 0) - out.get(key, 0))
            if take > 0:
                out[key] = out.get(key, 0) + take
                moved += take
        if moved == 0:
            break
        left -= moved
    return {k: v for k, v in out.items() if v}, left


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def value_of(block):
    return block.get("value") if isinstance(block, dict) else block


# ------------------------------------------------------------------ the inputs --

def lodging_model() -> dict:
    return load(LODGING)


def pools() -> dict:
    return load(POOLS)


def committed_districts() -> dict:
    """structure id -> the district the roof reconciliation already committed for it.

    T-1535. The refusal below used to say that "nothing this project holds says which
    division it stood in", and that was true of `data/structures/*.json`, which carries no
    division field — but it was never true of the dataset. `1835_existing_roof_reconciliation`
    settles every documented roof standing on the scene date into a district, BY NAME, and
    it names both houses this stage was refusing. The refusal was a fact about where this
    tool looked, not about the evidence.

    It is read LAST, after the programme's own district and after the household the
    residents layer attaches, so no house already resolved can move: the two sources
    disagree on exactly one house — `western_hotel`, south to the household that lives
    there and west to the reconciliation — and this ordering leaves that house, and the
    people already seated in it, exactly where they are. The disagreement is not swallowed:
    every house row carries `district_in_the_roof_reconciliation` beside the division it
    took, so a reader can see the two and T-1207 can adjudicate it.

    `fort` is a district of the building programme and is NOT one of the town's three
    civil divisions, so a roof reconciled there resolves to nothing here and keeps the
    refusal.
    """
    return {r["structure_id"]: r.get("district")
            for r in load(ROOF_RECONCILIATION)["records"]}


def sibling_directories() -> list:
    """Every directory of `data/residents/` that holds household cards, EXCEPT this
    stage's own.

    NAMED DIRECTORIES WERE NOT ENOUGH, and the gate said so. This read
    `(HOUSEHOLDS, READMITTED, TRADES)` until T-1353's transient cohort landed on `dev`
    between this branch's first build and its merge: `data/residents/transients/` did not
    exist when the list was written, so twelve lodgers were drawn with names and ids that
    stage had already spent, and `no committed list carries the same id twice` went red on
    `data/sidecars/1835/people.json`. A hard-coded list of sibling stages is a list that
    goes stale every time the programme grows a stage, which is every few days.

    So the directories are DISCOVERED. Any stage that writes `hh_*.json` under
    `data/residents/` is stepped past from the moment its cards exist, without this tool
    being told about it. The one directory left out is this stage's own, because a build
    that read its own previous answer as a spent name would draw a different person on the
    second run and `--check` would call that drift.

    The deference runs one way and that is deliberate: a stage already merged owns its
    names, and this one moves around them. The reverse — teaching every earlier stage to
    read `lodgers/` — would invalidate cards that are already committed and gated.
    """
    if not RESIDENTS.exists():
        return []
    return [d for d in sorted(RESIDENTS.iterdir())
            if d.is_dir() and d != MINTED and any(d.glob("hh_*.json"))]


def cards_in(directory: Path) -> list:
    if not directory.exists():
        return []
    return [(path, load(path)) for path in sorted(directory.glob("hh_*.json"))]


def layer() -> tuple:
    """(every name in the layer, the names REAL people bear, every person id).

    The programme's collision check: an invented name may never be an attested or
    inferred person's name. The other two sets are weaker and still necessary — a name
    another reconstruction already drew is stepped past where the pools allow it, and an
    id another stage holds may NEVER be reused, because an id that names two people is
    not an id. This stage reads `reconstructed_trades/` as well as the research
    directories, because T-1347 draws from the same pools.
    """
    all_names, real, ids = set(), set(), set()
    for directory in sibling_directories():
        for _, card in cards_in(directory):
            for person in card.get("persons") or []:
                name = " ".join(str(person.get("name") or "").split()).lower()
                pid = str(person.get("id") or "")
                if pid:
                    ids.add(pid)
                if not name:
                    continue
                all_names.add(name)
                if person.get("grade") != RECONSTRUCTED:
                    real.add(name)
    return all_names, real, ids


def occupancy() -> tuple:
    """(place -> the people already on its card, place -> the household that keeps it).

    Read off `lives_at` across the whole residents layer, which is the same join
    `tools/compile_scene.py` makes to put a household on a building's card. A household
    that WORKS at a house without living in it is its keeper and does not sleep there;
    both are recorded, because the keeper table wants the second and the bed count wants
    the first.
    """
    lives: dict[str, list] = {}
    keeps: dict[str, list] = {}
    for directory in (HOUSEHOLDS, READMITTED, TRADES):
        for _, card in cards_in(directory):
            at = value_of(card.get("lives_at"))
            works = value_of(card.get("works_at"))
            if at:
                lives.setdefault(at, []).append(card)
            if works:
                keeps.setdefault(works, []).append(card)
    return lives, keeps


def solitary_heads() -> list:
    """The people two stages of this programme have already drawn as living alone.

    T-1171's `solitary` household type and T-1173's household size of one. Both are the
    HOUSEHOLD MODEL's own verdict — not this stage's reading of a card — which is what
    makes seating them a spend of an existing decision rather than a new claim about
    where a named resident slept.
    """
    out = []
    families = load(FAMILIES).get("by_household", {}) if FAMILIES.exists() else {}
    for hid, row in sorted(families.items()):
        if row.get("household_type") != "solitary":
            continue
        path = HOUSEHOLDS / f"{hid}.json"
        if not path.exists():
            continue
        out.append(("T-1171", "modelled_families", path, load(path)))
    trades = load(TRADE_LEDGER).get("minted", []) if TRADE_LEDGER.exists() else []
    for row in sorted(trades, key=lambda r: str(r.get("id"))):
        path = RESIDENTS / row["file"]
        if not path.exists():
            continue
        card = load(path)
        if (card.get("household_owed") or {}).get("size_drawn") != 1:
            continue
        out.append(("T-1173", "trade_households", path, card))
    return out


def book_lodging_room() -> dict:
    """(division, sex, band, trade axis) -> (bucket key, how many the book orders there NOW.

    `to_reconstruct` is read and `filled` is ignored, which is the opposite of what
    T-1347 does with the same file and is deliberate. The book derives `to_reconstruct`
    from the town model's target less the KNOWN layer, and this stage's cards are not in
    the known layer — they live outside `data/residents/index.json`, like every
    reconstruction — so a build does not move it. `filled` is the counter this stage
    writes back; taking it off the room would make the second build draw against a
    smaller quota than the first, and `--check` would read that as drift. It did, once:
    the Steamboat Hotel's card came out differently on the build and the check.
    """
    book = load(BOOK)
    out = {}
    for family in book.get("bucket_families", []):
        if family.get("key") != "persons":
            continue
        for bucket in family.get("buckets", []):
            axes = bucket["axes"]
            if axes.get("household_type") != "lodging":
                continue
            out[(axes["division"], axes["sex"], axes["age_band"], axes["trade"])] = (
                bucket["key"], int(bucket.get("to_reconstruct") or 0))
    return out


def committed_basis() -> list:
    """The room THIS STAGE'S DEAL WAS MADE AGAINST, read off this stage's own committed
    ledger. `[]` before the first build has recorded one.

    T-1503, AND THE REASON THE ROOM IS NOT READ LIVE. The deal below is proportional: a
    lodger's sex and band come from `allocate()` over the room each cell has left, and a
    minted keeper's from `pick()` over the same weights. So the deal moves whenever ANY
    lodging bucket's `to_reconstruct` moves — and the book is re-cut: T-1459 re-cuts the
    trade axis under the owner's ruling of 2026-09-20 and T-1166 owns the book. Measured
    on 2026-09-21: a re-cut of 35 undrawn slots re-dealt 25 of this stage's 56 invented
    boarders, and six further gate steps went red with them, because
    `rcb_cavanagh_boarding_house` adopts the invented `rc_cavanagh_johanna` as its keeper
    by name, the employment join seats her there and the employment coverage pass answers
    for her. An invented lodger another layer has adopted is not re-dealable.

    So the room is the BASIS RECORDED WHEN THE DEAL WAS MADE, carried forward figure for
    figure, and the book may be re-cut underneath it without moving one card. Four things
    keep that honest rather than merely convenient:

      * the basis is COMMITTED, in this stage's own ledger, one row per bucket with the
        axes it was dealt on — so `--check` re-derives the same deal from the same
        numbers, `--build` twice in a row is a fixed point, and a reader can retype it;
      * it is CLOSED. The deal was dealt against exactly these buckets, so a bucket that
        appears in the book afterwards is not in the room — otherwise a cell the re-cut
        re-opened would walk back into the keeper weights and move the cards, which is
        the whole fault this is fixing;
      * where the book has since been re-cut, the divergence is STATED bucket by bucket
        in `quota_basis.re_cut_since` rather than silently absorbed; and
      * the one thing a re-cut may NOT do is take the order out from under somebody
        already standing, so `refuse()` fails if the book's live `to_reconstruct` for a
        bucket has fallen below what this stage drew out of it.
    """
    if not LEDGER.exists():
        return []
    rows = (load(LEDGER).get("quota_basis") or {}).get("buckets") or []
    return [dict(row) for row in rows]


def lodging_buckets() -> dict:
    """(division, sex, band, trade axis) -> (bucket key, the room the deal is dealt against).

    The committed basis where there is one, the book's live figures on the first build —
    `committed_basis()` above is the whole argument.
    """
    basis = committed_basis()
    if not basis:
        return book_lodging_room()
    return {(row["division"], row["sex"], row["age_band"], row["trade"]):
            (row["bucket"], int(row["to_reconstruct"])) for row in basis}


def basis_block(room: dict) -> dict:
    """The basis as it will be committed, and every way the book has moved away from it.

    `buckets` is the room the deal above was dealt against, which on a first build is the
    book's own `to_reconstruct` and on every build after that is this same block read
    back. `re_cut_since` is the difference between that and the live book, in the three
    shapes it can take, each stated rather than absorbed.
    """
    live = book_lodging_room()
    live_by_key = {key: n for key, n in live.values()}
    rows = [{"bucket": key, "division": div, "sex": sex, "age_band": band, "trade": axis,
             "to_reconstruct": n}
            for (div, sex, band, axis), (key, n) in sorted(room.items())]
    moved = [{"bucket": row["bucket"], "the_deal_was_dealt_against": row["to_reconstruct"],
              "the_book_orders_now": live_by_key[row["bucket"]]}
             for row in rows
             if row["bucket"] in live_by_key
             and live_by_key[row["bucket"]] != row["to_reconstruct"]]
    gone = sorted(row["bucket"] for row in rows if row["bucket"] not in live_by_key)
    fresh = sorted(set(live_by_key) - {row["bucket"] for row in rows})
    return {
        "$note": "DERIVED, and the room this stage deals against. T-1503: the deal is "
                 "proportional to the room, so reading the room live would re-deal "
                 "boarders the business layer and the employment join already name. The "
                 "basis is recorded once and carried, the book may be re-cut under it, "
                 "and every divergence is stated below.",
        "owning_ticket": "T-1503",
        "read_from": "the book's `to_reconstruct` on the build that first recorded it; "
                     "this block on every build after",
        "buckets": rows,
        "re_cut_since": {
            "statement": "The book has been re-cut in these cells since the deal was "
                         "dealt. Nobody moves: the cards stand on the basis, and the "
                         "re-cut spends what this stage did not.",
            "the_book_moved": moved,
            "gone_from_the_book": gone,
            "new_since_the_deal": fresh,
            "note": "`new_since_the_deal` is deliberately OUTSIDE the room. A cell the "
                    "re-cut re-opened is work for the stage that asked for it — T-1448's "
                    "shop boys — and letting it back into these weights would re-deal "
                    "this stage's own draw, which is the fault T-1503 fixed.",
        },
    }


# -------------------------------------------------------------------- the plan --

def group_of(trade) -> str:
    """Which of the mix's three groups a person's own trade sends them to."""
    if trade in PROFESSIONAL_TRADES:
        return "professional"
    if trade in MECHANIC_TRADES:
        return "mechanic"
    return "labour"


def houses_for(group: str, houses: list) -> list:
    """The houses of a group, in the order a seat takes them: most free beds first, ties
    on the id. A rule, not a draw — see the module docstring."""
    if group == "professional":
        pool = [h for h in houses if h["id"] in PROFESSIONAL_HOUSES]
    elif group == "mechanic":
        pool = [h for h in houses if h["id"] in MECHANIC_HOUSES
                or (h["class"] == "inn_tavern" and h["id"] not in PROFESSIONAL_HOUSES)]
    else:
        pool = [h for h in houses if h["class"] == "boarding_house"]
    return sorted(pool, key=lambda h: (-(h["beds_ordinary"] - h["occupancy"]), h["id"]))


def house_rows(model: dict, lives: dict, keeps: dict) -> list:
    """One row per BUILT lodging place: its beds, its division, and who is on it already.

    The places the model records with no beds — the Lake House, still a building site on
    the scene date, and Dr Temple's rooms, which the roof programme does not schedule —
    are not rows here. A house that holds nobody cannot be filled to a capacity it does
    not have.
    """
    reconciled = committed_districts()
    rows = []
    for place in model["places"]:
        residents = lives.get(place["id"], [])
        keepers = keeps.get(place["id"], [])
        district = reconciled.get(place["id"])
        division = place.get("division")
        division_from = "the reconstruction programme's own district for this roof"
        if not division:
            divisions = sorted({c.get("division") for c in residents + keepers
                                if c.get("division") in DIVISIONS})
            division = divisions[0] if len(divisions) == 1 else None
            division_from = ("the division of the household the residents layer attaches "
                             "to this house" if division else None)
        if not division and district in DIVISIONS:
            division = district
            division_from = ("the district data/reconstruction/1835_existing_roof_"
                             "reconciliation.json already settles this documented roof "
                             "into (T-1535)")
        rows.append({
            "id": place["id"],
            "name": place["name"],
            "function": place["function"],
            "class": place["class"],
            "standing": place["standing"],
            "division": division,
            "division_from": division_from,
            "district_in_the_roof_reconciliation": district,
            "beds_ordinary": int(place["beds_ordinary"]),
            "beds_crowded": int(place["beds_crowded"]),
            "occupied_before": sum(len(c.get("persons") or []) for c in residents),
            "occupancy": sum(len(c.get("persons") or []) for c in residents),
            "keeper_household": keepers[0]["id"] if keepers else None,
            "keeper_persons": len(keepers[0].get("persons") or []) if keepers else 0,
            "seated": [],
            "minted_keeper": None,
            "minted_lodgers": 0,
            "minted_children": 0,
        })
    return sorted(rows, key=lambda r: r["id"])


def seat_the_solitary(houses: list) -> tuple:
    """Rule 1: the heads the household model already drew as living alone."""
    seats, refused = [], []
    for ticket, stage, path, card in solitary_heads():
        person = (card.get("persons") or [None])[0]
        if person is None:
            continue
        trade = value_of(person.get("occupation"))
        if value_of(card.get("lives_at")):
            refused.append({"person": person["id"], "household": card["id"],
                            "refusal": "the layer already gives this head a roof"})
            continue
        if trade in KEEPER_TRADES:
            refused.append({
                "person": person["id"], "household": card["id"],
                "refusal": "a keeper is not another house's boarder",
                "note": "This head's own trade is keeping a lodging house. Which house "
                        "they kept is a placement question and the division they carry "
                        "is the order book's, which this stage may not move; T-1199 "
                        "seats them."})
            continue
        group = group_of(trade)
        taken = None
        for house in houses_for(group, houses):
            if house["occupancy"] < house["beds_ordinary"]:
                taken = house
                break
        if taken is None:
            refused.append({"person": person["id"], "household": card["id"],
                            "refusal": f"no ordinary-night bed was free in the {group} "
                                       f"group of the mix"})
            continue
        taken["occupancy"] += 1
        taken["seated"].append(person["id"])
        seats.append({
            "person": person["id"],
            "name": person.get("name"),
            "household": card["id"],
            "file": str(path.relative_to(RESIDENTS)),
            "drawn_solitary_by": ticket,
            "drawn_solitary_in_stage": stage,
            "trade": trade,
            "group": group,
            "place": taken["id"],
            "place_name": taken["name"],
            "relationship": RELATION[taken["class"]],
            "basis": {
                "kind": "rule",
                "id": "the_mix_of_the_lodging_model",
                "note": f"The household model drew this head as living alone ({ticket}) "
                        f"and no source gives them a roof. The mix puts a person at "
                        f"{trade or 'no recorded trade'} in the {group} group, and this "
                        f"house had the most free beds in it. A rule, not a draw: the "
                        f"seat reproduces without a seed.",
            },
            "replaceable_by": {
                "kind": "person",
                "match": "a source that says where this person lived on 1 July 1835",
            },
        })
    return seats, refused


# ---------------------------------------------------------------- the drawing --

def community_for(slot_seed: str, pool: dict) -> dict:
    """A lodger carries no trade, so the trade weighting has nothing to say about them:
    the community is drawn from the pools' own `_default`, which is the town's general
    documented stock rather than a story about who did what work."""
    weights = pool["trade_weights"]["_default"]
    by_id = {c["id"]: c for c in pool["communities"]}
    weighted = [(by_id[k], v) for k, v in sorted((weights.get("weights") or {}).items())
                if k in by_id]
    if not weighted:
        weighted = [(by_id["yankee"], 1)]
    return pick(f"{slot_seed}:name_pool_community", weighted)


def step_past(seed: str, names: list, taken: set) -> str:
    """A name from the pool, stepping past one already borne. Deterministic."""
    start = draw(seed) % len(names)
    for offset in range(len(names)):
        candidate = names[(start + offset) % len(names)]
        if candidate.lower() not in taken:
            return candidate
    return names[start]


def band_block(band: str, seed: str) -> dict:
    low, high = BAND_EDGES[band]
    return {
        "value": f"{low}-{high}" if high is not None else f"{low}+",
        "low": low,
        "high": high,
        "confidence": RECONSTRUCTED,
        "tier": RECONSTRUCTED,
        "basis": {
            "kind": "model",
            "id": "1835_reconstruction_order_book",
            "note": f"The bucket that ordered this person is {band}; the band is the "
                    f"order, not a draw. Nothing here is a reading of anybody's age.",
        },
        "seed": seed,
        "replaceable_by": {
            "kind": "person",
            "match": "a source that states this person's age or their birth year",
        },
        "note": "AN AGE BAND, NEVER A YEAR. The order book counts in the 1840 schedule's "
                "bands and this project writes no year it cannot read.",
    }


def name_for(slot_id: str, sex: str, pool: dict, taken_names: set, taken_ids: set) -> tuple:
    """(person id, full name, community). THE WHOLE POOL IS SEARCHED, not one draw and
    one retry: the draw picks where in the two lists to start and the search steps through
    every (surname, forename) pair from there, taking the first whose full name nobody in
    the layer bears and whose id nobody holds."""
    community = community_for(slot_id, pool)
    surnames = community["surnames"]
    givens = community["given_male" if sex == "male" else "given_female"]
    start_s = draw(f"{slot_id}:surname") % len(surnames)
    start_g = draw(f"{slot_id}:forename") % len(givens)
    for ds in range(len(surnames)):
        surname = surnames[(start_s + ds) % len(surnames)]
        for dg in range(len(givens)):
            given = givens[(start_g + dg) % len(givens)]
            full = f"{given} {surname}"
            pid = f"{PREFIX}{surname.lower().replace(' ', '_')}_{given.lower().replace(' ', '_')}"
            if full.lower() in taken_names or pid in taken_ids:
                continue
            return pid, full, community
    raise SystemExit(f"the name pools are exhausted for {slot_id}")


def person_card(slot_id: str, sex: str, band: str, bucket_key: str, place: dict,
                relationship: str, pool: dict, taken_names: set, taken_ids: set,
                keeper: bool = False) -> dict:
    pid, full, community = name_for(slot_id, sex, pool, taken_names, taken_ids)
    taken_names.add(full.lower())
    taken_ids.add(pid)
    person = {
        "id": pid,
        "name": full,
        "relationship": relationship,
        "grade": RECONSTRUCTED,
        "sex": sex,
        "age_band": band_block(band, f"{slot_id}:age_band"),
        "name_basis": {
            "value": full,
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "model",
                "id": "1835_invented_name_pools",
                "note": f"Both parts are drawn from the {community['id']} pool, which is "
                        f"seeded from the attested residents of this town. A lodger "
                        f"carries no trade, so the pools' trade weighting has nothing to "
                        f"say here and the community is drawn from the general stock.",
            },
            "seed": f"{slot_id}:forename",
            "replaceable_by": {
                "kind": "person",
                "match": "a source naming a real person who lodged in this house",
            },
            "note": "AN INVENTED NAME, AND IT IS NEVER EVIDENCE. No source names this "
                    "person. The name exists so a reader can tell one drawn lodger from "
                    "another, and it is checked against every real name in the layer.",
        },
        "basis": {
            "kind": "model",
            "id": "1835_reconstruction_order_book",
            "note": f"The book's bucket {bucket_key} ordered this person: the town "
                    f"model's lodging share, cut by sex, age band and division, less "
                    f"everyone the sources already name there. The bed is "
                    f"{place['id']}'s, from the lodging model's ordinary-night figure "
                    f"of {place['beds_ordinary']}.",
        },
        "seed": f"{slot_id}:forename",
        "replaceable_by": {
            "kind": "person",
            "match": "a source naming a person who lodged in this house, who would take "
                     "this bed instead",
        },
        "reconstruction": {
            "stage": STAGE,
            "programme": PROGRAMME_ID,
            "community": community["id"],
            "review_required": False,
        },
        "resident_subtype": "reconstructed_lodger",
    }
    if keeper:
        trade = KEEPER_TRADE[place["class"]]
        person["occupation"] = {
            "value": trade,
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "rule",
                "id": "the_house_s_own_function",
                "note": f"READ OFF THE BUILDING, NOT DEALT. This roof's record says its "
                        f"function is {place['function']}, and a house of that function "
                        f"was kept by somebody at {trade}. No directory share is "
                        f"consulted and no trade is drawn: the building states the trade "
                        f"and this person is the keeper it implies.",
            },
            "replaceable_by": {
                "kind": "person",
                "match": "a source naming the keeper of this house in 1835",
            },
            "note": "The staffing under a keeper — the bar-keeper, the hostler, the cook, "
                    "the chambermaid — is T-1183's model and is not written here.",
        }
        person["note"] = (
            "RECONSTRUCTED, NOT FOUND. Nobody is named by any source here. This roof is "
            "itself a reconstruction of the 1835 building programme, raised as a lodging "
            "place, and a lodging place with no keeper is not one. The whole of what is "
            "claimed is that: an adult of this sex and band kept this invented house. A "
            "NAMED house is never given a keeper this way — see the tool's refusals. The "
            "family this keeper is owed is not drawn here; `household_owed` says which "
            "ticket owes it. No figure is drawn (L1).")
    else:
        person["occupation"] = {
            "value": "none_recorded",
            "confidence": RECONSTRUCTED,
            "note": "NOT DEALT HERE. The order book's `lodging/trade` buckets want "
                    "working lodgers and this stage does not fill them: dealing a trade "
                    "is T-1173's machinery and the 1839 directory's shares are its "
                    "table. This person carries no trade, the same as the people the "
                    "rosters print without one.",
        }
        person["note"] = (
            f"RECONSTRUCTED, NOT FOUND. Nobody is named by any source here. This person "
            f"exists because the town model says {place['beds_ordinary']} people slept in "
            f"this house on an ordinary night and the layer holds fewer, and the whole of "
            f"what is claimed is that: an adult of this sex and band took a bed here as a "
            f"{relationship}. They are reproducible from the seeds printed above and a "
            f"real name retires them. No figure is drawn (L1).")
    return person


# ------------------------------------------------- the keepers' own children --
#
# T-1533. Refusal 3 below leaves the book's `under_10/*/lodging/none` cells to "the stage
# that completes a keeper's family", and refusal 4 named T-1171 and T-1174 as that stage.
# Neither reaches a keeper THIS stage minted: T-1171 draws families onto the cards in
# `data/residents/households/` and these six keepers are not there, they are invented here
# and live in `data/residents/lodgers/`. So the cells were ordered from nobody.
#
# WHAT IS DRAWN, AND WHAT IS NOT. A keeper's household is drawn at the 1840 size histogram
# — the same table, read through the same module, so two tools cannot size one town two
# ways. The keeper is one of that size and the rest are THEIR CHILDREN. A spouse is not
# drawn, and the reason is not thrift: the sibling stage's spouse rule is written for a
# male head ("a wife older than her husband's decade is the shape the schedule least
# supports"), and three of these six keepers are women. Drawing a husband for Esther
# Bardwell would need a rule this project has not made, and inventing one inside a
# children's ticket is how a model acquires a shape nobody argued for. So the household is
# drawn as ONE PARENT AND THEIR CHILDREN — a FLOOR on the house, never a claim that there
# was no spouse — and the shortfall is stated in the ledger with the cell it would come
# out of.
#
# A CHILD TAKES NO BED. The lodging model's `beds_ordinary` prices the house's LODGERS,
# and the keeper was minted against it; their children are kin under the same roof and are
# counted apart, so `ordinary_night_beds_still_empty` does not move and T-1534 still finds
# the 11 empty beds its own ticket counts. The crowded ceiling is the one figure that
# holds everybody, and `refuse()` asserts it over the roof's whole household.

def household_model():
    """The 1840 household-size histogram and age bands, read through T-1171's own module.

    IMPORTED RATHER THAN RE-READ. `size_histogram_1840` is the table that decides how big
    every reconstructed household in this town is, and a second reader of it here is a
    second place for the kin range, the tail rule and the column names to drift. The
    import is the acceptance condition stated plainly: the count a keeper's card gains is
    the household model's own figure.
    """
    import reconstruct_modelled_families as mf
    return mf


def child_name(slot_id: str, sex: str, surname: str, community: dict,
               taken_names: set, taken_ids: set, family_names: set) -> tuple:
    """(person id, full name), or (None, None) where the pool has nothing left.

    The surname is the keeper's — that is the kinship claim — so a child is confined to
    ONE surname's worth of the pool, which the boarders were not: the Irish pool prints
    eight female forenames and five of them are already borne beside Cavanagh. That is a
    real floor and the caller REFUSES the child on it rather than seating two Ellen
    Cavanaghs under one roof. Inventing a forename to get past it would put a name in this
    town that no pool sourced, which is the one thing the pools exist to prevent.
    """
    givens = community["given_male" if sex == "male" else "given_female"]
    start = draw(f"{slot_id}:forename") % len(givens)
    for offset in range(len(givens)):
        given = givens[(start + offset) % len(givens)]
        full = f"{given} {surname}"
        pid = f"{PREFIX}{surname.lower().replace(' ', '_')}_{given.lower().replace(' ', '_')}"
        if (given.lower() in family_names or full.lower() in taken_names
                or pid in taken_ids):
            continue
        return pid, full
    return None, None


def child_card(slot_id: str, sex: str, bucket_key: str, place: dict, keeper: dict,
               surname: str, community: dict, size: int, index: int, wanted: int,
               cap: int, taken_names: set, taken_ids: set, family_names: set) -> dict:
    pid, full = child_name(slot_id, sex, surname, community, taken_names, taken_ids,
                           family_names)
    if pid is None:
        return None
    taken_names.add(full.lower())
    taken_ids.add(pid)
    family_names.add(full.split(" ", 1)[0].lower())
    return {
        "id": pid,
        "name": full,
        "relationship": "son" if sex == "male" else "daughter",
        "grade": RECONSTRUCTED,
        "sex": sex,
        "age_band": band_block(CHILD_BAND, f"{slot_id}:age_band"),
        "kin_of": {
            "person": keeper["id"],
            "name": keeper["name"],
            "household": f"hh_lodging_{place['id']}",
            "relation": "child of the keeper of this house",
            "note": "THE JOIN IS THE KEEPER, NOT THE BUCKET. This child is written as the "
                    "kin of a named person on a named house and is never a free-standing "
                    "person in a lodging cell: a child took no bed at a tavern on their "
                    "own account, which is the whole reason the boarders stage would not "
                    "draw them.",
        },
        "name_basis": {
            "value": full,
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "model",
                "id": "1835_invented_name_pools",
                "note": f"The surname is the keeper's own, which is the kinship claim. "
                        f"The forename is drawn from the {community['id']} pool — the "
                        f"keeper's own community, carried rather than re-drawn — and it "
                        f"steps past every forename already borne in this family.",
            },
            "seed": f"{slot_id}:forename",
            "replaceable_by": {
                "kind": "person",
                "match": "a source naming a child of this keeper",
            },
            "note": "AN INVENTED NAME, AND IT IS NEVER EVIDENCE. No source names this "
                    "child. The name exists so a reader can tell one drawn child from "
                    "another, and it is checked against every real name in the layer.",
        },
        "basis": {
            "kind": "model",
            "id": "1835_town_model",
            "note": f"The 1840 size histogram drew this keeper's household at {size} "
                    f"people. The keeper is one of them and the other {wanted} are their "
                    f"children; this is child {index} of that {wanted}. The book's bucket "
                    f"{bucket_key} is the cell it is ordered out of — the town model's "
                    f"lodging share for people under ten in the {place['division']} "
                    f"division, which the boarders stage left whole.",
        },
        "seed": f"{slot_id}:age_band",
        "replaceable_by": {
            "kind": "person",
            "match": "a source naming the household of this house's keeper, which would "
                     "retire every child drawn here",
        },
        "reconstruction": {
            "stage": STAGE,
            "ticket": CHILD_TICKET,
            "programme": PROGRAMME_ID,
            "community": community["id"],
            "review_required": False,
        },
        "resident_subtype": "reconstructed_keeper_child",
        "occupation": {
            "value": "none_recorded",
            "confidence": RECONSTRUCTED,
            "note": "A child under ten carries no trade. The book's `lodging/trade` cells "
                    "do not reach this band at all.",
        },
        "note": (
            f"RECONSTRUCTED, NOT FOUND. Nobody is named by any source here. This child "
            f"exists because the household model draws the keeper of this house a "
            f"household of {size} and the card held only the keeper, and the whole of "
            f"what is claimed is that: a child of this sex, under ten, lived with their "
            f"parent in the house that parent kept. The eldest is capped at {cap} years, "
            f"because no child of this house is older than the keeper's own age band "
            f"allows and nobody is born after {SCENE_DATE}. They are reproducible from "
            f"the seeds printed above and a real name retires them. No figure is drawn "
            f"(L1)."),
    }


def keeper_children(cards: dict, houses: list, room: dict, pool: dict,
                    taken_names: set, taken_ids: set) -> tuple:
    """(child fills, the per-house family rows). Mutates `cards` and `room`.

    Runs AFTER every bed is dealt, so the room a child is ordered out of is what the
    boarders left — one quota ledger, spent once, in one tool.
    """
    mf = household_model()
    sizes = mf.size_rows()
    ages = mf.age_rows()
    child_bands = [(r, r[2]) for r in ages if r[1] < 20]
    male_children = sum(r[2] for r in ages if r[0] == "male" and r[1] < 20)
    all_children = sum(r[2] for r in ages if r[1] < 20)
    boy_rate = male_children / float(all_children)
    by_id = {c["id"]: c for c in pool["communities"]}

    fills = Counter()
    families = []
    for house in sorted(houses, key=lambda h: h["id"]):
        if not house["minted_keeper"]:
            continue
        card = cards[f"hh_lodging_{house['id']}"]
        keeper = next(p for p in card["persons"] if p["relationship"] == "head")
        surname = mf.surname_of(keeper["name"])
        community = by_id[keeper["reconstruction"]["community"]]
        head_low = int(keeper["age_band"]["low"])
        family_names = {surname.lower(), keeper["name"].split(" ", 1)[0].lower()}

        size = pick(f"{STAGE}:{house['id']}:household_size", [(s, n) for s, n in sizes])
        wanted = max(0, size - 1)
        # Nobody is born after the scene date and no child is older than the keeper's own
        # age band allows a parent to be — the sibling stage's cap, unchanged.
        cap = min(19, max(0, head_low - 20))
        drawn, refused = [], []
        for index in range(1, wanted + 1):
            slot_id = f"{STAGE}:{house['id']}:child:{index:03d}"
            allowed = [(r, w) for r, w in child_bands if r[1] <= cap]
            if not allowed:
                allowed = [(r, w) for r, w in child_bands if r[1] == 0]
            row = pick(f"{slot_id}:age_bands_1840", allowed)
            if row[1] >= 10:
                refused.append({
                    "child": index,
                    "refusal": "the band the model drew is not this stage's to fill",
                    "band": "10_19",
                    "note": "The household model drew this child into adolescence. The "
                            "book's six `10_19/*/lodging/none` cells are discharged — the "
                            "boarders stage filled 16 of 16 — so there is no order left "
                            "to draw them against, and re-banding a child downward to "
                            "reach a cell that is open would be dealing to the quota "
                            "rather than from the model.",
                })
                continue
            sex = "male" if unit(f"{slot_id}:sex_ratio") < boy_rate else "female"
            at = (house["division"], sex, CHILD_BAND, "none")
            key, left = room[at]
            if left <= 0:
                refused.append({
                    "child": index,
                    "refusal": "the cell is spent",
                    "band": CHILD_BAND,
                    "bucket": key,
                    "note": "The book orders no more people of this sex under ten into "
                            "lodging households in this division. The child the model "
                            "drew is not drawn, and is not moved to another cell to be "
                            "drawn somewhere the book has room.",
                })
                continue
            child = child_card(slot_id, sex, key, house, keeper, surname, community,
                               size, index, wanted, cap, taken_names, taken_ids,
                               family_names)
            if child is None:
                refused.append({
                    "child": index,
                    "refusal": "the name pool holds no forename left for this family",
                    "band": CHILD_BAND,
                    "community": community["id"],
                    "surname": surname,
                    "note": "A child takes the keeper's surname, which confines them to "
                            "one surname's worth of the pool — and the pool for this "
                            "community is short enough that every forename in it is "
                            "already borne beside this surname, by a person the sources "
                            "name or by somebody this programme has already drawn. The "
                            "child is not drawn. Inventing a forename to get past it "
                            "would put a name in this town that no pool sourced, and "
                            "seating a second person of the same name would break the "
                            "one invariant the pools exist for.",
                })
                continue
            card["persons"].append(child)
            drawn.append(child["id"])
            fills[key] += 1
            room[at] = (key, left - 1)

        house["minted_children"] = len(drawn)
        if drawn:
            # THE CARD STOPS SAYING IT HOLDS NO KIN, because it now does. Both sentences
            # were true of a card that held only beds and neither is true of this one; a
            # note left standing beside the thing it denies is worse than no note.
            card["lodging_household"]["minted_here"] = len(card["persons"])
            card["lodging_household"]["note"] = (
                f"BEDS, AND ONE FAMILY. {len(card['persons']) - len(drawn)} of the people "
                f"here took a bed and are not kin to each other or to anybody else under "
                f"this roof — `data/residents/` cannot carry a person outside a "
                f"household, so one record holds them all. The exception is the keeper "
                f"and the {len(drawn)} child(ren) on their card, who are a family and say "
                f"so: every one of them carries `kin_of` naming the keeper.")
        card["household_owed"] = {
            "size_drawn": size,
            "seated_by": (f"{CHILD_TICKET} (the keeper's children, drawn here), "
                          f"T-1179 (converge)"),
            "children_drawn": len(drawn),
            "children_the_model_wants": wanted,
            "note": (f"DRAWN HERE, AND ONLY THE CHILDREN. The 1840 size histogram draws "
                     f"this keeper a household of {size}: the keeper, and {wanted} "
                     f"child(ren) of whom {len(drawn)} could be ordered out of the book's "
                     f"`under_10/{house['division']}/lodging/none` cells. No spouse is "
                     f"drawn — the ledger's `keeper_families` row says why — so this is a "
                     f"FLOOR on the household and not a finished count."),
        }
        families.append({
            "place": house["id"],
            "keeper": keeper["id"],
            "keeper_name": keeper["name"],
            "household_size_drawn": size,
            "seed": f"{STAGE}:{house['id']}:household_size",
            "children_the_model_wants": wanted,
            "children_drawn": len(drawn),
            "children": drawn,
            "refused": refused,
            "spouse_not_drawn": (
                "NOT DRAWN, AND NOT FOR WANT OF A CELL. The sibling stage's spouse rule "
                "is written for a male head — a wife is drawn from the 1840 female adult "
                "columns and never above her husband's decade — and three of this stage's "
                "six keepers are women. A rule for the other direction is not one this "
                "project has made, and making one inside a children's ticket would give "
                "the town a shape nobody argued for. So the household stands at one "
                "parent and their children, which is a FLOOR on the house and not a "
                "claim that this keeper kept no spouse. The cell a spouse would come out "
                f"of is persons/<sex>/<band>/{house['division']}/lodging/none."
                if size >= 2 else
                "The model drew this household at one person, so there is no spouse and "
                "no child to draw: a solitary keeper is a shape the 1840 histogram holds "
                f"{dict(sizes).get(1, 0):,} households of, and this house is one."),
        })
    return dict(sorted(fills.items())), families


def house_card(place: dict, persons: list, seated: list) -> dict:
    keeper = next((p for p in persons if p["relationship"] == "head"), None)
    return {
        "id": f"hh_lodging_{place['id']}",
        "name": f"The lodgers of {place['name']}",
        "division": place["division"] or "unplaced",
        "head": keeper["id"] if keeper else None,
        "source_pass": SOURCE_PASS,
        "lodging_household": {
            "ticket": TICKET,
            "parent_ticket": PARENT,
            "stage": STAGE,
            "place": place["id"],
            "place_name": place["name"],
            "class": place["class"],
            "beds_ordinary": place["beds_ordinary"],
            "beds_crowded": place["beds_crowded"],
            "on_the_house_before_this_stage": place["occupied_before"],
            "seated_from_the_layer": seated,
            "minted_here": len(persons),
            "stands_on": "The lodging model (T-1370) gives this house an ordinary-night "
                         "capacity apportioned out of a figure the town model already "
                         "owns, and the residents layer holds fewer people in it than "
                         "that. The order book's `lodging` buckets are the quota these "
                         "people are drawn against.",
            "withdrawn_if": "a re-cut lodging model that gives this house a smaller "
                            "ordinary-night figure, or sources naming the people who "
                            "actually lodged here; the retirement runs through --build, "
                            "never by hand",
            "note": "A CONTAINER, NOT A FAMILY. `data/residents/` cannot carry a person "
                    "outside a household, and the people who boarded in one house were "
                    "not kin. This record holds the beds of one house and claims no "
                    "relation between the people in them beyond the roof.",
        },
        "household_owed": {
            "size_drawn": None,
            "seated_by": "T-1171 and T-1174 (the keeper's own kin), T-1179 (converge)",
            "note": "NOT DRAWN HERE. Where this house has a keeper, the family they are "
                    "owed is `family/none` in the order book and that quota belongs to "
                    "T-1171 and T-1174; drawing it here would order the same people "
                    "twice. The ledger's `keepers` table states the shortfall instead.",
        },
        "arrival": {
            "value": None,
            "confidence": RECONSTRUCTED,
            "tier": "unknown",
            "note": "NOT DRAWN HERE, AND THE REASON IS A CIRCLE. The arrival model's own "
                    "distribution is computed over the compiled scene and the scene "
                    "carries these cards; an arrival written here would move the table "
                    "that drew it. The programme's arrival stage owns this block.",
            "seated_by": "T-1169 (the arrival fill), T-1179 (converge)",
        },
        "lives_at": {
            "value": place["id"],
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "model",
                "id": "1835_lodging_model",
                "note": f"THE BED IS THE CLAIM. The lodging model puts {place['beds_ordinary']} "
                        f"people in this house on an ordinary night and {place['beds_crowded']} "
                        f"when it was full, apportioned from the town model's own bracket. "
                        f"These people are here because the beds are, and for no other "
                        f"reason.",
            },
            "seed": f"{STAGE}:{place['id']}:lives_at",
            "replaceable_by": {
                "kind": "person",
                "match": "sources naming the people who lodged in this house in 1835",
            },
        },
        "works_at": {
            "value": None,
            "confidence": RECONSTRUCTED,
            "tier": "unknown",
            "note": "Not seated. A lodger's workplace is the business band's (T-1189) "
                    "and a keeper's premises is the house they are already in.",
        },
        "present_on_scene_date": {
            "value": "present",
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "rule",
                "id": "ordered_by_the_reconstruction_order_book",
                "note": "Ordered, not argued: the book counts these people as missing "
                        "FROM the town of 1 July 1835, so presence is the order rather "
                        "than a draw made over it.",
            },
            "replaceable_by": {
                "kind": "person",
                "match": "a re-cut order book that no longer orders these buckets",
            },
        },
        "persons": persons,
        "touches_removal": False,
        "review_required": False,
        "research_note": "WRITTEN BY tools/seat_lodgers_1835.py (T-1371, of T-1175), the "
                         "`lodgers` stage of the 1835 resident reconstruction programme. "
                         "This file is NOT research and is not a mint output: "
                         "data/residents/households/ is re-derived by the mint writers "
                         "and data/residents/index.json is derived from that directory, "
                         "so a reconstruction lives here instead and is overlaid onto the "
                         "scene by tools/compile_scene.py. docs/LIBERTIES.md carries the "
                         "invention.",
    }


# -------------------------------------------------------------------- the fill --

def fill() -> tuple:
    model = lodging_model()
    lives, keeps = occupancy()
    houses = house_rows(model, lives, keeps)
    pool = pools()
    all_names, real_names, ids = layer()
    taken_names = set(all_names)
    taken_ids = set(ids)

    seats, seat_refusals = seat_the_solitary(houses)
    seated_by_house: dict[str, list] = {}
    for seat in seats:
        seated_by_house.setdefault(seat["place"], []).append(seat["person"])

    room = lodging_buckets()
    # THE ROOM AS DEALT, before the loop below spends it. This is what gets committed as
    # the basis, and on every build after the first it is what was read back — see
    # `committed_basis()`.
    room_as_dealt = dict(room)
    live_room = book_lodging_room()
    fills = Counter()
    cards: dict[str, dict] = {}
    refusals = list(seat_refusals)

    # T-1535 — THE HOUSES THE DIVISION REFUSAL USED TO HOLD ARE DEALT LAST, and that
    # ordering is the whole reason lifting the refusal moves nobody. The loop below spends
    # `room` as it goes, so a house inserted ahead of another changes what the second one
    # sees and re-deals people who are already standing in it — the fault T-1503 spent a
    # whole ticket on, where 25 of 56 invented boarders moved and six gate steps went red
    # behind them. Dealt last, every house dealt before T-1535 sees exactly the room it
    # saw before, draws the same cells on the same seeds, and writes the same bytes.
    def dealt_last(house: dict) -> tuple:
        new_to_the_deal = str(house.get("division_from") or "").startswith("the district data")
        return (1 if new_to_the_deal else 0, house["id"])

    for house in sorted(houses, key=dealt_last):
        short = house["beds_ordinary"] - house["occupancy"]
        if short <= 0:
            continue
        if house["division"] not in DIVISIONS:
            refusals.append({
                "place": house["id"],
                "refusal": "no division, no mint",
                "beds_left_empty": short,
                "note": "Nothing this project holds says which division this house "
                        "stood in: the reconstruction programme did not raise it, the "
                        "residents layer attaches no household to it, and "
                        "data/reconstruction/1835_existing_roof_reconciliation.json "
                        "either does not name it or reconciles it into a district that "
                        "is not one of the town's three civil divisions (T-1535). A "
                        "person drawn into a lodging house has to be ordered out of the "
                        "book's bucket for a division, so this stage mints nobody here. "
                        "Somebody the layer already counts may still be seated here, and "
                        "the seats above are.",
            })
            continue
        persons = []
        needed = short
        # THE KEEPER FIRST, and only for a roof this programme raised itself.
        if house["standing"] == RECONSTRUCTED and not house["keeper_household"]:
            weights = [((sex, band), n) for (div, sex, band, axis), (_, n) in sorted(room.items())
                       if div == house["division"] and axis == "trade" and band in ADULT_BANDS and n > 0]
            if weights:
                sex, band = pick(f"{STAGE}:{house['id']}:keeper", weights)
                key = room[(house["division"], sex, band, "trade")][0]
                slot_id = f"{STAGE}:{house['id']}:keeper:001"
                persons.append(person_card(slot_id, sex, band, key, house, "head", pool,
                                           taken_names, taken_ids, keeper=True))
                fills[key] += 1
                room[(house["division"], sex, band, "trade")] = (
                    key, room[(house["division"], sex, band, "trade")][1] - 1)
                house["minted_keeper"] = persons[0]["id"]
                needed -= 1
        weights = [((sex, band), n) for (div, sex, band, axis), (_, n) in sorted(room.items())
                   if div == house["division"] and axis == "none" and band in ADULT_BANDS and n > 0]
        # The ceiling is the BOOK'S OWN, live, less whatever this build has already drawn
        # out of the cell. It binds only where the frozen basis is more generous than the
        # book is today (T-1535's houses are dealt against the remainder, and two of the
        # south cells they weigh on have four slots left and no more); everywhere else
        # `room`'s figure is the smaller of the two and the deal is unchanged.
        capacity = {(sex, band): min(n, live_room.get((house["division"], sex, band, "none"),
                                                      (None, 0))[1]
                                     - fills[room[(house["division"], sex, band, "none")][0]])
                    for (sex, band), n in weights}
        deal, undealt = allocate_within(needed, weights, capacity) if needed > 0 else ({}, 0)
        if undealt:
            refusals.append({
                "place": house["id"],
                "refusal": "no order left, no mint",
                "beds_left_empty": undealt,
                "note": "This house has a division and empty beds, and the order book has "
                        "nothing left to draw them out of: every adult `lodging/none` cell "
                        "of the %s division is filled to what the book orders there. A "
                        "person minted past that would be a person the town never ordered, "
                        "so the beds stand empty and the order rather than the roof is what "
                        "is short (T-1535)." % house["division"],
            })
        index = 0
        for (sex, band), count in sorted(deal.items()):
            key = room[(house["division"], sex, band, "none")][0]
            for _ in range(count):
                index += 1
                slot_id = f"{STAGE}:{house['id']}:{sex}:{band}:{index:03d}"
                persons.append(person_card(slot_id, sex, band, key, house,
                                           RELATION[house["class"]], pool,
                                           taken_names, taken_ids))
                fills[key] += 1
            room[(house["division"], sex, band, "none")] = (
                key, room[(house["division"], sex, band, "none")][1] - count)
        if not persons:
            continue
        house["minted_lodgers"] = len(persons) - (1 if house["minted_keeper"] else 0)
        house["occupancy"] += len(persons)
        card = house_card(house, persons, seated_by_house.get(house["id"], []))
        cards[card["id"]] = card

    # THE KEEPERS' OWN CHILDREN, LAST (T-1533) — after every bed is dealt, so a child is
    # ordered out of the room the boarders left rather than out from under one.
    child_fills, families = keeper_children(cards, houses, room, pool,
                                            taken_names, taken_ids)

    ledger = {
        "$schema_note": "DERIVED. Written by tools/seat_lodgers_1835.py --build; "
                        "re-derived by --check in tools/check.sh. Do not hand-edit.",
        "id": "chicago_july_1835_lodgers_seated",
        "ticket": TICKET,
        "parent_ticket": PARENT,
        "stage": STAGE,
        "target_date": SCENE_DATE,
        "generated_by": "tools/seat_lodgers_1835.py",
        "not_a_reading": "This file reads no source. It spends a capacity the lodging "
                         "model already apportioned and an order the book already made, "
                         "and it names nobody the sources name.",
        "quota_basis": basis_block(room_as_dealt),
        "inputs": [
            "data/reconstruction/1835_lodging_model.json",
            "data/reconstruction/1835_reconstruction_order_book.json",
            "data/reconstruction/1835_modelled_families.json",
            "data/reconstruction/1835_trade_households.json",
            "data/reconstruction/1835_invented_name_pools.json",
            "data/reconstruction/1835_existing_roof_reconciliation.json",
            "data/residents/",
        ],
        "the_mix": {
            "statement": "Professionals and land agents at the Tremont, the Sauganash and "
                         "the Mansion House; mechanics at the Green Tree, the Steamboat "
                         "and the smaller houses; labourers and the people no roster "
                         "gives a trade on the floors of the boarding houses.",
            "from": "T-1175's own rules, quoted",
            "professional_houses": list(PROFESSIONAL_HOUSES),
            "mechanic_houses": list(MECHANIC_HOUSES),
            "everybody_else": "the boarding houses",
            "note": "The first two groups are NAMED HOUSES and not a class test, because "
                    "the ticket names them: the Steamboat Hotel's record says `hotel` and "
                    "the sentence puts it with the mechanics all the same. Within a "
                    "group, the house with the most free beds takes the next person and "
                    "ties break on the id — a rule, not a draw.",
        },
        "houses": [{k: v for k, v in house.items() if k != "occupancy"} | {
            "occupancy_after": house["occupancy"],
            "inside_its_band": house["occupied_before"] <= house["occupancy"] <= house["beds_crowded"],
            "at_its_ordinary_night_figure": house["occupancy"] >= house["beds_ordinary"],
        } for house in houses],
        "seats": seats,
        "minted": sorted(({"id": cid, "file": f"lodgers/{cid}.json",
                           "place": card["lodging_household"]["place"],
                           "persons": len(card["persons"])}
                          for cid, card in cards.items()), key=lambda r: r["id"]),
        "fills": dict(sorted(fills.items())),
        "child_fills": child_fills,
        "keeper_families": {
            "ticket": CHILD_TICKET,
            "statement": "The keepers this stage MINTED, and the household the 1840 size "
                         "histogram draws each of them. A documented keeper is not here: "
                         "their family is T-1171's draw or T-1179's convergence and was "
                         "settled before this stage ran.",
            "read_from": "data/reconstruction/1835_town_model.json, table "
                         "households_and_families/size_histogram_1840, through "
                         "tools/reconstruct_modelled_families.py — the same reader T-1171 "
                         "sizes every other reconstructed household with",
            "the_rule": "The keeper is one of the drawn size and the rest are their "
                        "children. No spouse is drawn: the sibling stage's spouse rule is "
                        "written for a male head and half of these keepers are women, so "
                        "the household stands at one parent and their children — a FLOOR, "
                        "never a claim that a keeper kept no spouse.",
            "a_child_takes_no_bed": "The children are counted apart from the lodging "
                                    "model's `beds_ordinary`, which prices the house's "
                                    "LODGERS. So `ordinary_night_beds_still_empty` does "
                                    "not move and T-1534 still finds the 11 beds it "
                                    "counts. The crowded ceiling holds everybody and "
                                    "`refuse()` asserts it over the whole roof.",
            "houses": families,
        },
        "keepers": keeper_table(houses),
        "refusals": sorted(refusals, key=lambda r: (str(r.get("place") or ""),
                                                    str(r.get("person") or ""))),
        "not_this_piece": {
            "the_crews_and_the_works_gang": "T-1372, piece 3 of this parent: the vessels "
                                            "in port and the hands at the pier works, and "
                                            "the card that prints who lived in a house.",
            "the_unbuilt_boarding_houses": "The lodging model schedules 42 boarding "
                                           "houses and 5 of them stand. The other 37 are "
                                           "333 ordinary beds with no roof over them, and "
                                           "a bed cannot be slept in before it is built: "
                                           "T-1196 re-derives the roof programme and "
                                           "T-1187 raises the houses.",
            "the_staff": "T-1183 models how a business was staffed. The bar-keeper, the "
                         "hostler, the cook and the chambermaid under every keeper here "
                         "are that ticket's, as T-1370 already said.",
            "the_trade_of_a_lodger": "The book's `lodging/trade` buckets are left open. "
                                     "Dealing a trade is T-1173's machinery.",
            "the_children": (
                "PART OF IT NOW IS. The book orders people under ten into lodging "
                "households and they are keepers' families rather than boarders, which is "
                "why refusal 3 would not deal them a bed. "
                f"{CHILD_TICKET} draws the ones this stage can reach: the children of the "
                "keepers this stage itself minted, on the houses it minted them onto, out "
                "of the `under_10/*/lodging/none` cells for those houses' divisions. The "
                "rest are not reachable from here and are not moved: a child of a "
                "DOCUMENTED keeper is T-1171's draw or T-1179's convergence, and the "
                "south division's cells order children into the 37 boarding houses the "
                "lodging model schedules and nobody has built (T-1187 raises them), where "
                "there is no keeper to be kin to. `keeper_families` counts both halves."),
        },
    }
    return cards, ledger


def keeper_table(houses: list) -> list:
    """Every lodging place, its keeper, and who owes the rest of their household.

    THE TITLE OF THIS TICKET SAYS "with each keeper's own household complete" AND THIS
    TABLE IS THE ANSWER IT CAN HONESTLY GIVE. The kin of a household are `family/none` in
    the order book and that quota is T-1171's and T-1174's; drawing them here would order
    the same people twice, which is the one arithmetic the book exists to prevent. So the
    shortfall is STATED, per house, with the ticket that owes it.
    """
    rows = []
    for house in houses:
        if house["keeper_household"]:
            who, count, owed = house["keeper_household"], house["keeper_persons"], None
            if count <= 1:
                owed = ("T-1171 refused this head a drawn family — the eligibility "
                        "refusals are in data/reconstruction/1835_modelled_families.json "
                        "— so the card stands at one person. T-1179 converges it.")
        elif house["minted_keeper"]:
            children = int(house.get("minted_children") or 0)
            who, count = house["minted_keeper"], 1 + children
            owed = (
                f"Minted by this stage as the keeper. {CHILD_TICKET} drew this keeper's "
                f"own children here — {children} of them — out of the book's `under_10` "
                f"lodging cells, at the size the 1840 histogram gives the household. What "
                f"is still owed is a SPOUSE, which no rule this project has made can draw "
                f"for a keeper who is a woman; the ledger's `keeper_families` row states "
                f"it, and the staffing under a keeper is T-1183's."
                if children else
                f"Minted by this stage as the keeper. {CHILD_TICKET} sized this keeper's "
                f"household at the 1840 histogram and it holds no child this stage could "
                f"draw — the ledger's `keeper_families` row says which of the two reasons "
                f"it was: a household the model drew at one, or a child whose cell was "
                f"spent.")
        else:
            who, count, owed = None, 0, (
                "NOBODY KEEPS THIS HOUSE IN THIS DATASET. It is a documented building and "
                "no source this project holds names its keeper on 1 July 1835. A "
                "reconstructed proprietor is not written into a documented house: that is "
                "a research question, not a draw.")
        rows.append({"place": house["id"], "name": house["name"], "keeper": who,
                     "persons_on_the_keeper_s_card": count, "owed_by": owed})
    return rows


# ------------------------------------------------------------- the measurement --

def measurement(cards: dict, ledger: dict) -> dict:
    houses = ledger["houses"]
    minted = sum(len(card["persons"]) for card in cards.values())
    beds = sum(h["beds_ordinary"] for h in houses)
    crowded = sum(h["beds_crowded"] for h in houses)
    before = sum(h["occupied_before"] for h in houses)
    after = sum(h["occupancy_after"] for h in houses)
    ids = [p["id"] for card in cards.values() for p in card["persons"]]
    children = sum(int(h.get("minted_children") or 0) for h in houses)
    families = (ledger.get("keeper_families") or {}).get("houses") or []
    return {
        "built_lodging_places": len(houses),
        "ordinary_night_beds": beds,
        "crowded_beds": crowded,
        "occupied_before_this_stage": before,
        "seated_from_the_layer": len(ledger["seats"]),
        "minted_here": minted - children,
        "minted_keepers": sum(1 for h in houses if h["minted_keeper"]),
        "keeper_children_minted": children,
        "keeper_children_the_model_wanted":
            sum(int(r["children_the_model_wants"]) for r in families),
        "keeper_children_refused": sum(len(r["refused"]) for r in families),
        "people_on_the_cards": minted,
        "occupied_after_this_stage": after,
        "ordinary_night_beds_still_empty": beds - after,
        "houses_at_their_ordinary_night_figure":
            sum(1 for h in houses if h["at_its_ordinary_night_figure"]),
        "houses_over_their_crowded_ceiling":
            sum(1 for h in houses if h["occupancy_after"] > h["beds_crowded"]),
        "nobody_is_seated_twice": len(ids) == len(set(ids)) and len(
            {s["person"] for s in ledger["seats"]}) == len(ledger["seats"]),
        "buckets_filled": len(ledger["fills"]),
        "child_buckets_filled": len(ledger.get("child_fills") or {}),
        "every_child_is_kin_of_a_named_keeper": all(
            p.get("kin_of", {}).get("person")
            and p["kin_of"]["person"] == card["head"]
            for card in cards.values() for p in card["persons"]
            if p["relationship"] in ("son", "daughter")),
        "people_ordered_into_lodging_still_owed": (
            "The book orders 544 people into lodging households. This piece spends "
            f"{minted - children} of them into beds and {children} more as the keepers' "
            "own children; the rest wait on the 37 unbuilt boarding houses, the crews and "
            "the works gang (T-1372), the trades this stage does not deal, and the "
            "children of houses this stage does not keep."),
    }


# --------------------------------------------------------------------- modes --

def write(cards: dict, ledger: dict) -> tuple:
    MINTED.mkdir(parents=True, exist_ok=True)
    written = removed = 0
    want = set(cards)
    for path in sorted(MINTED.glob("hh_*.json")):
        if path.stem not in want:
            path.unlink()
            removed += 1
    for cid, card in sorted(cards.items()):
        (MINTED / f"{cid}.json").write_text(dumps(card), encoding="utf-8")
        written += 1
    return written, removed


def write_fills(ledger: dict) -> None:
    """Carry this stage's fills into the order book and re-derive it. The book's own
    `--build` refuses an overfilled bucket, so the quota is enforced twice."""
    import build_order_book_1835 as ob
    book = load(BOOK)
    ours = (TICKET, CHILD_TICKET)
    kept = [f for f in book.get("fills", []) if f.get("ticket") not in ours]
    kept += [{"bucket": key, "ticket": TICKET, "stage": STAGE, "records": n,
              "by": "tools/seat_lodgers_1835.py --build"}
             for key, n in sorted(ledger["fills"].items())]
    # The children are counted against their OWN ticket, so the book still says which
    # piece of work filled which cell even though one tool wrote both.
    kept += [{"bucket": key, "ticket": CHILD_TICKET, "stage": STAGE, "records": n,
              "by": "tools/seat_lodgers_1835.py --build"}
             for key, n in sorted((ledger.get("child_fills") or {}).items())]
    book["fills"] = kept
    BOOK.write_text(json.dumps(book, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ob.cmd_build()


def build() -> int:
    cards, ledger = fill()
    refuse(cards, ledger)
    written, removed = write(cards, ledger)
    ledger["measurement"] = measurement(cards, ledger)
    LEDGER.write_text(dumps(ledger), encoding="utf-8")
    write_fills(ledger)
    print("  wrote %s" % LEDGER.relative_to(ROOT))
    print("  %d seat(s) from the layer, %d person(s) minted into %d house(s); "
          "%d card(s) written, %d retired"
          % (len(ledger["seats"]), ledger["measurement"]["minted_here"],
             len(cards), written, removed))
    return 0


def refuse_a_recut_under_the_draw(fills: dict, live: dict) -> None:
    """THE FLOOR UNDER THE BASIS (T-1503): a re-cut may not leave this stage's draw
    standing outside the book.

    The committed basis makes the deal immune to a re-cut, and that immunity has to have
    a floor — otherwise a bucket could be re-cut down to nothing while seven invented
    boarders stand on it and nothing in this tool would say so. `no_bucket_overfilled` is
    the book's own invariant over the same arithmetic (T-1166); this is the stage
    asserting it about its own fills, which is the half the book cannot see until its
    counters are carried.
    """
    for key, drew in sorted(fills.items()):
        if key not in live:
            raise SystemExit(
                "  FAIL %s drew %d person(s) out of %s and the book no longer carries "
                "that bucket at all" % (TICKET, drew, key))
        if drew > live[key]:
            raise SystemExit(
                "  FAIL %s drew %d person(s) out of %s and the book now orders only %d "
                "there: a re-cut has taken the order out from under people already "
                "standing" % (TICKET, drew, key, live[key]))


def refuse(cards: dict, ledger: dict) -> None:
    """The assertions that are the point of the stage. Each is a case in --self-test."""
    live = {key: n for key, n in book_lodging_room().values()}
    both = Counter({k: int(v) for k, v in (ledger.get("fills") or {}).items()})
    both.update({k: int(v) for k, v in (ledger.get("child_fills") or {}).items()})
    refuse_a_recut_under_the_draw(dict(both), live)
    for house in ledger["houses"]:
        # THE CEILING HOLDS EVERYBODY UNDER THE ROOF, lodgers and the keeper's children
        # alike. A child takes no ORDINARY-NIGHT bed — that figure prices the lodgers —
        # but they slept in the house, and the crowded figure is what the 1840 enumerator
        # would have counted walking through it.
        under_the_roof = house["occupancy_after"] + int(house.get("minted_children") or 0)
        if under_the_roof > house["beds_crowded"]:
            raise SystemExit(
                "  FAIL %s sleeps %d people and the lodging model's full capacity is %d"
                % (house["id"], under_the_roof, house["beds_crowded"]))
        if house.get("minted_children") and not house["minted_keeper"]:
            raise SystemExit(
                "  FAIL %s was drawn children and this stage keeps no keeper there to be "
                "kin to" % house["id"])
        if house["minted_lodgers"] and house["division"] not in DIVISIONS:
            raise SystemExit("  FAIL %s was minted lodgers with no division to order them "
                             "out of" % house["id"])
        if house["minted_keeper"] and house["standing"] != RECONSTRUCTED:
            raise SystemExit("  FAIL %s is a named house and this stage gave it an "
                             "invented keeper" % house["id"])
    ids = [p["id"] for card in cards.values() for p in card["persons"]]
    ids += [s["person"] for s in ledger["seats"]]
    if len(ids) != len(set(ids)):
        doubled = sorted({i for i in ids if ids.count(i) > 1})[:6]
        raise SystemExit("  FAIL somebody is seated twice: %s" % ", ".join(doubled))
    _, real, _ = layer()
    for card in cards.values():
        for person in card["persons"]:
            if person["name"].lower() in real:
                raise SystemExit("  FAIL the invented name '%s' is borne by a person the "
                                 "sources name" % person["name"])
            if person["relationship"] not in ("son", "daughter"):
                continue
            # A CHILD IS KIN OF A NAMED KEEPER OR IT IS NOT WRITTEN (T-1533's acceptance).
            # A person under ten standing free in a lodging cell is exactly the thing
            # refusal 3 would not draw, and it is one missing field away at every build.
            kin = person.get("kin_of") or {}
            if kin.get("person") != card["head"] or not kin.get("name"):
                raise SystemExit(
                    "  FAIL %s is under ten in %s and is not written as the kin of its "
                    "keeper" % (person["id"], card["id"]))
            if person["age_band"]["high"] is None or person["age_band"]["high"] >= 10:
                raise SystemExit(
                    "  FAIL %s is drawn as a keeper's child and is not under ten"
                    % person["id"])


def check() -> int:
    cards, ledger = fill()
    refuse(cards, ledger)
    ledger["measurement"] = measurement(cards, ledger)
    live = {path.stem: path.read_text(encoding="utf-8")
            for path in sorted(MINTED.glob("hh_*.json"))} if MINTED.exists() else {}
    want = {cid: dumps(card) for cid, card in cards.items()}
    if set(live) != set(want):
        missing = sorted(set(want) - set(live))[:6]
        extra = sorted(set(live) - set(want))[:6]
        print("  FAIL data/residents/lodgers/ is not what this stage derives")
        if missing:
            print("       missing: %s" % ", ".join(missing))
        if extra:
            print("       unexpected: %s" % ", ".join(extra))
        return 1
    for cid in sorted(want):
        if live[cid] != want[cid]:
            print("  FAIL %s has drifted from its derivation" % cid)
            return 1
    if not LEDGER.exists() or LEDGER.read_text(encoding="utf-8") != dumps(ledger):
        print("  FAIL %s has drifted from its derivation" % LEDGER.relative_to(ROOT))
        return 1
    book = load(BOOK)
    for ticket, want_fills in ((TICKET, ledger["fills"]),
                               (CHILD_TICKET, ledger.get("child_fills") or {})):
        ours = {f["bucket"]: int(f["records"]) for f in book.get("fills", [])
                if f.get("ticket") == ticket}
        if ours != dict(want_fills):
            print("  FAIL the order book's fills for %s are not this stage's ledger"
                  % ticket)
            return 1
    m = ledger["measurement"]
    if m["houses_over_their_crowded_ceiling"]:
        print("  FAIL a house sleeps more than the 1840 enumerator ever saw")
        return 1
    if not m["nobody_is_seated_twice"]:
        print("  FAIL somebody is seated twice")
        return 1
    if not m["every_child_is_kin_of_a_named_keeper"]:
        print("  FAIL a person under ten stands free in a lodging cell")
        return 1
    print("  ok    %d lodging place(s); %d bed(s) filled, %d still empty and every one of "
          "them said; %d child(ren) on %d keeper's card(s)"
          % (m["built_lodging_places"],
             m["occupied_after_this_stage"] - m["occupied_before_this_stage"],
             m["ordinary_night_beds_still_empty"], m["keeper_children_minted"],
             m["minted_keepers"]))
    return 0


def report() -> int:
    cards, ledger = fill()
    ledger["measurement"] = measurement(cards, ledger)
    print("THE BEDS OF 1 JULY 1835 — %s, stage `%s`" % (TICKET, STAGE))
    print()
    print("  %-30s %5s %5s %5s %5s %5s  %s" % ("house", "ord", "full", "was", "seat",
                                               "mint", "division"))
    for house in ledger["houses"]:
        print("  %-30s %5d %5d %5d %5d %5d  %s"
              % (house["id"][:30], house["beds_ordinary"], house["beds_crowded"],
                 house["occupied_before"], len(house["seated"]),
                 house["minted_lodgers"] + (1 if house["minted_keeper"] else 0),
                 house["division"] or "— not stated by anything this project holds"))
    print()
    for seat in ledger["seats"]:
        print("  seated  %-28s %-22s %s" % (seat["person"][:28], seat["place"],
                                            seat["group"]))
    print()
    for refusal in ledger["refusals"]:
        print("  refused %-28s %s" % (str(refusal.get("place") or refusal.get("person"))[:28],
                                      refusal["refusal"]))
    print()
    for key, value in ledger["measurement"].items():
        print("  %-46s %s" % (key, value))
    return 0


# ------------------------------------------------------------------ self-test --

def self_test() -> int:
    cases, failures = 0, 0

    def case(name: str, ok: bool):
        nonlocal cases, failures
        cases += 1
        if ok:
            print("  ok    %s" % name)
        else:
            failures += 1
            print("  FAIL  %s" % name)

    cards, ledger = fill()
    ledger["measurement"] = measurement(cards, ledger)

    # 1. A house pushed past the lodging model's full capacity is refused.
    broken = json.loads(json.dumps(ledger))
    broken["houses"][0]["occupancy_after"] = broken["houses"][0]["beds_crowded"] + 1
    try:
        refuse(cards, broken)
        case("a house over its crowded ceiling is refused", False)
    except SystemExit:
        case("a house over its crowded ceiling is refused", True)

    # 2. A person seated twice is refused.
    broken = json.loads(json.dumps(ledger))
    if broken["seats"]:
        broken["seats"].append(broken["seats"][0])
        try:
            refuse(cards, broken)
            case("a person seated twice is refused", False)
        except SystemExit:
            case("a person seated twice is refused", True)
    else:
        case("a person seated twice is refused (no seats to double)", False)

    # 3. An invented name that a real person bears is refused.
    broken_cards = json.loads(json.dumps(cards))
    _, real, _ = layer()
    a_real_name = sorted(real)[0] if real else None
    first = sorted(broken_cards)[0]
    broken_cards[first]["persons"][0]["name"] = a_real_name.title()
    try:
        refuse(broken_cards, ledger)
        case("an invented name a real person bears is refused", False)
    except SystemExit:
        case("an invented name a real person bears is refused", True)

    # 4. A house whose division nothing states mints nobody, and says so. Since T-1535
    #    resolved both houses that used to stand here live, the case is MADE rather than
    #    observed: a house is asked for with every division source silent, and the answer
    #    has to be a refusal by name with its empty beds counted. The live half still
    #    holds too — whatever this stage refuses today, it minted nobody into.
    divisionless = [h for h in ledger["houses"] if h["division"] not in DIVISIONS]
    said = {r.get("place") for r in ledger["refusals"] if r["refusal"] == "no division, no mint"}
    case("what this stage refuses for want of a division mints nobody",
         all(h["minted_lodgers"] == 0 and h["minted_keeper"] is None for h in divisionless)
         and {h["id"] for h in divisionless} == said)

    silent = house_rows({"places": [{"id": "a_house_nothing_places", "name": "A house "
                                     "nothing places", "function": "tavern_inn",
                                     "class": "inn_tavern", "standing": "named",
                                     "beds_ordinary": 6, "beds_crowded": 12}]}, {}, {})
    case("a house every division source is silent about resolves to no division",
         len(silent) == 1 and silent[0]["division"] is None
         and silent[0]["district_in_the_roof_reconciliation"] is None)

    fort = house_rows({"places": [{"id": "fort_dearborn_big_barn", "name": "A roof on "
                                   "the reservation", "function": "tavern_inn",
                                   "class": "inn_tavern", "standing": "named",
                                   "beds_ordinary": 6, "beds_crowded": 12}]}, {}, {})
    case("a roof reconciled into the fort district is not given a civil division",
         len(fort) == 1 and fort[0]["division"] is None
         and fort[0]["district_in_the_roof_reconciliation"] == "fort")

    # 4b. T-1535's own source is read LAST, so a house a household already places keeps
    #     the division it has even where the reconciliation disagrees — `western_hotel`
    #     is south to the people living in it and west to the reconciliation, and it is
    #     the reason the order matters rather than a hypothetical.
    disagree = [h for h in ledger["houses"]
                if h["district_in_the_roof_reconciliation"] in DIVISIONS
                and h["division"] in DIVISIONS
                and h["district_in_the_roof_reconciliation"] != h["division"]]
    case("a division read off the layer is not overturned by the reconciliation",
         all(h["division_from"].startswith("the division of the household") for h in disagree))

    # 5. A named house is never given an invented keeper.
    case("only a roof this programme raised is given a keeper",
         all(h["standing"] == RECONSTRUCTED for h in ledger["houses"] if h["minted_keeper"]))

    # 6. The mix sends a professional to a professional house.
    case("the mix sends a professional trade to the ticket's own named houses",
         all(s["place"] in PROFESSIONAL_HOUSES for s in ledger["seats"]
             if s["group"] == "professional"))

    # 7. No lodger is minted under ten. A keeper's CHILD is under ten by construction and
    #    is not a lodger — the test is on the people who took a bed.
    bands = {p["age_band"]["value"] for card in cards.values() for p in card["persons"]
             if p["relationship"] not in ("son", "daughter")}
    case("no lodger is drawn under ten",
         all(band in {band_block(b, "x")["value"] for b in ADULT_BANDS} for band in bands))

    # 8. No trade is dealt onto a lodger.
    trades = {(p["occupation"] or {}).get("value") for card in cards.values()
              for p in card["persons"] if p["relationship"] != "head"}
    case("no lodger is dealt a trade", trades <= {"none_recorded"})

    # 9. Every keeper's shortfall is stated rather than drawn.
    case("every lodging place's keeper row says who owes the rest of the household",
         len(ledger["keepers"]) == len(ledger["houses"])
         and all(row["keeper"] is None or row["owed_by"] is not None
                 or row["persons_on_the_keeper_s_card"] > 1
                 for row in ledger["keepers"]))

    # 9b. T-1533: every child is kin of a named keeper, and the gate fires when one is not.
    kids = [(cid, p) for cid, card in cards.items() for p in card["persons"]
            if p["relationship"] in ("son", "daughter")]
    case("every child drawn is the kin of a named keeper on a named house",
         bool(kids) and all(p["kin_of"]["person"] == cards[cid]["head"]
                            and p["kin_of"]["name"] for cid, p in kids))
    broken_cards = json.loads(json.dumps(cards))
    a_card = next(c for c in broken_cards.values()
                  if any(p["relationship"] in ("son", "daughter") for p in c["persons"]))
    for p in a_card["persons"]:
        if p["relationship"] in ("son", "daughter"):
            p.pop("kin_of")
            break
    try:
        refuse(broken_cards, ledger)
        case("a child standing free in a lodging cell is refused", False)
    except SystemExit:
        case("a child standing free in a lodging cell is refused", True)

    # 9c. The children come out of the book's `under_10` lodging cells and no other, and
    #     they are counted against their own ticket rather than the boarders'.
    case("every child is ordered out of an `under_10` lodging cell",
         bool(ledger["child_fills"])
         and all("/under_10/" in key and key.endswith("/lodging/none")
                 for key in ledger["child_fills"])
         and sum(ledger["child_fills"].values())
         == ledger["measurement"]["keeper_children_minted"])

    # 9d. A child takes no ordinary-night bed: the beds the boarders left stand where they
    #     stood, which is the figure T-1534's own ticket counts.
    case("drawing the children moves no bed",
         ledger["measurement"]["ordinary_night_beds_still_empty"]
         == ledger["measurement"]["ordinary_night_beds"]
         - ledger["measurement"]["occupied_after_this_stage"])

    # 9e. Every house the model wanted children for says what became of each one.
    rows = ledger["keeper_families"]["houses"]
    case("every child the model wanted is either drawn or refused in writing",
         bool(rows) and all(r["children_the_model_wants"]
                            == r["children_drawn"] + len(r["refused"]) for r in rows)
         and all(r["refused"] == [] or all(x.get("note") for x in r["refused"])
                 for r in rows))

    # 10. The draw reproduces.
    again, _ = fill()
    case("two builds over one layer write the same bytes",
         {k: dumps(v) for k, v in cards.items()} == {k: dumps(v) for k, v in again.items()})

    # 11. THE DEMONSTRATION T-1503 EXISTS FOR. The book is re-cut in a throwaway copy —
    # one undrawn slot out of every lodging bucket that has one — and the deal is
    # re-derived against it. Not one card may move.
    global BOOK
    original, perturbed, touched, moved_buckets = BOOK, load(BOOK), 0, set()
    for family in perturbed.get("bucket_families", []):
        if family.get("key") != "persons":
            continue
        for bucket in family.get("buckets", []):
            if bucket["axes"].get("household_type") != "lodging":
                continue
            if (bucket.get("to_reconstruct") or 0) - (bucket.get("filled") or 0) > 0:
                bucket["to_reconstruct"] -= 1
                moved_buckets.add(bucket["key"])
                touched += 1
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "1835_reconstruction_order_book.json"
        path.write_text(json.dumps(perturbed, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        BOOK = path
        try:
            recut_cards, recut_ledger = fill()
        finally:
            BOOK = original
    case("a re-cut of the book moves nobody this stage has already dealt",
         touched > 0 and {k: dumps(v) for k, v in cards.items()}
         == {k: dumps(v) for k, v in recut_cards.items()})

    # 12. And the re-cut is not absorbed in silence: it is stated, bucket by bucket. The
    # expected set is every bucket whose live figure now differs from the basis, which is
    # the buckets perturbed above PLUS the ones the committed book has already re-cut.
    basis_now = {row["bucket"]: int(row["to_reconstruct"])
                 for row in ledger["quota_basis"]["buckets"]}
    live_perturbed = {b["key"]: int(b.get("to_reconstruct") or 0)
                      for fam in perturbed.get("bucket_families", [])
                      if fam.get("key") == "persons"
                      for b in fam.get("buckets", [])
                      if b["axes"].get("household_type") == "lodging"}
    want_stated = {key for key, n in basis_now.items()
                   if key in live_perturbed and live_perturbed[key] != n}
    case("a re-cut the basis stands against is stated in `re_cut_since`",
         touched > 0 and bool(moved_buckets) and want_stated == {
             row["bucket"]
             for row in recut_ledger["quota_basis"]["re_cut_since"]["the_book_moved"]})

    # 13. The basis the ledger commits is read back as the same room, which is what makes
    # a second build a fixed point rather than a drift.
    rows = ledger["quota_basis"]["buckets"]
    reread = {(r["division"], r["sex"], r["age_band"], r["trade"]):
              (r["bucket"], int(r["to_reconstruct"])) for r in rows}
    case("the committed basis is read back as the room the deal was dealt against",
         bool(reread) and reread == lodging_buckets())

    # 14. A re-cut that falls BELOW what this stage drew is refused — the floor.
    fills_now = {k: int(v) for k, v in ledger["fills"].items()}
    live_now = {key: n for key, n in book_lodging_room().values()}
    a_bucket = sorted(fills_now)[0]
    try:
        refuse_a_recut_under_the_draw(
            fills_now, live_now | {a_bucket: fills_now[a_bucket] - 1})
        case("a bucket re-cut below its own draw is refused", False)
    except SystemExit:
        case("a bucket re-cut below its own draw is refused", True)

    # 15. And a bucket dropped from under a fill is refused rather than ignored.
    try:
        refuse_a_recut_under_the_draw(
            fills_now, {k: v for k, v in live_now.items() if k != a_bucket})
        case("a bucket dropped from under a fill is refused", False)
    except SystemExit:
        case("a bucket dropped from under a fill is refused", True)

    print("  %d case(s), %d failure(s)" % (cases, failures))
    return 1 if failures else 0


def main(argv) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.build:
        return build()
    if args.check:
        return check()
    if args.report:
        return report()
    if args.self_test:
        return self_test()
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
