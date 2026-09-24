# Resident and household evidence synthesis — 2 September 2026

T-0487 → T-0490 synthesis of the completed newspaper/letter-list sweep, resident-research cohorts and committed 1840 Chicago census work. Scene date: **1835-07-01**.

## Population layer: before → after

| Measure | Before | After |
|---|---:|---:|
| Households | 920 | 1393 |
| Person entries | 956 | 2265 |
| Attested | 823 | 410 |
| Inferred | 25 | 875 |
| Reconstructed | 108 | 980 |
| Letter-list-only flag | 727 | 736 |
| Projected residents | 0 | 721 |
| Linked to named 1840 census household | 0 | 3 |

**108 reconstructed people were retired** and 96 empty household containers removed. 5 evidence-based people/households formerly seated by the reconstructed programme were retained but made unplaced. Reconstructed building stock was abandoned as unassigned rather than deleted.

## Research adjudication

The synthesis resolved **873 unique research outcomes**: candidate: 5, candidate_identity: 117, corroborated: 55, corroborated_enrichment: 40, no_corroboration: 250, no_corroboration_yet: 406.

A post-office letter now documents a real named person considered reachable through Chicago; it is not automatic proof of Chicago residence. Independently corroborated letter-list identities are `attested`; other qualifying letter-list names are `inferred` + `projected_resident`. Candidate identities remain explicitly unasserted with evidence for/against retained.

**The owner's ratified grading ladder outranks that letter-list rule** (T-0822). 69 letter-list people carry a rung `mint_civic_residents.py --regrade` fired on the seven domains the ladder reads (T-0515, T-0699), recorded on the card as `resident_research.rule` + `regraded_on`. This pass reads one corpus — the resident-research CSVs — so the absence of a row there is a no-find in that corpus and not a finding about the poll lists, the enrolments or the press. It no longer demotes those grades, and each of those cards now carries the ladder's rule and the rule it beat in the note. New evidence still crosses the line in both directions: a corroborated research outcome promotes a ladder-graded person to `attested`.

## Profile enrichment

Structured promotion changed **2 corroborated profiles** where independent sources state usable facts (occupation, Chicago arrival year, birth-year/family evidence). Candidate-only matches never supply canonical facts.

- `hathaway_joshua` (T-0483): birth_year=1810
- `woodworth_james_h` (T-0486): birth_year=1804

## 1840 census evidence

The recovered v4 work is now retained as a complete dated census layer: **210 named 1840 household-head rows on printed pages 229–235, all with resolved IPUMS SERIALs and household demographic fields**. These records live under `data/census/1840/` whether or not they can yet be tied safely to a 1 July 1835 resident.

Canonical resident linkage is a separate assertion. There are currently **2 validated High-confidence 1835↔1840 identity bridges** — John Murphy (1840 p.233 r.30, SERIAL 5102066) and William Hanford Adams (p.229 r.9, SERIAL 5101954) — plus **1 provisional bridge**, John Miller ↔ John J. Miller (p.232 r.3, SERIAL 5102035). Miller is independently attested as the Chicago tanner and 1833 trustee, but the 1840 middle initial is new, so the link remains Medium/provisional rather than High.

**1840 is later evidence, not the 1835 household.** Household totals, children, sex structure, industry, foreigner and literacy fields are retained under the census dataset and `later_census` links for household-reconciliation research, but are not projected backward to 1 July 1835. Murphy's 1840 household has 6 people; Adams 2; Miller 5. Those counts do not themselves mint spouses, children, partners, servants or boarders into the 1835 resident layer.

The old September 2 “0 links / 29 unmatched heads” result is preserved in the machine ledger as the **legacy partial matcher** result. It came from the older pages-234/235 partial CSV plus exact normalized-name matching and did not consume the later v4 adjudication.

## Placement / structures

The retained evidence population is intentionally allowed to be unplaced. Structures that only inherited occupants from the retired reconstructed-household programme remain as anonymous/unassigned building stock for the later full placement sweep; no replacement home or workplace was invented here.
