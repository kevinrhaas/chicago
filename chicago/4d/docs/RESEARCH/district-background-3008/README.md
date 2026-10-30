# The background behind Prairie Avenue, begun: Calumet 18th-20th (T-3008)

Piece 1 of T-2983. Two things land together:

1. **The visibility census** — `tools/census_prairie_1904_background.py` writes
   `data/components/prairie_1904/background_census.json`. Sight lines from 264 stands (every 6 m
   along both Prairie Avenue walks, 16th-22nd, eye 1.6 m) to every non-Prairie parcel and every
   block's unlotted ground (4 m sample grid at 2 m and 9 m), blocked by the 153 traced buildings
   as prisms to a height from their printed storeys. **56 of 66 targets are seen.** By group:

   | group | targets | seen | most stands |
   |---|---|---|---|
   | Indiana, 16th-18th | 17 | 12 | 13 |
   | Indiana, 20th-21st | 11 | 11 | 25 |
   | **Calumet, 18th-20th (this PR)** | 10 | 9 | 36 (1800, Pullman's ground) / 22 |
   | Calumet, 21st-22nd | 6 | 6 | 20 |
   | Indiana, 21st-22nd | 8 | 6 | 6 |
   | Calumet, 20th-21st | 6 | 4 | 7 |
   | E. 20th / E. 21st / E. 16th lots | 6 | 6 | 31 |
   | unlotted Indiana half of 18th-20th | 1 | 1 | 48 |
   | the Illinois Central strip, 16th-18th | 1 | 1 | 24 |

   It errs toward *seen*: trees, fences and roof pitch are not counted.

2. **Calumet's west frontage, 18th-20th, drafted** from Sanborn 1911 sheet 28 (census
   `edges_census_s28.json`, trace `prairie_1904_footprints_s28x.json`): nine brick houses
   (1830-1932), four stables and 1922's garage backcast as a stable, and the one-storey strip of
   1910's stable that crosses onto the 1922 lot. 1800 Calumet is Pullman's glasshouse ground,
   T-1934's. Liberty `L-draft-district-background-3008`.

## Browser validation (published /1904/, `node tools/qa_draft_t3008.mjs`)

| viewport | load to ready | JS heap (after GC) | stands within budget | page errors / failed requests |
|---|---|---|---|---|
| 390x780, light | 34.6 s | 91.2 MB | 4 of 4 (max 0.76 M tris of 1.27 M) | 0 / 0 |
| 1280x800, full | 61.9 s | 60.4 MB | **3 of 4** | 0 / 0 |

The desktop stand on Calumet's east walk at 20th looking north reads **4.63 M triangles against
the 4.6 M full-detail budget**. The fifteen new drafts carry 30,476 triangles in all, so that stand
stood within about 2,000 triangles of the budget before them. It is filed as its own ticket
rather than hidden by moving the stand. No before reading was taken here: the before/after for the
whole background is T-3011's.
