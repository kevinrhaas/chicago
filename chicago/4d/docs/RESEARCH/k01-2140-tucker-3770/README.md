# T-3770 — 2140 Prairie on K01: the Tucker/Smith corner mansion, banded red brick under a mansard, three towers

Piece 1 of T-1928 (the S17A package of the T-1837 programme; piece 2, T-3771, is the porch, its stair, the glass
room, the gabled dormers and the stacks' pots; piece 3, T-3772, the rear range's fittings and the before/after
views and costs; T-1929 finishes the architecture and carries the image gate). The district draft (T-2351) is
refined in place, under its own id (`tucker_smith_house_2140_prairie`), onto the K01 frontage assembly
(`generators/k01_emit.py`), on the pattern of 2130 next door (T-3729); liberty `L-k01-2140-tucker-3770`. The yard
and alley buildings (`…_alley_building`, `…_coach_house`) are T-1937's and are untouched.

## What was read

Sheet 35 of the 1911 Sanborn (`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`),
read at full size by classifying pixels along rows and columns (0.1858 m a pixel), carried into the record's frame
through the committed trace's fit (`data/traces/prairie_1904_footprints_s35.json`). Plan frame: u from the main rear
wall toward Prairie (east), v from the 22nd Street wall (+v north), as 2130's. K01's 'south' wall is the 22nd Street
flank (its s from the rear), its 'north' wall the flank toward 2130 (its s from the front), and `front_bays` count
from the 22nd Street corner.

| reading | raster (column / row) | plan (u, v) |
|---|---|---|
| main body's rear wall | column 672.5 | u 0 |
| Prairie front | column 744.5 | u 13.38 |
| 22nd Street wall / north wall ('3S.B.') | rows 1659 / 1559 | v 0 / 18.59 (the draft's fit: 8.5 by 16.25 m) |
| Prairie street line | column 770 | 4.8 m before the front |
| dashed line inside the whole outline | about 1 m inside every wall | the key's mansard roof, all round |
| circle at the south-east corner | centre column 741, row 1667, radius about 12.5 px | a round tower about 2.3 m in radius, centre 0.65 m behind the front's plane and 1.3 m out of the 22nd Street wall |
| canted projection on the 22nd Street wall | columns 680-698, to row about 1676 | u 1.4-4.7, about 3.2 m out: the polygonal tower |
| projection on the Prairie front | rows 1574-1599, to column 751 | v 11.15-15.8, about 1.2 m proud: the square tower |
| yellow 'GLASS 1' before the front | rows 1622-1634, columns 744-768 | v 4.65-6.9: the glass room before the door's bay (T-3771) |
| '3SB' rear range | columns 644-672.5, rows 1586-1622 | u -5.3-0, v 6.88-13.57 |
| rear wall's south half | column 676, rows 1640-1659 | about 0.7 m further in: **not built** (one rectangle) |
| lot lines | rows about 1534 / 1700 | v 23.2 / -7.6 |

The two Chicagology photographs (`data/sources/chicagology_2140_photo_a.json`, `…_photo_b.json`, forms only,
`check_required`), both after 1890, the first from the south-east corner of the crossing, the second from the Prairie
roadway south-east of the house. Read off them (the second at about 86 px a metre on the round tower's drum, the
nearest wall; proportions, not a solved camera):

- deep red brick on every street wall and tower, banded in pale stone at the second floor (about 5.9-6.25 m) and at
  the chamber lights' springing (about 8.65 m), on a pale stone basement to a water table about 1.8 m up;
- the principal lights about 0.95 by 3.0-3.2 m on sills about 2.0 m over the yard, the chamber lights about 2.4 m,
  every light under a pale stone hood; the cornice's bed at about 9.8 m and its corona about 10.5 m;
- a deep stone cornice on close blocks round every wall and tower, a slated mansard rising about 3.8 m at about 75
  degrees, its gabled dormers over the light columns, iron cresting round its deck;
- the round tower's drum under the main cornice, one tall light a storey on the corner's diagonal; the polygonal
  tower's third stage over the cornice, lit in its gabled faces; the square tower's paired lights;
- one tall stack with clustered pots beside the round tower over the 22nd Street flank.

## The one roof state

The register asks for ONE declared 1904 state of the towers. Two pictures show them flat-topped inside iron
cresting — the 1898 plate (the Art Institute's quarter-century volume, its photograph probably older) and the second
Chicagology photograph (after 1890) — and two show the later spires: the first Chicagology photograph (after 1890,
the porch replaced by an arched glazed canopy, as the 1911 sheet's glass room may be) and the Tribune's 1928
photograph. None is dated before July 1904. The district draft declared the flat-topped state for that reason
(`L-draft-prairie-20-22-west-2351`, "a dated view showing spires by July 1904 replaces it"), and this refine keeps
the declaration: no such view was found. The first photograph's canopy suggests the spires and the glass room came
together, between the second photograph and 1911; that is a lead for T-1929, not a date.

## What is built

A `k01_frontage` record (`data/structures/tucker_smith_house_2140_prairie.json`, phase `as_mapped_1904`): two
storeys of K03 pressed red brick over a 1.65 m Lemont-limestone basement, stone belts at 5.9-6.25 and 8.65-8.8 m,
the moulded stone cornice on blocks round every wall at 10.45 m, a K05 convex mansard 3.8 m at 75 degrees with two
gabled dormers (over the Prairie front's light column north of the door and the 22nd Street flank's) and a 0.5 m cresting; four bays
on the Prairie front (the door in the second), one on 22nd Street, three on the north flank, two at the rear; two
stacks on the deck; the '3SB' rear range on K01's rear wing.

The towers, on K08:

- **round tower** — across the Prairie/22nd Street corner (`across_corner`), a 24-sided ring 2.3 m in radius,
  its drum's cornice the main cornice (`cap_at_eave`), its slated cap 4.2 m to a crested deck;
- **polygonal tower** — K08's octagon on the 22nd Street wall, 2.1 m in radius, 1.26 m out (its face about 3.2 m
  out, as the sheet), three stages, the third over the cornice, under a short slated cap and a crested deck;
- **square tower** — a K08 projection 4.65 m wide and 1.2 m proud with paired lights in both storeys, under a K01
  mansard crown 0.4 m over the main curb with its own cresting.

### The kit change

K01 set a tower across its wall's corner only as a square turned 45 degrees (T-3176, 1827's). `_bays` now also takes
a ROUND tower across a corner, drawn as K08's polygon of 16 or 24 sides turned half a side (`ACROSS_ROUND_SIDES`),
its centre up to its radius less 0.3 m out of the face; and such a tower may carry its cap at the eave
(`cap_at_eave`) under its many-sided hip, the drum then closing nothing on the corner's planes. The square case and
every other record build the same bytes (`python3 generators/k01_emit.py --check`).

## Not built, and whose it is

The columned porch, its stair and the glass room; the dormers' crocketed gables and the towers' gabled faces; the
stacks' pots (T-3771). The rear range's lights and fittings; the before/after views and the scene's costs (T-3772).
The lights' round-arched heads, the carved hoods and the corbelled cornices of the towers; the cameras and the
photo-match (T-1929). The long iron fence and gate piers on the corner (T-1945).
