# T-1879 (package N18B of T-1837) — 1721 Prairie worked to the 1891 plate

T-1878 stood the house on K01 (`docs/RESEARCH/k01-1721-dexter-1878/`). This package solves the
picture's camera and builds the front's detail until the render from that camera shows the plate's
building. Liberty `L-k01-1721-dress-1879`.

## The pictures

| picture | phase | camera |
|---|---|---|
| 1891 Inland Architect plate (`a16-inland-1891-dexter-residence`) | Little's front, as 1904 | `data/reference_views/dexter_house_1721_prairie/inland_architect_plate.json` — **matches** |
| c. 1888 Glessner photograph (`a16-ghm-blog-1721-dexter-c1888`) | the frame house before 1889 | none: another phase |
| c. 1888 winter copy (`cgn-1721-dexter-winter-photo-copy`) | the same, before 1889 | none: another phase |
| Detroit print (`a16-pullman-det-4a08065`) | 1890-1901 | Pullman's camera; 1721 is at its edge behind trees |
| c. 1905 Clark negative (`a16-chm-clark-ichi-071912-dexter-c1905`) | 1904's | none yet: a 375 px contact thumbnail in a PDF, not in the image store |

## The camera

Fitted to 14 readings of the plan's corners and the two cornice lines (the solve field has them),
5.5 px RMS. The eye stands at the house's own grade, about 36 m out from the rear wall: the plate's
walk and lawn are raised over the roadway behind a kerb, so a tripod in the roadway stands about level
with the house's grade.

## What changed, read off the plate

- **Bows**: two lights a storey each, a blank pier at the middle (T-1878 had three).
- **Third floor**: a light over each side of each bow and a round-headed fanlight between them.
- **Balustrades**: round each bow's top, along the forward block's parapet, and on the recessed front
  after 1.5 m of solid parapet from its corner.
- **Shutters** at every light of the front but the fanlight; **iron guards** under the ground floor's
  bay lights, the centre one long enough that the three middle ones read as one run.
- **Stack** to 16.9 m; **north flank** one column: window, small oval light, slot.

## The kit

| option | where | what |
|---|---|---|
| `window_shutters` | K01 walls | louvred leaves beside the named storeys' lights |
| `bays[].storeys[].windows[].shutters` | K08 lights | the same, in the light's frame (bent round a bow) |
| `bays[].storeys[].windows[].guard` | K08 lights | stone slab and iron guard under the sill |
| `flat_balustrade` | K01 flat roof | the blocking course stopped at a plinth, balusters and a rail over a stretch |

All four are opt-in: every other K01, K12, K13 and K16 asset re-emitted byte-identical. The house's
web GLB is 1.58 MB (1.54 MB before); its master 49k triangles (38k), of which the shutters are 4.7k
(each slat one face, so a bow's bend does not split a boxed slat).
