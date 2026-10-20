# W01 articulated wagon engineering prototype

Actual portable GLB and local browser fixture, outside the application checkout. **Not photographic-quality acceptance, not T-2793 completion, not integrated into any historical scene.** The body and running-gear proportions reuse the project's explicitly reconstructed static wagon values. Geometry is original procedural work; no unresolved-rights photograph pixels, tracing, textures or extracted measurements were used.

Regenerate with Python standard library only:

```sh
python /workspace/shared/period-transport-lab/wagon/generate.py --parameters /workspace/shared/period-transport-lab/wagon/parameters.json --output-dir /workspace/shared/period-transport-lab/wagon
```

The generator reads and preserves its input JSON. Main body dimensions, bed height, wheel radii, axle stations, track and tongue length are data-driven; smaller hardware and detail liberties are declared generator constants. Outputs are `wagon-w01.glb` and engine-neutral `wagon-w01.json`. Coordinates: metres, Y up, forward +Z, anatomical/travel left +X, ground root at axle midpoint for supplied symmetric parameters. Seat and hitch nodes are **empty proposed interfaces**, not proof of installed seating or working hitches.

Start the standalone fixture:

```sh
python -m http.server 8771 --directory /workspace/shared/period-transport-lab/wagon
```

Open <http://localhost:8771/>. Drag to orbit; wheel to zoom. Steering, travel, raised/resting tongue, roll/pause and reset controls exercise actual exported wheel/front-gear/tongue transforms. Turning uses a planar no-slip rear-axle path and separate wheel distances. It is not suspension/load/horse physics. Rolling loops reset at the slider bound; there is no production route controller.

Recheck while the server runs:

```sh
python /workspace/shared/period-transport-lab/wagon/verify.py
```

Validation uses installed Python Playwright and `/usr/bin/chromium`. It checks GLB framing, required unique transform names, finite accessor bounds, changed JSON input affecting generation without rewriting input, and actual browser loading/control behavior at 1280×800 and 390×780. Results: `validation.json`; screenshots: `preview-1280.png`, `preview-390.png`. This is a targeted prototype check, not the Khronos conformance validator or the full application release suite.

Geometry is batched by material within articulation frames: 22 mesh draws, 9,000 triangles, 678,852 GLB bytes at current parameters. Actual fixture render includes floor/grid: 24 draws without shadows; 46 with shadow pass. These are software Chromium receipts, **not physical-phone frame-time certification**. Empty original detail transforms remain for inspection; they have no draws. Geometry is flat shaded with original base-color materials, no image textures.

Ready-to-copy implementation files: `generate.py`, `parameters.json`, `wagon-w01.glb`, `wagon-w01.json`, `fixture.js`, `index.html`, `verify.py`, `README.md`, `LICENSE`, `LICENSES.md`. Local `vendor/` is a convenience copy of the existing app Three.js vendor; **reuse the app vendor during integration rather than copy it again**. Adjust import-map and loader import paths in the fixture when hosting alongside the app vendor. Generator CLI paths permit app `tools/` and `data/transport/` placement without patching generator internals.

Outstanding: cleared historical construction/anatomy reference, matched-camera photo review, calibrated color/material/wood grain, iron joinery refinements, historical seat/board hardware selection, steering collision sweep, independent GLB conformance validation, texture/LOD compression, real mobile performance, horse/harness coupling, suspension/load/brake behavior, source-registry and license entries on integration. Prototype steering is conservatively capped at ±8°; this is an engineering choice, not attested historical travel. Existing 80 static wagons are untouched.
