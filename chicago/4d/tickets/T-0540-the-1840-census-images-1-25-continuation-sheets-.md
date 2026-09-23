---
id: T-0540
title: The 1840 census images 1-25: continuation sheets 24, 5D and 5S read line by line and closed against their own printed column totals
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0538
opened: 2026-09-03
closed: 2026-09-03
pr: 689
claimed_by: run 9/3/2026, 5:55:41 AM CT
blocked_on: null
needs_bake: false
---

The 1840 census images 1-25: continuation sheets 24, 5D and 5S read line by line and closed against their own printed column totals.

Piece 1 of 2 of **T-0538 — The 1840 census images 1-25: six continuation sheets — 24, 5D, 5S, 5V, 6H and 6Q — read line by line and closed against their own printed column totals**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Why T-0538 was split again, and it is a measured size and not a second opinion.** T-0538
was cut out of T-0535 at six sheets on an estimate taken from the first sheet read
(`33S7-9YYJ-24`), which closed against all five of its printed column totals in four passes.
The estimate was wrong, and the run that made it says so here rather than shipping six
half-read sheets. A continuation sheet is 31 ruled lines across fifteen hand-written numeric
columns in a hand whose `4` is two strokes that read as `11`, whose `7` and `9` differ by a
loop, and whose two-digit family totals sit hard against the column rule. The reading is only
worth committing when it CLOSES — when the per-line values sum, column by column, to the
printed totals the enumerator wrote at the foot of his own sheet — and getting there took
ten-odd passes at magnification per sheet, not four. Six sheets is more than one run's
demonstration. This piece takes 24, 5D and 5S; T-0541 takes 5V, 6H and 6Q.

- Each of the three gets a `pages/<familysearch_id>.json` with one record per ruled line
  carrying an entry: the twelve slave columns, the family TOTAL, the seven industry columns,
  pensioners, the six white and four coloured deaf/dumb/blind/insane columns and the seven
  schools columns.
- **Every sheet is closed against its own printed footer row**, which is transcribed as
  committed data beside the lines. Where a column does not close, the RESIDUAL is recorded
  with it — a reading is never adjusted to make a total come out.
- The exact count of ruled lines carrying an entry is restated for each. `coverage.json`
  states this group's counts "to the nearest line" for the images it only inventoried, and
  all three of these are among them.
- No pairing is asserted. Each sheet publishes its page population (its TOTAL footer) as the
  key T-0539's pairing test will read, and is recorded as unpaired until then. An unpaired
  sheet is recorded as unpaired, never guessed.
- Coverage group 1's `read_state` and `page_file` updated for these images.

**The rules, unchanged from T-0535.** `reading: scan_verified`. Enumeration order is data:
never reorder lines, and record a blank or illegible line rather than skipping it. No IPUMS
serial is attached here (T-0504). Nothing here mints or regrades an 1835 resident: the 1840
census is LATER EVIDENCE and the ratified ladder is explicit that "1839/1840 alone is never a
1835 resident". Do not commit images or crops; the deposit is read-only. Town findings go in
`claims.json` with `town_finding: true`, verbatim quote and locator.
