---
id: T-0161
title: A full bake rebuilds estray_pen, which the dataset refuses to have committed, so every full bake needs a manual deletion to pass its own gate
state: done
epic: PIPELINE
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-23
closed: 2026-08-23
pr: 340
claimed_by: run 8/23/2026, 5:59:20 PM CT
blocked_on: null
needs_bake: false
---

`data/structures/estray_pen.json`'s only phase carries a `drawn_by` block that
could not be plainer:

> *"A phase carrying this block builds NO MESH: no GLB is baked from it,
> tools/compile_scene.py writes `asset: null` into the sidecar, the renderer
> loads no asset for it and the walker is not stopped by its footprint."*

`generators/build.py` does not read it. **Zero** occurrences of `drawn_by` in
that file, while `tools/validate.py`, `tools/compile_scene.py` and
`tools/generate_dooryard_plantings.py` all honour it.

So the builder and the validator disagree about the same record, and the bake
sits between them:

1. `build.py --all` bakes `estray_pen__pen_1833.glb` (119,816 bytes) and stamps
   it into `assets/manifest.json`;
2. `web_derivatives.sh` then makes a derivative of it;
3. `validate.py --all` fails twice — *"declares drawn_by but
   assets/gltf/… is still committed"* and *"…manifest.json still lists …"*;
4. so `tools/check.sh`, which `tools/bake.sh` runs as its own last step, is red.

**Every full bake therefore needs a hand-deletion to pass its own gate** — the
GLB, the derivative, and the entry in three manifests. Hit twice in one day, on
T-0015 and again on T-0160, by a run that had already been told about it once.

This is the fault class the record's own note is about. The geometry was retired
on 2026-08-18 (T-0051) precisely because the outbuilding archetype cannot build
a roofless structure; what the bake keeps rebuilding is the thing that was
deliberately removed, and only a validator rule stops it reaching the site.

**Blocked by T-0139**, which is worth stating because it is now the third
ticket in that position: the fix belongs in `generators/build.py`, and
`mesh_inputs.py` hashes that file's bytes into every asset's staleness key, so
a one-line skip stales all 345 assets and the rebake cannot reach the
courthouse.

**Acceptance:** `build.py` skips a phase carrying `drawn_by` — the same test
`validate.py` applies, read from the same place rather than restated — and says
it skipped it, the way it already says `skip: no phase covers …`. A full bake
then leaves no `estray_pen` GLB, no derivative and no manifest entry, and
`tools/check.sh` is green straight out of `tools/bake.sh` with no hand-deletion.
Demonstrate on a full `--all` run, not on `--only`: `--only` is how this got
mis-diagnosed once already.
