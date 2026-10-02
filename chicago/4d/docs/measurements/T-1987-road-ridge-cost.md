# T-1987 — what the road's ridge costs a frame

`PW_EXECUTABLE=… node tools/measure_detail_ceilings.mjs --only desktop --against <base>`,
2026-10-02, desktop 1280x800, T-0135's five stands, on two published mirrors of
dev @ 1da76db5: the branch (`streets.js`, `terrain.js` as in this PR) and the base
(the same mirror with dev's `streets.js` and `terrain.js` copied back in). The
`light` rows were read before the road learned to keep its grids at `light`; at that
tier the branch now lays exactly dev's 106,891 street triangles (measured in Node:
`setDetail('light')` → 106,891, `setDetail('full')` → 150,524), so its delta is 0.

| tier | stand | base | branch | delta |
| --- | --- | ---: | ---: | ---: |
| full | the Sauganash at 26 m | 1,196,825 | 1,240,459 | +43,634 |
| full | Lake Street at Canal, east down the axis | 1,708,512 | 1,752,146 | +43,634 |
| full | the forks, from Wolf Point | 1,627,717 | 1,671,351 | +43,634 |
| full | the open aerial | 1,517,627 | 1,561,261 | +43,634 |
| full | Lake and Market | 1,453,311 | 1,496,945 | +43,634 |
| balanced | the Sauganash at 26 m | 1,104,732 | 1,148,366 | +43,634 |
| balanced | Lake Street at Canal, east down the axis | 1,475,633 | 1,519,267 | +43,634 |
| balanced | the forks, from Wolf Point | 1,415,337 | 1,458,971 | +43,634 |
| balanced | the open aerial | 1,347,191 | 1,390,825 | +43,634 |
| balanced | Lake and Market | 1,306,928 | 1,350,562 | +43,634 |

Draw calls are unchanged at every stand: the ridge adds triangles to the three street
meshes, not meshes.

The same +43,634 everywhere because the street layer is three town-wide meshes,
drawn whole. Where it comes from (Node, the committed heightfield): 1,392 of 6,937
panels still sag more than 15 mm under the ground's cell ridge after refinement, and
the 21 joint fans; laid on the cells they take 42,638 triangles where their grids took
25,832 (merged straight runs) plus the lone panels and fans. Tolerances tried before
settling, triangles town-wide (dev 106,891):

| sag tolerance | panels on the ridge | street triangles |
| ---: | ---: | ---: |
| 15 mm (shipped) | 1,392 | 150,524 |
| 22 mm | 940 | 138,437 |
| 30 mm | 656 | 133,326 |
| 45 mm | 359 | 124,515 |
| 100 mm | 58 | 113,498 |

Anything above 15 mm leaves the ground able to rise through a road by more than the
22 mm lift less the bake's 4 mm over the ridge, which is the artifact. Lifting the
grids instead of cutting them (no new triangles) was measured too and rejected: to
clear the ridge the lifted road floats more than 45 mm above it on 567 panels and
more than 0.3 m on 9.

New ceilings, by the T-0672 rule (worst stand + the tier's recorded absolute headroom,
rounded up to 5,000): `full` 1,752,146 + 18,059 → 1,775,000; `balanced`
1,519,267 + 16,806 → 1,540,000. `light` unchanged at 825,000.
