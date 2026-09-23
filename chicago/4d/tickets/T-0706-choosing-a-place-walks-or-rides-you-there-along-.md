---
id: T-0706
title: Choosing a place walks or rides you there along the streets, with a Stop banner and the card on arrival
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-04
pr: 829
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T01:52:46.366Z
claimed_run: null
---

The owner, 2026-09-04: choosing a place should auto-walk you there and "open the card on landing".

**Decision.** `js/route.js` is a grid A* on 2 m cells over the heightfield: footprints (inflated by the walker radius + 0.6 m) and undecked water are blocked; cost 0.35 on a street track, 0.6 in its corridor, 0.4 on decks, 1.0 on prairie; 8-connected without corner cutting, string-pulled within a cost class; `standOff()` puts the destination `max(8, r + 5)` m from the footprint centre toward the nearest track. Built lazily on the first non-instant go. A `null` route falls back to instant travel with `hud.say('No walkable route was found — went straight there')`. The controller runs idle → planning → travelling → arriving → idle; any input of your own after a 250 ms grace stops it, as does `#travel-stop` in the `#travel-banner` (verb · destination · distance). Arrival eases yaw onto the building and opens its card.

**Acceptance:** smoke PART 12 — in walk mode, choosing the Sauganash shows `#travel-banner` with verb, destination and distance; `api.travelSimulate` runs the same code path to `idle`; the card for `sauganash` is open; the visitor stands within 14 m; ≥ 70 % of position samples have `streets.status(e,n).mode ∈ {on, intersection}`; a simulated input stops travel; the Stop button stops travel. The intersection-arrival assertion states its precondition `api.setTravelMode('instantly')`. Both viewports green.

Claimed together; ships in one PR into dev on the owner's instruction.
