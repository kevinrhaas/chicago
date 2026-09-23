---
id: T-0116
title: The road-legibility gate's third station turns red when the sloughs land: the swale ground pulls the 250-600 m band under its bar
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-20
closed: 2026-08-20
pr: 275
claimed_by: null
blocked_on: null
needs_bake: false
---

Found by T-0005's run (2026-08-20), measured on its branch against a dev baseline in a
clean tree, and it is the reason that branch is parked on `hold` rather than merged. The
`lake_market` station — the one road station of the three that still PASSED on dev after
T-0114 turned the other two red — fails on mobile the moment the slough swales are carved,
and the decimation setting is exonerated: it fails identically at `--decimate-deg 0.030`
(the committed value) and `0.031`, and dev with the same commands shows exactly its two
known failures and this station green.

The numbers, mobile 390x780, published mirror, 250-600 m band: dev ΔL* 2.3 of 4.2 opaque,
**99 % perceptible** of 111 bare, weber 0.0937 over ground L* 53.9 → branch ΔL* 2.0 of
3.8, **47-48 %**, weber 0.0827 over ground L* 53.5. Same 111 probes seen of the same 464
projected, so the road geometry and clipping did not move — the *contrast* fell, and even
the opaque ceiling fell (4.2 → 3.8). The 600-4000 m reported-only band collapses the same
way (100 % → 8 %). Bands under 250 m are byte-for-byte unchanged. Side-by-side renders
from the stand (tools/shoot.mjs, same coordinates) are visually indistinguishable.

What is NOT yet established is the mechanism: the swales cross roads inside the band at
only a handful of places (Lake at ~E +483, Randolph at ~E +622), which cannot account for
half of 111 probes losing perceptibility — something about the carved ground shifts the
band-wide road/ground contrast the probes measure. T-0114's own history warns the prime
suspect has been refuted once already in this system; measure before choosing.

**Acceptance:** the mechanism is identified with the R-BUG2 measurement (which probes fell,
where they sit, what pixel change moved them), and either the T-0005 branch's ground is
adjusted so all three stations clear their bars on both viewports, or the finding is shown
to be T-0114's mid-distance faintness arriving at a third station — in which case the two
tickets merge their diagnosis and the bar question goes to whoever owns T-0114's repair.
Links: T-0005, T-0114, docs/RESEARCH/main_branch_sloughs_1833.md.
