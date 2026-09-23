---
id: T-0444
title: Measure the west bank of the South Branch and step the plat's sequence from it: is the line drawn as Canal really Clinton?
state: done
epic: GROUND
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-0443
opened: 2026-08-31
closed: 2026-09-04
pr: 681
claimed_by: run 9/3/2026, 1:49:53 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T20:22:02.494Z
claimed_run: null
---

Piece 1 of 4 of **T-0443**. Take it first.

**The plat is a fully dimensioned survey and no new control is needed.** Its
legend states *"The Streets are all 80 feet wide and the alleys 18 feet wide"*
and *"a scale of 160 feet to an inch"*, and every block carries its lot count.
That is enough to reproduce the whole grid by arithmetic.

## The method is already proved against this project's own committed data

Lot depth, recovered from the committed east-west streets (South Division blocks
are two lots deep with an alley between):

| committed pair | m | ft | block | implied lot depth |
|---|---|---|---|---|
| lake → randolph | 142.1 | 466.2 | 386.2 ft | 184.1 ft |
| randolph → washington | 136.5 | 447.8 | 367.8 ft | 174.9 ft |

So the lot is **80 x 180 ft** with an **18 ft** alley — the round figures the
legend implies. Stepping the modules back out:

| module | plat arithmetic | committed mean | delta |
|---|---|---|---|
| South Division north-south streets | 4x80 + 80 = **400 ft = 121.92 m** | **121.92 m** | **0 mm** |
| East-west tiers | 2x180 + 18 + 80 = **458 ft = 139.60 m** | 139.30 m | 0.30 m |

The north-south module reproduces the committed mean **exactly**. The South
Division was built to this arithmetic, so the arithmetic is the right instrument
for the West Division.

## What it says about the West Division — and this part needs no anchor

The West Division's blocks are drawn **two lots across by five down** (ten lots:
`2 1 / 3 4 / 6 5 / 7 8 / 10 9`), not the South Division's four across by two. So
its north-south street module is a block **depth** plus a street:

**2x180 + 18 + 80 = 458 ft = 139.60 m**

The committed `clinton -> canal` spacing is **112.1 m = 367.8 ft**.

> **It is short by 27.5 m — 90.2 ft, most of a lot depth.**

**A spacing does not depend on where the grid is anchored.** So this is a finding
and not a question: whatever the answer to the owner's shift report, the two west
lines this project holds are too close together by 90 ft, and every building
seated between them is packed into ground that is 20% too narrow.

## The one thing arithmetic cannot supply

The river breaks the module between Market Street and West Water Street, so the
West Division needs **one anchor offset** — a single number — before the derived
spacings can be placed. Stepping west from the committed `canal` centreline at
E -170.1 m purely to show the shape of the answer:

| street | derived E (m) | committed |
|---|---|---|
| west_water | -30.5 | absent |
| canal | -170.1 | -170.1 |
| clinton | -309.7 | **-282.2** (27.5 m east of derived) |
| jefferson | -449.3 | absent |
| des_plaines | -588.9 | absent |

That anchoring assumes `canal` is correct, which is exactly what the owner
questions, so **it is an illustration and not a proposal**.

**Acceptance:**

1. The West Division's lot dimensions and block lot-counts are read off the plat
   sheet and committed as data, with the reading recorded — not inferred from
   the South Division as this ticket did.
2. The anchor is established from a committed source (the west bank of the South
   Branch at a named tier, or a plat block this project already holds), and its
   confidence stated.
3. The derived centrelines for all five West Division streets are committed
   beside the two currently held, and the answer to the owner's shift report is
   **written down in plain words with its numbers** — including if the answer is
   that `canal` is where it should be. Both outcomes pass. Silence does not.
4. Nothing moves in this ticket. Moving lines is T-0445.

## THE OWNER'S RULING ON THE PLAT SHEET, 2026-09-03

PR #681 carried out clauses 2–4 and parked on `hold` because clause 1 asks for the West Division's
lot dimensions and block lot-counts "read off the plat sheet", no plat survey was found in the
deposit, and `docs/RESEARCH/thompson_plat_grid.md` refuses to trace the 1834 sheets. Asked whether a
plat sheet could go into the deposit given that rule, the owner answered with a path, recorded
verbatim:

> `https://github.com/kevinrhaas/custom/blob/dev/chicago/pre_fire_v1/maps/images/1830_thompson_plat.png`

**What it means.** The Thompson plat of 1830 is ALREADY in the repository, at
`chicago/pre_fire_v1/maps/images/1830_thompson_plat.png` (7.3 MB, committed to `dev`), and the
run that finishes this ticket reads the West Division's lot dimensions and block lot-counts off
THAT file. `data/sources/thompson_plat_1830.json` now names the path in its `locator`.

**Its limits, stated so the ruling is not stretched:** the sheet is READ, as a period document
(tier 1), for the figures written on it — lot dimensions, lot counts, street and alley widths,
block numbers. It is not warped and not traced for geometry: the source record's rule that the
grid is generated analytically from the plat's stated module rather than from pixels stands, and
`docs/RESEARCH/thompson_plat_grid.md` § 1 still governs how lines are placed. A reading is
recorded with the crop it was taken from (page region, in pixels) so a later reader can check it,
and `verified` on the source record flips to `true` in the commit that reads it.

**Acceptance, restated with the ruling in it:**

1. The West Division's lot dimensions and block lot-counts are read off
   `chicago/pre_fire_v1/maps/images/1830_thompson_plat.png` and committed as data, each reading
   with the region of the sheet it was taken from — not inferred from the South Division.
2. Unchanged.
3. Unchanged; the memo in PR #681 is re-read against the figures the sheet actually gives.
4. Unchanged: nothing moves here. Moving lines is T-0445.
