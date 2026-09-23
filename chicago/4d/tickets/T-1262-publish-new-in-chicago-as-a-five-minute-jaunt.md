---
id: T-1262
title: Publish New in Chicago as a five-minute jaunt
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

Author the complete priority jaunt **New in Chicago** (`new-in-chicago`) — one of the six the owner named first — from [brief 03](../docs/JAUNTS-INITIAL-LIBRARY.md#03-new-in-chicago). Content only: one JSON file, its evidence, its liberties, the regenerated catalog. The engine (5G) is finished; if a story needs an engine change, that is a finding for the engine's ticket, not a change in this PR.

**Premise:** Find your bearings, a bed and a practical next step on your first day in town.
**Category:** Orientation · **Recommended mode:** Walk · **Keepsake:** Finding Your Feet (Wayfinding) · **Target:** 4–6 min primary path.

**Depends on:** T-1259 (menu), T-1256 (mechanics), T-1257 (links and leg notes), T-1258 (daybook). Runs in parallel with the other 5H tickets — each owns only its own file.

**Stops, in story order** (all verified to exist in `data/sidecars/1835/index.json` on 2026-09-17; positions are inferred or reconstructed, never attested — the stop text must not claim a front door the record does not place):
1. [`sauganash_hotel`](../data/structures/sauganash_hotel.json) — Sauganash Hotel — arrive
2. [`hogan_store`](../data/structures/hogan_store.json) — Hogan's store — the FORMER mail corner (the post office moved about July 1834)
3. [`peck_store`](../data/structures/peck_store.json) — Peck's store — note a supply shop
4. [`chicago_democrat_office`](../data/structures/chicago_democrat_office.json) — Chicago Democrat office — read one eligible notice
5. [`brown_boarding_house`](../data/structures/brown_boarding_house.json) — Rufus Brown's boarding house — choose a boarding arrangement

**Mechanics for this jaunt:** none required — one optional preference (cost or convenience) and a route-note keepsake.

**Evidence and route cautions:** This FINISHES the T-1253 pilot file in place — it does not create a second `new-in-chicago`. Hogan's is not the 1835 mail counter. Brown's boarding house position is reconstructed — say so on the stop.

**Authoring checklist (every stop):** read `data/structures/<id>.json`, its sidecar and dossier; state the stop's stand-off kind (exterior stand; no interior is implied); write 25–60 words of primary text; mark each sentence's tier — a DOC claim has a source id **and** locator, an INF claim states its reasoning, invented connective text (the errand, prices, small talk) is `reconstructed` with a LIBERTIES line; no quotation is put in a named person's mouth; nothing after 1 July 1835 is narrated as present; no human figure, ceremony or Indigenous dialogue is depicted. Card `links[]` point at the existing structure/person/source cards, never at a copy.

**Acceptance:**
1. `data/jaunts/new-in-chicago.json` compiles `available` in `check.sh` (`python3 tools/compile_jaunts.py`); every destination resolves; every claim's source and locator resolve; the compiler's path walk reaches every ending.
2. Every authored choice and ending is exercised by `tools/play_jaunt.mjs new-in-chicago --all-paths` (T-1256's walker); no dead end, no double keepsake.
3. Measured on the published mirror: primary path at **Walk** ≈ 4–6 min (opening + stops + rides, deep cards closed), quoted in the PR beside the card's estimate; Fly and Instantly measured too; a run outside 3–6 min is re-cut (fewer words, a nearer stop) or justified in one sentence.
4. Stills at 390×780 and 1280×800: menu card → opening → one mid-leg mode switch → one detail card and back → ending → menu. Previous/Next/End/Menu all used once.
5. The keepsake **Finding Your Feet** lands in the daybook once, under **Wayfinding**; replay does not add a second.
6. The diff contains `data/jaunts/new-in-chicago.json`, its LIBERTIES lines, the regenerated catalog and (if needed) `docs/JAUNTS-INITIAL-LIBRARY.md` route notes — and **no engine, compiler or CSS change**. A stop that cannot be supported is substituted with a typed supported destination and the reason recorded in the brief; it is never invented.

**Harness and gates:** `./tools/check.sh`; `node tools/smoke_budget.mjs --for-diff` (content-only diffs usually name no renderer part — say so); `node tools/play_jaunt.mjs new-in-chicago --all-paths`; `./tools/preflight.sh`.

Changelog: one visible entry naming the jaunt. Contract: [authoring guide](../docs/JAUNTS-AUTHORING.md) · [brief 03](../docs/JAUNTS-INITIAL-LIBRARY.md#03-new-in-chicago) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
