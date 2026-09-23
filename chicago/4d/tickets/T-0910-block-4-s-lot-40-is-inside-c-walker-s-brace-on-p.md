---
id: T-0910
title: Block 4's lot 40 is inside C. Walker's brace on printed page 47 and reaches the reading with no bidder at all
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-11
pr: 1111
claimed_by: run 9/11/2026, 1:49:41 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T07:25:32.104Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34571421320
---

Block 4's lot 40 is inside C. Walker's brace on printed page 47 and reaches the reading with no bidder at all.

FOUND BY T-0779's sweep of the bidder column, and deliberately not taken there: a brace is
not a ditto and the ticket's acceptance named the ditto rows only.

Printed page 47's right half ends block 4 with a printer's brace over lots 39 and 40 against
one name and one price — `C. Walker,` and $408 the pair, which `what_the_image_could_not_settle`
already records as a price that is not split. The BIDDER is a different matter: lot 39 carries
C. Walker and lot 40 (`f1839_lot0060`) carries nobody, because the OCR mapped it no ink and the
brace is not a ditto mark that `reads_as_ditto` would catch. The page image is plain that one
brace covers both lots.

Blocks 2, 4 and 5 have other braced runs, but those are `Reserved.` — no bidder to lose. This is
the one brace on these three pages that gathers a lot under a NAME, so it is one row, not a class.

**Acceptance:**

- Every braced run on printed pages 47-49 that gathers a lot under a bidder's name is enumerated
  off the page images, not just the one this was filed for.
- Each such lot carries the name its brace carries, through the corrections layer T-0779 built
  (a third kind beside `bidder` and `bidder_ditto`, or a stated reason why the existing kind
  serves), asserting the ink as every other correction does.
- The price stays unsplit and `what_the_image_could_not_settle` still says so: the brace prints
  one amount over two lots and this ticket does not invent a division of it.
- `fergus_1839_lots_crosswalk_1835.json` and the lot-sale spend regenerate, and the count of
  bidders and of lots carried onto cards is stated before and after.
