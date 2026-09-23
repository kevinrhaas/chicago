# T-0462 — second identity-research pass for 75 real named residents

## Scope and reproducibility

This pass reviews the next 75 of 848 eligible attested or inferred named people and
does not overlap T-0442. It excludes reconstructed people. The fixed sample contains
25 established profiles, 25 names from the 1 July 1835 post-office return and 25
earlier letter-list names. `tools/select_resident_research_pass_2.py` re-derives the
cohort and refuses overlap, reconstruction, missing people or stratum drift.

Six parallel research streams combined exact-name searches with Chicago, date,
occupation, office, spouse, migration and spelling/OCR variants. They searched the
repository corpus, contemporary statutes, a Supreme Court report and city directory,
institutional biographies and finding aids, edited documentary projects, digitized
county histories, memoirs, church histories and broad indexes. Indexes and trees were
discovery aids only. Every cited source has its own record in `data/sources/`; exact
queries, outcome and conflict text are retained in `pass_02_findings.json` and the
compiled public review.

## Results

| outcome | pass two | cumulative | meaning |
|---|---:|---:|---|
| corroborated enrichment | 27 | 31 | identity resolved by more than name and a source adds or corrects a fact |
| candidate identity | 23 | 30 | useful match, duplicate or rejection retained but never merged |
| no corroboration | 25 | 89 | no safe bridge found in the reviewed surfaces; not evidence of nonexistence |
| **total** | **75** | **150** | **17.7% of 848 eligible real named people** |

The established-profile half produced the clearest gains. The 1843 directory extends
John Bates Jr.'s exact-name auction trade; *Wilcox v. Jackson* gives Jean Baptiste
Beaubien's 28 May 1835 Cook County land payment; the edited 1835 incorporation act
names John S. C. Hogan as a trustee; Papers of Abraham Lincoln records sharpen Giles
Spring's and John Harris Kinzie's migration chronologies. Institutional sources also
add sourced household relationships for the Beaubien, Robinson, Kinzie and Owen
families. Conflicts remain visible: Billy Caldwell's westward-removal year, Robinson's
birth and arrival chronology, Temple's addresses, Snow's balloon-frame attribution,
and Hiram Pearsons's sourced house-painter trade versus the prior interpretive
“speculator” label.

## Candidate identities, duplicates and geography

The postal lists show why a letter is not a body count. Strong candidates place Ezra
Galusha at Warrenville, George R. Makepeace near Joliet, Paul Burdick at Milwaukee,
Thomas R. Covell at Salt Creek and Chester House at House's Grove. The Chicago post
office made them reachable; it does not establish physical presence in the town on 1
July 1835. Those biographies therefore remain unasserted candidates.

Three duplicate tests are retained rather than silently resolved:

- `chappel_eliza_mir` is probably Eliza Chappel Porter, with “Mir” likely a bad
  reading of “Miss,” but the original 1 July column must be inspected before merge.
- Aaron Parcel/Aron Parcell and Alonzo Murray/Murry are reciprocal spelling-variant
  candidates without an external bridge.
- Ebenezer Ford has a strong Fort Dearborn/church candidate and an omitted 20 May 1835
  return that needs a household-data correction ticket; the church roster alone does
  not equate him with the July addressee.

Printed numerals beside Amanda Miner and Ezra Galusha count letters, not people.
Reprinted or OCR-variant Filer and Drake lines likewise do not create additional people.
No heritage, ethnicity, lineage, immigration origin, spouse or occupation was inferred
from a surname.

## Limits and continuation

Many civil and church records are unindexed or image-only. A no-find records this
pass's limits, not an exhaustive proof. The next pass should begin with image-level
newspaper checks for Eliza Chappel, Amy C. Wear/Were/Ware, Frederick Page and Felch;
then use Cook, DuPage, Will, Kane, La Salle and Milwaukee land, probate, marriage,
naturalization and church registers to adjudicate the strongest regional candidates.
Common names should not advance without two independent discriminators.

The public payload remains separate from authoritative household claims at
`data/residents/research_pilot.json`. `tools/compile_resident_research_pilot.py`
validates non-overlap, source resolution and explicit `asserted: false` candidates and
publishes all 150 reviews by stable person id.
