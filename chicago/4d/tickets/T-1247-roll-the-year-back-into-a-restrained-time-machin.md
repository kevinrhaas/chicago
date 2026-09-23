---
id: T-1247
title: Roll the year back into a restrained time-machine arrival
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

The loading screen becomes the **arrival**: a welcome that says you are entering a digital reconstruction of 1835, a year that rolls back from 2026 and lands on exactly 1835 at the moment the town is ready, and statuses that read like the reconstruction is being assembled as you travel. The owner's brief, verbatim where it matters: *"a tick back rolling back of the years from 2026 … the year ticker … should roll back at a pace so that when the screen is fully loaded it lands exactly at 1835 … it might slow down or speed up over a section towards 1835 so it goes smoothly to the user in a Time Machine fashion. The UI should pick up a modern gently steampunk retro 60s Time Machine feel style, don't get cutesy or go overboard there."* This ticket is the presentation over T-1246's events; T-1275 fills the status library.

**Depends on:** T-1246. T-1275 and T-1278 depend on this.

**What exists today:** `renderers/web/index.html` L53–75 (`#gate` dialog: eyebrow, `#gate-title` "Chicago, summer 1835", `#gate-sub`, `#gate-bar`, `#gate-btn` "Tap to walk", key hints, `#gate-build`); `css/walk.css` L66–112 (`.gate*`) and the tokens at `:root` (`--ink`, `--ink-dim`, `--panel`, `--accent #d8a24a`, `--doc/--inf/--con`, light theme at L28+). `progress()` in main.js is now the adapter over `api.boot` (T-1246). Reduced motion is not honoured anywhere on the gate today.

**Build:**
1. `renderers/web/js/arrival.js` (~350 lines): subscribes to `api.boot` and drives three regions inside `#gate`: the **year** (`#arrival-year`, tabular digits, split-flap: each digit a two-half card that flips down; a continuous internal year `y ∈ [1835, currentYear]` with integer display), the **phase line** (`#gate-sub`, the real phase label from T-1246, always legible), and a **card slot** (`#arrival-card`) that T-1275 feeds — ship it with the phase label and a neutral "Drawing on previously researched sources" line until then. Keep `#gate-bar` as a thin phase-progress rule under the year.
2. **Pacing model.** Map boot progress `p ∈ [0,1]` to the year: `p` = Σ(finished phase weights) + current phase's fraction (units where counted, else elapsed/expected clamped to 0.92 of the phase's weight so an overrunning phase eases toward its bound and never lies). Weights come from `boot-weights.js` (T-1246) for the device/tier, refined by local history. Year = `currentYear − (currentYear − 1836) · easeInOut(p)`; hold at ≥ 1836 until `ready`; on `ready`, settle to 1835 within ≤ 300 ms (0 ms under `prefers-reduced-motion` or when the boot took < 1.5 s) and switch the phase line to **"You have arrived in Chicago, summer 1835."** Never roll forward, never overshoot, never show 1835 before `ready`.
3. **Style — restrained.** A dark instrument panel: `--panel-solid` ground, warm ivory `--ink` type, a new `--brass` token (muted, ~`#b8925a`) for the year card edges, hairline rules and the flip hinge; tabular numerals; one soft inner shadow on the flap. No gears, no rivets, no sound, no theatrical minimum duration. Light theme handled. Mobile: the year card ≤ 60 % of the 390 px width, the card slot two lines max, `#gate-btn` and hints below the fold are fine.
4. Error: `boot` `error` stops the ticker where it is, the phase line says what failed and offers **Retry** (reload) — never "arrived". Optional-phase failures do not change the arrival copy.
5. Accessibility: `#arrival-year` is `aria-hidden` (announcing every tick is noise); `#gate-sub` is `aria-live="polite"` and announces phase changes and arrival only; the dialog keeps `role="dialog"` and its labelling.
6. T-1278 replaces the button and what follows the arrival; this ticket keeps `#gate-btn` ("Tap to enter" wording is fine to set here) and the hints exactly where they are so the smoke's `enterTown()` still works.

**Acceptance:**
1. On a throttled cold boot (Chromium CPU 4×, network "Fast 3G", 390×780 light, published mirror) the year descends monotonically, pauses/eases through the long flora phase, and reads 1835 only after `api.ready`; recorded as a short screen capture or 6 stills in the PR.
2. On a sub-1.5-second warm boot the ticker settles immediately (no animation stall); with `prefers-reduced-motion` no flap animates and the year steps in ≤ 5 updates.
3. Forced essential failure (stub `terrain`) shows the stopped year, the failure text and Retry; the phrase "arrived" is absent. Forced optional failure (stub `people.json`) still arrives.
4. Both viewports, both themes, 320 px width, a 70-character phase label and a 120-character card line: nothing clips or overlaps (screenshots in the PR).
5. `tools/test_arrival.mjs` (node, no browser): the pacing function is pure and tested — monotone, bounded, holds ≥ 1836 before ready, lands on 1835 at ready, reduced-motion path is instant.
6. Screen reader: `#gate-sub` changes are the only live announcements; the year is not announced (assert `aria-hidden`).

**Harness and gates:** `./tools/check.sh` (renderer modules parse; add `test_arrival.mjs`); `node tools/smoke_budget.mjs --for-diff` → run the named parts `--published` at both viewports; boot payload `--check` (arrival.js is boot-critical — keep it under 12 KB minified-equivalent; no font download).

**Out of scope:** the status library (T-1275), the welcome and its buttons (T-1278), the City topic (T-1292).

Changelog: one visible entry. Contract: [architecture §A/§B and "Arrival states"](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#arrival-states-and-honest-readiness) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
