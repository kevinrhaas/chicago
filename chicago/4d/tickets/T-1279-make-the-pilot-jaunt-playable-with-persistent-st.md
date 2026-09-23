---
id: T-1279
title: Make the pilot jaunt playable with persistent stop navigation
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

The **jaunt engine and the persistent navigation**: a session reducer, the stop panel, and the four controls the owner asked for — *"During an active jaunt, provide a persistent, simple navigation control with Previous Stop, Next Stop, End Jaunt, access back to the Jaunts Menu. Ending a jaunt should immediately return the user to the Jaunts Menu."* Demonstrated by playing the T-1253 pilot (`new-in-chicago`) end to end at both viewports. No jaunt-specific code.

**Depends on:** T-1253 (content + catalog), T-1277 (destination resolver), T-1278 (the welcome hosts the menu). T-1280, T-1256, T-1257 depend on this.

**What exists today:** `travel.js` `createTravel` → `go(target) → bool`, `stop(reason)`, `state { phase, dest, dist_m, … }`; arrival calls `framing(id)` in main.js; `hud.say`, `hud.travelBanner(state)`, `hud.setTitle`; `popup.show`/`people.open` for cards; the welcome (`api.welcome`) and picker; `destinations.resolve` (T-1277). Nothing owns a session.

**Build:**
1. `renderers/web/js/jaunts.js` (~350 lines): a pure reducer `reduce(state, event)` over `{ jaunt, session, leg, stopIndex, visited[], vars, inventory, events[], phase: opening|travelling|atStop|detail|outcome|menu }` and a controller that binds it to travel and the panel. Every travel callback carries `{ session, leg }` tokens and is dropped if either is stale. Events are appended, never mutated; `Previous` moves the cursor over `visited[]` without re-applying effects; going forward over a visited stop re-applies nothing.
2. `renderers/web/js/jaunt-panel.js` (~250 lines) + `css/jaunt.css`: the stop panel (title, 25–60-word text, choices as buttons, card links) and the **sticky two-row control** — row 1: Previous · Next; row 2: End Jaunt · Jaunts Menu — always visible at 390×780 (above the touch stick, below the HUD top), ≥ 44 px targets, keyboard-reachable. Previous is disabled at stop 1; Next at the last stop completes and returns to the menu with a compact outcome card inside the menu.
3. Semantics: **End** cancels any ride (`travel.stop('jaunt')`), clears state, returns to the menu instantly — no confirmation, no ending card. **Menu** pauses (ride cancelled, position kept) and offers Resume/Restart; selecting another jaunt replaces the session; **Explore Myself** from the menu clears any paused jaunt. Starting places the visitor at stop 1's stand-off immediately (no unpriced ride from wherever they were); Next resolves the next stop through `destinations.resolve` and rides with the current mode (T-1280 makes the mode changeable; here the ride uses the session's `default_mode`).
4. Wire the welcome's Jaunts region (from T-1253) so a card's Start button launches the session; completion/End returns to that region with focus on the card. `api.jaunts = { start(id), state, next(), prev(), end(), menu(), catalog }` for the harness.
5. Free exploration, Go to, framing and the popup are untouched when no session exists (assert via the existing smoke parts).

**Acceptance:**
1. Play `new-in-chicago` from the welcome to the outcome at 390×780 and 1280×800 on the published mirror: all five stops, Previous/Next, End mid-ride returns to the menu in < 200 ms with no ride continuing, Menu → Resume continues at the same stop (evidence: stills + `api.jaunts.state` dumps).
2. `tools/test_jaunts_reducer.mjs` (node): Previous then Next re-applies no effect; late callback with a stale `leg` token is ignored; replacing a session mid-ride leaves no timers or listeners (count them); rapid Next×5 produces exactly one arrival per leg.
3. A second fixture jaunt (from T-1253's fixtures) plays through the same code path; `grep` proves no branch keyed to a jaunt id.
4. Starting a jaunt from the Sauganash stand and from the far south anchor both begin at stop 1 with the same framing.
5. No pointer lock is taken by any panel button; the panel never overlaps the popup or the drawer (screenshots at both viewports, popup open).

**Harness and gates:** `./tools/check.sh` (+ reducer test); `node tools/smoke_budget.mjs --for-diff` → chrome parts `--published`, both viewports; boot payload `--check` (jaunts.js/jaunt-panel.js load lazily on first Jaunts open, not at boot).

**Out of scope:** mode switching and ETAs (T-1280), mechanics (T-1256), between-stop context (T-1257), daybook (T-1258), menu filters (T-1259).

Changelog: one visible entry. Contract: [architecture "Jaunt content and runtime contract"](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#jaunt-content-and-runtime-contract) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
