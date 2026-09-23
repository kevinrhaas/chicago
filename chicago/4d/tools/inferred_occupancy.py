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
        return dict(street_face_occupancy())
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
    return blocks


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

    households = {sid for sid in occupancy()
                  if sid not in street_face_occupancy()}
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
    print("SELF-TEST PASS — the ledger refuses every way an adoption could lie (7 cases)")
    return 0


if __name__ == "__main__":
    import sys as _sys
    if "--self-test" in _sys.argv:
        raise SystemExit(self_test())
    for k, v in sorted(occupancy().items()):
        print(k, "->", v["note"][:90], "...")
