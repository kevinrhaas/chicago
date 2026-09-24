#!/usr/bin/env python3
"""Compile data/businesses/ — one record per business, with a tier on every field.

    tools/compile_businesses.py --build       rewrite the compiled records
    tools/compile_businesses.py --check       the gate
    tools/compile_businesses.py --self-test   the gate's assertions still fire
    tools/compile_businesses.py --community-report   the shares of docs/RESEARCH/business_community_1835.md

THE STAFFING OVERLAY (T-1422). data/businesses/rulings/establishment_staffing.json is laid
over the compiled records by `apply_staffing_overlay`, and it is the only thing in this
file that adds to a record the register did not print. It supplies two fields and no
others: `staff`, which a compiled record otherwise always has none of, and `staffing`,
the block saying what KIND of hand the 1835 staffing model puts about this kind of house,
naming nobody. It exists because T-1411 split over the absence of it — the schools and
the printing offices are COMPILED, so a reading about their hands had nowhere to be
written down at all, and authored/ holds whole records rather than additions to compiled
ones. An entry naming a record the register does not compile is refused.

T-1310, of T-1180. THERE WAS NOWHERE TO WRITE A BUSINESS DOWN. The business layer was
three DERIVED files — the newspaper claims, gazetteer.json, register_1835.json — and a
business existed in the scene only as a structure whose `function`/`occupants` block
named it. The register row has no staff field, no tier, no `sources[]`, and no dates
beyond the first and last issue a notice ran; a person's `works_at` is a bare structure
id. The owner's ask — a complete list of attested, inferred and then reconstructed
businesses, with the staff of each as part of their proprietors' resident profiles —
had no place to land. This builds the place. IT RECONSTRUCTS NOTHING: every one of the
196 records below is the register's own reading, restated with its tier made explicit
and its limits made queryable.

DERIVED, NEVER AUTHORED, for the same reason the gazetteer and the register are. A
`compiled_from_register` record is rewritten whole by `--build` and `--check` refuses a
committed copy a rebuild would not produce, so a hand edit to a compiled record is a
red gate rather than a silent divergence. A record a human means to author goes in
data/businesses/authored/ — which `--build` reads, validates and carries into the index
untouched. That directory is where T-1182's inferred-by-audit firms and T-1184's
reconstructions will be written; it is empty today, and the compiler is built to find
it empty without complaining.

THE ID SCHEME, AND WHY IT IS NOT THE ONE T-1180 NAMED. T-1180 asks for
`biz_<surname>_<trade>`. Derived over the 196 that scheme collides 27 times — five
houses land on `biz_montgomery_other`, four on `biz_wentworth_tavern`, two on
`biz_calhoun_printing_office` — and each collision is the same question: are these two
printed notices one house or two? That is an identity ruling, it is T-1182's to make
with the sources in front of it, and a compiler that settled it by appending `_2` would
be publishing an adjudication nobody made. So a compiled record takes the register's
own id with its `business_` prefix replaced by `biz_`: 1:1 with the printed notice it
comes from, collision-free by construction, and reversible, with `register_id` on the
record saying so out loud. `biz_<surname>_<trade>` and `rcb_…` stay in the schema for
the records a human authors, where the identity question has an author to answer it.

WHAT A TIER MEANS HERE. The ladder is the resident layer's, unchanged — attested,
inferred, reconstructed. A printed name is attested. The LINK from that printed name to
a town card is a separate claim from the name itself, and it is the register's: where
the register matched the name to a card, `person_id` carries the card and the basis
says which action made the match; where it did not, `person_id` is null and the basis
says the town does not hold that person yet. A null there is a finding, not a gap to be
filled by guessing.

THE LIMITS ARE DATA NOW. 61 of the register's businesses are `street_only` and 62 are
`unplaceable` at the scene date: the paper gives a street and no house, or no anchor at
all. Those are not missing locations — they are locations whose resolution the evidence
stops short of, and they were carried in prose in an `action_note` where nothing could
count them. Each is a `locations[]` entry with a `kind` that names the limit and a
`limit_reason` that quotes the register's reason, so "how many of the town's businesses
can we actually place?" is a query rather than a re-reading.
"""

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compile_gazetteer import (  # noqa: E402  — the identity policy has one home
    ROOT, RESEARCH, GAZETTEER, dumps, load_json,
)

REGISTER = RESEARCH / "register_1835.json"
RULINGS = RESEARCH / "trade_class_rulings.json"
RESIDENTS = ROOT / "data" / "residents"
BUSINESSES = ROOT / "data" / "businesses"
AUTHORED = BUSINESSES / "authored"
STAFFING_OVERLAY = BUSINESSES / "rulings" / "establishment_staffing.json"
RECONSTRUCTED_STAFF_OVERLAY = (ROOT / "data" / "reconstruction"
                              / "1835_business_staff_overlay.json")
INDEX = BUSINESSES / "index.json"
SCHEMA = ROOT / "data" / "businesses.schema.json"
STREETS = ROOT / "data" / "streets" / "1835.json"
STRUCTURES = ROOT / "data" / "structures"

REGISTER_PREFIX = "business_"
ID_PREFIX = "biz_"

GRADES = ("attested", "inferred", "reconstructed")


# ---------------------------------------------------------------- reading the town

# Every directory under data/residents/ that holds CARDS. The research mints re-derive
# `households/`, so the reconstruction programme writes its people beside it instead —
# `readmitted/` (T-1172), `reconstructed_trades/` (T-1347), `lodgers/` (T-1371), and
# `transients/` when it lands — and tools/compile_scene.py overlays all of them onto the
# scene. tools/reconstruct_underdocumented.py already reads the set this way.
RESIDENT_CARD_DIRS = ("households", "merged", "readmitted", "reconstructed_trades",
                      "lodgers", "transients", "underdocumented")


def person_ids(residents_dir=None):
    """Every person id the resident layer holds, so a link can be refused when it dangles.

    The index lists HEADS, and a proprietor is routinely not one — Archibald Clybourn
    heads a household and the clerk in his market does not — so the ids come from the
    household files themselves rather than from the index's summary rows.

    AND THE RECONSTRUCTION'S CARDS COUNT (T-1184). A reconstructed business adopts a
    reconstructed trade head as its proprietor rather than minting a person of its own —
    the head's card says so itself — and a link to a card this layer really holds is not
    a dangling link merely because the card sits outside `households/`. Reading the whole
    set here only ever LOOSENS the refusal below, and it loosens it onto people the scene
    already carries.
    """
    root = Path(residents_dir or RESIDENTS)
    ids = set()
    for folder in RESIDENT_CARD_DIRS:
        for path in sorted(root.glob("%s/*.json" % folder)):
            doc = load_json(path)
            record = doc.get("superseded_record", doc)
            for person in record.get("persons", []) or []:
                if person.get("id"):
                    ids.add(person["id"])
    return ids


def person_communities(residents_dir=None):
    """The community of every person, exactly as derive_person_community.py left it.

    T-1378, from T-1177. `proprietor_community` stood at the literal string "unattested"
    on all 196 records from the day the layer was compiled, and the comment beside it
    said what it was waiting for: NEVER INFERRED FROM A SURNAME. This is the reading that
    does not have to be. data/residents/community.json is a committed derivation off the
    household `origin` blocks and the reconstruction name pools — a claim about a person,
    made once, in one place — so a house can be read off the PEOPLE its record names
    rather than off the letters in their names.
    """
    path = Path(residents_dir or RESIDENTS) / "community.json"
    if not path.exists():
        raise SystemExit("data/residents/community.json is missing; it is what this layer "
                         "reads a proprietor's community from — run "
                         "tools/derive_person_community.py first")
    return load_json(path).get("persons") or {}


def community_vocabulary():
    """The closed vocabulary, from the resident layer's own rules file.

    ONE VOCABULARY, NOT TWO. The schema used to carry a second list of its own
    (`anglo_american`, `black`, ...) whose description already claimed to be "shared with
    the resident layer", and it was not: the resident layer separates New England, New
    York, British and Southern where that list said `anglo_american`, and says
    `free_black` where it said `black`. Nothing was ever written in the schema's terms —
    every record read `unattested` — so the divergence cost no record a rewrite, and
    T-1378 ends it by reading the terms from where they are decided.
    """
    rules = load_json(RESIDENTS / "community_rules.json")
    return [(v["value"], v["label"]) for v in rules["vocabulary"]]


def weaker(a, b):
    """The weaker of two tiers — the ladder derive_person_community.py caps on."""
    if a not in GRADES:
        return b
    if b not in GRADES:
        return a
    return GRADES[max(GRADES.index(a), GRADES.index(b))]


def derive_proprietor_community(proprietors, partners, communities):
    """The community of a house, read off the people its own record names.

    THE RULE, and what each half of it refuses.

      `proprietors_agree` — every proprietor and partner the resident layer holds a card
        for carries the same community, and that is the house's. The tier is the WEAKEST
        of theirs, CAPPED AT `inferred`: a person's community is evidence about the
        PERSON, and a house is not its keeper, so reading one onto the other is an
        inference about the house however attested the keeper's own card.

      `proprietors_disagree` — two keepers, two communities, and nothing in the record
        chooses between them. `unknown`, with every one of them named in `from`, so the
        disagreement is printed on the card instead of being settled by list order.

      `no_community_on_the_people_named` — the house names people the layer holds cards
        for and knows no community for any of them. `no_person_linked` — it names nobody
        the layer holds, or nobody at all. Both answer `unknown` and they are told apart
        because they are different silences: the first is a gap in the resident layer,
        the second in the register.

    STAFF ARE NOT READ. A clerk's community is evidence about the clerk, not about the
    house that employed him. (`staff` stood empty on every compiled record until T-1422,
    because the papers name owners and almost never a clerk; the staffing overlay has
    since put one row on one record, and the rule is still a rule rather than a filter.)
    """
    named = list(proprietors) + list(partners)
    rows = []
    for person in named:
        pid = person.get("person_id")
        if not pid:
            continue
        held = communities.get(pid) or {}
        rows.append({
            "person_id": pid,
            "name": person.get("name"),
            "role": person.get("role"),
            "community": held.get("value") or "unknown",
            "tier": held.get("tier"),
        })
    rows.sort(key=lambda r: (r["person_id"], r["role"] or ""))

    speaking = [r for r in rows if r["community"] != "unknown"]
    values = sorted({r["community"] for r in speaking})

    if len(values) == 1:
        tier = None
        for row in speaking:
            tier = weaker(tier, row["tier"]) if tier else (row["tier"] or "inferred")
        tier = weaker(tier or "inferred", "inferred")
        who = ", ".join("%s (%s)" % (r["name"], r["community"]) for r in speaking)
        return {
            "value": values[0],
            "tier": tier,
            "rule": "proprietors_agree",
            "basis": ("The %d keeper(s) this record names and the resident layer holds a card "
                      "for all read %s: %s. A house is not its keeper, so the reading is an "
                      "inference about the house and is capped there."
                      % (len(speaking), values[0], who)),
            "from": rows,
        }
    if len(values) > 1:
        return {
            "value": "unknown",
            "tier": None,
            "rule": "proprietors_disagree",
            "basis": ("The keepers this record names do not read as one community (%s), and "
                      "nothing in the record chooses between them. Each is named above."
                      % ", ".join(values)),
            "from": rows,
        }
    if rows:
        return {
            "value": "unknown",
            "tier": None,
            "rule": "no_community_on_the_people_named",
            "basis": ("This record names %d person/people the resident layer holds a card for "
                      "and the layer knows no community for any of them. The silence is in the "
                      "resident layer, not in the register." % len(rows)),
            "from": rows,
        }
    return {
        "value": "unknown",
        "tier": None,
        "rule": "no_person_linked",
        "basis": ("This record names nobody the resident layer holds a card for, so there is "
                  "no person to read a community off. The silence is in the register."),
        "from": [],
    }


def works_at_rows(residents_dir=None):
    """The households whose `works_at` names a structure — the crosswalk's left-hand side."""
    index = load_json(Path(residents_dir or RESIDENTS) / "index.json")
    return [
        {"household_id": h["id"], "head": h.get("head"), "structure_id": h["works_at"]}
        for h in index["households"]
        if h.get("works_at")
    ]


# ---------------------------------------------------------------- building a record

def record_id(register_id):
    if not register_id.startswith(REGISTER_PREFIX):
        raise ValueError("a register business id must start with %r: %r"
                         % (REGISTER_PREFIX, register_id))
    return ID_PREFIX + register_id[len(REGISTER_PREFIX):]


def person_entry(name, role, register_person, town_ids, evidence, claim_ids):
    """One named person on a business, with the LINK tiered separately from the name."""
    resolved = None
    if register_person and register_person.get("action") == "enrich":
        target = register_person.get("action_target")
        if target in town_ids:
            resolved = target

    if resolved:
        basis = ("The register matches the printed name to the town card %s (action: enrich), "
                 "so this is the same person the resident layer already holds." % resolved)
    elif register_person:
        basis = ("The register holds this printed name as %s with action %r: the town does not "
                 "carry a card for them under an id this record can name, so the reading is the "
                 "name and not yet a person." % (register_person["id"], register_person.get("action")))
    else:
        basis = ("A proprietor string the gazetteer reads as a person, which the register's own "
                 "person list does not carry under this spelling. The name is the evidence; no "
                 "link is claimed.")

    return {
        "name": name,
        "person_id": resolved,
        "register_person_id": register_person["id"] if register_person else None,
        "role": role,
        # THE PRINTING WINDOW IS THE BOUND, NOT THE TENURE. The paper says this person
        # was in this house on the days it printed; it does not say when they joined it
        # or left. The dates are carried because they are the only bound there is, and
        # the basis says what they are so no reader takes them for a start and an end.
        "from": evidence.get("first_issue"),
        "to": evidence.get("last_issue"),
        "tier": "attested",
        "basis": basis + " Dated by the printing window, which bounds the reading and does "
                         "not date the partnership.",
        "source_id": "chicago_newspapers_1833_1835",
        "claim_ids": list(claim_ids),
        # The other styles the paper printed this same person under, folded onto this
        # row by `fold_printed_styles`. Empty on all but the twelve it folds.
        "also_printed_as": [],
    }


def structure_titles():
    """`structure_id` -> the name the town gives that roof, for a card to print.

    The committed structures are the only place that mapping lives. A landmark the
    town does not hold is not a landmark this layer may name, so a miss here is a
    refusal in `anchor_of` and never a null quietly carried forward.
    """
    out = {}
    for path in sorted(STRUCTURES.glob("*.json")):
        doc = load_json(path)
        if doc.get("id"):
            out[doc["id"]] = doc.get("name") or doc["id"]
    return out


def anchor_of(target, structures, businesses, streets):
    """THE LANDMARK, AS AN ID — the register's own `action_target`, resolved.

    All 26 `new_building` rows anchor against something the town holds, and until
    T-1401 that something reached the record only inside `limit_reason`'s sentence
    ("…places this house against tremont_house_1…"). A sentence is not a crosswalk:
    the Tremont House's card could not say which four houses stand against it, and
    the Businesses view's `anchored` branch rendered a landmark title no record
    supplied. So the target is resolved HERE, off the register's field, and the
    prose is left to go on saying the same thing in words.

    Three kinds, and the register already distinguishes them:
      * `structure` — a committed roof (`tremont_house_1`, `mansion_house`), 15 rows
      * `business`  — another house in this layer (`business_newberry_dole`), 7 rows
      * `corner`    — a crossing of two platted streets (`dearborn+lake`), 4 rows

    NOTHING HERE PLACES THE HOUSE. `structure_id` stays null on an anchored location
    because the house has no roof of its own; the anchor says what it stood next to,
    which is exactly as far as the register went.
    """
    if not target:
        return None
    if "+" in target:
        parts = target.split("+")
        missing = [s for s in parts if s not in streets]
        if missing:
            raise ValueError("anchor corner %r names street(s) the 1835 corridors do not "
                             "hold: %s" % (target, ", ".join(missing)))
        return {
            "kind": "corner",
            "id": None,
            "title": " and ".join(streets[s] for s in parts),
            "streets": list(parts),
        }
    if target.startswith(REGISTER_PREFIX):
        if target not in businesses:
            raise ValueError("anchor %r names no business in the register" % target)
        return {
            "kind": "business",
            "id": record_id(target),
            "title": businesses[target],
            "streets": [],
        }
    if target not in structures:
        raise ValueError("anchor %r names no committed structure; a landmark this town "
                         "does not hold is not one this layer may print" % target)
    return {
        "kind": "structure",
        "id": target,
        "title": structures[target],
        "streets": [],
    }


def fold_printed_styles(people):
    """ONE ROW A PARTNER, NOT ONE ROW A PRINTING.

    Twelve person-firm pairs in this layer were named twice on the same record,
    because the register prints the same man under two styles and the gazetteer reads
    each style as a proprietor string: "J. D. Caton" and "J. Dean Caton" are one
    partner of Collins & Caton, not two, and Giles Spring was three. Left folded only
    in the renderer (T-1325), the firm's OWN card still printed both, which is the
    register's typography read as the town's partnership.

    So the fold happens in the DATA, on `person_id` — the identity claim the register
    itself made — and never on the name. A printing the resident layer holds no card
    for cannot be folded onto anything and is left exactly as printed; two men who
    really are two are two ids and stay two rows.

    THE TYPOGRAPHY IS EVIDENCE AND IS NOT DELETED. The styles the paper used are kept
    on `also_printed_as[]` in the order they were read, and the claims of every
    folded printing are carried onto the surviving row, so nothing a source said is
    lost by the fold — only counted once.
    """
    out, by_person = [], {}
    for person in people:
        pid = person.get("person_id")
        if not pid:
            out.append(person)
            continue
        kept = by_person.get((pid, person.get("role")))
        if kept is None:
            by_person[(pid, person.get("role"))] = person
            out.append(person)
            continue
        if person.get("name") and person["name"] not in kept["also_printed_as"]:
            kept["also_printed_as"].append(person["name"])
        for claim in person.get("claim_ids") or []:
            if claim not in kept["claim_ids"]:
                kept["claim_ids"].append(claim)
    return out


def locations_for(entry, gaz, anchors=None):
    """The register's action, restated as places and as the limits on places."""
    action = entry["action"]
    target = entry.get("action_target")
    note = entry.get("action_note") or ""
    out = []

    if action == "enrich_existing":
        # Matched onto a roof the town already holds. `occupants` matched the structure's
        # own occupants line and is the stronger read of the two; `name` matched the
        # structure's NAME, which a second house of the same style could also answer to.
        occupants = entry.get("match_tier") == "occupants"
        out.append({
            "kind": "premises",
            "structure_id": target,
            "street_id": entry.get("street_id"),
            "face": None,
            "primary": True,
            "from": (entry.get("evidence") or {}).get("first_issue"),
            "to": None,
            "tier": "attested" if occupants else "inferred",
            "basis": ("The register matches this business onto the committed structure %s on its "
                      "%s. %s" % (target, entry.get("match_tier"), note)).strip(),
            "limit_reason": None,
        })
    elif action == "new_building":
        # Placeable, and not placed: the paper anchors the house against a landmark the
        # town holds, but the town holds no roof of this house's own. That is a location
        # with a limit on it, not a premises.
        out.append({
            "kind": "anchored",
            "structure_id": None,
            "street_id": entry.get("street_id"),
            "face": None,
            "primary": True,
            "from": (entry.get("evidence") or {}).get("first_issue"),
            "to": None,
            "tier": "inferred",
            "basis": note or "Placeable against the committed town.",
            "limit_reason": ("The register places this house against %s and the town holds no roof "
                             "of its own for it (action: new_building), so the anchor is as far as "
                             "the reading goes." % (target or "a landmark it names")),
            "anchor": anchor_of(target, *anchors) if anchors else None,
        })
    elif action == "street_only":
        out.append({
            "kind": "street_only",
            "structure_id": None,
            "street_id": entry.get("street_id"),
            "face": None,
            "primary": True,
            "from": (entry.get("evidence") or {}).get("first_issue"),
            "to": None,
            "tier": "inferred",
            "basis": "The paper names a street and no house on it.",
            "limit_reason": note or "The anchor names nothing the committed town holds.",
        })
    else:
        out.append({
            "kind": "unplaceable",
            "structure_id": None,
            "street_id": None,
            "face": None,
            "primary": True,
            "from": (entry.get("evidence") or {}).get("first_issue"),
            "to": None,
            "tier": "inferred",
            "basis": "The register resolved no place for this house at the scene date.",
            "limit_reason": note or "The paper gives no anchor.",
        })

    # A HOUSE THAT MOVED (T-1402, of T-1182, audited with the sources in front of it).
    # Four of the register's businesses print one anchor and later another. The siting the
    # register did NOT make live is a real dated location and is kept as one, unplaced: it
    # is prose the register never resolved to an id, so the record says where the paper put
    # it and says that it could not be resolved.
    #
    # WHAT THE REGISTER'S TWO DATES ARE, because reading them the other way was the defect
    # this ticket found. A `changes` row brackets the MOVE: `after` is the last issue that
    # sets the old anchor and `before` is the first that sets the new one, so the address
    # changed somewhere in between and the corpus can say no more than that. The pair is
    # NOT the span of either siting — and it was being written onto the secondary row as
    # `from: after, to: before`, which dated the superseded address to exactly the window
    # in which it was being superseded, and carried it up to and including the first
    # printing of its replacement. Giles Spring's office read "Franklin and South Water,
    # 1834-11-26 to 1835-05-20" when 1834-11-26 is the LAST printing of that address and
    # 1835-05-20 the first of the Tremont House one.
    #
    # So each siting is dated by its own printings: the earlier one runs from the record's
    # first issue to `after`, the later one from `before` and is not closed.
    #
    # AND WHICH SIDE IS WHICH IS THE REGISTER'S RULING, NOT AN ASSUMPTION. `live_anchor`
    # names the anchor the register made the scene-date siting, by its own rule (the last
    # anchor first printed on or before the scene date). Usually that is the change's `to`
    # and the secondary row is the earlier siting. For business_the_chicago_democrat it is
    # the change's `from`: the move to Jones & King's is first printed 1835-08-05, after
    # the scene date, so the corner stays live and the LATER siting is the secondary row.
    # Reading every change as "earlier" put the corner on that record twice — once live,
    # once as its own predecessor — and left the move to Jones & King's nowhere on it.
    first_issue = (entry.get("evidence") or {}).get("first_issue")
    change_block = entry.get("anchor_change") or {}
    live_anchor = change_block.get("live_anchor")
    for change in (change_block.get("changes") or []):
        if live_anchor == change.get("to"):
            side, other = "earlier", change.get("from")
            loc_from, loc_to = first_issue, change.get("after")
            limit = ("A prose anchor the register did not resolve to a committed id; kept because "
                     "the house moved and the move is dated. Printed through %s; the anchor that "
                     "supersedes it is first printed %s, so the move falls between those two "
                     "issues and the corpus dates it no closer."
                     % (change.get("after"), change.get("before")))
        elif live_anchor == change.get("from"):
            side, other = "later", change.get("to")
            loc_from, loc_to = change.get("before"), None
            limit = ("A prose anchor the register did not resolve to a committed id; kept because "
                     "the house moved and the move is dated. First printed %s, which is after the "
                     "scene date, so the register keeps the earlier anchor live and this siting is "
                     "recorded without being made the premises." % (change.get("before"),))
        else:
            # The register's live anchor is neither side of its own change. That is a
            # register this compiler cannot read, and a refusal is the only honest answer:
            # guessing a direction would be publishing an adjudication nobody made.
            raise SystemExit(
                "%s: live_anchor %r is neither side of the change %r -> %r"
                % (entry["id"], live_anchor, change.get("from"), change.get("to")))
        out.append({
            "kind": "unplaceable",
            "structure_id": None,
            "street_id": None,
            "face": None,
            "primary": False,
            "from": loc_from,
            "to": loc_to,
            "tier": "inferred",
            "basis": ("The %s of this house's two printed anchors, set as “%s”; the register "
                      "makes “%s” the siting at the scene date."
                      % (side, other, live_anchor)),
            "limit_reason": limit,
        })
        # AND THE LIVE ROW MAY NOT CLAIM A DATE ITS ANCHOR WAS NOT PRINTED ON. Where the
        # move happened before the scene date, the live anchor's own first printing is
        # `before`, not the record's first issue — that earlier issue set the address this
        # house had LEFT. Giles Spring's card read "the Tremont House from 1833-12-17"
        # when the Tremont House address is first printed 1835-05-20.
        #
        # ONLY ON AN `anchored` ROW, because only an anchored row IS the anchor. A
        # `premises` row is the register's match onto a committed structure's own
        # occupants line and a `street_only` row is a street — neither is dated by which
        # landmark the advertisement named, and both of the ones here are unmoved by the
        # change: Matthias Mason's shop is matched on `mason_blacksmith_shop`'s occupants,
        # and the Democrat's printing office is in South Water street on both sides of its
        # move. Re-dating those would be asserting a vacancy no source states.
        if side == "earlier" and out[0]["kind"] == "anchored" and out[0].get("from") == first_issue:
            out[0]["from"] = change.get("before")
            out[0]["basis"] = (out[0]["basis"].rstrip() + " This house moved: the anchor above is "
                               "first printed %s, and “%s” is what the paper set before it."
                               % (change.get("before"), other)).strip()
    return out


def dates_for(entry):
    announced = [o for o in entry.get("opening_announced") or [] if o.get("iso")]
    evidence = entry.get("evidence") or {}
    first = evidence.get("first_issue")
    dissolved = entry.get("dissolved_after_scene_date") or []

    if announced:
        opened = min(o["iso"] for o in announced)
        precision = "exact"
        basis = ("The paper announces the opening: %s." % "; ".join(
            "%s (%s)" % (o["claim"], o["iso"]) for o in announced))
    elif first:
        opened = first
        precision = "not_later_than"
        basis = ("No opening is announced. The first printing, %s, is the bound: the house was "
                 "trading by then and the record does not say when it began." % first)
    else:
        opened = None
        precision = "unbounded"
        basis = "Neither an opening nor a printing date; the record bounds nothing."

    closed = None
    if dissolved:
        closed = evidence.get("last_issue")
        basis += (" A dissolution is printed after the scene date (%s), so the house is closed at "
                  "the last issue that carries it." % ", ".join(dissolved))

    return {
        "opened": opened,
        "closed": closed,
        "precision": precision,
        "tier": "attested" if announced else "inferred",
        "basis": basis,
    }


def compile_record(entry, gaz, register_persons, town_ids, communities, anchors=None):
    """One register business, restated as a record."""
    by_name = register_persons
    evidence = entry.get("evidence") or {}
    claims = list(gaz.get("mentions") or [])
    people = list(entry.get("partners") or [])
    sole = len(people) == 1 and not (gaz.get("firm_styles") or [])

    proprietors, partners = [], []
    for name in people:
        role = "proprietor" if sole else "partner"
        person = person_entry(name, role, by_name.get(name), town_ids, evidence, claims)
        (proprietors if sole else partners).append(person)
    proprietors, partners = fold_printed_styles(proprietors), fold_printed_styles(partners)

    classes = list(gaz.get("trade_classes") or []) or ["not_stated"]

    return {
        "id": record_id(entry["id"]),
        "register_id": entry["id"],
        "name": entry["name"],
        "provenance": "compiled_from_register",
        "type": classes,
        "trade": entry.get("trade"),
        "occupation": entry.get("occupation"),
        "goods": list(gaz.get("goods") or []),
        "firm_styles": list(entry.get("firm_styles") or []),
        "proprietors": proprietors,
        "partners": partners,
        # THE PAPERS NAME OWNERS AND ALMOST NEVER A CLERK. Empty here is a true reading
        # of the register and not an omission: T-1183 rules the staffing model and
        # T-1189 fills this from it.
        "staff": [],
        # AND NOWHERE TO WRITE THE HANDS THE MODEL DOES KNOW ABOUT, until T-1422. The
        # register compiles the schools and the printing offices, so a reading about who
        # taught at the Chicago Academy or who set type for the Democrat could not be
        # written down at all: a hand edit here is refused by --check, and
        # data/businesses/authored/ holds whole records rather than additions to compiled
        # ones. `staffing` is that place. It is null here and filled from
        # data/businesses/rulings/establishment_staffing.json by apply_staffing_overlay,
        # so it is DERIVED like everything else on this record.
        "staffing": None,
        "locations": locations_for(entry, gaz, anchors),
        "dates": dates_for(entry),
        "evidence": {
            "first_issue": evidence.get("first_issue"),
            "last_issue": evidence.get("last_issue"),
            "copy_dates": list((gaz.get("evidence") or {}).get("copy_dates") or []),
        },
        "present_at_scene_date": bool(entry.get("present_at_scene_date")),
        "exclusion": entry.get("exclusion"),
        "exclusion_note": entry.get("exclusion_note"),
        # NEVER INFERRED FROM A SURNAME. The community of a proprietor is a claim about a
        # person, and the register carries no such claim; reading one off a name is the
        # exact move the resident layer refuses. T-1378 fills it from the one place that
        # claim IS made — data/residents/community.json — and from nowhere else.
        "proprietor_community": derive_proprietor_community(proprietors, partners, communities),
        "customers": [],
        "sources": ["chicago_newspapers_1833_1835"],
        "claim_ids": claims,
        "liberties": {
            "survival_required": bool(entry.get("survival_liberty_required")),
            "backdating_required": bool(entry.get("backdating_liberty_required")),
        },
        "review_required": False,
        "replaceable_by": ("A directory, a deed or a later reading that names this house's premises, "
                           "its staff or its dates more exactly than the newspapers do."),
    }


def compile_all(register, gazetteer, town_ids, communities):
    gaz_by_id = {b["id"]: b for b in gazetteer["businesses"]}
    by_name = {}
    for person in register["persons"]:
        by_name.setdefault(person["name"], person)
    # The three id spaces a landmark can live in, read once for all 196 rows.
    anchors = (structure_titles(),
               {e["id"]: e["name"] for e in register["businesses"]},
               street_names())
    records = []
    for entry in register["businesses"]:
        gaz = gaz_by_id.get(entry["id"])
        if gaz is None:
            raise ValueError("register business %s has no gazetteer row" % entry["id"])
        records.append(compile_record(entry, gaz, by_name, town_ids, communities, anchors))
    records.sort(key=lambda r: r["id"])
    return records


# ---------------------------------------------------------------- the index

def crosswalk(records, rows):
    """`works_at` → a business, where a business sits in the roof the household names.

    The resident layer's `works_at` is a bare structure id and cannot say WHICH house of
    trade a person worked for; where two businesses share a roof the crosswalk says two,
    because that is what the evidence supports and picking one would be a ruling.
    """
    by_structure = {}
    for record in records:
        for loc in record["locations"]:
            if loc["kind"] == "premises" and loc.get("structure_id"):
                by_structure.setdefault(loc["structure_id"], []).append(record["id"])
    out = []
    for row in rows:
        out.append({
            "household_id": row["household_id"],
            "head": row["head"],
            "structure_id": row["structure_id"],
            "business_ids": sorted(by_structure.get(row["structure_id"], [])),
        })
    return out


# ---------------------------------------------------------- the directory's rows

def street_names():
    """`street_id` -> the name the town used in 1835, for the row a directory prints.

    The corridors are the only place that mapping lives, and a business's
    `street_id` is one of their ids; an id the corridors do not hold comes
    through as its own id rather than as a guess.
    """
    return {s["id"]: s.get("name_1835") or s["id"] for s in load_json(STREETS)["streets"]}


def record_grade(record):
    """The grade of the firm ITSELF, which is not the grade of any one of its rows.

    A business record states tiers in three places — who ran it, where it stood and
    when it opened — and a directory has to answer one question with them: how well
    is this house evidenced? So: `attested` where ANY of those claims is attested (a
    named proprietor, a premises, an announced opening), `reconstructed` where every
    one of them is reconstructed, `inferred` otherwise. The definition is stated here
    and printed in the app, because a grade a reader cannot unpick is a claim.
    """
    tiers = [record["dates"].get("tier")]
    tiers += [loc.get("tier") for loc in record["locations"]]
    tiers += [p.get("tier") for p in record["proprietors"] + record["partners"] + record["staff"]]
    tiers = [t for t in tiers if t]
    if not tiers:
        return "inferred"
    if "attested" in tiers:
        return "attested"
    if all(t == "reconstructed" for t in tiers):
        return "reconstructed"
    return "inferred"


def primary_location(record, streets):
    """The location a row is filed under: the one marked `primary`, else the first.

    A firm with two premises is filed under its principal one and the card prints
    the dated list in full — the list is the record, this is only the row.
    """
    locs = record["locations"]
    if not locs:
        return None
    loc = next((x for x in locs if x.get("primary")), locs[0])
    street_id = loc.get("street_id")
    return {
        "kind": loc.get("kind"),
        "structure_id": loc.get("structure_id"),
        # The landmark an `anchored` row stands against — a structure, another firm
        # or a street crossing. Null on every other kind, and never a premises: a
        # house anchored against the Tremont House has no roof of its own.
        "anchor": loc.get("anchor"),
        "street_id": street_id,
        "street": streets.get(street_id) if street_id else None,
        "tier": loc.get("tier"),
        "from": loc.get("from"),
        "to": loc.get("to"),
        "limit_reason": loc.get("limit_reason"),
    }


def index_people(record):
    """Everyone the record names, flattened to `{name, person_id, role, tier, from, to}`.

    The directory searches proprietors by name and the card links the ones the town
    holds a card for; both want one list, and the three fields it comes from say the
    same things in the same words.
    """
    out = []
    for field in ("proprietors", "partners", "staff"):
        for person in record[field]:
            out.append({
                "name": person.get("name"),
                "person_id": person.get("person_id"),
                "role": person.get("role") or field[:-1],
                "tier": person.get("tier"),
                "from": person.get("from"),
                "to": person.get("to"),
                # The styles folded onto this row, carried so the directory's search
                # still answers the query a reader typed off the paper: "James H.
                # Collins" is not on any record's `name` any more and must still
                # find Collins & Caton.
                "also_printed_as": list(person.get("also_printed_as") or []),
            })
    return out


def index_row(record, streets):
    """One business as a directory row: everything the list, its filters and its
    counts read, and nothing the card alone needs — the card fetches the record."""
    return {
        "id": record["id"],
        "file": "%s.json" % record["id"],
        "name": record["name"],
        "register_id": record.get("register_id"),
        "provenance": record["provenance"],
        "type": record["type"],
        "present_at_scene_date": record["present_at_scene_date"],
        "grade": record_grade(record),
        "trade": record.get("trade"),
        "occupation": record.get("occupation"),
        "goods": record.get("goods") or [],
        "firm_styles": record.get("firm_styles") or [],
        "people": index_people(record),
        "where": primary_location(record, streets),
        "locations": len(record["locations"]),
        "opened": record["dates"].get("opened"),
        "closed": record["dates"].get("closed"),
        "dates_tier": record["dates"].get("tier"),
        # THE VALUE AND ITS TIER, not the whole block: the list filters and counts on
        # the value, the pill greys on the tier, and the card fetches the record for the
        # rule, the basis and the keepers it was read off.
        "proprietor_community": (record.get("proprietor_community") or {}).get("value"),
        "proprietor_community_tier": (record.get("proprietor_community") or {}).get("tier"),
        "review_required": bool(record.get("review_required")),
        "liberties": sorted(k for k, v in (record.get("liberties") or {}).items() if v),
    }


def build_index(records, authored, rows):
    everything = records + authored
    counts_by_type = {}
    for record in everything:
        for kind in record["type"]:
            counts_by_type[kind] = counts_by_type.get(kind, 0) + 1
    counts_by_kind = {}
    for record in everything:
        for loc in record["locations"]:
            counts_by_kind[loc["kind"]] = counts_by_kind.get(loc["kind"], 0) + 1
    linked = sum(1 for r in everything for p in r["proprietors"] + r["partners"] + r["staff"]
                 if p["person_id"])
    named = sum(1 for r in everything for p in r["proprietors"] + r["partners"] + r["staff"])
    counts_by_grade = {}
    counts_by_street = {}
    # By the PRIMARY location, which is not the same tally as `by_location_kind`
    # above: that one counts LOCATIONS, and four of these houses moved inside the
    # window, so a firm filed under the street it ended on still carries an
    # unplaceable earlier address. The directory files a firm once, so it needs
    # the count of FIRMS — 83 unplaceable locations are 79 unplaceable houses.
    counts_by_where = {}
    counts_by_community = {}
    streets = street_names()
    directory = [index_row(r, streets) for r in sorted(everything, key=lambda r: r["id"])]
    for row in directory:
        counts_by_grade[row["grade"]] = counts_by_grade.get(row["grade"], 0) + 1
        street = (row["where"] or {}).get("street")
        if street:
            counts_by_street[street] = counts_by_street.get(street, 0) + 1
        kind = (row["where"] or {}).get("kind")
        if kind:
            counts_by_where[kind] = counts_by_where.get(kind, 0) + 1
        community = row.get("proprietor_community") or "unknown"
        counts_by_community[community] = counts_by_community.get(community, 0) + 1
    walk = crosswalk(everything, rows)
    return {
        "schema": 1,
        "_doc": ("DERIVED, NEVER AUTHORED. Rebuilt from register_1835.json, gazetteer.json and "
                 "data/residents/ by tools/compile_businesses.py; tools/check.sh refuses a "
                 "committed copy a rebuild would not produce. Edit the gazetteer, the dataset or "
                 "data/businesses/authored/, not this file."),
        "generated_by": "tools/compile_businesses.py",
        "counts": {
            "records": len(everything),
            "compiled_from_register": len(records),
            "authored": len(authored),
            "present_at_scene_date": sum(1 for r in everything if r["present_at_scene_date"]),
            "by_type": dict(sorted(counts_by_type.items())),
            "by_location_kind": dict(sorted(counts_by_kind.items())),
            "named_people": named,
            "named_people_linked_to_a_town_card": linked,
            "works_at_households": len(walk),
            "works_at_households_resolving_to_a_business": sum(1 for w in walk if w["business_ids"]),
            "by_grade": dict(sorted(counts_by_grade.items())),
            "by_where_kind": dict(sorted(counts_by_where.items())),
            "by_street": dict(sorted(counts_by_street.items())),
            "by_proprietor_community": dict(sorted(counts_by_community.items())),
        },
        "_vocabulary_doc": ("THE CLOSED VOCABULARY, and it is the resident layer's — "
                            "data/residents/community_rules.json, one list for people and for "
                            "the houses they kept. The rows with a zero count are the point and "
                            "are shipped anyway: a term nobody carries is a measurement of this "
                            "layer, not a gap in this file. The Businesses view offers a pill "
                            "only where the count is above zero."),
        "vocabulary": {
            "communities": [
                {"value": value, "label": label,
                 "count": counts_by_community.get(value, 0)}
                for value, label in community_vocabulary()
            ],
        },
        "_businesses_doc": ("THE DIRECTORY'S ROWS. Each carries what the Businesses list, its "
                            "filters and its counts read — the card fetches the record itself "
                            "and prints the rest. `grade` is the firm's own, not any one row's: "
                            "attested where any of who-ran-it, where-it-stood or when-it-opened "
                            "is attested, reconstructed where every one of them is, inferred "
                            "otherwise. `place` is the PRIMARY location; `locations` says how "
                            "many the record holds. The layer states no division for a business "
                            "— street is as near as the record goes."),
        "businesses": directory,
        "_works_at_doc": ("THE CROSSWALK, NOT A RULING. A household's `works_at` names a STRUCTURE; "
                          "this says which business records stand in that structure. Two entries "
                          "mean two houses share the roof and the evidence does not choose between "
                          "them; an empty list means the roof carries no business the register "
                          "knows, which is a finding about the register."),
        "works_at": walk,
    }


# ---------------------------------------------------------------- build / check

def read_staffing_overlay():
    """The hands each kind of house employed, laid over the records the register compiles.

    WHY AN OVERLAY AND NOT A FIELD OF THE REGISTER. The register reads NOTICES, and a
    notice names a keeper. The staffing model (T-1183) reads the 1839 directory and the
    census and says what KIND of hand a kind of house employed; it writes no person and
    names none. Neither of those two things can say what the other says, and until T-1422
    there was no third place to put the join — which is why T-1411 split with the
    churches done and the schools and the press undone. This is the third place.

    IT MAY ADD AND IT MAY NOT OVERWRITE. An entry contributes `staff` rows, which a
    compiled record always has none of, and a `staffing` block, which is null until an
    entry supplies one. It touches no other field, so the compiled record stays the
    register's own reading and the overlay stays legible as a separate claim.
    """
    if not STAFFING_OVERLAY.exists():
        return {}
    doc = load_json(STAFFING_OVERLAY)
    by_id = {}
    for entry in doc["entries"]:
        by_id.setdefault(entry["business_id"], []).append(entry)
    return by_id


def apply_staffing_overlay(records, overlay):
    """Carry each entry onto its record, and refuse an entry that names no record."""
    by_id = {record["id"]: record for record in records}
    for business_id, entries in sorted(overlay.items()):
        record = by_id.get(business_id)
        if record is None:
            # A RULING THAT HAS OUTLIVED ITS RECORD IS A JUDGEMENT NOBODY CAN CHECK. The
            # same rule trade_census_1835.py holds its own overrides to.
            raise ValueError(
                "the staffing overlay names %s, which the register does not compile. An "
                "overlay entry belongs to a compiled record; a house a human authors "
                "carries its own staffing in data/businesses/authored/." % business_id)
        if len(entries) > 1:
            raise ValueError("the staffing overlay carries %d entries for %s; one house, "
                             "one entry" % (len(entries), business_id))
        entry = entries[0]
        record["staff"] = list(entry.get("staff") or [])
        record["staffing"] = entry.get("staffing")
    return records


def read_reconstructed_overlay():
    """The reconstructed hands, laid over the houses the T-1433 seating seated them in.

    THE SECOND OVERLAY, AND WHY IT IS A SEPARATE ONE. The first is a RULING — authored
    by a human at T-1422, cited on every row, and a tool that rewrote it would be
    overwriting a judgement. This one is DERIVED: tools/staff_the_houses_1835.py --build
    restates the seating join and nothing else, and --check refuses a byte of it that has
    drifted. Keeping them apart is what lets a reader tell, on any one record, which of
    its hands somebody decided and which a pass computed.

    It carries nothing the seating does not already hold. 124 seats, in 84 houses, each
    at its own `reconstructed` tier with its own seed, its own basis and the source that
    would retire it — and beside them the `shortfall` block, which is the whole point of
    the exercise: a house standing at half the hands its class wants now says so on its
    own record instead of reading exactly like a house standing at all of them.
    """
    if not RECONSTRUCTED_STAFF_OVERLAY.exists():
        return {}
    doc = load_json(RECONSTRUCTED_STAFF_OVERLAY)
    by_id = {}
    for entry in doc["entries"]:
        by_id.setdefault(entry["business_id"], []).append(entry)
    return by_id


def apply_reconstructed_overlay(records, overlay):
    """Carry each entry on, over the ruling where there is one, and assert it added."""
    by_id = {record["id"]: record for record in records}
    for business_id, entries in sorted(overlay.items()):
        record = by_id.get(business_id)
        if record is None:
            raise ValueError(
                "the reconstructed staff overlay names %s, which the register does not "
                "compile. Re-run tools/staff_the_houses_1835.py --build after a change to "
                "the seating join." % business_id)
        if len(entries) > 1:
            raise ValueError("the reconstructed staff overlay carries %d entries for %s; "
                             "one house, one entry" % (len(entries), business_id))
        entry = entries[0]
        # A DERIVED PASS MAY ADD TO A JUDGEMENT AND MAY NOT OVERWRITE ONE. Where T-1422's
        # ruling has already put rows on this record, the derived entry must open with
        # exactly those rows — the tool carries them forward and this is where that claim
        # is checked rather than trusted. Five of the 84 houses are in both overlays.
        standing = list(record.get("staff") or [])
        offered = list(entry.get("staff") or [])
        if offered[:len(standing)] != standing:
            raise ValueError(
                "the reconstructed staff overlay would drop %d ruled staff row(s) from %s. "
                "A derived overlay adds to a ruling; it does not replace one."
                % (len(standing), business_id))
        record["staff"] = offered
        record["staffing"] = entry.get("staffing")
    return records


def staffing_problems(records):
    """The rules the `staffing` block stands on. Every one is a --self-test case.

    THE PROMISE THIS ENFORCES IS THE MODEL'S OWN: it writes no person. A block that
    carried a name or a person id would be a roster wearing a model's clothes, and the
    difference between the two is the whole reason `staff` and `staffing` are separate
    fields. The rest is bookkeeping that keeps a `drawn` flag honest in both directions.
    """
    bad = []
    for record in records:
        rid = record.get("id", "<no id>")
        block = record.get("staffing")
        if block is None:
            continue
        if block.get("writes_no_person") is not True:
            bad.append("%s: a staffing block that does not hold itself to writing no "
                       "person" % rid)
        for hand in block.get("hands") or []:
            if not (hand["count_low"] <= hand["count_typical"] <= hand["count_high"]):
                bad.append("%s: the %s hand runs %s-%s-%s, which is not a range"
                           % (rid, hand["role"], hand["count_low"], hand["count_typical"],
                              hand["count_high"]))
            if "person_id" in hand or "name" in hand:
                bad.append("%s: the %s hand names a person; the model writes none, and a "
                           "hand a source names belongs in staff[]" % (rid, hand["role"]))
            if not hand["drawn"] and not (hand.get("why_not_drawn") or "").strip():
                bad.append("%s: the %s hand is undrawn and says nothing about why; an "
                           "undrawn hand is a statement, not a gap" % (rid, hand["role"]))
            # A DRAWN HAND POINTS AT A ROW OR IT IS DRAWN ON NOTHING. `drawn: true` is a
            # claim that this record carries the person, and the only place it can carry
            # one is staff[] — so the claim is checked against it rather than trusted.
            if hand["drawn"] and not any(
                    person["role"] == hand["household_relationship"]
                    or person["role"] == hand["role"]
                    for person in record["staff"]):
                bad.append("%s: the %s hand is drawn and no staff row stands for it"
                           % (rid, hand["role"]))
        attendance = block.get("attendance")
        if attendance is not None:
            if attendance["kind"] == "none_printed" and attendance["value"] is not None:
                bad.append("%s: attendance says none was printed and prints one" % rid)
            if attendance["kind"] != "none_printed" and attendance["value"] is None:
                bad.append("%s: attendance claims a %s count and carries no figure"
                           % (rid, attendance["kind"]))
    return bad


def read_authored():
    if not AUTHORED.is_dir():
        return []
    return [load_json(p) for p in sorted(AUTHORED.glob("*.json"))]


def compiled_docs(residents_dir=None):
    register = load_json(REGISTER)
    gazetteer = load_json(GAZETTEER)
    town_ids = person_ids(residents_dir)
    records = compile_all(register, gazetteer, town_ids, person_communities(residents_dir))
    records = apply_staffing_overlay(records, read_staffing_overlay())
    records = apply_reconstructed_overlay(records, read_reconstructed_overlay())
    authored = read_authored()
    return records, authored, build_index(records, authored, works_at_rows(residents_dir))


def build():
    records, authored, index = compiled_docs()
    BUSINESSES.mkdir(parents=True, exist_ok=True)
    AUTHORED.mkdir(parents=True, exist_ok=True)
    wanted = {"%s.json" % r["id"] for r in records} | {"index.json"}
    for path in BUSINESSES.glob("*.json"):
        if path.name not in wanted:
            path.unlink()
    for record in records:
        (BUSINESSES / ("%s.json" % record["id"])).write_text(dumps(record), encoding="utf-8")
    INDEX.write_text(dumps(index), encoding="utf-8")
    problems = semantic_problems(records + authored)
    for problem in problems:
        print("  FAIL  " + problem, file=sys.stderr)
    print("compiled %d business record(s) (%d from the register, %d authored) → %s"
          % (len(records) + len(authored), len(records), len(authored),
             BUSINESSES.relative_to(ROOT)))
    print("  %d named proprietor(s)/partner(s); %d linked to a town card"
          % (index["counts"]["named_people"], index["counts"]["named_people_linked_to_a_town_card"]))
    print("  locations by kind: %s" % index["counts"]["by_location_kind"])
    return 1 if problems else 0


def semantic_problems(records, town_ids=None):
    """The rules a JSON schema cannot state. Every one of these is a --self-test case."""
    town_ids = town_ids if town_ids is not None else person_ids()
    vocab = {value for value, _ in community_vocabulary()}
    bad = staffing_problems(records)
    seen = set()
    for record in records:
        rid = record.get("id", "<no id>")
        if rid in seen:
            bad.append("%s: two records carry this id" % rid)
        seen.add(rid)

        for person in record["proprietors"] + record["partners"] + record["staff"]:
            if person["tier"] == "attested" and not (person.get("source_id") or person.get("claim_ids")):
                bad.append("%s: %r is attested and cites nothing" % (rid, person["name"]))
            if not (person.get("basis") or "").strip():
                bad.append("%s: %r carries no basis" % (rid, person["name"]))
            if person["person_id"] is not None and person["person_id"] not in town_ids:
                bad.append("%s: %r links to %s, which the resident layer does not hold"
                           % (rid, person["name"], person["person_id"]))

        primary = [loc for loc in record["locations"] if loc["primary"]]
        if len(primary) != 1:
            bad.append("%s: %d primary location(s); a record has exactly one"
                       % (rid, len(primary)))
        for loc in record["locations"]:
            if loc["kind"] in ("street_only", "unplaceable") and not (loc.get("limit_reason") or "").strip():
                bad.append("%s: a %s location states no limit_reason" % (rid, loc["kind"]))
            if loc["kind"] == "premises" and not loc.get("structure_id"):
                bad.append("%s: a premises location names no structure" % rid)
            # AN ANCHOR IS AN ID OR IT IS NOTHING (T-1401). An `anchored` location
            # whose landmark lives only in `limit_reason`'s sentence is unreachable
            # from the roof it stands against, which is the whole finding this rule
            # closes. And the anchor must not be mistaken for a roof of the house's
            # own: the register gave it none, and `structure_id` says so.
            if loc["kind"] == "anchored":
                anchor = loc.get("anchor")
                if not isinstance(anchor, dict):
                    bad.append("%s: an anchored location names no anchor" % rid)
                elif anchor["kind"] == "corner":
                    if len(anchor.get("streets") or []) != 2:
                        bad.append("%s: an anchor corner names %d street(s), not two"
                                   % (rid, len(anchor.get("streets") or [])))
                elif not anchor.get("id"):
                    bad.append("%s: an anchor of kind %r resolves to no id"
                               % (rid, anchor["kind"]))
                if loc.get("structure_id"):
                    bad.append("%s: an anchored location carries a structure_id; the "
                               "landmark is not the house's own roof" % rid)
            if loc["tier"] not in GRADES:
                bad.append("%s: location tier %r is off the ladder" % (rid, loc["tier"]))

        # A RECONSTRUCTED HOUSE SAYS WHERE IT CAME FROM, OR IT IS NOT ONE (T-1184). The
        # `reconstruction` block is the business layer's half of the contract T-1158 put on
        # every reconstructed value: what bought the house, the group and ticket that wrote
        # it, the seed a reader retypes to redraw it, and what retires it. The block belongs
        # to reconstructions and to nothing else — a compiled or an audited record carrying
        # one would be claiming a writer it does not have.
        #
        # AND THERE ARE TWO WAYS A HOUSE CAN BE BOUGHT (owner, 2026-09-19; widened from
        # T-1184's single form for T-1377). The first is a QUOTA ROW: the order book counts
        # a shortfall against the register and leaves N of a class to reconstruct, and the
        # record names the `bucket` and the `slot` it took. That is the whole of the
        # business reconstruction programme and it assumes a modelled shortfall exists.
        #
        # The second is a DOCUMENTED FLOOR, and T-1377 is the case that showed the first
        # form does not cover everything. Its two Black-owned firms do not fill a shortfall:
        # they stand for a count the corpus makes DIRECTLY — Andreas's six or seven
        # certificates of freedom obtained at Chicago in August 1833, read against the 1840
        # schedule's free-coloured share — and the order book holds no barber or
        # washing-and-ironing bucket at all, because the programme that would mint one
        # (T-1186) has not run. Under the single form the only ways to pass were to spend
        # another programme's quota before it runs, or to file documented evidence as an
        # estimate. Both are worse than widening the rule.
        #
        # The third is a STANDING ROOF, and T-1408 is the case that showed the second form
        # does not cover everything either. A boarding house fills no shortfall and stands
        # on no documented count: the December 1835 State census enumerates TAVERNS and
        # never boarding houses, and `business_buckets` in tools/build_order_book_1835.py
        # orders against printed counts or not at all — so the book can no more hold a
        # boarding-house bucket than it can hold a barber's. What this project does hold is
        # the BUILDING: the roof stands in data/structures/, the lodging model apportioned
        # it beds, and the lodgers stage put people in them and named a keeper. A house with
        # beds, lodgers and a keeper and no firm behind it is an establishment the business
        # layer cannot see, and the roof is what buys the firm that makes it visible.
        #
        # The fourth is a TRADE HEAD, and T-1424 is the case that showed the THIRD does not
        # cover everything either. A livery stable is as uncounted as a boarding house — the
        # census's eighteen lines reach the taverns and the saw-mill and never a livery — but
        # nothing in data/structures/ is a livery stable, so there is no committed building to
        # buy the firm and the roof form has nothing to point at. What is committed is the
        # MAN: the resident band drew two men at `livery_stable_keeper` and two at
        # `lumber_merchant` because the 1839 trade table says the town was short of the
        # trades, and the word of each trade names the house he keeps. A drawn keeper with no
        # house to keep is the mirror image of a standing roof with no firm in it.
        #
        # So the block must state EXACTLY ONE of the four, and say which. A record naming
        # more than one is claiming a house twice over; a record naming none is the original
        # fault this check exists to catch.
        block = record.get("reconstruction")
        if record["provenance"] == "reconstructed" and not block:
            bad.append("%s: reconstructed and carries no reconstruction block, so nothing "
                       "says what bought it — a quota row (bucket + slot), a documented "
                       "floor or a standing roof" % rid)
        elif block:
            quota = bool(block.get("bucket") or block.get("slot"))
            floor = bool(block.get("floor"))
            roof = bool(block.get("roof"))
            head = bool(block.get("trade_head"))
            if sum((quota, floor, roof, head)) > 1:
                bad.append("%s: the reconstruction block names more than one of an "
                           "order-book row, a documented floor, a standing roof and a trade "
                           "head; a house is bought once" % rid)
            elif not (quota or floor or roof or head):
                bad.append("%s: the reconstruction block names neither an order-book row "
                           "(bucket + slot) nor a documented floor nor a standing roof nor a "
                           "trade head" % rid)
            elif quota and not (block.get("bucket") and block.get("slot")):
                bad.append("%s: a quota row names a bucket and a slot, and this one names "
                           "only %s" % (rid, "a bucket" if block.get("bucket") else "a slot"))
            elif roof:
                # A ROOF IS ONLY A ROOF IF THE HOUSE IS ON IT. The whole argument is that
                # this firm is the trade of a building this project already stands, so a
                # record bought by a roof and seated on a street — or on somebody else's
                # roof — has bought nothing and the claim is empty.
                r = block["roof"]
                if not isinstance(r, dict):
                    bad.append("%s: the standing roof is not a block" % rid)
                else:
                    if not (r.get("keeper_person_id") or "").strip():
                        bad.append("%s: the standing roof names no keeper; the keeper is "
                                   "ADOPTED and a roof that names none minted one" % rid)
                    primary = next((l for l in record["locations"] if l.get("primary")), None)
                    seat = (primary or {}).get("structure_id")
                    if (primary or {}).get("kind") != "premises" or seat != r.get("structure_id"):
                        bad.append("%s: bought by the standing roof %r and its primary "
                                   "location is %r; a roof buys the firm of THAT building"
                                   % (rid, r.get("structure_id"), seat))
            elif head:
                # A TRADE HEAD IS ONLY A TRADE HEAD IF HE KEEPS THE HOUSE. The whole argument
                # is that this firm is the establishment a man this project already drew was
                # drawn to keep, so a record bought by his head and kept by somebody else —
                # or by nobody — has bought nothing. And it may not be seated on a roof: the
                # form exists precisely because no building of the class stands, and a record
                # that found one should be claiming that roof instead.
                h = block["trade_head"]
                if not isinstance(h, dict):
                    bad.append("%s: the trade head is not a block" % rid)
                else:
                    keepers = [p.get("person_id") for p in record["proprietors"]]
                    if keepers != [h.get("person_id")]:
                        bad.append("%s: bought by the trade head %r and kept by %r; a head "
                                   "buys the house HE keeps and no other"
                                   % (rid, h.get("person_id"),
                                      ", ".join(str(k) for k in keepers) or "nobody"))
                    primary = next((l for l in record["locations"] if l.get("primary")), None)
                    if (primary or {}).get("kind") != "street_only":
                        bad.append("%s: bought by a trade head and seated %r; the form exists "
                                   "because no building of this class stands, so the house "
                                   "takes a street face and nothing narrower"
                                   % (rid, (primary or {}).get("kind")))
            elif floor:
                # A floor carries its own evidence, because nothing upstream counted it.
                f = block["floor"]
                if not isinstance(f, dict):
                    bad.append("%s: the documented floor is not a block" % rid)
                else:
                    if not isinstance(f.get("count"), int) or f["count"] < 1:
                        bad.append("%s: the documented floor states no count" % rid)
                    if not (f.get("sources") or []):
                        bad.append("%s: the documented floor cites no source; a floor that "
                                   "nothing states is an estimate" % rid)
                    if not (f.get("note") or "").strip():
                        bad.append("%s: the documented floor argues no basis" % rid)
        if record.get("reconstruction") and record["provenance"] != "reconstructed":
            bad.append("%s: carries a reconstruction block and is provenance %r"
                       % (rid, record["provenance"]))
        if record["provenance"] == "reconstructed" and (record["sources"] or record["claim_ids"]):
            bad.append("%s: reconstructed and cites a source; the evidence is for the NEED "
                       "and it is argued in the basis" % rid)

        if record["dates"]["tier"] == "attested" and record["dates"]["precision"] != "exact":
            bad.append("%s: dates are attested at precision %r; an attested opening is exact"
                       % (rid, record["dates"]["precision"]))
        if not record["type"]:
            bad.append("%s: no census class" % rid)

        # THE COMMUNITY IS READ OFF PEOPLE OR IT IS NOT READ. Four rules, and the third
        # is the one this field exists for: the value must be a community every
        # contributing keeper actually carries, so no reading can arrive from anywhere
        # but the cards named in `from` — least of all from a surname.
        block = record.get("proprietor_community")
        if not isinstance(block, dict):
            bad.append("%s: proprietor_community is not a derived block" % rid)
        else:
            value = block.get("value")
            sources = block.get("from") or []
            speaking = {r.get("community") for r in sources if r.get("community") != "unknown"}
            if value not in vocab:
                bad.append("%s: proprietor_community %r is off the vocabulary" % (rid, value))
            if not (block.get("basis") or "").strip():
                bad.append("%s: proprietor_community states no basis" % rid)
            if value != "unknown" and speaking != {value}:
                bad.append("%s: proprietor_community reads %r and the keepers it names read %s"
                           % (rid, value, sorted(speaking) or "nobody"))
            if value != "unknown" and block.get("tier") == "attested":
                bad.append("%s: proprietor_community is attested; a house is not its keeper, so "
                           "the reading is capped at inferred" % rid)
            for row in sources:
                if row.get("person_id") not in town_ids:
                    bad.append("%s: proprietor_community reads off %s, which the resident layer "
                               "does not hold" % (rid, row.get("person_id")))
    return bad


def schema_problems(records):
    try:
        import jsonschema
    except ImportError:
        print("  note: jsonschema is not installed, so the records were NOT validated "
              "against data/businesses.schema.json. A GATE may not count this as a pass.",
              file=sys.stderr)
        return []
    schema = load_json(SCHEMA)
    validator = jsonschema.Draft202012Validator(schema)
    bad = []
    for record in records:
        for error in sorted(validator.iter_errors(record), key=lambda e: list(e.path)):
            bad.append("%s: %s at %s" % (record.get("id"), error.message,
                                         "/".join(str(p) for p in error.path) or "<root>"))
    return bad


def check():
    if not BUSINESSES.is_dir():
        return ["data/businesses/ does not exist; run tools/compile_businesses.py --build"]
    records, authored, index = compiled_docs()
    bad = []

    committed = {p.name for p in BUSINESSES.glob("*.json")}
    wanted = {"%s.json" % r["id"] for r in records} | {"index.json"}
    for extra in sorted(committed - wanted):
        bad.append("data/businesses/%s is committed and a rebuild does not produce it" % extra)
    for missing in sorted(wanted - committed):
        bad.append("data/businesses/%s is missing; run --build" % missing)

    for record in records:
        path = BUSINESSES / ("%s.json" % record["id"])
        if path.name in committed and path.read_text(encoding="utf-8") != dumps(record):
            bad.append("data/businesses/%s differs from a rebuild — it is DERIVED; edit the "
                       "gazetteer or the dataset, not this file" % path.name)
    if INDEX.exists() and INDEX.read_text(encoding="utf-8") != dumps(index):
        bad.append("data/businesses/index.json differs from a rebuild")

    for record in authored:
        if record.get("provenance") == "compiled_from_register":
            bad.append("%s: an authored record may not claim provenance "
                       "compiled_from_register" % record.get("id"))

    bad += schema_problems(records + authored)
    bad += semantic_problems(records + authored)

    # THE REGISTER MUST POINT AT THE LAYER. compile_register.py writes
    # `business_record_id` on every row; a row whose record is absent is the failure this
    # layer exists to make impossible.
    register = load_json(REGISTER)
    have = {r["id"] for r in records} | {r.get("id") for r in authored}
    for entry in register["businesses"]:
        pointed = entry.get("business_record_id")
        if not pointed:
            bad.append("register business %s carries no business_record_id" % entry["id"])
        elif pointed not in have:
            bad.append("register business %s points at %s, which the layer does not hold"
                       % (entry["id"], pointed))
    return bad


# ---------------------------------------------------------------- self-test

def self_test():
    """Break each assertion and require it to fire. A gate nobody has broken is a hope."""
    global BUSINESSES
    failures = []

    # COUNTED, NOT TYPED. The closing line used to print a literal 16 and went on
    # printing it after T-1422 added eight cases, which is a gate reporting on a version
    # of itself that no longer exists.
    fired = []

    def expect(name, records, needle, town_ids=None):
        fired.append(name)
        found = semantic_problems(records, town_ids)
        if not any(needle in problem for problem in found):
            failures.append("%s: expected a refusal mentioning %r, got %r" % (name, needle, found))

    base = {
        "id": "biz_fixture", "register_id": "business_fixture", "name": "A fixture",
        "provenance": "compiled_from_register", "type": ["store"], "trade": "dry goods",
        "occupation": "dry_goods_merchant", "goods": [], "firm_styles": [],
        "proprietors": [{"name": "A. Fixture", "person_id": "fixture_a",
                         "register_person_id": "person_a_fixture", "role": "proprietor",
                         "from": "1835-01-01", "to": "1835-06-01", "tier": "attested",
                         "basis": "the notice prints the name",
                         "source_id": "chicago_newspapers_1833_1835", "claim_ids": ["c001"]}],
        "partners": [], "staff": [],
        "locations": [{"kind": "premises", "structure_id": "fixture_store", "street_id": None,
                       "face": None, "primary": True, "from": "1835-01-01", "to": None,
                       "tier": "attested", "basis": "matched on occupants", "limit_reason": None}],
        "dates": {"opened": "1835-01-01", "closed": None, "precision": "exact",
                  "tier": "attested", "basis": "announced"},
        "evidence": {"first_issue": "1835-01-01", "last_issue": "1835-06-01", "copy_dates": []},
        "present_at_scene_date": True, "exclusion": None, "exclusion_note": None,
        "proprietor_community": {
            "value": "yankee", "tier": "inferred", "rule": "proprietors_agree",
            "basis": "the one keeper the layer cards reads yankee",
            "from": [{"person_id": "fixture_a", "name": "A. Fixture", "role": "proprietor",
                      "community": "yankee", "tier": "inferred"}],
        },
        "customers": [],
        "sources": ["chicago_newspapers_1833_1835"], "claim_ids": ["c001"],
        "liberties": {"survival_required": False, "backdating_required": False},
        "review_required": False, "replaceable_by": "a directory",
    }
    ids = {"fixture_a"}

    clean = semantic_problems([json.loads(json.dumps(base))], ids)
    if clean:
        failures.append("the fixture itself is refused: %r" % clean)

    def mutate(fn):
        doc = json.loads(json.dumps(base))
        fn(doc)
        return [doc]

    def unset_source(doc):
        doc["proprietors"][0]["source_id"] = None
        doc["proprietors"][0]["claim_ids"] = []
    expect("an attested person citing nothing", mutate(unset_source), "cites nothing", ids)

    expect("a person with no basis",
           mutate(lambda d: d["proprietors"][0].update(basis="  ")), "carries no basis", ids)

    expect("a person id the town does not hold",
           mutate(lambda d: d["proprietors"][0].update(person_id="nobody_at_all")),
           "the resident layer does not hold", ids)

    expect("two primary locations",
           mutate(lambda d: d["locations"].append(dict(d["locations"][0]))),
           "primary location(s)", ids)

    def make_street_only(doc):
        doc["locations"][0].update(kind="street_only", structure_id=None, limit_reason=None)
    expect("a limit with no reason", mutate(make_street_only), "states no limit_reason", ids)

    expect("a premises naming no structure",
           mutate(lambda d: d["locations"][0].update(structure_id=None)),
           "names no structure", ids)

    expect("a tier off the ladder",
           mutate(lambda d: d["locations"][0].update(tier="probable")), "off the ladder", ids)

    # T-1401 — an anchored location's landmark must be an id, and must not be read
    # as a roof of the house's own.
    def anchored(doc, **over):
        doc["locations"][0].update(
            kind="anchored", structure_id=None,
            limit_reason="the register places this house against a landmark",
            anchor={"kind": "structure", "id": "fixture_landmark",
                    "title": "A landmark", "streets": []})
        doc["locations"][0]["anchor"].update(over.pop("anchor", None) or {})
        doc["locations"][0].update(over)

    clean_anchor = mutate(lambda d: anchored(d))
    if semantic_problems(clean_anchor, ids):
        failures.append("a resolved anchor is refused: %r" % semantic_problems(clean_anchor, ids))

    def anchor_missing(doc):
        anchored(doc)
        doc["locations"][0]["anchor"] = None
    expect("an anchored location with no anchor", mutate(anchor_missing),
           "names no anchor", ids)

    expect("an anchor that resolves to no id",
           mutate(lambda d: anchored(d, anchor={"id": None})), "resolves to no id", ids)

    expect("an anchor corner naming one street",
           mutate(lambda d: anchored(d, anchor={"kind": "corner", "id": None,
                                                "streets": ["lake"]})),
           "names 1 street(s), not two", ids)

    expect("an anchored location carrying a roof of its own",
           mutate(lambda d: anchored(d, structure_id="fixture_store")),
           "the landmark is not the house's own roof", ids)

    # T-1422 — the staffing overlay. Every one of these is a way the block could stop
    # being a MODEL and start being a roster nobody wrote, which is the one thing the
    # field exists not to be.
    def staffed(doc, **over):
        doc["staffing"] = {
            "class": "printing_office", "reads_as": "a printing office",
            "principal_role": "printer", "principal_is": "A. Fixture",
            "hands": [{"role": "printer", "household_relationship": "journeyman",
                       "count_low": 1, "count_typical": 1, "count_high": 2, "drawn": False,
                       "basis": "directory_1839",
                       "why_not_drawn": "no source names him"}],
            "attendance": None, "writes_no_person": True,
            "basis": "the model's row for this class", "replaceable_by": "an imprint",
        }
        doc["staffing"].update(over)

    clean_block = mutate(lambda d: staffed(d))
    if semantic_problems(clean_block, ids):
        failures.append("a clean staffing block is refused: %r"
                        % semantic_problems(clean_block, ids))

    expect("a staffing block that will not promise to write no person",
           mutate(lambda d: staffed(d, writes_no_person=False)), "writing no person", ids)

    def names_a_person(doc):
        staffed(doc)
        doc["staffing"]["hands"][0]["person_id"] = "fixture_a"
    expect("a hand that names a person", mutate(names_a_person),
           "the model writes none", ids)

    def undrawn_and_silent(doc):
        staffed(doc)
        doc["staffing"]["hands"][0]["why_not_drawn"] = "  "
    expect("an undrawn hand that says nothing about why", mutate(undrawn_and_silent),
           "an undrawn hand is a statement", ids)

    def drawn_on_nothing(doc):
        staffed(doc)
        doc["staffing"]["hands"][0]["drawn"] = True
    expect("a hand drawn with no staff row behind it", mutate(drawn_on_nothing),
           "no staff row stands for it", ids)

    def not_a_range(doc):
        staffed(doc)
        doc["staffing"]["hands"][0].update(count_low=3, count_typical=1, count_high=2)
    expect("a hand count that is not a range", mutate(not_a_range),
           "which is not a range", ids)

    expect("an attendance that says none was printed and prints one",
           mutate(lambda d: staffed(d, attendance={"value": 30, "kind": "none_printed",
                                                   "tier": None, "on_date": None,
                                                   "basis": "b"})),
           "none was printed and prints one", ids)

    expect("an attendance claiming a count it does not carry",
           mutate(lambda d: staffed(d, attendance={"value": None, "kind": "attending",
                                                   "tier": "attested", "on_date": "1832",
                                                   "basis": "b"})),
           "carries no figure", ids)

    expect("an attested opening that is not exact",
           mutate(lambda d: d["dates"].update(precision="not_later_than")),
           "an attested opening is exact", ids)

    expect("no census class", mutate(lambda d: d.update(type=[])), "no census class", ids)

    expect("a reconstruction with nothing behind it",
           mutate(lambda d: d.update(provenance="reconstructed", sources=[], claim_ids=[])),
           "carries no reconstruction block", ids)

    # THE WIDENED RULE HOLDS EVERY WAY (owner, 2026-09-19; a third door for T-1408, a fourth
    # for T-1424). A reconstructed house is bought by a quota row, by a documented floor, by
    # a standing roof or by a drawn trade head, and the check has to refuse every way that
    # can go wrong — none of the four, more than one, a half quota row, a floor with nothing
    # behind it, a roof the house does not stand on, and a trade head who does not keep the
    # house he bought. Without these the widening would be a hole rather than a door.
    expect("a reconstruction naming neither a quota row nor a floor",
           mutate(lambda d: d.update(provenance="reconstructed", sources=[], claim_ids=[],
                                     reconstruction={"programme": "x", "group": "g",
                                                     "ticket": "T-0001", "seed": "s"})),
           "names neither an order-book row", ids)

    expect("a reconstruction naming a quota row AND a floor",
           mutate(lambda d: d.update(provenance="reconstructed", sources=[], claim_ids=[],
                                     reconstruction={"bucket": "b", "slot": "s",
                                                     "floor": {"count": 1}})),
           "a house is bought once", ids)

    expect("half a quota row",
           mutate(lambda d: d.update(provenance="reconstructed", sources=[], claim_ids=[],
                                     reconstruction={"bucket": "b"})),
           "names a bucket and a slot", ids)

    expect("a floor that cites nothing",
           mutate(lambda d: d.update(provenance="reconstructed", sources=[], claim_ids=[],
                                     reconstruction={"floor": {"count": 7, "note": "n",
                                                               "sources": []}})),
           "cites no source", ids)

    expect("a floor with no count",
           mutate(lambda d: d.update(provenance="reconstructed", sources=[], claim_ids=[],
                                     reconstruction={"floor": {"sources": ["s"], "note": "n"}})),
           "states no count", ids)

    expect("a standing roof that names no keeper",
           mutate(lambda d: d.update(provenance="reconstructed", sources=[], claim_ids=[],
                                     reconstruction={"roof": {"structure_id": "fixture_store",
                                                              "class": "boarding_house",
                                                              "beds_ordinary": 9,
                                                              "keeper_person_id": "",
                                                              "note": "n"}})),
           "names no keeper", ids)

    expect("a standing roof the house does not stand on",
           mutate(lambda d: d.update(provenance="reconstructed", sources=[], claim_ids=[],
                                     reconstruction={"roof": {"structure_id": "somewhere_else",
                                                              "class": "boarding_house",
                                                              "beds_ordinary": 9,
                                                              "keeper_person_id": "rc_x",
                                                              "note": "n"}})),
           "a roof buys the firm of THAT building", ids)

    expect("a reconstruction naming a standing roof AND a quota row",
           mutate(lambda d: d.update(provenance="reconstructed", sources=[], claim_ids=[],
                                     reconstruction={"bucket": "b", "slot": "s",
                                                     "roof": {"structure_id": "fixture_store"}})),
           "a house is bought once", ids)

    def head_block(**over):
        block = {"person_id": "fixture_a", "household_id": "hh_rc_fixture",
                 "trade": "livery_stable_keeper", "head_slot": "s", "note": "n"}
        block.update(over)
        return block

    def street_only(doc):
        doc["locations"] = [{"kind": "street_only", "structure_id": None,
                             "street_id": "lake", "face": None, "primary": True,
                             "from": None, "to": None, "tier": "reconstructed",
                             "basis": "a face off a stated rule", "limit_reason": "no source"}]

    expect("a trade head who does not keep the house he bought",
           mutate(lambda d: (d.update(provenance="reconstructed", sources=[], claim_ids=[],
                                      reconstruction={"trade_head": head_block(
                                          person_id="somebody_else")}),
                             street_only(d))),
           "a head buys the house HE keeps", ids)

    expect("a house bought by a trade head and seated on a roof",
           mutate(lambda d: d.update(provenance="reconstructed", sources=[], claim_ids=[],
                                     reconstruction={"trade_head": head_block()})),
           "the house takes a street face and nothing narrower", ids)

    expect("a reconstruction naming a trade head AND a standing roof",
           mutate(lambda d: d.update(provenance="reconstructed", sources=[], claim_ids=[],
                                     reconstruction={"trade_head": head_block(),
                                                     "roof": {"structure_id": "fixture_store"}})),
           "a house is bought once", ids)

    expect("a compiled record claiming a reconstruction",
           mutate(lambda d: d.update(reconstruction={"programme": "x"})),
           "carries a reconstruction block", ids)

    expect("a reconstructed house citing a source",
           mutate(lambda d: d.update(provenance="reconstructed",
                                     reconstruction={"programme": "x"})),
           "reconstructed and cites a source", ids)

    expect("a community off the vocabulary",
           mutate(lambda d: d["proprietor_community"].update(value="anglo_american")),
           "off the vocabulary", ids)

    expect("a community no named keeper carries",
           mutate(lambda d: d["proprietor_community"].update(value="irish")),
           "the keepers it names read", ids)

    expect("a community read off nobody",
           mutate(lambda d: d["proprietor_community"].update(**{"from": []})),
           "the keepers it names read", ids)

    expect("a community graded attested",
           mutate(lambda d: d["proprietor_community"].update(tier="attested")),
           "a house is not its keeper", ids)

    expect("a community read off a person the town does not hold",
           mutate(lambda d: d["proprietor_community"]["from"][0].update(person_id="fixture_ghost")),
           "which the resident layer does not hold", ids)

    def duplicate(doc):
        pass
    twins = [json.loads(json.dumps(base)), json.loads(json.dumps(base))]
    expect("two records with one id", twins, "two records carry this id", ids)

    # THE COMMITTED COPY IS A DERIVATION, and --check must say so when it is edited.
    #
    # THE COMMENT HERE USED TO SAY "broken in a temporary copy of the tree so the
    # working tree is never touched", AND THAT IS NOT WHAT IT DID (T-1336). The temp
    # copy was the BACKUP; the hand-edit went into the live data/businesses/ record and
    # was copied back in a `finally`. Serially that is invisible. Under check.sh's job
    # pool it is not: the step declared immediately above this one re-derives that same
    # directory, the pool runs the two together, and it reads the edit this fixture is
    # holding. Observed — a branch went red on
    # `biz_a_chicago_stove_and_hollow_ware_dealer_august_1835.json`, which is
    # `sorted(...)[0]`, this fixture's own victim, and `--check` was green on the same
    # tree run alone.
    #
    # So the COPY is now the thing that is edited. `check()` reads the module-level
    # BUSINESSES, and a self-test runs in its own process, so rebinding it is enough:
    # this process checks the copy while every other process still sees the committed
    # records. The `finally` puts the binding back, not the bytes — no byte of the live
    # directory is written any more.
    if BUSINESSES.is_dir():
        live = BUSINESSES
        with tempfile.TemporaryDirectory() as tmp:
            scratch = Path(tmp) / "businesses"
            shutil.copytree(live, scratch)
            sample = sorted(scratch.glob("biz_*.json"))
            if sample:
                target = sample[0]
                try:
                    BUSINESSES = scratch
                    doc = load_json(target)
                    doc["name"] = doc["name"] + " (hand-edited)"
                    target.write_text(dumps(doc), encoding="utf-8")
                    if not any("differs from a rebuild" in b for b in check()):
                        failures.append("a hand-edited compiled record was not refused")
                finally:
                    BUSINESSES = live

    # The build is deterministic: two compiles of the same input agree byte for byte.
    first, _, index_a = compiled_docs()
    second, _, index_b = compiled_docs()
    if dumps(first) != dumps(second) or dumps(index_a) != dumps(index_b):
        failures.append("the compile is not deterministic")

    for failure in failures:
        print("  FAIL  " + failure, file=sys.stderr)
    if failures:
        return 1
    print("self-test: %d assertion(s) fire when broken, and the compile is deterministic"
          % len(fired))
    return 0


def community_report():
    """Every figure docs/RESEARCH/business_community_1835.md prints, printed here.

    NOTHING ON THAT PAGE IS HAND-COUNTED. It is the same discipline
    docs/RESEARCH/community_shares_1835.md holds itself to, and for the same reason: a
    share nobody can re-derive is a share nobody can check.
    """
    records, authored, index = compiled_docs()
    everything = records + authored
    total = len(everything)
    by_value = index["counts"]["by_proprietor_community"]
    by_rule, by_tier = {}, {}
    disagreeing = []
    for record in everything:
        block = record["proprietor_community"]
        by_rule[block["rule"]] = by_rule.get(block["rule"], 0) + 1
        key = block["tier"] or "—"
        by_tier[key] = by_tier.get(key, 0) + 1
        if block["rule"] == "proprietors_disagree":
            disagreeing.append((record["name"],
                                sorted({r["community"] for r in block["from"]
                                        if r["community"] != "unknown"})))
    known = total - by_value.get("unknown", 0)
    print("%d business record(s); %d read a community, %d do not" % (total, known, total - known))
    print()
    print("| community | houses | of all %d | of the %d read |" % (total, known))
    print("|---|---:|---:|---:|")
    for value, label in community_vocabulary():
        count = by_value.get(value, 0)
        if value == "unknown":
            continue
        print("| %s (`%s`) | %d | %.1f%% | %.1f%% |"
              % (label, value, count, 100.0 * count / total,
                 100.0 * count / known if known else 0.0))
    print("| **unknown** | **%d** | **%.1f%%** | — |"
          % (by_value.get("unknown", 0), 100.0 * by_value.get("unknown", 0) / total))
    print()
    print("by rule: %s" % dict(sorted(by_rule.items())))
    print("by tier: %s" % dict(sorted(by_tier.items())))
    print()
    print("the %d houses whose keepers do not agree:" % len(disagreeing))
    for name, values in sorted(disagreeing):
        print("  %-28s %s" % (name, ", ".join(values)))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--community-report", action="store_true")
    args = ap.parse_args(argv)
    if args.build:
        return build()
    if args.self_test:
        return self_test()
    if args.community_report:
        return community_report()
    bad = check()
    for problem in bad:
        print("  FAIL  " + problem, file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
