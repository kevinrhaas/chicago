---
id: T-1265
title: Publish Fort Dearborn Errand as a five-minute jaunt
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

Author the complete priority jaunt **Fort Dearborn Errand** (`fort-dearborn-errand`) — one of the six the owner named first — from [brief 06](../docs/JAUNTS-INITIAL-LIBRARY.md#06-fort-dearborn-errand). Content only: one JSON file, its evidence, its liberties, the regenerated catalog. The engine (5G) is finished; if a story needs an engine change, that is a finding for the engine's ticket, not a change in this PR.

**Premise:** Carry a small fictional supply request through the fort's everyday service places.
**Category:** Fort Dearborn · **Recommended mode:** Walk · **Keepsake:** Accounted for at the Fort (Livelihood) · **Target:** 4–6 min primary path.

**Depends on:** T-1259 (menu), T-1256 (mechanics), T-1257 (links and leg notes), T-1258 (daybook). Runs in parallel with the other 5H tickets — each owns only its own file.

**Stops, in story order** (all verified to exist in `data/sidecars/1835/index.json` on 2026-09-17; positions are inferred or reconstructed, never attested — the stop text must not claim a front door the record does not place):
1. [`fort_dearborn_palisade`](../data/structures/fort_dearborn_palisade.json) — the stockade — approach at the supported entrance stand-off
2. [`fort_dearborn_guard_house`](../data/structures/fort_dearborn_guard_house.json) — guard house vicinity — state the errand
3. [`fort_dearborn_sutlers_store`](../data/structures/fort_dearborn_sutlers_store.json) — sutler's store — choose a supply
4. [`fort_dearborn_store_house`](../data/structures/fort_dearborn_store_house.json) — store house — account for the package
5. [`fort_dearborn_shop`](../data/structures/fort_dearborn_shop.json) — the shop — finish (a workshop by record; not automatically a blacksmith)

**Mechanics for this jaunt:** `cargo` and `readiness`; a concise ending that makes the fort a working neighbour, not a museum.

**Evidence and route cautions:** Harrison 1830 plan continuity to 1835 is inferred — say so; invent no interior access, military procedure, figure or Indigenous dialogue; use exterior stops throughout; the August 1835 gathering is not staged.

**Authoring checklist (every stop):** read `data/structures/<id>.json`, its sidecar and dossier; state the stop's stand-off kind (exterior stand; no interior is implied); write 25–60 words of primary text; mark each sentence's tier — a DOC claim has a source id **and** locator, an INF claim states its reasoning, invented connective text (the errand, prices, small talk) is `reconstructed` with a LIBERTIES line; no quotation is put in a named person's mouth; nothing after 1 July 1835 is narrated as present; no human figure, ceremony or Indigenous dialogue is depicted. Card `links[]` point at the existing structure/person/source cards, never at a copy.

**Acceptance:**
1. `data/jaunts/fort-dearborn-errand.json` compiles `available` in `check.sh` (`python3 tools/compile_jaunts.py`); every destination resolves; every claim's source and locator resolve; the compiler's path walk reaches every ending.
2. Every authored choice and ending is exercised by `tools/play_jaunt.mjs fort-dearborn-errand --all-paths` (T-1256's walker); no dead end, no double keepsake.
3. Measured on the published mirror: primary path at **Walk** ≈ 4–6 min (opening + stops + rides, deep cards closed), quoted in the PR beside the card's estimate; Fly and Instantly measured too; a run outside 3–6 min is re-cut (fewer words, a nearer stop) or justified in one sentence.
4. Stills at 390×780 and 1280×800: menu card → opening → one mid-leg mode switch → one detail card and back → ending → menu. Previous/Next/End/Menu all used once.
5. The keepsake **Accounted for at the Fort** lands in the daybook once, under **Livelihood**; replay does not add a second.
6. The diff contains `data/jaunts/fort-dearborn-errand.json`, its LIBERTIES lines, the regenerated catalog and (if needed) `docs/JAUNTS-INITIAL-LIBRARY.md` route notes — and **no engine, compiler or CSS change**. A stop that cannot be supported is substituted with a typed supported destination and the reason recorded in the brief; it is never invented.

**Harness and gates:** `./tools/check.sh`; `node tools/smoke_budget.mjs --for-diff` (content-only diffs usually name no renderer part — say so); `node tools/play_jaunt.mjs fort-dearborn-errand --all-paths`; `./tools/preflight.sh`.

Changelog: one visible entry naming the jaunt. Contract: [authoring guide](../docs/JAUNTS-AUTHORING.md) · [brief 06](../docs/JAUNTS-INITIAL-LIBRARY.md#06-fort-dearborn-errand) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
