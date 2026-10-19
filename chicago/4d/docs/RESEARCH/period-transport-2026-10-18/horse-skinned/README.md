# Original skinned equine prototype

This isolated follow-on to the original articulated study implements **real glTF skinning**, not a production anatomical horse. All code and geometry are original CC0-1.0 work. No third-party meshes, photograph traces, texture pixels, anatomy-plate copies or copied external source code are embedded. Pinned Three.js/GLTFLoader and the validator are external runtime/tool dependencies, not copied into this directory.

## Build and inspect

```sh
/workspace/shared/chicago-venv/bin/python generate.py --parameters parameters.json --output-dir .
node validate-khronos.cjs
python -m http.server 8782 --directory /workspace
node validate-browser.cjs
node validate-skin.cjs
```

`generator_base.py` creates the original loft/mesh geometry; `generate.py` bakes it into the common rest frame, adds normalized JOINTS_0/WEIGHTS_0 and valid inverse-bind matrices, groups by material and writes the self-contained GLB. NumPy is the only Python package required beyond the standard library. `parameters.json` controls coat, limb lateral offset, gait duration, hoof lift and stance sweep. The demo assumes `/workspace` as server root and existing pinned Three.js paths. Use `/shared/period-transport-lab/horse-skinned/`.

## What changed and what is proved

- One continuous original barrel-to-neck loft replaces the overlapping spherical croup/shoulder and cone-like neck base. Eyes/cheeks, nostrils and fetlock balls are smaller and more embedded. These changes improve the provisional silhouette but do not establish anatomical or photographic correctness.
- Five **SkinnedMesh** objects share one 15-joint Three.js Skeleton. Matrices bind rest vertices in model space; mesh nodes are scene roots to prevent ambiguous parent-bone/double transforms. Bone hierarchy, world rest positions and material vertex ranges are recorded in `manifest.json`.
- 4,046 vertices have two nonzero normalized weights in joint neighborhoods. Hoof vertices retain one fetlock influence, preserving the fixed authored sole surfaces. Existing semantic joints and sockets remain named and separate. Body/head/tail all deform via the loaded skin.
- Existing in-place idle/walk clips remain intact. At walk phase 0.32, coat vertices move up to 303.4 mm; the neutral skin rest-position discrepancy is below 0.0001 mm. Those are actual CPU `SkinnedMesh.applyBoneTransform` results using the same Skeleton/AnimationMixer as the loaded renderer.
- Khronos `gltf-validator`: **zero errors, zero warnings, zero hints**. Informational messages concern retained empty semantic nodes and one unused material. Full output is in `khronos-validation.json`.
- Actual desktop 1280×800 and mobile 390×780 renders have zero page errors; screenshots and `browser-validation.json` are provided.
- `skin-validation.json` samples **100 existing authored sole-plane vertices** at 1,001 walk times. They are selected from the rest mesh; no contact-marker relocation, changed contact definition or artificially planted proxy is used. Maximum forward-travel-compensated stance surface drift is **6.428 mm** (passes the proposed 20 mm flat-ground fixture target); maximum stance sole-height error **2.194 mm**; worst sampled penetration **0.141 mm**. Neutral sole height error is below 0.00001 mm. This does not validate collisions over other hoof surfaces, terrain or loaded horse/rider/carriage motion.
- `rebuild-validation.json` records a byte-identical regeneration and SHA-256.

## Open gates

The 15-joint fixture still collapses multiple anatomical bones into each limb link. It is not the complete scapula/humerus/radius/carpus and femur/tibia/hock equine rig, and it lacks dedicated spine/pelvis/withers/jaw/ear chains. Skinning is technically real, but simplified anatomy and joint topology remain visible. Legs and head retain disconnected surface pieces; torso-to-neck continuity does not make the full horse watertight. Joint neighborhood weights need informed muscle/deformation review and eventual retopology. No photographic or anatomically validated model claim is made.

Motion timing is synthetic: 62% stance fraction and the existing four-beat walk offsets, not measured movement. Trot, start/stop/turn and transitions remain absent. Anatomical plate/reference visual review, Blender authoring master, UV/PBR coat/hair, source-matched silhouette/landmarks, LODs/compression, full provenance registry, fitting/tension of tack, rider/driver interaction and production integration remain open. This is T-2803 subwork, not completion of T-2800 or T-2803.
