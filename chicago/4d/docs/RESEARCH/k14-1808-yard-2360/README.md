# K14 on 1808 Prairie's yard: lawn, front walk and side service walk (T-2360)

Piece 3 of T-2325 (package K14 of the T-1837 Prairie programme). T-2324 built the condition kit;
its ground layers return weights and leave how a yard shows them to the yard. This is the first
yard that does: the ground inside 1808 Prairie's K11 boundary (T-2319), aged at the house's own
age on 1904-07-01.

## Acceptance (stated before work)

1. The ground inside the K11 boundary is built, from the record's `yard` attribute, as surfaces of
   the house's own asset: a lawn over the front yard, a front walk from the stoop's foot through
   the entrance pair to the public walk, and a service walk from the side gate down the passage.
2. Both of the kit's ground layers are carried, read off the kit, not copied: `grass_edge` as a
   bare strip at the street front's wall foot (and round its bay), `path_wear` along the centre of
   each walk by its use. The age is the house's: `yard.built` must equal its phase's year.
3. Nothing in the yard sits under the drawn terrain, nothing is coincident, and the K01 contract's
   verdicts all stay `ok`.
4. Verified in the published `/1904/` app at 1280x800 (full) and 390x780 (light), with zero page
   errors and every stand within budget, and the costs recorded.
5. One liberty, `L-k14-1808-yard-2360`, says which parts were made up (all of them).

## What is built

`generators/archetypes/k14_yard.py`, called by `k01_frontage.build` after the K11 boundary,
reading the boundary's built geometry (`a.boundary`: the fence line, the stoop's foot, the
entrance and side-gate openings) so the yard is laid on the same lines the ironwork stands on.

| surface | where | material | kit layer |
|---|---|---|---|
| lawn | street front (and the bay's foot) to the curb's house face, s 0 to the north lot line (10.225) | `yard_turf`, Glessner's turf map | — |
| bare strip | along the street front's wall foot and round the bay | `yard_earth`, the K14 study's earth | `grass_edge` at age 0.45: 0.14 m, wobbling 0.02 m; measured square to the wall, so 0.12-0.25 m in plan round the bay's ends |
| under the stoop | the open stair's plan, s 7.2-9.6, u 18-21.6 | `yard_earth` | — |
| front walk | u 21.6 (the stoop's foot) to 22.75 (the public walk), s 7.76-9.04 | two flags of `stoop_stone`, 0.57 m each, 10 mm joint, 0.025 m proud of the lawn | `path_wear` front_walk: 0.975 on the centre line at this age (0.9 at full wear) |
| service walk | u 0 (the rear corner) to 22.75, between the boundary wall's north face (s -1.056) and the house's south wall (s 0); through the side gate, s -0.926 to 0 | `yard_cinder`, Glessner's gravel map darkened | `path_wear` service_walk: about 0.91 on the centre line at this age (0.78 at full wear, the K14 study's cinder) |

The wear is a `_TONE` per vertex (buildings.js `applyPieceTone`), so it darkens the surface it is on
and keeps its hue; `to_glb` now writes `_TONE` for any prim whose tones were laid point by point.
The bare strip is a surface of its own because earth beside turf is a change of material, which a
grey multiplier cannot draw.

**The lift.** The first bake laid the ground at Glessner's courtyard lift, 0.015 m, and the
published app showed the cinder only as a broken band down the passage. The renderer beds a
building on the LOWEST terrain under its bounds (`buildings.js` `groundUnder`); measured in the app,
1808's bed is 0.016 m under its origin's terrain and the terrain across the yard rises up to
0.018 m over the bed (at u 0, s -1.06). The ground surfaces now stand 0.035 m over grade, 0.017 m
clear of the highest terrain, and the flags 0.06 m.

## Verification

`node tools/qa_k14_t2360.mjs` (after `tools/publish.sh`), `QA_VIEWPORT=desktop|mobile`: the actual
published `/1904/` app, normal boot, six fixed stands in the house's own frame (front, oblique,
front walk, the bay's edge, down the passage, the passage's end at the rear corner). Both
viewports PASS: 0 page errors, 0 failed requests, every stand within budget. The readings and the
twelve screenshots are in this folder (`browser-validation-*.json`, `desktop-*.jpg`, `mobile-*.jpg`).

| viewport | load to ready | draw calls at the stands | triangles at the stands |
|---|---|---|---|
| desktop 1280x800, full | 20.2 s | 118-154 | 3.00-3.23 M |
| mobile 390x780, light | 12.3 s | 83-86 | 0.70-0.73 M |

(Software GL on the runner: frame times in the JSON are relative readings, not device claims.)

`tools/k01_contract.mjs --measure-asset keith_house_1808_prairie`: origin, coincident faces,
metric UV, scale drift all `ok`.

## Costs (the house's asset, before -> after; "before" is dev with T-2358's weathered walls)

| | full | web |
|---|---|---|
| bytes | 7,840,196 -> 8,763,700 (+924 KB) | 2,175,620 -> 2,471,860 (+296 KB) |
| draw primitives / materials | 28 -> 31 | 28 -> 31 |
| triangles | 67,312 -> 69,628 (+2,316) | same |
| vertices | 141,629 -> 148,563 | 110,909 -> 112,442 |
| images | 13 -> 15 (turf, gravel) | |
| GPU texture memory (RGBA8 + mips) | 64.2 -> 75.4 MB | |

Of the 2,316 triangles: lawn 186, earth 212, flags 86, cinder 1,832 (the passage is 22.75 m of
0.2 m rows, so its wear breaks up along it). The front walk takes no slot: it is the stoop's stone.

## Still open

- **The drawn sidewalk stands beyond a grass parkway.** The flags end at the lot's public-walk line
  (u 22.75, the record's `front_yard_m`); the 1904 street draws its sidewalk further out, so a
  strip of parkway grass lies between them. Carrying the walk across it is the street's question,
  not the lot's.
- **The service walk stops at the rear corner** (u 0). The rear yard and the way on to the coach
  house on the alley (T-1935's) are not laid.
- **The north side, against Glessner, is open**, as the K11 boundary left it (T-1944's).
- The bare strip runs only where the lawn meets the house's front and its bay; the stoop's cheeks,
  the piers and the curb meet the lawn with no strip.
- Every surface and number is reconstructed (`L-k14-1808-yard-2360`); a photograph of 1808's front,
  or of any Prairie Avenue front yard of the 1890s, replaces what it shows.
