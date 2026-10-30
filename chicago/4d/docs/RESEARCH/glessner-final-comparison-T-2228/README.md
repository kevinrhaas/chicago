# Glessner final comparison — T-2228, correction pass

Target: 1904-07-01; exterior and courtyard only. **Photographic signoff remains open.**
This pass corrects defects found while re-reading the frozen views; a green technical
build is not a `matches` verdict. All eleven comparisons of the preceding roof/window master were directly reviewed and remain `differs`;
[the review receipt](visual-review.json) identifies their exact asset.

## Visible corrections

- The north crest now runs straight through the west crossing. The west cross-gable and
  cupola move 3.8 ft north; fixed-camera overhead and west renders confirm the alignment.
  Eight west-wall windows remain clear. Historical northwest comparison then moves
  the southern upper slit two feet north; the other seven positions remain.
- The aerial's omitted northeast copper strip is restored as cladding on the existing
  north roof plane. The chamfer and extent are declared reconstructions; exact tile
  replacement prevents a raised fold. Its actual rebuilt master has been directly reviewed at the frozen aerial camera.
- A pointed north cone now meets a lower pitched connector. The former apex extended
  horizontally to the gable. HABS 14 bounds a reconstructed connector ridge 39.2 ft;
  HABS 01 confirms the pointed silhouette but does not independently measure that height.
- The north street facade keeps its approved 26.5 ft western shoulder datum, flat wall,
  staggered curved west drum and dark-glass default. The east-wing courtyard eave uses
  the HABS 4 visible edge 27.33 ft; with the retained ridge and 20 cm overhang its wall-plane
  height is 28.83 ft. The concealed north shoulder returns between those two roof planes.
- Courtyard dormers cut the main roof only inside their bodies below their own roof
  envelopes. Rear intersections and projecting soffits stay closed; tiles no longer
  cross the glazing. Section frame dimensions, eaves and bell finials replace the
  earlier approximate proportions. Side overhang is narrowed from 0.26 to 0.144 m,
  with an 85 mm apron inset preserving the flare. Hidden depth/profile stock remain reconstructed.
- The low bow hood rises 0.83 ft to its section datum. The broad basement grille beside
  the stair tower replaces an incorrectly narrow, low opening. The terminal terrace
  coping loses its flat shelf, but still crosses the rounded post in projection.
- Courtyard east leaders move into clear masonry strips beside the revised tower
  and basement light; neither crosses an opening. Their exact anchors remain reconstructed.
- The stair tower uses the independently rectified HABS 2 plan centre S 56.10 ft. HABS 4
  suggests S 56.73/r 5.55 ft, versus retained plan radius 5.25 ft; the disagreement remains
  explicit. Section roof/finial height supersedes the former overly high silhouette.

## Evidence and limitations

[Native section controls](section-controls.json) re-read the same cleared HABS drawing,
not a new witness. Grade 5858, north-wall x 1165, scales 100.6 horizontal/97.7 vertical px/ft
remain fixed. The wider section camera uses those independent controls; no camera was
refitted to hide the geometry changes. Native photographs, source crops and actual
master side-by-sides were viewed. The original five cameras and baseline asset hashes
are retained in the before receipt. Exact asset and visual receipts identify the reviewed candidate; they are not
inferred from source-code tests. The optional-parameter compatibility receipt and
first-roof review preserve earlier stages; their hashes are historical and do not
accept the current candidate.

HABS 05's title “Interior court” describes the exterior courtyard. Its library category
is corrected, while its rights remain unresolved. The c.1923 typescript was unpublished:
its date does not establish publication or clear the copied photographs. No new asset
is derived from HABS 05. Modern w_lemay courtyard records retain their individually
cleared CC BY-SA 2.0 provenance; the library's broad copyright enum is not a substitute
for those license records.

The original 168-image audit numbers remain intact. Ten of 17 retrieval failures were
recovered previously; #015, #025, #128–131, #140 remain unavailable. Duplicates and later
fabric are not additional 1904 corroboration. Monochrome photographs cannot establish
exact 1904 RGB colors; the app retains the owner-selected grey-greige granite and dark
ordinary glazing. Bare-GLB comparisons use a different material/lighting path.

## Added coverage

The unchanged T-2200 cameras for HABS 13 (north pairs), 15 (stable), 16 (Prairie
facade) and 17 (northeast) are imported into the canonical image gate. Their source
bytes were hash-checked and their actual photographs viewed again. Baseline RMS
values remain explicitly tied to the original asset; no camera fit or pixel pick
is silently revised. The new wide courtyard section uses the same independent
controls as the earlier hood/terrace crops. The raw source crop is credited in
[habs4-court-exterior-credit.txt](habs4-court-exterior-credit.txt).

## Remaining audit work

North finial/stack camera residuals, further elevation and opening correspondence,
west courtyard door/descending areaway levels, and whole-house material/lighting
comparisons remain under review. A rejected modern 058 camera fit reached its focal
and eye-height bounds; its rays are not accepted dimensional evidence. HABS 2's west
DN arrow is distinct from the later 1955 rear wooden stair. No unsupported raised
flight, changed door sill or guessed source license is introduced.

## Verification

Independent spatial regressions cover cone/connector coverage at 32/48 facets,
planar copper/host cuts, 1,500 dormer-host samples and clear glazing, terrace rays,
rounded-terminal silhouette, and concealed Light drum subtraction. The rebuilt assets contain 1,364,944 triangles in Full/Web and 193,697 in Light,
with zero coincident faces; the Light ceiling stays 200,000. Only concealed Light drum/barrel/valley faces
are omitted; Full stock and visible Light angular sampling remain. Runtime budget
and Full transparent-roof grouping are unchanged. Browser and repository gates are
recorded after the final bake, not assumed here.


## Current comparisons

All rows use the actual master asset named in [the asset receipt](asset-receipt.json).
The first five existing cameras retain their original bytes. The wide court section
is newly framed from the same fixed drawing controls; four import unchanged T-2200
poses. The Cornell northwest view adds independent west-plane corner controls,
with every window withheld from the camera fit; reconstructed-eave uncertainty remains explicit. [The discrepancy register](discrepancies.json) distinguishes
visible corrections from open work. No row is photographic signoff. T-3136 re-read every row against the current master, ruled two, replaced the two catch-alls with the specific open rows and named each row's ticket: [the reading](../glessner-signoff-reading-T-3136/README.md).

| View | Current comparison |
|---|---|
| Historical northwest windows | [Cornell ca. 1887](../photo-match/glessner_house/cornell-northwest-west-windows-side-by-side.jpg) |
| North inclined | [HABS14](../photo-match/glessner_house/habs-14-north-inclined-side-by-side.jpg) |
| Northwest | [HABS01](../photo-match/glessner_house/habs-01-northwest-side-by-side.jpg) |
| Early northeast | [Taylor2135](../photo-match/glessner_house/taylor-2135-ne-side-by-side.jpg) |
| Bow hood section | [HABS4 hood](../photo-match/glessner_house/habs04-hood-section-side-by-side.jpg) |
| Terrace section | [HABS4 terrace](../photo-match/glessner_house/habs04-terrace-section-side-by-side.jpg) |
| Wide courtyard section | [HABS4 court](../photo-match/glessner_house/habs04-court-exterior-side-by-side.jpg) |
| North window pairs | [HABS13](../photo-match/glessner_house/habs-13-north-level-side-by-side.jpg) |
| Stable entrance | [HABS15](../photo-match/glessner_house/habs-15-stable-detail-side-by-side.jpg) |
| Prairie facade | [HABS16](../photo-match/glessner_house/habs-16-prairie-front-side-by-side.jpg) |
| Northeast | [HABS17](../photo-match/glessner_house/habs-17-habs-ne-side-by-side.jpg) |


## Published-app review

Fresh published desktop Full and mobile Light checks cover six fixed stands each;
all twelve pass their scene budgets without page or asset errors. The mobile Images
check loads every credited tile. Exact counts and asset hashes appear in
[published-review.json](published-review.json). The source comparison and app use
different lighting/material paths; software rendering does not establish GPU FPS.

Full repository preflight, integration with current dev and exact-commit CI remain
merge gates. Their final receipts belong to the correction PR; this evidence report
does not claim final photographic acceptance. T-2228 stays active for the open items.


The subsequent [entrance correction and current-asset review](../glessner-entry-2228/README.md) adds a twelfth canonical view and supersedes this report’s 6b2cff4d asset acceptance. The earlier roof/window measurements remain valid as historical receipts; they do not validate a later asset.


## Stable roof heights: camera, not roof (T-2758)

HABS photograph 1 read the whole stable roof about 28 px (roughly 2 ft) low and the cupola about 4 ft
north of S14.6. [`tools/glessner_stable_roof_read.py`](../../../tools/glessner_stable_roof_read.py)
re-solves both stable cameras with the carriage doorway (sheet 2 jambs W 134.9-147.0, sheet 5 soffit
12.6 ft), the one measured length in the stable's face. It then reads the roof back through every fit
and writes [stable-roof-heights.json](../../../data/comparisons/glessner/stable-roof-heights.json).

| reading | model | photo 1, committed | photo 1, doorway re-solves | Cornell, committed | Cornell, re-solved at the roof |
|---|---|---|---|---|---|
| north gable coping apex | 39.6 ft | 37.8 | 38.1-38.6 (ruler 38.8) | 42.3 | 38.3-39.5 |
| cupola apex, on S14.6 | 47.0 ft | 45.1 | 45.5-46.3 | 51.2 | 46.5-47.8 |
| cupola centre on the ridge | S14.6 | S11.0 | S13.3-14.4 (S10.4-14.4, aspect free) | S11.2 | S13.0-13.2 |

The committed photograph-1 camera draws 14.6 px a foot at the stable where the doorway measures 13.85,
because its vertical scale comes from the eave at the Prairie corner. That camera error is most of the
2 ft. The roughly 1 ft left is inside the ridge's 1.5 ft tolerance, and the two photographs disagree by
about as much, so the roof is kept. Photograph 1 cannot place the cupola along S: all its controls lie in
one plane, and with the pixel aspect let go (those controls cannot measure it) fits of one RMS slide the
cupola from S14.4 at square pixels to S10.4 at an aspect of 1.06, the gable's height not moving. The Cornell re-solve, on two faces,
puts it about 1.5 ft north of S14.6, not 4 ft, so there is no question for the owner. Neither committed
camera is replaced. Photograph 1's doorway re-solve moves the north tower's finial about 9 px off the print,
and the Cornell west-wall camera still serves the west windows, which the re-solve reads in the same places.
Recorded in `docs/LIBERTIES.md` as L-glessner-stable-roof-camera-2758.
