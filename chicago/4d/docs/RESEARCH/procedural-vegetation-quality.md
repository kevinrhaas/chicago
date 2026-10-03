# T-2015 — Procedural vegetation quality

## Request and diagnosis

The owner supplied two views on 2026-10-02: solid polygonal tree crowns and oversized rectangular understory leaves. The shared renderer already carries researched species, dimensions, placement constraints, summer colours and phenology. Its visual primitives were the defect: jittered 20-face solids in `trees.js` and opaque trapezoid shrub sprays in `flora.js`.

The requested standard is photographic quality comparable to the detailed Glessner model. The work replaces these primitives with leaf-scale silhouettes, bark grain, porous crowns and more legible branching. Photorealism is a visual target, not a claim established merely by adding procedural noise.

## Boundaries

Species, community extents, historical placement, dimensions and July flowering eligibility remain owned by `data/flora`. New visual surfaces are deterministic code-authored reconstructions. No downloaded photograph, paid asset, external runtime service or additional network request is involved. Detailed geometry varies within the existing botanical forms rather than re-rolling ecological stations. The shared renderer is used wherever the current year loads the corresponding flora; this ticket does not plant missing 1812 or 1904 landscapes.

## Rendering approach

- Trees: multioriented branch sprays with species-family leaf silhouettes, transparent gaps, midribs/veins, varied leaf tones, mapped bark and tapered forks. Full and balanced spend detail on branch structure and overlapping sprays; light retains the low-end geometry floor.
- Understory: replace opaque spray rectangles with actual leaf/twig silhouettes; preserve recorded shrub width and plant distribution. Near higher-tier leaves and grasses gain curvature.
- Materials: alpha-tested opaque rendering avoids per-leaf transparent sorting. Wind and tree shadow passes share deformation and cutoff. Confidence grading remains attached to the source records.
- Placement randomness is separate from visual surface variation. New detail must not change downstream tree or species choices.

## Reproducible visual review

`tools/vegetation_review.mjs <site-root> <output> --tag before|after --viewport both --detail full`

The script serves the published mirror, freezes the animation clock and shoots 1280×800 and 390×780 at the river bank, North Branch bridge, west prairie and one deterministic plantable woodland point. The output includes the actual woodland pose, scene and vegetation census, hardware renderer, startup interval and page/console errors. Startup on this shared software-rendering host is not a consumer GPU performance claim.

The existing `measure_detail_ceilings.mjs` checks all three tiers at the five established worst-case stands plus the newly covered prairie view. `measure_timber_detail.mjs --gate` checks the timber distribution. Published smoke parts 10–11 cover physical rooting, species/flower census and sward reach. Moving camera, confidence mode and shadow views are reviewed separately because still images cannot establish those behaviours.

## Coordination with T-2014

The owner flagged active T-2014 during this run. PR #328 (`claude/project-thread-uzqpmm`) extends shrubs to 140 m at full detail, using the same lattice slots and a coarser `farShrubGeometry`. T-2015 keeps the reach/deal/seeding logic owned by that change, and makes its near and distant geometry use the same leaf-cutout material. The shared `shrubGeometry(grain, name, reach, segments)` signature permits the distant 48-triangle form to remain inexpensive. Integration validation must be on a tree containing both changes, including a forward walk at Kinzie/Clark.

## API references

- [Three.js Material](https://threejs.org/docs/pages/Material.html): alphaTest and shader cache behavior.
- [Three.js MeshDepthMaterial](https://threejs.org/docs/pages/MeshDepthMaterial.html): alpha cutouts in the depth pass.

## Recovery and verification state

Ticket: T-2015 in `kevinrhaas/chicago-tickets`. Code branch: `steward/photographic-flora`. Checkpoints are pushed during implementation. Verification results and before/after images are added before merge; until then this document is the implementation record, not a passing test report.

## Checkpoint findings

The isolated real BatchedMesh review passes 180 species/seed/tier cases: unchanged placement RNG consumption, finite attributes and light geometry no larger than the previous solid crown. Four representative full trees use 1,864 triangles / 3,232 vertices; light uses 832 / 1,408. Bark winding and atlas seams were corrected after close review. The atlas has 2048 × 2048 pixels with alpha-coverage-preserving mipmaps (approximately 21.3 MiB GPU); surfaces are reconstructed botanical families, not scanned species specimens.

The first scene preview was rejected: two flora shader programs exceeded the 16-attribute floor, hiding grass. Botanical UV/kind now occupy unused components in existing `aDir`/`aSide` attributes; CPU audit metadata remains available. Fixed-scene verification is in progress.

The previous published scene at `de81fad2` already exceeded its full and balanced limits at Lake/Canal (1,857,270 and 1,626,747 triangles), and its light limit at the forks (851,431). The previously uncovered prairie view drew 1,949,552 triangles and 243 calls at full. These inherited excesses are recorded separately from the upgrade. The owner explicitly approved measured upper-tier budget increases. The light limit remains 825,000 triangles / 90 calls. Final candidate readings will determine the new upper limits.
