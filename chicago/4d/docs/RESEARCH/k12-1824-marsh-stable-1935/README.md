# 1824 Prairie's alley stable on the K12 kit (T-1935)

`marsh_house_1824_prairie_coach_house` moves off the district draft (T-2329) onto the K12
coach-house kit, under the same id. It is the second of T-1935's seven alley buildings on the west
side of Prairie Avenue, 18th to 20th Street, after 1816's next door
(`docs/RESEARCH/k12-1816-henderson-stable-1935/`). Liberty: `L-k12-1824-stable-1935`.

## What sheet 28 of the 1911 Sanborn draws

The readings are median darkness profiles on the committed raster
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_28.jpg`;
the crop is `sanborn-1911-sheet-28-stable.jpg`, origin pixel 480, 2380). Each line is the
centroid of its profile's peak. They are carried to the local frame by
`data/traces/gcp/sanborn_1911_v3_sheet_28_gcps.json`.

| reading | pixels | metres |
|---|---|---|
| alley wall line (rows 2510-2550 / 2640-2680 / 2780-2820) | 575.83 / 574.78 / 573.96; fitted 574.90 at the middle row | — |
| east wall line (same rows) | 786.36 / 785.28 / 783.30; fitted 785.04 | depth 210.1 px = **10.62 m** |
| north wall line, shared with 1816's building | 2483.98 (1816's record reads 2484.00) | — |
| south wall line | 2832.18 | length 348.2 px = **17.60 m** |
| window mark on the alley wall, a cross with a dot for each storey | row 2648.9 | 8.34 m from the north wall |
| the 1824/1828 lot line, then 1828's building | rows 2893, 2913 | an open strip about 3 m wide south of the stable |
| the house's brick body, west wall | column 964.6, rows 2585.7-2799.5 | 9.08 m east of the yard wall |

The building also carries `2` storeys, brick (pink), wall figures `12 8` inside its north and south
walls, the key's fire-wall sign at the alley end of both of those walls, and the label GARAGE. A
small ring inside its south-west corner (about column 590, row 2817) is not read and builds nothing.

The middle of the alley wall is at local E 1338.811, N -3292.139. That is 1.56 m north of the middle
of parcel `prairie_1824`'s rear line, because the stable stands against the lot's north line. The
bearing is the parcel's, -0.627 degrees.

The draft had fitted this building as 9.75 by 17.25 m, set 0.75 m in from the alley. The sheet draws
one plain rectangle on the alley line.

## What is built and what is reconstructed

- **Ends.** Both ends are party walls, as the fire-wall signs show, so the building has no open gable.
  The north one stands back to back with 1816's south party wall on the line the sheet draws once.
  1626's and 1628's stables on sheet 20 do the same.
- **Window mark.** It becomes a stable sash with a loft sash above it.
- **Rest of the alley wall.** The kit's openings, laid out for 17.6 m:
  - two 3.0 m carriage bays;
  - the loft hatch and hoist over the northern bay;
  - a man door between that bay and the mark;
  - a loft sash over the southern bay;
  - a stable sash and loft sash toward the south end.
- **Yard wall.** Three stable sash with loft sash above them, and a door where the paved walk to the
  house meets the wall, on the middle of the house's brick west wall.
- **Roof.** The kit's 40-degree gable, ridge along the alley, with no dormer.
- **Use.** The sheet labels the building GARAGE in 1911. It is built as a stable (restriction
  `no_1911_use_labels`).
- **Street furniture.** On the alley line, the stable's eave reached alley pole
  `pole.alley.indiana_prairie_18_20#02`, which the draft's set-back had cleared.
  `lay_prairie_1904_street_furniture.py` moved that pole through its own inset list, 0.45 m further
  into the alley (E 1338.37 to 1337.92). Its `--check` now finds no pole, crossarm or wire touching a
  baked model.

## Dating

Robinson's 1886 plate 10 stops at 18th Street, so the range claims only the 1904 target, through the
census's carry-back.

## The image gate

T-1935's gate names one picture for this building, Clark's c. 1905 view north from 1936. It shows the
house fronts on Prairie Avenue and not the alley. No camera is solved here, and the gate stays on
T-1935.

## Browser check

`QA_TARGET=1824 node tools/qa_k12_t1932.mjs` ran on the published `/1904/` app. It passed at both
viewports, every stand inside its detail budget, with no page error and no failed request. The run's
records are `browser-validation-after.json` (desktop) and `browser-validation-after-mobile.json`.

| viewport | heap | load |
|---|---|---|
| 1280×800, full detail | 75.4 MB | 72 s |
| 390×780, light detail | 69.9 MB | 37 s |

The desktop run printed its PASS and wrote its record, then hung closing the browser, and the
harness's time limit stopped it there.
