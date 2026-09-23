#!/usr/bin/env python3
"""Derive T-0479's fixed fifth 75-person resident-research cohort.

Pass 5 was claimed while T-0478 was still in flight. The selector retains
a frozen copy of all 75 T-0478 person ids as the historical collision lock and
keeps the claim-time population frame stable while validating current residents.

`compact_member()` refuses a member that has left the town, gone `reconstructed`,
turned into an `inf_*` hypothesis or lost its name on every path, and scopes the
STRATUM tests — the flag and the presence value the stratum is named for — to the
minting path, reporting them on the gate (T-0870).
"""
from __future__ import annotations

import argparse
import json

from select_resident_research_pass_2 import ROOT, RESIDENTS, PILOT, load_people

import resident_cohort_freeze as freeze

OUT = ROOT / "data/research/residents/pass_05_75_cohort.json"
PASS2 = ROOT / "data/research/residents/pass_02_75_cohort.json"
PASS3 = ROOT / "data/research/residents/pass_03_75_cohort.json"

# These are the only remaining non-letter-list entries that are both real and
# individually named after the pilot and passes 2-4 are claimed.  Unnamed/count
# placeholders and hypothesised inf_* people are deliberately not substituted.
ESTABLISHED_IDS = (
    "pratt_oscar", "kercheval_gholson", "kimball_walter",
    "lampman_henry_s", "hall_benjamin", "murphy_harriet",
    "taylor_charles", "temple_peter", "wright_john_s",
)

PRESENT_LETTER_IDS = (
    "dalton_edward", "damels_samuel", "darling_daniel",
    "day_ann_airs", "dean_james_l", "demotte_lenac",
    "dilbee_david_b", "dykine_elias_s", "fadhams_ddward",
    "failor_william", "fitzlugh_daniel_i", "food_alonzo_c",
    "forceman_robert_r", "humphrey_fre_lemuel", "gabbs_james_i1",
    "gariner_joseph", "gilman_eli", "glen_james_l",
    "jaines_gooding", "goodsough_harriet_m", "gordon_william",
    "gould_a_b", "green_damel_m", "david_harris",
    "harrison_caleb", "hart_edwin_c", "hartman_peter",
    "hateh_betsey", "hickcox_joseph", "holliday_william",
    "holmes_hiram", "hopkins_henry", "hugunin_leonard_c",
)

UNCERTAIN_LETTER_IDS = (
    "hasslen_daniel", "howland_daniel", "newton_daniel",
    "robian_daniel_o", "platt_daniel", "roberson_daniel",
    "ayers_david", "bigelow_david", "dickson_david",
    "groover_david", "harris_david", "dimmick_e",
    "simons_e", "conte_e_w", "rogers_edward_a",
    "coleman_edward_b", "poor_edward", "trimble_edward",
    "maynard_elias", "dix_elijah", "garton_elijah",
    "hazzard_elisha_h", "pearce_eliza", "preston_esther",
    "turner_ezekiel", "berger_f_c", "morland_f_h",
    "plumer_f", "freeman_ford", "perry_francis",
    "burlingame_geo_a", "parmlee_george_b", "gifford_hezekiah",
)

# Frozen from steward/resident-research-pass-4 at the point T-0479 was claimed.
PASS4_ESTABLISHED_IDS = (
    "haddock_edward", "handy_major", "mason_matthias", "maxwell_philip",
    "mckee_david", "meeker_joseph", "miller_john", "mulford_e_h",
    "murphy_john", "norton_nelson_r", "pierce_asahel", "porthier_joseph",
    "pruyne_peter", "kimberly_edmund_s", "sproat_grenville", "st_cyr_john_mary",
    "steele_ashbel", "stow_william_h", "sweet_alanson", "taylor_anson_h",
    "thomas_frederick", "walters_william", "watkins_john", "kinzie_james",
    "kinzie_robert_a",
)
PASS4_PRESENT_LETTER_IDS = (
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
PASS4_UNCERTAIN_LETTER_IDS = (
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
PASS4_CLAIMED_IDS = (set(PASS4_ESTABLISHED_IDS) |
                     set(PASS4_PRESENT_LETTER_IDS) |
                     set(PASS4_UNCERTAIN_LETTER_IDS))


def compact_member(index: dict, person_id: str, stratum: str,
                   drift: freeze.Membership) -> dict:
    if person_id not in index:
        raise SystemExit(f"fixed cohort member {person_id} is missing")
    household, person = index[person_id]
    if person.get("grade") == "reconstructed":
        raise SystemExit(f"{person_id}: reconstructed person is outside T-0479")
    if person_id.startswith("inf_") or household["id"].startswith("hh_inf_"):
        raise SystemExit(f"{person_id}: hypothesised inf_* person is outside T-0479")
    if "unnamed" in person.get("name", "").lower():
        raise SystemExit(f"{person_id}: unnamed placeholder is outside T-0479")
    # …and below this line the questions are about the STRATUM, not the person (T-0870).
    letter = bool(person.get("letter_list_only"))
    if stratum == "remaining_named_non_letter":
        drift.holds(not letter,
                    f"{person_id}: remaining established person became letter-list-only")
    if stratum.startswith("letter_list_only_"):
        drift.holds(letter,
                    f"{person_id}: postal-list person no longer marked letter_list_only")
    if stratum == "letter_list_only_present":
        drift.holds(household["present_on_scene_date"]["value"] == "present",
                    f"{person_id}: pass-five present stratum changed")
    if stratum == "letter_list_only_uncertain":
        drift.holds(household["present_on_scene_date"]["value"] == "uncertain",
                    f"{person_id}: pass-five uncertain stratum changed")
    return {"household_id": household["id"], "person_id": person_id, "stratum": stratum}


def derive(drift: freeze.Membership | None = None) -> dict:
    drift = drift if drift is not None else freeze.Membership(minting=False)
    index, _ = load_people()
    pilot_ids = {row["person_id"] for row in json.loads(PILOT.read_text())["people"]}
    pass2_ids = {row["person_id"] for row in json.loads(PASS2.read_text())["people"]}
    pass3_ids = {row["person_id"] for row in json.loads(PASS3.read_text())["people"]}
    prior_merged = pilot_ids | pass2_ids | pass3_ids

    people = [compact_member(index, pid, "remaining_named_non_letter", drift) for pid in ESTABLISHED_IDS]
    people += [compact_member(index, pid, "letter_list_only_present", drift) for pid in PRESENT_LETTER_IDS]
    people += [compact_member(index, pid, "letter_list_only_uncertain", drift) for pid in UNCERTAIN_LETTER_IDS]
    ids = [row["person_id"] for row in people]

    if overlap := prior_merged.intersection(ids):
        raise SystemExit(f"T-0479 overlaps merged resident research: {sorted(overlap)}")
    if overlap := PASS4_CLAIMED_IDS.intersection(ids):
        raise SystemExit(f"T-0479 overlaps claimed T-0478 work: {sorted(overlap)}")
    if len(PASS4_CLAIMED_IDS) != 75:
        raise SystemExit(f"frozen T-0478 collision lock changed size: {len(PASS4_CLAIMED_IDS)}")
    if len(people) != 75 or len(set(ids)) != 75:
        raise SystemExit(f"pass five must contain 75 unique people, got {len(people)}/{len(set(ids))}")

    strata = {
        "remaining_named_non_letter": sum(r["stratum"] == "remaining_named_non_letter" for r in people),
        "letter_list_only_present": sum(r["stratum"] == "letter_list_only_present" for r in people),
        "letter_list_only_uncertain": sum(r["stratum"] == "letter_list_only_uncertain" for r in people),
    }
    expected = {"remaining_named_non_letter": 9, "letter_list_only_present": 33,
                "letter_list_only_uncertain": 33}
    # Counted off the FROZEN `stratum` labels above rather than today's records, so it
    # cannot move under the tree and stays hard on every path (T-0870).
    if strata != expected:
        raise SystemExit(f"pass-five strata changed: {strata}")

    # The eligible frame is a claim-time property of this frozen cohort. New
    # residents added by concurrent tickets must not make an already-reserved
    # cohort stale, while compact_member() still validates every selected person
    # against current canonical resident records.
    technical_nonreconstructed = 848
    return {
        "_doc": "T-0479's fixed fifth 75-person cohort. The compact manifest carries identity and stratum only; the selector validates current resident records.",
        "version": 1,
        "ticket": "T-0479",
        "scene_date": "1835-07-01",
        "generated_by": "tools/select_resident_research_pass_5.py",
        "population_frame": {
            "technical_nonreconstructed_entries": technical_nonreconstructed,
            "merged_reviews_before_pass": len(prior_merged),
            "pass4_claimed_not_yet_merged": len(PASS4_CLAIMED_IDS),
            "prior_reviewed_or_claimed": len(prior_merged | PASS4_CLAIMED_IDS),
            "sample_size": 75,
            "cumulative_reviewed_or_claimed": len(prior_merged | PASS4_CLAIMED_IDS) + 75,
            "strata": strata,
        },
        "people": people,
    }


def self_test() -> int:
    """One member through each of pass five's stratum tests, moved and unmoved."""
    def run_one(stratum, letter, presence):
        def run(drift, _moved):
            index = {"probe": ({"id": "hh_probe",
                                "present_on_scene_date": {"value": presence}},
                               {"id": "probe", "name": "A Probe", "grade": "inferred",
                                "letter_list_only": letter})}
            compact_member(index, "probe", stratum, drift)
        return run

    def flag_probe(stratum, letter):
        """Only the flag moves; the presence value the stratum names stays put."""
        return lambda drift, moved: run_one(
            stratum, letter if moved else not letter,
            "uncertain" if stratum.endswith("uncertain") else "present")(drift, moved)

    def presence_probe(stratum, presence):
        """Only the presence value moves; the flag stays marked."""
        return lambda drift, moved: run_one(
            stratum, True, "elsewhere" if moved else presence)(drift, moved)

    return freeze.stratum_self_test("resident research pass five", [
        ("a remaining-named member that became letter-list-only",
         flag_probe("remaining_named_non_letter", True)),
        ("a postal-list member whose letter_list_only flag moved",
         flag_probe("letter_list_only_present", False)),
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
    for line in drift.report("resident research pass five"):
        print("   %s" % line)
    # T-0764: the manifest's snapshot is frozen, so the gate does not re-derive it and a
    # regeneration does not rewrite it. tools/resident_cohort_freeze.py holds both halves.
    if args.gate:
        return freeze.gate(OUT, doc, "resident research pass five")
    return freeze.write(OUT, doc, "resident research pass five: wrote 75 people (9 remaining named non-letter, 33 present-list, 33 uncertain-list)")


if __name__ == "__main__":
    raise SystemExit(main())
