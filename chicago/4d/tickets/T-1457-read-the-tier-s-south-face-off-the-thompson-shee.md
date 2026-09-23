---
id: T-1457
title: Read the tier's south face off the Thompson sheet: a row scan across the seven blocks, the four drawn lines per block committed as pixels, metres through a px-to-northing fit anchored on the South Division corridors, and the depth the plat actually draws
state: done
epic: GROUND
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1436
opened: 2026-09-20
closed: 2026-09-20
pr: 1575
claimed_by: run 9/20/2026, 9:11:00 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T15:18:01.597Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35515025077
---

Read the tier's south face off the Thompson sheet: a row scan across the seven blocks, the four drawn lines per block committed as pixels, metres through a px-to-northing fit anchored on the South Division corridors, and the depth the plat actually draws.

Piece 1 of 2 of **T-1436 — Thompson's North Division tier: the seven Kinzie-to-the-river blocks and the four-to-a-face lots the plat draws in them**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance** (stated before working, one demonstration, not weakened to pass):

1. The tier's four drawn lines per block are read off the sheet by a row scan and
   committed as PIXELS to `data/traces/thompson_north_division_streets.json`, with
   `--reread` reproducing every one of them from the 7 MB sheet.
2. They become metres through a px-to-northing fit anchored on South Division corridors
   measured on the same sheet, and that fit is checked against something it was not
   fitted to.
3. The reading states what it does and does not entitle the cut to do.

**Met.** (1) `north_tier_horizontals_px`, six blocks by four lines, plus
`south_division_control_px`, 20 control samples;
`measure_north_division_tier_depth.py --reread` re-reads all of it exactly. (2) The fit
lands on 0.5345 m/px against T-0451's independent easting fit's 0.5345 - 0.004 % on two
axes with no shared arithmetic - and, in the extrapolation zone itself, reproduces the
180 ft the sheet letters to 0.2 ft in the mean. (3) The held-out Kinzie line is missed by
up to 16.8 m, monotonically in easting, so the reading publishes DEPTHS and refuses
northings, and says so in the trace, the tool and the doc. The finding: the tier is a
wedge - constant 180 ft lower row, upper row 178.6 to 232.7 ft - which overturns T-1436's
premise that "what varies is the bank, not the block".
