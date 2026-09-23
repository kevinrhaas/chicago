---
id: T-0098
title: Trees at the fort, which the plate puts in a mass east of the walls
state: done
epic: TOWN
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-24
pr: 370
claimed_by: run 8/24/2026, 9:53:54 AM CT
blocked_on: null
needs_bake: false
---

Trees at the fort, which the plate puts in a mass east of the walls.

Found by T-0044's image-accuracy pass. `p4_0` draws a substantial tree mass immediately east of the
stockade, around the two-storey frame house outside the walls; `p4_1` shows trees round the buildings
on both banks. The render has none at the fort. The placed-planting record kind that T-0091 built for
the Sauganash's yard (`data/flora/plantings/`) is exactly the mechanism, and it needs no bake.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

A planting record stands trees where the plate puts them, each stem inside its species' recorded
height band with the renderer refusing any that is not, the liberty is recorded, and a before/after
from `p4_0`'s stand is committed.

**Correction, 2026-08-24 — the mass is WEST, and the title is what was wrong.** The acceptance
above is unchanged and is met exactly as written: it asks for trees *where the plate puts them*.
Where the plate puts them is not east. `tools/measure_fort_trees_plate.py` segments `p4_0` for
foliage and splits the mask at the two ends of the drawn stockade: **33 334 connected px of canopy
on the frame-RIGHT**, running off the edge of the picture, against a largest frame-left component of
**924 px of bank grass on the viewer's own side of the river**. And frame-right is WEST — the plate's
stand is the north bank looking SOUTH, and the committed `chicago_lighthouse_1832`, 46.8 m west of
the fort's centre, draws to the frame-right of the fort in the render from that same stand. This
sentence and T-0044's row 8, from which it was inherited, were both read by eye. Written up in
`docs/RESEARCH/fort_dearborn_image_accuracy.md` § "Row 8's east is west".
