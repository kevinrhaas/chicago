# The background behind Prairie Avenue carried south: Calumet 20th-22nd (T-3018)

Piece 1 of T-3010 (piece 3 of T-2983). Calumet Avenue's west frontage, 20th to 22nd Street, drafted
from Sanborn 1911 sheet 35 as the background census (`data/components/prairie_1904/background_census.json`,
T-3008) ranks it: 21st-22nd, 6 of 6 lots seen (2140 from 20 Prairie stands, 2128 from 19, 2124 from 15);
20th-21st, 4 of 6 (2032 from 7; 2008 and 2018 are already the named Hanford and Wheeler-Kohn houses, T-2982).

- **Census** `edges_census_s35e.json`: ten frontages read by eye off the committed scan (1602 x 2000 px)
  at 3x, 2032's storey figure at 8x. 2016 is read and drafted though no Prairie stand sees it, so the
  frontage stands whole.
- **Trace** `data/traces/prairie_1904_footprints_s35e.json` (sheet `35e`): 10 parcels, 21 buildings.
  One new rule, `ABUT_M` (1.5 m): an outline the census has no id for, that near the house, is the
  house's, closed across the gap. It fires only while some outline would otherwise go unnamed, so every
  other sheet (20, 28, 35, 35x, 28x) re-derives byte-identical; here it joins 2100's frame porch (1.3 m
  off the house across the porch's dashed edge on this coarse copy) and 2140's 1B rear piece.
- **Drafts**: ten houses, nine alley stables (six lettered GARAGE, VACANT or REPAIRING & GARAGE in
  1911, backcast under study ruling 11) and two sheds. Liberty `L-draft-district-background-3018`.

## Browser validation (published /1904/, `node tools/qa_draft_t3018.mjs`)

| viewport | load to ready | JS heap (after GC) | stands within budget | page errors / failed requests |
|---|---|---|---|---|
| 390x780, light | 38.3 s | 95.6 MB | 4 of 4 (max 0.68 M tris of 1.27 M) | 0 / 0 |
| 1280x800, full | 86.2 s | 61.4 MB | 4 of 4 (max 3.62 M tris of 4.6 M) | 0 / 0 |

The heaviest desktop stand is Calumet's east walk at 22nd looking north (3.62 M). T-3012's stand at 20th
looking north, already at the budget before this face was drafted, is that ticket's and is not re-read here.
