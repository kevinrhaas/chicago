# T-3535 — Balanced shadow budget

The published desktop stage 5 run on 9b103acae failed at the 1835 West prairie stand: 2,658,284 triangles against the unchanged 2,625,000 ceiling. Full and Light already enabled the conservative shadow-caster filter; Balanced omitted it.

At the same stand, enabling that existing filter submits 2,591,747 triangles and 5,940 draw calls, saving 66,537 triangles and 501 calls. All 1,024,000 RGB pixels are identical. Removing shadows entirely changes 143,254 pixels, so the comparison can detect shadows. No geometry, tier reach, density, or ceiling changes.

`before.json` records the initial diagnosis and source hashes. `probe.mjs` reproduces the held-frame comparison and writes `browser-validation.json`, including the source and published main-module hashes. Run from `chicago/4d` after publishing:

```sh
NODE_PATH="$(npm root -g)" PW_EXECUTABLE=/path/to/chromium node docs/RESEARCH/balanced-shadow-budget-3535/probe.mjs
```

The diagnostic measures submitted work and image equality. The normal-loop published stage 5 smoke remains the release gate across all six stands and both viewports. CI failure receipt: https://github.com/kevinrhaas/chicago/actions/runs/42770762952.

A comparison on dev commit `1226c29f7` reproduces the failure: 2,657,384 triangles against 2,625,000 (29 passes, one failure), confirming the missing Balanced filter predates the routines. Baseline receipt: https://github.com/kevinrhaas/chicago/actions/runs/42775425682.

## Full Ghost allowance

The complete original desktop stage 13 run had 157 passes and one failure: Full X-RAY submitted 3,737,315 triangles and 8,152 calls against allowances of 3,675,000 and 8,900. Receipt: https://github.com/kevinrhaas/chicago/actions/runs/42770801483 (feature source `9b103acae`). This is a current-view measurement, not a claim that every possible camera is bounded by it.

Following AGENTS.md's explicit measured higher-tier re-budget policy, the Full active Ghost allowance becomes **3,760,000**: the measured 3,737,315 plus T-2981's existing 18,059 margin, rounded upward to 5,000. This changes no geometry or rendered work. Draw calls remain 8,900; ordinary Full, Balanced and Light ceilings remain unchanged. Independent policy/transition tests and the browser's independent pin use the new measured value; every draw/triangle assertion and restoration check remains enabled. Full is already an explicit visitor detail choice; no new setting is needed.

The final-source pixel probe initially timed out at its unchanged 240-second load limit while the local gate was also running, before recording a measurement. The quiet rerun on commit `2a426e4f9` passed with the same counts and zero changed pixels; `browser-validation.json` records the final source hashes and result.

`ghost-probe.mjs` additionally exercises the published X-RAY and Ghost40% controls, Normal restoration, and Balanced/Light transitions on 1280×800 and 390×780. Both viewports pass with zero page errors; `ghost-validation.json` retains camera poses, counts, policy values, and source hashes. This is transition coverage at its own arrival pose, not a replacement for the full desktop stage 13 rerun at the original failure pose.

## Completed release validation

All affected published reruns pass on `2a426e4f91c1d47ec8573880b8279c08c6f660a1`:

- [Phone stage 5](https://github.com/kevinrhaas/chicago/actions/runs/42787676968): 30 passed, zero failed.
- [Desktop stage 5](https://github.com/kevinrhaas/chicago/actions/runs/42787667033): 30 passed, zero failed.
- [Complete desktop stage 13](https://github.com/kevinrhaas/chicago/actions/runs/42787656979): 158 passed, zero failed, including the original Full X-RAY assertion.

The other sixteen groups of the original complete, two-viewport 15-stage suite passed on the initial feature commit `9b103acae`. Both original failing groups and the successful replacements are retained in the standing smoke record. All thirteen regular CI checks pass on the final implementation, alongside all four local gate parts and preflight. The qualified runtime hash is `sha256:b1b243d50655c6b1`; the final receipt changes are documentation only.
