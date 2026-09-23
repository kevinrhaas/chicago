---
id: T-1268
title: Publish harness, candles, building materials and leather jaunts
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

Author only this bounded content batch — **4 separate short jaunts** (harness, candles, building materials and leather): `mend-the-harness`, `soap-and-candles`, `materials-for-a-roof`, `boots-and-leather`. Each is its own outing with its own file, not stops in one long tour. Content only: JSON, evidence, liberties, regenerated catalog; the engine is finished (5G) and a story that needs an engine change reports it against the engine ticket instead of changing code here.

**Depends on:** T-1259, T-1256, T-1257, T-1258. Runs in parallel with the other 5I batches — each owns only its own files.

**Shared authoring rule** (every stop, every jaunt): read `data/structures/<id>.json`, its sidecar and dossier; exterior stand-off only; 25–60 words of primary text; each sentence tiered — DOC with source id **and** locator, INF with its reasoning, invented connective text (errand, prices, small talk, the keepsake) `reconstructed` with a LIBERTIES line; no quotation in a named person's mouth; nothing after 1 July 1835 narrated as present; no figure, ceremony or Indigenous dialogue; `links[]` point at existing cards. All ids below were verified against `data/sidecars/1835/index.json` on 2026-09-17; several positions are `reconstructed` — the text must not claim a placed front door. Follow [docs/JAUNTS-AUTHORING.md](../docs/JAUNTS-AUTHORING.md).

**15. Mend the Harness** (`mend-the-harness`) — Trades and repairs · Wagon · Sound Tack (Livelihood) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#15-mend-the-harness)
- Stops: `western_hotel_stable` → `goss_cobb_saddlery` → `pierce_blacksmith_shop` → `green_tree_tavern`
- Play: notice a reconstructed wear problem; choose a harness repair; check related hardware; decide the outfit is ready or keep the trip short.
- Cautions: the repair story is invented; leather work and iron work are distinguished by the firm records.
**16. Soap and Candles** (`soap-and-candles`) — Household and trades · Horse · Light for the Evening (Provisions) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#16-soap-and-candles)
- Stops: `h_jones_store` → `elston_soap_candle_manufactory` → `thomas_church_store` → `brown_boarding_house`
- Play: make a small list; learn what the manufactory produced; choose what to carry; bring the supplies back.
- Cautions: no documented retail counter at the works — an exterior observation carries that stop; the manufactory position is reconstructed; this is the batch's quiet outing.
**17. Materials for a Roof** (`materials-for-a-roof`) — Building trades · Horse · A Builder's List (Livelihood) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#17-materials-for-a-roof)
- Stops: `newberry_dole_warehouse` → `brickyard_north_side` → `lake_house_construction` → `peck_store`
- Play: consider freight; inspect the brickmaking site; see a hotel under construction; choose a bounded material order.
- Cautions: the Lake House is under construction, not open lodging; material costs and the order are reconstructed.
**18. Boots, Leather and the Road** (`boots-and-leather`) — Trades · Horse · Equipped to Travel (Livelihood) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#18-boots-leather-and-the-road)
- Stops: `miller_tannery` → `goss_cobb_saddlery` → `john_holbrook_store` → `green_tree_tavern`
- Play: observe the tannery from outside; tell harness from clothing trades; choose practical travel kit; finish at the road.
- Cautions: do not turn the saddler into a bootmaker; substitute a verified shoemaker only if its dated location resolves.

**Acceptance:**
1. All 4 files compile `available` (`python3 tools/compile_jaunts.py` in `check.sh`); every destination, source and locator resolves; every path reaches an ending.
2. `node tools/play_jaunt.mjs <id> --all-paths` walks every choice of every jaunt with no dead end and no double keepsake.
3. Each jaunt's primary path is measured on the published mirror at its recommended mode (normally 4–6 min; a quiet 3–4 min outing is fine) and a faster mode; the numbers sit in the PR beside the cards' estimates; any outlier is re-cut or justified in a sentence.
4. The batch's quiet outing (named above) declares no resource and shows no strip; the others use only the mechanics their subject earns.
5. Stills at 390×780 for one jaunt of the batch: card → opening → a detail card and back to the same stop → ending → menu; all 4 cards Start and End returns to the menu.
6. The diff is content only — `data/jaunts/mend-the-harness.json`, `data/jaunts/soap-and-candles.json`, `data/jaunts/materials-for-a-roof.json`, `data/jaunts/boots-and-leather.json`, LIBERTIES lines, the regenerated catalog and route notes in the briefs. A stop that cannot be supported is substituted with a typed supported destination and the reason recorded in its brief. Completion means the whole batch; split inside this band only on a real, named blocker.

**Harness and gates:** `./tools/check.sh`; `node tools/smoke_budget.mjs --for-diff` (content-only — state that no renderer part is named); `./tools/preflight.sh`.

Changelog: one visible entry naming the 4 jaunts. Contract: [authoring guide](../docs/JAUNTS-AUTHORING.md) · [briefs](../docs/JAUNTS-INITIAL-LIBRARY.md) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
