---
id: T-1008
title: The ninety-two lines of the 1 January 1834 letter list the crops never carried are read but unminted, and the 97 residents minted from it are a floor of a 170-name return
state: split
epic: PAPERS
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-10
closed: 2026-09-10
pr: null
claimed_by: run 9/10/2026, 7:08:32 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T00:17:59.827Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34544959894
---

T-0424 read the page image and counted the printed list: **170 lines**, in
`data/research/newspapers/letter_list_1834_01_01_printed.json`. Two things follow that it
deliberately did not do, because minting is a different decision from reading.

**1. THE COHORT IS A FLOOR.** T-0310 minted **97 residents** from the 1834-01-28 printing
under owner ruling 1 (a listed name mints a resident candidate). That printing is one of
nine impressions of ONE return, and the return prints 170 lines. So people the Chicago
post office held a letter for in January 1834 are named in this reconstruction's own
sources and stand in no card — not because a ruling refused them, but because the crop the
minting pass read had lost them.

**2. NOTHING WAS RE-MINTED BY THE READING.** T-0299 rules that one list mints once, and
these names are January's. The 79 entities of claims c026 and c027 now carry
`read_at_image` and their printed line, and twelve of them were CORRECTED — `[Ori]nda
Miner` to Miranda Miner, `[Ne]stor Marshall` to Chester Marshall, `John Monroe` to John
Monreou among them. Whether those corrections reach the cards minted from the OTHER
printings of the same list has not been checked; `tools/report_letter_list_collisions.py`
is the pass that would see it.

**3. THREE CARDS LOST A LADDER RUNG THE MOMENT THE READING CHANGED, and that is the
conflict this ticket owns.** `tools/spend_ladder_rungs.py` spends a rung onto a card only
where the card's name and the evidence's name agree. The image renamed three of them —
`hh_crisey_william` (William Crisey → William Crissy), `hh_pease_h` (H. Pease → C. H.
Pease) and `hh_plumer_f` (F. Plumer → S. F. Plumer) — so each dropped its `ladder_rule:
G3` and the pass now lists it among the owner's conflicts, 75 becoming 78. Nothing was
forced back: a card whose name the page contradicts SHOULD stop agreeing with the ladder,
and the three are named here rather than quietly repaired, because renaming a resident
card is the same decision as minting one.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Every one of the 170 printed lines is either matched to a minted resident of the
  1 January 1834 cohort or minted, under the same ruling 1 and carrying
  `letter_list_only`, with the roster line as its source.
- The two firm lines (`Axtel & Steele`, `Jesse B. Winn & Co.`) and the one line naming two
  people (`Lamira & Laura Carrier`) are handled explicitly rather than as personal names.
- Where the image's reading of a name differs from the reading a card was minted on, the
  card is corrected or the difference is recorded — a corrected claim over an uncorrected
  card is worse than neither.
- The count the cohort's own package states is the printed 170 and what reached a card.

**Size.** The mint itself is one run. If reconciling the existing 97 against the roster
turns out to need its own demonstration, `split` it rather than shipping half.

**Links:** T-0424 (the image read, and the roster) · T-0331 (the concordance repairs) ·
T-0310 (the 97) · T-0299 (one list mints once) · `tools/read_letter_list_1834_image.py`
