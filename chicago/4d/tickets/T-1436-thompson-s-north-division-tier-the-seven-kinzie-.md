---
id: T-1436
title: Thompson's North Division tier: the seven Kinzie-to-the-river blocks and the four-to-a-face lots the plat draws in them
state: split
epic: GROUND
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1194
opened: 2026-09-20
closed: 2026-09-20
pr: null
claimed_by: run 9/20/2026, 9:00:47 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T14:10:48.421Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35515025077
---

Thompson's North Division tier: the seven Kinzie-to-the-river blocks and the four-to-a-face lots the plat draws in them.

Piece 1 of 3 of **T-1194 — Generate the lot grid north and west of the river: Thompson's North Division blocks, Kinzie's Addition, Wabansia, the West Division blocks and the School Section tier — numbered lots from each sheet's own module, the small lots kept small, buildable ground tested**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**READ THIS BEFORE CLAIMING — the tier's SOUTH FACE is not derivable from committed data
today, and that is what this piece has to settle first.** Found sizing T-1437, 2026-09-20:

* The tier is bounded north by Kinzie Street and south by North Water Street
  (`docs/RESEARCH/north_division_streets.md` § 1). Kinzie is committed, `attested`, with an
  80 ft corridor. North Water is `reconstructed` and is CUT FROM THE RIVER BANK by
  `tools/derive_north_water.py`; `street_control.json` § `north_bank.not_in_the_corridor_layer`
  refuses it a corridor in as many words — *"offsetting that polyline by half a module would
  invent a rectangle no sheet draws"* — which is why T-1191 left it out of the corridor layer.
* Taking the south face off North Water's committed centreline anyway gives block depths of
  92 m at Franklin, 119 at Wells and 137-139 at La Salle, Clark and Dearborn, against the
  South Division's 93.9 m. A tier the plat draws two lot rows deep does not run 92 m at one
  end and 139 m at the other; what varies is the bank, not the block.
* The plat cannot supply the depth either: `data/sources/thompson_plat_1830.json` is a
  PARAMETER source and `data/traces/gcp/thompson_1830_gcps.json` § `use` is explicit that no
  block geometry may be derived through its transform. The sheet's stated figures give the
  80 ft corridor and nothing about a north-tier depth.
* So the first demonstration this piece owes is a READING: the tier's south face off the
  Thompson sheet by the same committed method T-0451 used for its north-south strokes — a
  row scan in a band, pixels committed to
  `data/traces/thompson_north_division_streets.json`, metres through a px-to-northing fit
  anchored on South Division corridors measured on the same sheet. Pillow and numpy are on
  the runner. Until that exists the tier cannot be cut, and the seven numerals waiting in
  `thompson_block_numbering.json` § `blocks_not_in_the_grid` stay where they are.
