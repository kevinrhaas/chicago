---
id: T-0059
title: The generator half of the wharf layer: a river-wharf mode of pier_crib
state: withdrawn
epic: TOWN
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-27
pr: 426
claimed_by: run 8/27/2026, 9:16:10 PM CT
blocked_on: The premise has no reader and the debt is not the wharf's: one renderer, which draws the wharves already; nine of nine drawn-at-load layers owe a generator half and none has one; and the wharf is the worst of the nine to bake, because its deck height, crib bents and stair are functions of terrain.surfaceHeight evaluated at load and a GLB freezes them. Measured by tools/measure_generator_half.py, gated in check.sh. Refiled whole as T-0252 for the owner to rank.
needs_bake: true
---

The generator half of the wharf layer: a river-wharf mode of `pier_crib`.

Filed by the run that shipped **T-0041**. `docs/ROADMAP.md` K5 (e) asked for the docks and said
they "need a river-wharf mode of `pier_crib`". That turned out to be a BAKE reason rather than a
blocker — the renderer-side half needs no Blender and is shipped — but the generator half is still
owed and is what a BAKED town would carry: `generators/archetypes/pier_crib.py` builds the harbour
piers, and nothing builds a river wharf, so a scene assembled from GLBs alone has no docks in it.

The outline is already derived and committed (`data/wharves/river_landings.json`), so this is the
archetype and its params, reading that record rather than inventing a second set of numbers.

**NEEDS THE BAKE** — Blender, so the improve runner cannot close it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

One demonstration: the river wharves are geometry that comes out of Blender and is placed
from a structure record, on the same terms as every other structure — or the ticket is
answered the other way, with the reading that answers it.

---

## WITHDRAWN 2026-08-27, on three readings — `tools/measure_generator_half.py`, gated in `check.sh`

Measured on `dev` @ `a638614c`, no Blender and no network. The tool reads
`assets/manifest.json`, the generators' own two hashing recipes and the nine committed
layer manifests; `--gate` holds every figure below to the `STATED` block written beside
it, and `tools/check.sh` runs that gate, so the case this ticket was withdrawn on cannot
go quietly stale.

### 1. The GLB this ticket asks for has no reader

The ticket's motivation is one sentence — *"a scene assembled from GLBs alone has no docks
in it"* — and it has a consumer in it. **There is one renderer: `renderers/web`.** It is
the thing that assembles the scene, and it has drawn the wharves since T-0041. Nothing in
this tree reads `assets/` without also reading `data/`, and no second renderer is
proposed anywhere in `tickets/` or `docs/`.

That is not an argument that a GLB-only scene would be worthless. It is the observation
that the cost would be paid **today** for a reader that does not exist **today**, which is
a different decision from the one the ticket states, and not one a loop run should take on
the owner's behalf.

### 2. The debt is nine layers, not the wharf's

| layer | renderer module | record files | generator |
|---|---|---:|---|
| boats | boats.js | 1 | NONE |
| enclosures | enclosures.js | 8 | NONE |
| fauna | fauna.js | 10 | NONE |
| flora | flora.js | 23 | NONE |
| frontage | frontage.js | 5 | NONE |
| residents | residents.js | 173 | NONE |
| signage | signage.js | 1 | NONE |
| **wharves** | **wharves.js** | **1** | **NONE** |
| yard | yard.js | 2 | NONE |

**Nine of nine drawn-at-load layers owe a generator half. Zero have one.** `docs/ROADMAP.md`
K5 asks for the same thing of the yards in almost the same words. So this ticket is not a
unit of work — it is one ninth of a decision nobody has taken, and taking that decision one
layer at a time, by whichever layer happens to reach the top of the queue, is the shape of
work that produces eight more tickets like this one. Refiled whole as **T-0252**.

### 3. Cost — and it cuts BOTH ways, which is why the earlier reading of it was wrong

`generators/mesh_inputs.py` hashes an archetype's builder, `generators/build.py` and
`generators/common/*.py` into every structure asset's `inputs_sha256`;
`generators/terrain_inputs.py` hashes `terrain_gen.py` and the same `common/*.py` into
every terrain asset's. `validate.py --stale` fails on any asset whose hash has moved.
Measured reach, over **349** committed input-tracked assets:

| edit site | re-stales |
|---|---:|
| `generators/common/*.py` | 349 — every committed mesh |
| `generators/build.py` | 347 — every structure in the town |
| `generators/archetypes/pier_crib.py` | **2** — the two harbour piers |
| `generators/terrain_gen.py` | 2 — the ground |

**A `pier_crib` MODE, which is literally what this ticket asks for, costs two meshes and a
`bake.sh --only` — it is cheap, and any argument that withdrew this ticket on rebake cost
would have been wrong.** What is expensive is the *other* route: a new archetype has to
enter `build.py`'s `ARCHETYPES` registry (`build.py:52`), and those bytes are hashed into
347 meshes, so registering one costs a full town rebake before it builds a triangle. The
figure is stated here in both directions because a gate that only reports the number
supporting the conclusion is not a measurement.

### 4. The reason it should not be baked at all is in the layer, and it is T-0001's

This is the reading that decides it, and it is neither of the two above. **A wharf's
geometry is a function of the terrain, evaluated at load.** `renderers/web/js/wharves.js`
takes three separate decisions from `terrain.surfaceHeight`:

- the **deck height**, sampled along the landward edge — *"THE DECK'S HEIGHT IS THE
  TERRAIN'S, NOT THE RECORD'S ... the bridge's lesson (T-0001), where a deck height
  authored beside the mesh instead of taken from it stood a walker 1.8 m over the planks"*;
- each **crib bent**, stepped down to the bed sample under it, *"which is the only reason a
  structure standing in water can be drawn honestly at all"*;
- the **stair**, whose tread count is the terrain's own rise at the foot (T-0058).

A GLB is baked once. Bake the wharf and all three freeze at the heightfield of the bake —
and **the heightfield has moved in 33 commits since 2026-08-01**, with T-0219 in the queue
to move it again. The failure mode is not hypothetical: it is exactly the one T-0001
recorded and this layer was built to avoid.

Both committed manifests already say so, and both said so before this ticket was filed —
`data/wharves/index.json`: *"A wharf is NOT a structure record and NOT baked geometry"*,
and `data/wharves/river_landings.json` gives the reason: a deck on cribs *"is a box on
boxes standing on ground and water this project already draws"*, derived by
`tools/generate_river_wharves.py` and **re-derived byte for byte by `tools/check.sh`,
because 'which frontage gets a wharf' is a rule and a rule has to be auditable.** A GLB is
not auditable that way. Baking the wharves would trade a rule that is re-run on every
commit for a mesh that is checked against a hash.

### What is NOT claimed

That a baked town is a bad idea, that K5's other clauses are wrong, or that the nine layers
should never have generators. Only that **this ticket cannot be the place that decides it**:
the wharf is the worst of the nine to start with, because it is the one whose geometry is a
terrain function, and the decision is general. T-0252 states it whole, for the owner to
rank.
