# Glessner surface finish — T-2226

Exterior/courtyard only, 1904-07-01. This pass restores mortar courses to plain brick surfaces and aligns rear-gate grain to the actual timber members. It preserves the owner's grey-greige granite, dark-glass setting, existing July light and physical contacts. Whole-house photographic acceptance remains with T-2228; the five existing historical match verdicts must remain honest.

## Evidence and before views

All sixteen Full captures (eight fixed stands, actual July light and a capture-only neutral diagnostic) and eight Light phone captures were actually inspected before implementation. `baseline-visual-review.json` records each reading. `baseline-assets.json` ties the local published assets to T-2225's verified dev deployment. Cameras, projection, exposure and dark-glass mode are retained in the raw browser receipts.

The neutral diagnostic removes the scene environment, whitens the sun and supplies a white hemisphere. Every capture asserts exact restoration of the environment, exposure and all original lights. It is not a production-lighting change. North stone remains readable under both lights; its stronger blue cast is primarily illumination. Sunny granite retains texture without white clipping. Court brick, limestone and seated supports remain distinct. These observations do not justify a global exposure lift, new granite tint or blanket contact-shadow multiplication.

The Light stair cheek, support piers and long boundary wall have clay grain but no mortar courses. Full has modeled brick joints there. Gate ledges and braces have vertical grain that merges visually into the boarding. Those are the confirmed visible targets.

HABS measured drawings and the licensed w_lemay courtyard references bound construction and material separation. The 2024 photos do not measure 1904 RGB, weathering, foliage or paving. The 1923 family account is a textual comparison only: its underlying reuse rights remain unresolved. It describes unglazed red tiles, pinkish common brick with grey limestone and exterior iron protected from rust. No new asset derives from that text, and no modern patina or neglected mid-century deterioration is copied.

## Implementation and limits

The new original 1024-pixel periodic maps reuse the existing clay/mortar studies and kiln palette, with exact sRGB transfer and linear data maps. They carry eight bricks by thirty-two half-bond courses, using the existing 215.9 by 66.675 mm module and 9 mm joints. The 5 mm recess is a normal-map reconstruction. A separate material is restricted to previously plain faces; individually modeled bricks are not double-gridded. No directional shadows or invented grunge are baked into the albedo.

Gate grain follows each ledge/brace axis in physical metres through both exporters' existing SurfaceUV path. Cut ends retain a full-rank generic oak mapping; no measured end-grain rings are claimed. Tests compare finish-on/off geometry, confidence, rails, supports and hinges exactly and check metric mapping and valid normals. Earlier profiles retain their original surfaces.

New material maps add one material primitive and 3,706,972 bytes to Full web / 3,706,868 bytes to Light. This measured download cost remains explicit in the T-2227 performance audit. The Light geometry ceiling remains 200,000 triangles. Software-renderer captures are not a physical-GPU FPS result.

## Existing budget failures

Before edits, Full north shade uses 299 calls/4,618,485 triangles and north close 300/4,616,007, above the unchanged 4,600,000 triangle limit. Light north shade uses 196/1,534,402 and north close 185/1,476,142, above the unchanged 1,270,000 limit. Both diagnostic programs exit 1 for these failures; no browser errors, failed requests or app problems occur. The other six stands pass their existing budgets. T-2227 owns the scene performance work. Do not reframe these cameras or weaken the limits to hide the readings.

## Completed component review

All twenty-four after images were actually viewed: eight Full scene views, their eight neutral-light counterparts and eight Light phone views. The new plain-brick joints and member-aligned gate grain are reviewed in `after-visual-review.json`. Cameras, projections, exposure, dark glass and budget thresholds match the baseline exactly; every diagnostic restores the original lighting rig. No page errors, failed requests or loader problems occurred. The original north-view budget failures remain failures, and both before/after programs preserve exit 1. SwiftShader counts are not hardware-GPU FPS.

| Tier | Stand | Light | Calls before / after | Triangles before / after | Within unchanged scene budget |
|---|---|---|---:|---:|---|
| full | north-shade | scene | 299 / 300 | 4,618,485 / 4,618,463 | no — T-2227 |
| full | north-shade | neutral | 299 / 300 | 4,618,485 / 4,618,463 | no — T-2227 |
| full | north-stone-close | scene | 300 / 301 | 4,616,007 / 4,615,985 | no — T-2227 |
| full | north-stone-close | neutral | 300 / 301 | 4,616,007 / 4,615,985 | no — T-2227 |
| full | prairie-stone | scene | 221 / 223 | 3,819,581 / 3,819,581 | yes |
| full | prairie-stone | neutral | 221 / 223 | 3,819,581 / 3,819,581 | yes |
| full | prairie-stone-close | scene | 220 / 222 | 3,816,773 / 3,816,773 | yes |
| full | prairie-stone-close | neutral | 220 / 222 | 3,816,773 / 3,816,773 | yes |
| full | court-west | scene | 208 / 210 | 3,717,848 / 3,717,848 | yes |
| full | court-west | neutral | 208 / 210 | 3,717,848 / 3,717,848 | yes |
| full | stair-support | scene | 212 / 214 | 3,724,810 / 3,724,810 | yes |
| full | stair-support | neutral | 212 / 214 | 3,724,810 / 3,724,810 | yes |
| full | gate-court | scene | 199 / 200 | 3,650,398 / 3,650,376 | yes |
| full | gate-court | neutral | 199 / 200 | 3,650,398 / 3,650,376 | yes |
| full | boundary-brick | scene | 293 / 294 | 4,540,610 / 4,540,588 | yes |
| full | boundary-brick | neutral | 293 / 294 | 4,540,610 / 4,540,588 | yes |
| light | north-shade | scene | 196 / 198 | 1,534,402 / 1,534,402 | no — T-2227 |
| light | north-stone-close | scene | 185 / 187 | 1,476,142 / 1,476,142 | no — T-2227 |
| light | prairie-stone | scene | 115 / 117 | 813,331 / 813,331 | yes |
| light | prairie-stone-close | scene | 112 / 114 | 774,179 / 774,179 | yes |
| light | court-west | scene | 95 / 97 | 604,940 / 604,940 | yes |
| light | stair-support | scene | 96 / 98 | 601,901 / 601,901 | yes |
| light | gate-court | scene | 88 / 90 | 565,461 / 565,461 | yes |
| light | boundary-brick | scene | 156 / 157 | 1,222,642 / 1,222,642 | yes |

Canonical Full/web geometry remains 1,371,506 triangles; Light remains 199,850, below its unchanged 200,000 house limit. Primitive counts are 31 / 28. K01 reports zero coincident faces and passing scale, origin and metric UV checks. The 112 actual exported gate-member corners were decoded from master and meshopt Full/Light: UV errors stay below 2.7e-8 cycles; maximum web position deviation is 0.571 mm. The full stone AO cache matches the unchanged mesh and was reused.

The phone confidence display, reconstructed surface liberty and Images panel were actually viewed; all 124 credited image tiles loaded. The five registered historical pairs were re-rendered and visually reviewed at unchanged cameras. All remain `differs`: this component does not resolve the tower cone, remaining opening correspondence, stone shape/coursing or terrace-section discrepancies. T-2228 owns final photographic acceptance.

Focused material, contact, vine and export checks pass. The original map writer was measured twice in an isolated fixture; outputs reproduce and its check mode writes nothing. The initial test fixture lacked ordinary modeled brick, so it was expanded on both sides without weakening the assertion. Validation passes with 0 errors and 263 pre-existing warnings after compilation of the new liberty. The unrelated regenerated resident workbook was restored only after proving all cells/formulas and all XML tree content identical; differences were serialization only.

Full local preflight and exact-head integration CI govern merge. The ticket-linked PR carries those results and public-dev verification. No hardware-FPS or whole-house photographic-match claim is made by this component review.

## First preflight and measured storage allowance

The first full preflight refused the new surface pass at **262.262 MiB** against
256 MiB. The original 1024-pixel joint maps add **7,413,840 bytes** across the
Full and Light assets; their geometry counts remain unchanged. The complete gate
reported this as its sole failure in 890 steps. This failure is retained in the
T-2226 evidence and is not described as an initial green run.

`site_budget.py` finds no identical-file waste over 64 KiB. A read-only price of
minifying every published JSON file saves **5.435 MiB**, insufficient to cover the
6.262 MiB overrun; the readable-record decision in docs/SITE-BUDGET.md §6 remains untouched. The
reviewed material maps and all public research records are preserved.

The whole-tree **repository-hygiene** allowance is now **288 MiB**, with
**25.738 MiB** of measured headroom. The 90% warning still fires on this tree, and
the duplicate-content guard is unchanged. This is a declared storage re-budget,
not a change to the visitor boot allowance, Full/Balanced/Light scene limits or
the 200,000-triangle Light house ceiling. T-2227 still owns the recorded scene
performance failures and the added asset-transfer cost.

This checkout carries 129.136 MiB outside `site/4d/`; two full 288 MiB app
allowances plus that measured content total **705.136 MiB**, below the 1 GiB
platform limit recorded in docs/SITE-BUDGET.md §4. That is a capacity calculation using the current
checkout, not a claim that both deployment branches were rebuilt here. Future
changes still need their own gate and measured visitor costs. Exact byte counts,
alternatives and limitations are in
`docs/RESEARCH/glessner-finish-T-2226/site-budget-reprice.json`.


## Integration with the current dev tree

The pre-integration re-budget run passed all **890** repository steps, with post-commit changelog and ID checks also passing. The branch then integrated dev `ca355afeb16b41217ae6b155c8c53760c8f421a7`, including T-2501's Hardscrabble research and T-2487's two 1812 houses. Both complete authored liberty sections are preserved; generated JSON was rebuilt from the combined sources. Re-derivation settled after two laps, with the final lap changing nothing.

All three reviewed Glessner asset hashes and sizes remain exact, and the historical camera/match files are unchanged (`integration-assets.json`). The combined register contains 561 liberties; every current-dev entry and the T-2226 entry survive exactly (`integration-liberty-audit.json`). The audit workbook's XML trees, cell values and formulae are unchanged; only serialization differed, so its original bytes were preserved. Canonical scale/UV/contact and changelog checks pass. The complete integration preflight and exact-head published smokes remain required before merge; this section does not claim them in advance.


The subsequent integration also preserves dev's T-2489 1812 exclusions and source-use changes (40979ecf). Its source-index conflict was regenerated by the repository manifest. The reviewed Glessner master, Full and Light assets and historical camera/review files remain unchanged; the additional integration asset receipt records the base.


The fort/apron integration (8cc2ab7e) preserves the newer dev records and every compiled dev liberty, alongside the unchanged Glessner surface liberty. The affected derived chain was regenerated to a stable result; the exact reviewed master, Full and Light model bytes and historical camera/review records remain unchanged. The additional integration receipts record the base and row audit.


The final dev integration (`44d130bae3af26ffe9f0fb2fbbb649b10841fb67`) preserves all current dev records and the exact reviewed Glessner master, Full and Light assets. The affected derived chain was rebuilt to stability; separate integration receipts record every dev liberty and the unchanged historical camera/review records.
