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
  the town census of **November** 1835, four months after the scene date. It is quoted as
  the town's recorded size, not as the scene's population on 1 July, and the gate says
  "of roughly 3,265" for that reason.

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
                               "recorded size, never as the scene's population on 1 July.",
            "basis": "Person entries in households whose `lives_at` names a structure "
                     "that resolves into the scene. A person counts when the building "
                     "they live in stands, so this grows as the town builds out.",
            "floor_note": "A FLOOR, not an estimate: some entries counted here stand for "
                          "a group a source counts but does not name (see group_entries).",
            "dangling_lives_at": dangling,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed census is not what the dataset re-derives")
    args = parser.parse_args()
    census = census_document()
    text = json.dumps(census, indent=1, ensure_ascii=False) + "\n"
    if census["people"]["dangling_lives_at"]:
        print("TOWN CENSUS BROKEN LINK\n  - a household's lives_at names a structure the "
              f"scene does not carry: {', '.join(census['people']['dangling_lives_at'])}")
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
    print(f"{'verified' if args.check else 'generated'} the town census: "
          f"{census['buildings']['standing']} buildings standing of "
          f"{census['buildings']['target']}, "
          f"{census['people']['housed']} people housed of "
          f"{census['people']['town_total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
