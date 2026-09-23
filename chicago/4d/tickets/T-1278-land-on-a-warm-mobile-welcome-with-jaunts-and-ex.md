---
id: T-1278
title: Land on a warm mobile welcome with Jaunts and Explore Myself
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

The landing surface. When the arrival settles on 1835 the visitor is **on the welcome**: a warm, directed page with two ways in — **Jaunts** and **I'll Explore Myself — Starting At…** — and no dashboard. The owner: *"You should land on the explore on your own / jaunts page when you are completely loaded and landed in Aug 1835 … the opening screen should give you a warmer directed welcome with options for jaunts … it should not be tap to walk, more like tap to enter … That new screen must all fit and work on mobile."* Wording stays the approved "Chicago, summer 1835".

**Depends on:** T-1247 (arrival), T-1292 (census gone from the loader), T-1277 (shared picker). T-1253/T-1279 (jaunts) and T-1259 (the finished menu) depend on this.

**What exists today:** `#gate` is the loader and the entry gesture in one (`index.html` L53–75); `openWorld()` in main.js (~L2082) hides `#gate`, shows the HUD, opens first-run control help, unlocks audio and — on desktop — takes pointer lock unless help is open; `canvas` click locks the pointer when `!gateOpen` (~L1810); `hud.showControlHelp({ auto })` is stored under `CONTROL_HELP_KEY`; the smoke's `enterTown()` clicks `#gate-btn` and dismisses `#control-help-gotit`; spawn is the Sauganash stand (`scenes/1835.json` `spawn`).

**Build:**
1. On `ready`, `arrival.js` transitions `#gate` from the arrival state to the **welcome** state in place (same dialog, one fade ≤ 300 ms, none under reduced motion): headline "Welcome to Chicago, summer 1835.", one sentence: "You are entering a digital reconstruction of the town as it stood on 1 July 1835, built from the sources listed under Evidence." Then three actions, in this order and prominence: **Jaunts** (primary; opens the Jaunts menu region — until T-1253 lands it shows a labelled "Jaunts are being written — the first arrive soon" card and the Explore option), **I'll Explore Myself — Starting At…** (opens the shared picker from T-1277 inline: search + kind pills + list; choosing a row spawns there and enters the world), and a tertiary **Enter Chicago** (walk from the Sauganash, today's spawn) that keeps the id `#gate-btn` so `enterTown()` and the harness keep working. On touch the primary buttons read "Tap to enter…" phrasing where a gesture is needed. "Tap to walk" disappears from every file (grep in the PR).
2. **No pointer lock on the menu.** `openWorld()` splits into `enterWorld({ spawn, jaunt })` (hides the dialog, shows the HUD, audio unlock on the gesture) and movement capture, which happens only after the world is entered and the visitor clicks the canvas or presses a movement key. Typing in the picker never switches backends (the existing `isTyping` guard) and never locks the pointer.
3. A **Start** route back: HUD menu gains "Start / Jaunts" (id `btn-start`) that reopens the welcome with the world paused behind it; Escape from the welcome returns to the world when one is entered. The welcome never shows a count, percentage or bar.
4. First-run control help is deferred until the first world entry, and never covers the welcome.
5. Mobile: everything fits 390×780 with the on-screen keyboard open (picker list scrolls inside the dialog, buttons ≥ 44 px, safe-area padding); landscape 780×390 and 320 px width checked.
6. Harness: `api.welcome = { state: 'arrival'|'welcome'|'world', enter(kind, id) }`; the smoke's `enterTown()` is updated in the same PR to prefer `api.welcome.enter('spawn')` and fall back to `#gate-btn`.

**Acceptance:**
1. Cold boot at both viewports settles into the welcome automatically; the DOM has no "Tap to walk", no census, no percentages; the three actions are visible without scrolling at 390×780.
2. Choosing a destination in the picker (a structure, an intersection, a person with an address) enters the world at that stand-off with arrival framing, no jaunt overlay, no reward, and `document.pointerLockElement === null` until the canvas is clicked.
3. "Enter Chicago" enters at the Sauganash spawn; `#gate-btn` still exists and the smoke's gate-entry helper passes on the published mirror at both viewports.
4. From the world, Start reopens the welcome with the scene paused and no pointer lock; Escape/close returns; the welcome and the control help never overlap (screenshots).
5. Reduced motion: no fade; screen reader: focus lands on the headline when the welcome appears and returns to the Start button on close.
6. Saved settings (theme, pace, travel mode) are untouched by any of this.

**Harness and gates:** `./tools/check.sh`; `node tools/smoke_budget.mjs --for-diff` → parts touching the gate and chrome (part 6 at least), `--published`, both viewports; `measure_boot_payload.mjs --check`; `preflight.sh`.

**Out of scope:** the jaunt catalog and menu cards (T-1253, T-1259); travel estimates (T-1280).

Changelog: one visible entry. Contract: [architecture "Mobile and input contract"](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#mobile-and-input-contract) and §F · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
