---
id: T-0823
title: Walk, wagon and horse each get a speed slider with a named gait, up to 20, 30 and 60 mph
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
claimed_by: run 9/5/2026, 12:57:32 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T18:22:54.548Z
claimed_run: null
---

The owner, 2026-09-05: "for the speed, can you add to set walk speed, horse speed and wagon
speed, like you have for walk speed, and have them max out up to very high levels like walk at
20 mph and horse gallop at some high number like 60 mph or whatever is sensible, and give them
names as you move the slider like trot, etc."

Each ground pace gets its own slider in the Travel section (the walking slider moves there
from Settings, keeping its ids): walk 0.5–8.94 m/s (20 mph), wagon 0.5–13.41 (30 mph), horse
0.5–26.82 (60 mph). The readout names the gait as the slider moves — stroll / walk / brisk walk
/ jog / run / sprint / "faster than any man"; crawl / walking pace / easy roll / steady roll / brisk pace /
rattling along / "runaway" (a wagon rolls; it has no gait of its own); walk / jog / trot / canter / gallop / racing gallop / "beyond any horse" —
beside the speed in the visitor's units. Shift multiplies by 2.28 on foot, 1 by wagon, 1.7 on
horseback, never past the slider's top. The horse's gait beat scales with the speed set. These
are interface choices, not claims about 1835; the top names say so in as many words.

**Acceptance:** PART 12 "each pace sets the walker to its own slider, its Shift factor and its
seat" (WALK.speed equals the stored value of the pace in force; sprint = value × factor capped
at the ceiling; seats +0 / +0.5 / +0.75 unchanged; defaults 1.45 / 3.6 / 6.5 on a fresh store)
and "the three pace sliders top out at 20, 30 and 60 mph and name the gait as they move"
(maxes 8.94 / 13.41 / 26.82; dragging the horse's slider paints "canter", "gallop", "beyond any
horse · 60.0 mph" and sets WALK 26.82 / 26.82); both viewports green, zero page errors.

Claimed together with T-0824; ships in one PR into dev on the owner's instruction.
