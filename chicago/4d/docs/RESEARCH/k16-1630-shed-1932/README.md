# 1630 Prairie's frame shed on the alley: the district draft refined onto K16 (T-1932)

`house_1630_prairie_coach_house` keeps its id and moves from the district draft (`prairie_draft`, T-2334) onto the
K16 timber kit's whole-house builder (`k16_timber`, `frame_house`, T-2357). That is the kit 1630's own house stands
on. The draft rules' `skip` now names census row `s20-1630-r1`, so the draft builder stands no second building in its
place. The phase is `as_standing_1904` (asset `house_1630_prairie_coach_house__as_standing_1904.glb`); the
`__draft_1904` master and its web derivative are retired. Liberty `L-k16-1630-shed-1932`; the draft block liberty
`L-draft-prairie-16-18-west-2334` records the retirement.

This is the eleventh building of T-1932's package (the north-west alley, 1600-1736), and the last one that was still
standing as the draft's. It is also the alley's only frame building, so the two-storey brick K12 kit the other ten
stand on does not fit it. 1620's image-gate items stay open as #1525 left them.

## What the sources say

| source | date | what it draws on this ground |
|---|---|---|
| Sanborn 1911, vol. 3 sheet 20 (`sanborn_1911_chicago_v3_sheet_20`) | 1911 | one **yellow (frame)** building, **`1`** storey, **uncrossed**, with no use lettered ([crop](sanborn-1911-sheet-20-shed.jpg)). Its west wall is on the alley line and its north wall stands just south of the 1628/1630 lot line, where 1628's stable has its south wall. The key's **small cross** (`×`, *shingle roof*, `sanborn_1911_vol3_key.jpg`) is inside its south end. There are no window marks: the sheet draws none on frame walls here |
| Robinson's atlas, plate 10 (`robinson_1886_chicago_plate_10`) | 1886 | the rear of **lot 18** **empty** ([crop](robinson-1886-lot-18.jpg)), with the crossed brick stables of lots 16-17 to the north and the small yellow frame house at lot 18's street end only |
| T-1840 census, row `s20-1630-r1` | (1911 reading) | "1-storey frame shed on the alley" |

**The ruling.** The shed was built between 1886 and 1911. Nothing read here dates it more closely. The census carries
it into 1904, as it did for the draft, so it is built for 1904, and the record's dates say it may postdate that.

- **Use:** a yard shed (`woodshed_or_storage_shed`), INFERRED from its size (too small for a carriage and a horse) and
  the census's word. The sheet does not cross it as a stable.
- **Roof:** shingle, ATTESTED for 1911 by the key's cross.

## The outline, read off sheet 20

Median darkness profiles on the committed raster
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_20.jpg`). Each peak is
refined by a parabola through its three highest samples.

| line | where profiled | peak |
|---|---|---|
| alley wall (the alley line) | rows 3110-3200 | column 2224.69 (1628's record: 2225.06) |
| east (yard) wall | rows 3110-3200 | column 2312.79 |
| north wall | columns 2240-2300 | row 3096.63 |
| south wall | columns 2240-2300 | row 3219.13 |
| the 1628/1630 lot line (1628's south wall) | columns 2240-2440 | row 3085.35 (1628's record: 3084.95) |

At the sheet's 0.050779 m a pixel, the shed is **4.474 m deep by 6.220 m along the alley**. Its north wall is
**0.57 m** south of the lot line. The middle of the alley wall, pixel (2224.69, 3157.88), carried through the sheet's
similarity fit, is local E 1334.330, N -3049.619 (UTM 448407.03, 4634346.181). The bearing is the house's, -0.58
degrees.

## What K16 builds

One block, `rect_uv` [0, -3.11, 4.474, 3.11], with u east and v north from the middle of the alley wall:

- **Walls:** clapboard on a water table over a 0.2 m foundation, corner boards, wall tops 2.9 m over grade.
- **Eave:** a shallow 0.2 m frieze under a plain boxed eave 0.25 m deep.
- **Roof:** a 30-degree gable, its ridge along the alley.
- **Alley wall:** a four-panel door 1.2 m wide toward the south end.
- **Yard wall:** a two-panel door 0.9 m wide.
- **South gable wall:** one two-over-two sash.
- **North wall:** blank. It stands 0.57 m off 1628's stable.
- **Paint:** the house's fawn, with the weathered cedar grey-brown of its shingle roof.

Everything but the outline, storey, frame and shingle roof is RECONSTRUCTED (in the liberty).

### The kit learns one thing (additive)

A block's **`brackets: false`** gives an outbuilding a plain boxed eave: no scroll brackets along the walls and none
at the corner returns (`generators/archetypes/k16_timber.py`). `k16_timber_params.py` refuses `brackets` with any
value but `false`, and refuses it beside bracket sizes or pairs. The six K16 houses (1601, 1609, 1611, 1630, 1638's
front, 1720) rebuild byte-identical (`k16_emit.py --check`). Their manifest entries are re-stamped only because the
kit's code is one of their inputs.

The master is 284.5 KB and the web derivative 54.7 KB: **2,638 triangles** in 12 primitives, where the draft's blocks
were 188.

### The house-walks gate reads dwellings only

`tools/check_house_walks.py` asks every `k01_frontage` / `k16_timber` record for a front walk to its door. Every one of
them was a residence until now. It now skips a record whose function is not `residence`, so an alley outbuilding built
from a house kit is not asked for a front walk. No existing record changes verdict.

## In the app

`QA_TARGET=1630 node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at four stands, at 1280x800 full and
390x780 light: `browser-validation-after.json` (desktop), `browser-validation-after-mobile.json` and
`after-<viewport>-<stand>.jpg` in this folder. The stands are:

- the shed's north-west corner from the alley (looking south-east past 1628's stable);
- up the alley from the south;
- the yard face from 1630's back yard;
- the air.

Both viewports had 0 page errors and 0 failed requests. All three records were placed (the shed, the 1630 house and
1628's stable).

| viewport | load to ready | JS heap | stand | draw calls | triangles | in budget |
|---|---|---|---|---|---|---|
| desktop, full | 71.3 s | 84.2 MB | alley, north-west corner | 6,005 | 5.32 M | **no** (4.70 M) |
| | | | alley from the south | 2,160 | 1.78 M | yes |
| | | | yard face | 3,393 | 0.65 M | yes |
| | | | air | 1,613 | 1.14 M | yes |
| mobile, light | 35.8 s | 110.8 MB | alley, north-west corner | 4,388 | 1.08 M | yes |
| | | | alley from the south | 1,837 | 0.67 M | yes |
| | | | yard face | 894 | 0.19 M | yes |
| | | | air | 1,677 | 0.45 M | yes |

Load times come from this runner's software GL, shared with four other runs, and are relative only.

**The desktop over-budget stand is the sight line, not the shed.** It looks south-east across the whole 1600 and
1700 blocks. The shed is 2,638 of its 5.32 M triangles (0.05%), so without the shed the stand is still 0.6 M over.
The package's own "alley from the north" stand shows the same pressure growing as the alley is refined:

- 1626's, on the tree of its PR, read 4.58 M;
- the same pose read 4.75 M here, with 1700-1730 since refined (and it cannot see this shed behind 1628's stable).

That is a scene-wide reading at a pose in the district's densest view. It is recorded here; it is not a defect of
this building.
