# Period transport recovery checkpoint

Owner, 2026-10-18: continue parallel work, take as many dependency-safe tickets as possible, and save/commit progress for session recovery.

Code checkpoint branch: `steward/period-transport-2793`, based on `dev` at `de37557c5`. No production branch is moved. The tickets evidence directory records the pushed checkpoint hash after commit.

## What exists

`renderers/web/transport/` is a visible development collection of original, portable GLB studies. It is copied by normal publication alongside the renderer. It does **not** populate existing town scenes or change camera travel modes. The original 80 trade wagons and separate water cart remain unchanged.

| Study | Geometry and articulation | Unfinished production work |
| --- | --- | --- |
| W01 wagon | 9,000 triangles; 22 material batches; four rolling wheels, front turntable and movable tongue | Photo/construction comparison, textures, LODs, collision sweep, horses/harness and actor integration |
| C01 open carriage | 9,744 triangles; 27 batches; shaped body, passenger/driver seats, steps, lamps, spring study, steering shafts | Historical subtype, measured mechanics, photo comparison, cloth/doors where appropriate, LODs and coupling |
| H01 horse | 13,872 triangles; five skinned material meshes, 15-joint skeleton, smooth joint weights, idle/walk clips and gear sockets | Complete anatomical topology/rig, source-plate comparison, photographic PBR/UVs, trot, fitted gear and riders |

These are original conjectural/reconstructed engineering studies, not completed T-2793/T-2794/T-2800/T-2801 assets. The follow-on H01 export has actual glTF skinning and a continuous torso/neck loft. Its 15-joint fixture remains short of a complete anatomical rig. Actual authored hoof-sole vertices, rather than relocated markers, show 6.43 mm compensated stance drift over 1,001 walk samples. The earlier rigid-study receipts remain historical lineage in the horse subdirectory; current skin receipts are in horse-skinned. The shown colors and gait are reconstructed. No unknown-rights photo pixels, tracing, base meshes or extracted measurements were used.

The formal glTF validator found empty child arrays in the first vehicle drafts. Integration removed them, pruned obsolete wagon nodes and compacted horse geometry buffers while preserving animation references. Current exports pass the independent Khronos validator with zero errors and warnings; informational empty nodes are intentional proposed sockets/frames.

A fourth study adds original light breastcollar harness, 5,188 triangles in 32 modular meshes, using a text-reported 1891 component list and trace width. Its bridle follows the horse head in a stress-test view; rein/trace tension and full-body fit remain unsolved. The canonical source record marks the OCR reading as not page-verified.

The Hitch page loads the same exported carriage, skinned horse and harness without copying or rescaling them. It synchronizes geometric wheel/horse travel and rebuilds rein/trace endpoint curves. All 42 observed hitch states are preserved in hitch/samples.json.gz with a checksum and a compact validation summary. A 45 mm shaft/socket fit gap remains, along with unproved full collision, forces, occupants and scene traffic. It is a motion compatibility study, not completed T-2795.

## Regenerate and inspect

From `chicago/4d` in the code repository:

```sh
python3 tools/transport/generate_studies.py
# Optional: --only wagon, --only carriage, --only horse
python3 -m http.server 8774 --bind 127.0.0.1
```

Internally request `/renderers/web/transport/` on that server. Each specimen reloads its actual GLB, rather than drawing a second procedural model in the renderer. The same relative vendor imports work in the published tree. Do not expose a localhost preview link from onboarding.

The current carriage and hitch preview motion equations are calibrated to the checked default dimensions/stride. Their fixtures still require corresponding code changes when those parameters change; they are not generic actors yet. W01 already reads its parameters from GLB extras. This is a known T-2795 follow-up, not a claimed parameter-independent runtime.

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
