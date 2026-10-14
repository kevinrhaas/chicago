# Glessner curved hall terrace and steps — T-2218

The narrow straight stair is replaced by the measured curved terrace, a fan-shaped flight and a rounded stone end post. The upper landing ends at the first tread; it cannot protrude through the descending brick cheek. The coping has a top, underside, inner face and closed ends. The first tread meets the retained 1.679 m doorway threshold.

## Evidence and dating

HABS first-floor plan, sheet 2, and Section A-A, sheet 4, are unrestricted government drawings: [LOC il0118](https://www.loc.gov/item/il0118/), source habs_glessner_house_il_1015_drawings. They record 1963 fabric, inferred for the 1904 scene. The c. 1923 courtyard photograph (HABS photo 05) agrees qualitatively with the curved brick cheek, pale cap, rounded terminal and three exposed lower tread ends. Its rights remain pending; it supplies no copied pixels or traced geometry. The 1948 Florian bow/chimney photograph does not show the stair base and supplies no stair dimensions. The later institutional parking surface is excluded.

The source drawings themselves were read, including full-sheet context. The heavy curved line crossing the treads on sheet 2 is the **DN arrow**, not a stair boundary.

## Plan and section controls

[Plan calibration](glessner-courtyard-steps-T-2218/plan-controls.json) records native scan points and the affine fit to the printed 161 ft 3 in / 74 ft envelope. [Overlay](glessner-courtyard-steps-T-2218/plan-overlay.png) distinguishes traced upper boundaries from reconstructed lower ones. Values are scan measurements, not printed dimensions to these decimal places.

| Control | Before | Built target and source bound |
|---|---:|---|
| Terrace outside radius | 14 ft | 18.8 ft, ±0.25 ft; sheet 2 |
| Hall bow centre W/S | 28 / 27.7 ft | 27.8 / 28.8 ft, ±0.25 ft; sheet 2 |
| Hall bow outside radius | 10.1 ft | 10.6 ft, ±0.2 ft; the printed 9.5 ft is **inside** |
| Upper coping | 2.542 m | 2.564 m; independently traced section edge |
| Rounded post crown | absent | 1.554 m, ±0.06 m; section |
| Stair | 1.25 m wide, straight boxes | Traced upper fan, roughly 2.3–2.8 m wide; lower turn bounded by post/tower |
| Risers | nine | Nine 186.6 mm rises to retained threshold; source count nine ± one |
| Grille clears, S | equal angular shares | 30.37–34.05 / 34.71–38.35 ft, ±0.3 ft; section |
| Grille clears, height | 0.305–1.158 m | 0.549–1.426 m; section reading ±0.06 m |

The shared hall-bow plan correction makes the measured tread ends enter the wall naturally. It retains the T-2183 central door, light rows and floor height. The existing stair tower remains in place. The lower three tread boundaries are reconstructed where the section hides them behind the cheek; they are not claimed as exact traced historical joints.

The section detail uses the already documented separate scan scales (100.6 px/ft horizontally, 97.7 vertically; glessner_house_1904.md, section 14). [Source crop](glessner-courtyard-steps-T-2218/habs4-terrace-section.png) is native [3770,5000,6470,5950], resized to 1600 px wide with vertical rectification 100.6/97.7. The fixed comparison camera cuts the west wing at the sheet-2 A-A line, W=51.5 ft (local x=33.4518 m), keeping the east side. Its eye is 400 m west; residual perspective across the curved facade is about 1%. North-wall x1165 and grade y5858 are the control origins. The distant review camera uses a 350 m near depth and 500 m far depth: the ordinary 0.1 m near depth could not resolve the stone/brick separation at this distance and produced false interference. A geometry ray probe confirmed the lintel front before this camera correction. The initial plan post centre S46.2 ft and final section-reconciled S46.05 ft differ by 1.8 inches; the terminal shoulder projection remains explicitly unresolved.

## Construction and checks

Closed solid treads extend 40 mm below grade; 22 mm stone noses are bounded construction details. The 1.55 m terminal is cylindrical with a hemispherical crown. Exposed brick receives the same finish as the courtyard walls; faces hidden beneath solid landing/treads stay closed but omit invisible individual brick relief. Light retains the footprint, openings, tread levels and cap profile, with fewer curve samples and four-sided grille bars.

tools/test_glessner_terrace.py casts actual vertical rays at nine walking-line points in Full and Light. Measured surfaces are 1.679, 1.493, 1.306, 1.120, 0.933, 0.746, 0.560, 0.373 and 0.187 m. It also checks that the landing does not cover the descending flight, that every terminal mesh edge closes, and that the deck reaches the recessed doorway across the leaf. The first browser inspection exposed a narrow threshold gap; the deck now extends 0.40 m inside the bow arc, beneath the retained recessed door and hidden within the wall elsewhere. A subsequent close view exposed depth interference: the legacy bottom reveal and sill shared the deck height. A closed stone threshold now covers both with a bounded 6 mm rise; nine rays across its leaf and jamb ends verify that separation in both tiers.

The actual published-app [before receipt](glessner-courtyard-steps-T-2218/before/browser-validation.json) covers five desktop and five phone cameras. All requests and pages were clean. Desktop peaked at 4,446,956 triangles / 334 calls. The phone stair-bottom view exposed an inherited overrun: 1,224,656 triangles / 213 calls against 1.19M. Under the owner's explicit headroom ruling, this Glessner inspection has a declared Light allowance of 1.27M (3.7% margin), below Balanced's 1.28M. Other scenes remain 1.19M; Light draw calls remain 330. This is a rendering-count allowance, not a frame-rate claim. The building's separate 200,000-triangle Light-asset cap remains unchanged.

The matched section exposed the original grille head reading as the outer surround rather than the clear opening. Native section pixels place the clear head near 5401 (1.426 m), with about 0.38 m stone above it. Eleven intermediate bars, two rails, 0.10 m jambs and a 0.11 m sill follow the visible section pattern; stock diameter, depth and hidden fixings remain bounded reconstructions. Both faces of the foundation are cut through at the openings.

The final section review also exposed an incorrect constant vertical cap thickness: it narrowed into a thin line on the steep descent. [Independent edge controls](glessner-courtyard-steps-T-2218/cap-section-controls.json) now trace both stone edges at ±5 pixels (~0.026 m) with monotone interpolation. The upper/lower edges stand at 2.13/1.46 m at S44.5 ft, so the steep band retains its section-drawn thickness. The post crown is 1.554 m; its 0.75 ft radius and S46.05 centre reconcile the plan/section readings and centre it beneath the cap. The 0.75 ft crown rise follows the section's roughly 0.20–0.25 m rounded top. The former plan-centre reading was S46.2, a 1.8-inch discrepancy, retained in the control record. Lower reconstructed tread ends follow that terminal. The ray check reads both emitted cap edges at four independently measured section positions in both tiers. Beyond the last visible trace at S45.35 ft, the cap carries a short level shoulder into the plan-located cylindrical terminal; this concealed/ambiguous three-dimensional join is reconstructed. It reads longer in the west section projection than the drawn profile, and remains an explicit terminal-junction comparison item for T-2228 rather than an exact source match.

## Final validation

The final build and K01 package contract pass: Full/Web **1,312,788 triangles / 28 primitives**, Light **199,496 / 25**, with no coincident faces in any tier. The exact recovery archive verifies. Both detail levels pass the nine-tread, recessed-threshold, paired-aperture, independent cap-edge and closed-terminal geometry checks.

The [final browser receipt](glessner-courtyard-steps-T-2218/after/browser-validation.json) records five desktop and five phone views of the actual published 1904 app, with the exact package hashes. All ten pass, with zero page errors, failed requests or scene problems. Desktop peaks at 4,264,704 triangles / 335 calls; phone at 1,224,896 / 213. All are within their declared inspection allowances. Desktop counts include the independently merged T-2493 street-tree culling and are not presented as a stair optimization or a frame-rate measurement.

The depth interference found during visual inspection is gone in the final [desktop threshold](glessner-courtyard-steps-T-2218/after/desktop-upper-landing.jpg) and [phone threshold](glessner-courtyard-steps-T-2218/after/mobile-upper-landing.jpg). The [intermediate defect](glessner-courtyard-steps-T-2218/threshold-before.jpg) is retained for comparison. All other approach, facade and bottom-of-flight captures were reviewed in both tiers.

[Supplemental UI checks](glessner-courtyard-steps-T-2218/supplemental-ui-validation.json), captured immediately before the threshold-only repair, verify Full-Light-Full budget restoration. [All 116 credited image tiles](glessner-courtyard-steps-T-2218/supplemental-images.json) loaded. Those checks are dated separately; they are not substituted for the final geometry receipt.

The [matched section](photo-match/glessner_house/habs04-terrace-section-side-by-side.jpg) was reviewed at the fixed source cut and depth settings. The measured terrace cap edges and paired grilles follow the controls. The short reconstructed shoulder into the terminal reads longer than the section silhouette; the neighboring stair-tower basement opening is narrower/taller and its lintel overlaps the terminal in this projection. These are explicit T-2228 comparison items. North HABS01/14 also retain their recorded whole-house differences. All three records honestly remain `differs`.

Full preflight and the required remote checks govern the dev merge; their results are recorded on the PR linked from T-2218. The separate full-town rebuild reproducibility issue is T-2494. Whole-house photographic acceptance remains T-2228.

## Dev integration

The branch integrates dev `09f5012ac` (the independent 1638 Prairie gable/bay update and asset-recovery check). The Glessner full/web/light package is unchanged by that integration. The fixed-camera receipts above were captured before integration on base `4368080cb`; their package hashes still identify these exact Glessner assets. Whole-app preflight and remote desktop/mobile smoke results for the integrated commit are recorded on the PR.
