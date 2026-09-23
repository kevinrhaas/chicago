---
id: T-0454
title: The gate calls a GLB stale and the bake declines to rebuild it, so a stale asset cannot be cleared by baking
state: done
epic: PIPELINE
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-31
closed: 2026-09-03
pr: 679
claimed_by: run 9/3/2026, 1:31:56 AM CT
blocked_on: null
needs_bake: false
---

Found while merging **PR #597** on 2026-08-31. Two committed tools disagree about
whether an asset needs rebuilding, and while they disagree the PR cannot be
landed by any route.

## What happened, in order

1. `tools/check.sh` on `steward/t-0429-south-water-lasalle` at `d9a04091` failed
   with exactly two errors, both staleness:

   ```
   FAIL  stale: recon_1835_blk_south_water_lasalle_d4_02__inferred_1835.glb
         its inputs now hash to 032beb895e2a, the committed mesh was built from 7a9cfe9694f3
   FAIL  stale: recon_1835_blk_south_water_lasalle_d5_01__inferred_1835.glb
   ```

2. `chicago-4d-bake.yml` was dispatched against that same branch and same commit.
   The `bake` job **succeeded in 12 m 34 s**, ran Blender, and reported
   `360x transformed — gltf-transform meshopt derivative built by bake.sh`.

3. It then reported:

   ```
   bake produced no CONTENT — only its own build stamp moved. No branch, no PR:
   the PR is the signal that a bake rebuilt something, and nothing was rebuilt.
   ```

**The gate names two assets as stale and the bake, run on the same tree, rebuilds
neither.** Both cannot be right, and there is no third tool to break the tie.

## What is known about the cause

The staleness hash is `structure_inputs_sha` from `generators/mesh_inputs.py`,
over `{scheme, structure, phase, archetype, params, code, blender_pin}`. `params`
comes from `resolve_params(...)`, and the difference in this case was real:
`siding_exposure_m` was **0.152** on `dev` and **0.127** on the branch, which is
a form parameter and therefore a mesh input.

So the gate was right that the mesh no longer matches its record. What is not
established is why `generators/build.py` did not rebuild it — whether it compares
against `assets/manifest.json` rather than recomputing, whether a merged manifest
left a hash that made the asset look current, or something else. **That is the
first thing to find out, and this ticket does not guess it.**

## Why it matters beyond one PR

Any merge that changes a mesh parameter — a form value, an archetype, a generator
module — produces exactly this state. The gate blocks the PR, and the documented
remedy the gate itself prints (*"Re-bake it (tools/bake.sh, or the
chicago-4d-bake workflow)"*) does not clear it. The remedy named in the error
message has to work.

**Acceptance:**

1. The disagreement is reproduced deliberately — change one mesh parameter on a
   branch, run the gate, run the bake — and the reason the bake skips is
   demonstrated rather than argued.
2. Whichever is wrong is fixed so that the sentence the gate prints is true: a
   stale asset is cleared by running the bake the error message names.
3. A test asserts it, so the two cannot drift apart again silently. This is the
   same class of fault as the stale-mirror and stale-board checks (T-0154,
   T-0155): two copies of one fact that can disagree.
4. **PR #597 is re-read against the result.** It is currently blocked on exactly
   this and on nothing else — its conflicts are resolved and its gate is
   otherwise green.

## What it turned out to be — 2026-09-03

**Neither tool was wrong. They were never shown the same tree.**
`.github/workflows/chicago-4d-bake.yml`'s second step ran, unconditionally:

```
if git ls-remote --exit-code --heads origin dev >/dev/null 2>&1; then
  git checkout -B dev origin/dev
fi
```

So a bake **dispatched against a branch discarded that branch and baked `dev`**.
`dev` was fresh, so Blender rebuilt 360 assets byte for byte, and
`tools/bake_content_changed.py` answered "no CONTENT" — honestly, about a tree
nobody had asked about. `generators/build.py` never skipped anything; it was
never asked. The gate's stale asset was on a branch the bake had thrown away
before Blender started.

Reproduced deliberately (acceptance 1), one mesh parameter moved on a branch —
`bates_auction_room` `siding_exposure_m` 0.14 → 0.127, the same field and the
same shape as the reported case:

```
tools/validate.py --stale     stale check: 367 match, 1 stale
                              FAIL stale: bates_auction_room__frame_1834.glb is STALE
                                   inputs now hash e2c58b0e5ee8, mesh built from 010608142cf0
the workflow's step, verbatim HEAD t0454-repro fbebc203 -> dev 8ecfcb57
                              the branch's changed parameter: 0 occurrences on disk
                              stale check: 368 match, 0 stale  ← the fault, exactly
build.py --only <id>          built bates_auction_room__frame_1834.glb, 36,512 bytes, ~394 tris
   on the branch, 0.7 s       stale check: 368 match, 0 stale
```

The bake clears the gate in under a second **when it is shown the tree that
carries the change**. The remedy the gate prints was true of `tools/bake.sh` and
false of the workflow the same sentence names.

**The fix (acceptance 2).** `tools/bake_ref.py` decides which ref a bake builds,
reading the tiers from `.github/pipeline.json`: the schedule and any run whose
ref is the production tier build `dev` — the nightly is unchanged, and nothing
can PR into `main` — and everything else builds the ref it was started on. The
PR base follows the ref that was baked.

**The test (acceptance 3).** `tools/bake_ref.py --self-test`, 14 cases, wired
into `check.sh`. Ten are the decision; four are drift guards on the workflow
itself, because a rule nothing calls any more is the same bug wearing a
different hat. Both halves demonstrated firing when broken.

**PR #597 (acceptance 4) is re-read and needs nothing.** It **merged** on
2026-09-01 at 00:40 UTC, so the ticket's "currently blocked on exactly this" no
longer holds; `dev` reports 368 assets fresh and 0 stale. T-0429 has since been
re-opened and claimed for its next deal, and it is that run — and every future
one that moves a mesh parameter — the fix is for.
