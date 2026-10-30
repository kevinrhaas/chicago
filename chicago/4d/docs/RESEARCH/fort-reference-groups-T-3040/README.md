# Fort picture-matching checkpoint — T-3040

The shared reviewer now renders a whole compound, not just one blockhouse. This
unblocks T-3041 (the remaining image work under T-2387) and T-2388. It does not
complete either image gate. No building geometry, scene position, structure grade
or source-rights ruling was changed for this tool prerequisite.

## Reproduce the baseline

From `chicago/4d/`, with Playwright and Chromium available:

```sh
node tools/image_gate.mjs --test
PW_EXECUTABLE=/usr/bin/chromium node tools/photo_match.mjs docs/RESEARCH/fort-reference-groups-T-3040/first-fort-panel-1.json --out docs/RESEARCH/fort-reference-groups-T-3040/comparisons
PW_EXECUTABLE=/usr/bin/chromium node tools/photo_match.mjs docs/RESEARCH/fort-reference-groups-T-3040/second-fort-panel-5.json --out docs/RESEARCH/fort-reference-groups-T-3040/comparisons
```

Both pictures are credited to Kurz & Allison, *Chicago In Early Days, 1779–1857*
(1893), panels 1 and 5. `data/sources/kurz_allison_1893.json` records the Library
of Congress holding and public-domain basis on the sheet itself. The existing
high-resolution crops are identified by `tools/measure_plate_join.py`.

These JSON files are **initial comparison cameras**, deliberately outside
`data/reference_views/`: neither is a solved camera or a matching building. The
first scales the north curtain and exposes a roughly 237 px staff-height
disagreement. The second conditional fit reaches its 100 m eye-height bound and
renders an aerial, undersized compound against the nearly level print. Improve
the camera before judging fine geometry. The source drawing may not admit one
physical camera over the surveyed plan. Do not distort surveyed coordinates to
force agreement. The comparison uses a common grade plane, not app terrain.

The first render includes all 21 ticket records plus nine existing context records
(four covered-way segments, armourer's shop, bake house, interpreter's house,
merchant's shop and wharf). The second includes all 21 ticket records. The
`rendered_members` inventories in the match records name every selected phase,
asset, transform and hash. Context membership does not attest hidden structures.

Both reviewed match records say `differs`, with open differences. Preserve that
verdict until actual subsequent renders justify another. A changed camera, image,
mesh or group placement resets review. The CLI waits for every GLB before
capturing; a missing member fails rather than producing an incomplete baseline.

## Parallel picture review: next work by ticket

Six independent reviewers inspected the actual local pictures across all 17
requested tickets. These are implementation leads, not completed matches or new
rights rulings. Keep each original ticket's full image acceptance.

| Ticket | Finding and next concrete work |
| --- | --- |
| T-2372 school | Subsequent owner approval on 2026-10-22 (T-3053) clears attributed project reference use of `eliza_chappel_school_shore_view`; it does not establish the original publication or pictured building identity. The school/annex identity is unresolved and the composed drawing has inconsistent perspective. T-0909 already exhausted the uncredited blog/Young lead; do not rerun that search without a new lead. |
| T-2373 lighthouse | The public-domain Andreas bridge plate shows a domed lantern, cage mullions, finial and gallery rail. `_tower` currently builds an opaque drum, pyramid cap and gallery disk. Add consumed optional details, document reconstructed dimensions, then bake and compare. Do not infer paint from monochrome. |
| T-2374 Cobweb Castle | The 20-vertex centre/wings/tails footprint is reduced to a bounding box by `log_dwelling_params`. Compound massing is not built; a camera cannot fix it. Implement opt-in compound geometry without changing other cabins. |
| T-2375 Dearborn bridge | Both pictures show board parapets; `_railing` builds an open pole rail. Add an opt-in board variant preserving existing defaults. The depicted deck hump and a 21.64 px initial frame-fit RMS remain unresolved. Andreas 1884 is rights-cleared. |
| T-2376 Green Tree | Both pictures show seven long-elevation bays; `_fenestration_gable_front` derives six and ignores `upper_windows`. Add an explicit optional eaves-bay count. Gable windows differ between Braunhold and Trowbridge; the off-centre entrance and low additions also need comparison. |
| T-2377 Hogan store/post office | Current generic cabin lacks the depicted off-centre door, single front sash and gable loft light. Existing consumed `front_set_out`, opening dimensions and `end_openings` can refine it without a new archetype. Proposed resolver-valid initial values: door at 4.6 m, window at 10.2 m, sash 0.55×0.95 m, door 0.85×1.95 m, +x gable light at 0.5 and z 3.35 m, ridge chimney at 0.6. These are inferred starting values, not verified measurements. Register the Cameron illustration's own source, then bake and fit (initial wallpoint RMS 13.1 px). |
| T-2378 Beaubien | Isolate the keyed Beaubien building from the separate Dean house in the panorama. T-0894 withdrew identity with the U.S. Factor's House; do not borrow that house's two-storey description. |
| T-2379 Lake House | `chicago_fort_dearborn_river_mouth_1830.jpg` actually depicts ca. 1836–1849 per `IMAGE_SOURCES.md`. Its finished hotel cannot establish July 1835 construction progress. Preserve the unfinished phase while resolving this temporal mismatch. |
| T-2380 jail | Pictures show a tall jail behind a palisade plus a low keeper's house; model is a low 6.096×4.572 m outbuilding. Catalogue dates the jail compound to 1836, so resolve identity/date before replacing July 1835 geometry. |
| T-2381 Miller | Colbert/Blanchard pictures show log lower storey, vertical-board upper storey and a low side annex. `_frame_addition` clads both floors in horizontal clapboard and puts the old cabin behind. Add opt-in split cladding and side-wing composition; preserve unrelated defaults. |
| T-2382 Carpenter | The annex is a separate structure, not a second hotel wing to re-enable. Refine tall multipane sash and brick stack from the rights-cleared Braunhold plate. Preserve the July 1835 function: former shop/school, current use unattested. |
| T-2383 Sauganash | Group with Carpenter. `sauganash_plate_baseline.json` supplies measured vanishing points (−1467.2, 6462.5), focal 3664.7 px and horizon 917.5 on 2017×1296. Fit translation against the render. Measured 2.392 m doorcase/1.923 m opening and 45 px transom are not fully consumed by `_frontispiece`. Braunhold/Petford/Trowbridge are related compositions, not independent witnesses. |
| T-2384 St Mary's | The later image's open belfry must not be backdated into the July 1835 phase; the original-location phase ends June 1837. Resolve the depicted phase before matching it. |
| T-2385 Tremont | Gifford shows three storeys, a shuttered three-bay gable and five-bay side, raised entrances and flagstaff; model is two storeys. Subsequent owner approval on 2026-10-22 (T-3053) clears attributed project reference use after the Chicagology/CARLI/CHM/Internet Archive investigation. The original sheet's publication remains unresolved; no public-domain finding is claimed. Simply rotating the existing 50×30 ft rectangle would also make the wrong broad gable. |
| T-2386 Wolf Point | The inspected NYPL Blanchard/Shober lithograph bears a legible 1867 publication line. Pictures show parallel gable-front volumes with two entrances and roof-piercing stacks; current model puts core/addition inline. Register that specific source and implement opt-in ridge/entrance composition before solving. |
| T-2387 / T-3041 first fort | Group support is T-3040. First preserve the documented plan and 75 ft staff while reconciling retrospective tower locations. Both blockhouses carry invented separate chimneys absent from panel 1; removing them is a bounded possible refinement after before/after baking. Whistler's 1808 'not yet built' note establishes absence then, not continued absence in 1812. Later completion may be inferred from the retrospective panel with explicit dated provenance; this is not an owner-approval blocker. |
| T-2388 second fort | The unique blockhouse at the right of panel 5 has an absent cupola. Add a consumed cupola option, grade occurrence inferred from this source and dimensions reconstructed, then bake. Do not guess which range carries the pictured gallery. Early 1820 views predate replacement barracks; 1838/1850s views cannot silently govern July 1835. |

T-3041 and T-2388 remain the owners of the full fort matches. No geometry task in
this table is complete. The code PR for T-3040 is only the review prerequisite;
the support slice is exempt from visible progress because it blocks those named
fort comparisons. Future model work must produce visible changes and meet its
image gate.

## Validation checkpoint — 2026-10-22

The final reader-required `tools/preflight.sh` completed with exit 0:
`CHECK PASS — 1047 steps, none red`, including 381 deliberate failure-fixture
self-tests. The operational tickets checkout and generated board were held fixed
through this run. The PR-event changelog check is repeated against the committed
diff before opening the PR because the initial preflight ran before the commit.

Published smoke slices passed at both viewports: mobile 390×780 stage 10,
31 passed / 0 failed; desktop 1280×800 stage 3, 107 passed / 0 failed.
These are the recommended always-on slices for a review-tool change, not the
entire renderer suite. Desktop took 10m30s under CPU contention, exceeding the
documented 10-minute foreground budget; its assertions passed. Results are filed
through `dev-smoke-state.mjs`. No assertion or timing ceiling was weakened.

Both real compound CLI renders completed and were visually inspected. A second
render retained the reviewed `differs` verdict for unchanged inputs. Focused
tests cover group placement and bearings, changed meshes and placements,
malformed or absent members, and stale-review refusal through the actual image
closing gate. Neither fort currently satisfies its original image gate.

### Integration refresh — 2026-10-23

Integrated `dev` at `ad95c276100e6c8c05b90fe97c0f3323e5206df0` and preserved both status entries. The
fort mesh/placement fingerprints remain identical. The newer upstream Glessner
light derivative was restored from its checksum-verified package after preserving
the known prior-package local output; no bake or tracked asset edit was made by
this task. Full reader-required preflight then passed all 1,047 checks again,
exit 0. The mobile/desktop smoke evidence above belongs to the original feature
tree; those slices were not repeated for the upstream building-date UI change.
