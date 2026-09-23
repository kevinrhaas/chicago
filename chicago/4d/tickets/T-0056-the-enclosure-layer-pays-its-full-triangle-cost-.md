---
id: T-0056
title: The enclosure layer pays its full triangle cost at every scene-detail level
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-27
pr: 415
claimed_by: run 8/27/2026, 3:54:05 PM CT
blocked_on: null
needs_bake: false
---

The enclosure layer pays its full triangle cost at every scene-detail level.

Found by T-0052. `renderers/web/js/enclosures.js` builds once, at load, and never consults the
scene-detail level — which cost nothing while the layer was two rail fences and costs real
headroom now that it draws pickets. A pale is a very small box and there are thousands of them.

Measured on the published mirror at 1280 x 800, `light` (the tightest of the three ceilings, and
the one a phone lands on): **597 486 / 600 000** at the first cut of T-0052 — 2 514 triangles of
headroom for the whole rest of the project. Two changes inside that ticket bought it back to
**565 206 / 600 000**: a pale skips its buried underside (12 triangles to 10), and the garden plot
is capped at 28 x 20 ft, which is a research number settled partly by a renderer budget and is
recorded as such at L129. Neither is the fix.

The fix is that the layer should know what detail level it is drawing at. What it must NOT do is
thin the pales or drop them: the rhythm is the record's and a picket drawn as a rail fence is a
misrepresentation, not a saving. Merging the pales of one bay into a single box loses the
see-through, which is the whole point of a fence.

**Acceptance:** at `light`, the enclosure layer draws measurably fewer triangles than at `full`
without changing what the fence is claimed to be, the saving is stated in the PR against the
numbers above, and `tools/smoke_renderer.mjs` keeps its "turning scene detail down actually draws
less" row green with the new figures.

**Links:** `renderers/web/js/enclosures.js` · `docs/LIBERTIES.md` L121, L129 · T-0052.
