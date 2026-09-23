---
id: T-0689
title: The West Division's lot dimensions and lot-counts are still unread off the Thompson plat, and T-0444 closed without them
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-12
pr: 1227
claimed_by: run 9/12/2026, 10:08:27 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T03:55:03.304Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34734600049
---

The West Division's lot dimensions and lot-counts are still unread off the Thompson plat,
and T-0444 closed without them.

**Filed 2026-09-04 when the owner closed T-0444**, so the one part of its acceptance that
was never carried out is not lost with it.

## What T-0444 delivered, and what it did not

T-0444 derived the West Division's module and answered the owner's shift report; PR #681
merged it. Its acceptance had been restated with the plat ruling in it, and point 1 reads:

> The West Division's lot dimensions and block lot-counts are read off
> `chicago/pre_fire_v1/maps/images/1830_thompson_plat.png` and committed as data, each
> reading with the region of the sheet it was taken from — **not inferred from the South
> Division.**

That reading was never done. #681 said so in its own words — *"The next run on T-0444 reads
the West Division's lot dimensions and lot-counts off that sheet, re-reads the memo against
them, and lifts the hold"* — and the run never came.

## Why it matters more than a tidy-up

The whole West Division question is whether its grid sits one street west of where this
project draws it — whether the line drawn as `canal` is really Clinton. **Every building
west of the river depends on the answer**, and the answer is supposed to rest on figures
read off the sheet rather than on the South Division's spacing carried across. Closing
T-0444 with point 1 unread leaves the module resting on the inference it was written to
replace.

## What is already covered elsewhere, so this ticket does not duplicate it

- **Moving any line is T-0445**, by T-0444's own point 4 — nothing here moves geometry.
- **T-0685** georeferences the Thompson plat at the forks and measures its bank against the
  Wright 1834 line. That is the same sheet and should probably be taken first or together:
  a georeference makes a lot-dimension reading measurable rather than scaled by eye.
- **T-0446** is Carroll and Fulton, the two platted tiers with no street between them.

## The constraint that shaped the original ruling

The owner answered the plat question on 2026-09-03 with a path rather than a new deposit:
the Thompson plat of 1830 is **already on dev**, and it is read for its **printed figures**
as a tier-1 document — never warped, never traced. That is what keeps the no-tracing rule
intact, and it binds this ticket too.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. The West Division's lot dimensions and block lot-counts are read off the committed
   Thompson plat image and committed as data, each reading carrying the region of the sheet
   it came from.
2. Not one figure is inferred from the South Division. Where the sheet cannot be read, the
   refusal is recorded with what was illegible — a gap stated is worth more than a number
   carried across.
3. #681's memo is re-read against the figures the sheet actually gives, and the difference
   stated either way: if the module it derived survives the reading, say so and by how much;
   if it does not, say that.
4. Nothing moves. Geometry is T-0445's.
