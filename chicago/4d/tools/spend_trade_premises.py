#!/usr/bin/env python3
"""The 37 corroborated_enrichment trade and premises units, read against the finished
business layer and spent one at a time (T-1469).

    python3 tools/spend_trade_premises.py             what each of the 37 units does
    python3 tools/spend_trade_premises.py --write     write the derived register
    python3 tools/spend_trade_premises.py --check     it re-derives; nothing drifted
    python3 tools/spend_trade_premises.py --self-test the rules below, over the table

WHY THIS EXISTS. T-1301 read all 98 `corroborated_enrichment` findings one at a time and
handed each to the OPEN ticket whose acceptance owns the kind of fact it names. Thirty-
seven of them named a TRADE, a firm, a shop, a tavern, a store or the PREMISES one was
kept at, and they have been handed on ever since -- T-1182, then its five children, then
T-1190, then its three, then T-1468 -- without once being read against the cards they
name. A hand-off is not a spend. This is the spend.

WHAT CHANGED UNDER THEM, AND WHY THE ANSWER IS NOW A READING RATHER THAN A DEFERRAL. The
rule these 37 sat under says the finding names a fact "that no exact source-bearing
structured field on that card carries today". That was true when it was written. It is not
true now, and three programmes are why:

  * THE BUSINESS LAYER IS BUILT (T-1310) AND CONVERGED (T-1440..T-1442). A card's
    `persons[].workplaces[]` names the `biz_*` record, the role held in it and the printing
    window that bounds the reading, and the household's `works_at` names the premises.
  * THE SINGLE OCCUPATION FIELD BECAME DATED PLURAL ROLES (T-0837, T-0991, written by
    tools/derive_resident_roles.py). `persons[].roles[]` carries every trade a source
    prints for the man WITH the bound that source permits and a `covers_scene_date` flag,
    and the 1835 field reads `none_recorded` where nothing in the window reaches it --
    with `occupation.withdrawn_from_scene_date` carrying the audit's verdict for the
    withdrawal and `occupation.later_occupation` pointing at the year a later volume does
    print. An absence there is an ANSWER, not a gap.
  * THE CANDIDATE-FACT TABLE IS COMMITTED (T-1232). `persons[].profile_facts[]` carries a
    reading's own `as_read` wording, its source, the date it speaks about and the research
    record id it came from.

So the question this pass asks of each of the 37 is not "is there a field?" but "WHICH
field carries it, and does that field reach 1 July 1835?" -- and where nothing carries it,
the refusal is written with its reason instead.

THE SIX OUTCOMES, and `--self-test` refuses a seventh.

  1. CARRIED AT THE SCENE DATE (21). The card's 1835 trade field holds the trade the
     finding names, graded and cited, and the premises stands in `works_at` or in a
     `workplaces[]` row naming its `biz_*` record. Under the ladder ratified 2026-09-03
     corroboration corroborates; it does not promote. `refused`.
  2. CARRIED WITH THE CARD'S OWN BOUND OUTSIDE THE WINDOW (6). The trade is on the card
     and is dated OUT of the scene window by the card itself -- Elston's soap and candle
     manufactory last printed 2 July 1834, Mason's firm 10 December 1834, Kimball's New
     Store June 1834, Bailey's and Chapman's trades printed in 1839. The finding names no
     field the card lacks; it names one the card has already refused for 1835, with its
     reason. `refused`.
  3. CARRIED AS A DATED PROFILE FACT (4). The reading is on the card verbatim, in
     `profile_facts[]`, with its source, the date it speaks about and its research record
     id. These are the four whose 1835 trade field is `none_recorded` and whose evidence
     is a life event rather than a printing. `refused`.
  4. PRINTED FOR A YEAR AFTER THE SCENE DATE (3). The trade or the incorporation the
     finding names describes 1836 or 1839. A directory of 1839 is evidence about 1839 and
     this project does not back-project one. `later_only`, which is the terminal
     disposition the registers already use for exactly this.
  5. NO FIELD CARRIES THE ENGAGEMENT, AND IT NAMES NO 1835 TRADE (2). Handy in the 1833
     river improvement and Chandler in executive charge of the harbour work from 1 July
     1833 are dated PRE-SCENE public-work engagements, not trades. Chandler's is already
     an adjudicated row in data/residents/person_facts.json under its own verdict; Handy's
     research block proposed no candidate at all. Neither names a trade the 1835 field
     lacks, and this pass refuses them here rather than handing them to a fourth ticket.
     `refused`.
  6. THE READING CONTRADICTS A TRADE THE CARD CARRIES (1). Pearsons is the one finding
     that does not corroborate: the reminiscence gives a HOUSE PAINTER, and the card
     carries `speculator` at `attested` on a note that calls it "this project's reading".
     Correcting that is a re-adjudication of the 1835 trade field, which
     tools/derive_resident_roles.py owns and this pass may not hand-edit. It is the one
     unit that stays `unresolved`, and it names the open ticket that owns the correction.

WHAT THIS PASS MAY NOT DO.

  * IT WRITES NOTHING ONTO A CARD. Every field it names was written by the pass that owns
    it. This pass reads, and the register records what it read, so a reader can put the
    note beside the card and see that it says what the card says.
  * IT NEVER NAMES A CARRIER IT CANNOT SHOW. A carrier must resolve on disk, be graded
    `attested`, `inferred` or `documented` (or a `workplaces[]` row at that tier) and cite
    at least one source. `--self-test` mutates each of the three and requires a fault.
  * A REFUSAL MAY NOT NAME A CARRIER AND A CARRY MAY NOT BE EMPTY. The two outcomes that
    refuse for want of a field (5 and 6) carry no carrier at all, because a refusal that
    points at a field is a carry wearing a refusal.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESIDENTS = ROOT / "data" / "residents"
RESEARCH = ROOT / "data" / "research" / "residents"
REGISTER = RESEARCH / "trade_premises_spend.json"

TICKET = "T-1469"
GENERATOR = "tools/spend_trade_premises.py"
SCENE_DATE = "1835-07-01"
GRADED = {"attested", "inferred", "documented"}

CARRIED = "the_trade_or_premises_is_carried_by_the_card_at_the_scene_date"
BOUNDED = "the_trade_is_carried_with_the_card_s_own_bound_outside_the_window"
PROFILE = "the_reading_is_carried_as_a_dated_profile_fact_on_the_card"
LATER = "the_trade_or_premises_is_printed_for_a_year_after_the_scene_date"
UNREACHED = "the_engagement_reaches_no_field_and_names_no_trade_the_1835_field_lacks"
HANDED = "the_reading_contradicts_the_trade_the_card_carries_and_the_field_is_re_adjudicated"

OUTCOMES = (CARRIED, BOUNDED, PROFILE, LATER, UNREACHED, HANDED)
CARRYING = (CARRIED, BOUNDED, PROFILE)
REFUSING = (UNREACHED, HANDED)

# The ticket the one contradicted reading is handed to. It is named here rather than in
# the register so that the register stays derived, and the ledger's own ownership
# invariant is what proves it is live work rather than a spent parent.
HANDED_TICKET = "T-1507"

RULES = {
    CARRIED: {
        "disposition": "refused",
        "statement": (
            "The completed pass returned `corroborated_enrichment` naming a trade, a shop, a "
            "tavern, a store or the premises one was kept at, and T-1469 read it against the "
            "finished business layer: the card's 1835 trade field ALREADY carries that trade, "
            "graded and citing a source of its own, and the premises stands beside it in the "
            "household's `works_at` or in a `persons[].workplaces[]` row naming its `biz_*` "
            "record. Under the evidence ladder ratified 2026-09-03 corroboration corroborates; "
            "it does not promote, and a second volume agreeing that a man the card already "
            "calls a saddler was a saddler names no field to fill. The fields it reaches are "
            "named on this unit's own note, which prints the card's value beside the finding."),
    },
    BOUNDED: {
        "disposition": "refused",
        "statement": (
            "The completed pass returned `corroborated_enrichment` naming a trade, and T-1469 "
            "read it against the card: the trade IS on the card, and the card's own dated "
            "evidence puts it outside the scene window. `persons[].roles[]` carries it with "
            "the bound its sources permit and `covers_scene_date` false, and either "
            "`occupation.withdrawn_from_scene_date` carries the audit's verdict for withdrawing "
            "it from the 1835 field (T-0991) or `occupation.later_occupation` names the year a "
            "later volume prints it (T-0693). This is a finished answer rather than a deferral: "
            "the finding names no field the card lacks, it names one the card has already "
            "refused for 1 July 1835 with its reason, and a corroborating volume does not move "
            "a bound its own printing does not reach."),
    },
    PROFILE: {
        "disposition": "refused",
        "statement": (
            "The completed pass returned `corroborated_enrichment` naming a trade or a life "
            "event, and T-1469 read it against the card: it is carried VERBATIM in "
            "`persons[].profile_facts[]`, the committed candidate-fact table's spend (T-1232), "
            "with the finding's own `as_read` wording, its source, the date it speaks about and "
            "the research record id it came from. The 1835 trade field reads `none_recorded` on "
            "these four and that is the answer their evidence supports -- a tavern remembered "
            "in a local history and a map drawn in 1834 are events this layer dates, not trades "
            "the scene-date field may assert. The reading has reached a structured field; it is "
            "not waiting on one."),
    },
    LATER: {
        "disposition": "later_only",
        "statement": (
            "The completed pass returned `corroborated_enrichment` naming a trade, a premises "
            "or an incorporation, and the thing it names describes a date AFTER 1 July 1835 -- "
            "Fergus's directory of 1839 for two of them, the January 1836 incorporation of the "
            "Chicago Hydraulic Company for the third. Under T-0513's ladder a source printed or "
            "describing after the scene date may date and corroborate and may never promote, "
            "and this project does not back-project a trade a later volume prints. The card "
            "carries what the 1835 sources reach; the later reading is recorded on this unit's "
            "note with the year it is about, which is what `later_only` is for."),
    },
    UNREACHED: {
        "disposition": "refused",
        "statement": (
            "The completed pass returned `corroborated_enrichment` naming a dated PUBLIC-WORK "
            "ENGAGEMENT before the scene date -- the 1833 river improvement, executive charge "
            "of the harbour work begun 1 July 1833 -- and T-1469 read it against the card: it "
            "is not a trade, it reaches no trade field, and it asks none. One of the two is "
            "already an adjudicated row in data/residents/person_facts.json carrying its own "
            "verdict and reason; the other's research block proposed no candidate at all. "
            "Refusing them here is the finished answer, because the alternative -- handing an "
            "1833 engagement to a fourth ticket that owns 1835 trades -- is the deferral this "
            "pass exists to end."),
    },
    HANDED: {
        "disposition": "unresolved",
        "ticket": HANDED_TICKET,
        "statement": (
            "The completed pass returned `corroborated_enrichment` and it does NOT corroborate: "
            "the reminiscence gives Hiram Pearsons a HOUSE PAINTER'S trade, and the card carries "
            "`speculator` at `attested` on a note that calls it this project's own reading of a "
            "man who arrived before the land craze. One of the two has a source and the other "
            "has an inference wearing a grade, which is the fault the finding was raised "
            "against. Correcting it is a re-adjudication of the 1835 trade field -- the field "
            "tools/derive_resident_roles.py derives from the role readings -- and a register may "
            "not hand-edit a derived field. It is the one unit of the thirty-seven that stays "
            "unresolved, and the ticket it names owns the correction."),
    },
}

# THE ADJUDICATION. One row per unit, keyed by the pass that read it and the person it is
# about -- the same key `tools/spend_remainder_rulings.py` routes enrichments on, so the
# two tables can be checked against each other in both directions and neither can grow a
# unit the other has not seen.
#
#   outcome   one of the six above
#   reading   the trade or premises the finding names, in this pass's words
#   carrier   the fields on committed records that carry it, resolved and graded below.
#             Empty for the two refusing outcomes, and required for the three carrying ones.
#   describes the year the reading is about, for the `later_only` rows only, which
#             `--self-test` requires to fall after the scene date.
#
# A carrier is (field, selector). The fields, and what a selector picks out:
#   occupation        the person's 1835 trade block; the selector is its value
#   withdrawn         occupation.withdrawn_from_scene_date; the selector is its value
#   later_occupation  occupation.later_occupation; the selector is its value
#   roles             a persons[].roles[] row; the selector matches role or as_printed
#   workplaces        a persons[].workplaces[] row; the selector is its business_id
#   profile_facts     a persons[].profile_facts[] row; the selector matches value or as_read
#   works_at          the household's own premises block; the selector is its value
ADJUDICATION: dict[tuple[str, str], dict] = {
    ("02", "bates_john_jr"): {
        "outcome": CARRIED,
        "reading": "an auctioneer's trade, and a Lake Street address the 1843 directory prints",
        "carrier": [("occupation", "auctioneer"), ("works_at", "bates_auction_room")],
    },
    ("02", "calhoun_john"): {
        "outcome": CARRIED,
        "reading": "the founding and operation of a printing office",
        "carrier": [("occupation", "editor"),
                    ("workplaces", "biz_chicago_democrat_printing_office"),
                    ("works_at", "chicago_democrat_office")],
    },
    ("02", "clybourne_archibald"): {
        "outcome": CARRIED,
        "reading": "a slaughterhouse and a meat trade with their premises",
        "carrier": [("occupation", "butcher"), ("works_at", "clybourn_slaughterhouse")],
    },
    ("02", "couch_ira"): {
        "outcome": CARRIED,
        "reading": "the keeping of the Tremont House",
        "carrier": [("occupation", "hotel_keeper"), ("works_at", "tremont_house_1")],
    },
    ("02", "pearsons_hiram"): {
        "outcome": HANDED,
        "reading": "a house painter's trade, against the `speculator` the card carries as attested",
        "carrier": [],
    },
    ("02", "sen_elijah_wentworth"): {
        "outcome": PROFILE,
        "reading": "a tavern kept at Wolf Point and later at Sand Ridge",
        "carrier": [("profile_facts", "Wolf Point tavern keeper")],
    },
    ("02", "taylor_augustine"): {
        "outcome": CARRIED,
        "reading": "a builder's trade and the building of St Mary's",
        "carrier": [("occupation", "carpenter"), ("works_at", "st_marys_church")],
    },
    ("03", "blodgett_tyler_k"): {
        "outcome": CARRIED,
        "reading": "an 1833 north-bank brickyard and a brick house",
        "carrier": [("occupation", "brickmaker"), ("works_at", "brickyard_north_side")],
    },
    ("03", "brown_rufus"): {
        "outcome": CARRIED,
        "reading": "a log boarding house kept full",
        "carrier": [("occupation", "boarding_house_keeper"), ("works_at", "brown_boarding_house")],
    },
    ("03", "cobb_silas_b"): {
        "outcome": CARRIED,
        "reading": "saddlery and harness work, and a Lake Street address the 1843 directory prints",
        "carrier": [("occupation", "saddler"),
                    ("workplaces", "biz_s_b_cobb_saddle_harness_and_trunk_manufactory"),
                    ("works_at", "goss_cobb_saddlery")],
    },
    ("03", "cohen_peter"): {
        "outcome": LATER,
        "reading": "incorporation of the Chicago Hydraulic Company",
        "carrier": [],
        "describes": "1836-01",
    },
    ("03", "davis_t_o"): {
        "outcome": CARRIED,
        "reading": "the establishing of the Whig newspaper in 1835",
        "carrier": [("occupation", "editor"), ("works_at", "chicago_american_office")],
    },
    ("03", "elston_daniel"): {
        "outcome": BOUNDED,
        "reading": "soap and candle manufacture, and a later distillery and brewery",
        "carrier": [("withdrawn", "soap_and_candle_maker"),
                    ("roles", "soap_and_candle_maker"),
                    ("workplaces", "biz_chicago_soap_and_candle_manufactory"),
                    ("works_at", "elston_soap_candle_manufactory")],
    },
    ("03", "ingersoll_chester"): {
        "outcome": CARRIED,
        "reading": "the Green Tree house held as landlord 1834-37",
        "carrier": [("occupation", "tavern_keeper"), ("works_at", "green_tree_tavern")],
    },
    ("04", "handy_major"): {
        "outcome": UNREACHED,
        "reading": "a named role in the 1833 river-improvement works",
        "carrier": [],
    },
    ("04", "kinzie_robert_a"): {
        "outcome": CARRIED,
        "reading": "a frame store and membership of Kinzie, Davis & Hyde",
        "carrier": [("occupation", "merchant"), ("works_at", "robert_kinzie_store")],
    },
    ("04", "mason_matthias"): {
        "outcome": BOUNDED,
        "reading": "a blacksmith shop opened in the fall of 1833",
        "carrier": [("withdrawn", "blacksmith"),
                    ("roles", "blacksmith"),
                    ("workplaces", "biz_matthias_mason_co"),
                    ("works_at", "mason_blacksmith_shop")],
    },
    ("04", "mckee_david"): {
        "outcome": CARRIED,
        "reading": "the agency blacksmith's shop at the foot of State Street",
        "carrier": [("occupation", "blacksmith"), ("works_at", "blacksmith_shop_state_st")],
    },
    ("04", "murphy_john"): {
        "outcome": CARRIED,
        "reading": "the keeping of the Exchange Coffee House from August 1834",
        "carrier": [("occupation", "tavern_keeper"), ("works_at", "exchange_coffee_house")],
    },
    ("04", "pruyne_peter"): {
        "outcome": CARRIED,
        "reading": "a drug store kept in partnership from early 1833",
        "carrier": [("occupation", "druggist"),
                    ("workplaces", "biz_p_pruyne_co"),
                    ("works_at", "pruyne_kimball_drugstore")],
    },
    ("04", "thomas_frederick"): {
        "outcome": CARRIED,
        "reading": "a barber-surgeon's and retail druggist's trade",
        "carrier": [("occupation", "barber_surgeon"),
                    ("workplaces", "biz_frederick_thomas_drugs_and_paints"),
                    ("works_at", "frederick_thomas_shop")],
    },
    ("04", "walters_william"): {
        "outcome": CARRIED,
        "reading": "the Wolf Point Tavern kept 1833-36",
        "carrier": [("occupation", "tavern_keeper"), ("works_at", "wolf_point_tavern")],
    },
    ("05", "kimball_walter"): {
        "outcome": BOUNDED,
        "reading": "a New Store at the South Water and Clark junction",
        "carrier": [("withdrawn", "dry_goods_merchant"),
                    ("roles", "dry_goods_merchant"),
                    ("workplaces", "biz_w_kimball_s_new_store")],
    },
    ("05", "lampman_henry_s"): {
        "outcome": CARRIED,
        "reading": "a brickmaker's trade and the yard that engaged him",
        "carrier": [("occupation", "brickmaker"), ("works_at", "brickyard_north_side")],
    },
    ("06", "mitchell_henry"): {
        "outcome": PROFILE,
        "reading": "wagon-factory work in 1834",
        "carrier": [("profile_facts", "wagon-factory work")],
    },
    ("09", "chandler_joseph"): {
        "outcome": UNREACHED,
        "reading": "executive charge of the harbour work begun 1 July 1833",
        "carrier": [],
    },
    ("09", "hathaway_joshua"): {
        "outcome": PROFILE,
        "reading": "the making of the 1834 cadastral map",
        "carrier": [("profile_facts", "cadastral map")],
    },
    ("14", "bailey_bennet"): {
        "outcome": BOUNDED,
        "reading": "a carpenter and builder's trade printed in 1839",
        "carrier": [("later_occupation", "carpenter and builder"),
                    ("roles", "carpenter and builder")],
    },
    ("14", "chapman_chas_h"): {
        "outcome": BOUNDED,
        "reading": "a real-estate dealer's trade and a Randolph Street address",
        "carrier": [("later_occupation", "real estate dealer"),
                    ("roles", "real estate dealer"),
                    ("workplaces", "biz_c_h_chapman")],
    },
    ("14", "clarke_h_b"): {
        "outcome": CARRIED,
        "reading": "a hardware merchant's trade the 1835 papers carry",
        "carrier": [("occupation", "hardware_merchant"), ("workplaces", "biz_jones_king_co")],
    },
    ("14", "collins_j_h"): {
        "outcome": CARRIED,
        "reading": "an attorney's practice carried across 1834-35",
        "carrier": [("occupation", "attorney"), ("workplaces", "biz_collins_caton")],
    },
    ("14", "elston_daniel"): {
        "outcome": BOUNDED,
        "reading": "soap and candle manufacture read in pass 3 and never written",
        "carrier": [("withdrawn", "soap_and_candle_maker"),
                    ("roles", "soap_and_candle_maker"),
                    ("workplaces", "biz_daniel_elston_co"),
                    ("works_at", "elston_soap_candle_manufactory")],
    },
    ("14", "marshall_j_a"): {
        "outcome": LATER,
        "reading": "an auction and commission trade on South Water Street",
        "carrier": [],
        "describes": "1839",
    },
    ("14", "moore_henry"): {
        "outcome": CARRIED,
        "reading": "an attorney's practice and a Clark Street office",
        "carrier": [("occupation", "attorney"), ("workplaces", "biz_henry_moore")],
    },
    ("14", "sabine_wm"): {
        "outcome": LATER,
        "reading": "a boarding house at 161 Lake Street",
        "carrier": [],
        "describes": "1839",
    },
    ("14", "sen_elijah_wentworth"): {
        "outcome": PROFILE,
        "reading": "the Wolf Point tavern, carried forward from pass 2",
        "carrier": [("profile_facts", "Wolf Point tavern keeper")],
    },
    ("14", "stewart_r"): {
        "outcome": CARRIED,
        "reading": "an attorney's practice on Lake Street",
        "carrier": [("occupation", "attorney"), ("workplaces", "biz_r_stewart_attorney")],
    },
}


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def person_index(root: Path = ROOT) -> dict[str, tuple[Path, dict, dict]]:
    """Every person the resident layer holds, and the record they stand in."""
    index: dict[str, tuple[Path, dict, dict]] = {}
    for path in sorted((root / "data" / "residents").rglob("*.json")):
        try:
            doc = read_json(path)
        except (ValueError, OSError):
            continue
        if not isinstance(doc, dict) or not isinstance(doc.get("persons"), list):
            continue
        for person in doc["persons"]:
            if isinstance(person, dict) and person.get("id"):
                index.setdefault(person["id"], (path, doc, person))
    return index


def cited(block) -> list[str]:
    if not isinstance(block, dict):
        return []
    out = []
    for key in ("sources", "claim_ids"):
        value = block.get(key)
        if isinstance(value, list):
            out.extend(str(item) for item in value if item)
    for key in ("source", "source_id"):
        if block.get(key):
            out.append(str(block[key]))
    return out


def grade(block) -> str | None:
    if not isinstance(block, dict):
        return None
    for key in ("confidence", "tier"):
        if block.get(key):
            return str(block[key])
    return None


def resolve(field: str, selector: str, path: Path, household: dict, person: dict):
    """The block a carrier names, and the pointer that says where it stands."""
    pid = person["id"]
    rel = path.relative_to(ROOT).as_posix()
    occupation = person.get("occupation") if isinstance(person.get("occupation"), dict) else {}
    if field == "occupation":
        block = occupation
        if str(block.get("value") or "") != selector:
            return None, f"{rel}#persons[{pid}].occupation"
        return block, f"{rel}#persons[{pid}].occupation"
    if field in ("withdrawn", "later_occupation"):
        key = "withdrawn_from_scene_date" if field == "withdrawn" else "later_occupation"
        block = occupation.get(key)
        pointer = f"{rel}#persons[{pid}].occupation.{key}"
        if not isinstance(block, dict) or str(block.get("value") or "") != selector:
            return None, pointer
        return block, pointer
    if field == "works_at":
        block = household.get("works_at")
        pointer = f"{rel}#works_at"
        if not isinstance(block, dict) or str(block.get("value") or "") != selector:
            return None, pointer
        return block, pointer
    if field in ("roles", "workplaces", "profile_facts"):
        rows = person.get(field)
        rows = rows if isinstance(rows, list) else []
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            if field == "roles":
                hay = f"{row.get('role') or ''} {row.get('as_printed') or ''}"
            elif field == "workplaces":
                hay = str(row.get("business_id") or "")
            else:
                hay = f"{row.get('value') or ''} {row.get('as_read') or ''}"
            if selector in hay:
                return row, f"{rel}#persons[{pid}].{field}[{index}]"
        return None, f"{rel}#persons[{pid}].{field}"
    raise SystemExit(f"{field!r} is not a field a carrier may name")


def reaches_scene_date(field: str, block: dict) -> bool:
    """Whether the block the carrier names stands in the 1 July 1835 view."""
    if field == "roles":
        return bool(block.get("covers_scene_date"))
    if field in ("withdrawn", "later_occupation"):
        return False
    if field == "workplaces":
        return bool(block.get("business_present_at_scene_date"))
    if field == "profile_facts":
        return False
    return True


def finding(pass_id: str, person_id: str, cache: dict) -> dict:
    path = RESEARCH / f"pass_{pass_id}_findings.json"
    doc = cache.get(path)
    if doc is None:
        doc = cache[path] = read_json(path)
    return (doc.get("overrides") or {}).get(person_id) or {}


def clip(text, limit: int = 300) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def carriers_for(key: tuple[str, str], row: dict, index: dict) -> tuple[list[dict], list[str]]:
    pass_id, person_id = key
    faults: list[str] = []
    found = index.get(person_id)
    if found is None:
        return [], [f"{pass_id}/{person_id}: the resident layer holds no such person"]
    path, household, person = found
    out = []
    for field, selector in row["carrier"]:
        block, pointer = resolve(field, selector, path, household, person)
        where = f"{pass_id}/{person_id} names {pointer}"
        if block is None:
            faults.append(f"{where}, which does not carry {selector!r}")
            continue
        confidence = grade(block)
        sources = cited(block)
        if confidence not in GRADED:
            faults.append(f"{where}, which is {confidence!r} and not attested, inferred or documented")
        if field == "withdrawn":
            # A WITHDRAWAL IS A VERDICT, NOT A CITATION. `occupation.withdrawn_from_scene_date`
            # is what T-0991's audit wrote when it took a trade OUT of the 1835 field, so it
            # names the verdict and the ticket that reached it; the sources stay on the
            # `roles[]` row the trade was withdrawn to. Asking it for a source would be asking
            # the wrong block, and a BOUNDED row still has to show a cited one -- `--self-test`
            # rule 10 is where that is required, over the row rather than over this block.
            if not block.get("verdict") or not block.get("ticket"):
                faults.append(f"{where}, which is a withdrawal stating neither a verdict nor the ticket that reached it")
        elif not sources:
            faults.append(f"{where}, which cites no source")
        out.append({
            "field": field,
            "at": pointer,
            "value": clip(block.get("value") or block.get("business_name")
                          or block.get("as_printed") or block.get("role") or selector, 120),
            "grade": confidence,
            "sources": sorted(set(sources)),
            "reaches_scene_date": reaches_scene_date(field, block),
        })
    return out, faults


def note_for(key: tuple[str, str], row: dict, carriers: list[dict]) -> str:
    """Derived: the finding in its own words, and the fields the card answers it with."""
    pass_id, person_id = key
    found = finding(pass_id, person_id, note_for.cache)
    summary = clip(found.get("summary"), 320)
    sources = ", ".join(str(s) for s in (found.get("sources") or [])) or "none named"
    head = (f"The pass on {person_id} returned: “{summary}” Sources as recorded: "
            f"{clip(sources, 160)}. T-1469 reads that as {row['reading']}.")
    if carriers:
        named = "; ".join(
            f"{c['at']} = “{c['value']}” ({c['grade']}, {'in' if c['reaches_scene_date'] else 'outside'} "
            f"the 1 July 1835 view)" for c in carriers)
        return head + " The card carries it at " + named + "."
    if row["outcome"] == LATER:
        return head + (f" Nothing on the card carries it for the scene date, and the reading "
                       f"describes {row['describes']}, which is after 1 July 1835.")
    if row["outcome"] == UNREACHED:
        return head + (" No field on the card carries the engagement and none is asked for: it is "
                       "a dated pre-scene public work, not a trade the 1835 field lacks.")
    return head + (" No field carries it, because the card carries the OPPOSITE reading at a grade "
                   f"the finding disputes; {HANDED_TICKET} owns the re-adjudication.")


note_for.cache = {}


def build(root: Path = ROOT) -> tuple[dict, list[str]]:
    index = person_index(root)
    faults: list[str] = []
    rows = []
    for key in sorted(ADJUDICATION):
        row = ADJUDICATION[key]
        carriers, carrier_faults = carriers_for(key, row, index)
        faults.extend(carrier_faults)
        pass_id, person_id = key
        rows.append({
            "unit": unit_id(pass_id, person_id),
            "pass": pass_id,
            "person": person_id,
            "outcome": row["outcome"],
            "rule": row["outcome"],
            "reading": row["reading"],
            "describes": row.get("describes"),
            "carries": carriers,
            "note": note_for(key, row, carriers),
        })
    tally = {outcome: sum(1 for row in rows if row["outcome"] == outcome) for outcome in OUTCOMES}
    document = {
        "schema": "trade-premises-spend-v1",
        "_doc": (
            "DERIVED, T-1469, by tools/spend_trade_premises.py from the resident layer and the "
            "pass findings beside it -- run --check to re-derive it. The 37 "
            "`corroborated_enrichment` units naming a trade, a shop, a tavern, a store or the "
            "premises one was kept at, each read against the finished business layer and given "
            "one of six outcomes. Nothing here writes a card: every field a row names was "
            "written by the pass that owns it, and this register records which field answers "
            "which finding."),
        "ticket": TICKET,
        "generated_by": GENERATOR,
        "scene_date": SCENE_DATE,
        "counts": {"units": len(rows), "by_outcome": tally},
        "rows": rows,
    }
    return document, faults


def unit_id(pass_id: str, person_id: str) -> str:
    return (f"residents:data/research/residents/pass_{pass_id}_75_cohort.json"
            f"#people/{person_id}")


def rule_for(key: tuple[str, str]) -> str:
    """The rule tools/spend_remainder_rulings.py should write for this enrichment."""
    return ADJUDICATION[key]["outcome"]


def carrier_sentence(key: tuple[str, str]) -> str:
    """The derived note this pass stands behind, for the register that routes the unit."""
    row = ADJUDICATION[key]
    index = person_index()
    carriers, _ = carriers_for(key, row, index)
    return note_for(key, row, carriers)


def write(root: Path = ROOT) -> int:
    document, faults = build(root)
    for fault in faults:
        print("   FAIL: " + fault)
    if faults:
        return 1
    REGISTER.parent.mkdir(parents=True, exist_ok=True)
    REGISTER.write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {REGISTER.relative_to(ROOT)}: {document['counts']['units']} units")
    return 0


def check(root: Path = ROOT) -> int:
    document, faults = build(root)
    for fault in faults:
        print("   FAIL: " + fault)
    if not REGISTER.exists():
        print(f"   FAIL: {REGISTER.relative_to(ROOT)} has not been written")
        return 1
    committed = read_json(REGISTER)
    if committed != document:
        print(f"   FAIL: {REGISTER.relative_to(ROOT)} does not re-derive from the layer as committed")
        faults.append("drift")
    if faults:
        return 1
    print("OK: the trade and premises spend re-derives from the cards it names")
    return 0


def describe() -> int:
    document, faults = build()
    for row in document["rows"]:
        print(f"{row['outcome'][:34]:<34} {row['pass']}/{row['person']}")
    print()
    for outcome, count in document["counts"]["by_outcome"].items():
        print(f"  {count:>3}  {outcome}")
    for fault in faults:
        print("   FAIL: " + fault)
    return 1 if faults else 0


def self_test() -> int:
    failures: list[str] = []

    # 1. The vocabulary is closed. A seventh outcome is a silent reclassification.
    for key, row in ADJUDICATION.items():
        if row["outcome"] not in OUTCOMES:
            failures.append(f"{key} claims outcome {row['outcome']!r}, which is not one of the six")

    # 2. A carry must name a field and a refusal may not. A refusal that points at a field
    #    is a carry wearing a refusal, and it is the way this pass could understate itself.
    for key, row in ADJUDICATION.items():
        if row["outcome"] in CARRYING and not row["carrier"]:
            failures.append(f"{key} carries the reading and names no field it reaches")
        if row["outcome"] in REFUSING and row["carrier"]:
            failures.append(f"{key} refuses the reading and names a field anyway")

    # 3. `later_only` has to say which year it is about, and the year has to fall after the
    #    scene date. A later_only that describes 1834 is a refusal wearing a disposition.
    for key, row in ADJUDICATION.items():
        describes = row.get("describes")
        if row["outcome"] == LATER:
            if not describes:
                failures.append(f"{key} is later_only and names no year it describes")
            elif str(describes) <= SCENE_DATE[:len(str(describes))]:
                failures.append(f"{key} is later_only and describes {describes}, which is not after the scene date")
        elif describes:
            failures.append(f"{key} names a year it describes and is not later_only")

    # 4. Every carrier resolves, is graded and cites a source, over the layer as committed.
    document, faults = build()
    failures.extend(faults)

    # 5. A CARRIED row's 1835 trade field must actually stand in the scene-date view, and a
    #    BOUNDED row's must not. This is the distinction the two outcomes exist to make, and
    #    without it BOUNDED is just CARRIED with a different word on it.
    by_unit = {row["unit"]: row for row in document["rows"]}
    for key, row in ADJUDICATION.items():
        entry = by_unit[unit_id(*key)]
        occupations = [c for c in entry["carries"] if c["field"] == "occupation"]
        if row["outcome"] == CARRIED and not occupations:
            failures.append(f"{key} is carried at the scene date and names no 1835 trade field")
        if row["outcome"] == BOUNDED and occupations:
            failures.append(f"{key} is bounded outside the window and names the 1835 trade field")
        if row["outcome"] == BOUNDED and not any(
                c["field"] in ("withdrawn", "later_occupation") for c in entry["carries"]):
            failures.append(f"{key} is bounded outside the window and shows no withdrawal or later printing")
        if row["outcome"] == PROFILE and not any(c["field"] == "profile_facts" for c in entry["carries"]):
            failures.append(f"{key} is carried as a profile fact and names no profile fact")

    # 10. A BOUNDED row shows a withdrawal, and a withdrawal is a verdict rather than a
    #     citation -- so the row itself still has to name at least one carrier that cites a
    #     source. Without this the outcome could rest on nothing but this project's own
    #     verdict about its own field.
    for key, row in ADJUDICATION.items():
        if row["outcome"] not in CARRYING:
            continue
        entry = by_unit[unit_id(*key)]
        if not any(c["sources"] for c in entry["carries"]):
            failures.append(f"{key} carries the reading and not one of its fields cites a source")

    # 6. A mutated carrier must fail. Three mutations, one per licence the carrier has to
    #    show: the field exists, it is graded, it cites a source.
    index = person_index()
    probe = ("02", "couch_ira")
    for mutation, why in (
            ({"carrier": [("occupation", "not_a_trade_anybody_carries")]}, "a selector nothing carries"),
            ({"carrier": [("workplaces", "biz_nothing_of_the_kind")]}, "a business id nothing names"),
            ({"carrier": [("works_at", "not_the_premises")]}, "a premises the household does not hold")):
        broken = dict(ADJUDICATION[probe]); broken.update(mutation)
        _, mutated_faults = carriers_for(probe, broken, index)
        if not mutated_faults:
            failures.append(f"a carrier naming {why} passed")

    # 7. The register's own note floor. The ledger refuses a ruling whose note is under 20
    #    characters, and a note that cannot say why THIS unit fell under the rule is the
    #    thing the floor is for.
    for row in document["rows"]:
        if len(row["note"].strip()) < 120:
            failures.append(f"{row['unit']}: the note says too little to be checked against the card")

    # 8. Every rule this pass writes states itself, and the one that hands on names a ticket.
    for name, rule in RULES.items():
        if name not in OUTCOMES:
            failures.append(f"RULES states {name!r}, which is not an outcome")
        if len(str(rule.get("statement") or "").strip()) < 40:
            failures.append(f"{name}: states no rule")
        if (rule["disposition"] == "unresolved") != bool(rule.get("ticket")):
            failures.append(f"{name}: an unresolved rule names a ticket and no other rule may")
    for outcome in OUTCOMES:
        if outcome not in RULES:
            failures.append(f"{outcome} is an outcome no rule states")

    # 9. THE TWO TABLES COVER EACH OTHER. `tools/spend_remainder_rulings.py` routes an
    #    enrichment to this pass by key, and a key in one table and not the other is how a
    #    unit would fall through the floor between them.
    from spend_remainder_rulings import ENRICHMENT_ROUTE, TRADE
    routed = {key for key, (rule, _) in ENRICHMENT_ROUTE.items() if rule == TRADE}
    for missing in sorted(routed - set(ADJUDICATION)):
        failures.append(f"{missing} is routed here and this pass has not adjudicated it")
    for stale in sorted(set(ADJUDICATION) - routed):
        failures.append(f"{stale} is adjudicated here and nothing routes it to this pass")

    for failure in failures:
        print("   FAIL: " + failure)
    if failures:
        return 1
    print(f"OK: {len(ADJUDICATION)} trade and premises units, six outcomes, every carrier shown")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true", dest="self_test")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.write:
        return write()
    if args.check:
        return check()
    return describe()


if __name__ == "__main__":
    sys.exit(main())
