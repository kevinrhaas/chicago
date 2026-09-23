---
id: T-0084
title: A wagon tongue is drawn as a plank on edge, not a pole
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-18
pr: 250
claimed_by: run 8/18/2026, 4:54:32 PM CT
blocked_on: null
needs_bake: false
---

Seen while shipping T-0081, standing in the Green Tree's yard where three wagons now
have their tongues down: the tongue reads as a heavy dark board lying on the grass, not
as a pole.

`renderers/web/js/yard.js` draws it as ONE horizontal box spanning the drop from the
front axle to the ground — `halfH = (rootY - tipY) / 2`, about 0.24 m — so a 2.75 m
stick 0.055 m thick is drawn 0.48 m deep. The comment says why it was done that way ("a
tongue is a stick, and a stick's exact inclination is not a claim this record makes"),
and that reasoning is sound about the ANGLE and wrong about the SECTION: the box has to
be that deep only because it is axis-aligned. An inclined box of the tongue's own
section makes the same claim about the angle and does not put a plank in the yard.

**Acceptance:** the tongue is drawn at its recorded section along its own inclination
(`pushBoxV` already exists on this layer for exactly this), on every wagon, with the
smoke's wagon bound unchanged; and one frame from the Green Tree's yard shows a pole.

**Confirmed independently by the owner, 2026-08-18, with a screenshot from the Green
Tree's yard: "a note about the wagons to fix, it looks like that bar is supposed to be
below the carriage of the wagon holding the wheels together but not sure. all the wagons
seem off."** He is looking at this plank — it lies in the grass ahead of the wheels, dark
and heavy, reading as a structural member that has come adrift rather than as a tongue
resting on the ground. That the defect was found twice, from the code and from the scene,
is the whole case for fixing it.

His second reading — that the bar ought to be *under* the wagon holding the wheels
together — is a **separate and also-real defect**, filed as its own ticket: the wagon has
no running gear at all, so the box floats over two loose axles and the eye goes looking
for the missing member. Fix this one narrowly (the tongue's section along its own
inclination); the undercarriage is that ticket's demonstration, not this one's.
