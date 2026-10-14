# T-2219 — service openings and the stable/north roof junction

Owner continuation, 13 October 2026. The circled north service doorway and sash
looked half-width, and the west/stable roof left a triangular shelf at the join.
This pass corrects those items and inventories the existing low openings. It
works toward the 1904 exterior; T-2228 retains whole-house photographic acceptance.

## Evidence and bounded measurements

HABS IL-1015 photograph 01 (Cervin Robinson, 23 July 1963) and photograph 15
(Jack E. Boucher, 9 June 1965) show the complete door, upper sash, gable foot,
steps and downpipe. Source records are `habs_glessner_photo_01_nw_1963` and
`habs_glessner_photo_15_north_stable_1965`; both have no known restrictions.
The high-resolution first- and second-floor plans, HABS sheets 2 and 3,
confirm different widths from the former 2.4-ft slit reading. The inspected
service-bay crop is x=.64–.77, y=.58–.70 of each original 9624×7584 scan.
[First-floor crop](glessner-service-junction-T-2219/habs-plan-2-service.png) ·
[Second-floor crop](glessner-service-junction-T-2219/habs-plan-3-service.png).
`habs_glessner_house_il_1015_drawings` supplies the plans and elevations.
The available set has no basement plan or north elevation drawing: sheet 1
is the title/site map, sheets 4–5 are sections, sheet 6 is the east elevation.

| Element | Former record | Revised reading | Status |
|---|---|---|---|
| Service door | W122.8–125.2 ft; 2.4 ft wide | W122.8–126.7; 3.9 ft | Inferred plan/photo reading, ±.3 ft |
| Upper sash | W122.8–125.2 ft; 2.4 ft wide | W122.8–127.0; 4.2 ft | Inferred, comparable to its 4.1-ft neighbour, ±.3 ft |
| North gable foot | W125.75 ft | W127.75 ft | Reconstructed junction, ±.5 ft |
| Door threshold | At ground | .85 ft above ground | Reconstructed from visible two-step stoop, ±.2 ft |
| Steps | Absent | Two .425-ft rises, .95-ft runs | Reconstructed dimensions, solid stone |

W measures westward from the east end of 18th Street. The stable courtyard
footprint remains W125.75–161.25; its north gable is a separate facade control.
The later photographs are carried back cautiously. The known 1946 garage
alterations are excluded. The door retains the existing plain wood treatment;
these images do not establish its 1904 paint or every joinery detail.
The pipe location and collector follow the photographed junction; diameter,
metal finish and unseen connection are reconstructed with the existing rainwater
kit. No change is derived from the rights-pending servants' entrance image.

## Roof correction

The stable ridge remains level and the approved west, south and courtyard roof
profiles remain fixed. A planar north return meets the existing courtyard plane
along a diagonal that ends at the north ridge valley. Their upper envelope joins
the north roof continuously. Its street overhang starts at the gable foot, so no
roof strip crosses the gable face. Coplanar envelope patches have a single owner;
a degenerate zero-plane subtraction previously allowed duplicated faces.
The test checks independent rays, shared edges and slight gable-foot perturbations.
This geometry is a bounded reconstruction, not a measured historic roof survey.

## Basement and low-opening inventory

The generated [street schedule](glessner-windows-2211/opening-schedule.md) and
[courtyard schedule](glessner-windows-2212/opening-schedule.md) list each aperture,
coordinates, type and provenance. The following index covers all low lights:

| Group | Stations, feet | Type / source cross-reference | Disposition |
|---|---|---|---|
| Prairie front, four | S8.1–12, 16.9–20.8, 45.1–49, 54.4–58.3; z.8–4.7 | Stone 3×3 grille lights; HABS6 east elevation | Retain |
| North court, six bays / seven lights | W40–44.5, 46–50, 52–56, 82–86, 92–96, 112–118; z.8–5.4 | Barred garden windows; HABS4–5 sections and photo05, widths reconstructed | Retain; no new resize supported |
| East-wing court, one | S43–48.5; z1–4.5 | Barred garden window; HABS4 section; reconstructed | Retain |
| Stable court, three | S29.5–33, 41–44.5, 50.8–54.3; z.8–4.2 | Barred garden windows; below HABS2/3 plan window bays; reconstructed, no independent basement plan | Retain, exact size unverified |
| Bow terrace, two | Curved terrace facets; z1–3.8 | Barred dark lights; HABS4/5 sectional context, reconstructed | Retain |
| Dining bay, three | Three bay facets; z1–5 | Barred dark lights; HABS4/5 sectional context, reconstructed | Retain |

Photo05 is the circa-1923 courtyard image: rights remain unknown/link-only. It is
used to check the existing model's classification and is not a source for newly
derived geometry or reproduced here. Existing courtyard heights and breadths
remain reconstructed; a perfect measured match is not asserted. HABS sheets
show occupied spaces and exterior levels, but do not establish unseen well depths.
No independent excavated well is modeled: these apertures are above the local
ground, with closed recesses, rather than holes requiring invented well bottoms.

The north arch and the porte-cochere are passages, not basement windows. The
north service door is a door; the stable carriage doors are vehicle access. No
new basement vent is inferred from these dark openings. The updated schedule
keeps these classes distinct. The service stoop meets its raised threshold;
the drainpipe terminates above ground using the existing detail construction.

Existing window recesses have a back at .90m behind the facade and closed sides;
small dark panes also have a solid rear slab. Garden-bar radius is .011m with
nominal .115m spacing in the shared sash kit. Stone grille mullions remain stone,
not thin iron substituted for the Prairie grid. Faceted bay/terrace lights retain
their existing solid dark backs. No furnished interiors are introduced.

## Published comparison and performance

Fixed cameras are in `tools/qa_glessner_t2219.mjs`. Before captures use the actual
T-2470 published assets. HABS01 uses the existing calibrated camera, unchanged
across the comparison; HABS14 checks the previously corrected north tower. Shape prototypes are scratch work only; final evidence
must use the canonical web assets. The whole-house comparison remains `differs`:
colour, masonry texture and other proportions are not declared exact by this pass.

The before Full frame already exceeded the old 3.8M selected-Glessner allowance:
3,890,920 triangles at the close junction stand, 3,836,612 frontal, 3,655,925 above
(225 draw calls maximum), with no page/request/scene errors. The separate wider
stand read 3,887,761. These are rendered passes, not asset triangle counts.
After integrating T-2473's street trees from dev, the same stand with summer
foliage measures 4,274,524 triangles / 229 calls. The initial 4.1M allowance fails
that combined scene. The final allowance is 4.6M, 7.6% above the integrated
measurement, under the existing owner budget policy. Light and ordinary-town
budgets stay fixed. The integrated pre-raise receipt is preserved alongside
the before receipts. Final default-summer captures include the trees; an extra
Full frontal capture uses the shipped Hidden setting to inspect the gable-foot
pipe and openings clearly. That extra capture does not replace the summer budget gate. This is measured scene headroom, not a hardware FPS claim. The before
failure is preserved in `glessner-service-junction-T-2219/before/budget-observations.json`.
The initial new Light geometry contained 200,465 triangles and correctly failed
its unchanged 200,000 asset cap. Light now samples physical tile-lap relief every
sixth course rather than every second; the metric texture still carries every
course and joint. Openings, roof planes and silhouette are preserved. The Full
asset is unaffected.

The phone audit exposed a separate omitted detail: the reduced axial sash path
never emitted the existing Full garden bars. Light now restores all 104 bars
across ten courtyard apertures, preserving their centres and 22-mm diameter,
with four-sided sections instead of six. This is restoration of an existing
feature, not a new derivation from the rights-unknown courtyard photograph.

With the integrated street trees, the first phone courtyard stand cost 1,417,383
triangles against its unchanged 1,190,000 ceiling. In selected Balanced/Light inspection,
building primitives are partitioned into 4-m plan / 2-m height cells inside the
existing material batches. Every original triangle, winding, normal, UV, colour,
confidence and material attribute survives. The same per-instance frustum tests
now reject smaller invisible pieces in both view and shadow passes. Shadows,
view distance and rendered surfaces are unchanged; ordinary scenes and Full
do not use the extra building partitioning. Balanced and Light share the same
reduced asset, so both use identical cells; a same-asset switch cannot retain
unpartitioned batches when entering Light. The CPU test compares exact triangles
and attributes and exercises vertical separation and cell-boundary corners.

A subsequent per-mesh measurement found the distant railway still submitting all
51,704 ballast-bed and 22,184 cinder-ground triangles from this courtyard. Its
three ground materials now use the same exact 40-m spatial batches as terrain,
at every detail tier. Alpha, UVs, confidence, render order, depth-write policy
and picking surfaces are preserved; no rails, ties or railway dimensions change.
The CPU checks include RGBA preservation and identical ray intersections. This
reduces unnecessary drawing without changing the shadow reach or Light ceiling.

## Asset validation

The rebuilt master and Full web asset each contain 1,296,748 triangles; Light
contains 199,071. All three have zero coincident faces, and K01 scale, origin
and metric-UV checks pass. The lossless recovery package verifies against all
three final files. The three legacy comparison versions are refreshed with
their ordinary UV unwrap, separately from the detailed current master.

The roof-envelope check passes 1,800 spatial rays, the courtyard check 1,200,
and the new service-junction test checks aperture proportions, threshold contact,
continuous seams and gable clearance under small control perturbations.
Existing north-tower, block-clipping and producer/package lifecycle checks pass.
These geometric tests supplement the fixed-camera HABS01 and HABS14 review;
their match records preserve outstanding whole-house differences.

## Published-app validation

The integrated phone run uses normal `/1904/` boot at 390×780, Light, the
default dark glass and summer street trees. All five fixed stands pass the
unchanged 1,190,000-triangle / 330-call ceiling, with no page, request or scene
errors. Service junction / front / roof / Prairie lights / courtyard lights
measure 1,069,084 / 870,944 / 670,579 / 815,640 / 1,155,173 triangles respectively.
The courtyard bars are visible in the final capture. All 116 Images-tab tiles
load with their credits. The JSON receipts and PNGs are in `after/`.

The integrated desktop run at 1280×800 uses Full and the same summer scene.
All five stands pass the explicit 4,600,000-triangle allowance, with no page,
request or scene errors. The additional front view uses the shipped Hidden
tree setting to expose the complete openings, pipe and roof junction.
The final Full maximum is 4,359,686 triangles and 325 calls at the courtyard
stand, leaving 5.5% triangle headroom under that allowance.

The settings-transition audit found that the background city chose its detail
only at boot: Balanced → Light retained 92,244 extra rendered triangles at
the courtyard stand. The inspection detail transaction now prepares and swaps
the existing context layer at the Light boundary, with failure/obsolete-request
disposal and the current seasonal look preserved. It uses the existing layer
recipe and density rules; it introduces no new skyline or thinning policy.
The failing receipt is retained in `before/balanced-retained-context.json`.

The final saved-Balanced phone run, after the seasonal-view integration, passes
all five Light stands and all 116 credited gallery images. Its explicit
Light → Balanced → Light cycle restores the exact initial context census and
retains Summer. All five rendered triangle counts equal the fresh-Light run
listed above; no page, request or scene errors occur. See
`after/balanced-to-light/browser-validation-mobile.json`.
