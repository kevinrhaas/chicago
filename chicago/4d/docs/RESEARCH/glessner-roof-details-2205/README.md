# T-2205 — Glessner roof-edge details

The 1904 exterior now has closed overlapping ridge caps, raised crest collars,
seated finials, capped dormer hips, layered eave edges, valley strips and chimney
abutment flashing. The new stock follows the existing roof geometry. The folded
northeast courtyard copper connector remains separately held under T-2220.

## Evidence and reconstruction

This is a rereading for a geometry review, not newly discovered historical evidence.
No historic image pixels are used in the assets. Source IDs resolve in `data/sources`.

| Reviewed view | What it supports | Limits and rights |
| --- | --- | --- |
| `taylor_2135_glessner_exterior_1887_1889`, Taylor 2135, c.1887–89, [AIC](https://artic.contentdm.oclc.org/digital/collection/mqc/id/28805) | Repeated raised ridge forms, early street silhouette and layered eave | Public domain. Foreshortening and scan resolution prevent a millimetre stock measurement. |
| `habs_glessner_photo_14_north_inclined_1965`, [HABS north inclined](https://hdl.loc.gov/loc.pnp/hhh.il0118/photos.060916p) | Repeated ridge profile, northern tower terminal, eave continuity | No known restrictions; later corroboration only, not proof of every 1904 detail. |
| `habs_glessner_photo_15_north_stable_1965`, [HABS stable](https://hdl.loc.gov/loc.pnp/hhh.il0118/photos.060917p) | Rounded raised collars and stable eave/gable relationship | No known restrictions. The cropped roof run cannot establish a whole-building collar count. |
| `habs_glessner_photo_05_court_c1923`, [courtyard](https://hdl.loc.gov/loc.pnp/hhh.il0118/photos.060907p) | Qualitative comparison of the previously reconstructed courtyard silhouette | Rights check required: textual cross-check only; no new dimensions, stock or image-derived assets from this view. |

The record already reads approximately **1.16 ft** ridge centres from HABS sheet 6
and the early photograph. This replaces the generator's rounded 0.36 m step with
0.353568 m. Taylor and HABS 15 show the same repeated raised rhythm and broadly
rounded profile. Neither independently verifies an exact whole-roof count.
The generated result contains **233 collars across 11 unobstructed intervals**;
cut pieces at chimneys and joins do not sprout extra end teeth. Counts are model
measurements, not asserted photo counts. Unseen ends and obscured stock remain
reconstructed, with the same uncertainty as the existing HABS-to-1904 carryback.

The inherited 140 mm cap radius, 55 mm seat and finial apex heights remain.
The 80 mm crest rise, 50 mm axial collar width, 18 mm overlap, finial moulding,
60 mm eave fascia with 24 mm lower step, 160 mm valley width, and 2.5 mm metal
stock are bounded reconstructions. Chimney flashing uses a 90 mm apron and
120 mm upstand. These are visibly plausible sections, not surveyed original
profiles. A dated specification or calibrated close photograph can replace them.
No later tar coating or later ornament is carried into the 1904 view.
See `docs/LIBERTIES.md`, L-glessner-roof-edges-2205.

## Geometry and preservation

`masonry_house_v4_roof_edges.py` constructs raw stock, so clay ornaments and
copper do not accidentally acquire tile courses or the distance-filtered
`_ROOF_DETAIL` tag. Ridge runs stop at chimney/cupola footprints; cross ridges
stop at the continuous ridge barrel. Cap bases follow two lower-circle points to a truncated foot 66 mm below
the host ridge, seating the closed body without a tall rectangular skirt.
The upper cap profile and spacing remain those specified above. Closed hip
covers retain the 47 mm radius.
Finials retain all seven positions, apex heights and maximum 132 mm radius.

Eaves use exposed horizontal downhill boundaries, split at collinear junctions
and mitred at shared corners. Fourteen shared concave sloping roof seams receive
clipped valley flanges; thirty-one short sections follow the roof at chimney
abutments. The algorithm does not recut overlapping roof planes or the separately
held copper connector. Closed stock and clipped flanges remove open cap ends and
projecting valley-strip corners without changing roof connectivity.

All **222 actual Full roof hosts** retain their baseline coordinates (compared at 1-micrometre precision).
Twenty-two former tile hosts disappear only because they were four hidden
ridge-roll faces and eighteen tiny finial cone facets, replaced by solid raw
stock. The street and courtyard roof surfaces, fixed comparison cameras, dining
roof connection, tower heights, west roof repair and dark glass are retained.
[The geometry receipt](geometry-validation.json) and
[baseline](baseline-geometry.json) allow that comparison to be repeated.

Light keeps the same collar count and apex/shoulder coordinates, with four
ridge intervals, eight radial finial segments and two hip-cover intervals.
Its cone sampling is capped at 32 angular segments, exclusively for the enabled
Glessner detail record: the largest 2.5451 m radius deviates from the analytic
circle by at most 12.3 mm. Full sampling is unchanged. This trade keeps real
edge stock within Light's existing ceiling: **199,744 / 200,000 triangles**,
88 more than the previous asset. Full download is 52,071,720 bytes and Light
27,014,548 bytes, respectively 1,836 and 528 bytes larger than before.

## Browser review

`PW_EXECUTABLE=/usr/bin/chromium QA_OUT=<directory> node tools/qa_glessner_t2205.mjs`
loads the actual published 1904 app at desktop 1280×800 (Full) and mobile
390×780 (Light). Eight deterministic cameras inspect both ridges, street and
courtyard eaves, dormers, a finial and the two overall silhouettes. Animation is
paused for repeatable captures. These SwiftShader screenshots are not a phone
hardware performance benchmark. Before and after both pass with zero page
errors, failed requests, glass-mode changes or budget overruns.

| View | Before | After |
| --- | --- | --- |
| Street ridge and chimney | [Full](before/desktop-ridge-east.png) · [Light](before/mobile-ridge-east.png) | [Full](after/desktop-ridge-east.png) · [Light](after/mobile-ridge-east.png) |
| West ridge and cupola | [Full](before/desktop-ridge-west.png) · [Light](before/mobile-ridge-west.png) | [Full](after/desktop-ridge-west.png) · [Light](after/mobile-ridge-west.png) |
| Street eave | [Full](before/desktop-eave-street.png) · [Light](before/mobile-eave-street.png) | [Full](after/desktop-eave-street.png) · [Light](after/mobile-eave-street.png) |
| Courtyard eave | [Full](before/desktop-eave-courtyard.png) · [Light](before/mobile-eave-courtyard.png) | [Full](after/desktop-eave-courtyard.png) · [Light](after/mobile-eave-courtyard.png) |
| Dormer hip covers | [Full](before/desktop-dormer.png) · [Light](before/mobile-dormer.png) | [Full](after/desktop-dormer.png) · [Light](after/mobile-dormer.png) |
| Tower finial | [Full](before/desktop-tower-finial.png) · [Light](before/mobile-tower-finial.png) | [Full](after/desktop-tower-finial.png) · [Light](after/mobile-tower-finial.png) |
| Street silhouette | [Full](before/desktop-northeast.png) · [Light](before/mobile-northeast.png) | [Full](after/desktop-northeast.png) · [Light](after/mobile-northeast.png) |
| Courtyard silhouette | [Full](before/desktop-courtyard.png) · [Light](before/mobile-courtyard.png) | [Full](after/desktop-courtyard.png) · [Light](after/mobile-courtyard.png) |

Raw browser receipts: [before](before/browser-validation.json),
[after](after/browser-validation.json). These demonstrate this ticket's details,
not completion of the entire photographic-quality programme.

## Reproduction and validation

The existing pinned Blender 4.5.3 built only Glessner with
`generators/build.py -- --only glessner_house --no-bake`; existing procedural
materials were reused. `tools/web_derivatives.sh --only glessner_house__as_built_1887.glb`
produced Full and Light and repacked the three-asset recovery package.
[Build log](bake.log), [derivatives](derivatives.log), [hashes](build-hashes.json).

- `python3 tools/test_glessner_roof_edges.py --baseline docs/RESEARCH/glessner-roof-details-2205/baseline-geometry.json`: closed concave stock, physical spacing, chimney clearance, eave thickness, counts, Light ceiling and unchanged Full hosts.
- `python3 tools/test_glessner_roof_tiles.py`: 6-inch width / 5-inch exposure and relief tagging retained.
- `python3 tools/test_glessner_roof_envelope.py`: 1,800 roof rays and 1,200 courtyard rays preserve the repaired envelope, intersections and tower datums.

The physical-tile, roof-envelope and recovery-package checks pass; their logs
are stored here. The smoke-budget mapper classifies all structure/manifest changes
as stages 1–14. This bounded 1904-only change is checked directly in the 1904
browser above, plus representative published stage 8 at both viewports for the
shared renderer. The entire fourteen-stage 1835 interaction suite is not rerun;
no renderer JavaScript, 1835 record or 1835 asset changes in this ticket.
Repository preflight passes **806 steps**, with no failures. The published
stage-8 smoke passes **36 checks**, with zero failures. See [preflight](preflight.log),
[full repository receipt](repository-validation.log), and [smoke](smoke-stage8.log).
The PR-event checks are also run against the actual committed range before the PR.
Only the selected T-2205 manual hold was released.

The liberties, Glessner 1904 sidecar and source-use coverage are regenerated.
The three legacy comparisons were rebuilt through the same `emit`
pipeline with their ordinary UV unwrap using [rebuild_legacy.py](rebuild_legacy.py),
then passed through the normal derivative producer. Their master files are
[byte-for-byte identical](legacy-versions-unchanged.json) to their prior versions;
only the shared-generator freshness receipts change. The current detailed house
retains its authored physical UVs. Its rebuilt master, Full and Light hashes all
match the final reviewed screenshots.

The final branch incorporates dev's separate T-2258 household-card and T-2250
boarding-house business changes. The
published stage-8 smoke above was taken before that integration and the final
ridge-base seating adjustment. Neither changes 1835 meshes or the shared 3D renderer;
the final 1904 assets receive the complete sixteen-view review above.
