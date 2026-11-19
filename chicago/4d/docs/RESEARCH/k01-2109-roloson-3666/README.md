# T-3666 — 2109 Prairie, the Roloson house, on K01 from the Armour photograph

Piece 2 of T-1924 (the S13 package of the T-1837 programme). The district draft (T-2352) is refined in
place, under its own id (`roloson_house_2109_prairie`), onto the K01 frontage assembly
(`generators/k01_emit.py`); liberty `L-k01-2109-roloson-3666`. The coach house
(`roloson_house_2109_prairie_coach_house`) is the R-series' and is untouched; 2101 next door is T-3665's.

## What was read

Sheet 35 of the 1911 Sanborn (`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`),
read at full size, 0.186 m a pixel, north up and Prairie Avenue on the left (the street line at raster column 878,
the parcel's north line at row 1121, its south line at row 1203):

| reading | raster (column / row) | in the record |
|---|---|---|
| veranda's front edge (yellow, frame) | column 908 | 5.6 m from the street line; 1.8 m deep |
| stone front (a blue band about 6 px deep across the whole front) | column 918 | 7.44 m from the street line, K01's street front |
| front block's north wall | row 1128 | 1.30 m inside the parcel's north line, K01 v 0 |
| front block's south wall | row 1169.5 | 7.72 m wide |
| veranda's south edge | row 1184 | 2.7 m down the south side |
| rear block steps out south | column 960, row 1182 | 15.25 m from the street line; K01's main body 7.81 m deep |
| rear block's rear wall | column 1013 | 25.1 m from the street line |
| frame back porch (yellow, north-east corner) | columns 988-1020, rows 1123-1141 | rear wing `back_porch`, one storey |

The draft's own trace fit (`s35fp-2109-b1`) had put a 3.75 m deep stone piece 4 m wide on the front; at full
size the blue is a uniform band across the front, no projection, and the photograph agrees: its "mansard tower" is
the front block's own mansard, seen at its south end.

The one picture of the house, the Armour photograph (`data/sources/chicagology_2115_armour_photo.json`, committed at
`data/sources/assets/roloson_2109_photo_t3666/`), catches 2109 at its left edge. Read off it:

- two storeys of wall under a bracketed cornice whose paired consoles turn the south corner, a frieze with a sunk
  panel and a lozenge under it, a carved pilaster strip on the corner;
- the slated mansard over them, a round-headed dormer in a carved, scrolled surround over the south bay, a cornice
  round the deck and a tall stack over it;
- the south bay's round-headed light in each storey, the upper one under a moulded hood with a carved key;
- the veranda: round columns on panelled pedestals, paired at the south-west corner, a turned balustrade between them,
  a deep plain entablature under a flat roof, its floor about 1.7 m up on open square piers; its front run passes the
  house's corner and returns down the south side;
- beyond the veranda, the cornice of the rear block where it steps out south.

## The camera

Solved on 2109 alone (`data/reference_views/roloson_house_2109_prairie/chicagology_armour_photo.json`, its `solve`
gives the points and residuals): eye in the roadway about 17 m west of the street line, level with the front block's
south wall, yaw -68 degrees in the record's frame, focal 2105 px. The Armour house's district draft could not hold it:
its footprint does not stand where the print draws the Armour front's corners.

## Image gate

T-1924's gate names 2109. Its view is recorded `differs`, with the veranda's front run, its open piers, the rear
block's step and the dormer's carved surround open
(`data/reference_views/roloson_house_2109_prairie/chicagology_armour_photo.match.json`). T-3665 (2101) is still live
and the gate stays on T-1924.
