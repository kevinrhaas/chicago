# 2021's garage on the east alley, 20th-21st: the district draft refined onto K12, free at both gables, its one-storey south end the kit's range and the gable over it tin-clad (T-1938)

`high_house_2021_prairie_coach_house` keeps its id and moves from the district draft (`prairie_draft`, T-2352) onto
the K12 coach-house kit (`k12_coach_house`), facing the alley on its east (`alley_side: east`) and built in mirror
image (`mirror`), as 2017's and 2123's are. The draft rules' `skip` now names census row `s35-2021-rear`, so the draft
builder stands no second building in its place, and its phase is `as_standing_1904` (the `__draft_1904` master and
web derivative are retired). Liberty `L-k12-2021-garage-1938`; the draft block liberty
`L-draft-prairie-20-22-east-2352` records the retirement.

It is the eleventh of T-1938's alley buildings to leave the draft. Still the draft's: 2013 (Reid, the image gate),
2035 (brick first storey and frame above, two and three storeys, joined to a building at the alley corner), 2101 (a
two-storey block on 21st Street with a one-storey range south of it along the alley) and 2115 (brick, the largest on
the alley).

## What the kit gained

- **A range on a building free at both gables.** `west_end: gable` (T-1938, 2125's) refused every fitting. The range
  stands only on the east gable and on the alley and yard walls' ends, none of which a free west end moves, so a
  BRICK building with `west_end: gable` may now carry one. A frame building still takes none, and the ramp, stair,
  lean-to and wing (each drawn against a party wall or its return) are still refused.
- **A tin-clad upper gable over the range** (`gable_upper: tin`, `parts.gable_upper`). The east gable is built in two
  walls on one plane: brick up to the range's roof (its top edge open, lying on the upper wall's foot) and painted
  sheet tin above it to the apex (new material `tin_cladding`, added last so every other file keeps its bytes). It
  is refused without a range.

`python3 generators/k12_emit.py --check` re-emits every existing coach house to the same bytes; their manifest
entries move only because the kit's generator and data, inputs of each, changed. `tools/check_coach_house_kit.py`
closes the upper gable as an elevation of its own (`gable_upper`) and gains two self-tests: the tin gable left out
(refused by `shell`) and the range pulled 5 mm off a free-gabled building (refused by `seated`). 36 variants pass.

## What the source says

Sanborn 1911, vol. 3 sheet 35 (`sanborn_1911_chicago_v3_sheet_35`), the committed copy at 0.185854 m a pixel
([crop](sanborn-1911-sheet-35-2021-garage.jpg), columns 990-1200, rows 585-690, enlarged 4x). The building is pink
(brick), lettered GARAGE, '2' in the body and '1' in the south end; the line between them is drawn yellow (frame) and
lettered **TIN CL. 2ND** along it.

Median darkness profiles, peaks refined by a parabola through the three highest samples. The same rule reads the
alley line at 1170.94 (2017's record 1170.96), the 2017/2021 lot line at 598.11 (2017's the same) and 2027's north
wall at 681.92 (2027's record 681.91).

| line | reading |
|---|---|
| alley line | column 1170.94 (rows 606-630), 1170.93 (rows 640-670) |
| yard (west) wall | column 1121.22 (rows 606-655), 1121.26 (rows 662-678): one line |
| north wall | row 601.17, 0.57 m inside the 2017/2021 lot line (row 598.11); no fire-wall sign |
| body / south end | row 660.00, the yellow 'TIN CL. 2ND' line |
| south end's wall | row 679.25, 0.50 m inside the 2021/2027 lot line (row 681.92) |
| size | 9.241 m deep; body 10.934 m and south end 3.578 m along the alley (14.51 m) |
| storeys | '2' (body), '1' (south end) |
| marks | a window mark (a cross) on the alley line at rows 636-639, 6.75 m from the north wall; a second mark at rows 671-678, in the south end; a solid dot in each part's south-east corner (the key's vertical steam boiler, as this project reads the sheet's dots; not built) |
| house behind | its one-storey brick rear range 11.93 m west (column 1057.02, rows 605-640) |

**The tin.** The census row read "its upper storey tin-clad". The lettering and the yellow lie on the one wall line
between body and south end, and the body's outer walls are pink, so the record reads 'TIN CL. 2ND' as that wall's
second storey, the part of the body's south gable above the south end's roof, and clads that part only. Its
thickness, its dull painted grey and its plain face are reconstructed.

## What K12 builds

The north end is the kit's open gable (`west_end: gable`): it stands clear of its lot line with no fire-wall sign, and
faces 2017's gable across 0.57 m, so it carries no opening. The south end is the kit's range, as deep as the body
(its yard wall on the body's line, as 1730's is), 3.578 m long, flat-roofed at the kit's 3.2 m; over it the body's
south gable is tin. On the body's alley wall, from the north end: a carriage bay 3.0 m clear under the loft hatch and
hoist, a man door, the window mark as a stable sash (centred at 6.75 m) and a stable sash toward the south gable,
each with a loft sash. On the south end's alley wall the second mark as a stable sash (centre 2.4 m past the gable;
the mark's about 2.7 m, held 0.45 m clear of the end wall). On the body's yard wall a stable sash, a door where the
walk to the house meets it and a stable sash, each with a loft sash; on the south end's yard wall a door. The
workyard is the kit's: a 2.4 m brick apron and a walk 11.93 m to the house's rear range. The kit's gable roof at 40
degrees, the ridge along the alley, a verge at each gable; no dormer, no ventilator.

`validate.py --stale`: the K12 masters restamped, every GLB byte-identical. Back yards relaid (141 lots), doors,
sidecars, the built-so-far walk, liberties.json and source-use coverage regenerated.

## In the app

`QA_TARGET=2021 node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at five stands (down the alley from
the north and from the south, the tin gable from the yard to the south-west, the yard from the west, and the air) at
1280x800 full and 390x780 light. Both viewports: 0 page errors, 0 failed requests, all four records placed (the
garage, its house, 2017's stable and 2027's barn), every stand inside the detail budget
(`browser-validation-after-<viewport>.json`, `after-<viewport>-<stand>.jpg`).

| viewport | load to ready | JS heap | stand | draw calls | triangles |
|---|---|---|---|---|---|
| desktop, full | 82.0 s | 154.4 MB | alley from north | 1,944 | 2.28 M |
| | | | alley from south | 3,002 | 4.01 M |
| | | | tin gable, south-west | 1,269 | 1.06 M |
| | | | yard, west | 873 | 0.96 M |
| | | | air | 2,281 | 2.62 M |
| mobile, light | 43.7 s | 153.1 MB | alley from north | 1,290 | 0.38 M |
| | | | alley from south | 2,464 | 0.68 M |
| | | | tin gable, south-west | 746 | 0.32 M |
| | | | yard, west | 482 | 0.26 M |
| | | | air | 3,285 | 1.04 M |

Times are this runner's software GL, relative only. The garage's GLB is 129,908 bytes as built and 34,800 bytes as its web derivative.
