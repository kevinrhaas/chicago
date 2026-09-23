#!/usr/bin/env python3
"""Derive T-0462's fixed, non-overlapping 75-person research cohort.

`member()` is shared with pass 3. It refuses a member that has left the town or gone
`reconstructed` on every path — that is staleness. A member that has moved out of the
stratum it was drawn from is the research landing instead, so its test is scoped to
the minting path and reported on the gate (T-0870); see
`resident_cohort_freeze.Membership`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import resident_cohort_freeze as freeze

ROOT = Path(__file__).resolve().parents[1]
RESIDENTS = ROOT / "data" / "residents"
PILOT = ROOT / "data" / "research" / "residents" / "pilot_75_cohort.json"
OUT = ROOT / "data" / "research" / "residents" / "pass_02_75_cohort.json"

KNOWN_IDS = (
    "bates_john_jr", "beaubien_jean_baptiste", "beaubien_josette",
    "beaubien_madore", "beaubien_mark", "caldwell_billy", "calhoun_john",
    "clybourne_archibald", "couch_ira", "hamilton_richard_j",
    "hogan_john_s_c", "kinzie_john_h", "kinzie_juliette",
    "robinson_alexander", "robinson_catherine", "owen_thomas_jv",
    "pearsons_hiram", "peck_philip", "porter_jeremiah",
    "porter_eliza_chappel", "snow_george_w", "spring_giles",
    "taylor_augustine", "temple_john_t", "wright_john",
)

PRESENT_LETTER_IDS = (
    "bailly_joseph", "chappel_eliza_mir", "dement_wm",
    "curtenius_fredk", "avery_charles", "bemis_samuel_c",
    "blood_amos", "boardman_elect", "bostwick_e_b",
    "bradstreet_j_p", "brooks_gardner", "brush_matthias",
    "burdick_paul", "case_nehemiah", "chamberlain_l_c",
    "cooley_edward_v", "cook_rowland_i", "covell_thomas_r",
    "curtis_liman", "davenport_dennis", "dow_albert_f",
    "fairchilds_ransom", "felch_alaneon", "ford_ebenezer",
    "galusha_ezra",
)

UNCERTAIN_LETTER_IDS = (
    "parcel_aaron", "parcell_aron", "murray_alonzo",
    "murry_alonzo", "foster_caleb", "house_chester",
    "tuller_elam", "ingersall_david", "filer_elihu_d",
    "drake_charles_c", "miner_amanda", "wear_amy_c",
    "vann_angeline", "knox_archibald", "brundage_asa",
    "abbott_constant", "dunn_dangerfield", "frame_david_p",
    "griswold_eben", "sen_elijah_wentworth", "covalt_enos",
    "page_frederick_w", "makepiece_george_r", "legg_gregory_e",
    "hurlburt_hannah",
)


def load_people() -> tuple[dict[str, tuple[dict, dict]], list[dict]]:
    index = json.loads((RESIDENTS / "index.json").read_text())
    households = [json.loads((RESIDENTS / row["file"]).read_text())
                  for row in index["households"]]
    people = {}
    for household in households:
        for person in household.get("persons", []):
            if person["id"] in people:
                raise SystemExit(f"duplicate person id {person['id']}")
            people[person["id"]] = (household, person)
    return people, households


def member(index: dict[str, tuple[dict, dict]], person_id: str,
           evidence: str, reason: str, drift: freeze.Membership) -> dict:
    if person_id not in index:
        raise SystemExit(f"fixed cohort member {person_id} is missing")
    household, person = index[person_id]
    if person.get("grade") == "reconstructed":
        raise SystemExit(f"{person_id}: reconstructed people are outside T-0462")
    # …and below this line the questions are about the STRATUM, not the person (T-0870).
    if evidence == "letter_list_only":
        drift.holds(bool(person.get("letter_list_only")),
                    f"{person_id}: no longer marked letter_list_only")
    if evidence == "established_profile":
        drift.holds(not person.get("letter_list_only"),
                    f"{person_id}: established stratum became letter-list-only")
    return {
        "household_id": household["id"], "person_id": person_id,
        "name": person["name"], "starting_evidence": evidence,
        "starting_grade": person["grade"],
        "starting_presence": household["present_on_scene_date"]["value"],
        "starting_occupation": (person.get("occupation") or {}).get("value"),
        "letter_list_returns": person.get("letter_list_returns", []),
        "sources": sorted(person.get("sources", [])),
        "selection_reason": reason,
    }


def derive(drift: freeze.Membership | None = None) -> dict:
    drift = drift if drift is not None else freeze.Membership(minting=False)
    index, households = load_people()
    prior = {row["person_id"] for row in json.loads(PILOT.read_text())["people"]}
    people = [member(index, pid, "established_profile",
                     "Established named resident selected to deepen an existing household profile.", drift)
              for pid in KNOWN_IDS]
    people += [member(index, pid, "letter_list_only",
                      "Distinctive or variant-rich scene-date return name selected for identity and duplicate testing.", drift)
               for pid in PRESENT_LETTER_IDS]
    people += [member(index, pid, "letter_list_only",
                      "Distinctive or variant-rich earlier-return name selected for identity and duplicate testing.", drift)
               for pid in UNCERTAIN_LETTER_IDS]
    ids = [row["person_id"] for row in people]
    if prior.intersection(ids):
        raise SystemExit(f"T-0462 overlaps T-0442: {sorted(prior.intersection(ids))}")
    if len(people) != 75 or len(set(ids)) != 75:
        raise SystemExit(f"pass two must contain 75 unique people, got {len(people)}/{len(set(ids))}")
    strata = {
        "established_profile": sum(row["starting_evidence"] == "established_profile" for row in people),
        "letter_list_only_present": sum(row["starting_evidence"] == "letter_list_only" and row["starting_presence"] == "present" for row in people),
        "letter_list_only_uncertain": sum(row["starting_evidence"] == "letter_list_only" and row["starting_presence"] == "uncertain" for row in people),
    }
    expected = {"established_profile": 25, "letter_list_only_present": 25,
                "letter_list_only_uncertain": 25}
    # Counted off today's `present_on_scene_date`, so this total moves when a presence
    # ruling lands on one member — the same event as a flag moving (T-0870). The 75
    # unique ids above are the frozen list and stay hard on every path.
    drift.holds(strata == expected, f"pass-two strata changed: {strata}")
    eligible = sum(person.get("grade") != "reconstructed"
                   for household in households for person in household.get("persons", []))
    return {
        "_doc": "T-0462's reproducible second 75-person research cohort; selection is not evidence about a person.",
        "version": 1, "ticket": "T-0462", "scene_date": "1835-07-01",
        "generated_by": "tools/select_resident_research_pass_2.py",
        "population_frame": {"eligible_real_named_people": eligible,
                             "previously_reviewed": len(prior), "sample_size": 75,
                             "cumulative_reviewed": len(prior) + 75, "strata": strata},
        "people": people,
    }


def stratum_probes(established: str, letter: str):
    """The probes pass 2, 3, 4 and 5 all run — one member, moved and unmoved."""
    def probe(stratum, flag):
        def run(drift, moved):
            index = {"probe": ({"id": "hh_probe",
                                "present_on_scene_date": {"value": "present"}},
                               {"id": "probe", "name": "A Probe", "grade": "inferred",
                                "letter_list_only": flag if moved else not flag})}
            member(index, "probe", stratum, "a probe", drift)
        return run
    return [(established, probe("established_profile", True)),
            (letter, probe("letter_list_only", False))]


def self_test() -> int:
    return freeze.stratum_self_test("resident research pass two", stratum_probes(
        "an established member that became letter-list-only",
        "a letter-list member whose letter_list_only flag moved"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    # T-0870, and T-0492 before it: minting is the FIRST write only, and the stratum
    # tests are selection checks, so they refuse then and report afterwards.
    drift = freeze.Membership(minting=not args.gate and not OUT.exists())
    doc = derive(drift)
    for line in drift.report("resident research pass two"):
        print("   %s" % line)
    # T-0764: the manifest's snapshot is frozen, so the gate does not re-derive it and a
    # regeneration does not rewrite it. tools/resident_cohort_freeze.py holds both halves.
    if args.gate:
        return freeze.gate(OUT, doc, "resident research pass two")
    return freeze.write(OUT, doc, "resident research pass two: wrote 75 people (25 established, 25 present-list, 25 earlier-list)")


if __name__ == "__main__":
    raise SystemExit(main())
