---
id: T-0225
title: The sward's drawn reach is measured off plants at two per cent coverage
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-28
pr: 450
claimed_by: run 8/28/2026, 4:18:27 AM CT
blocked_on: null
needs_bake: false
---

The sward's drawn reach is measured off plants at two per cent coverage.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by **T-0187** while pricing the obvious fix for the verge dither, and it is the reason that
fix took a different route.

**What it is.** `tools/smoke_renderer.mjs` part 7 reads the sward's outer boundary by binning the
view into 16 bearings and asking each bin for "the furthest plant in this bearing that is actually
DRAWN" — its own words. Drawn is decided by `a.flora.fadeAt(...) > 0.02`. On a coverage ramp that
admits a plant at **two per cent coverage**: the 4x4 screen door keeps one pixel in fifty of it, so
the plant the reach is read off is one a visitor cannot see. The boundary the statistic reports is
therefore the radius at which the placer stopped placing, which the placement guard already
guarantees, and not the edge of the field.

**Why it matters, with the number.** It makes the two reach bars — `minReach >= nominal − fringe −
1.2` and `meanReach >= nominal − 0.5 × fringe` — unmeetable by any representation that draws a
plant whole or not at all, because such a representation's drawn set IS its cover. Simulated slot
by slot on the published mirror against every mid instance's own ring: handing the mid ring's outer
edge over by density takes the mean drawn reach from **26.81 m to 25.42 m at `full`** (bar 24.90 —
survives) and from **11.89 m to 9.64 m at `light`** (bar 11.60, of which only 0.29 m was unspent).
Even a one-metre spread lands at 11.48 m. So the bar as written prefers the dither, which is the
opposite of what the project wants, and T-0187 had to fix the ramp's width instead of its kind.

**Acceptance:** the reach is read at a coverage a visitor can actually see — the threshold is
chosen and justified against the screen door's own behaviour rather than left at 0.02 — and the two
bars are re-derived against the new statistic in the same commit, with the figure each viewport
lands at recorded. Both readings, before and after, printed by the check itself (T-0187 added the
`show` flag for exactly this). It is NOT a licence to slacken the bars: if the honest statistic
puts the present sward below them, that is a finding about the sward and gets its own ticket.

**Links:** `tools/smoke_renderer.mjs` (part 7, `seam`, the `fadeAt(...) <= 0.02` cull) ·
`renderers/web/js/flora.js` (`fadeOf`, `ringsFor`, `slotRing`) · T-0187 · T-0093 · T-0086 ·
ROADMAP § S6a item 3.

---

**RESOLVED 2026-08-28.** The threshold is `1/16` — the screen door's own quantum, the smallest
value at which "drawn" is a property of the plant's coverage rather than of its dither phase, since
`chiBayer4` has sixteen levels and `vChiDither` only slides them. Both bars carry `band x 1/16`,
the inset a linear ramp costs at that coverage (0.44 m desktop, 0.10 m phone), because they are
stated against the placed boundary and the statistic reads the drawn one. Both readings print from
the check. Measured: desktop `full` 25.00-28.00 m, mean 26.61 (was 26.81 at 2 %), bars 21.76/24.46;
mobile `light` 10.32-13.22 m, mean 11.96 (unchanged at 2 %), bars 9.50/11.50. Both clear both bars,
so no finding about the sward falls out. `tools/measure_sward_reach.mjs` is the instrument, and
T-0277 carries the re-pricing of the density handover the old statistic refused.
