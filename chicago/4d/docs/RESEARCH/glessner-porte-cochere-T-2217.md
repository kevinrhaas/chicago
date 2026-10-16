# T-2217: Glessner carriage leaves and passage

Door refinement for the 1904 exterior, following the merged T-2219 service-junction repair.

Both leaves already existed. The old mesh drew 36 rectangular raised panels, one small rectangular handle per leaf, and no continuous iron straps. T-2202 already replaced the audit's grass passage with paving, so this work preserves its threshold, approach and courtyard connection.

Read sources:

- HABS IL-1015 sheet 6, the 1965 east elevation: two leaves, each three panels across and six high, circles around square fields, a middle strap with paired ring plates. This unrestricted drawing is the geometric reference. It depicts the original door pattern despite the documented later replacement; it is not treated as independent proof of unchanged 1965 fabric.
- HABS descriptive data, printed p.21 / PDF p.22: the original carriage door in a 1945 photograph had two heavily paneled leaves with heavy iron straps and latches. This supports continuity of the type, not precise metalwork dimensions.
- George Glessner's circa-1888 photograph, museum reproduction, and Florian GX112.10, July1948: visually cross-checked. Both show the circular/square fields and straps. The museum scan remains rights-pending, and the Florian photograph is copyrighted; neither supplies copied pixels or a traced asset here. No museum photograph is committed with this implementation.
- Museum restoration page re-read: oak leaves installed June2023; ironwork May2024. These replacements are not independent evidence of1904.

The confusing Florian image IDs were corrected by T-2198: the record named `a18-gh-florian-1948-ne-exterior` is the doors (GX112.10), while the porte-cochere-named ID is the courtyard (GX112.21). Their corrected captions remain intact.

Built mesh:

- Both oak leaves retain the existing reconstructed82-degree open position. The same generator supports a diagnostic0-degree pose, without adding an app control.
- Each leaf has18 real circular recesses tapering to square fields. Full uses64 circle segments, Light8. Both retain the straps, lock plates, rings, thickness and hinges; Full adds scrolls, beveled plates, pyramidal studs and shallow board joints on the unseen reverse.
- The hinge axes sit behind the leaf thickness. Two fixed oak jamb linings and rear hinge brackets fill the side gaps while allowing the entire leaf to swing inside the tapering passage.
- Moving bottoms stand15mm above the existing passage's highest paving; fixed linings seat into it by2mm. The passage soffit, brick reveals, paving and ground layout otherwise remain as accepted.
- Grain coordinates are assigned in each leaf's own frame before rotation, including correction for the builder reversing a face's vertex order. All microgeometry is marked reconstructed.

Bounds to record: leaf thickness90mm (plausible75–115mm), field relief35mm (25–45mm), ring radius about59mm (50–75mm), hinge setback280mm behind exterior face (hidden construction, not measured), side hinge inset85mm (60–100mm), leaf floor clearance15mm (10–25mm). Panel center shares and unmeasured metalwork curves are reconstructed within the HABS pattern. The plain boarded reverse is not visible in the historic references and is explicitly reconstructed. The dark-oak and iron materials are the existing reconstructed finishes; monochrome photographs do not establish their color.

Current resolved aperture is2.3714m wide and2.3592m high. Preserve the approved opening/ground controls; the circa1888 reproduction's apparent aspect differs, and no claim of a calibrated perfect photographic match is made from this front-on diagnostic. Whole-house camera/grade/proportion reconciliation remains withT-2228. Do not set a false `matches` verdict.

## Validation and review

`python3 tools/test_glessner_porte.py` casts rays through all 36 emitted fields in both tiers: each is recessed 35 mm, with a continuous oak surround and a closed reverse. Six swing angles from 0 to 82 degrees clear the tapering reveals by at least 42 mm and paving by at least 15.6 mm; fixed linings do not intersect moving leaves. Closed stiles leave a 12-mm operating joint. Metric UVs remain noncollapsed, including reversed face winding, at 0, 37 and 82 degrees.

[Unrestricted HABS sheet-6 crop](glessner-porte-cochere-T-2217/habs-sheet-6-door.png). Source: Library of Congress HABS IL-1015, 1965 measured east elevation. The museum images are cited above but not copied here.

[Full closed comparison](glessner-porte-cochere-T-2217/closed-full-habs-comparison.jpg) · [Light closed comparison](glessner-porte-cochere-T-2217/closed-light-habs-comparison.jpg).
These use the same generated members as the open scene, exported by
`python3 tools/glessner_porte_diagnostic.py --out <temporary-directory>`.
`closed-diagnostic-camera.json` records a front-on inspection, explicitly not a
calibrated historical camera. The drawing has been resized for the side-by-side;
its pixel aspect is not used to claim a measured aperture size. Full preserves
smooth circles and reconstructed scrollwork; Light keeps the pattern and rings
with reduced facets. Neither view establishes unrecorded reverse construction.

The before views show the previously approved passage, with the old rectangular
panels: [entrance](glessner-porte-cochere-T-2217/before-mobile-porte.jpg) and
[passage](glessner-porte-cochere-T-2217/before-mobile-passage.jpg).


## Canonical asset measurements

The rebuilt Full master and web derivative each contain 1,307,994 triangles and
28 primitives. Light contains 199,427 triangles and 25 primitives, below its
unchanged 200,000 asset ceiling. All three have zero coincident faces; K01 scale,
origin and metric-UV checks pass. The lossless recovery package verifies against
the generated assets. The compressed Full/Light files are 53,372,528 and
27,822,788 bytes. These are inventory costs, not a frame-rate claim.

A new north-leaf close-up of the **before** scene exposed a pre-existing Full
frame call-count breach: 4,443,344 triangles and 340 calls against 4.6M/330.
There were no page/resource errors. This reading predates the new door asset;
the final published measurements below distinguish it from the change's cost.

Published Light at 390x780 passes all five stands: entrance, passage, north leaf,
south leaf and outward passage. The largest frame is 1,062,261 triangles and
212 calls, below the unchanged 1,190,000/330 phone limits. There are no page or
resource errors. The Images tab loads all 116 credited tiles. Receipts and
captures are in [after/](glessner-porte-cochere-T-2217/after/).

Full published 1280x800 covers the same five stands without page or resource
errors. Frames measure 3,865,368 / 3,837,409 / 4,465,836 / 4,249,539 / 4,013,138
triangles, and 218 / 215 / 340 / 238 / 237 calls. The new doors add 22,492
rendered triangles at the north-leaf stand and **zero calls** compared with its
before capture. All triangle counts fit the existing 4.6M Full ceiling.

The previously unmeasured close-up's 340-call baseline exceeds the old 330 cap.
Under the owner's standing Full-headroom ruling, this inspection now declares
360 calls (5.9% over the measured peak); ordinary scenes, Balanced and Light
retain 330. This changes the reported Full allowance, not the rendered scene.
The tightest stand and a Full-to-Light-to-Full setting round trip are rechecked
on the final published renderer; the initial five-view receipt retains its
honest old-cap failure instead of being rewritten as a pass.

[Reverse inspection](glessner-porte-cochere-T-2217/closed-reconstructed-reverse.jpg)
shows the explicitly reconstructed vertical boarding, sealed backs and hinge
stock. The historical references do not show this face; this is a construction
review, not a source match.

The final published north-leaf check passes at 4,465,836 triangles / 340 calls.
The real Full -> Light -> Full setting round trip restores exactly
4,600,000/360 -> 1,190,000/330 -> 4,600,000/360, without page or resource errors.
[Final receipt](glessner-porte-cochere-T-2217/after/browser-validation-desktop-final.json).
The passage inspections also verify continuous soffit/reveals and the retained
T-2202 paving; its original finish is not independently established by the door
photographs. The existing material reconstruction is retained.
