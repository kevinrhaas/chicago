# T-3781 — 217 East Twentieth Street on K01: the red brick corner rowhouse and its copper oriel

Piece 1 of T-1939 (the X01 package of the T-1837 programme). Piece 2, T-3782, refines 213 and 215 beside it; piece 3,
T-3783, solves the photographs' cameras on all three houses, works the photo-match down and carries the parent's
image gate. The district draft (T-2982) is refined in place, under its own id (`house_217_e20th`), onto the K01
frontage assembly (`generators/k01_emit.py`); liberty `L-k01-217-e20th-3781`. It is the first K01 house on a cross
street: the plan's u axis runs north to East Twentieth Street, v west from the east wall, so K01's `south` wall is
the house's east flank on the 20 ft passage and its `north` wall the west one, toward 215.

## What was read

Sheet 35 of the 1911 Sanborn (`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`),
read at full size by classifying pixels along rows and columns (0.1858 m a pixel), carried into the record's frame
through the committed fit of the trace (`data/traces/prairie_1904_footprints_s35x.json`) and the draft's own corner.

| reading | raster (column / row) | plan (u, v) |
|---|---|---|
| front, on the street line | row 271.5 | u 14.6 |
| main body's rear (the outline narrows to the range) | row 350 | u 0 |
| east wall (on the 20 ft passage) / west wall (lot line with 215) | columns 437.5 / 399.5 | v 0 / 7.06 |
| the front's east end bowed out ('3½' over the front) | rows 267-271, columns 419-437 | about 0.8 m out over 3.4 m |
| yellow (frame) strip across the plan | rows 305-310 | about 6.4 m behind the front: **not built** |
| '3' rear range, its south-west corner cut | rows 350-377, columns 409-437.5 | u -5.0-0, v 0-5.3 (built square) |

The draft's fit had read a 6.75 by 6.5 m front block and an 11.5 m range; the house's rear corner moves 7.9 m back
and 0.31 m east of the draft's, and its front stays on the street line.

Three photographs of the surviving house from Jyoti Srivastava's 2009 blog post (`jyoti_blog_2009_cullerton_rowhouses`,
a new source record; forms only, `check_required`; the image library's `a19-jyoti-cullerton-106`, `-220` and `-223`):

- 220 looks west along the street from the passage's side: 217's east flank broadside, the oriel at its north
  corner, 215 set back beyond it. So the oriel stands at the street front's **east** corner, where the sheet bows
  the front out, over the two round-headed lights;
- 223, square to the front: the oriel's rounded copper underside over two round-headed lights in red brick on a
  smooth sandstone base course, and the door west of them in a carved stone surround;
- 106, from the north-east: the copper oriel's two tiers of bent lights under a copper cornice, and a steep gable
  with a finial over the east flank.

## Built

A K03 red pressed-brick body (the palette's `pressed_red`, laid all round) on a one-course sandstone base, three
storeys under a slated hip; a K08 round oriel **in copper** on the second floor (3.2 m chord, 0.8 m rise, a round
apron for its underside, three lights a tier); the two round-headed lights under it (`street_front_round_heads`);
the K07 panelled door on a three-riser stoop inside the 1.6 m strip between the front and the walk; the rear range.

**The kit change.** K08 bays took four fabrics (stone, brick, the front's stone, painted timber); a copper-sheathed
oriel had none. `copper` is added to `BAY_FABRICS`, and `k01_frontage.py` lays such a bay's walls in the `bay_copper`
material its roofs already used, its plinth, bands, corbels, apron, sills and heads with it. Every K01, K12, K13
and K16 asset was re-emitted on the changed code; every one is byte-identical, only its input hash moved.

## Not built (recorded in the liberty)

- the steep gable with a finial over the east flank and its small turreted dormer (K01 stands a shaped gable on
  the street front only);
- the oriel turning the corner onto the east flank (K01 keeps 0.3 m of wall between a bay and its corner), and its
  top at the wall head under a copper cornice (an oriel's wall top stays a metre under the eave; carrying a bowed
  oriel through it is not supported);
- the east flank's large round-headed ground light, the door's carved surround, the frame strip, the range's cut corner;
- the red of the stone (K02's brown sandstone stands in).

## Renders

Built and looked at from the north-west, the north-east and square to the front's ground storey (three.js,
the committed GLB): the copper oriel and the round-headed lights read as photograph 223 shows them.
