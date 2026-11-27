# T-3782 — 213 and 215 East Twentieth Street on K01: 215's round-headed front behind its yard, 213's four-storey red front under its cornice

Piece 2 of T-1939 (the X01 package of the T-1837 programme). Piece 1, T-3781, refined 217 beside them; piece 3,
T-3783, solves the photographs' cameras on all three houses, works the photo-match down and carries the parent's
image gate. The district drafts (T-2982) are refined in place, under their own ids (`house_213_e20th`,
`house_215_e20th`), onto the K01 frontage assembly (`generators/k01_emit.py`); liberty `L-k01-213-215-e20th-3782`.
Both use 217's frame: u runs north to East Twentieth Street, v west from the east wall, so K01's `south` wall is a
house's east flank and its `north` wall its west one; both take 217's rotation (-90.599 degrees) and are set on
217's own corner through the sheet's fit, so the row's party walls are single lines.

## What was read

Sheet 35 of the 1911 Sanborn (`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`),
read at full size by classifying pixels along rows and columns (0.1858 m a pixel).

| reading | raster (column / row) | plan |
|---|---|---|
| street line (213's and 217's fronts) | row 271.5 | |
| 215's front, a solid line under a dashed one at row 287 | row 289 | 215 u 11.43 |
| 215's rear, in line with 217's | row 350.5 | 215 u 0 |
| party wall 215/217 | column 399.5 | 215 v 0 |
| party wall 213/215 | column 361 | 215 v 7.15, 213 v 0 |
| 213's west wall | column 326 | 213 v 6.5 |
| 213's east wall steps in | row 357 | 213 u 0 |
| 213's rear range: east wall / rear | column 358.5 / row 397 | 213 u -7.43..0, v 0.46..6.5 |
| a rounded bulge on 213's east wall, about 3 px out | rows 343-358, columns 361-365 | not built |

215's front stands 17.5 px (3.25 m) behind the street line: the census's "set back behind a front yard". 213's
storey figure is illegible at this copy's resolution (the census read "3 or 4"); 215's '3' is clear.

Four 2009 photographs of the surviving houses from Jyoti Srivastava's blog post (`jyoti_blog_2009_cullerton_rowhouses`,
forms only, `check_required`; the image library's `a19-jyoti-cullerton-220`, `-222`, `-224` and `-225`):

- **224**, square to 215's front: red pressed brick; the ground storey's two round-headed lights and the door in a
  deep round-arched opening at the west bay, under plain stone heads with level imposts; the second storey's three
  square-headed lights on stone sills under flat stone lintels, a light stone course under them; a tall iron fence
  and gate closing the yard (2009's). Read at the front's own 7.15 m across the frame (about 76 px a metre at the
  print's double size): the bays' axes 1.15, 3.6 and 6.0 m from the east corner, the lights about 0.95 by 2.3 m,
  the door about 1.4 m wide and 2.9 m to its crown, the ground storey about 3.4 m.
- **222**, 213's ground storey: a panelled door with a transom light a step over the walk, between moulded
  pilasters, under a broad hood with a low pediment on carved consoles; a light each side in a moulded frame under
  a cornice, its sill about 1.4 m over the step. Read at the door's 1.2 m (about 124 px a metre): the west light
  1.05 m from the west corner, the door 2.8 m, the east light 5.05 m.
- **225**, 213 from across the street to the north-east: four tiers of lights (the ground storey hidden by a tree),
  the third round-headed, a deep bracketed cornice over a frieze crowning the front and returning along the east
  flank; the east flank buff where it stands over and before 215, two lights a storey near the front.
- **220**, looking west past 217: 215 set back, 213's buff east flank and red front beyond it, the flank's
  ground-storey lights in the strip before 215's front.

## Built

**215:** a K03 red pressed-brick front, three storeys of 3.4, 3.4 and 3.0 m on a 0.9 m principal floor; the ground
storey's two round-headed lights and the K07 deep-arched double door (`street_front_round_heads` with `door`), the
upper storeys' flat stone lintels; a K10 bracketed cornice over a flat tin deck; no lights in either party wall, two
in the rear; the kit's spear railing on a curb at the walk's inner edge with a walk gate, and a flagged walk across
the 4.75 m front yard to the stoop.

**213:** a K03 red pressed-brick front over buff common flanks, four storeys of 3.8, 3.5, 3.3 and 3.1 m at the
street; the ground storey's lights under the kit's corniced lintel and the door between them under the pedimented
hood on consoles; the third storey's lights round-headed; a K10 bracketed cornice on a frieze over a flat deck; two
bays of lights in the east flank's strip before 215's front, three on the west flank; the rear range on K01's rear
wing, four storeys under a flat deck.

## Not built (recorded in the liberty)

- 213's ground-storey pilasters, the moulded frames of its lights and the carving of the hood's consoles;
- 213's cornice returned along the east flank, and the fourth storey's flank lights over 215's roof (K01 cuts a
  flank's bays through every storey);
- the rounded bulge on 213's east wall behind 215's rear corner;
- 215's dashed line over its front on the sheet, unread.

## Renders

Built and looked at with 217 beside them (three.js, the committed GLBs) from across the street square to the row,
from the north-east as photograph 225 stands, square to 215's ground storey as photograph 224 stands, and from the
air over the rear: 215's round-headed lights and arched door, 213's red front, buff flank, round-headed third storey
and bracketed cornice read as the photographs show them.
