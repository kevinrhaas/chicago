# The district draft's 16th-18th block, east side (T-2335)

Piece 2 of T-2160, the 16th-18th block of the owner's district draft pass. The builder T-2329 wrote (`tools/draft_prairie_1904.py`) is run on sheet 20's east side, and the result is read in the actual published `/1904/` app. The west side is T-2334.

## What stands

There are thirteen houses: 1601, 1609 and 1611 (the lost frame pair), the 1613/1615 pair, 1619, the 1621-1625 group of three, 1637 Spalding, 1701 Hibbard, 1709 Kellogg, 1721 Dexter and 1729 Pullman. Beside them stand the Illinois Central's 16th Street station at 1605 and four buildings by the tracks behind 1637, 1701, 1709 and 1721. That covers every east-side row of the T-1840 census (frontage-20-022 to -035) and every detached rear polygon the T-2328 trace owns there.

All of it is data in `data/components/prairie_1904/draft_prairie_1904.json`: block `20` now drafts both sides, its east side under its own pass and liberty (`L-draft-prairie-16-18-east-2335`), with one frontage row per address. The 86 records on both blocks re-derive under `--check`. The 67 that stood before this branch are byte-identical, and so are their GLBs.

## The study's rulings, visible

- **1609-1611 at their 1904 form.** The 1911 sheet draws a four-storey loft (AUTO REPAIRING, WIND SHIELD MFG.) across 1607-1611. The census rules it a later replacement and stands, on the supplied expert guidance, the frame pair Robinson 1886 draws on lot 6. Each half is read off Robinson 1886 plate 10 in the plate's own pixels: lot 6's yellow building, x 564.5-595.0 and y 1045.5-1075.0, split by the line the plate draws across it at y 1059.5. 1609 is the north half and 1611 the south. Both are carried into the scene by the plate's T-1250 similarity (4.54 m RMS), which gives two narrow frame houses about 10.5 m deep with 4.8 m and 5.4 m fronts. Their doors stand at the pair's outer ends. The loft is not drawn (rules `skip`).
- **One Dexter house at 1719/1721.** The register read the sheet's 1721 as 1719. The census rules them one property (study ruling 3), so one house stands under `dexter_house_1721_prairie`, with 1719 as its alias (the row's `register` overlay corrects the address the card shows).
- **Forsyth 1635 left unresolved.** The census marks the strip next north of 1637 `phase_unresolved`. The draft builds nothing on it, and does not put the house on 1637 or on 1625's lot. T-1870 rules.
- **The Pullman house and its conservatory.** The east wing's south bay is the K13 record already standing (`pullman_house_1729_prairie_conservatory`, T-2306), set on a plain block in the wing's place. The draft keeps that record's footprint out of the traced fabric, so the wing is drawn once and not twice. The sheet's two-storey building at the wing's east end (lettered GARAGE, a 1911 use) stands at two storeys.
- **The 16th Street station is not a house.** The sheet letters it and Robinson 1886 shows a station on the same ground, so it stands as a plain two-storey gabled building with the use `railway_station`. That is a new term in the function vocabulary, carried by this one record.

## Builder changes (every earlier record unchanged)

1. **A plate row carries its own frontage overlay** (`frontage`), so two plate houses on one census frontage get their own address, family, entrance and id (1609 and 1611).
2. **A frontage row can correct the register** (`register`), as 1721's does for the address the register misread.
3. **`use`** names a service-kind building that is no one's stable (the station): its name, its function and the front ticket that refines it.
4. **`keep_out`** removes a standing record's footprint from the traced fill before rectangles are fitted (1729's K13 conservatory wing).
5. **`wing_storeys`** sets a house's wings below its main storeys (1729's two-storey building at the wing's end).

## Captured and measured

Captured with `node tools/qa_draft_t2335.mjs` on the published `/1904/` app. *Before* is the tree with the 18th-20th block and the 16th-18th west side drafted (T-2329, T-2330, T-2334). *After* is this branch. Desktop is 1280×800 at full detail, and phone is 390×780 at light. There are six stands: the walk south from 16th Street, across the avenue at 1609/1611 and at 1721, the walk north from 18th Street, the rear by the tracks, and the air. All four runs had **0 page errors and 0 failed requests**, and every stand was within the detail budget.

| | load to ready | JS heap (after GC) | draw calls | triangles at the stands |
|---|---|---|---|---|
| desktop before → after | 25.2 → 25.3 s | 23.2 → 24.7 MB | 49-91 → 51-91 | 1.40-2.82 M → 1.45-2.90 M |
| phone before → after | 13.1 → 13.5 s | 23.2 → 24.6 MB | 18-55 → 20-55 | 85-435 k → 130-491 k |

The 19 GLBs add 567 KB of web derivatives (3.13 MB of masters). The renderer batches by material key, so draw calls rise by at most two. Frame time is read on software GL (`frame_ms_median` in the JSON) and rose roughly 5-25 % with the added triangles. That is a relative reading on this runner, not a device claim.

## Not drafted here

- **Pullman's glasshouses and lodge across 18th Street.** The sheet-28 census allocates two glasshouse ranges and the two-storey lodge between them to the Pullman estate (`s28-pullman-service-garden`, package T-1934). The sheet-28 trace never drew them, so the builder has no polygon to read, and the draft archetype has no glass roof. They are left to T-1934, which owns that glasshouse geometry and the K13 kit it needs; its ticket now says so.
- Rounded and canted bays stay square-cornered projections. No K02-K16 kit part is laid, as on the other drafted sides.
- 1609 and 1611 rest on the weakest of the four georeferences. Their storeys, roofs and openings are the draft's, and T-1867 reads them.
