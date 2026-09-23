---
id: T-0001
title: A visitor can walk across every bridge, end to end
state: split
epic: TOWN
requested_by: owner
seen: true
effort: L
legacy_id: K10
parent: null
opened: 2026-08-17
closed: 2026-08-17
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

**The owner's ask, verbatim (K10):** "How would a wagon cross that?" Every bridge floats
over its banks (`approach_not_modelled`), and the walker cannot cross one — it follows the
terrain heightfield, so a deck is not ground.

Two halves. (1) **Walker deck support** — the walker stands on a bridge deck instead of the
water under it; renderer-only, no bake. Ship this first. (2) **Approach earthworks** — log
abutments in the shallows (the 1883 settlers' statement), wagon-plausible gradients meeting
the deck at grade; geometry, needs the bake. Regrade `ground_contact` per bridge as it lands.

**Acceptance:** spawn on foot, walk across both branch bridges and the Dearborn drawbridge
end to end without falling into the river; a smoke gate walks one and asserts deck height
under the walker the whole way. Deep history: docs/ROADMAP.md § K10 (line ~9671).

---

**WHERE IT STANDS — half (1) has landed, half (2) has not.** The ticket stays open and
stays where the owner put it; `claimed_by` is cleared so the next run may take the rest.

**Shipped in PR #231:** the walker stands on a deck. `placement.walk_surface_m` carries the
generator's own `deck_height_m` into every sidecar, `walker.js` resolves the floor
through one `surfaceAt()` that every path asks, and a scene anchor — *On the North
Branch bridge, mid-span* — puts a visitor on the planks on foot. The smoke walks the
North Branch crossing end to end and asserts the deck under the boot for the whole
span, that the deck and not the 4.0 m wading barrier is what holds the walker up, and
that they can walk off the far end onto the bank. All four decks in the dataset are
walkable; the gate drives one, as the acceptance clause asks.

**Not shipped, and it is the owner's actual question:** you still cannot get ONTO a
deck from the bank. The deck lands on the traced 1834 waterline, where the ground is at
zero and the deck is at 2.22 m, so the 0.35 m step-up rule refuses it exactly as it
refuses a wall. That is half (2) — log abutments in the shallows and wagon-plausible
approach gradients — and it is geometry: `generators/terrain_gen.py` needs Blender for
the ground GLB, and the improve runner has none, so it belongs to the nightly bake.
Nothing here was faked to look finished: no invented ramp, no widened step rule.

**So the acceptance clause is NOT discharged.** It reads "spawn on foot, walk across …
end to end without falling into the river", and a visitor who arrives at the new anchor
can now do exactly that — but one who walks down Kinzie Street to the bridge cannot,
and that is the reading the ticket is for.

---
**SPLIT 2026-08-17.** The loop's first run under this queue took this ticket, shipped only
the walker-deck half as **PR #231**, titled it `T-0001(1/2)` and left the ticket `claimed` —
it had to invent that notation because the queue had no way to say "this is two runs". That
is the evidence that produced the effort-in-RUNS rule. Split into **T-0045** (the deck, done
by #231) and **T-0046** (the approach earthworks, which needs the bake).
