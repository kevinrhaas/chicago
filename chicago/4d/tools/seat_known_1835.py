#!/usr/bin/env python3
"""The address book: where every known household and firm stands, at the rung its
evidence reaches — and, where the evidence does not reach a seat, what it DOES reach
and who owes the seat.

    tools/seat_known_1835.py --build      write the address book
    tools/seat_known_1835.py --check      re-derive, diff, re-assert every limit
    tools/seat_known_1835.py --self-test  break the assertions and require them to fire
    tools/seat_known_1835.py --report     print the counts

WHAT THIS IS FOR.

T-1198 asked for one row per household and per business, each seated at the first rung
of a six-rung ladder that fires:

    1  structure       a named roof
    2  lot             an address, a corner ordinal, a lot-and-block line
    3  face            a street and nothing narrower, housed on a block face
    4  division_band   a division from the evidence, banded by the placement policy
    5  policy_only     nothing in the evidence; the policy's band by class alone
    6  unplaceable     the evidence CONTRADICTS every band

It is more than three runs of work, so it was split (T-1491/T-1492/T-1493, and T-1492
again into T-1512/T-1513). **T-1491 wrote only the rungs the committed evidence already
reaches** — 1, 3 for the adopted firms, and 6 — recorded rung 2 as **measured empty**,
and for every other row wrote down the REACH, the narrowest thing the evidence actually
gives, with `seat: null` and the ticket that owed the seat.

**T-1512 seats the two reconstructed rungs the EVIDENCE still bounds**, and only those:

  * **rung 3, for the 21 street-only firms the face adoption refused.** The paper names
    a platted street and no roof on it was free. They stand on the FACE of that street —
    `seat.kind: street_face` — with no roof, no lot and no coordinate. The street is the
    evidence and keeps its tier; standing them on the face without a roof is the
    reconstructed step, and the row says so.
  * **rung 4, for every household whose own record names a division.** The division is
    the evidence; the BAND inside it is this pass's reconstruction, and it is the
    placement policy's own clause for the head's trade. Where no clause of the policy
    reaches that trade — `occupation: none_recorded`, and the trades the policy has no
    dwelling clause for — the band is the division's own ground and nothing narrower,
    and the row says that rather than dealing a class the record does not carry.

**T-1522 deals rung 5**, the last rung with rows in it. 1,186 households carry no division
at all — no roof, no street, no division, nothing but a name — and until now they stood
`owed`. Banding them means dealing a division AND a class no source gives, and both are
dealt here from committed models rather than guessed:

  * **the division, from the reconstruction order book's own household shape.** The book
    states a per-division household target — south 367, north 145, west 131 — and those
    three numbers ARE the town's household distribution as this project holds it. The
    deal is the book's shape and nothing of this file's own invention. The fort is not in
    it: the garrison's households are T-1176's and the book gives that bucket no target,
    so a household no source places is never dealt into the reservation.
  * **the class, from the town model's own employment distribution.** The model's
    `employment_shape_1840` table carries the 1840 schedule's seven industry columns as
    shares of the employed. Each column is mapped to the placement-policy clause the
    COMMITTED `TRADE_CLAUSE` table above already gives a trade of that column — so the
    mapping restates an adjudication this project has made rather than making a new one.
    Mining is REFUSED: the town has no mine, the column is 2 persons of 870, and its
    share is renormalised away rather than banded into something it is not.

Both deals are EXACT, not sampled. Households are ordered by a seeded digest of their own
id and the quota for each division and each clause is dealt off that order by largest
remainder, so the dealt totals are the committed shape to the person and a re-run gives
the same answer. A rung-5 row carries the digest that placed it.

**What rung 5 does NOT do, and T-1523 owes.** The division dealt here is written in the
address book and nowhere else. It is not carried back onto the household card or onto
`data/residents/index.json`, so those still read `unplaced` and the People view's division
filter is still short of these 1,186. That carry-back is T-1523.

No coordinate is invented by this file, no household record is written to by it, and the
division on a rung-4 seat is always the one the household's own card already carries. A
rung-5 division is the only division in this file that no household record carries, and
every row that has one says so in its own words.

THE ONE THING THIS FILE IS NOT.

It is not a second opinion on anything already adjudicated. The business half is a
strict restatement of `data/research/location_spend.json` (T-1239): assertion 4 fails if
a single firm's rung stops agreeing with the grade that file gives it, and assertion 5
fails if the 62 unplaceable firms are not the same 62. The household half is read from
the committed household records and from nothing else — `lives_at` is the seat, and a
household whose record names no roof gets no roof here.

WHAT A ROW SAYS, AND WHY EACH FIELD IS THERE.

    rung          the rung that fired: structure | lot | face | division_band |
                  unplaceable | owed
    seat          the thing it stands on, or null. NEVER set on an `owed` row. A seat
                  carries its own `kind`: structure, street_face or division_band —
                  and only a `structure` seat names a building this dataset holds.
    reach         what the evidence narrows to: structure | structure_owed | lot |
                  face | division | none
    reach_value   the street or the division the reach names, where it names one
    tier          the confidence the seat carries, from the record that made it
    basis         the clause or rule the seat rests on, in the words of its own source
    words         the sentence the household card shows a visitor
    replaceable_by  what would move this row UP the ladder
    owed_to       the ticket that owes the seat, on an `owed` row
    dealt_roof    where the PLACEMENT POLICY put them, or null. Not a rung, and it
                  never touches one (T-1618): the ladder says what the evidence
                  reaches and this says what this project decided, carried in from
                  the two committed seats files T-1613 and T-1614 wrote. 178 rows
                  carry one; 172 of those name a roof this scene raises, and the
                  remaining six carry a slot the policy REQUESTED and name who
                  builds it.

`words` is the point of the whole file. Before it, 1,186 household cards said "No known
address" and stopped, which reads as an absence in the town rather than an absence in the
record. A visitor is owed the difference between "nobody wrote down where they lived",
"the paper names their street and no more" and "the evidence puts them outside the town",
and those are three different sentences.

THE DEAL IS CARRIED, AND IT IS NOT A RUNG (T-1618).

For a reconstructed household the ladder tops out at a band, by definition: no source
names their roof, which is why they are reconstructed. So the button that takes a
visitor to a card's seat could never fire for them, and 172 of them had a roof standing
in the scene the whole time — dealt by T-1613 onto the plat's lots and by T-1614 onto
the ground the plat does not draw. `dealt_roof` carries that deal onto the row so the
card can offer it. Assertion 16 holds the separation: the rung, the seat, the tier and
the words of the ladder are untouched, the roof is marked substitutable, and the verb
on the button names the POLICY. Arriving somewhere must not be mistakable for the
record having put the household there.

THE RUNG-2 CLAIM IS MEASURED, NOT ASSUMED.

`data/research/newspapers/lot_addresses.json` is the whole of this project's lot-and-block
evidence and it carries ONE address — G. Spring's dwelling-house on lot 7 of block 16 —
which names no household and no firm. So rung 2 stands empty, and assertion 7 re-reads the
ledger on every run: the day a second lot address arrives naming somebody, the gate fails
here rather than the rung quietly staying empty.
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HOUSEHOLDS = ROOT / "data" / "residents" / "households"
INDEX = ROOT / "data" / "residents" / "index.json"
SPEND = ROOT / "data" / "research" / "location_spend.json"
LOT_ADDRESSES = ROOT / "data" / "research" / "newspapers" / "lot_addresses.json"
BUSINESSES = ROOT / "data" / "businesses"
STRUCTURES = ROOT / "data" / "structures"

OUT = ROOT / "data" / "reconstruction" / "1835_address_book.json"

POLICY = ROOT / "data" / "reconstruction" / "1835_placement_policy.json"
ORDER_BOOK = ROOT / "data" / "reconstruction" / "1835_reconstruction_order_book.json"
TOWN_MODEL = ROOT / "data" / "reconstruction" / "1835_town_model.json"

SCENE_DATE = "1835-07-01"
TICKET = "T-1618"
TICKETS = ["T-1491", "T-1512", "T-1522", "T-1618"]

# Who owes the seat a row does not have. A roof the paper reaches but the town has not
# raised is owed to the district build tickets. Rung 5 is no longer owed to anybody: it is
# dealt below, and the only thing still outstanding for those rows is the CARRY-BACK of
# the dealt division onto the household record, which is T-1523 and is not a seat.
# T-1523 CARRIED THE DEAL BACK, so this is no longer a debt: the constant names the
# ticket that SPENT it, and assertion 15 below holds `still_owed_to` at None. It is
# kept as a name rather than deleted because the `owed` rung still points business
# rows at the ticket that owes them a seat, and two of the self-tests below use it.
OWED_CARRY_BACK = "T-1523"
CARRIED_BACK_BY = "T-1523"
OWED_BUILD = "T-1200..T-1209"

# ---- the dealt roof (T-1618) ---------------------------------------------- #
#
# THE LADDER SAYS WHERE THE EVIDENCE REACHES. IT HAS NEVER SAID WHERE THE POLICY PUT
# THEM. T-1613 and T-1614 dealt the reconstructed households onto the ground — the
# plat's 226 lots first, then the ground the plat does not draw — and wrote the deal
# into two committed files. Until this pass it lived only there: 1,691 cards carried a
# band, 172 of them had a roof standing under them in the scene, and not one of those
# 172 could be walked to. The whole reason `seat.js` exists is that the weaker rungs
# are the ones a visitor most needs SHOWN, and those 172 were the weakest rungs of all.
#
# SO THE DEAL IS CARRIED ONTO THE ROW, AND IT IS NOT A RUNG. `dealt_roof` sits BESIDE
# `seat`; the rung, the seat, the tier and the words of the ladder are untouched and
# assertion 16 refuses a pass that moves any of them. That separation is the whole
# design: the row still says the record reaches nothing, and the card now also says
# which roof the policy dealt them and offers to take you there. Arriving somewhere
# must never be mistakable for the record having put the house there, which is why the
# verb on the button names the POLICY and the words under it say the roof is
# substitutable.
#
# A `slot` deal names no roof: the policy found the block's own committed plan had
# headroom and REQUESTED one. Nobody can be taken to a building that is not built, so
# a slot row carries the deal, says the roof is owed, and offers no button.
PLATTED_SEATS = ROOT / "data" / "reconstruction" / "1835_platted_seats.json"
OFF_PLAT_SEATS = ROOT / "data" / "reconstruction" / "1835_off_plat_seats.json"

# The two files, and the ticket that dealt each. The ground word is the file's own:
# a platted lot is a unit of Thompson's plan, an off-plat parcel is a tier lot, a
# survey chip, a block of an addition or the open ground of a camp.
DEALT_SEAT_FILES = (
    (PLATTED_SEATS, "T-1613", "platted_lot"),
    (OFF_PLAT_SEATS, "T-1614", "off_plat_parcel"),
)

# Who owes the six roofs the deal requested and did not find standing. The seats file
# says it in its own words on every one of them; this is the same debt, named once.
OWED_SLOT_BUILD = "T-1200..T-1214"

# The business grade -> (rung, reach, owed_to). A strict restatement of T-1239's
# adjudication; assertion 4 refuses any drift between this table and that file.
# `street_only_unseated` moved from `owed` to rung 3 in T-1512: the face adoption could
# not find the firm a free ROOF, which is not the same as not finding it a FACE.
FROM_GRADE = {
    "structure_committed": ("structure", "structure", None),
    "structure_pending": ("owed", "structure_owed", OWED_BUILD),
    "street_only_adopted": ("face", "face", None),
    "street_only_unseated": ("face", "face", None),
    "unplaceable": ("unplaceable", "none", None),
}

# ---- the band vocabulary (T-1512) ------------------------------------------ #
#
# A BAND IS AN ADJUDICATION OVER THE COMMITTED PLACEMENT POLICY, NOT A NEW READING.
# `data/reconstruction/1835_placement_policy.json` states twelve clauses, each one
# addressed to a set of ROOF FAMILY letters. A household is not a roof family, so the
# one thing this table does is say which clause a head's trade puts the household under
# — and it says it for the trades the policy's dwelling clauses actually reach, and for
# no others. Everything unlisted falls to `division_ground` below, which asserts nothing
# beyond the division the card already carries.
#
# Every value here is a clause id of that file. Assertion 9 refuses one that is not.
TRADE_CLAUSE = {
    # merchant_and_professional_dwellings (H1, H2, D7) — "the better houses take the
    # Randolph-Washington tier a block back from the trade, and the north tier under
    # Kinzie". The merchants and the professions the town's own register names.
    "merchant": "merchant_and_professional_dwellings",
    "lumber_merchant": "merchant_and_professional_dwellings",
    "forwarding_and_commission": "merchant_and_professional_dwellings",
    "clothier": "merchant_and_professional_dwellings",
    "druggist": "merchant_and_professional_dwellings",
    "grocer": "merchant_and_professional_dwellings",
    "auctioneer": "merchant_and_professional_dwellings",
    "attorney": "merchant_and_professional_dwellings",
    "physician": "merchant_and_professional_dwellings",
    "editor": "merchant_and_professional_dwellings",
    "surveyor": "merchant_and_professional_dwellings",
    "speculator": "merchant_and_professional_dwellings",
    "banker": "merchant_and_professional_dwellings",
    "land_agent": "merchant_and_professional_dwellings",
    # tradesman_dwellings (D3-D6) — "the frame cottages fall on the side streets behind
    # the principal frontages". The crafts that keep a shop and a cottage.
    "blacksmith": "tradesman_dwellings",
    "carpenter": "tradesman_dwellings",
    "ship_carpenter": "tradesman_dwellings",
    "mason": "tradesman_dwellings",
    "plasterer": "tradesman_dwellings",
    "painter": "tradesman_dwellings",
    "brickmaker": "tradesman_dwellings",
    "printer": "tradesman_dwellings",
    "watchmaker": "tradesman_dwellings",
    "silversmith": "tradesman_dwellings",
    "gunsmith": "tradesman_dwellings",
    "cooper": "tradesman_dwellings",
    "cabinetmaker": "tradesman_dwellings",
    "wheelwright": "tradesman_dwellings",
    "saddler": "tradesman_dwellings",
    "shoemaker": "tradesman_dwellings",
    "tailor": "tradesman_dwellings",
    "hatter": "tradesman_dwellings",
    "baker": "tradesman_dwellings",
    "butcher": "tradesman_dwellings",
    "barber_surgeon": "tradesman_dwellings",
    "dressmaker": "tradesman_dwellings",
    "milliner": "tradesman_dwellings",
    # labourer_dwellings (D1, D2) — "cabins and shanties take the small lots, the
    # fringes and the ground nobody is bidding on".
    "labourer": "labourer_dwellings",
    "laundress": "labourer_dwellings",
    "domestic": "labourer_dwellings",
    "servant": "labourer_dwellings",
    "cook": "labourer_dwellings",
    "teamster": "labourer_dwellings",
    "carter": "labourer_dwellings",
    "boatman": "labourer_dwellings",
    "sailor": "labourer_dwellings",
    # heavy_and_noxious_trades (W5) — "packing, tanning, slaughtering and soap-boiling
    # go to the branches and out of the town's nose".
    "packer": "heavy_and_noxious_trades",
    "tanner": "heavy_and_noxious_trades",
    "slaughterer": "heavy_and_noxious_trades",
    "soap_boiler": "heavy_and_noxious_trades",
    # lodging_near_the_landings (T1-T3, H3) — "an inn stands where the traveller
    # arrives".
    "tavern_keeper": "lodging_near_the_landings",
    "innkeeper": "lodging_near_the_landings",
    "boarding_house_keeper": "lodging_near_the_landings",
    # garrison_reservation (M1) — the military reservation, unplatted, no street.
    "soldier": "garrison_reservation",
}

# The band a household falls to when no clause of the policy reaches its head's trade.
# It is NOT a clause and it is not pretending to be one: it names the division the card
# already carries and stops there.
DIVISION_GROUND = "division_ground"

# The divisions the town holds. `outside_town` is rung 6 and not a band: the evidence
# does not fail to place these households, it places them somewhere else.
TOWN_DIVISIONS = ("south", "west", "north", "fort")


# ---- the rung-5 deal (T-1522) ---------------------------------------------- #
#
# THE CLASS COMES OUT OF A COMMITTED ADJUDICATION, NOT OUT OF THIS FILE.
# `data/reconstruction/1835_town_model.json` carries the 1840 schedule's seven industry
# columns as shares of the employed, and that is the only occupation distribution this
# project holds for the town as a whole. A column is not a placement-policy clause, so
# each one is mapped to the clause `TRADE_CLAUSE` above ALREADY gives a trade of that
# column — the trade named in the comment is the proof that the mapping restates a
# decision this project has made, rather than making a new one here.
#
# A column mapped to None is REFUSED: it orders no band at all and its share is
# renormalised away. That is the order book's own `an_uncompared_class_orders_nothing`
# rule applied to a distribution instead of a bucket.
COLUMN_CLAUSE = {
    # `merchant` and `grocer` are commerce, and TRADE_CLAUSE bands both here.
    "Commerce": "merchant_and_professional_dwellings",
    # `attorney`, `physician`, `surveyor` — TRADE_CLAUSE bands the professions here.
    "Learned professions and engineers": "merchant_and_professional_dwellings",
    # `blacksmith`, `carpenter`, `shoemaker` — the crafts, banded to the side streets.
    "Manufactures and trades": "tradesman_dwellings",
    # `boatman` — TRADE_CLAUSE bands the river trades with the labourers.
    "Navigation of canals, lakes and rivers": "labourer_dwellings",
    # `sailor` — the same clause, for the same reason.
    "Navigation of the ocean": "labourer_dwellings",
    # The policy holds a clause for the farms and country places outside the plat, and
    # `farms_and_country_seats` is addressed to the cabins (D1) that stand on them.
    "Agriculture": "farms_and_country_seats",
    # REFUSED. There is no mine in or near this town; the column is 2 persons of 870 in
    # a county schedule five years later. It bands nobody and its share is renormalised
    # away rather than dealt into a clause it does not mean.
    "Mining": None,
}

# The table the shares are read out of, named so a drift in the model is a gate failure
# here rather than a silent re-deal.
EMPLOYMENT_TABLE = "employment_shape_1840"

# The salts. Two independent seeded orders, so the division a household is dealt does not
# determine its class. They are part of the published method: change one and every row's
# deal changes, which `--check` reports as a rebuild that does not match.
DIVISION_SALT = "T-1522/policy_only/division"
CLASS_SALT = "T-1522/policy_only/class"

# The division no household with no evidence is ever dealt. The garrison's households
# belong to the fort's own stage (T-1176) and the order book gives `households/garrison/
# fort` no target at all, so the fort is not in the shape and assertion 13 says so.
NOT_DEALT = "fort"


def digest(key: str) -> str:
    """The seeded key that orders one household in one deal. sha256 of the household id
    and the salt — no clock, no run id, nothing that differs between two runs."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def largest_remainder(shares: dict[str, float], total: int) -> dict[str, int]:
    """Deal `total` places across `shares` so the parts sum to the whole EXACTLY.

    Floor each quota, then give the remaining places to the largest fractional parts,
    ties broken by name so the answer does not depend on dict order. This is why the
    dealt counts below are the committed shape to the person rather than near it.
    """
    quotas = {k: shares[k] * total for k in shares}
    dealt = {k: int(quotas[k]) for k in quotas}
    short = total - sum(dealt.values())
    order = sorted(quotas, key=lambda k: (-(quotas[k] - int(quotas[k])), k))
    for k in order[:short]:
        dealt[k] += 1
    return dealt


_ORDER_BOOK_CACHE: dict | None = None


def order_book() -> dict:
    global _ORDER_BOOK_CACHE
    if _ORDER_BOOK_CACHE is None:
        _ORDER_BOOK_CACHE = read_json(ORDER_BOOK)
    return _ORDER_BOOK_CACHE


def division_shape() -> dict[str, int]:
    """The town's household distribution by division, as the order book states it.

    Every `households/<kind>/<division>` bucket that carries a target, summed by
    division. Nothing here is this file's arithmetic on top of the book: the book's own
    `households_target` is the sum of exactly these numbers.
    """
    family = next(f for f in order_book()["bucket_families"] if f["key"] == "households")
    shape: dict[str, int] = {}
    for bucket in family["buckets"]:
        target = bucket.get("target")
        if target is None:
            continue
        division = bucket["key"].rsplit("/", 1)[1]
        shape[division] = shape.get(division, 0) + int(target)
    if NOT_DEALT in shape:
        raise Refused(f"the order book now gives {NOT_DEALT!r} a household target. A "
                      "household no source places may not be dealt into the garrison's "
                      "reservation — rule on it before the shape carries it")
    if not shape:
        raise Refused("the order book states no household target by division")
    return dict(sorted(shape.items()))


def class_shape() -> tuple[dict[str, float], list[dict]]:
    """The placement-policy clauses the town model's employment distribution implies.

    Returns the clause shares, renormalised over the columns that band somebody, and the
    refusals — a column this file bands nowhere, with its share and its reason.
    """
    model = read_json(TOWN_MODEL)
    section = next(s for s in model["sections"] if s["key"] == "occupations")
    table = section["tables"].get(EMPLOYMENT_TABLE)
    if not table:
        raise Refused(f"the town model no longer carries {EMPLOYMENT_TABLE!r} — the "
                      "class deal reads that table and may not fall back on anything")
    weights: dict[str, float] = {}
    refused: list[dict] = []
    for row in table["rows"]:
        column = row["column"]
        if column not in COLUMN_CLAUSE:
            raise Refused(f"the town model's employment table has grown a column "
                          f"{column!r} this file bands nowhere — rule on it rather than "
                          "letting it fall out of the deal unremarked")
        clause = COLUMN_CLAUSE[column]
        if clause is None:
            refused.append({"column": column, "share_of_employed": row["share_of_employed"],
                            "persons": row["persons"],
                            "refused_because": ("there is no mine in or near this town, so "
                                                "the column bands nobody here and its "
                                                "share is renormalised away")})
            continue
        weights[clause] = weights.get(clause, 0.0) + float(row["share_of_employed"])
    total = sum(weights.values())
    if total <= 0:
        raise Refused("every column of the employment distribution was refused")
    return {k: weights[k] / total for k in sorted(weights)}, refused


_DEAL_CACHE: dict[str, dict[str, str]] | None = None


def policy_only_deal() -> dict[str, dict]:
    """The division and the class dealt to every household no source places.

    One seeded order per axis, one exact quota per axis. The same 1,186 ids in, the same
    1,186 answers out, on any machine and in any run.
    """
    global _DEAL_CACHE
    if _DEAL_CACHE is not None:
        return _DEAL_CACHE
    ids = sorted(hh["id"] for hh in household_records()
                 if not (hh.get("lives_at") or {}).get("value")
                 and (hh.get("division") or "unplaced") == "unplaced")
    total = len(ids)
    shape = division_shape()
    book_total = sum(shape.values())
    division_shares = {k: shape[k] / book_total for k in shape}
    clause_shares, _ = class_shape()

    deal: dict[str, dict] = {}
    for axis, salt, shares in (("division", DIVISION_SALT, division_shares),
                               ("clause", CLASS_SALT, clause_shares)):
        quota = largest_remainder(shares, total)
        order = sorted(ids, key=lambda i: (digest(f"{i}|{salt}"), i))
        cursor = 0
        for key in sorted(quota):
            for hid in order[cursor:cursor + quota[key]]:
                deal.setdefault(hid, {})[axis] = key
                deal[hid][f"{axis}_digest"] = digest(f"{hid}|{salt}")[:12]
            cursor += quota[key]
        if cursor != total:
            raise Refused(f"the {axis} deal placed {cursor} of {total} households")
    _DEAL_CACHE = deal
    return deal


class Refused(Exception):
    """A limit this file may not cross."""


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def committed_structures() -> set[str]:
    return {p.stem for p in sorted(STRUCTURES.glob("*.json"))}


_HOUSEHOLD_CACHE: list[dict] | None = None


def household_records() -> list[dict]:
    """Every committed household card. Read once — `--self-test` re-asserts fifteen
    times over and the cards are 1,393 files."""
    global _HOUSEHOLD_CACHE
    if _HOUSEHOLD_CACHE is None:
        _HOUSEHOLD_CACHE = [read_json(p) for p in sorted(HOUSEHOLDS.glob("*.json"))]
    return _HOUSEHOLD_CACHE


_POLICY_CACHE: dict[str, dict] | None = None


def policy_clauses() -> dict[str, dict]:
    """The committed placement policy's clauses, by id. Nothing else is read from it."""
    global _POLICY_CACHE
    if _POLICY_CACHE is None:
        _POLICY_CACHE = {c["id"]: c for c in read_json(POLICY)["clauses"]}
    return _POLICY_CACHE


def head_trade(hh: dict) -> str | None:
    """The trade the household's OWN record gives its head, or None.

    `none_recorded` is a recorded absence, not a trade, and it returns None — a head
    with no trade is banded by the division alone, never by a class dealt for them.
    """
    head = hh.get("head")
    for person in hh.get("persons") or []:
        if person.get("id") == head:
            value = (person.get("occupation") or {}).get("value")
            return value if value and value != "none_recorded" else None
    return None


def band_for(division: str, trade: str | None, clauses: dict[str, dict]) -> dict:
    """The band a household in `division` with `trade` falls in.

    Two outcomes and no third. Either the policy holds a dwelling clause for the trade,
    and the band is that clause inside the division the card already names; or it does
    not, and the band is the division's own ground — which adds nothing to what the card
    said. The division is NEVER changed here: it is the evidence, and the band is the
    only reconstructed part of the seat.
    """
    clause_id = TRADE_CLAUSE.get(trade or "")
    if clause_id and clause_id in clauses:
        clause = clauses[clause_id]
        prefers = [t.split(":", 1)[1] for t in clause.get("prefers") or []
                   if t.startswith("division:")]
        return {
            "band": f"{division}/{clause_id}",
            "clause": clause_id,
            "clause_applies_to": list(clause.get("applies_to") or []),
            "clause_tier": clause.get("tier"),
            "statement": clause.get("note"),
            "division_is_the_clause_preference": (division in prefers) if prefers else None,
            "from_trade": trade,
        }
    return {
        "band": f"{division}/{DIVISION_GROUND}",
        "clause": None,
        "clause_applies_to": [],
        "clause_tier": None,
        "statement": ("No dwelling clause of the placement policy reaches this "
                      "household's head, so the band is the division the record names "
                      "and nothing narrower. A class is not dealt for them here."),
        "division_is_the_clause_preference": None,
        "from_trade": trade,
    }


def business_names() -> dict[str, str]:
    """register_id -> the firm's name, for the rows the spend adjudicates."""
    names = {}
    for path in sorted(BUSINESSES.glob("*.json")):
        rec = read_json(path)
        if rec.get("register_id"):
            names[rec["register_id"]] = rec.get("name") or rec["id"]
    return names


# ---- the household half ---------------------------------------------------- #


def household_row(hh: dict, committed: set[str], clauses: dict[str, dict]) -> dict:
    """One household, seated at the first rung that fires.

    Rung 1 fires on `lives_at`, the only field that names a roof. Rung 4 fires on the
    card's own `division` — the band inside it is reconstructed, the division is not.
    Rung 5 is T-1513's and does not fire here: a household with no division at all
    stays `owed` and says whose it is.
    """
    lives = hh.get("lives_at") or {}
    works = hh.get("works_at") or {}
    seat_id = lives.get("value")
    works_id = works.get("value")
    division = hh.get("division") or "unplaced"
    basis = lives.get("basis") or {}
    row = {
        "id": hh["id"],
        "kind": "household",
        "name": hh.get("name") or hh["id"],
        "rung": None,
        "seat": None,
        "works_seat": ({"kind": "structure", "id": works_id}
                       if works_id and works_id in committed else None),
        "reach": None,
        "reach_value": None,
        "division": division,
        "tier": None,
        "basis": None,
        "words": None,
        "replaceable_by": None,
        "owed_to": None,
        "band": None,
        "seed": None,
    }
    if seat_id:
        row["rung"] = "structure"
        row["seat"] = {"kind": "structure", "id": seat_id}
        row["reach"] = "structure"
        row["tier"] = lives.get("tier") or lives.get("confidence")
        row["basis"] = basis.get("note") or lives.get("note")
        row["words"] = (f"Seated at a named roof — the strongest rung this ladder has. "
                        f"The household record carries the seat at {row['tier']}.")
        rb = lives.get("replaceable_by") or {}
        row["replaceable_by"] = rb.get("match") or "a source naming a different building"
        return row
    if division == "outside_town":
        row["rung"] = "unplaceable"
        row["reach"] = "none"
        row["words"] = ("The evidence puts this household OUTSIDE the town, so no seat "
                        "inside it will be dealt for them. This is a placement, not a gap.")
        row["replaceable_by"] = "a source placing this household inside the town"
        return row
    if division in TOWN_DIVISIONS:
        trade = head_trade(hh)
        band = band_for(division, trade, clauses)
        row["rung"] = "division_band"
        row["seat"] = {"kind": "division_band", "id": band["band"],
                       "division": division, "clause": band["clause"]}
        row["reach"] = "division"
        row["reach_value"] = division
        row["tier"] = "reconstructed"
        row["basis"] = band["statement"]
        row["band"] = band
        # The deal makes no draw: the division is the card's and the clause follows from
        # the head's trade, so the same inputs give the same band every time. The seed is
        # the key that determined it, kept so a reader can retrace the deal — not a die.
        row["seed"] = f"{hh['id']}|{division}|{trade or 'no_trade'}|T-1512"
        if band["clause"]:
            row["words"] = (
                f"The record reaches the {division} division and nothing narrower. Inside "
                f"it the placement policy bands this household by its head's trade "
                f"({trade}): {band['statement']} The division is the evidence; the band "
                "is reconstruction, and no lot, roof or coordinate is claimed by it.")
            row["replaceable_by"] = ("a source naming a street, a corner or a building "
                                     "for this household")
        else:
            row["words"] = (
                f"The record reaches the {division} division and nothing narrower, and "
                "the head's trade is not one the placement policy has a dwelling clause "
                "for — so this household is banded to that division's own ground and no "
                "class is dealt for it. The division is the evidence; standing them "
                "anywhere inside it is reconstruction.")
            row["replaceable_by"] = ("a source giving this household's head a trade, or "
                                     "naming a street, a corner or a building for them")
        return row
    if division != "unplaced":
        raise Refused(f"{hh['id']}: its record carries division {division!r}, which is "
                      "neither a town division, nor outside the town, nor unplaced — "
                      "rule on it rather than letting it fall off the ladder")
    # Rung 5 (T-1522). Nothing in the record reaches anywhere, so BOTH halves of the
    # band are dealt: the division off the order book's household shape, the class off
    # the town model's employment distribution. Neither is read; both are stated as
    # dealt, on the row and in the words.
    dealt = policy_only_deal()[hh["id"]]
    dealt_division, clause_id = dealt["division"], dealt["clause"]
    clause = clauses[clause_id]
    row["rung"] = "policy_only"
    row["seat"] = {"kind": "division_band", "id": f"{dealt_division}/{clause_id}",
                   "division": dealt_division, "clause": clause_id}
    row["reach"] = "none"
    row["tier"] = "reconstructed"
    row["basis"] = clause.get("note")
    row["band"] = {
        "band": f"{dealt_division}/{clause_id}",
        "clause": clause_id,
        "clause_applies_to": list(clause.get("applies_to") or []),
        "clause_tier": clause.get("tier"),
        "statement": clause.get("note"),
        "division_is_the_clause_preference": (
            dealt_division in [t.split(":", 1)[1] for t in clause.get("prefers") or []
                               if t.startswith("division:")]),
        "from_trade": None,
        "division_is_dealt": True,
        "division_dealt_from": "the order book's household target by division",
        "class_is_dealt": True,
        "class_dealt_from": f"the town model's {EMPLOYMENT_TABLE} distribution",
    }
    row["seed"] = (f"{hh['id']}|T-1522|division:{dealt['division_digest']}"
                   f"|class:{dealt['clause_digest']}")
    row["owed_to"] = None
    row["words"] = (
        "No source places this household anywhere — the record gives a name and no "
        "address, no street and not even a division. So BOTH halves of this band are "
        f"dealt rather than read: the {dealt_division} division from the reconstruction "
        "order book's own household target by division, and the class from the town "
        "model's employment distribution, which puts this household under the placement "
        f"policy's {clause_id} clause. {clause.get('note')} The deal is seeded on this "
        "household's own id, so it is the same on every run — and it is the weakest seat "
        "this ladder makes: no lot, no roof, no coordinate and no source behind either "
        "half of it.")
    row["replaceable_by"] = "any source that places this household in a division or nearer"
    return row


# ---- the business half ----------------------------------------------------- #


def business_row(placement: dict, names: dict[str, str]) -> dict:
    grade = placement["grade"]
    if grade not in FROM_GRADE:
        raise Refused(f"{placement['business_id']}: unknown adjudicated grade {grade!r}")
    rung, reach, owed = FROM_GRADE[grade]
    street = placement.get("evidence_street")
    if placement.get("model_seat"):
        # The spend adjudicated a roof. Nothing here may move it.
        seat = {"kind": "structure", "id": placement["model_seat"]}
    elif grade == "street_only_unseated":
        # T-1512: the face adoption could not find this firm a free ROOF on the street
        # its advertisement names. That is not the same as not finding it a FACE. It
        # stands on the face — no roof, no lot, no coordinate, and the street it stands
        # on is the one the paper printed.
        seat = {"kind": "street_face", "id": placement["register_action_target"],
                "street_name": street}
    else:
        seat = None
    if grade == "structure_committed":
        words = ("The advertisement's anchor reaches a roof this town has built, and the "
                 "firm is seated on it.")
    elif grade == "structure_pending":
        words = ("The advertisement's anchor reaches a roof the town has NOT built yet. "
                 f"The seat waits on the district build tickets ({OWED_BUILD}); the "
                 "evidence is good enough for a roof and the roof is not there.")
    elif grade == "street_only_adopted":
        words = (f"The paper reaches {street} and nothing narrower. The street-face "
                 "adoption houses this firm on that face, which is housing and not a "
                 "reading: substitutable, no lot, no anchor.")
    elif grade == "street_only_unseated":
        words = (f"The paper reaches {street} and nothing narrower, and no ROOF on it "
                 "could be adopted — every one is spoken for. So this firm stands on the "
                 "FACE itself: on that street, in no building this model holds, with no "
                 "lot and no coordinate claimed. The street is the reading; standing them "
                 "on it without a roof is the reconstructed step.")
    else:
        words = ("The paper reaches no ground this model holds. This firm stays in the "
                 "register, unplaced, with its printed reason — and it is not moved by "
                 "any rule of the placement policy.")
    return {
        "id": placement["business_id"],
        "kind": "business",
        "name": names.get(placement["business_id"], placement["business_id"]),
        "rung": rung,
        "seat": seat,
        "works_seat": None,
        "reach": reach,
        "reach_value": street,
        "division": None,
        "tier": ("reconstructed" if grade == "street_only_unseated"
                 else "inferred" if rung in ("structure", "face") else None),
        "basis": placement.get("clause"),
        "words": words,
        "replaceable_by": ("a printing that names a lot, a corner ordinal or a building "
                           "for this firm"),
        "owed_to": owed,
        "band": None,
        "seed": (f"{placement['business_id']}|{placement['register_action_target']}|T-1512"
                 if grade == "street_only_unseated" else None),
        "seat_is_substitutable": bool(placement.get("seat_is_substitutable")),
        "adjudicated_grade": grade,
    }


# ---- the file -------------------------------------------------------------- #


def dealt_roofs() -> dict[str, dict]:
    """The placement policy's deal, by row id — the roof it seated a household at, or
    the slot it requested. Read from the two committed seats files and nothing else;
    no roof, lot, parcel or reason is composed here that those files do not state.

    `words` is the only sentence this function writes, and it is written to be
    unmistakable: it names the deal as a deal, and it carries the seats file's own
    `why` verbatim after it.
    """
    dealt: dict[str, dict] = {}
    for path, ticket, ground in DEALT_SEAT_FILES:
        doc = read_json(path)
        for seat in doc["seats"]:
            roof = seat.get("structure_id")
            on = seat.get("lot_id") if ground == "platted_lot" else seat.get("parcel_id")
            where = (f"on {on}" if on else "on no committed parcel of that ledger")
            if roof:
                words = (
                    f"The placement policy seats this household at a roof already "
                    f"standing — {roof}, a family {seat['family']} roof {where}. The "
                    f"roof is the POLICY'S deal and not a reading about this household: "
                    f"it is an anonymous roof of the reconstruction programme, adopted "
                    f"under the policy's {seat['clause']} clause, and any other free "
                    f"roof the clause admits would have done as well.")
            else:
                words = (
                    f"The placement policy deals this household a place {where} under "
                    f"its {seat['clause']} clause, and the roof is not built: the deal "
                    f"REQUESTED a family {seat['family']} roof off that block's own "
                    f"committed plan, and {OWED_SLOT_BUILD} raise it. So there is "
                    f"nowhere yet to stand.")
            dealt[seat["id"]] = {
                "structure_id": roof,
                "how": seat["how"],
                "dealt_by": ticket,
                "ground": ground,
                "on": on,
                "block_id": seat.get("block_id"),
                "fronts": seat.get("fronts"),
                "family": seat["family"],
                "clause": seat["clause"],
                "district": seat["district"],
                "stands_on": seat["stands_on"],
                "deal_seed": seat["seed"],
                "why": seat["why"],
                "owed_to": None if roof else OWED_SLOT_BUILD,
                "substitutable": True,
                # The seats file's own reason, verbatim and attributed, after the
                # sentence this function writes — never blended into it, so a reader
                # can tell the wording apart from the ruling.
                "words": f"{words} Why this one: {seat['why'].strip().rstrip('.')}.",
            }
    return dealt


def build() -> dict:
    committed = committed_structures()
    spend = read_json(SPEND)
    names = business_names()
    clauses = policy_clauses()
    rows = [household_row(hh, committed, clauses) for hh in household_records()]
    rows += [business_row(p, names) for p in spend["placements"]]

    # The policy's deal, carried onto the row BESIDE the ladder and never into it
    # (T-1618). Every row carries the key so a reader never has to ask whether its
    # absence means "not dealt" or "this book does not know about the deal".
    dealt = dealt_roofs()
    for row in rows:
        row["dealt_roof"] = dealt.get(row["id"])

    by_rung: dict[str, int] = {}
    by_reach: dict[str, int] = {}
    for row in rows:
        by_rung[row["rung"]] = by_rung.get(row["rung"], 0) + 1
        by_reach[row["reach"]] = by_reach.get(row["reach"], 0) + 1
    households = [r for r in rows if r["kind"] == "household"]
    businesses = [r for r in rows if r["kind"] == "business"]

    lot_ledger = read_json(LOT_ADDRESSES)
    shape = division_shape()
    book_total = sum(shape.values())
    clause_shares, class_refusals = class_shape()
    policy_only = [r for r in households if r["rung"] == "policy_only"]
    dealt_divisions: dict[str, int] = {}
    dealt_clauses: dict[str, int] = {}
    for row in policy_only:
        dealt_divisions[row["seat"]["division"]] = \
            dealt_divisions.get(row["seat"]["division"], 0) + 1
        dealt_clauses[row["seat"]["clause"]] = dealt_clauses.get(row["seat"]["clause"], 0) + 1
    return {
        "$schema_note": "Derived. Do not hand-edit — tools/seat_known_1835.py --build "
                        "writes it and --check re-derives it.",
        "id": "1835_address_book",
        "ticket": TICKET,
        "tickets": TICKETS,
        "parent_ticket": "T-1198",
        "generated_by": "tools/seat_known_1835.py --build",
        "scene_date": SCENE_DATE,
        "not_a_reading": (
            "Rungs 1, 3-for-an-adopted-firm and 6 restate a seat some other committed "
            "record already made. Rung 3 for a refused street-only firm and rung 4 are "
            "RECONSTRUCTION (T-1512): each carries tier `reconstructed`, the clause it "
            "rests on, a seed and what would retire it, and neither adds a street or a "
            "division the record did not already carry. RUNG 5 IS THE ONE PLACE IN THIS "
            "FILE WHERE A DIVISION IS DEALT (T-1522) — for the 1,186 households no "
            "source places at all, off the order book's own household shape and the town "
            "model's own employment distribution, seeded and exact, every row saying so "
            "in its words. No coordinate, no lot and no roof is invented by this pass, "
            "no bucket of the order book is spent, and no household record is written "
            "to. T-1618 carries the PLACEMENT POLICY's own deal onto the row as "
            "`dealt_roof` — read from the two committed seats files and restated, "
            "not re-decided — and it is not a rung: every dealt row keeps the rung, "
            "seat, tier and words its evidence earned, and the roof is substitutable "
            "by construction."),
        "policy_only_deal": {
            "ticket": "T-1522",
            "households": len(policy_only),
            "what_is_dealt": (
                "both halves of the band. These households carry no roof, no street and "
                "no division, so nothing about where they stood is read here — the "
                "division comes off the reconstruction order book's household target by "
                "division and the class off the town model's employment distribution, "
                "and every row says both in its own words."),
            "nothing_is_minted": (
                "these 1,186 households are already in the committed layer and the book "
                "records them as KNOWN, not as households to reconstruct. So the book "
                "supplies the SHAPE of the deal and no bucket's `filled` moves, no "
                "record is written and nothing is added to the town. The invariant the "
                "book calls `no_bucket_overfilled` is untouched by this pass."),
            "division": {
                "from": "data/reconstruction/1835_reconstruction_order_book.json",
                "how": ("every households/<kind>/<division> bucket that carries a "
                        "target, summed by division — the same sum the book's own "
                        "households_target is"),
                "target_by_division": shape,
                "target_total": book_total,
                "share_by_division": {k: round(shape[k] / book_total, 6) for k in shape},
                "dealt": dict(sorted(dealt_divisions.items())),
                "fort_is_not_in_the_shape": (
                    "the garrison's households are T-1176's and the book gives "
                    "households/garrison/fort no target, so a household no source places "
                    "is never dealt into the military reservation"),
            },
            "class": {
                "from": f"data/reconstruction/1835_town_model.json, {EMPLOYMENT_TABLE}",
                "how": ("each of the 1840 schedule's industry columns mapped to the "
                        "placement-policy clause the committed TRADE_CLAUSE table "
                        "already gives a trade of that column, then renormalised over "
                        "the columns that band somebody"),
                "column_to_clause": dict(sorted(
                    (k, v) for k, v in COLUMN_CLAUSE.items() if v)),
                "refused_columns": class_refusals,
                "share_by_clause": {k: round(clause_shares[k], 6) for k in clause_shares},
                "dealt": dict(sorted(dealt_clauses.items())),
            },
            "method": (
                "exact, not sampled. Households are ordered by sha256 of their own id "
                "and a stated salt — one order per axis, so the division a household is "
                "dealt does not determine its class — and each quota is dealt off that "
                "order by largest remainder. The dealt counts are therefore the "
                "committed shape to the person, and a re-run gives the same answer."),
            "salts": {"division": DIVISION_SALT, "class": CLASS_SALT},
            "still_owed_to": None,
            "carried_back_by": CARRIED_BACK_BY,
            "what_was_carried_back": (
                "the dealt division no longer lives in this file alone. "
                "tools/carry_policy_only_division.py writes it onto every rung-5 "
                "household card as the block `division_reconstructed` — through the same "
                "carry slot the mint stages use, so the four mints that re-derive a "
                "household record cannot delete it — and rebuild_resident_index.py "
                "denormalises the value into data/residents/index.json beside `division`. "
                "compile_scene.py shows it in the People view, marked `reconstructed`, so "
                "the division filter now holds these households instead of being short of "
                "them. THE CARD'S OWN `division` STILL READS `unplaced` AND MUST: it is "
                "what a source states, rung 5 is defined as the households where that is "
                "`unplaced` (assertion 13), and rebuild_resident_index's "
                "`a_stated_division` dwelling clause would otherwise count every one of "
                "these as a HOUSE this deal claims no roof for."),
        },
        "dealt_roofs": {
            "tickets": ["T-1613", "T-1614", "T-1618"],
            "what_it_is": (
                "where the placement policy PUT a household, carried onto its row from "
                "the two committed seats files. It is not a rung and it does not touch "
                "one: the ladder still says what the household's own record reaches, "
                "which for every dealt row is a band and nothing narrower."),
            "why_it_is_here": (
                "the deal was written in T-1613 and T-1614 and read by nothing a "
                "visitor opens. 172 reconstructed households stood under a roof this "
                "scene actually raises and their cards could not offer to take anybody "
                "to it, because the only seat the card could go to was one the "
                "household's own record named — which, for a reconstructed household, "
                "is by definition never there."),
            "what_it_refuses": (
                "it re-grades nothing. The row keeps its rung, its seat, its tier and "
                "its words; the roof is marked substitutable, the button names the "
                "POLICY rather than an address, and a `slot` deal — a roof the policy "
                "requested and the programme has not built — offers no destination at "
                "all and says who owes it."),
            "from": [
                "data/reconstruction/1835_platted_seats.json",
                "data/reconstruction/1835_off_plat_seats.json",
            ],
            "slots_are_owed_to": OWED_SLOT_BUILD,
        },
        "bands": {
            "what_a_band_is": (
                "an adjudication over data/reconstruction/1835_placement_policy.json — "
                "the division the household's own card carries, and the policy clause "
                "its head's trade falls under. A band claims no lot, no roof and no "
                "coordinate; it says which ground inside a division the policy puts a "
                "household of this kind on."),
            "division_ground": (
                "the band for a head whose trade no dwelling clause of the policy "
                "reaches — including every head recorded `none_recorded`. It names the "
                "division and stops, so that a household with no trade is not dealt a "
                "class it never had."),
            "trade_to_clause": dict(sorted(TRADE_CLAUSE.items())),
            "clauses_used": sorted({c for c in TRADE_CLAUSE.values()}),
        },
        "inputs": [
            "data/residents/households/",
            "data/reconstruction/1835_placement_policy.json",
            "data/reconstruction/1835_reconstruction_order_book.json",
            "data/reconstruction/1835_town_model.json",
            "data/research/location_spend.json",
            "data/research/newspapers/lot_addresses.json",
            "data/businesses/",
            "data/structures/",
            "data/reconstruction/1835_platted_seats.json",
            "data/reconstruction/1835_off_plat_seats.json",
        ],
        "vocabulary": {
            "rungs": [
                {"rung": "structure", "ladder": 1,
                 "means": "a named roof this town has built"},
                {"rung": "lot", "ladder": 2,
                 "means": "an address, a corner ordinal or a lot-and-block line that "
                          "narrows to the plat's own unit",
                 "stands_empty_because": (
                     "the committed lot-address ledger carries "
                     f"{len(lot_ledger['addresses'])} address(es) and none of them names "
                     "a household or a firm")},
                {"rung": "face", "ladder": 3,
                 "means": "a street and nothing narrower, housed on a block face — "
                          "substitutable, no lot, no anchor. A firm the adoption could "
                          "seat on a roof of that face carries a `structure` seat; one "
                          "it could not carries the `street_face` itself (T-1512)."},
                {"rung": "division_band", "ladder": 4,
                 "means": "the division the household's own record names, banded inside "
                          "it by the placement policy clause its head's trade falls "
                          "under — or by the division's own ground where no clause "
                          "reaches that trade. Reconstruction, seeded, no coordinate."},
                {"rung": "policy_only", "ladder": 5,
                 "means": ("nothing in the record reaches anywhere — no roof, no street "
                           "and no division — so both halves of the band are dealt: the "
                           "division from the order book's household target by division "
                           "and the class from the town model's employment "
                           "distribution. Reconstruction, seeded, exact to the "
                           "committed shape, and no coordinate (T-1522).")},
                {"rung": "unplaceable", "ladder": 6,
                 "means": "the evidence contradicts every band inside the town"},
                {"rung": "owed", "ladder": None,
                 "means": "the evidence reaches something, and the seat it implies is "
                          "owed to another ticket. `seat` is null and stays null."},
            ],
            "reaches": ["structure", "structure_owed", "face", "division", "none"],
            "reach_none_is_two_things": (
                "a rung-5 row and a rung-6 row both reach nothing, and they are opposite "
                "answers. Rung 6 is a household the evidence places OUTSIDE the town; "
                "rung 5 is one the evidence places nowhere at all."),
            "seat_kinds": ["structure", "street_face", "division_band"],
        },
        "counts": {
            "rows": len(rows),
            "households": len(households),
            "businesses": len(businesses),
            "by_rung": dict(sorted(by_rung.items())),
            "by_reach": dict(sorted(by_reach.items())),
            "households_by_rung": dict(sorted(
                {r["rung"]: sum(1 for x in households if x["rung"] == r["rung"])
                 for r in households}.items())),
            "businesses_by_rung": dict(sorted(
                {r["rung"]: sum(1 for x in businesses if x["rung"] == r["rung"])
                 for r in businesses}.items())),
            "seated": sum(1 for r in rows if r["seat"]),
            "owed": sum(1 for r in rows if r["rung"] == "owed"),
            "by_seat_kind": dict(sorted(
                {k: sum(1 for r in rows if r["seat"] and r["seat"]["kind"] == k)
                 for k in ("structure", "street_face", "division_band")}.items())),
            "by_band": dict(sorted(
                {r["seat"]["id"]: sum(1 for x in rows
                                      if x["seat"] and x["seat"]["kind"] == "division_band"
                                      and x["seat"]["id"] == r["seat"]["id"])
                 for r in rows
                 if r["seat"] and r["seat"]["kind"] == "division_band"}.items())),
            "reconstructed_seats": sum(1 for r in rows
                                       if r["seat"] and r["tier"] == "reconstructed"),
            "dealt_a_roof": sum(1 for r in rows if r["dealt_roof"]),
            "dealt_a_standing_roof": sum(1 for r in rows if (r["dealt_roof"] or {}).get(
                "structure_id")),
            "dealt_a_slot_not_yet_built": sum(1 for r in rows if r["dealt_roof"]
                                              and not r["dealt_roof"]["structure_id"]),
            "dealt_by_ticket": dict(sorted(
                {t: sum(1 for r in rows if (r["dealt_roof"] or {}).get("dealt_by") == t)
                 for t in ("T-1613", "T-1614")}.items())),
            "dealt_by_ground": dict(sorted(
                {g: sum(1 for r in rows if (r["dealt_roof"] or {}).get("ground") == g)
                 for g in ("platted_lot", "off_plat_parcel")}.items())),
        },
        "rows": rows,
    }


def write(doc: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")


def read_committed():
    try:
        return read_json(OUT)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


# ---- the limits ------------------------------------------------------------ #


def assertions(doc: dict) -> None:
    rows = doc["rows"]
    committed = committed_structures()
    spend = read_json(SPEND)

    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise Refused("a row appears twice — one row per household and per firm")

    # 7a. Rung 2 stands empty, and it is asked FIRST: a row that climbs to it must be
    # refused here rather than by whatever limit the rung it left happens to hold.
    if any(r["rung"] == "lot" for r in rows):
        raise Refused("a row sits at rung 2 and this pass writes none — if the lot "
                      "ledger has grown, seat it deliberately, with its address quoted")

    households = {r["id"] for r in rows if r["kind"] == "household"}
    on_disk = {p.stem for p in HOUSEHOLDS.glob("*.json")}
    if households != on_disk:
        missing = sorted(on_disk - households)[:3]
        extra = sorted(households - on_disk)[:3]
        raise Refused("the household rows are not the committed households "
                      f"(missing {missing}, extra {extra})")

    firms = {r["id"] for r in rows if r["kind"] == "business"}
    adjudicated = {p["business_id"] for p in spend["placements"]}
    if firms != adjudicated:
        raise Refused("the business rows are not the adjudicated firms of "
                      "data/research/location_spend.json")

    for row in rows:
        seat = row["seat"]
        if seat and seat["kind"] == "structure" and seat["id"] not in committed:
            raise Refused(f"{row['id']}: seated on {seat['id']}, which is not a "
                          "committed structure — no seat may be invented here")
        if seat and seat["kind"] not in ("structure", "street_face", "division_band"):
            raise Refused(f"{row['id']}: seat kind {seat['kind']!r} is not one this "
                          "book holds")
        if row["rung"] == "owed" and row["seat"]:
            raise Refused(f"{row['id']}: an owed row carries a seat. The whole point of "
                          "the rung is that it does not.")
        if row["rung"] == "owed" and not row["owed_to"]:
            raise Refused(f"{row['id']}: owed, and it does not say to whom")
        if not row["words"]:
            raise Refused(f"{row['id']}: no words — the card would have nothing to say")
        if not row["replaceable_by"]:
            raise Refused(f"{row['id']}: nothing would move it up the ladder")

    # 4. The business half is a strict restatement of T-1239's adjudication.
    by_id = {r["id"]: r for r in rows if r["kind"] == "business"}
    for placement in spend["placements"]:
        want_rung, want_reach, want_owed = FROM_GRADE[placement["grade"]]
        row = by_id[placement["business_id"]]
        if (row["rung"], row["reach"], row["owed_to"]) != (want_rung, want_reach, want_owed):
            raise Refused(f"{row['id']}: rung {row['rung']!r}/{row['reach']!r} does not "
                          f"restate the adjudicated grade {placement['grade']!r}")
        seat = row["seat"]
        roof = seat["id"] if seat and seat["kind"] == "structure" else None
        if roof != placement.get("model_seat"):
            raise Refused(f"{row['id']}: its roof is not the one the spend adjudicated")
        # 4b (T-1512). A firm the adoption could not seat stands on the FACE of the
        # street the register acted on, and on no roof.
        if placement["grade"] == "street_only_unseated":
            if not seat or seat["kind"] != "street_face":
                raise Refused(f"{row['id']}: the adoption refused it a roof, so it must "
                              "stand on the street face — and it does not")
            if seat["id"] != placement["register_action_target"]:
                raise Refused(f"{row['id']}: seated on the face of {seat['id']!r}, which "
                              "is not the street the register acted on")
            if row["tier"] != "reconstructed":
                raise Refused(f"{row['id']}: a face seat with no roof under it is "
                              "reconstruction and must say so")

    # 5. The 62 unplaceable firms stay unplaceable.
    unplaceable = {r["id"] for r in rows
                   if r["kind"] == "business" and r["rung"] == "unplaceable"}
    published = {p["business_id"] for p in spend["placements"]
                 if p["grade"] == "unplaceable"}
    if unplaceable != published:
        raise Refused("the unplaceable firms are not the ones the spend publishes — "
                      "a rung <= 3 fact must be cited before one of them moves")

    # 6. A household is seated where, and only where, its own record names a roof.
    seated = {r["id"] for r in rows
              if r["kind"] == "household" and r["rung"] == "structure"}
    named = {hh["id"] for hh in household_records()
             if (hh.get("lives_at") or {}).get("value")}
    if seated != named:
        raise Refused("the seated households are not the households whose committed "
                      "record names a roof")

    # 9 (T-1512). Every band is the division the card carries, and a clause the
    # committed policy holds — or the division's own ground and no class at all.
    clauses = policy_clauses()
    hh_by_id = {hh["id"]: hh for hh in household_records()}
    banded = [r for r in rows if r["rung"] == "division_band"]
    for row in banded:
        hh = hh_by_id[row["id"]]
        division = hh.get("division")
        seat = row["seat"]
        if seat["kind"] != "division_band":
            raise Refused(f"{row['id']}: rung 4 and the seat is not a band")
        if seat["division"] != division or not seat["id"].startswith(f"{division}/"):
            raise Refused(f"{row['id']}: banded into {seat['division']!r} while its own "
                          f"record says {division!r} — a band may not move a household "
                          "out of the division its evidence names")
        if row["tier"] != "reconstructed":
            raise Refused(f"{row['id']}: a band is reconstruction and must carry the tier")
        if not row["seed"]:
            raise Refused(f"{row['id']}: a reconstructed seat with no seed")
        clause_id = seat["clause"]
        if clause_id is not None and clause_id not in clauses:
            raise Refused(f"{row['id']}: cites placement-policy clause {clause_id!r}, "
                          "which that file does not hold")
        trade = head_trade(hh)
        if clause_id is None and TRADE_CLAUSE.get(trade or ""):
            raise Refused(f"{row['id']}: its head is a {trade} and the policy has a "
                          "clause for that trade — the band fell to the division ground "
                          "anyway")
        if clause_id is not None and trade is None:
            raise Refused(f"{row['id']}: banded by a clause while its record gives its "
                          "head no trade — no class may be dealt here")

    # 10 (T-1512). Every household whose record names a town division and no roof is
    # banded. None is left owed, and none without a division is banded.
    row_by_id = {r["id"]: r for r in rows if r["kind"] == "household"}
    for hh in household_records():
        row = row_by_id[hh["id"]]
        has_roof = bool((hh.get("lives_at") or {}).get("value"))
        in_division = hh.get("division") in TOWN_DIVISIONS
        if in_division and not has_roof and row["rung"] != "division_band":
            raise Refused(f"{hh['id']}: its record names the {hh['division']} division "
                          f"and it sits at rung {row['rung']!r}")
        if not in_division and row["rung"] == "division_band":
            raise Refused(f"{hh['id']}: banded into a division its record does not name")

    # 11 (T-1522, replacing T-1512's). No household is owed a seat any more: rung 5 is
    # dealt, so every household stands on a rung of the ladder.
    for row in rows:
        if row["kind"] == "household" and row["rung"] == "owed":
            raise Refused(f"{row['id']}: a household is still owed a seat. Rung 5 is "
                          "dealt now and every household reaches a rung of the ladder")

    # 13 (T-1522). Rung 5 is exactly the households nothing places, and every one of them
    # is banded into a division the order book's shape holds — never the fort.
    shape = division_shape()
    nowhere = {hh["id"] for hh in household_records()
               if not (hh.get("lives_at") or {}).get("value")
               and (hh.get("division") or "unplaced") == "unplaced"}
    dealt_rows = [r for r in rows if r["rung"] == "policy_only"]
    if {r["id"] for r in dealt_rows} != nowhere:
        raise Refused("rung 5 is not the households whose record places them nowhere — "
                      "a dealt band may not reach a household some source does place")
    clauses_held = policy_clauses()
    for row in dealt_rows:
        seat = row["seat"]
        if not seat or seat["kind"] != "division_band":
            raise Refused(f"{row['id']}: rung 5 and no band under it")
        if seat["division"] not in shape:
            raise Refused(f"{row['id']}: dealt into {seat['division']!r}, which the order "
                          "book's household shape does not hold")
        if seat["division"] == NOT_DEALT:
            raise Refused(f"{row['id']}: dealt into the garrison's reservation. A "
                          "household no source places is never put inside the fort")
        if seat["clause"] not in clauses_held:
            raise Refused(f"{row['id']}: dealt the clause {seat['clause']!r}, which the "
                          "committed placement policy does not hold")
        if seat["clause"] not in set(COLUMN_CLAUSE.values()):
            raise Refused(f"{row['id']}: dealt a clause no column of the town model's "
                          "employment distribution maps to")
        if seat["id"] != f"{seat['division']}/{seat['clause']}":
            raise Refused(f"{row['id']}: its band does not name its own division and clause")
        if row["tier"] != "reconstructed":
            raise Refused(f"{row['id']}: a dealt band is reconstruction and must say so")
        if not row["seed"] or "division:" not in row["seed"] or "class:" not in row["seed"]:
            raise Refused(f"{row['id']}: a dealt band must carry the digest that placed "
                          "it, on both axes")
        if row["owed_to"]:
            raise Refused(f"{row['id']}: rung 5 is dealt, so it owes nobody a seat")
        if "dealt" not in row["words"]:
            raise Refused(f"{row['id']}: a dealt band whose words do not say it is dealt")

    # 14 (T-1522). The deal is EXACT: the dealt totals are the committed shape, to the
    # person, on both axes. A drift here is a re-deal nobody asked for.
    total = len(dealt_rows)
    book_total = sum(shape.values())
    want_division = largest_remainder({k: shape[k] / book_total for k in shape}, total)
    got_division: dict[str, int] = {}
    for row in dealt_rows:
        got_division[row["seat"]["division"]] = got_division.get(row["seat"]["division"], 0) + 1
    if got_division != want_division:
        raise Refused(f"the dealt divisions {got_division} are not the order book's "
                      f"household shape {want_division}")
    clause_shares, refusals = class_shape()
    want_clause = largest_remainder(clause_shares, total)
    got_clause: dict[str, int] = {}
    for row in dealt_rows:
        got_clause[row["seat"]["clause"]] = got_clause.get(row["seat"]["clause"], 0) + 1
    if got_clause != want_clause:
        raise Refused(f"the dealt classes {got_clause} are not the town model's "
                      f"employment distribution {want_clause}")

    # 15 (T-1522). The file says what it dealt, and what it says is what it did.
    record = doc.get("policy_only_deal") or {}
    if record.get("households") != total:
        raise Refused("the deal's own record does not count the rows it dealt")
    if record.get("division", {}).get("target_by_division") != shape:
        raise Refused("the deal's record states a division shape the order book does not")
    if record.get("division", {}).get("dealt") != dict(sorted(got_division.items())):
        raise Refused("the deal's record states divisions it did not deal")
    if record.get("class", {}).get("dealt") != dict(sorted(got_clause.items())):
        raise Refused("the deal's record states classes it did not deal")
    if [r["column"] for r in record.get("class", {}).get("refused_columns") or []] \
            != [r["column"] for r in refusals]:
        raise Refused("the deal's record does not name the columns it refused")
    if record.get("still_owed_to") is not None:
        raise Refused("the carry-back onto the household record was spent by "
                      f"{CARRIED_BACK_BY}, so the deal may not still record it as owed")
    if record.get("carried_back_by") != CARRIED_BACK_BY:
        raise Refused("the deal must name the ticket that carried it onto the household "
                      "card, or a reader cannot tell a spent deal from an unspent one")

    # 16 (T-1522). The deal is nothing but a shape borrowed from the order book. It
    # spends no bucket, so no bucket of the book may name this ticket as a filler.
    for fill in order_book().get("fills") or []:
        if fill.get("ticket") in ("T-1513", "T-1522"):
            raise Refused("the order book records a fill against the policy-only deal. "
                          "These households are already in the layer; this pass mints "
                          "nobody and may not spend a bucket")

    # 12 (T-1512). No reconstructed seat carries a coordinate, a lot or a roof.
    for row in rows:
        seat = row["seat"]
        if not seat or row["tier"] != "reconstructed":
            continue
        for forbidden in ("lot", "lot_id", "coordinates", "local_enu_m", "structure",
                          "structure_id", "position"):
            if forbidden in seat:
                raise Refused(f"{row['id']}: a reconstructed seat has grown a "
                              f"{forbidden!r} — this pass invents no ground")

    # 16 (T-1618). The dealt roof is the two seats files, restated — and it re-grades
    # nothing. Six limits, because six different things could go wrong here and five of
    # them would look like an improvement.
    dealt_rows = {r["id"]: r for r in rows if r.get("dealt_roof")}
    from_files: dict[str, dict] = {}
    for path, ticket, _ground in DEALT_SEAT_FILES:
        doc_seats = read_json(path)
        for seat in doc_seats["seats"]:
            if seat["id"] in from_files:
                raise Refused(f"{seat['id']}: seated twice across the seats files — a "
                              "household stands in one place")
            from_files[seat["id"]] = {**seat, "_ticket": ticket}
        stated = doc_seats["counts"]["seated"]
        here = sum(1 for r in rows if (r.get("dealt_roof") or {}).get("dealt_by") == ticket)
        if here != stated:
            raise Refused(f"{path.name}: it seats {stated} and {here} row(s) carry that "
                          "deal — the book has fallen behind the deal")
    if set(dealt_rows) != set(from_files):
        loose = sorted(set(dealt_rows) - set(from_files))[:3]
        short = sorted(set(from_files) - set(dealt_rows))[:3]
        raise Refused("the rows carrying a dealt roof are not the households the seats "
                      f"files seat (invented {loose}, dropped {short})")
    taken: dict[str, str] = {}
    for row_id, row in dealt_rows.items():
        deal = row["dealt_roof"]
        if deal["structure_id"] and deal["structure_id"] not in committed:
            raise Refused(f"{row_id}: dealt {deal['structure_id']}, which is not a "
                          "committed structure — no roof may be invented here")
        if deal["structure_id"]:
            if deal["structure_id"] in taken:
                raise Refused(f"{row_id}: dealt {deal['structure_id']}, which "
                              f"{taken[deal['structure_id']]} already stands under")
            taken[deal["structure_id"]] = row_id
            if deal["owed_to"]:
                raise Refused(f"{row_id}: its roof is standing and it still owes one")
        elif deal["owed_to"] != OWED_SLOT_BUILD:
            raise Refused(f"{row_id}: the deal requested a slot and does not say who "
                          "raises it — nobody can be taken to a roof that is not built")
        if deal["how"] not in ("adopted", "slot"):
            raise Refused(f"{row_id}: {deal['how']!r} is not a way this policy deals a roof")
        if not deal["substitutable"]:
            raise Refused(f"{row_id}: a policy-dealt roof is substitutable by "
                          "construction, and a row that stops saying so is claiming "
                          "the record put the household there")
        if not deal["words"]:
            raise Refused(f"{row_id}: a dealt roof with nothing to say on a card")
        # The one that matters most: the deal must not have climbed the ladder.
        if row["rung"] not in ("division_band", "policy_only"):
            raise Refused(f"{row_id}: rung {row['rung']!r} carries a policy deal. The "
                          "deal is dealt to the rows the evidence does NOT place, and "
                          "carrying it is not a rung.")
        if not row["seat"] or row["seat"]["kind"] != "division_band":
            raise Refused(f"{row_id}: the deal has moved its seat off the band. The "
                          "seat is the ladder's and the deal never re-grades it.")
        if row["tier"] != "reconstructed":
            raise Refused(f"{row_id}: a dealt row that stops calling itself "
                          "reconstruction")
        # Asked LAST, so the limits above are the ones a broken row meets first and the
        # self-test can reach every one of them. This is the restatement check: the deal
        # on the row is the deal in the file, roof for roof and clause for clause.
        seat = from_files[row_id]
        for field, in_file in (("structure_id", seat.get("structure_id")),
                               ("how", seat["how"]), ("family", seat["family"]),
                               ("clause", seat["clause"]), ("district", seat["district"]),
                               ("deal_seed", seat["seed"]), ("why", seat["why"])):
            if deal[field] != in_file:
                raise Refused(f"{row_id}: its dealt {field} is not the one "
                              f"{deal['dealt_by']} dealt it")

    # And a roof the record ALREADY seats somebody at is not the policy's to deal.
    # THIS ONE IS NOT SELF-TESTABLE FROM A ROW, and it is kept anyway. Every way of
    # breaking it by editing a row is caught first by the restatement check above, so
    # `--self-test` reaches it through no mutation; what it actually guards is the two
    # SEATS FILES, which are regenerated by T-1613 and T-1614 and could deal a roof
    # somebody's own record already stands under. The self-test for it is that the
    # seats files carry their own `roofs_held_back` list for exactly this reason.
    by_record = {r["seat"]["id"] for r in rows
                 if r["seat"] and r["seat"]["kind"] == "structure"}
    clash = sorted(set(taken) & by_record)
    if clash:
        raise Refused(f"the policy dealt {clash[:3]}, which a household or firm already "
                      "stands under on its own record's say-so")

    # 7b. The ledger that would fill rung 2 is re-read to say so.
    ledger = read_json(LOT_ADDRESSES)["addresses"]
    claimed = next(v for v in doc["vocabulary"]["rungs"] if v["rung"] == "lot")
    if str(len(ledger)) not in claimed["stands_empty_because"]:
        raise Refused("the lot ledger has changed size and the rung still claims the old "
                      "one — re-read it before saying the rung is empty")

    # 8. The counts are what the rows say.
    fresh = build()["counts"]
    if fresh != doc["counts"]:
        raise Refused("the committed counts are not what the rows say")


def report(doc: dict) -> str:
    c = doc["counts"]
    out = [f"{c['rows']} rows — {c['households']} households, {c['businesses']} firms",
           f"  seated: {c['seated']}    owed: {c['owed']}"]
    for rung, n in c["by_rung"].items():
        out.append(f"  rung {rung:<12} {n}")
    for reach, n in c["by_reach"].items():
        out.append(f"  reach {reach:<11} {n}")
    return "\n".join(out) + "\n"


def check() -> int:
    committed = read_committed()
    if committed is None:
        print(f"REFUSED: {OUT.relative_to(ROOT)} is missing or unreadable — run --build")
        return 1
    fresh = build()
    if fresh["rows"] != committed["rows"]:
        fresh_by = {r["id"]: r for r in fresh["rows"]}
        old_by = {r["id"]: r for r in committed["rows"]}
        added = sorted(set(fresh_by) - set(old_by))
        gone = sorted(set(old_by) - set(fresh_by))
        changed = sorted(k for k in set(fresh_by) & set(old_by)
                         if fresh_by[k] != old_by[k])
        print("REFUSED: a rebuild would not produce the committed address book.")
        for label, items in (("added", added), ("gone", gone), ("changed", changed)):
            if items:
                print(f"  {label} ({len(items)}): {', '.join(items[:5])}"
                      + (" ..." if len(items) > 5 else ""))
        return 1
    try:
        assertions(committed)
    except Refused as exc:
        print(f"REFUSED: {exc}")
        return 1
    c = committed["counts"]
    print(f"{c['rows']} address-book rows — {c['seated']} seated, {c['owed']} owed; "
          f"by rung {c['by_rung']}")
    return 0


def self_test() -> int:
    """Break each limit and require its assertion to fire."""
    doc = read_committed() or build()
    faults = []
    FIRED: list[str] = []

    def fires(name, mutate):
        FIRED.append(name)
        broken = json.loads(json.dumps(doc))
        mutate(broken)
        try:
            assertions(broken)
        except Refused as exc:
            print(f"  fires: {name} -> {str(exc)[:110]}")
            return
        faults.append(name)

    def pick(kind, rung):
        return lambda d: next(r for r in d["rows"]
                              if r["kind"] == kind and r["rung"] == rung)

    def duplicate(d):
        d["rows"].append(json.loads(json.dumps(d["rows"][0])))

    def a_household_vanishes(d):
        d["rows"].remove(pick("household", "policy_only")(d))

    def a_firm_vanishes(d):
        d["rows"].remove(pick("business", "unplaceable")(d))

    def an_invented_seat(d):
        pick("household", "policy_only")(d)["seat"] = {"kind": "structure",
                                                       "id": "a_building_nobody_holds"}

    def an_owed_row_takes_a_roof(d):
        row = next(r for r in d["rows"] if r["rung"] == "owed")
        row["seat"] = {"kind": "structure", "id": sorted(committed_structures())[0]}

    def an_owed_row_owes_nobody(d):
        next(r for r in d["rows"] if r["rung"] == "owed")["owed_to"] = None

    def a_row_says_nothing(d):
        pick("household", "policy_only")(d)["words"] = ""

    def a_row_cannot_be_retired(d):
        pick("business", "unplaceable")(d)["replaceable_by"] = ""

    def a_firm_changes_rung(d):
        pick("business", "unplaceable")(d)["rung"] = "face"

    def an_unplaceable_firm_is_seated(d):
        row = pick("business", "unplaceable")(d)
        row["rung"] = "structure"
        row["reach"] = "structure"

    def a_household_is_seated_from_nowhere(d):
        row = pick("household", "policy_only")(d)
        row["rung"] = "structure"
        row["seat"] = {"kind": "structure", "id": sorted(committed_structures())[0]}

    def a_row_climbs_to_rung_two(d):
        pick("household", "policy_only")(d)["rung"] = "lot"

    def the_lot_ledger_claim_goes_stale(d):
        claimed = next(v for v in d["vocabulary"]["rungs"] if v["rung"] == "lot")
        claimed["stands_empty_because"] = "the ledger carries 99 addresses and names nobody"

    def the_counts_drift(d):
        d["counts"]["seated"] += 1

    # ---- T-1512's own limits ---- #

    def a_band_moves_a_household(d):
        row = pick("household", "division_band")(d)
        other = next(v for v in TOWN_DIVISIONS if v != row["seat"]["division"])
        row["seat"] = {**row["seat"], "division": other, "id": f"{other}/x"}

    def a_band_cites_a_clause_the_policy_lacks(d):
        row = pick("household", "division_band")(d)
        row["seat"] = {**row["seat"], "clause": "a_clause_nobody_wrote"}

    def a_band_loses_its_tier(d):
        pick("household", "division_band")(d)["tier"] = "inferred"

    def a_band_loses_its_seed(d):
        pick("household", "division_band")(d)["seed"] = None

    def a_household_in_a_division_is_left_owed(d):
        row = pick("household", "division_band")(d)
        row["rung"], row["seat"], row["owed_to"] = "owed", None, OWED_CARRY_BACK

    def an_unplaced_household_is_banded(d):
        row = pick("household", "policy_only")(d)
        row["rung"] = "division_band"
        row["seat"] = {"kind": "division_band", "id": "south/x",
                       "division": "south", "clause": None}
        row["tier"], row["seed"] = "reconstructed", "x"

    # ---- T-1522's own limits ---- #

    def a_household_is_left_owed(d):
        row = pick("household", "policy_only")(d)
        row["rung"], row["seat"], row["owed_to"] = "owed", None, OWED_CARRY_BACK

    def a_dealt_band_lands_in_the_fort(d):
        row = pick("household", "policy_only")(d)
        row["seat"] = {**row["seat"], "division": NOT_DEALT,
                       "id": f"{NOT_DEALT}/{row['seat']['clause']}"}

    def a_dealt_band_takes_a_clause_off_the_distribution(d):
        row = pick("household", "policy_only")(d)
        row["seat"] = {**row["seat"], "clause": "commercial_front",
                       "id": f"{row['seat']['division']}/commercial_front"}

    def a_dealt_band_loses_its_digest(d):
        pick("household", "policy_only")(d)["seed"] = "T-1522"

    def a_dealt_band_stops_saying_it_was_dealt(d):
        pick("household", "policy_only")(d)["words"] = "This household lived somewhere."

    def the_deal_drifts_off_the_book_shape(d):
        rows = [r for r in d["rows"] if r["rung"] == "policy_only"]
        a = next(r for r in rows if r["seat"]["division"] == "south")
        a["seat"] = {**a["seat"], "division": "west",
                     "id": f"west/{a['seat']['clause']}"}

    def the_record_misstates_the_shape(d):
        d["policy_only_deal"]["division"]["target_by_division"] = {"south": 1}

    def the_record_forgets_who_carried_it_back(d):
        d["policy_only_deal"]["carried_back_by"] = None

    def the_record_calls_a_spent_carry_back_owed(d):
        d["policy_only_deal"]["still_owed_to"] = OWED_CARRY_BACK

    def a_face_firm_moves_street(d):
        row = next(r for r in d["rows"]
                   if r.get("adjudicated_grade") == "street_only_unseated")
        row["seat"] = {**row["seat"], "id": "a_street_the_paper_did_not_print"}

    def a_face_firm_stops_saying_it_is_reconstruction(d):
        row = next(r for r in d["rows"]
                   if r.get("adjudicated_grade") == "street_only_unseated")
        row["tier"] = "inferred"

    def a_reconstructed_seat_grows_a_lot(d):
        row = pick("household", "division_band")(d)
        row["seat"] = {**row["seat"], "lot": "blk_16_lot_7"}

    def a_dealt_row(d):
        return next(r for r in d["rows"] if r.get("dealt_roof"))

    def a_dealt_roof_the_dataset_lacks(d):
        a_dealt_row(d)["dealt_roof"]["structure_id"] = "a_building_nobody_holds"

    def two_households_under_one_roof(d):
        rows_ = [r for r in d["rows"] if (r.get("dealt_roof") or {}).get("structure_id")]
        rows_[1]["dealt_roof"]["structure_id"] = rows_[0]["dealt_roof"]["structure_id"]

    def a_deal_invented_from_nowhere(d):
        row = next(r for r in d["rows"] if not r.get("dealt_roof")
                   and r["rung"] == "policy_only")
        row["dealt_roof"] = json.loads(json.dumps(a_dealt_row(d)["dealt_roof"]))

    def a_dealt_row_climbs_the_ladder(d):
        # The seat, and not the rung: assertion 6 already refuses a rung-1 household
        # the records do not seat, so this breaks the limit 16 actually owns — the
        # ladder's own seat quietly replaced by the roof the policy dealt.
        row = a_dealt_row(d)
        row["seat"] = {"kind": "structure", "id": row["dealt_roof"]["structure_id"]}

    def a_dealt_roof_stops_being_substitutable(d):
        a_dealt_row(d)["dealt_roof"]["substitutable"] = False

    def a_dealt_roof_that_misquotes_the_file(d):
        taken = {(r.get("dealt_roof") or {}).get("structure_id") for r in d["rows"]}
        taken |= {(r["seat"] or {}).get("id") for r in d["rows"] if r["seat"]}
        spare = next(x for x in sorted(committed_structures()) if x not in taken)
        a_dealt_row(d)["dealt_roof"]["structure_id"] = spare

    def a_deal_takes_a_roof_a_record_already_seats(d):
        row = next(r for r in d["rows"]
                   if r["seat"] and r["seat"]["kind"] == "structure")
        a_dealt_row(d)["dealt_roof"]["structure_id"] = row["seat"]["id"]

    def a_slot_forgets_who_builds_it(d):
        next(r for r in d["rows"] if r.get("dealt_roof")
             and not r["dealt_roof"]["structure_id"])["dealt_roof"]["owed_to"] = None

    def the_book_falls_behind_the_deal(d):
        a_dealt_row(d)["dealt_roof"] = None

    fires("a duplicated row", duplicate)
    fires("a household that loses its row", a_household_vanishes)
    fires("a firm that loses its row", a_firm_vanishes)
    fires("a seat the dataset does not hold", an_invented_seat)
    fires("an owed row that acquires a roof", an_owed_row_takes_a_roof)
    fires("an owed row that names no successor", an_owed_row_owes_nobody)
    fires("a row with nothing to say on a card", a_row_says_nothing)
    fires("a row nothing would retire", a_row_cannot_be_retired)
    fires("a firm whose rung stops restating the spend", a_firm_changes_rung)
    fires("an unplaceable firm that gets seated", an_unplaceable_firm_is_seated)
    fires("a household seated with no roof in its record", a_household_is_seated_from_nowhere)
    fires("a row that climbs to the empty rung 2", a_row_climbs_to_rung_two)
    fires("a stale reading of the lot-address ledger", the_lot_ledger_claim_goes_stale)
    fires("counts that drift from the rows", the_counts_drift)
    fires("a band that moves a household out of its own division", a_band_moves_a_household)
    fires("a band citing a clause the policy does not hold",
          a_band_cites_a_clause_the_policy_lacks)
    fires("a band that stops calling itself reconstruction", a_band_loses_its_tier)
    fires("a reconstructed band with no seed", a_band_loses_its_seed)
    fires("a household whose record names a division and is left owed",
          a_household_in_a_division_is_left_owed)
    fires("a household banded into a division its record does not name",
          an_unplaced_household_is_banded)
    fires("a face seat moved off the street the paper printed", a_face_firm_moves_street)
    fires("a roofless face seat that stops saying it is reconstruction",
          a_face_firm_stops_saying_it_is_reconstruction)
    fires("a reconstructed seat that grows a lot", a_reconstructed_seat_grows_a_lot)
    fires("a household left owed now that rung 5 is dealt", a_household_is_left_owed)
    fires("a dealt band put inside the garrison's reservation", a_dealt_band_lands_in_the_fort)
    fires("a dealt class no column of the model maps to",
          a_dealt_band_takes_a_clause_off_the_distribution)
    fires("a dealt band that loses the digest that placed it", a_dealt_band_loses_its_digest)
    fires("a dealt band whose words stop saying it was dealt",
          a_dealt_band_stops_saying_it_was_dealt)
    fires("a deal that drifts off the order book's shape", the_deal_drifts_off_the_book_shape)
    fires("a record that misstates the shape it dealt from", the_record_misstates_the_shape)
    fires("a record that forgets who carried the deal back",
          the_record_forgets_who_carried_it_back)
    fires("a record that still calls the spent carry-back owed",
          the_record_calls_a_spent_carry_back_owed)
    fires("a dealt roof the dataset does not hold", a_dealt_roof_the_dataset_lacks)
    fires("two households dealt the same roof", two_households_under_one_roof)
    fires("a deal on a row the seats files never seated", a_deal_invented_from_nowhere)
    fires("a dealt row that climbs the ladder on the strength of the deal",
          a_dealt_row_climbs_the_ladder)
    fires("a dealt roof that stops calling itself substitutable",
          a_dealt_roof_stops_being_substitutable)
    fires("a dealt roof that stops restating the seats file",
          a_dealt_roof_that_misquotes_the_file)
    fires("a deal moved onto a roof a committed record already seats somebody at",
          a_deal_takes_a_roof_a_record_already_seats)
    fires("a requested slot that names nobody to build it", a_slot_forgets_who_builds_it)
    fires("a book that has fallen behind the deal", the_book_falls_behind_the_deal)

    if faults:
        print("SELF-TEST FAILED — these assertions did not fire: " + ", ".join(faults))
        return 1
    print(f"all {len(FIRED)} assertions fire when broken")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if "--self-test" in argv:
        return self_test()
    if "--check" in argv:
        return check()
    if "--report" in argv:
        print(report(read_committed() or build()), end="")
        return 0
    if "--build" in argv:
        doc = build()
        assertions(doc)
        write(doc)
        print(f"wrote {OUT.relative_to(ROOT)}")
        print(report(doc), end="")
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
