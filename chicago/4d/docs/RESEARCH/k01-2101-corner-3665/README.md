# T-3665 — 2101 Prairie on K01: the brick corner house on 21st Street

Piece 1 of T-1924 (the S13 package of the T-1837 programme; piece 2, T-3666, is 2109 Prairie and carries
the parent's image gate). The district draft (T-2352) is refined in place, under its own id
(`house_2101_prairie`), onto the K01 frontage assembly (`generators/k01_emit.py`), on the pattern of
2001 Prairie (T-3347), the other east-side corner house of two and a half storeys; liberty
`L-k01-2101-corner-3665`. The alley building (`house_2101_prairie_coach_house`, census `s35-2101-rear`)
is T-1938's and is untouched.

## What was read

Sheet 35 of the 1911 Sanborn (`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`),
read at full size by dark-pixel profiles along rows and columns, and carried into the lot frame through the committed
trace's fit (`data/traces/prairie_1904_footprints_s35.json`, 0.1858 m a pixel), with the T-1842 census rows
s35-2101-front ('2½B brick dwelling (D) on the 21st Street corner, with one-storey frame porches') and s35-2101-wing
('a long rear range reaching back toward the alley').

| reading | raster (column / row) | plan frame (u from the rear wall toward the street, v from the 21st Street wall, + south) |
|---|---|---|
| main body's front | column 916 | u 21.93 |
| main body's rear wall | column 1034 | u 0 |
| 21st Street wall | row 1000.5 | v 0 |
| south wall | row 1060.5 | v 11.15 |
| 21st Street lot line | row 995 | v -0.97 |
| line with 2109 | row 1120 | v 22.21 |
| front lot line | column 877 | u 29.18 (a 7.25 m front yard) |
| front's north end set back, a one-storey frame porch in the recess | column 924, rows 1000.5-1018 | u 20.44, v 0-3.25: not built |
| open one-storey frame porch along the front and round the south-west corner (dashed) | columns 908-933, rows 1018-1075 | not built |
| two canted one-storey frame bays on the 21st Street flank, to the street line | columns 931.7-955 and 968-992.5 | u 14.7-19.0 and 7.7-12.3, 0.95 m out |
| two-storey frame projection ('2') on the south flank | columns 941-965, rows 1060-1067.5 | u 12.6-17.1, 1.3 m out (built 1.2 m, K08's limit) |
| attached rear range (pink) | columns 1034-1059.5, rows 1032-1078.5 | u -4.65-0, v 5.85-14.5 (3.35 m past the south wall) |
| small one-storey frame piece on the range's back | columns 1059.5-1065 | not built |

The draft's rectangle fit drew the main body 20.5 by 9.75 m; the walls stand 21.93 by 11.15 m on the raster.

## The design (all reconstructed; no picture of 2101 is known)

2001's floors and storeys (a 1.7 m principal floor, 4.0 and 3.6 m storeys) and its bracketed timber cornice under a
hip, here slated in Vermont slate at 45 degrees with one street dormer for the sheet's half storey; a pressed red
front with stone lintels and cornice hoods on the principal storey, returned along the 21st Street flank, salmon
common brick on the south flank and rear; four bays on the front, the door at the 21st Street end where the sheet
sets the front back for its entrance porch, on a stone stoop; the canted frame bays and the frame projection painted,
each with a light a storey; two stacks on the hip's south slope; the rear range two storeys under a flat tin deck.

## Not built

- Both frame porches: the one in the recess at the front's north end and the open one along the front and round the
  south-west corner. K01 lays the main block as a rectangle and lays no frame porch on a street front, so the front
  stands in its main line across the whole width.
- The small frame piece on the rear range's back.

## Checks

`node tools/photo_match.mjs` with throwaway review cameras (no picture to match, so nothing was committed under
`data/reference_views/`): the 21st Street corner (`after-nw.jpg`), the south-west oblique (`after-sw.jpg`) and the
rear from the 21st Street alley corner (`after-ne_rear.jpg`). The first look found the two stacks rising the whole
south slope from the eave; they were moved 2 m off the ridge line.
