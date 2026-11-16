# The open frame shed between 1834 and 1900 Prairie: the district draft refined onto K16 (T-1935)

`shed_1834_1900_prairie` keeps its id. It moves from the district draft (`prairie_draft`, T-2329) onto the K16
timber kit's whole-house builder (`k16_timber`, `frame_house`, T-2357), the builder 1630's alley shed on sheet 20
stands on (T-1932). The draft rules' `skip` now names census row `s28-vacant-west-1834-1900`, so the draft builder
stands no second building here. The phase is `as_standing_1904` (asset
`shed_1834_1900_prairie__as_standing_1904.glb`). The `__draft_1904` master and its web derivative are retired.
The new liberty is `L-k16-1834-1900-shed-1935`. The draft block liberty `L-draft-prairie-18-20-west-2329` records
the retirement.

This is the seventh and last of T-1935's alley buildings on the west side of Prairie Avenue, 18th to 20th. The six
before it (1816, 1824, 1834, 1900, 1906, 1912) are brick and stand on K12. This one is frame.

## What the sources say

| source | date | what it draws on this ground |
|---|---|---|
| Sanborn 1911, vol. 3 sheet 28 (`sanborn_1911_chicago_v3_sheet_28`) | 1911 | one **yellow (frame)** building lettered **`1`** (storey), **uncrossed**, with no use lettered ([crop](sanborn-1911-sheet-28-shed.jpg)). It stands at the alley end of the narrow unnumbered strip between 1834 and 1900. Its **alley (west) line is solid** and its **south line is solid**: that is the line it shares with 1900's pink two-storey stable, and the key's fire-wall sign stands at its alley end. Its **north and east sides are DASHED**. The key's **small cross** (`×`, *shingle roof*) is inside its south-east corner. There are no window marks: the sheet draws none on frame walls here |
| Robinson's atlas, plate 10 (`robinson_1886_chicago_plate_10`) | 1886 | stops at 18th Street: nothing on this block |
| T-1841 census, row `s28-vacant-west-1834-1900` | (1911 reading) | "unbuilt at the street, with a one-storey frame shed (yellow) at its alley end" |

**The ruling.** The shed stood by 1911. Nothing read here dates it more closely. The census carries it into 1904,
as it did for the draft, so it is built for 1904, and the record's dates say it may postdate that.

### The two dashed sides are read as open (INFERRED)

The 1911 key (`sanborn_1911_vol3_key.jpg`) explains one dashed line: the *frame partition*, a line drawn inside a
building. These two dashed lines are the building's own edges, and the key has no entry for a dashed outer wall.
The sheet draws open porches dashed (1726's open porch on sheet 20, read so in T-2934), so this reading takes them
as **open sides**:

- the shed is walled on the alley;
- on the south it stands against 1900's brick wall;
- it is open on the north, onto the 3.6 m open strip south of 1834's barn;
- it is open on the east, into the strip's yard.

If the dashes mean something else, the two sides are walls. The liberty says so.

- **Use:** an open yard shed (wagons, wood, coal), INFERRED from its form and the census's word. The sheet does
  not cross it as a stable.
- **Roof:** shingle, ATTESTED for 1911 by the key's cross.

## The outline, read off sheet 28

Darkness profiles on the committed raster
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_28.jpg`). Each peak is
refined by a parabola through its three highest samples. The dashed lines are read by mean profiles, so the gaps
between dashes do not hide the line; the solid ones by median.

| line | where profiled | peak |
|---|---|---|
| alley wall (the alley line) | rows 3555-3575, 3580-3600, 3600-3620 | columns 567.52, 567.47, 567.34 (1900's record: 567.44 just south) |
| east side (dashed) | the same rows | columns 749.84, 749.46, 749.43 (1900's east wall continues it below: 748.80) |
| north side (dashed) | columns 580-640, 640-700, 700-745 | rows 3547.04, 3547.83, 3548.65; 3547.89 over 580-745 (1834's record: 3547.89) |
| south wall (1900's north wall) | columns 580-745 | row 3624.85 (1900's record: 3625.03, taken) |

At the sheet's 0.050558 m a pixel, the shed is **9.201 m deep by 3.900 m along the alley**. The middle of the alley
wall is pixel (567.47, 3586.46). Carried through the sheet's similarity fit, that is local E 1339.266,
N -3339.075 (UTM 448411.966, 4634056.725). The bearing is the parcel's, -0.616 degrees, as 1834's and 1900's
buildings are. The draft had stood an 8.75 x 3.75 m rectangle fitted inside the trace.

## What K16 builds

One block, `rect_uv` [0, -1.95, 9.201, 1.95], with u east and v north from the middle of the alley wall. It stands
`against` the south side, where the record's `party_wall` names 1900's stable: the K12 stable builds that brick
wall, and this record does not.

- **Alley wall:** clapboard on a water table over a 0.2 m foundation, wall top 2.9 m over grade. It has a 0.2 m
  frieze under a plain boxed eave 0.25 m deep with no brackets (`brackets: false`). It has no opening: the sheet
  marks none on a frame wall, and the open sides are the way in.
- **Roof:** a 30-degree gable, its ridge running back from the alley along the shed's length. The gables face the
  alley and the yard, and the slopes shed north onto the open strip and south to the foot of 1900's wall. This is
  the same long-axis choice 1630's shed takes.
- **Open north and east sides:** five square posts 0.21 m on brick footings, no more than 3.2 m apart: four along
  the north side and one midway along the east. The posts carry a 0.25 m plate whose top meets the roof boards.
  The east plate runs into 1900's wall, so that end takes no post. A fascia runs along the open north eave, and
  the east gable is closed above its plate.
- **Inside:** the roof is boarded underneath. The alley wall and both gables are boarded on their inner faces,
  so nothing seen from inside the shed is the back of a face.
- **Paint:** 1630's shed's fawn, with the weathered cedar of its shingle roof.
- **The alley's poles:** the street-furniture layer (`tools/lay_prairie_1904_street_furniture.py`, T-3225)
  re-reads the alley with the shed built; poles #03 and #04 and their wire clear it where they stand.

Everything but the outline, storey, frame, shingle roof and which sides are dashed is RECONSTRUCTED (in the
liberty). The master is 83.1 KB and the web derivative 21.9 KB: **736 triangles**.

### The kit learns one thing (additive): open sides

A gabled `frame_house` block may name `open` sides. They must be sides the block would otherwise wall, and at
least one side must stay walled. It may also name `post_pitch_m` (1.5-4.0 m, default 3.0):

- each open side stands on posts under a plate, with no wall;
- a wall beside an open side ends cut at that corner, and the corner post covers the cut end;
- an open gable side still carries its gable;
- an open eave side gets a fascia;
- the roof is boarded underneath;
- the insides of the walls and gable backs are taken into the model as boards (the role `sheathing`), not
  dropped as a closed room's plaster.

All of this is in `generators/archetypes/k16_timber.py` (`_open_sides`, `frame_house_parts`) and is checked in
`k16_timber_params.py`. The ten K16 records already built (1601, 1609, 1611, 1630 and its shed, 1638's front,
1720, 1721, 2000, 2010) rebuild byte-identical (`k16_emit.py --check`). Their manifest entries are re-stamped only
because the kit's code is one of their inputs.

## In the app

`QA_TARGET=shed node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at five stands, at 1280x800 full
and 390x780 light. The results are in this folder: `browser-validation-after.json` (desktop),
`browser-validation-after-mobile.json` and `after-<viewport>-<stand>.jpg`. The stands are:

- the strip, from the north-east, looking into the open sides;
- the alley, from the north;
- the yard face, from the strip's yard, looking through the open east side to the alley wall;
- inside the shed, looking at the alley wall and its gable;
- the air.

Both viewports had 0 page errors and 0 failed requests. All three records were placed (the shed, 1900's stable
and 1834's barn), and every stand was inside the detail budget.

| viewport | load to ready | JS heap | stand | draw calls | triangles | in budget |
|---|---|---|---|---|---|---|
| desktop, full | 79.1 s | 105.1 MB | strip, north-east | 1,468 | 1.21 M | yes |
| | | | alley from the north | 2,740 | 2.60 M | yes |
| | | | yard face | 1,239 | 0.93 M | yes |
| | | | inside | 1,092 | 0.87 M | yes |
| | | | air | 2,133 | 2.41 M | yes |
| mobile, light | 44.7 s | 101.5 MB | strip, north-east | 692 | 0.26 M | yes |
| | | | alley from the north | 2,090 | 0.55 M | yes |
| | | | yard face | 750 | 0.29 M | yes |
| | | | inside | 610 | 0.28 M | yes |
| | | | air | 1,414 | 0.49 M | yes |

Load times come from this runner's software GL, shared with four other runs, and are relative only.

**The harness exits non-zero for a reason that is not this building's.** Every stand carries one problem line,
`fort_dearborn_massacre_monument_1893: review_required is set — review annotation retained; this flag does not
block scene release`. That is the monument's record as it stands on `dev`, not this shed's, and the line itself
says it does not block release. No other problem was reported.

## The image gate

T-1935's gate names one picture for this building: Clark's c. 1905 street view north from 1936
(`a18-chm-clark-c1905-prairie-west-side-north-from-1936`). Like the six alley buildings before it, the picture
shows the house fronts on Prairie Avenue and not the alley, so no camera is solved for the shed.
