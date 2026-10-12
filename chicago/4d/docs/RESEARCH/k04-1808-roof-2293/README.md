# T-2293 — the first K04 roof, on the 1808 Prairie exemplar

Piece 2 of T-1846 (package K04 of the T-1837 Prairie Avenue 1904 programme). The roof library
(T-2292, `assets/textures/prairie_1904_roofs/`, profiles in `data/components/prairie_1904/k04_roofs.json`)
is now built to: the 1808 Prairie frontage (`data/structures/keith_house_1808_prairie.json`,
`generators/archetypes/k01_frontage.py`) wears it. Every part is reconstructed and says so
(`docs/LIBERTIES.md` L-k04-1808-roof-2293).

## What was built, and from what

| part | built as | from |
|---|---|---|
| covering | Pennsylvania slate on all four hip planes; `TEXCOORD_0` = metres / tile, the first butt put on the eave by the map's own course phase, never scaled | `slate_pennsylvania` (tile 2.032 x 1.727 m) |
| cut edge | the doubled eave course's 12.8 mm butt and the underside of the 50 mm the slates run past the fascia | `cut_edges.eave`, `slate_exposure` |
| hip and ridge caps | a copper roll (32 mm) on each hip and the ridge, 100 mm flanges dressed over the courses, trimmed to the eave line | `hip_ridge_caps.copper_ridge_roll`, `copper_sheet` |
| dormer | a gabled dormer centred on the street hip: dressed-stone face with a K01 `sash_flat` cut through it (`k01.wall.dormer_face`), slated cheeks and roof, bargeboards and verge soffits, copper ridge roll (`k01.roof.dormer_gable`) | record `form.dormer` |
| valleys | open copper valleys, 100 mm exposed at the top widening 10 mm a metre, with a 25 mm crimped rib | `valley_flashing` |
| apron and steps | a copper apron lapped 100 mm over the course below the face with a 100 mm upstand; step flashing at each cheek, a 100 mm leg and upstand (one strip a cheek, not one a course: a liberty) | `dormer_apron` |
| gutter | a 5 in half-round copper gutter round the whole eave, mitred at the corners, falling 0.5 % from each run's middle to its outlets | `gutter.half_round`, `gutter.fall` |
| brackets | wrought-iron hangers at 30 in: a band under the gutter and a leg up the fascia, clear of the outlets | `gutter.bracket` |
| outlets, pipes, shoes | five outlets, each a swan neck back under the soffit to a 3.5 in round copper pipe strapped every 1.8 m, ending in a 45 degree shoe whose lowest lip is 50 mm over a splash stone at grade | `gutter.outlet`, `downpipe` |

The record moved twice to take the library honestly: the roof is 45 degrees (the library's slate is
cut for a 3 in headlap, which the profile allows from 45 degrees; at 40 it asks 4 in), and the eave
is 0.38 m so the soffit stays clear of the top storey's lintels at that pitch.
`k01_frontage_params` refuses a slate cut for less lap than the pitch needs, a restricted fabric as a
main covering, a pipe on the north wall and an empty pipe list.

**Where it departs from its profile:** no pipe can stand on the north wall (it closes the Glessner
court 0.02 m off its face), so the north gutter runs 20.5 m between its corner outlets against the
profile's 12 m, falling both ways from its middle.

## The contract measure (`keith_house_1808_prairie.measure.json`)

Every verdict ok, on both tiers: scale drift, origin, **0 coincident faces**, metric UVs
(`slate_covering` 1.0000 x tile on both tiers, `k04_copper_sheet` 1.0000 full / 0.9929 web).
`tools/k01_contract.mjs` now reads the K04 library's tiles beside Glessner's, so the slate and
copper are held to the same metric-UV rule as the walls.

| tier | bytes | triangles | primitives | images | texture bytes | GPU (RGBA8 + mips) |
|---|---|---|---|---|---|---|
| full, T-2266 | 1,864,120 | 2,218 | 10 | 2 | 1,671,910 | 44.7 MB |
| **full, T-2293** | 2,291,684 | 5,305 | 13 | 6 | 1,760,554 | 50.3 MB |
| web, T-2266 | 892,916 | 2,218 | 10 | 2 | 839,338 | 44.7 MB |
| **web, T-2293** | 1,031,380 | 5,305 | 13 | 6 | 921,720 | 50.3 MB |

The four new images are the slate's and copper's 512 px base colour and normal maps (about 88 KB
together); the GPU figure is dominated, before and after, by the Glessner library's 2048 px brick and
limestone maps the walls already carried.

## In the published app (`browser-validation-desktop.json`, `browser-validation-mobile.json`)

`QA_K04=1 node tools/qa_k01_t2266.mjs` — the T-2266 stands plus a dormer view, a grazing look along
the south-east eave and a downpipe's shoe, in the actual published `/1904/` app: desktop 1280x800 at
full detail, mobile 390x780 at light. Zero page errors, zero failed requests, every stand within the
detail tier's budget.

| stand | desktop draws | desktop tris | mobile draws | mobile tris |
|---|---|---|---|---|
| street-eye | 66 (62) | 2,484,956 | 65 (61) | 454,283 |
| oblique | 67 (63) | 2,487,241 | 64 (60) | 455,039 |
| rear | 68 (64) | 2,499,184 | 64 (60) | 454,667 |
| roof | 67 (63) | 2,488,276 | 65 (61) | 454,777 |
| courtyard-join | 73 (69) | 2,510,970 | 64 (60) | 454,852 |
| dormer | 66 | 2,484,647 | 65 | 454,597 |
| eave-grazing | 67 | 2,486,558 | 65 | 455,621 |
| downpipe-shoe | 66 | 2,485,385 | 65 | 455,102 |

Bracketed: the same stand under T-2266. The roof costs four draw calls at every stand (slate is now
textured, and copper, iron and the dormer's stone are three new materials). Scene load to ready was
14.4 s desktop and 7.4 s mobile on this runner's software GL (T-2266: 17.6 s and 9.6 s), and the
median frame times in the JSON are relative readings on that same software GL, not device claims.

## Seen

Slate courses read at true size from the street and at a grazing angle along the eave with no
oversized slates, no baked highlight and no seam zipper; the hip rolls and valleys read as metal
against the slate; every pipe reaches its splash stone (`*-downpipe-shoe.jpg`).
