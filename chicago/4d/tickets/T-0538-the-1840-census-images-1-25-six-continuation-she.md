---
id: T-0538
title: The 1840 census images 1-25: six continuation sheets — 24, 5D, 5S, 5V, 6H and 6Q — read line by line and closed against their own printed column totals
state: split
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0535
opened: 2026-09-03
closed: 2026-09-03
pr: null
claimed_by: run 9/3/2026, 5:49:24 AM CT
blocked_on: null
needs_bake: false
---

The 1840 census images 1-25: six continuation sheets — 24, 5D, 5S, 5V, 6H and 6Q — read line by line and closed against their own printed column totals.

Piece 1 of 2 of **T-0535 — The 1840 census images 1-25: the eleven continuation sheets, paired to their left sheets by printed page**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Why the parent was split, stated where the next run will read it.** The parent asked for
eleven continuation sheets AND the pairing of all eleven to their left sheets. Both halves
were sized on the images before any of them was committed, and neither is cheap: a
continuation sheet is 31 ruled lines across fifteen hand-written numeric columns, and it is
only worth committing if it CLOSES against the printed column totals at the foot of the
sheet — which takes several passes at magnification per sheet, not one. The pairing needs a
second reading of a different set of images again (the twelve filled left sheets of this
group), because the test the parent names — the continuation's TOTAL column against the left
sheet's age-band sums — cannot be run until each left sheet's own printed footer row has been
read. Eleven sheets plus twelve footers is more than one demonstration, so it is more than
one ticket. This piece takes six of the eleven sheets; T-0539 takes the other five and the
left-sheet population key that pairs all eleven.

- Each of `33S7-9YYJ-24`, `-5D`, `-5S`, `-5V`, `-6H`, `-6Q` gets a
  `pages/<familysearch_id>.json` with one record per ruled line carrying an entry: the twelve
  slave columns, the family TOTAL, the seven industry columns, pensioners, the six white and
  four coloured deaf/dumb/blind/insane columns and the seven schools columns.
- **Every sheet closes against its own printed footer row.** The footer totals are
  transcribed as committed data and the per-line readings are required to sum to them,
  column by column. A sheet that does not close is recorded as not closing, with the
  residual, rather than adjusted until it does.
- The exact count of ruled lines carrying an entry is restated for each of the six —
  `coverage.json` states this group's counts "to the nearest line" for the images it only
  inventoried, and three of these six are among them.
- No pairing is asserted here. Each of the six publishes its page population (its TOTAL
  footer) as the key T-0539's pairing test will read, and is recorded as unpaired until
  then. An unpaired sheet is recorded as unpaired, never guessed.
- Coverage group 1's `read_state` and `page_file` updated for these six images.

**The rules, unchanged from the parent.** `reading: scan_verified`. Enumeration order is
data: never reorder lines, and record a blank or illegible line rather than skipping it. No
IPUMS serial is attached here (T-0504). Nothing here mints or regrades an 1835 resident: the
1840 census is LATER EVIDENCE and the ratified ladder is explicit that "1839/1840 alone is
never a 1835 resident". Do not commit images or crops; the deposit is read-only. Town
findings go in `claims.json` with `town_finding: true`, verbatim quote and locator.
