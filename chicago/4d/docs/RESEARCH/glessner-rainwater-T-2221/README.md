# Glessner rainwater fittings — T-2221

Target: exterior and courtyard on 1904-07-01. The drainage network follows the
existing roof planes and repaired openings. It adds distinct photographed head
families, attached straps, box troughs, offsets and paths to grade.

## Evidence and bounds

| Source | What it supports | Limits |
| --- | --- | --- |
| [Taylor 2135, c.1887–1889](https://artic.contentdm.oclc.org/digital/collection/mqc/id/28805) | Two framed Prairie heads, narrow sockets, broad straps and corner leaders | Public domain. Native scan is 1056×991; the library's 1600×1502 display is enlarged. Small cast ornament and sheet dimensions cannot be measured from it. |
| [HABS01, 1963](https://hdl.loc.gov/loc.pnp/hhh.il0118/photos.060903p) | North-facing alley-corner leader, short stable eave and smaller service collector | No known restrictions. Later fabric corroboration, not an independent 1904 fitting date. |
| [HABS14, 1965](https://hdl.loc.gov/loc.pnp/hhh.il0118/photos.060916p) | Ribbed north bowl, upper leader entering its mouth, lower leader continuing to grade | No known restrictions. Existing 1800-pixel copy reviewed; native master GET requests returned 403 despite successful HEAD responses. |
| w_lemay courtyard photographs, 2024: [159537087](https://commons.wikimedia.org/wiki/File:Courtyard,_Glessner_House,_Prairie_Avenue_and_18th_Street,_Near_South_Side,_Chicago,_IL_-_54202785678.jpg) and [159537053](https://commons.wikimedia.org/wiki/File:Courtyard,_Glessner_House,_Prairie_Avenue_and_18th_Street,_Near_South_Side,_Chicago,_IL_-_54202591351.jpg) | Box troughs, rectangular leaders and projecting wall straps | CC BY-SA 2.0. Modern sections bound reconstruction only; modern green finish and inspection caps excluded. Canonical source URLs and attribution are in the existing source records and Images tab. |

The Cornell rear view and the copied HABS05 publication image were read
qualitatively. Their unresolved underlying rights do not authorize new geometry
or image derivatives. HABS written data does not give pipe/gutter section sizes.
The source print reproduced in `reference/taylor-2135.jpg` is J. W. Taylor's
public-domain early exposure, courtesy of the Art Institute of Chicago's
Ryerson & Burnham Archives, library ID `a18-rba-taylor-2135-glessner-ne`.

Exact stock and hidden joins are declared in
[L-glessner-rainwater-2221](../../LIBERTIES.md) and the structure's
`rainwater_details` attribute. No monochrome sample establishes a 1904 colour.

## Geometry

Twelve collectors feed twelve leaders and two branch connections. The Prairie
heads retain their framed panel silhouette; the north bowl has a broad mouth,
ribbed flare and banded neck; service and alley heads remain smaller plain
collectors. Receiver mouths sit level with their gutter rims. Actual floor
apertures admit water to the necks. Vertical sockets precede offsets to the wall.

The upper north-tower leader now feeds the bowl. The north-court return joins
the lower bow leader through a descending branch, preserving the repaired
copper and its adjoining roof planes. Both east-court gutter fragments have
outlets beside the stair drum. The north alley leader sits on the north face,
with the short eave stopping at the stable gable foot. No gutter crosses a rake,
and no vertical leader crosses an axial opening.

Three broad collars per lower leader return into masonry. Prairie collar
centres follow Taylor at reconstructed heights 1.74, 4.07 and 6.30 m. The two
featured courtyard leaders, dining and bow, use wider 160×100 mm sections,
shallow front flutes and 400 mm wrap straps bounded by the modern 159537087
close-up; those sections are not independently dated to 1904. Roof-edge brackets
support the troughs. Street runs enter grade; court and low alley runs have
bounded shoes. A separate matte oxidised/coated metal finish keeps the head relief readable
while preserving the existing dark iron hardware. It adds one material primitive
in each tier; its grey-green hue is a bounded 1904 reconstruction, not a colour
recovered from monochrome photographs. Light retains the same network, with simplified millimetre-scale lip
stock and coarser curved sampling.

## Run register

| Run | Visible basis and reconstructed connection |
| --- | --- |
| Prairie north and south | Taylor 2135 locates two framed heads and broad straps. Concealed sockets and street discharge below grade are reconstructed. |
| North tower and upper branch | HABS14 shows the upper leader, ribbed bowl and lower street leader. The upper outlet and lower gutter connection follow the retained roof geometry. |
| North service | HABS01 places the small collector at the service/gable junction. Its hidden wall ties and below-grade end are reconstructed. |
| North-facing alley corner | HABS01 locates the leader beside the stable gable. The short trough stops at the gable foot. |
| Low alley middle and rear | Bounded outlets for the retained low alley eave. Their exact 1904 locations and shoes are reconstructed, not individually established by the cited photographs. |
| Courtyard dining and bow | Licensed modern close-ups bound box stock, fluting and broad wraps. Hidden sockets, shoes and the descending north-court return are reconstructed. |
| Courtyard west | Reconstructed outlet for the retained west court trough, clear of openings. No independent 1904 close-up establishes this exact fitting. |
| Courtyard east north and south | Reconstructed outlets for the two eave fragments beside the stair drum. Roof geometry and opening clearance bound their positions. |

`network.json` records every collector edge, outlet, leader path and branch in
local east/north/up metres. These are construction coordinates, not a survey of
historic fitting dimensions. Generic runs receive three wall straps; heads have
two masonry returns; gutter brackets are spaced at most two metres along
straight runs, with coarser sampling along curves.

## Fixed-camera review and baseline failures

`tools/qa_glessner_t2221.mjs` uses the actual published July 1904 scene at
1280×800 Full and 390×780 Light. It preserves normal geometry, vegetation,
materials, shadows, errors and budget assertions. Animation pauses only after
readiness for repeatable cameras. The local renderer is SwiftShader; these are
not physical-GPU FPS measurements.

The refreshed before gallery uses the unchanged T-2220 house in the integrated
00147/75b9 scene. Seven Full street/alley views pass their budgets. The two court
views fail: bow 401 draws / 4,761,785 triangles, dining 400 / 4,711,778, against
360 / 4,600,000. There are no page errors, failed requests or app problems.
The failed observations remain in `before/`; T-2227 owns these existing Full
failures alongside its earlier Balanced failures. No budget is raised here.
Two earlier desktop startup attempts exceeded the unchanged 240-second wait;
neither is reported as passed. The successful readiness retry does not erase
those failures. An initial mobile baseline was interrupted by an environment
restart before producing observations and is not validation.
The completed mobile retry also fails its two close north views: 1,510,067 and
1,511,690 triangles against Light's 1,270,000 scene limit (181 draws each). Its
other seven views pass, with zero page errors or failed requests. These failures
are recorded under T-2227; the separate house geometry limit remains green.

The new Taylor camera uses five wall/eave controls, excludes drains, reconstructs
an eye height of 1.7 m and has a 1.57-display-pixel RMS residual. It is a fit to
the current house coordinates, not an independent survey. Existing HABS cameras
stay fixed. Whole-house tone, exact masonry, remaining silhouettes and absolute
eave/grade disagreements remain open for T-2228; no photographic match is
claimed by this drainage pass.

## Browser comparison gallery

| Interface | Before, Full | After, Full | After, Light |
| --- | --- | --- | --- |
| Prairie north head | [Before](before/desktop-prairie-ne.png) | [After](after-full/desktop-prairie-ne.png) | [Light](after-mobile/mobile-prairie-ne.png) |
| North bowl and upper feed | [Before](before/desktop-north-head-clear.png) | [After](after-full/desktop-north-head-clear.png) | [Light](after-mobile/mobile-north-head-clear.png) |
| Service door and gable foot | [Before](before/desktop-north-service.png) | [After](after-full/desktop-north-service.png) | [Light](after-mobile/mobile-north-service.png) |
| Courtyard bow connection | [Before](before/desktop-bow-leader.png) | [After](after-full/desktop-bow-leader.png) | [Light](after-mobile/mobile-bow-leader.png) |
| Dining leader and straps | [Before](before/desktop-dining-leader.png) | [After](after-full/desktop-dining-leader.png) | [Light](after-mobile/mobile-dining-leader.png) |

The additional [bowl side view](after-full/desktop-north-bowl-detail.png) has no
before baseline. The [mobile Images tab](after-mobile/mobile-images.png) shows
the credited library. These are visual comparisons, not clean scene-budget
verdicts; the retained failures are recorded below.

## Validation

Spatial drainage checks pass in both tiers: descending connections, supplied
collectors, clear openings, grade discharges and real outlet holes. The measured
Light assembly is 199,559 triangles, below its unchanged 200,000 ceiling; its
roof-plane regression checks pass. The north-tower perturbation test now checks
the emitted bowl connection rather than the retired roof-discharge rod.

Pinned Blender 4.5.3 baked the final master, then the canonical derivative
producer rebuilt Full web and Light plus their recovery package. Full/web
measure 1,333,765 triangles in 29 primitives; Light measures 199,559 in 26.
All three have zero coincident faces and pass scale, origin and metric-UV checks.
Exact final asset sizes and hashes are in `assets.json`. Compared with T-2220,
Full has 667 fewer triangles, Light has 373 more, and each tier adds one material
primitive (`asset-cost-delta.json`). Culling and shadow passes determine the
actual scene draw cost; the asset count is not a scene-budget verdict.

All five reference views were re-rendered explicitly from the final **web**
asset and visually reviewed: Taylor 2135, HABS01, HABS14, the hood section and
the terrace section. The receiver framing and bowl ribs are readable; existing
roof and terrace corrections are preserved. The match records remain `differs`
for the documented whole-house discrepancies. Cropped Taylor/HABS14 comparisons
are in `reference/`, with their source attribution above.

The completed published-app runs reached normal readiness, captured ten views
per tier, and recorded zero page errors, failed requests or app problems. All
121 image tiles loaded with credits; 46 further records remain links. All twenty
scene captures and the Images screenshot were visually reviewed. Two north
angles are foliage-obscured; the clear head close-up and added bowl angle carry
the fitting review. See `after-full/`, `after-mobile/`, `visual-review.txt` and
`app-comparison.json`.

Both browser commands correctly exit **1** for retained scene-budget failures:
Full bow 403 draws / 4,760,451 triangles and dining 402 / 4,710,444; Light
north-head-clear 183 / 1,510,528 and north-tower 183 / 1,512,187. No paired
camera newly fails. Every paired Full view adds two draws and removes 1,334
triangles; paired Light deltas range from -126 to +1,142 triangles, with two
additional draws. These are actual scene readings, including shadows and
culling, not merely the asset primitive count. The added after-only bowl angle
passes both budgets but has no baseline. T-2227 retains the four failing
observations; no assertion or budget was relaxed.

The corrected liberty register was republished and checked in the actual mobile
house card at 390×780. Its drainage entry displays the reconstruction bounds.
That narrow run also passes the added bowl view budget, with normal readiness
and no page errors or failed requests (`liberty-ui/`).

The fixed-camera runs used the final T-2221 assets on the published d69a197dd
scene. Dev's subsequent T-2496 street-travel change was integrated at e45496a11;
it changes routing/arrival behavior rather than this geometry. The complete
repository preflight passes all 883 checks, including 356 self-tests, with strict
raster-reader dependencies. The new drainage test has a measured isolation row
and writes nothing in-tree. Exact-commit CI and deployment receipts are
maintained on the PR before and after its dev merge.
