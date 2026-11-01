# 1720 Prairie's stable and its range on the alley: the district draft refined onto K12 (T-1932)

`walker_house_1720_prairie_coach_house` keeps its id and moves from the district draft (`prairie_draft`, T-2334)
onto the K12 coach-house kit (`k12_coach_house`), as 1812's (T-2321), 1736's (T-2995), 1620's, 1616's, 1612's,
1626's, 1628's, 1712's and 1700's (T-1932, [the last of them](../k12-1700-stable-1932/README.md)) did. The draft
rules' `skip` now names census rows `s20-1720-r1` (the stable) and `s20-1720-r2` (the range), so the draft builder
stands no second building in their place, and the phase is `as_standing_1904` (asset
`walker_house_1720_prairie_coach_house__as_standing_1904.glb`; the `__draft_1904` master and its web derivative are
retired). Liberty `L-k12-1720-stable-range-1932`; the draft block liberty `L-draft-prairie-16-18-west-2334` records
the retirement.

This is the eighth building of T-1932's package (the north-west alley, 1600-1736). It is the first one the kit could
not build as it stood: a two-storey stable with a one-storey brick range carried on along the alley past its south
gable. So the kit learns a **range** fitting (below), and the draft's worst piece on the alley goes: the stable's
cross had cut its trace into four triangles, and the draft stood the building as seven rectangles of mixed heights
(a 4.0 by 6.5 m "main body" among them). The rest of the alley (1630, 1726, 1730) stays the draft's.

## What the sources say

| source | date | what it draws on this ground |
|---|---|---|
| Sanborn 1911, vol. 3 sheet 20 (`sanborn_1911_chicago_v3_sheet_20`) | 1911 | a **pink (brick)** building **crossed by one X** (the key's stable), lettered **2**, with `12 12` inside its north wall and again inside its south wall ([crop](sanborn-1911-sheet-20-stable-range.jpg)); 10.11 m deep by 16.61 m along the alley; its north wall 1.20 m short of the 1712/1720 lot line; **one window mark with two dots** on its alley wall. South of it, on the alley line, an **uncrossed pink range lettered 1**, 4.22 m deep, running on past the 1720/1726 lot line to the building lettered GARAGE behind 1726, with **one window mark with one dot** on its alley wall at the lot line; no fire-wall sign anywhere |
| Robinson's atlas, plate 10 (`robinson_1886_chicago_plate_10`) | 1886 | behind **lot 4**, a **pink (brick)** building **crossed by an X** (the atlas's stable), about **9.1 m deep by 11.2 m along the alley**, and south of it, joined to it, an **uncrossed pink range** about **6.1 m deep by 13.4 m along the alley**, ending on the lot 4/5 line ([crop](robinson-1886-lot-4.jpg)); behind lot 5 a yellow (frame) building, not the range |

**The ruling.** A brick stable with a brick range south of it stood here from before 1886 through 1911, so July
1904 falls between two maps that agree it was there. They divide the run differently: the plate's crossed stable is
about 11.2 m and its range 13.4 m, the sheet's 16.6 m and 6.9 m to the lot line. The run from the north lot line to
the south one is alike on both (26.6 m on the plate, 24.7 m on the sheet; the plate reads long at this lot, as it
read 6% long at 1712's). Either the stable was lengthened southward over part of the range between the two maps, or
one map divides the run otherwise. The sheet's division is built, as the T-1840 census rules the 1911 buildings
present in 1904 and the sheet is the finer survey. By 1911 the range also runs on past the lot line to the garage
behind 1726, which the plate does not draw (a frame building stands there in 1886). The range is built **ending on
the lot line**, as the plate ends it; what stood south of the line in 1904 is 1726's ruling, and its draft still
stands a two-storey piece there, 0.56 m short of the line. No picture of the stable is known, so it has no image
gate.

## The outlines, read off sheet 20

Median darkness profiles on the committed raster
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_20.jpg`), each peak
refined by a parabola through its three highest samples:

| line | where profiled | peak |
|---|---|---|
| alley wall, stable | rows 4740-4880 / 4930-5040 | column 2225.03 / 2225.78 |
| alley wall, range | rows 5065-5170 | column 2225.66 |
| stable's east (yard) wall | rows 4745-5035 | column 2424.53 |
| stable's north wall | columns 2240-2400 | row 4726.06 |
| the 1712/1720 lot line | columns 2440-2600 | row 4702.44 |
| stable's south wall | columns 2330-2410 (east of the range) | row 5053.23 |
| range's east wall | rows 5065-5180 | column 2308.84 |
| the 1720/1726 lot line | columns 2330-2600 | row 5189.75 |
| across the range, on the lot line | columns 2240-2290 | no line (peak 92, against 250 for a drawn line) |

At the sheet's 0.050779 m a pixel: the stable is 10.112 m deep by 16.613 m along the alley; the range 4.224 m deep
by 6.932 m from the stable's south wall line to the lot line. The middle of the stable's alley wall, pixel (2225.41,
4889.65), carried by the sheet's similarity fit, is local E 1335.616, N -3137.547 (UTM 448408.316, 4634258.253).

The window marks: the stable's ticks cross the wall line at about rows 4897 and 4905, with its dots at about 4902 and
4920 (a dot for each storey), **8.90 m** from the north wall line and 7.72 m from the south. The range's crosses at
about row 5187 with one dot at 5196, **6.79 m** from the stable's south wall line and 0.14 m short of the lot line.

Robinson's lot 4, by pink-density (red minus green) profiles on the committed plate raster, half-height edges:
the stable rows 1508.1-1540.4 (over columns 367-372, east of the range) by columns 347.2-373.5; the range rows
1540.4-1579.0 by columns 347.3-364.9; the lot lines at rows 1502 (3/4) and 1579 (4/5). The same profiles return
lot 3's stable (1712's) as columns 346.4-369.8, its published reading.

## What K12 builds

- **The range fitting (new).** `range: {length_m, depth_m}` on a variant: a one-storey brick range carried on along
  the alley past the open gable. Its alley wall continues the stable's alley wall line and its end stands on that
  wall's end; its yard wall's end stands on the gable's face; a closed end wall at the far end; the wing's flat roof
  3.2 m up, flush with the alley face, dying into the gable and past the far end and the yard wall by 0.1 m.
  Openings go on `range_alley`, `range_yard` and `range_end`. `tools/check_coach_house_kit.py` holds its walls on
  the ground and seated, and two new self-test cases break it (19 cases, all refused). The specimen and the other
  ten variants are byte-for-byte unchanged.
- **North end:** the kit's party wall, rising 0.45 m above the roof, 1.20 m short of the lot line with nothing
  against it. The sheet draws no fire-wall sign and no window on that wall; the kit's end wall is in the liberty.
- **South end:** the kit's open gable, the range against its lower 3.45 m, blank above it.
- **Stable's alley wall:** the carriage bay (3.0 m clear) toward the north end with the loft hatch over it; the
  marked stable sash with a loft sash over it, centred where the mark stands (s 8.57 from the party wall's inner
  face); a man door with a loft sash over it toward the south end.
- **Stable's yard wall:** a door at the middle between four stable sash, loft sash over the outer two.
- **Range:** the mark's sash on its alley wall, set 0.25 m short of the end wall (centre 6.18), 0.61 m north of
  where the 1911 sheet puts it, because the 1911 mark stands in a wall that by then ran on past the lot line; a door
  in its yard wall at its middle (invented: the range has to open somewhere, and the yard is where its work was).
- **Roof:** one gable over the stable, ridge along the alley, at 30 degrees over the 10.11 m span, as the deep
  stables (1616, 1612, 1626, 1628, 1700, 1736) took; the range flat.
- **Workyard:** paved from the yard door to the 1720 house's rear wall line, 13.72 m east at the stable's middle.

`tools/check_coach_house_kit.py --check`: 11 variants, every piece seated or rooted, no doubled face, every elevation
closed, every opening cut through. The master is 123.6 KB and the web derivative 30.7 KB, 1,620 triangles (the
draft's seven blocks were 1,436).

`lay_prairie_1904_street_furniture.py`, re-run with the baked model tracked, found the wire from the alley's pole
#05 to #06 running through the stable's party wall 2.3 m along, and stepped both poles 1.0 m further into the alley
(insets 0.9 to 1.9 m); no other pole moves.

## In the app

See the table below, written by `QA_TARGET=1720 node tools/qa_k12_t1932.mjs` on the published `/1904/` app.
