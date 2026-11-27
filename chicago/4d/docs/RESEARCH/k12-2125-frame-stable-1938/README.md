# 2125's frame stable on the east alley, 21st-22nd: the district draft refined onto K12 in frame (T-1938)

`house_2125_prairie_coach_house` keeps its id and moves from the district draft (`prairie_draft`, T-2352) onto
the K12 coach-house kit (`k12_coach_house`), facing the alley on its east (`alley_side: east`), as 2001's,
2009's, 2011's, 2017's, 2027's, 2031's, 2033's, 2109's and 2123's did. The draft rules' `skip` now names census row
`s35-2125-rear`, so the draft builder stands no second building in its place, and its phase is
`as_standing_1904` (the `__draft_1904` master and web derivative are retired). Liberty `L-k12-2125-stable-1938`;
the draft block liberty `L-draft-prairie-20-22-east-2352` records the retirement.

It is the tenth of T-1938's alley buildings to leave the draft, and the first in **frame**. Still the draft's:
2013 (Reid, the image gate), 2021 (its tin-clad upper storey and one-storey south end), 2035 (brick and frame),
2101 (a two-storey block on 21st Street with a one-storey range south of it along the alley) and 2115 (brick, the
largest on the alley).

## What the kit gained

The kit built only brick, and only against a party wall at its west end (or a hip over four walls, T-1935). This
building is neither, so two variant fields were added to `generators/archetypes/k12_coach_house.py`:

- `west_end: gable` puts the kit's open gable, turned about the building's middle, where the party wall would
  stand. The alley and yard walls then run the building's whole length, the roof takes a verge at both ends, and
  the ground goes round a plain rectangle. Openings on the new wall (`gable_west`) count back from the yard face.
  It requires a gable roof and an east gable, and takes no ramp, stair, lean-to, wing or range yet.
- `construction: frame` stands the same shell on a 0.2 m wall (`parts.wall.frame_m`, new in
  `data/components/prairie_1904/k12_coach_house.json`), its walls in painted clapboard and its carriage ring,
  sills and lintels in painted timber trim, in K16's frame body and trim colours (`k16_timber.json` `paint`). A
  frame building must take `west_end: gable`: a party wall is a brick fire wall.

Neither field changes a brick building: `python3 generators/k12_emit.py --check` re-emits every existing K12
coach house to the same bytes. Their manifest entries move only because the kit's data file, an input of each,
changed. The kit's specimen GLB is regenerated because it carries every material. `tools/check_coach_house_kit.py`
closes the two gables of a `west_end: gable` building: 33 variants, every piece seated or rooted, no doubled
face, every elevation closed, every opening cut through.

## What the source says

Sanborn 1911, vol. 3 sheet 35 (`sanborn_1911_chicago_v3_sheet_35`), the committed copy at 0.185854 m a pixel
([crop](sanborn-1911-sheet-35-2125-stable.jpg), columns 990-1200, rows 1355-1460). The building is yellow (frame),
lettered '2' and crossed corner to corner by one X, the key's stable, with a solid dot in its south half. It is
the one building on this alley the 1911 sheet still marks as a stable rather than lettering GARAGE. No picture of
this alley is known, so it has no image gate.

Median darkness profiles, peaks refined by a parabola through the three highest samples. The same rule reads the
alley line behind 2123 at 1172.94 and the 2123/2125 lot line at 1366.91, against #2386's 1172.93 and 1367.01.

| line | reading |
|---|---|
| alley line | column 1172.98 (rows 1388-1415) |
| yard (west) wall | column 1136.00 |
| north wall | row 1381.16, 2.65 m inside the 2123/2125 lot line (row 1366.91) |
| south wall | row 1420.03, 5.22 m inside the next lot line (row 1449.07; 1448.11 at the alley end) |
| size | 6.873 m deep, 7.224 m along the alley |
| storeys | '2' |
| marks | the stable's X; a solid dot (the key's vertical steam boiler, as this project reads the sheet's dots; not built); no window mark |
| house behind | its one-storey frame rear range 23.43 m west (column 1009.95, rows 1384-1421) |

## What K12 builds

Both ends are open gables (`west_end: gable`, `east_end: gable`), in frame (`construction: frame`). The kit's x runs
north, so its west end is the south gable. On the alley, counted from the south end: a carriage bay 3.0 m clear under
the loft hatch and hoist, a man door, and a stable sash, each with a loft sash over it. On each gable a stable sash
with a loft sash over it, centred. On the yard wall a stable sash, a door and a stable sash, each with a loft sash,
the door in the middle where the workyard walk leaves for the house's rear range. The roof is at the kit's 40 degrees.
The sheet draws no window mark here, because the key marks openings only where a wall looks onto a near building. So
every opening is the kit's.

`validate.py --stale`: 0 errors. `draft_prairie_1904.py --check`: 154 draft records. Back yards: unchanged, 134
lots; their `--check` holds every surface clear of the stable's new, larger outline.

## In the app

`QA_TARGET=2125 node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at five stands (down the alley from
the north and from the south, the back yard from the south-west, the gap between 2123's stable and this one, and the
air) at 1280x800 full and 390x780 light. Both viewports: 0 page errors, 0 failed requests, all three records placed,
every stand inside the detail budget (`browser-validation-after-<viewport>.json`, `after-<viewport>-<stand>.jpg`).

| viewport | load to ready | JS heap | stand | draw calls | triangles |
|---|---|---|---|---|---|
| desktop, full | 59.6 s | 114.9 MB | alley from north | 684 | 0.94 M |
| | | | alley from south | 3,265 | 4.15 M |
| | | | yard, south-west | 909 | 0.96 M |
| | | | between the stables | 537 | 1.02 M |
| | | | air | 1,786 | 2.27 M |
| mobile, light | 41.6 s | 116.2 MB | alley from north | 420 | 0.23 M |
| | | | alley from south | 3,428 | 0.77 M |
| | | | yard, south-west | 590 | 0.26 M |
| | | | between the stables | 308 | 0.24 M |
| | | | air | 2,497 | 1.00 M |

Times are this runner's software GL, relative only. The stable's GLB is 127,004 bytes as built and 27,932 bytes as
its web derivative.
