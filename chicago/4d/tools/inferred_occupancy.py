#!/usr/bin/env python3
"""The occupancy ledger the anonymous-infill generators read.

TWO PROGRAMMES SEAT AN OCCUPANT ON AN ANONYMOUS ROOF, and both arrive here.

`tools/generate_inferred_infill.py` and `tools/generate_north_infill.py` build the
anonymous roofs of the 665-roof programme and re-derive them byte-for-byte on every
commit. Phase two of the inferred-residents programme (docs/ROADMAP.md K1) ADOPTS
some of those roofs: an inferred household takes one as its dwelling or its shop,
and the roof stops being anonymous massing and becomes a building with an argument
behind it.

That has to reach the structure record, or the adoption exists only in
`data/residents/` and a visitor clicking the building is told nothing. But editing
a generated record by hand would fail the very drift check that makes the
anonymous parcels trustworthy. So the link is data: the household programme names
the roof, this module hands the resulting `occupants` block to whichever generator
owns that roof, and both parcels stay re-derivable from their recipes.

An adopted roof's own existence, position and footprint stay exactly as
conjectural as they were. Nothing here is evidence that a building stood on that
spot; it is evidence about who the town must have held, attached to a roof the
programme had already placed.

THE THIRD PROGRAMME IS THE PLACEMENT POLICY'S PLATTED DEAL (T-1638, piece 1 of T-1200;
liberty L276 over L270). `tools/seat_platted_ground_1835.py` deals the committed plat to the
households the address book leaves standing at a BAND, and every one of its 108 seats ADOPTS
a roof that already stands. Until T-1638 that reached the person's card and stopped there:
the building said `Anonymous count-unit toward the July 1835 665-roof programme` and named
nobody. `tools/name_the_keepers_1835.py` writes the ledger and this module spends it, for the
third time for the same reason — a generated record edited by hand is drift.

It is the one programme here that hands over TWO blocks. `occupants` is the prose a card
shows; `resident_assignment` carries `status: assigned` and the household id, which is the
machine-readable half and is what lets the deal recognise its own writing and stay
idempotent. The id is deliberately absent from the prose: `generate_dooryard_pickets.py`
admits a lot for a garden on an id appearing there, and a keeper a policy deal seats is not
a measurement of anybody's garden.

THE SECOND PROGRAMME IS STREET-FACE ADOPTION (T-0354, the owner's ruling of
2026-08-29; docs/STREET-FACE-ADOPTION.md, liberty L212). Where the newspaper
register can place a DOCUMENTED business no closer than a platted street, the
business adopts a reconstructed roof already standing on that street face.
`tools/adopt_street_faces.py` derives the allocation into
`data/research/newspapers/street_face_adoptions.json`; until T-0417 nothing SPENT
it, so the policy's own file said in as many words that the table allocates and
"nothing here writes a card" while the roofs still carded as anonymous
count-units. This module is where it is spent, for the same reason the household
programme is: hand-editing a generated record would fail the drift check that
makes the anonymous parcels trustworthy.

The difference between the two is the difference the cards have to be able to say
in one breath. The household layer names NO PERSON — it hypothesises an occupant
from the town's arithmetic. The adoption layer names a business the papers PRINT,
with its trade, its street and its claims cited; what is invented there is the
whole of the PLACEMENT, which is why the block is still graded `reconstructed`.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROGRAMME = ROOT / "data" / "reconstruction" / "1835_inferred_household_programme.json"
ADOPTIONS = ROOT / "data" / "research" / "newspapers" / "street_face_adoptions.json"
KEEPERS = ROOT / "data" / "reconstruction" / "1835_roof_keepers.json"
STATED_USES = ROOT / "data" / "reconstruction" / "1835_stated_uses.json"
STATED_USE_SOURCE = "owner_chicago_1835_reconstruction_spec_2026"

# A claim id is `<issue_id>#<claim>`, and an issue id opens with the paper's name. The
# structure schema wants the SOURCE RECORD rather than the issue, and there are two.
CORPUS_SOURCE = (
    ("chicago_american_", "chicago_american_1835"),
    ("chicago_democrat_", "chicago_democrat_1833_1835"),
)


class LedgerError(RuntimeError):
    """Two programmes claim one roof, or an adoption is malformed."""

#: How a card says WHICH face the roof shows the street, because the two readings the
#: ruling adopts are two different claims and a visitor is owed the difference. A lot
#: front is the plat speaking; a corner side is the owner's ruling of 2026-08-30 that a
#: building on a corner stands on both the streets it meets. A record carrying anything
#: else — the centreline band he declined in the same breath — is refused here rather
#: than quietly worded as one of these.
FACE_NOTE = {
    "lot front": "THE ROOF'S PLATTED LOT FACES %s, which is the plat's own answer to "
                 "which street it fronts.",
    "corner side": "THE ROOF ENDS ITS PLATTED TIER AGAINST %s, so it is a corner "
                   "building and stands on that street as well as on the one its lot "
                   "faces — the owner's ruling of 2026-08-30 (T-0416). Nothing about the "
                   "roof changed and no geometry was raised to seat this business.",
}

TRADE_LABEL = {
    "barber_surgeon": "barber-surgeon",
    "boarding_house_keeper": "boarding-house keeper",
    "harness_maker": "harness maker",
    "tavern_keeper": "tavern keeper",
}


def label(occupation: str) -> str:
    return TRADE_LABEL.get(occupation, occupation.replace("_", " "))


def _load() -> dict:
    if not PROGRAMME.exists():
        return {}
    return json.loads(PROGRAMME.read_text(encoding="utf-8"))


def _sources(cites: list[str]) -> list[str]:
    """The source records the cited claims come out of, deduplicated and sorted."""
    out = set()
    for cite in cites:
        for prefix, source_id in CORPUS_SOURCE:
            if cite.startswith(prefix):
                out.add(source_id)
                break
        else:
            raise LedgerError("the adoption cites %r, which names no corpus source" % cite)
    return sorted(out)


def street_face_occupancy(doc: dict | None = None) -> dict[str, dict]:
    """structure_id -> the `occupants` block a street-face adoption gives that roof.

    Reads the DERIVED table and re-asserts the policy's four limits at the point of
    spending, rather than trusting that whoever wrote the table kept them: a record that
    has grown a lot, an order that has become a claim, a roof outside the anonymous layer
    or an adoption with nothing to cite is refused here as well as there. A limit checked
    only where it is produced is a limit that stops being checked the day something else
    produces it.
    """
    if doc is None:
        if not ADOPTIONS.exists():
            return {}
        doc = json.loads(ADOPTIONS.read_text(encoding="utf-8"))
    blocks: dict[str, dict] = {}
    for row in doc.get("adoptions", []):
        sid = row.get("structure_id") or ""
        who = row.get("business_id", "?")
        if not sid.startswith("recon_"):
            raise LedgerError("%s adopts %r, which is not an anonymous reconstructed "
                              "roof" % (who, sid))
        if row.get("lot") is not None or row.get("claims_lot") is not False:
            raise LedgerError("%s does not declare `lot: null, claims_lot: false` — "
                              "an adoption claims a street face and never a lot" % who)
        if row.get("order_is_a_claim") is not False:
            raise LedgerError("%s makes its order on the face a claim" % who)
        cites = row.get("cites") or []
        if not cites:
            raise LedgerError("%s cites no printing of its street" % who)
        if sid in blocks:
            raise LedgerError("%s is the second business on %s — one roof, one business"
                              % (who, sid))
        trade = row.get("trade")
        name = row["business_name"]
        street = row["street_name"]
        face = row.get("face")
        if face not in FACE_NOTE:
            raise LedgerError("%s took %r, which is not a face the ruling adopts" % (who, face))
        printings = ("%d printing%s, %s to %s"
                     % (row["mentions"], "" if row["mentions"] == 1 else "s",
                        row["first_issue"], row["last_issue"]))
        blocks[sid] = {
            "value": "%s — %s" % (name, trade) if trade else name,
            # The BUSINESS is documented and its street is documented. That THIS roof
            # held it is the invention, and `occupants` is an attribute of the roof, so
            # the grade is the bottom tier — the same reasoning the household layer above
            # applies to itself, and the reason L212 exists.
            "confidence": "reconstructed",
            "sources": _sources(cites),
            "note": ("SEATED BY THE STREET-FACE ADOPTION POLICY (docs/STREET-FACE-"
                     "ADOPTION.md, the owner's ruling of 2026-08-29 for T-0354, extended "
                     "2026-08-30 for T-0416; liberty L212). The newspaper register places "
                     "this business on " + street
                     + " AND NOTHING NARROWER — " + printings + ", claims "
                     + ", ".join(cites) + " — so it takes the STREET FACE and not a lot. "
                     + FACE_NOTE[face] % street + " "
                     "WHICH roof on that face it is given is an allocation by "
                     "tools/adopt_street_faces.py and not a reading of any source, and "
                     "nothing here says this business stood nearer the corner than any "
                     "other on the same face. THE ROOF'S OWN EXISTENCE, POSITION AND "
                     "FOOTPRINT REMAIN CONJECTURAL and are unchanged by the adoption: "
                     "the business is documented, the building under it is not, and this "
                     "attribute is graded `reconstructed` because the invented part is "
                     "the whole of the placement."),
        }
    return blocks


def occupancy() -> dict[str, dict]:
    """structure_id -> the `occupants` attested block that structure should carry.

    Only anonymous `recon_*` roofs appear here; the programme's own new records
    carry their occupants inline.
    """
    out: dict[str, dict] = {}
    programme = _load()
    # T-0516. THE HOUSEHOLD LAYER IS RETIRED, AND A RETIRED ARGUMENT SEATS NOBODY.
    # The owner retired the reconstructed resident population on 2026-09-02 —
    # "remove any pre-existing reconstructed people from the resident list and
    # household" — and ruled the geometry kept: "keep the geometry for the later
    # placement sweep". Its 101 households were deleted from `data/residents/` that
    # day, but the ADOPTIONS they had made were not, so 104 anonymous roofs went on
    # carrying an `occupants` block that named a household no file held, and a
    # visitor clicking one was told about people who had been retired weeks before.
    #
    # This is the one place that can undo it, because these roofs are generated and
    # a hand-edit would fail the drift check that makes the anonymous parcels
    # trustworthy. An adoption whose adopter no longer exists yields no block at
    # all, so the roof returns to what it was before the household layer reached
    # it: an anonymous count-unit of the 665-roof programme, carrying no occupant.
    # Nothing is deleted here and no geometry moves — the recipe still records
    # which roof each household had taken, and if the owner ever revives the
    # population `resident_population_active` turning back to true restores every
    # one of these blocks from that same record.
    if programme.get("resident_population_active") is False:
        # T-1638. The retirement of 2026-09-02 took the RECONSTRUCTED RESIDENT POPULATION's
        # adoptions off these roofs. It did not touch a programme that seats somebody the
        # town's own records name: the street-face adoptions have come through this return
        # since the day it was written, and the platted deal's keepers come through it for
        # the same reason. Missing this branch is how the keepers reached the ledger and not
        # the cards on the first attempt — this return is the live path, not the fallback.
        return _with_keepers(dict(street_face_occupancy()))
    for h in programme.get("households", []):
        for key in ("lives_at", "works_at"):
            sid = h.get(key)
            if not sid or not sid.startswith("recon_"):
                continue
            entry = out.setdefault(sid, {"households": [], "roles": []})
            if h["id"] not in entry["households"]:
                entry["households"].append(h["id"])
                entry["roles"].append((h["occupation"], key, h["ordinal"], h["of"]))

    blocks: dict[str, dict] = {}
    for sid, entry in out.items():
        parts = []
        for occ, key, ordinal, of in entry["roles"]:
            what = "dwelling of" if key == "lives_at" else "workplace of"
            parts.append(f"the {what} an inferred {label(occ)}'s household "
                         f"({ordinal} of {of} this layer infers)")
        blocks[sid] = {
            "value": "An inferred household; no name is claimed",
            # Bottom tier. The note below says the occupant is hypothesised and is
            # not a person; grading the claim as reasoned-from-evidence-about-this-
            # roof contradicted its own text, and left 83 invented roofs rendering
            # as though somebody had recorded who lived in them.
            "confidence": "reconstructed",
            "sources": ["andreas_1884_v1", "owner_chicago_1835_reconstruction_spec_2026"],
            "note": ("ADOPTED BY THE INFERRED-HOUSEHOLD PROGRAMME (docs/ROADMAP.md K1, phase "
                     "two). This anonymous roof is " + " and ".join(parts) + ": "
                     + ", ".join(entry["households"]) + " in data/residents/households/. THE "
                     "ROOF'S OWN EXISTENCE, POSITION AND FOOTPRINT REMAIN CONJECTURAL and are "
                     "unchanged by the adoption; what the adoption adds is an argued occupant "
                     "instead of an anonymous count-unit. The occupant is hypothesised from the "
                     "town's demonstrable needs - the 1835 census of 3,265 people in 398 "
                     "dwellings against the trades Andreas's 1833 roster names - and is not a "
                     "person: no name is claimed and no figure is drawn."),
        }

    # The two programmes must never both claim a roof. `adopt_street_faces.py` refuses a
    # roof `data/residents/` seats a NAMED household in, but the inferred layer's
    # households are not in `data/residents/` under a name, so nothing upstream stops the
    # collision — and silently letting one block win would put a documented shopkeeper
    # into an inferred labourer's cottage, or lose the labourer, with no record either way.
    for sid, block in street_face_occupancy().items():
        if sid in blocks:
            raise LedgerError(
                "%s is claimed by both the inferred-household programme and a street-face "
                "adoption. One roof, one occupant: re-run tools/adopt_street_faces.py, "
                "which must refuse a roof the household layer already holds." % sid)
        blocks[sid] = block
    return _with_keepers(blocks)


def _with_keepers(blocks: dict[str, dict]) -> dict[str, dict]:
    """The platted deal's keepers, added to whatever the other programmes already seated.

    Both of `occupancy()`'s exits come through here, because one of them is the live path
    and the other is the one a revival of the retired population would take.
    """
    for sid, block in keeper_occupancy().items():
        if sid in blocks:
            raise LedgerError(
                "%s is claimed by both the platted deal's keepers and another programme. "
                "One roof, one occupant: the deal's own adoption test refuses a roof whose "
                "record already states an occupancy, so a collision here means the ledger "
                "and the deal have come apart — re-run "
                "tools/name_the_keepers_1835.py --build." % sid)
        blocks[sid] = block
    for sid, block in stated_use_occupancy().items():
        if sid in blocks:
            raise LedgerError(
                "%s is given a stated use and is also seated by another programme. A stated "
                "use is for a roof NOBODY holds, so it retires the moment a keeper arrives: "
                "take its row out of data/reconstruction/1835_stated_uses.json." % sid)
        blocks[sid] = block
    return blocks


def stated_use_occupancy(doc: dict | None = None) -> dict[str, dict]:
    """T-1782. The `occupants` block of every roof whose USE is stated rather than seated.

    THE FOURTH PROGRAMME, and the only one that seats nobody. The order book's
    `every_structure_occupied_or_its_use_stated` asks for an occupant OR a stated use, and
    until now only the first half had anywhere to go: a stable in somebody's yard, or a
    work shed no household's trade reaches, carded as an anonymous count-unit forever.
    `data/reconstruction/1835_stated_uses.json` is authored, one row per roof, each with
    what bounds it. The block it yields says what the building is FOR, graded
    `reconstructed` and citing the spec the roof itself was raised under — and it never
    names a person or a household id, because a stated use is not a keeper.
    """
    doc = doc if doc is not None else (
        json.loads(STATED_USES.read_text(encoding="utf-8")) if STATED_USES.exists() else {})
    out: dict[str, dict] = {}
    for row in doc.get("rows") or []:
        sid, value, bound = row.get("structure_id"), row.get("value"), row.get("bounded_by")
        if not sid or not sid.startswith("recon_") or not value or not bound:
            raise LedgerError("a stated-use row needs an anonymous `recon_` roof, the use "
                              "and what bounds it")
        if "hh_" in json.dumps(row):
            raise LedgerError("%s names a household id in a stated use, which is a keeper "
                              "and not a use (and grows a dooryard garden, "
                              "tools/generate_dooryard_pickets.py clause 4)" % sid)
        if sid in out:
            raise LedgerError("%s is given two stated uses" % sid)
        out[sid] = {
            "value": value,
            "confidence": "reconstructed",
            "sources": [STATED_USE_SOURCE],
            "note": ("A STATED USE, NOT AN OCCUPANT (data/reconstruction/1835_stated_uses.json, "
                     "%s; liberty %s). No household holds this roof and nobody is named for it: "
                     "what is stated is what the building was for. %s The roof's own existence, "
                     "position and footprint remain the invention they were."
                     % (row.get("ticket") or doc.get("ticket", "T-1782"),
                        doc.get("liberty", "L310"), bound)),
        }
    return out


def keeper_occupancy(doc: dict | None = None) -> dict[str, dict]:
    """The `occupants` block of every roof the platted deal seated a household on.

    Verbatim off `data/reconstruction/1835_roof_keepers.json`, which
    `tools/name_the_keepers_1835.py --check` re-derives on every commit. Nothing is
    composed here: the ledger's own `--check` and the generator that spends it have to be
    reading one statement, not two that agree today.
    """
    doc = doc if doc is not None else (
        json.loads(KEEPERS.read_text(encoding="utf-8")) if KEEPERS.exists() else {})
    out: dict[str, dict] = {}
    for row in doc.get("written") or []:
        sid = row.get("structure_id")
        block = row.get("occupants")
        if not sid or not block:
            raise LedgerError("a keeper row names no roof or carries no occupants block")
        if block.get("confidence") != "reconstructed":
            raise LedgerError("%s is graded %r — a dealt lot is the invention, so a keeper "
                              "is never anything but reconstructed"
                              % (sid, block.get("confidence")))
        if not block.get("sources"):
            raise LedgerError("%s cites nothing — a keeper's sources carry the household's "
                              "NAME, and a card may not state one on this project's word "
                              "alone" % sid)
        if "hh_" in json.dumps(block):
            raise LedgerError("%s names a household id in its occupants PROSE, which grows "
                              "a dooryard garden as a side effect of naming a keeper "
                              "(tools/generate_dooryard_pickets.py clause 4)" % sid)
        if sid in out:
            raise LedgerError("%s is given two keepers" % sid)
        out[sid] = block
    return out


def keeper_assignments(doc: dict | None = None) -> dict[str, dict]:
    """The `resident_assignment` block of every roof the platted deal seated a household on."""
    doc = doc if doc is not None else (
        json.loads(KEEPERS.read_text(encoding="utf-8")) if KEEPERS.exists() else {})
    out: dict[str, dict] = {}
    for row in doc.get("written") or []:
        sid, block = row.get("structure_id"), row.get("resident_assignment")
        if not sid or not block:
            raise LedgerError("a keeper row names no roof or carries no assignment block")
        if block.get("status") != "assigned" or not block.get("household_id"):
            raise LedgerError("%s is written as a keeper's roof and its assignment does not "
                              "say who or that it is assigned" % sid)
        out[sid] = block
    return out


def keeper_refusals(doc: dict | None = None) -> dict[str, dict]:
    """The `resident_assignment` block of every roof the deal seated and this pass refused.

    T-1675. A refused roof says so on the record, so `status` is `unassigned` and there is
    no `household_id` — the two things that keep it honest. Without the id the deal's own
    `adoptable()` still offers the roof (it reserves on the id and nothing else), so writing
    the refusal changes no seat; and the letter-list ruling of 2026-08-30, which forbids a
    structure record naming one of those people, is respected rather than routed around.
    Both are refused here rather than trusted, because this is the hand-over point where a
    keeper block becomes part of a re-derived record.
    """
    doc = doc if doc is not None else (
        json.loads(KEEPERS.read_text(encoding="utf-8")) if KEEPERS.exists() else {})
    out: dict[str, dict] = {}
    for row in doc.get("refused") or []:
        if not row.get("on_the_card"):
            continue
        sid, block = row.get("structure_id"), row.get("resident_assignment")
        if not sid or not block:
            raise LedgerError("a refusal is marked as said on the roof and carries no "
                              "assignment block")
        if block.get("status") != "unassigned":
            raise LedgerError("%s is a refused seat's roof and its assignment does not say "
                              "unassigned" % sid)
        if block.get("household_id"):
            raise LedgerError("%s is a refused seat's roof and names a household anyway — "
                              "the ruling of 2026-08-30 refuses that cohort a roof, and an "
                              "id here is the claim it forbids" % sid)
        if not (block.get("note") or "").strip():
            raise LedgerError("%s is refused and says no reason, which is the silence "
                              "T-1675 was filed against" % sid)
        if sid in out:
            raise LedgerError("%s is refused twice" % sid)
        out[sid] = block
    return out


def self_test() -> int:
    """The collision refusal and the limits fire, and the two layers stay distinguishable.

    Every one of these is a way the ledger could go quietly wrong: a roof claimed twice, a
    lot smuggled into an adoption, an order that has become a claim, an adoption with
    nothing to cite. A gate nobody has watched fail is decoration.
    """
    import copy
    failed = 0

    def case(label: str, fn) -> None:
        nonlocal failed
        try:
            fn()
        except LedgerError as exc:
            print("  fires: %s — %s" % (label, str(exc)[:70]))
            return
        failed = 1
        print("  FAIL  %s did not fire" % label)

    doc = json.loads(ADOPTIONS.read_text(encoding="utf-8")) if ADOPTIONS.exists() else {}
    rows = doc.get("adoptions") or []
    if not rows:
        print("  FAIL  nothing is adopted, so nothing can be broken")
        return 1

    def spend(mutate) -> None:
        """Break the committed table IN MEMORY and spend the copy. The self-test never
        writes to `data/`: a gate that edits the tree it is gating can leave it broken."""
        broken = copy.deepcopy(doc)
        mutate(broken)
        street_face_occupancy(broken)

    case("an adoption that claims a lot",
         lambda: spend(lambda b: b["adoptions"][0].update(claims_lot=True)))
    case("an adoption whose order has become a claim",
         lambda: spend(lambda b: b["adoptions"][0].update(order_is_a_claim=True)))
    case("an adoption citing no printing of its street",
         lambda: spend(lambda b: b["adoptions"][0].update(cites=[])))
    case("an adoption on a roof outside the anonymous layer",
         lambda: spend(lambda b: b["adoptions"][0].update(structure_id="green_tree_tavern")))
    case("two businesses on one roof",
         lambda: spend(lambda b: b["adoptions"].__setitem__(
             1, dict(b["adoptions"][1],
                     structure_id=b["adoptions"][0]["structure_id"]))))
    case("a claim id that names no corpus source",
         lambda: spend(lambda b: b["adoptions"][0].update(cites=["the_tribune_1871#c1"])))
    # The face the owner DECLINED on 2026-08-30. A record reaching its street only by the
    # centreline band would otherwise be spent into a card that reads exactly like a lot
    # front — the one shape of this policy overstating itself that no other case catches.
    case("an adoption on the centreline band the owner declined",
         lambda: spend(lambda b: b["adoptions"][0].update(face="centreline band")))

    keepers = json.loads(KEEPERS.read_text(encoding="utf-8")) if KEEPERS.exists() else {}
    if not (keepers.get("written") or []):
        print("  FAIL  no keeper is written, so nothing of the third programme can break")
        return 1

    def spend_keepers(mutate) -> None:
        broken = copy.deepcopy(keepers)
        mutate(broken)
        keeper_occupancy(broken)
        keeper_assignments(broken)

    case("a keeper graded above `reconstructed`",
         lambda: spend_keepers(lambda b: b["written"][0]["occupants"].update(
             confidence="documented")))
    case("a keeper citing nothing for its own name",
         lambda: spend_keepers(lambda b: b["written"][0]["occupants"].update(sources=[])))
    case("a household id smuggled into the occupants prose",
         lambda: spend_keepers(lambda b: b["written"][0]["occupants"].update(
             note=b["written"][0]["occupants"]["note"] + " hh_somebody")))
    case("two keepers on one roof",
         lambda: spend_keepers(lambda b: b["written"].__setitem__(
             1, dict(b["written"][1],
                     structure_id=b["written"][0]["structure_id"]))))
    case("an assignment that does not say it is assigned",
         lambda: spend_keepers(lambda b: b["written"][0]["resident_assignment"].update(
             status="unassigned")))

    households = {sid for sid in occupancy()
                  if sid not in street_face_occupancy()
                  and sid not in keeper_occupancy()}
    adopted = set(street_face_occupancy())
    overlap = households & adopted
    if overlap:
        print("  FAIL  %d roof(s) are claimed by both layers: %s"
              % (len(overlap), ", ".join(sorted(overlap))))
        failed = 1
    else:
        print("  ok:    %d inferred-household roof(s) and %d street-face adoption(s) "
              "share none" % (len(households), len(adopted)))

    grades = {block["confidence"] for block in street_face_occupancy().values()}
    if grades != {"reconstructed"}:
        print("  FAIL  an adopted roof is graded %s — the placement is the invention"
              % ", ".join(sorted(grades)))
        failed = 1
    else:
        print("  ok:    every street-face adoption is graded `reconstructed`, because "
              "the invented part is which roof and not which business")

    if failed:
        print("SELF-TEST FAIL")
        return 1
    print("SELF-TEST PASS — the ledger refuses every way an adoption or a keeper could "
          "lie (12 cases)")
    return 0


if __name__ == "__main__":
    import sys as _sys
    if "--self-test" in _sys.argv:
        raise SystemExit(self_test())
    for k, v in sorted(occupancy().items()):
        print(k, "->", v["note"][:90], "...")
