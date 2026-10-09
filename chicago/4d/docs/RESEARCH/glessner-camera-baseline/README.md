# Glessner dated photographic baseline — T-2200

Target: **1904-07-01**, exterior and courtyard only. The comparison page is
`/4d/dev/walk/glessner-baseline.html`, also linked from the Glessner house card.
This establishes an instrument and a defect baseline, **not photographic acceptance**.
No house geometry, source-library metadata or glass behavior changes in this ticket.

## Existing contract and frozen assets

Uses the [T-1843 metric/component contract](https://github.com/kevinrhaas/chicago-tickets/blob/main/evidence/T-1837-prairie-1904-architectural-study/ASSET-CATALOG.md#glessner-comparison-protocol),
the canonical metric schedule and the existing Glessner review-camera coordinates.
T-1843 remains open for its component assembly and whole-scene performance scope.
No second architectural coordinate convention is introduced. The viewer converts the
existing SW bounding-footprint frame (east, north, up in metres) to glTF `[x,z,-y]`.
HABS architectural feet, source locators, north-grade/door uncertainty, full/light/master
and structure/sidecar hashes are in `data/comparisons/glessner/observations.json`.
The asset freeze is dev `caf1c4e3`, including T-2235's restored west roof. Its canonical
recovery archive is still the source of the GLBs. The page warns when loaded model bytes
no longer match; old residuals are never relabeled as measurements of a new asset.

## Method and limits

Nine dated photographs contain **87 distinct manual pixel picks**. Eight core views
have ten picks each (six pose controls plus four withheld checks); the limited 1948
courtyard-west reference has seven (six controls, one check) and does not count toward
the eight-view requirement. Cropped front/north/detail images distribute controls over
the visible openings, not an invented full facade. HABS 13/14 are related views of the
same retained fabric, not independent dating evidence.

A fixed nominal focal length, a fixed principal point at the declared photograph crop
center and a six-degree-of-freedom pinhole pose are fitted to controls only. Scanned
mounts and black plate edges are excluded from architectural control. Check points,
geometry, lens distortion and building scale are never optimized. Assumed camera-height
bounds are reconstructed, not surveyed. Most fits touch that height bound; the report
and page identify them. Changing the assumption can change attribution of an error.

Named nominal metric landmarks are associated with the nearest compatible material
**vertex**, with a separately reported distance. This is a reproducible candidate
association, not automatic feature recognition. Distances over 0.30 m require manual
review. Glass picks carry the declared nominal reveal recess. Source-picking uncertainty
is recorded per point; source dimensions, source hashes and full-resolution pixel
coordinates are retained. Pose and pick uncertainty preclude millimetric conclusions.

Six trials perturb focal length by ±20% and the principal point by ±5% of crop width
or height. Maximum projected displacement is a sensitivity, **not a statistical
confidence interval**. No outlier is discarded. Residuals and RMS are in source pixels.
The proposed target is 1% of projected facade width; it must also pass 1% of the observed
horizontal landmark span and the association-distance check. The latter prevents a
cropped/off-frame or unstable projected width from creating false passes. Individual
green rows do not certify a view or the house. All eight core views retain exceptions.

| View | Controls / checks | Control RMS px | Withheld RMS px | Active assumed bounds |
|---|---:|---:|---:|---|
| prairie-front | 6 / 4 | 3.6 | 7.8 | height |
| taylor-ne | 6 / 4 | 30.0 | 41.6 | height |
| habs-ne | 6 / 4 | 8.3 | 33.7 | none |
| northwest-stable | 6 / 4 | 26.3 | 34.1 | height |
| north-level | 6 / 4 | 17.2 | 21.6 | height |
| north-inclined | 6 / 4 | 18.6 | 125.3 | height |
| stable-detail | 6 / 4 | 13.4 | 26.9 | height |
| courtyard-east | 6 / 4 | 39.0 | 53.7 | none |
| courtyard-west | 6 / 1 | 71.3 | 133.4 | height |

Large residuals can combine geometry mismatch, source-pick/vertex ambiguity and camera
model limitations. They are review leads, not automatically measured construction errors.
North-inclined's large held-out discrepancy and the courtyard correspondences especially
need review before reshaping anything. T-2206 owns roof/bay validation; T-2201 owns the
south courtyard boundary; T-2228 owns eventual photographic sign-off.

## Dating, rights and missing coverage

Taylor 2135 (catalog ca.1889; likely 1887–88) is the early street-form reference. Later
HABS views test retained fabric only. Every feature has an attested/inferred/reconstructed
1904 tier. Design schemes, later overhead stable doors/infill, paving, utilities, signs,
stairs and restored finishes cannot silently establish 1904 condition. T-2235 roof
geometry remains a labeled working reconstruction, not a fact created by a photo fit.

The page displays public-domain/no-known-restrictions images through the existing
research library paths or holder URL. HABS 05's ca.1923 courtyard image and Florian's
July 1948 courtyard-west image remain link-only: numerical observations are supplied,
but their pixels are not newly embedded, copied into this package or used to derive
shipping textures/geometry. Restricted references are not in the committed screenshots.

**No dated, unobscured whole-west photograph was recovered.** Nickel's 1966–67 view is
a roof/dormer fragment; the 1948 courtyard view is cropped and ivy-obscured. The whole
west alley has a repeatable unmatched review stand in the observations, no invented
residual or match count. Courtyard-west is explicitly limited. No pre-1904 courtyard
photograph was recovered. T-2199's published missing-view brief remains the acquisition
list. The neutral isolated viewer is not a whole-scene occlusion or performance test;
no performance ceiling or historical-lighting claim is made here.

## Reproduce and compare a later candidate

From `chicago/4d`, with the canonical GLBs materialized:

```sh
python3 tools/glessner_camera_baseline.py --check
python3 tools/test_glessner_camera_baseline.py
python3 tools/glessner_camera_baseline.py --candidate /path/to/master.glb --output /tmp/glessner-candidate.json
bash tools/publish.sh
# Serve ../../site at port 8765 (both library root and /4d must be available).
PW_EXECUTABLE=/usr/bin/chromium node tools/qa_glessner_t2200.mjs
```

The candidate command uses the frozen poses and denominators; it does not call the
optimizer. Compare both residuals and vertex-association distances. Changed topology
may require an explicitly reviewed correspondence revision, never a silent camera
refit to absorb a geometry change. Regenerating the baseline is a distinct review
operation; `--check` refuses changed baseline asset bytes. `--strict` intentionally
fails while acceptance exceptions remain.

The dedicated browser QA covers nine views, source dimensions/rights, Python-to-Three
projection agreement, full/light bytes, markers, responsive layout and page/console
errors at 1280×800 and 390×780. The walk smoke does not import this isolated page;
its coverage map says so. The changed house-card link is covered by stage 3 and a
1904 card-link check; the release entry is covered by stage 12. Test receipts and
limitations are recorded in STATUS and the PR, not inferred from screenshots.

## Browser review captures

- [Desktop: early Taylor northeast view](desktop-taylor-ne.png)
- [Mobile: cropped HABS Prairie facade](mobile-prairie-front.png)

These are the actual published comparison page, not offline renders. Both source
images have cleared library display status. All other measured views remain
selectable on the page. The limited courtyard-west view is not an acceptance pass.

The public instrument lives under `data/comparisons/glessner/`; the historical
research corpus remains unpublished. `data/research/check_gate_baseline.json`
registers the frozen-asset `--check` as manual, with T-2228 owning final sign-off:
a future model edit must be compared against this reference rather than forcing
the reference cameras to follow the edit merely to satisfy a per-commit gate.
