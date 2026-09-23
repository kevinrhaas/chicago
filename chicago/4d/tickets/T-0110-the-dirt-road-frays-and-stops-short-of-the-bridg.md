---
id: T-0110
title: The dirt road frays and stops short of the bridge deck
state: done
epic: TOWN
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-19
closed: 2026-08-19
pr: 268
claimed_by: run 8/19/2026, 6:29:52 PM CT
blocked_on: null
needs_bake: false
---

The dirt road frays and stops short of the bridge deck.

**The owner, 2026-08-19, walking Kinzie Street west onto the bridge that T-0046 had just
raised to grade:** *"Bridges work great but the dirt road should lead all the way up, it
gets pixely and you can see grass triangles and it ends with a black line and more grass,
prob make it dirt road all the way."* Three phone frames at 264°, 255° and 257° show it:
the worn track narrows raggedly on the approach, green wedges cut into its edges, and it
stops on bare prairie a few metres short of the deck, with a dark line at the abutment.

## Why it frays — and every word of his report maps onto a mechanism

`renderers/web/js/streets.js` clips the track ribbon against the water, per panel:

- **the centreline test** drops a whole panel when either end is over water — right, and
  not the problem here (*"a crossing is a bridge's job, not a ribbon's"*);
- **`dryReach()`** then trims each end on each side INDEPENDENTLY by six-step bisection
  (`CLIP_STEPS = 6`) out to the recorded half-width. Asymmetric on purpose, so a bank road
  keeps its dry verge;
- a panel trimmed under **`MIN_PANEL_W_M = 1.0`** is dropped entirely.

And `terrain.isWater(e, n)` is `heightfield.sample(e, n) < SHORE_Y` (−0.10 m) on a
heightfield of **2.5 m cells**. So on an approach, where the ground crosses the shore
threshold within a few cells, each panel independently bisects against a **cell-quantised**
waterline and lands on a different width from its neighbour. That sawtooth IS the
"pixely" edge and the "grass triangles" — they are the prairie showing through where
consecutive panels were trimmed to different widths. The road then **stops** at the first
panel that falls under a metre, which leaves the last few metres to the deck unpainted:
his "more grass", with the deck's own edge as the "black line".

**T-0046 raised the ramp; it did not tell the road about it.** The earthworks are new dry
ground, but the ribbon still fringes against a threshold sampled at 2.5 m and still has no
idea a bridge is there.

## What "dirt road all the way" needs

The owner's instruction is the acceptance: the track runs onto the approach and butts the
deck. Ways in, for the run to weigh — the point is that **a bridge approach is a place the
ribbon should be told about, not left to infer from a height sample**:

- give the ribbon the bridge records it already has elsewhere in the scene, and where a
  street meets a deck, run the track to the abutment and let the deck carry it across;
- and/or sample the dry test **sub-cell** on approach panels (bilinear on the heightfield
  rather than a nearest-cell threshold) so consecutive panels agree and the edge stops
  sawtoothing;
- and/or make the earthworks wider than `track_width_m` so the whole track is dry — cheap,
  and it fixes the cause rather than the symptom, but only where the ramp is authored.

**Do not** flatten terrain under the road or author a second collision surface: the
module's own contract is that every ribbon vertex samples `terrain.surfaceHeight()` and
the walker stands on that same heightfield. Keep it.

**Acceptance:** from the owner's stand on Kinzie approaching the bridge — and at one other
bridged crossing — the worn track runs continuously onto the approach and meets the deck,
with no sawtooth edge and no bare gap between the last panel and the abutment; the walker
still stands on the heightfield; and a smoke assertion covers the join so it cannot
silently reopen. `needs_bake` only if the ramp geometry itself moves.

**Links:** T-0046 (the approach earthworks, PR #266 — this is its unfinished half) ·
`renderers/web/js/streets.js` (`dryReach`, `CLIP_STEPS`, `MIN_PANEL_W_M`) ·
`renderers/web/js/terrain.js` (`isWater`, `SHORE_Y = -0.10`, 2.5 m grid) · T-0001
(walkable bridge decks).
