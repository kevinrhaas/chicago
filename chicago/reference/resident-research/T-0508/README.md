# T-0508 resident-research handoff

Cohort 13 of the three T-0492 froze out of the 237 named residents carrying no research row.
Frozen manifest: `chicago/4d/data/research/residents/pass_13_76_cohort.json` (76 people —
26 `established_profile`, 25 `letter_list_only_present`, 25 `letter_list_only_uncertain`).

Reviewed 2026-09-05: **76/76 complete; 26 corroborated, 16 candidate identities retained
unasserted, 34 documented no-corroboration outcomes, 0 pending**.

## Artifacts

- `T-0508_resident_research.csv` — machine-readable export, one row per manifest member.
- `T-0508_resident_research_working.xlsx` — the same table plus a `Search_Log` sheet, one
  row per person reviewed (76 log rows against 76 people).
- `chicago/4d/data/research/residents/pass_13_findings.json` — the authoritative ledger.
- No new source record was minted. Every `source_id` cited here already resolves under
  `chicago/4d/data/sources/`.

## Method

The sweep is a **whole-corpus** one, and it is reproducible rather than recollected. Every
committed text and every string in every committed JSON under `chicago/4d/data/research/`
and `chicago/4d/data/sources/` — 775 documents — was loaded once, and each of the 76 names
was run against all of it as an exact given-name-plus-surname pattern (allowing up to two
intervening middle names or initials, and the inverted `Surname, Given` form the directories
print). That is the corpus the project actually holds: the post-office and newspaper
extractions, the 1833–1835 poll, tax and voter rolls, Fergus's Chicago directories of 1839
and 1843, Norris's of 1844 and every crosswalk built on them, the 1830 Peoria/Putnam schedule
leaves and the 1840 census readings, the St Mary's and St Cyr registers, the land-sale
entries, the Newberry family-history index leads, the digitised books (Andreas, Hurlbut,
Fergus's Historical Series, Hubbard) and the transcribed county histories.

A hit was then read, and it counted only if it was **independent of the post-office lists**,
which are what most of this cohort already stands on. `chicago_democrat_1833_1835` and
`chicago_american_1835` are therefore excluded from the corroboration test by the
synthesizer itself, and this pass does not argue with that.

**Recorded negatives are the bulk of the result, and they are not silence.** Where the only
independent reach was a surname, that surname had almost always already been ruled on by a
committed crosswalk — *"the surname 'Ayres' stands in the 1837 poll and no man under it
carries the initial 'L'"*. Those refusals are cited in `evidence_against` rather than
restated as fresh findings, because they are this project's own prior rulings and the honest
outcome is that they still hold.

**What was not swept.** No new web retrieval was performed. FamilySearch and Ancestry are
login-walled and were recorded as inaccessible by earlier passes, never as absent;
HathiTrust page views return 403. Eight of the candidate rows below rest on tier-3/tier-4
sources that T-0462 and T-0463 had already retrieved and committed for these very people —
the sources existed, and the rows that should have quoted them never got written. That gap
is precisely what T-0511 describes and what this cohort closes for its 76.

## Confidence rules

Unchanged from T-0486 and the programme README. Same-name hits remain **candidates** unless
date, place, occupation, kinship or another independent discriminator bridges the source to
the 1835 person. A candidate is written down and left unasserted. Negative searches are
documented negatives, not proof of nonexistence. Nothing here promotes a grade by hand;
`tools/synthesize_resident_research.py` applies the programme's own rule to the outcomes.

## The results worth naming

- **Joseph Bailly** is the clearest candidate and the clearest warning. The American Fur
  Company trader licensed for Lake Michigan in 1821 died at Baillytown, Indiana on 21
  December 1835 — Fergus's own death notices print it. A letter waiting for him at the
  Chicago post office is exactly what a trader who collected mail there would leave behind,
  and it is not a Chicago residence. Retained unasserted.
- **William Allen** and **Charles Avery** are reached by real Chicago doors — Fergus 1839's
  saloon on North Canal street and its lumber dealer at LaSalle and South Water — and both
  stay candidates, because this project's directory policy holds that an 1839 entry never
  attests 1835 presence.
- **Three pairs of manifest members are one letter apart in the same list family**: Aaron
  Parcel / Aron Parcell, Alanson B. Vaughan / Alison B. Vaughn, Alonzo Murray / Alonzo
  Murry. Each pair is recorded as a shared candidate and **not** collapsed: merging them
  would mint the man they merged into. This is a reading of the letter lists themselves and
  belongs to whoever next audits them.
- **Beckford**, who had no independent reach under his own bare surname, is corroborated by
  `chicago_antiquities_pratt` — the 1833 printing-press passage that names Oscar Pratt and
  Beckford together — which is why the town's printer keeps his trade.

## Unresolved

- The 16 candidates are unasserted by design and none of them should be promoted without a
  direct bridge to the 1834–35 postal entry.
- The three duplicate pairs need a ruling from the letter lists, not from this pass.
- 34 people end with a documented no-corroboration outcome. That is the honest shape of a
  town three quarters of whose people are a name on a post-office list (L214).
