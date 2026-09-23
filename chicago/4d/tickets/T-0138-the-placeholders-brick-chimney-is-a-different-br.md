---
id: T-0138
title: The placeholders' brick chimney is a different brick from the archetypes'
state: done
epic: RENDERING
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-22
closed: 2026-08-28
pr: 434
claimed_by: run 8/27/2026, 11:47:16 PM CT
blocked_on: null
needs_bake: false
---

The placeholders' brick chimney is a different brick from the archetypes'.

`generators/inferred_placeholder.py` paints its 90 committed masters' stacks
`placeholder_chimney_brick` at `#89503F` — (0.537, 0.314, 0.247) linear. T-0008 gave the 112 brick
stacks on the archetype buildings the sheet's `CHIMNEY_BRICK` at (0.45, 0.23, 0.17), which is
`frame_tavern`'s committed value off the Petford watercolour. The two are about 20 % apart in
linear red, standing on the same streets, and R-W2a finding 4 already named this shape of split:
*"an atlas that textures one path and not the other splits the town visibly in half."*

Converging them means picking which value survives and REGENERATING 90 masters, which moves their
compressed derivatives and the banked passthrough set with them (K38 — `--write-baseline` in the
same commit). That is why T-0008 did not smuggle it in.

**Acceptance:** one brick value reaches both generators, argued rather than picked; the 90
placeholder masters and their derivatives are regenerated in the same commit with the passthrough
baseline re-banked; before/after frame at a stand holding both a placeholder and an archetype
building. Gates green.

**Links:** T-0008 · T-0007 (the same convergence for the hewn log) · `docs/RESEARCH/materials.md`
§4 finding 4 · `docs/RESEARCH/chimneys.md` §4 · ROADMAP K38.
