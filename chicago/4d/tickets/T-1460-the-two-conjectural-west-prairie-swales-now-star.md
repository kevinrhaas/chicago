---
id: T-1460
title: The two conjectural west-prairie swales now start in open ground at E -320 and swale_a's corridor covers eight West Division roofs: review the invented alignments the terrain extension stranded
state: open
epic: GROUND
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-20
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: true
closed_at: null
claimed_run: null
---

The two conjectural west-prairie swales now start in open ground at E -320 and swale_a's corridor covers eight West Division roofs: review the invented alignments the terrain extension stranded.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found while taking the reading T-1444 owed. The West recipe's fourth terrain rule
(`terrain_and_hydrology_gate.rules[3]`) says *"Do not place a roof in the two
conjectural west-prairie swales until their alignments are reviewed after the west
terrain extension; move the roof rather than flattening the swale."* T-1416 made the
extension and T-1444 took the reading. It does not say what the rule assumed.

**What the reading found.**

1. **Both alignments now begin in open modelled prairie.** `west_prairie_swale_a` runs
   from local (-320, -120) north-east; `west_prairie_swale_b` from (-320, 200). Both
   start at E -320 because that was the west wall of the field when they were drawn —
   a drain ending at the edge of the ground reads as a drain leaving the model. Since
   T-1416 the field reaches E -705, so each now starts abruptly, 385 m inside the
   ground, in prairie that carries no hollow and no reason for one.
2. **`swale_a`'s 30 m corridor already holds eight anonymous West Division roofs** —
   seven of the twenty built under the terrain hold, seated 2026-08 while this rule was
   still deferred, and an eighth released by T-1444. Footprint-corner distance to the
   centreline: `recon_1835_west_002` 3.2 m, `_003` 8.9 m, `_012` 12.2 m, `_013` 14.3 m,
   `_009` 16.2 m, `_001` 19.2 m, `_005` 22.7 m, `_011` 26.4 m. `_004` (32.7 m) and
   `_029` (33.3 m) stand clear. `swale_b`'s corridor is empty.
3. **No roof is standing in a hole.** The cut is 0.75 ft over a 30 m half-width — about
   0.008 m per metre — so every one of the eight passes the generator's own 0.35 m
   relief-across-footprint contract and its dry-ground test with room to spare. This is
   a provenance question, not a geometry defect.

**Why it is the owner's.** The rule's remedy — move the roof — assumes the swale is the
fixed thing. It is the conjectural thing: `confidence: reconstructed`, `sources: []`,
and its own note records that T-0795 walked the whole NA/HUP sheet and Wright draws no
watercourse anywhere on the West Division prairie. Moving eight reviewed, baked roofs
to clear an invented line that starts nowhere trades a recorded liberty for an
unrecorded one. The alternatives — re-drawing both alignments onto the extended ground
so they begin at a plausible head and miss the cluster, shortening them, or retiring
them to `record_only` and letting zone 18's swales live in the dossier rather than the
field — are all his call, and each changes the heightfield and needs a town bake.

Until then `generate_west_infill.py` freezes the reading: `SWALE_CORRIDOR_OCCUPANTS`
holds exactly these eight, and the parcel fails to generate if a ninth arrives or one
of the eight quietly leaves.
