---
id: T-0139
title: The bake cannot reach cook_county_courthouse_1835, so any common/ edit leaves it stale
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-22
closed: 2026-08-23
pr: 333
claimed_by: run 8/23/2026, 10:45:51 AM CT
blocked_on: null
needs_bake: false
---

The bake cannot reach `cook_county_courthouse_1835`, so any `common/` edit leaves it stale.

`generators/build.py` resolves a structure's phase against the SCENE's target date and skips the
record when no phase covers it. The courthouse's only phase (`wood_1835`) runs 1835-10-01 to
1835-12-31; the only scene in `data/scenes/` targets 1835-07-01. So `build.py --only
cook_county_courthouse_1835` prints *"skip: no phase covers 1835-07-01"* and builds nothing — while
`cook_county_courthouse_1835__wood_1835.glb` is committed, is in `assets/manifest.json`, and IS
hashed by the staleness gate like every other asset.

The consequence is a trap rather than a defect anybody has hit twice: every edit to
`generators/common/` restales that asset along with the rest of the town, and the bake that heals
the rest cannot heal it. T-0008 got past it with a throwaway script that monkey-patched
`resolve_phase` — which is exactly the shape of thing that should not be needed twice.

**Acceptance:** the bake can rebuild every asset the staleness gate holds it responsible for, by a
committed route — either the scene grows an out-of-date-range build list, or `build.py` takes an
explicit phase, or the asset stops being committed because nothing loads it (`compile_scene`
already reports it as *"1 excluded by date"*). Whichever is chosen, `tools/check.sh` stays green on
a clean tree after a `common/` edit.

**Links:** T-0008 (the run that hit it) · `generators/build.py::main` · `generators/mesh_inputs.py`
· `tools/validate.py::run_stale_check`.

---

**Second hit, 2026-08-23 (T-0015).** This blocked another run. T-0015 edited two
comments in `generators/build.py` — a docstring correcting a claim its own
measurement had disproved, plus a guard against a demonstrated export fault. That
staled all 343 assets (`mesh_inputs.py` hashes build.py's bytes), the full rebake
was run and healed 342 of them, and `cook_county_courthouse_1835__wood_1835.glb`
stayed stale because the bake still cannot reach it.

That run chose NOT to monkey-patch `resolve_phase` a second time — this ticket
says that shape of thing should not be needed twice — and reverted its build.py
changes instead. So the cost is now concrete rather than hypothetical: **this
ticket blocks any edit to `generators/build.py`, including a one-line comment**,
and it has cost two runs their intended work.
