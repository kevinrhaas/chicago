# The district draft's named context buildings off Prairie Avenue (T-2982)

Piece 1 of T-2162, the district's edges. The parent's bound split it into exactly two pieces: these named context buildings, then the background census (T-2983).

## What stands

- **213, 215 and 217 East Twentieth Street.** These are three brick rowhouses where the study register had one aggregate record (`pa-213–217-e.-cullerton-street-27`). 213 and 215 stand flat behind a cornice. 217 is drafted at 3½ storeys with a street gable and a turret at its Prairie corner for the copper oriel its photographs show. Its 3-storey rear range stands behind it.
- **2008 Calumet, the Hanford house** (Jaffray & Scott, 1883). It stands under the steep brownstone hip of its December 1883 plate, with stone faces on its Calumet front and south side as sheet 35 colours them. Its 1884 two-storey barn stands on the alley.
- **2018 Calumet, the Wheeler-Kohn house** (Wheelock, 1870). It has a mansard over the brick body and its rear range, and its brick barn on the alley.
- **Second Presbyterian Church** (Renwick, 1872-74; rebuilt by Shaw, 1900-01) stands at the north-west corner of Michigan Avenue and 20th Street. The draft has the nave with its narthex, the parish hall across the west end and the north aisle. The south-east tower carries its **full spire, the 1904 state**: the 1901 Tribune cut and Sloan's photograph (1901-1925) show it, and it was lost in 1929.

## How they were read

- **The five houses.** These were read off sheet 35 in a census of their own, `data/components/prairie_1904/edges_census_s35.json`, because the T-1842 census counts Prairie frontages only. The T-2340 tracer reads them as sheet `35x` (`data/traces/prairie_1904_footprints_s35x.json`). Two changes made that possible: its street axis now reads any lot's street and rear corners, and a sheet entry may name its own census file and parcels. Sheets 20, 28 and 35 re-derive byte for byte. The draft builder names a building by the street its lot faces (`house_213_e20th`, `hanford_house_2008_calumet`). Every Prairie record is unchanged.
- **The church.** No committed Sanborn sheet reaches Michigan Avenue, so the church is a `sites` row of the draft rules. Its plan comes from HABS IL-328 sheet 2, read at the feet bar. The metric bar disagrees by 22 %, and the pews' 0.92 m spacing settles which bar is right. Its heights come from sheet 4's printed levels: the hall's gable at 80'-1" and the nave's ridge at 87'-8 1/4". The tower's 38 m of masonry and its 16 m spire are proportions read off Sloan's photograph, so they are upper figures. Its corner is set where Michigan's line meets 20th Street's measured north line, each moved in 3 m. Michigan's centre is the e1871 terrain box's reading at 16th Street, carried south on Indiana's bearing, with a 66 ft half-width. The position is **reconstructed** and good to a few metres; T-1942 owns a measured one. Its footprint is the whole plan, so the walker's walls and the context's stand-ins give way to all of it. The church is graded **attested** on Sloan's photograph (`data/structure_grades.json`).
- **Three new source records:** `habs_second_presbyterian_il_328_drawings`, `chicago_tribune_1901_11_10_second_presbyterian` and `newberry_sloan_second_presbyterian_street`. With dev's own additions the source index stands at 162 970 bytes, inside the 168 000 budget dev set (T-2792/T-2799).
- **One liberty** covers the piece: `L-draft-district-edges-2982`.

## Captured and measured

These were captured with `node tools/qa_draft_t2982.mjs` on the published `/1904/` app (`QA_ONLY` picks stands). Desktop is 1280×800 at full detail and phone is 390×780 at light. Both runs had **0 page errors and 0 failed requests**, and every stand was within the detail budget.

| | load to ready | JS heap (after GC) | stands |
|---|---|---|---|
| desktop | 62.4 s | 58.9 MB | church across Michigan (0.47 M tris), Calumet's east walk (0.95 M tris) |
| phone | 35.9 s | 86.9 MB | church across Michigan (0.16 M tris) |

There is **no before reading**. This runner's software GL took over 8 minutes for two desktop stands at twelve timed frames each, so the harness times three frames per stand, and a before run did not fit the run's budget. The eight GLBs add 241 KB of web derivatives (1.38 MB of masters). Frame times are software-GL relative readings, not device claims.

## Limits

- The openings are the draft's rows of sash, not the church's lancets, rose and great window. The church's walls stand as three draft storeys to its 14.7 m eave. Those details belong to T-1942.
- 213's storey figure is blurred on the scan (3 or 4) and is drafted as 3.
- 2018's 3B notation carries the mansard over three full storeys, as every Second Empire draft does. T-1941 reads the house's own section.
- Indiana's and Calumet's other frontages, the end streets and the rail side are T-2983's.
