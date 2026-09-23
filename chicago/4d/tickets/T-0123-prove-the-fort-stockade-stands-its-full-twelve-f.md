---
id: T-0123
title: Prove the fort stockade stands its full twelve feet, and name what a visitor walks up to
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-08-20
closed: 2026-08-20
pr: 283
claimed_by: run 8/20/2026, 3:25:57 PM CT
blocked_on: null
needs_bake: false
---

Prove the fort stockade stands its full twelve feet, and name what a visitor walks up to.

**The owner, 2026-08-19, from a phone frame at the fort, SW 226°:** *"I am fairly sure that
the wall around the fort Dearborn is way too short, I can walk up to it and it's below my
height, I would think those walls would be at least 8 feet high?"*

## Measured before queuing — and the stockade is not short

- `data/structures/fort_dearborn_palisade.json` records **`picket_height_m` 3.7 m** —
  twelve feet — `reconstructed`, and the note is unusually honest about it: *"THE SOURCE
  GIVES AN ADJECTIVE AND THIS RECORD NEEDS A NUMBER … a guess dressed in a plausible
  number."* Kinzie's *"high pickets"* is all the evidence there is.
- The committed geometry agrees: `assets/gltf/fort_dearborn_palisade__picket_1816.glb`
  measures **3.80 m tall** over a **59.6 × 59.6 m** square. Against the walker's
  `eyeHeight` of **1.68 m**, that is more than twice eye height.

So the fort wall already exceeds the eight feet he expected, and no height change is
warranted on this evidence.

## What he is most likely standing at

`fort_dearborn_garrison_garden` — the company gardens, *"on the reservation south-west of
Fort Dearborn"*, a 77 × 77 m plot whose fence is the SAME `palisade` archetype in its
other mode: `wall_kind: worm_fence`, `fence_height_m` **1.3 m**, built at **1.14 m**.
Chest height, split rails, and a zig-zag plan — which matches the triangular facets in his
frame. A four-foot worm fence around a vegetable garden is period-correct and should not
be raised either.

**The defect is therefore not the height. It is that a visitor cannot tell the two apart**
— he walked up to a garden fence, read it as the fort's wall, and concluded the
reconstruction was wrong. That is the confidence system failing at its own job: this
project's whole claim is that you can always find out what you are looking at.

## What to do

1. **Prove the stockade, with a gate.** A smoke assertion standing a walker at the
   stockade and requiring its top to sit above eye height — so nobody ever has to take
   this measurement by hand again, and so a future change that flattens it is caught.
   Include the garden fence as its opposite number: 1.14 m, deliberately below eye.
2. **Make the fence say what it is.** Check whether the garrison-garden fence answers a
   pick where a visitor would naturally tap it, and whether the card names it as the
   garden's fence rather than a fort wall. Enclosures are pickable
   (`enclosures.pickAt` in `main.js`) — confirm this one is, at the height and distance a
   walker meets it, and fix it if it is not.
3. **Only then consider the number.** If, with both of those true, twelve feet still reads
   short from the ground, that is a judgement about the reconstruction and it belongs to
   the owner — bring him the frame and the note that says the figure is a guess, do not
   quietly raise it.

**Acceptance:** a gated assertion that the stockade stands above eye height and the garden
fence below it; a pick on the garden fence that names the garden; and one frame from the
owner's stand with both in view. No dimension changed without his say-so.

**Links:** `data/structures/fort_dearborn_palisade.json` (`picket_height_m` 3.7) ·
`data/structures/fort_dearborn_garrison_garden.json` (`fence_height_m` 1.3) ·
`generators/archetypes/palisade.py` (the two modes) · `renderers/web/js/walker.js`
(`eyeHeight` 1.68).
