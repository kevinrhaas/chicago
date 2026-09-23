---
id: T-0790
title: Wabansia, surveyed 1831, is drawn whole north of Kinzie Street — eight streets, some 79 blocks and a water-lot tract on the North Branch — and the town has none of it
state: split
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-12
pr: null
claimed_by: run 9/12/2026, 6:19:24 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T11:31:27.773Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34690549976
---

**The source, 2026-09-05.** The owner added a second copy of J. S. Wright's manuscript survey of
1834 at `chicago/pre_fire_v1/maps/images/1834-wright-map.jpg` — the Historic Urban Plans (Ithaca) reproduction of the
**National Archives original**, 5050 × 6628 px at 600 dpi, with its own caption: *"Two portions are
missing, the larger being near the lower center … the manuscript was mounted on cloth to repair this
tear."* It is a different scan of the same drawing this project already traces as `wright_1834`
(the BPL/Leventhal copy, 4204 × 5166 px, IIIF `commonwealth:js957744g`). The owner's instruction:
*"review this and create tickets to update and enhance the map … several items from this map should
be incorporated including the streets, there are streets documented here that are missing, including
the blocks, where the public square is, where the various sloughs are, things like 'the kinzie block'
… look at all of the streets and block numbers … the lakeshore edge and that whole area … the whole
path of the river going south … note the sections as labeled in the legend."*

## What the sheet shows

North of Kinzie Street and west of the North Branch, Wright draws the tract the legend colours red
— **"Wabansia, surveyed in 1831"** (Wright spells it *Wonbonsia*; the Democrat and later sources
give *Wabansia* / *Wabonsia*, after the Potawatomi Wabansi):

- **East–west streets, north → south:** Free · Trade · Sailors · Right · Owen · Hubbard, with
  Kinzie Street as the tract's south line. The owner's own reading of the crop, 2026-09-05:
  *"kain, owen, hubbard, right or hight, sailors st, trade st"* — **two of these are doubtful on
  the crops** and must be read on the registered scan: *Right* may be *Hight*, and *Kain* may be
  *Kane*. Write the doubt into the record, not a guess.
- A **Water Street** and a street Wright letters *Kain* (to be re-read on the registered scan — it
  may be *Kane*) inside the **triangular water-lot tract** wedged between the grid and the North
  Branch, drawn in red with some 30 narrow numbered lots fronting the river.
- **Blocks numbered to 79**, in tiers, the river-side blocks cut by the North Branch's bank.

## What the project has

Nothing. `data/streets/1835.json` has no street north of Kinzie west of the river; no block, no
lot, no tract. The North Division parcel says in terms: *"Wabansia and the west side of the North
Branch require a separately traced hydrology parcel"* — the ground was deferred, and the plat with
it. The forks trace (`river.geojson`) carries the North Branch only as far as its window.

## Why it matters in 1835

Wabansia is where the town's first speculative addition was laid out, two years before Kinzie's,
on the Kinzie family's own claim — and it was largely unbuilt on the scene date. That is exactly the
kind of ground the owner's note about the south applies to as well: **a platted grid on prairie, no
alleys, streets surveyed and not worn.** The town should show a surveyed emptiness there, not a
blank, and not a suburb.

## The ask

1. **The streets into `data/streets/1835.json`** with `wright_1834` (and T-0787's scan) as source,
   graded for what they are: surveyed lines, with a `status` that says whether the sheet shows them
   as opened. Read the corridor width off the sheet.
2. **The blocks numbered**, tract-keyed, every numeral cited to its crop; the water-lot tract
   recorded as a lot strip (as T-0789 does for Kinzie's Addition's river front).
3. **The tract's edges** — its north line, its west line where the sheet's grid stops, and the
   North Branch bank that cuts it — as the polygon T-0792 will carry.
4. **Say what stood there.** Search the corpus — the Democrat's 1834 land notices, Andreas, the
   1839 directory — for anyone *at Wabansia* on or before 1 July 1835, and for the tavern and the
   two or three houses the sources put on the North Branch. A tract with 79 blocks and three roofs
   is a true reading; write the three, not the 79.
5. Depends on the North Branch being traced through the tract (T-0794); the grid can be authored
   before the water, but its river-side blocks close only once the bank is there.

**Done when** Wabansia's eight streets and its blocks are in the data, its water lots are a
recorded strip, its edge polygon exists, and the town shows the tract as surveyed prairie with
whatever the sources put on it and nothing more.
