# T-0462 — resident research pass 2

## Scope

This folder is the durable, human-reviewable handoff for **T-0462**, the pass 2
cohort of the Chicago resident-identity programme, for the 1835-07-01 scene date. It was
written by `tools/export_resident_research_package.py` from the committed records the pass
already left, and it asserts nothing they do not: no outcome is altered here and no person
is minted here.

The cohort is fixed at 75 unique, named, non-reconstructed people:

- 25 established profile
- 25 letter list only present
- 25 letter list only uncertain

Of an eligible population of 1362 named non-reconstructed people, 75 had been
reviewed before this pass and 150 after it.

## Results

- **27 corroborated enrichments**
- **23 candidate identities / duplicate leads**, explicitly unasserted
- **25 documented no-corroboration outcomes**
- **0 pending**

Reviewed 2026-09-01. A documented no-find is a research result, not evidence that the
person did not exist. An exact name is a search lead, not an identity assertion: a candidate
is bridged to the 1835 Chicago record by more than name similarity, or it stays a candidate.

## Confidence rules

Every row carries the outcome the review payload records and the confidence the canonical
record carries, side by side, and never a promotion of one into the other:

- `research_outcome` — `corroborated_enrichment`, `candidate_identity` or `no_corroboration`,
  as the pass resolved it.
- `identity_confidence` — the same judgement in words; `candidate — unasserted` never means
  the identity was accepted.
- `residence_confidence`, `occupation_confidence` — the household's and person's own
  `{value, confidence}` sidecars as they stand in the residents layer, not this pass's opinion.
- `household_confidence` — composition was not re-adjudicated by a research pass.

Competing geography, later-dated records and rejected leads are kept in the Candidates sheet
with their conflicts rather than normalized away.

## Files

- `T-0462_resident_research.csv` — machine-readable Residents table on the shared
  template header (`../cohort_research_template.csv`).
- `T-0462_resident_research_working.xlsx` — working workbook: Residents, Candidates,
  Sources, Search_Log and Summary sheets. Written when `openpyxl` imports.
- `README.md` — this note.

Counts in this package: 75 residents, 23 candidate rows, 48 sources,
225 logged searches.

## The records this is derived from

- `chicago/4d/data/research/residents/pass_02_75_cohort.json` — the frozen cohort manifest, re-derived
  by `tools/select_resident_research_pass_2.py --gate`.
- `chicago/4d/data/residents/research_pilot.json` — the public review payload holding this
  pass's outcomes, summaries, queries, sources and candidates; re-derived by
  `tools/compile_resident_research_pilot.py --gate`.
- `chicago/4d/data/research/residents/pass_02_findings.json` — the pass's authoritative outcome/candidate ledger.
- `chicago/4d/docs/RESEARCH/resident_identity_pass_02_75.md` — the pass's narrative dossier.
- `chicago/4d/data/sources/*.json` — the stable source records the rows cite.

`python3 tools/export_resident_research_package.py T-0462 --check` re-derives this folder
and fails if it has drifted from those records; `tools/check.sh` runs it.

## Unresolved

The 23 candidate identities are unresolved by design and are handed to the
T-0487–T-0490 adjudication sequence, not promoted here. The 25 no-corroboration
outcomes are receipts of a bounded search, revisited only when new evidence arrives.
