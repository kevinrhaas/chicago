# 1834 Prairie's alley barn on the K12 kit (T-1935)

`jones_house_1834_prairie_coach_house` moves off the district draft (T-2329) onto the K12
coach-house kit, under the same id. It is the third of T-1935's seven alley buildings on the west
side of Prairie Avenue, 18th to 20th Street, after 1816's and 1824's
(`docs/RESEARCH/k12-1816-henderson-stable-1935/`, `docs/RESEARCH/k12-1824-marsh-stable-1935/`).
Liberty: `L-k12-1834-stable-1935`.

## What sheet 28 of the 1911 Sanborn draws

The readings are median darkness profiles on the committed raster
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_28.jpg`;
the crop is `sanborn-1911-sheet-28-stable.jpg`, origin pixel 480, 3080). Each line is the
centroid of its profile's peak. They are carried to the local frame by
`data/traces/gcp/sanborn_1911_v3_sheet_28_gcps.json`.

| reading | pixels | metres |
|---|---|---|
| alley wall line (rows 3180-3220 / 3330-3370 / 3420-3460) | 571.67 / 569.98 / 569.11; fitted 570.42 at the middle row | — |
| stable's east (yard) wall line (rows 3330-3370 / 3420-3460) | 718.64 / 717.85 | depth **7.52 m** |
| north wall line, shared with 1828's building | 3153.15 | — |
| south wall line | 3476.11 | length 322.96 px = **16.33 m** |
| one-storey piece: east wall line (rows 3180-3220 / 3260-3300) | 780.56 / 780.49, against the stable's wall at 719.38 | **3.09 m** deep |
| one-storey piece: south wall line | 3309.10 | **7.89 m** along the yard wall from the north wall |
| window mark on the alley wall, a cross with a dot for each storey | row 3308.72 | 7.87 m from the north wall |
| break in the wall line between the piece and the stable | rows 3210-3238 | 2.85 to 4.32 m from the north wall |
| the house's rear porch, west face (yellow, OPEN 1st IR.CL.2nd) | column 988.37, rows 3276.22-3357.89 | 13.66 m east of the yard wall |
| the frame shed on the strip between 1834 and 1900, north line | row 3547.89 | an open strip about 3.6 m wide south of the barn |

The stable carries `2` storeys and the piece `1`, both brick (pink), wall figures `8 8` inside the
stable's south wall, and the label BARN. The `12 8` written across the north wall line stands on the
line shared with 1828's building and is not taken as this wall's. Unlike 1816's and 1824's, the sheet
draws **no fire-wall sign** at either end.

The middle of the alley wall is at local E 1339.172, N -3325.332, 0.25 m north of the middle of
parcel `prairie_1834`'s rear line. The bearing is the parcel's, -0.616 degrees.

## What is built and what is reconstructed

- **Ends.** The kit has one party wall. It stands at the north end, on the lot line, where the sheet
  draws one wall against 1828's building (still the draft's); the open gable is at the south end,
  over the open strip. The sheet's lack of a fire-wall sign is noted in the liberty.
- **One-storey piece.** Built on the kit's lean-to fitting, standing on the lot line against the party
  wall exactly as 1730's does (T-1932): 7.89 m by 3.09 m, its roof rising to 3.9 m where it dies into
  the yard wall, a stable (Dutch) door and a sash in its front. The break in the wall between it and
  the stable is an opening inside, covered by the piece, and is not built.
- **Window mark.** A stable sash with a loft sash above it, centred where the mark stands.
- **Rest of the alley wall.** The kit's, laid out for 16.3 m: two 3.0 m carriage bays, the loft hatch
  and hoist over the northern one, a man door between it and the mark, a loft sash over the southern
  bay, and a stable sash and loft sash toward the south end.
- **Yard wall.** South of the piece: two stable sash with loft sash over them, and a door where the
  paved walk to the house's rear porch meets the wall.
- **Roof.** The kit's 40-degree gable, ridge along the alley, 3.15 m from eave to ridge, no dormer.
- **Use.** BARN in 1911, built as the house's stable and coach house (inferred, carried back by the
  T-1841 census).
- **Not built.** The solid dot inside the piece (the key's vertical steam boiler; the kit has no
  stack). A small cross inside the stable's south-west corner, which 1630's shed record reads as the
  key's shingle-roof sign; if it is, the kit's slate is wrong for this roof, and the liberty says so.
- **Street furniture.** On the alley line, the barn's eave reached alley pole
  `pole.alley.indiana_prairie_18_20#03`. `lay_prairie_1904_street_furniture.py` moved it through its
  own inset list (E 1338.73 to 1336.78); its `--check` now finds no pole, crossarm or wire touching a
  baked model.

## Also in this change: 1824's stable re-stamped

`check.sh`'s staleness gate was red on `dev` for `marsh_house_1824_prairie_coach_house`: its mesh was
built on #1628's branch before #1622 changed `generators/archetypes/k01_frontage.py`, which the K12
builder imports. Rebaking it gives the same bytes (141,404) and a new inputs hash in
`assets/manifest.json`.

## Dating

Robinson's 1886 plate 10 stops at 18th Street, so the range claims only the 1904 target, through the
census's carry-back.

## The image gate

T-1935's gate names one picture for this building, Clark's c. 1905 view north from 1936. It shows the
house fronts on Prairie Avenue and not the alley. No camera is solved here, and the gate stays on
T-1935.

## Browser check

`QA_TARGET=1834 node tools/qa_k12_t1932.mjs` ran on the published `/1904/` app, one viewport per
call. It passed at both, every stand inside its detail budget, with no page error and no failed
request. The records are `browser-validation-after-desktop.json` and
`browser-validation-after-mobile.json`.

| viewport | heap | load |
|---|---|---|
| 1280×800, full detail | 75.4 MB | 74 s |
| 390×780, light detail | 70.0 MB | 49 s |
