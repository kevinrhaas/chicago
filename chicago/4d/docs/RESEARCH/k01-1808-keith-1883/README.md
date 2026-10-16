# T-1883 — 1808 Prairie, Keith / Field house

This pass replaces the remaining generic street-front finish with a procedural
interpretation of the owner-approved February 1888 Inland Architect photograph.
**Photographic acceptance remains open.** The new comparisons deliberately retain
`differs` where ornament, stone courses or proportions have not converged. A green
code/package check is not a declaration that the house matches every photograph.

## Evidence and date

The owner said on 2026-10-16: “Ok to use that image, go ahead and proceed on that
ticket and merge to green.” This approves the 1888 Keith plate for the project;
the canonical source records the quote and scope. It does not re-license the later
photographs. [Reference credits](../../../data/sources/assets/inland_architect_1888_02_keith/README.md)
retain each image's library attribution and rights statement. No photograph pixels
are baked into the model or used as a material texture.

Three contemporary notices were inspected at full resolution:

* **Inland Architect, September 1886, p. 28**, right column near the foot:
  “For O. R. Keith, three story dwelling, 38 by 80 feet, 1808 Prairie avenue,
  granite front; cost $40,000; John Angus, mason.” Canonical source
  `inland_architect_1886_09_keith_notice`, tier 1. It establishes granite, not
  a quarry or a calibrated colour. The permit dimensions do not replace the
  accepted mapped footprint.
* **American Architect and Building News**, vol. XX, no. 557, permit notice:
  O. R. Keith, three-story Prairie Avenue dwelling, $30,000, Cobb & Frost.
  No quarry or colour was found in the inspected notice.
* **Real Estate and Building Journal, 1886-08-28, p. 493**: Prairie Avenue
  No. 1808, three-story dwelling, 38 by 80 feet, $30,000. No quarry or colour
  was found. The scanned initials are reported by the library as D. R. Keith;
  that reading is not silently substituted for the other sources' O. R.

The target remains 1904-07-01. The early photographs show a low stone boundary;
1965's iron infill, ivy, and later neighbouring buildings are evidence of their
own dates. Later chimneys cannot be backdated solely from those pictures.
The 1874 Hitchcock/Galloway double-house engraving predates Keith's 1886 house:
it is excluded, with no camera or claim that Keith matches it.

The mid-1950s library photograph's direction is corrected to southeast looking
northwest: 1812 is nearest on the left, and Glessner recedes on the right.

## What changed

* Two open rows of stone lattice, corner pinnacles, a rock-faced checker band,
  five colonnettes between the six upper windows, and the solid short north return.
  The roof deck sits below the openings; they show actual sky, not a painted grid.
* Paired Ionic capitals, pierced lower porch panels, curved balcony coping with
  finial piers, shallow carved motifs, and concave stair cheeks with scrolls.
* Principal floor raised from 1.5 to 2.0 m, twelve equal risers, the second and
  third floors retained at 5.9 and 9.8 m. The principal bay has three tall transom
  openings, three shorter basement lights, and four second-storey windows.
* Coursed granite relief around real recessed bay openings; stone avoids the
  raised sill/head sockets. Convex flat quads are clipped once before bending,
  avoiding redundant diagonal subdivision. Light keeps the true curved wall,
  openings and texture while omitting the shallow relief.
* Low stone posts/rails, with a clear stair opening, replace the generic tall
  iron fence, piers and urns.
* Keith alone receives the separate load-time granite and dressed-stone tints
  in `renderers/web/js/keith-stone.js`. Glessner's tint is unchanged. The colour
  is a reconstruction constrained by the pale monochrome front and blue-cast,
  shaded 1965 print, not a claimed measured quarry colour.

The main footprint, placement, Glessner clearance, rear bay and service walls
remain the accepted assembly. Fine carving sections, concealed roof, rear
openings and exact material colour remain declared reconstructions under
`L-k01-keith-finish-1883`; superseded principal-floor liberty coverage is retired.
Other houses do not opt into these finish parameters.

## Comparisons and remaining work

Every listed Keith photograph has a camera and comparison under
[`data/reference_views/keith_house_1808_prairie`](../../../data/reference_views/keith_house_1808_prairie)
and [`docs/RESEARCH/photo-match/keith_house_1808_prairie`](../photo-match/keith_house_1808_prairie).
The Taylor reference is translated from the existing Glessner calibration;
reproductions of the same captures are registered with SIFT/RANSAC. Other
cameras use manually picked controls, with their residuals and assumptions
recorded. A numerical registration residual is not a visual match verdict.
The rotated Inland Architect Glessner plate is rendered with camera roll;
the source photograph is not altered.

The 1888 primary view has a before render made from dev commit `378a925` and
an after render from the same camera. `before/inland-1888-side-by-side.jpg`
retains the old generic finish. The actual-app front stand is also the same as
T-2500's recorded front stand.

Remaining differences are recorded per view rather than suppressed: the carved
balcony/pedestal ornament and scroll sections are schematic; granite face and
course variation are still more regular than the photographs; the fine pinnacle
and upper capital profiles need further convergence. The independent street
camera fits retain visible residuals, especially where only a sliver of Keith
is visible beside Glessner. The 1965 close view constrains the entrance strongly
but does not independently date all of its later surface and fence details.
Hidden rear surfaces, colour in monochrome prints, and features below a picture's
resolution are explicitly not shown. These are reasons to keep the image gate
open, not to mark an imperfect comparison `matches`.

## Validation

The K07 entrance gate checks every riser, walk clearance, sockets, closed surfaces
and overlapping coplanar faces. The K08 gate checks all kit and house bays at both
tiers, including genuine holes, curve normals, closure, silhouette and budgets.
Keith's south bay is **15,476 triangles full / 4,522 light**, below the unchanged
20,000 / 7,000 component ceilings. The K01 asset measurement reports **68,535
triangles, 25 primitives, zero coincident faces**, with scale, origin and metric
UV checks passing for both master and web derivative. Master **8,037,484 bytes**;
compressed browser asset **2,416,576 bytes**.

Browser evidence is captured from the actual published `/1904/` application,
1280×800 full desktop and 390×780 light mobile, with front, oblique, rear, roof
and entrance stands. JSON records include loader errors, scene costs and timed
frames. Software-renderer frame timings are not physical-GPU performance claims.
Repository and browser gate receipts follow.

Final mobile run: all seven stands passed, 96–104 draws and 445,870–727,112
triangles, zero page/HTTP/loader errors; all 28 Images-tab thumbnails loaded with
credits. Software-renderer cold boot was 230,937 ms under concurrent validation.
This is not a device-load benchmark.

The deterministic summation repair re-emitted the master byte-identically
(SHA-256 `1eae71eff559bb077f9ea8048e73b726074131ed399d8a418b98587b4c6cd1e4`).
Every other K01/K12/K13/K16 master also re-emits byte-identically to dev; their
manifest input hashes change because the shared helper set changes.

`tools/check.sh`: **PASS, 895 steps, none red (357 self-tests)**. Three
initial pooled failures were resolved before the quiet reruns: deterministic
`math.fsum` in the new helper, removal of the five newly cleared Keith citations
from the unresolved-rights ledger, and a resident-synthesizer drift comparison
that observed a concurrently written photo-match record. No drift baseline was
expanded. The gate reran each quietly and passed.

[Stone channel measurements](stone-colour-measurement.json) preserve exact patch
boxes and image hashes. The 1965 shaded bow sample is r/g **1.0067**, b/g **1.1316**;
the lighter lower bow patch in the actual app is **0.9148 / 1.0648**. The app still
has tree shadows and blue sky light, so this is not a calibrated sunlit-material
comparison. It documents the remaining colour difference rather than declaring
that a tint has passed. A neutral-light swatch and better matched illumination
remain part of photographic convergence.

Final desktop run: all five final stands (front, rear, roof, loggia and northeast)
passed with zero page/HTTP/loader errors, 126–143 draws and
3,333,536–3,904,661 triangles, inside the unchanged 360 / 4,600,000 scene
budgets. The earlier whole-front and southeast captures are labelled preliminary.
The published stage-14 mobile smoke also passed: 128 checks, zero failures.
This is staged coverage, not a claim that the complete 15-stage smoke ran.

Integration with dev `1d8fb34` preserves the new 1621 side stoop and 1637 paired
opening support. All K01/K12/K13/K16 masters were regenerated after the rebase;
only Keith differs from that dev tree, and Keith retains the master and browser
hashes used for the captures above. Browser receipts precede this integration;
they are not represented as a fresh full-district smoke of the rebased tree.

Required preflight on the rebased implementation (`d6b76b2`) passed in an
isolated clean checkout: full repository gate, changelog entry and ticket-ID
checks. No assertions or drift baselines were relaxed.

Published stage-14 desktop smoke: **128 passed, zero failed**, including the
1904 front door and zero-page-errors checks (115 stage checks and 13 always-on
checks). It took 29m05s on software GL, exceeding the steward timing target;
the unchanged assertions passed. Mobile took 14m52s. Both receipts identify
pre-rebase smoke tree `sha256:95aa65b69bca4e67`; the desktop receipt was filed
after rebase, so its provenance is restored from the captured test-time hash
and the matching mobile receipt rather than attributed to the later tree.

## T-2566 — the granite surface (piece 3 of 4)

**Read off the photograph.** The Glessner House archive print of the 1888 photograph
(`a18-gh-1808-keith-field-front`, the clearest reproduction) was read at full
resolution. From the basement to the third-floor line, the front runs a deep
rock-faced course of about 0.5 m and a thin one of about 0.2 m in turn. The basement
courses are the tallest. The third storey is laid in even, much shallower-faced
courses. The 1965 close view shows the same alternation on the south pier and on the
bow. The checker band is not a square grid: it is rows of rough lumps whose joints
break over the row below, standing out by different amounts, with a moulded head
band under it and corbelled bands over it.

**What changed.** `stone_front.coursing` (new, opt-in, Keith alone) lays the walling
high and low in turn (low = 0.4 of high, or the profile's 0.19 m least) below 9.8 m,
and evenly above. Deep courses take the upper half of the granite profile's
rock-face range, thin courses the lower half, and the even upper courses the bottom
35%. Every value stays inside `k02_stone_profiles.json`, whose `course_rule` already
allowed alternating courses. The checker rows are staggered by half a stone, with
each proud stone's projection and every face's rock height drawn from its seed. The
three plain bands became stepped mouldings of the same heights. The upper
colonnettes' capitals gained a neck ring under a flaring bell. Other houses do not
opt in, so their masters re-emit byte-identically; only their manifest input hashes
moved. Keith grew from 68,535 to 71,003 triangles (master 8,260,408 bytes; web
2,471,040).

**The tint, under neutral light.** Texture mean × load tint, with no sky or shade:
the old tint made the granite r/g 0.898, b/g 1.044, a green-grey. The 1965 print's
shaded bow reads r/g 1.007 even under its blue cast, and sky shade raises blue
without lowering red against green. Both stones are now neutral at the same
lightness (granite r/g 1.000, b/g 1.001). The reading is recorded with its tier,
`reconstructed`, in [stone-colour-measurement.json](stone-colour-measurement.json).

**Comparisons.** All sixteen views were re-rendered. The new rows are `fixed` only in
views that show them: the four reproductions of the 1888 front, and the 1965 close
view for the south pier. In the 1967 view they are below resolution (`not shown`).
The other oblique views keep an `open` row until someone compares them at their own
scale. Still open everywhere: the bow's own masonry keeps even courses, and the
joints, capital carving and moulding sections are drawn to the photograph's shadows
rather than read. No view is `matches`.

## T-2564 — the north return (piece 1 of the split)

T-1883 was split on 2026-10-16 into T-2564 (this north return and the pinnacle caps),
T-2565 (the carved loggia), T-2566 (the granite surface and tint) and T-2567 (the
camera re-fits and the image gate, which carries the house's `## Image gate`).

* **What the pictures show.** The 1887 construction view, the c. 1888 view beside
  Glessner, Taylor's c. 1889 view and the 1948 view all show the return as a solid
  block of large dressed courses, not a smooth face: a rounded coping on top that rises
  in a concave sweep into the corner pinnacle (the front coping does the same), a second,
  similar pinnacle at the rear end, and a lower brick parapet beyond.
* **Its length.** Course counts along the return give about twelve course heights in
  the Taylor view and at least ten in the 1948 view, and the c. 1888 view shows it about
  twice as long as the 2.8 m model from the same camera, so it is now 5.5 m, bounded
  4.5 to 7 m while the cameras carry residuals.
* **What was built.** `stone_finish.return_ashlar` (course 0.46 m, bond 0.9 to 1.5 m,
  coping rise 0.35 m over 0.85 m) lays one bonded field of K02 stones from the third
  floor to the coping, its face 15 mm inside the lot line; a swept rounded coping; ogival
  caps with collar and finial on all three pinnacles. The brick north parapet and its
  wall head stop at the return's back (`k01_frontage.py`), so no brick crosses the stone.
  A record without `return_ashlar` builds exactly as before; every other K01 master
  re-emits byte-identical.
* **Measured.** Keith full and web, integrated with T-2566's surface (#862): 74,160 triangles, 25 primitives, zero
  coincident faces; scale, origin and metric UV ok (`k01_contract.mjs --measure-asset`).
* **Still differs**, written into each match record: the carving (T-2565), the brown
  cornice-box band under the lattice where the pictures show stone (still there after T-2566), the camera
  residuals (T-2567), a cowl ventilator on the deck in the 1887-89 pictures, and where the
  full-height stone ends behind the rear pinnacle.
* **Browser receipts (T-2564).** The published `/1904/` app, `QA_VIEWS=front,roof,northeast
  node tools/qa_k01_t1883.mjs`: desktop 1280x800 full and mobile 390x780 light both PASS,
  zero page errors and zero bad loads, serving asset `6ec4aee594c1…`
  (`browser-validation-after.json`; the `after-*-front|roof|northeast.jpg` captures are
  re-taken). Smoke: desktop part 1 PASS (87/0), mobile part 14 PASS (128/0, the 1904
  door); desktop part 14 passed 102 checks before the 590 s cap, without reaching its 1904
  section (dev's last reading of that part took 29 min), so the app QA above stands for it.
