---
id: T-0521
title: dev's own check.sh gate is red in ten steps since the 1840 census merge, so no branch can prove itself
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-03
pr: null
claimed_by: null
blocked_on: Duplicate of dev's T-0522, which files the same red-gate finding; and the gate it reports was fixed by T-0491 (PR #682). Filed on this branch before either landed.
needs_bake: false
closed_at: 2026-09-03T21:35:44.629Z
claimed_run: null
---

dev's own check.sh gate is red in ten steps since the 1840 census merge, so no branch can prove itself.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Measured on a clean `origin/dev` worktree at `6e72679b`, 2026-09-03**, with
`pip install jsonschema pyproj` and nothing else: `./tools/check.sh` fails **ten
steps**. Every one of them traces to `4fa63347` — *"data(chicago-4d): register
recovered resident census bridge research"*, PR #670, merged 2026-09-02 22:55 CDT,
fourteen commits before dev's head.

```
^ dataset (schema, provenance, date gates, licenses, staleness, publish)
^ validator self-tests
^ inferred households, adoptions and their buildings match the programme
^ every flora and fauna figure is declared read or banked unread
^ published mirror matches its source
^ the reconstructed residents' invented names re-derive
^ the documented residents on reconstructed roofs re-derive from the register
^ the minted documented residents re-derive from the register
^ the minted letter-list residents re-derive from the register
^ the scene-date register re-derives, and every action names its target
```

**The four distinct faults underneath them:**

1. **A source record outside its own schema.** `data/sources/resident_research_v4_1835_census_bridge.json`
   declares `type: 'research_synthesis'` and `rights_status: 'research_notes'`, and
   neither is in the schema's enum. This is the one that fails `validate.py --all`
   with `2 error(s)`, and it cascades: `test_validate.py`'s own
   *"the committed dataset validates clean"* self-test fails on the same two lines,
   which is why the validator's self-tests are red as well as the dataset.
   **It is a provenance decision, not a typo** — either the record is mis-declared,
   or the project has decided a research synthesis is a source type and the schema
   has not been told. Do not silently retype the record to pass.
2. **Twelve unbanked `later_census` figures.** `persons[].later_census.serial`,
   `.year`, `.source_id`, `.source_image`, `.identity_confidence`,
   `.name_confidence`, `.serial_mapping_confidence` and the five
   `.household.*` counts are shipped to the browser on 1-3 records each, read by no
   renderer and absent from `layer_reads_baseline.json`. The gate's own instruction
   applies: wire them up, or bank them with `--update` and say in the message why a
   figure nobody builds is in the payload.
3. **`data/research/newspapers/register_1835.json` is stale** — not what
   `tools/compile_register.py --build` produces.
4. **RESIDENT SYNTHESIS FAIL** on all four re-derivation steps. Visible in the
   renderer too, not just the gate: an unstaged mobile smoke on dev's tree reads
   `a reconstructed resident has an invented period name — name "undefined"` and
   five more in the same family.

**Why it is worth its own ticket rather than a line in someone else's PR.** The dev
gate is `check.sh` and nothing else (`docs/PIPELINE.md`), so while it is red **no
branch can be merged on a green gate and every run must either hold or merge on a
red one.** T-0448 already records the same problem for the SMOKE; this is the same
failure mode one tier down, on the gate that is supposed to be the fast, reliable
half. Found by the T-0426 run, which held its PR (#675) on it after proving its own
branch introduced no new failure and repaired one.

**The mirror step is already fixed on that branch** — running `tools/publish.sh`
carried three resident household files the mirror had been missing since #670, so
`published mirror matches its source` passes there and this ticket is nine steps
once it lands.

**Acceptance:** `./tools/check.sh` exits clean on `origin/dev` with
`jsonschema` and `pyproj` installed and nothing else, and the schema/record
question in (1) is answered in writing rather than typed around.
