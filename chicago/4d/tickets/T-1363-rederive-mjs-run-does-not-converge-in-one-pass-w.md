---
id: T-1363
title: rederive.mjs --run does not converge in one pass when the town model moves: the arrival stage draws from a file the sequence rebuilds after it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-18
closed: 2026-09-21
pr: 1608
claimed_by: run 9/20/2026, 11:52:50 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T05:25:36.435Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35562378274
---

rederive.mjs --run does not converge in one pass when the town model moves: the arrival stage draws from a file the sequence rebuilds after it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Measured on #1495 (T-1172), 2026-09-19, three times over.

`tools/derived_manifest.json` runs `reconstruct_residents_1835.py --stage
attribute_fill_arrival --build` at step 75 and `model_town_1835.py --build` at step 97.
The arrival stage DRAWS from `data/reconstruction/1835_town_model.json`, so a run that
moves the population — any resident-writing stage — leaves the arrival draws one model
behind at the end of `--run`, and the gate goes red on ~1,200 cards with *"the committed
value does not re-derive from the programme"*. A second `--run` does not fix it either,
because the second pass moves the model again.

What actually converged it, by hand, after the sequence:

    python3 tools/reconstruct_residents_1835.py --stage attribute_fill_arrival --build
    python3 tools/migrate_attribute_tiers.py --build
    python3 tools/profile_population_1835.py --build

The manifest's own `_doc` already says ordering is a measured pass and not a graph anyone
should trust — this is a concrete edge it gets wrong, with a reproduction. Note the
constraint that makes it awkward: the model is derived FROM the layer the arrival stage
writes into, so simply moving step 75 below step 97 trades one lag for another. The
honest fix is probably a declared second pass over the stages that read a model the
sequence also rebuilds, rather than a re-ordering.

**Related:** the readmission stage (`readmit_borderline_roster.py`) is measured in
`tools/writer_inventory.json` and still `pending` — it has the same shape of dependency
and wants placing at the same time.
