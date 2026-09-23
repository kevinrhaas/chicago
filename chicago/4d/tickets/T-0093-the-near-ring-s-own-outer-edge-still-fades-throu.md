---
id: T-0093
title: The near ring's own outer edge still fades through a screen of dots at 5-7.6 m
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-24
pr: 363
claimed_by: run 8/24/2026, 7:57:44 AM CT
blocked_on: null
needs_bake: false
---

The near ring's own outer edge still fades through a screen of dots at 5–7.6 m.

Found while shipping **T-0086** (the far sward). That ticket closed the OUTER ring edge — past the
mid and forb rings the sward now continues as a density-thinned band with no dither in it at all —
and in doing so it made plain that the speckle a walker sees on the verge is a different edge.

**What it is.** `TUNE.near` fades from 5.4 m to 7.6 m (`radius: 7.6, band: 2.2`), resolved by the
same ordered 4×4 Bayer screen door every ring uses (`flora.js` ≈ `plantMaterial`, `chiBayer4`). At
five metres a tuft is hundreds of pixels tall and its blades are a few pixels wide, so the dither
carves the blades rather than thinning the plant: it reads as a patch of speckled grass in the
lower corners of the frame. The mid ring fades IN across 4.5–7.5 m over the same ground, so the
handover exists — what does not exist is a handover that is invisible.

**Why it was not done in T-0086.** That run's band stands at 16–175 m and never touches the near
ring's tune. Widening `band` spreads the dots over more ground rather than removing them, so the
answer is probably the same one T-0086 used — a density handover rather than a coverage ramp — and
the near ring is the most heavily tuned layer in the file, with `crowdsTheWalker`, the head ring
and the R-BUG7 support gate all reading off it. That is a run of its own.

**Acceptance:** at the two stands T-0086 used and at any stand in open prairie, no speckled band is
visible where the near tufts hand over to the mid cards, at HIGH and at LOW — and the head-support
gate and the pop-in gate are unchanged. Before/after pairs of the verge at eye height.

**Links:** T-0086 (which found it) · T-0035 (the ramp is coverage, not height) ·
`renderers/web/js/flora.js` (`TUNE.near`, `ringsFor`, `chiBayer4`).
