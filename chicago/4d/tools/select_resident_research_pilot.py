#!/usr/bin/env python3
"""Derive T-0442's fixed, stratified 75-person resident research pilot.

The named cohort is frozen so repeated research runs study the same people.  This
script still re-derives every member from the authoritative household records and
refuses reconstructed people, missing records and duplicate people.  Run with --gate
to compare the committed manifest without rewriting it.

A member who has moved OUT OF THE STRATUM it was drawn from is a different thing and
is scoped accordingly (T-0870): minting the cohort refuses it, and once the cohort is
frozen the gate counts and names it and stays green.  See
`resident_cohort_freeze.Membership`, and `select_resident_research_pass_13` for the
first selector to draw the distinction.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import resident_cohort_freeze as freeze

ROOT = Path(__file__).resolve().parents[1]
RESIDENTS = ROOT / "data" / "residents"
OUT = ROOT / "data" / "research" / "residents" / "pilot_75_cohort.json"

ESTABLISHED = (
    "hh_carpenter_philo", "hh_caton_john_dean", "hh_dole_george_w",
    "hh_egan_william_b", "hh_hubbard_gurdon",
)

# Fixed after a stratified draw: 25 names recorded present and 25 uncertain.
# All seven letter-list people for whom the corpus records sex are included; the
# rest span the source's name/OCR range.  Freezing the ids prevents a later mint
# or corrected spelling from quietly changing who received research effort.
LETTER_IDS = (
    "hh_hail_aifred", "hh_beddlecome_ash", "hh_gooding_caroline",
    "hh_benubien_charl", "hh_brookins_david", "hh_doolittle_ehjah",
    "hh_boles_george", "hh_vyekoff_henry_s", "hh_demans_j_t",
    "hh_force_john", "hh_bloget_josiah_i", "hh_lorenzo_maccoy",
    "hh_sunny_miches", "hh_anstin_al", "hh_mary_nelson",
    "hh_oakley_benjamin_w", "hh_harriet_paddock", "hh_win_payne",
    "hh_preston_stephen_ii", "hh_starkweather_robt", "hh_codding_sally",
    "hh_byam_seth", "hh_helen_soren", "hh_beger_tobias",
    "hh_saunders_william_s", "hh_vaughan_alanson_b",
    "hh_mvaughton_angus", "hh_ostrander_catherine", "hh_torry_d_v_s",
    "hh_farren_dean", "hh_benn_eli", "hh_spalding_franklin",
    "hh_vanderbogart_h", "hh_eager_hiram", "hh_langer_jacob",
    "hh_mcfadden_james", "hh_holder_jesse", "hh_musgrave_john",
    "hh_folliott_jonathan", "hh_kinsey_joshua", "hh_albyn_lucius_b",
    "hh_cutler_morris", "hh_stephens_s", "hh_chauncy_orange",
    "hh_howley_pierce", "hh_westover_roy_k", "hh_stuart_samuel",
    "hh_renwick_theophilus", "hh_conter_willard", "hh_loring_wm",
)


# Frozen for the same reason as LETTER_IDS, and it took a mint to notice they were
# not (T-0491). This stratum was DERIVED — "every richer, real named resident still
# lacking a dwelling" — which was true on the day the cohort was fixed and stopped
# being a fixed cohort the moment the layer gained another such person. PR #670 minted
# William Hanford Adams from the 1840 census bridge, the count went to 21, and the
# selection sentence below would have quietly claimed him as researched. The rule that
# drew these twenty is recorded in that sentence; the twenty are recorded here.
RICHER_UNPLACED_IDS = (
    "hh_garrett_a", "hh_king_byram", "hh_thrall_e_l",
    "hh_fowler_elmira", "hh_clarke_h_b", "hh_bennett_h_c",
    "hh_crocker_h", "hh_sherman_h", "hh_moore_henry",
    "hh_marshall_j_a", "hh_curtiss_j", "hh_collins_j_h",
    "hh_grant_james", "hh_stewart_r", "hh_lewis_samuel",
    "hh_sabine_wm", "hh_morris_b_s", "hh_hoit_thomas",
    "hh_boyer_j_k", "hh_fell_j_w",
)


def load_households() -> dict[str, dict]:
    """The layer, plus the households a landed merge ruling folded (T-0842).

    A frozen member the town has since ruled a duplicate is redirected, not deleted,
    and it resolves out of `data/residents/merged/` exactly as it stood on the day the
    merge landed. `freeze.folded_people()` carries the reasoning.
    """
    index = json.loads((RESIDENTS / "index.json").read_text())
    out = {}
    for record, _person in freeze.folded_people().values():
        if record.get("id"):
            out[record["id"]] = record
    for entry in index["households"]:
        out[entry["id"]] = json.loads((RESIDENTS / entry["file"]).read_text())
    return out


def member(hh: dict, evidence: str, reason: str) -> dict:
    person = next((p for p in hh["persons"] if p["id"] == hh["head"]), None)
    if person is None:
        raise SystemExit(f"{hh['id']}: household head is missing")
    if person.get("grade") == "reconstructed":
        raise SystemExit(f"{hh['id']}: reconstructed people are outside T-0442")
    return {
        "household_id": hh["id"],
        "person_id": person["id"],
        "name": person["name"],
        "starting_evidence": evidence,
        "starting_grade": person["grade"],
        "starting_presence": hh["present_on_scene_date"]["value"],
        "starting_occupation": (person.get("occupation") or {}).get("value"),
        "letter_list_returns": person.get("letter_list_returns", []),
        "sources": sorted(person.get("sources", [])),
        "selection_reason": reason,
    }


def check_stratum(drift, hid: str, hh: dict, stratum: str) -> None:
    """Does this frozen member still match the stratum it was DRAWN from? (T-0870)

    Not whether it is still a real, named, non-reconstructed person — `member()` and
    the freeze's own gate ask that on every path, and a member that vanishes is
    staleness. This asks the other question, whose answer moves when research lands.
    """
    person = hh["persons"][0] if hh.get("persons") else {}
    if stratum == "newspaper_profile_unplaced":
        drift.holds(hh.get("division") == "unplaced"
                    and len(hh.get("persons", [])) == 1
                    and not person.get("letter_list_only")
                    and person.get("grade") != "reconstructed",
                    f"{hid}: no longer the kind of record this stratum was drawn from")
    elif stratum == "letter_list_only":
        drift.holds(bool(person.get("letter_list_only")),
                    f"{hid}: no longer marked letter_list_only")
    else:
        raise SystemExit(f"{hid}: no stratum test for {stratum!r}")


def derive(drift: freeze.Membership | None = None) -> dict:
    drift = drift if drift is not None else freeze.Membership(minting=False)
    households = load_households()
    people: list[dict] = []

    for hid in ESTABLISHED:
        people.append(member(
            households[hid], "established_profile",
            "Established, occupationally identified resident selected for deeper household research.",
        ))

    missing = [hid for hid in RICHER_UNPLACED_IDS if hid not in households]
    if missing:
        raise SystemExit(f"pilot cohort members are no longer in the resident layer: {missing}")
    richer = [households[hid] for hid in RICHER_UNPLACED_IDS]
    for hh in richer:
        check_stratum(drift, hh["id"], hh, "newspaper_profile_unplaced")
    for hh in richer:
        people.append(member(
            hh, "newspaper_profile_unplaced",
            "Every richer, real named resident still lacking a dwelling on the day this cohort was fixed was included, not sampled; the twenty ids are frozen, so a resident minted later is not retro-claimed as researched.",
        ))

    for hid in LETTER_IDS:
        hh = households.get(hid)
        if not hh:
            raise SystemExit(f"fixed cohort member {hid} is missing")
        check_stratum(drift, hid, hh, "letter_list_only")
        people.append(member(
            hh, "letter_list_only",
            "Fixed stratified sample of the weakest-evidence cohort: 25 present and 25 uncertain, including every member whose sex was already recorded.",
        ))

    ids = [p["person_id"] for p in people]
    if len(people) != 75 or len(set(ids)) != 75:
        raise SystemExit(f"pilot must contain 75 unique people, got {len(people)}/{len(set(ids))}")
    # The 75 unique ids above are the FROZEN list and cannot move under the tree, so
    # that assertion is hard on every path. This one is not: it counts today's
    # `present_on_scene_date` values, so a presence ruling landing on one member moves
    # it — the same event as a flag moving, asked as a total rather than per person.
    letter = [p for p in people if p["starting_evidence"] == "letter_list_only"]
    status = {s: sum(p["starting_presence"] == s for p in letter)
              for s in ("present", "uncertain")}
    drift.holds(status == {"present": 25, "uncertain": 25},
                f"letter-list strata changed: {status}")

    return {
        "_doc": "T-0442's reproducible 75-person research cohort. This is a sampling manifest, not new evidence about any person.",
        "version": 1,
        "scene_date": "1835-07-01",
        "generated_by": "tools/select_resident_research_pilot.py",
        "population_frame": {
            "eligible_real_named_people": sum(
                p["grade"] != "reconstructed"
                for hh in households.values() for p in hh.get("persons", [])),
            "sample_size": 75,
            "strata": {
                "established_profile": 5,
                "newspaper_profile_unplaced": 20,
                "letter_list_only_present": 25,
                "letter_list_only_uncertain": 25,
            },
        },
        "people": people,
    }


def self_test() -> int:
    """Both strata's membership tests, fired against a member that moved (T-0870)."""
    def richer(drift, moved):
        check_stratum(drift, "hh_probe", {
            "id": "hh_probe",
            "division": "south" if moved else "unplaced",
            "persons": [{"id": "probe", "grade": "inferred"}],
        }, "newspaper_profile_unplaced")

    def letter(drift, moved):
        check_stratum(drift, "hh_probe", {
            "id": "hh_probe",
            "persons": [{"id": "probe", "letter_list_only": not moved}],
        }, "letter_list_only")

    return freeze.stratum_self_test("resident research pilot", [
        ("a richer-unplaced member that took a dwelling", richer),
        ("a letter-list member whose letter_list_only flag moved", letter),
    ])


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
    for line in drift.report("resident research pilot"):
        print("   %s" % line)
    # T-0764: the manifest's snapshot is frozen, so the gate does not re-derive it and a
    # regeneration does not rewrite it. tools/resident_cohort_freeze.py holds both halves.
    # A member the town has since ruled a duplicate is still studied and still counted,
    # and the gate SAYS so rather than counting them in silence (T-0842).
    for line in freeze.redirected(row["person_id"] for row in doc["people"]):
        print("   redirected by a landed merge ruling: %s" % line)
    if args.gate:
        return freeze.gate(OUT, doc, "resident research pilot")
    return freeze.write(OUT, doc, "resident research pilot: wrote 75 people (5 established, 20 richer unplaced, 50 letter-list)")


if __name__ == "__main__":
    raise SystemExit(main())
