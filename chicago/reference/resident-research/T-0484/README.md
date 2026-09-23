# T-0484 — tenth 75-person real-resident research cohort

## Status

Complete research handoff for the fixed T-0484 manifest. All 75 reserved people have a dated outcome and there are no pending members.

- corroborated enrichment: **5**
- candidate identity / duplicate lead: **9**
- documented no-corroboration: **61**
- pending: **0**

## Cohort

The frozen manifest contains 75 unique real named postal-list residents:

- 31 `letter_list_only_present`
- 44 `letter_list_only_uncertain`

No reconstructed `inf_*` people or unnamed/count placeholders are included. The manifest is treated as an identity lock. This completion does not regenerate or substitute cohort membership.

## Method

Every member was checked against the repository's Chicago Democrat/newspaper identity material and resident/source registers, then against appropriate Chicago directories, digitized county/local histories, government or institutional records, and exact-name plus justified OCR/spelling-variant web searches. The standard query family was:

- `"<name>" Chicago 1835`
- `"<name>" Illinois 1834 1835`
- `"<name>" Chicago directory`
- `"<name>" genealogy occupation migration`
- justified OCR/spelling variants only where the printed form was visibly suspect

A surname or generic same-name hit is never an identity bridge. Candidate records remain explicitly unasserted when geography, dates, competing people, later chronology, or OCR uncertainty prevent a safe merge.

## Strongest findings

1. **Nicholas Boilvin** — independent 1833 Treaty of Chicago payment schedule plus multiple 1834 Chicago postal returns safely corroborate the uncommon identity and treaty-era context. This does not prove a July 1, 1835 dwelling.
2. **Noel Vasseur** — independent treaty payment schedule corroborates the uncommon identity and regional/treaty context; later Will/Kankakee geography prevents a Chicago-household inference.
3. **Mary Barrows** — retrospective early-Chicago education history independently names her in Miss Chappel's school network and boarding-house context.
4. **Martin Cleland** — later genealogy gives a specific 1834 prospecting trip to Chicago, but the family selected a future home near Niles, Michigan, so July 1835 Chicago residence is not inferred.
5. **Nathan Christy** — the unusual paired Nathan/Rumsey Christy names recur from the 1834 postal material to the 1843 Chicago directory, providing a stronger discriminator than a lone same-name match.

Nine additional records are retained as candidate identities only, including Elisha Raymond, Thomas McClintock, Hon. John Reynolds, Robert Moody, Nathan Hutchins, Oscar L. Hawley, Moritz Baumgarten, Samuel L. Selden and Starr Titus.

## Guardrails and limitations

- A waiting letter is evidence of a postal-list resident candidate under the owner's standing ruling; it is not automatically proof of a specific roof, occupation, kinship or bodily presence on July 1, 1835.
- Retrospective county histories and genealogies are used conservatively and are not allowed to override contemporary geography or chronology.
- Later directories can establish continuity leads, but later addresses/occupations are not back-projected to 1835.
- Negative searches are recorded outcomes, not proof that the person did not exist.
- No canonical household/person fields are modified by this pass. Promotion of supported facts belongs in the later adjudication/promotion sequence.
- The public cumulative payload remains at the last fully integrated baseline until the separately claimed T-0482 and T-0483 passes complete. T-0484 should only advance the cumulative total to 750 when the missing preceding passes are merged and the compiler can reconcile all ten 75-person cohorts without overlap.

## Files

- `T-0484_resident_research_working.xlsx` — human-reviewable table with one row per manifest person and evidence/candidate columns.
- `T-0484_resident_research.csv` — machine-readable export of the same 75 rows.
- `README.md` — this methods, findings and limitations note.
- `chicago/4d/data/research/residents/pass_10_findings.json` — canonical machine-readable outcome ledger.
- source records under `chicago/4d/data/sources/` — exact source IDs referenced by the workbook/CSV.

## Validation contract

The completion branch must retain exactly 75 unique manifest IDs, all 75 in `completed_person_ids`, no pending IDs, and outcome counts of 5 / 9 / 61. Every override source ID must resolve to a committed source record or an existing repository source. The completion PR targets `dev`.
