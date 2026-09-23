---
id: T-1248
title: Compile the sources used and their reconstruction backlinks
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

Compile, at build time, **which sources this reconstruction actually used and for what** — the data behind the Sources browser (T-1276) and the loading-screen source cards (T-1275). The owner wants *"all the sources that you have used in building this … a link library or summary link to the items from that source, like what was pulled from that source for the reconstruction."* This ticket is compiler and published data only; no visitor-facing surface changes. (Visible-progress exemption 3: it is the gate blocking T-1275 and T-1276 — name both in the PR body.)

**Depends on:** nothing. **Runs in parallel with:** T-1246, T-1292, T-1277.

**What exists today:**
- `data/sources/*.json` — 292 registered sources (`data/source.schema.json`: `id, type, citation, author, date, describes_date, repository, url, archived_url, locator, tier 1–6, rights_status, what_it_supplies, what_it_does_not_supply, …`). 193 are `rights_status: check_required`; a registered source is not evidence that it reached the scene.
- `tools/compile_scene.py` `cite(source_ids, sources)` (~L239) joins citations into sidecar display fields and holds the public/internal field partition (~L215: `id, type, author, date, locator, rights_* , verified` are internal).
- Per-attribute `sources[]`/`confidence` live in `data/structures/*.json` → `data/sidecars/1835/<id>.json`; residents in `data/residents/` → `sidecars/1835/people.json` + `residents_sources.json`; terrain/flora/fauna in `data/terrain`, `data/flora`, `data/fauna` (+ `sidecars/1835/flora_sources.json`, `fauna_sources.json`); exclusions in `data/exclusions.json` → `sidecars/1835/exclusions.json`; liberties in `data/liberties.json`.
- `tools/publish.sh` copies `data/sidecars/` whole (~L184), so anything written under `data/sidecars/1835/sources/` is published without a publish.sh change. `data/research/` is never published (a `check.sh` step asserts it).

**Build:**
1. `tools/compile_source_use.py` (~300 lines), run by `check.sh` after `compile_scene.py`, deterministic (sorted keys, no timestamps): walks the inputs above and emits typed **edges** `{ source_id, entity_type: structure|person|household|business|terrain|flora|fauna|exclusion|liberty|decision, entity_id, claim: "<field path or claim label>", confidence: attested|inferred|reconstructed, locator, use: scene|other_scene|exclusion|research }`. A source with no edge is `unused` in the manifest, never dropped.
2. Outputs, under `data/sidecars/1835/sources/`: `index.json` — one compact row per source: public citation fields only, `type`, `date`, `tier`, `use`, `counts: { entities, claims }` (entities deduplicated separately from claims), `has_archive_link`; and `<source_id>.json` — that source's edges. Budget: `index.json` ≤ 120 KB; nothing here is fetched at boot.
3. Newspaper sources keep publication → issue grouping: an edge's `locator` carries issue date, page and column where the input has them.
4. Coverage report `docs/measurements/source_use_coverage.md` (generated): per input family, how many records were read, how many carried citations, how many source ids did not resolve (must be zero — rule 1), and which families are not yet covered (businesses until T-1180 lands).
5. `tools/test_compile_source_use.py`: fixture inputs → expected edges; dangling id refused; alias/citation joins; a mixed-tier entity counted once in `entities` and per claim in `claims`; a registered-but-unused source appears with `use: unused`.

**Acceptance:**
1. `python3 tools/compile_source_use.py` runs in `check.sh` and is deterministic (two runs, identical bytes).
2. Every one of the 292 sources appears in `index.json` with a `use` value; every edge's `source_id` resolves; every structure in `sidecars/1835/index.json` that carries citations has at least one edge.
3. The coverage report exists and names each unsupported family honestly.
4. No internal field (per `compile_scene.py`'s partition), no `data/research/` path, no PDF/image bytes and no `check_required` asset derivation reaches the published tree; the existing publish/research gate stays green.
5. Boot payload unchanged (`measure_boot_payload.mjs --check`), since nothing new is fetched at boot.

**Harness and gates:** `./tools/check.sh` (add the compile and test steps); `node tools/measure_boot_payload.mjs --check`. No smoke part is affected unless `index.html` changes — it should not.

**Out of scope:** the Sources browser UI (T-1276), loading cards (T-1275), jaunt claims (T-1253 registers those into this index later through the same compiler).

Contract: [architecture §D](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#d-source-use-index) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`; changelog entry says plainly that nothing visible changed and why (exemption 3).
