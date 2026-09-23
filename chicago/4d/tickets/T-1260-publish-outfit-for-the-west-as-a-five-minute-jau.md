---
id: T-1260
title: Publish Outfit for the West as a five-minute jaunt
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

Author the complete priority jaunt **Outfit for the West** (`outfit-for-the-west`) — one of the six the owner named first — from [brief 01](../docs/JAUNTS-INITIAL-LIBRARY.md#01-outfit-for-the-west). Content only: one JSON file, its evidence, its liberties, the regenerated catalog. The engine (5G) is finished; if a story needs an engine change, that is a finding for the engine's ticket, not a change in this PR.

**Premise:** Leave town with a practical kit, sound equipment and enough money for the road.
**Category:** Migration · **Recommended mode:** Wagon · **Keepsake:** Ready for the Road (Provisions) · **Target:** 4–6 min primary path.

**Depends on:** T-1259 (menu), T-1256 (mechanics), T-1257 (links and leg notes), T-1258 (daybook). Runs in parallel with the other 5H tickets — each owns only its own file.

**Stops, in story order** (all verified to exist in `data/sidecars/1835/index.json` on 2026-09-17; positions are inferred or reconstructed, never attested — the stop text must not claim a front door the record does not place):
1. [`green_tree_tavern`](../data/structures/green_tree_tavern.json) — Green Tree Tavern — set the supply list over the table
2. [`goss_cobb_saddlery`](../data/structures/goss_cobb_saddlery.json) — S. B. Cobb's saddlery — pack or harness
3. [`peck_store`](../data/structures/peck_store.json) — P. F. W. Peck's store — essential tools
4. [`h_jones_store`](../data/structures/h_jones_store.json) — Jones's grocery and provision store — provisions
5. [`pierce_blacksmith_shop`](../data/structures/pierce_blacksmith_shop.json) — Asahel Pierce's blacksmith shop — repair before departure, or not

**Mechanics for this jaunt:** money (a modest purse in cents) and `readiness`; two endings — light versus prepared — chosen by readiness, not a survival battle.

**Evidence and route cautions:** Prices, quantities and the errand are reconstructed; cite which trade actually sold each chosen good (saddlery ≠ ironwork ≠ provisions). Wagon is the recommended mode because the stops span Wolf Point to the South Water front — measure the long leg.

**Authoring checklist (every stop):** read `data/structures/<id>.json`, its sidecar and dossier; state the stop's stand-off kind (exterior stand; no interior is implied); write 25–60 words of primary text; mark each sentence's tier — a DOC claim has a source id **and** locator, an INF claim states its reasoning, invented connective text (the errand, prices, small talk) is `reconstructed` with a LIBERTIES line; no quotation is put in a named person's mouth; nothing after 1 July 1835 is narrated as present; no human figure, ceremony or Indigenous dialogue is depicted. Card `links[]` point at the existing structure/person/source cards, never at a copy.

**Acceptance:**
1. `data/jaunts/outfit-for-the-west.json` compiles `available` in `check.sh` (`python3 tools/compile_jaunts.py`); every destination resolves; every claim's source and locator resolve; the compiler's path walk reaches every ending.
2. Every authored choice and ending is exercised by `tools/play_jaunt.mjs outfit-for-the-west --all-paths` (T-1256's walker); no dead end, no double keepsake.
3. Measured on the published mirror: primary path at **Wagon** ≈ 4–6 min (opening + stops + rides, deep cards closed), quoted in the PR beside the card's estimate; Fly and Instantly measured too; a run outside 3–6 min is re-cut (fewer words, a nearer stop) or justified in one sentence.
4. Stills at 390×780 and 1280×800: menu card → opening → one mid-leg mode switch → one detail card and back → ending → menu. Previous/Next/End/Menu all used once.
5. The keepsake **Ready for the Road** lands in the daybook once, under **Provisions**; replay does not add a second.
6. The diff contains `data/jaunts/outfit-for-the-west.json`, its LIBERTIES lines, the regenerated catalog and (if needed) `docs/JAUNTS-INITIAL-LIBRARY.md` route notes — and **no engine, compiler or CSS change**. A stop that cannot be supported is substituted with a typed supported destination and the reason recorded in the brief; it is never invented.

**Harness and gates:** `./tools/check.sh`; `node tools/smoke_budget.mjs --for-diff` (content-only diffs usually name no renderer part — say so); `node tools/play_jaunt.mjs outfit-for-the-west --all-paths`; `./tools/preflight.sh`.

Changelog: one visible entry naming the jaunt. Contract: [authoring guide](../docs/JAUNTS-AUTHORING.md) · [brief 01](../docs/JAUNTS-INITIAL-LIBRARY.md#01-outfit-for-the-west) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
