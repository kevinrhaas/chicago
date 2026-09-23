---
id: T-0372
title: North Water Street's two tight spots are 5.5 m and 8.5 m from water, and the setback rule cannot see either
state: done
epic: TOWN
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-08-29
pr: 572
claimed_by: run 8/29/2026, 6:41:58 PM CT
blocked_on: null
needs_bake: false
---

Found by [[T-0307]], which re-derived the street on the bank's offset curve and, to
carry an honest before-and-after, replaced the clearance probe's single ray with a
search in every direction. That measurement is what found these: on the OLD committed
line they read the same, so neither is a regression — both are things the old statistic
could not see.

**THE WEST TERMINUS, 5.50 m.** The street's last vertex is `[-30, 45.2]`, unmoved by
T-0307. `E_WEST_END = -30.0` is where the street stops because west of E −35 "the widest
water run at an easting is no longer the main stem: the branch merges into it and its
north edge jumps from N +33 to N +216 in one 5 m step, so the setback rule has nothing
to read". The rule reads the main stem's north bank AT AN EASTING; the North Branch lies
to the WEST of the terminus and no easting-indexed rule can see it. So the derivation
holds the corridor half a module off the main stem and lets its own end stand 5.5 m from
the branch — a quarter of the module, and the drawn 6 m track's edge is 2.5 m off the
water there.

**THE CROSSING'S EAST ABUTMENT, 8.50 m**, at about `[200, 156.9]`. Here the street is
anchored on `north_water_slough_crossing`'s deck rather than on the setback — deliberate,
T-0254: "the street has to arrive AT the abutment, not at where the setback rule would
have put it." The bay's edge is still climbing there. The report excludes ±4 m of the
deck's own span because the crossing owns that water, and 8.50 m is what stands just
outside that exclusion.

**The question is which of three this is**, and it is a real question rather than a
number to tune: (a) the street genuinely ended at the fork and on a bridgehead, and a
town street may run within a quarter module of water at both — say so and gate the
figure at 5 m instead of 12; (b) the terminus should retreat east until the branch is a
half module off, which shortens the street; (c) the requirement should be raised on the
WATER MASK rather than on the main stem's bank polyline — `nearest_water(e, n) >=
SETBACK_M` — which sees the branch, the bay and everything else, and would move both
ends.

**Acceptance:** one of the three is chosen with the numbers behind it, the choice is
written into the street record's note, and `derive_north_water.py` either enforces it or
states in its report why the two ends are exempt.

**Links:** [[T-0307]] (the offset curve, and the measurement that found this) · T-0254
(the crossing and the abutment anchor) · T-0226 (why the line is derived at all) ·
`tools/derive_north_water.py` (`E_WEST_END`, `nearest_water`, `perpendicular_clearance`).
