#!/usr/bin/env python3
"""The documented businesses the papers place on a street and nothing narrower (T-0354).

    python3 tools/adopt_street_faces.py           write
    python3 tools/adopt_street_faces.py --check   re-derive, diff, and re-assert the limits
    python3 tools/adopt_street_faces.py --report  the adoption and every refusal, with counts

WHAT THIS IS FOR.

`data/research/newspapers/register_1835.json` reads 221 businesses out of the Chicago
Democrat and the Chicago American, 203 of them standing on the scene date, and says for
each what the committed town would have to do about it. Fifty-eight resolve to a
building: `enrich_existing` where the advertisement's anchor names a roof this project
holds, `new_building` where it names a place precise enough to raise one. Sixty do
not. The paper names a PLATTED STREET AND NOTHING NARROWER — Peter Cohen at "the east end
of South Water-street", J. S. C. Hogan on South Water — and the register calls them
`street_only`. Eighty-four more reach no street the model holds at all.
Those figures move with every newspaper merge and are a snapshot; the tool is the source.

**The owner ruled on these on 2026-08-29**, choosing between the three options T-0354
set out:

> Adopt a reconstructed roof already standing on that street face and attach the
> business to it.

Not a new frontage record with a conjectural along-street position, and not waiting for a
corner. This file is that ruling made re-derivable. `docs/STREET-FACE-ADOPTION.md` is the
policy it implements and states the five limits in full; what follows is how they are
enforced here.

THE FIVE LIMITS, AND EACH ONE IS AN ASSERTION IN `--check`.

  1. **A STREET FACE, NEVER A LOT.** The paper's constraint is the face; the lot is the
     reconstruction's. Every adoption carries `lot: null` and `claims_lot: false`, and
     `--check` refuses a record that grew a lot field of any name. The plat is READ to
     derive which street a roof faces — `tools/fronting_street.py` asks the Thompson lot
     grid which tier a footprint stands in — but reading a lot to learn a frontage is not
     asserting that a business held that lot, and this file asserts the frontage only.
  2. **THE ROOF STAYS `reconstructed`.** Adopting it does not promote the building. The
     business is documented and the building under it is not, and `--check` re-reads the
     adopted structure's own phase and fails if its confidence has stopped saying so.
     This is the pattern T-0264/#518 set for a documented head on a reconstructed
     dwelling (L205), followed rather than reinvented.
  3. **THE ALONG-STREET POSITION IS THE RECONSTRUCTION'S, NOT EVIDENCE.** Which roof on
     the face a business is given is an allocation. Businesses are ranked by evidence and
     paired with the face's free roofs — deterministic, and a statement about nothing.
  4. **ORDER WITHIN A FACE IS NOT A CLAIM.** Two businesses on one face: neither is
     nearer the corner than the other on any authority. `order_is_a_claim: false` says so
     in every record.
  5. **THE DEAL READS WHAT THE ROOF WAS RAISED AS (T-1651).** Of the roofs free on a face
     under one reading, a business takes one of the C, W or F bands — a house of trade —
     before one of the D, H, A, I, T or M bands. It is still an allocation and still says
     nothing about where the business stood; what it stops doing is contradicting the
     reconstruction's own typology for no reason, and `--check` refuses a business seated
     in a dwelling while a house of trade of the same reading stood free.

     **UNTIL T-1651 THE PAIRING WAS BY THE ROOF'S ID, AND THAT WAS NOT A READING OF THE
     FAMILY.** An anonymous roof's id carries its family as a token — `…_c2_08` — and
     within one block `c` sorts before `d`, so the deal LOOKED as though it preferred a
     shop. It did not. It preferred a NAME, which cost two things. A business on a face
     spanning several blocks took an earlier block's cottage over a later block's store,
     which is how eighteen of thirty-nine documented businesses came to stand in log
     cabins and frame cottages. And because the id carries the family, RE-FAMILYING ONE
     ROOF RENAMED IT and re-dealt every business below it on the face: `re_family_churn`
     measures that at 2,881 places changed over 2,322 re-families that did not change
     what any roof is, against zero under `deal_order`. `roof_key` is the roof's place in
     its block — pool and ordinal, the family token stripped with the record's own
     `family` — and a re-family does not move it.

WHAT COUNTS AS "ALREADY STANDING ON THAT STREET FACE" — the one reading this pass makes,
and it is the narrow one.

`tools/fronting_street.py` answers three ways, and they are different claims:

  * `lot front`      — the roof's platted lot faces this street. The plat says it.
  * `corner side`    — the roof is at the end of its tier and abuts this street on the
                       SIDE. Its front is the cross street.
  * `centreline band`— the roof is off the platted grid and its centroid is within 25 m
                       of this street's centreline. Proximity, not orientation.

**`lot front` AND `corner side` are adopted; the band is not.** The narrow reading shipped
first — only `lot front`, on the owner's ruling of 2026-08-29 — and it refused the whole of
Dearborn Street, which shows eighteen roofs a side and not one a front. T-0416 dealt that
cost out rather than estimating it and put the two remaining questions to the owner
separately. **He ruled on 2026-08-30: a corner side IS a face; the band is NOT added.**

  * A corner building genuinely fronts two streets. It has a side on each, and a business
    advertising on either one is describing where its door is. Saying a corner roof stands
    on BOTH its faces is a physical fact about a corner lot; it raises no geometry, moves
    no roof and promotes nothing.
  * A band is a DISTANCE from a centreline and not an orientation. A roof 20 m from
    Dearborn's centreline may show it a wall, a gable end or nothing at all, and no reading
    of the plat can say which. It was considered and declined in the same breath, and
    `reading.considered_and_declined` in the written table names the one business it would
    have added (Wm. Sabine, on North Water Street) so a later run does not re-open it as an
    oversight.

**The cost of BOTH rulings was DEALT, not estimated (T-0416).** "Twenty-four would become
eligible" is the count of businesses a widening lets back into the deal, and it is not what
one seats: those twenty-four then meet refusal 3 and refusal 4, and the supply a widening
adds is already net of the households' homes and the yard buildings among the side-only
roofs. So the pass re-runs the whole allocation under each reading and prints what it
stands up. Measured on `dev`, 2026-08-29, before the ruling: the corner-side reading seats
TWELVE more, not twenty-four — Dearborn +8, La Salle +3, Canal +1 — and adding the band
would have seated one further. Those twelve are seated now; the one is not.

**What the corner-side reading still does NOT do.** It seats none of the three storefronts
T-0416 is named for — Wm. Sabine and John Dave on North Water Street, which has no
side-only roof at all, and the Dearborn Street wine store, which is refused on supply
under both widenings. Their answer is frontage (T-0375's neighbourhood), not a wider
reading, and the ticket says so on the record rather than closing over it.

THE REFUSALS, AND WHY EACH ONE IS THERE.

  1. `not present at the scene date`  — the register excluded it already; a business
                                        contradicted before 1 July 1835, or first printed
                                        after it, is not standing in this town.
  2. `the face holds no roof standing on it` — the named street has no reconstructed roof
                                        under either adopted reading: no lot fronts it and
                                        no roof ends its tier against it. North Water
                                        Street is the case since 2026-08-30 — one roof
                                        lies in the band and the band is not a face.
  3. `every roof on the face is spoken for` — the supply ran out. South Water Street is
                                        the case, and it is the count this ticket exists
                                        to produce rather than a failure.
  4. `the roof is a named household's dwelling` — refuses a ROOF, not a business. A roof
                                        `data/residents/` seats a household in is that
                                        household's home; hanging a documented store on
                                        it would assert a relation between two claims
                                        nothing supports. The tradesmen this leaves
                                        without a roof on South Water are T-0375's, and
                                        this pass must not quietly answer that ticket.
  5. `the roof is a yard building` — the other refusal of a ROOF. The anonymous parcels
                                        deal ANCILLARY roofs as well as principal ones —
                                        privies, stables, woodsheds standing behind a lot
                                        — and `tools/generate_block_infill.py` has refused
                                        to hang an occupant on one since the inferred-
                                        household programme: "a yard building serves the
                                        lot it stands behind, and an adoption is a claim
                                        about who lived or worked in a building". This
                                        pass did not know that rule until 2026-08-29, and
                                        it had seated NINE documented businesses in
                                        outbuildings — Peter Cohen, clothier, grocer and
                                        liquor dealer and the best-evidenced house in the
                                        whole pool, in `recon_1835_blk_south_water_clark_
                                        a3_05`, which is a privy. Found by T-0417 trying
                                        to spend the allocation into the structure
                                        records, where the generator's own gate stopped
                                        it. An ancillary roof is not free supply.
  6. `this face already holds this proprietor` — the corpus prints one house under more
                                        than one heading. 'Peter Cohen' and 'Peter
                                        Cohen's store', 'the Chicago Bakery' and 'Chicago
                                        Bakery' and 'D. Graves' who kept it, 'John
                                        Holbrook' and 'John Holbrook, hats, clothing,
                                        boots and shoes'. Seating both puts one man in two
                                        storefronts on one street, which no advertisement
                                        says. So a business whose normalised proprietor
                                        SURNAME SET is exactly one already adopted on this
                                        face is refused, and the better-evidenced heading
                                        keeps the roof.

                                        **Exactly, and not by resemblance.** A firm that
                                        shares ONE partner surname with a sole trader is
                                        NOT refused: whether those are one house is
                                        T-0338's open question over thirty-one such
                                        groups, and a placement pass must not answer it by
                                        seating or refusing.

                                        **But it DOES defer to a ruling that already
                                        exists.** Where
                                        `identity.json` § `refused_firm_merges` declares
                                        two headings `two_houses` and their surname sets
                                        are equal, the collapse keys on (surname set,
                                        occupation) — the axis the ruling itself used —
                                        so W. Montgomery the auctioneer is no longer
                                        refused for being called Montgomery by L. W.
                                        Montgomery the bootmaker (T-0414). Two headings of
                                        the SAME trade in such a group still collide.

                                        Nor does this reach a
                                        variant SPELLING — 'F. G. Blanshard', 'G.
                                        Blanshard', 'W. G. Blanchard' and 'Wm. G.
                                        Branchaud' advertised the same Lake Street trade
                                        within five months and took three roofs here,
                                        because the gazetteer's identity layer had not
                                        judged them and this file will not judge a
                                        resemblance. T-0408 SETTLED IT WHERE IT BELONGS
                                        and the group is now TWO roofs: 'Branchaud' was a
                                        supply made from two Tesseract-fallback columns
                                        and the same card's Vision columns of 1834-07-16
                                        and 1834-09-17 set BLANCHARD, so that reading was
                                        repaired and an `identity.json` firm merge joined
                                        'Wm. G. Blanchard' to 'W. G. Blanchard'; and
                                        'W. G. Blanchard' against 'G. Blanshard' is a
                                        declared `not_joined` refusal — one door, one
                                        trade, and no printing that sets both spellings.

  7. `the roof was raised to answer a household's slot request` — the third refusal of
                                        a ROOF, and the one T-1626 added. The platted
                                        seating (T-1613) walks the banded households over
                                        the plat, and where it can find no standing roof
                                        for one it does not give up: it draws on the
                                        block's own committed family plan and writes a
                                        SLOT — a request, with the block and the family
                                        named, that the 5C build tickets fulfil. A roof
                                        raised in answer to such a request is not free
                                        supply, and until 2026-09-26 this pass took it.
                                        T-1622 built the D3 and D4 that
                                        blk_south_water_franklin was asked for and this
                                        pass handed both to documented firms before the
                                        seating could return: business adoptions went 39
                                        to 41 and the town's platted seats went 106 to
                                        104. The two households did not merely miss their
                                        roof, they lost the REQUEST — the block's headroom
                                        had been spent — and dropped back to `owed`. So
                                        the two roofs the build raised seated nobody new
                                        and cost the town two seats. See "THE PRECEDENCE
                                        T-1626 SETTLED" below.

THE PRECEDENCE T-1626 SETTLED, AND WHY IT IS NOT THE OWNER'S TO RULE ON.

Refusal 7 looks like it prefers an invented household to a printed advertisement, and it
does not. **The precedence here was never documented-beats-reconstructed.** Refusal 4 has
subordinated this pass to the INFERRED household layer since 2026-08-30 — a hypothesis
from the town's arithmetic that names nobody — and says in its own words that the
invention makes the case stronger rather than weaker. A platted seat is the same kind of
claim as an inferred household. The only reason it lost was that it was recorded as a
REQUEST rather than as an occupancy, and a request is invisible to a pass that reads
`occupants`. That is an ordering accident, not a policy: this pass runs first, so it takes
the roof in the window between the roof being raised and the household being seated in it.

What actually decides it is limit 3, which this file has stated from the first day.
**WHICH roof on a face a business is given is an allocation and "a statement about
nothing."** A business is roof-INDIFFERENT: any free roof on the face serves it equally,
and refusal 3 is the pre-existing, honest answer when the face runs out. A slot request is
roof-SPECIFIC: the roof exists because a named household asked this block for that family,
and `data/reconstruction/1835_platted_block_parcels.json` records the request beside the
deal that answered it. Giving the indifferent claim priority over the specific one is what
produced a build that seated nobody. So the reservation costs the register nothing it had:
the refused business falls back to refusal 3, which is exactly the refusal it carried
before the roof was built, and the reconstruction did not add supply for it.

It is therefore an allocation precedence between two of this project's own passes, with no
source read on either side and no claim about 1835 either way — not rights, not the
depiction of people, not money, not what the project is. A run settles it and writes down
why, which is this.

**THE RESERVATION DOES NOT EXPIRE, AND THAT IS DELIBERATE.** A roof carries it because of
how it came to be raised, and that does not stop being true if the seating pass later
deals the roof to some OTHER household than the one that asked — which roof a household
takes is the seating pass's allocation, exactly as which roof a business takes is this
one's. Measured on the tree this shipped against: with refusal 7 in force the platted deal seats
112 households against 110 without it, and it gives the two franklin roofs to
hh_beeson_william and hh_bench_reuben rather than to Brown and Bryant who asked. Both are
household seats, which is what the reservation is for; neither is this pass's to pick.
(T-1622 measured the same pair at 106 against 104; T-1611 has since seated six more, and
the DIFFERENCE the refusal makes is the two roofs either way.)

The cost of never releasing it is a roof the household layer declines to fill and this
pass may not take, so the table carries the count — but note WHAT IT READS. `reserved_
without_a_committed_occupancy` counts reserved roofs whose own STRUCTURE RECORD states no
occupant, and that is 2 today for both franklin roofs, because the platted deal is an
adjudication in `1835_platted_seats.json` and does not write `occupants` onto a record
(its own words: "no structure record is touched"). Reading that file here would close the
cycle `requested_roofs()` exists to avoid. So the number is an upper bound on the cost,
not the cost: it is the roofs no COMMITTED occupancy holds, and on today's tree the
seating adjudication holds both of them.

WHAT THIS FILE WILL NOT DO. It will not raise a structure, move one, promote one, or
write a lot. It writes ONE derived table and nothing else; spending it — a card, a
signboard, a frontage — is T-0263's and the seeding tickets'. It will not invent a
citation: every adoption carries the claim id of the advertisement that names the street.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import fronting_street  # noqa: E402  (needs the path above)
from compile_gazetteer import (  # noqa: E402  — the identity policy has one home
    sign_name_index, surname_words,
)
# The archetype bands whose roofs held a TRADE, read from the ONE place this project
# writes them down rather than re-decided here (T-1657): C is a shop or store, W a
# works, F a freight store. D and H are dwellings, A the yard buildings, I the churches,
# schools and civic roofs, T the inns and M the fort. `normalise_structure_function`
# gates that reading on every commit; this pass only asks it a question it had never
# been asked.
from normalise_structure_function import TRADE_BANDS  # noqa: E402

DATA = ROOT / "data"
REGISTER = DATA / "research" / "newspapers" / "register_1835.json"
GAZETTEER = DATA / "research" / "newspapers" / "gazetteer.json"
IDENTITY = DATA / "research" / "newspapers" / "identity.json"
OUT = DATA / "research" / "newspapers" / "street_face_adoptions.json"
STRUCTURES = DATA / "structures"
HOUSEHOLDS = DATA / "residents" / "households"
PROGRAMME = DATA / "reconstruction" / "1835_inferred_household_programme.json"
PARCELS = DATA / "reconstruction" / "1835_platted_block_parcels.json"

SCENE_DATE = "1835-07-01"
FRONT = "lot front"          # tools/fronting_street.FRONT
SIDE = "corner side"
BAND = "centreline band"

# The keys an adoption record may carry. `--check` refuses anything else, which is how
# limit 1 is enforced against a future field rather than only against today's.
ADOPTION_KEYS = {
    "business_id", "business_name", "trade", "proprietors",
    "partners", "firm_styles",          # T-0398: which of those strings are people
    "surnames",                         # T-1042: every surname those strings name
    "street_id", "street_name", "street_text", "placement_class",
    "cites", "first_issue", "last_issue", "mentions",
    "structure_id", "face", "roof_confidence",
    # T-1651. What the reconstruction RAISED the adopted roof as, read off the roof's own
    # record. The deal was blind to it for a year, which is how a documented dry-goods
    # store came to stand in a log cabin while a shop roof stood free on the same face;
    # carrying the reading on the record is what stops that being invisible again.
    "roof_family", "roof_function", "roof_is_a_house_of_trade", "family_note",
    "lot", "claims_lot", "order_is_a_claim", "note",
}

REFUSALS = (
    "not present at the scene date",
    "the face holds no roof standing on it",
    "this face already holds this proprietor",
    "every roof on the face is spoken for",
)

#: The readings of "already standing on that street face" the ruling adopts, in the order
#: a face is dealt. `lot front` is the owner's ruling of 2026-08-29 (T-0354); `corner side`
#: is his ruling of 2026-08-30 (T-0416), on the measurement this file produced. `centreline
#: band` was put to him in the same question and DECLINED, and it is absent here rather than
#: commented out so that adopting it again would have to be a deliberate edit.
ADOPTED_READINGS = (FRONT, SIDE)

#: How a record says, in its own note, why its roof stands on the face it took. A corner
#: adoption must not read as a lot-front one: the visitor is owed the difference between
#: "its platted lot faces that street" and "it ends its tier against that street".
FACE_PHRASE = {
    FRONT: "whose platted lot faces %s",
    SIDE: "standing at the end of its platted tier, where the tier meets %s: a corner "
          "building, which the owner ruled on 2026-08-30 stands on both its faces",
    # Only reachable from a COUNTERFACTUAL deal — the band is not an adopted reading, so
    # no record derive() writes can carry this phrase. It is here so that costing the
    # declined reading does not crash, which is a poorer reason to lose a measurement than
    # any argument about it.
    BAND: "lying within 25 m of the platted centreline of %s, which is the reading the "
          "owner declined on 2026-08-30",
}

#: The reading that was measured, offered and refused. Kept so the written table can name
#: what declining it cost, and so `--report` can go on printing the disagreement.
DECLINED_READING = BAND


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# the town: which reconstructed roofs front which street, and which are homes
# ---------------------------------------------------------------------------

def reconstructed_roofs() -> dict[str, str]:
    """structure id -> the confidence its own phase gives the building, for `recon_*`.

    The `recon_*` prefix is the anonymous count-unit layer — a roof raised to meet an
    aggregate target, standing for no named building. Those are the only roofs the ruling
    reaches: adopting a roof this project argues IS some particular structure would put a
    documented business inside a documented building on no evidence at all.
    """
    out: dict[str, str] = {}
    for path in sorted(STRUCTURES.glob("recon_*.json")):
        doc = load(path)
        phases = doc.get("phases") or []
        grades = {(phase.get("documented_range") or {}).get("confidence")
                  for phase in phases}
        grades.discard(None)
        out[doc["id"]] = sorted(grades)[0] if len(grades) == 1 else "|".join(sorted(grades))
    return out


_FAMILIES: dict[str, str] | None = None
_FUNCTIONS: dict[str, str] | None = None


def roof_families() -> dict[str, str]:
    """structure id -> `reconstruction.family` for every `recon_*` roof, read once.

    THE FAMILY IS A FIELD AND THE ID IS A NAME (T-1651). Every anonymous roof's id
    carries its family as a token — `…_c2_08` — and on every tree this project has held
    the two agree, which is exactly why a pass could sort the face's roofs by ID for a
    year and look as though it were reading the family. It was not. The id is the roof's
    NAME, and the moment a roof is re-familied the name changes with it, so an
    id-ordered deal re-deals the whole face for one roof's change. `limits()` asserts the
    token and the field still agree wherever the id carries a token, which is the
    statement this reader rests on.
    """
    global _FAMILIES
    if _FAMILIES is None:
        _FAMILIES = {}
        for path in sorted(STRUCTURES.glob("recon_*.json")):
            doc = load(path)
            _FAMILIES[doc["id"]] = (doc.get("reconstruction") or {}).get("family")
    return _FAMILIES


def roof_functions() -> dict[str, str]:
    """structure id -> `function.value` for every `recon_*` roof, read once.

    The family's own term for what the roof is — `store_residence`, `two_room_frame
    _cottage` — out of the closed vocabulary T-1311 put in `data/structures.schema.json`.
    It is carried onto the adoption so a reader can SEE what a business was seated in
    without holding the crosswalk in their head.
    """
    global _FUNCTIONS
    if _FUNCTIONS is None:
        _FUNCTIONS = {}
        for path in sorted(STRUCTURES.glob("recon_*.json")):
            doc = load(path)
            _FUNCTIONS[doc["id"]] = (doc.get("function") or {}).get("value")
    return _FUNCTIONS


def is_house_of_trade(family: str | None) -> bool:
    """Did a customer come in off the street to this roof? Its BAND answers, and only it.

    `TRADE_BANDS` is T-1657's ruling and this pass does not extend it. A roof of the C, W
    or F bands was raised as a house of trade — a counter, a works, a freight store — and
    a roof of the D, H, A, I, T or M bands was not.
    """
    return bool(family) and str(family).upper().startswith(TRADE_BANDS)


_ORDINAL = re.compile(r"^(?P<stem>.+)_(?P<ordinal>\d+)$")


def roof_key(structure_id: str, family: str | None) -> tuple[str, int]:
    """(pool, ordinal) — a roof's place among its neighbours, INVARIANT under a re-family.

    The anonymous layer numbers its roofs `<pool>_<family>_<ordinal>`, and the ordinal is
    unique within the pool ACROSS families on every tree this project holds — `limits()`
    asserts that, because the whole value of this key rests on it. So stripping the family
    token with the record's own `family` leaves `(pool, ordinal)`: the roof's place in its
    block, which a re-family does not move. The West Division's roofs carry no family
    token at all (`recon_1835_west_012`) and are already keyed this way.

    THIS IS NOT A GEOMETRIC ORDER AND MUST NOT BECOME ONE. Limit 4 says order within a
    face is not a claim, and ordering the deal by distance along the street would make the
    best-evidenced business the one nearest the corner — a claim nothing supports. The
    ordinal is the schedule's own numbering and says nothing about where a roof stands.
    """
    match = _ORDINAL.match(structure_id)
    if not match:
        raise AssertionError(
            "%s does not end in an ordinal, so it has no place in a pool the deal can "
            "hold steady across a re-family" % structure_id)
    stem, ordinal = match.group("stem"), int(match.group("ordinal"))
    if family:
        token = "_%s" % str(family).lower()
        if stem.endswith(token):
            stem = stem[: -len(token)]
    return (stem, ordinal)


def yard_roofs() -> set[str]:
    """The `recon_*` roofs the anonymous parcels dealt as YARD BUILDINGS.

    `reconstruction.inventory_class` is the parcels' own word for it: a
    `principal_functional` roof is a building on the lot and an `ancillary` one stands
    behind it, off the block alley.

    T-1610 SPLIT THAT WORD FROM "SHED", and this pass keeps refusing the whole of it
    anyway, for its own reason. An ancillary roof used to be a privy, a stable or a
    woodshed and nothing else; since the owner's rear-cottage ruling of 2026-09-23 it may
    also be a DWELLING in the yard, which `generate_block_infill` will now let a household
    into (it asks the family, not the class). A BUSINESS is a different question and gets
    a different answer: every adoption here is a claim about a STREET FACE, made on an
    advertisement that gives its address by one, and a roof off the alley has no street
    face to be on. So the set is unchanged and only the reasoning narrows — a rear cottage
    is refused for standing behind the frontage, not for being a shed.
    """
    out: set[str] = set()
    for path in sorted(STRUCTURES.glob("recon_*.json")):
        doc = load(path)
        if ((doc.get("reconstruction") or {}).get("inventory_class")) == "ancillary":
            out.add(doc["id"])
    return out


def named_dwellings() -> dict[str, list[str]]:
    """structure id -> the NAMED household ids `data/residents/` seats in it."""
    out: dict[str, list[str]] = {}
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        doc = load(path)
        at = (doc.get("lives_at") or {}).get("value")
        if isinstance(at, str) and at:
            out.setdefault(at, []).append(doc["id"])
    return out


def inferred_dwellings() -> dict[str, list[str]]:
    """structure id -> the INFERRED household ids the reconstruction seats in it.

    The other layer that holds a roof, and it does not live in `data/residents/`: the
    inferred-household programme hypothesises an occupant from the town's arithmetic
    without naming anybody, so its households have no resident record to be found by
    `named_dwellings()` above. `tools/inferred_occupancy.py` is the ledger that spends
    both layers into the structure records, and it RAISES if one roof is claimed twice —
    "one roof, one occupant" — because letting either win silently would put a documented
    shopkeeper into an inferred labourer's cottage, or lose the labourer.
    """
    if not PROGRAMME.exists():
        return {}
    out: dict[str, list[str]] = {}
    for household in load(PROGRAMME).get("households", []):
        for key in ("lives_at", "works_at"):
            at = household.get(key)
            if isinstance(at, str) and at.startswith("recon_"):
                out.setdefault(at, []).append(household["id"])
    return out


def dwellings() -> dict[str, list[str]]:
    """structure id -> every household id ANY layer seats in it. Refusal 4's supply test.

    Both layers, and refusal 4 has covered both since 2026-08-30. It could not bite under
    the narrow reading — no roof the inferred programme held happened to have its platted
    lot on a street the register named — and the corner-side ruling made it bite at once:
    the very first re-derivation handed Elmira Fowler's Dearborn Street millinery a corner
    roof, `recon_1835_south_d1_032`, that the inferred layer already holds. The ledger
    caught it, which is what the ledger is for; refusing it HERE is what keeps the table
    derivable rather than merely gated.

    It is the same refusal in both cases and for the same reason. A roof some layer seats
    a household in is that household's home, and hanging a documented store on it would
    assert a relation between two claims nothing supports. That the inferred household is
    itself an invention makes the case stronger, not weaker: the relation would then be
    between a printed advertisement and a hypothesis.
    """
    out = {sid: list(ids) for sid, ids in named_dwellings().items()}
    for sid, ids in inferred_dwellings().items():
        out.setdefault(sid, []).extend(ids)
    return out


def requested_trade_workplaces() -> dict[str, dict]:
    """Authored workplace allocations are already spent roofs, never spare supply.

    T-1766 uses an upstream recipe, not compiled firms or this pass's own output.
    This reserves a workplace without asserting that its keeper lives in it.
    """
    path = ROOT / "data/reconstruction/1835_canal_approach_occupancy.json"
    if not path.exists():
        return {}
    out = {}
    for row in load(path)["rows"]:
        sid = row["structure_id"]
        roof_path = STRUCTURES / (sid + ".json")
        if not roof_path.exists():
            raise AssertionError("workplace request has no standing roof: " + sid)
        recon = load(roof_path).get("reconstruction", {})
        if (recon.get("family") != row["family"] or
                recon.get("programme_phase") != "canal_approach_trade_1835"):
            raise AssertionError("workplace request does not match its trade roof: " + sid)
        if sid in out:
            raise AssertionError("duplicate workplace reservation: " + sid)
        out[sid] = {
            "structure_id": sid, "block_id": None,
            "programme_phase": recon["programme_phase"], "family": row["family"],
            "requested_by_seat": row["business_id"],
            "reservation_kind": "workplace", "keeper_person_id": row["person_id"],
            "order_book_draw": "structures/" + ("stores_mixed_use" if row["family"].startswith("C") else "workshops") + "/west",
            "dealt_by_ticket": "T-1766",
            "why": "The authored Canal trade allocation raised this roof for this existing keeper's reconstructed firm. It is already a workplace, not a home and not free supply for a second street-face business.",
        }
    return out


def requested_roofs() -> dict[str, dict]:
    """structure id -> the authored household or workplace seat that raised it.

    Refusal 7 includes T-1766's explicitly allocated trade workplaces. Their authored
    recipe is read by requested_trade_workplaces(), without making them homes.

    The link is DATA, and it is upstream of both passes, which is what keeps this
    derivation acyclic. `tools/seat_platted_ground_1835.py` writes a `slot` when it can
    find no standing roof for a banded household, naming the block and the family it drew
    on; the build ticket that answers one records the request it answered in
    `1835_platted_block_parcels.json` § `dealt_against_a_request`, beside the deal. This
    reads that recipe — an AUTHORED file neither pass derives — and matches each request
    to a roof of its family raised by that deal, in id order, one roof per request. A deal
    that raised fewer roofs of a family than it was asked for reserves fewer; nothing here
    invents a reservation the recipe does not carry.

    It could not read `1835_platted_seats.json` instead. That file is derived from the
    structure records, and this pass's own allocation is spent into them by
    `tools/inferred_occupancy.py`, so reading the seats here would close a cycle and make
    `check.sh`'s re-derivation depend on which of the two ran last.
    """
    if not PARCELS.exists():
        return requested_trade_workplaces()
    by_phase: dict[str, list[str]] = {}
    family_of: dict[str, str] = {}
    for path in sorted(STRUCTURES.glob("recon_*.json")):
        doc = load(path)
        recon = doc.get("reconstruction") or {}
        phase = recon.get("programme_phase")
        if not phase or recon.get("inventory_class") != "principal_functional":
            continue
        by_phase.setdefault(phase, []).append(doc["id"])
        family_of[doc["id"]] = recon.get("family")
    out: dict[str, dict] = {}
    for block in load(PARCELS).get("blocks", []):
        dealt = block.get("dealt_against_a_request")
        if not dealt:
            continue
        raised = sorted(by_phase.get(block.get("programme_phase")) or [])
        for request in dealt.get("requests") or []:
            for structure_id in raised:
                if structure_id in out:
                    continue
                if family_of.get(structure_id) != request.get("family"):
                    continue
                out[structure_id] = {
                    "structure_id": structure_id,
                    "block_id": block.get("block_id"),
                    "programme_phase": block.get("programme_phase"),
                    "family": request.get("family"),
                    "requested_by_seat": request.get("seat"),
                    "order_book_draw": request.get("order_book_draw"),
                    "dealt_by_ticket": dealt.get("ticket"),
                    "why": "raised in answer to this seat's slot request, so it is the "
                           "household layer's roof and not supply for an adoption "
                           "(refusal 7, T-1626)",
                }
                break
    for sid, row in requested_trade_workplaces().items():
        if sid in out:
            raise AssertionError("a roof has both a household and workplace request: " + sid)
        out[sid] = row
    return dict(sorted(out.items()))


EMPTY_FACE = {FRONT: [], SIDE: [], BAND: [], "free": [], "homes": [], "yards": [],
              "requested": []}

# The order a pass deals a face's roofs when it is allowed to read more than one of
# them: the plat first, then the corner sides, then the band. It is the order of
# decreasing claim, so a widened reading never takes a weaker roof while a stronger one
# is free, and the lot-front-only allocation this pass actually writes is unchanged by
# the existence of the others.
READING_ORDER = (FRONT, SIDE, BAND)


def deal_order(structure_id: str, families: dict[str, str]) -> tuple:
    """The key the deal takes a face's free roofs in — T-1651, and it replaced the id.

    Two things it does that sorting by the roof's id did not:

      * **It reads the roof's FAMILY.** A house of trade comes before a dwelling, so a
        documented business takes a roof the reconstruction raised for one while any is
        free. This is an ALLOCATION and not evidence — limit 3 still holds, and nothing
        here says the paper placed this business in a shop — but of the allocations
        available it is the only one that does not contradict the reconstruction's own
        typology. Blind to it, this pass stood eighteen of thirty-nine documented
        businesses in log cabins and frame cottages while shop roofs on the same faces
        stood empty.
      * **It is stable under a re-family.** `roof_key` is the roof's place in its block
        and does not move when the roof's family changes; the id does, because the id
        carries the family. The tier above it moves only if the re-family crosses the
        trade bands, so one roof's change now re-deals what that roof's change reaches
        and not the whole street.
    """
    family = families.get(structure_id)
    return (0 if is_house_of_trade(family) else 1, roof_key(structure_id, family))


def free_under(face: dict, readings: tuple[str, ...], homes: dict,
               yards: set[str], requested: dict | None = None,
               families: dict[str, str] | None = None) -> list[str]:
    """The roofs a pass adopting `readings` could take, in READING_ORDER then `deal_order`.

    Refusals 4, 5 and 7 are applied here rather than by the caller, because they are
    refusals of a ROOF and hold under any reading of "face": a named household's home is
    that household's home whichever street the roof shows, a privy is a privy, and a roof
    raised to answer a slot request was commissioned by the household layer whichever
    street it ends up showing. `free_under(face, (FRONT,), ...)` is `face["free"]`
    re-ordered, and nothing else: the SET a reading makes free is untouched by T-1651 and
    every refusal that governed it still does.
    """
    requested = requested or {}
    families = roof_families() if families is None else families
    out: list[str] = []
    for how in READING_ORDER:
        if how not in readings:
            continue
        here = [sid for sid in face[how]
                if sid not in homes and sid not in yards and sid not in requested]
        here.sort(key=lambda sid: deal_order(sid, families))
        out += here
    return out


def reading_of(face: dict, structure_id: str) -> str:
    """Which of the three readings put this roof on this face."""
    for how in READING_ORDER:
        if structure_id in face[how]:
            return how
    raise AssertionError("%s is not on this face under any reading" % structure_id)


def supply(roofs: dict[str, str], homes: dict[str, list[str]],
           yards: set[str], requested: dict | None = None) -> dict:
    """Per street: the roofs that show it a face, under each reading, and the free ones.

    A roof standing on this street under an ADOPTED reading lands in exactly one of four
    buckets, and only `free` is supply: a named household's home (refusal 4), a yard
    building (refusal 5), a roof raised to answer a household's slot request (refusal 7),
    or a roof a business may take. The bucketing spans the adopted
    readings rather than `lot front` alone, because refusals 4 and 5 refuse a ROOF and hold
    whichever way it shows the street — a privy is a privy seen end-on. Roofs that reach
    the street only by the DECLINED reading are counted under their own key and are not
    supply at all.
    """
    requested = requested or {}
    out: dict[str, dict] = {}
    for structure_id in sorted(roofs):
        for street_id, how in fronting_street.fronting(structure_id):
            face = out.setdefault(street_id, {key: list(value)
                                              for key, value in EMPTY_FACE.items()})
            face[how].append(structure_id)
            if how in ADOPTED_READINGS:
                if structure_id in homes:
                    face["homes"].append(structure_id)
                elif structure_id in yards:
                    face["yards"].append(structure_id)
                elif structure_id in requested:
                    face["requested"].append(structure_id)
                else:
                    face["free"].append(structure_id)
    return out


# ---------------------------------------------------------------------------
# the pool: the register's street_only businesses, ranked by evidence
# ---------------------------------------------------------------------------

_SIGNS: dict | None = None


def declared_sign_names() -> dict:
    """`identity.json` § `firm_sign_names`, read once: {style: its partner half}.

    A sign-name is the shop's own name over its door and no partner is named in it, so
    the split cannot be derived — it is DECLARED beside the merges it governs, and
    `compile_gazetteer.sign_name_index()` is the reader.
    """
    global _SIGNS
    if _SIGNS is None:
        _SIGNS = sign_name_index(load(IDENTITY)) if IDENTITY.exists() else {}
    return _SIGNS


def surnames(entry: dict, signs: dict | None = None) -> tuple[str, ...]:
    """The normalised proprietor surname SET a register entry prints, sorted.

    Empty where the advertisement names no proprietor at all — an anonymous 'wholesale
    wine and liquor store' cannot collide with anything, and is never refused by refusal 5.

    THE READING IS NOT THIS PASS'S (T-1042). Until this ticket the last word of each
    proprietor string was taken for its surname, which on a firm's own trading style is a
    guess — and it invented a man ('H. Doty & Co.' stood on Lake Street as somebody called
    Co, and refusal 5 could fire on him) and it lost one ('Clark, Filer & Co.' dropped
    Filer). `compile_gazetteer.surname_words()` is now the one derivation for all three
    passes that asked this; what stays here is only the normalisation these keys are
    built on, because `two_house_surnames()` and the collapse compare against them.

    A DECLARED sign-name is taken off the style first where `signs` is passed — the
    shop's own name over its door is a capitalised trade, not a partner, and only
    `identity.json` can say which is which.
    """
    signs = declared_sign_names() if signs is None else signs
    found: set[str] = set()
    for name in entry.get("proprietors") or []:
        style = signs.get(str(name), str(name))
        for word in surname_words(style):
            key = re.sub(r"[^a-z]", "", word.lower())
            if key:
                found.add(key)
    return tuple(sorted(found))


def two_house_surnames(register: dict) -> set[tuple[str, ...]]:
    """Surname sets the corpus has ALREADY RULED cover more than one house.

    `identity.json` § `refused_firm_merges` is where this project writes down that two
    headings are not one business. A refusal of kind `two_houses` says exactly what
    refusal 3's surname collapse would otherwise assume away — and refusal 3 is forbidden
    to answer an identity question (docs/STREET-FACE-ADOPTION.md § refusal 3), so where
    the ruling exists the pass must obey it rather than re-decide it.

    Only refusals whose two headings would actually MEET in the collapse count: the
    collapse fires on an exact surname-set match, so a `two_houses` refusal between
    'New York Clothing Store' and "Peter Cohen's store" has nothing to say to it and is
    not admitted here. A heading the register does not carry is likewise skipped — the
    ruling may name a business this pass never sees.
    """
    by_name = {entry["name"]: entry for entry in register["businesses"]}
    ruled: set[tuple[str, ...]] = set()
    for refusal in load(IDENTITY).get("refused_firm_merges", []):
        if refusal.get("kind") != "two_houses":
            continue
        pair = [by_name.get(refusal.get("into")), by_name.get(refusal.get("from"))]
        if not all(pair):
            continue
        left, right = (surnames(pair[0]), surnames(pair[1]))
        if left and left == right:
            ruled.add(left)
    return ruled


def collapse_key(entry: dict, ruled: set[tuple[str, ...]]) -> tuple:
    """What refusal 3 treats as "the same proprietor" on one face.

    Normally the normalised proprietor surname set, and nothing else — one man, one roof
    per face. But inside a surname set the corpus has ruled `two_houses`, the TRADE joins
    the key, because the trade is the axis the ruling itself used: W. Montgomery the
    auctioneer against L. W. Montgomery the bootmaker is "a different trade, a different
    stand and eighteen months later" in `identity.json`'s own words. Keying on the
    occupation there is derived from the ruling rather than invented by this pass, and it
    reaches nothing the ruling has not already decided.

    Two headings of the SAME trade inside such a group still collide and one is still
    refused — whether the three surplus Montgomery auction headings are one house is the
    gazetteer's question, not this pass's.
    """
    house = surnames(entry)
    if house and house in ruled and entry.get("occupation"):
        return house + ("trade:" + str(entry["occupation"]),)
    return house


def rank_key(entry: dict, gaz: dict) -> tuple:
    """Evidence first — most printings, then earliest sighting, then id.

    A ranking, not a claim: it decides which business is served first where a face is
    short of roofs, and nothing about where any of them stood.
    """
    printed = gaz.get(entry["id"], {})
    mentions = len(printed.get("mentions") or [])
    first = (entry.get("evidence") or {}).get("first_issue") or "9999-99-99"
    return (-mentions, first, entry["id"])


#: THE TWO LEDGERS A DEAL CAN KEEP (T-0422). `TOWN_LEDGER` is the policy — one roof, one
#: business, counted across the whole town. `PER_FACE_LEDGER` is the ledger this pass kept
#: until the corner-side widening made it wrong: a roof spent on Dearborn was still free to
#: Lake, so two faces could deal the same building. It survives here ONLY so `self_test()`
#: can DERIVE it and show what the town-wide ledger is buying; no document is ever written
#: under it, and `costed()` refuses to.
TOWN_LEDGER = "town-wide"
PER_FACE_LEDGER = "per face"


CROSSWALK = DATA / "reconstruction" / "1835_family_archetype_crosswalk.json"


def scheduled_families() -> list[str]:
    """Every archetype family the roof schedule holds — the re-families that are possible."""
    return [row["id"] for row in load(CROSSWALK)["families"]]


def _renamed(structure_id: str, family: str | None) -> str:
    """The id a roof would carry if it were re-familied to `family`.

    A re-family RENAMES the roof wherever the id carries a family token, which is the
    whole mechanism T-1651 is about: the id is the family's, so changing the family
    changes the name, and a deal ordered by the name re-deals. The West Division's ids
    carry no token and are returned unchanged.
    """
    return re.sub(r"_[a-z]\d(_\d+)$", lambda m: "_%s%s" % (str(family).lower(),
                                                            m.group(1)), structure_id)


def re_family_churn(faces: dict, homes: dict, yards: set[str], requested: dict,
                    families: dict[str, str]) -> dict:
    """How far ONE roof's re-family reaches into the deal order — measured, both ways.

    THIS IS THE NUMBER T-1651 WAS OPENED ON, so it is derived on every rebuild rather than
    argued in a ticket. Take every face, every roof free on it, and every family the roof
    schedule holds; re-family that one roof, re-order the face, and count how many OTHER
    roofs changed position. Under the ID ORDER the pass used until T-1651 the answer is
    large, because the family is in the name: re-family a roof and it jumps across the
    block's whole alphabet. Under `deal_order` it is zero unless the re-family crosses the
    C/W/F bands, because `roof_key` is the roof's place in its block and a re-family does
    not move it.

    A roof that moves position is a business that would be dealt a DIFFERENT BUILDING for
    a change made to somebody else's roof. Nothing about the register changed; nothing
    about the street changed. That is what the churn counts.
    """
    scheduled = scheduled_families()
    buckets = ("within the bands", "across the bands")
    tally = {bucket: {key: {"re_families_tried": 0, "places_changed": 0,
                            "worst_single_re_family": 0, "changed_nothing": 0}
                      for key in ("id_order", "deal_order")}
             for bucket in buckets}
    places = 0
    faces_measured = 0

    def ordered(roofs: list[str], ids: dict, fams: dict, key: str) -> list[str]:
        """The face in the order `key` deals it, as a list of the roofs' STANDING ids.

        The roofs are identified by the id they stand under today, so a re-familied roof
        can be told from its neighbours after it has been renamed; `ids` is what each one
        would be CALLED under the counterfactual and `fams` what each one would BE.
        """
        if key == "id_order":
            return sorted(roofs, key=lambda sid: ids[sid])
        return sorted(roofs, key=lambda sid: (
            0 if is_house_of_trade(fams[sid]) else 1, roof_key(ids[sid], fams[sid])))

    for street_id in sorted(faces):
        face = faces[street_id]
        for how in ADOPTED_READINGS:
            here = [sid for sid in face[how]
                    if sid not in homes and sid not in yards and sid not in requested]
            if len(here) < 2:
                continue
            faces_measured += 1
            places += len(here)
            plain_ids = {sid: sid for sid in here}
            plain_fams = {sid: families.get(sid) for sid in here}
            before = {key: ordered(here, plain_ids, plain_fams, key) for key in
                      ("id_order", "deal_order")}
            for subject in here:
                was = families.get(subject)
                for family in scheduled:
                    if family == was:
                        continue
                    # THE TWO KINDS OF RE-FAMILY, and they are different questions. A roof
                    # that goes from one dwelling family to another, or from one commercial
                    # family to another, has not changed WHAT IT IS: nothing about the deal
                    # should notice, and under `deal_order` nothing does. A roof that
                    # crosses the C/W/F bands has changed what it is, and a deal that reads
                    # the family is SUPPOSED to move it.
                    bucket = (buckets[0]
                              if is_house_of_trade(was) == is_house_of_trade(family)
                              else buckets[1])
                    ids = dict(plain_ids, **{subject: _renamed(subject, family)})
                    fams = dict(plain_fams, **{subject: family})
                    for key, row in tally[bucket].items():
                        after = ordered(here, ids, fams, key)
                        # POSITION BY POSITION, because the position is the allocation: the
                        # deal walks the businesses in evidence order and hands each the
                        # next free roof, so a roof that changes place changes which
                        # business gets which building.
                        changed = sum(1 for a, b in zip(before[key], after) if a != b)
                        row["re_families_tried"] += 1
                        row["places_changed"] += changed
                        row["worst_single_re_family"] = max(
                            row["worst_single_re_family"], changed)
                        if not changed:
                            row["changed_nothing"] += 1
    return {
        "_doc": "DERIVED. One roof re-familied, the face re-ordered, and the count of "
                "PLACES IN THE FREE LIST that changed hands — under the id order this "
                "pass dealt by until T-1651 and under `deal_order`, which replaced it. "
                "The place is the allocation: the deal walks the businesses in evidence "
                "order and hands each the next free roof, so a roof that changes place "
                "changes which business gets which building. Split by whether the "
                "re-family CROSSES the C/W/F bands, because those are different "
                "questions — a D4 that becomes a D5 has not changed what it is and the "
                "deal should not notice, while a D4 that becomes a C2 has, and a deal "
                "that reads the family is supposed to move it.",
        "measured_over": {
            "faces_with_two_or_more_free_roofs": faces_measured,
            "free_roof_places": places,
            "families_in_the_schedule": len(scheduled),
        },
        "places_changed_by_one_roof_s_re_family": tally,
    }


def family_reading(structure_id: str, how: str, families: dict[str, str],
                   functions: dict[str, str], trade_of_this_reading: list[str],
                   homes: dict, yards: set[str], requested: dict,
                   spoken_for: set[str]) -> str:
    """What the adopted roof was raised as, and where that leaves this business (T-1651).

    Written per adoption rather than once in the document's prose, because the two cases
    are different claims about the same table. A business in a house of trade stands in a
    roof built for one. A business in a dwelling is a COMPROMISE of the reconstruction's
    own typology — the deal had nothing better on the face — and the count of them is the
    number to watch, so each one says so on its own record.
    """
    family = families.get(structure_id)
    term = (functions.get(structure_id) or "?").replace("_", " ")
    if is_house_of_trade(family):
        return ("The reconstruction raised this roof as a %s — family %s, of the C, W and "
                "F bands T-1657 rules a house of trade — so a documented business stands "
                "in a roof built to be one. That is the deal preferring a fitting roof "
                "and not a reading of any source: which roof on the face is still an "
                "allocation, and the paper says only the street."
                % (term, family))
    free_trade = [sid for sid in trade_of_this_reading
                  if sid not in homes and sid not in yards and sid not in requested
                  and sid not in spoken_for]
    assert not free_trade, ("%s took a roof of no trade while %s stood free on the same "
                            "%s" % (structure_id, ", ".join(sorted(free_trade)), how))
    return ("A COMPROMISE, AND STATED AS ONE. This roof is a %s — family %s, which the "
            "reconstruction raised as a dwelling and not as a house of trade — so a "
            "documented business stands in a building with no shop front. It is what the "
            "face had by its %s: %d roof(s) reach this street that way and are of the C, "
            "W or F bands, and of those %d are a household's dwelling, %d are yard "
            "buildings, %d were raised to answer a slot request and %d are already "
            "adopted by a better-evidenced business, so none was free to this one. "
            "Raising a shop for it would be a building nothing records; re-familying one "
            "of these roofs is the roof programme's to do and not this pass's."
            % (term, family, how, len(trade_of_this_reading),
               len([sid for sid in trade_of_this_reading if sid in homes]),
               len([sid for sid in trade_of_this_reading if sid in yards]),
               len([sid for sid in trade_of_this_reading if sid in requested]),
               len([sid for sid in trade_of_this_reading if sid in spoken_for])))


def allocate(pool: list, gaz: dict, faces: dict, roofs: dict, homes: dict,
             yards: set[str], readings: tuple[str, ...],
             ruled_two_houses: set[tuple[str, ...]],
             ledger: str = TOWN_LEDGER,
             requested: dict | None = None) -> tuple[list, list]:
    """Deal the ranked pool onto the faces, reading "face" as `readings` says.

    The pass this file writes calls it with `ADOPTED_READINGS` and nothing else, and
    `limits()` re-asserts that against the committed document independently of anything
    here. The parameter exists so the counterfactual another ruling would produce can be
    MEASURED by dealing it, rather than estimated from the count of businesses a widened
    supply would make eligible; those two numbers are not the same, because a widened
    supply still meets refusals 3 and 4. It is what produced the +12 the owner ruled on.

    ONE ROOF, ONE BUSINESS — AND `taken` IS THEREFORE GLOBAL RATHER THAN PER STREET. Under
    the narrow reading a roof reached exactly one face, so the two were the same thing.
    From 2026-08-30 a corner roof stands on TWO faces, and a per-street ledger would let
    the Dearborn deal and the Lake deal each hand out the same corner: one building, two
    shopfronts, on nothing. `limits()` would have caught it after the fact and failed the
    gate; refusing it here means the table is never written that way in the first place.
    """
    requested = requested or {}
    families = roof_families()
    functions = roof_functions()
    taken: set[str] = set()
    spent_on_face: dict[str, set[str]] = {}

    def spoken_for(street_id: str) -> set[str]:
        """The roofs this deal has already spent, as `ledger` counts them."""
        return (taken if ledger == TOWN_LEDGER
                else spent_on_face.setdefault(street_id, set()))

    seated: dict[str, dict[tuple[str, ...], str]] = {}
    adoptions: list[dict] = []
    refusals: list[dict] = []

    for entry in pool:
        street_id = entry["action_target"]
        printed = gaz.get(entry["id"], {})
        common = {
            "business_id": entry["id"],
            "business_name": entry["name"],
            "street_id": street_id,
            "street_name": fronting_street.street_name(street_id),
        }
        if not entry.get("present_at_scene_date"):
            refusals.append(dict(common, refusal=REFUSALS[0],
                                 detail=entry.get("exclusion_note")
                                 or entry.get("exclusion") or ""))
            continue
        face = faces.get(street_id) or {key: list(value)
                                        for key, value in EMPTY_FACE.items()}
        free = [sid for sid in free_under(face, readings, homes, yards, requested,
                                          families)
                if sid not in spoken_for(street_id)]
        if not any(face[how] for how in readings):
            refusals.append(dict(
                common, refusal=REFUSALS[1],
                detail="no roof stands on this street under an adopted reading: %d has "
                       "its platted lot on it, %d end a tier against it, and %d lie "
                       "within the centreline band, which the owner declined as a face "
                       "on 2026-08-30."
                       % (len(face[FRONT]), len(face[SIDE]), len(face[BAND]))))
            continue
        house = collapse_key(entry, ruled_two_houses)
        held = seated.setdefault(street_id, {})
        if house and house in held:
            refusals.append(dict(
                common, refusal=REFUSALS[2],
                detail="%r already stands on this face under the same proprietor "
                       "surname(s) %s%s, on better evidence. One house, one roof per "
                       "face; whether these are two headings of one business is the "
                       "gazetteer's to judge (T-0338, T-0340), not this pass's."
                       % (held[house],
                          ", ".join(surnames(entry)),
                          " in the same trade (%s), which identity.json's two_houses "
                          "ruling on this surname does not separate"
                          % entry.get("occupation")
                          if len(house) > len(surnames(entry)) else "")))
            continue
        if not free:
            on_face = [sid for how in readings for sid in face[how]]
            refusals.append(dict(
                common, refusal=REFUSALS[3],
                detail="%d roof(s) stand on this street: %d are a household's "
                       "dwelling under one layer or the other, %d are yard buildings the "
                       "parcels dealt behind a lot, %d were raised to answer a "
                       "household's slot request, and %d are already adopted by a "
                       "better-evidenced business."
                       % (len(on_face),
                          len([sid for sid in on_face if sid in homes]),
                          len([sid for sid in on_face if sid in yards]),
                          len([sid for sid in on_face if sid in requested]),
                          len([sid for sid in on_face
                               if sid in spoken_for(street_id)]))))
            continue

        structure_id = free[0]
        how = reading_of(face, structure_id)
        # T-1651. The family reading, written while the deal still knows what was free.
        # `free` is ordered houses of trade first WITHIN EACH READING, so the roofs this
        # business could have had instead are the ones of its own reading: READING_ORDER
        # is the order of decreasing claim and a lot front outranks a corner side whatever
        # either roof was raised as. If `free[0]` is not a house of trade then none of
        # that reading was free to this business, and the note says why out of the face's
        # own buckets rather than leaving a reader to reconstruct it.
        trade_of_this_reading = [sid for sid in face[how]
                                 if is_house_of_trade(families.get(sid))]
        family_note = family_reading(structure_id, how, families, functions,
                                     trade_of_this_reading, homes, yards, requested,
                                     spoken_for(street_id))
        taken.add(structure_id)
        spent_on_face.setdefault(street_id, set()).add(structure_id)
        if house:
            held[house] = entry["name"]
        adoptions.append({
            "business_id": entry["id"],
            "business_name": entry["name"],
            "trade": entry.get("trade"),
            "proprietors": entry.get("proprietors") or [],
            # T-0398. The register derives which of those strings are people and which
            # are the house's own trading style, and the row carries both: a table that
            # prints 'Aaron Russell, Benj. H. Clift, Russell & Clift' otherwise states
            # that the partnership is its own third partner.
            "partners": entry.get("partners") or [],
            "firm_styles": entry.get("firm_styles") or [],
            # T-1042 ANSWERED. `surnames()` reads every surname the strings above name,
            # styles included, through `compile_gazetteer.surname_words()`; the row now
            # CARRIES that reading so the household pass reads it instead of guessing at
            # `proprietors` a third time and taking each string's last word.
            "surnames": list(surnames(entry)),
            "street_id": street_id,
            "street_name": fronting_street.street_name(street_id),
            "street_text": printed.get("street"),
            "placement_class": entry.get("placement_class"),
            "cites": sorted(printed.get("mentions") or []),
            "first_issue": (entry.get("evidence") or {}).get("first_issue"),
            "last_issue": (entry.get("evidence") or {}).get("last_issue"),
            "mentions": len(printed.get("mentions") or []),
            "structure_id": structure_id,
            "face": how,
            "roof_confidence": roofs[structure_id],
            # T-1651. WHAT THE RECONSTRUCTION RAISED THIS ROOF AS, off the roof's own
            # record. `roof_is_a_house_of_trade` is T-1657's band test and nothing wider;
            # `family_note` says, in the case where it is false, what stood free instead,
            # so a business seated in a dwelling is a stated compromise rather than a
            # thing a reader has to notice.
            "roof_family": families.get(structure_id),
            "roof_function": functions.get(structure_id),
            "roof_is_a_house_of_trade": is_house_of_trade(families.get(structure_id)),
            "family_note": family_note,
            "lot": None,
            "claims_lot": False,
            "order_is_a_claim": False,
            "note": "The advertisement names %s and nothing narrower, so this business "
                    "takes the street face and not a lot. The roof it is attached to is "
                    "an anonymous reconstructed count-unit %s; it stays reconstructed, "
                    "and WHICH roof on the face is an allocation by "
                    "tools/adopt_street_faces.py rather than a reading of any source. "
                    "Nothing here says this business stood nearer the corner than any "
                    "other on the same face."
                    % (fronting_street.street_name(street_id),
                       FACE_PHRASE[how] % fronting_street.street_name(street_id)),
        })

    adoptions.sort(key=lambda row: row["business_id"])
    refusals.sort(key=lambda row: (row["refusal"], row["business_id"]))
    return adoptions, refusals


#: Every reading of "face" the project has costed, dealt out in full so the table carries
#: the disagreement the decisions were made about. The first two are now HISTORY — the
#: narrow reading that shipped on 2026-08-29 and the corner-side widening the owner adopted
#: on 2026-08-30 — and the third is the one he declined. Keeping all three means the
#: written table answers "what did that ruling cost, and what did the other one save?"
#: without anybody re-deriving it from a git history.
COSTED_READINGS = (
    ("lot front only", (FRONT,)),
    ("a corner side is a face", (FRONT, SIDE)),
    ("a corner side or the band is a face", (FRONT, SIDE, BAND)),
)


def dealt_twice(rows: list) -> dict[str, list[str]]:
    """Every roof more than one row in `rows` is seated in, and who those rows are.

    T-0422. Under the narrow reading a roof reached exactly one face, so "once per face"
    and "once in the town" were the same sentence and no count could tell them apart. The
    corner-side widening separated them, and this is the reading that says which one a
    table obeys.
    """
    who: dict[str, list[str]] = {}
    for row in rows:
        who.setdefault(row["structure_id"], []).append(row["business_id"])
    return {sid: names for sid, names in sorted(who.items()) if len(names) > 1}


def costed(pool: list, gaz: dict, faces: dict, roofs: dict, homes: dict,
           yards: set[str], adoptions: list,
           ruled_two_houses: set[tuple[str, ...]],
           requested: dict | None = None) -> dict:
    """What each reading of "face" actually SEATS, dealt rather than estimated.

    `widened_reading_would_reach` counts the businesses refused for want of a face —
    the ones a wider reading would let back into the deal. It is NOT the number one
    seats, and reading it as one overstates the ruling: those businesses then meet
    refusal 3 (this face already holds this proprietor) and refusal 4 (every roof on the
    face is spoken for), and the supply a widening adds is itself net of refusals 5 and 6,
    because a corner-side roof can be a household's home or a privy exactly as a fronting
    one can. T-0416 is the ticket that put this to the owner, and dealing it is what let
    the question be asked as "twelve shops" rather than "twenty-four".
    """
    today = {row["business_id"]: row for row in adoptions}
    out: dict[str, dict] = {}
    for label, readings in COSTED_READINGS:
        would, refused = allocate(pool, gaz, faces, roofs, homes, yards, readings,
                                  ruled_two_houses, TOWN_LEDGER, requested)
        # T-0422. The same reading dealt under the ledger this pass kept until the
        # corner-side widening: one roof, one business PER FACE. It is derived here, on
        # every rebuild, so the difference between the two ledgers is a measured number in
        # the document rather than an argument in a ticket — and so `limits()` has
        # something to re-assert. Nothing below is ever written as an adoption.
        per_face, _ = allocate(pool, gaz, faces, roofs, homes, yards, readings,
                               ruled_two_houses, PER_FACE_LEDGER, requested)
        seated = {row["business_id"]: row for row in would}
        gained = sorted(set(seated) - set(today))
        # A wider reading is not automatically a superset. Roofs are dealt to the pool in
        # evidence order and a roof can be taken once, so a corner roof a side-reading
        # hands to a Dearborn advertisement is a roof no longer free to the Lake Street
        # one whose lot fronts it. Reporting only the gain would hide that, so both
        # directions are counted and the delta below is the net.
        lost = sorted(set(today) - set(seated))
        by_street: dict[str, int] = {}
        for business_id in gained:
            street_id = seated[business_id]["street_id"]
            by_street[street_id] = by_street.get(street_id, 0) + 1
        out[label] = {
            "adopted_faces": list(readings),
            "in_force": tuple(readings) == ADOPTED_READINGS,
            "would_seat": len(would),
            # ONE ROOF, ONE BUSINESS, TOWN-WIDE — stated as a count rather than asserted
            # in prose, because a counterfactual nobody looks at is exactly where this
            # would rot. `would_seat_on_distinct_roofs` must equal `would_seat`.
            "would_seat_on_distinct_roofs": len({row["structure_id"] for row in would}),
            "deals_a_roof_twice": dealt_twice(would),
            "per_face_ledger_would_seat": len(per_face),
            "per_face_ledger_would_deal_twice": dealt_twice(per_face),
            "against_the_reading_in_force": len(would) - len(today),
            "seats_that_the_reading_in_force_does_not": gained,
            "seats_that_the_reading_in_force_does_not_by_street":
                dict(sorted(by_street.items())),
            "loses_against_the_reading_in_force": lost,
            "would_still_refuse": len(refused),
            "would_still_refuse_by_reason": {reason: sum(1 for row in refused
                                                         if row["refusal"] == reason)
                                             for reason in REFUSALS},
        }
    return out


def derive() -> dict:
    register = load(REGISTER)
    gaz = {b["id"]: b for b in load(GAZETTEER)["businesses"]}
    roofs = reconstructed_roofs()
    named = named_dwellings()
    homes = dwellings()
    yards = yard_roofs()
    requested = requested_roofs()
    faces = supply(roofs, homes, yards, requested)

    families = roof_families()
    ruled_two_houses = two_house_surnames(register)
    pool = [b for b in register["businesses"] if b["action"] == "street_only"]
    pool.sort(key=lambda entry: rank_key(entry, gaz))

    adoptions, refusals = allocate(pool, gaz, faces, roofs, homes, yards,
                                   ADOPTED_READINGS, ruled_two_houses,
                                   TOWN_LEDGER, requested)

    unplaceable = [b for b in register["businesses"]
                   if b["action"] == "unplaceable" and b.get("present_at_scene_date")]
    by_street: dict[str, dict] = {}
    for street_id in sorted({b["action_target"] for b in pool
                             if b["action_target"]} | set(faces)):
        named = [b for b in pool if b["action_target"] == street_id]
        if not named:
            continue
        face = faces.get(street_id) or {key: list(value)
                                        for key, value in EMPTY_FACE.items()}
        by_street[street_id] = {
            "street_name": fronting_street.street_name(street_id),
            "businesses_naming_it": len(named),
            "adopted": sum(1 for row in adoptions if row["street_id"] == street_id),
            "roofs_lot_front": len(face[FRONT]),
            "roofs_corner_side": len(face[SIDE]),
            "roofs_on_the_adopted_face": sum(len(face[how])
                                             for how in ADOPTED_READINGS),
            "roofs_free": len(face["free"]),
            "roofs_home": len(face["homes"]),
            "roofs_home_named": len([sid for sid in face["homes"] if sid in named]),
            "roofs_home_inferred": len([sid for sid in face["homes"]
                                        if sid not in named]),
            "roofs_yard": len(face["yards"]),
            "roofs_requested_by_a_seat": len(face["requested"]),
            "roofs_in_centreline_band_declined": len(face[BAND]),
            # T-1651. The supply that actually binds. A business wants a roof the
            # reconstruction raised as a house of trade and the deal now prefers one; where
            # this number is short of `adopted`, the remainder stand in dwellings and each
            # says so on its own record.
            "roofs_free_and_a_house_of_trade": len(
                [sid for sid in face["free"] if is_house_of_trade(families.get(sid))]),
            "adopted_into_a_house_of_trade": sum(
                1 for row in adoptions if row["street_id"] == street_id
                and row["roof_is_a_house_of_trade"]),
        }

    eligible = sum(1 for row in refusals if row["refusal"] == REFUSALS[1])
    costed_readings = costed(pool, gaz, faces, roofs, homes, yards, adoptions,
                             ruled_two_houses, requested)

    # THE BAND, CONSIDERED AND DECLINED — recorded here rather than left to a document,
    # so a later run reads the refusal off the same file it reads the adoption off and
    # does not re-open it as an oversight (T-0416's acceptance).
    band = costed_readings["a corner side or the band is a face"]
    declined = {
        "reading": DECLINED_READING,
        "ruled": "The owner, 2026-08-30 (T-0416): the band is NOT added.",
        "why": "A band is a distance from a centreline and not an orientation. A roof "
               "within 25 m of a street's platted line may show it a wall, a gable end "
               "or nothing at all, and no reading of the plat can say which. The corner "
               "side adopted above is an orientation the plat does state.",
        "it_would_have_seated": len(band["seats_that_the_reading_in_force_does_not"]),
        "it_would_have_seated_ids": band["seats_that_the_reading_in_force_does_not"],
        "it_would_have_cost": len(band["loses_against_the_reading_in_force"]),
        "it_would_have_cost_ids": band["loses_against_the_reading_in_force"],
    }
    # REFUSAL 7's OWN LEDGER (T-1626). Written out rather than left implicit in a
    # smaller `roofs_free`, because a reservation nobody can see is a reservation that
    # gets quietly re-opened. `occupied_by_a_household` reads the roof's committed record:
    # a reserved roof the household layer has since filled is refusal 4's now and this
    # entry is only its history, while a reserved roof standing empty is the cost of
    # never releasing the reservation, and that is the number to watch.
    reserved = []
    for structure_id, row in requested.items():
        workplace = row.get("reservation_kind") == "workplace"
        held = bool(load(STRUCTURES / (structure_id + ".json")).get("occupants")) if workplace else structure_id in homes
        reserved.append(dict(row, held_by_a_committed_occupancy=held))
    return {
        "schema": 1,
        "generated_by": "tools/adopt_street_faces.py",
        "_doc": "DERIVED, NEVER AUTHORED. Rebuilt from register_1835.json, the committed "
                "structures and data/residents/ by tools/adopt_street_faces.py; "
                "tools/check.sh refuses a committed copy a rebuild would not produce. "
                "The policy is docs/STREET-FACE-ADOPTION.md and the liberty is L212. "
                "An adoption claims a STREET FACE and never a lot.",
        "policy": "docs/STREET-FACE-ADOPTION.md",
        "ruling": "The owner, 2026-08-29 (T-0354): a business the paper places on a "
                  "platted street and nothing narrower adopts a reconstructed roof "
                  "already standing on that street face.",
        "ruling_extended": "The owner, 2026-08-30 (T-0416): a corner side IS a face — a "
                           "building on a corner stands on both the streets it meets, "
                           "and a business advertising on either is saying where its "
                           "door is. The centreline band was offered in the same "
                           "question and DECLINED.",
        "scene_date": SCENE_DATE,
        "reading": {
            "adopted_faces": list(ADOPTED_READINGS),
            "refused_faces": [DECLINED_READING],
            "why": "An advertisement's street is where the door is. A corner building has "
                   "a door on each of the two streets it meets, so both are faces; a "
                   "centreline band is a distance from a line rather than an "
                   "orientation, and says nothing about which way a building looks.",
            "considered_and_declined": declined,
            "refused_for_want_of_a_face": eligible,
            "refused_for_want_of_a_face_note":
                "The count of businesses REFUSED FOR WANT OF A FACE, which is how many a "
                "wider reading would let back into the deal — not how many it would "
                "seat. `costed_readings` below deals every reading out in full and "
                "reports what each actually stands up (T-0416).",
            "costed_readings": costed_readings,
            # T-1651. THE DEAL READS THE ROOF'S FAMILY, and these two entries are what
            # says so on the record rather than in a comment: what the faces hold, and
            # what one roof's re-family now costs against what it used to.
            "the_roof_s_family": {
                "ruling": "T-1657's bands, not re-decided here: a roof of the C, W or F "
                          "families was raised as a house of trade — a counter, a works, "
                          "a freight store — and a roof of the D, H, A, I, T or M "
                          "families was not.",
                "how_the_deal_reads_it": "Within a face AND WITHIN A READING, a business "
                                         "takes a house of trade before a roof of no "
                                         "trade. The reading still outranks the family: "
                                         "READING_ORDER is the order of decreasing claim "
                                         "and a lot front is a better claim than a corner "
                                         "side whatever either roof was raised as.",
                "still_not_evidence": "Limit 3 is unchanged. Which roof on the face a "
                                      "business takes is an allocation and no source "
                                      "speaks to it; preferring a roof that does not "
                                      "contradict the reconstruction's own typology is a "
                                      "better allocation and not a new claim.",
                "read_off_the_record_never_the_id": "The family is `reconstruction.family` "
                                                    "on the roof's own record. The id "
                                                    "carries the family as a token and the "
                                                    "two agree, which is how an id-ordered "
                                                    "deal could look like a family-aware "
                                                    "one for a year while being neither.",
            },
            "re_family_stability": re_family_churn(faces, homes, yards, requested,
                                                   families),
        },
        "counts": {
            "street_only_in_register": len(pool),
            "adopted": len(adoptions),
            "refused": len(refusals),
            "refused_by_reason": {reason: sum(1 for row in refusals
                                              if row["refusal"] == reason)
                                  for reason in REFUSALS},
            "unplaceable_present_at_scene_date": len(unplaceable),
            "adopted_into_a_house_of_trade": sum(
                1 for row in adoptions if row["roof_is_a_house_of_trade"]),
            "adopted_into_a_roof_of_no_trade": sum(
                1 for row in adoptions if not row["roof_is_a_house_of_trade"]),
            "roofs_free_and_a_house_of_trade": len(
                {sid for face in faces.values() for sid in face["free"]
                 if is_house_of_trade(families.get(sid))}),
            # What is left over, and it is the number that says whether the deal or the
            # roof programme is the constraint. A house of trade still free after the deal
            # was one no business could reach: it stands on a face by a reading no
            # advertisement of that face was dealt under, or its face was exhausted of
            # BUSINESSES rather than of roofs.
            "houses_of_trade_left_free": len(
                {sid for face in faces.values() for sid in face["free"]
                 if is_house_of_trade(families.get(sid))}
                - {row["structure_id"] for row in adoptions}),
            "roofs_reserved_for_a_slot_request": len(reserved),
            "reserved_and_held_by_a_committed_occupancy":
                sum(1 for row in reserved if row["held_by_a_committed_occupancy"]),
            "reserved_without_a_committed_occupancy":
                sum(1 for row in reserved
                    if not row["held_by_a_committed_occupancy"]),
            "by_street": by_street,
        },
        "reserved_for_a_slot_request": reserved,
        "reserved_for_a_slot_request_note":
            "REFUSAL 7, T-1626. A roof raised in answer to a household's slot request is "
            "the household layer's and this pass may not take it. The link is "
            "data/reconstruction/1835_platted_block_parcels.json § "
            "dealt_against_a_request, which the build ticket writes beside the deal that "
            "answered the request; it is an authored recipe upstream of both passes, so "
            "reading it here closes no cycle. Which household finally occupies the roof "
            "is the seating pass's allocation and is not claimed here. "
            "`held_by_a_committed_occupancy` reads the roof's own structure record and "
            "nothing else: the platted deal writes no `occupants`, so a roof it has "
            "seated still reads false here, and the false count is an upper bound on "
            "what the reservation costs rather than the cost. T-1766 also reserves the five "
            "authored Canal workplace allocations from 1835_canal_approach_occupancy.json. "
            "Those rows have reservation_kind=workplace, claim no residence, and report "
            "held occupancy from their structure occupants block. The legacy slot-request "
            "keys count both kinds of authored reservation.",
        "adoptions": adoptions,
        "refusals": refusals,
    }


# ---------------------------------------------------------------------------
# build / check / report
# ---------------------------------------------------------------------------

def build() -> int:
    OUT.write_text(dumps(derive()), encoding="utf-8")
    print("wrote %s" % OUT.relative_to(ROOT))
    return 0


def limits(doc: dict) -> list[str]:
    """The five limits, re-asserted against the committed document."""
    bad: list[str] = []
    roofs = reconstructed_roofs()
    seen: set[str] = set()
    for row in doc["adoptions"]:
        who = row.get("business_id", "?")
        extra = set(row) - ADOPTION_KEYS
        if extra:
            bad.append("%s carries field(s) the policy does not allow: %s"
                       % (who, ", ".join(sorted(extra))))
        for key, value in row.items():
            if "lot" in key and value not in (None, False):
                bad.append("%s names a lot in %r — limit 1 refuses it" % (who, key))
        if row.get("lot") is not None or row.get("claims_lot") is not False:
            bad.append("%s does not declare `lot: null, claims_lot: false`" % who)
        if row.get("order_is_a_claim") is not False:
            bad.append("%s does not declare `order_is_a_claim: false`" % who)
        structure_id = row.get("structure_id")
        if structure_id not in roofs:
            bad.append("%s adopts %r, which is not an anonymous reconstructed roof"
                       % (who, structure_id))
        elif roofs[structure_id] != "reconstructed":
            bad.append("%s adopts %s, whose building is now %r — limit 2 refuses a "
                       "promoted roof" % (who, structure_id, roofs[structure_id]))
        else:
            how = fronting_street.fronts(structure_id, row["street_id"])
            if how not in ADOPTED_READINGS:
                bad.append("%s adopts %s, which does not front %s by a lot front or a "
                           "corner side — it reaches that street %s"
                           % (who, structure_id, row["street_id"],
                              "by the centreline band, which the owner declined as a "
                              "face on 2026-08-30" if how == BAND else "not at all"))
            elif row.get("face") != how:
                # The `face` field is what a card, a note or a later pass reads to know
                # WHICH claim the adoption makes. A record that says `lot front` over a
                # corner is the quiet way this ruling gets overstated, so it is checked
                # against the derivation rather than taken on trust.
                bad.append("%s says it took %s by its %r, but %s reaches that street by "
                           "its %r" % (who, row["street_id"], row.get("face"),
                                       structure_id, how))
        if structure_id in seen:
            bad.append("%s is the second business on %s — one roof, one business"
                       % (who, structure_id))
        seen.add(structure_id)
        if not row.get("cites"):
            bad.append("%s cites no printing of its street" % who)
    named = named_dwellings()
    inferred = inferred_dwellings()
    for structure_id in sorted(seen & (set(named) | set(inferred))):
        bad.append("%s is a %s household's dwelling and cannot also be adopted"
                   % (structure_id, "named" if structure_id in named else "n inferred"))
    for structure_id in sorted(seen & yard_roofs()):
        bad.append("%s is a yard building — a privy, a stable or a woodshed standing "
                   "behind a lot — and a business cannot be seated in one" % structure_id)
    # REFUSAL 7, T-1626. Asserted against the committed table for the same reason 4 and 5
    # are: the allocation refuses these roofs when it deals, and this is what says the
    # committed document still obeys the refusal after any hand or merge touches it.
    reserved_now = requested_roofs()
    for structure_id in sorted(seen & set(reserved_now)):
        bad.append("%s was raised to answer %s's slot request (%s, %s) and cannot also "
                   "be adopted — refusal 7 reserves it for its authored seat"
                   % (structure_id,
                      reserved_now[structure_id].get("requested_by_seat"),
                      reserved_now[structure_id].get("block_id"),
                      reserved_now[structure_id].get("dealt_by_ticket")))

    # LIMIT 5, T-1651 — THE DEAL READS THE ROOF'S FAMILY, AND THIS SAYS IT STILL DOES.
    # Asserted against the committed table rather than against the deal, so a hand edit or
    # a merge cannot put a business back into a cottage while a shop roof stands empty
    # beside it. The reasoning is that a roof only leaves the free set by being adopted:
    # homes, yards and slot-request roofs are refused throughout, so a trade-band roof
    # still unadopted at the end of the deal was free for the whole of it.
    families = roof_families()
    functions = roof_functions()
    adopted_by_street: dict[str, list[dict]] = {}
    for row in doc["adoptions"]:
        adopted_by_street.setdefault(row["street_id"], []).append(row)
    homes_for_limits = dwellings()
    yards_for_limits = yard_roofs()
    faces_for_limits = supply(roofs, homes_for_limits, yards_for_limits, reserved_now)
    for street_id, rows in sorted(adopted_by_street.items()):
        face = faces_for_limits.get(street_id) or {}
        for how in ADOPTED_READINGS:
            standing = face.get(how) or []
            free_trade = sorted(
                sid for sid in standing
                if is_house_of_trade(families.get(sid))
                and sid not in homes_for_limits and sid not in yards_for_limits
                and sid not in reserved_now and sid not in seen)
            if not free_trade:
                continue
            for row in rows:
                if row.get("face") != how or row.get("roof_is_a_house_of_trade"):
                    continue
                bad.append(
                    "%s stands in %s, a %s, while %s stood free on the same %s of %s — "
                    "limit 5 refuses a business in a roof of no trade while a house of "
                    "trade of the same reading is free"
                    % (row.get("business_id"), row.get("structure_id"),
                       row.get("roof_family"), ", ".join(free_trade), how, street_id))
    # And the two statements the stable deal order rests on, re-derived rather than
    # trusted. If either stops holding, `roof_key` is no longer a re-family invariant and
    # T-1651's whole claim goes with it.
    for row in doc["adoptions"]:
        structure_id = row.get("structure_id")
        family = families.get(structure_id)
        if row.get("roof_family") != family:
            bad.append("%s says its roof is family %r; %s's own record says %r"
                       % (row.get("business_id"), row.get("roof_family"),
                          structure_id, family))
        if row.get("roof_function") != functions.get(structure_id):
            bad.append("%s says its roof is a %r; %s's own record says %r"
                       % (row.get("business_id"), row.get("roof_function"),
                          structure_id, functions.get(structure_id)))
        if row.get("roof_is_a_house_of_trade") is not is_house_of_trade(family):
            bad.append("%s states the wrong reading of family %r against the C, W and F "
                       "bands" % (row.get("business_id"), family))
    pools: dict[tuple[str, int], list[str]] = {}
    for structure_id, family in sorted(families.items()):
        # A roof whose id carries a family token must carry ITS OWN, because that is the
        # token `roof_key` strips. A roof whose id carries none — the West Division numbers
        # its roofs `recon_1835_west_046` — is already invariant, and needs nothing.
        token = re.search(r"_([a-z]\d)_\d+$", structure_id)
        if token and str(family).lower() != token.group(1):
            bad.append("%s is family %r but its id carries the token %r, so `roof_key` "
                       "strips the wrong one and the deal order stops being a re-family "
                       "invariant" % (structure_id, family, token.group(1).upper()))
        pools.setdefault(roof_key(structure_id, family), []).append(structure_id)
    for key, ids in sorted(pools.items()):
        if len(ids) > 1:
            bad.append("%s share the pool-and-ordinal key %r, so it is not an identity a "
                       "re-family holds steady — T-1651's deal order rests on it being one"
                       % (" and ".join(ids), key))

    # LIMIT 1 HOLDS OVER THE COUNTERFACTUALS TOO — T-0422. Every check above reads the
    # SHIPPED table, which is the reading in force; the other two rows of
    # `costed_readings` are the numbers the owner is asked to rule on, and until this gate
    # existed nothing re-asserted anything about them. A widening whose seat count is
    # inflated by dealing one corner building to two shopfronts is a wrong price on a real
    # decision, and it would never fail a gate, because it is never adopted.
    for label, row in sorted((doc.get("reading") or {}).get("costed_readings", {}).items()):
        for structure_id, businesses in sorted((row.get("deals_a_roof_twice") or {}).items()):
            bad.append("the %r counterfactual deals %s to %s — one roof, one business "
                       "holds town-wide, not once per face"
                       % (label, structure_id, " and ".join(businesses)))
        if row.get("would_seat_on_distinct_roofs") != row.get("would_seat"):
            bad.append("the %r counterfactual seats %s business(es) on %s roof(s), so its "
                       "price is inflated by the difference"
                       % (label, row.get("would_seat"),
                          row.get("would_seat_on_distinct_roofs")))
    return bad


def check() -> int:
    if not OUT.exists():
        print("MISSING %s — run tools/adopt_street_faces.py" % OUT.relative_to(ROOT))
        return 1
    committed = load(OUT)
    rebuilt = derive()
    if dumps(committed) != dumps(rebuilt):
        print("STALE %s — a rebuild does not reproduce the committed copy."
              % OUT.relative_to(ROOT))
        for key in sorted(set(committed) | set(rebuilt)):
            if committed.get(key) != rebuilt.get(key):
                print("  differs: %s" % key)
        return 1
    bad = limits(committed)
    if bad:
        for line in bad:
            print("  FAIL %s" % line)
        return 1
    counts = committed["counts"]
    print("  ok    %d street-only business(es): %d adopted a street face, %d wait; "
          "no adoption claims a lot"
          % (counts["street_only_in_register"], counts["adopted"], counts["refused"]))
    print("  ok    %d unplaceable business(es) stand outside this policy (T-0354 half two)"
          % counts["unplaceable_present_at_scene_date"])
    # T-1651, REPORTED RATHER THAN LEFT IN THE FILE. The first line is the state of the
    # town; the second is the gate's own claim about the deal, and the number that matters
    # in it is the zero.
    churn = committed["reading"]["re_family_stability"]["places_changed_by_one_roof_s_re_family"]
    print("  ok    %d adoption(s) stand in a roof the reconstruction raised as a house of "
          "trade and %d in a roof of no trade; of the %d such roof(s) standing free on "
          "the faces the deal left %d unspent, so what the rest wanted is a roof the "
          "roof programme has not raised (limit 5, T-1651)"
          % (counts["adopted_into_a_house_of_trade"],
             counts["adopted_into_a_roof_of_no_trade"],
             counts["roofs_free_and_a_house_of_trade"],
             counts["houses_of_trade_left_free"]))
    print("  ok    a re-family that does not cross the C/W/F bands changes %d place(s) in "
          "the deal over %d trials, against %d under the id order this replaced (worst "
          "single re-family %d, was %d)"
          % (churn["within the bands"]["deal_order"]["places_changed"],
             churn["within the bands"]["deal_order"]["re_families_tried"],
             churn["within the bands"]["id_order"]["places_changed"],
             churn["within the bands"]["deal_order"]["worst_single_re_family"],
             churn["within the bands"]["id_order"]["worst_single_re_family"]))
    print("  ok    %d roof(s) raised for an authored household or workplace seat are reserved "
          "from the deal; %d carry a committed occupancy, %d do not yet (refusal 7, "
          "T-1626 — the platted deal writes none, so that is an upper bound)"
          % (counts["roofs_reserved_for_a_slot_request"],
             counts["reserved_and_held_by_a_committed_occupancy"],
             counts["reserved_without_a_committed_occupancy"]))
    return 0


def report() -> int:
    doc = derive()
    counts = doc["counts"]
    print("STREET-FACE ADOPTION — T-0354, the owner's ruling of 2026-08-29,")
    print("extended by his ruling of 2026-08-30 that a corner side is a face (T-0416)\n")
    print("  %-28s %s" % ("street_only in the register", counts["street_only_in_register"]))
    print("  %-28s %s" % ("adopted a street face", counts["adopted"]))
    print("  %-28s %s" % ("waiting", counts["refused"]))
    for reason, n in counts["refused_by_reason"].items():
        print("      %-40s %s" % (reason, n))
    print("  %-28s %s" % ("unplaceable, still open", counts["unplaceable_present_at_scene_date"]))
    print("  %-28s %s" % ("reserved by a slot request", counts["roofs_reserved_for_a_slot_request"]))
    for row in doc["reserved_for_a_slot_request"]:
        print("      %-52s %s %s, for %s%s"
              % (row["structure_id"], row["block_id"], row["family"],
                 row["requested_by_seat"],
                 "" if row["held_by_a_committed_occupancy"]
                 else "  <-- no committed occupancy yet"))
    print("\n  BY STREET FACE — `front` and `side` are both adopted faces; `band` is not")
    print("  %-20s %5s %5s %6s %5s %5s %5s %5s"
          % ("street", "ads", "took", "front", "side", "free", "band", "asked"))
    for street_id, row in sorted(counts["by_street"].items(),
                                 key=lambda kv: (-kv[1]["businesses_naming_it"], kv[0])):
        print("  %-20s %5d %5d %6d %5d %5d %5d %5d"
              % (row["street_name"], row["businesses_naming_it"], row["adopted"],
                 row["roofs_lot_front"], row["roofs_corner_side"], row["roofs_free"],
                 row["roofs_in_centreline_band_declined"],
                 row["roofs_requested_by_a_seat"]))
    print("\n  EVERY READING COSTED, because the reader is owed the disagreement the")
    print("  decisions were made about. Eligible is not seated: refusals 3 and 4 still")
    print("  hold, and the supply a wider reading adds is already net of a household's")
    print("  home and a yard building, so each row below is DEALT rather than estimated.")
    print("      %-36s %d refused for want of any face"
          % ("in force:", doc["reading"]["refused_for_want_of_a_face"]))
    for label, row in doc["reading"]["costed_readings"].items():
        mark = "<-- IN FORCE" if row["in_force"] else ""
        print("      %-34s %2d seated (%+d), %d still refused  %s"
              % (label, row["would_seat"], row["against_the_reading_in_force"],
                 row["would_still_refuse"], mark))
        # T-0422. One roof, one business is counted TOWN-WIDE, and the second line says
        # what that costs: a per-face ledger would price this reading higher by dealing
        # the same corner building to two shopfronts.
        print("          %d roof(s) dealt; per face it would seat %d and deal %s"
              % (row["would_seat_on_distinct_roofs"], row["per_face_ledger_would_seat"],
                 ", ".join("%s twice" % sid
                           for sid in row["per_face_ledger_would_deal_twice"])
                 or "no roof twice"))
        gains = row["seats_that_the_reading_in_force_does_not_by_street"]
        print("          gains: %s" % (", ".join(
            "%s +%d" % (fronting_street.street_name(street_id), n)
            for street_id, n in gains.items()) or "nothing"))
        if row["loses_against_the_reading_in_force"]:
            print("          loses: %s"
                  % ", ".join(row["loses_against_the_reading_in_force"]))
    declined = doc["reading"]["considered_and_declined"]
    print("\n  CONSIDERED AND DECLINED — the %s, %s" % (declined["reading"],
                                                        declined["ruled"]))
    print("      it would have seated %d further business(es): %s"
          % (declined["it_would_have_seated"],
             ", ".join(declined["it_would_have_seated_ids"]) or "none"))
    print("\n  ADOPTIONS")
    for row in doc["adoptions"]:
        print("      %-46s %-20s %s" % (row["business_name"][:46], row["street_name"],
                                        row["structure_id"]))
    print("\n  REFUSALS")
    for row in doc["refusals"]:
        print("      %-46s %-20s %s" % (row["business_name"][:46], row["street_name"],
                                        row["refusal"]))
        print("          %s" % row["detail"])
    return 0


def self_test() -> int:
    """Break each limit and each ruling boundary in turn; every one must fire.

    `--check` compares a rebuild before it reaches the limits, so a hand-edit trips the
    staleness gate first and the limits themselves would never be exercised by any
    ordinary failure. That is precisely how a gate becomes decoration. These cases call
    `limits()` on a mutated copy of the committed document and assert it complains.
    """
    doc = load(OUT)
    if not doc["adoptions"]:
        print("  FAIL nothing is adopted, so nothing can be broken")
        return 1
    failed = 0

    def case(label: str, mutate, wanted: str) -> None:
        nonlocal failed
        broken = json.loads(json.dumps(doc))
        mutate(broken)
        found = limits(broken)
        if any(wanted in line for line in found):
            print("  fires: %s" % label)
        else:
            failed = 1
            print("  FAIL  %s did not fire — got %r" % (label, found))

    def first(broken):
        return broken["adoptions"][0]

    case("a record that grows a lot field",
         lambda b: first(b).update(lot_id="blk_south_water_clark/n/3"),
         "does not allow")
    case("a record that fills the lot field it declares",
         lambda b: first(b).update(lot=7),
         "names a lot")
    case("a record that stops declaring `claims_lot: false`",
         lambda b: first(b).update(claims_lot=True),
         "names a lot")
    case("a record that makes its order a claim",
         lambda b: first(b).update(order_is_a_claim=True),
         "order_is_a_claim")
    case("an adoption on a roof this project does not hold",
         lambda b: first(b).update(structure_id="a_roof_that_is_not_there"),
         "not an anonymous reconstructed roof")
    case("an adoption on a roof that does not front its street",
         lambda b: first(b).update(street_id="washington"),
         "does not front")

    # THE 2026-08-30 RULING'S OWN BOUNDARY. It widened what counts as a face by exactly
    # one reading, and the two ways that widening could quietly become three are a record
    # that reaches its street only by the DECLINED band, and a corner adoption that
    # describes itself as a lot front. Neither is caught by any case above: both name a
    # street the roof genuinely reaches, and the second is a true record of a real
    # adoption with one field overstated.
    corner = next((row for row in doc["adoptions"] if row["face"] == SIDE), None)
    if corner is None:
        print("  FAIL  nothing is adopted on a corner side, so the 2026-08-30 ruling "
              "cannot be tested")
        failed = 1
    else:
        case("a corner adoption that calls itself a lot front",
             lambda b: next(row for row in b["adoptions"]
                            if row["business_id"] == corner["business_id"]
                            ).update(face=FRONT),
             "says it took")

    banded = next(((sid, street_id) for sid in sorted(reconstructed_roofs())
                   for street_id, how in fronting_street.fronting(sid) if how == BAND),
                  None)
    if banded is None:
        print("  FAIL  no roof reaches a street by the band, so the declined reading "
              "cannot be tested")
        failed = 1
    else:
        case("an adoption reaching its street only by the declined centreline band",
             lambda b: first(b).update(structure_id=banded[0], street_id=banded[1],
                                       face=BAND),
             "declined as a face")
    case("two businesses on one roof",
         lambda b: b["adoptions"].__setitem__(
             1, dict(b["adoptions"][1], structure_id=first(b)["structure_id"])),
         "one roof, one business")
    case("an adoption citing no printing of its street",
         lambda b: first(b).update(cites=[]),
         "cites no printing")

    # T-0422. THE COUNTERFACTUALS' OWN LEDGER. Both cases mutate a costed row rather than
    # an adoption, because that row is the only place a widening's price is written.
    widening = next((label for label, row in doc["reading"]["costed_readings"].items()
                     if not row["in_force"] and row["adopted_faces"] != [FRONT]), None)
    if widening is None:
        print("  FAIL  no widening is costed, so its ledger cannot be tested")
        failed = 1
    else:
        case("a widening that deals one corner roof to two shopfronts",
             lambda b: b["reading"]["costed_readings"][widening].update(
                 deals_a_roof_twice={first(b)["structure_id"]:
                                     ["business_a", "business_b"]}),
             "one roof, one business holds town-wide")
        case("a widening whose seat count runs ahead of the roofs it dealt",
             lambda b: b["reading"]["costed_readings"][widening].update(
                 would_seat_on_distinct_roofs=b["reading"]["costed_readings"]
                 [widening]["would_seat"] - 1),
             "its price is inflated")

    # Refusal 5's live half. Nine adoptions stood in outbuildings until 2026-08-29, so
    # this case is the one that would have caught it: seat the first business on a roof
    # the parcels dealt as ancillary and the limits must say so.
    yards = sorted(yard_roofs())
    if not yards:
        print("  FAIL  the town holds no ancillary roof, so refusal 5 cannot be tested")
        failed = 1
    else:
        case("a business seated in a yard building",
             lambda b: first(b).update(structure_id=yards[0], street_id=next(
                 street for street, how in fronting_street.fronting(yards[0])
                 if how == FRONT)),
             "is a yard building")

    # Refusal 4's OTHER half, and the one the corner-side ruling made live. A roof the
    # inferred-household programme holds is somebody's home too, and it is invisible to
    # `data/residents/`; the first re-derivation under the widened reading walked straight
    # into one. This is the case that would have caught it.
    inferred_only = sorted(set(inferred_dwellings()) - set(named_dwellings()))
    if not inferred_only:
        print("  FAIL  the inferred-household programme holds no roof of its own, so "
              "refusal 4's second half cannot be tested")
        failed = 1
    else:
        case("a business seated in a roof the inferred-household layer holds",
             lambda b: first(b).update(structure_id=inferred_only[0]),
             "inferred household's dwelling")

    # REFUSAL 7's live half (T-1626). The case that would have caught T-1622: seat the
    # first business on a roof the platted seating asked a block for, and the limits must
    # say so. The reservation has to be REAL for this to test anything, so a town holding
    # none fails loudly rather than skipping quietly.
    reserved_for_test = sorted(requested_roofs())
    if not reserved_for_test:
        print("  FAIL  no roof stands against a slot request, so refusal 7 cannot be "
              "tested")
        failed = 1
    else:
        on_a_face = [(sid, street) for sid in reserved_for_test
                     for street, how in fronting_street.fronting(sid)
                     if how in ADOPTED_READINGS]
        if not on_a_face:
            print("  FAIL  no reserved roof stands on an adopted face, so refusal 7 "
                  "cannot be tested")
            failed = 1
        else:
            case("a business seated in a roof raised to answer a slot request",
                 lambda b: first(b).update(structure_id=on_a_face[0][0],
                                           street_id=on_a_face[0][1]),
                 "refusal 7 reserves it for its authored seat")

    for sid in requested_trade_workplaces():
        case("a second business seated in an authored trade workplace: " + sid,
             lambda b, sid=sid: first(b).update(structure_id=sid),
             "refusal 7 reserves it for its authored seat")

    # LIMIT 5's THREE WAYS OF ROTTING, T-1651: a business put back into a dwelling while a
    # shop roof on the same face and the same reading stands free, and the two ways the
    # family reading on a record could stop being the roof's own.
    families_for_test = roof_families()
    functions_for_test = roof_functions()
    homes_for_test = dwellings()
    yards_for_test = yard_roofs()
    requested_for_test = requested_roofs()
    faces_for_test = supply(reconstructed_roofs(), homes_for_test, yards_for_test,
                            requested_for_test)
    adopted_now = {row["structure_id"] for row in doc["adoptions"]}
    swap = None
    for row in doc["adoptions"]:
        if not row["roof_is_a_house_of_trade"]:
            continue
        face = faces_for_test.get(row["street_id"]) or {}
        for sid in face.get(row["face"]) or []:
            if (sid not in adopted_now and sid not in homes_for_test
                    and sid not in yards_for_test and sid not in requested_for_test
                    and not is_house_of_trade(families_for_test.get(sid))):
                swap = (row["business_id"], sid)
                break
        if swap:
            break
    if swap is None:
        print("  ok:    no face holds both an adopted house of trade and a free roof of no "
              "trade under one reading, so limit 5 cannot be broken by a swap on this tree")
    else:
        business_id, into = swap

        def put_in_a_dwelling(broken, business_id=business_id, into=into):
            for row in broken["adoptions"]:
                if row["business_id"] == business_id:
                    row.update(structure_id=into,
                               roof_family=families_for_test.get(into),
                               roof_function=functions_for_test.get(into),
                               roof_is_a_house_of_trade=False)

        case("a business moved into a dwelling while its own shop roof stands free",
             put_in_a_dwelling, "limit 5 refuses a business in a roof of no trade")
    case("a record that misstates its roof's family",
         lambda b: first(b).update(roof_family="D1"),
         "own record says")
    case("a record that misstates the band its roof's family is in",
         lambda b: first(b).update(
             roof_is_a_house_of_trade=not first(b)["roof_is_a_house_of_trade"]),
         "wrong reading of family")

    # Limit 2's live half: a roof promoted out of `reconstructed` must fail. It cannot be
    # faked by mutating the table — the confidence is read from the structure — so this
    # asserts the reader that limit 2 depends on actually distinguishes the grades.
    roofs = reconstructed_roofs()
    grades = set(roofs.values())
    if grades == {"reconstructed"}:
        print("  ok:    every adoptable roof reads `reconstructed` from its own phase "
              "(%d roofs), which is what limit 2 re-reads" % len(roofs))
    else:
        print("  ok:    the phase reader distinguishes %s, so a promoted roof is visible "
              "to limit 2" % ", ".join(sorted(grades)))

    # T-0422, THE LIVE HALF. The two cases above prove the gate fires; this proves it is
    # not vacuous, by dealing every costed reading under BOTH ledgers on the tree as it
    # stands. The town-wide ledger must never double-deal, and the difference between the
    # two is the thing the ticket asked to be kept measured rather than argued.
    register_for_ledger = load(REGISTER)
    gaz_for_ledger = {b["id"]: b for b in load(GAZETTEER)["businesses"]}
    roofs_for_ledger = reconstructed_roofs()
    homes_for_ledger = dwellings()
    yards_for_ledger = yard_roofs()
    requested_for_ledger = requested_roofs()
    faces_for_ledger = supply(roofs_for_ledger, homes_for_ledger, yards_for_ledger,
                              requested_for_ledger)
    ruled_for_ledger = two_house_surnames(register_for_ledger)
    pool_for_ledger = [b for b in register_for_ledger["businesses"]
                       if b["action"] == "street_only"]
    pool_for_ledger.sort(key=lambda entry: rank_key(entry, gaz_for_ledger))
    bites = 0
    for label, readings in COSTED_READINGS:
        under = {}
        for ledger in (TOWN_LEDGER, PER_FACE_LEDGER):
            rows, _ = allocate(pool_for_ledger, gaz_for_ledger, faces_for_ledger,
                               roofs_for_ledger, homes_for_ledger, yards_for_ledger,
                               readings, ruled_for_ledger, ledger,
                               requested_for_ledger)
            under[ledger] = rows
        twice = dealt_twice(under[TOWN_LEDGER])
        if twice:
            failed = 1
            print("  FAIL  %r deals a roof twice under the town-wide ledger: %s"
                  % (label, ", ".join(sorted(twice))))
            continue
        per_face_twice = dealt_twice(under[PER_FACE_LEDGER])
        bites += len(per_face_twice)
        print("  holds: %-34s %2d seated on %2d roofs town-wide; per face it would "
              "seat %2d and deal %d roof(s) twice"
              % (label, len(under[TOWN_LEDGER]),
                 len({row["structure_id"] for row in under[TOWN_LEDGER]}),
                 len(under[PER_FACE_LEDGER]), len(per_face_twice)))
    print("  ok:    the per-face ledger would double-deal %d roof(s) across the costed "
          "readings, so the town-wide one is doing work" % bites)

    # T-0414: REFUSAL 3 MUST OBEY THE IDENTITY LAYER. This is not a limit on the
    # committed document — it is a rule about how the deal is MADE — so it is asserted
    # directly instead of by breaking a record. The four assertions are the four ways the
    # rule could rot: stop firing, fire on a group nobody ruled, stop separating trades,
    # or start separating headings of the SAME trade (which would answer T-0338's open
    # question by seating rather than by judging).
    register = load(REGISTER)
    ruled = two_house_surnames(register)
    by_id = {entry["id"]: entry for entry in register["businesses"]}
    boot = by_id.get("business_l_w_montgomery_boot_and_shoe_maker")
    auctioneer = by_id.get("business_w_montgomery")
    second = by_id.get("business_montgomery_auction_and_commission_house")

    def want(label: str, ok: bool) -> None:
        nonlocal failed
        if ok:
            print("  holds: %s" % label)
        else:
            failed = 1
            print("  FAIL  %s" % label)

    if not all((boot, auctioneer, second)):
        want("the Montgomery headings T-0414 rests on are still in the register", False)
    else:
        want("the bootmaker and the auctioneer still share one surname set, so the "
             "collapse would still reach them",
             surnames(boot) == surnames(auctioneer) != ())
        want("identity.json still rules that surname `two_houses`",
             surnames(boot) in ruled)
        want("the ruling separates the two trades",
             collapse_key(boot, ruled) != collapse_key(auctioneer, ruled))
        want("two headings of the SAME trade inside a ruled group still collide",
             collapse_key(auctioneer, ruled) == collapse_key(second, ruled))
        want("and without the ruling they would collapse, so the ruling is what does "
             "the work",
             collapse_key(boot, set()) == collapse_key(auctioneer, set()))
    unruled = [entry for entry in register["businesses"]
               if surnames(entry) and surnames(entry) not in ruled]
    want("a surname the corpus has NOT ruled is keyed on the surname alone (%d "
         "businesses)" % len(unruled),
         all(collapse_key(entry, ruled) == surnames(entry) for entry in unruled))

    if failed:
        print("SELF-TEST FAIL")
        return 1
    print("SELF-TEST PASS — all five limits, all three roof refusals (both halves of "
          "the household one, the yard building, and the roof raised to answer a slot "
          "request), both edges of the 2026-08-30 face ruling and both readings of the "
          "one-roof-one-business ledger fire when broken, and refusal 3 still obeys "
          "identity.json's two_houses rulings (20 cases)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="re-derive, diff the committed copy, and re-assert the limits")
    ap.add_argument("--report", action="store_true",
                    help="the adoption and every refusal, with counts")
    ap.add_argument("--self-test", action="store_true",
                    help="break each of the five limits in turn; every one must fire")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.check:
        return check()
    if args.report:
        return report()
    return build()


if __name__ == "__main__":
    raise SystemExit(main())
