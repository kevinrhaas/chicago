# T-2206 — roof, dormer and courtyard-bay proportions

The audit retains the current house geometry. It does **not** certify photographic
accuracy: it establishes which dimensions are implemented, which controls support
them, and which disagreements need resolution before another reshape.
Target: **1904-07-01**, exterior and courtyard, dark glass.

The [published comparison page](https://chicago.polecat.live/4d/dev/walk/glessner-baseline.html#proportion-audit)
now has a 15-row dimension/evidence/decision table and current-model measurements
for all nine T-2200 reference views. The earlier baseline remains selectable and
is explicitly identified as an earlier asset. Model bytes are checked against the
selected measurement record; a newer unmeasured asset is never called verified.

## Controls and method

The authoritative numerical deliverables are
[`audit-report.json`](../../../data/comparisons/glessner/audit-report.json) and
[`section-readings.json`](../../../data/comparisons/glessner/section-readings.json).
They include the dimension table, **15 compatible-material mesh controls**, all
**87 existing photo picks**, frozen cameras, pixel residuals, association distances,
input hashes and exact master/Full/Light hashes. The mesh controls associate within
0.023 m of their nominal locations; this demonstrates implementation consistency,
not historical measurement precision.

The source picks, cameras, 1% targets, normalization widths and outliers from
T-2200 are unchanged. No optimizer runs. Current compatible vertices are associated
again, so tessellation/roof stock can change a residual without moving the building.
Baseline lens/crop sensitivities are retained as **baseline** sensitivities, not
new candidate confidence intervals. Most camera fits touch their assumed height
bound. A roof or finial must not be lowered by converting a residual directly into
feet under an uncertain camera.

| Fixed view | Current withheld RMS, px | Interpretation |
| --- | ---: | --- |
| Prairie front | 7.8 | Cropped facade; does not independently constrain roof depth |
| Taylor northeast | 41.6 | Early form reference; assumed camera bound active |
| HABS northeast | 33.7 | Later retained fabric, not a 1904 survey |
| Northwest stable | 34.1 | Oblique gable/loft control; hidden west roof unresolved |
| North level | 21.6 | Cropped control coverage |
| North inclined | 125.3 | Chimney 139.2 px and north finial 206.3 px remain unresolved |
| Stable detail | 26.9 | Local openings, not full west silhouette |
| Courtyard east | 53.7 | Stair finial 75.7 px; camera/correspondence uncertainty remains |
| Courtyard west | 130.4 | Limited, cropped, ivy-obscured; only one withheld check |

The current north-inclined chimney projects to (875.6, 134.6), versus pick
(975, 232); the tower tip projects to (1373.8, 160.9), versus (1304, 355).
Their horizontal discrepancies run in opposite directions. Re-inspection confirms
the source picks identify the chimney top and visible finial, rather than the
utility-pole top. This does **not** clear the model heights: it shows that a single
vertical scale adjustment cannot explain the disagreement. Baseline camera
sensitivity is 48.1/70.1 px at those features and does not account for the entire
residual either. The unresolved attribution is retained, not dismissed as camera
error or silently hidden by refitting.

## Drawing audit and retained work

HABS sheets **2, 3, 4 and 6** were visually re-read. The first two establish the
plan, including the 74-ft Prairie length, 26-ft-6-in east range, 35-ft-6-in stable
width, 59-ft-9-in stable depth, curved hall and five-facet dining bay. Printed room
dimensions describe the interior; they cannot replace exterior polygon dimensions.

Sheet 4 is a 1963 section with the east courtyard elevation beyond it. A bounded
raster re-reading records actual source identity, normalized picking canvas,
pixel coordinates, scale, approximate uncertainty and every result. It supports
three dormers in the existing sequence, a taller stair turret and a low hall-bow
roof. Small discrepancies in dormer spacing and hood outlines are recorded, not
claimed as exact agreement. Roof apex and finial tip are separate features.

The section suggests approximately **17 ft** between the main courtyard eave and
ridge, while the current sheet-6-based ridge plus reconstructed datum transfer gives
**19.94 ft**. This roughly 3-ft difference exceeds the approximate reading bound.
Sheet 6 is a later photogrammetric front elevation with printed vertical controls
(48.62 ft at north chimney, 24.30 ft at second-floor soffit, 0.00 at door and
−0.74 at the adjacent walk). It remains the stronger existing vertical control;
the house is not shortened to make the earlier section match. A reconciled section
and elevation survey is required to resolve the conflict. The door/walk observation
does not independently prove north-grade equivalence.

The same section re-reading gives the stair turret approximately **7.54 ft** from
eave to cone apex and **9.20 ft** to its finial tip, against the model's **9.80 /
11.80 ft**. That 2–3-ft discrepancy is retained explicitly with the main-roof
question. It is not cleared by the near-zero mesh association distance: the mesh
can faithfully implement an uncertain number. The north cone is closer (about
10.32 ft versus 11.00 ft). Pixel definitions for eave, cone apex and finial tip
are recorded separately. A common vertical translation cannot remove a relative-rise
difference. However, this re-reading transfers the horizontal plan scale vertically
without an independent printed vertical control on the section; scan/drawing scale
and host-versus-ornament line choice remain unresolved. It cannot silently overrule
the later elevation or establish a corrective 1904 turret dimension.

The 54.54° street roof and approximately 56.4° courtyard roof follow the current
centered W13.25 ridge assumption, not a measured roof plan. The 36.996° north street
slope and approximately 34.69° courtyard slope preserve the existing ridge and
projecting eave. Exact recomputed values are in the dimension table; displayed
decimal places describe the model, not source precision.

Retain T-2235's full W141 west ridge at 38.6 ft for the entire 59.75-ft wing,
independent west cross-gable and complete courtyard slope. Its owner-corrected
rear ridge must not regress to 25.5 ft. Retain the connected west dormer,
T-2157 dining hip/crested connection, T-2172 raised upper glazing, and T-2183's
restored principal lights and continuous 24-ft eave. Preserve T-2203–2205 tile,
filtering and roof-edge work. Existing envelope tests independently verify the
roof union and junctions.

## Individual findings and disposition

1. **Confirmed repair — northeast copper attachment/fold (T-2220).** The owner's
   report and existing reproduced view establish the local defect. Attach the
   cladding to its roof host and remove the fold while retaining the envelope.
   Exact historic metal stock is reconstructed. This ticket remains manually held;
   the audit neither duplicates nor activates it.
2. **Unresolved dimensional disagreement — main roof and stair-turret rises.** Reconcile HABS 4/6,
   datum transfer and roof-host versus crest line. Retain current geometry pending
   that reconciliation; confidence is inferred, not a new attested height.
3. **Unresolved comparison — tower/chimney tips and courtyard correspondences.**
   Preserve all residuals and the frozen fit. Independently establish lens/crop,
   camera height and feature definitions before assigning a geometric correction.
   No new historical dimension is claimed.
4. **Description discrepancy — dining-bay projection.** The model outline extends
   from S26.83 to S36.73, **9.90 ft**, while older prose says 10.3 ft. The audit
   corrects the description presented to reviewers; there is no evidence for
   stretching the mesh by 0.4 ft. Source plan fabric is attested, exterior scaling
   inferred. The original provenance record remains historical input to this audit.
5. **Unmeasured details — dormer flare and copper shoulders.** Existing flared
   hoods, low copper bow and dining cap remain bounded reconstructions. Later
   fragments support qualitative inspection, not precise 1904 replacement shapes.
   No additional proportional correction was established. A separate K01 component
   audit (T-2265, PR #603) has assigned coincident-face inspection to T-2267; that
   mesh-topology follow-up is outside this proportions audit and is not executed here.

No new tickets are queued. T-2228 retains final photographic sign-off. The owner’s
other manual holds remain in place. Preliminary central-gable schemes, watercolor
conservatory/fountain, later ivy, utilities, replacement glazing and industrial
alterations remain excluded from 1904 facts.

## Source identity, rights and limits

`source-files.json` records the nine image files inspected again for this audit.
HABS 01 (northwest) and 14 (north inclined) supplement the four drawings; HABS 05
(court, ca.1923), Florian **GX112.24** (roofs/dormers/stair turret, July 1948) and
Nickel (west hood fragment, 1966–67) are restricted **textual cross-checks only**.
No restricted pixels, textures or geometry derived from those references are
introduced. The corrected Florian identity is retained; it is not a stable-court
overview. Their catalog links remain in the ticket and existing library.

The Cornell c.1887 stable reference and early Taylor northeast exposure remain
the programme's early-form evidence. They do not resolve the hidden courtyard
roof or provide a complete west survey. No pre-1904 courtyard photograph or
unobscured whole-west view was recovered. Current correspondence checks reuse
T-2200 observations; this is a re-reading, not nine new archival discoveries.

## Reproduce

```sh
python3 tools/glessner_proportion_audit.py --check
python3 tools/test_glessner_camera_baseline.py
python3 tools/test_glessner_roof_envelope.py
bash tools/publish.sh
# Serve ../../site at localhost:8765, including the research-library paths.
PW_EXECUTABLE=/usr/bin/chromium node tools/qa_glessner_t2206.mjs
```

Run the audit tool without `--check` only to measure a deliberately selected new
asset candidate for the same reviewed structure record. The record hash is pinned:
a changed dimension schedule requires a deliberate review of the table, controls
and dispositions before that pin is updated. Review all changed associations and
hashes before committing a new audit. Never
regenerate the frozen T-2200 baseline to improve a score. No Blender build is needed
for this audit because no geometry, material, source record or sidecar changes.

## Browser and numerical validation

Published desktop 1280×800 and mobile 390×780 both pass all nine comparisons,
Python/Three projection agreement, source image dimensions and rights handling,
Full/Light asset hashes, historical/current measurement switching, deliberately
stale hash refusal, markers, responsive overflow and the real 1904 house-card link.
Six camera-behavior tests pass, including held-out controls not changing the fitted
camera, refusing an altered baseline asset and prohibiting the candidate optimizer.
The existing roof-envelope tests pass 1,800 west and 1,200 courtyard rays.

- [Before, desktop](before-1280.png) / [before, mobile](before-390.png): exact
  pre-audit HTML/JS/CSS from dev `145a1ddc`, intercepted in the browser while loading
  the same current model. The page correctly warned that only old measurements
  were available. The interception method is recorded in `before.jsonl`.
- [After, north inclined](1280-north-inclined.png) / [mobile Taylor view](390-taylor-ne.png):
  actual published page with current measurements and all exceptions retained.
- [Dimension table detail](1280-audit.png). Mobile retains horizontal table scrolling.

`browser.log`, `camera-test.log`, `envelope-test.log` and `audit-check.log` are the
receipts. No restricted reference pixels are included in these screenshots. The
initial two historical-asset assumptions in the old camera tests were repaired;
a browser test fixture also initially altered the master hash instead of the
loaded Full hash on mobile, and was corrected. Neither failure changed the model
or relaxed a camera/asset assertion.

## Integration repair

T-2175 was split into T-2268/T-2269 in the separate ticket repository during
validation, leaving dev's warehouse order assigned to a split ticket. This branch
reuses the exact four-file repair from `c09db4ae` in PR #602: the inventory band,
owner-table fallback and two derived reports now point to T-2268. No roof count,
placement or household changes are imported from that PR. The order-book check
passes. Its remaining F4 sibling is T-2269. This clears the one unrelated failure
in dev's T-2205 CI run; the complete combined-tree gate is still run for this PR.

The dedicated Glessner browser review and stage-12 published smoke use the same
Glessner asset bytes and comparison page as the final change. The smoke's published
order-book metadata predates that owner-pointer repair; it is not represented as
an exact-tree test of the redirected warehouse assignment.

The first integration base is dev `01bf3aaf` (PR #599, Monroe–Adams lots). It
already includes the warehouse owner redirect, so the four-file repair is absent
from the final T-2206 diff. Dev's released changelog is preserved verbatim; only
T-2206 is re-stamped to v1602. The three Glessner GLB hashes and audit inputs remain
unchanged. The 1835 integration is covered by the combined repository gate; the
staged browser smoke predates it and is not an exact-tree claim for its lot changes.

Published stage 12 passes **200 checks, zero failures** (mobile 99, desktop 101),
with zero page errors; `smoke-12.log` is the receipt and the result is recorded in
dev-smoke-state. This is the applicable staged run, not the entire fourteen-stage
smoke. The combined invocation took 21m23s. An earlier invalid `both` viewport
filter selected no viewport and is excluded entirely from this result. Final
source-reading clarifications were then checked on the updated comparison page
at both viewports; they do not alter any camera, mesh or source photograph.

The 806-step repository preflight passed after using compensated summation for
the audit RMS and regenerating the research sign-off counts. Dev then advanced to
`9e0682cb` (T-2259 resident associations). That change merged cleanly; its released
changelog is preserved and T-2206 alone is re-stamped to v1603. A further combined-tree
preflight is run before this merge commit and PR. Final gate and deployment receipts
are recorded with T-2206 in the ticket repository.
