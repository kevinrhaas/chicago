# T-3566 — 1721 Prairie: the 1863 frame Dexter house behind Little's brick front

The owner, 2026-11-12 (project thread, after a meeting with Bill Tyre): *"on 1721 prairie there is a
frame house to the rear of the building that should be standing you should be able to see images of
it"*. Liberty `L-k01-1721-frame-house-3566`.

## The house in its sources

| source | date | what it says of the frame house |
|---|---|---|
| Robinson's atlas, plate 10 (`robinson_1886_chicago_plate_10`; library `cgn-1721-robinson-1886`) | 1886 | lot B (60.2 ft): a long **yellow (frame)** house on the north lot line, set back about 34 ft and running back about 100 ft, stepped on its south side |
| Inter Ocean, 1887 (quoted in the library) | 1887 | "tastefully constructed frame house" |
| George Glessner's photograph (`a16-ghm-blog-1721-dexter-c1888`) | c. 1888 | the house whole before Little: two storeys, central gable, bracketed eaves, cupola, tall chimneys, shutters |
| Inland Architect plate (`inland_architect_1891_06_dexter_plate`) | 1891 | Little's brick front on the street line; at the left rear, behind its north flank, a **clapboarded** block with a two-storey bay window under a balustrade and a steep gable |
| Detroit Publishing print (`loc_det_4a08065_pullman_residence`) | 1893-1901 | at its left edge, between Little's pale front and the Pullman house, a two-storey **clapboarded** house under a slated roof with tall chimneys and a columned porch on its south side |
| Chicago Tribune, 28 Nov. 1901 (library `npo-1721-tribune-1901-11-28-dexter-residence-bought-by-spalding`) | 1901 | the sale to Spalding required the street-line brick front rebuilt or **moved back** to the 20 ft building line |
| Sanborn 1911, vol. 3 sheet 20 (`sanborn_1911_chicago_v3_sheet_20`) | 1911 | the bowed 3B brick block 9.7 m back from the street; behind it on the north line a "2B" range 19.9 x 6.2 m coloured **brick**, one-storey frame pieces at its east end |

## The reading

The 1911 range stands exactly where Robinson's frame house ran: on the north lot line, from behind the
set-back brick block to about 41 m from the street. The pictures before the move show that part of the
lot as a clapboarded house. Nothing read records the frame house pulled down, or a brick range built,
between 1902 and 1911. So the range is read as the rear of the frame house, left standing when Little's
front was set back onto its front part, and the 1911 sheet's brick colouring is taken as the sheet's
error or a later refacing, not as the 1904 fabric. This is the disagreement the record carries; the
three pictures and the 1886 plate outweigh the one map, and the owner asked for it.

What the move took is not built: the print's columned porch and two tallest chimneys, and the plate's
north bay window and cross gable, stood on the frame house's front part, directly behind the 1889 front
on the street line, which is where the brick block stands from 1902.

## The build

`dexter_house_1721_prairie` `rear_wings`: `rear_wing` becomes `fabric: frame` with `clapboard`, a 45
degree slated gable to the rear and two brick stacks; `rear_frame_piece` takes the same clapboards.
The K01 kit learned `rear_wings[].clapboard` (`generators/archetypes/k01_frontage.py` `clapboards`):
each board a sloped face from its proud butt to the lap above and a lip under the butt, stopped at the
openings' casings, between corner boards, over a stone water table, in one flat paint
(`wing_clapboard`). No other K01 record names it; `k01_emit.py --check` holds every other house's bytes.

## The pictures

- `data/reference_views/dexter_house_1721_prairie/detroit_det_4a08065.json` — new: the Pullman house's
  solved camera on the print carried into this house's frame. **matches**.
- `inland_architect_plate.json` — re-rendered. **matches**.
- The coach house's view of the print re-rendered; still hidden. **matches**.
