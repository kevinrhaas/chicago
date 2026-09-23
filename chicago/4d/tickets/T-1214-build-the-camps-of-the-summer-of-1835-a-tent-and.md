---
id: T-1214
title: Build the camps of the summer of 1835: a tent and wagon-camp archetype, the encampments on the grounds the transient ticket evidenced — the land-sale crowd south of the fort, the immigrants' wagons at the west approach, the pier gang at the river mouth — bounded, labelled, and empty of figures
state: open
epic: TOWN
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: true
closed_at: null
claimed_run: null
---

No tent, encampment, wagon camp or lodge exists in any form: no record, no archetype
(`generators/archetypes/` has nine), no family, no exclusion, no liberty. T-1178 wrote
the people and the candidate grounds (`1835_camp_grounds.json`); this ticket gives them ground
and canvas. Native and Métis camps of families in town to trade or awaiting the annuity payment are IN
scope on the owner's 2026-09-17 ruling — sized and placed from T-1177's evidence, every such
record `review_required` + `touches_removal`, a lodge form added to the archetype only where a
source describes one; the August 1835 gathering is weeks after the scene date and is NOT
staged (AGENTS.md § Standing constraint, restated on every record).

**Acceptance:**

- A `camp` archetype (`generators/archetypes/camp.py` + `camp_params.py`): wall/wedge tents on
  poles, a covered wagon (the box and bows), a brush shelter, a cooking fire ring and a woodpile,
  parameters for count, arrangement (row, ring, scatter), canvas condition; `CONSUMED`,
  `GROUND_CONTACT`, `CONFIDENCE_VALUE` like its siblings; a family code added to the inventory
  (`X1 camp`) with a target from the transient bracket; the schema's `archetype` enum extended.
- Records placed on the camp grounds by T-1199's rows, tested for dry ground, outside
  every corridor and no-build region except where a region permits (`fort_dearborn_reservation`
  `permitted[]` — the lake shore south of the fort is a decision the record states), each with
  `occupants` = the transient party and the evidence sentence that put a camp there.
- Bake (`needs_bake: true`); `smoke_renderer.mjs` at both viewports; LIBERTIES entry with scope;
  L1 restated — no figure, no smoke-as-a-person, canvas and wagons only.
- **Visible:** a screenshot from the fort's south-west corner shows the camp on the shore.

**Stop condition:** every transient party has a camp to be counted at, and the camps read as
the summer of the land sale.

**Links:** T-1178 · T-1199 · `data/reconstruction/1835_no_build_ground.json` ·
AGENTS.md § Standing constraint · L1.
