---
id: T-1276
title: Browse every source the reconstruction used, with its counts and used-for links
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

The **Sources** browser: every source this reconstruction used, easy to scan though it is long, with per-source attested/inferred/reconstructed counts and a "used for" link library that opens the very cards each source fed. The owner: *"show all the sources that you have used in building this, maybe this is where you also have the stats of the attested inferred reconstructed next to that for the source list … It will be a long list so make that source list easy to review and consume and maybe have some kind of link library or summary link to the items from that source."* Built on T-1248's index; sits beside T-1292's City topic under Evidence so the narrow mobile rail gains no tab.

**Depends on:** T-1248, T-1292. T-1257 and T-1272 depend on this.

**What exists today:** Evidence hub `createEvidenceHub` (evidence.js) with topic tiles reading DOM mounts; `hud.setTitle(text, onBack)` for a pushed head title; `citations.js` `citationItems()` renders a citation list with `[DOC]/[INF]/[CONJ]` chips; `popup.js` opens a structure card by id (`show(record)`, `openId`); `people.js` `open(id)`; drawer becomes a bottom sheet on mobile (`drawer.css` ≥ L376). T-1248 publishes `data/sidecars/1835/sources/index.json` + per-source edge files. T-1292 owns the City topic and the moved smoke checks.

**Build:**
1. `renderers/web/js/sources.js` (~400 lines) mounted as an Evidence topic `sources` (tile: "The sources: what each one supplied, and where it shows"). Lazy: fetch `sources/index.json` the first time the topic opens; never at boot.
2. **List**: default filter *used in this scene*; toggle *all registered* (adds other-scene/exclusion/research/unused with their status chip). Search on citation/author; filter pills by `type` (book, newspaper, map, website, dataset, manuscript, illustration, photograph, legal, article), `tier` (1–6), `use`; sort by claims, entities, date, or title. Newspapers group as publication → issues (collapsed by default). Windowed rendering (render ~40 rows, extend on scroll) so 292+ rows stay quick on a phone.
3. **Row**: citation (public field), date, type, tier chip, and a small three-segment bar with **entities** by highest tier and the numeric **claims** by confidence (attested/inferred/reconstructed), labelled so the two are never read as one number.
4. **Detail** (pushed head title with back): what it supplies / does not supply, original and archive links (an unavailable archive link reads "no archive copy on record", never a dead button; `check_required` sources show no derived asset), then **Used for**: grouped by entity type, each row opening the existing card — `popup.show` for structures, `people.open` for persons, the terrain/flora/fauna/exclusion/liberty entries by scrolling their Evidence topic into view, and a plain "decision summary" row when there is no card. Each row carries the claim's confidence chip and locator.
5. Return path: closing a card restores the topic's search, filters and scroll (store them on the topic state; the hub already re-shows on tab select).
6. `[DOC]/[INF]/[CONJ]` chips stay as the display alias of `attested/inferred/reconstructed`; storage vocabulary untouched.

**Acceptance:**
1. Evidence → Sources lists every `use: scene` source with counts matching `index.json`; "all registered" lists all 292 with a status chip; search, each filter and sort work (smoke assertions on counts and on one known row: `andreas_1884_v1` shows type book, tier 3, date 1884).
2. Opening `chicago_democrat_1833_1835` shows its issues grouped, and a Used-for row opens the Sauganash card; back returns to the same scroll and filter (asserted at 390×780 and 1280×800).
3. Claims and entities are shown as two labelled figures; a mixed-tier entity appears once in entities and once per claim in claims (fixture-checked in `tools/test_sources_view.mjs`).
4. Missing `index.json` leaves the topic with an honest note and the rest of Evidence usable; no zero counts are painted as facts.
5. Boot payload unchanged; the topic's first open fetches ≤ 120 KB.

**Harness and gates:** `./tools/check.sh`; `node tools/smoke_budget.mjs --for-diff` → the drawer/Evidence parts, `--published`, both viewports; `measure_boot_payload.mjs --check`.

**Out of scope:** the City ladders (T-1292), loading cards (T-1275), jaunt facts appearing here (they arrive through T-1248's compiler when T-1253 registers them).

Changelog: one visible entry. Contract: [architecture § Sources & City](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#sources--city) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
