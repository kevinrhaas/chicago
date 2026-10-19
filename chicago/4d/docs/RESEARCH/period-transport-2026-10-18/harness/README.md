# Light breastcollar harness fixture — T-2801

This is actual original modular strap geometry and a portable GLB, not a completed historical model. Open `index.html` through the workspace HTTP server (currently port 8782), or load `light_breastcollar_harness_reconstructed_01.glb` plus `manifest.json` in the integrated transport workshop.

Rebuild: `python generate.py`. Export sanity: `python validate.py`. Browser check in this environment: `node validate-browser.cjs` (uses workspace Playwright and Chromium).

## Historical basis and rights

John Moore, *Fine harness, saddlery & horse clothing*, New York, 1891, printed p.1 “BUGGY HARNESS”, No.1, actually read as OCR at https://archive.org/stream/fineharnesssaddl1891john/fineharnesssaddl1891john_djvu.txt. The text specifies folded/stitched breast collar, breeching and girth, straight stitched 1-inch traces, flat reins, bridle with round check rein and plated front, with nickel or Davis rubber trim. We use that component family and **25.4 mm trace width**. This is light driving harness, not a riding saddle or full collar/hames harness.

US public-domain conclusion is based on the stated 1891 New York publication date. IA metadata has no explicit rights declaration; this is our rationale, not an institutional license grant. Only construction text was used. No plate, photograph, third-party geometry, texture or tracing is input to this generator. The original procedural code and generated geometry are offered CC0-1.0. This fixture does not establish that this exact harness was used by a named Chicago owner or in 1835. All dimensions except the trace width, all routing, buckle/bit shape, stitching omission, colors and pose are **reconstructed engineering choices**. Text identifies stitched/folded construction; this prototype does not model detailed stitching or a complete folded-leather cross section.

## Delivered geometry

32 modular meshes, 5,188 triangles, 396,960-byte GLB. Breastcollar and supporting straps, separate girth and short driving-harness pad, breeching and hip supports, two 25.4 mm traces, cheek/crown/brow/nose bridle straps, nickel fixture bit/bar and rings, flat reins, round check reins, terrets and small girth buckle frames. No UV/PBR texture pack; materials are plain metallic-roughness with no baked highlights.

Parameters are JSON-driven. All original centerlines live in `generate.py`; `parameters.json` exposes selected widths, thicknesses, rein endpoints, trace lengths, colors and head origin. Units metres, Y-up, +Z forward, +X anatomical left, root at horse fixture ground origin, no scale transforms. Individual named nodes permit replacement/refit. No source-specific mouthpiece or blinkers are asserted.

`manifest.json` holds 12 named attachment anchors and proposed horse-node mappings. Trace starts correspond to horse `socket_equine_trace_l/r`; bit anchors correspond to `socket_equine_bit_l/r`. Head-local bridle geometry is grouped under `harness_head` at the horse's rest head transform. Demonstration code actually copies the animated horse head world transform to the bridle group each frame; no horse files are edited. This follows rigid head motion only. Reins/check reins/traces remain independent static rest geometry, so motion visibly exposes attachment error. The integration host must solve/rebuild those paths from live endpoint transforms before claiming animated fit. Trace ends and rein-hand points intentionally extend aft to provisional vehicle/driver targets; the standalone view does not contain a vehicle.

## Verification and explicit open gates

`export-validation.json`: GLB header/length, finite float buffers, all scales 1, unique node names, required geometry components and explicit 25.4 mm trace-width metadata pass. `browser-validation.json`: Chromium/Three.js loaded all 32 meshes with zero page errors at 1280×800 and 390×780. Browser calls were 56 with the horse visible. Captures: desktop/mobile rest and head stress-test views; actual images visually inspected. One GLB only; no LOD derivatives or compressed web parity verified.

These checks establish usable prototype geometry only. Correct body fit/clearances, plate/photo matching, buckle construction, mouthpiece appropriateness, folded-leather/stitch detail, supported blinkers/check-rein routing, harness load path, realistic trace/breeching force response, rein slack/tension during animation and driving, skin binding, production textures/LODs, scene provenance integration and human/vehicle coupling remain **unpassed**. No riding tack, collars/hames, paired-team gear or animal-health suitability is claimed. The horse itself remains the separate provisional articulated fixture.
