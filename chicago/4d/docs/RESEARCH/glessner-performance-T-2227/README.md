# Glessner browser quality and performance — T-2227

Full, Balanced and the complete July Light/mobile matrix pass their existing scene budgets. The final seasonal fallback and summer restoration are pixel-identical.
Exterior/courtyard, 1904-07-01; owner grey-greige granite and dark glass retained.
No historical geometry, source rights, image-gate verdict or scene budget is changed.
T-2228 remains responsible for the visible photographic discrepancies.

## Reproduced failures

The integrated baseline has 147 building material batches. The complete fifteen-view
Light capture fails eight of its unchanged 330-call / 1,270,000-triangle limits.
The retained Full baseline is partial: eight captures survived an interrupted run;
a separate startup retry timed out. It is not a completed Full acceptance matrix.
The two Balanced baseline stills survived, but their motion run was terminated after
907 seconds without a result. Those stills are partial evidence, not a passing run.

The machine uses Chromium 154 with SwiftShader, four CPU cores under the container's
quota, and a 16 GiB memory limit. Counts and pixels are directly measured; software
rendering is not a physical-GPU frame-rate claim. Baseline background work is declared
in its contention record. It does not support a quiet before/after timing comparison.
Motion timing must include animation-frame cadence and wall elapsed time: the duration
of a JavaScript `render` or `gl.finish` call alone did not describe the observed cadence.

## Runtime changes

Inspection material batches can share a decoded texture Source only when their full
sampler, effective UV matrix and material state agree. Known shader patches register
both their closure values and preceding hooks. Unknown hooks, custom texture types,
video and render targets stay isolated. Color and unmapped roughness retain their
existing exact per-vertex representation. Other scenes retain their existing material
lifecycle. This reduces the measured building batches from 147 to 51.

Full Glessner opaque surfaces use the same 4 m by 2 m spatial pieces already used
in the other inspection tiers. Transparent tile relief retains its original draw
groups because repartitioning changes its blend order at the ridge. Every triangle and attribute remains; each camera can reject pieces
outside its own frustum. The fifteen-view Full capture and its movement/detail round trip pass, as reported below.

Light uses conservative opaque-surface visibility filtering. Its occluders are
actual building triangles, including neighboring buildings visible from elevated
courtyard stands. Unknown shader hooks and surfaces with transmission, alpha rejection, displacement,
depth bias or clipping are excluded. Small neighboring faces below 4 square metres
are omitted from the candidate set; the inspected house retains finer faces.

A complete instance box must project inside one inset polygon and lie behind its
plane. A source triangle crossing the near/far plane is clipped to its actual visible
polygon. Target boxes crossing the near plane or viewport boundary fail open. Visible
viewport coverage ranks the bounded set of 64 candidates. Two pixels plus a metric
rounding allowance inset each polygon. No coverage is invented across an opening or
between triangles. Main-camera draw ranges alone are filtered; shadows, original
geometry, instance visibility and picking remain intact. Hidden or dithered evidence
bands, changed backing transforms/geometry/hooks and global clipping fail open.

## Completed Full result

All fifteen Full stills pass, with a maximum of 219 calls and 4,289,410 triangles
against 360 / 4,600,000. All thirty moving samples pass, peaking at 4,004,441 triangles.
Full -> Light -> Full restores the exact material/instance census and a pixel-identical
whole canvas at the held camera. The complete scene submission totals are not identical:
217 calls / 3,931,007 triangles before versus 216 / 4,084,455 after; both pass.
The exact census assertion covers building material/instance groups, not every dynamic
context layer. No page errors or failed requests occurred.

## Completed Balanced result

All five Balanced stills and thirty moving samples pass the unchanged 330-call /
2,535,000-triangle limit. Stills peak at 218 calls / 2,328,422 triangles; motion peaks
at 2,382,548 triangles. The two retained baseline cameras had 401 / 403 calls at
exactly the same triangle counts; their final images differ only in 35 minimap pixels.
No page errors or failed assets occurred. The moving run took 1,175,789.8 ms, with
147.8 ms median JavaScript step time, 410.7 ms p95, and 35,368.65 ms median RAF cadence.
These are software-renderer observations, not physical-GPU performance promises.

## Light result and rejected trials

The complete fifteen-view published Light run passes all fifteen fixed cameras within the unchanged
330-call / 1,270,000-triangle ceiling: maximum 171 calls and 1,178,966 triangles.
All thirty moving samples pass too, peaking at 955,585 triangles. There are no page
errors, failed requests or loader problems; dark glass remains selected. All eighteen
whole-PNG on/off comparisons are exact, including evidence mode and hidden inferred /
reconstructed bands. Picking and restored draw counts agree at each comparison.
The published baseline and this candidate retain identical bytes for all 882 GLBs. All fifteen
baseline/candidate cameras, projections and exposures also agree exactly. Fourteen
Light images differ only inside the minimap; the northeast image additionally retains
three isolated scene-pixel differences, recorded with their exact coordinates. This
source-batching comparison is distinct from the eighteen exact visibility on/off pairs.

An earlier wall-only trial passed selected counts but changed three bow pixels at the
left viewport edge. A subsequent dining view changed fifteen edge pixels. Retaining a
single painted material class was insufficient and was rejected. The final general
rule retains every target box crossing the viewport boundary; it does not special-case
a material or hide the image difference with a tolerance. The underlying cause of the
small edge contributions remains unproven. Shadows were unchanged in the diagnostic.
A 10 m railway-chunk trial and convex-face union trial were also rejected.

The first Full trial split transparent roof relief into 471 pieces. Its north view
changed a band along the roof ridge, up to 73 channel levels. That run was interrupted
and rejected. Full now partitions only opaque Glessner surfaces; the transparent roof
keeps its original three draw groups. Against the eight retained Full baseline views,
the corrected run changes 81 common minimap pixels plus zero to ten isolated scene
pixels per image. The former ridge band is gone; cameras, projection and exposure are
identical. This is not a claim of whole-image Full bit identity. The full-resolution
before/after images and pixel comparison preserve these small differences.

## Reproduction and limits

Run from `chicago/4d`, using the normal published app and the committed camera plan:

```sh
tools/publish.sh
PW_EXECUTABLE=/usr/bin/chromium QA_VIEWPORT=desktop QA_BOOT_DETAIL=full QA_MOTION=1 QA_CHECK_BUDGET_LEVELS=1 QA_OUT=/tmp/glessner-full node docs/RESEARCH/glessner-performance-T-2227/qa-performance.mjs
PW_EXECUTABLE=/usr/bin/chromium QA_VIEWPORT=mobile QA_BOOT_DETAIL=light QA_MOTION=1 QA_OCCLUSION=1 QA_EVIDENCE_COMPARE=1 QA_REPEAT_FRAME=1 QA_OUT=/tmp/glessner-light node docs/RESEARCH/glessner-performance-T-2227/qa-performance.mjs
PW_EXECUTABLE=/usr/bin/chromium QA_VIEWPORT=balanced QA_BOOT_DETAIL=balanced QA_VIEW=owner-angle,dining-copper,north-court,terrace-foot,courtyard QA_MOTION=1 QA_OUT=/tmp/glessner-balanced node docs/RESEARCH/glessner-performance-T-2227/qa-performance.mjs
PW_EXECUTABLE=/usr/bin/chromium QA_VIEWPORT=mobile QA_BOOT_DETAIL=light QA_VIEW=north-tower,dining-leader,north-court,courtyard QA_OCCLUSION=1 QA_CYCLE_DETAIL=1 QA_SEASON_ROUNDTRIP=1 QA_MOTION=1 QA_OUT=/tmp/glessner-lifecycle node docs/RESEARCH/glessner-performance-T-2227/qa-performance.mjs
PW_EXECUTABLE=/usr/bin/chromium QA_VIEWPORT=mobile QA_BOOT_DETAIL=light QA_VIEW=courtyard QA_OCCLUSION=1 QA_SEASON_ROUNDTRIP=1 QA_REQUIRE_SEASON_FALLBACK=1 QA_OUT=/tmp/glessner-season node docs/RESEARCH/glessner-performance-T-2227/qa-performance.mjs
QA_COMPARE_DIR=/tmp/glessner-season QA_COMPARE_VIEWS=courtyard python3 docs/RESEARCH/glessner-performance-T-2227/compare-lifecycle-pixels.py
```

Run browsers sequentially. The recorded Balanced motion overlapped a short Python
comparison/contact-sheet job, declared in `candidate-background-activity.json`; it
is not an otherwise-idle benchmark. The optimized Light motion also overlapped a
3.50-second Python pixel comparison of its saved stills; the same activity record
declares that overlap. Counts include actual main and shadow submissions and are
reconciled against renderer totals. Texture storage is a source/sampler texel estimate,
not measured GPU memory: driver alignment, render targets and internal PMREM copies are
excluded. Light estimates 457,112,240 bytes with no unsupported formats. Its readiness
signal arrived at 112,923.9 ms; that signal is not a physical display's first presentation.
The Light thirty-frame run took 368,408.5 ms including warmup. Median RAF cadence was
10,455.75 ms; median measured JavaScript step cost was 286.2 ms and p95 1,072.2 ms.
These different intervals must not be substituted for one another or advertised as
hardware frame rates. The baseline was contended and lacks recorded cadence, so it
cannot substantiate a before/after frame-rate improvement.

The first two Light stills overlapped an automatically started Git repack. It was stopped
before motion; seven stashes were preserved. The contention receipt declares that scope.
An exec-server connection loss interrupted the first final Balanced run after three
saved within-budget stills. Those remain partial evidence in their own directory; the
replacement run uses the same frozen published JavaScript, verified file by file.

The complete Light capture precedes the exact season-wrapper recognition and the Full
transparent-roof exception; neither changes its initial summer/Light path. A later
two-condition guard excludes transmissive physical materials from opaque backing
eligibility. All 51 measured batches are MeshStandardMaterial, so that guard changes
none of their eligibility.

The first lifecycle run completed its count and picking assertions, but its pixel
comparison failed: the north-tower whole-page pair included the fading "Light detail
loaded" hint (3,827 pixels), and the winter canvas differed by one channel level at
one pixel. The original images and failed comparison are retained in
`candidate-lifecycle-before-cpu-opt/`; this is not accepted zero-difference evidence.
The repeated harness waits for the hint to reach zero opacity. All four July whole-page
pairs, repeated seasonal same-mode canvases and summer restoration are exact. Winter
on/off repeats the same one-pixel difference, so it is not accepted by a tolerance.
The final filter is restricted to summer; other seasons retain the complete normal
draw list. The final courtyard run verifies that fallback with ten exact unmodified PNG pairs:
July on/off, winter/summer on/off, repeated same-mode/restored-on canvases, and original
versus restored summer. Winter submits the same complete draw list with the toggle on
and off; summer restores the filter and its original counts. See
`season-fallback-validation.json`; the rejected winter differences remain recorded. Winter itself exceeds
the summer scene ceiling in both modes (1,525,376 on / 1,946,445 off triangles at
this courtyard stand); this supplemental seasonal round trip proves summer restoration,
not a claim that every season meets the July inspection budget.

That run also measured an excessive CPU cost inside Light batch callbacks. Box
projection now reuses double-precision scratch storage instead of allocating eight
vectors and eight arrays per tested instance. A deterministic audit compares 7,500
world boxes at the fifteen actual camera matrices against the preserved old function:
all Boolean visibility decisions agree (6,365 hidden / 1,135 visible). The numeric
operation order and all containment, depth and edge inequalities are unchanged.
The external microbenchmark is distinct from the subsequent actual-browser check.
In the optimized browser run, main-camera callbacks (sorting plus filtering) cost
132.9 ms at north tower, 64.7 ms at dining leader, 51.4 ms at north court and 54.8 ms
at courtyard. Corresponding filter-disabled callbacks cost 8.7, 9.5, 4.5 and 10.0 ms. These are single observations under
SwiftShader contention, not an isolated benchmark or a promised FPS improvement.
The filter still adds CPU work to reduce scene submissions; this limitation remains
visible in the report.
All four optimized July stills and thirty moving samples pass; motion still peaks at
955,585 triangles. Its wall duration is 285,443.3 ms, median JavaScript
step 115.7 ms, p95 590.8 ms, and median RAF cadence
7,614.40 ms. This is a separately timed run, not a controlled
before/after FPS comparison.

The final targeted Light run uses the reviewed dev fast-forward, the transmission
guard and allocation-reduced box projection. `candidate-cpu-opt-inputs.json` and
`cpu-opt-input-differences.json` distinguish these bytes from the earlier captures.
The fast-forward changes the 1904 index's excluded-structure list with new 1812
entries; no standing 1904 geometry changes. All non-1812 GLBs remain byte-identical.
Earlier fifteen-view images are not relabeled as captures of the later source revision.
The final season-only fallback follows the optimized four-view/motion run and changes
no summer visibility decision. Its input manifest and one-view seasonal regression
remain separate from those earlier measurements.

CPU checks exercise sampler/material isolation, slanting-wall depth, holes, clipped
triangles, viewport edges, instance transforms, evidence bands, shadow isolation, picking,
reversible disposal and precise season-hook identity. Browser pixels remain the visual
preservation proof. No source rights, historical-camera verdict, GLB or budget is changed.
Five historical views still read `differs`; final photographic corrections belong to
T-2228. This performance gate is the invisible-work exemption blocking that visible house.

Local preflight, exact-head CI, published smoke groups and deployment are recorded in
the ticket-linked PR; no pending check is represented here as passed.
