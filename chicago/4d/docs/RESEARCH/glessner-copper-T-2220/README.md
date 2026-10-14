# Glessner courtyard copper — T-2220

The old north-return connector had a folded, self-overlapping fan and an edge
about 0.703 m above the adjoining north roof. Sorting its arc by x interleaved
points around the western tangent: five faces wound backward. A broad unsupported
copper rectangle and its diagonal gutter crossed the upper-window line.

The repair uses a low hood over the hall bow, intersected with the north and east
roof planes. The two host surfaces are cut by the hood's convex footprint; every
exposed junction shares the same three-dimensional boundary. The projecting
curved edge has a shallow fascia and soffit. The north roof continues as tile
to the bow, with a straight gutter rather than the spurious inclined run.

## Evidence and uncertainty

[Native HABS reading](habs-bow-hood-reading.json) records the unrestricted sheet-4
scan, exact source hash, picks and scale. The relative rise is 1.78 ft, rounded
to 1.8 ft; the high point at S26.81 agrees with the actual ell at S26.83. This is
a 1963 survey carried back with the existing fabric evidence, not a 1904 roof
survey. The current bow eave remains fixed. The older absolute section datum
and eave-height discrepancy stays in T-2228; changing a relative hood rise
does not resolve it. [Former fan diagnostic](original-fan-diagnostic.json)
retains the pre-repair measurements.

The five newly reviewed photographs by w_lemay, October 26, 2024, are credited
in `stream-glessner-courtyard-2024.json` and the separate image store, under
CC BY-SA 2.0. They show complementary views from one modern visit. They are not
five independent historical witnesses. The dining close-up and hall-bow views
corroborate seams, laps and surviving low-hood form. Their bright-green patina,
replacement glazing, planters and paths are not copied into July 1904.

The earlier c.1923 HABS05 and 1948 Florian images remain qualitative cross-checks
under their recorded rights restrictions. No source-image pixels or traced
photographic patterns enter the generated materials. Individual 1904 sheet
joints, hidden stock and colour remain declared reconstructions; see
L-glessner-copper-2220.

## Construction and verification

Radial standing seams and transverse laps sit on the actual copper planes.
The dining roof retains its hip, apron, ridge, window positions and dark-glass
default; only stock and low laps are refined. Procedural patina varies gently
along radial drainage coordinates, without directional baked shadows.

The north-wall closure is local to the hood: the brick eave remains level outside
its footprint, rather than interpolating a false slope across the courtyard.

The independent spatial check rejects reversed/overlapping fan faces, warped
sheets, floating cut edges, tile holes that differ from copper coverage, and
raised seam stock. It samples 2,400 footprint points and checks both detail
levels. The complete engine-neutral roof check currently reads 199,186 Light
triangles against the unchanged 200,000 limit. Light reduces only tiny gutter
cross-section curves and seam stock; roof outlines and drainage paths agree.

The saved baseline covers ground, the owner angle, close oblique, overhead and
dining views in Full, Balanced and mobile Light. Full and Light pass all five.
Two Balanced views already exceeded 330 draw calls (334 / 332), recorded on
T-2227. No baseline page errors or failed assets occurred. Rendering counts
under SwiftShader are not physical-GPU frame-rate claims.

The rebuilt package passes K01: 1,334,432 Full/Web triangles and 199,186 Light,
zero coincident faces in all three tiers, with matching scale, origin and metric
UV checks. All five Full and mobile Light app views pass their unchanged
budgets, with no page errors, loader problems or failed assets. The mobile image
tab loads all 121 credited photographs, including the five new w_lemay images
with their CC BY-SA attribution. Balanced retains the same two pre-existing
draw-call failures: owner angle334 and dining332 against330; all five triangle
counts decrease and no draw count increases. This remains the T-2227 finding,
not a claimed passing Balanced budget. [Matched costs](matched-browser-costs.json).
Whole-house reference views retain their unresolved differences for T-2228.
Repository preflight passes: 879 checks, none red (356 intentional gate self-tests).
Canonical CI and published smoke tests must pass on the committed source before merge.

## Reproduce the review

Run the selected Glessner build, then its canonical web derivative and K01
measurement using the ordinary repository pipeline. With the published mirror
current, the fixed-camera harness is:

```sh
PW_EXECUTABLE=/usr/bin/chromium QA_VIEWPORT=desktop node tools/qa_glessner_t2220.mjs
PW_EXECUTABLE=/usr/bin/chromium QA_VIEWPORT=mobile QA_IMAGES=1 node tools/qa_glessner_t2220.mjs
PW_EXECUTABLE=/usr/bin/chromium QA_VIEWPORT=balanced node tools/qa_glessner_t2220.mjs
```

`QA_OUT` chooses the capture directory. The Balanced harness deliberately retains
its normal budget assertion; its two baseline failures are not suppressed.
The new `habs04-hood-section` reference camera uses the same independent scale and
ground control as the wider terrace section. Its before comparison is in `before/`.
Five published reference-file HTTP/hash receipts are in
[published-reference-files.json](published-reference-files.json); the separate
image-store PR is [#2](https://github.com/kevinrhaas/chicago-images/pull/2).

## Matched courtyard views

All captures use the same cameras and normal July 1904 app settings. Full
[ground before](before/desktop-court-ground.png) / [after](after/desktop-court-ground.png)
and [owner-angle before](before/desktop-owner-angle.png) / [after](after/desktop-owner-angle.png)
show the removed folded rectangle, continuous north tile and lower curved hood.
The section comparison retains its absolute-height disagreement explicitly in
`data/reference_views/glessner_house/habs04-hood-section.match.json`.
