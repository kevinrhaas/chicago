# T-2172 — courtyard tower proportions

Owner follow-up to T-2157, 8 October 2026. The supplied courtyard photo shows
the upper tower glazing related to the north-wing upper windows, with a shallower
copper cap than the current application. The model had placed the 3.1-ft glazed
band at 17.4–20.5 ft ng, below the wing upper windows at 19.5–24 ft ng.

Raise the band intact by 3.5 ft to 20.9–24 ft; extend the masonry to its sill.
Keep the copper apex at the established 34.1-ft north-wing ridge, its forward
plan position, flared apron, tiled connector and ridge crests. The cap rise
changes from 13.6 to 10.1 ft (25.7% shorter). This is an owner-directed proportional
reconstruction, approximately +/-1 ft, not a measured historical elevation.
The photograph has perspective and is not used as a survey or photographic texture.

HABS IL-1015 photograph 5 (courtyard view, circa 1923) shows a continuous band
with two pane rows and several vertical lights per facet. Retain those period
divisions rather than adopting the modern photograph's replacement broad panes.
The principal sash keep their 9.3-ft sills but their heads rise from 14.5 to
16.5 ft. This yields 7.2-ft lights, 2.32 times the 3.1-ft upper band; both supplied
and historical views show approximately 2–2.5 times, rather than the former
1.68. It also avoids extending an oversized brick spandrel beneath the raised
band. Facet positions, sash layout, basement openings, plan and main ridge remain
fixed. These principal-window heights are reconstructed (+/-1 ft).

## Validation and recovery

- Pinned Blender 4.5.3 rebuilt the canonical master. The full/light derivatives
  and the verified three-file recovery archive are rebuilt. Comparison versions
  retain their original geometry.
- 1,800 independent stable-roof samples and 1,200 courtyard roof samples pass.
  The band head equals the north-wing window head; its height and ridge stay fixed.
- The actual published 1904 app boots at desktop 1280x800/full and mobile
  390x780/light. Six fixed cameras have zero page, HTTP or loader errors.
  Desktop: 93–99 draws, 3,385,565–3,408,061 rendered triangles.
  Mobile: 52–53 draws, 469,004–471,698 rendered triangles. All existing budgets pass.
  The light asset itself has fewer than 200,000 triangles.
- PNGs and browser-validation.json retain the camera coordinates and observations.
  These are normal application materials, lighting and geometry; the animation
  loop is paused after entry for reproducible views. This is not an FPS benchmark.
- Repository preflight and newer-dev integration are pending. An initial gate
  caught concurrent local publishing, missing derived liberties, the browser
  path environment convention and a newly closed dev ticket. Those are being
  corrected before merge; no claim of a green whole-site browser suite is made.

Branch: steward/glessner-tower-proportions. Recovery checkpoints f08f65e4
(study), a2205615 (band/assets), 9eeaf4a7 (final sash/assets and six app views).
Canonical parameters: data/structures/glessner_house.json. Rebuild with the
pinned Blender using generators/build.py --only glessner_house, then
tools/web_derivatives.sh --only glessner_house__as_built_1887.glb.
The derivative producer repacks the recovery archive. Compile sidecars and
publish sequentially before running tools/qa_glessner_t2172.mjs, which accepts
PW_EXECUTABLE. Complete tools/preflight.sh before merging into dev.
