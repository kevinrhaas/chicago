# Resident transport-human studies — recovery and acceptance

The owner's October 18 request covers photographic adults driving wagons/carriages,
riding horses, standing near transport and walking streets, with at least one example
in each correct period. Later steering prioritizes existing attested, inferred or
reconstructed people. Anonymous figures require an explicit inability to use a suitable
existing person, not merely a convenient generic asset.

First references are existing reconstructed 1835 residents:

| person record | model study | recorded role / age |
|---|---|---|
| `rc_bardwell_otis` | `bardwell_otis_1835` | teamster, 20–29 |
| `rc_dufresne_joseph` | `dufresne_joseph_1835` | livery stable keeper, 30–39 |
| `rc_flynn_martin` | `flynn_martin_1835` | teamster, 30–39 |

The builder resolves those actual records and preserves their reconstruction grade.
The residents' identities and ages are modeled dataset records, not archival likenesses.
Using an existing identity does not attest this shared body, clothing, staged action or
face. Three material variants do not establish three finished individual anatomies.
See `../transport-human-candidates.md`, `../generic-human-period-clothing.md` and L418.

## Reproduction

`tools/human_base_prepare.py` verifies hashes of the pinned CC0 graphical inputs and
writes engine-neutral body geometry, corner UVs, an explicit source-bone mapping,
normalized four-influence weights and a quantified loss report. Its eleven tests read the
real source geometry; no Blender runs on this cloud runner.

The owner-visible human authoring PR adds `build_teamsters: true` to the existing
portable-human manual workflow. Dispatch it at the exact checked feature SHA/ref:

```
gh workflow run chicago-4d-humans.yml --repo kevinrhaas/chicago \
  --ref steward/generic-teamster-humans -f build_teamsters=true
```

CI first reproduces all existing fixture bytes and runs its desktop/mobile browser
proof. The dependent study job builds each canonical master under
`assets/authored/humans/teamsters/<model-study>/canonical.blend`, exports through
`tools/human_export.sh --master`, retains the original source skin in the masters,
derives web texture caps of 2048/1024/512/256 with JPEG92 only for verified opaque
color maps (alpha/data maps retain PNG), runs the contract and independent glTF container
validator, measures actual master/web GLBs, publishes compressed deliveries and
captures the study inspection at both viewports. Masters, exports, screenshots,
measurements and logs are retained as an artifact; it does not write any branch.

For an already acquired export, inspect the published delivery using:

```
NODE_PATH=/workspace/shared/chicago-browser/node_modules \
PW_EXECUTABLE=/usr/bin/chromium node tools/human_teamster.mjs \
  --published --output /tmp/resident-teamster-inspection
```

The source and published paths must each load their own actual files. The tool never
substitutes a source master for a missing published derivative. Do not overwrite a failed
receipt with a pass from a different tree or viewport.

## Remaining production gates

No scene instance is enabled by this work. The existing primitive human remains a test
fixture. Canonical validation after authoring changes, individual body/face refinement, photographic
skin/hair/cloth, period-specific garment cut, palms/weights/correctives, LOD silhouette,
real grounded walk, collision and seated driving/riding contact remain acceptance work.
An original procedural shirt weave is a material test, not photographic textile evidence.
The selected original 2K CC0 skin atlas is retained with its actual per-asset license,
ZIP-entry CRC and SHA-256; it does not attest a resident's appearance. Verified adult
shape targets are applied before every helper-joint recomputation. Engineering ages
25/35 and equal software-category blends are authoring choices, not demographic facts.

Drivers need pelvis registration to the real vehicle seat, supported feet, socket-bound
hands/reins, steering and clothing collision checks. Riders need actual dated saddle,
stirrups and bridle plus mounted clips; an empty horse socket is not riding tack. Walking
and standing need terrain sole contact. None of these interactions is completed by a
successful file export. 1812 and 1904 clothing must be qualified independently; this 1835
recipe is not permission to reuse its wardrobe in those scenes.

## Delivery preparation evidence

`../human-web-textures/README.md` records an actual scratch fixture with the selected
2K skin. The four web caps measured 640276 / 253956 / 149796 / 122444 bytes, with
40.99–42.34 dB JPEG PSNR against their actual resized inputs. These are tool proofs,
not the as-yet unbaked resident model sizes or photographic acceptance. Source PNGs
and fixture verification bytes are unchanged. Actual resident delivery still must
pass the existing site budget and both viewport checks.

## Preparation runtime reproducibility

The first canonical CI run 39168738942 passed all ten preparation tests but stopped
at the exact neutral input comparison, before Blender authoring. Python 3.11 uses
a left-fold builtin float sum; Python 3.12 changed that reduction. Emulating the
older behavior reproduced the exact first mismatch at byte 40084, at body vertex
652 X: -0.02902566498920024 versus -0.029025664989200235. The largest measured
numeric difference was 6.66e-16. This is a reproducibility defect, not a reason to
relax the exact-byte assertion.

Dot products, helper averages and weight normalization/pruning now explicitly use
math.fsum. All three neutral/adult inputs and reports are regenerated. A regression
reads the real pinned source data with emulated legacy sum behavior and requires
the full serialized bytes of each recipe to equal its committed input. Source OBJ,
UVs, weights, graphical targets and legal notices remain unchanged. CI must still
prove the actual Python 3.11 reproduction and execute the canonical builder.

## Authored export frame and skin repair

Run 39169918123 verified all three source preparations on actual Python 3.11 and
built Otis's canonical Blender master and all four source/web LODs. The contract
then rejected thigh scale [1, 0.9999999403953552, 0.9999979734420776] and unequal
flattened joint lists. Its output is a failed study, not an accepted model.

Only this original builder opts into rigid-frame export. The exporter independently
checks actual bpy object/world/delta and pose-bone scales, absence of constraints,
drivers and scale curves, and binds that proof to input/master hashes. Only joint
scale residue within 32 float32 ulps (3.8147e-6) may then be removed; genuine scaling
is refused. Nonjoint transforms retain the existing 1e-6 guard unchanged. Mesh,
weight and inverse-bind bytes stay identical. Removing residue can introduce tiny
rest skin mismatch; joint-frame bounds are not proof of skinned surface equivalence,
so actual browser/deformation review remains required.

Source skins consolidate only for exact ordered node identities, decoded inverse
binds and all metadata. Different palettes fail. Scene-wide Meshopt quantization
keeps one common palette across body parts; its slightly coarser small-part position
quantization must pass the same actual master/web frame and browser checks. The
existing fixture export path and all contract assertions remain unchanged. Focused
tests reproduce duplicate-skin and multipart quantization failures and the observed
scale residue; they do not replace execution on the real resident masters.
The actual verifier function is also exercised with explicit synthetic bpy objects
and the committed fixture: its proof reaches the repair helper, while authored
scale curves, constraints, drivers and nonunit scales are refused. These tests
check Python wiring without importing or running Blender; CI still checks its API.

The existing fixture can be tested locally without Blender. The failed resident
artifact is retained on GitHub, but downloading from its actual Azure artifact host
is denied by the current network policy. The exact host is saved in the environment
draft; Review/Save/Publish applies it.
CI retains the original unnormalized exports plus input-bound frame receipts under
teamster-studies/export-evidence, separately from accepted-name exports. Use these
for actual skin/clip comparisons; the raw files intentionally retain the rejected
scale residue and must not be mistaken for accepted source assets.

## Canonical build checkpoint and movement follow-up

Canonical workflow 39173614006 at `0577792dc` passed all three master builds,
24 source/web GLB contracts and 24 desktop/mobile mechanical inspections.
Khronos reported zero errors and seven warnings per GLB. Warning classification
and visual review remain pending: the ordinary artifact download failed at
`productionresultssa17.blob.core.windows.net`, and the saved network draft is
not yet applied. This success does not establish photographic quality.

The following authoring changes require a new canonical CI build. The mechanical
walk uses 37 inclusive keys over 1.2 seconds at 30 fps, declared speed 0.6 m/s,
62% stance, 65 mm swing lift and pelvis lowering 40 +/- 5 mm. Actual prepared
hip/knee/ankle lengths determine the joint rotations; unreachable targets fail,
and no joint stretch is added. All authored curves are explicitly LINEAR and
idle clears walking pelvis translation. These are reconstructed engineering
choices, not measured human biomechanics or a resident's documented motion.

Pure source LBS evaluation of the 37-key quaternion interpolation at 1,001 phases
measures approximately 0.336 mm maximum planted-sole drift and 0.264 mm supported
height error for the two prepared ages. This is not exported-GLB contact evidence.
The new opt-in `--sole-contact` inspector independently decodes each source/web
LOD, identifies fixed sole vertices from named foot/ball skin weights, and samples
actual CPU skinning at 1,001 phases. Loaded speed, stance and duration metadata
must agree with its assumptions. It adds declared actor travel without removing
encoded root motion or aligning feet. Explicit 2 mm drift, height, penetration
and local loop limits are engineering gates for this flat-foot study; discrete
samples do not prove continuous contact, biological quality or garment collision.
CI now runs source and published web inspection separately and retains per-asset
raw contact receipts and served-byte hashes.

Inspection also requires decoded skin texture bindings and temporal bone/surface
variation. Actual deformed geometry determines standing/head framing below the
measured resident header; the 2% margin, zero header overlap and minimum 20%
viewport-height head detail remain strict. Raw/source LOD0 comparisons sample
rest, 21 times per clip and every named morph independently at weight 1 at rest
and a clip midpoint, preserving other loaded defaults. Maximum sampled surface
delta must remain below 0.1 mm. This does not compare Meshopt topology pointwise,
prove all morph combinations, qualify facial anatomy or replace visual review.

Focused regressions use the real pinned Three CPU skin/morph implementation,
prepared source bodies and independent camera projection. No local Blender runs
are needed or permitted. Actual new exports, loaded gait, wardrobe, hair, seated
drivers, mounted riders and scene placements remain unfinished acceptance work.
