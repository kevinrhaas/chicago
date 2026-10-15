# Glessner courtyard ground — T-2224

This pass gives the service stair and curved terrace usable approaches, removes
lawn beneath hard surfaces and occupied masonry, and closes visible gravel edges.
The western path falls away from masonry. Gate and passage levels are retained.

## Evidence and scope

Target: exterior/courtyard, 1904-07-01. HABS IL-1015 sheet 2 locates the openings
and stairs; it does not draw the 1904 paving layout. The written history (printed
p2) records the entire courtyard being paved for parking in September 1946. Neither
that surface nor modern garden paving is copied. No early dated path photograph was
recovered. Paths, width, gravel finish and shallow grades are explicitly
reconstructed; their material choice is separate from the surveyed threshold basis.
The previous photograph-based drive bend is replaced with a direct connection
between measured gate and passage jambs. No new geometry derives from HABS05.

The separate court-side west stair remains a T-2228 chronology/geometry issue.
The path reserves access to its likely foot; it does not assert that stair finished.
The new ground is driven by `courtyard_ground.value.finish`, with actual building
footprints read from the same parameters as their generators. No buried drainage
network or guessed grates are added. L-glessner-court-ground-2224 records the choices.

## Before evidence

Five identical Full desktop/Light mobile cameras were captured and actually viewed.
The baseline is the byte-verified deployed T-2223 Full/Light assets. Four views in
each tier pass existing scene budgets. Terrace-foot already fails: Full 405 calls /
4,701,255 triangles (360 / 4,600,000 limit); Light 282 / 1,639,605 (330 / 1,270,000).
These failures remain assigned to T-2227. No budget or camera is moved to conceal them.
The screenshot results have no page errors or failed requests. SwiftShader is not
hardware FPS evidence.

## Validation

The emitted-ground test passes disjoint-layer ray checks, five access contacts,
three points across the actual lowest terrace tread, the outward west-wall fall,
and 1,500 actual blade samples clear of hard surfaces and masonry. The earlier
service-access contact/hinge test also passes. The new component has 327 triangles.
Canonical Full/web totals are 1,315,670; Light is 199,794, below its unchanged 200,000
house limit. K01 confirms zero coincident faces, retained metric UVs, scale and
origin. The canonical baseline retains the 1 mm quantized small-face census; the raw
emitted-ground test checks degenerate triangles separately.

All ten published browser views were actually inspected at their saved cameras.
Draw calls are unchanged. The same four views per tier pass; both terrace-foot
views remain over their original scene budgets. Both QA commands therefore exit 1
on the preserved budget assertion. This is component visual/contact acceptance,
not an all-view performance pass. No page errors or failed requests were reported.
The phone Images tab loaded all credited tiles and the new courtyard liberty is
visible after its generated index was refreshed. Confidence displays were reviewed
in both tiers. No hardware FPS claim is made from SwiftShader.

| Tier | View | Calls before/after | Triangles before → after | Scene budget |
|---|---|---:|---:|---|
| full | court-overview | 204 / 204 | 3,621,435 → 3,622,073 | PASS |
| full | carriage-route | 208 / 208 | 3,621,752 → 3,622,390 | PASS |
| full | porte-threshold | 242 / 242 | 3,886,130 → 3,886,768 | PASS |
| full | service-stair-foot | 210 / 210 | 3,612,500 → 3,613,138 | PASS |
| full | terrace-foot | 405 / 405 | 4,701,255 → 4,701,893 | FAIL (also fails baseline) |
| light | court-overview | 96 / 96 | 626,627 → 627,083 | PASS |
| light | carriage-route | 94 / 94 | 601,713 → 602,072 | PASS |
| light | porte-threshold | 111 / 111 | 728,988 → 729,410 | PASS |
| light | service-stair-foot | 95 / 95 | 601,479 → 601,845 | PASS |
| light | terrace-foot | 282 / 282 | 1,639,605 → 1,640,161 | FAIL (also fails baseline) |

The five registered historical pairs were re-rendered and actually viewed using
unchanged camera files. Their whole-house verdicts remain `differs`; the ground is
mostly concealed from those cameras, and the measured terrace section does not
establish a 1904 paving material/layout. Roof/cone silhouette, opening correspondence,
stone relief and other retained differences remain T-2228 work. No photographic
acceptance was promoted.

Full preflight and exact-head CI govern the dev merge; the ticket-linked PR carries
those results and deployment receipts. The two terrace scene failures are also
recorded on T-2227. `browser-comparison.json`, `scene-budget-failures.json`,
`refined-assets.json`, `historical-review.json` and `after-visual-review.json` retain
the underlying measurements and observations.
