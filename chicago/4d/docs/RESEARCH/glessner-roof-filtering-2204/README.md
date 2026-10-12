# T-2204 — Glessner roof filtering

T-2203 established the 6-inch width / 5-inch exposed course. This pass changes
sampling, not the physical model or its historical evidence. The 1904 inference
and source limitations remain those in [T-2203](../glessner-roof-tiles-2203/README.md).

## Cause and implementation

Matched diagnostic renders retain the broad ripple pattern with shadows disabled,
normal maps disabled, anisotropy raised to eight, and the camera near plane moved
out to five metres. Texture filtering and depth precision alone therefore do not
resolve the fine geometric course edges.

The generator adds `_ROOF_DETAIL`, the exposed course in metres, only to tile
fronts/noses and Light's reduced course lips. Beds, crests, copper and other
surfaces carry zero. Both assets keep every original position, normal, UV,
confidence value and index: [byte-for-byte comparison](geometry-unchanged.json).
[Physical checks](physical-coverage.json) retain 244 hosts, 63,518 Full tiles,
199,656 Light triangles, and the same 2.4384 × 2.032 m mapped repeat.

The renderer blends unresolved relief over the existing opaque tiled bed across
6–24 projected course pixels. The drawing-buffer height and projection matrix
set that footprint, so changing resolution or field of view cannot change the
physical tile size. No discrete distance cutoff or random dither is used. Zero
tagged vertices protect the crest silhouettes. Unfaded crests and near relief retain depth writes for correct self-occlusion;
fully filtered relief is discarded so the bed retains depth and chimney shadows.
Relief still casts its physical shadow. Clay maps use trilinear mipmaps
and anisotropy eight, clamped by Three to device support. No new texture is loaded.

## Review method

`PW_EXECUTABLE=/usr/bin/chromium QA_OUT=<directory> node tools/qa_glessner_t2204.mjs`
loads the real published 1904 app, Full at 1280×800 and Light at 390×780. It renders
six consecutive camera positions on each near, street, overhead and northeast
path, separated by 25 mm laterally, with matched before/after lighting. The UI
simulation is paused; these are successive rendered moving-camera samples, not
an assertion of real-time video speed. The baseline took additional identical
warm-up renders per sample; the final harness warms each path's first pose.

The final harness also switches Full → Light → Balanced → Full on desktop and
Light → Full → Balanced → Light on mobile, checking the imported sampling channel,
filtering, budget and absence of page errors. The motion pass records CPU submission through `gl.finish()`, which did not block
for GPU completion on this Chromium runner. The separate `QA_BENCHMARK=1` run
forces completion with framebuffer `readPixels`, also recording end-to-end
capture time. These are SwiftShader software measurements, not phone hardware
FPS. Baseline timings overlapped the asset rebuild and cannot establish a speedup.

`QA_REVIEW=1` runs the complete 70-capture review and detail switches in one boot per viewport.
`QA_PULLBACK=1` adds eleven matched-target poses from 3.4 to 50 metres to inspect
the gradual transition. The 6–24 pixel thresholds are renderer sampling policy,
not a historical dimension. Adjacent-frame luminance differences contain real
parallax and texture motion as well as aliasing; they are not a pure shimmer metric.

The known folded copper connector remains held under T-2220. This work does not
claim the whole house has reached the programme's photographic-quality target.

## Moving-view results

All 48 final motion captures and six Full/Light/Balanced switches pass with zero
page errors, failed requests or budget overruns. Draw calls, triangle counts and
texture counts match the baseline for these camera paths. The comparison records
[raw observations](browser-validation-after.json) and
[native-resolution motion measurements](motion-and-costs.json).

Mean adjacent-frame roof luminance change (0–255) drops from 3.778 to 0.177 in the
desktop street view, 1.218 to 0.319 overhead, and 1.608 to 0.189 northeast. The
corresponding mobile reductions are 0.757 → 0.073, 0.318 → 0.187, and 0.180 → 0.109.
Near-view change rises slightly (desktop 2.825 → 2.935, mobile 1.914 → 2.048): the
close tile/grain detail is retained, not erased to minimize a motion number.

Animations repeat the same six poses forward/back at 250 ms per image. Desktop
panels are reduced to at most 620 px per half for review; all measurements use
native pixels, and the linked stills retain the full viewport resolution.

| View | Full desktop | Light mobile |
| --- | --- | --- |
| Near | [Motion](motion-desktop-near.gif) · [Still](after-desktop-near.png) | [Motion](motion-mobile-near.gif) · [Still](after-mobile-near.png) |
| Street | [Motion](motion-desktop-street.gif) · [Still](after-desktop-street.png) | [Motion](motion-mobile-street.gif) · [Still](after-mobile-street.png) |
| Overhead | [Motion](motion-desktop-overhead.gif) · [Still](after-desktop-overhead.png) | [Motion](motion-mobile-overhead.gif) · [Still](after-mobile-overhead.png) |
| Northeast | [Motion](motion-desktop-northeast.gif) · [Still](after-desktop-northeast.png) | [Motion](motion-mobile-northeast.gif) · [Still](after-mobile-northeast.png) |

The early 2–8 pixel fade left intermediate-distance course bands. The final
6–24 interval accounts for noses becoming subpixel well before a whole course
does. Diagnostic controls show the original pattern with
[shadows disabled](diagnostic-no-shadow.png) and [all clay maps removed](diagnostic-no-maps.png).

## Pullback and rendering cost

The final eleven-pose pullback passes in both viewports: [Full contact sheet](pullback-desktop.png),
[Light contact sheet](pullback-mobile.png), and [raw GPU-readback receipt](pullback-and-gpu-cost.json).
Native middle-distance examples: [Full 7 m](desktop-pullback-7-0.png),
[Full 12 m](desktop-pullback-12-0.png), [Light 7 m](mobile-pullback-7-0.png),
and [Light 12 m](mobile-pullback-12-0.png). The mapped courses remain visible as
physical noses become unresolved; the earlier broad intermediate bands are absent.

| Cost | Full desktop | Light mobile |
| --- | ---: | ---: |
| Matched-path draw calls, before and after | 54–60 | 53–55 |
| Matched-path peak triangles, before and after | 2,507,196 | 447,699 |
| Matched-path texture objects, before and after | 112–120 | 124–128 |
| Additional GPU sampling attribute | 2,137,844 bytes | 89,196 bytes |
| Additional web GLB bytes | 36,908 | 4,648 |
| Pullback median render + forced readback | 6,740 ms | 1,325 ms |
| Pullback render + readback range | 4,809–8,726 ms | 1,119–1,660 ms |

The last two rows are deliberately **software-renderer timings**, after draining
each pose's warm-up frame, across eleven different camera distances. They are not
hardware FPS or a before/after performance claim. Draw, triangle and texture
counts are unchanged at matched poses. Sampling asks for eight anisotropic taps
rather than the imported maps' default one; the GPU also reads the new scalar
attribute and blends the relief over the same existing bed. Neither tier gains
a texture, an image, or a triangle.

Reproduce the cost/pullback run with `QA_PULLBACK=1 QA_BENCHMARK=1` plus the normal
QA command. Reproduce this dossier's charts with:

```
python tools/measure_glessner_t2204.py --before <before> --after <after> --pullback <pullback> --output <dossier>
```

Animations use a fixed palette without dithering; the measurements use original
RGB screenshots. The diagnostic pilot also caught a harness-only byte-count
read of a CPU array already released on mobile; the final harness counts the
retained attribute length instead. Both final viewport runs complete successfully.

## Repository validation

- [Published renderer regression, both viewports, stage 8](smoke-8.log): **36 passed,
  0 failed**, zero page errors. This covers the shared building batching/material
  path. It is a scoped regression run, not the complete 14-stage suite.
- Final Glessner review: **70 captures and six detail switches**, zero page errors,
  failed requests or budget overruns, with the final depth-writing/discard behavior.
- Physical geometry/coverage and structure-version lifecycle tests pass.
- The final integration includes dev's subsequent family-assignment metadata;
  that integration changes no Glessner geometry or renderer code.

The full working-tree preflight passes: **804 checks, none red**. Its 329 deliberate
self-tests are included in that pass. The PR receipt records the additional
changelog and ticket-ID checks against the committed branch range.
