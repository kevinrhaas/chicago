---
id: T-1067
title: The modelled ground stops at n +400 m and all of Kinzie's Addition stands north of it — eleven committed streets and 54 blocks on ground the heightfield does not cover
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-12
closed: 2026-09-14
pr: 1317
claimed_by: run 9/14/2026, 3:04:32 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T08:53:47.622Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34820520379
---

The modelled ground stops at n +400 m and all of Kinzie's Addition stands north of it — eleven committed streets and 54 blocks on ground the heightfield does not cover.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-1062**, which set out to put a viewpoint on the Kinzie Block and could not.

`data/terrain/epochs/e1834_harbor_cut/heightfield.json` boxes the modelled ground at
`n` +400 m. The Kinzie Block's SOUTH face — its nearest edge to the town — is at
+402.72, so the whole block misses the heightfield, by 2.7 m at the near corner and by
about 70 m at the far one. It is not a near miss for the Addition as a whole: T-1060
committed eleven streets whose paths run north to n ≈ +1029, which is 629 m past the
edge, and T-1061's 54 blocks all stand on the same ground.

This is the NORTH counterpart of T-0219, which finishes the heightfield south to Madison
Street. Two things are worth measuring before anything is built:

- What the renderer currently does north of +400. `data/streets/1835.json` already
  carries lines out there and `streets.js` drapes every vertex on
  `terrain.surfaceHeight()`; what that returns outside the box, and what a visitor
  therefore sees standing on Michigan Street looking north (the `kinzie_block`
  viewpoint T-1062 added), is unrecorded.
- What the box would have to become. `terrain_spec.json` § `box_derivation` argues each
  of its four numbers from evidence; `n_max` would need the same treatment, and
  Wright's sheet covers the Addition whole.

**Acceptance:** (stated before working — one demonstration, never weakened to pass)

This ticket is the MEASUREMENT the body above asks for, and the derivation of the number.
The extension itself is a build — a 77 % larger field and 288 rows of ground this spec carries
no micro-relief, substrate, shore or flora for — and is filed as its own ticket rather than
smuggled in under a ticket that opened by asking what is there.

1. What the renderer does north of +400 is MEASURED and committed, not described: every street
   record walked against the renderer's own sampler, with the drawn population separated from
   the platted-and-unopened one, because a record that compiles to no geometry cannot be
   draped on anything and counting the two together would overstate the artefact by two orders
   of magnitude.
2. The box's edge is measured as a walker meets it — metres of perimeter the 0.35 m step-up
   rule will not let a visitor back across — because that is the part of this a visitor can
   find without reading JSON.
3. The reading is re-derivable and gated, so it cannot rot while the box or the street layer
   moves. The gate asserts agreement, never that the gap is small.
4. `n_max` is argued from evidence in `terrain_spec.json` § `box_derivation`, in the same form
   as the other three numbers, including what it costs.
5. What the scene draws off the modelled ground is on the record for a visitor in
   `docs/LIBERTIES.md`.
6. `bash tools/check.sh` green. No bake: no geometry moves.
