# Web-to-Unreal parity tracker

Owner priority, 2026-09-20: improve the standalone app to the current web renderer's
quality, then streaming. This is a **work inventory**, not a completion receipt.
For every comparison, pin the same source SHA, scene date, terrain epoch and quality
preset. Update this matrix with exact layer/route coverage and links to receipts;
mark partial work partial. Refresh the inventory against current web code before
closing a slice, because the web app continues to change.

| Capability | Current native evidence / gap | Owner and next acceptance |
|---|---|---|
| Fresh Mac build and downloadable preview | T-1464 packaged terrain/structures; first GitHub prerelease published; manual rebuild works | T-1472: latest validated snapshot, on-demand build/test/release, failure retention |
| Scheduled source assets and incremental imports | Fresh checkout build exists; versioned bundle and incremental retirement contract unfinished | T-1357 / T-1358, shared export policy T-0252 |
| Structure placement and terrain contact | Garden yaw corrected; owner reports sinking buildings; lowest-footprint anchor is not proof of correct floor/door fit | T-1473: measured systemic fix, before/after views and normal walking |
| Roads, alleys, frontage/plank walks, bridge and wharf approaches | Web procedural layers absent; core GLB structures alone do not supply the network | Existing T-1360: first complete corridor, then a bounded remaining-network successor |
| Trees, shrubs, grasses/reeds and other current flora | Web procedural flora absent | T-1474: shared deterministic instances, grounded placement, materials/LOD/performance on a corridor, then remaining coverage |
| First-person input, map, search and place inspection | WASD/mouse/jump/reset/quit exist; map/search/cards absent | T-1475: usable packaged find/select/inspect/return-to-walk flow with input focus and runtime provenance |
| Confidence, citations and review constraints | Source sidecars retained, native confidence display absent | T-1475 supplies initial cards; T-1356 keeps complete confidence visualization and review-aware interaction pending |
| Year/epoch switching and historical continuity | Native preview is fixed to 1835 | T-1356: bounded successor after navigation/data contract; date-specific assets, terrain, spawn and preserved review constraints |
| Fences/enclosures, yards/wells, boats/wagons/camps/signs and other props | Some committed structure GLBs present; procedural web props/enclosures absent | T-1356 inventory; bounded successors after shared exports, one layer/route at a time |
| Fauna and other non-human scene life | Web fauna module exists; native coverage not established | T-1356: inventory source-supported animals and behavior, export/instance/performance slice under existing historical constraints |
| Research and community data views | Native research UI absent; web includes businesses, residents, census, population, evidence and liberties modules | T-1475 inventories entry points; T-1356 retains bounded data-card/view successors with runtime-safe provenance, including Native/Métis and Black resident records under existing review rules; no human figures |
| Water, ground/building materials, atmosphere and lighting | Basic imported materials/daylight; matched visual parity unverified | T-1356 successors with same-view comparisons and rights/source evidence |
| Settings, accessibility and other current web interactions | Small native controls overlay only | T-1475 inventories current controls; T-1356 keeps remaining input/UI flows and supported presets pending |
| Full-town collision, scale and performance | Short packaged spawn-route check only | T-1358 plus each layer ticket: named routes, normal collision, frame/memory measurements; no blanket claim |
| Windows and broader Mac distribution | Apple Silicon development build only, locally signed | T-1356 tracks Windows qualified-runner packaging and Mac signing/notarization/second-machine qualification as separate future slices |
| Streaming and server handoff | Not established by native packaging | T-1359 corruption diagnosis, T-1361 approved host/deployment/rollback after native priorities |

A slice's closing receipt includes source/bundle hashes, layer/feature ids, known
omissions, before/after or matched-view images, normal route/input checks, target
hardware/preset, performance where affected, and reproducible build instructions.
No human figures are authorized; preserve all historical confidence, source rights
and Indigenous-review constraints. No generic remote web worker can close a row
requiring Unreal execution merely by generating data or passing schema tests.

The four owner-requested new tickets are explicitly queued now. Additional layer
expansion stays under T-1356 and is split into one bounded successor when its
predecessor establishes the contract. Do not drop the remaining matrix rows or close
overall parity after the first road, flora corridor or search screen.

Inventory starting points in `renderers/web/js/`: `navigation.js`, `goto.js`, `travel.js`, `route.js`, `hud.js`, `popup.js`, `confidence.js`, `citations.js`, `businesses.js`, `residents.js`, `census.js`, `population.js`, `evidence.js`, `liberties.js`, `flora.js`, `trees.js`, `plants.js`, `fauna.js`, `streets.js`, `frontage.js`, `wharves.js`, `enclosures.js`, `yards.js`, `wells.js`, `boats.js`, `signage.js`, `terrain.js`, and `world.js`. A module name is an inventory lead, not evidence that its whole behavior is enabled in the selected web scene.
