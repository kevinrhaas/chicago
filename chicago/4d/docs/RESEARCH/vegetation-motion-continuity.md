# Vegetation and South Water plankwalk continuity

Owner report: 2026-10-03. Tickets T-2035 (walking/flying plants), T-2038
(regular shrub rows) and T-2037 (distant plankwalks). Recovery branch:
`steward/t2035-vegetation-continuity`, based on dev `519ccf6b`.

## Why the earlier still-frame review was insufficient

The original moving-camera baseline, measured from the published mirror at
1280 x 800/full, contains 101 abrupt on-screen rooted-plant coverage changes on
an eight-metre roadside walk, 38 on the riverbank walk and 75 in the flight pass.
These are changes greater than 0.45 coverage between adjacent samples, with the
plant centre inside both frames. The walking sample spacing is 0.25 m; flight
is 0.75 m. This is a continuity diagnostic, not a perceptual score or consumer
frame-rate measurement. Wind/light are held and real production ticks place and
render the plants. Original frames and a compact per-frame receipt are in
`vegetation-motion-continuity/`.

## Current implementation

- Near and mid clumps retain their exact world-slot species, support and transform
  in lower-cost geometry beyond the detailed ring. The mid carry selects three
  columns from the canonical seven and remains through the close inner edge.
- Far cards and shrubs preload before their shader coverage becomes positive;
  coverage changes every frame, with no change in plant height. Far shrubs use
  a subset of canonical detailed sprays, avoiding a different silhouette at the
  handover. The close verge retains its solid coverage policy.
- Camera cones account for pitch, in outward angular buckets. Slow-rebuilding
  carry populations have spatial cone padding. High flight also uses a padded
  3D frustum; larger buffers avoid row-order truncation. These are allocations,
  not permission to exceed rendering budgets.
- Sparse shrubs use full-cell jitter instead of repeatedly selecting one
  quarter-cell. Near/far identities still share the same seed and species deal.
- The sampled shrub roots are predominantly in riverbank timber (red-osier and
  grey dogwoods, common elderberry and ninebark), with wet-prairie meadowsweet
  nearby. A screenshot alone does not identify one particular plant. The small
  legacy settled-town community separately contains inferred dooryard currants.

## Plankwalk diagnosis and remaining work

The separate review sampled 25,200 points across ten South Water walks against
published ground triangles and found no buried board tops. Minimum clearance was
7.85 mm in one small river-west patch; other minima were 50-105 mm. Full-detail
browser controls at E550/N14.8 did not support a near-plane, draw-order or
far-merge explanation. Narrow board gaps become subpixel at distance; a
resolution-aware gap filter is being prepared on `steward/t2037-plank-visibility`
for comparison. Its geometry/depth behavior and light-tier reach still need
moving-camera validation. The intentional La Salle slough gap E459.5-489 remains.

## Validation status at the recovery checkpoint

The new full/desktop roadside pass reports **zero** abrupt coverage changes and
zero identity mismatches, versus 101 before. Its peak is 1,839,182 triangles and
215 calls (before: 1,769,095 and 213). Other motion routes, all-tier desktop/mobile
budgets, mandatory browser stages, and the dev merge are pending. Do not describe
this checkpoint as a completed repair. The first source-gate attempt was blocked
by sandbox subprocess fixtures and stale generated documentation; the clean,
regenerated gate passed all 750 steps. No assertions have been relaxed.

Run: `NODE_PATH=<playwright> PW_EXECUTABLE=<chromium> node
 tools/vegetation_motion_review.mjs ../../site <output> --tag after
 --viewport desktop --detail full`. Add `--baseline --baseline-ref 519ccf6`
for the original flora module. `--routes` accepts comma-separated route names.
The browser is Chromium/SwiftShader; absolute rendering times are not phone FPS.
