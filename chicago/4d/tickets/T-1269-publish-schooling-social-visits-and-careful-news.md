---
id: T-1269
title: Publish schooling, social visits and careful news reading jaunts
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

Author only this bounded content batch — **4 separate short jaunts** (schooling, social visits and careful news reading): `schoolday-errand`, `sunday-circuit`, `calling-on-neighbors`, `gossip-or-notice`. Each is its own outing with its own file, not stops in one long tour. Content only: JSON, evidence, liberties, regenerated catalog; the engine is finished (5G) and a story that needs an engine change reports it against the engine ticket instead of changing code here.

**Depends on:** T-1259, T-1256, T-1257, T-1258. Runs in parallel with the other 5I batches — each owns only its own files.

**Shared authoring rule** (every stop, every jaunt): read `data/structures/<id>.json`, its sidecar and dossier; exterior stand-off only; 25–60 words of primary text; each sentence tiered — DOC with source id **and** locator, INF with its reasoning, invented connective text (errand, prices, small talk, the keepsake) `reconstructed` with a LIBERTIES line; no quotation in a named person's mouth; nothing after 1 July 1835 narrated as present; no figure, ceremony or Indigenous dialogue; `links[]` point at existing cards. All ids below were verified against `data/sidecars/1835/index.json` on 2026-09-17; several positions are `reconstructed` — the text must not claim a placed front door. Follow [docs/JAUNTS-AUTHORING.md](../docs/JAUNTS-AUTHORING.md).

**19. A Schoolday Errand** (`schoolday-errand`) — Education · Horse · A Schooling Note (News & Knowledge) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#19-a-schoolday-errand)
- Stops: `chappel_infant_school` → `watkins_school_house` → `north_side_school_1833` → `chicago_democrat_office`
- Play: ask a bounded fictional household question; compare the documented school histories; cross between neighbourhoods; keep a useful notice.
- Cautions: two school sites are marked "use on the scene date unattested" in their records — narrate them as history, not as active classes; check operation dates and teachers before any present tense.
**20. A Sunday Circuit** (`sunday-circuit`) — Social life · Walk · A Morning Among Neighbors (Neighbors) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#20-a-sunday-circuit)
- Stops: `first_presbyterian_church` → `st_marys_church` → `walker_meeting_house` → `sauganash_hotel`
- Play: notice the buildings; read short supported histories; finish with a social-visit premise — no score, sermon or compulsory choice.
- Cautions: no actual service schedule or day is asserted for 1 July; an era-themed outing, not a dated Sunday — this is the batch's quiet outing.
**21. Calling on Neighbors** (`calling-on-neighbors`) — Social life · Walk · An Introduction Made (Neighbors) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#21-calling-on-neighbors)
- Stops: `brown_boarding_house` → `peck_store` → `exchange_coffee_house` → `sauganash_hotel`
- Play: choose an introduction note; learn about a merchant household from its card; find a public meeting place; leave a fictional calling card.
- Cautions: named resident information stays on the sourced cards; no invented real-person quotation or encounter.
**22. Gossip or Printed Notice?** (`gossip-or-notice`) — News and social life · Walk · A Careful Reader (News & Knowledge) — [brief](../docs/JAUNTS-INITIAL-LIBRARY.md#22-gossip-or-printed-notice)
- Stops: `wolf_point_tavern` → `chicago_democrat_office` → `chicago_american_office` → `exchange_coffee_house`
- Play: hear explicitly invented connective gossip; inspect two eligible items; decide what is actually supported; keep a careful note.
- Cautions: no defamatory invented claim about a real person; uncertainty is a valid ending and no fabricated source settles it.

**Acceptance:**
1. All 4 files compile `available` (`python3 tools/compile_jaunts.py` in `check.sh`); every destination, source and locator resolves; every path reaches an ending.
2. `node tools/play_jaunt.mjs <id> --all-paths` walks every choice of every jaunt with no dead end and no double keepsake.
3. Each jaunt's primary path is measured on the published mirror at its recommended mode (normally 4–6 min; a quiet 3–4 min outing is fine) and a faster mode; the numbers sit in the PR beside the cards' estimates; any outlier is re-cut or justified in a sentence.
4. The batch's quiet outing (named above) declares no resource and shows no strip; the others use only the mechanics their subject earns.
5. Stills at 390×780 for one jaunt of the batch: card → opening → a detail card and back to the same stop → ending → menu; all 4 cards Start and End returns to the menu.
6. The diff is content only — `data/jaunts/schoolday-errand.json`, `data/jaunts/sunday-circuit.json`, `data/jaunts/calling-on-neighbors.json`, `data/jaunts/gossip-or-notice.json`, LIBERTIES lines, the regenerated catalog and route notes in the briefs. A stop that cannot be supported is substituted with a typed supported destination and the reason recorded in its brief. Completion means the whole batch; split inside this band only on a real, named blocker.

**Harness and gates:** `./tools/check.sh`; `node tools/smoke_budget.mjs --for-diff` (content-only — state that no renderer part is named); `./tools/preflight.sh`.

Changelog: one visible entry naming the 4 jaunts. Contract: [authoring guide](../docs/JAUNTS-AUTHORING.md) · [briefs](../docs/JAUNTS-INITIAL-LIBRARY.md) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
