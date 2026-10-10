# T-2289 — K02 stone on the 1808 Prairie exemplar

Piece 2 of T-1844 (package K02 of the T-1837 Prairie programme). Piece 1, T-2288, built the stone
library (`assets/textures/prairie_1904_stone/`, `data/components/prairie_1904/k02_stone_profiles.json`).
This piece lays the 1808 Prairie street front from it. It is RECONSTRUCTED throughout
(`docs/LIBERTIES.md` L-k02-1808-stone-2289).

## What is built, and what is left to the other kits

The front had already been dressed by four kits when the stone was laid. They keep what they build,
and the stone is laid round them:

| on the front | built by |
|---|---|
| rock-faced walling, 35 courses, stones 0.40-1.20 m | **K02** (`k01.wall.stone_course`) |
| rusticated base, two 0.41 m channel-jointed courses | **K02** (`k01.wall.rusticated_base`) |
| weathered coping over the base, its top on the area lights' heads | **K02** (`k01.wall.coping`) |
| two belts, 0.05 m proud | **K02** (`k01.wall.stone_course`, kind `belt`) |
| quoins on the south return, long and short | **K02** (`k01.wall.corner_bond`, 31) |
| flat arches over the area light and the three third-floor windows | **K02** (`k01.opening.flat_arch`, 4) |
| every window sill | K06 (T-2298) |
| principal-floor surround and apron, second-floor hoods, ringed entrance | K09 (T-2310) |
| the stoop | K07 (T-2304) |
| the curved bow at the south corner | K08 (T-2308) |

**How the two meet.** Each kit notes the extent of every piece it seats on the wall
(`Assembly.seat`: the points at or proud of the face, in the wall's own frame). The front is laid
after them, and any stone whose cell meets a seat (widened by a joint and an arris, 0.023 m) is laid
dressed: the trim fabric, flush with the wall line, no rock face and no chip, and a belt not proud.
So a K06 sill, a K09 console or colonnette and the K08 bow's junction all stand on a plane face; a
rock face never buries a foot. A seat's edge cuts a course unless it falls within 0.08 m of a harder
edge, so no sliver stone is laid.

## Measured

`node tools/k01_contract.mjs --measure-asset keith_house_1808_prairie` — every verdict ok on both tiers.

| | before (dev) | T-2289 |
|---|---|---|
| triangles | 30,828 | 40,418 |
| primitives | 25 | 26 (the mortar) |
| full GLB | 3,956 KB | 5,626 KB |
| web GLB | 1,223 KB | 1,941 KB |
| coincident / degenerate faces | 0 / 0 | 0 / 0 |
| metric UV x tile, Lemont / dressed trim / mortar | — | 1.000 / 1.000 / 1.000 full, 0.998 / 0.997 / 1.000 web |

214 rock-faced stones and 259 dressed ones (most of the dressed are behind the bow, where nothing
sees them); 47 chips survive the joint-floor rule, all at corners.

## In the app

`QA_K02=1 node tools/qa_k01_t2266.mjs` against the published `/1904/` app, desktop 1280x800 at full
detail and mobile 390x780 at light: zero page errors, zero failed requests, every stand within
budget at 75-81 draw calls. Raking stands put the scene's sun 25 degrees up and 10 degrees off the
front's plane; diffuse stands turn the sun off. The arch and base stands were re-aimed for this
rebuild (the third floor's middle flat arch, and the area light beside the stoop), because the K08
bow now stands where they used to look.

- `desktop-raking-front.jpg`, `desktop-diffuse-front.jpg`, `desktop-oblique.jpg`
- `desktop-raking-arch.jpg`, `desktop-diffuse-arch.jpg`
- `desktop-raking-base.jpg`, `desktop-diffuse-base.jpg`
- `mobile-raking-front.jpg`, `mobile-raking-arch.jpg`, `mobile-raking-base.jpg`,
  `mobile-street-eye.jpg`, `mobile-oblique.jpg`, `mobile-diffuse-front.jpg`

## Not done

- The dressed trim's 1-3 mm chips (below the 1 mm measure grid).
- Trim in the walling takes the walling's 5 mm recess, not its own 1 mm.
- A dressed seat runs a whole course high, so the smooth stone round a sill or the apron is deeper
  than the piece it carries.
- The K08 bow keeps Glessner's limestone slot; laying it in Lemont is K08's own question.
- The stone itself: the register reads "rock-faced" and names no stone.
