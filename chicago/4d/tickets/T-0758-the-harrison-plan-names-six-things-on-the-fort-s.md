---
id: T-0758
title: The Harrison plan names six things on the fort's ground that this model has never drawn: Well, Wash house, Big Barn with Cupola, Shop, Out Buildings and the Fort Cemetery
state: split
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-06
pr: null
claimed_by: null
blocked_on: null
needs_bake: true
closed_at: 2026-09-06T10:33:23.841Z
claimed_run: null
---

`harrison_1830_river_mouth` is the only plan of Fort Dearborn this project has found, and
eleven committed records come off it — the palisade, the blockhouse, the barracks, the
officers' and commandant's quarters, the magazine, the guard house, the store house, the
sutler's store, the parade — plus the garrison garden, which stands OUTSIDE the pickets on
the same sheet. So the plan is trusted, and it is trusted for things in the outer enclosure.

What it also names, and nothing draws: **Well, Wash house, Big Barn with Cupola, Shop, Out
Buildings, Fort Cemetery.** Hubbard corroborates two of them independently — the well *"was
in the outer inclosure and near the south gate"*, and *"rude wash-houses"* stood on the low
sandy beach east of the pickets (`hubbard_autobiography_1911`, leaves 75-76, printed pp.
37-38). The fort's ground is therefore the emptiest documented acre in the model.

**Opened out of T-0592**, which read the town's water question and refused a well class for
the town (`docs/RESEARCH/wells.md`) — and found while refusing it that the fort's well is a
different question, resting on a plan and a memoir rather than on a distribution. This
ticket is that question and the five things standing next to it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Each of the six is either placed off the plan with a stated grade and its own note, or
  refused in writing with the reason on the record — no silent omissions.
- Both witnesses are pre-1835: the plan is dated 24 February 1830 and Hubbard's narrative
  stops in November 1830. Anything placed carries that in its `documented_range` note, and
  its standing on 1 July 1835 is argued from the garrison's continuity to the evacuation of
  29 December 1836 rather than assumed.
- The plan carries NO SCALE BAR and its source record says it is used *"for ARRANGEMENT AND
  PROPORTION rather than for absolute size"*; every size taken here obeys that.
- Any new archetype is a bake: `./tools/bake.sh --only` per structure and `tools/publish.sh`
  in the same commit. This is very likely more than one run — `split` it rather than
  half-shipping it.

**Links:** T-0592 · `docs/RESEARCH/wells.md` · `data/sources/harrison_1830_river_mouth.json` ·
`data/sources/hubbard_autobiography_1911.json` · `data/structures/fort_dearborn_*.json`
