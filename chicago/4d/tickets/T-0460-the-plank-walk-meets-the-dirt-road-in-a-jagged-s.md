---
id: T-0460
title: The plank walk meets the dirt road in a jagged sawtooth, and it is the first thing a visitor sees
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-31
closed: 2026-09-03
pr: 676
claimed_by: run 9/2/2026, 11:53:13 PM CT
blocked_on: null
needs_bake: false
---

Reported by the owner on 2026-08-31, with a screenshot, and flagged as wanting
fixing **sooner than most**: *"this one still really bugs me… it's like the first
thing we see."*

The plank walk meets the dirt road in a **jagged sawtooth**. Close up it reads as
a row of loose boards with ragged ends rather than as a made footway. The owner's
statement of what would be acceptable is either of:

- the plank walk sits **consistently over** the dirt road, or
- the walk is **dirty** — the boards meet the mud the way boards in mud do

What is not acceptable is the current in-between: a clean hard sawtooth edge.

## Measured

`data/frontage/town_street_edge.json` — 77 runs, 41 `plank_walk` and 36
`board_crossing`, **254 footway decks** in total:

| | |
|---|---|
| walk width | 1.83 m (6 ft) |
| deck rise over the ground | **0.06 m and 0.11 m** |
| plank thickness | 0.055 m |
| plank pitch | 0.26 m on a walk, 0.32 m on a street edge (`EDGE_PLANK_PITCH_M`) |
| clear between wall face and deck | 0.20 m (`WALK_CLEAR_M`) |

The deck stands **6 to 11 cm proud of the ground** and is built of individual
boards at a 26–32 cm pitch. The sawtooth is what those two facts produce at the
outer edge when nothing resolves the boundary: each board ends where it ends, the
deck is high enough to cast a hard line, and the road surface simply stops.

## Where this sits against the rest of the queue

This is a **visible-quality** ticket in a queue whose top band exists because 41
merges added nothing a visitor could see. It is at the front door of the
experience — the owner's point is that it is among the first things in view — and
it is cheap next to the ground work in T-0444 and T-0453.

**Acceptance:**

1. The chosen treatment is stated before it is built, and it is one of the
   owner's two: the walk sits over the road consistently, or the boards meet dirt
   as dirty boards do. **Not a compromise that keeps the hard sawtooth.**
2. Whatever is chosen is applied to all **254 decks**, not to the one in the
   screenshot. A fix visible from one stand and wrong from the next is not a fix.
3. It holds at walking distance. The fault is reported from close up, so the
   demonstration is a close stand, not an overhead.
4. The 6 cm and 11 cm rises are re-read: if the rise is what makes the edge hard,
   say so and say what it becomes. `WALK_RISE_M` is a chosen number, not a source.
5. `tools/check.sh` green, and the renderer smoke carries an assertion for
   whatever the new edge rule is.

## The treatment chosen, stated before it was built (acceptance 1)

**The first of the owner's two: the walk sits consistently over the dirt road.** Not
lowered into the mud, and not a compromise that keeps the sawtooth.

What made the edge hard was never the rise on its own — it was that nothing at all
resolved the boundary. A walk laid as boards alone ends, at each side, in a row of board
ENDS: at a 0.32 m pitch with a 0.02 m gap between them over a deck standing 0.11 m proud
of the road, the outer edge of 3.17 km of sidewalk was about twenty thousand short
end-grain faces with daylight between them. The one member that DID reach the ground —
the 2.08 m bay stringer — stood 0.09 m inboard, in shadow under the overhanging ends.

So the boundary is resolved the way a plank sidewalk actually resolves it: **the boards
are held between two string pieces.** 0.09 m stock running ALONG the walk down each side,
taking the outermost 0.09 m of its own 1.83 m width so the walk does not widen, its top
flush with the boards it holds, its foot at the lowest ground under its own length. The
boards stop at its inner face.

It costs no timber the layer did not already draw. The string piece IS the bay stringer,
moved out to the walk's own edge and brought up flush with the deck instead of stopping
under it, so the box count does not move — the layer gains a made edge without gaining a
box.

**The rises are re-read and NOT reduced (acceptance 4).** `WALK_RISE_M` is a chosen number
and it stays chosen: a plank walk in a street of mud is a step up out of it, and standing
consistently over the road is the whole of the treatment the owner picked. What the rise
becomes is a face rather than a comb — the same 0.11 m, presented once along the length
instead of ten thousand times across it. The crossings' 0.06 m is likewise unchanged, and
for its own reason, below.

**A second thing moved with it, and it is a correction rather than a decision.** A board
used to sample the terrain under its own centre, which put a fresh height on the deck
every 0.32 m; a walk laid in stringer bays does not do that, because the bay is the timber
that carries the boards. Every board in a bay now takes THAT BAY's height, which is what
makes the top of the string piece and the tops of the boards it holds one line to the
millimetre. Measured over the whole town: the largest step between two consecutive string
pieces is **0.026 m**, against the 0.04 m the generator already audits a bay's ground flat
to.

**What is NOT treated, and why (part of acceptance 2).** The **36 board crossings** keep
their 0.06 m rise and take no string piece. A crossing lies in the wheel track and its
boards are laid ALONG the way a foot travels, so its sides are already one continuous
board face rather than a comb of ends — there is no sawtooth on a crossing to resolve, and
an edge timber raised across a road is a thing to catch a wheel on. All **48 plank walks**
are treated, which is every walk in the layer and all 182 of the 254 walking decks that
carry one.

## Verified

- **6,646 lengths of string piece** laid across the layer, largest step between two
  consecutive ones **0.026 m**.
- **The gate carries the edge rule** (acceptance 5): `smoke_renderer.mjs` marches the named
  98.6 m run `blk_lake_clark_north_walk_1` in 0.2 m stations and asks each of the 487 for
  timber from the deck down to the ground at the walk's own edge line, by FACE rather than
  by vertex. On the geometry this replaced, **487 of 487** stations read as an open edge; on
  the string piece, **0 of 487**. The check was run against the old build to confirm it
  fails there.
- **Close stands** (acceptance 3): two 1280x800 walking-eye stands on Lake Street at
  (600, -123.4) and (620, -124.1), 2.5 m out in the road — the edge reads as one unbroken
  made line to the vanishing point, with no daylight and no end grain.
- `smoke_renderer.mjs` stage 2 (the part that covers this layer) green at **390x780** and
  **1280x800**, zero page errors; the band check "the plank decks tie into the ground they
  cross" still passes.
- **`tools/check.sh` could NOT be brought green, and not because of this work.** `dev` was
  already failing 10 legs before this branch existed — measured on a clean checkout of
  `origin/dev` — from PR #670. This diff's failing-leg list is byte-identical to that
  baseline. Filed as its own ticket.
