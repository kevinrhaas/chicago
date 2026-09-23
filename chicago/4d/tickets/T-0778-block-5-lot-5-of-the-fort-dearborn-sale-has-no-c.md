---
id: T-0778
title: Block 5 lot 5 of the Fort Dearborn sale has no claim at all: the row map never gathered it, and the printed page 47 brace covers it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-06
pr: 1000
claimed_by: run 9/6/2026, 1:33:33 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T18:54:48.750Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34051766484
---

Block 5 lot 5 of the Fort Dearborn sale has no claim at all: the row map never gathered it, and the printed page 47 brace covers it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Printed page 47's right half ends on block 5, whose lots 1 to 5 are braced together against
a single *Reserved.* The reading has claims for lots 1, 2, 3 and 4 and then jumps to block
5's lot 6 at the top of the next leaf. Lot 5 is printed — it was read off the page image by
T-0679 — but `fergus_1839_lots_rowmap.json` never gathered a row for it, so there is no cell
for the corrections layer to correct: a layer that fills cells cannot mint a row.

So the file says 267 printed rows and the page has 268.

Two ways in, and the choice is the ticket: teach `--map` to gather the row (it is the last
line of a half-page, and TABLE_TOP / the tight-pass merge are the likely reason it is
dropped), which renumbers nothing because it inserts before block 5's lot 6; or give the
corrections layer an `added_rows` section carrying explicit spans into the committed text,
the way the population half already reaches a row the reading drops. The first is better if
the map is simply wrong; the second if the ink for the row is not there to gather.

**Acceptance:** 268 lot claims, block 5's lot 5 among them and graded for how it was
recovered, `tools/read_fergus_1839_lots.py --check` and `--self-test` green, and the
crosswalk regenerated.
