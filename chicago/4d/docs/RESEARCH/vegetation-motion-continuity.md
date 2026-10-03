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

## Recovery and concurrent continuation, 20:24 UTC

The first checkpoint is saved as `65a334da` in draft PR #364. After restoring it
and merging current dev `17756b47`, the complete 24-sample full/desktop flight
route reported zero abrupt changes, zero identity errors and no instance-cap
shortfalls. Peak: 1,874,103 triangles / 193 calls. The next route crashed Chromium;
that does not constitute a pass for the complete run. The completed flight receipt
and a representative frame are stored alongside the baseline.

The recovered plank-gap filter and its 12 passing source checks are included in
this checkpoint. Paired browser checks, remaining motion routes, mobile, all-tier
costs and release smoke remain pending. The merged source gate passed 752 of 753
steps on its first attempt: the new test needed its measured isolation row. That
row is being measured and the gate re-run before committing.

A second live continuation re-claimed these same tickets at 19:47 UTC (T-2035:
ticket commit `902070e`) and is editing the same branch name with additional
flora and adaptive-ground work. Reconcile the two implementations before merging
to dev; compare both plank diagnoses against actual rendered ground triangles.
This checkpoint is recovery material, not a completed repair or deployment.


## Reconciled diagnosis and second movement pass

Checkpoint `e518e6f9` contains the recovered work and passed all 753 source checks.
The other continuation is now isolated on `steward/flora-recovery-experiment`.
Its terrain diagnosis was reconciled with actual emitted geometry: the original
longitudinal-walk sample omitted street crossings. Across all 213 walks/crossings,
752,724 top-face samples, and an exact overlap check of 107,532 top triangles,
the old base intersects 1,855 top triangles, all in board crossings. The reviewed
crossing-only adaptive mesh removes every intersection and leaves at least
47.90 mm clearance. Its 103 refined cells add 8,704 triangles, versus 28,064
for protecting every vegetation exclusion. The transition has no internal open
edges, non-manifold edges, downward triangles or degenerate triangles. The
25 mm setting is the refinement trigger at sample vertices, not a global error
bound between samples.

The full-detail strafe and reverse routes also passed with zero coverage jumps
and identity mismatches. The additional nadir prairie route exposed a different
failure: walking clearance removed plants beneath a flying camera. Clearance
now applies only when the camera body could meet the plant. Pitched views also
exposed undersized flower/rosette allocations; the light near set needed up to
465 instances against its old 420 cap. Allocations are enlarged without changing
placement density, botanical heights, or the rendering ceilings.

The corrected full and balanced desktop nadir routes passed without shortfalls.
The first multi-tier diagnostic revealed its initial mobile/full label was wrong:
it wrote an obsolete preference key, so that first mobile tier was actually light.
That reading is excluded. Both browser tools now use the real settings preference,
explicitly select the requested tier and verify `api.detail`. The final sweep
persists each finished route and samples every production placement tick; its
optional sparse-render mode draws saved frames only. Renderer budget gates still
perform their normal complete renders. Final all-tier/mobile results and release
gates remain pending.


## Integrated flight and reach repair, 21:40 UTC

The 42-combination movement sweep covers seven routes, three tiers and both
viewports: 960 placement samples. It found no identity errors or instance-cap
shortfalls. Forty combinations passed the coverage-step limit; the two light
flight passes exposed a too-short rosette fade. Widening that fade from 1.6 to
1.75 m leaves the close nine-metre verge solid. Repeating those two routes adds
48 passing samples with zero jumps, identity errors or shortfalls. Both the
original result (including its two failures) and the corrected repeat are saved.
The mobile census smoke also exposed a minimal-camera compatibility assumption;
the renderer again supports its existing camera-like probe interface, and the
repeat passed 46 checks with zero failures.

The light-tier overhead control identified a third plankwalk problem: the
250 m furniture reach removed complete distant sidewalk chunks. A new batch
retains only their actual emitted top triangles, using the same material and
all original attributes. It excludes tier-disabled crossings, visible detailed
chunks, frustum-excluded chunks and chunks hidden only by the far-merge system.
It adds at most one call and exposes live cost statistics for review. Nine new
source checks cover exact geometry, material, handover and eligibility contracts.

The initial six-stand light diagnostic, before the far-top batch, measured
1,013,329 triangles at the prairie stand against the previous 910,000 ceiling.
The owner authorized increasing the limit if needed at 16:35 CDT. The repair
first removes zero-area grass-tip triangles without changing any visible plant
surface; final integrated measurements will determine whether a higher budget
is needed. No change in a test limit is treated as evidence of acceptable visual
behavior or consumer frame rate.

Current dev a9c98af7 is integrated, including its unrelated scene and research
updates. Earlier fetches had updated FETCH_HEAD but not origin/dev because this
clone tracked only the task branch; that tracking configuration is corrected.
The PR's conflict was therefore real, not a reason to bypass integration gates.
Final published costs, plank pairs, complete smoke and the dev merge remain pending.


## Measured budget update

The owner authorized increasing the rendering limit if needed, repeated at
16:42 CDT. With current dev and exact distant walk tops, the six desktop stands
measure Full 2,820,988 triangles / 282 calls, Balanced 2,127,277 / 248, and
Light 1,015,035 / 77 (triangle maxima at west prairie; Light calls at Lake/Market).
Light's narrow-viewport maximum is 920,708 / 75. The declared limits become
2,840,000 / 2,145,000 / 1,040,000, preserving the existing defended margins
18,059 / 16,806 / 21,933 and rounding upward to 5,000. The 295-call overall and
90-call Light caps remain unchanged. This knowingly increases the triangle
budget, including on weaker devices; SwiftShader diagnostics establish geometry
cost and continuity, not consumer frame rate. Ordinary published smoke is still
the release assertion. The concise cost receipts retain their original exceeded
ceilings rather than rewriting historical readings to pass.

The integrated source gate passed 759 steps, including 313 self-tests, before
this table update. Full preflight is now repeating against the updated limits.
