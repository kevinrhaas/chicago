# Original equine articulation study

This is an **original conjectural articulated fixture**, not a photographic model, anatomically validated master, completed T-2800/T-2803 deliverable, or a historical individual. It is unpublished research-lab work. Geometry, bay coat, proportions, movement timing and socket offsets are engineering choices. No photograph pixels, traced contours or third-party geometry are embedded. The original source and generated asset are dedicated under CC0-1.0.

## Rebuild and inspect

Python standard library only:

```sh
python generate.py --parameters parameters.json --output-dir .
python validate.py
python -m http.server 8782 --directory /workspace
node validate-browser.cjs
```

Open `http://localhost:8782/shared/period-transport-lab/horse/`. The browser demo uses the checkout's pinned Three.js and GLTFLoader (not a CDN); it currently assumes `/workspace` is the server root. The browser validation uses the existing shared Playwright package and `/usr/bin/chromium`. Integration may adjust those hosting paths. Parameters control coat, lateral limb spacing, cycle duration, hoof lift and stance sweep; the generator contains the original loft geometry.

## What exists

- Metre-scale, Y-up, +Z-forward glTF 2 binary; fixed ground root.
- 15,600 source triangles; 23 visible material-group meshes (23 main-pass draws, plus shadow-pass work). Unused leaf names retain semantic traceability. Export intentionally has no textures or external buffers.
- Original lofted barrel/neck/face, croup and shoulder volumes, muzzle, eyes, nostrils, ears, narrow mane, tail, four two-link limb chains, fetlocks, pasterns and hooves.
- Stable fore/hind, left/right semantic names and provisional sockets. Socket `+X` is anatomical left. Tack sockets are **unfitted**; no harness clearance/tension or rider fit is claimed.
- In-place `idle` and `walk` animation, deterministic phase control, counter-moving contact-review grid, side/front/head/three-quarter views, mobile layout.
- The walk is a **synthetic four-beat kinematic fixture** with lateral sequence hind-left / fore-left / hind-right / fore-right and 62% stance fraction; these timings are not measured historical or biomechanical reference data.

## Actual validation

`export-validation.json` checks GLB header/chunks, binary accessor ranges, finite floats, index bounds, increasing animation times, animation input/output counts and no animated root. It does not claim an external Khronos validator pass.

`browser-validation.json` records actual GLTFLoader renders at 1280×800 and 390×780, zero page errors and 1,001 walk samples per viewport, including interpolation between authored keys. Neutral contact markers are within 0.00001 mm of the plane. After compensating for the authored forward speed, maximum world-space stance-marker drift is **6.39 mm**, below the proposed 20 mm fixture threshold. Maximum stance-marker height error is **1.994 mm**; minimum sampled contact height is **−0.455 mm** (small interpolation penetration). These checks concern semantic sole markers on a flat plane, **not** collision detection over the whole hoof surface, terrain, real measured gait, or a rider/hitched unit. Contact errors must be remeasured after edits. Screenshots include desktop/mobile idle and side walk.

The speed is `stance_sweep_m / (0.62 × walk_cycle_duration_s)`; cycle travel is `stance_sweep_m / 0.62`. Default 0.72 m stance sweep and 1.25 s cycle yield 0.929 m/s and 1.161 m cycle travel. This satisfies the metadata speed/cycle/stride consistency relationship by construction, not by motion-reference matching.

## Remaining production gates

The limbs currently use **rigid articulated mesh segments, not glTF skinning**. The two-link solver collapses multiple anatomical bones; it is not a complete equine skeletal contract. Joint/shoulder/barrel seams, simplified muscular shape, faceted transitions and untextured coat remain visible. Continuous topology, anatomically correct scapula/humerus/radius/carpus and femur/tibia/hock chains, skin weights and body deformation are required before photographic or close-up acceptance. The current file is an original procedural master; it is not the contract's authored Blender master.

Also outstanding: direct study of cleared anatomy plates (research agent located public-domain Stubbs metadata; no visual matching is claimed here), measured movement, start/stop/turn/trot, UVs/PBR coat and hair, close silhouette/landmark reference review, LODs/compression parity, distant-population budgets, fitted sourced tack, reins, rider and vehicle integration, mounting/riding behavior, terrain contacts, licensing/provenance registry integration and project contract acceptance. No production scene placement is enabled by this study.
