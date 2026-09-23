---
id: T-0005
title: The three Main Branch sloughs, from the 1833 map
state: done
epic: GROUND
requested_by: owner
seen: true
effort: M
legacy_id: K13
parent: null
opened: 2026-08-17
closed: 2026-08-20
pr: 273
claimed_by: run 8/20/2026, 4:36:15 AM CT
blocked_on: null
needs_bake: true
---

**The owner's ask (twice):** "refer the 1833 map for the locations and terminus of the
several streams coming in." The 1830 Thompson plat shows THREE sloughs off the Main Branch;
only the La Salle re-entrant's mouth is traced today.

Identify the three; carry the attested ones as hydrology centrelines with termini from
Conley/Stelzer 1833 as S2e already establishes.

**Acceptance:** each slough present or its absence argued in the record; the La Salle
re-entrant reaches its terminus. Deep history: § K13 (~9714).

**Marked `needs_bake` on 2026-08-18 (steward, PR for T-0080), measured rather than assumed.** It
was authored `false`. Any new centreline added to `data/terrain/epochs/<e>/hydrology.geojson`
changes the prose-stripped input document `generators/terrain_inputs.py` hashes, which IS
`assets/manifest.json`'s `inputs_sha256` for `terrain__e1834_harbor_cut.glb` — so `tools/check.sh`
reports the ground stale and refuses the commit until Blender rebuilds it. The research half
(identifying the three, arguing the absent ones) needs no bake; the half that puts a slough in the
scene does. Split it that way if the research is worth a run on its own.
