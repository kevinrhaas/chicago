---
id: T-0794
title: The two branches run to the sheet's edges and the town's traces stop at the box: the South Branch through the School Section and the North Branch through Wabansia, off Wright
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
claimed_by: run 9/12/2026, 7:02:24 AM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-12T12:13:45.458Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34692358283
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

## The owner, 2026-09-05

*"and the whole path of the river going south and all of those."*

## What the sheet shows

- **The South Branch**, from the forks at Wolf Point, runs south-south-west through the Original
  Town between Canal and Market Streets, crosses Madison into the School Section, and winds down
  through **blocks 70, 71, 78, 83, 84, 85, 86, 87, 88** to the section's south line and off the
  sheet — with the *Reserved* blocks 87/88 on its east bank and the manuscript's larger tear on top
  of them (T-0787).
- **The North Branch**, from the forks, runs north-north-west between Wabansia's water lots and
  Kinzie's Addition's western edge to the top margin of the sheet.
- Both branches are drawn with a bank on each side, shaded as water, with the river-side blocks'
  lot lines stopping at the bank.

## What the project has

`data/terrain/epochs/e1834_harbor_cut/river.geojson` traces the forks — *"main stem, North Branch
and South Branch, traced from Wright 1834 by tools/trace_river.py"* — within a window. The terrain
stops at N −400 (Washington), and T-0465 records why: *"the present terrain stops because the
committed South Branch trace stops near N −405."* Above the forks the North Branch stops at its
window too, which is why the North Division parcel defers Wabansia to *"a separately traced
hydrology parcel."* Both branches are graded `inferred` for bed depth with no source at all
(`sources: []`).

T-0465 already asks for the South Branch *"through the expanded field"*, and names its evidence as
*"period maps, surveys and later historical shoreline reconstructions."* **This ticket names the
map.** Wright draws the South Branch through the whole School Section at survey scale; there is no
better 1834 source for its course, and it is already registered.

## The ask

1. **Trace both branches to the sheet's edges off the registered scan** (T-0787) with
   `tools/trace_river.py`'s own method, so the new run splices onto the existing forks trace at its
   window without moving a vertex inside it — the blast-radius rule the shoreline trace already
   follows.
2. **Say where the tear is.** The South Branch's east bank at blocks 87/88 crosses the manuscript's
   missing portion; that reach is graded down and the gap boxed, not drawn through.
3. **The blocks the river cuts.** Hand T-0791 the bank so blocks 70/71/78/83–88 (School Section)
   and the West Division's river-side blocks close on water; hand T-0790 the North Branch bank for
   Wabansia's water lots.
4. **Depth stays inferred and says so** — the sheet gives planform, not soundings; do not let a
   traced bank promote the bed.
5. This is T-0465's evidence step and T-0464's ground has to arrive for it to bake south of
   Madison; file the trace now so the ground has a river to meet.

**Done when** both branches are continuous traces from the forks to the sheet's margins, spliced
onto the existing trace byte-for-byte inside its window, the tear is boxed, and the river-side
blocks of three tracts can close on the bank.
