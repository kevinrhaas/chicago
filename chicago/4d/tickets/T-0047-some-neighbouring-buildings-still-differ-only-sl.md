---
id: T-0047
title: Some neighbouring buildings still differ only slightly, because the facade tone is a random deal
state: done
epic: RENDERING
requested_by: loop
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-08-17
closed: 2026-08-22
pr: 310
claimed_by: run 8/22/2026, 9:36:34 AM CT
blocked_on: null
needs_bake: false
---

**Opened by T-0048, from its own measurement.** Every structure's facade tone is dealt from a
hash of its id (`renderers/web/js/facades.js`), which is deterministic, cheap and blind to where
the building stands. A blind deal has a tail: measured on the published mirror over 321
nearest-neighbour pairs within 60 m, the median pair differs by **10.4 %** in applied value and
the tenth percentile by **2.4 %**, which is at or under what a visitor can see between two walls
in the same light. No pair is identical — that invariant is gated — but about a tenth of them
read as one paint.

This is K49's stratification finding one layer over: an even deal is not an even LOOK, and the
fix there was to deal against the structure of the thing being dealt into rather than to raise
the magnitude. Here that means a repulsion pass — a building's tone nudged away from the
neighbours already placed — not a bigger jitter, whose ceiling is already argued from the spread
the archetypes bake (`docs/LIBERTIES.md` L126).

**Acceptance:** the tenth-percentile neighbour-pair difference in applied value is at least half
the median, measured by `tools/measure_facade_variety.mjs` on the published mirror, with the deal
still deterministic (two loads of one scene give one town) and no building outside L126's stated
bounds. The two attested-paint records stay exempt and bit-exact.
