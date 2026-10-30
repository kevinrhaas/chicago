# Transport study licenses

All studies use original procedural geometry, solid PBR colors and no external photographic textures, tracing or extracted dimensions. These are technical studies, not finished historical reconstructions. Three.js is the existing separately licensed vendor dependency; no second vendor copy is included.

| Study | Generator and geometry | Basis |
| --- | --- | --- |
| `wagon/` | GPL-3.0-or-later, project-derived original work | Existing explicitly reconstructed wagon dimensions in `data/yard/town_trade_goods.json` and running-gear arrangement in `yard.js`. Those are not measured Chicago artifacts. |
| `carriage/` | GPL-3.0-or-later, original work | Independent engineering reconstruction; no rights-pending image derivation and no claimed manufacturer or historical owner. |
| `horse/` | CC0-1.0, original work | Independent anatomical/articulation study; no source pixels, base meshes or textures. No particular breed or individual animal is asserted. Integration code is under the project's GPL license. |

Harness generator and geometry are original CC0-1.0. The component list and 25.4 mm trace width use John Moore’s New York 1891 published text; US public-domain reasoning and exact source URL are recorded in the harness manifest. Source images and plates were not used. Unmeasured shapes, dimensions and routing remain reconstructed.

Generated GLB files, JSON notes and browser fixtures retain these terms. See `docs/RESEARCH/period-transport-2026-10-18/` for validation and limitations, and `data/transport/studies/` for the geometry inputs. Dimensions, surfaces, color and gait in these studies are reconstructed or conjectural, not attested.

## W01 wheel refinement: original reconstruction (2026-10-19)

The enabled W01 study uses original tapered octagonal spokes (hub section35×32mm, felloe22×22mm), retained radial endpoints and1.2mm board/stave chamfers. These dimensions and reduced board-color contrast are engineering choices, not source-attested1835 joinery, wear, paint or photographic measurements. GPL-3.0-or-later remains unchanged; no third-party material is introduced.

| Generated/reproducible file | SHA-256 |
| --- | --- |
| `tools/transport/generate_wagon.py` | `9f3879f05734bf78bcddd4e564464244c0f11c4c5242466770becf1398599934` |
| `data/transport/studies/wagon.json` | `0a317cd45c514866a0a43ec5c208b93b5f2832de415e2551a0a4be146836e103` |
| `renderers/web/transport/wagon/wagon-w01.glb` | `7749a0199b93bd196ecf6c3482af8ec537f1420a38f6fac88ab79fd8f34d44aa` |
| `renderers/web/transport/wagon/wagon-w01.json` | `ea3705651f11ddddcc33595abffd7ee0c3cffb7ae94fc18967c65883fb15243f` |

## C01 upholstery rounding: original reconstruction (2026-10-19)

Three cushion shells use original20mm rounded edges with four samples per quarter edge. Radius, shell construction and unchanged original colors are unmeasured engineering choices, not source-attested upholstery, compressed cloth/leather, historical interior or photographic materials. GPL-3.0-or-later is unchanged; no external pixels, textures or sourced geometry are introduced. Existing1904development-only eligibility remains.

| Generated/reproducible file | SHA-256 |
| --- | --- |
| `tools/transport/generate_carriage.py` | `167f163962fe6f6b12b0b6a09b696188b23d21dbd37071a00e95ac4975bfb856` |
| `data/transport/studies/carriage.json` | `3268082b9a8f90a2288a49db16f95de5acb732ac6d589b568ed8b53b11dbbf6f` |
| `renderers/web/transport/carriage/carriage-c01.glb` | `5d4038fcb1e0982100c776239d649de21035098e019d5fa5d0c399427f15a062` |
| `renderers/web/transport/carriage/carriage-c01.json` | `118a614a3a2d67352bb3f1b48cac4e6371523bee4320f0ccb6c5d35fed68135c` |
| `renderers/web/transport/carriage/parameters.json` | `3268082b9a8f90a2288a49db16f95de5acb732ac6d589b568ed8b53b11dbbf6f` |


## Original paired equine head/neck and headstrap refinement (T-2800/T-2801/T-2803)

CC0-1.0 original generated geometry and original generator source: `tools/transport/horse_geometry.py`, `tools/transport/generate_horse.py`, `tools/transport/generate_harness.py`; original parameter data `data/transport/studies/horse.json` (unchanged) and `data/transport/studies/harness.json`; derived `renderers/web/transport/horse/{equine_light_harness_skinned_prototype_01.glb,manifest.json}` and `renderers/web/transport/harness/{light_breastcollar_harness_reconstructed_01.glb,manifest.json,geometry-stats.json}`. Exact hashes are recorded in `docs/RESEARCH/period-transport-2026-10-18/head-neck-refinement/integration-inputs.json`. No external model, texture, source pixels or traced plate geometry. Research text informs provisional anatomy/construction but does not attest a horse, owner, breed, exact anatomy or strap dimensions. Original additions retain CC0-1.0 SPDX headers. Demo/integration and reused project fit methodology remain under the project's existing GPL license; CC0 geometry does not relicense those tools. Documentary screenshots/receipts are original diagnostic outputs, not source photographs.


## Grounded trot study (2026-10-19)

Original grounded-trot engineering addition (T-2803): tools/transport/horse_geometry.py, unchanged original tools/transport/generate_horse.py, data/transport/studies/horse.json, generated renderers/web/transport/horse/{equine_light_harness_skinned_prototype_01.glb,manifest.json} contain project-original CC0-1.0 procedural geometry/solver/animation/data; no externally copied program/model/texture or image tracing. Original3Dtwo-bone solver uses geometric sphere intersection and shortest-arc quaternions. renderers/web/transport/horse/{demo.js,index.html} and diagnostic test glue retain project's existing GPL license. No source-bounded measured biological gait or historic animal identity asserted. Concrete checkpoint hashes are in `docs/RESEARCH/period-transport-2026-10-18/head-neck-refinement/trot-inputs.json`.

## C02 enclosed carriage reconstruction (T-2794,2026-10-19)

Original project-derived GPL-3.0-or-later source/geometry, based on the already licensed C01 procedural conventions; C02 is standalone source, not a runtime import or downloaded base. Exact source/input/output hashes are in docs/RESEARCH/period-transport-2026-10-18/c02-enclosed-door/INTEGRATION-MANIFEST.json. New files are tools/transport/generate_carriage_c02.py, tools/transport/test_carriage_c02_door.py, tools/transport/smoke_carriage_c02.cjs, data/transport/studies/carriage-c02.json, tools/transport/fixtures/carriage-c02-flag-off.json and renderers/web/transport/carriage-c02/{carriage-c02.glb,carriage-c02.json,parameters.json,index.html,demo.js}; gallery/orchestrator changes and original documentary receipts/screenshots retain projectGPL terms. No external model/texture/sourcepixels or proprietary program code is included. ExistingThree/vendor remains separately licensed and is not copied. No asset under assets/ is added; this entry records original generated-output provenance, not a CC0 external-asset exception.

All cabin/hardware/color dimensions are reconstructed. Reference catalog wording is 'No known restrictions on publication', not a new unconditional license. No rights-pending local photo or unseenWareplate derivation, attested ownership/subtype or historical paint is asserted. BaselineGLB SHA256 93d4020036e5c685ce95010fe64b26c55a1561db4517405f0590f7a398253331.


**Metadata and articulation qualification:** The pre-door project scope quotation is preserved separately with its original branch and explicit non-period origin; the enabled branch now describes reconstructed rigid door/hinge geometry and endpoint transforms. Current model metadata hash is 93d4020036e5c685ce95010fe64b26c55a1561db4517405f0590f7a398253331 (860956 bytes). Corrected checks bind all 424 actual moving triangles to the unique active exported door and compose actual hierarchy transforms at each angle; closed-world shape alone cannot qualify detached geometry. Old closed-mapping/source-posed receipts are retained only as limited historical checkpoints. No continuous/occupant/photographic acceptance or installed-head gate is implied.


Parked W01 `parked-wagon/wagon-w01.glb` and sidecar: original GPL-3.0-or-later reconstructed geometry with original CC0-1.0 procedural maps, source in tools/transport/wagon_parked and assets/authored/transport/wagon_parked.
Parked C02 `parked-carriage/carriage-c02.glb`, sidecar and recipe: GPL-3.0-or-later original geometry/cushions/finish/maps, with CC0 helper code retaining its own SPDX. See parked-carriage/LICENSE. No imported photographic texture or identified historical owner/maker is supplied.

`parked-carriage/shaft-rest.glb` and shaft-rest.json: original GPL-3.0-or-later reconstructed timber support, reproduced by tools/transport/produce_carriage_shaft_rest.py from actual carriage shaft underside and disclosed chosen trestle dimensions; no external image pixels.

## Original selected covered W01 derivatives (T-2980)

`covered-wagon/{covered_w01_western_blue,covered_w01_wolfpoint_oak}/{covered-w01.glb,covered-w01.json}` and `covered-wagon/LICENSE`: original reconstructed project-derived GPL-3.0-or-later geometry/source, with original CC0-1.0 analytic pixels. Reproduced by `tools/transport/generate_covered_wagons.py` from the original pinned W01 source chain and `data/transport/parked/covered-w01.json`; source/product hashes and original per-ID coat/age/yoke lineage are recorded in `assets/authored/transport/wagon_covered/SOURCE.json`. Five bows, canvas construction, seams, folds and weathering are original reconstruction, not an attested maker or historical wagon. No imported model, scan, photographic pixels, historical owner/load, occupied socket, horse or ride claim.


## V18 catalogue-guided Brougham lamps (T-2794)

Original project GPL-3.0-or-later source and generated geometry: `tools/transport/brougham/{generate.py,lamp_geometry.py,source_details.py,quarter_surface.py,index_streams.py,static_master.py,parameters.json,lods.json,rear-quarter.json,ring16-mid-lods.json,LICENSE}`. Current V18 near raw SHA256 `99f2ca33f0228d486db274f461c59eecdfa19dcb70d1eb2c080c30d4d5456b4a`, indexed SHA256 `bce1ecc757a7175cb193b1263fc8dbcdf1ce76a263916d3cff5e41dc4a835938` (33,374 triangles). Current mid raw SHA256 `f184d0fc96ecca92ae4ed51a57c468e9cf7e689264865ae45b23ccb007236f0d`, indexed SHA256 `65eec8b7e04e636c90e2d797f5e7e8c1d2695f0f45c6fb5c7f340f73e5616fa1` (11,706 triangles). The existing ring16 distance recipe uses 480 near and 314 mid subdivision records. Protected non-lamp positions/normals, seven materials, nodes, anchors, contacts and original conservative collision proxy remain exact; only the reconstructed lamp form changes. No external geometry or image textures are used.

The public-domain appearance reference is US1893 Studebaker catalogue leaf0095, source `studebaker_1893_illustrated_souvenir`, plate SHA256 `b458565ec06ba1e8e59d1455cc2d3f277c2371910b3085c2085749fc59a68abe`. No plate pixels are embedded. Maker/design availability is evidenced; this specimen, owner, stop, absolute dimensions, hidden construction and optical materials remain reconstructed. No Pullman/Glessner ownership is claimed. Rounder twin-faced lamp heads replace the earlier tall angular cages; a fixed-camera software projection comparison supports that limited form improvement, not Three PBR, browser, world, photographic or occupied acceptance. New native desktop/mobile image acceptance remains false after environment-limited launches. Eight earlier native views applied only to historical V17 distance appearance and are not transferred to V18. V17 source/contracts/metadata/receipts are retained explicitly as historical under `tools/transport/brougham/archive-v17/`, with its original GLBs in PR1175 Git history. The earlier22,238-triangle mid likewise remains historical. No Brougham file is added under assets/.

## W01 fine-grained timber material increment (T-2793)

`parked-wagon-fine-wood/` uses unchanged original project W01 geometry and project-authored UV/tangent/index charts (GPL-3.0-or-later). Side timber pixels derive from [Fine Grained Wood](https://polyhaven.com/a/fine_grained_wood), Rob Tuytel / Poly Haven, [CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/); original paint, iron and cut-end pixels remain CC0. Native2K maps were rotated, cropped, reduced2x, narrow8pxperiodic edge blended, and albedo given bounded1.5linear exposure; GL normal vectors were correspondingly rotated and renormalized. This is a modern optical analogy and reconstructed brown finish, with no species/date/coating/maker/Chicago-specimen attestation. Photographic/world/budget acceptance remains open. Source map URLs, official hashes and derivation are in `assets/authored/transport/wagon_parked_fine_wood/SOURCE.json`.

The authored binding files `assets/authored/transport/wagon_parked_fine_wood/{surface.json,surface.bin}` combine original project GPL-3.0-or-later UV/tangent/index charts with the documented CC0 image derivatives; the geometry is freshly regenerated by `tools/transport/generate_parked_wagon_fine_wood.py` through the unchanged original W01 pipeline. `ATTRIBUTION.txt` and `SOURCE.json` preserve creator, URLs, source hashes and transformations. The installed `renderers/web/transport/parked-wagon-fine-wood/wagon-w01.glb` SHA256 is e1e5b4f1d7dfe6bf08cca21e8cfae2e88748a3f6e6c6959753334ae2b0c84dd8. The original parked-wagon asset remains unchanged. The two covered variants retain distinct finish families and take only the separately documented cloth-drape increment.

The covered-cloth refinement under T-2980 changes only the reconstructed inter-bow drape constants (8–10mm to20–28mm over750mm spans), retaining original GPL geometry/source lineage and CC0 analytic texture pixels. Current source/product hashes are in `assets/authored/transport/wagon_covered/SOURCE.json`: core679fc439, blue GLB aaffa339, oak GLB22072e6f. Variant identities, seeded finish colors/aging, yokes, pivots, stands and newer terrain qualification are preserved. This is not an attested historic textile form or physical cloth simulation.


## Canonical26 planted-standing horse (T-2800/T-2803)

`standing-horse/horse-sevket-v16-planted-standing-v1.glb`: CC BY4.0 derivative of “Horse” by sevketkabatas, https://sketchfab.com/3d-models/horse-53a6eb7ccf054aa2a378dd7ec08f88fe. Exact b479442cb03ac46eb13c19da15a79cdfaf28dbdf356b116f78de7ce7ecdc60be,3,783,600bytes. Canonical-metre surface, reconstructed26 rig/V16skin and planted12s body shift; no original head/tail or walking playback. Hierarchy analogy only: antemeossa Rigged Mid-Poly Horse, CC BY4.0, https://sketchfab.com/3d-models/rigged-mid-poly-horse-fea999c1d8d64eb4a9c2bb1fac1e7d83. Exact rights/change notices and mirrored authored binary are in assets/authored/transport/horse_standing and assets/LICENSES.md. Selected runtime dielectric metalness0 is explicit. No historical individual/breed/photo/gait/riding approval.
