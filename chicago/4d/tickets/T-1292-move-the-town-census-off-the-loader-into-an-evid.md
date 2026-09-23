---
id: T-1292
title: Move the town census off the loader into an Evidence → City summary topic
state: open
epic: RENDERING
requested_by: owner
seen: true
effort: S
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

The owner: *"remove all of the number and percent households reconstructed, data etc to one of the tabs as an overall city and summary."* The loader's census card (`#gate-census`: buildings standing of the roofs the town held; people named, graded attested/inferred/reconstructed, of the 1835 count) moves off the first screen into an Evidence topic called **City**, unchanged in definitions and denominators, and the loader stops showing it. Small, self-contained, and it unblocks the welcome (T-1278), which must not carry a coverage dashboard.

**Depends on:** nothing. **Runs in parallel with:** T-1246, T-1248, T-1277. T-1278 depends on this.

**What exists today:**
- `renderers/web/js/census.js` `mountGateCensus({ dataBase, root })` reads `data/town_census.json` and `data/residents/index.json` and paints `#gate-census` (rows `.gc-row`, figures `.gc-n`, bars `.gc-bar`, key `.gc-key`); `main.js` ~L900 starts it before `loadScene` and awaits it before `ready`; `api.census` carries the document for the smoke.
- `renderers/web/js/evidence.js` `createEvidenceHub` paints the Evidence tab as tiles over seven topics (`grades`, `liberties`, `ground`, `fauna`, `plants`, `exclusions`, `uncertain`); each topic reads its entries from an existing mount in `index.html`.
- `tools/smoke_renderer.mjs` part 1 (~L2094) asserts "the gate shows the town census" and "the gate's figures are the committed data's" against `#gate-census` and `api.census`.
- `world.describe()` writes the "when the town is" line into `#gate-sub` at ready (~L2517).

**Build:**
1. Add an eighth Evidence topic `city` ("The town in numbers: what stands, who is named, and what each grade promises") with a mount `#city` in `index.html`; `mountGateCensus` becomes `mountCityCensus({ dataBase, root })` and paints the same two ladders into that mount, plus the census's `target_date`, `derived_by` and the build stamp, and one sentence per figure saying what it counts (the T-0782 wording, kept).
2. Remove `#gate-census` from `index.html` and its CSS from `walk.css`; the loader no longer starts or awaits the census — mount it lazily the first time the Evidence tab opens (the topic count re-reads on show, as the hub already does). Keep `api.census` populated once the topic has painted so the smoke can still compare figures.
3. Move the two smoke checks from part 1 to the Evidence section of the part that opens the drawer (part 8/9 per `smoke_budget.mjs --for tools/smoke_renderer.mjs`), asserting the same figures against `api.census` and `data/residents/index.json` at the new location. Do not delete the assertions.
4. Evidence tile order: `grades`, `city`, then the rest.

**Acceptance:**
1. Cold boot at 390×780 and 1280×800 shows no count, percentage or bar anywhere on the loader or the ready screen; `#gate-census` does not exist in the DOM.
2. Evidence → City shows both ladders with the committed figures, the grade key, the census date and the build stamp; at 390×780 nothing clips and the topic scrolls inside the sheet.
3. The two relocated smoke checks pass on the published mirror at both viewports; part 1 no longer references `#gate-census`.
4. Boot payload does not grow (the census JSON is now fetched on demand — measure_boot_payload should read slightly lower).

**Harness and gates:** `./tools/check.sh`; `node tools/smoke_budget.mjs --for-diff`; run the named parts `--published` at both viewports; `node tools/measure_boot_payload.mjs --check`.

**Out of scope:** the Sources browser and per-source counts (T-1276), the welcome (T-1278).

Changelog: one visible entry ("the town's numbers moved from the loading screen to Evidence → City"). Contract: [architecture § Sources & City](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#sources--city) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
