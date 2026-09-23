---
id: T-1257
title: Connect jaunt stops and travel to optional historical context
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

**Deeper history one tap away, and the road between stops made interesting.** The owner: *"Links into the project's existing deeper information cards so users who want more history can explore it without slowing down the basic jaunt"* and *"make the jaunt interesting with mentioning sites along the way or providing the user more historical context of the story of when you left and when you are getting to the next scene stop."* Two mechanisms: typed card links on every stop, and route-aware leg notes that name what the visitor actually passes.

**Depends on:** T-1279, T-1280, T-1276 (source cards to link to). T-1258 depends on this.

**What exists today:** `popup.show(record)` (structure card, with dossier and citations), `people.open(id)`, Evidence topics incl. Sources (T-1276) and their `[DOC]/[INF]/[CONJ]` chips; `router.plan()` returns the polyline the ride follows; the registry has every structure's position (`positionOf`) and name; `hud.travelBanner` paints the ride banner; the panel and reducer have a `detail` phase.

**Build:**
1. Stop links: `links[]` of `{ kind: structure|person|business|source|topic, id, label }` render as chips under the stop text; tapping pushes `detail` (ride paused if travelling, panel collapsed to the sticky control), opens the existing card, and on close restores the exact stop, choices and scroll; reading changes no variable and earns no credit.
2. **Leg notes, route-aware.** At leg start compute the structures whose stand-off lies within 25 m of the planned polyline (excluding origin and destination), ordered by arc length; the panel's banner region shows at most two short lines during the ride — an authored `legs[].note` from the content if present, else a generated "Passing <name> on your left/right" from the polyline bearing — plus an optional authored one-line "story of the road" (`legs[].story`, evidence-marked like any claim). Non-blocking: a fly/instant hop never waits for a note; notes are dismissible and readable later from a small "on the way" chip at the next stop.
3. Provenance in the panel: every historical sentence a stop or leg shows carries its claim chip; invented connective text (gossip, bridging dialogue) is styled as narrative and never attributed as a quotation of a named person (the compiler already refuses the field combination — add the render-side assertion).
4. Unavailable card (missing dossier or person) → an honest "no card yet" state; a failed source fetch never ends the jaunt.
5. Layout: detail card, drawer, panel and sticky control never overlap at 390×780 or 1280×800; opening the drawer during a jaunt collapses the panel to the control row.

**Acceptance:**
1. On `new-in-chicago`, tap a structure link, a person link and a source link at each viewport; each returns to the same stop with the same scroll and choice state (stills + `api.jaunts.state`).
2. `tools/test_leg_notes.mjs`: for Green Tree → Sauganash the pass-by list names Wolf Point Tavern and the bridge, in route order, with correct side; a straight fly leg yields notes without delaying arrival (simulated).
3. Exiting during a pending card fetch leaves no orphan overlay or listener; a 404 dossier shows the "no card yet" state.
4. Reading for two minutes on a card changes no variable and no ETA except the remaining travel time.
5. Screenshots prove no overlap of popup, drawer, panel and control with the touch stick at 390×780.

**Harness and gates:** `./tools/check.sh` (+ test); `smoke_budget.mjs --for-diff` → chrome/popup parts `--published`, both viewports.

**Out of scope:** authoring the notes for the 25 jaunts (content tickets), the daybook (T-1258).

Changelog: one visible entry. Contract: [architecture "Travel and the five-minute path" (optional context)](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#travel-and-the-five-minute-path) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
