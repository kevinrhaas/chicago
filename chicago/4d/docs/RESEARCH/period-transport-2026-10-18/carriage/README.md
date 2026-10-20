# C01 articulated open-carriage engineering study

Original procedural geometry, GPL-3.0-or-later. This is a visibly inspectable development study for a 1904 open passenger-carriage family, **not** a manufacturer replica, an identified Pullman carriage, a source-measured historical reconstruction, or a photographic-quality finished asset. No rights-pending image pixels, tracing, extracted proportions or textures were used.

Generate with Python 3 and NumPy:

```sh
python generate.py --parameters parameters.json --output-dir .
python -m http.server 8773
python verify.py
```

Verification uses installed Python Playwright and `/usr/bin/chromium`. The browser fixture reloads `carriage-c01.glb` through Three's GLTFLoader, so the controls exercise the exported model. It supports orbit/zoom, bounded front steering, wheel-distance rolling, differential wheel distances during turns, reset and play. There are no doors, horse, harness, humans or vehicle physics. Motion is a geometric demonstration on a flat plane, not a traffic actor.

The local `vendor/` copy is a standalone inspection convenience; reuse the app's existing Three vendor when integrating, and do not add a second vendor tree to the application repository.

## Interface and acceptance

Metres, Y-up, +Z-forward. Empty root at ground midpoint between axles. Four independent wheel pivots roll around local +X. Front steering carries axle, front wheels, shafts and single-horse hitch. Driver/passenger seat, boarding and ride-camera sockets are empty proposed attachment frames. There are three seating places in this study (one driver, two passengers); fit and boarding collision have not been tested against a portable human.

The default exported model has 9,744 triangles, 27 material batches, 49 nodes and 722,768 bytes. Desktop 1280×800 and mobile390×780 tests passed with zero page errors. Loaded wheel centers establish 1.90m wheelbase, 1.40m track, front radius0.45m and rear radius0.55m; wheel-ground error is below 0.000001m. Actual fixture rendering records56 total draw calls including shadow pass, floor and grid. Evidence is in `validation.json` and the two `preview-*.png` screenshots.

`parameters.json` is required input. Wheelbase, track, front/rear radii and shaft length drive the corresponding geometry. The body-envelope entry describes the fixed original furniture study; changing it alone does not resize furniture. Spring attachment geometry and guards are fixed for the default package, so changing running gear parameters requires renewed mechanical inspection and adjustment. The default ±12° steering limit is provisional: controls work and wheels visibly turn, but a swept triangle-collision test has not been completed. Do not treat it as a historical or collision-certified steering limit.

Before application promotion: document license/provenance/liberties in the application ledger; integrate behind an explicit development choice; validate body/gear swept clearances, harness/horse coupling without scaling either asset, portable-human seating/boarding, normal-map/material upgrades, LOD budgets and archival-source fidelity. The current material colors, leaf springs, lamps, guards and body details are independent unmeasured design choices. The eligible1875/1893 handbook/catalog metadata located by research does not imply plates were read or used.
