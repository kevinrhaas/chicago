#!/usr/bin/env python3
"""THE 1835 TOWN MODEL: what the town of 1 July 1835 looked like beyond the people we can name.

T-1293, which folds T-1161 (population), T-1162 (occupations), T-1163 (households
and families), T-1164 (lodging and institutions) and T-1165 (arrival and origin)
into one pass, because all five answer one question off one body of evidence with
one method: take the known layer, set it against what a lake port of roughly three
thousand people implies, and STATE THE DIFFERENCE.

    tools/model_town_1835.py --build       write the model and its report
    tools/model_town_1835.py --check       re-derive both and refuse any drift
    tools/model_town_1835.py --self-test   the guards, fired on fixtures

WHAT THIS TOOL IS.  An ADJUDICATION over files this repository already holds and
already gates. It reads no page of any source, opens no network, names nobody, ages
nobody, houses nobody and creates no person, business or building. Every figure it
prints is a function of a committed derived file, and the file is named beside the
figure so a reader can go and disagree with it.

THE TOLERANCE IS THE POINT (the owner, 2026-09-17: "make them good but not great").
Every figure is A RANGE with a stated method and a named comparandum. A range is the
ANSWER here and not a hedge: a single number nobody can defend is worse than a bounded
one, and this model exists to be spent by the order book (T-1166) and then revised when
reconstruction finds it wrong. What the evidence cannot bound is written as an open
question in the section that owns it, and does NOT become a ticket.

THE THREE RECORDED COUNTS, AND WHY NONE OF THEM IS THE SCENE.  The Illinois State
census taken between 1 September and December 1835 returns 3,297 (`bk_mose1_006`).
Andreas prints a November 1835 town census of 3,265 people in 398 dwellings
(`andreas_1884_v1`). Both are AFTER 1 July 1835, in the fastest-growing months the
town had, so both are CEILINGS on the scene and never its population. The 1840 city
count is five years later and is a SHAPE — a sex ratio, a household histogram, a trade
split — and never a population to fill 1835 from.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "data" / "reconstruction" / "1835_town_model.json"
REPORT = ROOT / "docs" / "RESEARCH" / "1835_town_model.md"

PEOPLE = ROOT / "data" / "sidecars" / "1835" / "people.json"
TOWN_CENSUS = ROOT / "data" / "town_census.json"
INVENTORY = ROOT / "data" / "reconstruction" / "1835_building_inventory.json"
TRADE_CENSUS = ROOT / "data" / "research" / "books" / "trade_census_1835_crosswalk.json"
COMPOSITION = ROOT / "data" / "research" / "census_1840" / "composition_1840.json"
OLD_SETTLERS = ROOT / "data" / "research" / "old_settlers" / "people.json"

SCENE_DATE = "1835-07-01"

# The navigation season is the arrival window: the lake closed to shipping in winter
# and the overland road was the slower half of the traffic. April through November is
# eight months, and 1 July is the end of the third of them.
SEASON_MONTHS = 8
MONTHS_ASHORE_BY_SCENE = 3


class Fault(Exception):
    """A defect in the inputs, phrased for the person who must fix it."""


# ---------------------------------------------------------------------------
# a figure


def figure(name: str, low, high, method: str, comparanda: list[str],
           derived_from: list[str], point=None) -> dict:
    """One bounded answer. A range whose ends are equal is a COUNT, not an estimate."""
    if low > high:
        raise Fault(f"figure '{name}' is inverted: {low} > {high}")
    if not method.strip():
        raise Fault(f"figure '{name}' states no method")
    if not derived_from:
        raise Fault(f"figure '{name}' names no file it was derived from")
    if point is not None and not (low <= point <= high):
        raise Fault(f"figure '{name}' puts its point reading {point} outside [{low}, {high}]")
    return {"figure": name, "low": low, "high": high, "point": point,
            "is_a_count": low == high, "method": method,
            "comparanda": comparanda, "derived_from": derived_from}


def section(key: str, title: str, figures: list[dict], not_claiming: str,
            open_questions: list[str], tables: dict | None = None) -> dict:
    """A page, not a paper. Every section says what it is NOT claiming, in one sentence."""
    if not figures:
        raise Fault(f"section '{key}' carries no figure")
    if not not_claiming.strip():
        raise Fault(f"section '{key}' does not say what it is not claiming")
    if not_claiming.count(".") > 1:
        raise Fault(f"section '{key}' takes more than one sentence to say what it is not claiming")
    return {"key": key, "title": title, "figures": figures,
            "not_claiming": not_claiming, "open_questions": open_questions,
            "tables": tables or {}}


# ---------------------------------------------------------------------------
# origin: the roll's own birthplace column, bucketed by a rule and not by hand

REGION_RULES = [
    ("new_york", r"\bN\.?\s?Y\.?$|\bNew York\b"),
    ("new_england", r"\bVt\.?$|\bVermont\b|\bN\.?\s?H\.?$|\bNew Hampshire\b|\bMass\.?$|"
                    r"\bMassachusetts\b|\bConn\.?$|\bConnecticut\b|\bMaine$|\bR\.?\s?I\.?$"),
    ("mid_atlantic", r"\bPenn\.?$|\bPennsylvania\b|\bPhiladelphia\b|\bNew Jersey\b|\bN\.?\s?J\.?$|"
                     r"\bMd\.?$|\bMaryland\b|\bDel\.?$"),
    ("south", r"\bVa\.?$|\bVirginia\b|\bNorth Carolina\b|\bN\.?\s?C\.?$|\bKy\.?$|\bTenn\.?$|"
              r"\bS\.?\s?C\.?$|\bGa\.?$"),
    ("west_of_the_alleghenies", r"\bMich\.?$|\bOhio$|\bO\.$|\bInd\.?$|\bIll\.?$|\bMo\.?$"),
    ("england", r"\bEngland\.?$|\bEng\.?$"),
    ("ireland", r"\bIreland\.?$"),
    ("elsewhere_abroad", r"\bScotland\b|\bWales\b|\bCanada\b|\bGermany\b|\bFrance\b"),
]


def region_of(birthplace: str) -> str:
    """Bucket a printed birthplace. Unreadable and blank are one bucket and are counted."""
    text = (birthplace or "").strip().rstrip(".").strip()
    if not text:
        return "not_given"
    for name, pattern in REGION_RULES:
        if re.search(pattern, text, re.IGNORECASE):
            return name
    return "unclassified"


# ---------------------------------------------------------------------------
# the five sections


def named_arrivals(people: dict) -> dict:
    """`by_arrival_year`, over the people the layer can name. Same rule as `named_people`:
    a drawn person inherits the arrival of the household drawn around them, so counting
    one here would feed the reconstruction's own output back into the floor it was
    reconstructed against."""
    out: dict = {}
    for person in people.get("people") or []:
        if person.get("grade") == "reconstructed":
            continue
        year = person.get("arrival_year")
        if year is None:
            continue
        out[str(year)] = out.get(str(year), 0) + 1
    return dict(sorted(out.items()))


def named_people(counts: dict) -> int:
    """How many people the layer can NAME: the attested and the inferred, and no more.

    T-1171. This model is a model of the EVIDENCE, and the reconstruction it feeds draws
    against it — so a reconstructed person counted here would come back round as a larger
    layer, a higher population floor, a bigger quota and more people to draw, which is a
    model reading its own output as a reading. `by_grade` keeps the three apart and this
    is the sum the figures below mean when they say "the layer carries".
    """
    by_grade = counts["by_grade"]
    return int(by_grade["attested"]) + int(by_grade["inferred"])


def build_population(people: dict, census: dict, inventory: dict, comp: dict) -> dict:
    counts = people["counts"]
    known = named_people(counts)
    nov_people = census["people"]["town_total"]
    nov_dwellings = census["people"]["town_total_dwellings"]
    state_census = 3297  # bk_mose1_006, the State count of 1 Sept - Dec 1835

    arrivals = named_arrivals(people)
    # THE FLOOR RESTS ON THIS DISTRIBUTION, so an empty or scene-blind one is a FAULT and
    # not a floor of zero. Without it the arithmetic silently returns the November ceiling
    # at both ends and the range stops being a range while still looking like one.
    if not arrivals:
        raise Fault("the layer records no arrival year at all, so the population floor "
                    "has nothing to stand on")
    in_1835 = arrivals.get("1835", 0)
    if not in_1835:
        raise Fault("the layer records no 1835 arrival, which the population floor is "
                    "derived from")
    share_1835 = in_1835 / known

    # The town did not shrink, so the November count is the CEILING on 1 July.
    # The floor discounts the part of the 1835 arrival cohort that was still to come.
    cohort = share_1835 * nov_people
    still_to_come = cohort * (SEASON_MONTHS - MONTHS_ASHORE_BY_SCENE) / SEASON_MONTHS
    floor = int(round(nov_people - still_to_come))
    half_ashore = int(round(nov_people - cohort * 0.5))

    totals = comp["totals"]
    ratio_all = totals["males_per_100_females"]
    ratio_adult = totals["males_per_100_females_aged_20_and_over"]
    child_share = totals["child_share"]

    matrix = inventory["district_group_matrix"]["ordinary_dwellings"]
    dwelling_total = matrix["total"]
    divisions = {d: matrix[d] for d in ("south", "west", "north")}

    figures = [
        figure("recorded_town_count_november_1835", nov_people, nov_people,
               "Andreas prints the November 1835 town census as 3,265 people in 398 "
               "dwellings. Four months after the scene, so a ceiling on 1 July and never "
               "its population.", ["andreas_1884_v1"], ["data/town_census.json"]),
        figure("recorded_state_count_september_to_december_1835", state_census, state_census,
               "The Illinois State census returns 3,297 for Chicago. Two to five months "
               "after the scene, and a second ceiling that disagrees with the first by 32.",
               ["moses_kirkland_history_of_chicago_v1"],
               ["data/research/books/claims/moses_kirkland_history_of_chicago_v1.json"]),
        figure("population_on_1_july_1835", floor, nov_people,
               f"CEILING: the November count of {nov_people:,}, because the town grew "
               f"through 1835 and did not shrink. FLOOR: {share_1835:.1%} of the "
               f"{known:,} people the layer carries give an arrival year of 1835, so about "
               f"{cohort:,.0f} of the November town arrived that year; spread evenly over an "
               f"eight-month navigation season, {SEASON_MONTHS - MONTHS_ASHORE_BY_SCENE} "
               f"months of that cohort were still to come on 1 July. POINT READING: "
               f"{half_ashore:,}, which is the same arithmetic with half the cohort ashore "
               "by midsummer rather than three-eighths — the spring land-sale rush pulls "
               "arrivals earlier than a flat season does.",
               ["andreas_1884_v1"],
               ["data/town_census.json", "data/sidecars/1835/people.json"],
               point=half_ashore),
        figure("people_the_layer_can_name", known, known,
               f"The resident layer carries {known:,} people — "
               f"{counts['by_grade']['attested']:,} attested, "
               f"{counts['by_grade']['inferred']:,} inferred, "
               f"{counts['by_grade']['reconstructed']:,} reconstructed. A count of the "
               "layer, not of the town.", [], ["data/sidecars/1835/people.json"]),
        figure("males_per_100_females", ratio_all, 150.0,
               f"The 1840 city returns {ratio_all} overall and {ratio_adult} among those "
               "aged 20 and over. 1835 is five years earlier and rawer — more single men "
               "and fewer families — so the 1840 ratio is a FLOOR and the 1840 adult ratio "
               "is inside the range, not at the top of it.",
               ["census_1840_chicago_name_crosswalk"],
               ["data/research/census_1840/composition_1840.json"], point=ratio_adult),
        figure("share_under_ten", 0.20, child_share,
               f"Children under ten are {child_share:.1%} of the 1840 city. A town with a "
               "higher adult sex ratio carries proportionally fewer of them, so 1840 is the "
               "CEILING here and the floor is set one fifth below it.",
               ["census_1840_chicago_name_crosswalk"],
               ["data/research/census_1840/composition_1840.json"]),
    ]

    tables = {
        "by_division": {
            "unit": "share of the town, from the authored dwelling programme",
            "note": "The spec's ordinary-dwelling matrix is the only committed statement of "
                    "how the town divided between the three divisions. Applied to people it "
                    "assumes one division's dwellings held as many people as another's.",
            "rows": [{"division": d, "dwellings": n,
                      "share": round(n / dwelling_total, 4),
                      "people_low": int(round(floor * n / dwelling_total)),
                      "people_high": int(round(nov_people * n / dwelling_total))}
                     for d, n in divisions.items()],
        },
        "known_by_presence": people["counts"]["by_presence"],
    }

    return section(
        "population", "Population",
        figures,
        "This section does not claim that any named person was in the town on 1 July 1835; "
        "presence is a per-person ruling and 824 of the layer's people are still uncertain.",
        [
            "Neither recorded count is of the scene, and they disagree with each other by 32 "
            "people. Which of 3,265 and 3,297 is the better ceiling is not settled here.",
            "The floor rests on the arrival distribution of the people the layer can NAME, and "
            "the sources that name them (letter lists, voter rolls, directories) are themselves "
            "dated 1834-1835, so that distribution is biased toward late arrivals and the floor "
            "is more likely too low than too high.",
            "`bk_mose1_006`'s reading note says the figure 3,297 'is already in the repository' "
            "from the Chicago Democrat of 1835-07-01 and the Chicago American of 1835-06-08 and "
            "1835-06-27. Neither committed text carries it: the 3297 that greps in those files "
            "is an OCR coordinate, not a population. The note overstates its corroboration and "
            "the claim stands on Moses and Kirkland alone.",
            "The authored spec's `population_working_range` is [3200, 3265]. This model's "
            f"derived range for 1 July is [{floor:,}, {nov_people:,}] — the same ceiling and a "
            "far lower floor. The roof programme is cut against the spec's range; T-1196 is "
            "where the two are reconciled.",
        ],
        tables)


def build_occupations(crosswalk: dict, comp: dict, people: dict, pop: dict) -> dict:
    classes = crosswalk["classes"]
    # `other` and `not_stated` are register classes the census never printed a line for:
    # they are marked compared and carry no count, and a total that swept them in would be
    # the register measured against itself.
    compared = [c for c in classes
                if c.get("compared") and isinstance(c.get("census_count"), int)
                and isinstance(c.get("delta"), int)]
    uncounted = [c for c in classes if c not in compared]
    census_total = sum(c["census_count"] for c in compared)
    town_total = sum(c["town_records_at_scene_date"] for c in compared)
    short = [c for c in compared if c["delta"] < 0]
    over = [c for c in compared if c["delta"] > 0]
    shortfall = sum(-c["delta"] for c in short)
    # HOW MUCH OF THE SHORTFALL THE SOURCES HAVE ALREADY ACCOUNTED FOR (T-1428). The
    # crosswalk names, per class, the register's houses whose OPENING is dated after
    # 1 July: houses that stand in the autumn census and honestly not in the July town.
    # Without this the table reads a dated, named August opening as a hole in the town,
    # which is the reading that nearly had the order book commission two schools.
    explained = sum(c.get("shortfall_explained_by_later_openings") or 0 for c in short)

    industry = comp["industry"]
    employed_share = industry["employed_share_of_persons"]
    per_household = industry["employed_per_household"]

    pop_low = _fig(pop, "population_on_1_july_1835")["low"]
    pop_high = _fig(pop, "population_on_1_july_1835")["high"]

    counts = people["counts"]

    figures = [
        figure("census_classes_compared", len(compared), len(compared),
               f"{len(compared)} of the {len(classes)} classes the T-1006 crosswalk holds "
               f"carry both a printed census line and a register count; the other "
               f"{len(uncounted)} are a class the census never printed a line for, or a "
               "line the town holds nothing for.",
               ["moses_kirkland_history_of_chicago_v1"],
               ["data/research/books/trade_census_1835_crosswalk.json"]),
        figure("establishments_in_the_compared_classes",
               min(town_total, census_total), max(town_total, census_total),
               f"The register holds {town_total} records at the scene date across the "
               f"compared classes and the census counted {census_total} two to five months "
               + ("later — THE SAME NUMBER, which is a coincidence and not an agreement: "
                  f"{len(short)} classes are short and {len(over)} are over, and they "
                  "cancel. A total that matches while its rows do not is the strongest "
                  "argument in this model for reading the census BY CLASS and never as a "
                  "population of shops."
                  if town_total == census_total else
                  "later. The low end is what the town can name and the high end is what "
                  "the census counted, and the difference is growth plus what no notice "
                  "advertised."),
               ["moses_kirkland_history_of_chicago_v1"],
               ["data/research/books/trade_census_1835_crosswalk.json"]),
        figure("classes_short_of_the_census", len(short), len(short),
               f"{len(short)} compared classes hold fewer records than the census counted, "
               f"{shortfall} establishments short in total — of which {explained} are houses "
               "the register names with an opening announced AFTER the scene date, so that "
               f"much of the gap is already accounted for; {len(over)} hold more, which is "
               "the register counting NOTICES where the census counted houses.",
               ["moses_kirkland_history_of_chicago_v1"],
               ["data/research/books/trade_census_1835_crosswalk.json"]),
        figure("employed_persons", int(round(pop_low * employed_share)),
               int(round(pop_high * employed_share)),
               f"The 1840 schedule returns {employed_share:.0%} of persons in its seven "
               f"industry columns, {per_household} per household. Applied to this model's "
               "July population range. The 1840 columns count persons in families and not "
               "occupations of named men, so this is a size and not a roster.",
               ["census_1840_chicago_name_crosswalk"],
               ["data/research/census_1840/composition_1840.json"]),
        figure("people_the_layer_gives_a_trade", counts["with_a_role_at_scene_date"],
               counts["with_roles"],
               f"{counts['with_a_role_at_scene_date']} people carry a role that reaches "
               f"1 July 1835; {counts['with_roles']} carry any role at all, and "
               f"{counts['with_every_role_off_scene_date']} carry only roles dated off the "
               "scene. The gap between this and the employed-persons figure above is what "
               "the reconstruction bands have to fill.",
               [], ["data/sidecars/1835/people.json"]),
    ]

    tables = {
        "against_the_state_census": {
            "unit": "establishment records at the scene date against the printed census line",
            "date_caution": crosswalk["date_caution"],
            "rows": [{"class": c["class"], "census_line": c["census_line"],
                      "census_count": c["census_count"],
                      "town_at_scene_date": c["town_records_at_scene_date"],
                      "delta": c["delta"], "outcome": c["outcome"],
                      "opened_after_the_scene_date":
                          c.get("shortfall_explained_by_later_openings") or 0}
                     for c in sorted(compared, key=lambda c: (c["delta"], c["class"]))],
        },
        "employment_shape_1840": {
            "unit": "persons in families, 1840, as the relative weight of each pursuit",
            "rows": industry["columns"],
        },
    }

    return section(
        "occupations", "Occupations",
        figures,
        "This section does not claim a trade for any named man, and a class that stands short "
        "of the census stays short rather than being filled with invented practitioners.",
        [
            "The census's lawyer and physician lines count PEOPLE and the register counts "
            "RECORDS, so those two rows are not comparable in the same unit as the rest; "
            "`trade_census_spend_1835.py` holds that adjudication.",
            "A shortfall against a count taken two to five months later is never evidence that "
            "an establishment stood in July, and this model does not treat it as a quota until "
            "the order book (T-1166) rules on how much of it is growth.",
            "The 1840 industry columns have no row for domestic service, which a port with "
            "this adult sex ratio certainly had; the trade split understates household labour "
            "by an amount this model cannot bound.",
        ],
        tables)


def build_households(comp: dict, census: dict, people: dict, inventory: dict, pop: dict) -> dict:
    size = comp["household_size"]
    mean = size["mean"]
    median = size["median"]
    nov_people = census["people"]["town_total"]
    nov_dwellings = census["people"]["town_total_dwellings"]
    per_dwelling = round(nov_people / nov_dwellings, 3)

    pop_low = _fig(pop, "population_on_1_july_1835")["low"]
    pop_high = _fig(pop, "population_on_1_july_1835")["high"]

    hh_low = int(round(pop_low / mean))
    hh_high = int(round(pop_high / median))

    counts = people["counts"]
    layer_households = counts["households"]
    layer_people = named_people(counts)

    matrix = inventory["district_group_matrix"]
    figures = [
        figure("people_per_dwelling_november_1835", per_dwelling, per_dwelling,
               f"{nov_people:,} people in {nov_dwellings} dwellings. Against a 1840 mean "
               f"HOUSEHOLD of {mean}, the gap is the finding: in 1835 a dwelling held more "
               "than one household, and a roof programme that seats one family per roof "
               "undercounts the town.",
               ["andreas_1884_v1", "census_1840_chicago_name_crosswalk"],
               ["data/town_census.json", "data/research/census_1840/composition_1840.json"]),
        figure("households_on_1_july_1835", hh_low, hh_high,
               f"This model's July population divided by household size: the low end takes "
               f"the low population at the 1840 MEAN of {mean}, the high end the high "
               f"population at the 1840 MEDIAN of {median}. The distribution is long-tailed "
               "— one 1840 household in a hundred holds twenty-one people or more — so mean "
               "and median bracket it better than either alone.",
               ["census_1840_chicago_name_crosswalk"],
               ["data/research/census_1840/composition_1840.json"]),
        figure("household_size", median, mean,
               f"Median {median}, mean {mean} in the 1840 city; p75 is "
               f"{size['percentiles']['p75']} and p99 is {size['percentiles']['p99']}. Half "
               "the town lives in households of four or fewer and the tail is boarding "
               "houses, hotels and crews.",
               ["census_1840_chicago_name_crosswalk"],
               ["data/research/census_1840/composition_1840.json"]),
        figure("household_records_the_layer_carries", layer_households, layer_households,
               f"{layer_households:,} household records for {layer_people:,} people — "
               f"{layer_people / layer_households:.2f} people per record. The layer mints a "
               "letter-list or civic name as its own household, so it holds MORE household "
               "shells than the town had households. That is a property of the mint, not a "
               "reading of the town, and the order book must not count them as families.",
               [], ["data/sidecars/1835/people.json"]),
        figure("dwellings_the_programme_schedules", matrix["ordinary_dwellings"]["total"],
               matrix["ordinary_dwellings"]["total"] + matrix["larger_boarding_houses"]["total"],
               f"The authored programme schedules "
               f"{matrix['ordinary_dwellings']['total']} ordinary dwellings and "
               f"{matrix['larger_boarding_houses']['total']} larger boarding houses. The "
               "November census counted 398 dwellings, so the programme's dwelling half sits "
               "below the recorded count and its boarding houses make up the difference.",
               ["owner_chicago_1835_reconstruction_spec_2026"],
               ["data/reconstruction/1835_building_inventory.json"]),
    ]

    tables = {
        "size_histogram_1840": {"unit": "households by person count, 1840 city",
                                "rows": size["histogram"]},
        "the_rule_for_a_head_no_source_names": {
            "statement": "A head the sources name but whose family they do not gets a household "
                         "drawn from the 1840 distribution at his own size band, never from the "
                         "mean. The mean is 5.015 and the median is 4: drawing every unnamed "
                         "family at the mean would build a town with no small households and no "
                         "long tail, which is the one shape the 1840 count rules out.",
            "sex_ratio_caution": "Households drawn symmetrically break the adult sex ratio "
                                 f"({comp['totals']['males_per_100_females_aged_20_and_over']} "
                                 "males per 100 females aged 20 and over in 1840, and higher in "
                                 "1835). The surplus men are boarders and lodgers, not husbands.",
        },
    }

    return section(
        "households_and_families", "Households and families",
        figures,
        "This section supplies no member to any household and names nobody; it states the "
        "distribution a reconstructed family must be drawn from and nothing about which family.",
        [
            "How many households a dwelling held in 1835 is not settled: 8.20 people per "
            "dwelling against a 1840 mean household of 5.02 implies roughly 1.6, but the 1835 "
            "count's 'dwelling' is the enumerator's word and this project has not read his "
            "schedule.",
            "The layer's 1,258 household records cannot be reconciled with a town of 469 to 816 "
            "households without a ruling on what a letter-list mint IS; T-0660 and T-0691 hold "
            "that question and are blocked on the owner.",
        ],
        tables)


def build_lodging(inventory: dict, crosswalk: dict, comp: dict, pop: dict) -> dict:
    matrix = inventory["district_group_matrix"]
    boarding = matrix["larger_boarding_houses"]["total"]
    inns = matrix["inns_taverns"]["total"]
    institutional = matrix["institutional_public"]["total"]
    fort = matrix["fort_principal"]["total"]

    by_class = {c["class"]: c for c in crosswalk["classes"]}
    tavern_line = by_class.get("tavern", {})
    p99 = comp["household_size"]["percentiles"]["p99"]
    p90 = comp["household_size"]["percentiles"]["p90"]
    maximum = comp["household_size"]["max"]

    pop_high = _fig(pop, "population_on_1_july_1835")["high"]

    lodged_low = boarding * p90 + inns * p90
    lodged_high = boarding * p99 + inns * maximum

    figures = [
        figure("larger_boarding_houses", boarding, boarding,
               f"The authored programme schedules {boarding} across the three divisions "
               f"({matrix['larger_boarding_houses']['south']} south, "
               f"{matrix['larger_boarding_houses']['west']} west, "
               f"{matrix['larger_boarding_houses']['north']} north).",
               ["owner_chicago_1835_reconstruction_spec_2026"],
               ["data/reconstruction/1835_building_inventory.json"]),
        figure("inns_and_taverns", tavern_line.get("town_records_at_scene_date", inns),
               max(inns, tavern_line.get("census_count", inns),
                   tavern_line.get("town_records_at_scene_date", inns)),
               f"The programme schedules {inns} inns and taverns; the State census counted "
               f"{tavern_line.get('census_count', 'no')} taverns two to five months later "
               f"and the business layer holds "
               f"{tavern_line.get('town_records_at_scene_date', 'no')} at the scene date. "
               "The three units are a roof, a licence and a printed notice, and they are not "
               "the same thing counted three ways. THE LAYER'S COUNT MAY EXCEED BOTH OTHERS "
               "AND THE CEILING FOLLOWS IT (T-1404): the census's figure is a count of "
               "LICENCES taken months after the scene, and the town's named public houses — "
               "the Sauganash, the Exchange, the Tremont, the Mansion House, the Steamboat, "
               "the Western, Wolf Point — are houses the papers never advertised and the "
               "licence roll never separated. A licence count cannot cap a house count, so "
               "the ceiling is whichever of the three reads highest. T-1196 owns re-cutting "
               "the roof programme against it.",
               ["moses_kirkland_history_of_chicago_v1",
                "owner_chicago_1835_reconstruction_spec_2026"],
               ["data/reconstruction/1835_building_inventory.json",
                "data/research/books/trade_census_1835_crosswalk.json"]),
        figure("people_in_lodging_places", lodged_low, lodged_high,
               f"{boarding} boarding houses and {inns} inns, filled from the 1840 "
               f"household tail: the low end puts every one at p90 ({p90} people), the high "
               f"end at p99 ({p99}) for the boarding houses and the observed maximum "
               f"({maximum}) for the inns. That tail IS lodging — it is what a household of "
               "twenty-one people in a lake port was.",
               ["census_1840_chicago_name_crosswalk"],
               ["data/research/census_1840/composition_1840.json",
                "data/reconstruction/1835_building_inventory.json"]),
        figure("share_of_the_town_in_lodging", round(lodged_low / pop_high, 3),
               round(min(lodged_high / pop_high, 1.0), 3),
               f"The lodged range against the ceiling population of {pop_high:,}: between "
               f"{lodged_low / pop_high:.0%} and {min(lodged_high / pop_high, 1.0):.0%} of a "
               "boom-year port living in somebody else's house, which is the shape the adult "
               "sex ratio already implies. It is also the single figure most likely to be "
               "wrong in this model, because it multiplies an authored roof count by a "
               "borrowed capacity and neither end is measured.",
               ["census_1840_chicago_name_crosswalk"],
               ["data/reconstruction/1835_building_inventory.json"]),
        figure("institutional_and_public_roofs", institutional, institutional + fort,
               f"{institutional} institutional or public roofs outside the fort and {fort} "
               "principal roofs inside it. The census's five churches, seven schools, one "
               "bank, one lottery office and a lyceum are counted in December and several of "
               "them met in rooms rather than in buildings of their own.",
               ["moses_kirkland_history_of_chicago_v1",
                "owner_chicago_1835_reconstruction_spec_2026"],
               ["data/reconstruction/1835_building_inventory.json"]),
    ]

    tables = {
        "lodging_and_institutional_roofs": {
            "unit": "roofs in the authored programme, by division",
            "rows": [dict(group=g, **matrix[g]) for g in
                     ("larger_boarding_houses", "inns_taverns", "institutional_public",
                      "fort_principal", "stores_mixed_use", "warehouses_freight")],
        },
        "counted_in_december_not_in_july": {
            "line": crosswalk["classes"][0]["claim_id"],
            "institutions": "five churches, seven schools, one bank, one lottery office, "
                            "a lyceum and reading room, four storage and forwarding houses",
            "caution": "Counted between 1 September and December 1835. A church with five "
                       "congregations in December had fewer in July and some of them had no "
                       "building at all.",
        },
    }

    return section(
        "lodging_and_institutions", "Lodging and institutions",
        figures,
        "This section seats nobody in any lodging place and gives no boarding house a "
        "capacity of its own; it states how many beds the town needed in total.",
        [
            "The garrison of Fort Dearborn on 1 July 1835 is not modelled here. The fort's "
            "strength is a roster question owned by T-1176 and the ten principal roofs are all "
            "this model counts.",
            "The vessels in port held people the shore census may or may not have counted, and "
            "no committed source settles how the November enumerator treated a crew ashore.",
            "Whether the census's 398 dwellings include boarding houses and taverns or count "
            "them separately is unknown, and the answer moves the lodging share by more than "
            "any other assumption in this section.",
        ],
        tables)


def build_arrival(people: dict, settlers: dict) -> dict:
    counts = people["counts"]
    known = named_people(counts)
    # THE WHOLE LAYER, and the TABLE below is the only thing that may read it. It is what
    # the reconstruction's arrival stage draws against, so re-cutting it re-draws every
    # card it ever dealt; see this section's notes for why that circle is a ticket of its
    # own and not a line here.
    by_year = {int(y): n for y, n in counts["by_arrival_year"].items()}
    # THE NAMED LAYER, and every FIGURE below divides by it. T-1364: the two figures read
    # `by_year` over `known`, which is a count of the whole compiled layer over a
    # denominator that excludes every reconstructed person in it. The share passed 1 the
    # moment T-1171 drew a layer bigger than the evidence, and the complement it printed
    # went negative — "only -809 came before 1833", which tells a reader nothing except
    # that something is wrong. `named_arrivals` is the same rule `build_population`
    # already applies to the population floor, so the two sections now count the same
    # cohort over the same denominator instead of two different ones.
    named_by_year = {int(y): n for y, n in named_arrivals(people).items()}
    dated = sum(named_by_year.values())
    since_1833 = sum(n for y, n in named_by_year.items() if y >= 1833)
    before_1833 = dated - since_1833
    undated = known - dated
    if since_1833 > known:
        raise Fault("more named people arrived in 1833-35 than the layer can name, so "
                    "the arrival share is over the wrong denominator again (T-1364)")

    pre36 = [p for p in settlers["people"] if p.get("arrival_at_or_before_1835")]
    regions = Counter(region_of(p.get("birthplace_as_read")) for p in pre36)
    given = sum(n for r, n in regions.items() if r not in ("not_given", "unclassified"))

    ny = regions.get("new_york", 0)
    ne = regions.get("new_england", 0)

    figures = [
        figure("arrived_in_the_three_years_before_the_scene",
               round(since_1833 / known, 3), round(since_1833 / known, 3),
               f"{since_1833:,} of the {known:,} people the layer can NAME give an arrival "
               f"year of 1833, 1834 or 1835; {before_1833:,} give an earlier one"
               + (f" and {undated:,} give none at all" if undated else
                  ", and no named person is left without a year")
               + ". The town of 1 July 1835 is overwhelmingly three years old or less. "
               "DENOMINATOR: the named layer — the attested and the inferred — and not "
               "the whole one. A reconstructed person's arrival year is DRAWN from this "
               "section's own table, so counting it back into this share would be the "
               "model reading its own output as a reading.",
               [], ["data/sidecars/1835/people.json"]),
        figure("arrived_in_1835_itself", round(named_by_year.get(1835, 0) / known, 3),
               round(named_by_year.get(1835, 0) / known, 3),
               f"{named_by_year.get(1835, 0):,} of the same {known:,} named people. This "
               "is the figure the population floor is built on — `population_on_1_july_1835` "
               "divides this same cohort by this same denominator — and it is the one most "
               "exposed to the bias below.",
               [], ["data/sidecars/1835/people.json"]),
        figure("born_in_new_york_state", round(ny / given, 3) if given else 0.0,
               round((ny + ne) / given, 3) if given else 0.0,
               f"Of the {len(pre36)} Old Settlers who registered an arrival at or before "
               f"1835 and gave a birthplace, {ny} were born in New York State and {ne} "
               "elsewhere in New England. The low end is New York alone, the high end New "
               "York and New England together — the Erie Canal corridor and its feeders, "
               "which is the origin story this town has.",
               ["calumet_club_early_chicago_1879"],
               ["data/research/old_settlers/people.json"]),
        figure("born_abroad",
               round((regions.get("england", 0) + regions.get("ireland", 0)
                      + regions.get("elsewhere_abroad", 0)) / given, 3) if given else 0.0,
               round((regions.get("england", 0) + regions.get("ireland", 0)
                      + regions.get("elsewhere_abroad", 0)) / given, 3) if given else 0.0,
               "England and Ireland in the Old Settlers roll. A floor and not a share: the "
               "1840 extract's foreign-born column reads zero in all 964 rows, which is a "
               "column that was not coded and not a count of none, so this project holds no "
               "measure of the town's foreign-born at all.",
               ["calumet_club_early_chicago_1879"],
               ["data/research/old_settlers/people.json"]),
    ]

    tables = {
        "arrival_year_of_the_known_layer": {
            "unit": "people in the WHOLE compiled layer — named and reconstructed together "
                    "— by the arrival year each one records, out of the "
                    f"{sum(by_year.values()):,} who record one at all",
            "not_the_figures_denominator": "The FIGURES above divide by the named layer "
                                           "alone; this table does not, and the two are "
                                           "different populations on purpose (T-1364).",
            "rows_total": sum(by_year.values()),
            "rows": [{"year": y, "people": by_year[y],
                      # exact-sum-ok: a count of rows, summed in exact integers
                      "share": round(by_year[y] / sum(by_year.values()), 4)}
                     for y in sorted(by_year)],
        },
        "birthplace_of_the_old_settlers_who_came_by_1835": {
            "unit": "rows of the Calumet Club rolls whose arrival is at or before 1835",
            "rows_total": len(pre36),
            "rows": [{"region": r, "people": n} for r, n in regions.most_common()],
        },
    }

    return section(
        "arrival_and_origin", "Arrival and origin",
        figures,
        "This section dates and places nobody: it is a distribution over cohorts and an "
        "arrival year on a card is still that card's own evidence.",
        [
            "The arrival distribution is of people the project can NAME, and the sources that "
            "name them — letter lists, voter rolls, the 1839 and 1843 directories — are "
            "themselves of 1834 and later, so a man who came in 1831 and left no notice is "
            "missing from it. The 1835 share is a ceiling on the true share.",
            "THE FIGURES AND THE TABLE COUNT TWO DIFFERENT POPULATIONS, and saying so is the "
            "point of this note. Every figure divides by the NAMED layer — the attested and "
            "the inferred — because a reconstructed person's arrival year was drawn from "
            "this model and counting it back in would be the model reading its own output "
            "(the same rule `people_the_layer_can_name` states). The table below is the "
            "WHOLE compiled layer, because that is what the reconstruction's arrival stage "
            "reads: `reconstruct_residents_1835.py` draws each filled arrival from these "
            "rows. Until T-1364 the figures took the table's numerator over the figures' "
            "denominator, and the share read 1.605 with a complement of -777 people.",
            "THAT TABLE IS STILL A CIRCLE, and this model cannot close it alone: the "
            "distribution the arrival stage draws from is computed over a layer that stage "
            "has already written into, so each pass re-reads its own last draw. Cutting the "
            "table to the named layer would redraw every arrival ever dealt, which is a "
            "rebuild and not a figure — recorded on T-1179, which owns the convergence "
            "rebuild order, and deliberately not done here.",
            "The Old Settlers roll is a self-selected survivorship sample registered forty-four "
            "years later: it over-represents men who stayed, prospered and lived to 1879, and "
            "it holds no woman who married out of her registered name. Its birthplaces are the "
            "only origin distribution this project has and they are not the town's.",
            "WHY people came is not modelled. The land sales, the canal commission and the "
            "harbour works are each a documented draw, but no committed source apportions the "
            "town between them and this model will not invent the split.",
        ],
        tables)


# ---------------------------------------------------------------------------


def _fig(sect: dict, name: str) -> dict:
    for f in sect["figures"]:
        if f["figure"] == name:
            return f
    raise Fault(f"section '{sect['key']}' has no figure '{name}'")


def build(people: dict, census: dict, inventory: dict, crosswalk: dict,
          comp: dict, settlers: dict) -> dict:
    pop = build_population(people, census, inventory, comp)
    sections = [
        pop,
        build_occupations(crosswalk, comp, people, pop),
        build_households(comp, census, people, inventory, pop),
        build_lodging(inventory, crosswalk, comp, pop),
        build_arrival(people, settlers),
    ]
    keys = [s["key"] for s in sections]
    if len(set(keys)) != len(keys):
        raise Fault("two sections share a key")
    if len(sections) != 5:
        raise Fault(f"the model is five sections and this is {len(sections)}")
    return {
        "$schema_note": "DERIVED — regenerate with tools/model_town_1835.py --build; "
                        "tools/check.sh re-derives it. Do not hand-edit: every figure is a "
                        "function of a committed file named in its own `derived_from`.",
        "id": "chicago_july_1835_town_model",
        "ticket": "T-1293",
        "target_date": SCENE_DATE,
        "generated_by": "tools/model_town_1835.py --build",
        "not_a_reading": "an adjudication over committed derived files — no page of any "
                         "source is read here, and nobody is named, aged, dated or housed",
        "folds": ["T-1161", "T-1162", "T-1163", "T-1164", "T-1165"],
        "spent_by": "T-1166, the reconstruction order book",
        "tolerance": "Every figure is a range with a stated method and a named comparandum. "
                     "A range is the answer and not a hedge. The model does not need to be "
                     "right to the person; it needs to be defensible, bounded and finished, "
                     "and it will be revised when reconstruction finds it wrong.",
        "inputs": sorted({p for s in sections for f in s["figures"] for p in f["derived_from"]}),
        "sections": sections,
    }


def load(root: Path = ROOT) -> tuple:
    def read(path: Path):
        full = root / path.relative_to(ROOT)
        if not full.exists():
            raise Fault(f"a file the model is derived from is missing: {path}")
        return json.loads(full.read_text(encoding="utf-8"))
    return (read(PEOPLE), read(TOWN_CENSUS), read(INVENTORY), read(TRADE_CENSUS),
            read(COMPOSITION), read(OLD_SETTLERS))


# ---------------------------------------------------------------------------
# the report


def _range(f: dict) -> str:
    lo, hi = f["low"], f["high"]
    fmt = (lambda v: f"{v:,}" if isinstance(v, int) else f"{v:g}")
    if f["is_a_count"]:
        return f"**{fmt(lo)}**"
    point = f" (point reading **{fmt(f['point'])}**)" if f["point"] is not None else ""
    return f"**{fmt(lo)} – {fmt(hi)}**{point}"


def report_text(doc: dict) -> str:
    out = ["# The 1835 town model", "",
           "**T-1293.** What the town of 1 July 1835 looked like beyond the people we can "
           "name: population, occupations, households, lodging and arrival, each figure a "
           "range with its method and its comparanda.", "",
           f"Derived file: `data/reconstruction/1835_town_model.json`  ",
           f"Built and gated by: `{doc['generated_by'].replace(' --build', '')} "
           "--build | --check | --self-test`  ",
           f"Folds: {' · '.join(doc['folds'])}  ",
           f"Spent by: {doc['spent_by']}", "", "---", "",
           "## The tolerance, stated first", "", doc["tolerance"], "",
           "It is " + doc["not_a_reading"] + ".", ""]

    for n, s in enumerate(doc["sections"], 1):
        out += [f"## {n}. {s['title']}", ""]
        out += ["| Figure | Reading | Method |", "| --- | ---: | --- |"]
        for f in s["figures"]:
            method = f["method"].replace("\n", " ")
            out.append(f"| `{f['figure']}` | {_range(f)} | {method} |")
        out += ["", f"**Not claiming.** {s['not_claiming']}", ""]
        for name, table in s["tables"].items():
            out += [f"### {name.replace('_', ' ')}", ""]
            rows = table.get("rows") if isinstance(table, dict) else None
            if isinstance(rows, list) and rows and isinstance(rows[0], dict):
                cols = list(rows[0].keys())
                out += ["| " + " | ".join(c.replace("_", " ") for c in cols) + " |",
                        "| " + " | ".join("---" for _ in cols) + " |"]
                for r in rows:
                    out.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
            for k, v in (table.items() if isinstance(table, dict) else []):
                if k in ("rows", "unit"):
                    continue
                out.append(f"- **{k.replace('_', ' ')}** — {v}")
            if isinstance(table, dict) and table.get("unit"):
                out.append(f"- **unit** — {table['unit']}")
            out.append("")
        if s["open_questions"]:
            out += ["**Open questions.** These are recorded here and do not become tickets.", ""]
            for q in s["open_questions"]:
                out.append(f"- {q}")
            out.append("")

    out += ["---", "", "## What this model may not do", "",
            "- **name, age, date or house anybody.** Every figure is a cohort;",
            "- **fill a shortfall with invented people.** A class short of the census stays "
            "short until the order book (T-1166) rules on how much of the gap is growth;",
            "- **raise a confidence.** Nothing here is evidence about any person, household "
            "or building, and no card may cite it;",
            "- **stand unrevised.** It will be wrong somewhere, and reconstruction finding it "
            "wrong is the honest way round — not polishing it before anything is built on it.",
            "", "## Inputs", ""]
    for path in doc["inputs"]:
        out.append(f"- `{path}`")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# commands


def cmd_build() -> int:
    doc = build(*load())
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    MODEL.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report_text(doc), encoding="utf-8")
    print(f"OK: 1835 town model — {len(doc['sections'])} sections, "
          f"{sum(len(s['figures']) for s in doc['sections'])} figures, "
          f"{sum(len(s['open_questions']) for s in doc['sections'])} open questions")
    return 0


def cmd_check() -> int:
    expected = build(*load())
    faults = []
    if not MODEL.exists():
        faults.append("the 1835 town model is missing — run --build")
    elif json.loads(MODEL.read_text(encoding="utf-8")) != expected:
        faults.append("the 1835 town model is stale — run --build")
    if not REPORT.exists():
        faults.append("the 1835 town model report is missing — run --build")
    elif REPORT.read_text(encoding="utf-8") != report_text(expected):
        faults.append("the 1835 town model report is stale — run --build")
    if faults:
        for f in faults:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    pop = _fig(expected["sections"][0], "population_on_1_july_1835")
    print(f"OK: 1835 town model — July population {pop['low']:,}–{pop['high']:,} "
          f"(point {pop['point']:,}), {len(expected['sections'])} sections")
    return 0


def cmd_self_test() -> int:
    args = load()
    fired = 0

    def _fires(mutated, why):
        nonlocal fired
        try:
            build(*mutated)
        except Fault:
            fired += 1
            print(f"   fires: {why}")
            return
        raise AssertionError(f"did not fire: {why}")

    # A RANGE MAY NOT BE INVERTED, and the November count is the ceiling the floor
    # is measured down from — invert the town census and the population figure inverts.
    a = list(copy.deepcopy(args)); a[1]["people"]["town_total"] = 1
    _fires(a, "a recorded town count below the floor the arrival cohort implies")

    # EVERY FIGURE NAMES A FILE. Strip the arrival distribution and the section that
    # rests on it cannot be built at all rather than quietly reporting zero.
    # T-1171: the distribution is counted off the people the layer can NAME, one row at a
    # time, rather than off the sidecar's pre-aggregated tally — so stripping it means
    # stripping the rows.
    a = list(copy.deepcopy(args))
    a[0]["counts"]["by_arrival_year"] = {}
    a[0]["people"] = []
    try:
        build(*a)
        raise AssertionError("did not fire: an empty arrival distribution")
    except (Fault, ZeroDivisionError, ValueError):
        fired += 1
        print("   fires: an empty arrival distribution")

    # T-1364: AN ARRIVAL SHARE'S NUMERATOR AND DENOMINATOR ARE ONE POPULATION. The
    # section is built on its own so the guard is tested for the reason it exists and
    # not for the population floor inverting first. Shrink the named layer below the
    # named arrivals already counted in it and the share would pass 1 and print a
    # negative complement, which is exactly what "only -777 came before 1833" was.
    a = copy.deepcopy(args[0])
    a["counts"]["by_grade"] = {"attested": 1, "inferred": 1, "reconstructed": 0}
    try:
        build_arrival(a, copy.deepcopy(args[5]))
        raise AssertionError("did not fire: an arrival share over the wrong denominator")
    except Fault:
        fired += 1
        print("   fires: an arrival share over the wrong denominator")

    # A POINT READING OUTSIDE ITS OWN RANGE. The half-ashore reading must sit between
    # the floor and the ceiling; a season shorter than the months already ashore
    # would put it outside, and the figure guard is what catches that.
    assert figure("x", 1, 3, "m", [], ["p"], point=2)["point"] == 2
    try:
        figure("x", 1, 3, "m", [], ["p"], point=9)
        raise AssertionError("did not fire: a point reading outside its range")
    except Fault:
        fired += 1
        print("   fires: a point reading outside its range")

    # A FIGURE WITH NO METHOD, and a figure derived from nothing.
    for bad, why in ((dict(method="  "), "a figure that states no method"),
                     (dict(derived_from=[]), "a figure derived from no file")):
        kwargs = dict(name="x", low=1, high=2, method="m", comparanda=[],
                      derived_from=["p"])
        kwargs.update(bad)
        try:
            figure(**kwargs)
            raise AssertionError(f"did not fire: {why}")
        except Fault:
            fired += 1
            print(f"   fires: {why}")

    # THE ONE-SENTENCE RULE on what a section is not claiming.
    try:
        section("k", "T", [figure("x", 1, 2, "m", [], ["p"])], "One. Two.", [])
        raise AssertionError("did not fire: a two-sentence refusal")
    except Fault:
        fired += 1
        print("   fires: a refusal that takes more than one sentence")
    try:
        section("k", "T", [figure("x", 1, 2, "m", [], ["p"])], "   ", [])
        raise AssertionError("did not fire: a section that does not refuse anything")
    except Fault:
        fired += 1
        print("   fires: a section that does not say what it is not claiming")

    # A MISSING INPUT IS A FAULT, not a section quietly built without it.
    try:
        load(Path("/nonexistent-root-for-the-self-test"))
        raise AssertionError("did not fire: a missing input file")
    except Fault:
        fired += 1
        print("   fires: an input file the model cannot read")

    # THE BIRTHPLACE BUCKETS ARE A RULE, not a hand count: blank is counted rather
    # than dropped, and a place no rule matches is `unclassified` and visible.
    assert region_of("Fishkill, Duchess Co., N.Y.") == "new_york"
    assert region_of("Burlington, Vt.") == "new_england"
    assert region_of("London, England.") == "england"
    assert region_of("") == "not_given"
    assert region_of("Somewhere nobody ruled") == "unclassified"

    # AND THE MODEL IS FIVE SECTIONS. Four is a model with a hole in it.
    doc = build(*args)
    assert len(doc["sections"]) == 5, doc["sections"]
    assert all(s["figures"] for s in doc["sections"])
    assert doc["sections"][0]["figures"], "population carries no figure"

    # NOBODY IS NAMED. The whole point of the tolerance is that this file is cohorts.
    text = json.dumps(doc)
    for forbidden in ("person_", "hh_", "business_"):
        assert forbidden not in text, f"the model names a {forbidden} record"

    print(f"model_town_1835 self-tests pass ({fired} guards fired, 5 sections, "
          "no record named)")
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
