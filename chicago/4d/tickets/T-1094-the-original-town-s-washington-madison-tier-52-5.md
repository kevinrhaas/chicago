---
id: T-1094
title: The Original Town's Washington-Madison tier (52-58), cut once Madison Street landed
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1089
opened: 2026-09-12
closed: 2026-09-12
pr: 1217
claimed_by: run 9/12/2026, 6:05:01 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T23:46:30.923Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34723880089
---

The Original Town's Washington-Madison tier (52-58), cut once Madison Street landed.

Piece 1 of 2 of **T-1089 — The Washington-Madison tier (52-58), the West Division past Clinton (8-13, 22-27, 46-51) and 14-15 on the North Branch's west bank: no committed street line reaches them, so no crop can be cut**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** every numeral of the Original Town's Washington–Madison tier is read by the
T-0788 block-cut method — one crop per block, each cut from that block's own committed street
lines by a tool the gate re-runs — or it is refused in writing. No numeral located by eye. Where
a box's fourth side is not a committed line, the rule that stands in for it is stated in the tool
and in the memo, and the reading is graded no better than `inferred`.

**Done, 2026-09-12.** Seven numerals: **52 53 54 55 56 57 58**, rising eastward, which is the
fourth term of the boustrophedon § 0 read off the three tiers above it and the first test of that
alternation made in advance of the reading.

- `tools/read_washington_madison_numerals.py` derives the seven boxes and `tools/check.sh` runs
  its `--check` and `--self-test`. Washington and Madison are committed across the tier; the
  seven flanking north–south lines are committed and `attested` but stop at y = −400 m, so each
  is continued south along its own bearing to Madison. That continuation is arithmetic on
  committed endpoints and is deliberately **not** written into `data/streets/1835.json`.
- The module measures **123.36 m**, the North Division's figure of T-1088 to the centimetre, on
  different streets a kilometre away and derived independently.
- Block 52 is the one numeral not wholly inside its own box — the 2's flourish runs ~10 px
  (~7 m) past the east edge, because the georeference seats Market Street about 25 m west of the
  block line Wright inks there. The overhang is committed as a number and the gate checks it.
- The seven wait in `blocks_not_in_the_grid`: `generate_plat_lots.py` emits nothing south of
  Washington, so there is no cell to stamp them onto.

Thirty-eight of fifty-eight now read. The twenty still refused are T-1095.
