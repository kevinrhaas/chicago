---
id: T-0942
title: The SCHOOLS block of 33S7-9YYJ-L3 carries ink and is unread: the landed reading took the TOTAL column and the footer row and swept nothing to their right
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-17
pr: null
claimed_by: null
blocked_on: folded into T-1290
needs_bake: false
closed_at: 2026-09-17T19:18:41.135Z
claimed_run: null
---

**Salvaged from PR #1013 by T-0927, 2026-09-07, before that PR was closed as superseded.**
Filed there as T-0924; that number was never on `dev` and the ticket file has never
existed there.

The reading of 33S7-9YYJ-L3 that landed as PR #1014 took the TOTAL column and the footer
row and swept nothing to their right. The leaf's SCHOOLS block carries ink and no pass has
committed it. On `dev` the page file has no `schools_block_as_read` key at all.

PR #1015 — parked on `hold`, and not landed — did read it, and what it read is why this
matters rather than being tidy-up: its `schools_block_as_read` names a figure on line 1 and
a footing, on a leaf whose seventh SCHOOLS column is already recorded elsewhere as unread
for a different reason (T-0755: `No. of Scholars at public charge` sits in the binding
gutter of 33S7-9YYJ-6H and is recorded unread rather than blank). Two leaves, the same
column, unread twice.

**Acceptance:**

1. The SCHOOLS block of 33S7-9YYJ-L3 is read cell by cell at the exposure the rest of the
   leaf was read at, and each cell is committed, or recorded unread with the reason.
2. A cell with no ink is recorded as carrying no ink — not as a zero — in the form the
   other blocks on this leaf already use.
3. The block's own footing is read and the column closure is stated, closing or not, with
   nothing adjusted to make it close.
4. If #1015's reading of the block is used, it is cited as the source and re-verified at
   the image rather than copied.

**Links:** T-0744 · T-0755 · T-0927 · PR #1013 (closed) · PR #1015 (`hold`) · T-0941.

## Folded in from T-0943 (2026-09-10) — the rest of 33S7-9YYJ-L3 once T-0957 settles its footing: the SCHOOLS block and the PC sequence test

*T-0943: Test 33S7-9YYJ-L3 against printed 218 (33S7-9YYJ-PC) line by line: T-0744 moved both pairing keys onto PC and a sequence test is what would close it*

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
