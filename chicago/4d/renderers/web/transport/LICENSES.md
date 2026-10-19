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
