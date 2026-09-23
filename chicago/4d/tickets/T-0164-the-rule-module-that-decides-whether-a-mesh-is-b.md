---
id: T-0164
title: The rule module that decides whether a mesh is built at all now sits inside the hash of what a mesh is built from
state: done
epic: PIPELINE
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-23
closed: 2026-08-28
pr: 467
claimed_by: run 8/28/2026, 10:46:19 AM CT
blocked_on: null
needs_bake: false
---

T-0161 (#340) put the shared `drawn_by` test in `generators/common/phases.py`, which
is the right idea in a place that costs a full rebake to maintain.

`generators/common/*.py` is globbed into **both** staleness recipes:

* `mesh_inputs.py::_code_shas` — `wanted += sorted((gen / "common").glob("*.py"))`
* `terrain_inputs.py` (scheme `resolved-spec-v2`) — the same glob, line 256

So the new module's bytes are now hashed into every asset in the manifest, and
`phases.py` makes no geometry: it answers *whether a mesh is built at all*, one
step before anything is built.

**Measured 2026-08-23 on `dev` at c0436f2f**, appending a single comment line to
`generators/common/phases.py` and running `tools/validate.py --all`:

    stale check: 0 asset(s) match their inputs, 344 stale

**344 of 344, for a comment.** For comparison, the same edit to `generators/build.py`
stales 342 — the two spec-hashed assets are insensitive to `build.py` but not to
`common/`, because only `terrain_inputs.py` reads them and it globs `common/` too.
So the new module is hashed *more widely* than the builder it was extracted from.

This is the trap T-0139 and T-0161 between them cost three runs, one directory
further out. `mesh_inputs.py` states the principle it now breaks, in its own words:

> A hash that cries stale for reasons that cannot change the geometry gets
> disbelieved, and a disbelieved gate is worse than no gate.

and, on itself: *"Not this file, which computes the hash and makes no geometry."*
`phases.py` has exactly that property and is inside the hash anyway.

Nothing is red today — the module landed with its rebake, and it is unlikely to be
edited often. The cost is the next edit to it: a docstring correction, a second rule
moving in beside `drawn_by_another_layer`, or the `resolve_phase` consolidation this
module invites, each buys a full-town rebake.

**Acceptance:** an edit to the shared phase-rule module does not stale any asset,
and the reason is written where the next reader will meet it. The obvious route is
to move it out of `generators/common/` (top-level `generators/` is not globbed by
either recipe) and update the two importers — but `_code_shas` naming what `common/`
means, and excluding what makes no geometry, would do as well. Either way the change
is its own demonstration: make the edit, then show the same comment-only edit
staling **0** assets where it staled 344, and `tools/check.sh` green with no rebake.

**Links:** #340 (T-0161) · `generators/common/phases.py` · `generators/mesh_inputs.py::_code_shas`
· `generators/terrain_inputs.py:256` · T-0139 (the same trap, on `build.py`).
