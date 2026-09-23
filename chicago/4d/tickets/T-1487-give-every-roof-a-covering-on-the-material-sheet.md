---
id: T-1487
title: Give every roof a covering on the material sheet: shingle and roof_board substrates at L263's tile, a dealing rule argued by archetype and the liberty for what it asserts beyond materials.md 2.2, every roof material named for the covering it carries, and the town baked
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: T-1465
opened: 2026-09-20
closed: 2026-09-20
pr: 1591
claimed_by: run 9/20/2026, 2:31:55 PM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-20T21:26:58.208Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35532164463
---

Give every roof a covering on the material sheet: shingle and roof_board substrates at L263's tile, a dealing rule argued by archetype and the liberty for what it asserts beyond materials.md 2.2, every roof material named for the covering it carries, and the town baked.

Piece 1 of 2 of **T-1465 — Give every roof its covering and its texture before the 297 are built: shingle and roof_board substrates on the sheet, dealt by archetype, bound to the vendored relief maps on L263's exposure — a roof nobody can see the material of is not a reconstruction, it is a gap**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Why this is piece 1.** The parent asks for the sheet AND the relief binding in one run.
The binding cannot be done in one: `generators/build.py` `unwrap()` runs
`bpy.ops.uv.smart_project` per object, which is a PER-OBJECT ISLAND PACK in 0..1 — the
layout an AO bake wants. A 4.48 m shingle tile needs UVs in METRES, and there is no second
UV set and no triplanar path in `renderers/web/js/buildings.js` today. Laying metric roof
UVs is a generator change on every archetype plus its own bake plus a draw-call
measurement, which is T-1488. What this ticket does is everything that comes first and
gates nothing on that question.

**Acceptance:**

- `materials.py` gains **`shingle`** and **`roof_board`** substrates. Shingle at L263's
  tile — 4.48 m, 0.14 m exposure, 32 courses, 228.6 px/m. `roof_board` at `sawn_board`'s
  4.00 m. Both carry their §2.2 grade and their evidence in the row, as every other
  substrate does.
- **No roughness is re-argued.** §3.1 says in terms that the deliverable is a roughness
  map, not better constants, and that a round should not be spent re-tuning the 18 numbers.
  So `shingle` takes the 0.90 the framed archetypes already ship and `roof_board` takes the
  0.93 `outbuilding.py` already ships — NOT `sawn_board`'s 0.94. Not one float in the town
  moves; what moves is that each roof is now drawn on a row that says what it is.
- **A dealing rule, argued and written down**, in `materials.py` as `roof_substrate()`:
  an outbuilding takes boards, every other roofed building takes a shingle field.
- **The liberty for what that asserts beyond §2.2.** §2.2 grades shingle for a FRAMED
  building; the rule above also gives it to the 49 log dwellings and the fort's garrison
  buildings. That is a claim, it takes an L-number in the form L263 used, and the L-number
  is what a reader finds when they ask why a cabin is shingled.
- **`roof_plane` survives as the fallback and nothing else** — and the row says so and
  carries zero records rather than being deleted, so a reader can see the question was
  answered rather than removed.
- Every roof material in the GLB is **named for its covering** (`roof_shingle`,
  `roof_board`) rather than `roof`. The name is the generator's own honest label and is
  explicitly NOT offered as a renderer key: `docs/GLB-CONTRACT.md` says material names are
  not pinned and a renderer keyed on one would be reading a convention nobody promised to
  keep. Which carrier T-1488 reads — a pinned name, or material extras — is T-1488's to
  propose.
- The palisade's mis-named `roof` slot, which draws two GATE LEAVES and not a roof, is
  renamed `gate`, so that "every material called roof states its covering" is true of the
  town and not true-with-one-exception.
- **Bake** (`needs_bake`): `materials.py` is under `generators/common/`, which
  `mesh_inputs` hashes for every archetype, so the whole town stales. Full bake in the same
  commit, and `check.sh --stale` is what proves it landed.
- The roof **condition** grading is untouched.

**Stop condition:** no roof in the town is drawn on a substrate whose covering is unstated,
and the liberty that says why is recorded where a reader can find it. What a visitor can
SEE is T-1488.

**Links:** T-1465 (the parent) · T-1488 (the binding) · L263 · T-1450 · `docs/RESEARCH/materials.md` §2.2, §3.1.
