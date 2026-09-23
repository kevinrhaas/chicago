---
id: T-0049
title: Unpainted boards as a surface: board-width irregularity and lap rhythm
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: S
legacy_id: K4
parent: T-0002
opened: 2026-08-17
closed: 2026-08-19
pr: 269
claimed_by: run 8/19/2026, 8:01:02 PM CT
blocked_on: null
needs_bake: true
---

Piece 2 of 2 of **T-0002 — Weathered facades: unpainted boards, no two buildings alike**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**NEEDS THE BAKE.** Board width, lap rhythm and the weatherboard's own relief come from
`generators/archetypes/`, which needs Blender; the improve runner has none, so this closes on the
nightly `chicago-4d-bake.yml` or on a runner that has one. T-0048 deliberately shipped no invented
texture and no normal map in its place.

**Acceptance:** two neighbouring frame buildings show visibly different board widths or lap
courses in the `south_water` critic frame, from a parameter derived from the records rather than
dealt at random, with what is invented graded and recorded in `docs/LIBERTIES.md` (it extends L22
and L23).
