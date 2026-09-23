#!/usr/bin/env python3
"""Compile every reviewed resident-research pass into the public payload."""
from __future__ import annotations

import argparse
import json

import resident_cohort_freeze
from pathlib import Path

from select_resident_research_pass_2 import load_people
from select_resident_research_pass_5 import derive as derive_pass5_cohort

ROOT = Path(__file__).resolve().parents[1]
PASS5_COHORT = ROOT / "data/research/residents/pass_05_75_cohort.json"
PASS5_FINDINGS = ROOT / "data/research/residents/pass_05_findings.json"
OUT = ROOT / "data/residents/research_pilot.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def derive() -> dict:
    prior = load(OUT)
    cohort, findings = load(PASS5_COHORT), load(PASS5_FINDINGS)

    # T-0479 keeps a compact frozen manifest. Re-derive it against current
    # canonical resident records so a renamed/moved/deleted person cannot hide
    # behind copied display metadata — on the same freeze contract the cohort's
    # own gate uses, so a member whose stratum snapshot has moved since the freeze
    # is the research landing and not staleness (T-0764).
    fails, _moved = resident_cohort_freeze.check(
        cohort, derive_pass5_cohort(), resident_cohort_freeze.live_people())
    if fails:
        raise SystemExit("the pass-five cohort is not the frame's frozen cohort:\n  - %s"
                         % "\n  - ".join(fails))

    baseline = prior.get("reviews", [])[:300]
    tickets = prior.get("tickets", [prior.get("ticket")])
    expected_prior = ["T-0442", "T-0462", "T-0463", "T-0478"]
    if len(baseline) != 300 or tickets[:4] != expected_prior:
        raise SystemExit("expected the committed T-0442/T-0462/T-0463/T-0478 300-review baseline")

    if findings.get("status") != "complete" or findings.get("pending_person_ids"):
        raise SystemExit("T-0479 findings are not complete")

    index, _ = load_people()
    prior_ids = {r["person_id"] for r in baseline}
    cohort_ids = {p["person_id"] for p in cohort["people"]}
    if prior_ids & cohort_ids:
        raise SystemExit(f"research passes overlap: {sorted(prior_ids & cohort_ids)}")
    if set(findings.get("completed_person_ids", [])) != cohort_ids:
        missing = sorted(cohort_ids - set(findings.get("completed_person_ids", [])))
        extra = sorted(set(findings.get("completed_person_ids", [])) - cohort_ids)
        raise SystemExit(f"T-0479 completion ledger mismatch: missing={missing}, extra={extra}")
    if extras := set(findings["overrides"]) - cohort_ids:
        raise SystemExit(f"pass-five findings outside cohort: {sorted(extras)}")

    reviews = list(baseline)
    for member in cohort["people"]:
        pid = member["person_id"]
        if pid not in index:
            raise SystemExit(f"pass-five person missing from residents layer: {pid}")
        household, person = index[pid]
        name = person["name"]
        stratum = member["stratum"]
        starting_evidence = (
            "established_profile" if stratum == "remaining_named_non_letter" else "letter_list_only"
        )
        result = findings["overrides"].get(
            pid,
            {
                "outcome": "no_corroboration",
                "summary": findings["default_summary"],
                "sources": [],
                "candidates": [],
            },
        )
        if result["outcome"] not in {
            "corroborated_enrichment",
            "candidate_identity",
            "no_corroboration",
        }:
            raise SystemExit(f"{pid}: unsupported or pending research outcome {result['outcome']!r}")
        reviews.append({
            "person_id": pid,
            "household_id": household["id"],
            "name_as_recorded": name,
            "starting_evidence": starting_evidence,
            "reviewed_on": findings["reviewed_on"],
            "outcome": result["outcome"],
            "summary": result["summary"],
            "queries": result.get(
                "queries", [t.format(name=name) for t in findings["query_templates"]]
            ),
            "sources": result.get("sources", []),
            "candidates": result.get("candidates", []),
            "identity_rule": "Candidate facts remain unasserted until a source bridges the candidate to the historical record by more than name similarity.",
        })

    source_ids = {p.stem for p in (ROOT / "data/sources").glob("*.json")}
    for review in reviews:
        cited = set(review["sources"])
        for candidate in review["candidates"]:
            if candidate.get("asserted") is not False:
                raise SystemExit(f"{review['person_id']}: candidate must be explicitly unasserted")
            cited.update(candidate.get("sources", []))
        if missing := cited - source_ids:
            raise SystemExit(f"{review['person_id']}: unresolved source ids {sorted(missing)}")

    outcomes = ("corroborated_enrichment", "candidate_identity", "no_corroboration")
    counts = {k: sum(r["outcome"] == k for r in reviews) for k in outcomes}
    pass_counts = []
    for ticket, start in (
        ("T-0442", 0), ("T-0462", 75), ("T-0463", 150),
        ("T-0478", 225), ("T-0479", 300),
    ):
        review_pass = reviews[start:start + 75]
        pass_counts.append({
            "ticket": ticket,
            "size": 75,
            "counts": {k: sum(r["outcome"] == k for r in review_pass) for k in outcomes},
        })

    pass5_counts = pass_counts[-1]["counts"]
    expected_pass5 = {
        "corroborated_enrichment": 5,
        "candidate_identity": 13,
        "no_corroboration": 57,
    }
    if pass5_counts != expected_pass5:
        raise SystemExit(f"pass-five outcome census changed: {pass5_counts}")
    if findings.get("outcome_counts") != expected_pass5:
        raise SystemExit(f"pass-five findings census changed: {findings.get('outcome_counts')}")

    frame = cohort["population_frame"]
    eligible = frame.get("eligible_real_named_people", frame.get("technical_nonreconstructed_entries"))
    return {
        "_doc": "T-0442, T-0462, T-0463, T-0478, and T-0479 public resident research reviews. Candidate biographies are leads, not asserted resident facts.",
        "version": 5,
        "ticket": "T-0479",
        "tickets": ["T-0442", "T-0462", "T-0463", "T-0478", "T-0479"],
        "scene_date": "1835-07-01",
        "reviewed_on": findings["reviewed_on"],
        "cohort_size": len(reviews),
        "eligible_real_named_people": eligible,
        "counts": counts,
        "passes": pass_counts,
        "reviews": reviews,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="store_true")
    args = parser.parse_args()
    doc = derive()
    if len(doc["reviews"]) != 375 or sum(doc["counts"].values()) != 375:
        raise SystemExit("resident research must compile exactly 375 non-overlapping reviews")
    rendered = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    if args.gate:
        if not OUT.exists() or OUT.read_text() != rendered:
            raise SystemExit("data/residents/research_pilot.json is stale")
        print(f"resident research reviews: 375 current ({doc['counts']})")
    else:
        OUT.write_text(rendered)
        print(f"resident research reviews: wrote 375 ({doc['counts']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
