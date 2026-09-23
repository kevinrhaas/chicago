---
id: T-1261
title: Publish Taverns of Chicago as a five-minute jaunt
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

Author the complete priority jaunt **Taverns of Chicago** (`taverns-of-chicago`) — one of the six the owner named first — from [brief 02](../docs/JAUNTS-INITIAL-LIBRARY.md#02-taverns-of-chicago). Content only: one JSON file, its evidence, its liberties, the regenerated catalog. The engine (5G) is finished; if a story needs an engine change, that is a finding for the engine's ticket, not a change in this PR.

**Premise:** Visit three taverns, collect local talk and decide where to finish the evening.
**Category:** Taverns · **Recommended mode:** Horse · **Keepsake:** A Sensible Evening (Neighbors) · **Target:** 4–6 min primary path.

**Depends on:** T-1259 (menu), T-1256 (mechanics), T-1257 (links and leg notes), T-1258 (daybook). Runs in parallel with the other 5H tickets — each owns only its own file.

**Stops, in story order** (all verified to exist in `data/sidecars/1835/index.json` on 2026-09-17; positions are inferred or reconstructed, never attested — the stop text must not claim a front door the record does not place):
1. [`sauganash_hotel`](../data/structures/sauganash_hotel.json) — Sauganash Hotel — choose the purse
2. [`wolf_point_tavern`](../data/structures/wolf_point_tavern.json) — Wolf Point Tavern — a piece of clearly fictional talk, bounded by the papers
3. [`green_tree_tavern`](../data/structures/green_tree_tavern.json) — Green Tree Tavern — compare welcome and lodging
4. [`western_hotel`](../data/structures/western_hotel.json) — Western Hotel — pick the house to finish at

**Mechanics for this jaunt:** money and optional `sobriety`; restrained endings vary by both; abstaining is equally playable and equally rewarded.

**Evidence and route cautions:** No reconstructed dialogue is quoted from a named historical person; each house's presence and tenure keep their own grades (Western Hotel and Wolf Point Tavern records differ in support). The evening premise changes no lighting.

**Authoring checklist (every stop):** read `data/structures/<id>.json`, its sidecar and dossier; state the stop's stand-off kind (exterior stand; no interior is implied); write 25–60 words of primary text; mark each sentence's tier — a DOC claim has a source id **and** locator, an INF claim states its reasoning, invented connective text (the errand, prices, small talk) is `reconstructed` with a LIBERTIES line; no quotation is put in a named person's mouth; nothing after 1 July 1835 is narrated as present; no human figure, ceremony or Indigenous dialogue is depicted. Card `links[]` point at the existing structure/person/source cards, never at a copy.

**Acceptance:**
1. `data/jaunts/taverns-of-chicago.json` compiles `available` in `check.sh` (`python3 tools/compile_jaunts.py`); every destination resolves; every claim's source and locator resolve; the compiler's path walk reaches every ending.
2. Every authored choice and ending is exercised by `tools/play_jaunt.mjs taverns-of-chicago --all-paths` (T-1256's walker); no dead end, no double keepsake.
3. Measured on the published mirror: primary path at **Horse** ≈ 4–6 min (opening + stops + rides, deep cards closed), quoted in the PR beside the card's estimate; Fly and Instantly measured too; a run outside 3–6 min is re-cut (fewer words, a nearer stop) or justified in one sentence.
4. Stills at 390×780 and 1280×800: menu card → opening → one mid-leg mode switch → one detail card and back → ending → menu. Previous/Next/End/Menu all used once.
5. The keepsake **A Sensible Evening** lands in the daybook once, under **Neighbors**; replay does not add a second.
6. The diff contains `data/jaunts/taverns-of-chicago.json`, its LIBERTIES lines, the regenerated catalog and (if needed) `docs/JAUNTS-INITIAL-LIBRARY.md` route notes — and **no engine, compiler or CSS change**. A stop that cannot be supported is substituted with a typed supported destination and the reason recorded in the brief; it is never invented.

**Harness and gates:** `./tools/check.sh`; `node tools/smoke_budget.mjs --for-diff` (content-only diffs usually name no renderer part — say so); `node tools/play_jaunt.mjs taverns-of-chicago --all-paths`; `./tools/preflight.sh`.

Changelog: one visible entry naming the jaunt. Contract: [authoring guide](../docs/JAUNTS-AUTHORING.md) · [brief 02](../docs/JAUNTS-INITIAL-LIBRARY.md#02-taverns-of-chicago) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
