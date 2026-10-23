# T-2377: Hogan's first picture-based geometry increment

This is a rebuilt first increment, not a completed image match. The original T-2377 acceptance remains open. `cameron-1833.match.json` is reviewed `differs`, and its camera stays in this research directory while provisional. Do not move it into accepted reference-view data or mark it matches without resolving the listed differences.

## Visible change

The generic front's two flanking windows and centred door become one sash and an off-centre doorway; a small framed opening appears on the visible gable, and one stack moves to a roof-piercing ridge station. These use existing consumed log_dwelling parameters; no generator/default changed. The documented 45 by 20 ft footprint, position, bearing, dates and use remain unchanged. All newly chosen metric sizes/stations are reconstructed, bounded by Cameron's depicted arrangement; the count of one visible chimney is inferred. L-hogan-pictured-openings-2377 records the choices, including the reconstructed 0.65 m square section and generic 0.95 m-high ridge-stack head and the unresolved gable-light treatment.

The first actual paired close-up exposed misplaced and narrow openings. The final reconstructed stations are door8.45 m and sash11.55 m from minimum-u, with widths1.45/0.75 m; the narrower stack section is0.65 m. The revised six-point review camera has16.099 px point RMS and26.809 px maximum residual, rather than claiming a consistent photographic solve. `camera-fit.json` records the manually selected wall points, projections and parameters. An independent visual review confirmed an incremental improvement while retaining the open differences below.

## Source and grade

The actual local halftone's caption reads Chicago's First Postoffice in 1833, credits Edgar S. Cameron's painting and the Chicago Historical Society, and locates it near the later Lake Street bridge's east end. Source `cameron_c1900_first_post_office` preserves that credit, the Commons locator, the local inventory's circa1900/public-domain attribution and its limits. The local image/caption were inspected; the inventory's date/rights attribution is not represented as a freshly verified remote catalogue. It supplies appearance rather than surveyed geometry or proof of survival/use on 1 July 1835.

An explicit pictured ruling makes the compiler derive the structure grade attested because a reasonable whole-building picture exists (rule12). Individual attribute grades and the survival/date limits are unchanged; that grade is not a completed-match verdict. The generated Images entry credits Cameron and the Chicago Historical Society and links to the holding locator.

## Before and after

- `before-side-by-side.jpg`: actual pre-change committed GLB, base7a9123e9d6986fc3ea7b8912bd78f6278b0350f7.
- `cameron-1833-side-by-side.jpg`: actual rebuilt master and the same numeric camera/intrinsics; the portable photo path differs from the original temporary camera only in path spelling.
- `cameron-1833.json`: reconstructed review pose, no historical camera/measurement claim.
- `cameron-1833.match.json`: current mesh/camera/photo hashes and the full remaining differences.

The open doorway, gable glazing/hatch, chimney detail, camera/proportions, log/roof texture and tone remain unresolved. No match ticket is closed by this increment.

## Reproduction

In chicago/4d, use the exact binary from generators/blender.pin (4.5.3, checksum verified), `blender -b -noaudio --factory-startup --python generators/build.py -- --only hogan_store --wrote /tmp/hogan-wrote.txt`, then `npm_config_cache=/workspace/shared/npm-cache tools/web_derivatives.sh --only hogan_store__log_1831.glb`, `python3 tools/compile_liberties.py`, `python3 tools/generate_entrances.py`, `node tools/rederive.mjs --tail tools/compile_scene.py`, and `PW_EXECUTABLE=/usr/bin/chromium node tools/photo_match.mjs docs/RESEARCH/hogan-picture-match-T-2377/cameron-1833.json --out docs/RESEARCH/hogan-picture-match-T-2377`. The working environment is an interactive cloud workspace; the system Blender4.3.2 was not used. The pinned binary was downloaded to /workspace/shared/blender-dl and verified against the committed SHA256. On an improve runner, obey the no-Blender rule and use the supported content-build workflow.

Validation and in-app checks are recorded in STATUS and the GitHub recovery checkpoint when complete; this README does not claim unrun checks.
