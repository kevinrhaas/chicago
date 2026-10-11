# The district draft's 16th-18th block, west side (T-2334)

Piece 1 of T-2160, the 16th-18th block of the owner's district draft pass. The builder T-2329 wrote (`tools/draft_prairie_1904.py`) is run on sheet 20's west side. The result is read in the actual published `/1904/` app.

## What stands

There are nineteen houses: 1600, 1604, 1608, 1612 Goodman, 1616, 1620 Law, the 1626/1628 pair, 1630, the 1634/1636 stone-front pair, 1700 Glessner Lee and 1706 George Glessner, 1708, 1712, 1720 Walker, 1726, 1730 and 1736. There are also thirteen alley buildings, the stables and garages that sheet 20 draws behind 1612, 1616, 1620, 1626, 1628, 1630, 1638, 1700, 1712, 1720, 1726, 1730 and 1736. That is every west-side row of the T-1840 census (frontage-20-001 to -021) and every detached rear polygon the T-2328 trace owns there. Two rows stand no new house: 1702 is an alias of 1700 (study ruling 2), and 1638's front is the K16 timber record already standing (T-2323), which this pass keeps, as T-2323 asked.

All of it is data in `data/components/prairie_1904/draft_prairie_1904.json`: block `20` (its sheet, its census, its pass and its liberty `L-draft-prairie-16-18-west-2334`) and one frontage row per address. The 67 records on both blocks re-derive under `--check`. Sheet 28's 35 records and GLBs are byte-identical.

## The study's rulings, visible

- **1700/1706: two Glessner-family townhouses and no third house at 1702.** The sheet traces the U-shaped block as one building in two parts. Each frontage row names its own part (`house_part`), so 1700 stands on the north half and 1706 on the south. The two are mirrored, with their doors at the outer ends. Their one stable is drawn once, under 1700's id.
- **1620 at its 1904 form.** The 1911 sheet shows the lot open. The census stands the Robert Law house for 1904 from Robinson 1886 and the 1904 Blue Book. Its L-shaped outline is read off Robinson 1886 plate 10 in the plate's own pixels (row `plates` in block 20). The plate's T-1250 similarity carries it into the scene (4.54 m RMS). Its plan therefore cites the plate, not the sheet. Its storeys are reconstructed, because the atlas prints none. Its stable is the sheet's own long brick building on the alley.

## Builder changes (sheet 28 output unchanged)

1. **A block names its own sheet, census, pass and fit.** `source`, `census_ticket`, `pass` and `fit_note` were hard-coded to sheet 28 (T-1841, 1.47 m RMS). They now default to those values and are read from the block.
2. **`house_part`** splits one traced building into the townhouses its census ids belong to.
3. **`house_id`** names the house a stable belongs to when this pass does not draft that house (1638's K16 front, 1620's plate house).
4. **`plates`** drafts a house the census carries from an earlier georeferenced plate: an outline in the plate's pixels, the plate's GCP file, and the notes its record carries.

## Captured and measured

Captured with `node tools/qa_draft_t2334.mjs` on the published `/1904/` app. *Before* is the tree with both sides of the 18th-20th block drafted (T-2329 + T-2330). *After* is this branch. Desktop is 1280×800 at full detail; phone is 390×780 at light. There are six stands: the north walk from 16th Street, across the avenue at 1620 and at 1700/1706, the south walk from 18th Street, the west alley and the air. All four runs had **0 page errors and 0 failed requests**.

| | load to ready | JS heap (after GC) | draw calls | triangles at the stands |
|---|---|---|---|---|
| desktop before → after | 28.6 → 19.0 s | 20.8 → 23.1 MB | 47-89 → 49-89 | 1.36-2.74 M → 1.43-2.83 M |
| phone before → after | 10.3 → 10.4 s | 20.8 → 23.1 MB | 20-52 → 22-53 | 56-405 k → 110-480 k |

The 32 GLBs add 821 KB of web derivatives (4.15 MB of masters). The renderer batches by material key, so draw calls rise by at most two. Desktop load times on this runner swing by several seconds between runs, and the fall is not a claim. Frame time is read on software GL (`frame_ms_median` in the JSON) and rose about 10-30 % with the added triangles. That is a relative reading, not a device claim.

## Limits

- 1620's outline rests on the weakest of the four georeferences. Its storeys, roof and openings are the draft's. T-1861 reads the 1898 numbered drawing the register names.
- Rounded and canted bays stay square-cornered projections. No K02-K16 kit part is laid, as on the 18th-20th block.
- The east side (1601 to 1729, with the Pullman estate, 1609-1611, 1719/1721 and Forsyth 1635) is T-2335.
