---
id: T-0286
title: The AO unwrap leaves 68.9 per cent of every atlas empty, and the map is priced as if it were full
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

The AO unwrap leaves 68.9 per cent of every atlas empty, and the map is priced as if it were full.

Measured by T-0158 and re-derived by T-0227, 2026-08-28, on `sauganash_hotel`:
`smart_project(angle_limit=1.15, island_margin=0.02)` writes **81,458 of 262,144**
texels — **31.1 % occupancy**. The bake is correct; the packing is not. The asset's
master goes 94,420 -> 202,292 bytes with AO on, so a ~107 KB occlusion PNG is spending
roughly 74 KB of itself on blank space.

`assets/gltf/` is 27 MB over 348 masters and the published tree stands at 23.53 MB
against a 25 MB `SITE_BUDGET_MB`. One 512² map each is a ~37 MB ask against ~1.5 MB of
headroom (T-0158's figures), which is what makes the empty two thirds a budget question
rather than a tidiness one: at full occupancy the same coverage fits a 288² atlas.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Occupancy is measured across a representative set of masters, not one — one asset is
  an anecdote about one unwrap.
- One packing change is made and re-measured (island margin, angle limit, or a pack
  pass), with the before/after occupancy and byte figures stated.
- Texel DENSITY on the walls does not fall to buy the occupancy: state the texels per
  square metre on a named wall before and after, because a tighter pack that shrinks
  the islands has bought nothing.
- No claim about how the result looks without a `tools/measure_ao_frame.mjs` reading
  behind it (T-0227's rule: an atlas statistic is not a statement about the walls).
