#!/usr/bin/env python3
"""Derive T-0478's fixed, non-overlapping fourth 75-person research cohort.

`compact_member()` refuses a member that has left the town or gone `reconstructed` on
every path, and scopes the STRATUM tests — the flag and the presence value the stratum
is named for — to the minting path, reporting them on the gate (T-0870).
"""
from __future__ import annotations

import argparse
import json

from select_resident_research_pass_2 import ROOT, PILOT, load_people
from select_resident_research_pass_3 import (
    ESTABLISHED_IDS as PASS3_ESTABLISHED_IDS,
    PRESENT_LETTER_IDS as PASS3_PRESENT_LETTER_IDS,
    UNCERTAIN_LETTER_IDS as PASS3_UNCERTAIN_LETTER_IDS,
)

import resident_cohort_freeze as freeze

OUT = ROOT / "data/research/residents/pass_04_75_cohort.json"
PASS2 = ROOT / "data/research/residents/pass_02_75_cohort.json"

ESTABLISHED_IDS = (
    "haddock_edward", "handy_major", "mason_matthias", "maxwell_philip",
    "mckee_david", "meeker_joseph", "miller_john", "mulford_e_h",
    "murphy_john", "norton_nelson_r", "pierce_asahel", "porthier_joseph",
    "pruyne_peter", "kimberly_edmund_s", "sproat_grenville", "st_cyr_john_mary",
    "steele_ashbel", "stow_william_h", "sweet_alanson", "taylor_anson_h",
    "thomas_frederick", "walters_william", "watkins_john", "kinzie_james",
    "kinzie_robert_a",
)

PRESENT_LETTER_IDS = (
    "sewyer_edward_f", "shattick_walter", "albert_shepherd",
    "shielde_willam", "simpaon_lyman", "simpson_john_p",
    "skinner_heury_c", "smith_elded", "lymor_sorton",
    "souee_theson", "spencer_william", "spicer_charles",
    "sprague_willinm_b", "stallord_arnold", "stark_b_b",
    "stater_asa_p", "steel_richard", "stevens_issac",
    "stocking_austin", "stoel_c_ii", "stold_abraham_f",
    "strode_p_m", "strong_george", "swapp_abram",
    "swearingen_david",
)

UNCERTAIN_LETTER_IDS = (
    "doane_seth_b", "paine_seth", "wescott_seth",
    "arrowsmith_sidney", "dyer_sidney", "simmons_medad_i",
    "andress_stephen", "mack_stephen", "may_stephen",
    "stith_sherrygood", "donkin_thos_w", "barbour_timothy",
    "titcomb_timothy", "tindal_james", "tryon_david",
    "vandeventer_wm", "ewing_w_l_d", "lewin_w_y",
    "wampler_westley", "ward_hanibal", "wells_charles",
    "diggins_westley", "wheeler_orson", "white_edson",
    "whiting_henry",
)


def compact_member(index: dict, person_id: str, stratum: str,
                   drift: freeze.Membership) -> dict:
    if person_id not in index:
        raise SystemExit(f"fixed cohort member {person_id} is missing")
    household, person = index[person_id]
    if person.get("grade") == "reconstructed":
        raise SystemExit(f"{person_id}: reconstructed person is outside T-0478")
    # …and below this line the questions are about the STRATUM, not the person (T-0870).
    letter = bool(person.get("letter_list_only"))
    if stratum == "established_profile":
        drift.holds(not letter, f"{person_id}: established resident became letter-list-only")
    if stratum.startswith("letter_list_only_"):
        drift.holds(letter, f"{person_id}: postal-list person no longer marked letter_list_only")
    expected_presence = {
        "letter_list_only_present": "present",
        "letter_list_only_uncertain": "uncertain",
    }.get(stratum)
    if expected_presence:
        drift.holds(household["present_on_scene_date"]["value"] == expected_presence,
                    f"{person_id}: {stratum} presence changed")
    return {"person_id": person_id, "stratum": stratum}


def derive(drift: freeze.Membership | None = None) -> dict:
    drift = drift if drift is not None else freeze.Membership(minting=False)
    index, households = load_people()
    pilot_ids = {row["person_id"] for row in json.loads(PILOT.read_text())["people"]}
    pass2_ids = {row["person_id"] for row in json.loads(PASS2.read_text())["people"]}
    pass3_ids = (
        set(PASS3_ESTABLISHED_IDS)
        | set(PASS3_PRESENT_LETTER_IDS)
        | set(PASS3_UNCERTAIN_LETTER_IDS)
    )
    reviewed = pilot_ids | pass2_ids | pass3_ids

    people = [compact_member(index, pid, "established_profile", drift) for pid in ESTABLISHED_IDS]
    people += [compact_member(index, pid, "letter_list_only_present", drift) for pid in PRESENT_LETTER_IDS]
    people += [compact_member(index, pid, "letter_list_only_uncertain", drift) for pid in UNCERTAIN_LETTER_IDS]
    ids = [row["person_id"] for row in people]

    if overlap := reviewed.intersection(ids):
        raise SystemExit(f"T-0478 overlaps prior reviews: {sorted(overlap)}")
    if len(people) != 75 or len(set(ids)) != 75:
        raise SystemExit(f"pass four must contain 75 unique people, got {len(people)}/{len(set(ids))}")

    strata = {
        "established_profile": sum(r["stratum"] == "established_profile" for r in people),
        "letter_list_only_present": sum(r["stratum"] == "letter_list_only_present" for r in people),
        "letter_list_only_uncertain": sum(r["stratum"] == "letter_list_only_uncertain" for r in people),
    }
    expected = {
        "established_profile": 25,
        "letter_list_only_present": 25,
        "letter_list_only_uncertain": 25,
    }
    # This total counts the FROZEN `stratum` labels above rather than today's records,
    # so unlike the pilot's and passes two and three's it cannot move under the tree.
    # It is hard on every path for that reason (T-0870).
    if strata != expected:
        raise SystemExit(f"pass-four strata changed: {strata}")

    eligible = sum(
        p.get("grade") != "reconstructed"
        for h in households
        for p in h.get("persons", [])
    )
    return {
        "_doc": "T-0478's fixed fourth 75-person cohort. The compact manifest carries identity and stratum only; the selector validates current resident records.",
        "version": 1,
        "ticket": "T-0478",
        "scene_date": "1835-07-01",
        "generated_by": "tools/select_resident_research_pass_4.py",
        "population_frame": {
            "eligible_real_named_people": eligible,
            "previously_reviewed": len(reviewed),
            "sample_size": 75,
            "cumulative_reviewed": len(reviewed) + 75,
            "strata": strata,
        },
        "people": people,
    }


def stratum_probes():
    """One member through each stratum test, moved and unmoved (T-0870)."""
    def probe(stratum, flag):
        def run(drift, moved):
            index = {"probe": ({"id": "hh_probe",
                                "present_on_scene_date": {"value": "present"}},
                               {"id": "probe", "name": "A Probe", "grade": "inferred",
                                "letter_list_only": flag if moved else not flag})}
            compact_member(index, "probe", stratum, drift)
        return run
    return [
        ("an established member that became letter-list-only",
         probe("established_profile", True)),
        ("a postal-list member whose letter_list_only flag moved",
         probe("letter_list_only_present", False)),
    ]


def presence_probe(stratum: str, presence: str):
    """The presence value a letter-list stratum is NAMED for, moved on its own."""
    def run(drift, moved):
        index = {"probe": ({"id": "hh_probe",
                            "present_on_scene_date": {"value": "elsewhere" if moved else presence}},
                           {"id": "probe", "name": "A Probe", "grade": "inferred",
                            "letter_list_only": True})}
        compact_member(index, "probe", stratum, drift)
    return run


def self_test() -> int:
    return freeze.stratum_self_test("resident research pass four", stratum_probes() + [
        ("a present-list member ruled elsewhere on the scene date",
         presence_probe("letter_list_only_present", "present")),
        ("an uncertain-list member whose presence was settled",
         presence_probe("letter_list_only_uncertain", "uncertain")),
    ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    drift = freeze.Membership(minting=not args.gate and not OUT.exists())
    doc = derive(drift)
    for line in drift.report("resident research pass four"):
        print("   %s" % line)
    # T-0764: the manifest's snapshot is frozen, so the gate does not re-derive it and a
    # regeneration does not rewrite it. tools/resident_cohort_freeze.py holds both halves.
    if args.gate:
        return freeze.gate(OUT, doc, "resident research pass four")
    return freeze.write(OUT, doc, "resident research pass four: wrote 75 people (25 established, 25 present-list, 25 earlier-list)")


if __name__ == "__main__":
    raise SystemExit(main())
