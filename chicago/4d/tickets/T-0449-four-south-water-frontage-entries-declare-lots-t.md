---
id: T-0449
title: Four South Water frontage entries declare lots their runs never reach, and each hides its block's headroom
state: split
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-30
closed: 2026-09-12
pr: null
claimed_by: run 9/12/2026, 1:33:19 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T06:40:29.388Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34678274590
---

Four South Water frontage entries declare lots their runs never reach, and each hides its block's headroom.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Measured on 2026-08-30 by T-0429, which hit this on `blk_south_water_lasalle` and had to correct
that block's own entry before it could be dealt. The same defect stands on four more entries, and
all four are the blocks T-0430, T-0431 and T-0432 are queued to open.

A `frontage` entry in `data/reconstruction/1835_platted_block_parcels.json` names the LOTS its
party-line run stands across. Two files then read that list for two different purposes and they
disagree:

* `tools/plat_occupancy.py` derives occupancy from FOOTPRINTS, so the 665-roof schedule scores a
  lot free when nothing physically stands on it. That is why `blk_south_water_lasalle` has been
  reading three free lots and eight roofs of headroom.
* `check_block` in `tools/generate_block_infill.py` reads the RECIPE, so a lot named on any deal's
  frontage falls in the class `built on by another deal on this block` and its four lot classes
  must be disjoint. A second deal that tries to build on such a lot is refused.

So an over-declared lot is headroom the schedule offers and the generator will not let anybody
spend. Measured, declared against reached:

| entry | declared | actually reached |
|---|---|---|
| `phase3_platted_block_south_water_franklin` | 2, 4, 6 | **6** |
| `phase3_platted_block_south_water_wells` | 0, 2, 4 | **2, 4** |
| `phase3_platted_block_south_water_clark` | 2, 4 | **4** |
| `phase3_platted_block_south_water_dearborn` | 0, 2, 4 | **4** |

Every one of them is a run anchored `corner: east` whose units ran out before they crossed back
into the lots the entry had listed — the same shape T-0429 corrected on `lasalle` (declared 0, 2,
4; stands on 4 alone).

**The correction is free, and T-0429 demonstrated that it is.** The strip's `along_max` is the east
line of the eastmost declared lot, and on an east-anchored run that lot is the one the run actually
occupies, so dropping the unreached lots does not move the anchor. `frontage.lots` is not part of
the record payload either — only `frontage.why` is — so no structure file changes, no mesh stales
and no bake is needed. What has to be checked per entry is the run's own ceiling: `check_block`
allows `ROW_UNITS_PER_LOT` (3) units per declared lot, so an entry that drops to one lot must be
carrying no more than three units. `lasalle` carried exactly three.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The four entries above declare only the lots their runs measurably stand across, re-measured by
  the same reading T-0429 used (project each unit's footprint onto the block face, project each
  declared lot onto it, and keep a lot the run's span overlaps).
- `tools/generate_block_infill.py --check` re-derives every committed record byte for byte, so the
  correction is provably one to what the recipe DECLARED and not to anything it built.
- `tools/reconcile_665.py --check` still re-derives, and the PR states, per block, the headroom the
  correction hands back.
- Each entry's `arrangement_note` and `frontage.runs` record the correction with its measurement,
  as `lasalle`'s do. Nothing else in the entry moves — not `drawn_from_schedule`, not `families`,
  not a slot.
- Sized S: it is four one-line edits and their prose, no bake, and the gate is `check.sh`.

**Note it does NOT itself build anything** — it is the invisible half that unblocks T-0430, T-0431
and T-0432, and it should be named as such under the visible-progress rule's third exemption. If a
run opening one of those blocks finds its own entry over-declared, correcting that ONE entry in
passing is that ticket's business and this one shrinks accordingly.

**Links:** T-0429 (where it was found and corrected on `lasalle`) · T-0430 · T-0431 · T-0432 ·
T-0105 (the lot classes) · T-0079 (the three-units-per-lot ceiling) · `tools/plat_occupancy.py`.

**Measured on `blk_south_water_dearborn`, 2026-09-11 by T-0432, and the entry was NOT corrected.**
The first deal declares `frontage.lots: [0, 2, 4]` and its run of three units stands entirely on
lot 4: `plat_occupancy.lot_holders` puts `c3_01`, `c3_02` and `d1_05` on lot 4 and nothing of that
run on lot 0 or lot 2. So this block is a live instance of the defect — two of the three declared
lots carry none of the run — and T-0432 left the entry alone on purpose. Rewriting an August
entry's declaration is exactly what T-0105's second-deal rule exists to avoid, and T-0432 needed
the opposite of a correction: it needed lot 2, which the declaration puts in the FIRST deal's
hands, to be dealable by a second. It got there by admitting the overlap and bounding it with the
density ceiling counted across deals, not by narrowing the declaration.

That changes what this ticket is worth, and it is worth saying plainly rather than quietly
shrinking the scope: the over-declaration no longer HIDES this block's headroom, because the
headroom was found and spent without touching it. What is left is that the declaration is still
untrue about lots 0 and 2 — a recipe saying a run stands on ground it does not reach — and the
three sibling entries have not been measured since. A run taking this ticket should re-measure all
four against `lot_holders` before editing any of them, and should know that `generate_block_infill`
now reads a lot's row units off where they STAND rather than off what a run was dealt, so a
corrected declaration and an uncorrected one give the same ceiling.
