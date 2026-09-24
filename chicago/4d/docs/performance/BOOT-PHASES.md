# Boot phases — T-1246

`window.__chicago4d.boot` owns the real boot work. Its `phases` array is ordered
scene, terrain, buildings, ground, flora, people, census, interaction. People and
census are optional and may overlap essential work. Timestamps use
`performance.now()` in milliseconds; `timings()` adds seconds and expected seconds.
`on(type, listener)` returns an unsubscribe function. Events are synchronous
snapshots, never a queue replayed after a background tab resumes.

A phase has `id`, `label`, `essential`, `startedAt`, `endedAt`, `units`,
`unitsDone`, and `error`. Unknown totals are null. Sidecar loads, building records,
and planting rows report completed work; phase end means the entire operation
finished, including batch assembly. The existing gate DOM, copy and styles stay
in place. Progress uses measured weights and completed units, never elapsed time
pretending work is complete. Optional failures reach both the phase and
`api.problems`; essential failure leaves `api.ready` false. Readiness also waits
for the first actual render, after preparing shader programs asynchronously.

The planting algorithm is shared by two consumers: startup drains its generator
with timed paint yields, while movement uses the same generator synchronously.
Yields occur at row/batch boundaries without changing seeds, arithmetic or order.
Ground sampling, coverage audit, building batches and tree planting also yield.
Visible tabs use a frame followed by a timer; hidden tabs use a timer and retain
no frame backlog. A 50 ms fallback handles a tab hidden while a frame is pending.

## Reproduce

From `chicago/4d`, with Playwright and Chromium installed:

```sh
./tools/publish.sh
node tools/measure_boot_phases.mjs --published --json --check > boot.json
node tools/test_boot_phases.mjs --browser
node tools/measure_boot_payload.mjs --check
```

`--quick` measures mobile/light cold and warm only. `--root /absolute/mirror`
measures a frozen published mirror of an unchanged commit, including versions
with only the old five progress milestones. Save that JSON, then run the new
mirror with `--compare /absolute/baseline.json`; this asserts every flora/tree
geometry attribute, index and active instance matrix byte digest, full flora/tree
stats, `api.roll`, and the drawn-placement census. The report also contains all
phase timings, events, 100 ms timer-to-frame heartbeats and longest main-thread
tasks. `--check` refuses a mobile/light flora paint gap above 250 ms.

`tools/boot_phase_measurements.json` is the compact September 20 receipt, against
unchanged commit c8c11eabe9fcbe0ddb610161f0d3f5106b3fbefc. Its per-cell digests
represent identical before/after objects; `boot-weights.js` contains all 12 measured
phase-duration sets and identifies machine/browser. Cold is a new browser
context; warm repeats navigation in that context. These are viewport/input
emulations on the recorded Mac, not measurements of a physical phone. No CPU
throttling or network shaping was used. Values are planning estimates, not a
promise of load time on another device.

Mobile/light's flora repaint gap was 974.5 ms cold before slicing; it is 123.8 ms
cold and 116.5 ms warm afterward. All twelve comparisons are byte-identical.
The full long-task reading includes software WebGL/compositor work at first
presentation; it is reported separately and is not the flora heartbeat metric.
No claim is made that all browser rendering tasks now take under 250 ms.

History is optional: `c4d.boot.timings.v1` stores one build stamp and at most six
device/tier cells. Each reading is clamped to 0.25–4 times the committed default,
including repeated writes; unavailable/corrupt storage and stale build keys fall
back to defaults. `test_boot_phases.mjs` exercises readiness, mocked failed
fetches, history bounds/fallback and hidden-tab yields in `check.sh` without
requiring browser installation. Its `--browser` mode additionally fails real
people/census/terrain requests in the published app and freezes/resumes its tab.

## Regression receipt

Final focused published smoke passed desktop stages 1/6/13 (196 checks) and mobile
stages 1/6 (91 checks), with zero page errors. The full 1–13 runs also completed:
mobile 538 passed / 4 failed; desktop 533 passed / 6 failed. The standing dev ledger
already records the household, placeholder/grade, people-count/trade-pill and
desktop light-tier draw-call failures. The full desktop run also hit a pointer-lock
error; isolated baseline 1/6 and final 1/6/13 both passed without it. Those broader
failures are not erased or treated as a fully green suite. The per-commit Linux
gate is required before merging PR #1586.
