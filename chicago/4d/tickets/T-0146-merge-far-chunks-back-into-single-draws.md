---
id: T-0146
title: Merge far chunks back into single draws
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-0149
opened: 2026-08-22
closed: 2026-08-27
pr: 408
claimed_by: run 8/27/2026, 1:53:20 PM CT
blocked_on: null
needs_bake: false
---

Merge far chunks back into single draws.

Piece 2 of 3 of **T-0149 — Win the light tier back as a floor: trim the axial view instead of carrying it**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance**, stated before the work and not weakened to pass:

At the two axial stands — Lake Street east from Canal, and the forks from Wolf Point —
the draw-call count falls by at least a quarter at `full`, **and the triangle count does
not move at all**, at every one of T-0135's five stands and at all three tiers, at both
release viewports. Zero, not a tolerance: the merge is only free while it draws the
identical set, and the ceilings it is meant to help have four figures of headroom. The
2026-08-21 chunking is kept (nothing is un-chunked; a cluster is merged for the frames in
which the frustum is skipping nothing, and drawn in parts again the moment it is not).
Measured by turning the merge off and back on at the same stand, so the saving is
attributable by construction — the method T-0150's reach gate uses, and for its reason.

**Links:** T-0149 (the parent, and why the axial view is the target) · T-0150 (piece 1,
the reach) · T-0147 (piece 3, the ceilings this frees room for) ·
`renderers/web/js/far-merge.js` (the two conditions and why each makes the merge free) ·
`tools/measure_far_merge.mjs` (the instrument).
