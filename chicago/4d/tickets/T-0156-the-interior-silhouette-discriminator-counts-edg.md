---
id: T-0156
title: The interior/silhouette discriminator counts edges internal to a layer as interior
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-23
closed: 2026-08-28
pr: 471
claimed_by: run 8/28/2026, 10:47:33 AM CT
blocked_on: null
needs_bake: false
---

`measure_tie_class.mjs` calls a flickering pixel INTERIOR when the layer's own footprint
surrounds it on all eight sides, and reads that as *the layer fighting itself*. It is not:
`interiorOf` knows the layer's outline against the rest of the scene and cannot see the
boundary between two surfaces OF that layer — one crown behind another, a chimney against its
own roof, a house against the house behind it.

T-0013 measured the size of the error with a depth pass: **94–98 % of what the instrument
reports as interior sits on a depth BREAK inside the footprint**, i.e. is silhouette by any
honest reading, and 0 % is a depth reorder or a shading resample. The number drove a ticket for
six days and would have driven the next one.

The instrument was deliberately NOT changed in the run that measured this — closing a ticket by
rewriting the instrument that measured it is the one move this project does not allow.

**Acceptance:** `measure_tie_class.mjs` reports the internal-edge share separately from the
self-fight share, at the same station and nudge, using a discriminator the tool itself can
defend (T-0013's second-difference depth break is one, `tools/diagnose_interior_flicker.mjs` is
the worked example). The published table in ROADMAP § R-BUG6(c2) and the tool's own output agree
to within the noise of a re-run, control and return both 0 px. No baseline is loosened to make
them agree.