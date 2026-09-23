---
id: T-1266
title: Publish news, mail, lodging and work jaunts
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

Author only this bounded content batch — **4 separate short jaunts** (news, mail, lodging and work): `news-before-breakfast`, `letter-home`, `bed-for-the-night`, `work-on-waterfront`. Each is its own outing with its own file, not stops in one long tour. Content only: JSON, evidence, liberties, regenerated catalog; the engine is finished (5G) and a story that needs an engine change reports it against the engine ticket instead of changing code here.

**Depends on:** T-1259, T-1256, T-1257, T-1258. Runs in parallel with the other 5I batches — each owns only its own files.

**Shared authoring rule** (every stop, every jaunt): read `data/structures/<id>.json`, its sidecar and dossier; exterior stand-off only; 25–60 words of primary text; each sentence tiered — DOC with source id **and** locator, INF with its reasoning, invented connective text (errand, prices, small talk, the keepsake) `reconstructed` with a LIBERTIES line; no quotation in a named person's mouth; nothing after 1 July 1835 narrated as present; no figure, ceremony or Indigenous dialogue; `links[]` point at existing cards. All ids below were verified against `data/sidecars/1835/index.json` on 2026-09-17; several positions are `reconstructed` — the text must not claim a placed front door. Follow [docs/JAUNTS-AUTHORING.md](../docs/JAUNTS-AUTHORING.md).

**07. News Before Breakfast** (`news-before-breakfast`) — Newspapers · Walk · A Useful Clipping (News & Knowledge) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#07-news-before-breakfast)
- Stops: `sauganash_hotel` → `chicago_democrat_office` → `chicago_american_office` → `exchange_coffee_house`
- Play: choose a question; read one short item from each paper; tell reporting from an advertisement; keep a clipping.
- Cautions: only issue-dated, page-and-column-located items eligible on the scene date; later news is not current.
**08. A Letter Home** (`letter-home`) — Mail · Walk · A Letter Ready to Send (News & Knowledge) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#08-a-letter-home)
- Stops: `brown_boarding_house` → `hogan_store` → `chicago_democrat_office` → `peck_store`
- Play: choose the fictional letter's purpose; visit the FORMER mail corner; consult an eligible postal notice; writing supplies only where supported; end with a draft and a plan for posting.
- Cautions: no invented current post-office address — if dated evidence resolves a counter during authoring, substitute that typed location; otherwise the posting inquiry ends honestly unresolved.
**09. A Bed for the Night** (`bed-for-the-night`) — Lodging · Walk · A Place to Lay Your Head (Neighbors) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#09-a-bed-for-the-night)
- Stops: `sauganash_hotel` → `brown_boarding_house` → `western_hotel` → `mansion_house`
- Play: state a preference for cost or convenience; compare short supported descriptions; choose a lodging outcome.
- Cautions: room prices and availability are narrative bounds, not documented bookings; four stops may finish early without padding — this is the batch's quiet outing.
**10. Work on the Waterfront** (`work-on-waterfront`) — Employment · Horse · A Day's Work in Prospect (Livelihood) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#10-work-on-the-waterfront)
- Stops: `chicago_democrat_office` → `newberry_dole_warehouse` → `dole_warehouse_south` → `exchange_coffee_house`
- Play: choose a skill; a bounded fictional inquiry at two documented firms; leave with a work chit or a sensible next lead.
- Cautions: no actual named vacancy, wage or employer offer without a dated source; Newberry & Dole's position is reconstructed.

**Acceptance:**
1. All 4 files compile `available` (`python3 tools/compile_jaunts.py` in `check.sh`); every destination, source and locator resolves; every path reaches an ending.
2. `node tools/play_jaunt.mjs <id> --all-paths` walks every choice of every jaunt with no dead end and no double keepsake.
3. Each jaunt's primary path is measured on the published mirror at its recommended mode (normally 4–6 min; a quiet 3–4 min outing is fine) and a faster mode; the numbers sit in the PR beside the cards' estimates; any outlier is re-cut or justified in a sentence.
4. The batch's quiet outing (named above) declares no resource and shows no strip; the others use only the mechanics their subject earns.
5. Stills at 390×780 for one jaunt of the batch: card → opening → a detail card and back to the same stop → ending → menu; all 4 cards Start and End returns to the menu.
6. The diff is content only — `data/jaunts/news-before-breakfast.json`, `data/jaunts/letter-home.json`, `data/jaunts/bed-for-the-night.json`, `data/jaunts/work-on-waterfront.json`, LIBERTIES lines, the regenerated catalog and route notes in the briefs. A stop that cannot be supported is substituted with a typed supported destination and the reason recorded in its brief. Completion means the whole batch; split inside this band only on a real, named blocker.

**Harness and gates:** `./tools/check.sh`; `node tools/smoke_budget.mjs --for-diff` (content-only — state that no renderer part is named); `./tools/preflight.sh`.

Changelog: one visible entry naming the 4 jaunts. Contract: [authoring guide](../docs/JAUNTS-AUTHORING.md) · [briefs](../docs/JAUNTS-INITIAL-LIBRARY.md) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
