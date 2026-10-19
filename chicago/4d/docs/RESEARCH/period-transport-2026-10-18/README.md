# Period transport recovery checkpoint

Owner, 2026-10-18: continue parallel work, take as many dependency-safe tickets as possible, and save/commit progress for session recovery.

Code checkpoint branch: `steward/period-transport-2793`, based on `dev` at `de37557c5`. No production branch is moved. The tickets evidence directory records the pushed checkpoint hash after commit.

## What exists

`renderers/web/transport/` is a visible development collection of original, portable GLB studies. It is copied by normal publication alongside the renderer. It does **not** populate existing town scenes or change camera travel modes. The original 80 trade wagons and separate water cart remain unchanged.

| Study | Geometry and articulation | Unfinished production work |
| --- | --- | --- |
| W01 wagon | 9,000 triangles; 22 material batches; four rolling wheels, front turntable and movable tongue | Photo/construction comparison, textures, LODs, collision sweep, horses/harness and actor integration |
| C01 open carriage | 9,744 triangles; 27 batches; shaped body, passenger/driver seats, steps, lamps, spring study, steering shafts | Historical subtype, measured mechanics, photo comparison, cloth/doors where appropriate, LODs and coupling |
| H01 horse | 14,544 triangles; five skinned material meshes, 15-joint skeleton, smooth joint weights, idle/walk clips and gear sockets | Complete anatomical topology/rig, source-plate comparison, photographic PBR/UVs, trot, fitted gear and riders |

These are original conjectural/reconstructed engineering studies, not completed T-2793/T-2794/T-2800/T-2801 assets. The follow-on H01 export has actual glTF skinning and a continuous torso/neck loft. Its 15-joint fixture remains short of a complete anatomical rig. Actual authored hoof-sole vertices, rather than relocated markers, show 0.020 mm compensated stance drift over 1,001 walk samples. The earlier rigid-study receipts remain historical lineage in the horse subdirectory; current skin receipts are in horse-skinned. The shown colors and gait are reconstructed. No unknown-rights photo pixels, tracing, base meshes or extracted measurements were used.

The formal glTF validator found empty child arrays in the first vehicle drafts. Integration removed them, pruned obsolete wagon nodes and compacted horse geometry buffers while preserving animation references. Current exports pass the independent Khronos validator with zero errors and warnings; informational empty nodes are intentional proposed sockets/frames.

A fourth study adds original light breastcollar harness, 7,532 triangles in 36 modular meshes, using a text-reported 1891 component list and trace width. Its bridle follows the horse head in a stress-test view; rein/trace tension and full-body fit remain unsolved. The canonical source record marks the OCR reading as not page-verified.

The Hitch page loads the same exported carriage, skinned horse and harness without copying or rescaling them. It synchronizes geometric wheel/horse travel and rebuilds rein/trace endpoint curves. All 70 observed hitch states are preserved in hitch/samples.json.gz with a checksum and a compact validation summary. The former 45 mm lateral socket mismatch is resolved by original reconstructed leather tugs and support webbing. Actual shaft-section and loop geometry show 6.49 mm radial clearance at the checked poses; full collision, forces, occupants and scene traffic remain unproved. It is a motion compatibility study, not completed T-2795.

## Regenerate and inspect

From `chicago/4d` in the code repository:

```sh
python3 tools/transport/generate_studies.py
# Optional: --only wagon, --only carriage, --only horse
python3 -m http.server 8774 --bind 127.0.0.1
```

Internally request `/renderers/web/transport/` on that server. Each specimen reloads its actual GLB, rather than drawing a second procedural model in the renderer. The same relative vendor imports work in the published tree. Do not expose a localhost preview link from onboarding.

Carriage and hitch motion now read exported wheelbase, track, wheel radii and walk-stride metadata. A browser-only 10% metadata perturbation verifies four wheel angles and gait phase against independent formulas. Shaft tip and bore measurements use loaded vertices. These remain development fixtures; changing dimensions still requires renewed physical fit checks.

Inputs are `data/transport/studies/{wagon,carriage,horse,harness}.json`. Generators are `tools/transport/generate_{wagon,carriage,horse,harness}.py`; horse skinning also calls `horse_geometry.py`. NumPy 2.3.5 is needed for carriage batching and horse skinning. All geometry is rebuilt from those inputs; some explicitly documented furniture/detail constants remain in the generators. Changing running gear requires renewed clearance inspection, not only a JSON edit.

For independent export checking, install `gltf-validator@2.0.0-dev.3.10` outside the checkout, set `NODE_PATH` to its node_modules directory, then run:

```sh
node tools/transport/validate_exports.cjs
```

For the current environment, that package is in `/workspace/shared/transport-tools/node_modules`; browser tooling is in `/workspace/shared/chicago-browser/node_modules`. Normal repository validation remains `CHECK_JOBS=4 bash tools/check.sh` with the shared Python venv active and the local `bc` tools directory on PATH. Never run two publishers/checks concurrently in this checkout.

Additional exercised browser checks (serve the source tree on port 8774 first):

```sh
NODE_PATH=/workspace/shared/chicago-browser/node_modules node tools/transport/smoke_studies.cjs
NODE_PATH=/workspace/shared/chicago-browser/node_modules node tools/transport/smoke_skin.cjs
python3 tools/transport/smoke_hitch.py
```

The first checks all four model pages at desktop/mobile; the second checks actual skinned sole vertices; the third samples coupled distance/steering states. These are development-fixture checks, not the full application release smoke.

## Evidence and resume order

The authoritative queue and research are in `kevinrhaas/chicago-tickets`. Epics T-2791 and T-2798 are split into children in bands 8D/8E below portable humans. T-2792/T-2799 are the parallel research/specification work; T-2793/T-2794/T-2800/T-2801 are started model/gear work. No production ticket is closed by this checkpoint.

Read `chicago-tickets/evidence/period-transport-2026-10-18/`, especially the two source-acquisition reports. Actual new text reads include 1891 John Moore harness construction, 1904 Hasluck, 1882 Stillman, and a Stubbs anatomy edition with a Public Domain Mark. Some metadata-only coachbuilding finds and original plates remain blocked at archive storage hosts; no dimensions from unread pages are asserted. Pullman carriage ownership remains unproven. The Chrimes left-team count remains disputed.

Next: fit the independently built harness to actual H01 sockets; verify trace/rein paths against W01/C01; improve anatomical continuity and source-matched surfaces; qualify LOD/export and measured source comparisons; then implement traffic and mounting/boarding. Reuse portable humans once their dependencies and current depiction policy allow them. Do not mistake the fixture's flat-plane rolling for finished town traffic or riding physics.

The per-model subdirectories retain the original lab receipts and screenshots for lineage. Their original sizes/node counts precede integration pruning and buffer compaction; the current GLB and new integrated receipts govern current claims. Licenses are in `renderers/web/transport/LICENSES.md`. No Blender installation or bake was used for these procedural studies.

## Second checkpoint: fitted study refinements

The walk now has exact contact-event keys and smooth swing/lift endpoints; 100 existing actual sole vertices sampled over 1,001 phases show 0.0201 mm compensated stance drift and 0.0396 mm maximum stance height error. Timing remains synthetic. Original muzzle, ear, mane and hoof silhouettes were refined; anatomical/photo acceptance remains open.

The breastcollar previously floated up to 171 mm from the torso. A raised symmetric route follows the actual continuous torso, with per-point width directions tangent to its surface normals. The first lower route passed torso proximity but produced upper-forelimb overlap indications; it was replaced before commit. Across 204 actual collar vertices in neutral idle and 21 walk phases, current signed nearest-torso distances are +4.167 to +16.774 mm. Separate deformed limb bounds are checked; nearest-face signs outside a limb are only diagnostic. These checks do not establish full harness collision, pressure or historical fit. See harness-fit. Original reconstructed shaft loops have finite thickness; their toroidal section remains a development approximation rather than source-verified folded leather construction. Breeching still lacks a validated holdback load path.

Front-axle wheel paths account for the axle itself steering: the front factor is sec(steering) minus curvature times lateral wheel offset. The earlier formula assumed unsteered wheel-center positions. A finite-difference check compares actual loaded wheel-center world motion with wheel-angle change times exported radius at straight and both turning limits; it is stronger than comparing two copies of the motion formula.

The collar band is now an explicit reconstructed 50 mm width (8 mm thickness), reduced from the unmeasured 65 mm study after triangle-level foreleg checks found intersections in four walk poses. Its raised route and per-point tangent widths are model-fit choices, not period measurements or animal-suitability approval. The failed 65 mm receipts remain alongside the corrected report.

Final forelimb sweep covers idle plus 101 walk phases: no triangle-pair AABB candidates or intersections for the breastcollar against the selected actual upper-forelimb meshes. Minimum vertical bounds separation is only 0.589 mm (limb max Y 1.306008 m, band min Y 1.306597 m). This is a narrow sampled geometric clearance, not sufficient production margin, continuous collision, all-harness fit or force validation. Nearest-face signed distances outside the limb are diagnostic and can be negative despite disjoint bounds; assertions use actual triangle/bounds tests instead.

## Pre-merge smoke isolation

Integration with newer dev exposed an existing T-2559 smoke-harness issue: the cold profile was timed in a second page while the first page was already drawing the town. A lone scene still produced an 8.74-second probe, while the same published module with no town measured 128 ms. The probe now runs before town navigation, matching actual boot order; the one-second cold and 50 ms warm limits are unchanged. The corrected desktop stage-1 benchmark assertion passes. Application device profiling is unchanged. Full preflight and published desktop/mobile workflow results govern the dev merge; the ticket repository records exact revisions and outcomes.

## Replacement smoke coverage on current dev

The first full mobile run39164260098 failed its stage5 far-merge triangle invariant; desktop39164186323 timed out at90minutes with incomplete coverage and four observed failures. These results remain retained, not waived. The current integration includes dev a99f3623849bb2e7ce6c7d255ff3adecc66d5dcd and preserves its120-second Guide readiness fix.

The far-merge assertion now compares fresh synchronous on/off/on frames at the same camera, retaining exact zero triangle movement and adding exact restoration of triangles and calls. A bounded published mobile probe measured91 saved calls and zero triangle/restoration delta; it did not reproduce or prove the cause of the CI failure. Yard/confidence capture trios now record camera, geometry, flora and texture state fingerprints without adding frames, waits or readiness changes; original pixel thresholds remain. The bounded desktop yard trio passed mean0/worst0 restoration, while the confidence diagnostic remained incomplete. A state fingerprint change alone does not attribute a pixel residual.

After the full preflight and commit, use the existing nine stage groups at both viewports, one frozen head, for18 manual smoke runs. Every individual run remains partial. The tickets repository retains an aggregate validator requiring exact head/attempt, completed published logs, all stage coverage, all always-on guards and assertion-count arithmetic. No new full coverage or green merge is claimed until those actual results pass.


## Transport integration repair — 2026-10-19

Dev a369c613 is integrated, preserving its Guide, Inspect, crash-card and 1904 building changes. Four conflicted source-use outputs were rebuilt with the manifest resolver: 50 steps, two laps, final lap unchanged. No derived JSON was merged by hand.

The earlier e5 desktop confidence restoration failed while flora pending state and geometry changed. Baseline capture now waits for four unchanged semantic observations with no active near/far flora placement or pending texture loads, bounded by 120 animation callbacks and 60 seconds. It uses normal rendering and does not force-drain the scene. The after image still captures immediately; the same pixel thresholds, grids, scenarios and failure behavior remain. Deterministic tests execute the actual helper and cover pending work, late changes, both deadlines and unchanged after capture. This is bounded readiness, not universal future asynchronous quiescence.

Stage5 now forces a production step after its existing two animation callbacks before reading last-frame renderer counters. Fresh pricing captured 36 unique stand/tier/viewport rows, split into 27 rows before a diagnostic timeout and nine continuation rows. It is not canonical smoke coverage. At measured379e7d3d, tree modules match e5 and main differs by resident role-card wiring without actors. The later dev merge is qualified separately by new exact-head coverage.

Conscious measured repricing follows the standing rule: full 3,449,919 +18,059 rounded to 5,000 gives 3,470,000; balanced 2,607,952 +16,806 gives 2,625,000. These maxima are desktop West prairie. Upstream T2807 tree integration and the measurement freshness correction are distinct; the whole change is not attributed to new trees. Historical notes remain. Light stays at 1,190,000 triangles, measured 1,154,091. General draw calls stay at 330; Light's separate 90-call limit stays strict, measured 89. No future actors are prepaid. See docs/measurements/period-transport-fresh-detail-2026-10-19.json.

Full preflight and complete published desktop/mobile coverage of this corrected merged head are required before merge. Photographic fidelity, anatomy/material refinement, harness forces, traffic, boarding, riders and driver occupation remain open production work.




## Recovery diagnostics on current dev

The frozen9a84 full fast gate passed983 steps. Its newer stage1-2 restoration and
stage5 budget checks passed both viewports, but mobile6-7 refused two old
`notice === null` assertions. T-2826 on dev intentionally shows the previous
reset diagnostic even when the prior page subsequently left cleanly. Actual
receipts showed the expected navigation counts and tier changes; this was a
conflict between the old smoke predicate and the new feature contract.

The next revision retains dev43d8f0a04, including Researcher mode, and requires
that exact prior-reset diagnostic: readable rendered text equals the notice,
Copy matches the actual previous record, no extra Reload prompt appears, and
its previous-page ID equals the page that just reset. Navigation counts,
single automatic reload and balanced-to-light policy stay strict. The manual
reload also requires null pending lowering, two session losses and active
watching. A regression imports the real blackbox and actual smoke predicate,
checks two clean navigation sequences, and refuses eleven wrong/missing states.
It proves the predicate and record semantics; actual browser context loss and
tier behavior still require the complete published smoke on the next commit.

The old e5 batch finished with16 successful legs and two failures. The frozen9a84
batch had15 accepted successes, one mobile6-7 failure and two desktop legs still
running at last observation. These results are retained, not replaced with a
new-head pass. No model photographic gate, occupied traffic or boarding/riding
acceptance follows from a corrected test predicate.


## Combined transport and resident checkpoint — 2026-10-19

Transport c4f6e5424 passed full preflight985/0 and postcommit changelog checks. Resident2679d6c98 passed local991/0, but canonical CI39184480142 failed during the first resident LOD0 body custom-normal readback. The guard raised before printing errors, so neither magnitude nor seam disagreement is yet known; no resident master/export/hair/hierarchy/browser proof followed. Legacy fixture checks passed separately. The combined source adds bounded diagnostics before the unchanged1e-3 guard. Pinned Blender codec analysis supplies a conditional counterexample to a universal1e-3 bound, but no complete floating-point/fallback bound or actual resident metrics; it does not authorize relaxing acceptance.

W01 now has original reconstructed tapered octagonal spokes,1.2mm board/stave chamfers and less board-color contrast. Reviewed controlled close/clay/mobile comparisons show a slimmer taper, with modest full-view gain. It increases9000 to10792 triangles, retaining22 meshes,47nodes, wheel bounds and proposed socket frames. Determinism and Khronos0errors/0warnings were measured outside the application; combined integration gates remain required. These dimensions are engineering liberties. Historical joinery, photographic surfaces, occupied traffic, boarding and riding remain open. Horse-head and strap candidates remain outside the application pending visual refinement; intersection checks alone do not establish fit or photographic quality.

The frozen9a84 batch currently has16 accepted successes, one preserved mobile6-7 recovery-predicate failure and desktop13 still running. It cannot qualify this combined revision. Full local preflight, canonical resident authoring and complete published desktop/mobile coverage must pass on the final same head before dev merge.


Combined merge derivation qualification: full `rederive --resolve` failed at unchanged North Branch raster reread (IIIF HTTP403); this is retained as a failed attempt, not a successful full rebuild. All44 tracked terrain/traces and river readers/baseline were byte-identical to both parents. A separate cycle audit found22 selected readers/outputs/declared inputs byte-identical to both parents and mergebase; changed resident data outside human metadata consists only of incoming prose, with no seating/population/placement field change. The supported `--tail tools/compile_liberties.py` route rebuilds the actual liberties conflict and every downstream step, with a final unchanged lap required. Complete earlier verifiers remain required in full preflight. That bounded route does not claim a fresh raster measurement or equivalent full second-pass orchestration.


## Refined transport studies and strict resident experiment — 2026-10-19

Combined9cc7b9ac8 passed998 local checks and postcommit checks, but canonical39192083053 failed the first resident normal audit: maximum0.00129066,21bad corners and one UV-seam group above the unchanged0.001 limit. No new resident export, hair, hierarchy or browser qualification followed. The next source activates an explicit isolated-CI Short2 fan-probe experiment, preserving raw target/seam limits, original topology/UV/weights and fail-closed restoration. Thirteen portable math/API-mock/argument tests pass; actual Blender repair and downstream exported visual quality remain unverified.

The current development models have rounded C01 cushions, a continuous shared-weight horse neck/head join, revised paired headstraps and an additive grounded diagonal trot. Source/data regenerate all ten outputs identically in two runs. Independent container validation reports zero errors/warnings, with informational/hint diagnostics retained. Existing horse geometry, sockets,15joints and idle/walk animation tracks stay unchanged by the additive trot; the earlier ear revision raises rest bounds19.200087mm and adds one inner-ear draw batch. No actor capacity is prepaid.

Fresh browser checks before trot passed all isolated desktop/mobile specimens,35coupled states per viewport, actual100hoofsole vertices over1,001walk poses, selected torso/forelimb checks and21full headstrap surface tests. These receipts identify their exact input revision. Subsequent actual trot tests against the new GLB passed1,001poses/clip,8.026micrometre trot stance drift,21headstrap poses with zero SAT crossings and2.406431mm unsigned minimum,24shared-boundary pairs with zero gaps, and101selected upper-forelimb poses with zero collar crossings. The forelimb nearest-face sign minimum−0.137m remains a diagnostic, not containment. Torso evidence remains a vertex nearest-face criterion, not full torso SAT. No pressure, continuous motion, biological gait or load acceptance is inferred.

Actual viewed bare-horse and coupled/mobile images show improvement, but anatomy, rigid ears, eyelids/muzzle, segmented limbs, materials and photographic quality remain primitive. Trotting is isolated bare-horse playback; distance-matched transitions, trotting hitch, dynamic reins, riders, boarding and town traffic remain open.120desktop synchronous samples give0.6ms p95 update/render submission only; no GPU completion, phone performance or town budget acceptance. Final portable walk/trot head-measurement execution and full combined preflight remain required before the next commit. All production tickets stay open.

Portable installed head-fit verification completed for current walk and trot: 21 sampled poses each, zero tested strap/head triangle intersections, zero paired neck-boundary separation, unsigned minimum 2.406431169 mm. Actual input hashes and bounded receipts are in RESEARCH/period-transport-2026-10-18/head-neck-refinement/. This does not establish containment, continuous collision, riding or photographic acceptance. Full preflight follows after freezing authored inputs.

Current dev5c83a1854590ed2c1e4c77e925fc7bda5f3532e3 is combined with the refined transport batch. Both black-box notice and exact prior-reset record assertions survive the smoke merge. The actual loss callback now captures its page identity before restoring; a caller-level regression catches the former missing return field. Travel-grid preview distance accumulates across gait loops and respects pause and reduced grid motion; geometry/clip data are unchanged by that viewer repair. Earlier trot-inputs.json remains its original stage receipt, superseded for demo.js only by travel-grid-repair.json. Derived owning tail and full preflight follow.
