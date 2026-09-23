---
id: T-0252
title: Decide once whether a baked town carries the nine renderer-drawn layers, or none of them
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

Decide once whether a baked town carries the nine renderer-drawn layers, or none of them.

Filed by the run that withdrew **T-0059**, which asked for one ninth of this decision and
could not answer it without taking the other eight on the owner's behalf.

## The reading, and it is gated

`tools/measure_generator_half.py`, run by `tools/check.sh`. Measured on `dev` @ `a638614c`:

| layer | renderer module | record files | generator |
|---|---|---:|---|
| boats | boats.js | 1 | NONE |
| enclosures | enclosures.js | 8 | NONE |
| fauna | fauna.js | 10 | NONE |
| flora | flora.js | 23 | NONE |
| frontage | frontage.js | 5 | NONE |
| residents | residents.js | 173 | NONE |
| signage | signage.js | 1 | NONE |
| wharves | wharves.js | 1 | NONE |
| yard | yard.js | 2 | NONE |

**Nine of nine drawn-at-load layers owe a generator half. Zero have one.** Each is a
directory under `data/` with its own `index.json` manifest and a renderer module that
draws it from those numbers at load; none of them produces or consumes a GLB.

## Why it is one decision and not nine tickets

`docs/ROADMAP.md` K5 asks for the generator half of the wharves and of the yards in almost
the same words, and T-0059 was the wharf clause. Answering them one at a time, in whatever
order a layer reaches the top of the queue, means:

- **the same argument is had nine times**, and it is the same argument every time;
- **each answer sets a precedent the next one inherits without anybody deciding it**;
- **the cost is not additive.** A new archetype enters `generators/build.py`'s
  `ARCHETYPES` registry, and those bytes are hashed into 347 of the 349 committed meshes,
  so the FIRST layer to take this route costs a full town rebake and the other eight are
  then nearly free. Which layer goes first is therefore an arbitrary tax on one ticket.

## What the decision has to answer

1. **Who reads the GLBs?** There is one renderer, `renderers/web`, and it draws all nine
   layers already. A baked town that carried them would be for a reader that does not yet
   exist. Is one proposed — a viewer, an export, a third party's import — and when?
2. **What happens to the terrain-dependent layers?** At least one of the nine cannot be
   baked without regressing: `wharves.js` takes its deck height, every crib bent and its
   stair tread count from `terrain.surfaceHeight` at load, and the heightfield moved in 33
   commits in August 2026 alone. Baking those reintroduces T-0001's fault by construction.
   `flora`, `fauna` and `frontage` are likely to have the same shape. So the honest answer
   may be "some of them", and if it is, the rule that sorts them belongs here.
3. **What happens to the RULES?** Five of these layers' records are re-derived byte for
   byte by `check.sh` on every commit — *"'which frontage gets a wharf' is a rule and a
   rule has to be auditable"*. A GLB is checked against a hash instead. Does a baked layer
   keep its re-derivation gate, and against what?
4. **Is the answer just "no"?** It is a legitimate one, and it is nearly free: it costs a
   sentence in `docs/GLB-CONTRACT.md` saying that a data layer drawn at load is drawn at
   load, and it retires four ROADMAP clauses and any future ticket that reopens them.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

A stated decision — all nine, none, or a named subset with the rule that picks it — written
where the next run will hit it (`docs/GLB-CONTRACT.md`, since this is a generator/renderer
boundary question and that document is the boundary), with the ROADMAP clauses it answers
pointed at it and `tools/measure_generator_half.py`'s reading either kept as the gate or
retired with a reason. **This is the owner's call, not a measurement**; the loop's part was
to establish that it is one question rather than nine, and that part is done.
