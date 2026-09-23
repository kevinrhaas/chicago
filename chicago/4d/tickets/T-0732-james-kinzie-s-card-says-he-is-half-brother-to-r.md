---
id: T-0732
title: James Kinzie's card says he is half brother to Robert A. Kinzie too, in prose, citing nothing — and there are two Robert Kinzie households
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 950
claimed_by: run 9/5/2026, 8:35:18 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T02:22:29.046Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34004139758
---

James Kinzie's card says he is half brother to Robert A. Kinzie too, in prose, citing
nothing — and there are two Robert Kinzie households.

**The reading.** T-0597 gave the residents layer a `kin` field and wrote the one kinship a
source states in as many words: James Kinzie and John Harris Kinzie, half brothers, on
Hurlbut's 1881 bracketed note. The same person record already carried a second claim, in
free text and against no citation of its own: *"He is a half-brother to John H. and Robert
A. Kinzie."* The John H. half is now a graded, reciprocal row. The Robert A. half is still
a sentence.

**And it cannot simply be copied across**, which is the interesting part. This dataset holds
SIX Kinzie households — `hh_kinzie_james`, `hh_kinzie_john_h`, `hh_kinzie_j_h`,
`hh_kinzie_john_s`, `hh_kinzie_r_a`, `hh_kinzie_robert_a` — and two of those six are Robert.
Writing the tie needs the prior question answered first: are `hh_kinzie_r_a` and
`hh_kinzie_robert_a` one man minted twice by two passes, or two people? The same question
stands over `hh_kinzie_j_h` beside `hh_kinzie_john_h`. A `kin` row aimed at the wrong one of
a duplicated pair is worse than no row, because it looks adjudicated.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Say, with evidence, whether the two Robert households are one household and whether the
  two John H. households are one, and record the finding either way.
- If they resolve to one man each, the Robert A. kinship is written as a reciprocal `kin`
  pair citing a source that states it — or, if no held source states it, the free-text
  sentence is marked as the uncited claim it is rather than quietly promoted.
- Nothing is merged on the strength of a shared surname. `data/research/books/crosswalk.json`
  refuses exactly that move for "Mr. John Kinzie", and its rule governs here.
- `tools/check.sh` green.

**Links:** T-0597 · `data/residents/README.md` § `kin` · `data/research/books/crosswalk.json`
· `hh_kinzie_james.json` persons[0].note.
