---
id: T-0793
title: The river's mouth is wrong at its east end: re-trace the piers, the cut, the sand bar to its southern tip, the old channel to where Wright closes it, and the shore south to the sheet's edge
state: split
epic: META
requested_by: owner
seen: false
effort: L
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: null
claimed_by: null
blocked_on: null
needs_bake: true
closed_at: 2026-09-05T15:33:50.940Z
claimed_run: null
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

*"the lakeshore edge and that whole area, you currently dont have that whole edge where the river
comes out and ends correct — this area of where the river goes and where the sand bar ends needs to
be addressed."*

## What the sheet shows, east of State Street

- **The 1834 cut**: two straight, parallel pier lines from the river's bend at the fort, north-east
  into the lake, lettered *Harbor*, with a direction arrow down the channel.
- **The old channel**: from the same bend, the river's former course turns **south** behind the bar
  — drawn as open water, shaded like the river, narrowing as it runs, its own arrow still pointing
  south — and **closes** at about the line of Madison Street, where the lake shore takes over.
- **The Sand-bar**: the tongue of land between old channel and lake, lettered *Sand-bar*, from the
  south pier down to where the channel closes — about half a mile.
- **The lake shore south of the bar**: one continuous line from the bar's southern tip down the
  whole east edge of the sheet, the brown *Fractional Section 15* strip inside it, to the bottom
  margin below the School Section's south line.
- **Fort Dearborn** as a drawn quadrangle on the bend, and beside it *L. House* — the lighthouse
  (`data/structures/chicago_lighthouse_1832.json` holds the structure).
- The **U.S. Military Reservation** outlined in blue: the river on the north, the old channel on
  the east, Madison's line on the south.

## What the project has, in its own words

`data/terrain/epochs/e1834_harbor_cut/shoreline.geojson` traces the harbour reach off the BPL scan,
and its provenance is honest about where it stops:

- *"The EASTERN boundary of this polygon is the traced window, not a shore."*
- South shore: *"Beyond about N −580 it leaves the traced window; the shore and the old channel
  continue south of there and are not traced."*
- North shore: *"BETWEEN THE PIERS THIS IS NOT A NATURAL SHORE … the piers are structures with
  phases, so they are not modelled here."*
- The bar: *"NO ELEVATION IS CLAIMED HERE"*; and in the terrain spec, *"THE HEIGHT OF THE BAR IS
  CHOSEN, NOT FOUND, AND IT IS THE ONLY LAND SURFACE IN THIS BOX THAT IS."*
- The old channel is graded `reconstructed`: *"the abandoned channel behind the spit, which the
  dossier … marks CONJECTURAL for its 1835 state."*

So the mouth, as built: a window-bounded water polygon, a bar with an invented height, an old
channel that stops at N −580 instead of closing, no piers, and no lake shore south of the fort at
all. The owner's reading is correct.

## The ask

1. **Trace the whole east edge off the registered scan** (T-0787), whose window is the full sheet:
   both pier lines, the cut between them, the bar's outline to its southern tip, the old channel's
   west bank to where Wright closes it, and the lake shore from there to the sheet's bottom margin.
   One continuous shore run, not a window.
2. **Where the old channel ends is a stated reading, not a window.** Wright draws it closing near
   Madison's line; the dossier (zone 26) says *"silting into a lagoon/slough"* and
   *"conjectural for 1835 state."* Write the closure as the sheet draws it, dated 1834, graded for
   what a year of silting could do to it, and say so — the town shows a narrowing backwater ending
   in sand, not a canal.
3. **The piers as structures.** Two pier lines with the length the sources give for 1835 —
   docs/research/01-terrain-hydrology.md § 3.2: north pier between 700 ft (1834) and 1,850 ft
   (1837), *"interpolate ~1,000–1,300 ft, flagged inferred"* — drawn from the bend on Wright's
   alignment, as `data/structures/` records with phases, not as terrain.
4. **The bar's height, argued.** Still chosen, but from something: the dossier's beach-ridge
   figures, the 1839 Fort Dearborn Addition plat's *"at best a low sandbar"*, and the fact that
   the 1834 cut went through it. Write the argument where the terrain spec already admits the
   number is chosen.
5. **The reservation's blue edge** as T-0792's polygon, closing on the traced old channel; the
   lighthouse checked against *L. House* on the sheet.
6. Replaces the shoreline trace's east half; the forks trace west of E +314 is untouched. Re-bake
   the terrain epoch; the water/land polygons must close.

**Done when** the mouth, the bar to its tip, the closed old channel and the lake shore to the
sheet's edge are one traced run off the full sheet with no window boundary in it, the piers stand
as structures, the bar's height has an argument, and the terrain bakes with the land and water
closed.
