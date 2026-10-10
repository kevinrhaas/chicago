# T-2289 — K02 stone on the 1808 Prairie exemplar

Piece 2 of T-1844 (package K02 of the T-1837 Prairie Avenue 1904 programme). The stone library
(T-2288, `assets/textures/prairie_1904_stone/`, profiles in
`data/components/prairie_1904/k02_stone_profiles.json`) is now built to: the street front of the
1808 Prairie frontage (`data/structures/keith_house_1808_prairie.json`,
`generators/archetypes/k01_frontage.py`) is laid as coursed ashlar from it instead of drawn as one
flat face. Every part is reconstructed and says so (`docs/LIBERTIES.md` L-k02-1808-stone-2289).

## What was built, and from what

The record names four things (`form.stone_front`): the walling fabric and its dressing
(`limestone_lemont`, `rock_faced`), the trim fabric (`dressed_trim`), how many courses the
rusticated base runs (2) and which corners are bonded (`south`). Everything a stone is laid to is the
profile's, resolved by `k01_frontage_params._k02` into the mesh's input hash and refused outside it.

| component | built as | from the profile |
|---|---|---|
| `k01.wall.stone_course` (33) | 30 courses of walling, 0.20-0.41 m, struck on the sills, heads, arch tops and belts and divided equally between them; the two belts and a 0.07 m band under the soffit in dressed trim | `course_height_m` [0.2, 0.41], `block_length_m` [0.4, 1.2] |
| stones (487) | each its own cell: arris = cell less half a joint each side, recessed to the mortar; face = arris less the bevel; a rock face rises 0-25 mm to a wandering crown over an inner ring of points at their own heights, so no two stones facet alike | joint 10 mm, recess 5 mm, bevel 8 mm, `rock_face_projection_m` [0, 0.025] |
| nonrepeating courses | every stone samples its own window of the 1.2 m tile (offset from its seed on both axes, mirrored in u on the seed's top bit); joints kept 0.1 m off the course below's where twelve draws allow | `common.nonrepeat` |
| mortar recess | the mortar fills every stone's whole cell at the recess, so every joint has a floor; Glessner's sandy lime | `common.mortar` |
| sparse chipped edges | 92 corners, drawn at 1.2 a metre of arris, kept where the chip's floor stays in front of the joint's | `arris.chips_per_m`, `chip_length_m`, `chip_depth_m` |
| `k01.wall.rusticated_base` (2) | two 0.41 m courses from grade, horizontal joints opened to 18 mm channels 12 mm deep, a ledge closing their mortar floor to the coping's | `rusticated_base` channel 0.018 x 0.012, courses [1, 2] |
| `k01.wall.coping` (1) | 0.23 m of dressed trim over the base, its top falling 1:8 from the wall line to a nose 40 mm past the rock faces, a 10 mm drip groove under it; its top is the area lights' head line | `dressed_trim.coping` |
| `k01.wall.corner_bond` (32) | quoins on the south return, alternately 0.48-0.60 m and 0.25-0.30 m (to the cm), cut out of the brick, against a front corner stone short and long in turn; steps close each one's mortar floor to the brick | `corner_bond.return_m` [0.25, 0.6] |
| `k01.opening.flat_arch` (11) | a flat arch over every front opening, 0.12 m seats, voussoirs about 0.2 m whose joints radiate from a 12 degree splay, the keystone 20 mm prouder; each stone's u along its own radial joint | `common.bed_orientation` |
| `k01.opening.slip_sill` (10) | one dressed piece under each front window and area light, 0.10 m deep, 0.06 m proud | dressed trim joint and bevel |

The brick side and rear walls keep Glessner's brick (laying K03's brick library is K03's work);
their sills and lintels now wear the K02 dressed trim, the fabric the profiles give a sill or lintel.

**Where it departs from its profile:** chips are kept only where their floor stays in front of the
joint's 5 mm floor (92 of those drawn), and only at corners; dressed trim's 1-3 mm chips are not built;
trim set in the walling takes its 5 mm recess, not trim's own 1 mm; the north corner is not bonded,
standing 0.02 m from Glessner.

## The contract measure (`keith_house_1808_prairie.measure.json`)

Every verdict ok, on both tiers: scale drift, origin, **0 coincident faces, 0 degenerate**, metric UVs
(`rough_stone_trim` on `limestone_lemont` 1.0000 full / 1.0188 web, `limestone_trim` on
`dressed_trim` 1.0000 / 1.0065, `mortar` 1.0000 / 1.0000). `tools/k01_contract.mjs` now reads the K02
library's tiles beside Glessner's and K04's, so the stone is held to the same metric-UV rule as the
rest. Every face of every stone is mapped in its own plane, so a bevel, a sill top or a coping's
weathering is metres over the tile like the face it leaves.

| tier | bytes | triangles | primitives | images | texture bytes | GPU (RGBA8 + mips) |
|---|---|---|---|---|---|---|
| T-2293 full | 2,291,684 | 5,305 | 13 | 6 | 1,760,554 | 50.3 MB |
| T-2293 web | 1,031,380 | 5,305 | 13 | 6 | 921,720 | 50.3 MB |
| **T-2289 full** | 4,177,460 | 16,753 | 14 | 11 | 2,552,664 | 78.3 MB |
| **T-2289 web** | 1,826,308 | 16,753 | 14 | 11 | 1,387,339 | 78.3 MB |

The stone adds 11,448 triangles (8,180 walling, 1,636 trim, 1,142 mortar on this house in all), one
primitive (the mortar) and five images: the Lemont and dressed-trim web base colour and OpenGL
normal maps, and Glessner's mortar. The two K02 fabrics bind their normal maps, the relief a raking
sun reads on a rock face.

## In the app

The published `/1904/` app, normal boot, the stands in the assembly's own footprint frame
(`QA_K02=1 node tools/qa_k01_t2266.mjs`, run in parts with `QA_STANDS=`): front, oblique, rear and
roof, then the front, a flat arch and the rusticated base's south corner at 3-9 m, each in a **raking**
sun (the scene's own sun moved to 25 degrees up, 10 degrees off the front's plane from the south) and
in **diffuse** light (the sun off; sky and environment only).

| viewport | detail | load to ready | page errors | failed requests | draws per stand | within budget |
|---|---|---|---|---|---|---|
| 1280x800 | full | 18.1-18.7 s | 0 | 0 | 72-74 | every stand |
| 390x780 | light | 10.0-10.3 s | 0 | 0 | 70-71 | every stand |

Frame times are this machine's software GL (12 renders each waited on, median), a relative reading:
desktop 3.0-7.2 s, mobile 0.8-1.6 s. Each `browser-validation-<viewport>-<first stand>.json` holds a
part's stands, triangles, draws and frame time; the captures are `<viewport>-<stand>.jpg`.

**What the captures show.** `desktop-raking-front.jpg`: the courses, the belts and sills standing off
the rough wall, the quoins long and short on the brick return. `desktop-raking-arch.jpg` /
`desktop-diffuse-arch.jpg`: one flat arch at 4 m, voussoir joints radiating, the keystone proud, the
belt above; the rock faces' facets read in the raking sun and go quiet in diffuse light, where the
trim's smoother, lower-roughness face separates from the walling by tone alone.
`desktop-raking-base.jpg`: the two channel-jointed base courses, the coping's nose and shadow, the
area lights' slip sills and arches, the quoins' returns into the brick.
