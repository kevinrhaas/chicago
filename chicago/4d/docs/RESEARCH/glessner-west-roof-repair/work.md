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
