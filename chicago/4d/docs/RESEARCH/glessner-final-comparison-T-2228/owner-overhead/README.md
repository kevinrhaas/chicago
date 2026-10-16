# Owner overhead roof comparison — T-2228

The 2026-10-15 owner priority is a straight north-range ridge through the west
wing, then remaining roof features, including northeast courtyard copper.
The pre-correction asset shows the west cross crest/cupola south of the long
north ridge. The record supplies S18.4 versus S14.6 ft: a3.8ft displacement.

The unmarked owner aerial is a modern surviving-form reference, not a1904
material or height survey. Its third-party pixels are retained privately; only
the model render, source hash, camera and observations are committed.
The camera is fitted to four outer wall/eave corners, using HABS footprint
coordinates and retained eave heights. West eave heights are reconstructed.
No ridge, cupola, tree, shadow or map-label pixels enter the fit. The corner
RMS is approximately2.5px with5px picking uncertainty; a single pinhole pose
only approximates a possibly orthorectified image. It cannot measure exact
roof heights or establish that every residual is a model error.

To reproduce, supply the owner aerial whose hash is recorded in camera.json,
copy that camera outside the repository, replace external_photo with a photo
field pointing to the supplied image, then run tools/photo_match.mjs from
chicago/4d with --out directed to a private review directory. Use the same
camera before and after the correction. The public before-render.png is the
actual master; its exact bytes are named in before-review.json.

The alignment change keeps the north-range S14.6 ridge, W141 stable ridge,
separate34.1/38.6ft heights, north street service apertures and rear courtyard
roof. The west cross-gable and cupola move north toS14.6; their right-angle
plan intersection is tested independently of the camera. The directly reviewed
`after-ridge-render.png` shows the corrected straight plan alignment; its exact
master and image hashes are in `after-ridge-review.json`. Copper coverage and
other roof features still differ, so this does not accept the whole roof.

The `west-before/` and `west-after/` generic renders and `after-ridge-*` files
preserve the earlier ridge-only stage (master6f1cbdee). They do not show the final
window/copper correction. Final actual-master evidence is
`after-window-copper-render.png`, `after-window-copper-review.json`, and the
`west-window-after-*` pair. The overhead review shows the restored copper return
seated on the north roof plane; seam detail and other roof-feature correspondence
remain open.

## Historical northwest window check

The owner clarified that historical northwest photographs should confirm the
window locations. HABS01 was rendered at its unchanged camera and directly
reviewed. The ca.1887 Cornell stable photograph exposes all eight west lights
more clearly. Its official catalog, accession15/5/3090.00156 (ss:3874294), was
recovered and its explicit public-domain statement verified. The direct scan
and existing museum reproduction were both viewed; they are one exposure.
The source copy and attribution are included here.

`west-window-before-comparison.jpg` uses the actual ridge-only master6f1cbdee
and a west-plane diagnostic camera. Four exterior corner/eave points control
it; every window and gable peak is withheld. The59.75-ft wall length is HABS;
25.2/16.5-ft eaves retain existing reconstructions. Principal x is the image
midpoint; orthogonal wall axes solve the remaining intrinsics. Camera height
comes out1.768m. This does not refit a window to hide its own error. Eave and
hand-pick uncertainty remains explicit, and north-face/gable residuals prevent
using this pose as whole-house surveyed acceptance.

At the retained eaves, the southern upper slit reads near S19.8 versus S21.8
in the model. Alternate eave interpretations give roughly S17.8–20.5; the
former location is too far south throughout that check. The other seven
centers are within about1ft of their existing locations. Move only the southern
upper slit2ft north, retaining its width and vertical bounds. This supersedes
the earlier ridge-only decision to preserve all apertures. The upper pair's
midpoint then becomes S15.25,0.65ft from the new S14.6 peak. The new bake and after comparison have been directly reviewed. The corrected
slit follows the photographed position more closely. Other seven centers remain,
with approximate 1 ft station uncertainty; widths/heights and full-facade acceptance
remain open. All eight openings clear both roof slopes across their full widths.

`data/reference_views/glessner_house/cornell-northwest-west-windows.json`
adds this camera to the canonical comparison set. The earlier owner study is
still archived as a reconstructed target, not elevated above the photograph.
