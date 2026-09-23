---
id: T-0118
title: The sloughs as built: the bay, the sill, the trench and the too-straight course
state: done
epic: GROUND
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-20
closed: 2026-08-20
pr: 284
claimed_by: run 8/20/2026, 3:43:46 PM CT
blocked_on: null
needs_bake: true
---

The sloughs as built: the bay, the sill, the trench and the too-straight course.

**The owner, 2026-08-20, walking the new sloughs on the dev preview** (T-0005, PR #273,
merged hours earlier) with an 1830s engraving of a prairie watercourse beside them. Four
faults, and the spec explains every one of them.

## 1. The bay at the State Street mouth — it should empty straight into the river

*"there is a small almost a bay in the river near where the slough is, i think that bay
should be removed and the slough should empty straight into the river as depicted in this
picture, and not curve like that."*

`state_slough_mouth` runs north to about (809.3, +14.5) and then **turns east and runs
ALONG the shore** — (816, 21) · (824, 20.5) · (836, 20.5) · (842, 18) · (848, 13) — at
`depth_ft` 6.2, the deepest cut in the spec. A six-foot trench dug parallel to the bank
for thirty-odd metres is the bay: the water fills the pocket between the course and the
river instead of joining it.

The dogleg exists because the entry is pinned to two fixed points that are not in line —
the Slough Log Bridge's committed deck at E +805…+813, N +14, and Wright's traced mouth
at about E +848. The course visits the bridge, then walks east to the mouth. **The
engraving shows the resolution**: a watercourse meets open water square, in one reach,
without a shore-parallel pocket. Straighten the last reach so it enters the river; if the
traced mouth and the bridge cannot both be honoured by a straight line, say which one
moves and why on the record.

## 2. The La Salle slough is interrupted by a piece of land

*"the second slough does not go through, it is interrupted by a piece of land."*

Two entries, one watercourse, and they **step**: `lasalle_slough_lower` cuts
`depth_ft` 3.2 (≈0.98 m) and `lasalle_slough_upper` only **1.8** (≈0.55 m), meeting at
(479, −108). Water is drawn wherever the ground falls below `SHORE_Y` (−0.10 m), so the
deep reach fills and the shallow one does not — and the join reads as a **dry sill
across the channel**.

Note the tension before changing a number: PR #273 chose "wet mouths, damp inland
courses" deliberately, because the dossier's own thalweg for these sloughs sits ABOVE
datum, and a continuous below-datum cut would contradict the row it was built from. So
this is not simply "make it deeper". Either the bed drops (a claim about the land, needing
its own liberty and a note) or the transition is graded so the reach shallows out
gradually instead of ending at a wall — but the visitor must not meet a hard edge of land
sitting in the middle of a watercourse.

## 3. The inland end leaves a trench that should level out

*"where the slough ends in the city and is filled with water, there is a depression for
the slough that keeps going but it should not, it should level out with the rest of the
land."*

Every course carries a constant `depth_ft` to its final vertex and then stops:
`state_slough_course` at 2.2 ft to (596, −340), `lasalle_slough_upper` at 1.8 ft to
(497, −228). Nothing tapers, so the carve ends as an open-ended ditch running into level
prairie. **A watercourse's head should feather out to grade** over its last reach, so the
ground closes over it rather than being cut away to a stop.

## 4. The course is too straight

*"it is too straight, i think it curved more at an angle according to the image."*

`lasalle_slough_lower` + `upper` together run E +467 → +497 across 220 m of northing —
essentially a north-south ruled line with a slight kink. The engraving shows a prairie
drain that **meanders and crosses the ground at an angle**, and the reference the owner
supplied is the standard for the look. Give it plan curvature. Where the alignment is
already fixed by traced points, keep them and bend between them — the invented part is
what happens between the fixings, and it is `reconstructed` either way.

**Acceptance:** from the owner's stand and from the air, the State slough enters the river
in one reach with no shore-parallel pocket; the La Salle slough reads as one continuous
watercourse with no dry sill across it; neither course ends in an open trench — both
feather to grade; and the La Salle course carries plan curvature rather than a ruled line.
Every changed number keeps its liberty entry, the ground-contact gates stay green, and the
terrain is rebaked in the same commit.

**Links:** `data/terrain/epochs/e1834_harbor_cut/terrain_spec.json` (`swales`:
`state_slough_mouth`, `state_slough_course`, `lasalle_slough_lower`, `lasalle_slough_upper`)
· T-0005 / PR #273 · `docs/RESEARCH/main_branch_sloughs_1833.md` · L149/L150 ·
`renderers/web/js/terrain.js` (`SHORE_Y = -0.10`) · T-0119 (the plank walk over the mouth).
