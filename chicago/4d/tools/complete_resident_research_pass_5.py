#!/usr/bin/env python3
"""Generate T-0479's durable CSV/method notes and standing gate wiring."""
from __future__ import annotations

from collections import Counter
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
MANIFEST = ROOT / "data/research/residents/pass_05_75_cohort.json"
FINDINGS = ROOT / "data/research/residents/pass_05_findings.json"
OUTDIR = ROOT.parent / "reference/resident-research/T-0479"

CANDIDATE_IDS = {
    "murphy_harriet": "cand_harriet_murphy_us_hotel",
    "dalton_edward": "cand_edward_dalton_chicago_1840",
    "jaines_gooding": "cand_james_gooding_grove",
    "gould_a_b": "cand_ambrose_b_gould_1843",
    "hateh_betsey": "cand_betsey_hatch_lasalle",
    "holliday_william": "cand_william_holliday_white_hall",
    "newton_daniel": "cand_daniel_newton_ottawa",
    "platt_daniel": "cand_daniel_platt_lisbon",
    "dimmick_e": "cand_edward_dimmick_1839",
    "poor_edward": "cand_edward_poor_homer",
    "trimble_edward": "cand_edward_trimble_geneva",
    "garton_elijah": "cand_elijah_garton_st_charles",
    "gifford_hezekiah": "cand_hezekiah_gifford_elgin",
}
EXPECTED = {
    "corroborated_enrichment": 5,
    "candidate_identity": 13,
    "no_corroboration": 57,
}
HEADERS = [
    "ticket","cohort","person_id","household_id","name_transcribed","name_normalized",
    "stratum","seed_source_id","seed_source_date","letter_list_dates","research_outcome",
    "identity_confidence","residence_confidence","household_confidence","occupation_confidence",
    "candidate_ids","proposed_birth","proposed_death","proposed_arrival_migration",
    "proposed_occupation_trade","proposed_address_property","proposed_spouse_kin",
    "proposed_civic_voter_census","proposed_household_facts","evidence_for","evidence_against",
    "source_ids","source_urls_locators","source_tiers","queries","access_dates",
    "source_limitations","recommended_data_action","notes",
]
PROPOSED = {
    "kercheval_gholson": {"civic": "named 'of Chicago' in the 1833 treaty federal-payment clause; early civic chronology"},
    "kimball_walter": {"occupation": "merchant; W. Kimball's New Store", "address": "South Water / Clark junction in 1833 advertisement"},
    "lampman_henry_s": {"migration": "then of Ann Arbor before spring-1833 Chicago brickyard work", "occupation": "brickmaker/workman at Tyler K. Blodgett's brickyard"},
    "wright_john_s": {"address": "Chicago original-town land purchases documented in the Wright papers; later dates not back-projected"},
    "hugunin_leonard_c": {"migration": "arrived Chicago 1833-08-17", "occupation": "speculator by 1839 directory"},
}


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def list_text(value) -> str:
    if not value:
        return ""
    if not isinstance(value, list):
        return str(value)
    return "; ".join(json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, dict) else str(v) for v in value)


def annotate_findings(findings: dict) -> None:
    for pid, cid in CANDIDATE_IDS.items():
        result = findings["overrides"][pid]
        candidates = result.get("candidates", [])
        if result["outcome"] != "candidate_identity" or len(candidates) != 1:
            raise SystemExit(f"{pid}: candidate shape changed")
        candidates[0]["candidate_id"] = cid


def update_source_hierarchy() -> None:
    path = ROOT / "data/research/residents/source_hierarchy.json"
    doc = load(path)
    doc["tickets"] = ["T-0442", "T-0462", "T-0463", "T-0478", "T-0479"]
    doc["reviewed_on"] = "2026-09-02"
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")


def update_check_gate() -> None:
    path = ROOT / "tools/check.sh"
    text = path.read_text()
    text = text.replace(
        "# T-0442, T-0462, T-0463, and T-0478. These reviews sit beside household facts on purpose:",
        "# T-0442, T-0462, T-0463, T-0478, and T-0479. These reviews sit beside household facts on purpose:",
    )
    old = '''step "the fourth non-overlapping 75-person research cohort is fixed" \\
  python3 tools/select_resident_research_pass_4.py --gate

step "all 300 reviewed residents have reproducible research outcomes" \\
  python3 tools/compile_resident_research_pilot.py --gate'''
    new = '''step "the fourth non-overlapping 75-person research cohort is fixed" \\
  python3 tools/select_resident_research_pass_4.py --gate

step "the fifth non-overlapping 75-person research cohort is fixed" \\
  python3 tools/select_resident_research_pass_5.py --gate

step "all 375 reviewed residents have reproducible research outcomes" \\
  python3 tools/compile_resident_research_pilot.py --gate'''
    if new not in text:
        if old not in text:
            raise SystemExit("current resident-research check block not found")
        text = text.replace(old, new)
    path.write_text(text)


def build_person_index() -> dict:
    residents = ROOT / "data/residents"
    idx = load(residents / "index.json")
    people = {}
    for entry in idx["households"]:
        household = load(residents / entry["file"])
        for person in household.get("persons", []):
            people[person["id"]] = (household, person)
    return people


def build_csv(manifest: dict, findings: dict) -> list[dict[str, str]]:
    people = build_person_index()
    source_cache = {p.stem: load(p) for p in (ROOT / "data/sources").glob("*.json")}
    rows = []
    for member in manifest["people"]:
        pid = member["person_id"]
        if pid not in people:
            raise SystemExit(f"{pid}: missing canonical resident")
        household, person = people[pid]
        result = findings["overrides"].get(pid, {
            "outcome": "no_corroboration", "summary": findings["default_summary"],
            "sources": [], "candidates": [],
        })
        candidates = result.get("candidates", [])
        source_ids = result.get("sources", [])
        locators, tiers, limitations = [], [], []
        for sid in source_ids:
            source = source_cache.get(sid)
            if not source:
                raise SystemExit(f"{pid}: unresolved source {sid}")
            locator = source.get("url", "")
            if source.get("locator"):
                locator += " — " + source["locator"]
            locators.append(f"{sid}: {locator}")
            tiers.append(f"{sid}:{source.get('tier','')}")
            if source.get("note"):
                limitations.append(f"{sid}: {source['note']}")
        queries = result.get("queries", [q.format(name=person["name"]) for q in findings["query_templates"]])
        presence = household.get("present_on_scene_date", {})
        presence_text = (
            f"{presence.get('value','')} ({presence.get('confidence','')})".strip()
            if isinstance(presence, dict) else str(presence)
        )
        occupation = person.get("occupation") or {}
        occupation_text = (
            f"{occupation.get('value','')} ({occupation.get('confidence','')})".strip()
            if isinstance(occupation, dict) else str(occupation)
        )
        proposed = PROPOSED.get(pid, {})
        outcome = result["outcome"]
        identity_confidence = {
            "corroborated_enrichment": "corroborated",
            "candidate_identity": "candidate — unasserted",
            "no_corroboration": "unresolved / no safe external match",
        }[outcome]
        action = {
            "corroborated_enrichment": "T-0487 adjudication; T-0488 attested promotion where independently supported",
            "candidate_identity": "retain candidate unasserted; resolve in T-0487 before any canonical identity change",
            "no_corroboration": "retain documented no-find; revisit only with new evidence",
        }[outcome]
        row = {h: "" for h in HEADERS}
        row.update({
            "ticket": "T-0479", "cohort": "5", "person_id": pid,
            "household_id": household["id"], "name_transcribed": person["name"],
            "name_normalized": person["name"], "stratum": member["stratum"],
            "seed_source_id": list_text(person.get("sources", [])),
            "letter_list_dates": list_text(person.get("letter_list_returns", [])),
            "research_outcome": outcome, "identity_confidence": identity_confidence,
            "residence_confidence": presence_text,
            "household_confidence": "existing canonical household; composition not re-adjudicated in T-0479",
            "occupation_confidence": occupation_text,
            "candidate_ids": "; ".join(c.get("candidate_id", "") for c in candidates if c.get("candidate_id")),
            "proposed_arrival_migration": proposed.get("migration", ""),
            "proposed_occupation_trade": proposed.get("occupation", ""),
            "proposed_address_property": proposed.get("address", ""),
            "proposed_civic_voter_census": proposed.get("civic", ""),
            "evidence_for": result["summary"],
            "evidence_against": " | ".join("; ".join(c.get("conflicts", [])) for c in candidates if c.get("conflicts")),
            "source_ids": "; ".join(source_ids), "source_urls_locators": " | ".join(locators),
            "source_tiers": "; ".join(tiers), "queries": " | ".join(queries),
            "access_dates": "2026-09-02", "source_limitations": " | ".join(limitations),
            "recommended_data_action": action, "notes": result["summary"],
        })
        rows.append(row)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    with (OUTDIR / "T-0479_resident_research.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def write_docs() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "README.md").write_text("""# T-0479 — fifth resident-research cohort

## Scope and completion

T-0479 researches the frozen fifth 75-person cohort for the 1835-07-01 scene date: 9 remaining individually named non-letter-list people, 33 scene-date postal-list people, and 33 earlier/uncertain postal-list people. The cohort is unchanged from its committed selector/manifest and does not overlap the first four passes.

All 75 members now have a resolved outcome: **5 corroborated enrichments, 13 explicitly unasserted candidate identities, and 57 documented no-corroboration outcomes. There are 0 pending members.** With passes 1–4, cumulative completed research is 375 people.

## Method

The pass searched the repository newspaper/reference corpus, Chicago directories (especially 1839 and 1843), institutional/municipal history, digitized Cook/Will/Kane/Kendall/La Salle/Greene county histories, and broad exact-name searches. OCR and spelling variants were searched when the recorded form plausibly reflected transcription error. Searches were reviewed on 2026-09-02.

An exact name is a search lead, not an identity assertion. Later Chicago directory continuity, nearby-county settlement, occupation, migration chronology, and household information were retained as candidates unless independent evidence bridged the outside record to the 1835 Chicago person. Competing geography is recorded rather than normalized away. A documented no-find is not evidence that a person did not exist.

## Key findings

The strongest new completion-stage corroboration is **Leonard C. Hugunin**: Old Settlers of Chicago proceedings give an arrival date of 17 August 1833, and the 1839 Chicago directory independently lists Leonard C. Hugunin as a speculator. The initial tranche's corroborations for Gholson Kercheval, Walter Kimball, Henry S. Lampman and John S. Wright are preserved.

Thirteen candidates remain deliberately unasserted: Harriet Murphy; Edward Dalton; James Gooding; Ambrose B. Gould; Betsey Hatch; William Holliday; Daniel Newton; Daniel Platt; Edward Dimmick; Edward Poor; Edward Trimble; Elijah Garton; and Hezekiah Gifford. Their later dates and competing geography remain visible in the CSV/workbook and findings ledger.

## Durable files

- `T-0479_resident_research.csv` — machine-readable cohort research table using the shared template.
- `T-0479_resident_research_working.xlsx` — human-reviewable workbook with Residents, Candidates, Sources, Search_Log and Summary sheets.
- `README.md` — this method, limitation and handoff note.
- `chicago/4d/data/research/residents/pass_05_findings.json` — authoritative outcome/candidate ledger.
- `chicago/4d/data/sources/*.json` — stable source records referenced by the findings.

No canonical household/person facts are promoted by this completion pass. Corroborated facts and candidates are handed to the later T-0487–T-0490 adjudication/promotion sequence.
""")
    (ROOT / "docs/RESEARCH/resident-research-pass-5.md").write_text("""# T-0479 — Fifth resident-research pass

Status: **research complete; integration pending** · reviewed 2026-09-02

The frozen fifth cohort contains 75 unique real named people: nine remaining individually named non-letter-list residents, 33 scene-date postal-list names and 33 earlier/uncertain postal-list names. All 75 now have resolved outcomes: **5 corroborated enrichments, 13 candidate identities, 57 documented no-corroboration outcomes, 0 pending**.

The initial tranche's four corroborations (Gholson Kercheval, Walter Kimball, Henry S. Lampman and John S. Wright) remain intact. Completion adds Leonard C. Hugunin, whose 17 August 1833 Chicago arrival is preserved by the Old Settlers of Chicago proceedings and whose continued Chicago presence is independently visible in the 1839 directory.

Candidate matching remained conservative. Later Chicago records for Edward Dalton, Ambrose B. Gould and Edward Dimmick are not back-projected to 1835. Northern-Illinois pioneers Daniel Newton, Daniel Platt, Edward Poor, Edward Trimble, Elijah Garton, Hezekiah Gifford, James Gooding and Betsey Hatch remain candidates because their documented geography competes with a Chicago identity and no direct postal bridge was found. William Holliday's 1834 White Hall record is retained only as a weak competing Illinois namesake. Harriet Murphy remains the initial tranche's strong but unasserted hotel-history candidate.

No household or canonical person fields are changed by this completion. The research artifacts preserve recorded spellings, candidate conflicts, source IDs/locators, query families and negative-search scope for later T-0487–T-0490 adjudication.
""")


def main() -> int:
    manifest, findings = load(MANIFEST), load(FINDINGS)
    annotate_findings(findings)
    FINDINGS.write_text(json.dumps(findings, indent=2, ensure_ascii=False) + "\n")
    update_source_hierarchy()
    update_check_gate()
    rows = build_csv(manifest, findings)
    counts = dict(Counter(row["research_outcome"] for row in rows))
    if len(rows) != 75 or counts != EXPECTED:
        raise SystemExit(f"T-0479 CSV census changed: rows={len(rows)} counts={counts}")
    if findings.get("pending_person_ids") or set(findings.get("completed_person_ids", [])) != {p["person_id"] for p in manifest["people"]}:
        raise SystemExit("T-0479 completion membership is inconsistent")
    write_docs()
    print(f"T-0479 durable text artifacts: 75 current ({counts})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
