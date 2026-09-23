---
id: T-1267
title: Publish land, freight, household supplies and clothing jaunts
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

Author only this bounded content batch — **4 separate short jaunts** (land, freight, household supplies and clothing): `inspect-a-lot`, `freight-for-the-store`, `household-provisions`, `a-decent-coat`. Each is its own outing with its own file, not stops in one long tour. Content only: JSON, evidence, liberties, regenerated catalog; the engine is finished (5G) and a story that needs an engine change reports it against the engine ticket instead of changing code here.

**Depends on:** T-1259, T-1256, T-1257, T-1258. Runs in parallel with the other 5I batches — each owns only its own files.

**Shared authoring rule** (every stop, every jaunt): read `data/structures/<id>.json`, its sidecar and dossier; exterior stand-off only; 25–60 words of primary text; each sentence tiered — DOC with source id **and** locator, INF with its reasoning, invented connective text (errand, prices, small talk, the keepsake) `reconstructed` with a LIBERTIES line; no quotation in a named person's mouth; nothing after 1 July 1835 narrated as present; no figure, ceremony or Indigenous dialogue; `links[]` point at existing cards. All ids below were verified against `data/sidecars/1835/index.json` on 2026-09-17; several positions are `reconstructed` — the text must not claim a placed front door. Follow [docs/JAUNTS-AUTHORING.md](../docs/JAUNTS-AUTHORING.md).

**11. Look Before You Buy a Lot** (`inspect-a-lot`) — Land · Walk · Read the Ground (News & Knowledge) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#11-look-before-you-buy-a-lot)
- Stops: `chicago_democrat_office` → `bates_auction_room` → `peck_store` → `lasalle_slough_crossing`
- Play: read an eligible land notice; tell auction context from a particular sale; orient at a known corner; inspect the wet ground and decide to inquire further or hold your money.
- Cautions: a precise offer only on a matched in-window lot; no invented parcel ownership, price or a functioning 1835 bank; caution is a successful ending; the slough crossing position is reconstructed.
**12. Freight for the Store** (`freight-for-the-store`) — River commerce · Wagon · Cargo Accounted For (Livelihood) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#12-freight-for-the-store)
- Stops: `newberry_dole_warehouse` → `dole_warehouse_south` → `peck_store` → `thomas_church_store`
- Play: count packages; choose a manageable load (`cargo` capacity); check the store list; deliver a tally.
- Cautions: warehouse roles may be sourced; this shipment and its bill are fictional; street paths only, no unloading simulation.
**13. Stock the Household** (`household-provisions`) — Household · Walk · A Cupboard Begun (Provisions) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#13-stock-the-household)
- Stops: `brown_boarding_house` → `h_jones_store` → `carpenter_south_water_store` → `peck_store`
- Play: pick a short list; select provisions; consider household goods; finish with a practical basket.
- Cautions: items tie to supported trades with bounded reconstructed quantities and prices; no compulsory health score.
**14. A Decent Coat** (`a-decent-coat`) — Shopping · Walk · Fit for the Occasion (Provisions) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#14-a-decent-coat)
- Stops: `brown_boarding_house` → `john_holbrook_store` → `harmon_loomis_store` → `sauganash_hotel`
- Play: choose an occasion; inspect supported clothing stock; compare practical needs; finish prepared for the visit.
- Cautions: no fitting service or named tailor at a shop whose record only supports retail — this is the batch's quiet outing.

**Acceptance:**
1. All 4 files compile `available` (`python3 tools/compile_jaunts.py` in `check.sh`); every destination, source and locator resolves; every path reaches an ending.
2. `node tools/play_jaunt.mjs <id> --all-paths` walks every choice of every jaunt with no dead end and no double keepsake.
3. Each jaunt's primary path is measured on the published mirror at its recommended mode (normally 4–6 min; a quiet 3–4 min outing is fine) and a faster mode; the numbers sit in the PR beside the cards' estimates; any outlier is re-cut or justified in a sentence.
4. The batch's quiet outing (named above) declares no resource and shows no strip; the others use only the mechanics their subject earns.
5. Stills at 390×780 for one jaunt of the batch: card → opening → a detail card and back to the same stop → ending → menu; all 4 cards Start and End returns to the menu.
6. The diff is content only — `data/jaunts/inspect-a-lot.json`, `data/jaunts/freight-for-the-store.json`, `data/jaunts/household-provisions.json`, `data/jaunts/a-decent-coat.json`, LIBERTIES lines, the regenerated catalog and route notes in the briefs. A stop that cannot be supported is substituted with a typed supported destination and the reason recorded in its brief. Completion means the whole batch; split inside this band only on a real, named blocker.

**Harness and gates:** `./tools/check.sh`; `node tools/smoke_budget.mjs --for-diff` (content-only — state that no renderer part is named); `./tools/preflight.sh`.

Changelog: one visible entry naming the 4 jaunts. Contract: [authoring guide](../docs/JAUNTS-AUTHORING.md) · [briefs](../docs/JAUNTS-INITIAL-LIBRARY.md) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
