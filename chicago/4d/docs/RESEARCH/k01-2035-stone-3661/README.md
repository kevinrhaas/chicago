# T-3661 — 2035 Prairie on K01: the 21st Street corner of the 1869 limestone row

Piece 3 of T-1918 (the S09 package of the T-1837 programme). The district draft (T-2352) is refined in
place, under its own id (`stone_house_2035_prairie`), onto the K01 frontage assembly
(`generators/k01_emit.py`); liberty `L-k01-2035-stone-3661`. The detached rear building
(`stone_house_2035_prairie_rear_building`, census `s35-2035-rear`) is T-1938's and is untouched.

## What was read

Sheet 35 of the 1911 Sanborn (`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`),
read at full size and carried into the lot frame through the committed trace's fit
(`data/traces/prairie_1904_footprints_s35.json`, 0.186 m a pixel), with the T-1842 census row s35-2035-front
('3B brick dwelling with a stone front and a full-height bay (D), the 21st Street corner of the row').

| reading | raster (column / row) | lot frame (u from the rear lot line, v from its middle, + south) |
|---|---|---|
| main body's front (pink edge) | column 920.5 | u 46.6; built on 2033's line, u 46.5 |
| main body's rear, where the rear range begins | column 1006.5 | u 30.6 |
| north party line (2033's south wall) | row 847 | v -3.88 |
| 21st Street wall | row 887 | v 3.67-3.70 (built 7.6 m from the party line) |
| the stone bay's curved bulge | rows 862-884, out to column 909-911 | v -0.61..3.1, out about 1.1 m past the stone |
| attached rear range ('BRICK 1ST' lettered across it) | columns 1006.5-1060 | u 20.7..30.6, v -3.48..3.77 |
| one-storey brick strip on the range's north side, not built | columns 1015-1041, rows 847-854 | |
| two small frame (yellow) projections on the 21st Street flank, not built | columns 982-1001 and 1010-1029 | |

The Chicago Tribune's strip of 9 January 1898 (`data/sources/chicago_tribune_1898_01_09_residence_district.json`,
public domain), its fourth panel, numbered 2035, committed unscaled at
`data/sources/assets/stone_2035_pictures_t3661/tribune_1898_2035_panel.jpg` and solved approximately in
`data/reference_views/stone_house_2035_prairie/tribune_1898_front.json`: the round-arched door with a fanlight at
the north end of the front; a flat-roofed portico with a deep plain entablature on slender columns; a deck at the
principal floor beside the stoop, under the same roof, railed with a band of scrolls; the stoop's swept cheeks; a
tall round-headed light over the porch roof; a low railing on a curb along the walk.

## The design

The row shares one cornice line (census ruling r35-2031-2035-row), so the floor (1.7 m), storeys (3.8, 3.8,
4.15 m), lights and bracketed cornice are 2033's as T-3659 read them off its 1946 photograph. What is 2035's own:
the door at the north end under a stone portico on two columns, its deck to the bay's north foot behind a pierced
parapet, swept cheeks with newels; the bay bowed where 2033's is canted (the sheet draws a curve); round heads with
keys over the door where 2033's are segmental; the 21st Street flank windowed four lights a storey (the register's
'corner return'; its fenestration reconstructed); two stacks on the north party wall; the rear range on K01's rear
wings, two storeys in brick.

## Not built

- The porch's run across the whole front, before the bay (K01 lays a door hood beside a bay, not before it).
- A cornice returned along the 21st Street flank: K01's flat roof is corniced on the street front only, and the
  flank stands under a coped parapet.
- The rear range's frame upper storey (a K01 wing takes one fabric), the brick strip beside it (no wing beside a
  wing) and the flank's two small frame projections.

## Image gate

T-1918's gate names 2031, 2033 and 2035. 2035's view (the Tribune panel) is recorded `differs`, with the porch's
extent, the bay, the portico's railed top and the deck's railing open
(`data/reference_views/stone_house_2035_prairie/tribune_1898_front.match.json`). T-3660 (2031) is still live and so
is the last piece, and carries the gate. The undated Chicagology engraving of the 2031-2035 walk (rights unknown,
link only) is not used here.

## Checks

Oblique renders from the 21st Street corner and from the rear yard were looked at during the build (the flank's
four lights a storey under its parapet, the rear range's flat roof under the main rear wall's lights).
`check_bay_kit.py --check` holds the bow to the K08 rules (12876 triangles full, 3739 light).
