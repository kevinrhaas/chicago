---
id: T-1259
title: Finish the scalable Jaunts Menu and integrated start experience
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

**The finished Jaunts Menu** — quick to browse at 25 and at 50+, beside the shared Explore Myself option. The owner: *"The Jaunts Menu should show each jaunt's title, one-sentence premise, number of stops, approximate quick-play duration, category, changeable method of travel and that changes the duration … Also include a prominent non-jaunt option: I'll Explore Myself — Starting At…"* This is the last engine ticket; the content batches (5H/5I) then only add JSON.

**Depends on:** T-1279, T-1280, T-1258, T-1278. 5H and 5I depend on this.

**What exists today:** the welcome's Jaunts region listing catalog cards (T-1253/T-1279), the mode selector and `estimateJaunt` (T-1280), the daybook entry (T-1258), the shared picker (T-1277/T-1278), `catalog.json` with summary fields.

**Build:**
1. `renderers/web/js/jaunt-menu.js` (~300 lines) + `css/jaunt.css`: cards with **title · premise · N stops · category · about M min at <mode>** and a per-card mode select that re-estimates instantly; **Start**; unavailable cards show their compiler reason and no Start.
2. A **Featured** row (the six priority jaunts as they land, by a `featured` flag in the catalog), then **All jaunts** with a search box and category pills (categories from the catalog, not a hard-coded list), sorted by title; windowed rendering above 20 cards; the whole region scrolls inside the welcome dialog at 390×780 with the on-screen keyboard open.
3. **I'll Explore Myself — Starting At…** stays the second primary action above the list, opening the shared picker; **Daybook** and **Sources & City** are secondary links. Selecting Explore clears any paused jaunt (T-1279's rule).
4. Return semantics: End/complete returns to this menu with the previous scroll, filter and focused card; a paused jaunt shows a "Resume <title> · Restart" strip at the top; starting another cancels it cleanly.
5. Lazy: the menu code and `catalog.json` load on first open of Jaunts, not at boot; a 55-entry test manifest (`data/jaunts/_fixtures/catalog-55.json`, harness-only) exercises windowing with no UI code change.

**Acceptance:**
1. At 390×780 and 1280×800 on the published mirror: every card shows the six fields; changing a card's mode changes its minutes; Start plays; End returns to the same scroll position and focus (stills + `document.activeElement` dump).
2. The 55-entry manifest renders with < 60 DOM cards mounted at once, no clipped control, no extra boot download (`measure_boot_payload.mjs --check` unchanged).
3. Search "tavern" and the category pill "Taverns" narrow the list; clearing restores it; keyboard: Tab order menu → cards → picker, Enter starts, Escape closes to the world when one is entered.
4. The welcome contains no counts or percentages; Sources & City is one tap away.
5. A paused jaunt survives Menu → browse → Resume; Explore Myself clears it (asserted via `api.jaunts.state`).

**Harness and gates:** `./tools/check.sh`; `smoke_budget.mjs --for-diff` → gate/chrome parts `--published`, both viewports; boot payload `--check`.

**Out of scope:** content (5H/5I), acceptance timing of all 25 (T-1271).

Changelog: one visible entry. Contract: [architecture "Mobile and input contract"](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#mobile-and-input-contract) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
