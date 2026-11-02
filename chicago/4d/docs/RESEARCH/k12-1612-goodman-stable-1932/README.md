# 1612 Prairie's stable on the alley: the district draft refined onto K12, in mirror image (T-1932)

`goodman_house_1612_prairie_coach_house` keeps its id and moves from the district draft (`prairie_draft`,
T-2334) onto the K12 coach-house kit (`k12_coach_house`), as 1812's (T-2321), 1736's (T-2995), 1620's and
1616's (T-1932, [the building south of it](../k12-1616-stable-1932/README.md)) did. The draft rules' `skip`
now names census row `s20-1612-r1`, so the draft builder stands no second building in its place, and its
phase is `as_standing_1904` (asset `goodman_house_1612_prairie_coach_house__as_standing_1904.glb`; the
`__draft_1904` master and its web derivative are retired). Liberty `L-k12-1612-stable-1932`; the draft
block liberty `L-draft-prairie-16-18-west-2334` records the retirement.

This is the third building of T-1932's package (the north-west alley, 1600-1736). The rest of the
alley (1626, 1628, 1630, 1700, 1712, 1720, 1726, 1730) stays the draft's.

## What the sources say

| source | date | what it draws on this ground |
|---|---|---|
| Sanborn 1911, vol. 3 sheet 20 (`sanborn_1911_chicago_v3_sheet_20`) | 1911 | a **pink (brick)** building **crossed by one X** (the key's stable), 15.23 m along the alley by 14.02 m deep, cut north to south by a **dashed line** 7.87 m from the alley (the key's *frame partition*), each part lettered **2** (storeys); walls `12 8` inside the north and south walls; a **window mark with two dots** on the alley wall and one **with one dot** on the north wall; a **solid dot** inside near the south-east corner (the key's vertical steam boiler); a small **cross** inside near the south end of the alley wall, which the key does not explain; no fire-wall sign anywhere on it; 1616's building with its own wall line 7.5 px (0.38 m) to the south ([crop](sanborn-1911-sheet-20-stable.jpg)) |
| Robinson's atlas, plate 10 (`robinson_1886_chicago_plate_10`) | 1886 | a **pink (brick)** building **crossed by an X** (the atlas's stable) on the alley behind lot 8, about **7.1 m deep by 14.5 m along the alley** ([crop](robinson-1886-lot-8.jpg)) |

**The ruling.** The 1904 building is the 1911 sheet's: its outline, storeys, brick, X and two window
marks. Robinson's stable is the size of the 1911 building's alley part, the part west of the frame
partition (7.87 by 15.23 m, against 7.1 by 14.5 m on a plate whose lines are 0.35 m a pixel). So the
alley part stood from before 1886 through 1911, and the yard part, 6.14 m more behind the partition,
was added between 1886 and 1911. That the whole stood by July 1904 is the census's carry-back
(`present_as_mapped`), the claim the district draft already made, and the record says plainly that
the yard part may postdate 1904. No picture of the building is known, so it has no image gate.

## The outline, read off sheet 20

Median darkness profiles on the committed raster
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_20.jpg`):
the alley wall at column 2229 (rows 1850-2090, the column 1616's reading found below it), the yard
wall at 2505, the north wall at row 1817 and the south wall at 2117 (1616's north wall at 2124.5),
the partition at column 2384. At the sheet's 0.050779 m a pixel: 14.015 m deep, 15.234 m along the
alley. The middle of the alley wall, pixel (2229, 1967), carried by the sheet's similarity fit, is
local E 1333.689, N -2989.151. The draft had fitted a 13.5 by 14.5 m rectangle.

The alley wall's mark (ticks over rows 1970-1990, dots at rows 1983 and 1993) stands about 8.38 m
from the north wall line, with a dot for each storey: a stable sash and a loft sash over it. The
north wall's mark (ticks at about column 2415, its dot at 2406) stands about 9.29 m from the alley
line, east of the partition, with one dot: one stable sash, in the first storey as 1620's one-dot
mark was built. The boiler dot is at (2481, 2099), 12.8 m from the alley and 0.9 m from the south
wall; the small cross at about (2250, 2080).

Robinson's stable, by pink-density profiles on the committed plate raster: columns 339-359.5 and
rows 1084-1126, at the plate's 0.346 m a pixel.

## What K12 builds, and why in mirror image

The kit stands its party wall at one end of the alley run and its open gable at the other; every
K12 coach house before this one has its party wall to the north. Here the sheet puts the window mark
and no fire-wall sign on the **north** wall, which faces 1608's open rear yard, while the **south**
end stands 0.38 m from 1616's party wall. So the generator gained `mirror` (T-1932): the kit's run
along the alley is reversed before it is turned onto the lot, and every triangle rewound. The kit is
built and gated in its own frame, so `check_coach_house_kit.py` holds this variant to every rule it
holds the others to, and the four existing K12 GLBs build byte for byte as before (their recorded
inputs hash moves with the generator file and is refreshed).

- **South end:** the kit's party wall, rising 0.45 m above the roof under its coping. The sheet draws
  no fire-wall sign on this building; the parapet is the kit's, and this is the end hidden against
  1616's taller party wall (in the liberty).
- **North end:** the kit's open gable, with one stable sash where the sheet's mark stands.
- **Alley wall:** a man door with a loft sash over it toward the south end; the marked stable sash
  and loft sash; the carriage bay (3.0 m clear) toward the north end with the loft hatch over it.
- **Yard wall:** a door at the middle between two stable sash and two loft sash; the workyard paved
  to the house's rear wing, 13.0 m east.
- **Roof:** one gable with its ridge along the alley at 30 degrees (the deep stables' pitch at 1736,
  1812 and 1616), about 4.0 m eave to ridge over the 14.02 m span. Whether the later yard part had a
  roof of its own is not read.
- **Not built:** the frame partition (inside), the boiler's stack (the kit has none and the sheet
  draws none), and the unexplained cross.

`tools/check_coach_house_kit.py --check`: 6 variants, every piece seated or rooted, no doubled face,
every elevation closed, every opening cut through. The web derivative is 28.0 KB.

The alley's second pole (`pole.alley.indiana_prairie_16_18#01`) stood where the new stable's eave
now reaches; `lay_prairie_1904_street_furniture.py` moved it 0.45 m west, further into the alley, and
lists it under `moved`.

## In the app

`QA_TARGET=1612 node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at four stands (in
the alley 15 m south, the north gable from 1608's rear yard, the yard face from 1612's back yard, and
the air) at 1280x800 full and 390x780 light: `browser-validation-after-<viewport>.json` and
`after-<viewport>-<stand>.jpg` in this folder. Both viewports: 0 page errors, 0 failed requests, 284
of 284 structures standing.

| viewport | load to ready | JS heap | stand | draw calls | triangles | frame (software GL) | in budget |
|---|---|---|---|---|---|---|---|
| desktop, full | 73.2 s | 83.1 MB | alley from the south | 1,299 | 1.12 M | 7.9 s | yes |
| | | | north gable | 6,734 | 1.91 M | 9.6 s | yes |
| | | | yard face | 1,871 | 0.69 M | 6.5 s | yes |
| | | | air | 1,291 | 0.96 M | 6.3 s | yes |
| mobile, light | 45.2 s | 108.8 MB | alley from the south | 888 | 0.40 M | 2.0 s | yes |
| | | | north gable | 1,415 | 0.24 M | 1.8 s | yes |
| | | | yard face | 583 | 0.21 M | 1.3 s | yes |
| | | | air | 1,302 | 0.55 M | 2.4 s | yes |

Frame times are this runner's software GL, relative only.
