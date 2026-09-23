---
id: T-1246
title: Expose real boot phases and yield long scene-building tasks
state: open
epic: RENDERING
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

Make the boot **measurable and responsive** before anything is done to its looks. The owner's ask: *"as it's loading we should inside be able to calculate know how long each section is take and should be taking and know how to roll the clock years back and update statuses smoothly while things are loading"*. Today the loader knows five milestones and nothing in between; the prairie phase blocks the main thread so no status could repaint even if one wanted to. This ticket gives the boot real phase events, measured expected durations, and yielding long tasks. It changes no copy and no styling — T-1247 does that on top of these events.

**Depends on:** nothing in this feature. **Runs in parallel with:** T-1292, T-1248, T-1277.

**What exists today** (`renderers/web/js/main.js`, dev 2026-09-17):
- `progress(pct, label)` at ~L777 paints `#gate-sub` and `#gate-bar`; `boot()` calls it at 8 ("Reading the scene…"), 30 ("Placing the buildings…"), 55 ("Laying the ground and the river…"), 68 ("Planting the prairie…") and 100 ("Ready", ~L2513). Between 68 and 100 sit flora, fauna, wharves, signage, people, HUD and controls, all unlabelled.
- `api.ready = true` (~L2514) is what `tools/smoke_renderer.mjs` and `tools/measure_boot_payload.mjs` wait on. It must keep meaning "the visitor can stand in the street".
- `mountGateCensus` (census.js) and `people.json` are started early and fail soft; neither is essential.
- `createFlora` (flora.js, 4,907 lines) and the tree/shrub planting are the long synchronous CPU phase on a phone; measure it rather than assume it.

**Build:**
1. A small boot controller (`renderers/web/js/boot-phases.js`, ~150 lines) exposed as `api.boot`: `phases[]` of `{ id, label, essential, startedAt, endedAt, units, unitsDone, error }`, plus `on('phasestart'|'phaseprogress'|'phaseend'|'ready'|'error', fn)`. Phase ids, in order: `scene`, `terrain`, `buildings`, `ground` (streets, wharves, enclosures, yards, signage), `flora`, `people` (optional), `census` (optional), `interaction` (HUD, controls, first frame). Add phases only where a real boundary exists; do not invent sub-phases to make a smoother bar.
2. Replace the five `progress()` calls with `boot.start(id)` / `boot.end(id)`; keep `progress()` as the presentation adapter so `#gate-sub`/`#gate-bar` still paint exactly as today (T-1247 swaps the presentation, not the events). `phaseprogress` carries `unitsDone/units` wherever a loop already counts (sidecar fetches in `loadScene`, buildings batched, flora tiles planted).
3. **Expected durations** — commit `renderers/web/js/boot-weights.js`: measured seconds per phase for `{ desktop, mobile } × { full, balanced, light }`, cold and warm, taken on the published mirror with `--published`, with the date and machine in a comment. Optional refinement: a bounded local history at `localStorage['c4d.boot.timings.v1']` keyed by the build stamp (`#gate-build`) and detail tier; clamp any reading outside 0.25×–4× of the committed default; a storage failure or a stale build key falls back to the table. The table is the contract T-1247 paces the year ticker against.
4. **Yield the long task.** Time-slice the flora/tree planting loop (and any other phase that measures > 250 ms of continuous main-thread time at 390×780 on the light tier) at safe boundaries — per tile or per species batch — using `requestAnimationFrame`/`setTimeout(0)` chunks, so the status line can repaint between chunks. Geometry must be byte-identical to the unsliced path: assert instance counts, the `roll` counts and the drawn-placement census against the unchanged tree before and after.
5. Essential vs optional: `ready` fires only when every `essential` phase ended without error and one frame has rendered; an optional phase's failure is recorded on the phase and in `problems[]` and never blocks `ready`. An essential failure emits `error` and never `ready` (today's `boot().catch` path).
6. Harness: `api.boot.timings()` returns the phase table for the smoke and for `tools/measure_boot_phases.mjs` (new, ~80 lines: boots the published mirror at both gate viewports, prints per-phase seconds and the longest main-thread task, `--json`).

**Acceptance:**
1. `api.boot.phases` shows every phase above with monotone timestamps; `ready` fires after the last essential phase and the first rendered frame; `api.ready` semantics unchanged (measure_boot_payload still completes).
2. During the flora phase, a status repaint scheduled every 100 ms lands at least every 250 ms at 390×780 light on the published mirror (measured by `measure_boot_phases.mjs`, recorded in the PR); before the slice it did not.
3. Scene counts (`api.roll`, tree/shrub instance counts, `drawn_placement_census`) match the unsliced tree exactly.
4. Forced failure of `people.json` or the census still reaches `ready`; a forced failure of `terrain` reaches `error` and never `ready` (both demonstrated with a harness fetch stub, in a focused check `tools/test_boot_phases.mjs` that runs in `check.sh`).
5. `boot-weights.js` carries measured numbers for all six device × tier cells, cold and warm, with their date; the local-history clamp and storage-failure fallback are unit-tested in the same focused check.
6. A backgrounded tab resumes from the current phase without replaying a backlog of events.

**Harness and gates:** `./tools/check.sh`; `node tools/smoke_budget.mjs --for-diff` names the smoke parts (main.js touches part 1 and part 6 at least); run them `--published` at both viewports; `node tools/measure_boot_payload.mjs --check` stays under 12 MB. Keep the ids `#gate`, `#gate-btn`, `#gate-sub`, `#gate-bar` — the smoke's `enterTown()` and part 1 read them.

**Out of scope:** new copy, the year ticker, the flip cards, the welcome (T-1247, T-1275, T-1278). Do not put Three.js objects in a worker for this.

**Visible-progress note:** the visitor sees statuses that repaint during the prairie phase instead of a frozen line — say so in the changelog entry. Contract: [architecture §A](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#a-boot-phases-and-readiness) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`; meet this acceptance before closing; a genuine leftover becomes one successor placed `--after` this ticket, never a tail line.
