---
id: T-1010
title: The 170 printed lines of the 1 January 1834 return, tied line by line to what each of them reaches: a minted card, a resident the town already held, a named refusal, or nothing
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1008
opened: 2026-09-10
closed: 2026-09-10
pr: 1095
claimed_by: run 9/10/2026, 7:18:34 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T00:32:22.990Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34544959894
---

The 170 printed lines of the 1 January 1834 return, tied line by line to what each of them reaches: a minted card, a resident the town already held, a named refusal, or nothing.

Piece 1 of 2 of **T-1008 — The ninety-two lines of the 1 January 1834 letter list the crops never carried are read but unminted, and the 97 residents minted from it are a floor of a 170-name return**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- A ledger with ONE ROW PER PRINTED LINE, all 170 of them, saying what that line
  reaches: a household this project minted from the return, a resident the town
  already held on other evidence, a named refusal out of the mint's own rules, or
  nothing at all.
- DERIVED, not asserted. The minted and refused outcomes come from
  `mint_letter_list_residents.mint()` itself rather than from a second reading of its
  printed report, so the ledger cannot drift from the pass it describes, and
  `--check` re-derives it in `tools/check.sh`.
- The tie between a printed line and an extracted name is a RULE, recorded on the row,
  and every ambiguity is refused rather than broken — a concordance that guesses is
  worse than one that counts its own gaps.
- The two firm lines and the one line naming two people are marked as what they are,
  and the count of PEOPLE named is stated beside the count of LINES.
- Where the image's reading of a name differs from the reading a card was minted on,
  both are carried, and the card's own spelling says which of the two it follows.

**Closed by PR #1095.** 116 of the 170 lines tie to a name this project has extracted
from one of the return's nine impressions; 69 reach a card (64 minted, 5 already held);
47 are refused under a named rule; **54 reach nothing at all**, and that number is the
floor T-1011 mints against.
