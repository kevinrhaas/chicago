---
id: T-1096
title: Wright's legend chips read: the nine colours measured, and the two ambiguous swatches refused because the palette cannot separate them
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0792
opened: 2026-09-12
closed: 2026-09-12
pr: 1218
claimed_by: run 9/12/2026, 6:33:36 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T00:08:38.992Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34724869993
---

Wright's legend chips read: the nine colours measured, and the two ambiguous swatches refused because the palette cannot separate them.

Piece 1 of 2 of **T-0792 — The legend's nine coloured tracts are the town's survey history — who surveyed what ground, when, for whom — and the project has no tract layer**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. The nine chips are LOCATED on a named scan and MEASURED — a pixel box, a median, a mean
   and a per-channel spread each, with the sample count — so that "read it against the
   legend's swatches" becomes a thing another tool can do.
2. The legend's wording is read verbatim, with the hand's own spelling kept where it
   differs from the project's, and each line's date carried.
3. How many separable colours the nine chips carry is MEASURED against the spread inside a
   chip, and the answer decides whether T-0792's ask 2 — the two ambiguous swatches read by
   matching swatch to ground — can be done at all. If it cannot, the refusal is recorded as
   a refusal and gated, not softened into a guess.
4. One chip-to-ground reading is made and TESTED against geometry derived without reference
   to colour, so that the method's worth is demonstrated rather than asserted.

**Done, 2026-09-12.** `tools/read_wright_legend_swatches.py` (build, an offline
`--check-properties` wired into `tools/check.sh`, `--report`, `--self-test`),
`data/traces/wright_1834_legend_swatches.json`, and
`docs/RESEARCH/wright_1834_legend_swatches.md`.

The answer to 3 is **six separable colours, not nine**. Chips 4 and 9 differ by 9.0 RGB
units, chips 3 and 7 by 10.0, while the spread inside a single chip reaches 60.8 per
channel. Chip 6 — one of the two the parent wants resolved — falls in a class with two
named tracts; chip 8 stands 47 from chip 5, three quarters of chip 5's own spread. So
swatch-to-ground by colour cannot resolve either, and `check.sh` now gates the refusal
itself: an edit that made the nine look separable fails the step.

The reading made under 4 is chip 5's. Every one of section 16's four committed sides —
seated on the PLSS corner and a nominal mile, by work that never looked at a colour —
falls INSIDE the band of chip 5's colour. Two derivations that never referred to each
other agree on all four sides.

Handed to T-1097: Wabansia's faded stroke classifies with chip 8 rather than with its own
chip, so a tract layer assigning ground by nearest chip would misfile it; and the largest
band on the sheet is the lake quadrant's foxing and the tear's repair, not a wash.
