# T-0478 — resident research pass 4

## Scope

This folder is the durable, human-reviewable handoff for T-0478, the fourth fixed 75-person Chicago resident-research cohort for the 1835-07-01 scene date.

The cohort is fixed at 75 unique, named, non-reconstructed people:

- 25 established profiles
- 25 scene-date letter-list-only people
- 25 earlier/uncertain letter-list-only people

Passes 1–3 account for 225 prior reviews, so T-0478 brings cumulative reviewed coverage to **300 of 848** eligible named non-reconstructed people.

## Results

- **22 corroborated enrichments**
- **4 candidate identities / duplicate leads**, explicitly unasserted
- **49 documented no-corroboration outcomes**
- **0 pending**

A documented no-find is a research result, not evidence that the person did not exist. Name similarity, surname similarity, or regional same-name evidence alone does not resolve identity.

## Files

- `T-0478_resident_research_working.xlsx` — working research workbook with Residents, Candidates, Sources, Search_Log, and Summary sheets.
- `T-0478_resident_research.csv` — machine-readable export of the Residents sheet using the shared cohort template.
- `README.md` — this method and handoff note.

The authoritative machine-facing research records remain:

- `chicago/4d/data/research/residents/pass_04_75_cohort.json`
- `chicago/4d/data/research/residents/pass_04_findings.json`
- the stable source records named by `source_ids` under `chicago/4d/data/sources/`

The workbook/CSV use the same stable `person_id`, `household_id`, candidate IDs, and repository source IDs so later synthesis can trace every row back to the JSON and source registry.

## Research method

The pass retained the authored T-0478 search scope:

1. exact-name Chicago searches around 1835;
2. Illinois / Cook County searches around 1834–1835;
3. directories, occupations, migration and institutional histories;
4. repository-held contemporary newspapers and reference corpus;
5. regional/local histories and genealogy/index leads where they could discriminate identity.

Standard query families are recorded in the workbook and CSV. The access/review date is **2026-09-02**.

Evidence was treated conservatively:

- contemporary or near-contemporary evidence outranks later compilations;
- a waiting Chicago letter indicates postal reachability/expectation, not bodily presence;
- candidates remain `asserted: false` unless evidence bridges the external identity to the repository person by more than the name;
- competing geography is preserved as a conflict rather than normalized away;
- no-find outcomes preserve the negative search scope rather than asserting nonexistence.

## Canonical-data changes in T-0478

This research pass does **not** attempt the later corpus-wide promotion/adjudication work. That work is explicitly staged in T-0487 through T-0490.

Two already-safe household-level changes are preserved in the pass:

1. **Joseph Porthier** — dated February–March 1835 migration evidence places his removal before the 1835-07-01 scene date, so the canonical household records him absent with the exact source/reasoning.
2. **Peter Pruyne / Edmund Stoughton Kimberly** — the partnership record gains independent drug-store/medical evidence, including Kimberly's explicit 1803-04-07 birth date and related dated biographical facts.

Other corroborated findings remain research evidence for the synthesis sequence rather than being mass-promoted during T-0478 closeout.

## Candidates requiring later adjudication

The four candidate identities remain unasserted:

- E. H. Mulford ↔ possible James H. Mulford, Chicago watch/jewelry trade
- Timothy Titcomb ↔ Wheeling Township settler
- Hanibal/Hannibal Ward ↔ DuPage River valley settler
- Edson White ↔ Joliet arrival

Each candidate's supporting evidence and contradictory/limiting geography is retained in the workbook and `pass_04_findings.json`.

## Downstream sequence

The repository's final resident-research synthesis is intentionally separate:

- **T-0487** — adjudicate the full research corpus and candidates/conflicts
- **T-0488** — promote well-supported attested resident/household facts with per-attribute provenance
- **T-0489** — integrate justified inferred people/households, explicitly graded as inference
- **T-0490** — final citation, duplicate, household, occupation and coverage audit

This preserves the distinction between **research completed** and **canonical population model fully enriched**.
