---
id: T-0100
title: A street's geometry confidence never reaches the picture
state: done
epic: RENDERING
requested_by: loop
seen: false
effort: XS
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-24
pr: 357
claimed_by: run 8/24/2026, 7:26:15 AM CT
blocked_on: null
needs_bake: false
---

A street's geometry confidence never reaches the picture.

Found while shipping T-0044's fort road. `renderers/web/js/streets.js` dithers a street by
`max(surface_confidence, wear_confidence)` and never reads `geometry_confidence` — the field that
says whether the LINE is traced, inferred or invented. It happens to be harmless today because
every reconstructed line here also carries reconstructed wear, but that is a coincidence of the
data and not a property of the renderer: a street whose route was invented and whose surface and
wear were attested would draw at full confidence, and turning `reconstructed` off would leave the
invention standing.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

The street layer's confidence includes `geometry_confidence`, and a test or measurement shows a
street with an invented line dithering out with the rest of the invented town.
