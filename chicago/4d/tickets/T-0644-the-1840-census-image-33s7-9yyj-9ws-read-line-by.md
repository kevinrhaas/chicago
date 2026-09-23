---
id: T-0644
title: The 1840 census image 33S7-9YYJ-9WS read line by line and closed against its own printed column totals
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0640
opened: 2026-09-03
closed: 2026-09-04
pr: 769
claimed_by: run 9/4/2026, 2:52:40 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T08:10:47.650Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33846643856
---

The 1840 census image 33S7-9YYJ-9WS read line by line and closed against its own printed column totals.

Piece 2 of 2 of **T-0640 — The 1840 census images 1-25: continuation sheets 33S7-9YYJ-8D and -9WS read line by line and closed against their own printed column totals**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- `pages/33S7-9YYJ-9WS.json` on the shape 33S7-9YYJ-8D was committed with: one record per
  ruled line carrying an entry, the twelve slave columns, the family TOTAL, the seven
  industry columns, pensioners, the ten deaf/dumb/blind/insane columns and the seven schools
  columns; and every committed column checked against the enumerator's own footer row, with
  a residual recorded rather than adjusted away where it does not close.
- The footer row is already read and is not in dispute: **TOTAL 157, commerce 15,
  manufactures and trades 12, learned professions 8** (the last glyph is a closed
  double-loop and the sheet's own `5` in `157` carries a top bar, so it is read as an 8 —
  say so either way), mining, agriculture and both navigation columns blank. `coverage.json`
  also records that this sheet's schools columns carry 1 and 25, and those are the two
  figures the schools block has to be checked against.
- The sheet publishes its page population as the key T-0642's pairing test reads, and is
  recorded as unpaired until then.

**What the run that split this off measured, so the next one does not pay for it twice.**

- The reading of 33S7-9YYJ-8D took most of a run on its own, and 9WS is the harder of the
  two: 8D is a sparse sheet in a clean hand where every family total is one or two strokes,
  and 9WS is dense, in a different hand, with multi-digit totals (its page population is 157
  against 8D's 106) whose digits touch the line above and below.
- **The line grid is the actual problem, and it is unsolved on this image.** Connected
  components of the TOTAL column between the body rules cluster into thirty groups plus one
  merged run of about four lines at the foot, at spacings from 43 to 101 px; `coverage.json`
  inventoried the sheet at 28 lines "to the nearest line". No uniform pitch fits: neither
  28 lines at 84.6 px nor 31 at 76.5 px lands on the observed clusters. The row assignment
  has to be anchored by cross-column coincidence — an entry in commerce, manufactures or the
  learned professions sits on the same line as the TOTAL group it coincides with in y — and
  that reading has not been made.
- `tools/read_census_continuation.py`, which exists to do exactly that, **does not run on
  this image**: it exits `no industry run bracketed by TOTAL and PENSIONERS`. It fails the
  same way on -B1, -B2 and -BF, and on -8D it exits `too few vertical rules to name the
  middle columns`. The cause found on 8D is leaf skew — the printed rules drift about 20 px
  left down the page, and the tool's rule finder wants a rule continuous down a fixed x. On
  9WS the drift is smaller (about 6 px over 2,000 px) and the bracket test is what fails
  instead. Either teaching that tool the shear or reading against a measured, sheared column
  map by hand is a legitimate route; 8D was done the second way, and its `geometry_note`
  records the column map and the slope.
- The column map measured for 9WS, if it saves a pass: body band y 578-2948; footer row
  between y 2948 and 3030; TOTAL x 1115-1306 with the digits standing in its right half;
  then mining 1306-1376, agriculture 1376-1441, commerce 1441-1506, manufactures and trades
  1506-1585, navigation of the ocean 1585-1668, navigation of canals lakes and rivers
  1668-1744, learned professions and engineers 1744-1818 — all at y=750, sheared by
  -0.003 px per px of y.

**The rules, unchanged from the parent.** `reading: scan_verified`; enumeration order is
data, so never reorder lines and record a blank or illegible line rather than skipping it;
no IPUMS serial here (T-0504); nothing here mints or regrades an 1835 resident; the deposit
is read-only, and no image or crop is ever committed. Town findings go to `claims.json` with
`town_finding: true`, a verbatim quote and a locator.
