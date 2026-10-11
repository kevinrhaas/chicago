# The district draft's 20th-22nd block, west side (T-2351)

Piece 1 of T-2161, the 20th-22nd block of the owner's district draft pass. The builder T-2329 wrote (`tools/draft_prairie_1904.py`) is run on sheet 35's west side, read from the T-2340 trace and the T-1842 census, and the result is read in the actual published `/1904/` app. The east side is T-2352.

## What stands

There are thirteen houses: the frame pair 2000 and 2010, 2018, 2026, 2036 Buckingham, 2100 Sherman, 2108 Mark Kimball, 2110 Rees, 2112 Rothschild, 2120, 2126 Robbins (a building site), 2130 Murdoch and 2140 Tucker/Smith. There are also thirteen alley buildings: the stable or coach house behind each lot, one coach house shared by 2108 and 2110, and 2140's three-storey building on the alley beside its stable. That covers every west-side row of the T-1842 census (frontage-35-059 to -071) and every detached rear polygon the trace owns there.

All of it is data in `data/components/prairie_1904/draft_prairie_1904.json`: block `35` (its sheet, census, pass and liberty `L-draft-prairie-20-22-west-2351`) and one frontage row per address. The 112 records on the three blocks re-derive under `--check`. The 86 records that stood before are byte-identical, and so are their GLBs. Their manifest input hashes move only because the archetype's source is part of every draft's input hash.

## The study's rulings, visible

- **2126, one working phase (r35-robbins-2126).** On 1 July 1904 the Hamill house is razed and the Robbins house is rising. The draft stands a hollow brick shell two storeys up over its stone basement. The street wall and its returns rise 1.6 m into the third storey. The five bays are empty openings, there is no roof, a deck sits at the principal floor, and a pole scaffold stands along the street and the open side. The alley stable stands. How high the walls stood is reconstructed; a 1904 permit or a dated progress photograph replaces it (T-1926).
- **2108/2110, one coach house (r35-2108-2110-coach-house).** The sheet draws one stable across both lots, divided on the lot line, and the trace outlines it as two. The draft fills both outlines as one envelope under one roof and stands the lot line through it as a coped party wall. It is one record, `mark_kimball_house_2108_prairie_coach_house`, whose south half is Rees's.
- **Rees at 2110**, its historical site, not the site the house was moved to in 2014.
- **2140, one roof state.** The towers are drawn flat-topped and crested, the house's first state. Only a 1928 photograph dates the conical spires, and nothing puts them on the house by 1904. A dated view showing spires by July 1904 replaces this state (T-1928, T-1929).

## Builder changes (every earlier record unchanged)

1. **`join`** fills two traced buildings on neighbouring lots as one (`close_cells` closes the drawn line between them) and draws a `party_wall` feature on the lot line.
2. **`census_fix`** corrects a trace's census assignment. The T-2340 trace gave 2140's two rear buildings each other's ids. Read again on the raster, the yard building is crossed and numbered 2 (the stable), and the alley building is lettered CATERER and numbered 3.
3. **`service_outline`** fills a block's service buildings from their traced outline. Sheet 35's crossed stables are split by the trace into four triangles, which fit only as slivers.
4. **`services`** gives one of several service buildings on a lot its own id suffix and use: 2140's `…_alley_building`, an `outbuilding`.
5. **Shared lots** (`frontage_shares`): a lot that three census frontages share (2000, 2010 and 2018) keeps each house's own number and each stable's own house.
6. **`works`** stands a house still being built (2126). **`on: "bay"`** sets a turret on the sheet's own round bay (2130). **`cap: "flat_crested"`** is the corner tower's other roof state (2140).

## Captured and measured

Captured with `node tools/qa_draft_t2351.mjs` on the published `/1904/` app. *Before* is dev with the 18th-20th and 16th-18th blocks drafted. *After* is this branch. Desktop is 1280×800 at full detail, and phone is 390×780 at light. There are six stands: the walk south from 20th Street, across the avenue at 2108/2110 and at 2126, the walk north from 22nd Street, the alley and the air. All four runs had **0 page errors and 0 failed requests**, and every stand was within the detail budget.

| | load to ready | JS heap (after GC) | draw calls | triangles at the stands |
|---|---|---|---|---|
| desktop before → after | 15.9 → 15.9 s | 24.7 → 26.6 MB | 20-58 → 22-60 | 0.08-1.54 M → 0.16-1.65 M |
| phone before → after | 9.0 → 9.0 s | 24.6 → 26.5 MB | 16-51 → 20-53 | 41-501 k → 113-588 k |

The 26 GLBs add 791 KB of web derivatives (4.42 MB of masters). Frame time is read on software GL (`frame_ms_median` in the JSON) and rose about 7-35 % with the added triangles. That is a relative reading on this runner, not a device claim.

## Limits

- The 6- and 8-ft brick walls along 21st Street and the alley (2036, 2100, 2140) and 2026's open ground are not drawn, because the draft archetype has no boundary walls.
- Rounded and canted bays stay square-cornered projections, except 2130's turret and 2140's corner tower.
- 2140's main body fits as an 8.5 × 14 m rectangle inside its traced outline, which the sheet's dashed roof line splits; T-1928 reads the full plan.
- The T-2340 trace's assignment rule, which swapped 2140's two rear buildings, is that tool's to mend. The draft corrects only its own reading.
