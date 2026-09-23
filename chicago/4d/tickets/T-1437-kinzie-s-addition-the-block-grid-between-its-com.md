---
id: T-1437
title: Kinzie's Addition: the block grid between its committed corridors, its fifty-two read numerals stamped onto it, and the lots the sheet's own figures allow
state: done
epic: GROUND
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1194
opened: 2026-09-20
closed: 2026-09-20
pr: 1561
claimed_by: run 9/20/2026, 4:55:56 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T10:59:13.901Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35502972675
---

Kinzie's Addition: the block grid between its committed corridors, its fifty-two read numerals stamped onto it, and the lots the sheet's own figures allow.

Piece 2 of 3 of **T-1194 — Generate the lot grid north and west of the river: Thompson's North Division blocks, Kinzie's Addition, Wabansia, the West Division blocks and the School Section tier — numbered lots from each sheet's own module, the small lots kept small, buildable ground tested**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:**

1. `generate_plat_lots.py` cuts blocks between the Addition's OWN corridors as well as the
   Original Town's. The two street lists it holds today decide one grid; a second pair is
   read out of committed files — the Addition's eleven streets from
   `street_control.json` § `north_bank.tiers.kinzies_addition.axis`, and the two lines that
   close the grid on its south and west from `kinzie_addition_street_grid.json` § `seating`
   — so no street id is written into the tool, for the same reason T-1191 writes none.
2. Every cell whose four bounding lines are committed is emitted, at the Addition's own
   22.17 m corridor and not the Original Town's 24.384; every cell that is not is carried
   in `omitted` with the line that falls short named. The west gore, the east-of-Sand
   column, the river tier and the tier above Superior Street have no committed line on one
   side and say so.
3. The fifty-two numerals of `kinzie_addition_block_numbering.json` are stamped — each onto
   the cell its own `column_name` and `tier` name, never counted from a neighbour — and
   every one of the fifty-two is either on a block or on an omission. A numeral that
   reaches neither fails the run.
4. **The lots are WITHHELD and the withholding is the finding.** The Addition's lot figures
   have not been read: `kinzie_addition_street_grid.json` measures a tier pitch and a column
   pitch and no lot rule, and the Original Town's four-to-a-face 80 ft module is a reading of
   one Original Town block. So each Addition block carries `subdivision_withheld` naming what
   is missing and what would settle it, `lots: []` and no alley — never a guessed
   subdivision, which is what the parent ticket asks for in as many words.
5. **Buildable ground, tested.** Every block on the grid — the Original Town's nineteen as
   well — carries a `ground` reading sampled off the committed `e1834_harbor_cut`
   heightfield on a deterministic 5 m lattice: sample count, min/max/mean height, and how
   many samples fall below datum or off the modelled field. Wet ground is recorded, not
   silently skipped.
6. The survey-tract layer's own finding is re-derived rather than left standing: it reads
   "no block here stands in Wabansia or Kinzie's Addition" today, and after this it does.
7. Gates: `generate_plat_lots.py --check` (byte-for-byte re-derivation) and `--self-test`
   with the new grid asserted, plus the whole of `check.sh` green.

**Stop condition:** the Addition's numbered blocks stand on the grid with their boundaries,
their numerals and their ground, and a placement ticket can name one — while the lot lines
inside them stay unclaimed until the sheet is read.
