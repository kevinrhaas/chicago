#!/usr/bin/env python3
"""THE 1835 LODGING MODEL: a capacity for every lodging place the town holds.

T-1370, the first piece of T-1175. The town model (T-1293) says how many beds
this town needed IN TOTAL and says, in as many words, that it "seats nobody in
any lodging place and gives no boarding house a capacity of its own". T-1175
cannot seat a boarder without that number, and the ticket that was to have
written it -- T-1164 -- was withdrawn on 2026-09-17 as "folded into T-1293". The
fold lost the per-place half. This tool is that half.

    tools/build_lodging_model_1835.py --build       write the model and its report
    tools/build_lodging_model_1835.py --check       re-derive both and refuse drift
    tools/build_lodging_model_1835.py --self-test   the guards, fired on fixtures

WHAT THIS TOOL IS. An ADJUDICATION over files this repository already holds and
already gates, exactly as the order book is. It reads no page of any source,
opens no network, names nobody, ages nobody, and creates no person, household,
business or building. It puts a NUMBER OF BEDS on buildings that already stand
in the dataset, and every quantity is a function of a committed file named
beside it.

WHICH BUILDINGS ARE LODGING PLACES, AND WHY IT IS READ RATHER THAN DECIDED.
Every structure record carries a top-level `function`, and this tool classifies
on that field alone: `boarding_house` and its small/medium/large variants are
the boarding-house class, `tavern_inn`, `hotel` and `small_inn_or_tavern` the
inn class. Nothing here reads a building's NAME, and nothing reads the roof
programme's family code -- see THE GROUP LABEL DISAGREES WITH THE RECORDS below,
which is the reason that distinction is load-bearing rather than fussy.

THE CAPACITY RULE, AND THE ONE THING IT IS CAREFUL NOT TO DO. The town model
already fixes the per-place figures, and they are the 1840 household tail read
off this project's own committed extract of the census: the ordinary end puts a
lodging place at p90 (9 people), the crowded end puts a boarding house at p99
(21) and an inn at the largest household the enumerator actually recorded (35).
Those are the model's numbers and this tool does not move them. What it adds is
WHICH HOUSE IS BIGGER THAN WHICH, from the one dimension the records carry --
enclosed floor area, footprint times storeys -- by apportioning each class's own
total (n places x the model's figure) across its places in proportion to that
area, by largest remainder. So the MEAN capacity of each class is the town
model's figure exactly, by construction, and the model makes no new claim about
the town at all: it redistributes a figure the town model already owns.

THE CLAMP. No place is given more beds than the largest household the 1840
census recorded in Chicago (35). A proportional share can ask for more -- the
Western Hotel is five times the floor area of the smallest tavern here -- and
granting it would be this model inventing a bigger house than the source it
draws from ever saw. The surplus from a clamped place is redistributed across
the places that are not clamped, iterated to a fixed point, and every clamp is
recorded on the row it bound.

THE GROUP LABEL DISAGREES WITH THE RECORDS, AND THE MODEL SAYS SO RATHER THAN
CHOOSING. The roof programme schedules 42 roofs in a group it calls
`larger_boarding_houses`, and the town model's 468-1,232 bed bracket is 42 of
those plus 10 inns. But the group is families H1+H2+H3 (18+14+10), and the
family-archetype crosswalk gives H1 `house_frame_large:center_hall_one_and_half`
and H2 `house_frame_large:merchant_two_story` -- houses, both of them, with the
crosswalk noting of H2 that "merchant/professional is a type label". Only H3 is
`boarding_house_frame`. The roofs already built agree with the crosswalk and not
with the group name: four H1 and two H2 records in the south carry
`function: larger_one_and_a_half_story_house` and `merchant_or_professional_house`.
So 32 of the 42 roofs behind the town's bed bracket are, on the records'
own account, dwellings. This tool will not quietly adopt either reading. It
classifies on `function`, counts the programme both ways, and prints the
disagreement as an open question for the tickets that own the two files.

WHAT THIS MODEL DOES NOT DO. It seats nobody -- T-1371 fills the beds. It
staffs nobody: the bar-keeper, the hostler, the cook and the chambermaid are
priced by the business staffing model, T-1183, which is open, and a staff
establishment invented here would be that ticket's answer written by a tool with
no licence to give it. And it gives no capacity to a building that was not open
on the scene date: the Lake House is `hotel_under_construction` in July 1835 and
is carried as a row with no beds and the reason on it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL_OUT = ROOT / "data" / "reconstruction" / "1835_lodging_model.json"
REPORT = ROOT / "docs" / "RESEARCH" / "1835_lodging_model.md"

SCENE_DATE = "1835-07-01"
TICKET = "T-1370"

#: The record `function` values that make a building a lodging place, and the
#: class each belongs to. READ, never guessed: a record whose function is not
#: here is not a lodging place, however it is named.
LODGING_FUNCTIONS = {
    "boarding_house": "boarding_house",
    "small_boarding_house": "boarding_house",
    "medium_boarding_house": "boarding_house",
    "large_boarding_house": "boarding_house",
    "tavern_inn": "inn_tavern",
    "hotel": "inn_tavern",
    "small_inn_or_tavern": "inn_tavern",
}

#: Lodging that the roof programme does not count and this model therefore does
#: not apportion. Rooms over an office are lodging a visitor can be seated in,
#: and T-1371 is told about them; they are not one of the 42 or the 10.
OUTSIDE_THE_PROGRAMME = {"office_and_lodging"}

#: Not open on 1 July 1835. Carried as a row, with no beds and the reason.
NOT_YET_OPEN = {"hotel_under_construction"}

#: The programme group each class is scheduled under, and the families in it.
PROGRAMME_GROUPS = {
    "boarding_house": ("larger_boarding_houses", ("H1", "H2", "H3")),
    "inn_tavern": ("inns_taverns", ("T1", "T2", "T3")),
}

#: How each class is spoken of in the prose a visitor reads. The article is part
#: of it: "a inn tavern" is the tell of a label being pasted into a sentence.
CLASS_WORDS = {"boarding_house": "a boarding house", "inn_tavern": "an inn or tavern"}

#: Which 1840 household-size figure sets each class's crowded end. The ordinary
#: end is p90 for both -- the town model's own low.
CROWDED_FIGURE = {"boarding_house": "p99", "inn_tavern": "max"}


class Fault(Exception):
    """A refusal. Never a warning: a bed count with a hole in it seats nobody."""


# ------------------------------------------------------------------- inputs --

def load(root: Path = ROOT) -> dict:
    paths = {
        "model": root / "data" / "reconstruction" / "1835_town_model.json",
        "inventory": root / "data" / "reconstruction" / "1835_building_inventory.json",
        "composition": root / "data" / "research" / "census_1840" / "composition_1840.json",
    }
    out = {}
    for key, path in paths.items():
        if not path.exists():
            raise Fault(f"the lodging model's input {path.name} is missing — it cannot be built without it")
        out[key] = json.loads(path.read_text(encoding="utf-8"))
    out["structures"] = read_structures(root / "data" / "structures")
    return out


def read_structures(dirpath: Path) -> list[dict]:
    """Every structure record, in id order, flattened to what this tool reads."""
    if not dirpath.is_dir():
        raise Fault(f"{dirpath} is not a directory — there are no structures to measure")
    out = []
    for path in sorted(dirpath.glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        out.append(rec)
    return out


def figure(model: dict, section_key: str, name: str) -> dict:
    for section in model["sections"]:
        if section["key"] != section_key:
            continue
        for fig in section["figures"]:
            if fig["figure"] == name:
                return fig
    raise Fault(f"the town model carries no figure {name!r} in section {section_key!r}")


def function_of(rec: dict) -> str | None:
    fn = rec.get("function")
    if isinstance(fn, dict):
        fn = fn.get("value")
    return fn if isinstance(fn, str) else None


def scene_phase(rec: dict) -> dict | None:
    """The phase this record shows on the scene date, or the last one it has.

    Structure records are phased and the dataset's own compiler resolves a phase
    against the target date; this tool is measuring a building's size, which is
    the one thing that a phase can change, so it must not read an 1829 log cabin
    and call it the 1835 frame block.
    """
    phases = rec.get("phases") or []
    if not phases:
        return None
    for phase in phases:
        rng = phase.get("documented_range") or {}
        start, end = rng.get("from"), rng.get("to")
        if start and start > SCENE_DATE:
            continue
        if end and end < SCENE_DATE:
            continue
        return phase
    return phases[-1]


def enclosed_area_m2(phase: dict) -> tuple[float, float, float]:
    """Footprint area, storeys, and the enclosed floor area that is their product.

    The footprint polygon is metres in the record's own local frame. Area is the
    shoelace of the polygon rather than its bounding box: an L-plan tavern with a
    service wing is not the rectangle that contains it, and reading it as one
    would hand that building beds it has no floor for.
    """
    poly = (phase.get("footprint") or {}).get("polygon") or []
    if len(poly) < 3:
        raise Fault("a lodging place carries no footprint polygon, so it cannot be measured")
    area = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i][0], poly[i][1]
        x2, y2 = poly[(i + 1) % len(poly)][0], poly[(i + 1) % len(poly)][1]
        area += x1 * y2 - x2 * y1
    area = abs(area) / 2.0
    storeys = ((phase.get("form") or {}).get("stories") or {}).get("value")
    if storeys is None:
        raise Fault("a lodging place carries no storey count, so its floor area cannot be found")
    return round(area, 2), float(storeys), round(area * float(storeys), 2)


def weakest(*confidences: str | None) -> str:
    """The weakest grade among the claims a derived value rests on.

    A capacity read off a reconstructed footprint and a reconstructed storey
    count is reconstructed, whatever the building's name. Upgrading it because
    the building is attested would be the exact misrepresentation AGENTS.md puts
    above the work.
    """
    order = ["reconstructed", "inferred", "documented", "attested"]
    seen = [c for c in confidences if c in order]
    if not seen:
        return "reconstructed"
    return min(seen, key=order.index)


# --------------------------------------------------------------- arithmetic --

def apportion(areas: list[float], total: int, ceiling: int) -> tuple[list[int], list[bool]]:
    """Split `total` across places in proportion to `areas`, by largest remainder.

    Largest remainder rather than plain rounding because the class total is the
    invariant this model rests on: the mean capacity of a class must BE the town
    model's figure for that class, and a column of independently rounded numbers
    does not sum to anything in particular.

    A place is clamped at `ceiling` -- the largest household the 1840 census
    actually recorded -- and the beds it could not take are re-apportioned across
    the places that are not clamped, iterated until the set of clamped places
    stops growing. If every place is clamped the remainder simply cannot be
    placed, and the caller is told rather than having it forced onto somebody.
    """
    n = len(areas)
    if n == 0:
        return [], []
    if any(a <= 0 for a in areas):
        raise Fault("a lodging place measured zero floor area, which no building has")
    clamped = [False] * n
    out = [0] * n
    while True:
        free = [i for i in range(n) if not clamped[i]]
        if not free:
            return out, clamped
        budget = total - sum(out[i] for i in range(n) if clamped[i])
        if budget <= 0:
            for i in free:
                out[i] = 0
            return out, clamped
        pool = sum(areas[i] for i in free)
        exact = {i: budget * areas[i] / pool for i in free}
        got = {i: int(exact[i]) for i in free}
        short = budget - sum(got.values())
        for i in sorted(free, key=lambda j: (-(exact[j] - got[j]), j))[:short]:
            got[i] += 1
        newly = [i for i in free if got[i] > ceiling]
        for i in free:
            out[i] = min(got[i], ceiling)
        if not newly:
            return out, clamped
        for i in newly:
            clamped[i] = True


# -------------------------------------------------------------------- build --

def build(data: dict) -> dict:
    model, comp = data["model"], data["composition"]
    sizes = comp["household_size"]
    ordinary = sizes["percentiles"]["p90"]
    crowded = {
        "boarding_house": sizes["percentiles"][CROWDED_FIGURE["boarding_house"]],
        "inn_tavern": sizes[CROWDED_FIGURE["inn_tavern"]],
    }
    ceiling = sizes["max"]

    targets = data["inventory"]["family_targets"]

    places, outside, closed = [], [], []
    for rec in data["structures"]:
        fn = function_of(rec)
        if fn is None:
            continue
        if fn in NOT_YET_OPEN:
            phase = scene_phase(rec)
            closed.append({
                "id": rec["id"], "name": rec["name"], "function": fn,
                "beds_ordinary": None, "beds_crowded": None,
                "why_no_beds": "The record's own function says this building was still going up on "
                               f"{SCENE_DATE}. A house that was not open held nobody, and giving it a "
                               "capacity would put beds in a building site.",
            })
            continue
        if fn in OUTSIDE_THE_PROGRAMME:
            outside.append({
                "id": rec["id"], "name": rec["name"], "function": fn,
                "beds_ordinary": None, "beds_crowded": None,
                "why_no_beds": "Lodging the roof programme does not schedule and the town model's bed "
                               "bracket does not count. Recorded so T-1371 knows the rooms are here; "
                               "not apportioned, because apportioning it would spend beds the "
                               "programme allotted to a boarding house somewhere else.",
            })
            continue
        cls = LODGING_FUNCTIONS.get(fn)
        if cls is None:
            continue
        phase = scene_phase(rec)
        if phase is None:
            raise Fault(f"{rec['id']} is a lodging place with no phases at all")
        footprint_m2, storeys, enclosed = enclosed_area_m2(phase)
        grade = weakest((phase.get("footprint") or {}).get("confidence"),
                        (((phase.get("form") or {}).get("stories")) or {}).get("confidence"))
        recon = rec.get("reconstruction") or {}
        places.append({
            "id": rec["id"],
            "name": rec["name"],
            "function": fn,
            "class": cls,
            "family": recon.get("family"),
            "division": recon.get("district"),
            "standing": "reconstructed" if recon else "named",
            "footprint_m2": footprint_m2,
            "storeys": storeys,
            "enclosed_floor_m2": enclosed,
            "capacity_grade": grade,
        })

    places.sort(key=lambda p: (p["class"], p["id"]))

    classes = []
    for cls, (group, families) in PROGRAMME_GROUPS.items():
        mine = [p for p in places if p["class"] == cls]
        n = len(mine)
        scheduled = sum(targets[f] for f in families)
        areas = [p["enclosed_floor_m2"] for p in mine]
        low, low_clamp = apportion(areas, n * ordinary, ceiling)
        high, high_clamp = apportion(areas, n * crowded[cls], ceiling)
        for p, lo, hi, lc, hc in zip(mine, low, high, low_clamp, high_clamp):
            if lo > hi:
                raise Fault(f"{p['id']} is given more beds on an ordinary night ({lo}) "
                            f"than when full ({hi})")
            p["beds_ordinary"] = lo
            p["beds_crowded"] = hi
            p["clamped_at_1840_maximum"] = bool(lc or hc)
            p["basis"] = (
                f"The town model puts {CLASS_WORDS[cls]} at {ordinary} people on an ordinary "
                f"night and {crowded[cls]} when full, from the 1840 household tail "
                f"(p90 and {CROWDED_FIGURE[cls]} of {sizes['households']:,} Chicago households). "
                f"This building takes the share of its class's total that its "
                f"{enclosed_floor_words(p)} is of the class's floor area."
            )
            p["replaceable_by"] = (
                "Any source that states this house's rooms, beds or lodgers on a dated day: an "
                "advertisement counting its rooms, a traveller's account of how many it slept, a "
                "licence return. A stated capacity retires the apportioned one outright."
            )
        classes.append({
            "class": cls,
            "programme_group": group,
            "families": list(families),
            "scheduled_roofs": scheduled,
            "built_places": n,
            "unbuilt_slots": scheduled - n,
            "ordinary_per_place": ordinary,
            "crowded_per_place": crowded[cls],
            "built_beds_ordinary": sum(low),
            "built_beds_crowded": sum(high),
            "unbuilt_beds_ordinary": (scheduled - n) * ordinary,
            "unbuilt_beds_crowded": (scheduled - n) * crowded[cls],
            # WHEN THE CROWDED END *IS* THE CEILING THERE IS NOTHING TO APPORTION,
            # and a column of identical numbers must not be allowed to read as a
            # derivation. The town model's high for inns is the largest household
            # the 1840 enumerator recorded, once per inn — so its own crowded end
            # already assumes every inn full to that maximum, and floor area has
            # nothing left to distinguish. Said here rather than left to be
            # noticed, because the alternative is a table that looks measured and
            # is not.
            "crowded_end_is_the_ceiling": crowded[cls] == ceiling,
        })

    bracket = figure(model, "lodging_and_institutions", "people_in_lodging_places")
    programme_low = sum(c["built_beds_ordinary"] + c["unbuilt_beds_ordinary"] for c in classes)
    programme_high = sum(c["built_beds_crowded"] + c["unbuilt_beds_crowded"] for c in classes)

    doc = {
        "$schema_note": "DERIVED. Written by tools/build_lodging_model_1835.py --build; "
                        "re-derived by --check in tools/check.sh. Do not hand-edit.",
        "id": "chicago_july_1835_lodging_model",
        "ticket": TICKET,
        "parent_ticket": "T-1175",
        "target_date": SCENE_DATE,
        "generated_by": "tools/build_lodging_model_1835.py",
        "not_a_reading": "This file reads no source. It measures committed structure records and "
                         "apportions a figure the town model already owns. It seats nobody, staffs "
                         "nobody and names nobody.",
        "inputs": [
            "data/reconstruction/1835_town_model.json",
            "data/reconstruction/1835_building_inventory.json",
            "data/research/census_1840/composition_1840.json",
            "data/structures/*.json",
        ],
        "the_figures_this_model_does_not_move": {
            "ordinary_night": ordinary,
            "crowded_boarding_house": crowded["boarding_house"],
            "crowded_inn": crowded["inn_tavern"],
            "ceiling": ceiling,
            "read_from": "data/research/census_1840/composition_1840.json § household_size",
            "note": f"p90, p99 and the observed maximum of {sizes['households']:,} Chicago "
                    f"households in 1840. The town model states these as the per-place ends of its "
                    f"own bed bracket; this model apportions them and never changes them.",
        },
        "classes": classes,
        "places": places,
        "not_open_on_the_scene_date": closed,
        "lodging_outside_the_programme": outside,
        "reconciliation": {
            "town_model_bracket": [bracket["low"], bracket["high"]],
            "programme_total_ordinary": programme_low,
            "programme_total_crowded": programme_high,
            "inside_the_bracket": bracket["low"] <= programme_low and programme_high <= bracket["high"],
            "note": "Built places at their apportioned capacity plus unbuilt slots at the model's "
                    "own per-place figure. It reproduces the town model's bracket because the "
                    "apportionment preserves each class's mean exactly; a total outside the bracket "
                    "would mean this tool had invented beds, and --check refuses it.",
        },
        "open_questions": [
            {
                "question": "The 42 roofs behind the town's bed bracket are scheduled under the "
                            "group name `larger_boarding_houses`, but 32 of them are families H1 and "
                            "H2, which the family-archetype crosswalk calls a center-hall house and a "
                            "merchant's house, and which the six such roofs already built record as "
                            "`larger_one_and_a_half_story_house` and `merchant_or_professional_house`. "
                            "Either the group name is wrong or the archetypes are.",
                "why_it_matters": "If the records are right, the town model's 468-1,232 counts 32 "
                                  "dwellings as lodging places and the bed bracket is too high by "
                                  "most of its width. This model classifies on the records' own "
                                  "`function` and counts the programme both ways rather than "
                                  "choosing, because choosing would be answering a question that "
                                  "belongs to the files' own tickets.",
                "owned_by": ["T-1293", "T-1196"],
            },
            {
                "question": "What staff each lodging place kept -- bar-keeper, hostler, cook, "
                            "chambermaid -- is not here.",
                "why_it_matters": "The business staffing model is T-1183 and it is open. A staff "
                                  "establishment written here would be that ticket's answer given by "
                                  "a tool with no licence to give it.",
                "owned_by": ["T-1183"],
            },
        ],
    }
    return doc


def enclosed_floor_words(p: dict) -> str:
    return (f"{p['enclosed_floor_m2']:,.0f} m² of enclosed floor "
            f"({p['footprint_m2']:,.0f} m² × {p['storeys']:g} storeys)")


# ------------------------------------------------------------------- report --

def report_text(doc: dict) -> str:
    out = [
        "# The 1835 lodging model",
        "",
        "> DERIVED from `data/reconstruction/1835_lodging_model.json`. Regenerate with",
        "> `tools/build_lodging_model_1835.py --build`; `tools/check.sh` re-derives both.",
        "> Do not hand-edit.",
        "",
        f"**{doc['ticket']}**, the first piece of T-1175. The town model says how many beds this "
        "town needed in total and says plainly that it \"seats nobody in any lodging place and gives "
        "no boarding house a capacity of its own\". This is the per-place half: how many of those "
        "beds stood in each house that is actually in the dataset.",
        "",
        "It reads no source. It measures committed structure records and apportions figures the town "
        "model already owns, so the town totals are unchanged by construction. It seats nobody.",
        "",
        "## What the town holds",
        "",
        "| class | scheduled | built | unbuilt | ordinary | full |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for c in doc["classes"]:
        out.append(f"| {c['class'].replace('_', ' ')} | {c['scheduled_roofs']} | {c['built_places']} "
                   f"| {c['unbuilt_slots']} | {c['ordinary_per_place']} | {c['crowded_per_place']} |")
    out += [
        "",
        "`ordinary` and `full` are the per-place figures, which this model does not move: the 1840 "
        f"household tail's p90 ({doc['the_figures_this_model_does_not_move']['ordinary_night']}), "
        f"p99 ({doc['the_figures_this_model_does_not_move']['crowded_boarding_house']}) and observed "
        f"maximum ({doc['the_figures_this_model_does_not_move']['crowded_inn']}).",
        "",
        "## Every lodging place, and the beds apportioned to it",
        "",
        "| place | class | standing | floor | ordinary | full | grade |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for p in doc["places"]:
        out.append(f"| {p['name']} | {p['class'].replace('_', ' ')} | {p['standing']} | "
                   f"{p['enclosed_floor_m2']:,.0f} m² | {p['beds_ordinary']} | {p['beds_crowded']} | "
                   f"{p['capacity_grade']}{' · clamped' if p['clamped_at_1840_maximum'] else ''} |")
    rec = doc["reconciliation"]
    out += [
        "",
        f"`floor` is the footprint times the storeys. `grade` is the weakest of the footprint and "
        "storey claims the capacity rests on — a bed count read off a reconstructed outline is "
        "reconstructed, whatever the building is called. `clamped` means a proportional share asked "
        f"for more than the largest household the 1840 enumerator recorded "
        f"({doc['the_figures_this_model_does_not_move']['ceiling']}) and was held to it.",
        "",
    ]
    for c in doc["classes"]:
        if c["crowded_end_is_the_ceiling"]:
            out += [
                f"Every {c['class'].replace('_', ' ')} carries the same {c['crowded_per_place']} in "
                f"the `full` column, and that is the town model speaking rather than this one "
                f"measuring. The model's crowded end for the class is {c['scheduled_roofs']} × "
                f"{c['crowded_per_place']} — the largest household the 1840 enumerator recorded, "
                f"once per roof — so it already assumes every one of them full to that maximum and "
                f"leaves floor area nothing to distinguish. Only the `ordinary` column varies here.",
                "",
            ]
    out += [
        "## Against the town model",
        "",
        f"Built places at their apportioned capacity, plus the unbuilt slots at the model's own "
        f"per-place figure, give **{rec['programme_total_ordinary']:,}–"
        f"{rec['programme_total_crowded']:,}** against the town model's "
        f"**{rec['town_model_bracket'][0]:,}–{rec['town_model_bracket'][1]:,}**. "
        + ("They agree, as they must: the apportionment preserves each class's mean exactly."
           if rec["inside_the_bracket"] else
           "**They do not agree, which means this tool has invented beds.**"),
        "",
    ]
    for c in doc["classes"]:
        if c["unbuilt_slots"]:
            out.append(f"- The {c['programme_group'].replace('_', ' ')} programme is "
                       f"**{c['built_places']} of {c['scheduled_roofs']}**: "
                       f"{c['unbuilt_slots']} slots hold no building yet, and the "
                       f"{c['unbuilt_beds_ordinary']:,}–{c['unbuilt_beds_crowded']:,} beds behind "
                       f"them are scheduled rather than standing.")
        else:
            out.append(f"- The {c['programme_group'].replace('_', ' ')} programme is "
                       f"**complete at {c['built_places']} of {c['scheduled_roofs']}**.")
    out += ["", "## Open questions", ""]
    for q in doc["open_questions"]:
        out += [f"- **{q['question']}** {q['why_it_matters']} "
                f"({', '.join(q['owned_by'])})"]
    lodging = doc["lodging_outside_the_programme"] + doc["not_open_on_the_scene_date"]
    if lodging:
        out += ["", "## Carried with no beds", ""]
        for row in lodging:
            out.append(f"- **{row['name']}** — {row['why_no_beds']}")
    out.append("")
    return "\n".join(out)


# -------------------------------------------------------------- the commands --

def cmd_build() -> int:
    doc = build(load())
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    MODEL_OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report_text(doc), encoding="utf-8")
    rec = doc["reconciliation"]
    print(f"OK: 1835 lodging model — {len(doc['places'])} lodging places with beds, "
          f"{rec['programme_total_ordinary']:,}–{rec['programme_total_crowded']:,} over the "
          f"programme, inside the town model's "
          f"{rec['town_model_bracket'][0]:,}–{rec['town_model_bracket'][1]:,}")
    return 0


def cmd_check() -> int:
    if not MODEL_OUT.exists():
        raise Fault(f"{MODEL_OUT.relative_to(ROOT)} has never been built")
    doc = build(load())
    on_disk = json.loads(MODEL_OUT.read_text(encoding="utf-8"))
    if json.dumps(doc, sort_keys=True) != json.dumps(on_disk, sort_keys=True):
        raise Fault(f"{MODEL_OUT.relative_to(ROOT)} no longer re-derives from its inputs — "
                    "run tools/build_lodging_model_1835.py --build")
    if REPORT.read_text(encoding="utf-8") != report_text(doc):
        raise Fault(f"{REPORT.relative_to(ROOT)} no longer re-derives from the model — "
                    "run tools/build_lodging_model_1835.py --build")
    if not doc["reconciliation"]["inside_the_bracket"]:
        raise Fault("the apportioned beds fall outside the town model's own bracket, "
                    "which means beds were invented here")
    for place in doc["places"]:
        if place["beds_ordinary"] < 1:
            raise Fault(f"{place['id']} is a lodging place that sleeps nobody")
        if place["beds_crowded"] > doc["the_figures_this_model_does_not_move"]["ceiling"]:
            raise Fault(f"{place['id']} sleeps more than the largest household of 1840")
    print(f"OK: the 1835 lodging model re-derives — {len(doc['places'])} places, "
          f"{doc['reconciliation']['programme_total_ordinary']:,}–"
          f"{doc['reconciliation']['programme_total_crowded']:,} beds over the programme")
    return 0


def cmd_self_test() -> int:
    fired = 0

    def fires(what, fn):
        nonlocal fired
        try:
            fn()
        except Fault:
            fired += 1
            return
        raise AssertionError(f"guard did not fire: {what}")

    # THE APPORTIONMENT PRESERVES THE CLASS TOTAL. This is the whole claim the
    # model rests on — that it redistributes the town model's figure rather than
    # changing it — so it is the first thing tested, on a spread wide enough that
    # plain rounding would not sum.
    areas = [79.4, 446.0, 84.0, 120.0, 260.0, 92.9, 139.3]
    got, clamped = apportion(areas, len(areas) * 9, 35)
    assert sum(got) == len(areas) * 9, (got, sum(got))
    assert not any(clamped)

    # AND A BIGGER HOUSE NEVER GETS FEWER BEDS THAN A SMALLER ONE.
    order = sorted(range(len(areas)), key=lambda i: areas[i])
    assert all(got[order[i]] <= got[order[i + 1]] for i in range(len(order) - 1)), got

    # THE CLAMP BINDS, AND THE BEDS IT REFUSES GO SOMEWHERE RATHER THAN VANISHING.
    lopsided = [1000.0, 10.0, 10.0, 10.0]
    got, clamped = apportion(lopsided, len(lopsided) * 21, 35)
    assert clamped[0] and got[0] == 35, (got, clamped)
    assert sum(got) == len(lopsided) * 21, (got, sum(got))

    # WHEN EVERY PLACE IS AT THE CEILING THE REMAINDER IS NOT FORCED ONTO ANYBODY.
    got, clamped = apportion([10.0, 10.0], 200, 35)
    assert got == [35, 35], got

    # A BUILDING WITH NO FLOOR IS A REFUSAL, NOT A ZERO.
    fires("a lodging place with no footprint polygon",
          lambda: enclosed_area_m2({"footprint": {"polygon": []}, "form": {"stories": {"value": 2}}}))
    fires("a lodging place with no storey count",
          lambda: enclosed_area_m2({"footprint": {"polygon": [[0, 0], [1, 0], [1, 1], [0, 1]]}}))
    fires("a lodging place measured at zero area", lambda: apportion([0.0, 5.0], 18, 35))

    # THE AREA IS THE POLYGON'S, NOT ITS BOUNDING BOX — an L-plan must not be
    # handed the beds of the rectangle that contains it.
    ell = {"footprint": {"polygon": [[0, 0], [10, 0], [10, 4], [4, 4], [4, 10], [0, 10]]},
           "form": {"stories": {"value": 1}}}
    assert enclosed_area_m2(ell)[0] == 64.0, enclosed_area_m2(ell)

    # A GRADE IS THE WEAKEST CLAIM UNDER IT, NEVER THE FLATTERING ONE.
    assert weakest("attested", "reconstructed") == "reconstructed"
    assert weakest("inferred", "documented") == "inferred"
    assert weakest(None, None) == "reconstructed"

    # THE PHASE IS THE ONE STANDING ON THE SCENE DATE — the Sauganash's 1829 log
    # cabin and its 1831 frame block are different buildings to measure.
    rec = {"phases": [
        {"id": "log_1829", "documented_range": {"from": "1829-01-01", "to": "1831-12-31"}},
        {"id": "frame_1831", "documented_range": {"from": "1831-01-01", "to": "1857-12-31"}},
    ]}
    assert scene_phase(rec)["id"] == "frame_1831", scene_phase(rec)

    # A HOUSE IS NOT A LODGING PLACE, however the programme groups its roof. This
    # is the H1/H2 distinction the open question is about, and reading it wrong
    # would silently put boarders in six south-division dwellings.
    assert "larger_one_and_a_half_story_house" not in LODGING_FUNCTIONS
    assert "merchant_or_professional_house" not in LODGING_FUNCTIONS
    assert LODGING_FUNCTIONS["large_boarding_house"] == "boarding_house"

    # THE REAL BUILD CLOSES ON THE TOWN MODEL, AND IS BYTE-IDENTICAL TWICE OVER.
    data = load()
    doc = build(data)
    assert doc["reconciliation"]["inside_the_bracket"], doc["reconciliation"]
    assert json.dumps(build(data), sort_keys=True) == json.dumps(doc, sort_keys=True)

    # EVERY CLASS'S MEAN IS THE TOWN MODEL'S FIGURE, which is the invariant that
    # makes this an apportionment rather than an opinion.
    for c in doc["classes"]:
        assert c["built_beds_ordinary"] == c["built_places"] * c["ordinary_per_place"], c
        assert c["built_beds_crowded"] == c["built_places"] * c["crowded_per_place"], c

    # NOBODY IS SEATED, STAFFED OR NAMED. The model is buildings and counts; a
    # person id in it would be T-1371's work done without its acceptance.
    text = json.dumps(doc["places"])
    for forbidden in ("hh_", "rc_", "person_", "relationship", "lives_at"):
        assert forbidden not in text, f"the lodging model carries a {forbidden}"

    print(f"build_lodging_model_1835 self-tests pass ({fired} guards fired, "
          f"{len(doc['places'])} places, "
          f"{doc['reconciliation']['programme_total_ordinary']:,}–"
          f"{doc['reconciliation']['programme_total_crowded']:,} beds inside the town model's "
          f"{doc['reconciliation']['town_model_bracket'][0]:,}–"
          f"{doc['reconciliation']['town_model_bracket'][1]:,}, nobody seated)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    try:
        if args.build:
            return cmd_build()
        if args.check:
            return cmd_check()
        if args.self_test:
            return cmd_self_test()
    except Fault as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
