# 1730 Prairie's stable, its range and its one-storey piece on the alley: the district draft refined onto K12 (T-1932)

`house_1730_prairie_coach_house` keeps its id and moves from the district draft (`prairie_draft`, T-2334) onto the
K12 coach-house kit (`k12_coach_house`), as 1812's (T-2321), 1736's (T-2995), 1620's, 1616's, 1612's, 1626's,
1628's, 1712's, 1700's, 1720's and 1726's (T-1932, [the last of them](../k12-1726-stable-1932/README.md)) did. The
draft rules' `skip` now names census row `s20-1730-r1`, so the draft builder stands no second building in its place,
and the phase is `as_standing_1904` (asset `house_1730_prairie_coach_house__as_standing_1904.glb`; the `__draft_1904`
master and its web derivative are retired). Liberty `L-k12-1730-stable-range-1932`; the draft block liberty
`L-draft-prairie-16-18-west-2334` records the retirement.

This is the tenth building of T-1932's package (the north-west alley, 1600-1736). It is the last brick building on
the alley still standing as the draft's. Only 1630's frame shed is left, plus 1620's image-gate items, which stay as
#1525 left them.

## What the sources say

| source | date | what it draws on this ground |
|---|---|---|
| Sanborn 1911, vol. 3 sheet 20 (`sanborn_1911_chicago_v3_sheet_20`) | 1911 | three **pink (brick)** pieces, **uncrossed**, with no use lettered ([crop](sanborn-1911-sheet-20-building.jpg)): a **two-storey** piece (`2`) on the alley, its north wall on the 1726/1730 lot line, with `12 12` inside that wall and `12 8` inside its south wall; a **one-storey range** (`1`) running on south of it along the alley, as deep, to the north wall of 1736's coach house; a **one-storey piece** (`1`) against the two-storey piece's east wall at its north end, on the lot line. The key's **fire-wall sign with two ticks** at the alley end of the lot-line wall and of the wall between the stable and the range; a **window mark with two dots** on the stable's alley wall; a **window mark with one dot** on the range's; a **solid dot** inside the stable's south-east corner and another inside the range's |
| Robinson's atlas, plate 10 (`robinson_1886_chicago_plate_10`) | 1886 | behind **lot 7**, a **pink (brick)** building **crossed by an X** (the atlas's stable), about 9.6 m deep by 8.5 m along the alley; joined to it behind **lot 8**, an **uncrossed pink** piece the same depth, about 7.6 m along, running up to the crossed building behind lot 9 (1736) ([crop](robinson-1886-lots-7-8.jpg)); nothing on the yard side |
| T-1840 census, row `s20-1730-r1` | (1911 reading) | "2-storey and 1-storey brick pieces with a long 1-storey brick range on the alley" |

**The ruling.** The stable and range stood from before 1886 through 1911. Both maps draw the same run, 16.1 m on the
plate and 18.1 m on the sheet, and divide it about the same way: 8.5 + 7.6 m against 9.8 + 8.3 m. (At its 0.346 m a
pixel, the plate's edges take in its own border lines.) So both are built for 1904, as the census rules, and the
two-storey piece is the stable the plate crosses. Function `stable` is INFERRED from the plate's X. The one-storey
piece on the yard side is first seen in 1911, because the plate's stable has a straight east wall, so it may
postdate 1904. The census carries the whole building into 1904, so the piece is built with the rest and its use is
left unread.

## The outlines, read off sheet 20

Median darkness profiles on the committed raster
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_20.jpg`). Each peak is
refined by a parabola through its three highest samples.

| line | where profiled | peak |
|---|---|---|
| alley wall, stable | rows 5570-5640 / 5660-5740 | column 2224.90 / 2225.57 |
| alley wall, range | rows 5760-5830 / 5850-5900 | column 2225.39 / 2225.94 |
| east (yard) wall, stable | rows 5620-5730 | column 2379.35 |
| east (yard) wall, range | rows 5760-5900 | column 2380.23 |
| the stable's north wall (1726/1730 lot line) | columns 2240-2370 | row 5554.37 (1726's record: 5554.39; east of the building 5554.80) |
| the stable's south wall (where the range meets it) | columns 2240-2370 | row 5746.53 |
| the range's south end (1736's north wall) | columns 2240-2370 | row 5910.49 (1736's record: 5910.5) |
| the one-storey piece's east wall | rows 5560-5610 | column 2455.47 (1726's east wall: 2454.62) |
| the one-storey piece's south wall | columns 2390-2450 | row 5615.80 |
| the 1730 house's rear wall | rows 5630-5700 | column 2676.97 |

At the sheet's 0.050779 m a pixel:

- **Stable:** 7.826 m deep by 9.758 m along the alley.
- **Range:** 8.326 m along. Its east wall is 0.88 px (0.04 m) off the stable's, so it is built as deep as the stable.
- **One-storey piece:** 3.865 m deep by 3.119 m from the lot line.

The middle of the stable's alley wall, pixel (2225.24, 5650.45), carried through the sheet's similarity fit, is
local E 1336.157, N -3176.176 (UTM 448408.857, 4634219.624).

The window marks:

- **Stable:** the ticks cross outside the wall at rows 5649 and 5659, with its two dots inside at 5667 and 5677.
  Built centred at row 5662: **5.47 m** from the north wall line and 4.29 m from the south.
- **Range:** the stroke crosses at about row 5834, with its dot at 5841: **4.44 m** from the stable's south wall line.

Robinson's lots 7-8, read by a pink-density ((red - green)) profile on the committed plate raster:

- The two buildings' half-height edges are at columns 348.2-375.9 (lot 7) and 348.6-375.6 (lot 8).
- The north end's edge is at row 1620.5.
- The darkness peaks of the dividing lines are at row 1645.0 (lots 7/8) and row 1667.0 (lot 8 against lot 9's
  crossed building).

## What K12 builds

- **Stable, as drawn.** The party wall is at the north end, on the lot line, rising 0.45 m above the roof. The open
  gable is at the south end; the range covers it to 3.45 m, and above that it is blank.
- **Alley wall** (s from the party wall's inner face):
  - the carriage bay (3.0 m clear) toward the north end, with the loft hatch over it;
  - the stable's mark, built as a stable sash with a loft sash over it, centred where it stands (s 5.135);
  - a man door with a loft sash over it toward the south end.
- **Yard wall,** south of the one-storey piece: a door between two stable sash, with loft sash over them.
- **Range** (the kit's range fitting): 8.33 m long, flat-roofed at 3.2 m. The mark is built as a sash where it
  stands (s 4.44), with a door at the middle of its yard wall.
- **One-storey piece** (the kit's lean-to fitting): a single-pitch roof at the kit's 20 degrees, 3.9 m high where it
  dies into the yard wall and 2.49 m at its front, with the kit's stable (Dutch) door in its front.
- **Roof:** one gable at 30 degrees over the 7.83 m span, ridge along the alley.
- **Workyard:** paved from the yard door to the 1730 house's rear wall line, 15.11 m east. The walk runs 1.55 m south
  of the stable's middle, where the door is, clear of the house's frame back porch.
- **Not built:** the two solid dots (no stack is drawn), and the fire-wall sign at the stable's south end (the kit has
  one party wall, and the range stands against the open gable, as 1720's does).

**The shared wall.** The sheet draws one wall on the 1726/1730 line. 1726's record already stands its party wall
there, inside its own outline, so this record stands a second one inside its own. That makes two 13-inch walls back
to back where the sheet draws one line. Each building's outside is the sheet's, and only the shared wall is doubled,
out of sight between the two buildings (in the liberty). 1730's party wall, gable and roof are all lower than
1726's, so from the alley 1726's coped wall reads above 1730's.

### The kit learns two things (additive)

`generators/archetypes/k12_coach_house.py`:

1. **A range as deep as the coach house.** Its yard wall's end stands on the yard wall's end, as its alley wall's
   does on the alley wall's, and its flat roof is flush with both faces. A range shallower than that is built as
   before.
2. **A lean-to on the lot line against the party wall** (`x0` at the party wall's outer face):
   - its west wall stops at the party wall's return, its end standing on the return's end face;
   - its roof steps round the return: one piece over the return's thickness, starting where the return ends, and
     beyond it the roof dies into the yard wall;
   - no verge passes the lot line.

   A lean-to between the lot line and the party wall's inner face is refused, because it would run into the wall.
   The workyard's apron now starts clear of a lean-to rather than under it.

The kit specimen and the other twelve K12 coach houses rebuild byte-identical. Their manifest entries are
re-stamped only because the kit's code and data are their inputs. `tools/check_coach_house_kit.py`:

- `--check`: 13 variants, every piece seated or rooted, no doubled face, every elevation closed, every opening cut
  through.
- `--self-test`: 0 failures, with two new cases that are refused as they should be: the lean-to's roof 5 mm off the
  party wall's return, and the full-depth range 5 mm off the yard wall.

The master is 117.3 KB and the web derivative 30.2 KB: 1,532 triangles, where the draft's blocks were 1,100.

`lay_prairie_1904_street_furniture.py --check`, run with the baked model tracked: every pole, crossarm and wire of
the alley clears the building, and no pole moves. Run before the GLB was tracked, the tool walls it to 15 m and
reports the wire from pole #06 to #07 running through it; that reading is not the building's.

## In the app

`QA_TARGET=1730 node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at four stands at 1280x800 full and
390x780 light: `browser-validation-after.json` and `after-<viewport>-<stand>.jpg` in this folder. The stands are:

- down the alley from the north, past 1726's building;
- up the alley from the south, past 1736's;
- the yard face from 1730's back yard;
- the air.

Both viewports had 0 page errors and 0 failed requests. All four records were placed (the building, the 1730 house,
and 1726's and 1736's coach houses), and every stand was inside its budget.

| viewport | load to ready | JS heap | stand | draw calls | triangles | in budget |
|---|---|---|---|---|---|---|
| desktop, full | 39.8 s | 84.0 MB | alley from the north | 6,938 | 4.38 M | yes |
| | | | alley from the south | 3,171 | 2.70 M | yes |
| | | | yard face | 3,842 | 1.10 M | yes |
| | | | air | 2,659 | 2.58 M | yes |
| mobile, light | 28.0 s | 110.7 MB | alley from the north | 4,397 | 0.85 M | yes |
| | | | alley from the south | 2,118 | 0.58 M | yes |
| | | | yard face | 1,008 | 0.23 M | yes |
| | | | air | 2,241 | 0.58 M | yes |

Load times come from this runner's software GL, shared with four other runs, and are relative only. The building
adds 432 triangles to what the draft drew.

**Seen, not fixed here.** The tall pink shafts in the alley and air views were already in 1726's renders, on the far
side of the alley; they are not this building's. The renderer's bedding of a K12 stable at its workyard walk's far
end (recorded on [1700's](../k12-1700-stable-1932/README.md)) applies here too.
