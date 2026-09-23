---
id: T-1211
title: Plank sidewalks, stoops, hitching posts and street crossings for every business face, varied by the business — a forwarding house's wide decked walk, a store's board walk and stoop, a smithy's bare ground and rail, a tavern's posts and mounting block — extended to the new fronts town-wide
state: open
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-16
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

The owner: *"include their correct plank sidewalks for each business that varies because business
vary and fill it in so it is complete."* The street-edge layer (`data/frontage/town_street_edge.json`,
`tools/generate_frontage_works.py`, `renderers/web/js/frontage.js`) holds 77 walks, 31 fences
and 16 posts, dealt to the documented fronts; the new business fronts of the build tickets have
none. Drawn at load — no bake.

**Acceptance:**

- A **frontage-by-business rule** in `generate_frontage_works.py` (and recorded in the placement
  policy): per business type — walk kind (decked plank walk / board walk / none), width, plank
  run and step, rise, stoop or none, hitching posts (count by trade: taverns, stores, the livery),
  a mounting block at the inns, a crossing at the corners of the principal streets, the bare
  ground and rail at the works trades, the wagon apron at the warehouses and forwarding houses —
  each with its evidence (the documented walks, the *American*'s sidewalk notices, the 1835
  ordinances the layer already cites) and tier.
- Applied to every business face in the address book (attested, inferred, reconstructed), the
  record naming the business it serves (`belongs_to`) and the rule; the documented 77 unchanged
  unless the rule finds one inconsistent with its own evidence (stated, not silently moved).
- `generate_frontage_works.py --check` green; walks never enter a corridor's roadway beyond the
  kerb rule; **visible** at both viewports: a walk along the whole of South Water and Lake, and
  the variety readable from one screenshot.

**Stop condition:** every business front has the street edge its trade would have had.

**Links:** T-0003 · T-0038 · `data/frontage/` · T-1190 · T-1195.
