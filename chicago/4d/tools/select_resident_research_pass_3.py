#!/usr/bin/env python3
"""Derive T-0463's fixed, non-overlapping 75-person research cohort.

The stratum tests are pass 2's `member()`, and so is their scope: refused while
minting, reported on the gate (T-0870).
"""
from __future__ import annotations
import argparse
import json

from select_resident_research_pass_2 import ROOT, RESIDENTS, PILOT, load_people, member
from select_resident_research_pass_2 import stratum_probes

import resident_cohort_freeze as freeze

OUT = ROOT / "data/research/residents/pass_03_75_cohort.json"
PASS2 = RESIDENTS.parent / "research" / "residents" / "pass_02_75_cohort.json"

ESTABLISHED_IDS = (
    "beckford_printer", "blodgett_tyler_k", "brown_lemuel", "brown_rufus",
    "brown_mrs_rufus", "carver_david", "casey_edward_w", "church_thomas",
    "cobb_silas_b", "cohen_peter", "couch_james", "davis_john", "davis_t_o",
    "egan_emeline", "elston_daniel", "fullerton_alexander", "gale_stephen_f",
    "goss_o", "greene_john", "harmon_charles_l", "harmon_elijah_d",
    "harmon_isaac_d", "heacock_russel_e", "ingersoll_chester", "jones_benjamin",
)

PRESENT_LETTER_IDS = (
    "aiker_samuel", "akers_simon", "allen_william", "allin_richard",
    "alling_prudde", "anderson_eli_f", "archer_joseph", "ayres_levi",
    "bakwith_albert", "bebee_orson", "beeson_william",
    "benton_datas_e", "bishop_j_e", "blair_william_g", "bly_rouse",
    "bullen_jeduthnn", "bullock_stephen", "burbee_jonathan",
    "butterfield_ben", "chadwick_joseph", "chambers_john",
    "chanpagne_batist", "chase_peter", "clark_erastus",
    "comstock_h_h",
)

UNCERTAIN_LETTER_IDS = (
    "reel_absolam", "vandorwerk_adam", "wilkes_alexander",
    "tucker_alexr_h", "churchill_alfred", "vaughn_alison_b",
    "perring_almon", "castle_alonzo", "crandal_alva", "dunlap_alva",
    "rathburn_amos", "miles_andrew", "heere_anthony", "winsor_aram",
    "doel_asa", "parsalls_austin", "paige_b_r", "bailey_bennet",
    "romer_carl", "bartlett_charles_h", "richards_charles_t",
    "chapman_chas_h", "albee_clark_b", "parkes_curtis",
    "alden_ebenozer",
)

def derive(drift: freeze.Membership | None = None) -> dict:
    drift = drift if drift is not None else freeze.Membership(minting=False)
    index, households = load_people()
    # The compiled payload grows when this pass is added, so its review list cannot
    # be used as the prior set. Read the two fixed manifests that predate T-0463.
    reviewed = ({row["person_id"] for row in json.loads(PILOT.read_text())["people"]}
                | {row["person_id"] for row in json.loads(PASS2.read_text())["people"]})
    people = [member(index, pid, "established_profile",
                     "Established named resident selected to deepen an existing household profile.", drift)
              for pid in ESTABLISHED_IDS]
    people += [member(index, pid, "letter_list_only",
                      "Distinctive or variant-rich scene-date return selected for identity and duplicate testing.", drift)
               for pid in PRESENT_LETTER_IDS]
    people += [member(index, pid, "letter_list_only",
                      "Distinctive or variant-rich earlier return selected for identity and duplicate testing.", drift)
               for pid in UNCERTAIN_LETTER_IDS]
    ids = [row["person_id"] for row in people]
    if overlap := reviewed.intersection(ids):
        raise SystemExit(f"T-0463 overlaps prior reviews: {sorted(overlap)}")
    if len(people) != 75 or len(set(ids)) != 75:
        raise SystemExit(f"pass three must contain 75 unique people, got {len(people)}/{len(set(ids))}")
    strata = {
        "established_profile": sum(r["starting_evidence"] == "established_profile" for r in people),
        "letter_list_only_present": sum(r["starting_evidence"] == "letter_list_only" and r["starting_presence"] == "present" for r in people),
        "letter_list_only_uncertain": sum(r["starting_evidence"] == "letter_list_only" and r["starting_presence"] == "uncertain" for r in people),
    }
    expected = {"established_profile": 25, "letter_list_only_present": 25,
                "letter_list_only_uncertain": 25}
    # Counted off today's presence values, so it moves for the same reason a flag does
    # (T-0870). The frozen id lists above stay hard on every path.
    drift.holds(strata == expected, f"pass-three strata changed: {strata}")
    eligible = sum(p.get("grade") != "reconstructed" for h in households for p in h.get("persons", []))
    return {"_doc": "T-0463's reproducible third 75-person research cohort; selection is not evidence about a person.",
            "version": 1, "ticket": "T-0463", "scene_date": "1835-07-01",
            "generated_by": "tools/select_resident_research_pass_3.py",
            "population_frame": {"eligible_real_named_people": eligible,
                                 "previously_reviewed": len(reviewed), "sample_size": 75,
                                 "cumulative_reviewed": len(reviewed) + 75, "strata": strata},
            "people": people}

def self_test() -> int:
    return freeze.stratum_self_test("resident research pass three", stratum_probes(
        "an established member that became letter-list-only",
        "a letter-list member whose letter_list_only flag moved"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    drift = freeze.Membership(minting=not args.gate and not OUT.exists())
    doc = derive(drift)
    for line in drift.report("resident research pass three"):
        print("   %s" % line)
    # T-0764: the manifest's snapshot is frozen, so the gate does not re-derive it and a
    # regeneration does not rewrite it. tools/resident_cohort_freeze.py holds both halves.
    if args.gate:
        return freeze.gate(OUT, doc, "resident research pass three")
    return freeze.write(OUT, doc, "resident research pass three: wrote 75 people (25 established, 25 present-list, 25 earlier-list)")


if __name__ == "__main__":
    raise SystemExit(main())
