---
id: T-0396
title: Newberry & Dole's partner is read as Oliver Newberry in 1834 and Walter L. Newberry in 1835, and the corpus cannot say which stood in the firm
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-11
pr: 1168
claimed_by: run 9/11/2026, 10:16:12 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T03:54:19.424Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34669733060
---

Newberry & Dole's partner is read as Oliver Newberry in 1834 and Walter L. Newberry in 1835, and the corpus cannot say which stood in the firm.

**Acceptance:** (stated before working, 2026-09-12)

1. The question is DECIDED for the scene date, on the corpus's own evidence and not on the
   literature's: which Newberry stood in Newberry & Dole on 1 July 1835. The argument is
   written where a reader meets the claim, not only in a research file.
2. No record in the dataset asserts at `attested` a partner the firm's own advertisement
   contradicts. Both structure records of the firm — `newberry_dole_warehouse` and
   `newberry_dole_slaughterhouse_south_branch` — carry the ruled partnership at the
   confidence the evidence actually supports, with both limbs of the argument (who is
   EXCLUDED, and who is identified) graded separately in the note.
3. `data/research/newspapers/identity.json`'s `business_newberry_dole` proprietor
   distinction stops saying the question is open and carries the answer, since that
   declaration is the place the corpus itself nominated for it.
4. Oliver Newberry remains a non-resident, and `data/residents/index.json` carries the
   stronger reason the firm's own card gives: he is its DETROIT REFERENCE, not half of it.
5. Nothing on `hh_newberry_walter_loomis` is regraded, and no trade and no premises is
   minted onto Walter L. Newberry from this ruling. Grading against every source at once
   is T-0515's pass; this one hands it a decided identity and not a verdict.
6. The WALTER S / W S finding added below is ANSWERED, with the two things that decide
   how much the reading weighs: what the deposit actually is, and how many independent
   witnesses it holds.
7. `tools/check.sh` green, the smoke parts `smoke_budget.mjs --for-diff` names green,
   `publish.sh` run in the same commit, a changelog entry shipped.


---

**ADDED BY T-1034 COHORT A, 2026-09-11 — a third Newberry the register holds, and no
volume prints him.** Adjudicating the town-lot purchaser spellings turned up that the
Public Domain Land Tract Sales register distinguishes **WALTER L** (six rows) from
**WALTER S** (six rows), and **W L** from **W S** (one row each), consistently and across
two separate sales:

- WALTER S / W S: six rows of the school-section sale of 22–24 October 1833 (blocks 5, 60,
  85, 104, 109 and 115 of section 16, $809 together) and **lot 1 of block 3 of the original
  town, 20 June 1836, $11,950** — the second-largest single lot in the whole 619.
- WALTER L / W L: six ring tracts of June 1835 and **lot 8 of block 3, the same 20 June
  1836, $8,290** — the adjacent record id to the W S row, same day, same block.

**No volume of this corpus prints a Walter S. Newberry.** Fergus 1839, Fergus 1843 and
Norris 1844 all print Walter L. / Walter Loomis and nobody else of that forename, and the
register writes a bare NEWBERRY once more besides. So either the register holds a man the
town never printed, or `S` is a misreading of `L` on twelve rows and the two "brothers"
buying adjoining lots of block 3 on one morning are one man. **This ticket already owns
the question of which Newberry the corpus is holding, so the finding is added here rather
than filed separately** (queue FILING RULE (a)). T-1034 upheld NEWBERRY W L on its middle
initial and deliberately did NOT rule on WALTER S, which the crosswalk proposes no match
for; whichever way this goes, $11,950 of the town's own ground moves with it.
