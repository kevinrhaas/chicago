# 1700-1706 Prairie's stable on the alley: the district draft refined onto K12 (T-1932)

`glessner_lee_house_1700_prairie_coach_house` keeps its id and moves from the district draft (`prairie_draft`,
T-2334) onto the K12 coach-house kit (`k12_coach_house`), as 1812's (T-2321), 1736's (T-2995), 1620's, 1616's,
1612's, 1626's, 1628's and 1712's (T-1932, [the last of them](../k12-1712-stable-1932/README.md)) did. The draft
rules' `skip` now names census row `s20-1700-r1`, so the draft builder stands no second building in its place, and
its phase is `as_standing_1904` (asset `glessner_lee_house_1700_prairie_coach_house__as_standing_1904.glb`; the
`__draft_1904` master and its web derivative are retired). Liberty `L-k12-1700-stable-1932`; the draft block
liberty `L-draft-prairie-16-18-west-2334` records the retirement.

This is the seventh building of T-1932's package (the north-west alley, 1600-1736). The rest of the alley (1630,
1720, 1726, 1730) stays the draft's: 1630's is a one-storey frame shed, 1720's a stable joined by a one-storey range
to the building behind 1726, and 1730's a two-storey and one-storey group with a long range on the alley, none of
them the plain two-storey brick rectangle the kit builds as it stands. 1700's is that rectangle, the longest on the
alley, and the only rear building on the one lot (`prairie_1700`) the 1700 and 1706 townhouses share.

## What the sources say

| source | date | what it draws on this ground |
|---|---|---|
| Sanborn 1911, vol. 3 sheet 20 (`sanborn_1911_chicago_v3_sheet_20`) | 1911 | one **pink (brick)** building **crossed by one X** (the key's stable), lettered **2** (storeys), with `12 8` inside its north wall and `12` alone inside its south wall ([crop](sanborn-1911-sheet-20-stable.jpg)); 10.42 m deep from the alley by 19.37 m along it; its north wall on the lot line, which the sheet runs on east from it; one **window mark with two dots** at the middle of the alley wall; a **dashed L** inside, 1.29 m in from the east wall and 1.66 m in from the south, meeting at a small open circle (the census's "dashed partition"); a **solid dot** inside near the south-east corner (the key's vertical steam boiler); no fire-wall sign |
| Robinson's atlas, plate 10 (`robinson_1886_chicago_plate_10`) | 1886 | a **pink (brick)** building **crossed by an X** (the atlas's stable) on the alley behind **lot 2**, house number **1702** and a **105 ft** frontage in the plate's margin, about **9.6 m deep by 19.6 m along the alley** ([crop](robinson-1886-lot-2.jpg)) |

**The ruling.** The 1904 building is the 1911 sheet's: its outline, storeys, brick, X and window mark. Robinson's
plate draws a crossed brick stable of the same proportions on the same ground. Its size comes from the half-height
edges of its pink fill, which take in the plate's own border lines (0.346 m a pixel); the same profiles return lot
3's stable (1712's) as rows 1456.1-1492.2 by columns 346.4-369.9, its published reading, so the method holds, and
lot 2's is the 1911 building within two and a half of the plate's pixels. It stood from before 1886 through 1911,
and July 1904 falls between two maps that agree. The house Robinson draws on lot 2 is not the 1911 pair; that is
the houses' question (T-1871), not this one. No picture of the stable is known, so it has no image gate.

## The outline, read off sheet 20

Median darkness profiles on the committed raster
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_20.jpg`), each peak
refined by a parabola through its three highest samples:

| line | where profiled | peak |
|---|---|---|
| alley wall | rows 3830-3980 / 4020-4170 | column 2224.30 / 2224.36 |
| east (yard) wall | rows 3830-4170 | column 2429.47 |
| north wall (the lot line) | columns 2250-2400 (and 2460-2600, east of the building: 3807.43) | row 3807.13 |
| south wall | columns 2250-2400 | row 4188.56 |
| dashed L, its east leg | rows 3830-4140 | column 2404.00 |
| dashed L, its south leg | columns 2250-2390 | row 4155.92 |

At the sheet's 0.050779 m a pixel: 10.417 m deep by 19.369 m along the alley. The middle of the alley wall, pixel
(2224.33, 3997.85), carried by the sheet's similarity fit, is local E 1334.918, N -3092.268 (UTM 448407.618,
4634303.532). The draft had stood it inside a rectangle fitted to its trace (polygon 10.4 by 19.5 m).

The window mark: its ticks cross the wall line at about rows 3985-3995 and its dots stand inside the wall at about
rows 3997 and 4009 (a dot for each storey). That is **9.74 m** from the north wall line and **9.63 m** from the
south, the middle of the wall. The boiler dot is at about (2369, 4133), 7.3 m from the alley and 2.8 m from the
south wall. The dashed L stands 1.29 m inside the east wall and 1.66 m inside the south; it divides the inside and
shows nothing outside, so it is not built.

The neighbours: the lot line south of the stable is 2.9 m past its gable (row 4245), and 1712's stable begins 10.6
m south.

## What K12 builds

- **North end:** the kit's party wall, on the lot line, rising 0.45 m above the roof under its coping. The sheet
  draws no fire-wall sign; a wall on the lot line is where the kit's party wall belongs (in the liberty).
- **South end:** the kit's open gable, blank, as the sheet marks no window on it.
- **Alley wall:** the carriage bay (3.0 m clear) toward the north end with the loft hatch over it; the marked stable
  sash with a loft sash over it at the middle, where the mark stands (s 9.41 from the party wall's inner face); a
  man door and a second stable sash, each with a loft sash over it, toward the south end. Only the mark is the
  sheet's; the rest is the kit's, spaced along the longest alley wall in the package.
- **Yard wall:** a door at the middle between four stable sash, loft sash over the outer two.
- **Roof:** one gable, ridge along the alley, at 30 degrees, about 3.0 m eave to ridge over the 10.42 m span, as the
  deep stables (1616, 1612, 1626, 1628, 1736) took over 11-15 m. 1712's shallow 7.64 m span kept the kit's 40.
- **Workyard:** paved from the yard door to the pair's shared rear wall line, 22.6 m east, between the two
  townhouses' rear ranges. The walk takes the middle because which household the stable served is not read.
- **Not built:** the boiler's stack (the kit has none and the sheet draws none), and the dashed partition.

`tools/check_coach_house_kit.py --check`: 10 variants, every piece seated or rooted, no doubled face, every elevation
closed, every opening cut through. The master is 123.2 KB and the web derivative 28.9 KB, 1,632 triangles (the
draft's was 1,592).

`lay_prairie_1904_street_furniture.py`, re-run with the baked model tracked, steps the alley's pole #04 0.45 m west,
to 0.9 m inside the alley's east edge (E 1334.58 to 1334.13): it stood under the new alley eave at the stable's
middle. Its wires to #03 and #05 clear the eave from there; no other pole moves.

## In the app

`QA_TARGET=1700 node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at four stands (down the alley from
the north and from the south, the yard face from the pair's back yard, and the air) at 1280x800 full and 390x780
light: `browser-validation-after-<viewport>.json` and `after-<viewport>-<stand>.jpg` in this folder. Both
viewports: 0 page errors, 0 failed requests, all three records placed (the stable, the 1700 house and 1712's stable
south of it).

| viewport | load to ready | JS heap | stand | draw calls | triangles | in budget |
|---|---|---|---|---|---|---|
| desktop, full | 57.1 s | 83.6 MB | alley from the north | 7,590 | 4.87 M | **no** (4.70 M) |
| | | | alley from the south | 2,473 | 2.05 M | yes |
| | | | yard face | 5,926 | 1.39 M | yes |
| | | | air | 1,851 | 1.40 M | yes |
| mobile, light | 35.9 s | 109.8 MB | alley from the north | 4,892 | 0.90 M | yes |
| | | | alley from the south | 2,184 | 0.63 M | yes |
| | | | yard face | 1,489 | 0.24 M | yes |
| | | | air | 1,848 | 0.55 M | yes |

Load times are this runner's software GL, relative only.

**The one stand over budget is the view, not the stable.** Desktop's alley-from-north stand, 10 m north of the
stable's party wall looking south down the whole alley toward 18th Street, draws 4.87 M triangles against the full
tier's 4.70 M near budget (draw calls 7,590 of 7,800). The stable adds 40 triangles to what the draft drew there
(1,632 against 1,592), so the same eye on dev would read within a few hundred triangles of it (inferred from the
meshes, not measured here); 1712's alley-from-north stand, 30 m further south with less of the alley ahead of it,
read 4.58 M. The stand is left where it was chosen
rather than moved until it passes.

**An open defect: the workyard's apron is under the lawn.** `buildings.js` stands a structure on the lowest ground
under its feet (`building-feet.js`, T-3029), and its feet are every edge on the y = 0 plane, the workyard's paving
included. The ground here falls east, 4.030 m at the alley wall to 4.004 at the yard wall and 3.945 at the walk's
far end 33 m in, so the stable is bedded at the walk's end, about 8.5 cm under its alley wall's ground, and the
0.04 m apron lies a few centimetres under the lawn beside the yard wall (the yard face shows grass to the door
sill). 1712's walk ends 25 m in, on ground about 6 cm below its alley wall's, and its apron clears the lawn by a few
millimetres, which is why it shows.
The paving is in the GLB (`k12_brick_paving`, u 10.42-33.02 m); the fault is in how the renderer seats a building
whose foot plane carries an open slab, which is a renderer and GLB-contract question, not this stable's. It is
recorded on T-1932, whose acceptance asks for visible defects to be fixed before the ticket closes.
