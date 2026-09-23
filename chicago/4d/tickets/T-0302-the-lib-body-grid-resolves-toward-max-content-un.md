---
id: T-0302
title: The .lib-body grid resolves toward max-content under all six other Evidence sections, and only the plants section is fixed
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-09-13
pr: 1246
claimed_by: run 9/13/2026, 5:37:57 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T11:48:36.263Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34752209854
---

The .lib-body grid resolves toward max-content under all six other Evidence sections, and only the plants section is fixed.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`.lib-body` is a one-column grid on the default `auto` track, and an `auto` track resolves
toward MAX-CONTENT. So a `<dd>` holding one long unbreakable run widens the whole card
instead of wrapping inside it, and the panel then CLIPS the text at its right edge rather
than overflowing the document — which is why no assertion has ever seen it: every overflow
check in the suite measures `document.documentElement.scrollWidth`, and the document does
not overflow while every line of reasoning is being cut off.

**Measured 2026-08-28 at 390x780 on the published mirror,** finding it in T-0281: the
plants mount reached **419 px against its 338 px box** and the panel **434 px against 368**.
`.liberties` (the outer grid) was fixed globally in that ticket, because every section that
mounts there had fitted anyway and `minmax(0, 1fr)` changes none of them. The INNER
`.lib-body` fix was scoped to `.plant-vocab` / `.plant-zone` / `.plant-sp` deliberately:
correcting it globally is a layout change to the liberties, the ground, the households, the
wildlife, the exclusions and the still-open list, and T-0281 measured none of those.

So the fault is still latent under six sections. It is invisible today only because their
longest line happens to fit; the first long `<dd>` any of them gains clips silently.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The `.lib-body` track is `minmax(0, 1fr)` for every section that mounts in `.liberties`,
  not only the plants, and the scoped rule T-0281 added is retired into it.
- A check that would have caught this: the MOUNT's own box (`scrollWidth <= clientWidth`)
  is asserted for each of the seven sections at 390x780, not only the document's. T-0281
  added that assertion for the plants section alone and it is the shape to copy.
- Both viewports green, and the six sections are looked at rather than only measured.
