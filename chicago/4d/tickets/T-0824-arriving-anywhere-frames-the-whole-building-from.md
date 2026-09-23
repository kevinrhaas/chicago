---
id: T-0824
title: Arriving anywhere frames the whole building from its front and opens its card
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 907
claimed_by: run 9/5/2026, 12:57:33 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T18:22:54.696Z
claimed_run: null
---

The owner, 2026-09-05: "for any travel, when you land it should be a nice complete view of the
structure and you should open up the detail card for that structure, center the structure
entirely in frame."

One framing rule in main.js (`framing(id)`), used by an instant Go to, by the end of a ride
and by the end of a flight: stand on the building's front (the router's nearest-street
bearing, south-west when no street is near) at the distance that fits its footprint's
half-diagonal across the 76° horizontal field of view and its height (wall × 1.55 for the
roof) within the live vertical one, with margin; aim at its middle; the card opens on arrival.
The distance is derived from the record and the camera, never a constant, so a privy and a
long store are each framed to fit (clamped 10–90 m). The router's stand-off takes the
distance as an argument and still probes for free ground.

**Acceptance:** PART 12 — the walk to the Sauganash, the flight to a far structure and "Go
there" from a person's card each end within 2.5 m of `api.framing(id).distance` with the
card open AND the footprint's four extreme ground points and the ridge project inside the
frame (NDC ±0.95); both viewports green, zero page errors.

Claimed together with T-0823; ships in one PR into dev on the owner's instruction.
