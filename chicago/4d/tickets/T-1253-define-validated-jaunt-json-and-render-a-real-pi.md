---
id: T-1253
title: Define validated jaunt JSON and render a real pilot preview
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

The **jaunt content contract**: a validated JSON schema, a build-time compiler that produces a light catalog, the semantic validator, an authoring guide, and the first real jaunt file (`new-in-chicago`) as the pilot. The owner: *"Design jaunts as data-driven content — preferably structured JSON plus reusable UI/engine components — so adding a jaunt primarily means authoring its premise, stops, decisions, conditions and outcomes rather than writing custom application logic … support an initial library of roughly 25 jaunts, designed so it can grow to 50+ through data."* Everything the engine (T-1279) and the content batches (5H/5I) rely on is fixed here, so this lands before them and touches no runtime UI beyond listing the catalog on the welcome if T-1278 is already in.

**Depends on:** nothing hard. **Runs in parallel with 5F.** Uses T-1248's compiler for claim registration if it has landed (otherwise emits `data/sidecars/1835/jaunts/claims.json` for T-1248 to ingest — say which in the PR). T-1279 depends on this.

**What exists today:** no jaunt code anywhere (`grep -ri jaunt renderers tools` is empty); typed ids the schema must reference: structures (`data/sidecars/1835/index.json`, 383), anchors (`data/scenes/1835.json`, 17), intersections (5), people (`sidecars/1835/people.json`), businesses (derived from structures until T-1180 — see T-1277); `data/exclusions.json` and `excluded_by_date` for date gates; confidence vocabulary `attested|inferred|reconstructed` with `[DOC]/[INF]/[CONJ]` display aliases; `docs/LIBERTIES.md` append-only; `tools/publish.sh` copies `data/sidecars/` whole.

**Build:**
1. `data/jaunts/schema.json` (JSON Schema, draft 2020-12) per [architecture §C](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#c-jaunt-json-contract): identity, timing inputs, `stops[]` with typed `destination {kind, id}`, `text` (25–60 words, checked), `choices[]` (0–3), `links[]` (typed card links), `next` edges, declarative `when` conditions (`all/any/not`, comparisons on declared variables, `has(item)`), `effects` (`add|remove|set|inc` on declared variables/inventory, integer cents for money), `endings[]`, `keepsake`, `evidence[]` claims (`text, confidence, sources[], locator, reasoning|liberty`), `review_required`, `content_version`, `default_mode`, `allowed_modes`. No `eval`, no HTML, no per-jaunt callbacks.
2. `tools/compile_jaunts.py` (~250 lines, in `check.sh`): validates schema; semantic checks — unique ids, every destination resolves (structure/anchor/intersection/person/business), scene-date eligibility (a destination in `exclusions.json`/`excluded_by_date` is refused), every source id resolves, every `attested` claim has a locator, effects stay inside declared bounds, every reachable state has a viable choice/default/skip, every branch reaches an ending, no cycles except explicit `Previous`; a `review_required` jaunt is compiled as `unavailable` with its reason. Emits `data/sidecars/1835/jaunts/catalog.json` (id, title, premise, category, stop count, primary/secondary keepsake family, default/allowed modes, timing inputs, availability + reason, stop destination ids for ETA) and `data/sidecars/1835/jaunts/<id>.json` (full content). Registers each claim as a `jaunt` edge for the source index.
3. `data/jaunts/new-in-chicago.json` — the pilot, authored from brief 03 in `JAUNTS-INITIAL-LIBRARY.md`: five stops (`sauganash_hotel`, `hogan_store`, `peck_store`, `chicago_democrat_office`, `brown_boarding_house`), full text, one optional preference, the Wayfinding keepsake "Finding Your Feet", every factual claim cited (Hogan's post office moved about July 1834 — it is the *former* mail corner). This file is what T-1279 plays and T-1262 finishes; it is not a throwaway.
4. `data/jaunts/_fixtures/` — two tiny fixtures used only by tests (a two-stop plain walk; a three-stop branch with money) plus one deliberately malformed file the compiler must refuse without breaking the catalog.
5. `docs/JAUNTS-AUTHORING.md` (≤ 200 lines): the field reference with one worked example, the provenance rules (facts vs supported inference vs invented connective text, and how each is marked), the stop-count and word-count norms, how to run the compiler, and the "no engine change in a content PR" rule. Content authors read this page and nothing else.
6. If T-1278 has landed, the welcome's Jaunts region lists the catalog's available cards (title, premise, stops, category) and shows unavailable ones with their reason; otherwise expose `api.jaunts.catalog` only.

**Acceptance:**
1. `python3 tools/compile_jaunts.py` runs in `check.sh`, deterministic; `tools/test_compile_jaunts.py` covers every refusal above with the fixtures (dangling id, excluded date, missing locator on a DOC claim, unbounded effect, unreachable ending, cycle, malformed JSON isolated).
2. The pilot compiles as `available` with all five destinations resolved and every claim registered; its text passes the 25–60-word check per stop.
3. Adding a second fixture jaunt requires only a JSON file and a compiler run — the catalog lists it, no JS changed (show the diff).
4. `catalog.json` ≤ 30 KB at 27 entries and is not fetched at boot (`measure_boot_payload.mjs --check` unchanged); per-jaunt files load on selection only.
5. The authoring guide exists and is linked from the architecture and the execution plan.

**Harness and gates:** `./tools/check.sh` (+ the new steps); if `index.html`/`arrival.js` are touched, `smoke_budget.mjs --for-diff` → those parts `--published`, both viewports.

**Out of scope:** playing a jaunt (T-1279), estimates (T-1280), mechanics beyond schema shape (T-1256), the daybook (T-1258), menu polish (T-1259).

Visible-progress: if the welcome lists the pilot card this is visible; otherwise exemption 3 (blocks T-1279) — say which in the PR. Changelog entry either way. Contract: [architecture §C](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#c-jaunt-json-contract) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md) · [briefs](../docs/JAUNTS-INITIAL-LIBRARY.md). One PR into `dev`; claim with `ticket.mjs`.
