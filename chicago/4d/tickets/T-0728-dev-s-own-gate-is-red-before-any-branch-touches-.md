---
id: T-0728
title: dev's own gate is red before any branch touches it: three research cohorts are stale and seven household records no longer re-derive from the ladder
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: repaired by T-0739 (#863) — pilot --gate 0, mint_civic_residents --check re-derives, compile_scene --check OK on dev
needs_bake: false
closed_at: 2026-09-10T04:20:08.493Z
claimed_run: null
---

dev's own gate is red before any branch touches it: three research cohorts are stale and seven household records no longer re-derive from the ladder.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Measured on a clean `origin/dev` worktree at 06a0a9ec on 2026-09-05 — no branch, no edits:

```
python3 tools/select_resident_research_pilot.py --gate
  data/research/residents/pilot_75_cohort.json is stale; regenerate without --gate
  ... and the same for pass_02_75_cohort.json and pass_03_75_cohort.json, and for
      cohorts 13, 14 and 15

python3 tools/mint_civic_residents.py --check
  hh_campbell_james_b.json, hh_hale_john.json, hh_lloyd_alexander.json,
  hh_price_jeremiah.json do not match the derivation — 4 file(s) differ; run --build

python3 tools/mint_civic_residents.py --regrade --check
  hh_chandler_joseph.json, hh_clybourne_archibald.json, hh_kingston_paul.json
  do not match the regrade — 3 file(s) differ; run --regrade

python3 tools/compile_scene.py --all --check
  5 derived file(s) disagree with the dataset — clybourn_slaughterhouse,
  elston_soap_candle_manufactory, green_tree_tavern, pruyne_kimball_drugstore,
  residents_sources
```

That is nine failing steps of `check.sh`, which `docs/PIPELINE.md` names as the dev gate and
nothing else. **No PR into `dev` can go green until they are repaired**, and every branch that
runs the gate pays four minutes to rediscover a red it did not cause — the exact cost T-0216
built `dev-smoke-state.mjs` to stop paying for the smoke, and which the fast gate has no
equivalent for.

**How it got here, as far as the tree says.** All four are the same shape: a derivation whose
inputs moved and whose outputs were not regenerated in the same commit. The land-sale evidence
pass reached the households and the sidecars; the cohort selectors read the resident index and
it grew under them. Each has a stated repair command in its own error message, which is the
good news — but running them blind is not the unit. **Regenerating seven household records
means reading what changes in them**, because `mint_civic_residents.py --build` mints grades
and this project does not accept a grade nobody looked at.

The five sidecars are repaired by T-0713's branch, which had to recompile them to reach the
dataset step at all; if that PR lands first this ticket is four steps smaller.

**Worth deciding while here:** `check.sh` has no counterpart to `dev-smoke-state.mjs`, so the
answer to "is this red mine?" costs a clean worktree and a full run every time. A recorded
standing result for the fast gate would have turned this ticket's four minutes into one command.
That is a second ticket if it is wanted, not a smuggled scope here.

**Acceptance:** `./tools/check.sh` green on `origin/dev` with nothing else changed; each
regenerated record's diff read and what moved stated in the PR; a STATUS section naming which
commit's derivation each output had fallen behind.
