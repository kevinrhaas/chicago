# T-1805 — west roof and sidewalk repair

Owner report 2026-10-01: the stable gable incorrectly spans the entire north face, the intersecting north roof cuts across its loft opening, and a sidewalk slab projects at a wall corner. Supplied screenshots are compared with the already catalogued public-domain HABS photographs 1 and 15.

## Checkpoint 1 — work in progress

- Ticket filed and claimed in chicago-tickets; branch steward/glessner-west-roof-repair.
- Preserve the W 141 carriage/loft/pigeon axis. Return the north gable to z 23.1 ft at W 125.75 and 156.25, leaving a 5 ft ordinary eave to the alley. These are photographic proportions, approximately ±1 ft, not surveyed dimensions.
- One joined roof envelope replaces the overlapping north roof inside the stable. The hidden transition back to the retained rear stable profile is reconstructed; no source is represented as a measured roof plan.
- Full and light use the same range builder. The west wall follows the crossing roof instead of projecting above its lowered street corner.
- First full bake completed; final bake and render review are running. The first check correctly refuses the old recovery package after the mesh changed. Do not merge this checkpoint: derivatives, package, sidecars, sidewalk repair and final gates are still outstanding.

Recovery commands, from chicago/4d:

1. Pinned Blender: generators/build.py -- --only glessner_house --no-bake.
2. tools/web_derivatives.sh --only glessner_house__as_built_1887.glb (also rebuilds light and repacks canonical outputs).
3. Regenerate older-version derivatives if their masters changed; compile sidecars.
4. Inspect street-level/elevated north and northwest views in full/light, and the reported sidewalk corner.
5. Run check.sh, published desktop/mobile smoke and preflight; only then merge to dev.

Production is not authorized by this request. Dev is the integration target.

## Checkpoint 2 — source correction ready; validation in progress

- Actual GLB review confirms the centered street gable, ordinary eave return and clear loft opening. The alley review caught a remaining floating cornice; its north end now stops at the intersecting range, and the full master has been rebuilt.
- Reduced roof sampling keeps the shared light geometry within the existing 200,000-triangle limit (196,687 before the final cornice trim); the limit is unchanged. The first checkpoint's CI bake stopped on that limit, as expected before this correction.
- Street surfaces already stand 30–60 mm above terrain. Remove their large slope-dependent depth pull, which can draw sidewalk pixels through walls at grazing views; retain a one-unit constant bias. Browser visual verification remains outstanding.
- Existing stone/aperture/glass clipping fixtures pass. Final web derivatives, recovery package, full gate and published desktop/mobile smoke remain outstanding. Local Chromium cannot launch because the execution sandbox refuses its socket; use the existing GitHub bake/smoke workflow for the required browser gate.
- The full source checkpoint is pushed separately from generated assets, at the owner's explicit request for recoverable progress. Do not merge this checkpoint until those gates are green.

## Recovery checkpoint — 2026-10-01

The owner requested continuation after the original session stopped reporting. The last process was no longer running. Recovered the pushed source checkpoint e643f977 and the subsequent local bake, shortened cornice, sidewalk change and final render outputs. All recovered assets were saved on the same branch in 8a77dbeb.

- The final full master is SHA-256 `5a919b27e0ba0402745450a2d0ebc107cf20273e8c7a4ae4d231ead65588a4ef`. Its full/light web derivatives and split recovery package are rebuilt and checked. Light has 196,687 triangles against the unchanged 200,000 ceiling. Older-version derivatives were refreshed to match their rebaked masters.
- Full north and northwest review images are beside this note. A fresh light northwest render also confirms the gable return and clear loft opening. The final alley cornice ends at the intersecting range. These are actual model renders, not generated illustrations.
- Staleness validation passes with no errors (262 existing warnings); stone/aperture/glass clipping fixtures pass. The first recovered source gate passed 715 of 716 checks. Its sole failure was the external split of T-1779: all three boarding-house order-book owners now follow its open remainder T-1810, matching the sweep already proposed in PR #229. The book was regenerated without changing its allocations.
- Integrated dev at 4ca01605 and restamped the repair changelog. Final preflight and published desktop/mobile browser checks are the remaining merge gates; their results belong in the repair PR. Local Chromium is refused by the environment, so browser validation uses the existing GitHub smoke workflow.

## Integration validation — PR #230

The 717-step source gate passed on 3be47a42, and both portrait GLB variants were
reviewed from north, northwest and alley views. Published mobile parts 10–13
passed, including Glessner loading, placement, picking and its 1904 street grid,
with zero page errors. Both viewports passed parts 7–9. The subsequent dev merge
at 13af98aa adds five 1835 boarding-house models; local preflight passed again.
Remaining run receipts are recorded in PR #230 before merge.

The desktop parts 1–2 run found a pre-existing yard census error blocking this
visible repair: it counted 64 source chunks plus four lazy far-merge cache meshes
as 68 chunks. Far batches live beside the originals and reuse their geometry;
they are not extra yard objects. The frontage census already excludes those
tagged caches. Apply that same distinction to yard geometry, retain the 64-chunk
ceiling, require agreement with the layer's own chunk census, and verify that
excluded meshes are named yard-far-merge. Both source chunks and cached batches
must still share one material and carry bounding spheres. No yard geometry or
rendering setting changes. Rerun parts 1–2 with their preceding camera history,
plus part 5's unchanged zero-extra-triangle far-merge and rendering-budget gates.

Dev integration at 21acac92 added the landing camps and registered their archetype
in the shared emitter, invalidating the input fingerprints of this branch's four
Glessner masters. Rebuilt all four with pinned Blender 4.5.3 and regenerated their
web derivatives. Every master and the canonical full/light web files reproduced
byte-for-byte; the recovery archive is unchanged. Staleness is again zero errors.
The repair's desktop 1904 loading, placement, picking and street-grid checks also
passed in run 36888731661. That wider run separately found a 3.9 px sward-boundary
reading against the unchanged 4 px floor in part 11; the prior unfiltered receipt
has the identical ground reaches but an 8.2 px spread. An isolated dev comparison
and explicit buffer/FOV/eye-height diagnostics are checking the measurement state.
No grass parameter or assertion threshold has been changed.

### Development gate repairs

The isolated dev run 36895681173 reproduced the same grass failure and found a
second failure from the newly merged camps: their placement anchor was 0.005 m
above the terrain at the declared origin. Include that origin in `groundUnder`'s
minimum alongside the mesh-bound samples. A sparse model's bounds need not reach
its declared origin; all existing samples remain in the minimum. The original
no-floating-anchor assertion is unchanged.

For the grass, increase only the full-detail mid-ring's world-anchored fringe
from 3 m to 3.5 m. This addresses the actual near-circular edge at the desktop
release view: run 36896083944 confirms an 800 px buffer, 55-degree vertical field
and 1.68 m eye, so this is a real shortfall at the normal release settings.
Light and balanced retain their explicit fringe overrides; density,
fade bands, nominal reach and all performance ceilings are unchanged. The browser
reruns must demonstrate the existing four-pixel spread, intact ground coverage,
unclamped detail tiers and rendering budgets. The wider prairie work remains
T-1772, where the independent baseline finding is recorded. Final receipts belong
in PR #230; these integration fixes are not a claim that T-1772 is complete.

Part 10 then exposed a second sparse-compound assumption in the drawn-placement
census. The east camp's record explicitly anchors the north-east corner of its
42 x 7 m ground; its nearest drawn tent or baggage is 3.87 m inside that corner.
The building-corner assertion therefore rejects correctly placed camp geometry.
Keep that one-metre assertion for buildings and add an independent comparison of
every GPU-transformed vertex to the sidecar's origin and bearing, with a 0.001 m
float32 tolerance, for all structures including camps. Camps owe that exact
transform instead of occupying their plot corner. The mirror check remains.
Source fixtures demonstrate that a 2 cm displacement, wrong rotation, mirrored
northing and missing placement all fail. This is an accounting correction to the
shared gate, not a relocation or an invented addition to the camps. Both viewports
must rerun part 10 on this instrument before merge.

Run 36899366739 measured the 3.5 m grass trial just below the four-pixel bar
(the old one-decimal diagnostic misleadingly rounded the failing value to 4.0).
Use a 4 m full-detail fringe and print two decimals; the assertion stays at four
pixels. Repeat the boundary, coverage, cap and rendering-budget checks. The
mobile 3.5 m run already confirms terrain contact and its unchanged 19.8 px edge.
