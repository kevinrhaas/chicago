# T-0509 resident research package — cohort 14

Completed 2026-09-05 for the frozen fourteenth cohort: 76 of the 228 named people in
`data/residents/` who carried no research row (`pass_14_76_cohort.json`, frozen by T-0492).

## What this pass did, and what it deliberately did not do

It read no new volume. The owner's instruction of 2026-09-04 is that the bottleneck is
SPENDING, not reading, and this cohort proved it: every one of the 76 already stood in
adjudicated evidence somewhere in the repository, and 23 of them had been *read* by the
pilot, pass 2 and pass 3 — a Whiteside County biography, a Du Page county history, a
Buffalo directory, the Chicago History Museum's Bartlett diaries, a UIUC finding aid —
by passes that then closed without ever completing a findings ledger (T-0511). Thirteen
of those readings are carried into this ledger verbatim, attributed and dated to the
pass that made them; one (`brookins_david`) was recovered from its source record alone.

The sweep behind the rest is mechanical and reproducible: an exact-name and
justified-initial-variant pass over 936 files of `data/sources/`, `data/research/` and
`chicago/reference/`, then every record in thirteen crosswalks that names a cohort
person by stable id — the four civic lists (T-0493), Fergus 1839 and the 1837 election
return printed in it, Fergus 1843, Norris 1844 and its advertising cards, the
old-settler death notices, the 1840 census heads and their ruled bridge candidates, the
Newberry index leads, the newspaper register, the directory spend crosswalk and the
address back-projection.

## The rule, stated before the work

| rule | outcome | what it takes |
|---|---|---|
| R2 | `corroborated` | a `matched` entry on the 1833 tax list or the 1833/1834/1835 poll lists — contemporary with the scene and independent of the post office |
| R1 | `corroborated_enrichment` | an identification in a source not already on the person's record whose printed forename expands the resident's own with no conflicting element; carried as evidence of its own date |
| R3 | `candidate_identity` | surname plus one initial, a conflicting forename, an ambiguous/contested/lead ruling, or a same-name regional person with no dated Chicago bridge — unasserted |
| R4 | `no_corroboration` | refusals only, or nothing beyond the 1835 post-office return |

A newspaper-register row is enrichment, not corroboration, when the paper is already the
person's seed source: the Chicago Democrat cannot corroborate a man it is the sole
witness to. That single clause is what keeps five well-known townspeople —
Mrs. H. Sherman the dressmaker, O. Goss, Emeline Egan among them — at R4 rather than
being lifted by their own seed.

## Outcome summary

- 76 of 76 manifest members carry a dated outcome; `pending_person_ids` is empty
- 8 `corroborated` · 14 `corroborated_enrichment` · 32 `candidate_identity` ·
  22 `no_corroboration`
- 51 of the 150 ids on `letter_list_missing_research_row` are closed by this cohort
- 76 Search_Log rows for 76 people reviewed

**Corroborated on the town's own rolls (R2):** Gardner Brooks, George W. Dole, Dr William
Bradshaw Egan, Alexander N. Fullerton, Stephen F. Gale, James Grant, Richard Jones
Hamilton, Charles Loomis Harmon.

**Identified in a later record (R1):** Bennet Bailey, Chas. H. Chapman, H. B. Clarke,
J. H. Collins, H. Crocker (Hans Crocker), James Curtiss, Daniel Elston, J. A. Marshall
(James A. Marshall), Henry Moore, Wm. Sabine, Elijah Wentworth sen., R. Stewart (Royal
Stewart), E. L. Thrall (Edward L. Thrall), Elam Tuller.

## Rulings this pass made against a crosswalk

Four crosswalk "matches" are REFUSED here, because a folding rule cannot see a printed
forename and this pass can:

- `albee_clark_b` — Fergus 1839 prints **Cyrus P. Albee**, not Clark B. Albee.
- `chadwick_joseph` — the 1837 return prints **J. W. Chadwick**; the resident carries no
  middle initial, so the W. is unsupported rather than agreeing.
- `clarke_h_b` — the old-settler notice is **Dr. Henry Clarke**, died Walworth, Wisconsin,
  a doctor rather than a hardware merchant. A different man.
- `marshall_j_a` — the old-settler notice is **James Monroe Marshall**, aged 45-9 at his
  1880 death, which would make him an infant in the scene.

Two upgrades run the other way, and both are honest consequences of evidence that landed
after the pass which first looked: Gardner Brooks (pass 2 had only a Des Plaines
settlers' history and called it a candidate; the 1834 poll list, read by T-0493 later,
prints his uncommon forename whole) and Bennet Bailey (pass 3 saw only an 1843
directorship over a nine-year gap; the 1837 election return closes most of it).

## What this changes in the town: nothing, yet

No household, roof, occupation, kinship, address or grade is promoted here. Candidate
identities stay unasserted, negative searches are recorded as negative searches, and
`ladder_note` on every row says which rule decided it so that a later pass can argue with
it. T-0513 consolidates and T-0514/T-0515 apply.

**Measured, for the pass that applies it:** re-deriving
`tools/synthesize_resident_research.py` against this completed ledger moves 12 people out
of `attested` and 60 into `projected_resident`, because a letter-list-only person who now
carries a *documented* no-corroboration reads differently from one who was never
reviewed. That is a grade movement, this ticket forbids grade movement, and so the
synthesis write is NOT run here — the numbers are reported for T-0515 to rule on.
The 459-file drift underneath that write is pre-existing on `dev` and unrelated to this
cohort; it is filed as **T-0720**, with the measurement and with the reason `--check`
cannot see it.

Files:
- `T-0509_resident_research.csv` — machine-readable outcome export, one row per person
- `T-0509_resident_research_working.xlsx` — Cohort, Search_Log and Method sheets
- repository `data/research/residents/pass_14_findings.json` — the completion ledger
- repository `chicago/4d/tools/complete_resident_research_pass_14.py` — the generator;
  `--check` re-derives the ledger and refuses a source_id that does not resolve
