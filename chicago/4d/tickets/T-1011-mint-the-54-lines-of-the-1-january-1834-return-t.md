---
id: T-1011
title: Mint the 54 lines of the 1 January 1834 return that reach no card at all, under ruling 1 and carrying letter_list_only, with the roster line as the source
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1008
opened: 2026-09-10
closed: 2026-09-10
pr: 1100
claimed_by: run 9/10/2026, 8:36:24 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T03:06:12.231Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34551115214
---

Mint the 54 lines of the 1 January 1834 return that reach no card at all, under ruling 1 and carrying letter_list_only, with the roster line as the source.

Piece 2 of 2 of **T-1008 — The ninety-two lines of the 1 January 1834 letter list the crops never carried are read but unminted, and the 97 residents minted from it are a floor of a 170-name return**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

T-1010 measured the gap and `data/research/newspapers/letter_list_1834_01_01_concordance.json`
is the ledger: 54 of the return's 170 printed lines reach no card at all, because the
transcriptions the minting pass read had lost them to an interleaved advertisement.
They are not refusals — no rule ever saw them.

- Every line the concordance marks `unread` is either MINTED under the owner's ruling 1
  (a listed name mints a resident candidate), carrying `letter_list_only` and the
  roster line as its source, or refused by one of `mint_letter_list_residents.py`'s own
  refusals with the refusal named. The pass decides; this ticket does not hand-pick.
- The 1 January 1834 return is dated by the return and not by the impression a name was
  read in (T-0425), so a newly minted record takes the same `not_later_than` bound its
  cohort already carries.
- T-0299 still holds: one list mints once. A line that already reaches a card is not
  minted a second time, and the concordance is what proves which those are.
- The 29 readings the concordance could not tie to a line are looked at once more
  before the mint runs — several name a surname the list carries on a line whose
  forename contradicts them, and those are a scan question, not a minting one.
- `tools/concord_letter_list_1834_01_01.py --check` still green afterwards, with its
  `unread` count moved to whatever the mint left, and `bash tools/check.sh` green.

**Size.** The mint itself is one run; the town's resident count moves by it, so the
derived files that count residents move with it in the same commit.
