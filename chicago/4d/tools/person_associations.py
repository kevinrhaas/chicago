#!/usr/bin/env python3
"""The OTHER places a person was — civic seat, church, agency, land, school (T-1405).

    python3 tools/person_associations.py             the table and every refusal, on stdout
    python3 tools/person_associations.py --write     write the rows onto the person records
                                                     and data/research/residents/person_associations.json
    python3 tools/person_associations.py --check     re-derive both and refuse a drift
    python3 tools/person_associations.py --self-test the assertions of --check, broken on purpose

WHAT THIS IS FOR.

T-1147 clause 7 widened a person's place from one roof to a LIST of dated,
tiered relationships, and `tools/associations.py` gave that list its shape and
its gate. What it did not do is fill it: four records carried rows and 2,265 did
not, because every row was hand-authored from a reading. This module fills it
from the four committed bodies of evidence that already say where people OTHER
THAN AT HOME were — and it fills it only that far.

  * the CIVIC SEAT of an office a man held      `roles[].kind == "office"`
  * the CHURCH a register names him at          `church_evidence[]`
  * an AGENCY he held                           `data/reconstruction/1835_agencies.json`
  * the GROUND he bought                        `data/research/land_sales/resident_crosswalk.json`
                                                `data/reconstruction/1835_land_sales_by_tract.json`
  * the SCHOOL he taught in                     `roles[].role == "schoolteacher"`

THE REFUSALS ARE THE FINDING, and they are counted beside the rows rather than
dropped. An office is not a seat: `civic_public_buildings_1835.md` § 4 is a
whole section on the public functions of Chicago that had no building of their
own, and three quarters of the offices this layer holds are in it. A relationship
with no place is not a row — `associations.py` says so in its own docstring — so
an office whose seat no source reached produces a REFUSAL with the sentence that
refused it, and never a row at a guessed address. The two numbers that matter
are therefore `rows` and `refusals`, and the second is the larger.

THE SEAT TABLE IS A READING AND IT IS WRITTEN DOWN. `CIVIC_SEATS` below is the
whole of what this module knows about where an office sat; every entry carries
the source that placed it, the rung the source's own words reach, and the note
that is copied onto the row. Nothing is placed by this module that is not in
that table, and adding to the table is a reading, not a refactor.

WHY THE POST OFFICE IS A FACE AND NOT A ROOF. The easy, wrong answer is
`hogan_store`: it held Chicago's first post office and the walkthrough anchors
`first_post_office` there. The store's own record refuses it — "NOT THE POST
OFFICE AT THE SCENE DATE, which is the fact this record exists to get right" —
because Andreas has the office removed about July 1834 to near the corner of
Franklin and South Water, "where it stayed through Hogan's term". So the row
reaches a corner and stops, and the word "near" is the source's own.

A FACE ID IS WRITTEN IN UNDERSCORES BECAUSE THE PEOPLE VIEW READS IT ALOUD.
`residents.js` prints `place_or_structure_id` through `words()`, which is
`replace(/_/g, ' ')` and nothing else — so `south_water_and_franklin_corner`
reaches a visitor as "south water and franklin corner" and any other punctuation
reaches them as punctuation. Every street token in a face id is a committed
corridor in `data/streets/1835.json`, and the self-test holds that.

THE ROWS GO ON PERSONS. The ticket's own scope is a person's other significant
locations, and the household is the wrong record for them: an office, a parish
act and a quarter-section are held by a man and not by a house. It is also what
keeps `singular_drift` out of the way — `lives_at`/`works_at` are household
fields, so a person's list cannot contradict a singular link it does not have.

WHAT IS PRESERVED. A record that already carries `associated_with` keeps every
row it has: this module appends by the (kind, place, from) key `associations.py`
already dedupes on, and reports what it found already held. The four
demonstration records T-1238 wrote by hand are not rewritten by a generator.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
REPORT = DATA / "research" / "residents" / "person_associations.json"

SCENE = dt.date(1835, 7, 1)

# --------------------------------------------------------------------------
# The seat table. Every entry is a reading of a committed source, and the note
# is copied onto the row it makes.

CIVIC_SEATS = {
    "united_states_post_office": {
        "place_or_structure_id": "south_water_and_franklin_corner",
        "resolves_to": "face",
        "tier": "inferred",
        "source_id": "andreas_1884_v1",
        "from": "1834",
        "streets": ("south_water", "franklin"),
        "note": (
            "THE POST OFFICE OF 1835 IS A CORNER AND NOT A ROOF. "
            "`civic_public_buildings_1835.md` § 4 has the mail taken at a store and no "
            "post office building in the town; `data/structures/hogan_store.json` — the "
            "obvious wrong answer, and the building the walkthrough's `first_post_office` "
            "anchor stands at — states the limit itself: 'NOT THE POST OFFICE AT THE SCENE "
            "DATE ... Andreas has the office removed to near the corner of Franklin and "
            "South Water, where it stayed through Hogan's term.' So the row reaches the "
            "corner of two committed corridors and stops there. The word 'near' is the "
            "source's own and is why this is a face and not a lot, and the date is the "
            "removal's 'about July 1834', kept at the year because 'about' is the "
            "source's word too. The row places the OFFICE; the holder's own tenure is "
            "what his `roles[]` block dates."),
    },
    "united_states_land_office": {
        "place_or_structure_id": "lake_street_east_side_clark_to_dearborn",
        "resolves_to": "face",
        "tier": "inferred",
        "source_id": "andreas_1884_v1",
        "from": "1835-05",
        "streets": ("lake", "clark", "dearborn"),
        "note": (
            "THE MOST CONSPICUOUS PUBLIC FUNCTION IN THE TOWN THAT SUMMER, AND NEVER A "
            "PUBLIC BUILDING. `civic_public_buildings_1835.md` § 4 quotes Andreas twice "
            "in one paragraph: 'The location of the first United States Land Office in "
            "Chicago was on the east side of Lake Street, between Clark and Dearborn "
            "streets', and 'the office of the Registers and Receivers were usually at "
            "their private offices'. The first sentence is a block face and the second is "
            "why the row may not go past one. `us_land_office_1835` is in "
            "data/exclusions.json for the same reason. The date is the opening the "
            "chronology gives — 'May' 1835, 'Opening of Government Land-Office at "
            "Chicago' — so the SEAT is dated by the office and not by the officer, whose "
            "own span may begin before the office existed."),
    },
}

# The offices this layer holds whose seat no source reached, with the sentence
# that refused them. An office in this table is a REFUSAL and never a row.
CIVIC_NO_SEAT = {
    "cook_county": (
        "THE COUNTY HAD NO BUILDING ON THE SCENE DATE. "
        "`civic_public_buildings_1835.md` § 4: 'The county's own offices were private "
        "until late October 1835 ... Before the county building existed, the Recorder, "
        "the Clerk of the Circuit Court, the Judge of Probate and the notary were one man "
        "working out of an office of his own.' § 3 dates the court-house out of the scene "
        "and § 1 leaves the log jail as the only county roof on the square, which is not "
        "an office. No source reached names the private room, so there is no place and "
        "therefore no row."),
    "cook_county_regiment": (
        "A MILITIA COMMISSION IS NOT A PLACE. Nothing reached seats the Cook County "
        "regiment in a building, and the dataset holds none for it."),
    "cook_county_circuit_court": (
        "THE COURT-HOUSE IS DATED OUT OF THE SCENE. `civic_public_buildings_1835.md` § 3 "
        "is a whole section on it, and § 4 has the Clerk of the Circuit Court working out "
        "of a private office until late October 1835."),
    "town_of_chicago": (
        "THE TOWN HAD NO HALL. `chicago_town_hall` is one of the three guards "
        "`civic_public_buildings_1835.md` § 4 added to data/exclusions.json precisely so "
        "that the next parcel would not build one. A town trustee met where he met; no "
        "source reached says where."),
    "city_of_chicago": (
        "THE CITY IS LATER THAN THE SCENE. Chicago was incorporated as a city in 1837 and "
        "every role in this layer carrying this body is read off the 1839 or 1840 "
        "directory, so the relationship had not started on 1835-07-01 — which is the one "
        "thing `associations.py` will not let a row say."),
    "state_of_illinois": (
        "A STATE COMMISSION IS NOT A PLACE IN THIS TOWN, and nothing reached seats one "
        "here."),
    "united_states_army": (
        "THE GARRISON IS A SEPARATE PROGRAMME. The fort's buildings are dealt by the "
        "garrison work and not by an office's seat; nothing reached puts a named officer "
        "in a named building as the seat of an OFFICE rather than as his quarters."),
    "united_states_treasury": (
        "THE LIGHTHOUSE KEEPER'S OFFICE IS DATED OUT OF THE SCENE. The dataset holds "
        "`chicago_lighthouse_1832` and would seat a keeper in it gladly, but the only "
        "keeper role in this layer is read off the 1843 directory and dated 1843, eight "
        "years after the scene date."),
    "united_states_war_department": (
        "A DEPARTMENT COMMISSION IS NOT A PLACE, and nothing reached seats one here."),
    "united_states_indian_department": (
        "THE COUNCIL HOUSE IS A COUNCIL HOUSE AND NOT AN OFFICE, and this is the one "
        "refusal in this table that had to be argued rather than found. It is the only "
        "Indian-department roof the dataset holds, which is exactly what makes the "
        "inference tempting; `data/structures/council_house.json` refuses it in its own "
        "words — 'Both sources name the building by its function and neither describes "
        "what happened inside it in a way this record repeats' — and the record is "
        "`review_required` under AGENTS.md's standing constraint on the removal. Seating "
        "an agent's office inside it would put a man to work in a building whose record "
        "declines to say what happened in it. T-1204 is the ticket that builds the Agency "
        "establishment; a seat waits for it."),
    "not_stated": (
        "THE ROLE NAMES NO BODY, so there is nothing to look a seat up by. The press "
        "printed the office against the man and not the room."),
}

# An office names its body unambiguously even when the role block does not.
# `employer_or_body` is 'not_stated' on a third of these rows because the press
# printed the office against the man and not the department — but a postmaster is
# the post office's and a land office register is the land office's, and reading
# the body off the office's own name is a lookup and not an inference. Without
# this, James Whitlock — the Register the civic paper NAMES — falls into the
# 'names no body' refusal while his Receiver is seated.
OFFICE_BODY = {
    "postmaster": "united_states_post_office",
    "land_office_register": "united_states_land_office",
    "land_office_receiver": "united_states_land_office",
    "sheriff": "cook_county",
    "county_clerk": "cook_county",
    "justice_of_the_peace": "cook_county",
    "public_administrator": "cook_county",
    "town_president": "town_of_chicago",
    "town_clerk": "town_of_chicago",
    "fire_warden": "town_of_chicago",
    "indian_agent": "united_states_indian_department",
    "sub_agent": "united_states_indian_department",
    "militia_officer": "cook_county_regiment",
    "lighthouse_keeper": "united_states_treasury",
}

# The schools a teacher can be seated in, and the reading that seats him.
SCHOOL_SEATS = {
    "watkins_john": {
        "place_or_structure_id": "north_side_school_1833",
        "resolves_to": "structure",
        "tier": "attested",
        "source_id": "andreas_1884_v1",
        "from": "1835",
        "to": None,
        "note": (
            "THE 1835 USE IS ATTESTED, AND IT IS THE ONLY TEACHING IN THIS LAYER THAT IS. "
            "`data/structures/north_side_school_1833.json` carries Andreas at full text: "
            "'John Watkins was THEN teaching what had become a public school on the North "
            "Side, on the river bank just east of Clark Street, in the building erected by "
            "Colonels Hamilton and Owen.' THE GRAIN IS THE YEAR AND NOT THE DAY — Andreas "
            "adds his own limit, 'Mr. Watkins taught as late as 1835, but the exact date "
            "of his retirement is not known' — so `from` is 1835 and `to` is null rather "
            "than the scene date. HIS EARLIER SCHOOL IS NOT WRITTEN AS A SECOND ROW: "
            "`watkins_school_house` and this record both carry 'the Watkins school-house' "
            "among their aka, and until that overlap is ruled on, one man taught in two "
            "records and only one of them is attested for the year of the scene."),
    },
}

# --------------------------------------------------------------------------


def load_households() -> list:
    return [(p, json.loads(p.read_text())) for p in sorted(HOUSEHOLDS.glob("*.json"))]


def starts_by_scene(value) -> bool:
    """True when a `from` value this module would write is on or before the scene."""
    from associations import read_bounds
    b = read_bounds(value)
    return bool(b) and b[0] <= SCENE


def street_ids() -> set:
    f = DATA / "streets" / "1835.json"
    if not f.exists():
        return set()
    return {s.get("id") for s in (json.loads(f.read_text()).get("streets") or [])}


def tract_ids() -> set:
    f = DATA / "reconstruction" / "1835_survey_tracts.json"
    if not f.exists():
        return set()
    return {t.get("id") for t in (json.loads(f.read_text()).get("tracts") or [])}


def row(kind, place, rung, frm, to, tier, source_id, note, undated=False) -> dict:
    r = {"kind": kind, "place_or_structure_id": place, "resolves_to": rung,
         "from": frm, "to": to, "tier": tier, "source_id": source_id, "note": note}
    if undated:
        r["undated"] = True
    return r


def key(r) -> tuple:
    return (r.get("kind"), r.get("place_or_structure_id"), str(r.get("from")))


# --------------------------------------------------------------------------
# The five derivations. Each returns (rows_by_person_id, refusals).

def derive_civic(households) -> tuple:
    out, refusals = {}, []
    for _p, h in households:
        for person in h.get("persons") or []:
            for role in person.get("roles") or []:
                if role.get("kind") != "office":
                    continue
                body = role.get("employer_or_body") or "not_stated"
                if body == "not_stated":
                    body = OFFICE_BODY.get(role.get("role"), "not_stated")
                # THE MAN'S OWN TENURE GATES THE SEAT, not just the seat's date.
                # A register of the 1844 land office was not at the 1835 one, and
                # the seat table would happily place him there.
                if not (role.get("covers_scene_date") or starts_by_scene(role.get("from"))):
                    refusals.append({
                        "kind": "civic_seat", "person_id": person.get("id"),
                        "household_id": h.get("id"), "office": role.get("role"),
                        "body": body,
                        "why": (f"The role itself is dated {role.get('from')} to "
                                f"{role.get('to')} and does not reach the scene date, so "
                                f"there is no office in this scene to seat. A seat table "
                                f"keyed on the office alone would place a man at the "
                                f"1835 land office on the strength of an 1844 directory."),
                    })
                    continue
                seat = CIVIC_SEATS.get(body)
                if not seat:
                    refusals.append({
                        "kind": "civic_seat", "person_id": person.get("id"),
                        "household_id": h.get("id"), "office": role.get("role"),
                        "body": body,
                        "why": CIVIC_NO_SEAT.get(body, (
                            f"No seat is read for '{body}', and this module places nothing "
                            f"that is not in its own seat table.")),
                    })
                    continue
                frm = seat["from"]
                if not starts_by_scene(frm):
                    refusals.append({
                        "kind": "civic_seat", "person_id": person.get("id"),
                        "household_id": h.get("id"), "office": role.get("role"),
                        "body": body,
                        "why": f"The seat is dated {frm}, after the scene date.",
                    })
                    continue
                note = (seat["note"] + " THE OFFICE HERE IS " +
                        str(role.get("role") or "unnamed in the role block").upper() +
                        f", carried on this person's roles[] block from "
                        f"{role.get('from')} to {role.get('to')} at "
                        f"{role.get('confidence')} confidence; this row states where that "
                        f"office SAT and inherits neither its dates nor its tier.")
                out.setdefault(person["id"], []).append(
                    row("civic_seat", seat["place_or_structure_id"], seat["resolves_to"],
                        frm, None, seat["tier"], seat["source_id"], note))
    return out, refusals


def derive_church(households) -> tuple:
    out, refusals = {}, []
    for _p, h in households:
        for person in h.get("persons") or []:
            for ev in person.get("church_evidence") or []:
                when = ev.get("describes_date")
                src = ev.get("source")
                if src != "st_cyr_register_ichr_v4":
                    refusals.append({
                        "kind": "church", "person_id": person.get("id"),
                        "household_id": h.get("id"), "record_id": ev.get("record_id"),
                        "why": (f"The source '{src}' is not the one register this module "
                                f"can place. A church row needs a building, and St. Mary's "
                                f"is the only congregation in this dataset whose register "
                                f"has been read."),
                    })
                    continue
                if not starts_by_scene(when):
                    refusals.append({
                        "kind": "church", "person_id": person.get("id"),
                        "household_id": h.get("id"), "record_id": ev.get("record_id"),
                        "why": (f"The register dates this act {when}, after the scene date "
                                f"of {SCENE.isoformat()}. A relationship that had not "
                                f"started is not in this scene, and an earlier date may "
                                f"not be borrowed for it: a man buried by the parish in "
                                f"July was very likely of it in June, and 'very likely' is "
                                f"not a date."),
                    })
                    continue
                note = (
                    "THE REGISTER NAMES HIM AT A PARISH ACT, AND THAT IS THE WHOLE OF THE "
                    f"CLAIM. Father St. Cyr's register carries this person as "
                    f"{ev.get('locator')} in {ev.get('record_id')}, dated "
                    f"{when} and tied to this card by the church crosswalk's rule "
                    f"{ev.get('rule')}. `st_marys_church` is his church, which the "
                    f"structure record states — 'St. Cyr selected the lot in 1833 and ... "
                    f"was succeeded by Father O'Meara only after 1837, so he is the pastor "
                    f"across the whole scene window'. THIS IS NOT A MEMBERSHIP ROW: being "
                    f"a witness, a party or a decedent at a Catholic act is what the "
                    f"register states, and the dates are the act's own, which is why "
                    f"`from` and `to` are the same day and the row is not carried forward "
                    f"to the scene date.")
                out.setdefault(person["id"], []).append(
                    row("church", "st_marys_church", "structure", when, when,
                        "attested", "st_cyr_register_ichr_v4", note))
    return out, refusals


def derive_agency(households) -> tuple:
    out, refusals = {}, []
    f = DATA / "reconstruction" / "1835_agencies.json"
    if not f.exists():
        return out, refusals
    doc = json.loads(f.read_text())
    hh = {h.get("id"): h for _p, h in households}
    for agency in doc.get("agencies") or []:
        for holding in agency.get("holdings") or []:
            if holding.get("holder_kind") != "person":
                refusals.append({
                    "kind": "agency_held", "holder": holding.get("holder"),
                    "holder_id": holding.get("holder_id"),
                    "why": ("The holder is a firm and not a person; a business's agency "
                            "belongs on the business layer, which "
                            "data/reconstruction/1835_agencies.json already carries it "
                            "to."),
                })
                continue
            if not holding.get("structure_id"):
                refusals.append({
                    "kind": "agency_held", "holder": holding.get("holder"),
                    "holder_id": holding.get("holder_id"),
                    "household_id": holding.get("household_id"),
                    "why": ("THE HOLDING NAMES NO PREMISES, AND THE AGENCY FILE REFUSES "
                            "THE OBVIOUS SUBSTITUTE IN ITS OWN WORDS. Its caveat reads "
                            "'A holding is a relation and nothing more. Nothing here says "
                            "this holder dealt in the principal's line, kept a roof for "
                            "it, or was a partner in any house that signed for it', and "
                            "the firm holding's note says what the relation gains a card: "
                            "'a line on its card and nothing else — no trade, no street, "
                            "no roof'. Seating the agency at the man's own house or his "
                            "old firm's roof would be exactly the claim those two "
                            "sentences refuse. `associated_with[]` is defined over claims "
                            "with a place; this claim has none, so it has no row. It is "
                            "not lost: the agency file carries it, and the town card "
                            "prints it."),
                })
                continue
            household = hh.get(holding.get("household_id"))
            person_id = None
            if household:
                for person in household.get("persons") or []:
                    if person.get("id") == (holding.get("holder_id") or "").removeprefix("person_"):
                        person_id = person["id"]
            if not person_id:
                refusals.append({
                    "kind": "agency_held", "holder": holding.get("holder"),
                    "holder_id": holding.get("holder_id"),
                    "why": "The holding's person does not resolve in the resident layer.",
                })
                continue
            note = ("The agency file seats this holding at a committed roof; the dates are "
                    "the first and last PRINTING of the holder's notice, which is what "
                    "that file says they are and not the term of the appointment.")
            out.setdefault(person_id, []).append(
                row("agency_held", holding["structure_id"], "structure",
                    holding.get("first_issue"), holding.get("last_issue"),
                    "attested", "chicago_democrat_1833_1835", note))
    return out, refusals


def derive_land(households) -> tuple:
    out, refusals = {}, []
    cw = json.loads((DATA / "research" / "land_sales" / "resident_crosswalk.json").read_text())
    bt = json.loads((DATA / "reconstruction" / "1835_land_sales_by_tract.json").read_text())
    by_record = {r["record_id"]: r for r in bt.get("sorted") or []}
    persons = {}
    for _p, h in households:
        for person in h.get("persons") or []:
            persons[person["id"]] = h.get("id")

    unsorted_rows = 0
    for match in cw.get("matches") or []:
        ruling = (match.get("ruling") or {}).get("ruling")
        if ruling != "upheld":
            refusals.append({
                "kind": "land_purchased", "person_id": match.get("resident_id"),
                "purchaser_as_read": match.get("purchaser_as_read"),
                "why": (f"The crosswalk's match is {ruling or 'unruled'}, and that file "
                        f"says of itself: 'PROPOSALS, not identities. Nothing here mints a "
                        f"resident'. Only an ADJUDICATED match may reach a card."),
            })
            continue
        if match.get("resident_id") not in persons:
            refusals.append({
                "kind": "land_purchased", "person_id": match.get("resident_id"),
                "purchaser_as_read": match.get("purchaser_as_read"),
                "why": "The upheld match names a resident id no person record carries.",
            })
            continue
        by_tract: dict = {}
        for rid in match.get("record_ids") or []:
            reg = by_record.get(rid)
            if reg is None:
                unsorted_rows += 1
                continue
            if reg.get("void") or not reg.get("on_or_before_scene_date"):
                continue
            by_tract.setdefault(reg["tract"], []).append(reg)
        if not by_tract:
            refusals.append({
                "kind": "land_purchased", "person_id": match.get("resident_id"),
                "purchaser_as_read": match.get("purchaser_as_read"),
                "why": ("No register row of this purchaser is both sorted onto a tract and "
                        "dated on or before the scene date. The tract sort's own "
                        "`refusals` block says which rows it would not place — town plat "
                        "lots, ground outside the modelled extent, descriptions not read, "
                        "and rows with neither a ring nor a citation."),
            })
            continue
        for tract, regs in sorted(by_tract.items()):
            dates = sorted(r.get("date_purchased") for r in regs if r.get("date_purchased"))
            acres = round(math.fsum((r.get("parcel_acres") or 0)
                                    * (r.get("share_of_the_parcel") or 0)
                                    for r in regs), 2)
            ids = ", ".join(sorted(r["record_id"] for r in regs))
            note = (
                f"GROUND HE BOUGHT, WHICH IS NOT GROUND HE STOOD ON — the rung is `tract` "
                f"for that reason, and `land_purchased` is in neither the home kinds nor "
                f"the work kinds because a holding is not a place a man was. The federal "
                f"tract-sale register carries {len(regs)} row(s) — {ids} — to this "
                f"purchaser, read as '{match.get('purchaser_as_read')}', sorted onto "
                f"{tract} by tools/sort_land_sales_onto_tracts.py and covering about "
                f"{acres} acre(s) of it. THE TIER IS INFERRED AND THE TWO HALVES DIFFER: "
                f"the purchase is documented — the register is a public record and states "
                f"it — while the tie between that purchaser and THIS card is an identity "
                f"ruling, upheld under "
                f"{(match.get('ruling') or {}).get('ticket')} on "
                f"{(match.get('ruling') or {}).get('ruled_on')} by the rule "
                f"'{match.get('rule')}'. The weaker half sets the tier. `to` is null "
                f"because the register records a sale and not a tenure.")
            out.setdefault(match["resident_id"], []).append(
                row("land_purchased", tract, "tract", dates[0] if dates else None, None,
                    "inferred", "isa_public_domain_land_tract_sales", note,
                    undated=not dates))
    if unsorted_rows:
        refusals.append({
            "kind": "land_purchased", "person_id": None,
            "why": (f"{unsorted_rows} register row(s) of upheld purchasers are not in the "
                    f"tract sort's `sorted` list at all, so this module has no ground to "
                    f"name for them. The reasons are that file's own: "
                    f"`refusals.town_plat_lots`, `refusals.outside_the_modelled_ground`, "
                    f"`refusals.description_not_read` and "
                    f"`refusals.no_ring_and_no_citation`."),
        })
    return out, refusals


def derive_school(households) -> tuple:
    out, refusals = {}, []
    for _p, h in households:
        for person in h.get("persons") or []:
            teaches = [r for r in (person.get("roles") or [])
                       if r.get("role") == "schoolteacher"]
            if not teaches:
                continue
            seat = SCHOOL_SEATS.get(person["id"])
            if not seat:
                refusals.append({
                    "kind": "school", "person_id": person.get("id"),
                    "household_id": h.get("id"),
                    "why": ("The press and the directories print the trade against the "
                            "name and not the room. No source reached names a building "
                            "this teacher taught in, and the dataset's three school "
                            "records name a teacher between them only where the seat "
                            "table already says so."),
                })
                continue
            out.setdefault(person["id"], []).append(
                row("school", seat["place_or_structure_id"], seat["resolves_to"],
                    seat["from"], seat.get("to"), seat["tier"], seat["source_id"],
                    seat["note"]))
    return out, refusals


DERIVATIONS = (("civic_seat", derive_civic), ("church", derive_church),
               ("agency_held", derive_agency), ("land_purchased", derive_land),
               ("school", derive_school))


def derive() -> tuple:
    """(proposal by person id, refusals, already-held)."""
    households = load_households()
    held = {}
    for _p, h in households:
        for person in h.get("persons") or []:
            if "associated_with" in person:
                held[person["id"]] = {key(r) for r in person["associated_with"] or []}

    proposal: dict = {}
    refusals: list = []
    already: list = []
    for _name, fn in DERIVATIONS:
        rows, refused = fn(households)
        refusals.extend(refused)
        for pid, rs in rows.items():
            for r in rs:
                if key(r) in held.get(pid, set()):
                    already.append({"person_id": pid, "key": list(key(r))})
                    continue
                if any(key(r) == key(x) for x in proposal.get(pid, [])):
                    continue
                proposal.setdefault(pid, []).append(r)
    return proposal, refusals, already


def counts(proposal, refusals, already) -> dict:
    by_kind: dict = {}
    for rs in proposal.values():
        for r in rs:
            by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
    ref_by_kind: dict = {}
    for r in refusals:
        ref_by_kind[r["kind"]] = ref_by_kind.get(r["kind"], 0) + 1
    return {
        "persons_gaining_rows": len(proposal),
        "rows_proposed": sum(len(v) for v in proposal.values()),
        "rows_by_kind": dict(sorted(by_kind.items())),
        "refusals": len(refusals),
        "refusals_by_kind": dict(sorted(ref_by_kind.items())),
        "rows_already_held": len(already),
    }


def before_after() -> dict:
    """The coverage file's own numbers, before this pass and after it."""
    from associations import derive as coverage_derive
    return coverage_derive()


def payload(proposal, refusals, already) -> dict:
    return {
        "schema": "person_associations/1",
        "generated_by": "tools/person_associations.py",
        "_doc": ("T-1405. The civic seats, parish acts, agencies, purchased ground and "
                 "schools this layer can place on a PERSON, and — the larger half — every "
                 "one it refuses to place, with the sentence that refused it. DERIVED: "
                 "rebuild with --write, and --check refuses a hand-edit or a drift between "
                 "this file and the rows on the cards."),
        "scene_date": SCENE.isoformat(),
        "sources_read": [
            "data/residents/households/*.json (roles[], church_evidence[])",
            "data/reconstruction/1835_agencies.json",
            "data/research/land_sales/resident_crosswalk.json",
            "data/reconstruction/1835_land_sales_by_tract.json",
            "docs/RESEARCH/civic_public_buildings_1835.md (the seat table's reading)",
        ],
        "counts": counts(proposal, refusals, already),
        "rows_by_person": {pid: rs for pid, rs in sorted(proposal.items())},
        "rows_already_held": already,
        "refusals": refusals,
    }


def render(p: dict) -> str:
    c = p["counts"]
    out = [f"person associations: {c['rows_proposed']} row(s) on "
           f"{c['persons_gaining_rows']} person(s), {c['refusals']} refusal(s), "
           f"{c['rows_already_held']} already held"]
    for k, v in c["rows_by_kind"].items():
        out.append(f"  row      {k:18} {v}")
    for k, v in c["refusals_by_kind"].items():
        out.append(f"  refused  {k:18} {v}")
    return "\n".join(out)


# --------------------------------------------------------------------------

# The tail `reconstruct_sex_age.settle_order` owns, in the order it writes it.
# Those blocks are moved to the END of a person by TWO passes that re-derive this
# layer, and both prove themselves by rebuilding a card and comparing it byte for
# byte. A new key appended after them reads as drift on an ordering alone — which
# is exactly what happened the first time these rows were written, on 70 cards.
SETTLED_TAIL = ("age_band", "sex", "sex_basis", "birth_year")


def place_rows(person: dict, rows: list) -> None:
    """Write `associated_with` IN FRONT OF the tail the sex/age passes re-order.

    `reconstruct_sex_age.settle_order` pops `age_band`, then a sex it inferred,
    then a birth year it drew, so each lands at the end of the person; its
    `--check` strips this pass's blocks, derives them again and compares the
    JSON text. Appending anything after that tail makes the committed card and
    the derived one differ by position and by nothing else.

    THE TAIL'S OWN ORDER IS LEFT EXACTLY AS IT LIES. Which of those four keys
    that pass moves depends on the card — a sex it did not infer and a birth
    year it did not draw stay where they were — so re-emitting them in a fixed
    order is its own drift, on 44 cards. This inserts in front of the first of
    them and touches nothing else.
    """
    out = {}
    placed = False
    for k, v in list(person.items()):
        if not placed and k in SETTLED_TAIL:
            out["associated_with"] = rows
            placed = True
        if k != "associated_with":
            out[k] = v
    if not placed:
        out["associated_with"] = rows
    person.clear()
    person.update(out)


def apply_to_cards(proposal) -> int:
    """Append the proposed rows to the person records. Returns files written."""
    written = 0
    for path, h in load_households():
        changed = False
        for person in h.get("persons") or []:
            rows = proposal.get(person.get("id"))
            if not rows:
                continue
            existing = person.get("associated_with") or []
            have = {key(r) for r in existing}
            add = [r for r in rows if key(r) not in have]
            if not add:
                continue
            place_rows(person, existing + add)
            changed = True
        if changed:
            path.write_text(json.dumps(h, indent=1, ensure_ascii=False) + "\n")
            written += 1
    return written


def cards_match(proposal) -> list:
    """Every proposed row that is not on its card. The drift check."""
    missing = []
    on_card: dict = {}
    for _p, h in load_households():
        for person in h.get("persons") or []:
            if "associated_with" in person:
                on_card[person["id"]] = {key(r) for r in person["associated_with"] or []}
    for pid, rows in proposal.items():
        for r in rows:
            if key(r) not in on_card.get(pid, set()):
                missing.append(f"{pid}: {key(r)}")
    return missing


def main(argv) -> int:
    if "--self-test" in argv:
        return self_test()
    proposal, refusals, already = derive()
    p = payload(proposal, refusals, already)
    if "--write" in argv:
        n = apply_to_cards(proposal)
        # re-derive against the written cards: what was proposed is now held.
        proposal2, refusals2, already2 = derive()
        p = payload(proposal2, refusals2, already2)
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(p, indent=2) + "\n")
        print(f"wrote {n} household file(s) and {REPORT.relative_to(ROOT)}")
        print(render(p))
        return 0
    if "--check" in argv:
        if not REPORT.exists():
            print(f"FAIL {REPORT.relative_to(ROOT)} is missing", file=sys.stderr)
            return 1
        committed = json.loads(REPORT.read_text())
        bad = [k for k in ("counts", "rows_by_person", "refusals")
               if committed.get(k) != p[k]]
        if bad:
            print(f"FAIL {REPORT.relative_to(ROOT)} does not re-derive: {bad} differ. "
                  f"Rebuild with --write; the file is derived and a hand-edit loses.",
                  file=sys.stderr)
            return 1
        missing = cards_match(proposal)
        if missing:
            print(f"FAIL {len(missing)} derived row(s) are not on their cards — a writer "
                  f"has dropped them. First: {missing[0]}", file=sys.stderr)
            return 1
        print(f"ok  {render(p)}")
        return 0
    print(render(p))
    if "--refusals" in argv:
        for r in refusals:
            print(f"  - {r['kind']:16} {r.get('person_id') or r.get('holder_id') or '-'}: "
                  f"{r['why'][:110]}")
    return 0


def self_test() -> int:
    """Break the assertions --check stands on; a gate that cannot fail is not a gate."""
    failed = 0
    streets = street_ids()
    tracts = tract_ids()

    for body, seat in CIVIC_SEATS.items():
        for s in seat.get("streets") or ():
            ok = s in streets and s in seat["place_or_structure_id"]
            print(("ok   " if ok else "FAIL ") +
                  f"the {body} seat names the committed corridor '{s}'")
            failed += 0 if ok else 1
        ok = starts_by_scene(seat["from"])
        print(("ok   " if ok else "FAIL ") + f"the {body} seat starts by the scene date")
        failed += 0 if ok else 1

    bodies = set()
    for _p, h in load_households():
        for person in h.get("persons") or []:
            for role in person.get("roles") or []:
                if role.get("kind") == "office":
                    b = role.get("employer_or_body") or "not_stated"
                    if b == "not_stated":
                        b = OFFICE_BODY.get(role.get("role"), "not_stated")
                    bodies.add(b)
    unnamed = sorted(bodies - set(CIVIC_SEATS) - set(CIVIC_NO_SEAT))
    ok = not unnamed
    print(("ok   " if ok else "FAIL ") +
          "every body an office in this layer names is either seated or refused by name" +
          ("" if ok else f" -> {unnamed}"))
    failed += 0 if ok else 1

    proposal, refusals, _already = derive()
    ok = bool(refusals)
    print(("ok   " if ok else "FAIL ") + "the refusals are not empty — they are the finding")
    failed += 0 if ok else 1

    bad = [(pid, r) for pid, rs in proposal.items() for r in rs
           if r["resolves_to"] == "tract" and r["place_or_structure_id"] not in tracts]
    ok = not bad
    print(("ok   " if ok else "FAIL ") + "every tract row names a surveyed tract")
    failed += 0 if ok else 1

    bad = [(pid, r) for pid, rs in proposal.items() for r in rs
           if not starts_by_scene(r["from"]) and not r.get("undated")]
    ok = not bad
    print(("ok   " if ok else "FAIL ") + "no row begins after the scene date" +
          ("" if ok else f" -> {bad[0][0]}"))
    failed += 0 if ok else 1

    bad = [(pid, r) for pid, rs in proposal.items() for r in rs
           if len(str(r["note"])) < 80]
    ok = not bad
    print(("ok   " if ok else "FAIL ") + "every row carries the reasoning that made it")
    failed += 0 if ok else 1

    bad = [r for r in refusals if len(str(r.get("why") or "")) < 40]
    ok = not bad
    print(("ok   " if ok else "FAIL ") + "every refusal carries the sentence that refused it")
    failed += 0 if ok else 1

    print(f"{failed} failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main(sys.argv[1:]))
