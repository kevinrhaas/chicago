---
id: T-0943
title: Test 33S7-9YYJ-L3 against printed 218 (33S7-9YYJ-PC) line by line: T-0744 moved both pairing keys onto PC and a sequence test is what would close it
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: folded into T-0942: the rest of 33S7-9YYJ-L3 once T-0957 settles its footing: the SCHOOLS block and the PC sequence test
needs_bake: false
closed_at: 2026-09-10T04:20:06.971Z
claimed_run: null
---

**Salvaged from PR #1015 by T-0927, 2026-09-07.** #1015 is NOT closed — it self-declares a
disagreement with the landed reading and belongs to T-0930 — but the ticket it filed was
given the number T-0923, which another run took on `dev` while #1015 sat open, and the
file has never existed on `dev`. Refiled here so the test survives whatever T-0930 rules
about the PR.

T-0744 moved both of 33S7-9YYJ-L3's pairing keys onto printed 218 (33S7-9YYJ-PC). The
pairing rests on the page-population key and the line-count key, and neither is a sequence
test: what would close it is reading the two leaves against each other line by line, so
that the order of households on the left sheet is shown to be the order of figures on the
right.

That test is worth more here than on an ordinary pair, because the leaf's own arithmetic
is in dispute — the TOTAL column does not close on either reading of it (T-0941), so the
population key cannot be the thing that settles the pairing.

**Acceptance:**

1. Printed 218's households are read in order and put beside 33S7-9YYJ-L3's TOTAL figures
   in order, position by position, with the count of positions that agree stated.
2. Any position where the two disagree is named, not averaged away.
3. The pairing carries the verdict the sequence test gives it — including "the test does
   not settle it" — and the page record says which key it now rests on.
4. Nothing in the pairing is re-derived from the disputed footing.

**Links:** T-0744 · T-0941 · T-0927 · T-0930 · PR #1015 (`hold`).
