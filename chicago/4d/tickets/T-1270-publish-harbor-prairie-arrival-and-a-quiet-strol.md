---
id: T-1270
title: Publish harbor, prairie arrival and a quiet stroll jaunts
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

Author only this bounded content batch — **3 separate short jaunts** (harbor, prairie arrival and a quiet stroll): `along-the-harbor`, `from-prairie-to-town`, `an-evening-stroll`. Each is its own outing with its own file, not stops in one long tour. Content only: JSON, evidence, liberties, regenerated catalog; the engine is finished (5G) and a story that needs an engine change reports it against the engine ticket instead of changing code here.

**Depends on:** T-1259, T-1256, T-1257, T-1258. Runs in parallel with the other 5I batches — each owns only its own files.

**Shared authoring rule** (every stop, every jaunt): read `data/structures/<id>.json`, its sidecar and dossier; exterior stand-off only; 25–60 words of primary text; each sentence tiered — DOC with source id **and** locator, INF with its reasoning, invented connective text (errand, prices, small talk, the keepsake) `reconstructed` with a LIBERTIES line; no quotation in a named person's mouth; nothing after 1 July 1835 narrated as present; no figure, ceremony or Indigenous dialogue; `links[]` point at existing cards. All ids below were verified against `data/sidecars/1835/index.json` on 2026-09-17; several positions are `reconstructed` — the text must not claim a placed front door. Follow [docs/JAUNTS-AUTHORING.md](../docs/JAUNTS-AUTHORING.md).

**23. Along the Working Harbor** (`along-the-harbor`) — River transportation · Horse · Knows the Harbor (Wayfinding) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#23-along-the-working-harbor)
- Stops: `newberry_dole_warehouse` → `dearborn_street_drawbridge` → `north_pier` → `chicago_lighthouse_1832`
- Play: follow freight; inspect a crossing; view the pier; learn the lighthouse's role; leave with a harbour route note.
- Cautions: no boarding vessels or entering the tower; safe stand-offs; cite the pier's construction-stage limits.
**24. From Prairie to Town** (`from-prairie-to-town`) — Migration and routes · Horse · Into Town (Wayfinding) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#24-from-prairie-to-town)
- Stops: `anchor:lake_shore_south` → `fort_dearborn_palisade` → `peck_store` → `sauganash_hotel`
- Play: orient at the open shore (a typed viewpoint, not an establishment); approach the fort; find a supply shop; finish at a lodging place.
- Cautions: do not stage the August removal, an 1812 encounter or any Indigenous presence; the long first leg is the one to measure — Fly and Instantly must stay offered.
**25. An Evening Stroll** (`an-evening-stroll`) — Leisure · Walk · A Pleasant Circuit (Neighbors) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#25-an-evening-stroll)
- Stops: `sauganash_hotel` → `peck_store` → `chicago_democrat_office` → `exchange_coffee_house`
- Play: notice a shopfront, a newspaper office and a social meeting place; end with a short keepsake note — no resources, no plot.
- Cautions: the evening premise changes no lighting and claims no dated event; no advertised entertainment is invented — this is the batch's quiet outing.

**Acceptance:**
1. All 3 files compile `available` (`python3 tools/compile_jaunts.py` in `check.sh`); every destination, source and locator resolves; every path reaches an ending.
2. `node tools/play_jaunt.mjs <id> --all-paths` walks every choice of every jaunt with no dead end and no double keepsake.
3. Each jaunt's primary path is measured on the published mirror at its recommended mode (normally 4–6 min; a quiet 3–4 min outing is fine) and a faster mode; the numbers sit in the PR beside the cards' estimates; any outlier is re-cut or justified in a sentence.
4. The batch's quiet outing (named above) declares no resource and shows no strip; the others use only the mechanics their subject earns.
5. Stills at 390×780 for one jaunt of the batch: card → opening → a detail card and back to the same stop → ending → menu; all 3 cards Start and End returns to the menu.
6. The diff is content only — `data/jaunts/along-the-harbor.json`, `data/jaunts/from-prairie-to-town.json`, `data/jaunts/an-evening-stroll.json`, LIBERTIES lines, the regenerated catalog and route notes in the briefs. A stop that cannot be supported is substituted with a typed supported destination and the reason recorded in its brief. Completion means the whole batch; split inside this band only on a real, named blocker.

**Harness and gates:** `./tools/check.sh`; `node tools/smoke_budget.mjs --for-diff` (content-only — state that no renderer part is named); `./tools/preflight.sh`.

Changelog: one visible entry naming the 3 jaunts. Contract: [authoring guide](../docs/JAUNTS-AUTHORING.md) · [briefs](../docs/JAUNTS-INITIAL-LIBRARY.md) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
