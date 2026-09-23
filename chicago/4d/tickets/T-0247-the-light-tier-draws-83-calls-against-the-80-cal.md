---
id: T-0247
title: The light tier draws 83 calls against the 80-call floor restored yesterday, on an unmodified dev
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-28
pr: null
claimed_by: null
blocked_on: Owner ruling 2026-08-28: 'Raise floor to 90' — the re-budget was chosen over the trim this ticket demanded; ruling recorded in the ticket body and at LIGHT_CALL_FLOOR's definition site
needs_bake: false
---

The light tier draws 83 calls against the 80-call floor restored yesterday, on an unmodified dev.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`tools/smoke_renderer.mjs` stage 4 at desktop fails on an **unmodified `dev`**:

```
FAILURES:
 - desktop 1280x800: the light tier draws inside its 80-call floor at the worst stand
   light  worst 746,060 tris of 785,000 at Lake Street at Canal
          worst 83 calls at Lake and Market, the corner itself
```

**Found while working T-0193** (PR #421), whose branch changes one JSON string and no geometry at
all. It reproduced identically against the untouched `dev` mirror
(`git archive origin/dev site/chicago/4d`, then `SMOKE_ROOT` pointed at it), so it is
neither that branch's nor any branch's — it is the state of `dev`.

**Why this is fresh rather than long-standing.** T-0300 restored this floor YESTERDAY,
deliberately and with the reasoning written into the changelog: *"it is eighty again —
the count this project chose before any of the summer's building, not one fitted around
today's reading of seventy-five."* It read 75 then, at the stand it was checked at. It
reads 83 now at `lake_and_market`. Something between those two readings added eight draws
to the lightest tier, and the ticket that restored the floor is the reason anybody can
tell.

**The triangle ceilings are all green** — `light` sits 38,940 under its 785,000, and
`full` and `balanced` pass too. This is the draw-call half of the budget alone, which is
exactly the half T-0300 argued was worth keeping as a separate promise: *"apart from
triangles there is a tally of how many separate times a frame is handed to the graphics
card ... which guarantees a person nothing"* if it is allowed to float.

**Where to start:** the worst stand is `lake_and_market`, not the axial view, and the
count is a per-stand worst — so the question is which layer stopped batching at that
corner specifically. T-0146 (merge far chunks back into single draws) and T-0150's
`furnitureReachM` distance cull are the two mechanisms that hold this number down at
`light`, and the hitching posts (T-0194) and Randolph's street edge (T-0240) are the two
parcels that landed between T-0300's reading and this one.

**Do not fix it by moving the floor.** T-0300's whole argument is that 80 is a chosen
number rather than a fitted one.

**Links:** T-0300 (restored the floor) · T-0135 (the five stands) · T-0146 · T-0150 ·
T-0149 · T-0193 (found it) · T-0240 · T-0194.

---

## WITHDRAWN — THE OWNER RULED FOR THE RE-BUDGET, 2026-08-28

This ticket's own instruction was **"Do not fix it by moving the floor."** The
owner, put the choice directly — *raise the floor to 90, or leave the red
standing and trim* — chose:

> **"Raise floor to 90."**

That supersedes the instruction, and the ticket is withdrawn rather than closed
as done, because the work it asked for — finding which layer stopped batching at
Lake & Market and trimming it — was **declined, not performed**. The reading had
moved 83 → **85** by the time of the ruling (dev's standing smoke,
2026-08-28T18:36Z, the T-0028 tree), so the floor moved by a measured ten
against a measured 85, five calls of slack at today's worst stand.

What survives of this ticket's argument is written at the floor's definition
site in `tools/smoke_renderer.mjs`: the bar has now moved twice, what 90
surrenders is stated there, and the rule for the next red — a trim or an argued
re-budget, never a quiet weakening — stands unchanged. If the batching question
(which layer stopped batching at that corner) ever earns its own ticket, T-0146
and T-0150 remain the places to start.
