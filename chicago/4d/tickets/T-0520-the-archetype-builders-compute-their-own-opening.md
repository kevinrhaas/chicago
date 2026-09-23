---
id: T-0520
title: The archetype builders compute their own opening rectangles beside the ones facade_openings states, and only a town-wide rebake can join them
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-13
pr: 1251
claimed_by: run 9/13/2026, 7:30:48 AM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-13T13:23:11.599Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34757125217
---

Raised out of T-0459, which is where the reader came from, and left open there
deliberately rather than folded in.

## The state it left

`generators/archetypes/facade_openings.py` states, Blender-free, where the doors
and windows are on a building's front wall, and `tools/generate_business_signboards.py`
now reads it: no board is fixed over an opening any more. The rectangles are stated
in each archetype's `*_params` module, from the same shared constants the builder
draws with — but the BUILDER does not read them. `frame_storefront.py`,
`log_dwelling.py` and `outbuilding.py` still compute the same arithmetic inline.

So there are two copies of one rule, and the second one is the one a visitor sees.

## Why it was not simply done

`generators/mesh_inputs.py::_code_shas` hashes each archetype's BUILDER MODULE byte
for byte into every asset's `inputs_sha256`. Touching those three files staled **212
of 349 assets** — measured on this branch, 124 outbuildings, 48 log dwellings, 40
storefronts — and `validate.py --stale` then hard-fails the tree until every one of
them is rebaked. The refactor is byte-for-byte geometry-neutral by construction and
still costs a town-wide bake, which is ~20 minutes of Blender and does not fit in a
run beside the work that needed the reader.

That is not an argument against doing it. It is an argument for doing it as its own
run, whose whole content is the refactor and the bake that proves it changed nothing.

**Acceptance:**

1. `frame_storefront.py`, `log_dwelling.py` and `outbuilding.py` build their front
   elevations from the `*_params` functions rather than from inline arithmetic —
   `shopfront_panels`, `front_window_rects`, `core_front_rects`,
   `addition_front_rects`, `boarding_holes`, `loft_rect`, `vent_rect`. No archetype
   keeps a second copy.
2. The bake is run and the 212 assets are landed in the same commit, with the
   manifest.
3. The geometry is shown to be unchanged, not asserted to be: compare the rebuilt
   GLBs' vertex counts and bounding boxes against the committed ones and state the
   result. A refactor that moves a vertex is a bug in the refactor.
4. The mirroring warning in all four modules' docstrings comes out, because it is
   no longer true.
