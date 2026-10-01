# Glessner v4 — final published-model review

Reviewed 2026-09-30 UTC. Code checkpoint `823442ee1bdc67d3c41b5e3b6610625d1ddc349c`
has the exact tree `e76abc3b976f9815d74074db3fcac6684bdd0104` of the local final
model checkpoint `b5bd006b`. The test serves an unchanged copy of that checkpoint's
published mirror, including its compressed full/light GLBs. No asset override is used.

## Final selected-model browser checks

`browser-refined06.json` preserves thirty explicit-frame readings: five camera
stands (Prairie, 18th Street, courtyard, stable and aerial), three detail tiers,
and desktop 1280×800 plus touch-mobile 390×780. All thirty select v4 and the
correct asset for the tier, retain mapped surfaces and physical glass, stay
within their declared budgets, and report no unexpected page or HTTP errors.

| Viewport | Light max triangles | Balanced max triangles | Full max triangles | Max calls |
| --- | ---: | ---: | ---: | ---: |
| Desktop | 799,079 | 799,079 | 3,433,805 | 105 |
| Touch mobile | 788,405 | 788,405 | 3,423,131 | 105 |

The unchanged Light ceiling is 825,000 triangles; Balanced is 1,280,000.
The measured and documented selected-v4 Full allowance is 3,800,000; other
scenes retain their normal ceiling. All three tiers retain the 215-call cap.
These are explicit-frame budget readings under software rendering, not an FPS
claim about a phone or native GPU.

Both viewports also pass a deliberate failed-full-download fixture (the visible
Light model survives), repeated full/light swaps (same structure record,
confidence mode and weathering, no texture/geometry resource growth), and a
rapid full/balanced/light sequence (the latest requested tier wins). The injected
503 responses are recorded separately from unexpected errors.

## Visual assessment

The actual final GLB's neutral Prairie entrance and sky-lit courtyard closeups
are preserved under `../images/glessner-v4/refined-06-glazing/`, with their render
settings and asset fingerprints. The entry view has coherent stone coursing,
relief around the arch, distinct carved trim, recessed frames and glazing. The
courtyard view shows the bow, stair tower, dormer eaves, clay variation and open
passage. These images were inspected alongside the final published desktop and
mobile views. The browser's first-use help panel remains visible in those browser
captures; it does not change the frame-budget readings.

The clear dielectric material and enclosed recesses materially improve the
previous diffuse grey glazing. Repeated generic capitals, bounded carving,
exact weathering and window interiors remain declared reconstructions. This
is a selectable comparison build for the owner's visual review, not a claim
that a validator establishes photographic or historical accuracy. Default,
v2 and v3 stay available; v4 is not promoted to the default.

## Integration verification

The validator regression passes, including indexed alternate-only fields,
unlisted-record exclusion, removed fields and scenes without alternates.
The final architecture proof retains all 172 openings in full and Light and
matches protected position/confidence fingerprints. The exact three-GLB
recovery package's tree and blob hashes were verified during upload.

GitHub gate run [36664653871](https://github.com/kevinrhaas/chicago/actions/runs/36664653871)
passed all **712 steps**, none red, plus the PR changelog-entry check, on
`823442ee`. The full published mobile smoke passed **572 checks, zero failures**
in 29 m 31 s, including zero page errors. Its complete log is
`mobile-refined06.log` and its result is filed in `tools/dev-smoke-state.json`.
The full published desktop run passed **569 checks, zero failures** in
44 m 12 s, including zero page errors; `desktop-refined06.log` preserves the
complete run. Together these unfiltered viewport runs cover every smoke stage.
Both results carry the same smoke-relevant tree `sha256:da40ab7c053f7196`
and are filed in the standing record. No assertion, threshold or viewport was
skipped to obtain these results.

Local preflight has no verdict: the environment blocked a test's GitHub API
request. That interrupted invocation is not counted as a pass.
