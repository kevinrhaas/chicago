---
id: T-1280
title: Offer live jaunt travel modes and honest quick-play estimates
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

**Travel modes and honest durations.** The owner: *"you would have a recommended mode of travel that you can change for each jaunt so it's faster or you can change the mode mid jaunt like if taking a horse seems to take forever it would be boring so someone might want to make it fly instead … if I change a logical horse ride … the default may be to horse and the whole jaunt takes 5 min but if I fly I can do it in 3 min."* The estimate comes from the same router and pace settings that move the visitor, so it cannot lie.

**Depends on:** T-1279. T-1257 and T-1259 depend on this.

**What exists today:** `travel.js` `PACES` (`instantly, walk, wagon, horse, fly`), `paceSpeed(pace, settings)` (slider-set m/s with defaults 1.45 / 3.6 / 6.5), `PACES.fly.cruise(d)`, `go()` plans through `router.plan(from, to) → { points, length_m }` and falls back to instant when unroutable; `setMode(id)` only changes the label for the *next* `go()` — a live ride keeps its mode; `stop('input')` on visitor movement. HUD has `#s-travel` (mode) and `#s-pace` (own pace) segmented controls with stored settings.

**Build:**
1. `estimateLeg({ from, to, mode, settings, router })` in a new `renderers/web/js/travel-estimate.js` (~120 lines, pure): ground = `route.length_m / paceSpeed(mode)`; fly = ascent + cruise at the flight speed the controller uses + descent, with `cruise(d)`; instantly = 0 + the arrival framing settle; unroutable → straight-line × 1.3 flagged `approx: true`; no route and no positions → `null` (the UI says "no estimate", never a number). `estimateJaunt(jaunt, mode)` = opening read + Σ stop reads (from the content's timing inputs) + Σ legs. Rounded to the nearest half-minute for display, prefixed "about".
2. Mode selector on the jaunt card (menu) **and** in the sticky control (a fifth chip row or a compact popover): Walk · Wagon · Horse · Fly · Instantly. Selecting mid-leg: `travel.stop('replan')`, then `go()` again with the new mode from the current position to the same stop; session, choices and inventory untouched; the panel's remaining-time readout updates. The choice is per-session and never overwrites the visitor's stored `travelMode`/pace settings.
3. **Go straight to next stop** is always present during a leg (including a stalled or replanned ride) and uses the existing instant arrival; it earns nothing extra.
4. Manual movement during a leg pauses the ride (existing `stop('input')`) and the panel shows "Resume ride" without losing the stop; End/Menu cancel it.
5. Remaining-time readout during play: recomputed at leg start and on mode change from the current position; hidden when `null`.

**Acceptance:**
1. `tools/test_travel_estimate.mjs`: a near walk (Sauganash → Peck's), a cross-river horse leg (Green Tree → Sauganash over the bridge graph), fly and instantly — assert route length, not straight line, prices ground travel; fly ≠ horse; unroutable pair returns `approx`; missing positions return `null`.
2. On the published mirror, switching horse → fly mid-leg visibly changes motion (altitude rises, the banner verb changes) and the ETA drops; the arrival still frames the stop and stands on ground (`travel.simulate` in the harness, both viewports).
3. The card estimate for `new-in-chicago` differs by mode, and the measured primary path at the recommended mode lands within ±25 % of the estimate (numbers in the PR).
4. Stored settings before and after a jaunt are identical (assert `localStorage` snapshot).
5. Fly is labelled a viewing convenience in the selector's hint, never narrated as 1835 transport.

**Harness and gates:** `./tools/check.sh`; `smoke_budget.mjs --for-diff` → travel/chrome parts `--published`, both viewports.

**Out of scope:** between-stop narration (T-1257), menu sort/filter (T-1259).

Changelog: one visible entry. Contract: [architecture §H and "Travel and the five-minute path"](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#travel-and-the-five-minute-path) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
