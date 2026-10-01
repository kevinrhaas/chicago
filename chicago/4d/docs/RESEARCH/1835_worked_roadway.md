# The worked roadway — T-1811 (piece 1 of T-1770)

The owner, 2026-09-30: replace the paired-tread look with a full dirt roadway. This piece is
the SURFACE. Grading the roadbed below an entrance-level walk shelf, with the terrain and
walker collision moved, is T-1812, and nothing here claims it.

## What changed

`renderers/web/js/streets.js`. Before this, `roadTexture` drew two Gaussian ruts at 0.29 and
0.71 of the recorded track over a translucent body (alpha 0.28–0.93, capped at 0.92). From
every distance that read as two brown treads with the prairie showing between and through
them. Now:

- **Width.** Each opened street draws a *worked width* derived from its traffic class: 0.80 /
  0.64 / 0.44 of the 80 ft corridor for principal / ordinary / light. It is never less than the
  recorded `track_width_m`, which stays the opaque core (at least half the worked width), and it
  never reaches the walks (the corridor less 2 × (1.83 m walk + 0.2 m clearance) = 20.3 m).
  `track_width_m` is unchanged in the data, so no generator moved anything.
- **Surface.** It is opaque packed earth: dry dust tones times T-1797's shared grit tile (one
  256 px canvas for the whole town). The tones sit between T-1797's dirt pair and its grey
  sand; the smoke chose where, as described below. The wear is value noise laid in each street's
  OWN frame (u across, metres along). That gives many overlapping lanes 11 × 1.3 m and
  4 × 0.55 m, wandering over ~23 m. On top of them are narrow ruts (9 × 0.32 m cells, cut at
  the crest), mud where 8 m / 2.6 m wetness meets heavy wear, and a 35 m broad tone. Relief is
  the grit's normal in a world tangent frame, levelled where it is wet.
- **Shoulders stop at a fill's flank.** Past the recorded track, a shoulder ends where the
  ground falls more than 0.35 m from the crown (read in 0.5 m steps). The first pass draped the
  worked width down the flanks of the bridge approach fills, and the fill's crest rose 0.58 m
  through the ribbon between vertices: Kinzie's approaches at E −115 and E −47, and Dearborn's
  drawbridge fill. After the change the worst is 0.22 m, against the smoke's 0.35 m.
- **Joint fans are clipped, not dropped.** A fan whose rim reached the waterline used to be
  dropped whole. That never happened at the old 5.25 m half-width and always did at 9.75 m,
  which reopened T-0184's wedge at South Water's 17.8° bend. Each rim vertex is now pulled back
  along its own ray by the reach the panels use. 21 of 21 fanned joints draw.
- **Edges.** Past the core the shoulders give way to grass as clumps (1.1 m) once a jittered
  ramp passes each clump's value, so there is no ruled line. A light street keeps sod islands
  between its lanes as well: the "sparse peripheral tracks" the ticket allows where use
  supports no more.
- **The legibility aid** (R-A1) used to scale alpha only, and on an opaque road that moved
  almost nothing (a mean cell change of 0.02 at the crossing, against 0.15). It now also fills
  the core's sod islands and lifts the dirt's lightness by up to 25 %, both multiplied by the
  aid, so the default frame is unchanged. At full aid the mean cell change is 6.20, and dropping
  the aid restores the frame with a residual of 0.00.
- **Cost.** One texture fetch per fragment (the grit), against one before (the rut canvas). The
  draw calls are the same, one per surface (3). The streets layer draws 59,323 triangles over
  6,937 panels, 606 of them refined. The smoke's panel accounting re-derives from
  `drawn_width_m`, the width the module actually draws. The joint stations stay on the
  recorded track, because past it a shoulder may stop at a fill's flank.

## The tones, and how the smoke chose them

The road-legibility gate reads luminance, not hue (R-BUG2/3: median ΔL\* ≥ 1.8 and ≥ 55 %
perceptible per band). Three passes, at desktop part 7:

| tones | walker's eye 2–40 m | from the air 100–250 m |
|---|---|---|
| T-1797's pair (lane 126,112,91) | ΔL\* 7.2, 100 % (road lighter) | 1.3 of 2.2 opaque, 42 % — FAIL |
| a step darker (lane 112,99,80) | 2.1, 50 % — FAIL | 2.1 of 4.6 opaque, 52 % — FAIL |
| dry dust (lane 142,128,104), more cover on light streets | 13.8, 100 % | 9.0 of 9.7 opaque, 94 % |

The prairie reads darker than the road at grazing angles and brighter from above. So a road
near the grass's own lightness passes one station and fails the other, and only a road clearly
lighter than the grass passes both. A dry July street plausibly is that, and the owner's peer
views show one. The light streets' sod islands were reduced in the same pass (bare share 0.55 →
0.68), because a probe that lands on sod reads no road.

All of it is reconstruction, recorded as **L326**.

## Coverage — every opened corridor

28 opened streets. The 51 platted but unopened lines (`opened: false`, track 0) draw nothing,
as before.

| id | 1835 name | traffic | surface | track m | worked m | core m | bare share |
|---|---|---|---|---|---|---|---|
| `south_water` | South Water Street | principal | graded_earth | 10.5 | 19.5 | 10.5 | 1.00 |
| `lake` | Lake Street | principal | graded_earth | 10.5 | 19.5 | 10.5 | 1.00 |
| `randolph` | Randolph Street | ordinary | worn_earth | 7 | 15.6 | 7.8 | 0.90 |
| `washington` | Washington Street | light | light_worn_earth | 5.8 | 10.7 | 5.8 | 0.68 |
| `market` | Market Street | principal | worn_earth | 8 | 19.5 | 9.8 | 1.00 |
| `franklin` | Franklin Street | ordinary | worn_earth | 7 | 15.6 | 7.8 | 0.90 |
| `wells` | Wells Street | ordinary | worn_earth | 7 | 15.6 | 7.8 | 0.90 |
| `lasalle` | La Salle Street | ordinary | worn_earth | 7 | 15.6 | 7.8 | 0.90 |
| `clark` | Clark Street | ordinary | worn_earth | 7 | 15.6 | 7.8 | 0.90 |
| `dearborn` | Dearborn Street | ordinary | worn_earth | 7 | 15.6 | 7.8 | 0.90 |
| `state` | State Street | light | light_worn_earth | 6 | 10.7 | 6.0 | 0.68 |
| `west_water` | West Water Street | light | light_worn_earth | 5.8 | 10.7 | 5.8 | 0.68 |
| `canal` | Canal Street | ordinary | worn_earth | 7 | 15.6 | 7.8 | 0.90 |
| `clinton` | Clinton Street | light | light_worn_earth | 5.8 | 10.7 | 5.8 | 0.68 |
| `kinzie` | Kinzie Street | ordinary | worn_earth | 7 | 15.6 | 7.8 | 0.90 |
| `carroll` | Carroll Street | light | light_worn_earth | 4.5 | 10.7 | 5.4 | 0.68 |
| `fulton` | Fulton Street | light | light_worn_earth | 4.5 | 10.7 | 5.4 | 0.68 |
| `north_water` | North Water Street | light | light_worn_earth | 6 | 10.7 | 6.0 | 0.68 |
| `wolcott` | Wolcott Street | light | light_worn_earth | 5.8 | 10.7 | 5.8 | 0.68 |
| `market_north` | Market Street | light | light_worn_earth | 5.8 | 10.7 | 5.8 | 0.68 |
| `franklin_north` | Franklin Street | light | light_worn_earth | 5.8 | 10.7 | 5.8 | 0.68 |
| `wells_north` | Wells Street | light | light_worn_earth | 5.8 | 10.7 | 5.8 | 0.68 |
| `lasalle_north` | La Salle Street | light | light_worn_earth | 5.8 | 10.7 | 5.8 | 0.68 |
| `clark_north` | Clark Street | light | light_worn_earth | 5.8 | 10.7 | 5.8 | 0.68 |
| `dearborn_north` | Dearborn Street | light | light_worn_earth | 5.8 | 10.7 | 5.8 | 0.68 |
| `michigan_north` | Michigan Street | light | light_worn_earth | 5.8 | 10.7 | 5.8 | 0.68 |
| `fort_road` | The fort road | ordinary | worn_earth | 5.5 | 7.7 | 5.5 | 0.90 |
| `fort_bank_track` | The bank track | light | light_worn_earth | 3.6 | 5.3 | 3.6 | 0.68 |
*Bare share* is `WEAR_INTENSITY`: 1 means bare across the core, and lower values keep sod
between the lanes. Exceptions are inherited, not new. Panels whose centreline is wet are still
dropped, and panels are still clipped at the waterline (R-BUG4), so no roadway is painted over
the river. Sand approaches and the riverbank aprons are T-1771's and T-1772's.

## Review — fixed stands, frozen clock, chrome hidden, `full` detail, SwiftShader

Captured from the published mirror (`site/4d/1835/`) at 1280×800, and at 390×780 for South
Water. The "before" frames are `dev` at 4ca01605 from the same stands. Stands are given in
street-frame terms, as metres along the drawn line, offset and yaw relative to it:

| stand | pose (E, N, yaw) | files |
|---|---|---|
| South Water, walker height, looking east | 380.4, 5.4, 89.5 | `before-`/`after-south_water_walk-desktop.jpg`, `after-south_water_walk-mobile.jpg` |
| South Water from 16 m, pitch −32° | 350.4, 3.2, 89.5 | `before-`/`after-south_water_above-desktop.jpg`, `after-south_water_above-mobile.jpg` |
| Lake Street at walker height, east from Market | 118.0, −108.6, 90.5 | `after-lake_walk-desktop.jpg` |
| Clark Street north (light), looking north | 575.9, 149.1, 0.4 | `before-`/`after-clark_north_walk-desktop.jpg` |
| Randolph, the west approach, looking west | −188.6, −249.9, 270.4 | `after-randolph_west_walk-desktop.jpg` |
| The town from 70 m, pitch −32° | 330, −420, 20 | `before-`/`after-town_above-desktop.jpg` |

Zero pageerrors at every stand.

**Critique, written against the frames.**

- From above, South Water now reads as one worked plane with dozens of wandering wheel lines
  and a ragged grass margin. That is what the peer views show and the old frame did not. At
  walker height the ruts read as darker streaks running with the street, and the grit holds up
  to a metre or two.
- The first pass laid mud at 7–18 m with 0.85 of the muck tone, and from 70 m it read as dark
  blotches. That was cut to 8 m / 2.6 m patches at 0.7 and confined to heavier wear. It still
  reads a little soft, which is the 8 m scale; the T-1797 strip had the same residual.
- Ruts are colour only. A rut has no wall, because the relief is the grit's normal. Rut walls
  and a crowned, drained section are geometry and grading, so they belong to T-1812, as does
  the strip of grass still left between South Water's south shoulder and its plank walk.
- The road is now pale dust in full sun. The gate forced that choice (above), and it is
  consistent with a dry July. A wet-weather state, with the black loam showing through, would
  be a different scene condition, and nothing here models weather.
- The light streets keep fewer sod islands than the first pass drew (Clark North now reads
  mostly bare with grass at its edges), because the legibility gate counts probes on sod as
  road not seen.
- The flora still clears only the recorded track (`blocksGrowth`), so on the shoulders a few
  grass blades stand on bare earth. Read as stragglers, it is acceptable. A sward clearance
  that follows the shader's own coverage is a T-1812 item.
