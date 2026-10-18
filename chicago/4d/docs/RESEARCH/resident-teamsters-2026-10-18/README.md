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
fixture. Canonical Blender execution, individual body/face refinement, photographic
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
