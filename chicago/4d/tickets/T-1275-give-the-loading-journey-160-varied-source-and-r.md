---
id: T-1275
title: Give the loading journey 160 varied source and reconstruction statuses
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

The loading-screen **status library**: the flip cards and status lines that make the arrival feel like the reconstruction being assembled as the years roll back. The owner: *"Include statuses while loading show sources we have used, like 'Assessing newspapers… Chicago Democrat' … show flip through the list of the sources in a flip card roll back type view … vary it so it is not the same every time … like extracting from x, and then show a fact periodically like 'Building P. F. W. Peck's Store', make them vary a lot, with a library of maybe a hundred or a few hundred statuses and include humorous ones like 'reticulating splines' very rarely, ideally include facts from the sources you show … feel like it starts by assessing and collecting and preparing and then it is resolving towards landing."* Target 160 entries (100–250 accepted), every fact traceable to T-1248's index.

**Depends on:** T-1247 (the card slot), T-1248 (the source index to draw facts and ids from).

**What exists today:** `arrival.js` (T-1247) exposes `#arrival-card` and the phase timeline; `api.boot` phases `scene, terrain, buildings, ground, flora, people, census, interaction`; `data/sidecars/1835/sources/index.json` lists used sources with public citation fields; structure names come from `display-name.js`; the newspaper register is research-only and not published.

**Build:**
1. `data/loading/statuses.json` (schema in `data/loading/schema.json`): `{ schema_version, entries: [{ id, phase: assess|collect|prepare|resolve|land, kind: source|build|fact|operational|humor, text, source_ids?: [], entity?: { type, id }, fact?: { locator, confidence, reasoning }, weight, min_dwell_ms }] }`. Phase arc mapped to boot phases: assess→`scene`, collect→`terrain`+`buildings`, prepare→`ground`+`flora`, resolve→`people`+`interaction`, land→`ready`. Suggested mix: assess 30, collect 35, prepare 40, resolve 25, land 28, humor 2.
2. Card kinds: **source** ("Assessing newspapers… *Chicago Democrat*, 1834–35", "Comparing the Wright and Hathaway maps of 1834") drawn from `index.json` `use: scene` sources with their date shown when retrospective (an 1884 account is evidence *about* 1835 — say so); **build** ("Reconstructing P. F. W. Peck's store", "Laying the riverbank", "Planting the prairie") naming real entity ids; **fact** — ≥ 50 entries each pairing one supported observation with its source and locator and confidence (never promote: Peck's store has no certain build date, so it is "reconstructing", not "built in summer 1835"); **operational** ("Setting the scene date to 1 July 1835"); **humor** — "Reticulating splines" and at most one other, uncited, shown in ≤ 1 % of sessions, never on error or at arrival.
3. `renderers/web/js/loading-content.js` (~200 lines): phase-local weighted shuffle bags, seedable (`?seed=` in debug and in tests), no immediate repeats, dwell 2–4 s scaled to the phase's expected duration (T-1246 weights) so a fast boot shows one or two cards and a slow prairie phase shows several; a fixed early subset of ~24 entries inlined in `loading-early.js` so cards appear before `statuses.json` (fetched in parallel with the scene) arrives; all rotation stops on `ready`/`error`; the final card at `land` is the arrival line.
4. Register every `fact` entry's `source_ids` + locator as edges of type `decision`/`loading_fact` through `tools/compile_source_use.py` (T-1248) so Sources can show "used for: loading facts" — extend the compiler's inputs, not its schema.
5. `tools/check_loading_content.py` in `check.sh`: schema valid; every `source_ids` resolves in `data/sources/`; every `entity.id` resolves in the sidecar index; no duplicate `text`; no markup in `text`; `humor` weight cap; ≥ 50 `fact` entries with locator; per-phase minimum counts; a `fact` never carries confidence above its source claim (compare to the sidecar's own attribute confidence where the entity has one).

**Acceptance:**
1. ≥ 160 distinct entries pass `check_loading_content.py`; the counts per phase and kind are printed by the check and quoted in the PR.
2. Two seeded sessions differ in card order; the same seed reproduces; no card repeats within a session until its bag empties; `prepare` cards never show during `scene` (unit-tested in `tools/test_loading_content.mjs`).
3. A throttled cold boot shows source cards in `assess`, build cards during `buildings`/`flora`, and the arrival line exactly once at 1835 (stills in the PR); a warm boot shows ≤ 2 cards and still lands cleanly.
4. Humor appears in ≤ 1 % of 10,000 simulated sessions (deterministic test), never at `land` or on error.
5. Long card text wraps to two lines at 320 px with no overflow; boot payload stays under budget (`statuses.json` ≤ 60 KB, loaded in parallel, never awaited for `ready`).

**Harness and gates:** `./tools/check.sh` (new content check + node test); `node tools/smoke_budget.mjs --for-diff` → arrival parts `--published`, both viewports; `measure_boot_payload.mjs --check`.

**Out of scope:** the flip animation and pacing (T-1247), the Sources browser (T-1276).

Changelog: one visible entry. Contract: [architecture §B](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#b-loading-content-entries) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
