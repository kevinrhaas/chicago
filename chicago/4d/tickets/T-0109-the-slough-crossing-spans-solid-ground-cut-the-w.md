---
id: T-0109
title: The slough crossing spans solid ground: cut the watercourse under its deck
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-19
closed: 2026-08-24
pr: 368
claimed_by: run 8/24/2026, 9:55:52 AM CT
blocked_on: null
needs_bake: false
---

The slough crossing spans solid ground: cut the watercourse under its deck.

**Acceptance:** stated 2026-08-24, before working, because the ticket carried none.

> Standing at the Water Street crossing, the log bridge spans open water. The watercourse is cut
> under the deck; its abutments land on dry bank at both ends; the channel runs unbroken from the
> deck to the river; nothing else is rooted in the cut; and the crossing's own record — the card a
> visitor opens — says what it spans, in figures read off the committed heightfield, rather than
> saying the stream is not modelled.

Not weakened at any point. Measured before choosing, on the committed heightfield: the first four
clauses were **already true** and this run did not make them true — **T-0005** carved dossier zone 14
on 2026-08-20 (changelog v204) and **T-0118** ran its last reach square under this deck the same day
(v210), both filed after this ticket and neither aimed at it. **3.30 m** of open water in the deck's
**8.00 m** span (41 %), deepest **−0.53 m**, **2.35 m** of dry abutment seat at each end, **277 of
277** samples from the deck to the river below the water surface, nearest other structure **45.8 m**
away and nothing rooted in the cut.

The fifth clause was still open and is what shipped: the record told the card, in three places, that
the slough "IS NOT MODELLED IN THIS TERRAIN EPOCH" and that "a visitor sees a bridge over nothing",
and `docs/LIBERTIES.md` L69 said the same in the Evidence panel. All three now carry the measurement.
`tools/measure_slough_crossing.py` gates all five clauses on every commit — proved firing by moving
the deck off the water, by standing an abutment in the stream, by walking the drain up the dry bank,
by hand-editing the clearance, and by planting a fence in the channel.

**No terrain change was available or needed**: swale geometry is inside the terrain staleness hash,
so a re-carve costs a Blender bake the improve runner does not have; the notes added to
`state_slough_mouth` are prose and are stripped from that hash.
