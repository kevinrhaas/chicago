#!/usr/bin/env python3
"""The two numbers the gate screen shows: buildings standing, people housed.

T-0036, the owner's ask of 2026-08-17 — *"on the front screen, show the number of
buildings in the city and the population, people living in their buildings"*, and the
population *"should get to the correct Chicago 1835 population number as the buildings
all complete"*.

**This is a read, not an invention.** Both numbers already exist in committed data and
neither is typed here:

* **Buildings standing** is the 665-roof programme's own standing count
  (`data/reconstruction/1835_665_roof_programme.json`, itself derived by
  `tools/reconcile_665.py` from the structure records). The programme counts PHYSICAL
  ROOFS, not records — a bridge, a pier, a palisade and a parade ground are structure
  records that are not buildings — and where a record's source reads as two or three
  cabins the ledger takes the low reading. This takes the same low reading, for the same
  reason: the two figures must not be able to disagree.
* **People housed** is `data/residents/` joined through `lives_at`. A person counts when
  the building they live in STANDS: the household's `lives_at` must name a structure that
  resolves into the scene (`data/sidecars/<year>/index.json`, which is what the renderer
  actually loads). So the number grows as the town builds out, by construction, exactly
  as the ask describes — a household whose dwelling has not been built yet is in the
  dataset and not in this count.

**Why a derived file and not a constant in the page.** `data/reconstruction`'s own
build.json lesson: a number written once by hand goes stale silently, and a stale number
on the FRONT screen is the most visible possible place to be wrong. `tools/check.sh`
re-derives this file, so a run that builds ten roofs and does not regenerate it fails at
the commit rather than shipping a town that says it is smaller than it is.

**What the numbers are NOT, stated here because the gate has no room to say it.**

* `people_housed` counts PERSON ENTRIES, and three of the entries it counts stand for
  groups nobody named — "the rest of the Beaubien household, unnamed", "Heacock's wife
  and children", "the rest of the Robinson household". Each is at least one person and
  probably several, so the figure is a FLOOR on the people this dataset houses, never a
  population estimate. `group_entries` carries the count so a reader can see the seam.
* The town's own total is 3,265 people in 398 dwellings — Andreas vol. 1, printed p. 180,
  the town census of **November** 1835, four months after the scene date. It is the town's
  recorded size and never the scene's population on 1 July; it stays in this file as the
  record it is, and the gate does NOT fill toward it (T-1365). What the gate fills toward
  is `people.scene`, below.

**`people.scene`, and why the gate needed it (T-1365).** The gate read `1,588 named
residents of roughly 3,265 who lived here`, and neither half of that sentence was sound.
The DENOMINATOR was the November count, which the note in this very file forbids reading
as the scene's population, and which the town model has since resolved to a point of 2,536
within 2,353–3,265 — so the front screen and the reconstruction programme were filling
toward two different towns. The NUMERATOR was every card in the residents index, most of
which are people the project has not established in Chicago on 1 July at all: a name on a
post-office letter list is a card, not a resident of that Tuesday. `people.scene` counts
the two ends the same way — persons in households recorded `present` on the scene date,
against the model's point for that date — and carries `cards_total` beside them so the
cards the layer holds are still stated, as cards.

**And the people it counts APART.** T-1353 mints the summer crowd of 1835 — the strangers
the Chicago American put OUTSIDE its own population estimate — as reconstructed visitors in
`data/residents/transients/`. They are not residents and they do not touch either figure
above: their cards carry no `lives_at`, they are not in the manifest this file joins, and
the `transients` block below reports them on a row of their own. Chicago's own enumerator
did the same thing in 1843, printing `Transient persons` as a separate line of his table.

    tools/town_census.py            regenerate data/town_census.json
    tools/town_census.py --check    fail if the committed file is not what the dataset
                                    re-derives
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_PATH = DATA / "town_census.json"

YEAR = "1835"

# The town census of November 1835, four months after the scene date. Andreas vol. 1,
# printed p. 180; the same pair of figures the inferred-residents programme calibrates
# against (docs/RESEARCH/residents_1835_inferred.md).
TOWN_TOTAL_PEOPLE = 3265
TOWN_TOTAL_DWELLINGS = 398
TOWN_TOTAL_SOURCE = "andreas_1884_v1"

# T-1353. The visitors, read from the ledger that mints them. Absent file, absent block:
# this census reports what the dataset carries and never a figure typed here.
TRANSIENTS = DATA / "reconstruction" / "1835_transient_persons.json"


def transient_block() -> dict | None:
    """The summer crowd, on its own row — or None while nothing has minted one.

    Counted from the ledger and cross-checked against the cards, because the whole point
    of the row is that these people are NOT in the resident join above: nothing else in
    this file would notice if the two drifted apart.
    """
    if not TRANSIENTS.exists():
        return None
    ledger = json.loads(TRANSIENTS.read_text(encoding="utf-8"))
    minted = ledger.get("minted") or []
    on_disk = 0
    housed = []
    for row in minted:
        path = DATA / "residents" / row["file"]
        if not path.exists():
            continue
        card = json.loads(path.read_text(encoding="utf-8"))
        on_disk += len(card.get("persons") or [])
        if (card.get("lives_at") or {}).get("value"):
            housed.append(card["id"])
    totals = ledger.get("totals") or {}
    point = ledger.get("the_point_adopted") or {}
    return {
        "persons": on_disk,
        "households": len(minted),
        "by_household_kind": totals.get("persons_by_household_kind", {}),
        "point_adopted": point.get("persons"),
        "point_reading": point.get("reading"),
        "bracket": [192, 900],
        "reserved_not_minted": totals.get("reserved_not_minted"),
        "counted_in_people_housed": 0,
        "claiming_a_residence": sorted(housed),
        "basis": "Reconstructed visitors of the summer of 1835 (T-1353), bounded by "
                 "data/reconstruction/1835_transient_cohort.json. They are NOT residents: "
                 "no card here names a dwelling, none is in the resident manifest, and "
                 "neither figure above moves when this one does.",
        "why_apart": "The Chicago American of 13 June 1835 put the town's population at "
                     "2,500 to 3,000 and the strangers at 'some hundreds more' — outside "
                     "its own estimate. Chicago's own enumerator printed `Transient "
                     "persons` as a row of its own in 1843. This row is that row.",
        "reserved_note": "The land-sale purchasers the register NAMES and this layer "
                         "cannot place. Slots held open, nobody drawn into them: a "
                         "reconstruction may not stand in for a person a source names.",
    }

# The town model's own figure for the scene date. The gate fills its people bar toward
# THIS and never toward the November count (T-1365): 3,265 is the high end of this
# figure's range, and `town_total_note` in this very file forbids reading it as the
# population on 1 July. The point, the range and the method all come out of the model,
# so the screen and the reconstruction programme cannot fill toward two different towns.
TOWN_MODEL_PATH = DATA / "reconstruction" / "1835_town_model.json"
SCENE_POPULATION_FIGURE = "population_on_1_july_1835"


def scene_population_figure() -> dict:
    """The town model's `population_on_1_july_1835` — point, range and method.

    A read, like everything else here. The figure is a MODEL and says so (`is_a_count`
    is false); what matters for the gate is that its point is the same number the
    reconstruction order book quotas against, and that its range is carried beside the
    point so the tooltip can say what the bar is a portion of.
    """
    model = json.loads(TOWN_MODEL_PATH.read_text(encoding="utf-8"))
    for section in model.get("sections", []):
        for figure in section.get("figures", []):
            if figure.get("figure") == SCENE_POPULATION_FIGURE:
                return figure
    raise SystemExit(
        f"TOWN CENSUS: the town model carries no `{SCENE_POPULATION_FIGURE}` figure, and "
        "the gate screen's people bar is a portion of it. Rebuild the town model.")


def group_entry_count(housed_ids: set[str]) -> int:
    """Person entries inside the housed set that stand for a GROUP, not an individual.

    `data/residents/index.json` says it in its own `_doc`: a handful of entries carry an
    unnamed wife, an unnamed family or "four children" because a source counts people it
    does not name, and they must not be read as individuals. They are counted here rather
    than dropped — each is at least one person who lived in a building that stands — and
    reported separately so the seam is visible instead of averaged away.

    The test is the entry's own `relationship` plus a name that names no one: the records
    say `household_member` for the group placeholders and `child` for the Temple four.
    """
    n = 0
    for hh_id in sorted(housed_ids):
        rec = json.loads((DATA / "residents" / "households" / f"{hh_id}.json")
                         .read_text(encoding="utf-8"))
        for person in rec.get("persons", []):
            name = str(person.get("name") or "").lower()
            if "unnamed" in name or "the four " in name:
                n += 1
    return n


def census_document() -> dict:
    programme = json.loads(
        (DATA / "reconstruction" / "1835_665_roof_programme.json").read_text(encoding="utf-8"))
    sidecars = json.loads(
        (DATA / "sidecars" / YEAR / "index.json").read_text(encoding="utf-8"))
    residents = json.loads((DATA / "residents" / "index.json").read_text(encoding="utf-8"))
    # THE PRESENCE RULINGS (T-1386). The 827 people the research left `uncertain` are
    # ruled into the town one at a time, each with the tier its own dated readings reach,
    # in data/reconstruction/1835_presence_rulings.json. They are the difference between
    # the two figures below and the file is the only place the ruling lives — the cards
    # are derived and keep the inferred `uncertain` the research wrote.
    rulings_path = DATA / "reconstruction" / "1835_presence_rulings.json"
    rulings = (json.loads(rulings_path.read_text(encoding="utf-8"))
               if rulings_path.exists() else {"rulings": []})

    in_scene = {s["id"] for s in sidecars["structures"]}
    roofs = programme["standing"]["physical_roofs"]

    housed = [h for h in residents["households"] if h.get("lives_at") in in_scene]
    housed_ids = {h["id"] for h in housed}
    people = sum(int(h["persons"]) for h in housed)
    # A household in the dataset whose dwelling is not yet built. Not an error — it is
    # the headroom the ask is about — but if it ever goes negative-shaped (a lives_at
    # naming a structure the scene does not carry) that is a broken link, so both halves
    # are reported and they must sum to the layer's own household count.
    unhoused = [h for h in residents["households"] if not h.get("lives_at")]
    dangling = sorted(h["lives_at"] for h in residents["households"]
                      if h.get("lives_at") and h["lives_at"] not in in_scene)

    # THE PEOPLE THE PROJECT HAS ESTABLISHED IN THE TOWN ON THE SCENE DATE, which is the
    # only population a figure for 1 July can be a portion of. The test is the order
    # book's Rule 3 and is the household's own `present_on_scene_date`: a card the layer
    # holds because a letter was waiting at the post office for that name is NOT a person
    # established in Chicago on 1 July, and 829 of them are not. All three grades count
    # here — unlike the order book's `known`, which excludes the reconstructed because
    # they are the order being filled; the gate is not filling an order, it is saying how
    # much of the town it can show you, and a reconstructed resident is shown.
    scene_persons = 0
    scene_households = 0
    scene_grades = {"attested": 0, "inferred": 0, "reconstructed": 0}
    for h in residents["households"]:
        if h.get("present_on_scene_date") != "present":
            continue
        scene_households += 1
        scene_persons += int(h.get("persons") or 0)
        for grade, n in (h.get("grades") or {}).items():
            if grade in scene_grades:
                scene_grades[grade] += int(n or 0)
    cards_total = int(residents["counts"]["persons"])

    # THE POPULATION OF THE TOWN, which is a different question from the one above and is
    # the one the gate screen answers (T-1386). `scene_*` counts the people a record
    # ESTABLISHES here on 1 July; this counts every person the project knows of who was in
    # the town that day — the established, plus the 827 the research left unadjudicated and
    # this project has now ruled in, each at the tier its own readings reach. The owner's
    # rule: an attested or inferred resident is in the population unless there is evidence
    # they were not, and exactly two cards are out on that evidence.
    ruled_persons = 0
    ruled_households = 0
    ruled_tiers = {"attested": 0, "inferred": 0, "reconstructed": 0}
    ruled_grades = {"attested": 0, "inferred": 0, "reconstructed": 0}
    for row in rulings.get("rulings", []):
        ruled_households += 1
        ruled_persons += int(row.get("persons") or 0)
        tier = (row.get("present_on_scene_date") or {}).get("tier")
        if tier in ruled_tiers:
            ruled_tiers[tier] += int(row.get("persons") or 0)
        for grade, n in (row.get("grades") or {}).items():
            if grade in ruled_grades:
                ruled_grades[grade] += int(n or 0)
    population_persons = scene_persons + ruled_persons
    population_grades = {g: scene_grades[g] + ruled_grades[g] for g in scene_grades}
    absences = len((rulings.get("evidenced_absences") or []))

    figure = scene_population_figure()
    point = int(figure["point"])
    low = int(figure["low"])
    high = int(figure["high"])

    return {
        "$schema_note": "DERIVED — regenerate with tools/town_census.py; tools/check.sh "
                        "re-derives it. Do not hand-edit: both figures are functions of "
                        "the committed roof programme and the committed residents "
                        "layer, and the gate screen shows them.",
        "id": f"chicago_july_{YEAR}_town_census",
        "target_date": programme["target_date"],
        "derived_by": "tools/town_census.py",
        "inputs": [
            "data/reconstruction/1835_665_roof_programme.json",
            f"data/sidecars/{YEAR}/index.json",
            "data/residents/index.json",
            "data/residents/households/",
            "data/reconstruction/1835_town_model.json",
            "data/reconstruction/1835_presence_rulings.json",
        ],
        "buildings": {
            "standing": roofs["min"],
            "target": programme["remaining"]["of_target"],
            "records_in_scene": len(in_scene),
            # A VISITOR READS THIS, on the gate figure's own tooltip, so it must not
            # quote a number the figure beside it contradicts: it said "the 665-roof
            # reconciliation" for a day after T-0032 took the total to 662.
            "basis": "Physical roofs credited by the roof reconciliation, not "
                     "structure records: a bridge, a pier, a palisade and a parade "
                     "ground are records that are not buildings.",
            "range_note": roofs["range_note"],
        },
        "people": {
            "housed": people,
            "households_housed": len(housed),
            "group_entries": group_entry_count(housed_ids),
            "households_without_a_dwelling": len(unhoused),
            "town_total": TOWN_TOTAL_PEOPLE,
            "town_total_dwellings": TOWN_TOTAL_DWELLINGS,
            "town_total_source": TOWN_TOTAL_SOURCE,
            "town_total_note": "The town census of November 1835 — four months after the "
                               "scene date — counts 3,265 people in 398 dwellings "
                               "(Andreas vol. 1, printed p. 180). Quoted as the town's "
                               "recorded size, never as the scene's population on 1 July: "
                               "it is the HIGH END of the town model's range for the scene "
                               "date, and `scene.target` below is the figure the gate "
                               "screen and the reconstruction programme both fill toward.",
            "scene": {
                "persons": scene_persons,
                "households": scene_households,
                "by_grade": scene_grades,
                "cards_total": cards_total,
                "cards_not_established": cards_total - scene_persons,
                "target": point,
                "target_low": low,
                "target_high": high,
                "target_figure": SCENE_POPULATION_FIGURE,
                "target_source": "data/reconstruction/1835_town_model.json",
                "target_method": figure["method"],
                "target_note": f"The town model's point reading for 1 July 1835 within "
                               f"{low:,}–{high:,}, and the same number the "
                               f"reconstruction order book quotas against. The November "
                               f"count of {TOWN_TOTAL_PEOPLE:,} is this range's high end, "
                               f"four months later, and is not what the scene holds.",
                "basis": "Persons in households the layer records `present` on the scene "
                         "date — the order book's Rule 3. A card the layer holds "
                         "without establishing the person in Chicago on 1 July is not "
                         "counted here; `cards_not_established` is how many those are.",
                # WHICH QUESTION THIS NUMBER ANSWERS, in one line, because the gate screen
                # shows a figure from this file and a visitor cannot ask it (T-1386 acc. 4).
                "question": "How many people does a record establish in Chicago on 1 July "
                            "1835? It is the strictest reading the layer supports and it "
                            "is NOT the town's population: it leaves out every person the "
                            "research left unadjudicated.",
                "population": {
                    "persons": population_persons,
                    "households": scene_households + ruled_households,
                    "by_grade": population_grades,
                    "question": "How many people did the project's evidence put in the "
                                "town on 1 July 1835? This is the population — the "
                                "established people plus the ones the research left "
                                "`uncertain` and T-1386 has ruled in, each at the tier "
                                "its own dated readings reach.",
                    "established": scene_persons,
                    "ruled_in": ruled_persons,
                    "ruled_in_households": ruled_households,
                    "ruled_in_by_tier": ruled_tiers,
                    "ruled_in_by_residence_grade": ruled_grades,
                    "absent_on_evidence": absences,
                    "basis": "data/reconstruction/1835_presence_rulings.json — one ruling "
                             "per household the research left `uncertain`, with the dated "
                             "reading it was reached from. An attested or inferred "
                             "resident is in the population unless there is EVIDENCE they "
                             "were not; `absent_on_evidence` is how many that is.",
                    "generated_by": "tools/rule_presence_1835.py",
                },
            },
            "basis": "Person entries in households whose `lives_at` names a structure "
                     "that resolves into the scene. A person counts when the building "
                     "they live in stands, so this grows as the town builds out.",
            "floor_note": "A FLOOR, not an estimate: some entries counted here stand for "
                          "a group a source counts but does not name (see group_entries).",
            "dangling_lives_at": dangling,
        },
        "transients": transient_block(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed census is not what the dataset re-derives")
    args = parser.parse_args()
    census = census_document()
    text = json.dumps(census, indent=1, ensure_ascii=False) + "\n"
    visitors = census.get("transients")
    if visitors and visitors["claiming_a_residence"]:
        print("TOWN CENSUS BROKEN APART\n  - a transient household claims a residence, "
              "which would count a visitor of the season among the people housed: "
              f"{', '.join(visitors['claiming_a_residence'])}")
        return 1
    if census["people"]["dangling_lives_at"]:
        print("TOWN CENSUS BROKEN LINK\n  - a household's lives_at names a structure the "
              f"scene does not carry: {', '.join(census['people']['dangling_lives_at'])}")
        return 1
    # THE GATE THE SCREEN NEEDS (T-1365). The gate card fills a bar of established
    # residents toward `scene.target`, so a target outside its own range, or a count of
    # residents that has overrun the town it is a portion of, is a bar that lies. Both
    # are cheap to check and neither can be noticed by eye on a splash screen.
    scene = census["people"]["scene"]
    if not scene["target_low"] <= scene["target"] <= scene["target_high"]:
        print("TOWN CENSUS BAD TARGET\n  - the town model's point for the scene date "
              f"({scene['target']:,}) is outside its own range "
              f"{scene['target_low']:,}-{scene['target_high']:,}, and the gate screen "
              "fills a bar toward it.")
        return 1
    if scene["population"]["persons"] > scene["target_high"]:
        print("TOWN CENSUS OVERRUN\n  - the ruled population reads "
              f"{scene['population']['persons']:,} people in the town on the scene date, "
              f"more than the town model's own ceiling of {scene['target_high']:,}. The "
              "presence rulings and the model disagree and the gate screen shows both.")
        return 1
    if scene["persons"] > scene["target_high"]:
        print("TOWN CENSUS OVERRUN\n  - the layer establishes "
              f"{scene['persons']:,} people in the town on the scene date, more than the "
              f"town model's own ceiling of {scene['target_high']:,}. One of the two is "
              "wrong and the gate screen shows both.")
        return 1
    if args.check:
        if not OUT_PATH.exists():
            print(f"TOWN CENSUS DRIFT\n  - {OUT_PATH.relative_to(ROOT)} is missing")
            return 1
        if OUT_PATH.read_text(encoding="utf-8") != text:
            print("TOWN CENSUS DRIFT\n  - data/town_census.json is not what the committed "
                  "roof programme and residents layer re-derive, and the gate screen shows "
                  "it. Re-run tools/town_census.py and commit the result alongside the "
                  "records that moved it.")
            return 1
    else:
        OUT_PATH.write_text(text, encoding="utf-8")
    visitors_line = ("" if not visitors else
                     f", and {visitors['persons']} visitor(s) counted apart")
    print(f"{'verified' if args.check else 'generated'} the town census: "
          f"{census['buildings']['standing']} buildings standing of "
          f"{census['buildings']['target']}, "
          f"{scene['population']['persons']} people in the town of "
          f"{scene['target']} modelled "
          f"({scene['persons']} of them established by a record that spans the day, "
          f"{scene['population']['ruled_in']} ruled in by T-1386), "
          f"{census['people']['housed']} of them housed{visitors_line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
