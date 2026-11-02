# 1816 Prairie's alley stable on the K12 kit (T-1935)

`henderson_house_1816_prairie_coach_house` moves off the district draft (T-2329) onto the K12
coach-house kit, under the same id. It is the first of T-1935's seven alley buildings on the west
side of Prairie Avenue, 18th to 20th Street. 1812's coach house next door (T-2321) was the first K12
building on this sheet. Liberty: `L-k12-1816-stable-1935`.

## What sheet 28 of the 1911 Sanborn draws

The readings are median darkness profiles on the committed raster
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_28.jpg`;
the crop is `sanborn-1911-sheet-28-stable.jpg`, origin pixel 540, 2000). They are carried to the
local frame by `data/traces/gcp/sanborn_1911_v3_sheet_28_gcps.json`.

| reading | pixels | metres |
|---|---|---|
| alley wall line (rows 2100-2140 / 2250-2290 / 2420-2460) | 580.00 / 578.99 / 576.02; fitted 578.51 at the middle row | — |
| east wall line (rows 2100-2140 / 2300-2340 / 2420-2460) | 792.04 / 788.03 / 787.85 | depth 211.0-211.4 px = **10.68 m** |
| north wall line | 2041.03 (1812's own wall line at 2034, 0.35 m north) | — |
| south wall line, shared with 1824's building | 2484.00 | length 442.97 px = **22.40 m** |
| window marks on the alley wall, two dots each | rows 2165 and 2352 | 6.27 and 15.72 m from the north wall |
| the house's rear range, west wall | column 1021, rows 2107-2258 | 11.64 m east of the yard wall |

The building also carries `2½` storeys, brick (pink), wall figures `12 8` inside its north and south
walls, and the key's fire-wall sign at the alley end of both of those walls. A dashed line runs
about 1.1 m inside the east wall (the key's frame partition). It is not built, because it is inside
the building.

The middle of the alley wall is at local E 1338.640, N -3272.140, which is 0.11 m from the middle of
the rear line of parcel `prairie_1816`. The bearing is the parcel's, -0.621 degrees.

The draft had fitted this building as 9.25 m deep, with two 1.25 m strips on the alley side. The
sheet draws one plain rectangle.

## What is built and what is reconstructed

- **Ends.** Both ends are party walls, as the fire-wall signs show, so the building has no open gable.
- **Window marks.** Each mark becomes a stable sash with a loft sash above it.
- **Rest of the alley wall.** The kit's openings, laid out for a building this long:
  - two 3.0 m carriage bays;
  - the loft hatch and hoist over the northern bay;
  - a man door between the bays;
  - a third stable sash and loft sash toward the south end.
- **Yard wall.** Four stable sash with loft sash above them, and a door where the paved walk to the
  house's rear range meets the wall.
- **Roof.** The kit's 40-degree gable, ridge along the alley, 4.5 m from eave to ridge. The half
  storey sits under it.
- **Use.** The sheet labels the building GARAGE in 1911. It is built as a stable (restriction
  `no_1911_use_labels`).
- **Street furniture.** `lay_prairie_1904_street_furniture.py` moved alley poles
  `pole.alley.indiana_prairie_18_20#01` and `#02` west, inset 1.9 m. Their wire had run through the
  longer eave.

## Dating

Robinson's 1886 plate 10 stops at 18th Street, so the range claims only the 1904 target, through the
census's carry-back.

## The image gate

T-1935's gate names two pictures for this building:

- Clark's c. 1905 view north from 1936;
- Taylor's 9974, looking south from 18th.

Both show the house fronts on Prairie Avenue and not the alley. No camera is solved here. The gate
stays on T-1935.

## Browser check

`QA_TARGET=1816 node tools/qa_k12_t1932.mjs` ran on the published `/1904/` app. It passed at both
viewports, every stand inside its detail budget, with no page error and no failed request. The run's
record is `browser-validation-after.json`.

| viewport | heap | load |
|---|---|---|
| 1280×800, full detail | 75.5 MB | 71 s |
| 390×780, light detail | 69.8 MB | 37 s |
