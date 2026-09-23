#!/usr/bin/env python3
"""Fix cohorts 13, 14 and 15 — the named residents that have no research row.

    tools/select_resident_research_pass_13.py            (re)write the manifest
    tools/select_resident_research_pass_13.py --gate     the committed manifest is current

T-0492 fixes all three here, in one file, so that T-0508, T-0509 and T-0510 do not
edit `tools/check.sh` and the same population frame at the same moment in three
parallel runs. `_14.py` and `_15.py` are two lines each and import this.

WHAT THE FRAME ACTUALLY IS, MEASURED RATHER THAN ASSERTED. The ticket asks for 237
named people with no research row, in three cohorts of 79. The tree holds **228**,
and the arithmetic is worth writing down because the difference is not rounding:

    238  people carrying no `resident_research` block at all
     -5  unnamed placeholders ("The rest of the Beaubien household, unnamed" and
         four like it) — a count, not a person, and outside every cohort since the
         pilot
     -5  real named people whose ids and containers are `inf_*` / `hh_inf_*`
         (J. Garland, J. W. Reed, Dr. Josiah C. Goodhue, Thomas S. Eels,
         J. Shrigley), retained unplaced by T-0489. `select_resident_research_pass_5.py`
         refuses an `inf_` id outright and this follows it. They are real people and
         they are worth researching; that is a ticket, not a silent inclusion here.
    ---
    228  = 76 + 76 + 76

AND WHERE THEY COME FROM, WHICH IS THE SURPRISE. 225 of the 228 are the **pilot,
pass 2 and pass 3 cohorts** — reserved, and never researched: no findings ledger,
no reference package, no row on any person. That is T-0511's finding from the other
side. So T-0492's acceptance clause "zero overlap with passes 1-12" cannot be met
as written — the population that satisfies it is THREE PEOPLE — and the non-overlap
that carries the meaning is stated instead:

  * zero overlap AMONG 13, 14 and 15;
  * zero overlap with the 611 people who DO carry a research row, which is passes
    4-12 and the reference packages behind them.

Researching a person the pilot reserved in June and never reviewed is the work the
owner asked for. Refusing to, because a reservation exists, is how 225 people stay
unresearched for ever.

THE FRAME IS FROZEN, and deliberately. It was measured on 2026-09-03 against
`data/residents/households/*.json`, sorted inside each stratum, round-robin
interleaved across the three strata and chunked in fixed order. A person who
acquires a research row after this — which is what T-0508 to T-0510 are for — does
NOT make the manifest stale; a person who VANISHES, or turns into a placeholder,
does, and the gate says so.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import resident_cohort_freeze as freeze

ROOT = Path(__file__).resolve().parents[1]
RESIDENTS = ROOT / "data" / "residents"
RESEARCH = ROOT / "data" / "research" / "residents"

# Frozen 2026-09-03. Sorted within `established_profile`, `letter_list_only_present`
# and `letter_list_only_uncertain`, then interleaved one from each in turn, so no
# cohort is all of one stratum and the three are comparable to each other.
FRAME = (
    "adams_william_h", "aiker_samuel", "parcel_aaron",
    "bates_john_jr", "akers_simon", "reel_absolam",
    "beaubien_jean_baptiste", "allen_william", "vandorwerk_adam",
    "beaubien_josette", "allin_richard", "vaughan_alanson_b",
    "beaubien_madore", "alling_prudde", "wilkes_alexander",
    "beaubien_mark", "anderson_eli_f", "tucker_alexr_h",
    "beckford_printer", "anstin_al", "churchill_alfred",
    "blodgett_tyler_k", "archer_joseph", "vaughn_alison_b",
    "brown_lemuel", "avery_charles", "perring_almon",
    "brown_mrs_rufus", "ayres_levi", "castle_alonzo",
    "brown_rufus", "bailly_joseph", "murray_alonzo",
    "caldwell_billy", "bakwith_albert", "murry_alonzo",
    "calhoun_john", "bebee_orson", "crandal_alva",
    "carpenter_philo", "beddlecome_ash", "dunlap_alva",
    "carver_david", "beeson_william", "miner_amanda",
    "casey_edward_w", "beger_tobias", "rathburn_amos",
    "caton_john_dean", "bemis_samuel_c", "wear_amy_c",
    "church_thomas", "benton_datas_e", "miles_andrew",
    "clybourne_archibald", "benubien_charl", "vann_angeline",
    "cobb_silas_b", "bishop_j_e", "heere_anthony",
    "cohen_peter", "blair_william_g", "winsor_aram",
    "couch_ira", "bloget_josiah_i", "knox_archibald",
    "couch_james", "blood_amos", "parcell_aron",
    "davis_john", "bly_rouse", "brundage_asa",
    "davis_t_o", "boardman_elect", "doel_asa",
    "garrett_a", "boles_george", "parsalls_austin",
    "king_byram", "bostwick_e_b", "paige_b_r",
    "thrall_e_l", "bradstreet_j_p", "bailey_bennet",
    "fowler_elmira", "brookins_david", "foster_caleb",
    "clarke_h_b", "brooks_gardner", "romer_carl",
    "bennett_h_c", "brush_matthias", "drake_charles_c",
    "crocker_h", "bullen_jeduthnn", "bartlett_charles_h",
    "sherman_h", "bullock_stephen", "richards_charles_t",
    "moore_henry", "burbee_jonathan", "chapman_chas_h",
    "marshall_j_a", "burdick_paul", "house_chester",
    "curtiss_j", "butterfield_ben", "albee_clark_b",
    "collins_j_h", "byam_seth", "abbott_constant",
    "grant_james", "case_nehemiah", "parkes_curtis",
    "stewart_r", "chadwick_joseph", "torry_d_v_s",
    "lewis_samuel", "chamberlain_l_c", "dunn_dangerfield",
    "sabine_wm", "chambers_john", "ingersall_david",
    "dole_george_w", "chanpagne_batist", "frame_david_p",
    "egan_emeline", "chappel_eliza_mir", "farren_dean",
    "egan_william_b", "chase_peter", "griswold_eben",
    "elston_daniel", "clark_erastus", "alden_ebenozer",
    "fullerton_alexander", "codding_sally", "tuller_elam",
    "gale_stephen_f", "comstock_h_h", "benn_eli",
    "goss_o", "cook_rowland_i", "filer_elihu_d",
    "greene_john", "cooley_edward_v", "sen_elijah_wentworth",
    "hamilton_richard_j", "covell_thomas_r", "covalt_enos",
    "harmon_charles_l", "curtenius_fredk", "spalding_franklin",
    "harmon_elijah_d", "curtis_liman", "page_frederick_w",
    "harmon_isaac_d", "davenport_dennis", "makepiece_george_r",
    "heacock_russel_e", "demans_j_t", "legg_gregory_e",
    "hogan_john_s_c", "dement_wm", "vanderbogart_h",
    "hubbard_gurdon", "dow_albert_f", "hurlburt_hannah",
    "ingersoll_chester", "doolittle_ehjah", "eager_hiram",
    "jones_benjamin", "fairchilds_ransom", "langer_jacob",
    "kinzie_john_h", "felch_alaneon", "mcfadden_james",
    "kinzie_juliette", "force_john", "holder_jesse",
    "owen_thomas_jv", "ford_ebenezer", "musgrave_john",
    "pearsons_hiram", "galusha_ezra", "folliott_jonathan",
    "peck_philip", "gooding_caroline", "kinsey_joshua",
    "morris_b_s", "hail_aifred", "albyn_lucius_b",
    "hoit_thomas", "lorenzo_maccoy", "mvaughton_angus",
    "boyer_j_k", "mary_nelson", "cutler_morris",
    "fell_j_w", "oakley_benjamin_w", "chauncy_orange",
    "porter_eliza_chappel", "harriet_paddock", "ostrander_catherine",
    "porter_jeremiah", "win_payne", "howley_pierce",
    "robinson_alexander", "preston_stephen_ii", "westover_roy_k",
    "robinson_catherine", "saunders_william_s", "stephens_s",
    "snow_george_w", "helen_soren", "stuart_samuel",
    "spring_giles", "starkweather_robt", "renwick_theophilus",
    "taylor_augustine", "sunny_miches", "conter_willard",
    "temple_children_four", "vyekoff_henry_s", "loring_wm",
    "temple_john_t", "temple_mrs_john_t", "wright_john",

)

CHUNKS = {13: (0, 76), 14: (76, 152), 15: (152, 228)}
ORDINALS = {13: "thirteenth", 14: "fourteenth", 15: "fifteenth"}
TICKETS = {13: "T-0508", 14: "T-0509", 15: "T-0510"}

PRIOR_COHORTS = (
    "pilot_75_cohort.json",
    *("pass_%02d_75_cohort.json" % n for n in range(2, 12)),
    "pass_12_11_cohort.json",
)


def out_path(pass_no: int) -> Path:
    return RESEARCH / ("pass_%d_76_cohort.json" % pass_no)


def load_people() -> dict:
    """Every person in the tree, read from the household files themselves.

    NOT from `index.json`: on 2026-09-03 the index lists 824 households and 825
    stand on disk (`hh_adams_william_h.json` is unlisted — T-0491's finding). The
    records are the town; the index is a summary of it, and a cohort must not move
    because a summary is behind.
    """
    folded = freeze.folded_people()      # a fold is a redirect, not a deletion (T-0842)
    people = dict(folded)
    for path in sorted((RESIDENTS / "households").glob("*.json")):
        household = json.loads(path.read_text(encoding="utf-8"))
        for person in household.get("persons") or []:
            pid = person.get("id")
            if pid in people and pid not in folded:
                raise SystemExit("duplicate person id %s" % pid)
            people[pid] = (household, person)
    return people


def stratum_of(household: dict, person: dict) -> str:
    if not person.get("letter_list_only"):
        return "established_profile"
    return "letter_list_only_%s" % household["present_on_scene_date"]["value"]


def member(people: dict, person_id: str) -> dict:
    """Validate one frozen member against the records as they stand today."""
    if person_id not in people:
        raise SystemExit("frozen cohort member %s is no longer in the town" % person_id)
    household, person = people[person_id]
    if person.get("grade") == "reconstructed":
        raise SystemExit("%s: a reconstructed person is outside these cohorts" % person_id)
    if person_id.startswith("inf_") or str(household.get("id", "")).startswith("hh_inf_"):
        raise SystemExit("%s: an inf_* record is outside these cohorts" % person_id)
    name = person.get("name") or ""
    if not name or "unnamed" in name.lower():
        raise SystemExit("%s: an unnamed placeholder is outside these cohorts" % person_id)
    return {
        "household_id": household["id"],
        "person_id": person_id,
        "name": name,
        "stratum": stratum_of(household, person),
        "starting_grade": person.get("grade"),
        "starting_presence": household["present_on_scene_date"]["value"],
        "letter_list_returns": person.get("letter_list_returns", []),
        "sources": sorted(person.get("sources", [])),
    }


def researched_ids(people: dict) -> set:
    """The people a RESEARCH pass has ruled on — an adjudicated OUTCOME, not merely
    the presence of a `resident_research` key.

    T-0515's regrade writes the rule and date of a grade change into that same block
    on people no research pass has looked at. A grade moving under the owner's ladder
    is not a research row: it says nothing about who the person was, which is the
    whole of what these cohorts are selected to find out. Reading the key rather than
    the outcome would have emptied a third of the frozen frame the moment a ladder
    rung fired, which is the opposite of what freezing it was for.
    """
    return {pid for pid, (_h, p) in people.items()
            if (p.get("resident_research") or {}).get("outcome")}


def derive(pass_no: int, minting: bool = False) -> dict:
    if len(FRAME) != 228 or len(set(FRAME)) != 228:
        raise SystemExit("the frozen frame is not 228 unique people: %d/%d"
                         % (len(FRAME), len(set(FRAME))))
    people = load_people()
    lo, hi = CHUNKS[pass_no]
    ids = list(FRAME[lo:hi])
    rows = [member(people, pid) for pid in ids]

    # Zero overlap among the three, which is the collision lock T-0508 to T-0510
    # run against in parallel.
    for other, (olo, ohi) in CHUNKS.items():
        if other == pass_no:
            continue
        if overlap := set(FRAME[olo:ohi]).intersection(ids):
            raise SystemExit("cohort %d overlaps cohort %d: %s"
                             % (pass_no, other, sorted(overlap)))

    # Zero overlap with the people who already carry a research row. This is the
    # non-overlap that means something; see the module docstring for why "zero
    # overlap with passes 1-12" is not the same claim and is not made.
    #
    # IT IS A SELECTION CHECK, SO IT ONLY RUNS WHILE SELECTING. The module docstring
    # has always said this — "a person who acquires a research row after this — which
    # is what T-0508 to T-0510 are for — does NOT make the manifest stale" — and the
    # committed manifest repeats it in `selection_policy`. The code did not: `derive`
    # ran the assertion on every call, including `--gate`, so the three cohorts began
    # failing the build the moment their own tickets did the work they were selected
    # for. dev went red on 2026-09-05 when T-0510 landed and cohort 15 tripped it;
    # 13 and 14 followed as T-0508 and T-0509 landed rows of their own.
    #
    # Nothing is weakened by scoping it. FRAME is a hardcoded 228-name literal frozen
    # on 2026-09-03, so membership cannot drift between a selection and a gate — a
    # regeneration re-reads today's records for each member's `starting_*` fields and
    # cannot reshuffle who is in the cohort. `member()` still refuses a member who
    # left the town, turned into a placeholder or went `reconstructed`, on every call
    # including the gate, which is the staleness the docstring says DOES matter.
    if minting and (overlap := researched_ids(people).intersection(ids)):
        raise SystemExit("cohort %d claims people who already carry a research row: %s"
                         % (pass_no, sorted(overlap)))

    strata = {}
    for row in rows:
        strata[row["stratum"]] = strata.get(row["stratum"], 0) + 1

    reserved_by_earlier_passes = set()
    for name in PRIOR_COHORTS:
        path = RESEARCH / name
        if path.exists():
            reserved_by_earlier_passes.update(
                r["person_id"] for r in json.loads(path.read_text(encoding="utf-8"))["people"])

    return {
        "_doc": "%s's fixed %s cohort: 76 named residents carrying no research row. "
                "The manifest is a reservation and identity lock; research outcomes "
                "live in the findings ledger beside it."
                % (TICKETS[pass_no], ORDINALS[pass_no]),
        "version": 1,
        "ticket": TICKETS[pass_no],
        "scene_date": "1835-07-01",
        "generated_by": "tools/select_resident_research_pass_13.py",
        "selection_policy":
            "Frozen 2026-09-03 from data/residents/households/*.json: every named "
            "person carrying no resident_research block, excluding unnamed placeholders "
            "and inf_*/hh_inf_* records, sorted within the established / present-list / "
            "uncertain-list strata, interleaved one from each stratum in turn, and "
            "chunked 76/76/76 in fixed order. A member that later acquires a research "
            "row does not make the manifest stale; a member that leaves the town does.",
        "population_frame": {
            "named_people_without_a_research_row": 228,
            "cohort_13_14_15_sizes": [76, 76, 76],
            "sample_size": len(rows),
            "already_reserved_by_passes_1_to_12": len(
                reserved_by_earlier_passes.intersection(ids)),
            "reservation_note":
                "225 of the 228 were reserved by the pilot, pass 2 and pass 3 and never "
                "researched — no findings ledger, no reference package, no row on any "
                "person (T-0511). These cohorts research them. Overlap with a "
                "RESERVATION is intended; overlap with a completed research row is "
                "refused above.",
            "strata": strata,
        },
        "people": rows,
    }


def run(pass_no: int, argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    args = ap.parse_args(argv)
    path = out_path(pass_no)
    # Minting is the first write only, and so is the FREEZE. A later regeneration
    # re-selects nobody, because FRAME is frozen — and since T-0764 it no longer
    # refreshes each member's `starting_*` snapshot against today's records either:
    # that snapshot is what the cohort was fixed with, and rewriting it is how the
    # "came in at `inferred` on one source" reading of a finished pass was lost.
    # tools/resident_cohort_freeze.py holds both halves of the contract.
    doc = derive(pass_no, minting=not args.gate and not path.exists())
    # A member the town has since ruled a duplicate is still studied and still counted,
    # and the gate SAYS so rather than counting them in silence (T-0842).
    for line in freeze.redirected(row["person_id"] for row in doc["people"]):
        print("   redirected by a landed merge ruling: %s" % line)
    if args.gate:
        return freeze.gate(path, doc, "resident research pass %d" % pass_no)
    return freeze.write(
        path, doc,
        "resident research pass %d: wrote %d people (%s)"
        % (pass_no, len(doc["people"]),
           ", ".join("%s %s" % (v, k) for k, v in sorted(doc["population_frame"]["strata"].items()))))


if __name__ == "__main__":
    raise SystemExit(run(13))
