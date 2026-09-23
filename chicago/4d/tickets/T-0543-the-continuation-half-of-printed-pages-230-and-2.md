---
id: T-0543
title: The continuation half of printed pages 230 and 232 is on a right sheet nobody has identified, and it is not in images 26-50
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-05
pr: 848
claimed_by: run 9/5/2026, 12:00:22 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T05:44:11.776Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33945841743
---
The continuation half of printed pages 230 and 232 is on a right sheet nobody has identified, and it is not in images 26-50.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

The family TOTAL, the six industry columns, pensioners, and the schools and illiteracy
columns for the 62 households of printed pages **230** (`33S7-9YYJ-NY`) and **232**
(`33S7-9YYJ-W6`) live on those pages' paired continuation sheets. T-0530 read the left
sheets to the cell and could not read the continuation half, because **which right sheet
belongs to which left sheet is not settled** — that is T-0528's ticket — and because the
two sheets in question are **not in image group 26-50 at all**.

**The evidence for that, so it does not have to be gathered twice.** Every right sheet in
images 26-50 was read at its TOTAL footing:

| image | TOTAL footing | image | TOTAL footing |
|---|---|---|---|
| `33S7-9YYJ-FJ` | 135 | `33S7-9YYJ-VJ` | 107 |
| `33S7-9YYJ-K2` | 151 | `33S7-9YYN-3CF6` | 110 |
| `33S7-9YYJ-L3` | 115 | `33S7-9YYN-3CNQ` | blank |
| `33S7-9YYJ-V4` | 100 | `33SQ-GYYJ-5H` | 15? (partly cut by the scan edge) |
| `33S7-9YYJ-V2` | three-figure, and T-0529's ticket | `33SQ-GYYJ-7L` | blank |
| | | `33SQ-GYYJ-9CZ` | 151 |

Page 230's free population is **151** by its own marks and by its own footings; page 232's
is **193** by the marks and **195** by the footings. **No sheet here foots 193.** Two foot
151, and one of them, `33SQ-GYYJ-9CZ`, was checked line by line and its per-line TOTAL
vector (6, 5, 11, 3, 4, 8, 8, 2, 7, 9, 2, 11, 6, 7, ...) is not page 230's. `33S7-9YYJ-K2`
was not ruled out: its per-line vector, read at a third of full scale, has the same tail as
page 230's — `..., 2, 1, 4, 3, 9, 6, 5, 16, 5, 4, 2, 4, 7, 3, 6` — which is a distinctive
match and worth one careful pass at full resolution. It would mean K2 pairs with 230 rather
than with `33S7-9YYJ-JM` (printed 224), which is what `coverage.json` currently assumes.

**The pairing key is already committed.** `records[].cells.free_persons` on both page files
is the free population of each ruled line; a household is one line spanning both sheets, so
the right sheet's TOTAL column has to equal it line for line. That vector is a 31-number
fingerprint and it is what settles a pairing rather than a footing that happens to agree.

**Acceptance:** (one demonstration, never weakened to pass)
- The continuation sheet for printed 230, and the one for printed 232, are each named with
  the per-line TOTAL comparison that identifies them — or the search is recorded as
  exhausted over all 33 right sheets in the deposit, image by image, with each one's
  footing and the reason it is not the pair.
- Where a pair is found, its family TOTAL, six industry columns, pensioner, deaf/dumb/blind
  and schools/illiteracy cells are read for all 31 lines and land on the left page's records.
- The reading is checked against that sheet's own printed footings, the way T-0530 checked
  the left sheets, and a column that does not reconcile is named.

Blocked on nothing, but it overlaps T-0528 (the pairing of the nine continuation sheets):
whichever runs first should carry the other's finding rather than repeat it.
