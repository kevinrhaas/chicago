# Glessner chimney shafts and caps — T-2222

Target: exterior and courtyard, 1904-07-01. Seven existing stacks are retained.
The two middle/south street stacks now straddle the established main ridge;
their shafts and flashing meet both roof pitches. Street caps use a thick flush
masonry course and a shallow belt, with open, recessed flue mouths. Service
stacks have brick shafts and plain pale masonry caps.

## Evidence and uncertainty

HABS measured sheets 4 and 6 supply the two roof-contact readings and street cap
proportions. Taylor 2135 (c.1887–1889, public domain) independently corroborates
the street silhouettes. The reference grids and datum receipt are in `reference/`.
The measured drawing's printed heights establish the scale; the inferred plan
bounds have approximately ±0.3 ft uncertainty. Raster coordinates are not survey
precision. All existing stack top heights, north/south positions and stack counts
are retained. `stack-register.json` separates existence from finish confidence.

The prior middle and south footprints lay east of the corrected ridge, leaving
overlong exposed shafts. Revised transverse bounds are W15.55–21.8 ft (middle)
and W14.18–21.8 ft (south). Independent east-roof toe readings are 42.488 and
41.128 door-datum ft; the retained roof predicts 42.485 and 41.129. The reverse
roof toe bounds W21.8. Two crossing shaft faces are split at the ridge so no
low straight chord cuts through the high roof.

The 1888 Inland Architect plate was re-viewed to check retained stack existence;
its digital rights remain unresolved, so it contributes no new traced geometry
or copied pixels. In particular, Taylor obscures the great stack; that does not
justify removing it. The service stacks remain explicitly reconstructed for
1904: modern views do not establish their date or exact historical plan.

Two credited modern references by w_lemay, photographed October 26, 2024, are
added to the Prairie library and mobile Images tab. Commons IDs 159537051 and
159537085 show brick service shafts and pale caps. They are CC BY-SA 2.0:
https://creativecommons.org/licenses/by-sa/2.0. Native-original requests returned
HTTP 403; the reviewed 1920-pixel-request display renditions supplied the library
copies. Their metadata records actual downloaded dimensions and checksums.
Modern roof vents, paint, wrapping, paving and planting are not historic facts.

## Reconstruction choices

`stack_finish` separately records 448 mm street cap courses, 229 mm belts,
220 mm service caps, 8 mm joints, 12 mm shallow top fall, 300 mm bounded flue
widths and 600 mm depth. Flue counts and hidden details are reconstructed, not
measured. No pots, projecting slabs or side vents are added. Existing abutment
flashing follows each roof plane; a duplicate rectangular base band is removed.
The owner's granite colour and dark glass remain unchanged.

Full carries individual service bricks and cap top joints. Light preserves the
same shaft silhouette, cap thickness, exterior cap joints, mouth size and depth;
it omits millimetre-scale service-brick relief, interior cap-joint sides and fine
joints within the cap's top bed. It uses the existing metric brick material and
one continuous dark flue lining. Complete Light generation measures 199,967
triangles against the unchanged 200,000 limit. Earlier over-budget candidates
were rejected; the final canonical package contract confirms that count.

T-2221's drainage meshes were documented as reconstructed but accidentally
emitted confidence 0 (attested). This rebuild corrects them to 1 (reconstructed),
with a regression assertion. New stack finishes also emit 1. Geometry and
colour are not changed by that correction.

## Validation

Functional geometry checks pass in Full and Light: seven stacks; both roof
pitches; no coincident or zero-area triangles; vertical rays pass through each
mouth to its 600 mm deep floor; cap tops retain their declared elevations.
The north-tower and rainwater regressions pass. Canonical bake, asset contracts,
paired browser views and all five fixed historical comparisons are complete.
Full/web each contain 1,314,803 triangles; Light contains 199,967. All package
hashes match. Repository preflight and exact-commit CI are required before
merge; their receipts are maintained on the PR.

Baseline captures in `before-full/` and `before-mobile/` use fixed six-camera
positions, including a roof-side north-cap view unobscured by foliage. The
original north-gable street view is foliage-obscured and cannot certify the cap.
The west-service Full baseline already exceeds the scene budget (402 calls,
4,694,719 submitted triangles). T-2227 owns existing scene-budget failures;
no thresholds or cameras will be relaxed to conceal them. Chromium uses
SwiftShader, so these are browser correctness/budget checks, not hardware FPS.

All five whole-house photo-match records remain `differs`. Their remaining
silhouette, opening and material differences stay with T-2228; completion of
this component must not be described as whole-house photographic acceptance.


## Browser and publication receipts

All twelve paired Full/Light observations preserve the same camera and budgets.
There are no page errors, failed requests or scene problems, and no new budget
failure. Existing failures remain failures: the west-service and north-cap-clear
Full views, and the north-cap-clear Light view. T-2227 retains them.

| Detail / view | Before calls / triangles | After calls / triangles | Budget after |
| --- | ---: | ---: | --- |
| full / street-stack-overview | 228 / 3,864,309 | 228 / 3,826,385 | pass |
| full / middle-stack | 223 / 3,779,145 | 223 / 3,741,221 | pass |
| full / north-gable-cap | 229 / 3,905,268 | 229 / 3,867,344 | pass |
| full / service-east-stack | 226 / 3,742,867 | 226 / 3,704,943 | pass |
| full / service-west-stack | 402 / 4,694,719 | 402 / 4,656,795 | existing failure |
| light / street-stack-overview | 136 / 964,894 | 136 / 965,710 | pass |
| light / middle-stack | 118 / 843,241 | 118 / 844,034 | pass |
| light / north-gable-cap | 130 / 901,591 | 130 / 902,450 | pass |
| light / service-east-stack | 100 / 639,780 | 100 / 640,012 | pass |
| light / service-west-stack | 243 / 1,176,472 | 243 / 1,176,728 | pass |
| full / north-cap-clear | 400 / 4,691,199 | 400 / 4,653,275 | existing failure |
| light / north-cap-clear | 284 / 1,581,241 | 284 / 1,581,587 | existing failure |

The north-cap-clear Light baseline was separately captured on the unchanged
T-2221 published asset (SHA-256
`dfd630e0e4322604da2f5c989c49f8df1c905dc2b8bb00516dcefa252211869a`),
before the new package was published. Its existing failure is not a new result
hidden by changing the camera. Street north-gable foliage still obscures the
cap, so the unobstructed roof-side view supplies its visual acceptance instead.
The cap has deep visible mouths, connected top/side joints and a flush course;
the courtyard views show brick shafts and continuous roof-following flashing.
Confidence display was exercised in both tiers; dark glass remains the default.

The mobile Images pane loads 123 credited tiles. Both new references
are found by title with w_lemay and CC BY-SA 2.0 credits. The new chimney liberty
opens on the mobile card and states the reconstructed details. The four image
bytes published by [image-store PR #3](https://github.com/kevinrhaas/chicago-images/pull/3)
match the recorded SHA-256 and byte lengths. The original seven unavailable
historic records remain unavailable; modern additions do not count as recovery.

The early Taylor comparison visibly shortens the two overlong street shafts
without refitting its camera. All five comparison records were re-viewed on the
same canonical web hash and retain `differs`; the individual remaining issues
are recorded in each match file and `photo-review-notes.json`.
