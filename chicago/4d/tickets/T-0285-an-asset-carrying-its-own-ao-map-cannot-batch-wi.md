---
id: T-0285
title: An asset carrying its own AO map cannot batch with the town: +2 draw calls for one building
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

An asset carrying its own AO map cannot batch with the town: +2 draw calls for one building.

Measured by T-0227, 2026-08-28. `sauganash_hotel` baked with `--ao` and swapped into
the source tree raised the draw count at **every** station and viewport by exactly two:
`sauganash` desktop 112 -> 114, mobile 104 -> 106; `sauganash_wing` desktop 139 -> 141,
mobile 122 -> 124. Triangles were identical in all four. The cause is not the texture,
it is the key: `materialKey()` in `renderers/web/js/buildings.js` includes
`m.aoMap?.uuid`, and it has to — a batch is one draw with one material, so a mapped
material cannot merge with an unmapped one.

**Why it matters to R-W3a and not only to this one asset.** Every master gets its own
baked 512² atlas, so every master gets its own `aoMap` uuid, so no two AO'd buildings
can batch with each other either. The town's whole batching strategy is built on
buildings sharing a handful of materials. Nobody has measured what a fully-AO'd town
costs in draws, and the ceilings are breached already (T-0223, T-0271) — so this
number has to exist before the cage parcel bakes 348 maps, not after.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The draw-call cost of AO on the town is MEASURED, not reasoned: bake a
  representative set with `--ao` (or all of them) and read the draw count at the
  critic stations at both viewports, against the same tree without it.
- The answer names which of the three routes it implies — a shared atlas across
  masters, a per-batch atlas built at load, or AO per-vertex — and what each would
  cost. Refuting the concern (the town batches fine) is a legitimate outcome.
- The figure lands in `docs/ROADMAP.md` R-W3a beside the byte cost, so the cage
  parcel starts from both.
